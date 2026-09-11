# Potateking / realpotateking cross-platform attribution — issue #2335

Date: 2026-09-11
Run: potateking-crossplatform-2026-09-11

## Question
Is YouTube @potateking operated by the same operator as the Lemon8 @davemuthafukkingr (profile id `realpotateking`) / X @realpotateking / TikTok davemuthafukkingr cluster? What is the JimmyTalks-targeting context of Reddit u/Alternative-Park5963?

## Bottom line
- A candidate identity relation (`starintel:relation:lemon8-to-youtube-candidate-identity`, confidence 0.55) links the Lemon8 account to the YouTube account. It is explicitly NOT a merge; per-platform entities remain canonical.
- Supporting evidence is string/declaration-based: Lemon8 profile id `realpotateking` matches the X handle declared on the Lemon8 profile; Linktree (declared from Lemon8) links Twitch `potateking`, TikTok `davemuthafukkingr`, X `realpotateking`, Facebook share link.
- Counterevidence/alternatives preserved in the relation note: possible coincidental or impostor reuse of "potateking"; display-name mismatch (Potateking vs Davemuthafukkingrimes3.0); no observed third-party link Lemon8->YouTube content; persona text on Lemon8 not evidenced on YouTube.
- Reddit u/Alternative-Park5963 authored r/youtube post 1qjpk7p (2026-01-22) naming "JimmyTalks" as the targeted YouTuber; JimmyTalks remains an unresolved entity and the targeting relation is the author's claim only (confidence 0.3).

## Records
All documents were written through `scripts/create-db-document.py` (dataset `potateking-crossplatform-2026-09-11`) into canonical `db/<dtype>/`. 32 new documents this pass: 27 core docs (6 source, 8 entity, 1 social-media-post, 11 relation, 1 research-pass) plus 5 investigation-target docs from the recursive target selector. Full-corpus streaming validation: 7168 docs, 0 invalid (note: scripts/validate-db.py is OOM-killed in this container at EXIT 137; equivalent streaming validation of every db document passed with exit 0).

## Unresolved
- Ownership proof for X/TikTok/Twitch/Facebook accounts (login-consistent cross-references).
- Content-level corroboration between Lemon8 posts and YouTube channel content.
- Resolution of the actual "JimmyTalks" YouTube channel and whether the Reddit characterization is accurate.
- Whether the Facebook share page resolves to a named profile.
