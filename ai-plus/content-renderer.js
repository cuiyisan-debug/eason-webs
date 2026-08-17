(() => {
  const params = new URLSearchParams(window.location.search);
  const pageKey = document.body?.dataset?.section;
  const root = document.querySelector("[data-ai-plus-content]");
  if (!pageKey || !root) return;
  const shouldRender = params.has("feishu") || root.dataset.aiPlusLive === "true";
  if (params.has("static") || !shouldRender) return;

  const PAGE_FILE = {
    overview: "overview.html",
    office: "office.html",
    "open-models": "open-models.html",
    agents: "agents.html",
    toolbox: "toolbox.html",
  };

  const PAGE_CLASS = {
    overview: "page-overview",
    office: "page-office",
    "open-models": "page-open-models",
    agents: "page-agents",
    toolbox: "page-toolbox",
  };

  const OFFICE_KIND = {
    "日常软件推荐": "daily",
    "浏览器及插件推荐": "browser",
    "正版软件推荐": "licensed",
    "工作习惯建议": "habit",
  };

  const TOOLBOX_KIND = {
    "综合导航站": "nav",
    "教程类": "tutorial",
    "B站 UP 推荐": "bilibili",
    "软件与小众工具": "software",
    "API 推荐": "api",
    "线上画布入口": "canvas",
  };

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

  const textOf = (item = {}) => item.body || item.note || "";

  const sectionIntro = (sections, name) => sections.get(name)?.find((item) => item.moduleType === "section");
  const sectionItems = (sections, name, type) => (sections.get(name) || []).filter((item) => item.moduleType === type);
  const firstOfType = (records, type) => records.find((item) => item.moduleType === type);

  function renderHero(hero, captions = []) {
    if (!hero) return "";
    return `
      <section class="live-hero live-hero--${escapeHtml(pageKey)}" id="top">
        <div class="live-hero-copy">
          ${hero.tag ? `<p class="live-eyebrow">${escapeHtml(hero.tag)}</p>` : ""}
          <h1>${escapeHtml(hero.title || "")}</h1>
          ${textOf(hero) ? `<p class="live-hero-lead">${escapeHtml(textOf(hero))}</p>` : ""}
        </div>
        <div class="live-hero-art" aria-hidden="true">
          <span class="orb orb-a"></span>
          <span class="orb orb-b"></span>
          <span class="orb orb-c"></span>
          ${captions.length ? `<div class="live-hero-captions">${captions.map((item) => `<span>${escapeHtml(item.title || textOf(item))}</span>`).join("")}</div>` : ""}
        </div>
      </section>`;
  }

  function renderResourceLinks(items = []) {
    if (!items.length) return "";
    return `
      <div class="live-resource-links">
        ${items.map((item) => `
          <a class="live-resource-link" href="${escapeHtml(item.linkUrl || "#")}" target="_blank" rel="noopener noreferrer">
            <strong>${escapeHtml(item.linkTitle || item.title || "打开链接")}</strong>
            <small>${escapeHtml(textOf(item) || item.note || "查看资源说明")}</small>
          </a>
        `).join("")}
      </div>`;
  }

  function renderInlineList(items = []) {
    if (!items.length) return "";
    return `
      <div class="live-inline-list">
        ${items.map((item) => `
          <a class="live-inline-row" href="${escapeHtml(item.linkUrl || "#")}" target="_blank" rel="noopener noreferrer">
            <strong>${escapeHtml(item.title || item.linkTitle || "")}</strong>
            <span>${escapeHtml(textOf(item) || item.note || "打开资源")}</span>
          </a>
        `).join("")}
      </div>`;
  }

  function renderCaseCard(item, compact = false) {
    if (!item) return "";
    const href = `./article.html?id=${encodeURIComponent(item.key || item.id)}&from=${encodeURIComponent(PAGE_FILE[pageKey] || "overview.html")}`;
    const cover = item.cover ? ` style="background-image:url('${escapeHtml(item.cover)}')"` : "";
    return `
      <a class="live-case-card${compact ? " is-compact" : ""}" href="${escapeHtml(href)}" data-ai-plus-article-link>
        <span class="live-case-cover${item.cover ? " has-cover" : ""}"${cover}>
          <span class="cover-grid"></span>
        </span>
        <span class="live-case-copy">
          ${item.tag ? `<small>${escapeHtml(item.tag)}</small>` : ""}
          <strong>${escapeHtml(item.title || "")}</strong>
          ${textOf(item) ? `<span>${escapeHtml(textOf(item))}</span>` : ""}
        </span>
      </a>`;
  }

  function renderOverview(records, sections) {
    const hero = firstOfType(records, "hero");
    const captions = records.filter((item) => item.section === "顶部引导" && item.moduleType === "caption");
    const mapIntro = sectionIntro(sections, "总地图");
    const mapCards = sectionItems(sections, "总地图", "card");
    const timelineIntro = sectionIntro(sections, "发展脉络");
    const timelineItems = sectionItems(sections, "发展脉络", "timeline");
    const termsIntro = sectionIntro(sections, "核心名词");
    const terms = sectionItems(sections, "核心名词", "term");
    const toolsIntro = sectionIntro(sections, "工具分类");
    const tools = sectionItems(sections, "工具分类", "tool");

    return `
      <div class="live-page ${PAGE_CLASS[pageKey]}">
        ${renderHero(hero, captions)}

        <section class="live-section">
          <div class="live-section-head">
            <h2>${escapeHtml(mapIntro?.title || "先建立一张总地图")}</h2>
            ${textOf(mapIntro) ? `<p>${escapeHtml(textOf(mapIntro))}</p>` : ""}
          </div>
          <div class="live-overview-map">
            ${mapCards.map((item) => `
              <article class="live-map-card">
                <h3>${escapeHtml(item.title || "")}</h3>
                ${textOf(item) ? `<p>${escapeHtml(textOf(item))}</p>` : ""}
                ${item.note ? `<small>${escapeHtml(item.note)}</small>` : ""}
              </article>
            `).join("")}
          </div>
        </section>

        <section class="live-section">
          <div class="live-section-head">
            <h2>${escapeHtml(timelineIntro?.title || "AI 发展脉络")}</h2>
            ${textOf(timelineIntro) ? `<p>${escapeHtml(textOf(timelineIntro))}</p>` : ""}
          </div>
          <div class="live-timeline">
            ${timelineItems.map((item) => `
              <article class="live-timeline-row">
                <b>${escapeHtml(item.tag || "")}</b>
                <div>
                  <h3>${escapeHtml(item.title || "")}</h3>
                  ${textOf(item) ? `<p>${escapeHtml(textOf(item))}</p>` : ""}
                </div>
              </article>
            `).join("")}
          </div>
        </section>

        <section class="live-section">
          <div class="live-section-head">
            <h2>${escapeHtml(termsIntro?.title || "核心名词")}</h2>
            ${textOf(termsIntro) ? `<p>${escapeHtml(textOf(termsIntro))}</p>` : ""}
          </div>
          <div class="live-terms-grid">
            ${terms.map((item) => `
              <article class="live-term-card">
                <h3>${escapeHtml(item.title || "")}</h3>
                ${textOf(item) ? `<p>${escapeHtml(textOf(item))}</p>` : ""}
                ${item.note ? `<small>${escapeHtml(item.note)}</small>` : ""}
              </article>
            `).join("")}
          </div>
        </section>

        <section class="live-section">
          <div class="live-section-head">
            <h2>${escapeHtml(toolsIntro?.title || "AI 工具分类认知体系")}</h2>
            ${textOf(toolsIntro) ? `<p>${escapeHtml(textOf(toolsIntro))}</p>` : ""}
          </div>
          <div class="live-tooltype-grid">
            ${tools.map((item) => `
              <article class="live-tooltype-card">
                <h3>${escapeHtml(item.title || "")}</h3>
                ${textOf(item) ? `<p>${escapeHtml(textOf(item))}</p>` : ""}
                ${item.note ? `<small>${escapeHtml(item.note)}</small>` : ""}
                ${item.linkUrl ? `<a href="${escapeHtml(item.linkUrl)}" target="_blank" rel="noopener noreferrer">${escapeHtml(item.linkTitle || "查看入口")}</a>` : ""}
              </article>
            `).join("")}
          </div>
        </section>
      </div>`;
  }

  function renderOffice(records, sections) {
    const hero = firstOfType(records, "hero");
    const comboIntro = sectionIntro(sections, "四类组合");
    const order = ["日常软件推荐", "浏览器及插件推荐", "正版软件推荐", "工作习惯建议"];

    return `
      <div class="live-page ${PAGE_CLASS[pageKey]}">
        ${renderHero(hero)}
        <section class="live-section">
          <div class="live-section-head">
            <h2>${escapeHtml(comboIntro?.title || "四类组合，按问题使用")}</h2>
            ${textOf(comboIntro) ? `<p>${escapeHtml(textOf(comboIntro))}</p>` : ""}
          </div>
          <div class="live-resource-grid live-resource-grid--office">
            ${order.map((name) => {
              const introCard = sectionItems(sections, name, "card")[0];
              const links = sectionItems(sections, name, "link");
              const cases = sectionItems(sections, name, "case");
              const kind = OFFICE_KIND[name] || "office";
              return `
                <article class="live-resource-card" data-kind="${escapeHtml(kind)}">
                  <div class="live-resource-title">
                    <h3>${escapeHtml(introCard?.title || name)}</h3>
                    ${introCard?.tag ? `<span class="live-chip">${escapeHtml(introCard.tag)}</span>` : ""}
                  </div>
                  ${textOf(introCard) ? `<p>${escapeHtml(textOf(introCard))}</p>` : ""}
                  ${renderInlineList(links)}
                </article>
                ${cases.map((item) => renderCaseCard(item, true)).join("")}
              `;
            }).join("")}
          </div>
        </section>
      </div>`;
  }

  function renderOpenModels(records, sections) {
    const hero = firstOfType(records, "hero");
    const evolutionIntro = sectionIntro(sections, "发展迭代");
    const evolution = sectionItems(sections, "发展迭代", "pipeline");
    const modelsIntro = sectionIntro(sections, "常见开源大模型");
    const models = sectionItems(sections, "常见开源大模型", "card");
    const caseIntro = sectionIntro(sections, "应用实例");
    const cases = sectionItems(sections, "应用实例", "case");
    const canvasIntro = sectionIntro(sections, "无限画布");
    const canvasLinks = sectionItems(sections, "无限画布", "link");

    return `
      <div class="live-page ${PAGE_CLASS[pageKey]}">
        ${renderHero(hero)}

        <section class="live-section">
          <div class="live-section-head">
            <h2>${escapeHtml(evolutionIntro?.title || "开源模型发展迭代")}</h2>
            ${textOf(evolutionIntro) ? `<p>${escapeHtml(textOf(evolutionIntro))}</p>` : ""}
          </div>
          <div class="live-journey-grid">
            ${evolution.map((item) => `
              <article class="live-stage-card">
                ${item.tag ? `<b>${escapeHtml(item.tag)}</b>` : ""}
                <h3>${escapeHtml(item.title || "")}</h3>
                ${textOf(item) ? `<p>${escapeHtml(textOf(item))}</p>` : ""}
              </article>
            `).join("")}
          </div>
        </section>

        <section class="live-section">
          <div class="live-section-head">
            <h2>${escapeHtml(modelsIntro?.title || "常见开源大模型")}</h2>
            ${textOf(modelsIntro) ? `<p>${escapeHtml(textOf(modelsIntro))}</p>` : ""}
          </div>
          <div class="live-model-grid">
            ${models.map((item) => `
              <article class="live-model-card">
                <div class="live-resource-title">
                  <h3>${escapeHtml(item.title || "")}</h3>
                  ${item.tag ? `<span class="live-chip">${escapeHtml(item.tag)}</span>` : ""}
                </div>
                ${textOf(item) ? `<p>${escapeHtml(textOf(item))}</p>` : ""}
                ${item.note && item.note !== textOf(item) ? `<small>${escapeHtml(item.note)}</small>` : ""}
                ${item.linkUrl ? `<a href="${escapeHtml(item.linkUrl)}" target="_blank" rel="noopener noreferrer">${escapeHtml(item.linkTitle || "查看模型入口")}</a>` : ""}
              </article>
            `).join("")}
          </div>
        </section>

        <section class="live-section">
          <div class="live-section-head">
            <h2>${escapeHtml(caseIntro?.title || "应用实例")}</h2>
            ${textOf(caseIntro) ? `<p>${escapeHtml(textOf(caseIntro))}</p>` : ""}
          </div>
          <div class="live-case-grid">
            ${cases.map((item) => renderCaseCard(item)).join("")}
          </div>
        </section>

        <section class="live-section">
          <div class="live-section-head">
            <h2>${escapeHtml(canvasIntro?.title || "无限画布")}</h2>
            ${textOf(canvasIntro) ? `<p>${escapeHtml(textOf(canvasIntro))}</p>` : ""}
          </div>
          <div class="live-resource-grid">
            ${canvasLinks.map((item) => `
              <article class="live-resource-card" data-kind="canvas">
                <div class="live-resource-title">
                  <h3>${escapeHtml(item.title || item.linkTitle || "")}</h3>
                </div>
                ${textOf(item) ? `<p>${escapeHtml(textOf(item))}</p>` : ""}
                ${item.linkUrl ? `<a href="${escapeHtml(item.linkUrl)}" target="_blank" rel="noopener noreferrer">${escapeHtml(item.linkTitle || "打开网站")}</a>` : ""}
              </article>
            `).join("")}
          </div>
        </section>
      </div>`;
  }

  function renderAgents(records, sections) {
    const hero = firstOfType(records, "hero");
    const journeyIntro = sectionIntro(sections, "发展路径");
    const journey = sectionItems(sections, "发展路径", "pipeline");
    const platformsIntro = sectionIntro(sections, "常见平台");
    const platforms = sectionItems(sections, "常见平台", "card");
    const casesIntro = sectionIntro(sections, "应用实例");
    const cases = sectionItems(sections, "应用实例", "case");

    return `
      <div class="live-page ${PAGE_CLASS[pageKey]}">
        ${renderHero(hero)}

        <section class="live-section">
          <div class="live-section-head">
            <h2>${escapeHtml(journeyIntro?.title || "Agent 发展路径")}</h2>
            ${textOf(journeyIntro) ? `<p>${escapeHtml(textOf(journeyIntro))}</p>` : ""}
          </div>
          <div class="live-journey-grid">
            ${journey.map((item) => `
              <article class="live-stage-card">
                ${item.tag ? `<b>${escapeHtml(item.tag)}</b>` : ""}
                <h3>${escapeHtml(item.title || "")}</h3>
                ${textOf(item) ? `<p>${escapeHtml(textOf(item))}</p>` : ""}
              </article>
            `).join("")}
          </div>
        </section>

        <section class="live-section">
          <div class="live-section-head">
            <h2>${escapeHtml(platformsIntro?.title || "常见智能体平台")}</h2>
            ${textOf(platformsIntro) ? `<p>${escapeHtml(textOf(platformsIntro))}</p>` : ""}
          </div>
          <div class="live-platform-grid">
            ${platforms.map((item) => `
              <article class="live-platform-card">
                <div class="live-resource-title">
                  <h3>${escapeHtml(item.title || "")}</h3>
                  ${item.tag ? `<span class="live-chip">${escapeHtml(item.tag)}</span>` : ""}
                </div>
                ${textOf(item) ? `<p>${escapeHtml(textOf(item))}</p>` : ""}
                ${item.linkUrl ? `<a href="${escapeHtml(item.linkUrl)}" target="_blank" rel="noopener noreferrer">${escapeHtml(item.linkTitle || "查看入口")}</a>` : ""}
              </article>
            `).join("")}
          </div>
        </section>

        <section class="live-section">
          <div class="live-section-head">
            <h2>${escapeHtml(casesIntro?.title || "应用实例")}</h2>
            ${textOf(casesIntro) ? `<p>${escapeHtml(textOf(casesIntro))}</p>` : ""}
          </div>
          <div class="live-case-grid">
            ${cases.map((item) => renderCaseCard(item)).join("")}
          </div>
        </section>
      </div>`;
  }

  function renderToolbox(records, sections) {
    const hero = firstOfType(records, "hero");
    const intro = sectionIntro(sections, "五类入口");
    const order = ["综合导航站", "教程类", "B站 UP 推荐", "软件与小众工具", "API 推荐", "线上画布入口"];

    return `
      <div class="live-page ${PAGE_CLASS[pageKey]}">
        ${renderHero(hero)}
        <section class="live-section">
          <div class="live-section-head">
            <h2>${escapeHtml(intro?.title || "五类入口，按任务找资源")}</h2>
            ${textOf(intro) ? `<p>${escapeHtml(textOf(intro))}</p>` : ""}
          </div>
          <div class="live-filter-bar" aria-label="AI 工具箱分类筛选">
            <button class="live-filter is-active" type="button" data-filter="all">全部</button>
            <button class="live-filter" type="button" data-filter="nav">综合导航站</button>
            <button class="live-filter" type="button" data-filter="tutorial">教程类</button>
            <button class="live-filter" type="button" data-filter="bilibili">B站 UP 推荐</button>
            <button class="live-filter" type="button" data-filter="software">软件与小众工具</button>
            <button class="live-filter" type="button" data-filter="api">API 推荐</button>
            <button class="live-filter" type="button" data-filter="canvas">线上画布入口</button>
          </div>
          <div class="live-resource-grid live-resource-grid--toolbox">
            ${order.map((name) => {
              const introCard = sectionItems(sections, name, "card")[0];
              const links = sectionItems(sections, name, "link");
              const kind = TOOLBOX_KIND[name] || "misc";
              return `
                <article class="live-resource-card" data-kind="${escapeHtml(kind)}">
                  <div class="live-resource-title">
                    <h3>${escapeHtml(introCard?.title || name)}</h3>
                    ${introCard?.tag ? `<span class="live-chip">${escapeHtml(introCard.tag)}</span>` : ""}
                  </div>
                  ${textOf(introCard) ? `<p>${escapeHtml(textOf(introCard))}</p>` : ""}
                  ${renderInlineList(links)}
                </article>
              `;
            }).join("")}
          </div>
        </section>
      </div>`;
  }

  function initToolboxFilters() {
    if (pageKey !== "toolbox") return;
    const filters = root.querySelectorAll(".live-filter");
    const cards = root.querySelectorAll(".live-resource-grid--toolbox .live-resource-card");
    if (!filters.length || !cards.length) return;
    filters.forEach((button) => {
      button.addEventListener("click", () => {
        const value = button.dataset.filter || "all";
        filters.forEach((item) => item.classList.toggle("is-active", item === button));
        cards.forEach((card) => {
          const kind = card.dataset.kind || "";
          card.classList.toggle("is-hidden", value !== "all" && kind !== value);
        });
      });
    });
  }

  async function mergeArticleCovers(records) {
    const needsCover = records.some((item) => (item.moduleType === "case" || item.moduleType === "article" || (item.linkUrl || "").includes("feishu.cn/docx/")) && !item.cover);
    if (!needsCover) return records;
    try {
      const response = await fetch(`../api/ai-plus-articles.json?v=${Date.now()}`, { cache: "no-store" });
      if (!response.ok) return records;
      const data = await response.json();
      const articlesById = new Map((data.articles || []).map((item) => [item.id || item.key, item]));
      return records.map((item) => {
        const article = articlesById.get(item.key || item.id);
        if (!article) return item;
        return {
          ...item,
          cover: item.cover || article.cover || "",
          title: article.title || item.title,
          body: article.summary || item.body,
        };
      });
    } catch {
      return records;
    }
  }

  function renderPageContent(records) {
    const sections = groupBy(records.filter((item) => !["hero", "caption"].includes(item.moduleType)));
    switch (pageKey) {
      case "overview":
        return renderOverview(records, sections);
      case "office":
        return renderOffice(records, sections);
      case "open-models":
        return renderOpenModels(records, sections);
      case "agents":
        return renderAgents(records, sections);
      case "toolbox":
        return renderToolbox(records, sections);
      default:
        return "";
    }
  }

  async function boot() {
    try {
      const response = await fetch(`../api/ai-plus-content.json?v=${Date.now()}`, { cache: "no-store" });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      const page = data.pages?.[pageKey];
      if (!page?.records?.length) return;
      const records = await mergeArticleCovers(page.records.filter((item) => item.enabled !== false));
      const html = renderPageContent(records);
      if (!html) return;
      root.innerHTML = html;
      root.classList.add("live-rendered");
      root.dataset.feishuRendered = "true";
      initToolboxFilters();
      document.dispatchEvent(new CustomEvent("ai-plus-content-rendered", { detail: { pageKey, count: records.length } }));
    } catch (error) {
      console.warn("[AI++] Feishu content JSON unavailable, static fallback is kept.", error);
    }
  }

  boot();
})();
