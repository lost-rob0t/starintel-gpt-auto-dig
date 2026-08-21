from __future__ import annotations

import argparse
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

TRANSACTIONS_API = "https://api.usaspending.gov/api/v2/transactions/"
DEFAULT_GENERATED_AWARD_IDS = (
    "CONT_AWD_15F06725F0001209_1549_GS00F240CA_4732",
    "CONT_AWD_15F06725F0001838_1549_GS00F240CA_4732",
    "CONT_AWD_15F06726F0000362_1549_GS10F0473Y_4732",
)
DEFAULT_USER_AGENT = (
    "StarIntel-USAspending-Transaction-Collector/1.0 "
    "(+https://github.com/lost-rob0t/starintel-gpt-auto-dig)"
)


def utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def request_json(
    url: str,
    *,
    body: dict[str, Any],
    timeout: float,
    retries: int,
    user_agent: str,
) -> dict[str, Any]:
    encoded = json.dumps(body, separators=(",", ":")).encode("utf-8")
    request = Request(
        url,
        data=encoded,
        method="POST",
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": user_agent,
        },
    )
    for attempt in range(retries):
        try:
            with urlopen(request, timeout=timeout) as response:
                payload = json.loads(response.read())
            if not isinstance(payload, dict):
                raise TypeError("USAspending returned a non-object response")
            return payload
        except (HTTPError, URLError, TimeoutError):
            if attempt + 1 >= retries:
                raise
            time.sleep(2**attempt)
    raise AssertionError("unreachable")


def transaction_payload(
    generated_award_id: str,
    *,
    page: int,
    limit: int,
) -> dict[str, Any]:
    if not generated_award_id.strip():
        raise ValueError("generated award ID cannot be empty")
    if page < 1:
        raise ValueError("page must be positive")
    if limit < 1 or limit > 100:
        raise ValueError("limit must be between 1 and 100")
    return {
        "award_id": generated_award_id.strip(),
        "page": page,
        "limit": limit,
        "sort": "action_date",
        "order": "desc",
    }


def transaction_identity(transaction: dict[str, Any]) -> str:
    for field in (
        "generated_transaction_unique_id",
        "transaction_id",
        "modification_number",
    ):
        value = transaction.get(field)
        if value not in (None, ""):
            return f"{field}:{value}"
    canonical = json.dumps(
        transaction,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return f"sha256:{sha256_bytes(canonical)}"


def award_url(generated_award_id: str) -> str:
    return f"https://www.usaspending.gov/award/{generated_award_id}"


def raw_record(
    *,
    generated_award_id: str,
    transaction: dict[str, Any],
    retrieved_at: str,
) -> dict[str, Any]:
    canonical = json.dumps(
        transaction,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return {
        "source": "usaspending",
        "record_type": "award-transaction",
        "source_url": award_url(generated_award_id),
        "retrieved_at": retrieved_at,
        "sha256": sha256_bytes(canonical),
        "generated_award_id": generated_award_id,
        "transaction_identity": transaction_identity(transaction),
        "payload": transaction,
    }


def has_next_page(response: dict[str, Any], results: list[Any], *, page: int, limit: int) -> bool:
    metadata = response.get("page_metadata")
    if isinstance(metadata, dict):
        for field in ("hasNext", "has_next_page", "has_next"):
            value = metadata.get(field)
            if isinstance(value, bool):
                return value
        total = metadata.get("total")
        if isinstance(total, int):
            return page * limit < total
    return len(results) == limit


def collect_award_transactions(
    generated_award_id: str,
    *,
    limit: int,
    max_pages: int,
    timeout: float,
    retries: int,
    user_agent: str,
    retrieved_at: str,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    for page in range(1, max_pages + 1):
        response = request_json(
            TRANSACTIONS_API,
            body=transaction_payload(generated_award_id, page=page, limit=limit),
            timeout=timeout,
            retries=retries,
            user_agent=user_agent,
        )
        raw_results = response.get("results") or []
        if not isinstance(raw_results, list):
            raise TypeError("USAspending transactions response has non-list results")
        results = [item for item in raw_results if isinstance(item, dict)]
        for transaction in results:
            identity = transaction_identity(transaction)
            if identity in seen:
                continue
            seen.add(identity)
            records.append(
                raw_record(
                    generated_award_id=generated_award_id,
                    transaction=transaction,
                    retrieved_at=retrieved_at,
                )
            )
        if not results or not has_next_page(response, raw_results, page=page, limit=limit):
            break
    return sorted(
        records,
        key=lambda row: (
            str(row["payload"].get("action_date") or ""),
            str(row["transaction_identity"]),
        ),
        reverse=True,
    )


def collect_transactions(
    generated_award_ids: Iterable[str],
    *,
    limit: int,
    max_pages: int,
    timeout: float,
    retries: int,
    user_agent: str,
    retrieved_at: str,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for generated_award_id in dict.fromkeys(
        value.strip() for value in generated_award_ids if value.strip()
    ):
        records.extend(
            collect_award_transactions(
                generated_award_id,
                limit=limit,
                max_pages=max_pages,
                timeout=timeout,
                retries=retries,
                user_agent=user_agent,
                retrieved_at=retrieved_at,
            )
        )
    return records


def write_jsonl(records: Iterable[dict[str, Any]], output: Path) -> int:
    unique: dict[tuple[str, str], dict[str, Any]] = {}
    for record in records:
        key = (
            str(record.get("generated_award_id") or ""),
            str(record.get("transaction_identity") or ""),
        )
        unique[key] = record
    ordered = [
        unique[key]
        for key in sorted(
            unique,
            key=lambda item: (item[0], item[1]),
        )
    ]
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        for record in ordered:
            handle.write(
                json.dumps(
                    record,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                )
            )
            handle.write("\n")
    return len(ordered)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Collect USAspending transaction histories for FBI TSC awards, "
            "including obligations, deobligations and modifications."
        )
    )
    parser.add_argument("--generated-award-id", action="append", default=[])
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("imports/fbi-procurement/transactions.jsonl"),
    )
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--max-pages", type=int, default=100)
    parser.add_argument("--timeout", type=float, default=60.0)
    parser.add_argument("--retries", type=int, default=4)
    parser.add_argument("--user-agent", default=DEFAULT_USER_AGENT)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.limit < 1 or args.limit > 100:
        raise SystemExit("--limit must be between 1 and 100")
    if args.max_pages < 1:
        raise SystemExit("--max-pages must be positive")
    if args.timeout <= 0:
        raise SystemExit("--timeout must be positive")
    if args.retries < 1:
        raise SystemExit("--retries must be positive")

    records = collect_transactions(
        args.generated_award_id or DEFAULT_GENERATED_AWARD_IDS,
        limit=args.limit,
        max_pages=args.max_pages,
        timeout=args.timeout,
        retries=args.retries,
        user_agent=args.user_agent,
        retrieved_at=utc_now(),
    )
    count = write_jsonl(records, args.output)
    print(json.dumps({"output": str(args.output), "records": count}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
