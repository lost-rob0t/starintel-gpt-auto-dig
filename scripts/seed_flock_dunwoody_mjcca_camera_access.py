#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from starintel_doc.model import Document
from starintel_doc.store import compact
from starintel_doc.validation import validate_document

DATASET = "flock-dunwoody-mjcca-2026-08-17"
RUN_ID = "flock-dunwoody-mjcca-camera-access-2026-08-17"
GENERATED_AT = "2026-08-17T20:53:00Z"
OUTPUT = ROOT / "digs/flock/2026-08-17-dunwoody-mjcca-camera-access"
PACKET = OUTPUT / "starintel-documents.jsonl"

FLOCK = "starintel:org:flock-safety"
DUNWOODY = "starintel:org:city-of-dunwoody-georgia"
DPD = "starintel:org:dunwoody-police-department"
MJCCA = "starintel:org:marcus-jewish-community-center-of-atlanta"
CARTER = "starintel:person:bob-carter-flock"
GLUCK = "starintel:person:randy-gluck-flock"
HUNYAR = "starintel:person:jason-hunyar-dunwoody"
GYM_CAMERA = "starintel:asset:mjcca-gymnastics-camera"
POOL_CAMERA = "starintel:asset:mjcca-main-pool-right-camera"

CARTER_EVENT = "starintel:event:flock-carter-mjcca-gymnastics-live-view-2025-09-30"
GLUCK_EVENT = "starintel:event:flock-gluck-mjcca-camera-live-views-2025-07-23"

CLAIM_ACCESS = "starintel:claim:carter-accessed-mjcca-gymnastics-camera-2025-09-30"
CLAIM_SINGLE = "starintel:claim:carter-single-camera-view-2025-09-30"
CLAIM_DEMO = "starintel:claim:flock-characterizes-carter-access-as-authorized-demo"
CLAIM_SCOPE = "starintel:claim:mjcca-camera-sharing-critical-incident-scope"
CLAIM_POLICY = "starintel:claim:flock-changed-sensitive-demo-location-policy"
CLAIM_AGREEMENT_GAP = "starintel:claim:demo-partner-documentation-not-produced-report"

ANALYSIS = "starintel:analysis:flock-dunwoody-mjcca-access-initial-assessment"
ROOT_TARGET = "starintel:investigation-target:flock-dunwoody-mjcca-access"
TARGET_LOGS = "starintel:investigation-target:dunwoody-flock-raw-audit-logs"
TARGET_AUTH = "starintel:investigation-target:dunwoody-flock-demo-authorization-chain"
TARGET_MJCCA = "starintel:investigation-target:mjcca-dunwoody-camera-sharing-terms"
TARGET_AUDIT = "starintel:investigation-target:flock-live-view-audit-semantics"
RESEARCH_PASS = "starintel:research-pass:flock-dunwoody-mjcca-initial-2026-08-17"

SOURCES: dict[str, dict[str, Any]] = {
    "deflock-x": {
        "id": "starintel:source:deflock-x-2079202670380814382",
        "title": "DeFlock post highlighting the Dunwoody gymnastics-camera access",
        "url": "https://x.com/therealdeflock/status/2079202670380814382",
        "kind": "social_media_post",
        "publisher": "X",
        "author": "DeFlock (@therealDeFlock)",
        "summary": "Viral post alleging that a Flock vice president viewed the children's-gymnastics camera and no other camera in Dunwoody's roughly 400-camera network that day.",
    },
    "hunyar": {
        "id": "starintel:source:hunyar-why-are-flock-employees-watching-our-children-2026",
        "title": "Why Are Flock Employees Watching Our Children?",
        "url": "https://jasonhunyar.substack.com/p/why-are-flock-employees-watching-720",
        "kind": "open_records_analysis",
        "publisher": "Substack",
        "author": "Jason Hunyar",
        "published_at": "2026-04-08T00:00:00Z",
        "summary": "Resident analysis of Dunwoody Flock event-log export D048397-031926 and related public-records material, including Carter and Gluck live-view entries.",
    },
    "flock": {
        "id": "starintel:source:flock-testing-development-program-dunwoody-2026",
        "title": "Understanding Flock's Testing and Development Program",
        "url": "https://www.flocksafety.com/blog/understanding-flocks-testing-and-development-program",
        "kind": "company_statement",
        "publisher": "Flock Safety",
        "author": "Flock Safety",
        "summary": "Flock statement acknowledging a Dunwoody demo involving a camera at a local Jewish Community Center, asserting city authorization, and announcing more-public-location demo training.",
    },
    "404": {
        "id": "starintel:source:404media-dunwoody-flock-demo-camera-access-2026",
        "title": "City Learns Flock Accessed Cameras in Children's Gymnastics Room as a Sales Pitch Demo, Renews Contract Anyway",
        "url": "https://www.404media.co/city-learns-flock-accessed-cameras-in-childrens-gymnastics-room-as-a-sales-pitch-demo-renews-contract-anyway/",
        "kind": "news_report",
        "publisher": "404 Media",
        "author": "Jason Koebler",
        "published_at": "2026-04-30T13:25:00Z",
        "summary": "Independent reporting that Flock confirmed employee access as part of sales demonstrations and that accessed Dunwoody feeds included sensitive MJCCA cameras.",
    },
    "acpc": {
        "id": "starintel:source:acpc-dunwoody-flock-contract-camera-access-2026-04-14",
        "title": "Dunwoody approves Flock contract after delays over security and privacy concerns",
        "url": "https://atlpresscollective.com/2026/04/14/dunwoody-flock-safety-contract-passed/",
        "kind": "news_report",
        "publisher": "Atlanta Community Press Collective",
        "author": "Matt Scott",
        "published_at": "2026-04-14T00:00:00Z",
        "summary": "Local reporting identifying Bob Carter and Randy Gluck, the MJCCA camera labels and dates, and the mayor's statement that the access involved a potential sales call.",
    },
    "ledger": {
        "id": "starintel:source:dunwoody-brookhaven-ledger-flock-gymnastics-camera-2026",
        "title": "Dunwoody resident questions Flock camera oversight after vendor executive viewed children's gymnastics feed",
        "url": "https://dunwoodybrookhavenledger.com/articles/dunwoody-resident-questions-flock-camera-oversight-after-vendor-executive-viewed-children-s-gymnastics-feed-mrtdt8v2",
        "kind": "local_news_report",
        "publisher": "Dunwoody-Brookhaven Ledger",
        "summary": "Local report describing the Sept. 30 Carter access, the July 23 Gluck access, the stated critical-incident condition for MJCCA sharing, and the dispute over demo authorization.",
    },
    "muckrock-camera-partnership": {
        "id": "starintel:source:muckrock-dunwoody-camera-partnership-request-d038447-061624",
        "title": "GORA Request: Flock Safety Partnership",
        "url": "https://www.muckrock.com/foi/dunwoody-5142/gora-request-flock-safety-partnership-165189/",
        "kind": "public_records_request",
        "publisher": "MuckRock",
        "author": "e",
        "published_at": "2024-06-16T00:00:00Z",
        "summary": "Public-records request for agreements used to register or integrate privately owned cameras. Dunwoody reported no responsive city-held template and later said partnership agreements were with Flock.",
    },
    "muckrock-contracts": {
        "id": "starintel:source:muckrock-dunwoody-flock-contracts-d045363-090725",
        "title": "Open Records Request: Flock",
        "url": "https://www.muckrock.com/foi/dunwoody-5142/open-records-request-flock-192582/",
        "kind": "public_records_request",
        "publisher": "MuckRock",
        "author": "e",
        "published_at": "2025-09-05T00:00:00Z",
        "summary": "Completed Dunwoody request for Flock agreements active from 2023 through Sept. 5, 2025; the response page exposes ten contract-related files.",
    },
}

def source_ref(key: str) -> dict[str, Any]:
    source = SOURCES[key]
    out = {
        "source_id": source["id"],
        "kind": source["kind"],
        "title": source["title"],
        "publisher": source["publisher"],
        "url": source["url"],
        "retrieved_at": GENERATED_AT,
        "access_method": "public_web",
    }
    if source.get("author"):
        out["author"] = source["author"]
    if source.get("published_at"):
        out["published_at"] = source["published_at"]
    return out

def evidence(key: str, claim: str, *, confidence: float, role: str = "supporting") -> dict[str, Any]:
    source = SOURCES[key]
    suffix = source["id"].split(":")[-1]
    digest = hashlib.sha256(claim.encode("utf-8")).hexdigest()[:12]
    return {
        "evidence_id": f"starintel:evidence:{suffix}:{digest}",
        "source_id": source["id"],
        "source_url": source["url"],
        "kind": source["kind"],
        "role": role,
        "claim": claim,
        "collected_at": GENERATED_AT,
        "confidence": confidence,
        "status": "collected",
    }

def make(
    dtype: str,
    doc_id: str,
    title: str,
    summary: str,
    data: dict[str, Any],
    *,
    source_keys: tuple[str, ...] = (),
    evidence_items: list[dict[str, Any]] | None = None,
    tags: tuple[str, ...] = (),
    related_ids: tuple[str, ...] = (),
    assessment: dict[str, Any] | None = None,
    verification: dict[str, Any] | None = None,
    temporal: dict[str, Any] | None = None,
    workflow: dict[str, Any] | None = None,
    notes: list[str] | None = None,
) -> dict[str, Any]:
    value = Document.create(
        dtype,
        DATASET,
        doc_id=doc_id,
        title=title,
        summary=summary,
        data=data,
        tags=list(tags),
        sources=[source_ref(key) for key in source_keys],
        evidence=evidence_items or [],
        related_ids=list(related_ids),
        assessment=assessment or {},
        verification=verification or {
            "status": "source-triangulated",
            "verified": bool(source_keys),
            "verified_by": ["auto-dig-source-triangulation"],
            "verified_at": GENERATED_AT if source_keys else None,
            "methods": ["public-source comparison"] if source_keys else [],
            "last_reviewed_at": GENERATED_AT,
        },
        temporal=temporal or {},
        provenance={
            "collector": "ChatGPT",
            "collector_type": "llm-assisted-open-source-research",
            "agent": "GPT-5.6 Sol",
            "skill": "auto-dig",
            "run_id": RUN_ID,
            "method": "public-source triangulation and claim separation",
            "pipeline": "starintel-gpt-auto-dig",
            "created_by": "auto-dig",
        },
        handling={"visibility": "public", "sensitive": False, "pii": False},
        quality={
            "validation_status": "schema-valid",
            "last_validated_at": GENERATED_AT,
            "validator": "starintel_doc.validate_document",
        },
        workflow=workflow or {"research_status": "initial-pass", "run_id": RUN_ID},
        notes=notes or [],
    ).to_dict()
    value["date_added"] = GENERATED_AT
    value["date_updated"] = GENERATED_AT
    validate_document(value)
    return value

def source_document(key: str) -> dict[str, Any]:
    source = SOURCES[key]
    data = {
        "source_id": source["id"],
        "kind": source["kind"],
        "title": source["title"],
        "publisher": source["publisher"],
        "url": source["url"],
        "retrieved_at": GENERATED_AT,
        "access_method": "public_web",
    }
    if source.get("author"):
        data["author"] = source["author"]
    if source.get("published_at"):
        data["published_at"] = source["published_at"]
    return make(
        "source",
        source["id"],
        source["title"],
        source["summary"],
        data,
        source_keys=(key,),
        tags=("flock-safety", "dunwoody", "source"),
    )

def relation(
    doc_id: str,
    title: str,
    subject: str,
    predicate: str,
    object_id: str,
    *,
    source_keys: tuple[str, ...],
    note: str = "",
    qualifiers: dict[str, Any] | None = None,
    confidence: float = 0.9,
) -> dict[str, Any]:
    return make(
        "relation",
        doc_id,
        title,
        note,
        {
            "subject": subject,
            "predicate": predicate,
            "object": object_id,
            "directed": True,
            "qualifiers": qualifiers or {},
            "confidence": confidence,
            "note": note,
        },
        source_keys=source_keys,
        evidence_items=[
            evidence(key, f"{subject} {predicate} {object_id}", confidence=confidence)
            for key in source_keys
        ],
        tags=("flock-safety", "dunwoody", "graph-edge"),
        related_ids=(subject, object_id),
    )

def target(
    doc_id: str,
    title: str,
    target_value: str,
    question: str,
    objectives: list[str],
    *,
    seed_ids: list[str],
    priority: float,
    next_action: str,
) -> dict[str, Any]:
    return make(
        "investigation-target",
        doc_id,
        title,
        question,
        {
            "target": target_value,
            "target_id": doc_id,
            "target_type": "documentary-verification",
            "research_question": question,
            "hypotheses": [],
            "objectives": objectives,
            "in_scope": ["public records", "contracts", "audit logs", "public statements", "role and permission records"],
            "out_of_scope": ["private personal data", "speculation about sexual motive", "harassment or identification of minors"],
            "scope_type": "bounded-open-source-investigation",
            "seed_ids": seed_ids,
            "source_ids": [source["id"] for source in SOURCES.values()],
            "required_dtypes": ["source", "claim", "event", "relation", "analysis"],
            "preferred_sources": ["official records", "raw audit exports", "contracts", "first-party statements", "independent local reporting"],
            "excluded_sources": ["unsourced reposts as sole evidence"],
            "recurring": False,
            "depth": 1,
            "max_depth": 2,
            "breadth": 8,
            "priority": priority,
            "status": "open",
            "selection_reason": ["Unresolved evidence gap identified in initial AutoDig pass"],
        },
        source_keys=("hunyar", "flock", "404", "acpc", "ledger"),
        tags=("flock-safety", "dunwoody", "research-target"),
        related_ids=tuple(seed_ids),
        workflow={
            "research_status": "queued",
            "priority": priority,
            "next_action": next_action,
            "run_id": RUN_ID,
            "root_target_id": ROOT_TARGET,
            "recursion_depth": 1 if doc_id != ROOT_TARGET else 0,
            "max_depth": 2,
        },
    )

def build_documents() -> list[dict[str, Any]]:
    docs: list[dict[str, Any]] = [source_document(key) for key in SOURCES]

    docs.extend([
        make(
            "org", FLOCK, "Flock Safety",
            "Atlanta-based public-safety technology vendor whose platform is used by Dunwoody.",
            {"name": "Flock Safety", "org_type": "company", "website": "https://www.flocksafety.com/"},
            source_keys=("flock", "404", "acpc"), tags=("flock-safety",),
        ),
        make(
            "org", DUNWOODY, "City of Dunwoody, Georgia",
            "Municipal government of Dunwoody, Georgia.",
            {"name": "City of Dunwoody, Georgia", "org_type": "municipal_government", "jurisdiction": "Dunwoody, Georgia, United States"},
            source_keys=("acpc", "muckrock-contracts"), tags=("dunwoody", "government"),
        ),
        make(
            "org", DPD, "Dunwoody Police Department",
            "Police department operating the Dunwoody Flock environment discussed in the access records.",
            {"name": "Dunwoody Police Department", "org_type": "law_enforcement_agency", "jurisdiction": "Dunwoody, Georgia, United States", "parent_id": DUNWOODY},
            source_keys=("acpc", "muckrock-camera-partnership", "muckrock-contracts"), tags=("dunwoody", "law-enforcement"),
            related_ids=(DUNWOODY, FLOCK),
        ),
        make(
            "org", MJCCA, "Marcus Jewish Community Center of Atlanta",
            "Private community center whose camera feeds were integrated with the Dunwoody police/Flock environment.",
            {"name": "Marcus Jewish Community Center of Atlanta", "short_name": "MJCCA", "org_type": "private_community_center"},
            source_keys=("404", "acpc", "ledger"), tags=("mjcca", "private-camera-network"),
            related_ids=(DPD,),
        ),
        make(
            "person", CARTER, "Bob Carter",
            "Flock executive identified by public reporting and open-records analysis as a user of Dunwoody's Flock environment.",
            {"full_name": "Bob Carter", "employers": [FLOCK], "positions": ["Vice President, Strategic Relations & Business Development"]},
            source_keys=("hunyar", "acpc", "404"), tags=("flock-safety", "person"),
            related_ids=(FLOCK,),
        ),
        make(
            "person", GLUCK, "Randy Gluck",
            "Flock business-development manager identified in public records analysis as having accessed MJCCA camera feeds on July 23, 2025.",
            {"full_name": "Randy Gluck", "employers": [FLOCK], "positions": ["Business Development Manager, 911/Emergency"]},
            source_keys=("hunyar", "acpc", "ledger"), tags=("flock-safety", "person"),
            related_ids=(FLOCK,),
        ),
        make(
            "person", HUNYAR, "Jason Hunyar",
            "Dunwoody resident who obtained and analyzed Flock event logs through Georgia public-records requests.",
            {"full_name": "Jason Hunyar"},
            source_keys=("hunyar", "acpc"), tags=("dunwoody", "researcher"),
        ),
        make(
            "asset", GYM_CAMERA, "MJCCA camera labeled Gymnastics",
            "Camera/feed identified in Dunwoody Flock records and reporting by the label 'Gymnastics'. Public sources place it in an MJCCA gymnastics area.",
            {"name": "Gymnastics", "asset_type": "surveillance_camera_feed", "owner_ids": [MJCCA], "status": "historically_observed"},
            source_keys=("hunyar", "acpc", "404", "ledger"), tags=("camera", "mjcca", "gymnastics"),
            related_ids=(MJCCA, DPD),
        ),
        make(
            "asset", POOL_CAMERA, "MJCCA camera labeled Main Pool Right",
            "MJCCA camera/feed identified in July 23, 2025 live-view records.",
            {"name": "Main Pool Right", "asset_type": "surveillance_camera_feed", "owner_ids": [MJCCA], "status": "historically_observed"},
            source_keys=("hunyar", "acpc", "ledger"), tags=("camera", "mjcca", "pool"),
            related_ids=(MJCCA, DPD),
        ),
        make(
            "social-media-post",
            "starintel:social-media-post:deflock-2079202670380814382",
            "DeFlock post on Carter's Dunwoody camera access",
            "Post that triggered this AutoDig pass and framed the Sept. 30 access as a Flock vice president viewing the children's-gymnastics camera and no other camera that day.",
            {
                "content": "DeFlock highlighted the Sept. 30, 2025 Dunwoody access and alleged that the gymnastics camera was Carter's only camera view that day.",
                "platform": "X",
                "user": "@therealDeFlock",
                "message_id": "2079202670380814382",
                "url": SOURCES["deflock-x"]["url"],
                "links": [],
                "visibility": "public",
            },
            source_keys=("deflock-x",), tags=("flock-safety", "viral-claim"),
            related_ids=(CARTER, GYM_CAMERA, CLAIM_SINGLE),
        ),
        make(
            "observation",
            "starintel:observation:hunyar-carter-live-view-log-2025-09-30",
            "Hunyar-reported Carter live-view log entry",
            "Structured capture of Hunyar's published interpretation of event-log request D048397-031926. The raw export was not independently parsed in this pass.",
            {
                "observer_id": HUNYAR,
                "subject_id": CARTER,
                "observation_type": "reported_flock_event_log_entry",
                "value": {
                    "request_id": "D048397-031926",
                    "camera_label": "Gymnastics",
                    "timestamp_as_published": "2025-09-30 13:20:36 EST",
                    "same_day_camera_views_reported": 1,
                    "next_activity_as_published": "2025-10-07 19:40:22 EST - Skate Park #014",
                },
                "method": "analysis of public-records export as published by Jason Hunyar",
                "instrument": "Flock event-log export event-logs_010125_031926",
                "observed_at": "2025-09-30T13:20:36-04:00",
            },
            source_keys=("hunyar",),
            evidence_items=[evidence("hunyar", "Published log analysis reports one Carter live-view entry on Sept. 30 labeled Gymnastics.", confidence=0.93)],
            tags=("audit-log", "observation", "flock-safety"),
            related_ids=(CARTER, GYM_CAMERA),
            assessment={"confidence": 0.9, "gaps": ["Underlying full export was not independently parsed in this pass."]},
            notes=["Hunyar says he converted displayed log times to EST. This record preserves his published timestamp string; observed_at uses Dunwoody civil time offset for Sept. 30."],
        ),
        make(
            "event", CARTER_EVENT, "Bob Carter live-view access to MJCCA Gymnastics camera",
            "On Sept. 30, 2025 a Flock account attributed to Bob Carter initiated a live view of the MJCCA camera labeled Gymnastics. Public evidence does not establish viewing duration or what was visible at that instant.",
            {
                "event_kind": "live_camera_access",
                "name": "Carter MJCCA Gymnastics live view",
                "description": "A live-view action was recorded for Bob Carter against the MJCCA camera labeled Gymnastics.",
                "participant_ids": [CARTER],
                "participants": ["Bob Carter"],
                "start_at": "2025-09-30T13:20:36-04:00",
                "status": "documented",
                "outcome": "Live view initiated; duration and content actually visible are not established by the public sources reviewed.",
                "jurisdiction": "Dunwoody, Georgia, United States",
            },
            source_keys=("hunyar", "acpc", "404", "ledger", "flock"),
            evidence_items=[
                evidence("hunyar", "Open-records analysis identifies Carter's Sept. 30 live-view entry labeled Gymnastics.", confidence=0.93),
                evidence("acpc", "Local reporting independently identifies Carter, the Sept. 30 date, and the Gymnastics camera label.", confidence=0.95),
                evidence("flock", "Flock acknowledges a Dunwoody demo involving a camera at a local Jewish Community Center.", confidence=0.98),
            ],
            tags=("flock-safety", "dunwoody", "mjcca", "camera-access"),
            related_ids=(CARTER, GYM_CAMERA, DPD, FLOCK, MJCCA),
            assessment={"confidence": 0.97, "gaps": ["Viewing duration is not exposed by the published log analysis.", "Whether children were present or visible is not established."]},
            verification={"status": "corroborated", "verified": True, "verified_by": ["Hunyar open-records analysis", "ACPC", "404 Media", "Flock Safety statement"], "verified_at": GENERATED_AT, "methods": ["multi-source triangulation"], "last_reviewed_at": GENERATED_AT},
        ),
        make(
            "event", GLUCK_EVENT, "Randy Gluck live views of MJCCA cameras",
            "On July 23, 2025 Flock business-development manager Randy Gluck is reported to have accessed multiple private MJCCA camera feeds, including a gym camera and Main Pool Right.",
            {
                "event_kind": "live_camera_access_sequence",
                "name": "Gluck MJCCA live-view sequence",
                "description": "Published event-log analysis reports a sequence ending at the MJCCA camera labeled Main Pool Right.",
                "participant_ids": [GLUCK],
                "participants": ["Randy Gluck"],
                "start_at": "2025-07-23T11:46:44-04:00",
                "status": "reported",
                "jurisdiction": "Dunwoody, Georgia, United States",
            },
            source_keys=("hunyar", "acpc", "ledger"),
            evidence_items=[
                evidence("hunyar", "Published log analysis reports Gluck accessing private MJCCA cameras on July 23, including Main Pool Right.", confidence=0.92),
                evidence("acpc", "Local reporting corroborates Gluck's July 23 MJCCA access and camera labels.", confidence=0.94),
            ],
            tags=("flock-safety", "dunwoody", "mjcca", "camera-access"),
            related_ids=(GLUCK, POOL_CAMERA, MJCCA, DPD),
            assessment={"confidence": 0.92, "gaps": ["Underlying full event-log export was not independently parsed in this pass."]},
        ),
    ])

    docs.extend([
        make(
            "claim", CLAIM_ACCESS, "Claim: Carter accessed the MJCCA Gymnastics camera",
            "The access event itself is strongly corroborated across the open-records analysis, local reporting, independent reporting, and Flock's own response.",
            {
                "claim": "Bob Carter accessed the MJCCA camera labeled Gymnastics through Dunwoody's Flock environment on Sept. 30, 2025.",
                "subject_ids": [CARTER, GYM_CAMERA, DPD],
                "predicate": "accessed_live_view",
                "object": {"event_id": CARTER_EVENT, "date": "2025-09-30"},
                "claim_type": "factual_event",
                "polarity": "affirmative",
                "certainty": 0.98,
                "supporting_evidence_ids": [],
                "contradicting_evidence_ids": [],
                "status": "corroborated",
                "adjudication": "supported",
            },
            source_keys=("hunyar", "acpc", "404", "ledger", "flock"),
            evidence_items=[
                evidence("hunyar", "Carter is shown in the published log analysis accessing Gymnastics on Sept. 30.", confidence=0.93),
                evidence("acpc", "ACPC identifies Carter and the Gymnastics camera access.", confidence=0.95),
                evidence("flock", "Flock acknowledges the sensitive-location Dunwoody demo access.", confidence=0.98),
            ],
            tags=("claim", "confirmed-core"),
            related_ids=(CARTER_EVENT, CARTER, GYM_CAMERA),
            assessment={"confidence": 0.98},
        ),
        make(
            "claim", CLAIM_SINGLE, "Claim: Gymnastics was Carter's only camera view that day",
            "Hunyar's event-log analysis reports one Carter camera view on Sept. 30 and no further Carter activity for 7.3 days. This pass did not independently parse the raw export.",
            {
                "claim": "The Gymnastics live view was Bob Carter's only camera view in the Dunwoody Flock environment on Sept. 30, 2025.",
                "subject_ids": [CARTER, DPD],
                "predicate": "same_day_camera_view_count",
                "object": 1,
                "claim_type": "audit_log_interpretation",
                "polarity": "affirmative",
                "certainty": 0.9,
                "supporting_evidence_ids": [],
                "contradicting_evidence_ids": [],
                "status": "supported-not-independently-reproduced",
                "adjudication": "provisionally-supported",
            },
            source_keys=("hunyar", "ledger", "deflock-x"),
            evidence_items=[
                evidence("hunyar", "Hunyar's published event-log sequence states one singular Carter viewing that day.", confidence=0.93),
                evidence("ledger", "Local reporting repeats the sole-view characterization.", confidence=0.82),
                evidence("deflock-x", "The viral post repeats the sole-view characterization.", confidence=0.6),
            ],
            tags=("claim", "audit-log"),
            related_ids=(CARTER_EVENT, CLAIM_ACCESS),
            assessment={"confidence": 0.9, "uncertainty": 0.1, "gaps": ["Raw event-log export not independently parsed in this pass."]},
            verification={"status": "supported-not-independently-reproduced", "verified": False, "verified_by": ["published open-records analysis", "secondary local report"], "verified_at": None, "methods": ["source triangulation"], "unresolved": ["Reproduce count from original event-log export."], "last_reviewed_at": GENERATED_AT},
        ),
        make(
            "claim", CLAIM_DEMO, "Claim: Flock characterizes the access as an authorized demo",
            "This record captures Flock's explanation as an attributed claim, not as an independently established authorization fact.",
            {
                "claim": "Flock states that the Dunwoody MJCCA camera access occurred during a routine demo authorized under the city's demo-partner arrangement.",
                "claimant_id": FLOCK,
                "subject_ids": [FLOCK, DPD, CARTER_EVENT],
                "predicate": "characterizes_access_as",
                "object": "authorized routine demonstration",
                "claim_type": "attributed_company_statement",
                "polarity": "affirmative",
                "certainty": 1.0,
                "supporting_evidence_ids": [],
                "contradicting_evidence_ids": [],
                "status": "confirmed-as-statement",
                "adjudication": "underlying-authorization-unresolved",
            },
            source_keys=("flock", "404", "acpc"),
            evidence_items=[
                evidence("flock", "Flock publicly states the Dunwoody demo was authorized under a demo partner agreement.", confidence=1.0),
                evidence("404", "404 Media reports the same company explanation and quotes a Flock spokesperson describing demo-partner authorization.", confidence=0.95),
            ],
            tags=("claim", "attributed", "authorization"),
            related_ids=(FLOCK, DPD, CARTER_EVENT, TARGET_AUTH),
            assessment={"confidence": 1.0, "gaps": ["The underlying authorization instrument was not produced and reviewed in this pass."]},
        ),
        make(
            "claim", CLAIM_SCOPE, "Claim: MJCCA camera sharing was described as critical-incident-only",
            "A local report says MJCCA shared its cameras with Dunwoody Police under a stated condition limiting access to real-time critical-incident response.",
            {
                "claim": "The Dunwoody-Brookhaven Ledger reports that MJCCA's camera sharing with Dunwoody Police was subject to a stated condition of real-time critical-incident response.",
                "subject_ids": [MJCCA, DPD],
                "predicate": "reported_camera_sharing_scope",
                "object": "real-time critical incident response",
                "claim_type": "reported_contractual_or_operational_condition",
                "polarity": "affirmative",
                "certainty": 0.84,
                "supporting_evidence_ids": [],
                "contradicting_evidence_ids": [],
                "status": "reported",
                "adjudication": "primary-document-needed",
            },
            source_keys=("ledger",),
            evidence_items=[evidence("ledger", "Ledger reports the stated critical-incident limitation for MJCCA sharing.", confidence=0.84)],
            tags=("claim", "mjcca", "scope"),
            related_ids=(MJCCA, DPD, TARGET_MJCCA),
            assessment={"confidence": 0.84, "gaps": ["Obtain the primary MJCCA-Flock/Dunwoody agreement or onboarding record."]},
            verification={"status": "reported-primary-document-needed", "verified": False, "verified_by": ["Dunwoody-Brookhaven Ledger"], "verified_at": None, "methods": ["secondary-source review"], "unresolved": ["Obtain primary sharing terms."], "last_reviewed_at": GENERATED_AT},
        ),
        make(
            "claim", CLAIM_POLICY, "Claim: Flock changed demo-location policy after Dunwoody controversy",
            "Flock says employees will be trained to conduct demonstrations only at more public locations, such as retail parking lots.",
            {
                "claim": "Flock announced a policy/training change directing employees to conduct demos in more public locations after concerns about the Dunwoody MJCCA demo.",
                "claimant_id": FLOCK,
                "subject_ids": [FLOCK],
                "predicate": "announced_demo_location_policy_change",
                "object": "more public demo locations",
                "claim_type": "company_policy_statement",
                "polarity": "affirmative",
                "certainty": 1.0,
                "supporting_evidence_ids": [],
                "contradicting_evidence_ids": [],
                "status": "confirmed-as-statement",
                "adjudication": "statement-confirmed-implementation-not-audited",
            },
            source_keys=("flock", "404", "acpc"),
            evidence_items=[evidence("flock", "Flock announced new training to avoid sensitive demo locations.", confidence=1.0)],
            tags=("claim", "policy-change"),
            related_ids=(FLOCK, CARTER_EVENT),
        ),
        make(
            "claim", CLAIM_AGREEMENT_GAP, "Claim: documentary support for the demo authorization remains unresolved",
            "Published reporting and Hunyar's records work state that the city had not produced documentation substantiating the demo-partner authorization. This packet does not infer that no authorization existed.",
            {
                "claim": "Public reporting states that documentary support for Flock's claimed Dunwoody demo-partner authorization had not been produced to the researcher at the time of reporting.",
                "subject_ids": [FLOCK, DPD, DUNWOODY],
                "predicate": "authorization_documentation_status",
                "object": "not produced in the public-records trail reviewed",
                "claim_type": "records_production_status",
                "polarity": "affirmative",
                "certainty": 0.78,
                "supporting_evidence_ids": [],
                "contradicting_evidence_ids": [],
                "status": "reported-contested-context",
                "adjudication": "unresolved",
            },
            source_keys=("ledger", "hunyar", "muckrock-camera-partnership", "muckrock-contracts"),
            evidence_items=[
                evidence("ledger", "Ledger reports that the city had been unable to produce documentation of the claimed demo agreement.", confidence=0.78),
                evidence("muckrock-camera-partnership", "An earlier Dunwoody request found no city-held template for private-camera integration agreements and said such agreements were with Flock.", confidence=0.9),
                evidence("muckrock-contracts", "A completed 2025 request produced Flock contract-related files, creating a bounded contract corpus for follow-up review.", confidence=0.9),
            ],
            tags=("claim", "authorization", "records-gap"),
            related_ids=(TARGET_AUTH, FLOCK, DPD, DUNWOODY),
            assessment={"confidence": 0.78, "alternatives": ["Authorization may exist in another document, account configuration, oral approval, or Flock-held agreement not surfaced in the city records reviewed."], "gaps": ["Obtain and authenticate the exact demo-partner authorization instrument effective Sept. 30, 2025."]},
            verification={"status": "unresolved", "verified": False, "verified_by": ["public reporting and records-request pages"], "verified_at": None, "methods": ["records-trail comparison"], "conflicts": ["Flock states explicit authorization existed."], "unresolved": ["Identity, terms, signatory, date, and scope of any demo-partner agreement."], "last_reviewed_at": GENERATED_AT},
        ),
    ])

    docs.extend([
        relation("starintel:relation:bob-carter-employed-by-flock", "Bob Carter employed by Flock Safety", CARTER, "employed_by", FLOCK, source_keys=("hunyar", "acpc"), note="Public reporting identifies Carter as a Flock vice president.", confidence=0.97),
        relation("starintel:relation:randy-gluck-employed-by-flock", "Randy Gluck employed by Flock Safety", GLUCK, "employed_by", FLOCK, source_keys=("hunyar", "acpc"), note="Public reporting identifies Gluck as a Flock business-development manager.", confidence=0.96),
        relation("starintel:relation:dpd-part-of-city-of-dunwoody", "Dunwoody Police Department part of City of Dunwoody", DPD, "part_of", DUNWOODY, source_keys=("acpc", "muckrock-contracts"), confidence=0.99),
        relation("starintel:relation:dunwoody-pd-uses-flock", "Dunwoody Police Department uses Flock technology", DPD, "uses_vendor_technology", FLOCK, source_keys=("acpc", "muckrock-contracts"), confidence=0.99),
        relation("starintel:relation:mjcca-shares-cameras-with-dunwoody-pd", "MJCCA camera feeds shared with Dunwoody Police", MJCCA, "shares_camera_feeds_with", DPD, source_keys=("404", "acpc", "ledger"), note="Sources describe MJCCA cameras as integrated/shared with the Dunwoody police Flock environment.", confidence=0.96),
        relation("starintel:relation:bob-carter-viewed-mjcca-gymnastics-camera", "Bob Carter viewed MJCCA Gymnastics camera", CARTER, "viewed_live_camera", GYM_CAMERA, source_keys=("hunyar", "acpc", "404", "flock"), note="Event-log analysis and reporting identify the Sept. 30, 2025 live-view access.", qualifiers={"event_id": CARTER_EVENT, "date": "2025-09-30"}, confidence=0.97),
        relation("starintel:relation:randy-gluck-viewed-mjcca-pool-camera", "Randy Gluck viewed MJCCA Main Pool Right camera", GLUCK, "viewed_live_camera", POOL_CAMERA, source_keys=("hunyar", "acpc", "ledger"), note="Published log analysis and reporting identify the July 23, 2025 access.", qualifiers={"event_id": GLUCK_EVENT, "date": "2025-07-23"}, confidence=0.92),
    ])

    docs.append(
        make(
            "analysis", ANALYSIS, "Initial assessment: Flock/Dunwoody/MJCCA camera access",
            "Evidence-first separation of what is established, what is reported from audit-log analysis, what Flock says about purpose and authorization, and what remains unresolved.",
            {
                "question": "What can be established from public evidence about Flock employee access to MJCCA camera feeds through Dunwoody's Flock environment, especially Bob Carter's Sept. 30, 2025 Gymnastics-camera view?",
                "method": "Triangulate open-records analysis, Flock's first-party statement, independent reporting, local reporting, records-request pages, and the triggering social post; keep attributed explanations separate from underlying factual adjudication.",
                "framework": "evidence-first claim separation",
                "scope": "Sept. 30, 2025 Carter access, July 23 related Gluck access, demo explanation, authorization chain, and auditability gaps",
                "input_ids": [CARTER_EVENT, GLUCK_EVENT, CLAIM_ACCESS, CLAIM_SINGLE, CLAIM_DEMO, CLAIM_SCOPE, CLAIM_POLICY, CLAIM_AGREEMENT_GAP],
                "finding_ids": [CLAIM_ACCESS, CLAIM_SINGLE, CLAIM_DEMO, CLAIM_SCOPE, CLAIM_POLICY, CLAIM_AGREEMENT_GAP],
                "findings": [
                    "The Carter access event is strongly corroborated and acknowledged in substance by Flock.",
                    "The sole-camera-that-day detail is supported by Hunyar's published event-log analysis and repeated by local reporting, but the raw export was not independently parsed in this pass.",
                    "Flock characterizes the access as an authorized routine demo; that is confirmed as Flock's position, not as independent proof of the underlying authorization.",
                    "The public documentary chain establishing who authorized access, under what instrument, and with what scope remains unresolved.",
                    "Available public evidence does not establish viewing duration, whether children were present or visible, or improper personal intent.",
                    "Related July 23 access by Randy Gluck shows that the Sept. 30 event was not the only reported Flock-employee access to sensitive MJCCA feeds.",
                ],
                "conclusions": [
                    "The viral post's factual nucleus survives source checking, but insinuations about motive are unsupported.",
                    "The highest-value next step is authorization-chain and raw-audit-log reconstruction rather than additional social-media amplification.",
                ],
                "recommendations": [
                    "Obtain the original event-log export and reproduce Carter's same-day view count.",
                    "Obtain every demo-partner agreement, amendment, permission record, and communication effective on Sept. 30, 2025.",
                    "Obtain the primary MJCCA camera-sharing terms and compare their authorized purpose to demo use.",
                    "Determine which Flock live-view actions are logged, whether duration is logged elsewhere, and what role/permission Carter and Gluck held at the time.",
                ],
                "counterarguments": [
                    "Flock says Dunwoody explicitly authorized select employees to conduct demos in the live environment.",
                    "No reviewed evidence establishes that Carter selected the camera for an improper personal purpose.",
                ],
                "limitations": [
                    "The full raw event-log export was not public in the sources reviewed because the researcher said it contained unredacted personal information.",
                    "This pass did not authenticate a demo-partner agreement or primary MJCCA sharing agreement.",
                ],
                "unresolved": [
                    "Who authorized the demo access and through what document or system permission?",
                    "What exact camera-selection workflow led to the Gymnastics feed?",
                    "How long was the live view open and what was visible?",
                    "What did the complete Carter and Gluck account/permission history show on the event dates?",
                ],
                "confidence": 0.94,
            },
            source_keys=("hunyar", "flock", "404", "acpc", "ledger", "muckrock-camera-partnership", "muckrock-contracts", "deflock-x"),
            evidence_items=[
                evidence("flock", "Flock acknowledges the Dunwoody sensitive-location demo and describes its authorization position.", confidence=0.98),
                evidence("acpc", "ACPC independently identifies Carter, Gluck, dates, camera labels, and the mayor's sales-call explanation.", confidence=0.95),
                evidence("404", "404 Media independently reports the access and Flock's response.", confidence=0.95),
                evidence("hunyar", "Hunyar provides the most detailed published event-log sequence and request identifiers.", confidence=0.9),
            ],
            tags=("analysis", "flock-safety", "dunwoody", "mjcca"),
            related_ids=(ROOT_TARGET,),
            assessment={"confidence": 0.94, "uncertainty": 0.06, "caveats": ["Do not infer sexual motive, child presence, or viewing duration from the access log alone."]},
        )
    )

    docs.extend([
        target(
            ROOT_TARGET,
            "Root target: Flock access to Dunwoody/MJCCA camera feeds",
            "Flock employee access to MJCCA cameras through Dunwoody's Flock environment",
            "What authorized, enabled, logged, and governed Flock employee access to MJCCA camera feeds, and what can be established about the Sept. 30, 2025 Carter event?",
            ["Reconstruct access events from primary logs", "Reconstruct authorization chain", "Recover MJCCA sharing terms", "Map Flock account roles and audit semantics"],
            seed_ids=[CARTER_EVENT, CLAIM_ACCESS, CLAIM_SINGLE, CLAIM_DEMO, CLAIM_SCOPE, CLAIM_AGREEMENT_GAP],
            priority=1.0,
            next_action="Acquire primary audit logs and authorization documents and reconcile them to the published account.",
        ),
        target(
            TARGET_LOGS,
            "Target: original Dunwoody Flock event logs",
            "D048397-031926 and related Dunwoody Flock audit exports",
            "Can the original event-log export reproduce Carter's Sept. 30, 2025 Gymnastics entry, the claimed one-view same-day count, and the surrounding account activity?",
            ["Acquire an appropriately redacted native export", "Verify timestamps and event types", "Reproduce per-user view sequences", "Preserve audit-log limitations"],
            seed_ids=[CARTER_EVENT, CLAIM_SINGLE],
            priority=1.0,
            next_action="Acquire a redacted native copy of event-logs_010125_031926 and independently parse the Carter and Gluck sequences.",
        ),
        target(
            TARGET_AUTH,
            "Target: Dunwoody/Flock demo authorization chain",
            "Demo-partner authorization effective Sept. 30, 2025",
            "What written or system-level authorization allowed Flock employees to use Dunwoody-connected private cameras for product demonstrations, who approved it, and what scope or limits applied?",
            ["Acquire demo-partner agreement and amendments", "Identify signatories and effective dates", "Collect demo scheduling/approval communications", "Compare authority to MJCCA sharing terms"],
            seed_ids=[CLAIM_DEMO, CLAIM_AGREEMENT_GAP, FLOCK, DPD, DUNWOODY],
            priority=1.0,
            next_action="Search city and Flock records for the exact demo-partner instrument and communications authorizing the Sept. 30 demo.",
        ),
        target(
            TARGET_MJCCA,
            "Target: MJCCA camera-sharing terms",
            "MJCCA camera integration/sharing agreement and onboarding records",
            "What did MJCCA authorize when its cameras were connected to Dunwoody/Flock, and did that authorization include vendor demonstrations or third-party viewing?",
            ["Acquire primary agreement or onboarding terms", "Identify permitted purposes and recipients", "Identify any Do Not Share controls", "Compare terms to documented access events"],
            seed_ids=[MJCCA, CLAIM_SCOPE, CARTER_EVENT, GLUCK_EVENT],
            priority=0.99,
            next_action="Acquire primary MJCCA-Flock/Dunwoody sharing documentation and any configuration records governing access.",
        ),
        target(
            TARGET_AUDIT,
            "Target: Flock live-view audit semantics and permissions",
            "Flock live-view logging, role permissions, and session duration",
            "What actions did Flock's 2025 audit system record or omit, and what roles and permissions did Carter and Gluck hold when they accessed Dunwoody cameras?",
            ["Obtain historical user export D048465-032526 and adjacent exports", "Map role and permission flags", "Determine whether live-view termination/duration is logged", "Test completeness against known actions"],
            seed_ids=[CARTER, GLUCK, CARTER_EVENT, GLUCK_EVENT],
            priority=0.97,
            next_action="Acquire user/permission exports and technical audit documentation and reconcile them to known live-view events.",
        ),
    ])

    docs.append(
        make(
            "research-pass", RESEARCH_PASS, "Research pass: Flock/Dunwoody/MJCCA camera access",
            "Initial AutoDig pass converting the viral claim into typed StarIntel records with explicit evidence, caveats, graph edges, and recursive documentary targets.",
            {
                "research_question": "What is established about Flock employee access to MJCCA cameras through Dunwoody, and what remains unverified?",
                "method": "Evidence-first public-source triangulation with attributed-claim separation and explicit unresolved targets.",
                "classification_rules": [
                    "Treat Flock's explanation as an attributed company claim unless independently documented.",
                    "Treat Hunyar's log counts as supported but not independently reproduced until the original export is parsed.",
                    "Do not infer motive, viewing duration, or presence of children from camera-access metadata alone.",
                    "Prefer primary records and first-party statements; use reporting for corroboration and discovery.",
                ],
                "finding_ids": [CLAIM_ACCESS, CLAIM_SINGLE, CLAIM_DEMO, CLAIM_SCOPE, CLAIM_POLICY, CLAIM_AGREEMENT_GAP],
                "findings": [
                    {"id": CLAIM_ACCESS, "status": "corroborated", "confidence": 0.98},
                    {"id": CLAIM_SINGLE, "status": "supported-not-independently-reproduced", "confidence": 0.9},
                    {"id": CLAIM_DEMO, "status": "confirmed-as-attributed-statement", "confidence": 1.0},
                    {"id": CLAIM_AGREEMENT_GAP, "status": "unresolved", "confidence": 0.78},
                ],
                "supporting_record_ids": [CARTER_EVENT, GLUCK_EVENT, ANALYSIS, CLAIM_ACCESS, CLAIM_SINGLE, CLAIM_DEMO, CLAIM_SCOPE, CLAIM_POLICY, CLAIM_AGREEMENT_GAP],
                "counterevidence_ids": [CLAIM_DEMO],
                "unresolved_target_ids": [TARGET_LOGS, TARGET_AUTH, TARGET_MJCCA, TARGET_AUDIT],
                "source_ids": [source["id"] for source in SOURCES.values()],
                "agent_identity": "GPT-5.6 Sol",
                "narrative_role": "initial verification and graph-construction pass",
                "started_at": GENERATED_AT,
                "completed_at": GENERATED_AT,
                "iteration": 1,
            },
            source_keys=tuple(SOURCES.keys()),
            tags=("research-pass", "flock-safety", "dunwoody", "mjcca"),
            related_ids=(ROOT_TARGET, ANALYSIS),
            workflow={"research_status": "completed", "run_id": RUN_ID, "completed_at": GENERATED_AT, "root_target_id": ROOT_TARGET, "recursion_depth": 0, "max_depth": 2},
            verification={"status": "schema-validated-source-triangulated", "verified": True, "verified_by": ["starintel_doc.validate_document"], "verified_at": GENERATED_AT, "methods": ["schema validation", "source triangulation"], "unresolved": ["Primary authorization and raw audit-log targets remain open."], "last_reviewed_at": GENERATED_AT},
        )
    )

    seen: set[str] = set()
    for document in docs:
        validate_document(document)
        doc_id = document["_id"]
        if doc_id in seen:
            raise ValueError(f"duplicate document id: {doc_id}")
        seen.add(doc_id)
    return docs

def main() -> int:
    docs = build_documents()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    payload = "".join(compact(document) + "\n" for document in docs)
    PACKET.write_text(payload, encoding="utf-8")
    subprocess.run(
        [sys.executable, str(ROOT / "scripts/starintel.py"), "import", str(PACKET), "--root", str(ROOT)],
        cwd=ROOT,
        check=True,
    )
    print(json.dumps({
        "packet": str(PACKET.relative_to(ROOT)),
        "documents": len(docs),
        "ids": [document["_id"] for document in docs],
    }, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
