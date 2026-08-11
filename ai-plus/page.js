const defaultModules = [
  { number: "00", slug: "overview", title: "AI 概述", tag: "共同语言", description: "从计算、识别、生成到行动；先分清模型、工具、Agent、Skill 与工作流，才能正确选择方法。", question: "当 AI 给出答案时，我们是否先定义好了问题？", points: ["能力演变：计算 → 识别 → 生成 → 行动", "概念关系：模型、工具、Agent、Skill、工作流", "人的责任：问题、上下文、判断、验收"] },
  { number: "01", slug: "office", title: "日常增效", tag: "研究 / 表达 / 协同", description: "把 Brief、研究资料、方案结构、会议纪要与待办事项整理为可追溯、可审核的项目情报。", question: "怎样把零散项目资料变成能够讨论和推进的方案依据？", points: ["Brief 拆解与待确认项", "案例研究与来源核验", "方案目录、会议纪要与行动清单"] },
  { number: "02", slug: "open-models", title: "开源模型", tag: "视觉工作流", description: "以 ComfyUI 为视觉工作流入口，理解参考控制、局部修正、版本复现与团队交接。", question: "怎样让视觉生成从碰运气，变成可控制、可复现的过程？", points: ["参考图、构图与局部控制", "工作流、节点与版本记录", "从主视觉探索到方案板输出"] },
  { number: "03", slug: "agents", title: "Agent 智能体", tag: "协作 / 权限 / Skill", description: "理解在线模型、工作区 Agent、自动化 Agent 与 Skill 的协同边界；权限越高，人工审核越重要。", question: "何时只需对话，何时让 Agent 在受控范围内执行？", points: ["聊天模型、工作区 Agent、自动化 Agent", "Skill：岗位经验的可复用说明", "权限、日志、人工审核与责任"] },
  { number: "04", slug: "toolbox", title: "AI 工具箱", tag: "持续更新", description: "沉淀经实际验证的办公软件、Chrome 插件、开源模型、GitHub 项目、B 站学习路径与实测记录。", question: "工具如何变成团队资产，而不是不断过期的收藏夹？", points: ["按任务和岗位，而不是按产品 Logo 分类", "记录输入、输出、实测、风险和复核日期", "将教程、插件、模型和 Skill 连接到真实案例"] }
];

async function getModules() {
  try {
    const response = await fetch("../api/ai-plus.json", { cache: "no-store" });
    if (!response.ok) throw new Error("content unavailable");
    const data = await response.json();
    return Array.isArray(data.modules) ? data.modules.map((item) => ({ ...defaultModules.find((entry) => entry.slug === item.slug), ...item })) : defaultModules;
  } catch { return defaultModules; }
}

async function renderPage() {
  const modules = await getModules();
  const slug = document.body.dataset.section;
  const item = modules.find((entry) => entry.slug === slug) || modules[0];
  const rail = document.querySelector("[data-section-rail]");
  if (rail) rail.innerHTML = modules.map((entry) => `<a href="./${entry.slug}.html"${entry.slug === slug ? ' aria-current="page"' : ""}><strong>${entry.number}</strong><span>${entry.title}</span></a>`).join("");
  document.title = `${item.title}｜AI+ 展览设计训练营`;
  document.querySelector("[data-number]").textContent = item.number;
  document.querySelector("[data-title]").textContent = item.title;
  document.querySelector("[data-tag]").textContent = item.tag;
  document.querySelector("[data-description]").textContent = item.description;
  document.querySelector("[data-question]").textContent = item.question;
  document.querySelector("[data-points]").innerHTML = (item.points || []).map((point, index) => `<li><b>0${index + 1}</b>${point}</li>`).join("");
}

renderPage();
