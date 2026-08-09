from __future__ import annotations

import html
from collections import Counter, defaultdict
from datetime import date, timedelta
from typing import Any
from urllib.parse import urlparse

from .dashboard import review_state
from .model import source_record, summary
from .render import page

FINDING_DTYPES = {"claim", "analysis", "research-pass"}


def _date(value: Any) -> date | None:
    text = str(value or "")[:10]
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def _endpoint_ids(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict) and isinstance(value.get("id"), str):
        return [value["id"]]
    if isinstance(value, list):
        out: list[str] = []
        for item in value:
            out.extend(_endpoint_ids(item))
        return out
    return []


def _source_key(raw: Any) -> str:
    source = source_record(raw)
    return str(source.get("url") or source.get("uri") or source.get("title") or source)


def dataset_metrics(docs: list[dict[str, Any]]) -> dict[str, int | str]:
    counts = Counter(str(doc.get("dtype") or "unknown") for doc in docs)
    sources = {_source_key(raw) for doc in docs for raw in doc.get("sources", [])}
    latest = max((_date(doc.get("date_added")) for doc in docs), default=None)
    latest = latest or max((_date(doc.get("date_updated")) for doc in docs), default=None)
    cutoff = latest - timedelta(days=29) if latest else None
    added_30d = sum(
        1
        for doc in docs
        if cutoff is not None and (added := _date(doc.get("date_added"))) is not None and added >= cutoff
    )
    return {
        "record_count": len(docs),
        "people_count": counts.get("person", 0),
        "organization_count": counts.get("org", 0),
        "relation_count": counts.get("relation", 0),
        "source_count": len(sources),
        "added_30d": added_30d,
        "updated_through": max((str(doc.get("date_updated") or "") for doc in docs), default=""),
    }


def _top_connected_people(docs: list[dict[str, Any]], url_by_id: dict[str, str]) -> list[dict[str, Any]]:
    people = {
        doc["_id"]: str(doc.get("title") or (doc.get("data") or {}).get("name") or doc["_id"])
        for doc in docs
        if doc.get("dtype") == "person"
    }
    degrees: Counter[str] = Counter()
    datasets: dict[str, set[str]] = defaultdict(set)
    predicates: dict[str, Counter[str]] = defaultdict(Counter)
    for doc in docs:
        if doc.get("dtype") != "relation" or review_state(doc) != "reviewed":
            continue
        data = doc.get("data") or {}
        endpoints = list(dict.fromkeys(_endpoint_ids(data.get("subject")) + _endpoint_ids(data.get("object"))))
        predicate = str(data.get("predicate") or "related to").replace("_", " ")
        for endpoint in endpoints:
            if endpoint not in people:
                continue
            others = max(1, len(endpoints) - 1)
            degrees[endpoint] += others
            datasets[endpoint].add(str(doc.get("dataset") or "unknown"))
            predicates[endpoint][predicate] += 1
    rows = []
    for person_id, degree in degrees.most_common(12):
        rows.append(
            {
                "id": person_id,
                "name": people[person_id],
                "connections": degree,
                "dataset_count": len(datasets[person_id]),
                "relations": [
                    {"label": label, "count": count}
                    for label, count in predicates[person_id].most_common(3)
                ],
                "url": url_by_id.get(person_id, ""),
            }
        )
    return rows


def _confidence(doc: dict[str, Any]) -> float:
    raw = (doc.get("assessment") or {}).get("confidence")
    if not isinstance(raw, (int, float)):
        return 0.0
    value = float(raw)
    return max(0.0, min(1.0, value / 100.0 if value > 1 else value))


def _top_findings(docs: list[dict[str, Any]], url_by_id: dict[str, str]) -> list[dict[str, Any]]:
    rows = []
    for doc in docs:
        if doc.get("dtype") not in FINDING_DTYPES or review_state(doc) != "reviewed":
            continue
        sources = {_source_key(raw) for raw in doc.get("sources", [])}
        evidence_count = len(doc.get("evidence") or [])
        confidence = _confidence(doc)
        related_count = len(doc.get("related_ids") or [])
        score = evidence_count * 4 + len(sources) * 3 + confidence * 10 + min(related_count, 10)
        if score <= 0:
            continue
        title = str(doc.get("title") or (doc.get("data") or {}).get("claim") or doc["_id"])
        reasons = []
        if evidence_count:
            reasons.append(f"{evidence_count} evidence")
        if sources:
            reasons.append(f"{len(sources)} sources")
        if confidence:
            reasons.append(f"{confidence:.0%} confidence")
        if related_count:
            reasons.append(f"{related_count} linked records")
        rows.append(
            {
                "id": doc["_id"],
                "title": title,
                "summary": summary(doc),
                "dtype": doc.get("dtype"),
                "score": round(score, 3),
                "reason": " · ".join(reasons) or "reviewed finding",
                "url": url_by_id.get(doc["_id"], ""),
            }
        )
    rows.sort(key=lambda row: (-float(row["score"]), str(row["title"]).lower()))
    return rows[:8]


def _source_domains(docs: list[dict[str, Any]]) -> tuple[int, list[dict[str, Any]]]:
    sources: set[str] = set()
    domains: Counter[str] = Counter()
    for doc in docs:
        for raw in doc.get("sources", []):
            source = source_record(raw)
            key = _source_key(raw)
            if not key or key in sources:
                continue
            sources.add(key)
            url = str(source.get("url") or source.get("uri") or "")
            domain = urlparse(url).hostname or str(source.get("publisher") or "other")
            domains[domain.removeprefix("www.").lower()] += 1
    return len(sources), [{"label": label, "count": count} for label, count in domains.most_common(8)]


def dashboard_projection(
    docs: list[dict[str, Any]],
    catalog: list[dict[str, Any]],
    search_records: list[dict[str, Any]],
) -> dict[str, Any]:
    url_by_id = {str(record["id"]): str(record["url"]) for record in search_records}
    by_day: Counter[str] = Counter()
    dtypes: Counter[str] = Counter()
    relations: Counter[str] = Counter()
    for doc in docs:
        day = str(doc.get("date_added") or "")[:10]
        if day:
            by_day[day] += 1
        dtype = str(doc.get("dtype") or "unknown")
        if dtype == "relation":
            predicate = str((doc.get("data") or {}).get("predicate") or "related to").replace("_", " ")
            relations[predicate] += 1
        else:
            dtypes[dtype] += 1

    source_count, source_domains = _source_domains(docs)
    latest = sorted(
        (doc for doc in docs if review_state(doc) == "reviewed"),
        key=lambda doc: (str(doc.get("date_updated") or ""), str(doc.get("_id") or "")),
        reverse=True,
    )[:10]
    active = sorted(
        catalog,
        key=lambda row: (
            -int(row.get("added_30d") or 0),
            -int(row.get("record_count") or 0),
            str(row.get("title") or row.get("dataset") or "").lower(),
        ),
    )[:8]
    counts = Counter(str(doc.get("dtype") or "unknown") for doc in docs)
    return {
        "version": 1,
        "generated_at": max((str(doc.get("date_updated") or "") for doc in docs), default=""),
        "summary": {
            "documents": len(docs),
            "people": counts.get("person", 0),
            "organizations": counts.get("org", 0),
            "relations": counts.get("relation", 0),
            "datasets": len(catalog),
            "sources": source_count,
            "updated_through": max((str(doc.get("date_updated") or "") for doc in docs), default=""),
        },
        "documents_by_day": [{"date": day, "count": count} for day, count in sorted(by_day.items())],
        "document_types": [{"label": label, "count": count} for label, count in dtypes.most_common()],
        "relation_types": [{"label": label, "count": count} for label, count in relations.most_common()],
        "top_connected_people": _top_connected_people(docs, url_by_id),
        "top_findings": _top_findings(docs, url_by_id),
        "source_domains": source_domains,
        "active_datasets": active,
        "latest_activity": [
            {
                "id": doc["_id"],
                "title": str(doc.get("title") or (doc.get("data") or {}).get("name") or doc["_id"]),
                "dtype": doc.get("dtype"),
                "updated": doc.get("date_updated", ""),
                "url": url_by_id.get(doc["_id"], ""),
            }
            for doc in latest
        ],
    }


def _metric(value: Any, label: str) -> str:
    return f'<div class="corpus-metric"><strong>{html.escape(f"{int(value):,}")}</strong><span>{html.escape(label)}</span></div>'


def _fallback_table(rows: list[dict[str, Any]], label_key: str = "label") -> str:
    return (
        '<div class="chart-fallback"><table><thead><tr><th>Category</th><th>Count</th></tr></thead><tbody>'
        + "".join(
            f'<tr><td>{html.escape(str(row.get(label_key, "")))}</td><td>{int(row.get("count") or 0):,}</td></tr>'
            for row in rows[:16]
        )
        + "</tbody></table></div>"
    )


def root_dashboard_page(projection: dict[str, Any], site_title: str) -> str:
    summary_data = projection["summary"]
    people = projection["top_connected_people"]
    findings = projection["top_findings"]
    active = projection["active_datasets"]
    activity = projection["latest_activity"]
    source_domains = projection["source_domains"]
    body = f'''
    <div id="corpus-dashboard" class="corpus-dashboard" data-dashboard="dashboard-data.json">
      <section class="corpus-hero">
        <div><span class="eyebrow">StarIntel corpus / live projection</span><h1>Follow the evidence.<br>See the network move.</h1>
        <p class="lede">A source-backed view across the public StarIntel corpus. Start with the pulse, drill into the datasets, then go as deep as the graph.</p></div>
        <div class="corpus-status"><span>Updated through</span><strong>{html.escape(str(summary_data["updated_through"])[:10])}</strong><a href="downloads/starintel-complete-corpus.jsonl" download>Download corpus ↘</a></div>
      </section>
      <section class="corpus-metrics" aria-label="Corpus totals">
        {_metric(summary_data["documents"], "records")}{_metric(summary_data["people"], "people")}{_metric(summary_data["organizations"], "organizations")}{_metric(summary_data["relations"], "relations")}{_metric(summary_data["datasets"], "datasets")}{_metric(summary_data["sources"], "sources")}
      </section>
      <section class="dashboard-primary-grid">
        <article class="chart-surface chart-surface-wide">
          <div class="section-head"><div><span class="eyebrow">Corpus pulse</span><h2>Documents added by day</h2></div><div class="range-switch" role="group" aria-label="Chart date range"><button data-range="30">30d</button><button data-range="90" class="active">90d</button><button data-range="365">1y</button><button data-range="all">All</button></div></div>
          <div id="documents-by-day-chart" class="chart-frame" aria-label="Documents added by day chart"></div>
          {_fallback_table(projection["documents_by_day"][-14:], "date")}
        </article>
        <aside class="corpus-sidecar"><span class="eyebrow">Evidence base</span><strong>{int(summary_data["sources"]):,}</strong><h2>unique sources</h2><ol class="domain-list">{''.join(f'<li><span>{html.escape(str(row["label"]))}</span><strong>{int(row["count"]):,}</strong></li>' for row in source_domains)}</ol></aside>
      </section>
      <section class="dashboard-chart-grid">
        <article class="chart-surface"><span class="eyebrow">Corpus composition</span><h2>Document types</h2><p>Relations are intentionally excluded.</p><div id="document-types-chart" class="chart-frame chart-frame-square"></div>{_fallback_table(projection["document_types"])}</article>
        <article class="chart-surface"><span class="eyebrow">Network grammar</span><h2>Relation types</h2><p>The connection types shaping the graph.</p><div id="relation-types-chart" class="chart-frame"></div>{_fallback_table(projection["relation_types"])}</article>
      </section>
      <section class="dashboard-rank-grid">
        <article><div class="section-head"><div><span class="eyebrow">Reviewed graph</span><h2>Top connected people</h2></div><a href="datasets.html">Browse datasets →</a></div><ol class="people-rank">{''.join(_person_row(row, index + 1) for index, row in enumerate(people)) or '<li>No reviewed person relations yet.</li>'}</ol></article>
        <article><div class="section-head"><div><span class="eyebrow">Evidence-backed</span><h2>Top findings</h2></div></div><ol class="finding-rank">{''.join(_finding_row(row, index + 1) for index, row in enumerate(findings)) or '<li>No reviewed findings met the ranking threshold.</li>'}</ol></article>
      </section>
      <section class="dashboard-rank-grid dashboard-lower">
        <article><div class="section-head"><div><span class="eyebrow">Growing now</span><h2>Active datasets</h2></div><a class="primary-action" href="datasets.html">All datasets →</a></div><ol class="dataset-rank">{''.join(_dataset_row(row) for row in active)}</ol></article>
        <article><div class="section-head"><div><span class="eyebrow">Fresh evidence</span><h2>Latest activity</h2></div></div><ol class="activity-rank">{''.join(_activity_row(row) for row in activity)}</ol></article>
      </section>
    </div>'''
    return page(site_title, body)


def _person_row(row: dict[str, Any], rank: int) -> str:
    relations = ", ".join(f'{item["label"]} {item["count"]}' for item in row.get("relations", []))
    name = html.escape(str(row.get("name") or row.get("id")))
    url = html.escape(str(row.get("url") or ""), quote=True)
    title = f'<a href="{url}">{name}</a>' if url else name
    return f'<li><span class="rank-number">{rank:02d}</span><div><strong>{title}</strong><small>{html.escape(relations or "reviewed relations")}</small></div><b>{int(row.get("connections") or 0):,}</b></li>'


def _finding_row(row: dict[str, Any], rank: int) -> str:
    title = html.escape(str(row.get("title") or row.get("id")))
    url = html.escape(str(row.get("url") or ""), quote=True)
    title_markup = f'<a href="{url}">{title}</a>' if url else title
    return f'<li><span class="rank-number">{rank:02d}</span><div><strong>{title_markup}</strong><p>{html.escape(str(row.get("summary") or ""))}</p><small>{html.escape(str(row.get("reason") or "reviewed"))}</small></div></li>'


def _dataset_row(row: dict[str, Any]) -> str:
    title = html.escape(str(row.get("title") or row.get("dataset") or row.get("id")))
    url = html.escape(str(row.get("url") or ""), quote=True)
    return f'<li><div><strong><a href="{url}">{title}</a></strong><small>{html.escape(str(row.get("kind") or "dataset"))} · {int(row.get("source_count") or 0):,} sources</small></div><span><b>{int(row.get("record_count") or 0):,}</b> records<br><small>+{int(row.get("added_30d") or 0):,} / 30d</small></span></li>'


def _activity_row(row: dict[str, Any]) -> str:
    title = html.escape(str(row.get("title") or row.get("id")))
    url = html.escape(str(row.get("url") or ""), quote=True)
    title_markup = f'<a href="{url}">{title}</a>' if url else title
    return f'<li><time>{html.escape(str(row.get("updated") or "")[:10])}</time><div><strong>{title_markup}</strong><small>{html.escape(str(row.get("dtype") or "record"))}</small></div></li>'


def datasets_page(catalog: list[dict[str, Any]], site_title: str) -> str:
    topic_count = sum(row.get("kind") == "topic" for row in catalog)
    source_count = sum(row.get("kind") == "source" for row in catalog)
    cards_icon = '<svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>'
    table_icon = '<svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="16" rx="1"/><path d="M3 9h18M3 14h18M9 4v16M15 4v16"/></svg>'
    body = f'''
    <div id="dataset-browser" class="dataset-browser" data-catalog="dataset-catalog.json">
      <section class="dataset-hero"><div><span class="eyebrow">Corpus catalog</span><h1>Datasets</h1><p class="lede">Every generated topic dataset and source dataset in one place. Filter it, sort it, then open the dataset view you need.</p></div><div class="dataset-totals"><strong>{len(catalog):,}</strong><span>datasets</span><small>{topic_count:,} topic · {source_count:,} source</small></div></section>
      <section class="dataset-toolbar" aria-label="Dataset controls">
        <input id="dataset-search" type="search" placeholder="Search datasets or research targets…" autocomplete="off">
        <div class="segmented" role="group" aria-label="Dataset class"><button type="button" class="active" data-kind="all" aria-pressed="true">All</button><button type="button" data-kind="topic" aria-pressed="false">Topic</button><button type="button" data-kind="source" aria-pressed="false">Source</button></div>
        <select id="dataset-sort" aria-label="Sort datasets"><option value="activity">Recent growth</option><option value="records">Record count</option><option value="sources">Source count</option><option value="updated">Recently updated</option><option value="name">Name</option></select>
        <div class="segmented" role="group" aria-label="Dataset view"><button type="button" class="active icon-only-toggle" data-view="cards" aria-label="Card view" title="Card view" aria-pressed="true">{cards_icon}</button><button type="button" class="icon-only-toggle" data-view="table" aria-label="Table view" title="Table view" aria-pressed="false">{table_icon}</button></div>
      </section>
      <div id="dataset-summary" class="dataset-summary">Loading dataset catalog…</div>
      <section id="dataset-card-grid" class="dataset-card-grid" aria-live="polite"></section>
      <div id="dataset-table-wrap" class="dataset-table-wrap" hidden><table class="dataset-table"><thead><tr><th>Dataset</th><th>Class</th><th>Records</th><th>People</th><th>Orgs</th><th>Relations</th><th>Sources</th><th>+30d</th><th>Updated</th><th></th></tr></thead><tbody id="dataset-table-body"></tbody></table></div>
      <noscript><p>JavaScript is required for interactive filtering. <a href="dataset-catalog.json">Open the generated catalog JSON.</a></p></noscript>
    </div>'''
    return page(f"Datasets · {site_title}", body)