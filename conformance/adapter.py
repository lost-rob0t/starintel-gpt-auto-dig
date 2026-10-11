"""Canonical wire adapter consuming the maintained StarLang-generated runtime.

Historical local research fixtures use conformance.legacy_adapter explicitly.
"""
import json
import sys
import starintel_canonical as runtime


def handle(request):
    if not isinstance(request, dict):
        raise ValueError("request must be a JSON object")
    if request.get("spec_version", runtime.SPEC_VERSION) != runtime.SPEC_VERSION:
        raise runtime.UnsupportedVersion(request.get("spec_version"))
    command = request.get("command")
    if command == "version":
        return {"ok": True, "spec_version": runtime.SPEC_VERSION}
    if command == "capabilities":
        return {"ok": True, **runtime.capabilities()}
    if command == "schema-inventory":
        return {"ok": True, "inventory": runtime.schema_inventory()}
    if command == "validate":
        runtime.validate_document(request.get("document"))
        return {"ok": True, "spec_version": runtime.SPEC_VERSION}
    if command == "roundtrip":
        return {"ok": True, "spec_version": runtime.SPEC_VERSION,
                "document": runtime.roundtrip_document(request.get("document"))}
    raise ValueError("unsupported command")


def main():
    try:
        response = handle(json.load(sys.stdin))
        status = 0
    except ValueError as error:
        response = {"ok": False, "error": getattr(error, "category", "invalid_request"), "message": str(error)}
        status = 1
    print(json.dumps(response, ensure_ascii=False, allow_nan=False))
    return status


if __name__ == "__main__":
    raise SystemExit(main())
