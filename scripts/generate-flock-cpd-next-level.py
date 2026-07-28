#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from starintel_doc.validation import validate_document

GENERATED_AT = "2026-07-26T12:00:00-04:00"
DATASET = "flock-safety-columbus-cpd-next-level-2026-07-26"
OUTPUT_DIR = Path("digs/flock-safety/2026-07-26-columbus-cpd-next-level")

URLS = {
    "ord_0166": "https://columbus.legistar.com/LegislationDetail.aspx?GUID=C5009076-68A9-4FBF-8FA1-DDAB6017CF3B&ID=6014679&Options=&Search=",
    "ord_3173": "https://columbus.legistar.com/LegislationDetail.aspx?GUID=ECAA5E62-4E70-4B41-ABB9-F2C2D78C7360&ID=6427988&Options=&Search=",
    "insight_ac": "https://columbus.legistar.com/View.ashx?GUID=2995841A-313C-4092-9DD6-BF79CA0BBF18&ID=12469980&M=F",
    "bid_3173": "https://columbus.legistar.com/View.ashx?GUID=4F99C091-E49D-4630-B7F1-0A09F5F148B1&ID=12469981&M=F",
    "sts_3173": "https://columbus.legistar.com/View.ashx?GUID=DC14E2A4-0A22-46BA-A3BD-55A1E7E01069&ID=12469988&M=F",
    "ord_3181": "https://columbus.legistar.com/LegislationDetail.aspx?From=RSS&GUID=76B3DB80-9EF4-4657-A21F-24773FB0E5DD&ID=7043675",
    "quote_3181": "https://columbus.legistar.com/View.ashx?GUID=EEE48DA7-05AC-443F-80A1-7EB85D0E482A&ID=13601905&M=F",
    "bid_3181": "https://columbus.legistar.com/View.ashx?GUID=4335FB20-0E53-4982-A083-C368C1B17638&ID=13601906&M=F",
    "ord_1510": "https://columbus.legistar.com/LegislationDetail.aspx?FullText=1&GUID=32C056FC-D5FD-4C8D-B6BF-E903E6B5A7F6&ID=7444898",
    "attachment_1510": "https://columbus.legistar.com/View.ashx?GUID=C3A169ED-01C5-48AC-858D-475632F093DA&ID=14311170&M=F",
    "records_minutes": "https://columbus.legistar.com/LegislationDetail.aspx?FullText=1&GUID=5E0C0C18-90C4-43D0-93F3-97833273958F&ID=7878913",
    "cpd_org": "https://www.columbus.gov/Services/Public-Safety/Police/About-the-Columbus-Division-of-Police/Organizational-Structure",
    "cpd_contact": "https://www.columbus.gov/Services/Public-Safety/Police/About-the-Columbus-Division-of-Police/Contact-the-Division-of-Police",
    "cpd_directives": "https://www.columbus.gov/Services/Public-Safety/Police/About-the-Columbus-Division-of-Police/Directives",
    "cpd_records": "https://www.columbus.gov/Services/Public-Safety/Police/About-the-Columbus-Division-of-Police/Highlighted-Areas/Police-PublicRecordsUnit",
    "wosu_jun25": "https://www.wosu.org/politics-government/2026-06-25/columbus-police-limit-nationwide-access-to-flock-surveillance-cameras",
    "wosu_jul11": "https://www.wosu.org/politics-government/2026-07-11/ginther-orders-columbus-police-to-stop-statewide-sharing-of-flock-cameras-after-audit-release",
    "wosu_jul15": "https://www.wosu.org/politics-government/2026-07-15/columbus-police-says-it-will-stop-using-flock-technology-if-asked-but-would-solve-fewer-crimes",
    "wosu_remy": "https://www.wosu.org/politics-government/2026-07-15/columbus-city-councilmember-emmanuel-remy-hesitant-to-cancel-citys-flock-camera-contract",
    "dispatch_audit": "https://www.aol.com/articles/columbus-audit-links-thousands-flock-214549884.html",
    "dispatch_hsi": "https://www.aol.com/articles/did-ice-access-columbus-flock-100343000.html",
    "dispatch_successes": "https://www.aol.com/news/columbus-police-tout-flock-successes-224636701.html",
    "dispatch_officer": "https://www.aol.com/articles/columbus-officer-searched-flock-ice-220021000.html",
    "dispatch_287g": "https://www.aol.com/articles/columbus-cuts-off-flock-access-202042000.html",
    "flock_compliance": "https://www.flocksafety.com/blog/ensuring-local-compliance",
    "flock_deletion": "https://www.flocksafety.com/blog/how-does-flock-handle-license-plate-data-deletion",
    "flock_lpr": "https://www.flocksafety.com/products/license-plate-readers",
    "hearing": "https://www.wosu.org/politics-government/2026-07-14/activists-renew-calls-for-stronger-policy-and-more-transparency-with-flock-cameras",
    "ord_0515": "https://columbus.legistar.com/LegislationDetail.aspx?FullText=1&GUID=50CE964D-110B-4B3D-8507-BE4835274DE8&ID=7923613",
}


def source(key: str, title: str, publisher: str, kind: str = "web") -> dict[str, object]:
    url = URLS[key]
    return {
        "kind": kind,
        "url": url,
        "uri": url,
        "name": title,
        "title": title,
        "publisher": publisher,
        "retrieved_at": GENERATED_AT,
    }


S = {
    "ord_0166": source("ord_0166", "Columbus Ordinance 0166-2023", "City of Columbus"),
    "ord_3173": source("ord_3173", "Columbus Ordinance 3173-2023", "City of Columbus"),
    "insight_ac": source("insight_ac", "3173-2023 expenditure attachment", "City of Columbus", "official-document"),
    "bid_3173": source("bid_3173", "3173-2023 bid waiver", "City of Columbus", "official-document"),
    "sts_3173": source("sts_3173", "Flock camera State Term Contract permission request", "City of Columbus", "official-document"),
    "ord_3181": source("ord_3181", "Columbus Ordinance 3181-2024", "City of Columbus"),
    "quote_3181": source("quote_3181", "Flock quote Q-90784", "Flock Safety / City of Columbus", "official-document"),
    "bid_3181": source("bid_3181", "3181-2024 bid waiver", "City of Columbus", "official-document"),
    "ord_1510": source("ord_1510", "Columbus Ordinance 1510-2025", "City of Columbus"),
    "attachment_1510": source("attachment_1510", "Attachment labeled 1510-2025 Flock Group SOS Details", "City of Columbus", "official-document"),
    "records_minutes": source("records_minutes", "Columbus Records Commission minutes, February 9, 2026", "City of Columbus"),
    "cpd_org": source("cpd_org", "CPD organizational structure", "City of Columbus"),
    "cpd_contact": source("cpd_contact", "CPD contact and unit directory", "City of Columbus"),
    "cpd_directives": source("cpd_directives", "CPD published directives index", "City of Columbus"),
    "cpd_records": source("cpd_records", "CPD Public Records Unit", "City of Columbus"),
    "wosu_jun25": source("wosu_jun25", "CPD limits nationwide Flock access", "WOSU Public Media", "news"),
    "wosu_jul11": source("wosu_jul11", "Ginther orders statewide Flock sharing stopped", "WOSU Public Media", "news"),
    "wosu_jul15": source("wosu_jul15", "CPD presents Flock audit findings", "WOSU Public Media", "news"),
    "wosu_remy": source("wosu_remy", "Remy discusses Flock contract and audit", "WOSU Public Media", "news"),
    "dispatch_audit": source("dispatch_audit", "Columbus Flock audit reporting", "The Columbus Dispatch via AOL", "news"),
    "dispatch_hsi": source("dispatch_hsi", "HSI access to Columbus Flock data", "The Columbus Dispatch via AOL", "news"),
    "dispatch_successes": source("dispatch_successes", "CPD defense of Flock and federal pilot analysis", "The Columbus Dispatch via AOL", "news"),
    "dispatch_officer": source("dispatch_officer", "CPD officer ICE-reason Flock searches", "The Columbus Dispatch via AOL", "news"),
    "dispatch_287g": source("dispatch_287g", "Columbus cuts off four additional 287(g) agencies", "The Columbus Dispatch via AOL", "news"),
    "flock_compliance": source("flock_compliance", "Flock statement on CBP and HSI pilots", "Flock Safety", "vendor-statement"),
    "flock_deletion": source("flock_deletion", "Flock data-deletion explanation", "Flock Safety", "vendor-statement"),
    "flock_lpr": source("flock_lpr", "Flock LPR product page", "Flock Safety", "vendor-statement"),
    "hearing": source("hearing", "Columbus Flock hearing and transparency demands", "WOSU Public Media", "news"),
    "ord_0515": source("ord_0515", "Columbus Ordinance 0515-2026", "City of Columbus"),
}


def ev(source_url: str, claim: str, confidence: float = 0.95, kind: str = "document") -> dict[str, object]:
    return {
        "kind": kind,
        "role": "supporting",
        "claim": claim,
        "source_url": source_url,
        "collected_at": GENERATED_AT,
        "confidence": confidence,
        "status": "reviewed",
    }


def doc(
    document_id: str,
    dtype: str,
    title: str,
    summary: str,
    data: dict[str, object],
    sources: list[dict[str, object]],
    evidence: list[dict[str, object]] | None = None,
    **extra: object,
) -> dict[str, object]:
    record: dict[str, object] = {
        "_id": document_id,
        "dataset": DATASET,
        "dtype": dtype,
        "schema_version": "0.9.0",
        "version": 1,
        "date_added": GENERATED_AT,
        "date_updated": GENERATED_AT,
        "title": title,
        "summary": summary,
        "sources": sources,
        "evidence": evidence or [],
        "data": data,
        "provenance": {
            "collector": "OpenAI GPT-5.6 Thinking",
            "collector_type": "research-agent",
            "method": "official-record and reputable-local-report review",
            "pipeline": "starintel-auto-dig",
            "run_id": DATASET,
        },
        "handling": {"visibility": "public", "pii": False, "sensitive": False},
    }
    record.update(extra)
    validate_document(record)
    return record


def build() -> list[dict[str, object]]:
    docs: list[dict[str, object]] = []

    orgs = [
        ("city-columbus", "City of Columbus", "municipal-government", "Columbus, Ohio", [S["ord_3173"], S["ord_3181"], S["ord_1510"]]),
        ("public-safety", "Columbus Department of Public Safety", "municipal-department", "Columbus, Ohio", [S["ord_3181"], S["ord_1510"]]),
        ("cpd", "Columbus Division of Police", "police-department", "Columbus, Ohio", [S["cpd_org"], S["ord_3181"], S["wosu_jul15"]]),
        ("flock", "Flock Safety", "public-safety-technology-company", "United States", [S["flock_lpr"], S["quote_3181"]]),
        ("insight", "Insight Public Sector", "technology-reseller", "United States", [S["ord_3173"], S["bid_3173"]]),
        ("forcemetrics", "ForceMetrics", "public-safety-data-platform-company", "United States", [S["ord_1510"]]),
        ("ocjs", "Ohio Office of Criminal Justice Services", "state-grant-agency", "Ohio", [S["ord_0166"], S["ord_3181"]]),
        ("hsi", "Homeland Security Investigations", "federal-law-enforcement-agency", "United States", [S["dispatch_hsi"], S["flock_compliance"]]),
        ("cbp", "U.S. Customs and Border Protection", "federal-law-enforcement-agency", "United States", [S["dispatch_successes"], S["flock_compliance"]]),
        ("records-commission", "Columbus Records Commission", "municipal-records-governance-body", "Columbus, Ohio", [S["records_minutes"]]),
        ("cpd-support-services", "CPD Support Services Subdivision", "police-subdivision", "Columbus, Ohio", [S["cpd_org"], S["cpd_contact"]]),
        ("cpd-technical-services", "CPD Technical Services Section", "police-technical-section", "Columbus, Ohio", [S["cpd_contact"]]),
        ("soundthinking", "SoundThinking", "public-safety-technology-company", "United States", [S["ord_3173"], S["ord_3181"]]),
    ]
    for slug, name, org_type, jurisdiction, sources in orgs:
        docs.append(doc(
            f"starintel:org:cpd-flock-next:{slug}",
            "org",
            name,
            f"{name} as a node in the Columbus Flock procurement, implementation, data-sharing, audit, or oversight chain.",
            {
                "etype": org_type,
                "name": name,
                "org_type": org_type,
                "jurisdiction": jurisdiction,
                "country": "United States",
                "government_levels": ["municipal"] if "Columbus" in jurisdiction else [],
            },
            sources,
            assessment={"confidence": 0.97},
            verification={"status": "source-verified", "verified": True},
        ))

    persons = [
        ("tim-myers", "Tim Myers", ["Deputy Chief", "Commander of CPD Support Services Subdivision"], ["Columbus Division of Police"], [S["cpd_org"], S["wosu_jul15"]], "Operational lead publicly presenting the audit and negotiating sharing restrictions."),
        ("elaine-bryant", "Elaine Bryant", ["Chief of Police"], ["Columbus Division of Police"], [S["wosu_jul15"], S["wosu_jun25"]], "Command authority associated with withdrawal from nationwide sharing."),
        ("justin-coleman", "Justin Coleman", ["Deputy Chief", "Commander of CPD Criminal Investigations Subdivision"], ["Columbus Division of Police"], [S["cpd_org"], S["dispatch_successes"]], "Criminal-investigations command node connected to CPD's operational use arguments."),
        ("lieutenant-williams", "Lieutenant Williams", ["Official city representative for ARPA 2022 grant"], ["Columbus Division of Police"], [S["ord_0166"]], "Named grant representative; first name is not promoted without a reviewed official record."),
        ("r-metheney", "R. Metheney", ["Division of Police procurement contact"], ["Columbus Division of Police"], [S["sts_3173"]], "Named contact on the 2023 State Term Contract permission request; initials preserved exactly."),
        ("ryan-elswick", "Ryan Elswick", ["Flock Safety main sales contact for quote Q-90784"], ["Flock Safety"], [S["quote_3181"]], "Named vendor contact for the direct 2024 Flock proposal."),
        ("clinton-foster", "Clinton Foster", ["Police records officer"], ["Columbus Division of Police"], [S["records_minutes"]], "Explained and defended the 30-day Flock retention schedule before the Records Commission."),
        ("andrew-ginther", "Andrew Ginther", ["Mayor of Columbus"], ["City of Columbus"], [S["wosu_jul11"]], "Ordered statewide Flock data sharing stopped after the audit release."),
        ("emmanuel-remy", "Emmanuel V. Remy", ["Columbus City Council member", "Public Safety and Criminal Justice Committee chair"], ["City of Columbus"], [S["wosu_remy"], S["hearing"]], "Requested the audit and controls the key council oversight hearing."),
        ("melanie-crabill", "Melanie Crabill", ["Records Commission chair", "Mayor's Office representative"], ["City of Columbus"], [S["records_minutes"]], "Chaired the meeting approving the merged CPD retention schedule."),
        ("angie-blevins", "Angie Blevins", ["Citizens Representative, Columbus Records Commission"], ["Columbus Records Commission"], [S["records_minutes"]], "Questioned why Flock data was kept 30 days while other LPR data was listed at 30 months."),
    ]
    for slug, name, positions, employers, sources, summary in persons:
        parts = name.split()
        data = {
            "etype": "person",
            "name": name,
            "full_name": name,
            "positions": positions,
            "employers": employers,
            "public_roles": positions,
        }
        if len(parts) >= 2 and not name.startswith("R.") and not name.startswith("Lieutenant"):
            data["fname"] = parts[0]
            data["lname"] = parts[-1]
        docs.append(doc(
            f"starintel:person:cpd-flock-next:{slug}",
            "person",
            name,
            summary,
            data,
            sources,
            assessment={"confidence": 0.96},
            verification={"status": "source-verified", "verified": True},
        ))

    docs.extend([
        doc(
            "starintel:grant:cpd-flock-next:arpa-2022",
            "grant",
            "American Rescue Plan 2022 public-safety grant",
            "Columbus accepted $628,835.22 for 32 fixed and eight quick-deploy LPRs plus analyst staffing tied to ShotSpotter data use.",
            {
                "contract_id": "0166-2023",
                "grantor_id": "starintel:org:cpd-flock-next:ocjs",
                "recipient_ids": ["starintel:org:cpd-flock-next:city-columbus", "starintel:org:cpd-flock-next:cpd"],
                "agency_ids": ["starintel:org:cpd-flock-next:cpd"],
                "description": "American Rescue Plan 2022 award covering LPR equipment and analyst positions.",
                "scope": "32 fixed LPRs, eight quick-deploy LPRs, two criminal intelligence analysts, and one crime analyst supporting ShotSpotter-related work.",
                "award_type": "subgrant",
                "status": "accepted",
                "start_at": "2022-04-01T00:00:00-04:00",
                "end_at": "2024-03-31T23:59:59-04:00",
                "ceiling_amount": 628835.22,
                "obligated_amount": 628835.22,
                "currency": "USD",
                "program": "American Rescue Plan 2022",
                "matching_required": False,
                "place_of_performance": "Columbus, Ohio",
            },
            [S["ord_0166"], S["ord_3173"]],
            [ev(URLS["ord_0166"], "Ordinance 0166-2023 identifies the $628,835.22 award and Lieutenant Williams as official representative.")],
            assessment={"confidence": 0.99},
            verification={"status": "official-record", "verified": True},
        ),
        doc(
            "starintel:grant:cpd-flock-next:fy24-lpr",
            "grant",
            "FY24 Columbus LPR Project Grant",
            "The $228,000 grant-funded direct Flock expansion was required to meet a December 2024 grant deadline.",
            {
                "contract_id": "FY24-Columbus-LPR-Project",
                "grantor_id": "starintel:org:cpd-flock-next:ocjs",
                "recipient_ids": ["starintel:org:cpd-flock-next:cpd"],
                "agency_ids": ["starintel:org:cpd-flock-next:cpd"],
                "description": "Office of Criminal Justice Services funding used for the 38-camera Flock lease.",
                "scope": "Lease and installation of 38 fixed Flock Falcon LPRs.",
                "award_type": "state criminal-justice grant",
                "status": "expended-by-ordinance",
                "ceiling_amount": 228000.0,
                "obligated_amount": 228000.0,
                "currency": "USD",
                "program": "FY24 Columbus LPR Project",
                "matching_required": False,
                "place_of_performance": "Columbus, Ohio",
            },
            [S["ord_3181"], S["bid_3181"]],
            [ev(URLS["ord_3181"], "Ordinance 3181-2024 authorizes $228,000 from the FY24 Columbus LPR Project Grant.")],
            assessment={"confidence": 0.98},
            verification={"status": "official-record", "verified": True},
        ),
        doc(
            "starintel:procurement:cpd-flock-next:3173-2023",
            "procurement",
            "Columbus LPR procurement 3173-2023",
            "Two-year $275,200.01 Insight Public Sector procurement for 32 fixed and eight quick-deploy LPRs using an unbid state-term schedule and a city bid waiver.",
            {
                "contract_id": "3173-2023",
                "vehicle_id": "Ohio State Term Schedule 534242",
                "buyer_id": "starintel:org:cpd-flock-next:city-columbus",
                "seller_id": "starintel:org:cpd-flock-next:insight",
                "agency_ids": ["starintel:org:cpd-flock-next:public-safety", "starintel:org:cpd-flock-next:cpd"],
                "vendor_ids": ["starintel:org:cpd-flock-next:insight", "starintel:org:cpd-flock-next:flock"],
                "description": "Lease and installation of 40 LPR units.",
                "scope": "32 fixed and eight quick-deploy LPRs installed in ShotSpotter areas.",
                "award_type": "state-term-schedule purchase",
                "competition_type": "bid waiver; state schedule not competitively bid",
                "status": "approved",
                "signed_at": "2023-11-21T00:00:00-05:00",
                "ceiling_amount": 275200.01,
                "obligated_amount": 275200.01,
                "currency": "USD",
                "place_of_performance": "Columbus, Ohio",
                "modifications": [
                    {"component": "equipment lease", "amount": 204800.0},
                    {"component": "professional services", "amount": 70400.01},
                ],
            },
            [S["ord_3173"], S["insight_ac"], S["bid_3173"], S["sts_3173"]],
            [
                ev(URLS["ord_3173"], "The ordinance authorizes a two-year, $275,200.01 contract for 32 fixed and eight quick-deploy readers."),
                ev(URLS["sts_3173"], "The state-term request names R. Metheney and says three or more quotations should accompany new requests when the contract was not bid."),
            ],
            assessment={"confidence": 0.99},
            verification={"status": "official-record", "verified": True},
        ),
        doc(
            "starintel:contract:cpd-flock-next:3181-2024",
            "contract",
            "Columbus direct Flock contract 3181-2024",
            "Two-year $228,000 direct Flock lease for 38 fixed Falcon LPRs, with 30-day retention and unlimited users.",
            {
                "contract_id": "3181-2024",
                "buyer_id": "starintel:org:cpd-flock-next:city-columbus",
                "seller_id": "starintel:org:cpd-flock-next:flock",
                "agency_ids": ["starintel:org:cpd-flock-next:public-safety", "starintel:org:cpd-flock-next:cpd"],
                "vendor_ids": ["starintel:org:cpd-flock-next:flock"],
                "description": "Direct lease and installation of 38 fixed Flock Falcon LPRs.",
                "scope": "38 fixed Falcon cameras in existing ShotSpotter areas; Vehicle Fingerprint search and real-time alerts; unlimited users.",
                "award_type": "direct vendor contract",
                "competition_type": "city bid waiver",
                "status": "active-or-expiring",
                "signed_at": "2024-12-10T00:00:00-05:00",
                "ceiling_amount": 228000.0,
                "obligated_amount": 228000.0,
                "currency": "USD",
                "place_of_performance": "Columbus, Ohio",
                "modifications": [
                    {"quote": "Q-90784", "created": "2024-10-23", "year_one": 114000.0, "annual_recurring": 114000.0, "retention_days": 30, "camera_count": 38}
                ],
            },
            [S["ord_3181"], S["quote_3181"], S["bid_3181"]],
            [
                ev(URLS["quote_3181"], "Quote Q-90784 lists 38 Falcon cameras, 30-day retention, unlimited users, $114,000 annually, and $228,000 total."),
                ev(URLS["bid_3181"], "The bid waiver cites a delayed procurement and December 2024 grant deadline."),
            ],
            assessment={"confidence": 0.99},
            verification={"status": "official-record", "verified": True},
        ),
        doc(
            "starintel:contract:cpd-flock-next:1510-2025-forcemetrics",
            "contract",
            "Columbus ForceMetrics trial amendment 1510-2025",
            "Free one-year non-renewable ForceMetrics trial for up to 500 users, integrated with CAD, RMS, and other city systems.",
            {
                "contract_id": "1510-2025",
                "buyer_id": "starintel:org:cpd-flock-next:city-columbus",
                "seller_id": "starintel:org:cpd-flock-next:flock",
                "agency_ids": ["starintel:org:cpd-flock-next:public-safety", "starintel:org:cpd-flock-next:cpd"],
                "vendor_ids": ["starintel:org:cpd-flock-next:flock", "starintel:org:cpd-flock-next:forcemetrics"],
                "description": "Amendment adding the ForceMetrics Informed Responder Platform to the Flock agreement.",
                "scope": "Up to 500 users; CAD/RMS and city-system integration; implementation, onboarding, training, support, updates, customer-success management, SAML SSO, and optional regional sharing.",
                "award_type": "free vendor trial",
                "competition_type": "amendment to existing agreement",
                "status": "trial-period-ended-status-unresolved",
                "signed_at": "2025-06-26T00:00:00-04:00",
                "start_at": "2025-06-27T00:00:00-04:00",
                "end_at": "2026-06-27T00:00:00-04:00",
                "ceiling_amount": 0.0,
                "potential_amount": 857412.0,
                "currency": "USD",
                "place_of_performance": "Columbus, Ohio",
                "modifications": [
                    {"year_two_price": 209999.0},
                    {"year_three_price": 220499.0},
                    {"additional_100_user_block": 54000.0},
                    {"full_agency_deployment": 857412.0},
                ],
            },
            [S["ord_1510"], S["attachment_1510"]],
            [
                ev(URLS["ord_1510"], "The ordinance describes a free one-year trial for up to 500 users with city-system integrations."),
                ev(URLS["attachment_1510"], "The sole public attachment labeled SOS Details is an Ohio business-entity certificate rather than a scope of services."),
            ],
            assessment={"confidence": 0.99},
            verification={"status": "official-record-with-document-gap", "verified": True, "unresolved": ["Actual approved Scope of Services not found in the public packet.", "Post-trial disposition not found."]},
        ),
    ])

    relations = [
        ("cpd-operates-flock", "starintel:org:cpd-flock-next:cpd", "operates", "starintel:org:cpd-flock-next:flock", {"context": "Columbus Flock deployment"}, [S["ord_3181"]], 0.99),
        ("public-safety-contracts-flock", "starintel:org:cpd-flock-next:public-safety", "contracted-with", "starintel:org:cpd-flock-next:flock", {"ordinance": "3181-2024"}, [S["ord_3181"]], 0.99),
        ("insight-resells-flock", "starintel:org:cpd-flock-next:insight", "resold", "starintel:org:cpd-flock-next:flock", {"ordinance": "3173-2023"}, [S["ord_3173"]], 0.96),
        ("myers-commands-support", "starintel:person:cpd-flock-next:tim-myers", "commands", "starintel:org:cpd-flock-next:cpd-support-services", {}, [S["cpd_org"]], 0.99),
        ("support-contains-technical", "starintel:org:cpd-flock-next:cpd-support-services", "contains", "starintel:org:cpd-flock-next:cpd-technical-services", {}, [S["cpd_contact"]], 0.99),
        ("metheney-procurement-contact", "starintel:person:cpd-flock-next:r-metheney", "procurement-contact-for", "starintel:procurement:cpd-flock-next:3173-2023", {}, [S["sts_3173"]], 0.99),
        ("elswick-sales-contact", "starintel:person:cpd-flock-next:ryan-elswick", "sales-contact-for", "starintel:contract:cpd-flock-next:3181-2024", {"quote": "Q-90784"}, [S["quote_3181"]], 0.99),
        ("williams-grant-rep", "starintel:person:cpd-flock-next:lieutenant-williams", "official-representative-for", "starintel:grant:cpd-flock-next:arpa-2022", {}, [S["ord_0166"]], 0.99),
        ("foster-retention", "starintel:person:cpd-flock-next:clinton-foster", "administers-records-policy-for", "starintel:org:cpd-flock-next:cpd", {"retention_days": 30}, [S["records_minutes"]], 0.97),
        ("forcemetrics-integrates-cpd", "starintel:org:cpd-flock-next:forcemetrics", "integrated-with", "starintel:org:cpd-flock-next:cpd", {"systems": ["CAD", "RMS", "other city systems"], "maximum_users": 500}, [S["ord_1510"]], 0.99),
        ("lpr-colocated-shotspotter", "starintel:org:cpd-flock-next:cpd", "co-located-technology-with", "starintel:org:cpd-flock-next:soundthinking", {"technology": "Flock LPR", "geography": "ShotSpotter areas"}, [S["ord_3173"], S["ord_3181"]], 0.99),
        ("ginther-ordered-sharing-stop", "starintel:person:cpd-flock-next:andrew-ginther", "ordered-policy-change-at", "starintel:org:cpd-flock-next:cpd", {"change": "stop statewide Flock sharing", "date": "2026-07-10"}, [S["wosu_jul11"]], 0.99),
        ("remy-requested-audit", "starintel:person:cpd-flock-next:emmanuel-remy", "requested-audit-of", "starintel:org:cpd-flock-next:cpd", {"system": "Flock"}, [S["wosu_remy"]], 0.98),
        ("hsi-searched-network", "starintel:org:cpd-flock-next:hsi", "searched-data-including", "starintel:org:cpd-flock-next:cpd", {"approximate_searches": 200, "pilot_period": "March-August 2025"}, [S["dispatch_hsi"], S["flock_compliance"]], 0.94),
        ("cbp-searched-network", "starintel:org:cpd-flock-next:cbp", "searched-data-including", "starintel:org:cpd-flock-next:cpd", {"searches_more_than": 3500, "pilot_period": "March-August 2025"}, [S["dispatch_successes"], S["flock_compliance"]], 0.94),
    ]
    for slug, subject, predicate, obj, qualifiers, sources, confidence in relations:
        docs.append(doc(
            f"starintel:relation:cpd-flock-next:{slug}",
            "relation",
            f"{predicate}: {subject} → {obj}",
            f"Verified or bounded relation in the CPD/Flock implementation and access chain: {predicate}.",
            {
                "subject": subject,
                "predicate": predicate,
                "object": obj,
                "directed": True,
                "qualifiers": qualifiers,
                "confidence": confidence,
                "active": True,
            },
            sources,
            assessment={"confidence": confidence},
            verification={"status": "source-supported", "verified": True},
            related_ids=[subject, obj],
        ))

    docs.extend([
        doc(
            "starintel:policy:cpd-flock-next:retention-30-days",
            "policy",
            "CPD Flock LPR 30-day retention schedule",
            "The Records Commission approved a merged CPD schedule retaining Flock captured LPR data for 30 days, compared with 30 months for previously listed Axon and Vigilant LPR schedules.",
            {
                "policy_id": "CPD-RC2-24-3c",
                "name": "Flock LPR captured-data retention",
                "issuer_id": "starintel:org:cpd-flock-next:records-commission",
                "jurisdiction": "Columbus, Ohio",
                "policy_type": "records-retention",
                "text": "Flock LPR captured data: 30-day retention.",
                "effective_at": "2026-02-09T10:00:00-05:00",
                "status": "approved",
                "affected_ids": ["starintel:org:cpd-flock-next:cpd", "starintel:org:cpd-flock-next:flock"],
            },
            [S["records_minutes"], S["flock_deletion"]],
            [ev(URLS["records_minutes"], "Clinton Foster said captured Flock data did not require the 30-month retention applied to other LPR records.")],
            assessment={"confidence": 0.99},
            verification={"status": "official-record", "verified": True},
        ),
        doc(
            "starintel:policy:cpd-flock-next:national-sharing-disabled",
            "policy",
            "CPD nationwide Flock sharing disabled",
            "CPD disabled nationwide network sharing while retaining individually vetted and statewide relationships at that stage.",
            {
                "policy_id": "CPD-Flock-National-Sharing-2026",
                "name": "Nationwide Flock sharing disabled",
                "issuer_id": "starintel:org:cpd-flock-next:cpd",
                "jurisdiction": "Columbus, Ohio",
                "policy_type": "data-sharing-control",
                "text": "Disable nationwide network sharing; continue individually vetted relationships subject to policy.",
                "effective_at": "2026-06-03T00:00:00-04:00",
                "status": "implemented",
                "affected_ids": ["starintel:org:cpd-flock-next:cpd"],
            },
            [S["wosu_jun25"], S["wosu_jul15"]],
            assessment={"confidence": 0.96, "caveats": ["Public reporting gives slightly different descriptions of the exact effective date; obtain platform configuration logs."]},
            verification={"status": "reported-and-acknowledged", "verified": True},
        ),
        doc(
            "starintel:policy:cpd-flock-next:statewide-sharing-disabled",
            "policy",
            "Columbus statewide Flock sharing disabled",
            "Mayor Ginther ordered CPD to stop statewide Flock data sharing after the July 2026 audit.",
            {
                "policy_id": "Mayor-Order-Flock-Statewide-2026-07-10",
                "name": "Statewide Flock sharing suspension",
                "issuer_id": "starintel:person:cpd-flock-next:andrew-ginther",
                "jurisdiction": "Columbus, Ohio",
                "policy_type": "executive-data-sharing-order",
                "text": "Stop statewide data sharing from the Columbus Flock network.",
                "effective_at": "2026-07-10T00:00:00-04:00",
                "status": "implemented",
                "affected_ids": ["starintel:org:cpd-flock-next:cpd"],
            },
            [S["wosu_jul11"], S["dispatch_audit"]],
            assessment={"confidence": 0.99},
            verification={"status": "publicly-announced", "verified": True},
        ),
        doc(
            "starintel:policy:cpd-flock-next:287g-council-approval",
            "policy",
            "Columbus 287(g) agreement council-approval restriction",
            "Ordinance 0515-2026 would prohibit city employees or agencies from entering a 287(g) agreement without explicit council approval.",
            {
                "policy_id": "0515-2026",
                "name": "287(g) agreement approval restriction",
                "issuer_id": "starintel:org:cpd-flock-next:city-columbus",
                "jurisdiction": "Columbus, Ohio",
                "policy_type": "immigration-enforcement-governance",
                "text": "No city employee or agency may enter a 287(g) agreement without explicit Columbus City Council approval.",
                "status": "legislative-record",
                "affected_ids": ["starintel:org:cpd-flock-next:cpd"],
            },
            [S["ord_0515"]],
            assessment={"confidence": 0.98},
            verification={"status": "official-legislative-record", "verified": True},
        ),
    ])

    events = [
        (
            "federal-pilots",
            "Federal HSI and CBP Flock pilots included Columbus data",
            "data-access",
            "Dispatch analysis found nearly 200 HSI searches and more than 3,500 CBP searches that included Columbus among many networks during direct federal pilot access from March through August 2025.",
            ["starintel:org:cpd-flock-next:hsi", "starintel:org:cpd-flock-next:cbp", "starintel:org:cpd-flock-next:flock", "starintel:org:cpd-flock-next:cpd"],
            "2025-03-01T00:00:00-05:00",
            "2025-08-31T23:59:59-04:00",
            [S["dispatch_hsi"], S["dispatch_successes"], S["flock_compliance"]],
            ["Flock acknowledged limited CBP and HSI pilots and poor communication and permissions design."],
        ),
        (
            "officer-ice-searches",
            "Unnamed CPD user recorded six ICE-reason searches",
            "audit-finding",
            "An unnamed CPD officer made six searches within ten minutes on February 3, 2025, using ICE as the stated reason while looking for a silver or gray GMC pickup; three searches covered one network and three covered 287 networks.",
            ["starintel:org:cpd-flock-next:cpd"],
            "2025-02-03T09:00:00-05:00",
            "2025-02-03T09:10:00-05:00",
            [S["dispatch_officer"]],
            ["The user made more than 5,000 Flock inquiries overall; only 12 of nearly 1,400 users made more.", "CPD stated further inquiry was pending."],
        ),
        (
            "audit-release",
            "CPD Flock audit released",
            "audit",
            "CPD released an audit covering nearly 19.6 million searches since November 2023 and flagged 15,577 possible immigration-related searches, including 20 originating within CPD.",
            ["starintel:org:cpd-flock-next:cpd", "starintel:person:cpd-flock-next:tim-myers"],
            "2026-07-10T00:00:00-04:00",
            None,
            [S["dispatch_audit"], S["wosu_jul15"]],
            ["The audit used broad terms and CPD disputed that every flagged search reflected immigration enforcement.", "The executive summary was one page; underlying raw logs are necessary for independent replication."],
        ),
        (
            "four-287g-cutoff",
            "CPD removed four additional 287(g)-linked agencies",
            "access-control-correction",
            "After press inquiries, CPD removed four agencies with current ICE 287(g) agreements that were still receiving Columbus data, including Spartanburg County, South Carolina.",
            ["starintel:org:cpd-flock-next:cpd"],
            "2026-07-17T00:00:00-04:00",
            None,
            [S["dispatch_287g"]],
            ["Three agencies had recently entered 287(g) agreements; Spartanburg County's agreement dated to April 2025.", "The correction demonstrates a manual-vetting lag."],
        ),
        (
            "hearing-aug10",
            "Columbus City Council Flock public hearing",
            "public-hearing",
            "Special hearing scheduled for August 10, 2026 at 4 p.m. at City Hall to examine the audit, safeguards, contract, and policy.",
            ["starintel:person:cpd-flock-next:emmanuel-remy", "starintel:org:cpd-flock-next:cpd", "starintel:org:cpd-flock-next:flock"],
            "2026-08-10T16:00:00-04:00",
            None,
            [S["hearing"], S["wosu_remy"], S["wosu_jul15"]],
            ["Flock representatives were invited to answer questions."],
        ),
    ]
    for slug, name, kind, description, participants, start, end, sources, actions in events:
        data = {
            "event_kind": kind,
            "name": name,
            "description": description,
            "participant_ids": participants,
            "start_at": start,
            "status": "scheduled" if slug == "hearing-aug10" else "occurred",
            "actions": actions,
            "jurisdiction": "Columbus, Ohio",
        }
        if end:
            data["end_at"] = end
        docs.append(doc(
            f"starintel:event:cpd-flock-next:{slug}",
            "event",
            name,
            description,
            data,
            sources,
            assessment={"confidence": 0.94 if slug == "federal-pilots" else 0.97},
            verification={"status": "multi-source" if len(sources) > 1 else "reported", "verified": True},
            related_ids=participants,
        ))

    docs.extend([
        doc(
            "starintel:claim:cpd-flock-next:no-central-policy-before-late-2025",
            "claim",
            "CPD lacked a centralized Flock policy during early deployment",
            "Local reporting states CPD did not establish a centralized Flock policy until after December 2025; the published CPD directives index still does not expose a dedicated ALPR/Flock directive.",
            {
                "claim": "CPD operated Flock access for a substantial period without a centralized published Flock-specific policy.",
                "claimant_id": "starintel:org:cpd-flock-next:cpd",
                "subject_ids": ["starintel:org:cpd-flock-next:cpd"],
                "predicate": "lacked-centralized-policy",
                "object": {"period": "November 2023 through at least late 2025"},
                "claim_type": "governance-gap",
                "polarity": "positive",
                "certainty": 0.88,
                "status": "supported-with-record-gap",
                "adjudication": "Obtain all historical directives, SOPs, training materials, and effective dates before treating the absence of a public directive as proof of no internal guidance.",
            },
            [S["wosu_jun25"], S["cpd_directives"], S["dispatch_successes"]],
            assessment={"confidence": 0.88, "caveats": ["A non-public internal SOP may have existed."]},
            verification={"status": "partially-verified", "verified": False, "unresolved": ["Historical internal policy inventory."]},
        ),
        doc(
            "starintel:analysis:cpd-flock-next:procurement-anomalies",
            "analysis",
            "CPD Flock procurement anomaly analysis",
            "The official packets show quote-count, award-rationale, and repeated-price anomalies that require native-file and email review.",
            {
                "question": "Did Columbus's 2023 and 2024 Flock-related bid-waiver process preserve the required competitive and cost-effectiveness documentation?",
                "method": "Compare ordinances, bid-waiver forms, state-term request, quotes, and expenditure attachments.",
                "framework": "document-completeness and cross-packet consistency",
                "scope": "Ordinances 3173-2023 and 3181-2024",
                "input_ids": ["starintel:procurement:cpd-flock-next:3173-2023", "starintel:contract:cpd-flock-next:3181-2024"],
                "findings": [
                    "The 2023 state-term request says new unbid requests should attach three or more quotations, but the public packet exposes only one $212,800 Insight cameras-only quote.",
                    "Both the 2023 and 2024 bid-waiver forms repeat the identical $212,800 Insight cameras-only amount.",
                    "Both forms leave the field explaining why the lowest bid was not accepted blank and use generic approval language.",
                    "The 2024 direct Flock award is $228,000 for 38 cameras; the public packet does not establish whether the repeated Insight figure was a fresh 2024 quote.",
                ],
                "conclusions": [
                    "The public record is insufficient to reconstruct a full competitive evaluation.",
                    "The repeated amount is an anomaly, not proof of wrongdoing.",
                ],
                "recommendations": [
                    "Obtain native quote files and metadata.",
                    "Obtain procurement routing, approval emails, cost-comparison worksheets, and all vendor quotes.",
                ],
                "counterarguments": [
                    "Supporting quotes or approvals may exist outside the Legistar packet.",
                    "The same price may have remained valid under a reseller schedule.",
                ],
                "limitations": ["No native file metadata or procurement email chain was available."],
                "unresolved": ["Whether the 2024 $212,800 comparison was newly issued or copied forward.", "Who approved exceptions to the three-quote instruction."],
                "confidence": 0.96,
            },
            [S["bid_3173"], S["sts_3173"], S["bid_3181"], S["quote_3181"]],
            assessment={"confidence": 0.96},
            verification={"status": "document-comparison", "verified": True},
        ),
        doc(
            "starintel:analysis:cpd-flock-next:forcemetrics-gap",
            "analysis",
            "ForceMetrics integration and public-document gap",
            "The legislation describes a major cross-system data platform, but its only public attachment is a corporate registration certificate rather than the claimed scope of services.",
            {
                "question": "What data, users, controls, and post-trial obligations governed Columbus's ForceMetrics deployment?",
                "method": "Compare ordinance narrative to the attached public document and trial timeline.",
                "framework": "system-integration and contract-document completeness",
                "scope": "Ordinance 1510-2025 and the one-year trial",
                "input_ids": ["starintel:contract:cpd-flock-next:1510-2025-forcemetrics"],
                "findings": [
                    "The platform could serve up to 500 users and integrate CAD, RMS, and other city systems.",
                    "The ordinance promises an approved Scope of Services, SSO, onboarding, support, and a dedicated customer-success manager.",
                    "The only public attachment labeled SOS Details is an Ohio Secretary of State business-entity certificate.",
                    "The trial should have ended around June 2026, but no public disposition was located in this pass.",
                ],
                "conclusions": [
                    "The public packet does not expose the technical or security contract needed to evaluate data flows.",
                    "The current operational status and data-deletion outcome remain unresolved.",
                ],
                "recommendations": [
                    "Obtain the executed Scope of Services, data-flow diagrams, integration inventory, SSO configuration, user and administrator roster, trial evaluation, renewal proposals, invoices, and deletion/return certification.",
                ],
                "counterarguments": ["The Scope of Services may be maintained in procurement or contract-management systems rather than Legistar."],
                "limitations": ["No internal contract repository or security review was available."],
                "unresolved": ["Whether ForceMetrics remains active.", "What data sources were ingested.", "Who had access.", "Whether trial data was deleted or retained."],
                "confidence": 0.99,
            },
            [S["ord_1510"], S["attachment_1510"]],
            assessment={"confidence": 0.99},
            verification={"status": "official-packet-comparison", "verified": True},
        ),
        doc(
            "starintel:analysis:cpd-flock-next:sharing-control-failure",
            "analysis",
            "Flock sharing-control failure analysis",
            "CPD's restrictions reduced broad access but depended on manually maintained agency lists and failed to promptly exclude four active 287(g) partners.",
            {
                "question": "Did CPD's sharing controls reliably enforce Columbus's stated immigration-use restrictions?",
                "method": "Timeline reconstruction from CPD statements, audit reporting, vendor admissions, and post-audit access corrections.",
                "framework": "access-control effectiveness",
                "scope": "December 2025 through July 2026",
                "input_ids": [
                    "starintel:policy:cpd-flock-next:national-sharing-disabled",
                    "starintel:policy:cpd-flock-next:statewide-sharing-disabled",
                    "starintel:event:cpd-flock-next:four-287g-cutoff",
                ],
                "findings": [
                    "CPD enabled immigration and reproductive-care filters in December 2025.",
                    "CPD requested a 287(g) opt-out in April 2026 and later withdrew from national and statewide sharing.",
                    "Four current 287(g)-linked agencies still had access until press inquiries prompted removal.",
                    "Flock acknowledged that its federal pilots lacked distinct permissions and protocols for local compliance.",
                ],
                "conclusions": [
                    "Text-reason filters and manually curated sharing lists did not provide a self-updating policy boundary.",
                    "The key remaining control question is whether direct one-to-one partners and downstream queries are continuously reconciled against changing agency status.",
                ],
                "recommendations": [
                    "Require machine-enforced deny lists, immutable policy versions, periodic recertification, and public audit exports.",
                    "Reconcile all one-to-one partners against current 287(g), federal task-force, and prohibited-purpose lists.",
                ],
                "counterarguments": ["Not every search by HSI, CBP, or a 287(g) agency is necessarily civil immigration enforcement."],
                "limitations": ["The full sharing roster and query-level case context were not public."],
                "unresolved": ["Complete one-to-one sharing roster.", "Automated versus manual update mechanism.", "All agencies removed and re-added over time."],
                "confidence": 0.95,
            },
            [S["wosu_jun25"], S["wosu_jul15"], S["dispatch_287g"], S["flock_compliance"]],
            assessment={"confidence": 0.95},
            verification={"status": "multi-source-analysis", "verified": True},
        ),
    ])

    targets = [
        ("raw-audit", "Obtain and independently reproduce the CPD Flock audit", ["Raw audit-log exports", "query dictionaries", "deduplication rules", "network scope", "user and agency identifiers", "case outcomes"], 1.0),
        ("officer-inquiry", "Resolve the unnamed CPD officer ICE-search inquiry", ["Officer identity and assignment", "case number", "supervisor approval", "search history", "disciplinary findings", "policy in force", "final disposition"], 1.0),
        ("sharing-roster", "Reconstruct every CPD Flock sharing relationship", ["National, statewide, and one-to-one partners", "activation and removal timestamps", "approving administrators", "287(g) status", "federal task-force links", "private-camera access"], 1.0),
        ("forcemetrics-sos", "Recover the executed ForceMetrics Scope of Services and security package", ["Executed SOS", "DPA", "CJIS and SOC 2 materials", "data-flow diagrams", "CAD/RMS integrations", "SSO configuration", "customer-success records"], 1.0),
        ("forcemetrics-disposition", "Determine the ForceMetrics trial disposition", ["Current service status", "renewal or direct agreement", "invoices", "evaluation report", "data return/deletion certificate", "remaining accounts"], 1.0),
        ("admin-roster", "Identify CPD Flock and ForceMetrics administrators and power users", ["Organization administrators", "sharing administrators", "auditors", "user-provisioning staff", "top search users", "role history"], 0.98),
        ("procurement-native-files", "Recover native procurement files and metadata", ["All Insight and Flock quotes", "email transmittals", "file metadata", "approval routing", "evaluation worksheets", "grant-deadline communications"], 0.98),
        ("camera-inventory", "Map the complete CPD-owned and accessible camera inventory", ["38 direct Flock units", "32 prior fixed units", "eight quick-deploy units", "installation dates", "site coordinates", "permits", "ownership", "private and regional cameras"], 0.98),
        ("shotspotter-colocation", "Analyze Flock and ShotSpotter co-location and combined investigative workflow", ["Deployment maps", "alert-to-search workflow", "analyst assignments", "case linkage", "neighborhood concentration", "renewal metrics"], 0.96),
        ("retention-deletion", "Verify actual deletion and evidentiary preservation behavior", ["Configured retention value", "AWS lifecycle evidence", "exports to case systems", "legal holds", "audit logs", "deletion certificates", "Axon/Vigilant comparison"], 0.97),
        ("policy-history", "Recover every CPD Flock policy and effective version", ["Directives", "SOPs", "training", "acceptable-use rules", "reason-code rules", "hotlist verification", "immigration and reproductive-care filters", "revision history"], 1.0),
        ("vendor-support", "Map Flock personnel and support interventions affecting Columbus controls", ["Sales", "implementation engineers", "customer-success manager", "support tickets", "feature requests", "287(g) opt-out discussions", "sharing configuration changes"], 0.97),
    ]
    seed_ids = [
        "starintel:org:cpd-flock-next:cpd",
        "starintel:org:cpd-flock-next:flock",
        "starintel:person:cpd-flock-next:tim-myers",
    ]
    for slug, target, scope, priority in targets:
        docs.append(doc(
            f"starintel:investigation-target:cpd-flock-next:{slug}",
            "investigation-target",
            target,
            f"Recursive CPD/Flock target: {target}.",
            {
                "target": target,
                "target_id": f"cpd-flock-next:{slug}",
                "target_type": "records-and-network-investigation",
                "query": f"Columbus CPD Flock {target}",
                "research_question": f"What primary records fully establish: {target}?",
                "hypotheses": [
                    "The public record omits operationally significant configuration and personnel details.",
                    "Native records will clarify dates, approvals, and actual technical controls.",
                ],
                "objectives": scope,
                "in_scope": scope,
                "out_of_scope": ["Private personal data unrelated to official duties", "Unverified attribution presented as fact"],
                "scope_type": "municipal-police-technology",
                "seed_ids": seed_ids,
                "required_dtypes": ["person", "org", "relation", "contract", "policy", "event", "claim", "analysis"],
                "preferred_sources": ["City contracts", "CPD audit logs", "Flock configuration exports", "public records", "official communications"],
                "depth": 2,
                "max_depth": 5,
                "breadth": 25,
                "priority": priority,
                "score": priority,
                "status": "queued",
            },
            [S["ord_3181"], S["wosu_jul15"], S["dispatch_audit"]],
            assessment={"priority": priority, "confidence": 0.98},
            verification={"status": "research-target", "verified": True},
            workflow={"research_status": "queued", "priority": priority, "recursion_depth": 2, "max_depth": 5, "root_target_id": "starintel:investigation-target:cpd-flock-next:root", "next_action": target},
            related_ids=seed_ids,
        ))

    root_target_ids = [d["_id"] for d in docs if d["dtype"] == "investigation-target"]
    docs.append(doc(
        "starintel:investigation-target:cpd-flock-next:root",
        "investigation-target",
        "Map the full CPD–Flock implementation, data, and accountability system",
        "Root target for a records-first reconstruction of procurement, personnel, architecture, sharing, policy, audits, use, and termination paths.",
        {
            "target": "Columbus Division of Police and Flock Safety implementation",
            "target_id": "cpd-flock-next:root",
            "target_type": "municipal-surveillance-system",
            "query": "CPD Flock procurement implementation audit access sharing ForceMetrics",
            "research_question": "Who controls the system, what data flows through it, who can query it, and what records prove the controls actually work?",
            "hypotheses": [
                "The operational system is broader than the 38-camera direct contract because it includes prior equipment, regional/private cameras, and ForceMetrics integrations.",
                "Public legislative packets omit key technical agreements and administrator identities.",
            ],
            "objectives": [
                "Resolve procurement and grant chains.",
                "Map operational and administrative personnel.",
                "Reconstruct all data-sharing relationships.",
                "Verify policy and retention enforcement.",
                "Resolve audit findings and ForceMetrics status.",
            ],
            "in_scope": ["CPD", "Public Safety", "Flock", "ForceMetrics", "Insight", "OCJS", "regional and federal sharing partners"],
            "scope_type": "municipal-police-technology",
            "seed_ids": ["starintel:org:cpd-flock-next:cpd", "starintel:org:cpd-flock-next:flock"],
            "required_dtypes": ["person", "org", "relation", "grant", "procurement", "contract", "policy", "event", "claim", "analysis"],
            "preferred_sources": ["Official city records", "audit logs", "vendor configuration exports", "contracts", "emails", "local investigative reporting"],
            "depth": 0,
            "max_depth": 6,
            "breadth": 50,
            "priority": 1.0,
            "score": 1.0,
            "status": "active",
        },
        [S["ord_3173"], S["ord_3181"], S["ord_1510"], S["wosu_jul15"]],
        assessment={"priority": 1.0, "confidence": 0.99},
        verification={"status": "research-root", "verified": True},
        workflow={"research_status": "active", "priority": 1.0, "recursion_depth": 0, "max_depth": 6, "next_action": "Execute queued records targets."},
        related_ids=root_target_ids,
    ))

    findings = [
        {"finding": "Columbus used two purchasing paths: a 2023 Insight state-term procurement and a 2024 direct Flock award.", "support": ["starintel:procurement:cpd-flock-next:3173-2023", "starintel:contract:cpd-flock-next:3181-2024"]},
        {"finding": "Both bid-waiver forms repeat the same $212,800 Insight cameras-only figure.", "support": ["starintel:analysis:cpd-flock-next:procurement-anomalies"]},
        {"finding": "ForceMetrics created a potential 500-user cross-system data layer whose actual Scope of Services is absent from the public packet.", "support": ["starintel:analysis:cpd-flock-next:forcemetrics-gap"]},
        {"finding": "The 2026 audit identified 15,577 possible immigration-related searches in nearly 19.6 million searches.", "support": ["starintel:event:cpd-flock-next:audit-release"]},
        {"finding": "Federal HSI and CBP pilots directly queried networks including Columbus in 2025.", "support": ["starintel:event:cpd-flock-next:federal-pilots"]},
        {"finding": "Manual vetting failed to promptly exclude four current 287(g)-linked agencies.", "support": ["starintel:event:cpd-flock-next:four-287g-cutoff", "starintel:analysis:cpd-flock-next:sharing-control-failure"]},
    ]
    docs.append(doc(
        "starintel:research-pass:cpd-flock-next:2026-07-26",
        "research-pass",
        "CPD and Flock next-level research pass",
        "Official-record and local-reporting pass resolving procurement, grant, ForceMetrics, audit, sharing, policy, and personnel layers and emitting recursive records targets.",
        {
            "research_question": "What deeper procurement, architecture, personnel, policy, and access-control facts define Columbus's Flock deployment?",
            "method": "Cross-compare official ordinances and attachments, city organizational and records material, vendor statements, and reputable local reporting.",
            "classification_rules": [
                "Official records outrank narrative summaries.",
                "Document anomalies are targets, not misconduct findings.",
                "Unnamed officers remain unnamed.",
                "Vendor statements are identified as vendor statements.",
                "Absence from a public packet is not proof that an internal record does not exist.",
            ],
            "finding_ids": [item for f in findings for item in f["support"]],
            "findings": findings,
            "supporting_record_ids": [d["_id"] for d in docs if d["dtype"] in {"grant", "procurement", "contract", "policy", "event", "analysis"}],
            "counterevidence_ids": [],
            "unresolved_target_ids": root_target_ids,
            "source_ids": [],
            "agent_identity": "OpenAI GPT-5.6 Thinking",
            "narrative_role": "evidence-first investigator",
            "started_at": GENERATED_AT,
            "completed_at": GENERATED_AT,
            "iteration": 2,
        },
        list(S.values()),
        assessment={"confidence": 0.97, "completeness": 0.72, "gaps": ["Raw CPD logs", "internal contracts and policies", "administrator roster", "ForceMetrics disposition"]},
        verification={"status": "schema-validated-research-pass", "verified": True},
        workflow={"research_status": "completed", "priority": 1.0, "recursion_depth": 1, "max_depth": 6, "completed_at": GENERATED_AT},
        related_ids=root_target_ids,
    ))

    return docs


def validate_packet(docs: list[dict[str, object]]) -> None:
    ids = [str(d["_id"]) for d in docs]
    if len(ids) != len(set(ids)):
        raise RuntimeError("duplicate document ids")
    idset = set(ids)
    for record in docs:
        validate_document(record)
        for related in record.get("related_ids", []):
            if related.startswith("starintel:") and related not in idset:
                raise RuntimeError(f"unresolved related_id {related} in {record['_id']}")
        if record["dtype"] == "relation":
            for endpoint in (record["data"]["subject"], record["data"]["object"]):
                if isinstance(endpoint, str) and endpoint.startswith("starintel:") and endpoint not in idset:
                    raise RuntimeError(f"unresolved relation endpoint {endpoint} in {record['_id']}")


def write_packet(docs: list[dict[str, object]]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    jsonl = "".join(json.dumps(d, sort_keys=True, separators=(",", ":")) + "\n" for d in docs)
    (OUTPUT_DIR / "starintel-documents.jsonl").write_text(jsonl, encoding="utf-8")

    counts = Counter(str(d["dtype"]) for d in docs)
    digest = hashlib.sha256(jsonl.encode("utf-8")).hexdigest()
    manifest = {
        "dataset": DATASET,
        "generated_at": GENERATED_AT,
        "schema_version": "0.9.0",
        "total": len(docs),
        "counts": dict(sorted(counts.items())),
        "files": ["README.md", "sources.md", "starintel-documents.jsonl"],
        "hash_algorithm": "sha256",
        "starintel_documents_sha256": digest,
        "validation": {
            "starintel_doc_validate_document": "passed",
            "unique_ids": "passed",
            "relation_endpoints": "passed",
            "related_id_references": "passed",
        },
    }
    (OUTPUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    readme = f"""# Flock Safety: Columbus CPD next-level pass

Generated: `{GENERATED_AT}`

This packet reconstructs the Columbus Division of Police Flock system beyond the public camera count. It covers:

- the 2022 grant and 2023 Insight reseller procurement;
- the 2024 direct Flock award and bid-waiver anomalies;
- Flock/ShotSpotter geographic co-deployment;
- the ForceMetrics 500-user CAD/RMS integration trial and missing public Scope of Services;
- CPD command, procurement, vendor, records, and council personnel;
- federal HSI/CBP pilots and CPD audit findings;
- national, statewide, one-to-one, and 287(g)-linked sharing controls;
- records retention and policy gaps;
- recursive targets for raw logs, administrators, contracts, camera maps, support tickets, and trial disposition.

## Counts

"""
    for dtype, count in sorted(counts.items()):
        readme += f"- {dtype}: {count}\n"
    readme += f"- total: **{len(docs)}**\n\n"
    readme += """## Evidence boundaries

- The repeated $212,800 Insight amount is a document anomaly, not a finding of misconduct.
- `R. Metheney` and `Lieutenant Williams` are preserved as exposed in reviewed official records; missing first names are not guessed.
- The CPD officer associated with the ICE-reason searches remains unnamed.
- HSI/CBP search totals describe searches that included Columbus among potentially many networks; they are not treated as proof that each query returned or used a Columbus record.
- The absence of a dedicated public directive or Scope of Services does not prove no internal document exists.
- Vendor statements are labeled as vendor statements.

## Validation

Every record is validated with the repository-local `starintel_doc` v0.9.0 runtime. The packet also checks unique IDs, relation endpoints, and related-document references.
"""
    (OUTPUT_DIR / "README.md").write_text(readme, encoding="utf-8")

    source_lines = ["# Sources", "", f"Retrieved and reviewed for `{DATASET}`.", ""]
    seen: set[str] = set()
    for key, record in S.items():
        url = str(record["url"])
        if url in seen:
            continue
        seen.add(url)
        source_lines.append(f"- [{record['title']}]({url}) — {record['publisher']}")
    (OUTPUT_DIR / "sources.md").write_text("\n".join(source_lines) + "\n", encoding="utf-8")


def main() -> None:
    docs = build()
    validate_packet(docs)
    write_packet(docs)
    print(json.dumps({"dataset": DATASET, "documents": len(docs), "output": str(OUTPUT_DIR)}, indent=2))


if __name__ == "__main__":
    main()
