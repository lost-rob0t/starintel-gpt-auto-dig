# BAE Systems → Thiel, WEF and think-tank cross-dataset map — depth 4

**Root:** FBI TSC Analysis Services / `FBI-TSC-AIE`  
**Parent:** #1962 depth 3  
**Primary dataset:** `fed`  
**Linked datasets:** `wef`, `palantir`, `rusi`, `csis`, `cnas`, `atlantic-council`, `us-israel-military-integration`  
**Date:** 2026-08-02  
**Records:** 30  
**JSONL SHA-256:** `574bedea951d4470d189b3b4d5e41ef3b02ef550a60c77cb6e7670654ad12517`

## Result

The pass found one direct World Economic Forum institutional surface, one indirect Peter Thiel investment path, several think-tank relationships, and an already-existing Aerospace Industries Association bridge in the repository.

None of these paths establishes that Peter Thiel, Palantir, the World Economic Forum, Scale AI, RUSI, CSIS, CNAS, the Atlantic Council or AIA participated in BAE's FBI Threat Screening Center contract or responded to `FBI-TSC-AIE`.

## Direct WEF surface

The World Economic Forum maintains an official organization page for **BAE Systems**. The page identifies the company and lists the **Centre for Advanced Manufacturing and Supply Chains** as a related centre.

This supports:

```text
BAE Systems plc
  -> has official organization profile at
World Economic Forum

BAE Systems plc
  -> related centre listed by WEF
Centre for Advanced Manufacturing and Supply Chains
```

It does not establish that every BAE subsidiary, executive, contract or program participates in the Forum.

## Indirect Peter Thiel path

Official primary sources establish this bounded chain:

```text
Peter Thiel
  -> Partner
Founders Fund
  -> led Scale AI Series C in 2019
  -> participated in Scale AI Series E in 2021
  -> participated in Scale AI Series F in 2024
Scale AI
  -> strategic relationship announced March 26, 2026
BAE Systems Intelligence & Security
```

Named participants in the BAE–Scale announcement:

- **Peder Jungck** — Chief Innovation & Strategy Officer, BAE Systems Intelligence & Security
- **Zane Teeters** — Head of Public Sector GTM Strategy, Scale AI

This is an indirect investment-and-partnership path. It is not evidence that Thiel controls Scale AI, directs BAE, influenced the TSC award, or participated in the FBI AI RFI.

## RUSI shared-institution path

RUSI's current organizational-membership page lists:

- BAE Systems plc
- BAE Systems Digital Intelligence
- Palantir Technologies

This creates a verified common-institution path between BAE and Palantir. Co-membership is not evidence of direct collaboration.

Named BAE personnel with public RUSI roles include:

- **Oliver Waghorn** — BAE Head of Government Relations and RUSI Advisory Board member
- **Dr Mary Haigh** — BAE Director of Digital Delivery / deputy Global CIO and RUSI Senior Associate Fellow

Additional public RUSI/BAE personnel remain queued for canonical identity resolution.

## Other think-tank surfaces

- **CNAS:** its current supporters page lists BAE Systems, Inc. for the October 2024–September 2025 disclosure period.
- **CSIS:** official CSIS publications and events identify BAE Systems support.
- **Atlantic Council:** its 2019 honor roll lists BAE Systems as a contributor. This is historical and must not be represented as current support.

Funding or membership establishes a disclosed institutional relationship. It does not prove control over research conclusions, lobbying coordination, contract influence or a TSC operational role.

## Existing repository bridge

The `us-israel-military-integration` pass 6 already contains:

```text
Tom Arseneault
  -> leads
BAE Systems Inc.
  -> represented on
Aerospace Industries Association
```

The pass reuses those canonical IDs rather than duplicating the AIA records.

## Cross-dataset merge policy

The packet emits relations directly into the target datasets while keeping one depth-4 analysis and workflow record in `fed`.

| Target dataset | Added surface |
|---|---|
| `wef` | BAE official WEF profile and related centre |
| `palantir` | Peter Thiel / Founders Fund → Scale AI → BAE I&S path |
| `rusi` | BAE and Palantir organizational memberships; named BAE/RUSI personnel |
| `csis` | BAE-supported CSIS research |
| `cnas` | disclosed BAE supporter relationship |
| `atlantic-council` | historical 2019 contributor relationship |
| `us-israel-military-integration` | reuse existing BAE–AIA graph; no duplicate relation emitted |
| `fed` | corporate hierarchy, TSC boundary analysis and next target |

See `merge-plan.json` for exact IDs and dataset destinations.

## Evidence boundaries

1. An official WEF organization page is an institutional surface, not proof of personal membership by every employee.
2. Founders Fund investment in Scale AI does not establish Peter Thiel's operational role at Scale or BAE.
3. The BAE–Scale agreement concerns defense platforms and mission systems; no reviewed source ties it to TSC.
4. Shared RUSI membership does not prove BAE–Palantir cooperation.
5. Think-tank funding, membership and fellowship relations are preserved separately.
6. Historical donor records are dated and are not silently converted into current relationships.
7. No cross-dataset path is treated as proof of procurement corruption, covert direction or source-selection influence.

## Next layer

- enumerate all BAE people publicly tied to WEF centres, meetings, councils, reports and initiatives;
- enumerate BAE/RUSI fellows, advisory-board members, speakers and sponsored programs;
- identify direct personnel overlap among BAE, Scale AI, Palantir and Founders Fund;
- test whether any BAE–Scale personnel, products or proposal materials appear in `FBI-TSC-AIE` records;
- resolve BAE support tiers and years at CSIS, CNAS and Atlantic Council;
- enumerate the six unsuccessful TSC Analysis Services offerors and cross-match them against the same datasets.

## Validation

```bash
python3 scripts/starintel.py import \
  digs/fed/2026-08-02-bae-thiel-wef-think-tank-cross-dataset-depth-4/starintel-documents.jsonl
python3 scripts/validate-for-merge.py --site
```
