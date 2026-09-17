from __future__ import annotations

from copy import deepcopy
from typing import Any

from . import spec as base

SCHEMA_VERSION = base.SCHEMA_VERSION
RELEASE_VERSION = "0.9.2"
PROFILE_VERSION = RELEASE_VERSION
PROFILE_ID = "https://spec.starintel.actor/profile/network-capture-v0.9.2.json"

STR = base.STR
STRS = base.STRS
INT = base.INT
NUM = base.NUM
BOOL = base.BOOL
DATE_TIME = base.DATE_TIME
NULLABLE_DATE_TIME = base.NULLABLE_DATE_TIME
JSON_MAP = base.JSON_MAP

HTTP_TRANSACTION_FIELDS: dict[str, dict[str, Any]] = {
    "transaction_id": STR,
    "request_id": STR,
    "connection_id": STR,
    "parent_transaction_id": STR,
    "method": STR,
    "url": STR,
    "scheme": STR,
    "host": STR,
    "port": INT,
    "path": STR,
    "query": STR,
    "http_version": STR,
    "request_headers": JSON_MAP,
    "request_body_size": INT,
    "request_body_hash": STR,
    "request_body_artifact_uri": STR,
    "response_status": INT,
    "response_reason": STR,
    "response_headers": JSON_MAP,
    "response_body_size": INT,
    "response_body_hash": STR,
    "response_body_artifact_uri": STR,
    "started_at": NULLABLE_DATE_TIME,
    "ended_at": NULLABLE_DATE_TIME,
    "duration_ms": NUM,
    "remote_ip": STR,
    "remote_port": INT,
    "tls_version": STR,
    "tls_cipher": STR,
    "tls_server_name": STR,
    "certificate_sha256": STR,
    "redirect_from_id": STR,
    "redirect_to_id": STR,
    "capture_actor_uri": STR,
    "proxy_actor_uri": STR,
    "challenge_status": STR,
    "redacted_headers": STRS,
    "body_capture_policy": STR,
    "request_truncated": BOOL,
    "response_truncated": BOOL,
}

WEB_CAPTURE_FIELDS: dict[str, dict[str, Any]] = {
    "capture_id": STR,
    "url": STR,
    "final_url": STR,
    "title": STR,
    "status_code": INT,
    "browser": STR,
    "browser_version": STR,
    "viewport_width": INT,
    "viewport_height": INT,
    "device_scale_factor": NUM,
    "screenshot_uri": STR,
    "screenshot_hash": STR,
    "screenshot_media_type": STR,
    "screenshot_size_bytes": INT,
    "dom_artifact_uri": STR,
    "dom_artifact_hash": STR,
    "dom_artifact_size_bytes": INT,
    "captured_at": NULLABLE_DATE_TIME,
    "http_transaction_ids": STRS,
    "capture_actor_uri": STR,
    "proxy_actor_uri": STR,
    "challenge_status": STR,
    "challenge_actor_uri": STR,
}

TYPE_FIELDS: dict[str, dict[str, Any]] = {
    **base.TYPE_FIELDS,
    "http-transaction": HTTP_TRANSACTION_FIELDS,
    "web-capture": WEB_CAPTURE_FIELDS,
}

REQUIRED_DATA_FIELDS: dict[str, tuple[str, ...]] = {
    **base.REQUIRED_DATA_FIELDS,
    "http-transaction": ("transaction_id", "method", "url", "response_status"),
    "web-capture": ("capture_id", "url", "screenshot_uri", "screenshot_hash"),
}

DTYPE_ALIASES = {
    **base.DTYPE_ALIASES,
    "http_transaction": "http-transaction",
    "web_capture": "web-capture",
}

COMMON_PROPERTIES = deepcopy(base.COMMON_PROPERTIES)
COMMON_PROPERTIES["dtype"] = base.string(enum=sorted(TYPE_FIELDS))
REQUIRED_COMMON = base.REQUIRED_COMMON


def data_schema(dtype: str) -> dict[str, Any]:
    canonical = DTYPE_ALIASES.get(dtype, dtype)
    if canonical not in TYPE_FIELDS:
        raise KeyError(f"unknown dtype: {dtype}")
    return base.obj(
        deepcopy(TYPE_FIELDS[canonical]),
        required=REQUIRED_DATA_FIELDS.get(canonical, ()),
        additional=False,
    )


def document_schema(dtype: str | None = None) -> dict[str, Any]:
    properties = deepcopy(COMMON_PROPERTIES)
    if dtype is None:
        variants = [
            {
                "if": {"properties": {"dtype": {"const": name}}},
                "then": {"properties": {"data": data_schema(name)}},
            }
            for name in sorted(TYPE_FIELDS)
        ]
        return {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": PROFILE_ID,
            "title": "StarIntel Document v0.9.0 + network-capture profile v0.9.2",
            "type": "object",
            "properties": properties,
            "required": list(REQUIRED_COMMON),
            "additionalProperties": False,
            "allOf": variants,
        }
    canonical = DTYPE_ALIASES.get(dtype, dtype)
    if canonical not in TYPE_FIELDS:
        raise KeyError(f"unknown dtype: {dtype}")
    properties["dtype"] = {"const": canonical}
    properties["data"] = data_schema(canonical)
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"{PROFILE_ID}#{canonical}",
        "title": f"StarIntel {canonical} document network-capture v0.9.2",
        "type": "object",
        "properties": properties,
        "required": list(REQUIRED_COMMON),
        "additionalProperties": False,
    }
