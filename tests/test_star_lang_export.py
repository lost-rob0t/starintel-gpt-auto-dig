from __future__ import annotations

import unittest

from starintel_doc.spec import REQUIRED_DATA_FIELDS, SCHEMA_VERSION, TYPE_FIELDS
from starintel_doc.star_lang import (
    LIBRARY_ID,
    camel,
    library_digest,
    render_library,
)


class StarLangExportTest(unittest.TestCase):
    def test_deterministic(self):
        self.assertEqual(render_library(), render_library())
        self.assertTrue(library_digest().startswith("sha256:"))

    def test_camel_case(self):
        self.assertEqual(camel("transaction_id"), "transactionId")
        self.assertEqual(camel("_id"), "id")
        self.assertEqual(camel("resolved_addresses"), "resolvedAddresses")

    def test_covers_every_dtype(self):
        text = render_library()
        for dtype in sorted(TYPE_FIELDS):
            self.assertIn(f"(document {dtype}", text, dtype)

    def test_required_fields_required(self):
        text = render_library()
        # http-transaction data fields are required in the wire schema and in
        # the star export.
        for required in REQUIRED_DATA_FIELDS["http-transaction"]:
            line = [l for l in text.splitlines()
                    if l.strip().startswith(f"({camel(required)} ")]
            self.assertTrue(any(":required" in l for l in line), required)

    def test_library_identity_and_version(self):
        text = render_library()
        self.assertIn(f'(spec-library "{LIBRARY_ID}"', text)
        self.assertIn(f'(:version "{SCHEMA_VERSION}")', text)
        self.assertIn("(document starintel-document", text)


if __name__ == "__main__":
    unittest.main()
