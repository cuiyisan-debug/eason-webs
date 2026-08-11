const aiSections = [
  ["overview", "AI 概述"],
  ["office", "日常增效"],
  ["open-models", "开源模型"],
  ["agents", "Agent 智能体"],
  ["toolbox", "AI 工具箱"],
];

function renderAiShell() {
  const host = document.querySelector("[data-ai-shell]");
  if (!host) return;
  const current = document.body.dataset.section || "";
  host.innerHTML = `
    <button class="ai-nav-toggle" type="button" aria-label="打开 AI+ 导航" aria-expanded="false" aria-controls="ai-site-nav"><span></span><span></span><span></span></button>
    <div class="ai-brand">
      <a class="ai-brand-logo" href="./index.html#top" aria-label="返回 AI+ 片头"><img src="../assets/site-logo-dark.svg" alt="格物研习社" /></a>
      <a class="ai-brand-text" href="./home.html#top" aria-label="返回 AI++ 首页"><strong>AI++</strong></a>
    </div>
    <nav class="ai-site-nav" id="ai-site-nav" aria-label="AI+ 二级页面导航">
      ${aiSections.map(([slug, title]) => `<a href="./${slug}.html"${slug === current ? ' aria-current="page"' : ""}>${title}</a>`).join("")}
    </nav>`;

  const toggle = host.querySelector(".ai-nav-toggle");
  const nav = host.querySelector(".ai-site-nav");
  toggle?.addEventListener("click", () => {
    const open = host.classList.toggle("ai-nav-open");
    toggle.setAttribute("aria-expanded", String(open));
  });
  nav?.addEventListener("click", () => {
    host.classList.remove("ai-nav-open");
    toggle?.setAttribute("aria-expanded", "false");
  });

  const scrollHost = document.querySelector(".intro-sequence");
  const scrollTarget = scrollHost || window;
  const readScrollY = () => scrollHost ? scrollHost.scrollTop : window.scrollY;
  let lastY = readScrollY();
  let ticking = false;
  scrollTarget.addEventListener("scroll", () => {
    if (ticking) return;
    ticking = true;
    window.requestAnimationFrame(() => {
      const currentY = readScrollY();
      const delta = currentY - lastY;
      if (host.classList.contains("ai-nav-open") || currentY < 12 || delta < -6) {
        host.classList.remove("ai-header-hidden");
      } else if (currentY > host.offsetHeight + 28 && delta > 6) {
        host.classList.add("ai-header-hidden");
      }
      lastY = currentY;
      ticking = false;
    });
  }, { passive: true });
}

renderAiShell();
