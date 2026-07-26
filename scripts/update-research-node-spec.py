from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "starintel_doc" / "spec.py"
FIXTURES = ROOT / "conformance" / "fixtures.py"
DOCS = ROOT / "docs" / "starintel-doc-v0.9.0.md"
SCHEMA = ROOT / "schemas" / "starintel-doc-v0.9.0.schema.json"

RESEARCH_SCHEMA = '''
RESEARCH_NODE_LIMITS = obj(
    {
        "max_depth": integer(minimum=1),
        "max_actor_runs": integer(minimum=1),
        "max_requests": integer(minimum=1),
        "max_elapsed_ms": integer(minimum=1),
        "max_repeated_state": integer(minimum=1),
        "max_cost": number(minimum=0.0),
        "currency": STR,
    }
)

RESEARCH_NODE_STOP = obj(
    {
        "when_actor_queue_empty": BOOL,
        "when_no_new_documents": BOOL,
        "when_objective_satisfied": BOOL,
        "halt_on_actor_failure": BOOL,
    }
)

RESEARCH_NODE_COUNTERS = obj(
    {
        "depth": integer(minimum=0),
        "actor_runs": integer(minimum=0),
        "requests": integer(minimum=0),
        "repeated_state": integer(minimum=0),
        "elapsed_ms": integer(minimum=0),
        "cost": number(minimum=0.0),
    }
)

RESEARCH_NODE_HISTORY_ENTRY = obj(
    {
        "from": NULLABLE_STRING,
        "to": STR,
        "at": DATE_TIME,
        "message": STR,
        "error": STR,
        "actor_id": STR,
        "run_id": STR,
        "output_ids": STRS,
        "artifact_ids": STRS,
    },
    required=("to", "at"),
)

RESEARCH_NODE_FIELDS = {
    "objective": STR,
    "instructions": STR,
    "status": string(
        enum=[
            "draft",
            "queued",
            "running",
            "paused",
            "blocked",
            "completed",
            "failed",
            "killed",
        ]
    ),
    "input_ids": STRS,
    "target_ids": STRS,
    "actor_ids": STRS,
    "actor_selection_rules": array(JSON_MAP),
    "output_ids": STRS,
    "artifact_ids": STRS,
    "child_ids": STRS,
    "dependency_ids": STRS,
    "run_ids": STRS,
    "current_actor_id": STR,
    "current_run_id": STR,
    "limits": RESEARCH_NODE_LIMITS,
    "stop": RESEARCH_NODE_STOP,
    "counters": RESEARCH_NODE_COUNTERS,
    "history": array(RESEARCH_NODE_HISTORY_ENTRY),
    "created_at": NULLABLE_DATE_TIME,
    "started_at": NULLABLE_DATE_TIME,
    "completed_at": NULLABLE_DATE_TIME,
    "last_error": STR,
    "paused_reason": STR,
}

'''

FULL_FIXTURE = '''
    values.append(
        fixture(
            "research-node.full.v1",
            "research-node",
            base_document(
                "research-node",
                108,
                {
                    "objective": "Map an organization and the people responsible for a program.",
                    "instructions": "Prefer primary records and preserve provenance.",
                    "status": "running",
                    "input_ids": ["starintel:target:program"],
                    "target_ids": ["starintel:target:program"],
                    "actor_ids": ["quasar.actor.web-search", "quasar.actor.url-content"],
                    "actor_selection_rules": [{"accepts": ["target"], "priority": 10}],
                    "output_ids": ["starintel:org:example"],
                    "artifact_ids": ["artifact:report"],
                    "child_ids": ["starintel:research-node:child"],
                    "dependency_ids": [],
                    "run_ids": ["run:research:001"],
                    "current_actor_id": "quasar.actor.url-content",
                    "current_run_id": "run:research:001",
                    "limits": {
                        "max_depth": 4,
                        "max_actor_runs": 64,
                        "max_requests": 1024,
                        "max_elapsed_ms": 1800000,
                        "max_repeated_state": 3,
                        "max_cost": 10.0,
                        "currency": "USD",
                    },
                    "stop": {
                        "when_actor_queue_empty": True,
                        "when_no_new_documents": True,
                        "when_objective_satisfied": False,
                        "halt_on_actor_failure": True,
                    },
                    "counters": {
                        "depth": 1,
                        "actor_runs": 2,
                        "requests": 8,
                        "repeated_state": 0,
                        "elapsed_ms": 1200,
                        "cost": 0.25,
                    },
                    "history": [
                        {
                            "from": None,
                            "to": "draft",
                            "at": FIXED_UTC,
                            "message": "Research node created",
                            "error": "",
                            "actor_id": "",
                            "run_id": "",
                            "output_ids": [],
                            "artifact_ids": [],
                        },
                        {
                            "from": "queued",
                            "to": "running",
                            "at": "2026-01-02T03:05:05Z",
                            "message": "Actor queue started",
                            "error": "",
                            "actor_id": "quasar.actor.web-search",
                            "run_id": "run:research:001",
                            "output_ids": ["starintel:org:example"],
                            "artifact_ids": ["artifact:report"],
                        },
                    ],
                    "created_at": FIXED_UTC,
                    "started_at": "2026-01-02T03:05:05Z",
                    "completed_at": None,
                    "last_error": "",
                    "paused_reason": "",
                },
            ),
        )
    )
'''


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise RuntimeError(f"missing {label} anchor")
    if text.count(old) != 1:
        raise RuntimeError(f"ambiguous {label} anchor")
    return text.replace(old, new, 1)


def update_spec() -> None:
    text = SPEC.read_text(encoding="utf-8")
    if "RESEARCH_NODE_FIELDS = {" not in text:
        text = replace_once(text, "\nMANIFEST_FIELDS = {", f"\n{RESEARCH_SCHEMA}MANIFEST_FIELDS = {{", "research schema")
    if '    "research-node": RESEARCH_NODE_FIELDS,\n' not in text:
        text = replace_once(
            text,
            '    "research-pass": RESEARCH_PASS_FIELDS,\n',
            '    "research-pass": RESEARCH_PASS_FIELDS,\n    "research-node": RESEARCH_NODE_FIELDS,\n',
            "dtype registry",
        )
    if '    "research-node": ("objective", "status"),\n' not in text:
        text = replace_once(
            text,
            'REQUIRED_DATA_FIELDS: dict[str, tuple[str, ...]] = {\n',
            'REQUIRED_DATA_FIELDS: dict[str, tuple[str, ...]] = {\n    "research-node": ("objective", "status"),\n',
            "required fields",
        )
    if '    "research_node": "research-node",\n' not in text:
        text = replace_once(
            text,
            '    "research_pass": "research-pass",\n',
            '    "research_pass": "research-pass",\n    "research_node": "research-node",\n',
            "dtype alias",
        )
    SPEC.write_text(text, encoding="utf-8")


def update_fixtures() -> None:
    text = FIXTURES.read_text(encoding="utf-8")
    if '        "research-node": {' not in text:
        text = replace_once(
            text,
            '        "claim": {"claim": "A documented claim."},\n',
            '        "claim": {"claim": "A documented claim."},\n'
            '        "research-node": {\n'
            '            "objective": "Run a bounded investigation.",\n'
            '            "status": "draft",\n'
            '        },\n',
            "minimal research node fixture",
        )
    if '"research-node.full.v1"' not in text:
        text = replace_once(
            text,
            '    duplicate_a = base_document("person", 106, {"fname": "Alex", "lname": "Smith"})\n',
            FULL_FIXTURE + '\n    duplicate_a = base_document("person", 106, {"fname": "Alex", "lname": "Smith"})\n',
            "full research node fixture",
        )
    FIXTURES.write_text(text, encoding="utf-8")


def update_docs() -> None:
    text = DOCS.read_text(encoding="utf-8")
    text = text.replace(
        '`analysis`, `concept`, `research-pass`.',
        '`analysis`, `concept`, `research-pass`, `research-node`.',
    )
    section = '''
## Research nodes

`research-node` is the executable investigation-plan object type. It records an objective, instructions, corpus inputs and targets, an ordered actor queue or actor-selection rules, bounded execution limits, stop conditions, counters, lifecycle history, outputs, artifacts, child nodes, dependencies, and run identifiers.

Research nodes remain ordinary StarIntel documents. Runtime-specific details may be namespaced in `extensions`, but portable execution state belongs in the declared `data` fields and validates identically in Python, JavaScript, Common Lisp, and Nim.

'''
    if "## Research nodes" not in text:
        text = replace_once(text, "## Relations\n", section + "## Relations\n", "research node docs")
    DOCS.write_text(text, encoding="utf-8")


def regenerate_schema() -> None:
    command = (
        "import json; "
        "from pathlib import Path; "
        "from starintel_doc.spec import document_schema; "
        f"Path({str(SCHEMA)!r}).write_text(json.dumps(document_schema(), ensure_ascii=False, indent=2, sort_keys=True) + '\\n', encoding='utf-8')"
    )
    subprocess.run([sys.executable, "-c", command], cwd=ROOT, check=True)


def main() -> None:
    update_spec()
    update_fixtures()
    update_docs()
    regenerate_schema()


if __name__ == "__main__":
    main()
