from __future__ import annotations

import csv
import io
import json
import urllib.error
from typing import Any, Iterable, Iterator, Mapping

from .model import Collector, Observation, PageParser, TargetPlan, keyword_hits


class AuditorCollector(Collector):
    name = "auditor"

    @staticmethod
    def _format_hint(link: Mapping[str, str], headers: Mapping[str, str]) -> str:
        haystack = f"{link.get('text', '')} {link.get('url', '')} {headers.get('Content-Type', '')}".casefold()
        if "json" in haystack:
            return "json"
        if "csv" in haystack:
            return "csv"
        return "text"

    def _rows(self, body: bytes, format_hint: str) -> Iterator[tuple[int, Any]]:
        text = body.decode("utf-8-sig", errors="replace")
        if format_hint == "json":
            value = json.loads(text)
            records = value if isinstance(value, list) else value.get("data", value.get("records", [])) if isinstance(value, Mapping) else []
            if isinstance(records, list):
                for index, record in enumerate(records, 1):
                    if index > self.args.auditor_row_limit:
                        break
                    yield index, record
                return
        if format_hint == "csv":
            for index, record in enumerate(csv.DictReader(io.StringIO(text)), 1):
                if index > self.args.auditor_row_limit:
                    break
                yield index, record
            return
        for index, line in enumerate(text.splitlines(), 1):
            if index > self.args.auditor_row_limit:
                break
            yield index, line

    def collect(self, target: TargetPlan) -> Iterable[Observation]:
        explorer = str(self.config.get("auditor_explorer", "https://www.columbusauditor.org/Data-Hub/data-sets-explorer/"))
        try:
            body, headers, final_url = self.client.fetch(explorer, max_bytes=8_000_000)
        except (OSError, ValueError, urllib.error.URLError):
            return
        parser = PageParser(final_url)
        parser.feed(body.decode("utf-8", errors="replace"))
        links = []
        for text, href in parser.links:
            haystack = f"{text} {href}".casefold()
            if any(term in haystack for term in ("payment", "vendor", "invoice", "purchase order", "csv", "json")):
                links.append({"text": text, "url": href})
        payload = {"title": parser.title, "links": links, "headers": dict(headers)}
        yield Observation(self.name, target.target_id, "auditor-dataset-index", final_url, payload, keyword_hits(payload, target.keywords))
        if not self.args.auditor_download:
            return
        emitted = 0
        for link in links:
            if emitted >= self.args.auditor_hit_limit:
                break
            try:
                dataset, dataset_headers, dataset_url = self.client.fetch(link["url"], max_bytes=self.args.max_dataset_bytes)
                rows = self._rows(dataset, self._format_hint(link, dataset_headers))
            except (OSError, ValueError, urllib.error.URLError, json.JSONDecodeError, csv.Error):
                continue
            for row_number, row in rows:
                row_hits = keyword_hits(row, target.keywords)
                if not row_hits:
                    continue
                yield Observation(
                    self.name,
                    target.target_id,
                    "auditor-dataset-row",
                    dataset_url,
                    {"row_number": row_number, "row": row, "headers": dict(dataset_headers)},
                    row_hits,
                )
                emitted += 1
                if emitted >= self.args.auditor_hit_limit:
                    break
