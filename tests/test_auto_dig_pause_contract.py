from __future__ import annotations

import json
from pathlib import Path


def test_repository_auto_dig_is_paused() -> None:
    control = json.loads(Path("config/auto-dig-control.json").read_text(encoding="utf-8"))

    assert control["schema"] == "auto-dig-control.v1"
    assert control["enabled"] is False
    assert control["state"] == "paused"
    assert control["allow_new_claims"] is False
    assert control["allow_new_passes"] is False
    assert control["allow_new_branches"] is False
    assert control["allow_new_pull_requests"] is False
    assert control["allow_state_advance"] is False
    assert control["resume_requires"] == "explicit operator instruction"
