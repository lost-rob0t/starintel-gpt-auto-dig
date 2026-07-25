from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any, Iterable

from .model import Document, stable_id
from .store import LocatedDocument


@dataclass(frozen=True, slots=True)
class Candidate:
    target_id: str
    target_type: str
    score: float
    reasons: tuple[str, ...]
    seed_ids: tuple[str, ...]


DTYPE_PRIOR = {
    "org": 2.2,
    "person": 1.9,
    "product": 1.7,
    "contract": 2.1,
    "procurement": 2.0,
    "lobbying-filing": 2.0,
    "legal-case": 1.9,
    "event": 1.5,
    "claim": 1.4,
    "financial-observation": 1.5,
    "policy": 1.6,
    "asset": 1.2,
    "domain": 1.1,
    "host": 1.1,
    "url": 0.8,
}


def _endpoint_id(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value] if value.startswith("starintel:") else []
    if isinstance(value, dict):
        value = value.get("id")
        return [value] if isinstance(value, str) and value.startswith("starintel:") else []
    if isinstance(value, list):
        out: list[str] = []
        for item in value:
            out.extend(_endpoint_id(item))
        return out
    return []


def _references(value: Any, key: str = "") -> list[str]:
    out: list[str] = []
    if isinstance(value, str):
        if value.startswith("starintel:") and (key.endswith("_id") or key.endswith("_ids") or key in {"subject", "object", "target", "source"}):
            out.append(value)
    elif isinstance(value, list):
        for item in value:
            out.extend(_references(item, key))
    elif isinstance(value, dict):
        for child_key, item in value.items():
            out.extend(_references(item, child_key))
    return out


def select_candidates(
    documents: Iterable[LocatedDocument],
    *,
    limit: int = 20,
    exclude_ids: set[str] | None = None,
) -> list[Candidate]:
    docs = [located.document for located in documents]
    by_id = {str(doc.get("_id")): doc for doc in docs if doc.get("_id")}
    excluded = set(exclude_ids or set())
    excluded.update(
        str(doc.get("data", {}).get("target_id"))
        for doc in docs
        if doc.get("dtype") in {"target", "investigation-target"}
    )
    excluded.discard("")
    excluded.discard("None")

    degree: Counter[str] = Counter()
    seeds: dict[str, set[str]] = defaultdict(set)
    reasons: dict[str, list[str]] = defaultdict(list)

    for doc in docs:
        doc_id = str(doc.get("_id", ""))
        refs = set(_references(doc))
        if doc.get("dtype") == "relation":
            data = doc.get("data", {})
            refs.update(_endpoint_id(data.get("subject")))
            refs.update(_endpoint_id(data.get("object")))
        for ref in refs:
            if ref == doc_id:
                continue
            degree[ref] += 1
            if doc_id:
                seeds[ref].add(doc_id)

    candidates: list[Candidate] = []
    for doc_id, doc in by_id.items():
        dtype = str(doc.get("dtype", "document"))
        if doc_id in excluded or dtype in {"relation", "target", "investigation-target", "dataset-manifest", "actor-manifest", "research-pass"}:
            continue
        prior = DTYPE_PRIOR.get(dtype, 0.5)
        score = prior
        why = [f"dtype prior {dtype}={prior:.2f}"]
        connections = degree.get(doc_id, 0)
        if connections:
            connection_score = min(3.0, connections * 0.25)
            score += connection_score
            why.append(f"referenced by {connections} records (+{connection_score:.2f})")
        assessment = doc.get("assessment", {})
        for field, weight in (("relevance", 1.5), ("priority", 1.5), ("threat", 1.0), ("confidence", 0.8), ("impact", 0.8)):
            value = assessment.get(field)
            if isinstance(value, (int, float)):
                contribution = max(0.0, min(1.0, float(value))) * weight
                score += contribution
                why.append(f"{field}={value:.2f} (+{contribution:.2f})")
        source_score = min(1.0, len(doc.get("sources", [])) * 0.15)
        evidence_score = min(1.0, len(doc.get("evidence", [])) * 0.2)
        if source_score:
            score += source_score
            why.append(f"{len(doc.get('sources', []))} sources (+{source_score:.2f})")
        if evidence_score:
            score += evidence_score
            why.append(f"{len(doc.get('evidence', []))} evidence items (+{evidence_score:.2f})")
        gaps = assessment.get("gaps", [])
        unresolved = doc.get("verification", {}).get("unresolved", [])
        open_count = len(gaps) + len(unresolved)
        if open_count:
            open_score = min(1.5, open_count * 0.3)
            score += open_score
            why.append(f"{open_count} unresolved gaps (+{open_score:.2f})")
        candidates.append(
            Candidate(
                target_id=doc_id,
                target_type=dtype,
                score=round(score, 4),
                reasons=tuple(why),
                seed_ids=tuple(sorted(seeds.get(doc_id, set()))),
            )
        )

    candidates.sort(key=lambda item: (-item.score, item.target_type, item.target_id))
    return candidates[:limit]


def candidate_documents(
    candidates: Iterable[Candidate],
    *,
    dataset: str,
    root_target_id: str = "",
    depth: int = 1,
    max_depth: int = 3,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for candidate in candidates:
        doc_id = stable_id("investigation-target", candidate.target_id, depth, root_target_id)
        document = Document.create(
            "investigation-target",
            dataset,
            doc_id=doc_id,
            title=f"Recursive dig target: {candidate.target_id}",
            summary=f"Selected from existing StarIntel records with score {candidate.score:.4f}.",
            tags=["auto-dig", "recursive-target"],
            workflow={
                "research_status": "queued",
                "priority": candidate.score,
                "recursion_depth": depth,
                "max_depth": max_depth,
                "root_target_id": root_target_id,
                "selected_from": list(candidate.seed_ids),
                "selection_reason": list(candidate.reasons),
                "selection_score": candidate.score,
            },
            data={
                "target": candidate.target_id,
                "target_id": candidate.target_id,
                "target_type": candidate.target_type,
                "seed_ids": list(candidate.seed_ids),
                "depth": depth,
                "max_depth": max_depth,
                "priority": candidate.score,
                "score": candidate.score,
                "selection_reason": list(candidate.reasons),
                "status": "queued",
            },
        )
        out.append(document.to_dict())
    return out
