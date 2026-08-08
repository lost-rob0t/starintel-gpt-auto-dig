from __future__ import annotations

import unittest
from pathlib import Path

from starintel_doc.frontier_state import resolve_latest_target_states
from starintel_doc.store import LocatedDocument


def target_state(
    document_id: str,
    target_id: str,
    status: str,
    date_updated: str,
) -> LocatedDocument:
    return LocatedDocument(
        {
            "_id": document_id,
            "dtype": "investigation-target",
            "dataset": "test",
            "date_updated": date_updated,
            "version": 1,
            "data": {
                "target_id": target_id,
                "status": status,
            },
            "workflow": {
                "research_status": status,
            },
        },
        Path(document_id),
    )


class FreeRangeStateTests(unittest.TestCase):
    def test_newer_completed_state_replaces_older_queued_state(self) -> None:
        target_id = "starintel:investigation-target:example"
        documents = [
            target_state(
                "starintel:investigation-target:example-queued",
                target_id,
                "queued",
                "2026-07-27T00:00:00Z",
            ),
            target_state(
                "starintel:investigation-target:example-completed",
                target_id,
                "completed",
                "2026-08-08T00:00:00Z",
            ),
        ]

        resolved = resolve_latest_target_states(documents)

        self.assertEqual(len(resolved), 1)
        self.assertEqual(
            resolved[0].document["_id"],
            "starintel:investigation-target:example-completed",
        )

    def test_newer_queued_state_can_reopen_older_completed_state(self) -> None:
        target_id = "starintel:investigation-target:example"
        documents = [
            target_state(
                "starintel:investigation-target:example-completed",
                target_id,
                "completed",
                "2026-07-27T00:00:00Z",
            ),
            target_state(
                "starintel:investigation-target:example-reopened",
                target_id,
                "queued",
                "2026-08-08T00:00:00Z",
            ),
        ]

        resolved = resolve_latest_target_states(documents)

        self.assertEqual(len(resolved), 1)
        self.assertEqual(
            resolved[0].document["_id"],
            "starintel:investigation-target:example-reopened",
        )

    def test_non_target_documents_are_preserved(self) -> None:
        source = LocatedDocument(
            {"_id": "starintel:source:x", "dtype": "source", "dataset": "test"},
            Path("source"),
        )

        resolved = resolve_latest_target_states([source])

        self.assertEqual(resolved, [source])


if __name__ == "__main__":
    unittest.main()
