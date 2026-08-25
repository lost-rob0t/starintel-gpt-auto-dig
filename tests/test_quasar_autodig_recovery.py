from __future__ import annotations

import unittest

from scripts.quasar_autodig_worker import (
    AutoDigLifecycleWorker,
    ExecutionResult,
    LifecycleConflict,
)


class RecoveryControl:
    def __init__(self, *, reclaimable: bool) -> None:
        self.reclaimable = reclaimable
        self.run = {
            "runId": "run-restart-1",
            "workspaceId": "ws-restart",
            "status": "active",
            "workerId": "dead-worker",
            "leaseId": "dead-lease",
            "target": "restart.example",
        }
        self.claim_attempts = 0
        self.completed = False

    def list_runs(self, workspace_id: str, *, limit: int = 20) -> list[dict]:
        if workspace_id != self.run["workspaceId"]:
            return []
        return [dict(self.run)][:limit]

    def claim_run(self, workspace_id: str, run_id: str, worker_id: str) -> dict:
        self.claim_attempts += 1
        if not self.reclaimable:
            raise LifecycleConflict("lease is still live")
        self.run.update(
            status="active",
            workerId=worker_id,
            leaseId="replacement-lease",
        )
        return dict(self.run)

    def get_run(self, workspace_id: str, run_id: str) -> dict:
        return dict(self.run)

    def heartbeat(
        self,
        workspace_id: str,
        run_id: str,
        worker_id: str,
        lease_id: str,
    ) -> dict:
        if self.run.get("workerId") != worker_id or self.run.get("leaseId") != lease_id:
            raise LifecycleConflict("stale worker")
        return dict(self.run)

    def complete_run(
        self,
        workspace_id: str,
        run_id: str,
        worker_id: str,
        lease_id: str,
        outcome: dict,
    ) -> dict:
        self.heartbeat(workspace_id, run_id, worker_id, lease_id)
        self.run.update(status="completed", outcome=dict(outcome))
        self.completed = True
        return dict(self.run)

    def fail_run(
        self,
        workspace_id: str,
        run_id: str,
        worker_id: str,
        lease_id: str,
        error: dict,
    ) -> dict:
        raise AssertionError(f"unexpected failure: {error}")


class VerifiedExecutor:
    def execute(self, run: dict, should_continue) -> ExecutionResult:
        should_continue()
        return ExecutionResult.completed(
            {
                "published": True,
                "validationPassed": True,
                "issueNumber": 2293,
            }
        )


class AutoDigWorkerRecoveryTests(unittest.TestCase):
    def test_active_run_is_offered_to_quasar_for_stale_lease_reclaim(self) -> None:
        control = RecoveryControl(reclaimable=True)
        worker = AutoDigLifecycleWorker(
            control,
            VerifiedExecutor(),
            worker_id="replacement-worker",
        )

        self.assertEqual(worker.run_once("ws-restart"), 1)
        self.assertEqual(control.claim_attempts, 1)
        self.assertTrue(control.completed)
        self.assertEqual(control.run["workerId"], "replacement-worker")
        self.assertEqual(control.run["leaseId"], "replacement-lease")

    def test_live_active_lease_remains_exclusive(self) -> None:
        control = RecoveryControl(reclaimable=False)
        worker = AutoDigLifecycleWorker(
            control,
            VerifiedExecutor(),
            worker_id="replacement-worker",
        )

        self.assertEqual(worker.run_once("ws-restart"), 0)
        self.assertEqual(control.claim_attempts, 1)
        self.assertFalse(control.completed)
        self.assertEqual(control.run["workerId"], "dead-worker")


if __name__ == "__main__":
    unittest.main()
