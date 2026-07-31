# USAID, DOGE, mortality estimates, and accountability

StarIntel v0.9.0 seed packet for issue #68.

## Scope

This packet separates four evidence branches:

1. **Observed government actions** — the foreign-assistance pause, the DOGE/USDS advisory structure, and USAID functions transferred to the State Department.
2. **Modeled mortality estimates** — the Lancet forecast and the Boston University Impact Counter.
3. **Individually documented cases** — Abdullahi Ibrahim, Purity Wamboi, and Ibrahim Garba.
4. **Statements and rhetoric** — Musk's mortality denial and retrospective political statement, the White House position on his formal authority, and the GDF seed video's title.

## Core findings

- Executive Order 14169 directed department and agency heads to pause new obligations and disbursements for 90 days and gave the Secretary of State waiver authority.
- Executive Order 14158 created the DOGE/USDS structure and described agency DOGE teams as coordinating with USDS and advising agency heads.
- CRS reports that USAID ceased implementing foreign assistance on July 1, 2025 and selected functions moved to the State Department.
- The Lancet study forecast more than 14 million additional all-age deaths, including about 4.5 million children under five, under its steep defunding scenario through 2030.
- The Impact Counter's reported one-year figure is model-derived and methodologically distinct from the Lancet forecast.
- NPR/KPBS documented three named child deaths and reported service interruptions. Each prevention claim remains a separate, unresolved counterfactual.
- The White House represented that Musk lacked formal decision authority. This does not settle questions of influence, advocacy, or moral responsibility.
- “Mass murderer” is stored only as attributed rhetoric, not an identity or legal conclusion.

## Packet

- Dataset: `usaid-doge-mortality-accountability`
- Schema: `0.9.0`
- Records: **42**
- Dtypes: 9 source, 8 claim, 7 person, 7 relation, 5 event, 4 org, 1 research-pass, 1 dataset-manifest
- Canonical transport: `starintel-documents.jsonl`
- SHA-256: `ef60aafbdfa3bcb6027fffcd83de5739536ecb88581d5297d4fbb47789c33659`
- Source inventory: `sources.md`
- Integrity manifest: `manifest.json`

## Validation status

Local checks passed for JSON parsing, unique IDs, required common fields, strict dtype-specific data keys, relation subject shape, and internal StarIntel references. The generated file's Git blob SHA matched the blob stored on the branch. The repository command `python3 scripts/validate-for-merge.py --site` was not run because this environment had no repository checkout; GitHub checks are authoritative.
