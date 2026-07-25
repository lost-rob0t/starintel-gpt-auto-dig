import { TAU, clamp, colorFor, shapeFor, edgeKey, seeded } from "./graph-core.mjs";

export class GraphModel {
  constructor(data) {
    const rawNodes = Array.isArray(data.nodes) ? data.nodes : [];
    const rawEdges = Array.isArray(data.edges) ? data.edges : [];
    const degrees = new Map(rawNodes.map((node) => [node.id, 0]));
    rawEdges.forEach((edge) => {
      degrees.set(edge.source, (degrees.get(edge.source) || 0) + 1);
      degrees.set(edge.target, (degrees.get(edge.target) || 0) + 1);
    });
    this.nodes = rawNodes.map((node, index) => {
      const degree = degrees.get(node.id) || 0;
      const angle = index * 2.399963229728653;
      const spread = 28 * Math.sqrt(index + 1);
      return {
        ...node,
        color: colorFor(node.group || "entity", node.color),
        shape: shapeFor(node.group || "entity"),
        x: Math.cos(angle) * spread + (seeded(node.id, "x") - 0.5) * 22,
        y: Math.sin(angle) * spread + (seeded(node.id, "y") - 0.5) * 22,
        vx: 0, vy: 0, tx: 0, ty: 0, degree,
        radius: clamp(6 + Math.sqrt(degree + 1) * 1.6, 7, 18),
        mass: 1 + Math.sqrt(degree + 1) * 0.45,
        visible: true, pinned: false
      };
    });
    this.nodeMap = new Map(this.nodes.map((node) => [node.id, node]));
    this.edges = rawEdges.map((edge) => ({
      ...edge, a: this.nodeMap.get(edge.source), b: this.nodeMap.get(edge.target), key: edgeKey(edge)
    })).filter((edge) => edge.a && edge.b);
    this.layout = "force";
    this.alpha = 1;
  }

  visibleNodes() { return this.nodes.filter((node) => node.visible); }
  visibleEdges() { return this.edges.filter((edge) => edge.a.visible && edge.b.visible); }
  reheat(value = 0.9) { this.alpha = Math.max(this.alpha, value); }

  updateVisibility({ query = "", group = "", focusIds = null, pathIds = new Set() }) {
    const needle = query.trim().toLowerCase();
    this.nodes.forEach((node) => {
      if (pathIds.has(node.id)) { node.visible = true; return; }
      if (group && node.group !== group) { node.visible = false; return; }
      if (focusIds && !focusIds.has(node.id)) { node.visible = false; return; }
      node.visible = !needle || [node.label, node.id, node.detail, node.group]
        .filter(Boolean).some((value) => String(value).toLowerCase().includes(needle));
    });
    this.reheat(1);
  }

  neighborhood(node, depth = 1) {
    const ids = new Set([node.id]);
    let frontier = new Set([node.id]);
    for (let step = 0; step < depth; step += 1) {
      const next = new Set();
      this.edges.forEach((edge) => {
        if (frontier.has(edge.source) && !ids.has(edge.target)) next.add(edge.target);
        if (frontier.has(edge.target) && !ids.has(edge.source)) next.add(edge.source);
      });
      next.forEach((id) => ids.add(id));
      frontier = next;
    }
    return ids;
  }

  levels(active, root) {
    const activeIds = new Set(active.map((node) => node.id));
    const adjacency = new Map(active.map((node) => [node.id, []]));
    this.visibleEdges().forEach((edge) => {
      if (!activeIds.has(edge.a.id) || !activeIds.has(edge.b.id)) return;
      adjacency.get(edge.a.id).push(edge.b);
      adjacency.get(edge.b.id).push(edge.a);
    });
    const levels = new Map();
    const queue = [];
    if (root) { levels.set(root.id, 0); queue.push(root); }
    while (queue.length) {
      const node = queue.shift();
      const level = levels.get(node.id);
      adjacency.get(node.id).forEach((neighbor) => {
        if (levels.has(neighbor.id)) return;
        levels.set(neighbor.id, level + 1);
        queue.push(neighbor);
      });
    }
    let max = Math.max(0, ...levels.values());
    active.forEach((node) => { if (!levels.has(node.id)) levels.set(node.id, ++max); });
    return levels;
  }

  applyLayout(name, primary = null, immediate = false) {
    this.layout = name;
    const active = this.visibleNodes();
    if (!active.length) return;
    const root = primary?.visible ? primary : [...active].sort((a, b) => b.degree - a.degree)[0];
    const levels = this.levels(active, root);
    if (name === "force") active.forEach((node) => { node.tx = 0; node.ty = 0; });
    if (name === "hierarchical") {
      const rows = new Map();
      active.forEach((node) => {
        const level = levels.get(node.id) || 0;
        if (!rows.has(level)) rows.set(level, []);
        rows.get(level).push(node);
      });
      const entries = [...rows.entries()].sort(([a], [b]) => a - b);
      entries.forEach(([level, row]) => {
        row.sort((a, b) => b.degree - a.degree || (a.label || a.id).localeCompare(b.label || b.id));
        row.forEach((node, index) => {
          node.tx = (index - (row.length - 1) / 2) * 125;
          node.ty = (level - (entries.length - 1) / 2) * 160;
        });
      });
    }
    if (name === "radial") {
      const rings = new Map();
      active.forEach((node) => {
        const level = levels.get(node.id) || 0;
        if (!rings.has(level)) rings.set(level, []);
        rings.get(level).push(node);
      });
      [...rings.entries()].forEach(([level, ring]) => {
        ring.sort((a, b) => b.degree - a.degree);
        const radius = level === 0 ? 0 : 125 + (level - 1) * 140;
        ring.forEach((node, index) => {
          const angle = ring.length === 1 ? 0 : index / ring.length * TAU - Math.PI / 2;
          node.tx = Math.cos(angle) * radius; node.ty = Math.sin(angle) * radius;
        });
      });
    }
    if (name === "concentric") {
      const maxDegree = Math.max(1, ...active.map((node) => node.degree));
      const rings = new Map();
      active.forEach((node) => {
        const ring = Math.floor((1 - node.degree / maxDegree) * 4);
        if (!rings.has(ring)) rings.set(ring, []);
        rings.get(ring).push(node);
      });
      [...rings.entries()].forEach(([index, ring]) => {
        const radius = index === 0 ? 0 : 110 + index * 125;
        ring.forEach((node, position) => {
          const angle = ring.length === 1 ? 0 : position / ring.length * TAU - Math.PI / 2;
          node.tx = Math.cos(angle) * radius; node.ty = Math.sin(angle) * radius;
        });
      });
    }
    if (name === "grid") {
      const groups = new Map();
      active.forEach((node) => {
        if (!groups.has(node.group)) groups.set(node.group, []);
        groups.get(node.group).push(node);
      });
      const columns = [...groups.entries()].sort(([a], [b]) => a.localeCompare(b));
      columns.forEach(([, column], x) => {
        column.sort((a, b) => b.degree - a.degree);
        column.forEach((node, y) => {
          node.tx = (x - (columns.length - 1) / 2) * 185;
          node.ty = (y - (column.length - 1) / 2) * 94;
        });
      });
    }
    if (immediate && name !== "force") active.forEach((node) => {
      node.x = node.tx; node.y = node.ty; node.vx = 0; node.vy = 0;
    });
    this.reheat(1);
  }

  repel(active, temperature) {
    const limit = active.length <= 420 ? active.length : 0;
    if (limit) {
      for (let i = 0; i < limit; i += 1) for (let j = i + 1; j < limit; j += 1) {
        const a = active[i], b = active[j];
        const dx = a.x - b.x, dy = a.y - b.y;
        const d2 = dx * dx + dy * dy + 80, distance = Math.sqrt(d2);
        const force = Math.min(6.5, 930 * temperature / d2), ux = dx / distance, uy = dy / distance;
        a.vx += ux * force / a.mass; a.vy += uy * force / a.mass;
        b.vx -= ux * force / b.mass; b.vy -= uy * force / b.mass;
      }
      return;
    }
    const size = 190, buckets = new Map();
    active.forEach((node) => {
      const key = `${Math.floor(node.x / size)},${Math.floor(node.y / size)}`;
      if (!buckets.has(key)) buckets.set(key, []);
      buckets.get(key).push(node);
    });
    active.forEach((node) => {
      const cx = Math.floor(node.x / size), cy = Math.floor(node.y / size);
      for (let ox = -1; ox <= 1; ox += 1) for (let oy = -1; oy <= 1; oy += 1) {
        (buckets.get(`${cx + ox},${cy + oy}`) || []).forEach((other) => {
          if (other === node || other.id < node.id) return;
          const dx = node.x - other.x, dy = node.y - other.y;
          const d2 = dx * dx + dy * dy + 90, distance = Math.sqrt(d2);
          const force = Math.min(5.5, 900 * temperature / d2), ux = dx / distance, uy = dy / distance;
          node.vx += ux * force / node.mass; node.vy += uy * force / node.mass;
          other.vx -= ux * force / other.mass; other.vy -= uy * force / other.mass;
        });
      }
    });
  }

  collide(active, temperature) {
    const size = 52, buckets = new Map();
    active.forEach((node) => {
      const key = `${Math.floor(node.x / size)},${Math.floor(node.y / size)}`;
      if (!buckets.has(key)) buckets.set(key, []);
      buckets.get(key).push(node);
    });
    active.forEach((node) => {
      const cx = Math.floor(node.x / size), cy = Math.floor(node.y / size);
      for (let ox = -1; ox <= 1; ox += 1) for (let oy = -1; oy <= 1; oy += 1) {
        (buckets.get(`${cx + ox},${cy + oy}`) || []).forEach((other) => {
          if (other === node || other.id < node.id) return;
          let dx = other.x - node.x, dy = other.y - node.y, distance = Math.hypot(dx, dy);
          const minimum = node.radius + other.radius + 10;
          if (distance >= minimum) return;
          if (distance < 0.001) { dx = seeded(`${node.id}:${other.id}`, "cx") - .5; dy = seeded(`${node.id}:${other.id}`, "cy") - .5; distance = Math.hypot(dx, dy) || 1; }
          const overlap = (minimum - distance) * .3 * Math.max(temperature, .18), ux = dx / distance, uy = dy / distance;
          node.vx -= ux * overlap / node.mass; node.vy -= uy * overlap / node.mass;
          other.vx += ux * overlap / other.mass; other.vy += uy * overlap / other.mass;
        });
      }
    });
  }

  simulate(dragged = null) {
    if (this.alpha <= 0 && !dragged) return;
    const active = this.visibleNodes();
    if (!active.length) return;
    const temperature = dragged ? Math.max(this.alpha, .35) : this.alpha;
    if (this.layout === "force") {
      this.repel(active, temperature);
      this.visibleEdges().forEach((edge) => {
        const dx = edge.b.x - edge.a.x, dy = edge.b.y - edge.a.y, distance = Math.hypot(dx, dy) || 1;
        const target = 92 + edge.a.radius + edge.b.radius + Math.min(65, (edge.a.degree + edge.b.degree) * 1.8);
        const spring = clamp((distance - target) * .018 * temperature, -5, 5), ux = dx / distance, uy = dy / distance;
        edge.a.vx += ux * spring / edge.a.mass; edge.a.vy += uy * spring / edge.a.mass;
        edge.b.vx -= ux * spring / edge.b.mass; edge.b.vy -= uy * spring / edge.b.mass;
      });
      active.forEach((node) => { node.vx += -node.x * .0016 * temperature; node.vy += -node.y * .0016 * temperature; });
    } else active.forEach((node) => { node.vx += (node.tx - node.x) * .055 * temperature; node.vy += (node.ty - node.y) * .055 * temperature; });
    this.collide(active, temperature);
    active.forEach((node) => {
      node.vx *= .78; node.vy *= .78;
      const speed = Math.hypot(node.vx, node.vy);
      if (speed > 18) { node.vx = node.vx / speed * 18; node.vy = node.vy / speed * 18; }
      if (dragged !== node && !node.pinned) { node.x += node.vx; node.y += node.vy; }
    });
    this.alpha = dragged ? Math.max(this.alpha * .985, .22) : (this.alpha < .002 ? 0 : this.alpha * .982);
  }
}
