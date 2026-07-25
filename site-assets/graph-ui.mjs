import { esc } from "./graph-core.mjs";

export function injectStyles() {
  if (document.getElementById("graph-controller-styles")) return;
  const style = document.createElement("style");
  style.id = "graph-controller-styles";
  style.textContent = `
    .graph-share-status{min-width:4.4rem;color:#93a4b8;font-size:.72rem;align-self:center}
    .graph-pathfinder{margin:.7rem 0;border:1px solid #29415e;border-radius:12px;background:#091727;overflow:hidden}
    .graph-pathfinder summary{cursor:pointer;padding:.7rem .85rem;color:#e2e8f0;font-weight:700;list-style:none}
    .graph-pathfinder summary::-webkit-details-marker{display:none}
    .graph-pathfinder summary::after{content:"▾";float:right;color:#7dd3fc}
    .graph-pathfinder[open] summary{border-bottom:1px solid #29415e}
    .graph-path-body{padding:.8rem}.graph-path-inputs{display:grid;grid-template-columns:minmax(0,1fr) auto minmax(0,1fr);gap:.55rem;align-items:end}
    .graph-path-inputs label{display:grid;gap:.25rem;color:#93a4b8;font-size:.72rem;text-transform:uppercase;letter-spacing:.06em}
    .graph-path-inputs input{min-width:0;width:100%;border:1px solid #29415e;border-radius:8px;background:#07111f;color:#f8fafc;padding:.62rem .7rem}
    .graph-path-arrow{padding-bottom:.58rem;color:#38bdf8;font-weight:800}.graph-path-actions{display:flex;gap:.5rem;flex-wrap:wrap;margin:.65rem 0 0}
    .graph-path-actions button,.graph-path-result{border:1px solid #29415e;border-radius:8px;background:#10233a;color:#e2e8f0;padding:.52rem .7rem;cursor:pointer}
    .graph-path-actions button:hover,.graph-path-result:hover{border-color:#6b8db3;background:#17304e}.graph-path-results{display:grid;gap:.45rem;margin-top:.7rem}
    .graph-path-result{display:grid;gap:.28rem;text-align:left;width:100%}.graph-path-result[aria-pressed="true"]{border-color:#38bdf8;background:#0c4a6e88;box-shadow:0 0 0 1px #38bdf855 inset}
    .graph-path-result strong{color:#fff}.graph-path-result span{color:#93a4b8;font-size:.75rem}.graph-path-trail{display:flex;gap:.28rem;align-items:center;flex-wrap:wrap;line-height:1.3}
    .graph-path-trail b{font-weight:600;color:#dbeafe}.graph-path-trail i{font-style:normal;color:#7dd3fc;font-size:.72rem}.graph-path-empty{margin:.5rem 0 0;color:#93a4b8;font-size:.82rem}
    .graph-endpoint{display:inline-flex;gap:.35rem;align-items:center;border:1px solid #29415e;border-radius:999px;padding:.22rem .52rem;background:#07111f;color:#cbd5e1;font-size:.75rem}
    .graph-detail-actions{grid-template-columns:1fr 1fr}
    @media(max-width:700px){.graph-path-inputs{grid-template-columns:1fr}.graph-path-arrow{display:none}.graph-path-actions button{flex:1 1 7rem}}
  `;
  document.head.appendChild(style);
}

export function buildUI(canvas, detail) {
  injectStyles();
  const controls = canvas.closest("section")?.querySelector(".controls") || canvas.parentElement;
  const shell = canvas.closest("#graph-shell");
  const layout = document.createElement("select");
  layout.id = "graph-layout"; layout.title = "Topology layout";
  layout.innerHTML = [["force","Force"],["hierarchical","Hierarchy"],["radial","Radial"],["concentric","Concentric"],["grid","Type grid"]]
    .map(([value, label]) => `<option value="${value}">${label}</option>`).join("");
  const labels = document.createElement("label"); labels.className = "graph-toggle";
  labels.innerHTML = '<input id="graph-edge-labels" type="checkbox"> Relations';
  const focus = Object.assign(document.createElement("button"), { type: "button", id: "graph-focus", textContent: "Focus", title: "Show selected node and direct relationships" });
  const all = Object.assign(document.createElement("button"), { type: "button", id: "graph-all", textContent: "All", title: "Show the full graph" });
  const share = Object.assign(document.createElement("button"), { type: "button", id: "graph-share", textContent: "Share view", title: "Copy a link to the exact graph state" });
  const status = document.createElement("span"); status.className = "graph-share-status"; status.setAttribute("aria-live", "polite");
  controls?.append(layout, labels, focus, all, share, status);

  const legend = document.createElement("div"); legend.id = "graph-legend"; legend.className = "graph-legend"; shell?.insertAdjacentElement("beforebegin", legend);
  const help = document.createElement("div"); help.className = "graph-help"; help.textContent = "Drag nodes · pan empty space · pinch/wheel to zoom · select two nodes for a path · double-click to open"; legend.insertAdjacentElement("afterend", help);
  const path = document.createElement("details"); path.className = "graph-pathfinder";
  path.innerHTML = `<summary>Connection finder</summary><div class="graph-path-body"><div class="graph-path-inputs">
    <label>Start node<input id="graph-path-start" list="graph-node-options" placeholder="Select a node or paste an ID"></label><span class="graph-path-arrow">→</span>
    <label>End node<input id="graph-path-end" list="graph-node-options" placeholder="Select a node or paste an ID"></label></div><datalist id="graph-node-options"></datalist>
    <div class="graph-path-actions"><button type="button" data-path-action="selected">Use two selected</button><button type="button" data-path-action="find">Find paths</button>
    <button type="button" data-path-action="clear">Clear path</button><button type="button" data-path-action="copy">Copy path link</button></div><div id="graph-path-results" class="graph-path-results"></div></div>`;
  shell?.insertAdjacentElement("beforebegin", path);
  return {
    detail, layout, labels: labels.querySelector("input"), focus, all, share, status, legend, help, path,
    pathStart: path.querySelector("#graph-path-start"), pathEnd: path.querySelector("#graph-path-end"),
    pathResults: path.querySelector("#graph-path-results"), nodeOptions: path.querySelector("#graph-node-options")
  };
}

export function populateNodeOptions(ui, nodes) {
  ui.nodeOptions.innerHTML = [...nodes].sort((a,b) => (a.label || a.id).localeCompare(b.label || b.id))
    .map((node) => `<option value="${esc(node.id)}" label="${esc(node.label || node.id)} · ${esc(node.group || "entity")}"></option>`).join("");
}

export function renderLegend(ui, nodes) {
  const counts = new Map();
  nodes.filter((node) => node.visible).forEach((node) => {
    const item = counts.get(node.group) || { count: 0, color: node.color, shape: node.shape };
    item.count += 1; counts.set(node.group, item);
  });
  ui.legend.innerHTML = [...counts.entries()].sort(([a],[b]) => a.localeCompare(b)).map(([group,item]) =>
    `<button type="button" class="graph-legend-item" data-group="${esc(group)}"><span class="graph-legend-shape graph-shape-${esc(item.shape)}" style="--node-color:${esc(item.color)}"></span><span>${esc(group.replaceAll("-"," "))}</span><strong>${item.count}</strong></button>`
  ).join("");
}

export function renderDetail(ui, node, state, incidentEdges) {
  if (!node) { ui.detail.innerHTML = '<h3>Graph explorer</h3><p>Select a node to inspect relationships, set path endpoints, or open its record.</p>'; return; }
  const rows = incidentEdges(node).sort((a,b) => (a.label || "").localeCompare(b.label || "")).slice(0,80).map((edge) => {
    const outgoing = edge.a === node, neighbor = outgoing ? edge.b : edge.a;
    return `<li><button type="button" data-node-id="${esc(neighbor.id)}"><span>${outgoing ? "→" : "←"} ${esc(edge.label || "related")}</span><strong>${esc(neighbor.label || neighbor.id)}</strong></button></li>`;
  }).join("");
  const endpoint = `${state.pathStart === node.id ? '<span class="graph-endpoint">Path start</span>' : ""}${state.pathEnd === node.id ? '<span class="graph-endpoint">Path end</span>' : ""}`;
  ui.detail.innerHTML = `<div class="graph-detail-heading"><span class="graph-detail-swatch" style="--node-color:${esc(node.color)}"></span><div><span>${esc((node.group || "entity").replaceAll("-"," "))}</span><h3>${esc(node.label || node.id)}</h3>${endpoint}</div></div>
    <p><code>${esc(node.id)}</code></p><p>${esc(node.detail || "No summary attached.")}</p><div class="graph-detail-stats"><span><strong>${node.degree}</strong> links</span><span><strong>${state.selected.size}</strong> selected</span></div>
    <div class="graph-detail-actions"><button type="button" data-action="path-start">Set path start</button><button type="button" data-action="path-end">Set path end</button><button type="button" data-action="focus-1">Focus 1 hop</button><button type="button" data-action="focus-2">Focus 2 hops</button><button type="button" data-action="pin">${node.pinned ? "Unpin" : "Pin"}</button><button type="button" data-action="show-all">Show all</button></div>
    ${node.href ? `<p><a class="graph-open-record" href="${esc(node.href)}">Open record →</a></p>` : ""}<h4>Relationships</h4><ul class="graph-relations">${rows}</ul>`;
}

export function renderPaths(ui, paths, active, nodeMap, start, end) {
  if (!start || !end) { ui.pathResults.innerHTML = '<p class="graph-path-empty">Choose a start and end node, or Shift-click two graph nodes.</p>'; return; }
  if (!paths.length) { ui.pathResults.innerHTML = '<p class="graph-path-empty">No path found within nine hops.</p>'; return; }
  ui.pathResults.innerHTML = paths.map((path,index) => {
    const trail = path.nodes.map((id,i) => {
      const label = esc(nodeMap.get(id)?.label || id);
      if (i === path.nodes.length - 1) return `<b>${label}</b>`;
      const edge = path.edges[i]; return `<b>${label}</b><i>${edge.reverse ? "←" : "→"} ${esc(edge.label || "related")}</i>`;
    }).join("");
    return `<button type="button" class="graph-path-result" data-path-index="${index}" aria-pressed="${index === active}"><strong>Route ${index + 1}: ${path.edges.length} hop${path.edges.length === 1 ? "" : "s"}</strong><span>relationship cost ${path.cost.toFixed(2)}</span><span class="graph-path-trail">${trail}</span></button>`;
  }).join("");
}
