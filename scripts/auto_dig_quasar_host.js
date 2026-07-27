(() => {
  "use strict";
  const PROTOCOL = "auto-dig-quasar.v1";
  const frame = document.querySelector("#quasar-frame");
  const params = new URLSearchParams(location.search);
  const datasetId = params.get("dataset") || "complete-corpus";
  const runId = params.get("run");
  const correctionRepository = document.documentElement.dataset.correctionRepository || "lost-rob0t/starintel-gpt-auto-dig";
  const DB_NAME = "auto-dig-quasar-host-v1";
  const DB_VERSION = 1;
  let childOrigin = location.origin;
  let route = "/";

  function db() {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(DB_NAME, DB_VERSION);
      request.onupgradeneeded = () => {
        const database = request.result;
        for (const name of ["documents", "graphs", "corrections", "runs"]) {
          if (!database.objectStoreNames.contains(name)) database.createObjectStore(name, { keyPath: "id" });
        }
      };
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  async function put(storeName, value) {
    const database = await db();
    await new Promise((resolve, reject) => {
      const transaction = database.transaction(storeName, "readwrite");
      transaction.objectStore(storeName).put(value);
      transaction.oncomplete = resolve;
      transaction.onerror = () => reject(transaction.error);
    });
  }

  async function all(storeName) {
    const database = await db();
    return new Promise((resolve, reject) => {
      const request = database.transaction(storeName).objectStore(storeName).getAll();
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  function notify(type, payload) {
    frame.contentWindow?.postMessage({ protocol: PROTOCOL, channel: "event", type, payload }, childOrigin);
  }

  function response(event, id, ok, result, error) {
    event.source.postMessage({ protocol: PROTOCOL, channel: "response", id, ok, result, error }, event.origin);
  }

  function datasetUrl(id) {
    if (id === "complete-corpus") return "../downloads/starintel-complete-corpus.jsonl";
    const safe = id.replace(/[^a-zA-Z0-9._-]/g, "");
    return `../${safe}/downloads/starintel-documents.jsonl`;
  }

  async function loadJsonl(url) {
    const text = await fetch(url, { credentials: "same-origin" }).then((result) => {
      if (!result.ok) throw new Error(`Dataset load failed: ${result.status}`);
      return result.text();
    });
    return text.split(/\r?\n/).filter(Boolean).map((line) => JSON.parse(line));
  }

  async function loadDataset(id) {
    const base = await loadJsonl(datasetUrl(id));
    const overlay = (await all("documents")).filter((row) => row.datasetId === id).map((row) => row.document);
    const merged = new Map(base.map((document) => [document._id, document]));
    overlay.forEach((document) => merged.set(document._id, document));
    return { id, runId, documents: [...merged.values()], graph: null };
  }

  function localFinding(request) {
    const now = new Date().toISOString();
    const id = `starintel:analysis:auto-dig-local:${crypto.randomUUID()}`;
    return {
      _id: id,
      dataset: request.datasetId || datasetId,
      dtype: "analysis",
      schema_version: "0.9.0",
      version: 1,
      date_added: now,
      date_updated: now,
      title: `Local Auto-Dig finding: ${request.input?.title || request.targetIds?.[0] || "investigation"}`,
      summary: request.input?.body || "Local actor run completed without external services.",
      sources: [],
      evidence: [],
      data: {
        question: request.input?.title || request.targetIds?.[0] || "Local investigation",
        method: "auto-dig.local.investigation",
        input_ids: request.targetIds || [],
        findings: [request.input?.body || "Local actor run completed without external services."],
        conclusions: [],
        unresolved: [],
        confidence: 0.5
      },
      extensions: { auto_dig: { kind: "finding", run_id: runId, tip_id: request.tipId || null, target_ids: request.targetIds || [] } }
    };
  }

  const handlers = {
    handshake: async (params) => {
      if (params?.childOrigin !== location.origin) throw new Error("Bridge origin mismatch");
      childOrigin = params.childOrigin;
      return { protocol: PROTOCOL, datasetId, runId, correctionRepository };
    },
    getActiveDatasetId: async () => datasetId,
    getActiveRunId: async () => runId,
    loadDataset: async ({ datasetId: id }) => loadDataset(id),
    saveDocument: async ({ document }) => {
      await put("documents", { id: `${datasetId}:${document._id}`, datasetId, document, updatedAt: new Date().toISOString() });
      notify("dataset-documents", { documents: [document] });
    },
    saveRelation: async ({ relation }) => handlers.saveDocument({ document: relation }),
    saveGraph: async ({ graph }) => put("graphs", { id: `${datasetId}:${graph.id}`, datasetId, graph, updatedAt: new Date().toISOString() }),
    runActor: async ({ request }) => {
      const adapters = window.autoDigActorAdapters || {};
      const adapter = adapters[request.actorId];
      const result = adapter ? await adapter(request) : { documents: [localFinding(request)] };
      const documents = Array.isArray(result.documents) ? result.documents : [];
      for (const document of documents) await handlers.saveDocument({ document });
      const run = { id: `run:${crypto.randomUUID()}`, actorId: request.actorId, status: "completed", documents };
      await put("runs", run);
      notify("actor-findings", { run, documents });
      return run;
    },
    openTipline: async () => {
      notify("navigate", { route: "/tipline" });
    },
    reportIncorrectData: async ({ target }) => {
      const report = target.payload;
      await put("corrections", { id: report.id || `correction:${crypto.randomUUID()}`, report, updatedAt: new Date().toISOString() });
    }
  };

  addEventListener("message", async (event) => {
    if (event.source !== frame.contentWindow || event.origin !== location.origin) return;
    const message = event.data;
    if (!message || message.protocol !== PROTOCOL) return;
    if (message.channel === "event") {
      if (message.type === "route-changed") route = message.payload?.route || route;
      if (message.type === "open-tipline") notify("navigate", { route: "/tipline" });
      return;
    }
    if (message.channel !== "request" || !handlers[message.method]) return;
    try {
      response(event, message.id, true, await handlers[message.method](message.params || {}));
    } catch (error) {
      response(event, message.id, false, null, error.message || String(error));
    }
  });

  document.querySelectorAll("[data-quasar-route]").forEach((button) => {
    button.addEventListener("click", () => notify("navigate", { route: button.dataset.quasarRoute }));
  });

  const themeObserver = new MutationObserver(() => notify("theme-changed", { theme: document.documentElement.dataset.theme || "midnight" }));
  themeObserver.observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
  addEventListener("popstate", () => notify("dataset-changed", { datasetId }));
})();
