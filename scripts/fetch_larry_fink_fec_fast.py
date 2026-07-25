from __future__ import annotations

import fetch_larry_fink_fec as ledger

# FEC reports contributor names surname-first. These two queries cover the
# documented first-name variants; the base generator also performs a separate
# FINK + BLACKROCK employer query.
ledger.NAME_QUERIES = ["FINK, LAURENCE", "FINK, LARRY"]

# Omitting the cycle filter asks OpenFEC for the complete available history in
# each targeted query. Keep the full cycle list in the generated coverage note.
_original_api_get = ledger.api_get


def lean_api_get(endpoint, params):
    query = dict(params)
    query.pop("two_year_transaction_period", None)
    return _original_api_get(endpoint, query)


ledger.api_get = lean_api_get

# Committee enrichment is useful presentation metadata but would require one
# extra API request per recipient and can exhaust DEMO_KEY. Transaction records
# retain committee IDs, filing IDs, image numbers, amounts, dates, and memo data.
ledger.committee_lookup = lambda ids: ({}, [])

if __name__ == "__main__":
    ledger.main()
