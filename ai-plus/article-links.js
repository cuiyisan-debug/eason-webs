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

  document.addEventListener("click", (event) => {
    const anchor = event.target.closest("a[data-ai-plus-article-link], a[href*='article.html']");
    if (!anchor) return;
    rememberReturn(anchor);
  });

  restoreScroll();
})();
