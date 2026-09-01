# Auto-Dig Research Output

**Run status:** This pass opened the authoritative task context (`greenville-nc-ring-camera-detention-phone-unlock`, issue https://github.com/lost-rob0t/starintel-gpt-auto-dig/issues/2284), executed three Brave research operations (web, news, LLM-context), and captured their outputs as registered result contexts — but the wall-clock synthesis reserve activated before those outputs could be inspected. **No external web content was actually read this run.** Everything below is therefore either (a) sourced from the authoritative briefing itself, (b) clearly-labeled general background knowledge, or (c) explicitly unresolved. No verification of any incident-specific claim was performed, and none is claimed.

## Findings

**1. Fact baseline (from the authoritative task context — allegations and leads, not verified findings).**
The subject is a Greenville, North Carolina Police Department (GPD) incident in which officers investigating shots fired at an apartment complex on Mosley Drive sought Ring-camera footage from a nearby resident. Per the briefing's reported encounter facts (derived from the Lato's Law video transcript supplied as a seed lead), the resident declined to show the footage; an officer allegedly stated she could either show the footage or officers would remove the camera, seek a warrant, and keep her up all night; she was placed in handcuffs; and an officer allegedly entered/reached into her residence, retrieved her phone, and held it to her face to unlock it. A formal complaint was filed, and The Daily Reflector (per the video's citation) reported GPD placed the primary officer on administrative leave pending an internal review. Seed video: "Officer Handcuffs Woman for Not Sharing Ring Cam Footage," https://www.youtube.com/watch?v=KP2SJb3soLE

**2. Reporting constraints carried into findings (per the task's own rules).** The YouTube transcript and the resident's allegations are leads, not findings. Administrative leave is not discipline and is not a finding of wrongdoing. Consent must not be inferred merely because the device was ultimately accessed. Whether the resident was a suspect, witness, or simply the controller of a camera thought to contain evidence is an open question. No characterization of the officer's conduct as unlawful or unconstitutional is supported by anything this run gathered.

**3. General legal background (well-established, incident-verification still required).** Under the Fourth Amendment, warrantless entry into a home and warrantless search of a phone are presumptively unreasonable absent an exception such as consent or exigency; *Riley v. California*, 573 U.S. 373 (2014) requires a warrant for cellphone searches incident to arrest. Whether officers may physically force a detainee's biometric feature (face/fingerprint) to unlock a device is a contested, unsettled area — courts have split on treating compelled biometric unlocking like compelled passcode disclosure. Amazon's stated policy is to require valid legal process (warrant/court order/subpoena) to disclose Ring user footage; the Neighbors law-enforcement portal was discontinued in 2023. These general propositions still need primary-source confirmation in the next pass before being attached to this incident.

## Evidence

**Evidence actually held this run:**
- **Authoritative task issue (primary for scoping, not for incident facts):** https://github.com/lost-rob0t/starintel-gpt-auto-dig/issues/2284 — full brief read via context slice; supplies subject, dataset routing (reuse canonical StarIntel public-safety/police-accountability dataset; do not create a standalone Ring dataset), seed leads, constraints, dedupe key, and completion criteria.
- **Seed video lead:** https://www.youtube.com/watch?v=KP2SJb3soLE (Lato's Law) — not watched this run; transcript facts are second-hand via the briefing.
- **Outlet lead:** The Daily Reflector (Greenville, NC newspaper, https://www.reflector.com) — cited by the video as reporting the administrative-leave decision; specific article not located or read this run.
- **Search audit trail:** three Brave operations completed with status `ok` on 2025-run timestamp 1788278404–405 and were registered as result contexts `result_call_4061862d87d64c7283cf1a96` (web search: "Greenville North Carolina police handcuffed woman Ring camera footage unlocked phone with her face"), `result_call_02053b748d854f9a80a742a1` (news search: "Greenville NC police officer administrative leave Ring video woman handcuffed phone unlocked"), and `result_call_335e9942c83542c8bde6ad36` (LLM-context: Mosley Drive / shooting investigation query). Their contents (approx. 21 KB, 9 KB, 57 KB) were **not inspected**: the first inspection attempt used the wrong alias (bare call id, which the runtime reported as `unknown_context_alias`, while listing the correct `result_call_…` aliases), and the evidence-closure boundary arrived before a corrected read. These outputs are recoverable in a follow-up pass.

**Claim-to-evidence mapping:**

| Claim | Status | Source of status |
|---|---|---|
| Shots-fired investigation on Mosley Drive prompted the camera request | Reported (unverified) | Briefing's transcript summary |
| Resident handcuffed after declining to show footage | Allegation (unverified) | Briefing; seed video |
| "Show footage or we remove camera / get a warrant / keep you up all night" | Officer-statement allegation (unverified) | Briefing; seed video |
| Phone retrieved and unlocked with her face | Allegation (unverified) | Briefing |
| Formal complaint filed | Reported (unverified) | Briefing |
| Officer on administrative leave pending internal review | Reported (unverified) | Daily Reflector via seed-video citation |
| Footage/device data actually seized, copied, or accessed | Unknown | No evidence gathered |
| Ring/Amazon legal process sought separately | Unknown | No evidence gathered |

## Unresolved / Follow-up

**Mechanical fix (cheapest first step):** re-read the three registered result contexts using the correct `result_call_…` aliases listed above — they already contain the search payload from this run. Note for future turns: registered tool results use a `result_call_<id>` alias, not the bare call id.

**Verification tasks for the next pass:**
1. Watch/transcribe the seed video (https://www.youtube.com/watch?v=KP2SJb3soLE) and timestamp the exact encounter sequence and officer statements.
2. Locate The Daily Reflector article(s) on the administrative-leave decision (site search at https://www.reflector.com; likely paywalled — attempt archive or library access).
3. Obtain primary GPD records: incident/report number for the Mosley Drive shots-fired call, dispatch/CAD records, and body-camera footage (via City of Greenville public-records request).
4. Identify the primary officer and involved officers only through public records/official releases.
5. Determine the documented legal justification, if any, for the handcuff detention, the home entry, and the phone retrieval/unlock; request any search-warrant applications/returns (including any Ring/Amazon demand).
6. Confirm the formal complaint, internal-affairs review status, findings, and any discipline, retraining, resignation, referral, or litigation (NC court records, PACER if federal).
7. Verify GPD policy text on witness/evidence requests, detention, consent searches, electronic devices, biometric unlocking, and exigent circumstances (GPD policy manual / Law Enforcement Accreditation materials).
8. Check for civil claims or attorney correspondence and any prosecutor/district-attorney involvement.
9. Confirm the general legal propositions (*Riley*; biometric-unlock case-law split; Amazon/Ring legal-process policy, current Amazon Transparency Report) against primary sources before binding them to this incident.

**Falsification criteria (explicit):** (a) Bodycam showing the resident voluntarily provided footage or consented to the phone search would falsify the coercive-unlock allegation. (b) A documented warrant or exigency memo covering the home entry/phone search would falsify "no documented authority." (c) GPD or court records showing the resident was a suspect, rather than a camera owner/witness, would alter the Fourth Amendment analysis. (d) Daily Reflector or GPD statements contradicting administrative leave, or records showing leave predated the complaint for unrelated reasons, would falsify the accountability-chain narrative.

**Capability that would materially improve the next pass:** (i) pre-validated alias handling for registered result contexts (avoid the one-turn alias-mismatch cost); (ii) direct transcript extraction for the YouTube seed; (iii) paywalled-archive access (e.g., archive.today or library proxy) for Daily Reflector articles; and (iv) a public-records request tracker for GPD bodycam/CAD/IA-file requests, which are the decisive primary sources and are unlikely to surface via search alone.
