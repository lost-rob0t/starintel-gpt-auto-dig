# Auto-Dig Prolog false-success dogfood evidence

Source run: GitHub Actions `33502262680`
Source main SHA: `47016b3280997a2ca09cb13d1a5465acfda83a94`
Pinned Prolog-RLM: `a89711d504e6cc6c3fac789b7f0b6b0453aea23b`

The workflow concluded success, but the archived `rlm-result.json` did not contain a substantive investigation result. Its envelope was `prolog-rlm.trace.v1` / `auto_dig_rlm_result`, with payload term `ok`, while the final assistant content consisted of provider-style tool markup such as `to=multi_tool_use.parallel` and `to=functions.context_slice` rather than evidence-backed report prose.

This is a false-success regression fixture/evidence record. A future live run may count as end-to-end only when the runtime exposes a non-empty substantive final assistant answer and the workflow/runtime rejects tool-markup-only terminal responses.
