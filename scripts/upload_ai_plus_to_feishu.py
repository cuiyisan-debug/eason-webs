#!/usr/bin/env python3
"""Create AI++ Feishu docs and companion Bitable apps from local AI++ pages.

This is an intentionally standalone helper for a one-off content migration.
It reads local static HTML files, creates Docx documents in a target Feishu
folder, and creates one Bitable app per page as that page's sync area.

Secrets are read from environment variables only.
"""

from __future__ import annotations

import argparse
import html.parser
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


API = "https://open.feishu.cn/open-apis"

PAGES = [
    ("AI 概述", "overview.html", "ai-plus-content"),
    ("日常增效", "office.html", "daily-efficiency-content"),
    ("开源模型", "open-models.html", "open-models-content"),
    ("Agent 智能体", "agents.html", "agent-content"),
    ("AI 工具箱", "toolbox.html", "ai-toolbox-content"),
]


class MainTextExtractor(html.parser.HTMLParser):
    """Small dependency-free HTML-to-lines extractor for our static pages."""

    BLOCK_TAGS = {"h1", "h2", "h3", "p", "li", "small", "span", "strong", "a"}

    def __init__(self, target_id: str) -> None:
        super().__init__(convert_charrefs=True)
        self.target_id = target_id
        self.stack: list[str] = []
        self.capture_depth = 0
        self.current: list[str] = []
        self.lines: list[str] = []
        self.href: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)
        if attrs_dict.get("id") == self.target_id:
            self.capture_depth = 1
        elif self.capture_depth:
            self.capture_depth += 1

        if not self.capture_depth:
            return

        if tag in {"script", "style", "canvas", "button"}:
            self.stack.append("skip")
            return
        self.stack.append(tag)
        if tag in {"h1", "h2", "h3", "p", "li"}:
            self.flush()
        if tag == "a":
            self.href = attrs_dict.get("href")

    def handle_endtag(self, tag: str) -> None:
        if not self.capture_depth:
            return
        if tag in {"h1", "h2", "h3", "p", "li"}:
            self.flush(prefix="- " if tag == "li" else "")
        if tag == "a" and self.href:
            text = normalize("".join(self.current))
            if text and self.href.startswith("http"):
                self.current = [f"{text}（{self.href}）"]
            self.href = None
        if self.stack:
            self.stack.pop()
        self.capture_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self.capture_depth or "skip" in self.stack:
            return
        if self.stack and self.stack[-1] in self.BLOCK_TAGS:
            self.current.append(data)

    def flush(self, prefix: str = "") -> None:
        text = normalize("".join(self.current))
        self.current = []
        if not text:
            return
        if self.lines and self.lines[-1] == text:
            return
        self.lines.append(prefix + text)


def normalize(value: str) -> str:
    value = re.sub(r"\s+", " ", value.replace("\u200b", "")).strip()
    return value


def request_json(method: str, path: str, token: str | None = None, body: dict | None = None) -> dict:
    data = None if body is None else json.dumps(body, ensure_ascii=False).encode("utf-8")
    headers = {"Content-Type": "application/json; charset=utf-8"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(f"{API}{path}", data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
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


def extract_page(repo_root: Path, filename: str, content_id: str) -> list[str]:
    html = (repo_root / "ai-plus" / filename).read_text(encoding="utf-8")
    parser = MainTextExtractor(content_id)
    parser.feed(html)
    parser.flush()
    # Remove repeated nav/action noise while preserving meaningful content.
    skip = {"开始梳理", "看工具分类", "按类别查找", "建立情报站", "四类组合", "工作习惯", "发展迭代", "无限画布", "发展路径", "Codex 案例"}
    lines = [line for line in parser.lines if line not in skip]
    return lines


def create_doc(token: str, folder_token: str, title: str) -> tuple[str, str]:
    payload = request_json(
        "POST",
        "/docx/v1/documents",
        token,
        {"folder_token": folder_token, "title": title},
    )
    document = payload.get("data", {}).get("document", {})
    document_id = document.get("document_id") or payload.get("data", {}).get("document_id")
    url = document.get("url") or f"https://my.feishu.cn/docx/{document_id}"
    if not document_id:
        raise RuntimeError(f"Create document returned no document_id: {payload}")
    return str(document_id), str(url)


def append_text_blocks(token: str, document_id: str, lines: list[str]) -> None:
    children = []
    for line in lines:
        children.append(
            {
                "block_type": 2,
                "text": {
                    "elements": [
                        {
                            "text_run": {
                                "content": line,
                            }
                        }
                    ]
                },
            }
        )
    # Feishu has per-request block limits; keep chunks modest.
    for start in range(0, len(children), 40):
        chunk = children[start : start + 40]
        request_json(
            "POST",
            f"/docx/v1/documents/{urllib.parse.quote(document_id)}/blocks/{urllib.parse.quote(document_id)}/children",
            token,
            {"children": chunk},
        )
        time.sleep(0.25)


def create_bitable(token: str, folder_token: str, page_name: str) -> tuple[str, str]:
    name = f"{page_name}｜同步区域"
    payload = request_json(
        "POST",
        "/bitable/v1/apps",
        token,
        {"name": name, "folder_token": folder_token},
    )
    app = payload.get("data", {}).get("app", {}) or payload.get("data", {})
    app_token = app.get("app_token") or app.get("token")
    url = app.get("url") or f"https://my.feishu.cn/base/{app_token}"
    if not app_token:
        raise RuntimeError(f"Create bitable returned no app_token: {payload}")
    return str(app_token), str(url)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--folder-token", required=True)
    parser.add_argument("--repo-root", default=".")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    token = tenant_access_token()
    results = []

    for page_name, filename, content_id in PAGES:
        doc_title = f"AI++｜{page_name}"
        bitable_token, bitable_url = create_bitable(token, args.folder_token, page_name)
        lines = [
            doc_title,
            f"对应二级页面：{page_name}",
            f"同步区域多维表格：{page_name}｜同步区域",
            f"多维表格链接：{bitable_url}",
            "以下内容由 AI++ 网站二级页面正文转换生成，可作为后续飞书维护与网站同步的内容底稿。",
            "",
        ]
        lines.extend(extract_page(repo_root, filename, content_id))
        doc_id, doc_url = create_doc(token, args.folder_token, doc_title)
        append_text_blocks(token, doc_id, lines)
        results.append(
            {
                "page": page_name,
                "document_url": doc_url,
                "bitable_url": bitable_url,
                "bitable_token": bitable_token,
            }
        )

    print("AI_PLUS_FEISHU_UPLOAD_RESULTS=" + json.dumps(results, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
