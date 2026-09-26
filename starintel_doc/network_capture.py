from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Mapping

from . import spec as core_spec
from . import spec_092 as legacy_spec
from .spec_092 import CAPTCHA_SOLVE_CAPABILITY
from .validation import ValidationError, validate_value

SENSITIVE_HEADERS = frozenset(
    {
        "authorization",
        "proxy-authorization",
        "cookie",
        "set-cookie",
        "x-api-key",
        "x-auth-token",
    }
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def redact_headers(headers: Mapping[str, Any]) -> tuple[dict[str, Any], list[str]]:
    clean: dict[str, Any] = {}
    redacted: list[str] = []
    for key, value in headers.items():
        name = str(key)
        if name.casefold() in SENSITIVE_HEADERS:
            clean[name] = "[REDACTED]"
            redacted.append(name)
        else:
            clean[name] = deepcopy(value)
    return clean, sorted(redacted, key=str.casefold)


def stable_capture_id(dtype: str, dataset: str, identity: Mapping[str, Any]) -> str:
    payload = json.dumps(
        {"dataset": dataset, "dtype": dtype, **dict(identity)},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    digest = hashlib.sha256(payload).hexdigest()
    return f"starintel:{dtype}:{digest}"


def validate_network_capture_document(document: Mapping[str, Any]) -> dict[str, Any]:
    value = deepcopy(dict(document))
    dtype = value.get("dtype")
    if dtype not in {"http-transaction", "web-capture"}:
        raise ValidationError(
            f"$.dtype: network-capture profile expects http-transaction or web-capture, got {dtype!r}"
        )
    schema_version = value.get("schema_version")
    spec = legacy_spec if schema_version == legacy_spec.SCHEMA_VERSION else core_spec
    validate_value(value, spec.document_schema(str(dtype)))
    return value


def _apply_capture_context(data: dict[str, Any], fields: Mapping[str, Any] | None) -> None:
    if fields:
        data.update(deepcopy(dict(fields)))
    if data.get("challenge_status") not in (None, "", "none"):
        data.setdefault("captcha_capability", CAPTCHA_SOLVE_CAPABILITY)


def build_http_transaction(
    *,
    dataset: str,
    method: str,
    url: str,
    response_status: int,
    transaction_id: str | None = None,
    request_headers: Mapping[str, Any] | None = None,
    response_headers: Mapping[str, Any] | None = None,
    observed_at: str | None = None,
    fields: Mapping[str, Any] | None = None,
    legacy_profile: bool = False,
) -> dict[str, Any]:
    if not dataset or not method or not url:
        raise ValueError("dataset, method, and url are required")
    timestamp = observed_at or utc_now()
    spec = legacy_spec if legacy_profile else core_spec
    request, request_redacted = redact_headers(request_headers or {})
    response, response_redacted = redact_headers(response_headers or {})
    identity_id = transaction_id or stable_capture_id(
        "http-transaction",
        dataset,
        {
            "method": method.upper(),
            "url": url,
            "response_status": response_status,
            "observed_at": timestamp,
        },
    )
    data: dict[str, Any] = {
        "transaction_id": identity_id,
        "method": method.upper(),
        "url": url,
        "request_headers": request,
        "response_status": response_status,
        "response_headers": response,
        "redacted_headers": sorted(set(request_redacted + response_redacted), key=str.casefold),
        "started_at": timestamp,
        "ended_at": timestamp,
        "challenge_status": "none",
        "body_capture_policy": "artifact-reference-only",
    }
    _apply_capture_context(data, fields)
    document = {
        "_id": stable_capture_id("http-transaction", dataset, {"transaction_id": identity_id}),
        "dataset": dataset,
        "dtype": "http-transaction",
        "schema_version": spec.SCHEMA_VERSION,
        "version": 1,
        "date_added": timestamp,
        "date_updated": timestamp,
        "sources": [],
        "evidence": [],
        "data": data,
        "extensions": {"starintel.profile": {"release_version": legacy_spec.PROFILE_VERSION if legacy_profile else core_spec.SCHEMA_VERSION}},
    }
    return validate_network_capture_document(document)


def build_web_capture(
    *,
    dataset: str,
    url: str,
    screenshot_uri: str,
    screenshot_hash: str,
    capture_id: str | None = None,
    captured_at: str | None = None,
    fields: Mapping[str, Any] | None = None,
    legacy_profile: bool = False,
) -> dict[str, Any]:
    if not dataset or not url or not screenshot_uri or not screenshot_hash:
        raise ValueError("dataset, url, screenshot_uri, and screenshot_hash are required")
    timestamp = captured_at or utc_now()
    spec = legacy_spec if legacy_profile else core_spec
    identity_id = capture_id or stable_capture_id(
        "web-capture",
        dataset,
        {
            "url": url,
            "screenshot_hash": screenshot_hash,
            "captured_at": timestamp,
        },
    )
    data: dict[str, Any] = {
        "capture_id": identity_id,
        "url": url,
        "screenshot_uri": screenshot_uri,
        "screenshot_hash": screenshot_hash,
        "screenshot_media_type": "image/png",
        "captured_at": timestamp,
        "http_transaction_ids": [],
        "challenge_status": "none",
    }
    _apply_capture_context(data, fields)
    document = {
        "_id": stable_capture_id("web-capture", dataset, {"capture_id": identity_id}),
        "dataset": dataset,
        "dtype": "web-capture",
        "schema_version": spec.SCHEMA_VERSION,
        "version": 1,
        "date_added": timestamp,
        "date_updated": timestamp,
        "sources": [],
        "evidence": [],
        "data": data,
        "extensions": {"starintel.profile": {"release_version": legacy_spec.PROFILE_VERSION if legacy_profile else core_spec.SCHEMA_VERSION}},
    }
    return validate_network_capture_document(document)


def to_jsonld(document: Mapping[str, Any]) -> dict[str, Any]:
    value = validate_network_capture_document(document)
    data = value["data"]
    if value["dtype"] == "http-transaction":
        return {
            "@context": "https://schema.org",
            "@id": value["_id"],
            "@type": "Action",
            "name": f"HTTP {data['method']} transaction",
            "target": data["url"],
            "startTime": data.get("started_at"),
            "endTime": data.get("ended_at"),
            "result": {"@type": "Thing", "identifier": str(data["response_status"])},
        }
    return {
        "@context": "https://schema.org",
        "@id": value["_id"],
        "@type": "DigitalDocument",
        "url": data["url"],
        "encoding": {
            "@type": "MediaObject",
            "contentUrl": data["screenshot_uri"],
            "encodingFormat": data.get("screenshot_media_type", "image/png"),
            "sha256": data["screenshot_hash"],
        },
        "dateCreated": data.get("captured_at"),
    }
