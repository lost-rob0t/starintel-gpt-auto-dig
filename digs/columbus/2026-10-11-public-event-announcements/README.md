# Columbus-area public event announcements

Bounded manual review on 2026-10-11. Related request: [#2745](https://github.com/lost-rob0t/starintel-gpt-auto-dig/issues/2745).
Base: PR #2744, commit `638e51e48b5b1688ae80747548b6de4fc0de2e4b`, stacked on canonical consumer PR #2740. This base supplies the maintained contract and the mixed-wire site fixes. No historical records are relabelled.

## Deliverable and contract mapping

28 flat StarLang 0.10.1 records: six `target`, six `mission-target`, six `mission`, one `scope`, six `finding`, and three `url` records. IDs derive from the dated event key and record role, not retrieval order. Findings describe announcements, not occurred events.

The exact maintained registry includes **Mission**, **MissionTarget**, and **Target**. It has no **Operation**, **investigation-target**, **research-pass**, **event**, or **source** dtype. The requested mission-or-operation object is therefore a real canonical `mission`; bounded investigative work is represented by `mission-target` linked to its `target`. This is an explicit semantic mapping, not an alias or an invented dtype. Source observations use `url` records; event-specific structured metadata is losslessly namespaced under `org.starintel.columbus.publicEvent` on a `finding`.

The old recursive selector emits historical `investigation-target` documents and is not used to mint canonical output. No scored recursion or unsupported confidence claims are introduced. The six explicitly requested dated scopes are the complete selection. This README is the pass receipt because `research-pass` is absent from the canonical contract. Supporting findings and unresolved tasks are linked by canonical references.

## Reviewed announcements

All times are Columbus local time, America/New_York (UTC−04:00 on these dates).

| Announced instance | Time | Public location | Uncertainty or change |
| --- | --- | --- | --- |
| Stop the Cruelty, Oct 12 | 16:15–17:15 | 1 E Nationwide Blvd, High Street side | Calendar explicitly announces relocation |
| Veterans rally, Oct 13 | 16:00–17:00 | Public sidewalks at 420 N James Rd | Not the clinic grounds |
| Worthington rally, Oct 13 | 16:30–17:30 | High Street / Route 161 | Separate Columbus-area municipality |
| Husted/Moreno protest, Oct 14 | 12:00–13:00 | 200 N High St | Only this dated instance |
| Clintonville protest, Oct 17 | 12:00–13:00 | N High / E North Broadway | Only this dated instance |
| No Kings Vote Early, Oct 17 | 16:30–18:00 | Ohio Statehouse, 1 Capitol Square | Secondary says Atrium; organizer does not specify assembly point. Precise march route unverified |

Sources: [organizer calendar](https://indivisiblecentralohio.org/events), [No Kings organizer announcement](https://indivisiblecentralohio.org/events/no-kings-vote-early-rally), [secondary listing](https://columbusunderground.com/events/no-kings-vote-early-rally/).

## Evidence and time receipt

The web tool opened all three URLs during this session and re-opened the No Kings organizer text and secondary Atrium detail. The receipt timestamp is `2026-10-11T07:35:10Z`; it is an upper bound for these rendered-page retrievals, not a precise individual HTTP request timestamp. The canonical retrieval/observation fields carry this session receipt time with that precision explicitly recorded in provenance. Source publication times are unknown and are not inferred from event dates, crawl dates, or unrelated page articles. No occurrence time is claimed.

Only factual, concise paraphrases are retained in the source records. Origin HTML, response headers, original bytes, and HTTP hashes are not archived: direct requests were blocked by the environment proxy (403), while the web retrieval tool succeeded. This limits independent byte-for-byte replay. Neither the secondary venue label nor an announcement proves attendance or that the event occurred. No future source monitoring is configured.

## Execution boundary

Each Mission is `draft`; all Targets are `paused`, with recurrence disabled and no dispatch schedule. MissionTargets are `pending` under its own draft mission. `executionEnabled: false` is explicit planning metadata, not a claim that an external collector enforces it. This packet is not submitted to any runtime or queue. No attendees, RSVPs, individual political profiles, devices, location traces, private WiGLE records, registration, group joins, or contact activity are included. The existing issue is linked rather than recreated.

## Duplicate search

Before generation, the maintained corpus reader and search engine inspected 1,315,898 records across normalized DB and canonical packet discovery. Query counts and paths are preserved in `duplicate-search.json`. Five queries returned zero; `Worthington Rush Hour` returned two surfaces of the same historical Dark Academia research-pass record. That broad all-terms match contains neither the exact phrase, the October 13 date, nor the organizer domain. It is not this event. The separate canonical CLI search for `no-kings-vote-early` also returned zero records.

GitHub issue searches found existing #2745 for No Kings, no Stop the Cruelty / Veterans / Worthington / Clintonville event issue, and an unrelated Ohio political research issue (#1914) for Husted/Moreno terms. No duplicate issues were opened. These searches establish the reviewed corpus/issue scope, not global absence of other announcements.

## Local validation receipt

- Schema release check: PASS, immutable StarLang `765f1673851192bcaf1cdd2f35c47608f979b079`, Python and Nim source pins consistent.
- Packet: all 28 documents accepted by the strict canonical create command and generated runtime.
- `python -m unittest tests.test_columbus_public_events_packet -v`: 5 tests, all PASS.
- Consumer suite: 6 tests attempted; 5 PASS, 1 ERROR because `bin/starintel-validate` is absent. This is an unavailable native dependency, not a successful full gate.
- Nim/Nimble is not installed; direct download from nim-lang.org was blocked by the environment proxy (403). Hosted native validation on the published head is required. A full local gate is not claimed.
- After installing missing pytest/pypdf dependencies, full unittest discovery ran 311 tests in 57.073s: 294 passed, 11 failures and 6 errors, all remaining failures/errors requiring absent native site/ingest/validator binaries. This run preceded the final per-event Mission split/exporter repair; the final changed surfaces are covered by the focused run below.
- Final focused packet/exporter/importer suites: 21 tests PASS. Canonical explicit-ID lookup now accepts `id` as well as `_id`; regression coverage also checks duplicate-carrier suppression and fail-closed unversioned changes. General canonical update ingestion remains limited: changed existing documents without comparable integer versions are rejected; this new-ID packet does not rely on that path.
- The historical Python full-corpus validator was stopped after reaching approximately 12 GB RSS in this constrained environment; no result or site-gate success is claimed. Both mandatory native commands were unavailable (exit 127).

## Applied-state verification boundary

The canonical packet is persisted on the PR branch. It is not yet merged into main, imported into the repository's normalized `db/`, or proven applied to a live service. Both parent PRs #2740 and #2744 were still draft when checked; they must become eligible before this stacked change can be merged to main through the approved workflow.

The maintained workflow defaults to `https://ingest.starintel.actor`, but this environment has neither `STAR_SERVER_API_KEY` nor `STAR_INGEST_URL` configured. The repository control file separately says live ingestion remains fail-closed pending credential repair. No credentialed readback, workflow dispatch, queue activation, or network submission was attempted. A successful PR importer test is not a runtime ingestion receipt. Durable readback of all 28 matching IDs and document values is still required after an authorized live import; HTTP acceptance alone is insufficient.

Bounded local replay (repository transactional importer, no network):

```sh
python scripts/starintel.py import \
  digs/columbus/2026-10-11-public-event-announcements/starintel-documents.jsonl \
  --root /tmp/columbus-event-replay
```

Read back the 28 normalized files using `starintel_doc.store.iter_corpus(Path('/tmp/columbus-event-replay'))`, compare their complete parsed documents by `id` against the packet, and run `validate_repository` on that isolated root. This checks local persistence and searchability only. Merge export can be replayed without contacting the service:

```sh
python scripts/export_starintel_documents.py \
  --diff 638e51e48b5b1688ae80747548b6de4fc0de2e4b > /tmp/columbus-event-export.jsonl
```

## Reproduction

Install the exact Python runtime in `schema/starintel-runtime.lock.json`, and check out its pinned Nim companion at `.starintel-doc-nim` for release agreement. Then:

```sh
python scripts/schema-release.py check
python scripts/build_columbus_public_events_packet.py
python -m unittest tests.test_columbus_public_events_packet -v
python -m compileall -q starintel_doc scripts
git diff --check
```

The builder calls the repository canonical `create` CLI for every document before writing the packet. No normalized records are imported into the repository DB; bounded replay uses an isolated temporary DB. Full native corpus/site validation remains required before readiness or merge; keep this change draft until the exact published head passes required CI. No deployment or live collection is part of this change.
