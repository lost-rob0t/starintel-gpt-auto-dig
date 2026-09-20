from __future__ import annotations

from copy import deepcopy
from typing import Any

from . import spec as base
from . import spec_092

SCHEMA_VERSION = base.SCHEMA_VERSION
RELEASE_VERSION = "0.9.3"
PROFILE_VERSION = RELEASE_VERSION
PROFILE_ID = "https://spec.starintel.actor/profile/breach-v0.9.3.json"
BASE_PROFILE_ID = spec_092.PROFILE_ID
BASE_PROFILE_VERSION = spec_092.PROFILE_VERSION

STR = base.STR
STRS = base.STRS
INT = base.INT
NUM = base.NUM
BOOL = base.BOOL
DATE_TIME = base.DATE_TIME
NULLABLE_DATE_TIME = base.NULLABLE_DATE_TIME
JSON_MAP = base.JSON_MAP

BREACH_ADDITIONAL_FIELDS: dict[str, dict[str, Any]] = {
    "compilation_ids": STRS,
    "corpus_entry_ref": STR,
    "credential_classes": STRS,
    "first_observed_at": NULLABLE_DATE_TIME,
    "corpus_record_count": INT,
}

BREACH_COMPILATION_FIELDS: dict[str, dict[str, Any]] = {
    "compilation_id": STR,
    "name": STR,
    "description": STR,
    "acquired_at": NULLABLE_DATE_TIME,
    "source_artifact_uri": STR,
    "source_artifact_hash": STR,
    "source_dataset_ids": STRS,
    "format": STR,
    "topology": STR,
    "entry_file_count": INT,
    "record_count_estimate": INT,
    "entries_indexed": INT,
    "last_checkpoint": STR,
    "dataset_ids": STRS,
}

PASTE_FIELDS: dict[str, dict[str, Any]] = {
    "paste_key": STR,
    "paste_service": STR,
    "paste_url": STR,
    "title": STR,
    "syntax": STR,
    "author": STR,
    "visibility": STR,
    "size_bytes": INT,
    "paste_created_at": NULLABLE_DATE_TIME,
    "paste_expires_at": NULLABLE_DATE_TIME,
    "fetched_at": NULLABLE_DATE_TIME,
    "content_artifact_uri": STR,
    "content_hash": STR,
    "content_media_type": STR,
    "matched_rule_ids": STRS,
    "watch_source": STR,
    "http_transaction_ids": STRS,
    "alert_ids": STRS,
}

TYPE_FIELDS: dict[str, dict[str, Any]] = {
    **spec_092.TYPE_FIELDS,
    "breach": {**spec_092.TYPE_FIELDS["breach"], **BREACH_ADDITIONAL_FIELDS},
    "breach-compilation": BREACH_COMPILATION_FIELDS,
    "paste": PASTE_FIELDS,
}

REQUIRED_DATA_FIELDS: dict[str, tuple[str, ...]] = {
    **spec_092.REQUIRED_DATA_FIELDS,
    "breach-compilation": ("compilation_id", "name", "source_artifact_uri", "format"),
    "paste": ("paste_key", "paste_service", "paste_url"),
}

DTYPE_ALIASES = {
    **spec_092.DTYPE_ALIASES,
    "breach_compilation": "breach-compilation",
}

COMMON_PROPERTIES = deepcopy(spec_092.COMMON_PROPERTIES)
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
            "title": "StarIntel Document v0.9.0 + breach profile v0.9.3",
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
        "title": f"StarIntel {canonical} document breach v0.9.3",
        "type": "object",
        "properties": properties,
        "required": list(REQUIRED_COMMON),
        "additionalProperties": False,
    }
