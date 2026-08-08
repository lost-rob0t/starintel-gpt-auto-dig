(() => {
  "use strict";

  const RESEARCH_URL = "https://auto-research.starintel.actor/";

  function mount() {
    const header = document.querySelector("header");
    if (!header) return;
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
    const links = [
      ["Dashboard", `${prefix}index.html`, false],
      ["Datasets", `${prefix}datasets.html`, false],
      ["Research ↗", RESEARCH_URL, true]
    ];
    links.forEach(([label, url, external]) => {
      const link = document.createElement("a");
      link.href = url;
      link.textContent = label;
      if (external) link.dataset.siblingSite = "research";
      nav.appendChild(link);
    });
    if (picker) nav.appendChild(picker);
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", mount, { once: true });
  else mount();
})();
