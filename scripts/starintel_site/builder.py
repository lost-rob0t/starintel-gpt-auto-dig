from __future__ import annotations

import hashlib
import html
import json
import shutil
from collections import defaultdict
from pathlib import Path
from urllib.parse import quote

from starintel_doc.spec import SCHEMA_VERSION
from starintel_doc.validation import validate_document

from .dashboard import annotate_graph, dashboard_page, document_index, documents_page, graph_page
from .model import discover, graph, org_index, render_org, slug
from .render import node, page, source_inventory
from .topic_datasets import excluded_source_dataset, load_topic_config, topics_for_document


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


def _latest_documents(documents: list[dict]) -> list[dict]:
    by_id: dict[str, dict] = {}
    for doc in documents:
        old = by_id.get(doc["_id"])
        if old is None or str(doc["date_updated"]) >= str(old["date_updated"]):
            by_id[doc["_id"]] = doc
    return sorted(by_id.values(), key=lambda doc: doc["_id"])


def _jsonl(documents: list[dict]) -> str:
    return "".join(json.dumps(doc, ensure_ascii=False, separators=(",", ":")) + "\n" for doc in documents)


def _topic_node_redirect(destination: str) -> str:
    escaped = html.escape(destination, quote=True)
    return (
        "<!doctype html><html><head><meta charset=\"utf-8\">"
        f'<meta http-equiv="refresh" content="0; url={escaped}">'
        f'<link rel="canonical" href="{escaped}"><title>Open document</title></head>'
        f'<body><p><a href="{escaped}">Open the canonical document</a></p></body></html>'
    )


def _write_topic_dataset(
    *,
    topic_id: str,
    title: str,
    subtitle: str,
    docs: list[dict],
    source_targets_by_id: dict[str, str],
    source_targets: set[str],
    source_datasets: set[str],
    output: Path,
    org_output: Path,
) -> dict[str, object]:
    target = f"dataset-{slug(topic_id)}"
    target_out = output / target
    node_out = target_out / "nodes"
    org_out = org_output / target
    public_org = output / "org" / target
    downloads = target_out / "downloads"
    for directory in (target_out, node_out, org_out, public_org, downloads):
        directory.mkdir(parents=True, exist_ok=True)

    docs = _latest_documents(docs)
    known = {doc["_id"] for doc in docs}
    topic_config = {
        "packets": {
            target: {
                "title": title,
                "subtitle": subtitle,
            }
        }
    }
    network = annotate_graph(docs, graph(docs))
    (target_out / "graph.json").write_text(json.dumps(network, ensure_ascii=False, separators=(",", ":")))
    (target_out / "documents.json").write_text(json.dumps(document_index(docs), ensure_ascii=False, separators=(",", ":")))
    (target_out / "index.html").write_text(themed(dashboard_page(target, docs, topic_config, network), "../"))
    (target_out / "graph.html").write_text(themed(graph_page(target, topic_config, network), "../"))
    (target_out / "documents.html").write_text(themed(documents_page(target, docs, topic_config), "../"))
    (target_out / "sources.html").write_text(themed(source_inventory(target, docs), "../"))

    index = org_index(title, docs)
    (org_out / "index.org").write_text(index)
    (public_org / "index.org").write_text(index)
    (downloads / "starintel-documents.jsonl").write_text(_jsonl(docs))
    manifest = {
        "topic_dataset": topic_id,
        "title": title,
        "record_count": len(docs),
        "source_targets": sorted(source_targets),
        "source_datasets": sorted(source_datasets),
    }
    (downloads / "topic-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    (downloads / "research-history.json").write_text(json.dumps([manifest], ensure_ascii=False, indent=2) + "\n")

    for doc in docs:
        name = slug(doc["_id"])
        org = render_org(doc, known)
        (org_out / f"{name}.org").write_text(org)
        (public_org / f"{name}.org").write_text(org)
        source_target = quote(source_targets_by_id[doc["_id"]], safe="")
        destination = f"../../{source_target}/nodes/{name}.html"
        (node_out / f"{name}.html").write_text(_topic_node_redirect(destination))

    return {
        "dataset": topic_id,
        "title": title,
        "record_count": len(docs),
        "source_target_count": len(source_targets),
        "source_dataset_count": len(source_datasets),
        "source_targets": sorted(source_targets),
        "source_datasets": sorted(source_datasets),
        "updated_through": max(str(doc.get("date_updated", "")) for doc in docs),
        "url": f"{target}/index.html",
        "download": f"{target}/downloads/starintel-documents.jsonl",
    }


def _topic_card(row: dict[str, object]) -> str:
    url = html.escape(str(row["url"]))
    title = html.escape(str(row["title"]))
    updated = html.escape(str(row["updated_through"]))
    return (
        f'<article><span>{int(row["record_count"]):,} records · {int(row["source_target_count"]):,} targets</span>'
        f'<h2><a href="{url}">{title}</a></h2>'
        f'<p>{int(row["source_dataset_count"]):,} source datasets · updated through {updated}</p>'
        f'<a href="{url}">Open merged dataset →</a></article>'
    )


def _source_dataset_card(row: dict[str, object]) -> str:
    url = html.escape(str(row["url"]))
    target_title = html.escape(str(row["target_title"]))
    dataset = html.escape(str(row["dataset"]))
    updated = html.escape(str(row["updated_through"]))
    return (
        f'<article><span>{int(row["record_count"]):,} records · {target_title}</span>'
        f'<h2><a href="{url}">{dataset}</a></h2>'
        f'<p>Updated through {updated}</p>'
        f'<a href="{url}">Browse source dataset →</a></article>'
    )


def build_site(input_root: Path, output: Path, org_output: Path, config_path: Path, assets: Path) -> None:
    packets = discover(input_root)
    config = json.loads(config_path.read_text(encoding="utf-8")) if config_path.exists() else {}
    topic_config = load_topic_config(config_path.parent / "manifests" / "topic-datasets.json")
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

    complete_docs = _latest_documents([doc for item in packets for doc in item.documents])
    root_downloads = output / "downloads"
    root_downloads.mkdir()
    corpus_name = "starintel-complete-corpus.jsonl"
    corpus_text = _jsonl(complete_docs)
    (root_downloads / corpus_name).write_text(corpus_text)

    corpus_timestamp = max(str(doc["date_updated"]) for doc in complete_docs)
    corpus_manifest = {
        "_id": "starintel:dataset-manifest:auto-dig-complete-corpus",
        "dataset": "starintel-auto-dig-complete-corpus",
        "dtype": "dataset-manifest",
        "schema_version": SCHEMA_VERSION,
        "version": 1,
        "date_added": corpus_timestamp,
        "date_updated": corpus_timestamp,
        "title": "StarIntel Auto Dig complete corpus",
        "sources": [],
        "evidence": [],
        "data": {
            "manifest_type": "dataset",
            "name": "StarIntel Auto Dig complete corpus",
            "counts_by_dtype": {
                dtype: sum(doc["dtype"] == dtype for doc in complete_docs)
                for dtype in sorted({str(doc["dtype"]) for doc in complete_docs})
            },
            "record_count": len(complete_docs),
            "hash_algorithm": "sha256",
            "content_hash": hashlib.sha256(corpus_text.encode("utf-8")).hexdigest(),
            "files": [
                {
                    "path": corpus_name,
                    "media_type": "application/x-ndjson",
                    "size_bytes": len(corpus_text.encode("utf-8")),
                }
            ],
            "schema_versions": sorted({str(doc["schema_version"]) for doc in complete_docs}),
            "generated_at": corpus_timestamp,
        },
    }
    validate_document(corpus_manifest)
    (root_downloads / "starintel-complete-corpus.manifest.json").write_text(
        json.dumps(corpus_manifest, ensure_ascii=False, indent=2) + "\n"
    )

    grouped = defaultdict(list)
    for item in packets:
        grouped[item.target].append(item)

    cards = []
    dataset_rows: list[dict[str, object]] = []
    search = []
    topic_documents: dict[str, dict[str, dict]] = defaultdict(dict)
    topic_document_targets: dict[str, dict[str, str]] = defaultdict(dict)
    topic_metadata: dict[str, dict[str, str]] = {}
    topic_targets: dict[str, set[str]] = defaultdict(set)
    topic_sources: dict[str, set[str]] = defaultdict(set)

    for target, target_packets in sorted(grouped.items()):
        docs = _latest_documents([doc for item in target_packets for doc in item.documents])
        known = {doc["_id"] for doc in docs}
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

        (downloads / "starintel-documents.jsonl").write_text(_jsonl(docs))
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
            search.append(
                {
                    "target": target,
                    "id": doc["_id"],
                    "title": doc.get("title") or doc.get("name") or doc["_id"],
                    "dtype": doc["dtype"],
                    "dataset": doc.get("dataset", ""),
                    "summary": doc.get("summary") or doc.get("description", ""),
                    "url": f"{target}/nodes/{name}.html",
                }
            )
            for topic in topics_for_document(target, doc, topic_config):
                topic_id = topic["id"]
                old = topic_documents[topic_id].get(doc["_id"])
                if old is None or str(doc["date_updated"]) >= str(old["date_updated"]):
                    topic_documents[topic_id][doc["_id"]] = doc
                    topic_document_targets[topic_id][doc["_id"]] = target
                topic_metadata[topic_id] = topic
                topic_targets[topic_id].add(target)
                if not excluded_source_dataset(doc.get("dataset"), topic_config):
                    topic_sources[topic_id].add(str(doc.get("dataset") or "unknown"))

        cfg = config.get("packets", {}).get(target, {})
        target_title = cfg.get("title") or target.replace("-", " ").title()
        cards.append(
            f'<article><span>{len(docs)} records</span><h2><a href="{target}/index.html">{html.escape(str(target_title))}</a></h2>'
            f'<p>{html.escape(str(cfg.get("subtitle") or "StarIntel public-record research"))}</p><a href="{target}/index.html">Open dashboard →</a></article>'
        )

        datasets: dict[str, list[dict]] = defaultdict(list)
        for doc in docs:
            if excluded_source_dataset(doc.get("dataset"), topic_config):
                continue
            datasets[str(doc.get("dataset") or "unknown")].append(doc)
        for dataset, dataset_docs in sorted(datasets.items()):
            dataset_rows.append(
                {
                    "dataset": dataset,
                    "target": target,
                    "target_title": target_title,
                    "record_count": len(dataset_docs),
                    "updated_through": max(str(doc.get("date_updated", "")) for doc in dataset_docs),
                    "url": f"{target}/documents.html?dataset={quote(dataset, safe='')}",
                }
            )

    topic_rows = []
    for topic_id, by_id in sorted(topic_documents.items()):
        metadata = topic_metadata[topic_id]
        topic_rows.append(
            _write_topic_dataset(
                topic_id=topic_id,
                title=metadata["title"],
                subtitle=metadata["subtitle"],
                docs=list(by_id.values()),
                source_targets_by_id=topic_document_targets[topic_id],
                source_targets=topic_targets[topic_id],
                source_datasets=topic_sources[topic_id],
                output=output,
                org_output=org_output,
            )
        )

    dataset_rows.sort(key=lambda row: (str(row["dataset"]).lower(), str(row["target"])))
    topic_rows.sort(key=lambda row: str(row["title"]).lower())
    (output / "datasets.json").write_text(json.dumps(dataset_rows, ensure_ascii=False, separators=(",", ":")))
    (output / "topic-datasets.json").write_text(json.dumps(topic_rows, ensure_ascii=False, separators=(",", ":")))
    (output / "search-index.json").write_text(json.dumps(search, ensure_ascii=False, separators=(",", ":")))

    topic_cards = "".join(_topic_card(row) for row in topic_rows)
    dataset_cards = "".join(_source_dataset_card(row) for row in dataset_rows)
    body = (
        "<h1>StarIntel GPT Auto Dig</h1>"
        '<p class="lede">Source-backed research transformed into dashboards, Org-roam nodes, source inventories, and progressive graph explorers.</p>'
        '<div class="dashboard-actions"><a class="primary-action" href="downloads/starintel-complete-corpus.jsonl" download>Download complete corpus</a>'
        '<a href="downloads/starintel-complete-corpus.manifest.json" download>Download corpus manifest</a></div>'
        '<div class="notice"><strong>Dataset rule:</strong> topical datasets merge related research across packets. Source datasets remain available. The obsolete daily dataset is excluded from the generated catalog.</div>'
        '<section class="stats dashboard-stats">'
        f'<div><strong>{len(grouped):,}</strong><span>research targets</span></div>'
        f'<div><strong>{len(topic_rows):,}</strong><span>topic datasets</span></div>'
        f'<div><strong>{len(dataset_rows):,}</strong><span>source datasets</span></div>'
        f'<div><strong>{len(complete_docs):,}</strong><span>canonical records</span></div>'
        "</section>"
        '<section id="topic-datasets"><div class="section-head"><div><h2>Topic datasets</h2><p>Merged by subject across all matching packets and source datasets.</p></div>'
        '<a href="topic-datasets.json">Topic index JSON →</a></div><div class="packets dataset-catalog">'
        + topic_cards
        + "</div></section>"
        '<section><div class="section-head"><div><h2>Research targets</h2><p>Original packet dashboards remain intact.</p></div></div>'
        '<div class="packets">'
        + "".join(cards)
        + "</div></section>"
        '<section id="datasets"><div class="section-head"><div><h2>Source datasets</h2><p>Original datasets, except the removed daily bucket.</p></div>'
        '<a href="datasets.json">Source index JSON →</a></div><div class="packets dataset-catalog">'
        + dataset_cards
        + "</div></section>"
    )
    (output / "index.html").write_text(themed(page(config.get("site_title", "StarIntel GPT Auto Dig"), body), ""))
