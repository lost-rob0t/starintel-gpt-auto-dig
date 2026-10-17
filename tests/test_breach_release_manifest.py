from __future__ import annotations

import json
from pathlib import Path


def test_breach_release_manifest_is_additive_v09():
    path = Path(__file__).resolve().parents[1] / "schemas" / "starintel-breach-v0.9.3.manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    assert manifest["schema_version"] == "0.9.0"
    assert manifest["release_version"] == "0.9.3"
    assert manifest["profile_version"] == "0.9.3"
    assert manifest["compatibility"] == "additive-v0.9"
    assert manifest["dtypes"] == ["breach-compilation", "paste"]
    assert manifest["base_profile"] == {
        "profile": "starintel-network-capture",
        "profile_version": "0.9.2",
    }
    assert manifest["security"]["credential_values_never_embedded"] is True
    assert manifest["security"]["artifact_reference_only"] == [
        "paste_body",
        "compilation_source_artifact",
    ]
