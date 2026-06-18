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

function renderRichText(value) {
  const text = String(value || "");
  const urlPattern = /https?:\/\/[^\s<>"']+/g;
  let html = "";
  let cursor = 0;
  for (const match of text.matchAll(urlPattern)) {
    let url = match[0];
    const start = match.index || 0;
    const trailing = url.match(/[),.，。；;：:!?！？]+$/)?.[0] || "";
    if (trailing) {
      url = url.slice(0, -trailing.length);
    }
    html += escapeHtml(text.slice(cursor, start));
    html += `<a href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(url)}</a>`;
    html += escapeHtml(trailing);
    cursor = start + match[0].length;
  }
  html += escapeHtml(text.slice(cursor));
  return html;
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

function shouldEmbedOriginal(article) {
  const mode = String(article?.displayMode || "").trim();
  return Boolean(article?.contentUrl && (mode.includes("飞书原文") || mode.includes("嵌入")));
}

function isCaptionText(text) {
  const value = String(text || "").trim();
  return /^(图\s*\d+|Figure\s*\d+|封面[:：]|配图[:：])/i.test(value) && value.length <= 90;
}

function inferredHeadingLevel(text) {
  const value = String(text || "").trim();
  if (!value) return 0;
  if (/^(简介|结语|来源|四要素的关系)$/.test(value)) return 2;
  if (/^[一二三四五六七八九十]+[、.．]\s*/.test(value)) return 2;
  if (/^第[一二三四五六七八九十]+[章节部分]/.test(value)) return 2;
  if (/^\d+([.．、])\s*\S+/.test(value) && value.length <= 42) return 3;
  return 0;
}

function isLikelyTableHeader(text) {
  const value = String(text || "").trim();
  return Boolean(value) && value.length <= 16 && !/[。！？!?；;]/.test(value) && !isCaptionText(value) && !inferredHeadingLevel(value);
}

function isLikelyStandaloneHeading(text) {
  const value = String(text || "").trim();
  return Boolean(value) && inferredHeadingLevel(value) > 0 && !isLikelyTableHeader(value);
}

function rawTablesByHeading(body) {
  const lines = paragraphs(body);
  const tables = new Map();
  for (let index = 0; index < lines.length; index += 1) {
    const heading = lines[index];
    if (!inferredHeadingLevel(heading)) continue;
    for (let columns = 6; columns >= 2; columns -= 1) {
      const headers = lines.slice(index + 1, index + 1 + columns);
      if (headers.length !== columns || !headers.every(isLikelyTableHeader)) continue;
      const values = [];
      let cursor = index + 1 + columns;
      while (cursor < lines.length && !isLikelyStandaloneHeading(lines[cursor]) && !isCaptionText(lines[cursor])) {
        values.push(lines[cursor]);
        cursor += 1;
      }
      if (values.length < columns || values.length % columns !== 0) continue;
      const rows = [headers];
      for (let offset = 0; offset < values.length; offset += columns) {
        rows.push(values.slice(offset, offset + columns));
      }
      tables.set(heading, rows);
      break;
    }
  }
  return tables;
}

function headingSlug(text, index) {
  return `section-${index + 1}-${String(text || "")
    .trim()
    .replace(/\s+/g, "-")
    .replace(/[^\w\u4e00-\u9fa5-]/g, "")
    .slice(0, 36)}`;
}

function normalizeArticleBlocks(article) {
  const sourceBlocks = Array.isArray(article.contentBlocks) && article.contentBlocks.length
    ? article.contentBlocks
    : paragraphs(article.body).map((text) => ({ type: "paragraph", text }));
  const hasSourceTables = sourceBlocks.some((block) => block?.type === "table");
  const fallbackTables = hasSourceTables ? new Map() : rawTablesByHeading(article.body);
  const normalizedSourceBlocks = [];
  const existingTableKeys = new Set(
    sourceBlocks
      .filter((block) => block?.type === "table")
      .flatMap((block) => (Array.isArray(block.rows?.[0]) ? [block.rows[0].join("|")] : []))
  );
  sourceBlocks.forEach((block) => {
    normalizedSourceBlocks.push(block);
    const text = String(block?.text || "").trim();
    const rows = fallbackTables.get(text);
    const tableKey = rows?.[0]?.join("|");
    if (rows && tableKey && !existingTableKeys.has(tableKey)) {
      normalizedSourceBlocks.push({ type: "table", rows });
      existingTableKeys.add(tableKey);
    }
  });

  const blocks = [];
  for (let index = 0; index < normalizedSourceBlocks.length; index += 1) {
    const block = normalizedSourceBlocks[index];
    if (!block || !block.type) continue;
    if (block.type === "image") {
      const next = normalizedSourceBlocks[index + 1];
      const caption = next?.type === "paragraph" && isCaptionText(next.text) ? next.text : block.caption || "";
      blocks.push({ ...block, caption });
      if (caption) index += 1;
      continue;
    }
    if (block.type === "paragraph") {
      const text = String(block.text || "").trim();
      if (!text) continue;
      if (isCaptionText(text)) {
        blocks.push({ type: "caption", text });
        continue;
      }
      const level = Number(block.level || block.headingLevel || inferredHeadingLevel(text));
      if (level >= 1 && level <= 6) {
        blocks.push({ type: "heading", level, text });
      } else {
        blocks.push({ ...block, text });
      }
      continue;
    }
    blocks.push(block);
  }
  return groupListBlocks(blocks);
}

function groupListBlocks(blocks) {
  const grouped = [];
  for (let index = 0; index < blocks.length; index += 1) {
    const block = blocks[index];
    if (block?.type !== "list_item") {
      grouped.push(block);
      continue;
    }
    const ordered = block.style === "ordered";
    const items = [];
    while (index < blocks.length && blocks[index]?.type === "list_item" && (blocks[index].style === "ordered") === ordered) {
      items.push(blocks[index].text || "");
      index += 1;
    }
    index -= 1;
    grouped.push({ type: "list", ordered, items });
  }
  return grouped;
}

function renderArticleToc(headings) {
  const toc = document.querySelector("[data-article-toc]");
  if (!toc) return;
  const visibleHeadings = headings.filter((item) => item.level <= 3);
  toc.hidden = visibleHeadings.length < 2;
  toc.innerHTML = visibleHeadings.length
    ? `
      <p>文章框架</p>
      <nav aria-label="文章目录">
        ${visibleHeadings
          .map((item) => `<a class="level-${item.level}" href="#${escapeHtml(item.id)}">${escapeHtml(item.text)}</a>`)
          .join("")}
      </nav>
    `
    : "";
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

function renderContentBlock(block, index) {
  if (!block || !block.type) return "";
  if (block.type === "image" && block.url) {
    return `
      <figure class="article-inline-media">
        <button class="article-image-button" type="button" data-article-image-url="${escapeHtml(block.url)}" aria-label="打开图片浏览">
          <img src="${escapeHtml(block.url)}" alt="" loading="lazy" />
        </button>
        ${block.caption ? `<figcaption>${escapeHtml(block.caption)}</figcaption>` : ""}
      </figure>
    `;
  }
  if (block.type === "caption" && block.text) {
    return `<p class="article-caption">${renderRichText(block.text)}</p>`;
  }
  if (block.type === "heading" && block.text) {
    const level = Math.min(Math.max(Number(block.level || 2), 2), 4);
    const id = block.id || headingSlug(block.text, index);
    return `<h${level} id="${escapeHtml(id)}">${escapeHtml(block.text)}</h${level}>`;
  }
  if (block.type === "table" && Array.isArray(block.rows) && block.rows.length) {
    const [headRow, ...bodyRows] = block.rows;
    return `
      <div class="article-table-wrap">
        <table class="article-table">
          <thead>
            <tr>
              ${(headRow || []).map((cell) => `<th scope="col">${renderRichText(cell)}</th>`).join("")}
            </tr>
          </thead>
          <tbody>
            ${bodyRows
              .map(
                (row) => `
                <tr>
                  ${(row || []).map((cell) => `<td>${renderRichText(cell)}</td>`).join("")}
                </tr>
              `
              )
              .join("")}
          </tbody>
        </table>
      </div>
    `;
  }
  if (block.type === "list" && Array.isArray(block.items) && block.items.length) {
    const tag = block.ordered ? "ol" : "ul";
    return `
      <${tag} class="article-list">
        ${block.items.map((item) => `<li>${renderRichText(item)}</li>`).join("")}
      </${tag}>
    `;
  }
  if (block.type === "paragraph" && block.text) {
    return `<p>${renderRichText(block.text)}</p>`;
  }
  return "";
}

function renderBody(article) {
  const container = document.querySelector("[data-article-body]");
  if (!container) return;
  if (shouldEmbedOriginal(article)) {
    renderArticleToc([]);
    container.innerHTML = `
      <div class="article-source-embed">
        <iframe src="${escapeHtml(article.contentUrl)}" title="${escapeHtml(article.title || "飞书原文")}" loading="lazy"></iframe>
        <p>如果飞书限制嵌入显示，可以点击上方“查看原文链接”打开原文。</p>
      </div>
    `;
    return;
  }
  const blocks = normalizeArticleBlocks(article).map((block, index) => {
    if (block.type !== "heading") return block;
    return { ...block, id: headingSlug(block.text, index) };
  });
  const headings = blocks.filter((block) => block.type === "heading");
  renderArticleToc(headings);
  container.innerHTML = blocks.length
    ? blocks.map(renderContentBlock).join("")
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
