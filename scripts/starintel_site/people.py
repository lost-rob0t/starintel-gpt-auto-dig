from __future__ import annotations

import html
import json
import os
import re
import shutil
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

from .model import discover, slug, source_record, summary

HISTORICAL_WORDS = {
    "alumni", "alumnus", "alumna", "alumnus_of", "alumni_of", "former",
    "former_member", "former_member_of", "former_fellow", "former_fellow_of",
    "past_member", "past_participant", "graduate", "graduated", "cohort",
    "class_of", "emeritus",
}
CURRENT_WORDS = {
    "member", "member_of", "works_for", "employed_by", "employee_of",
    "board_member", "trustee", "leader", "leadership", "advisor", "adviser",
    "fellow", "expert",
}
YEAR_RE = re.compile(r"\b(?:19|20)\d{2}\b")


def _latest_documents(documents: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id: dict[str, dict[str, Any]] = {}
    for document in documents:
        old = by_id.get(str(document["_id"]))
        if old is None or str(document.get("date_updated", "")) >= str(old.get("date_updated", "")):
            by_id[str(document["_id"])] = document
    return sorted(by_id.values(), key=lambda document: str(document["_id"]))


def _endpoint_ids(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        for key in ("id", "entity_id", "document_id"):
            if isinstance(value.get(key), str):
                return [value[key]]
        return []
    if isinstance(value, list):
        found: list[str] = []
        for item in value:
            found.extend(_endpoint_ids(item))
        return found
    return []


def _display_name(document: dict[str, Any] | None, fallback: str) -> str:
    if not document:
        return fallback
    data = document.get("data", {})
    return str(
        document.get("title")
        or data.get("display_name")
        or data.get("full_name")
        or data.get("name")
        or fallback
    )


def _relation_status(predicate: str, qualifiers: dict[str, Any]) -> str:
    text = " ".join(
        [predicate, *(str(key) for key in qualifiers), *(str(value) for value in qualifiers.values())]
    ).lower().replace("-", "_").replace(" ", "_")
    if any(word in text for word in HISTORICAL_WORDS):
        return "alumni"
    if qualifiers.get("active") is False or qualifiers.get("current") is False:
        return "alumni"
    return "current" if any(word in text for word in CURRENT_WORDS) else "related"


def _qualifier_value(qualifiers: dict[str, Any], keys: tuple[str, ...]) -> str:
    for key in keys:
        value = qualifiers.get(key)
        if value not in (None, "", [], {}):
            if isinstance(value, list):
                return ", ".join(str(item) for item in value)
            return str(value)
    return ""


def _years(*values: Any) -> list[str]:
    found: set[str] = set()
    for value in values:
        for year in YEAR_RE.findall(json.dumps(value, ensure_ascii=False)):
            found.add(year)
    return sorted(found)


def _source_rows(documents: Iterable[dict[str, Any]]) -> list[dict[str, str]]:
    rows: dict[str, dict[str, str]] = {}
    for document in documents:
        for raw in document.get("sources", []):
            source = source_record(raw)
            url = str(source.get("url") or source.get("uri") or "")
            title = str(source.get("title") or source.get("publisher") or url or "Source")
            key = url or json.dumps(source, ensure_ascii=False, sort_keys=True)
            rows[key] = {"title": title, "url": url}
    return sorted(rows.values(), key=lambda row: row["title"].lower())


def _page(title: str, body: str, *, prefix: str) -> str:
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="dark light"><title>{html.escape(title)}</title>
<link rel="stylesheet" href="{prefix}assets/style.css">
<link rel="stylesheet" href="{prefix}assets/people.css">
<script src="{prefix}assets/theme.js"></script></head><body>
<header><a class="brand" href="{prefix}index.html">StarIntel GPT Auto Dig</a>
<nav><a href="{prefix}index.html">Research</a><a href="{prefix}people/index.html">People</a></nav></header>
<main>{body}</main><footer>Generated from canonical StarIntel v0.9.0 data.</footer>
</body></html>"""


def _membership_rows(
    person_id: str,
    relations: list[dict[str, Any]],
    by_id: dict[str, dict[str, Any]],
    document_targets: dict[str, set[str]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for relation in relations:
        data = relation.get("data", {})
        subjects = _endpoint_ids(data.get("subject"))
        objects = _endpoint_ids(data.get("object"))
        if person_id not in subjects and person_id not in objects:
            continue
        outward = person_id in subjects
        counterpart_ids = objects if outward else subjects
        predicate = str(data.get("predicate") or data.get("relation_type") or "related_to")
        qualifiers = data.get("qualifiers") if isinstance(data.get("qualifiers"), dict) else {}
        for counterpart_id in counterpart_ids:
            if counterpart_id == person_id:
                continue
            counterpart = by_id.get(counterpart_id)
            status = _relation_status(predicate, qualifiers)
            years = _years(
                qualifiers,
                data.get("start_at"),
                data.get("end_at"),
                relation.get("temporal"),
                relation.get("title"),
            )
            rows.append(
                {
                    "relation_id": relation["_id"],
                    "predicate": predicate,
                    "predicate_label": predicate.replace("_", " ").replace("-", " "),
                    "direction": "outbound" if outward else "inbound",
                    "organization_id": counterpart_id,
                    "organization": _display_name(counterpart, counterpart_id),
                    "organization_dtype": counterpart.get("dtype", "") if counterpart else "",
                    "status": status,
                    "program": _qualifier_value(qualifiers, ("program", "program_name", "initiative", "chapter")),
                    "cohort": _qualifier_value(qualifiers, ("cohort", "class", "class_year", "cohort_year")),
                    "role": _qualifier_value(qualifiers, ("role", "title", "position", "capacity")),
                    "region": _qualifier_value(qualifiers, ("region", "location", "country", "chapter")),
                    "years": years,
                    "datasets": sorted(
                        {
                            str(relation.get("dataset") or ""),
                            *(document_targets.get(str(relation["_id"]), set())),
                        }
                        - {""}
                    ),
                    "sources": _source_rows([relation]),
                }
            )
    rows.sort(
        key=lambda row: (
            row["status"] != "current",
            row["organization"].lower(),
            row["predicate_label"],
            row["cohort"],
        )
    )
    return rows


def _person_record(
    person: dict[str, Any],
    relations: list[dict[str, Any]],
    by_id: dict[str, dict[str, Any]],
    document_targets: dict[str, set[str]],
) -> dict[str, Any]:
    person_id = str(person["_id"])
    data = person.get("data", {})
    memberships = _membership_rows(person_id, relations, by_id, document_targets)
    datasets = sorted(
        {
            str(person.get("dataset") or ""),
            *(document_targets.get(person_id, set())),
            *(dataset for membership in memberships for dataset in membership["datasets"]),
        }
        - {""}
    )
    organizations = sorted(
        {
            membership["organization"]
            for membership in memberships
            if membership["organization_dtype"] in {"org", "event", "product", "entity"}
            or membership["organization_id"].startswith("starintel:org:")
        }
    )
    statuses = sorted({membership["status"] for membership in memberships}) or ["profile"]
    years = sorted({year for membership in memberships for year in membership["years"]})
    roles: list[str] = []
    for key in ("public_roles", "positions", "occupations", "employers", "professional_affiliations"):
        value = data.get(key)
        if isinstance(value, str):
            roles.append(value)
        elif isinstance(value, list):
            roles.extend(str(item) for item in value if item)
    roles = list(dict.fromkeys(roles))
    name = _display_name(person, person_id)
    aliases = [str(item) for item in person.get("aliases", []) if item]
    relation_ids = {membership["relation_id"] for membership in memberships}
    sources = _source_rows([person, *(relation for relation in relations if str(relation["_id"]) in relation_ids)])
    return {
        "id": person_id,
        "name": name,
        "bio": summary(person),
        "aliases": aliases,
        "roles": roles,
        "datasets": datasets,
        "organizations": organizations,
        "statuses": statuses,
        "years": years,
        "memberships": memberships,
        "verification": str(person.get("verification", {}).get("status") or "unverified"),
        "confidence": person.get("assessment", {}).get("confidence"),
        "source_count": len(sources),
        "sources": sources,
        "updated": str(person.get("date_updated") or ""),
        "person_document": person,
        "url": f"{slug(person_id)}.html",
    }


def _option(values: Iterable[str], label: str) -> str:
    items = [f'<option value="">{html.escape(label)}</option>']
    items.extend(f'<option value="{html.escape(value.lower())}">{html.escape(value)}</option>' for value in values)
    return "".join(items)


def _directory_page(records: list[dict[str, Any]]) -> str:
    datasets = sorted({item for record in records for item in record["datasets"]}, key=str.lower)
    organizations = sorted({item for record in records for item in record["organizations"]}, key=str.lower)
    statuses = sorted({item for record in records for item in record["statuses"]}, key=str.lower)
    cards: list[str] = []
    for record in records:
        initials = "".join(part[0] for part in record["name"].split()[:2] if part).upper() or "?"
        meta = " · ".join(
            item
            for item in (
                f'{len(record["memberships"])} relations' if record["memberships"] else None,
                f'{record["source_count"]} sources',
                ", ".join(record["years"][-3:]) if record["years"] else None,
            )
            if item
        )
        cards.append(
            f"""<article class="person-card"
 data-search="{html.escape(' '.join([record['name'], record['bio'], *record['aliases'], *record['roles']]).lower())}"
 data-datasets="{html.escape('|'.join(item.lower() for item in record['datasets']))}"
 data-organizations="{html.escape('|'.join(item.lower() for item in record['organizations']))}"
 data-statuses="{html.escape('|'.join(item.lower() for item in record['statuses']))}"
 data-years="{html.escape('|'.join(record['years']))}">
<div class="person-avatar" aria-hidden="true">{html.escape(initials)}</div>
<div class="person-card-body"><span>{html.escape(' / '.join(record['statuses']))}</span>
<h2><a href="{html.escape(record['url'])}">{html.escape(record['name'])}</a></h2>
<p>{html.escape(record['bio'])}</p><small>{html.escape(meta)}</small></div></article>"""
        )
    body = (
        '<div class="crumb"><a href="../index.html">← Research index</a></div>'
        "<h1>People directory</h1>"
        '<p class="lede">Canonical people across every AutoDig dataset, with current roles, alumni cohorts, historical memberships, and source-backed profile summaries.</p>'
        '<div class="directory-actions"><a href="people.json" download>Download directory JSON</a></div>'
        '<section class="stats people-stats">'
        f'<div><strong>{len(records):,}</strong><span>people</span></div>'
        f'<div><strong>{sum("alumni" in record["statuses"] for record in records):,}</strong><span>alumni profiles</span></div>'
        f'<div><strong>{len(organizations):,}</strong><span>organizations</span></div>'
        f'<div><strong>{sum(record["source_count"] for record in records):,}</strong><span>source links</span></div></section>'
        '<section class="people-controls" aria-label="Directory filters">'
        '<label>Search<input id="people-search" type="search" placeholder="Name, role, bio, alias"></label>'
        f'<label>Status<select id="people-status">{_option(statuses, "All statuses")}</select></label>'
        f'<label>Dataset<select id="people-dataset">{_option(datasets, "All datasets")}</select></label>'
        f'<label>Organization<select id="people-organization">{_option(organizations, "All organizations")}</select></label>'
        '<label>Year<input id="people-year" inputmode="numeric" placeholder="2024"></label>'
        '</section>'
        '<p id="people-result-count" class="people-result-count"></p>'
        '<section id="people-grid" class="people-grid">'
        + "".join(cards)
        + "</section>"
        '<p id="people-empty" class="people-empty" hidden>No matching people.</p>'
        '<script src="../assets/people.js"></script>'
    )
    return _page("People directory", body, prefix="../")


def _membership_table(record: dict[str, Any]) -> str:
    if not record["memberships"]:
        return "<p>No normalized organization relation has been recorded yet.</p>"
    rows = []
    for membership in record["memberships"]:
        detail = " · ".join(
            item
            for item in (
                membership["program"],
                f'cohort {membership["cohort"]}' if membership["cohort"] else "",
                ", ".join(membership["years"]),
                membership["role"],
                membership["region"],
            )
            if item
        )
        sources = " ".join(
            f'<a href="{html.escape(source["url"])}">{html.escape(source["title"])}</a>'
            if source["url"]
            else html.escape(source["title"])
            for source in membership["sources"][:3]
        )
        rows.append(
            "<tr>"
            f'<td><span class="status-pill status-{html.escape(membership["status"])}">{html.escape(membership["status"])}</span></td>'
            f'<td>{html.escape(membership["organization"])}</td>'
            f'<td>{html.escape(membership["predicate_label"])}</td>'
            f'<td>{html.escape(detail or "—")}</td>'
            f'<td>{sources or "—"}</td>'
            "</tr>"
        )
    return (
        '<div class="table-wrap"><table><thead><tr><th>Status</th><th>Organization / program</th>'
        "<th>Relation</th><th>Cohort / role</th><th>Sources</th></tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table></div>"
    )


def _bio_page(record: dict[str, Any], document_targets: dict[str, set[str]]) -> str:
    person = record["person_document"]
    person_id = record["id"]
    badges = "".join(
        f'<span class="badge">{html.escape(item)}</span>'
        for item in [*record["statuses"], record["verification"], *(f"cohort {year}" for year in record["years"][-3:])]
        if item
    )
    target_links = []
    for target in sorted(document_targets.get(person_id, set())):
        target_links.append(
            f'<a class="dataset-link" href="../{html.escape(target)}/nodes/{slug(person_id)}.html">{html.escape(target.replace("-", " ").title())}</a>'
        )
    roles = "".join(f"<li>{html.escape(role)}</li>" for role in record["roles"])
    aliases = ", ".join(record["aliases"]) or "None recorded"
    source_items = "".join(
        f'<li><a href="{html.escape(source["url"])}">{html.escape(source["title"])}</a></li>'
        if source["url"]
        else f"<li>{html.escape(source['title'])}</li>"
        for source in record["sources"]
    )
    confidence = record["confidence"]
    body = (
        '<div class="crumb"><a href="index.html">← People directory</a></div>'
        '<article class="person-profile">'
        f'<div class="person-profile-heading"><div><h1>{html.escape(record["name"])}</h1>'
        f'<div class="badges">{badges}</div></div></div>'
        f'<p class="lede">{html.escape(record["bio"])}</p>'
        '<section class="profile-summary">'
        f'<div><span>StarIntel ID</span><code>{html.escape(person_id)}</code></div>'
        f'<div><span>Datasets</span><strong>{len(record["datasets"])}</strong></div>'
        f'<div><span>Sources</span><strong>{record["source_count"]}</strong></div>'
        f'<div><span>Confidence</span><strong>{html.escape(str(confidence if confidence is not None else "unassigned"))}</strong></div>'
        "</section>"
        '<section><h2>Membership and alumni history</h2>'
        + _membership_table(record)
        + "</section>"
        '<section class="profile-columns"><div><h2>Public roles</h2>'
        + (f"<ul>{roles}</ul>" if roles else "<p>No public roles recorded.</p>")
        + f'</div><div><h2>Aliases</h2><p>{html.escape(aliases)}</p>'
        + '<h2>Dataset records</h2><div class="dataset-links">'
        + ("".join(target_links) if target_links else "<span>No packet location recorded.</span>")
        + "</div></div></section>"
        '<section><h2>Sources</h2><ul class="sources">'
        + (source_items or "<li>No source attached.</li>")
        + "</ul></section>"
        '<details><summary>Canonical person document</summary><pre>'
        + html.escape(json.dumps(person, ensure_ascii=False, indent=2))
        + "</pre></details></article>"
    )
    return _page(record["name"], body, prefix="../")


def _inject_navigation(output: Path) -> None:
    for path in output.rglob("*.html"):
        if path.parent == output / "people":
            continue
        markup = path.read_text(encoding="utf-8")
        if ">People</a>" in markup or "</nav>" not in markup:
            continue
        people_path = os.path.relpath(output / "people" / "index.html", path.parent).replace(os.sep, "/")
        markup = markup.replace("</nav>", f'<a href="{html.escape(people_path)}">People</a></nav>', 1)
        path.write_text(markup, encoding="utf-8")


def _inject_root_launch(output: Path, count: int) -> None:
    index = output / "index.html"
    if not index.is_file():
        return
    markup = index.read_text(encoding="utf-8")
    if 'href="people/index.html"' not in markup:
        marker = '<section class="stats dashboard-stats">'
        launch = (
            '<div class="notice"><strong>People directory:</strong> '
            f'{count:,} canonical people with sourced bios, organizations, cohorts, and alumni history. '
            '<a href="people/index.html">Browse people →</a></div>'
        )
        markup = markup.replace(marker, launch + marker, 1)
        index.write_text(markup, encoding="utf-8")


def build_people_directory(input_root: Path, output: Path, assets: Path) -> dict[str, Any]:
    packets = discover(input_root)
    document_targets: dict[str, set[str]] = defaultdict(set)
    all_documents: list[dict[str, Any]] = []
    for packet in packets:
        for document in packet.documents:
            document_targets[str(document["_id"])].add(packet.target)
            all_documents.append(document)

    documents = _latest_documents(all_documents)
    by_id = {str(document["_id"]): document for document in documents}
    relations = [document for document in documents if document.get("dtype") == "relation"]
    people = [document for document in documents if document.get("dtype") == "person"]
    records = [_person_record(person, relations, by_id, document_targets) for person in people]
    records.sort(key=lambda record: record["name"].lower())

    people_output = output / "people"
    if people_output.exists():
        shutil.rmtree(people_output)
    people_output.mkdir(parents=True)
    asset_output = output / "assets"
    asset_output.mkdir(exist_ok=True)
    shutil.copy2(assets / "people.css", asset_output / "people.css")
    shutil.copy2(assets / "people.js", asset_output / "people.js")

    serializable = [{key: value for key, value in record.items() if key != "person_document"} for record in records]
    (people_output / "people.json").write_text(
        json.dumps(serializable, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (people_output / "index.html").write_text(_directory_page(records), encoding="utf-8")
    for record in records:
        (people_output / record["url"]).write_text(_bio_page(record, document_targets), encoding="utf-8")

    _inject_navigation(output)
    _inject_root_launch(output, len(records))
    return {
        "people": len(records),
        "alumni": sum("alumni" in record["statuses"] for record in records),
        "organizations": len({item for record in records for item in record["organizations"]}),
        "output": str(people_output),
    }
