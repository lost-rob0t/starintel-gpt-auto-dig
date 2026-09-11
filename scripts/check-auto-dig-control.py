#!/usr/bin/env python3
"""Fail closed unless the repository Auto-Dig control permits execution."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

CONTROL_SCHEMA = "auto-dig-control.v1"
DEFAULT_CONTROL = Path(__file__).resolve().parents[1] / "config" / "auto-dig-control.json"


def main() -> int:
    path = Path(os.environ.get("AUTO_DIG_CONTROL_FILE", str(DEFAULT_CONTROL)))
    try:
        control = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - fail-closed control boundary
        print(f"AUTO-DIG BLOCKED: cannot read valid control file {path}: {exc}", file=sys.stderr)
        return 3

    if control.get("schema") != CONTROL_SCHEMA:
        print(f"AUTO-DIG BLOCKED: invalid control schema in {path}", file=sys.stderr)
        return 3

    enabled = control.get("enabled") is True
    running = control.get("state") == "running"
    if not (enabled and running):
        reason = control.get("reason", "operator pause")
        print(f"AUTO-DIG PAUSED: {reason}")
        return 75

    print("AUTO-DIG ENABLED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
