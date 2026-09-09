from __future__ import annotations

from typing import Any

from .spec import (
    BOOL,
    JSON_MAP,
    STR,
    STRS,
    COMMON_PROPERTIES,
    REQUIRED_DATA_FIELDS,
    TYPE_FIELDS,
    array,
    obj,
    string,
)

# Transitional v0.9 structural contract for starintel-server#151.
#
# Operation is control-plane/executable-knowledge state, not a real-world
# intelligence entity.  The canonical semantic model is intentionally due for
# re-examination under the JSON-LD ontology system; do not treat these Python
# names as the permanent ontology authority.

OPERATION_STATES = (
    "draft",
    "planned",
    "active",
    "blocked",
    "suspended",
    "completed",
    "aborted",
    "archived",
)

PHASE_STATES = (
    "planned",
    "ready",
    "active",
    "blocked",
    "awaiting-review",
    "completed",
    "skipped",
    "failed",
    "aborted",
)

DATASET_ROLES = (
    "collection",
    "working",
    "derived",
    "publication",
    "reference",
    "archive",
)

DATASET_ACCESS = (
    "read",
    "append",
    "write",
    "read-write",
)

CAPABILITY_CATEGORIES = (
    "actor",
    "software",
    "hardware",
    "device",
    "source",
    "dataset",
    "schema",
    "protocol",
    "infrastructure",
    "research",
)

CAPABILITY_STATES = (
    "required",
    "missing",
    "planned",
    "in-progress",
    "available",
    "resolved",
    "waived",
)

ASSIGNMENT_STATES = (
    "planned",
    "assigned",
    "active",
    "completed",
    "blocked",
    "released",
)

POST_ACTION_STATES = (
    "planned",
    "ready",
    "running",
    "completed",
    "failed",
    "skipped",
)

CONDITION = obj(
    {
        "condition_id": STR,
        "kind": STR,
        "predicate": STR,
        "subject": STR,
        "object": STR,
        "expression": STR,
        "required": BOOL,
        "metadata": JSON_MAP,
    },
    required=("kind",),
)

TARGET_POLICY = obj(
    {
        "allowed_dtypes": STRS,
        "allowed_target_types": STRS,
        "allowed_roles": STRS,
        "selectors": array(JSON_MAP),
    }
)

TARGET_BINDINGS = obj(
    {
        "primary": STRS,
        "supporting": STRS,
        "derived": STRS,
        "excluded": STRS,
    }
)

DATASET_BINDING = obj(
    {
        "binding_id": STR,
        "dataset": STR,
        "role": string(enum=list(DATASET_ROLES)),
        "access": string(enum=list(DATASET_ACCESS)),
        "phases": STRS,
        "purpose": STR,
    },
    required=("binding_id", "dataset", "role", "access"),
)

CAPABILITY_GAP = obj(
    {
        "capability_id": STR,
        "category": string(enum=list(CAPABILITY_CATEGORIES)),
        "description": STR,
        "required_by": STRS,
        "blocking": BOOL,
        "status": string(enum=list(CAPABILITY_STATES)),
        "capability_ref": STR,
        "resolution_ref": STR,
        "owner": STR,
        "metadata": JSON_MAP,
    },
    required=("capability_id", "category", "description", "blocking", "status"),
)

ASSIGNMENT = obj(
    {
        "assignment_id": STR,
        "agent_id": STR,
        "actor_id": STR,
        "phase_ids": STRS,
        "role": STR,
        "status": string(enum=list(ASSIGNMENT_STATES)),
        "metadata": JSON_MAP,
    },
    required=("assignment_id", "phase_ids", "status"),
)

POST_ACTION = obj(
    {
        "action_id": STR,
        "action_type": STR,
        "condition": CONDITION,
        "target_ids": STRS,
        "dataset_binding_ids": STRS,
        "status": string(enum=list(POST_ACTION_STATES)),
        "config": JSON_MAP,
    },
    required=("action_id", "action_type", "status"),
)

PHASE = obj(
    {
        "phase_id": STR,
        "title": STR,
        "objective": STR,
        "state": string(enum=list(PHASE_STATES)),
        "depends_on": STRS,
        "entry_conditions": array(CONDITION),
        "exit_conditions": array(CONDITION),
        "in_scope": STRS,
        "out_of_scope": STRS,
        "target_policy": TARGET_POLICY,
        "target_ids": STRS,
        "dataset_binding_ids": STRS,
        "required_capability_ids": STRS,
        "deliverable_ids": STRS,
        "completion_evidence": STRS,
    },
    required=("phase_id", "objective", "state"),
)

OPERATION_FIELDS: dict[str, dict[str, Any]] = {
    "mission": STR,
    "objectives": STRS,
    "status": string(enum=list(OPERATION_STATES)),
    "in_scope": STRS,
    "out_of_scope": STRS,
    "target_policy": TARGET_POLICY,
    "targets": TARGET_BINDINGS,
    "phases": array(PHASE),
    "datasets": array(DATASET_BINDING),
    "capability_gaps": array(CAPABILITY_GAP),
    "assignments": array(ASSIGNMENT),
    "post_actions": array(POST_ACTION),
}


def install_operation_spec() -> None:
    """Install the transitional operation dtype into the v0.9 schema tables."""

    TYPE_FIELDS["operation"] = OPERATION_FIELDS
    REQUIRED_DATA_FIELDS["operation"] = ("mission", "status", "phases")
    dtype_enum = COMMON_PROPERTIES["dtype"].setdefault("enum", [])
    if "operation" not in dtype_enum:
        dtype_enum.append("operation")
        dtype_enum.sort()


def _require_unique(items: list[dict[str, Any]], key: str, path: str) -> set[str]:
    values: set[str] = set()
    for index, item in enumerate(items):
        value = str(item.get(key) or "").strip()
        if not value:
            raise ValueError(f"{path}[{index}].{key}: non-empty identifier required")
        if value in values:
            raise ValueError(f"{path}[{index}].{key}: duplicate identifier {value!r}")
        values.add(value)
    return values


def _require_refs(refs: list[str], known: set[str], path: str) -> None:
    for ref in refs:
        if ref not in known:
            raise ValueError(f"{path}: unknown reference {ref!r}")


def _assert_phase_dag(phases: list[dict[str, Any]], phase_ids: set[str]) -> None:
    graph = {str(phase["phase_id"]).strip(): list(phase.get("depends_on") or []) for phase in phases}
    for phase_id, dependencies in graph.items():
        _require_refs(dependencies, phase_ids, f"$.data.phases[{phase_id}].depends_on")
        if phase_id in dependencies:
            raise ValueError(f"$.data.phases[{phase_id}].depends_on: self dependency")

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(phase_id: str) -> None:
        if phase_id in visiting:
            raise ValueError(f"$.data.phases: dependency cycle reaches {phase_id!r}")
        if phase_id in visited:
            return
        visiting.add(phase_id)
        for dependency in graph[phase_id]:
            visit(dependency)
        visiting.remove(phase_id)
        visited.add(phase_id)

    for phase_id in graph:
        visit(phase_id)


def validate_operation_semantics(document: dict[str, Any]) -> None:
    """Validate cross-reference/DAG invariants JSON Schema cannot express here."""

    if document.get("dtype") != "operation":
        return

    data = document.get("data")
    if not isinstance(data, dict):
        return

    mission = data.get("mission")
    if not isinstance(mission, str) or not mission.strip():
        raise ValueError("$.data.mission: non-empty mission required")

    phases = data.get("phases") or []
    if not phases:
        raise ValueError("$.data.phases: at least one phase required")

    datasets = data.get("datasets") or []
    capabilities = data.get("capability_gaps") or []
    assignments = data.get("assignments") or []
    post_actions = data.get("post_actions") or []

    phase_ids = _require_unique(phases, "phase_id", "$.data.phases")
    dataset_ids = _require_unique(datasets, "binding_id", "$.data.datasets")
    capability_ids = _require_unique(capabilities, "capability_id", "$.data.capability_gaps")
    _require_unique(assignments, "assignment_id", "$.data.assignments")
    _require_unique(post_actions, "action_id", "$.data.post_actions")

    _assert_phase_dag(phases, phase_ids)

    operation_excluded = set(data.get("out_of_scope") or [])
    for phase in phases:
        phase_id = str(phase["phase_id"]).strip()
        objective = phase.get("objective")
        if not isinstance(objective, str) or not objective.strip():
            raise ValueError(f"$.data.phases[{phase_id}].objective: non-empty objective required")
        _require_refs(
            list(phase.get("dataset_binding_ids") or []),
            dataset_ids,
            f"$.data.phases[{phase_id}].dataset_binding_ids",
        )
        _require_refs(
            list(phase.get("required_capability_ids") or []),
            capability_ids,
            f"$.data.phases[{phase_id}].required_capability_ids",
        )
        contradiction = operation_excluded.intersection(phase.get("in_scope") or [])
        if contradiction:
            raise ValueError(
                f"$.data.phases[{phase_id}].in_scope: operation out_of_scope overrides {sorted(contradiction)!r}"
            )
        if phase.get("state") == "completed" and not phase.get("completion_evidence"):
            raise ValueError(
                f"$.data.phases[{phase_id}].completion_evidence: completed phase requires evidence"
            )

    for binding in datasets:
        _require_refs(
            list(binding.get("phases") or []),
            phase_ids,
            f"$.data.datasets[{binding['binding_id']}].phases",
        )

    for capability in capabilities:
        _require_refs(
            list(capability.get("required_by") or []),
            phase_ids,
            f"$.data.capability_gaps[{capability['capability_id']}].required_by",
        )

    for assignment in assignments:
        _require_refs(
            list(assignment.get("phase_ids") or []),
            phase_ids,
            f"$.data.assignments[{assignment['assignment_id']}].phase_ids",
        )

    for action in post_actions:
        _require_refs(
            list(action.get("dataset_binding_ids") or []),
            dataset_ids,
            f"$.data.post_actions[{action['action_id']}].dataset_binding_ids",
        )

    if data.get("status") == "completed":
        nonterminal = [
            phase["phase_id"]
            for phase in phases
            if phase.get("state") not in {"completed", "skipped"}
        ]
        if nonterminal:
            raise ValueError(
                f"$.data.status: completed operation has nonterminal phases {nonterminal!r}"
            )