from __future__ import annotations

import unittest

from starintel_doc import (
    COMMON_DATA_FIELDS,
    FIELD_EXPANSIONS,
    SCHEMA_REVISION,
    TYPE_FIELDS,
    Document,
    document_schema,
    validate_document,
)
from starintel_doc.validation import ValidationError


class StarIntelV09ExpansionTests(unittest.TestCase):
    def test_every_dtype_has_an_explicit_expansion(self) -> None:
        self.assertEqual(set(FIELD_EXPANSIONS), set(TYPE_FIELDS))
        for dtype, fields in TYPE_FIELDS.items():
            with self.subTest(dtype=dtype):
                self.assertTrue(set(COMMON_DATA_FIELDS).issubset(fields))
                self.assertTrue(set(FIELD_EXPANSIONS[dtype]).issubset(fields))

    def test_generated_schema_exposes_revision_and_defs(self) -> None:
        schema = document_schema()
        self.assertEqual(schema["x-starintel-schema-revision"], SCHEMA_REVISION)
        self.assertIn("reference", schema["$defs"])
        self.assertIn("researchFinding", schema["$defs"])
        self.assertIn("schema_revision", schema["properties"])

    def test_new_documents_stamp_the_revision(self) -> None:
        document = Document.create(
            "org",
            "test",
            doc_id="starintel:org:expanded",
            data={
                "name": "Expanded Org",
                "legal_form": "corporation",
                "contract_ids": ["starintel:contract:example"],
                "facets": [
                    {
                        "facet_type": "governance",
                        "properties": {"board_model": "unitary"},
                    }
                ],
            },
        ).to_dict()
        self.assertEqual(document["schema_revision"], SCHEMA_REVISION)
        self.assertEqual(document["lineage"]["schema_revision"], SCHEMA_REVISION)
        validate_document(document)

    def test_pre_expansion_v09_document_remains_valid(self) -> None:
        document = Document.create(
            "org",
            "test",
            doc_id="starintel:org:legacy-v09",
            data={"name": "Legacy v0.9 Org"},
        ).to_dict()
        for field in (
            "schema_revision",
            "schema_uri",
            "profile",
            "profile_version",
            "object_marking_ids",
            "revoked",
            "deleted",
        ):
            document.pop(field, None)
        document["lineage"].pop("schema_revision", None)
        validate_document(document)

    def test_expansion_remains_strict(self) -> None:
        document = Document.create(
            "research-pass",
            "test",
            doc_id="starintel:research-pass:expanded",
            data={
                "research_question": "What changed?",
                "finding_records": [
                    {
                        "statement": "A schema field was added.",
                        "confidence": 1.0,
                    }
                ],
            },
        ).to_dict()
        document["data"]["invented_field"] = True
        with self.assertRaises(ValidationError):
            validate_document(document)


if __name__ == "__main__":
    unittest.main()
