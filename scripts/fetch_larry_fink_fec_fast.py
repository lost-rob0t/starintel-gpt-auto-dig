from __future__ import annotations

import json
import os
import time
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import fetch_larry_fink_fec as ledger

# FEC reports contributor names surname-first. These variants cover the
# documented name forms; the base generator also runs a FINK + BLACKROCK query.
ledger.NAME_QUERIES = ["FINK, LAURENCE", "FINK, LARRY"]


def endpoint_api_get(endpoint: str, params: dict[str, Any]):
    """Query OpenFEC with its endpoint-specific public browser credential."""
    key_name = "FEC_API_KEY_SCHEDULE_A" if endpoint.startswith("/schedules/schedule_a/") else "FEC_API_KEY"
    api_key = os.environ.get(key_name)
    if not api_key:
        raise RuntimeError(f"Missing {key_name}")

    query_params = dict(params)
    # An omitted cycle filter returns the complete available transaction history
    # in one targeted search instead of repeating the query for every cycle.
    query_params.pop("two_year_transaction_period", None)

    rows: list[dict[str, Any]] = []
    audit_urls: list[str] = []
    page = 1
    while True:
        query = dict(query_params)
        query.update({"api_key": api_key, "per_page": 100, "page": page})
        url = f"{ledger.BASE}{endpoint}?{urlencode(query, doseq=True)}"
        audit_urls.append(url.replace(f"api_key={api_key}", "api_key=REDACTED"))
        request = Request(url, headers={"User-Agent": "starintel-gpt-auto-dig/1.0"})
        for attempt in range(5):
            try:
                with urlopen(request, timeout=60) as response:
                    payload = json.load(response)
                break
            except Exception:
                if attempt == 4:
                    raise
                time.sleep(2 ** attempt)
        results = payload.get("results", [])
        rows.extend(results)
        pages = int(payload.get("pagination", {}).get("pages") or 1)
        if page >= pages or not results:
            break
        page += 1
    return rows, audit_urls


ledger.api_get = endpoint_api_get

# Committee IDs and filing identifiers remain in every transaction. Avoiding
# one extra request per committee keeps the public-data fetch bounded.
ledger.committee_lookup = lambda ids: ({}, [])

if __name__ == "__main__":
    ledger.main()
