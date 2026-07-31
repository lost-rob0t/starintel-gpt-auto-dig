# RELX / LexisNexis Risk Solutions government surveillance infrastructure

StarIntel v0.9.0 research packet for issue #92.

## Scope

This packet maps the first five recursive passes over the commercial-dossier and public-safety stack operated by RELX / LexisNexis Risk Solutions:

1. corporate entities, acquisitions, products, and leadership;
2. government customers and procurement records;
3. data-source and analytic-capability lineage;
4. executives and the next influence-research frontier;
5. oversight, security, accuracy, market structure, and adjacent-vendor bridges.

## Core findings

- LexisNexis markets Accurint Virtual Crime Center as combining more than 10,000 sources, including police-agency data, with identity location, booking-photo retrieval, mapping, analytics, and link analysis.
- LexisNexis states Accurint AI Insights uses Public Safety Data Exchange crime incidents contributed by more than 2,100 agencies.
- USAspending records ICE contract `70CMSD21C00000001` for a Law Enforcement Investigative Database Subscription with $24,509,115 obligated and a current end date of August 31, 2026.
- GAO documented longstanding federal reliance on information resellers and identified gaps in openness, accountability, and permissible-purpose auditing.
- FTC records connect Seisint/Accurint to a 2008 data-security settlement and ChoicePoint to an antitrust divestiture that transferred AutoTrackXP and CLEAR assets to Thomson Reuters.
- The 2025 IDVerse acquisition expanded document authentication, biometric face matching, liveness detection, and deepfake-detection capabilities.
- LexisNexis itself warns that public-record and commercially available source data may contain errors and should be independently verified.

## Evidence boundaries

- Vendor pages establish the vendor's public claims, not universal deployment or independent effectiveness.
- Procurement records establish the award's stated purpose and financial record, not every operational use.
- FTC allegations, settlements, and orders are represented separately from admissions or adjudicated liability.
- GAO findings establish oversight observations for the reviewed agencies and periods; they are not automatically current findings about every customer.
- No private addresses, phone numbers, family mapping, or unnecessary personal data are included.

## Packet

- Dataset: `lexisnexis-risk-state-surveillance`
- Run: `2026-07-31-root-and-four-recursive-passes`
- Schema: `0.9.0`
- Records across packet files: **90**
- Canonical source/manifest transport: `starintel-documents.jsonl`
- Root entity transports: `starintel-documents-root-entities.jsonl` and `starintel-documents-root-products.jsonl`
- Recursive pass transports: `starintel-documents-pass-1.jsonl` through `starintel-documents-pass-4.jsonl`
- Recursive target outputs: `recursive-targets-pass-1.jsonl` through `recursive-targets-pass-4.jsonl`
- SHA-256 (canonical source/manifest transport): `bd7d651201f140e5292ad6698d4e9ac30ff7819fab7834d42d6ca176c493d7df`
- Source inventory: `sources.md`
- Integrity manifest: `manifest.json`

## Validation performed

- JSON parsing
- unique document IDs across all packet JSONL files
- required common envelope fields
- strict use of declared dtype fields
- source-reference resolution
- relation endpoint resolution
- generated Git blob SHA calculation

The repository's GitHub Actions checks remain authoritative for the complete `python3 scripts/validate-for-merge.py --site` gate.
