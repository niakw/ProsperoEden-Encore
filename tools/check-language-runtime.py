#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Release guard for PS5 locale -> launcher catalog selection and live language switching."""
from pathlib import Path
import re

root = Path(__file__).resolve().parents[1]
system = (root / 'third_party/ps5_system_language.hpp').read_text()
settings = (root / 'headless/settings_store.h').read_text()
frontend = (root / 'headless/prosperoeden/frontend.cpp').read_text()
browse = (root / 'headless/prosperoeden/pe/ui/browse.cpp').read_text()
services = (root / 'headless/prosperoeden/eden_services.cpp').read_text()
launcher = (root / 'headless/prosperoeden/pe/ui/launcher.hpp').read_text()
fake_services = (root / 'headless/prosperoeden/host/fake_services.cpp').read_text()
lang_dir = root / 'headless/prosperoeden/ui/lang'

quoted = lambda body: re.findall(r'"([^"\\]*(?:\\.[^"\\]*)*)"', body)

def array(name: str, text: str):
    match = re.search(rf'{re.escape(name)}[^=]*=\s*\{{(.*?)\}};', text, re.S)
    assert match, f'missing {name}'
    return quoted(match.group(1))

system_tags = array('kLanguageTags', system)
assert len(system_tags) == 31, len(system_tags)
assert system_tags[2] == 'fr-FR', f'PS5 French must map to fr-FR, got {system_tags[2]!r}'

keys = array('kLanguageKeys', settings)
catalogs = array('kLanguageCatalogTags', settings)
labels = array('kLanguageLabels', settings)

def numeric_array(name: str, text: str):
    match = re.search(rf'{re.escape(name)}[^=]*=\s*\{{(.*?)\}};', text, re.S)
    assert match, f'missing {name}'
    return [int(x) for x in re.findall(r'\b\d+\b', match.group(1))]

guest_languages = numeric_array('kLanguageSettings', settings)
regions = numeric_array('kLanguageRegions', settings)
preview_labels = array('kLanguageLabels', fake_services)
preview_regions = numeric_array('kLanguageRegions', fake_services)
assert len(keys) == len(catalogs) >= 18
assert keys[2] == 'fr' and catalogs[2] == 'fr-FR', (keys[2], catalogs[2])

po = sorted(lang_dir.glob('*.po'))
assert len(po) == 31, f'expected 31 official PS5 launcher catalogs, got {len(po)}'
assert len(keys) == len(catalogs) == len(system_tags) == 31, 'official PS5 language choice count changed'
assert len(labels) == len(guest_languages) == len(regions) == 31, 'PS5 language presentation and guest mappings differ'
assert preview_labels == labels, 'host preview must expose exactly the same 31 PS5 labels as the native launcher'
assert preview_regions == regions, 'host preview regions have drifted from the native launcher'
assert guest_languages[18:] == [1] * 13, 'PS5 UI-only locales must retain safe English guest fallback'
assert all(0 <= region <= 6 for region in regions), 'invalid guest region index'
assert set(catalogs) == set(system_tags), 'launcher choices must match the PS5 system language tags exactly'
assert set(catalogs) == {p.stem for p in po}, 'every PS5 selector must have its own PO catalog'
assert len(set(catalogs)) == len(catalogs), 'duplicate catalog selector'
assert keys[18:31] == catalogs[18:31], 'original thirteen hidden catalogs must be selectable'
fr = lang_dir / 'fr-FR.po'
assert fr.is_file() and fr.stat().st_size > 1000, 'complete fr-FR catalog missing'
core_strings = (root / 'headless/prosperoeden/pe/core/strings.cpp').read_text()
assert 'return {"en-US"};' in core_strings and 'return {"en-GB", "en-US"};' in core_strings, (
    'both regional English catalogs must be loaded')

# A release must never let an old dev override force English. The only language.txt read must live
# inside the EDEN_DEV_PROFILE block.
needle = 'Eden::AppFile(\"language.txt\")'
pos = frontend.find(needle)
assert pos >= 0, 'development language override missing'
ifdef = frontend.rfind('#ifdef EDEN_DEV_PROFILE', 0, pos)
endif = frontend.find('#endif', pos)
assert ifdef >= 0 and endif > pos, 'language.txt is not development-only'
assert 'pe::catalog().clear();' in frontend, 'catalog is not cleared before each launcher language load'
assert 'launcher.restart_requested()' in frontend, 'frontend does not honor launcher language restart'
assert 'EDEN_LANGUAGE launcher-restart=1' in frontend, 'language restart is not diagnosable'
assert 'Requested launcher catalog unavailable:' in frontend, 'missing catalog is not reported'
assert 'restart_requested_ = true;' in browse, 'Settings > Language does not request live launcher reload'
assert 'bool restart_requested() const' in launcher, 'launcher restart contract missing'
assert 'language < static_cast<int>(std::size(kLanguageRegions))' in fake_services, 'host preview still limits PS5 languages to 18'
assert 'static const std::vector<std::string> labels = Labels' not in services, 'translated labels survive a launcher restart'
assert 'return language_labels_;' in services and 'return resolution_labels_;' in services, 'translated labels are not per-service caches'

print('Language runtime contract PASS (PS5 French -> fr-FR, release override safe, live reload, 31 catalogs, 31 official PS5 selector choices)')

# The locale displayed by the launcher is not the encoded Horizon language.
assert 'locale == kLanguageKeys[i] || locale == kLanguageCatalogTags[i]' in settings
assert 'return SavedLanguageIndex(saved) >= 0;' in settings
assert 'document["system"]["language"] = kLanguageKeys[value.language];' in settings
main = (root / 'headless/main.cpp').read_text()
assert 'const int requested_language = Eden::kLanguageSettings[choice];' in main
assert 'EDEN_GUEST_LANGUAGE title=' in main
assert 'launcher_locale=%s saved_key=%s requested_code=%s configured_code=%s' in main
assert 'service_reply_observed=0' in main
assert guest_languages[2:4] == [2, 13] and regions[2:4] == [2, 1]
print('Locale/guest distinction PASS (fr-FR -> fr, fr-CA -> fr-CA)')
