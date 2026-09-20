from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Mapping

from .network_capture import stable_capture_id
from .spec_093 import PROFILE_VERSION, SCHEMA_VERSION, document_schema
from .validation import ValidationError, validate_value

BREACH_PROFILE_DTYPES = frozenset({"breach", "breach-compilation", "paste"})


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def stable_breach_id(dtype: str, dataset: str, identity: Mapping[str, Any]) -> str:
    return stable_capture_id(dtype, dataset, identity)


def validate_breach_document(document: Mapping[str, Any]) -> dict[str, Any]:
    value = deepcopy(dict(document))
    dtype = value.get("dtype")
    if dtype not in BREACH_PROFILE_DTYPES:
        raise ValidationError(
            f"$.dtype: breach profile expects breach, breach-compilation, or paste, got {dtype!r}"
        )
    data = value.get("data")
    if isinstance(data, Mapping) and data.get("content_artifact_uri") and not data.get("content_hash"):
        raise ValidationError(
            "$.data.content_hash: paste content is artifact-reference-only and requires a content hash"
        )
    validate_value(value, document_schema(str(dtype)))
    return value


def _envelope(
    *,
    dataset: str,
    dtype: str,
    data: dict[str, Any],
    observed_at: str,
) -> dict[str, Any]:
    return {
        "_id": "",
        "dataset": dataset,
        "dtype": dtype,
        "schema_version": SCHEMA_VERSION,
        "version": 1,
        "date_added": observed_at,
        "date_updated": observed_at,
        "sources": [],
        "evidence": [],
        "data": data,
        "extensions": {"starintel.profile": {"release_version": PROFILE_VERSION}},
    }


def build_breach_compilation(
    *,
    dataset: str,
    name: str,
    source_artifact_uri: str,
    fmt: str,
    compilation_id: str | None = None,
    acquired_at: str | None = None,
    fields: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if not dataset or not name or not source_artifact_uri or not fmt:
        raise ValueError("dataset, name, source_artifact_uri, and fmt are required")
    timestamp = acquired_at or utc_now()
    identity_id = compilation_id or stable_breach_id(
        "breach-compilation",
        dataset,
        {"name": name, "source_artifact_uri": source_artifact_uri},
    )
    data: dict[str, Any] = {
        "compilation_id": identity_id,
        "name": name,
        "source_artifact_uri": source_artifact_uri,
        "format": fmt,
        "acquired_at": timestamp,
    }
    if fields:
        data.update(deepcopy(dict(fields)))
    document = _envelope(dataset=dataset, dtype="breach-compilation", data=data, observed_at=timestamp)
    document["_id"] = stable_breach_id("breach-compilation", dataset, {"compilation_id": identity_id})
    return validate_breach_document(document)


def build_paste(
    *,
    dataset: str,
    paste_key: str,
    paste_service: str,
    paste_url: str,
    paste_id: str | None = None,
    fetched_at: str | None = None,
    fields: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if not dataset or not paste_key or not paste_service or not paste_url:
        raise ValueError("dataset, paste_key, paste_service, and paste_url are required")
    timestamp = fetched_at or utc_now()
    identity_id = paste_id or stable_breach_id(
        "paste",
        dataset,
        {"paste_service": paste_service, "paste_key": paste_key},
    )
    data: dict[str, Any] = {
        "paste_key": paste_key,
        "paste_service": paste_service,
        "paste_url": paste_url,
        "fetched_at": timestamp,
        "http_transaction_ids": [],
        "alert_ids": [],
    }
    if fields:
        data.update(deepcopy(dict(fields)))
    document = _envelope(dataset=dataset, dtype="paste", data=data, observed_at=timestamp)
    document["_id"] = stable_breach_id("paste", dataset, {"paste_key": paste_key, "paste_service": paste_service})
    return validate_breach_document(document)


def to_jsonld(document: Mapping[str, Any]) -> dict[str, Any]:
    value = validate_breach_document(document)
    data = value["data"]
    if value["dtype"] == "paste":
        return {
            "@context": "https://schema.org",
            "@id": value["_id"],
            "@type": "DigitalDocument",
            "name": data.get("title") or data["paste_key"],
            "url": data["paste_url"],
            "dateCreated": data.get("paste_created_at"),
            "encoding": {
                "@type": "MediaObject",
                "contentUrl": data.get("content_artifact_uri"),
                "sha256": data.get("content_hash"),
                "encodingFormat": data.get("content_media_type", "text/plain"),
            },
        }
    return {
        "@context": "https://schema.org",
        "@id": value["_id"],
        "@type": "Dataset",
        "name": data["name"],
        "description": data.get("description"),
        "dateCreated": data.get("acquired_at"),
        "distribution": {
            "@type": "DataDownload",
            "contentUrl": data["source_artifact_uri"],
            "sha256": data.get("source_artifact_hash"),
        },
    }
