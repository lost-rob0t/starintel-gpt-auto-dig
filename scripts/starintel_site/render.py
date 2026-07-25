from __future__ import annotations

import html
import json
from collections import Counter, defaultdict
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
<main>{body}</main><footer>Generated from canonical StarIntel data. Org and HTML are derived artifacts.</footer>
</body></html>"""


def value(data: Any) -> str:
    if isinstance(data, str):
        return "".join(f"<p>{html.escape(part)}</p>" for part in data.split("\\n\\n") if part.strip())
    if isinstance(data, list):
        return "<ul>" + "".join(f"<li>{value(item)}</li>" for item in data) + "</ul>"
    if isinstance(data, dict):
        return "<dl>" + "".join(
            f"<dt>{html.escape(str(key).replace('_', ' ').title())}</dt><dd>{value(item)}</dd>"
            for key, item in data.items()
        ) + "</dl>"
    return f"<code>{html.escape(str(data))}</code>"


def sources(items: list[Any]) -> str:
    rows = []
    for raw_source in items:
        source = source_record(raw_source)
        title = source.get("title") or source.get("publisher") or source.get("url") or "Source"
        heading = f'<a href="{html.escape(source["url"])}">{html.escape(title)}</a>' if source.get("url") else html.escape(title)
        meta = " · ".join(str(x) for x in (
            source.get("publisher"),
            f"reliability {source['reliability']}" if source.get("reliability") is not None else None,
            f"accessed {source['accessed']}" if source.get("accessed") else None,
        ) if x and x != title)
        rows.append(f"<li>{heading}<span>{html.escape(meta)}</span></li>")
    return '<ul class="sources">' + "".join(rows) + "</ul>"


def node(doc: dict[str, Any], target: str, known: set[str]) -> str:
    title = doc.get("title") or doc.get("name") or doc["_id"]
    badges = "".join(f'<span class="badge">{html.escape(str(x))}</span>' for x in (
        doc["dtype"], doc.get("verification", {}).get("status"),
        f"confidence {doc['confidence']}" if doc.get("confidence") is not None else None,
    ) if x)
    body = [
        f'<div class="crumb"><a href="../index.html">← {html.escape(target.replace("-", " ").title())}</a></div>',
        f"<h1>{html.escape(title)}</h1><div class=\"badges\">{badges}</div>",
        f'<p class="lede">{html.escape(summary(doc))}</p>',
        "<section><h2>Metadata</h2><table>",
        f"<tr><th>StarIntel ID</th><td><code>{html.escape(doc['_id'])}</code></td></tr>",
        f"<tr><th>Dataset</th><td>{html.escape(str(doc['dataset']))}</td></tr>",
        f"<tr><th>Version</th><td>{html.escape(str(doc['version']))}</td></tr>",
        f"<tr><th>Updated</th><td>{html.escape(str(doc['date_updated']))}</td></tr></table></section>",
    ]
    if doc.get("predicates"):
        body.append("<section><h2>Predicates</h2>")
        for pred in doc["predicates"]:
            if isinstance(pred, dict):
                body += [f"<article><h3>{html.escape(str(pred.get('predicate', 'predicate')).replace('_', ' '))}</h3>",
                         value(pred.get("object")), "</article>"]
        body.append("</section>")
    omitted = {
        "_id", "dataset", "dtype", "version", "date_added", "date_updated", "title",
        "summary", "description", "definition", "sources", "predicates", "tags",
        "confidence", "verification", "subject",
    }
    for key, item in doc.items():
        if key not in omitted:
            body.append(f"<section><h2>{html.escape(key.replace('_', ' ').title())}</h2>{value(item)}</section>")
    related = links(doc, known)
    if related:
        body.append("<section><h2>Related records</h2><ul>" + "".join(
            f'<li><a href="{slug(record)}.html">{html.escape(record)}</a></li>' for record in related
        ) + "</ul></section>")
    body += [
        f"<section><h2>Sources</h2>{sources(doc.get('sources', []))}</section>",
        f'<section><h2>Generated Org node</h2><a href="../../org/{quote(target)}/{slug(doc["_id"])}.org">Download Org source</a></section>',
        "<details><summary>Raw JSON</summary><pre>" + html.escape(json.dumps(doc, ensure_ascii=False, indent=2)) + "</pre></details>",
    ]
    return page(title, "".join(body), "../../")


def comparison(rows: list[dict[str, Any]]) -> str:
    keys = ("dimension", "observed_record", "corporatist_comparison", "fascist_comparison", "assessment")
    labels = ("Dimension", "Observed record", "Corporatist comparison", "Fascist comparison", "Assessment")
    head = "<tr>" + "".join(f"<th>{x}</th>" for x in labels) + "</tr>"
    body = "".join("<tr>" + "".join(f"<td>{html.escape(str(row.get(key, '')))}</td>" for key in keys) + "</tr>" for row in rows)
    return f'<div class="table-wrap"><table class="comparison">{head}{body}</table></div>'


def packet(target: str, docs: list[dict[str, Any]], config: dict[str, Any], graph: dict[str, Any]) -> str:
    cfg = config.get("packets", {}).get(target, {})
    title = cfg.get("title") or target.replace("-", " ").title()
    narrative = next((doc for doc in docs if doc["_id"] == cfg.get("narrative_document_id")), None)
    unique_sources = {
        source_record(source).get("url") or json.dumps(source_record(source), sort_keys=True)
        for doc in docs for source in doc.get("sources", [])
    }
    counts = Counter(doc["dtype"] for doc in docs)
    body = [
        f"<h1>{html.escape(title)}</h1>",
        f'<p class="lede">{html.escape(cfg.get("subtitle") or "StarIntel public-record research")}</p>',
        '<div class="notice"><strong>Method:</strong> Facts, allegations, estimates, analysis, and open probes remain separate record types. The graph is navigation, not guilt by association.</div>',
        '<section class="stats">',
        f"<div><strong>{len(docs)}</strong><span>records</span></div>",
        f"<div><strong>{len(unique_sources)}</strong><span>sources</span></div>",
        f"<div><strong>{len(graph['nodes'])}</strong><span>graph nodes</span></div>",
        f"<div><strong>{len(graph['edges'])}</strong><span>graph edges</span></div></section>",
    ]
    if narrative:
        assessment = narrative.get("assessment", {})
        body += [
            "<section><h2>Neutral analytical narrative</h2>",
            f'<p class="lede">{html.escape(narrative.get("summary", ""))}</p>',
            '<div class="verdicts">',
            f"<div><span>Corporatism fit</span><strong>{html.escape(str(assessment.get('corporatism_fit')))}</strong></div>",
            f"<div><span>Fascism fit</span><strong>{html.escape(str(assessment.get('fascism_fit')))}</strong></div>",
            f"<div><span>Confidence</span><strong>{html.escape(str(assessment.get('confidence')))}</strong></div></div>",
            f"<blockquote>{html.escape(str(assessment.get('bottom_line', '')))}</blockquote>",
        ]
        for section in narrative.get("narrative", []):
            body.append(f"<h3>{html.escape(section.get('heading', 'Analysis'))}</h3>")
            body += [f"<p>{html.escape(text)}</p>" for text in section.get("paragraphs", [])]
        body += ["<h3>Governance failure modes</h3>", value(narrative.get("governance_flaws", [])),
                 "<h3>Corporatism and fascism comparison matrix</h3>", comparison(narrative.get("comparison", [])),
                 "<h3>Limits and falsification conditions</h3>", value(narrative.get("limitations", [])), "</section>"]
    body += [
        '<section><div class="section-head"><div><h2>Exploration graph</h2><p>Search, filter, drag, zoom, and open records.</p></div><a href="graph.json">graph.json</a></div>',
        '<div class="controls"><input id="graph-search" type="search" placeholder="Search nodes…"><select id="graph-filter"><option value="">All record types</option></select><button id="graph-reset">Reset</button></div>',
        '<div id="graph-shell"><canvas id="graph-canvas"></canvas><aside id="graph-detail">Select a node.</aside></div>',
        '<script src="../assets/graph.js"></script><script>StarIntelGraph.mount("graph-canvas","graph-detail","graph.json");</script></section>',
        '<section><h2>Record inventory</h2><div class="chips">',
    ]
    body += [f'<span>{html.escape(kind)} <strong>{count}</strong></span>' for kind, count in sorted(counts.items())]
    body.append('</div><div class="records">')
    for doc in sorted(docs, key=lambda d: (d["dtype"], d.get("title") or d.get("name") or d["_id"])):
        record_title = doc.get("title") or doc.get("name") or doc["_id"]
        body.append(
            f'<article><span>{html.escape(doc["dtype"])}</span><h3><a href="nodes/{slug(doc["_id"])}.html">{html.escape(record_title)}</a></h3>'
            f'<p>{html.escape(summary(doc))}</p><code>{html.escape(doc["_id"])}</code></article>'
        )
    body += [
        "</div></section><section><h2>Generated formats</h2><ul>",
        '<li><a href="downloads/starintel-documents.jsonl">Decoded canonical JSONL</a></li>',
        f'<li><a href="../org/{quote(target)}/index.org">Generated Org-roam index</a></li>',
        '<li><a href="sources.html">Generated source inventory</a></li></ul></section>',
    ]
    return page(title, "".join(body), "../")


def source_inventory(target: str, docs: list[dict[str, Any]]) -> str:
    by_key, support = {}, defaultdict(list)
    for doc in docs:
        for raw_source in doc.get("sources", []):
            source = source_record(raw_source)
            key = source.get("url") or source.get("source_id") or json.dumps(source, sort_keys=True)
            by_key.setdefault(key, source)
            support[key].append(doc["_id"])
    rows = []
    for key, source in sorted(by_key.items(), key=lambda item: (item[1].get("publisher", ""), item[1].get("title", ""))):
        title = source.get("title") or source.get("url") or "Source"
        heading = f'<a href="{html.escape(source.get("url", "#"))}">{html.escape(title)}</a>'
        refs = " ".join(f'<a class="mini" href="nodes/{slug(record)}.html">{html.escape(record)}</a>' for record in sorted(set(support[key])))
        rows.append(f"<tr><td>{heading}</td><td>{html.escape(source.get('publisher', ''))}</td><td>{html.escape(str(source.get('source_type', '')))}</td><td>{refs}</td></tr>")
    body = f'<div class="crumb"><a href="index.html">← {html.escape(target.replace("-", " ").title())}</a></div><h1>Source inventory</h1>'
    body += '<div class="table-wrap"><table><tr><th>Source</th><th>Publisher</th><th>Type</th><th>Records</th></tr>' + "".join(rows) + "</table></div>"
    return page("Source inventory", body, "../")
