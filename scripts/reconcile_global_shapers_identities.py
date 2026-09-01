#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import gzip
import hashlib
import json
import re
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

ROOT = Path(__file__).resolve().parents[1]
CURRENT_PACKET = ROOT / "digs" / "global-shapers" / "global-shapers-current-members-api"
LEGACY_PACKET = ROOT / "digs" / "wef" / "global-shapers-legacy-intact-prefix"
REPORT_JSON = ROOT / "reports" / "global-shapers-identity-reconciliation.json"
REPORT_MD = ROOT / "reports" / "global-shapers-identity-reconciliation.md"
PROFILE_HOSTS = {
    "globalshapers.org",
    "www.globalshapers.org",
    "weforum.org",
    "www.weforum.org",
}
GLOBAL_SHAPERS_HOSTS = {"globalshapers.org", "www.globalshapers.org"}
WEF_HOSTS = {"weforum.org", "www.weforum.org"}
SOCIAL_HOST_ALIASES = {
    "linkedin.com": "linkedin.com",
    "www.linkedin.com": "linkedin.com",
    "twitter.com": "x.com",
    "www.twitter.com": "x.com",
    "x.com": "x.com",
    "www.x.com": "x.com",
    "facebook.com": "facebook.com",
    "www.facebook.com": "facebook.com",
}
SOCIAL_HOSTS = set(SOCIAL_HOST_ALIASES.values())
HUB_RE = re.compile(r"\b(.{2,100}?\s+Hub)\b", re.I)


def compact(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def normalize_text(value: str) -> str:
    text = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    return " ".join(re.sub(r"[^a-z0-9]+", " ", text.casefold()).split())


def iter_strings(value: Any) -> Iterator[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from iter_strings(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from iter_strings(item)


def canonical_url(value: str) -> str | None:
    value = value.strip()
    if not value.startswith(("http://", "https://")):
        return None
    parsed = urlparse(value)
    host = parsed.netloc.casefold().split("@")[-1].split(":", 1)[0]
    host = SOCIAL_HOST_ALIASES.get(host, host)
    if host not in PROFILE_HOSTS and host not in SOCIAL_HOSTS:
        return None
    path = re.sub(r"/{2,}", "/", parsed.path).rstrip("/") or "/"
    query = urlencode(
        sorted(
            (key, val)
            for key, val in parse_qsl(parsed.query, keep_blank_values=False)
            if not key.casefold().startswith("utm_")
        )
    )
    return urlunparse(("https", host, path, "", query, ""))


def is_official_profile_url(url: str) -> bool:
    parsed = urlparse(url)
    host = parsed.netloc.casefold()
    path = parsed.path.rstrip("/") or "/"

    if host in GLOBAL_SHAPERS_HOSTS:
        if any(
            path.startswith(prefix)
            for prefix in ("/member-details/", "/members/", "/shapers/")
        ):
            return True
        if path == "/member-details":
            query = {key.casefold(): value for key, value in parse_qsl(parsed.query)}
            return any(query.get(key) for key in ("id", "member", "profile", "uid", "user"))
        return False

    if host in WEF_HOSTS:
        return any(path.startswith(prefix) for prefix in ("/people/", "/agenda/authors/"))

    return False


def is_linkedin_profile_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.netloc.casefold() != "linkedin.com":
        return False
    path = parsed.path.rstrip("/")
    return path.startswith("/in/") or path.startswith("/pub/")


def read_packet(packet_dir: Path) -> list[dict[str, Any]]:
    manifest = packet_dir / "starintel-documents.jsonl.gz.b64.parts"
    direct = packet_dir / "starintel-documents.jsonl.gz.b64"
    plain = packet_dir / "starintel-documents.jsonl"
    if manifest.is_file():
        names = [line.strip() for line in manifest.read_text(encoding="utf-8").splitlines() if line.strip()]
        encoded = "".join("".join((packet_dir / name).read_text(encoding="utf-8").split()) for name in names)
        payload = gzip.decompress(base64.b64decode(encoded)).decode("utf-8")
    elif direct.is_file():
        encoded = "".join(direct.read_text(encoding="utf-8").split())
        payload = gzip.decompress(base64.b64decode(encoded)).decode("utf-8")
    elif plain.is_file():
        payload = plain.read_text(encoding="utf-8")
    else:
        raise RuntimeError(f"no StarIntel packet found under {packet_dir}")

    documents: list[dict[str, Any]] = []
    for number, line in enumerate(payload.splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise RuntimeError(f"{packet_dir}:{number}: expected object")
        documents.append(value)
    return documents


@dataclass
class Identity:
    source: str
    document_id: str
    name: str
    normalized_name: str
    hubs: set[str] = field(default_factory=set)
    wef_ids: set[str] = field(default_factory=set)
    official_urls: set[str] = field(default_factory=set)
    linkedin_urls: set[str] = field(default_factory=set)
    social_urls: set[str] = field(default_factory=set)
    all_urls: set[str] = field(default_factory=set)

    def strong_keys(self) -> set[str]:
        keys = {f"wef:{value}" for value in self.wef_ids}
        keys.update(f"official:{value}" for value in self.official_urls)
        keys.update(f"linkedin:{value}" for value in self.linkedin_urls)
        return keys

    def hub_name_keys(self) -> set[str]:
        return {
            f"name-hub:{self.normalized_name}|{hub}"
            for hub in self.hubs
            if self.normalized_name and hub
        }


def identity_from_document(document: dict[str, Any], source: str) -> Identity:
    data = document.get("data") if isinstance(document.get("data"), dict) else {}
    name = str(
        data.get("full_name")
        or data.get("display_name")
        or data.get("name")
        or document.get("title")
        or ""
    ).strip()
    identity = Identity(
        source=source,
        document_id=str(document.get("_id") or ""),
        name=name,
        normalized_name=normalize_text(name),
    )

    external_ids = data.get("external_ids", [])
    for value in external_ids if isinstance(external_ids, list) else []:
        if not isinstance(value, dict):
            continue
        scheme = str(value.get("scheme") or "").casefold()
        identifier = str(value.get("value") or "").strip().casefold()
        if identifier and scheme in {
            "wef-profile-id",
            "global-shapers-profile-id",
            "salesforce-profile-id",
        }:
            identity.wef_ids.add(identifier)

    extensions = document.get("extensions") if isinstance(document.get("extensions"), dict) else {}
    api = extensions.get("global_shapers_api") if isinstance(extensions.get("global_shapers_api"), dict) else {}
    wef_id = str(api.get("wef_profile_id") or "").strip().casefold()
    if wef_id:
        identity.wef_ids.add(wef_id)

    hub_candidates: list[str] = []
    for key in ("hub_names", "professional_affiliations", "positions"):
        value = api.get(key) if key in api else data.get(key)
        if isinstance(value, list):
            hub_candidates.extend(item for item in value if isinstance(item, str))
        elif isinstance(value, str):
            hub_candidates.append(value)
    for value in hub_candidates:
        for match in HUB_RE.finditer(value):
            normalized = normalize_text(match.group(1))
            if normalized:
                identity.hubs.add(normalized)

    for raw in iter_strings(
        {
            "sources": document.get("sources", []),
            "data_misc": data.get("misc", []),
            "extensions": extensions,
        }
    ):
        url = canonical_url(raw)
        if not url:
            continue
        identity.all_urls.add(url)
        host = urlparse(url).netloc
        if host in PROFILE_HOSTS:
            if is_official_profile_url(url):
                identity.official_urls.add(url)
        elif host == "linkedin.com":
            if is_linkedin_profile_url(url):
                identity.linkedin_urls.add(url)
            else:
                identity.social_urls.add(url)
        else:
            identity.social_urls.add(url)
    return identity


class UnionFind:
    def __init__(self, size: int) -> None:
        self.parent = list(range(size))
        self.rank = [0] * size

    def find(self, value: int) -> int:
        while self.parent[value] != value:
            self.parent[value] = self.parent[self.parent[value]]
            value = self.parent[value]
        return value

    def union(self, left: int, right: int) -> None:
        left_root = self.find(left)
        right_root = self.find(right)
        if left_root == right_root:
            return
        if self.rank[left_root] < self.rank[right_root]:
            left_root, right_root = right_root, left_root
        self.parent[right_root] = left_root
        if self.rank[left_root] == self.rank[right_root]:
            self.rank[left_root] += 1


def reconcile(identities: list[Identity]) -> dict[str, Any]:
    union = UnionFind(len(identities))
    strong_members: dict[str, list[int]] = defaultdict(list)
    for index, identity in enumerate(identities):
        for key in sorted(identity.strong_keys()):
            strong_members[key].append(index)

    strong_matches: Counter[str] = Counter()
    suppressed_strong_key_collisions: list[dict[str, Any]] = []
    for key, members in sorted(strong_members.items()):
        if len(members) < 2:
            continue
        key_type = key.split(":", 1)[0]
        normalized_names = sorted(
            {
                identities[index].normalized_name
                for index in members
                if identities[index].normalized_name
            }
        )
        if key_type in {"official", "linkedin"} and len(members) > 2 and len(normalized_names) > 1:
            suppressed_strong_key_collisions.append(
                {
                    "key": key,
                    "documents": len(members),
                    "normalized_names": normalized_names,
                    "document_ids": sorted(identities[index].document_id for index in members),
                }
            )
            continue
        anchor = members[0]
        for index in members[1:]:
            union.union(anchor, index)
            strong_matches[key_type] += 1

    name_hub_index: dict[str, int] = {}
    name_hub_matches = 0
    for index, identity in enumerate(identities):
        for key in sorted(identity.hub_name_keys()):
            prior = name_hub_index.get(key)
            if prior is None:
                name_hub_index[key] = index
            else:
                union.union(index, prior)
                name_hub_matches += 1

    components: dict[int, list[int]] = defaultdict(list)
    for index in range(len(identities)):
        components[union.find(index)].append(index)

    component_records: list[dict[str, Any]] = []
    overlaps_by_sources: Counter[str] = Counter()
    for members in components.values():
        sources = sorted({identities[index].source for index in members})
        source_counts = Counter(identities[index].source for index in members)
        if len(sources) > 1:
            overlaps_by_sources["+".join(sources)] += 1
        component_records.append(
            {
                "canonical_component_id": hashlib.sha256(
                    "\n".join(sorted(identities[index].document_id for index in members)).encode()
                ).hexdigest()[:24],
                "documents": len(members),
                "sources": sources,
                "source_counts": dict(sorted(source_counts.items())),
                "document_ids": sorted(identities[index].document_id for index in members),
                "names": sorted({identities[index].name for index in members if identities[index].name}),
                "normalized_names": sorted(
                    {
                        identities[index].normalized_name
                        for index in members
                        if identities[index].normalized_name
                    }
                ),
                "hubs": sorted({hub for index in members for hub in identities[index].hubs}),
                "wef_ids": sorted({value for index in members for value in identities[index].wef_ids}),
                "official_urls": sorted(
                    {value for index in members for value in identities[index].official_urls}
                ),
                "linkedin_urls": sorted(
                    {value for index in members for value in identities[index].linkedin_urls}
                ),
            }
        )

    name_groups: dict[str, list[int]] = defaultdict(list)
    for index, identity in enumerate(identities):
        if identity.normalized_name:
            name_groups[identity.normalized_name].append(index)
    possible_name_only: list[dict[str, Any]] = []
    for normalized_name, members in sorted(name_groups.items()):
        roots = {union.find(index) for index in members}
        sources = {identities[index].source for index in members}
        if len(roots) > 1 and len(sources) > 1:
            possible_name_only.append(
                {
                    "normalized_name": normalized_name,
                    "names": sorted({identities[index].name for index in members}),
                    "sources": sorted(sources),
                    "components": len(roots),
                    "documents": sorted(identities[index].document_id for index in members),
                }
            )

    source_counts = Counter(identity.source for identity in identities)
    return {
        "input_people": len(identities),
        "input_people_by_source": dict(sorted(source_counts.items())),
        "reconciled_unique_people": len(components),
        "duplicates_reconciled": len(identities) - len(components),
        "strong_match_events": dict(sorted(strong_matches.items())),
        "suppressed_strong_key_collision_count": len(suppressed_strong_key_collisions),
        "suppressed_strong_key_collisions": suppressed_strong_key_collisions,
        "name_hub_match_events": name_hub_matches,
        "cross_source_components": sum(len(record["sources"]) > 1 for record in component_records),
        "overlaps_by_sources": dict(sorted(overlaps_by_sources.items())),
        "possible_name_only_overlap_count": len(possible_name_only),
        "possible_name_only_overlaps": possible_name_only,
        "components": sorted(component_records, key=lambda item: item["canonical_component_id"]),
    }


def load_people(packet_dir: Path, source: str) -> list[Identity]:
    return [
        identity_from_document(document, source)
        for document in read_packet(packet_dir)
        if document.get("dtype") == "person"
    ]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Reconcile Global Shapers identities across current API and historical packet sources."
    )
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--current-packet", type=Path, default=CURRENT_PACKET)
    parser.add_argument("--legacy-packet", type=Path, default=LEGACY_PACKET)
    parser.add_argument("--report", type=Path, default=REPORT_JSON)
    parser.add_argument("--minimum-current", type=int, default=4600)
    parser.add_argument("--minimum-legacy", type=int, default=2700)
    args = parser.parse_args()
    if args.root.resolve() != ROOT:
        raise RuntimeError(f"runner must execute from repository root {ROOT}")

    current = load_people(args.current_packet, "current-api")
    legacy = load_people(args.legacy_packet, "legacy-prefix")
    if len(current) < args.minimum_current:
        raise RuntimeError(f"current API packet has {len(current)} people; expected at least {args.minimum_current}")
    if len(legacy) < args.minimum_legacy:
        raise RuntimeError(f"legacy prefix packet has {len(legacy)} people; expected at least {args.minimum_legacy}")

    report = reconcile([*current, *legacy])
    report.update(
        {
            "status": "complete",
            "current_packet": str(args.current_packet.relative_to(ROOT)),
            "legacy_packet": str(args.legacy_packet.relative_to(ROOT)),
            "identity_policy": [
                "merge exact WEF profile identifiers",
                "merge canonical person-specific official profile URLs only",
                "merge canonical personal LinkedIn profile URLs only",
                "suppress high-fanout official/LinkedIn key collisions across distinct names",
                "merge normalized exact name plus normalized hub",
                "report exact-name-only candidates without merging them",
            ],
        }
    )
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    REPORT_MD.write_text(
        "# Global Shapers identity reconciliation\n\n"
        f"- Current API people: **{len(current):,}**\n"
        f"- Intact historical-prefix people: **{len(legacy):,}**\n"
        f"- Input person documents: **{report['input_people']:,}**\n"
        f"- Reconciled unique people: **{report['reconciled_unique_people']:,}**\n"
        f"- Cross-source duplicate identities merged: **{report['duplicates_reconciled']:,}**\n"
        f"- Cross-source components: **{report['cross_source_components']:,}**\n"
        f"- Suppressed high-fanout strong-key collisions: **{report['suppressed_strong_key_collision_count']:,}**\n"
        f"- Unmerged exact-name candidates: **{report['possible_name_only_overlap_count']:,}**\n\n"
        "Generic organization/community URLs are never identity keys. Exact-name-only candidates are deliberately not counted as duplicates without a shared hub, WEF ID, person-specific official profile URL, or personal LinkedIn URL.\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                key: report[key]
                for key in (
                    "input_people_by_source",
                    "input_people",
                    "reconciled_unique_people",
                    "duplicates_reconciled",
                    "cross_source_components",
                    "strong_match_events",
                    "suppressed_strong_key_collision_count",
                    "name_hub_match_events",
                    "possible_name_only_overlap_count",
                )
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
