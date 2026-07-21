#!/usr/bin/env python3
"""Deploy the static website files to Tencent COS.

The script uploads only changed files by comparing local MD5 values with COS
object ETags when possible. Secrets are read from environment variables.
"""
from __future__ import annotations

import hashlib
import json
import mimetypes
import os
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

from qcloud_cos import CosConfig, CosS3Client
from qcloud_cos.cos_exception import CosServiceError


ROOT = Path(__file__).resolve().parent
REPORTS_DIR = ROOT / "reports"
SITE_PREFIX = os.environ.get("COS_SITE_PREFIX", "").strip("/")

EXCLUDED_DIRS = {
    ".git",
    ".github",
    ".playwright-cli",
    "__pycache__",
    "docs",
    "reports",
    "test-results",
    "temp-video-previews",
}
EXCLUDED_NAMES = {
    ".env",
    ".env.local",
    ".env.production",
    "deploy_site_to_cos.py",
}
EXCLUDED_PREFIXES = (
    ".codex-",
    ".tmp-",
    "temp-",
)
INCLUDED_SUFFIXES = {
    ".html",
    ".css",
    ".js",
    ".json",
    ".svg",
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".gif",
    ".ico",
    ".mp4",
    ".webm",
    ".txt",
    ".xml",
}


def require(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise SystemExit(f"Missing required environment variable: {name}")
    return value


def should_include(path: Path) -> bool:
    rel = path.relative_to(ROOT)
    parts = rel.parts
    if any(part in EXCLUDED_DIRS for part in parts[:-1]):
        return False
    name = path.name
    if name in EXCLUDED_NAMES or any(name.startswith(prefix) for prefix in EXCLUDED_PREFIXES):
        return False
    return path.is_file() and (path.suffix.lower() in INCLUDED_SUFFIXES or name == "CNAME")


def object_key(path: Path) -> str:
    rel = path.relative_to(ROOT).as_posix()
    return str(PurePosixPath(SITE_PREFIX) / rel) if SITE_PREFIX else rel


def file_md5(path: Path) -> str:
    digest = hashlib.md5()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def cache_control(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".html", ".json", ".xml", ".txt"}:
        return "public, max-age=60"
    return "public, max-age=31536000"


def content_type(path: Path) -> str:
    guessed, _ = mimetypes.guess_type(path.name)
    return guessed or "application/octet-stream"


def remote_matches(client: CosS3Client, bucket: str, key: str, path: Path, md5: str) -> bool:
    try:
        meta = client.head_object(Bucket=bucket, Key=key)
    except CosServiceError as error:
        if error.get_status_code() == 404:
            return False
        raise
    etag = str(meta.get("ETag", "")).strip('"').lower()
    length = int(meta.get("Content-Length", -1))
    return etag == md5 and length == path.stat().st_size


def main() -> None:
    secret_id = require("TENCENT_SECRET_ID")
    secret_key = require("TENCENT_SECRET_KEY")
    bucket = require("COS_BUCKET")
    region = require("COS_REGION")
    endpoint = os.environ.get("COS_PUBLIC_BASE_URL", "").strip()
    if not endpoint:
        endpoint = f"https://{bucket}.cos.{region}.myqcloud.com"

    client = CosS3Client(CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key))
    files = sorted(path for path in ROOT.rglob("*") if should_include(path))
    stats = {"scanned": len(files), "uploaded": 0, "skipped": 0, "failed": 0}
    failures: list[dict[str, str]] = []

    for path in files:
        key = object_key(path)
        md5 = file_md5(path)
        try:
            if remote_matches(client, bucket, key, path, md5):
                stats["skipped"] += 1
                continue
            with path.open("rb") as handle:
                client.put_object(
                    Bucket=bucket,
                    Key=key,
                    Body=handle,
                    ContentType=content_type(path),
                    CacheControl=cache_control(path),
                )
            stats["uploaded"] += 1
        except Exception as exc:
            stats["failed"] += 1
            failures.append({"file": path.relative_to(ROOT).as_posix(), "key": key, "error": str(exc)})

    REPORTS_DIR.mkdir(exist_ok=True)
    report = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "bucket": bucket,
        "region": region,
        "publicBaseUrl": endpoint,
        "sitePrefix": SITE_PREFIX,
        "stats": stats,
        "failures": failures,
    }
    report_path = REPORTS_DIR / f"cos-site-deploy-{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        "COS site deploy complete: "
        f"{stats['scanned']} file(s), {stats['uploaded']} uploaded, "
        f"{stats['skipped']} skipped, {stats['failed']} failure(s)."
    )
    print(f"Report: {report_path.relative_to(ROOT)}")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
