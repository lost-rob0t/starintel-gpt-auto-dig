#!/usr/bin/env python3
"""Resolve the immutable StarLang release. Downstream repositories cannot mint it."""
import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("command", choices=["current", "check", "next", "bump", "mint"])
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--to")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.command in {"bump", "mint", "next"}:
        parser.exit(2, "StarLang is the sole release authority; update and release star-lang, then repin scripts/sync-starintel-schema.py --commit <full-SHA>.\n")
    lock = json.loads((args.root / "schema/starintel-schema.lock.json").read_text())
    if args.command == "check":
        subprocess.run([sys.executable, str(ROOT / "scripts/sync-starintel-schema.py"), "--offline"], cwd=args.root, check=True)
        sys.path.insert(0, str(args.root))
        from starintel_doc.canonical import verify_runtime_release
        verify_runtime_release()
        print("StarLang consumer and runtime release locks are consistent")
    else:
        state = {key: lock[key] for key in ("canonical_repository", "canonical_commit", "release_version", "schema_version", "authority_library")}
        state["profile_version"] = state["release_version"]
        print(json.dumps(state, indent=2) if args.json else "\n".join(f"{key}={value}" for key, value in state.items()))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
