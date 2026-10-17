from __future__ import annotations

import pytest

from starintel_doc.breach import (
    build_breach_compilation,
    build_paste,
    to_jsonld,
    validate_breach_document,
)
from starintel_doc.spec_092 import TYPE_FIELDS as TYPE_FIELDS_092
from starintel_doc.spec_093 import (
    DTYPE_ALIASES,
    PROFILE_VERSION,
    SCHEMA_VERSION,
    TYPE_FIELDS,
    document_schema,
)
from starintel_doc.validation import ValidationError

NOW = "2026-09-19T02:00:00Z"


def test_profile_composes_over_network_capture_and_adds_breach_dtypes():
    assert SCHEMA_VERSION == "0.9.0"
    assert PROFILE_VERSION == "0.9.3"
    assert "http-transaction" in TYPE_FIELDS
    assert "web-capture" in TYPE_FIELDS
    assert "breach-compilation" in TYPE_FIELDS
    assert "paste" in TYPE_FIELDS
    assert DTYPE_ALIASES["breach_compilation"] == "breach-compilation"
    for dtype, fields in TYPE_FIELDS_092.items():
        expected = set(fields)
        if dtype == "breach":
            continue
        assert expected <= set(TYPE_FIELDS[dtype])


def test_breach_dtype_gains_only_additive_optional_fields():
    base_fields = set(TYPE_FIELDS_092["breach"])
    extended_fields = set(TYPE_FIELDS["breach"])
    assert base_fields <= extended_fields
    assert extended_fields - base_fields == {
        "compilation_ids",
        "corpus_entry_ref",
        "credential_classes",
        "first_observed_at",
        "corpus_record_count",
    }


def test_build_breach_compilation_creates_valid_document():
    doc = build_breach_compilation(
        dataset="breach-fixture",
        name="fixture-compilation",
        source_artifact_uri="artifact://corpora/fixture",
        fmt="email:password-sorted-tree",
        acquired_at=NOW,
        fields={
            "topology": "c1/c2/c3",
            "entry_file_count": 4,
            "record_count_estimate": 1000,
        },
    )
    assert doc["schema_version"] == "0.9.0"
    assert doc["dtype"] == "breach-compilation"
    assert doc["data"]["name"] == "fixture-compilation"
    assert doc["data"]["entry_file_count"] == 4
    assert doc["_id"].startswith("starintel:breach-compilation:")
    assert validate_breach_document(doc) == doc


def test_build_paste_is_artifact_reference_only():
    doc = build_paste(
        dataset="breach-fixture",
        paste_key="AbCd1234",
        paste_service="pastebin",
        paste_url="https://pastebin.com/raw/AbCd1234",
        fetched_at=NOW,
        fields={
            "title": "fixture paste",
            "syntax": "text",
            "size_bytes": 42,
            "watch_source": "archive",
            "content_artifact_uri": "artifact://pastes/fixture-1",
            "content_hash": "sha256:abc",
            "matched_rule_ids": ["rule:email-password-pair"],
        },
    )
    assert doc["dtype"] == "paste"
    assert doc["data"]["paste_key"] == "AbCd1234"
    assert doc["data"]["content_artifact_uri"] == "artifact://pastes/fixture-1"
    assert doc["_id"].startswith("starintel:paste:")


def test_paste_artifact_reference_requires_hash():
    doc = build_paste(
        dataset="breach-fixture",
        paste_key="AbCd1234",
        paste_service="pastebin",
        paste_url="https://pastebin.com/raw/AbCd1234",
        fetched_at=NOW,
    )
    doc["data"]["content_artifact_uri"] = "artifact://pastes/fixture-1"
    with pytest.raises(ValidationError):
        validate_breach_document(doc)


def test_breach_profile_rejects_foreign_dtype():
    doc = build_paste(
        dataset="breach-fixture",
        paste_key="AbCd1234",
        paste_service="pastebin",
        paste_url="https://pastebin.com/raw/AbCd1234",
        fetched_at=NOW,
    )
    doc["dtype"] = "person"
    with pytest.raises(ValidationError):
        validate_breach_document(doc)


def test_breach_extended_document_validates_under_profile():
    doc = build_breach_compilation(
        dataset="breach-fixture",
        name="fixture-compilation",
        source_artifact_uri="artifact://corpora/fixture",
        fmt="email:password-sorted-tree",
        acquired_at=NOW,
    )
    breach_doc = {
        "_id": "starintel:breach:fixture",
        "dataset": "breach-fixture",
        "dtype": "breach",
        "schema_version": SCHEMA_VERSION,
        "version": 1,
        "date_added": NOW,
        "date_updated": NOW,
        "sources": [],
        "evidence": [],
        "data": {
            "compilation_ids": [doc["data"]["compilation_id"]],
            "corpus_record_count": 10,
            "credential_classes": ["password"],
        },
        "extensions": {"starintel.profile": {"release_version": PROFILE_VERSION}},
    }
    validated = validate_breach_document(breach_doc)
    assert validated["data"]["corpus_record_count"] == 10
    schema = document_schema()
    assert "breach-compilation" in schema["allOf"][0]["if"]["properties"]["dtype"]["const"] or any(
        variant["if"]["properties"]["dtype"]["const"] == "breach-compilation"
        for variant in schema["allOf"]
    )


def test_to_jsonld_paste_and_compilation():
    paste = build_paste(
        dataset="breach-fixture",
        paste_key="AbCd1234",
        paste_service="pastebin",
        paste_url="https://pastebin.com/raw/AbCd1234",
        fetched_at=NOW,
    )
    jsonld = to_jsonld(paste)
    assert jsonld["@type"] == "DigitalDocument"
    assert jsonld["url"] == "https://pastebin.com/raw/AbCd1234"
    compilation = build_breach_compilation(
        dataset="breach-fixture",
        name="fixture-compilation",
        source_artifact_uri="artifact://corpora/fixture",
        fmt="email:password-sorted-tree",
        acquired_at=NOW,
    )
    assert to_jsonld(compilation)["@type"] == "Dataset"
