# Auto-Dig Research Output

## Findings

**Established (multi-source): The current CEO of Mozilla Corporation is Anthony Enzor-DeMeo.**
- The seed source, Mozilla's official leadership page ([mozilla.org/en-US/about/leadership/](https://www.mozilla.org/en-US/about/leadership/)), fetched directly, states: *"As CEO of Mozilla Corporation, Anthony leads the vision and corporate strategy for the nonprofit-backed tech company behind the Firefox web browser."* It identifies him fully as Anthony Enzor-DeMeo, notes he joined Mozilla in 2024 as General Manager of Firefox, and the same page references 2026-dated activity (e.g., MZLA's "Thunderbolt" launch), indicating the page is current.
- Mozilla's own press release (issued via PR Newswire, "SOURCE Mozilla Corporation", dateline December 16, 2025) announces *"the appointment of Anthony Enzor-DeMeo as Chief Executive Officer of the Mozilla Corporation"* and quotes him as "incoming CEO of Mozilla Corporation". ([prnewswire.com](https://www.prnewswire.com/news-releases/mozilla-appoints-anthony-enzor-demeo-as-ceo-to-lead-the-next-era-of-user-first-trusted-technology-302642829.html))
- Independent corroboration: The Register ([theregister.com, 2025-12-16](https://www.theregister.com/2025/12/16/mozilla_corporation_new_ceo/)), Times of India ([indiatimes.com](https://timesofindia.indiatimes.com/technology/tech-news/mozilla-brings-changes-to-company-leadership-anthony-enzor-demeo-appointed-as-ceo-former-apple-exec-joins-as-cmo/articleshow/126013489.cms)), and Wikipedia's Laura Chambers article all report the same appointment.

**Established (multi-source): Transition history.** Mitchell Baker stepped down as CEO of Mozilla Corporation on February 8, 2024, replaced by board member Laura Chambers as interim CEO (Mozilla blog [blog.mozilla.org](https://blog.mozilla.org/en/mozilla/a-new-chapter-for-mozilla-laura-chambers-expanded-role/); Fortune; The Register; Wikipedia). Chambers served as interim CEO from February 2024 to December 2025 and then returned to the Mozilla Corporation Board of Directors when Enzor-DeMeo took over (press release; The Register). Other changes announced alongside: John Solomon as CMO, Ajit Varma promoted to Head of Firefox.

**Falsification criteria (load-bearing):** The "Enzor-DeMeo is current CEO" finding would be falsified by (a) the leadership page no longer listing him under the CEO heading, (b) a Mozilla announcement of a subsequent leadership change dated after 2025-12-16, or (c) a credible report of resignation/termination. None of these were observed; the live fetch of the seed page returned him as CEO.

## Evidence

| Claim | Source URL | What it directly supports |
|---|---|---|
| Anthony Enzor-DeMeo is CEO of Mozilla Corporation | https://www.mozilla.org/en-US/about/leadership/ (fetched) | Primary Mozilla source; biography begins "As CEO of Mozilla Corporation, Anthony leads the vision and corporate strategy…" — satisfies the request's primary-source criterion |
| Mozilla appointed Enzor-DeMeo as CEO (official announcement, Dec 16, 2025; Chambers outgoing; Solomon CMO; Varma Head of Firefox; Chambers returns to board) | https://www.prnewswire.com/news-releases/mozilla-appoints-anthony-enzor-demeo-as-ceo-to-lead-the-next-era-of-user-first-trusted-technology-302642829.html (fetched; "SOURCE Mozilla Corporation") | Primary official press release naming him in the role and dating the transition |
| Independent coverage of the Dec 2025 appointment and successor relationship | https://www.theregister.com/2025/12/16/mozilla_corporation_new_ceo/ ; https://timesofindia.indiatimes.com/technology/tech-news/mozilla-brings-changes-to-company-leadership-anthony-enzor-demeo-appointed-as-ceo-former-apple-exec-joins-as-cmo/articleshow/126013489.cms (search results) | Second/third unrelated origins corroborating the appointment |
| Baker → Chambers interim transition, Feb 8, 2024 | https://blog.mozilla.org/en/mozilla/a-new-chapter-for-mozilla-laura-chambers-expanded-role/ (Mozilla blog, search result) ; https://fortune.com/2024/02/08/mozilla-firefox-ceo-laura-chambers-mitchell-baker-leadership-transition/ | Establishes the interim CEO period preceding the current appointment |
| Chambers interim tenure Feb 2024–Dec 2025 | https://en.wikipedia.org/wiki/Laura_Chambers (search result) | Corroborates timeline; cites Mozilla's Dec 16, 2025 "Mozilla's Next Chapter" piece |

## Unresolved / Follow-up

- **Fully answered core goal:** current CEO identified (Anthony Enzor-DeMeo) with two primary Mozilla-sourced URLs (leadership page and official press release). No required surface from the request (people: Baker, Chambers, Enzor-DeMeo; organization: Mozilla Corporation; jurisdiction: US-based corporation; record: leadership page + announcement; date range: Feb 2024–present) went uncovered within scope.
- **Minor follow-up for the canonical record (out of this run's lane):** locate and cite the canonical `blog.mozilla.org` URL for the December 16, 2025 "Mozilla's Next Chapter" post (referenced by Wikipedia but not directly surfaced by search in this run) as an alternative on-domain primary link to the PR Newswire distribution copy.
- **Date precision:** exact effective date Enzor-DeMeo assumed the role (announcement date Dec 16, 2025 is established; a distinct "effective as of" date, if any, was not stated in fetched sources).
- **Tooling that would improve the next pass:** nothing beyond current Brave/Fetch capability was needed; a direct search restricted to `site:blog.mozilla.org` would have surfaced the canonical announcement post faster.
