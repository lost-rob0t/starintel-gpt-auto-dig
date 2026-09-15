from __future__ import annotations

import unittest

from scripts.quasar_autodig_worker import AutoDigLifecycleWorker
from tests.test_quasar_autodig_worker import CompletingExecutor, FakeControl


class PublicRunControl(FakeControl):
    """Mirror Quasar's public autodig.run.get projection.

    Claim/heartbeat own the private worker lease, while run.get intentionally
    exposes lifecycle status without workerId/leaseId fencing material.
    """

    def get_run(self, workspace_id: str, run_id: str) -> dict:
        public = super().get_run(workspace_id, run_id)
        for key in ("workerId", "leaseId", "claimedAt", "heartbeatAt"):
            public.pop(key, None)
        return public


class QuasarPublicRunContractTests(unittest.TestCase):
    def test_safe_checkpoint_fences_with_heartbeat_not_public_run_lease_fields(self) -> None:
        control = PublicRunControl()
        worker = AutoDigLifecycleWorker(
            control,
            CompletingExecutor(),
            worker_id="worker-a",
        )

        self.assertEqual(worker.run_once("ws-a"), 1)
        self.assertEqual(control.completions, ["run-1"])
        self.assertEqual(control.failures, [])
        self.assertEqual(control.runs["run-1"]["status"], "completed")


if __name__ == "__main__":
    unittest.main()
