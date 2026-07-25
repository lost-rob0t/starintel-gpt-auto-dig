from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from .spec import DTYPE_ALIASES, SCHEMA_VERSION, TYPE_FIELDS, document_schema


class ValidationError(ValueError):
    pass


def _typename(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


def _matches_type(value: Any, expected: str) -> bool:
    if expected == "null":
        return value is None
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "string":
        return isinstance(value, str)
    if expected == "array":
        return isinstance(value, list)
    if expected == "object":
        return isinstance(value, dict)
    return True


def _validate_datetime(value: str, path: str) -> None:
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValidationError(f"{path}: expected ISO-8601 date-time, got {value!r}") from exc


def validate_value(value: Any, schema: dict[str, Any], path: str = "$") -> None:
    if not schema:
        return

    if "anyOf" in schema:
        failures: list[str] = []
        for candidate in schema["anyOf"]:
            try:
                validate_value(value, candidate, path)
                return
            except ValidationError as exc:
                failures.append(str(exc))
        raise ValidationError(f"{path}: value did not match any allowed schema: {'; '.join(failures)}")

    if "const" in schema and value != schema["const"]:
        raise ValidationError(f"{path}: expected constant {schema['const']!r}, got {value!r}")

    if "enum" in schema and value not in schema["enum"]:
        raise ValidationError(f"{path}: expected one of {schema['enum']!r}, got {value!r}")

    expected = schema.get("type")
    if expected and not _matches_type(value, expected):
        raise ValidationError(f"{path}: expected {expected}, got {_typename(value)}")

    if isinstance(value, str):
        pattern = schema.get("pattern")
        if pattern and re.search(pattern, value) is None:
            raise ValidationError(f"{path}: value does not match {pattern!r}")
        if schema.get("format") == "date-time":
            _validate_datetime(value, path)

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            raise ValidationError(f"{path}: {value} is below minimum {schema['minimum']}")
        if "maximum" in schema and value > schema["maximum"]:
            raise ValidationError(f"{path}: {value} is above maximum {schema['maximum']}")

    if isinstance(value, list):
        item_schema = schema.get("items", {})
        for index, item in enumerate(value):
            validate_value(item, item_schema, f"{path}[{index}]")

    if isinstance(value, dict):
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        for key in required:
            if key not in value:
                raise ValidationError(f"{path}: missing required field {key!r}")
        additional = schema.get("additionalProperties", True)
        for key, item in value.items():
            if key in properties:
                validate_value(item, properties[key], f"{path}.{key}")
            elif additional is False:
                raise ValidationError(f"{path}: undeclared field {key!r}")
            elif isinstance(additional, dict):
                validate_value(item, additional, f"{path}.{key}")


def validate_document(document: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(document, dict):
        raise ValidationError("$: expected object")
    dtype = str(document.get("dtype", ""))
    dtype = DTYPE_ALIASES.get(dtype, dtype)
    if dtype not in TYPE_FIELDS:
        raise ValidationError(f"$.dtype: unknown document type {dtype!r}")
    if document.get("schema_version") != SCHEMA_VERSION:
        raise ValidationError(
            f"$.schema_version: expected {SCHEMA_VERSION!r}, got {document.get('schema_version')!r}"
        )
    validate_value(document, document_schema(dtype))
    return document
