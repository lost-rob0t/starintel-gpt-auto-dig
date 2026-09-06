from __future__ import annotations

import json
import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from agents.auto_dig_service import (
    DEFAULT_FORGE_HOST,
    DEFAULT_REPO,
    QUEUE_LABEL,
    STATE_ISSUE_TITLE,
    STATE_SCHEMA,
    ForgejoClient,
    ServiceConfig,
    advance_state,
    default_state,
    load_config,
    normalize_issue,
    parse_state_body,
    render_receipt_comment,
    render_request_markdown,
    research_env,
    resolve_model_route,
)


def make_config(**overrides: object) -> ServiceConfig:
    base = dict(
        host=DEFAULT_FORGE_HOST,
        repo=DEFAULT_REPO,
        token=None,
        queue_label=QUEUE_LABEL,
        state_file=None,
        queue_file=None,
        run_root=Path("agent-runs/auto-dig-prolog"),
        repo_root=Path("/tmp/opencode/auto-dig-repo"),
        prolog_rlm_dir=Path("/tmp/opencode/auto-dig-rlm"),
        prolog_rlm_ref="0" * 40,
        force_issue=None,
        max_issues=0,
        time_budget=0.0,
        loop=False,
        interval=3600.0,
        dry_run=False,
        allow_dirty=False,
        model_override=None,
        reasoning_effort_override=None,
    )
    base.update(overrides)
    return ServiceConfig(**base)  # type: ignore[arg-type]


class ServiceConfigTests(unittest.TestCase):
    def test_defaults_target_starintel_forgejo(self) -> None:
        cfg = make_config()
        self.assertEqual(cfg.host, "https://git.starintel.actor")
        self.assertEqual(cfg.repo, "lost-rob0t/starintel-gpt-auto-dig")
        self.assertEqual(cfg.api_base, "https://git.starintel.actor/api/v1/repos/lost-rob0t/starintel-gpt-auto-dig")

    def test_cli_flags_override_environment_defaults(self) -> None:
        cfg = load_config(
            [
                "--host",
                "https://forge.example.org",
                "--repo",
                "owner/research",
                "--max-issues",
                "2",
                "--queue-file",
                "/tmp/opencode/queue.json",
            ]
        )
        self.assertEqual(cfg.host, "https://forge.example.org")
        self.assertEqual(cfg.repo, "owner/research")
        self.assertEqual(cfg.max_issues, 2)
        self.assertEqual(cfg.queue_file, Path("/tmp/opencode/queue.json"))


class QueueTests(unittest.TestCase):
    def test_normalize_issue_maps_forgejo_fields(self) -> None:
        cfg = make_config()
        raw = {
            "number": 2297,
            "title": "[Auto-Dig request] Flock vendor control",
            "body": "## Priority\n\nurgent\n",
            "html_url": "https://git.starintel.actor/lost-rob0t/starintel-gpt-auto-dig/issues/2297",
            "created_at": "2026-08-27T10:00:00Z",
            "updated_at": "2026-08-27T10:00:00Z",
            "labels": [{"name": "investigation-target"}],
        }
        entry = normalize_issue(raw, cfg)
        self.assertEqual(entry["number"], 2297)
        self.assertEqual(entry["url"], raw["html_url"])
        self.assertEqual(entry["labels"], [{"name": "investigation-target"}])
        self.assertIn("urgent", entry["body"])

    def test_normalize_issue_falls_back_to_constructed_url(self) -> None:
        cfg = make_config()
        entry = normalize_issue({"number": 5, "title": "t", "body": ""}, cfg)
        self.assertEqual(
            entry["url"],
            "https://git.starintel.actor/lost-rob0t/starintel-gpt-auto-dig/issues/5",
        )

    def test_client_queue_path_filters_open_issues_with_label(self) -> None:
        cfg = make_config()
        client = ForgejoClient(cfg)
        self.assertTrue(str(client.cfg.api_base).endswith("/api/v1/repos/lost-rob0t/starintel-gpt-auto-dig"))


class StateTests(unittest.TestCase):
    def test_default_state_matches_schema(self) -> None:
        state = default_state()
        self.assertEqual(state["schema"], STATE_SCHEMA)
        self.assertIsNone(state["last_issue"])
        for key in ("last_issue", "last_priority", "last_branch", "last_run_id", "last_success_at"):
            self.assertIn(key, state)

    def test_parse_state_body_rejects_foreign_schema(self) -> None:
        with self.assertRaises(ValueError):
            parse_state_body(json.dumps({"schema": "something-else"}))

    def test_parse_state_body_accepts_empty_body(self) -> None:
        self.assertEqual(parse_state_body(""), default_state())

    def test_advance_state_keeps_actor_fields_and_records_push(self) -> None:
        decision = {
            "next_state": {
                "schema": STATE_SCHEMA,
                "last_issue": 2297,
                "last_priority": "urgent",
                "last_branch": None,
                "last_run_id": None,
                "last_success_at": None,
            }
        }
        state = advance_state(decision, "auto-dig-prolog/2026-09-06-svc-x", "svc-x")
        self.assertEqual(state["last_issue"], 2297)
        self.assertEqual(state["last_priority"], "urgent")
        self.assertEqual(state["last_branch"], "auto-dig-prolog/2026-09-06-svc-x")
        self.assertEqual(state["last_run_id"], "svc-x")
        self.assertEqual(state["schema"], STATE_SCHEMA)
        self.assertIsNotNone(state["last_success_at"])

    def test_state_issue_title_is_the_documented_convention(self) -> None:
        self.assertEqual(STATE_ISSUE_TITLE, "[actor-state] auto-dig-prolog")


class RequestRenderingTests(unittest.TestCase):
    def test_request_includes_structured_body_and_lane_contract(self) -> None:
        decision = {"priority": "high"}
        issue = {
            "number": 1901,
            "title": "[Auto-Dig request] Rensselaer sheriff network",
            "url": "https://git.starintel.actor/lost-rob0t/starintel-gpt-auto-dig/issues/1901",
            "body": "## Subject\n\nRensselaer County Sheriff\n\n## Goal\n\nMap the Flock vendor network.",
        }
        markdown = render_request_markdown(decision, issue)
        self.assertIn("# Auto-Dig request", markdown)
        self.assertIn("## Request body", markdown)
        self.assertIn("## Research lane contract for this run", markdown)
        self.assertIn("Rensselaer County Sheriff", markdown)
        self.assertIn("Queue priority: high", markdown)
        self.assertIn("Intake: git.starintel.actor issues, label `investigation-target`", markdown)
        self.assertIn("read-only web research", markdown)

    def test_request_body_is_verbatim(self) -> None:
        markdown = render_request_markdown({"priority": "normal"}, {"number": 1, "title": "t", "url": "u", "body": "SEED https://example.org"})
        self.assertIn("SEED https://example.org", markdown)

    def test_receipt_documents_run_without_closing_the_issue(self) -> None:
        cfg = make_config()
        comment = render_receipt_comment(cfg, "svc-1", "auto-dig-prolog/2026-09-06-svc-1", "z-ai/glm-5.3-flash", "max")
        self.assertIn("completed bounded run `svc-1`", comment)
        self.assertIn("https://git.starintel.actor/lost-rob0t/starintel-gpt-auto-dig/src/branch/auto-dig-prolog/2026-09-06-svc-1", comment)
        self.assertIn("does **not** mark the investigation complete", comment)
        self.assertIn("z-ai/glm-5.3-flash", comment)


class GatewayModeTests(unittest.TestCase):
    def _with_env(self, env: dict[str, str]) -> None:
        self._saved = {k: os.environ.get(k) for k in env}
        os.environ.update(env)

    def tearDown(self) -> None:
        for key, value in getattr(self, "_saved", {}).items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def test_gateway_mode_requires_gateway_key_and_brave(self) -> None:
        cfg = make_config()
        self._with_env(
            {
                "AUTO_DIG_LLM_ENDPOINT": "https://llm.starintel.actor/v1/chat/completions",
                "AUTO_DIG_LLM_API_KEY": "test-gateway-key",
                "BRAVE_API_KEY": "test-brave-key",
                "OPENROUTER_API_KEY": "",
            }
        )
        self.assertTrue(cfg.gateway_mode)
        env = research_env(cfg)
        self.assertEqual(env["AUTO_DIG_LLM_API_KEY"], "test-gateway-key")

    def test_gateway_mode_fails_closed_without_gateway_key(self) -> None:
        cfg = make_config()
        self._with_env(
            {
                "AUTO_DIG_LLM_ENDPOINT": "https://llm.starintel.actor/v1/chat/completions",
                "AUTO_DIG_LLM_API_KEY": "",
                "BRAVE_API_KEY": "test-brave-key",
            }
        )
        with self.assertRaises(SystemExit):
            research_env(cfg)

    def test_openrouter_mode_still_requires_openrouter_key(self) -> None:
        cfg = make_config()
        self._with_env(
            {
                "AUTO_DIG_LLM_ENDPOINT": "",
                "OPENROUTER_API_KEY": "",
                "BRAVE_API_KEY": "test-brave-key",
            }
        )
        with self.assertRaises(SystemExit):
            research_env(cfg)

    def test_model_override_writes_route_without_router(self) -> None:
        cfg = make_config(model_override="qwen38-27b", reasoning_effort_override="high")
        with TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            route = resolve_model_route(cfg, run_dir, "normal")
            self.assertEqual(route["schema"], "auto-dig-model-route.v1")
            self.assertEqual(route["model"], "qwen38-27b")
            self.assertEqual(route["tier"], "override")
            self.assertEqual(route["reasoning"]["effort"], "high")
            self.assertEqual(
                json.loads((run_dir / "model-route.json").read_text(encoding="utf-8")),
                route,
            )


if __name__ == "__main__":
    unittest.main()
