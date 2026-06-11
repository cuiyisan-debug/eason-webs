const state = {
  items: [],
  activeFilter: "All"
};

const grid = document.querySelector("[data-grid]");
const filters = document.querySelector("[data-filters]");
const header = document.querySelector("[data-header]");
const dialog = document.querySelector("[data-dialog]");
const closeButton = document.querySelector("[data-close]");

const cover = document.querySelector("[data-dialog-cover]");
const title = document.querySelector("[data-dialog-title]");
const meta = document.querySelector("[data-dialog-meta]");
const description = document.querySelector("[data-dialog-description]");
const link = document.querySelector("[data-dialog-link]");

async function loadPortfolio() {
  const response = await fetch("./api/portfolio.json");
  if (!response.ok) throw new Error("Unable to load api/portfolio.json");
  const data = await response.json();
  state.items = [...data.items].sort((a, b) => a.order - b.order);
  document.querySelector("[data-count]").textContent = `${data._count} pieces`;
  renderFilters();
  renderGrid();
}

function getCategories() {
  const categories = new Set();
  state.items.forEach((item) => item.categories.forEach((category) => categories.add(category)));
  return ["All", ...categories];
}

function renderFilters() {
  filters.innerHTML = "";
  getCategories().forEach((category) => {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = category;
    button.className = category === state.activeFilter ? "is-active" : "";
    button.setAttribute("role", "tab");
    button.setAttribute("aria-selected", category === state.activeFilter ? "true" : "false");
    button.addEventListener("click", () => {
      state.activeFilter = category;
      renderFilters();
      renderGrid();
    });
    filters.appendChild(button);
  });
}

function renderGrid() {
  const items = state.activeFilter === "All"
    ? state.items
    : state.items.filter((item) => item.categories.includes(state.activeFilter));

  grid.innerHTML = "";
  items.forEach((item, index) => {
    const card = document.createElement("article");
    card.className = "project-card reveal";
    card.style.transitionDelay = `${Math.min(index * 45, 240)}ms`;
    card.tabIndex = 0;
    card.innerHTML = `
      <img src="${item.cover_url}" alt="">
      <div class="card-content">
        <span class="card-kicker">${item.categories.join(" / ")} · ${item.year}</span>
        <h3>${item.title}</h3>
        <div class="card-meta">
          <span>${item.duration}</span>
          <span>${item.tools}</span>
        </div>
      </div>
    `;
    card.addEventListener("click", () => openProject(item));
    card.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        openProject(item);
      }
    });
    grid.appendChild(card);
  });
  observeReveals();
}

function openProject(item) {
  cover.src = item.cover_url;
  cover.alt = `${item.title} cover`;
  title.textContent = item.title;
  meta.textContent = `${item.categories.join(" / ")} · ${item.duration} · ${item.tools}`;
  description.textContent = item.description;
  link.href = item.video_url || item.cover_url;
  link.textContent = item.video_url ? "Open Video" : "Open Cover";
  dialog.showModal();
}

function observeReveals() {
  if (!("IntersectionObserver" in window)) {
    document.querySelectorAll(".reveal").forEach((element) => element.classList.add("is-visible"));
    return;
  }

  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add("is-visible");
        observer.unobserve(entry.target);
      }
    });
  }, { rootMargin: "0px 0px 220px", threshold: 0.04 });

  document.querySelectorAll(".reveal:not(.is-visible)").forEach((element) => observer.observe(element));
}

closeButton.addEventListener("click", () => dialog.close());
dialog.addEventListener("click", (event) => {
  if (event.target === dialog) dialog.close();
});

window.addEventListener("scroll", () => {
  header.classList.toggle("is-scrolled", window.scrollY > 12);
}, { passive: true });

loadPortfolio().then(observeReveals).catch((error) => {
  grid.innerHTML = `<p>${error.message}</p>`;
});
