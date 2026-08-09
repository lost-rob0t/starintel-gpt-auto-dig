#!/usr/bin/env python3
from __future__ import annotations

import scrape_violent_offender_recovery_fixups as fixups

# The sheriff site's legacy Current-Inmate-Roster.html entry point no longer
# contains the report payload. The current official head-count report is the
# PDF below; keep the parser source pointed at the actual data artifact.
fixups.recovery.RECOVERY_SOURCES["summit"]["url"] = (
    "https://sheriff.summitoh.net/files/31565/file/activeoffenderreport.pdf"
)

if __name__ == "__main__":
    raise SystemExit(fixups.recovery.main())
