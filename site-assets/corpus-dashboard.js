(() => {
  "use strict";

  const NS = "http://www.w3.org/2000/svg";
  const DAY_MS = 86400000;
  const PALETTE = [
    "var(--accent)", "var(--warm)", "var(--success)", "var(--purple)",
    "var(--orange)", "var(--teal)", "var(--blue)", "var(--pink)", "var(--neutral)"
  ];
  const VIEW_ICONS = Object.freeze({
    cards: '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>',
    table: '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="4" width="18" height="16" rx="1"/><path d="M3 9h18M3 14h18M9 4v16M15 4v16"/></svg>'
  });

  function number(value) {
    return new Intl.NumberFormat().format(Number(value || 0));
  }

  function escapeHtml(value) {
    return String(value ?? "").replace(/[&<>'"]/g, (char) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;"
    })[char]);
  }

  function svg(name, attrs = {}) {
    const node = document.createElementNS(NS, name);
    Object.entries(attrs).forEach(([key, value]) => node.setAttribute(key, String(value)));
    return node;
  }

  function parseDay(value) {
    const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(String(value || "").slice(0, 10));
    if (!match) return null;
    const date = new Date(Date.UTC(Number(match[1]), Number(match[2]) - 1, Number(match[3])));
    return Number.isNaN(date.getTime()) ? null : date;
  }

  function dayKey(date) {
    return date.toISOString().slice(0, 10);
  }

  function denseDailyRows(rows) {
    const counts = new Map();
    rows.forEach((row) => {
      const date = parseDay(row.date);
      if (!date) return;
      const key = dayKey(date);
      counts.set(key, (counts.get(key) || 0) + Number(row.count || 0));
    });
    const keys = [...counts.keys()].sort();
    if (!keys.length) return [];
    const first = parseDay(keys[0]);
    const last = parseDay(keys.at(-1));
    const dense = [];
    for (let cursor = first.getTime(); cursor <= last.getTime(); cursor += DAY_MS) {
      const key = dayKey(new Date(cursor));
      dense.push({ date: key, count: counts.get(key) || 0 });
    }
    return dense;
  }

  function rowsForRange(rows, range) {
    if (range === "all" || !rows.length) return rows;
    const days = Number(range);
    if (!Number.isFinite(days) || days <= 0) return rows;
    const last = parseDay(rows.at(-1).date);
    if (!last) return rows;
    const threshold = last.getTime() - (days - 1) * DAY_MS;
    return rows.filter((row) => {
      const date = parseDay(row.date);
      return date && date.getTime() >= threshold;
    });
  }

  function shortDate(value) {
    const date = parseDay(value);
    if (!date) return String(value || "");
    return new Intl.DateTimeFormat(undefined, {
      month: "short", day: "numeric", timeZone: "UTC"
    }).format(date);
  }

  function chooseTicks(length, maxTicks = 7) {
    if (length <= maxTicks) return new Set(Array.from({ length }, (_, index) => index));
    const ticks = new Set([0, length - 1]);
    const step = (length - 1) / (maxTicks - 1);
    for (let index = 1; index < maxTicks - 1; index += 1) ticks.add(Math.round(index * step));
    return ticks;
  }

  function chartLabel(x, y, text, anchor = "middle") {
    const node = svg("text", {
      x,
      y,
      "text-anchor": anchor,
      style: "fill:var(--muted);font:600 11px 'IBM Plex Mono',ui-monospace,monospace;letter-spacing:.01em"
    });
    node.textContent = text;
    return node;
  }

  function renderLine(container, rows) {
    container.replaceChildren();
    if (!rows.length) {
      container.textContent = "No canonical date_added values in this range.";
      return;
    }

    const width = 960;
    const height = 340;
    const left = 62;
    const right = 24;
    const top = 24;
    const bottom = 54;
    const plotWidth = width - left - right;
    const plotHeight = height - top - bottom;
    const maxCount = Math.max(...rows.map((row) => Number(row.count || 0)), 1);
    const roundedMax = Math.max(1, Math.ceil(maxCount / 5) * 5);
    const chart = svg("svg", {
      viewBox: `0 0 ${width} ${height}`,
      role: "img",
      "aria-label": "Documents added by canonical date_added over time"
    });
    chart.classList.add("line-chart");

    for (let tick = 0; tick <= 4; tick += 1) {
      const value = Math.round((roundedMax * tick) / 4);
      const y = top + plotHeight - (value / roundedMax) * plotHeight;
      chart.appendChild(svg("line", {
        x1: left,
        x2: width - right,
        y1: y,
        y2: y,
        style: `stroke:${tick === 0 ? "var(--line)" : "color-mix(in srgb,var(--line) 48%,transparent)"};stroke-width:1`
      }));
      chart.appendChild(chartLabel(left - 10, y + 4, number(value), "end"));
    }

    const points = rows.map((row, index) => {
      const x = left + (index / Math.max(rows.length - 1, 1)) * plotWidth;
      const y = top + plotHeight - (Number(row.count || 0) / roundedMax) * plotHeight;
      return [x, y, row];
    });

    chart.appendChild(svg("path", {
      d: `M ${points[0][0]} ${top + plotHeight} L ${points.map(([x, y]) => `${x} ${y}`).join(" L ")} L ${points.at(-1)[0]} ${top + plotHeight} Z`,
      class: "line-area"
    }));
    chart.appendChild(svg("path", {
      d: `M ${points.map(([x, y]) => `${x} ${y}`).join(" L ")}`,
      class: "line-path"
    }));

    const ticks = chooseTicks(rows.length);
    points.forEach(([x, y, row], index) => {
      if (ticks.has(index)) {
        chart.appendChild(svg("line", {
          x1: x,
          x2: x,
          y1: top + plotHeight,
          y2: top + plotHeight + 6,
          style: "stroke:var(--line);stroke-width:1"
        }));
        chart.appendChild(chartLabel(x, height - 20, shortDate(row.date)));
      }

      const point = svg("circle", {
        cx: x,
        cy: y,
        r: Number(row.count || 0) > 0 ? 5.5 : 3.25,
        tabindex: 0,
        class: "line-point",
        style: Number(row.count || 0) > 0
          ? "fill:var(--bg);stroke:var(--warm);stroke-width:3;cursor:crosshair"
          : "fill:var(--bg);stroke:var(--line);stroke-width:1.5;opacity:.75"
      });
      point.setAttribute("aria-label", `${row.date}: ${number(row.count)} documents added`);
      const title = svg("title");
      title.textContent = `${row.date}: ${number(row.count)} documents added`;
      point.appendChild(title);
      chart.appendChild(point);
    });

    container.appendChild(chart);
    const total = rows.reduce((sum, row) => sum + Number(row.count || 0), 0);
    const activeDays = rows.filter((row) => Number(row.count || 0) > 0).length;
    const caption = document.createElement("div");
    caption.setAttribute("role", "status");
    caption.style.cssText = "display:flex;flex-wrap:wrap;gap:.65rem 1.25rem;margin:.55rem 0 0;color:var(--muted);font:600 .72rem 'IBM Plex Mono',ui-monospace,monospace";
    caption.innerHTML = `<span>${escapeHtml(rows[0].date)} → ${escapeHtml(rows.at(-1).date)}</span><span>${number(total)} documents</span><span>${number(activeDays)} active days</span><span>source: canonical <code>date_added</code></span>`;
    container.appendChild(caption);
  }

  function renderDonut(container, rows) {
    container.replaceChildren();
    const visible = rows.slice(0, 9);
    const total = visible.reduce((sum, row) => sum + Number(row.count || 0), 0);
    if (!total) {
      container.textContent = "No document types available.";
      return;
    }
    let cursor = 0;
    const stops = [];
    visible.forEach((row, index) => {
      const start = cursor;
      cursor += (Number(row.count || 0) / total) * 100;
      stops.push(`${PALETTE[index % PALETTE.length]} ${start}% ${cursor}%`);
    });
    const shell = document.createElement("div");
    shell.className = "donut-shell";
    const donut = document.createElement("div");
    donut.className = "donut-chart";
    donut.style.background = `conic-gradient(${stops.join(",")})`;
    donut.innerHTML = `<div><strong>${number(total)}</strong><span>non-relation docs</span></div>`;
    const legend = document.createElement("ol");
    legend.className = "chart-legend";
    legend.innerHTML = visible.map((row, index) => `<li><i style="--legend-color:${PALETTE[index % PALETTE.length]}"></i><span>${escapeHtml(row.label)}</span><strong>${number(row.count)}</strong></li>`).join("");
    shell.append(donut, legend);
    container.appendChild(shell);
  }

  function renderBars(container, rows) {
    container.replaceChildren();
    const visible = rows.slice(0, 10);
    const max = Math.max(...visible.map((row) => Number(row.count || 0)), 1);
    const list = document.createElement("ol");
    list.className = "relation-bars";
    list.innerHTML = visible.map((row) => {
      const width = Math.max(2, (Number(row.count || 0) / max) * 100);
      return `<li><div><span>${escapeHtml(row.label)}</span><strong>${number(row.count)}</strong></div><i style="--bar-width:${width}%"></i></li>`;
    }).join("");
    container.appendChild(list);
  }

  function mountDashboard(root) {
    fetch(root.dataset.dashboard)
      .then((response) => {
        if (!response.ok) throw new Error(`dashboard data ${response.status}`);
        return response.json();
      })
      .then((data) => {
        const lineTarget = document.getElementById("documents-by-day-chart");
        const typeTarget = document.getElementById("document-types-chart");
        const relationTarget = document.getElementById("relation-types-chart");
        const allRows = denseDailyRows(data.documents_by_day || []);
        const renderRange = (range) => renderLine(lineTarget, rowsForRange(allRows, range));

        renderRange("90");
        renderDonut(typeTarget, data.document_types || []);
        renderBars(relationTarget, data.relation_types || []);

        root.querySelectorAll("[data-range]").forEach((button) => {
          button.type = "button";
          button.setAttribute("aria-pressed", String(button.classList.contains("active")));
          button.addEventListener("click", () => {
            root.querySelectorAll("[data-range]").forEach((other) => {
              const active = other === button;
              other.classList.toggle("active", active);
              other.setAttribute("aria-pressed", String(active));
            });
            renderRange(button.dataset.range || "90");
          });
        });
      })
      .catch((error) => {
        root.querySelectorAll(".chart-frame").forEach((node) => {
          node.textContent = `Chart unavailable: ${error.message}`;
          node.classList.add("chart-error");
        });
      });
  }

  function datasetCard(row) {
    const title = escapeHtml(row.title || row.dataset || row.id);
    const target = row.target_title ? `<span>${escapeHtml(row.target_title)}</span>` : "";
    const download = row.download ? `<a href="${escapeHtml(row.download)}" download>Download</a>` : "";
    return `<article class="dataset-card"><div class="dataset-card-top"><span class="dataset-kind">${escapeHtml(row.kind)}</span><time>${escapeHtml(String(row.updated_through || "").slice(0, 10))}</time></div><h2><a href="${escapeHtml(row.url)}">${title}</a></h2>${target}<div class="dataset-card-metrics"><b>${number(row.record_count)}<small>records</small></b><b>${number(row.source_count)}<small>sources</small></b><b>+${number(row.added_30d)}<small>30d</small></b></div><div class="dataset-card-actions"><a class="primary-action" href="${escapeHtml(row.url)}">Open dashboard →</a>${download}</div></article>`;
  }

  function datasetTableRow(row) {
    const title = escapeHtml(row.title || row.dataset || row.id);
    const download = row.download ? ` · <a href="${escapeHtml(row.download)}" download>download</a>` : "";
    return `<tr><td><strong>${title}</strong>${row.target_title ? `<small>${escapeHtml(row.target_title)}</small>` : ""}</td><td>${escapeHtml(row.kind)}</td><td>${number(row.record_count)}</td><td>${number(row.people_count)}</td><td>${number(row.organization_count)}</td><td>${number(row.relation_count)}</td><td>${number(row.source_count)}</td><td>${number(row.added_30d)}</td><td>${escapeHtml(String(row.updated_through || "").slice(0, 10))}</td><td><a href="${escapeHtml(row.url)}">open</a>${download}</td></tr>`;
  }

  function normalizedDatasetKey(row) {
    return String(row.dataset || row.title || row.id || "")
      .normalize("NFKC")
      .trim()
      .toLowerCase()
      .replace(/[\s_-]+/g, " ");
  }

  function datasetPriority(row) {
    const aggregate = row.kind === "topic" ? 1_000_000_000_000 : 0;
    return aggregate
      + Number(row.record_count || 0) * 1_000_000
      + Number(row.source_count || 0) * 1_000
      + Number(row.added_30d || 0);
  }

  function dedupeCatalog(rows) {
    const unique = new Map();
    rows.forEach((row) => {
      const key = normalizedDatasetKey(row);
      if (!key) return;
      const current = unique.get(key);
      if (!current || datasetPriority(row) > datasetPriority(current)) unique.set(key, row);
    });
    return [...unique.values()];
  }

  function installDatasetControlStyles() {
    if (document.getElementById("dataset-control-hotfix")) return;
    const style = document.createElement("style");
    style.id = "dataset-control-hotfix";
    style.textContent = `
      .segmented button.icon-only-toggle{width:2.35rem;min-width:2.35rem;padding:.35rem;display:inline-grid;place-items:center}
      .segmented button.icon-only-toggle svg{width:1.05rem;height:1.05rem;fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}
      .dataset-table-wrap[hidden],.dataset-card-grid[hidden]{display:none!important}
    `;
    document.head.appendChild(style);
  }

  function iconifyViewButtons(root) {
    root.querySelectorAll("[data-view]").forEach((button) => {
      const view = button.dataset.view;
      const label = view === "table" ? "Table view" : "Card view";
      button.type = "button";
      button.classList.add("icon-only-toggle");
      button.innerHTML = VIEW_ICONS[view] || "";
      button.title = label;
      button.setAttribute("aria-label", label);
      button.setAttribute("aria-pressed", String(button.classList.contains("active")));
    });
  }

  function mountDatasets(root) {
    const search = document.getElementById("dataset-search");
    const sort = document.getElementById("dataset-sort");
    const summary = document.getElementById("dataset-summary");
    const cards = document.getElementById("dataset-card-grid");
    const tableWrap = document.getElementById("dataset-table-wrap");
    const tableBody = document.getElementById("dataset-table-body");
    let catalog = [];
    let rawCatalogCount = 0;
    let kind = "all";
    let view = "cards";

    installDatasetControlStyles();
    iconifyViewButtons(root);
    cards.hidden = false;
    cards.style.display = "grid";
    tableWrap.hidden = true;
    tableWrap.style.display = "none";

    root.querySelectorAll("[data-kind]").forEach((button) => {
      button.type = "button";
      button.setAttribute("aria-pressed", String(button.classList.contains("active")));
    });

    function render() {
      const query = search.value.trim().toLowerCase();
      const rows = catalog.filter((row) => {
        if (kind !== "all" && row.kind !== kind) return false;
        if (!query) return true;
        return [row.title, row.dataset, row.target_title, row.id]
          .some((value) => String(value || "").toLowerCase().includes(query));
      });
      const comparators = {
        activity: (a, b) => Number(b.added_30d || 0) - Number(a.added_30d || 0) || Number(b.record_count || 0) - Number(a.record_count || 0),
        records: (a, b) => Number(b.record_count || 0) - Number(a.record_count || 0),
        sources: (a, b) => Number(b.source_count || 0) - Number(a.source_count || 0),
        updated: (a, b) => String(b.updated_through || "").localeCompare(String(a.updated_through || "")),
        name: (a, b) => String(a.title || a.dataset || "").localeCompare(String(b.title || b.dataset || ""))
      };
      rows.sort(comparators[sort.value] || comparators.activity);
      const dedupeNote = rawCatalogCount > catalog.length ? ` · ${number(rawCatalogCount - catalog.length)} duplicates removed` : "";
      summary.textContent = `${number(rows.length)} of ${number(catalog.length)} unique datasets${dedupeNote}`;
      cards.innerHTML = rows.map(datasetCard).join("");
      tableBody.innerHTML = rows.map(datasetTableRow).join("");

      const showCards = view === "cards";
      cards.hidden = !showCards;
      tableWrap.hidden = showCards;
      cards.style.display = showCards ? "grid" : "none";
      tableWrap.style.display = showCards ? "none" : "block";
    }

    fetch(root.dataset.catalog)
      .then((response) => {
        if (!response.ok) throw new Error(`catalog ${response.status}`);
        return response.json();
      })
      .then((rows) => {
        rawCatalogCount = rows.length;
        catalog = dedupeCatalog(rows);
        render();
      })
      .catch((error) => {
        summary.textContent = `Dataset catalog unavailable: ${error.message}`;
      });

    search.addEventListener("input", render);
    sort.addEventListener("change", render);
    root.querySelectorAll("[data-kind]").forEach((button) => button.addEventListener("click", () => {
      kind = button.dataset.kind;
      root.querySelectorAll("[data-kind]").forEach((other) => {
        const active = other === button;
        other.classList.toggle("active", active);
        other.setAttribute("aria-pressed", String(active));
      });
      render();
    }));
    root.querySelectorAll("[data-view]").forEach((button) => button.addEventListener("click", () => {
      view = button.dataset.view;
      root.querySelectorAll("[data-view]").forEach((other) => {
        const active = other === button;
        other.classList.toggle("active", active);
        other.setAttribute("aria-pressed", String(active));
      });
      render();
    }));
  }

  function mount() {
    const dashboard = document.getElementById("corpus-dashboard");
    if (dashboard) mountDashboard(dashboard);
    const datasets = document.getElementById("dataset-browser");
    if (datasets) mountDatasets(datasets);
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", mount, { once: true });
  else mount();
})();
