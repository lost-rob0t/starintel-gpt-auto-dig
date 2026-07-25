from __future__ import annotations

from copy import deepcopy
from typing import Any

SCHEMA_VERSION = "0.9.0"
SCHEMA_ID = "https://spec.starintel.actor/schema/starintel-doc-v0.9.0.json"


def string(*, enum: list[str] | None = None, pattern: str | None = None) -> dict[str, Any]:
    out: dict[str, Any] = {"type": "string"}
    if enum is not None:
        out["enum"] = enum
    if pattern is not None:
        out["pattern"] = pattern
    return out


def number(*, minimum: float | None = None, maximum: float | None = None) -> dict[str, Any]:
    out: dict[str, Any] = {"type": "number"}
    if minimum is not None:
        out["minimum"] = minimum
    if maximum is not None:
        out["maximum"] = maximum
    return out


def integer(*, minimum: int | None = None) -> dict[str, Any]:
    out: dict[str, Any] = {"type": "integer"}
    if minimum is not None:
        out["minimum"] = minimum
    return out


def boolean() -> dict[str, Any]:
    return {"type": "boolean"}


def array(items: dict[str, Any]) -> dict[str, Any]:
    return {"type": "array", "items": items}


def obj(
    properties: dict[str, Any],
    *,
    required: tuple[str, ...] = (),
    additional: bool | dict[str, Any] = False,
) -> dict[str, Any]:
    out: dict[str, Any] = {
        "type": "object",
        "properties": properties,
        "additionalProperties": additional,
    }
    if required:
        out["required"] = list(required)
    return out


STR = string()
STRS = array(STR)
NUM = number()
BOOL = boolean()
INT = integer()
SCORE = number(minimum=0.0, maximum=1.0)
DATE_TIME = {"type": "string", "format": "date-time"}
NULLABLE_DATE_TIME = {"anyOf": [DATE_TIME, {"type": "null"}]}
NULLABLE_STRING = {"anyOf": [STR, {"type": "null"}]}
JSON_VALUE: dict[str, Any] = {}
JSON_MAP = {"type": "object", "additionalProperties": True}

IDENTIFIER = obj(
    {
        "scheme": STR,
        "value": STR,
        "issuer": STR,
        "jurisdiction": STR,
        "canonical": BOOL,
        "confidence": SCORE,
        "valid_from": NULLABLE_DATE_TIME,
        "valid_to": NULLABLE_DATE_TIME,
        "url": STR,
        "notes": STR,
    },
    required=("scheme", "value"),
)

SOURCE = obj(
    {
        "source_id": STR,
        "kind": STR,
        "type": STR,
        "sensor": STR,
        "name": STR,
        "title": STR,
        "publisher": STR,
        "author": STR,
        "organization": STR,
        "uri": STR,
        "url": STR,
        "archive_url": STR,
        "published_at": NULLABLE_DATE_TIME,
        "retrieved_at": NULLABLE_DATE_TIME,
        "accessed_at": NULLABLE_DATE_TIME,
        "language": STR,
        "jurisdiction": STR,
        "medium": STR,
        "credibility": SCORE,
        "reliability": SCORE,
        "authenticity": SCORE,
        "independence": SCORE,
        "access_method": STR,
        "query": STR,
        "request_id": STR,
        "response_status": INT,
        "content_hash": STR,
        "hash_algorithm": STR,
        "license": STR,
        "quote": STR,
        "locator": STR,
        "page": STR,
        "section": STR,
        "notes": STR,
        "metadata": JSON_MAP,
    }
)

EVIDENCE = obj(
    {
        "evidence_id": STR,
        "source_id": STR,
        "source_url": STR,
        "kind": STR,
        "role": STR,
        "claim": STR,
        "observation": STR,
        "excerpt": STR,
        "locator": STR,
        "page": STR,
        "section": STR,
        "collected_at": NULLABLE_DATE_TIME,
        "observed_at": NULLABLE_DATE_TIME,
        "valid_from": NULLABLE_DATE_TIME,
        "valid_to": NULLABLE_DATE_TIME,
        "content_hash": STR,
        "hash_algorithm": STR,
        "confidence": SCORE,
        "corroborates": STRS,
        "contradicts": STRS,
        "chain_of_custody": STRS,
        "attachments": STRS,
        "status": STR,
        "notes": STR,
        "metadata": JSON_MAP,
    }
)

TEMPORAL = obj(
    {
        "observed_at": NULLABLE_DATE_TIME,
        "collected_at": NULLABLE_DATE_TIME,
        "published_at": NULLABLE_DATE_TIME,
        "created_at": NULLABLE_DATE_TIME,
        "modified_at": NULLABLE_DATE_TIME,
        "event_start": NULLABLE_DATE_TIME,
        "event_end": NULLABLE_DATE_TIME,
        "valid_from": NULLABLE_DATE_TIME,
        "valid_to": NULLABLE_DATE_TIME,
        "first_seen": NULLABLE_DATE_TIME,
        "last_seen": NULLABLE_DATE_TIME,
        "timezone": STR,
        "precision": STR,
        "recurrence": STR,
        "duration_seconds": NUM,
        "sequence": INT,
        "notes": STR,
    }
)

PROVENANCE = obj(
    {
        "collector": STR,
        "collector_type": STR,
        "agent": STR,
        "actor": STR,
        "skill": STR,
        "tool": STR,
        "model": STR,
        "prompt_hash": STR,
        "run_id": STR,
        "session_id": STR,
        "operation_id": STR,
        "method": STR,
        "pipeline": STR,
        "imported_from": STR,
        "original_id": STR,
        "original_schema_version": STR,
        "original_path": STR,
        "transform": STR,
        "software_version": STR,
        "environment": STR,
        "created_by": STR,
        "updated_by": STR,
        "notes": STR,
        "metadata": JSON_MAP,
    }
)

ASSESSMENT = obj(
    {
        "confidence": SCORE,
        "analytic_confidence": SCORE,
        "source_reliability": SCORE,
        "information_credibility": SCORE,
        "relevance": SCORE,
        "priority": SCORE,
        "threat": SCORE,
        "impact": SCORE,
        "likelihood": SCORE,
        "severity": SCORE,
        "deception_probability": SCORE,
        "uncertainty": SCORE,
        "bias": SCORE,
        "completeness": SCORE,
        "assumptions": STRS,
        "inferences": STRS,
        "alternatives": STRS,
        "counterevidence": STRS,
        "gaps": STRS,
        "caveats": STRS,
        "criteria": JSON_MAP,
        "scores": {"type": "object", "additionalProperties": NUM},
        "notes": STR,
    }
)

VERIFICATION = obj(
    {
        "status": STR,
        "result": STR,
        "verified": BOOL,
        "verified_by": STRS,
        "verified_at": NULLABLE_DATE_TIME,
        "methods": STRS,
        "checks": STRS,
        "conflicts": STRS,
        "unresolved": STRS,
        "last_reviewed_at": NULLABLE_DATE_TIME,
        "review_due_at": NULLABLE_DATE_TIME,
        "review_count": INT,
        "notes": STR,
    }
)

HANDLING = obj(
    {
        "visibility": STR,
        "handling": STR,
        "classification": STR,
        "compartment": STR,
        "dissemination": STRS,
        "access_groups": STRS,
        "caveats": STRS,
        "retention": STR,
        "embargo_until": NULLABLE_DATE_TIME,
        "pii": BOOL,
        "sensitive": BOOL,
        "redactions": STRS,
        "license": STR,
        "copyright": STR,
        "notes": STR,
    }
)

LINEAGE = obj(
    {
        "parent_ids": STRS,
        "child_ids": STRS,
        "derived_from": STRS,
        "source_document_ids": STRS,
        "supersedes": STRS,
        "superseded_by": STRS,
        "merged_from": STRS,
        "split_from": STRS,
        "duplicates": STRS,
        "replaces": STRS,
        "migration_from": STR,
        "migration_notes": STRS,
        "transform": STR,
        "generation": INT,
    }
)

QUALITY = obj(
    {
        "completeness": SCORE,
        "consistency": SCORE,
        "timeliness": SCORE,
        "uniqueness": SCORE,
        "accuracy": SCORE,
        "coverage": SCORE,
        "freshness": SCORE,
        "validation_status": STR,
        "validation_errors": STRS,
        "warnings": STRS,
        "missing_fields": STRS,
        "last_validated_at": NULLABLE_DATE_TIME,
        "validator": STR,
    }
)

WORKFLOW = obj(
    {
        "research_status": STR,
        "queue": STR,
        "priority": NUM,
        "assigned_to": STRS,
        "requested_by": STR,
        "due_at": NULLABLE_DATE_TIME,
        "next_action": STR,
        "blockers": STRS,
        "run_id": STR,
        "actor": STR,
        "skill": STR,
        "recursion_depth": INT,
        "max_depth": INT,
        "root_target_id": STR,
        "selected_from": STRS,
        "selection_reason": STRS,
        "selection_score": NUM,
        "selection_features": JSON_MAP,
        "completed_at": NULLABLE_DATE_TIME,
        "notes": STR,
    }
)

GEOSPATIAL = obj(
    {
        "lat": NUM,
        "lon": NUM,
        "long": NUM,
        "altitude": NUM,
        "accuracy_meters": NUM,
        "bbox": array(NUM),
        "geohash": STR,
        "coordinate_system": STR,
        "place_name": STR,
        "address_id": STR,
        "street": STR,
        "street2": STR,
        "city": STR,
        "county": STR,
        "state": STR,
        "region": STR,
        "postal": STR,
        "country": STR,
        "country_code": STR,
        "timezone": STR,
        "jurisdiction": STR,
        "notes": STR,
    }
)

ATTACHMENT = obj(
    {
        "attachment_id": STR,
        "name": STR,
        "role": STR,
        "description": STR,
        "media_type": STR,
        "uri": STR,
        "size_bytes": INT,
        "content_hash": STR,
        "hash_algorithm": STR,
        "captured_at": NULLABLE_DATE_TIME,
        "created_at": NULLABLE_DATE_TIME,
        "metadata": JSON_MAP,
    }
)

RELATION_ENDPOINT = obj(
    {
        "id": STR,
        "entity_id": STR,
        "document_id": STR,
        "external_id": STR,
        "dtype": STR,
        "label": STR,
        "name": STR,
        "role": STR,
        "unresolved": BOOL,
        "external_ids": array(IDENTIFIER),
        "aliases": STRS,
        "qualifiers": JSON_MAP,
        "metadata": JSON_MAP,
    }
)


ENTITY_FIELDS = {
    "etype": STR,
    "eid": STR,
    "name": STR,
    "display_name": STR,
    "legal_name": STR,
    "short_name": STR,
    "former_names": STRS,
    "description": STR,
    "bio": STR,
    "jurisdiction": STR,
    "country": STR,
    "status": STR,
    "founded_at": NULLABLE_DATE_TIME,
    "dissolved_at": NULLABLE_DATE_TIME,
    "website": STR,
    "image_url": STR,
    "logo_url": STR,
    "external_ids": array(IDENTIFIER),
    "contact_ids": STRS,
    "location_ids": STRS,
}

PERSON_FIELDS = {
    **ENTITY_FIELDS,
    "fname": STR,
    "mname": STR,
    "lname": STR,
    "suffix": STR,
    "full_name": STR,
    "preferred_name": STR,
    "gender": STR,
    "pronouns": STR,
    "dob": NULLABLE_DATE_TIME,
    "birthplace": STR,
    "death_date": NULLABLE_DATE_TIME,
    "nationalities": STRS,
    "citizenships": STRS,
    "occupations": STRS,
    "employers": STRS,
    "positions": STRS,
    "education_ids": STRS,
    "social_account_ids": STRS,
    "email_ids": STRS,
    "phone_ids": STRS,
    "family_ids": STRS,
    "associate_ids": STRS,
    "political_affiliations": STRS,
    "professional_affiliations": STRS,
    "public_roles": STRS,
    "misc": STRS,
}

ORG_FIELDS = {
    **ENTITY_FIELDS,
    "org_type": STR,
    "registration_number": STR,
    "reg": STR,
    "tax_id": STR,
    "lei": STR,
    "ticker": STR,
    "exchange": STR,
    "industry": STR,
    "sectors": STRS,
    "mission": STR,
    "business": STR,
    "headquarters": STR,
    "parent_id": STR,
    "subsidiary_ids": STRS,
    "affiliate_ids": STRS,
    "predecessor_ids": STRS,
    "successor_ids": STRS,
    "owner_ids": STRS,
    "beneficial_owner_ids": STRS,
    "director_ids": STRS,
    "executive_ids": STRS,
    "member_ids": STRS,
    "employee_count": INT,
    "revenue": NUM,
    "currency": STR,
    "fiscal_year_end": STR,
    "products": STRS,
    "services": STRS,
    "markets": STRS,
    "government_levels": STRS,
}

RELATION_FIELDS = {
    "subject": {"anyOf": [STR, RELATION_ENDPOINT]},
    "predicate": STR,
    "object": {"anyOf": [STR, RELATION_ENDPOINT, array(STR), array(RELATION_ENDPOINT)]},
    "source": STR,
    "target": STR,
    "directed": BOOL,
    "inverse_predicate": STR,
    "relation_type": STR,
    "qualifiers": JSON_MAP,
    "weight": NUM,
    "confidence": SCORE,
    "start_at": NULLABLE_DATE_TIME,
    "end_at": NULLABLE_DATE_TIME,
    "active": BOOL,
    "note": STR,
}

TARGET_FIELDS = {
    "actor": STR,
    "target": STR,
    "target_id": STR,
    "target_type": STR,
    "query": STR,
    "research_question": STR,
    "hypotheses": STRS,
    "objectives": STRS,
    "in_scope": STRS,
    "out_of_scope": STRS,
    "scope_type": STR,
    "seed_ids": STRS,
    "source_ids": STRS,
    "required_dtypes": STRS,
    "preferred_sources": STRS,
    "excluded_sources": STRS,
    "delay": INT,
    "recurring": BOOL,
    "recurrence": STR,
    "options": array(JSON_VALUE),
    "depth": INT,
    "max_depth": INT,
    "breadth": INT,
    "priority": NUM,
    "score": NUM,
    "selection_reason": STRS,
    "status": STR,
    "next_run_at": NULLABLE_DATE_TIME,
}

HOST_FIELDS = {
    "hostname": STR,
    "fqdn": STR,
    "ip": STR,
    "ipv4": STRS,
    "ipv6": STRS,
    "mac": STR,
    "asn": INT,
    "organization": STR,
    "network_id": STR,
    "domain_ids": STRS,
    "reverse_dns": STRS,
    "os": STR,
    "os_version": STR,
    "architecture": STR,
    "device_type": STR,
    "vendor": STR,
    "model": STR,
    "services": array(JSON_MAP),
    "ports": array(JSON_MAP),
    "certificates": array(JSON_MAP),
    "technologies": STRS,
    "vulnerabilities": STRS,
    "first_seen": NULLABLE_DATE_TIME,
    "last_seen": NULLABLE_DATE_TIME,
}

DOMAIN_FIELDS = {
    "domain": STR,
    "record_type": STR,
    "record": STR,
    "resolved_addresses": STRS,
    "registrar": STR,
    "registrant": STR,
    "created_at": NULLABLE_DATE_TIME,
    "expires_at": NULLABLE_DATE_TIME,
    "updated_at": NULLABLE_DATE_TIME,
    "nameservers": STRS,
    "dns_records": array(JSON_MAP),
    "subdomains": STRS,
    "whois": JSON_MAP,
    "status": STRS,
    "dnssec": BOOL,
}

NETWORK_FIELDS = {
    "org": STR,
    "asn": INT,
    "asn_name": STR,
    "subnet": STR,
    "cidr": STR,
    "range_start": STR,
    "range_end": STR,
    "rir": STR,
    "country": STR,
    "description": STR,
    "route_objects": STRS,
    "peer_asns": array(INT),
    "upstream_asns": array(INT),
    "downstream_asns": array(INT),
}

URL_FIELDS = {
    "url": STR,
    "scheme": STR,
    "host": STR,
    "port": INT,
    "path": STR,
    "query": STR,
    "fragment": STR,
    "title": STR,
    "content": STR,
    "content_type": STR,
    "status_code": INT,
    "headers": JSON_MAP,
    "redirect_chain": STRS,
    "links": STRS,
    "forms": array(JSON_MAP),
    "technologies": STRS,
    "content_hash": STR,
    "captured_at": NULLABLE_DATE_TIME,
}

LOCATION_FIELDS = {
    "name": STR,
    "location_type": STR,
    "address": STR,
    "street": STR,
    "street2": STR,
    "city": STR,
    "county": STR,
    "state": STR,
    "region": STR,
    "postal": STR,
    "country": STR,
    "country_code": STR,
    "lat": NUM,
    "long": NUM,
    "lon": NUM,
    "alt": NUM,
    "timezone": STR,
    "geohash": STR,
    "parent_location_id": STR,
    "contained_location_ids": STRS,
}

CONTACT_FIELDS = {
    "value": STR,
    "type": STR,
    "label": STR,
    "owner_id": STR,
    "status": STR,
    "verified": BOOL,
    "verified_at": NULLABLE_DATE_TIME,
    "first_seen": NULLABLE_DATE_TIME,
    "last_seen": NULLABLE_DATE_TIME,
}

MESSAGE_FIELDS = {
    "content": STR,
    "platform": STR,
    "user": STR,
    "user_id": STR,
    "is_reply": BOOL,
    "media": STRS,
    "message_id": STR,
    "reply_to": STR,
    "group": STR,
    "channel": STR,
    "thread_id": STR,
    "mentions": STRS,
    "reactions": array(JSON_MAP),
    "links": STRS,
    "posted_at": NULLABLE_DATE_TIME,
    "edited_at": NULLABLE_DATE_TIME,
    "deleted": BOOL,
    "visibility": STR,
}

POST_FIELDS = {
    **MESSAGE_FIELDS,
    "replies": array(JSON_MAP),
    "reply_count": INT,
    "repost_count": INT,
    "like_count": INT,
    "view_count": INT,
    "url": STR,
    "tags": STRS,
    "title": STR,
    "quote_post_id": STR,
}

EVENT_FIELDS = {
    "event_kind": STR,
    "name": STR,
    "description": STR,
    "participant_ids": STRS,
    "participants": STRS,
    "organizer_ids": STRS,
    "sponsor_ids": STRS,
    "location_ids": STRS,
    "start_at": NULLABLE_DATE_TIME,
    "end_at": NULLABLE_DATE_TIME,
    "status": STR,
    "outcome": STR,
    "agenda": STRS,
    "decisions": STRS,
    "actions": STRS,
    "amount": NUM,
    "currency": STR,
    "jurisdiction": STR,
    "case_id": STR,
    "contract_id": STR,
    "meeting_id": STR,
}

CLAIM_FIELDS = {
    "claim": STR,
    "claimant_id": STR,
    "subject_ids": STRS,
    "predicate": STR,
    "object": JSON_VALUE,
    "claim_type": STR,
    "polarity": STR,
    "certainty": SCORE,
    "supporting_evidence_ids": STRS,
    "contradicting_evidence_ids": STRS,
    "status": STR,
    "adjudication": STR,
}

ANALYSIS_FIELDS = {
    "question": STR,
    "method": STR,
    "framework": STR,
    "scope": STR,
    "input_ids": STRS,
    "finding_ids": STRS,
    "findings": STRS,
    "conclusions": STRS,
    "recommendations": STRS,
    "counterarguments": STRS,
    "limitations": STRS,
    "unresolved": STRS,
    "confidence": SCORE,
}

PRODUCT_FIELDS = {
    **ENTITY_FIELDS,
    "manufacturer_id": STR,
    "vendor_ids": STRS,
    "product_type": STR,
    "model": STR,
    "version_name": STR,
    "release_date": NULLABLE_DATE_TIME,
    "end_of_life": NULLABLE_DATE_TIME,
    "features": STRS,
    "capabilities": STRS,
    "integrations": STRS,
    "customers": STRS,
    "license": STR,
    "pricing": JSON_MAP,
    "technical": JSON_MAP,
}

FINANCIAL_FIELDS = {
    "entity_id": STR,
    "observation_type": STR,
    "amount": NUM,
    "currency": STR,
    "value_type": STR,
    "period_start": NULLABLE_DATE_TIME,
    "period_end": NULLABLE_DATE_TIME,
    "fiscal_year": INT,
    "fiscal_quarter": STR,
    "reported_at": NULLABLE_DATE_TIME,
    "counterparty_ids": STRS,
    "instrument": STR,
    "units": NUM,
    "unit_price": NUM,
    "percentage": NUM,
    "methodology": STR,
    "qualifications": STRS,
}

CONTRACT_FIELDS = {
    "contract_id": STR,
    "award_id": STR,
    "solicitation_id": STR,
    "vehicle_id": STR,
    "buyer_id": STR,
    "seller_id": STR,
    "agency_ids": STRS,
    "vendor_ids": STRS,
    "subcontractor_ids": STRS,
    "description": STR,
    "scope": STR,
    "award_type": STR,
    "competition_type": STR,
    "status": STR,
    "signed_at": NULLABLE_DATE_TIME,
    "start_at": NULLABLE_DATE_TIME,
    "end_at": NULLABLE_DATE_TIME,
    "ceiling_amount": NUM,
    "potential_amount": NUM,
    "obligated_amount": NUM,
    "outlay_amount": NUM,
    "recognized_revenue": NUM,
    "currency": STR,
    "naics": STRS,
    "psc": STRS,
    "place_of_performance": STR,
    "modifications": array(JSON_MAP),
}

LOBBYING_FIELDS = {
    "filing_id": STR,
    "registrant_id": STR,
    "client_id": STR,
    "lobbyist_ids": STRS,
    "government_entities": STRS,
    "issues": STRS,
    "specific_issues": STRS,
    "income": NUM,
    "expenses": NUM,
    "currency": STR,
    "period_start": NULLABLE_DATE_TIME,
    "period_end": NULLABLE_DATE_TIME,
    "filed_at": NULLABLE_DATE_TIME,
    "filing_type": STR,
    "amendment": BOOL,
    "termination": BOOL,
}

LEGAL_FIELDS = {
    "case_number": STR,
    "case_name": STR,
    "court": STR,
    "jurisdiction": STR,
    "judge_ids": STRS,
    "party_ids": STRS,
    "plaintiff_ids": STRS,
    "defendant_ids": STRS,
    "attorney_ids": STRS,
    "case_type": STR,
    "claims": STRS,
    "status": STR,
    "filed_at": NULLABLE_DATE_TIME,
    "closed_at": NULLABLE_DATE_TIME,
    "docket_entries": array(JSON_MAP),
    "outcome": STR,
    "citation": STR,
}

RESEARCH_PASS_FIELDS = {
    "research_question": STR,
    "method": STR,
    "classification_rules": STRS,
    "finding_ids": STRS,
    "findings": array(JSON_MAP),
    "supporting_record_ids": STRS,
    "counterevidence_ids": STRS,
    "unresolved_target_ids": STRS,
    "source_ids": STRS,
    "agent_identity": STR,
    "narrative_role": STR,
    "started_at": NULLABLE_DATE_TIME,
    "completed_at": NULLABLE_DATE_TIME,
    "iteration": INT,
}

MANIFEST_FIELDS = {
    "manifest_type": STR,
    "name": STR,
    "actor": STR,
    "consumer_path": STR,
    "target_options": array(JSON_VALUE),
    "document_ids": STRS,
    "counts_by_dtype": {"type": "object", "additionalProperties": INT},
    "record_count": INT,
    "hash_algorithm": STR,
    "content_hash": STR,
    "files": array(JSON_MAP),
    "schema_versions": STRS,
    "generated_at": NULLABLE_DATE_TIME,
}

TYPE_FIELDS: dict[str, dict[str, Any]] = {
    "document": {},
    "entity": ENTITY_FIELDS,
    "person": PERSON_FIELDS,
    "org": ORG_FIELDS,
    "relation": RELATION_FIELDS,
    "target": TARGET_FIELDS,
    "investigation-target": TARGET_FIELDS,
    "domain": DOMAIN_FIELDS,
    "network": NETWORK_FIELDS,
    "host": HOST_FIELDS,
    "url": URL_FIELDS,
    "geo": LOCATION_FIELDS,
    "address": LOCATION_FIELDS,
    "location": LOCATION_FIELDS,
    "phone": {**CONTACT_FIELDS, "number": STR, "carrier": STR, "phone_type": STR, "country_code": STR, "extension": STR},
    "email": {**CONTACT_FIELDS, "user": STR, "domain": STR, "address": STR, "display_name": STR},
    "email-message": {
        **MESSAGE_FIELDS,
        "body": STR,
        "subject": STR,
        "to": STRS,
        "from": STR,
        "cc": STRS,
        "bcc": STRS,
        "headers": JSON_MAP,
        "attachments": STRS,
    },
    "user": {**ENTITY_FIELDS, "url": STR, "username": STR, "platform": STR, "bio": STR, "misc": array(JSON_MAP)},
    "message": MESSAGE_FIELDS,
    "social-media-post": POST_FIELDS,
    "breach": {"name": STR, "description": STR, "url": STR, "total": INT, "breached_at": NULLABLE_DATE_TIME, "discovered_at": NULLABLE_DATE_TIME, "data_classes": STRS, "organization_id": STR, "verified": BOOL},
    "product": PRODUCT_FIELDS,
    "event": EVENT_FIELDS,
    "meeting": EVENT_FIELDS,
    "claim": CLAIM_FIELDS,
    "analysis": ANALYSIS_FIELDS,
    "concept": {"term": STR, "definition": STR, "domain": STR, "broader_ids": STRS, "narrower_ids": STRS, "related_ids": STRS, "examples": STRS, "criteria": STRS},
    "observation": {"observer_id": STR, "subject_id": STR, "observation_type": STR, "value": JSON_VALUE, "unit": STR, "method": STR, "instrument": STR, "observed_at": NULLABLE_DATE_TIME},
    "financial-observation": FINANCIAL_FIELDS,
    "contract": CONTRACT_FIELDS,
    "procurement": CONTRACT_FIELDS,
    "grant": {**CONTRACT_FIELDS, "grantor_id": STR, "recipient_ids": STRS, "program": STR, "assistance_listing": STR, "matching_required": BOOL},
    "lobbying-filing": LOBBYING_FIELDS,
    "campaign-finance": {**FINANCIAL_FIELDS, "committee_id": STR, "donor_id": STR, "recipient_id": STR, "filing_id": STR, "contribution_type": STR, "election_cycle": STR},
    "legal-case": LEGAL_FIELDS,
    "policy": {"policy_id": STR, "name": STR, "issuer_id": STR, "jurisdiction": STR, "policy_type": STR, "text": STR, "effective_at": NULLABLE_DATE_TIME, "expires_at": NULLABLE_DATE_TIME, "status": STR, "affected_ids": STRS},
    "education": {"person_id": STR, "institution_id": STR, "degree": STR, "field": STR, "start_at": NULLABLE_DATE_TIME, "end_at": NULLABLE_DATE_TIME, "graduated": BOOL, "honors": STRS},
    "employment": {"person_id": STR, "organization_id": STR, "title": STR, "department": STR, "start_at": NULLABLE_DATE_TIME, "end_at": NULLABLE_DATE_TIME, "current": BOOL, "employment_type": STR, "location_id": STR},
    "ownership": {"owner_id": STR, "asset_id": STR, "ownership_type": STR, "percentage": NUM, "units": NUM, "start_at": NULLABLE_DATE_TIME, "end_at": NULLABLE_DATE_TIME, "beneficial": BOOL, "direct": BOOL},
    "asset": {**ENTITY_FIELDS, "asset_type": STR, "owner_ids": STRS, "operator_ids": STRS, "serial_number": STR, "registration": STR, "value": NUM, "currency": STR, "location_id": STR, "status": STR},
    "media": {"title": STR, "media_type": STR, "uri": STR, "creator_ids": STRS, "publisher_id": STR, "published_at": NULLABLE_DATE_TIME, "duration_seconds": NUM, "transcript": STR, "content_hash": STR, "license": STR},
    "file": {"name": STR, "path": STR, "uri": STR, "media_type": STR, "size_bytes": INT, "content_hash": STR, "hash_algorithm": STR, "created_at": NULLABLE_DATE_TIME, "modified_at": NULLABLE_DATE_TIME, "owner_id": STR},
    "source": SOURCE["properties"],
    "evidence-record": EVIDENCE["properties"],
    "research-pass": RESEARCH_PASS_FIELDS,
    "actor-manifest": MANIFEST_FIELDS,
    "dataset-manifest": MANIFEST_FIELDS,
    "alert": {"alert_type": STR, "subject_ids": STRS, "condition": STR, "threshold": NUM, "triggered_at": NULLABLE_DATE_TIME, "severity": NUM, "status": STR, "acknowledged_by": STRS},
    "task": {"task_type": STR, "subject_ids": STRS, "assignee_ids": STRS, "status": STR, "priority": NUM, "due_at": NULLABLE_DATE_TIME, "completed_at": NULLABLE_DATE_TIME, "instructions": STR, "result_ids": STRS},
}

REQUIRED_DATA_FIELDS: dict[str, tuple[str, ...]] = {
    "relation": ("subject", "predicate", "object"),
    "target": ("target",),
    "investigation-target": ("target",),
    "phone": ("number",),
    "email": ("address",),
    "domain": ("domain",),
    "url": ("url",),
    "claim": ("claim",),
}

DTYPE_ALIASES = {
    "organization": "org",
    "organisation": "org",
    "investigation_target": "investigation-target",
    "social_media_post": "social-media-post",
    "email_message": "email-message",
    "financial_observation": "financial-observation",
    "research_pass": "research-pass",
    "dataset_manifest": "dataset-manifest",
    "actor_manifest": "actor-manifest",
    "legal_case": "legal-case",
    "lobbying_filing": "lobbying-filing",
    "campaign_finance": "campaign-finance",
}

COMMON_PROPERTIES: dict[str, Any] = {
    "_id": string(pattern=r"^[^/\\\x00]+$"),
    "_rev": STR,
    "dataset": STR,
    "dtype": string(enum=sorted(TYPE_FIELDS)),
    "schema_version": {"const": SCHEMA_VERSION},
    "version": integer(minimum=1),
    "date_added": DATE_TIME,
    "date_updated": DATE_TIME,
    "title": STR,
    "summary": STR,
    "description": STR,
    "status": STR,
    "language": STR,
    "tags": STRS,
    "labels": STRS,
    "aliases": STRS,
    "keywords": STRS,
    "identifiers": array(IDENTIFIER),
    "sources": array(SOURCE),
    "evidence": array(EVIDENCE),
    "temporal": TEMPORAL,
    "provenance": PROVENANCE,
    "assessment": ASSESSMENT,
    "verification": VERIFICATION,
    "handling": HANDLING,
    "lineage": LINEAGE,
    "quality": QUALITY,
    "workflow": WORKFLOW,
    "geospatial": GEOSPATIAL,
    "attachments": array(ATTACHMENT),
    "related_ids": STRS,
    "notes": STRS,
    "data": {"type": "object"},
    "extensions": {"type": "object", "additionalProperties": True},
}

REQUIRED_COMMON = (
    "_id",
    "dataset",
    "dtype",
    "schema_version",
    "version",
    "date_added",
    "date_updated",
    "sources",
    "evidence",
    "data",
)


def data_schema(dtype: str) -> dict[str, Any]:
    canonical = DTYPE_ALIASES.get(dtype, dtype)
    if canonical not in TYPE_FIELDS:
        raise KeyError(f"unknown dtype: {dtype}")
    return obj(
        deepcopy(TYPE_FIELDS[canonical]),
        required=REQUIRED_DATA_FIELDS.get(canonical, ()),
        additional=False,
    )


def document_schema(dtype: str | None = None) -> dict[str, Any]:
    properties = deepcopy(COMMON_PROPERTIES)
    if dtype is None:
        variants = []
        for name in sorted(TYPE_FIELDS):
            variants.append(
                {
                    "if": {"properties": {"dtype": {"const": name}}},
                    "then": {"properties": {"data": data_schema(name)}},
                }
            )
        return {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": SCHEMA_ID,
            "title": "StarIntel Document v0.9.0",
            "type": "object",
            "properties": properties,
            "required": list(REQUIRED_COMMON),
            "additionalProperties": False,
            "allOf": variants,
        }
    canonical = DTYPE_ALIASES.get(dtype, dtype)
    properties["dtype"] = {"const": canonical}
    properties["data"] = data_schema(canonical)
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"{SCHEMA_ID}#{canonical}",
        "title": f"StarIntel {canonical} document v0.9.0",
        "type": "object",
        "properties": properties,
        "required": list(REQUIRED_COMMON),
        "additionalProperties": False,
    }
