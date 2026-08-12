# WEF ECP Fall 2026 — methodology audit and requisition graph, depth 2

**Dataset:** `wef`  
**Date:** 2026-08-11  
**Recursion depth:** 2  
**Schema:** StarIntel v0.9.0  
**Records:** 6

## Why this pass exists

The July 27 Reddit applicant-cluster seed is primarily useful as a SOCMINT methodology test. This pass audits its identity boundary and advances the stronger official-source frontier rather than attempting to deanonymize pseudonymous applicants.

## Methodology verdict

The seed's identity handling is conservative and should remain the rule:

- Public Reddit handles remain pseudonymous `user` records, not resolved `person` records.
- Thread participation is not WEF affiliation, employment, selection, or proof of applicant status.
- Applicant status claims remain `self-reported/unverified` unless independently corroborated.
- Exact username equality across platforms is a discovery signal only.
- Unresolved cross-platform collisions stay as separate entities with `identity_resolved=false` and `do_not_merge_entities=true`.
- No private/gated accounts, breach data, personal contact/residential/family data, or face recognition belong in this recursion.

No applicant deanonymization was performed in this pass.

## Depth-2 findings

### 1. The July 27 requisition inventory is incomplete

An additional official WEF Workday requisition is now indexed:

- **R4228** — *ECP Fall 2026 – Centre for Regions, Trade and Geopolitics, Greater China* — Beijing
  - https://weforum.wd3.myworkdayjobs.com/en-US/Forum_Careers/job/ECP-Fall-2026---Centre-for-Regions--Trade-and-Geopolitics--Greater-China_R4228

The depth-1 packet documented two umbrella requisitions plus four later role-specific requisitions. R4228 raises the known official inventory to **at least seven requisitions**: two umbrella and at least five later role-specific postings.

### 2. Candidate-facing Workday status strings are not universal stages

Official Workday documentation says tenants can configure external candidate labels through dynamic/external label overrides:

- https://doc.workday.com/workday-education/en-us/course-manuals/recruiting-for-administrators/prospects-and-candidates.html

Therefore strings reported by applicants such as `Candidate Assessment` and `Application Under Review` should be modeled as **observed WEF Candidate Home labels**, with source and observation time. They must not be normalized into universal Workday stage semantics without WEF-specific documentation.

### 3. Two more New York ECP role titles need official-ID resolution

The World Economic Forum company jobs surface lists:

- `ECP Fall 2026 – North America and Latin America Regional Teams`
- `Early Career Program – North America and Latin America Government Teams`

Discovery surface:

- https://ir.linkedin.com/company/world-economic-forum/jobs

These titles are useful recursive leads, but this pass did **not** resolve stable official Workday requisition IDs for them. Do not guess the IDs or infer that any Reddit applicant was routed into these roles.

## Recommended SOCMINT invariant

```text
public handle
    -> pseudonymous user

exact cross-platform string match
    -> unresolved lexical collision / candidate edge
    -> identity_resolved = false
    -> do_not_merge_entities = true

user -> person
    -> forbidden from username equality alone
    -> requires independent public identity evidence and a separate review
```

Recruitment state should use the same discipline:

```text
applicant report
    -> self-reported claim

portal string
    -> observed tenant label

internal stage interpretation
    -> inference unless WEF documents the mapping
```

## Next recursive target

`starintel:investigation-target:wef-ecp-fall-2026-official-role-refresh-depth-3`

Depth 3 should resolve official requisition IDs/URLs for the newly visible New York roles, enumerate remaining Fall 2026 ECP requisitions, and preserve the same no-deanonymization boundary.

## Packet

`starintel-documents.jsonl` contains:

- 3 `source` records
- 1 `analysis`
- 1 `investigation-target`
- 1 `research-pass`

## Validation status

The packet was prepared against the repository's v0.9.0 field contract and existing depth-2 record shapes. The mandatory local Nim merge gate must still be run:

```bash
nimble buildFast
bin/validate-for-merge --site
```

Do not merge until that gate and required GitHub checks are green.
