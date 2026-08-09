(() => {
  const script = document.currentScript;
  const previewSource = script?.dataset.documents || "documents.json";
  const searchRoot = script?.dataset.searchRoot || "";
  const recordRoot = script?.dataset.recordRoot || "";
  const scope = script?.dataset.scope || "";
  const rootPrefix = script?.dataset.rootPrefix || "";
  const params = new URLSearchParams(location.search);
  const requestedDataset = params.get("dataset") || "";
  const requestedId = params.get("id") || "";
  const requestedLegacy = params.get("legacy") || "";
  const requestedQuery = params.get("q") || "";
  const search = document.getElementById("documents-search");
  const type = document.getElementById("documents-type");
  const review = document.getElementById("documents-review");
  const grid = document.getElementById("documents-grid");
  const summary = document.getElementById("documents-summary");
  const pageLabel = document.getElementById("documents-page");
  const previous = document.getElementById("documents-prev");
  const next = document.getElementById("documents-next");
  if (!grid) return;

  const esc = (value) => String(value ?? "").replace(/[&<>"']/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  })[character]);
  const slug = (value) => String(value || "").toLowerCase().replace(/^starintel:/, "").replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
  const queryPrefix = (value) => {
    const token = String(value || "").toLowerCase().match(/[a-z0-9]{2,}/);
    return token ? token[0].slice(0, 2) : "";
  };
  const pageSize = 36;
  const candidateLimit = 5000;
  let previewRecords = [];
  let searchedRecords = null;
  let page = 0;
  let searchSerial = 0;
  const recordPageCache = new Map();
  let recordPageSize = 2000;

  const decodeRecord = (row) => ({
    target: row[0],
    id: row[1],
    title: row[2],
    dtype: row[3],
    dataset: row[4],
    status: row[5],
    updated: row[6],
    review: "reviewed",
    summary: "",
    url: `${rootPrefix}${row[0]}/documents.html?id=${encodeURIComponent(row[1])}`
  });

  if (requestedDataset && search) search.placeholder = `Search within ${requestedDataset}…`;
  if (requestedId && search) search.value = requestedId;
  else if (requestedLegacy && search) search.value = requestedLegacy;
  else if (requestedQuery && search) search.value = requestedQuery;

  const activeRecords = () => searchedRecords === null ? previewRecords : searchedRecords;
  const filtered = () => {
    const needle = String(search?.value || "").trim().toLowerCase();
    const dtype = type?.value || "";
    const state = review?.value || "";
    return activeRecords().filter((record) => {
      if (requestedDataset && record.dataset !== requestedDataset) return false;
      if (dtype && record.dtype !== dtype) return false;
      if (state && record.review !== state) return false;
      if (!needle) return true;
      return [record.title, record.summary, record.id, slug(record.id), record.dataset, record.dtype]
        .some((value) => String(value || "").toLowerCase().includes(needle));
    });
  };

  const render = () => {
    const matches = filtered();
    const pages = Math.max(1, Math.ceil(matches.length / pageSize));
    page = Math.min(page, pages - 1);
    const start = page * pageSize;
    const slice = matches.slice(start, start + pageSize);
    grid.innerHTML = slice.map((record) => `
      <article data-review="${esc(record.review)}">
        <div class="document-card-meta"><span>${esc(record.dtype)}</span><span class="review-badge ${esc(record.review)}">${esc(record.review)}</span></div>
        <h3><a href="${esc(record.url)}">${esc(record.title)}</a></h3>
        <p>${esc(record.summary || "Canonical metadata result. Open the record context or bulk corpus for the full payload.")}</p>
        <div class="document-card-footer"><code>${esc(record.id)}</code><span>${esc(record.updated || "")}</span></div>
      </article>`).join("");
    const datasetPrefix = requestedDataset ? `${requestedDataset} · ` : "";
    const mode = searchedRecords === null ? "preview" : "sharded search";
    summary.textContent = `${datasetPrefix}${matches.length.toLocaleString()} ${mode} matches · showing ${matches.length ? start + 1 : 0}–${Math.min(start + pageSize, matches.length)}`;
    pageLabel.textContent = `Page ${page + 1} of ${pages}`;
    previous.disabled = page === 0;
    next.disabled = page >= pages - 1;
  };

  const loadRecordManifest = async () => {
    if (!recordRoot) return;
    const response = await fetch(`${recordRoot}/manifest.json`);
    if (!response.ok) throw new Error(`Record index manifest load failed: ${response.status}`);
    const manifest = await response.json();
    recordPageSize = Number(manifest.page_size) || recordPageSize;
  };

  const loadRecordPage = async (pageNumber) => {
    if (recordPageCache.has(pageNumber)) return recordPageCache.get(pageNumber);
    const promise = fetch(`${recordRoot}/page-${String(pageNumber).padStart(5, "0")}.json`).then((response) => {
      if (!response.ok) throw new Error(`Record metadata page load failed: ${response.status}`);
      return response.json();
    });
    recordPageCache.set(pageNumber, promise);
    return promise;
  };

  const resolveOrdinals = async (ordinals) => {
    const limited = ordinals.slice(0, candidateLimit);
    const byPage = new Map();
    for (const ordinal of limited) {
      const pageNumber = Math.floor(ordinal / recordPageSize);
      if (!byPage.has(pageNumber)) byPage.set(pageNumber, []);
      byPage.get(pageNumber).push(ordinal);
    }
    const records = [];
    for (const [pageNumber, wanted] of byPage) {
      const rows = await loadRecordPage(pageNumber);
      for (const ordinal of wanted) {
        const row = rows[ordinal % recordPageSize];
        if (row) records.push(decodeRecord(row));
      }
    }
    return records;
  };

  const runShardedSearch = async () => {
    const serial = ++searchSerial;
    const needle = String(search?.value || "").trim();
    if (!searchRoot || !recordRoot || needle.length < 2 || requestedId || requestedLegacy) {
      searchedRecords = null;
      page = 0;
      render();
      return;
    }
    const prefix = queryPrefix(needle);
    if (!prefix) {
      searchedRecords = [];
      render();
      return;
    }
    summary.textContent = `Searching ${prefix}…`;
    try {
      const response = await fetch(`${searchRoot}/${prefix}.json`);
      if (response.status === 404) {
        searchedRecords = [];
        render();
        return;
      }
      if (!response.ok) throw new Error(`Search shard load failed: ${response.status}`);
      const shard = await response.json();
      let ordinals = [];
      if (scope) {
        ordinals = Array.isArray(shard[scope]) ? shard[scope] : [];
      } else {
        for (const values of Object.values(shard)) {
          if (!Array.isArray(values)) continue;
          ordinals.push(...values);
          if (ordinals.length >= candidateLimit) break;
        }
      }
      if (serial !== searchSerial) return;
      searchedRecords = await resolveOrdinals(ordinals);
      if (serial !== searchSerial) return;
      page = 0;
      render();
    } catch (error) {
      if (serial !== searchSerial) return;
      summary.textContent = error.message;
    }
  };

  search?.addEventListener("input", runShardedSearch);
  [type, review].forEach((control) => control?.addEventListener("input", () => { page = 0; render(); }));
  previous?.addEventListener("click", () => { if (page > 0) { page -= 1; render(); window.scrollTo({ top: 0, behavior: "smooth" }); } });
  next?.addEventListener("click", () => { const pages = Math.ceil(filtered().length / pageSize); if (page < pages - 1) { page += 1; render(); window.scrollTo({ top: 0, behavior: "smooth" }); } });

  Promise.all([
    fetch(previewSource).then((response) => {
      if (!response.ok) throw new Error(`Document preview load failed: ${response.status}`);
      return response.json();
    }),
    loadRecordManifest()
  ]).then(([data]) => {
    previewRecords = Array.isArray(data) ? data : [];
    render();
    if (search?.value && !requestedId && !requestedLegacy) runShardedSearch();
  }).catch((error) => {
    summary.textContent = error.message;
  });
})();
