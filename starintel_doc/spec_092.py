from __future__ import annotations

from copy import deepcopy
from typing import Any

from . import spec as base

# 0.9-line compatibility module (docs/schema-0.10.1-design.md §2).
# The 0.9.2 network-capture profile is superseded by the 0.10.1 core, which
# folds http-transaction and web-capture into base TYPE_FIELDS. This module
# keeps working for consumers still pinned to the 0.9 line: the wire identity
# stays a strict "0.9.0" const, while the field tables transparently re-export
# the unified base vocabulary (a superset). Freeze-pin the 0.9.x git tag or
# the legacy schemas/starintel-doc-v0.9.0.* artifacts for the exact frozen
# 0.9-era profile.
SCHEMA_VERSION = "0.9.0"
RELEASE_VERSION = "0.9.2"
PROFILE_VERSION = RELEASE_VERSION
PROFILE_ID = "https://spec.starintel.actor/profile/network-capture-v0.9.2.json"
CAPTCHA_SOLVE_CAPABILITY = "captcha.solve"

STR = base.STR
STRS = base.STRS
INT = base.INT
NUM = base.NUM
BOOL = base.BOOL
DATE_TIME = base.DATE_TIME
NULLABLE_DATE_TIME = base.NULLABLE_DATE_TIME
JSON_MAP = base.JSON_MAP

CAPTCHA_CONTEXT_FIELDS = base.CAPTCHA_CONTEXT_FIELDS
HTTP_TRANSACTION_FIELDS = base.HTTP_TRANSACTION_FIELDS
WEB_CAPTURE_FIELDS = base.WEB_CAPTURE_FIELDS

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
# Strict 0.9-line profile: only the legacy envelope validates here.
COMMON_PROPERTIES["schema_version"] = {"const": SCHEMA_VERSION}
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
