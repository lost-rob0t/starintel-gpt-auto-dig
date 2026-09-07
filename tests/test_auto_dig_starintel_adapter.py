from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.auto_dig_starintel_adapter import handle_request
from starintel_doc.model import Document


class AutoDigStarIntelAdapterTests(unittest.TestCase):
    def test_types_and_schema_are_repository_owned(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            types = handle_request("types", {}, root=root)
            self.assertIn("org", types["dtypes"])
            schema = handle_request("schema", {"dtype": "org"}, root=root)
            self.assertEqual(schema["dtype"], "org")
            self.assertEqual(schema["schema"]["properties"]["dtype"]["const"], "org")

    def test_search_is_bounded_and_returns_locations(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for suffix in ("one", "two"):
                document = Document.create(
                    "org",
                    "test",
                    doc_id=f"starintel:org:{suffix}",
                    title=f"Example {suffix}",
                    data={"name": f"Example {suffix}"},
                ).to_dict()
                handle_request("write-document", {"document": document}, root=root)
            result = handle_request("search", {"query": "Example", "limit": 1}, root=root)
            self.assertEqual(result["count"], 1)
            self.assertEqual(result["results"][0]["surface"], "db")
            self.assertTrue(result["results"][0]["path"].startswith("db/org/"))

    def test_draft_and_validate_return_complete_canonical_document(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            draft = handle_request(
                "draft",
                {
                    "dtype": "org",
                    "dataset": "test",
                    "id": "starintel:org:example",
                    "title": "Example",
                    "data": {"name": "Example"},
                    "metadata": {"sources": [{"url": "https://example.org"}]},
                },
                root=root,
            )
            self.assertEqual(draft["document"]["schema_version"], "0.9.0")
            validated = handle_request(
                "validate-document", {"document": draft["document"]}, root=root
            )
            self.assertTrue(validated["valid"])

    def test_prepare_write_is_pure_and_write_refuses_changed_existing_id(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            document = Document.create(
                "org",
                "test",
                doc_id="starintel:org:example",
                data={"name": "Example"},
            ).to_dict()
            prepared = handle_request(
                "prepare-write", {"document": document}, root=root
            )
            target = root / prepared["details"]["target"]
            self.assertFalse(target.exists())
            written = handle_request(
                "write-document", prepared["request"], root=root
            )
            self.assertEqual(written["status"], "written")
            self.assertTrue(target.exists())
            changed = dict(document)
            changed["title"] = "Changed"
            with self.assertRaisesRegex(ValueError, "already exists"):
                handle_request("write-document", {"document": changed}, root=root)

    def test_issue_reply_is_idempotent_by_content_marker(self) -> None:
        calls: list[list[str]] = []

        def runner(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
            calls.append(command)
            if command[1:3] == ["api", "--paginate"]:
                return subprocess.CompletedProcess(command, 0, stdout="[]", stderr="")
            return subprocess.CompletedProcess(
                command,
                0,
                stdout="https://github.com/example/repo/issues/7#issuecomment-1\n",
                stderr="",
            )

        request = {"body": "Research pass completed with unresolved primary records."}
        result = handle_request(
            "issue-reply",
            request,
            root=Path("."),
            github_repository="example/repo",
            issue=7,
            runner=runner,
        )
        self.assertEqual(result["status"], "posted")
        self.assertIn("<!-- auto-dig-prolog-reply:", result["body"])
        self.assertEqual(len(calls), 2)
        posted_body = calls[1][calls[1].index("--body") + 1]
        marker = posted_body.splitlines()[0]

        def existing_runner(
            command: list[str], **kwargs: object
        ) -> subprocess.CompletedProcess[str]:
            payload = json.dumps(
                [{"html_url": "https://example.test/comment/1", "body": marker + "\nold"}]
            )
            return subprocess.CompletedProcess(command, 0, stdout=payload, stderr="")

        replay = handle_request(
            "issue-reply",
            request,
            root=Path("."),
            github_repository="example/repo",
            issue=7,
            runner=existing_runner,
        )
        self.assertEqual(replay["status"], "existing")
        self.assertEqual(replay["url"], "https://example.test/comment/1")

    def test_issue_reply_requires_trusted_repository_and_issue(self) -> None:
        with self.assertRaisesRegex(ValueError, "repository"):
            handle_request("issue-reply", {"body": "hello"}, root=Path("."))


if __name__ == "__main__":
    unittest.main()
