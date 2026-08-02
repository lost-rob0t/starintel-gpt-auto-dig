#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path('.')
OLD = Path('/tmp/pr105-old')
DATASETS = {'rand', 'bilderberg'}


def read_document(path: Path) -> dict[str, Any] | None:
    try:
        lines = [line for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
        if len(lines) != 1:
            return None
        value = json.loads(lines[0])
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def canonical(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n'


def item_key(value: Any) -> str:
    if isinstance(value, dict):
        for key in ('source_id', '_id', 'id', 'uri', 'url', 'value'):
            candidate = value.get(key)
            if candidate not in (None, ''):
                return f'{key}:{candidate}'
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


conflicts: list[str] = []


def merge_value(current: Any, incoming: Any, path: str) -> Any:
    if current in (None, '', [], {}) and incoming not in (None, '', [], {}):
        return copy.deepcopy(incoming)
    if isinstance(current, dict) and isinstance(incoming, dict):
        result = copy.deepcopy(current)
        for key, value in incoming.items():
            child = f'{path}.{key}' if path else key
            if key not in result:
                result[key] = copy.deepcopy(value)
            else:
                result[key] = merge_value(result[key], value, child)
        return result
    if isinstance(current, list) and isinstance(incoming, list):
        result = copy.deepcopy(current)
        seen = {item_key(value) for value in result}
        for value in incoming:
            marker = item_key(value)
            if marker not in seen:
                result.append(copy.deepcopy(value))
                seen.add(marker)
        return result
    if current != incoming and incoming not in (None, '', [], {}):
        conflicts.append(path)
    return current


def main() -> int:
    main_by_id: dict[str, tuple[Path, dict[str, Any]]] = {}
    for path in ROOT.glob('db/**/*.ndjson'):
        document = read_document(path)
        if document and document.get('dataset') in DATASETS and document.get('_id'):
            main_by_id[str(document['_id'])] = (path, document)

    old_by_id: dict[str, tuple[Path, dict[str, Any]]] = {}
    for path in OLD.glob('db/**/*.ndjson'):
        document = read_document(path)
        if document and document.get('dataset') in DATASETS and document.get('_id'):
            old_by_id[str(document['_id'])] = (path, document)

    added = 0
    enriched = 0
    unchanged = 0
    dtype_counts: Counter[str] = Counter()
    written: list[str] = []

    for doc_id, (old_path, old_document) in sorted(old_by_id.items()):
        existing = main_by_id.get(doc_id)
        if existing is None:
            relative = old_path.relative_to(OLD)
            target = ROOT / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(canonical(old_document), encoding='utf-8')
            added += 1
            dtype_counts[str(old_document.get('dtype', 'unknown'))] += 1
            written.append(str(relative))
            continue

        current_path, current_document = existing
        merged = merge_value(current_document, old_document, doc_id)
        if canonical(merged) == canonical(current_document):
            unchanged += 1
            continue
        current_path.write_text(canonical(merged), encoding='utf-8')
        enriched += 1
        dtype_counts[str(merged.get('dtype', 'unknown'))] += 1
        written.append(str(current_path))

    main_config_path = ROOT / 'config/dark-academia-targets.json'
    old_config_path = OLD / 'config/dark-academia-targets.json'
    config_updates: list[str] = []
    if main_config_path.exists() and old_config_path.exists():
        main_config = json.loads(main_config_path.read_text(encoding='utf-8'))
        old_config = json.loads(old_config_path.read_text(encoding='utf-8'))
        main_targets = main_config.get('targets', [])
        old_targets = {
            str(target.get('dataset')): target
            for target in old_config.get('targets', [])
            if isinstance(target, dict) and target.get('dataset') in DATASETS
        }
        for index, target in enumerate(main_targets):
            if not isinstance(target, dict):
                continue
            dataset = str(target.get('dataset', ''))
            incoming = old_targets.get(dataset)
            if incoming is None:
                continue
            merged_target = copy.deepcopy(target)
            for key, value in incoming.items():
                merged_target[key] = copy.deepcopy(value)
            if merged_target != target:
                main_targets[index] = merged_target
                config_updates.append(dataset)
        main_config['targets'] = main_targets
        main_config_path.write_text(
            json.dumps(main_config, ensure_ascii=False, indent=2, sort_keys=True) + '\n',
            encoding='utf-8',
        )

    report = {
        'source_pr': 105,
        'source_archive': 'archive/pr-105-pre-takeover-f8035f2',
        'datasets': sorted(DATASETS),
        'old_documents_considered': len(old_by_id),
        'main_documents_before': len(main_by_id),
        'documents_added': added,
        'documents_enriched': enriched,
        'documents_unchanged': unchanged,
        'written_dtype_counts': dict(sorted(dtype_counts.items())),
        'config_targets_updated': sorted(config_updates),
        'scalar_conflicts_kept_from_main': len(set(conflicts)),
        'sample_conflict_paths': sorted(set(conflicts))[:100],
        'written_files': written,
        'strategy': 'current-main wins scalar conflicts; missing fields and unique list evidence are retained from the archived branch',
    }
    report_path = ROOT / 'reports/pr-105-rand-bilderberg-takeover.json'
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(json.dumps({key: value for key, value in report.items() if key != 'written_files'}, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
