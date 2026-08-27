#!/usr/bin/env python3
"""Emission-boundary sanitizer and failure reporter for Auto-Dig.

Live RLM/MCP output can be streamed through this process so credentials are
removed before Actions or tee sees the line. Structured failure reports are
also sanitized before the Markdown file used for issue comments is written.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

REDACTED = "[REDACTED]"
SENSITIVE_KEY_RE = re.compile(
    r"(?:api[_-]?key|authorization|access[_-]?token|refresh[_-]?token|"
    r"bearer|password|passwd|secret|credential|private[_-]?key|token)$",
    re.IGNORECASE,
)

TEXT_PATTERNS = [
    re.compile(r"(?i)(authorization\s*[:=]\s*)(?:bearer\s+)?[^\s,;\]\}\)]+"),
    re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._~+/=-]{8,}"),
    re.compile(r"(?i)((?:api[_-]?key|access[_-]?token|refresh[_-]?token|token|secret|password)\s*[:=]\s*)[^\s,;\]\}\)]+"),
    re.compile(r"(?i)([?&](?:api[_-]?key|key|token|access_token)=)[^&#\s]+"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{8,}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{12,}\b"),
    re.compile(r"\bsk-or-v1-[A-Za-z0-9_-]{8,}\b"),
]

KNOWN_SECRET_ENV = (
    "OPENROUTER_API_KEY",
    "BRAVE_API_KEY",
    "PROLOG_RLM_BUG_TOKEN",
    "BUG_TOKEN",
    "GH_TOKEN",
    "GITHUB_TOKEN",
)


def known_secrets() -> list[str]:
    values = []
    for name in KNOWN_SECRET_ENV:
        value = os.environ.get(name)
        if value and len(value) >= 4:
            values.append(value)
    return sorted(set(values), key=len, reverse=True)


def redact_text(text: str) -> str:
    result = text
    for secret in known_secrets():
        result = result.replace(secret, REDACTED)
    for pattern in TEXT_PATTERNS:
        if pattern.groups:
            result = pattern.sub(lambda match: f"{match.group(1)}{REDACTED}", result)
        else:
            result = pattern.sub(REDACTED, result)
    return result


def sanitize(value: Any, key: str | None = None) -> Any:
    if key is not None and SENSITIVE_KEY_RE.search(key):
        return REDACTED
    if isinstance(value, dict):
        return {str(k): sanitize(v, str(k)) for k, v in value.items()}
    if isinstance(value, list):
        return [sanitize(v) for v in value]
    if isinstance(value, str):
        return redact_text(value)
    return value


def emit_sanitized_stream() -> int:
    """Write each input line only after sanitizing it."""
    for line in sys.stdin:
        sys.stdout.write(redact_text(line))
        sys.stdout.flush()
    return 0


def extract_error_envelope(result: Any) -> dict[str, Any] | None:
    if not isinstance(result, dict):
        return None
    payload = result.get("payload")
    if not isinstance(payload, dict) or payload.get("$term") != "error":
        return None
    args = payload.get("args")
    if not isinstance(args, list) or not args or not isinstance(args[0], dict):
        return None
    return args[0]


def load_json(path: Path | None) -> Any:
    if path is None or not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "phase": "diagnostics",
            "kind": "invalid_result_json",
            "message": redact_text(str(exc)),
        }


def stderr_tail(path: Path | None, max_lines: int) -> str:
    if path is None or not path.is_file():
        return "(no stderr/traceback captured)"
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    tail = "\n".join(lines[-max_lines:])
    return redact_text(tail) if tail else "(stderr was empty)"


def compact_summary(error: dict[str, Any] | None) -> str:
    if not error:
        return "phase=unknown kind=unknown"
    fields = []
    for key in ("phase", "kind", "message", "used", "limit"):
        if key in error:
            fields.append(f"{key}={redact_text(str(error[key]))}")
    usage = error.get("usage")
    if isinstance(usage, dict):
        for key in (
            "model_calls",
            "prompt_tokens",
            "completion_tokens",
            "total_tokens",
            "cost_usd",
        ):
            if key in usage:
                fields.append(f"{key}={usage[key]}")
    return " ".join(fields) if fields else "phase=unknown kind=unknown"


def render_report(result_path: Path | None, stderr_path: Path | None, max_lines: int) -> str:
    result = load_json(result_path)
    error = extract_error_envelope(result)
    if error is None and isinstance(result, dict) and result.get("phase") == "diagnostics":
        error = result
    safe_error = sanitize(error) if error is not None else None
    summary = compact_summary(safe_error)
    trace = stderr_tail(stderr_path, max_lines)

    sections = [
        "## Sanitized failure diagnostics",
        "",
        f"**Summary:** `{summary}`",
        "",
        "### Structured Prolog-RLM error",
        "",
        "```json",
        json.dumps(safe_error or {"phase": "unknown", "kind": "unknown"}, indent=2, sort_keys=True),
        "```",
        "",
        f"### Sanitized traceback / stderr tail (last {max_lines} lines)",
        "",
        "```text",
        trace,
        "```",
        "",
        "> Diagnostics are sanitized at emission time. Raw environment dumps and raw provider payloads are never included in issue-bound output.",
    ]
    return "\n".join(sections) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stream", action="store_true")
    parser.add_argument("--result", type=Path)
    parser.add_argument("--stderr", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--max-lines", type=int, default=120)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.stream:
        if args.result or args.stderr or args.output:
            raise SystemExit("--stream cannot be combined with report file arguments")
        return emit_sanitized_stream()

    if args.output is None:
        raise SystemExit("--output is required unless --stream is used")
    if args.max_lines < 1 or args.max_lines > 500:
        raise SystemExit("--max-lines must be between 1 and 500")

    report = render_report(args.result, args.stderr, args.max_lines)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
