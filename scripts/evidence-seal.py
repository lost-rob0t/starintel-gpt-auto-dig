#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from starintel_doc.integrity import (
    build_corpus_inclusion_proof,
    build_corpus_seal,
    verify_corpus_seal,
    verify_inclusion_proof,
)
from starintel_doc.integrity_site import publish_site_seal


def load_object(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def write_object(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def cmd_create(args: argparse.Namespace) -> int:
    receipt = build_corpus_seal(args.corpus, include_entries=args.include_entries)
    if args.output:
        write_object(args.output, receipt)
    else:
        print(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    result = verify_corpus_seal(args.corpus, load_object(args.receipt))
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    elif result["ok"]:
        print(
            "VERIFIED "
            f"records={result['actual']['leaf_count']} "
            f"merkle_root_sha256={result['actual']['merkle_root_sha256']}"
        )
    else:
        for error in result["errors"]:
            print(f"ERROR: {error}", file=sys.stderr)
    return 0 if result["ok"] else 1


def cmd_prove(args: argparse.Namespace) -> int:
    proof = build_corpus_inclusion_proof(args.corpus, args.document_id)
    if args.receipt:
        receipt = load_object(args.receipt)
        expected = receipt.get("merkle_root_sha256")
        if proof["merkle_root_sha256"] != expected:
            raise ValueError(
                "corpus root does not match the supplied receipt: "
                f"{proof['merkle_root_sha256']} != {expected}"
            )
    if args.output:
        write_object(args.output, proof)
    else:
        print(json.dumps(proof, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def cmd_verify_proof(args: argparse.Namespace) -> int:
    expected_root = ""
    if args.receipt:
        expected_root = str(load_object(args.receipt).get("merkle_root_sha256", ""))
    result = verify_inclusion_proof(load_object(args.proof), expected_root=expected_root)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    elif result["ok"]:
        print(f"VERIFIED merkle_root_sha256={result['merkle_root_sha256']}")
    else:
        for error in result["errors"]:
            print(f"ERROR: {error}", file=sys.stderr)
    return 0 if result["ok"] else 1


def cmd_publish(args: argparse.Namespace) -> int:
    receipt = publish_site_seal(args.corpus, args.site_root)
    print(
        "PUBLISHED "
        f"records={receipt['leaf_count']} "
        f"merkle_root_sha256={receipt['merkle_root_sha256']}"
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create and verify StarIntel cryptographic evidence seals"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    command = sub.add_parser("create", help="seal one canonical JSONL corpus")
    command.add_argument("corpus", type=Path)
    command.add_argument("--output", type=Path)
    command.add_argument("--include-entries", action="store_true")
    command.set_defaults(func=cmd_create)

    command = sub.add_parser("verify", help="verify a JSONL corpus against a seal receipt")
    command.add_argument("corpus", type=Path)
    command.add_argument("receipt", type=Path)
    command.add_argument("--json", action="store_true")
    command.set_defaults(func=cmd_verify)

    command = sub.add_parser("prove", help="generate a portable inclusion proof for one record")
    command.add_argument("corpus", type=Path)
    command.add_argument("document_id")
    command.add_argument("--receipt", type=Path)
    command.add_argument("--output", type=Path)
    command.set_defaults(func=cmd_prove)

    command = sub.add_parser("verify-proof", help="verify one portable inclusion proof")
    command.add_argument("proof", type=Path)
    command.add_argument("--receipt", type=Path)
    command.add_argument("--json", action="store_true")
    command.set_defaults(func=cmd_verify_proof)

    command = sub.add_parser("publish", help="publish a site receipt and verification page")
    command.add_argument("corpus", type=Path)
    command.add_argument("site_root", type=Path)
    command.set_defaults(func=cmd_publish)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return int(args.func(args))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
