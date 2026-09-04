from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Callable, Mapping

from scripts.quasar_autodig_worker import (
    AutoDigLifecycleWorker,
    QuasarWebSocketControlPlane,
)
from scripts.quasar_issue_queue import GitHubIssueQueueExecutor, GitHubRestIssueQueue


@dataclass(frozen=True)
class RuntimeConfig:
    control_url: str
    session_token: str = field(repr=False)
    workspace_id: str
    worker_id: str
    repository: str
    github_token: str = field(repr=False)

    @classmethod
    def from_mapping(cls, values: Mapping[str, str]) -> "RuntimeConfig":
        required = (
            "QUASAR_CONTROL_URL",
            "QUASAR_SESSION_TOKEN",
            "QUASAR_WORKSPACE_ID",
            "QUASAR_WORKER_ID",
            "AUTO_DIG_REPOSITORY",
            "GITHUB_TOKEN",
        )
        missing = [name for name in required if not str(values.get(name, "")).strip()]
        if missing:
            raise ValueError(f"missing required runtime configuration: {', '.join(missing)}")

        return cls(
            control_url=str(values["QUASAR_CONTROL_URL"]).strip(),
            session_token=str(values["QUASAR_SESSION_TOKEN"]).strip(),
            workspace_id=str(values["QUASAR_WORKSPACE_ID"]).strip(),
            worker_id=str(values["QUASAR_WORKER_ID"]).strip(),
            repository=str(values["AUTO_DIG_REPOSITORY"]).strip(),
            github_token=str(values["GITHUB_TOKEN"]).strip(),
        )


@dataclass
class AutoDigRuntime:
    worker: AutoDigLifecycleWorker
    workspace_id: str

    def run_once(self) -> int:
        return self.worker.run_once(self.workspace_id)


def build_runtime(
    config: RuntimeConfig,
    *,
    control=None,
    issues=None,
    worker=None,
) -> AutoDigRuntime:
    if worker is not None:
        return AutoDigRuntime(worker=worker, workspace_id=config.workspace_id)

    if control is None:
        control = QuasarWebSocketControlPlane(
            config.control_url,
            session_token=config.session_token,
        )
    if issues is None:
        issues = GitHubRestIssueQueue(
            config.repository,
            token=config.github_token,
        )

    executor = GitHubIssueQueueExecutor(issues)
    lifecycle_worker = AutoDigLifecycleWorker(
        control,
        executor,
        worker_id=config.worker_id,
    )
    return AutoDigRuntime(worker=lifecycle_worker, workspace_id=config.workspace_id)


def run_from_mapping(
    values: Mapping[str, str],
    *,
    builder: Callable[[RuntimeConfig], AutoDigRuntime] = build_runtime,
) -> int:
    config = RuntimeConfig.from_mapping(values)
    return builder(config).run_once()


def main() -> int:
    processed = run_from_mapping(os.environ)
    print(f"processed={processed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
