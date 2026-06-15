const projectCloud = document.getElementById("projectCloud");
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

function stableHash(value) {
  return String(value || "").split("").reduce((hash, char) => ((hash << 5) - hash + char.charCodeAt(0)) | 0, 0);
}

function cloudClass(project, index) {
  const title = project.title || "";
  const hash = Math.abs(stableHash(`${project.id || index}-${title}`));
  const classes = [];
  if (hash % 10 === 0) classes.push("is-featured");
  if (title.length <= 6) classes.push("is-short");
  if (hash % 17 === 0) classes.push("is-large");
  if (hash % 13 === 0) classes.push("is-medium");
  return classes.join(" ");
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
  }
}

loadProjectCloud();
