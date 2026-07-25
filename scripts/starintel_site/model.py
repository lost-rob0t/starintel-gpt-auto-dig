from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from starintel_doc.store import read_transport
from starintel_doc.validation import validate_document

COLORS = {
    "person": "#f59e0b",
    "org": "#22c55e",
    "relation": "#38bdf8",
    "event": "#a78bfa",
    "claim": "#fb7185",
    "analysis": "#f97316",
    "concept": "#eab308",
    "investigation-target": "#ef4444",
    "financial-observation": "#14b8a6",
    "education": "#60a5fa",
    "employment": "#818cf8",
    "dataset-manifest": "#64748b",
    "entity": "#94a3b8",
}


@dataclass(frozen=True)
class Packet:
    target: str
    run: str
    path: Path
    documents: list[dict[str, Any]]


def slug(value: str) -> str:
    value = re.sub(r"^starintel:", "", value.lower().strip())
    return re.sub(r"[^a-z0-9]+", "-", value).strip("-") or "record"


def org_id(value: str) -> str:
    return "starintel-" + slug(value)


def load(path: Path) -> list[dict[str, Any]]:
    docs: list[dict[str, Any]] = []
    seen: set[str] = set()
    for number, line in enumerate(read_transport(path).splitlines(), 1):
        if not line.strip():
            continue
        try:
            doc = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{number}: invalid JSON: {exc}") from exc
        validate_document(doc)
        if doc["_id"] in seen:
            raise ValueError(f"{path}:{number}: duplicate _id {doc['_id']}")
        seen.add(doc["_id"])
        docs.append(doc)
    if not docs:
        raise ValueError(f"{path}: empty dataset")
    return docs


def discover(root: Path) -> list[Packet]:
    paths = list(root.glob("*/*/starintel-documents.jsonl"))
    paths += list(root.glob("*/*/starintel-documents.jsonl.gz.b64"))
    paths += list(root.glob("*/*/starintel-documents.jsonl.gz.b64.parts"))
    packets: list[Packet] = []
    seen_dirs: set[Path] = set()
    for path in sorted(paths):
        if path.parent in seen_dirs:
            continue
        seen_dirs.add(path.parent)
        preferred = path.parent / "starintel-documents.jsonl"
        selected = preferred if preferred.exists() else path
        rel = selected.relative_to(root)
        packets.append(Packet(rel.parts[0], rel.parts[1], selected, load(selected)))
    if not packets:
        raise ValueError(f"No canonical StarIntel datasets below {root}")
    return packets


def summary(doc: dict[str, Any]) -> str:
    for key in ("summary", "description"):
        value = doc.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    data = doc.get("data", {})
    for key in ("description", "definition", "claim", "bio", "business", "mission"):
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return doc.get("title") or doc["_id"]


def source_record(source: Any) -> dict[str, Any]:
    if isinstance(source, dict):
        result = dict(source)
        if result.get("uri") and not result.get("url"):
            result["url"] = result["uri"]
        if result.get("url") and not result.get("uri"):
            result["uri"] = result["url"]
        if result.get("name") and not result.get("title"):
            result["title"] = result["name"]
        if result.get("retrieved_at") and not result.get("accessed"):
            result["accessed"] = result["retrieved_at"]
        return result
    if isinstance(source, str):
        return {"url": source, "uri": source, "title": source}
    return {"title": str(source)}


def strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from strings(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from strings(item)


def normalize_id(value: str, known: set[str]) -> str | None:
    if value in known:
        return value
    candidate = value if value.startswith("starintel:") else f"starintel:{value}"
    return candidate if candidate in known else None


def links(doc: dict[str, Any], known: set[str]) -> list[str]:
    found: set[str] = set()
    for value in strings(doc):
        target = normalize_id(value, known)
        if target and target != doc["_id"]:
            found.add(target)
    return sorted(found)


def _endpoint_ids(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict) and isinstance(value.get("id"), str):
        return [value["id"]]
    if isinstance(value, list):
        out: list[str] = []
        for item in value:
            out.extend(_endpoint_ids(item))
        return out
    return []


def graph(docs: list[dict[str, Any]]) -> dict[str, Any]:
    known = {doc["_id"] for doc in docs}
    by_id = {doc["_id"]: doc for doc in docs}
    nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, str]] = []
    edge_keys: set[tuple[str, str, str]] = set()

    def label_for(node_id: str) -> str:
        doc = by_id.get(node_id)
        if not doc:
            return node_id
        data = doc.get("data", {})
        return doc.get("title") or data.get("display_name") or data.get("name") or data.get("full_name") or node_id

    def add_node(node_id: str, group: str | None = None) -> bool:
        doc = by_id.get(node_id)
        if doc and doc.get("dtype") == "relation":
            return False
        actual_group = group or (doc.get("dtype") if doc else "entity")
        nodes.setdefault(
            node_id,
            {
                "id": node_id,
                "label": label_for(node_id),
                "group": actual_group,
                "color": COLORS.get(actual_group, COLORS["entity"]),
                "href": f"nodes/{slug(node_id)}.html" if node_id in known else None,
                "detail": summary(doc) if doc else "Referenced entity",
            },
        )
        return True

    def add_edge(source: str, target: str, label: str) -> None:
        key = (source, target, label)
        if source in nodes and target in nodes and source != target and key not in edge_keys:
            edge_keys.add(key)
            edges.append({"source": source, "target": target, "label": label})

    for doc in docs:
        if doc.get("dtype") != "relation":
            add_node(doc["_id"])

    for doc in docs:
        if doc.get("dtype") == "relation":
            data = doc.get("data", {})
            subjects = _endpoint_ids(data.get("subject"))
            objects = _endpoint_ids(data.get("object"))
            predicate = str(data.get("predicate") or "related to").replace("_", " ")
            for subject in subjects:
                add_node(subject)
                for object_id in objects:
                    add_node(object_id)
                    add_edge(subject, object_id, predicate)
            continue
        for target in links(doc, known):
            add_edge(doc["_id"], target, "references")
    return {"nodes": list(nodes.values()), "edges": edges}


def org_value(value: Any, indent: int = 0) -> str:
    prefix = " " * indent
    if isinstance(value, str):
        return value
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, list):
        return "\n".join(f"{prefix}- {org_value(item, indent + 2)}" for item in value)
    return "#+begin_src json\n" + json.dumps(value, ensure_ascii=False, indent=2) + "\n#+end_src"


def render_org(doc: dict[str, Any], known: set[str]) -> str:
    title = doc.get("title") or doc["_id"]
    description = summary(doc).replace("\n", " ")
    status = doc.get("verification", {}).get("status", doc.get("status", "recorded")).upper()
    tags = sorted({slug(str(tag)) for tag in doc.get("tags", [])} | {slug(doc["dtype"]), "starintel"})
    confidence = doc.get("assessment", {}).get("confidence", "not assigned")
    out = [
        ":PROPERTIES:",
        f":ID:       {org_id(doc['_id'])}",
        f":STARINTEL_ID: {doc['_id']}",
        ":END:",
        f"#+title: {title}",
        f"#+description: {description}",
        f"#+status: {status}",
        f"#+filetags: :{':'.join(tags)}:",
        "",
        "* Record Summary",
        "",
        description,
        "",
        "* Metadata",
        "",
        "| Field | Value |",
        "|-",
        f"| ID | ={doc['_id']}= |",
        f"| Dataset | ={doc['dataset']}= |",
        f"| Type | ={doc['dtype']}= |",
        f"| Schema | ={doc['schema_version']}= |",
        f"| Version | ={doc['version']}= |",
        f"| Confidence | {confidence} |",
        f"| Updated | {doc['date_updated']} |",
        "",
    ]
    related = links(doc, known)
    if related:
        out += ["* Related Nodes", ""]
        out += [f"- [[id:{org_id(target)}][{target}]]" for target in related]
        out.append("")
    data = doc.get("data", {})
    if data:
        out += ["* Type-Specific Data", ""]
        for key, value in data.items():
            out += [f"** {key.replace('_', ' ').title()}", "", org_value(value), ""]
    metadata_keys = (
        "temporal", "provenance", "assessment", "verification", "handling",
        "lineage", "quality", "workflow", "geospatial", "identifiers",
        "evidence", "attachments", "extensions",
    )
    out += ["* Metadata Detail", ""]
    for key in metadata_keys:
        value = doc.get(key)
        if value not in (None, {}, []):
            out += [f"** {key.replace('_', ' ').title()}", "", org_value(value), ""]
    out += ["* Sources", ""]
    for raw_source in doc.get("sources", []):
        source = source_record(raw_source)
        source_title = source.get("title") or source.get("publisher") or source.get("url") or "Source"
        citation = f"[[{source['url']}][{source_title}]]" if source.get("url") else source_title
        out.append(f"- {citation}")
    if not doc.get("sources"):
        out.append("- No source attached.")
    out += [
        "",
        "* Raw StarIntel Document",
        "",
        "#+begin_src json",
        json.dumps(doc, ensure_ascii=False, indent=2),
        "#+end_src",
        "",
    ]
    return "\n".join(out)


def org_index(target: str, docs: list[dict[str, Any]]) -> str:
    out = [
        ":PROPERTIES:",
        f":ID:       starintel-index-{slug(target)}",
        ":END:",
        f"#+title: {target.replace('-', ' ').title()} StarIntel Exploration Index",
        "#+description: Generated navigation index from canonical StarIntel v0.9.0 JSONL.",
        "#+status: GENERATED",
        "#+filetags: :starintel:index:generated:",
        "",
        "* Records",
        "",
    ]
    for doc in sorted(docs, key=lambda d: (d["dtype"], d.get("title", d["_id"]))):
        out.append(f"- [[id:{org_id(doc['_id'])}][{doc.get('title') or doc['_id']}]] =({doc['dtype']})=")
    out += ["", "* Build Provenance", "", "Generated from canonical StarIntel v0.9.0 packets. JSONL remains the source of truth.", ""]
    return "\n".join(out)
