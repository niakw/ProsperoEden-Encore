#!/usr/bin/env python3
"""Reconcile PS5 OpenGL's *inner* upstream pins against its fully vendored inputs.

No remote network and no PS5 compiler required. A full staging test is done
separately, because it copies and extracts hundreds of MiB of Mesa sources.
"""
from pathlib import Path
import ast
import json
import re
import runpy
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
DEPS=json.loads((ROOT/'tools/deps.json').read_text())['items']
LOCK={x['name']:x for x in DEPS}
VENDOR=ROOT/'vendor/sources'
SOURCE=VENDOR/'opengl-source'
pins=json.loads((SOURCE/'dependencies.json').read_text())
assert (SOURCE/'VENDOR-ORIGIN.json').is_file()
required=0
for name,record in pins['repositories'].items():
    if record.get('optional'):continue
    key='opengl-'+name.lower().replace('_','-')
    assert key in LOCK,key
    x=LOCK[key]
    assert x['kind']=='git' and x['commit']==record['revision'] and x['url']==record['url'],key
    origin=json.loads((VENDOR/key/'VENDOR-ORIGIN.json').read_text())
    assert origin['commit']==x['commit'] and origin['url']==x['url'],key
    assert (ROOT/'vendor/objects'/key/'chunks.json').is_file(),key
    required+=1
assert required==7
mesa=pins['mesa'];m=LOCK['opengl-mesa-26-2']
assert m['url']==mesa['url'] and m['sha256']==mesa['sha256']
assert (VENDOR/'opengl-mesa-26-2/VERSION').read_text().strip()==mesa['version']
assert (ROOT/'vendor/objects/opengl-mesa-26-2/chunks.json').is_file()
b=pins['native_boilerplate'];n=LOCK['opengl-native-boilerplate']
assert b['revision']==n['commit'] and b['url']==n['url']
assert json.loads((VENDOR/'opengl-native-boilerplate/VENDOR-ORIGIN.json').read_text())['commit']==n['commit']
assert b['payload_sdk_archive_sha256']==LOCK['boilerplate']['setup_prefetch'][1]['sha256']
original_fetch=(SOURCE/'tools/fetch-sources.py').read_text()
assert 'third_party' in original_fetch and 'fetch_repo(name, pin)' in original_fetch
builder=(ROOT/'tools/build-opengl-sdk.sh').read_text()
stager=(ROOT/'tools/stage-vendored-opengl-deps.py').read_text()
assert 'tools/stage-vendored-opengl-deps.py' in builder
assert 'python3 "$source_dir/tools/fetch-sources.py"\n' not in builder
assert 'python3 "$source_dir/tools/fetch-sources.py" --verify-psbc' in builder
for required in ("git','-C',str(checkout),'apply','--index'",
                 "patch['patched_tree']", "tarfile.open(target)",
                 "mesa_complete=", "shutil.rmtree(directory)",
                 "sdk_complete=", "shutil.rmtree(sdk)",
                 "Wrong vendored Mesa source version after extraction",
                 "Wrong vendored zlib 1.3.2 after repair"):
    assert required in stager, required
for forbidden in ('git clone --quiet', 'git -C "$template" fetch', 'setup-native-dependencies.sh'):
    assert forbidden not in builder, f"standard OpenGL builder retained network/bootstrap fallback: {forbidden}"
assert 'Vendored PS5 OpenGL boilerplate staging is missing' in builder
assert 'Vendored PS5 OpenGL PayloadSDK compiler missing after staging' in builder
# Native Mesa's C11 shim declares struct timespec unless the SDK already
# owns it. Both C and C++ compiler args must arrive as four separate Meson
# list entries, not one comma-joined unknown -Wno option. The frozen upstream
# shell expands meson_args unquoted, so a whitespace-free array is required.
mesa_opts=runpy.run_path(str(ROOT/'tools/ci/patch-ps5-opengl-mesa-options.py'))
expected_flags=[
    '-Wno-thread-safety-analysis',
    '-Wno-unreachable-code-generic-assoc',
    '-Wno-unused-parameter',
    '-DHAVE_STRUCT_TIMESPEC=1',
]
for language in ('C','CPP'):
    option=mesa_opts[f'{language}_ARGS_NEW'].strip()
    assert len(option.split())==1, ('Mesa shell would split compiler flags',option)
    assert option.startswith('-D'+('c' if language=='C' else 'cpp')+'_args=')
    assert ast.literal_eval(option.split('=',1)[1])==expected_flags
assert '#ifndef HAVE_STRUCT_TIMESPEC' in (
    VENDOR/'opengl-mesa-26-2/src/c11/time.h'
).read_text()
with tempfile.TemporaryDirectory(prefix='encore-mesa-opts-') as temporary:
    script=Path(temporary)/'build-mesa-ps5.sh'
    script.write_text((SOURCE/'toolchain/build-mesa-ps5.sh').read_text())
    mesa_opts['patch'](script)
    patched=script.read_text()
    for language in ('C','CPP'):
        assert patched.count(mesa_opts[f'{language}_ARGS_NEW'])==1
    assert '--wrap-mode=nodownload' in patched
    mesa_opts['patch'](script)
    assert script.read_text()==patched
print('PS5_OPENGL_MESA_TIMESPEC_ARGS_OK sdk_timespec=1 c_args=4 cpp_args=4 nodownload=1')

# Reproduce the previously failing cached checkout: original Git index, but
# the exact audited patch has already been applied to the working tree.
# Use only a disposable synthetic repository, never reset real build caches.
apply_pinned_patch = runpy.run_path(
    str(ROOT/'tools/stage-vendored-opengl-deps.py')
)['apply_pinned_psbc_patch']
def git_in(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args],
                                   text=True, stderr=subprocess.PIPE).strip()
with tempfile.TemporaryDirectory(prefix='encore-psbc-reconcile-') as temporary:
    tmp=Path(temporary)
    repo=tmp/'source'
    repo.mkdir()
    git_in(repo,'init','-q')
    git_in(repo,'config','user.name','Encore CI')
    git_in(repo,'config','user.email','ci@example.invalid')
    (repo/'shader.c').write_text('int main(void) { return 0; }\n')
    (repo/'build.txt').write_text('base\n')
    git_in(repo,'add','.')
    git_in(repo,'commit','-qm','Original pinned source')
    (repo/'shader.c').write_text('int main(void) { return 1; }\n')
    (repo/'build.txt').write_text('base\npatch\n')
    patch_path=tmp/'reviewed.patch'
    patch_path.write_text(git_in(repo,'diff','HEAD')+'\n')
    git_in(repo,'add','-u')
    expected_tree=git_in(repo,'write-tree')
    original_tree=git_in(repo,'rev-parse','HEAD^{tree}')
    assert expected_tree!=original_tree
    for case in ('clean', 'patched-worktree', 'unknown-worktree'):
        git_in(repo,'reset','--hard','HEAD')
        if case=='patched-worktree':
            git_in(repo,'apply',str(patch_path))
        elif case=='unknown-worktree':
            (repo/'shader.c').write_text('foreign guest edit\n')
        previous=(repo/'shader.c').read_bytes()
        if case=='unknown-worktree':
            try:
                apply_pinned_patch(repo,patch_path,expected_tree)
            except RuntimeError:
                pass
            else:
                raise AssertionError('PSBC reconciliation accepted unrelated worktree edits')
            assert (repo/'shader.c').read_bytes()==previous
            assert git_in(repo,'write-tree')==original_tree
        else:
            apply_pinned_patch(repo,patch_path,expected_tree)
            assert git_in(repo,'write-tree')==expected_tree
            assert subprocess.run(['git','-C',str(repo),'diff','--quiet']).returncode==0
            # The already patched index must be safely reusable.
            apply_pinned_patch(repo,patch_path,expected_tree)
print('PS5_OPENGL_PSBC_INDEX_RECONCILE_OK clean=1 cached_patched=1 unknown_rejected=1')

print('PS5_OPENGL_CLOSURE_OK 7 mandatory source repos + PSBC patch + Mesa 26.2 + native boilerplate staged offline')
print('PS5_OPENGL_CLOSURE_LIMITS optional CTS/sokol-samples not used by release; Mesa wraps and non-PS5 CPM pins separate')
