# Trilateral Commission regional legal and secretariat structure pass — 2026-08-08

## Scope

This pass tests whether the Commission's three regional groups can safely be modeled as one kind of organization. The evidence says no. North America has a U.S. tax-exempt legal entity, Europe has a separately registered French association, and Asia Pacific has a documented secretariat/operator succession from JCIE to the International House of Japan.

The resulting model must distinguish **regional group**, **legal entity**, **secretariat/operator**, **contact address**, and **registered establishment** rather than collapsing them into a single organization node.

## Findings

### 1. The European section has a concrete French association identity

France's official `L’Annuaire des Entreprises` lists:

- name: **ASSOCIATION SECTION EUROPEENNE COMMISSION TRILATERALE**
- SIREN: **507 983 153**
- legal form: `Association déclarée`
- status: active
- activity: other voluntary membership organizations (`94.99Z`)
- 2023 workforce band: 1–2 employees
- registered in SIRENE since **2008-01-01**
- also registered in the French National Register of Associations (RNA)

The government page records two establishments:

- SIRET `507 983 153 00010`, 5 rue de Téhéran, Paris 8e — closed **2023-11-24**;
- SIRET `507 983 153 00028`, Chez Vivien Associés, 3 rue de Monttessuy, Paris 7e — active since **2023-11-24**.

This is sufficient to create a distinct European legal-entity identity once normalized writes are performed through repository scripts.

### 2. Association-register history extends the European section back to 1983

An RNA-derived association index resolves the European section as RNA **W751064404** and reports:

- association creation: **1983-05-06**;
- publication of creation notice: **1983-05-28**;
- latest declaration: **2024-12-20**;
- status: active.

Its recorded purpose concerns study/reflection aimed at harmonizing political, economic, social, and cultural relations among industrialized Western Europe, North America, Japan, and third countries.

The 1983 association history and 2008 SIRENE registration date should **not** be treated as a contradiction requiring one date to be discarded. They refer to different registries/registration events. Preserve both with their provenance.

### 3. The Commission's published European secretariat address is not the same as the active French establishment

The current Commission website publishes the European Group at:

`95, rue d’Amsterdam, 75008 Paris, France`

The French government directory's active establishment is:

`Chez Vivien Associés, 3 rue de Monttessuy, 75007 Paris`

Therefore an operational/contact/secretariat address must not be silently promoted to the legal entity's active registered establishment. Both can be true for different purposes.

### 4. Asia Pacific has a documented secretariat succession

The Japan Center for International Exchange (JCIE) states that it served as the Asia Pacific Secretariat from the Commission's establishment in **1973 through 2024**, managing regional participation and conferences.

JCIE states that from **January 2025**, the **International House of Japan (I-House)** took over as Secretariat.

I-House independently confirms that it has served as Secretariat of the Trilateral Commission's Asia-Pacific Group since 2025.

This establishes time-bounded operational relations:

- JCIE `secretariat_for` Asia Pacific Group: 1973–2024;
- International House of Japan `secretariat_for` Asia Pacific Group: 2025–present.

Neither relation should be represented as ordinary Commission membership or as proof that the secretariat organization is legally identical to the regional group.

### 5. International House of Japan is itself a distinct nonprofit legal organization

I-House's corporate profile says it was established on **1952-08-27** and is headquartered at:

`5-11-16 Roppongi, Minato-ku, Tokyo 106-0032`.

Its institutional history says it became a **Public Interest Incorporated Foundation** on **2012-04-01**. It is therefore a source-backed organization node in its own right, not merely an address string for the Commission.

### 6. The Commission footer still points to JCIE after the secretariat transfer

The current Trilateral website footer correctly shows the Asia Pacific Group at International House of Japan's Roppongi address, but still displays `www.jcie.or.jp` as the regional website link.

JCIE and I-House both state that the secretariat transferred to I-House in January 2025.

This is another field-level freshness failure on `trilateral.org`: **address/operator state is current, linked-domain state is stale**.

### 7. Canadian and Mexican legal entities remain unresolved

The Commission's North America page says Canadian and Mexican groups are separately organized for membership selection and raising/expending funds, but this pass did not find sufficiently authoritative registry evidence to assign a distinct Canadian or Mexican legal entity.

Government records do independently establish current operational interaction with the North American Group—for example, Canadian ministers have attended/spoken at its meetings, and Mexico's foreign ministry documented a North American regional annual meeting—but those records do not establish separate incorporation.

Do not create Canadian or Mexican legal-entity nodes solely from regional-group wording.

## Data-model implications

1. Separate `regional_group`, `legal_entity`, and `secretariat/operator` identities.
2. Add time-bounded `secretariat_for` relations for JCIE and I-House.
3. Store contact/secretariat addresses separately from legally registered establishments.
4. Preserve SIREN/SIRET/RNA identifiers as entity-resolution keys for the European association.
5. Preserve multiple registry dates with their meaning rather than selecting one generic `founded` date.
6. Treat the stale JCIE footer link as source-freshness evidence, not as evidence JCIE still operates the secretariat.
7. Keep Canada/Mexico legal status `unresolved` until registry evidence is found.

## Next frontier

- retrieve official RNA/JOAFE records for W751064404 directly and reconcile historical addresses/names;
- determine the formal relationship between the European registered association and the website's European secretariat address;
- identify whether I-House receives or disburses Commission regional funds as secretariat, using I-House disclosures if available;
- search Canadian federal/provincial nonprofit registries and CRA data using historical name/address variants;
- search Mexican civil-association and tax/public-benefit registries using Spanish and English name variants;
- model these entities only through repository-scripted normalized writes after the research pass is approved.

## Sources

- https://annuaire-entreprises.data.gouv.fr/entreprise/507983153
- https://assoce.fr/waldec/W751064404/EUROPESE-SEKTIE-VAN-DE-TRILATERALE-COMMISSIE-SECTION-EUROPEENNE-DE-LA-COMMISSION-TRILATERALE
- https://www.trilateral.org/europe/
- https://www.trilateral.org/about/contact-us/
- https://jcie.org/programs/trilateral-commission/
- https://ihj.global/trilateral/en/about/
- https://ihj.global/en/about-disclo/
- https://ihj.global/en/about-index/
- https://www.canada.ca/en/innovation-science-economic-development/news/2024/11/minister-champagne-wraps-up-visit-to-silicon-valley.html
- https://www.gob.mx/sre/es/prensa/discurso-de-la-canciller-claudia-ruiz-massieu-en-el-15-encuentro-regional-anual-para-america-del-norte
