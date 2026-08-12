#!/usr/bin/env python3
"""Upsert one AI++ open-model case record into its Feishu Bitable.

This script is intentionally narrow: it only touches the AI++ 开源模型 table and
only the record identified by 数据键=open-models.case.001.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.parse
import urllib.request
from typing import Any


API = "https://open.feishu.cn/open-apis"
APP_TOKEN = "J5XNbCDYmaoIeUswVcxcmavbnfh"
TABLE_ID = "tblgdaw7EzAe40Cg"
SECTION_KEY = "open-models.cases.section"
CASE_KEY = "open-models.case.001"


def request_json(method: str, path: str, token: str | None = None, body: dict | None = None) -> dict:
    data = None if body is None else json.dumps(body, ensure_ascii=False).encode("utf-8")
    headers = {"Content-Type": "application/json; charset=utf-8"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(f"{API}{path}", data=data, method=method, headers=headers)
    with urllib.request.urlopen(req, timeout=35) as response:
        payload = json.loads(response.read().decode("utf-8"))
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
        parts: list[str] = []
        for item in value:
            if isinstance(item, dict):
                parts.append(str(item.get("text") or item.get("name") or item.get("url") or ""))
            else:
                parts.append(str(item))
        return "".join(parts).strip()
    if isinstance(value, dict):
        return str(value.get("text") or value.get("name") or value.get("link") or "").strip()
    return str(value).strip()


def fetch_records(token: str) -> list[dict]:
    records: list[dict] = []
    page_token = ""
    while True:
        query = urllib.parse.urlencode({"page_size": 500, **({"page_token": page_token} if page_token else {})})
        payload = request_json(
            "GET",
            f"/bitable/v1/apps/{APP_TOKEN}/tables/{TABLE_ID}/records?{query}",
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


def main() -> int:
    token = tenant_access_token()
    rows = [
        {
            "key": SECTION_KEY,
            "fields": {
                "内容ID": "open-models-cases-section",
                "页面名称": "开源模型",
                "页面路径": "ai-plus/open-models.html",
                "模块类型": "section",
                "所属板块": "应用实例",
                "排序": 450,
                "标题": "应用实例",
                "正文": "把模型、节点、画布和工作流放回真实任务中观察：不是只看模型参数，而是看它能否形成可复用的创作方法。",
                "数据键": SECTION_KEY,
                "是否启用": "是",
                "备注": "AI++ 开源模型页面应用实例板块标题",
            },
        },
        {
            "key": CASE_KEY,
            "fields": {
                "内容ID": "open-models-case-001",
                "页面名称": "开源模型",
                "页面路径": "ai-plus/open-models.html",
                "模块类型": "case",
                "所属板块": "应用实例",
                "排序": 460,
                "标题": "开源模型应用实例",
                "副标题/标签": "FEISHU DOC / CASE",
                "正文": "从飞书云文档读取案例内容，后续可继续补充缩略图、步骤记录和模型配置。",
                "小字/说明": "应用实例板块用于沉淀真实创作过程：模型选择、节点工作流、输入输出、迭代记录与最终效果。",
                "链接标题": "打开飞书案例文档",
                "链接URL": "https://my.feishu.cn/docx/EPrWdPee9oziP8xiRHscFKsLnuf",
                "数据键": CASE_KEY,
                "是否启用": "是",
                "备注": "AI++ 开源模型页面应用实例入口",
            },
        },
    ]
    existing = {}
    for record in fetch_records(token):
        key = text_value(record.get("fields", {}).get("数据键"))
        if key:
            existing[key] = record
    results = []
    for row in rows:
        target = existing.get(row["key"])
        if target:
            record_id = target["record_id"]
            request_json("PUT", f"/bitable/v1/apps/{APP_TOKEN}/tables/{TABLE_ID}/records/{record_id}", token, {"fields": row["fields"]})
            action = "updated"
        else:
            payload = request_json("POST", f"/bitable/v1/apps/{APP_TOKEN}/tables/{TABLE_ID}/records", token, {"fields": row["fields"]})
            record_id = payload.get("data", {}).get("record", {}).get("record_id", "")
            action = "created"
        results.append({"action": action, "recordId": record_id, "dataKey": row["key"]})
    print(json.dumps({"results": results}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
