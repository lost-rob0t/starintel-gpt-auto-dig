#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
from pathlib import Path
import re
import runpy
import sys
import threading
from typing import Any

TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.I | re.S)
H1_RE = re.compile(r"<h1[^>]*>(.*?)</h1>", re.I | re.S)
TAG_RE = re.compile(r"<[^>]+>")
SPACE_RE = re.compile(r"\s+")


def clean_html_text(value: str) -> str:
    value = TAG_RE.sub(" ", value)
    value = html.unescape(value)
    return SPACE_RE.sub(" ", value).strip()[:500]


def extract_page_labels(response: Any) -> tuple[str, str]:
    content_type = str(response.headers.get("content-type", "")).lower()
    if "html" not in content_type:
        return "", ""
    try:
        text = response.text[:2_000_000]
    except Exception:
        return "", ""
    title_match = TITLE_RE.search(text)
    h1_match = H1_RE.search(text)
    title = clean_html_text(title_match.group(1)) if title_match else ""
    heading = clean_html_text(h1_match.group(1)) if h1_match else ""
    return title, heading


def install_capture(log_path: Path, source_script: str) -> None:
    import requests

    log_path.parent.mkdir(parents=True, exist_ok=True)
    lock = threading.Lock()
    original = requests.sessions.Session.request

    def write(record: dict[str, Any]) -> None:
        with lock:
            with log_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")

    def captured(self: Any, method: str, url: str, *args: Any, **kwargs: Any) -> Any:
        started = dt.datetime.now(dt.timezone.utc)
        try:
            response = original(self, method, url, *args, **kwargs)
        except Exception as exc:
            write(
                {
                    "observed_at": started.isoformat().replace("+00:00", "Z"),
                    "source_script": source_script,
                    "method": str(method).upper(),
                    "requested_url": str(url),
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )
            raise

        title, heading = extract_page_labels(response)
        write(
            {
                "observed_at": started.isoformat().replace("+00:00", "Z"),
                "source_script": source_script,
                "method": str(method).upper(),
                "requested_url": str(url),
                "final_url": str(getattr(response, "url", url)),
                "status_code": int(getattr(response, "status_code", 0) or 0),
                "content_type": str(response.headers.get("content-type", "")),
                "title": title,
                "heading": heading,
            }
        )
        return response

    requests.sessions.Session.request = captured


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a Python scraper while recording every HTTP URL it encounters."
    )
    parser.add_argument("--log", required=True, type=Path)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if args.command and args.command[0] == "--":
        args.command = args.command[1:]
    if not args.command:
        parser.error("a Python script and its arguments are required after --")
    return args


def main() -> int:
    args = parse_args()
    script = Path(args.command[0]).resolve()
    if not script.is_file():
        raise SystemExit(f"scraper script not found: {script}")

    install_capture(args.log.resolve(), str(script))
    old_argv = sys.argv
    old_cwd = Path.cwd()
    try:
        sys.argv = [str(script), *args.command[1:]]
        os.chdir(old_cwd)
        runpy.run_path(str(script), run_name="__main__")
    except SystemExit as exc:
        if exc.code is None:
            return 0
        if isinstance(exc.code, int):
            return exc.code
        print(exc.code, file=sys.stderr)
        return 1
    finally:
        sys.argv = old_argv
        os.chdir(old_cwd)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
