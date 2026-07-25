from __future__ import annotations

import base64
import gzip
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

REQUIRED = {"_id", "dataset", "dtype", "version", "sources", "date_added", "date_updated"}

ENTITY_PREDICATES = {
    "co_founded", "chairs", "chief_executive_of", "chairs_committee",
    "serves_on_board_of", "serves_as_trustee_of", "serves_on",
    "serves_on_advisory_board_of", "serves_on_executive_committee_of",
    "co_chairs", "co_namesake_of", "founded", "employed_by", "organization",
    "principal", "contractor", "facility", "member", "administration",
    "candidate", "participants", "parties", "plaintiffs", "defendants",
    "acquirer", "target", "seller", "buyer_group", "appointed_person",
    "co_appointee", "former_blackrock_executive_became",
    "former_fink_chief_of_staff_became",
}

COLORS = {
    "person": "#f59e0b", "organization": "#22c55e", "relation": "#38bdf8",
    "event": "#a78bfa", "claim": "#fb7185", "analysis": "#f97316",
    "concept": "#eab308", "investigation-target": "#ef4444",
    "financial-observation": "#14b8a6", "education": "#60a5fa",
    "employment": "#818cf8", "dataset-manifest": "#64748b", "entity": "#94a3b8",
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


def read_canonical(path: Path) -> str:
    if path.name.endswith(".parts"):
        names = [line.strip() for line in path.read_text().splitlines() if line.strip()]
        encoded = "".join((path.parent / name).read_text().strip() for name in names).encode()
        return gzip.decompress(base64.b64decode(encoded)).decode("utf-8")
    if path.name.endswith(".gz.b64"):
        return gzip.decompress(base64.b64decode(path.read_bytes())).decode("utf-8")
    return path.read_text(encoding="utf-8")


def load(path: Path) -> list[dict[str, Any]]:
    docs, seen = [], set()
    for number, line in enumerate(read_canonical(path).splitlines(), 1):
        if not line.strip():
            continue
        try:
            doc = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{number}: invalid JSON: {exc}") from exc
        missing = REQUIRED - doc.keys()
        if missing:
            raise ValueError(f"{path}:{number}: missing {sorted(missing)}")
        if doc["_id"] in seen:
            raise ValueError(f"{path}:{number}: duplicate _id {doc['_id']}")
        if not isinstance(doc["sources"], list):
            raise ValueError(f"{path}:{number}: sources must be a list")
        seen.add(doc["_id"])
        docs.append(doc)
    if not docs:
        raise ValueError(f"{path}: empty dataset")
    return docs


def discover(root: Path) -> list[Packet]:
    paths = list(root.glob("*/*/starintel-documents.jsonl"))
    paths += list(root.glob("*/*/starintel-documents.jsonl.gz.b64"))
    paths += list(root.glob("*/*/starintel-documents.jsonl.gz.b64.parts"))
    packets = []
    for path in sorted(paths):
        rel = path.relative_to(root)
        packets.append(Packet(rel.parts[0], rel.parts[1], path, load(path)))
    if not packets:
        raise ValueError(f"No canonical StarIntel datasets below {root}")
    return packets


def summary(doc: dict[str, Any]) -> str:
    for key in ("summary", "description", "definition"):
        value = doc.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return doc.get("title") or doc["_id"]


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
    found = set()
    for value in strings(doc):
        target = normalize_id(value, known)
        if target and target != doc["_id"]:
            found.add(target)
    subject = doc.get("subject")
    if isinstance(subject, dict) and isinstance(subject.get("entity_id"), str):
        target = normalize_id(subject["entity_id"], known)
        if target and target != doc["_id"]:
            found.add(target)
    return sorted(found)


def entity(value: Any) -> tuple[str, str] | None:
    if isinstance(value, dict):
        if isinstance(value.get("entity_id"), str):
            label = value.get("name") or value.get("organization") or value.get("person") or value["entity_id"]
            return value["entity_id"], str(label)
        for key in ("organization", "person", "candidate", "administration", "firm"):
            if isinstance(value.get(key), str):
                return f"entity:{slug(value[key])}", value[key]
    if isinstance(value, str) and 2 < len(value) < 100:
        return f"entity:{slug(value)}", value
    return None


def graph(docs: list[dict[str, Any]]) -> dict[str, Any]:
    known = {doc["_id"] for doc in docs}
    nodes, edges, edge_keys = {}, [], set()

    def add_node(node_id: str, label: str, group: str, href: str | None = None, detail: str = "") -> None:
        nodes.setdefault(node_id, {
            "id": node_id, "label": label, "group": group,
            "color": COLORS.get(group, COLORS["entity"]), "href": href, "detail": detail,
        })

    def add_edge(source: str, target: str, label: str) -> None:
        key = (source, target, label)
        if source != target and key not in edge_keys:
            edge_keys.add(key)
            edges.append({"source": source, "target": target, "label": label})

    for doc in docs:
        add_node(doc["_id"], doc.get("title") or doc["_id"], doc.get("dtype", "entity"),
                 f"nodes/{slug(doc['_id'])}.html", summary(doc))

    for doc in docs:
        for target in links(doc, known):
            add_edge(doc["_id"], target, "references")
        subject = doc.get("subject")
        if isinstance(subject, dict) and isinstance(subject.get("entity_id"), str):
            raw = subject["entity_id"]
            subject_id = normalize_id(raw, known) or raw
            add_node(subject_id, subject.get("name") or raw, "person")
            add_edge(subject_id, doc["_id"], "documented by")
        for pred in doc.get("predicates", []):
            if not isinstance(pred, dict) or pred.get("predicate") not in ENTITY_PREDICATES:
                continue
            values = pred.get("object")
            values = values if isinstance(values, list) else [values]
            for item in values:
                found = entity(item)
                if not found:
                    continue
                raw, label = found
                target = normalize_id(raw, known) or raw
                add_node(target, label, "entity")
                add_edge(doc["_id"], target, str(pred["predicate"]).replace("_", " "))
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
    status = doc.get("verification", {}).get("status", "recorded").upper()
    tags = sorted({slug(str(tag)) for tag in doc.get("tags", [])} | {slug(doc["dtype"]), "starintel"})
    out = [
        ":PROPERTIES:", f":ID:       {org_id(doc['_id'])}", f":STARINTEL_ID: {doc['_id']}",
        ":END:", f"#+title: {title}", f"#+description: {description}",
        f"#+status: {status}", f"#+filetags: :{':'.join(tags)}:", "",
        "* Record Summary", "", description, "", "* Metadata", "",
        "| Field | Value |", "|-",
        f"| ID | ={doc['_id']}= |", f"| Dataset | ={doc['dataset']}= |",
        f"| Type | ={doc['dtype']}= |", f"| Version | ={doc['version']}= |",
        f"| Confidence | {doc.get('confidence', 'not assigned')} |",
        f"| Updated | {doc['date_updated']} |", "",
    ]
    related = links(doc, known)
    if related:
        out += ["* Related Nodes", ""]
        out += [f"- [[id:{org_id(target)}][{target}]]" for target in related]
        out.append("")
    if doc.get("predicates"):
        out += ["* Predicates", ""]
        for pred in doc["predicates"]:
            if not isinstance(pred, dict):
                continue
            out += [f"** {pred.get('predicate', 'predicate')}", "", org_value(pred.get("object")), ""]
    omitted = {
        "_id", "dataset", "dtype", "version", "date_added", "date_updated", "title",
        "summary", "description", "definition", "sources", "predicates", "tags",
        "confidence", "verification", "subject",
    }
    content = [(key, value) for key, value in doc.items() if key not in omitted]
    if content:
        out += ["* Record Content", ""]
        for key, value in content:
            out += [f"** {key.replace('_', ' ').title()}", "", org_value(value), ""]
    out += ["* Sources", ""]
    for source in doc.get("sources", []):
        title = source.get("title") or source.get("publisher") or source.get("url") or "Source"
        citation = f"[[{source['url']}][{title}]]" if source.get("url") else title
        out.append(f"- {citation}")
    if not doc.get("sources"):
        out.append("- No external source attached.")
    out += [
        "", "* Raw StarIntel Document", "", "#+begin_src json",
        json.dumps(doc, ensure_ascii=False, indent=2), "#+end_src", "",
        "* Footnotes and Glossary", "",
        "[fn:starintel] StarIntel: A document-based research system that preserves claims, relations, sources, confidence, and provenance.",
        "[fn:corporatism] Corporatism: Structured representation or policymaking through organized functional groups.",
        "[fn:fascism] Fascism: An ultranationalist authoritarian project that rejects pluralism and liberal democracy.",
        "",
    ]
    return "\n".join(out)


def org_index(target: str, docs: list[dict[str, Any]]) -> str:
    out = [
        ":PROPERTIES:", f":ID:       starintel-index-{slug(target)}", ":END:",
        f"#+title: {target.replace('-', ' ').title()} StarIntel Exploration Index",
        "#+description: Generated navigation index from canonical StarIntel JSONL.",
        "#+status: GENERATED", "#+filetags: :starintel:index:generated:", "",
        "* Records", "",
    ]
    for doc in sorted(docs, key=lambda d: (d["dtype"], d.get("title", d["_id"]))):
        out.append(f"- [[id:{org_id(doc['_id'])}][{doc.get('title') or doc['_id']}]] =({doc['dtype']})=")
    out += ["", "* Build Provenance", "", "Generated from the canonical packet. JSONL remains the source of truth.", ""]
    return "\n".join(out)
