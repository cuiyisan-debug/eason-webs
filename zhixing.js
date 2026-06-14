const zhixingGrid = document.querySelector("[data-zhixing-grid]");
const zhixingDetail = document.querySelector("[data-zhixing-detail]");
const zhixingStatus = document.querySelector("[data-zhixing-status]");

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

function renderMedia(urls) {
  if (!urls?.length) return "";
  return `
    <div class="zhixing-media">
      ${urls
        .map((url) =>
          isVideo(url)
            ? `<video src="${escapeHtml(url)}" controls playsinline preload="metadata"></video>`
            : `<img src="${escapeHtml(url)}" alt="" loading="lazy" />`
        )
        .join("")}
    </div>
  `;
}

function renderDetail(article) {
  const body = paragraphs(article.body);
  zhixingDetail.hidden = false;
  zhixingDetail.innerHTML = `
    <div>
      <p class="eyebrow">ZHIXING NOTE</p>
      <h2>${escapeHtml(article.title)}</h2>
      <p class="zhixing-summary">${escapeHtml(article.summary || "")}</p>
      ${article.contentUrl ? `<a class="source-link" href="${escapeHtml(article.contentUrl)}" target="_blank" rel="noreferrer">查看原文链接 →</a>` : ""}
    </div>
    ${renderMedia(article.media)}
    <div class="zhixing-body">
      ${
        body.length
          ? body.map((item) => `<p>${escapeHtml(item)}</p>`).join("")
          : `<p>正文内容正在补充中。</p>`
      }
    </div>
  `;
}

function renderArticles(items) {
  if (!items.length) {
    zhixingGrid.hidden = true;
    zhixingDetail.hidden = true;
    return;
  }
  zhixingStatus.textContent = `已从飞书读取 ${items.length} 篇知行文章。`;
  zhixingGrid.hidden = false;
  zhixingGrid.innerHTML = items
    .map(
      (article, index) => `
        <article class="zhixing-card" data-article-index="${index}" tabindex="0">
          ${article.cover ? `<div class="zhixing-thumb" style="background-image:url('${escapeHtml(article.cover)}')"></div>` : ""}
          <span>${String(index + 1).padStart(2, "0")}</span>
          <h3>${escapeHtml(article.title)}</h3>
          <p>${escapeHtml(article.summary || "")}</p>
        </article>
      `
    )
    .join("");
  renderDetail(items[0]);
  zhixingGrid.addEventListener("click", (event) => {
    const card = event.target.closest("[data-article-index]");
    if (!card) return;
    renderDetail(items[Number(card.dataset.articleIndex)]);
  });
  zhixingGrid.addEventListener("keydown", (event) => {
    if (event.key !== "Enter") return;
    const card = event.target.closest("[data-article-index]");
    if (!card) return;
    renderDetail(items[Number(card.dataset.articleIndex)]);
  });
}

async function loadZhixing() {
  if (!zhixingGrid) return;
  try {
    const response = await fetch(`./api/zhixing.json?ts=${Date.now()}`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const payload = await response.json();
    if (payload.error) {
      zhixingStatus.textContent = `知行表格暂未同步成功：${payload.error}`;
    }
    renderArticles(payload.items || []);
  } catch (error) {
    zhixingStatus.textContent = "知行表格暂未生成，先显示示意内容。";
    renderArticles([]);
  }
}

loadZhixing();
