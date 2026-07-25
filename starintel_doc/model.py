from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from .spec import (
    DTYPE_ALIASES,
    SCHEMA_ID,
    SCHEMA_PROFILE,
    SCHEMA_PROFILE_VERSION,
    SCHEMA_REVISION,
    SCHEMA_VERSION,
    TYPE_FIELDS,
)
from .validation import validate_document


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "record"


def stable_id(dtype: str, *identity: Any) -> str:
    canonical = DTYPE_ALIASES.get(dtype, dtype)
    if canonical not in TYPE_FIELDS:
        raise ValueError(f"unknown dtype: {dtype}")
    raw = "\x1f".join(json.dumps(item, ensure_ascii=False, sort_keys=True) for item in identity)
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20]
    label = slug(str(identity[0]))[:64] if identity else digest
    return f"starintel:{canonical}:{label}-{digest}"


def empty_document(dtype: str, dataset: str, doc_id: str | None = None) -> dict[str, Any]:
    canonical = DTYPE_ALIASES.get(dtype, dtype)
    if canonical not in TYPE_FIELDS:
        raise ValueError(f"unknown dtype: {dtype}")
    now = utc_now()
    return {
        "_id": doc_id or stable_id(canonical, now),
        "dataset": dataset,
        "dtype": canonical,
        "schema_version": SCHEMA_VERSION,
        "schema_revision": SCHEMA_REVISION,
        "schema_uri": SCHEMA_ID,
        "profile": SCHEMA_PROFILE,
        "profile_version": SCHEMA_PROFILE_VERSION,
        "version": 1,
        "date_added": now,
        "date_updated": now,
        "title": "",
        "summary": "",
        "description": "",
        "status": "recorded",
        "language": "en",
        "tags": [],
        "labels": [],
        "aliases": [],
        "keywords": [],
        "identifiers": [],
        "sources": [],
        "evidence": [],
        "temporal": {},
        "provenance": {},
        "assessment": {},
        "verification": {"status": "unverified", "verified": False},
        "handling": {"visibility": "public", "sensitive": False, "pii": False},
        "lineage": {"schema_revision": SCHEMA_REVISION},
        "quality": {},
        "workflow": {},
        "geospatial": {},
        "attachments": [],
        "related_ids": [],
        "object_marking_ids": [],
        "revoked": False,
        "deleted": False,
        "notes": [],
        "data": {},
        "extensions": {},
    }


@dataclass(slots=True)
class Document:
    value: dict[str, Any]

    @classmethod
    def create(
        cls,
        dtype: str,
        dataset: str,
        *,
        doc_id: str | None = None,
        title: str = "",
        summary: str = "",
        data: dict[str, Any] | None = None,
        **metadata: Any,
    ) -> "Document":
        value = empty_document(dtype, dataset, doc_id)
        value["title"] = title
        value["summary"] = summary
        value["data"] = data or {}
        for key, item in metadata.items():
            if key not in value:
                raise ValueError(f"undeclared top-level field: {key}")
            value[key] = item
        validate_document(value)
        return cls(value)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "Document":
        validate_document(value)
        return cls(value)

    def validate(self) -> "Document":
        validate_document(self.value)
        return self

    def touch(self, *, updated_by: str = "") -> "Document":
        self.value["version"] = int(self.value["version"]) + 1
        self.value["date_updated"] = utc_now()
        self.value["schema_revision"] = SCHEMA_REVISION
        self.value["schema_uri"] = SCHEMA_ID
        self.value.setdefault("lineage", {})["schema_revision"] = SCHEMA_REVISION
        if updated_by:
            self.value.setdefault("provenance", {})["updated_by"] = updated_by
        return self.validate()

    def to_dict(self) -> dict[str, Any]:
        return json.loads(json.dumps(self.value, ensure_ascii=False))

    def to_json(self, *, pretty: bool = False) -> str:
        if pretty:
            return json.dumps(self.value, ensure_ascii=False, indent=2, sort_keys=True)
        return json.dumps(self.value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
