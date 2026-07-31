from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import alumni_membership_list_surface_candidates as alumni
from patch_alumni_scraper import patch_source


class AlumniRosterPipelineTests(unittest.TestCase):
    def test_classifier_accepts_archive_lists_and_rejects_profiles(self) -> None:
        accepted = [
            "https://example.org/alumni",
            "https://example.org/alumni-directory",
            "https://example.org/former-fellows",
            "https://example.org/program/cohort-2024",
            "https://example.org/classes/class-of-1998",
            "https://example.org/past-participants?page=3",
        ]
        rejected = [
            "https://example.org/alumni/jane-doe",
            "https://example.org/graduates/john-smith",
            "https://example.org/profile/former-fellow-name",
        ]
        for url in accepted:
            self.assertTrue(
                alumni.base.is_list_path(url)
                or alumni.qualifies(url, "Official alumni directory cohort roster"),
                url,
            )
        for url in rejected:
            self.assertFalse(alumni.qualifies(url, "Official alumni directory cohort roster"), url)

    def test_scraper_patch_creates_historical_relations(self) -> None:
        fixture = '''ROLE_KEYWORDS = {
    "member": "member_of",
}

            f"Recursive target to enumerate public leadership, boards, advisory groups, fellows, experts, and explicitly published work contacts for {name}.",
                    "query": f"{name} official leadership board team members fellows advisors directory",
                    "objectives": ["enumerate official public rosters", "capture explicitly published work contacts", "resolve cross-dataset ties"],
        relation_suffix = ''
        if record.role_category == 'participant':
            year_match = re.search(r'/(?:meeting-)?(19|20)\\d{2}/|participants-(19|20)\\d{2}', record.source_url)
            year = re.search(r'(19|20)\\d{2}', record.source_url)
            relation_suffix = '-' + (year.group(0) if year else hashlib.sha256(record.source_url.encode()).hexdigest()[:10])
        relation = {"subject": person_id, "predicate": predicate, "object": org_id, "directed": True, "inverse_predicate": "has_publicly_listed_person", "relation_type": record.role_category, "qualifiers": {"published_role": record.role, "source_page": record.source_url, "coverage_status": record.coverage_status}, "confidence": 0.98, "active": True},
'''
        patched = patch_source(fixture)
        self.assertIn('"alumni": "alumnus_of"', patched)
        self.assertIn('"former member": "former_member_of"', patched)
        self.assertIn("relation_qualifiers['cohort']", patched)
        self.assertIn('"active": not historical', patched)
        self.assertIn("complete alumni/cohort archives", patched)


if __name__ == "__main__":
    unittest.main()
