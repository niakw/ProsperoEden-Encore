#!/usr/bin/env python3
"""Fast no-build CI contract for both PS5 English regional launcher catalogs."""
from pathlib import Path
import runpy

root = Path(__file__).resolve().parents[1]
language_dir = root / "headless/prosperoeden/ui/lang"
parse_po = runpy.run_path(str(root / "tools/launcher/strings.py"))["parse_po"]
source = parse_po(root / "tools/launcher/launcher.pot")
us = parse_po(language_dir / "en-US.po")
uk = parse_po(language_dir / "en-GB.po")
catalogs = {p.stem for p in language_dir.glob("*.po")}
assert len(catalogs) == 31, f"Expected 31 official PS5 catalogs, got {len(catalogs)}"
assert len(source) >= 500, "Launcher gettext source template is incomplete"
assert set(us) == set(uk) == set(source), "English regional catalogs have missing or stale entries"
assert all(us[key] == key for key in source), "US catalog must keep source US spelling"
regional = {key: key.replace("Color", "Colour").replace("Customize", "Customise")
            for key in source if "Color" in key or "Customize" in key}
assert len(regional) >= 10, "Not enough real English UK spelling cases"
assert all(uk[key] == regional.get(key, key) for key in source), (
    "UK catalog must use British spellings while preserving unrelated strings")
core = (root / "headless/prosperoeden/pe/core/strings.cpp").read_text(encoding="utf-8")
assert 'return {"en-US"};' in core and 'return {"en-GB", "en-US"};' in core, (
    "Runtime must load each English variant's own catalog")
print(f"ENGLISH_VARIANTS_PASS locales=31 catalog_entries={len(source)} uk_differences={len(regional)}")
