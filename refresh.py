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
ZHIXING_MEDIA_FIELDS = ["附件", "图片", "封面", "视频", "媒体", "素材"]
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


def resolve_urls(token: str, file_tokens: list[str], *, table_id: str = TABLE_ID) -> dict[str, str]:
    resolved: dict[str, str] = {}
    unique = [item for item in dict.fromkeys(file_tokens) if item]
    if not unique:
        return resolved

    extra = urllib.parse.quote(json.dumps({"bitablePerm": {"tableId": table_id}}, ensure_ascii=False))
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


def fetch_feishu_doc_content(token: str, url: str) -> dict[str, str]:
    document_id = feishu_doc_id_from_url(url)
    if not document_id:
        return {}
    api_url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{urllib.parse.quote(document_id)}/raw_content"
    req = urllib.request.Request(api_url, headers={"Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            res = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        return {"error": str(exc)}
    if res.get("code") != 0:
        return {"error": json.dumps(res, ensure_ascii=False)}
    data = res.get("data", {})
    content = normalize_text(data.get("content") or data.get("text") or data.get("raw_content"))
    return {"body": content[:8000]} if content else {}


def media_from_fields(fields: dict[str, Any]) -> list[str]:
    tokens: list[str] = []
    for field_name in ZHIXING_MEDIA_FIELDS:
        tokens.extend(attachment_tokens(fields.get(field_name)))
    media = list(dict.fromkeys(tokens))
    order_text = normalize_text(first_field(fields, ARTICLE_ORDER_FIELDS))
    if "倒序" in order_text:
        media.reverse()
    return media


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
        if not summary:
            summary = body[:120] if body else "工具、方法与创意工作流记录。"
        media_tokens = media_from_fields(fields)
        media = [urls[token] for token in media_tokens if token in urls]
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
                "cover": media[0] if media else "",
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
        article_urls = resolve_urls(token, article_tokens, table_id=table_id)
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
