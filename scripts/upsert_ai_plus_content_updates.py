#!/usr/bin/env python3
"""Apply narrow AI++ Bitable content updates.

This script is separate from refresh.py. It only touches the five AI++ content
tables that drive the AI++ subpages.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any


API = "https://open.feishu.cn/open-apis"


@dataclass(frozen=True)
class Page:
    key: str
    name: str
    path: str
    app_token: str
    table_id: str


PAGES = {
    "overview": Page("overview", "AI 概述", "ai-plus/overview.html", "DgDxb8vQWaAJy7s6P9Sc7lz7nIe", "tbl4uFig9xBbBGR8"),
    "office": Page("office", "日常增效", "ai-plus/office.html", "DD3Bb6vhEa061SsoPMkcDXAOn1f", "tbl9HE667F8n1V8t"),
    "open-models": Page("open-models", "开源模型", "ai-plus/open-models.html", "J5XNbCDYmaoIeUswVcxcmavbnfh", "tblgdaw7EzAe40Cg"),
    "agents": Page("agents", "Agent 智能体", "ai-plus/agents.html", "YVCtb0YrSauOACsbR2qceE4mnee", "tbl7s5yDTe3d34KK"),
    "toolbox": Page("toolbox", "AI 工具箱", "ai-plus/toolbox.html", "BKoabyKIjahjXYsLzKIctWvHnTb", "tblmjrUteAqFoRYG"),
}


UPDATES: dict[str, list[dict[str, Any]]] = {
    "toolbox": [
        {
            "key": "toolbox.bilibili.limu",
            "fields": {
                "内容ID": "toolbox-bilibili-limu",
                "模块类型": "link",
                "所属板块": "B站 UP 推荐",
                "排序": "33",
                "标题": "跟李沐学AI",
                "正文": "深度学习、论文精读和模型基础。",
                "链接标题": "跟李沐学AI",
                "链接URL": "https://space.bilibili.com/1567748478/",
                "数据键": "toolbox.bilibili.limu",
                "是否启用": "是",
                "备注": "补齐 AI++ 工具箱 B站 UP 推荐。",
            },
        },
        {
            "key": "toolbox.bilibili.fange",
            "fields": {
                "内容ID": "toolbox-bilibili-fange",
                "模块类型": "link",
                "所属板块": "B站 UP 推荐",
                "排序": "34",
                "标题": "AI研究室-帆哥",
                "正文": "AI 应用实践和工具案例。",
                "链接标题": "AI研究室-帆哥",
                "链接URL": "https://space.bilibili.com/2161614/",
                "数据键": "toolbox.bilibili.fange",
                "是否启用": "是",
                "备注": "补齐 AI++ 工具箱 B站 UP 推荐。",
            },
        },
    ],
    "office": [
        {
            "key": "office.daily.article.001",
            "fields": {
                "内容ID": "office-daily-article-001",
                "模块类型": "case",
                "所属板块": "日常软件推荐",
                "排序": "15",
                "标题": "日常软件应用实例",
                "副标题/标签": "FEISHU DOC / DAILY",
                "正文": "以飞书云文档沉淀日常软件的组合、选择逻辑和真实使用记录。",
                "小字/说明": "独立飞书云文档文章卡；封面留空时由文档首图自动兜底。",
                "链接标题": "打开飞书文章",
                "链接URL": "https://my.feishu.cn/docx/YPkVdnU0Ho4WbixlQNwcbslvnad",
                "封面": "",
                "数据键": "office.daily.article.001",
                "是否启用": "是",
                "备注": "日常增效 / 日常软件推荐下新增飞书文章卡。",
            },
        },
        {
            "key": "office.browser.article.001",
            "fields": {
                "内容ID": "office-browser-article-001",
                "模块类型": "case",
                "所属板块": "浏览器及插件推荐",
                "排序": "24",
                "标题": "浏览器及插件应用实例",
                "副标题/标签": "FEISHU DOC / BROWSER",
                "正文": "以飞书云文档方式沉淀插件选择、浏览器工作流和真实使用记录。",
                "小字/说明": "独立飞书云文档文章卡；封面留空时由文档首图自动兜底。",
                "链接标题": "打开飞书文章",
                "链接URL": "https://my.feishu.cn/docx/GxgsdWQOzosgZTxllE7cBGZRnBh",
                "封面": "",
                "数据键": "office.browser.article.001",
                "是否启用": "是",
                "备注": "日常增效 / 浏览器及插件下独立飞书文章卡。",
            },
        },
    ],
    "open-models": [
        {
            "key": "open-models.cases.section",
            "fields": {
                "内容ID": "open-models-cases-section",
                "模块类型": "section",
                "所属板块": "应用实例",
                "排序": "30",
                "标题": "应用实例",
                "正文": "把模型、节点、画布和工作流放回真实任务中观察：不是只看模型参数，而是看它能否形成可复用的创作方法。",
                "数据键": "open-models.cases.section",
                "是否启用": "是",
                "备注": "应用实例移动到无限画布之前。",
            },
        },
        {
            "key": "open-models.case.001",
            "fields": {
                "内容ID": "open-models-case-001",
                "模块类型": "case",
                "所属板块": "应用实例",
                "排序": "31",
                "标题": "开源模型应用实例",
                "副标题/标签": "FEISHU DOC / CASE",
                "正文": "从飞书云文档读取案例内容，后续可继续补充缩略图、步骤记录和模型配置。",
                "小字/说明": "应用实例板块用于沉淀真实创作过程：模型选择、节点工作流、输入输出、迭代记录与最终效果。",
                "链接标题": "打开飞书案例文档",
                "链接URL": "https://my.feishu.cn/docx/PGTrdaKiOoTffix5anpcLclzndd",
                "封面": "",
                "数据键": "open-models.case.001",
                "是否启用": "是",
                "备注": "应用实例入口；封面留空时由文档首图自动兜底。",
            },
        },
        {
            "key": "models.canvas",
            "fields": {
                "排序": "40",
                "数据键": "models.canvas",
            },
        },
    ],
}


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
    if isinstance(value, list):
        parts = []
        for item in value:
            if isinstance(item, dict):
                parts.append(str(item.get("text") or item.get("name") or item.get("url") or ""))
            else:
                parts.append(str(item))
        return "".join(parts).strip()
    if isinstance(value, dict):
        return str(value.get("text") or value.get("name") or value.get("link") or "").strip()
    return str(value).strip()


def fetch_all_records(token: str, page: Page) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    page_token = ""
    while True:
        query = urllib.parse.urlencode({"page_size": 500, **({"page_token": page_token} if page_token else {})})
        payload = request_json(
            "GET",
            f"/bitable/v1/apps/{page.app_token}/tables/{page.table_id}/records?{query}",
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


def fetch_fields(token: str, page: Page) -> list[dict[str, Any]]:
    fields: list[dict[str, Any]] = []
    page_token = ""
    while True:
        query = urllib.parse.urlencode({"page_size": 100, **({"page_token": page_token} if page_token else {})})
        payload = request_json(
            "GET",
            f"/bitable/v1/apps/{page.app_token}/tables/{page.table_id}/fields?{query}",
            token,
        )
        data = payload.get("data", {})
        fields.extend(data.get("items", []))
        if not data.get("has_more"):
            break
        page_token = data.get("page_token", "")
        if not page_token:
            break
    return fields


def ensure_cover_field(token: str, page: Page) -> str:
    existing = {str(item.get("field_name") or ""): item for item in fetch_fields(token, page)}
    if "封面" in existing:
        return "exists"
    request_json(
        "POST",
        f"/bitable/v1/apps/{page.app_token}/tables/{page.table_id}/fields",
        token,
        {"field_name": "封面", "type": 1},
    )
    return "created"


def upsert_record(token: str, page: Page, row: dict[str, Any], existing: dict[str, dict[str, Any]]) -> dict[str, str]:
    fields = {
        "页面名称": page.name,
        "页面路径": page.path,
        **row["fields"],
    }
    target = existing.get(row["key"])
    if target:
        record_id = str(target["record_id"])
        request_json(
            "PUT",
            f"/bitable/v1/apps/{page.app_token}/tables/{page.table_id}/records/{record_id}",
            token,
            {"fields": fields},
        )
        action = "updated"
    else:
        payload = request_json(
            "POST",
            f"/bitable/v1/apps/{page.app_token}/tables/{page.table_id}/records",
            token,
            {"fields": fields},
        )
        record_id = str(payload.get("data", {}).get("record", {}).get("record_id", ""))
        action = "created"
    return {"page": page.key, "action": action, "recordId": record_id, "dataKey": row["key"]}


def main() -> int:
    token = tenant_access_token()
    field_results: dict[str, str] = {}
    record_results: list[dict[str, str]] = []
    for page in PAGES.values():
        field_results[page.key] = ensure_cover_field(token, page)

    for page_key, rows in UPDATES.items():
        page = PAGES[page_key]
        existing = {}
        for record in fetch_all_records(token, page):
            key = text_value(record.get("fields", {}).get("数据键"))
            if key:
                existing[key] = record
        for row in rows:
            record_results.append(upsert_record(token, page, row, existing))

    print(json.dumps({"coverFields": field_results, "records": record_results}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
