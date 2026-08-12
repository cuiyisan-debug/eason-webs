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
    "overview": [
        {
            "key": "overview.term.context",
            "fields": {
                "内容ID": "overview-term-context",
                "模块类型": "term",
                "所属板块": "核心名词",
                "排序": "33",
                "标题": "上下文窗口",
                "正文": "模型一次能“看见”的信息范围，包括系统规则、用户问题、历史对话、文件片段和工具返回结果。",
                "小字/说明": "上下文不是长期记忆。窗口外的信息如果没有被重新放进来，模型就无法可靠使用。",
                "数据键": "overview.term.context",
                "是否启用": "是",
                "备注": "恢复 AI 概述原静态页核心名词。",
            },
        },
        {
            "key": "overview.term.prompt",
            "fields": {
                "内容ID": "overview-term-prompt",
                "模块类型": "term",
                "所属板块": "核心名词",
                "排序": "34",
                "标题": "Prompt",
                "正文": "不是魔法咒语，而是任务说明。好 Prompt 应该交代目标、角色、输入材料、限制、输出格式和判断标准。",
                "小字/说明": "提示词工程的本质，是把“你脑子里的隐含要求”显性化。",
                "数据键": "overview.term.prompt",
                "是否启用": "是",
                "备注": "恢复 AI 概述原静态页核心名词。",
            },
        },
        {
            "key": "overview.term.rag",
            "fields": {
                "内容ID": "overview-term-rag",
                "模块类型": "term",
                "所属板块": "核心名词",
                "排序": "35",
                "标题": "RAG",
                "正文": "检索增强生成。先从资料库里找相关内容，再把内容交给模型回答，用来降低胡编和补充专有知识。",
                "小字/说明": "RAG 的上限很依赖资料质量、切分方式、检索准确率和引用校验。",
                "数据键": "overview.term.rag",
                "是否启用": "是",
                "备注": "恢复 AI 概述原静态页核心名词。",
            },
        },
        {
            "key": "overview.term.embedding",
            "fields": {
                "内容ID": "overview-term-embedding",
                "模块类型": "term",
                "所属板块": "核心名词",
                "排序": "36",
                "标题": "Embedding",
                "正文": "把文本、图片等内容转换成向量，让机器能比较“语义距离”。常用于搜索、聚类、推荐和知识库检索。",
                "小字/说明": "Embedding 不是摘要，而是一种方便机器比较相似度的表示方式。",
                "数据键": "overview.term.embedding",
                "是否启用": "是",
                "备注": "恢复 AI 概述原静态页核心名词。",
            },
        },
        {
            "key": "overview.term.finetuning",
            "fields": {
                "内容ID": "overview-term-finetuning",
                "模块类型": "term",
                "所属板块": "核心名词",
                "排序": "37",
                "标题": "Fine-tuning",
                "正文": "在已有模型基础上继续训练，让模型更贴近某种格式、语气或专业任务。",
                "小字/说明": "很多场景先用提示词、资料库、模板和工作流就够了，不必一上来微调。",
                "数据键": "overview.term.finetuning",
                "是否启用": "是",
                "备注": "恢复 AI 概述原静态页核心名词。",
            },
        },
        {
            "key": "overview.term.skill",
            "fields": {
                "内容ID": "overview-term-skill",
                "模块类型": "term",
                "所属板块": "核心名词",
                "排序": "38",
                "标题": "Skill",
                "正文": "可复用的工作能力包，通常包含说明、规范、示例、素材、脚本或工具连接。它让 AI 按一套稳定流程做事。",
                "小字/说明": "Skill 是把经验产品化。比如“生成策划 PPT”“整理飞书文章”“压缩图片”都可以做成 Skill。",
                "数据键": "overview.term.skill",
                "是否启用": "是",
                "备注": "恢复 AI 概述原静态页核心名词。",
            },
        },
        {
            "key": "overview.term.mcp",
            "fields": {
                "内容ID": "overview-term-mcp",
                "模块类型": "term",
                "所属板块": "核心名词",
                "排序": "39",
                "标题": "MCP",
                "正文": "AI 说“我要看现在的数据库结构”，通过 MCP 接到你的数据库、素材库或软件环境。",
                "小字/说明": "比如 Eagle、SketchUp 等工具可以通过 MCP 被 AI 调用或控制。MCP 的价值，是把 AI 从聊天框接到真实工具和数据源。",
                "数据键": "overview.term.mcp",
                "是否启用": "是",
                "备注": "AI++ 概述核心名词新增。",
            },
        },
        {
            "key": "overview.term.cli",
            "fields": {
                "内容ID": "overview-term-cli",
                "模块类型": "term",
                "所属板块": "核心名词",
                "排序": "40",
                "标题": "CLI",
                "正文": "你打在命令行里的这句话，会被 CLI 层接收；它负责解析意图、管理会话并把任务交给工具执行。",
                "小字/说明": "比如围绕飞书同步、GitHub 操作、本地文件处理，CLI 像是 AI 与系统之间的任务控制台。",
                "数据键": "overview.term.cli",
                "是否启用": "是",
                "备注": "AI++ 概述核心名词新增。",
            },
        },
        {
            "key": "overview.term.vibe-coding",
            "fields": {
                "内容ID": "overview-term-vibe-coding",
                "模块类型": "term",
                "所属板块": "核心名词",
                "排序": "41",
                "标题": "Vibe Coding（氛围编程）",
                "正文": "用自然语言驱动编程：边聊边写、边看边改，把想法快速推进成可运行的原型。",
                "小字/说明": "它降低了开始写程序的门槛，但不等于可以跳过测试、结构设计和代码审查。",
                "数据键": "overview.term.vibe-coding",
                "是否启用": "是",
                "备注": "AI++ 概述核心名词新增。",
            },
        },
        {
            "key": "overview.tool.talk",
            "fields": {
                "内容ID": "overview-tool-talk",
                "模块类型": "tool",
                "所属板块": "工具分类",
                "排序": "41",
                "标题": "对话与研究",
                "副标题/标签": "Conversation",
                "正文": "用自然语言完成问答、梳理、翻译、改写、头脑风暴、资料摘要和方案推演。",
                "小字/说明": "代表：ChatGPT、Claude、Gemini、Perplexity 等。适合先把问题想清楚，再形成提纲、观点、清单和判断。",
                "数据键": "overview.tool.talk",
                "是否启用": "是",
                "备注": "恢复 AI 概述工具分类卡片。",
            },
        },
        {
            "key": "overview.tool.image",
            "fields": {
                "内容ID": "overview-tool-image",
                "模块类型": "tool",
                "所属板块": "工具分类",
                "排序": "42",
                "标题": "图像与设计",
                "副标题/标签": "Image",
                "正文": "从文字、参考图或草图生成视觉方案，也能扩图、改图、抠图、统一风格。",
                "小字/说明": "代表：Midjourney、Adobe Firefly、ChatGPT 图像、Stable Diffusion 生态等。注意商用授权与人物肖像边界。",
                "数据键": "overview.tool.image",
                "是否启用": "是",
                "备注": "恢复 AI 概述工具分类卡片。",
            },
        },
        {
            "key": "overview.tool.video",
            "fields": {
                "内容ID": "overview-tool-video",
                "模块类型": "tool",
                "所属板块": "工具分类",
                "排序": "43",
                "标题": "视频与音频",
                "副标题/标签": "Video",
                "正文": "生成短视频、分镜预演、口播、配音、音乐、字幕和快速剪辑版本。",
                "小字/说明": "代表：Sora、Veo、Runway、可灵、剪映 AI、ElevenLabs 等。时长、连续性和版权仍需人工把关。",
                "数据键": "overview.tool.video",
                "是否启用": "是",
                "备注": "恢复 AI 概述工具分类卡片。",
            },
        },
        {
            "key": "overview.tool.office",
            "fields": {
                "内容ID": "overview-tool-office",
                "模块类型": "tool",
                "所属板块": "工具分类",
                "排序": "44",
                "标题": "办公与知识",
                "副标题/标签": "Office",
                "正文": "围绕文档、表格、PPT、会议、邮件和知识库，提高组织、总结和交付效率。",
                "小字/说明": "代表：Microsoft 365 Copilot、Google Workspace Gemini、Notion AI、Gamma 等。注意企业数据权限与引用来源。",
                "数据键": "overview.tool.office",
                "是否启用": "是",
                "备注": "恢复 AI 概述工具分类卡片。",
            },
        },
        {
            "key": "overview.tool.code",
            "fields": {
                "内容ID": "overview-tool-code",
                "模块类型": "tool",
                "所属板块": "工具分类",
                "排序": "45",
                "标题": "代码与数据",
                "副标题/标签": "Code",
                "正文": "辅助写代码、读仓库、查 Bug、生成脚本、分析数据、搭建小工具和验证结果。",
                "小字/说明": "代表：Codex、Cursor、GitHub Copilot、Claude Code、数据分析助手等。必须测试，敏感密钥不能交给不可信环境。",
                "数据键": "overview.tool.code",
                "是否启用": "是",
                "备注": "恢复 AI 概述工具分类卡片。",
            },
        },
        {
            "key": "overview.tool.agent",
            "fields": {
                "内容ID": "overview-tool-agent",
                "模块类型": "tool",
                "所属板块": "工具分类",
                "排序": "46",
                "标题": "智能体与自动化",
                "副标题/标签": "Agent",
                "正文": "让 AI 按目标拆任务，连接浏览器、文件、日历、数据库、邮件和内部系统执行动作。",
                "小字/说明": "代表：OpenAI Agents SDK、Dify、n8n、Zapier、企业内部 Agent 平台等。权限、审批、日志和回滚比模型本身更关键。",
                "数据键": "overview.tool.agent",
                "是否启用": "是",
                "备注": "恢复 AI 概述工具分类卡片。",
            },
        },
    ],
    "toolbox": [
        {
            "key": "toolbox.bilibili.guizang",
            "fields": {
                "是否启用": "否",
                "数据键": "toolbox.bilibili.guizang",
                "备注": "B站 UP 推荐按用户新名单替换，旧记录停用。",
            },
        },
        {
            "key": "toolbox.bilibili.baoyu",
            "fields": {
                "是否启用": "否",
                "数据键": "toolbox.bilibili.baoyu",
                "备注": "B站 UP 推荐按用户新名单替换，旧记录停用。",
            },
        },
        {
            "key": "toolbox.bilibili.limu",
            "fields": {
                "是否启用": "否",
                "数据键": "toolbox.bilibili.limu",
                "备注": "B站 UP 推荐按用户新名单替换，旧记录停用。",
            },
        },
        {
            "key": "toolbox.bilibili.fange",
            "fields": {
                "是否启用": "否",
                "数据键": "toolbox.bilibili.fange",
                "备注": "B站 UP 推荐按用户新名单替换，旧记录停用。",
            },
        },
        {
            "key": "toolbox.bilibili.heihei001",
            "fields": {
                "内容ID": "toolbox-bilibili-heihei001",
                "模块类型": "link",
                "所属板块": "B站 UP 推荐",
                "排序": "31",
                "标题": "黑鹤001",
                "正文": "ComfyUI 整合包。",
                "链接标题": "打开 B站主页",
                "链接URL": "https://space.bilibili.com/515231056?spm_id_from=333.1387.follow.user_card.click",
                "数据键": "toolbox.bilibili.heihei001",
                "是否启用": "是",
                "备注": "AI++ 工具箱 B站 UP 推荐新名单。",
            },
        },
        {
            "key": "toolbox.bilibili.dayu",
            "fields": {
                "内容ID": "toolbox-bilibili-dayu",
                "模块类型": "link",
                "所属板块": "B站 UP 推荐",
                "排序": "32",
                "标题": "comfyui大鱼老师",
                "正文": "ComfyUI 教程。",
                "链接标题": "打开 B站主页",
                "链接URL": "https://space.bilibili.com/1464283375?spm_id_from=333.1387.follow.user_card.click",
                "数据键": "toolbox.bilibili.dayu",
                "是否启用": "是",
                "备注": "AI++ 工具箱 B站 UP 推荐新名单。",
            },
        },
        {
            "key": "toolbox.bilibili.nenly",
            "fields": {
                "内容ID": "toolbox-bilibili-nenly",
                "模块类型": "link",
                "所属板块": "B站 UP 推荐",
                "排序": "33",
                "标题": "Nenly同学",
                "正文": "AI 教程。",
                "链接标题": "打开 B站主页",
                "链接URL": "https://space.bilibili.com/1814756990?spm_id_from=333.1387.follow.user_card.click",
                "数据键": "toolbox.bilibili.nenly",
                "是否启用": "是",
                "备注": "AI++ 工具箱 B站 UP 推荐新名单。",
            },
        },
        {
            "key": "toolbox.bilibili.tetae",
            "fields": {
                "内容ID": "toolbox-bilibili-tetae",
                "模块类型": "link",
                "所属板块": "B站 UP 推荐",
                "排序": "34",
                "标题": "TETAE",
                "正文": "ComfyUI 启动器。",
                "链接标题": "打开 B站主页",
                "链接URL": "https://space.bilibili.com/361444771?spm_id_from=333.337.search-card.all.click",
                "数据键": "toolbox.bilibili.tetae",
                "是否启用": "是",
                "备注": "AI++ 工具箱 B站 UP 推荐新名单。",
            },
        },
        {
            "key": "toolbox.software.zlib",
            "fields": {
                "内容ID": "toolbox-software-zlib",
                "模块类型": "link",
                "所属板块": "软件与小众工具",
                "排序": "44",
                "标题": "Z-Library",
                "正文": "图书与文献检索下载站，适合查找电子书和参考资料；使用时注意版权与合规边界。",
                "链接标题": "打开网站",
                "链接URL": "https://zh.z-lib.fm/",
                "数据键": "toolbox.software.zlib",
                "是否启用": "是",
                "备注": "AI++ 工具箱新增软件与小众工具。",
            },
        },
        {
            "key": "toolbox.software.500px",
            "fields": {
                "内容ID": "toolbox-software-500px",
                "模块类型": "link",
                "所属板块": "软件与小众工具",
                "排序": "45",
                "标题": "500px 中国",
                "正文": "高质量摄影作品网站，适合查找构图、光影、色彩和视觉氛围参考。",
                "链接标题": "打开网站",
                "链接URL": "https://500px.com.cn/",
                "数据键": "toolbox.software.500px",
                "是否启用": "是",
                "备注": "AI++ 工具箱新增软件与小众工具。",
            },
        },
        {
            "key": "toolbox.api.openai",
            "fields": {
                "是否启用": "否",
                "数据键": "toolbox.api.openai",
                "备注": "API 推荐按用户新名单替换，旧记录停用。",
            },
        },
        {
            "key": "toolbox.api.claude",
            "fields": {
                "是否启用": "否",
                "数据键": "toolbox.api.claude",
                "备注": "API 推荐按用户新名单替换，旧记录停用。",
            },
        },
        {
            "key": "toolbox.api.openrouter",
            "fields": {
                "是否启用": "否",
                "数据键": "toolbox.api.openrouter",
                "备注": "API 推荐按用户新名单替换，旧记录停用。",
            },
        },
        {
            "key": "toolbox.api.siliconflow",
            "fields": {
                "内容ID": "toolbox-api-siliconflow",
                "模块类型": "link",
                "所属板块": "API 推荐",
                "排序": "51",
                "标题": "硅基流动 SiliconFlow",
                "正文": "一站式大模型 API 与推理服务平台，适合按任务接入国产和开源模型能力。",
                "链接标题": "打开网站",
                "链接URL": "https://www.siliconflow.cn/",
                "数据键": "toolbox.api.siliconflow",
                "是否启用": "是",
                "备注": "AI++ 工具箱 API 推荐新名单。",
            },
        },
        {
            "key": "toolbox.api.sillydream",
            "fields": {
                "内容ID": "toolbox-api-sillydream",
                "模块类型": "link",
                "所属板块": "API 推荐",
                "排序": "52",
                "标题": "SillyDream API",
                "正文": "统一 AI API 网关，适合把不同模型服务接入到脚本、小工具和工作流里。",
                "链接标题": "打开网站",
                "链接URL": "https://wish.sillydream.top/",
                "数据键": "toolbox.api.sillydream",
                "是否启用": "是",
                "备注": "AI++ 工具箱 API 推荐新名单。",
            },
        },
        {
            "key": "toolbox.api.zhenzhen",
            "fields": {
                "内容ID": "toolbox-api-zhenzhen",
                "模块类型": "link",
                "所属板块": "API 推荐",
                "排序": "53",
                "标题": "zhenzhen",
                "正文": "面向 ComfyUI 等创作流程的平价 API 调用节点，适合把线上模型接入本地工作流。",
                "链接标题": "打开网站",
                "链接URL": "https://ai.t8star.org/zh",
                "数据键": "toolbox.api.zhenzhen",
                "是否启用": "是",
                "备注": "AI++ 工具箱 API 推荐新名单。",
            },
        },
        {
            "key": "toolbox.canvas",
            "fields": {
                "内容ID": "toolbox-canvas",
                "模块类型": "card",
                "所属板块": "线上画布入口",
                "排序": "60",
                "标题": "线上画布入口",
                "副标题/标签": "Canvas",
                "正文": "把在线画布、云端 ComfyUI 和空间化创作平台作为快速试验入口，再把稳定流程沉淀成本地或团队工作流。",
                "数据键": "toolbox.canvas",
                "是否启用": "是",
                "备注": "与开源模型页面线上画布入口保持同源维护。",
            },
        },
        {
            "key": "toolbox.canvas.tapnow",
            "fields": {
                "内容ID": "toolbox-canvas-tapnow",
                "模块类型": "link",
                "所属板块": "线上画布入口",
                "排序": "61",
                "标题": "TapNow",
                "正文": "Agentic Creative Canvas，把文案、图像与创意素材放在同一画布中持续组织和迭代。",
                "链接标题": "打开网站",
                "链接URL": "https://app.tapnow.ai/home",
                "数据键": "toolbox.canvas.tapnow",
                "是否启用": "是",
                "备注": "线上画布入口同步到 AI 工具箱。",
            },
        },
        {
            "key": "toolbox.canvas.runninghub",
            "fields": {
                "内容ID": "toolbox-canvas-runninghub",
                "模块类型": "link",
                "所属板块": "线上画布入口",
                "排序": "62",
                "标题": "RunningHub",
                "正文": "云端 ComfyUI 与 AI 应用平台，支持在线运行工作流、应用发布和协作创作。",
                "链接标题": "打开网站",
                "链接URL": "https://www.runninghub.cn/",
                "数据键": "toolbox.canvas.runninghub",
                "是否启用": "是",
                "备注": "线上画布入口同步到 AI 工具箱。",
            },
        },
        {
            "key": "toolbox.canvas.aix",
            "fields": {
                "内容ID": "toolbox-canvas-aix",
                "模块类型": "link",
                "所属板块": "线上画布入口",
                "排序": "63",
                "标题": "AIX Studio",
                "正文": "面向 AI 视觉创作的工作流平台，适合查找与复用图像、视频和设计类创作流程。",
                "链接标题": "打开网站",
                "链接URL": "https://aix.studio/creation/WorkFlowListNew",
                "数据键": "toolbox.canvas.aix",
                "是否启用": "是",
                "备注": "线上画布入口同步到 AI 工具箱。",
            },
        },
        {
            "key": "toolbox.canvas.lovart",
            "fields": {
                "内容ID": "toolbox-canvas-lovart",
                "模块类型": "link",
                "所属板块": "线上画布入口",
                "排序": "64",
                "标题": "Lovart",
                "正文": "AI 设计智能体与创意平台，适合把品牌视觉、海报和图像探索组织成可迭代的创作过程。",
                "链接标题": "打开网站",
                "链接URL": "https://www.lovart.ai/zh?",
                "数据键": "toolbox.canvas.lovart",
                "是否启用": "是",
                "备注": "线上画布入口同步到 AI 工具箱。",
            },
        },
        {
            "key": "toolbox.canvas.easyai",
            "fields": {
                "内容ID": "toolbox-canvas-easyai",
                "模块类型": "link",
                "所属板块": "线上画布入口",
                "排序": "65",
                "标题": "EasyAI",
                "正文": "企业级 AIGC 应用平台，面向图文视频生成、工作流搭建和团队内容生产。",
                "链接标题": "打开网站",
                "链接URL": "https://51easyai.com/home",
                "数据键": "toolbox.canvas.easyai",
                "是否启用": "是",
                "备注": "线上画布入口同步到 AI 工具箱。",
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
        {
            "key": "office.habit.article.001",
            "fields": {
                "内容ID": "office-habit-article-001",
                "模块类型": "case",
                "所属板块": "工作习惯建议",
                "排序": "44",
                "标题": "工作习惯应用实例",
                "副标题/标签": "FEISHU DOC / HABIT",
                "正文": "以飞书云文档沉淀日常工作习惯、任务推进节奏和可复用流程。",
                "小字/说明": "独立飞书云文档文章卡；封面留空时由文档首图自动兜底。",
                "链接标题": "打开飞书文章",
                "链接URL": "https://my.feishu.cn/docx/GGr3d9UQso5eY8xXsOYc8DOznuh",
                "封面": "",
                "数据键": "office.habit.article.001",
                "是否启用": "是",
                "备注": "日常增效 / 工作习惯建议下新增飞书文章卡。",
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
        {
            "key": "models.canvas.comfyui",
            "fields": {
                "是否启用": "否",
                "数据键": "models.canvas.comfyui",
                "备注": "线上画布入口按用户新名单替换，旧 ComfyUI 链接停用。",
            },
        },
        {
            "key": "models.canvas.tapnow",
            "fields": {
                "内容ID": "models-canvas-tapnow",
                "模块类型": "link",
                "所属板块": "无限画布",
                "排序": "41",
                "标题": "TapNow",
                "正文": "Agentic Creative Canvas，把文案、图像与创意素材放在同一画布中持续组织和迭代。",
                "链接标题": "打开网站",
                "链接URL": "https://app.tapnow.ai/home",
                "数据键": "models.canvas.tapnow",
                "是否启用": "是",
                "备注": "开源模型页面线上画布入口新名单。",
            },
        },
        {
            "key": "models.canvas.runninghub",
            "fields": {
                "内容ID": "models-canvas-runninghub",
                "模块类型": "link",
                "所属板块": "无限画布",
                "排序": "42",
                "标题": "RunningHub",
                "正文": "云端 ComfyUI 与 AI 应用平台，支持在线运行工作流、应用发布和协作创作。",
                "链接标题": "打开网站",
                "链接URL": "https://www.runninghub.cn/",
                "数据键": "models.canvas.runninghub",
                "是否启用": "是",
                "备注": "开源模型页面线上画布入口新名单。",
            },
        },
        {
            "key": "models.canvas.aix",
            "fields": {
                "内容ID": "models-canvas-aix",
                "模块类型": "link",
                "所属板块": "无限画布",
                "排序": "43",
                "标题": "AIX Studio",
                "正文": "面向 AI 视觉创作的工作流平台，适合查找与复用图像、视频和设计类创作流程。",
                "链接标题": "打开网站",
                "链接URL": "https://aix.studio/creation/WorkFlowListNew",
                "数据键": "models.canvas.aix",
                "是否启用": "是",
                "备注": "开源模型页面线上画布入口新名单。",
            },
        },
        {
            "key": "models.canvas.lovart",
            "fields": {
                "内容ID": "models-canvas-lovart",
                "模块类型": "link",
                "所属板块": "无限画布",
                "排序": "44",
                "标题": "Lovart",
                "正文": "AI 设计智能体与创意平台，适合把品牌视觉、海报和图像探索组织成可迭代的创作过程。",
                "链接标题": "打开网站",
                "链接URL": "https://www.lovart.ai/zh?",
                "数据键": "models.canvas.lovart",
                "是否启用": "是",
                "备注": "开源模型页面线上画布入口新名单。",
            },
        },
        {
            "key": "models.canvas.easyai",
            "fields": {
                "内容ID": "models-canvas-easyai",
                "模块类型": "link",
                "所属板块": "无限画布",
                "排序": "45",
                "标题": "EasyAI",
                "正文": "企业级 AIGC 应用平台，面向图文视频生成、工作流搭建和团队内容生产。",
                "链接标题": "打开网站",
                "链接URL": "https://51easyai.com/home",
                "数据键": "models.canvas.easyai",
                "是否启用": "是",
                "备注": "开源模型页面线上画布入口新名单。",
            },
        },
        {
            "key": "models.minimax",
            "fields": {
                "内容ID": "models-minimax",
                "模块类型": "card",
                "所属板块": "常见开源大模型",
                "排序": "25",
                "标题": "MiniMax",
                "副标题/标签": "音视频 / 多模态",
                "正文": "适合关注视频、语音和多模态应用的开发者，用作线上能力与本地工作流的对照组。",
                "小字/说明": "适合：需要比较模型能力、API 与开源生态边界的场景。选型：先区分开放权重、开放代码和 API 服务，不要混为“免费开源”。",
                "链接标题": "MiniMax 官方组织",
                "链接URL": "https://github.com/MiniMax-AI",
                "数据键": "models.minimax",
                "是否启用": "是",
                "备注": "恢复常见开源大模型卡片。",
            },
        },
        {
            "key": "models.seedvr2",
            "fields": {
                "内容ID": "models-seedvr2",
                "模块类型": "card",
                "所属板块": "常见开源大模型",
                "排序": "26",
                "标题": "SeedVR2",
                "副标题/标签": "视频修复",
                "正文": "面向视频恢复与增强，适合放在生成工作流的后处理环节，而不是当作主生成模型。",
                "小字/说明": "适合：提升视频清晰度、细节和连续帧观感。选型：把它放在生成、插帧或放大之后，观察速度和画面稳定性。",
                "链接标题": "SeedVR2 官方仓库",
                "链接URL": "https://github.com/IceClear/SeedVR2",
                "数据键": "models.seedvr2",
                "是否启用": "是",
                "备注": "恢复常见开源大模型卡片。",
            },
        },
    ],
    "agents": [
        {
            "key": "agents.case",
            "fields": {
                "内容ID": "agents-case-section",
                "模块类型": "section",
                "所属板块": "应用实例",
                "排序": "30",
                "标题": "应用实例",
                "正文": "把 Agent 从概念放回真实任务中观察：它如何理解目标、调用工具、执行步骤、检查结果，并在人的确认边界内继续推进。",
                "数据键": "agents.case",
                "是否启用": "是",
                "备注": "Agent 智能体 / 应用实例板块。",
            },
        },
        {
            "key": "agents.case.001",
            "fields": {
                "内容ID": "agents-case-001",
                "模块类型": "case",
                "所属板块": "应用实例",
                "排序": "31",
                "标题": "Agent 应用实例 01",
                "副标题/标签": "FEISHU DOC / AGENT",
                "正文": "从飞书云文档读取案例内容，沉淀 Agent 平台、任务目标、执行步骤和验证结果。",
                "小字/说明": "独立飞书云文档文章卡；封面留空时由文档首图自动兜底。",
                "链接标题": "打开飞书案例文档",
                "链接URL": "https://my.feishu.cn/docx/BGbWd7Y8mosFzlxOYK4cUiiWntb",
                "封面": "",
                "数据键": "agents.case.001",
                "是否启用": "是",
                "备注": "Agent 智能体 / 应用实例新增飞书文章卡。",
            },
        },
        {
            "key": "agents.case.002",
            "fields": {
                "内容ID": "agents-case-002",
                "模块类型": "case",
                "所属板块": "应用实例",
                "排序": "32",
                "标题": "Agent 应用实例 02",
                "副标题/标签": "FEISHU DOC / AGENT",
                "正文": "从飞书云文档读取案例内容，沉淀 Agent 平台、任务目标、执行步骤和验证结果。",
                "小字/说明": "独立飞书云文档文章卡；封面留空时由文档首图自动兜底。",
                "链接标题": "打开飞书案例文档",
                "链接URL": "https://my.feishu.cn/docx/C4VtdiGbBoEev4xQt1Lc4ZYsnMc",
                "封面": "",
                "数据键": "agents.case.002",
                "是否启用": "是",
                "备注": "Agent 智能体 / 应用实例新增飞书文章卡。",
            },
        },
        {
            "key": "agents.case.003",
            "fields": {
                "内容ID": "agents-case-003",
                "模块类型": "case",
                "所属板块": "应用实例",
                "排序": "33",
                "标题": "Agent 应用实例 03",
                "副标题/标签": "FEISHU DOC / AGENT",
                "正文": "从飞书云文档读取案例内容，沉淀 Agent 平台、任务目标、执行步骤和验证结果。",
                "小字/说明": "独立飞书云文档文章卡；封面留空时由文档首图自动兜底。",
                "链接标题": "打开飞书案例文档",
                "链接URL": "https://my.feishu.cn/docx/YGx6dGvnjonv9WxncQBckbGcnyf",
                "封面": "",
                "数据键": "agents.case.003",
                "是否启用": "是",
                "备注": "Agent 智能体 / 应用实例新增飞书文章卡。",
            },
        },
        {
            "key": "agents.workbuddy",
            "fields": {
                "内容ID": "agents-workbuddy",
                "模块类型": "card",
                "所属板块": "常见平台",
                "排序": "24",
                "标题": "WorkBuddy",
                "副标题/标签": "办公智能体",
                "正文": "面向办公与团队任务协作的智能体平台，适合观察 AI 如何进入日常工作流和组织流程。",
                "小字/说明": "选平台时重点看账号体系、工具连接、权限边界和团队协作能力。",
                "数据键": "agents.workbuddy",
                "是否启用": "是",
                "备注": "Agent 智能体常见平台新增。",
            },
        },
        {
            "key": "agents.openclaw",
            "fields": {
                "内容ID": "agents-openclaw",
                "模块类型": "card",
                "所属板块": "常见平台",
                "排序": "25",
                "标题": "OpenClaw",
                "副标题/标签": "开源个人 Agent",
                "正文": "开源个人 AI 助手方向，强调从聊天入口进入本机设备和实际任务执行。",
                "小字/说明": "适合理解 Agent 如何连接桌面、消息应用与外部工具；同时要关注本地权限与隐私边界。",
                "数据键": "agents.openclaw",
                "是否启用": "是",
                "备注": "Agent 智能体常见平台新增。",
            },
        },
        {
            "key": "agents.claude-code",
            "fields": {
                "内容ID": "agents-claude-code",
                "模块类型": "card",
                "所属板块": "常见平台",
                "排序": "26",
                "标题": "Claude Code",
                "副标题/标签": "编码智能体",
                "正文": "Anthropic 面向开发者的编码 Agent，适合命令行、IDE 和复杂代码任务协作。",
                "小字/说明": "适合读代码、改仓库、解释工程结构和协助调试；关键仍是测试与人工验收。",
                "链接标题": "Claude Code 文档",
                "链接URL": "https://docs.anthropic.com/en/docs/claude-code/overview",
                "数据键": "agents.claude-code",
                "是否启用": "是",
                "备注": "Agent 智能体常见平台新增。",
            },
        },
        {
            "key": "agents.hermes-agent",
            "fields": {
                "内容ID": "agents-hermes-agent",
                "模块类型": "card",
                "所属板块": "常见平台",
                "排序": "27",
                "标题": "Hermes Agent",
                "副标题/标签": "任务型 Agent",
                "正文": "用于观察任务型智能体的另一类产品形态：把目标拆解、工具调用和执行反馈组织成连续流程。",
                "小字/说明": "纳入对比时重点看它能连接哪些工具、如何保留日志、是否支持人工确认与回滚。",
                "数据键": "agents.hermes-agent",
                "是否启用": "是",
                "备注": "Agent 智能体常见平台新增。",
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
    incoming_fields = {
        "页面名称": page.name,
        "页面路径": page.path,
        **row["fields"],
    }
    target = existing.get(row["key"])
    if target:
        record_id = str(target["record_id"])
        fields = {
            **(target.get("fields") or {}),
            **incoming_fields,
        }
        request_json(
            "PUT",
            f"/bitable/v1/apps/{page.app_token}/tables/{page.table_id}/records/{record_id}",
            token,
            {"fields": fields},
        )
        action = "updated"
    else:
        if row.get("fields", {}).get("是否启用") == "否":
            return {"page": page.key, "action": "skipped", "recordId": "", "dataKey": row["key"]}
        fields = incoming_fields
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
