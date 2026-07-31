from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Sequence

from starintel_doc.model import Document, stable_id, utc_now

from .constants import BASE_URL, DATASET, TERMS_URL
from .parser import Profile
from .utils import content_digest


def identifier_records(profile: Profile) -> list[dict[str, Any]]:
    identifiers: list[dict[str, Any]] = [
        {"scheme": "influencewatch-profile", "value": profile.url, "issuer": "InfluenceWatch", "canonical": True, "url": profile.url}
    ]
    for label in ("tax id", "fec id", "fec number"):
        if value := profile.fields.get(label):
            identifiers.append({"scheme": label.replace(" ", "-"), "value": value, "issuer": "InfluenceWatch"})
    return identifiers


def source_record(profile: Profile) -> dict[str, Any]:
    return {
        "kind": "webpage",
        "title": profile.title,
        "publisher": "InfluenceWatch",
        "url": profile.url,
        "retrieved_at": profile.collected_at,
        "access_method": "authorized HTML retrieval",
        "content_hash": profile.content_hash,
        "hash_algorithm": "sha256",
        "license": "Use subject to InfluenceWatch Terms of Use and any written authorization",
        "metadata": {"terms_url": TERMS_URL, "profile_type": profile.profile_type},
    }


def profile_data(profile: Profile) -> dict[str, Any]:
    website = profile.fields.get("website", "")
    if profile.dtype == "person":
        data: dict[str, Any] = {"name": profile.title, "full_name": profile.title, "bio": profile.text or profile.summary}
        if occupation := profile.fields.get("occupation"):
            data["occupations"] = [item.strip() for item in occupation.split(",") if item.strip()]
    elif profile.dtype == "org":
        data = {
            "name": profile.title,
            "legal_name": profile.title,
            "org_type": profile.fields.get("type") or profile.profile_type.replace("-", " "),
            "description": profile.text or profile.summary,
        }
        if tax_id := profile.fields.get("tax id"):
            data["tax_id"] = tax_id
        if location := profile.fields.get("location"):
            data["headquarters"] = location
        if issue_areas := profile.fields.get("issue areas"):
            data["sectors"] = [item.strip() for item in issue_areas.split(",") if item.strip()]
    else:
        data = {"name": profile.title, "display_name": profile.title, "etype": profile.profile_type, "description": profile.text or profile.summary}
    if website:
        data["website"] = website
    if profile.image_url:
        data["image_url"] = profile.image_url
    return data


def profile_document(profile: Profile, *, site_source_id: str) -> dict[str, Any]:
    temporal: dict[str, Any] = {"collected_at": profile.collected_at}
    if profile.published_at:
        temporal["published_at"] = profile.published_at
    if profile.modified_at:
        temporal["modified_at"] = profile.modified_at
    tags = ["influencewatch", "profile", profile.profile_type]
    if issue_areas := profile.fields.get("issue areas"):
        tags.extend(item.strip().lower().replace(" ", "-") for item in issue_areas.split(",") if item.strip())
    return Document.create(
        profile.dtype,
        DATASET,
        doc_id=stable_id(profile.dtype, "influencewatch", profile.url),
        title=profile.title,
        summary=profile.summary,
        description=profile.text,
        data=profile_data(profile),
        tags=sorted(set(tags)),
        identifiers=identifier_records(profile),
        sources=[source_record(profile)],
        evidence=[{
            "source_url": profile.url,
            "kind": "source-profile",
            "role": "publisher-attributed",
            "claim": f"InfluenceWatch publishes a {profile.profile_type} profile titled {profile.title}.",
            "excerpt": (profile.summary or profile.text)[:500],
            "collected_at": profile.collected_at,
            "content_hash": profile.content_hash,
            "hash_algorithm": "sha256",
            "status": "source-recorded",
        }],
        temporal=temporal,
        provenance={
            "collector": "starintel-gpt-auto-dig",
            "collector_type": "permission-gated-web-importer",
            "method": "authorized public webpage import",
            "pipeline": "scripts/import_influencewatch.py",
            "imported_from": profile.url,
            "original_id": profile.url,
            "metadata": {"terms_url": TERMS_URL, "profile_type": profile.profile_type},
        },
        assessment={"caveats": [
            "InfluenceWatch is a secondary source; profile claims are publisher-attributed until independently corroborated.",
            "Ideological alignment labels and characterizations remain attributed to InfluenceWatch.",
        ]},
        verification={"status": "source-recorded", "verified": False, "checks": ["Content hash recorded", "Canonical profile URL recorded"]},
        handling={"visibility": "public", "sensitive": False, "pii": profile.dtype == "person", "license": "Source terms and authorization apply"},
        related_ids=[site_source_id],
        extensions={"influencewatch": {
            "profile_type": profile.profile_type,
            "at_a_glance": profile.fields,
            "internal_profile_links": [{"label": label, "url": url} for label, url in profile.links],
        }},
    ).to_dict()


def site_source_document(collected_at: str) -> dict[str, Any]:
    return Document.create(
        "source",
        DATASET,
        doc_id=stable_id("source", "influencewatch", BASE_URL),
        title="InfluenceWatch",
        summary="Source website for InfluenceWatch public-policy influence profiles.",
        data={
            "kind": "website",
            "title": "InfluenceWatch",
            "publisher": "InfluenceWatch",
            "url": BASE_URL,
            "accessed_at": collected_at,
            "access_method": "permission-gated importer",
            "license": "Systematic collection requires express written consent under the Terms of Use effective May 1, 2026",
            "notes": f"Terms: {TERMS_URL}",
        },
        sources=[{"kind": "terms-of-use", "title": "InfluenceWatch Terms of Use", "publisher": "InfluenceWatch", "url": TERMS_URL, "retrieved_at": collected_at}],
        provenance={"collector": "starintel-gpt-auto-dig", "pipeline": "scripts/import_influencewatch.py"},
        verification={"status": "source-recorded", "verified": False},
        handling={"visibility": "public", "sensitive": False, "pii": False},
    ).to_dict()


def relation_documents(profiles: Sequence[Profile], documents: dict[str, dict[str, Any]], *, site_source_id: str) -> list[dict[str, Any]]:
    relations: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for profile in profiles:
        subject = documents[profile.url]["_id"]
        for label, target_url in profile.links:
            if (profile.url, target_url) in seen:
                continue
            seen.add((profile.url, target_url))
            if target_document := documents.get(target_url):
                target: str | dict[str, Any] = target_document["_id"]
                target_identity = target_document["_id"]
            else:
                target = {"external_id": target_url, "label": label or target_url, "unresolved": True, "metadata": {"source": "InfluenceWatch internal profile link"}}
                target_identity = target_url
            relations.append(Document.create(
                "relation",
                DATASET,
                doc_id=stable_id("relation", "influencewatch", subject, "references_profile", target_identity),
                title=f"{profile.title} references {label or target_url}",
                summary="Internal profile link published on an InfluenceWatch profile.",
                data={
                    "subject": subject,
                    "predicate": "references_profile",
                    "object": target,
                    "directed": True,
                    "relation_type": "influencewatch-profile-link",
                    "qualifiers": {"source_url": profile.url, "target_url": target_url, "link_label": label},
                },
                tags=["influencewatch", "relationship", "publisher-attributed"],
                sources=[source_record(profile)],
                provenance={"collector": "starintel-gpt-auto-dig", "method": "authorized profile-link extraction", "pipeline": "scripts/import_influencewatch.py", "imported_from": profile.url},
                assessment={"caveats": ["The relation reflects an InfluenceWatch internal link and does not independently establish the nature of the association."]},
                verification={"status": "source-recorded", "verified": False},
                handling={"visibility": "public", "sensitive": False, "pii": False},
                related_ids=[site_source_id],
            ).to_dict())
    return relations


def manifest_document(records: Sequence[dict[str, Any]], *, output: Path, generated_at: str) -> dict[str, Any]:
    serialized = b"".join((json.dumps(record, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n").encode() for record in records)
    counts = Counter(record["dtype"] for record in records)
    return Document.create(
        "dataset-manifest",
        DATASET,
        doc_id=stable_id("dataset-manifest", DATASET),
        title="InfluenceWatch DB dataset manifest",
        summary="Manifest for permission-authorized InfluenceWatch profile records imported into Auto-Dig.",
        data={
            "manifest_type": "source-dataset",
            "name": DATASET,
            "consumer_path": "scripts/starintel.py import",
            "document_ids": [record["_id"] for record in records],
            "counts_by_dtype": dict(sorted(counts.items())),
            "record_count": len(records),
            "hash_algorithm": "sha256",
            "content_hash": content_digest(serialized),
            "files": [{"path": str(output), "format": "jsonl"}],
            "schema_versions": sorted({record["schema_version"] for record in records}),
            "generated_at": generated_at,
        },
        sources=[{"kind": "website", "title": "InfluenceWatch", "publisher": "InfluenceWatch", "url": BASE_URL}],
        provenance={"collector": "starintel-gpt-auto-dig", "pipeline": "scripts/import_influencewatch.py"},
        verification={"status": "generated", "verified": True, "checks": ["All records validated by Document.create"]},
        handling={"visibility": "public", "sensitive": False, "pii": False},
    ).to_dict()


def build_records(profiles: Sequence[Profile], *, output: Path) -> list[dict[str, Any]]:
    generated_at = utc_now()
    source = site_source_document(generated_at)
    documents = {profile.url: profile_document(profile, site_source_id=source["_id"]) for profile in profiles}
    records: list[dict[str, Any]] = [source, *documents.values()]
    records.extend(relation_documents(profiles, documents, site_source_id=source["_id"]))
    records.append(manifest_document(records, output=output, generated_at=generated_at))
    return records
