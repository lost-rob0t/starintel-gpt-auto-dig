(() => {
  const script = document.currentScript;
  const source = script?.dataset.documents || "documents.json";
  const params = new URLSearchParams(location.search);
  const requestedDataset = params.get("dataset") || "";
  const requestedId = params.get("id") || "";
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
  const pageSize = 36;
  let records = [];
  let page = 0;

  if (requestedDataset && search) search.placeholder = `Search within ${requestedDataset}…`;
  if (requestedId && search) search.value = requestedId;

  const filtered = () => {
    const needle = String(search?.value || "").trim().toLowerCase();
    const dtype = type?.value || "";
    const state = review?.value || "";
    return records.filter((record) => {
      if (requestedDataset && record.dataset !== requestedDataset) return false;
      if (dtype && record.dtype !== dtype) return false;
      if (state && record.review !== state) return false;
      if (!needle) return true;
      return [record.title, record.summary, record.id, record.dataset, record.dtype]
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
        <p>${esc(record.summary || "No summary attached.")}</p>
        <div class="document-card-footer"><code>${esc(record.id)}</code><span>${esc(record.updated || "")}</span></div>
      </article>`).join("");
    const datasetPrefix = requestedDataset ? `${requestedDataset} · ` : "";
    summary.textContent = `${datasetPrefix}${matches.length.toLocaleString()} indexed matches · showing ${matches.length ? start + 1 : 0}–${Math.min(start + pageSize, matches.length)}`;
    pageLabel.textContent = `Page ${page + 1} of ${pages}`;
    previous.disabled = page === 0;
    next.disabled = page >= pages - 1;
  };

  [search, type, review].forEach((control) => control?.addEventListener("input", () => { page = 0; render(); }));
  previous?.addEventListener("click", () => { if (page > 0) { page -= 1; render(); window.scrollTo({ top: 0, behavior: "smooth" }); } });
  next?.addEventListener("click", () => { const pages = Math.ceil(filtered().length / pageSize); if (page < pages - 1) { page += 1; render(); window.scrollTo({ top: 0, behavior: "smooth" }); } });

  fetch(source).then((response) => {
    if (!response.ok) throw new Error(`Document index load failed: ${response.status}`);
    return response.json();
  }).then((data) => {
    records = Array.isArray(data) ? data : [];
    render();
  }).catch((error) => {
    summary.textContent = error.message;
  });
})();
