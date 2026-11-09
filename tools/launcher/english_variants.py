#!/usr/bin/env python3
"""Regenerate complete en-US/en-GB catalogs when new launcher UI keys are introduced.

The base English catalog contains explicit translations for legacy French-source
Neural Rendering strings. Preserve those, add any new source strings, and apply
British spelling overrides only to en-GB. This does not alter any other locale.
"""
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[2]
LANG = ROOT / "headless/prosperoeden/ui/lang"

def regenerate() -> None:
    module = runpy.run_path(str(ROOT / "tools/launcher/strings.py"))
    current = module["marked_text"]()
    for genre in module["DYNAMIC_LIBRARY_GENRES"]:
        current.setdefault(genre, ["eden_services.cpp: runtime library category"])
    existing_us = module["parse_po"](LANG / "en-US.po")
    for tag in ("en-US", "en-GB"):
        translations = {
            key: (existing_us.get(key, key).replace("Color", "Colour").replace("Customize", "Customise")
                  if tag == "en-GB" else existing_us.get(key, key))
            for key in current
        }
        path = LANG / (tag + ".po")
        module["write_catalog"](path, current, translations, tag)
        print(f"{tag}: {len(translations)} complete active + runtime genre entries")

if __name__ == "__main__":
    regenerate()
