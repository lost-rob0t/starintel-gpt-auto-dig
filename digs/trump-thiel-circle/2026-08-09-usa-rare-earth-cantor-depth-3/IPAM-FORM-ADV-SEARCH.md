# IPAM Form ADV / Freedom Fund public-source search

**Run:** `usa-rare-earth-cantor-depth-3-2026-08-09`  
**Research cutoff:** 2026-08-09  
**Status:** public-source boundary documented; primary archive extraction still pending

## Objective

Use SEC Investment Adviser Public Disclosure and EDGAR records to identify additional natural persons, related entities, private-fund details, or service providers behind **Inflection Point Freedom Fund LP** and **Inflection Point Asset Management LLC (IPAM)**.

## Confirmed adviser identity

SEC/IAPD identifies:

- **Inflection Point Asset Management LLC**
- CRD **340616**
- SEC number **802-135401**
- status: **Exempt Reporting Adviser — Active**
- effective date: **January 23, 2026**
- principal location: Miami Beach, Florida

IPAM is not shown as a fully registered investment adviser; it files reports as an exempt reporting adviser.

## Important Form ADV scope limitation

SEC documentation states that exempt reporting advisers file only portions of Form ADV rather than the full registered-adviser form. SEC monthly adviser-information reports are also described as subsets of Form ADV data.

That means absence of a field from the monthly public spreadsheet cannot automatically be treated as proof that a private-fund fact does not exist in the underlying adviser filing.

## SEC monthly archive

The SEC adviser-data page publishes monthly ZIP archives for exempt reporting advisers, including:

- December 2025;
- January 2026; and
- February 2026.

The January/February files are the most relevant for determining what IPAM reported when it became an active ERA on January 23 and whether it amended the report after the January 26 USAR PIPE.

### Tooling boundary

The current research environment resolved the official SEC ZIP filenames but could not extract the binary ZIP payload through the available web/download path.

This is a **research-tool access limitation**, not a finding that the underlying SEC data are unavailable to the public.

The archive should be retrieved later through a normal SEC-compliant HTTP client and parsed locally for CRD 340616.

## EDGAR pivot

Separate EDGAR filings identify IPAM as a reporting/beneficial-ownership person in multiple Inflection Point SPAC structures.

Later 2026 Schedule 13G and Section 16 filings continue to describe Michael Blitzer as a control person of IPAM in sponsor/entity contexts and show him signing for IPAM as Chief Investment Officer.

That is consistent with the corrected governance classification already recorded in this pass:

- **company-level IPAM control:** still attributed to Blitzer in later SEC filings;
- **specified fund-position voting/dispositive authority:** moved into a three-person majority investment committee after the January 1 governance amendment.

## Freedom Fund exact-name filing search

Targeted EDGAR/public-index searches were run for:

- `Inflection Point Freedom Fund LP` + Schedule 13G;
- `Inflection Point Freedom Fund LP` + Schedule 13D;
- `Inflection Point Freedom Fund LP` + Form D;
- `Inflection Point Freedom Fund GP LLC`; and
- exact Freedom Fund name plus limited-partner/distribution terms.

### Result

No standalone Freedom Fund Schedule 13D/13G or Form D filing was located through the indexed public searches performed in this pass.

This is a **negative indexed-search result only**. It should not be converted into a legal conclusion that no filing obligation existed or that no filing was made under another reporting person/entity name.

The SEC USAR prospectus remains the primary source identifying Freedom Fund's GP, investment manager, investment committee, and related-party economics.

## Current source-backed Freedom Fund roster remains

Natural persons:

1. **Michael Blitzer** — investment committee; GP/SLP member; USAR board chairman.
2. **Kevin Shannon** — investment committee; GP/SLP member; USAR board adviser.
3. **David Kronenfeld** — explicitly named Freedom Fund limited partner; documented pro-rata distribution recipient.
4. **Unnamed third investment-committee member** — role confirmed, identity not disclosed in reviewed SEC filings.

Entities:

- Inflection Point Freedom Fund LP — purchaser/vehicle.
- Inflection Point Freedom Fund GP LLC — general partner.
- Inflection Point Asset Management LLC — investment manager.

## What the adviser search has NOT exposed yet

- Freedom Fund formation date;
- gross asset value;
- full LP roster;
- capital commitments;
- third investment-committee member;
- GP/SLP ownership percentages;
- carry/performance-allocation percentage;
- administrator;
- auditor;
- custodian;
- prime broker;
- placement/marketing agent for Freedom Fund interests;
- full January/February Form ADV filing history.

## Highest-value next acquisition

Retrieve and diff the official SEC exempt-adviser datasets for:

`December 2025 -> January 2026 -> February 2026`

Filter on:

- CRD 340616;
- SEC 802-135401;
- `INFLECTION POINT ASSET MANAGEMENT LLC`.

Then extract every populated field from Items 1, 2, 3, 6, 7, 10 and 11, plus any private-fund/related-person data carried in the archive.

If the monthly subset does not expose the Freedom Fund, obtain the underlying IAPD Form ADV filing and amendment history directly.

## Primary source spine

- IAPD firm summary: https://adviserinfo.sec.gov/firm/summary/340616
- SEC adviser-data page: https://www.sec.gov/foia-services/frequently-requested-documents/information-about-registered-investment-advisers-exempt-reporting-advisers
- SEC Form ADV data information: https://www.sec.gov/foia-services/frequently-requested-documents/form-adv-data
- SEC EDGAR API documentation: https://www.sec.gov/search-filings/edgar-application-programming-interfaces
- USAR Freedom Fund disclosure: https://www.sec.gov/Archives/edgar/data/1970622/000121390026011595/ea0269018-02.htm

## Current classification

The public source record still supports only **Blitzer, Shannon, Kronenfeld and one unnamed committee member** in Freedom Fund's natural-person chain. The adviser-data route remains open, but the archive itself has not yet been successfully extracted in this research environment. No additional Freedom Fund LP should be inferred from the broader Inflection Point Fund I network.