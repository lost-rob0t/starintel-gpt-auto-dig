from __future__ import annotations

from copy import deepcopy
from typing import Any

from . import spec as _spec

SCHEMA_REVISION = "0.9.0+fields.20260725.1"
SCHEMA_PROFILE = "starintel-core"
SCHEMA_PROFILE_VERSION = "0.9"

STR = _spec.STR
STRS = _spec.STRS
NUM = _spec.NUM
INT = _spec.INT
BOOL = _spec.BOOL
SCORE = _spec.SCORE
DATE_TIME = _spec.DATE_TIME
NULLABLE_DATE_TIME = _spec.NULLABLE_DATE_TIME
JSON_VALUE = _spec.JSON_VALUE
JSON_MAP = _spec.JSON_MAP


def array(items: dict[str, Any]) -> dict[str, Any]:
    return _spec.array(items)


def obj(
    properties: dict[str, Any],
    *,
    required: tuple[str, ...] = (),
    additional: bool | dict[str, Any] = False,
) -> dict[str, Any]:
    return _spec.obj(properties, required=required, additional=additional)


REFERENCE = obj(
    {
        "id": STR,
        "dtype": STR,
        "role": STR,
        "label": STR,
        "dataset": STR,
        "schema_version": STR,
        "external_ids": array(_spec.IDENTIFIER),
        "unresolved": BOOL,
        "confidence": SCORE,
        "valid_from": NULLABLE_DATE_TIME,
        "valid_to": NULLABLE_DATE_TIME,
        "qualifiers": JSON_MAP,
    },
    required=("id",),
)

EXTERNAL_REFERENCE = obj(
    {
        "source_name": STR,
        "external_id": STR,
        "url": STR,
        "description": STR,
        "hashes": {"type": "object", "additionalProperties": STR},
        "retrieved_at": NULLABLE_DATE_TIME,
        "archived_url": STR,
        "license": STR,
    },
    required=("source_name",),
)

MONEY = obj(
    {
        "amount": NUM,
        "currency": STR,
        "basis": STR,
        "as_of": NULLABLE_DATE_TIME,
        "low": NUM,
        "high": NUM,
        "estimated": BOOL,
        "method": STR,
        "source_ids": STRS,
    },
    required=("amount", "currency"),
)

MEASUREMENT = obj(
    {
        "value": JSON_VALUE,
        "unit": STR,
        "datatype": STR,
        "low": NUM,
        "high": NUM,
        "uncertainty": NUM,
        "precision": STR,
        "method": STR,
        "instrument_id": STR,
    },
    required=("value",),
)

STATUS_CHANGE = obj(
    {
        "status": STR,
        "changed_at": NULLABLE_DATE_TIME,
        "changed_by": STR,
        "reason": STR,
        "source_ids": STRS,
    },
    required=("status",),
)

ROLE_ASSIGNMENT = obj(
    {
        "subject_id": STR,
        "role": STR,
        "organization_id": STR,
        "context_id": STR,
        "title": STR,
        "department": STR,
        "start_at": NULLABLE_DATE_TIME,
        "end_at": NULLABLE_DATE_TIME,
        "current": BOOL,
        "source_ids": STRS,
        "confidence": SCORE,
    },
    required=("role",),
)

FACET = obj(
    {
        "facet_type": STR,
        "schema": STR,
        "version": STR,
        "properties": JSON_MAP,
        "source_ids": STRS,
        "evidence_ids": STRS,
        "confidence": SCORE,
    },
    required=("facet_type", "properties"),
)

ACTION = obj(
    {
        "action_type": STR,
        "actor_ids": STRS,
        "object_ids": STRS,
        "instrument_ids": STRS,
        "started_at": NULLABLE_DATE_TIME,
        "completed_at": NULLABLE_DATE_TIME,
        "status": STR,
        "result_ids": STRS,
        "parameters": JSON_MAP,
        "source_ids": STRS,
    },
    required=("action_type",),
)

NETWORK_SERVICE = obj(
    {
        "service_id": STR,
        "name": STR,
        "transport": STR,
        "protocol": STR,
        "port": INT,
        "product": STR,
        "version": STR,
        "banner": STR,
        "tls": BOOL,
        "certificate_ids": STRS,
        "first_seen": NULLABLE_DATE_TIME,
        "last_seen": NULLABLE_DATE_TIME,
        "source_ids": STRS,
    },
    required=("port",),
)

NETWORK_INTERFACE = obj(
    {
        "name": STR,
        "mac": STR,
        "ipv4": STRS,
        "ipv6": STRS,
        "network_ids": STRS,
        "vlan": INT,
        "mtu": INT,
        "status": STR,
    }
)

CERTIFICATE = obj(
    {
        "fingerprint": STR,
        "serial_number": STR,
        "subject": STR,
        "issuer": STR,
        "subject_alt_names": STRS,
        "not_before": NULLABLE_DATE_TIME,
        "not_after": NULLABLE_DATE_TIME,
        "signature_algorithm": STR,
        "public_key_algorithm": STR,
        "pem_hash": STR,
        "revoked": BOOL,
        "source_ids": STRS,
    },
    required=("fingerprint",),
)

DNS_RECORD = obj(
    {
        "name": STR,
        "record_type": STR,
        "value": STR,
        "ttl": INT,
        "priority": INT,
        "observed_at": NULLABLE_DATE_TIME,
        "resolver": STR,
        "source_ids": STRS,
    },
    required=("record_type", "value"),
)

HTTP_EXCHANGE = obj(
    {
        "method": STR,
        "request_url": STR,
        "request_headers": {"type": "object", "additionalProperties": STR},
        "request_body_hash": STR,
        "status_code": INT,
        "response_headers": {"type": "object", "additionalProperties": STR},
        "response_body_hash": STR,
        "content_type": STR,
        "started_at": NULLABLE_DATE_TIME,
        "completed_at": NULLABLE_DATE_TIME,
        "redirect_location": STR,
        "source_ids": STRS,
    }
)

MESSAGE_REACTION = obj(
    {
        "reaction": STR,
        "actor_id": STR,
        "count": INT,
        "reacted_at": NULLABLE_DATE_TIME,
        "removed": BOOL,
    },
    required=("reaction",),
)

CONTRACT_MODIFICATION = obj(
    {
        "modification_id": STR,
        "number": STR,
        "effective_at": NULLABLE_DATE_TIME,
        "signed_at": NULLABLE_DATE_TIME,
        "description": STR,
        "change_type": STR,
        "amount_change": MONEY,
        "new_end_at": NULLABLE_DATE_TIME,
        "source_ids": STRS,
    },
    required=("modification_id",),
)

DOCKET_ENTRY = obj(
    {
        "entry_number": STR,
        "filed_at": NULLABLE_DATE_TIME,
        "entry_type": STR,
        "title": STR,
        "description": STR,
        "document_ids": STRS,
        "party_ids": STRS,
        "source_ids": STRS,
    },
    required=("entry_number",),
)

RESEARCH_FINDING = obj(
    {
        "finding_id": STR,
        "statement": STR,
        "finding_type": STR,
        "subject_ids": STRS,
        "supporting_ids": STRS,
        "contradicting_ids": STRS,
        "confidence": SCORE,
        "verification_status": STR,
        "open_questions": STRS,
        "notes": STR,
    },
    required=("statement",),
)

MANIFEST_FILE = obj(
    {
        "path": STR,
        "media_type": STR,
        "size_bytes": INT,
        "record_count": INT,
        "content_hash": STR,
        "hash_algorithm": STR,
        "schema_revision": STR,
        "generated_at": NULLABLE_DATE_TIME,
    },
    required=("path", "content_hash"),
)

QUERY_SPEC = obj(
    {
        "query": STR,
        "language": STR,
        "source": STR,
        "parameters": JSON_MAP,
        "expected_dtypes": STRS,
        "required": BOOL,
        "status": STR,
        "result_ids": STRS,
    },
    required=("query",),
)

COMMON_DATA_FIELDS: dict[str, dict[str, Any]] = {
    "canonical_key": STR,
    "display_label": STR,
    "description": STR,
    "status": STR,
    "status_history": array(STATUS_CHANGE),
    "reference_ids": STRS,
    "source_record_ids": STRS,
    "evidence_record_ids": STRS,
    "object_marking_ids": STRS,
    "external_references": array(EXTERNAL_REFERENCE),
    "role_assignments": array(ROLE_ASSIGNMENT),
    "facets": array(FACET),
    "valid_from": NULLABLE_DATE_TIME,
    "valid_to": NULLABLE_DATE_TIME,
    "supersedes_ids": STRS,
    "superseded_by_ids": STRS,
    "attributes": JSON_MAP,
}

FIELD_EXPANSIONS: dict[str, dict[str, Any]] = {
    "document": {
        "document_kind": STR,
        "body": STR,
        "format": STR,
        "author_ids": STRS,
        "publisher_id": STR,
        "section_ids": STRS,
        "published_at": NULLABLE_DATE_TIME,
        "revision_label": STR,
    },
    "entity": {
        "entity_class": STR,
        "canonical_name": STR,
        "same_as_ids": STRS,
        "duplicate_candidate_ids": STRS,
        "identity_confidence": SCORE,
        "identity_keys": array(_spec.IDENTIFIER),
    },
    "person": {
        "canonical_name": STR,
        "name_parts": JSON_MAP,
        "birth_date_precision": STR,
        "birth_location_id": STR,
        "residence_ids": STRS,
        "employment_ids": STRS,
        "membership_ids": STRS,
        "public_office_ids": STRS,
        "ownership_ids": STRS,
        "campaign_finance_ids": STRS,
        "legal_case_ids": STRS,
        "biography_source_ids": STRS,
        "same_as_ids": STRS,
    },
    "org": {
        "legal_form": STR,
        "incorporated_at": NULLABLE_DATE_TIME,
        "incorporation_location_id": STR,
        "registration_ids": array(_spec.IDENTIFIER),
        "headquarters_id": STR,
        "office_location_ids": STRS,
        "leadership_role_ids": STRS,
        "governance_document_ids": STRS,
        "filing_ids": STRS,
        "contract_ids": STRS,
        "grant_ids": STRS,
        "lobbying_filing_ids": STRS,
        "campaign_finance_ids": STRS,
        "financial_observation_ids": STRS,
        "same_as_ids": STRS,
    },
    "relation": {
        "statement_id": STR,
        "predicate_id": STR,
        "predicate_namespace": STR,
        "subject_role": STR,
        "object_role": STR,
        "subject_dtype": STR,
        "object_dtype": STR,
        "asserted_by_ids": STRS,
        "supporting_evidence_ids": STRS,
        "contradicting_evidence_ids": STRS,
        "negated": BOOL,
        "symmetric": BOOL,
        "transitive": BOOL,
        "qualifier_records": array(FACET),
    },
    "target": {
        "target_ids": STRS,
        "root_target_id": STR,
        "parent_target_id": STR,
        "depends_on_target_ids": STRS,
        "query_plan": array(QUERY_SPEC),
        "completion_criteria": STRS,
        "stop_conditions": STRS,
        "deliverables": STRS,
        "result_ids": STRS,
        "attempt_count": INT,
        "last_run_at": NULLABLE_DATE_TIME,
    },
    "investigation-target": {
        "target_ids": STRS,
        "root_target_id": STR,
        "parent_target_id": STR,
        "depends_on_target_ids": STRS,
        "query_plan": array(QUERY_SPEC),
        "completion_criteria": STRS,
        "stop_conditions": STRS,
        "deliverables": STRS,
        "result_ids": STRS,
        "attempt_count": INT,
        "last_run_at": NULLABLE_DATE_TIME,
    },
    "domain": {
        "unicode_domain": STR,
        "punycode_domain": STR,
        "tld": STR,
        "registrar_id": STR,
        "registrant_ids": STRS,
        "dns_record_entries": array(DNS_RECORD),
        "certificate_ids": STRS,
        "url_ids": STRS,
        "mail_exchange_hosts": STRS,
        "zone_hash": STR,
    },
    "network": {
        "network_type": STR,
        "prefixes": STRS,
        "allocation_id": STR,
        "registrant_id": STR,
        "contact_ids": STRS,
        "routing_policy": STRS,
        "bgp_observation_ids": STRS,
        "announced_by_asns": array(INT),
        "rpki_status": STR,
    },
    "host": {
        "host_type": STR,
        "interface_records": array(NETWORK_INTERFACE),
        "service_records": array(NETWORK_SERVICE),
        "certificate_records": array(CERTIFICATE),
        "software_ids": STRS,
        "cloud_account_ids": STRS,
        "virtualization_type": STR,
        "parent_host_id": STR,
        "observed_by_ids": STRS,
    },
    "url": {
        "canonical_url": STR,
        "final_url": STR,
        "parent_url_id": STR,
        "discovered_from_ids": STRS,
        "http_exchanges": array(HTTP_EXCHANGE),
        "archive_ids": STRS,
        "screenshot_ids": STRS,
        "content_file_ids": STRS,
        "crawl_depth": INT,
        "robots_allowed": BOOL,
    },
    "geo": {
        "geometry_type": STR,
        "coordinates": array(NUM),
        "geometry": JSON_MAP,
        "feature_type": STR,
        "accuracy_meters": NUM,
        "source_coordinate_system": STR,
        "address_ids": STRS,
        "contains_ids": STRS,
        "contained_by_ids": STRS,
    },
    "address": {
        "formatted": STR,
        "address_type": STR,
        "building": STR,
        "unit": STR,
        "district": STR,
        "administrative_areas": STRS,
        "geometry": JSON_MAP,
        "occupant_ids": STRS,
        "valid_from": NULLABLE_DATE_TIME,
        "valid_to": NULLABLE_DATE_TIME,
    },
    "location": {
        "geometry_type": STR,
        "coordinates": array(NUM),
        "geometry": JSON_MAP,
        "feature_type": STR,
        "accuracy_meters": NUM,
        "address_ids": STRS,
        "contains_ids": STRS,
        "contained_by_ids": STRS,
        "jurisdiction_ids": STRS,
    },
    "phone": {
        "normalized_number": STR,
        "e164": STR,
        "subscriber_id": STR,
        "provider_id": STR,
        "usage_types": STRS,
        "porting_history": array(STATUS_CHANGE),
        "account_ids": STRS,
    },
    "email": {
        "normalized_address": STR,
        "local_part": STR,
        "domain_id": STR,
        "owner_ids": STRS,
        "provider_id": STR,
        "usage_types": STRS,
        "account_ids": STRS,
        "deliverability_status": STR,
    },
    "email-message": {
        "sender_refs": array(REFERENCE),
        "recipient_refs": array(REFERENCE),
        "reply_to_refs": array(REFERENCE),
        "message_id_header": STR,
        "in_reply_to_ids": STRS,
        "reference_message_ids": STRS,
        "body_file_ids": STRS,
        "attachment_ids": STRS,
        "authentication_results": JSON_MAP,
        "transport_hops": array(FACET),
    },
    "user": {
        "account_id": STR,
        "platform_id": STR,
        "profile_url": STR,
        "created_at": NULLABLE_DATE_TIME,
        "last_active_at": NULLABLE_DATE_TIME,
        "owner_ids": STRS,
        "follower_count": INT,
        "following_count": INT,
        "post_count": INT,
        "account_status": STR,
        "verified_type": STR,
    },
    "message": {
        "author_refs": array(REFERENCE),
        "recipient_refs": array(REFERENCE),
        "conversation_id": STR,
        "parent_message_id": STR,
        "quoted_message_id": STR,
        "reaction_records": array(MESSAGE_REACTION),
        "attachment_ids": STRS,
        "capture_ids": STRS,
        "content_hash": STR,
    },
    "social-media-post": {
        "author_refs": array(REFERENCE),
        "conversation_id": STR,
        "parent_post_id": STR,
        "quoted_post_id": STR,
        "reaction_records": array(MESSAGE_REACTION),
        "attachment_ids": STRS,
        "capture_ids": STRS,
        "engagement_observation_ids": STRS,
        "content_hash": STR,
    },
    "breach": {
        "affected_org_ids": STRS,
        "affected_product_ids": STRS,
        "record_count_estimate": INT,
        "record_count_basis": STR,
        "data_class_records": array(FACET),
        "disclosure_source_ids": STRS,
        "notification_ids": STRS,
        "severity_score": SCORE,
        "incident_ids": STRS,
    },
    "product": {
        "supplier_ids": STRS,
        "version_ids": STRS,
        "component_ids": STRS,
        "dependency_ids": STRS,
        "deployment_ids": STRS,
        "sbom_file_ids": STRS,
        "support_end_at": NULLABLE_DATE_TIME,
        "pricing_records": array(MONEY),
        "security_advisory_ids": STRS,
    },
    "event": {
        "event_type_id": STR,
        "parent_event_id": STR,
        "child_event_ids": STRS,
        "participant_roles": array(ROLE_ASSIGNMENT),
        "action_records": array(ACTION),
        "source_event_ids": STRS,
        "recurrence_rule": STR,
        "result_ids": STRS,
        "claim_ids": STRS,
    },
    "meeting": {
        "meeting_type": STR,
        "chair_ids": STRS,
        "attendee_roles": array(ROLE_ASSIGNMENT),
        "agenda_item_ids": STRS,
        "minute_file_ids": STRS,
        "decision_ids": STRS,
        "action_item_ids": STRS,
        "parent_meeting_id": STR,
        "recurrence_rule": STR,
    },
    "claim": {
        "proposition": STR,
        "subject_refs": array(REFERENCE),
        "object_refs": array(REFERENCE),
        "supporting_source_ids": STRS,
        "review_ids": STRS,
        "truth_status": STR,
        "verification_method": STRS,
        "derived_from_claim_ids": STRS,
        "scope": STR,
        "valid_from": NULLABLE_DATE_TIME,
        "valid_to": NULLABLE_DATE_TIME,
    },
    "analysis": {
        "hypotheses": STRS,
        "method_ids": STRS,
        "claim_ids": STRS,
        "finding_records": array(RESEARCH_FINDING),
        "logic": STR,
        "reasoning_artifact_ids": STRS,
        "uncertainty_sources": STRS,
        "dependency_ids": STRS,
        "review_ids": STRS,
        "output_ids": STRS,
    },
    "concept": {
        "concept_id": STR,
        "vocabulary": STR,
        "namespace": STR,
        "version": STR,
        "preferred_label": STR,
        "synonyms": STRS,
        "definition_source_ids": STRS,
        "mapping_ids": STRS,
    },
    "observation": {
        "subject_refs": array(REFERENCE),
        "observed_property": STR,
        "measurement": MEASUREMENT,
        "raw_value": JSON_VALUE,
        "action_id": STR,
        "observer_refs": array(REFERENCE),
        "source_record_ids": STRS,
        "evidence_record_ids": STRS,
        "uncertainty": NUM,
    },
    "financial-observation": {
        "transaction_id": STR,
        "payer_ids": STRS,
        "payee_ids": STRS,
        "account_ids": STRS,
        "amount_record": MONEY,
        "amount_basis": STR,
        "reporting_standard": STR,
        "filing_ids": STRS,
        "source_transaction_ids": STRS,
        "memoed": BOOL,
        "refunded": BOOL,
    },
    "contract": {
        "parent_award_id": STR,
        "prime_award_id": STR,
        "party_roles": array(ROLE_ASSIGNMENT),
        "funding_records": array(MONEY),
        "line_items": array(FACET),
        "modification_records": array(CONTRACT_MODIFICATION),
        "clause_ids": STRS,
        "deliverable_ids": STRS,
        "performance_location_ids": STRS,
        "source_system_ids": array(_spec.IDENTIFIER),
    },
    "procurement": {
        "procurement_stage": STR,
        "notice_id": STR,
        "parent_award_id": STR,
        "party_roles": array(ROLE_ASSIGNMENT),
        "funding_records": array(MONEY),
        "line_items": array(FACET),
        "modification_records": array(CONTRACT_MODIFICATION),
        "competition_exceptions": STRS,
        "evaluation_criteria": STRS,
        "source_system_ids": array(_spec.IDENTIFIER),
    },
    "grant": {
        "award_number": STR,
        "prime_recipient_id": STR,
        "subrecipient_ids": STRS,
        "program_id": STR,
        "funding_records": array(MONEY),
        "assistance_listing_ids": STRS,
        "matching_amount": MONEY,
        "performance_location_ids": STRS,
        "objective_ids": STRS,
        "report_ids": STRS,
    },
    "lobbying-filing": {
        "filing_system": STR,
        "registrant_refs": array(REFERENCE),
        "client_refs": array(REFERENCE),
        "lobbyist_refs": array(REFERENCE),
        "covered_official_ids": STRS,
        "issue_codes": STRS,
        "amount_records": array(MONEY),
        "foreign_entity_ids": STRS,
        "prior_filing_id": STR,
        "amends_filing_id": STR,
        "source_filing_url": STR,
    },
    "campaign-finance": {
        "transaction_id": STR,
        "committee_ids": STRS,
        "donor_refs": array(REFERENCE),
        "recipient_refs": array(REFERENCE),
        "amount_record": MONEY,
        "transaction_date": NULLABLE_DATE_TIME,
        "memoed": BOOL,
        "memo_text": STR,
        "refund_of_id": STR,
        "aggregate_amount": MONEY,
        "employer": STR,
        "occupation": STR,
        "source_system_ids": array(_spec.IDENTIFIER),
    },
    "legal-case": {
        "court_id": STR,
        "docket_id": STR,
        "party_roles": array(ROLE_ASSIGNMENT),
        "related_case_ids": STRS,
        "docket_entry_records": array(DOCKET_ENTRY),
        "motion_ids": STRS,
        "order_ids": STRS,
        "opinion_ids": STRS,
        "appeal_case_ids": STRS,
        "disposition": STR,
        "precedential_status": STR,
    },
    "policy": {
        "policy_version": STR,
        "parent_policy_id": STR,
        "authority_ids": STRS,
        "implementation_ids": STRS,
        "text_file_ids": STRS,
        "section_ids": STRS,
        "adopted_at": NULLABLE_DATE_TIME,
        "repealed_at": NULLABLE_DATE_TIME,
        "superseded_by_id": STR,
        "compliance_requirement_ids": STRS,
    },
    "education": {
        "education_type": STR,
        "credential_id": STR,
        "program_id": STR,
        "attendance_status": STR,
        "awarded_at": NULLABLE_DATE_TIME,
        "thesis_title": STR,
        "advisor_ids": STRS,
        "source_record_ids": STRS,
    },
    "employment": {
        "role_ids": STRS,
        "reports_to_ids": STRS,
        "appointment_type": STR,
        "appointed_by_ids": STRS,
        "compensation_records": array(MONEY),
        "responsibilities": STRS,
        "termination_reason": STR,
        "source_record_ids": STRS,
    },
    "ownership": {
        "owner_refs": array(REFERENCE),
        "owned_refs": array(REFERENCE),
        "ownership_instrument": STR,
        "percentage_basis": STR,
        "voting_percentage": NUM,
        "economic_percentage": NUM,
        "value_record": MONEY,
        "acquisition_event_id": STR,
        "disposal_event_id": STR,
        "source_record_ids": STRS,
    },
    "asset": {
        "asset_class": STR,
        "custodian_ids": STRS,
        "beneficial_owner_ids": STRS,
        "identifier_records": array(_spec.IDENTIFIER),
        "valuation_records": array(MONEY),
        "acquired_at": NULLABLE_DATE_TIME,
        "disposed_at": NULLABLE_DATE_TIME,
        "acquisition_event_id": STR,
        "disposal_event_id": STR,
        "component_ids": STRS,
    },
    "media": {
        "source_file_id": STR,
        "derivative_file_ids": STRS,
        "creator_refs": array(REFERENCE),
        "capture_action_id": STR,
        "width": INT,
        "height": INT,
        "codec": STR,
        "language": STR,
        "ocr_text": STR,
        "transcript_file_id": STR,
        "hashes": {"type": "object", "additionalProperties": STR},
    },
    "file": {
        "storage_id": STR,
        "original_name": STR,
        "extension": STR,
        "magic_type": STR,
        "hashes": {"type": "object", "additionalProperties": STR},
        "parent_file_id": STR,
        "container_file_id": STR,
        "derived_file_ids": STRS,
        "capture_action_id": STR,
        "extracted_metadata": JSON_MAP,
        "quarantined": BOOL,
    },
    "source": {
        "source_type_id": STR,
        "publisher_id": STR,
        "author_ids": STRS,
        "external_references": array(EXTERNAL_REFERENCE),
        "capture_action_id": STR,
        "original_file_ids": STRS,
        "archive_ids": STRS,
        "terms_of_use": STR,
        "access_restrictions": STRS,
        "supersedes_source_ids": STRS,
    },
    "evidence-record": {
        "subject_ids": STRS,
        "claim_ids": STRS,
        "source_record_ids": STRS,
        "exact_content": STR,
        "normalized_content": STR,
        "extraction_method": STR,
        "capture_action_id": STR,
        "custody_actions": array(ACTION),
        "hashes": {"type": "object", "additionalProperties": STR},
        "admissibility_status": STR,
    },
    "research-pass": {
        "parent_pass_id": STR,
        "child_pass_ids": STRS,
        "target_ids": STRS,
        "query_plan": array(QUERY_SPEC),
        "action_records": array(ACTION),
        "finding_records": array(RESEARCH_FINDING),
        "claim_ids": STRS,
        "output_ids": STRS,
        "metrics": JSON_MAP,
        "termination_reason": STR,
        "schema_revision": STR,
    },
    "actor-manifest": {
        "actor_id": STR,
        "actor_type": STR,
        "implementation": STR,
        "entrypoint": STR,
        "input_dtypes": STRS,
        "output_dtypes": STRS,
        "dependencies": STRS,
        "routing_keys": STRS,
        "configuration_schema": JSON_MAP,
        "capabilities": STRS,
        "healthcheck": JSON_MAP,
        "schema_revision": STR,
    },
    "dataset-manifest": {
        "dataset_id": STR,
        "dataset_version": STR,
        "profile": STR,
        "profile_version": STR,
        "schema_revision": STR,
        "document_versions": array(REFERENCE),
        "file_records": array(MANIFEST_FILE),
        "source_dataset_ids": STRS,
        "sync_cursor": STR,
        "sync_status": STR,
        "validated_at": NULLABLE_DATE_TIME,
    },
    "alert": {
        "rule_id": STR,
        "trigger_event_id": STR,
        "related_alert_ids": STRS,
        "first_triggered_at": NULLABLE_DATE_TIME,
        "last_triggered_at": NULLABLE_DATE_TIME,
        "occurrence_count": INT,
        "acknowledgement_actions": array(ACTION),
        "suppressed_until": NULLABLE_DATE_TIME,
        "resolved_at": NULLABLE_DATE_TIME,
        "resolution": STR,
    },
    "task": {
        "parent_task_id": STR,
        "dependency_task_ids": STRS,
        "actor_ids": STRS,
        "skill_ids": STRS,
        "tool_ids": STRS,
        "input_ids": STRS,
        "attempt_ids": STRS,
        "schedule": STR,
        "started_at": NULLABLE_DATE_TIME,
        "result_summary": STR,
        "error_ids": STRS,
    },
}


def _merge_fields(target: dict[str, Any], additions: dict[str, Any]) -> None:
    for name, schema in additions.items():
        target.setdefault(name, deepcopy(schema))


def apply_v09_expansion() -> None:
    if getattr(_spec, "_V09_EXPANSION_APPLIED", False):
        return

    for fields in _spec.TYPE_FIELDS.values():
        _merge_fields(fields, COMMON_DATA_FIELDS)

    for dtype, fields in FIELD_EXPANSIONS.items():
        if dtype not in _spec.TYPE_FIELDS:
            raise RuntimeError(f"v0.9 expansion references unknown dtype: {dtype}")
        _merge_fields(_spec.TYPE_FIELDS[dtype], fields)

    _merge_fields(
        _spec.COMMON_PROPERTIES,
        {
            "schema_revision": {"const": SCHEMA_REVISION},
            "schema_uri": {"const": _spec.SCHEMA_ID},
            "profile": STR,
            "profile_version": STR,
            "content_hash": STR,
            "hash_algorithm": STR,
            "revoked": BOOL,
            "deleted": BOOL,
            "tombstone_reason": STR,
            "created_by_ref": STR,
            "modified_by_ref": STR,
            "object_marking_ids": STRS,
        },
    )

    _merge_fields(
        _spec.PROVENANCE["properties"],
        {
            "activity_id": STR,
            "agent_ids": STRS,
            "used_ids": STRS,
            "generated_by": STR,
            "was_derived_from": STRS,
            "was_attributed_to": STRS,
            "was_associated_with": STRS,
            "plan_id": STR,
            "action_records": array(ACTION),
        },
    )

    _merge_fields(
        _spec.LINEAGE["properties"],
        {
            "content_hash": STR,
            "schema_revision": STR,
            "revision_parent_id": STR,
            "revision_child_ids": STRS,
            "tombstone_of": STR,
        },
    )

    _merge_fields(
        _spec.VERIFICATION["properties"],
        {
            "review_ids": STRS,
            "verification_action_ids": STRS,
            "policy_id": STR,
            "schema_revision": STR,
        },
    )

    _spec.SCHEMA_REVISION = SCHEMA_REVISION
    _spec.SCHEMA_PROFILE = SCHEMA_PROFILE
    _spec.SCHEMA_PROFILE_VERSION = SCHEMA_PROFILE_VERSION

    original_document_schema = _spec.document_schema

    def expanded_document_schema(dtype: str | None = None) -> dict[str, Any]:
        schema = original_document_schema(dtype)
        schema["$comment"] = (
            "StarIntel v0.9 additive field expansion. Existing v0.9 documents remain valid; "
            "schema_revision identifies the exact contract used for newly emitted records."
        )
        schema["x-starintel-schema-revision"] = SCHEMA_REVISION
        schema["x-starintel-profile"] = SCHEMA_PROFILE
        schema["x-starintel-profile-version"] = SCHEMA_PROFILE_VERSION
        schema["$defs"] = {
            "reference": deepcopy(REFERENCE),
            "externalReference": deepcopy(EXTERNAL_REFERENCE),
            "money": deepcopy(MONEY),
            "measurement": deepcopy(MEASUREMENT),
            "statusChange": deepcopy(STATUS_CHANGE),
            "roleAssignment": deepcopy(ROLE_ASSIGNMENT),
            "facet": deepcopy(FACET),
            "action": deepcopy(ACTION),
            "networkService": deepcopy(NETWORK_SERVICE),
            "certificate": deepcopy(CERTIFICATE),
            "dnsRecord": deepcopy(DNS_RECORD),
            "httpExchange": deepcopy(HTTP_EXCHANGE),
            "contractModification": deepcopy(CONTRACT_MODIFICATION),
            "docketEntry": deepcopy(DOCKET_ENTRY),
            "researchFinding": deepcopy(RESEARCH_FINDING),
            "manifestFile": deepcopy(MANIFEST_FILE),
            "querySpec": deepcopy(QUERY_SPEC),
        }
        return schema

    _spec.document_schema = expanded_document_schema
    _spec._V09_EXPANSION_APPLIED = True


apply_v09_expansion()
