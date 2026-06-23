const articleRoot = document.querySelector("[data-article-source]");
const articleGrid = document.querySelector("[data-article-grid]");
const articleStatus = document.querySelector("[data-article-status]");

const articleLabels = {
  zhixing: "ZHIXING NOTE",
  curation: "CURATION NOTE",
};

const articleSourceNames = {
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

function articleUrl(source, article) {
  const params = new URLSearchParams({
    source,
    id: article.id || "",
  });
  return `./article.html?${params.toString()}`;
}

function restartAnimatedImage(image) {
  if (!image?.dataset?.gifSource) return;
  const marker = `gif-replay-${Date.now()}-${Math.floor(Math.random() * 1000)}`;
  image.src = `${image.dataset.gifSource}#${marker}`;
}

function setupArticleThumbMotion(root = document) {
  root.querySelectorAll(".article-thumb img").forEach((image) => {
    if (image.dataset.motionReady) return;
    image.dataset.motionReady = "true";
    image.dataset.gifSource = image.currentSrc || image.src;

    window.setTimeout(() => restartAnimatedImage(image), 4200);

    const card = image.closest(".article-card");
    let hoverTimer = 0;
    card?.addEventListener("mouseenter", () => {
      restartAnimatedImage(image);
      hoverTimer = window.setInterval(() => restartAnimatedImage(image), 4200);
    });
    card?.addEventListener("mouseleave", () => {
      window.clearInterval(hoverTimer);
    });
  });
}

function renderArticleCards(source, items) {
  if (!articleGrid) return;
  if (!items.length) {
    articleGrid.hidden = true;
    return;
  }

  articleGrid.hidden = false;
  articleGrid.innerHTML = items
    .map((article) => {
      const href = articleUrl(source, article);
      return `
        <article class="zhixing-card article-card" data-article-href="${escapeHtml(href)}" tabindex="0">
          ${
            article.cover
              ? `
                <a class="zhixing-thumb article-thumb" href="${escapeHtml(href)}" aria-label="${escapeHtml(article.title)}">
                  <img src="${escapeHtml(article.cover)}" alt="" loading="lazy" draggable="false" />
                </a>
              `
              : ""
          }
          <h3><a href="${escapeHtml(href)}" title="${escapeHtml(article.title)}">${escapeHtml(article.title)}</a></h3>
        </article>
      `;
    })
    .join("");
  setupArticleThumbMotion(articleGrid);

  articleGrid.addEventListener("click", (event) => {
    if (event.target.closest("a")) return;
    const card = event.target.closest("[data-article-href]");
    if (card?.dataset.articleHref) {
      window.location.href = card.dataset.articleHref;
    }
  });

  articleGrid.addEventListener("keydown", (event) => {
    if (event.key !== "Enter") return;
    const card = event.target.closest("[data-article-href]");
    if (card?.dataset.articleHref) {
      window.location.href = card.dataset.articleHref;
    }
  });
}

async function loadArticleList() {
  if (!articleRoot || !articleGrid) return;
  const source = articleRoot.dataset.articleSource || "zhixing";
  const sourceName = articleSourceNames[source] || source;
  try {
    const response = await fetch(`./api/${source}.json?ts=${Date.now()}`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const payload = await response.json();
    const items = payload.items || [];
    if (payload.error && articleStatus) {
      articleStatus.textContent = `${sourceName}表格暂未同步成功：${payload.error}`;
    } else if (articleStatus) {
      articleStatus.textContent = `当前收录 ${items.length} 篇${sourceName}文章。`;
    }
    renderArticleCards(source, items);
  } catch (error) {
    if (articleStatus) {
      articleStatus.textContent = `${sourceName}文章暂时无法读取。`;
    }
    renderArticleCards(source, []);
  }
}

loadArticleList();
