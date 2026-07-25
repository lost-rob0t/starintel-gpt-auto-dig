(() => {
  "use strict";

  const esc = (value) => String(value).replace(/[&<>"']/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  })[char]);

  async function loadJson(path) {
    const response = await fetch(path);
    if (!response.ok) throw new Error(`${path}: ${response.status}`);
    return response.json();
  }

  async function initSearch() {
    const input = document.querySelector("#search-input");
    if (!input) return;

    const results = document.querySelector("#search-results");
    const status = document.querySelector("#search-status");
    const records = await loadJson("search-index.json");

    const render = () => {
      const query = input.value.trim().toLowerCase();
      const matches = records.filter((record) => {
        const haystack = [
          record.title, record.description, record.kind, ...(record.tags || [])
        ].join(" ").toLowerCase();
        return !query || haystack.includes(query);
      }).slice(0, 100);

      status.textContent = `${matches.length} result${matches.length === 1 ? "" : "s"}`;
      results.innerHTML = matches.map((record) =>
        `<li><a href="${encodeURI(record.url)}">${esc(record.title)}</a>` +
        `<span>${esc(record.kind)}</span></li>`
      ).join("");
    };

    input.addEventListener("input", render);
    render();
  }

  async function initGraph() {
    const canvas = document.querySelector("#graph-canvas");
    if (!canvas) return;

    const graph = await loadJson("graph.json");
    const status = document.querySelector("#graph-status");
    const ctx = canvas.getContext("2d");
    const nodes = graph.nodes || [];
    const links = graph.links || [];
    const positions = new Map();

    nodes.forEach((node, index) => {
      const angle = (index / Math.max(nodes.length, 1)) * Math.PI * 2;
      const radius = Math.min(canvas.width, canvas.height) * 0.36;
      positions.set(node.id, {
        x: canvas.width / 2 + Math.cos(angle) * radius,
        y: canvas.height / 2 + Math.sin(angle) * radius,
        node
      });
    });

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.strokeStyle = "#334155";
    links.forEach((link) => {
      const source = positions.get(link.source);
      const target = positions.get(link.target);
      if (!source || !target) return;
      ctx.beginPath();
      ctx.moveTo(source.x, source.y);
      ctx.lineTo(target.x, target.y);
      ctx.stroke();
    });

    ctx.fillStyle = "#7dd3fc";
    positions.forEach((point) => {
      ctx.beginPath();
      ctx.arc(point.x, point.y, 5, 0, Math.PI * 2);
      ctx.fill();
    });

    status.textContent = `${nodes.length} nodes, ${links.length} links`;
    canvas.addEventListener("click", (event) => {
      const rect = canvas.getBoundingClientRect();
      const x = (event.clientX - rect.left) * (canvas.width / rect.width);
      const y = (event.clientY - rect.top) * (canvas.height / rect.height);
      let nearest = null;
      let distance = 18;
      positions.forEach((point) => {
        const candidate = Math.hypot(point.x - x, point.y - y);
        if (candidate < distance) {
          nearest = point;
          distance = candidate;
        }
      });
      if (nearest) window.location.href = encodeURI(nearest.node.url);
    });
  }

  initSearch().catch(console.error);
  initGraph().catch(console.error);
})();
