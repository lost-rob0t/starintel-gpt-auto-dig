from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

SCRIPT = Path("scripts/check-auto-dig-control.py")


def run_control(control: dict | None) -> subprocess.CompletedProcess[str]:
    with TemporaryDirectory() as tmp:
        path = Path(tmp) / "control.json"
        if control is not None:
            path.write_text(json.dumps(control), encoding="utf-8")
        env = dict(os.environ)
        env["AUTO_DIG_CONTROL_FILE"] = str(path)
        return subprocess.run(
            [sys.executable, str(SCRIPT)],
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )


def test_paused_control_blocks() -> None:
    result = run_control(
        {"schema": "auto-dig-control.v1", "enabled": False, "state": "paused", "reason": "test"}
    )
    assert result.returncode == 75
    assert "AUTO-DIG PAUSED" in result.stdout


def test_running_control_allows() -> None:
    result = run_control(
        {"schema": "auto-dig-control.v1", "enabled": True, "state": "running"}
    )
    assert result.returncode == 0
    assert "AUTO-DIG ENABLED" in result.stdout


def test_missing_control_fails_closed() -> None:
    result = run_control(None)
    assert result.returncode == 3
    assert "AUTO-DIG BLOCKED" in result.stderr
