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
        : `<img src="${escapeHtml(url)}" alt="" loading="lazy" />`
    )
    .join("");
}

function renderContentBlock(block) {
  if (!block || !block.type) return "";
  if (block.type === "image" && block.url) {
    return `
      <figure class="article-inline-media">
        <img src="${escapeHtml(block.url)}" alt="" loading="lazy" />
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

loadArticle();
