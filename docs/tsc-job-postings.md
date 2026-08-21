# Public TSC job-posting collector

`scripts/scrape_tsc_job_postings.py` preserves public contractor job postings that expose Threat Screening Center staffing, labor-category and mission evidence.

## Current source

The default source is Agile Defense's public Lever Postings API:

```text
https://api.lever.co/v0/postings/agile-defense?mode=json
```

The Postings API exposes published jobs without authentication. The collector does not access Lever's authenticated recruiting API, application questions, candidate records, resumes or applicant forms.

## Default matching

A posting is retained when its public text matches a configured mission phrase or its public location matches Vienna, Virginia.

Default mission phrases include:

- threat screening;
- identity resolution;
- intelligence analysis;
- information sharing;
- personal identifiers;
- biometric data;
- national security mission support;
- CI polygraph.

The filter deliberately retains Vienna postings even where a later edit removes an explicit mission phrase, allowing first-seen and last-seen comparison across collection runs.

## Run

```bash
python3 scripts/scrape_tsc_job_postings.py \
  --site agile-defense \
  --output imports/fbi-procurement/tsc-job-postings.jsonl
```

Narrow or expand matching:

```bash
python3 scripts/scrape_tsc_job_postings.py \
  --site agile-defense \
  --term 'threat screening' \
  --term 'identity resolution' \
  --location 'Vienna, VA' \
  --output /tmp/tsc-jobs.jsonl
```

## Preserved fields

Each record includes:

- Lever site and posting ID;
- canonical public posting URL;
- title, department, team, commitment and workplace type;
- location and all public locations;
- description and public content sections converted to normalized text;
- public requisition code where exposed;
- matched mission terms and locations;
- retrieval timestamp;
- SHA-256 of the normalized public posting.

The collector intentionally omits application-form fields and never follows the `apply` URL.

## Interpretation

A public posting can establish:

- an active or recently active staffing surface;
- public labor categories and experience levels;
- clearance and polygraph requirements;
- mission concepts and work location;
- probable contract staffing when the posting closely matches a known award.

A posting does not establish:

- who was hired;
- employee identity;
- vacancy count;
- prime or subcontract allocation;
- named key-personnel status;
- a government supervisor;
- a response to `FBI-TSC-AIE`.

## Validation

```bash
python3 -m unittest tests.test_scrape_tsc_job_postings -v
python3 -m compileall -q scripts/scrape_tsc_job_postings.py
```
