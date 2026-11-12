#!/usr/bin/env python3
"""Fast no-build gate for separate PS5 English US and UK launcher catalogs."""
from pathlib import Path
import re
import runpy

root = Path(__file__).resolve().parents[1]
language_dir = root / "headless/prosperoeden/ui/lang"
module = runpy.run_path(str(root / "tools/launcher/strings.py"))
parse_po = module["parse_po"]
template = parse_po(root / "tools/launcher/launcher.pot")
us = parse_po(language_dir / "en-US.po")
uk = parse_po(language_dir / "en-GB.po")
expected = set(template) | set(module["DYNAMIC_LIBRARY_GENRES"])
assert len(list(language_dir.glob("*.po"))) == 31, "All 31 official PS5 catalogs are required"
# The guide workflow deliberately checks out catalogs and the template only;
# its sparse tree omits the source files marked_text() needs. The full launcher
# workflow checks live-source parity when settings_store.h is present.
if (root / "headless/settings_store.h").is_file():
    live = set(module["marked_text"]())
    assert set(template) == live, "Launcher template is stale relative to marked UI sources"
assert len(template) >= 566 and len(expected) >= 596, (
    "Launcher texts or runtime genres unexpectedly shrank")
assert len(expected) - len(template) == len(module["DYNAMIC_LIBRARY_GENRES"]), (
    "Launcher template overlaps or omits dynamic runtime genres")
assert set(us) == set(uk) == expected, "English variants have missing or stale msgids"
assert all(us[key] and uk[key] for key in expected), "Empty English translation"
assert all(uk[key] == us[key].replace("Color", "Colour").replace("Customize", "Customise")
           for key in expected), "UK catalog drifted from deliberate regional spelling differences"
regional = {key for key in expected if us[key] != uk[key]}
assert len(regional) >= 10 and uk["Customize"] == "Customise"
assert uk["Color 1 blue"] == "Colour 1 blue"
assert us["Intensité DLSS-NR"] == "DLSS-NR intensity", "Inherited French text not localized to English"
french_source = [key for key in template if re.search("[àâéèêîôùûç]", key, re.I)]
assert french_source and all(not re.search("[àâéèêîôùûç]", us[key], re.I)
                             for key in french_source), "Untranslated legacy French UI source keys"
core = (root / "headless/prosperoeden/pe/core/strings.cpp").read_text(encoding="utf-8")
assert 'return {"en-US"};' in core and 'return {"en-GB", "en-US"};' in core, (
    "Runtime must load the appropriate regional catalog")
print(f"ENGLISH_VARIANTS_PASS catalog_count=31 active={len(template)} "
      f"runtime_categories={len(expected)-len(template)} regional_differences={len(regional)}")
