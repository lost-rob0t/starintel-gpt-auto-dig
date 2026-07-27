(() => {
  "use strict";

  const PROTOCOL = "auto-dig-quasar.v1";
  const GRAPH_ROUTE = "/graph";
  const frame = document.querySelector("#quasar-frame");
  const params = new URLSearchParams(location.search);
  const datasetId = params.get("dataset") || "complete-corpus";
  const runId = params.get("run");
  const correctionRepository =
    document.documentElement.dataset.correctionRepository ||
    "lost-rob0t/starintel-gpt-auto-dig";
  let childOrigin = location.origin;

  function notify(type, payload) {
    frame.contentWindow?.postMessage(
      { protocol: PROTOCOL, channel: "event", type, payload },
      childOrigin
    );
  }

  function response(event, id, ok, result, error) {
    event.source.postMessage(
      { protocol: PROTOCOL, channel: "response", id, ok, result, error },
      event.origin
    );
  }

  function datasetUrl(id) {
    if (id === "complete-corpus") {
      return "../downloads/starintel-complete-corpus.jsonl";
    }
    const safe = id.replace(/[^a-zA-Z0-9._-]/g, "");
    if (!safe || safe !== id) throw new Error("Invalid dataset identifier");
    return `../${safe}/downloads/starintel-documents.jsonl`;
  }

  async function loadJsonl(url) {
    const result = await fetch(url, { credentials: "same-origin" });
    if (!result.ok) throw new Error(`Dataset load failed: ${result.status}`);
    const text = await result.text();
    return text
      .split(/\r?\n/)
      .filter((line) => line.trim())
      .map((line) => JSON.parse(line));
  }

  async function loadDataset(id) {
    return {
      id,
      runId,
      documents: await loadJsonl(datasetUrl(id)),
      graph: null
    };
  }

  function localFinding(request) {
    const now = new Date().toISOString();
    return {
      _id: `starintel:analysis:auto-dig-local:${crypto.randomUUID()}`,
      dataset: request.datasetId || datasetId,
      dtype: "analysis",
      schema_version: "0.9.0",
      version: 1,
      date_added: now,
      date_updated: now,
      title: `Local Auto-Dig finding: ${
        request.input?.title || request.targetIds?.[0] || "investigation"
      }`,
      summary:
        request.input?.body ||
        "Local actor run completed without external services.",
      sources: [],
      evidence: [],
      data: {
        question:
          request.input?.title || request.targetIds?.[0] || "Local investigation",
        method: "auto-dig.local.investigation",
        input_ids: request.targetIds || [],
        findings: [
          request.input?.body ||
            "Local actor run completed without external services."
        ],
        conclusions: [],
        unresolved: [],
        confidence: 0.5
      },
      extensions: {
        auto_dig: {
          kind: "finding",
          run_id: runId,
          tip_id: request.tipId || null,
          target_ids: request.targetIds || []
        }
      }
    };
  }

  const handlers = {
    handshake: async (request) => {
      if (request?.childOrigin !== location.origin) {
        throw new Error("Bridge origin mismatch");
      }
      childOrigin = request.childOrigin;
      setTimeout(() => notify("navigate", { route: GRAPH_ROUTE }), 0);
      return {
        protocol: PROTOCOL,
        datasetId,
        runId,
        correctionRepository,
        initialRoute: GRAPH_ROUTE
      };
    },
    getActiveDatasetId: async () => datasetId,
    getActiveRunId: async () => runId,
    loadDataset: async ({ datasetId: id }) => loadDataset(id),

    // Quasar owns persistence. The host only supplies generated dataset records.
    saveDocument: async () => undefined,
    saveRelation: async () => undefined,
    saveGraph: async () => undefined,

    runActor: async ({ request }) => {
      const adapter = window.autoDigActorAdapters?.[request.actorId];
      const result = adapter
        ? await adapter(request)
        : { documents: [localFinding(request)] };
      const documents = Array.isArray(result?.documents) ? result.documents : [];
      const run = {
        id: `run:${crypto.randomUUID()}`,
        actorId: request.actorId,
        status: "completed",
        documents
      };
      notify("actor-findings", { run, documents });
      return run;
    },
    openTipline: async () => notify("navigate", { route: "/tipline" }),
    reportIncorrectData: async () => undefined
  };

  addEventListener("message", async (event) => {
    if (event.source !== frame.contentWindow || event.origin !== location.origin) {
      return;
    }
    const message = event.data;
    if (!message || message.protocol !== PROTOCOL) return;
    if (message.channel !== "request" || !handlers[message.method]) return;

    try {
      const result = await handlers[message.method](message.params || {});
      response(event, message.id, true, result, null);
    } catch (error) {
      response(event, message.id, false, null, error.message || String(error));
    }
  });
})();
