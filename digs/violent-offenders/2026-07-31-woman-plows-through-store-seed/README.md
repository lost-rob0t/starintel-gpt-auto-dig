# Violent Offenders — “Woman Plows Through Store While Fleeing” seed

Initial source packet for the new `violent-offenders` dataset.

## Seed

- Video title: **Woman Plows Through Store While Fleeing**
- Video URL: https://www.youtube.com/watch?v=W1YNVWqPMZg
- Retrieved: 2026-07-31
- Current identity status: **unresolved**
- Current jurisdiction status: **unresolved**
- Current legal disposition status: **unresolved**

The upload is an investigative lead and provenance artifact. Its title, narration, captions, thumbnail, and edited footage do not independently establish a person's identity, criminal charge, conviction, sentence, or legal classification.

## Dataset scope

The dataset will track public-source cases involving alleged or adjudicated intentional violence, threatened violence, or dangerous conduct presenting an immediate risk of serious physical harm.

Each case must keep the following stages separate:

1. reported incident;
2. law-enforcement allegation;
3. arrest or booking;
4. filed charge;
5. adjudication or dismissal;
6. sentence and custody status;
7. appeal, expungement, or later correction.

A person must not be represented as convicted when the available evidence establishes only an allegation, arrest, or charge. A video title or uploader summary may seed research but cannot pass the publication gate by itself.

## First-pass resolution plan

1. Preserve the YouTube upload as a source record with the exact URL and title.
2. Extract available captions and identify agency names, officer names, dates, addresses, businesses, vehicles, case numbers, and quoted charges.
3. Identify the originating law-enforcement agency and obtain the agency release, incident report, arrest affidavit, or public-record metadata.
4. Resolve the suspect only from corroborating official or high-quality public sources.
5. Locate the court docket and preserve every filed count and disposition separately.
6. Represent victims, officers, businesses, vehicles, locations, events, and legal cases as separate typed records.
7. Store uncertainty and conflicting names explicitly; do not merge ambiguous identities.
8. Run the repository's canonical StarIntel writer and full merge validation before importing normalized records.

## Initial target graph

- source: YouTube upload `W1YNVWqPMZg`;
- event: reported vehicle flight and storefront collision;
- person: unresolved driver;
- org: unresolved law-enforcement agency;
- org: unresolved affected business;
- location: unresolved incident location;
- asset: unresolved vehicle;
- legal-case: unresolved criminal docket;
- claims: title-derived and narration-derived statements, attributed to the uploader until corroborated.

## Publication gate

A named person record may enter the public dataset only when identity is supported by at least one official source or by two independent reliable public sources that agree on the person, event, and jurisdiction. Conviction and sentence fields require a court record or an official court/prosecutor release.

## Status

`DRAFT` — dataset scaffold and source seed only. No normalized StarIntel records have been created yet because the executable schema writer and repository validation must be run against a checkout before DB import.
