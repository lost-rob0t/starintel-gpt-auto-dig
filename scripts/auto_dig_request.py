#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

REQUEST_MARKER = "<!-- auto-dig-request:v1 -->"
KEY_PREFIX = "auto-dig:"


def _normalize(value: str) -> str:
    return " ".join(value.split()).strip().casefold()


def request_key(
    *,
    subject: str,
    goal: str,
    scope: str,
    completion: str,
    dedupe_key: str = "",
) -> str:
    """Return the stable v1 request fingerprint used by GitHub and hourly GPT runs."""
    if dedupe_key.strip():
        material = "manual\0" + _normalize(dedupe_key)
    else:
        material = "\0".join(
            (
                "v1",
                _normalize(subject),
                _normalize(goal),
                _normalize(scope),
                _normalize(completion),
            )
        )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()[:24]


def render_body(
    *,
    subject: str,
    goal: str,
    scope: str,
    seed_sources: str,
    constraints: str,
    completion: str,
    priority: str,
    dedupe_key: str = "",
) -> tuple[str, str]:
    key = request_key(
        subject=subject,
        goal=goal,
        scope=scope,
        completion=completion,
        dedupe_key=dedupe_key,
    )
    body = f"""{REQUEST_MARKER}

## Subject

{subject.strip()}

## Goal

{goal.strip()}

## Scope

{scope.strip()}

## Seed sources

{seed_sources.strip() or "None supplied."}

## Constraints

{constraints.strip() or "None supplied."}

## Completion criteria

{completion.strip()}

## Priority

{priority.strip() or "normal"}

## Auto-Dig identity

Request key: `{KEY_PREFIX}{key}`

This issue is a queued Auto-Dig research request. The hourly GPT run must drain open request issues before selecting autonomous free-range research.
"""
    return key, body


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render an idempotent Auto-Dig GitHub request.")
    parser.add_argument("--subject", required=True)
    parser.add_argument("--goal", required=True)
    parser.add_argument("--scope", required=True)
    parser.add_argument("--seed-sources", default="")
    parser.add_argument("--constraints", default="")
    parser.add_argument("--completion", required=True)
    parser.add_argument("--priority", default="normal")
    parser.add_argument("--dedupe-key", default="")
    parser.add_argument("--output", required=True)
    parser.add_argument("--github-output")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    key, body = render_body(
        subject=args.subject,
        goal=args.goal,
        scope=args.scope,
        seed_sources=args.seed_sources,
        constraints=args.constraints,
        completion=args.completion,
        priority=args.priority,
        dedupe_key=args.dedupe_key,
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(body, encoding="utf-8")

    if args.github_output:
        with Path(args.github_output).open("a", encoding="utf-8") as handle:
            handle.write(f"key={key}\n")
    else:
        print(key)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
