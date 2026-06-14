const projectCloud = document.getElementById("projectCloud");
const projectCloudCount = document.getElementById("projectCloudCount");

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => {
    const map = {
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#039;",
    };
    return map[char];
  });
}

function cloudClass(project, index) {
  const title = project.title || "";
  if (project.featured) return "is-featured";
  if (title.length <= 6) return "is-short";
  if (index % 11 === 0) return "is-large";
  if (index % 7 === 0) return "is-medium";
  return "";
}

function renderProjectCloud(projects) {
  if (!projectCloud) return;
  const uniqueProjects = [];
  const seen = new Set();

  projects.forEach((project) => {
    const title = String(project.title || "").trim();
    if (!title || seen.has(title)) return;
    seen.add(title);
    uniqueProjects.push(project);
  });

  if (projectCloudCount) {
    projectCloudCount.textContent = `${uniqueProjects.length} 个项目名称 / FEISHU PROJECT INDEX`;
  }

  const rows = [[], [], []];
  uniqueProjects.forEach((project, index) => {
    rows[index % rows.length].push({ project, index });
  });

  projectCloud.innerHTML = rows
    .map((row, rowIndex) => {
      const doubled = [...row, ...row];
      const items = doubled
        .map(({ project, index }) => {
          const title = project.title || "";
          const href = `./project.html?id=${encodeURIComponent(project.id || index)}`;
          return `<a class="${cloudClass(project, index)}" href="${href}" title="${escapeHtml(title)}">${escapeHtml(title)}</a>`;
        })
        .join("");
      return `<div class="project-cloud-row ${rowIndex % 2 ? "is-reverse" : ""}"><div class="project-cloud-track">${items}</div></div>`;
    })
    .join("");
}

async function loadProjectCloud() {
  if (!projectCloud) return;
  try {
    const response = await fetch("./api/portfolio.json", { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const payload = await response.json();
    renderProjectCloud(Array.isArray(payload.items) ? payload.items : []);
  } catch (error) {
    projectCloud.innerHTML = "<span>项目名称暂时无法读取</span>";
    if (projectCloudCount) projectCloudCount.textContent = "飞书项目库读取失败，请稍后刷新。";
  }
}

loadProjectCloud();
