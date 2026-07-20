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

const fallbackClients = [
  { name: "CIFTIS", logo: "" },
  { name: "中关村论坛", logo: "" },
  { name: "中国科技馆", logo: "" },
  { name: "安徽自贸区", logo: "" },
  { name: "vivo", logo: "" },
  { name: "ANTA", logo: "" },
  { name: "OPPO", logo: "" },
  { name: "DJI", logo: "" },
  { name: "LYNK&CO", logo: "" },
];

let projects = [];
let clients = [];
let clientLogoFallbacks = {};
let activeCategory = "政企展厅";
let featureIndex = 0;
let expanded = false;
let yearFilter = "全部";
let allCategoryFilter = "全部";
let searchQuery = "";
let activeMediaItems = [];
let activeMediaIndex = 0;
let mediaAutoplay = false;
let lastScrollAt = 0;
let featureRenderToken = 0;
let hashScrollDone = false;

const grid = document.querySelector("[data-project-grid]");
const countLabel = document.querySelector("[data-count]");
const featureCover = document.querySelector("[data-feature-cover]");
const featureCard = document.querySelector(".feature-card");
const featureTitle = document.querySelector("[data-feature-title]");
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
const clientStrip = document.querySelector("[data-client-strip]");
const siteHeader = document.querySelector(".site-header");
const navToggle = document.querySelector(".nav-toggle");
const siteNav = document.querySelector(".nav");

const hasPortfolioGrid = Boolean(grid);

function imageOf(project) {
  return project.cover || project.images?.[0] || FALLBACK_IMAGE;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function extractBilibiliBv(value) {
  const text = String(value || "");
  const match = text.match(/BV[0-9A-Za-z]+/);
  return match ? match[0] : "";
}

function bilibiliEmbedUrl(project, autoplay = false) {
  const bv = extractBilibiliBv(project.videoBv) || extractBilibiliBv(project.videoUrl);
  if (!bv) return "";
  return `https://player.bilibili.com/player.html?bvid=${encodeURIComponent(bv)}&page=1&high_quality=1&autoplay=${autoplay ? 1 : 0}`;
}

function hasVideo(project) {
  return Boolean(bilibiliEmbedUrl(project));
}

function mediaItemsFor(project) {
  const items = [];
  const videoUrl = bilibiliEmbedUrl(project);
  if (videoUrl) items.push({ type: "video", src: videoUrl, label: "VIDEO" });
  const images = project.images?.length ? project.images : [imageOf(project)];
  images.forEach((src, index) => items.push({ type: "image", src, label: String(index + 1) }));
  return items;
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
  const featured = projects.filter((project) => project.featured);
  const source = featured.filter((project) => project.cover).slice(0, 8);
  if (!source.length) {
    featureCard.hidden = true;
    featureCover.style.backgroundImage = "";
    featureTitle.textContent = "";
    return;
  }
  featureCard.hidden = false;
  const currentIndex = ((featureIndex % source.length) + source.length) % source.length;
  const current = source[currentIndex];
  const next = source[(currentIndex + 1) % source.length];
  const nextImage = imageOf(current);
  const renderToken = ++featureRenderToken;
  const image = new Image();
  image.onload = () => {
    if (renderToken === featureRenderToken) {
      featureCover.style.backgroundImage = `url("${nextImage}")`;
    }
  };
  image.onerror = image.onload;
  image.src = nextImage;
  featureTitle.textContent = current.title;
  if (nextTitle) nextTitle.textContent = next?.title || "更多项目";
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
      const href = `./project.html?id=${encodeURIComponent(project.id || projects.indexOf(project))}`;
      return `
        <article class="project-card" data-index="${projects.indexOf(project)}" tabindex="0">
          <div class="project-thumb" style="background-image:url('${imageOf(project)}')"></div>
          <div class="project-body">
            <span class="tag">${project.category || "其他创意"}</span>
            <h3><a href="${href}">${project.title}</a></h3>
            <p>${project.summary || ""}</p>
            <div class="project-meta">${meta.map((item) => `<span>${item}</span>`).join("")}</div>
          </div>
        </article>
      `;
    })
    .join("");
}

function openProject(project) {
  activeMediaItems = mediaItemsFor(project);
  activeMediaIndex = 0;
  mediaAutoplay = false;
  renderGallery();
  dialogCategory.textContent = project.category || "";
  const href = `./project.html?id=${encodeURIComponent(project.id || projects.indexOf(project))}`;
  dialogTitle.innerHTML = `<a href="${href}">${project.title}</a>`;
  dialogSummary.textContent = project.summary || "该项目资料正在补充中。";
  const meta = [project.year, project.role, ...(project.tags || []), hasVideo(project) ? "Bilibili" : ""].filter(Boolean);
  dialogMeta.innerHTML = meta.map((item) => `<span>${item}</span>`).join("");
  dialog.showModal();
}

function renderGallery() {
  const item = activeMediaItems[activeMediaIndex] || { type: "image", src: FALLBACK_IMAGE, label: "1" };
  const mediaSrc = item.type === "video" ? item.src.replace(/autoplay=\d/, `autoplay=${mediaAutoplay ? 1 : 0}`) : item.src;
  dialogMedia.classList.toggle("video-mode", item.type === "video");
  dialogMedia.style.backgroundImage = item.type === "image" ? `url("${mediaSrc}")` : "";
  dialogMedia.innerHTML =
    item.type === "video"
      ? `<iframe src="${mediaSrc}" title="项目视频" loading="lazy" allow="autoplay; fullscreen" allowfullscreen></iframe>`
      : "";
  galleryThumbs.innerHTML = activeMediaItems
    .map(
      (item, index) => `
        <button class="gallery-thumb ${item.type === "video" ? "video-thumb" : ""} ${index === activeMediaIndex ? "active" : ""}" 
          type="button" data-gallery-index="${index}" ${item.type === "image" ? `style="background-image:url('${item.src}')"` : ""}
          aria-label="${item.type === "video" ? "查看项目视频" : `查看第 ${index + 1} 张图`}">${item.type === "video" ? item.label : ""}</button>
      `
    )
    .join("");
}

function changeGallery(delta) {
  if (!activeMediaItems.length) return;
  activeMediaIndex = (activeMediaIndex + delta + activeMediaItems.length) % activeMediaItems.length;
  mediaAutoplay = false;
  renderGallery();
}

function activateVideoAutoplay() {
  const item = activeMediaItems[activeMediaIndex];
  if (!item || item.type !== "video" || mediaAutoplay) return;
  mediaAutoplay = true;
  renderGallery();
}

function populateYearFilter() {
  const years = [...new Set(projects.map((project) => String(project.year || "").trim()).filter(Boolean))].sort((a, b) => Number(b) - Number(a));
  yearSelect.innerHTML = `<option value="全部">全部年份</option>${years.map((year) => `<option value="${year}">${year}</option>`).join("")}`;
}

async function loadData() {
  if (!hasPortfolioGrid) return;
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
  await loadClients();
}

function renderClients() {
  if (!clientStrip) return;
  const source = clients.length ? clients : fallbackClients;
  const repeated = source.length > 1 ? [...source, ...source] : source;
  clientStrip.innerHTML = `
    <div class="client-track">
      ${repeated
        .map((client) => {
          const name = escapeHtml(client.name || "");
          const logoSrc = client.logo || clientLogoFallbacks[client.name];
          const logo = logoSrc ? `<img src="${escapeHtml(logoSrc)}" alt="${name}" loading="lazy" draggable="false" />` : `<strong>${name}</strong>`;
          return `<span class="client-item">${logo}<small>${name}</small></span>`;
        })
        .join("")}
    </div>
  `;
}

async function loadClients() {
  if (!clientStrip) return;
  try {
    const [response, logoResponse] = await Promise.all([
      fetch(`./api/clients.json?ts=${Date.now()}`),
      fetch(`./assets/client-logos/manifest.json?ts=${Date.now()}`).catch(() => null),
    ]);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const payload = await response.json();
    if (logoResponse?.ok) {
      clientLogoFallbacks = await logoResponse.json();
    }
    clients = (payload.items || []).filter((client) => client.name);
  } catch (error) {
    clients = fallbackClients;
  }
  renderClients();
}

function scrollToCurrentHash() {
  if (!window.location.hash) return;
  if (hashScrollDone) return;
  if (lastScrollAt && Date.now() - lastScrollAt < 900) return;
  const target = document.querySelector(window.location.hash);
  if (target) {
    const top = target.getBoundingClientRect().top + window.scrollY;
    window.scrollTo({ top, behavior: "auto" });
    hashScrollDone = true;
  }
}

window.scrollToCurrentHash = scrollToCurrentHash;

function initVisitorStats() {
  if (document.querySelector(".visitor-stats")) return;
  const stats = document.createElement("div");
  stats.className = "visitor-stats";
  stats.setAttribute("aria-label", "浏览统计");
  stats.innerHTML = `
    <span id="busuanzi_container_site_pv">浏览 <strong id="busuanzi_value_site_pv">--</strong> 次</span>
    <span id="busuanzi_container_site_uv">访客 <strong id="busuanzi_value_site_uv">--</strong> 人</span>
  `;
  stats.querySelectorAll("span").forEach((item) => {
    item.style.display = "inline-flex";
  });
  const footer = document.querySelector(".footer-line");
  if (footer) {
    footer.insertBefore(stats, footer.lastElementChild);
  } else {
    document.querySelector("main")?.insertAdjacentElement("beforeend", stats);
  }
  if (!document.querySelector('script[data-visitor-counter="busuanzi"]')) {
    const counterScript = document.createElement("script");
    counterScript.async = true;
    counterScript.defer = true;
    counterScript.dataset.visitorCounter = "busuanzi";
    counterScript.src = "https://busuanzi.ibruce.info/busuanzi/2.3/busuanzi.pure.mini.js";
    document.body.appendChild(counterScript);
  }
  window.setTimeout(sanitizeVisitorStats, 2600);
  window.setTimeout(sanitizeVisitorStats, 5200);
}

function sanitizeVisitorStats() {
  const pv = document.querySelector("#busuanzi_value_site_pv");
  const uv = document.querySelector("#busuanzi_value_site_uv");
  if (!pv || !uv) return;
  const pvValue = Number(String(pv.textContent || "").replace(/\D/g, ""));
  const uvValue = Number(String(uv.textContent || "").replace(/\D/g, ""));
  if (!Number.isFinite(pvValue) || !Number.isFinite(uvValue)) return;
  if (pvValue > 1000000 || uvValue > 1000000 || uvValue > pvValue) {
    const stats = document.querySelector(".visitor-stats");
    if (stats) {
      stats.innerHTML = `<span>\u8bbf\u5ba2\u7edf\u8ba1\u6682\u4e0d\u53ef\u7528</span>`;
    }
  }
}

function protectPortfolioMedia() {
  const protectedSelector = [
    ".feature-image",
    ".project-thumb",
    ".dialog-media",
    ".project-detail-cover",
    ".story-image",
    ".article-image-button",
    ".zhixing-thumb",
    ".related-thumb",
  ].join(",");

  document.addEventListener("contextmenu", (event) => {
    if (event.target.closest(protectedSelector)) {
      event.preventDefault();
    }
  });

  document.addEventListener("dragstart", (event) => {
    if (event.target.closest(protectedSelector) || event.target.matches("img")) {
      event.preventDefault();
    }
  });

  document.querySelectorAll("img").forEach((image) => {
    image.setAttribute("draggable", "false");
  });
}

function initWechatPopovers() {
  const triggers = document.querySelectorAll(".social-wechat");
  if (!triggers.length) return;

  const closeAll = (except) => {
    triggers.forEach((trigger) => {
      if (trigger === except) return;
      trigger.classList.remove("is-open");
      trigger.setAttribute("aria-expanded", "false");
    });
  };

  triggers.forEach((trigger) => {
    trigger.addEventListener("click", (event) => {
      event.stopPropagation();
      const nextOpen = !trigger.classList.contains("is-open");
      closeAll(trigger);
      trigger.classList.toggle("is-open", nextOpen);
      trigger.setAttribute("aria-expanded", String(nextOpen));
    });

    trigger.addEventListener("keydown", (event) => {
      if (event.key !== "Enter" && event.key !== " ") return;
      event.preventDefault();
      const nextOpen = !trigger.classList.contains("is-open");
      closeAll(trigger);
      trigger.classList.toggle("is-open", nextOpen);
      trigger.setAttribute("aria-expanded", String(nextOpen));
    });
  });

  document.addEventListener("click", () => closeAll());
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") closeAll();
  });
}

if (hasPortfolioGrid) {
  const navLinks = document.querySelectorAll(".nav a");
  function setActiveNav(target) {
    navLinks.forEach((link) => link.classList.toggle("active", link === target));
  }
  navLinks.forEach((link) => {
    link.addEventListener("click", () => setActiveNav(link));
  });

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
    if (event.target.closest("a")) return;
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
  dialog.addEventListener("click", (event) => {
    if (event.target === dialog) dialog.close();
  });
  dialog.addEventListener("close", () => {
    dialogMedia.innerHTML = "";
  });
  dialogMedia.addEventListener("mouseenter", activateVideoAutoplay);
  document.querySelector("[data-gallery-prev]").addEventListener("click", () => changeGallery(-1));
  document.querySelector("[data-gallery-next]").addEventListener("click", () => changeGallery(1));
  galleryThumbs.addEventListener("click", (event) => {
    const thumb = event.target.closest("[data-gallery-index]");
    if (!thumb) return;
    activeMediaIndex = Number(thumb.dataset.galleryIndex);
    mediaAutoplay = false;
    renderGallery();
  });
  galleryThumbs.addEventListener("mouseover", (event) => {
    const thumb = event.target.closest("[data-gallery-index]");
    if (!thumb || !thumb.classList.contains("video-thumb")) return;
    const nextIndex = Number(thumb.dataset.galleryIndex);
    if (activeMediaIndex === nextIndex && mediaAutoplay) return;
    activeMediaIndex = nextIndex;
    mediaAutoplay = true;
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
    featureIndex -= 1;
    renderFeature();
  });
  document.querySelector("[data-next]").addEventListener("click", () => {
    featureIndex += 1;
    renderFeature();
  });
  window.setInterval(() => {
    if (!projects.length) return;
    if (document.hidden || Date.now() - lastScrollAt < 1200) return;
    featureIndex += 1;
    renderFeature();
  }, 5200);
}

window.addEventListener(
  "scroll",
  () => {
    lastScrollAt = Date.now();
  },
  { passive: true }
);

function initResponsiveHeader() {
  if (!siteHeader) return;

  const closeNav = () => {
    siteHeader.classList.remove("nav-open");
    navToggle?.setAttribute("aria-expanded", "false");
  };

  navToggle?.addEventListener("click", () => {
    const isOpen = siteHeader.classList.toggle("nav-open");
    navToggle.setAttribute("aria-expanded", String(isOpen));
    if (isOpen) {
      siteHeader.classList.remove("header-hidden");
    }
  });

  siteNav?.querySelectorAll("a").forEach((link) => {
    link.addEventListener("click", closeNav);
  });

  let lastY = window.scrollY;
  let ticking = false;
  window.addEventListener(
    "scroll",
    () => {
      if (ticking) return;
      ticking = true;
      window.requestAnimationFrame(() => {
        const currentY = window.scrollY;
        const delta = currentY - lastY;
        if (siteHeader.classList.contains("nav-open")) {
          siteHeader.classList.remove("header-hidden");
        } else if (delta > 8 && currentY > 120) {
          siteHeader.classList.add("header-hidden");
        } else if (delta < -6 || currentY <= 20) {
          siteHeader.classList.remove("header-hidden");
        }
        lastY = currentY;
        ticking = false;
      });
    },
    { passive: true }
  );
}

function initBrandNavigation() {
  const videoEntry = document.querySelector(".brand-logo-link");
  const homeEntry = document.querySelector(".brand-text");

  videoEntry?.addEventListener("click", (event) => {
    event.preventDefault();
    window.location.assign("./three-portrait-journey.html#top");
  });

  homeEntry?.addEventListener("click", (event) => {
    event.preventDefault();
    window.location.assign("./index.html#top");
  });
}

const themeToggle = document.querySelector(".theme-toggle");
const themeIcon = document.querySelector(".theme-icon");
const brandLogo = document.querySelector(".brand-logo");

function setTheme(theme) {
  const isLight = theme === "light";
  document.documentElement.classList.toggle("light", isLight);
  document.documentElement.dataset.theme = isLight ? "light" : "dark";
  themeToggle.setAttribute("aria-pressed", String(isLight));
  themeToggle.setAttribute("aria-label", isLight ? "Switch to dark mode" : "Switch to light mode");
  themeIcon.textContent = "";
  if (brandLogo) {
    brandLogo.src = isLight ? "./assets/site-logo-light.svg" : "./assets/site-logo-dark.svg";
  }
  localStorage.setItem("portfolio-theme", isLight ? "light" : "dark");
}

themeToggle.addEventListener("click", () => {
  setTheme(document.documentElement.dataset.theme === "light" ? "dark" : "light");
});

setTheme(localStorage.getItem("portfolio-theme") === "light" ? "light" : "dark");

initResponsiveHeader();
initBrandNavigation();
initWechatPopovers();
initVisitorStats();
protectPortfolioMedia();
scrollToCurrentHash();
loadData().finally(() => {
  scrollToCurrentHash();
});
window.addEventListener("hashchange", () => {
  hashScrollDone = false;
  window.setTimeout(scrollToCurrentHash, 0);
});
