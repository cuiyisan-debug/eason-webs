(() => {
  const storageKey = "ai-plus:last-section-return";
  const restoreKey = "ai-plus:restore-scroll";

  function restoreScroll() {
    let payload = null;
    try {
      payload = JSON.parse(sessionStorage.getItem(restoreKey) || "null");
    } catch {
      payload = null;
    }
    if (!payload || Date.now() - Number(payload.createdAt || 0) > 120000) return;
    sessionStorage.removeItem(restoreKey);
    requestAnimationFrame(() => {
      window.scrollTo({ top: Math.max(0, Number(payload.y) || 0), behavior: "instant" });
    });
  }

  function rememberReturn(anchor) {
    const href = anchor.getAttribute("href") || "";
    if (!href.includes("article.html")) return;
    const payload = {
      path: window.location.pathname.split("/").pop() || "open-models.html",
      search: window.location.search || "",
      hash: window.location.hash || "",
      scrollY: Math.max(0, Math.round(window.scrollY || document.documentElement.scrollTop || 0)),
      createdAt: Date.now(),
    };
    sessionStorage.setItem(storageKey, JSON.stringify(payload));
  }

  function articleIdFromHref(href) {
    try {
      const url = new URL(href, window.location.href);
      return url.searchParams.get("id") || "";
    } catch {
      return "";
    }
  }

  async function hydrateArticleCardCovers() {
    const cards = Array.from(document.querySelectorAll("a[data-ai-plus-article-link], a[href*='article.html?id=']"));
    if (!cards.length) return;
    try {
      const response = await fetch("../api/ai-plus-articles.json", { cache: "no-store" });
      if (!response.ok) return;
      const data = await response.json();
      const articles = new Map((data.articles || []).map((item) => [item.id || item.key, item]));
      cards.forEach((card) => {
        const id = articleIdFromHref(card.getAttribute("href") || "");
        const article = articles.get(id);
        const cover = article?.cover || "";
        const thumb = card.querySelector(".ai-plus-case-thumb");
        if (cover && thumb) {
          thumb.classList.add("has-cover");
          thumb.style.setProperty("--case-cover", `url("${cover}")`);
        }
        const title = card.querySelector(".ai-plus-case-copy strong");
        if (article?.title && title) title.textContent = article.title;
        const summary = card.querySelector(".ai-plus-case-copy span");
        if (article?.summary && summary) summary.textContent = article.summary;
      });
    } catch {
      // Keep the designed placeholder thumbnail when article JSON is unavailable.
    }
  }

  document.addEventListener("click", (event) => {
    const anchor = event.target.closest("a[data-ai-plus-article-link], a[href*='article.html']");
    if (!anchor) return;
    rememberReturn(anchor);
  });

  restoreScroll();
  hydrateArticleCardCovers();
})();
