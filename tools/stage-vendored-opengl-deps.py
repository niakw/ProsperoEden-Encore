#!/usr/bin/env python3
"""Stage all mandatory PS5 OpenGL transitive dependencies from our own Git.

All Git original SHAs, PSBC source/compiler patch, Mesa 26.2 tar, and the
second native boilerplate are pinned. No upstream network access is required.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import deps


def sha(path):
 h=hashlib.sha256()
 with open(path,'rb') as stream:
  for part in iter(lambda:stream.read(1<<20),b''):h.update(part)
 return h.hexdigest()


def apply_pinned_psbc_patch(checkout: Path, patch_path: Path, expected_tree: str):
    """Reconcile only the exact audited PSBC patch; never reset a dirty cache."""
    git = ['git', '-C', str(checkout)]

    def output(*args, env=None):
        return subprocess.check_output([*git, *args], text=True, env=env).strip()

    index_tree = output('write-tree')
    original_tree = output('rev-parse', 'HEAD^{tree}')
    if index_tree != expected_tree:
        if index_tree != original_tree:
            raise RuntimeError('PSBC checkout index has unreviewed staged changes')
        dirty = subprocess.run([*git, 'diff', '--quiet', '--exit-code']).returncode
        if dirty == 0:
            # Ordinary empty-cache path: update the index and working tree
            # together, as required by the original pinned patch contract.
            subprocess.run(['git','-C',str(checkout),'apply','--index',str(patch_path)], check=True)
        elif dirty == 1:
            # A cached upstream checkout may already contain the exact patch
            # in its working tree while the index was restored to upstream.
            # git apply --index rejects that state with 49 "does not match
            # index" errors. First verify with a disposable alternate index,
            # leaving both source files and the real index untouched.
            with tempfile.TemporaryDirectory(prefix='encore-psbc-index-') as tmp:
                candidate_index = Path(tmp) / 'index'
                shutil.copyfile(checkout / '.git/index', candidate_index)
                candidate_env = os.environ.copy()
                candidate_env['GIT_INDEX_FILE'] = str(candidate_index)
                subprocess.run([*git, 'apply', '--cached', str(patch_path)],
                               check=True, env=candidate_env)
                if (output('write-tree', env=candidate_env) != expected_tree or
                    subprocess.run([*git, 'diff', '--quiet', '--exit-code'],
                                   env=candidate_env).returncode != 0):
                    raise RuntimeError('PSBC cached working tree differs from the audited patched tree')
            # Exact same source bytes and reviewed index: only publish the
            # matching staged index, without modifying the working tree.
            subprocess.run([*git, 'apply', '--cached', str(patch_path)], check=True)
            print('OPENGL_PSBC_PATCH_RECONCILED index-only cached tree', flush=True)
        else:
            raise RuntimeError('Cannot inspect cached PSBC working tree')
    if output('write-tree') != expected_tree:
        raise RuntimeError('PS5 OpenGL compiler patched tree mismatch')
    subprocess.run([*git, 'diff', '--exit-code', '--quiet'], check=True)


def stage(opengl_root:Path):
 opengl_root=opengl_root.resolve()
 declared=json.loads((opengl_root/'dependencies.json').read_text())
 original=json.loads((ROOT/'vendor/sources/opengl-source/dependencies.json').read_text())
 if declared!=original:raise RuntimeError('PS5 OpenGL upstream dependency pins diverged from our complete source mirror')
 workspace=opengl_root/'third_party';workspace.mkdir(parents=True,exist_ok=True)
 for name,pin in declared['repositories'].items():
  if pin.get('optional'):continue
  locked=next(x for x in deps.MANIFEST['items'] if x['name']=='opengl-'+name.lower().replace('_','-'))
  if locked['commit']!=pin['revision'] or locked['url']!=pin['url']:
   raise RuntimeError(f'PS5 OpenGL dep {name} version mismatch')
  deps.fetch_git(locked)
  recovered=deps.location(locked)
  checkout=workspace/name
  if not (checkout/'.git').exists():
   if checkout.exists():raise RuntimeError(f'Unrecognized third_party source {checkout}')
   shutil.copytree(recovered,checkout,symlinks=True)
  actual=subprocess.check_output(['git','-C',str(checkout),'rev-parse','HEAD'],text=True).strip()
  if actual!=locked['commit']:raise RuntimeError(f'PS5 OpenGL staged {name} SHA mismatch')
  if name=='opengnm-psbc':
   patch=declared['psbc_patch']
   patch_path=opengl_root/patch['path']
   if sha(patch_path)!=patch['sha256']:
    raise RuntimeError('PS5 OpenGL compiler patch checksum mismatch')
   apply_pinned_psbc_patch(checkout, patch_path, patch['patched_tree'])
   print('OPENGL_PSBC_PATCH_OFFLINE',patch['patched_tree'],flush=True)
  else:
   subprocess.run(['git','-C',str(checkout),'diff','--cached','--exit-code','--quiet'],check=True)
  print('OPENGL_GIT_DEP_OFFLINE',name,actual[:12],flush=True)

 # Restore and preserve the ORIGINAL Mesa release archive; the audited PS5
 # OpenGL fetcher verifies SHA and unpacks it itself, but never needs network.
 mesa=declared['mesa']
 locked=next(x for x in deps.MANIFEST['items'] if x['name']=='opengl-mesa-26-2')
 if locked['sha256']!=mesa['sha256'] or locked['url']!=mesa['url']:
  raise RuntimeError('PS5 OpenGL Mesa pin mismatch')
 deps.ensure_saved_archive(locked)
 target=workspace/f"mesa-{mesa['version']}.tar.xz"
 if not target.is_file():shutil.copy2(ROOT/locked['save'],target)
 if sha(target)!=mesa['sha256']:raise RuntimeError('Wrong vendored Mesa 26.2 archive')
 directory=workspace/f"mesa-{mesa['version']}"
 mesa_required=('VERSION','meson.build','src/mesa/main/context.c',
                'src/gallium/drivers/softpipe/sp_screen.c')
 mesa_complete=(directory.is_dir() and
                all((directory/name).is_file() for name in mesa_required) and
                (directory/'VERSION').read_text().strip()==mesa['version'])
 if not mesa_complete:
  if directory.exists():
   shutil.rmtree(directory)
  with tarfile.open(target) as stream:
   stream.extractall(workspace,filter='data')
 if not all((directory/name).is_file() for name in mesa_required):
  raise RuntimeError('Incomplete vendored Mesa source after extraction')
 if (directory/'VERSION').read_text().strip()!=mesa['version']:
  raise RuntimeError('Wrong vendored Mesa source version after extraction')
 print('OPENGL_MESA_ARCHIVE_OFFLINE',target.stat().st_size,'sources-ready',flush=True)

 boiler=declared['native_boilerplate']
 locked=next(x for x in deps.MANIFEST['items'] if x['name']=='opengl-native-boilerplate')
 if locked['commit']!=boiler['revision'] or locked['url']!=boiler['url']:
  raise RuntimeError('PS5 OpenGL native boilerplate mismatch')
 deps.fetch_git(locked)
 dest=opengl_root/'build/native-app-boilerplate'
 if not (dest/'.git').exists():
  if dest.exists():raise RuntimeError(f'Unrecognized native boilerplate folder {dest}')
  shutil.copytree(deps.location(locked),dest,symlinks=True)
 actual=subprocess.check_output(['git','-C',str(dest),'rev-parse','HEAD'],text=True).strip()
 if actual!=locked['commit']:raise RuntimeError('Wrong native boilerplate staged')
 # Upstream setup checks for the extracted bin/prospero-lld BEFORE it looks
 # for the ZIP. Extract the complete pinned SDK ourselves or it re-downloads.
 extras=next(x for x in deps.MANIFEST['items'] if x['name']=='boilerplate')['setup_prefetch']
 sdk_zip=deps.restore_chunked_object({'name':'boilerplate-setup-1'})
 zlib_tar=deps.restore_chunked_object({'name':'boilerplate-setup-0'})
 assert sdk_zip and zlib_tar
 if sha(sdk_zip)!=extras[1]['sha256'] or sha(zlib_tar)!=extras[0]['sha256']:
  raise RuntimeError('Mismatch in pinned OpenGL bootstrap prefetch')
 native=dest/'.deps/native';native.mkdir(parents=True,exist_ok=True)
 sdk=native/'ps5-payload-sdk'
 required_tools=('prospero-lld','prospero-clang','prospero-clang++')
 sdk_complete=all((sdk/'bin'/name).is_file() and os.access(sdk/'bin'/name,os.X_OK)
                  for name in required_tools)
 if not sdk_complete:
  if sdk.exists():
   shutil.rmtree(sdk)
  with zipfile.ZipFile(sdk_zip) as archive:
   for entry in archive.infolist():
    path=Path(entry.filename)
    if path.is_absolute() or '..' in path.parts:
     raise RuntimeError('Unsafe vendored PayloadSDK ZIP member')
   archive.extractall(native)
   for entry in archive.infolist():
    bits=(entry.external_attr>>16)&0o777
    if bits and not entry.is_dir():os.chmod(native/entry.filename,bits)
 archive=native/'zlib/zlib-1.3.2.tar.gz'
 archive.parent.mkdir(parents=True,exist_ok=True)
 if not archive.exists() or sha(archive)!=extras[0]['sha256']:
  shutil.copy2(zlib_tar,archive)
 if sha(archive)!=extras[0]['sha256']:
  raise RuntimeError('Wrong vendored zlib 1.3.2 after repair')
 for required_tool in required_tools:
  tool=sdk/'bin'/required_tool
  if not tool.is_file() or not os.access(tool, os.X_OK):
   raise RuntimeError(f'PS5 SDK tool missing after vendored extraction: {required_tool}')
 print('OPENGL_NATIVE_TEMPLATE_OFFLINE',actual[:12],'SDK compiler/linker and zlib verified',flush=True)

if __name__=='__main__':
 if len(sys.argv)!=2:raise SystemExit('usage: stage-vendored-opengl-deps.py PS5_OPENGL_SOURCE_ROOT')
 stage(Path(sys.argv[1]))
