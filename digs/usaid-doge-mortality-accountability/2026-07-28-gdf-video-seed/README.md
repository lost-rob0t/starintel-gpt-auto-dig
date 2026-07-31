# USAID, DOGE, mortality estimates, and accountability

StarIntel v0.9.0 seed packet for issue #68.

## Scope

This packet separates four evidence branches:

1. **Observed government actions** — executive orders, the foreign-assistance pause, USAID restructuring, appropriations activity, and litigation.
2. **Modeled mortality estimates** — the Lancet retrospective/forecast model and the Boston University Impact Counter.
3. **Individually documented cases** — Abdullahi Ibrahim, Purity Wamboi, and Ibrahim Garba.
4. **Statements and rhetoric** — Musk's denials and retrospective statement, Ro Khanna's accountability demand, and the GDF seed video's title.

## Core findings

- Executive Order 14169 directed department and agency heads to pause new obligations and disbursements for 90 days and gave the Secretary of State waiver authority.
- Executive Order 14158 created the DOGE/USDS structure and described agency DOGE teams as coordinating with USDS and advising agency heads.
- CRS reports that USAID ceased implementing foreign assistance on July 1, 2025 and selected functions moved to the State Department.
- The Lancet study estimated historical mortality associations and forecast **14,051,750** additional all-age deaths, including **4,537,157** children under five, under its steep defunding scenario through 2030.
- The Impact Counter's reported one-year figure is model-derived and methodologically distinct from the Lancet forecast.
- NPR/KPBS documented three named child deaths and reported service interruptions. Each prevention claim remains a separate, unresolved counterfactual.
- The White House represented in litigation that Musk lacked formal decision authority. This does not settle questions of influence, advocacy, or moral responsibility.
- “Mass murderer” is stored only as attributed rhetoric, not an identity or legal conclusion.

## Packet

- Dataset: `usaid-doge-mortality-accountability`
- Schema: `0.9.0`
- Records: **109**
- Canonical transport: `starintel-documents.jsonl`
- SHA-256: `ededfe8fe106167f11ad691d8b02690b7d706c6c8fb96de45ada237733a9bbbf`
- Source inventory: `sources.md`
- Integrity manifest: `manifest.json`

## Validation status

Local checks passed for JSON parsing, unique IDs, strict dtype-specific data keys, scalar relation subjects, and internal StarIntel references. The repository command `python3 scripts/validate-for-merge.py --site` was not run because this environment had no repository checkout; the draft PR and GitHub checks are authoritative.
