from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COUNTEREVIDENCE_PACKET = (
    ROOT
    / "digs"
    / "dnc"
    / "2026-08-01-key-people-accountability-counterevidence"
    / "starintel-documents.jsonl"
)
CANONICAL_ENTITY_DTYPES = frozenset({"person", "org"})


def read_documents(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


class CounterevidencePacketIdentityTests(unittest.TestCase):
    def test_counterevidence_does_not_shadow_canonical_entities(self) -> None:
        counterevidence_ids = {
            document["_id"]
            for document in read_documents(COUNTEREVIDENCE_PACKET)
            if document.get("dtype") in CANONICAL_ENTITY_DTYPES
        }

        canonical_ids: set[str] = set()
        for path in (ROOT / "digs").rglob("starintel-documents.jsonl"):
            if path == COUNTEREVIDENCE_PACKET:
                continue
            for document in read_documents(path):
                if document.get("dtype") in CANONICAL_ENTITY_DTYPES:
                    canonical_ids.add(document["_id"])

        shadowed_ids = sorted(counterevidence_ids & canonical_ids)
        self.assertEqual(
            shadowed_ids,
            [],
            "counterevidence packets must reference existing canonical entities by _id "
            "instead of re-declaring packet-local copies",
        )


if __name__ == "__main__":
    unittest.main()
