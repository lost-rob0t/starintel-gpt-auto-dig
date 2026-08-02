from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from build_research_site import coalesce_legacy_fec_employment_collisions


class LegacyFecCollisionTests(unittest.TestCase):
    def _document(self, *, row_count: int, first: str, last: str, title: str = "EXAMPLE CORP") -> dict:
        return {
            "_id": "starintel:employment:fec-reported-collision-test",
            "dataset": "dnc",
            "dtype": "employment",
            "data": {
                "person_id": "starintel:person:fec-contributor-example",
                "organization_id": "starintel:org:fec-reported-employer-example",
                "title": title,
                "employment_type": "reported_employment",
            },
            "sources": [{"source_id": "starintel:source:fec-example"}],
            "extensions": {
                "fec_reporting": {
                    "row_count": row_count,
                    "first_transaction_date": first,
                    "last_transaction_date": last,
                    "first_fec_sub_id": "1",
                }
            },
        }

    def test_coalesces_normalized_legacy_employment_title_variants(self) -> None:
        merged = coalesce_legacy_fec_employment_collisions(
            [
                self._document(
                    row_count=2,
                    first="2026-01-10T00:00:00Z",
                    last="2026-02-10T00:00:00Z",
                    title="Example Corp.",
                ),
                self._document(
                    row_count=3,
                    first="2026-01-01T00:00:00Z",
                    last="2026-03-10T00:00:00Z",
                    title="EXAMPLE CORP",
                ),
            ],
            Path("legacy.jsonl"),
        )

        self.assertEqual(len(merged), 1)
        reporting = merged[0]["extensions"]["fec_reporting"]
        self.assertEqual(reporting["row_count"], 5)
        self.assertEqual(reporting["first_transaction_date"], "2026-01-01T00:00:00Z")
        self.assertEqual(reporting["last_transaction_date"], "2026-03-10T00:00:00Z")
        self.assertEqual(reporting["legacy_collision_merged_documents"], 2)
        self.assertEqual(reporting["legacy_collision_raw_titles"], ["EXAMPLE CORP", "Example Corp."])

    def test_rejects_non_equivalent_legacy_collision(self) -> None:
        with self.assertRaisesRegex(ValueError, "non-equivalent legacy FEC collision"):
            coalesce_legacy_fec_employment_collisions(
                [
                    self._document(row_count=1, first="2026-01-01T00:00:00Z", last="2026-01-01T00:00:00Z"),
                    self._document(
                        row_count=1,
                        first="2026-01-01T00:00:00Z",
                        last="2026-01-01T00:00:00Z",
                        title="DIFFERENT ROLE",
                    ),
                ],
                Path("legacy.jsonl"),
            )


if __name__ == "__main__":
    unittest.main()
