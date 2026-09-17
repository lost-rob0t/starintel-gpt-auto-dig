from __future__ import annotations

import copy

import pytest

from starintel_doc.network_capture import (
    build_http_transaction,
    build_web_capture,
    redact_headers,
    to_jsonld,
    validate_network_capture_document,
)
from starintel_doc.spec_092 import (
    CAPTCHA_SOLVE_CAPABILITY,
    DTYPE_ALIASES,
    PROFILE_VERSION,
    SCHEMA_VERSION,
    TYPE_FIELDS,
    document_schema,
)
from starintel_doc.validation import ValidationError

NOW = "2026-09-17T01:00:00Z"


def test_profile_keeps_v09_wire_and_adds_two_dtypes():
    assert SCHEMA_VERSION == "0.9.0"
    assert PROFILE_VERSION == "0.9.2"
    assert "http-transaction" in TYPE_FIELDS
    assert "web-capture" in TYPE_FIELDS
    assert DTYPE_ALIASES["http_transaction"] == "http-transaction"
    assert DTYPE_ALIASES["web_capture"] == "web-capture"


def test_http_transaction_redacts_sensitive_headers_and_uses_artifact_policy():
    doc = build_http_transaction(
        dataset="capture-fixture",
        method="get",
        url="https://example.test/a?x=1",
        response_status=403,
        observed_at=NOW,
        request_headers={"Authorization": "Bearer secret", "Accept": "text/html"},
        response_headers={"Set-Cookie": "sid=secret", "Content-Type": "text/html"},
        fields={
            "request_body_hash": "sha256:req",
            "request_body_artifact_uri": "artifact://requests/req-1",
            "response_body_hash": "sha256:resp",
            "response_body_artifact_uri": "artifact://responses/resp-1",
            "capture_actor_uri": "star://bbp.starintel.actor/actor/http-proxy",
            "proxy_actor_uri": "star://proxy.starintel.actor/actor/egress",
            "challenge_status": "observed",
            "captcha_detection_id": "captcha-detection:fixture-1",
            "browser_session_ref": "star-secret://webdriver/session/fixture-1",
            "network_context_ref": "star-secret://network/context/fixture-1",
        },
    )
    assert doc["schema_version"] == "0.9.0"
    assert doc["data"]["method"] == "GET"
    assert doc["data"]["request_headers"]["Authorization"] == "[REDACTED]"
    assert doc["data"]["response_headers"]["Set-Cookie"] == "[REDACTED]"
    assert doc["data"]["redacted_headers"] == ["Authorization", "Set-Cookie"]
    assert doc["data"]["body_capture_policy"] == "artifact-reference-only"
    assert doc["data"]["captcha_capability"] == CAPTCHA_SOLVE_CAPABILITY
    assert doc["data"]["browser_session_ref"].startswith("star-secret://")
    assert doc["data"]["network_context_ref"].startswith("star-secret://")
    assert doc["extensions"]["starintel.profile"]["release_version"] == "0.9.2"


def test_web_capture_requires_artifact_reference_and_hash():
    doc = build_web_capture(
        dataset="capture-fixture",
        url="https://example.test/",
        screenshot_uri="artifact://screenshots/abc.png",
        screenshot_hash="sha256:abc",
        captured_at=NOW,
        fields={
            "viewport_width": 1440,
            "viewport_height": 900,
            "capture_actor_uri": "star://bbp.starintel.actor/actor/screenshot",
            "challenge_status": "observed",
            "browser_session_ref": "star-secret://webdriver/session/fixture-2",
        },
    )
    assert doc["dtype"] == "web-capture"
    assert doc["data"]["screenshot_uri"].startswith("artifact://")
    assert doc["data"]["captcha_capability"] == CAPTCHA_SOLVE_CAPABILITY
    assert to_jsonld(doc)["@type"] == "DigitalDocument"


def test_profile_rejects_unknown_http_fields():
    doc = build_http_transaction(
        dataset="capture-fixture",
        method="GET",
        url="https://example.test/",
        response_status=204,
        observed_at=NOW,
    )
    bad = copy.deepcopy(doc)
    bad["data"]["raw_password"] = "nope"
    with pytest.raises(ValidationError, match="undeclared field"):
        validate_network_capture_document(bad)


def test_profile_rejects_missing_required_http_method():
    doc = build_http_transaction(
        dataset="capture-fixture",
        method="GET",
        url="https://example.test/",
        response_status=204,
        observed_at=NOW,
    )
    bad = copy.deepcopy(doc)
    del bad["data"]["method"]
    with pytest.raises(ValidationError, match="missing required field"):
        validate_network_capture_document(bad)


def test_profile_schema_inventory_is_additive():
    schema = document_schema()
    assert schema["properties"]["dtype"]["enum"] == sorted(TYPE_FIELDS)
    assert {"http-transaction", "web-capture"} <= set(schema["properties"]["dtype"]["enum"])


def test_redact_headers_is_case_insensitive():
    headers, names = redact_headers({"COOKIE": "secret", "x-test": "ok"})
    assert headers == {"COOKIE": "[REDACTED]", "x-test": "ok"}
    assert names == ["COOKIE"]
