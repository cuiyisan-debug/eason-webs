(() => {
  const root = document.querySelector("[data-ai-issues]");
  if (!root) return;

  const track = root.querySelector(".issues-track");
  const buttons = [...root.querySelectorAll(".issues-controls button")];
  const panels = [...root.querySelectorAll(".issue-panel")];
  let active = 0;
  let lastMove = 0;

  const revealItems = (panel) => [...panel.querySelectorAll(":scope > .issue-copy > .issue-quote, :scope > .issue-copy > .issue-summary, :scope > .issue-copy > h2, :scope > .issue-copy > .issue-small")];

  const resetReveal = (panel) => {
    revealItems(panel).forEach((item, index) => {
      item.dataset.reveal = "";
      item.classList.toggle("is-hidden", index !== 0);
    });
  };

  const setActive = (next) => {
    const bounded = Math.max(0, Math.min(buttons.length - 1, next));
    if (bounded === active) return;
    active = bounded;
    track.style.transform = `translateX(-${active * 25}%)`;
    buttons.forEach((button, index) => {
      if (index === active) button.setAttribute("aria-current", "step");
      else button.removeAttribute("aria-current");
    });
    resetReveal(panels[active]);
  };

  panels.forEach(resetReveal);
  buttons.forEach((button, index) => button.addEventListener("click", () => setActive(index)));

  root.addEventListener("click", (event) => {
    if (event.target.closest(".issues-controls")) return;
    const items = revealItems(panels[active]);
    const hidden = items.find((item) => item.classList.contains("is-hidden"));
    if (hidden) {
      hidden.classList.remove("is-hidden");
      return;
    }
    setActive(active + 1);
  });

  root.addEventListener("wheel", (event) => {
    if (Math.abs(event.deltaY) < Math.abs(event.deltaX) || Math.abs(event.deltaY) < 8) return;
    if ((active === 0 && event.deltaY < 0) || (active === buttons.length - 1 && event.deltaY > 0)) return;
    event.preventDefault();
    const now = Date.now();
    if (now - lastMove < 520) return;
    lastMove = now;
    setActive(active + (event.deltaY > 0 ? 1 : -1));
  }, { passive: false });
})();
