#!/usr/bin/env python3
from __future__ import annotations

from html.parser import HTMLParser
import html
import re
from typing import Any


HQ_LOCALITY_PATTERN = re.compile(
    r"\b(?:located|based)\s+in\s+(?:sunny\s+)?(?P<city>[A-Z][A-Za-z .'-]+),\s*"
    r"(?P<region>[A-Z][A-Za-z .'-]+),\s*(?:[^.]{0,160}\b)?HQ\b",
    re.IGNORECASE,
)
LABELED_CONTACT_ADDRESS_PATTERN = re.compile(
    r"\bAddress:\s*(?P<street>[^,\n]+),\s*(?P<city>[^,\n]+),\s*"
    r"(?P<region>[A-Z]{2}|[A-Za-z .'-]+)\s+(?P<postal>\d{5}(?:-\d{4})?)\b",
    re.IGNORECASE,
)
ORGANIZATIONAL_CONTACT_ADDRESS_PATTERN = re.compile(
    r"\b(?:let['’]s\s+talk\s+business|contact\s+us)\b.{0,160}?"
    r"(?P<street>\d{1,6}\s+[A-Za-z0-9 .#'-]+?)\s+"
    r"(?P<city>[A-Z][A-Za-z .'-]+),\s*"
    r"(?P<region>[A-Z]{2})\s+(?P<postal>\d{5}(?:-\d{4})?)\b",
    re.IGNORECASE,
)
PUBLIC_AGENCY_FOOTER_ADDRESS_PATTERN = re.compile(
    r"\b(?:department|office|agency|authority|commission)\b.{0,120}?•\s*"
    r"(?P<street>\d{1,6}\s+[A-Za-z0-9 .'-]+?)\s*•\s*"
    r"(?P<floor>\d{1,3}(?:st|nd|rd|th)\s+Floor)\s*•\s*"
    r"(?P<city>[A-Z][A-Za-z .'-]+),\s*"
    r"(?P<region>[A-Z]{2}|[A-Za-z .'-]+)\s+(?P<postal>\d{5}(?:-\d{4})?)\b",
    re.IGNORECASE,
)
REGION_NAMES = {
    "CA": "California",
    "OH": "Ohio",
}


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        value = " ".join(data.split())
        if value:
            self.parts.append(value)


def visible_text(raw: str) -> str:
    parser = _TextExtractor()
    parser.feed(raw)
    parser.close()
    return html.unescape(" ".join(parser.parts)).replace("\xa0", " ").strip()


def _region_name(value: str) -> str:
    cleaned = " ".join(value.split()).strip()
    return REGION_NAMES.get(cleaned.upper(), cleaned)


def extract_hq_locality(raw: str) -> dict[str, Any]:
    text = visible_text(raw)
    match = HQ_LOCALITY_PATTERN.search(text)
    if match is None:
        raise ValueError("source does not expose an explicit headquarters locality")

    return {
        "city": " ".join(match.group("city").split()).strip(),
        "region": _region_name(match.group("region")),
        "country": "United States",
        "location_type": "headquarters_locality",
        "source_semantics": "explicit headquarters locality",
    }


def _address_result(
    match: re.Match[str],
    *,
    location_type: str,
    source_semantics: str,
    floor: str | None = None,
) -> dict[str, Any]:
    street = " ".join(match.group("street").split()).strip()
    if floor:
        street = f"{street}, {' '.join(floor.split()).strip()}"
    city = " ".join(match.group("city").split()).strip()
    region = _region_name(match.group("region"))
    postal = match.group("postal")
    return {
        "address": f"{street}, {city}, {region} {postal}",
        "street": street,
        "city": city,
        "region": region,
        "state": region,
        "postal": postal,
        "country": "United States",
        "country_code": "US",
        "location_type": location_type,
        "source_semantics": source_semantics,
    }


def extract_public_contact_address(raw: str) -> dict[str, Any]:
    text = visible_text(raw)
    labeled = LABELED_CONTACT_ADDRESS_PATTERN.search(text)
    if labeled is not None:
        return _address_result(
            labeled,
            location_type="public_legal_contact_address",
            source_semantics="explicit public contact address",
        )

    organizational = ORGANIZATIONAL_CONTACT_ADDRESS_PATTERN.search(text)
    if organizational is not None:
        return _address_result(
            organizational,
            location_type="public_organizational_contact_address",
            source_semantics="explicit public organizational contact address",
        )

    agency_footer = PUBLIC_AGENCY_FOOTER_ADDRESS_PATTERN.search(text)
    if agency_footer is not None:
        return _address_result(
            agency_footer,
            floor=agency_footer.group("floor"),
            location_type="public_organizational_contact_address",
            source_semantics="explicit public agency footer address",
        )

    raise ValueError("source does not expose an explicit public contact address")
