#!/usr/bin/env python3
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import unicodedata
import urllib.parse
import urllib.robotparser
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import requests
from bs4 import BeautifulSoup

SCHEMA = "0.9.0"
RUN_ID = "dark-academia-membership-recursion-2026-07-31"
STAMP = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
USER_AGENT = "StarIntel-AutoDig/0.9 (+https://starintel.actor; public-source roster research)"
SOCIAL_HOSTS = {
    "linkedin.com": "linkedin",
    "www.linkedin.com": "linkedin",
    "x.com": "x",
    "twitter.com": "x",
    "www.twitter.com": "x",
    "facebook.com": "facebook",
    "www.facebook.com": "facebook",
    "instagram.com": "instagram",
    "www.instagram.com": "instagram",
    "youtube.com": "youtube",
    "www.youtube.com": "youtube",
}
NAME_STOPWORDS = {
    "about", "apply", "board", "contact", "experts", "fellow", "fellows", "leadership",
    "load more", "member", "members", "membership", "our people", "people", "researchers",
    "staff", "team", "trustees", "view profile", "who we are",
}
ROLE_KEYWORDS = {
    "board": "board_member_of",
    "trustee": "trustee_of",
    "director": "director_of",
    "chair": "chair_of",
    "president": "executive_of",
    "chief": "executive_of",
    "ceo": "executive_of",
    "fellow": "fellow_of",
    "advisor": "advisor_to",
    "adviser": "advisor_to",
    "staff": "works_for",
    "researcher": "works_for",
    "expert": "affiliated_with",
    "member": "member_of",
    "participant": "participant_in",
}


@dataclass
class PersonRecord:
    dataset: str
    name: str
    role: str
    organization_name: str
    organization_id: str
    source_url: str
    source_title: str
    profile_url: str = ""
    role_category: str = "member"
    affiliations: list[str] = field(default_factory=list)
    emails: list[str] = field(default_factory=list)
    phones: list[str] = field(default_factory=list)
    socials: dict[str, str] = field(default_factory=dict)
    country: str = ""
    coverage_status: str = "recorded"


class Scraper:
    def __init__(self, config: dict[str, Any], root: Path):
        self.config = config
        self.root = root
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.8"})
        self.robot_cache: dict[str, urllib.robotparser.RobotFileParser | None] = {}
        self.fetch_cache: dict[str, tuple[str, int, str]] = {}
        self.stats: dict[str, Any] = {"targets": {}, "errors": [], "started_at": STAMP}
        self.people: list[PersonRecord] = []
        self.documents: dict[str, dict[str, Any]] = {}
        self.source_urls: set[str] = set()

    @staticmethod
    def slug(value: str, limit: int = 100) -> str:
        value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
        value = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
        return (value or "unknown")[:limit].strip("-")

    @staticmethod
    def norm_name(value: str) -> str:
        value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
        value = re.sub(r"\b(dr|mr|mrs|ms|prof|professor|ambassador|general|secretary|president|prime minister|sir|dame|hon)\.?\b", " ", value, flags=re.I)
        return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()

    @staticmethod
    def source(url: str, title: str, kind: str = "official_public_directory", publisher: str = "") -> dict[str, Any]:
        return {
            "source_id": "sha256:" + hashlib.sha256(url.encode()).hexdigest(),
            "kind": kind,
            "title": title,
            "publisher": publisher,
            "url": url,
            "uri": url,
            "retrieved_at": STAMP,
            "access_method": "public web",
            "credibility": 0.98,
        }

    @staticmethod
    def common_doc(
        dtype: str,
        dataset: str,
        doc_id: str,
        title: str,
        summary: str,
        data: dict[str, Any],
        sources: list[dict[str, Any]],
        evidence: list[dict[str, Any]] | None = None,
        *,
        tags: list[str] | None = None,
        status: str = "recorded",
        pii: bool = False,
        related_ids: list[str] | None = None,
        assessment: dict[str, Any] | None = None,
        workflow: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return {
            "_id": doc_id,
            "dataset": dataset,
            "dtype": dtype,
            "schema_version": SCHEMA,
            "version": 1,
            "date_added": STAMP,
            "date_updated": STAMP,
            "title": title,
            "summary": summary,
            "description": "",
            "status": status,
            "language": "en",
            "tags": tags or [],
            "labels": [],
            "aliases": [],
            "keywords": [],
            "identifiers": [],
            "sources": sources,
            "evidence": evidence or [],
            "temporal": {"collected_at": STAMP, "observed_at": STAMP},
            "provenance": {
                "collector": "starintel-gpt-auto-dig",
                "collector_type": "github-actions-scraper",
                "agent": "public-membership-roster-scraper",
                "method": "official public directory extraction",
                "pipeline": "dark-academia-membership-recursion",
                "run_id": RUN_ID,
                "software_version": SCHEMA,
            },
            "assessment": assessment or {"confidence": 0.95, "completeness": 0.75},
            "verification": {
                "status": "source-backed",
                "verified": True,
                "verified_at": STAMP,
                "methods": ["official-page extraction"],
            },
            "handling": {
                "visibility": "public",
                "handling": "public-source-only",
                "sensitive": False,
                "pii": pii,
            },
            "lineage": {},
            "quality": {"validation_status": "pending_repository_validation", "validator": "scripts/starintel.py validate"},
            "workflow": workflow or {},
            "geospatial": {},
            "attachments": [],
            "related_ids": related_ids or [],
            "notes": [],
            "data": data,
            "extensions": {},
        }

    def add_doc(self, doc: dict[str, Any]) -> None:
        doc_id = doc["_id"]
        existing = self.documents.get(doc_id)
        if existing is None:
            self.documents[doc_id] = doc
            return
        # Merge public sources/evidence deterministically rather than dropping repeated roster observations.
        for key in ("sources", "evidence", "related_ids", "tags"):
            seen = {json.dumps(v, sort_keys=True) if isinstance(v, dict) else str(v) for v in existing.get(key, [])}
            for item in doc.get(key, []):
                marker = json.dumps(item, sort_keys=True) if isinstance(item, dict) else str(item)
                if marker not in seen:
                    existing.setdefault(key, []).append(item)
                    seen.add(marker)

    def robots_allowed(self, url: str) -> bool:
        parsed = urllib.parse.urlparse(url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        if base not in self.robot_cache:
            rp = urllib.robotparser.RobotFileParser()
            rp.set_url(base + "/robots.txt")
            try:
                rp.read()
                self.robot_cache[base] = rp
            except Exception:
                self.robot_cache[base] = None
        rp = self.robot_cache[base]
        return True if rp is None else rp.can_fetch(USER_AGENT, url)

    def fetch(self, url: str, *, allow_binary: bool = False) -> tuple[str, int, str]:
        url = url.split("#", 1)[0]
        if url in self.fetch_cache:
            return self.fetch_cache[url]
        if not self.robots_allowed(url):
            result = ("", 999, "blocked_by_robots")
            self.fetch_cache[url] = result
            return result
        last_error = ""
        for attempt in range(3):
            try:
                response = self.session.get(url, timeout=35, allow_redirects=True)
                ctype = response.headers.get("content-type", "")
                text = response.text if ("text" in ctype or "html" in ctype or "xml" in ctype or "json" in ctype or not ctype) else ""
                if not allow_binary and response.status_code == 200 and not text:
                    last_error = f"unsupported content-type {ctype}"
                result = (text, response.status_code, response.url)
                self.fetch_cache[url] = result
                self.source_urls.add(response.url)
                return result
            except requests.RequestException as exc:
                last_error = str(exc)
                time.sleep(1.5 * (attempt + 1))
        result = ("", 598, last_error)
        self.fetch_cache[url] = result
        return result

    def discover_sitemaps(self, homepage: str, configured: list[str]) -> list[str]:
        parsed = urllib.parse.urlparse(homepage)
        base = f"{parsed.scheme}://{parsed.netloc}"
        candidates = list(configured)
        robots, status, _ = self.fetch(base + "/robots.txt")
        if status == 200:
            candidates.extend(re.findall(r"(?im)^\s*Sitemap:\s*(\S+)", robots))
        candidates.extend([base + "/sitemap.xml", base + "/sitemap_index.xml", base + "/wp-sitemap.xml"])
        return list(dict.fromkeys(candidates))

    def sitemap_urls(self, roots: list[str], max_sitemaps: int = 80, max_urls: int = 120000) -> set[str]:
        pending = list(roots)
        seen_maps: set[str] = set()
        urls: set[str] = set()
        while pending and len(seen_maps) < max_sitemaps and len(urls) < max_urls:
            sm = pending.pop(0)
            if sm in seen_maps:
                continue
            seen_maps.add(sm)
            text, status, final = self.fetch(sm)
            if status != 200 or "<loc" not in text:
                continue
            try:
                root = ET.fromstring(text)
            except ET.ParseError:
                continue
            locs = [el.text.strip() for el in root.iter() if el.tag.endswith("loc") and el.text]
            if root.tag.endswith("sitemapindex"):
                pending.extend(locs)
            else:
                urls.update(locs)
        return urls

    @staticmethod
    def url_matches(url: str, patterns: list[str]) -> bool:
        path = urllib.parse.urlparse(url).path.lower()
        return any(re.search(pattern, path, flags=re.I) for pattern in patterns)

    @staticmethod
    def clean_text(value: str) -> str:
        return re.sub(r"\s+", " ", value or "").strip(" \t\r\n|-–—")

    def looks_like_name(self, value: str) -> bool:
        value = self.clean_text(value)
        if not 3 <= len(value) <= 100 or value.lower() in NAME_STOPWORDS:
            return False
        if any(ch in value for ch in "{}[]<>@") or re.search(r"https?://", value):
            return False
        words = [w for w in re.split(r"\s+", value) if w]
        if not 2 <= len(words) <= 8:
            return False
        alpha = sum(ch.isalpha() for ch in value)
        return alpha >= max(3, int(len(value) * 0.55))

    def jsonld_people(self, soup: BeautifulSoup) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []

        def walk(value: Any) -> None:
            if isinstance(value, list):
                for item in value:
                    walk(item)
            elif isinstance(value, dict):
                t = value.get("@type")
                types = [t] if isinstance(t, str) else (t or [])
                if "Person" in types:
                    out.append(value)
                for key in ("@graph", "itemListElement", "member", "employee", "founder"):
                    if key in value:
                        walk(value[key])

        for script in soup.select('script[type="application/ld+json"]'):
            try:
                walk(json.loads(script.get_text(strip=True)))
            except Exception:
                continue
        return out

    def extract_contacts(self, soup: BeautifulSoup) -> tuple[list[str], list[str], dict[str, str]]:
        emails: set[str] = set()
        phones: set[str] = set()
        socials: dict[str, str] = {}
        for a in soup.select("a[href]"):
            href = a.get("href", "").strip()
            if href.lower().startswith("mailto:"):
                email = urllib.parse.unquote(href[7:].split("?", 1)[0]).strip()
                if re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
                    emails.add(email.lower())
            elif href.lower().startswith("tel:"):
                phone = urllib.parse.unquote(href[4:].split("?", 1)[0]).strip()
                phone = re.sub(r"[^0-9+() .-]", "", phone)
                if len(re.sub(r"\D", "", phone)) >= 7:
                    phones.add(phone)
            else:
                host = urllib.parse.urlparse(href).netloc.lower()
                if host in SOCIAL_HOSTS:
                    socials[SOCIAL_HOSTS[host]] = href
        return sorted(emails), sorted(phones), socials

    def profile_record(self, target: dict[str, Any], url: str, role_category: str = "member") -> PersonRecord | None:
        text, status, final = self.fetch(url)
        if status != 200 or not text:
            return None
        soup = BeautifulSoup(text, "lxml")
        ld = self.jsonld_people(soup)
        name = ""
        role = ""
        affiliations: list[str] = []
        if ld:
            item = ld[0]
            name = self.clean_text(str(item.get("name", "")))
            role = self.clean_text(str(item.get("jobTitle", "")))
            works = item.get("worksFor") or item.get("affiliation")
            if isinstance(works, dict) and works.get("name"):
                affiliations.append(self.clean_text(str(works["name"])))
            elif isinstance(works, list):
                affiliations.extend(self.clean_text(str(x.get("name", ""))) for x in works if isinstance(x, dict) and x.get("name"))
        if not name:
            node = soup.select_one("h1") or soup.select_one("[itemprop='name']")
            name = self.clean_text(node.get_text(" ", strip=True) if node else "")
        if not role:
            for selector in target.get("role_selectors", []) + [
                "[itemprop='jobTitle']", ".job-title", ".position", ".person-title", ".expert-title",
                ".profile-title", ".bio-title", ".field--name-field-title", ".subtitle",
            ]:
                node = soup.select_one(selector)
                if node:
                    candidate = self.clean_text(node.get_text(" ", strip=True))
                    if candidate and candidate != name:
                        role = candidate
                        break
        if not self.looks_like_name(name):
            return None
        emails, phones, socials = self.extract_contacts(soup)
        title = self.clean_text((soup.title.string if soup.title and soup.title.string else "") or target["name"])
        return PersonRecord(
            dataset=target["dataset"], name=name, role=role, organization_name=target["name"],
            organization_id=target.get("org_id", f"starintel:org:{target['dataset']}"), source_url=final, source_title=title,
            profile_url=final, role_category=role_category or target.get("default_role", "member"),
            affiliations=[a for a in affiliations if a], emails=emails, phones=phones, socials=socials,
        )

    def extract_bilderberg(self, target: dict[str, Any], url: str) -> list[PersonRecord]:
        text, status, final = self.fetch(url)
        if status != 200:
            return []
        soup = BeautifulSoup(text, "lxml")
        title = self.clean_text(soup.title.string if soup.title and soup.title.string else f"{target['name']} participants")
        records: list[PersonRecord] = []
        for line in soup.get_text("\n").splitlines():
            line = self.clean_text(line)
            match = re.match(r"^(.+?)\s*\(([A-Z]{3}|INT)\),\s*(.+)$", line)
            if not match:
                continue
            raw_name, country, role = match.groups()
            if "," in raw_name:
                last, first = [self.clean_text(x) for x in raw_name.split(",", 1)]
                name = f"{first} {last}".strip()
            else:
                name = raw_name
            if not self.looks_like_name(name):
                continue
            records.append(PersonRecord(
                dataset=target["dataset"], name=name, role=role, organization_name=target["name"],
                organization_id=target.get("org_id", f"starintel:org:{target['dataset']}"), source_url=final,
                source_title=title, role_category="participant", country=country,
            ))
        return records

    def extract_cards(self, target: dict[str, Any], url: str, role_category: str = "member") -> list[PersonRecord]:
        text, status, final = self.fetch(url)
        if status != 200 or not text:
            return []
        soup = BeautifulSoup(text, "lxml")
        title = self.clean_text(soup.title.string if soup.title and soup.title.string else target["name"])
        records: list[PersonRecord] = []
        selectors = target.get("card_selectors", []) + [
            "article", ".person", ".people-item", ".profile", ".member", ".team-member", ".expert",
            ".staff-member", ".card-person", ".views-row", ".elementor-post", ".wp-block-column",
        ]
        seen_nodes: set[int] = set()
        for selector in selectors:
            for card in soup.select(selector):
                if id(card) in seen_nodes:
                    continue
                seen_nodes.add(id(card))
                name_node = card.select_one("h1,h2,h3,h4,h5,[itemprop='name'],.name,.person-name,.expert-name,strong")
                if not name_node:
                    continue
                name = self.clean_text(name_node.get_text(" ", strip=True))
                if not self.looks_like_name(name):
                    continue
                role_node = card.select_one("[itemprop='jobTitle'],.job-title,.position,.title,.role,.person-title,.expert-title,p")
                role = self.clean_text(role_node.get_text(" ", strip=True) if role_node else "")
                if role == name:
                    role = ""
                link = name_node.find("a", href=True) or card.find("a", href=True)
                profile = urllib.parse.urljoin(final, link["href"]) if link else ""
                emails, phones, socials = self.extract_contacts(card)
                records.append(PersonRecord(
                    dataset=target["dataset"], name=name, role=role, organization_name=target["name"],
                    organization_id=target.get("org_id", f"starintel:org:{target['dataset']}"), source_url=profile or final,
                    source_title=title, profile_url=profile, role_category=role_category,
                    emails=emails, phones=phones, socials=socials,
                ))
        # Board/staff pages often expose plain bullet lists rather than cards.
        for li in soup.select("main li, article li, .entry-content li"):
            text_value = self.clean_text(li.get_text(" ", strip=True))
            if not text_value or len(text_value) > 220:
                continue
            name_part, sep, role = text_value.partition(",")
            name = self.clean_text(name_part)
            if not self.looks_like_name(name):
                continue
            link = li.find("a", href=True)
            profile = urllib.parse.urljoin(final, link["href"]) if link else ""
            records.append(PersonRecord(
                dataset=target["dataset"], name=name, role=self.clean_text(role if sep else ""),
                organization_name=target["name"], organization_id=target.get("org_id", f"starintel:org:{target['dataset']}"),
                source_url=profile or final, source_title=title, profile_url=profile,
                role_category=role_category,
            ))
        return records

    def crawl_directory(self, target: dict[str, Any]) -> list[PersonRecord]:
        patterns = target.get("profile_patterns", [])
        profile_urls: set[str] = set()
        roots = self.discover_sitemaps(target["homepage"], target.get("sitemaps", []))
        if patterns:
            for url in self.sitemap_urls(roots):
                if self.url_matches(url, patterns):
                    profile_urls.add(url)
        list_records: list[PersonRecord] = []
        for seed in target.get("seed_pages", []):
            category = target.get("seed_roles", {}).get(seed, target.get("default_role", "member"))
            if target.get("parser") == "bilderberg":
                list_records.extend(self.extract_bilderberg(target, seed))
                continue
            list_records.extend(self.extract_cards(target, seed, category))
            text, status, final = self.fetch(seed)
            if status == 200 and patterns:
                soup = BeautifulSoup(text, "lxml")
                for a in soup.select("a[href]"):
                    candidate = urllib.parse.urljoin(final, a.get("href", ""))
                    if urllib.parse.urlparse(candidate).netloc == urllib.parse.urlparse(target["homepage"]).netloc and self.url_matches(candidate, patterns):
                        profile_urls.add(candidate)
        max_profiles = int(target.get("max_profiles", 4000))
        selected = sorted(profile_urls)[:max_profiles]
        records: list[PersonRecord] = list_records
        with concurrent.futures.ThreadPoolExecutor(max_workers=int(target.get("workers", 10))) as pool:
            futures = {pool.submit(self.profile_record, target, url, target.get("default_role", "member")): url for url in selected}
            for future in concurrent.futures.as_completed(futures):
                try:
                    rec = future.result()
                    if rec:
                        records.append(rec)
                except Exception as exc:
                    self.stats["errors"].append({"target": target["dataset"], "url": futures[future], "error": str(exc)})
        return records

    def resolve_wikidata_website(self, name: str) -> str:
        try:
            search = self.session.get("https://www.wikidata.org/w/api.php", params={
                "action": "wbsearchentities", "search": name, "language": "en", "format": "json", "limit": 5,
            }, timeout=25).json()
            normalized = self.norm_name(name)
            for item in search.get("search", []):
                label = self.norm_name(item.get("label", ""))
                description = (item.get("description") or "").lower()
                if label != normalized and normalized not in label and label not in normalized:
                    continue
                if not any(word in description for word in ("company", "organization", "organisation", "bank", "corporation", "firm", "university", "agency", "foundation", "group")):
                    continue
                entity = self.session.get("https://www.wikidata.org/w/api.php", params={
                    "action": "wbgetentities", "ids": item["id"], "props": "claims", "format": "json",
                }, timeout=25).json()["entities"][item["id"]]
                claims = entity.get("claims", {}).get("P856", [])
                if claims:
                    return claims[0]["mainsnak"]["datavalue"]["value"]
        except Exception:
            return ""
        return ""

    def wef_partner_targets(self) -> list[dict[str, Any]]:
        docs: list[dict[str, Any]] = []
        for path in sorted((self.root / "db" / "org").glob("*.ndjson")):
            try:
                value = json.loads(path.read_text(encoding="utf-8").splitlines()[0])
            except Exception:
                continue
            if value.get("dataset") != "wef" or "partner-organization" not in value.get("tags", []):
                continue
            name = value.get("data", {}).get("name") or value.get("title")
            if not name:
                continue
            org_id = value["_id"]
            website = value.get("data", {}).get("website", "")
            source = value.get("sources", [])[:1]
            target_id = f"starintel:target:wef:{self.slug(name)}-public-rosters-and-cross-ties"
            docs.append(self.common_doc(
                "target", "wef", target_id, f"Map {name} public rosters and cross-ties",
                f"Recursive target to enumerate public leadership, boards, advisory groups, fellows, experts, and explicitly published work contacts for {name}.",
                {
                    "target": org_id,
                    "target_id": org_id,
                    "target_type": "organization-public-roster",
                    "query": f"{name} official leadership board team members fellows advisors directory",
                    "research_question": f"Who is publicly listed by {name}, what roles are stated, and which people recur across dark-academia component datasets?",
                    "objectives": ["enumerate official public rosters", "capture explicitly published work contacts", "resolve cross-dataset ties"],
                    "in_scope": ["official organization pages", "official annual reports", "official public directories"],
                    "out_of_scope": ["private contact data", "paywalled membership databases", "inferred personal contact information"],
                    "scope_type": "public-roster-recursion",
                    "seed_ids": [org_id],
                    "preferred_sources": [website] if website else ["official organization website"],
                    "depth": 1,
                    "max_depth": 5,
                    "breadth": 200,
                    "priority": 0.88,
                    "status": "queued",
                },
                source,
                tags=["wef", "partner-organization", "recursive-target", "public-roster"],
                related_ids=[org_id],
                workflow={"research_status": "queued", "queue": "dark-academia-auto-dig", "priority": 0.88, "recursion_depth": 1, "max_depth": 5, "root_target_id": target_id, "run_id": RUN_ID},
            ))
        return docs

    def relation_predicate(self, record: PersonRecord) -> str:
        haystack = f"{record.role_category} {record.role}".lower()
        for word, predicate in ROLE_KEYWORDS.items():
            if word in haystack:
                return predicate
        return "member_of"

    def emit_person_bundle(self, record: PersonRecord) -> None:
        dataset = record.dataset
        person_id = f"starintel:person:{dataset}:{self.slug(record.name)}"
        org_id = record.organization_id
        src = self.source(record.source_url, record.source_title, publisher=record.organization_name)
        contact_ids: list[str] = []
        email_ids: list[str] = []
        phone_ids: list[str] = []
        for email in record.emails:
            suffix = hashlib.sha256(email.encode()).hexdigest()[:12]
            email_id = f"starintel:email:{dataset}:{self.slug(record.name)}:{suffix}"
            email_ids.append(email_id)
            contact_ids.append(email_id)
            self.add_doc(self.common_doc(
                "email", dataset, email_id, f"Public work email for {record.name}",
                f"Email address explicitly published on an official {record.organization_name} page.",
                {"address": email, "value": email, "type": "public_work_email", "label": "officially published", "owner_id": person_id, "status": "published", "verified": True, "verified_at": STAMP, "first_seen": STAMP, "last_seen": STAMP},
                [src], tags=[dataset, "public-contact", "email"], pii=True, related_ids=[person_id, org_id],
            ))
            relation_id = f"starintel:relation:{dataset}:{self.slug(record.name)}-has-public-email-{suffix}"
            self.add_doc(self.common_doc(
                "relation", dataset, relation_id, f"{record.name} has an officially published work email",
                "Official organization page publishes this work contact.",
                {"subject": person_id, "predicate": "has_public_contact", "object": email_id, "directed": True, "relation_type": "public-contact", "qualifiers": {"contact_type": "email", "published_by": record.organization_name}, "confidence": 0.99, "active": True},
                [src], tags=[dataset, "public-contact"], related_ids=[person_id, email_id],
            ))
        for phone in record.phones:
            suffix = hashlib.sha256(phone.encode()).hexdigest()[:12]
            phone_id = f"starintel:phone:{dataset}:{self.slug(record.name)}:{suffix}"
            phone_ids.append(phone_id)
            contact_ids.append(phone_id)
            self.add_doc(self.common_doc(
                "phone", dataset, phone_id, f"Public work phone for {record.name}",
                f"Phone number explicitly published on an official {record.organization_name} page.",
                {"number": phone, "value": phone, "type": "public_work_phone", "phone_type": "work", "label": "officially published", "owner_id": person_id, "status": "published", "verified": True, "verified_at": STAMP, "first_seen": STAMP, "last_seen": STAMP},
                [src], tags=[dataset, "public-contact", "phone"], pii=True, related_ids=[person_id, org_id],
            ))
        positions = [record.role] if record.role else []
        affiliations = list(dict.fromkeys([record.organization_name] + record.affiliations))
        person = self.common_doc(
            "person", dataset, person_id, record.name,
            f"Publicly listed by {record.organization_name}{' as ' + record.role if record.role else ''}.",
            {
                "name": record.name,
                "display_name": record.name,
                "full_name": record.name,
                "website": record.profile_url or record.source_url,
                "positions": positions,
                "employers": record.affiliations,
                "professional_affiliations": affiliations,
                "public_roles": positions,
                "email_ids": email_ids,
                "phone_ids": phone_ids,
                "contact_ids": contact_ids,
                "country": record.country,
            },
            [src],
            [{"source_url": record.source_url, "kind": "official-directory-entry", "role": "supports", "observation": f"{record.organization_name} publicly lists {record.name}{' — ' + record.role if record.role else ''}.", "collected_at": STAMP, "confidence": 0.98, "status": "verified"}],
            tags=[dataset, "public-roster", record.role_category], pii=bool(contact_ids), related_ids=[org_id] + contact_ids,
            assessment={"confidence": 0.97, "completeness": 0.8, "caveats": ["Role text is preserved as published; historical or current status depends on the source page."]},
        )
        self.add_doc(person)
        predicate = self.relation_predicate(record)
        relation_suffix = ''
        if record.role_category == 'participant':
            year_match = re.search(r'/(?:meeting-)?(19|20)\d{2}/|participants-(19|20)\d{2}', record.source_url)
            year = re.search(r'(19|20)\d{2}', record.source_url)
            relation_suffix = '-' + (year.group(0) if year else hashlib.sha256(record.source_url.encode()).hexdigest()[:10])
        relation_id = f"starintel:relation:{dataset}:{self.slug(record.name)}-{predicate}-{self.slug(record.organization_name)}{relation_suffix}"
        self.add_doc(self.common_doc(
            "relation", dataset, relation_id, f"{record.name} {predicate.replace('_', ' ')} {record.organization_name}",
            f"Official public roster lists {record.name}{' as ' + record.role if record.role else ''}.",
            {"subject": person_id, "predicate": predicate, "object": org_id, "directed": True, "inverse_predicate": "has_publicly_listed_person", "relation_type": record.role_category, "qualifiers": {"published_role": record.role, "source_page": record.source_url, "coverage_status": record.coverage_status}, "confidence": 0.98, "active": True},
            [src], tags=[dataset, "public-roster", "membership-relation"], related_ids=[person_id, org_id],
        ))
        target_id = f"starintel:target:{dataset}:{self.slug(record.name)}-cross-ties"
        self.add_doc(self.common_doc(
            "target", dataset, target_id, f"Resolve cross-ties for {record.name}",
            f"Follow-up target generated from the {record.organization_name} public roster.",
            {"target": person_id, "target_id": person_id, "target_type": "person-cross-ties", "query": f'"{record.name}" board fellow advisor member director government corporate affiliations', "research_question": f"Which dark-academia component organizations, companies, government bodies, boards, and advisory groups publicly list {record.name}?", "objectives": ["resolve exact identity", "enumerate official affiliations", "detect cross-dataset recurrence"], "in_scope": ["official profiles", "government biographies", "corporate leadership pages", "public filings"], "out_of_scope": ["private contact information", "identity inference without corroboration"], "scope_type": "cross-tie-recursion", "seed_ids": [person_id, org_id], "preferred_sources": ["official sources"], "required_dtypes": ["person", "org", "relation"], "depth": 1, "max_depth": 5, "breadth": 50, "priority": 0.8, "status": "queued"},
            [src], tags=[dataset, "recursive-target", "cross-ties"], related_ids=[person_id, org_id],
            workflow={"research_status": "queued", "queue": "dark-academia-auto-dig", "priority": 0.8, "recursion_depth": 1, "max_depth": 5, "root_target_id": target_id, "run_id": RUN_ID},
        ))

    def emit_org(self, target: dict[str, Any], count: int, coverage: str, source_urls: list[str]) -> None:
        org_id = target.get("org_id", f"starintel:org:{target['dataset']}")
        sources = [self.source(u, f"{target['name']} official public directory", publisher=target["name"]) for u in source_urls[:30]]
        if not sources:
            sources = [self.source(target["homepage"], f"{target['name']} official website", publisher=target["name"])]
        org_path = self.root / "db" / "org" / f"{org_id}.ndjson"
        if not org_path.exists():
            self.add_doc(self.common_doc(
                "org", target["dataset"], org_id, target["name"],
                f"Organization target and public-roster source in the dark-academia composite dataset.",
                {"name": target["name"], "display_name": target["name"], "org_type": target.get("org_type", "policy-network"), "website": target["homepage"], "member_ids": []},
                sources, tags=[target["dataset"], "dark-academia", "organization-target"],
                assessment={"confidence": 0.99, "completeness": 0.95 if count else 0.2, "gaps": [] if count else ["No parseable public roster entries were returned in this run."]},
            ))
        manifest_id = f"starintel:dataset-manifest:{target['dataset']}-public-roster"
        self.add_doc(self.common_doc(
            "dataset-manifest", target["dataset"], manifest_id, f"{target['name']} public roster dataset",
            f"Machine-generated official-source roster packet for {target['name']}.",
            {"manifest_type": "official-public-roster", "name": target["dataset"], "actor": "scripts/scrape_dark_academia_memberships.py", "consumer_path": f"digs/{target['dataset']}/{RUN_ID}", "target_options": [{"homepage": target["homepage"], "coverage_status": coverage, "parsed_people": count}], "document_ids": [], "counts_by_dtype": {}, "record_count": 0, "hash_algorithm": "sha256", "content_hash": "", "files": [{"url": u} for u in source_urls[:50]], "schema_versions": [SCHEMA], "generated_at": STAMP},
            sources, tags=[target["dataset"], "dataset-manifest", "dark-academia"], related_ids=[org_id],
        ))

    def emit_cross_ties(self) -> int:
        by_name: dict[str, list[str]] = defaultdict(list)
        display: dict[str, str] = {}
        for doc_id, doc in self.documents.items():
            if doc.get("dtype") != "person":
                continue
            key = self.norm_name(doc.get("data", {}).get("full_name") or doc.get("title", ""))
            if key:
                by_name[key].append(doc_id)
                display[key] = doc.get("title", key)
        count = 0
        for key, ids in sorted(by_name.items()):
            datasets = {self.documents[x]["dataset"] for x in ids}
            if len(ids) < 2 or len(datasets) < 2:
                continue
            ordered = sorted(ids)
            for left, right in zip(ordered, ordered[1:]):
                relation_id = f"starintel:relation:dark-academia:cross-listing-{hashlib.sha256((left+'|'+right).encode()).hexdigest()[:20]}"
                sources = self.documents[left]["sources"][:1] + self.documents[right]["sources"][:1]
                self.add_doc(self.common_doc(
                    "relation", "dark-academia", relation_id, f"Cross-listing match for {display[key]}",
                    "Exact normalized public name recurs across two component datasets; identity still requires contextual confirmation.",
                    {"subject": left, "predicate": "possible_same_person_as", "object": right, "directed": False, "inverse_predicate": "possible_same_person_as", "relation_type": "cross-dataset-name-match", "qualifiers": {"normalized_name": key, "datasets": sorted(datasets), "match_method": "exact-normalized-name"}, "confidence": 0.82, "active": True},
                    sources, tags=["dark-academia", "cross-tie", "identity-resolution"], related_ids=[left, right],
                    assessment={"confidence": 0.82, "caveats": ["An exact normalized name match is a lead, not definitive identity proof."]},
                ))
                count += 1
        return count

    def run(self) -> None:
        targets = self.config["targets"]
        for target in targets:
            started = time.time()
            try:
                records = self.crawl_directory(target)
                dedup: dict[str, PersonRecord] = {}
                for record in records:
                    key = self.norm_name(record.name)
                    if target.get("parser") == "bilderberg":
                        key = key + "|" + record.source_url
                    if not key:
                        continue
                    old = dedup.get(key)
                    if old is None or (record.profile_url and not old.profile_url):
                        dedup[key] = record
                    elif old:
                        old.emails = sorted(set(old.emails + record.emails))
                        old.phones = sorted(set(old.phones + record.phones))
                        old.socials.update(record.socials)
                        if not old.role and record.role:
                            old.role = record.role
                clean = list(dedup.values())
                self.people.extend(clean)
                source_urls = sorted({r.source_url for r in clean if r.source_url})
                coverage = "roster_exposed" if clean else "no_parseable_roster_entries"
                self.emit_org(target, len(clean), coverage, source_urls)
                for record in clean:
                    self.emit_person_bundle(record)
                self.stats["targets"][target["dataset"]] = {
                    "name": target["name"], "people": len(clean), "source_pages": len(source_urls),
                    "coverage_status": coverage, "elapsed_seconds": round(time.time() - started, 2),
                }
            except Exception as exc:
                self.stats["targets"][target["dataset"]] = {"name": target["name"], "people": 0, "coverage_status": "scrape_failed", "error": str(exc)}
                self.stats["errors"].append({"target": target["dataset"], "error": str(exc)})
        for doc in self.wef_partner_targets():
            self.add_doc(doc)
        cross_count = self.emit_cross_ties()
        component_datasets = ["wef"] + [t["dataset"] for t in targets]
        composite_sources = [self.source(t["homepage"], f"{t['name']} official website", publisher=t["name"]) for t in targets]
        manifest = self.common_doc(
            "dataset-manifest", "dark-academia", "starintel:dataset-manifest:dark-academia",
            "Dark Academia composite dataset",
            "Composite public-source graph of WEF, RAND, Atlantic Council, Bilderberg, Trilateral Commission, and comparable policy, foundation, think-tank, and leadership networks.",
            {"manifest_type": "composite-dataset", "name": "dark-academia", "actor": "scripts/scrape_dark_academia_memberships.py", "consumer_path": "db", "target_options": [{"component_dataset": x} for x in component_datasets], "document_ids": [], "counts_by_dtype": {}, "record_count": 0, "hash_algorithm": "sha256", "content_hash": "", "files": [{"component_dataset": x} for x in component_datasets], "schema_versions": [SCHEMA], "generated_at": STAMP},
            composite_sources, tags=["dark-academia", "composite-dataset", "public-rosters"],
        )
        self.add_doc(manifest)
        counts = Counter(doc["dtype"] for doc in self.documents.values())
        findings = [{"dataset": k, **v} for k, v in self.stats["targets"].items()]
        research_pass = self.common_doc(
            "research-pass", "dark-academia", f"starintel:research-pass:{RUN_ID}",
            "Dark Academia membership recursion",
            "Enumerated official public rosters, published work contacts, generated recursive person and organization targets, and linked exact-name recurrences across component datasets.",
            {"research_question": "Who is publicly listed across WEF-adjacent and comparable policy networks, and where do names recur across organizations?", "method": "Official directories, sitemaps, profile pages, annual participant lists, and public contact links; exact-name cross-dataset matching.", "classification_rules": ["Only collect contact details explicitly published by the source organization", "Treat exact-name cross-listing as a lead requiring identity confirmation", "Record inaccessible or absent rosters as coverage gaps rather than empty membership claims"], "finding_ids": [], "findings": findings, "supporting_record_ids": ["starintel:dataset-manifest:dark-academia"], "counterevidence_ids": [], "unresolved_target_ids": [doc_id for doc_id, doc in self.documents.items() if doc.get("dtype") == "target"], "source_ids": sorted(self.source_urls), "agent_identity": "public-membership-roster-scraper", "narrative_role": "source normalization and target generation", "started_at": self.stats["started_at"], "completed_at": STAMP, "iteration": 1},
            composite_sources, tags=["dark-academia", "research-pass", "membership-recursion"],
        )
        self.add_doc(research_pass)
        # Finalize manifest counts after all documents exist.
        for doc in self.documents.values():
            if doc["dtype"] == "dataset-manifest":
                dataset = doc["dataset"]
                ids = sorted(x for x, value in self.documents.items() if value["dataset"] == dataset)
                dtype_counts = Counter(self.documents[x]["dtype"] for x in ids)
                doc["data"]["document_ids"] = ids
                doc["data"]["counts_by_dtype"] = dict(sorted(dtype_counts.items()))
                doc["data"]["record_count"] = len(ids)
                payload = "\n".join(json.dumps(self.documents[x], sort_keys=True, ensure_ascii=False, separators=(",", ":")) for x in ids)
                doc["data"]["content_hash"] = hashlib.sha256(payload.encode()).hexdigest()
        self.stats.update({
            "completed_at": STAMP,
            "documents": len(self.documents),
            "counts_by_dtype": dict(sorted(Counter(doc["dtype"] for doc in self.documents.values()).items())),
            "people_records": len([d for d in self.documents.values() if d["dtype"] == "person"]),
            "cross_tie_relations": cross_count,
            "wef_partner_targets": len([d for d in self.documents.values() if d["dtype"] == "target" and d["dataset"] == "wef"]),
        })

    def write_and_import(self) -> None:
        packet_dir = self.root / "digs" / "dark-academia" / RUN_ID
        packet_dir.mkdir(parents=True, exist_ok=True)
        packet = packet_dir / "starintel-documents.jsonl"
        ordered = [self.documents[k] for k in sorted(self.documents)]
        packet.write_text("".join(json.dumps(doc, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n" for doc in ordered), encoding="utf-8")
        report_dir = self.root / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        (report_dir / "dark-academia-membership-recursion.json").write_text(json.dumps(self.stats, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        lines = [
            "# Dark Academia membership recursion", "",
            f"- Generated: `{STAMP}`", f"- Documents: **{self.stats['documents']}**",
            f"- People: **{self.stats['people_records']}**", f"- Cross-tie relations: **{self.stats['cross_tie_relations']}**",
            f"- WEF partner follow-up targets: **{self.stats['wef_partner_targets']}**", "", "## Component coverage", "",
            "| Dataset | People | Status | Sources |", "|---|---:|---|---:|",
        ]
        for dataset, info in sorted(self.stats["targets"].items()):
            lines.append(f"| {dataset} | {info.get('people', 0)} | {info.get('coverage_status', '')} | {info.get('source_pages', 0)} |")
        lines.extend(["", "## Document counts", ""])
        for dtype, count in self.stats["counts_by_dtype"].items():
            lines.append(f"- `{dtype}`: {count}")
        (report_dir / "dark-academia-membership-recursion.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
        subprocess.run([sys.executable, "scripts/starintel.py", "import", str(packet), "--root", str(self.root), "--replace"], cwd=self.root, check=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/dark-academia-targets.json")
    parser.add_argument("--root", default=".")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    config = json.loads((root / args.config).read_text(encoding="utf-8"))
    scraper = Scraper(config, root)
    scraper.run()
    scraper.write_and_import()
    print(json.dumps(scraper.stats, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
