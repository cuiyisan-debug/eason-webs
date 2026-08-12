(() => {
  const params = new URLSearchParams(window.location.search);
  if (!params.has("feishu")) return;

  const pageKey = document.body?.dataset?.section;
  const root = document.querySelector("[data-ai-plus-content]");
  if (!pageKey || !root) return;

  const escapeHtml = (value = "") =>
    String(value).replace(/[&<>"']/g, (char) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;",
    })[char]);

  const groupBy = (records) => records.reduce((map, record) => {
    const key = record.section || "其他";
    if (!map.has(key)) map.set(key, []);
    map.get(key).push(record);
    return map;
  }, new Map());

  const sectionId = (section = "") => {
    const map = {
      "发展迭代": "evolution",
      "常见开源大模型": "models",
      "无限画布": "canvas",
      "应用实例": "cases",
    };
    return map[section] || "";
  };

  function renderHero(records) {
    const hero = records.find((item) => item.moduleType === "hero") || records[0];
    const captions = records.filter((item) => item.moduleType === "caption").slice(0, 3);
    if (!hero) return "";
    return `
      <section class="ai-plus-module-hero" id="top">
        <div class="ai-plus-module-copy">
          ${hero.tag ? `<p class="ai-plus-module-kicker">${escapeHtml(hero.tag)}</p>` : ""}
          <h1>${escapeHtml(hero.title)}</h1>
          ${hero.body ? `<p>${escapeHtml(hero.body)}</p>` : ""}
        </div>
        <div class="ai-plus-module-lab ai-plus-module-lab--${escapeHtml(pageKey)}" aria-label="${escapeHtml(hero.pageName)}示意">
          ${captions.length ? `<div class="ai-plus-module-caption">${captions.map((item) => `<span>${escapeHtml(item.title || item.body)}</span>`).join("")}</div>` : ""}
        </div>
      </section>`;
  }

  function renderSection(section, records) {
    const intro = records.find((item) => item.moduleType === "section");
    const items = records.filter((item) => item.moduleType !== "section" && item.moduleType !== "hero" && item.moduleType !== "caption");
    if (!intro && !items.length) return "";
    const isCaseSection = items.some((item) => item.moduleType === "case");
    const cards = items.map(isCaseSection ? renderCaseCard : renderCard).join("");
    const id = sectionId(section);
    return `
      <section class="ai-plus-module-section"${id ? ` id="${escapeHtml(id)}"` : ""}>
        ${intro ? `<div class="ai-plus-module-head"><h2>${escapeHtml(intro.title)}</h2>${intro.body ? `<p>${escapeHtml(intro.body)}</p>` : ""}</div>` : `<div class="ai-plus-module-head"><h2>${escapeHtml(section)}</h2></div>`}
        ${cards ? `<div class="${isCaseSection ? "ai-plus-case-grid" : "ai-plus-module-tools ai-plus-resource-grid"}">${cards}</div>` : ""}
      </section>`;
  }

  function renderCaseCard(item) {
    const href = item.linkUrl || "#";
    return `
      <a class="ai-plus-case-card" href="${escapeHtml(href)}" target="_blank" rel="noopener noreferrer">
        <span class="ai-plus-case-thumb" aria-hidden="true">
          <span class="case-node node-1"></span>
          <span class="case-node node-2"></span>
          <span class="case-node node-3"></span>
          <span class="case-frame frame-1"></span>
          <span class="case-frame frame-2"></span>
        </span>
        <span class="ai-plus-case-copy">
          ${item.tag ? `<small>${escapeHtml(item.tag)}</small>` : ""}
          <strong>${escapeHtml(item.title)}</strong>
          ${item.body ? `<span>${escapeHtml(item.body)}</span>` : ""}
        </span>
      </a>`;
  }

  function renderCard(item) {
    const link = item.linkUrl ? `
      <div class="ai-plus-resource-links compact">
        <a href="${escapeHtml(item.linkUrl)}" target="_blank" rel="noopener noreferrer">
          <strong>${escapeHtml(item.linkTitle || item.title)}</strong>
          <small>${escapeHtml(item.linkUrl)}</small>
        </a>
      </div>` : "";
    return `
      <article data-kind="${escapeHtml(item.moduleType)}">
        <h3>${escapeHtml(item.title)}${item.tag ? ` <span>${escapeHtml(item.tag)}</span>` : ""}</h3>
        ${item.body ? `<p>${escapeHtml(item.body)}</p>` : ""}
        ${item.note ? `<small class="ai-plus-record-note">${escapeHtml(item.note)}</small>` : ""}
        ${link}
      </article>`;
  }

  async function boot() {
    try {
      const response = await fetch(`../api/ai-plus-content.json?v=${Date.now()}`, { cache: "no-store" });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      const page = data.pages?.[pageKey];
      if (!page?.records?.length) return;
      const records = page.records;
      const heroHtml = renderHero(records);
      const sections = Array.from(groupBy(records.filter((item) => !["hero", "caption"].includes(item.moduleType))).entries());
      const sectionHtml = sections.map(([section, items]) => renderSection(section, items)).join("");
      root.innerHTML = heroHtml + sectionHtml;
      root.dataset.feishuRendered = "true";
      document.dispatchEvent(new CustomEvent("ai-plus-content-rendered", { detail: { pageKey, count: records.length } }));
    } catch (error) {
      console.warn("[AI++] Feishu content JSON unavailable, static fallback is kept.", error);
    }
  }

  boot();
})();
