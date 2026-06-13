#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
API_DIR = ROOT / "api"
PORTFOLIO_FILE = API_DIR / "portfolio.json"

APP_ID = os.environ.get("LARK_APP_ID", "").strip()
APP_SECRET = os.environ.get("LARK_APP_SECRET", "").strip()
ACCESS_TOKEN = os.environ.get("LARK_ACCESS_TOKEN", "").strip()
BASE_TOKEN = os.environ.get("LARK_BASE_TOKEN", "").strip()
TABLE_ID = os.environ.get("LARK_TABLE_ID", "").strip()

FIELD_TITLE = os.environ.get("LARK_FIELD_TITLE", "项目名称")
FIELD_CATEGORY = os.environ.get("LARK_FIELD_CATEGORY", "前台分类")
FIELD_SUMMARY = os.environ.get("LARK_FIELD_SUMMARY", "项目简介")
FIELD_IMAGES = os.environ.get("LARK_FIELD_IMAGES", "图片")
FIELD_YEAR = os.environ.get("LARK_FIELD_YEAR", "年份")
FIELD_FEATURED = os.environ.get("LARK_FIELD_FEATURED", "首页轮播")
FIELD_FEATURED_ALIASES = [FIELD_FEATURED, "首页轮播", "是否精选", "首页推荐", "精选", "推荐"]
FIELD_VIDEO_URL = os.environ.get("LARK_FIELD_VIDEO_URL", "视频链接")
FIELD_VIDEO_BV = os.environ.get("LARK_FIELD_VIDEO_BV", "视频BV号")
FIELD_ROLE = os.environ.get("LARK_FIELD_ROLE", "角色")
FIELD_TAGS = os.environ.get("LARK_FIELD_TAGS", "二级标签")
FIELD_STATUS = os.environ.get("LARK_FIELD_STATUS", "项目状态")
FIELD_ORDER = os.environ.get("LARK_FIELD_ORDER", "序号")

CATEGORIES = ["政企展厅", "品牌空间", "文博展陈", "文旅体验", "大型展会", "临展活动", "其他创意"]
BATCH_SIZE = 5


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


def fetch_records(token: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    page_token = ""
    while True:
        params = {"page_size": 500}
        if page_token:
            params["page_token"] = page_token
        url = (
            f"https://open.feishu.cn/open-apis/bitable/v1/apps/{BASE_TOKEN}/tables/{TABLE_ID}/records?"
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


def resolve_urls(token: str, file_tokens: list[str]) -> dict[str, str]:
    resolved: dict[str, str] = {}
    unique = [item for item in dict.fromkeys(file_tokens) if item]
    if not unique:
        return resolved

    extra = urllib.parse.quote(json.dumps({"bitablePerm": {"tableId": TABLE_ID}}, ensure_ascii=False))
    base_url = "https://open.feishu.cn/open-apis/drive/v1/medias/batch_get_tmp_download_url"
    for start in range(0, len(unique), BATCH_SIZE):
        batch = unique[start : start + BATCH_SIZE]
        query = [("extra", extra)]
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


def safe_order(value: Any, fallback: int) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(fallback)


def is_featured(value: Any) -> bool:
    text = normalize_text(value)
    return text in {"是", "精选", "推荐", "首页", "true", "True", "TRUE", "1", "yes", "Yes", "YES"}


def first_field(fields: dict[str, Any], names: list[str]) -> Any:
    for name in dict.fromkeys(names):
        if name in fields:
            return fields.get(name)
    return None


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
        images = [urls[token] for token in tokens if token in urls]
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
            "featured": is_featured(first_field(fields, FIELD_FEATURED_ALIASES)),
            "images": images,
            "cover": images[0] if images else "",
            "videoUrl": normalize_text(fields.get(FIELD_VIDEO_URL)),
            "videoBv": normalize_text(fields.get(FIELD_VIDEO_BV)),
        }
        items.append(item)
    items.sort(key=lambda row: (0 if row["featured"] else 1, row["order"], row["title"]))
    return items


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


def main() -> None:
    require_env()
    token = access_token()
    records = fetch_records(token)
    all_tokens: list[str] = []
    for record in records:
        all_tokens.extend(attachment_tokens(record.get("fields", {}).get(FIELD_IMAGES)))
    urls = resolve_urls(token, all_tokens)
    items = build_portfolio(records, urls)
    write_output(items)


if __name__ == "__main__":
    main()
