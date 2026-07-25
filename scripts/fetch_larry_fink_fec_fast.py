from __future__ import annotations

import json
import os
import re
import time
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import fetch_larry_fink_fec as ledger

# FEC reports contributor names surname-first. These variants cover the
# documented name forms; the base generator also runs a FINK + BLACKROCK query.
ledger.NAME_QUERIES = ["FINK, LAURENCE", "FINK, LARRY"]
KNOWN_FINK_CITIES = {"NEW YORK", "NEW YORK CITY", "MANHATTAN", "NORTH SALEM"}


def words(value: Any) -> set[str]:
    return set(re.sub(r"[^A-Z ]+", " ", str(value or "").upper()).split())


def strict_identity_score(row: dict[str, Any], kind: str):
    """Reject fuzzy surname matches and require stronger refund geography."""
    name_key = "contributor_name" if kind == "receipt" else "recipient_name"
    city_key = "contributor_city" if kind == "receipt" else "recipient_city"
    state_key = "contributor_state" if kind == "receipt" else "recipient_state"
    zip_key = "contributor_zip" if kind == "receipt" else "recipient_zip"
    name_tokens = words(row.get(name_key))
    if "FINK" not in name_tokens or not ({"LAURENCE", "LARRY"} & name_tokens):
        return 0.0, ["surname was not exactly FINK or first name did not match"]

    reasons = ["exact FINK surname token and Laurence/Larry first name"]
    score = 0.45
    city = re.sub(r"[^A-Z ]+", " ", str(row.get(city_key) or "").upper()).strip()
    state = str(row.get(state_key) or "").upper()
    zip_code = str(row.get(zip_key) or "")

    if kind == "receipt":
        employer = " ".join(words(row.get("contributor_employer")))
        occupation = " ".join(words(row.get("contributor_occupation")))
        if "BLACKROCK" in employer or ("BLACK" in employer and "ROCK" in employer):
            score += 0.35
            reasons.append("BlackRock employer")
        elif "FIRST" in employer and "BOSTON" in employer:
            score += 0.25
            reasons.append("historical First Boston employer")
        elif employer and employer not in {"NONE", "NOT EMPLOYED", "RETIRED", "SELF EMPLOYED"}:
            reasons.append(f"other employer: {employer}")
        if any(term in occupation for term in ledger.EXECUTIVE_TERMS):
            score += 0.12
            reasons.append("executive or finance occupation")
        if state == "NY":
            score += 0.04
            reasons.append("New York state")
        if city in KNOWN_FINK_CITIES:
            score += 0.03
            reasons.append("consistent New York locality")
        if zip_code.startswith(("100", "105")):
            score += 0.01
            reasons.append("consistent New York ZIP prefix")
    else:
        amount = float(row.get("disbursement_amount") or 0)
        if amount <= 0:
            return 0.0, reasons + ["non-positive Schedule B adjustment"]
        if state == "NY":
            score += 0.10
            reasons.append("New York state")
        if city in KNOWN_FINK_CITIES:
            score += 0.10
            reasons.append("known Fink New York locality")
        if zip_code.startswith(("100", "105")):
            score += 0.05
            reasons.append("consistent New York ZIP prefix")

    return min(score, 1.0), reasons


def endpoint_api_get(endpoint: str, params: dict[str, Any]):
    """Query OpenFEC using the same key selection and origin as FEC.gov."""
    key_name = "FEC_API_KEY_SCHEDULE_A" if endpoint.startswith("/schedules/schedule_a/") else "FEC_API_KEY"
    api_key = os.environ.get(key_name)
    if not api_key:
        raise RuntimeError(f"Missing {key_name}")

    query_params = dict(params)
    query_params.pop("two_year_transaction_period", None)

    rows: list[dict[str, Any]] = []
    audit_urls: list[str] = []
    page = 1
    while True:
        query = dict(query_params)
        query.update({"api_key": api_key, "per_page": 100, "page": page})
        url = f"{ledger.BASE}{endpoint}?{urlencode(query, doseq=True)}"
        audit_urls.append(url.replace(f"api_key={api_key}", "api_key=REDACTED"))
        request = Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/140 Safari/537.36",
                "Accept": "application/json, text/plain, */*",
                "Origin": "https://www.fec.gov",
                "Referer": "https://www.fec.gov/data/receipts/individual-contributions/",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-site",
            },
        )
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


ledger.identity_score = strict_identity_score
ledger.api_get = endpoint_api_get

if __name__ == "__main__":
    ledger.main()
