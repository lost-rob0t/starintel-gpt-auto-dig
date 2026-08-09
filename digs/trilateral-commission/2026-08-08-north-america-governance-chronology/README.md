# Trilateral Commission North America governance chronology — 2016–2025

## Scope

This pass reconstructs the U.S. North American entity's dated officer/trustee history from annual Form 990 data and compares it with the Commission's current regional-leadership page. The purpose is to stop historical governance from being overwritten by a single current website snapshot.

## Findings

### 1. Joseph S. Nye Jr. is the filing-listed chairman in FY2016 and FY2017

IRS-derived Form 990 data lists:

- FY2016: Michael J. O'Neil — President & Treasurer; Mary M. Valder — Secretary; Joseph S. Nye Jr. — Chairman.
- FY2017: the same three roles remain, with O'Neil and Valder compensated and Nye listed as Chairman.

### 2. Meghan O'Sullivan is chair by FY2018 and remains filing-listed through FY2020

FY2018 and FY2019 filings list Meghan O'Sullivan as Chair, with Michael J. O'Neil still President & Treasurer. Karen Elliott House appears as North American Trustee / Executive Committee in FY2018 and as North American Trustee in FY2019.

FY2020 is a transition year: O'Neil is marked `President & Treasurer - Outgoing`, Richard Fontaine first appears as `Executive Director`, and O'Sullivan remains Chair.

The current Commission website still identifies Meghan L. O'Sullivan as North America Chair, so the chair role continues beyond the last tax-return year in which the extracted filing table explicitly displays it.

### 3. Richard Fontaine becomes the durable paid executive-director role from FY2020 onward

Extracted compensation records show Fontaine as Executive Director:

- FY2020: $40,000
- FY2021: $73,333
- FY2022: $95,000
- FY2023: $110,000
- FY2024: $110,000
- FY2025: $125,000

The current Commission page independently identifies Fontaine as Executive Director, North America Group.

This is a strong dated operational-role series, not just a biography assertion.

### 4. North American trustees rotate across filing years

The extracted Form 990 tables show:

- FY2018: Karen Elliott House — North American Trustee / Executive Committee
- FY2019: Karen Elliott House — North American Trustee
- FY2021: Marc Allen; Catherine Bertini
- FY2022: Carla Hills; Esther Brimmer
- FY2023: B. Marc Allen; Catherine Bertini
- FY2024: B. Marc Allen; Carla A. Hills
- FY2025: B. Marc Allen; Carla A. Hills; Joseph S. Nye Jr. — `North American Trustee (until 5/25)`

The series shows why `trustee_of` needs filing-year validity rather than a timeless edge.

### 5. Tax-return trustees/officers are not the same thing as the Commission's current Executive Committee

The current Commission page says the overall Commission has a 74-member Executive Committee and separately lists regional chairs, deputy chairs, executive directors, and regional Executive Committee members.

The Form 990 data, by contrast, reports officers/trustees of the U.S. tax-exempt North American legal entity.

These are overlapping governance surfaces but not interchangeable categories. A person can appear in one or both without the predicates meaning the same thing.

## Data-model implications

1. Represent Form 990 roles as annual/time-bounded governance observations tied to `Trilateral Commission North America`, EIN `23-7309933`.
2. Preserve exact filing labels such as `Chairman`, `Chair`, `President & Treasurer`, `Executive Director`, and `North American Trustee`.
3. Do not map `North American Trustee` automatically to the global/regional `Executive Committee` unless the source explicitly says both.
4. Separate current website leadership from filed legal-entity governance.
5. Use transition markers such as `Outgoing` and `until 5/25` as end-date evidence, not prose to discard.
6. Compensation values are filing-year observations and should not become a person's timeless salary.

## Next frontier

- extract the full officer/trustee tables from each raw Form 990 XML to capture people hidden behind `View more people`;
- extend the series backward before FY2016 and forward when new filings appear;
- resolve each named officer/trustee to canonical person identities before creating normalized relations;
- compare tax-return governance with current Executive Committee membership without conflating the two.

## Sources

- https://projects.propublica.org/nonprofits/organizations/237309933
- https://www.trilateral.org/about/members-fellows/
- https://www.trilateral.org/people/richard-fontaine/
