#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import json
import lzma
import re
import shutil
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from starintel_doc.store import read_transport
from starintel_doc.validation import validate_document
from starintel_site.builder import build_site
from starintel_site.model import slug


WEF_SHAPERS_IMPORT_PARTS = ROOT / "imports" / ".wef-shapers-compact"
WEF_SHAPERS_SOURCE_PARTS = ROOT / "imports" / ".wef-shapers-source"
WEF_SHAPERS_IMPORTER = ROOT / "scripts" / "import_legacy_shapers_alumni.py"
WEF_SHAPERS_EXPECTED_RECORDS = 12_187
WEF_SHAPERS_EXPECTED_SHA256 = "82408fb3baa6d2fcbba1948801a26827ccdbf6e5b2a18685502a7ca70b2f070f"


def load_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def normalize_document(path: Path) -> dict[str, Any]:
    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(lines) != 1:
        raise ValueError(f"{path}: expected exactly one non-empty NDJSON line")
    document = json.loads(lines[0])
    validate_document(document)
    return document


def infer_target(dataset: str, mappings: dict[str, str]) -> str:
    configured = mappings.get(dataset)
    if configured:
        return slug(configured)
    candidate = re.sub(r"-20\d{2}(?:-\d{2}-\d{2})?$", "", slug(dataset))
    return candidate or slug(dataset)


def filter_excluded(workspace: Path, config: dict[str, Any]) -> None:
    raw_ids = config.get("excluded_document_ids", [])
    if not isinstance(raw_ids, list):
        raise ValueError("site-config.json: excluded_document_ids must be a list")
    excluded = {str(value) for value in raw_ids}
    if not excluded:
        return
    paths = list(workspace.glob("*/*/starintel-documents.jsonl"))
    paths += list(workspace.glob("*/*/starintel-documents.jsonl.gz.b64"))
    paths += list(workspace.glob("*/*/starintel-documents.jsonl.gz.b64.parts"))
    handled: set[Path] = set()
    for path in sorted(paths):
        if path.parent in handled:
            continue
        handled.add(path.parent)
        preferred = path.parent / "starintel-documents.jsonl"
        selected = preferred if preferred.exists() else path
        documents = [json.loads(line) for line in read_transport(selected).splitlines() if line.strip()]
        kept = [document for document in documents if str(document.get("_id")) not in excluded]
        if kept:
            preferred.write_text(
                "".join(json.dumps(document, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n" for document in kept),
                encoding="utf-8",
            )
        elif preferred.exists():
            preferred.unlink()
        for candidate in path.parent.glob("starintel-documents.jsonl.gz.b64*"):
            candidate.unlink()


def decode_part_bundle(parts_dir: Path) -> str | None:
    parts = sorted(parts_dir.glob("part-*"))
    if not parts:
        return None
    raw = "".join(path.read_text(encoding="utf-8") for path in parts)
    encoded = "".join(raw.split())
    try:
        compressed = base64.b64decode(encoded, validate=True)
        return lzma.decompress(compressed).decode("utf-8")
    except (binascii.Error, lzma.LZMAError, UnicodeDecodeError):
        return raw


def parse_jsonl_payload(payload: str, source: Path) -> tuple[list[Any], str]:
    lines = [line for line in payload.splitlines() if line.strip()]
    if not lines:
        raise ValueError(f"{source}: decoded bundle is empty")
    values: list[Any] = []
    for number, line in enumerate(lines, 1):
        try:
            values.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"{source}:{number}: invalid decoded JSON: {exc}") from exc
    canonical = "".join(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
        for value in values
    )
    return values, canonical


def verify_wef_shapers_packet(packet: Path) -> None:
    payload = packet.read_text(encoding="utf-8")
    values, canonical = parse_jsonl_payload(payload, packet)
    if not all(isinstance(value, dict) for value in values):
        raise ValueError(f"{packet}: expected canonical StarIntel document objects")
    if len(values) != WEF_SHAPERS_EXPECTED_RECORDS:
        raise ValueError(
            f"{packet}: expected {WEF_SHAPERS_EXPECTED_RECORDS} records, found {len(values)}"
        )
    digest = hashlib.sha256(canonical.encode()).hexdigest()
    if digest != WEF_SHAPERS_EXPECTED_SHA256:
        raise ValueError(
            f"{packet}: expected sha256 {WEF_SHAPERS_EXPECTED_SHA256}, found {digest}"
        )
    packet.write_text(canonical, encoding="utf-8")


def materialize_wef_shapers_import(workspace: Path) -> None:
    packet_dir = workspace / "wef" / "db-wef-global-shapers-alumni"
    packet = packet_dir / "starintel-documents.jsonl"
    report = packet_dir / "import-report.json"

    compact_payload = decode_part_bundle(WEF_SHAPERS_IMPORT_PARTS)
    if compact_payload is not None:
        values, canonical = parse_jsonl_payload(compact_payload, WEF_SHAPERS_IMPORT_PARTS)
        if all(isinstance(value, dict) for value in values):
            packet_dir.mkdir(parents=True, exist_ok=True)
            packet.write_text(canonical, encoding="utf-8")
            verify_wef_shapers_packet(packet)
            return

    source_payload = decode_part_bundle(WEF_SHAPERS_SOURCE_PARTS)
    if source_payload is None:
        source_payload = compact_payload
    if source_payload is None:
        return

    values, canonical_source = parse_jsonl_payload(source_payload, WEF_SHAPERS_SOURCE_PARTS)
    if not all(isinstance(value, list) for value in values):
        raise ValueError("Bundled Global Shapers payload is neither canonical documents nor compact source rows")

    packet_dir.mkdir(parents=True, exist_ok=True)
    source = packet_dir / "legacy-shapers-alumni.jsonl"
    source.write_text(canonical_source, encoding="utf-8")
    subprocess.run(
        [
            sys.executable,
            str(WEF_SHAPERS_IMPORTER),
            str(source),
            "--output",
            str(packet),
            "--report",
            str(report),
        ],
        cwd=ROOT,
        check=True,
    )
    verify_wef_shapers_packet(packet)
    source.unlink()


def materialize_input(digs_root: Path, db_root: Path, workspace: Path, config: dict[str, Any]) -> None:
    if workspace.exists():
        shutil.rmtree(workspace)
    workspace.mkdir(parents=True)
    if digs_root.exists():
        shutil.copytree(digs_root, workspace, dirs_exist_ok=True)
    filter_excluded(workspace, config)

    mappings = config.get("database_targets", {})
    if not isinstance(mappings, dict):
        raise ValueError("site-config.json: database_targets must be an object")
    normalized_mappings = {str(key): str(value) for key, value in mappings.items()}
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    if db_root.exists():
        for path in sorted(db_root.glob("*/*.ndjson")):
            document = normalize_document(path)
            dataset = str(document.get("dataset") or "database")
            target = infer_target(dataset, normalized_mappings)
            grouped[(target, slug(dataset))].append(document)
    for (target, dataset), documents in grouped.items():
        packet = workspace / target / f"db-{dataset}" / "starintel-documents.jsonl"
        packet.parent.mkdir(parents=True, exist_ok=True)
        packet.write_text(
            "".join(
                json.dumps(document, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n"
                for document in sorted(documents, key=lambda item: str(item.get("_id", "")))
            ),
            encoding="utf-8",
        )
    materialize_wef_shapers_import(workspace)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a static StarIntel v0.9.0 research explorer.")
    parser.add_argument("--input", type=Path, default=Path("digs"))
    parser.add_argument("--db", type=Path, default=Path("db"))
    parser.add_argument("--output", type=Path, default=Path("_site"))
    parser.add_argument("--org-output", type=Path, default=Path(".generated/org"))
    parser.add_argument("--workspace", type=Path, default=Path(".generated/site-input"))
    parser.add_argument("--config", type=Path, default=Path("site-config.json"))
    parser.add_argument("--assets", type=Path, default=Path("site-assets"))
    args = parser.parse_args()
    try:
        config = load_config(args.config)
        materialize_input(args.input, args.db, args.workspace, config)
        build_site(args.workspace, args.output, args.org_output, args.config, args.assets)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"Built explorer at {args.output} and Org corpus at {args.org_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
