#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import json
import lzma
from pathlib import Path
from typing import Any, Iterable

BASE64_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
EXPECTED_RAW_ROW_COUNTS = {4062, 4176}
EXPECTED_UNIQUE_PEOPLE = 4062


def stripped(path: Path) -> str:
    return "".join(path.read_text(encoding="utf-8").split())


def padded(value: str) -> str:
    return value + ("=" * ((-len(value)) % 4))


def validate_payload(payload: bytes) -> tuple[list[Any], int]:
    values: list[Any] = []
    ids: set[str] = set()
    for number, raw_line in enumerate(payload.decode("utf-8").splitlines(), 1):
        if not raw_line.strip():
            continue
        value = json.loads(raw_line)
        values.append(value)
        if isinstance(value, list) and value:
            ids.add(str(value[0]))
        elif isinstance(value, dict):
            data = value.get("data") if isinstance(value.get("data"), dict) else {}
            identifier = data.get("_id") or data.get("id") or value.get("_id") or value.get("id")
            if identifier is not None:
                ids.add(str(identifier))
        else:
            raise ValueError(f"row {number}: unsupported value type {type(value).__name__}")
    if len(values) not in EXPECTED_RAW_ROW_COUNTS:
        raise ValueError(
            f"expected one of {sorted(EXPECTED_RAW_ROW_COUNTS)} raw row counts, decoded {len(values)}"
        )
    if len(ids) != EXPECTED_UNIQUE_PEOPLE:
        raise ValueError(f"expected {EXPECTED_UNIQUE_PEOPLE} unique IDs, decoded {len(ids)}")
    return values, len(ids)


def write_validated_payload(output: Path, payload: bytes) -> tuple[int, str]:
    values, _ = validate_payload(payload)
    normalized = payload if payload.endswith(b"\n") else payload + b"\n"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(normalized)
    return len(values), hashlib.sha256(normalized).hexdigest()


def decode_base64(encoded: str) -> bytes | None:
    try:
        return base64.b64decode(padded(encoded), validate=True)
    except binascii.Error:
        return None


def decode_candidate(encoded: str) -> tuple[bytes, int] | None:
    compressed = decode_base64(encoded)
    if compressed is None or not compressed.startswith(b"\xfd7zXZ\x00"):
        return None
    try:
        payload = lzma.decompress(compressed)
        values, _ = validate_payload(payload)
    except (lzma.LZMAError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
        return None
    return payload, len(values)


def salvage_truncated_xz(encoded: str, chunk_size: int = 64) -> tuple[bytes, dict[str, Any]] | None:
    compressed = decode_base64(encoded)
    if compressed is None or not compressed.startswith(b"\xfd7zXZ\x00"):
        return None

    decompressor = lzma.LZMADecompressor(format=lzma.FORMAT_XZ)
    chunks: list[bytes] = []
    error = ""
    consumed = 0
    for offset in range(0, len(compressed), chunk_size):
        block = compressed[offset:offset + chunk_size]
        try:
            chunks.append(decompressor.decompress(block))
            consumed = offset + len(block)
        except lzma.LZMAError as exc:
            error = f"{type(exc).__name__}: {exc}"
            consumed = offset
            break

    payload = b"".join(chunks)
    candidates = [payload]
    last_newline = payload.rfind(b"\n")
    if last_newline >= 0:
        candidates.append(payload[:last_newline + 1])

    for candidate in candidates:
        try:
            values, _ = validate_payload(candidate)
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
            continue
        return candidate, {
            "compressed_bytes": len(compressed),
            "compressed_bytes_consumed": consumed,
            "decompressor_eof": decompressor.eof,
            "decompression_error": error,
            "raw_rows": len(values),
            "payload_bytes": len(candidate),
        }
    return None


def ordered_deltas(radius: int) -> list[int]:
    values = [0]
    for distance in range(1, radius + 1):
        values.extend((-distance, distance))
    return values


def candidate_positions(lengths: list[int], radius: int) -> list[int]:
    total = sum(lengths)
    boundaries: list[int] = []
    cursor = 0
    for length in lengths[:-1]:
        cursor += length
        boundaries.append(cursor)

    anchors = [total, *reversed(boundaries), 0]
    seen: set[int] = set()
    positions: list[int] = []
    for delta in ordered_deltas(radius):
        for anchor in anchors:
            position = anchor + delta
            if 0 <= position <= total and position not in seen:
                seen.add(position)
                positions.append(position)
    return positions


def successful_insertion(encoded: str, position: int) -> tuple[str, str, bytes, int] | None:
    left = encoded[:position]
    right = encoded[position:]
    for character in BASE64_ALPHABET:
        repaired = left + character + right
        decoded = decode_candidate(repaired)
        if decoded is not None:
            payload, raw_rows = decoded
            return character, repaired, payload, raw_rows
    return None


def recover_transport(
    part_paths: Iterable[Path],
    output: Path,
    report_path: Path | None = None,
    radius: int = 32,
) -> dict[str, Any]:
    paths = sorted(part_paths)
    chunks = [stripped(path) for path in paths]
    lengths = [len(chunk) for chunk in chunks]
    encoded = "".join(chunks)

    direct = decode_candidate(encoded)
    if direct is not None:
        payload, raw_rows = direct
        raw_rows, payload_sha = write_validated_payload(output, payload)
        report = {
            "status": "already-valid",
            "parts": [str(path) for path in paths],
            "part_lengths": lengths,
            "encoded_length": len(encoded),
            "encoded_sha256": hashlib.sha256(encoded.encode()).hexdigest(),
            "payload_sha256": payload_sha,
            "raw_rows": raw_rows,
            "unique_people": EXPECTED_UNIQUE_PEOPLE,
        }
        if report_path:
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return report

    # The retained file ends with normal Base64 padding but has an impossible
    # number of data characters. The dominant failure mode is one omitted data
    # character immediately before the existing '=' padding.
    data_end = len(encoded.rstrip("="))
    preferred = successful_insertion(encoded, data_end)
    if preferred is not None:
        character, repaired, payload, _ = preferred
        raw_rows, payload_sha = write_validated_payload(output, payload)
        report = {
            "status": "recovered-before-base64-padding",
            "parts": [str(path) for path in paths],
            "part_lengths": lengths,
            "encoded_length_before": len(encoded),
            "encoded_length_after": len(repaired),
            "insert_position": data_end,
            "insert_character": character,
            "repaired_encoded_sha256": hashlib.sha256(repaired.encode()).hexdigest(),
            "payload_sha256": payload_sha,
            "raw_rows": raw_rows,
            "unique_people": EXPECTED_UNIQUE_PEOPLE,
        }
        if report_path:
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return report

    salvaged = salvage_truncated_xz(encoded)
    if salvaged is not None:
        payload, salvage = salvaged
        raw_rows, payload_sha = write_validated_payload(output, payload)
        report = {
            "status": "salvaged-truncated-xz",
            "parts": [str(path) for path in paths],
            "part_lengths": lengths,
            "encoded_length": len(encoded),
            "encoded_length_mod_4": len(encoded) % 4,
            "encoded_sha256": hashlib.sha256(encoded.encode()).hexdigest(),
            "payload_sha256": payload_sha,
            "raw_rows": raw_rows,
            "unique_people": EXPECTED_UNIQUE_PEOPLE,
            "salvage": salvage,
        }
        if report_path:
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return report

    positions = candidate_positions(lengths, radius)
    attempts = 64
    for position in positions:
        if position == data_end:
            continue
        result = successful_insertion(encoded, position)
        attempts += 64
        if result is None:
            continue
        character, repaired, payload, _ = result
        raw_rows, payload_sha = write_validated_payload(output, payload)
        report = {
            "status": "recovered-inserted-base64-character",
            "parts": [str(path) for path in paths],
            "part_lengths": lengths,
            "encoded_length_before": len(encoded),
            "encoded_length_after": len(repaired),
            "insert_position": position,
            "insert_character": character,
            "boundary_radius": radius,
            "attempts": attempts,
            "repaired_encoded_sha256": hashlib.sha256(repaired.encode()).hexdigest(),
            "payload_sha256": payload_sha,
            "raw_rows": raw_rows,
            "unique_people": EXPECTED_UNIQUE_PEOPLE,
        }
        if report_path:
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return report

    report = {
        "status": "not-recovered",
        "parts": [str(path) for path in paths],
        "part_lengths": lengths,
        "encoded_length": len(encoded),
        "encoded_data_characters": data_end,
        "encoded_padding_characters": len(encoded) - data_end,
        "encoded_length_mod_4": len(encoded) % 4,
        "boundary_radius": radius,
        "positions_tested": len(positions) + 1,
        "attempts": attempts,
    }
    if report_path:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    raise RuntimeError(
        "unable to salvage or repair retained transport; "
        f"part lengths={lengths}, encoded length={len(encoded)}, data characters={data_end}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Recover a truncated retained Global Shapers XZ/Base64 transport."
    )
    parser.add_argument(
        "--parts",
        type=Path,
        default=Path("imports/.wef-shapers-compact"),
        help="Directory containing part-* files.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(".generated/legacy-global-shapers/recovered.compact.jsonl"),
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("reports/global-shapers-transport-recovery.json"),
    )
    parser.add_argument("--radius", type=int, default=32)
    args = parser.parse_args()
    report = recover_transport(
        args.parts.glob("part-*"),
        args.output,
        args.report,
        radius=args.radius,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
