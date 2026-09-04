from __future__ import annotations

import unittest

from scripts.quasar_autodig_worker import AutoDigLifecycleWorker
from tests.test_quasar_autodig_worker import CompletingExecutor, FakeControl


class AutoDigWorkerHeartbeatTests(unittest.TestCase):
    def test_each_safe_checkpoint_renews_the_quasar_worker_lease(self) -> None:
        control = FakeControl()
        worker = AutoDigLifecycleWorker(
            control,
            CompletingExecutor(),
            worker_id="worker-a",
        )

        self.assertEqual(worker.run_once("ws-a"), 1)

        # One heartbeat occurs immediately after claim. CompletingExecutor then
        # invokes a safe checkpoint, the worker checks once more before commit,
        # and FakeControl's completion path validates the final lease. Every
        # execution checkpoint must therefore renew the owning Quasar lease.
        self.assertEqual(control.heartbeats, ["run-1", "run-1", "run-1", "run-1"])


if __name__ == "__main__":
    unittest.main()
