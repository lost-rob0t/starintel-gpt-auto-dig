from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urlsplit
from urllib.request import Request, urlopen

from scripts.auto_dig_request import render_body
from scripts.quasar_autodig_worker import ExecutionResult, LifecycleWaiting


RUN_MARKER = "<!-- quasar-autodig-run:v1 -->"
COMPLETION_MARKER = "<!-- auto-dig-completion:v1 -->"
_DEFAULT_GOAL = "Investigate the requested subject with the canonical StarIntel Auto-Dig workflow."
_DEFAULT_SCOPE = "Use lawful public sources and canonical StarIntel datasets; preserve provenance and uncertainty."
_DEFAULT_COMPLETION = (
    "Publish validated findings, merge the research changes, and post the structured Auto-Dig completion receipt."
)


@dataclass(frozen=True)
class IssueSnapshot:
    number: int
    state: str
    title: str
    body: str
    comments: tuple[str, ...]


@dataclass(frozen=True)
class RenderedIssue:
    request_key: str
    title: str
    body: str


class IssueQueue(Protocol):
    def find_by_request_key(self, request_key: str) -> IssueSnapshot | None: ...

    def create_issue(
        self,
        *,
        title: str,
        body: str,
        labels: tuple[str, ...],
    ) -> IssueSnapshot: ...

    def refresh_issue(self, number: int) -> IssueSnapshot: ...


def _required_public_id(value: object, field: str) -> str:
    text = str(value or "").strip()
    if not text or len(text) > 256 or any(ch in text for ch in "\r\n\x00"):
        raise ValueError(f"{field} must be a bounded single-line value")
    return text


def _safe_publication_url(value: object) -> str | None:
    text = str(value or "").strip()
    try:
        parts = urlsplit(text)
    except ValueError:
        return None
    if parts.scheme != "https" or not parts.hostname or parts.username or parts.password:
        return None
    host = parts.hostname.rstrip(".").lower()
    if host == "localhost" or host.endswith(".localhost") or host == "star.intel" or host.endswith(".star.intel"):
        return None
    labels = host.split(".")
    if len(labels) == 4 and all(label.isdigit() for label in labels):
        octets = [int(label) for label in labels]
        if any(value < 0 or value > 255 for value in octets):
            return None
        first, second = octets[0], octets[1]
        if (
            first in {0, 10, 127}
            or (first == 169 and second == 254)
            or (first == 172 and 16 <= second <= 31)
            or (first == 192 and second == 168)
            or first >= 224
        ):
            return None
    return text


def parse_completion_receipt(comment: str) -> dict | None:
    if not isinstance(comment, str) or COMPLETION_MARKER not in comment:
        return None
    payload_text = comment.split(COMPLETION_MARKER, 1)[1].strip()
    try:
        payload = json.loads(payload_text)
    except (TypeError, ValueError):
        return None
    if not isinstance(payload, dict):
        return None
    if payload.get("validationPassed") is not True or payload.get("published") is not True:
        return None
    commit = str(payload.get("commit") or "").strip()
    publication = _safe_publication_url(payload.get("publication"))
    if not commit or len(commit) > 128 or not publication:
        return None
    return {
        "validationPassed": True,
        "published": True,
        "commit": commit,
        "publication": publication,
    }


class GitHubIssueQueueExecutor:
    """Bridge a Quasar-owned run to the existing issue-driven Auto-Dig executor.

    This adapter does not perform research and owns no lifecycle state. It only
    materializes/reuses the canonical investigation-target request, then waits
    for the existing scheduled GPT worker to publish a structured completion
    receipt. Quasar remains the durable run and lease authority.
    """

    def __init__(self, issues: IssueQueue) -> None:
        self.issues = issues

    def render_issue(self, run: dict) -> RenderedIssue:
        run_id = _required_public_id(run.get("runId"), "runId")
        request_id = _required_public_id(run.get("requestId"), "requestId")
        target = _required_public_id(run.get("target"), "target")
        key, canonical = render_body(
            subject=target,
            goal=_DEFAULT_GOAL,
            scope=_DEFAULT_SCOPE,
            seed_sources="",
            constraints=(
                "This request is linked to a Quasar durable Auto-Dig run. "
                "Do not infer lifecycle identity from the issue title or prose."
            ),
            completion=_DEFAULT_COMPLETION,
            priority="normal",
            dedupe_key=f"quasar:{request_id}",
        )
        linkage = (
            f"\n{RUN_MARKER}\n\n"
            "## Quasar Auto-Dig linkage\n\n"
            f"Run ID: `{run_id}`\n\n"
            f"Request ID: `{request_id}`\n\n"
            "Lifecycle state remains owned by Quasar; this issue is the canonical research queue surface.\n"
        )
        return RenderedIssue(
            request_key=key,
            title=f"[Auto-Dig request] {target}",
            body=canonical.rstrip() + "\n" + linkage,
        )

    def execute(self, run: dict, should_continue) -> ExecutionResult:
        should_continue()
        rendered = self.render_issue(run)
        issue = self.issues.find_by_request_key(rendered.request_key)
        if issue is None:
            issue = self.issues.create_issue(
                title=rendered.title,
                body=rendered.body,
                labels=("investigation-target",),
            )
        should_continue()
        issue = self.issues.refresh_issue(issue.number)
        if issue.state.lower() != "closed":
            raise LifecycleWaiting(f"research issue #{issue.number} remains open")

        for comment in reversed(issue.comments):
            receipt = parse_completion_receipt(comment)
            if receipt is not None:
                return ExecutionResult.completed({"issueNumber": issue.number, **receipt})

        return ExecutionResult.failed(
            code="completion_receipt_missing",
            message="The research issue closed without a validated publication receipt.",
        )


class GitHubRestIssueQueue:
    """Minimal GitHub REST adapter for the existing issue queue.

    The token is used only in request headers and is never included in errors,
    issue content, or returned snapshots.
    """

    def __init__(
        self,
        repository: str,
        *,
        token: str,
        api_origin: str = "https://api.github.com",
        timeout: float = 15.0,
    ) -> None:
        if repository.count("/") != 1:
            raise ValueError("repository must be owner/name")
        if not token.strip():
            raise ValueError("token must be non-empty")
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        self.repository = repository
        self.token = token
        self.api_origin = api_origin.rstrip("/")
        self.timeout = float(timeout)

    def _request(self, method: str, path: str, payload: dict | None = None) -> object:
        data = None
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "starintel-gpt-auto-dig-worker",
        }
        if payload is not None:
            data = json.dumps(payload, separators=(",", ":")).encode("utf-8")
            headers["Content-Type"] = "application/json"
        request = Request(f"{self.api_origin}{path}", data=data, headers=headers, method=method)
        try:
            with urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, ValueError) as exc:
            raise RuntimeError("GitHub issue queue request failed") from exc

    def _snapshot(self, raw: dict, comments: tuple[str, ...] = ()) -> IssueSnapshot:
        return IssueSnapshot(
            number=int(raw["number"]),
            state=str(raw.get("state") or "open"),
            title=str(raw.get("title") or ""),
            body=str(raw.get("body") or ""),
            comments=comments,
        )

    def find_by_request_key(self, request_key: str) -> IssueSnapshot | None:
        query = f'repo:{self.repository} "auto-dig:{request_key}" in:body is:issue'
        raw = self._request("GET", f"/search/issues?{urlencode({'q': query, 'per_page': 5})}")
        if not isinstance(raw, dict):
            raise RuntimeError("GitHub issue queue returned an invalid search response")
        items = raw.get("items")
        if not isinstance(items, list):
            raise RuntimeError("GitHub issue queue returned an invalid search response")
        for item in items:
            if isinstance(item, dict) and f"auto-dig:{request_key}" in str(item.get("body") or ""):
                return self.refresh_issue(int(item["number"]))
        return None

    def create_issue(self, *, title: str, body: str, labels: tuple[str, ...]) -> IssueSnapshot:
        owner_repo = "/".join(quote(part, safe="") for part in self.repository.split("/"))
        raw = self._request(
            "POST",
            f"/repos/{owner_repo}/issues",
            {"title": title, "body": body, "labels": list(labels)},
        )
        if not isinstance(raw, dict):
            raise RuntimeError("GitHub issue queue returned an invalid create response")
        return self._snapshot(raw)

    def refresh_issue(self, number: int) -> IssueSnapshot:
        owner_repo = "/".join(quote(part, safe="") for part in self.repository.split("/"))
        raw = self._request("GET", f"/repos/{owner_repo}/issues/{int(number)}")
        comments_raw = self._request(
            "GET",
            f"/repos/{owner_repo}/issues/{int(number)}/comments?per_page=100",
        )
        if not isinstance(raw, dict) or not isinstance(comments_raw, list):
            raise RuntimeError("GitHub issue queue returned an invalid issue response")
        comments = tuple(
            str(comment.get("body") or "")
            for comment in comments_raw
            if isinstance(comment, dict)
        )
        return self._snapshot(raw, comments)
