from __future__ import annotations

import json
import shutil
from collections import defaultdict
from pathlib import Path

from .model import discover, graph, org_index, render_org, slug
from .render import node, packet, page, source_inventory


def themed(markup: str, prefix: str) -> str:
    stylesheet = f'<link rel="stylesheet" href="{prefix}assets/style.css">'
    theme_script = f'<script src="{prefix}assets/theme.js"></script>'
    if theme_script in markup:
        return markup
    return markup.replace(stylesheet, stylesheet + theme_script, 1)


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
    shutil.copy2(assets / "theme.js", asset_output / "theme.js")
    shutil.copy2(assets / "graph.js", asset_output / "graph.js")
    shutil.copy2(assets / "graph-core.mjs", asset_output / "graph-core.mjs")
    shutil.copy2(assets / "graph-model.mjs", asset_output / "graph-model.mjs")
    shutil.copy2(assets / "graph-render.mjs", asset_output / "graph-render.mjs")
    shutil.copy2(assets / "graph-ui.mjs", asset_output / "graph-ui.mjs")
    shutil.copy2(assets / "graph-controller.mjs", asset_output / "graph-controller.mjs")
    shutil.copy2(assets / "graph-touch.js", asset_output / "graph-touch.js")
    (output / ".nojekyll").write_text("")

    grouped = defaultdict(list)
    for item in packets:
        grouped[item.target].append(item)

    cards = []
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

        network = graph(docs)
        (target_out / "graph.json").write_text(json.dumps(network, ensure_ascii=False, separators=(",", ":")))
        graph_markup = (
            '<div class="controls"><input id="graph-search" type="search" placeholder="Search nodes…">'
            '<select id="graph-filter"><option value="">All record types</option></select>'
            '<button id="graph-reset" type="button">Fit</button></div>'
            '<div id="graph-shell"><canvas id="graph-canvas"></canvas><aside id="graph-detail">Select a node.</aside></div>'
            '<script type="module">import { mount } from "../assets/graph-controller.mjs"; '
            'mount("graph-canvas","graph-detail","graph.json");</script>'
            '<script src="../assets/graph-touch.js"></script>'
        )
        packet_html = packet(target, docs, config, network).replace(
            '<div id="graph"></div><script src="../assets/graph.js"></script><script>renderGraph("graph.json")</script>',
            graph_markup,
            1,
        )
        (target_out / "index.html").write_text(themed(packet_html, "../"))
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
                "summary": doc.get("summary") or doc.get("description", ""),
                "url": f"{target}/nodes/{name}.html",
            })
        cfg = config.get("packets", {}).get(target, {})
        cards.append(
            f'<article><span>{len(docs)} records</span><h2><a href="{target}/index.html">{cfg.get("title") or target.replace("-", " ").title()}</a></h2>'
            f'<p>{cfg.get("subtitle") or "StarIntel public-record research"}</p><a href="{target}/index.html">Explore research →</a></article>'
        )

    (output / "search-index.json").write_text(json.dumps(search, ensure_ascii=False, separators=(",", ":")))
    body = (
        "<h1>StarIntel GPT Auto Dig</h1>"
        '<p class="lede">Source-backed research transformed into Org-roam nodes, source inventories, neutral narratives, and interactive exploration graphs.</p>'
        '<div class="notice"><strong>Canonical-data rule:</strong> only StarIntel packets are committed. Org, graph, and HTML are generated. Incremental packets are merged by stable document ID.</div>'
        '<section class="packets">' + "".join(cards) + "</section>"
    )
    (output / "index.html").write_text(themed(page(config.get("site_title", "StarIntel GPT Auto Dig"), body), ""))
