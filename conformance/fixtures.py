from __future__ import annotations

from copy import deepcopy
from typing import Any

from starintel_doc.spec import SCHEMA_VERSION, TYPE_FIELDS

FIXED_UTC = "2026-01-02T03:04:05Z"
FIXED_OFFSET = "2026-01-01T22:04:05-05:00"
DATASET = "conformance-v0.9.0"


def base_document(dtype: str, index: int, data: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "_id": f"starintel:{dtype}:fixture-{index:03d}",
        "dataset": DATASET,
        "dtype": dtype,
        "schema_version": SCHEMA_VERSION,
        "version": 1,
        "date_added": FIXED_UTC,
        "date_updated": "2026-01-02T03:04:05+00:00",
        "sources": [],
        "evidence": [],
        "data": deepcopy(data or {}),
    }


def fixture(
    fixture_id: str,
    object_type: str,
    document: dict[str, Any],
    *,
    expected_valid: bool = True,
    expected_error: str | None = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "fixture_id": fixture_id,
        "spec_version": SCHEMA_VERSION,
        "object_type": object_type,
        "expected_valid": expected_valid,
        "document": document,
    }
    if expected_error is not None:
        result["expected_error"] = expected_error
    return result


def minimal_data(dtype: str) -> dict[str, Any]:
    required = {
        "relation": {
            "subject": "starintel:person:ada",
            "predicate": "works_for",
            "object": "starintel:org:analytical-engines",
        },
        "target": {"target": "starintel:person:ada"},
        "investigation-target": {"target": "starintel:person:ada"},
        "phone": {"number": "+1-555-0100"},
        "email": {"address": "ada@example.test"},
        "domain": {"domain": "example.test"},
        "url": {"url": "https://example.test/a?x=1"},
        "claim": {"claim": "A documented claim."},
    }
    return deepcopy(required.get(dtype, {}))


def full_person() -> dict[str, Any]:
    document = base_document(
        "person",
        100,
        {
            "etype": "human",
            "eid": "person:ada-lovelace",
            "name": "Augusta Ada King",
            "display_name": "Ada Lovelace",
            "legal_name": "Augusta Ada King, Countess of Lovelace",
            "former_names": ["Augusta Ada Byron"],
            "description": "Mathematician\nWriter",
            "bio": "Unicode: λ, 漢字, emoji 🧠; escaped \"quote\" and backslash \\\\.",
            "jurisdiction": "GB",
            "country": "United Kingdom",
            "status": "historical",
            "website": "https://example.test/ada",
            "external_ids": [
                {
                    "scheme": "example",
                    "value": "ada-1",
                    "canonical": True,
                    "confidence": 1.0,
                }
            ],
            "contact_ids": ["starintel:email:ada"],
            "location_ids": ["starintel:location:london"],
            "fname": "Ada",
            "mname": "",
            "lname": "Lovelace",
            "suffix": "",
            "full_name": "Ada Lovelace",
            "preferred_name": "Ada",
            "gender": "female",
            "pronouns": "she/her",
            "dob": "1815-12-10T00:00:00+00:00",
            "birthplace": "London",
            "death_date": "1852-11-27T00:00:00Z",
            "nationalities": ["British"],
            "citizenships": ["United Kingdom"],
            "occupations": ["mathematician", "writer"],
            "employers": [],
            "positions": [],
            "education_ids": [],
            "social_account_ids": [],
            "email_ids": ["starintel:email:ada"],
            "phone_ids": [],
            "family_ids": [],
            "associate_ids": ["starintel:person:babbage"],
            "political_affiliations": [],
            "professional_affiliations": [],
            "public_roles": [],
            "misc": ["line 1", "line\t2"],
        },
    )
    document.update(
        {
            "title": "Ada Lovelace",
            "summary": "Full person fixture",
            "description": "Top-level description",
            "status": "verified",
            "language": "en-GB",
            "tags": ["person", "history"],
            "labels": [],
            "aliases": ["A. A. Lovelace"],
            "keywords": ["analytical engine"],
            "identifiers": [
                {
                    "scheme": "wikidata",
                    "value": "Q7259",
                    "issuer": "Wikidata",
                    "jurisdiction": "",
                    "canonical": True,
                    "confidence": 1.0,
                    "valid_from": None,
                    "valid_to": None,
                    "url": "https://www.wikidata.org/wiki/Q7259",
                    "notes": "",
                }
            ],
            "sources": [
                {
                    "source_id": "src-1",
                    "kind": "reference",
                    "type": "web",
                    "name": "Example Source",
                    "title": "Ada",
                    "publisher": "Example",
                    "author": "A. Author",
                    "organization": "Example Org",
                    "uri": "https://example.test/ada",
                    "url": "https://example.test/ada",
                    "published_at": "2025-12-31T23:59:59-05:00",
                    "retrieved_at": FIXED_UTC,
                    "accessed_at": None,
                    "language": "en",
                    "jurisdiction": "GB",
                    "medium": "web",
                    "credibility": 0.95,
                    "reliability": 0.9,
                    "authenticity": 1.0,
                    "independence": 0.8,
                    "access_method": "https",
                    "response_status": 200,
                    "content_hash": "abc123",
                    "hash_algorithm": "sha256",
                    "quote": "First line\nSecond line",
                    "locator": "p. 1",
                    "page": "1",
                    "section": "intro",
                    "metadata": {"headers": {"etag": "\"abc\""}, "attempt": 1},
                }
            ],
            "evidence": [
                {
                    "evidence_id": "ev-1",
                    "source_id": "src-1",
                    "source_url": "https://example.test/ada",
                    "kind": "excerpt",
                    "role": "supporting",
                    "claim": "Ada wrote notes.",
                    "excerpt": "A short excerpt.",
                    "collected_at": FIXED_UTC,
                    "observed_at": None,
                    "valid_from": None,
                    "valid_to": None,
                    "confidence": 0.99,
                    "corroborates": [],
                    "contradicts": [],
                    "chain_of_custody": ["fetch", "hash"],
                    "attachments": [],
                    "status": "verified",
                    "metadata": {"line": 1},
                }
            ],
            "temporal": {
                "observed_at": None,
                "collected_at": FIXED_UTC,
                "published_at": "2025-12-31T23:59:59-05:00",
                "first_seen": FIXED_OFFSET,
                "last_seen": FIXED_UTC,
                "timezone": "Europe/London",
                "precision": "second",
                "duration_seconds": 0.0,
                "sequence": 1,
            },
            "provenance": {
                "collector": "conformance",
                "collector_type": "test",
                "agent": "python",
                "tool": "fixture-generator",
                "run_id": "run-1",
                "method": "generated",
                "pipeline": "conformance",
                "software_version": SCHEMA_VERSION,
                "environment": "test",
                "created_by": "suite",
                "updated_by": "suite",
                "metadata": {"nested": {"depth": {"value": 42}}},
            },
            "assessment": {
                "confidence": 1.0,
                "analytic_confidence": 0.9,
                "source_reliability": 0.9,
                "information_credibility": 0.95,
                "relevance": 1.0,
                "priority": 0.5,
                "threat": 0.0,
                "impact": 0.2,
                "likelihood": 0.1,
                "severity": 0.0,
                "deception_probability": 0.0,
                "uncertainty": 0.1,
                "bias": 0.0,
                "completeness": 0.95,
                "assumptions": [],
                "inferences": [],
                "alternatives": [],
                "counterevidence": [],
                "gaps": [],
                "caveats": [],
                "criteria": {"a": True},
                "scores": {"x": 0.5},
            },
            "verification": {
                "status": "verified",
                "result": "pass",
                "verified": True,
                "verified_by": ["fixture-suite"],
                "verified_at": FIXED_UTC,
                "methods": ["schema"],
                "checks": ["roundtrip"],
                "conflicts": [],
                "unresolved": [],
                "last_reviewed_at": FIXED_UTC,
                "review_due_at": None,
                "review_count": 1,
            },
            "handling": {
                "visibility": "public",
                "handling": "standard",
                "classification": "unclassified",
                "dissemination": [],
                "access_groups": [],
                "caveats": [],
                "retention": "indefinite",
                "embargo_until": None,
                "pii": False,
                "sensitive": False,
                "redactions": [],
                "license": "CC0",
            },
            "lineage": {
                "parent_ids": [],
                "child_ids": [],
                "derived_from": ["starintel:source:example"],
                "source_document_ids": [],
                "supersedes": [],
                "superseded_by": [],
                "merged_from": [],
                "split_from": [],
                "duplicates": [],
                "replaces": [],
                "migration_notes": [],
                "transform": "generated",
                "generation": 0,
            },
            "quality": {
                "completeness": 1.0,
                "consistency": 1.0,
                "timeliness": 1.0,
                "uniqueness": 1.0,
                "accuracy": 1.0,
                "coverage": 1.0,
                "freshness": 1.0,
                "validation_status": "valid",
                "validation_errors": [],
                "warnings": [],
                "missing_fields": [],
                "last_validated_at": FIXED_UTC,
                "validator": "conformance",
            },
            "workflow": {
                "research_status": "complete",
                "priority": 1.0,
                "assigned_to": [],
                "requested_by": "suite",
                "due_at": None,
                "blockers": [],
                "run_id": "run-1",
                "recursion_depth": 0,
                "max_depth": 3,
                "selected_from": [],
                "selection_reason": [],
                "selection_score": 1.0,
                "selection_features": {"score": 1.0},
                "completed_at": FIXED_UTC,
            },
            "geospatial": {
                "lat": 51.5074,
                "lon": -0.1278,
                "long": -0.1278,
                "altitude": 15.5,
                "accuracy_meters": 10.0,
                "bbox": [-0.2, 51.4, -0.1, 51.6],
                "geohash": "gcpvj",
                "coordinate_system": "EPSG:4326",
                "place_name": "London",
                "city": "London",
                "region": "England",
                "country": "United Kingdom",
                "country_code": "GB",
                "timezone": "Europe/London",
                "jurisdiction": "GB",
            },
            "attachments": [
                {
                    "attachment_id": "att-1",
                    "name": "ada.txt",
                    "role": "evidence",
                    "media_type": "text/plain",
                    "uri": "https://example.test/ada.txt",
                    "size_bytes": 9007199254740991,
                    "content_hash": "0123",
                    "hash_algorithm": "sha256",
                    "captured_at": FIXED_UTC,
                    "created_at": FIXED_UTC,
                    "metadata": {"encoding": "utf-8"},
                }
            ],
            "related_ids": ["starintel:org:analytical-engines"],
            "notes": ["Unicode preserved: café"],
            "extensions": {
                "example.test": {
                    "large_integer": 9007199254740991,
                    "float": 1.25,
                    "empty_object": {},
                    "empty_array": [],
                    "null": None,
                    "deep": {"a": {"b": {"c": {"d": "value"}}}},
                }
            },
        }
    )
    return document


def invalid_fixtures(person: dict[str, Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []

    def add(name: str, document: dict[str, Any], error: str, object_type: str = "person") -> None:
        result.append(
            fixture(
                name,
                object_type,
                document,
                expected_valid=False,
                expected_error=error,
            )
        )

    document = base_document("person", 200)
    del document["_id"]
    add("person.missing-id.v1", document, "missing_required_field")

    document = base_document("person", 201)
    document["schema_version"] = "0.8.0"
    add("person.unsupported-version.v1", document, "unsupported_spec_version")

    document = base_document("person", 202)
    document["dtype"] = "organization"
    add("person.alias-not-canonical.v1", document, "invalid_enum", "organization")

    document = base_document("person", 203)
    document["invented"] = True
    add("person.extra-top-level.v1", document, "undeclared_field")

    document = base_document("person", 204)
    document["data"]["invented"] = True
    add("person.extra-data-field.v1", document, "undeclared_field")

    document = base_document("person", 205)
    document["version"] = "1"
    add("person.version-string.v1", document, "wrong_type")

    document = base_document("person", 206)
    document["version"] = True
    add("person.boolean-as-integer.v1", document, "wrong_type")

    document = base_document("person", 207)
    document["date_added"] = "not-a-date"
    add("person.bad-date.v1", document, "invalid_datetime")

    document = base_document("person", 208)
    document["_id"] = "bad/id"
    add("person.bad-id.v1", document, "pattern_mismatch")

    document = base_document("relation", 209, {"subject": "a", "object": "b"})
    add("relation.missing-predicate.v1", document, "missing_required_field", "relation")

    document = base_document("person", 210)
    document["sources"] = None
    add("person.null-sources.v1", document, "wrong_type")

    document = base_document("person", 211)
    document["sources"] = ["https://example.test"]
    add("person.source-string.v1", document, "wrong_type")

    document = base_document("person", 212)
    document["data"]["fname"] = 1
    add("person.fname-number.v1", document, "wrong_type")

    document = deepcopy(person)
    document["assessment"]["confidence"] = 1.1
    add("person.score-too-high.v1", document, "above_maximum")

    document = deepcopy(person)
    document["assessment"]["confidence"] = -0.1
    add("person.score-too-low.v1", document, "below_minimum")

    document = deepcopy(person)
    document["data"]["nationalities"] = ["British", 2]
    add("person.array-item-type.v1", document, "wrong_type")

    document = base_document("unknown", 213)
    add("document.unknown-dtype.v1", document, "unknown_object_type", "unknown")

    document = base_document(
        "relation",
        214,
        {"subject": None, "predicate": "x", "object": "b"},
    )
    add("relation.null-subject.v1", document, "wrong_type", "relation")

    document = base_document("person", 215)
    document["data"] = []
    add("person.data-array.v1", document, "wrong_type")

    document = base_document("person", 216)
    document["version"] = 0
    add("person.version-zero.v1", document, "below_minimum")
    return result


def all_fixtures() -> list[dict[str, Any]]:
    values = [
        fixture(
            f"{dtype}.minimal.v1",
            dtype,
            base_document(dtype, index, minimal_data(dtype)),
        )
        for index, dtype in enumerate(sorted(TYPE_FIELDS), 1)
    ]

    person = full_person()
    values.append(fixture("person.full.v1", "person", person))
    values.append(
        fixture(
            "relation.full.v1",
            "relation",
            base_document(
                "relation",
                101,
                {
                    "subject": {
                        "id": "starintel:person:ada",
                        "dtype": "person",
                        "label": "Ada",
                        "role": "employee",
                        "unresolved": False,
                        "external_ids": [],
                        "aliases": [],
                        "qualifiers": {"since": "1842"},
                        "metadata": {},
                    },
                    "predicate": "works_for",
                    "object": {
                        "id": "starintel:org:analytical-engines",
                        "dtype": "org",
                        "label": "Analytical Engines",
                        "role": "employer",
                        "unresolved": False,
                        "external_ids": [],
                        "aliases": [],
                        "qualifiers": {},
                        "metadata": {},
                    },
                    "source": "starintel:person:ada",
                    "target": "starintel:org:analytical-engines",
                    "directed": True,
                    "inverse_predicate": "employs",
                    "relation_type": "employment",
                    "qualifiers": {"rank": 1},
                    "weight": 1.0,
                    "confidence": 0.99,
                    "start_at": "1842-01-01T00:00:00Z",
                    "end_at": None,
                    "active": False,
                    "note": "Distinct endpoint objects.",
                },
            ),
        )
    )
    values.append(
        fixture(
            "event.full.v1",
            "event",
            base_document(
                "event",
                102,
                {
                    "event_kind": "meeting",
                    "name": "Conformance Summit",
                    "description": "Timezone offset test",
                    "participant_ids": ["starintel:person:ada"],
                    "participants": ["Ada"],
                    "organizer_ids": ["starintel:org:analytical-engines"],
                    "sponsor_ids": [],
                    "location_ids": ["starintel:location:london"],
                    "start_at": "2026-01-02T10:00:00-05:00",
                    "end_at": "2026-01-02T16:00:00Z",
                    "status": "scheduled",
                    "outcome": "",
                    "agenda": ["JSON"],
                    "decisions": [],
                    "actions": [],
                    "amount": 0.0,
                    "currency": "USD",
                    "jurisdiction": "US-OH",
                    "case_id": "",
                    "contract_id": "",
                    "meeting_id": "meeting-1",
                },
            ),
        )
    )
    values.append(
        fixture(
            "source.full.v1",
            "source",
            base_document(
                "source",
                103,
                {
                    "source_id": "src-1",
                    "kind": "web",
                    "type": "article",
                    "sensor": "http",
                    "name": "Example",
                    "title": "Escapes \" and \\\\ ",
                    "publisher": "Example",
                    "author": "A",
                    "organization": "O",
                    "uri": "https://example.test",
                    "url": "https://example.test",
                    "published_at": "2026-01-01T23:00:00-04:00",
                    "retrieved_at": FIXED_UTC,
                    "accessed_at": None,
                    "language": "en",
                    "jurisdiction": "US",
                    "medium": "web",
                    "credibility": 0.5,
                    "reliability": 0.5,
                    "authenticity": 0.5,
                    "independence": 0.5,
                    "access_method": "GET",
                    "response_status": 200,
                    "quote": "line1\nline2\tend",
                    "metadata": {"unicode": "Привет"},
                },
            ),
        )
    )
    values.append(
        fixture(
            "actor-manifest.full.v1",
            "actor-manifest",
            base_document(
                "actor-manifest",
                104,
                {
                    "manifest_type": "actor",
                    "name": "Test Actor",
                    "actor": "starintel.actor.test",
                    "consumer_path": "queue.test",
                    "target_options": [{"key": "depth", "value": 3}],
                    "document_ids": [],
                    "counts_by_dtype": {"person": 1},
                    "record_count": 1,
                    "hash_algorithm": "sha256",
                    "content_hash": "abc",
                    "files": [{"path": "actor.json"}],
                    "schema_versions": [SCHEMA_VERSION],
                    "generated_at": FIXED_UTC,
                },
            ),
        )
    )
    values.append(
        fixture(
            "dataset-manifest.full.v1",
            "dataset-manifest",
            base_document(
                "dataset-manifest",
                105,
                {
                    "manifest_type": "dataset",
                    "name": "Fixture Dataset",
                    "target_options": [],
                    "document_ids": ["starintel:person:ada"],
                    "counts_by_dtype": {"person": 1, "org": 1},
                    "record_count": 2,
                    "hash_algorithm": "sha256",
                    "content_hash": "def",
                    "files": [{"path": "fixtures.json", "size": 123}],
                    "schema_versions": [SCHEMA_VERSION],
                    "generated_at": FIXED_UTC,
                },
            ),
        )
    )

    duplicate_a = base_document("person", 106, {"fname": "Alex", "lname": "Smith"})
    duplicate_b = deepcopy(duplicate_a)
    duplicate_b["_id"] = "starintel:person:fixture-107"
    duplicate_b["data"]["eid"] = "distinct-2"
    values.append(fixture("person.duplicate-looking-a.v1", "person", duplicate_a))
    values.append(fixture("person.duplicate-looking-b.v1", "person", duplicate_b))
    values.extend(invalid_fixtures(person))
    return values


def fixture_payload() -> dict[str, Any]:
    return {
        "fixture_format_version": 1,
        "spec_version": SCHEMA_VERSION,
        "fixtures": all_fixtures(),
    }
