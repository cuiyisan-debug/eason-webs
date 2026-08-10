const fallbackModules = [
  { number: "00", slug: "overview", title: "AI 概述", description: "从计算、识别、生成到行动；先分清模型、工具、Agent、Skill 与工作流，才能正确选择方法。", tag: "共同语言" },
  { number: "01", slug: "office", title: "日常增效", description: "把 Brief、研究资料、方案结构、会议纪要与待办事项整理为可追溯、可审核的项目情报。", tag: "研究 / 表达 / 协同" },
  { number: "02", slug: "open-models", title: "开源模型应用", description: "以 ComfyUI 为视觉工作流入口，理解参考控制、局部修正、版本复现与团队交接。", tag: "视觉工作流" },
  { number: "03", slug: "agents", title: "Agent 智能体", description: "理解在线模型、工作区 Agent、自动化 Agent 与 Skill 的协同边界；权限越高，人工审核越重要。", tag: "协作 / 权限 / Skill" },
  { number: "04", slug: "toolbox", title: "AI 工具箱", description: "沉淀经实际验证的办公软件、Chrome 插件、开源模型、GitHub 项目、B 站学习路径与实测记录。", tag: "持续更新" }
];

function renderModules(modules) {
  const index = document.querySelector("#module-index");
  const list = document.querySelector("#module-list");
  index.innerHTML = modules.map((item) => `<a href="./${item.slug}.html"><strong>${item.number}</strong>${item.title}</a>`).join("");
  list.innerHTML = modules.map((item) => `
    <article class="module" id="${item.slug}">
      <div class="module-number">${item.number}</div>
      <h3><a href="./${item.slug}.html">${item.title}</a></h3>
      <p>${item.description}</p>
      <span class="module-tag">${item.tag}</span>
    </article>`).join("");
}

async function loadContent() {
  try {
    const response = await fetch("../api/ai-plus.json", { cache: "no-store" });
    if (!response.ok) throw new Error("AI+ content unavailable");
    const data = await response.json();
    renderModules(Array.isArray(data.modules) ? data.modules : fallbackModules);
  } catch {
    renderModules(fallbackModules);
  }
}

loadContent();
