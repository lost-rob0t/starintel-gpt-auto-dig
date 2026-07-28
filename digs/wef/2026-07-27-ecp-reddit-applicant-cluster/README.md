# WEF ECP Fall 2026 — public Reddit applicant-cluster seed

**Dataset:** `wef`  
**Pass:** seed / recursion depth 0  
**Date:** 2026-07-27  
**Schema:** StarIntel v0.9.0  
**Records:** 34

This packet seeds Auto-Dig with public World Economic Forum Early Careers Program recruitment discussions. It captures public Reddit handles, self-reported office and application-stage claims, cross-cycle account recurrence, and bounded follow-on targets.

## Record inventory

| Dtype | Count |
|---|---:|
| `source` | 3 |
| `social-media-post` | 2 |
| `user` | 21 |
| `relation` | 4 |
| `investigation-target` | 1 |
| `analysis` | 1 |
| `research-node` | 1 |
| `research-pass` | 1 |

## Guardrails

- A public handle is stored as a pseudonymous `user`, not a resolved `person`.
- Thread participation does **not** establish WEF affiliation, selection, employment, or real-world identity.
- Applicant claims remain marked `self-reported/unverified`.
- Exact username equality across platforms is insufficient for an identity merge.
- Do not collect private accounts, gated content, breach data, passwords, personal contact information, residential information, family information, or biometric/face-recognition matches.
- Preserve negative searches and false-positive collisions.

## Seed sources

1. [Fall 2026 r/careerguidance thread](https://www.reddit.com/r/careerguidance/comments/1ub655o/world_economic_forum_early_careers_program_fall/)
2. [Spring 2026 r/UNpath thread](https://www.reddit.com/r/UNpath/comments/1p1exmf/world_economic_forum_early_career_program/)
3. [Pinterest profile using the exact string `nonochan1011`](https://jp.pinterest.com/nonochan1011/)

The Pinterest result is an exact-string candidate only. The Reddit and Pinterest users remain separate entities.

## Public Reddit handles captured

- `u/Destiny_Breaker_007`
- `u/Vast-Regret-8191`
- `u/FoxKey5055`
- `u/Downtown_Sport_8653`
- `u/PM_ME_YOUR_CORRELATI`
- `u/Electrical-Baby-7310`
- `u/Traveller_emmz`
- `u/AffectionateTaste73`
- `u/Select_Plum_4580`
- `u/darrioup974`
- `u/Initial_Bridge_2822`
- `u/Dove_Hazy`
- `u/jsjsjsnsxkks`
- `u/TwistThese581`
- `u/czpbasi`
- `u/nonochan1011`
- `u/Spirited_Avocado27`
- `u/Famous-Act2958`
- `u/Difficult_Profile_45`
- `u/Civil-Sky-3933`

## Initial findings

- The Fall thread snapshot exposes **20 distinct public Reddit handles**.
- `darrioup974` and `Dove_Hazy` recur in the older Spring 2026 WEF recruitment thread.
- Self-reported applicant activity spans Geneva, Mumbai, Beijing, and New York.
- Reported states include `Candidate Assessment`, `Application Under Review`, inactive applications, role-specific rejection, automated video interview/HireVue, and hiring-team interview.
- An indexed Pinterest profile uses the exact string `nonochan1011`; no same-controller conclusion is supported.
- Initial indexed searches for a limited subset of other distinctive handles produced no credible non-Reddit exact-match result.

## Recursive targets

1. Exact public-handle reuse with normalization variants and negative-result logging.
2. Cross-cycle Reddit recurrence across WEF Early Careers cohorts.
3. Office/track/status timeline for Geneva, Mumbai, Beijing, and New York.
4. Official WEF, Workday, and HireVue recruitment-process documentation.
5. Public WEF Early Careers recruiting and program-management personnel.
6. New public cohort threads, role postings, and application-state changes.

## Auto-Dig node

The packet includes the queued research node:

```text
starintel:research-node:wef-ecp-fall-2026-public-recursive-dig
```

It is depth-limited to 5, public-source-only, local-cost capped at zero, and stops when the actor queue is empty, no new documents are emitted, or the objective is satisfied.

## Import

```bash
python3 scripts/starintel.py import \
  digs/wef/2026-07-27-ecp-reddit-applicant-cluster/starintel-documents.jsonl
```

Then validate the complete corpus and generated site:

```bash
python3 scripts/validate-for-merge.py --site
```
