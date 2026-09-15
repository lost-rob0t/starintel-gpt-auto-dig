#!/usr/bin/env python3
from __future__ import annotations

import re
from typing import Any

from bs4 import BeautifulSoup

import dark_academia_memberships_impl as _impl
from dark_academia_memberships_impl import *  # noqa: F401,F403

PersonRecord = _impl.PersonRecord


class Scraper(_impl.Scraper):
    """Stable scraper entrypoint with parser hardening kept separate from the generated implementation."""

    def extract_bilderberg(self, target: dict[str, Any], url: str) -> list[PersonRecord]:
        text, status, final = self.fetch(
            url,
            respect_robots=not target.get("explicit_public_seeds", False),
        )
        if status != 200:
            return []

        soup = BeautifulSoup(text, "lxml")
        title = self.clean_text(
            soup.title.string
            if soup.title and soup.title.string
            else f"{target['name']} participants"
        )

        def parse_line(value: str) -> PersonRecord | None:
            line = self.clean_text(value)
            match = re.match(r"^(.+?)\s*\(([A-Z]{3}|INT)\),\s*(.+)$", line)
            if not match:
                return None
            raw_name, country, role = match.groups()
            if "," in raw_name:
                last, first = [self.clean_text(x) for x in raw_name.split(",", 1)]
                name = f"{first} {last}".strip()
            else:
                name = raw_name
            if not self.looks_like_name(name):
                return None
            return PersonRecord(
                dataset=target["dataset"],
                name=name,
                role=self.clean_text(role),
                organization_name=target["name"],
                organization_id=target.get(
                    "org_id",
                    f"starintel:org:{target['dataset']}",
                ),
                source_url=final,
                source_title=title,
                role_category="participant",
                country=country,
            )

        records: list[PersonRecord] = []
        for node in soup.select("p, li"):
            # Bilderberg participant pages sometimes split a single published
            # role across adjacent inline spans. Concatenating stripped strings
            # reconstructs split words; punctuation normalization restores the
            # separator space without inventing role text.
            line = "".join(node.stripped_strings)
            line = re.sub(r",(?=\S)", ", ", line)
            record = parse_line(line)
            if record:
                records.append(record)

        if records:
            return records

        # Preserve the older plain-text parser as a fallback for historical
        # pages whose participant rows are not wrapped in paragraph/list nodes.
        for line in soup.get_text("\n").splitlines():
            record = parse_line(line)
            if record:
                records.append(record)
        return records

    def relation_predicate(self, record: PersonRecord) -> str:
        # Participation in a dated Bilderberg roster is the source-backed
        # relation. A published role such as "Director" describes the person's
        # external job and must not change that roster relation to director_of.
        if record.role_category == "participant":
            return "participant_in"
        return super().relation_predicate(record)


_impl.Scraper = Scraper


def main() -> int:
    return _impl.main()


if __name__ == "__main__":
    raise SystemExit(main())
