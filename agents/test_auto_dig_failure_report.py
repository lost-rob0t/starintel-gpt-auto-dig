#!/usr/bin/env python3

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

import auto_dig_failure_report as report


class FailureReportTests(unittest.TestCase):
    def test_structured_failure_and_traceback_are_redacted(self) -> None:
        old_env = os.environ.copy()
        try:
            os.environ["OPENROUTER_API_KEY"] = "sk-or-v1-OPENROUTERSECRETVALUE"
            os.environ["BRAVE_API_KEY"] = "BRAVE-SECRET-VALUE-12345"
            os.environ["PROLOG_RLM_BUG_TOKEN"] = "github_pat_FAKEBUGTOKEN123456789"

            payload = {
                "schema": "prolog-rlm.trace.v1",
                "payload": {
                    "$term": "error",
                    "args": [
                        {
                            "phase": "budget",
                            "kind": "token_budget_exceeded",
                            "message": "token budget exceeded",
                            "used": 9508,
                            "limit": 8192,
                            "usage": {
                                "model_calls": 2,
                                "prompt_tokens": 5412,
                                "completion_tokens": 4096,
                                "total_tokens": 9508,
                            },
                            "authorization": "Bearer should-never-appear",
                            "api_key": "raw-key-should-never-appear",
                        }
                    ],
                },
            }
            stderr = "\n".join(
                [
                    "phase=mcp_ready",
                    "Authorization: Bearer ABCDEFGHIJKLMNOP",
                    "url=https://example.test/?api_key=query-secret&x=1",
                    "openrouter=sk-or-v1-OPENROUTERSECRETVALUE",
                    "brave=BRAVE-SECRET-VALUE-12345",
                    "github=github_pat_FAKEBUGTOKEN123456789",
                    "phase=budget kind=token_budget_exceeded",
                ]
            )

            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                result_path = root / "result.json"
                stderr_path = root / "stderr.log"
                result_path.write_text(json.dumps(payload), encoding="utf-8")
                stderr_path.write_text(stderr, encoding="utf-8")
                rendered = report.render_report(result_path, stderr_path, 120)

            self.assertIn("phase=budget", rendered)
            self.assertIn("kind=token_budget_exceeded", rendered)
            self.assertIn("prompt_tokens=5412", rendered)
            self.assertIn("Sanitized traceback / stderr tail", rendered)
            self.assertIn("[REDACTED]", rendered)
            for secret in (
                "sk-or-v1-OPENROUTERSECRETVALUE",
                "BRAVE-SECRET-VALUE-12345",
                "github_pat_FAKEBUGTOKEN123456789",
                "ABCDEFGHIJKLMNOP",
                "query-secret",
                "raw-key-should-never-appear",
                "should-never-appear",
            ):
                self.assertNotIn(secret, rendered)
        finally:
            os.environ.clear()
            os.environ.update(old_env)

    def test_missing_files_still_produce_useful_report(self) -> None:
        rendered = report.render_report(Path("/no/result"), Path("/no/stderr"), 20)
        self.assertIn("phase=unknown", rendered)
        self.assertIn("no stderr/traceback captured", rendered)


if __name__ == "__main__":
    unittest.main()
