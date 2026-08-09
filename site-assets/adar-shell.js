(() => {
  "use strict";

  const RESEARCH_URL = "https://auto-research.starintel.actor/";
  const THEME_KEY = "starintel-theme";
  const DEFAULT_MARKER_KEY = "starintel-black-gold-default-v1";

  const ICONS = Object.freeze({
    Dashboard: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 4h6v6H4zM14 4h6v10h-6zM4 14h6v6H4zM14 18h6v2h-6z"/></svg>',
    Datasets: '<svg viewBox="0 0 24 24" aria-hidden="true"><ellipse cx="12" cy="5" rx="7" ry="3"/><path d="M5 5v5c0 1.7 3.1 3 7 3s7-1.3 7-3V5M5 10v5c0 1.7 3.1 3 7 3s7-1.3 7-3v-5M5 15v4c0 1.7 3.1 3 7 3s7-1.3 7-3v-4"/></svg>',
    Research: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 4h10a2 2 0 0 1 2 2v14H7a2 2 0 0 1-2-2z"/><path d="M17 8h2a2 2 0 0 1 2 2v10h-4M8 8h6M8 12h6M8 16h4"/></svg>',
    Dataset: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 5h16v14H4zM4 9h16M9 9v10"/></svg>',
    Documents: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 3h9l3 3v15H6zM14 3v4h4M9 11h6M9 15h6"/></svg>',
    Graph: '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="6" cy="12" r="2.5"/><circle cx="17" cy="6" r="2.5"/><circle cx="18" cy="18" r="2.5"/><path d="M8.3 10.8 14.7 7M8.5 13.2l7 3.4M17.4 8.5l.4 7"/></svg>',
    Sources: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 4h14v16H5zM8 8h8M8 12h8M8 16h5"/></svg>'
  });

  function icon(label) {
    return ICONS[label] || ICONS.Documents;
  }

  function normalizeLabel(label) {
    return String(label || "").replace(/\s*↗\s*$/, "").trim();
  }

  function styleShell() {
    if (document.getElementById("adar-shell-polish")) return;
    const style = document.createElement("style");
    style.id = "adar-shell-polish";
    style.textContent = `
      header nav > a { display:inline-flex; align-items:center; gap:.42rem; }
      header nav > a svg { width:1rem; height:1rem; flex:0 0 auto; fill:none; stroke:currentColor; stroke-width:1.8; stroke-linecap:round; stroke-linejoin:round; }
      header nav > a[data-nav-icon="Dashboard"] svg path:first-child,
      header nav > a[data-nav-icon="Datasets"] svg ellipse { fill:currentColor; stroke:none; }
      header nav > a[aria-current="page"] { color:var(--text-strong); background:color-mix(in srgb, var(--accent) 14%, transparent); box-shadow:inset 0 -2px 0 var(--accent); }
      .local-nav-divider { width:1px; height:1.5rem; margin:0 .15rem; background:var(--line); }
      @media (max-width:760px) { .local-nav-divider { display:none; } header nav > a { min-height:2.35rem; } }
    `;
    document.head.appendChild(style);
  }

  function applyBlackGoldDefault() {
    try {
      if (!localStorage.getItem(DEFAULT_MARKER_KEY)) {
        const current = localStorage.getItem(THEME_KEY);
        if (!current || current === "midnight") window.StarIntelThemes?.apply("black-gold");
        localStorage.setItem(DEFAULT_MARKER_KEY, "1");
      }
    } catch (_) {
      if (window.StarIntelThemes?.active?.() === "midnight") window.StarIntelThemes.apply("black-gold");
    }
    const picker = document.getElementById("theme-select");
    if (picker && window.StarIntelThemes?.active?.() === "black-gold") picker.value = "black-gold";
  }

  function addLink(nav, label, url, siblingSite = "") {
    const link = document.createElement("a");
    const clean = normalizeLabel(label);
    link.href = url;
    link.dataset.navIcon = clean;
    link.innerHTML = `${icon(clean)}<span>${clean}${siblingSite ? " ↗" : ""}</span>`;
    if (siblingSite) link.dataset.siblingSite = siblingSite;
    const resolved = new URL(link.href, window.location.href);
    if (!siblingSite && resolved.pathname === window.location.pathname && resolved.hash === window.location.hash) {
      link.setAttribute("aria-current", "page");
    }
    nav.appendChild(link);
    return link;
  }

  function parentPrefix(prefix) {
    const depth = (prefix.match(/\.\.\//g) || []).length;
    return depth > 0 ? "../".repeat(depth - 1) : "";
  }

  function mount() {
    const header = document.querySelector("header");
    if (!header) return;
    styleShell();
    applyBlackGoldDefault();

    const brand = header.querySelector(".brand") || header.querySelector("a");
    if (!brand) return;
    brand.textContent = "StarIntel Auto-Dig";
    const href = brand.getAttribute("href") || "index.html";
    const prefix = href.endsWith("index.html") ? href.slice(0, -"index.html".length) : "";
    let nav = header.querySelector("nav");
    if (!nav) {
      nav = document.createElement("nav");
      header.appendChild(nav);
    }

    const picker = nav.querySelector(".theme-picker");
    nav.replaceChildren();
    addLink(nav, "Dashboard", `${prefix}index.html#corpus-dashboard`);
    addLink(nav, "Datasets", `${prefix}datasets.html`);
    addLink(nav, "Research", RESEARCH_URL, "research");

    if (prefix) {
      const local = parentPrefix(prefix);
      const divider = document.createElement("span");
      divider.className = "local-nav-divider";
      divider.setAttribute("aria-hidden", "true");
      nav.appendChild(divider);
      addLink(nav, "Dataset", `${local}index.html`);
      addLink(nav, "Graph", `${local}graph.html`);
      addLink(nav, "Documents", `${local}documents.html`);
      addLink(nav, "Sources", `${local}sources.html`);
    }

    if (picker) nav.appendChild(picker);
    const currentTheme = document.getElementById("theme-select");
    if (currentTheme && window.StarIntelThemes?.active?.() === "black-gold") currentTheme.value = "black-gold";
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", mount, { once: true });
  else mount();
})();
