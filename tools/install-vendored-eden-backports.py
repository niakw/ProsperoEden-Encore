#!/usr/bin/env python3
"""Install ALL shipping Eden backports as actual, complete, versioned sources.

Usage:
 python3 tools/install-vendored-eden-backports.py --materialize PATCHED_SOURCE
 python3 tools/install-vendored-eden-backports.py --check [--replay]
 python3 tools/install-vendored-eden-backports.py INSTALL_SOURCE

The pinned original remains pristine; no git apply is used in production.
The separately unsafe dummy-thread workaround remains excluded by policy;
I-cache and service-manager fixes are installed by install-active-core-backports.py.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import re
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
ORIGINAL=ROOT/'vendor/sources/eden'
ACTIVE=ROOT/'vendor/encore-active/eden'
PIN='5f142c7926d0c7fcbbd0ce30794d72f638a43b2a'
EXPERIMENT=('EDEN_EXPERIMENTAL_DUMMY_THREAD_WAITS',)

def sha(content:bytes)->str:return hashlib.sha256(content).hexdigest()

def changed(patched:Path)->dict[str,dict]:
    results={}
    for f in sorted((patched/'src').rglob('*')):
        if not f.is_file():continue
        relative=str(f.relative_to(patched))
        before=ORIGINAL/relative
        prior=before.read_bytes() if before.is_file() else None
        new=f.read_bytes()
        if prior==new:continue
        results[relative]={'upstream':sha(prior) if prior is not None else None,
                           'active':sha(new),'bytes':len(new)}
    return results

PATCHES=ROOT/'headless/backports'
EXCLUDED_PATCHES={'eden-dummy-thread-waits.patch'}
APPLY_RE=re.compile(
    r'apply_one "\$root/headless/backports/([^"]+)" "\$eden/([^"]+)"')


def patch_paths(patch:Path)->set[str]:
    """Return logical Eden paths modified or added by one reviewed patch."""
    paths=set()
    for line in patch.read_text().splitlines():
        if not line.startswith('+++ b/'):
            continue
        relative=line[len('+++ b/'):]
        if relative and relative!='/dev/null':
            paths.add(relative)
    return paths


def shipping_spec()->dict:
    """Derive the scratch-overlay contract from current structure.

    Canonical ownership is the relative path under vendor/encore-active/eden.
    Hashes below protect one scratch-copy transaction; they never admit or
    reject a versioned owner and are not a vendor source allowlist.
    """
    calls=APPLY_RE.findall((ROOT/'tools/apply-eden-backports.sh').read_text())
    touched=set()
    receipts={}
    for patch_name,receipt_name in calls:
        if patch_name in EXCLUDED_PATCHES:
            continue
        patch=PATCHES/patch_name
        if not patch.is_file():
            raise RuntimeError(f'Missing shipping Eden patch: {patch_name}')
        touched.update(patch_paths(patch))
        receipts[receipt_name]=sha(patch.read_bytes())
    entries={}
    for relative in sorted(touched):
        active=ACTIVE/relative
        if not active.is_file():
            raise RuntimeError(
                f'Missing canonical Encore owner for backport path: {relative}')
        before=ORIGINAL/relative
        prior=before.read_bytes() if before.is_file() else None
        current=active.read_bytes()
        if prior==current:
            continue
        entries[relative]={
            'upstream':sha(prior) if prior is not None else None,
            'active':sha(current),
            'bytes':len(current),
        }
    if len(entries)<65:
        raise RuntimeError(
            f'Unexpectedly few canonical Eden backport owners: {len(entries)}')
    if len(receipts)<30:
        raise RuntimeError(
            f'Backport patch set unexpectedly incomplete: {len(receipts)}')
    return {
        'pinned_eden_commit':PIN,
        'source':'tools/apply-eden-backports.sh',
        'entries':entries,
        'shipping_receipts':dict(sorted(receipts.items())),
        'excluded_experimental':list(EXPERIMENT),
    }


def materialize(patched:Path)->None:
    raise RuntimeError(
        '--materialize is retired: maintain final owners directly under '
        'vendor/encore-active/eden; never regenerate the vendor override tree')


def lock()->dict:
    return shipping_spec()


def verify()->dict:
    meta=shipping_spec()
    for path,contract in meta['entries'].items():
        target=ACTIVE/path
        if sha(target.read_bytes())!=contract['active']:
            raise RuntimeError(
                f'Canonical Encore owner changed while verifying: {path}')
    print(
        f'EDEN_PATCHED_SOURCES_OK {len(meta["entries"])} canonical owners; '
        f'{len(meta["shipping_receipts"])} derived patch checksums')
    return meta


def is_owned_cached_source(destination:Path)->bool:
    """Only the disposable, owner-stamped Encore native source may be rebased."""
    if destination.is_symlink() or destination.name!='source':
        return False
    scratch=destination.parent
    if not scratch.name.startswith('ps5-eden-headless.') or scratch.is_symlink():
        return False
    owner=scratch/'owner'
    return owner.is_file() and not owner.is_symlink() and (
        owner.read_text().strip()==str(ROOT.resolve()))

def install(destination:Path, *, repair_owned_cache:bool=False)->None:
    spec=verify()
    if (destination/'GIT-COMMIT').read_text().strip()!=PIN:
        raise RuntimeError('Refusing to patch wrong Eden source version')
    if repair_owned_cache and not is_owned_cached_source(destination):
        raise RuntimeError('Cache repair limited to an owner-stamped native build source')
    # Validate ALL unexpected paths before modifying any target. A restored
    # source tree can contain an older generated texture/cache overlay, but
    # canonical vendor/sources and the shipping reviewed overlay stay immutable.
    stale=[]
    for rel,contract in spec['entries'].items():
        if Path(rel).is_absolute() or '..' in Path(rel).parts:
            raise RuntimeError(f'Unsafe vendored source path: {rel}')
        target=destination/rel
        if target.is_symlink() or not target.parent.resolve().is_relative_to(destination.resolve()):
            raise RuntimeError(f'Symlinked or escaping build source: {rel}')
        current=sha(target.read_bytes()) if target.is_file() else None
        if current in (contract['upstream'],contract['active']):
            continue
        if not repair_owned_cache:
            raise RuntimeError(f'Unknown previous source modifications at {rel}: {current}')
        if current is None:
            raise RuntimeError(f'Missing previously managed cached source: {rel}')
        stale.append((rel,current))
    if stale:
        # Preserve exact unknown cached bytes for diagnosis before overlaying.
        # Never repair arbitrary source trees or replace an immutable pin.
        backup_root=destination.parent/'.eden-stale-overlay-backup'
        if backup_root.is_symlink():
            raise RuntimeError('Stale overlay backup path is symlinked')
        for rel,digest in stale:
            target=destination/rel
            backup=backup_root/(rel+'.'+digest[:16])
            backup.parent.mkdir(parents=True,exist_ok=True)
            if backup.is_symlink():
                raise RuntimeError(f'Stale backup is symlinked: {rel}')
            if backup.exists():
                if sha(backup.read_bytes())!=digest:
                    raise RuntimeError(f'Stale backup hash mismatch: {rel}')
            else:
                staged=backup.with_name(backup.name+f'.new-{os.getpid()}')
                try:
                    shutil.copy2(target,staged)
                    if sha(staged.read_bytes())!=digest:
                        raise RuntimeError(f'Cached source changed during backup: {rel}')
                    staged.replace(backup)
                finally:staged.unlink(missing_ok=True)
            print(f'EDEN_STALE_SOURCE_PRESERVED path={rel} prior_sha256={digest}',flush=True)
    # Only the exact unknown hashes that were just preserved in our owned
    # scratch cache are authorized to be replaced. An unknown file in any
    # other destination still fails closed. Re-hash before each replacement
    # so a concurrent cache modification cannot slip in after the backup.
    saved_stale=dict(stale)
    changed_count=0
    for rel,contract in spec['entries'].items():
        target=destination/rel
        current=sha(target.read_bytes()) if target.is_file() else None
        if current==contract['active']:continue
        if current!=contract['upstream'] and (
            not repair_owned_cache or saved_stale.get(rel)!=current):
            raise RuntimeError(f'Unknown previous source modifications at {rel}: {current}')
        target.parent.mkdir(parents=True,exist_ok=True)
        temp=target.with_name(target.name+f'.active-{os.getpid()}')
        try:
            shutil.copy2(ACTIVE/rel,temp)
            temp.replace(target)
        finally:temp.unlink(missing_ok=True)
        changed_count+=1
    for receipt,digest in spec['shipping_receipts'].items():
        (destination/receipt).write_text(digest+'\n')
    print(f'EDEN_ACTIVE_SOURCE_INSTALLED total={len(spec["entries"])} changed={changed_count} stale_rebased={len(stale)} no_git_apply')

def replay()->None:
    """Replay shipping patches on frozen Eden and verify canonical ownership."""
    spec=verify()
    with tempfile.TemporaryDirectory(prefix='eden-backports-replay-') as tmp:
        stage=Path(tmp)/'source'
        shutil.copytree(ORIGINAL,stage,symlinks=True)
        (stage/'GIT-COMMIT').write_text(PIN+'\n')
        env=os.environ.copy()
        for key in EXPERIMENT:
            env[key]='OFF'
        result=subprocess.run(
            ['bash',str(ROOT/'tools/apply-eden-backports.sh'),str(stage)],
            cwd=ROOT,env=env,text=True,capture_output=True,timeout=240)
        if result.returncode:
            raise RuntimeError(
                f'Audited Eden patch replay failed: '
                f'{result.stderr[-1800:]} {result.stdout[-1800:]}')
        observed=changed(stage)
        expected=set(spec['entries'])
        actual=set(observed)
        missing=expected-actual
        extra=actual-expected
        # A historical shipping patch may have been superseded by a reviewed
        # canonical owner that deliberately restores the pinned upstream bytes
        # (for example the final PS5 Strict fence helper). Keep the old patch
        # replay immutable, but do not force its retired intermediate state
        # back into vendor/encore-active. Only an exact upstream restoration is
        # admitted as a canonical successor; every other extra owner fails.
        canonical_successors=[]
        unexpected_extra=[]
        for rel in sorted(extra):
            active=ACTIVE/rel
            original=ORIGINAL/rel
            if (active.is_file() and original.is_file() and
                    active.read_bytes()==original.read_bytes()):
                canonical_successors.append(rel)
            else:
                unexpected_extra.append(rel)
        if missing or unexpected_extra:
            raise RuntimeError(
                f'Patch replay owner set drift: '
                f'missing={sorted(missing)},extra={sorted(unexpected_extra)}')
        receipts={p.name:p.read_text().strip()
                  for p in stage.glob('.encore-backport-*.sha256')}
        if receipts!=spec['shipping_receipts']:
            raise RuntimeError('Missing or stale patch receipts')
        for rel in sorted(actual):
            if not (ACTIVE/rel).is_file():
                raise RuntimeError(f'Missing canonical owner after replay: {rel}')
        print(f'EDEN_COMPLETE_PATCH_REPLAY_OK files={len(actual)} '
              f'receipts={len(receipts)} canonical_successors={len(canonical_successors)}')

if __name__=='__main__':
    arg=argparse.ArgumentParser()
    arg.add_argument('--materialize',type=Path)
    arg.add_argument('--check',action='store_true')
    arg.add_argument('--replay',action='store_true')
    arg.add_argument('--repair-owned-cache',action='store_true',help='Preserve/rebase old overlays only inside owner-stamped native cache')
    arg.add_argument('destination',nargs='?',type=Path)
    args=arg.parse_args()
    if args.materialize:materialize(args.materialize)
    if args.check or args.replay:verify()
    if args.replay:replay()
    if args.destination:install(args.destination,repair_owned_cache=args.repair_owned_cache)
    if not(any((args.materialize,args.check,args.replay,args.destination))):arg.error('requires an action')
