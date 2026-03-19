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

  document.addEventListener("DOMContentLoaded", () => {
    initMotion();
    initMobileMenu();
    initServiceAccordion();
    initNestedLinks();
  });
})();
