#!/usr/bin/env python3
"""Launch one explicit Auto-Dig task with the repository's OpenCode tools."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    task = parser.add_mutually_exclusive_group(required=True)
    task.add_argument("--task", help="bounded research question and scope")
    task.add_argument("--task-file", type=Path, help="UTF-8 task instructions")
    parser.add_argument("--model", help="OpenCode provider/model (otherwise use its default)")
    parser.add_argument("--opencode", default="opencode", help="OpenCode executable, not a shell command")
    parser.add_argument("--dry-run", action="store_true", help="print plan without launching any process or writing files")
    args = parser.parse_args(argv)
    try:
        task_text = args.task_file.read_text(encoding="utf-8") if args.task_file else args.task
        if not task_text.strip():
            parser.error("task must not be empty")
        control = json.loads((ROOT / "config/auto-dig-control.json").read_text())
        if not isinstance(control, dict) or control.get("schema") != "auto-dig-control.v1":
            raise ValueError("invalid Auto-Dig control schema")
        if control.get("enabled") is not True or control.get("state") != "running":
            print("Auto-Dig is paused; launcher blocked", file=sys.stderr)
            return 75
        for flag in ("allow_new_claims", "allow_new_passes"):
            if control.get(flag, True) is not True:
                print(f"Auto-Dig control denies {flag}", file=sys.stderr)
                return 75
        instructions = (ROOT / "docs/opencode-auto-dig-task.md").read_text(encoding="utf-8")
        prompt = instructions + "\n\nOperator task:\n" + task_text
        command = [args.opencode, "run", "--dir", str(ROOT)]
        if args.model:
            command += ["--model", args.model]
        command += ["--", prompt]
        if args.dry_run:
            print(json.dumps({"cwd": str(ROOT), "argv": command,
                              "config": str(ROOT / "opencode.jsonc"),
                              "required_environment": ["BRAVE_API_KEY", "provider credentials via OpenCode"]}, indent=2))
            return 0
        resolved = {}
        for executable in (args.opencode, "npx", "nimble"):
            location = shutil.which(executable)
            if not location:
                print(f"Missing prerequisite: {executable}; see docs/opencode-auto-dig.md", file=sys.stderr)
                return 127
            resolved[executable] = os.path.abspath(location)
        # Resolve in the caller's cwd/PATH before changing either for the child.
        command[0] = resolved[args.opencode]
        if not os.environ.get("BRAVE_API_KEY", "").strip():
            print("Missing BRAVE_API_KEY in runtime environment", file=sys.stderr)
            return 2
        # Check generated release and pinned Python/Nim runtimes before any agent work.
        status = subprocess.run([sys.executable, "scripts/schema-release.py", "check"], cwd=ROOT).returncode
        if status:
            return status
        # Keep the activated Python environment available to the agent's python3 calls.
        env = os.environ.copy()
        env["PATH"] = str(Path(sys.executable).parent) + os.pathsep + env.get("PATH", "")
        env["PWD"] = str(ROOT)
        # OpenCode uses PWD for session routing and appends piped stdin to tasks.
        # Both project selection and task content must come from this launcher.
        status = subprocess.run(command, cwd=ROOT, env=env, stdin=subprocess.DEVNULL).returncode
        return status if status >= 0 else 128 - status
    except (OSError, ValueError) as exc:
        print(f"Cannot launch Auto-Dig: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
