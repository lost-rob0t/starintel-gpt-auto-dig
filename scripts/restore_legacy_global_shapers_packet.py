#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import gzip
import hashlib
import json
import lzma
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PARTS = ROOT / "imports" / ".wef-shapers-compact"
IMPORTER = ROOT / "scripts" / "import_legacy_shapers_alumni.py"
EXPECTED_PEOPLE = 4062
EXPECTED_DOCUMENTS = 12187
EXPECTED_OUTPUT_SHA256 = "82408fb3baa6d2fcbba1948801a26827ccdbf6e5b2a18685502a7ca70b2f070f"
RUN = "global-shapers-legacy-alumni-4062"
PACKET_DIR = ROOT / "digs" / "wef" / RUN
REPORT_JSON = ROOT / "reports" / "wef-global-shapers-alumni-import.json"
REPORT_MD = ROOT / "reports" / "wef-global-shapers-alumni-import.md"


def restore_source(target: Path) -> dict[str, Any]:
    part_paths = sorted(PARTS.glob("part-*"))
    if len(part_paths) != 8:
        raise RuntimeError(f"expected 8 retained compact parts, found {len(part_paths)}")
    encoded = "".join("".join(path.read_text(encoding="utf-8").split()) for path in part_paths)
    compressed = base64.b64decode(encoded, validate=True)
    if not compressed.startswith(b"\xfd7zXZ\x00"):
        raise RuntimeError("retained compact source is not an XZ stream")
    payload = lzma.decompress(compressed)
    lines = [line for line in payload.decode("utf-8").splitlines() if line.strip()]
    if len(lines) != EXPECTED_PEOPLE:
        raise RuntimeError(f"expected {EXPECTED_PEOPLE} retained people, decoded {len(lines)}")
    for number, line in enumerate(lines, 1):
        value = json.loads(line)
        if not isinstance(value, list) or len(value) != 12:
            raise RuntimeError(f"retained source line {number}: expected compact 12-field person row")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(payload if payload.endswith(b"\n") else payload + b"\n")
    return {
        "parts": len(part_paths),
        "encoded_sha256": hashlib.sha256(encoded.encode()).hexdigest(),
        "compressed_sha256": hashlib.sha256(compressed).hexdigest(),
        "source_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
        "people": len(lines),
    }


def chunk_transport(jsonl: Path, packet_dir: Path, chunk_size: int = 850_000) -> dict[str, Any]:
    payload = jsonl.read_bytes()
    output_sha = hashlib.sha256(payload).hexdigest()
    if output_sha != EXPECTED_OUTPUT_SHA256:
        raise RuntimeError(f"legacy canonical output digest mismatch: {output_sha}")
    lines = [line for line in payload.decode("utf-8").splitlines() if line.strip()]
    if len(lines) != EXPECTED_DOCUMENTS:
        raise RuntimeError(f"expected {EXPECTED_DOCUMENTS} canonical documents, found {len(lines)}")
    counts: dict[str, int] = {}
    for number, line in enumerate(lines, 1):
        document = json.loads(line)
        dtype = str(document.get("dtype") or "")
        counts[dtype] = counts.get(dtype, 0) + 1
        if not document.get("_id"):
            raise RuntimeError(f"canonical output line {number}: missing _id")
    if counts.get("person") != EXPECTED_PEOPLE:
        raise RuntimeError(f"canonical person count mismatch: {counts}")

    compressed = gzip.compress(payload, compresslevel=9, mtime=0)
    encoded = base64.b64encode(compressed).decode("ascii")
    for old in packet_dir.glob("starintel-documents.jsonl*"):
        old.unlink()
    names: list[str] = []
    for index in range(0, len(encoded), chunk_size):
        name = f"starintel-documents.jsonl.gz.b64.part-{index // chunk_size:03d}"
        (packet_dir / name).write_text(encoded[index:index + chunk_size] + "\n", encoding="utf-8")
        names.append(name)
    (packet_dir / "starintel-documents.jsonl.gz.b64.parts").write_text("\n".join(names) + "\n", encoding="utf-8")
    jsonl.unlink()
    return {
        "documents": len(lines),
        "counts_by_dtype": dict(sorted(counts.items())),
        "output_sha256": output_sha,
        "gzip_sha256": hashlib.sha256(compressed).hexdigest(),
        "base64_parts": names,
    }


def write_markdown(report: dict[str, Any]) -> None:
    counts = report["transport"]["counts_by_dtype"]
    REPORT_MD.write_text(
        "# Retained Global Shapers alumni import\n\n"
        f"- People: **{counts.get('person', 0):,}**\n"
        f"- Relations: **{counts.get('relation', 0):,}**\n"
        f"- Organizations: **{counts.get('org', 0):,}**\n"
        f"- Total canonical documents: **{report['transport']['documents']:,}**\n"
        f"- Canonical output SHA-256: `{report['transport']['output_sha256']}`\n"
        f"- Source rows restored: **{report['source']['people']:,}**\n\n"
        "These are retained legacy Global Shapers alumni records. The 12,187-document total contains 4,062 people and 8,124 relations; it does not represent 12,187 distinct people.\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Restore the retained 4,062-person Global Shapers corpus as a compressed StarIntel packet.")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    root = args.root.resolve()
    if root != ROOT:
        raise RuntimeError(f"runner must execute from repository root {ROOT}")

    work = root / ".generated" / "legacy-global-shapers"
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    source = work / "shapers_alumni.compact.jsonl"
    output = PACKET_DIR / "starintel-documents.jsonl"
    PACKET_DIR.mkdir(parents=True, exist_ok=True)
    source_report = restore_source(source)
    subprocess.run(
        [
            sys.executable,
            str(IMPORTER),
            str(source),
            "--output",
            str(output),
            "--report",
            str(work / "import-report.json"),
        ],
        cwd=root,
        check=True,
    )
    transport_report = chunk_transport(output, PACKET_DIR)
    report = {
        "dataset": "wef",
        "run": RUN,
        "packet": str(PACKET_DIR.relative_to(root)),
        "source": source_report,
        "transport": transport_report,
        "minimum_known_people": EXPECTED_PEOPLE,
        "status": "restored-retained-corpus",
    }
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
