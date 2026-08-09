import std/[json, unittest]

import ../scripts/starintel_legacy


suite "StarIntel Nim legacy normalization":
  test "source file_format normalizes to medium":
    let document = %*{
      "dtype": "source",
      "data": {
        "file_format": "application/pdf"
      }
    }

    check normalizeLegacyDocument(document) == ""
    check not document["data"].hasKey("file_format")
    check document["data"]["medium"].getStr == "application/pdf"
    check document["lineage"]["migration_notes"].len == 1
    check document["lineage"]["migration_notes"][0].getStr == LegacyFileFormatNote

  test "matching canonical medium is accepted":
    let document = %*{
      "dtype": "source",
      "data": {
        "file_format": "application/pdf",
        "medium": "application/pdf"
      }
    }

    check normalizeLegacyDocument(document) == ""
    check not document["data"].hasKey("file_format")
    check document["data"]["medium"].getStr == "application/pdf"

  test "conflicting canonical medium is rejected":
    let document = %*{
      "dtype": "source",
      "data": {
        "file_format": "application/pdf",
        "medium": "text/html"
      }
    }

    check normalizeLegacyDocument(document) ==
      "$.data: conflicting legacy 'file_format' and canonical 'medium' values"
    check document["data"].hasKey("file_format")
    check document["data"]["medium"].getStr == "text/html"

  test "non-source documents are untouched":
    let document = %*{
      "dtype": "org",
      "data": {
        "file_format": "application/pdf"
      }
    }

    check normalizeLegacyDocument(document) == ""
    check document["data"].hasKey("file_format")
    check not document["data"].hasKey("medium")
