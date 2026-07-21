#!/usr/bin/env python3
"""Mirror temporary Feishu media URLs in generated API JSON to Tencent COS.

This script is deliberately separate from refresh.py.  refresh.py remains the
single source of truth for reading Feishu; this file only turns the resulting
temporary attachment URLs into stable COS public URLs.
"""
from __future__ import annotations

import hashlib
import json
import mimetypes
import os
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests
from qcloud_cos import CosConfig, CosS3Client
from qcloud_cos.cos_exception import CosServiceError


ROOT = Path(__file__).resolve().parent
API_FILES = ("portfolio.json", "clients.json", "zhixing.json", "curation.json")
COS_PREFIX = os.environ.get("COS_MEDIA_PREFIX", "feishu-media").strip("/") or "feishu-media"
SYNC_MODE = os.environ.get("COS_SYNC_MODE", "mirror").strip().lower() or "mirror"


def require(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise SystemExit(f"Missing required environment variable: {name}")
    return value


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
    url_cache: dict[str, str] = {}
    content_cache: dict[str, str] = {}
    stats = {"downloaded": 0, "uploaded": 0, "reused": 0, "pending": 0}

    def mirror(url: str) -> str:
        if url in url_cache:
            return url_cache[url]

        response = requests.get(url, timeout=90)
        response.raise_for_status()
        body = response.content
        if not body:
            raise RuntimeError("Feishu returned an empty media response")
        stats["downloaded"] += 1

        digest = hashlib.sha256(body).hexdigest()
        if digest in content_cache:
            url_cache[url] = content_cache[digest]
            return content_cache[digest]

        content_type = response.headers.get("Content-Type", "application/octet-stream")
        key = f"{COS_PREFIX}/{digest[:2]}/{digest}{extension_for(content_type, url)}"
        target = public_url(endpoint, key)
        try:
            client.head_object(Bucket=bucket, Key=key)
            stats["reused"] += 1
        except CosServiceError as error:
            if error.get_status_code() != 404:
                raise
            if SYNC_MODE == "reuse":
                # During scheduled Feishu refreshes, keep new media on its
                # temporary source URL until the owner manually mirrors it.
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

        url_cache[url] = target
        content_cache[digest] = target
        return target

    def transform(value: Any) -> Any:
        if isinstance(value, str):
            return mirror(value) if is_feishu_media_url(value) else value
        if isinstance(value, list):
            return [transform(item) for item in value]
        if isinstance(value, dict):
            return {key: transform(item) for key, item in value.items()}
        return value

    changed_files = 0
    for name in API_FILES:
        path = ROOT / "api" / name
        original = path.read_text(encoding="utf-8")
        updated = json.dumps(transform(json.loads(original)), ensure_ascii=False, indent=2) + "\n"
        if updated != original:
            path.write_text(updated, encoding="utf-8")
            changed_files += 1

    print(
        "COS media mirror complete: "
        f"{changed_files} JSON file(s), {stats['downloaded']} download(s), "
        f"{stats['uploaded']} upload(s), {stats['reused']} existing object(s), "
        f"{stats['pending']} pending manual mirror(s)."
    )


if __name__ == "__main__":
    main()
