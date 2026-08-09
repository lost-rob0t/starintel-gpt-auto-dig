(() => {
  const script = document.currentScript;
  const previewSource = script?.dataset.documents || "documents.json";
  const scope = script?.dataset.scope || "";
  const rootPrefix = script?.dataset.rootPrefix || "";
  const indexConfigSource = `${rootPrefix}search-index.json`;
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
  const pageSize = 36;
  const candidateLimit = 5000;
  const decoder = new TextDecoder();
  let previewRecords = [];
  let searchedRecords = null;
  let page = 0;
  let searchSerial = 0;
  let indexConfig = null;
  let recordPageSize = 2000;
  const recordPageCache = new Map();
  const segmentCache = new Map();

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
        <p>${esc(record.summary || "Canonical metadata result. Full payloads live in the canonical bulk corpus.")}</p>
        <div class="document-card-footer"><code>${esc(record.id)}</code><span>${esc(record.updated || "")}</span></div>
      </article>`).join("");
    const datasetPrefix = requestedDataset ? `${requestedDataset} · ` : "";
    const mode = searchedRecords === null ? "preview" : "range search";
    summary.textContent = `${datasetPrefix}${matches.length.toLocaleString()} ${mode} matches · showing ${matches.length ? start + 1 : 0}–${Math.min(start + pageSize, matches.length)}`;
    pageLabel.textContent = `Page ${page + 1} of ${pages}`;
    previous.disabled = page === 0;
    next.disabled = page >= pages - 1;
  };

  const bundleUrl = (group, bundle) => {
    const metadata = indexConfig?.[group]?.bundles?.[bundle];
    const url = typeof metadata === "string" ? metadata : metadata?.url;
    if (!url) throw new Error(`Missing ${group} bundle URL for ${bundle}`);
    return url;
  };

  const fetchSegment = async (group, segment) => {
    if (!segment) return null;
    const key = `${group}:${segment.bundle}:${segment.offset}:${segment.length}`;
    if (segmentCache.has(key)) return segmentCache.get(key);
    const promise = (async () => {
      const start = Number(segment.offset);
      const length = Number(segment.length);
      if (!Number.isSafeInteger(start) || !Number.isSafeInteger(length) || start < 0 || length <= 0) {
        throw new Error("Invalid external index byte range");
      }
      const response = await fetch(bundleUrl(group, segment.bundle), {
        headers: { Range: `bytes=${start}-${start + length - 1}` }
      });
      if (response.status !== 206) {
        throw new Error(`Index host ignored byte range (${response.status}); refusing a full bundle download`);
      }
      const bytes = new Uint8Array(await response.arrayBuffer());
      if (bytes.byteLength !== length) {
        throw new Error(`Index byte-range length mismatch: ${bytes.byteLength} != ${length}`);
      }
      return JSON.parse(decoder.decode(bytes));
    })();
    segmentCache.set(key, promise);
    return promise;
  };

  const queryPrefix = (value) => {
    const minimum = Number(indexConfig?.minimum_query_characters) || 2;
    const prefixLength = Number(indexConfig?.search?.prefix_length) || 2;
    const token = String(value || "").toLowerCase().match(new RegExp(`[a-z0-9]{${minimum},}`));
    return token ? token[0].slice(0, prefixLength) : "";
  };

  const loadRecordPage = async (pageNumber) => {
    if (recordPageCache.has(pageNumber)) return recordPageCache.get(pageNumber);
    const segment = indexConfig?.records?.pages?.[pageNumber];
    if (!segment) throw new Error(`Missing record metadata page ${pageNumber}`);
    const promise = fetchSegment("records", segment);
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

  const findExactRecord = async (id) => {
    const pages = indexConfig?.records?.pages || [];
    let low = 0;
    let high = pages.length - 1;
    while (low <= high) {
      const middle = Math.floor((low + high) / 2);
      const segment = pages[middle];
      if (id < segment.first_id) {
        high = middle - 1;
        continue;
      }
      if (id > segment.last_id) {
        low = middle + 1;
        continue;
      }
      const rows = await loadRecordPage(middle);
      const row = rows.find((candidate) => candidate?.[1] === id);
      return row ? decodeRecord(row) : null;
    }
    return null;
  };

  const runExactId = async () => {
    const serial = ++searchSerial;
    summary.textContent = "Resolving canonical record…";
    try {
      const record = await findExactRecord(requestedId);
      if (serial !== searchSerial) return;
      searchedRecords = record ? [record] : [];
      page = 0;
      render();
    } catch (error) {
      if (serial !== searchSerial) return;
      summary.textContent = error.message;
    }
  };

  const runShardedSearch = async () => {
    const serial = ++searchSerial;
    const needle = String(search?.value || "").trim();
    const minimum = Number(indexConfig?.minimum_query_characters) || 2;
    if (!indexConfig || needle.length < minimum) {
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
    const allSegments = indexConfig?.search?.segments?.[prefix] || [];
    const segments = scope
      ? allSegments.filter((segment) => segment.scope === scope)
      : allSegments;
    if (!segments.length) {
      searchedRecords = [];
      page = 0;
      render();
      return;
    }
    summary.textContent = `Searching ${prefix}…`;
    try {
      const ordinals = [];
      for (const segment of segments) {
        const shard = await fetchSegment("search", segment);
        if (serial !== searchSerial) return;
        if (scope) {
          const values = shard?.[scope];
          if (Array.isArray(values)) ordinals.push(...values);
        } else {
          for (const values of Object.values(shard || {})) {
            if (Array.isArray(values)) ordinals.push(...values);
          }
        }
        if (ordinals.length >= candidateLimit) break;
      }
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
    fetch(indexConfigSource).then((response) => {
      if (!response.ok) throw new Error(`Search index map load failed: ${response.status}`);
      return response.json();
    })
  ]).then(([data, config]) => {
    previewRecords = Array.isArray(data) ? data : [];
    indexConfig = config;
    recordPageSize = Number(indexConfig?.records?.page_size) || recordPageSize;
    render();
    if (requestedId) runExactId();
    else if (search?.value) runShardedSearch();
  }).catch((error) => {
    summary.textContent = error.message;
  });
})();
