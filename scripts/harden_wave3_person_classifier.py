#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
from pathlib import Path

START = "    def looks_like_name(self, value: str) -> bool:\n"
END = "\n    def jsonld_people"

REPLACEMENT = '''    def looks_like_name(self, value: str) -> bool:
        value = self.clean_text(value)
        if not 3 <= len(value) <= 100 or value.lower() in NAME_STOPWORDS:
            return False
        if any(ch in value for ch in "{}[]<>@") or re.search(r"https?://", value):
            return False
        words = [w for w in re.split(r"\\s+", value) if w]
        if not 2 <= len(words) <= 8:
            return False
        alpha = sum(ch.isalpha() for ch in value)
        if alpha < max(3, int(len(value) * 0.55)):
            return False

        # The public-professional corpus must prefer false negatives over false
        # identities. Generic page headings, topic labels, navigation text,
        # programs, and geographic surfaces are not evidence of a human.
        non_person_terms = {
            "about", "action", "affairs", "agreement", "agreements", "announcements",
            "artificial", "background", "board", "california", "careers", "center",
            "climate", "coalition", "committee", "communications", "conflict", "council",
            "development", "directors", "division", "donor", "donors", "economics",
            "education", "energy", "environment", "events", "executives", "explore",
            "fellows", "financial", "foundation", "global", "governance", "health",
            "history", "impact", "industry", "initiative", "institute", "institution",
            "institutional", "intelligence", "international", "jobs", "leadership",
            "media", "member", "members", "membership", "museum", "national", "network",
            "news", "nuclear", "office", "operations", "people", "policy", "press",
            "privacy", "profile", "profiles", "program", "project", "regional", "releases",
            "research", "researchers", "security", "services", "society", "staff",
            "statements", "strategy", "support", "sustainability", "team", "technology",
            "terms", "terrorism", "topic", "topics", "trustees", "university", "volunteers",
            "war", "weapons", "website", "what", "who", "you",
        }
        name_particles = {
            "al", "bin", "binti", "da", "das", "de", "del", "della", "den", "der",
            "di", "dos", "du", "el", "la", "le", "st", "van", "von",
        }
        suffixes = {"ii", "iii", "iv", "jr", "sr"}
        normalized = [re.sub(r"[^a-z]+", "", word.lower()) for word in words]
        if any(term in non_person_terms for term in normalized):
            return False

        name_like = 0
        for word, token in zip(words, normalized):
            if not token:
                continue
            if token in name_particles or token in suffixes:
                continue
            bare = word.strip(".,()[]{}")
            if len(token) == 1 and bare[:1].isalpha():
                name_like += 1
                continue
            hyphen_parts = bare.split("-")
            if (
                len(hyphen_parts) > 1
                and hyphen_parts[0].lower() in name_particles
                and all(part and part[:1].isupper() for part in hyphen_parts[1:])
            ):
                name_like += 1
                continue
            if bare[:1].isupper() or bare.isupper():
                name_like += 1
                continue
            return False
        return name_like >= 2
'''


def patch(path: Path) -> None:
    source = path.read_text(encoding="utf-8")
    try:
        start = source.index(START)
        end = source.index(END, start)
    except ValueError as exc:
        raise SystemExit(f"cannot locate looks_like_name implementation in {path}") from exc

    updated = source[:start] + REPLACEMENT + source[end:]
    if updated == source:
        raise SystemExit("classifier hardening produced no change")
    ast.parse(updated, filename=str(path))
    path.write_text(updated, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    patch(args.path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
