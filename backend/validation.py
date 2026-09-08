"""StarIntel v0.9 validation wrapper.

The repository-local `starintel_doc` package is the canonical authority.
Validation failures are typed errors; nothing invalid ever crosses the API.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from starintel_doc.validation import validate_document  # noqa: E402


class DocumentValidationError(ValueError):
    def __init__(self, doc_id: str, message: str) -> None:
        super().__init__(f"{doc_id}: {message}")
        self.doc_id = doc_id


def validate_v09(document: Any) -> dict[str, Any]:
    """Validate one parsed document against StarIntel v0.9. Raises DocumentValidationError."""
    if not isinstance(document, dict):
        raise DocumentValidationError("<unknown>", "document must be a JSON object")
    doc_id = str(document.get("_id", "<unknown>"))
    try:
        return validate_document(document)
    except Exception as exc:  # starintel_doc raises ValueError subclasses
        raise DocumentValidationError(doc_id, str(exc)) from exc


def validate_v09_line(line: str) -> dict[str, Any]:
    """Parse and validate one NDJSON line. Empty lines are skipped via None return."""
    trimmed = line.strip()
    if not trimmed:
        raise DocumentValidationError("<empty>", "empty NDJSON line")
    import json

    try:
        parsed = json.loads(trimmed)
    except json.JSONDecodeError as exc:
        raise DocumentValidationError("<unparseable>", f"invalid JSON: {exc}") from exc
    return validate_v09(parsed)
