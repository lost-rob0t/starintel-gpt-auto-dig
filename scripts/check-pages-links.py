#!/usr/bin/env python3
"""Fail when generated HTML references a missing internal page, asset or anchor."""

from __future__ import annotations

import argparse
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


class Collector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []
        self.ids: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        data = dict(attrs)
        if value := data.get("id"):
            self.ids.add(value)
        for key in ("href", "src"):
            if value := data.get(key):
                self.links.append(value)


def parse(path: Path) -> Collector:
    collector = Collector()
    collector.feed(path.read_text(encoding="utf-8"))
    return collector


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("site", type=Path)
    args = parser.parse_args()
    site = args.site.resolve()

    html_files = sorted(site.rglob("*.html"))
    parsed = {path: parse(path) for path in html_files}
    errors: list[str] = []

    for source, page in parsed.items():
        for raw in page.links:
            parts = urlsplit(raw)
            if parts.scheme or parts.netloc or raw.startswith(("mailto:", "javascript:", "data:")):
                continue

            relative = unquote(parts.path)
            target = source if not relative else (source.parent / relative).resolve()
            try:
                target.relative_to(site)
            except ValueError:
                errors.append(f"{source.relative_to(site)}: escapes site root: {raw}")
                continue

            if target.is_dir():
                target = target / "index.html"
            if not target.exists():
                errors.append(f"{source.relative_to(site)}: missing target: {raw}")
                continue

            if parts.fragment and target.suffix.lower() == ".html":
                target_page = parsed.get(target)
                if target_page is None:
                    target_page = parse(target)
                    parsed[target] = target_page
                if unquote(parts.fragment) not in target_page.ids:
                    errors.append(
                        f"{source.relative_to(site)}: missing anchor {parts.fragment!r} in "
                        f"{target.relative_to(site)}"
                    )

    if errors:
        print("\n".join(f"ERROR: {error}" for error in errors))
        return 1

    print(f"validated {len(html_files)} HTML files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
