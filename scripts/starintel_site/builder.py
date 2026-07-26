from __future__ import annotations

import html
import json
import shutil
from collections import defaultdict
from pathlib import Path
from urllib.parse import quote

from .dashboard import annotate_graph, dashboard_page, document_index, documents_page, graph_page
from .model import discover, graph, org_index, render_org, slug
from .render import node, page, source_inventory


def themed(markup: str, prefix: str) -> str:
    stylesheet = f'<link rel="stylesheet" href="{prefix}assets/style.css">'
    explorer_stylesheet = f'<link rel="stylesheet" href="{prefix}assets/explorer.css">'
    theme_script = f'<script src="{prefix}assets/theme.js"></script>'
    additions = ""
    if explorer_stylesheet not in markup:
        additions += explorer_stylesheet
    if theme_script not in markup:
        additions += theme_script
    return markup.replace(stylesheet, stylesheet + additions, 1)


def build_site(input_root: Path, output: Path, org_output: Path, config_path: Path, assets: Path) -> None:
    packets = discover(input_root)
    config = json.loads(config_path.read_text(encoding="utf-8")) if config_path.exists() else {}
    for directory in (output, org_output):
        if directory.exists():
            shutil.rmtree(directory)
        directory.mkdir(parents=True)
    asset_output = output / "assets"
    asset_output.mkdir()
    shutil.copy2(assets / "style.css", asset_output / "style.css")
    shutil.copy2(assets / "explorer.css", asset_output / "explorer.css")
    shutil.copy2(assets / "theme.js", asset_output / "theme.js")
    shutil.copy2(assets / "dashboard.js", asset_output / "dashboard.js")
    shutil.copy2(assets / "graph.js", asset_output / "graph.js")
    shutil.copy2(assets / "graph-core.mjs", asset_output / "graph-core.mjs")
    shutil.copy2(assets / "graph-model.mjs", asset_output / "graph-model.mjs")
    shutil.copy2(assets / "graph-render.mjs", asset_output / "graph-render.mjs")
    shutil.copy2(assets / "graph-render-scaled.mjs", asset_output / "graph-render-scaled.mjs")
    shutil.copy2(assets / "graph-ui.mjs", asset_output / "graph-ui.mjs")
    shutil.copy2(assets / "graph-controller.mjs", asset_output / "graph-controller.mjs")
    shutil.copy2(assets / "graph-explorer.mjs", asset_output / "graph-explorer.mjs")
    shutil.copy2(assets / "graph-touch.js", asset_output / "graph-touch.js")
    (output / ".nojekyll").write_text("")

    grouped = defaultdict(list)
    for item in packets:
        grouped[item.target].append(item)

    cards = []
    dataset_rows: list[dict[str, object]] = []
    search = []
    for target, target_packets in sorted(grouped.items()):
        by_id = {}
        for item in target_packets:
            for doc in item.documents:
                old = by_id.get(doc["_id"])
                if old is None or str(doc["date_updated"]) >= str(old["date_updated"]):
                    by_id[doc["_id"]] = doc
        docs = sorted(by_id.values(), key=lambda doc: doc["_id"])
        known = set(by_id)
        target_out = output / target
        node_out = target_out / "nodes"
        org_out = org_output / target
        public_org = output / "org" / target
        downloads = target_out / "downloads"
        for directory in (target_out, node_out, org_out, public_org, downloads):
            directory.mkdir(parents=True, exist_ok=True)

        network = annotate_graph(docs, graph(docs))
        (target_out / "graph.json").write_text(json.dumps(network, ensure_ascii=False, separators=(",", ":")))
        (target_out / "documents.json").write_text(json.dumps(document_index(docs), ensure_ascii=False, separators=(",", ":")))
        (target_out / "index.html").write_text(themed(dashboard_page(target, docs, config, network), "../"))
        (target_out / "graph.html").write_text(themed(graph_page(target, config, network), "../"))
        (target_out / "documents.html").write_text(themed(documents_page(target, docs, config), "../"))
        (target_out / "sources.html").write_text(themed(source_inventory(target, docs), "../"))
        index = org_index(target, docs)
        (org_out / "index.org").write_text(index)
        (public_org / "index.org").write_text(index)

        # The public download is the merged target history, not merely the newest
        # incremental packet. This keeps append-only agent research passes from
        # hiding the underlying evidence corpus.
        canonical = "".join(json.dumps(doc, ensure_ascii=False, separators=(",", ":")) + "\n" for doc in docs)
        (downloads / "starintel-documents.jsonl").write_text(canonical)
        history = [
            {
                "run": item.run,
                "path": str(item.path.relative_to(input_root)),
                "document_count": len(item.documents),
                "updated_through": max(str(doc["date_updated"]) for doc in item.documents),
            }
            for item in sorted(target_packets, key=lambda packet_item: packet_item.run)
        ]
        (downloads / "research-history.json").write_text(json.dumps(history, ensure_ascii=False, indent=2))

        for doc in docs:
            name = slug(doc["_id"])
            org = render_org(doc, known)
            (org_out / f"{name}.org").write_text(org)
            (public_org / f"{name}.org").write_text(org)
            (node_out / f"{name}.html").write_text(themed(node(doc, target, known), "../../"))
            search.append({
                "target": target,
                "id": doc["_id"],
                "title": doc.get("title") or doc.get("name") or doc["_id"],
                "dtype": doc["dtype"],
                "dataset": doc.get("dataset", ""),
                "summary": doc.get("summary") or doc.get("description", ""),
                "url": f"{target}/nodes/{name}.html",
            })

        cfg = config.get("packets", {}).get(target, {})
        target_title = cfg.get("title") or target.replace("-", " ").title()
        cards.append(
            f'<article><span>{len(docs)} records</span><h2><a href="{target}/index.html">{html.escape(str(target_title))}</a></h2>'
            f'<p>{html.escape(str(cfg.get("subtitle") or "StarIntel public-record research"))}</p><a href="{target}/index.html">Open dashboard →</a></article>'
        )

        datasets: dict[str, list[dict]] = defaultdict(list)
        for doc in docs:
            datasets[str(doc.get("dataset") or "unknown")].append(doc)
        for dataset, dataset_docs in sorted(datasets.items()):
            dataset_rows.append({
                "dataset": dataset,
                "target": target,
                "target_title": target_title,
                "record_count": len(dataset_docs),
                "updated_through": max(str(doc.get("date_updated", "")) for doc in dataset_docs),
                "url": f"{target}/documents.html?dataset={quote(dataset, safe='')}",
            })

    dataset_rows.sort(key=lambda row: (str(row["dataset"]).lower(), str(row["target"])))
    (output / "datasets.json").write_text(json.dumps(dataset_rows, ensure_ascii=False, separators=(",", ":")))
    (output / "search-index.json").write_text(json.dumps(search, ensure_ascii=False, separators=(",", ":")))

    dataset_cards = "".join(
        f'<article><span>{int(row["record_count"]):,} records · {html.escape(str(row["target_title"]))}</span>'
        f'<h2><a href="{html.escape(str(row["url"]))}">{html.escape(str(row["dataset"]))}</a></h2>'
        f'<p>Updated through {html.escape(str(row["updated_through"]))}</p>'
        f'<a href="{html.escape(str(row["url"]))}">Browse dataset →</a></article>'
        for row in dataset_rows
    )
    body = (
        "<h1>StarIntel GPT Auto Dig</h1>"
        '<p class="lede">Source-backed research transformed into dashboards, Org-roam nodes, source inventories, and progressive graph explorers.</p>'
        '<div class="notice"><strong>Canonical-data rule:</strong> only StarIntel packets are committed. Generated dashboards default to reviewed records while preserving explicit access to unreviewed material.</div>'
        '<section class="stats dashboard-stats">'
        f'<div><strong>{len(grouped):,}</strong><span>research targets</span></div>'
        f'<div><strong>{len(dataset_rows):,}</strong><span>datasets</span></div>'
        f'<div><strong>{len(search):,}</strong><span>canonical records</span></div>'
        '</section>'
        '<section><div class="section-head"><div><h2>Research targets</h2><p>Combined dashboards grouped by target.</p></div></div>'
        '<div class="packets">' + "".join(cards) + "</div></section>"
        '<section id="datasets"><div class="section-head"><div><h2>All datasets</h2><p>Every dataset discovered from canonical StarIntel records.</p></div>'
        '<a href="datasets.json">Dataset index JSON →</a></div><div class="packets dataset-catalog">' + dataset_cards + "</div></section>"
    )
    (output / "index.html").write_text(themed(page(config.get("site_title", "StarIntel GPT Auto Dig"), body), ""))
