from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from starintel_doc.migration import migrate_document
from starintel_doc.model import Document
from starintel_doc.schema_org import DTYPE_SCHEMA_ORG_TYPES, SCHEMA_ORG_CONTEXT, to_schema_org
from starintel_doc.selectors import candidate_documents, select_candidates
from starintel_doc.spec import TYPE_FIELDS
from starintel_doc.store import LocatedDocument, migrate_repository, validate_repository
from starintel_doc.validation import ValidationError, validate_document


class StarIntelDocumentTests(unittest.TestCase):
    def test_create_relation(self) -> None:
        doc = Document.create(
            "relation",
            "test",
            doc_id="starintel:relation:a-related-b",
            data={
                "subject": "starintel:person:a",
                "predicate": "related_to",
                "object": "starintel:org:b",
            },
        ).to_dict()
        self.assertEqual(doc["schema_version"], "0.9.0")
        validate_document(doc)

    def test_schema_org_defaults_cover_every_dtype(self) -> None:
        self.assertEqual(set(DTYPE_SCHEMA_ORG_TYPES), set(TYPE_FIELDS))
        doc = Document.create(
            "org",
            "test",
            doc_id="starintel:org:schema-org",
            title="Schema Org",
            data={"name": "Schema Org", "org_type": "company"},
        ).to_dict()
        self.assertEqual(doc["schema_org"]["@context"], SCHEMA_ORG_CONTEXT)
        self.assertEqual(doc["schema_org"]["@type"], "Organization")
        self.assertEqual(doc["schema_org"]["@id"], doc["_id"])
        validate_document(doc)

    def test_schema_org_accepts_json_ld_metadata(self) -> None:
        doc = Document.create(
            "person",
            "test",
            doc_id="starintel:person:example",
            title="Example Person",
            aliases=["E. Person"],
            identifiers=[{"scheme": "wikidata", "value": "Q42", "url": "https://www.wikidata.org/wiki/Q42"}],
            schema_org={
                "@context": "https://schema.org/",
                "@type": ["Person", "Thing"],
                "@id": "starintel:person:example",
                "sameAs": ["https://example.test/person"],
                "additionalProperty": [
                    {"@type": "PropertyValue", "name": "source rank", "value": 1}
                ],
                "properties": {"award": "Example Award"},
            },
            data={"full_name": "Example Person"},
        ).to_dict()
        validate_document(doc)
        jsonld = to_schema_org(doc)
        self.assertEqual(jsonld["name"], "Example Person")
        self.assertEqual(jsonld["sameAs"], ["https://example.test/person"])
        self.assertEqual(jsonld["identifier"][0]["propertyID"], "wikidata")

    def test_schema_org_rejects_undeclared_direct_field(self) -> None:
        doc = Document.create("org", "test", doc_id="starintel:org:a", data={"name": "A"}).to_dict()
        doc["schema_org"]["invented"] = True
        with self.assertRaises(ValidationError):
            validate_document(doc)

    def test_rejects_undeclared_top_level_field(self) -> None:
        doc = Document.create("org", "test", doc_id="starintel:org:a", data={"name": "A"}).to_dict()
        doc["invented"] = True
        with self.assertRaises(ValidationError):
            validate_document(doc)

    def test_rejects_undeclared_type_field(self) -> None:
        doc = Document.create("org", "test", doc_id="starintel:org:a", data={"name": "A"}).to_dict()
        doc["data"]["invented"] = True
        with self.assertRaises(ValidationError):
            validate_document(doc)

    def test_migrates_v082_relation(self) -> None:
        legacy = {
            "_id": "starintel:relation:a-b",
            "dataset": "legacy",
            "dtype": "relation",
            "version": "0.8.0",
            "sources": ["https://example.test"],
            "date_added": 1700000000,
            "date_updated": 1700000001,
            "source": "starintel:person:a",
            "target": "starintel:org:b",
            "predicate": "founded",
            "note": "recorded relation",
        }
        migrated = migrate_document(legacy)
        self.assertEqual(migrated["data"]["subject"], "starintel:person:a")
        self.assertEqual(migrated["data"]["object"], "starintel:org:b")
        self.assertEqual(migrated["sources"][0]["url"], "https://example.test")
        self.assertEqual(migrated["schema_org"]["@type"], "Role")
        validate_document(migrated)

    def test_creates_unresolved_relation_endpoint(self) -> None:
        doc = Document.create(
            "relation",
            "test",
            doc_id="starintel:relation:unresolved-direct",
            data={
                "subject": {"label": "Unknown intermediary", "unresolved": True},
                "predicate": "related_to",
                "object": "starintel:org:example",
            },
        )
        self.assertTrue(doc.to_dict()["data"]["subject"]["unresolved"])
        validate_document(doc.to_dict())

    def test_migrates_relation_entity_id_endpoint(self) -> None:
        legacy = {
            "_id": "starintel:relation:embedded-a-b",
            "dataset": "legacy",
            "dtype": "relation",
            "version": "0.8.0",
            "sources": [],
            "date_added": 1700000000,
            "date_updated": 1700000001,
            "subject": {"entity_id": "starintel:person:a", "name": "A", "office": "CEO"},
            "predicate": "works_for",
            "object": {"entity_id": "starintel:org:b", "organization": "B"},
        }
        migrated = migrate_document(legacy)
        self.assertEqual(migrated["data"]["subject"]["id"], "starintel:person:a")
        self.assertEqual(migrated["data"]["subject"]["qualifiers"]["legacy"]["office"], "CEO")
        self.assertEqual(migrated["data"]["object"]["id"], "starintel:org:b")
        validate_document(migrated)

    def test_migrates_unresolved_relation_endpoint(self) -> None:
        legacy = {
            "_id": "starintel:relation:embedded-unresolved",
            "dataset": "legacy",
            "dtype": "relation",
            "version": "0.8.0",
            "sources": [],
            "date_added": 1700000000,
            "date_updated": 1700000001,
            "subject": {"name": "Unknown intermediary", "role": "intermediary"},
            "predicate": "related_to",
            "object": "starintel:org:b",
        }
        migrated = migrate_document(legacy)
        self.assertTrue(migrated["data"]["subject"]["unresolved"])
        self.assertEqual(migrated["data"]["subject"]["label"], "Unknown intermediary")
        validate_document(migrated)

    def test_migrates_ad_hoc_metadata_without_loss(self) -> None:
        legacy = {
            "_id": "starintel:org:example",
            "dataset": "legacy",
            "dtype": "org",
            "schema_version": "starintel.v0.2.1",
            "version": 1,
            "date_added": "2026-07-25T14:00:00-04:00",
            "date_updated": "2026-07-25T14:00:00-04:00",
            "source": {"kind": "filing", "uri": "https://example.test", "credibility": 0.99},
            "analysis": {"threat": 0.5, "confidence": 0.9},
            "opsec": {"handling": "internal", "compartment": "X"},
            "entity": {"name": "Example Inc.", "ticker": "EX", "custom_metric": 42},
        }
        migrated = migrate_document(legacy)
        self.assertEqual(migrated["data"]["name"], "Example Inc.")
        self.assertEqual(migrated["assessment"]["confidence"], 0.9)
        self.assertEqual(migrated["extensions"]["legacy.v0"]["data"]["custom_metric"], 42)
        validate_document(migrated)

    def test_repository_migration(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "db" / "org" / "starintel:org:a.ndjson"
            path.parent.mkdir(parents=True)
            legacy = {
                "_id": "starintel:org:a",
                "dataset": "legacy",
                "dtype": "org",
                "version": "0.8.0",
                "sources": [],
                "date_added": 1700000000,
                "date_updated": 1700000001,
                "name": "A",
            }
            path.write_text(json.dumps(legacy) + "\n", encoding="utf-8")
            result = migrate_repository(root, write=True)
            self.assertEqual(result["record_count"], 1)
            validation = validate_repository(root)
            self.assertTrue(validation["ok"], validation["errors"])

    def test_recursive_selector_emits_targets(self) -> None:
        org = Document.create(
            "org",
            "test",
            doc_id="starintel:org:a",
            data={"name": "A"},
            assessment={"relevance": 0.9, "confidence": 0.9},
            sources=[{"url": "https://example.test", "kind": "filing"}],
        ).to_dict()
        claim = Document.create(
            "claim",
            "test",
            doc_id="starintel:claim:a",
            data={"claim": "A did something", "subject_ids": ["starintel:org:a"]},
        ).to_dict()
        located = [LocatedDocument(org, Path("org")), LocatedDocument(claim, Path("claim"))]
        candidates = select_candidates(located, limit=1)
        self.assertEqual(candidates[0].target_id, "starintel:org:a")
        targets = candidate_documents(candidates, dataset="targets")
        self.assertEqual(targets[0]["dtype"], "investigation-target")
        validate_document(targets[0])


if __name__ == "__main__":
    unittest.main()
