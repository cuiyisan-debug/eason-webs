#!/usr/bin/env python3
"""Mirror temporary Feishu media URLs in generated API JSON to Tencent COS.

refresh.py remains the single source of truth for reading Feishu. This script
only turns generated temporary attachment URLs into stable COS public URLs.
It uploads by content hash, so unchanged media is reused instead of re-uploaded.
"""
from __future__ import annotations

import hashlib
import json
import mimetypes
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests
from qcloud_cos import CosConfig, CosS3Client
from qcloud_cos.cos_exception import CosServiceError


ROOT = Path(__file__).resolve().parent
API_DIR = ROOT / "api"
REPORTS_DIR = ROOT / "reports"
API_FILES = ("portfolio.json", "clients.json", "zhixing.json", "curation.json")
MANIFEST_FILE = API_DIR / "media-manifest.json"
COS_PREFIX = os.environ.get("COS_MEDIA_PREFIX", "feishu-media").strip("/") or "feishu-media"
SYNC_MODE = os.environ.get("COS_SYNC_MODE", "mirror").strip().lower() or "mirror"


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


def load_manifest(endpoint: str) -> dict[str, Any]:
    if not MANIFEST_FILE.exists():
        return {
            "schemaVersion": 1,
            "generatedAt": now_iso(),
            "cosPrefix": COS_PREFIX,
            "publicBaseUrl": endpoint,
            "objects": {},
        }
    try:
        data = json.loads(MANIFEST_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        data = {}
    if not isinstance(data, dict):
        data = {}
    data.setdefault("schemaVersion", 1)
    data.setdefault("objects", {})
    data["cosPrefix"] = COS_PREFIX
    data["publicBaseUrl"] = endpoint
    return data


def save_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    if SYNC_MODE not in {"mirror", "reuse"}:
        raise SystemExit("COS_SYNC_MODE must be either 'mirror' or 'reuse'")
    secret_id = require("TENCENT_SECRET_ID")
    secret_key = require("TENCENT_SECRET_KEY")
    bucket = require("COS_BUCKET")
    region = require("COS_REGION")
    endpoint = os.environ.get("COS_PUBLIC_BASE_URL", "").strip()
    if not endpoint:
        endpoint = f"https://{bucket}.cos.{region}.myqcloud.com"

    client = CosS3Client(CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key))
    manifest = load_manifest(endpoint)
    objects: dict[str, Any] = manifest.setdefault("objects", {})
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
    }
    failures: list[dict[str, str]] = []

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
            if SYNC_MODE == "reuse":
                url_cache[url] = url
                return url
            raise

        if not body:
            raise RuntimeError("Feishu returned an empty media response")
        stats["downloaded"] += 1

        digest = hashlib.sha256(body).hexdigest()
        content_type = response.headers.get("Content-Type", "application/octet-stream")
        existing = objects.get(digest)
        if isinstance(existing, dict) and existing.get("cosKey"):
            stats["reused"] += 1
            target = public_url(endpoint, str(existing["cosKey"]))
            if existing.get("cosUrl") != target:
                existing["cosUrl"] = target
                manifest_dirty = True
            url_cache[url] = target
            return target

        key = f"{COS_PREFIX}/{digest[:2]}/{digest}{extension_for(content_type, url)}"
        target = public_url(endpoint, key)
        try:
            client.head_object(Bucket=bucket, Key=key)
            stats["reused"] += 1
        except CosServiceError as error:
            if error.get_status_code() != 404:
                raise
            if SYNC_MODE == "reuse":
                stats["pending"] += 1
                url_cache[url] = url
                return url
            client.put_object(
                Bucket=bucket,
                Key=key,
                Body=body,
                ContentType=content_type.split(";", 1)[0],
                CacheControl="public, max-age=31536000, immutable",
            )
            stats["uploaded"] += 1

        objects[digest] = {
            "sha256": digest,
            "size": len(body),
            "contentType": content_type.split(";", 1)[0],
            "cosKey": key,
            "cosUrl": target,
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

    for name in API_FILES:
        path = API_DIR / name
        original = path.read_text(encoding="utf-8")
        updated = json.dumps(transform(json.loads(original)), ensure_ascii=False, indent=2) + "\n"
        if updated != original:
            path.write_text(updated, encoding="utf-8")
            stats["changedFiles"] += 1

    report_path: Path | None = None
    if SYNC_MODE == "mirror" or manifest_dirty:
        manifest["generatedAt"] = now_iso()
        manifest["mode"] = SYNC_MODE
        save_json(MANIFEST_FILE, manifest)

        REPORTS_DIR.mkdir(exist_ok=True)
        report = {
            "generatedAt": now_iso(),
            "mode": SYNC_MODE,
            "bucket": bucket,
            "region": region,
            "publicBaseUrl": endpoint,
            "cosPrefix": COS_PREFIX,
            "stats": stats,
            "failures": failures,
            "manifestFile": str(MANIFEST_FILE.relative_to(ROOT)),
            "apiFiles": list(API_FILES),
        }
        report_path = REPORTS_DIR / f"cos-media-sync-{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.json"
        save_json(report_path, report)

    print(
        "COS media mirror complete: "
        f"{stats['changedFiles']} JSON file(s), {stats['downloaded']} download(s), "
        f"{stats['uploaded']} upload(s), {stats['reused']} reused object(s), "
        f"{stats['pending']} pending manual mirror(s), {stats['failed']} failure(s)."
    )
    if report_path:
        print(f"Report: {report_path.relative_to(ROOT)}")

    if failures and SYNC_MODE == "mirror":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
