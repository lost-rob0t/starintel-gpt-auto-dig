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
    *,
    supersedes: tuple[str, ...] = (),
    version: int = 1,
) -> LocatedDocument:
    return LocatedDocument(
        {
            "_id": document_id,
            "dtype": "investigation-target",
            "dataset": "test",
            "date_updated": date_updated,
            "version": version,
            "data": {
                "target_id": target_id,
                "status": status,
            },
            "lineage": {
                "supersedes": list(supersedes),
            },
            "workflow": {
                "research_status": status,
            },
        },
        Path(document_id),
    )


class FreeRangeStateTests(unittest.TestCase):
    def test_explicit_completion_supersedes_prior_queue_document(self) -> None:
        queued_id = "starintel:investigation-target:example"
        documents = [
            target_state(
                queued_id,
                "starintel:person:subject",
                "queued",
                "2026-07-27T00:00:00Z",
            ),
            target_state(
                "starintel:investigation-target:example-completed",
                "starintel:person:subject",
                "completed",
                "2026-08-08T00:00:00Z",
                supersedes=(queued_id,),
            ),
        ]

        resolved = resolve_latest_target_states(documents)

        self.assertEqual(
            [item.document["_id"] for item in resolved],
            ["starintel:investigation-target:example-completed"],
        )

    def test_same_subject_does_not_collapse_unrelated_targets(self) -> None:
        documents = [
            target_state(
                "starintel:investigation-target:ethics",
                "starintel:person:subject",
                "queued",
                "2026-07-27T00:00:00Z",
            ),
            target_state(
                "starintel:investigation-target:employment",
                "starintel:person:subject",
                "queued",
                "2026-08-08T00:00:00Z",
            ),
        ]

        resolved = resolve_latest_target_states(documents)

        self.assertEqual(
            {item.document["_id"] for item in resolved},
            {
                "starintel:investigation-target:ethics",
                "starintel:investigation-target:employment",
            },
        )

    def test_later_queue_state_reopens_blocked_state(self) -> None:
        original_id = "starintel:investigation-target:example"
        blocked_id = "starintel:investigation-target:example-blocked"
        reopened_id = "starintel:investigation-target:example-reopened"
        documents = [
            target_state(
                original_id,
                "starintel:person:subject",
                "queued",
                "2026-07-27T00:00:00Z",
            ),
            target_state(
                blocked_id,
                "starintel:person:subject",
                "blocked",
                "2026-08-08T00:00:00Z",
                supersedes=(original_id,),
            ),
            target_state(
                reopened_id,
                "starintel:person:subject",
                "queued",
                "2026-08-09T00:00:00Z",
                supersedes=(blocked_id,),
            ),
        ]

        resolved = resolve_latest_target_states(documents)

        self.assertEqual(
            [item.document["_id"] for item in resolved],
            [reopened_id],
        )

    def test_duplicate_document_id_keeps_latest_state(self) -> None:
        document_id = "starintel:investigation-target:example"
        documents = [
            target_state(
                document_id,
                "starintel:person:subject",
                "queued",
                "2026-07-27T00:00:00Z",
                version=1,
            ),
            target_state(
                document_id,
                "starintel:person:subject",
                "completed",
                "2026-08-08T00:00:00Z",
                version=2,
            ),
        ]

        resolved = resolve_latest_target_states(documents)

        self.assertEqual(len(resolved), 1)
        self.assertEqual(resolved[0].document["data"]["status"], "completed")

    def test_non_target_documents_are_preserved(self) -> None:
        source = LocatedDocument(
            {"_id": "starintel:source:x", "dtype": "source", "dataset": "test"},
            Path("source"),
        )

        resolved = resolve_latest_target_states([source])

        self.assertEqual(resolved, [source])


if __name__ == "__main__":
    unittest.main()
