from __future__ import annotations

from copy import deepcopy
from typing import Any

from .schema_org import schema_org_metadata


def enrich_schema_org(document: dict[str, Any]) -> dict[str, Any]:
    """Add deterministic Schema.org defaults without replacing explicit JSON-LD metadata."""
    value = deepcopy(document)
    dtype = str(value.get("dtype") or "document")
    document_id = str(value.get("_id") or "")
    explicit = value.get("schema_org") if isinstance(value.get("schema_org"), dict) else {}
    value["schema_org"] = {
        **schema_org_metadata(dtype, document_id),
        **deepcopy(explicit),
    }
    return value
