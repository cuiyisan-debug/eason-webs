const detailRoot = document.querySelector("[data-project-page]");
const detailCover = document.querySelector("[data-detail-cover]");
const detailCategory = document.querySelector("[data-detail-category]");
const detailTitle = document.querySelector("[data-detail-title]");
const detailSummary = document.querySelector("[data-detail-summary]");
const detailFacts = document.querySelector("[data-detail-facts]");
const detailStory = document.querySelector("[data-detail-story]");
const relatedProjects = document.querySelector("[data-related-projects]");

function detailImageOf(project) {
  return project.cover || project.images?.[0] || FALLBACK_IMAGE;
}

function detailBv(project) {
  return extractBilibiliBv(project.videoBv) || extractBilibiliBv(project.videoUrl);
}

function detailVideoUrl(project) {
  const bv = detailBv(project);
  return bv ? `https://player.bilibili.com/player.html?bvid=${encodeURIComponent(bv)}&page=1&high_quality=1&autoplay=0` : "";
}

function factRows(project) {
  return [
    ["项目时间", project.year],
    ["类别", project.category],
    ["角色", project.role],
    ["状态", project.status],
    ["视频", detailBv(project) ? `Bilibili ${detailBv(project)}` : ""],
  ].filter(([, value]) => value);
}

function renderDetail(project, allProjects) {
  document.title = `${project.title} | EASON.CUI`;
  detailCover.style.backgroundImage = `url("${detailImageOf(project)}")`;
  detailCategory.textContent = project.category || "PROJECT";
  detailTitle.textContent = project.title;
  detailSummary.textContent = project.summary || "该项目资料正在补充中。";
  detailFacts.innerHTML = factRows(project)
    .map(([label, value]) => `<div><dt>${label}</dt><dd>${value}</dd></div>`)
    .join("");

  const media = [];
  const videoUrl = detailVideoUrl(project);
  if (videoUrl) media.push(`<figure class="story-video"><iframe src="${videoUrl}" title="${project.title} 视频" allow="autoplay; fullscreen" allowfullscreen></iframe></figure>`);
  (project.images || []).forEach((src, index) => {
    media.push(`<figure class="story-image"><img src="${src}" alt="${project.title} 项目图片 ${index + 1}" loading="lazy" /></figure>`);
  });
  if (!media.length) {
    media.push(`<figure class="story-image"><img src="${detailImageOf(project)}" alt="${project.title}" loading="lazy" /></figure>`);
  }
  detailStory.innerHTML = media.join("");

  const related = allProjects
    .filter((item) => item.id !== project.id && item.category === project.category)
    .slice(0, 6);
  relatedProjects.innerHTML = related
    .map((item) => `<a class="related-card" href="./project.html?id=${encodeURIComponent(item.id)}"><span>${item.category}</span><strong>${item.title}</strong></a>`)
    .join("");
}

async function loadProjectDetail() {
  if (!detailRoot) return;
  const params = new URLSearchParams(window.location.search);
  const id = params.get("id");
  try {
    const response = await fetch(`./api/portfolio.json?ts=${Date.now()}`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const payload = await response.json();
    const items = (payload.items || []).filter((item) => item.title);
    const project = items.find((item) => String(item.id) === String(id)) || items[0];
    if (!project) throw new Error("No project");
    renderDetail(project, items);
  } catch (error) {
    detailTitle.textContent = "项目资料暂未读取成功";
    detailSummary.textContent = "请稍后刷新页面，或返回项目列表继续浏览。";
    detailFacts.innerHTML = "";
    detailStory.innerHTML = "";
  }
}

loadProjectDetail();
