from __future__ import annotations

import json
import sys
from copy import deepcopy
from typing import Any

from starintel_doc.model import Document
from starintel_doc.spec import DTYPE_ALIASES, SCHEMA_VERSION, TYPE_FIELDS, data_schema
from starintel_doc.validation import ValidationError, validate_document

EXIT_OK = 0
EXIT_REJECTED = 1
EXIT_RUNTIME = 2
EXIT_UNSUPPORTED = 3


def error_category(message: str) -> str:
    checks = (
        ("missing required field", "missing_required_field"),
        ("undeclared field", "undeclared_field"),
        ("expected ISO-8601 date-time", "invalid_datetime"),
        ("below minimum", "below_minimum"),
        ("above maximum", "above_maximum"),
        ("does not match", "pattern_mismatch"),
        ("expected one of", "invalid_enum"),
        ("unknown document type", "unknown_object_type"),
        ("expected constant", "unsupported_spec_version"),
        ("expected ", "wrong_type"),
    )
    for needle, category in checks:
        if needle in message:
            return category
    return "validation_error"


def schema_inventory() -> list[dict[str, Any]]:
    inventory: list[dict[str, Any]] = []
    for dtype in sorted(TYPE_FIELDS):
        schema = data_schema(dtype)
        fields: dict[str, Any] = {}
        required = set(schema.get("required", []))
        for name, definition in sorted(schema.get("properties", {}).items()):
            item: dict[str, Any] = {"required": name in required}
            if "type" in definition:
                item["type"] = definition["type"]
            elif "anyOf" in definition:
                item["any_of"] = [candidate.get("type", candidate.get("const", "any")) for candidate in definition["anyOf"]]
            if "enum" in definition:
                item["enum"] = definition["enum"]
            if "format" in definition:
                item["format"] = definition["format"]
            fields[name] = item
        inventory.append({"object_type": dtype, "fields": fields})
    return inventory


def capabilities() -> dict[str, Any]:
    return {
        "language": "python",
        "adapter_version": 1,
        "spec_versions": [SCHEMA_VERSION],
        "commands": ["validate", "normalize", "roundtrip", "version", "capabilities", "schema-inventory"],
        "object_types": sorted(TYPE_FIELDS),
        "preserves_unknown_extensions": True,
        "preserves_missing_optional_fields": True,
    }


def check_version(request: dict[str, Any]) -> None:
    requested = request.get("spec_version", SCHEMA_VERSION)
    if requested != SCHEMA_VERSION:
        raise UnsupportedVersion(str(requested))


class UnsupportedVersion(ValueError):
    pass


def normalize(document: dict[str, Any]) -> dict[str, Any]:
    value = deepcopy(document)
    dtype = value.get("dtype")
    if isinstance(dtype, str) and dtype in DTYPE_ALIASES:
        value["dtype"] = DTYPE_ALIASES[dtype]
    validate_document(value)
    return value


def handle(request: dict[str, Any]) -> dict[str, Any]:
    command = request.get("command")
    if command == "version":
        return {"ok": True, "spec_version": SCHEMA_VERSION, "adapter_version": 1, "language": "python"}
    if command == "capabilities":
        return {"ok": True, **capabilities()}
    if command == "schema-inventory":
        check_version(request)
        return {"ok": True, "spec_version": SCHEMA_VERSION, "inventory": schema_inventory()}

    check_version(request)
    document = request.get("document")
    if not isinstance(document, dict):
        raise ValidationError("$: expected object")

    if command == "validate":
        validate_document(document)
        return {"ok": True, "spec_version": SCHEMA_VERSION, "warnings": []}
    if command == "normalize":
        return {"ok": True, "spec_version": SCHEMA_VERSION, "document": normalize(document), "warnings": []}
    if command == "roundtrip":
        value = Document.from_dict(deepcopy(document)).to_dict()
        return {"ok": True, "spec_version": SCHEMA_VERSION, "document": value, "warnings": []}
    raise ValueError(f"unsupported command: {command!r}")


def main() -> int:
    try:
        request = json.load(sys.stdin)
        if not isinstance(request, dict):
            raise ValueError("request must be a JSON object")
        response = handle(request)
        print(json.dumps(response, ensure_ascii=False, separators=(",", ":"), sort_keys=True))
        return EXIT_OK
    except UnsupportedVersion as exc:
        print(json.dumps({"ok": False, "error": "unsupported_spec_version", "message": str(exc)}, separators=(",", ":"), sort_keys=True))
        return EXIT_UNSUPPORTED
    except ValidationError as exc:
        message = str(exc)
        category = error_category(message)
        print(json.dumps({"ok": False, "error": category, "message": message}, ensure_ascii=False, separators=(",", ":"), sort_keys=True))
        return EXIT_UNSUPPORTED if category == "unsupported_spec_version" else EXIT_REJECTED
    except Exception as exc:  # adapter boundary
        print(f"python adapter failure: {exc}", file=sys.stderr)
        print(json.dumps({"ok": False, "error": "adapter_failure", "message": str(exc)}, ensure_ascii=False, separators=(",", ":"), sort_keys=True))
        return EXIT_RUNTIME


if __name__ == "__main__":
    raise SystemExit(main())
