(() => {
  if (window.__NOIRI_SITE_INIT__) return;
  window.__NOIRI_SITE_INIT__ = true;

  function isActivationKey(event) {
    return event.key === "Enter" || event.key === " ";
  }

  function setMenuState(header, open) {
    const toggle = header.querySelector(".framer-MhXte");
    header.classList.toggle("framer-v-jmkeqr", !open);
    header.classList.toggle("framer-v-130jrpj", open);
    header.dataset.framerName = open ? "Responsive Open" : "Responsive Close";
    header.setAttribute("aria-expanded", open ? "true" : "false");

    if (toggle) {
      toggle.classList.toggle("framer-v-1t7nb4p", !open);
      toggle.classList.toggle("framer-v-1u3lxb1", open);
      toggle.dataset.framerName = open ? "Open" : "Close";
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
      toggle.setAttribute("role", "button");
      toggle.setAttribute("tabindex", "0");
    }
  }

  function initMobileMenu() {
    const header = document.querySelector(".framer-HW7rs.framer-v-jmkeqr, .framer-HW7rs.framer-v-130jrpj");
    if (!(header instanceof HTMLElement)) return;

    const toggle = header.querySelector(".framer-MhXte");
    if (!(toggle instanceof HTMLElement)) return;

    setMenuState(header, header.classList.contains("framer-v-130jrpj"));

    const onToggle = (event) => {
      if (event.type === "keydown" && !isActivationKey(event)) return;
      event.preventDefault();
      event.stopPropagation();
      setMenuState(header, !header.classList.contains("framer-v-130jrpj"));
    };

    toggle.addEventListener("click", onToggle);
    toggle.addEventListener("keydown", onToggle);

    header.querySelectorAll("nav a").forEach((link) => {
      link.addEventListener("click", () => setMenuState(header, false));
    });
  }

  function getStandaloneNavPrefix() {
    const path = window.location.pathname.replace(/\/index\.html$/u, "/");
    if (/\/projects\/[^/]+\/?$/u.test(path)) return "../../";
    if (/\/(?:about|services|projects|contact|privacy-policy|terms-conditions|404)\/?$/u.test(path)) {
      return "../";
    }
    return "./";
  }

  function getStandaloneNavCurrent() {
    const path = window.location.pathname.replace(/\/index\.html$/u, "/");
    if (/\/about\/?$/u.test(path)) return "about";
    if (/\/services\/?$/u.test(path)) return "services";
    if (/\/projects(?:\/[^/]+)?\/?$/u.test(path)) return "projects";
    if (/\/contact\/?$/u.test(path)) return "contact";
    return "home";
  }

  function initStandaloneNav() {
    if (document.querySelector(".noiri-site-nav")) return;

    const prefix = getStandaloneNavPrefix();
    const current = getStandaloneNavCurrent();
    const links = [
      { id: "home", label: "Home", href: prefix },
      { id: "about", label: "About", href: `${prefix}about/` },
      { id: "services", label: "Services", href: `${prefix}services/` },
      { id: "projects", label: "Projects", href: `${prefix}projects/` },
      { id: "contact", label: "Contact", href: `${prefix}contact/` },
    ];

    const nav = document.createElement("div");
    nav.className = "noiri-site-nav";
    nav.innerHTML = `
      <a class="noiri-site-nav__logo" href="${prefix}">KODAK BLACK</a>
      <nav class="noiri-site-nav__links" aria-label="Primary">
        ${links
          .map(
            (link) => `
              <a class="noiri-site-nav__link${link.id === current ? " is-active" : ""}" href="${link.href}">
                <span>${link.label}</span>
              </a>
            `,
          )
          .join("")}
      </nav>
    `;

    document.body.appendChild(nav);
  }

  function setServiceState(row, open) {
    const panel = row.querySelector(".noiri-service-panel");
    const openClass = row.getAttribute("data-noiri-service-open-class") || "framer-v-14lylx1";

    row.classList.remove("framer-v-776hw8", "framer-v-14lylx1", "framer-v-iivdbu");
    row.classList.add(open ? openClass : "framer-v-776hw8");
    row.classList.toggle("noiri-service-open", open);
    row.setAttribute("aria-expanded", open ? "true" : "false");

    if (panel instanceof HTMLElement) {
      panel.hidden = !open;
      panel.setAttribute("aria-hidden", open ? "false" : "true");
    }
  }

  function initServiceAccordion() {
    const rows = Array.from(document.querySelectorAll("[data-noiri-service-row]"));
    if (!rows.length) return;

    const closeOthers = (current) => {
      rows.forEach((row) => {
        if (row !== current) setServiceState(row, false);
      });
    };

    rows.forEach((row) => {
      setServiceState(row, false);

      const onToggle = (event) => {
        if (event.type === "keydown" && !isActivationKey(event)) return;
        event.preventDefault();
        const next = row.getAttribute("aria-expanded") !== "true";
        closeOthers(row);
        setServiceState(row, next);
      };

      row.addEventListener("click", onToggle);
      row.addEventListener("keydown", onToggle);
    });
  }

  function openLink(url, rel, target) {
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.rel = rel;
    anchor.target = target;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
  }

  function initNestedLinks() {
    document.querySelectorAll("[data-nested-link]").forEach((node) => {
      if (!(node instanceof HTMLElement)) return;

      node.addEventListener("click", (event) => {
        const href = node.getAttribute("href");
        if (!href) return;
        if (/Mac|iPod|iPhone|iPad/u.test(navigator.userAgent) ? event.metaKey : event.ctrlKey) {
          event.preventDefault();
          openLink(href, "", "_blank");
          return;
        }
        if (node.tagName === "A") return;
        event.preventDefault();
        openLink(href, node.getAttribute("rel") || "", node.getAttribute("target") || "");
      });

      node.addEventListener("keydown", (event) => {
        if (!isActivationKey(event)) return;
        const href = node.getAttribute("href");
        if (!href || node.tagName === "A") return;
        event.preventDefault();
        openLink(href, node.getAttribute("rel") || "", node.getAttribute("target") || "");
      });
    });
  }

  function initMotion() {
    const elements = Array.from(document.querySelectorAll("[data-noiri-animate]")).filter(
      (node) => node instanceof HTMLElement,
    );
    if (!elements.length) return;

    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      document.documentElement.classList.remove("noiri-motion-enabled");
      elements.forEach((element) => element.classList.add("noiri-animated"));
      return;
    }

    const inlineGroups = new Map();
    elements.forEach((element) => {
      if (element.dataset.noiriAnimate !== "inline" || !element.parentElement) return;
      const group = inlineGroups.get(element.parentElement) || [];
      group.push(element);
      inlineGroups.set(element.parentElement, group);
    });

    inlineGroups.forEach((group) => {
      group.forEach((element, index) => {
        const existingDelay = parseFloat(element.style.getPropertyValue("--noiri-delay")) || 0;
        element.style.setProperty("--noiri-delay", `${existingDelay + index * 0.04}s`);
      });
    });

    const reveal = (element) => {
      if (element.classList.contains("noiri-animated")) return;
      element.classList.add("noiri-animated");
    };

    if (!("IntersectionObserver" in window)) {
      elements.forEach(reveal);
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          reveal(entry.target);
          observer.unobserve(entry.target);
        });
      },
      {
        rootMargin: "0px 0px -12% 0px",
        threshold: 0.18,
      },
    );

    elements.forEach((element) => observer.observe(element));
  }

  function initProcessAnimation() {
    const section = document.querySelector('section[data-framer-name="Process"]');
    if (!(section instanceof HTMLElement)) return;

    const sticky = section.querySelector('[data-framer-name="Sticky Container"]');
    const nativeCard = sticky?.querySelector('[data-framer-name="First Image"]');
    const nativeImage = nativeCard?.querySelector("img");
    const fill = section.querySelector("#fill-image");
    const steps = ["first-process", "second-process", "third-process", "fourth-process"]
      .map((id) => document.getElementById(id))
      .filter((node) => node instanceof HTMLElement);

    if (
      !(sticky instanceof HTMLElement) ||
      !(nativeCard instanceof HTMLElement) ||
      !(nativeImage instanceof HTMLImageElement) ||
      !(fill instanceof HTMLElement) ||
      steps.length !== 4
    ) {
      return;
    }

    if (sticky.querySelector(".noiri-process-stage")) return;

    const resolveAsset = (path) => new URL(path, document.baseURI).href;
    const introAsset = {
      id: "intro",
      src: new URL(nativeImage.getAttribute("src") || "", document.baseURI).href,
      alt: nativeImage.getAttribute("alt") || "Artistic close-up of hands touching",
    };

    const assets = [
      introAsset,
      {
        id: "discovery",
        src: resolveAsset("./assets/local/gallery/gallery-08.webp"),
        alt: "Cinematic portrait in urban streetwear",
      },
      {
        id: "concepting",
        src: resolveAsset("./assets/local/gallery/gallery-09.webp"),
        alt: "High-end editorial indoor portrait",
      },
      {
        id: "production",
        src: resolveAsset("./assets/local/gallery/gallery-10.webp"),
        alt: "Side profile photography with warm lighting",
      },
      {
        id: "post-production",
        src: resolveAsset("./assets/local/gallery/gallery-11.webp"),
        alt: "Minimalist studio fashion portrait",
      },
      {
        id: "fill",
        src: introAsset.src,
        alt: introAsset.alt,
      },
    ];

    const assetById = new Map(assets.map((asset) => [asset.id, asset]));
    const motionReduced = window.matchMedia("(prefers-reduced-motion: reduce)");

    section.classList.add("noiri-process-ready");
    nativeCard.setAttribute("aria-hidden", "true");

    const stage = document.createElement("div");
    stage.className = "noiri-process-stage";
    stage.setAttribute("aria-hidden", "true");
    stage.innerHTML = `
      <div class="noiri-process-shell">
        <div class="noiri-process-card">
          <div class="noiri-process-face noiri-process-face-front">
            <img class="noiri-process-face-image" alt="" decoding="async" />
          </div>
          <div class="noiri-process-face noiri-process-face-back">
            <img class="noiri-process-face-image" alt="" decoding="async" />
          </div>
        </div>
      </div>
    `;
    sticky.appendChild(stage);

    const shell = stage.querySelector(".noiri-process-shell");
    const card = stage.querySelector(".noiri-process-card");
    const frontImage = stage.querySelector(".noiri-process-face-front img");
    const backImage = stage.querySelector(".noiri-process-face-back img");

    if (
      !(shell instanceof HTMLElement) ||
      !(card instanceof HTMLElement) ||
      !(frontImage instanceof HTMLImageElement) ||
      !(backImage instanceof HTMLImageElement)
    ) {
      stage.remove();
      return;
    }

    let currentAssetId = introAsset.id;
    let pendingAssetId = null;
    let flipTimer = 0;
    let initialized = false;
    let rafId = 0;

    const clamp = (value, min, max) => Math.min(Math.max(value, min), max);
    const mix = (from, to, progress) => from + (to - from) * progress;
    const easeOutExpo = (value) => {
      if (value <= 0) return 0;
      if (value >= 1) return 1;
      return 1 - 2 ** (-10 * value);
    };

    const setFaceImage = (image, asset) => {
      image.src = asset.src;
      image.alt = asset.alt;
    };

    const syncFaces = (assetId) => {
      const asset = assetById.get(assetId);
      if (!asset) return;
      setFaceImage(frontImage, asset);
      setFaceImage(backImage, asset);
      currentAssetId = asset.id;
      stage.dataset.noiriProcessAsset = asset.id;
    };

    const completeFlip = (assetId) => {
      const asset = assetById.get(assetId);
      if (!asset) return;
      syncFaces(asset.id);
      stage.classList.add("noiri-process-no-transition");
      stage.classList.remove("is-flipping");
      void card.offsetWidth;
      stage.classList.remove("noiri-process-no-transition");
      if (pendingAssetId && pendingAssetId !== currentAssetId) {
        const nextAssetId = pendingAssetId;
        pendingAssetId = null;
        flipTo(nextAssetId);
        return;
      }
      pendingAssetId = null;
    };

    const flipTo = (assetId) => {
      if (!assetById.has(assetId)) return;
      if (!initialized || motionReduced.matches) {
        syncFaces(assetId);
        return;
      }
      if (currentAssetId === assetId && !stage.classList.contains("is-flipping")) return;
      if (stage.classList.contains("is-flipping")) {
        pendingAssetId = assetId;
        return;
      }

      const asset = assetById.get(assetId);
      setFaceImage(backImage, asset);
      pendingAssetId = null;
      stage.classList.add("is-flipping");
      window.clearTimeout(flipTimer);
      flipTimer = window.setTimeout(() => completeFlip(assetId), 580);
    };

    const readTop = (element) => element.getBoundingClientRect().top + window.scrollY;

    const measure = () => {
      const viewportHeight = window.innerHeight || document.documentElement.clientHeight || 0;
      const triggerOffset = Math.min(Math.max(viewportHeight * 0.11, 72), 120);
      const firstTrigger = readTop(steps[0]) - triggerOffset;
      const secondTrigger = readTop(steps[1]) - triggerOffset;
      const thirdTrigger = readTop(steps[2]) - triggerOffset;
      const fourthTrigger = readTop(steps[3]) - triggerOffset;
      const fillTrigger = readTop(fill) - triggerOffset;
      const revealLead = clamp((fillTrigger - fourthTrigger) * 0.36, 180, 240);
      const revealStart = fillTrigger - revealLead;
      const revealEnd = fillTrigger + clamp(viewportHeight * 0.35, 260, 420);
      const stickyWidth = sticky.clientWidth;
      const stickyHeight = sticky.clientHeight;
      const smallWidth = Math.min(200, Math.max(128, stickyWidth * 0.26));
      const smallHeight = Math.round(smallWidth * 1.25);

      return {
        fillTrigger,
        firstTrigger,
        secondTrigger,
        thirdTrigger,
        fourthTrigger,
        revealStart,
        revealEnd,
        smallHeight,
        smallWidth,
        stickyHeight,
        stickyWidth,
      };
    };

    const targetAssetId = (scrollY, metrics) => {
      const epsilon = 2;
      if (scrollY >= metrics.revealStart - epsilon) return "fill";
      if (scrollY >= metrics.fourthTrigger - epsilon) return "post-production";
      if (scrollY >= metrics.thirdTrigger - epsilon) return "production";
      if (scrollY >= metrics.secondTrigger - epsilon) return "concepting";
      if (scrollY >= metrics.firstTrigger - epsilon) return "discovery";
      return "intro";
    };

    const applySize = (scrollY, metrics) => {
      const revealRaw = clamp(
        (scrollY - metrics.revealStart) / Math.max(metrics.revealEnd - metrics.revealStart, 1),
        0,
        1,
      );
      const revealProgress = easeOutExpo(revealRaw);
      const width = mix(metrics.smallWidth, metrics.stickyWidth, revealProgress);
      const height = mix(metrics.smallHeight, metrics.stickyHeight, revealProgress);

      shell.style.width = `${width}px`;
      shell.style.height = `${height}px`;
      stage.style.setProperty("--noiri-process-progress", revealProgress.toFixed(4));
      stage.classList.toggle("is-filling", revealProgress > 0.001);
    };

    const update = () => {
      rafId = 0;
      const metrics = measure();
      const scrollY = window.scrollY;
      const assetId = targetAssetId(scrollY, metrics);

      if (!initialized) {
        syncFaces(assetId);
        initialized = true;
      } else if (assetId !== currentAssetId) {
        flipTo(assetId);
      }

      applySize(scrollY, metrics);
    };

    const scheduleUpdate = () => {
      if (rafId) return;
      rafId = window.requestAnimationFrame(update);
    };

    scheduleUpdate();
    window.addEventListener("scroll", scheduleUpdate, { passive: true });
    window.addEventListener("resize", scheduleUpdate);
    motionReduced.addEventListener("change", scheduleUpdate);
  }

  document.addEventListener("DOMContentLoaded", () => {
    initMotion();
    initProcessAnimation();
    initMobileMenu();
    initStandaloneNav();
    initServiceAccordion();
    initNestedLinks();
  });
})();
