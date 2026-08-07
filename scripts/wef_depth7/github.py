from __future__ import annotations

import base64
import json
import urllib.error
import urllib.parse
from typing import Any, Iterable, Iterator, Mapping, Sequence

from .model import DEPLOYMENT_MARKERS, Collector, Observation, TargetPlan, keyword_hits


class GitHubCollector(Collector):
    name = "github"

    def _get(self, path: str, params: Sequence[tuple[str, str]] = ()) -> tuple[Any, str]:
        url = f"https://api.github.com/{path.lstrip('/')}"
        if params:
            url = f"{url}?{urllib.parse.urlencode(params)}"
        return self.client.json(url), url

    def _repo_observations(self, target: TargetPlan, repository: str) -> Iterator[Observation]:
        repo, repo_url = self._get(f"repos/{repository}")
        yield Observation(self.name, target.target_id, "github-repository", repo_url, repo, keyword_hits(repo, target.keywords))
        for kind, endpoint in (
            ("github-forks", f"repos/{repository}/forks"),
            ("github-releases", f"repos/{repository}/releases"),
            ("github-deployments", f"repos/{repository}/deployments"),
            ("github-workflows", f"repos/{repository}/actions/workflows"),
        ):
            try:
                payload, url = self._get(endpoint, (("per_page", "100"),))
            except (OSError, ValueError, urllib.error.URLError, json.JSONDecodeError):
                continue
            yield Observation(self.name, target.target_id, kind, url, payload, keyword_hits(payload, target.keywords))
        branch = str(repo.get("default_branch") or "main")
        try:
            tree, tree_url = self._get(f"repos/{repository}/git/trees/{urllib.parse.quote(branch, safe='')}", (("recursive", "1"),))
        except (OSError, ValueError, urllib.error.URLError, json.JSONDecodeError):
            return
        entries = tree.get("tree", []) if isinstance(tree, Mapping) else []
        candidates = [
            item
            for item in entries
            if item.get("type") == "blob" and any(marker in str(item.get("path", "")).casefold() for marker in DEPLOYMENT_MARKERS)
        ][: self.args.github_file_limit]
        yield Observation(
            self.name,
            target.target_id,
            "github-deployment-tree",
            tree_url,
            {"repository": repository, "branch": branch, "files": candidates},
            keyword_hits(candidates, target.keywords),
        )
        for item in candidates:
            path = str(item.get("path", ""))
            try:
                content, content_url = self._get(f"repos/{repository}/contents/{urllib.parse.quote(path)}", (("ref", branch),))
            except (OSError, ValueError, urllib.error.URLError, json.JSONDecodeError):
                continue
            if not isinstance(content, Mapping) or content.get("encoding") != "base64" or int(content.get("size") or 0) > self.args.max_document_bytes:
                continue
            decoded = base64.b64decode(str(content.get("content", "")), validate=False).decode("utf-8", errors="replace")
            payload = {"repository": repository, "branch": branch, "path": path, "sha": content.get("sha"), "content": decoded[:250_000]}
            yield Observation(self.name, target.target_id, "github-deployment-file", content_url, payload, keyword_hits(payload, target.keywords))

    def collect(self, target: TargetPlan) -> Iterable[Observation]:
        for repository in target.github_repositories:
            try:
                yield from self._repo_observations(target, repository)
            except (OSError, ValueError, urllib.error.URLError, json.JSONDecodeError):
                continue
        for query in target.github_queries:
            try:
                payload, url = self._get("search/repositories", (("q", query), ("per_page", "100")))
            except (OSError, ValueError, urllib.error.URLError, json.JSONDecodeError):
                continue
            yield Observation(self.name, target.target_id, "github-repository-search", url, payload, keyword_hits(payload, target.keywords))
