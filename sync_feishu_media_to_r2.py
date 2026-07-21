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
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import boto3
import requests
from botocore.config import Config
from botocore.exceptions import ClientError


ROOT = Path(__file__).resolve().parent
API_DIR = ROOT / "api"
REPORTS_DIR = ROOT / "reports"
API_FILES = ("portfolio.json", "clients.json", "zhixing.json", "curation.json")
MANIFEST_FILE = API_DIR / "r2-media-manifest.json"
R2_PREFIX = os.environ.get("R2_MEDIA_PREFIX", "feishu-media").strip("/") or "feishu-media"
R2_LOCAL_MEDIA_PREFIX = os.environ.get("R2_LOCAL_MEDIA_PREFIX", "site-media").strip("/") or "site-media"
SYNC_MODE = os.environ.get("R2_SYNC_MODE", "mirror").strip().lower() or "mirror"
SYNC_SCOPE = os.environ.get("R2_SYNC_SCOPE", "all").strip().lower() or "all"
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


def main() -> None:
    if SYNC_MODE not in {"mirror", "reuse"}:
        raise SystemExit("R2_SYNC_MODE must be either 'mirror' or 'reuse'")
    if SYNC_SCOPE not in {"all", "local_videos"}:
        raise SystemExit("R2_SYNC_SCOPE must be either 'all' or 'local_videos'")

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
    }
    failures: list[dict[str, str]] = []

    def ensure_r2_object(body: bytes, *, key: str, content_type: str) -> str:
        nonlocal manifest_dirty
        target = public_url(public_base_url, key)
        try:
            client.head_object(Bucket=bucket, Key=key)
            stats["reused"] += 1
        except ClientError as error:
            if not is_missing_object(error):
                raise
            if SYNC_MODE == "reuse":
                stats["pending"] += 1
                return ""
            client.put_object(
                Bucket=bucket,
                Key=key,
                Body=body,
                ContentType=content_type,
                CacheControl="public, max-age=31536000, immutable",
            )
            stats["uploaded"] += 1
            manifest_dirty = True
        return target

    def mirror(url: str) -> str:
        nonlocal manifest_dirty
        stats["scanned"] += 1
        if url in url_cache:
            return url_cache[url]

        try:
            response = requests.get(url, timeout=90)
            response.raise_for_status()
            body = response.content
        except Exception as exc:
            stats["failed"] += 1
            failures.append({"url": url, "error": str(exc)})
            url_cache[url] = url
            return url

        if not body:
            raise RuntimeError("Feishu returned an empty media response")
        stats["downloaded"] += 1

        digest = hashlib.sha256(body).hexdigest()
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
            url_cache[url] = url
            return url

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

    def transform(value: Any) -> Any:
        if isinstance(value, str):
            return mirror(value) if is_feishu_media_url(value) else value
        if isinstance(value, list):
            return [transform(item) for item in value]
        if isinstance(value, dict):
            return {key: transform(item) for key, item in value.items()}
        return value

    if SYNC_SCOPE == "all":
        for name in API_FILES:
            path = API_DIR / name
            original = path.read_text(encoding="utf-8")
            updated = json.dumps(transform(json.loads(original)), ensure_ascii=False, indent=2) + "\n"
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

    report_path: Path | None = None
    if SYNC_MODE == "mirror" or manifest_dirty:
        manifest["generatedAt"] = now_iso()
        manifest["mode"] = SYNC_MODE
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
            "manifestFile": str(MANIFEST_FILE.relative_to(ROOT)),
            "apiFiles": list(API_FILES),
        }
        report_path = REPORTS_DIR / f"r2-media-sync-{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.json"
        save_json(report_path, report)

    print(
        "R2 media mirror complete: "
        f"{stats['changedFiles']} JSON file(s), {stats['downloaded']} download(s), "
        f"{stats['uploaded']} upload(s), {stats['reused']} reused object(s), "
        f"{stats['pending']} pending manual mirror(s), {stats['failed']} failure(s)."
    )
    if report_path:
        print(f"Report: {report_path.relative_to(ROOT)}")
    if failures:
        print("Some Feishu media URLs could not be downloaded; see the report for details.")


if __name__ == "__main__":
    main()
