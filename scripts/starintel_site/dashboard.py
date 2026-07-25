from __future__ import annotations

import html
import json
from collections import Counter
from typing import Any

from .model import slug, source_record, summary
from .render import page

REVIEWED_TOKENS = (
    "reviewed",
    "verified",
    "validated",
    "confirmed",
    "corroborated",
    "source-backed",
    "source backed",
    "resolved",
)
UNREVIEWED_TOKENS = (
    "unreviewed",
    "unverified",
    "pending",
    "draft",
    "queued",
    "unknown",
    "unclassified",
    "needs-review",
    "needs review",
    "not-reviewed",
    "not reviewed",
    "proposed",
)


def review_state(doc: dict[str, Any]) -> str:
    verification = doc.get("verification") or {}
    workflow = doc.get("workflow") or {}
    raw = (
        verification.get("status")
        or workflow.get("review_status")
        or workflow.get("status")
        or doc.get("status")
        or ""
    )
    status = str(raw).strip().lower().replace("_", "-")
    if any(token in status for token in UNREVIEWED_TOKENS):
        return "unreviewed"
    if any(token in status for token in REVIEWED_TOKENS):
        return "reviewed"
    return "unreviewed"


def _endpoint_ids(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict) and isinstance(value.get("id"), str):
        return [value["id"]]
    if isinstance(value, list):
        result: list[str] = []
        for item in value:
            result.extend(_endpoint_ids(item))
        return result
    return []


def annotate_graph(docs: list[dict[str, Any]], network: dict[str, Any]) -> dict[str, Any]:
    by_id = {doc["_id"]: doc for doc in docs}
    relation_review: dict[tuple[str, str, str], bool] = {}

    for doc in docs:
        if doc.get("dtype") != "relation":
            continue
        data = doc.get("data") or {}
        predicate = str(data.get("predicate") or "related to").replace("_", " ")
        reviewed = review_state(doc) == "reviewed"
        for subject in _endpoint_ids(data.get("subject")):
            for object_id in _endpoint_ids(data.get("object")):
                key = (subject, object_id, predicate)
                relation_review[key] = relation_review.get(key, False) or reviewed

    node_review: dict[str, bool] = {}
    for node in network.get("nodes", []):
        doc = by_id.get(node.get("id"))
        reviewed = bool(doc and review_state(doc) == "reviewed")
        node_review[str(node.get("id"))] = reviewed
        node["reviewed"] = reviewed
        node["review_status"] = review_state(doc) if doc else "unreviewed"
        node["dataset"] = doc.get("dataset") if doc else None
        node["updated"] = doc.get("date_updated") if doc else None

    reviewed_edges = 0
    for edge in network.get("edges", []):
        key = (str(edge.get("source")), str(edge.get("target")), str(edge.get("label") or "related"))
        if edge.get("label") == "references":
            reviewed = node_review.get(str(edge.get("source")), False)
        else:
            reviewed = relation_review.get(key, False)
        edge["reviewed"] = reviewed
        edge["predicate"] = edge.get("label") or "related"
        reviewed_edges += int(reviewed)

    reviewed_nodes = sum(int(node.get("reviewed", False)) for node in network.get("nodes", []))
    network["meta"] = {
        "reviewed_nodes": reviewed_nodes,
        "unreviewed_nodes": len(network.get("nodes", [])) - reviewed_nodes,
        "reviewed_edges": reviewed_edges,
        "unreviewed_edges": len(network.get("edges", [])) - reviewed_edges,
    }
    return network


def document_index(docs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "id": doc["_id"],
            "title": doc.get("title") or (doc.get("data") or {}).get("name") or doc["_id"],
            "dtype": doc["dtype"],
            "dataset": doc.get("dataset", ""),
            "summary": summary(doc),
            "review": review_state(doc),
            "status": (doc.get("verification") or {}).get("status") or doc.get("status") or "unclassified",
            "updated": doc.get("date_updated", ""),
            "url": f"nodes/{slug(doc['_id'])}.html",
        }
        for doc in docs
    ]


def _stats_cards(items: list[tuple[str, str]]) -> str:
    return '<section class="stats dashboard-stats">' + "".join(
        f'<div><strong>{html.escape(value)}</strong><span>{html.escape(label)}</span></div>'
        for value, label in items
    ) + "</section>"


def _latest_research(docs: list[dict[str, Any]], limit: int = 5) -> str:
    passes = sorted(
        (doc for doc in docs if doc.get("dtype") == "research-pass"),
        key=lambda doc: (str(doc.get("date_updated", "")), doc["_id"]),
        reverse=True,
    )[:limit]
    if not passes:
        return '<section><h2>Latest research</h2><p class="graph-muted">No research passes recorded.</p></section>'
    rows = []
    for research in passes:
        rows.append(
            '<article class="activity-row">'
            f'<span>{html.escape(str(research.get("date_updated", "")))}</span>'
            f'<h3><a href="nodes/{slug(research["_id"])}.html">{html.escape(str(research.get("title") or research["_id"]))}</a></h3>'
            f'<p>{html.escape(summary(research))}</p>'
            '</article>'
        )
    return '<section><div class="section-head"><div><h2>Latest research</h2><p>Most recent agent passes.</p></div></div><div class="activity-list">' + "".join(rows) + "</div></section>"


def _topology_summary(network: dict[str, Any]) -> str:
    degrees: Counter[str] = Counter()
    predicates: Counter[str] = Counter()
    labels = {str(node["id"]): str(node.get("label") or node["id"]) for node in network.get("nodes", [])}
    reviewed = {str(node["id"]): bool(node.get("reviewed")) for node in network.get("nodes", [])}
    for edge in network.get("edges", []):
        if not edge.get("reviewed"):
            continue
        source = str(edge.get("source"))
        target = str(edge.get("target"))
        if reviewed.get(source) and reviewed.get(target):
            degrees[source] += 1
            degrees[target] += 1
            predicates[str(edge.get("label") or "related")] += 1
    hubs = "".join(
        f'<li><span>{count} links</span><strong>{html.escape(labels.get(node_id, node_id))}</strong></li>'
        for node_id, count in degrees.most_common(8)
    ) or '<li><span>0 links</span><strong>No reviewed hubs yet</strong></li>'
    relations = "".join(
        f'<li><span>{count}</span><strong>{html.escape(predicate)}</strong></li>'
        for predicate, count in predicates.most_common(8)
    ) or '<li><span>0</span><strong>No reviewed predicates yet</strong></li>'
    return (
        '<section class="topology-grid">'
        '<div><h2>Most connected</h2><ol class="rank-list">' + hubs + '</ol></div>'
        '<div><h2>Top predicates</h2><ol class="rank-list">' + relations + '</ol></div>'
        '</section>'
    )


def dashboard_page(target: str, docs: list[dict[str, Any]], config: dict[str, Any], network: dict[str, Any]) -> str:
    cfg = config.get("packets", {}).get(target, {})
    title = cfg.get("title") or target.replace("-", " ").title()
    unique_sources = {
        source_record(source).get("url") or json.dumps(source_record(source), sort_keys=True)
        for doc in docs for source in doc.get("sources", [])
    }
    reviewed_docs = sum(review_state(doc) == "reviewed" for doc in docs)
    unreviewed_docs = len(docs) - reviewed_docs
    meta = network.get("meta", {})
    counts = Counter(doc["dtype"] for doc in docs)
    chips = "".join(
        f'<span>{html.escape(dtype)} <strong>{count}</strong></span>'
        for dtype, count in counts.most_common(16)
    )
    graph_card = f'''
    <a class="graph-launch-card" href="graph.html">
      <div class="graph-launch-copy">
        <span class="eyebrow">Reviewed graph default</span>
        <h2>Explore the relationship graph</h2>
        <p>Starts with a reviewed backbone instead of rendering the entire network. Search, filter, expand neighborhoods, inspect paths, or explicitly load the complete graph.</p>
        <strong class="graph-launch-button">Open graph explorer →</strong>
      </div>
      <div class="graph-preview" aria-hidden="true">
        <i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i>
        <span>{meta.get("reviewed_nodes", 0):,} reviewed nodes</span>
        <b>{meta.get("reviewed_edges", 0):,} reviewed edges</b>
      </div>
    </a>'''
    body = [
        '<div class="dashboard-hero">',
        f'<div><span class="eyebrow">StarIntel dashboard</span><h1>{html.escape(title)}</h1>',
        f'<p class="lede">{html.escape(cfg.get("subtitle") or "StarIntel public-record research")}</p></div>',
        '<div class="dashboard-actions"><a class="primary-action" href="graph.html">Open graph</a><a href="documents.html">Browse documents</a><a href="sources.html">Sources</a></div></div>',
        _stats_cards([
            (f"{reviewed_docs:,}", "reviewed records"),
            (f"{unreviewed_docs:,}", "unreviewed records"),
            (f"{len(unique_sources):,}", "sources"),
            (f"{len(network.get('edges', [])):,}", "total relations"),
        ]),
        graph_card,
        _topology_summary(network),
        _latest_research(docs),
        '<section><div class="section-head"><div><h2>Record types</h2><p>Largest canonical document groups.</p></div><a href="documents.html">Browse all documents →</a></div><div class="chips">',
        chips,
        '</div></section>',
        '<section class="download-strip"><div><h2>Data exports</h2><p>Canonical records remain the source of truth.</p></div><p><a href="downloads/starintel-documents.jsonl">Merged JSONL</a> · <a href="downloads/research-history.json">Research history</a> · <a href="sources.html">Source inventory</a></p></section>',
    ]
    return page(title, "".join(body), "../")


def documents_page(target: str, docs: list[dict[str, Any]], config: dict[str, Any]) -> str:
    cfg = config.get("packets", {}).get(target, {})
    title = cfg.get("title") or target.replace("-", " ").title()
    dtypes = sorted({doc["dtype"] for doc in docs})
    options = "".join(f'<option value="{html.escape(dtype)}">{html.escape(dtype.replace("-", " "))}</option>' for dtype in dtypes)
    body = f'''
    <div class="crumb"><a href="index.html">← {html.escape(title)} dashboard</a></div>
    <div class="documents-heading"><div><span class="eyebrow">Canonical records</span><h1>Documents</h1><p class="lede">Search and paginate the document index without rendering every record card at once.</p></div><a class="primary-action" href="graph.html">Open graph</a></div>
    <section class="document-controls">
      <input id="documents-search" type="search" placeholder="Search titles, summaries, IDs, or datasets…">
      <select id="documents-type"><option value="">All record types</option>{options}</select>
      <select id="documents-review"><option value="reviewed">Reviewed</option><option value="unreviewed">Unreviewed</option><option value="">All review states</option></select>
    </section>
    <div id="documents-summary" class="documents-summary">Loading records…</div>
    <section id="documents-grid" class="record-grid document-browser"></section>
    <nav class="document-pages"><button id="documents-prev" type="button">← Previous</button><span id="documents-page"></span><button id="documents-next" type="button">Next →</button></nav>
    <script src="../assets/dashboard.js" data-documents="documents.json"></script>
    '''
    return page(f"{title} documents", body, "../")


def graph_page(target: str, config: dict[str, Any], network: dict[str, Any]) -> str:
    cfg = config.get("packets", {}).get(target, {})
    title = cfg.get("title") or target.replace("-", " ").title()
    meta = network.get("meta", {})
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="dark light">
<title>{html.escape(title)} graph</title><link rel="stylesheet" href="../assets/style.css"><link rel="stylesheet" href="../assets/explorer.css"></head>
<body class="graph-page"><header><a class="brand" href="../index.html">StarIntel GPT Auto Dig</a><nav><a href="index.html">Dashboard</a><a href="documents.html">Documents</a><a href="sources.html">Sources</a></nav></header>
<main class="graph-workbench"><section class="graph-stage"><div class="graph-titlebar"><div><span class="eyebrow">Progressive graph explorer</span><h1>{html.escape(title)}</h1></div><button id="graph-detail-toggle" type="button">Toggle details</button></div>
<div class="controls graph-controls"><input id="graph-search" type="search" placeholder="Search nodes and show their neighborhood…"><select id="graph-filter"><option value="">All record types</option></select><select id="graph-review"><option value="reviewed">Reviewed only</option><option value="unreviewed">Unreviewed only</option><option value="">All review states</option></select><select id="graph-predicate"><option value="">All predicates</option></select><select id="graph-dataset"><option value="">All datasets</option></select><button id="graph-reset" type="button">Fit</button></div>
<div id="graph-shell"><canvas id="graph-canvas"></canvas><aside id="graph-detail">Select a node.</aside></div>
<div class="graph-statusbar"><span id="graph-mode-status">Reviewed backbone</span><span>Visible <strong id="graph-visible-count">0</strong> / {len(network.get('nodes', [])):,} nodes</span><span>Edges <strong id="graph-visible-edges">0</strong> / {len(network.get('edges', [])):,}</span><span>Reviewed corpus {meta.get('reviewed_nodes', 0):,} nodes · {meta.get('reviewed_edges', 0):,} edges</span></div></section></main>
<script src="../assets/theme.js"></script><script type="module">import {{ mount }} from "../assets/graph-explorer.mjs"; mount("graph-canvas", "graph-detail", "graph.json");</script><script src="../assets/graph-touch.js"></script></body></html>'''
