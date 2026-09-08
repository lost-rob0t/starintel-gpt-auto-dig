import json
import tempfile
import unittest
from pathlib import Path

from agents.coverage_backlog import (
    claim_batch,
    complete_batch,
    ensure_ledger,
    fail_batch,
    main,
    shard_items,
    unresolved_items,
)


class CoverageBacklogTests(unittest.TestCase):
    def state(self):
        return {
            "schema": "auto-dig-prolog-state.v1",
            "last_issue": None,
            "last_priority": None,
            "last_branch": None,
            "last_run_id": None,
            "last_success_at": None,
        }

    def ledger(self):
        state = self.state()
        _, ledger = ensure_ledger(
            state,
            corpus="anarchist-violence",
            seed_kind="us-geographic-npa",
            authority="NANPA/FCC",
            shard="B",
            shard_count=3,
            shard_index=1,
        )
        return state, ledger

    def test_sharding_uses_only_authoritative_input_items(self):
        valid = [202, 205, 208, 212, 213, 214, 215]
        self.assertEqual(shard_items(valid, 3, 1), [202, 205, 208, 214])
        self.assertNotIn(211, shard_items(valid, 3, 1))

    def test_claim_is_numeric_bounded_and_no_repeat(self):
        _, ledger = self.ledger()
        valid = [202, 205, 208, 214, 217]
        ledger["completed"] = [202]
        first = claim_batch(ledger, valid, 2)
        second = claim_batch(ledger, valid, 2)
        self.assertEqual(first, [205, 208])
        self.assertEqual(second, [214, 217])
        self.assertEqual(ledger["in_progress"], [205, 208, 214, 217])

    def test_completed_items_never_reenter_unresolved(self):
        _, ledger = self.ledger()
        valid = [202, 205, 208]
        self.assertEqual(claim_batch(ledger, valid, 2), [202, 205])
        complete_batch(ledger, [202, 205])
        self.assertEqual(unresolved_items(ledger, valid), [208])
        self.assertEqual(ledger["completed"], [202, 205])

    def test_failed_items_become_retryable_and_reenter_queue(self):
        _, ledger = self.ledger()
        valid = [202, 205]
        self.assertEqual(claim_batch(ledger, valid, 1), [202])
        fail_batch(ledger, [202])
        self.assertEqual(ledger["failed_retryable"], [202])
        self.assertEqual(unresolved_items(ledger, valid), [202, 205])
        self.assertEqual(claim_batch(ledger, valid, 1), [202])
        self.assertEqual(ledger["failed_retryable"], [])

    def test_new_authoritative_item_appears_without_resetting_state(self):
        _, ledger = self.ledger()
        ledger["completed"] = [202, 205, 208]
        self.assertEqual(unresolved_items(ledger, [202, 205, 208]), [])
        self.assertEqual(unresolved_items(ledger, [202, 205, 208, 214]), [214])

    def test_ledger_identity_cannot_drift(self):
        state, _ = self.ledger()
        with self.assertRaises(ValueError):
            ensure_ledger(
                state,
                corpus="anarchist-violence",
                seed_kind="us-geographic-npa",
                authority="NANPA/FCC",
                shard="B",
                shard_count=3,
                shard_index=2,
            )

    def test_cli_persists_claim_atomically(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state_path = root / "state.json"
            valid_path = root / "valid.json"
            state_path.write_text(json.dumps(self.state()), encoding="utf-8")
            valid_path.write_text(json.dumps([202, 205, 208, 214]), encoding="utf-8")
            rc = main(
                [
                    "--state",
                    str(state_path),
                    "--valid-items",
                    str(valid_path),
                    "--corpus",
                    "anarchist-violence",
                    "--seed-kind",
                    "us-geographic-npa",
                    "--authority",
                    "NANPA/FCC",
                    "--shard",
                    "B",
                    "--shard-count",
                    "3",
                    "--shard-index",
                    "1",
                    "--batch-size",
                    "2",
                ]
            )
            self.assertEqual(rc, 0)
            stored = json.loads(state_path.read_text(encoding="utf-8"))
            ledger = stored["coverage"]["anarchist-violence/us-geographic-npa/B"]
            self.assertEqual(ledger["in_progress"], [202, 205])


if __name__ == "__main__":
    unittest.main()
