#!/usr/bin/env python3
"""Populate existing AI++ Feishu Bitable apps with structured website content.

This is a one-off migration helper. It does not change refresh.py or the
standing Feishu sync workflow. Secrets are read only from environment vars.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request


API = "https://open.feishu.cn/open-apis"

FIELD_NAMES = [
    "内容ID",
    "页面名称",
    "页面路径",
    "模块类型",
    "所属板块",
    "排序",
    "标题",
    "副标题/标签",
    "正文",
    "小字/说明",
    "链接标题",
    "链接URL",
    "数据键",
    "是否启用",
    "备注",
]

APPS = {
    "AI 概述": {
        "token": "DgDxb8vQWaAJy7s6P9Sc7lz7nIe",
        "path": "ai-plus/overview.html",
        "records": [
            ("hero", "顶部引导", 1, "把 AI 从热词讲成一张可用的地图", "AI++ 基础介绍", "这页用于快速建立 AI 基础认知：先看 AI 为什么从“会算”走到“会对话、会创作、会调用工具”，再把大模型、Token、上下文、Skill、Agent 等名词讲清楚，最后按对话、图像、视频、办公、代码和自动化建立工具分类体系。", "", "", "", "overview.hero"),
            ("caption", "顶部引导", 2, "数据进入模型，被切成 Token 与向量表示。", "", "", "", "", "", "overview.caption.1"),
            ("caption", "顶部引导", 3, "模型在上下文窗口里预测、推理、组合答案。", "", "", "", "", "", "overview.caption.2"),
            ("caption", "顶部引导", 4, "Skill 与工具把能力接到真实工作流程。", "", "", "", "", "", "overview.caption.3"),
            ("section", "总地图", 10, "先建立一张总地图", "", "今天常说的 AI，不只是一个聊天框。更准确地说，它是一套由模型、数据、界面、工具调用和工作流组成的能力系统。理解它，先分清“脑”“记忆”“手”和“流程”。", "", "", "", "overview.map"),
            ("card", "总地图", 11, "模型", "", "负责理解、生成和推理。大模型像一个通用能力底座，本身不等于完整产品。", "", "", "", "overview.map.model"),
            ("card", "总地图", 12, "上下文", "", "负责把当前任务、资料、规则和对话历史交给模型。上下文越清楚，输出越稳定。", "", "", "", "overview.map.context"),
            ("card", "总地图", 13, "工具", "", "负责执行动作，例如搜索、读文件、写代码、生成图片、操作表格、调用外部 API。", "", "", "", "overview.map.tools"),
            ("card", "总地图", 14, "Skill", "", "负责沉淀可复用方法，把提示词、规范、素材、脚本和工具流程封装成“可重复使用的工作能力”。", "", "", "", "overview.map.skill"),
            ("section", "发展脉络", 20, "AI 发展脉络：四次关键转向", "", "AI 的主线不是“突然冒出来一个聊天机器人”，而是从规则系统，到统计学习，到深度学习，再到大模型与多模态工作流的连续演进。", "", "", "", "overview.timeline"),
            ("timeline", "发展脉络", 21, "概念诞生：让机器表现出智能", "1950s", "1956 年达特茅斯暑期研究项目让“人工智能”成为一个正式研究方向。早期 AI 更相信符号、逻辑、规则和搜索。", "", "", "", "overview.timeline.1950"),
            ("timeline", "发展脉络", 22, "深度学习爆发：数据、算力、算法汇合", "2012", "AlexNet 在大规模图像识别上取得突破，让 GPU 训练深度神经网络成为主流路径，视觉、语音、翻译等任务进入快速进步期。", "", "", "", "overview.timeline.2012"),
            ("timeline", "发展脉络", 23, "从模型到工作流：多模态、工具调用、智能体", "2023-2026", "AI 不再只输出文本，而是能读图、生成图像和视频、调用工具、处理文件、辅助办公与编程。竞争焦点从“谁更会回答”扩展到“谁更能完成任务”。", "", "", "", "overview.timeline.workflow"),
            ("section", "核心名词", 30, "核心名词：用人话讲清楚", "", "这些词经常混在一起。讲解时建议按“模型怎么读、怎么想、怎么动手、怎么沉淀”这条线说，听众最容易接住。", "", "", "", "overview.terms"),
            ("term", "核心名词", 31, "大模型 LLM", "", "用海量文本、代码和多种数据训练出的通用模型。它不是数据库，而是学会了语言、知识和任务模式之间的统计关系。", "模型越强，不代表越懂你的具体场景；场景信息要靠上下文、资料库或工具补进去。", "", "", "overview.term.llm"),
            ("term", "核心名词", 32, "Token", "", "模型处理文本的基本单位，可以是一个字、一个词的一部分、标点或空格。中文通常不能简单按“字数”估算。", "输入和输出都会消耗 Token，长文档、长对话和多轮修改都会占用上下文空间。", "", "", "overview.term.token"),
            ("term", "核心名词", 33, "Agent", "", "能围绕目标拆步骤、调用工具、观察结果并继续推进的 AI 应用形态。它强调“完成任务”，不只是“给答案”。", "Agent 的关键不是人格化，而是计划、工具、状态、权限和边界。", "", "", "overview.term.agent"),
            ("section", "工具分类", 40, "AI 工具分类认知体系", "", "不要按品牌背工具名，要按“输入是什么、输出是什么、改变了哪段工作流”来分。下面的代表工具会变化，但分类方法能长期复用。", "", "", "", "overview.tools"),
        ],
    },
    "日常增效": {
        "token": "DD3Bb6vhEa061SsoPMkcDXAOn1f",
        "path": "ai-plus/office.html",
        "records": [
            ("hero", "顶部引导", 1, "让日常工作少一点摩擦", "WORKFLOW / DAILY EFFICIENCY", "跳出 AI 本身，重新整理每天真正影响效率的基础设施：软件、浏览器、正版工具与工作习惯。好的效率系统不是工具越多，而是每个工具各司其职。", "", "", "", "office.hero"),
            ("section", "四类组合", 10, "四类组合，按场景使用", "", "先建立稳定的底层工具，再用浏览器和习惯把它们串起来，避免为了“效率”不断换软件。", "", "", "", "office.categories"),
            ("card", "日常软件推荐", 11, "日常软件推荐", "Base", "负责记录、检索、启动和整理，让高频动作尽量在几秒内完成。", "", "", "", "office.daily"),
            ("link", "日常软件推荐", 12, "Obsidian", "", "本地优先的知识库，适合长期积累与双向链接。", "", "Obsidian", "https://obsidian.md/download", "office.daily.obsidian"),
            ("link", "日常软件推荐", 13, "Everything", "", "Windows 文件秒级搜索，替代层层翻文件夹。", "", "Everything", "https://www.voidtools.com/", "office.daily.everything"),
            ("link", "日常软件推荐", 14, "Microsoft PowerToys", "", "批量重命名、窗口布局、快捷启动等系统增强工具。", "", "Microsoft PowerToys", "https://learn.microsoft.com/zh-cn/windows/powertoys/", "office.daily.powertoys"),
            ("card", "浏览器及插件推荐", 20, "浏览器及插件推荐", "Web", "浏览器是信息入口，插件只解决明确问题：保存、阅读、翻译、专注和安全。", "", "", "", "office.browser"),
            ("link", "浏览器及插件推荐", 21, "Chrome", "", "扩展生态成熟，适合作为主力工作浏览器。", "", "Chrome", "https://www.google.com/chrome/", "office.browser.chrome"),
            ("link", "浏览器及插件推荐", 22, "Chrome Web Store", "", "从官方商店安装扩展，先看权限与开发者信息。", "", "Chrome Web Store", "https://chromewebstore.google.com/", "office.browser.store"),
            ("link", "浏览器及插件推荐", 23, "Raindrop.io", "", "把网页收藏按主题沉淀，减少“收藏后失踪”。", "", "Raindrop.io", "https://raindrop.io/", "office.browser.raindrop"),
            ("card", "正版软件推荐", 30, "正版软件推荐", "Trust", "涉及工作成果、账号和长期协作时，优先选择正版授权，换取更新、支持与安全边界。", "", "", "", "office.licensed"),
            ("link", "正版软件推荐", 31, "Microsoft 365", "", "Office、OneDrive 与协作服务的一体化订阅。", "", "Microsoft 365", "https://www.microsoft.com/microsoft-365", "office.licensed.microsoft365"),
            ("link", "正版软件推荐", 32, "Adobe Creative Cloud", "", "图像、排版、视频等专业创作软件套件。", "", "Adobe Creative Cloud", "https://www.adobe.com/creativecloud.html", "office.licensed.adobe"),
            ("link", "正版软件推荐", 33, "1Password", "", "集中管理密码、通行密钥和安全共享。", "", "1Password", "https://www.1password.com/", "office.licensed.1password"),
            ("card", "工作习惯建议", 40, "工作习惯建议", "Rhythm", "工具只能缩短动作，习惯才能减少决策。把“下一步”写清楚，比堆更多软件更有效。", "", "", "", "office.habit"),
        ],
    },
    "开源模型": {
        "token": "J5XNbCDYmaoIeUswVcxcmavbnfh",
        "path": "ai-plus/open-models.html",
        "records": [
            ("hero", "顶部引导", 1, "模型不只是下载，更是创作基础设施", "OPEN SOURCE / COMFYUI", "从开源权重、节点工作流到在线无限画布，开源模型真正改变的是“怎么组织创作”。这页不追求模型名单，而是帮助你围绕 ComfyUI 做出可复用、可迭代的选型。", "", "", "", "models.hero"),
            ("section", "发展迭代", 10, "开源大模型发展迭代", "", "理解迭代重点，比背版本号更重要：模型从“能生成”走向“可控制、可组合、可部署”。", "", "", "", "models.evolution"),
            ("pipeline", "发展迭代", 11, "开放权重", "01 / 基础能力", "模型权重和推理代码可获得，个人可以下载、测试和部署，硬件门槛开始下降。", "", "", "", "models.evolution.weights"),
            ("pipeline", "发展迭代", 12, "节点组合", "02 / 工作流化", "ComfyUI 把采样器、模型、LoRA、ControlNet、放大与输出拆成可连接节点。", "", "", "", "models.evolution.nodes"),
            ("pipeline", "发展迭代", 13, "图像与视频", "03 / 多模态化", "文本、图像、视频、音频和修复模型进入同一套工作流，创作开始跨媒介流动。", "", "", "", "models.evolution.multimodal"),
            ("pipeline", "发展迭代", 14, "可复用资产", "04 / 可持续迭代", "工作流、提示词、参考图和模型配置被保存下来，形成自己的本地创作资产库。", "", "", "", "models.evolution.assets"),
            ("section", "常见开源大模型", 20, "常见开源大模型", "", "以下模型都可以放入 ComfyUI 生态理解：先按任务选模态，再看显存、速度、许可和控制能力。", "", "", "", "models.list"),
            ("card", "常见开源大模型", 21, "Qwen", "文本 / 视觉 / 代码", "通用能力覆盖面广，适合提示词改写、视觉理解、工作流辅助和本地知识处理。", "适合中文理解、代码与多模态协同的任务；按参数规模、量化格式和显存预算选择。", "Qwen 官方仓库", "https://github.com/QwenLM/Qwen", "models.qwen"),
            ("card", "常见开源大模型", 22, "Z-Image-Turbo", "快速生图", "面向快速文本生图的轻量方案，适合在 ComfyUI 里测试构图、风格和批量出图。", "适合低步骤、快反馈地迭代视觉方案；先确认显存、采样节点和模型许可。", "模型页面", "https://huggingface.co/h4tef/Z-Image-Turbo", "models.zimage"),
            ("card", "常见开源大模型", 23, "LTX-2.3", "视频 / 音频", "LTX 系列面向音视频生成与编辑，适合把镜头、运动和声音纳入 ComfyUI 视频工作流。", "重点比较分辨率、时长、显存和音视频同步能力。", "LTX 官方仓库", "https://github.com/Lightricks/LTX-Video", "models.ltx"),
            ("card", "常见开源大模型", 24, "ComfyUI", "工作流中枢", "它不是模型，而是把模型、节点、参数和输出组织起来的可视化工作流环境。", "先学会读工作流，再决定安装哪些模型和自定义节点。", "ComfyUI 官方仓库", "https://github.com/comfyanonymous/ComfyUI", "models.comfyui"),
            ("section", "无限画布", 40, "无限画布：空间化创作范式", "", "无限画布把模型能力从“单张输出”变成可以平铺、回看、分支和持续迭代的空间。", "", "", "", "models.canvas"),
        ],
    },
    "Agent 智能体": {
        "token": "YVCtb0YrSauOACsbR2qceE4mnee",
        "path": "ai-plus/agents.html",
        "records": [
            ("hero", "顶部引导", 1, "从回答问题到真正去做事", "AGENT / DIGITAL WORKER", "Agent 智能体不是更会聊天的机器人，而是能够理解目标、调用工具、执行步骤、检查结果并继续推进的数字员工。本页通过 Coze、Codex、QClaw 等平台，建立从概念到实践的认知。", "", "", "", "agents.hero"),
            ("section", "发展路径", 10, "Agent 智能体的发展", "", "智能体的关键变化，不在于回答变长，而在于它开始拥有“行动回路”：目标 → 计划 → 工具 → 结果 → 校验。", "", "", "", "agents.evolution"),
            ("pipeline", "发展路径", 11, "回答问题", "01 / Chat", "模型根据上下文生成文字或代码，主要价值是信息理解与内容产出。", "", "", "", "agents.chat"),
            ("pipeline", "发展路径", 12, "调用工具", "02 / Tool", "智能体开始连接搜索、知识库、表格、浏览器、API 和本地文件。", "", "", "", "agents.tool"),
            ("pipeline", "发展路径", 13, "连续执行", "03 / Loop", "把复杂目标拆成多个步骤，执行后读取结果，再决定下一步。", "", "", "", "agents.loop"),
            ("pipeline", "发展路径", 14, "数字员工", "04 / Worker", "在权限、规则和人工确认边界内，长期承担一类可复用工作。", "", "", "", "agents.worker"),
            ("section", "常见平台", 20, "常见智能体平台", "", "平台的区别主要在搭建方式、工具连接、部署渠道和权限边界，而不是“谁更像人”。", "", "", "", "agents.platforms"),
            ("card", "常见平台", 21, "Coze / 扣子", "可视化搭建", "适合用工作流、插件、知识库和多种触发器快速搭建面向业务的 Agent。", "适合内容生产、客服、数据整理、社媒机器人。上线前检查数据权限和第三方插件边界。", "进入扣子平台", "https://www.coze.cn/overview", "agents.coze"),
            ("card", "常见平台", 22, "Codex", "代码智能体", "面向真实代码仓库和开发任务，能够读取项目、编辑文件、运行检查并根据结果继续修改。", "适合网页、脚本、测试、重构、文档和自动化。明确文件范围、命令权限和验收标准。", "Codex 开发者入口", "https://developers.openai.com/codex", "agents.codex"),
            ("card", "常见平台", 23, "QClaw", "本地部署 / 远程操作", "将 Agent 部署到个人电脑环境，强调本地任务、应用控制和降低部署门槛。", "适合个人电脑操作、消息处理、日常自动化。注意本地权限、隐私数据和误操作风险。", "查看 QClaw 入口", "https://qclawd.com/en/", "agents.qclaw"),
            ("section", "Codex 案例", 30, "应用实例：用 Codex 做一个网页页面", "", "把“做页面”从一句模糊要求，变成一条可检查的智能体执行链。", "", "", "", "agents.case"),
        ],
    },
    "AI 工具箱": {
        "token": "BKoabyKIjahjXYsLzKIctWvHnTb",
        "path": "ai-plus/toolbox.html",
        "records": [
            ("hero", "顶部引导", 1, "把收藏夹变成 AI 资源情报站", "AI++ / TOOLBOX", "精选常用 AI 网站、效率工具与优质 UP 主资源。关键不是收藏一堆链接，而是建立自己的资源判断系统：想用时有，用时选得对。", "", "", "", "toolbox.hero"),
            ("section", "五类入口", 10, "五类入口，按任务找资源", "", "先判断你要找的是“发现、学习、跟进、使用还是开发”，再进入对应类别，减少无效试错。", "", "", "", "toolbox.categories"),
            ("card", "综合导航站", 11, "AI 综合导航站", "Find", "快速发现新工具、按任务检索替代方案，适合作为找工具的第一入口。", "", "", "", "toolbox.nav"),
            ("link", "综合导航站", 12, "AI 工具集", "", "中文 AI 工具导航，适合按场景查找。", "", "AI 工具集", "https://ai-bot.cn/", "toolbox.nav.aibot"),
            ("link", "综合导航站", 13, "AIBase 产品库", "", "跟踪国内外 AI 产品与新品。", "", "AIBase 产品库", "https://top.aibase.com/", "toolbox.nav.aibase"),
            ("link", "综合导航站", 14, "There&apos;s An AI For That", "", "查海外小众产品和用例关键词。", "", "There's An AI For That", "https://theresanaiforthat.com/", "toolbox.nav.taaft"),
            ("card", "教程类", 20, "教程类", "Learn", "系统学习概念、提示词、开源模型和应用开发，建立可迁移的基础。", "", "", "", "toolbox.tutorial"),
            ("link", "教程类", 21, "OpenAI Academy", "", "AI 基础、ChatGPT 使用与应用入门。", "", "OpenAI Academy", "https://academy.openai.com/", "toolbox.tutorial.openai"),
            ("link", "教程类", 22, "DeepLearning.AI Courses", "", "生成式 AI 与模型应用课程库。", "", "DeepLearning.AI Courses", "https://www.deeplearning.ai/courses/", "toolbox.tutorial.deeplearning"),
            ("link", "教程类", 23, "Hugging Face Learn", "", "开源模型、Agent、扩散与多模态实践。", "", "Hugging Face Learn", "https://huggingface.co/learn", "toolbox.tutorial.hf"),
            ("card", "B站 UP 推荐", 30, "B站 UP 推荐", "Watch", "跟踪中文 AI 圈的产品测评、提示词、Agent 实战和通俗教程。", "", "", "", "toolbox.bilibili"),
            ("link", "B站 UP 推荐", 31, "歸藏的AI工具箱", "", "AI 产品、工具资讯与工作流。", "", "歸藏的AI工具箱", "https://space.bilibili.com/1741797/", "toolbox.bilibili.guizang"),
            ("link", "B站 UP 推荐", 32, "宝玉xp", "", "AI 编程、Agent 与产品实践。", "", "宝玉xp", "https://space.bilibili.com/589397373/", "toolbox.bilibili.baoyu"),
            ("card", "软件与小众工具", 40, "软件与小众工具", "Use", "把 AI 接进真实工作流：桌面客户端、本地模型、知识库和自动化。", "", "", "", "toolbox.software"),
            ("link", "软件与小众工具", 41, "Cherry Studio", "", "多模型桌面客户端与知识库。", "", "Cherry Studio", "https://cherryai.com/", "toolbox.software.cherry"),
            ("link", "软件与小众工具", 42, "Ollama", "", "在本机运行开源模型。", "", "Ollama", "https://ollama.com/", "toolbox.software.ollama"),
            ("link", "软件与小众工具", 43, "Dify", "", "构建 Agent、RAG 和 AI 应用。", "", "Dify", "https://dify.ai/", "toolbox.software.dify"),
            ("card", "API 推荐", 50, "API 推荐", "Build", "开发 AI 功能、自动化脚本和小工具；先比较能力、价格、上下文与稳定性。", "", "", "", "toolbox.api"),
            ("link", "API 推荐", 51, "OpenAI API", "", "通用多模态与 Agent 能力。", "", "OpenAI API", "https://platform.openai.com/docs", "toolbox.api.openai"),
            ("link", "API 推荐", 52, "Claude API", "", "长文本、写作、代码理解与知识任务。", "", "Claude API", "https://platform.claude.com/docs", "toolbox.api.claude"),
            ("link", "API 推荐", 53, "OpenRouter", "", "一个接口对接多模型，便于比较成本。", "", "OpenRouter", "https://openrouter.ai/docs/quickstart", "toolbox.api.openrouter"),
        ],
    },
}


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


def create_sync_table(token: str, app_token: str) -> str:
    payload = request_json(
        "POST",
        f"/bitable/v1/apps/{urllib.parse.quote(app_token)}/tables",
        token,
        {
            "table": {
                "name": "网站内容同步表",
                "default_view_name": "按页面维护",
                "fields": [{"field_name": name, "type": 1} for name in FIELD_NAMES],
            }
        },
    )
    table = payload.get("data", {}).get("table", {}) or payload.get("data", {})
    table_id = table.get("table_id")
    if not table_id:
        raise RuntimeError(f"Create table returned no table_id: {payload}")
    return str(table_id)


def make_record(page_name: str, page_path: str, index: int, item: tuple[str, str, int, str, str, str, str, str, str, str]) -> dict:
    module_type, section, order, title, tag, body, note, link_title, link_url, key = item
    return {
        "fields": {
            "内容ID": f"{page_name}-{index:03d}",
            "页面名称": page_name,
            "页面路径": page_path,
            "模块类型": module_type,
            "所属板块": section,
            "排序": str(order),
            "标题": title,
            "副标题/标签": tag,
            "正文": body,
            "小字/说明": note,
            "链接标题": link_title,
            "链接URL": link_url,
            "数据键": key,
            "是否启用": "是",
            "备注": "由 AI++ 页面内容转换，供后续飞书维护网站使用。",
        }
    }


def batch_create_records(token: str, app_token: str, table_id: str, records: list[dict]) -> None:
    for start in range(0, len(records), 400):
        chunk = records[start : start + 400]
        request_json(
            "POST",
            f"/bitable/v1/apps/{urllib.parse.quote(app_token)}/tables/{urllib.parse.quote(table_id)}/records/batch_create",
            token,
            {"records": chunk},
        )
        time.sleep(0.25)


def main() -> int:
    token = tenant_access_token()
    results = []
    for page_name, config in APPS.items():
        table_id = create_sync_table(token, config["token"])
        records = [
            make_record(page_name, config["path"], idx, item)
            for idx, item in enumerate(config["records"], start=1)
        ]
        batch_create_records(token, config["token"], table_id, records)
        results.append(
            {
                "page": page_name,
                "table_id": table_id,
                "record_count": len(records),
                "bitable_url": f"https://my.feishu.cn/base/{config['token']}",
            }
        )
    print("AI_PLUS_BITABLE_POPULATE_RESULTS=" + json.dumps(results, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
