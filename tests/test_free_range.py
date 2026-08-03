from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from starintel_doc.free_range import (
    ACTOR_ROLES,
    load_frontier_documents,
    plan_free_range,
    render_markdown,
)
from starintel_doc.store import LocatedDocument


def located(document: dict) -> LocatedDocument:
    return LocatedDocument(document, Path(document["_id"]))


def target(
    document_id: str,
    target_id: str,
    dataset: str,
    score: float,
    *,
    status: str = "queued",
    blockers: list[str] | None = None,
    target_type: str = "org",
) -> LocatedDocument:
    return located(
        {
            "_id": document_id,
            "dtype": "investigation-target",
            "dataset": dataset,
            "title": target_id,
            "workflow": {
                "research_status": status,
                "selection_score": score,
                "blockers": blockers or [],
            },
            "data": {
                "target_id": target_id,
                "target_type": target_type,
                "score": score,
                "seed_ids": [],
            },
        }
    )


class FreeRangeTests(unittest.TestCase):
    def test_balances_datasets_and_excludes_completed(self) -> None:
        documents = [
            target("q:a1", "starintel:org:a1", "alpha", 9),
            target("q:a2", "starintel:org:a2", "alpha", 8),
            target("q:b1", "starintel:org:b1", "beta", 7),
            target(
                "q:c1",
                "starintel:org:c1",
                "gamma",
                100,
                status="completed",
            ),
        ]
        missions = plan_free_range(
            documents,
            limit=3,
            max_per_dataset=1,
            discover=False,
        )
        self.assertEqual(
            [mission.target.target_id for mission in missions],
            ["starintel:org:a1", "starintel:org:b1"],
        )

    def test_blocked_targets_are_opt_in(self) -> None:
        documents = [
            target(
                "q:a",
                "starintel:org:a",
                "alpha",
                9,
                status="blocked",
                blockers=["records request pending"],
            )
        ]
        self.assertEqual(plan_free_range(documents, discover=False), [])
        missions = plan_free_range(
            documents,
            include_blocked=True,
            discover=False,
        )
        self.assertEqual(missions[0].target.state, "blocked")

    def test_discovery_assigns_actor_swarm(self) -> None:
        documents = [
            located(
                {
                    "_id": "starintel:org:x",
                    "dtype": "org",
                    "dataset": "x",
                    "title": "X",
                    "assessment": {"relevance": 0.9},
                }
            )
        ]
        missions = plan_free_range(documents, limit=1)
        self.assertEqual(
            tuple(actor["role"] for actor in missions[0].actors),
            ACTOR_ROLES,
        )
        self.assertEqual(missions[0].target.state, "discovered")

    def test_type_cap_prevents_one_surface_from_consuming_frontier(self) -> None:
        documents = [
            target("q:o1", "starintel:org:o1", "alpha", 9, target_type="org"),
            target("q:o2", "starintel:org:o2", "beta", 8, target_type="org"),
            target(
                "q:c1",
                "starintel:contract:c1",
                "gamma",
                7,
                target_type="contract",
            ),
        ]
        missions = plan_free_range(
            documents,
            limit=3,
            max_per_dataset=0,
            max_per_type=1,
            discover=False,
        )
        self.assertEqual(
            [mission.target.target_type for mission in missions],
            ["org", "contract"],
        )

    def test_broken_packet_is_skipped_without_hiding_db(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            db_path = root / "db" / "org" / "starintel:org:x.ndjson"
            db_path.parent.mkdir(parents=True)
            db_path.write_text(
                '{"_id":"starintel:org:x","dtype":"org","dataset":"x"}\n',
                encoding="utf-8",
            )
            packet = (
                root
                / "digs"
                / "broken"
                / "2026-08-03-run"
                / "starintel-documents.jsonl.gz.b64"
            )
            packet.parent.mkdir(parents=True)
            packet.write_text("not-base64", encoding="utf-8")

            documents, warnings = load_frontier_documents(root)
            self.assertEqual(len(documents), 1)
            self.assertEqual(documents[0].document["_id"], "starintel:org:x")
            self.assertEqual(len(warnings), 1)
            self.assertIn("skipped unreadable packet", warnings[0])

    def test_markdown_is_deterministic(self) -> None:
        documents = [target("q:a", "starintel:org:a", "alpha", 9)]
        first = render_markdown(plan_free_range(documents, discover=False))
        second = render_markdown(plan_free_range(documents, discover=False))
        self.assertEqual(first, second)
        self.assertIn("## Batch 1", first)
        self.assertIn("**skeptic**", first)


if __name__ == "__main__":
    unittest.main()
