from __future__ import annotations

import json
import urllib.error
import urllib.parse
from typing import Iterable

from .model import Collector, Observation, TargetPlan, keyword_hits


class LegistarCollector(Collector):
    name = "legistar"
    expansions = ("Attachments", "Sponsors", "Relations", "Versions", "Histories")

    def collect(self, target: TargetPlan) -> Iterable[Observation]:
        root = str(self.config.get("legistar_root", "https://webapi.legistar.com/v1/columbus")).rstrip("/")
        top = min(max(self.args.page_size, 1), 1000)
        for page in range(self.args.max_pages):
            params = {"$top": str(top), "$skip": str(page * top), "$orderby": "MatterLastModifiedUtc desc"}
            url = f"{root}/Matters?{urllib.parse.urlencode(params)}"
            matters = self.client.json(url)
            if not isinstance(matters, list) or not matters:
                break
            for matter in matters:
                hits = keyword_hits(matter, target.keywords)
                if not hits:
                    continue
                matter_id = matter.get("MatterId")
                payload = {"matter": matter, "related": {}}
                if matter_id is not None:
                    for expansion in self.expansions:
                        endpoint = f"{root}/Matters/{matter_id}/{expansion}"
                        try:
                            payload["related"][expansion.casefold()] = self.client.json(endpoint)
                        except (OSError, ValueError, urllib.error.URLError, json.JSONDecodeError) as error:
                            payload["related"][expansion.casefold()] = {"error": str(error)}
                source_url = matter.get("MatterInSiteURL") or matter.get("MatterAgendaURL") or f"{root}/Matters/{matter_id}"
                yield Observation(self.name, target.target_id, "legistar-matter", str(source_url), payload, hits)
            if len(matters) < top:
                break
