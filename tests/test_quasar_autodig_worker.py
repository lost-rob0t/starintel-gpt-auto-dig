from __future__ import annotations

import unittest

from scripts.quasar_autodig_worker import (
    AutoDigLifecycleWorker,
    ExecutionResult,
    LifecycleConflict,
)


class FakeControl:
    def __init__(self) -> None:
        self.runs = {
            "run-1": {
                "runId": "run-1",
                "workspaceId": "ws-a",
                "status": "queued",
                "target": "example.org",
            }
        }
        self.claims: list[tuple[str, str]] = []
        self.completions: list[str] = []
        self.failures: list[str] = []
        self.heartbeats: list[str] = []
        self.lease_counter = 0

    def list_runs(self, workspace_id: str, *, limit: int = 20) -> list[dict]:
        return [
            dict(run)
            for run in self.runs.values()
            if run["workspaceId"] == workspace_id and run["status"] == "queued"
        ][:limit]

    def claim_run(self, workspace_id: str, run_id: str, worker_id: str) -> dict:
        run = self.runs[run_id]
        if run["workspaceId"] != workspace_id or run["status"] != "queued":
            raise LifecycleConflict("claim conflict")
        self.lease_counter += 1
        lease_id = f"lease-{self.lease_counter}"
        run.update(status="active", workerId=worker_id, leaseId=lease_id)
        self.claims.append((run_id, worker_id))
        return dict(run)

    def get_run(self, workspace_id: str, run_id: str) -> dict:
        run = self.runs[run_id]
        if run["workspaceId"] != workspace_id:
            raise LifecycleConflict("wrong workspace")
        return dict(run)

    def heartbeat(self, workspace_id: str, run_id: str, worker_id: str, lease_id: str) -> dict:
        run = self.runs[run_id]
        if run.get("workerId") != worker_id or run.get("leaseId") != lease_id:
            raise LifecycleConflict("stale worker")
        self.heartbeats.append(run_id)
        return dict(run)

    def complete_run(
        self,
        workspace_id: str,
        run_id: str,
        worker_id: str,
        lease_id: str,
        outcome: dict,
    ) -> dict:
        self.heartbeat(workspace_id, run_id, worker_id, lease_id)
        self.runs[run_id].update(status="completed", outcome=dict(outcome))
        self.completions.append(run_id)
        return dict(self.runs[run_id])

    def fail_run(
        self,
        workspace_id: str,
        run_id: str,
        worker_id: str,
        lease_id: str,
        error: dict,
    ) -> dict:
        self.heartbeat(workspace_id, run_id, worker_id, lease_id)
        self.runs[run_id].update(status="failed", error=dict(error))
        self.failures.append(run_id)
        return dict(self.runs[run_id])


class CompletingExecutor:
    def __init__(self) -> None:
        self.calls = 0

    def execute(self, run: dict, should_continue) -> ExecutionResult:
        self.calls += 1
        self.assert_can_continue = should_continue
        self.assert_can_continue()
        return ExecutionResult.completed(
            {
                "issueNumber": 123,
                "published": True,
                "validationPassed": True,
            }
        )


class PausingExecutor:
    def __init__(self, control: FakeControl) -> None:
        self.control = control
        self.calls = 0

    def execute(self, run: dict, should_continue) -> ExecutionResult:
        self.calls += 1
        self.control.runs[run["runId"]]["status"] = "paused"
        should_continue()
        raise AssertionError("paused run must not continue execution")


class FailingExecutor:
    def execute(self, run: dict, should_continue) -> ExecutionResult:
        should_continue()
        return ExecutionResult.failed(
            code="validation_failed",
            message="merge/publication validation failed",
        )


class AutoDigLifecycleWorkerTests(unittest.TestCase):
    def test_claims_queued_run_once_and_completes_only_verified_result(self) -> None:
        control = FakeControl()
        executor = CompletingExecutor()
        worker = AutoDigLifecycleWorker(control, executor, worker_id="worker-a")

        self.assertEqual(worker.run_once("ws-a"), 1)
        self.assertEqual(worker.run_once("ws-a"), 0)
        self.assertEqual(control.claims, [("run-1", "worker-a")])
        self.assertEqual(control.completions, ["run-1"])
        self.assertEqual(control.failures, [])
        self.assertEqual(executor.calls, 1)
        self.assertTrue(control.runs["run-1"]["outcome"]["published"])

    def test_pause_observed_at_safe_checkpoint_prevents_completion(self) -> None:
        control = FakeControl()
        worker = AutoDigLifecycleWorker(
            control,
            PausingExecutor(control),
            worker_id="worker-a",
        )

        self.assertEqual(worker.run_once("ws-a"), 1)
        self.assertEqual(control.runs["run-1"]["status"], "paused")
        self.assertEqual(control.completions, [])
        self.assertEqual(control.failures, [])

    def test_validation_failure_is_failed_not_completed(self) -> None:
        control = FakeControl()
        worker = AutoDigLifecycleWorker(control, FailingExecutor(), worker_id="worker-a")

        self.assertEqual(worker.run_once("ws-a"), 1)
        self.assertEqual(control.runs["run-1"]["status"], "failed")
        self.assertEqual(control.completions, [])
        self.assertEqual(control.failures, ["run-1"])
        self.assertEqual(control.runs["run-1"]["error"]["code"], "validation_failed")

    def test_stale_worker_fails_closed(self) -> None:
        control = FakeControl()
        executor = CompletingExecutor()
        worker = AutoDigLifecycleWorker(control, executor, worker_id="worker-a")
        original_claim = control.claim_run

        def stolen_claim(workspace_id: str, run_id: str, worker_id: str) -> dict:
            claimed = original_claim(workspace_id, run_id, worker_id)
            control.runs[run_id]["leaseId"] = "newer-lease"
            return claimed

        control.claim_run = stolen_claim  # type: ignore[method-assign]

        self.assertEqual(worker.run_once("ws-a"), 1)
        self.assertEqual(control.completions, [])
        self.assertEqual(control.failures, [])
        self.assertEqual(control.runs["run-1"]["status"], "active")


if __name__ == "__main__":
    unittest.main()
