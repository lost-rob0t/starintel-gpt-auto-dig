from __future__ import annotations

import html
import json
from collections import Counter
from typing import Any
from urllib.parse import quote

from .model import links, slug, source_record, summary


def page(title: str, body: str, prefix: str = "") -> str:
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="dark light"><title>{html.escape(title)}</title>
<link rel="stylesheet" href="{prefix}assets/style.css"></head><body>
<header><a class="brand" href="{prefix}index.html">StarIntel GPT Auto Dig</a>
<nav><a href="{prefix}index.html">Research</a></nav></header>
<main>{body}</main><footer>Generated from canonical StarIntel v0.9.0 data.</footer>
</body></html>"""


def value(data: Any) -> str:
    if isinstance(data, str):
        return "".join(f"<p>{html.escape(part)}</p>" for part in data.split("\n\n") if part.strip())
    if isinstance(data, list):
        return "<ul>" + "".join(f"<li>{value(item)}</li>" for item in data) + "</ul>"
    if isinstance(data, dict):
        return "<dl>" + "".join(
            f"<dt>{html.escape(str(key).replace('_', ' ').title())}</dt><dd>{value(item)}</dd>"
            for key, item in data.items()
        ) + "</dl>"
    if data is None:
        return "<code>null</code>"
    return f"<code>{html.escape(str(data))}</code>"


def sources(items: list[Any]) -> str:
    rows = []
    for raw_source in items:
        source = source_record(raw_source)
        title = source.get("title") or source.get("publisher") or source.get("url") or "Source"
        heading = f'<a href="{html.escape(source["url"])}">{html.escape(str(title))}</a>' if source.get("url") else html.escape(str(title))
        meta = " · ".join(
            str(item)
            for item in (
                source.get("publisher"),
                f"credibility {source['credibility']}" if source.get("credibility") is not None else None,
                f"retrieved {source.get('retrieved_at') or source.get('accessed_at')}" if source.get("retrieved_at") or source.get("accessed_at") else None,
            )
            if item and item != title
        )
        rows.append(f"<li>{heading}<span>{html.escape(meta)}</span></li>")
    return '<ul class="sources">' + "".join(rows) + "</ul>"


def node(doc: dict[str, Any], target: str, known: set[str]) -> str:
    data = doc.get("data", {})
    title = doc.get("title") or data.get("name") or data.get("full_name") or doc["_id"]
    confidence = doc.get("assessment", {}).get("confidence")
    badges = "".join(
        f'<span class="badge">{html.escape(str(item))}</span>'
        for item in (
            doc["dtype"],
            doc.get("verification", {}).get("status"),
            f"confidence {confidence}" if confidence is not None else None,
            f"schema {doc.get('schema_version')}",
        )
        if item
    )
    body = [
        f'<div class="crumb"><a href="../index.html">← {html.escape(target.replace("-", " ").title())}</a></div>',
        f'<h1>{html.escape(str(title))}</h1><div class="badges">{badges}</div>',
        f'<p class="lede">{html.escape(summary(doc))}</p>',
        "<section><h2>Metadata</h2><table>",
        f"<tr><th>StarIntel ID</th><td><code>{html.escape(doc['_id'])}</code></td></tr>",
        f"<tr><th>Dataset</th><td>{html.escape(str(doc['dataset']))}</td></tr>",
        f"<tr><th>Schema</th><td>{html.escape(str(doc['schema_version']))}</td></tr>",
        f"<tr><th>Version</th><td>{html.escape(str(doc['version']))}</td></tr>",
        f"<tr><th>Updated</th><td>{html.escape(str(doc['date_updated']))}</td></tr></table></section>",
    ]
    if data:
        body.append(f"<section><h2>Type-specific data</h2>{value(data)}</section>")
    for key in (
        "assessment", "verification", "temporal", "provenance", "handling",
        "lineage", "quality", "workflow", "geospatial", "evidence", "attachments", "extensions",
    ):
        item = doc.get(key)
        if item not in (None, {}, []):
            body.append(f"<section><h2>{html.escape(key.replace('_', ' ').title())}</h2>{value(item)}</section>")
    related = links(doc, known)
    if related:
        body.append(
            "<section><h2>Related records</h2><ul>"
            + "".join(f'<li><a href="{slug(record)}.html">{html.escape(record)}</a></li>' for record in related)
            + "</ul></section>"
        )
    body += [
        f"<section><h2>Sources</h2>{sources(doc.get('sources', []))}</section>",
        f'<section><h2>Generated Org node</h2><a href="../../org/{quote(target)}/{slug(doc["_id"])}.org">Download Org source</a></section>',
        "<details><summary>Raw JSON</summary><pre>" + html.escape(json.dumps(doc, ensure_ascii=False, indent=2)) + "</pre></details>",
    ]
    return page(str(title), "".join(body), "../../")


def record_refs(values: Any, known: set[str]) -> str:
    if isinstance(values, str):
        values = [values]
    if not isinstance(values, list):
        return ""
    rows = []
    for record in values:
        if not isinstance(record, str):
            continue
        if record in known:
            rows.append(f'<a class="mini" href="nodes/{slug(record)}.html">{html.escape(record)}</a>')
        else:
            rows.append(f'<code>{html.escape(record)}</code>')
    return " ".join(rows)


def evidence_posture(docs: list[dict[str, Any]]) -> str:
    statuses: Counter[str] = Counter()
    confidence: Counter[str] = Counter()
    source_types: Counter[str] = Counter()
    for doc in docs:
        statuses[str(doc.get("verification", {}).get("status", "unclassified"))] += 1
        score = doc.get("assessment", {}).get("confidence")
        if isinstance(score, (int, float)):
            if score >= 0.97:
                confidence["very high"] += 1
            elif score >= 0.90:
                confidence["high"] += 1
            elif score >= 0.80:
                confidence["moderate"] += 1
            else:
                confidence["low / estimate"] += 1
        else:
            confidence["unassigned"] += 1
        for raw_source in doc.get("sources", []):
            source = source_record(raw_source)
            source_types[str(source.get("kind") or source.get("type") or "unspecified")] += 1

    def chips(counter: Counter[str]) -> str:
        return '<div class="chips">' + "".join(
            f'<span>{html.escape(label)} <strong>{count}</strong></span>' for label, count in sorted(counter.items())
        ) + "</div>"

    return (
        "<section><h2>Evidence posture</h2>"
        "<h3>Verification status</h3>" + chips(statuses)
        + "<h3>Confidence bands</h3>" + chips(confidence)
        + "<h3>Source types</h3>" + chips(source_types) + "</section>"
    )


def research_ledger(docs: list[dict[str, Any]]) -> str:
    passes = sorted(
        (doc for doc in docs if doc.get("dtype") == "research-pass"),
        key=lambda doc: (str(doc.get("date_updated", "")), doc["_id"]),
        reverse=True,
    )
    if not passes:
        return ""
    known = {doc["_id"] for doc in docs}
    body = ["<section><h2>Agent research ledger</h2>"]
    for research in passes:
        data = research.get("data", {})
        title = research.get("title") or research["_id"]
        confidence = research.get("assessment", {}).get("confidence", "unassigned")
        body += [
            '<article class="research-pass">',
            f'<span>{html.escape(str(research.get("date_updated", "")))}</span>',
            f'<h3><a href="nodes/{slug(research["_id"])}.html">{html.escape(str(title))}</a></h3>',
            f'<p class="lede">{html.escape(summary(research))}</p>',
            f'<p><strong>Research question:</strong> {html.escape(str(data.get("research_question", "Not recorded")))}</p>',
            f'<p><strong>Agent:</strong> {html.escape(str(data.get("agent_identity", research.get("provenance", {}).get("agent", "agent"))))} · <strong>Confidence:</strong> {html.escape(str(confidence))}</p>',
        ]
        if data.get("method"):
            body += ["<h4>Method</h4>", value(data["method"])]
        if data.get("findings"):
            body += ["<h4>Findings</h4>", value(data["findings"])]
        if data.get("supporting_record_ids"):
            body.append(f'<p><strong>Support:</strong> {record_refs(data["supporting_record_ids"], known)}</p>')
        if data.get("counterevidence_ids"):
            body.append(f'<p><strong>Counterevidence:</strong> {record_refs(data["counterevidence_ids"], known)}</p>')
        if data.get("unresolved_target_ids"):
            body.append(f'<p><strong>Open targets:</strong> {record_refs(data["unresolved_target_ids"], known)}</p>')
        body.append("</article>")
    body.append("</section>")
    return "".join(body)


def packet(target: str, docs: list[dict[str, Any]], config: dict[str, Any], graph: dict[str, Any]) -> str:
    cfg = config.get("packets", {}).get(target, {})
    title = cfg.get("title") or target.replace("-", " ").title()
    unique_sources = {
        source_record(source).get("url") or json.dumps(source_record(source), sort_keys=True)
        for doc in docs for source in doc.get("sources", [])
    }
    counts = Counter(doc["dtype"] for doc in docs)
    body = [
        f"<h1>{html.escape(title)}</h1>",
        f'<p class="lede">{html.escape(cfg.get("subtitle") or "StarIntel public-record research")}</p>',
        '<div class="notice"><strong>Canonical schema:</strong> all records validate against the embedded StarIntel v0.9.0 fork.</div>',
        '<section class="stats">',
        f"<div><strong>{len(docs)}</strong><span>records</span></div>",
        f"<div><strong>{len(unique_sources)}</strong><span>sources</span></div>",
        f"<div><strong>{len(graph['nodes'])}</strong><span>graph nodes</span></div>",
        f"<div><strong>{len(graph['edges'])}</strong><span>graph edges</span></div></section>",
        research_ledger(docs),
        evidence_posture(docs),
        '<section><div class="section-head"><div><h2>Record types</h2></div></div><div class="chips">',
        "".join(f"<span>{html.escape(dtype)} <strong>{count}</strong></span>" for dtype, count in sorted(counts.items())),
        "</div></section>",
        '<section><div class="section-head"><div><h2>Relationship graph</h2></div></div><div id="graph"></div>',
        '<script src="../assets/graph.js"></script><script>renderGraph("graph.json")</script></section>',
        '<section><div class="section-head"><div><h2>Documents</h2></div></div><div class="record-grid">',
    ]
    for doc in sorted(docs, key=lambda item: (item["dtype"], item.get("title") or item["_id"])):
        body.append(
            f'<article><span>{html.escape(doc["dtype"])}</span><h3><a href="nodes/{slug(doc["_id"])}.html">{html.escape(str(doc.get("title") or doc["_id"]))}</a></h3>'
            f'<p>{html.escape(summary(doc))}</p><code>{html.escape(doc["_id"])}</code></article>'
        )
    body += [
        "</div></section>",
        '<section><h2>Downloads</h2><p><a href="downloads/starintel-documents.jsonl">Merged canonical JSONL</a> · '
        '<a href="downloads/research-history.json">Research packet history</a> · <a href="sources.html">Source inventory</a></p></section>',
    ]
    return page(title, "".join(body), "../")


def source_inventory(target: str, docs: list[dict[str, Any]]) -> str:
    rows: dict[str, dict[str, Any]] = {}
    refs: Counter[str] = Counter()
    for doc in docs:
        for raw in doc.get("sources", []):
            source = source_record(raw)
            key = source.get("url") or source.get("source_id") or json.dumps(source, sort_keys=True)
            rows[key] = source
            refs[key] += 1
    body = [
        f'<div class="crumb"><a href="index.html">← {html.escape(target.replace("-", " ").title())}</a></div>',
        "<h1>Source inventory</h1><table><tr><th>Source</th><th>Kind</th><th>Credibility</th><th>Records</th></tr>",
    ]
    for key, source in sorted(rows.items(), key=lambda item: str(item[1].get("title") or item[0])):
        title = source.get("title") or source.get("name") or source.get("url") or key
        link = f'<a href="{html.escape(source["url"])}">{html.escape(str(title))}</a>' if source.get("url") else html.escape(str(title))
        body.append(
            f"<tr><td>{link}</td><td>{html.escape(str(source.get('kind') or source.get('type') or ''))}</td>"
            f"<td>{html.escape(str(source.get('credibility', '')))}</td><td>{refs[key]}</td></tr>"
        )
    body.append("</table>")
    return page("Source inventory", "".join(body), "../")
