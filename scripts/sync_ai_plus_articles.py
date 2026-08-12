#!/usr/bin/env python3
"""Sync AI++ Feishu docx articles into api/ai-plus-articles.json.

This script is separate from refresh.py. It reuses stable helper functions from
refresh.py without changing the main portfolio/zhixing sync flow.
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import refresh


CONTENT_PATH = ROOT / "api" / "ai-plus-content.json"
OUTPUT_PATH = ROOT / "api" / "ai-plus-articles.json"

MANUAL_ARTICLE_VIDEOS: dict[str, list[dict[str, str]]] = {
    "open-models.case.001": [
        {
            "filename": "LTX23-20260521165107_00001_.mp4",
            "url": "assets/ai-plus-ltx-single.mp4",
            "text": "LTX-2.3 单图生成视频测试",
        },
        {
            "filename": "LTX23-20260526151852_00001_.mp4",
            "url": "assets/ai-plus-ltx-two-shot.mp4",
            "text": "LTX-2.3 双图生成视频测试",
        },
    ],
}


def looks_like_feishu_docx(url: str) -> bool:
    return "my.feishu.cn/docx/" in str(url) or "feishu.cn/docx/" in str(url)


def is_video_url(url: str) -> bool:
    return str(url).lower().split("?", 1)[0].endswith((".mp4", ".webm", ".ogg", ".mov"))


def media_filename(url: str) -> str:
    return str(url).split("?", 1)[0].rstrip("/").rsplit("/", 1)[-1].lower()


def media_block_references(body: str, media_urls: list[str]) -> list[dict[str, Any]]:
    """Add a safe fallback when a Feishu doc references uploaded video files as text.

    Some Feishu docx exports surface attachment filenames in paragraph text while
    the corresponding download URLs are only available in mediaTokens. If a media
    URL is a video and its filename appears in the body, render it as a video
    block near the end rather than losing it completely.
    """

    lowered_body = body.lower()
    referenced: list[dict[str, Any]] = []
    seen: set[str] = set()
    for url in media_urls:
        if not is_video_url(url):
            continue
        filename = media_filename(url)
        if not filename or filename in seen:
            continue
        if filename in lowered_body or re.search(re.escape(filename.replace("_", " ")), lowered_body):
            referenced.append({"type": "video", "url": url, "text": filename})
            seen.add(filename)
    return referenced


def inject_manual_videos(article_key: str, body: str, content_blocks: list[dict[str, Any]], media: list[str]) -> None:
    """Render known local videos when Feishu exposes only attachment filenames.

    Feishu docx can sometimes return video attachments as plain filename text
    instead of media blocks. The files still need to be rendered in the article,
    so we insert stable local asset references; the R2 mirror workflow replaces
    them with Cloudflare URLs after upload.
    """

    videos = MANUAL_ARTICLE_VIDEOS.get(article_key, [])
    if not videos:
        return
    lowered_body = body.lower()
    existing_urls = {str(block.get("url") or "") for block in content_blocks if isinstance(block, dict)}
    existing_urls.update(str(item) for item in media)
    for item in videos:
        filename = item["filename"]
        filename_lower = filename.lower()
        if filename_lower not in lowered_body:
            continue
        url = item["url"]
        if url in existing_urls:
            continue
        inserted = False
        for index, block in enumerate(list(content_blocks)):
            if filename_lower in str(block.get("text") or "").lower():
                content_blocks.insert(index + 1, {"type": "video", "url": url, "text": item.get("text") or filename})
                inserted = True
                break
        if not inserted:
            content_blocks.append({"type": "video", "url": url, "text": item.get("text") or filename})
        media.append(url)
        existing_urls.add(url)


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


def text_blocks(blocks: list[dict[str, Any]]) -> list[str]:
    values: list[str] = []
    for block in blocks:
        if not isinstance(block, dict):
            continue
        if block.get("type") not in {"paragraph", "heading", "list_item", "quote"}:
            continue
        text = str(block.get("text") or "").strip()
        if text:
            values.append(text)
    return values


def derive_doc_title(fallback: str, body: str, blocks: list[dict[str, Any]]) -> str:
    for text in text_blocks(blocks):
        cleaned = text.strip()
        if cleaned:
            return cleaned[:80]
    first_line = next((line.strip() for line in body.splitlines() if line.strip()), "")
    return (first_line or fallback or "AI++ 文章")[:80]


def derive_summary(fallback: str, body: str, blocks: list[dict[str, Any]], title: str) -> str:
    candidates = text_blocks(blocks)
    if not candidates:
        candidates = [line.strip() for line in body.splitlines() if line.strip()]
    normalized_title = title.strip()
    filtered: list[str] = []
    seen: set[str] = set()
    for text in candidates:
        cleaned = re.sub(r"\s+", " ", text).strip()
        if not cleaned or cleaned == normalized_title:
            continue
        if cleaned in seen:
            continue
        if re.match(r"^(图|截图)\s*\d*[:：]", cleaned):
            continue
        seen.add(cleaned)
        filtered.append(cleaned)
    summary = " ".join(filtered[:2]).strip()
    if len(summary) > 180:
        summary = summary[:177].rstrip() + "..."
    return summary or fallback or body[:160]


def sync_article(token: str, record: dict[str, Any]) -> dict[str, Any]:
    fallback_title = str(record.get("title") or "AI++ 文章").strip()
    url = str(record.get("linkUrl") or "").strip()
    record_cover = str(record.get("cover") or "").strip()
    linked = refresh.fetch_feishu_doc_content(token, url) if url else {}
    body = str(linked.get("body") or record.get("body") or "").strip()
    raw_blocks = linked.get("rawBlocks") if isinstance(linked.get("rawBlocks"), list) else []
    content_blocks: list[dict[str, Any]] = []
    media: list[str] = []
    if raw_blocks:
        content_blocks = refresh.build_doc_content_blocks(raw_blocks, fallback_title)
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
    article_key = str(record.get("key") or record.get("id") or "")
    if not content_blocks and body:
        content_blocks = [{"type": "paragraph", "text": paragraph} for paragraph in body.splitlines() if paragraph.strip()]
    else:
        existing_urls = {str(block.get("url") or "") for block in content_blocks if isinstance(block, dict)}
        for block in media_block_references(body, media):
            if block["url"] not in existing_urls:
                content_blocks.append(block)
    inject_manual_videos(article_key, body, content_blocks, media)
    title = derive_doc_title(fallback_title, body, content_blocks)
    summary = derive_summary(str(record.get("body") or "").strip(), body, content_blocks, title)
    return {
        "id": record.get("key") or record.get("id"),
        "key": record.get("key") or record.get("id"),
        "pageKey": record.get("pageKey"),
        "pageName": record.get("pageName"),
        "pagePath": record.get("pagePath"),
        "section": record.get("section"),
        "title": title,
        "summary": summary,
        "body": body,
        "contentUrl": url,
        "sourceRecordId": record.get("recordId"),
        "linkedError": linked.get("error", ""),
        "media": media,
        "contentBlocks": content_blocks,
        "cover": record_cover or next((item for item in media if not is_video_url(item)), media[0] if media else ""),
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
