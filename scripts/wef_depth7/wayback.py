from __future__ import annotations

import json
import urllib.error
import urllib.parse
from typing import Any, Iterable

from .model import Collector, Observation, TargetPlan, keyword_hits


class WaybackCollector(Collector):
    name = "wayback"

    def collect(self, target: TargetPlan) -> Iterable[Observation]:
        endpoint = str(self.config.get("wayback_cdx", "https://web.archive.org/cdx/search/cdx"))
        for pattern in target.wayback_patterns:
            params = [
                ("url", pattern),
                ("output", "json"),
                ("fl", "timestamp,original,statuscode,mimetype,digest,length"),
                ("filter", "statuscode:200"),
                ("collapse", "digest"),
                ("limit", str(self.args.archive_limit)),
            ]
            url = f"{endpoint}?{urllib.parse.urlencode(params)}"
            try:
                rows = self.client.json(url)
            except (OSError, ValueError, urllib.error.URLError, json.JSONDecodeError):
                continue
            if not isinstance(rows, list) or len(rows) < 2:
                continue
            header = rows[0]
            for row in rows[1:]:
                capture = dict(zip(header, row, strict=False))
                original = str(capture.get("original", ""))
                hits = keyword_hits((original, capture), target.keywords)
                if not hits and "columbus" not in original.casefold():
                    continue
                timestamp = str(capture.get("timestamp", ""))
                capture_url = f"https://web.archive.org/web/{timestamp}id_/{original}"
                payload: dict[str, Any] = {"capture": capture}
                if self.args.archive_content:
                    try:
                        body, headers, final_url = self.client.fetch(capture_url, max_bytes=self.args.max_document_bytes)
                        payload["content"] = body.decode("utf-8", errors="replace")[:250_000]
                        payload["headers"] = dict(headers)
                        capture_url = final_url
                        hits = keyword_hits(payload, target.keywords) or hits
                    except (OSError, ValueError, urllib.error.URLError):
                        pass
                yield Observation(self.name, target.target_id, "archive-capture", capture_url, payload, hits)
