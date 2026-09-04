from __future__ import annotations

import io
import os
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from scripts.quasar_autodig_runtime import RuntimeConfig, build_runtime, main, run_from_mapping
from scripts.quasar_autodig_worker import AutoDigLifecycleWorker
from scripts.quasar_issue_queue import GitHubIssueQueueExecutor


class FakeControl:
    pass


class FakeIssues:
    pass


class QuasarAutoDigRuntimeTests(unittest.TestCase):
    def runtime_values(self) -> dict[str, str]:
        return {
            "QUASAR_CONTROL_URL": "wss://quasar.example/control",
            "QUASAR_SESSION_TOKEN": "session-secret",
            "QUASAR_WORKSPACE_ID": "workspace-1",
            "QUASAR_WORKER_ID": "scheduled-worker-1",
            "AUTO_DIG_REPOSITORY": "lost-rob0t/starintel-gpt-auto-dig",
            "GITHUB_TOKEN": "github-secret",
        }

    def test_runtime_config_requires_only_explicit_service_and_queue_inputs(self) -> None:
        config = RuntimeConfig.from_mapping(self.runtime_values())

        self.assertEqual(config.control_url, "wss://quasar.example/control")
        self.assertEqual(config.workspace_id, "workspace-1")
        self.assertEqual(config.worker_id, "scheduled-worker-1")
        self.assertEqual(config.repository, "lost-rob0t/starintel-gpt-auto-dig")
        self.assertNotIn("session-secret", repr(config))
        self.assertNotIn("github-secret", repr(config))

    def test_runtime_config_fails_closed_when_required_secret_is_missing(self) -> None:
        values = self.runtime_values()
        del values["QUASAR_SESSION_TOKEN"]

        with self.assertRaisesRegex(ValueError, "QUASAR_SESSION_TOKEN"):
            RuntimeConfig.from_mapping(values)

    def test_build_runtime_composes_existing_quasar_worker_and_issue_queue_executor(self) -> None:
        config = RuntimeConfig.from_mapping(self.runtime_values())
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

        config = RuntimeConfig.from_mapping(self.runtime_values())
        runtime = build_runtime(config, worker=FakeWorker())

        self.assertEqual(runtime.run_once(), 2)
        self.assertEqual(calls, ["workspace-1"])

    def test_run_from_mapping_is_the_scheduler_facing_single_iteration_boundary(self) -> None:
        seen = []

        class FakeRuntime:
            def run_once(self) -> int:
                return 3

        def fake_builder(config: RuntimeConfig):
            seen.append(config)
            return FakeRuntime()

        self.assertEqual(run_from_mapping(self.runtime_values(), builder=fake_builder), 3)
        self.assertEqual(len(seen), 1)
        self.assertEqual(seen[0].workspace_id, "workspace-1")

    def test_module_main_reads_environment_runs_once_and_logs_only_processed_count(self) -> None:
        output = io.StringIO()
        values = self.runtime_values()

        with patch.dict(os.environ, values, clear=True):
            with patch("scripts.quasar_autodig_runtime.run_from_mapping", return_value=2) as run:
                with redirect_stdout(output):
                    self.assertEqual(main(), 0)

        run.assert_called_once()
        self.assertEqual(output.getvalue(), "processed=2\n")
        self.assertNotIn("session-secret", output.getvalue())
        self.assertNotIn("github-secret", output.getvalue())


if __name__ == "__main__":
    unittest.main()
