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

# Data-only field inventory. This is intentionally easy for StarLang and other
# runtimes to ingest or generate without reproducing Python model classes.
EXPANSION_FIELD_NAMES: dict[str, tuple[str, ...]] = {
    "document": tuple("document_kind body format author_ids publisher_id section_ids published_at revision_label".split()),
    "entity": tuple("entity_class canonical_name same_as_ids duplicate_candidate_ids identity_confidence identity_keys".split()),
    "person": tuple("canonical_name name_parts birth_date_precision birth_location_id residence_ids employment_ids membership_ids public_office_ids ownership_ids campaign_finance_ids legal_case_ids biography_source_ids same_as_ids".split()),
    "org": tuple("legal_form incorporated_at incorporation_location_id registration_ids headquarters_id office_location_ids leadership_role_ids governance_document_ids filing_ids contract_ids grant_ids lobbying_filing_ids campaign_finance_ids financial_observation_ids same_as_ids".split()),
    "relation": tuple("statement_id predicate_id predicate_namespace subject_role object_role subject_dtype object_dtype asserted_by_ids supporting_evidence_ids contradicting_evidence_ids negated symmetric transitive qualifier_records".split()),
    "target": tuple("target_ids root_target_id parent_target_id depends_on_target_ids query_plan completion_criteria stop_conditions deliverables result_ids attempt_count last_run_at".split()),
    "investigation-target": tuple("target_ids root_target_id parent_target_id depends_on_target_ids query_plan completion_criteria stop_conditions deliverables result_ids attempt_count last_run_at".split()),
    "domain": tuple("unicode_domain punycode_domain tld registrar_id registrant_ids dns_record_entries certificate_ids url_ids mail_exchange_hosts zone_hash".split()),
    "network": tuple("network_type prefixes allocation_id registrant_id contact_ids routing_policy bgp_observation_ids announced_by_asns rpki_status".split()),
    "host": tuple("host_type interface_records service_records certificate_records software_ids cloud_account_ids virtualization_type parent_host_id observed_by_ids".split()),
    "url": tuple("canonical_url final_url parent_url_id discovered_from_ids http_exchanges archive_ids screenshot_ids content_file_ids crawl_depth robots_allowed".split()),
    "geo": tuple("geometry_type coordinates geometry feature_type accuracy_meters source_coordinate_system address_ids contains_ids contained_by_ids".split()),
    "address": tuple("formatted address_type building unit district administrative_areas geometry occupant_ids valid_from valid_to".split()),
    "location": tuple("geometry_type coordinates geometry feature_type accuracy_meters address_ids contains_ids contained_by_ids jurisdiction_ids".split()),
    "phone": tuple("normalized_number e164 subscriber_id provider_id usage_types porting_history account_ids".split()),
    "email": tuple("normalized_address local_part domain_id owner_ids provider_id usage_types account_ids deliverability_status".split()),
    "email-message": tuple("sender_refs recipient_refs reply_to_refs message_id_header in_reply_to_ids reference_message_ids body_file_ids attachment_ids authentication_results transport_hops".split()),
    "user": tuple("account_id platform_id profile_url created_at last_active_at owner_ids follower_count following_count post_count account_status verified_type".split()),
    "message": tuple("author_refs recipient_refs conversation_id parent_message_id quoted_message_id reaction_records attachment_ids capture_ids content_hash".split()),
    "social-media-post": tuple("author_refs conversation_id parent_post_id quoted_post_id reaction_records attachment_ids capture_ids engagement_observation_ids content_hash".split()),
    "breach": tuple("affected_org_ids affected_product_ids record_count_estimate record_count_basis data_class_records disclosure_source_ids notification_ids severity_score incident_ids".split()),
    "product": tuple("supplier_ids version_ids component_ids dependency_ids deployment_ids sbom_file_ids support_end_at pricing_records security_advisory_ids".split()),
    "event": tuple("event_type_id parent_event_id child_event_ids participant_roles action_records source_event_ids recurrence_rule result_ids claim_ids".split()),
    "meeting": tuple("meeting_type chair_ids attendee_roles agenda_item_ids minute_file_ids decision_ids action_item_ids parent_meeting_id recurrence_rule".split()),
    "claim": tuple("proposition subject_refs object_refs supporting_source_ids review_ids truth_status verification_method derived_from_claim_ids scope valid_from valid_to".split()),
    "analysis": tuple("hypotheses method_ids claim_ids finding_records logic reasoning_artifact_ids uncertainty_sources dependency_ids review_ids output_ids".split()),
    "concept": tuple("concept_id vocabulary namespace version preferred_label synonyms definition_source_ids mapping_ids".split()),
    "observation": tuple("subject_refs observed_property measurement raw_value action_id observer_refs source_record_ids evidence_record_ids uncertainty".split()),
    "financial-observation": tuple("transaction_id payer_ids payee_ids account_ids amount_record amount_basis reporting_standard filing_ids source_transaction_ids memoed refunded".split()),
    "contract": tuple("parent_award_id prime_award_id party_roles funding_records line_items modification_records clause_ids deliverable_ids performance_location_ids source_system_ids".split()),
    "procurement": tuple("procurement_stage notice_id parent_award_id party_roles funding_records line_items modification_records competition_exceptions evaluation_criteria source_system_ids".split()),
    "grant": tuple("award_number prime_recipient_id subrecipient_ids program_id funding_records assistance_listing_ids matching_amount performance_location_ids objective_ids report_ids".split()),
    "lobbying-filing": tuple("filing_system registrant_refs client_refs lobbyist_refs covered_official_ids issue_codes amount_records foreign_entity_ids prior_filing_id amends_filing_id source_filing_url".split()),
    "campaign-finance": tuple("transaction_id committee_ids donor_refs recipient_refs amount_record transaction_date memoed memo_text refund_of_id aggregate_amount employer occupation source_system_ids".split()),
    "legal-case": tuple("court_id docket_id party_roles related_case_ids docket_entry_records motion_ids order_ids opinion_ids appeal_case_ids disposition precedential_status".split()),
    "policy": tuple("policy_version parent_policy_id authority_ids implementation_ids text_file_ids section_ids adopted_at repealed_at superseded_by_id compliance_requirement_ids".split()),
    "education": tuple("education_type credential_id program_id attendance_status awarded_at thesis_title advisor_ids source_record_ids".split()),
    "employment": tuple("role_ids reports_to_ids appointment_type appointed_by_ids compensation_records responsibilities termination_reason source_record_ids".split()),
    "ownership": tuple("owner_refs owned_refs ownership_instrument percentage_basis voting_percentage economic_percentage value_record acquisition_event_id disposal_event_id source_record_ids".split()),
    "asset": tuple("asset_class custodian_ids beneficial_owner_ids identifier_records valuation_records acquired_at disposed_at acquisition_event_id disposal_event_id component_ids".split()),
    "media": tuple("source_file_id derivative_file_ids creator_refs capture_action_id width height codec language ocr_text transcript_file_id hashes".split()),
    "file": tuple("storage_id original_name extension magic_type hashes parent_file_id container_file_id derived_file_ids capture_action_id extracted_metadata quarantined".split()),
    "source": tuple("source_type_id publisher_id author_ids external_references capture_action_id original_file_ids archive_ids terms_of_use access_restrictions supersedes_source_ids".split()),
    "evidence-record": tuple("subject_ids claim_ids source_record_ids exact_content normalized_content extraction_method capture_action_id custody_actions hashes admissibility_status".split()),
    "research-pass": tuple("parent_pass_id child_pass_ids target_ids query_plan action_records finding_records claim_ids output_ids metrics termination_reason schema_revision".split()),
    "actor-manifest": tuple("actor_id actor_type implementation entrypoint input_dtypes output_dtypes dependencies routing_keys configuration_schema capabilities healthcheck schema_revision".split()),
    "dataset-manifest": tuple("dataset_id dataset_version profile profile_version schema_revision document_versions file_records source_dataset_ids sync_cursor sync_status validated_at".split()),
    "alert": tuple("rule_id trigger_event_id related_alert_ids first_triggered_at last_triggered_at occurrence_count acknowledgement_actions suppressed_until resolved_at resolution".split()),
    "task": tuple("parent_task_id dependency_task_ids actor_ids skill_ids tool_ids input_ids attempt_ids schedule started_at result_summary error_ids".split()),
}

FIELD_SCHEMA_OVERRIDES: dict[str, dict[str, Any]] = {
    "identity_keys": array(_spec.IDENTIFIER),
    "registration_ids": array(_spec.IDENTIFIER),
    "source_system_ids": array(_spec.IDENTIFIER),
    "identifier_records": array(_spec.IDENTIFIER),
    "query_plan": array(QUERY_SPEC),
    "interface_records": array(NETWORK_INTERFACE),
    "service_records": array(NETWORK_SERVICE),
    "certificate_records": array(CERTIFICATE),
    "dns_record_entries": array(DNS_RECORD),
    "http_exchanges": array(HTTP_EXCHANGE),
    "sender_refs": array(REFERENCE),
    "recipient_refs": array(REFERENCE),
    "reply_to_refs": array(REFERENCE),
    "author_refs": array(REFERENCE),
    "subject_refs": array(REFERENCE),
    "object_refs": array(REFERENCE),
    "observer_refs": array(REFERENCE),
    "donor_refs": array(REFERENCE),
    "registrant_refs": array(REFERENCE),
    "client_refs": array(REFERENCE),
    "lobbyist_refs": array(REFERENCE),
    "owner_refs": array(REFERENCE),
    "owned_refs": array(REFERENCE),
    "creator_refs": array(REFERENCE),
    "document_versions": array(REFERENCE),
    "reaction_records": array(MESSAGE_REACTION),
    "qualifier_records": array(FACET),
    "data_class_records": array(FACET),
    "line_items": array(FACET),
    "transport_hops": array(FACET),
    "participant_roles": array(ROLE_ASSIGNMENT),
    "attendee_roles": array(ROLE_ASSIGNMENT),
    "party_roles": array(ROLE_ASSIGNMENT),
    "action_records": array(ACTION),
    "custody_actions": array(ACTION),
    "acknowledgement_actions": array(ACTION),
    "finding_records": array(RESEARCH_FINDING),
    "modification_records": array(CONTRACT_MODIFICATION),
    "docket_entry_records": array(DOCKET_ENTRY),
    "file_records": array(MANIFEST_FILE),
    "measurement": MEASUREMENT,
    "raw_value": JSON_VALUE,
    "amount_record": MONEY,
    "matching_amount": MONEY,
    "aggregate_amount": MONEY,
    "value_record": MONEY,
    "pricing_records": array(MONEY),
    "funding_records": array(MONEY),
    "amount_records": array(MONEY),
    "compensation_records": array(MONEY),
    "valuation_records": array(MONEY),
    "name_parts": JSON_MAP,
    "geometry": JSON_MAP,
    "authentication_results": JSON_MAP,
    "metrics": JSON_MAP,
    "configuration_schema": JSON_MAP,
    "healthcheck": JSON_MAP,
    "extracted_metadata": JSON_MAP,
    "hashes": {"type": "object", "additionalProperties": STR},
    "coordinates": array(NUM),
    "announced_by_asns": array(INT),
}

BOOL_FIELDS = {
    "negated",
    "symmetric",
    "transitive",
    "robots_allowed",
    "memoed",
    "refunded",
    "quarantined",
}

SCORE_FIELDS = {"identity_confidence", "severity_score"}
NUMBER_FIELDS = {"accuracy_meters", "uncertainty", "voting_percentage", "economic_percentage"}
INTEGER_FIELDS = {
    "attempt_count",
    "crawl_depth",
    "follower_count",
    "following_count",
    "post_count",
    "record_count_estimate",
    "width",
    "height",
    "occurrence_count",
}
JSON_FIELDS = {"raw_value"}


def _schema_for_field(name: str) -> dict[str, Any]:
    if name in FIELD_SCHEMA_OVERRIDES:
        return deepcopy(FIELD_SCHEMA_OVERRIDES[name])
    if name in BOOL_FIELDS:
        return deepcopy(BOOL)
    if name in SCORE_FIELDS:
        return deepcopy(SCORE)
    if name in NUMBER_FIELDS:
        return deepcopy(NUM)
    if name in INTEGER_FIELDS or name.endswith("_count") or name.endswith("_depth"):
        return deepcopy(INT)
    if name in JSON_FIELDS:
        return deepcopy(JSON_VALUE)
    if name.endswith("_at") or name.endswith("_date"):
        return deepcopy(NULLABLE_DATE_TIME)
    if name.endswith("_ids") or name.endswith("_sources") or name in {
        "prefixes",
        "routing_policy",
        "mail_exchange_hosts",
        "administrative_areas",
        "usage_types",
        "completion_criteria",
        "stop_conditions",
        "deliverables",
        "verification_method",
        "hypotheses",
        "uncertainty_sources",
        "synonyms",
        "competition_exceptions",
        "evaluation_criteria",
        "issue_codes",
        "responsibilities",
        "capabilities",
        "dependencies",
        "routing_keys",
        "input_dtypes",
        "output_dtypes",
        "access_restrictions",
    }:
        return deepcopy(STRS)
    return deepcopy(STR)


FIELD_EXPANSIONS: dict[str, dict[str, Any]] = {
    dtype: {name: _schema_for_field(name) for name in names}
    for dtype, names in EXPANSION_FIELD_NAMES.items()
}


def _merge_fields(target: dict[str, Any], additions: dict[str, Any]) -> None:
    for name, schema in additions.items():
        target.setdefault(name, deepcopy(schema))


def apply_v09_expansion() -> None:
    if getattr(_spec, "_V09_EXPANSION_APPLIED", False):
        return
    if set(EXPANSION_FIELD_NAMES) != set(_spec.TYPE_FIELDS):
        missing = sorted(set(_spec.TYPE_FIELDS) - set(EXPANSION_FIELD_NAMES))
        extra = sorted(set(EXPANSION_FIELD_NAMES) - set(_spec.TYPE_FIELDS))
        raise RuntimeError(f"v0.9 expansion registry mismatch: missing={missing} extra={extra}")

    for fields in _spec.TYPE_FIELDS.values():
        _merge_fields(fields, COMMON_DATA_FIELDS)
    for dtype, fields in FIELD_EXPANSIONS.items():
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
