from __future__ import annotations

import hashlib
import html
import os
import re
import urllib.parse
from datetime import datetime, timezone
from typing import Any, Iterator

from .constants import ARCHIVE_SLUGS, AUTH_ENV, BASE_URL, PROFILE_PATH_DTYPES, TERMS_URL


def clean(value: Any) -> str:
    return " ".join(html.unescape(str(value or "")).split())


def first(value: Any) -> str:
    if isinstance(value, list):
        return next((candidate for item in value if (candidate := first(item))), "")
    if isinstance(value, dict):
        return next((candidate for key in ("name", "headline", "description", "url", "@id") if (candidate := first(value.get(key)))), "")
    return clean(value)


def normalize_resource_url(value: str, *, base: str = BASE_URL) -> str:
    parsed = urllib.parse.urlsplit(urllib.parse.urljoin(base, clean(value)))
    host = parsed.hostname.lower() if parsed.hostname else ""
    if host == "influencewatch.org":
        host = "www.influencewatch.org"
    scheme = "https" if host == "www.influencewatch.org" else (parsed.scheme or "https")
    netloc = f"{host}:{parsed.port}" if parsed.port else host
    path = re.sub(r"/{2,}", "/", parsed.path or "/")
    return urllib.parse.urlunsplit((scheme, netloc, path, parsed.query, ""))


def canonicalize_url(value: str, *, base: str = BASE_URL) -> str:
    parsed = urllib.parse.urlsplit(normalize_resource_url(value, base=base))
    path = parsed.path if parsed.path == "/" or parsed.path.endswith("/") else f"{parsed.path}/"
    return urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, path, "", ""))


def profile_kind(value: str) -> tuple[str, str] | None:
    parsed = urllib.parse.urlsplit(canonicalize_url(value))
    if parsed.hostname != "www.influencewatch.org":
        return None
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) < 2:
        return None
    prefix, slug = parts[0], parts[1]
    if prefix not in PROFILE_PATH_DTYPES or slug in ARCHIVE_SLUGS or slug == "page":
        return None
    return prefix, PROFILE_PATH_DTYPES[prefix]


def normalize_datetime(value: Any) -> str | None:
    text = clean(value)
    if not text:
        return None
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
        text += "T00:00:00+00:00"
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def content_digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def require_network_authorization(*, authorized: bool, environment: dict[str, str] | None = None) -> None:
    env = environment if environment is not None else os.environ
    if authorized or clean(env.get(AUTH_ENV)).lower() in {"1", "true", "yes"}:
        return
    raise SystemExit(
        "InfluenceWatch Terms of Use effective May 1, 2026 prohibit automated scraping or systematic downloading "
        "without express written consent. Obtain authorization, then pass --authorized or set "
        f"{AUTH_ENV}=1. Terms: {TERMS_URL}"
    )


def iter_json_ld_nodes(value: Any) -> Iterator[dict[str, Any]]:
    if isinstance(value, dict):
        yield value
        for item in value.get("@graph", []) if isinstance(value.get("@graph"), list) else []:
            yield from iter_json_ld_nodes(item)
    elif isinstance(value, list):
        for item in value:
            yield from iter_json_ld_nodes(item)
