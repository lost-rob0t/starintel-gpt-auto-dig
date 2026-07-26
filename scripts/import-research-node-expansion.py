from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas"
EXPANSION_PATH = SCHEMAS / "starintel-doc-v0.9.0.expansion.json"
MANIFEST_PATH = SCHEMAS / "starintel-doc-v0.9.0.manifest.json"
SOURCE_REF = "origin/agent/starintel-v0.9-field-expansion"
REVISION = "0.9.0+fields.20260726.2"

RESEARCH_NODE_FIELDS = [
    "objective",
    "instructions",
    "status",
    "input_ids",
    "target_ids",
    "actor_ids",
    "actor_selection_rules",
    "output_ids",
    "artifact_ids",
    "child_ids",
    "dependency_ids",
    "run_ids",
    "current_actor_id",
    "current_run_id",
    "limits",
    "stop",
    "counters",
    "history",
    "created_at",
    "started_at",
    "completed_at",
    "last_error",
    "paused_reason",
]


def git_show(path: str) -> str:
    return subprocess.check_output(
        ["git", "show", f"{SOURCE_REF}:{path}"],
        cwd=ROOT,
        text=True,
    )


def canonicalize(value: Any) -> Any:
    if isinstance(value, list):
        return [canonicalize(item) for item in value]
    if isinstance(value, dict):
        return {key: canonicalize(value[key]) for key in sorted(value)}
    return value


def canonical_hash(value: Any) -> str:
    payload = json.dumps(
        canonicalize(value),
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def main() -> None:
    expansion = json.loads(
        git_show("schemas/starintel-doc-v0.9.0.expansion.json")
    )
    manifest = json.loads(
        git_show("schemas/starintel-doc-v0.9.0.manifest.json")
    )

    expansion["schema_revision"] = REVISION
    expansion.setdefault("dtype_fields", {})["research-node"] = RESEARCH_NODE_FIELDS
    expansion["dtype_fields"] = {
        key: expansion["dtype_fields"][key]
        for key in sorted(expansion["dtype_fields"])
    }

    manifest["schema_revision"] = REVISION
    manifest["expansion_content_hash"] = canonical_hash(expansion)
    manifest["dtype_count"] = len(expansion["dtype_fields"])

    EXPANSION_PATH.write_text(
        json.dumps(expansion, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    MANIFEST_PATH.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
