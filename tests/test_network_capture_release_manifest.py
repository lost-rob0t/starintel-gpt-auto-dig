from __future__ import annotations

import json
from pathlib import Path


def test_network_capture_release_manifest_is_additive_v09():
    path = Path(__file__).resolve().parents[1] / "schemas" / "starintel-network-capture-v0.9.2.manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    assert manifest["schema_version"] == "0.9.0"
    assert manifest["release_version"] == "0.9.2"
    assert manifest["profile_version"] == "0.9.2"
    assert manifest["compatibility"] == "additive-v0.9"
    assert manifest["dtypes"] == ["http-transaction", "web-capture"]
    assert manifest["captcha_capability"] == "captcha.solve"
    assert manifest["security"]["opaque_context_refs"] == [
        "browser_session_ref",
        "network_context_ref",
    ]
