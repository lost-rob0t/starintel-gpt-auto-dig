(() => {
  "use strict";

  const NS = "http://www.w3.org/2000/svg";
  const PALETTE = ["var(--accent)", "var(--warm)", "var(--success)", "var(--purple)", "var(--orange)", "var(--teal)", "var(--blue)", "var(--pink)", "var(--neutral)"];

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

  function renderLine(container, rows) {
    container.replaceChildren();
    if (!rows.length) {
      container.textContent = "No dated documents in this range.";
      return;
    }
    const width = 900;
    const height = 280;
    const pad = 28;
    const max = Math.max(...rows.map((row) => Number(row.count || 0)), 1);
    const chart = svg("svg", { viewBox: `0 0 ${width} ${height}`, role: "img", "aria-label": "Documents added over time" });
    chart.classList.add("line-chart");
    const baseline = svg("line", { x1: pad, x2: width - pad, y1: height - pad, y2: height - pad, class: "chart-axis" });
    chart.appendChild(baseline);
    const points = rows.map((row, index) => {
      const x = pad + (index / Math.max(rows.length - 1, 1)) * (width - pad * 2);
      const y = height - pad - (Number(row.count || 0) / max) * (height - pad * 2);
      return [x, y, row];
    });
    const area = svg("path", {
      d: `M ${points[0][0]} ${height - pad} L ${points.map(([x, y]) => `${x} ${y}`).join(" L ")} L ${points.at(-1)[0]} ${height - pad} Z`,
      class: "line-area"
    });
    const path = svg("path", { d: `M ${points.map(([x, y]) => `${x} ${y}`).join(" L ")}`, class: "line-path" });
    chart.append(area, path);
    points.forEach(([x, y, row]) => {
      const point = svg("circle", { cx: x, cy: y, r: 3.2, tabindex: 0, class: "line-point" });
      const title = svg("title");
      title.textContent = `${row.date}: ${number(row.count)} documents`;
      point.appendChild(title);
      chart.appendChild(point);
    });
    container.appendChild(chart);
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
    const source = root.dataset.dashboard;
    fetch(source)
      .then((response) => {
        if (!response.ok) throw new Error(`dashboard data ${response.status}`);
        return response.json();
      })
      .then((data) => {
        const lineTarget = document.getElementById("documents-by-day-chart");
        const typeTarget = document.getElementById("document-types-chart");
        const relationTarget = document.getElementById("relation-types-chart");
        const renderRange = (range) => {
          const rows = data.documents_by_day || [];
          if (range === "all") return renderLine(lineTarget, rows);
          renderLine(lineTarget, rows.slice(-Number(range)));
        };
        renderRange(90);
        renderDonut(typeTarget, data.document_types || []);
        renderBars(relationTarget, data.relation_types || []);
        root.querySelectorAll("[data-range]").forEach((button) => {
          button.addEventListener("click", () => {
            root.querySelectorAll("[data-range]").forEach((other) => other.classList.toggle("active", other === button));
            renderRange(button.dataset.range);
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

  function mountDatasets(root) {
    const search = document.getElementById("dataset-search");
    const sort = document.getElementById("dataset-sort");
    const summary = document.getElementById("dataset-summary");
    const cards = document.getElementById("dataset-card-grid");
    const tableWrap = document.getElementById("dataset-table-wrap");
    const tableBody = document.getElementById("dataset-table-body");
    let catalog = [];
    let kind = "all";
    let view = "cards";

    function render() {
      const query = search.value.trim().toLowerCase();
      const rows = catalog.filter((row) => {
        if (kind !== "all" && row.kind !== kind) return false;
        if (!query) return true;
        return [row.title, row.dataset, row.target_title, row.id].some((value) => String(value || "").toLowerCase().includes(query));
      });
      const comparators = {
        activity: (a, b) => Number(b.added_30d || 0) - Number(a.added_30d || 0) || Number(b.record_count || 0) - Number(a.record_count || 0),
        records: (a, b) => Number(b.record_count || 0) - Number(a.record_count || 0),
        sources: (a, b) => Number(b.source_count || 0) - Number(a.source_count || 0),
        updated: (a, b) => String(b.updated_through || "").localeCompare(String(a.updated_through || "")),
        name: (a, b) => String(a.title || a.dataset || "").localeCompare(String(b.title || b.dataset || ""))
      };
      rows.sort(comparators[sort.value] || comparators.activity);
      summary.textContent = `${number(rows.length)} of ${number(catalog.length)} datasets`;
      cards.innerHTML = rows.map(datasetCard).join("");
      tableBody.innerHTML = rows.map(datasetTableRow).join("");
      cards.hidden = view !== "cards";
      tableWrap.hidden = view !== "table";
    }

    fetch(root.dataset.catalog)
      .then((response) => {
        if (!response.ok) throw new Error(`catalog ${response.status}`);
        return response.json();
      })
      .then((rows) => {
        catalog = rows;
        render();
      })
      .catch((error) => { summary.textContent = `Dataset catalog unavailable: ${error.message}`; });

    search.addEventListener("input", render);
    sort.addEventListener("change", render);
    root.querySelectorAll("[data-kind]").forEach((button) => button.addEventListener("click", () => {
      kind = button.dataset.kind;
      root.querySelectorAll("[data-kind]").forEach((other) => other.classList.toggle("active", other === button));
      render();
    }));
    root.querySelectorAll("[data-view]").forEach((button) => button.addEventListener("click", () => {
      view = button.dataset.view;
      root.querySelectorAll("[data-view]").forEach((other) => other.classList.toggle("active", other === button));
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
