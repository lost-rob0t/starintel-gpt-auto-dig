import { URL_KEYS, clamp, edgeKey, findPaths } from "./graph-core.mjs";
import { GraphModel } from "./graph-model.mjs";
import { GraphRendererScaled } from "./graph-render-scaled.mjs";
import { buildUI, populateNodeOptions, renderLegend, renderDetail, renderPaths } from "./graph-ui.mjs";

const EXTRA_URL_KEYS = ["review", "predicate", "dataset", "mode"];
const MAX_BACKBONE = 140;
const MAX_CONTEXT = 260;
const MAX_FOCUS = 380;

export async function mount(canvasId, detailId, url) {
  const canvas = document.getElementById(canvasId);
  const detail = document.getElementById(detailId);
  if (!canvas || !detail) return;

  const search = document.getElementById("graph-search");
  const filter = document.getElementById("graph-filter");
  const review = document.getElementById("graph-review");
  const predicate = document.getElementById("graph-predicate");
  const dataset = document.getElementById("graph-dataset");
  const reset = document.getElementById("graph-reset");
  const detailToggle = document.getElementById("graph-detail-toggle");
  const modeStatus = document.getElementById("graph-mode-status");
  const visibleCount = document.getElementById("graph-visible-count");
  const visibleEdges = document.getElementById("graph-visible-edges");

  const response = await fetch(url);
  if (!response.ok) {
    detail.textContent = `Graph load failed: ${response.status}`;
    return;
  }

  const model = new GraphModel(await response.json());
  const renderer = new GraphRendererScaled(canvas, model);
  const ui = buildUI(canvas, detail);
  const state = {
    scale: 1,
    pan: { x: 0, y: 0 },
    drag: null,
    hover: null,
    primary: null,
    selected: new Set(),
    mode: "backbone",
    focusIds: null,
    focusDepth: 1,
    edgeLabels: false,
    pathStart: null,
    pathEnd: null,
    paths: [],
    activePath: -1,
    pathNodes: new Set(),
    pathEdges: new Set(),
    restoring: false,
    urlTimer: null,
    dirty: true
  };

  const originalVisibleEdges = model.visibleEdges.bind(model);
  model.visibleEdges = () => originalVisibleEdges().filter((edge) => edge.visible !== false);

  const groups = [...new Set(model.nodes.map((node) => node.group || "entity"))].sort();
  const predicates = [...new Set(model.edges.map((edge) => edge.label || "related"))].sort();
  const datasets = [...new Set(model.nodes.map((node) => node.dataset).filter(Boolean))].sort();
  groups.forEach((group) => {
    const option = document.createElement("option");
    option.value = group;
    option.textContent = group.replaceAll("-", " ");
    filter?.appendChild(option);
  });
  predicates.forEach((label) => {
    const option = document.createElement("option");
    option.value = label;
    option.textContent = label;
    predicate?.appendChild(option);
  });
  datasets.forEach((name) => {
    const option = document.createElement("option");
    option.value = name;
    option.textContent = name;
    dataset?.appendChild(option);
  });

  ui.all.textContent = "Full graph";
  ui.all.title = "Explicitly load every node that passes the current filters";
  ui.focus.textContent = "Focus 1 hop";
  reset.textContent = "Fit";
  reset.title = "Fit visible nodes";

  const reviewedBackbone = buildBackbone(model.nodes, (node) => node.reviewed !== false);
  const unreviewedBackbone = buildBackbone(model.nodes, (node) => node.reviewed === false);
  const completeBackbone = buildBackbone(model.nodes, () => true);
  let frame = null;

  const incident = (node) => model.edges.filter((edge) => edge.a === node || edge.b === node);
  const view = () => ({
    scale: state.scale,
    pan: state.pan,
    hover: state.hover,
    primary: state.primary,
    selected: state.selected,
    pathNodes: state.pathNodes,
    pathEdges: state.pathEdges,
    edgeLabels: state.edgeLabels,
    reviewMode: review?.value || "",
    labelDegree: state.mode === "full" ? 8 : 3
  });
  const point = (event) => {
    const rect = canvas.getBoundingClientRect();
    return { x: event.clientX - rect.left, y: event.clientY - rect.top };
  };
  const invalidate = () => { state.dirty = true; };
  const resolve = (value) => {
    const text = String(value || "").trim();
    if (!text) return null;
    if (model.nodeMap.has(text)) return text;
    const found = model.nodes.filter((node) => (node.label || "").toLowerCase() === text.toLowerCase());
    return found.length === 1 ? found[0].id : null;
  };

  const reviewAllowed = (item) => {
    const mode = review?.value || "";
    if (!mode) return true;
    return mode === "reviewed" ? item.reviewed !== false : item.reviewed === false;
  };
  const groupAllowed = (node) => !filter?.value || node.group === filter.value;
  const datasetAllowed = (node) => !dataset?.value || node.dataset === dataset.value;
  const backboneIds = () => review?.value === "unreviewed" ? unreviewedBackbone : review?.value ? reviewedBackbone : completeBackbone;
  const predicateAllowed = (edge) => !predicate?.value || (edge.label || "related") === predicate.value;

  const searchContext = () => {
    const needle = String(search?.value || "").trim().toLowerCase();
    if (!needle) return null;
    const matches = model.nodes.filter((node) => reviewAllowed(node) && groupAllowed(node) && datasetAllowed(node) && [node.label, node.id, node.detail, node.group, node.dataset]
      .filter(Boolean).some((value) => String(value).toLowerCase().includes(needle)));
    const ids = new Set(matches.map((node) => node.id));
    const frontier = new Set(ids);
    for (const edge of model.edges) {
      if (!predicateAllowed(edge) || !reviewAllowed(edge)) continue;
      if (frontier.has(edge.source)) ids.add(edge.target);
      if (frontier.has(edge.target)) ids.add(edge.source);
    }
    return capIds(ids, model.nodeMap, MAX_CONTEXT, new Set(matches.map((node) => node.id)));
  };

  const updateStatus = () => {
    const nodes = model.visibleNodes();
    const edges = model.visibleEdges();
    if (visibleCount) visibleCount.textContent = nodes.length.toLocaleString();
    if (visibleEdges) visibleEdges.textContent = edges.length.toLocaleString();
    if (modeStatus) {
      const label = state.focusIds ? `${state.focusDepth}-hop focus` : search?.value.trim() ? "Search neighborhood" : state.mode === "full" ? "Complete graph" : "Reviewed backbone";
      modeStatus.textContent = label;
    }
    ui.all.textContent = state.mode === "full" && !state.focusIds ? "Backbone" : "Full graph";
  };

  const applyVisibility = (relayout = true) => {
    const context = searchContext();
    let ids = state.pathNodes.size ? new Set(state.pathNodes) : state.focusIds || context || (state.mode === "full" ? null : backboneIds());
    model.nodes.forEach((node) => {
      const included = !ids || ids.has(node.id);
      node.visible = included && reviewAllowed(node) && groupAllowed(node) && datasetAllowed(node);
    });

    model.edges.forEach((edge) => {
      edge.visible = edge.a.visible && edge.b.visible && reviewAllowed(edge) && predicateAllowed(edge);
    });

    if (predicate?.value) {
      const connected = new Set();
      model.edges.forEach((edge) => {
        if (!edge.visible) return;
        connected.add(edge.source);
        connected.add(edge.target);
      });
      model.nodes.forEach((node) => {
        if (!connected.has(node.id) && node !== state.primary && !state.pathNodes.has(node.id)) node.visible = false;
      });
    }

    state.selected = new Set([...state.selected].filter((node) => node.visible));
    if (state.primary && !state.primary.visible && !state.pathNodes.has(state.primary.id)) state.primary = null;
    model.reheat(state.mode === "full" ? 0.35 : 0.8);
    if (relayout) model.applyLayout(model.layout, state.primary, false);
    renderLegend(ui, model.nodes);
    renderDetail(ui, state.primary, state, incident);
    updateStatus();
    scheduleURL();
    invalidate();
  };

  const select = (node, additive = false) => {
    if (!node) {
      if (!additive) {
        state.selected.clear();
        state.primary = null;
      }
    } else if (additive) {
      state.selected.has(node) ? state.selected.delete(node) : state.selected.add(node);
      state.primary = state.selected.has(node) ? node : [...state.selected].at(-1) || null;
    } else {
      state.selected = new Set([node]);
      state.primary = node;
    }
    renderDetail(ui, state.primary, state, incident);
    scheduleURL();
    invalidate();
  };

  const focus = (depth = 1) => {
    if (!state.primary) return;
    state.focusDepth = depth;
    const raw = model.neighborhood(state.primary, depth);
    state.focusIds = capIds(raw, model.nodeMap, MAX_FOCUS, new Set([state.primary.id]));
    applyVisibility();
    fit(model.visibleNodes(), true);
    if (raw.size > state.focusIds.size) {
      ui.status.textContent = `Focus capped at ${MAX_FOCUS} nodes`;
      setTimeout(() => { ui.status.textContent = ""; }, 2500);
    }
  };

  const showBackbone = () => {
    state.mode = "backbone";
    state.focusIds = null;
    state.focusDepth = 1;
    if (search) search.value = "";
    applyVisibility();
    fit(model.visibleNodes(), true);
  };

  const showFull = () => {
    state.mode = "full";
    state.focusIds = null;
    state.focusDepth = 1;
    applyVisibility();
    fit(model.visibleNodes(), true);
  };

  const fit = (nodes, animate = true) => {
    const active = nodes.filter(Boolean);
    if (!active.length) return;
    let minX = Infinity;
    let minY = Infinity;
    let maxX = -Infinity;
    let maxY = -Infinity;
    active.forEach((node) => {
      minX = Math.min(minX, node.x - node.radius - 25);
      minY = Math.min(minY, node.y - node.radius - 25);
      maxX = Math.max(maxX, node.x + node.radius + 25);
      maxY = Math.max(maxY, node.y + node.radius + 25);
    });
    const targetScale = clamp(Math.min((renderer.width - 40) / Math.max(1, maxX - minX), (renderer.height - 40) / Math.max(1, maxY - minY)), 0.06, 4);
    const targetPan = { x: renderer.width / 2 - (minX + maxX) / 2 * targetScale, y: renderer.height / 2 - (minY + maxY) / 2 * targetScale };
    if (!animate) {
      state.scale = targetScale;
      state.pan = targetPan;
      scheduleURL();
      invalidate();
      return;
    }
    const startScale = state.scale;
    const startPan = { ...state.pan };
    const started = performance.now();
    const step = (now) => {
      const progress = clamp((now - started) / 280, 0, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      state.scale = startScale + (targetScale - startScale) * eased;
      state.pan.x = startPan.x + (targetPan.x - startPan.x) * eased;
      state.pan.y = startPan.y + (targetPan.y - startPan.y) * eased;
      invalidate();
      if (progress < 1) requestAnimationFrame(step); else scheduleURL();
    };
    requestAnimationFrame(step);
  };

  const allowedPathEdges = () => model.edges.filter((edge) => reviewAllowed(edge) && predicateAllowed(edge));
  const applyPath = (index, shouldFit = true) => {
    const path = state.paths[index];
    state.activePath = path ? index : -1;
    state.pathNodes = new Set(path?.nodes || []);
    state.pathEdges = new Set((path?.edges || []).map(edgeKey));
    applyVisibility(false);
    renderPaths(ui, state.paths, state.activePath, model.nodeMap, state.pathStart, state.pathEnd);
    if (path && shouldFit) fit(path.nodes.map((id) => model.nodeMap.get(id)), true);
    scheduleURL();
  };
  const calculatePaths = (activate = true) => {
    state.pathStart = resolve(ui.pathStart.value) || state.pathStart;
    state.pathEnd = resolve(ui.pathEnd.value) || state.pathEnd;
    ui.pathStart.value = state.pathStart || "";
    ui.pathEnd.value = state.pathEnd || "";
    state.paths = findPaths(model.nodes, allowedPathEdges(), state.pathStart, state.pathEnd, 5, 9);
    ui.path.open = true;
    if (activate && state.paths.length) applyPath(0, true);
    else {
      state.activePath = -1;
      state.pathNodes.clear();
      state.pathEdges.clear();
      applyVisibility(false);
      renderPaths(ui, state.paths, -1, model.nodeMap, state.pathStart, state.pathEnd);
    }
  };
  const clearPath = () => {
    state.pathStart = null;
    state.pathEnd = null;
    state.paths = [];
    state.activePath = -1;
    state.pathNodes.clear();
    state.pathEdges.clear();
    ui.pathStart.value = "";
    ui.pathEnd.value = "";
    renderPaths(ui, [], -1, model.nodeMap, null, null);
    applyVisibility(false);
  };
  const twoSelected = () => {
    const picks = [...state.selected];
    if (picks.length !== 2) {
      ui.path.open = true;
      ui.pathResults.innerHTML = '<p class="graph-path-empty">Select exactly two nodes with Shift-click first.</p>';
      return;
    }
    state.pathStart = picks[0].id;
    state.pathEnd = picks[1].id;
    ui.pathStart.value = state.pathStart;
    ui.pathEnd.value = state.pathEnd;
    calculatePaths(true);
  };

  const serialize = () => {
    const next = new URL(location.href);
    [...URL_KEYS, ...EXTRA_URL_KEYS].forEach((key) => next.searchParams.delete(key));
    if (model.layout !== "force") next.searchParams.set("layout", model.layout);
    if (filter?.value) next.searchParams.set("type", filter.value);
    if (review?.value !== "reviewed") next.searchParams.set("review", review?.value || "all");
    if (predicate?.value) next.searchParams.set("predicate", predicate.value);
    if (dataset?.value) next.searchParams.set("dataset", dataset.value);
    if (search?.value.trim()) next.searchParams.set("q", search.value.trim());
    if (state.mode !== "backbone") next.searchParams.set("mode", state.mode);
    if (state.edgeLabels) next.searchParams.set("relations", "1");
    if (state.primary) next.searchParams.set("node", state.primary.id);
    if (state.focusIds && state.primary) {
      next.searchParams.set("focus", state.primary.id);
      next.searchParams.set("depth", String(state.focusDepth));
    }
    if (state.pathStart) next.searchParams.set("from", state.pathStart);
    if (state.pathEnd) next.searchParams.set("to", state.pathEnd);
    if (state.activePath >= 0) next.searchParams.set("route", String(state.activePath));
    next.searchParams.set("scale", state.scale.toFixed(4));
    next.searchParams.set("panx", state.pan.x.toFixed(1));
    next.searchParams.set("pany", state.pan.y.toFixed(1));
    return next;
  };
  const syncURL = () => {
    if (state.restoring) return;
    const next = serialize();
    history.replaceState(null, "", `${next.pathname}${next.search}${next.hash}`);
  };
  function scheduleURL() {
    if (state.restoring) return;
    clearTimeout(state.urlTimer);
    state.urlTimer = setTimeout(syncURL, 140);
  }

  const restore = () => {
    state.restoring = true;
    const params = new URLSearchParams(location.search);
    const layout = params.get("layout") || "force";
    model.layout = ["force", "hierarchical", "radial", "concentric", "grid"].includes(layout) ? layout : "force";
    ui.layout.value = model.layout;
    if (filter) filter.value = params.get("type") || "";
    if (review) review.value = params.get("review") === "all" ? "" : params.get("review") || "reviewed";
    if (predicate) predicate.value = params.get("predicate") || "";
    if (dataset) dataset.value = params.get("dataset") || "";
    if (search) search.value = params.get("q") || "";
    state.mode = params.get("mode") === "full" ? "full" : "backbone";
    state.edgeLabels = params.get("relations") === "1";
    ui.labels.checked = state.edgeLabels;
    state.primary = model.nodeMap.get(params.get("node")) || null;
    state.selected = state.primary ? new Set([state.primary]) : new Set();
    const focusNode = model.nodeMap.get(params.get("focus"));
    state.focusDepth = clamp(Number(params.get("depth")) || 1, 1, 2);
    state.focusIds = focusNode ? capIds(model.neighborhood(focusNode, state.focusDepth), model.nodeMap, MAX_FOCUS, new Set([focusNode.id])) : null;
    if (focusNode && !state.primary) {
      state.primary = focusNode;
      state.selected = new Set([focusNode]);
    }
    state.pathStart = model.nodeMap.has(params.get("from")) ? params.get("from") : null;
    state.pathEnd = model.nodeMap.has(params.get("to")) ? params.get("to") : null;
    ui.pathStart.value = state.pathStart || "";
    ui.pathEnd.value = state.pathEnd || "";
    state.paths = state.pathStart && state.pathEnd ? findPaths(model.nodes, allowedPathEdges(), state.pathStart, state.pathEnd, 5, 9) : [];
    state.activePath = state.paths.length ? clamp(Number(params.get("route")) || 0, 0, state.paths.length - 1) : -1;
    const route = state.paths[state.activePath];
    state.pathNodes = new Set(route?.nodes || []);
    state.pathEdges = new Set((route?.edges || []).map(edgeKey));
    if (route) ui.path.open = true;
    const scale = Number(params.get("scale"));
    const x = Number(params.get("panx"));
    const y = Number(params.get("pany"));
    if (Number.isFinite(scale)) state.scale = clamp(scale, 0.06, 5);
    if (Number.isFinite(x)) state.pan.x = x;
    if (Number.isFinite(y)) state.pan.y = y;
    applyVisibility(false);
    model.applyLayout(model.layout, state.primary, model.layout !== "force");
    renderPaths(ui, state.paths, state.activePath, model.nodeMap, state.pathStart, state.pathEnd);
    renderDetail(ui, state.primary, state, incident);
    state.restoring = false;
  };

  const copyLink = async (pathOnly = false) => {
    syncURL();
    try {
      await navigator.clipboard.writeText(location.href);
    } catch (_) {
      const input = document.createElement("input");
      input.value = location.href;
      document.body.appendChild(input);
      input.select();
      document.execCommand("copy");
      input.remove();
    }
    ui.status.textContent = pathOnly ? "Path copied" : "Copied";
    setTimeout(() => { ui.status.textContent = ""; }, 1800);
  };

  renderer.resize();
  populateNodeOptions(ui, model.nodes);
  restore();
  if (!new URLSearchParams(location.search).has("scale")) requestAnimationFrame(() => fit(model.visibleNodes(), false));

  canvas.addEventListener("pointerdown", (event) => {
    const position = point(event);
    const node = renderer.nearest(position, view());
    canvas.setPointerCapture(event.pointerId);
    if (node) {
      select(node, event.shiftKey);
      state.drag = { node, last: position };
      node.vx = 0;
      node.vy = 0;
      model.reheat(0.55);
    } else {
      if (!event.shiftKey) select(null, false);
      state.drag = { pan: true, last: position };
    }
    invalidate();
  });
  canvas.addEventListener("pointermove", (event) => {
    const position = point(event);
    const hover = renderer.nearest(position, view());
    if (hover !== state.hover) {
      state.hover = hover;
      invalidate();
    }
    canvas.style.cursor = state.hover ? "pointer" : state.drag ? "grabbing" : "grab";
    if (!state.drag) return;
    if (state.drag.pan) {
      state.pan.x += position.x - state.drag.last.x;
      state.pan.y += position.y - state.drag.last.y;
      state.drag.last = position;
      scheduleURL();
    } else {
      const world = renderer.world(position, view());
      const node = state.drag.node;
      node.x = world.x;
      node.y = world.y;
      node.vx = 0;
      node.vy = 0;
      if (model.layout !== "force") {
        node.tx = world.x;
        node.ty = world.y;
      }
      model.reheat(0.35);
    }
    invalidate();
  });
  canvas.addEventListener("pointerup", (event) => {
    if (canvas.hasPointerCapture(event.pointerId)) canvas.releasePointerCapture(event.pointerId);
    state.drag = null;
    scheduleURL();
    invalidate();
  });
  canvas.addEventListener("pointercancel", () => { state.drag = null; invalidate(); });
  canvas.addEventListener("pointerleave", () => { if (!state.drag) { state.hover = null; invalidate(); } });
  canvas.addEventListener("dblclick", (event) => {
    const node = renderer.nearest(point(event), view());
    if (node?.href) location.href = node.href;
  });
  canvas.addEventListener("contextmenu", (event) => {
    event.preventDefault();
    const node = renderer.nearest(point(event), view());
    if (node) {
      select(node, false);
      focus(1);
    }
  });
  canvas.addEventListener("wheel", (event) => {
    event.preventDefault();
    const position = point(event);
    const old = state.scale;
    state.scale = clamp(state.scale * (event.deltaY < 0 ? 1.13 : 0.885), 0.06, 5);
    state.pan.x = position.x - (position.x - state.pan.x) * (state.scale / old);
    state.pan.y = position.y - (position.y - state.pan.y) * (state.scale / old);
    scheduleURL();
    invalidate();
  }, { passive: false });

  search?.addEventListener("input", () => { state.focusIds = null; applyVisibility(); fit(model.visibleNodes(), true); });
  filter?.addEventListener("input", () => { applyVisibility(); fit(model.visibleNodes(), true); });
  review?.addEventListener("input", () => { applyVisibility(); fit(model.visibleNodes(), true); });
  predicate?.addEventListener("input", () => { applyVisibility(false); fit(model.visibleNodes(), true); });
  dataset?.addEventListener("input", () => { applyVisibility(); fit(model.visibleNodes(), true); });
  reset?.addEventListener("click", () => fit(model.visibleNodes(), true));
  detailToggle?.addEventListener("click", () => { document.body.classList.toggle("graph-details-collapsed"); renderer.resize(); fit(model.visibleNodes(), true); });
  ui.layout.addEventListener("change", () => {
    model.applyLayout(ui.layout.value, state.primary, ui.layout.value !== "force");
    requestAnimationFrame(() => fit(model.visibleNodes(), true));
    invalidate();
  });
  ui.labels.addEventListener("change", () => { state.edgeLabels = ui.labels.checked; scheduleURL(); invalidate(); });
  ui.focus.addEventListener("click", () => focus(1));
  ui.all.addEventListener("click", () => state.mode === "full" && !state.focusIds ? showBackbone() : showFull());
  ui.share.addEventListener("click", () => copyLink(false));
  ui.legend.addEventListener("click", (event) => {
    const button = event.target.closest("[data-group]");
    if (!button || !filter) return;
    filter.value = filter.value === button.dataset.group ? "" : button.dataset.group;
    applyVisibility();
    fit(model.visibleNodes(), true);
  });
  ui.detail.addEventListener("click", (event) => {
    const nodeButton = event.target.closest("[data-node-id]");
    if (nodeButton) {
      const node = model.nodeMap.get(nodeButton.dataset.nodeId);
      if (node) {
        if (!node.visible) {
          state.focusIds = capIds(model.neighborhood(node, 1), model.nodeMap, MAX_CONTEXT, new Set([node.id]));
          applyVisibility();
        }
        select(node, false);
        const position = renderer.screen(node, view());
        state.pan.x += renderer.width / 2 - position.x;
        state.pan.y += renderer.height / 2 - position.y;
        scheduleURL();
        invalidate();
      }
      return;
    }
    const action = event.target.closest("[data-action]")?.dataset.action;
    if (action === "focus-1") focus(1);
    if (action === "focus-2") focus(2);
    if (action === "show-all") showFull();
    if (action === "path-start" && state.primary) {
      state.pathStart = state.primary.id;
      ui.pathStart.value = state.pathStart;
      ui.path.open = true;
      state.pathEnd ? calculatePaths(true) : renderPaths(ui, [], -1, model.nodeMap, state.pathStart, state.pathEnd);
      renderDetail(ui, state.primary, state, incident);
    }
    if (action === "path-end" && state.primary) {
      state.pathEnd = state.primary.id;
      ui.pathEnd.value = state.pathEnd;
      ui.path.open = true;
      state.pathStart ? calculatePaths(true) : renderPaths(ui, [], -1, model.nodeMap, state.pathStart, state.pathEnd);
      renderDetail(ui, state.primary, state, incident);
    }
    if (action === "pin" && state.primary) {
      state.primary.pinned = !state.primary.pinned;
      state.primary.vx = 0;
      state.primary.vy = 0;
      renderDetail(ui, state.primary, state, incident);
    }
    invalidate();
  });
  ui.path.addEventListener("click", (event) => {
    const route = event.target.closest("[data-path-index]");
    if (route) {
      applyPath(Number(route.dataset.pathIndex), true);
      return;
    }
    const action = event.target.closest("[data-path-action]")?.dataset.pathAction;
    if (action === "selected") twoSelected();
    if (action === "find") calculatePaths(true);
    if (action === "clear") clearPath();
    if (action === "copy") copyLink(true);
  });
  ui.pathStart.addEventListener("change", () => { state.pathStart = resolve(ui.pathStart.value); scheduleURL(); });
  ui.pathEnd.addEventListener("change", () => { state.pathEnd = resolve(ui.pathEnd.value); scheduleURL(); });
  window.addEventListener("resize", () => { renderer.resize(); model.reheat(0.3); scheduleURL(); invalidate(); });
  window.addEventListener("popstate", restore);
  window.addEventListener("keydown", (event) => {
    if (event.key === "Escape") showBackbone();
    if (event.key.toLowerCase() === "f" && !/input|select|textarea/i.test(document.activeElement?.tagName || "")) fit(model.visibleNodes(), true);
  });

  const loop = () => {
    if (!document.hidden) {
      if (model.alpha > 0 || state.drag?.node) {
        model.simulate(state.drag?.node || null);
        state.dirty = true;
      }
      if (state.dirty) {
        renderer.draw(view());
        state.dirty = false;
      }
    }
    frame = requestAnimationFrame(loop);
  };
  if (frame) cancelAnimationFrame(frame);
  loop();
  renderLegend(ui, model.nodes);
  renderDetail(ui, state.primary, state, incident);
  renderPaths(ui, state.paths, state.activePath, model.nodeMap, state.pathStart, state.pathEnd);
}

function buildBackbone(nodes, include) {
  const picks = new Set();
  const groups = new Map();
  nodes.forEach((node) => {
    if (!include(node)) return;
    if (!groups.has(node.group)) groups.set(node.group, []);
    groups.get(node.group).push(node);
  });
  groups.forEach((items) => items.sort((a, b) => b.degree - a.degree).slice(0, 3).forEach((node) => picks.add(node.id)));
  [...nodes].filter(include).sort((a, b) => b.degree - a.degree || (a.label || a.id).localeCompare(b.label || b.id)).forEach((node) => {
    if (picks.size < MAX_BACKBONE) picks.add(node.id);
  });
  return picks;
}

function capIds(ids, nodeMap, limit, required = new Set()) {
  if (!ids || ids.size <= limit) return ids;
  const result = new Set(required);
  [...ids].map((id) => nodeMap.get(id)).filter(Boolean).sort((a, b) => b.degree - a.degree || (a.label || a.id).localeCompare(b.label || b.id)).forEach((node) => {
    if (result.size < limit) result.add(node.id);
  });
  return result;
}
