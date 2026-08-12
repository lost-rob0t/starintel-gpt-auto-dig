# Katherine Hsiao / WEF attribution — depth 7

This pass resolves the boundary between Katherine Hsiao's verified WEF council service and individual publication attribution.

## Findings

- WEF's current Hsiao profile directly states that she recently served on the Global Future Council for Data Policy.
- The current profile does not provide exact start/end dates.
- The WEF HTML page for `Pathways to Digital Justice` attributes the 2021 work at the council/collaboration level.
- The WEF launch page names six speakers and a moderator; Hsiao is not named on that launch-page speaker list.
- The official WEF PDF endpoint is exposed by the publication page but timed out in the current research environment.

No absence claim is made from the launch page, and no individual authorship of the 2021 paper is assigned to Hsiao without direct credit.

## Collector added

`scripts/scrape_wef_council_artifacts.py` discovers same-domain WEF pages/PDFs, downloads and SHA-256 hashes artifacts, optionally extracts PDF text with `pdftotext`, records requested name/topic mentions, respects robots where readable, and refuses to write staging output under `db/`.

`tests/test_scrape_wef_council_artifacts.py` covers URL normalization, WEF-only link extraction, PDF classification, and deterministic mention extraction.

## Next target

Depth 8 recovers WEF council/publication artifacts and resolves named Hsiao credits. The broader recursion remains bounded: council membership is not treated as endorsement of every output.
