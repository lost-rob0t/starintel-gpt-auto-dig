from __future__ import annotations

import unittest
from pathlib import Path

from scripts.auto_dig_request import REQUEST_MARKER, render_body, request_key


ROOT = Path(__file__).resolve().parents[1]


class AutoDigRequestTests(unittest.TestCase):
    def test_request_key_ignores_case_and_incidental_whitespace(self) -> None:
        left = request_key(
            subject="Flock VP incident",
            goal="Map the incident and evidence",
            scope="Public records only",
            completion="Publish findings",
        )
        right = request_key(
            subject="  flock   vp INCIDENT ",
            goal="map the incident AND evidence",
            scope=" public records only ",
            completion="publish findings",
        )
        self.assertEqual(left, right)

    def test_request_key_changes_when_research_goal_changes(self) -> None:
        base = dict(
            subject="Flock VP incident",
            scope="Public records only",
            completion="Publish findings",
        )
        self.assertNotEqual(
            request_key(goal="Map people", **base),
            request_key(goal="Map contracts", **base),
        )

    def test_manual_dedupe_key_is_stable_across_rewording(self) -> None:
        first = request_key(
            subject="One wording",
            goal="One goal",
            scope="One scope",
            completion="One completion",
            dedupe_key="flock-vp-incident",
        )
        second = request_key(
            subject="Totally different wording",
            goal="Different goal",
            scope="Different scope",
            completion="Different completion",
            dedupe_key=" FLOCK-VP-INCIDENT ",
        )
        self.assertEqual(first, second)

    def test_rendered_body_carries_machine_identity_and_queue_rule(self) -> None:
        key, body = render_body(
            subject="Subject",
            goal="Goal",
            scope="Scope",
            seed_sources="https://example.invalid/source",
            constraints="No private data",
            completion="Publish validated findings",
            priority="high",
        )
        self.assertIn(REQUEST_MARKER, body)
        self.assertIn(f"Request key: `auto-dig:{key}`", body)
        self.assertIn("drain open request issues before selecting autonomous", body)

    def test_issue_form_and_action_use_the_shared_queue(self) -> None:
        form = (ROOT / ".github/ISSUE_TEMPLATE/auto-dig-request.yml").read_text(encoding="utf-8")
        workflow = (ROOT / ".github/workflows/auto-dig-request.yml").read_text(encoding="utf-8")
        self.assertIn("investigation-target", form)
        self.assertIn("investigation-target", workflow)
        self.assertIn("scripts/auto_dig_request.py", workflow)
        self.assertIn("gh issue list", workflow)
        self.assertIn("gh issue create", workflow)


if __name__ == "__main__":
    unittest.main()
