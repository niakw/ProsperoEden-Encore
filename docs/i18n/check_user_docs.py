#!/usr/bin/env python3
"""Validate user guides for 29 non-English locales among 31 PS5 catalogs.

This is a documentation/path check, not a native compiler, linguistic
certification, hardware test, or replacement for P0-P4 exit proofs.
"""
from __future__ import annotations

import json
from pathlib import Path
import re
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[2]
I18N = ROOT / "docs" / "i18n"
CATALOGS = ROOT / "headless" / "prosperoeden" / "ui" / "lang"
TYPES = ("README", "INSTALL", "SETTINGS", "TROUBLESHOOTING", "SUPPORT", "ACCESSIBILITY")
README_ALIAS = dict.fromkeys(
    ("de-DE", "es-ES", "fr-FR", "it-IT", "ja-JP", "ko-KR",
     "nl-NL", "pl-PL", "ru-RU", "th-TH")
)
INSTALL_ALIAS = dict.fromkeys(
    ("de-DE", "it-IT", "ja-JP", "ko-KR", "nl-NL",
     "pl-PL", "ru-RU", "th-TH")
)
for aliases in (README_ALIAS, INSTALL_ALIAS):
    for key in aliases:
        aliases[key] = key.split("-", 1)[0]

errors: list[str] = []


def check(condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def filename(kind: str, code: str) -> str:
    alias = (README_ALIAS if kind == "README" else INSTALL_ALIAS
             if kind == "INSTALL" else {})
    return f"{kind}.{alias.get(code, code)}.md"


def local_links(page: Path, text: str) -> None:
    references = re.findall(r"\]\(([^)]+)\)", text)
    references += re.findall(r"""\bhref=["']([^"']+)["']""", text)
    references += re.findall(r"""\bsrc=["']([^"']+)["']""", text)
    for original in references:
        target = original.strip().strip("<>").split()[0]
        if target.startswith(("https://", "http://", "mailto:", "data:",
                              "#", "//")):
            continue
        target = unquote(target.split("#", 1)[0].split("?", 1)[0])
        if not target:
            continue
        expected = (page.parent / target).resolve()
        check(expected.is_relative_to(ROOT) and expected.exists(),
              f"{page.relative_to(ROOT)}: invalid local link {original}")


seed = json.loads((I18N / "USER_DOC_TRANSLATIONS.json").read_text(encoding="utf-8"))
locales = seed["locales"]
codes = {x["code"] for x in locales}
catalog_codes = {p.stem for p in CATALOGS.glob("*.po")}
check(len(locales) == len(codes) == 29, "expected 29 unique documentation locales")
check(codes == catalog_codes - {"en-US", "en-GB"} and len(catalog_codes) == 31,
      f"documentation vs PO locale difference: {sorted(codes ^ catalog_codes)}")

index = ROOT / "LANGUAGES.md"
index_text = index.read_text(encoding="utf-8")
local_links(index, index_text)
check("31 application translation catalogs" in index_text, "language index count missing")
check("31 official PS5 system language/region selections" in index_text, "launcher selection count missing")

for loc in locales:
    code, native = loc["code"], loc["native"]
    check("31" in loc["controls"] and "PS5" in loc["controls"],
          f"{code}: the localized controls guide must state the exact 31 official PS5 choices")
    for kind in TYPES:
        p = I18N / filename(kind, code)
        if not p.is_file():
            errors.append(f"missing {p.relative_to(ROOT)}")
            continue
        content = p.read_text(encoding="utf-8")
        check(len(content.strip()) >= 650, f"too short: {p.relative_to(ROOT)}")
        check(f"../../LANGUAGES.md" in content,
              f"missing language index link: {p.relative_to(ROOT)}")
        local_links(p, content)
        if kind in ("SETTINGS", "ACCESSIBILITY", "TROUBLESHOOTING", "SUPPORT"):
            check(native in content,
                  f"missing native locale title in {p.relative_to(ROOT)}")
            check(loc["safety"] in content,
                  f"missing translated backup/safety advice in {p.relative_to(ROOT)}")
            check(loc["limits"] in content,
                  f"missing dated release limitation in {p.relative_to(ROOT)}")
            for stale in (
                "Controller navigation: use on-screen focus",
                "Safe Launch resets problematic game-specific settings",
                "The following are **exact option names",
                "`Touchpad` (short press) opens the Encore",
            ):
                check(stale not in content,
                      f"untranslated English template in {p.relative_to(ROOT)}")
        if kind in ("SETTINGS", "ACCESSIBILITY"):
            check(loc["controls"] in content,
                  f"missing translated quick-overlay guidance in {p.relative_to(ROOT)}")
        if kind == "SETTINGS":
            check("FSR 1" in content and "Touchpad" in content,
                  f"missing video/controller coverage in {p.relative_to(ROOT)}")

for kind in TYPES:
    p = ROOT / f"{kind}.md"
    check(p.is_file(), f"missing English reference {kind}.md")

readme = (ROOT / "README.md").read_text(encoding="utf-8")
settings = (ROOT / "SETTINGS.md").read_text(encoding="utf-8")
check("LANGUAGES.md" in readme, "English README has no language directory")
check("Neural Rendering et composition d'image" not in settings,
      "English SETTINGS.md still contains untranslated French")
for old in ("/tree/feat/graphics-network-achievements",
            "/tree/research/ns2-ps5-compatibility"):
    check(old not in readme, f"English README links deleted branch {old}")

if errors:
    for msg in errors[:80]:
        print("USER_DOC_LOCALE_FAIL", msg)
    raise SystemExit(f"{len(errors)} user-doc localization/links violations")
print("ENCORE_USER_DOC_LOCALES_PASS",
      f"locales={len(codes)} manuals={len(codes)*len(TYPES)}",
      "references=6 coverage=verified link_scope=local no_ps5_build=1")
