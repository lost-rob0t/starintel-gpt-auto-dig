from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from bs4 import BeautifulSoup

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
MODULE_PATH = SCRIPTS / "scrape_violent_offender_recovery_entry.py"
SPEC = importlib.util.spec_from_file_location("violent_recovery_entry", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_franklin_current_radio_is_serialized():
    form = BeautifulSoup(
        """
        <form>
          <input type="radio" id="statusCurrent" name="offenderStatus" value="Current">
          <label for="statusCurrent">Current</label>
          <input type="radio" id="statusAll" name="offenderStatus" value="All">
          <label for="statusAll">All</label>
        </form>
        """,
        "html.parser",
    ).find("form")
    payload: dict[str, str] = {}
    MODULE.set_current_status(form, payload)
    assert payload == {"offenderStatus": "Current"}


def test_summit_points_at_current_official_report_pdf():
    assert MODULE.fixups.recovery.RECOVERY_SOURCES["summit"]["url"].endswith("/activeoffenderreport.pdf")
