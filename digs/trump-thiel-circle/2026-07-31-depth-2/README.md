# trump-thiel-circle — depth-2 network pass

This pass recurses from the current Trump cabinet seed into organization leadership, board members, financiers, policy personnel, transaction counterparties, and federal procurement paths. It preserves the requested corruption-investigation frame while classifying each record by evidence status.

## Scope

- Dataset: `trump-thiel-circle`
- Run: `trump-thiel-circle-depth-2-2026-07-31`
- New records: **156**
- Combined with cabinet seed: **467**
- New records by type:
  - 35 people
  - 15 organizations
  - 72 relations
  - 24 sources
  - 9 claims
  - 1 research pass

## Clear connection paths expanded

### 1. Lutnick / Cantor / Tether / Rumble / Vance / Thiel

`Howard Lutnick → Cantor Fitzgerald → Tether → Rumble ← Narya Capital / Peter Thiel ← J.D. Vance`

The pass adds Cantor's current family-control structure, the Tether convertible-debt record, Tether's Rumble financing, Cantor's placement role, Rumble governance, and the Narya/Thiel/Vance investment path.

### 2. Lutnick / Commerce / USA Rare Earth / Cantor

`Howard Lutnick → Commerce Department → USA Rare Earth agreement ← Cantor Fitzgerald & Co. financing`

This is classified as an **ongoing congressional conflict inquiry**, not a concluded corruption finding. The queue requests the agreement terms, Cantor compensation, beneficial investors, and recusal records.

### 3. Vought / Project 2025 / Heritage / Vance

`Russ Vought → Center for Renewing America → Project 2025 / Heritage Foundation → Kevin Roberts ← J.D. Vance`

The pass adds CRA leadership, Project 2025 chapter authors, Heritage trustees, Vance's documented Roberts connection, and a queue for staff-to-administration appointments, donors, and policy implementation.

### 4. Hegseth / Defense Department / Palantir / Thiel

`Pete Hegseth → Department of Defense / U.S. Army awards → Palantir Technologies ← Peter Thiel`

The pass records the official Palantir contract announcements, Palantir founder-control structure, and government-contract exposure. It does **not** claim that Hegseth personally selected or directed the awards without evidence.

## Findings classified in this pass

- Official SEC enforcement finding against Cantor over misleading SPAC disclosures.
- Congressional record documenting Cantor's convertible-debt investment in Tether.
- Documented Lutnick-family trust and control continuity after Howard Lutnick's formal transfer.
- Open congressional inquiry into the Commerce–USA Rare Earth–Cantor conflict path.
- Documented Rumble capital chain connecting Cantor/Tether with the Vance/Thiel investment network.
- Documented Vought/Heritage/Project 2025/Vance policy-personnel network.
- Documented Hegseth/DoD/Palantir/Thiel procurement path, with causation caveat.
- Official DoD Inspector General finding that Hegseth did not comply with policy in his Signal use.
- Documented Palantir founder voting control and substantial government-contract exposure.

## Files

- `payload/depth2-part-*.b64` — deterministic compressed StarIntel payload.
- `build-depth2.py` — validates and materializes `starintel-documents.jsonl`.
- `manifest.json` — counts, hashes, and validation results.
- `research-queue.json` — depth-3 targets and required evidence paths.

## Evidence rule

A connection is only labeled clear when the data contains a named, source-backed path between nodes. Association alone is not classified as corruption. Official findings, transactions, inquiries, allegations, and analytic connections remain separate statuses.

## Materialize

```bash
python3 build-depth2.py
```
