const params = new URLSearchParams(window.location.search);
const source = params.get("source") || "zhixing";
const articleId = params.get("id") || "";

const sourceLabels = {
  zhixing: "ZHIXING NOTE",
  curation: "CURATION NOTE",
};

const sourceNames = {
  zhixing: "知行",
  curation: "策展",
};

let articleImages = [];
let activeArticleImageIndex = 0;

function escapeHtml(value) {
  return String(value || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function paragraphs(text) {
  return String(text || "")
    .split(/\n{1,}/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function isVideo(url) {
  return /\.(mp4|webm|ogg|mov)(\?|$)/i.test(String(url || ""));
}

function articleUrl(item) {
  const next = new URLSearchParams({
    source,
    id: item.id || "",
  });
  return `./article.html?${next.toString()}`;
}

function renderMedia(urls) {
  const container = document.querySelector("[data-article-media]");
  if (!container) return;
  if (!urls?.length) {
    container.hidden = true;
    return;
  }
  container.hidden = false;
  container.innerHTML = urls
    .map((url) =>
      isVideo(url)
        ? `<video src="${escapeHtml(url)}" controls playsinline preload="metadata"></video>`
        : `
          <button class="article-image-button" type="button" data-article-image-url="${escapeHtml(url)}" aria-label="打开图片浏览">
            <img src="${escapeHtml(url)}" alt="" loading="lazy" />
          </button>
        `
    )
    .join("");
}

function renderContentBlock(block) {
  if (!block || !block.type) return "";
  if (block.type === "image" && block.url) {
    return `
      <figure class="article-inline-media">
        <button class="article-image-button" type="button" data-article-image-url="${escapeHtml(block.url)}" aria-label="打开图片浏览">
          <img src="${escapeHtml(block.url)}" alt="" loading="lazy" />
        </button>
      </figure>
    `;
  }
  if (block.type === "table" && Array.isArray(block.rows) && block.rows.length) {
    return `
      <div class="article-table-wrap">
        <table class="article-table">
          <tbody>
            ${block.rows
              .map(
                (row) => `
                  <tr>
                    ${(row || []).map((cell) => `<td>${escapeHtml(cell)}</td>`).join("")}
                  </tr>
                `
              )
              .join("")}
          </tbody>
        </table>
      </div>
    `;
  }
  if (block.type === "paragraph" && block.text) {
    return `<p>${escapeHtml(block.text)}</p>`;
  }
  return "";
}

function renderBody(article) {
  const container = document.querySelector("[data-article-body]");
  if (!container) return;
  if (Array.isArray(article.contentBlocks) && article.contentBlocks.length) {
    container.innerHTML = article.contentBlocks.map(renderContentBlock).join("");
    return;
  }
  const body = paragraphs(article.body);
  container.innerHTML = body.length
    ? body.map((item) => `<p>${escapeHtml(item)}</p>`).join("")
    : `<p>正文内容正在同步解析中，可点击原文链接查看。</p>`;
}

function collectArticleImages(article) {
  const fromBlocks = Array.isArray(article.contentBlocks)
    ? article.contentBlocks.filter((block) => block.type === "image" && block.url).map((block) => block.url)
    : [];
  const fromMedia = Array.isArray(article.media) ? article.media.filter((url) => !isVideo(url)) : [];
  return [...new Set([...fromBlocks, ...fromMedia])];
}

function renderArticleImageLightbox() {
  const stage = document.querySelector("[data-article-image-stage]");
  const thumbs = document.querySelector("[data-article-image-thumbs]");
  if (!stage || !thumbs || !articleImages.length) return;
  const activeUrl = articleImages[activeArticleImageIndex] || articleImages[0];
  stage.style.backgroundImage = `url("${activeUrl}")`;
  thumbs.innerHTML = articleImages
    .map(
      (url, index) => `
        <button class="gallery-thumb ${index === activeArticleImageIndex ? "active" : ""}" 
          type="button" data-article-thumb-index="${index}" style="background-image:url('${escapeHtml(url)}')"
          aria-label="查看第 ${index + 1} 张图片"></button>
      `
    )
    .join("");
}

function openArticleImageLightbox(url) {
  const dialog = document.querySelector("[data-article-image-dialog]");
  if (!dialog || !articleImages.length) return;
  const index = articleImages.indexOf(url);
  activeArticleImageIndex = index >= 0 ? index : 0;
  renderArticleImageLightbox();
  dialog.showModal();
}

function changeArticleImage(delta) {
  if (!articleImages.length) return;
  activeArticleImageIndex = (activeArticleImageIndex + delta + articleImages.length) % articleImages.length;
  renderArticleImageLightbox();
}

function bindArticleImageLightbox() {
  const dialog = document.querySelector("[data-article-image-dialog]");
  if (!dialog) return;
  document.querySelector("[data-article-image-close]")?.addEventListener("click", () => dialog.close());
  document.querySelector("[data-article-image-prev]")?.addEventListener("click", () => changeArticleImage(-1));
  document.querySelector("[data-article-image-next]")?.addEventListener("click", () => changeArticleImage(1));
  document.querySelector("[data-article-image-thumbs]")?.addEventListener("click", (event) => {
    const thumb = event.target.closest("[data-article-thumb-index]");
    if (!thumb) return;
    activeArticleImageIndex = Number(thumb.dataset.articleThumbIndex);
    renderArticleImageLightbox();
  });
  dialog.addEventListener("click", (event) => {
    if (event.target === dialog) dialog.close();
  });
  document.addEventListener("keydown", (event) => {
    if (!dialog.open) return;
    if (event.key === "ArrowLeft") changeArticleImage(-1);
    if (event.key === "ArrowRight") changeArticleImage(1);
  });
}

function bindArticleInlineImages() {
  document.addEventListener("click", (event) => {
    const button = event.target.closest("[data-article-image-url]");
    if (!button) return;
    openArticleImageLightbox(button.dataset.articleImageUrl);
  });
}

function renderRelated(current, items) {
  const container = document.querySelector("[data-related-articles]");
  if (!container) return;
  const related = items.filter((item) => item.id !== current.id).slice(0, 3);
  container.innerHTML = related
    .map(
      (item) => `
        <a class="related-card article-related-card ${item.cover ? "has-thumb" : "no-thumb"}" href="${escapeHtml(articleUrl(item))}">
          ${item.cover ? `<span class="related-thumb" style="background-image:url('${escapeHtml(item.cover)}')"></span>` : ""}
          <span class="related-category">${escapeHtml(sourceNames[source] || "文章")}</span>
          <strong>${escapeHtml(item.title)}</strong>
        </a>
      `
    )
    .join("");
}

function renderArticle(article, items) {
  document.title = `${article.title} | EASON.CUI`;
  document.querySelector("[data-article-label]").textContent = sourceLabels[source] || "ARTICLE";
  document.querySelector("[data-article-title]").textContent = article.title;
  document.querySelector("[data-article-summary]").textContent = article.summary || "";

  const sourceLink = document.querySelector("[data-article-source-link]");
  if (sourceLink && article.contentUrl) {
    sourceLink.hidden = false;
    sourceLink.href = article.contentUrl;
  }

  const currentNav = document.querySelector(`[data-nav-${source}]`);
  if (currentNav) currentNav.setAttribute("aria-current", "page");

  renderMedia(article.contentBlocks?.length ? [] : article.media || []);
  renderBody(article);
  articleImages = collectArticleImages(article);
  activeArticleImageIndex = 0;
  renderRelated(article, items);
}

async function loadArticle() {
  try {
    const response = await fetch(`./api/${source}.json?ts=${Date.now()}`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const payload = await response.json();
    const items = payload.items || [];
    const article = items.find((item) => item.id === articleId) || items[0];
    if (!article) throw new Error("No article data");
    renderArticle(article, items);
  } catch (error) {
    document.querySelector("[data-article-title]").textContent = "文章暂未同步";
    document.querySelector("[data-article-summary]").textContent = "请稍后刷新，或检查飞书表格权限与字段。";
    renderBody({ body: "" });
  }
}

bindArticleImageLightbox();
bindArticleInlineImages();
loadArticle();
