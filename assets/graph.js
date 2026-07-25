(async () => {
  const data = await fetch('graph.json').then((response) => response.json());
  const canvas = document.querySelector('#graph');
  const context = canvas.getContext('2d');
  const inspector = document.querySelector('#inspector');
  const search = document.querySelector('#graph-search');
  const reset = document.querySelector('#reset');
  const colors = { document: '#f6019d', entity: '#2de2e6', publisher: '#fba922' };
  let width = 0;
  let height = 0;
  let scale = 1;
  let offsetX = 0;
  let offsetY = 0;
  let drag = null;
  let hover = null;

  const nodes = data.nodes.map((node, index) => ({
    ...node,
    x: (Math.random() - 0.5) * 800,
    y: (Math.random() - 0.5) * 600,
    vx: 0,
    vy: 0,
    index,
  }));
  const byId = new Map(nodes.map((node) => [node.id, node]));
  const edges = data.edges
    .map((edge) => ({ ...edge, source: byId.get(edge.source), target: byId.get(edge.target) }))
    .filter((edge) => edge.source && edge.target);

  function resize() {
    const rect = canvas.getBoundingClientRect();
    const ratio = window.devicePixelRatio || 1;
    width = rect.width;
    height = rect.height;
    canvas.width = Math.round(width * ratio);
    canvas.height = Math.round(height * ratio);
    context.setTransform(ratio, 0, 0, ratio, 0, 0);
  }

  function screen(node) {
    return {
      x: (node.x + offsetX) * scale + width / 2,
      y: (node.y + offsetY) * scale + height / 2,
    };
  }

  function draw() {
    context.clearRect(0, 0, width, height);
    context.lineWidth = 1;
    for (const edge of edges) {
      const source = screen(edge.source);
      const target = screen(edge.target);
      context.strokeStyle = edge.type === 'related'
        ? 'rgba(151,0,204,.18)'
        : 'rgba(243,244,245,.08)';
      context.beginPath();
      context.moveTo(source.x, source.y);
      context.lineTo(target.x, target.y);
      context.stroke();
    }
    for (const node of nodes) {
      const point = screen(node);
      const radius = node.kind === 'document' ? 5 : 3;
      context.fillStyle = colors[node.kind] || '#f3f4f5';
      context.globalAlpha = hover && hover !== node ? 0.25 : 1;
      context.beginPath();
      context.arc(point.x, point.y, radius + (hover === node ? 4 : 0), 0, Math.PI * 2);
      context.fill();
      if (scale > 1.05 || hover === node) {
        context.globalAlpha = 1;
        context.fillStyle = '#f3f4f5';
        context.font = '11px system-ui';
        context.fillText(node.label.slice(0, 48), point.x + 9, point.y + 4);
      }
    }
    context.globalAlpha = 1;
  }

  function step() {
    for (const node of nodes) {
      node.vx *= 0.89;
      node.vy *= 0.89;
      node.vx += -node.x * 0.0004;
      node.vy += -node.y * 0.0004;
    }
    for (let left = 0; left < nodes.length; left += 1) {
      for (let right = left + 1; right < nodes.length; right += 1) {
        const a = nodes[left];
        const b = nodes[right];
        const dx = a.x - b.x;
        const dy = a.y - b.y;
        const distanceSquared = dx * dx + dy * dy + 0.1;
        const force = Math.min(1.4, 600 / distanceSquared);
        a.vx += dx * force * 0.02;
        a.vy += dy * force * 0.02;
        b.vx -= dx * force * 0.02;
        b.vy -= dy * force * 0.02;
      }
    }
    for (const edge of edges) {
      const dx = edge.target.x - edge.source.x;
      const dy = edge.target.y - edge.source.y;
      const distance = Math.hypot(dx, dy) || 1;
      const desired = edge.type === 'related' ? 95 : 150;
      const force = (distance - desired) * 0.0008;
      edge.source.vx += dx * force;
      edge.source.vy += dy * force;
      edge.target.vx -= dx * force;
      edge.target.vy -= dy * force;
    }
    for (const node of nodes) {
      if (node !== drag) {
        node.x += node.vx;
        node.y += node.vy;
      }
    }
    draw();
    requestAnimationFrame(step);
  }

  function canvasPoint(event) {
    const rect = canvas.getBoundingClientRect();
    return { x: event.clientX - rect.left, y: event.clientY - rect.top };
  }

  function findNode(x, y) {
    let best = null;
    let distance = 18;
    for (const node of nodes) {
      const point = screen(node);
      const candidate = Math.hypot(point.x - x, point.y - y);
      if (candidate < distance) {
        distance = candidate;
        best = node;
      }
    }
    return best;
  }

  function inspect(node) {
    const confidence = node.confidence == null ? '' : `<p>Confidence: ${node.confidence}</p>`;
    const link = node.url ? `<p><a href="${node.url}">Open record →</a></p>` : '';
    const dtype = node.dtype ? ` // ${node.dtype}` : '';
    inspector.innerHTML = `<div class="eyebrow">${node.kind}${dtype}</div><h3>${node.label}</h3>${confidence}${link}`;
  }

  canvas.addEventListener('pointerdown', (event) => {
    const point = canvasPoint(event);
    drag = findNode(point.x, point.y);
    canvas.setPointerCapture(event.pointerId);
  });
  canvas.addEventListener('pointermove', (event) => {
    const point = canvasPoint(event);
    hover = findNode(point.x, point.y);
    if (drag) {
      drag.x = (point.x - width / 2) / scale - offsetX;
      drag.y = (point.y - height / 2) / scale - offsetY;
      drag.vx = 0;
      drag.vy = 0;
    }
  });
  canvas.addEventListener('pointerup', () => {
    const selected = drag || hover;
    drag = null;
    if (selected) inspect(selected);
  });
  canvas.addEventListener('wheel', (event) => {
    event.preventDefault();
    scale = Math.max(0.35, Math.min(3, scale * (event.deltaY > 0 ? 0.9 : 1.1)));
  }, { passive: false });
  search.addEventListener('input', () => {
    const query = search.value.toLowerCase();
    const node = nodes.find((candidate) => candidate.label.toLowerCase().includes(query));
    if (node) {
      hover = node;
      offsetX = -node.x;
      offsetY = -node.y;
      scale = 1.4;
      inspect(node);
    }
  });
  reset.addEventListener('click', () => {
    scale = 1;
    offsetX = 0;
    offsetY = 0;
    hover = null;
    search.value = '';
  });
  resize();
  window.addEventListener('resize', resize);
  step();
})();
