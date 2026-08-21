from __future__ import annotations

import hashlib
import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from .selectors import select_candidates
from .store import LocatedDocument, iter_db, iter_jsonl, packet_paths


ACTOR_ROLES = ("scout", "archivist", "verifier", "linker", "skeptic")
TERMINAL_STATUSES = {
    "cancelled",
    "closed",
    "complete",
    "completed",
    "done",
    "rejected",
    "superseded",
}
BLOCKED_STATUSES = {
    "blocked",
    "waiting",
    "records_pending",
    "awaiting_records",
    "pending_external",
}


@dataclass(frozen=True, slots=True)
class FrontierTarget:
    target_id: str
    target_type: str
    dataset: str
    title: str
    score: float
    state: str
    reasons: tuple[str, ...]
    seed_ids: tuple[str, ...]
    blockers: tuple[str, ...]
    queue_document_id: str = ""


@dataclass(frozen=True, slots=True)
class Mission:
    mission_id: str
    batch: int
    lane: int
    target: FrontierTarget
    actors: tuple[dict[str, str], ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "mission_id": self.mission_id,
            "batch": self.batch,
            "lane": self.lane,
            "target_id": self.target.target_id,
            "target_type": self.target.target_type,
            "dataset": self.target.dataset,
            "title": self.target.title,
            "score": self.target.score,
            "state": self.target.state,
            "reasons": list(self.target.reasons),
            "seed_ids": list(self.target.seed_ids),
            "blockers": list(self.target.blockers),
            "queue_document_id": self.target.queue_document_id,
            "actors": list(self.actors),
            "evidence_rules": [
                "Prefer primary sources and preserve exact provenance, dates, hashes, and source versions.",
                "Keep facts, attributed claims, inference, counterevidence, and unresolved gaps separate.",
                "Do not promote proximity, capability, employment, or allegation into control or culpability without a direct evidence edge.",
                "Reuse canonical StarIntel identities and exact predicates; do not create parallel schemas or duplicate entities.",
            ],
        }


def _strings(value: Any) -> tuple[str, ...]:
    if isinstance(value, str):
        return (value,) if value.strip() else ()
    if isinstance(value, (list, tuple)):
        return tuple(str(item) for item in value if str(item).strip())
    return ()


def _number(*values: Any, default: float = 0.0) -> float:
    for value in values:
        if isinstance(value, bool):
            continue
        if isinstance(value, (int, float)):
            return float(value)
    return default


def _target_id(data: dict[str, Any], fallback: str) -> str:
    value = data.get("target_id", data.get("target", fallback))
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        for key in ("id", "document_id", "entity_id"):
            item = value.get(key)
            if isinstance(item, str) and item:
                return item
    return fallback


def _target_type(data: dict[str, Any], target_id: str) -> str:
    value = data.get("target_type")
    if isinstance(value, str) and value:
        return value
    parts = target_id.split(":", 2)
    return parts[1] if len(parts) > 1 and parts[1] else "document"


def _status(document: dict[str, Any]) -> str:
    workflow = document.get("workflow", {})
    data = document.get("data", {})
    for value in (
        workflow.get("research_status"),
        data.get("status"),
        document.get("status"),
    ):
        if isinstance(value, str) and value.strip():
            return value.strip().lower().replace("-", "_").replace(" ", "_")
    return "queued"


def _queued_targets(
    documents: list[LocatedDocument],
    *,
    include_blocked: bool,
) -> list[FrontierTarget]:
    targets: list[FrontierTarget] = []
    for located in documents:
        document = located.document
        if document.get("dtype") not in {"target", "investigation-target"}:
            continue

        status = _status(document)
        if status in TERMINAL_STATUSES:
            continue

        workflow = document.get("workflow", {})
        data = document.get("data", {})
        blockers = _strings(workflow.get("blockers"))
        blocked = status in BLOCKED_STATUSES or bool(blockers)
        if blocked and not include_blocked:
            continue

        document_id = str(document.get("_id", ""))
        target_id = _target_id(data, document_id)
        target_type = _target_type(data, target_id)
        dataset = str(document.get("dataset", "unknown")) or "unknown"
        assessment = document.get("assessment", {})
        base_score = _number(
            workflow.get("selection_score"),
            data.get("score"),
            workflow.get("priority"),
            data.get("priority"),
            default=1.0,
        )
        if base_score <= 1.0:
            base_score += _number(assessment.get("priority")) * 2.0
            base_score += _number(assessment.get("relevance")) * 1.5

        gaps = _strings(assessment.get("gaps"))
        unresolved = _strings(document.get("verification", {}).get("unresolved"))
        seed_ids = _strings(data.get("seed_ids")) or _strings(workflow.get("selected_from"))
        open_count = len(gaps) + len(unresolved)
        depth = int(_number(data.get("depth"), workflow.get("recursion_depth")))
        gap_bonus = min(1.5, open_count * 0.25)
        seed_bonus = min(0.75, len(seed_ids) * 0.1)
        depth_penalty = min(1.0, depth * 0.1)
        blocked_penalty = 2.0 if blocked else 0.0
        score = round(
            base_score + gap_bonus + seed_bonus - depth_penalty - blocked_penalty,
            4,
        )

        reasons = [f"queued target status={status}", f"base priority={base_score:.2f}"]
        if open_count:
            reasons.append(f"{open_count} unresolved items (+{gap_bonus:.2f})")
        if seed_ids:
            reasons.append(f"{len(seed_ids)} seed records (+{seed_bonus:.2f})")
        if depth:
            reasons.append(f"recursion depth {depth} (-{depth_penalty:.2f})")
        if blocked:
            reasons.append(f"blocked ({len(blockers)} blockers, -{blocked_penalty:.2f})")

        targets.append(
            FrontierTarget(
                target_id=target_id,
                target_type=target_type,
                dataset=dataset,
                title=str(document.get("title", "")) or f"Research {target_id}",
                score=score,
                state="blocked" if blocked else "ready",
                reasons=tuple(reasons),
                seed_ids=seed_ids,
                blockers=blockers,
                queue_document_id=document_id,
            )
        )
    return targets


def _discovered_targets(
    documents: list[LocatedDocument],
    *,
    limit: int,
) -> list[FrontierTarget]:
    by_id = {
        str(located.document.get("_id")): located.document
        for located in documents
        if located.document.get("_id")
    }
    discovered: list[FrontierTarget] = []
    for candidate in select_candidates(documents, limit=limit):
        document = by_id.get(candidate.target_id, {})
        discovered.append(
            FrontierTarget(
                target_id=candidate.target_id,
                target_type=candidate.target_type,
                dataset=str(document.get("dataset", "unknown")) or "unknown",
                title=str(document.get("title", "")) or f"Research {candidate.target_id}",
                score=candidate.score,
                state="discovered",
                reasons=candidate.reasons,
                seed_ids=candidate.seed_ids,
                blockers=(),
            )
        )
    return discovered


def _deduplicate(targets: Iterable[FrontierTarget]) -> list[FrontierTarget]:
    state_rank = {"ready": 2, "discovered": 1, "blocked": 0}
    best: dict[str, FrontierTarget] = {}
    for target in targets:
        current = best.get(target.target_id)
        if current is None or (state_rank[target.state], target.score) > (
            state_rank[current.state],
            current.score,
        ):
            best[target.target_id] = target
    return sorted(
        best.values(),
        key=lambda item: (-item.score, item.dataset, item.target_type, item.target_id),
    )


def _balanced(
    targets: Iterable[FrontierTarget],
    *,
    limit: int,
    max_per_dataset: int,
    max_per_type: int,
) -> list[FrontierTarget]:
    selected: list[FrontierTarget] = []
    dataset_counts: Counter[str] = Counter()
    type_counts: Counter[str] = Counter()
    remaining = list(targets)

    while remaining and len(selected) < limit:
        progressed = False
        for index, target in enumerate(remaining):
            if max_per_dataset > 0 and dataset_counts[target.dataset] >= max_per_dataset:
                continue
            if max_per_type > 0 and type_counts[target.target_type] >= max_per_type:
                continue
            selected.append(target)
            dataset_counts[target.dataset] += 1
            type_counts[target.target_type] += 1
            remaining.pop(index)
            progressed = True
            break
        if not progressed:
            break
    return selected


def _actor_objectives(target: FrontierTarget) -> tuple[dict[str, str], ...]:
    if target.target_type in {
        "contract",
        "procurement",
        "campaign-finance",
        "financial-observation",
        "lobbying-filing",
    }:
        scout_focus = (
            "Locate primary filings, award records, amendments, transaction rows, "
            "named decisionmakers, and exact legal entities."
        )
    elif target.target_type in {"person", "org"}:
        scout_focus = (
            "Enumerate official roles, dates, identifiers, organizations, filings, "
            "and directly evidenced relationship surfaces."
        )
    elif target.target_type in {"claim", "analysis", "policy"}:
        scout_focus = (
            "Recover the original statement or instrument, its context, strongest "
            "supporting evidence, and strongest counterevidence."
        )
    elif target.target_type in {"product", "system", "protocol", "software"}:
        scout_focus = (
            "Recover architecture, operators, contracts, data flows, versions, "
            "permissions, and documented operational use."
        )
    else:
        scout_focus = (
            "Locate the next highest-value primary-source surface and enumerate "
            "concrete people, organizations, records, identifiers, and dates."
        )

    return (
        {"role": "scout", "objective": scout_focus},
        {
            "role": "archivist",
            "objective": (
                "Capture source URLs, retrieval times, hashes, versions, archive "
                "locations, and document lineage before interpretation."
            ),
        },
        {
            "role": "verifier",
            "objective": (
                "Corroborate the strongest material assertion with an independent "
                "primary source and preserve conflicts, uncertainty, and negative-search scope."
            ),
        },
        {
            "role": "linker",
            "objective": (
                "Resolve canonical IDs, aliases, dates, and exact predicates; reuse "
                "existing records and create only evidence-supported edges."
            ),
        },
        {
            "role": "skeptic",
            "objective": (
                "Try to falsify the leading hypothesis and downgrade any proximity, "
                "capability, employment, or allegation lacking a direct evidence edge."
            ),
        },
    )


def load_frontier_documents(
    root: Path,
    *,
    include_db: bool = True,
    include_packets: bool = True,
    strict_packets: bool = False,
) -> tuple[list[LocatedDocument], tuple[str, ...]]:
    documents: list[LocatedDocument] = []
    warnings: list[str] = []
    if include_db:
        documents.extend(iter_db(root))
    if include_packets:
        for path in packet_paths(root):
            try:
                documents.extend(iter_jsonl(path, surface="packet"))
            except Exception as exc:
                message = f"{path}: skipped unreadable packet: {exc}"
                if strict_packets:
                    raise ValueError(message) from exc
                warnings.append(message)
    return documents, tuple(warnings)


def plan_free_range(
    documents: Iterable[LocatedDocument],
    *,
    limit: int = 20,
    batch_size: int = 5,
    max_per_dataset: int = 3,
    max_per_type: int = 5,
    include_blocked: bool = False,
    discover: bool = True,
) -> list[Mission]:
    if limit < 1:
        return []
    if batch_size < 1:
        raise ValueError("batch_size must be at least 1")

    located = list(documents)
    queued = _queued_targets(located, include_blocked=include_blocked)
    discovered = (
        _discovered_targets(located, limit=max(limit * 4, 20))
        if discover
        else []
    )
    frontier = _deduplicate([*queued, *discovered])
    selected = _balanced(
        frontier,
        limit=limit,
        max_per_dataset=max_per_dataset,
        max_per_type=max_per_type,
    )

    missions: list[Mission] = []
    for index, target in enumerate(selected):
        digest = hashlib.sha256(target.target_id.encode("utf-8")).hexdigest()[:12]
        missions.append(
            Mission(
                mission_id=f"free-range-{digest}",
                batch=(index // batch_size) + 1,
                lane=(index % batch_size) + 1,
                target=target,
                actors=_actor_objectives(target),
            )
        )
    return missions


def render_jsonl(missions: Iterable[Mission]) -> str:
    return "".join(
        json.dumps(
            mission.to_dict(),
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        + "\n"
        for mission in missions
    )


def render_markdown(missions: Iterable[Mission]) -> str:
    values = list(missions)
    lines = [
        "# Free-Range Auto-Dig Frontier",
        "",
        f"Missions: **{len(values)}**",
        "",
        (
            "The planner balances datasets and target types, prefers actionable "
            "queued work, and assigns a five-actor evidence workflow to every mission."
        ),
        "",
    ]
    current_batch = 0
    for mission in values:
        if mission.batch != current_batch:
            current_batch = mission.batch
            lines.extend([f"## Batch {current_batch}", ""])

        target = mission.target
        lines.extend(
            [
                f"### {mission.lane}. {target.title}",
                "",
                f"- Mission: `{mission.mission_id}`",
                f"- Target: `{target.target_id}` (`{target.target_type}`)",
                f"- Dataset: `{target.dataset}`",
                f"- State: `{target.state}`",
                f"- Score: `{target.score:.4f}`",
            ]
        )
        if target.blockers:
            lines.append(f"- Blockers: {'; '.join(target.blockers)}")

        lines.extend(["", "Actors:"])
        for actor in mission.actors:
            lines.append(f"- **{actor['role']}** — {actor['objective']}")

        lines.extend(["", "Selection reasons:"])
        for reason in target.reasons:
            lines.append(f"- {reason}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"
