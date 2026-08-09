from __future__ import annotations

import hashlib
import html
import json
import shutil
import unicodedata
from collections import defaultdict
from pathlib import Path
from urllib.parse import quote

from starintel_doc.spec import SCHEMA_VERSION
from starintel_doc.validation import validate_document

from .corpus_dashboard import dashboard_projection, dataset_metrics, datasets_page, root_dashboard_page
from .dashboard import annotate_graph, dashboard_page, document_index, documents_page, graph_page
from .model import discover, graph, org_index, render_org, slug
from .render import node, source_inventory
from .topic_datasets import excluded_source_dataset, load_topic_config, topics_for_document


def themed(markup: str, prefix: str) -> str:
    stylesheet = f'<link rel="stylesheet" href="{prefix}assets/style.css">'
    explorer_stylesheet = f'<link rel="stylesheet" href="{prefix}assets/explorer.css">'
    dashboard_stylesheet = f'<link rel="stylesheet" href="{prefix}assets/adar-dashboard.css">'
    theme_script = f'<script src="{prefix}assets/theme.js"></script>'
    shell_script = f'<script defer src="{prefix}assets/adar-shell.js"></script>'
    dashboard_script = f'<script defer src="{prefix}assets/corpus-dashboard.js"></script>'
    additions = ""
    if explorer_stylesheet not in markup:
        additions += explorer_stylesheet
    if dashboard_stylesheet not in markup:
        additions += dashboard_stylesheet
    if theme_script not in markup:
        additions += theme_script
    if shell_script not in markup:
        additions += shell_script
    if dashboard_script not in markup:
        additions += dashboard_script
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
        "kind": "topic",
        "id": topic_id,
        "dataset": topic_id,
        "title": title,
        "source_target_count": len(source_targets),
        "source_dataset_count": len(source_datasets),
        "source_targets": sorted(source_targets),
        "source_datasets": sorted(source_datasets),
        "url": f"{target}/index.html",
        "download": f"{target}/downloads/starintel-documents.jsonl",
        **dataset_metrics(docs),
    }


def _dataset_key(value: object) -> str:
    normalized = unicodedata.normalize("NFKC", str(value or "unknown")).casefold()
    return " ".join(normalized.replace("_", " ").replace("-", " ").split())


def _write_source_dataset(
    *,
    dataset: str,
    docs: list[dict],
    source_targets_by_id: dict[str, str],
    source_targets: set[str],
    output: Path,
    org_output: Path,
) -> dict[str, object]:
    target = f"dataset-source-{slug(dataset)}"
    target_out = output / target
    node_out = target_out / "nodes"
    org_out = org_output / target
    public_org = output / "org" / target
    downloads = target_out / "downloads"
    for directory in (target_out, node_out, org_out, public_org, downloads):
        directory.mkdir(parents=True, exist_ok=True)

    docs = _latest_documents(docs)
    known = {doc["_id"] for doc in docs}
    target_count = len(source_targets)
    source_config = {
        "packets": {
            target: {
                "title": dataset,
                "subtitle": f"Canonical source dataset aggregated across {target_count:,} research target{'s' if target_count != 1 else ''}.",
            }
        }
    }
    network = annotate_graph(docs, graph(docs))
    (target_out / "graph.json").write_text(json.dumps(network, ensure_ascii=False, separators=(",", ":")))
    (target_out / "documents.json").write_text(json.dumps(document_index(docs), ensure_ascii=False, separators=(",", ":")))
    (target_out / "index.html").write_text(themed(dashboard_page(target, docs, source_config, network), "../"))
    (target_out / "graph.html").write_text(themed(graph_page(target, source_config, network), "../"))
    (target_out / "documents.html").write_text(themed(documents_page(target, docs, source_config), "../"))
    (target_out / "sources.html").write_text(themed(source_inventory(target, docs), "../"))

    index = org_index(dataset, docs)
    (org_out / "index.org").write_text(index)
    (public_org / "index.org").write_text(index)
    (downloads / "starintel-documents.jsonl").write_text(_jsonl(docs))
    manifest = {
        "source_dataset": dataset,
        "record_count": len(docs),
        "source_targets": sorted(source_targets),
    }
    (downloads / "source-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    (downloads / "research-history.json").write_text(json.dumps([manifest], ensure_ascii=False, indent=2) + "\n")

    for doc in docs:
        name = slug(doc["_id"])
        org = render_org(doc, known)
        (org_out / f"{name}.org").write_text(org)
        (public_org / f"{name}.org").write_text(org)
        source_target = quote(source_targets_by_id[doc["_id"]], safe="")
        destination = f"../../{source_target}/nodes/{name}.html"
        (node_out / f"{name}.html").write_text(_topic_node_redirect(destination))

    target_label = f"{target_count:,} research target{'s' if target_count != 1 else ''}"
    return {
        "kind": "source",
        "id": dataset,
        "dataset": dataset,
        "title": dataset,
        "target": target,
        "target_title": target_label,
        "source_target_count": target_count,
        "source_targets": sorted(source_targets),
        "url": f"{target}/index.html",
        "download": f"{target}/downloads/starintel-documents.jsonl",
        **dataset_metrics(docs),
    }


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
    for asset_name in (
        "style.css",
        "explorer.css",
        "theme.js",
        "dashboard.js",
        "adar-dashboard.css",
        "adar-shell.js",
        "corpus-dashboard.js",
        "graph.js",
        "graph-core.mjs",
        "graph-model.mjs",
        "graph-render.mjs",
        "graph-render-scaled.mjs",
        "graph-ui.mjs",
        "graph-controller.mjs",
        "graph-explorer.mjs",
        "graph-touch.js",
    ):
        shutil.copy2(assets / asset_name, asset_output / asset_name)
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

    dataset_rows: list[dict[str, object]] = []
    search: list[dict[str, object]] = []
    topic_documents: dict[str, dict[str, dict]] = defaultdict(dict)
    topic_document_targets: dict[str, dict[str, str]] = defaultdict(dict)
    topic_metadata: dict[str, dict[str, str]] = {}
    topic_targets: dict[str, set[str]] = defaultdict(set)
    topic_sources: dict[str, set[str]] = defaultdict(set)
    source_documents: dict[str, dict[str, dict]] = defaultdict(dict)
    source_document_targets: dict[str, dict[str, str]] = defaultdict(dict)
    source_names: dict[str, str] = {}
    source_targets: dict[str, set[str]] = defaultdict(set)

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

            if excluded_source_dataset(doc.get("dataset"), topic_config):
                continue
            dataset_name = str(doc.get("dataset") or "unknown")
            source_key = _dataset_key(dataset_name)
            old = source_documents[source_key].get(doc["_id"])
            if old is None or str(doc["date_updated"]) >= str(old["date_updated"]):
                source_documents[source_key][doc["_id"]] = doc
                source_document_targets[source_key][doc["_id"]] = target
            source_names.setdefault(source_key, dataset_name)
            source_targets[source_key].add(target)

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

    for source_key, by_id in sorted(source_documents.items()):
        dataset_rows.append(
            _write_source_dataset(
                dataset=source_names[source_key],
                docs=list(by_id.values()),
                source_targets_by_id=source_document_targets[source_key],
                source_targets=source_targets[source_key],
                output=output,
                org_output=org_output,
            )
        )

    dataset_rows.sort(key=lambda row: str(row["dataset"]).lower())
    topic_rows.sort(key=lambda row: str(row["title"]).lower())
    catalog = topic_rows + dataset_rows
    catalog.sort(key=lambda row: (str(row.get("title") or row.get("dataset") or "").lower(), str(row.get("kind") or "")))

    (output / "datasets.json").write_text(json.dumps(dataset_rows, ensure_ascii=False, separators=(",", ":")))
    (output / "topic-datasets.json").write_text(json.dumps(topic_rows, ensure_ascii=False, separators=(",", ":")))
    (output / "dataset-catalog.json").write_text(json.dumps(catalog, ensure_ascii=False, separators=(",", ":")))
    (output / "search-index.json").write_text(json.dumps(search, ensure_ascii=False, separators=(",", ":")))

    projection = dashboard_projection(complete_docs, catalog, search)
    (output / "dashboard-data.json").write_text(json.dumps(projection, ensure_ascii=False, separators=(",", ":")))

    site_title = config.get("site_title", "StarIntel GPT Auto Dig")
    (output / "index.html").write_text(themed(root_dashboard_page(projection, site_title), ""))
    (output / "datasets.html").write_text(themed(datasets_page(catalog, site_title), ""))