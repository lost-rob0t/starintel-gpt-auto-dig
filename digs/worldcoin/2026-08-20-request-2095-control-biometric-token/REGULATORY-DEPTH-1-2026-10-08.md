# THE ORB VERSUS THE REGULATORS — primary-source depth 1

**Auto-Dig request:** [#2095](https://github.com/lost-rob0t/starintel-gpt-auto-dig/issues/2095)  
**Dataset:** `worldcoin`  
**Research pass:** `request-2095-regulatory-depth-1-2026-10-08`  
**Reviewed:** 2026-10-08  
**Status:** Bounded historical-regulator pass; NOT an October 2026 operating-status census, NOT the full global investigation.

The word **"banned"** is too blunt for the evidence. These authorities took materially different actions: an urgent time-limited processing restriction, a temporary biometric-collection restriction, a cease-collection enforcement notice after a privacy-law finding, a cross-border lead-authority reassignment, a corrective GDPR order, and a ban on paying people in exchange for iris collection. Those distinctions change the story.

## BANNED, PAUSED, BACK AGAIN? — seven events we can document

| Decision / statement date | Jurisdiction | Authority | Documented action | What the source does **not** establish |
| --- | --- | --- | --- | --- |
| 2024-03-06 | Spain | AEPD | Emergency provisional order for Tools for Humanity to stop Worldcoin biometric collection/processing and block previously collected data; Article 66(1) GDPR measure limited to a maximum three months. | Permanent ban; whether it is still operationally restricted in October 2026. |
| 2024-03-25 (published 03-26) | Portugal | CNPD | Urgent provisional limitation on Worldcoin Foundation's Orb iris/eye/face collection pending inquiry, highlighting minors' rights. | Permanent ban or a final adverse judgment. |
| 2024-05-22 | Hong Kong | PCPD | Privacy-law contravention findings and an enforcement notice directing Worldcoin Foundation to cease public iris/face scanning and collection in Hong Kong. Worldcoin confirmed 8,302 scanned participants. | Any finding about all World ID services worldwide; subsequent compliance without new evidence. |
| 2024-07-10 | Portugal / EU | CNPD | CNPD identified Bavaria's BayLDA as the lead GDPR supervisory authority based on an establishment in Germany, while CNPD remained a concerned authority. | Cancellation of the original concerns or vindication of biometric data practices. |
| 2024-12-19 | Germany / EEA | BayLDA | GDPR corrective measures: establish an adequate data-erasure procedure once the decision becomes final; seek express consent for specified processing; delete certain datasets collected without sufficient legal basis. The company had announced a planned challenge. | That a lawsuit is concluded, that deletion has been implemented, or that a fine was imposed by this particular announcement. |
| 2025-01-24 (effective 01-25) | Brazil | ANPD | Preventive restriction on offering WLD or other financial compensation for iris collection; also demanded a published data-protection-officer identification. | A blanket prohibition on all iris verification or World Chain operations. |
| 2025-02-11 | Brazil | ANPD | Board denied Tools for Humanity's appeal and maintained the financial-compensation restriction, refusing another 45 days to adjust. | Current order status in October 2026 or a prohibition on all World ID authentication. |

### What the documents show

**Hong Kong is a substantiated enforcement finding, not merely complaints.** The PCPD explicitly found contraventions of collection, retention, transparency, and access/correction obligations. Its notice instructed Worldcoin Foundation to cease iris and face image collection using Orbs in Hong Kong. Source: [PCPD findings and enforcement release, 22 May 2024](https://www.pcpd.org.hk/english/news_events/media_statements/press_20240522.html).

**Spain and Portugal began with extraordinary interim restrictions.** Spain invoked Article 66(1) GDPR with a maximum three-month emergency window; Portugal ordered provisional restrictions on biometric collection in March. In July, Portugal confirmed BayLDA's lead-authority role under the EU cooperation mechanism. These documents should be treated as a chronology, not three independent permanent bans.

**The German order concerns data rights and lawfulness.** BayLDA's December 2024 press release identifies conditions on deletion rights, express consent, and particular unlawfully collected datasets. It specifically says the company intended litigation and leaves other complaint investigations and any fine proceeding to separate decisions.

**Brazil's instrument is narrower than a biometric ban.** ANPD restricted financial inducements to surrender iris biometrics; the February 2025 appeal decision maintained that specific measure. Its consent rationale cannot be turned into a claim that every World ID function was shut down.

## Primary-source ledger

1. Spain AEPD, 2024-03-06: https://www.aepd.es/en/press-and-communication/press-releases/agency-orders-precautionary-measure-which-prevents-Worldcoin-from-continuing-toprocess-personal-data-in-spain
2. Portugal CNPD, 2024-03-26: https://www.cnpd.pt/comunicacao-publica/noticias/cnpd-suspende-recolha-de-dados-biometricos/
3. Hong Kong PCPD, 2024-05-22: https://www.pcpd.org.hk/english/news_events/media_statements/press_20240522.html
4. Portugal CNPD, 2024-07-10: https://www.cnpd.pt/comunicacao-publica/noticias/cnpd-atualiza-informacao-sobre-o-caso-worldcoin/
5. Germany BayLDA, 2024-12-19: https://www.lda.bayern.de/media/pm/pm2024_08.pdf
6. Brazil ANPD, 2025-01-24: https://www.gov.br/anpd/pt-br/assuntos/noticias/anpd-determina-suspensao-de-incentivos-financeiros-por-coleta-de-iris
7. Brazil ANPD, 2025-02-11: https://www.gov.br/anpd/pt-br/assuntos/noticias/apos-recurso-administrativo-conselho-diretor-mantem-suspensao-de-pagamento-por-coleta-de-iris

No news article is substituted for a regulator's original description. Where a regulator's action dates and release dates differ, both are preserved.

## Typed 0.10.1 output

`starintel-documents-regulatory-depth-1.jsonl` contains **seven distinct `finding` documents** (one per decision/procedural milestone) and **one `finding` recording this bounded research pass**. It uses the immutable StarLang 0.10.1 generated `Finding` type: flat `id`, `dataset`, `dtype`, `schemaVersion`, `sourceUrls`, `provenance`, etc. `research-pass` is a `findingType`, **not** an invented `dtype` or nested v0.9 envelope.

All seven event IDs are stable and source-scoped. The research-pass finding refers to those IDs under its declared provenance map; it does not claim that a cross-repository on-chain relationship, named Orb operator, or individual controller has been proven by the regulatory actions.

## Next Auto-Dig B handoff — exact unresolved work

- **Current status and appeals:** Resolve the 2025–2026 BayLDA case/appeal docket, Spain and Portugal follow-ups, Hong Kong enforcement compliance, and any later Brazil ANPD disposition. Record source dates and jurisdiction-specific status; do not silently carry 2024 measures forward.
- **Expand the regulator map:** Source original Korean PIPC decisions and subsequent corrective-action status; official Kenya privacy/court determinations; any Philippine, Indonesian or other jurisdictional actions. Classify investigations vs orders vs court judgments separately.
- **Compare product generations:** Link the legally relevant iris-code and SMPC processing in the regulator decisions to the product/configuration/version at the time, not automatically to the October 2026 Orb code path.
- **Corroborate outcomes:** Seek company submissions, regulator findings, court documents, and procedural status; keep corporate claims and adverse findings independently attributable.
- **Do not close #2095:** Funding, token flows, exact administrative key custody, current governance, integration inventory, lobbying and deployment/operator mapping remain outside this bounded pass.

## Merge / publication gate

This is a research-slice proposal stacked on the unmerged StarLang 0.10.1 consumer PR #2740. Structural validation against the checked-in generated `Finding` definition was performed before commit. The repository-native full corpus, Nim, import, and static-site gates plus exact-head hosted CI remain required. Do not present this packet as live published or close the request before they pass and the changes merge.
