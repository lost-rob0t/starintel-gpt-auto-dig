#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import py_compile


def replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one source anchor, found {count}")
    return source.replace(old, new, 1)


def patch_source(source: str) -> str:
    source = replace_once(
        source,
        '    "member": "member_of",\n',
        '    "alumni": "alumnus_of",\n'
        '    "alumnus": "alumnus_of",\n'
        '    "alumna": "alumnus_of",\n'
        '    "former fellow": "former_fellow_of",\n'
        '    "former member": "former_member_of",\n'
        '    "past fellow": "former_fellow_of",\n'
        '    "past member": "former_member_of",\n'
        '    "graduate": "alumnus_of",\n'
        '    "member": "member_of",\n',
        "role predicate map",
    )

    source = replace_once(
        source,
        "        relation_suffix = ''\n"
        "        if record.role_category == 'participant':\n"
        "            year_match = re.search(r'/(?:meeting-)?(19|20)\\d{2}/|participants-(19|20)\\d{2}', record.source_url)\n"
        "            year = re.search(r'(19|20)\\d{2}', record.source_url)\n"
        "            relation_suffix = '-' + (year.group(0) if year else hashlib.sha256(record.source_url.encode()).hexdigest()[:10])\n",
        "        relation_suffix = ''\n"
        "        historical_categories = {\n"
        "            'alumni', 'alumnus', 'alumna', 'graduate', 'former-member',\n"
        "            'former_member', 'former-fellow', 'former_fellow', 'past-member',\n"
        "            'past_member', 'past-fellow', 'past_fellow',\n"
        "        }\n"
        "        historical = record.role_category.lower().replace(' ', '-') in historical_categories\n"
        "        if record.role_category == 'participant' or historical:\n"
        "            year = re.search(r'(19|20)\\d{2}', record.source_url)\n"
        "            relation_suffix = '-' + (year.group(0) if year else hashlib.sha256(record.source_url.encode()).hexdigest()[:10])\n"
        "        cohort_year = re.search(r'(19|20)\\d{2}', record.source_url)\n"
        "        relation_qualifiers = {\n"
        "            'published_role': record.role,\n"
        "            'source_page': record.source_url,\n"
        "            'coverage_status': record.coverage_status,\n"
        "        }\n"
        "        if historical:\n"
        "            relation_qualifiers['historical_status'] = record.role_category\n"
        "            relation_qualifiers['current'] = False\n"
        "            if cohort_year:\n"
        "                relation_qualifiers['cohort'] = cohort_year.group(0)\n",
        "historical relation identity",
    )

    source = replace_once(
        source,
        '{"subject": person_id, "predicate": predicate, "object": org_id, "directed": True, "inverse_predicate": "has_publicly_listed_person", "relation_type": record.role_category, "qualifiers": {"published_role": record.role, "source_page": record.source_url, "coverage_status": record.coverage_status}, "confidence": 0.98, "active": True},',
        '{"subject": person_id, "predicate": predicate, "object": org_id, "directed": True, "inverse_predicate": "has_publicly_listed_person", "relation_type": record.role_category, "qualifiers": relation_qualifiers, "confidence": 0.98, "active": not historical},',
        "historical relation qualifiers",
    )

    source = replace_once(
        source,
        '            f"Recursive target to enumerate public leadership, boards, advisory groups, fellows, experts, and explicitly published work contacts for {name}.",',
        '            f"Recursive target to enumerate public leadership, boards, advisory groups, fellows, experts, complete alumni/cohort archives, and explicitly published work contacts for {name}.",',
        "partner target summary",
    )
    source = replace_once(
        source,
        '                    "query": f"{name} official leadership board team members fellows advisors directory",',
        '                    "query": f"{name} official leadership board team members fellows advisors alumni former members cohorts archive directory",',
        "partner target query",
    )
    source = replace_once(
        source,
        '                    "objectives": ["enumerate official public rosters", "capture explicitly published work contacts", "resolve cross-dataset ties"],',
        '                    "objectives": ["enumerate official current rosters", "enumerate every exposed alumni, former-member, cohort, and historical roster", "preserve cohort and year qualifiers", "capture explicitly published work contacts", "resolve cross-dataset ties"],',
        "partner target objectives",
    )
    return source


def main() -> int:
    parser = argparse.ArgumentParser(description="Patch the restored organization scraper for complete alumni and historical roster ingestion.")
    parser.add_argument("scraper", type=Path)
    args = parser.parse_args()

    path = args.scraper.resolve()
    source = path.read_text(encoding="utf-8")
    patched = patch_source(source)
    path.write_text(patched, encoding="utf-8")
    py_compile.compile(str(path), doraise=True)
    print(f"Patched alumni relation semantics in {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
