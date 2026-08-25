from __future__ import annotations

import unittest

from scripts.quasar_autodig_runtime import RuntimeConfig, build_runtime
from scripts.quasar_autodig_worker import AutoDigLifecycleWorker
from scripts.quasar_issue_queue import GitHubIssueQueueExecutor


class FakeControl:
    pass


class FakeIssues:
    pass


class QuasarAutoDigRuntimeTests(unittest.TestCase):
    def test_runtime_config_requires_only_explicit_service_and_queue_inputs(self) -> None:
        config = RuntimeConfig.from_mapping(
            {
                "QUASAR_CONTROL_URL": "wss://quasar.example/control",
                "QUASAR_SESSION_TOKEN": "session-secret",
                "QUASAR_WORKSPACE_ID": "workspace-1",
                "QUASAR_WORKER_ID": "scheduled-worker-1",
                "AUTO_DIG_REPOSITORY": "lost-rob0t/starintel-gpt-auto-dig",
                "GITHUB_TOKEN": "github-secret",
            }
        )

        self.assertEqual(config.control_url, "wss://quasar.example/control")
        self.assertEqual(config.workspace_id, "workspace-1")
        self.assertEqual(config.worker_id, "scheduled-worker-1")
        self.assertEqual(config.repository, "lost-rob0t/starintel-gpt-auto-dig")
        self.assertNotIn("session-secret", repr(config))
        self.assertNotIn("github-secret", repr(config))

    def test_runtime_config_fails_closed_when_required_secret_is_missing(self) -> None:
        with self.assertRaisesRegex(ValueError, "QUASAR_SESSION_TOKEN"):
            RuntimeConfig.from_mapping(
                {
                    "QUASAR_CONTROL_URL": "wss://quasar.example/control",
                    "QUASAR_WORKSPACE_ID": "workspace-1",
                    "QUASAR_WORKER_ID": "scheduled-worker-1",
                    "AUTO_DIG_REPOSITORY": "lost-rob0t/starintel-gpt-auto-dig",
                    "GITHUB_TOKEN": "github-secret",
                }
            )

    def test_build_runtime_composes_existing_quasar_worker_and_issue_queue_executor(self) -> None:
        config = RuntimeConfig.from_mapping(
            {
                "QUASAR_CONTROL_URL": "wss://quasar.example/control",
                "QUASAR_SESSION_TOKEN": "session-secret",
                "QUASAR_WORKSPACE_ID": "workspace-1",
                "QUASAR_WORKER_ID": "scheduled-worker-1",
                "AUTO_DIG_REPOSITORY": "lost-rob0t/starintel-gpt-auto-dig",
                "GITHUB_TOKEN": "github-secret",
            }
        )
        control = FakeControl()
        issues = FakeIssues()

        runtime = build_runtime(config, control=control, issues=issues)

        self.assertIsInstance(runtime.worker, AutoDigLifecycleWorker)
        self.assertIs(runtime.worker.control, control)
        self.assertIsInstance(runtime.worker.executor, GitHubIssueQueueExecutor)
        self.assertIs(runtime.worker.executor.issues, issues)
        self.assertEqual(runtime.workspace_id, "workspace-1")

    def test_runtime_runs_exactly_one_bounded_worker_iteration(self) -> None:
        calls = []

        class FakeWorker:
            def run_once(self, workspace_id: str) -> int:
                calls.append(workspace_id)
                return 2

        config = RuntimeConfig.from_mapping(
            {
                "QUASAR_CONTROL_URL": "wss://quasar.example/control",
                "QUASAR_SESSION_TOKEN": "session-secret",
                "QUASAR_WORKSPACE_ID": "workspace-1",
                "QUASAR_WORKER_ID": "scheduled-worker-1",
                "AUTO_DIG_REPOSITORY": "lost-rob0t/starintel-gpt-auto-dig",
                "GITHUB_TOKEN": "github-secret",
            }
        )
        runtime = build_runtime(config, worker=FakeWorker())

        self.assertEqual(runtime.run_once(), 2)
        self.assertEqual(calls, ["workspace-1"])


if __name__ == "__main__":
    unittest.main()
