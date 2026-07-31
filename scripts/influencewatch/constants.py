from __future__ import annotations

import urllib.parse

BASE_URL = "https://www.influencewatch.org/"
TERMS_URL = urllib.parse.urljoin(BASE_URL, "terms-of-use/")
DEFAULT_SITEMAP_URL = urllib.parse.urljoin(BASE_URL, "sitemap_index.xml")
DATASET = "influence-watch-db"
AUTH_ENV = "INFLUENCEWATCH_AUTHORIZED"
USER_AGENT_HEX_LENGTH = 64
MIN_REQUEST_DELAY = 1.0
MAX_RESPONSE_BYTES = 12 * 1024 * 1024
PROFILE_PATH_DTYPES = {
    "person": "person",
    "people": "person",
    "non-profit": "org",
    "organization": "org",
    "for-profit": "org",
    "labor-union": "org",
    "government-agency": "org",
    "political-party": "org",
    "influence-network": "entity",
}
ARCHIVE_SLUGS = set(PROFILE_PATH_DTYPES)
VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
BLOCK_TAGS = {
    "address", "article", "aside", "blockquote", "dd", "div", "dl", "dt",
    "figcaption", "footer", "h1", "h2", "h3", "h4", "h5", "h6", "header",
    "li", "main", "nav", "p", "section", "td", "th", "tr",
}
FIELD_LABELS = {
    "type", "issue areas", "ideological alignment", "occupation", "website",
    "location", "tax id", "fec id", "fec number", "formation", "founder",
    "founders", "executive director", "president", "chair", "chairman",
    "parent organization", "project of", "most recent filing", "budget",
    "assets", "revenue", "expenses",
}
