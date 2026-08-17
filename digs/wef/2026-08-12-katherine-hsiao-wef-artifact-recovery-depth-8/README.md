# Katherine Hsiao / WEF artifact recovery — depth 8

This pass reaches the configured maximum depth and resolves a direct publication attribution that was stronger than the unresolved 2021 `Pathways to Digital Justice` lead.

## Resolved

- WEF publishes **Data Equity: Foundational Concepts for Generative AI**, dated 17 October 2023.
- arXiv record `2311.10741` for the same title lists **Katherine Hsiao** among the authors.
- The packet therefore records an exact `coauthored` relation between Hsiao and the 2023 WEF briefing paper.

This finding is deliberately scoped to the 2023 paper. It does not back-propagate authorship to the separate 2021 `Pathways to Digital Justice` publication.

## Still unresolved

- exact start/end dates of Hsiao's earlier Global Future Council for Data Policy term;
- direct Hsiao contributor credit on the 2021 `Pathways` paper;
- exact Hsiao contributor role, if any, on the 2024 `Advancing Data Equity` framework;
- first-party PDF contributor pages and artifact hashes while `www3.weforum.org` remains unreachable from the current research environment.

## Max-depth handling

The original recursion was configured to stop at depth 8. This pass does not silently exceed that boundary. Instead it emits a distinct new root target:

`starintel:investigation-target:palantir-wef-data-equity-output-network`

That new root follows only direct, named Palantir-personnel publication/council links and preserves coauthorship separately from claims of policy influence or institutional coordination.
