"""Public site projections read both wire shapes without rewriting evidence."""
from __future__ import annotations

import shutil
import os
import json
import sys
import subprocess
import tempfile
import unittest
from pathlib import Path

from starintel_canonical import validate_document


class NimSiteContractTests(unittest.TestCase):
    def test_historical_public_handling_annotations_are_not_access_restrictions(self):
        repo = Path(__file__).resolve().parents[1]
        markers = ["public-source-only", "public-source only", "public-source-research",
                   "public-source-research-no-credentials", "verified-source-evidence",
                   "verified-source-artifact"]
        base = {"dataset": "handling", "dtype": "org", "schema_version": "0.9.0",
                "title": "Public institutional record", "sources": []}
        policy = {"visibility": "public", "pii": True, "sensitive": False,
                  "classification": "unclassified", "notes": "Public records only",
                  "caveats": ["No unpublished details collected"],
                  "redactions": ["Private details omitted"]}
        public = [{**base, "_id": f"public:{i}", "handling": {**policy, "handling": marker},
                   "extensions": {"receipt": {"handling": policy}}}
                  for i, marker in enumerate(markers)]
        restricted = [
            {**base, "_id": "blocked:internal", "handling": {**policy, "visibility": "internal"}},
            {**base, "_id": "blocked:ambiguous-sensitive", "handling": {
                "visibility": "public", "handling": "verified-source-evidence", "sensitive": True}},
            {**base, "_id": "blocked:classified", "handling": {**policy, "classification": "confidential"}},
            {**base, "_id": "blocked:acl", "accessControl": {"allow": ["team"]}},
            {**base, "_id": "blocked:unknown", "handling": {"visibility": "public", "unrecognized": True}},
        ]
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            packet = root / "digs/handling/run"
            packet.mkdir(parents=True)
            (packet / "starintel-documents.jsonl").write_text(
                "".join(json.dumps(row) + "\n" for row in public + restricted))
            subprocess.run([
                str(repo / "bin/starintel-site"), "--input", str(root / "digs"),
                "--db", str(root / "db"), "--output", str(root / "site"),
                "--bulk-output", str(root / "bulk"), "--org-output", str(root / "org"),
                "--topics", str(root / "no-topics"), "--config", str(root / "no-config"),
                "--assets", str(root / "no-assets"),
            ], check=True, capture_output=True, text=True)
            corpus = [json.loads(row) for row in
                      (root / "bulk/starintel-complete-corpus.jsonl").read_text().splitlines()]
            self.assertCountEqual(corpus, public)

    def test_flat_url_and_exact_id_overlay_preserve_existing_topics(self):
        repo = Path(__file__).resolve().parents[1]
        base = {"dataset": "anarchist-violence", "dtype": "url", "schemaVersion": "0.10.1",
                "visibility": "public", "sensitivity": "public", "createdAt": 0,
                "updatedAt": 1767225600, "url": "https://example.invalid/election",
                "sourceUrls": ["https://example.invalid/election"], "sources": []}
        records = [
            {**base, "id": "case:Direct", "dataset": "dedicated", "contentTitle": "Direct source"},
            {**base, "id": "case:Term", "contentTitle": "Ohio election source"},
            {**base, "id": "case:Fallback", "contentTitle": "Selected source"},
            {**base, "id": "case:Other", "contentTitle": "Unrelated source"},
            {**base, "id": "case:direct", "contentTitle": "Case-sensitive nonmatch"},
        ]
        undated = {**base, "id": "case:Undated", "dataset": "undated", "contentTitle": "Undated source"}
        del undated["createdAt"]
        del undated["updatedAt"]
        records.append(undated)
        for document in records:
            validate_document(document)
        topics = {"topics": [
            {"id": "dedicated", "match": {"datasets": ["dedicated"]}},
            {"id": "ohio", "match": {"terms": ["ohio"]}},
            {"id": "election26", "match": {"ids": [row["id"] for row in records[:3]]}},
        ]}
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            packet = root / "digs/mixed/run"
            packet.mkdir(parents=True)
            (packet / "starintel-documents.jsonl").write_text(
                "".join(json.dumps(row) + "\n" for row in records))
            (root / "topics.json").write_text(json.dumps(topics))
            subprocess.run([
                str(repo / "bin/starintel-site"), "--input", str(root / "digs"),
                "--db", str(root / "db"), "--output", str(root / "site"),
                "--bulk-output", str(root / "bulk"), "--org-output", str(root / "org"),
                "--topics", str(root / "topics.json"), "--config", str(root / "no-config"),
                "--assets", str(root / "no-assets"),
            ], check=True, capture_output=True, text=True)
            subprocess.run([sys.executable, "scripts/externalize_search_indexes.py", "--site",
                            str(root / "site"), "--transport", "pages-static"],
                           cwd=repo, check=True, capture_output=True, text=True)
            subprocess.run([sys.executable, "scripts/prepare_pages_data.py", "--site",
                            str(root / "site"), "--bulk", str(root / "bulk")],
                           cwd=repo, check=True, capture_output=True, text=True)
            def members(topic):
                return set((root / f"bulk/memberships/topic-{topic}.ids").read_text().splitlines())
            self.assertEqual(members("election26"), {row["id"] for row in records[:3]})
            self.assertEqual(members("dedicated"), {"case:Direct"})
            self.assertEqual(members("ohio"), {"case:Term"})
            self.assertEqual(members("mixed"), {"case:Fallback", "case:Other", "case:direct", "case:Undated"})
            corpus = [json.loads(row) for row in
                      (root / "bulk/starintel-complete-corpus.jsonl").read_text().splitlines()]
            self.assertCountEqual(corpus, records)
            dashboard = json.loads((root / "site/dashboard-data.json").read_text())
            self.assertEqual(dashboard["summary"]["documents"], 6)
            self.assertEqual(dashboard["summary"]["sources"], 1)
            search_index = json.loads((root / "site/search-index.json").read_text())
            metadata = [json.loads((root / "site" / page["url"]).read_text())
                        for page in search_index["records"]["pages"]]
            self.assertIn("Ohio election source", json.dumps(metadata))
            self.assertIn("https://example.invalid/election",
                          (root / "site/mixed/sources.html").read_text())

    @unittest.skipUnless(os.name == "posix", "POSIX signal status")
    def test_wrapper_preserves_child_exit_status(self):
        repo = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            shutil.copy2(repo / "bin/starintel-site", root / "starintel-site")
            core = root / "starintel-site-core"
            for command, expected in [("exit 7", 7), ("exit 137", 137), ("kill -KILL $$", 137)]:
                with self.subTest(command=command):
                    core.write_text("#!/bin/sh\n" + command + "\n")
                    core.chmod(0o755)
                    result = subprocess.run([str(root / "starintel-site"), "--help"],
                                            capture_output=True, text=True)
                    self.assertEqual(result.returncode, expected)
                    self.assertIn(f"core failed with exit status {expected}", result.stderr)

    def test_entry_does_not_resurrect_restricted_duplicate(self):
        repo = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            shutil.copy2(repo / "bin/starintel-site", root / "starintel-site")
            core = root / "starintel-site-core"
            core.write_text("#!/bin/sh\nexit 0\n")
            core.chmod(0o755)
            (root / "site").mkdir()
            (root / "bulk").mkdir()
            public = {"id": "starintel:person:revoked", "dtype": "person", "dataset": "test",
                      "schemaVersion": "0.10.1", "visibility": "public", "sensitivity": "public"}
            validate_document(public)
            private = {**public, "visibility": "private"}
            for rows in ([public, private], [private, public]):
                (root / "bulk/starintel-complete-corpus.jsonl").write_text(
                    "".join(json.dumps(row) + "\n" for row in rows))
                subprocess.run([str(root / "starintel-site"), "--output", str(root / "site"),
                                "--bulk-output", str(root / "bulk")], check=True, capture_output=True)
                data = json.loads((root / "site/dashboard-data.json").read_text())
                self.assertEqual(data["summary"]["documents"], 0)
                self.assertNotIn(public["id"], json.dumps(data))

    def test_mixed_wire_shapes_and_restrictive_metadata(self):
        repo = Path(__file__).resolve().parents[1]
        native = {
            "id": "starintel:person:native", "dataset": "mixed", "dtype": "person",
            "schemaVersion": "0.10.1", "fullName": "Native Person",
            "createdAt": 0, "updatedAt": 1767225600,
            "visibility": "public", "sensitivity": "public",
            "verificationStatus": "reviewed",
            "sources": [{"schema": "source", "id": "starintel:source:evidence"}],
        }
        legacy = {
            "_id": "starintel:person:legacy", "dataset": "mixed", "dtype": "person",
            "schema_version": "0.9.0", "title": "Historical Person",
            "date_added": "2025-01-01T00:00:00Z", "date_updated": "2025-02-01T00:00:00Z",
            "status": "reviewed", "sources": ["https://example.invalid/evidence"],
            "assessment": {"caveats": ["Evidence caveats must not be read as access restrictions."]},
            "handling": {"handling": "public-source-only", "visibility": "public", "pii": True, "sensitive": False},
            "extensions": {"legacy": {"v0": {"original_field": "Preserved migration evidence", "evidence_policy": "Primary sources first"}},
                           "compatibility": {"original_schema": "historical"}},
        }
        relation = {**native, "id": "starintel:relation:mixed", "dtype": "relation",
                    "source": {"schema": "person", "id": native["id"]},
                    "destination": {"schema": "person", "id": legacy["_id"]},
                    "predicate": "knows"}
        del relation["fullName"]
        for document in (native, relation):
            validate_document(document)
        records = [native, relation, {**legacy, "_id": native["id"], "title": "Stale public copy"}]
        blocked_ids = []
        policies = [
            {"visibility": "private"}, {"sensitivity": "unknown"},
            {"accessControl": {"allow": ["team"]}}, {"retentionPolicy": "internal-only"},
            {"deleted": True}, {"collectionStatus": "deleted"}, {"metadata": {"handling": {"restricted": True}}},
            {"extensions": {"legacy": {"handling": {"visibility": "private"}}}},
        ]
        policies += [
            {"extensions": {"handling": {"restricted": True}}},
            {"extensions": {"handling": {"restricted": "false"}}},
            {"metadata": {"Confidential": True}},
            {"metadata": {"Classified": "false"}},
            {"metadata": {"access_control": {"allow": "team"}}},
            {"extensions": {"acl": ["team"]}},
            {"extensions": {"legacy_handling": {"unknown": False}}},
        ]
        policies += [{"metadata": {key: ["restricted"]}}
                     for key in ("dissemination", "embargo")]
        for i, policy in enumerate(policies):
            doc = {**native, "id": f"starintel:person:blocked-{i}", **policy}
            records.append(doc)
            blocked_ids.append(doc["id"])
        for key in ("visibility", "sensitivity"):
            doc = {**native, "id": f"starintel:person:missing-{key}"}
            del doc[key]
            records.append(doc)
            blocked_ids.append(doc["id"])
        historical_restricted = {**legacy, "_id": "starintel:person:historical-private",
                                 "handling": {"visibility": "private"}}
        records.append(historical_restricted)
        blocked_ids.append(historical_restricted["_id"])
        # A newer restrictive observation must not resurrect its public duplicate.
        duplicate = {**native, "id": "starintel:person:revoked"}
        records += [duplicate, {**duplicate, "visibility": "private", "updatedAt": 1767312000}]
        blocked_ids.append(duplicate["id"])
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            packet = root / "digs/mixed/run"
            packet.mkdir(parents=True)
            (packet / "starintel-documents.jsonl").write_text(
                "".join(json.dumps(doc) + "\n" for doc in records))
            db = root / "db/person"
            db.mkdir(parents=True)
            (db / (legacy["_id"] + ".ndjson")).write_text(json.dumps(legacy) + "\n")
            site, bulk = root / "site", root / "bulk"
            result = subprocess.run([
                str(repo / "bin/starintel-site"), "--input", str(root / "digs"),
                "--db", str(root / "db"), "--output", str(site),
                "--bulk-output", str(bulk), "--org-output", str(root / "org"),
                "--config", str(root / "no-config"), "--topics", str(root / "no-topics"),
                "--assets", str(root / "no-assets"),
            ], cwd=repo, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            corpus = [json.loads(line) for line in (bulk / "starintel-complete-corpus.jsonl").read_text().splitlines()]
            self.assertCountEqual(corpus, [native, legacy, relation])
            dashboard = json.loads((site / "dashboard-data.json").read_text())
            self.assertEqual(dashboard["summary"]["documents"], 3)
            self.assertEqual(dashboard["summary"]["updated_through"], "2026-01-01T00:00:00Z")
            self.assertEqual(dashboard["summary"]["sources"], 2)
            self.assertIn("1970-01-01", json.dumps(dashboard["documents_by_day"]))
            manifest = json.loads((site / "downloads/starintel-complete-corpus.manifest.json").read_text())
            self.assertCountEqual(manifest["data"]["schema_versions"], ["0.9.0", "0.10.1"])
            graph = json.loads((site / "mixed/graph.json").read_text())
            self.assertIn({"source": native["id"], "target": legacy["_id"], "label": "knows",
                           "predicate": "knows", "reviewed": True}, graph["edges"])
            self.assertEqual(next(n for n in graph["nodes"] if n["id"] == native["id"])["label"], "Native Person")
            for path in [*site.rglob("*"), *bulk.rglob("*"), *(root / "org").rglob("*")]:
                if path.is_file() and path.suffix != ".gz":
                    text = path.read_text()
                    for identifier in blocked_ids:
                        self.assertNotIn(identifier, text, str(path))


if __name__ == "__main__":
    unittest.main()
