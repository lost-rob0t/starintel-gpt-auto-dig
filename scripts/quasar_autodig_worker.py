from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping, Protocol


class LifecycleConflict(RuntimeError):
    """The worker no longer owns the durable Quasar run lease."""


class LifecycleSuspended(LifecycleConflict):
    """The run was paused or stopped at a safe worker checkpoint."""


class ControlPlane(Protocol):
    def list_runs(self, workspace_id: str, *, limit: int = 20) -> list[dict]: ...

    def claim_run(self, workspace_id: str, run_id: str, worker_id: str) -> dict: ...

    def get_run(self, workspace_id: str, run_id: str) -> dict: ...

    def heartbeat(
        self,
        workspace_id: str,
        run_id: str,
        worker_id: str,
        lease_id: str,
    ) -> dict: ...

    def complete_run(
        self,
        workspace_id: str,
        run_id: str,
        worker_id: str,
        lease_id: str,
        outcome: dict,
    ) -> dict: ...

    def fail_run(
        self,
        workspace_id: str,
        run_id: str,
        worker_id: str,
        lease_id: str,
        error: dict,
    ) -> dict: ...


class Executor(Protocol):
    def execute(
        self,
        run: dict,
        should_continue: Callable[[], None],
    ) -> "ExecutionResult": ...


@dataclass(frozen=True)
class ExecutionResult:
    state: str
    outcome: dict[str, Any] | None = None
    error: dict[str, Any] | None = None

    @classmethod
    def completed(cls, outcome: Mapping[str, Any]) -> "ExecutionResult":
        return cls(state="completed", outcome=dict(outcome))

    @classmethod
    def failed(cls, *, code: str, message: str) -> "ExecutionResult":
        return cls(
            state="failed",
            error={"code": str(code), "message": str(message)},
        )


class AutoDigLifecycleWorker:
    """Coordinate one scheduled worker iteration through Quasar lifecycle authority.

    This class deliberately owns no durable run state. Quasar owns run identity,
    workspace isolation, status transitions, and the worker lease. The executor
    owns the existing research/validation/publication pipeline.
    """

    def __init__(
        self,
        control: ControlPlane,
        executor: Executor,
        *,
        worker_id: str,
        list_limit: int = 20,
    ) -> None:
        if not worker_id.strip():
            raise ValueError("worker_id must be non-empty")
        if list_limit < 1 or list_limit > 100:
            raise ValueError("list_limit must be between 1 and 100")
        self.control = control
        self.executor = executor
        self.worker_id = worker_id
        self.list_limit = list_limit

    def run_once(self, workspace_id: str) -> int:
        if not workspace_id.strip():
            raise ValueError("workspace_id must be non-empty")

        processed = 0
        for candidate in self.control.list_runs(workspace_id, limit=self.list_limit):
            if candidate.get("status") != "queued":
                continue

            run_id = str(candidate.get("runId") or "")
            if not run_id:
                continue

            try:
                claimed = self.control.claim_run(
                    workspace_id,
                    run_id,
                    self.worker_id,
                )
            except LifecycleConflict:
                continue

            processed += 1
            lease_id = str(claimed.get("leaseId") or "")
            if not lease_id:
                # A claim without a fencing token is unsafe to execute. Do not
                # attempt a mutation with a made-up or missing lease.
                continue

            def should_continue() -> None:
                current = self.control.get_run(workspace_id, run_id)
                status = current.get("status")
                if status in {"paused", "stopped"}:
                    raise LifecycleSuspended(f"run is {status}")
                if status != "active":
                    raise LifecycleConflict(f"run is no longer active: {status!r}")
                if current.get("workerId") != self.worker_id:
                    raise LifecycleConflict("worker ownership changed")
                if current.get("leaseId") != lease_id:
                    raise LifecycleConflict("worker lease changed")

            try:
                self.control.heartbeat(
                    workspace_id,
                    run_id,
                    self.worker_id,
                    lease_id,
                )
                result = self.executor.execute(claimed, should_continue)
                should_continue()
                self._commit_result(
                    workspace_id=workspace_id,
                    run_id=run_id,
                    lease_id=lease_id,
                    result=result,
                )
            except (LifecycleConflict, LifecycleSuspended):
                # A newer user/control-plane decision or worker lease wins. A
                # stale worker must never convert that state into completed or
                # failed.
                continue

        return processed

    def _commit_result(
        self,
        *,
        workspace_id: str,
        run_id: str,
        lease_id: str,
        result: ExecutionResult,
    ) -> None:
        if result.state == "completed":
            outcome = dict(result.outcome or {})
            if outcome.get("validationPassed") is not True or outcome.get("published") is not True:
                self.control.fail_run(
                    workspace_id,
                    run_id,
                    self.worker_id,
                    lease_id,
                    {
                        "code": "completion_gate_failed",
                        "message": "Auto-Dig output was not both validated and published.",
                    },
                )
                return
            self.control.complete_run(
                workspace_id,
                run_id,
                self.worker_id,
                lease_id,
                outcome,
            )
            return

        if result.state == "failed":
            error = dict(result.error or {})
            self.control.fail_run(
                workspace_id,
                run_id,
                self.worker_id,
                lease_id,
                {
                    "code": str(error.get("code") or "autodig_failed"),
                    "message": str(error.get("message") or "Auto-Dig execution failed."),
                },
            )
            return

        self.control.fail_run(
            workspace_id,
            run_id,
            self.worker_id,
            lease_id,
            {
                "code": "invalid_execution_result",
                "message": "Auto-Dig executor returned an unsupported terminal state.",
            },
        )
