# Request #1904 — Tompkins County October 2025 renewal-hearing baseline

Worker 8/8 bounded additive pass for `alpr-ny-tompkins-county-network`.

## What this adds

Tompkins County's official October 7, 2025 Legislature highlights establish a pre-termination renewal baseline that is not yet canonicalized elsewhere in the current corpus:

1. The Legislature was publicly discussing a **pending Flock Safety renewal** for AI-enhanced license-plate-reader technology funded in the broader NYS GIVE context.
2. The County summary attributes to Flock Safety representative Trevor Chandler claims that Flock used end-to-end encryption, automatically deleted data after 30 days, did not sell/share customer data, and left sharing choices to the customer/community. These remain **attributed vendor claims**, not independent proof of configured platform state.
3. The County summary attributes to Sheriff Derek Osborne a policy/access boundary requiring proper legal process for federal access and describing limited local access to certain New York agencies. This is an **officially reported policy statement**, not a native `SharedNetworks` or audit export.
4. The Legislature separately approved, **9–4**, acceptance of **$220,650** for GIVE activities in the Sheriff's and Probation departments. This pass does **not** equate the entire grant award with Flock spending.

This pre-renewal layer helps explain the funding/renewal context preceding the April 2026 termination decision while keeping grant acceptance, vendor contract spending, policy statements, technical configuration, and later offboarding as separate predicates.

## Primary source

- Tompkins County, *Highlights of the 10/07/25 Tompkins County Legislature meeting*  
  https://www.tompkinscountyny.gov/News-articles/Highlights-of-the-100725-Tompkins-County-Legislature-meeting

## Canonicalization

`starintel-documents.jsonl` is the authored packet. Normalized `db/` records must be produced only through the repository's required transactional importer:

```bash
python3 scripts/schema-release.py current
python3 scripts/schema-release.py check
python3 scripts/starintel.py types
python3 scripts/starintel.py import \
  digs/flock/2026-09-15-request-1904-renewal-hearing-baseline/starintel-documents.jsonl
```

Do not hand-edit normalized `db/` records.

## Still unresolved

- native IQM2 GIVE resolution number/text and budget attachments;
- exact Flock contract/order-form/invoice amounts charged against GIVE;
- native retention and deletion settings;
- native `SharedNetworks`, Organization Audit and Network Audit state;
- executed termination notice, vendor acknowledgment and final contract closeout;
- credential/account shutdown, device disposition and deletion/retention proof after termination.
