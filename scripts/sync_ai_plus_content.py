#!/usr/bin/env python3
"""Sync AI++ subpage content from Feishu Bitable apps into public JSON.

This is deliberately separate from refresh.py and the existing portfolio/article
sync. It only reads the five AI++ "网站内容同步表" tables and writes:

  api/ai-plus-content.json

Secrets are read from environment variables only.
"""

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


API = "https://open.feishu.cn/open-apis"

PAGES = [
    {
        "key": "overview",
        "name": "AI 概述",
        "path": "ai-plus/overview.html",
        "app_token": "DgDxb8vQWaAJy7s6P9Sc7lz7nIe",
        "table_id": "tbl4uFig9xBbBGR8",
    },
    {
        "key": "office",
        "name": "日常增效",
        "path": "ai-plus/office.html",
        "app_token": "DD3Bb6vhEa061SsoPMkcDXAOn1f",
        "table_id": "tbl9HE667F8n1V8t",
    },
    {
        "key": "open-models",
        "name": "开源模型",
        "path": "ai-plus/open-models.html",
        "app_token": "J5XNbCDYmaoIeUswVcxcmavbnfh",
        "table_id": "tblgdaw7EzAe40Cg",
    },
    {
        "key": "agents",
        "name": "Agent 智能体",
        "path": "ai-plus/agents.html",
        "app_token": "YVCtb0YrSauOACsbR2qceE4mnee",
        "table_id": "tbl7s5yDTe3d34KK",
    },
    {
        "key": "toolbox",
        "name": "AI 工具箱",
        "path": "ai-plus/toolbox.html",
        "app_token": "BKoabyKIjahjXYsLzKIctWvHnTb",
        "table_id": "tblmjrUteAqFoRYG",
    },
]


def request_json(method: str, path: str, token: str | None = None, body: dict | None = None) -> dict:
    data = None if body is None else json.dumps(body, ensure_ascii=False).encode("utf-8")
    headers = {"Content-Type": "application/json; charset=utf-8"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(f"{API}{path}", data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=35) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {path} failed: HTTP {exc.code}: {detail}") from exc
    if payload.get("code") != 0:
        raise RuntimeError(f"{method} {path} failed: {payload}")
    return payload


def tenant_access_token() -> str:
    app_id = os.environ.get("LARK_APP_ID", "").strip()
    app_secret = os.environ.get("LARK_APP_SECRET", "").strip()
    if not app_id or not app_secret:
        raise RuntimeError("Missing LARK_APP_ID or LARK_APP_SECRET")
    payload = request_json(
        "POST",
        "/auth/v3/tenant_access_token/internal",
        body={"app_id": app_id, "app_secret": app_secret},
    )
    return str(payload["tenant_access_token"])


def text_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, list):
        parts: list[str] = []
        for item in value:
            if isinstance(item, dict):
                if "text" in item:
                    parts.append(str(item.get("text", "")))
                elif "name" in item:
                    parts.append(str(item.get("name", "")))
                elif "url" in item:
                    parts.append(str(item.get("url", "")))
            else:
                parts.append(str(item))
        return "".join(parts).strip()
    if isinstance(value, dict):
        if "text" in value:
            return str(value.get("text", "")).strip()
        if "name" in value:
            return str(value.get("name", "")).strip()
        if "link" in value:
            return str(value.get("link", "")).strip()
    return str(value).strip()


def enabled_value(value: Any) -> bool:
    text = text_value(value).lower()
    return text not in {"否", "false", "0", "no", "disabled", "停用"}


def int_value(value: Any) -> int:
    text = text_value(value)
    try:
        return int(float(text))
    except (TypeError, ValueError):
        return 0


def fetch_records(token: str, app_token: str, table_id: str) -> list[dict]:
    records: list[dict] = []
    page_token = ""
    while True:
        query = urllib.parse.urlencode(
            {
                "page_size": 500,
                **({"page_token": page_token} if page_token else {}),
            }
        )
        payload = request_json(
            "GET",
            f"/bitable/v1/apps/{urllib.parse.quote(app_token)}/tables/{urllib.parse.quote(table_id)}/records?{query}",
            token,
        )
        data = payload.get("data", {})
        records.extend(data.get("items", []))
        if not data.get("has_more"):
            break
        page_token = data.get("page_token", "")
        if not page_token:
            break
    return records


def normalize_record(page: dict, record: dict) -> dict:
    fields = record.get("fields", {})
    return {
        "id": text_value(fields.get("内容ID")) or record.get("record_id", ""),
        "recordId": record.get("record_id", ""),
        "pageKey": page["key"],
        "pageName": text_value(fields.get("页面名称")) or page["name"],
        "pagePath": text_value(fields.get("页面路径")) or page["path"],
        "moduleType": text_value(fields.get("模块类型")) or "card",
        "section": text_value(fields.get("所属板块")),
        "order": int_value(fields.get("排序")),
        "title": text_value(fields.get("标题")),
        "tag": text_value(fields.get("副标题/标签")),
        "body": text_value(fields.get("正文")),
        "note": text_value(fields.get("小字/说明")),
        "linkTitle": text_value(fields.get("链接标题")),
        "linkUrl": text_value(fields.get("链接URL")),
        "cover": text_value(fields.get("封面") or fields.get("封面URL") or fields.get("封面图")),
        "key": text_value(fields.get("数据键")),
        "enabled": enabled_value(fields.get("是否启用")),
        "remark": text_value(fields.get("备注")),
    }


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    output_path = root / "api" / "ai-plus-content.json"
    token = tenant_access_token()
    payload = {
        "source": "feishu-bitable",
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "pages": {},
    }
    warnings: list[str] = []
    for page in PAGES:
        raw_records = fetch_records(token, page["app_token"], page["table_id"])
        records = [normalize_record(page, record) for record in raw_records]
        records = [record for record in records if record["enabled"]]
        records.sort(key=lambda item: (item["order"], item["id"]))
        if not records:
            warnings.append(f"{page['name']} has no enabled records")
        payload["pages"][page["key"]] = {
            "name": page["name"],
            "path": page["path"],
            "appToken": page["app_token"],
            "tableId": page["table_id"],
            "records": records,
        }
    if warnings:
        payload["warnings"] = warnings
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        "AI_PLUS_CONTENT_SYNC="
        + json.dumps(
            {
                "output": str(output_path.relative_to(root)),
                "pages": {k: len(v["records"]) for k, v in payload["pages"].items()},
                "warnings": warnings,
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
