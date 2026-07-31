#!/usr/bin/env python3
from __future__ import annotations

import html
from urllib.parse import urlsplit

import sync_membership_list_issues as base


def issue_body(candidate: dict) -> str:
    digest = str(candidate["digest"])
    organization = str(candidate.get("organization") or "unresolved")
    dataset = str(candidate.get("dataset") or "unresolved")
    label = str(candidate.get("label") or "unresolved")
    source = str(candidate.get("discovered_from") or "unknown")
    evidence = str(candidate.get("evidence") or "")[:1200]
    url = str(candidate["url"])
    return f"""<!-- membership-list-url-sha256:{digest} -->
## Membership and alumni roster scraper target

- **Organization:** {organization}
- **Dataset:** `{dataset}`
- **URL:** {url}
- **Page label:** {label}
- **Discovered from:** `{source}`

## Required parser work

- [ ] Verify this official public roster-list surface.
- [ ] Add or extend the organization-specific parser.
- [ ] Traverse every exposed year, cohort, class, archive, pagination route, region, and tab.
- [ ] Include alumni, former members, former fellows, graduates, honorees, and past participants when exposed.
- [ ] Preserve program, cohort/class, year range, role, region, organization, roster label, and source provenance.
- [ ] Represent historical records as sourced historical relations such as `alumnus_of`, `former_member_of`, `former_fellow_of`, or `participated_in`; do not mark them as current memberships.
- [ ] Reuse canonical person identities where evidence supports the match; retain unresolved identity distinctions otherwise.
- [ ] Record only contacts explicitly published by the organization.
- [ ] Import through the canonical StarIntel writer and validate the corpus.
- [ ] Add regression coverage for this URL and its historical archive traversal.

```text
{evidence}
```
"""


base.issue_body = issue_body

if __name__ == "__main__":
    raise SystemExit(base.main())
