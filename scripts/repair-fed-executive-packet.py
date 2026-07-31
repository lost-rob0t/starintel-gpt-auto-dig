#!/usr/bin/env python3
from __future__ import annotations

import base64
import gzip
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from starintel_doc.spec import DTYPE_ALIASES, REQUIRED_DATA_FIELDS, TYPE_FIELDS
from starintel_doc.validation import ValidationError, validate_document, validate_value

PACKET = Path("digs/fed/2026-07-31-executive-branch-cabinet-advisors-pass-1")
TRANSPORT = PACKET / "starintel-documents.jsonl.gz.b64"
TARGETS = PACKET / "recursive-targets-pass-1.jsonl"
MANIFEST = PACKET / "manifest.json"
README = PACKET / "README.md"

PRIORITY_MAP = {
    "low": 0.25,
    "medium": 0.5,
    "normal": 0.5,
    "high": 0.85,
    "urgent": 1.0,
    "critical": 1.0,
}


def canonical_dtype(document: dict[str, Any]) -> str:
    dtype = str(document.get("dtype", ""))
    return DTYPE_ALIASES.get(dtype, dtype)


def preserve(legacy: dict[str, Any], key: str, value: Any) -> None:
    legacy.setdefault(key, value)


def coerce(value: Any, schema: dict[str, Any]) -> Any:
    if not schema:
        return value
    if "anyOf" in schema:
        for candidate in schema["anyOf"]:
            try:
                converted = coerce(value, candidate)
                validate_value(converted, candidate)
                return converted
            except (ValidationError, TypeError, ValueError):
                continue
        raise ValidationError("value cannot be coerced to any allowed schema")

    expected = schema.get("type")
    if expected == "string":
        if isinstance(value, list):
            return "; ".join(str(item) for item in value)
        if isinstance(value, dict):
            return json.dumps(value, sort_keys=True, separators=(",", ":"))
        return str(value)
    if expected == "array":
        return value if isinstance(value, list) else [value]
    if expected == "number":
        if isinstance(value, str) and value.lower() in PRIORITY_MAP:
            return PRIORITY_MAP[value.lower()]
        return float(value)
    if expected == "integer":
        return int(float(value))
    if expected == "boolean":
        if isinstance(value, str):
            lowered = value.strip().lower()
            if lowered in {"true", "yes", "1"}:
                return True
            if lowered in {"false", "no", "0"}:
                return False
        return bool(value)
    if expected == "object":
        if isinstance(value, dict):
            return value
        raise ValidationError("non-object cannot be coerced safely")
    return value


def normalize_document(document: dict[str, Any]) -> None:
    data = document.setdefault("data", {})
    extensions = document.setdefault("extensions", {})
    legacy = extensions.setdefault("legacy_data", {})
    dtype = canonical_dtype(document)

    if dtype in {"target", "investigation-target"}:
        questions = data.get("questions")
        if isinstance(questions, list) and questions:
            data.setdefault("objectives", [str(item) for item in questions])
            data.setdefault("research_question", str(questions[0]))
        next_sources = data.get("next_sources")
        if isinstance(next_sources, list) and next_sources:
            data.setdefault("preferred_sources", [str(item) for item in next_sources])
        data.setdefault(
            "target",
            document.get("title")
            or document.get("summary")
            or data.get("research_question")
            or data.get("query")
            or document["_id"],
        )

    if dtype == "relation":
        qualifiers = data.setdefault("qualifiers", {})
        for key in ("appointment_status", "confirmation_date"):
            if key in data:
                qualifiers.setdefault(key, data[key])

    allowed_schemas = TYPE_FIELDS[dtype]
    required = set(REQUIRED_DATA_FIELDS.get(dtype, ()))

    for key in list(data):
        if key not in allowed_schemas:
            preserve(legacy, key, data.pop(key))

    for key, value in list(data.items()):
        schema = allowed_schemas[key]
        try:
            validate_value(value, schema, f"$.data.{key}")
        except ValidationError:
            preserve(legacy, key, value)
            try:
                converted = coerce(value, schema)
                validate_value(converted, schema, f"$.data.{key}")
                data[key] = converted
            except (ValidationError, TypeError, ValueError):
                if key in required:
                    raise
                data.pop(key)

    if not legacy:
        extensions.pop("legacy_data", None)
    if not extensions:
        document.pop("extensions", None)

    validate_document(document)


def main() -> None:
    encoded = "".join(TRANSPORT.read_text(encoding="utf-8").split())
    original_gzip = base64.b64decode(encoded, validate=True)
    original_jsonl = gzip.decompress(original_gzip).decode("utf-8")
    documents = [json.loads(line) for line in original_jsonl.splitlines() if line.strip()]

    for document in documents:
        normalize_document(document)

    payload = (
        "\n".join(
            json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
            for document in documents
        )
        + "\n"
    ).encode("utf-8")
    compressed = gzip.compress(payload, compresslevel=9, mtime=0)
    TRANSPORT.write_text(base64.b64encode(compressed).decode("ascii") + "\n", encoding="utf-8")

    targets = [
        document
        for document in documents
        if canonical_dtype(document) in {"target", "investigation-target"}
    ]
    TARGETS.write_text(
        "\n".join(
            json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
            for document in targets
        )
        + "\n",
        encoding="utf-8",
    )

    jsonl_hash = hashlib.sha256(payload).hexdigest()
    gzip_hash = hashlib.sha256(compressed).hexdigest()
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manifest["starintel_documents_sha256"] = jsonl_hash
    manifest["gzip_transport_sha256"] = gzip_hash
    manifest.setdefault("validation", {})["strict_v0_9_schema"] = "passed"
    manifest["validation"]["legacy_fields"] = "preserved under extensions.legacy_data"
    MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    readme = README.read_text(encoding="utf-8")
    readme = re.sub(
        r"Canonical JSONL SHA-256: `[^`]+`",
        f"Canonical JSONL SHA-256: `{jsonl_hash}`",
        readme,
    )
    readme = re.sub(r"Gzip SHA-256: `[^`]+`", f"Gzip SHA-256: `{gzip_hash}`", readme)
    if "## Schema normalization" not in readme:
        readme += (
            "\n\n## Schema normalization\n\n"
            "Legacy packet-only fields and original values requiring type coercion were preserved "
            "under `extensions.legacy_data`; target questions and preferred sources were mapped "
            "into declared StarIntel v0.9 fields.\n"
        )
    README.write_text(readme, encoding="utf-8")

    print(f"normalized_documents={len(documents)} targets={len(targets)}")
    print(f"jsonl_sha256={jsonl_hash}")
    print(f"gzip_sha256={gzip_hash}")


if __name__ == "__main__":
    main()
