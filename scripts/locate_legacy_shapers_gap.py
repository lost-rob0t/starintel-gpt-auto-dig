#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
import lzma
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Iterable

ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
EXPECTED_UNIQUE = 4062
THREAD_LOCAL = threading.local()


def read_encoded(parts: Path) -> tuple[str, list[int]]:
    paths = sorted(parts.glob("part-*"))
    chunks = ["".join(path.read_text(encoding="utf-8").split()) for path in paths]
    return "".join(chunks), [len(chunk) for chunk in chunks]


def decode_with_insert(encoded: str, position: int, character: str) -> bytes:
    repaired = encoded[:position] + character + encoded[position:]
    return base64.b64decode(repaired, validate=True)


def inspect_failure(compressed: bytes, chunk_size: int = 1) -> dict[str, Any]:
    decompressor = lzma.LZMADecompressor(format=lzma.FORMAT_XZ)
    output: list[bytes] = []
    consumed = 0
    error = ""
    for offset in range(0, len(compressed), chunk_size):
        try:
            output.append(decompressor.decompress(compressed[offset:offset + chunk_size]))
            consumed = offset + chunk_size
        except lzma.LZMAError as exc:
            error = f"{type(exc).__name__}: {exc}"
            consumed = offset
            break
    payload = b"".join(output)
    complete = payload[:payload.rfind(b"\n") + 1] if b"\n" in payload else b""
    rows = 0
    ids: set[str] = set()
    for line in complete.decode("utf-8", errors="ignore").splitlines():
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            break
        rows += 1
        if isinstance(value, list) and value:
            ids.add(str(value[0]))
        elif isinstance(value, dict):
            data = value.get("data") if isinstance(value.get("data"), dict) else {}
            identifier = data.get("_id") or data.get("id") or value.get("_id") or value.get("id")
            if identifier is not None:
                ids.add(str(identifier))
    return {
        "compressed_bytes": len(compressed),
        "consumed_before_error": consumed,
        "error": error,
        "eof": decompressor.eof,
        "decompressed_bytes": len(payload),
        "complete_rows": rows,
        "unique_ids": len(ids),
    }


def valid_payload(payload: bytes) -> bool:
    ids: set[str] = set()
    rows = 0
    try:
        for line in payload.decode("utf-8").splitlines():
            if not line.strip():
                continue
            value = json.loads(line)
            rows += 1
            if isinstance(value, list) and value:
                ids.add(str(value[0]))
            elif isinstance(value, dict):
                data = value.get("data") if isinstance(value.get("data"), dict) else {}
                identifier = data.get("_id") or data.get("id") or value.get("_id") or value.get("id")
                if identifier is not None:
                    ids.add(str(identifier))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return False
    return len(ids) == EXPECTED_UNIQUE and rows in {4062, 4176}


def try_position(encoded: str, position: int) -> tuple[int, str, bytes] | None:
    for character in ALPHABET:
        try:
            compressed = decode_with_insert(encoded, position, character)
            payload = lzma.decompress(compressed)
        except (ValueError, lzma.LZMAError):
            continue
        if valid_payload(payload):
            return position, character, payload
    return None


def search_positions(encoded: str, positions: Iterable[int], workers: int) -> tuple[int, str, bytes] | None:
    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        futures = {pool.submit(try_position, encoded, position): position for position in positions}
        for future in as_completed(futures):
            result = future.result()
            if result is not None:
                for pending in futures:
                    pending.cancel()
                return result
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Locate and repair the missing Base64 character in the retained Global Shapers XZ stream.")
    parser.add_argument("--parts", type=Path, default=Path("imports/.wef-shapers-compact"))
    parser.add_argument("--output", type=Path, default=Path(".generated/legacy-global-shapers/located.compact.jsonl"))
    parser.add_argument("--report", type=Path, default=Path("reports/global-shapers-gap-location.json"))
    parser.add_argument("--radius", type=int, default=2048)
    parser.add_argument("--workers", type=int, default=32)
    args = parser.parse_args()

    encoded, lengths = read_encoded(args.parts)
    data_end = len(encoded.rstrip("="))
    padded_end = encoded[:data_end] + "A" + encoded[data_end:]
    compressed = base64.b64decode(padded_end, validate=True)
    failure = inspect_failure(compressed)
    estimated = min(data_end, max(0, (int(failure["consumed_before_error"]) * 4) // 3))
    part07_start = sum(lengths[:-1])
    lower = max(part07_start, estimated - args.radius)
    upper = min(data_end, estimated + args.radius)
    positions = list(range(lower, upper + 1))

    result = search_positions(encoded, positions, args.workers)
    report: dict[str, Any] = {
        "part_lengths": lengths,
        "encoded_length": len(encoded),
        "data_characters": data_end,
        "part07_start": part07_start,
        "placeholder_failure": failure,
        "estimated_character_position": estimated,
        "search_lower": lower,
        "search_upper": upper,
        "positions": len(positions),
        "attempts_max": len(positions) * len(ALPHABET),
    }
    if result is None:
        report["status"] = "not-found"
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(report, indent=2, sort_keys=True))
        return 2

    position, character, payload = result
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(payload if payload.endswith(b"\n") else payload + b"\n")
    report.update({
        "status": "recovered",
        "insert_position": position,
        "insert_character": character,
        "payload_bytes": len(payload),
    })
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
