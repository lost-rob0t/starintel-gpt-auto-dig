from __future__ import annotations

import unittest

from starintel_doc.model import empty_document
from starintel_doc.validation import ValidationError, validate_document


class LegacySourceValidationTests(unittest.TestCase):
    def test_normalizes_file_format_to_medium(self) -> None:
        document = empty_document("source", "test", "starintel:source:legacy-file-format")
        document["title"] = "Legacy PDF source"
        document["data"] = {
            "kind": "official_document",
            "publisher": "Example",
            "uri": "https://example.test/document.pdf",
            "file_format": "application/pdf",
        }

        validate_document(document)

        self.assertNotIn("file_format", document["data"])
        self.assertEqual(document["data"]["medium"], "application/pdf")
        self.assertIn(
            "normalized legacy source data.file_format to data.medium",
            document["lineage"]["migration_notes"],
        )

    def test_rejects_conflicting_file_format_and_medium(self) -> None:
        document = empty_document("source", "test", "starintel:source:conflicting-file-format")
        document["title"] = "Conflicting source"
        document["data"] = {
            "kind": "official_document",
            "publisher": "Example",
            "uri": "https://example.test/document.pdf",
            "file_format": "application/pdf",
            "medium": "text/html",
        }

        with self.assertRaisesRegex(ValidationError, "conflicting legacy 'file_format'"):
            validate_document(document)


if __name__ == "__main__":
    unittest.main()
