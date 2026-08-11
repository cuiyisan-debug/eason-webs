(() => {
  const root = document.querySelector("[data-ai-chapters]");
  if (!root) return;

  const track = root.querySelector(".chapter-track");
  const buttons = [...root.querySelectorAll(".chapter-controls button")];
  const chapters = [...root.querySelectorAll(".chapter")];
  let active = 0;
  let lastMove = 0;
  let touchStartX = 0;

  const revealItems = (chapter) => [...chapter.querySelectorAll(":scope > .chapter-copy > h1, :scope > .chapter-copy > .chapter-small, :scope > .chapter-copy > .chapter-lead, :scope > .chapter-copy > blockquote")];

  const resetReveal = (chapter) => {
    const items = revealItems(chapter);
    items.forEach((item) => {
      item.dataset.reveal = "";
      item.classList.add("is-hidden");
    });
    window.setTimeout(() => items[0]?.classList.remove("is-hidden"), 130);
  };

  const setActive = (next) => {
    const bounded = Math.max(0, Math.min(buttons.length - 1, next));
    if (bounded === active) return;
    active = bounded;
    track.style.transform = `translateX(-${active * 20}%)`;
    buttons.forEach((button, index) => {
      if (index === active) button.setAttribute("aria-current", "step");
      else button.removeAttribute("aria-current");
    });
    resetReveal(chapters[active]);
  };

  buttons.forEach((button, index) => button.addEventListener("click", () => setActive(index)));
  root.addEventListener("wheel", (event) => {
    if (Math.abs(event.deltaY) < Math.abs(event.deltaX) || Math.abs(event.deltaY) < 8) return;
    event.preventDefault();
    const now = Date.now();
    if (now - lastMove < 520) return;
    lastMove = now;
    setActive(active + (event.deltaY > 0 ? 1 : -1));
  }, { passive: false });
  root.addEventListener("touchstart", (event) => { touchStartX = event.changedTouches[0].clientX; }, { passive: true });
  root.addEventListener("touchend", (event) => {
    const distance = event.changedTouches[0].clientX - touchStartX;
    if (Math.abs(distance) > 42) setActive(active + (distance < 0 ? 1 : -1));
  }, { passive: true });
  root.addEventListener("click", (event) => {
    if (event.target.closest("button, a")) return;
    const hidden = revealItems(chapters[active]).find((item) => item.classList.contains("is-hidden"));
    if (hidden) hidden.classList.remove("is-hidden");
    else setActive(active + 1);
  });
  document.addEventListener("keydown", (event) => {
    if (event.target.closest("a, button")) return;
    if (event.key === "ArrowRight" || event.key === "ArrowDown") setActive(active + 1);
    if (event.key === "ArrowLeft" || event.key === "ArrowUp") setActive(active - 1);
  });
  resetReveal(chapters[active]);
})();
