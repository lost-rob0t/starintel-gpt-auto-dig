"""Explicit corpus profile compatibility, separate from the canonical wire API."""
from .validation import validate_document as validate_research_document

def validate_stored_document(document):
    if "schemaVersion" in document:
        from .canonical import validate_document
        return validate_document(document)
    return validate_research_document(document)

def document_id(document):
    return document.get("id") if "schemaVersion" in document else document.get("_id")
