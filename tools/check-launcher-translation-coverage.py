#!/usr/bin/env python3
"""Report exact active translations, reject obsolete catalog entries.

All 31 official PS5 interface catalogs must have full active-key coverage. Recent non-primary
locale texts include provisional machine-assisted translations: coverage and
placeholder checks do NOT replace human review or on-console typography QA.
"""
from pathlib import Path
import runpy

root = Path(__file__).resolve().parents[1]
module = runpy.run_path(str(root / "tools/launcher/strings.py"))
marked = set(module["marked_text"]())
read_po = module["parse_po"]
catalogs = sorted((root / "headless/prosperoeden/ui/lang").glob("*.po"))
assert len(catalogs) == 31, f"catalog count changed: {len(catalogs)}"
english_us = read_po(root / "headless/prosperoeden/ui/lang/en-US.po")
english_uk = read_po(root / "headless/prosperoeden/ui/lang/en-GB.po")
assert all(english_us.get(key) for key in marked), "en-US must contain every active source string"
uk_variants = {key: key.replace("Color", "Colour").replace("Customize", "Customise")
               for key in marked if "Color" in key or "Customize" in key}
assert len(uk_variants) >= 10, "Not enough live UK spelling cases"
assert all(english_uk.get(key) == value for key, value in uk_variants.items()), (
    "en-GB must use UK Colour/Customise spellings")
assert all(english_uk.get(key) == english_us.get(key) for key in marked if key not in uk_variants), (
    "en-GB must retain US translations for keys without regional spelling changes")
# Category strings arrive from external metadata at runtime; they are not
# automatically captured by tr("literal") extraction. Guard both French
# regional catalogs, including genres that previously fell back to English.
required_french_genres = {"Strategy", "Multiplayer", "Other", "Racing",
                          "Adventure", "Role-Playing", "Arcade", "Casual"}
assert required_french_genres <= module["DYNAMIC_LIBRARY_GENRES"]
for name in ("fr-FR.po", "fr-CA.po"):
    genre_translations = read_po(root / "headless/prosperoeden/ui/lang" / name)
    absent = {key for key in required_french_genres
              if not genre_translations.get(key) or genre_translations[key] == key
              and key in {"Strategy", "Multiplayer", "Other", "Role-Playing"}}
    assert not absent, f"{name}: untranslated game categories {sorted(absent)}"
# Resolution labels are dynamic constants, not tr("...") literals. Never
# permit them to disappear in non-primary languages after gettext extraction.
import re
settings = (root / "headless/settings_store.h").read_text()
m = re.search(r'kResolutionLabels\[\] = \{([^}]*)\}', settings, re.S)
assert m, "no resolution labels"
resolution_labels = re.findall(r'"([^"]+)"', m.group(1))
assert len(resolution_labels) == 9, resolution_labels
assert "2x (high memory)" in resolution_labels and "4x (extreme memory)" in resolution_labels
core_ui = {
    "Anti-aliasing", "ANTI-ALIASING", "Button mapping", "BUTTON MAPPING",
    "Quick settings", "QUICK SETTINGS", "Storage", "STORAGE",
    "Video preset", "VIDEO PRESET", "Game resolution", "GAME RESOLUTION",
    "TV output", "TV OUTPUT", "Sharpness", "SHARPNESS",
    "Stick deadzone", "STICK DEADZONE",
    "Vibration strength", "VIBRATION STRENGTH", "Play", "Cancel", "Confirm",
    "Reset", "Ultra", "Recommended", "Minimum", "Home", "Clear cache",
    "Done", "Custom", "Controllers", "Quit", "Preset", "Open settings",
}
assert core_ui <= marked, "essential UI source markers disappeared"
# AMD FSR remains a shipping spatial-upscale mode (filter ID 1), NOT
# a neural-rendering variant. Removing old "AMD FSR" / "FSR SHARPNESS"
# msgids from an inactive translation key set must NEVER remove the
# FSR 1 label, its EASU/RCAS help, or the shared sharpness control.
settings_filter = (root / "headless/settings_store.h").read_text()
assert re.search(r'kUpscalingFilterLabels\[\]\s*=\s*\{\s*"Bilinear",\s*"FSR 1",', settings_filter), (
    "AMD FSR 1 filter removed or persistent enum index changed")
presets = (root / "headless/prosperoeden/pe/ui/video_presets.hpp").read_text()
assert "return filter == 1 || filter == 5 || filter == 6;" in presets, (
    "FSR 1 sharpness support removed")
fsr_keys = {
    "FSR 1",
    "Sharpness",
    "SHARPNESS",
    "AMD FSR 1: EASU enlarges the picture; RCAS adds sharpness. Most useful below the TV output resolution.",
    "Bilinear is the lightest default. AMD FSR is most useful when rendering below the TV output size.",
    "Image sharpness affects FSR 1 and SGSR only. Start at 50% and reduce it if fine edges shimmer or show halos.",
}
assert fsr_keys <= marked, "Active AMD FSR 1 translation/help keys disappeared"
total_missing = 0
total_english_fallbacks = 0
for catalog in catalogs:
    translations = read_po(catalog)
    missing_fsr = sorted(k for k in fsr_keys if not translations.get(k))
    assert not missing_fsr, (f"{catalog.name}: active FSR 1 text missing "
                            f"after stale-key removal: {missing_fsr}")
    assert translations["FSR 1"] == "FSR 1", (
        f"{catalog.name}: AMD FSR 1 product name changed")
    stale = set(translations) - marked - module["DYNAMIC_LIBRARY_GENRES"]
    missing = {key for key in marked if not translations.get(key)}
    missing_resolutions = [label for label in resolution_labels if not translations.get(label)]
    assert not missing_resolutions, f"{catalog.name}: untranslated display scale options {missing_resolutions}"
    core_missing = sorted(k for k in core_ui if not translations.get(k))
    assert not core_missing, f"{catalog.name}: missing translated core UI labels {core_missing}"
    if stale:
        raise AssertionError(f"{catalog.name}: {len(stale)} stale msgid entries, examples={sorted(stale)[:5]}")
    assert not missing, f"{catalog.name}: {len(missing)} untranslated strings"
    total_missing += len(missing)
    english_fallbacks = sum(1 for key in marked if translations.get(key) == key)
    total_english_fallbacks += english_fallbacks
    print(f"LOCALE_COVERAGE {catalog.stem} active={len(marked)} "
          f"populated={len(marked)-len(missing)} english_fallbacks={english_fallbacks} missing={len(missing)} stale=0")
print(f"LOCALE_COVERAGE_SUMMARY languages={len(catalogs)} active_texts={len(marked)} "
      f"missing_entries={total_missing} english_fallbacks={total_english_fallbacks} (English fallback is NOT native translation; human review outstanding)")
