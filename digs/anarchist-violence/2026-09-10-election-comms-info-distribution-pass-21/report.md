# Auto-Dig 2026 election information distribution pass 21

## Scope

One bounded PUBLIC political-discourse / communications + election-ecosystem enumeration pass for the `anarchist-violence` corpus. This pass preferentially opened new graph surface around public election-information production, API distribution, search/AI surfaces, civic-technology partnerships, and downstream public platform integrations rather than revisiting the voter-roll, texting, or ballot-mail clusters from recent passes.

## Coverage

Materialized 54 StarIntel v0.9 records: 11 source records, 12 organizations, 6 products/public information surfaces, 3 public people, 21 explicit evidence-supported relations, and 1 recursive investigation target. No inferred relation was promoted to direct observation in this pass. No identity collision was resolved by name similarity alone.

Primary graph surface includes Democracy Works; the Voting Information Project (VIP); Google and the Google Civic Information API; Google Search and Gemini; the Democracy Works Elections API; TikTok; Perplexity; OpenAI; Civic Alliance; CAA Foundation; Meteorite; Microsoft; HeadCount; Propeller; and TurboVote.

## Evidence and information flow

Current first-party material dated September 9, 2026 documents Democracy Works and Google continuing their election-information partnership for the 2026 U.S. midterms. Public election information from state and local election administrators, routed through Democracy Works/VIP, is surfaced through Google Search (including AI Mode and AI Overviews), the Gemini app, and the Google Civic Information API. Google separately states its 2026 election experiences use official state/local-government and Democracy Works data and AP election results.

Democracy Works states that VIP originated in 2008 with state/local election officials, The Pew Charitable Trusts, and Google, and that Democracy Works has operated the project since 2018. Its Elections API currently exposes additional downstream integration pivots including TikTok and Perplexity; a May 27, 2026 Democracy Works announcement documents election-information delivery to OpenAI products including ChatGPT.

Civic Alliance is represented as a distinct organization. Its public site identifies Democracy Works and CAA Foundation as co-founders and Meteorite as a build partner. Historical 2024 Democracy Works impact material is retained with date context for Microsoft/Civic Alliance and HeadCount/Propeller/TurboVote edges rather than being represented as newly observed 2026 activity.

## Provenance / source strategy

The pass prioritizes current first-party organization, platform, and developer documentation. Evidence domains represented directly in source records include `democracy.works`, `blog.google`, `developers.google.com`, and `civicalliance.com`. Historical material is explicitly described as historical in relation notes where applicable.

The local Git clone path was unavailable because DNS resolution for `github.com` failed in the runtime. Following repository policy, the pass uses the GitHub connector fallback to materialize canonical packet files on a fresh branch. Exact-head repository CI is therefore the authoritative validation gate; the PR must remain draft unless every required exact-head check succeeds.

## Recursive frontier

Expand additional named Elections API consumers; state/local election-office participation in VIP; official data submission/review paths; public election-center implementations; search/AI election-information surfaces; platform embeds; newsletters and public voter-information channels; upstream data partners; downstream media/API consumers; and Civic Alliance member/partner relationships when supported by first-party or otherwise strong public evidence.

Preserve the distinction between: (1) an election administrator publishing official information, (2) Democracy Works/VIP collecting or normalizing it, (3) an API/platform transporting it, and (4) a downstream product presenting it. Do not infer editorial control, endorsement, targeting, or coordination beyond what the evidence establishes.

## Canonical write path

Mature findings are materialized in this packet directory as v0.9 JSONL files. No generated normalized `db/` record was hand-edited. The fresh-branch packet is subject to the repository's complete exact-head StarIntel document and site validation before it may be marked ready or merged.
