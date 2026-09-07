#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from starintel_doc.model import Document
from starintel_doc.schema_org import document_schema
from starintel_doc.spec import TYPE_FIELDS
from starintel_doc.store import iter_corpus, search_documents
from starintel_doc.validation import validate_document
from starintel_doc.writer import canonical_db_path, write_db_document

Runner = Callable[..., subprocess.CompletedProcess[str]]
IDENTITY_METADATA = {
    "_id",
    "dataset",
    "dtype",
    "schema_version",
    "version",
    "title",
    "summary",
    "data",
}


def require_object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object")
    return value


def bounded_limit(value: Any) -> int:
    if value is None:
        return 10
    if not isinstance(value, int) or isinstance(value, bool) or not 1 <= value <= 20:
        raise ValueError("limit must be an integer from 1 through 20")
    return value


def draft_document(request: dict[str, Any]) -> dict[str, Any]:
    metadata = require_object(request.get("metadata", {}), "metadata")
    forbidden = sorted(IDENTITY_METADATA.intersection(metadata))
    if forbidden:
        raise ValueError(f"metadata cannot override identity fields: {', '.join(forbidden)}")
    document = Document.create(
        request.get("dtype", ""),
        request.get("dataset", ""),
        doc_id=request.get("id") or None,
        title=request.get("title", ""),
        summary=request.get("summary", ""),
        data=require_object(request.get("data", {}), "data"),
        **metadata,
    ).to_dict()
    return {"document": document}


def search(root: Path, request: dict[str, Any]) -> dict[str, Any]:
    dtype = request.get("dtype", "")
    if dtype and dtype not in TYPE_FIELDS:
        raise ValueError(f"unknown dtype: {dtype}")
    limit = bounded_limit(request.get("limit"))
    documents = iter_corpus(root, include_db=True, include_packets=True)
    matches = search_documents(
        documents,
        query=request.get("query", ""),
        dtypes={dtype} if dtype else None,
        dataset=request.get("dataset", ""),
        predicate=request.get("predicate", ""),
        doc_id=request.get("id", ""),
        source=request.get("source", ""),
        min_confidence=request.get("min_confidence"),
    )[:limit]
    results = [
        {
            "path": str(item.path.relative_to(root)),
            "line": item.line,
            "surface": item.surface,
            "document": item.document,
        }
        for item in matches
    ]
    return {"count": len(results), "results": results}


def prepare_write(root: Path, request: dict[str, Any]) -> dict[str, Any]:
    document = require_object(request.get("document"), "document")
    validate_document(document)
    target = canonical_db_path(root, document)
    relative = str(target.relative_to(root.resolve()))
    digest = hashlib.sha256(
        json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return {
        "request": {"document": document},
        "details": {
            "target": relative,
            "document_id": document["_id"],
            "dtype": document["dtype"],
            "sha256": digest,
        },
    }


def write_document(root: Path, request: dict[str, Any]) -> dict[str, Any]:
    prepared = prepare_write(root, request)
    document = prepared["request"]["document"]
    target = root.resolve() / prepared["details"]["target"]
    existed = target.exists()
    written = write_db_document(root, document, replace=False, validate_corpus=True)
    return {
        "status": "unchanged" if existed else "written",
        "path": str(written.relative_to(root.resolve())),
        "document_id": document["_id"],
        "dtype": document["dtype"],
    }


def prepare_issue_reply(
    request: dict[str, Any], github_repository: str, issue: int
) -> dict[str, Any]:
    if not github_repository or "/" not in github_repository:
        raise ValueError("trusted GitHub repository is required")
    if not isinstance(issue, int) or isinstance(issue, bool) or issue <= 0:
        raise ValueError("trusted positive GitHub issue number is required")
    body = request.get("body")
    if not isinstance(body, str) or not body.strip():
        raise ValueError("issue reply body must be non-empty text")
    body = body.strip()
    if len(body) > 16000:
        raise ValueError("issue reply body exceeds 16000 characters")
    identity = f"{github_repository}\n{issue}\n{body}".encode("utf-8")
    digest = hashlib.sha256(identity).hexdigest()[:24]
    marker = f"<!-- auto-dig-prolog-reply:{digest} -->"
    return {
        "request": {"body": body},
        "details": {
            "repository": github_repository,
            "issue": issue,
            "marker": marker,
        },
        "body": f"{marker}\n{body}",
    }


def run_checked(runner: Runner, command: list[str]) -> subprocess.CompletedProcess[str]:
    completed = runner(command, text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or "command failed"
        raise ValueError(detail)
    return completed


def issue_reply(
    request: dict[str, Any],
    github_repository: str,
    issue: int,
    runner: Runner,
) -> dict[str, Any]:
    prepared = prepare_issue_reply(request, github_repository, issue)
    marker = prepared["details"]["marker"]
    endpoint = f"repos/{github_repository}/issues/{issue}/comments?per_page=100"
    listed = run_checked(runner, ["gh", "api", "--paginate", "--slurp", endpoint])
    pages = json.loads(listed.stdout or "[]")
    comments = pages if pages and isinstance(pages[0], dict) else [c for page in pages for c in page]
    for comment in comments:
        if isinstance(comment, dict) and marker in str(comment.get("body", "")):
            return {
                "status": "existing",
                "url": comment.get("html_url", ""),
                "marker": marker,
                "body": prepared["body"],
            }
    posted = run_checked(
        runner,
        [
            "gh",
            "issue",
            "comment",
            str(issue),
            "--repo",
            github_repository,
            "--body",
            prepared["body"],
        ],
    )
    return {
        "status": "posted",
        "url": posted.stdout.strip(),
        "marker": marker,
        "body": prepared["body"],
    }


def handle_request(
    command: str,
    raw_request: Any,
    *,
    root: Path,
    github_repository: str = "",
    issue: int = 0,
    runner: Runner = subprocess.run,
) -> dict[str, Any]:
    request = require_object(raw_request, "request")
    root = root.resolve()
    if command == "types":
        return {"schema_version": "0.9.0", "dtypes": sorted(TYPE_FIELDS)}
    if command == "schema":
        dtype = request.get("dtype", "")
        if dtype and dtype not in TYPE_FIELDS:
            raise ValueError(f"unknown dtype: {dtype}")
        return {"dtype": dtype or None, "schema": document_schema(dtype or None)}
    if command == "search":
        return search(root, request)
    if command == "draft":
        return draft_document(request)
    if command == "validate-document":
        document = require_object(request.get("document"), "document")
        validate_document(document)
        return {"valid": True, "document_id": document["_id"], "dtype": document["dtype"]}
    if command == "prepare-write":
        return prepare_write(root, request)
    if command == "write-document":
        return write_document(root, request)
    if command == "prepare-issue-reply":
        return prepare_issue_reply(request, github_repository, issue)
    if command == "issue-reply":
        return issue_reply(request, github_repository, issue, runner)
    raise ValueError(f"unknown adapter command: {command}")


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description="Bounded StarIntel adapter for Auto-Dig Prolog")
    value.add_argument("command")
    value.add_argument("--root", default=str(ROOT))
    value.add_argument("--github-repository", default="")
    value.add_argument("--issue", type=int, default=0)
    return value


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        request = json.load(sys.stdin)
        result = handle_request(
            args.command,
            request,
            root=Path(args.root),
            github_repository=args.github_repository,
            issue=args.issue,
        )
        json.dump({"ok": True, "result": result}, sys.stdout, ensure_ascii=False, sort_keys=True)
        sys.stdout.write("\n")
        return 0
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        json.dump({"ok": False, "error": str(exc)}, sys.stdout, ensure_ascii=False, sort_keys=True)
        sys.stdout.write("\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
