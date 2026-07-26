from __future__ import annotations

import json
from pathlib import Path

from starintel_doc.spec import document_schema

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "starintel_doc" / "spec.py"
SCHEMA = ROOT / "schemas" / "starintel-doc-v0.9.0.schema.json"

text = SPEC.read_text(encoding="utf-8")
old = '    "research-pass": RESEARCH_PASS_FIELDS,\n    "research-node": RESEARCH_NODE_FIELDS,\n'
new = '    "research-node": RESEARCH_NODE_FIELDS,\n    "research-pass": RESEARCH_PASS_FIELDS,\n'
if old in text:
    SPEC.write_text(text.replace(old, new, 1), encoding="utf-8")
elif new not in text:
    raise SystemExit("research-node registry anchor missing")

SCHEMA.write_text(
    json.dumps(document_schema(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
