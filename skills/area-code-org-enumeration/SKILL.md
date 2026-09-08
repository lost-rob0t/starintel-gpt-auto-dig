---
name: area-code-org-enumeration
description: Enumerate public anarchist, anti-authoritarian, mutual-aid, autonomous and adjacent organizations across every valid U.S. geographic NANP area code and materialize each discovery as canonical StarIntel records.
---

# Area-Code Organization Enumeration

## Mission

Systematically cover the current set of valid U.S. geographic telephone area codes and find public organizations tied to each code or the localities served by it. This is a coverage workflow, not a one-off search.

The operator's selected investigation scope is authoritative. Preserve operator assessments separately from scraper-observed provenance.

## Area-code authority

Never invent NPAs and never iterate arbitrary `200..999` values.

At the start of a campaign or whenever the cached list is stale, obtain the current U.S. geographic NPA list from an authoritative source:

1. NANPA / national numbering-plan data and maps;
2. FCC NANP/area-code material as a corroborating authority.

Record the retrieval URL and timestamp. Use geographic NPAs by default; exclude toll-free and other non-geographic service codes unless the task explicitly asks for them. Preserve overlay codes as distinct valid NPAs even when they share a locality.

Maintain durable coverage state: `unsearched`, `searched-no-hit`, `searched-hit`, `needs-refresh`. Do not repeatedly search completed codes without new evidence or a refresh reason.

## Preferred tools

Use existing tools before writing new collectors.

- StarIntel corpus search: `python3 scripts/starintel.py search ...`
- Brave/web search MCP when available.
- Browser/fetch tooling for direct source inspection.
- `curl`/`wget` + `jq` for public structured endpoints and pages when appropriate.
- Internet Archive CDX/Wayback for dead historical organization pages.
- `yt-dlp` for public YouTube channel/video metadata.
- UserHunt/Sherlock-style username enumeration for public handle candidates.
- `gallery-dl` only when it materially helps collect public media/profile metadata.
- Existing platform actors/collectors whenever present; do not reimplement them inside the skill.

For X/Twitter and Reddit, do not use official APIs, paid developer access, OAuth application credentials, or official SDK authentication. Prefer public-web collectors, maintained OSS scrapers/frontends, archive sources and existing StarIntel actors. Bluesky may use public AT Protocol/AppView/XRPC access.

## High-value sites and directories

Search first-party/local pages whenever possible, then public directories and archives. Useful discovery surfaces include:

- Slingshot Radical Contact List / radical contact directories;
- A Radical Guide and similar public radical-space directories;
- It's Going Down public articles/event announcements for named organizations and local collectives;
- Black Rose / Rosa Negra public locals/chapters;
- Food Not Bombs public location listings;
- IWW public branch/industrial-union directories when relevant to adjacent local networks;
- Anarchist Black Cross / prisoner-support group public chapter or contact pages where current;
- public university/student-organization directories;
- local event calendars, public flyers, venue pages and co-sponsor lists;
- organization Linktree/Carrd/Beacons/bio.site/solo.to pages;
- public YouTube, Reddit, X/Nitter, Bluesky, Mastodon/Fediverse and GitHub pages;
- Internet Archive for retired/renamed local groups.

Directories are leads. Prefer the organization itself, a current public profile, or another primary source for confirmation.

## Query strategy per area code

For each valid NPA, resolve its current major localities and overlays, then use both numeric and locality searches. Examples:

```text
"614 anarchist"
"614 anarchists"
"614 anarchist collective"
"614 mutual aid"
"614 autonomous"
"614 anti-authoritarian"
"area code 614" anarchist
Columbus Ohio anarchist collective
Columbus Ohio autonomous group
Columbus Ohio mutual aid anarchist
site:linktr.ee Columbus anarchist
site:instagram.com Columbus anarchist collective
site:reddit.com Columbus anarchist
```

Repeat with relevant locality names, abbreviations, campus names, neighborhood names and historical group aliases. Search adjacent descriptors only when they are useful leads; preserve the source's own self-description rather than relabeling it.

## Discovery expansion

For every discovered public organization:

1. resolve canonical name plus aliases;
2. collect its public website and social handles;
3. identify city/state/region and any publicly listed phone area code;
4. find local/parent/affiliate/federation/chapter relationships;
5. find public events/co-sponsors that expose additional organizations;
6. cross-enumerate public handles on YouTube, X, Reddit, Bluesky and UserHunt-supported sites;
7. emit each directly related organization as its own investigation target;
8. queue newly discovered localities/area codes when they expose an uncovered edge.

Matching handles alone do not prove common ownership or identity. Preserve them as candidates unless stronger public evidence links them.

## StarIntel output — mandatory

Do not emit approximate "StarIntel-like" JSON. Use the executable repository schema and canonical writers.

Before every document class:

```bash
python3 scripts/starintel.py types
python3 scripts/starintel.py schema --dtype <dtype>
```

Use existing exact dtypes. A normal discovery should materialize, as supported by the current schema:

- `source` record(s) for pages/evidence;
- an `org` record for the organization;
- a separate `investigation-target` record for every discovered organization;
- account/user/social records when the current schema provides the correct dtype;
- `relation` records for chapter/affiliate/locality/event/account edges;
- a `research-pass` for method, coverage and unresolved work.

If the schema has no exact representation for a useful value, preserve it only through the schema-approved namespaced extension mechanism and open/follow the schema-change path. Never guess a data field.

Normalized DB writes MUST use:

```bash
python3 scripts/create-db-document.py <dtype> ...
# or
python3 scripts/starintel.py import records.jsonl
```

Never hand-edit `db/`.

Keep exact source URL, retrieval time, evidence state and uncertainty. Generate human-readable Org/site output from canonical records through the repository build path rather than treating prose Org files as data authority.

## Validation

Before completion:

```bash
python3 scripts/validate-for-merge.py --site
```

or the current Nim-first repository merge gate when available. Failing, skipped, missing or inconclusive validation is not success.
