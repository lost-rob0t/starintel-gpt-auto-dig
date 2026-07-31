#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from starintel_doc.spec import DTYPE_ALIASES, REQUIRED_DATA_FIELDS, TYPE_FIELDS
from starintel_doc.validation import ValidationError, validate_document, validate_value

PACKET_DIR = Path("digs/wef/2026-07-31-thiel-company-employee-enumeration-depth-1")
PACKET = PACKET_DIR / "starintel-documents.jsonl"
README = PACKET_DIR / "README.md"


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
        raise ValidationError("value cannot be coerced to an allowed schema")

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
    if expected == "object" and not isinstance(value, dict):
        raise ValidationError("non-object cannot be coerced safely")
    return value


def normalize_document(document: dict[str, Any]) -> None:
    dtype = canonical_dtype(document)
    data = document.setdefault("data", {})
    extensions = document.setdefault("extensions", {})
    legacy = extensions.setdefault("legacy_data", {})

    if dtype == "org" and "organization_type" in data:
        organization_type = data.pop("organization_type")
        preserve(legacy, "organization_type", organization_type)
        data.setdefault("org_type", str(organization_type))

    if dtype == "person" and "employer_ids" in data:
        preserve(legacy, "employer_ids", data.pop("employer_ids"))

    allowed = TYPE_FIELDS[dtype]
    required = set(REQUIRED_DATA_FIELDS.get(dtype, ()))

    for key in list(data):
        if key not in allowed:
            preserve(legacy, key, data.pop(key))

    for key, value in list(data.items()):
        schema = allowed[key]
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
    documents = [json.loads(line) for line in PACKET.read_text(encoding="utf-8").splitlines() if line.strip()]
    for document in documents:
        normalize_document(document)

    PACKET.write_text(
        "\n".join(
            json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
            for document in documents
        )
        + "\n",
        encoding="utf-8",
    )

    readme = README.read_text(encoding="utf-8")
    if "## Schema normalization" not in readme:
        readme += (
            "\n\n## Schema normalization\n\n"
            "Packet-only organization, employer, standing-rule, required-rule, and pass-count fields "
            "were normalized to strict StarIntel v0.9. Original values remain under "
            "`extensions.legacy_data`; explicit relation records remain authoritative for employment "
            "and WEF links.\n"
        )
    README.write_text(readme, encoding="utf-8")

    print(f"validated_documents={len(documents)}")


if __name__ == "__main__":
    main()
