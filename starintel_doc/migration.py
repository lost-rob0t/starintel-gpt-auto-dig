from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any

from .model import empty_document
from .spec import (
    ASSESSMENT,
    ATTACHMENT,
    DTYPE_ALIASES,
    EVIDENCE,
    GEOSPATIAL,
    HANDLING,
    IDENTIFIER,
    LINEAGE,
    PROVENANCE,
    QUALITY,
    SCHEMA_VERSION,
    SOURCE,
    TEMPORAL,
    TYPE_FIELDS,
    VERIFICATION,
    WORKFLOW,
)
from .validation import validate_document

COMMON_KEYS = {
    "_id", "_rev", "dataset", "dtype", "schema_version", "version",
    "date_added", "date_updated", "title", "summary", "description",
    "status", "language", "tags", "labels", "aliases", "keywords",
    "identifiers", "sources", "evidence", "temporal", "provenance",
    "assessment", "verification", "handling", "lineage", "quality",
    "workflow", "geospatial", "attachments", "related_ids", "notes",
    "data", "extensions",
}

CAMEL_ALIASES = {
    "isReply": "is_reply",
    "messageId": "message_id",
    "replyTo": "reply_to",
    "replyCount": "reply_count",
    "repostCount": "repost_count",
    "likeCount": "like_count",
    "viewCount": "view_count",
    "from_": "from",
    "dateAdded": "date_added",
    "dateUpdated": "date_updated",
    "phoneType": "phone_type",
    "recordType": "record_type",
    "resolvedAddresses": "resolved_addresses",
    "targetOptions": "target_options",
    "consumerPath": "consumer_path",
}


def _allowed(schema: dict[str, Any]) -> set[str]:
    return set(schema.get("properties", {}))


SOURCE_KEYS = _allowed(SOURCE)
EVIDENCE_KEYS = _allowed(EVIDENCE)
TEMPORAL_KEYS = _allowed(TEMPORAL)
ASSESSMENT_KEYS = _allowed(ASSESSMENT)
HANDLING_KEYS = _allowed(HANDLING)


def _coerce(value: Any, schema: dict[str, Any]) -> Any:
    if not schema:
        return value
    if "anyOf" in schema:
        for candidate in schema["anyOf"]:
            expected = candidate.get("type")
            if expected == "null" and value is None:
                return None
            if expected == "string" and isinstance(value, str):
                return _coerce(value, candidate)
            if expected == "object" and isinstance(value, dict):
                return _coerce(value, candidate)
            if expected == "array" and isinstance(value, list):
                return _coerce(value, candidate)
        return _coerce(value, schema["anyOf"][0])
    expected = schema.get("type")
    if expected == "string":
        if schema.get("format") == "date-time":
            return _iso(value)
        return "" if value is None else str(value)
    if expected == "integer":
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0
    if expected == "number":
        try:
            result = float(value)
        except (TypeError, ValueError):
            result = 0.0
        if "minimum" in schema:
            result = max(float(schema["minimum"]), result)
        if "maximum" in schema:
            result = min(float(schema["maximum"]), result)
        return result
    if expected == "boolean":
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "on"}
        return bool(value)
    if expected == "array":
        items = value if isinstance(value, list) else ([] if value in (None, "") else [value])
        return [_coerce(item, schema.get("items", {})) for item in items]
    if expected == "object":
        if not isinstance(value, dict):
            return {}
        properties = schema.get("properties", {})
        additional = schema.get("additionalProperties", True)
        out: dict[str, Any] = {}
        for key, item in value.items():
            if key in properties:
                out[key] = _coerce(item, properties[key])
            elif additional is True:
                out[key] = item
            elif isinstance(additional, dict):
                out[key] = _coerce(item, additional)
        return out
    if expected == "null":
        return None
    return value


def _normalize_relation_endpoint(value: Any) -> Any:
    if isinstance(value, list):
        return [_normalize_relation_endpoint(item) for item in value]
    if not isinstance(value, dict):
        return "" if value is None else str(value)

    endpoint_id = next(
        (
            value.get(key)
            for key in ("id", "_id", "entity_id", "document_id", "target_id", "source_id")
            if value.get(key) not in (None, "")
        ),
        None,
    )
    label = next(
        (
            value.get(key)
            for key in ("label", "name", "display_name", "organization", "person", "firm", "candidate")
            if value.get(key) not in (None, "")
        ),
        None,
    )

    endpoint: dict[str, Any] = {}
    if endpoint_id is not None:
        endpoint["id"] = str(endpoint_id)
    if value.get("entity_id") not in (None, ""):
        endpoint["entity_id"] = str(value["entity_id"])
    if value.get("document_id") not in (None, ""):
        endpoint["document_id"] = str(value["document_id"])
    if value.get("external_id") not in (None, ""):
        endpoint["external_id"] = str(value["external_id"])
    if value.get("dtype") not in (None, ""):
        endpoint["dtype"] = str(value["dtype"])
    if label is not None:
        endpoint["label"] = str(label)
        endpoint["name"] = str(value.get("name") or label)
    if value.get("role") not in (None, ""):
        endpoint["role"] = str(value["role"])
    if isinstance(value.get("external_ids"), list):
        endpoint["external_ids"] = value["external_ids"]
    if isinstance(value.get("aliases"), list):
        endpoint["aliases"] = [str(item) for item in value["aliases"]]

    known = {
        "id", "_id", "entity_id", "document_id", "target_id", "source_id",
        "external_id", "dtype", "label", "name", "display_name", "organization",
        "person", "firm", "candidate", "role", "unresolved", "external_ids",
        "aliases", "qualifiers", "metadata",
    }
    qualifiers = dict(value.get("qualifiers")) if isinstance(value.get("qualifiers"), dict) else {}
    legacy = {key: item for key, item in value.items() if key not in known}
    if legacy:
        qualifiers.setdefault("legacy", {}).update(legacy)
    if qualifiers:
        endpoint["qualifiers"] = qualifiers
    if isinstance(value.get("metadata"), dict):
        endpoint["metadata"] = value["metadata"]
    endpoint["unresolved"] = bool(value.get("unresolved", not endpoint.get("id")))
    return endpoint


def _sanitize_object(raw: Any, schema: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    if not isinstance(raw, dict):
        return {}, {"legacy_value": raw} if raw not in (None, "", [], {}) else {}
    properties = schema.get("properties", {})
    out: dict[str, Any] = {}
    extra: dict[str, Any] = {}
    for key, value in raw.items():
        canonical_key = CAMEL_ALIASES.get(key, key)
        if canonical_key in properties:
            coerced = _coerce(value, properties[canonical_key])
            if coerced is not None or any(branch.get("type") == "null" for branch in properties[canonical_key].get("anyOf", [])):
                out[canonical_key] = coerced
        else:
            extra[canonical_key] = value
    return out, extra


def _iso(value: Any) -> str | None:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, timezone.utc).isoformat().replace("+00:00", "Z")
    text = str(value).strip()
    if not text:
        return None
    if re.fullmatch(r"\d{4}", text):
        return f"{text}-01-01T00:00:00Z"
    if re.fullmatch(r"\d{4}-\d{2}", text):
        return f"{text}-01T00:00:00Z"
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
        return f"{text}T00:00:00Z"
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.isoformat().replace("+00:00", "Z")


def _now_from(record: dict[str, Any]) -> str:
    return _iso(record.get("date_updated")) or _iso(record.get("date_added")) or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if item is not None and str(item) != ""]
    if isinstance(value, (tuple, set)):
        return [str(item) for item in value if item is not None and str(item) != ""]
    return [str(value)] if str(value) else []


def _normalize_source(raw: Any) -> dict[str, Any]:
    if isinstance(raw, str):
        return {"kind": "web", "name": raw, "title": raw, "uri": raw, "url": raw}
    if not isinstance(raw, dict):
        return {"kind": "unknown", "name": str(raw), "metadata": {"legacy_value": raw}}
    out: dict[str, Any] = {}
    metadata: dict[str, Any] = {}
    aliases = {"credibility_score": "credibility", "retrieved": "retrieved_at", "accessed": "accessed_at"}
    for key, value in raw.items():
        key = aliases.get(key, key)
        if key in {"published_at", "retrieved_at", "accessed_at"}:
            value = _iso(value)
        if key in SOURCE_KEYS:
            out[key] = value
        else:
            metadata[key] = value
    if "uri" in out and "url" not in out:
        out["url"] = out["uri"]
    if "url" in out and "uri" not in out:
        out["uri"] = out["url"]
    if "name" in out and "title" not in out:
        out["title"] = out["name"]
    if metadata:
        out["metadata"] = {**out.get("metadata", {}), **metadata}
    return out


def _normalize_evidence(raw: Any) -> dict[str, Any]:
    if isinstance(raw, str):
        return {"kind": "statement", "observation": raw}
    if not isinstance(raw, dict):
        return {"kind": "unknown", "metadata": {"legacy_value": raw}}
    out: dict[str, Any] = {}
    metadata: dict[str, Any] = {}
    for key, value in raw.items():
        if key in {"collected_at", "observed_at", "valid_from", "valid_to"}:
            value = _iso(value)
        if key in EVIDENCE_KEYS:
            out[key] = value
        else:
            metadata[key] = value
    if metadata:
        out["metadata"] = {**out.get("metadata", {}), **metadata}
    return out


def _normalize_object(raw: Any, allowed: set[str], date_fields: set[str] = set()) -> tuple[dict[str, Any], dict[str, Any]]:
    if not isinstance(raw, dict):
        return {}, {"legacy_value": raw} if raw not in (None, "", [], {}) else {}
    out: dict[str, Any] = {}
    extra: dict[str, Any] = {}
    for key, value in raw.items():
        key = CAMEL_ALIASES.get(key, key)
        if key in date_fields:
            value = _iso(value)
        if key in allowed:
            out[key] = value
        else:
            extra[key] = value
    return out, extra


def _normalize_version(value: Any) -> int:
    if isinstance(value, int) and value >= 1:
        return value
    if isinstance(value, float) and value >= 1:
        return int(value)
    text = str(value or "").strip()
    if text.isdigit() and int(text) >= 1:
        return int(text)
    return 1


def _canonical_dtype(value: Any) -> str:
    raw = str(value or "document").strip().lower().replace(" ", "-")
    raw = DTYPE_ALIASES.get(raw, raw)
    return raw if raw in TYPE_FIELDS else "document"


def _fallback_title(record: dict[str, Any], data: dict[str, Any]) -> str:
    for key in ("title", "name", "display_name", "legal_name", "full_name", "claim", "term", "case_name", "target"):
        value = record.get(key) if key in record else data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return str(record.get("_id", "StarIntel record"))


def migrate_document(record: dict[str, Any], *, original_path: str = "") -> dict[str, Any]:
    if not isinstance(record, dict):
        raise TypeError("StarIntel record must be an object")
    if record.get("schema_version") == SCHEMA_VERSION:
        validate_document(record)
        return record

    dtype = _canonical_dtype(record.get("dtype"))
    now = _now_from(record)
    doc_id = str(record.get("_id") or record.get("id") or "")
    if not doc_id:
        raise ValueError("record is missing _id")
    dataset = str(record.get("dataset") or "star-intel")
    out = empty_document(dtype, dataset, doc_id)
    out["version"] = _normalize_version(record.get("version"))
    out["date_added"] = _iso(record.get("date_added") or record.get("dateAdded")) or now
    out["date_updated"] = _iso(record.get("date_updated") or record.get("dateUpdated")) or now
    if record.get("_rev"):
        out["_rev"] = str(record["_rev"])

    for key in ("title", "summary", "description", "status", "language"):
        value = record.get(key)
        if isinstance(value, str):
            out[key] = value
    for key in ("tags", "labels", "aliases", "keywords", "related_ids", "notes"):
        if key in record:
            out[key] = _string_list(record[key])
    if record.get("identifiers") is not None:
        out["identifiers"] = _coerce(record.get("identifiers"), {"type": "array", "items": IDENTIFIER})
    if record.get("attachments") is not None:
        out["attachments"] = _coerce(record.get("attachments"), {"type": "array", "items": ATTACHMENT})

    raw_sources: list[Any] = []
    if isinstance(record.get("sources"), list):
        raw_sources.extend(record["sources"])
    elif record.get("sources") not in (None, ""):
        raw_sources.append(record["sources"])
    if isinstance(record.get("source"), dict):
        raw_sources.append(record["source"])
    out["sources"] = [_normalize_source(item) for item in raw_sources]

    raw_evidence = record.get("evidence", [])
    if not isinstance(raw_evidence, list):
        raw_evidence = [raw_evidence]
    out["evidence"] = [_normalize_evidence(item) for item in raw_evidence if item not in (None, "")]

    temporal_raw = record.get("temporal", record.get("time", {}))
    temporal, temporal_extra = _normalize_object(
        temporal_raw,
        TEMPORAL_KEYS,
        {
            "observed_at", "collected_at", "published_at", "created_at", "modified_at",
            "event_start", "event_end", "valid_from", "valid_to", "first_seen", "last_seen",
        },
    )
    out["temporal"] = temporal

    assessment_raw = record.get("assessment", record.get("analysis", {}))
    assessment, assessment_extra = _normalize_object(assessment_raw, ASSESSMENT_KEYS)
    if "confidence" in record and "confidence" not in assessment:
        try:
            assessment["confidence"] = float(record["confidence"])
        except (TypeError, ValueError):
            assessment_extra["confidence"] = record["confidence"]
    out["assessment"] = assessment

    handling_raw = record.get("handling", record.get("opsec", {}))
    handling, handling_extra = _normalize_object(handling_raw, HANDLING_KEYS, {"embargo_until"})
    out["handling"] = {**out["handling"], **handling}

    nested_schemas = {
        "provenance": PROVENANCE,
        "verification": VERIFICATION,
        "lineage": LINEAGE,
        "quality": QUALITY,
        "workflow": WORKFLOW,
        "geospatial": GEOSPATIAL,
    }
    nested_extras: dict[str, Any] = {}
    for key, schema in nested_schemas.items():
        if record.get(key) is not None:
            normalized, extra = _sanitize_object(record.get(key), schema)
            out[key] = normalized
            if extra:
                nested_extras[key] = extra
    out["provenance"].update(
        {
            "original_schema_version": str(record.get("schema_version") or record.get("version") or "legacy"),
            "original_id": doc_id,
            "original_path": original_path,
            "transform": "starintel_doc.migration.migrate_document",
            "software_version": SCHEMA_VERSION,
        }
    )
    out["lineage"].update(
        {
            "migration_from": str(record.get("schema_version") or record.get("version") or "legacy"),
            "migration_notes": ["Normalized into the canonical StarIntel v0.9.0 document envelope."],
        }
    )

    allowed_data = set(TYPE_FIELDS[dtype])
    data: dict[str, Any] = {}
    data_extra: dict[str, Any] = {}

    if isinstance(record.get("data"), dict):
        for key, value in record["data"].items():
            canonical_key = CAMEL_ALIASES.get(key, key)
            if canonical_key in allowed_data:
                data[canonical_key] = _coerce(value, TYPE_FIELDS[dtype][canonical_key])
            else:
                data_extra[canonical_key] = value

    if isinstance(record.get("entity"), dict):
        for key, value in record["entity"].items():
            canonical_key = CAMEL_ALIASES.get(key, key)
            if canonical_key in allowed_data and canonical_key not in data:
                data[canonical_key] = _coerce(value, TYPE_FIELDS[dtype][canonical_key])
            else:
                data_extra[canonical_key] = value

    excluded = COMMON_KEYS | {"id", "source", "time", "analysis", "opsec", "entity", "predicates"}
    for key, value in record.items():
        canonical_key = CAMEL_ALIASES.get(key, key)
        if key in excluded or canonical_key in excluded:
            continue
        if canonical_key in allowed_data and canonical_key not in data:
            data[canonical_key] = _coerce(value, TYPE_FIELDS[dtype][canonical_key])
        else:
            data_extra[canonical_key] = value

    if dtype == "relation":
        raw_subject = record.get("subject")
        if raw_subject in (None, ""):
            raw_subject = record.get("source") if isinstance(record.get("source"), str) else data.get("subject", "")
        raw_object = record.get("object")
        if raw_object in (None, ""):
            raw_object = record.get("target") or data.get("object", "")
        data["subject"] = _normalize_relation_endpoint(raw_subject)
        data["object"] = _normalize_relation_endpoint(raw_object)
        data.setdefault("predicate", str(record.get("predicate") or "related_to"))
        if isinstance(record.get("source"), str):
            data.setdefault("source", record["source"])
        if isinstance(record.get("target"), str):
            data.setdefault("target", record["target"])
    elif dtype in {"target", "investigation-target"}:
        data.setdefault("target", str(record.get("target") or record.get("title") or record.get("_id")))
    elif dtype == "email":
        if "address" not in data:
            user = str(data.get("user", ""))
            domain = str(data.get("domain", ""))
            data["address"] = f"{user}@{domain}" if user and domain else str(record.get("address") or "")
    elif dtype == "domain":
        data.setdefault("domain", str(record.get("domain") or record.get("record") or record.get("title") or ""))
    elif dtype == "url":
        data.setdefault("url", str(record.get("url") or record.get("title") or ""))
    elif dtype == "phone":
        data.setdefault("number", str(record.get("number") or record.get("value") or ""))
    elif dtype == "claim":
        data.setdefault("claim", str(record.get("claim") or record.get("statement") or record.get("summary") or record.get("description") or ""))

    out["data"] = data
    out["title"] = out["title"] or _fallback_title(record, data)
    if not out["summary"]:
        for candidate in (record.get("summary"), record.get("description"), data.get("description"), data.get("claim"), data.get("definition")):
            if isinstance(candidate, str) and candidate.strip():
                out["summary"] = candidate.strip()
                break

    extensions = record.get("extensions") if isinstance(record.get("extensions"), dict) else {}
    legacy: dict[str, Any] = {}
    if data_extra:
        legacy["data"] = data_extra
    if temporal_extra:
        legacy["temporal"] = temporal_extra
    if assessment_extra:
        legacy["assessment"] = assessment_extra
    if handling_extra:
        legacy["handling"] = handling_extra
    if nested_extras:
        legacy["metadata"] = nested_extras
    if record.get("predicates") not in (None, [], {}):
        legacy["predicates"] = record["predicates"]
    if legacy:
        extensions = {**extensions, "legacy.v0": legacy}
    out["extensions"] = extensions

    validate_document(out)
    return out


def migrate_json_line(line: str, *, original_path: str = "") -> str:
    record = json.loads(line)
    migrated = migrate_document(record, original_path=original_path)
    return json.dumps(migrated, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
