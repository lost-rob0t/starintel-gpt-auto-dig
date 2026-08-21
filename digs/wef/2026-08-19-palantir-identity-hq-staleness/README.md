# Palantir identity resolution and WEF headquarters staleness

## Selection

This hourly pass used run seed `20260819125206`. The current topic manifest exposes eight topic views. `offshore-leaks` was excluded by the recent-run anti-repeat rule because the immediately preceding successful hourly sequence included the Energia Global offshore-leaks pass; the most recent recovered pass was `dark-academia` / ECFR. The first seeded topic draw landed on `occrp-aleph`, but its only explicit bootstrap target is blocked on authenticated collection visibility, so it was excluded from the actionable frontier. The next actionable seeded topic was `wef`.

Within the WEF-connected frontier, the pass selected queued target `starintel:investigation-target:palantir-org-id-resolution`, which explicitly asks whether `starintel:org:palantir-technologies-inc` and `starintel:org:palantir-technologies` are the same operating/legal organization.

The complete executable target frontier was not reconstructed in this connector-only run, so this packet does not invent an exact global actionable-target count.

## Identity finding

Primary-source evidence supports treating the two records as representations of the same Palantir organization, while preserving the distinction between the legal issuer name and WEF's display name:

- the SEC identifies the filer as **Palantir Technologies Inc.**, CIK `0001321655`;
- the WEF organization profile is titled **Palantir Technologies** and links to Palantir's company website;
- WEF's Alex Karp profile calls him CEO and co-founder of **Palantir Technologies Inc.**, directly bridging WEF's display-name surface to the legal issuer name;
- WEF's 2026 partner surfaces list **Palantir Technologies**.

This packet records the resolution as analysis evidence. It does not hand-edit normalized DB IDs or silently rewire relations. Canonical ID consolidation should use the repository's scripted DB writer/import path so all references are updated transactionally.

## HQ / location finding

The identity pass exposed a source-freshness conflict that matters for location enrichment. WEF's current Palantir organization profile still says the company is headquartered in Denver, Colorado. Palantir's own February 17, 2026 principal-executive-office notice and SEC filings place the public principal executive office at **19505 Biscayne Boulevard, Suite 2350, Aventura, Florida 33180**. The normalized Palantir Inc. record already carries that source-backed Aventura location.

The WEF text is therefore preserved as a stale/conflicting third-party profile claim, not promoted over the newer company/regulatory evidence. A bounded follow-up target asks when WEF updates the profile and whether it explicitly changes its headquarters wording.

## Current-news scan

A current search through August 19, 2026 checked Palantir first-party/investor surfaces, SEC results, WEF current organization/partner pages, and recent reporting queries. No newly published item in the search window materially changed the identity or headquarters conclusion. No filler event was created.

## Evidence boundaries

- `principal executive office` is the exact company/SEC semantic and is not silently broadened into every possible meaning of `headquarters`.
- WEF's Denver text is evidence about WEF's profile content, not evidence that the newer SEC/company address is false.
- WEF participation/partnership does not imply control, policy agreement, or misconduct.
- No private residence or inferred coordinates are collected.

## Validation intent

The packet uses only executable v0.9.0 `analysis`, `investigation-target`, and `research-pass` fields and lives outside normalized `db/`. Required GitHub merge-gate workflows must pass on the exact PR head before merge.