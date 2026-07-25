const StarIntelGraph = (() => {
  "use strict";

  const TAU = Math.PI * 2;
  const GROUP_COLORS = {
    person: "#f59e0b",
    organization: "#22c55e",
    relation: "#38bdf8",
    event: "#a78bfa",
    claim: "#fb7185",
    analysis: "#f97316",
    concept: "#eab308",
    "investigation-target": "#ef4444",
    "financial-observation": "#14b8a6",
    education: "#60a5fa",
    employment: "#818cf8",
    "dataset-manifest": "#64748b",
    "research-pass": "#06b6d4",
    contract: "#10b981",
    policy: "#8b5cf6",
    source: "#64748b",
    entity: "#94a3b8"
  };
  const FALLBACK_COLORS = [
    "#2dd4bf", "#60a5fa", "#c084fc", "#f472b6", "#fb7185",
    "#fbbf24", "#a3e635", "#4ade80", "#22d3ee", "#818cf8"
  ];

  const clamp = (value, min, max) => Math.max(min, Math.min(max, value));
  const escapeHtml = (value) => String(value).replace(/[&<>"']/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  })[char]);

  function hashString(value) {
    let hash = 2166136261;
    for (let index = 0; index < value.length; index += 1) {
      hash ^= value.charCodeAt(index);
      hash = Math.imul(hash, 16777619);
    }
    return hash >>> 0;
  }

  function colorForGroup(group, provided) {
    if (GROUP_COLORS[group]) return GROUP_COLORS[group];
    if (provided && provided !== GROUP_COLORS.entity) return provided;
    if (group === "entity") return GROUP_COLORS.entity;
    return FALLBACK_COLORS[hashString(group) % FALLBACK_COLORS.length];
  }

  function shapeForGroup(group) {
    if (group === "person") return "circle";
    if (group === "organization") return "square";
    if (group === "relation") return "diamond";
    if (group === "event") return "hexagon";
    if (group === "claim" || group === "investigation-target") return "triangle";
    if (group === "research-pass" || group === "analysis") return "document";
    return "circle";
  }

  function mount(canvasId, detailId, url) {
    const canvas = document.getElementById(canvasId);
    const detail = document.getElementById(detailId);
    if (!canvas || !detail) return;

    const ctx = canvas.getContext("2d");
    const search = document.getElementById("graph-search");
    const filter = document.getElementById("graph-filter");
    const reset = document.getElementById("graph-reset");
    const controls = canvas.closest("section")?.querySelector(".controls") || canvas.parentElement;

    let data = null;
    let nodes = [];
    let edges = [];
    let nodeMap = new Map();
    let width = 1;
    let height = 1;
    let scale = 1;
    let pan = { x: 0, y: 0 };
    let drag = null;
    let hover = null;
    let primary = null;
    let selected = new Set();
    let focusIds = null;
    let alpha = 1;
    let animationFrame = null;
    let layoutName = "force";
    let edgeLabels = false;

    const layoutSelect = document.createElement("select");
    layoutSelect.id = "graph-layout";
    layoutSelect.title = "Topology layout";
    layoutSelect.innerHTML = [
      ["force", "Force"],
      ["hierarchical", "Hierarchy"],
      ["radial", "Radial"],
      ["concentric", "Concentric"],
      ["grid", "Type grid"]
    ].map(([value, label]) => `<option value="${value}">${label}</option>`).join("");

    const labelsToggle = document.createElement("label");
    labelsToggle.className = "graph-toggle";
    labelsToggle.innerHTML = '<input id="graph-edge-labels" type="checkbox"> Relations';
    const labelsInput = labelsToggle.querySelector("input");

    const focusButton = document.createElement("button");
    focusButton.type = "button";
    focusButton.id = "graph-focus";
    focusButton.textContent = "Focus";
    focusButton.title = "Show the selected node and direct relationships";

    const allButton = document.createElement("button");
    allButton.type = "button";
    allButton.id = "graph-all";
    allButton.textContent = "All";
    allButton.title = "Show the full graph";

    if (reset) {
      reset.textContent = "Fit";
      reset.title = "Fit visible nodes";
    }
    if (controls) controls.append(layoutSelect, labelsToggle, focusButton, allButton);

    const legend = document.createElement("div");
    legend.id = "graph-legend";
    legend.className = "graph-legend";
    canvas.closest("#graph-shell")?.insertAdjacentElement("beforebegin", legend);

    const help = document.createElement("div");
    help.className = "graph-help";
    help.textContent = "Drag nodes · drag empty space to pan · wheel to zoom · Shift-click to multi-select · double-click to open";
    legend.insertAdjacentElement("afterend", help);

    function reheat(value = 0.9) {
      alpha = Math.max(alpha, value);
    }

    function resize() {
      const rect = canvas.getBoundingClientRect();
      const dpr = window.devicePixelRatio || 1;
      const oldWidth = width;
      const oldHeight = height;
      width = Math.max(1, rect.width);
      height = Math.max(1, rect.height);
      canvas.width = Math.max(1, Math.floor(width * dpr));
      canvas.height = Math.max(1, Math.floor(height * dpr));
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      if (oldWidth > 1 && oldHeight > 1) {
        pan.x += (width - oldWidth) / 2;
        pan.y += (height - oldHeight) / 2;
      }
      reheat(0.35);
    }

    function seededUnit(id, salt) {
      return (hashString(`${id}:${salt}`) % 100000) / 100000;
    }

    function seedGraph() {
      const rawNodes = Array.isArray(data.nodes) ? data.nodes : [];
      const rawEdges = Array.isArray(data.edges) ? data.edges : [];
      const degrees = new Map(rawNodes.map((node) => [node.id, 0]));
      rawEdges.forEach((edge) => {
        degrees.set(edge.source, (degrees.get(edge.source) || 0) + 1);
        degrees.set(edge.target, (degrees.get(edge.target) || 0) + 1);
      });

      nodes = rawNodes.map((node, index) => {
        const degree = degrees.get(node.id) || 0;
        const radius = clamp(6 + Math.sqrt(degree + 1) * 1.6, 7, 18);
        const angle = index * 2.399963229728653;
        const spread = 28 * Math.sqrt(index + 1);
        return {
          ...node,
          color: colorForGroup(node.group || "entity", node.color),
          shape: shapeForGroup(node.group || "entity"),
          x: Math.cos(angle) * spread + (seededUnit(node.id, "x") - 0.5) * 22,
          y: Math.sin(angle) * spread + (seededUnit(node.id, "y") - 0.5) * 22,
          vx: 0,
          vy: 0,
          tx: 0,
          ty: 0,
          degree,
          radius,
          mass: 1 + Math.sqrt(degree + 1) * 0.45,
          visible: true,
          pinned: false
        };
      });
      nodeMap = new Map(nodes.map((node) => [node.id, node]));
      edges = rawEdges.map((edge) => ({
        ...edge,
        a: nodeMap.get(edge.source),
        b: nodeMap.get(edge.target)
      })).filter((edge) => edge.a && edge.b);

      populateFilters();
      updateVisibility();
      updateLegend();
      applyLayout("force", true);
      requestAnimationFrame(() => fitVisible(false));
      setTimeout(() => fitVisible(true), 650);
    }

    function populateFilters() {
      if (!filter) return;
      const existing = new Set([...filter.options].map((option) => option.value));
      [...new Set(nodes.map((node) => node.group || "entity"))].sort().forEach((group) => {
        if (existing.has(group)) return;
        const option = document.createElement("option");
        option.value = group;
        option.textContent = group.replaceAll("-", " ");
        filter.appendChild(option);
      });
    }

    function matchesControls(node) {
      const query = (search?.value || "").trim().toLowerCase();
      const group = filter?.value || "";
      if (group && node.group !== group) return false;
      if (focusIds && !focusIds.has(node.id)) return false;
      if (!query) return true;
      return [node.label, node.id, node.detail, node.group]
        .filter(Boolean)
        .some((value) => String(value).toLowerCase().includes(query));
    }

    function updateVisibility() {
      nodes.forEach((node) => {
        node.visible = matchesControls(node);
      });
      if (primary && !primary.visible) primary = null;
      selected = new Set([...selected].filter((node) => node.visible));
      applyLayout(layoutName, false);
      updateLegend();
      reheat(1);
    }

    function updateLegend() {
      const counts = new Map();
      nodes.forEach((node) => {
        if (!node.visible) return;
        const current = counts.get(node.group) || { count: 0, color: node.color, shape: node.shape };
        current.count += 1;
        counts.set(node.group, current);
      });
      legend.innerHTML = [...counts.entries()].sort(([a], [b]) => a.localeCompare(b)).map(([group, item]) => (
        `<button type="button" class="graph-legend-item" data-group="${escapeHtml(group)}">` +
        `<span class="graph-legend-shape graph-shape-${escapeHtml(item.shape)}" style="--node-color:${escapeHtml(item.color)}"></span>` +
        `<span>${escapeHtml(group.replaceAll("-", " "))}</span><strong>${item.count}</strong></button>`
      )).join("");
    }

    function visibleNodes() {
      return nodes.filter((node) => node.visible);
    }

    function visibleEdges() {
      return edges.filter((edge) => edge.a.visible && edge.b.visible);
    }

    function chooseRoot(active) {
      if (primary?.visible) return primary;
      return [...active].sort((a, b) => b.degree - a.degree || a.id.localeCompare(b.id))[0] || null;
    }

    function breadthFirstLevels(active, root) {
      const activeIds = new Set(active.map((node) => node.id));
      const adjacency = new Map(active.map((node) => [node.id, []]));
      visibleEdges().forEach((edge) => {
        if (!activeIds.has(edge.a.id) || !activeIds.has(edge.b.id)) return;
        adjacency.get(edge.a.id).push(edge.b);
        adjacency.get(edge.b.id).push(edge.a);
      });
      const levels = new Map();
      const queue = [];
      if (root) {
        levels.set(root.id, 0);
        queue.push(root);
      }
      while (queue.length) {
        const node = queue.shift();
        const level = levels.get(node.id);
        adjacency.get(node.id).forEach((neighbor) => {
          if (levels.has(neighbor.id)) return;
          levels.set(neighbor.id, level + 1);
          queue.push(neighbor);
        });
      }
      let maxLevel = Math.max(0, ...levels.values());
      active.forEach((node) => {
        if (levels.has(node.id)) return;
        maxLevel += 1;
        levels.set(node.id, maxLevel);
      });
      return levels;
    }

    function applyLayout(name, immediate = false) {
      layoutName = name;
      if (layoutSelect.value !== name) layoutSelect.value = name;
      const active = visibleNodes();
      if (!active.length) return;
      const root = chooseRoot(active);
      const levels = breadthFirstLevels(active, root);

      if (name === "force") {
        active.forEach((node) => {
          node.tx = 0;
          node.ty = 0;
        });
      } else if (name === "hierarchical") {
        const grouped = new Map();
        active.forEach((node) => {
          const level = levels.get(node.id) || 0;
          if (!grouped.has(level)) grouped.set(level, []);
          grouped.get(level).push(node);
        });
        [...grouped.entries()].sort(([a], [b]) => a - b).forEach(([level, row]) => {
          row.sort((a, b) => b.degree - a.degree || a.label.localeCompare(b.label));
          const gap = 115;
          row.forEach((node, index) => {
            node.tx = (index - (row.length - 1) / 2) * gap;
            node.ty = (level - (grouped.size - 1) / 2) * 150;
          });
        });
      } else if (name === "radial") {
        const grouped = new Map();
        active.forEach((node) => {
          const level = levels.get(node.id) || 0;
          if (!grouped.has(level)) grouped.set(level, []);
          grouped.get(level).push(node);
        });
        [...grouped.entries()].forEach(([level, ring]) => {
          ring.sort((a, b) => b.degree - a.degree || a.label.localeCompare(b.label));
          const radius = level === 0 ? 0 : 120 + (level - 1) * 130;
          ring.forEach((node, index) => {
            const angle = ring.length === 1 ? 0 : (index / ring.length) * TAU - Math.PI / 2;
            node.tx = Math.cos(angle) * radius;
            node.ty = Math.sin(angle) * radius;
          });
        });
      } else if (name === "concentric") {
        const sorted = [...active].sort((a, b) => b.degree - a.degree || a.label.localeCompare(b.label));
        const maxDegree = Math.max(1, ...sorted.map((node) => node.degree));
        const rings = new Map();
        sorted.forEach((node) => {
          const ring = Math.floor((1 - node.degree / maxDegree) * 4);
          if (!rings.has(ring)) rings.set(ring, []);
          rings.get(ring).push(node);
        });
        [...rings.entries()].forEach(([ringIndex, ring]) => {
          const radius = ringIndex === 0 ? 0 : 105 + ringIndex * 115;
          ring.forEach((node, index) => {
            const angle = ring.length === 1 ? 0 : (index / ring.length) * TAU - Math.PI / 2;
            node.tx = Math.cos(angle) * radius;
            node.ty = Math.sin(angle) * radius;
          });
        });
      } else if (name === "grid") {
        const groups = new Map();
        active.forEach((node) => {
          if (!groups.has(node.group)) groups.set(node.group, []);
          groups.get(node.group).push(node);
        });
        const columns = [...groups.entries()].sort(([a], [b]) => a.localeCompare(b));
        const columnGap = 170;
        columns.forEach(([, column], columnIndex) => {
          column.sort((a, b) => b.degree - a.degree || a.label.localeCompare(b.label));
          column.forEach((node, rowIndex) => {
            node.tx = (columnIndex - (columns.length - 1) / 2) * columnGap;
            node.ty = (rowIndex - (column.length - 1) / 2) * 88;
          });
        });
      }

      if (immediate && name !== "force") {
        active.forEach((node) => {
          node.x = node.tx;
          node.y = node.ty;
          node.vx = 0;
          node.vy = 0;
        });
      }
      reheat(1);
    }

    function makeQuad(active) {
      if (!active.length) return null;
      let minX = Infinity;
      let minY = Infinity;
      let maxX = -Infinity;
      let maxY = -Infinity;
      active.forEach((node) => {
        minX = Math.min(minX, node.x);
        minY = Math.min(minY, node.y);
        maxX = Math.max(maxX, node.x);
        maxY = Math.max(maxY, node.y);
      });
      const size = Math.max(maxX - minX, maxY - minY, 1) + 2;
      const root = {
        x: (minX + maxX - size) / 2,
        y: (minY + maxY - size) / 2,
        size,
        body: null,
        children: null,
        mass: 0,
        cx: 0,
        cy: 0
      };

      function childIndex(quad, node) {
        const right = node.x >= quad.x + quad.size / 2 ? 1 : 0;
        const bottom = node.y >= quad.y + quad.size / 2 ? 2 : 0;
        return right + bottom;
      }

      function subdivide(quad) {
        const half = quad.size / 2;
        quad.children = [0, 1, 2, 3].map((index) => ({
          x: quad.x + (index % 2) * half,
          y: quad.y + (index > 1 ? half : 0),
          size: half,
          body: null,
          children: null,
          mass: 0,
          cx: 0,
          cy: 0
        }));
      }

      function insert(quad, node, depth = 0) {
        if (!quad.children && !quad.body) {
          quad.body = node;
          return;
        }
        if (!quad.children) {
          if (depth > 18 || quad.size < 0.01) {
            node.x += (seededUnit(node.id, depth) - 0.5) * 0.1;
            node.y += (seededUnit(node.id, depth + 1) - 0.5) * 0.1;
          }
          subdivide(quad);
          const oldBody = quad.body;
          quad.body = null;
          insert(quad.children[childIndex(quad, oldBody)], oldBody, depth + 1);
        }
        insert(quad.children[childIndex(quad, node)], node, depth + 1);
      }

      function aggregate(quad) {
        if (!quad.children) {
          if (quad.body) {
            quad.mass = quad.body.mass;
            quad.cx = quad.body.x;
            quad.cy = quad.body.y;
          }
          return;
        }
        quad.mass = 0;
        quad.cx = 0;
        quad.cy = 0;
        quad.children.forEach((child) => {
          aggregate(child);
          quad.mass += child.mass;
          quad.cx += child.cx * child.mass;
          quad.cy += child.cy * child.mass;
        });
        if (quad.mass) {
          quad.cx /= quad.mass;
          quad.cy /= quad.mass;
        }
      }

      active.forEach((node) => insert(root, node));
      aggregate(root);
      return root;
    }

    function applyRepulsion(node, quad, temperature) {
      if (!quad || !quad.mass) return;
      if (!quad.children && quad.body === node) return;
      const dx = node.x - quad.cx;
      const dy = node.y - quad.cy;
      const distanceSquared = dx * dx + dy * dy + 64;
      const distance = Math.sqrt(distanceSquared);
      if (!quad.children || quad.size / distance < 0.72) {
        const force = Math.min(7, (850 * quad.mass * temperature) / distanceSquared);
        node.vx += (dx / distance) * force / node.mass;
        node.vy += (dy / distance) * force / node.mass;
        return;
      }
      quad.children.forEach((child) => applyRepulsion(node, child, temperature));
    }

    function applyLinks(temperature) {
      visibleEdges().forEach((edge) => {
        const dx = edge.b.x - edge.a.x;
        const dy = edge.b.y - edge.a.y;
        const distance = Math.hypot(dx, dy) || 1;
        const target = 92 + edge.a.radius + edge.b.radius + Math.min(65, (edge.a.degree + edge.b.degree) * 1.8);
        const spring = clamp((distance - target) * 0.018 * temperature, -5, 5);
        const ux = dx / distance;
        const uy = dy / distance;
        edge.a.vx += ux * spring / edge.a.mass;
        edge.a.vy += uy * spring / edge.a.mass;
        edge.b.vx -= ux * spring / edge.b.mass;
        edge.b.vy -= uy * spring / edge.b.mass;
      });
    }

    function applyCollisions(active, temperature) {
      const cellSize = 48;
      const buckets = new Map();
      active.forEach((node) => {
        const key = `${Math.floor(node.x / cellSize)},${Math.floor(node.y / cellSize)}`;
        if (!buckets.has(key)) buckets.set(key, []);
        buckets.get(key).push(node);
      });
      active.forEach((node) => {
        const cx = Math.floor(node.x / cellSize);
        const cy = Math.floor(node.y / cellSize);
        for (let ox = -1; ox <= 1; ox += 1) {
          for (let oy = -1; oy <= 1; oy += 1) {
            const bucket = buckets.get(`${cx + ox},${cy + oy}`);
            if (!bucket) continue;
            bucket.forEach((other) => {
              if (other === node || other.id < node.id) return;
              let dx = other.x - node.x;
              let dy = other.y - node.y;
              let distance = Math.hypot(dx, dy);
              const minimum = node.radius + other.radius + 9;
              if (distance >= minimum) return;
              if (distance < 0.001) {
                dx = seededUnit(`${node.id}:${other.id}`, "cx") - 0.5;
                dy = seededUnit(`${node.id}:${other.id}`, "cy") - 0.5;
                distance = Math.hypot(dx, dy) || 1;
              }
              const overlap = (minimum - distance) * 0.28 * Math.max(temperature, 0.18);
              const ux = dx / distance;
              const uy = dy / distance;
              node.vx -= ux * overlap / node.mass;
              node.vy -= uy * overlap / node.mass;
              other.vx += ux * overlap / other.mass;
              other.vy += uy * overlap / other.mass;
            });
          }
        }
      });
    }

    function simulate() {
      if (alpha <= 0 && !drag) return;
      const active = visibleNodes();
      if (!active.length) return;
      const temperature = drag ? Math.max(alpha, 0.35) : alpha;

      if (layoutName === "force") {
        const quad = makeQuad(active);
        active.forEach((node) => applyRepulsion(node, quad, temperature));
        applyLinks(temperature);
        active.forEach((node) => {
          node.vx += -node.x * 0.0016 * temperature;
          node.vy += -node.y * 0.0016 * temperature;
        });
      } else {
        active.forEach((node) => {
          node.vx += (node.tx - node.x) * 0.055 * temperature;
          node.vy += (node.ty - node.y) * 0.055 * temperature;
        });
      }

      applyCollisions(active, temperature);
      active.forEach((node) => {
        node.vx *= 0.78;
        node.vy *= 0.78;
        const speed = Math.hypot(node.vx, node.vy);
        if (speed > 18) {
          node.vx = node.vx / speed * 18;
          node.vy = node.vy / speed * 18;
        }
        if (drag?.node !== node && !node.pinned) {
          node.x += node.vx;
          node.y += node.vy;
        }
      });
      alpha = drag ? Math.max(alpha * 0.985, 0.22) : (alpha < 0.002 ? 0 : alpha * 0.982);
    }

    function screen(node) {
      return { x: node.x * scale + pan.x, y: node.y * scale + pan.y };
    }

    function world(point) {
      return { x: (point.x - pan.x) / scale, y: (point.y - pan.y) / scale };
    }

    function drawArrow(a, b, edge, emphasized) {
      const dx = b.x - a.x;
      const dy = b.y - a.y;
      const distance = Math.hypot(dx, dy) || 1;
      const ux = dx / distance;
      const uy = dy / distance;
      const startPadding = edge.a.radius * scale + 2;
      const endPadding = edge.b.radius * scale + 7;
      const sx = a.x + ux * startPadding;
      const sy = a.y + uy * startPadding;
      const tx = b.x - ux * endPadding;
      const ty = b.y - uy * endPadding;

      ctx.beginPath();
      ctx.moveTo(sx, sy);
      ctx.lineTo(tx, ty);
      ctx.strokeStyle = emphasized ? "#8ec5ff" : "#29415e";
      ctx.globalAlpha = emphasized ? 0.92 : 0.42;
      ctx.lineWidth = emphasized ? 1.5 : 0.8;
      ctx.stroke();

      const arrowSize = emphasized ? 6 : 4;
      ctx.beginPath();
      ctx.moveTo(tx, ty);
      ctx.lineTo(tx - ux * arrowSize - uy * arrowSize * 0.7, ty - uy * arrowSize + ux * arrowSize * 0.7);
      ctx.lineTo(tx - ux * arrowSize + uy * arrowSize * 0.7, ty - uy * arrowSize - ux * arrowSize * 0.7);
      ctx.closePath();
      ctx.fillStyle = emphasized ? "#8ec5ff" : "#4c6685";
      ctx.fill();

      if (edgeLabels || emphasized) {
        const mx = (sx + tx) / 2;
        const my = (sy + ty) / 2;
        const label = edge.label || "related";
        ctx.font = "10px system-ui";
        const metrics = ctx.measureText(label);
        ctx.globalAlpha = 0.94;
        ctx.fillStyle = "#07111f";
        ctx.fillRect(mx - metrics.width / 2 - 4, my - 8, metrics.width + 8, 14);
        ctx.fillStyle = emphasized ? "#dbeafe" : "#93a4b8";
        ctx.fillText(label, mx - metrics.width / 2, my + 3);
      }
    }

    function nodePath(point, node, radius) {
      ctx.beginPath();
      if (node.shape === "square") {
        const r = radius * 0.28;
        ctx.roundRect(point.x - radius, point.y - radius, radius * 2, radius * 2, r);
      } else if (node.shape === "diamond") {
        ctx.moveTo(point.x, point.y - radius * 1.25);
        ctx.lineTo(point.x + radius * 1.1, point.y);
        ctx.lineTo(point.x, point.y + radius * 1.25);
        ctx.lineTo(point.x - radius * 1.1, point.y);
        ctx.closePath();
      } else if (node.shape === "triangle") {
        ctx.moveTo(point.x, point.y - radius * 1.25);
        ctx.lineTo(point.x + radius * 1.12, point.y + radius);
        ctx.lineTo(point.x - radius * 1.12, point.y + radius);
        ctx.closePath();
      } else if (node.shape === "hexagon") {
        for (let index = 0; index < 6; index += 1) {
          const angle = index / 6 * TAU - Math.PI / 2;
          const x = point.x + Math.cos(angle) * radius * 1.15;
          const y = point.y + Math.sin(angle) * radius * 1.15;
          if (index === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
        }
        ctx.closePath();
      } else if (node.shape === "document") {
        ctx.roundRect(point.x - radius * 0.86, point.y - radius * 1.1, radius * 1.72, radius * 2.2, radius * 0.18);
      } else {
        ctx.arc(point.x, point.y, radius, 0, TAU);
      }
    }

    function drawNode(node) {
      const point = screen(node);
      const isPrimary = node === primary;
      const isSelected = selected.has(node);
      const isHover = node === hover;
      const radius = Math.max(4.5, node.radius * clamp(scale, 0.65, 1.3));
      nodePath(point, node, radius);
      ctx.globalAlpha = node.visible ? 1 : 0.1;
      ctx.fillStyle = node.color;
      ctx.fill();
      ctx.strokeStyle = isPrimary ? "#ffffff" : isSelected ? "#bae6fd" : isHover ? "#e2e8f0" : "#07111f";
      ctx.lineWidth = isPrimary ? 3 : isSelected || isHover ? 2 : 1.1;
      ctx.stroke();

      const showLabel = isPrimary || isSelected || isHover || (scale > 1.2 && node.degree >= 2);
      if (showLabel) {
        ctx.font = isPrimary ? "600 12px system-ui" : "11px system-ui";
        ctx.textBaseline = "middle";
        const label = node.label || node.id;
        const maxWidth = 260;
        let visibleLabel = label;
        while (visibleLabel.length > 8 && ctx.measureText(`${visibleLabel}…`).width > maxWidth) {
          visibleLabel = visibleLabel.slice(0, -1);
        }
        if (visibleLabel !== label) visibleLabel += "…";
        const textWidth = ctx.measureText(visibleLabel).width;
        const lx = point.x + radius + 8;
        const ly = point.y;
        ctx.globalAlpha = 0.94;
        ctx.fillStyle = "#07111f";
        ctx.fillRect(lx - 3, ly - 9, textWidth + 6, 18);
        ctx.fillStyle = "#f8fafc";
        ctx.fillText(visibleLabel, lx, ly + 0.5);
      }
    }

    function draw() {
      ctx.clearRect(0, 0, width, height);
      ctx.save();
      ctx.lineCap = "round";
      const selectedIds = new Set([...selected].map((node) => node.id));
      visibleEdges().forEach((edge) => {
        const emphasized = edge.a === hover || edge.b === hover || edge.a === primary || edge.b === primary ||
          selectedIds.has(edge.a.id) && selectedIds.has(edge.b.id);
        drawArrow(screen(edge.a), screen(edge.b), edge, emphasized);
      });
      ctx.globalAlpha = 1;
      visibleNodes().sort((a, b) => a.degree - b.degree).forEach(drawNode);
      ctx.restore();
    }

    function loop() {
      simulate();
      draw();
      animationFrame = requestAnimationFrame(loop);
    }

    function pointerPoint(event) {
      const rect = canvas.getBoundingClientRect();
      return { x: event.clientX - rect.left, y: event.clientY - rect.top };
    }

    function nearest(point) {
      let best = null;
      let bestDistance = 18;
      nodes.forEach((node) => {
        if (!node.visible) return;
        const location = screen(node);
        const distance = Math.hypot(location.x - point.x, location.y - point.y) - node.radius * scale;
        if (distance < bestDistance) {
          bestDistance = distance;
          best = node;
        }
      });
      return best;
    }

    function selectNode(node, additive = false) {
      if (!node) {
        if (!additive) {
          selected.clear();
          primary = null;
          showDetail(null);
        }
        return;
      }
      if (additive) {
        if (selected.has(node)) selected.delete(node); else selected.add(node);
        primary = selected.has(node) ? node : [...selected].at(-1) || null;
      } else {
        selected = new Set([node]);
        primary = node;
      }
      showDetail(primary);
      if (layoutName === "hierarchical" || layoutName === "radial") applyLayout(layoutName, false);
    }

    function neighborhood(node, depth = 1) {
      const ids = new Set([node.id]);
      let frontier = new Set([node.id]);
      for (let step = 0; step < depth; step += 1) {
        const next = new Set();
        edges.forEach((edge) => {
          if (frontier.has(edge.source) && !ids.has(edge.target)) next.add(edge.target);
          if (frontier.has(edge.target) && !ids.has(edge.source)) next.add(edge.source);
        });
        next.forEach((id) => ids.add(id));
        frontier = next;
      }
      return ids;
    }

    function focus(node = primary, depth = 1) {
      if (!node) return;
      focusIds = neighborhood(node, depth);
      updateVisibility();
      fitVisible(true);
    }

    function showAll() {
      focusIds = null;
      updateVisibility();
      fitVisible(true);
    }

    function incidentEdges(node) {
      return edges.filter((edge) => edge.a === node || edge.b === node);
    }

    function showDetail(node) {
      if (!node) {
        detail.innerHTML = '<h3>Graph explorer</h3><p>Select a node to inspect its direct relationships.</p>';
        return;
      }
      const relationships = incidentEdges(node).sort((a, b) => (a.label || "").localeCompare(b.label || ""));
      const relationshipRows = relationships.slice(0, 80).map((edge) => {
        const outgoing = edge.a === node;
        const neighbor = outgoing ? edge.b : edge.a;
        const direction = outgoing ? "→" : "←";
        return `<li><button type="button" data-node-id="${escapeHtml(neighbor.id)}">` +
          `<span>${direction} ${escapeHtml(edge.label || "related")}</span><strong>${escapeHtml(neighbor.label || neighbor.id)}</strong></button></li>`;
      }).join("");
      const hiddenCount = Math.max(0, relationships.length - 80);
      detail.innerHTML = `
        <div class="graph-detail-heading">
          <span class="graph-detail-swatch" style="--node-color:${escapeHtml(node.color)}"></span>
          <div><span>${escapeHtml((node.group || "entity").replaceAll("-", " "))}</span><h3>${escapeHtml(node.label || node.id)}</h3></div>
        </div>
        <p><code>${escapeHtml(node.id)}</code></p>
        <p>${escapeHtml(node.detail || "No summary attached.")}</p>
        <div class="graph-detail-stats"><span><strong>${node.degree}</strong> links</span><span><strong>${selected.size}</strong> selected</span></div>
        <div class="graph-detail-actions">
          <button type="button" data-action="focus-1">Focus 1 hop</button>
          <button type="button" data-action="focus-2">Focus 2 hops</button>
          <button type="button" data-action="pin">${node.pinned ? "Unpin" : "Pin"}</button>
          <button type="button" data-action="show-all">Show all</button>
        </div>
        ${node.href ? `<p><a class="graph-open-record" href="${escapeHtml(node.href)}">Open record →</a></p>` : ""}
        <h4>Relationships</h4>
        <ul class="graph-relations">${relationshipRows}</ul>
        ${hiddenCount ? `<p class="graph-muted">${hiddenCount} more relationships hidden.</p>` : ""}
      `;
    }

    function fitVisible(animate = true) {
      const active = visibleNodes();
      if (!active.length) return;
      let minX = Infinity;
      let minY = Infinity;
      let maxX = -Infinity;
      let maxY = -Infinity;
      active.forEach((node) => {
        minX = Math.min(minX, node.x - node.radius - 20);
        minY = Math.min(minY, node.y - node.radius - 20);
        maxX = Math.max(maxX, node.x + node.radius + 20);
        maxY = Math.max(maxY, node.y + node.radius + 20);
      });
      const graphWidth = Math.max(1, maxX - minX);
      const graphHeight = Math.max(1, maxY - minY);
      const targetScale = clamp(Math.min((width - 40) / graphWidth, (height - 40) / graphHeight), 0.12, 2.4);
      const targetPan = {
        x: width / 2 - ((minX + maxX) / 2) * targetScale,
        y: height / 2 - ((minY + maxY) / 2) * targetScale
      };
      if (!animate) {
        scale = targetScale;
        pan = targetPan;
        return;
      }
      const startScale = scale;
      const startPan = { ...pan };
      const started = performance.now();
      const duration = 260;
      function step(now) {
        const progress = clamp((now - started) / duration, 0, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        scale = startScale + (targetScale - startScale) * eased;
        pan.x = startPan.x + (targetPan.x - startPan.x) * eased;
        pan.y = startPan.y + (targetPan.y - startPan.y) * eased;
        if (progress < 1) requestAnimationFrame(step);
      }
      requestAnimationFrame(step);
    }

    canvas.addEventListener("pointerdown", (event) => {
      const point = pointerPoint(event);
      const node = nearest(point);
      canvas.setPointerCapture(event.pointerId);
      if (node) {
        selectNode(node, event.shiftKey);
        drag = { node, start: point };
        node.vx = 0;
        node.vy = 0;
        reheat(0.55);
      } else {
        if (!event.shiftKey) selectNode(null, false);
        drag = { pan: true, last: point, start: point };
      }
    });

    canvas.addEventListener("pointermove", (event) => {
      const point = pointerPoint(event);
      hover = nearest(point);
      canvas.style.cursor = hover ? "pointer" : drag ? "grabbing" : "grab";
      if (!drag) return;
      if (drag.pan) {
        pan.x += point.x - drag.last.x;
        pan.y += point.y - drag.last.y;
        drag.last = point;
      } else if (drag.node) {
        const location = world(point);
        drag.node.x = location.x;
        drag.node.y = location.y;
        drag.node.vx = 0;
        drag.node.vy = 0;
        if (layoutName !== "force") {
          drag.node.tx = location.x;
          drag.node.ty = location.y;
        }
        reheat(0.35);
      }
    });

    canvas.addEventListener("pointerup", (event) => {
      if (canvas.hasPointerCapture(event.pointerId)) canvas.releasePointerCapture(event.pointerId);
      drag = null;
    });
    canvas.addEventListener("pointercancel", () => { drag = null; });
    canvas.addEventListener("pointerleave", () => { if (!drag) hover = null; });
    canvas.addEventListener("dblclick", (event) => {
      const node = nearest(pointerPoint(event));
      if (node?.href) window.location.href = node.href;
    });
    canvas.addEventListener("contextmenu", (event) => {
      event.preventDefault();
      const node = nearest(pointerPoint(event));
      if (node) {
        selectNode(node, false);
        focus(node, 1);
      }
    });
    canvas.addEventListener("wheel", (event) => {
      event.preventDefault();
      const point = pointerPoint(event);
      const oldScale = scale;
      scale = clamp(scale * (event.deltaY < 0 ? 1.13 : 0.885), 0.08, 5);
      pan.x = point.x - (point.x - pan.x) * (scale / oldScale);
      pan.y = point.y - (point.y - pan.y) * (scale / oldScale);
    }, { passive: false });

    search?.addEventListener("input", updateVisibility);
    filter?.addEventListener("input", updateVisibility);
    reset?.addEventListener("click", () => fitVisible(true));
    layoutSelect.addEventListener("change", () => {
      applyLayout(layoutSelect.value, layoutSelect.value !== "force");
      requestAnimationFrame(() => fitVisible(true));
    });
    labelsInput.addEventListener("change", () => { edgeLabels = labelsInput.checked; });
    focusButton.addEventListener("click", () => focus(primary, 1));
    allButton.addEventListener("click", showAll);
    legend.addEventListener("click", (event) => {
      const button = event.target.closest("[data-group]");
      if (!button || !filter) return;
      filter.value = filter.value === button.dataset.group ? "" : button.dataset.group;
      updateVisibility();
      fitVisible(true);
    });
    detail.addEventListener("click", (event) => {
      const nodeButton = event.target.closest("[data-node-id]");
      if (nodeButton) {
        const node = nodeMap.get(nodeButton.dataset.nodeId);
        if (node) {
          selectNode(node, false);
          const point = screen(node);
          pan.x += width / 2 - point.x;
          pan.y += height / 2 - point.y;
        }
        return;
      }
      const action = event.target.closest("[data-action]")?.dataset.action;
      if (!action) return;
      if (action === "focus-1") focus(primary, 1);
      if (action === "focus-2") focus(primary, 2);
      if (action === "show-all") showAll();
      if (action === "pin" && primary) {
        primary.pinned = !primary.pinned;
        primary.vx = 0;
        primary.vy = 0;
        showDetail(primary);
      }
    });
    window.addEventListener("resize", resize);
    window.addEventListener("keydown", (event) => {
      if (event.key === "Escape") showAll();
      if (event.key.toLowerCase() === "f" && !/input|select|textarea/i.test(document.activeElement?.tagName || "")) fitVisible(true);
    });

    fetch(url)
      .then((response) => {
        if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
        return response.json();
      })
      .then((graph) => {
        data = graph;
        resize();
        seedGraph();
        showDetail(null);
        if (animationFrame) cancelAnimationFrame(animationFrame);
        loop();
      })
      .catch((error) => {
        detail.textContent = `Graph load failed: ${error.message || error}`;
      });
  }

  return { mount };
})();
