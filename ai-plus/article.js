(() => {
  const params = new URLSearchParams(window.location.search);
  const articleId = params.get("id") || "";
  const returnKey = "ai-plus:last-section-return";

  const escapeHtml = (value = "") =>
    String(value).replace(/[&<>"']/g, (char) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;",
    })[char]);

  const isVideoUrl = (url = "") => /\.(mp4|webm|ogg|mov)(\?|#|$)/i.test(url);
  const isImageUrl = (url = "") => /\.(png|jpe?g|webp|gif|avif|svg)(\?|#|$)/i.test(url);
  const bilibiliBv = (url = "") => {
    const match = String(url).match(/BV[a-zA-Z0-9]+/);
    return match ? match[0] : "";
  };

  function articleUrl(id) {
    const next = new URLSearchParams({ id });
    return `./article.html?${next.toString()}`;
  }

  function renderRichMedia(url, caption = "") {
    if (!url) return "";
    const bv = bilibiliBv(url);
    if (bv) {
      return `<figure class="ai-plus-article-media"><iframe src="https://player.bilibili.com/player.html?bvid=${escapeHtml(bv)}&autoplay=0" allowfullscreen loading="lazy" title="${escapeHtml(caption || bv)}"></iframe>${caption ? `<figcaption>${escapeHtml(caption)}</figcaption>` : ""}</figure>`;
    }
    if (isVideoUrl(url)) {
      return `<figure class="ai-plus-article-media"><video src="${escapeHtml(url)}" controls playsinline preload="metadata"></video>${caption ? `<figcaption>${escapeHtml(caption)}</figcaption>` : ""}</figure>`;
    }
    if (isImageUrl(url)) {
      return `<figure class="ai-plus-article-media"><img src="${escapeHtml(url)}" alt="${escapeHtml(caption)}" loading="lazy" />${caption ? `<figcaption>${escapeHtml(caption)}</figcaption>` : ""}</figure>`;
    }
    return `<p><a href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(caption || url)}</a></p>`;
  }

  function renderBlock(block) {
    const type = block?.type || "";
    const text = block?.text || "";
    if (type === "heading") {
      const level = Math.min(Math.max(Number(block.level) || 2, 2), 4);
      return `<h${level}>${escapeHtml(text)}</h${level}>`;
    }
    if (type === "list_item") {
      return `<li>${escapeHtml(text)}</li>`;
    }
    if (type === "image" || type === "video" || type === "media") {
      return renderRichMedia(block.url || block.link || "", text);
    }
    if (type === "table" && Array.isArray(block.rows)) {
      const rows = block.rows.map((row) => `<tr>${(row || []).map((cell) => `<td>${escapeHtml(cell)}</td>`).join("")}</tr>`).join("");
      return `<div class="ai-plus-article-table-wrap"><table>${rows}</table></div>`;
    }
    return text ? `<p>${escapeHtml(text)}</p>` : "";
  }

  function compactListItems(html) {
    return html.replace(/(<li>.*?<\/li>)(\s*<li>.*?<\/li>)+/gs, (match) => `<ul>${match}</ul>`);
  }

  function renderArticle(article) {
    document.title = `${article.title || "AI++ 文章"}｜格物研习社`;
    document.querySelector("[data-article-title]").textContent = article.title || "AI++ 文章";
    document.querySelector("[data-article-kicker]").textContent = `${article.pageName || "AI++"} / ${article.section || "ARTICLE"}`;
    document.querySelector("[data-article-summary]").textContent = article.summary || article.body || "飞书云文档内容。";
    const body = document.querySelector("[data-article-body]");
    const blocks = Array.isArray(article.contentBlocks) ? article.contentBlocks : [];
    const media = Array.isArray(article.media) ? article.media : [];
    const bodyHtml = blocks.length ? compactListItems(blocks.map(renderBlock).join("")) : `<p>${escapeHtml(article.body || article.summary || "")}</p>`;
    const mediaHtml = media.map((url, index) => renderRichMedia(url, index === 0 ? article.title : "")).join("");
    const sourceHtml = article.contentUrl ? `<p class="ai-plus-article-source"><a href="${escapeHtml(article.contentUrl)}" target="_blank" rel="noopener noreferrer">打开飞书原文 →</a></p>` : "";
    body.innerHTML = mediaHtml + bodyHtml + sourceHtml;
  }

  function bindReturn() {
    document.querySelector("[data-article-return]")?.addEventListener("click", () => {
      let target = null;
      try {
        target = JSON.parse(sessionStorage.getItem(returnKey) || "null");
      } catch {
        target = null;
      }
      if (target?.path) {
        sessionStorage.setItem("ai-plus:restore-scroll", JSON.stringify({ y: target.scrollY || 0, createdAt: Date.now() }));
        window.location.href = `./${target.path}${target.search || ""}${target.hash || ""}`;
      } else {
        window.history.length > 1 ? window.history.back() : (window.location.href = "./open-models.html");
      }
    });
  }

  async function boot() {
    bindReturn();
    try {
      const response = await fetch(`../api/ai-plus-articles.json?v=${Date.now()}`, { cache: "no-store" });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      const article = data.articles?.find((item) => item.id === articleId || item.key === articleId) || data.articles?.[0];
      if (!article) throw new Error("article not found");
      renderArticle(article);
    } catch (error) {
      document.querySelector("[data-article-title]").textContent = "文章暂未同步";
      document.querySelector("[data-article-summary]").textContent = "请先运行 AI++ 飞书文章同步，或检查飞书文档权限。";
      document.querySelector("[data-article-body]").innerHTML = `<p class="ai-plus-article-source"><a href="./open-models.html">返回开源模型页面</a></p>`;
      console.warn("[AI++] article unavailable", error);
    }
  }

  boot();
})();
