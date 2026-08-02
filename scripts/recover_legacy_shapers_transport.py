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
EXPECTED_RAW_ROWS = 4176
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
    if len(values) != EXPECTED_RAW_ROWS:
        raise ValueError(f"expected {EXPECTED_RAW_ROWS} raw rows, decoded {len(values)}")
    if len(ids) != EXPECTED_UNIQUE_PEOPLE:
        raise ValueError(f"expected {EXPECTED_UNIQUE_PEOPLE} unique IDs, decoded {len(ids)}")
    return values, len(ids)


def decode_candidate(encoded: str) -> bytes | None:
    try:
        compressed = base64.b64decode(padded(encoded), validate=True)
    except binascii.Error:
        return None
    if not compressed.startswith(b"\xfd7zXZ\x00"):
        return None
    try:
        payload = lzma.decompress(compressed)
        validate_payload(payload)
    except (lzma.LZMAError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
        return None
    return payload


def candidate_positions(lengths: list[int], radius: int) -> list[int]:
    total = sum(lengths)
    anchors = {0, total}
    cursor = 0
    for length in lengths[:-1]:
        cursor += length
        anchors.add(cursor)
    positions: set[int] = set()
    for anchor in anchors:
        for delta in range(-radius, radius + 1):
            position = anchor + delta
            if 0 <= position <= total:
                positions.add(position)
    return sorted(positions)


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
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(direct if direct.endswith(b"\n") else direct + b"\n")
        report = {
            "status": "already-valid",
            "parts": [str(path) for path in paths],
            "part_lengths": lengths,
            "encoded_length": len(encoded),
            "encoded_sha256": hashlib.sha256(encoded.encode()).hexdigest(),
            "payload_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
            "raw_rows": EXPECTED_RAW_ROWS,
            "unique_people": EXPECTED_UNIQUE_PEOPLE,
        }
        if report_path:
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return report

    positions = candidate_positions(lengths, radius)
    attempts = 0
    for position in positions:
        left = encoded[:position]
        right = encoded[position:]
        for character in BASE64_ALPHABET:
            attempts += 1
            repaired = left + character + right
            payload = decode_candidate(repaired)
            if payload is None:
                continue
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(payload if payload.endswith(b"\n") else payload + b"\n")
            report = {
                "status": "recovered",
                "parts": [str(path) for path in paths],
                "part_lengths": lengths,
                "encoded_length_before": len(encoded),
                "encoded_length_after": len(repaired),
                "insert_position": position,
                "insert_character": character,
                "boundary_radius": radius,
                "attempts": attempts,
                "repaired_encoded_sha256": hashlib.sha256(repaired.encode()).hexdigest(),
                "payload_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
                "raw_rows": EXPECTED_RAW_ROWS,
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
        "encoded_length_mod_4": len(encoded) % 4,
        "boundary_radius": radius,
        "positions_tested": len(positions),
        "attempts": attempts,
    }
    if report_path:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    raise RuntimeError(
        "unable to recover retained transport by inserting one Base64 character "
        f"near {len(positions)} chunk-boundary positions; part lengths={lengths}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Recover the one-character-truncated retained Global Shapers XZ/Base64 transport."
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
