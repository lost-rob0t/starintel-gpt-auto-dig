from __future__ import annotations

import json
import unittest

from scripts.quasar_autodig_worker import (
    AutoDigLifecycleWorker,
    ExecutionResult,
    LifecycleConflict,
    QuasarControlError,
    QuasarWebSocketControlPlane,
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


class FakeSocket:
    def __init__(self, responses: list[dict]) -> None:
        self.responses = [json.dumps(response) for response in responses]
        self.sent: list[dict] = []
        self.closed = False

    def send(self, payload: str) -> None:
        self.sent.append(json.loads(payload))

    def recv(self) -> str:
        if not self.responses:
            raise AssertionError("unexpected recv")
        return self.responses.pop(0)

    def close(self) -> None:
        self.closed = True


class SocketFactory:
    def __init__(self, responses: list[dict]) -> None:
        self.socket = FakeSocket(responses)
        self.calls: list[tuple[str, float, str | None]] = []

    def __call__(self, url: str, timeout: float, origin: str | None) -> FakeSocket:
        self.calls.append((url, timeout, origin))
        return self.socket


class QuasarWebSocketControlPlaneTests(unittest.TestCase):
    def test_list_runs_uses_authenticated_session_and_exact_control_envelope(self) -> None:
        factory = SocketFactory(
            [
                {
                    "protocol": "quasar.control.v1",
                    "id": "worker-1",
                    "status": "ok",
                    "result": [{"runId": "run-1", "status": "queued"}],
                }
            ]
        )
        control = QuasarWebSocketControlPlane(
            "wss://quasar.internal/control",
            session_token="secret token+/=",
            socket_factory=factory,
            request_id_factory=lambda: "worker-1",
            timeout=3.5,
            origin="https://worker.starintel.actor",
        )

        runs = control.list_runs("workspace-a", limit=7)

        self.assertEqual(runs, [{"runId": "run-1", "status": "queued"}])
        self.assertEqual(
            factory.calls,
            [
                (
                    "wss://quasar.internal/control?session=secret%20token%2B%2F%3D",
                    3.5,
                    "https://worker.starintel.actor",
                )
            ],
        )
        self.assertEqual(
            factory.socket.sent,
            [
                {
                    "protocol": "quasar.control.v1",
                    "id": "worker-1",
                    "command": "autodig.run.list",
                    "payload": {"limit": 7},
                    "metadata": {
                        "client": "starintel-gpt-auto-dig-worker",
                        "workspace": "workspace-a",
                    },
                }
            ],
        )
        self.assertTrue(factory.socket.closed)

    def test_claim_maps_quasar_claim_conflict_to_lifecycle_conflict(self) -> None:
        factory = SocketFactory(
            [
                {
                    "protocol": "quasar.control.v1",
                    "id": "claim-1",
                    "status": "error",
                    "error": {
                        "code": "autodig.claim-conflict",
                        "message": "run already claimed",
                    },
                }
            ]
        )
        control = QuasarWebSocketControlPlane(
            "ws://127.0.0.1:8081",
            session_token="worker-session",
            socket_factory=factory,
            request_id_factory=lambda: "claim-1",
        )

        with self.assertRaises(LifecycleConflict):
            control.claim_run("ws-a", "run-1", "worker-a")

        self.assertEqual(
            factory.socket.sent[0]["payload"],
            {"runId": "run-1", "workerId": "worker-a"},
        )

    def test_unknown_control_error_keeps_stable_code_without_raw_envelope(self) -> None:
        factory = SocketFactory(
            [
                {
                    "protocol": "quasar.control.v1",
                    "id": "get-1",
                    "status": "error",
                    "error": {
                        "code": "security.forbidden",
                        "message": "workspace denied",
                        "details": {"internal": "must-not-leak-in-exception-string"},
                    },
                }
            ]
        )
        control = QuasarWebSocketControlPlane(
            "ws://127.0.0.1:8081?mode=worker",
            session_token="worker-session",
            socket_factory=factory,
            request_id_factory=lambda: "get-1",
        )

        with self.assertRaises(QuasarControlError) as caught:
            control.get_run("ws-a", "run-1")

        self.assertEqual(caught.exception.code, "security.forbidden")
        self.assertEqual(str(caught.exception), "workspace denied")
        self.assertNotIn("internal", str(caught.exception))
        self.assertEqual(
            factory.calls[0][0],
            "ws://127.0.0.1:8081?mode=worker&session=worker-session",
        )

    def test_complete_and_fail_send_worker_fencing_payloads(self) -> None:
        responses = [
            {"protocol": "quasar.control.v1", "id": "1", "status": "ok", "result": {}},
            {"protocol": "quasar.control.v1", "id": "2", "status": "ok", "result": {}},
        ]
        ids = iter(["1", "2"])
        factory = SocketFactory(responses)
        control = QuasarWebSocketControlPlane(
            "ws://127.0.0.1:8081",
            session_token="worker-session",
            socket_factory=factory,
            request_id_factory=lambda: next(ids),
        )

        control.complete_run(
            "ws-a",
            "run-1",
            "worker-a",
            "lease-a",
            {"published": True, "validationPassed": True},
        )
        control.fail_run(
            "ws-a",
            "run-2",
            "worker-a",
            "lease-b",
            {"code": "validation_failed", "message": "failed"},
        )

        self.assertEqual(
            factory.socket.sent[0]["command"],
            "autodig.worker.complete",
        )
        self.assertEqual(
            factory.socket.sent[0]["payload"],
            {
                "runId": "run-1",
                "workerId": "worker-a",
                "leaseId": "lease-a",
                "outcome": {"published": True, "validationPassed": True},
            },
        )
        self.assertEqual(factory.socket.sent[1]["command"], "autodig.worker.fail")
        self.assertEqual(
            factory.socket.sent[1]["payload"],
            {
                "runId": "run-2",
                "workerId": "worker-a",
                "leaseId": "lease-b",
                "error": {"code": "validation_failed", "message": "failed"},
            },
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
