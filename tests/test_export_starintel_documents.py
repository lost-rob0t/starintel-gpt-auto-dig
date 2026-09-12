from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "export_starintel_documents.py"
SPEC = importlib.util.spec_from_file_location("export_starintel_documents", SCRIPT)
assert SPEC and SPEC.loader
EXPORTER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = EXPORTER
SPEC.loader.exec_module(EXPORTER)
IMPORTER = EXPORTER.load_importer()


def git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return result.stdout.strip()


def write_packet(path: Path, documents: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(document, separators=(",", ":")) + "\n" for document in documents),
        encoding="utf-8",
    )


def init_repo(root: Path) -> None:
    git(root, "init")
    git(root, "config", "user.email", "test@example.invalid")
    git(root, "config", "user.name", "Diff Ingest Test")


class DiffResolverTests(unittest.TestCase):
    def test_identical_existing_id_added_in_new_packet_is_not_reimported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            init_repo(root)
            document = {"_id": "starintel:test:existing", "dtype": "note", "version": 1}
            write_packet(root / "db" / "note" / "existing.ndjson", [document])
            git(root, "add", ".")
            git(root, "commit", "-m", "base")
            base = git(root, "rev-parse", "HEAD")

            write_packet(
                root / "digs" / "run" / "starintel-documents.jsonl",
                [document],
            )
            git(root, "add", ".")
            git(root, "commit", "-m", "duplicate carrier")

            records = EXPORTER.resolve_diff_records(IMPORTER, root, base)
            self.assertEqual(records, [])

    def test_new_document_is_emitted_once_even_if_two_new_packets_repeat_it(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            init_repo(root)
            (root / "README").write_text("base\n", encoding="utf-8")
            git(root, "add", ".")
            git(root, "commit", "-m", "base")
            base = git(root, "rev-parse", "HEAD")

            document = {"_id": "starintel:test:new", "dtype": "note", "version": 1}
            write_packet(root / "digs" / "a" / "starintel-documents.jsonl", [document])
            write_packet(root / "digs" / "b" / "starintel-documents.jsonl", [document])
            git(root, "add", ".")
            git(root, "commit", "-m", "repeat new logical id")

            records = EXPORTER.resolve_diff_records(IMPORTER, root, base)
            self.assertEqual([record.document_id for record in records], [document["_id"]])

    def test_version_bump_is_emitted_once(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            init_repo(root)
            packet = root / "digs" / "run" / "starintel-documents.jsonl"
            old = {"_id": "starintel:test:versioned", "dtype": "note", "version": 1, "data": {"v": "old"}}
            new = {"_id": "starintel:test:versioned", "dtype": "note", "version": 2, "data": {"v": "new"}}
            write_packet(packet, [old])
            git(root, "add", ".")
            git(root, "commit", "-m", "base")
            base = git(root, "rev-parse", "HEAD")

            write_packet(packet, [new])
            git(root, "add", ".")
            git(root, "commit", "-m", "bump")

            records = EXPORTER.resolve_diff_records(IMPORTER, root, base)
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0].document["version"], 2)

    def test_same_version_mutation_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            init_repo(root)
            packet = root / "digs" / "run" / "starintel-documents.jsonl"
            old = {"_id": "starintel:test:mutated", "dtype": "note", "version": 1, "data": {"v": "old"}}
            changed = {"_id": "starintel:test:mutated", "dtype": "note", "version": 1, "data": {"v": "changed"}}
            write_packet(packet, [old])
            git(root, "add", ".")
            git(root, "commit", "-m", "base")
            base = git(root, "rev-parse", "HEAD")

            write_packet(packet, [changed])
            git(root, "add", ".")
            git(root, "commit", "-m", "mutate")

            with self.assertRaisesRegex(ValueError, "without a version bump"):
                EXPORTER.resolve_diff_records(IMPORTER, root, base)

    def test_version_regression_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            init_repo(root)
            packet = root / "digs" / "run" / "starintel-documents.jsonl"
            old = {"_id": "starintel:test:regress", "dtype": "note", "version": 2}
            regressed = {"_id": "starintel:test:regress", "dtype": "note", "version": 1}
            write_packet(packet, [old])
            git(root, "add", ".")
            git(root, "commit", "-m", "base")
            base = git(root, "rev-parse", "HEAD")

            write_packet(packet, [regressed])
            git(root, "add", ".")
            git(root, "commit", "-m", "regress")

            with self.assertRaisesRegex(ValueError, "version regression"):
                EXPORTER.resolve_diff_records(IMPORTER, root, base)


if __name__ == "__main__":
    unittest.main()
