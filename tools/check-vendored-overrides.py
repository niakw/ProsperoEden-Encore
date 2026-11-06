#!/usr/bin/env python3
"""Verify complete pinned Encore Overrides dataset, and active binary snapshots.

No remote access or running Git checkout is required. Unlike trusting the
compiled C++ profile header alone, assert none of the 8,993 game manifests
was dropped or mismatched when vendoring.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'vendor/sources/encore-overrides'
PIN = '95f21edf13bfbd2888602f2b419dd856d6d0fbfa'
TIERS = ('minimum','recommended','high','ultra')
META = json.loads((BASE/'VENDOR-ORIGIN.json').read_text())
assert META['commit']==PIN and META['name']=='encore-overrides'
assert META['url']=='https://github.com/niakw/encore-overrides.git'
assert META['tracked_files']==9496
LOCK = json.loads((ROOT/'tools/deps.json').read_text())
record = next(x for x in LOCK['items'] if x['name']=='encore-overrides')
assert record['commit']==PIN
manifest = json.loads((BASE/'manifest.json').read_text())
assert manifest['schema_version']==1 and manifest['database_revision']>=6
assert tuple(manifest['profile_order'])==TIERS
assert len(manifest['entries'])==9460
files = set((BASE/'games').glob('*.json'))
assert len(files)==len(manifest['entries'])
seen=set()
non_default=[]
native_ns2=0
general={tier:json.loads((BASE/'general'/f'{tier}.json').read_text())['settings'] for tier in TIERS}
general_ns2={tier:json.loads((BASE/'general/ns2'/f'{tier}.json').read_text())['settings'] for tier in TIERS}
sys.path.insert(0,str(ROOT/'tools'))
import importlib.util
spec=importlib.util.spec_from_file_location('encore_profile_gen',ROOT/'tools/sync-encore-overrides.py')
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
compiled_general=[module.profile(general[tier]) for tier in TIERS]
assert general['recommended']['upscaling_filter']=='fsr'
assert general['recommended']['texture_anisotropy']=='4x'
assert general_ns2['recommended']['upscaling_filter']=='fsr'
assert general_ns2['recommended']['texture_anisotropy']=='4x'
for entry in manifest['entries']:
    name=entry['title_id']
    assert re.fullmatch('[0-9A-F]{16}',name),name
    assert name not in seen,f'duplicate game {name}'
    seen.add(name)
    assert entry['path']==f'games/{name}.json'
    source=BASE/entry['path']
    assert source in files,source
    game=json.loads(source.read_text())
    assert game['schema_version']==1 and game['title_id']==name,(name,game.get('title_id'))
    assert game['auto_apply']==entry['auto_apply'] and game['default_profile']==entry['default_profile']
    for tier in TIERS:
        assert tier in game['profiles'] and 'settings' in game['profiles'][tier],(name,tier)
    values=[module.profile(game['profiles'][tier]['settings']) for tier in TIERS]
    if name.startswith('040'):
        native_ns2+=1
        assert game['source_console']=='Nintendo Switch 2',name
        assert game['status']=='auto-baseline',name
        assert all(game['profiles'][tier]['settings']['texture_anisotropy'] ==
                   general_ns2[tier]['texture_anisotropy'] for tier in TIERS),name
    else:
        assert name.startswith('010') and game['source_console']=='Nintendo Switch 1',name
        if game['status']=='auto-baseline':
            assert values==compiled_general,('NS1 generic profile drift',name)
    if game.get('source_console')!='Nintendo Switch 2' and values!=compiled_general:
        non_default.append(name)
assert native_ns2==467,native_ns2
assert len(seen)==9460,len(seen)
assert non_default==['0100C49025D3E000'],non_default
control=json.loads((BASE/'general/controls.json').read_text())
assert 'detection' in control
with tempfile.TemporaryDirectory(prefix='eden-overrides-sync-') as d:
    output=Path(d)/'generated.h'
    subprocess.run([sys.executable,'-B',str(ROOT/'tools/sync-encore-overrides.py'),
                    '--source',str(BASE),'--output',str(output)],
                   check=True,capture_output=True,text=True,timeout=100)
    embedded=(ROOT/'headless/encore_overrides_generated.h').read_bytes()
    assert output.read_bytes()==embedded,'compiled per-game profiles differ from the vendored canonical source'
    assert PIN.encode() in embedded
    assert b'0x0100C49025D3E000ULL' in embedded
    assert b'0x040074A01BF12000ULL' in embedded  # Donkey Kong Bananza native NS2
    assert b'0x0400C3F00006E000ULL' in embedded   # Mario Kart World native NS2
    assert b'std::array<TitleProfiles, 468>' in embedded
    assert b'kDatabaseRevision = 7;' in embedded
    subprocess.run([sys.executable,'-B',str(ROOT/'tools/sync-glyph-overrides.py'),
                    '--source',str(BASE),'--check'],check=True,
                    capture_output=True,text=True,timeout=30)
    assert json.loads((BASE/'glyphs/manifest.json').read_text())['schema_version']==2
    # No request for the currently nonexistent runtime-manifest.json may run
    # on the default launcher boot path, even if DNS/network is available.
    service=(ROOT/'headless/prosperoeden/eden_services.cpp').read_text()
    assert not (BASE/'runtime-manifest.json').exists()
    assert 'EDEN_OVERRIDES_REMOTE_REFRESH' in service
    assert 'if (remote_overrides != nullptr && std::strcmp(remote_overrides, "1") == 0)' in service
    assert service.count('StartEncoreOverridesRefresh();')==1
    print('ENCORE_OVERRIDES_OFFLINE_STARTUP_OK remote missing manifest is opt-in only')
    print('ENCORE_OVERRIDES_FULL_CATALOG_OK',len(files),'complete title records; NS2 profiles',native_ns2,'curated NS1 titles',len(non_default))
    print('ENCORE_OVERRIDES_ACTIVE_SNAPSHOT_OK exact SHA and C++ video, controls and glyphs')
