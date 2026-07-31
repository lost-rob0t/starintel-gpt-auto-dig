#!/usr/bin/env python3
from __future__ import annotations

import json
import re

import membership_list_surface_candidates as base

ALUMNI_ROOTS = {
    "alumni", "alumnae", "alumnus", "graduates", "graduate", "cohorts", "cohort",
    "classes", "class", "former-members", "past-members", "past-participants",
    "former-fellows", "past-fellows", "honorees", "awardees", "laureates",
}
ALUMNI_SLUGS = {
    "alumni-directory", "alumni-list", "alumni-network", "alumni-community",
    "all-alumni", "our-alumni", "meet-the-alumni", "former-members",
    "past-members", "former-fellows", "past-fellows", "past-participants",
    "cohort-directory", "class-directory", "graduate-directory",
}
ALUMNI_TOKEN_RE = re.compile(
    r"(?:^|[-_])(?:alumni|alumnae|alumnus|graduates?|cohorts?|classes?|"
    r"former[-_]?(?:members?|fellows?|participants?)|past[-_]?(?:members?|fellows?|participants?)|"
    r"honorees?|awardees?|laureates?)(?:$|[-_\d])",
    re.IGNORECASE,
)
ALUMNI_TEXT_RE = re.compile(
    r"\b(?:alumni|alumnae|alumnus|graduates?|former members?|past members?|"
    r"former fellows?|past fellows?|past participants?|alumni (?:directory|list|network|community)|"
    r"cohort (?:directory|list|roster)|class (?:directory|list|roster|of \d{4})|"
    r"honorees? (?:directory|list|roster)|awardees? (?:directory|list|roster))\b",
    re.IGNORECASE,
)

base.PROFILE_ROOTS.update(ALUMNI_ROOTS)
base.LIST_ROOTS.update(ALUMNI_ROOTS)
base.LIST_SLUGS.update(ALUMNI_SLUGS)
_original_listish = base.listish_segment
_original_qualifies = base.qualifies
_original_self_test = base.run_self_test


def listish_segment(segment: str) -> bool:
    return _original_listish(segment) or bool(ALUMNI_TOKEN_RE.search(segment))


def qualifies(url: str, evidence: str) -> bool:
    if base.is_profile_path(url):
        return False
    return _original_qualifies(url, evidence) or bool(ALUMNI_TEXT_RE.search(evidence))


base.listish_segment = listish_segment
base.qualifies = qualifies


def run_self_test() -> None:
    _original_self_test()
    accepted = [
        "https://example.org/alumni",
        "https://example.org/alumni-directory",
        "https://example.org/fellows/former-fellows",
        "https://example.org/program/cohort-2024",
        "https://example.org/classes/class-of-1998",
        "https://example.org/past-participants?page=4",
    ]
    rejected = [
        "https://example.org/alumni/jane-doe",
        "https://example.org/graduates/john-smith",
        "https://example.org/profile/alumna-name",
    ]
    for url in accepted:
        assert base.is_list_path(url) or qualifies(url, "Official alumni directory and cohort roster"), url
    for url in rejected:
        assert not qualifies(url, "Official alumni directory and cohort roster"), url
    print(json.dumps({"alumni_accepted": accepted, "alumni_rejected": rejected}, indent=2))


base.run_self_test = run_self_test

if __name__ == "__main__":
    raise SystemExit(base.main())
