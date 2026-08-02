# Hunter Biden — BHR Partners depth 6 active-role and fund-lifecycle pass

**Dataset:** `hunter-biden`  
**Run:** `2026-08-01-bhr-partners-depth-6`  
**Schema:** StarIntel v0.9.0  
**Status:** source-backed findings plus source-qualified current-fund lead

## What this pass adds

This pass converts several depth-5 targets into graph findings:

- confirms through a March 2026 SEC annual report that Xin Wang remained described as a BHR venture partner while serving as Bayview Acquisition Corp.'s CEO and director;
- records that a 2023 Bayview filing instead used the title `Managing Partner`, creating a title-history reconciliation target;
- adds Xinzhong Li as a distinct BHR principal, with an SEC-sourced April 2013–September 2020 managing-partner and investment-committee tenure;
- records a source-qualified April 2026 Taizhou venture-fund lead naming the Shenzhen BHR successor as executive partner;
- maps the 2018 BHR Fund VIII structure, its BHR-linked manager and GP, its 2021 renaming to Shanghai Xiangmin, the BHR-linked exit, replacement manager, and first/only reported investment target.

## Key analytic correction

`Xinzhong Li`, `Li Xiangsheng`, and `Jonathan Li` are not merged. The packet creates a dedicated identity-resolution target because the English renderings and roles are materially different.

## Evidence boundary

- SEC filings are treated as official regulatory filings, but biographies remain issuer representations filed with the SEC.
- The Taizhou fund is encoded with `reported_*` semantics because only a third-party registry mirror was located.
- The BHR Fund VIII lifecycle is sourced to a published copy of a listed-company regulatory response; underlying agreements remain target documents.

## Counts

- Sources: 5
- Organizations: 8
- People: 1
- Relations: 13
- Investigation targets: 10
- Total records: 37
