---
description: Mine live StarIntel social relations with symbolic verification
---

Run a bounded social-relations research pass for: $ARGUMENTS

Hard requirements:

1. Read `config/auto-dig-control.json` first. Stop without changing research
   state if Auto-Dig is disabled, paused, invalid, or disallows new work.
2. Call the `starintel-live` MCP `starintel_health` tool before research.
   This command is specifically a live-ingest mining lane: require
   `backend=server`. If only the local fallback is available, report that and
   stop rather than pretending the run was live.
3. Search the live StarIntel corpus before creating identities or relations.
   Fetch exact existing documents when an ID already exists. Reuse canonical
   IDs and deduplicate against current packets.
4. Mine only public or operator-authorized evidence. Do not collect private
   addresses, private contact details, credentials, or unrelated personal
   information.
5. Keep explicit facts and derived graph hypotheses separate. Never infer
   family, romantic/sexual, political, religious, health, race/ethnicity,
   union, criminal-status, or account-identity relationships from proximity,
   common neighbors, embeddings, or model guesses.
6. Use `agents/social_relations_expert.pl` for symbolic assessment of any
   relation slice you assemble. Treat `association_candidate/4` as a research
   lead only; it may only map to generic `associated_with`, must retain
   supporting relation IDs, must stay under the expert confidence cap, and must
   remain `requires_review`.
7. For source-backed additions, write a normal Auto-Dig packet under
   `digs/social-relations/<UTC-date>-<short-slug>/starintel-documents.jsonl`.
   Preserve the current StarIntel document conventions: source records,
   explicit relation records, analysis/research-pass provenance, and
   investigation-target records for unresolved joins.
8. Do not call the ingest write API and do not print secrets. This lane mines
   the live corpus but leaves publication to the existing explicit importer.
9. Validate the packet and expert before finishing:
   - `swipl -q -s agents/test_social_relations_expert.pl -g 'run_tests,halt'`
   - `python3 scripts/validate-for-merge.py --site`
10. Summarize exact new IDs, evidence sources, expert conclusions, unresolved
    targets, and validation results. Do not overstate a derived association as
    a verified real-world relationship.
