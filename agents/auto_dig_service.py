#!/usr/bin/env python3
"""Standalone Auto-Dig Prolog actor service runner.

Runs the Auto-Dig harness end to end without an action runner. The harness is
reused unchanged: the supervised Prolog queue actor, the expert model router,
the native direct Prolog-RLM research loop, and the read-only Brave/Fetch MCP
tool allow-list. This module only replaces the GitHub Actions orchestration
shell:

  git.starintel.actor issues (label `investigation-target`)
    -> snapshot the queue through the Forgejo API
    -> load durable `[actor-state] auto-dig-prolog` state
    -> Prolog actor selects one eligible request (repeat policy intact)
    -> expert model route
    -> bounded read-only Prolog-RLM web research
    -> push the run branch to origin
    -> post the receipt comment and advance durable state
    -> re-snapshot the queue and keep working down the issues

Configuration is environment-driven. No secrets are logged or embedded in
outputs. The deployed service later wraps this entrypoint; no deployment
logic lives here.

Exit codes: 0 = drain finished (idle queue or --max-issues reached),
1 = at least one pass failed, 2 = fatal configuration or intake error.
"""

from __future__ import annotations

import argparse
import json
import os
import secrets
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_FORGE_HOST = "https://git.starintel.actor"
DEFAULT_REPO = "nsaspy/starintel-gpt-auto-dig"
DEFAULT_PROLOG_RLM_REF = "39b278589dae8518e583778cd6671a6cb1e026c7"
DEFAULT_TOKEN_ENVS = ("AUTO_DIG_FORGE_TOKEN", "FORGEJO_TOKEN")
QUEUE_LABEL = "investigation-target"
STATE_ISSUE_TITLE = "[actor-state] auto-dig-prolog"
STATE_SCHEMA = "auto-dig-prolog-state.v1"
RUN_SCHEMA = "auto-dig-prolog-run.v1"
AGENT_NAME = "auto-dig-prolog"
ACTOR_DIR = "agents"

RLM_FEATURES = [
    "automatic_default_skills",
    "native_direct_mode",
    "all_capability_filtered_tools",
    "context_search_peek_slice",
    "context_peek_selector_contract",
    "recoverable_native_preflight_faults",
    "transient_provider_retry",
    "read_only_tool_error_recovery",
    "wall_clock_synthesis_reserve",
    "model_context_budget_30_percent",
    "read_only_brave_search_mcp",
    "read_only_fetch_mcp",
    "read_only_starintel_corpus_mcp",
    "corpus_first_identity_reuse",
    "emission_boundary_diagnostic_sanitization",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def utc_date() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def log(message: str) -> None:
    print(f"[auto-dig-service] {message}", flush=True)


def die(message: str, code: int = 2) -> None:
    print(f"[auto-dig-service] fatal: {message}", file=sys.stderr, flush=True)
    raise SystemExit(code)


# ---------------------------------------------------------------------------
# Configuration


def _env_repo() -> str:
    raw = os.environ.get("AUTO_DIG_FORGE_REPO", "").strip()
    return raw or DEFAULT_REPO


def _env_host() -> str:
    raw = os.environ.get("AUTO_DIG_FORGE_HOST", "").strip().rstrip("/")
    return raw or DEFAULT_FORGE_HOST


def _resolve_token(explicit_env: str | None) -> str | None:
    candidates = [explicit_env] if explicit_env else list(DEFAULT_TOKEN_ENVS)
    for name in candidates:
        if not name:
            continue
        value = os.environ.get(name, "").strip()
        if value:
            return value
    return None


@dataclass
class ServiceConfig:
    host: str
    repo: str
    token: str | None
    queue_label: str
    state_file: Path | None
    queue_file: Path | None
    run_root: Path
    repo_root: Path
    prolog_rlm_dir: Path
    prolog_rlm_ref: str
    force_issue: int | None
    max_issues: int
    time_budget: float
    loop: bool
    interval: float
    dry_run: bool
    allow_dirty: bool
    model_override: str | None
    reasoning_effort_override: str | None

    @property
    def api_base(self) -> str:
        return f"{self.host}/api/v1/repos/{self.repo}"

    @property
    def gateway_mode(self) -> bool:
        return bool(os.environ.get("AUTO_DIG_LLM_ENDPOINT", "").strip())


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the Auto-Dig Prolog actor as a standalone service pass."
    )
    parser.add_argument(
        "--host",
        default=None,
        help="Forgejo host (default: $AUTO_DIG_FORGE_HOST or https://git.starintel.actor)",
    )
    parser.add_argument(
        "--repo",
        default=None,
        help="owner/name queue repository (default: $AUTO_DIG_FORGE_REPO or the canonical repo)",
    )
    parser.add_argument(
        "--token-env",
        default=None,
        help="environment variable holding the Forgejo API token "
        "(default: AUTO_DIG_FORGE_TOKEN then FORGEJO_TOKEN)",
    )
    parser.add_argument(
        "--queue-label",
        default=QUEUE_LABEL,
        help="issue label that marks queue entries (default: investigation-target)",
    )
    parser.add_argument(
        "--queue-file",
        default=None,
        help="read the queue snapshot from a JSON file instead of the Forgejo API",
    )
    parser.add_argument(
        "--state-file",
        default=None,
        help="keep durable state in a local JSON file instead of the state issue",
    )
    parser.add_argument(
        "--run-root",
        default="agent-runs/auto-dig-prolog",
        help="run artifact directory relative to the repository root",
    )
    parser.add_argument(
        "--repo-root",
        default=None,
        help="Auto-Dig repository checkout root (default: parent of this script)",
    )
    parser.add_argument(
        "--prolog-rlm-dir",
        default=None,
        help="pinned Prolog-RLM checkout (default: $PROLOG_RLM_DIR or <repo-root>/.prolog-rlm)",
    )
    parser.add_argument(
        "--prolog-rlm-ref",
        default=os.environ.get("PROLOG_RLM_REF", DEFAULT_PROLOG_RLM_REF),
        help="pinned Prolog-RLM commit that must be checked out",
    )
    parser.add_argument(
        "--force-issue",
        type=int,
        default=None,
        help="force a specific investigation-target issue number for one pass",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="override the expert model route (for example a gateway model)",
    )
    parser.add_argument(
        "--reasoning-effort",
        default="high",
        help="reasoning effort used with --model (default: high)",
    )
    parser.add_argument(
        "--max-issues",
        type=int,
        default=0,
        help="stop after N completed passes in one drain (0 = work down the whole queue)",
    )
    parser.add_argument(
        "--time-budget",
        type=float,
        default=0.0,
        help="stop draining after N wall-clock seconds (0 = unlimited)",
    )
    parser.add_argument(
        "--loop",
        action="store_true",
        help="keep draining forever, sleeping --interval seconds between drains",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=3600.0,
        help="sleep seconds between drain invocations in --loop mode",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="select and stage a run without research, branch push, or issue writes",
    )
    parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help="skip the clean-worktree preflight (selection-only debugging)",
    )
    return parser


def load_config(argv: list[str]) -> ServiceConfig:
    args = build_parser().parse_args(argv)
    script_dir = Path(__file__).resolve().parent
    repo_root = Path(args.repo_root).resolve() if args.repo_root else script_dir.parent
    rlm_dir = (
        Path(args.prolog_rlm_dir).resolve()
        if args.prolog_rlm_dir
        else Path(os.environ.get("PROLOG_RLM_DIR", repo_root / ".prolog-rlm")).resolve()
    )
    return ServiceConfig(
        host=args.host or _env_host(),
        repo=args.repo or _env_repo(),
        token=_resolve_token(args.token_env),
        queue_label=args.queue_label,
        state_file=Path(args.state_file).resolve() if args.state_file else None,
        queue_file=Path(args.queue_file).resolve() if args.queue_file else None,
        run_root=Path(args.run_root),
        repo_root=repo_root,
        prolog_rlm_dir=rlm_dir,
        prolog_rlm_ref=args.prolog_rlm_ref.strip(),
        force_issue=args.force_issue,
        max_issues=max(0, args.max_issues),
        time_budget=max(0.0, args.time_budget),
        loop=args.loop,
        interval=max(60.0, args.interval),
        dry_run=args.dry_run,
        allow_dirty=args.allow_dirty,
        model_override=args.model,
        reasoning_effort_override=(args.reasoning_effort if args.model else None),
    )


# ---------------------------------------------------------------------------
# Forgejo API client (stdlib only; no gh/tea CLI, no action runner)


class ForgejoError(RuntimeError):
    pass


class ForgejoClient:
    def __init__(self, cfg: ServiceConfig) -> None:
        self.cfg = cfg

    def _request(self, method: str, path: str, body: dict[str, Any] | None = None) -> Any:
        url = f"{self.cfg.api_base}{path}"
        data = None
        headers = {"Accept": "application/json"}
        if self.cfg.token:
            headers["Authorization"] = f"token {self.cfg.token}"
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                raw = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:400]
            raise ForgejoError(
                f"{method} {path} -> HTTP {exc.code}: {detail}; "
                "check the token and repository access"
            ) from exc
        except urllib.error.URLError as exc:
            raise ForgejoError(f"{method} {path} -> unreachable: {exc.reason}") from exc
        if not raw:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ForgejoError(f"{method} {path} -> non-JSON response") from exc

    def list_issues(self, label: str) -> list[dict[str, Any]]:
        issues: list[dict[str, Any]] = []
        page = 1
        while True:
            batch = self._request(
                "GET",
                f"/issues?state=open&type=issues&labels={label}&limit=50&page={page}",
            )
            if not isinstance(batch, list) or not batch:
                break
            issues.extend(batch)
            if len(batch) < 50:
                break
            page += 1
            if page > 50:
                raise ForgejoError("issue pagination exceeded 50 pages")
        return issues

    def find_state_issue(self, title: str) -> dict[str, Any] | None:
        page = 1
        while True:
            batch = self._request(
                "GET",
                "/issues?state=open&type=issues&limit=50&page={}".format(page),
            )
            if not isinstance(batch, list) or not batch:
                return None
            for issue in batch:
                if issue.get("title") == title:
                    return issue
            if len(batch) < 50:
                return None
            page += 1
            if page > 50:
                raise ForgejoError("state issue scan exceeded 50 pages")

    def create_issue(self, title: str, body: str) -> dict[str, Any]:
        return self._request("POST", "/issues", {"title": title, "body": body})

    def edit_issue_body(self, number: int, body: str) -> Any:
        return self._request("PATCH", f"/issues/{number}", {"body": body})

    def add_comment(self, number: int, body: str) -> Any:
        return self._request("POST", f"/issues/{number}/comments", {"body": body})


# ---------------------------------------------------------------------------
# Queue, state, and request rendering


def normalize_issue(raw: dict[str, Any], cfg: ServiceConfig) -> dict[str, Any]:
    number = int(raw["number"])
    return {
        "number": number,
        "title": raw.get("title", ""),
        "body": raw.get("body") or "",
        "url": raw.get("html_url") or f"{cfg.host}/{cfg.repo}/issues/{number}",
        "createdAt": raw.get("created_at", ""),
        "updatedAt": raw.get("updated_at", ""),
        "labels": [{"name": label.get("name", "")} for label in raw.get("labels", [])],
    }


def default_state() -> dict[str, Any]:
    return {
        "schema": STATE_SCHEMA,
        "last_issue": None,
        "last_priority": None,
        "last_branch": None,
        "last_run_id": None,
        "last_success_at": None,
    }


def parse_state_body(raw: str | None) -> dict[str, Any]:
    text = (raw or "").strip()
    if not text:
        return default_state()
    state = json.loads(text)
    if state.get("schema") != STATE_SCHEMA:
        raise ValueError(f"state schema is not {STATE_SCHEMA!r}")
    return state


def advance_state(decision: dict[str, Any], branch: str, run_id: str) -> dict[str, Any]:
    next_state = dict(decision.get("next_state") or {})
    next_state.update(
        {
            "schema": STATE_SCHEMA,
            "last_branch": branch,
            "last_run_id": run_id,
            "last_success_at": utc_now(),
        }
    )
    return next_state


def render_request_markdown(decision: dict[str, Any], issue: dict[str, Any]) -> str:
    body = (issue.get("body") or "").strip() or "(The issue body is empty.)"
    return (
        "# Auto-Dig request\n\n"
        f"- Issue: #{issue['number']}\n"
        f"- Title: {issue['title']}\n"
        f"- URL: {issue['url']}\n"
        f"- Queue priority: {decision.get('priority', 'normal')}\n"
        f"- Selected at: {utc_now()}\n"
        f"- Intake: git.starintel.actor issues, label `{QUEUE_LABEL}`\n\n"
        "## Request body\n\n"
        f"{body}\n\n"
        "## Research lane contract for this run\n\n"
        "- Bounded read-only web research: Brave search and Fetch tools only; "
        "this run does not write canonical StarIntel records, commit research, "
        "merge, or publish.\n"
        "- Answer the request's stated Goal and Completion criteria within its "
        "Scope; honor its Seed sources and Constraints.\n"
        "- Cover the people, organizations, jurisdictions, records, and date "
        "ranges the request names explicitly; state which required surfaces "
        "could not be covered and why.\n"
        "- The Completion criteria describe the end state after merge and "
        "publication; this run contributes an evidence-backed research slice "
        "toward that end state.\n"
    )


RECEIPT_REPORT_CHAR_LIMIT = 16000


def receipt_report_section(report: str | None) -> list[str]:
    """Render the research report block appended to the receipt comment.

    The full report always lives on the run branch as report.md; the copy in
    the comment is bounded so one oversized report cannot crowd out the
    receipt contract or trip the forge's comment size limits.
    """
    if not report:
        return []
    text = report.strip()
    if not text:
        return []
    if len(text) > RECEIPT_REPORT_CHAR_LIMIT:
        truncated = text[:RECEIPT_REPORT_CHAR_LIMIT].rstrip()
        return [
            "",
            "## Research report (truncated)",
            "",
            truncated,
            "",
            f"Report truncated at {RECEIPT_REPORT_CHAR_LIMIT} characters in this comment; "
            "the complete validated report is `report.md` on the run branch above.",
        ]
    return [
        "",
        "## Research report",
        "",
        text,
    ]


def render_receipt_comment(
    cfg: ServiceConfig,
    run_id: str,
    branch: str,
    model: str,
    effort: str,
    dry_run: bool = False,
    report: str | None = None,
) -> str:
    branch_url = f"{cfg.host}/{cfg.repo}/src/branch/{branch}"
    lines = [
        f"Auto-Dig Prolog actor completed bounded run `{run_id}`.",
        "",
        f"- Branch: {branch_url}",
        f"- Prolog-RLM: `{cfg.prolog_rlm_ref}`",
        f"- Expert route: `{model}`, reasoning `{effort}`",
        "- Stage: supervised actor + current native direct Prolog-RLM loop + "
        "automatic default skills + full capability-filtered read-only "
        "Brave/Fetch MCP research + recoverable per-call native preflight + "
        "bounded transient provider retries + wall-clock synthesis reserve + "
        "30% model-context token budget.",
    ]
    lines.extend(receipt_report_section(report))
    lines.extend([
        "",
        "This receipt does **not** mark the investigation complete; canonical "
        "StarIntel writes, validation, merge, and final publication remain "
        "separate gates.",
    ])
    if dry_run:
        lines.append("")
        lines.append("(Dry run: no branch was pushed and no state advanced.)")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Harness stages (reuse the Prolog components unchanged)


def _swipl_library_option(cfg: ServiceConfig) -> list[str]:
    return ["-p", f"library={cfg.prolog_rlm_dir}/prolog"]


def run_prolog_script(
    cfg: ServiceConfig,
    script: Path,
    args: list[str],
    use_rlm_library: bool,
    env: dict[str, str],
) -> None:
    command = ["swipl", "-q"]
    if use_rlm_library:
        command += _swipl_library_option(cfg)
    command += ["-s", str(script), "--", *args]
    result = subprocess.run(
        command,
        cwd=cfg.repo_root,
        env=env,
        capture_output=True,
        text=True,
    )
    if result.stdout:
        print(result.stdout, end="", flush=True)
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr, flush=True)
    if result.returncode != 0:
        raise RuntimeError(f"{script.name} failed with exit {result.returncode}")


def run_queue_actor(
    cfg: ServiceConfig,
    queue_path: Path,
    state_path: Path,
    output_path: Path,
    trace_path: Path,
    env: dict[str, str],
) -> dict[str, Any]:
    args = [
        "--queue",
        str(queue_path),
        "--state",
        str(state_path),
        "--output",
        str(output_path),
        "--trace",
        str(trace_path),
    ]
    if cfg.force_issue is not None:
        args += ["--force-issue", str(cfg.force_issue)]
    run_prolog_script(
        cfg,
        cfg.repo_root / ACTOR_DIR / "auto_dig_prolog_actor.pl",
        args,
        use_rlm_library=True,
        env=env,
    )
    decision = json.loads(output_path.read_text(encoding="utf-8"))
    if not isinstance(decision, dict) or "action" not in decision:
        raise ValueError("actor decision is not an object with an action")
    return decision


def run_model_route(cfg: ServiceConfig, run_dir: Path, priority: str) -> dict[str, Any]:
    risk = "high" if priority == "urgent" else "normal"
    profile = {
        "task": "research",
        "phase": "execute",
        "risk": risk,
        "irreversible": False,
        "failed_verifications": 0,
    }
    profile_path = run_dir / "model-profile.json"
    output_path = run_dir / "model-route.json"
    profile_path.write_text(json.dumps(profile, indent=2) + "\n", encoding="utf-8")
    run_prolog_script(
        cfg,
        cfg.repo_root / ACTOR_DIR / "auto_dig_model_router.pl",
        ["--profile", str(profile_path), "--output", str(output_path)],
        use_rlm_library=False,
        env=dict(os.environ),
    )
    route = json.loads(output_path.read_text(encoding="utf-8"))
    if (
        route.get("schema") != "auto-dig-model-route.v1"
        or not isinstance(route.get("model"), str)
        or not isinstance(route.get("reasoning", {}).get("effort"), str)
    ):
        raise ValueError("model route did not satisfy the routing contract")
    return route


def run_research(
    cfg: ServiceConfig,
    run_dir: Path,
    request_path: Path,
    model: str,
    effort: str,
    env: dict[str, str],
) -> int:
    """Mirror the workflow's sanitized swipl | failure-report | tee pipeline."""
    result_path = run_dir / "rlm-result.json"
    trace_path = run_dir / "rlm-trace.json"
    stderr_log = run_dir / "rlm-stderr.log"
    status_path = run_dir / "pipeline.status"
    script = (
        "set +e\n"
        "swipl -q "
        + " ".join(_swipl_library_option(cfg))
        + f" -s {ACTOR_DIR}/auto_dig_rlm_runner.pl --"
        + f" --context-file '{request_path}'"
        + f" --model '{model}'"
        + f" --reasoning-effort '{effort}'"
        + f" --output '{result_path}'"
        + f" --trace '{trace_path}'"
        + " 2>&1"
        + f" | python3 {ACTOR_DIR}/auto_dig_failure_report.py --stream"
        + f" | tee '{stderr_log}' >&2\n"
        'status=("${PIPESTATUS[@]}")\n'
        f"printf '%s\\n' \"${{status[@]}}\" > '{status_path}'\n"
        'exit "${status[0]}"\n'
    )
    result = subprocess.run(
        ["bash", "-c", script],
        cwd=cfg.repo_root,
        env=env,
        text=True,
    )
    statuses: list[int] = []
    if status_path.is_file():
        statuses = [
            int(line)
            for line in status_path.read_text(encoding="utf-8").split()
            if line.lstrip("-").isdigit()
        ]
    status = statuses[0] if statuses else result.returncode
    if len(statuses) >= 3 and (statuses[1] != 0 or statuses[2] != 0):
        print(
            "[auto-dig-service] diagnostic emission failure: "
            f"sanitizer={statuses[1]} tee={statuses[2]}",
            file=sys.stderr,
            flush=True,
        )
        status = 2
    return status


def write_failure_report(cfg: ServiceConfig, run_dir: Path) -> Path | None:
    report = run_dir / "failure-report.md"
    args = [
        "python3",
        str(cfg.repo_root / ACTOR_DIR / "auto_dig_failure_report.py"),
        "--output",
        str(report),
        "--max-lines",
        "180",
    ]
    result_file = run_dir / "rlm-result.json"
    stderr_file = run_dir / "rlm-stderr.log"
    if result_file.is_file():
        args += ["--result", str(result_file)]
    if stderr_file.is_file():
        args += ["--stderr", str(stderr_file)]
    completed = subprocess.run(args, cwd=cfg.repo_root, capture_output=True, text=True)
    if completed.returncode != 0 or not report.is_file():
        print(completed.stderr, end="", file=sys.stderr, flush=True)
        return None
    return report


# ---------------------------------------------------------------------------
# Git stage


def git(cfg: ServiceConfig, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(cfg.repo_root), *args],
        capture_output=True,
        text=True,
        check=check,
    )


def preflight_worktree(cfg: ServiceConfig) -> None:
    git(cfg, "rev-parse", "--git-dir")
    status = git(cfg, "status", "--porcelain")
    if status.stdout.strip() and not cfg.allow_dirty:
        raise RuntimeError(
            "worktree is not clean; the service stages runs on committed "
            "branches (use --allow-dirty for selection-only debugging)"
        )


def current_branch(cfg: ServiceConfig) -> str:
    return git(cfg, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()


def push_run_branch(cfg: ServiceConfig, run_dir_rel: Path, branch: str, run_id: str) -> str:
    original = current_branch(cfg)
    try:
        git(cfg, "switch", "-c", branch)
        git(cfg, "add", str(run_dir_rel))
        git(
            cfg,
            "-c",
            "user.name=auto-dig-prolog[bot]",
            "-c",
            "user.email=auto-dig-prolog@users.noreply.starintel.actor",
            "commit",
            "-m",
            f"agent({AGENT_NAME}): run {run_id}",
        )
        git(cfg, "push", "origin", branch)
        pushed = git(cfg, "rev-parse", branch).stdout.strip()
        return pushed
    finally:
        # The run artifacts live on the run branch now; switching back
        # removes them from this worktree, so nothing may touch the run
        # directory after this returns.
        git(cfg, "switch", original, check=False)


# ---------------------------------------------------------------------------
# Durable state accessors


class StateStore:
    """Durable actor state, kept either in a local file or the state issue."""

    def __init__(self, cfg: ServiceConfig, client: ForgejoClient | None) -> None:
        self.cfg = cfg
        self.client = client
        self._issue_number: int | None = None

    def load(self) -> dict[str, Any]:
        if self.cfg.state_file is not None:
            return parse_state_body(self.cfg.state_file.read_text(encoding="utf-8"))
        if self.cfg.dry_run and self.client is None:
            return default_state()
        if self.client is None:
            raise RuntimeError("no Forgejo client available to load state")
        issue = self.client.find_state_issue(STATE_ISSUE_TITLE)
        if issue is None:
            return default_state()
        self._issue_number = int(issue["number"])
        return parse_state_body(issue.get("body"))

    def save(self, state: dict[str, Any]) -> None:
        payload = json.dumps(state, indent=2, sort_keys=True)
        if self.cfg.state_file is not None:
            self.cfg.state_file.write_text(payload + "\n", encoding="utf-8")
            return
        if self.cfg.dry_run:
            return
        if self.client is None:
            raise RuntimeError("no Forgejo client available to persist state")
        if self._issue_number is None:
            issue = self.client.find_state_issue(STATE_ISSUE_TITLE)
            if issue is None:
                created = self.client.create_issue(STATE_ISSUE_TITLE, payload)
                self._issue_number = int(created["number"])
                return
            self._issue_number = int(issue["number"])
        self.client.edit_issue_body(self._issue_number, payload)


def resolve_model_route(cfg: ServiceConfig, run_dir: Path, priority: str) -> dict[str, Any]:
    """Expert route from the Prolog KB, or the explicit --model override."""
    if cfg.model_override:
        route = {
            "schema": "auto-dig-model-route.v1",
            "model": cfg.model_override,
            "tier": "override",
            "reasoning": {"effort": cfg.reasoning_effort_override or "high"},
        }
        (run_dir / "model-route.json").write_text(
            json.dumps(route, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        return route
    return run_model_route(cfg, run_dir, priority)


# ---------------------------------------------------------------------------
# One pass


@dataclass
class PassResult:
    outcome: str
    issue_number: int | None = None
    detail: str = ""


def verify_prolog_rlm_checkout(cfg: ServiceConfig) -> None:
    if not (cfg.prolog_rlm_dir / "prolog").is_dir():
        die(
            f"pinned Prolog-RLM checkout not found at {cfg.prolog_rlm_dir}; "
            "check out the pinned ref and run "
            "scripts/apply_prolog_rlm_hotfix.py on it"
        )
    head = subprocess.run(
        ["git", "-C", str(cfg.prolog_rlm_dir), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    if head != cfg.prolog_rlm_ref:
        die(f"Prolog-RLM checkout is {head}, expected pinned {cfg.prolog_rlm_ref}")


def research_env(cfg: ServiceConfig) -> dict[str, str]:
    env = dict(os.environ)
    if cfg.gateway_mode:
        required = ("AUTO_DIG_LLM_API_KEY", "BRAVE_API_KEY")
    else:
        required = ("OPENROUTER_API_KEY", "BRAVE_API_KEY")
    missing = [
        name for name in required if not env.get(name, "").strip()
    ]
    if missing:
        die(f"required research secret(s) missing: {', '.join(missing)}")
    return env


def write_run_manifest(
    cfg: ServiceConfig,
    run_dir: Path,
    run_id: str,
    branch: str,
    issue_number: int,
) -> None:
    manifest = {
        "schema": RUN_SCHEMA,
        "agent": AGENT_NAME,
        "run_id": run_id,
        "branch": branch,
        "trigger": "service",
        "prolog_rlm_ref": cfg.prolog_rlm_ref,
        "issue_number": issue_number,
        "status": "selected",
        "rlm_features": list(RLM_FEATURES),
    }
    (run_dir / "run.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def update_run_manifest(run_dir: Path, patch: dict[str, Any]) -> None:
    path = run_dir / "run.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest.update(patch)
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def stage_run_artifacts(
    cfg: ServiceConfig,
    run_dir: Path,
    decision: dict[str, Any],
    issue: dict[str, Any],
    scratch_decision: Path,
    scratch_trace: Path,
) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "decision.json").write_text(
        json.dumps(decision, indent=2) + "\n", encoding="utf-8"
    )
    if scratch_trace.is_file():
        (run_dir / "actor.trace").write_text(
            scratch_trace.read_text(encoding="utf-8"), encoding="utf-8"
        )
    (run_dir / "issue.json").write_text(
        json.dumps(issue, indent=2) + "\n", encoding="utf-8"
    )
    (run_dir / "request.md").write_text(
        render_request_markdown(decision, issue), encoding="utf-8"
    )


def run_one_pass(
    cfg: ServiceConfig,
    client: ForgejoClient | None,
    state_store: StateStore,
    pass_index: int,
    attempted: set[int],
) -> PassResult:
    if not cfg.dry_run:
        preflight_worktree(cfg)

    with tempfile.TemporaryDirectory(prefix="auto-dig-service-") as scratch:
        scratch_dir = Path(scratch)
        queue_path = scratch_dir / "queue.json"
        state_path = scratch_dir / "state.json"
        decision_path = scratch_dir / "decision.json"
        trace_path = scratch_dir / "actor.trace"

        # 1. Snapshot the queue.
        if cfg.queue_file is not None:
            queue = json.loads(cfg.queue_file.read_text(encoding="utf-8"))
        else:
            if client is None:
                die("no queue source: pass --queue-file or configure the Forgejo API")
            raw_issues = client.list_issues(cfg.queue_label)
            queue = [normalize_issue(issue, cfg) for issue in raw_issues]
        queue = [entry for entry in queue if int(entry["number"]) not in attempted]
        queue_path.write_text(json.dumps(queue, indent=2) + "\n", encoding="utf-8")
        log(f"queue candidates: {len(queue)} (attempted: {sorted(attempted)})")

        # 2. Load durable state.
        state = state_store.load()
        state_path.write_text(
            json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

        # 3. Let the supervised Prolog actor select work.
        decision = run_queue_actor(
            cfg, queue_path, state_path, decision_path, trace_path, dict(os.environ)
        )
        if decision.get("action") == "idle":
            log(f"idle: {decision.get('reason', 'no eligible target')}")
            return PassResult(outcome="idle")

        issue_number = int(decision["issue_number"])
        issue = decision.get("selected_issue") or {}
        run_id = (
            f"svc-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
            f"-{pass_index}-{secrets.token_hex(3)}"
        )
        branch = f"{AGENT_NAME}/{utc_date()}-{run_id}"
        run_dir_rel = Path(cfg.run_root) / f"{utc_date()}-{run_id}"
        run_dir = cfg.repo_root / run_dir_rel

        stage_run_artifacts(cfg, run_dir, decision, issue, decision_path, trace_path)
        write_run_manifest(cfg, run_dir, run_id, branch, issue_number)
        log(
            f"selected #{issue_number} priority={decision.get('priority')} "
            f"run_id={run_id} branch={branch}"
        )
        attempted.add(issue_number)

        if cfg.dry_run:
            log("dry run: stopping before model routing and research")
            return PassResult(outcome="run", issue_number=issue_number, detail=run_id)

    try:
        # 4. Expert model route (or the explicit gateway override).
        route = resolve_model_route(
            cfg, run_dir, str(decision.get("priority", "normal"))
        )
        model = route["model"]
        effort = route["reasoning"]["effort"]
        update_run_manifest(run_dir, {"model_route": route})
        log(f"model route: {model} ({route.get('tier')}) reasoning={effort}")

        # 5. Bounded read-only research.
        env = research_env(cfg)
        status = run_research(cfg, run_dir, run_dir / "request.md", model, effort, env)
        update_run_manifest(
            run_dir,
            {"status": "researched" if status == 0 else "rlm_failed"},
        )
        if status != 0:
            report = write_failure_report(cfg, run_dir)
            if client is not None:
                body = (
                    "## Auto-Dig live-run failure\n\n"
                    f"- Run: `{run_id}`\n"
                    f"- Prolog-RLM: `{cfg.prolog_rlm_ref}`\n"
                    f"- Model route: `{model}`, reasoning `{effort}`\n\n"
                )
                if report is not None:
                    body += report.read_text(encoding="utf-8")
                else:
                    body += "No sanitized failure report was produced."
                client.add_comment(issue_number, body)
            log(f"research failed for #{issue_number} (exit {status})")
            return PassResult(outcome="failed", issue_number=issue_number, detail=run_id)

        result = json.loads((run_dir / "rlm-result.json").read_text(encoding="utf-8"))
        if (
            result.get("schema") != "prolog-rlm.trace.v1"
            or result.get("name") != "auto_dig_rlm_result"
        ):
            raise ValueError("rlm-result.json failed the trace envelope contract")
        report_path = run_dir / "report.md"
        if not report_path.is_file() or not report_path.stat().st_size:
            raise ValueError("research passed but no substantive report.md was emitted")
        # The receipt embeds the findings; read the report before the push
        # because the run directory leaves this worktree with the branch.
        report_text = report_path.read_text(encoding="utf-8")

        # 6. Push the isolated run branch. The manifest records everything
        # knowable before the push ("researched" plus the run contract);
        # pushed/receipt state is durably recorded in the actor state and
        # the issue receipt instead, because the run directory leaves this
        # worktree once the branch is pushed and we switch back.
        pushed = push_run_branch(cfg, run_dir_rel, branch, run_id)
        log(f"pushed {branch} at {pushed}")

        # 7. Advance durable state only after a successful push.
        state_store.save(advance_state(decision, branch, run_id))

        # 8. Post the receipt comment with the embedded findings report.
        if client is not None:
            client.add_comment(
                issue_number,
                render_receipt_comment(
                    cfg, run_id, branch, model, effort, report=report_text
                ),
            )
        log(f"pass complete for #{issue_number} (branch {branch})")
        return PassResult(outcome="run", issue_number=issue_number, detail=run_id)
    except Exception as exc:  # noqa: BLE001 - pass isolation boundary
        log(f"pass failed for #{issue_number}: {exc}")
        return PassResult(outcome="failed", issue_number=issue_number, detail=str(exc))


# ---------------------------------------------------------------------------
# Drain


def drain(cfg: ServiceConfig) -> int:
    verify_prolog_rlm_checkout(cfg)
    client: ForgejoClient | None = None
    if cfg.queue_file is None or cfg.state_file is None:
        if cfg.token is None and cfg.queue_file is None:
            log(
                "no Forgejo token found (AUTO_DIG_FORGE_TOKEN/FORGEJO_TOKEN); "
                "anonymous read will fail on private repositories"
            )
        client = ForgejoClient(cfg)
    state_store = StateStore(cfg, client)

    started = time.monotonic()
    completed = 0
    failures = 0
    attempted: set[int] = set()

    while True:
        result = run_one_pass(cfg, client, state_store, completed + failures + 1, attempted)
        if result.outcome == "idle":
            break
        completed += 1
        if result.outcome == "failed":
            failures += 1
        if cfg.max_issues and completed >= cfg.max_issues:
            log(f"--max-issues {cfg.max_issues} reached")
            break
        if cfg.time_budget and time.monotonic() - started >= cfg.time_budget:
            log(f"--time-budget {cfg.time_budget}s reached")
            break
    log(f"drain finished: {completed} passes ({failures} failed)")
    return 1 if failures else 0


def main(argv: list[str]) -> int:
    cfg = load_config(argv)
    if cfg.loop and cfg.dry_run:
        die("--loop cannot be combined with --dry-run")
    if not cfg.loop:
        return drain(cfg)
    log(f"service mode: draining git.starintel.actor issues every {cfg.interval}s")
    while True:
        try:
            drain(cfg)
        except (ForgejoError, RuntimeError, ValueError) as exc:
            log(f"drain error: {exc}")
        time.sleep(cfg.interval)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
