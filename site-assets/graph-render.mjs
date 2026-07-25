import { TAU, clamp, colorFor } from "./graph-core.mjs";

export class GraphRenderer {
  constructor(canvas, model) {
    this.canvas = canvas;
    this.ctx = canvas.getContext("2d");
    this.model = model;
    this.width = 1; this.height = 1;
    this.colors = {};
  }
  resize() {
    const rect = this.canvas.getBoundingClientRect(), dpr = window.devicePixelRatio || 1;
    this.width = Math.max(1, rect.width); this.height = Math.max(1, rect.height);
    this.canvas.width = Math.max(1, Math.floor(this.width * dpr));
    this.canvas.height = Math.max(1, Math.floor(this.height * dpr));
    this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }
  palette() {
    const style = getComputedStyle(document.documentElement);
    const value = (name, fallback) => style.getPropertyValue(name).trim() || fallback;
    return {
      edge: value("--edge", "#29415e"),
      edgeStrong: value("--edge-strong", "#8ec5ff"),
      edgeArrow: value("--edge-arrow", "#4c6685"),
      edgePath: value("--edge-path", "#fbbf24"),
      labelBackground: value("--label-bg", "#07111f"),
      labelText: value("--label-text", "#f8fafc"),
      labelMuted: value("--label-muted", "#93a4b8"),
      pathLabel: value("--path-label", "#fde68a"),
      selected: value("--accent", "#38bdf8"),
      hover: value("--text", "#e2e8f0"),
      primary: value("--text-strong", "#ffffff"),
      nodeBorder: value("--bg", "#07111f")
    };
  }
  screen(node, view) { return { x: node.x * view.scale + view.pan.x, y: node.y * view.scale + view.pan.y }; }
  world(point, view) { return { x: (point.x - view.pan.x) / view.scale, y: (point.y - view.pan.y) / view.scale }; }
  nearest(point, view) {
    let best = null, distance = 18;
    this.model.visibleNodes().forEach((node) => {
      const p = this.screen(node, view), candidate = Math.hypot(p.x - point.x, p.y - point.y) - node.radius * view.scale;
      if (candidate < distance) { distance = candidate; best = node; }
    });
    return best;
  }
  path(point, node, radius) {
    const ctx = this.ctx; ctx.beginPath();
    if (node.shape === "square") ctx.roundRect(point.x - radius, point.y - radius, radius * 2, radius * 2, radius * .28);
    else if (node.shape === "diamond") { ctx.moveTo(point.x, point.y - radius * 1.25); ctx.lineTo(point.x + radius * 1.1, point.y); ctx.lineTo(point.x, point.y + radius * 1.25); ctx.lineTo(point.x - radius * 1.1, point.y); ctx.closePath(); }
    else if (node.shape === "triangle") { ctx.moveTo(point.x, point.y - radius * 1.25); ctx.lineTo(point.x + radius * 1.12, point.y + radius); ctx.lineTo(point.x - radius * 1.12, point.y + radius); ctx.closePath(); }
    else if (node.shape === "hexagon") { for (let i = 0; i < 6; i += 1) { const a = i / 6 * TAU - Math.PI / 2, x = point.x + Math.cos(a) * radius * 1.15, y = point.y + Math.sin(a) * radius * 1.15; if (!i) ctx.moveTo(x, y); else ctx.lineTo(x, y); } ctx.closePath(); }
    else if (node.shape === "document") ctx.roundRect(point.x - radius * .86, point.y - radius * 1.1, radius * 1.72, radius * 2.2, radius * .18);
    else ctx.arc(point.x, point.y, radius, 0, TAU);
  }
  edge(edge, view, emphasized, pathEdge) {
    const ctx = this.ctx, colors = this.colors, a = this.screen(edge.a, view), b = this.screen(edge.b, view);
    const dx = b.x - a.x, dy = b.y - a.y, distance = Math.hypot(dx, dy) || 1, ux = dx / distance, uy = dy / distance;
    const sx = a.x + ux * (edge.a.radius * view.scale + 2), sy = a.y + uy * (edge.a.radius * view.scale + 2);
    const tx = b.x - ux * (edge.b.radius * view.scale + 7), ty = b.y - uy * (edge.b.radius * view.scale + 7);
    ctx.beginPath(); ctx.moveTo(sx, sy); ctx.lineTo(tx, ty);
    ctx.strokeStyle = pathEdge ? colors.edgePath : emphasized ? colors.edgeStrong : colors.edge;
    ctx.globalAlpha = pathEdge ? 1 : emphasized ? .92 : .42; ctx.lineWidth = pathEdge ? 3 : emphasized ? 1.5 : .8; ctx.stroke();
    const arrow = pathEdge ? 7 : emphasized ? 6 : 4;
    ctx.beginPath(); ctx.moveTo(tx, ty); ctx.lineTo(tx - ux * arrow - uy * arrow * .7, ty - uy * arrow + ux * arrow * .7); ctx.lineTo(tx - ux * arrow + uy * arrow * .7, ty - uy * arrow - ux * arrow * .7); ctx.closePath();
    ctx.fillStyle = pathEdge ? colors.edgePath : emphasized ? colors.edgeStrong : colors.edgeArrow; ctx.fill();
    if (view.edgeLabels || emphasized || pathEdge) {
      const mx = (sx + tx) / 2, my = (sy + ty) / 2, label = edge.label || "related";
      ctx.font = pathEdge ? "600 10px system-ui" : "10px system-ui";
      const metrics = ctx.measureText(label); ctx.globalAlpha = .96; ctx.fillStyle = colors.labelBackground;
      ctx.fillRect(mx - metrics.width / 2 - 4, my - 8, metrics.width + 8, 14);
      ctx.fillStyle = pathEdge ? colors.pathLabel : emphasized ? colors.labelText : colors.labelMuted; ctx.fillText(label, mx - metrics.width / 2, my + 3);
    }
  }
  node(node, view) {
    const ctx = this.ctx, colors = this.colors, point = this.screen(node, view), isPath = view.pathNodes.has(node.id);
    const primary = node === view.primary, selected = view.selected.has(node), hover = node === view.hover;
    const radius = Math.max(4.5, node.radius * clamp(view.scale, .65, 1.3));
    this.path(point, node, radius); ctx.globalAlpha = 1; ctx.fillStyle = colorFor(node.group || "entity", node.color); ctx.fill();
    ctx.strokeStyle = isPath ? colors.edgePath : primary ? colors.primary : selected ? colors.selected : hover ? colors.hover : colors.nodeBorder;
    ctx.lineWidth = isPath ? 4 : primary ? 3 : selected || hover ? 2 : 1.1; ctx.stroke();
    if (isPath || primary || selected || hover || (view.scale > 1.2 && node.degree >= 2)) {
      ctx.font = isPath || primary ? "600 12px system-ui" : "11px system-ui"; ctx.textBaseline = "middle";
      const label = node.label || node.id; let visible = label;
      while (visible.length > 8 && ctx.measureText(`${visible}…`).width > 260) visible = visible.slice(0, -1);
      if (visible !== label) visible += "…";
      const textWidth = ctx.measureText(visible).width, x = point.x + radius + 8, y = point.y;
      ctx.globalAlpha = .95; ctx.fillStyle = colors.labelBackground; ctx.fillRect(x - 3, y - 9, textWidth + 6, 18);
      ctx.fillStyle = isPath ? colors.pathLabel : colors.labelText; ctx.fillText(visible, x, y + .5);
    }
  }
  draw(view) {
    const ctx = this.ctx; this.colors = this.palette(); ctx.clearRect(0, 0, this.width, this.height); ctx.save(); ctx.lineCap = "round";
    const selectedIds = new Set([...view.selected].map((node) => node.id));
    this.model.visibleEdges().forEach((edge) => {
      const pathEdge = view.pathEdges.has(edge.key);
      const emphasized = pathEdge || edge.a === view.hover || edge.b === view.hover || edge.a === view.primary || edge.b === view.primary || (selectedIds.has(edge.a.id) && selectedIds.has(edge.b.id));
      this.edge(edge, view, emphasized, pathEdge);
    });
    ctx.globalAlpha = 1; this.model.visibleNodes().sort((a, b) => a.degree - b.degree).forEach((node) => this.node(node, view)); ctx.restore();
  }
}
