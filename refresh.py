#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
API_DIR = ROOT / "api"
PORTFOLIO_FILE = API_DIR / "portfolio.json"
ZHIXING_FILE = API_DIR / "zhixing.json"
CURATION_FILE = API_DIR / "curation.json"

APP_ID = os.environ.get("LARK_APP_ID", "").strip()
APP_SECRET = os.environ.get("LARK_APP_SECRET", "").strip()
ACCESS_TOKEN = os.environ.get("LARK_ACCESS_TOKEN", "").strip()
BASE_TOKEN = os.environ.get("LARK_BASE_TOKEN", "").strip()
TABLE_ID = os.environ.get("LARK_TABLE_ID", "").strip()
ZHIXING_BASE_TOKEN = os.environ.get("LARK_ZHIXING_BASE_TOKEN", "Vn7hbNMygaDrSMseVgycCCJen1e").strip()
ZHIXING_TABLE_ID = os.environ.get("LARK_ZHIXING_TABLE_ID", "").strip()
CURATION_BASE_TOKEN = os.environ.get("LARK_CURATION_BASE_TOKEN", "CtqgbzQHVazUyhsSiOEcIrxfnSd").strip()
CURATION_TABLE_ID = os.environ.get("LARK_CURATION_TABLE_ID", "").strip()

FIELD_TITLE = os.environ.get("LARK_FIELD_TITLE", "项目名称")
FIELD_CATEGORY = os.environ.get("LARK_FIELD_CATEGORY", "前台分类")
FIELD_SUMMARY = os.environ.get("LARK_FIELD_SUMMARY", "项目简介")
FIELD_IMAGES = os.environ.get("LARK_FIELD_IMAGES", "图片")
FIELD_COVER = os.environ.get("LARK_FIELD_COVER", "封面")
FIELD_YEAR = os.environ.get("LARK_FIELD_YEAR", "年份")
FIELD_FEATURED = os.environ.get("LARK_FIELD_FEATURED", "首页轮播")
FIELD_VIDEO_URL = os.environ.get("LARK_FIELD_VIDEO_URL", "视频链接")
FIELD_VIDEO_BV = os.environ.get("LARK_FIELD_VIDEO_BV", "视频BV号")
FIELD_ROLE = os.environ.get("LARK_FIELD_ROLE", "角色")
FIELD_TAGS = os.environ.get("LARK_FIELD_TAGS", "二级标签")
FIELD_STATUS = os.environ.get("LARK_FIELD_STATUS", "项目状态")
FIELD_ORDER = os.environ.get("LARK_FIELD_ORDER", "序号")

CATEGORIES = ["政企展厅", "品牌空间", "文博展陈", "文旅体验", "大型展会", "临展活动", "其他创意"]
BATCH_SIZE = 5
ZHIXING_TITLE_FIELDS = ["标题", "文章标题", "名称", "主题", "Title", "title"]
ZHIXING_SUMMARY_FIELDS = ["简介", "摘要", "说明", "描述", "Summary", "summary"]
ZHIXING_BODY_FIELDS = ["正文", "正文内容", "内容", "详细内容", "文章内容", "文章正文", "全文", "Body", "body", "Content", "content"]
ZHIXING_LINK_FIELDS = ["正文链接", "文章链接", "原文链接", "外部链接", "链接", "URL", "url", "Link", "link"]
ARTICLE_COVER_FIELDS = ["封面图", "封面图片", "封面", "Cover", "cover"]
ZHIXING_MEDIA_FIELDS = ["附件", "图片", "视频", "媒体", "素材"]
ARTICLE_ORDER_FIELDS = ["附件顺序", "图片顺序", "媒体顺序"]


def fail(message: str) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(1)


def require_env() -> None:
    missing = [
        name
        for name, value in (("LARK_BASE_TOKEN", BASE_TOKEN), ("LARK_TABLE_ID", TABLE_ID))
        if not value
    ]
    if not ACCESS_TOKEN:
        missing.extend(
            name
            for name, value in (("LARK_APP_ID", APP_ID), ("LARK_APP_SECRET", APP_SECRET))
            if not value
        )
    if missing:
        fail("Missing required environment variables: " + ", ".join(missing))


def request_json(url: str, *, data: dict[str, Any] | None = None, token: str | None = None) -> dict[str, Any]:
    headers = {"Content-Type": "application/json; charset=utf-8"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    payload = None if data is None else json.dumps(data, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=90) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "ignore")
        fail(f"HTTP {exc.code} calling {url}: {body}")
    except urllib.error.URLError as exc:
        fail(f"Request failed for {url}: {exc}")


def tenant_access_token() -> str:
    res = request_json(
        "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
        data={"app_id": APP_ID, "app_secret": APP_SECRET},
    )
    if res.get("code") != 0 or not res.get("tenant_access_token"):
        fail(f"Failed to get tenant token: {json.dumps(res, ensure_ascii=False)}")
    return str(res["tenant_access_token"])


def access_token() -> str:
    if ACCESS_TOKEN:
        return ACCESS_TOKEN
    return tenant_access_token()


def list_tables(token: str, base_token: str) -> list[dict[str, Any]]:
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{base_token}/tables"
    res = request_json(url, token=token)
    if res.get("code") != 0:
        fail(f"Failed to fetch tables: {json.dumps(res, ensure_ascii=False)}")
    return res.get("data", {}).get("items", [])


def fetch_records(token: str, *, base_token: str = BASE_TOKEN, table_id: str = TABLE_ID) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    page_token = ""
    while True:
        params = {"page_size": 500}
        if page_token:
            params["page_token"] = page_token
        url = (
            f"https://open.feishu.cn/open-apis/bitable/v1/apps/{base_token}/tables/{table_id}/records?"
            + urllib.parse.urlencode(params)
        )
        res = request_json(url, token=token)
        if res.get("code") != 0:
            fail(f"Failed to fetch records: {json.dumps(res, ensure_ascii=False)}")
        data = res.get("data", {})
        records.extend(data.get("items", []))
        if not data.get("has_more"):
            break
        page_token = data.get("page_token", "")
        if not page_token:
            break
    return records


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (int, float)):
        return str(int(value)) if isinstance(value, float) and value.is_integer() else str(value)
    if isinstance(value, dict):
        for key in ("text", "name", "value"):
            if isinstance(value.get(key), str):
                return value[key].strip()
        return ""
    if isinstance(value, list):
        parts = [normalize_text(item) for item in value]
        return ", ".join(part for part in parts if part)
    return str(value).strip()


def first_field(fields: dict[str, Any], names: list[str]) -> Any:
    for name in names:
        if name in fields:
            return fields.get(name)
    lower_map = {str(key).strip().lower(): key for key in fields}
    for name in names:
        key = lower_map.get(name.lower())
        if key:
            return fields.get(key)
    return None


def normalize_url(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        for key in ("link", "url", "href", "text"):
            text = normalize_url(value.get(key))
            if text.startswith(("http://", "https://")):
                return text
    if isinstance(value, list):
        for item in value:
            text = normalize_url(item)
            if text.startswith(("http://", "https://")):
                return text
    text = normalize_text(value)
    return text if text.startswith(("http://", "https://")) else ""


def normalize_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [text for text in (normalize_text(item) for item in value) if text]
    text = normalize_text(value)
    if not text:
        return []
    return [part.strip() for part in text.replace("；", ";").replace("，", ";").replace(",", ";").split(";") if part.strip()]


def attachment_tokens(value: Any) -> list[str]:
    tokens: list[str] = []
    if isinstance(value, list):
        for item in value:
            if not isinstance(item, dict):
                continue
            file_name = normalize_text(item.get("name") or item.get("file_name"))
            if file_name.startswith("00-slide-") or "-full-page" in file_name:
                continue
            if item.get("file_token"):
                tokens.append(str(item["file_token"]))
    return tokens


def resolve_urls(token: str, file_tokens: list[str], *, table_id: str = TABLE_ID, use_bitable_extra: bool = True) -> dict[str, str]:
    resolved: dict[str, str] = {}
    unique = [item for item in dict.fromkeys(file_tokens) if item]
    if not unique:
        return resolved

    base_url = "https://open.feishu.cn/open-apis/drive/v1/medias/batch_get_tmp_download_url"
    for start in range(0, len(unique), BATCH_SIZE):
        batch = unique[start : start + BATCH_SIZE]
        query: list[tuple[str, str]] = []
        if use_bitable_extra:
            extra = urllib.parse.quote(json.dumps({"bitablePerm": {"tableId": table_id}}, ensure_ascii=False))
            query.append(("extra", extra))
        query.extend(("file_tokens", file_token) for file_token in batch)
        url = base_url + "?" + "&".join(f"{key}={value}" for key, value in query)
        res = request_json(url, token=token)
        if res.get("code") != 0:
            fail(f"Failed to resolve media URLs: {json.dumps(res, ensure_ascii=False)}")
        for item in res.get("data", {}).get("tmp_download_urls", []):
            file_token = item.get("file_token")
            tmp_url = item.get("tmp_download_url")
            if file_token and tmp_url:
                resolved[str(file_token)] = str(tmp_url)
    return resolved


def resolve_urls_best_effort(
    token: str,
    file_tokens: list[str],
    *,
    table_id: str = TABLE_ID,
    use_bitable_extra: bool = True,
) -> dict[str, str]:
    try:
        return resolve_urls(token, file_tokens, table_id=table_id, use_bitable_extra=use_bitable_extra)
    except SystemExit as exc:
        print(f"Warning: skipped article media URL resolution: {exc}", file=sys.stderr)
        return {}


def safe_order(value: Any, fallback: int) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(fallback)


def is_featured(value: Any) -> bool:
    text = normalize_text(value)
    return text in {"是", "精选", "推荐", "首页", "true", "True", "TRUE", "1", "yes", "Yes", "YES"}


def build_portfolio(records: list[dict[str, Any]], urls: dict[str, str]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for index, record in enumerate(records, 1):
        fields = record.get("fields", {})
        title = normalize_text(fields.get(FIELD_TITLE))
        if not title:
            continue
        category = normalize_text(fields.get(FIELD_CATEGORY)) or "其他创意"
        if category not in CATEGORIES:
            category = "其他创意"
        tokens = attachment_tokens(fields.get(FIELD_IMAGES))
        cover_tokens = attachment_tokens(fields.get(FIELD_COVER))
        images = [urls[token] for token in tokens if token in urls]
        cover_images = [urls[token] for token in cover_tokens if token in urls]
        tags = normalize_list(fields.get(FIELD_TAGS))
        item = {
            "id": record.get("record_id") or f"project-{index}",
            "order": safe_order(fields.get(FIELD_ORDER), index),
            "title": title,
            "category": category,
            "summary": normalize_text(fields.get(FIELD_SUMMARY)),
            "year": normalize_text(fields.get(FIELD_YEAR)),
            "role": normalize_text(fields.get(FIELD_ROLE)),
            "status": normalize_text(fields.get(FIELD_STATUS)),
            "tags": tags[:6],
            "featured": is_featured(fields.get(FIELD_FEATURED)),
            "images": images,
            "cover": cover_images[0] if cover_images else images[0] if images else "",
            "videoUrl": normalize_text(fields.get(FIELD_VIDEO_URL)),
            "videoBv": normalize_text(fields.get(FIELD_VIDEO_BV)),
        }
        items.append(item)
    items.sort(key=lambda row: (0 if row["featured"] else 1, row["order"], row["title"]))
    return items


def choose_article_table(token: str, base_token: str, table_id: str) -> str:
    if table_id:
        return table_id
    tables = list_tables(token, base_token)
    best_table = ""
    best_score = -1
    for table in tables:
        table_id = table.get("table_id")
        if not table_id:
            continue
        try:
            records = fetch_records(token, base_token=base_token, table_id=table_id)
        except SystemExit:
            raise
        except Exception:
            continue
        score = len(records)
        for record in records[:5]:
            fields = record.get("fields", {})
            if first_field(fields, ZHIXING_TITLE_FIELDS):
                score += 10
            if first_field(fields, ZHIXING_BODY_FIELDS) or first_field(fields, ZHIXING_LINK_FIELDS):
                score += 6
            if first_field(fields, ZHIXING_MEDIA_FIELDS):
                score += 3
        if score > best_score:
            best_table = str(table_id)
            best_score = score
    return best_table


def fetch_link_content(url: str) -> dict[str, str]:
    if not url:
        return {}
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; EasonPortfolioBot/1.0)",
            },
        )
        with urllib.request.urlopen(req, timeout=25) as response:
            raw = response.read(1_200_000)
            charset = response.headers.get_content_charset() or "utf-8"
        html = raw.decode(charset, "ignore")
    except Exception as exc:
        return {"error": str(exc)}
    import re

    title_match = re.search(r"<title[^>]*>(.*?)</title>", html, flags=re.I | re.S)
    title = re.sub(r"\s+", " ", title_match.group(1)).strip() if title_match else ""
    html = re.sub(r"<script[\s\S]*?</script>|<style[\s\S]*?</style>|<noscript[\s\S]*?</noscript>", " ", html, flags=re.I)
    paragraphs = re.findall(r"<p[^>]*>(.*?)</p>", html, flags=re.I | re.S)
    if not paragraphs:
        paragraphs = re.findall(r"<article[^>]*>(.*?)</article>", html, flags=re.I | re.S)
    text_parts: list[str] = []
    for paragraph in paragraphs[:80]:
        text = re.sub(r"<[^>]+>", " ", paragraph)
        text = re.sub(r"&nbsp;?", " ", text)
        text = re.sub(r"&amp;", "&", text)
        text = re.sub(r"&lt;", "<", text)
        text = re.sub(r"&gt;", ">", text)
        text = re.sub(r"\s+", " ", text).strip()
        if len(text) >= 12:
            text_parts.append(text)
    body = "\n\n".join(text_parts)
    return {"title": title, "body": body[:6000]}


def feishu_doc_id_from_url(url: str) -> str:
    if not url:
        return ""
    parsed = urllib.parse.urlparse(url)
    if not parsed.netloc.endswith(("feishu.cn", "larksuite.com")):
        return ""
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) >= 2 and parts[0] == "docx":
        return parts[1]
    return ""


def fetch_feishu_doc_blocks(token: str, document_id: str) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    page_token = ""
    while True:
        params = {"page_size": 500}
        if page_token:
            params["page_token"] = page_token
        api_url = (
            f"https://open.feishu.cn/open-apis/docx/v1/documents/{urllib.parse.quote(document_id)}/blocks?"
            + urllib.parse.urlencode(params)
        )
        req = urllib.request.Request(api_url, headers={"Authorization": f"Bearer {token}"})
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                res = json.loads(response.read().decode("utf-8"))
        except Exception:
            return blocks
        if res.get("code") != 0:
            return blocks
        data = res.get("data", {})
        blocks.extend(data.get("items", []))
        if not data.get("has_more"):
            break
        page_token = data.get("page_token", "")
        if not page_token:
            break
    return blocks


def fetch_feishu_child_blocks(token: str, document_id: str, parent_block_id: str) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    page_token = ""
    while True:
        params = {"page_size": 500}
        if page_token:
            params["page_token"] = page_token
        api_url = (
            f"https://open.feishu.cn/open-apis/docx/v1/documents/{urllib.parse.quote(document_id)}"
            f"/blocks/{urllib.parse.quote(parent_block_id)}/children?"
            + urllib.parse.urlencode(params)
        )
        req = urllib.request.Request(api_url, headers={"Authorization": f"Bearer {token}"})
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                res = json.loads(response.read().decode("utf-8"))
        except Exception:
            return blocks
        if res.get("code") != 0:
            return blocks
        data = res.get("data", {})
        blocks.extend(data.get("items", []))
        if not data.get("has_more"):
            break
        page_token = data.get("page_token", "")
        if not page_token:
            break
    return blocks


def fetch_feishu_doc_block_tree(token: str, document_id: str) -> list[dict[str, Any]]:
    root_children = fetch_feishu_child_blocks(token, document_id, document_id)
    root = {"block_id": document_id, "children": [block_id(block) for block in root_children if block_id(block)]}
    blocks = [root, *root_children]
    seen = {document_id}
    queue = list(root["children"])
    while queue:
        parent_id = queue.pop(0)
        if parent_id in seen:
            continue
        seen.add(parent_id)
        children = fetch_feishu_child_blocks(token, document_id, parent_id)
        for child in children:
            child_id = block_id(child)
            if child_id:
                blocks.append(child)
                queue.extend(item for item in child_ids(child) if item not in seen)
        time.sleep(0.08)
    return blocks


def fetch_feishu_descendant_blocks(token: str, document_id: str, parent_block_id: str) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    page_token = ""
    while True:
        params = {"page_size": 500, "document_revision_id": -1}
        if page_token:
            params["page_token"] = page_token
        api_url = (
            f"https://open.feishu.cn/open-apis/docx/v1/documents/{urllib.parse.quote(document_id)}"
            f"/blocks/{urllib.parse.quote(parent_block_id)}/descendant?"
            + urllib.parse.urlencode(params)
        )
        req = urllib.request.Request(api_url, headers={"Authorization": f"Bearer {token}"})
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                res = json.loads(response.read().decode("utf-8"))
        except Exception:
            return blocks
        if res.get("code") != 0:
            return blocks
        data = res.get("data", {})
        blocks.extend(data.get("items", []))
        if not data.get("has_more"):
            break
        page_token = data.get("page_token", "")
        if not page_token:
            break
    return blocks


def collect_doc_media_tokens(value: Any, path: tuple[str, ...] = ()) -> list[str]:
    tokens: list[str] = []
    if isinstance(value, dict):
        keys = tuple(str(part).lower() for part in path)
        looks_like_media = any(part in {"image", "file", "media"} or "image" in part for part in keys)
        for key, item in value.items():
            key_text = str(key).lower()
            if looks_like_media and key_text in {"file_token", "token"} and isinstance(item, str):
                tokens.append(item)
            tokens.extend(collect_doc_media_tokens(item, path + (str(key),)))
    elif isinstance(value, list):
        for item in value:
            tokens.extend(collect_doc_media_tokens(item, path))
    return list(dict.fromkeys(tokens))


def block_id(block: dict[str, Any]) -> str:
    return normalize_text(block.get("block_id") or block.get("id"))


def child_ids(block: dict[str, Any]) -> list[str]:
    children = block.get("children")
    if isinstance(children, list):
        return [normalize_text(item) for item in children if normalize_text(item)]
    return []


def first_nested_dict(value: Any, target_key: str) -> dict[str, Any]:
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key).lower() == target_key.lower() and isinstance(item, dict):
                return item
        for item in value.values():
            found = first_nested_dict(item, target_key)
            if found:
                return found
    elif isinstance(value, list):
        for item in value:
            found = first_nested_dict(item, target_key)
            if found:
                return found
    return {}


def collect_block_text(value: Any, path: tuple[str, ...] = ()) -> list[str]:
    parts: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key).lower()
            if key_text in {"block_id", "parent_id", "token", "file_token", "url", "href"}:
                continue
            if key_text in {"content", "text"} and isinstance(item, str):
                text = item.strip()
                if text:
                    parts.append(text)
                continue
            parts.extend(collect_block_text(item, path + (str(key),)))
    elif isinstance(value, list):
        for item in value:
            parts.extend(collect_block_text(item, path))
    return parts


def text_from_block(block: dict[str, Any]) -> str:
    text = "".join(collect_block_text(block))
    return " ".join(text.split())


def text_from_block_tree(block: dict[str, Any], block_map: dict[str, dict[str, Any]]) -> str:
    parts = [text_from_block(block)]
    for child_id in child_ids(block):
        child = block_map.get(child_id)
        if child:
            parts.append(text_from_block_tree(child, block_map))
    return " ".join(part for part in parts if part).strip()


def looks_like_table(block: dict[str, Any]) -> bool:
    return bool(first_nested_dict(block, "table")) or "table" in str(block.get("block_type", "")).lower()


def table_rows_from_block(block: dict[str, Any], block_map: dict[str, dict[str, Any]]) -> list[list[str]]:
    table = first_nested_dict(block, "table")
    row_count = int(table.get("row_size") or table.get("row_count") or table.get("rows") or 0) if table else 0
    col_count = int(table.get("column_size") or table.get("column_count") or table.get("columns") or 0) if table else 0
    cells: list[tuple[int, int, str]] = []

    raw_cells = table.get("cells") if table else None
    if isinstance(raw_cells, list):
        for index, cell in enumerate(raw_cells):
            if isinstance(cell, list):
                row = [normalize_text(item) for item in cell]
                cells.extend((len(cells), col, value) for col, value in enumerate(row))
                continue
            if not isinstance(cell, dict):
                continue
            row_index = int(cell.get("row_index") or cell.get("row") or (index // max(col_count, 1)))
            col_index = int(cell.get("column_index") or cell.get("col") or cell.get("column") or (index % max(col_count, 1)))
            text = text_from_block(cell)
            if not text and cell.get("block_id") in block_map:
                text = text_from_block(block_map[str(cell["block_id"])])
            cells.append((row_index, col_index, text))

    table_children = [block_map[item] for item in child_ids(block) if item in block_map]
    if not cells and table_children:
        for index, child in enumerate(table_children):
            table_cell = first_nested_dict(child, "table_cell")
            row_index = int(table_cell.get("row_index") or child.get("row_index") or child.get("row") or (index // max(col_count, 1)))
            col_index = int(table_cell.get("column_index") or child.get("column_index") or child.get("col") or child.get("column") or (index % max(col_count, 1)))
            cells.append((row_index, col_index, text_from_block_tree(child, block_map)))

    if not cells:
        return []
    max_row = max(row for row, _, _ in cells)
    max_col = max(col for _, col, _ in cells)
    row_total = max(row_count, max_row + 1)
    col_total = max(col_count, max_col + 1)
    rows = [["" for _ in range(col_total)] for _ in range(row_total)]
    for row, col, text in cells:
        if row < row_total and col < col_total:
            rows[row][col] = text
    return [row for row in rows if any(cell.strip() for cell in row)]


def build_doc_content_blocks(blocks: list[dict[str, Any]], title: str) -> list[dict[str, Any]]:
    block_map = {block_id(block): block for block in blocks if block_id(block)}
    table_child_ids: set[str] = set()
    for block in blocks:
        if not looks_like_table(block):
            continue
        queue = list(child_ids(block))
        while queue:
            item_id = queue.pop(0)
            table_child_ids.add(item_id)
            if item_id in block_map:
                queue.extend(child_ids(block_map[item_id]))
    content: list[dict[str, Any]] = []
    seen_media: set[str] = set()
    title_skipped = False

    for block in blocks:
        current_id = block_id(block)
        if current_id and current_id in table_child_ids:
            continue
        if looks_like_table(block):
            rows = table_rows_from_block(block, block_map)
            if rows:
                content.append({"type": "table", "rows": rows})
            continue
        media_tokens = collect_doc_media_tokens(block)
        if media_tokens:
            for media_token in media_tokens:
                if media_token not in seen_media:
                    content.append({"type": "image", "token": media_token})
                    seen_media.add(media_token)
            continue
        text = text_from_block(block)
        if not text:
            continue
        if not title_skipped and strip_duplicate_title(text, title) == "":
            title_skipped = True
            continue
        content.append({"type": "paragraph", "text": text})
    return content


def parse_tables_from_body(body: str) -> list[dict[str, Any]]:
    lines = [line.strip() for line in (body or "").splitlines() if line.strip()]
    tables: list[dict[str, Any]] = []

    for index, line in enumerate(lines):
        if line != "四要素的关系":
            continue
        headers = lines[index + 1 : index + 5]
        values = lines[index + 5 : index + 9]
        if len(headers) != 4 or len(values) != 4:
            continue
        if headers != ["定位", "内容", "空间", "运营"]:
            continue
        tables.append({"after": line, "rows": [headers, values]})
    return tables


def merge_body_tables(content_blocks: list[dict[str, Any]], body: str) -> list[dict[str, Any]]:
    body_tables = parse_tables_from_body(body)
    if not body_tables or any(block.get("type") == "table" for block in content_blocks):
        return content_blocks

    merged: list[dict[str, Any]] = []
    pending = list(body_tables)
    for block in content_blocks:
        merged.append(block)
        if block.get("type") != "paragraph":
            continue
        text = normalize_text(block.get("text"))
        matches = [table for table in pending if table["after"] == text]
        for table in matches:
            merged.append({"type": "table", "rows": table["rows"]})
            pending.remove(table)
    return merged


def fetch_feishu_doc_content(token: str, url: str) -> dict[str, Any]:
    document_id = feishu_doc_id_from_url(url)
    if not document_id:
        return {}
    blocks = fetch_feishu_descendant_blocks(token, document_id, document_id)
    if not blocks:
        blocks = fetch_feishu_doc_block_tree(token, document_id)
    if len(blocks) <= 1:
        blocks = fetch_feishu_doc_blocks(token, document_id)
    media_tokens = collect_doc_media_tokens(blocks)
    api_url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{urllib.parse.quote(document_id)}/raw_content"
    req = urllib.request.Request(api_url, headers={"Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            res = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        return {"error": str(exc)}
    if res.get("code") != 0:
        return {"error": json.dumps(res, ensure_ascii=False), "mediaTokens": media_tokens}
    data = res.get("data", {})
    content = normalize_text(data.get("content") or data.get("text") or data.get("raw_content"))
    result: dict[str, Any] = {"mediaTokens": media_tokens, "rawBlocks": blocks}
    if content:
        result["body"] = content[:8000]
    return result


def strip_duplicate_title(body: str, title: str) -> str:
    if not body or not title:
        return body
    lines = [line.strip() for line in body.splitlines()]
    while lines and not lines[0]:
        lines.pop(0)
    if not lines:
        return ""

    def compact(text: str) -> str:
        return "".join(str(text).split()).strip("：:丨|-— ")

    if compact(lines[0]) == compact(title):
        lines = lines[1:]
        while lines and not lines[0]:
            lines.pop(0)
    return "\n".join(lines).strip()


def media_from_fields(fields: dict[str, Any]) -> list[str]:
    tokens: list[str] = []
    for field_name in ZHIXING_MEDIA_FIELDS:
        tokens.extend(attachment_tokens(fields.get(field_name)))
    media = list(dict.fromkeys(tokens))
    order_text = normalize_text(first_field(fields, ARTICLE_ORDER_FIELDS))
    if "倒序" in order_text:
        media.reverse()
    return media


def article_cover_tokens(fields: dict[str, Any]) -> list[str]:
    return attachment_tokens(first_field(fields, ARTICLE_COVER_FIELDS))


def build_articles(
    records: list[dict[str, Any]],
    urls: dict[str, str],
    source_type: str,
    fallback_title: str,
    token: str = "",
) -> list[dict[str, Any]]:
    articles: list[dict[str, Any]] = []
    for index, record in enumerate(records, 1):
        fields = record.get("fields", {})
        title = normalize_text(first_field(fields, ZHIXING_TITLE_FIELDS))
        summary = normalize_text(first_field(fields, ZHIXING_SUMMARY_FIELDS))
        body = normalize_text(first_field(fields, ZHIXING_BODY_FIELDS))
        content_url = normalize_url(first_field(fields, ZHIXING_LINK_FIELDS))
        if not title and not summary and not body and not content_url:
            continue
        linked = fetch_feishu_doc_content(token, content_url) if token and content_url else {}
        if content_url and not linked.get("body"):
            fallback_linked = fetch_link_content(content_url)
            linked = {
                **fallback_linked,
                **{key: value for key, value in linked.items() if value},
                "error": linked.get("error") or fallback_linked.get("error", ""),
            }
        if not title:
            title = linked.get("title") or f"{fallback_title} {index}"
        if not body and linked.get("body"):
            body = linked["body"]
        body = strip_duplicate_title(body, title)
        if not summary:
            summary = body[:120] if body else "工具、方法与创意工作流记录。"
        cover_tokens = article_cover_tokens(fields)
        media_tokens = media_from_fields(fields)
        cover_images = [urls[token] for token in cover_tokens if token in urls]
        media = [urls[token] for token in media_tokens if token in urls]
        doc_tokens = linked.get("mediaTokens") if isinstance(linked.get("mediaTokens"), list) else []
        doc_urls: dict[str, str] = {}
        if doc_tokens:
            doc_urls = resolve_urls_best_effort(token, [str(item) for item in doc_tokens], use_bitable_extra=False)
            media.extend(url for file_token, url in doc_urls.items() if file_token in doc_tokens and url not in media)
        content_blocks = []
        raw_blocks = linked.get("rawBlocks") if isinstance(linked.get("rawBlocks"), list) else []
        if raw_blocks:
            content_blocks = build_doc_content_blocks(raw_blocks, title)
            for content_block in content_blocks:
                if content_block.get("type") == "image":
                    image_token = normalize_text(content_block.get("token"))
                    content_block["url"] = doc_urls.get(image_token, "")
        content_blocks = merge_body_tables(content_blocks, body)
        articles.append(
            {
                "id": record.get("record_id") or f"{source_type}-{index}",
                "sourceType": source_type,
                "order": safe_order(fields.get("序号") or fields.get("排序"), index),
                "title": title,
                "summary": summary,
                "body": body,
                "contentUrl": content_url,
                "linkedTitle": linked.get("title", ""),
                "linkedError": linked.get("error", ""),
                "media": media,
                "contentBlocks": content_blocks,
                "cover": cover_images[0] if cover_images else media[0] if media else "",
            }
        )
    articles.sort(key=lambda row: (row["order"], row["title"]))
    return articles


def write_output(items: list[dict[str, Any]]) -> None:
    API_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "source": "feishu-bitable",
        "categories": CATEGORIES,
        "count": len(items),
        "items": items,
    }
    PORTFOLIO_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(items)} items to {PORTFOLIO_FILE}")


def write_article_output(
    output_file: Path,
    items: list[dict[str, Any]],
    *,
    base_token: str,
    table_id: str,
    source_type: str,
    error: str = "",
) -> None:
    API_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "source": "feishu-bitable",
        "sourceType": source_type,
        "baseToken": base_token,
        "tableId": table_id,
        "count": len(items),
        "error": error,
        "items": items,
    }
    output_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(items)} items to {output_file}")


def refresh_article_source(
    token: str,
    *,
    output_file: Path,
    base_token: str,
    explicit_table_id: str,
    source_type: str,
    fallback_title: str,
) -> None:
    if not base_token:
        write_article_output(output_file, [], base_token=base_token, table_id="", source_type=source_type)
        return
    try:
        table_id = choose_article_table(token, base_token, explicit_table_id)
        if not table_id:
            write_article_output(
                output_file,
                [],
                base_token=base_token,
                table_id="",
                source_type=source_type,
                error=f"No suitable {source_type} table found.",
            )
            return
        article_records = fetch_records(token, base_token=base_token, table_id=table_id)
        article_tokens: list[str] = []
        for record in article_records:
            article_tokens.extend(media_from_fields(record.get("fields", {})))
            article_tokens.extend(article_cover_tokens(record.get("fields", {})))
        article_urls = resolve_urls_best_effort(token, article_tokens, table_id=table_id)
        write_article_output(
            output_file,
            build_articles(article_records, article_urls, source_type, fallback_title, token),
            base_token=base_token,
            table_id=table_id,
            source_type=source_type,
        )
    except SystemExit as exc:
        write_article_output(output_file, [], base_token=base_token, table_id="", source_type=source_type, error=str(exc))
    except Exception as exc:
        write_article_output(output_file, [], base_token=base_token, table_id="", source_type=source_type, error=str(exc))


def main() -> None:
    require_env()
    token = access_token()
    records = fetch_records(token)
    all_tokens: list[str] = []
    for record in records:
        fields = record.get("fields", {})
        all_tokens.extend(attachment_tokens(fields.get(FIELD_IMAGES)))
        all_tokens.extend(attachment_tokens(fields.get(FIELD_COVER)))
    urls = resolve_urls(token, all_tokens)
    items = build_portfolio(records, urls)
    write_output(items)
    refresh_article_source(
        token,
        output_file=ZHIXING_FILE,
        base_token=ZHIXING_BASE_TOKEN,
        explicit_table_id=ZHIXING_TABLE_ID,
        source_type="zhixing",
        fallback_title="知行记录",
    )
    refresh_article_source(
        token,
        output_file=CURATION_FILE,
        base_token=CURATION_BASE_TOKEN,
        explicit_table_id=CURATION_TABLE_ID,
        source_type="curation",
        fallback_title="策展文章",
    )


if __name__ == "__main__":
    main()
