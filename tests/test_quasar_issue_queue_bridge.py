from __future__ import annotations

import unittest

from scripts.quasar_issue_queue import (
    COMPLETION_MARKER,
    RUN_MARKER,
    GitHubIssueQueueExecutor,
    IssueSnapshot,
    parse_completion_receipt,
)
from scripts.quasar_autodig_worker import LifecycleWaiting


class FakeIssues:
    def __init__(self) -> None:
        self.issues: dict[int, IssueSnapshot] = {}
        self.created: list[tuple[str, str, tuple[str, ...]]] = []
        self.next_number = 10

    def find_by_request_key(self, request_key: str) -> IssueSnapshot | None:
        needle = f"auto-dig:{request_key}"
        for issue in self.issues.values():
            if needle in issue.body:
                return issue
        return None

    def create_issue(self, *, title: str, body: str, labels: tuple[str, ...]) -> IssueSnapshot:
        number = self.next_number
        self.next_number += 1
        issue = IssueSnapshot(number=number, state="open", title=title, body=body, comments=())
        self.issues[number] = issue
        self.created.append((title, body, labels))
        return issue

    def refresh_issue(self, number: int) -> IssueSnapshot:
        return self.issues[number]


class QuasarIssueQueueBridgeTests(unittest.TestCase):
    def sample_run(self) -> dict:
        return {
            "runId": "run-42",
            "requestId": "request-42",
            "target": "John Smith",
            "status": "active",
            "workerId": "worker-secret",
            "leaseId": "lease-secret",
            "workspaceId": "private-workspace",
        }

    def test_first_execution_creates_one_canonical_investigation_issue_and_waits(self) -> None:
        issues = FakeIssues()
        executor = GitHubIssueQueueExecutor(issues)
        checkpoints = []

        with self.assertRaises(LifecycleWaiting):
            executor.execute(self.sample_run(), lambda: checkpoints.append("ok"))

        self.assertEqual(checkpoints, ["ok", "ok"])
        self.assertEqual(len(issues.created), 1)
        title, body, labels = issues.created[0]
        self.assertEqual(title, "[Auto-Dig request] John Smith")
        self.assertEqual(labels, ("investigation-target",))
        self.assertIn("<!-- auto-dig-request:v1 -->", body)
        self.assertIn(RUN_MARKER, body)
        self.assertIn("Run ID: `run-42`", body)
        self.assertIn("Request ID: `request-42`", body)
        self.assertNotIn("worker-secret", body)
        self.assertNotIn("lease-secret", body)
        self.assertNotIn("private-workspace", body)

    def test_repeated_or_restarted_execution_reuses_request_key_without_duplicate_issue(self) -> None:
        issues = FakeIssues()
        executor = GitHubIssueQueueExecutor(issues)

        for _ in range(2):
            with self.assertRaises(LifecycleWaiting):
                executor.execute(self.sample_run(), lambda: None)

        self.assertEqual(len(issues.created), 1)

    def test_existing_issue_only_queue_request_with_same_request_key_is_reused(self) -> None:
        issues = FakeIssues()
        seed = GitHubIssueQueueExecutor(issues).render_issue(self.sample_run())
        issues.issues[7] = IssueSnapshot(
            number=7,
            state="open",
            title="existing request",
            body=seed.body.replace(f"\n{RUN_MARKER}", ""),
            comments=(),
        )
        executor = GitHubIssueQueueExecutor(issues)

        with self.assertRaises(LifecycleWaiting):
            executor.execute(self.sample_run(), lambda: None)

        self.assertEqual(issues.created, [])

    def test_closed_issue_without_structured_verified_receipt_does_not_complete(self) -> None:
        issues = FakeIssues()
        rendered = GitHubIssueQueueExecutor(issues).render_issue(self.sample_run())
        issues.issues[8] = IssueSnapshot(
            number=8,
            state="closed",
            title=rendered.title,
            body=rendered.body,
            comments=("done! merged something somewhere",),
        )

        result = GitHubIssueQueueExecutor(issues).execute(self.sample_run(), lambda: None)

        self.assertEqual(result.state, "failed")
        self.assertEqual(result.error["code"], "completion_receipt_missing")

    def test_verified_completion_receipt_is_required_for_completed_result(self) -> None:
        issues = FakeIssues()
        rendered = GitHubIssueQueueExecutor(issues).render_issue(self.sample_run())
        receipt = (
            f"{COMPLETION_MARKER}\n"
            '{"validationPassed":true,"published":true,'
            '"commit":"735d649ee0dcffa0f5e928f9b47c5ab4a690fae2",'
            '"publication":"https://auto-dig.starintel.actor/data/run-42"}'
        )
        issues.issues[9] = IssueSnapshot(
            number=9,
            state="closed",
            title=rendered.title,
            body=rendered.body,
            comments=(receipt,),
        )

        result = GitHubIssueQueueExecutor(issues).execute(self.sample_run(), lambda: None)

        self.assertEqual(result.state, "completed")
        self.assertTrue(result.outcome["validationPassed"])
        self.assertTrue(result.outcome["published"])
        self.assertEqual(result.outcome["issueNumber"], 9)
        self.assertEqual(result.outcome["commit"], "735d649ee0dcffa0f5e928f9b47c5ab4a690fae2")

    def test_receipt_rejects_false_flags_private_urls_and_unstructured_json(self) -> None:
        self.assertIsNone(parse_completion_receipt('{"validationPassed":true,"published":true}'))
        self.assertIsNone(
            parse_completion_receipt(
                f'{COMPLETION_MARKER}\n'
                '{"validationPassed":false,"published":true,'
                '"commit":"abc","publication":"https://auto-dig.starintel.actor/data/x"}'
            )
        )
        self.assertIsNone(
            parse_completion_receipt(
                f'{COMPLETION_MARKER}\n'
                '{"validationPassed":true,"published":true,'
                '"commit":"abc","publication":"http://10.0.0.5/private"}'
            )
        )

    def test_rendered_issue_never_contains_control_plane_transport_or_fencing_values(self) -> None:
        rendered = GitHubIssueQueueExecutor(FakeIssues()).render_issue(self.sample_run())
        lower = rendered.body.lower()
        for forbidden in (
            "quasar.control.v1",
            "worker-secret",
            "lease-secret",
            "private-workspace",
            "session_token",
            "websocket",
        ):
            self.assertNotIn(forbidden, lower)


if __name__ == "__main__":
    unittest.main()
