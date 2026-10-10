from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "dataset"


def load_topic_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"version": 1, "excluded_source_datasets": ["daily"], "topics": []}
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: topic dataset config must be an object")
    topics = value.get("topics", [])
    if not isinstance(topics, list):
        raise ValueError(f"{path}: topics must be a list")
    seen: set[str] = set()
    for topic in topics:
        if not isinstance(topic, dict):
            raise ValueError(f"{path}: every topic must be an object")
        topic_id = slug(str(topic.get("id") or ""))
        if not topic_id:
            raise ValueError(f"{path}: topic id is required")
        if topic_id in seen:
            raise ValueError(f"{path}: duplicate topic id {topic_id}")
        seen.add(topic_id)
        topic["id"] = topic_id
        match = topic.get("match") or {}
        if isinstance(match, dict) and "ids" in match:
            ids = match["ids"]
            if not isinstance(ids, list) or any(not isinstance(item, str) or not item.strip() for item in ids):
                raise ValueError(f"{path}: topic match.ids requires non-empty exact IDs")
    return value


def excluded_source_dataset(dataset: Any, config: dict[str, Any]) -> bool:
    candidate = slug(str(dataset or ""))
    excluded = {slug(str(item)) for item in config.get("excluded_source_datasets", [])}
    return candidate in excluded


def _document_text(target: str, doc: dict[str, Any]) -> str:
    selected = {
        "target": target,
        "dataset": doc.get("dataset"),
        "title": doc.get("title"),
        "summary": doc.get("summary"),
        "description": doc.get("description"),
        "tags": doc.get("tags"),
        "labels": doc.get("labels"),
        "aliases": doc.get("aliases"),
        "keywords": doc.get("keywords"),
        "data": doc.get("data"),
        "geospatial": doc.get("geospatial"),
    }
    return json.dumps(selected, ensure_ascii=False, sort_keys=True).lower()


def _matches(topic: dict[str, Any], target: str, doc: dict[str, Any]) -> bool:
    rules = topic.get("match") or {}
    if not isinstance(rules, dict):
        return False
    target_slug = slug(target)
    dataset_slug = slug(str(doc.get("dataset") or ""))
    target_rules = [slug(str(item)) for item in rules.get("targets", [])]
    dataset_rules = [slug(str(item)) for item in rules.get("datasets", [])]
    if any(item and item in target_slug for item in target_rules):
        return True
    if any(item and item == dataset_slug for item in dataset_rules):
        return True
    text = _document_text(target, doc)
    return any(str(term).strip().lower() in text for term in rules.get("terms", []) if str(term).strip())


def topics_for_document(target: str, doc: dict[str, Any], config: dict[str, Any]) -> list[dict[str, str]]:
    matches: list[dict[str, str]] = []
    for raw in config.get("topics", []):
        if not isinstance(raw, dict) or not _matches(raw, target, doc):
            continue
        topic_id = slug(str(raw.get("id") or ""))
        matches.append(
            {
                "id": topic_id,
                "title": str(raw.get("title") or topic_id.replace("-", " ").title()),
                "subtitle": str(raw.get("subtitle") or f"Merged topical dataset for {topic_id.replace('-', ' ')}"),
            }
        )
    if not matches:
        topic_id = slug(target)
        matches = [{
            "id": topic_id,
            "title": target.replace("-", " ").title(),
            "subtitle": f"Merged dataset for all {target.replace('-', ' ')} research packets",
        }]
    included = {item["id"] for item in matches}
    identity = doc.get("id") if "schemaVersion" in doc else doc.get("_id")
    for raw in config.get("topics", []):
        if not isinstance(raw, dict):
            continue
        rules = raw.get("match") or {}
        if not isinstance(rules, dict):
            continue
        topic_id = slug(str(raw.get("id") or ""))
        if identity in rules.get("ids", []) and topic_id not in included:
            matches.append({
                "id": topic_id,
                "title": str(raw.get("title") or topic_id.replace("-", " ").title()),
                "subtitle": str(raw.get("subtitle") or f"Merged topical dataset for {topic_id.replace('-', ' ')}"),
            })
            included.add(topic_id)
    return matches
