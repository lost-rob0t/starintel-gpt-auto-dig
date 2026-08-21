from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from starintel_doc.integrity import (
    build_corpus_inclusion_proof,
    build_corpus_seal,
    build_seal,
    verify_corpus_seal,
    verify_inclusion_proof,
)
from starintel_doc.integrity_site import publish_site_seal
from starintel_doc.store import LocatedDocument, compact


def document(doc_id: str, *, title: str, dtype: str = "claim") -> dict:
    return {
        "_id": doc_id,
        "dataset": "test",
        "dtype": dtype,
        "schema_version": "0.9.0",
        "title": title,
        "data": {"value": title},
    }


def write_corpus(path: Path, documents: list[dict]) -> None:
    path.write_text(
        "".join(compact(item) + "\n" for item in documents),
        encoding="utf-8",
    )


class EvidenceSealTests(unittest.TestCase):
    def test_seal_is_deterministic_for_input_iteration_order(self) -> None:
        first = LocatedDocument(
            document("starintel:claim:a", title="A"),
            Path("a.ndjson"),
            1,
            "test",
        )
        second = LocatedDocument(
            document("starintel:org:b", title="B", dtype="org"),
            Path("b.ndjson"),
            1,
            "test",
        )
        forward = build_seal([first, second])
        reverse = build_seal([second, first])
        self.assertEqual(forward, reverse)

    def test_mutation_changes_root_and_fails_receipt_verification(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            corpus = Path(directory) / "corpus.jsonl"
            write_corpus(corpus, [document("starintel:claim:a", title="A")])
            receipt = build_corpus_seal(corpus)
            self.assertTrue(verify_corpus_seal(corpus, receipt)["ok"])

            write_corpus(corpus, [document("starintel:claim:a", title="Changed")])
            result = verify_corpus_seal(corpus, receipt)
            self.assertFalse(result["ok"])
            self.assertNotEqual(
                receipt["merkle_root_sha256"],
                result["actual"]["merkle_root_sha256"],
            )

    def test_inclusion_proof_round_trip_and_tamper_detection(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            corpus = Path(directory) / "corpus.jsonl"
            write_corpus(
                corpus,
                [
                    document("starintel:claim:a", title="A"),
                    document("starintel:claim:b", title="B"),
                    document("starintel:claim:c", title="C"),
                ],
            )
            proof = build_corpus_inclusion_proof(corpus, "starintel:claim:c")
            verified = verify_inclusion_proof(proof)
            self.assertTrue(verified["ok"], verified["errors"])

            tampered = copy.deepcopy(proof)
            tampered["document_canonical"] = tampered["document_canonical"].replace(
                '"C"', '"X"'
            )
            rejected = verify_inclusion_proof(tampered)
            self.assertFalse(rejected["ok"])
            self.assertIn("document hash does not match leaf", rejected["errors"])

    def test_site_publish_writes_receipt_page_and_index_link(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            site = root / "_site"
            downloads = site / "downloads"
            downloads.mkdir(parents=True)
            corpus = downloads / "starintel-complete-corpus.jsonl"
            write_corpus(corpus, [document("starintel:claim:a", title="A")])
            (site / "index.html").write_text(
                "<!doctype html><html><body><main><h1>Auto-Dig</h1></main></body></html>",
                encoding="utf-8",
            )

            receipt = publish_site_seal(corpus, site)
            receipt_path = downloads / "starintel-evidence-seal.json"
            page_path = site / "evidence-seal.html"
            self.assertTrue(receipt_path.is_file())
            self.assertTrue(page_path.is_file())
            self.assertEqual(json.loads(receipt_path.read_text()), receipt)
            self.assertIn(receipt["merkle_root_sha256"], page_path.read_text())
            index = (site / "index.html").read_text()
            self.assertIn("data-evidence-seal", index)
            self.assertIn("evidence-seal.html", index)

    def test_command_line_create_verify_prove_and_verify_proof(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            corpus = root / "corpus.jsonl"
            receipt = root / "seal.json"
            proof = root / "proof.json"
            write_corpus(corpus, [document("starintel:claim:a", title="A")])
            script = Path(__file__).resolve().parents[1] / "scripts" / "evidence-seal.py"

            subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "create",
                    str(corpus),
                    "--output",
                    str(receipt),
                ],
                check=True,
            )
            subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "verify",
                    str(corpus),
                    str(receipt),
                ],
                check=True,
            )
            subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "prove",
                    str(corpus),
                    "starintel:claim:a",
                    "--receipt",
                    str(receipt),
                    "--output",
                    str(proof),
                ],
                check=True,
            )
            subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "verify-proof",
                    str(proof),
                    "--receipt",
                    str(receipt),
                ],
                check=True,
            )


if __name__ == "__main__":
    unittest.main()
