# WEF ECP Fall 2026: don't deanonymize the applicants

**Dataset:** `wef`  
**Date:** 2026-08-11  
**Recursion depth:** 2  
**Schema:** StarIntel v0.9.0  
**Records:** 6

## What happened

The July 27 Reddit applicant cluster is useful as a SOCMINT methodology test, not as an excuse to play identity bingo with pseudonymous applicants.

> public Reddit handle appears
>
> same string maybe exists somewhere else
>
> congratulations, you found a string
>
> you did not find a person

No applicant deanonymization was performed.

## The rule

- Public Reddit handles stay pseudonymous `user` records, not resolved `person` records.
- Thread participation is not WEF affiliation, employment, selection, or proof of applicant status.
- Applicant-status claims stay `self-reported/unverified` until independently corroborated.
- Exact username equality across platforms is a discovery signal only.
- Unresolved collisions remain separate with `identity_resolved=false` and `do_not_merge_entities=true`.
- Private/gated accounts, breach data, personal contact/residential/family data, and face recognition stay out of this recursion.

## What the official sources added

### The requisition inventory was incomplete

Official WEF Workday requisition **R4228** adds another role:

- *ECP Fall 2026 – Centre for Regions, Trade and Geopolitics, Greater China* — Beijing
- https://weforum.wd3.myworkdayjobs.com/en-US/Forum_Careers/job/ECP-Fall-2026---Centre-for-Regions--Trade-and-Geopolitics--Greater-China_R4228

That brings the known official inventory to **at least seven requisitions**: two umbrella postings plus at least five role-specific postings.

### Workday status labels are tenant-configurable

Official Workday documentation says external candidate labels can be configured by the tenant:

- https://doc.workday.com/workday-education/en-us/course-manuals/recruiting-for-administrators/prospects-and-candidates.html

So applicant-reported strings such as `Candidate Assessment` and `Application Under Review` should be stored as **observed WEF Candidate Home labels**, with source and observation time. They are not universal Workday stages unless WEF documents that mapping.

### Two New York role titles still need official requisition IDs

The WEF company jobs discovery surface lists:

- `ECP Fall 2026 – North America and Latin America Regional Teams`
- `Early Career Program – North America and Latin America Government Teams`

Discovery surface:

- https://ir.linkedin.com/company/world-economic-forum/jobs

Those are leads, not permission to guess requisition IDs or map Reddit users into the roles.

## SOCMINT invariant

```text
public handle
    -> pseudonymous user

exact cross-platform string match
    -> unresolved lexical collision / candidate edge
    -> identity_resolved = false
    -> do_not_merge_entities = true

user -> person
    -> forbidden from username equality alone
    -> requires independent public identity evidence and separate review
```

Recruitment state gets the same treatment:

```text
applicant report
    -> self-reported claim

portal string
    -> observed tenant label

internal stage interpretation
    -> inference unless WEF documents the mapping
```

## Next dig

`starintel:investigation-target:wef-ecp-fall-2026-official-role-refresh-depth-3`

Resolve official requisition IDs/URLs for the newly visible New York roles, enumerate the remaining Fall 2026 ECP requisitions, and keep the no-deanonymization boundary intact.

## Packet

`starintel-documents.jsonl` contains:

- 3 `source`
- 1 `analysis`
- 1 `investigation-target`
- 1 `research-pass`

## Validation

The previous cancelled site run was recovered successfully and passed the full current site gate, including `nimble buildFast` and `bin/validate-for-merge --site`. This README refresh intentionally triggers the current exact-head document and site validators so the packet can be judged under today's repository contract before promotion.
