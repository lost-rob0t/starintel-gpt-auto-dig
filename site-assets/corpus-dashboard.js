(() => {
  "use strict";

  const DAY_MS = 86400000;
  const D3_URL = "https://cdn.jsdelivr.net/npm/d3@7.9.0/dist/d3.min.js";
  const PALETTE = [
    "var(--accent)", "var(--warm)", "var(--success)", "var(--purple)",
    "var(--orange)", "var(--teal)", "var(--blue)", "var(--pink)", "var(--neutral)"
  ];
  const VIEW_ICONS = Object.freeze({
    cards: '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>',
    table: '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="4" width="18" height="16" rx="1"/><path d="M3 9h18M3 14h18M9 4v16M15 4v16"/></svg>'
  });
  let d3Promise = null;

  function number(value) {
    return new Intl.NumberFormat().format(Number(value || 0));
  }

  function compactNumber(value) {
    const numeric = Number(value || 0);
    if (Math.abs(numeric) < 1000) return number(Math.round(numeric));
    return new Intl.NumberFormat(undefined, {
      notation: "compact",
      maximumFractionDigits: Math.abs(numeric) >= 100000 ? 0 : 1
    }).format(numeric);
  }

  function escapeHtml(value) {
    return String(value ?? "").replace(/[&<>'"]/g, (char) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;"
    })[char]);
  }

  function loadD3() {
    if (window.d3?.scaleSymlog && window.d3?.scaleUtc) return Promise.resolve(window.d3);
    if (d3Promise) return d3Promise;
    d3Promise = new Promise((resolve, reject) => {
      const script = document.createElement("script");
      script.src = D3_URL;
      script.async = true;
      script.crossOrigin = "anonymous";
      script.addEventListener("load", () => {
        if (window.d3?.scaleSymlog && window.d3?.scaleUtc) resolve(window.d3);
        else reject(new Error("D3 loaded without required scale modules"));
      }, { once: true });
      script.addEventListener("error", () => reject(new Error("D3 chart runtime failed to load")), { once: true });
      document.head.appendChild(script);
    });
    return d3Promise;
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

  function scaleProfile(d3, rows) {
    const counts = rows.map((row) => Math.max(0, Number(row.count || 0)));
    const positive = counts.filter((value) => value > 0).sort((left, right) => left - right);
    const max = d3.max(counts) || 1;
    const median = d3.median(positive) || 1;
    const lowerQuartile = d3.quantileSorted(positive, 0.25) || median;
    const zeroShare = counts.length ? counts.filter((value) => value === 0).length / counts.length : 0;
    const skew = max / Math.max(median, 1);
    const symlog = max >= 10000 && (skew >= 12 || zeroShare >= 0.45);
    const constant = Math.max(1, Math.min(lowerQuartile, max / 1000));
    return { max, symlog, constant };
  }

  function symlogTicks(d3, scale, count = 6) {
    const [bottom, top] = scale.range();
    const values = d3.range(count).map((index) => {
      const ratio = index / Math.max(count - 1, 1);
      return Math.max(0, Math.round(scale.invert(bottom + (top - bottom) * ratio)));
    });
    return [...new Set(values)];
  }

  function renderLine(container, rows) {
    if (container._lineResizeObserver) {
      container._lineResizeObserver.disconnect();
      container._lineResizeObserver = null;
    }
    container.replaceChildren();
    if (!rows.length) {
      container.textContent = "No canonical date_added values in this range.";
      return;
    }

    const d3 = window.d3;
    if (!d3?.scaleSymlog || !d3?.scaleUtc) throw new Error("D3 runtime is unavailable");
    const data = rows.map((row) => ({
      date: parseDay(row.date),
      dateKey: row.date,
      count: Math.max(0, Number(row.count || 0))
    })).filter((row) => row.date);
    if (!data.length) {
      container.textContent = "No canonical date_added values in this range.";
      return;
    }

    let lastWidth = 0;
    let frameRequest = 0;

    const draw = () => {
      const measured = Math.floor(container.getBoundingClientRect().width || 960);
      const width = Math.max(360, measured);
      if (Math.abs(width - lastWidth) < 2) return;
      lastWidth = width;
      container.replaceChildren();

      const height = Math.max(320, Math.min(430, Math.round(width * 0.42)));
      const margin = { top: 20, right: 24, bottom: 48, left: width < 560 ? 58 : 72 };
      const plotWidth = width - margin.left - margin.right;
      const plotHeight = height - margin.top - margin.bottom;
      const profile = scaleProfile(d3, data);
      const firstDate = data[0].date;
      const lastDate = data.at(-1).date;
      const xDomain = firstDate.getTime() === lastDate.getTime()
        ? [new Date(firstDate.getTime() - DAY_MS / 2), new Date(lastDate.getTime() + DAY_MS / 2)]
        : [firstDate, lastDate];
      const x = d3.scaleUtc().domain(xDomain).range([margin.left, width - margin.right]);
      const y = profile.symlog
        ? d3.scaleSymlog().constant(profile.constant).domain([0, profile.max * 1.03]).nice().range([height - margin.bottom, margin.top])
        : d3.scaleLinear().domain([0, profile.max]).nice(5).range([height - margin.bottom, margin.top]);
      const yTicks = profile.symlog ? symlogTicks(d3, y) : y.ticks(5);
      const xTickCount = Math.max(3, Math.min(8, Math.floor(plotWidth / 105)));
      const shell = document.createElement("div");
      shell.style.cssText = "position:relative;width:100%";
      const tooltip = document.createElement("div");
      tooltip.setAttribute("role", "status");
      tooltip.style.cssText = "position:absolute;display:none;z-index:5;pointer-events:none;min-width:9rem;padding:.55rem .65rem;border:1px solid var(--line);border-radius:.45rem;background:color-mix(in srgb,var(--panel) 96%,transparent);box-shadow:0 10px 28px color-mix(in srgb,var(--bg) 72%,transparent);color:var(--text);font:600 .72rem 'IBM Plex Mono',ui-monospace,monospace";
      const chart = d3.select(shell).append("svg")
        .attr("class", "line-chart")
        .attr("viewBox", `0 0 ${width} ${height}`)
        .attr("width", width)
        .attr("height", height)
        .attr("role", "img")
        .attr("aria-label", `Documents added by canonical date_added over time using ${profile.symlog ? "adaptive symlog" : "linear"} scaling`);

      const grid = chart.append("g")
        .attr("transform", `translate(${margin.left},0)`)
        .call(d3.axisLeft(y).tickValues(yTicks).tickSize(-plotWidth).tickFormat(""));
      grid.select(".domain").remove();
      grid.selectAll(".tick line")
        .attr("stroke", "var(--line)")
        .attr("stroke-opacity", 0.42)
        .attr("shape-rendering", "crispEdges");

      const yAxis = chart.append("g")
        .attr("transform", `translate(${margin.left},0)`)
        .call(d3.axisLeft(y).tickValues(yTicks).tickSize(0).tickPadding(10).tickFormat(compactNumber));
      yAxis.select(".domain").remove();
      yAxis.selectAll("text")
        .attr("fill", "var(--muted)")
        .style("font", "600 11px 'IBM Plex Mono',ui-monospace,monospace");

      const xAxis = chart.append("g")
        .attr("transform", `translate(0,${height - margin.bottom})`)
        .call(d3.axisBottom(x).ticks(xTickCount).tickSize(6).tickPadding(10).tickFormat(d3.utcFormat("%b %-d")));
      xAxis.select(".domain").attr("stroke", "var(--line)");
      xAxis.selectAll("line").attr("stroke", "var(--line)");
      xAxis.selectAll("text")
        .attr("fill", "var(--muted)")
        .style("font", "600 11px 'IBM Plex Mono',ui-monospace,monospace");

      const area = d3.area()
        .x((row) => x(row.date))
        .y0(y(0))
        .y1((row) => y(row.count));
      const line = d3.line()
        .x((row) => x(row.date))
        .y((row) => y(row.count));

      chart.append("path").datum(data).attr("class", "line-area").attr("d", area);
      chart.append("path").datum(data).attr("class", "line-path").attr("d", line);

      const active = chart.append("g").selectAll("circle")
        .data(data.filter((row) => row.count > 0))
        .join("circle")
        .attr("class", "line-point")
        .attr("cx", (row) => x(row.date))
        .attr("cy", (row) => y(row.count))
        .attr("r", 5.25)
        .attr("tabindex", 0)
        .attr("aria-label", (row) => `${row.dateKey}: ${number(row.count)} documents added`);
      active.append("title").text((row) => `${row.dateKey}: ${number(row.count)} documents added`);

      const focus = chart.append("g").style("display", "none").attr("aria-hidden", "true");
      focus.append("line")
        .attr("y1", margin.top)
        .attr("y2", height - margin.bottom)
        .attr("stroke", "var(--accent-2)")
        .attr("stroke-opacity", 0.55)
        .attr("stroke-dasharray", "3 4");
      focus.append("circle")
        .attr("r", 6.5)
        .attr("fill", "var(--bg)")
        .attr("stroke", "var(--warm)")
        .attr("stroke-width", 3);
      const bisect = d3.bisector((row) => row.date).center;

      const hideFocus = () => {
        focus.style("display", "none");
        tooltip.style.display = "none";
      };
      const showFocus = (row) => {
        const px = x(row.date);
        const py = y(row.count);
        focus.style("display", null);
        focus.select("line").attr("x1", px).attr("x2", px);
        focus.select("circle").attr("cx", px).attr("cy", py);
        tooltip.innerHTML = `<strong style="display:block;color:var(--text-strong);font-size:.78rem">${escapeHtml(row.dateKey)}</strong><span style="display:block;margin-top:.18rem;color:var(--accent-2)">${number(row.count)} documents</span>`;
        tooltip.style.display = "block";
        tooltip.style.left = `${Math.max(4, Math.min(width - 164, px + 12))}px`;
        tooltip.style.top = `${Math.max(4, py - 58)}px`;
      };

      chart.append("rect")
        .attr("x", margin.left)
        .attr("y", margin.top)
        .attr("width", plotWidth)
        .attr("height", plotHeight)
        .attr("fill", "transparent")
        .style("cursor", "crosshair")
        .on("pointermove", function (event) {
          const [px] = d3.pointer(event, this);
          const date = x.invert(px);
          const index = Math.max(0, Math.min(data.length - 1, bisect(data, date)));
          showFocus(data[index]);
        })
        .on("pointerleave", hideFocus);

      shell.appendChild(tooltip);
      container.appendChild(shell);

      const total = data.reduce((sum, row) => sum + row.count, 0);
      const activeDays = data.filter((row) => row.count > 0).length;
      const caption = document.createElement("div");
      caption.setAttribute("role", "status");
      caption.style.cssText = "display:flex;flex-wrap:wrap;gap:.65rem 1.25rem;margin:.55rem 0 0;color:var(--muted);font:600 .72rem 'IBM Plex Mono',ui-monospace,monospace";
      caption.innerHTML = `<span>${escapeHtml(data[0].dateKey)} → ${escapeHtml(data.at(-1).dateKey)}</span><span>${number(total)} documents</span><span>${number(activeDays)} active days</span><span>scale: ${profile.symlog ? "adaptive symlog" : "linear"} · D3 v7</span><span>source: canonical <code>date_added</code></span>`;
      container.appendChild(caption);
    };

    draw();
    if ("ResizeObserver" in window) {
      const observer = new ResizeObserver(() => {
        cancelAnimationFrame(frameRequest);
        frameRequest = requestAnimationFrame(draw);
      });
      observer.observe(container);
      container._lineResizeObserver = observer;
    }
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
        let activeRange = "90";
        const renderRange = (range) => {
          activeRange = range;
          lineTarget.textContent = "Loading chart runtime…";
          loadD3()
            .then(() => {
              if (activeRange === range) renderLine(lineTarget, rowsForRange(allRows, range));
            })
            .catch((error) => {
              lineTarget.textContent = `Chart unavailable: ${error.message}`;
              lineTarget.classList.add("chart-error");
            });
        };

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