#!/usr/bin/env python3
from __future__ import annotations

import re

import scrape_violent_offender_recovery_fixups as fixups


def set_current_status(form, payload: dict[str, str]) -> None:
    """Select a current-inmate status whether the form uses select, radio, or checkbox controls."""
    original = fixups.core.form_field(form, ("status",), ("select",))
    select = form.find("select", attrs={"name": original}) if original else None
    if select:
        for option in select.find_all("option"):
            text = fixups.core.normalize_space(option.get_text(" "))
            if "current" in text.casefold():
                payload[original] = option.get("value", text)
                return

    for tag in form.find_all("input"):
        name = tag.get("name")
        if not name:
            continue
        input_type = (tag.get("type") or "text").casefold()
        if input_type not in {"radio", "checkbox"}:
            continue
        value = str(tag.get("value") or "")
        control_id = str(tag.get("id") or "")
        label = form.find("label", attrs={"for": control_id}) if control_id else None
        label_text = fixups.core.normalize_space(label.get_text(" ")) if label else ""
        parent_text = fixups.core.normalize_space(tag.parent.get_text(" ")) if tag.parent else ""
        haystack = " ".join((name, control_id, value, label_text, parent_text)).casefold()
        if "current" not in haystack:
            continue
        # Avoid unrelated controls where 'current' happens to occur elsewhere in the row.
        if not ("status" in haystack or label_text.casefold() == "current" or value.casefold() == "current"):
            continue
        payload[name] = value or "Current"
        return


# Franklin's public BookingFind page currently renders Offender Status=Current as
# an input control rather than the select assumed by the original adapter.
fixups.core.set_current_status = set_current_status

# The sheriff site's legacy Current-Inmate-Roster.html entry point no longer
# contains the report payload. Point at the current official head-count PDF.
fixups.recovery.RECOVERY_SOURCES["summit"]["url"] = (
    "https://sheriff.summitoh.net/files/31565/file/activeoffenderreport.pdf"
)

if __name__ == "__main__":
    raise SystemExit(fixups.recovery.main())
