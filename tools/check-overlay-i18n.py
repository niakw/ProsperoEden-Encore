#!/usr/bin/env python3
"""Qualify the in-game quick overlay against all 31 maintained UI catalogues.

Host/source gate only: this proves catalogue coverage and source routing, not
physical PS5 glyph rendering. Vulkan shaping/atlas validation is a separate gate.
"""
from pathlib import Path
import ast
import re

ROOT = Path(__file__).resolve().parents[1]
MENU = (ROOT / "headless/in_game_overlay_menu.h").read_text(encoding="utf-8")
SETTINGS = (ROOT / "headless/settings_store.h").read_text(encoding="utf-8")
VIDEO = (ROOT / "headless/prosperoeden/pe/ui/video_guidance.hpp").read_text(encoding="utf-8")
LANG_DIR = ROOT / "headless/prosperoeden/ui/lang"

def parse_po(path: Path) -> dict[str, str]:
    entries: dict[str, str] = {}
    key = ""
    value = ""
    part = None
    def finish():
        nonlocal key, value
        if key:
            entries[key] = value
        key = ""
        value = ""
    for raw in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("msgid "):
            finish()
            part = "id"
            key = ast.literal_eval(line[6:].strip())
        elif line.startswith("msgstr "):
            part = "str"
            value = ast.literal_eval(line[7:].strip())
        elif line.startswith('"'):
            text = ast.literal_eval(line)
            if part == "id":
                key += text
            elif part == "str":
                value += text
    finish()
    return entries

def cpp_array(name: str, source: str) -> list[str]:
    match = re.search(rf"\b{name}\s*\[\]\s*=\s*\{{(.*?)\}};", source, re.S)
    if not match:
        raise AssertionError(f"missing array {name}")
    return re.findall(r'"((?:\\.|[^"\\])*)"', match.group(1))

# Direct overlay vocabulary.
required = set(re.findall(r'Text\("((?:\\.|[^"\\])*)"\)', MENU))
required.update({"Automatic", "On", "Off", "Game default"})

# Dynamic labels used by translated value helpers.
required.update(cpp_array("kLanguageLabels", SETTINGS))
required.update(cpp_array("kUpscalingFilterLabels", SETTINGS))
required.update(cpp_array("kAntiAliasingLabels", SETTINGS))

neural = VIDEO.split("inline const char* NeuralModeName(int mode)", 1)[1].split(
    "inline const char* NeuralModeGuide", 1)[0]
required.update(re.findall(r'TR\("((?:\\.|[^"\\])*)"\)', neural))

catalogs = sorted(LANG_DIR.glob("*.po"))
assert len(catalogs) == 31, f"expected 31 catalogues, got {len(catalogs)}"

# The selected locale is visible on every overlay page, using the translated
# language name and the exact configured regional catalogue tag.
assert "std::string LanguageLine() const" in MENU
assert "pe::tr(kLanguageLabels[language])" in MENU
assert "kLanguageCatalogTags[language]" in MENU
assert "line(LanguageLine(), kRow);" in MENU

# No regression to the former French-only/English-only overlay copy.
for stale in (
    "REPRENDRE LE JEU", "AFFICHAGE FPS", "LOGS DETAILLES",
    "RETOUR BIBLIOTHEQUE", "GRAPHISMES", "COMMANDES", "MULTIJOUEUR",
    "MODIFS ENREGISTREES", "REGLAGES DE CE JEU", "RELANCER LE JEU REQUIS",
    "SAVE FAILED OR INCOMPAT", "CANNOT SAVE FPS SETTING",
    "CANNOT SAVE LOG SETTING", "FPS DISPLAY ENABLED", "DETAILED LOGS ENABLED",
    '"UPSCALE "', '"SQUARE"', '"TRIANGLE"', '"CREATE"', '"TOUCHPAD"',
):
    assert stale not in MENU, f"stale hard-coded overlay copy: {stale}"

# Human-facing core labels must have a real non-empty catalogue entry in all
# 31 files. English variants may equal their msgid; other locales are allowed
# to retain proper names/loanwords, but never an empty fallback.
missing: list[str] = []
for catalog in catalogs:
    entries = parse_po(catalog)
    for key in sorted(required):
        if not entries.get(key, "").strip():
            missing.append(f"{catalog.name}:{key}")
if missing:
    raise AssertionError("overlay catalogue gaps: " + "; ".join(missing[:40]))

# Configured language labels themselves are all translated catalogue keys.
language_labels = cpp_array("kLanguageLabels", SETTINGS)
tags = cpp_array("kLanguageCatalogTags", SETTINGS)
assert len(language_labels) == len(tags) == 31
for catalog in catalogs:
    entries = parse_po(catalog)
    for label in language_labels:
        assert entries.get(label, "").strip(), (catalog.name, label)

print(
    "OVERLAY_I18N_31_PASS",
    f"catalogues={len(catalogs)}",
    f"keys={len(required)}",
    "configured_language_visible=1",
    "hardcoded_fr_en_ui=0",
)
