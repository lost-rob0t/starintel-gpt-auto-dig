from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Protocol
from urllib.parse import parse_qsl, quote, urlencode, urlsplit, urlunsplit


PROTOCOL_VERSION = "quasar.control.v1"
WORKER_CLIENT_ID = "starintel-gpt-auto-dig-worker"
_CONFLICT_CODES = {
    "autodig.claim-conflict",
    "autodig.run-not-found",
    "autodig.stale-worker",
}


class LifecycleConflict(RuntimeError):
    """The worker no longer owns the durable Quasar run lease."""


class LifecycleSuspended(LifecycleConflict):
    """The run was paused or stopped at a safe worker checkpoint."""


class LifecycleWaiting(LifecycleConflict):
    """Research is delegated to the canonical issue queue and is still running."""


class QuasarControlError(RuntimeError):
    """Stable Quasar control-plane failure without raw envelope leakage."""

    def __init__(self, code: str, message: str) -> None:
        self.code = str(code or "control-plane.error")
        super().__init__(str(message or "Quasar control-plane request failed."))


class SocketLike(Protocol):
    def send(self, payload: str) -> Any: ...

    def recv(self) -> Any: ...

    def close(self) -> Any: ...


SocketFactory = Callable[[str, float, str | None], SocketLike]


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


def _default_socket_factory(url: str, timeout: float, origin: str | None) -> SocketLike:
    try:
        import websocket  # type: ignore[import-not-found]
    except ImportError as exc:
        raise RuntimeError(
            "websocket-client is required for live Quasar worker transport"
        ) from exc

    options: dict[str, Any] = {"timeout": timeout}
    if origin is not None:
        options["origin"] = origin
    return websocket.create_connection(url, **options)


def _session_url(endpoint: str, session_token: str) -> str:
    if not endpoint.strip():
        raise ValueError("endpoint must be non-empty")
    if not session_token.strip():
        raise ValueError("session_token must be non-empty")

    parts = urlsplit(endpoint)
    if parts.scheme not in {"ws", "wss"} or not parts.netloc:
        raise ValueError("endpoint must be an absolute ws:// or wss:// URL")

    query = parse_qsl(parts.query, keep_blank_values=True)
    query = [(key, value) for key, value in query if key != "session"]
    query.append(("session", session_token))
    encoded_query = urlencode(query, quote_via=quote)
    return urlunsplit(
        (parts.scheme, parts.netloc, parts.path, encoded_query, parts.fragment)
    )


class QuasarWebSocketControlPlane:
    """Least-privilege client for Quasar's worker-only quasar.control.v1 session.

    Quasar remains lifecycle authority. This adapter only translates the Python
    worker protocol into exact typed command envelopes and never persists run
    state or worker leases locally.
    """

    def __init__(
        self,
        endpoint: str,
        *,
        session_token: str,
        timeout: float = 10.0,
        origin: str | None = None,
        socket_factory: SocketFactory = _default_socket_factory,
        request_id_factory: Callable[[], str] | None = None,
    ) -> None:
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        self.url = _session_url(endpoint, session_token)
        self.timeout = float(timeout)
        self.origin = origin
        self.socket_factory = socket_factory
        self.request_id_factory = request_id_factory or (
            lambda: f"autodig-worker-{uuid.uuid4().hex}"
        )

    def _command(self, workspace_id: str, command: str, payload: Mapping[str, Any]) -> Any:
        if not workspace_id.strip():
            raise ValueError("workspace_id must be non-empty")
        request_id = str(self.request_id_factory())
        if not request_id:
            raise ValueError("request_id_factory returned an empty id")

        envelope = {
            "protocol": PROTOCOL_VERSION,
            "id": request_id,
            "command": command,
            "payload": dict(payload),
            "metadata": {
                "client": WORKER_CLIENT_ID,
                "workspace": workspace_id,
            },
        }

        socket = self.socket_factory(self.url, self.timeout, self.origin)
        try:
            socket.send(json.dumps(envelope, separators=(",", ":")))
            for _ in range(100):
                raw = socket.recv()
                if isinstance(raw, bytes):
                    raw = raw.decode("utf-8")
                response = json.loads(str(raw))
                if response.get("protocol") != PROTOCOL_VERSION:
                    continue
                if response.get("id") != request_id:
                    continue
                status = response.get("status")
                if status == "ok":
                    return response.get("result")
                if status == "error":
                    failure = response.get("error") or {}
                    code = str(failure.get("code") or "control-plane.error")
                    message = str(
                        failure.get("message") or "Quasar control-plane request failed."
                    )
                    if code in _CONFLICT_CODES:
                        raise LifecycleConflict(message)
                    raise QuasarControlError(code, message)
                raise QuasarControlError(
                    "protocol.invalid-envelope",
                    "Quasar returned an invalid response status.",
                )
            raise QuasarControlError(
                "control-plane.unavailable",
                "Quasar did not return the matching command response.",
            )
        finally:
            socket.close()

    def list_runs(self, workspace_id: str, *, limit: int = 20) -> list[dict]:
        if limit < 1 or limit > 100:
            raise ValueError("limit must be between 1 and 100")
        result = self._command(workspace_id, "autodig.run.list", {"limit": limit})
        if not isinstance(result, list):
            raise QuasarControlError(
                "protocol.invalid-envelope",
                "Quasar Auto-Dig run list was not an array.",
            )
        return [dict(run) for run in result if isinstance(run, dict)]

    def claim_run(self, workspace_id: str, run_id: str, worker_id: str) -> dict:
        return self._run_command(
            workspace_id,
            "autodig.worker.claim",
            {"runId": run_id, "workerId": worker_id},
        )

    def get_run(self, workspace_id: str, run_id: str) -> dict:
        return self._run_command(
            workspace_id,
            "autodig.run.get",
            {"runId": run_id},
        )

    def heartbeat(
        self,
        workspace_id: str,
        run_id: str,
        worker_id: str,
        lease_id: str,
    ) -> dict:
        return self._run_command(
            workspace_id,
            "autodig.worker.heartbeat",
            {"runId": run_id, "workerId": worker_id, "leaseId": lease_id},
        )

    def complete_run(
        self,
        workspace_id: str,
        run_id: str,
        worker_id: str,
        lease_id: str,
        outcome: dict,
    ) -> dict:
        return self._run_command(
            workspace_id,
            "autodig.worker.complete",
            {
                "runId": run_id,
                "workerId": worker_id,
                "leaseId": lease_id,
                "outcome": dict(outcome),
            },
        )

    def fail_run(
        self,
        workspace_id: str,
        run_id: str,
        worker_id: str,
        lease_id: str,
        error: dict,
    ) -> dict:
        return self._run_command(
            workspace_id,
            "autodig.worker.fail",
            {
                "runId": run_id,
                "workerId": worker_id,
                "leaseId": lease_id,
                "error": dict(error),
            },
        )

    def _run_command(
        self,
        workspace_id: str,
        command: str,
        payload: Mapping[str, Any],
    ) -> dict:
        result = self._command(workspace_id, command, payload)
        if not isinstance(result, dict):
            raise QuasarControlError(
                "protocol.invalid-envelope",
                "Quasar Auto-Dig run response was not an object.",
            )
        return dict(result)


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
            if candidate.get("status") not in {"queued", "active"}:
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
                self.control.heartbeat(
                    workspace_id,
                    run_id,
                    self.worker_id,
                    lease_id,
                )

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
