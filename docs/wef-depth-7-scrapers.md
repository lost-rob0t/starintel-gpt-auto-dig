# WEF–Columbus Depth 7 scrapers

`wef_depth7_scrape.py` collects public evidence for the eight queued WEF dataset Depth 7 investigations. It writes raw, provenance-bearing observations. It does **not** write canonical `db/` documents; review and normalize the output through the repository import workflow.

## Enumeration

| Queue target | Collectors | Primary surfaces |
|---|---|---|
| HNTB executed files and workshare | Legistar, Auditor, site crawl | Matters, attachments, sponsors, modifications, purchase orders, invoices, utilization records |
| AndHealth compliance ledger | Legistar, Auditor, site crawl | Incentive ordinances, executed agreements, compliance reports, payment rows, worksheets |
| Green IT adoption roster | Legistar, site crawl, Wayback | Playbooks, meeting records, participant pages, adoption cases, archived Smart Columbus pages |
| Living Lab project identifiers | Legistar, site crawl, Wayback | Charters, vendor agreements, test sites, budgets, data terms, evaluation reports |
| UrbanOS deployment proof | GitHub, site crawl, Wayback | Forks, releases, deployments, workflows, deployment files, public operator documentation |
| Columbus Shapers archive | Site crawl, Wayback | Hub pages, curators, rosters, launch records, archived status notices |
| WEF–Columbus public records | Legistar, Auditor, site crawl, Wayback | MOUs, dues, invoices, travel, grants, correspondence, profile authorization |
| Smart Columbus project assignments | Legistar, site crawl, Wayback, GitHub | Staff pages, board pages, minutes, charters, grant reports, code ownership evidence |

The configuration lives at `scrapers/wef-depth-7.json`. Each target has its exact StarIntel investigation-target ID, collectors, keywords, official seed URLs, archive patterns, and repository queries.

## Architecture

The runner uses a small actor system:

- `CollectorActor` instances consume target/collector jobs concurrently.
- Source adapters perform blocking network collection in worker threads.
- `WriterActor` serializes and deduplicates observations by deterministic SHA-256 ID.
- The HTTP client rate-limits per host and checks `robots.txt` for site crawls by default.

Collectors are stdlib-only and run on Python 3.11. `GITHUB_TOKEN` is optional and is used only for public GitHub API rate limits.

## Commands

Enumerate all targets:

```bash
python3 scripts/wef_depth7_scrape.py --list
```

Print the 25 planned target/collector jobs without network access:

```bash
python3 scripts/wef_depth7_scrape.py --dry-run
```

Run all bounded metadata collectors:

```bash
python3 scripts/wef_depth7_scrape.py \
  --output imports/wef-depth-7/raw-observations.jsonl
```

Run one target against Legistar only:

```bash
python3 scripts/wef_depth7_scrape.py \
  --target starintel:investigation-target:wef-depth-7-andhealth-compliance-ledger \
  --collector legistar \
  --output imports/wef-depth-7/andhealth-legistar.jsonl
```

Download and scan public Columbus Auditor CSV/JSON datasets:

```bash
python3 scripts/wef_depth7_scrape.py \
  --collector auditor \
  --auditor-download \
  --auditor-hit-limit 500 \
  --output imports/wef-depth-7/auditor-hits.jsonl
```

Fetch archived page content and save matching documents:

```bash
python3 scripts/wef_depth7_scrape.py \
  --archive-content \
  --download-dir imports/wef-depth-7/documents \
  --output imports/wef-depth-7/archive-and-documents.jsonl
```

Use authenticated public GitHub API limits:

```bash
GITHUB_TOKEN="$(gh auth token)" \
python3 scripts/wef_depth7_scrape.py --collector github
```

## Output

Every JSONL row contains:

```text
observation_id, collector, target_id, kind, source_url,
retrieved_at, matched_keywords, match_count, payload_sha256, payload
```

`observation_id` is deterministic across identical collector, target, source URL, and payload combinations. The output file is rebuilt on each run and duplicate observations in that run are suppressed.

## Boundaries

- Public, unauthenticated records only, except an optional GitHub token for higher public API limits.
- No bypass of access controls, CAPTCHAs, or private systems.
- Site crawling honors `robots.txt` unless `--ignore-robots` is explicitly supplied.
- Default request delay is one second per host.
- Page, depth, archive, file-size, dataset-size, and result-count caps are enforced.
- Raw observations are leads and source captures, not automatically verified conclusions.

## Validation

```bash
python3 -m unittest -v tests/test_wef_depth7_scrape.py
python3 -m py_compile scripts/wef_depth7_scrape.py
python3 scripts/wef_depth7_scrape.py --dry-run
python3 scripts/validate-for-merge.py --site
```
