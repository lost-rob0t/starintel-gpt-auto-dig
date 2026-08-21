#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

import dark_academia_memberships_core as _core

# Preserve the public surface of the original scraper while keeping this entrypoint
# small enough to isolate organization-specific parser corrections.
for _name in dir(_core):
    if not _name.startswith("_"):
        globals().setdefault(_name, getattr(_core, _name))

_BILDERBERG_ENTRY_RE = re.compile(
    r"^(.+?)\s*\(((?:[A-Z]{3})(?:/[A-Z]{3})*)\),\s*(.+)$"
)
_BILDERBERG_COUNTRY_MARKER_RE = re.compile(r"\([A-Z]{3}(?:/[A-Z]{3})*\),")


class Scraper(_core.Scraper):
    @classmethod
    def _bilderberg_node_text(cls, node: Any) -> str:
        parts = [cls.clean_text(str(part)) for part in node.stripped_strings]
        parts = [part for part in parts if part]
        if not parts:
            return ""

        merged = parts[0]
        for part in parts[1:]:
            if (
                part[0] in ",.;:!?)]}"
                or merged[-1] in "([{/'\""
                or (merged[-1].isalpha() and part[0].islower())
            ):
                merged += part
            else:
                merged += " " + part
        return cls.clean_text(merged)

    def _bilderberg_rows(self, soup: BeautifulSoup) -> list[str]:
        rows: list[str] = []
        seen: set[str] = set()

        # Participant entries are rendered as block elements whose role/affiliation
        # text may be split across nested spans. Reconstruct the block text before
        # parsing instead of treating every text node as a separate roster row.
        for node in soup.find_all(("p", "li", "tr", "article", "div")):
            text = self._bilderberg_node_text(node)
            if not text or len(_BILDERBERG_COUNTRY_MARKER_RE.findall(text)) != 1:
                continue
            if _BILDERBERG_ENTRY_RE.match(text) is None or text in seen:
                continue
            rows.append(text)
            seen.add(text)

        if rows:
            return rows

        # Conservative fallback for older pages that expose bare text separated by
        # line breaks. Join continuation fragments until the next participant row.
        current: list[str] = []
        for raw in soup.stripped_strings:
            line = self.clean_text(str(raw))
            if not line:
                continue
            if _BILDERBERG_ENTRY_RE.match(line):
                if current:
                    row = self.clean_text(" ".join(current))
                    if _BILDERBERG_ENTRY_RE.match(row) and row not in seen:
                        rows.append(row)
                        seen.add(row)
                current = [line]
                continue
            if current:
                current.append(line)

        if current:
            row = self.clean_text(" ".join(current))
            if _BILDERBERG_ENTRY_RE.match(row) and row not in seen:
                rows.append(row)
        return rows

    def extract_bilderberg(self, target: dict[str, Any], url: str) -> list[PersonRecord]:
        text, status, final = self.fetch(url)
        if status != 200:
            return []

        soup = BeautifulSoup(text, "lxml")
        title = self.clean_text(
            soup.title.string if soup.title and soup.title.string else f"{target['name']} participants"
        )
        records: list[PersonRecord] = []
        for row in self._bilderberg_rows(soup):
            match = _BILDERBERG_ENTRY_RE.match(row)
            if match is None:
                continue
            raw_name, country, role = match.groups()
            if "," in raw_name:
                last, first = [self.clean_text(value) for value in raw_name.split(",", 1)]
                name = f"{first} {last}".strip()
            else:
                name = self.clean_text(raw_name)
            role = self.clean_text(role)
            if not self.looks_like_name(name) or not role:
                continue
            records.append(
                PersonRecord(
                    dataset=target["dataset"],
                    name=name,
                    role=role,
                    organization_name=target["name"],
                    organization_id=target.get("org_id", f"starintel:org:{target['dataset']}"),
                    source_url=final,
                    source_title=title,
                    role_category="participant",
                    country=country,
                )
            )
        return records

    def relation_predicate(self, record: PersonRecord) -> str:
        if self.clean_text(record.role_category).casefold() == "participant":
            return "participant_in"
        return super().relation_predicate(record)


def main() -> int:
    _core.Scraper = Scraper
    return _core.main()


if __name__ == "__main__":
    raise SystemExit(main())
