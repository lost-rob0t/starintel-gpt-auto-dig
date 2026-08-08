(() => {
  "use strict";

  const RESEARCH_URL = "https://auto-research.starintel.actor/";

  function addLink(nav, label, url, siblingSite = "") {
    const link = document.createElement("a");
    link.href = url;
    link.textContent = label;
    if (siblingSite) link.dataset.siblingSite = siblingSite;
    nav.appendChild(link);
  }

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
    const localLinks = [...nav.querySelectorAll(":scope > a")]
      .map((link) => ({ label: link.textContent.trim(), href: link.getAttribute("href") || "" }))
      .filter((link) => link.label !== "Research" && link.href !== `${prefix}index.html`);

    nav.replaceChildren();
    addLink(nav, "Dashboard", `${prefix}index.html`);
    addLink(nav, "Datasets", `${prefix}datasets.html`);
    addLink(nav, "Research ↗", RESEARCH_URL, "research");

    if (localLinks.length) {
      const divider = document.createElement("span");
      divider.className = "local-nav-divider";
      divider.setAttribute("aria-hidden", "true");
      nav.appendChild(divider);
      localLinks.forEach((link) => addLink(nav, link.label === "Dashboard" ? "Dataset" : link.label, link.href));
    }
    if (picker) nav.appendChild(picker);
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", mount, { once: true });
  else mount();
})();
