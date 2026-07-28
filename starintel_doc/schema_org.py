from __future__ import annotations

from copy import deepcopy
from typing import Any

from .spec import (
    JSON_MAP,
    JSON_VALUE,
    STR,
    STRS,
    TYPE_FIELDS,
    array,
    document_schema as core_document_schema,
    obj,
)

SCHEMA_ORG_CONTEXT = "https://schema.org/"

DTYPE_SCHEMA_ORG_TYPES: dict[str, tuple[str, ...]] = {
    "actor-manifest": ("CreativeWork",),
    "address": ("PostalAddress",),
    "alert": ("SpecialAnnouncement",),
    "analysis": ("CreativeWork",),
    "asset": ("Thing",),
    "breach": ("Event",),
    "campaign-finance": ("CreativeWork",),
    "claim": ("Claim",),
    "concept": ("DefinedTerm",),
    "contract": ("DigitalDocument",),
    "dataset-manifest": ("Dataset",),
    "document": ("CreativeWork",),
    "domain": ("WebSite",),
    "education": ("EducationalOccupationalCredential",),
    "email": ("ContactPoint",),
    "email-message": ("Message",),
    "employment": ("OrganizationRole",),
    "entity": ("Thing",),
    "event": ("Event",),
    "evidence-record": ("CreativeWork",),
    "file": ("DigitalDocument",),
    "financial-observation": ("CreativeWork",),
    "geo": ("GeoCoordinates",),
    "grant": ("Grant",),
    "host": ("Thing",),
    "investigation-target": ("Thing",),
    "legal-case": ("CreativeWork",),
    "lobbying-filing": ("DigitalDocument",),
    "location": ("Place",),
    "media": ("MediaObject",),
    "meeting": ("Event",),
    "message": ("Message",),
    "network": ("Thing",),
    "observation": ("CreativeWork",),
    "org": ("Organization",),
    "ownership": ("Role",),
    "person": ("Person",),
    "phone": ("ContactPoint",),
    "policy": ("CreativeWork",),
    "procurement": ("DigitalDocument",),
    "product": ("Product",),
    "relation": ("Role",),
    "research-pass": ("CreativeWork",),
    "research-node": ("CreativeWork",),
    "social-media-post": ("SocialMediaPosting",),
    "source": ("CreativeWork",),
    "target": ("Thing",),
    "task": ("Action",),
    "url": ("WebPage",),
    "user": ("Person",),
}

STRING_OR_STRINGS = {"anyOf": [STR, STRS]}

SCHEMA_ORG_IDENTIFIER = obj(
    {
        "@type": STR,
        "propertyID": STR,
        "value": JSON_VALUE,
        "url": STR,
        "name": STR,
        "description": STR,
    },
    required=("value",),
)

SCHEMA_ORG_REFERENCE = obj(
    {
        "@id": STR,
        "@type": STRING_OR_STRINGS,
        "name": STR,
        "description": STR,
        "url": STR,
        "sameAs": STRING_OR_STRINGS,
        "identifier": {
            "anyOf": [
                STR,
                SCHEMA_ORG_IDENTIFIER,
                array({"anyOf": [STR, SCHEMA_ORG_IDENTIFIER]}),
            ]
        },
    }
)

REFERENCE_OR_REFERENCES = {
    "anyOf": [
        STR,
        SCHEMA_ORG_REFERENCE,
        array({"anyOf": [STR, SCHEMA_ORG_REFERENCE]}),
    ]
}

SCHEMA_ORG_PROPERTY_VALUE = obj(
    {
        "@type": STR,
        "propertyID": STR,
        "name": STR,
        "value": JSON_VALUE,
        "unitCode": STR,
        "unitText": STR,
        "valueReference": {"anyOf": [STR, SCHEMA_ORG_REFERENCE]},
        "url": STR,
        "description": STR,
    },
    required=("name", "value"),
)

SCHEMA_ORG_POSTAL_ADDRESS = obj(
    {
        "@type": STR,
        "streetAddress": STR,
        "postOfficeBoxNumber": STR,
        "addressLocality": STR,
        "addressRegion": STR,
        "postalCode": STR,
        "addressCountry": {"anyOf": [STR, SCHEMA_ORG_REFERENCE]},
    }
)

SCHEMA_ORG_GEO = obj(
    {
        "@type": STR,
        "latitude": {"type": "number"},
        "longitude": {"type": "number"},
        "elevation": {"type": "number"},
        "postalCode": STR,
        "addressCountry": STR,
    }
)

SCHEMA_ORG = obj(
    {
        "@context": STRING_OR_STRINGS,
        "@type": STRING_OR_STRINGS,
        "@id": STR,
        "additionalType": STRING_OR_STRINGS,
        "name": STR,
        "alternateName": STRING_OR_STRINGS,
        "description": STR,
        "disambiguatingDescription": STR,
        "url": STR,
        "sameAs": STRING_OR_STRINGS,
        "identifier": {
            "anyOf": [
                STR,
                SCHEMA_ORG_IDENTIFIER,
                array({"anyOf": [STR, SCHEMA_ORG_IDENTIFIER]}),
            ]
        },
        "image": REFERENCE_OR_REFERENCES,
        "logo": REFERENCE_OR_REFERENCES,
        "mainEntity": REFERENCE_OR_REFERENCES,
        "mainEntityOfPage": REFERENCE_OR_REFERENCES,
        "subjectOf": REFERENCE_OR_REFERENCES,
        "about": REFERENCE_OR_REFERENCES,
        "mentions": REFERENCE_OR_REFERENCES,
        "isPartOf": REFERENCE_OR_REFERENCES,
        "hasPart": REFERENCE_OR_REFERENCES,
        "isBasedOn": REFERENCE_OR_REFERENCES,
        "citation": REFERENCE_OR_REFERENCES,
        "supportingData": REFERENCE_OR_REFERENCES,
        "associatedMedia": REFERENCE_OR_REFERENCES,
        "encoding": REFERENCE_OR_REFERENCES,
        "creator": REFERENCE_OR_REFERENCES,
        "author": REFERENCE_OR_REFERENCES,
        "publisher": REFERENCE_OR_REFERENCES,
        "provider": REFERENCE_OR_REFERENCES,
        "contributor": REFERENCE_OR_REFERENCES,
        "copyrightHolder": REFERENCE_OR_REFERENCES,
        "funder": REFERENCE_OR_REFERENCES,
        "sponsor": REFERENCE_OR_REFERENCES,
        "organizer": REFERENCE_OR_REFERENCES,
        "participant": REFERENCE_OR_REFERENCES,
        "memberOf": REFERENCE_OR_REFERENCES,
        "affiliation": REFERENCE_OR_REFERENCES,
        "parentOrganization": REFERENCE_OR_REFERENCES,
        "subOrganization": REFERENCE_OR_REFERENCES,
        "contactPoint": REFERENCE_OR_REFERENCES,
        "location": REFERENCE_OR_REFERENCES,
        "contentLocation": REFERENCE_OR_REFERENCES,
        "spatialCoverage": REFERENCE_OR_REFERENCES,
        "address": {"anyOf": [STR, SCHEMA_ORG_POSTAL_ADDRESS]},
        "geo": SCHEMA_ORG_GEO,
        "dateCreated": STR,
        "dateModified": STR,
        "datePublished": STR,
        "startDate": STR,
        "endDate": STR,
        "temporalCoverage": STR,
        "inLanguage": STRING_OR_STRINGS,
        "license": REFERENCE_OR_REFERENCES,
        "copyrightNotice": STR,
        "copyrightYear": {"type": "integer"},
        "keywords": STRING_OR_STRINGS,
        "jobTitle": STRING_OR_STRINGS,
        "knowsAbout": REFERENCE_OR_REFERENCES,
        "knowsLanguage": STRING_OR_STRINGS,
        "potentialAction": {"anyOf": [JSON_MAP, array(JSON_MAP)]},
        "additionalProperty": array(SCHEMA_ORG_PROPERTY_VALUE),
        "schemaVersion": STR,
        "sdDatePublished": STR,
        "sdLicense": REFERENCE_OR_REFERENCES,
        "sdPublisher": REFERENCE_OR_REFERENCES,
        "properties": JSON_MAP,
    }
)


def schema_org_types(dtype: str) -> tuple[str, ...]:
    canonical = str(dtype or "document").strip().lower().replace("_", "-").replace(" ", "-")
    return DTYPE_SCHEMA_ORG_TYPES.get(canonical, ("Thing",))


def schema_org_metadata(dtype: str, doc_id: str = "") -> dict[str, Any]:
    types = schema_org_types(dtype)
    value: dict[str, Any] = {
        "@context": SCHEMA_ORG_CONTEXT,
        "@type": types[0] if len(types) == 1 else list(types),
        "additionalType": f"https://starintel.dev/dtype/{str(dtype).strip().lower().replace('_', '-')}",
    }
    if doc_id:
        value["@id"] = doc_id
    return value


def document_schema(dtype: str | None = None) -> dict[str, Any]:
    schema = deepcopy(core_document_schema(dtype))
    schema["properties"]["schema_org"] = deepcopy(SCHEMA_ORG)
    return schema


def _label(document: dict[str, Any]) -> str:
    data = document.get("data") if isinstance(document.get("data"), dict) else {}
    for value in (
        document.get("title"),
        data.get("display_name"),
        data.get("full_name"),
        data.get("legal_name"),
        data.get("name"),
        data.get("claim"),
        data.get("term"),
        data.get("target"),
    ):
        if isinstance(value, str) and value.strip():
            return value.strip()
    return str(document.get("_id") or "StarIntel record")


def _identifier_values(document: dict[str, Any]) -> list[dict[str, Any]]:
    values: list[dict[str, Any]] = []
    for identifier in document.get("identifiers", []):
        if not isinstance(identifier, dict) or identifier.get("value") in (None, ""):
            continue
        item: dict[str, Any] = {
            "@type": "PropertyValue",
            "propertyID": str(identifier.get("scheme") or identifier.get("issuer") or "identifier"),
            "value": identifier["value"],
        }
        if identifier.get("url"):
            item["url"] = str(identifier["url"])
        if identifier.get("notes"):
            item["description"] = str(identifier["notes"])
        values.append(item)
    return values


def to_schema_org(document: dict[str, Any]) -> dict[str, Any]:
    dtype = str(document.get("dtype") or "document")
    data = document.get("data") if isinstance(document.get("data"), dict) else {}
    explicit = document.get("schema_org") if isinstance(document.get("schema_org"), dict) else {}
    value = schema_org_metadata(dtype, str(document.get("_id") or ""))
    value["name"] = _label(document)

    description = document.get("description") or document.get("summary") or data.get("description")
    if isinstance(description, str) and description.strip():
        value["description"] = description.strip()

    aliases = [str(item) for item in document.get("aliases", []) if str(item)]
    if aliases:
        value["alternateName"] = aliases

    keywords = [str(item) for item in [*document.get("keywords", []), *document.get("tags", [])] if str(item)]
    if keywords:
        value["keywords"] = list(dict.fromkeys(keywords))

    if document.get("language"):
        value["inLanguage"] = str(document["language"])
    if document.get("date_added"):
        value["dateCreated"] = str(document["date_added"])
    if document.get("date_updated"):
        value["dateModified"] = str(document["date_updated"])

    identifiers = _identifier_values(document)
    if identifiers:
        value["identifier"] = identifiers

    url = data.get("url") or data.get("website") or data.get("uri")
    if isinstance(url, str) and url:
        value["url"] = url

    image = data.get("image_url") or data.get("logo_url")
    if isinstance(image, str) and image:
        value["image"] = image

    related = [str(item) for item in document.get("related_ids", []) if str(item)]
    if related:
        value["about"] = [{"@id": item} for item in related]

    geospatial = document.get("geospatial") if isinstance(document.get("geospatial"), dict) else {}
    if geospatial.get("lat") is not None and (geospatial.get("lon") is not None or geospatial.get("long") is not None):
        value["geo"] = {
            "@type": "GeoCoordinates",
            "latitude": geospatial["lat"],
            "longitude": geospatial.get("lon", geospatial.get("long")),
        }

    value.update(deepcopy(explicit))
    return value


missing = sorted(set(TYPE_FIELDS) - set(DTYPE_SCHEMA_ORG_TYPES))
extra = sorted(set(DTYPE_SCHEMA_ORG_TYPES) - set(TYPE_FIELDS))
if missing or extra:
    raise RuntimeError(f"Schema.org dtype map drift: missing={missing} extra={extra}")
