const state = {
  progress: 0,
  threeReady: false,
  scene: null,
  camera: null,
  renderer: null,
  portraitGroup: null,
  particles: null,
  dots: [],
};

const fallbackProjects = [
  { title: "安徽自贸区展厅", cover: "./assets/portrait-creative-management.png" },
  { title: "中关村论坛", cover: "./assets/portrait-creative-management.png" },
  { title: "大同城市规划馆", cover: "./assets/portrait-creative-management.png" },
  { title: "国家海洋信息中心展厅", cover: "./assets/portrait-creative-management.png" },
];

document.documentElement.classList.add("intro-pending");

function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max);
}

function setupHeaderNav() {
  const header = document.querySelector(".site-header");
  const toggle = document.querySelector(".nav-toggle");
  const nav = document.querySelector(".nav");
  if (!header || !toggle || !nav) return;

  let lastScrollY = window.scrollY;
  let ticking = false;

  const updateHeaderVisibility = () => {
    const currentScrollY = window.scrollY;
    const delta = currentScrollY - lastScrollY;
    const pastHeader = currentScrollY > header.offsetHeight + 28;
    const menuOpen = header.classList.contains("nav-open");

    if (menuOpen || currentScrollY < 12 || delta < -6) {
      header.classList.remove("nav-hidden");
    } else if (pastHeader && delta > 6) {
      header.classList.add("nav-hidden");
    }

    lastScrollY = currentScrollY;
    ticking = false;
  };

  window.addEventListener("scroll", () => {
    if (ticking) return;
    ticking = true;
    window.requestAnimationFrame(updateHeaderVisibility);
  }, { passive: true });

  toggle.addEventListener("click", () => {
    const isOpen = header.classList.toggle("nav-open");
    header.classList.remove("nav-hidden");
    toggle.setAttribute("aria-expanded", String(isOpen));
  });

  nav.addEventListener("click", (event) => {
    if (!(event.target instanceof HTMLAnchorElement)) return;
    header.classList.remove("nav-open");
    toggle.setAttribute("aria-expanded", "false");
  });
}

function setupBrandNavigation() {
  const videoEntry = document.querySelector(".brand-logo-link");
  const homeEntry = document.querySelector(".brand-text");

  videoEntry?.addEventListener("click", (event) => {
    event.preventDefault();
    window.location.assign("./three-portrait-journey.html#top");
  });

  homeEntry?.addEventListener("click", (event) => {
    event.preventDefault();
    window.location.assign("./home.html#top");
  });
}

function setupTheme() {
  const toggle = document.querySelector(".theme-toggle");
  // The five-scene film is intentionally fixed in a dark treatment. Do not
  // overwrite the visitor's theme preference for the main portfolio site.
  document.documentElement.dataset.theme = "dark";
  document.documentElement.classList.add("journey-theme-locked");
  document.querySelectorAll(".brand-logo, .fifth-return-logo").forEach((logo) => {
    logo.src = "./assets/site-logo-dark.svg";
  });

  if (toggle) {
    toggle.disabled = true;
    toggle.hidden = true;
    toggle.setAttribute("aria-hidden", "true");
    toggle.setAttribute("tabindex", "-1");
  }
}

function setupHeroVideoIntro() {
  const root = document.documentElement;
  const video = document.querySelector(".hero-video");
  const capabilityPanel = document.querySelector(".hero-right-panel--intro");
  const targetLoopSeconds = 5;
  const minimumLoaderMs = 360;
  const firstFrameHoldMs = 720;
  const introStartedAt = performance.now();
  let hasLeftHero = false;
  let replaying = false;
  let heroStarted = false;
  let firstFramePrepared = false;

  const revealInterface = () => {
    root.classList.add("intro-ui-ready", "is-ready");
    root.classList.remove("intro-pending");
  };

  const revealVideo = () => {
    root.classList.add("intro-video-ready");
  };

  const startHeroPlayback = () => {
    if (heroStarted) return;
    heroStarted = true;
    const playPromise = video.play();
    if (playPromise && typeof playPromise.catch === "function") playPromise.catch(() => {});
  };

  const completeIntro = () => {
    if (firstFramePrepared) return;
    firstFramePrepared = true;
    video.pause();
    try { video.currentTime = 0; } catch (_) {}
    revealVideo();
    const elapsed = performance.now() - introStartedAt;
    const remainder = Math.max(0, minimumLoaderMs - elapsed);
    window.setTimeout(() => {
      revealInterface();
      window.setTimeout(startHeroPlayback, firstFrameHoldMs);
    }, remainder);
  };

  if (!video) {
    revealInterface();
    return;
  }

  const tunePlaybackRate = () => {
    const duration = Number.isFinite(video.duration) ? video.duration : 0;
    video.playbackRate = duration > targetLoopSeconds ? clamp(duration / targetLoopSeconds, 1, 3.2) : 1;
  };

  const syncCapabilityReveal = () => {
    const duration = Number.isFinite(video.duration) ? video.duration : 0;
    if (!duration) return;
    const progress = clamp(video.currentTime / duration, 0, 1);
    capabilityPanel?.classList.toggle("is-capability-ready", progress >= 0.78);
  };

  const replayFromStart = () => {
    if (replaying) return;
    replaying = true;
    root.classList.remove("hero-video-ended");
    capabilityPanel?.classList.remove("is-capability-ready");
    video.currentTime = 0;
    const replayPromise = video.play();
    if (replayPromise && typeof replayPromise.then === "function") {
      replayPromise
        .catch(() => {})
        .finally(() => {
          replaying = false;
        });
    } else {
      replaying = false;
    }
  };

  video.loop = false;
  video.muted = true;
  video.playsInline = true;
  video.addEventListener("loadedmetadata", tunePlaybackRate, { once: true });
  video.addEventListener("loadeddata", completeIntro, { once: true });
  video.addEventListener("canplay", completeIntro, { once: true });
  video.addEventListener("timeupdate", syncCapabilityReveal);
  video.addEventListener("ended", () => {
    capabilityPanel?.classList.add("is-capability-ready");
    root.classList.add("hero-video-ended");
    video.pause();
  });

  window.addEventListener("scroll", () => {
    if (window.scrollY > window.innerHeight * 0.42) {
      hasLeftHero = true;
      return;
    }
    if (hasLeftHero && window.scrollY < window.innerHeight * 0.14) {
      hasLeftHero = false;
      replayFromStart();
    }
  }, { passive: true });

  window.setTimeout(() => {
    tunePlaybackRate();
    completeIntro();
  }, 1300);
}

function setupDeferredVideoLoading() {
  const isMobile = window.matchMedia("(max-width: 900px), (pointer: coarse)").matches;
  const sequence = document.querySelector("#cinematic-sequence");
  const staged = [
    {
      scene: document.querySelector("#tools"),
      video: document.querySelector(".tools-video"),
      // Both opening scenes are sticky, so tools.offsetTop remains 0. Its
      // actual scroll entrance is one viewport after the portrait scene.
      // A touch device needs the second clip buffered while the first scene is
      // still visible; otherwise the first scroll can arrive before decoding.
      trigger: () => (sequence?.offsetTop || 0) + window.innerHeight * (isMobile ? -0.1 : 0.28),
    },
    { scene: document.querySelector("#city-data"), video: document.querySelector(".city-data-video") },
    { scene: document.querySelector("#fourth"), video: document.querySelector(".fourth-video") },
    { scene: document.querySelector("#fifth"), video: document.querySelector(".fifth-video") },
  ].filter(({ scene, video }) => scene && video);

  const promote = (video) => {
    if (video.dataset.preloadReady === "true") return;
    video.dataset.preloadReady = "true";
    video.preload = "auto";
    video.load();
  };

  // Desktop has enough headroom to keep the original instant transitions.
  if (!isMobile) {
    staged.forEach(({ video }) => promote(video));
    return;
  }

  let nextIndex = 0;
  let loading = false;
  let ticking = false;

  const pump = () => {
    ticking = false;
    if (loading || nextIndex >= staged.length) return;
    const next = staged[nextIndex];
    // Keep exactly one upcoming clip in the media buffer on touch devices.
    // This stays serial, so it does not compete with five simultaneous downloads.
    const preloadLead = isMobile ? 1.15 : 0.34;
    const triggerY = next.trigger ? next.trigger() : next.scene.offsetTop - window.innerHeight * preloadLead;
    if (window.scrollY < triggerY) return;

    loading = true;
    let finished = false;
    const finish = () => {
      if (finished) return;
      finished = true;
      next.video.removeEventListener("loadeddata", finish);
      loading = false;
      nextIndex += 1;
      window.setTimeout(pump, 80);
    };
    next.video.addEventListener("loadeddata", finish, { once: true });
    promote(next.video);
    // Some Android browsers delay loadeddata while the page is settling.
    window.setTimeout(finish, 2400);
  };

  const schedulePump = () => {
    if (ticking) return;
    ticking = true;
    window.requestAnimationFrame(pump);
  };

  window.addEventListener("scroll", schedulePump, { passive: true });
  window.addEventListener("resize", schedulePump);
  // Let the opening frame draw first, then quietly warm the next scene.
  window.setTimeout(schedulePump, isMobile ? 750 : 0);
}

function setupGlobalCursorAura() {
  const root = document.documentElement;
  const journey = document.querySelector(".journey");
  if (!journey || window.matchMedia("(pointer: coarse)").matches) return;

  window.addEventListener("pointermove", (event) => {
    const target = event.target;
    const isMenuSurface = target instanceof Element && target.closest(".site-header");
    root.style.setProperty("--cursor-x", `${event.clientX}px`);
    root.style.setProperty("--cursor-y", `${event.clientY}px`);
    if (isMenuSurface) {
      root.classList.remove("cursor-aura-active");
      return;
    }
    root.classList.add("cursor-aura-active");
  }, { passive: true });

  window.addEventListener("blur", () => {
    root.classList.remove("cursor-aura-active");
  });
  document.addEventListener("mouseleave", () => {
    root.classList.remove("cursor-aura-active");
  });
}

function updateProgress() {
  const max = Math.max(document.documentElement.scrollHeight - window.innerHeight, 1);
  state.progress = clamp(window.scrollY / max, 0, 1);
  if (state.threeReady) {
    updateThreeScene(state.progress);
  }
}

function smoothstep(edge0, edge1, value) {
  const x = clamp((value - edge0) / (edge1 - edge0), 0, 1);
  return x * x * (3 - 2 * x);
}

function setupCinematicTransition() {
  const sequence = document.querySelector(".cinematic-sequence");
  const heroVideo = document.querySelector(".hero-video");
  const toolsVideo = document.querySelector(".tools-video");
  const toolKeywordNodes = Array.from(document.querySelectorAll(".tools-keyword"));
  const leftToolKeywordNodes = Array.from(document.querySelectorAll(".tools-keyword-left"));
  const rightToolKeywordNodes = Array.from(document.querySelectorAll(".tools-keyword-right"));
  const toolCapabilities = document.querySelector(".tools-capabilities");
  const toolsScene = document.querySelector(".scene-tools");
  if (!sequence) return;
  let toolsStarted = false;
  let toolsFinished = false;
  let scrollTicking = false;

  const resetToolsReveal = () => {
    toolKeywordNodes.forEach((node) => node.classList.remove("is-visible"));
    toolCapabilities?.classList.remove("is-capability-ready");
    toolsScene?.classList.remove("is-keywords-complete");
  };

  const syncToolsReveal = () => {
    const duration = Number.isFinite(toolsVideo?.duration) ? toolsVideo.duration : 0;
    if (!duration) return;
    const progress = clamp(toolsVideo.currentTime / duration, 0, 1);
    [leftToolKeywordNodes, rightToolKeywordNodes].forEach((nodes) => {
      nodes.forEach((node, index) => {
        const order = Number(node.dataset.order) || index + 1;
        // The city begins growing in the latter half of the clip. Let each side's
        // labels travel outward with that growth rather than appearing over the coin.
        const phaseOffset = node.closest(".tools-keyword-stage-en") ? 0.61 : 0.56;
        const threshold = phaseOffset + (order - 1) * 0.022;
        node.classList.toggle("is-visible", progress >= threshold);
      });
    });
    toolCapabilities?.classList.toggle("is-capability-ready", progress >= 0.82);
    toolsScene?.classList.toggle("is-keywords-complete", progress >= 0.82);
  };

  if (toolsVideo) {
    toolsVideo.loop = false;
    const tuneToolsPlaybackRate = () => {
      const duration = Number.isFinite(toolsVideo.duration) ? toolsVideo.duration : 0;
      toolsVideo.playbackRate = duration > 5 ? duration / 5 : 1;
    };
    toolsVideo.addEventListener("loadedmetadata", tuneToolsPlaybackRate, { once: true });
    tuneToolsPlaybackRate();
    toolsVideo.addEventListener("timeupdate", syncToolsReveal);
    toolsVideo.addEventListener("ended", () => {
      toolsFinished = true;
      toolKeywordNodes.forEach((node) => node.classList.add("is-visible"));
      toolCapabilities?.classList.add("is-capability-ready");
      toolsScene?.classList.add("is-keywords-complete");
      toolsVideo.pause();
    });
    resetToolsReveal();
  }

  const update = () => {
    const rect = sequence.getBoundingClientRect();
    const scrollable = Math.max(rect.height - window.innerHeight, 1);
    const progress = clamp(-rect.top / scrollable, 0, 1);
    const blend = smoothstep(0.56, 0.78, progress);
    const toolsActive = blend > 0.52;

    sequence.style.setProperty("--cinematic-progress", progress.toFixed(4));
    sequence.style.setProperty("--portrait-opacity", String(clamp(1 - blend, 0, 1)));
    sequence.style.setProperty("--portrait-scale", String(1 - blend * 0.012));
    sequence.style.setProperty("--portrait-y", `${Math.round(-blend * 8)}px`);
    sequence.style.setProperty("--tools-opacity", String(blend));
    const isNarrow = window.matchMedia("(max-width: 900px)").matches;
    sequence.style.setProperty("--tools-scale", String(isNarrow ? 1 : 1.01 - blend * 0.01));
    sequence.style.setProperty("--tools-y", `${Math.round((1 - blend) * 8)}px`);
    sequence.classList.toggle("is-tools-active", toolsActive);

    if (toolsVideo && progress < 0.48) {
      toolsStarted = false;
      toolsFinished = false;
      resetToolsReveal();
      if (!toolsVideo.paused) toolsVideo.pause();
      if (toolsVideo.readyState > 0 && toolsVideo.currentTime > 0.02) toolsVideo.currentTime = 0;
    }
    if (toolsVideo && progress >= 0.52 && !toolsStarted && !toolsFinished) {
      toolsStarted = true;
      if (toolsVideo.readyState > 0) toolsVideo.currentTime = 0;
      const playPromise = toolsVideo.play();
      if (playPromise && typeof playPromise.catch === "function") {
        playPromise.catch(() => {
          toolsStarted = false;
        });
      }
    }
  };

  const scheduleUpdate = () => {
    if (scrollTicking) return;
    scrollTicking = true;
    window.requestAnimationFrame(() => {
      scrollTicking = false;
      update();
    });
  };

  window.addEventListener("scroll", scheduleUpdate, { passive: true });
  window.addEventListener("resize", update);
  update();
}

function setupSceneSnap() {
  const sequence = document.querySelector(".cinematic-sequence");
  const portrait = document.querySelector("#portrait");
  const tools = document.querySelector("#tools");
  const city = document.querySelector("#city-data");
  const fourth = document.querySelector("#fourth");
  const fifth = document.querySelector("#fifth");
  if (!sequence || !portrait || !tools || !city || !fourth || !fifth) return;

  let settleTimer = 0;
  let releaseTimer = 0;
  let isSettling = false;
  let wheelLocked = false;

  const getAnchors = () => {
    // Do not infer scene positions from the viewport. Mobile browser chrome can
    // change window.innerHeight mid-gesture, while the scenes use stable svh.
    // The second scene is sticky, so its visible position is not its scroll
    // anchor; its start is exactly one rendered portrait-scene tall.
    const firstSceneTop = sequence.offsetTop;
    return [
      firstSceneTop,
      firstSceneTop + portrait.offsetHeight,
      city.offsetTop,
      fourth.offsetTop,
      fifth.offsetTop,
    ];
  };

  const coarsePointer = window.matchMedia("(pointer: coarse)").matches;

  const moveToAnchor = (nearest) => {
    const current = window.scrollY;
    if (Math.abs(nearest - current) < 24) return;
    isSettling = true;
    window.scrollTo({ top: nearest, behavior: "smooth" });
    window.clearTimeout(releaseTimer);
    releaseTimer = window.setTimeout(() => {
      isSettling = false;
    }, 520);
  };

  const settleToScene = () => {
    if (isSettling || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const current = window.scrollY;
    const anchors = getAnchors();
    const nearest = anchors.reduce((best, target) => (
      Math.abs(target - current) < Math.abs(best - current) ? target : best
    ), anchors[0]);
    moveToAnchor(nearest);
  };

  const scheduleSettle = () => {
    if (isSettling) return;
    window.clearTimeout(settleTimer);
    settleTimer = window.setTimeout(settleToScene, 180);
  };

  if (coarsePointer) {
    // Inertia continues after touchend. Wait for the final scroll event (or
    // scrollend where available) before making one small correction.
    const scheduleTouchSettle = (delay = 160) => {
      if (isSettling) return;
      window.clearTimeout(settleTimer);
      settleTimer = window.setTimeout(settleToScene, delay);
    };

    window.addEventListener("scroll", () => scheduleTouchSettle(), { passive: true });
    window.addEventListener("touchend", () => scheduleTouchSettle(220), { passive: true });
    if ("onscrollend" in window) {
      window.addEventListener("scrollend", settleToScene, { passive: true });
    }
    window.addEventListener("resize", () => {
      window.clearTimeout(settleTimer);
    });
    return;
  }

  window.addEventListener("scroll", scheduleSettle, { passive: true });
  window.addEventListener("wheel", (event) => {
    if (window.matchMedia("(pointer: coarse)").matches || Math.abs(event.deltaY) < 4) return;
    const anchors = getAnchors();
    const current = window.scrollY;
    const insideJourney = current >= anchors[0] - 4 && current <= anchors.at(-1) + window.innerHeight - 4;
    if (!insideJourney || wheelLocked || isSettling) return;

    const activeIndex = anchors.reduce((index, target, currentIndex) => (
      target <= current + window.innerHeight * 0.22 ? currentIndex : index
    ), 0);
    const nextIndex = clamp(activeIndex + (event.deltaY > 0 ? 1 : -1), 0, anchors.length - 1);
    if (nextIndex === activeIndex) return;

    event.preventDefault();
    wheelLocked = true;
    moveToAnchor(anchors[nextIndex]);
    window.setTimeout(() => {
      wheelLocked = false;
    }, 620);
  }, { passive: false });
  window.addEventListener("resize", () => {
    window.clearTimeout(settleTimer);
  });
}

function setupPortraitScan() {
  const portrait = document.querySelector("[data-portrait-wrap]");
  if (!portrait || window.matchMedia("(pointer: coarse)").matches) return;
  portrait.addEventListener("pointermove", (event) => {
    const rect = portrait.getBoundingClientRect();
    const x = ((event.clientX - rect.left) / rect.width) * 100;
    const y = ((event.clientY - rect.top) / rect.height) * 100;
    portrait.style.setProperty("--mx", `${clamp(x, 0, 100)}%`);
    portrait.style.setProperty("--my", `${clamp(y, 0, 100)}%`);
    portrait.classList.add("is-scanning");
  });
  portrait.addEventListener("pointerleave", () => {
    portrait.classList.remove("is-scanning");
  });
}

function setupCityDataScene() {
  const scene = document.querySelector(".scene-city-data");
  const video = document.querySelector(".city-data-video");
  if (!scene || !video) return;

  const heading = scene.querySelector(".city-data-heading");
  const nodes = Array.from(scene.querySelectorAll(".city-data-node"));
  const revealPoints = [0.48, 0.58, 0.69, 0.53, 0.65, 0.76];
  const firstFrameHoldMs = 900;
  let completed = false;
  let hasExited = false;
  let startTimer = 0;

  const reset = () => {
    completed = false;
    window.clearTimeout(startTimer);
    scene.classList.remove("is-data-ready");
    heading?.classList.remove("is-visible");
    nodes.forEach((node) => node.classList.remove("is-visible"));
    video.pause();
    if (video.readyState > 0) video.currentTime = 0;
  };

  const syncReveal = () => {
    const duration = Number.isFinite(video.duration) ? video.duration : 0;
    if (!duration) return;
    const progress = clamp(video.currentTime / duration, 0, 1);
    heading?.classList.toggle("is-visible", progress >= 0.43);
    nodes.forEach((node, index) => {
      node.classList.toggle("is-visible", progress >= (revealPoints[index] || 0.8));
    });
  };

  video.loop = false;
  video.muted = true;
  video.playsInline = true;
  video.addEventListener("timeupdate", syncReveal);
  video.addEventListener("ended", () => {
    completed = true;
    scene.classList.add("is-data-ready");
    heading?.classList.add("is-visible");
    nodes.forEach((node) => node.classList.add("is-visible"));
    video.pause();
  });

  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting && entry.intersectionRatio > 0.55) {
        if (hasExited) reset();
        hasExited = false;
        if (!completed) {
          window.clearTimeout(startTimer);
          startTimer = window.setTimeout(() => {
            if (hasExited || completed) return;
            const playPromise = video.play();
            if (playPromise && typeof playPromise.catch === "function") playPromise.catch(() => {});
          }, firstFrameHoldMs);
        }
        return;
      }
      if (!entry.isIntersecting) {
        hasExited = true;
        window.clearTimeout(startTimer);
        video.pause();
      }
    });
  }, { threshold: [0, 0.55, 0.8] });
  observer.observe(scene);
}

function setupFourthVideoScene() {
  const scene = document.querySelector(".scene-fourth");
  const video = document.querySelector(".fourth-video");
  if (!scene || !video) return;

  let completed = false;
  let hasExited = false;
  let startTimer = 0;
  const firstFrameHoldMs = 1050;

  const reset = () => {
    completed = false;
    window.clearTimeout(startTimer);
    video.pause();
    if (video.readyState > 0) video.currentTime = 0;
  };

  video.loop = false;
  video.muted = true;
  video.playsInline = true;
  video.addEventListener("ended", () => {
    completed = true;
    video.pause();
  });

  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting && entry.intersectionRatio > 0.55) {
        if (hasExited) reset();
        hasExited = false;
        if (!completed) {
          window.clearTimeout(startTimer);
          startTimer = window.setTimeout(() => {
            if (hasExited || completed) return;
            const playPromise = video.play();
            if (playPromise && typeof playPromise.catch === "function") playPromise.catch(() => {});
          }, firstFrameHoldMs);
        }
        return;
      }
      if (!entry.isIntersecting) {
        hasExited = true;
        window.clearTimeout(startTimer);
        video.pause();
      }
    });
  }, { threshold: [0, 0.55, 0.8] });
  observer.observe(scene);
}

function setupFourthClientWall() {
  const scene = document.querySelector(".scene-fourth");
  const video = document.querySelector(".fourth-video");
  const leftZone = document.querySelector('[data-fourth-clients="left"]');
  const rightZone = document.querySelector('[data-fourth-clients="right"]');
  if (!scene || !video || !leftZone || !rightZone) return;

  const revealAtProgress = 0.53;
  const isMobile = window.matchMedia("(max-width: 900px), (pointer: coarse)").matches;
  let wallLoaded = false;
  let loading = false;

  const createLogo = (client) => {
    const item = document.createElement("span");
    item.className = "fourth-client-logo";

    const label = document.createElement("small");
    label.textContent = client.name;
    const textLogo = document.createElement("strong");
    textLogo.textContent = client.name;

    const renderTextLogo = () => {
      item.classList.add("is-text-only");
      item.replaceChildren(textLogo, label);
    };

    if (client.logo) {
      const image = document.createElement("img");
      image.src = client.logo;
      image.alt = "";
      image.loading = isMobile ? "lazy" : "eager";
      image.decoding = "async";
      image.addEventListener("error", () => {
        renderTextLogo();
      }, { once: true });
      item.prepend(image);
      item.append(label);
    } else {
      renderTextLogo();
    }
    return item;
  };

  const renderTrack = (zone, items) => {
    const createTrack = (source, secondary = false) => {
      const track = document.createElement("div");
      track.className = `fourth-client-track${secondary ? " fourth-client-track--secondary" : ""}`;
      // A second identical cycle lets the marquee cross its reset point without a visible jump.
      [...source, ...source].forEach((client) => track.append(createLogo(client)));
      return track;
    };
    const rowCount = 5;
    const rows = Array.from({ length: rowCount }, () => []);
    items.forEach((client, index) => rows[index % rowCount].push(client));
    zone.replaceChildren(...rows.map((row, index) => createTrack(row, index % 2 === 1)));
  };

  const load = async () => {
    if (loading || wallLoaded) return;
    loading = true;
    try {
      const [clientsResponse, manifestResponse] = await Promise.all([
        fetch("./api/clients.json", { cache: "no-store" }),
        fetch("./assets/client-logos/manifest.json", { cache: "no-store" }).catch(() => null),
      ]);
      if (!clientsResponse.ok) throw new Error(`clients ${clientsResponse.status}`);
      const payload = await clientsResponse.json();
      const manifest = manifestResponse?.ok ? await manifestResponse.json() : {};
      const items = (payload.items || [])
        .filter((client) => client?.name)
        .sort((a, b) => (a.order || 0) - (b.order || 0))
        .map((client) => ({ ...client, logo: manifest[client.name] || client.logo || "" }));
      if (!items.length) return;
      renderTrack(leftZone, items.filter((_, index) => index % 2 === 0));
      renderTrack(rightZone, items.filter((_, index) => index % 2 === 1));
      wallLoaded = true;
      const duration = Number.isFinite(video.duration) ? video.duration : 0;
      if (duration && video.currentTime / duration >= revealAtProgress) {
        scene.classList.add("is-clients-ready");
      }
    } catch (error) {
      console.warn("Client wall unavailable", error);
    } finally {
      loading = false;
    }
  };

  // Desktop can decode the client wall before the scene. On mobile, defer it
  // until the video is already playing to avoid competing with first render.
  if (!isMobile) {
    const preloadObserver = new IntersectionObserver((entries) => {
      if (!entries.some((entry) => entry.isIntersecting)) return;
      load();
      preloadObserver.disconnect();
    }, { rootMargin: "65% 0px", threshold: 0.01 });
    preloadObserver.observe(scene);
  }

  video.addEventListener("timeupdate", () => {
    const duration = Number.isFinite(video.duration) ? video.duration : 0;
    if (!duration) return;
    const progress = clamp(video.currentTime / duration, 0, 1);
    if (progress < revealAtProgress) {
      scene.classList.remove("is-clients-ready");
      return;
    }
    if (!wallLoaded) load();
    else scene.classList.add("is-clients-ready");
  });
}

function setupFifthVideoScene() {
  const scene = document.querySelector(".scene-fifth");
  const video = document.querySelector(".fifth-video");
  if (!scene || !video) return;

  let completed = false;
  let hasExited = false;
  let startTimer = 0;
  const firstFrameHoldMs = 1050;

  const reset = () => {
    completed = false;
    scene.classList.remove("is-fifth-complete");
    window.clearTimeout(startTimer);
    video.pause();
    if (video.readyState > 0) video.currentTime = 0;
  };

  video.loop = false;
  video.muted = true;
  video.playsInline = true;
  const revealReturnHome = () => {
    if (completed) return;
    completed = true;
    video.pause();
    scene.classList.add("is-fifth-complete");
  };
  video.addEventListener("ended", () => {
    revealReturnHome();
  });
  video.addEventListener("timeupdate", () => {
    if (!Number.isFinite(video.duration) || video.duration <= 0) return;
    if (video.currentTime / video.duration >= 0.992) revealReturnHome();
  });

  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting && entry.intersectionRatio > 0.55) {
        if (hasExited) reset();
        hasExited = false;
        if (!completed) {
          window.clearTimeout(startTimer);
          startTimer = window.setTimeout(() => {
            if (hasExited || completed) return;
            const playPromise = video.play();
            if (playPromise && typeof playPromise.catch === "function") playPromise.catch(() => {});
          }, firstFrameHoldMs);
        }
        return;
      }
      if (!entry.isIntersecting) {
        hasExited = true;
        window.clearTimeout(startTimer);
        video.pause();
      }
    });
  }, { threshold: [0, 0.55, 0.8] });
  observer.observe(scene);
}

async function loadProjects() {
  try {
    const response = await fetch("./api/portfolio.json", { cache: "no-store" });
    if (!response.ok) throw new Error(`portfolio ${response.status}`);
    const payload = await response.json();
    const items = Array.isArray(payload.items) ? payload.items : [];
    return items
      .filter((item) => item.cover || item.images?.[0])
      .filter((item) => item.featured || item.category === "政企展厅")
      .slice(0, 12)
      .map((item) => ({
        title: item.title || "未命名项目",
        cover: item.cover || item.images?.[0],
      }));
  } catch (error) {
    console.warn("Using journey fallback projects", error);
    return fallbackProjects;
  }
}

function renderProjectMatrix(projects) {
  const matrix = document.querySelector("[data-work-matrix]");
  if (!matrix) return;
  matrix.innerHTML = projects
    .map(
      (project) => `
        <a class="work-card" href="./home.html#projects">
          <img src="${project.cover}" alt="" loading="lazy" draggable="false" />
          <span>${project.title}</span>
        </a>
      `,
    )
    .join("");
}

function setupScrollAnimation() {
  if (window.matchMedia("(pointer: coarse)").matches) return;
  const portraitWrap = document.querySelector(".portrait-wrap");
  const portraitLeft = document.querySelector(".portrait-left");
  const portraitRight = document.querySelector(".portrait-right");
  const wirePerson = document.querySelector(".wire-person");
  const wand = document.querySelector(".wand");
  const tools = document.querySelectorAll(".tool-orbit span");
  const cards = document.querySelectorAll(".work-card");

  const animateFallback = () => {
    const p = state.progress;
    const portraitExit = clamp(p * 3.2, 0, 1);
    if (portraitLeft && portraitRight) {
      const split = clamp(portraitExit * 42, 0, 42);
      portraitLeft.style.transform = `translateX(${-split}px)`;
      portraitRight.style.transform = `translateX(${split}px)`;
    }
    if (portraitWrap) {
      portraitWrap.style.opacity = String(clamp(1 - (p - 0.08) * 2.4, 0.28, 1));
      portraitWrap.style.filter = `grayscale(${clamp((p - 0.05) * 1.6, 0, 1)}) contrast(${1.04 + portraitExit * 0.25})`;
      portraitWrap.style.transform = `translateY(${-portraitExit * 26}px) scale(${1 - portraitExit * 0.035})`;
    }
    if (wirePerson) {
      const emerge = clamp((p - 0.18) * 4.4, 0, 1);
      wirePerson.style.opacity = String(0.18 + emerge * 0.82);
      wirePerson.style.transform = `translateY(${(1 - emerge) * 46}px) scale(${0.88 + emerge * 0.12})`;
    }
    if (wand) {
      const swing = Math.sin(p * Math.PI * 8) * 8;
      wand.style.transform = `rotate(${-18 + swing}deg)`;
    }
    tools.forEach((tool, index) => {
      const emerge = clamp((p - 0.2) * 4.2, 0, 1);
      const angle = p * 220 + index * 19;
      const pulse = Math.sin(p * 5 + index) * 10;
      tool.style.opacity = String(clamp(emerge - index * 0.018, 0.25, 1));
      tool.style.transform = `rotate(${angle}deg) translateY(${pulse}px) scale(${0.82 + emerge * 0.18})`;
    });
    cards.forEach((card, index) => {
      const drift = Math.sin(p * 7 + index) * 10;
      card.style.transform = `translateY(${drift}px)`;
    });
  };

  window.addEventListener("scroll", () => {
    updateProgress();
    animateFallback();
  }, { passive: true });
  window.addEventListener("resize", updateProgress);
  updateProgress();
  animateFallback();
}

async function setupThree() {
  const canvas = document.querySelector("#journey-canvas");
  const desktopEffects = window.matchMedia("(min-width: 901px) and (hover: hover) and (pointer: fine)").matches;
  if (!canvas || !desktopEffects || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  let THREE;
  try {
    THREE = await import("https://esm.sh/three@0.160.0");
  } catch (error) {
    console.warn("Three.js unavailable; using CSS-only preview.", error);
    return;
  }

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(55, window.innerWidth / window.innerHeight, 0.1, 100);
  camera.position.set(0, 0, 7.2);

  const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.7));
  renderer.setSize(window.innerWidth, window.innerHeight);

  const textureLoader = new THREE.TextureLoader();
  const portraitTexture = textureLoader.load("./assets/portrait-creative-management.png");
  portraitTexture.colorSpace = THREE.SRGBColorSpace;

  const leftMat = new THREE.MeshBasicMaterial({ map: portraitTexture, transparent: true, opacity: 0.16, side: THREE.DoubleSide });
  const rightMat = leftMat.clone();
  const planeGeo = new THREE.PlaneGeometry(1.8, 2.7);
  const leftPlane = new THREE.Mesh(planeGeo, leftMat);
  const rightPlane = new THREE.Mesh(planeGeo, rightMat);
  leftPlane.position.set(-0.48, 0, -0.4);
  rightPlane.position.set(0.48, 0, -0.4);

  const portraitGroup = new THREE.Group();
  portraitGroup.add(leftPlane, rightPlane);
  scene.add(portraitGroup);

  const pointGeo = new THREE.BufferGeometry();
  const count = 760;
  const positions = new Float32Array(count * 3);
  for (let i = 0; i < count; i += 1) {
    positions[i * 3] = (Math.random() - 0.5) * 12;
    positions[i * 3 + 1] = (Math.random() - 0.5) * 7;
    positions[i * 3 + 2] = (Math.random() - 0.5) * 8;
  }
  pointGeo.setAttribute("position", new THREE.BufferAttribute(positions, 3));
  const particles = new THREE.Points(
    pointGeo,
    new THREE.PointsMaterial({
      color: 0xff6a00,
      size: 0.022,
      transparent: true,
      opacity: 0.7,
    }),
  );
  scene.add(particles);

  const dotGeo = new THREE.SphereGeometry(0.08, 24, 24);
  const dotMat = new THREE.MeshBasicMaterial({ color: 0xff6a00 });
  const dots = [new THREE.Mesh(dotGeo, dotMat), new THREE.Mesh(dotGeo, dotMat.clone())];
  dots[0].position.set(-2.1, 0.25, 0);
  dots[1].position.set(2.1, -0.25, 0);
  dots.forEach((dot) => scene.add(dot));

  state.threeReady = true;
  Object.assign(state, { scene, camera, renderer, portraitGroup, particles, dots });

  window.addEventListener("resize", () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
  });

  function tick() {
    const time = performance.now() * 0.001;
    particles.rotation.y = time * 0.025 + state.progress * 1.6;
    particles.rotation.x = Math.sin(time * 0.2) * 0.08;
    dots.forEach((dot, index) => {
      dot.scale.setScalar(1 + Math.sin(time * 2 + index) * 0.16);
    });
    renderer.render(scene, camera);
    requestAnimationFrame(tick);
  }
  tick();
}

function updateThreeScene(progress) {
  const { camera, portraitGroup, particles, dots } = state;
  if (!camera || !portraitGroup || !particles || !dots.length) return;
  camera.position.z = 7.2 - progress * 2.5;
  camera.position.x = Math.sin(progress * Math.PI * 1.2) * 1.15;
  camera.position.y = (0.5 - progress) * 0.6;
  camera.lookAt(0, 0, 0);
  portraitGroup.position.x = (progress - 0.22) * -3.2;
  portraitGroup.rotation.y = progress * -0.42;
  portraitGroup.children[0].position.x = -0.48 - clamp((progress - 0.16) * 2.8, 0, 1.35);
  portraitGroup.children[1].position.x = 0.48 + clamp((progress - 0.16) * 2.8, 0, 1.35);
  particles.material.opacity = clamp(0.85 - progress * 0.22, 0.38, 0.85);
  dots[0].position.x = -2.1 + progress * 1.72;
  dots[1].position.x = 2.1 - progress * 1.72;
  dots[0].position.y = 0.25 - progress * 0.18;
  dots[1].position.y = -0.25 + progress * 0.18;
}

async function boot() {
  setupHeroVideoIntro();
  setupDeferredVideoLoading();
  setupHeaderNav();
  setupBrandNavigation();
  setupTheme();
  setupGlobalCursorAura();
  setupCinematicTransition();
  setupSceneSnap();
  setupPortraitScan();
  setupCityDataScene();
  setupFourthVideoScene();
  setupFourthClientWall();
  setupFifthVideoScene();
  setupScrollAnimation();
  setupThree();
}

boot();
