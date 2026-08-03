# FBI procurement collector

`scripts/scrape_fbi_procurement.py` collects raw, source-attributed procurement evidence from official public systems. It does **not** write to the canonical StarIntel database.

## Sources

| Source | Collection |
|---|---|
| FBI Business file repository | Repository item pages and downloadable public files, saved by SHA-256 |
| SAM.gov Opportunities API v2 | FBI notices partitioned into API-compliant one-year date windows and notice types |
| USAspending API | Exact award-ID searches and separate TSC keyword searches |

## Output

The default run writes:

```text
imports/fbi-procurement/
  raw.jsonl
  files/
    <sha256>.<extension>
```

Each JSONL row includes:

- source system;
- record type;
- official source URL;
- UTC retrieval time;
- SHA-256 of the source payload;
- parsed source payload or file metadata.

Downloaded FBI files use content-addressed names. Existing files are verified against their expected digest before reuse.

## Run FBI Business repository collection

```bash
python3 scripts/scrape_fbi_procurement.py \
  --source biz \
  --output imports/fbi-procurement/biz-raw.jsonl
```

The collector follows only same-host `/file-repository/.../view` pages, extracts direct public document links, waits one second between requests by default, and does not crawl the rest of `biz.fbi.gov`.

Limit a test pass:

```bash
python3 scripts/scrape_fbi_procurement.py \
  --source biz \
  --biz-max-items 5 \
  --biz-delay 1.0 \
  --output /tmp/fbi-biz-test.jsonl
```

## Run SAM.gov collection

The official Opportunities API requires a SAM.gov public API key. The key is read from the environment and never written to output.

```bash
export SAM_GOV_API_KEY='...'
python3 scripts/scrape_fbi_procurement.py \
  --source sam \
  --posted-from 2025-01-01 \
  --posted-to 2026-08-03 \
  --output imports/fbi-procurement/sam-raw.jsonl
```

Restrict notice types:

```bash
python3 scripts/scrape_fbi_procurement.py \
  --source sam \
  --sam-ptype r \
  --sam-ptype a \
  --posted-from 2025-01-01 \
  --posted-to 2026-08-03
```

Common SAM.gov notice codes used by the collector:

- `r` — sources sought;
- `p` — presolicitation;
- `o` — solicitation;
- `k` — combined synopsis/solicitation;
- `a` — award notice;
- `u` — justification and approval;
- `s` — special notice.

## Run USAspending collection

```bash
python3 scripts/scrape_fbi_procurement.py \
  --source usaspending \
  --award-id 15F06725F0001209 \
  --award-id 15F06725F0001838 \
  --keyword 'terrorist screening center' \
  --keyword 'threat screening center' \
  --posted-from 2020-01-01 \
  --posted-to 2026-08-03 \
  --output imports/fbi-procurement/usaspending-raw.jsonl
```

Exact award IDs and keyword searches are executed separately and then deduplicated. This avoids requiring an award to satisfy both an exact identifier and a keyword filter.

## Full run

```bash
export SAM_GOV_API_KEY='...'
python3 scripts/scrape_fbi_procurement.py \
  --source all \
  --posted-from 2020-01-01 \
  --posted-to 2026-08-03
```

Without `SAM_GOV_API_KEY`, an `all` run logs a warning and continues with the FBI Business repository and USAspending. A SAM-only run fails closed when the key is missing.

## Validation

```bash
python3 -m unittest tests.test_scrape_fbi_procurement -v
python3 -m compileall -q scripts/scrape_fbi_procurement.py
python3 scripts/validate-for-merge.py --site
```

## Evidence boundary

Raw collection is not attribution. A company appearing in an FBI forecast, awardee list, industry-day registration list, SAM notice, or USAspending result is not automatically a bidder or respondent for another requirement. Promotion into canonical StarIntel records requires source-specific role evidence and schema validation.
