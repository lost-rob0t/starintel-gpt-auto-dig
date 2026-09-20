from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from starintel_doc import spec as base_spec
from starintel_doc import spec_092
from starintel_doc.schema_org import document_schema
from starintel_doc.spec import (
    ACCEPTED_SCHEMA_VERSIONS,
    DTYPE_ALIASES,
    REQUIRED_DATA_FIELDS,
    SCHEMA_VERSION,
    TYPE_FIELDS,
)
from starintel_doc.validation import ValidationError, validate_document

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_FILE = ROOT / "schemas" / "starintel-doc-v0.10.1.schema.json"
NOW = "2026-09-19T00:00:00Z"

NEW_DTYPES = (
    "network-device",
    "pcap-capture",
    "network-conversation",
    "wireless-network",
    "wireless-station",
    "http-transaction",
    "web-capture",
)

REQUIRED_BY_DTYPE = {
    "network-device": {"device_class": "router"},
    "pcap-capture": {
        "capture_id": "cap-1",
        "file_uri": "artifact://pcap/cap-1.pcapng",
        "file_sha256": "sha256:abc",
    },
    "network-conversation": {
        "conversation_id": "conv-1",
        "capture_id": "cap-1",
        "layer": "tcp",
    },
    "wireless-network": {"bssid": "aa:bb:cc:00:00:01", "security": "wpa2-psk"},
    "wireless-station": {"mac": "aa:bb:cc:00:00:02"},
    "http-transaction": {
        "transaction_id": "txn-1",
        "method": "GET",
        "url": "https://example.test/",
        "response_status": 200,
    },
    "web-capture": {
        "capture_id": "webcap-1",
        "url": "https://example.test/",
        "screenshot_uri": "artifact://screens/1.png",
        "screenshot_hash": "sha256:abc",
    },
}


def make_doc(dtype: str, data: dict, schema_version: str = SCHEMA_VERSION) -> dict:
    return {
        "_id": f"starintel:{dtype}:spec-0101",
        "dataset": "spec-0101",
        "dtype": dtype,
        "schema_version": schema_version,
        "version": 1,
        "date_added": NOW,
        "date_updated": NOW,
        "sources": [],
        "evidence": [],
        "data": data,
    }


class TestNewDtypes:
    def test_new_dtypes_are_registered_with_aliases(self) -> None:
        for dtype in NEW_DTYPES:
            assert dtype in TYPE_FIELDS
        assert DTYPE_ALIASES["network_device"] == "network-device"
        assert DTYPE_ALIASES["http_transaction"] == "http-transaction"
        assert DTYPE_ALIASES["web_capture"] == "web-capture"

    def test_required_fields_are_enforced(self) -> None:
        for dtype, data in REQUIRED_BY_DTYPE.items():
            doc = make_doc(dtype, dict(data))
            validate_document(doc)
            for field in data:
                bad = copy.deepcopy(doc)
                del bad["data"][field]
                with pytest.raises(ValidationError, match="missing required field"):
                    validate_document(bad)

    def test_enum_rejections(self) -> None:
        cases = [
            ("network-device", {"device_class": "space-station"}),
            ("network-device", {"device_class": "router", "hardware_class": "hyperspace"}),
            ("pcap-capture", {**REQUIRED_BY_DTYPE["pcap-capture"], "format": "snoop"}),
            ("network-conversation", {**REQUIRED_BY_DTYPE["network-conversation"], "layer": "sctp"}),
            ("wireless-network", {"bssid": "aa:bb:cc:00:00:01", "security": "wpa4-psk"}),
            ("wireless-network", {"bssid": "aa:bb:cc:00:00:01", "security": "wep", "band": "60ghz"}),
            ("wireless-station", {"mac": "aa:bb:cc:00:00:02", "station_type": "satellite"}),
        ]
        for dtype, data in cases:
            with pytest.raises(ValidationError, match="expected one of"):
                validate_document(make_doc(dtype, data))

    def test_conversation_endpoints_and_capture_shapes_are_typed(self) -> None:
        doc = make_doc(
            "network-conversation",
            {
                **REQUIRED_BY_DTYPE["network-conversation"],
                "a_endpoint": {"ipv4": "10.0.0.1", "port": 443},
                "b_endpoint": {"mac": "aa:bb:cc:00:00:03"},
                "protocols": ["eth", "ethertype:ipv4", "tcp", "http"],
            },
        )
        validate_document(doc)
        bad = copy.deepcopy(doc)
        bad["data"]["a_endpoint"]["hostname"] = "not-a-field"
        with pytest.raises(ValidationError, match="undeclared field"):
            validate_document(bad)

        pcap = make_doc(
            "pcap-capture",
            {
                **REQUIRED_BY_DTYPE["pcap-capture"],
                "format": "pcapng",
                "interfaces": [{"name": "eth0", "iftype": 6, "mac": "aa:bb:cc:00:00:04", "snaplen": 262144}],
                "protocol_hierarchy": [{"protocol": "tcp", "frames": 10, "bytes": 800, "pct_frames": 1.0, "pct_bytes": 1.0}],
            },
        )
        validate_document(pcap)
        bad_pcap = copy.deepcopy(pcap)
        bad_pcap["data"]["interfaces"][0]["link_type"] = 1
        with pytest.raises(ValidationError, match="undeclared field"):
            validate_document(bad_pcap)

    def test_wireless_fields_roundtrip(self) -> None:
        doc = make_doc(
            "wireless-network",
            {
                "bssid": "aa:bb:cc:00:00:01",
                "security": "wpa3-psk",
                "ssid": "example",
                "band": "5ghz",
                "channel": 36,
                "frequency_mhz": 5180,
                "signal_dbm": -67,
                "latitude": 1.0,
                "longitude": 2.0,
                "location_accuracy_m": 15.0,
                "observations": 3,
                "client_count": 1,
                "first_seen": NOW,
                "last_seen": NOW,
                "source_network_id": "wigle:EXAMPLE",
                "vendor": "Example OUI",
                "qos": 4,
            },
        )
        validate_document(doc)
        station = make_doc(
            "wireless-station",
            {
                "mac": "aa:bb:cc:00:00:02",
                "station_type": "station",
                "probe_ssids": ["example", "hidden"],
                "packets": 42,
                "data_bytes": 4096,
                "source_device_id": "kismet:abc",
            },
        )
        validate_document(station)


class TestSchemaVersionMigration:
    def test_emitters_write_current_version(self) -> None:
        assert SCHEMA_VERSION == "0.10.1"
        assert ACCEPTED_SCHEMA_VERSIONS == {"0.9.0", "0.10.1"}

    def test_validators_accept_both_versions(self) -> None:
        for version in ("0.9.0", "0.10.1"):
            validate_document(make_doc("domain", {"domain": "example.test"}, version))

    def test_validators_reject_unknown_versions(self) -> None:
        with pytest.raises(ValidationError, match=r"\$\.schema_version"):
            validate_document(make_doc("domain", {"domain": "example.test"}, "0.11.0"))

    def test_spec_092_stays_a_strict_0_9_profile(self) -> None:
        assert spec_092.SCHEMA_VERSION == "0.9.0"
        assert spec_092.RELEASE_VERSION == "0.9.2"
        legacy = make_doc("http-transaction", dict(REQUIRED_BY_DTYPE["http-transaction"]), "0.9.0")
        from starintel_doc.validation import validate_value

        validate_value(legacy, spec_092.document_schema("http-transaction"))
        migrated = copy.deepcopy(legacy)
        migrated["schema_version"] = "0.10.1"
        with pytest.raises(ValidationError):
            validate_value(migrated, spec_092.document_schema("http-transaction"))


class TestUnify:
    def test_folded_capture_fields_match_spec_092(self) -> None:
        from starintel_doc.spec import ABSORBED_COMMON_DATA_FIELDS

        assert TYPE_FIELDS["http-transaction"] == {
            **ABSORBED_COMMON_DATA_FIELDS,
            **spec_092.HTTP_TRANSACTION_FIELDS,
        }
        assert TYPE_FIELDS["web-capture"] == {
            **ABSORBED_COMMON_DATA_FIELDS,
            **spec_092.WEB_CAPTURE_FIELDS,
        }
        assert REQUIRED_DATA_FIELDS["http-transaction"] == spec_092.REQUIRED_DATA_FIELDS["http-transaction"]
        assert REQUIRED_DATA_FIELDS["web-capture"] == spec_092.REQUIRED_DATA_FIELDS["web-capture"]

    def test_absorbed_vocabulary_is_wire_typed(self) -> None:
        assert TYPE_FIELDS["org"]["legal_form"] == base_spec.STR
        assert TYPE_FIELDS["network"]["announced_by_asns"] == {"type": "array", "items": {"type": "integer"}}
        assert TYPE_FIELDS["host"]["interface_records"] == {"type": "array", "items": {"type": "object", "additionalProperties": True}}
        assert TYPE_FIELDS["url"]["http_exchanges"] == {"type": "array", "items": {"type": "object", "additionalProperties": True}}
        assert "dns_records" in TYPE_FIELDS["domain"]

    def test_identifier_arrays_require_identifier_records(self) -> None:
        doc = make_doc(
            "entity",
            {"name": "Example", "identity_keys": [{"scheme": "lei", "value": "1234"}]},
        )
        validate_document(doc)
        bad = copy.deepcopy(doc)
        bad["data"]["identity_keys"] = ["just-a-string"]
        with pytest.raises(ValidationError):
            validate_document(bad)

    def test_dropped_expansion_names_stay_rejected(self) -> None:
        with pytest.raises(ValidationError, match="undeclared field"):
            validate_document(make_doc("domain", {"domain": "example.test", "dns_record_entries": []}))
        with pytest.raises(ValidationError, match="undeclared field"):
            validate_document(
                make_doc("social-media-post", {"content": "hi", "quoted_post_id": "x"})
            )
        with pytest.raises(ValidationError, match="undeclared field"):
            validate_document(make_doc("url", {"url": "https://example.test/", "facets": []}))

    def test_common_absorbed_data_fields_apply_everywhere(self) -> None:
        doc = make_doc(
            "network-device",
            {"device_class": "switch", "description": "core switch", "status": "observed",
             "valid_from": NOW, "valid_to": None},
        )
        validate_document(doc)


class TestBreachDataLeak:
    def test_breach_requires_name(self) -> None:
        with pytest.raises(ValidationError, match="missing required field"):
            validate_document(make_doc("breach", {"leak_type": "data-breach"}))

    def test_breach_enums(self) -> None:
        assert validate_document(
            make_doc(
                "breach",
                {
                    "name": "Example Leak",
                    "leak_type": "ransomware-exfiltration",
                    "record_count_basis": "sample-extrapolated",
                    "corroboration": "officially-confirmed",
                    "data_categories": ["email-addresses", "password-hash", "other"],
                    "records_affected": 1_000_000,
                    "sample_size": 10_000,
                    "credential_count": 900_000,
                    "unique_email_count": 800_000,
                    "plaintext_password_count": 0,
                    "hash_algorithms": ["bcrypt"],
                    "leak_corpus_uri": "artifact://leaks/example-2026",
                    "leak_corpus_sha256": "sha256:abc",
                    "distribution_observations": [
                        {"platform": "forum", "actor_handle": "leaklord", "first_seen": NOW, "last_seen": NOW}
                    ],
                    "affected_org_ids": ["starintel:org:example"],
                    "affected_person_count": 800_000,
                    "cve_ids": ["CVE-2026-1234"],
                    "regulator_filing_refs": ["ref-1"],
                },
            )
        )
        for field, value in (
            ("leak_type", "gift"),
            ("record_count_basis", "vibes"),
            ("corroboration", "double-secret"),
        ):
            with pytest.raises(ValidationError, match="expected one of"):
                validate_document(make_doc("breach", {"name": "x", field: value}))
        with pytest.raises(ValidationError, match="expected one of"):
            validate_document(make_doc("breach", {"name": "x", "data_categories": ["spaceships"]}))

    def test_breach_rejects_inline_raw_material(self) -> None:
        for forbidden in ("credentials", "raw_records", "password_dump", "dump_content"):
            with pytest.raises(ValidationError, match="inline leaked material"):
                validate_document(make_doc("breach", {"name": "x", forbidden: ["user:pass"]}))
        # Reference-only posture: corpus lives behind a URI, not inline bytes.
        doc = make_doc(
            "breach",
            {"name": "x", "leak_corpus_uri": "artifact://leaks/x", "leaked_file_ids": ["starintel:file:x"]},
        )
        assert validate_document(doc)

    def test_distribution_observation_shape_is_enforced(self) -> None:
        doc = make_doc(
            "breach",
            {"name": "x", "distribution_observations": [{"platform": "forum", "password": "hunter2"}]},
        )
        with pytest.raises(ValidationError, match="undeclared field"):
            validate_document(doc)


class TestGeneratedSchema:
    def test_generated_schema_is_current(self) -> None:
        payload = json.loads(SCHEMA_FILE.read_text(encoding="utf-8"))
        assert payload["properties"]["dtype"]["enum"] == sorted(TYPE_FIELDS)
        assert payload["properties"]["schema_version"] == {"enum": ["0.9.0", "0.10.1"]}
        assert payload == document_schema()

    def test_legacy_artifacts_remain(self) -> None:
        for name in (
            "starintel-doc-v0.9.0.schema.json",
            "starintel-doc-v0.9.0.manifest.json",
            "starintel-doc-v0.9.0.expansion.json",
            "starintel-network-capture-v0.9.2.manifest.json",
        ):
            assert (ROOT / "schemas" / name).exists(), name


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
