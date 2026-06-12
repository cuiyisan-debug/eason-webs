const FALLBACK_IMAGE =
  "https://images.unsplash.com/photo-1518005020951-eccb494ad742?auto=format&fit=crop&w=1400&q=80";

const fallbackProjects = [
  {
    title: "中国声谷展示中心",
    category: "政企展厅",
    summary: "打造国家级产业基地，展现语音和人工智能领域的创新成果。",
    year: "2021",
    tags: ["人工智能", "产业展示"],
    cover: FALLBACK_IMAGE,
    images: [FALLBACK_IMAGE],
  },
  {
    title: "京东方技术创新中心",
    category: "品牌空间",
    summary: "屏联万物，致敬每一次创新，让科技更有温度。",
    year: "2023",
    tags: ["科技品牌", "体验中心"],
    cover: "https://images.unsplash.com/photo-1497366754035-f200968a6e72?auto=format&fit=crop&w=1400&q=80",
    images: ["https://images.unsplash.com/photo-1497366754035-f200968a6e72?auto=format&fit=crop&w=1400&q=80"],
  },
  {
    title: "中国-中东欧国家合作成果展",
    category: "临展活动",
    summary: "搭建跨区域合作平台，绘制中欧关系发展的新篇章。",
    year: "2026",
    tags: ["成果展", "国际合作"],
    cover: "https://images.unsplash.com/photo-1505373877841-8d25f7d46678?auto=format&fit=crop&w=1400&q=80",
    images: ["https://images.unsplash.com/photo-1505373877841-8d25f7d46678?auto=format&fit=crop&w=1400&q=80"],
  },
];

let projects = [];
let activeCategory = "全部";
let featureIndex = 0;
let expanded = false;
let yearFilter = "全部";
let allCategoryFilter = "全部";
let searchQuery = "";
let activeGalleryImages = [];
let activeGalleryIndex = 0;

const grid = document.querySelector("[data-project-grid]");
const countLabel = document.querySelector("[data-count]");
const featureCover = document.querySelector("[data-feature-cover]");
const featureTitle = document.querySelector("[data-feature-title]");
const featureSummary = document.querySelector("[data-feature-summary]");
const nextTitle = document.querySelector("[data-next-title]");
const dialog = document.querySelector("[data-dialog]");
const dialogMedia = document.querySelector("[data-dialog-media]");
const dialogTitle = document.querySelector("[data-dialog-title]");
const dialogSummary = document.querySelector("[data-dialog-summary]");
const dialogCategory = document.querySelector("[data-dialog-category]");
const dialogMeta = document.querySelector("[data-dialog-meta]");
const yearSelect = document.querySelector("[data-year-filter]");
const allCategorySelect = document.querySelector("[data-category-filter]");
const searchInput = document.querySelector("[data-search-filter]");
const allFilters = document.querySelector("[data-all-filters]");
const loadMore = document.querySelector("[data-load-more]");
const galleryThumbs = document.querySelector("[data-gallery-thumbs]");

function imageOf(project) {
  return project.cover || project.images?.[0] || FALLBACK_IMAGE;
}

function filteredProjects() {
  let list = activeCategory === "全部" ? projects : projects.filter((project) => project.category === activeCategory);
  if (activeCategory === "全部") {
    if (yearFilter !== "全部") list = list.filter((project) => String(project.year || "") === yearFilter);
    if (allCategoryFilter !== "全部") list = list.filter((project) => project.category === allCategoryFilter);
    const keyword = searchQuery.trim().toLowerCase();
    if (keyword) {
      list = list.filter((project) => {
        const searchable = [
          project.title,
          project.category,
          project.summary,
          project.year,
          project.role,
          project.status,
          ...(project.tags || []),
        ]
          .filter(Boolean)
          .join(" ")
          .toLowerCase();
        return searchable.includes(keyword);
      });
    }
  }
  return [...list].sort((a, b) => Number(Boolean(b.cover)) - Number(Boolean(a.cover)) || (a.order || 0) - (b.order || 0));
}

function renderFeature() {
  const withImages = projects.filter((project) => project.cover).slice(0, 8);
  const featured = projects.filter((project) => project.featured).slice(0, 8);
  const source = withImages.length ? withImages : featured.length ? featured : projects;
  if (!source.length) return;
  const current = source[featureIndex % source.length];
  const next = source[(featureIndex + 1) % source.length];
  featureCover.style.backgroundImage = `url("${imageOf(current)}")`;
  featureTitle.textContent = current.title;
  featureSummary.textContent = current.summary || current.category;
  nextTitle.textContent = next?.title || "更多项目";
}

function renderProjects() {
  const list = filteredProjects();
  const visible = expanded ? list : list.slice(0, 12);
  const searchText = activeCategory === "全部" && searchQuery.trim() ? ` · 搜索“${searchQuery.trim()}”` : "";
  const visibleText = !expanded && list.length > 12 ? " · 显示 12 个" : "";
  countLabel.textContent = `${activeCategory} · ${list.length} 个项目${searchText}${visibleText}`;
  allFilters.hidden = activeCategory !== "全部";
  loadMore.hidden = list.length <= 12;
  loadMore.textContent = expanded ? "收起项目" : `查看更多 ${list.length - 12} 个`;
  if (!list.length) {
    grid.innerHTML = `<div class="empty">没有找到匹配的项目</div>`;
    return;
  }
  grid.innerHTML = visible
    .map((project, index) => {
      const meta = [project.year, ...(project.tags || []).slice(0, 2)].filter(Boolean);
      return `
        <article class="project-card" data-index="${projects.indexOf(project)}" tabindex="0">
          <div class="project-thumb" style="background-image:url('${imageOf(project)}')"></div>
          <div class="project-body">
            <span class="tag">${project.category || "其他创意"}</span>
            <h3>${project.title}</h3>
            <p>${project.summary || ""}</p>
            <div class="project-meta">${meta.map((item) => `<span>${item}</span>`).join("")}</div>
          </div>
        </article>
      `;
    })
    .join("");
}

function openProject(project) {
  activeGalleryImages = project.images?.length ? project.images : [imageOf(project)];
  activeGalleryIndex = 0;
  renderGallery();
  dialogCategory.textContent = project.category || "";
  dialogTitle.textContent = project.title;
  dialogSummary.textContent = project.summary || "该项目资料正在补充中。";
  const meta = [project.year, project.role, ...(project.tags || []), project.videoBv ? `BV: ${project.videoBv}` : ""].filter(Boolean);
  dialogMeta.innerHTML = meta.map((item) => `<span>${item}</span>`).join("");
  dialog.showModal();
}

function renderGallery() {
  const image = activeGalleryImages[activeGalleryIndex] || FALLBACK_IMAGE;
  dialogMedia.style.backgroundImage = `url("${image}")`;
  galleryThumbs.innerHTML = activeGalleryImages
    .map(
      (item, index) => `
        <button class="gallery-thumb ${index === activeGalleryIndex ? "active" : ""}" 
          type="button" data-gallery-index="${index}" style="background-image:url('${item}')" 
          aria-label="查看第 ${index + 1} 张图"></button>
      `
    )
    .join("");
}

function changeGallery(delta) {
  if (!activeGalleryImages.length) return;
  activeGalleryIndex = (activeGalleryIndex + delta + activeGalleryImages.length) % activeGalleryImages.length;
  renderGallery();
}

function populateYearFilter() {
  const years = [...new Set(projects.map((project) => String(project.year || "").trim()).filter(Boolean))].sort((a, b) => Number(b) - Number(a));
  yearSelect.innerHTML = `<option value="全部">全部年份</option>${years.map((year) => `<option value="${year}">${year}</option>`).join("")}`;
}

async function loadData() {
  try {
    const response = await fetch(`./api/portfolio.json?ts=${Date.now()}`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const payload = await response.json();
    projects = (payload.items || []).filter((project) => project.title);
  } catch (error) {
    projects = fallbackProjects;
  }
  if (!projects.length) projects = fallbackProjects;
  populateYearFilter();
  renderFeature();
  renderProjects();
}

document.querySelectorAll("[data-category]").forEach((button) => {
  button.addEventListener("click", () => {
    document.querySelectorAll("[data-category]").forEach((item) => item.classList.remove("active"));
    button.classList.add("active");
    activeCategory = button.dataset.category;
    expanded = false;
    if (activeCategory !== "全部") {
      yearFilter = "全部";
      allCategoryFilter = "全部";
      searchQuery = "";
      yearSelect.value = "全部";
      allCategorySelect.value = "全部";
      searchInput.value = "";
    }
    renderProjects();
  });
});

grid.addEventListener("click", (event) => {
  const card = event.target.closest(".project-card");
  if (!card) return;
  openProject(projects[Number(card.dataset.index)]);
});

grid.addEventListener("keydown", (event) => {
  if (event.key !== "Enter") return;
  const card = event.target.closest(".project-card");
  if (!card) return;
  openProject(projects[Number(card.dataset.index)]);
});

document.querySelector("[data-close]").addEventListener("click", () => dialog.close());
document.querySelector("[data-gallery-prev]").addEventListener("click", () => changeGallery(-1));
document.querySelector("[data-gallery-next]").addEventListener("click", () => changeGallery(1));
galleryThumbs.addEventListener("click", (event) => {
  const thumb = event.target.closest("[data-gallery-index]");
  if (!thumb) return;
  activeGalleryIndex = Number(thumb.dataset.galleryIndex);
  renderGallery();
});
loadMore.addEventListener("click", () => {
  expanded = !expanded;
  renderProjects();
});
yearSelect.addEventListener("change", () => {
  yearFilter = yearSelect.value;
  expanded = false;
  renderProjects();
});
allCategorySelect.addEventListener("change", () => {
  allCategoryFilter = allCategorySelect.value;
  expanded = false;
  renderProjects();
});
searchInput.addEventListener("input", () => {
  searchQuery = searchInput.value;
  expanded = false;
  renderProjects();
});
document.querySelector("[data-prev]").addEventListener("click", () => {
  featureIndex = Math.max(0, featureIndex - 1);
  renderFeature();
});
document.querySelector("[data-next]").addEventListener("click", () => {
  featureIndex += 1;
  renderFeature();
});

document.querySelector(".theme-toggle").addEventListener("click", () => {
  document.documentElement.classList.toggle("light");
  localStorage.setItem("portfolio-theme", document.documentElement.classList.contains("light") ? "light" : "dark");
});

if (localStorage.getItem("portfolio-theme") === "light") {
  document.documentElement.classList.add("light");
}

loadData();
