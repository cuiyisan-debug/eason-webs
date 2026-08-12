#!/usr/bin/env python3
"""Sync AI++ Feishu docx articles into api/ai-plus-articles.json.

This script is separate from refresh.py. It reuses stable helper functions from
refresh.py without changing the main portfolio/zhixing sync flow.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import refresh


CONTENT_PATH = ROOT / "api" / "ai-plus-content.json"
OUTPUT_PATH = ROOT / "api" / "ai-plus-articles.json"


def looks_like_feishu_docx(url: str) -> bool:
    return "my.feishu.cn/docx/" in str(url) or "feishu.cn/docx/" in str(url)


def is_video_url(url: str) -> bool:
    return str(url).lower().split("?", 1)[0].endswith((".mp4", ".webm", ".ogg", ".mov"))


def content_records() -> list[dict[str, Any]]:
    if not CONTENT_PATH.exists():
        return []
    payload = json.loads(CONTENT_PATH.read_text(encoding="utf-8"))
    records: list[dict[str, Any]] = []
    for page_key, page in (payload.get("pages") or {}).items():
        for record in page.get("records") or []:
            link = str(record.get("linkUrl") or "").strip()
            if not link or not looks_like_feishu_docx(link):
                continue
            records.append({**record, "pageKey": page_key})
    return records


def sync_article(token: str, record: dict[str, Any]) -> dict[str, Any]:
    title = str(record.get("title") or "AI++ 文章").strip()
    url = str(record.get("linkUrl") or "").strip()
    linked = refresh.fetch_feishu_doc_content(token, url) if url else {}
    body = str(linked.get("body") or record.get("body") or "").strip()
    raw_blocks = linked.get("rawBlocks") if isinstance(linked.get("rawBlocks"), list) else []
    content_blocks: list[dict[str, Any]] = []
    media: list[str] = []
    if raw_blocks:
        content_blocks = refresh.build_doc_content_blocks(raw_blocks, title)
    doc_tokens = linked.get("mediaTokens") if isinstance(linked.get("mediaTokens"), list) else []
    doc_urls: dict[str, str] = {}
    if doc_tokens:
        doc_urls = refresh.resolve_urls_best_effort(token, [str(item) for item in doc_tokens], use_bitable_extra=False)
        media = [url for token_id, url in doc_urls.items() if token_id in doc_tokens]
        for block in content_blocks:
            if block.get("type") == "image":
                image_token = str(block.get("token") or "")
                resolved = doc_urls.get(image_token, "")
                block["url"] = resolved
                if resolved and is_video_url(resolved):
                    block["type"] = "video"
    if not content_blocks and body:
        content_blocks = [{"type": "paragraph", "text": paragraph} for paragraph in body.splitlines() if paragraph.strip()]
    return {
        "id": record.get("key") or record.get("id"),
        "key": record.get("key") or record.get("id"),
        "pageKey": record.get("pageKey"),
        "pageName": record.get("pageName"),
        "pagePath": record.get("pagePath"),
        "section": record.get("section"),
        "title": title,
        "summary": record.get("body") or body[:160],
        "body": body,
        "contentUrl": url,
        "sourceRecordId": record.get("recordId"),
        "linkedError": linked.get("error", ""),
        "media": media,
        "contentBlocks": content_blocks,
        "cover": next((item for item in media if not is_video_url(item)), media[0] if media else ""),
    }


def main() -> int:
    if not os.environ.get("LARK_ACCESS_TOKEN") and (
        not os.environ.get("LARK_APP_ID") or not os.environ.get("LARK_APP_SECRET")
    ):
        raise RuntimeError("Missing LARK_APP_ID/LARK_APP_SECRET or LARK_ACCESS_TOKEN")
    token = refresh.access_token()
    records = content_records()
    articles = [sync_article(token, record) for record in records]
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "source": "ai-plus-feishu-docx",
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "articles": articles,
    }
    OUTPUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        "AI_PLUS_ARTICLE_SYNC="
        + json.dumps(
            {
                "output": str(OUTPUT_PATH.relative_to(ROOT)),
                "articles": len(articles),
                "ids": [item.get("id") for item in articles],
                "warnings": [item["linkedError"] for item in articles if item.get("linkedError")],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
