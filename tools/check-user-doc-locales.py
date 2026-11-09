#!/usr/bin/env python3
"""Check 29 fully documented locales plus 12 provisional app-only Indian locales."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
catalogs = sorted(p.stem for p in (ROOT/"headless/prosperoeden/ui/lang").glob("*.po"))
data = json.loads((ROOT/"docs/i18n/USER_DOC_TRANSLATIONS.json").read_text(encoding="utf-8"))
locales = {x["code"]:x for x in data["locales"]}
assert len(locales) == 29 and len(catalogs) == 41 and set(locales) <= set(catalogs)
short = {k:k.split("-")[0] for k in ("de-DE","it-IT","ja-JP","ko-KR","nl-NL","pl-PL","ru-RU","th-TH")}
read_short = {**short, "es-ES":"es", "fr-FR":"fr"}
index = (ROOT/"LANGUAGES.md").read_text(encoding="utf-8")
for code in catalogs:
    for prefix in ("README","INSTALL","SETTINGS","TROUBLESHOOTING","SUPPORT","ACCESSIBILITY"):
        filename = prefix+"."+(read_short.get(code,code) if prefix=="README" else short.get(code,code) if prefix=="INSTALL" else code)+".md"
        page = ROOT/"docs/i18n"/filename
        assert page.is_file(), f"Missing translated user page: {page}"
        content = page.read_text(encoding="utf-8")
        assert len(content)>300, f"Too little user text: {page}"
        assert filename in index, f"Missing link in language portal: {page}"
        if prefix in ("SETTINGS","TROUBLESHOOTING","SUPPORT","ACCESSIBILITY"):
            assert "LANGUAGES.md" in content
    assert all(locales[code].get(k) for k in ("intro","install","settings","trouble","support","access","safety","limits"))
assert "43 language/region selections" in index
assert "12 provisional Indian" in index
print(f"ENCORE_USER_DOC_29_LOCALES_PASS locales={len(catalogs)} guides={6*len(catalogs)} menu_choices=43")
