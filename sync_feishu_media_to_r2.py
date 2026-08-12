#!/usr/bin/env python3
"""Mirror temporary Feishu media URLs in generated API JSON to Cloudflare R2.

refresh.py remains the single source of truth for reading Feishu. This script
only turns generated temporary attachment URLs into stable R2 public URLs.
Media is stored by SHA-256, so unchanged content is reused instead of uploaded
again.
"""
from __future__ import annotations

import hashlib
import json
import mimetypes
import os
import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

import boto3
import requests
from botocore.config import Config
from botocore.exceptions import ClientError


ROOT = Path(__file__).resolve().parent
API_DIR = ROOT / "api"
REPORTS_DIR = ROOT / "reports"
API_FILES = ("portfolio.json", "clients.json", "zhixing.json", "curation.json", "ai-plus-articles.json")
MANIFEST_FILE = API_DIR / "r2-media-manifest.json"
R2_PREFIX = os.environ.get("R2_MEDIA_PREFIX", "feishu-media").strip("/") or "feishu-media"
R2_LOCAL_MEDIA_PREFIX = os.environ.get("R2_LOCAL_MEDIA_PREFIX", "site-media").strip("/") or "site-media"
SYNC_MODE = os.environ.get("R2_SYNC_MODE", "mirror").strip().lower() or "mirror"
SYNC_SCOPE = os.environ.get("R2_SYNC_SCOPE", "all").strip().lower() or "all"
R2_CLEANUP_MODE = os.environ.get("R2_CLEANUP_MODE", "report").strip().lower() or "report"
DOWNLOAD_TIMEOUT = float(os.environ.get("R2_DOWNLOAD_TIMEOUT", "30"))
WORKERS = max(1, int(os.environ.get("R2_SYNC_WORKERS", "6")))
LOCAL_MEDIA_EXTENSIONS = {".mp4", ".webm", ".mov"}
TEXT_EXTENSIONS = {".html", ".css", ".js"}


def require(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise SystemExit(f"Missing required environment variable: {name}")
    return value


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def is_feishu_media_url(value: str) -> bool:
    parsed = urlparse(value)
    return (
        parsed.scheme in {"http", "https"}
        and parsed.hostname is not None
        and parsed.hostname.endswith("feishu.cn")
        and "/stream/download/authcode/" in parsed.path
    )


def extension_for(content_type: str, source_url: str) -> str:
    content_type = content_type.split(";", 1)[0].strip().lower()
    known = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
        "image/gif": ".gif",
        "image/svg+xml": ".svg",
        "video/mp4": ".mp4",
        "video/webm": ".webm",
        "application/pdf": ".pdf",
    }
    if content_type in known:
        return known[content_type]
    guessed = mimetypes.guess_extension(content_type)
    if guessed:
        return guessed
    suffix = Path(urlparse(source_url).path).suffix
    return suffix if suffix and len(suffix) <= 8 else ".bin"


def public_url(base_url: str, key: str) -> str:
    return f"{base_url.rstrip('/')}/{key}"


def load_manifest(public_base_url: str) -> dict[str, Any]:
    if not MANIFEST_FILE.exists():
        return {
            "schemaVersion": 1,
            "generatedAt": now_iso(),
            "r2Prefix": R2_PREFIX,
            "r2LocalMediaPrefix": R2_LOCAL_MEDIA_PREFIX,
            "publicBaseUrl": public_base_url,
            "objects": {},
            "localAssets": {},
        }
    try:
        data = json.loads(MANIFEST_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        data = {}
    if not isinstance(data, dict):
        data = {}
    data.setdefault("schemaVersion", 1)
    data.setdefault("objects", {})
    data.setdefault("localAssets", {})
    data["r2Prefix"] = R2_PREFIX
    data["r2LocalMediaPrefix"] = R2_LOCAL_MEDIA_PREFIX
    data["publicBaseUrl"] = public_base_url
    return data


def save_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def is_missing_object(error: ClientError) -> bool:
    code = str(error.response.get("Error", {}).get("Code", ""))
    status = int(error.response.get("ResponseMetadata", {}).get("HTTPStatusCode", 0))
    return code in {"404", "403", "NoSuchKey", "NotFound", "Forbidden"} or status in {403, 404}


def content_type_for_path(path: Path) -> str:
    guessed, _ = mimetypes.guess_type(path.name)
    return guessed or "application/octet-stream"


def should_skip_text_file(path: Path) -> bool:
    rel = path.relative_to(ROOT)
    if rel.parts[0] in {".git", ".github", ".playwright-cli", "__pycache__", "reports", "test-results"}:
        return True
    if rel.parts[0] == "temp-video-previews":
        return True
    return path.name.startswith((".codex-", ".tmp-", "temp-"))


def r2_key_from_url(value: str, public_base_url: str) -> str:
    base = public_base_url.rstrip("/") + "/"
    if not value.startswith(base):
        return ""
    key = value[len(base) :].split("?", 1)[0].split("#", 1)[0]
    return unquote(key).strip("/")


def collect_used_r2_keys_from_value(value: Any, public_base_url: str, keys: set[str]) -> None:
    if isinstance(value, str):
        key = r2_key_from_url(value, public_base_url)
        if key:
            keys.add(key)
        return
    if isinstance(value, list):
        for item in value:
            collect_used_r2_keys_from_value(item, public_base_url, keys)
        return
    if isinstance(value, dict):
        for item in value.values():
            collect_used_r2_keys_from_value(item, public_base_url, keys)


def collect_used_r2_keys(public_base_url: str) -> set[str]:
    keys: set[str] = set()
    for name in API_FILES:
        path = API_DIR / name
        if path.exists():
            collect_used_r2_keys_from_value(json.loads(path.read_text(encoding="utf-8")), public_base_url, keys)

    base_pattern = re.escape(public_base_url.rstrip("/") + "/")
    url_pattern = re.compile(base_pattern + r"[^\"'\s<>)]+")
    for path in sorted(ROOT.rglob("*")):
        if (
            not path.is_file()
            or path.suffix.lower() not in TEXT_EXTENSIONS
            or should_skip_text_file(path)
        ):
            continue
        for match in url_pattern.finditer(path.read_text(encoding="utf-8")):
            key = r2_key_from_url(match.group(0), public_base_url)
            if key:
                keys.add(key)
    return keys


def main() -> None:
    if SYNC_MODE not in {"mirror", "reuse"}:
        raise SystemExit("R2_SYNC_MODE must be either 'mirror' or 'reuse'")
    if SYNC_SCOPE not in {"all", "local_videos"}:
        raise SystemExit("R2_SYNC_SCOPE must be either 'all' or 'local_videos'")
    if R2_CLEANUP_MODE not in {"off", "report", "delete"}:
        raise SystemExit("R2_CLEANUP_MODE must be one of: off, report, delete")

    account_id = require("CLOUDFLARE_ACCOUNT_ID")
    access_key_id = require("R2_ACCESS_KEY_ID")
    secret_access_key = require("R2_SECRET_ACCESS_KEY")
    bucket = require("R2_BUCKET")
    public_base_url = require("R2_PUBLIC_BASE_URL")
    endpoint_url = f"https://{account_id}.r2.cloudflarestorage.com"

    client = boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key_id,
        aws_secret_access_key=secret_access_key,
        region_name="auto",
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
    )
    manifest = load_manifest(public_base_url)
    objects: dict[str, Any] = manifest.setdefault("objects", {})
    local_assets: dict[str, Any] = manifest.setdefault("localAssets", {})
    url_cache: dict[str, str] = {}
    state_lock = threading.Lock()
    manifest_dirty = False
    stats = {
        "scanned": 0,
        "downloaded": 0,
        "uploaded": 0,
        "reused": 0,
        "pending": 0,
        "changedFiles": 0,
        "failed": 0,
        "localScanned": 0,
        "localUploaded": 0,
        "localReused": 0,
        "localReferenceFilesChanged": 0,
        "orphanObjects": 0,
        "orphanLocalAssets": 0,
        "orphanUniqueKeys": 0,
        "orphanDeleted": 0,
        "orphanDeleteFailed": 0,
    }
    failures: list[dict[str, str]] = []
    cleanup_failures: list[dict[str, str]] = []

    def ensure_r2_object(body: bytes, *, key: str, content_type: str) -> str:
        nonlocal manifest_dirty
        target = public_url(public_base_url, key)
        try:
            client.head_object(Bucket=bucket, Key=key)
            with state_lock:
                stats["reused"] += 1
        except ClientError as error:
            if not is_missing_object(error):
                raise
            if SYNC_MODE == "reuse":
                with state_lock:
                    stats["pending"] += 1
                return ""
            client.put_object(
                Bucket=bucket,
                Key=key,
                Body=body,
                ContentType=content_type,
                CacheControl="public, max-age=31536000, immutable",
            )
            with state_lock:
                stats["uploaded"] += 1
                manifest_dirty = True
        return target

    def mirror(url: str) -> str:
        nonlocal manifest_dirty
        with state_lock:
            if url in url_cache:
                return url_cache[url]
            stats["scanned"] += 1

        try:
            response = requests.get(url, timeout=DOWNLOAD_TIMEOUT)
            response.raise_for_status()
            body = response.content
        except Exception as exc:
            with state_lock:
                stats["failed"] += 1
                failures.append({"url": url, "error": str(exc)})
                url_cache[url] = url
            return url

        if not body:
            with state_lock:
                stats["failed"] += 1
                failures.append({"url": url, "error": "Feishu returned an empty media response"})
                url_cache[url] = url
            return url
        with state_lock:
            stats["downloaded"] += 1

        digest = hashlib.sha256(body).hexdigest()
        with state_lock:
            existing = objects.get(digest)
            if isinstance(existing, dict) and existing.get("r2Key"):
                target = public_url(public_base_url, str(existing["r2Key"]))
                if existing.get("r2Url") != target:
                    existing["r2Url"] = target
                    manifest_dirty = True
                stats["reused"] += 1
                url_cache[url] = target
                return target

        content_type = response.headers.get("Content-Type", "application/octet-stream")
        key = f"{R2_PREFIX}/{digest[:2]}/{digest}{extension_for(content_type, url)}"
        target = ensure_r2_object(body, key=key, content_type=content_type.split(";", 1)[0])
        if not target:
            with state_lock:
                url_cache[url] = url
            return url

        with state_lock:
            objects[digest] = {
                "sha256": digest,
                "size": len(body),
                "contentType": content_type.split(";", 1)[0],
                "r2Key": key,
                "r2Url": target,
                "sourceUrlHost": urlparse(url).hostname or "",
                "createdAt": now_iso(),
                "lastSeenAt": now_iso(),
            }
            manifest_dirty = True
            url_cache[url] = target
        return target

    def collect_urls(value: Any, urls: set[str]) -> None:
        if isinstance(value, str):
            if is_feishu_media_url(value):
                urls.add(value)
            return
        if isinstance(value, list):
            for item in value:
                collect_urls(item, urls)
            return
        if isinstance(value, dict):
            for item in value.values():
                collect_urls(item, urls)

    def transform(value: Any) -> Any:
        if isinstance(value, str):
            return mirror(value) if is_feishu_media_url(value) else value
        if isinstance(value, list):
            return [transform(item) for item in value]
        if isinstance(value, dict):
            return {key: transform(item) for key, item in value.items()}
        return value

    if SYNC_SCOPE == "all":
        payloads: dict[str, Any] = {}
        urls: set[str] = set()
        for name in API_FILES:
            path = API_DIR / name
            original = path.read_text(encoding="utf-8")
            payload = json.loads(original)
            payloads[name] = payload
            collect_urls(payload, urls)
        print(
            f"Found {len(urls)} unique Feishu media URL(s); mirroring with {WORKERS} worker(s).",
            flush=True,
        )
        if urls:
            completed = 0
            with ThreadPoolExecutor(max_workers=WORKERS) as executor:
                futures = [executor.submit(mirror, url) for url in sorted(urls)]
                for future in as_completed(futures):
                    future.result()
                    completed += 1
                    if completed % 25 == 0 or completed == len(futures):
                        print(f"Mirrored {completed}/{len(futures)} Feishu media URL(s).", flush=True)
        for name, payload in payloads.items():
            path = API_DIR / name
            original = path.read_text(encoding="utf-8")
            updated = json.dumps(transform(payload), ensure_ascii=False, indent=2) + "\n"
            if updated != original:
                path.write_text(updated, encoding="utf-8")
                stats["changedFiles"] += 1

    if SYNC_MODE == "mirror":
        replacement_map: dict[str, str] = {}
        previous_local_urls: dict[str, list[str]] = {}
        for rel_path, entry in local_assets.items():
            if isinstance(entry, dict) and entry.get("r2Url"):
                previous_local_urls.setdefault(rel_path, []).append(str(entry["r2Url"]))

        for path in sorted((ROOT / "assets").rglob("*")):
            if not path.is_file() or path.suffix.lower() not in LOCAL_MEDIA_EXTENSIONS:
                continue
            stats["localScanned"] += 1
            body = path.read_bytes()
            digest = hashlib.sha256(body).hexdigest()
            rel_path = path.relative_to(ROOT).as_posix()
            content_type = content_type_for_path(path)
            key = f"{R2_LOCAL_MEDIA_PREFIX}/{digest[:2]}/{digest}{path.suffix.lower()}"
            actual_key = key
            target = public_url(public_base_url, key)
            existing = objects.get(digest)
            if isinstance(existing, dict) and existing.get("r2Key"):
                actual_key = str(existing["r2Key"])
                target = public_url(public_base_url, actual_key)
                stats["localReused"] += 1
            else:
                before_uploaded = stats["uploaded"]
                uploaded_target = ensure_r2_object(body, key=key, content_type=content_type)
                target = uploaded_target or target
                if stats["uploaded"] > before_uploaded:
                    stats["localUploaded"] += 1
                else:
                    stats["localReused"] += 1
                objects[digest] = {
                    "sha256": digest,
                    "size": len(body),
                    "contentType": content_type,
                    "r2Key": key,
                    "r2Url": target,
                    "source": "local-asset",
                    "createdAt": now_iso(),
                    "lastSeenAt": now_iso(),
                }
                manifest_dirty = True

            if local_assets.get(rel_path, {}).get("r2Url") != target:
                local_assets[rel_path] = {
                    "sha256": digest,
                    "size": len(body),
                    "contentType": content_type,
                    "r2Key": actual_key,
                    "r2Url": target,
                    "updatedAt": now_iso(),
                }
                manifest_dirty = True
            replacement_map[rel_path] = target
            replacement_map[f"./{rel_path}"] = target
            replacement_map[f"/{rel_path}"] = target
            for old_url in previous_local_urls.get(rel_path, []):
                replacement_map[old_url] = target

        if replacement_map:
            for path in sorted(ROOT.rglob("*")):
                if (
                    not path.is_file()
                    or path.suffix.lower() not in TEXT_EXTENSIONS
                    or should_skip_text_file(path)
                ):
                    continue
                original = path.read_text(encoding="utf-8")
                updated = original
                for source, target in sorted(replacement_map.items(), key=lambda item: len(item[0]), reverse=True):
                    if source.startswith("http"):
                        updated = updated.replace(source, target)
                        continue
                    pattern = re.compile(re.escape(source) + r"(?:\?[^\"'\s<>)]+)?")
                    updated = pattern.sub(target, updated)
                updated = updated.replace("./http://", "http://").replace("./https://", "https://")
                if updated != original:
                    path.write_text(updated, encoding="utf-8")
                    stats["localReferenceFilesChanged"] += 1

    cleanup_report_path: Path | None = None
    if R2_CLEANUP_MODE != "off":
        used_keys = collect_used_r2_keys(public_base_url)
        orphan_objects: list[dict[str, str]] = []
        orphan_local_assets: list[dict[str, str]] = []
        orphan_keys: set[str] = set()

        for digest, entry in objects.items():
            if not isinstance(entry, dict):
                continue
            key = str(entry.get("r2Key") or "")
            if key and key not in used_keys:
                orphan_keys.add(key)
                orphan_objects.append(
                    {
                        "sha256": str(entry.get("sha256") or digest),
                        "r2Key": key,
                        "r2Url": public_url(public_base_url, key),
                        "contentType": str(entry.get("contentType") or ""),
                        "source": str(entry.get("source") or entry.get("sourceUrlHost") or ""),
                    }
                )

        for rel_path, entry in local_assets.items():
            if not isinstance(entry, dict):
                continue
            key = str(entry.get("r2Key") or "")
            if key and key not in used_keys:
                orphan_keys.add(key)
                orphan_local_assets.append(
                    {
                        "path": str(rel_path),
                        "r2Key": key,
                        "r2Url": public_url(public_base_url, key),
                        "contentType": str(entry.get("contentType") or ""),
                    }
                )

        stats["orphanObjects"] = len(orphan_objects)
        stats["orphanLocalAssets"] = len(orphan_local_assets)
        stats["orphanUniqueKeys"] = len(orphan_keys)

        if R2_CLEANUP_MODE == "delete" and orphan_keys:
            deleted_keys: set[str] = set()
            for key in sorted(orphan_keys):
                try:
                    client.delete_object(Bucket=bucket, Key=key)
                    deleted_keys.add(key)
                    stats["orphanDeleted"] += 1
                except ClientError as error:
                    if is_missing_object(error):
                        deleted_keys.add(key)
                        stats["orphanDeleted"] += 1
                        continue
                    stats["orphanDeleteFailed"] += 1
                    cleanup_failures.append({"r2Key": key, "error": str(error)})

            if deleted_keys:
                for digest, entry in list(objects.items()):
                    if isinstance(entry, dict) and str(entry.get("r2Key") or "") in deleted_keys:
                        del objects[digest]
                        manifest_dirty = True
                for rel_path, entry in list(local_assets.items()):
                    if isinstance(entry, dict) and str(entry.get("r2Key") or "") in deleted_keys:
                        del local_assets[rel_path]
                        manifest_dirty = True

        REPORTS_DIR.mkdir(exist_ok=True)
        cleanup_report = {
            "generatedAt": now_iso(),
            "mode": R2_CLEANUP_MODE,
            "bucket": bucket,
            "publicBaseUrl": public_base_url,
            "usedKeyCount": len(used_keys),
            "orphanUniqueKeyCount": len(orphan_keys),
            "deletedCount": stats["orphanDeleted"],
            "deleteFailedCount": stats["orphanDeleteFailed"],
            "orphanObjects": orphan_objects,
            "orphanLocalAssets": orphan_local_assets,
            "failures": cleanup_failures,
        }
        cleanup_report_path = REPORTS_DIR / f"r2-orphans-{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.json"
        save_json(cleanup_report_path, cleanup_report)

    report_path: Path | None = None
    if SYNC_MODE == "mirror" or manifest_dirty:
        manifest["generatedAt"] = now_iso()
        manifest["mode"] = SYNC_MODE
        manifest["cleanupMode"] = R2_CLEANUP_MODE
        save_json(MANIFEST_FILE, manifest)

        REPORTS_DIR.mkdir(exist_ok=True)
        report = {
            "generatedAt": now_iso(),
            "mode": SYNC_MODE,
            "scope": SYNC_SCOPE,
            "bucket": bucket,
            "publicBaseUrl": public_base_url,
            "r2Prefix": R2_PREFIX,
            "r2LocalMediaPrefix": R2_LOCAL_MEDIA_PREFIX,
            "stats": stats,
            "failures": failures,
            "cleanupFailures": cleanup_failures,
            "cleanupReport": str(cleanup_report_path.relative_to(ROOT)) if cleanup_report_path else "",
            "manifestFile": str(MANIFEST_FILE.relative_to(ROOT)),
            "apiFiles": list(API_FILES),
        }
        report_path = REPORTS_DIR / f"r2-media-sync-{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.json"
        save_json(report_path, report)

    print(
        "R2 media mirror complete: "
        f"{stats['changedFiles']} JSON file(s), {stats['downloaded']} download(s), "
        f"{stats['uploaded']} upload(s), {stats['reused']} reused object(s), "
        f"{stats['pending']} pending manual mirror(s), {stats['failed']} failure(s), "
        f"{stats['orphanUniqueKeys']} orphan R2 object(s) found, {stats['orphanDeleted']} deleted."
    )
    if report_path:
        print(f"Report: {report_path.relative_to(ROOT)}")
    if cleanup_report_path:
        print(f"Cleanup report: {cleanup_report_path.relative_to(ROOT)}")
    if failures:
        print("Some Feishu media URLs could not be downloaded; see the report for details.")


if __name__ == "__main__":
    main()
