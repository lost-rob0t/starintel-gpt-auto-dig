"""StarLang-generated public wire API. Historical research tooling: .legacy."""
from .canonical import (
    Document, DOCUMENT_TYPES, MANIFEST, SPEC_VERSION, ValidationError,
    UnsupportedVersion, capabilities, generated, load_schema,
    roundtrip_document, schema_inventory, validate_document,
)

SCHEMA_VERSION = SPEC_VERSION
ACCEPTED_SCHEMA_VERSIONS = (SPEC_VERSION,)
SCHEMA_ID = load_schema()["$id"]

def document_schema(dtype=None):
    schema = load_schema()
    if dtype is not None:
        schema["$ref"] = f"#/$defs/{DOCUMENT_TYPES[dtype]}"
    return schema
