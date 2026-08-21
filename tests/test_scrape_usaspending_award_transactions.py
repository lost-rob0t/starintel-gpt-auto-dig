from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "scrape_usaspending_award_transactions.py"
SPEC = importlib.util.spec_from_file_location(
    "scrape_usaspending_award_transactions",
    MODULE_PATH,
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class USAspendingAwardTransactionTests(unittest.TestCase):
    def test_default_awards_cover_bae_and_intelliware_orders(self) -> None:
        self.assertEqual(
            {
                "CONT_AWD_15F06725F0001209_1549_GS00F240CA_4732",
                "CONT_AWD_15F06725F0001838_1549_GS00F240CA_4732",
                "CONT_AWD_15F06726F0000362_1549_GS10F0473Y_4732",
            },
            set(MODULE.DEFAULT_GENERATED_AWARD_IDS),
        )

    def test_transaction_payload_is_stable(self) -> None:
        payload = MODULE.transaction_payload(
            "CONT_AWD_TEST_1549_PARENT_4732",
            page=2,
            limit=50,
        )
        self.assertEqual("CONT_AWD_TEST_1549_PARENT_4732", payload["award_id"])
        self.assertEqual(2, payload["page"])
        self.assertEqual(50, payload["limit"])
        self.assertEqual("action_date", payload["sort"])
        self.assertEqual("desc", payload["order"])

    def test_transaction_payload_rejects_invalid_inputs(self) -> None:
        with self.assertRaises(ValueError):
            MODULE.transaction_payload("", page=1, limit=100)
        with self.assertRaises(ValueError):
            MODULE.transaction_payload("award", page=0, limit=100)
        with self.assertRaises(ValueError):
            MODULE.transaction_payload("award", page=1, limit=101)

    def test_transaction_identity_prefers_stable_ids(self) -> None:
        self.assertEqual(
            "generated_transaction_unique_id:abc",
            MODULE.transaction_identity(
                {
                    "generated_transaction_unique_id": "abc",
                    "transaction_id": "secondary",
                }
            ),
        )
        self.assertEqual(
            "transaction_id:secondary",
            MODULE.transaction_identity({"transaction_id": "secondary"}),
        )
        fallback = MODULE.transaction_identity({"action_date": "2026-04-01"})
        self.assertTrue(fallback.startswith("sha256:"))
        self.assertEqual(71, len(fallback))

    def test_page_detection_honors_metadata(self) -> None:
        self.assertTrue(
            MODULE.has_next_page(
                {"page_metadata": {"hasNext": True}},
                [{}],
                page=1,
                limit=100,
            )
        )
        self.assertFalse(
            MODULE.has_next_page(
                {"page_metadata": {"hasNext": False}},
                [{}] * 100,
                page=1,
                limit=100,
            )
        )
        self.assertTrue(
            MODULE.has_next_page(
                {"page_metadata": {"total": 201}},
                [{}] * 100,
                page=2,
                limit=100,
            )
        )

    def test_raw_record_preserves_award_and_transaction(self) -> None:
        transaction = {
            "generated_transaction_unique_id": "tx-1",
            "action_date": "2026-04-01",
            "federal_action_obligation": -1000,
        }
        record = MODULE.raw_record(
            generated_award_id="CONT_AWD_TEST",
            transaction=transaction,
            retrieved_at="2026-08-03T00:00:00Z",
        )
        self.assertEqual("award-transaction", record["record_type"])
        self.assertEqual("CONT_AWD_TEST", record["generated_award_id"])
        self.assertEqual(transaction, record["payload"])
        self.assertEqual(64, len(record["sha256"]))
        self.assertTrue(record["source_url"].endswith("/CONT_AWD_TEST"))

    def test_jsonl_output_is_deterministic_and_deduplicated(self) -> None:
        records = [
            MODULE.raw_record(
                generated_award_id="B",
                transaction={"generated_transaction_unique_id": "2"},
                retrieved_at="2026-08-03T00:00:00Z",
            ),
            MODULE.raw_record(
                generated_award_id="A",
                transaction={"generated_transaction_unique_id": "1"},
                retrieved_at="2026-08-03T00:00:00Z",
            ),
        ]
        records.append(dict(records[0]))
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "transactions.jsonl"
            self.assertEqual(2, MODULE.write_jsonl(records, output))
            rows = [json.loads(line) for line in output.read_text().splitlines()]
        self.assertEqual(["A", "B"], [row["generated_award_id"] for row in rows])


if __name__ == "__main__":
    unittest.main()
