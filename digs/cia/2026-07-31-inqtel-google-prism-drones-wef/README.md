# CIA, In-Q-Tel, Google, PRISM, drones, and WEF

StarIntel v0.9.0 public-source packet for issue #93.

## Scope

This packet executes five evidence-separated passes:

1. **CIA and In-Q-Tel root** — public institutional structure, leadership seeds, and technology priorities.
2. **Keyhole → Google → Niantic → Pokémon GO** — investment, acquisition, internal venture, financing, product, and restructuring lineage.
3. **PRISM / FISA Section 702** — public program mechanics, agency receipt roles, leaked provider naming, and Google's public response.
4. **Drone and autonomous-systems organizations** — Skydio, Anduril, Advanced Navigation, Wing, Shield AI, and responsible public people.
5. **WEF recursion** — continue until a direct sourced World Economic Forum relation is found, then preserve weaker profile/editorial edges separately.

## Verified graph spine

`CIA → established/partnered with IQT → invested in Keyhole → acquired by Google → Niantic created inside Google → Pokémon GO`

That is a corporate and technology lineage. It is **not** evidence that CIA or IQT controls Pokémon GO or receives its data.

The WEF stop condition is met through the official **Google → partner_of → World Economic Forum** relation in the 2026 Annual Meeting partner roster. Google’s Technology Pioneer alumni relation, Skydio’s WEF organization profile, Camille François’s WEF profile, and WEF editorial coverage of Niantic/Pokémon GO are stored as different, weaker relation classes.

## Drone/autonomy branch

- IQT portfolio relations: Anduril, Skydio, Advanced Navigation.
- Google lineage: Google X → Wing → Alphabet.
- Adjacent unresolved target: Shield AI; this pass found no direct IQT investment edge.
- Public people include Adam Bry, Abe Bachrach, Adam Woodworth, Brian Schimpf, Palmer Luckey, Trae Stephens, Matt Grimm, Brandon Tseng, Ryan Tseng, Andrew Reiter, and Gary Steele.

## PRISM boundary

The packet does not label PRISM as a CIA-run program. PCLOB’s public description is represented as a compelled, selector-based Section 702 collection process. NSA receives all PRISM collection; CIA and FBI receive selected portions under that public description. Google’s denial of direct server access/backdoor access is retained separately. No direct public evidence was found in this pass connecting Pokémon GO or Niantic data to PRISM.

## Packet

- Dataset: `cia`
- Schema: `0.9.0`
- Records: **142**
- Dtypes: claim 8, dataset-manifest 1, event 9, org 20, person 19, relation 48, research-pass 5, source 32
- Canonical transport: `starintel-documents.jsonl.gz.b64` (gzip+base64; decodes to canonical JSONL)
- SHA-256: `3e2133459a4126cad4194f42e883d8c3e484a2ee531049f47e4b515f4ff217b3`
- Entity roster: `entity-roster.csv`
- Drone people matrix: `drone-people.csv`
- WEF edge table: `wef-edges.csv`
- PRISM responsibility matrix: `prism-responsibility.md`
- Source inventory and coverage: `sources.md`

## Validation status

Passed locally against the generated packet:

- JSON parsing
- unique IDs
- required common fields
- source references
- relation endpoint resolution
- record counts and SHA-256 generation

The repository command `python3 scripts/validate-for-merge.py --site` and canonical `db/` import were **not run** because the execution environment cannot resolve GitHub for a checkout and has no authenticated `gh` CLI. Keep the PR draft until repository CI and the canonical importer complete successfully.
