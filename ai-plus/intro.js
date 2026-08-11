(() => {
  const root = document.querySelector("[data-ai-chapters]");
  if (!root) return;

  const track = root.querySelector(".chapter-track");
  const buttons = [...root.querySelectorAll(".chapter-controls button")];
  let active = 0;
  let lastMove = 0;
  let touchStartX = 0;

  const setActive = (next) => {
    const bounded = Math.max(0, Math.min(buttons.length - 1, next));
    if (bounded === active) return;
    active = bounded;
    track.style.transform = `translateX(-${active * 20}%)`;
    buttons.forEach((button, index) => {
      if (index === active) button.setAttribute("aria-current", "step");
      else button.removeAttribute("aria-current");
    });
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
  document.addEventListener("keydown", (event) => {
    if (event.target.closest("a, button")) return;
    if (event.key === "ArrowRight" || event.key === "ArrowDown") setActive(active + 1);
    if (event.key === "ArrowLeft" || event.key === "ArrowUp") setActive(active - 1);
  });
})();
