# U.S.–Israel Military Integration — Recursive Pass 3

**Run:** `2026-07-31`  
**Dataset:** `us-israel-military-integration`  
**Research pass:** `3`  
**Incremental packet:** `72` StarIntel v0.9.0 documents  
**Baseline plus pass 2:** `102` records  
**Cumulative after import:** `174` records  
**JSONL SHA-256:** `1d0606d2478b75eda508f7b5e48f8c48a1f112e077513317fdc36ac2ac44423b`  
**Scope:** Public official sources. Broad headquarters and contractor locations only; no tactical coordinates, access procedures, private identifiers, or inferred personal contact information.

## Findings added in this pass

### 1. Joint Task Force-Israel was a named deployable U.S. command construct

Official 2018 exercise records identified a **deployable Joint Task Force-Israel** commanded by Third Air Force commander Lt. Gen. Richard Clark. A bilateral Combined Exercise Control Group directed Juniper Cobra exercise activity, and U.S. reporting described the mission as training to defend Israel.

The construct remained visible in 2021. USAFE–AFAFRICA deputy commander Lt. Gen. Steven Basham was concurrently identified as Joint Task Force-Israel commander during Juniper Falcon. The exercise tested ballistic-missile defense, crisis response, logistics resupply, humanitarian assistance, and a segmented forward/rear deployment model for U.S. personnel.

**Assessment:** This proves a repeatable U.S. deployable headquarters model supporting Israel's defense. It does **not** prove that the historical JTF became the “bilateral operational headquarters” referenced by Israel's defense ministry in 2025.

### 2. The Gaza CMCC is paired with a dedicated IDF headquarters

CENTCOM opened the Civil-Military Coordination Center in Israel on October 17, 2025. Approximately 200 U.S. service members with transportation, planning, security, logistics, and engineering expertise established the center under U.S. Army Central commander Lt. Gen. Patrick Frank.

The IDF then established a separate headquarters specifically to coordinate and synchronize the Israeli defense establishment's work with the U.S.-led CMCC. Maj. Gen. Yaki Dolf was appointed to lead it. The IDF reported more than 100 permanent positions plus additional conscript staffing.

By December 2025, the CMCC included representatives from approximately 60 partner nations and organizations. CENTCOM also confirmed that a U.S. MQ-9 supplied surveillance video used by the center to monitor ceasefire implementation.

**Assessment:** This is a documented parallel-headquarters interface:

```text
CENTCOM-led multinational CMCC
              ↕
Dedicated IDF coordination headquarters
              ↕
Israeli defense establishment and Gaza operations
```

The arrangement is institutionalized and operational, but it remains two connected chains rather than one publicly merged sovereign command.

### 3. End-use monitoring retained unresolved inspection actions

The DoD OIG's enhanced end-use monitoring audit issued four recommendations. Oversight.gov listed three as open, including:

- a CENTCOM Security Cooperation Organization command inspection of the Office of Defense Cooperation–Israel, or a remote inspection;
- a DSCA compliance assessment visit for end-use monitoring in Israel, or a virtual visit;
- one Controlled Unclassified Information recommendation.

Golden Sentry requires routine and enhanced monitoring of U.S.-origin defense articles, including physical-security assessment and serial-number inventory for enhanced-monitoring items.

**Assessment:** The record establishes unresolved inspection and compliance-assessment actions. It does not, without additional evidence, establish diversion, unauthorized use, or loss of specific equipment.

### 4. Operation Epic Fury now has a formal financial-audit trail

On July 13, 2026, the OIG announced an audit of open FY2026 funding commitments supporting Operation Epic Fury. The audit seeks stale, invalid, or excess commitments that may be canceled and redirected.

**Assessment:** The operation generated identifiable financial commitments across DoD components. The announcement does not disclose the operation's total cost, obligated amount, or component-level ledger.

### 5. Arms sales create embedded multi-year support structures

On January 30, 2026, DSCA announced four possible Israeli Foreign Military Sales with a combined maximum estimate of **$6.67 billion**:

| Program | Maximum estimate | Principal contractor | Public support footprint |
|---|---:|---|---|
| 3,250 JLTVs | $1.98B | AM General | 15 U.S. government and 20 contractor representatives for up to six years |
| 30 AH-64E Apaches | $3.8B | Boeing and Lockheed Martin | Five to eight government/contractor representatives for up to five years |
| Namer power packs and logistics | $740M | Rolls-Royce Solutions America | Technical assistance, engineering, configuration management, and logistics support |
| AW119Kx helicopters | $150M | Leonardo Helicopters USA | Three to five U.S. government representatives for up to five years, plus contractor trainers |

These are congressional notifications and maximum estimates, not proof of fully executed contracts or spending at the listed values.

## Escalation judgment

The integration architecture now includes all of the following publicly documented layers:

1. deployable U.S. joint-task-force headquarters designed around Israel's defense;
2. bilateral exercise-control and combined planning structures;
3. a current CENTCOM-led headquarters inside Israel;
4. a dedicated IDF headquarters built to interface with the U.S.-led center;
5. U.S. intelligence-surveillance feeds supporting the center's operations floor;
6. U.S. government inspection and end-use-monitoring structures;
7. operational funding commitments subject to DoD audit;
8. multi-year government and contractor fielding footprints attached to major arms programs.

The strongest defensible description remains:

> **Deep operational, command-interface, oversight, and industrial integration with formally preserved sovereign command.**

## Packet counts

```json
{
  "analysis": 1,
  "claim": 7,
  "event": 8,
  "org": 14,
  "person": 5,
  "relation": 35,
  "research-pass": 1,
  "target": 1
}
```

## New high-priority nodes

```text
starintel:org:joint-task-force-israel
starintel:org:idf-cmcc-coordination-headquarters
starintel:org:odc-israel
starintel:org:golden-sentry
starintel:org:middle-east-air-defense-network
starintel:person:richard-clark
starintel:person:steven-basham
starintel:person:patrick-frank
starintel:person:yaki-dolf
starintel:event:dodig-eeum-israel-audit-2025
starintel:event:dodig-epic-fury-open-commitments-audit-2026
starintel:event:israel-fms-approvals-2026-01-30
```

## Next recursive targets

- Identify post-2021 command ownership of any deployable JTF-Israel function after Israel moved from EUCOM to CENTCOM.
- Trace the current CMCC U.S. command roster below Lt. Gen. Patrick Frank and the IDF headquarters staff below Maj. Gen. Yaki Dolf.
- Obtain the final or interim results of the Operation Epic Fury open-commitments audit when published.
- Determine whether CENTCOM and DSCA completed the FY2026 ODC-Israel and end-use-monitoring inspections.
- Trace Letters of Offer and Acceptance and executed contracts for the January 2026 FMS notifications.
- Map contractor subcontractors, training teams, field-service representatives, and sustainment depots for JLTV, Apache, AW119Kx, and Namer programs.
- Resolve whether the 2025 “bilateral operational headquarters” is a successor, activation state, or separate construct from historical Joint Task Force-Israel.

## Source index

| Publisher | Source | Date |
|---|---|---|
| U.S. Central Command | CENTCOM Opens Civil-Military Coordination Center to Support Gaza Stabilization | 2025-10-21 |
| U.S. Central Command | CMCC Achieves Gaza Support Milestone, Welcomes More Partners | 2025-12-11 |
| Israel Defense Forces | New Headquarters Established to Coordinate Activities in Gaza with International Partners | 2025-11-27 |
| U.S. Central Command | US Drone Observes Aid Truck Looted by Hamas in Gaza | 2025-11-01 |
| DVIDS | Joint U.S.-Israel Exercise Juniper Cobra 2018 Officially Underway | 2018-03-08 |
| U.S. European Command | IDF delegation arrives at Ramstein Air Base to participate in Juniper Falcon 21 | 2021-02-09 |
| Oversight.gov / DoD OIG | Audit of DoD's Enhanced End-Use Monitoring in Israel | 2025-12-17 |
| Defense Security Cooperation Agency | Golden Sentry End-Use Monitoring Program | current |
| Defense Security Cooperation Agency | DSCA Policy Memorandum 26-79 | 2026-05-13 |
| DoD OIG | Audit of Open Commitments for Operation Epic Fury | 2026-07-13 |
| Defense Security Cooperation Agency | Israel JLTV, AH-64E, Namer, and AW119Kx notifications | 2026-01-30 |
