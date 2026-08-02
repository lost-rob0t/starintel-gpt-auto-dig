#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import gzip
import hashlib
import json
import lzma
import re
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
PARTS = ROOT / "imports" / ".wef-shapers-compact"
IMPORTER = ROOT / "scripts" / "import_legacy_shapers_alumni.py"
RUN = "global-shapers-legacy-intact-prefix"
PACKET_DIR = ROOT / "digs" / "wef" / RUN
REPORT_JSON = ROOT / "reports" / "wef-global-shapers-intact-prefix.json"
REPORT_MD = ROOT / "reports" / "wef-global-shapers-intact-prefix.md"
CITY_SEEDS = ROOT / "imports" / "global-shapers" / "retained-city-seeds.txt"
MINIMUM_PEOPLE = 2700
EXPECTED_OBSERVED_PEOPLE = 2736
HUB_RE = re.compile(
    r"(?P<city>[A-ZÀ-ÖØ-Þ][A-Za-zÀ-ÖØ-öø-ÿ'’.()\-–—/ ]{1,80}?)\s+Hub\b"
)
LEGACY_HUB_RE = re.compile(r"/hubs/(?P<slug>[a-z0-9][a-z0-9-]{1,90})", re.I)


def ascii_slug(value: str) -> str:
    text = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", text.casefold()).strip("-")


def clean_city(value: str) -> str | None:
    value = " ".join(value.replace("\u00a0", " ").split()).strip(" ,;:–—-|/")
    if not value or len(value) < 2 or len(value) > 82:
        return None
    if sum(character.isalpha() for character in value) < 2:
        return None
    folded = value.casefold()
    if any(
        token in folded
        for token in ("global shapers community", "world economic forum", "annual report")
    ):
        return None
    return value


def iter_strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from iter_strings(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from iter_strings(item)


def extract_cities(rows: Iterable[list[Any]]) -> list[str]:
    values: dict[str, str] = {}
    for row in rows:
        for text in iter_strings(row):
            for match in HUB_RE.finditer(" ".join(text.split())):
                city = clean_city(match.group("city"))
                if city:
                    values.setdefault(ascii_slug(city), city)
            for match in LEGACY_HUB_RE.finditer(text):
                city = clean_city(
                    " ".join(
                        word.capitalize()
                        for word in match.group("slug").removesuffix("-hub").split("-")
                    )
                )
                if city:
                    values.setdefault(ascii_slug(city), city)
    return [values[key] for key in sorted(values)]


def read_encoded(parts: Path) -> tuple[str, list[dict[str, Any]]]:
    paths = sorted(parts.glob("part-*"))
    if not paths:
        raise RuntimeError(f"no retained transport parts found under {parts}")
    records: list[dict[str, Any]] = []
    chunks: list[str] = []
    for path in paths:
        chunk = "".join(path.read_text(encoding="utf-8").split())
        chunks.append(chunk)
        records.append(
            {
                "path": str(path.relative_to(ROOT)),
                "characters": len(chunk),
                "sha256": hashlib.sha256(chunk.encode()).hexdigest(),
            }
        )
    return "".join(chunks), records


def decode_until_xz_error(encoded: str) -> tuple[bytes, dict[str, Any]]:
    data_end = len(encoded.rstrip("="))
    repaired_length_only = encoded[:data_end] + "A" + encoded[data_end:]
    compressed = base64.b64decode(repaired_length_only, validate=True)
    decompressor = lzma.LZMADecompressor(format=lzma.FORMAT_XZ)
    output: list[bytes] = []
    consumed = 0
    error = ""
    for offset, byte in enumerate(compressed):
        try:
            output.append(decompressor.decompress(bytes([byte])))
            consumed = offset + 1
        except lzma.LZMAError as exc:
            error = f"{type(exc).__name__}: {exc}"
            consumed = offset
            break
    payload = b"".join(output)
    if not payload:
        raise RuntimeError("truncated XZ stream did not yield decompressed bytes")
    return payload, {
        "encoded_characters": len(encoded),
        "encoded_data_characters": data_end,
        "compressed_bytes": len(compressed),
        "compressed_bytes_consumed": consumed,
        "decompressed_bytes_before_error": len(payload),
        "xz_eof": decompressor.eof,
        "xz_error": error,
        "length_repair_character": "A",
        "length_repair_position": data_end,
    }


def parse_valid_jsonl_prefix(payload: bytes) -> tuple[list[list[Any]], bytes, dict[str, Any]]:
    rows: list[list[Any]] = []
    accepted: list[bytes] = []
    ids: set[str] = set()
    byte_offset = 0
    failure: dict[str, Any] = {"kind": "end-of-payload", "byte_offset": len(payload)}

    for physical_line, raw_line in enumerate(payload.splitlines(keepends=True), 1):
        line_start = byte_offset
        byte_offset += len(raw_line)
        if not raw_line.endswith(b"\n"):
            failure = {
                "kind": "partial-line",
                "physical_line": physical_line,
                "byte_offset": line_start,
                "bytes": len(raw_line),
            }
            break
        try:
            text = raw_line.decode("utf-8")
        except UnicodeDecodeError as exc:
            failure = {
                "kind": "invalid-utf8",
                "physical_line": physical_line,
                "byte_offset": line_start + exc.start,
                "error": str(exc),
            }
            break
        if not text.strip():
            accepted.append(raw_line)
            continue
        try:
            value = json.loads(text)
        except json.JSONDecodeError as exc:
            failure = {
                "kind": "invalid-json",
                "physical_line": physical_line,
                "byte_offset": line_start,
                "error": str(exc),
            }
            break
        if not isinstance(value, list) or len(value) != 12:
            failure = {
                "kind": "invalid-row-shape",
                "physical_line": physical_line,
                "byte_offset": line_start,
                "value_type": type(value).__name__,
                "field_count": len(value) if isinstance(value, list) else None,
            }
            break
        identifier = str(value[0])
        if identifier in ids:
            failure = {
                "kind": "duplicate-person-id",
                "physical_line": physical_line,
                "byte_offset": line_start,
                "person_id": identifier,
            }
            break
        ids.add(identifier)
        rows.append(value)
        accepted.append(raw_line)

    if len(rows) < MINIMUM_PEOPLE:
        raise RuntimeError(
            f"intact prefix yielded only {len(rows)} people; expected at least {MINIMUM_PEOPLE}; "
            f"first rejected record: {failure}"
        )

    prefix = b"".join(accepted)
    return rows, prefix, {
        "people": len(rows),
        "unique_ids": len(ids),
        "valid_jsonl_bytes": len(prefix),
        "rejected_suffix_bytes": len(payload) - len(prefix),
        "first_rejected_record": failure,
        "matches_previous_observation": len(rows) == EXPECTED_OBSERVED_PEOPLE,
    }


def write_compact(path: Path, rows: Iterable[list[Any]]) -> str:
    digest = hashlib.sha256()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            line = json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n"
            handle.write(line)
            digest.update(line.encode())
    return digest.hexdigest()


def chunk_packet(jsonl: Path, packet_dir: Path, chunk_size: int = 850_000) -> dict[str, Any]:
    payload = jsonl.read_bytes()
    lines = [line for line in payload.decode("utf-8").splitlines() if line.strip()]
    counts: dict[str, int] = {}
    for number, line in enumerate(lines, 1):
        document = json.loads(line)
        dtype = str(document.get("dtype") or "")
        counts[dtype] = counts.get(dtype, 0) + 1
        if not document.get("_id"):
            raise RuntimeError(f"canonical output line {number}: missing _id")
    compressed = gzip.compress(payload, compresslevel=9, mtime=0)
    encoded = base64.b64encode(compressed).decode("ascii")
    packet_dir.mkdir(parents=True, exist_ok=True)
    for old in packet_dir.glob("starintel-documents.jsonl*"):
        old.unlink()
    names: list[str] = []
    for index in range(0, len(encoded), chunk_size):
        name = f"starintel-documents.jsonl.gz.b64.part-{index // chunk_size:03d}"
        (packet_dir / name).write_text(
            encoded[index:index + chunk_size] + "\n", encoding="utf-8"
        )
        names.append(name)
    (packet_dir / "starintel-documents.jsonl.gz.b64.parts").write_text(
        "\n".join(names) + "\n", encoding="utf-8"
    )
    jsonl.unlink()
    return {
        "documents": len(lines),
        "counts_by_dtype": dict(sorted(counts.items())),
        "output_sha256": hashlib.sha256(payload).hexdigest(),
        "gzip_sha256": hashlib.sha256(compressed).hexdigest(),
        "base64_parts": names,
    }


def write_markdown(report: dict[str, Any]) -> None:
    REPORT_MD.write_text(
        "# Intact prefix of retained Global Shapers alumni transport\n\n"
        f"- Intact people recovered before corruption: **{report['prefix']['people']:,}**\n"
        f"- Canonical documents emitted: **{report['packet']['documents']:,}**\n"
        f"- Person documents: **{report['packet']['counts_by_dtype'].get('person', 0):,}**\n"
        f"- Relations: **{report['packet']['counts_by_dtype'].get('relation', 0):,}**\n"
        f"- XZ corruption begins after compressed byte: **{report['transport']['compressed_bytes_consumed']:,}**\n"
        f"- Valid JSONL bytes preserved: **{report['prefix']['valid_jsonl_bytes']:,}**\n"
        f"- First rejected record: `{report['prefix']['first_rejected_record']['kind']}`\n\n"
        "The retained transport is corrupted after this verified prefix. These rows are preserved as evidence-backed seeds; "
        "the missing alumni suffix is reconstructed from live and archived official Global Shapers pages.\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Salvage the intact JSONL prefix from the corrupted retained Global Shapers XZ/Base64 transport."
    )
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--parts", type=Path, default=PARTS)
    args = parser.parse_args()
    root = args.root.resolve()
    if root != ROOT:
        raise RuntimeError(f"runner must execute from repository root {ROOT}")

    work = ROOT / ".generated" / "legacy-global-shapers-prefix"
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)

    encoded, part_report = read_encoded(args.parts)
    decompressed, transport_report = decode_until_xz_error(encoded)
    rows, prefix_payload, prefix_report = parse_valid_jsonl_prefix(decompressed)
    transport_report["valid_jsonl_bytes"] = len(prefix_payload)
    compact = work / "intact-prefix.compact.jsonl"
    prefix_report["compact_sha256"] = write_compact(compact, rows)

    cities = extract_cities(rows)
    CITY_SEEDS.parent.mkdir(parents=True, exist_ok=True)
    CITY_SEEDS.write_text("".join(f"{city}\n" for city in cities), encoding="utf-8")
    prefix_report["city_seeds"] = len(cities)

    canonical = PACKET_DIR / "starintel-documents.jsonl"
    canonical.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            sys.executable,
            str(IMPORTER),
            str(compact),
            "--output",
            str(canonical),
            "--report",
            str(work / "canonical-import.json"),
        ],
        cwd=ROOT,
        check=True,
    )
    packet_report = chunk_packet(canonical, PACKET_DIR)
    if packet_report["counts_by_dtype"].get("person") != len(rows):
        raise RuntimeError(f"canonical person count mismatch: {packet_report['counts_by_dtype']}")

    report = {
        "status": "partial-intact-prefix",
        "dataset": "wef",
        "run": RUN,
        "source_parts": part_report,
        "source_encoded_sha256": hashlib.sha256(encoded.encode()).hexdigest(),
        "transport": transport_report,
        "prefix": prefix_report,
        "packet": packet_report,
        "packet_path": str(PACKET_DIR.relative_to(ROOT)),
        "missing_suffix_status": "requires-live-and-archive-reconstruction",
    }
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    write_markdown(report)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
