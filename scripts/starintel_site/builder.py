from __future__ import annotations

import json
import shutil
from collections import defaultdict
from pathlib import Path

from .model import discover, graph, org_index, read_canonical, render_org, slug
from .render import node, packet, page, source_inventory


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
    shutil.copy2(assets / "graph.js", asset_output / "graph.js")
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
        docs = list(by_id.values())
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
        (target_out / "index.html").write_text(packet(target, docs, config, network))
        (target_out / "sources.html").write_text(source_inventory(target, docs))
        index = org_index(target, docs)
        (org_out / "index.org").write_text(index)
        (public_org / "index.org").write_text(index)

        newest = sorted(target_packets, key=lambda item: item.run)[-1]
        (downloads / "starintel-documents.jsonl").write_text(read_canonical(newest.path))
        for doc in docs:
            name = slug(doc["_id"])
            org = render_org(doc, known)
            (org_out / f"{name}.org").write_text(org)
            (public_org / f"{name}.org").write_text(org)
            (node_out / f"{name}.html").write_text(node(doc, target, known))
            search.append({
                "target": target, "id": doc["_id"], "title": doc.get("title") or doc["_id"],
                "dtype": doc["dtype"], "summary": doc.get("summary", ""), "url": f"{target}/nodes/{name}.html",
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
        '<div class="notice"><strong>Canonical-data rule:</strong> only the StarIntel packet is committed. Org, graph, and HTML are generated.</div>'
        '<section class="packets">' + "".join(cards) + "</section>"
    )
    (output / "index.html").write_text(page(config.get("site_title", "StarIntel GPT Auto Dig"), body))
