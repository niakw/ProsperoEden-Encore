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
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
ORIGINAL=ROOT/'vendor/sources/eden'
ACTIVE=ROOT/'vendor/encore-active/eden-backports'
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

def materialize(patched:Path)->None:
    entries=changed(patched)
    if len(entries)<65:raise RuntimeError(f'Unexpectedly few shipping Eden backports: {len(entries)}')
    ACTIVE.mkdir(parents=True,exist_ok=True)
    for path in entries:
        destination=ACTIVE/path
        destination.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(patched/path,destination)
    receipts={p.name:p.read_text().strip() for p in patched.glob('.encore-backport-*.sha256')}
    if len(receipts)<30:raise RuntimeError(f'Backport receipts unexpectedly incomplete: {len(receipts)}')
    spec={'pinned_eden_commit':PIN,'source':'tools/apply-eden-backports.sh',
          'entries':entries,'shipping_receipts':dict(sorted(receipts.items())),
          'excluded_experimental':list(EXPERIMENT)}
    (ACTIVE/'manifest.json').write_text(json.dumps(spec,indent=2,sort_keys=True)+'\n')
    print(f'MATERIALIZED_EDEN_BACKPORTS files={len(entries)} verified_patch_receipts={len(receipts)}')

def lock()->dict:
    data=json.loads((ACTIVE/'manifest.json').read_text())
    if data['pinned_eden_commit']!=PIN:raise RuntimeError('Wrong pinned Eden revision')
    if set(data['excluded_experimental'])!=set(EXPERIMENT):raise RuntimeError('Shipping/experimental policy changed')
    return data

def verify()->dict:
    meta=lock()
    mismatches=[]
    for path,contract in meta['entries'].items():
        target=ACTIVE/path
        actual=sha(target.read_bytes()) if target.is_file() else None
        if actual!=contract['active']:
            mismatches.append(f'active {path}: expected={contract["active"]}, actual={actual}')
        old=ORIGINAL/path
        original=sha(old.read_bytes()) if old.is_file() else None
        if original!=contract['upstream']:
            mismatches.append(f'pinned {path}: expected={contract["upstream"]}, actual={original}')
    if mismatches:
        raise RuntimeError(
            'Vendored Eden source drift (all mismatches, no bypass): '
            f'{len(mismatches)}\n'+'\n'.join(mismatches))
    if len(meta['entries'])<65 or len(meta['shipping_receipts'])<30:
        raise RuntimeError('Missing shipping Eden patches')
    print(f'EDEN_PATCHED_SOURCES_OK {len(meta["entries"])} complete files; {len(meta["shipping_receipts"])} patch checksums')
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
    spec=verify()
    with tempfile.TemporaryDirectory(prefix='eden-backports-replay-') as tmp:
        stage=Path(tmp)/'source'
        shutil.copytree(ORIGINAL,stage,symlinks=True)
        (stage/'GIT-COMMIT').write_text(PIN+'\n')
        env=os.environ.copy()
        for key in EXPERIMENT:env[key]='OFF'
        result=subprocess.run(['bash',str(ROOT/'tools/apply-eden-backports.sh'),str(stage)],
                              cwd=ROOT,env=env,text=True,capture_output=True,timeout=240)
        if result.returncode:
            raise RuntimeError(f'Audited Eden patch replay failed: {result.stderr[-1400:]} {result.stdout[-1400:]}')
        observed=changed(stage)
        # FW23/HOS23 reviewed post-backport changes are separate from the
        # frozen source-patch replay. Prove each exact extra delta can be
        # reversed to the old generated source; never accept a new SHA only.
        successor=json.loads(
            (ROOT/'tools/fixtures/r23-fw23-backports-reverse.json').read_text())
        assert successor['schema_version']==1
        assert successor['baseline_vendor']=='87ef285eae969388a7c9ad98467ff7fd6c314cba'
        assert successor['active_vendor']=='b977c24a00d85b8279f1a78b173e5995cd82353e'
        reviewed=successor['reviewed_fw23_sources']
        assert len(reviewed)==4 and len({entry['path'] for entry in reviewed})==4
        for entry in reviewed:
            rel=entry['path']
            assert rel in observed and rel in spec['entries'], (
                'Unexpected replay successor',rel)
            generated=(stage/rel).read_bytes()
            current=(ACTIVE/rel).read_bytes()
            assert len(generated)==entry['before_bytes'] and sha(generated)==entry['before_sha256'], (
                'Historical FW23 patch replay drift',rel)
            assert len(current)==entry['after_bytes'] and sha(current)==entry['after_sha256'], (
                'Unreviewed integrated FW23 source',rel)
            assert spec['entries'][rel]['active']==entry['after_sha256']
            prior=current.decode('utf-8')
            for hunk in reversed(entry['hunks']):
                assert prior.count(hunk['after'])==1, (
                    'FW23/R23 exact reverse span moved',rel)
                prior=prior.replace(hunk['after'],hunk['before'],1)
            assert prior.encode('utf-8')==generated, (
                'FW23 source not derivable from frozen patch replay',rel)
            observed[rel]=spec['entries'][rel]
        print('FW23_R23_EXACT_POST_BACKPORT_REPLAY_PASS',
              f'successors={len(reviewed)}', 'historical_receipts=untouched')
        # GetInfo 29/30/33 was reviewed later as a bounded NS2 successor to
        # the same frozen Eden patch replay. Keep that provenance separate
        # from FW23 and prove the exact maintained files reverse byte-for-byte
        # to the generated pre-GetInfo sources.
        getinfo=json.loads(
            (ROOT/'tools/fixtures/ns2-getinfo-backports-reverse.json').read_text())
        assert getinfo['schema_version']==1
        assert getinfo['baseline_vendor']=='c5614d3c7ef75958965bac93c9e343eccdbc0fbe'
        assert getinfo['page_size_vendor']=='f6ace750bf7a1b37101b420203a7f9633888d4f2'
        assert getinfo['vamm_region_vendor']=='035c0333a05954beaa8810c6e28c1377cf500eec'
        assert getinfo['manifest_receipt_vendor']=='67926ea4b6960eefebf0427929cf299e8e056013'
        assert getinfo['active_vendor'] in {'ffa519db0f68fb0d5d2acf791e381c898a34a175','9e38066a508716fd959477eccf32c7fb2fde3356','e298a9b05732346141b685eb4c9850bfa02d9e58','f7ccfda091fd7429f44159318a07391881a3e7c0','92c480e17fedecc21ab4882b76e8507b5aed3771','7039d7752c5d8b1a53db50be0d8f2f7803867e13','d3fca0aa188052f0efd2bad102950aeaeeb36ab0','dfc39fcc087738955b0373b45fa97facdeb2fc47'}

        # Review each NS2 successor byte-for-byte against the previously
        # qualified maintainer overlay before applying the historical reverse.
        ns2_successor=json.loads(
            (ROOT/'tools/fixtures/ns2-memory-service-backports-reverse.json').read_text())
        assert ns2_successor['schema_version']==1
        reviewed_ns2=ns2_successor['reviewed_sources']
        assert set(reviewed_ns2)=={
            'src/core/device_memory_manager.h',
            'src/core/hle/kernel/svc/svc_info.cpp',
            'src/core/hle/kernel/svc_types.h',
        }
        def reverse_ns2_successor(rel, content):
            record=reviewed_ns2[rel]
            assert len(content)==record['after_bytes'] and sha(content)==record['after_sha256'], rel
            value=content.decode('utf-8')
            for hunk in reversed(record['hunks']):
                assert value.count(hunk['after'])==1, rel
                value=value.replace(hunk['after'],hunk['before'],1)
            prior=value.encode('utf-8')
            assert len(prior)==record['before_bytes'] and sha(prior)==record['before_sha256'], rel
            assert spec['entries'][rel]['active']==record['after_sha256'], rel
            assert spec['entries'][rel]['bytes']==record['after_bytes'], rel
            return prior

        getinfo_sources=getinfo['reviewed_getinfo_sources']
        assert len(getinfo_sources)==2 and len({entry['path'] for entry in getinfo_sources})==2
        for entry in getinfo_sources:
            rel=entry['path']
            assert rel in observed and rel in spec['entries'], (
                'Unexpected GetInfo replay successor',rel)
            generated=(stage/rel).read_bytes()
            # svc_info.cpp/svc_types.h have a later reviewed NS2 successor.
            # Reverse only that successor first, then prove the historical
            # GetInfo 29/30/33 delta against the frozen backport replay.
            current=reverse_ns2_successor(rel,(ACTIVE/rel).read_bytes())
            assert len(generated)==entry['before_bytes'] and sha(generated)==entry['before_sha256'], (
                'Historical GetInfo patch replay drift',rel)
            assert len(current)==entry['after_bytes'] and sha(current)==entry['after_sha256'], (
                'Unreviewed integrated GetInfo source',rel)
            assert spec['entries'][rel]['active']==reviewed_ns2[rel]['after_sha256']
            prior=current.decode('utf-8')
            for hunk in reversed(entry['hunks']):
                assert prior.count(hunk['after'])==1, (
                    'GetInfo exact reverse span moved',rel)
                prior=prior.replace(hunk['after'],hunk['before'],1)
            assert prior.encode('utf-8')==generated, (
                'GetInfo source not derivable from frozen patch replay',rel)
            observed[rel]=spec['entries'][rel]
        device_rel='src/core/device_memory_manager.h'
        device_previous=reverse_ns2_successor(device_rel,(ACTIVE/device_rel).read_bytes())
        assert device_previous==(stage/device_rel).read_bytes(), 'NS2 SMMU precursor replay drift'
        observed[device_rel]=spec['entries'][device_rel]
        assert 'Nx2RemoteMemorySize = 31' in (ACTIVE/'src/core/hle/kernel/svc_types.h').read_text()
        assert 'Nx2RemoteMemoryUsed = 32' in (ACTIVE/'src/core/hle/kernel/svc_types.h').read_text()
        print('NS2_GETINFO_EXACT_POST_BACKPORT_REPLAY_PASS',
              f'successors={len(getinfo_sources)}',
              'info_types=29,30,31,32,33', 'remote_memory_31_32=zero_without_pool',
              'historical_receipts=untouched')

        # Vendor #178 moves the reviewed HTTPS-only JSON POST primitive into
        # the shipping maintained Eden backport while restoring pinned Eden
        # sources byte-for-byte. Prove the exact two-file successor can be
        # reversed to this frozen patch replay; never whitelist arbitrary
        # network-source drift.
        diagnostics_cpp='src/common/net/net.cpp'
        diagnostics_h='src/common/net/net.h'
        if diagnostics_h in spec['entries']:
            assert spec['entries'][diagnostics_cpp]['active']=='9d3d56b9fa6b4a47097aa32c18b42e8839c547915d3af19aa37830dd75ac5da8'
            assert spec['entries'][diagnostics_h]['active']=='3ce233a0020b17b680f733a2ec41cdb8fd5100bd27cec8550ec3ca7202109f27'
            generated_cpp=(stage/diagnostics_cpp).read_bytes()
            current_cpp=(ACTIVE/diagnostics_cpp).read_bytes()
            assert sha(generated_cpp)=='b359ea24cf97759de4e5599334a266190ae19ad480639c2400bdfc72d54bebc2'
            assert len(generated_cpp)==9974
            assert sha(current_cpp)==spec['entries'][diagnostics_cpp]['active']
            post_json=b'''std::optional<HttpResponse> PostJson(const std::string& url, const std::string& path,
                                     const std::string& body,
                                     std::size_t timeout_seconds) {
    try {
        constexpr std::size_t max_timeout_seconds = 15;
        constexpr std::size_t max_request_bytes = 64 * 1024;
        constexpr std::size_t max_response_bytes = 64 * 1024;
        if (!url.starts_with("https://") || path.empty() || path.front() != '/' ||
            path.find_first_of("\\r\\n") != std::string::npos ||
            body.empty() || body.size() > max_request_bytes ||
            timeout_seconds == 0 || timeout_seconds > max_timeout_seconds) {
            LOG_ERROR(Common, "Refusing invalid HTTPS JSON POST target or bounds");
            return std::nullopt;
        }

        std::unique_ptr<httplib::Client> client = std::make_unique<httplib::Client>(url);
        client->set_connection_timeout(timeout_seconds);
        client->set_read_timeout(timeout_seconds);
        client->set_write_timeout(timeout_seconds);
#ifdef YUZU_BUNDLED_OPENSSL
        client->load_ca_cert_store(kCert, sizeof(kCert));
#endif
        client->set_follow_location(false);
        httplib::Result result = client->Post(path, body, "application/json");
        if (!result) {
            LOG_ERROR(Common, "POST to {}{} returned null", url, path);
            return std::nullopt;
        }
        const auto& response = result.value();
        if (response.body.size() > max_response_bytes) {
            LOG_ERROR(Common, "POST to {}{} returned oversized response", url, path);
            return std::nullopt;
        }
        return HttpResponse{.status = response.status, .body = response.body};
    } catch (const std::exception& e) {
        LOG_ERROR(Common, "POST to {}{} failed: {}", url, path, e.what());
        return std::nullopt;
    }
}

'''
            assert current_cpp.count(post_json)==1
            assert current_cpp.replace(post_json,b'',1)==generated_cpp
            generated_h=(ORIGINAL/diagnostics_h).read_bytes()
            current_h=(ACTIVE/diagnostics_h).read_bytes()
            assert sha(generated_h)==spec['entries'][diagnostics_h]['upstream']
            assert sha(current_h)==spec['entries'][diagnostics_h]['active']
            active_header=current_h.decode('utf-8')
            assert active_header.count('#include <cstddef>\n')==1
            http_decl='''struct HttpResponse {
    int status{};
    std::string body;
};

// Small HTTPS-only JSON POST primitive for opt-in launcher services.
// It never follows redirects and reports HTTP status to the caller so policy
// can distinguish retryable transport failures from server rejection.
std::optional<HttpResponse> PostJson(const std::string& url, const std::string& path,
                                     const std::string& body,
                                     std::size_t timeout_seconds = 5);

'''
            assert active_header.count(http_decl)==1
            reversed_h=active_header.replace('#include <cstddef>\n','',1).replace(http_decl,'',1)
            assert reversed_h.encode('utf-8')==generated_h
            observed[diagnostics_cpp]=spec['entries'][diagnostics_cpp]
            observed[diagnostics_h]=spec['entries'][diagnostics_h]
            print('DIAGNOSTICS_NET_EXACT_POST_BACKPORT_REPLAY_PASS',
                  'successors=2', 'https_post=bounded', 'pinned_sources=immutable')
        # NS1 Nintendo-online successors are maintained as exact overlays rather than
        # mutating the pinned Eden tree. Reverse the reviewed dispatcher-only delta
        # byte-for-byte before admitting these files into the replay result.
        online=json.loads(
            (ROOT/'tools/fixtures/ns1-online-service-backports-reverse.json').read_text())
        assert online['schema_version']==1
        assert online['baseline_vendor']=='a64bcf8c38473234474aca49b4013ed3617e0dec'
        assert online['active_vendor']=='dc460d59824f532705781f8df8e72d951ebbd446'
        online_handler='''
    // Encore NS1: unavailable Nintendo online backend; explicit error, never fake success.
    void RejectUnavailableNintendoOnline(HLERequestContext& ctx) {
        IPC::ResponseBuilder rb{ctx, 2};
        rb.Push(ResultUnknown);
    }

'''
        ipc_include='#include "core/hle/service/ipc_helpers.h"\n'
        online_count=0
        for rel,entry in online['reviewed_sources'].items():
            assert rel not in observed, ('Nintendo-online source unexpectedly changed by frozen replay',rel)
            assert rel in spec['entries'], ('Missing Nintendo-online shipping overlay',rel)
            generated=(stage/rel).read_bytes()
            current=(ACTIVE/rel).read_bytes()
            assert len(generated)==entry['before_bytes'] and sha(generated)==entry['before_sha256'], (
                'Nintendo-online frozen source drift',rel)
            assert spec['entries'][rel]['upstream']==entry['before_sha256'], rel
            assert len(current)==entry['after_bytes'] and sha(current)==entry['after_sha256'], (
                'Unreviewed Nintendo-online maintained source',rel)
            assert spec['entries'][rel]['active']==entry['after_sha256'], rel
            assert spec['entries'][rel]['bytes']==entry['after_bytes'], rel
            value=current.decode('utf-8')
            for class_name,count in entry['classes'].items():
                token=f'&{class_name}::RejectUnavailableNintendoOnline'
                assert value.count(token)==count, ('Nintendo-online handler count drift',rel,class_name)
                value=value.replace(token,'nullptr')
                online_count+=count
            assert value.count(online_handler)==len(entry['classes']), (
                'Nintendo-online rejection method drift',rel)
            value=value.replace(online_handler,'',len(entry['classes']))
            if entry['added_ipc_helpers_include']:
                assert value.count(ipc_include)==1, ('Nintendo-online IPC include drift',rel)
                value=value.replace(ipc_include,'',1)
            assert value.encode('utf-8')==generated, (
                'Nintendo-online source not exactly reversible to pinned Eden',rel)
            observed[rel]=spec['entries'][rel]
        assert online_count==412
        print('NS1_ONLINE_SERVICE_EXACT_POST_BACKPORT_REPLAY_PASS',
              f'successors={len(online["reviewed_sources"])}',
              f'rejected_slots={online_count}', 'pinned_sources=immutable')

        # NS1 factory-settings is a reviewed post-backport overlay. Keep the pinned
        # Eden sources byte-identical, then admit only these exact maintained
        # before/after blobs into the shipping replay.
        factory_overlays={
            'src/core/hle/service/set/factory_settings_server.cpp': {
                'before_sha256':'e398e12a102f44ccc43ed7d652fffafaa7ad4af253a0f40f939fb39860670c18',
                'before_bytes':2667,
                'after_sha256':'1648b43aaa98758007d0a6edd40f80f2ef04da278085bfaf1179bfe86273159a',
                'after_bytes':11169,
            },
            'src/core/hle/service/set/factory_settings_server.h': {
                'before_sha256':'375b4c15ffe68979af8e184651f3c92889129d5f8a25d2bf668352935e1d20c8',
                'before_bytes':450,
                'after_sha256':'019972d8200732ed18e277e83467f53cebe5e921fcb4a07d07612f069bb8961c',
                'after_bytes':2225,
            },
        }
        for rel,entry in factory_overlays.items():
            assert rel not in observed, ('SET:CAL unexpectedly changed by frozen replay',rel)
            assert rel in spec['entries'], ('Missing SET:CAL shipping overlay',rel)
            generated=(stage/rel).read_bytes()
            current=(ACTIVE/rel).read_bytes()
            assert len(generated)==entry['before_bytes'] and sha(generated)==entry['before_sha256'], (
                'SET:CAL pinned source drift',rel)
            assert spec['entries'][rel]['upstream']==entry['before_sha256'], rel
            assert len(current)==entry['after_bytes'] and sha(current)==entry['after_sha256'], (
                'Unreviewed SET:CAL maintained source',rel)
            assert spec['entries'][rel]['active']==entry['after_sha256'], rel
            assert spec['entries'][rel]['bytes']==entry['after_bytes'], rel
            observed[rel]=spec['entries'][rel]
        factory_cpp=(ACTIVE/'src/core/hle/service/set/factory_settings_server.cpp').read_text()
        assert factory_cpp.count('&IFactorySettingsServer::RejectUnsupportedFactoryCommand')==20
        assert factory_cpp.count('void IFactorySettingsServer::RejectUnsupportedFactoryCommand(')==1
        assert factory_cpp.count('#include "core/hle/service/ipc_helpers.h"')==1
        print('NS1_FACTORY_SETTINGS_EXACT_POST_BACKPORT_REPLAY_PASS',
              'successors=2', 'rejected_slots=20', 'pinned_sources=immutable')

        # set:fd is development-mode-only on Horizon; Encore shipping has no
        # firmware-debug settings backend. Admit only these exact maintained
        # fail-closed owners while preserving the pinned Eden source bytes.
        firmware_debug_overlays={
            'src/core/hle/service/set/firmware_debug_settings_server.cpp': {
                'before_sha256':'ec943c54def8e62c30e89e0035ad95e94979d9982182ada6c49db3cf9646b02b',
                'before_bytes':1197,
                'after_sha256':'54a8e47b2b6df8ee4a1872ee0ecbac35bea95d7ab97a43a9cbb0bcd4f560f1be',
                'after_bytes':2010,
            },
            'src/core/hle/service/set/firmware_debug_settings_server.h': {
                'before_sha256':'48a11c6e2147f97b1d7b7803af4b20862554ecb45312fb641de7f0738bdee1f2',
                'before_bytes':474,
                'after_sha256':'8149664a2a199dbb1710af15db64c93b6f8fa312ce38f1633c7539ff26b2e70a',
                'after_bytes':548,
            },
        }
        for rel,entry in firmware_debug_overlays.items():
            assert rel not in observed, ('SET:FD unexpectedly changed by frozen replay',rel)
            assert rel in spec['entries'], ('Missing SET:FD shipping overlay',rel)
            generated=(stage/rel).read_bytes()
            current=(ACTIVE/rel).read_bytes()
            assert len(generated)==entry['before_bytes'] and sha(generated)==entry['before_sha256'], (
                'SET:FD pinned source drift',rel)
            assert spec['entries'][rel]['upstream']==entry['before_sha256'], rel
            assert len(current)==entry['after_bytes'] and sha(current)==entry['after_sha256'], (
                'Unreviewed SET:FD maintained source',rel)
            assert spec['entries'][rel]['active']==entry['after_sha256'], rel
            assert spec['entries'][rel]['bytes']==entry['after_bytes'], rel
            observed[rel]=spec['entries'][rel]
        firmware_debug_cpp=(ACTIVE/'src/core/hle/service/set/firmware_debug_settings_server.cpp').read_text()
        assert firmware_debug_cpp.count('&IFirmwareDebugSettingsServer::RejectUnavailableDebugSetting')==11
        assert firmware_debug_cpp.count('void IFirmwareDebugSettingsServer::RejectUnavailableDebugSetting(')==1
        print('NS1_FIRMWARE_DEBUG_SETTINGS_EXACT_POST_BACKPORT_REPLAY_PASS',
              'successors=2', 'rejected_slots=11', 'pinned_sources=immutable')

        # BGTC awake-state helpers were previously maintained only in vendor/sources
        # and therefore were not guaranteed to reach the native pinned Eden cache.
        # Admit the complete reviewed shipping owner, including fail-closed task/sleep
        # commands, while keeping the pinned source tree byte-identical.
        bgtc_overlays={
            'src/core/hle/service/glue/bgtc.cpp': {
                'before_sha256':'e5b42f6f166c4f2d1a434295e3bec3131eb86e09883cffd185e3eb6dde0f5f2a',
                'before_bytes':2408,
                'after_sha256':'d772b524d0aee373f73bc0b9ff9851619b09084d2dce9ea24b2c72e10fe0c428',
                'after_bytes':4170,
            },
            'src/core/hle/service/glue/bgtc.h': {
                'before_sha256':'0f2da586f3d413f15c64bc830f27aec6fd775037466c5ef6835f8117fce8a9e1',
                'before_bytes':737,
                'after_sha256':'0c2fd912305a94f5ec5091a223f1f40ce2e0e3dff20999c20f95f3ea71df076e',
                'after_bytes':1177,
            },
        }
        for rel,entry in bgtc_overlays.items():
            assert rel not in observed, ('BGTC unexpectedly changed by frozen replay',rel)
            assert rel in spec['entries'], ('Missing BGTC shipping overlay',rel)
            generated=(stage/rel).read_bytes()
            current=(ACTIVE/rel).read_bytes()
            assert len(generated)==entry['before_bytes'] and sha(generated)==entry['before_sha256'], (
                'BGTC pinned source drift',rel)
            assert spec['entries'][rel]['upstream']==entry['before_sha256'], rel
            assert len(current)==entry['after_bytes'] and sha(current)==entry['after_sha256'], (
                'Unreviewed BGTC maintained source',rel)
            assert spec['entries'][rel]['active']==entry['after_sha256'], rel
            assert spec['entries'][rel]['bytes']==entry['after_bytes'], rel
            observed[rel]=spec['entries'][rel]
        bgtc_cpp=(ACTIVE/'src/core/hle/service/glue/bgtc.cpp').read_text()
        assert bgtc_cpp.count('&ITaskService::RejectUnavailableBackgroundTask')==12
        assert bgtc_cpp.count('&BGTC_SC::RejectUnavailableStateControl')==5
        for implemented in (
            'D<&ITaskService::IsInHalfAwake>',
            'D<&ITaskService::IsInFullAwake>',
            'D<&ITaskService::WillDisconnectNetworkWhenEnteringSleep>',
            'D<&ITaskService::WillStayHalfAwakeInsteadSleep>',
        ):
            assert bgtc_cpp.count(implemented)==1, implemented
        print('NS1_BGTC_EXACT_POST_BACKPORT_REPLAY_PASS',
              'successors=2', 'rejected_slots=17', 'awake_handlers=4',
              'pinned_sources=immutable')

        # BCAT keeps explicit foreground/local cache synchronization but Encore has
        # no Horizon delivery-task scheduler, push log or storage-update notifier.
        # The reviewed owner also makes the previously source-only system-task NOOP
        # actually reach the native pinned Eden build.
        bcat_overlays={
            'src/core/hle/service/bcat/bcat_service.cpp': {
                'before_sha256':'d34a5f0e6cce26635b719dd1f31c295a7db7d8865c29fc9ab83f5c9c764b2a22',
                'before_bytes':5959,
                'after_sha256':'f48b5d2a2bd7aa9813bac1fce9302956674d1bf7db941442df75e26a989be495',
                'after_bytes':7171,
            },
            'src/core/hle/service/bcat/bcat_service.h': {
                'before_sha256':'e5689ca4661a9b49baee97fbc86f2a0b42eb39db577ed27238cf2bb545378b92',
                'before_bytes':1542,
                'after_sha256':'8f0c4487f49850a940ea3bf8c81a51c643daae391d8294498c8dbc70990a3864',
                'after_bytes':1606,
            },
        }
        for rel,entry in bcat_overlays.items():
            assert rel not in observed, ('BCAT unexpectedly changed by frozen replay',rel)
            assert rel in spec['entries'], ('Missing BCAT shipping overlay',rel)
            generated=(stage/rel).read_bytes()
            current=(ACTIVE/rel).read_bytes()
            assert len(generated)==entry['before_bytes'] and sha(generated)==entry['before_sha256'], (
                'BCAT pinned source drift',rel)
            assert spec['entries'][rel]['upstream']==entry['before_sha256'], rel
            assert len(current)==entry['after_bytes'] and sha(current)==entry['after_sha256'], (
                'Unreviewed BCAT maintained source',rel)
            assert spec['entries'][rel]['active']==entry['after_sha256'], rel
            assert spec['entries'][rel]['bytes']==entry['after_bytes'], rel
            observed[rel]=spec['entries'][rel]
        bcat_cpp=(ACTIVE/'src/core/hle/service/bcat/bcat_service.cpp').read_text()
        assert bcat_cpp.count('&IBcatService::RejectUnavailableDeliveryTask')==21
        assert bcat_cpp.count('{20100, nullptr, "RequestSyncDeliveryCacheWithApplicationId"}')==0
        assert bcat_cpp.count('{20101, nullptr, "RequestSyncDeliveryCacheWithApplicationIdAndDirectoryName"}')==0
        assert bcat_cpp.count('D<&IBcatService::RequestSyncDeliveryCache>')==1
        assert bcat_cpp.count('D<&IBcatService::RequestSyncDeliveryCacheWithDirectoryName>')==1
        assert bcat_cpp.count('D<&IBcatService::RegisterSystemApplicationDeliveryTasks>')==1
        print('NS1_BCAT_EXACT_POST_BACKPORT_REPLAY_PASS',
              'successors=2', 'rejected_slots=21', 'sync_slots_left=0',
              'pinned_sources=immutable')

        # BCAT creator/news successors: retain local DeliveryCache and NewsStorage
        # handlers, but fail closed remote Nintendo delivery/reception surfaces.
        bcat_extra = {
            'src/core/hle/service/bcat/service_creator.cpp':
                (2899, 'dbe31f2f022c398241a55d651760f0c32d2cb86f7de4a9039d275ac02b4a1f79',
                 3260, '03ea8235a5e5a28dd14bb5448a6820fb4a36fe4158fd32444ae7f9aab8f6dd50'),
            'src/core/hle/service/bcat/service_creator.h':
                (1120, '5d27d3d39660908036b98c18811f628ca10776ea1c96d58bce27d2dbbb90a0d9',
                 1197, '46507c0de3014066c4dea7f7ccb3f7894a5ec7f57c4d0dc1cb472b066d9b5948'),
            'src/core/hle/service/bcat/news/news_service.cpp':
                (4945, '91a10861ac155b4125ece0a5faee874d90ee56b338079e96b8527d58b1fcc6a0',
                 5473, '8213114b28b51b080e7451efac3aa9f6f2e897debc56a9bab1daad8cea6ad718'),
            'src/core/hle/service/bcat/news/news_service.h':
                (1158, 'db79fca3521c6b1afd4a2a6bcc1130b2121d6c5443c6a4508aafbce5fa1cd082',
                 1231, '89e8791e2aff88485dd74e2daf355c2092ed00e06732b687ea80d095887bd0e4'),
        }
        for rel, (before_bytes, before_hash, after_bytes, after_hash) in bcat_extra.items():
            generated = (stage/rel).read_bytes()
            current = (ACTIVE/rel).read_bytes()
            assert len(generated)==before_bytes and sha(generated)==before_hash, ('BCAT extra prior drift',rel)
            assert len(current)==after_bytes and sha(current)==after_hash, ('BCAT extra active drift',rel)
            assert spec['entries'][rel] == {
                'active':after_hash, 'bytes':after_bytes, 'upstream':before_hash
            }, ('BCAT extra manifest drift',rel)
            observed[rel]=spec['entries'][rel]

        creator=(ACTIVE/'src/core/hle/service/bcat/service_creator.cpp').read_text()
        assert creator.count('&IServiceCreator::RejectUnavailableProgressService')==2
        assert creator.count('D<&IServiceCreator::CreateDeliveryCacheStorageService>')==1
        assert creator.count('D<&IServiceCreator::CreateDeliveryCacheStorageServiceWithApplicationId>')==1
        news=(ACTIVE/'src/core/hle/service/bcat/news/news_service.cpp').read_text()
        assert news.count('&INewsService::RejectUnavailableNewsBackend')==7
        for local_owner in (
            'D<&INewsService::PostLocalNews>',
            'D<&INewsService::GetTopicList>',
            'D<&INewsService::ClearStorage>',
            'D<&INewsService::GetNewsDatabaseDump>',
        ):
            assert news.count(local_owner)>=1, local_owner
        print('NS1_BCAT_REMOTE_BACKEND_EXACT_SOURCE_PASS',
              'physical_closed=11', 'bcat_sync=2', 'progress_creators=2',
              'news_remote=7', 'local_cache_preserved=1')

        # miiimg has an intentionally empty guest-visible database until a Horizon
        # image-file backend exists. The previously source-only empty-database handlers
        # must be installed into the native pinned Eden cache; file operations fail closed.
        miiimg_rel='src/core/hle/service/mii/mii.cpp'
        miiimg_entry={
            'before_sha256':'5cefdb565a5abd82233f60875d7a0e93fa5d41f16d21df3a86b3cd73d50b826d',
            'before_bytes':14164,
            'after_sha256':'e3d71bc7189d3675e16aa03bc03ea032581249625cbe3c5dc330c86f1e2dacbd',
            'after_bytes':15496,
        }
        assert miiimg_rel not in observed, ('MiiImg unexpectedly changed by frozen replay',miiimg_rel)
        assert miiimg_rel in spec['entries'], ('Missing MiiImg shipping overlay',miiimg_rel)
        generated=(stage/miiimg_rel).read_bytes()
        current=(ACTIVE/miiimg_rel).read_bytes()
        assert len(generated)==miiimg_entry['before_bytes'] and sha(generated)==miiimg_entry['before_sha256'], (
            'MiiImg pinned source drift',miiimg_rel)
        assert spec['entries'][miiimg_rel]['upstream']==miiimg_entry['before_sha256']
        assert len(current)==miiimg_entry['after_bytes'] and sha(current)==miiimg_entry['after_sha256'], (
            'Unreviewed MiiImg maintained source',miiimg_rel)
        assert spec['entries'][miiimg_rel]['active']==miiimg_entry['after_sha256']
        assert spec['entries'][miiimg_rel]['bytes']==miiimg_entry['after_bytes']
        observed[miiimg_rel]=spec['entries'][miiimg_rel]
        miiimg_cpp=(ACTIVE/miiimg_rel).read_text()
        assert miiimg_cpp.count('&IImageDatabaseService::RejectUnavailableImageFile')==9
        assert miiimg_cpp.count('D<&IImageDatabaseService::Reload>')==1
        assert miiimg_cpp.count('D<&IImageDatabaseService::GetCount>')==1
        assert miiimg_cpp.count('D<&IImageDatabaseService::IsEmpty>')==1
        assert miiimg_cpp.count('D<&IImageDatabaseService::IsFull>')==1
        assert miiimg_cpp.count('{18, nullptr, "Import"}')==1
        assert miiimg_cpp.count('{19, nullptr, "Export"}')==1
        print('NS1_MIIIMG_EXACT_POST_BACKPORT_REPLAY_PASS',
              'successors=1', 'rejected_slots=9', 'core_mii_nulls_left=2',
              'pinned_sources=immutable')

        # PDM notify is already part of the frozen NS shipping owner. Layer only the
        # reviewed local play-log notification successor over that exact generated blob.
        pdm_rel='src/core/hle/service/ns/ns.cpp'
        pdm_generated=(stage/pdm_rel).read_bytes()
        pdm_current=(ACTIVE/pdm_rel).read_bytes()
        assert pdm_rel in observed and pdm_rel in spec['entries'], (
            'Missing frozen NS owner for PDM successor',pdm_rel)
        assert len(pdm_generated)==5478 and sha(pdm_generated)=='a127ff1be0863bc47022473264ee703c3da61eeec70b84866fff9e288b95805f', (
            'PDM predecessor replay drift',pdm_rel)
        assert len(pdm_current)==6151 and sha(pdm_current)=='4af9b51074d7a9b95e30030633a60753227abf6af6ced22bc4ed7f286544d189', (
            'Unreviewed PDM maintained source',pdm_rel)
        assert spec['entries'][pdm_rel]['active']=='4af9b51074d7a9b95e30030633a60753227abf6af6ced22bc4ed7f286544d189'
        assert spec['entries'][pdm_rel]['bytes']==6151
        assert spec['entries'][pdm_rel]['upstream']=='0f937e715ef2fbac9783e7b4e46003bade0eb1cf03ab33e78eac4256a6328f88'
        pdm_text=pdm_current.decode('utf-8')
        assert pdm_text.count('&INotifyService::AcceptLocalPlayLogNotification')==6
        for command in (
            '{ 8, nullptr, "NotifyLibraryAppletEvent" }',
            '{ 9, nullptr, "Cmd9" }',
            '{ 20, nullptr, "Cmd20" }',
            '{ 30, nullptr, "Cmd30" }',
            '{ 100, nullptr, "Cmd100" }',
            '{ 101, nullptr, "Cmd101" }',
        ):
            assert pdm_text.count(command)==1, command
        assert pdm_text.count('&INotifyService::UnsupportedDebugCommand')==1
        observed[pdm_rel]=spec['entries'][pdm_rel]
        print('NS1_PDM_NOTIFY_EXACT_POST_BACKPORT_REPLAY_PASS',
              'accepted_notifications=6', 'newer_unqualified_slots=6',
              'historical_owner=preserved')

        # NSD local/offline responses were previously maintained only under
        # vendor/sources. Install them as explicit shipping owners and fail closed
        # only the reviewed Nintendo network-setting commands.
        nsd_overlays={
            'src/core/hle/service/sockets/nsd.cpp': {
                'before_sha256':'706b5751eda10aa9219a720222e1ca21bda043fe38dea478b98ac643d8b880cf',
                'before_bytes':4515,
                'after_sha256':'75a65607bcf99b344abe57393a9bb19aceab9194e4d282a083401b74422c954f',
                'after_bytes':6085,
            },
            'src/core/hle/service/sockets/nsd.h': {
                'before_sha256':'26f8440d3047ec6ab70fd45f27b4be54fdefc2763f9229a26192295e5f78ed68',
                'before_bytes':808,
                'after_sha256':'e6cee0431e3b7fbadda24ff8adb4618f7b5710be7041f15fb708a97ba6a7249d',
                'after_bytes':1056,
            },
        }
        for rel,entry in nsd_overlays.items():
            assert rel not in observed, ('NSD unexpectedly changed by frozen replay',rel)
            assert rel in spec['entries'], ('Missing NSD shipping overlay',rel)
            generated=(stage/rel).read_bytes()
            current=(ACTIVE/rel).read_bytes()
            assert len(generated)==entry['before_bytes'] and sha(generated)==entry['before_sha256'], (
                'NSD pinned source drift',rel)
            assert spec['entries'][rel]['upstream']==entry['before_sha256'], rel
            assert len(current)==entry['after_bytes'] and sha(current)==entry['after_sha256'], (
                'Unreviewed NSD maintained source',rel)
            assert spec['entries'][rel]['active']==entry['after_sha256'], rel
            assert spec['entries'][rel]['bytes']==entry['after_bytes'], rel
            observed[rel]=spec['entries'][rel]
        nsd_cpp=(ACTIVE/'src/core/hle/service/sockets/nsd.cpp').read_text()
        assert nsd_cpp.count('&NSD::RejectUnavailableNintendoSetting')==11
        assert nsd_cpp.count('&NSD::Resolve, "Resolve"')==1
        assert nsd_cpp.count('&NSD::ResolveEx, "ResolveEx"')==1
        assert nsd_cpp.count('&NSD::GetEnvironmentIdentifier')==1
        assert nsd_cpp.count('&NSD::GetApplicationServerEnvironmentType')==1
        for command in (
            '{5, nullptr, "GetSettingUrl"}',
            '{64, nullptr, "SetWithoutDomainExchangeFqdns"}',
            '{101, nullptr, "SetApplicationServerEnvironmentType"}',
            '{102, nullptr, "DeleteApplicationServerEnvironmentType"}',
        ):
            assert nsd_cpp.count(command)==1, command
        print('NS1_NSD_EXACT_POST_BACKPORT_REPLAY_PASS',
              'successors=2', 'rejected_historical_slots=11',
              'unqualified_physical_slots=4', 'pinned_sources=immutable')

        # System update is intentionally offline in Encore. Preserve the already
        # reviewed local state/event behavior, but expose it from shipping owners
        # and reject transfer/card/firmware operations that have no Horizon backend.
        system_update_overlays={
            'src/core/hle/service/ns/system_update_interface.cpp': {
                'before_sha256':'0ee7723f6edd55c94aabc8e41c50696aa779922247df9931127f982e189cae72',
                'before_bytes':2584,
                'after_sha256':'98fec76ca0b9aefcd502dbd810cb8d7eefa6bf7611a131ab40ab38a9d5232611',
                'after_bytes':5406,
            },
            'src/core/hle/service/ns/system_update_interface.h': {
                'before_sha256':'446ca472ebabcdba5160c9436eae668a24239282751739a3a335fbb96512de94',
                'before_bytes':1120,
                'after_sha256':'e7e5ad346667a12f4b03d7f2f5abbf0fc076b02e4ecfbba97b561e3fbbaea5de',
                'after_bytes':1695,
            },
            'src/core/hle/service/ns/system_update_control.cpp': {
                'before_sha256':'3c4f396c17c0bbe2c8b69e851eaf08b9421c95436cdc53ad096ae84535452530',
                'before_bytes':1733,
                'after_sha256':'5216661fcb40960e519f0071b891fae82bf9c3fc6fe19e85731d6eb0f869f7be',
                'after_bytes':3058,
            },
            'src/core/hle/service/ns/system_update_control.h': {
                'before_sha256':'8d81d0a6877e1819ca550e56e67fffe88e116addd2ae4b3c62770c648a16c028',
                'before_bytes':406,
                'after_sha256':'35d9565f0bdbd5671efa6ebc97c42d5ea7368d2e615ef27a1c51e1503362d2f9',
                'after_bytes':480,
            },
        }
        for rel,entry in system_update_overlays.items():
            assert rel not in observed, ('NS:SU unexpectedly changed by frozen replay',rel)
            assert rel in spec['entries'], ('Missing NS:SU shipping overlay',rel)
            generated=(stage/rel).read_bytes()
            current=(ACTIVE/rel).read_bytes()
            assert len(generated)==entry['before_bytes'] and sha(generated)==entry['before_sha256'], (
                'NS:SU pinned source drift',rel)
            assert spec['entries'][rel]['upstream']==entry['before_sha256'], rel
            assert len(current)==entry['after_bytes'] and sha(current)==entry['after_sha256'], (
                'Unreviewed NS:SU maintained source',rel)
            assert spec['entries'][rel]['active']==entry['after_sha256'], rel
            assert spec['entries'][rel]['bytes']==entry['after_bytes'], rel
            observed[rel]=spec['entries'][rel]
        ns_su=(ACTIVE/'src/core/hle/service/ns/system_update_interface.cpp').read_text()
        ns_su_control=(ACTIVE/'src/core/hle/service/ns/system_update_control.cpp').read_text()
        assert ns_su.count('&ISystemUpdateInterface::RejectUnavailableSystemUpdateTransfer')==2
        assert ns_su_control.count('&ISystemUpdateControl::RejectUnavailableSystemUpdate')==23
        assert ns_su_control.count('nullptr')==0
        for command in (
            '{12, nullptr, "Unknown12"}',
            '{13, nullptr, "Unknown13"}',
            '{14, nullptr, "Unknown14"}',
            '{15, nullptr, "Unknown15"}',
        ):
            assert ns_su.count(command)==1, command
        print('NS1_SYSTEM_UPDATE_EXACT_POST_BACKPORT_REPLAY_PASS',
              'successors=4', 'rejected_historical_slots=25',
              'unqualified_interface_slots=4', 'pinned_sources=immutable')

        # PDM aggregate statistics are backed by Eden play-time and launch metadata.
        # Raw play/account event queries still require the Horizon PDM log, which Encore
        # intentionally does not persist.
        pdm_query_overlays={
            'src/core/hle/service/ns/query_service.cpp': {
                'before_sha256':'90b9da8dfff82c9141685249153f373ad4d4a477b8d9dbcd049f0637228c5581',
                'before_bytes':4583,
                'after_sha256':'8acc95fba8b1871c20dc4a64140654a3471c26557857e68cec139b3c1f2198c0',
                'after_bytes':10195,
            },
            'src/core/hle/service/ns/query_service.h': {
                'before_sha256':'c892d6cc75b1b7df5d87bb2f39540096765a0569397a31dc07b71cc2947a3dbd',
                'before_bytes':2326,
                'after_sha256':'fb7bc2c8358e0e152bbcec15a3ae7df26c85ca049e372f484d15371d9ba3ea55',
                'after_bytes':3758,
            },
        }
        for rel,entry in pdm_query_overlays.items():
            assert rel not in observed, ('PDM query unexpectedly changed by frozen replay',rel)
            assert rel in spec['entries'], ('Missing PDM query shipping overlay',rel)
            generated=(stage/rel).read_bytes()
            current=(ACTIVE/rel).read_bytes()
            assert len(generated)==entry['before_bytes'] and sha(generated)==entry['before_sha256'], (
                'PDM query pinned source drift',rel)
            assert spec['entries'][rel]['upstream']==entry['before_sha256'], rel
            assert len(current)==entry['after_bytes'] and sha(current)==entry['after_sha256'], (
                'Unreviewed PDM query maintained source',rel)
            assert spec['entries'][rel]['active']==entry['after_sha256'], rel
            assert spec['entries'][rel]['bytes']==entry['after_bytes'], rel
            observed[rel]=spec['entries'][rel]
        pdm_query=(ACTIVE/'src/core/hle/service/ns/query_service.cpp').read_text()
        pdm_header=(ACTIVE/'src/core/hle/service/ns/query_service.h').read_text()
        assert pdm_query.count('D<&IQueryService::QueryPlayStatisticsByApplicationId>')==1
        assert pdm_query.count('D<&IQueryService::QueryPlayStatisticsByApplicationIdAndUserAccountId>')==1
        assert pdm_query.count('D<&IQueryService::QueryLastPlayTimeV0>')==1
        assert pdm_query.count('D<&IQueryService::QueryApplicationPlayStatisticsForSystemV0>')==1
        assert pdm_query.count('D<&IQueryService::QueryApplicationPlayStatisticsByUserAccountIdForSystemV0>')==1
        assert pdm_query.count('&IQueryService::RejectUnavailablePlayLogQuery')==16
        assert pdm_query.count('nullptr')==0
        assert 'constexpr s64 HorizonMinuteEpoch = 946598400' in pdm_query
        assert 'InArray<u64, BufferAttr_HipcMapAlias> application_ids' in pdm_query
        assert 'static_assert(sizeof(LastPlayTime) == 0x18' in pdm_header
        assert 'u32 minutes_since_last_played{};' in pdm_header
        assert 'u8 has_minutes_since_last_played{};' in pdm_header
        print('NS1_PDM_QUERY_EXACT_POST_BACKPORT_REPLAY_PASS',
              'successors=2', 'real_application_stats=2',
              'v0_functional_wrappers=3', 'last_play_time_abi=0x18',
              'raw_playlog_rejections=16', 'physical_nulls=0',
              'pinned_sources=immutable')

        # btdrv/bt are Switch Bluetooth UART/BSA services. Encore has no guest
        # Bluetooth controller backend on PS5; keep the real bt event and fail closed
        # all hardware/GATT operations from the exact reviewed shipping owner.
        btdrv_rel='src/core/hle/service/btdrv/btdrv.cpp'
        btdrv_entry={
            'before_sha256':'c88bda026ea851e357db1fffd1226d9f07a8fc438b87af0e5e20bf9b5c5aa57c',
            'before_bytes':9543,
            'after_sha256':'60ab520184f4f7ba390424ce9bf5c8f47693456a7afdef558f27f366157baa61',
            'after_bytes':16709,
        }
        assert btdrv_rel not in observed, ('BTDRV unexpectedly changed by frozen replay',btdrv_rel)
        assert btdrv_rel in spec['entries'], ('Missing BTDRV shipping overlay',btdrv_rel)
        generated=(stage/btdrv_rel).read_bytes()
        current=(ACTIVE/btdrv_rel).read_bytes()
        assert len(generated)==btdrv_entry['before_bytes'] and sha(generated)==btdrv_entry['before_sha256'], (
            'BTDRV pinned source drift',btdrv_rel)
        assert spec['entries'][btdrv_rel]['upstream']==btdrv_entry['before_sha256']
        assert len(current)==btdrv_entry['after_bytes'] and sha(current)==btdrv_entry['after_sha256'], (
            'Unreviewed BTDRV maintained source',btdrv_rel)
        assert spec['entries'][btdrv_rel]['active']==btdrv_entry['after_sha256']
        assert spec['entries'][btdrv_rel]['bytes']==btdrv_entry['after_bytes']
        observed[btdrv_rel]=spec['entries'][btdrv_rel]
        btdrv_cpp=(ACTIVE/btdrv_rel).read_text()
        assert btdrv_cpp.count('&IBluetoothUser::RejectUnavailableBluetoothUser')==9
        assert btdrv_cpp.count('&IBluetoothDriver::RejectUnavailableBluetoothHardware')==129
        assert btdrv_cpp.count('nullptr')==0
        assert btdrv_cpp.count('C<&IBluetoothUser::RegisterBleEvent>')==1
        assert btdrv_cpp.count('&IBluetoothDriver::EnableRadio')==1
        assert btdrv_cpp.count('&IBluetoothDriver::UnsupportedDebugCommand')==1
        print('NS1_BTDRV_EXACT_POST_BACKPORT_REPLAY_PASS',
              'bt_user_rejections=9', 'driver_rejections=129',
              'physical_nulls=0', 'pinned_sources=immutable')

        # caps:sc controls the Switch screenshot-capture module, not the normal
        # guest display path. Encore has AlbumManager-backed album services but no
        # raw screenshot-control/shared-buffer backend.
        caps_sc_overlays={
            'src/core/hle/service/caps/caps_sc.cpp': {
                'before_sha256':'ad576f05a16b9f46374ea7744617307c24505f702e01891dd1581a68a94b03cb',
                'before_bytes':1573,
                'after_sha256':'7738dad7be563ddec28c31bf7171c21add60a273be177687e19d201ee4d46fcd',
                'after_bytes':2886,
            },
            'src/core/hle/service/caps/caps_sc.h': {
                'before_sha256':'7393d4e1412202d7f9b07af303325c5bb07375b8af5e17a9c4287c62d195f98b',
                'before_bytes':470,
                'after_sha256':'04e55e77d5b5535731df71f48247c9f086590bfead83b7055677ed06b771bcd7',
                'after_bytes':549,
            },
        }
        for rel,entry in caps_sc_overlays.items():
            assert rel not in observed, ('CAPS:SC unexpectedly changed by frozen replay',rel)
            assert rel in spec['entries'], ('Missing CAPS:SC shipping overlay',rel)
            generated=(stage/rel).read_bytes()
            current=(ACTIVE/rel).read_bytes()
            assert len(generated)==entry['before_bytes'] and sha(generated)==entry['before_sha256'], (
                'CAPS:SC pinned source drift',rel)
            assert spec['entries'][rel]['upstream']==entry['before_sha256'], rel
            assert len(current)==entry['after_bytes'] and sha(current)==entry['after_sha256'], (
                'Unreviewed CAPS:SC maintained source',rel)
            assert spec['entries'][rel]['active']==entry['after_sha256'], rel
            assert spec['entries'][rel]['bytes']==entry['after_bytes'], rel
            observed[rel]=spec['entries'][rel]
        caps_sc_cpp=(ACTIVE/'src/core/hle/service/caps/caps_sc.cpp').read_text()
        assert caps_sc_cpp.count('&IScreenShotControlService::RejectUnavailableScreenShotControl')==20
        assert caps_sc_cpp.count('nullptr')==0
        print('NS1_CAPS_SC_EXACT_POST_BACKPORT_REPLAY_PASS',
              'rejected_slots=20', 'physical_nulls=0',
              'pinned_sources=immutable')

        # caps:c keeps real AlbumManager-backed registration/storage state, but Encore
        # has no Horizon album movie read/write stream backend. Admit exactly the
        # reviewed shipping owner and keep screenshot-file operations open for real work.
        caps_c_overlays={
            'src/core/hle/service/caps/caps_c.cpp': {
                'before_sha256':'4207c00db15d28949c3299ec36814d35ba77625594a454857bf1c97d4ca6bd95',
                'before_bytes':2427,
                'after_sha256':'8e3d804411b15d512abf536914c4cc52ba81ec63e13900976d0b7024619b3eb6',
                'after_bytes':7549,
            },
            'src/core/hle/service/caps/caps_c.h': {
                'before_sha256':'2f6b8e4567725287f959b54928bd74f3516d6a67a404ea48a52d408eafab4d17',
                'before_bytes':828,
                'after_sha256':'74f731531f62a7e26e33a09ffd9623b0613f89075cacab1c052e062a0ef96722',
                'after_bytes':1734,
            },
        }
        for rel,entry in caps_c_overlays.items():
            assert rel not in observed, ('CAPS:C unexpectedly changed by frozen replay',rel)
            assert rel in spec['entries'], ('Missing CAPS:C shipping overlay',rel)
            generated=(stage/rel).read_bytes()
            current=(ACTIVE/rel).read_bytes()
            assert len(generated)==entry['before_bytes'] and sha(generated)==entry['before_sha256'], (
                'CAPS:C pinned source drift',rel)
            assert spec['entries'][rel]['upstream']==entry['before_sha256'], rel
            assert len(current)==entry['after_bytes'] and sha(current)==entry['after_sha256'], (
                'Unreviewed CAPS:C maintained source',rel)
            assert spec['entries'][rel]['active']==entry['after_sha256'], rel
            assert spec['entries'][rel]['bytes']==entry['after_bytes'], rel
            observed[rel]=spec['entries'][rel]
        caps_c_cpp=(ACTIVE/'src/core/hle/service/caps/caps_c.cpp').read_text()
        assert caps_c_cpp.count('&IAlbumControlService::RejectUnavailableMovieBackend')==22
        assert caps_c_cpp.count('D<&IAlbumControlService::NotifyAlbumStorageIsAvailable>')==1
        assert caps_c_cpp.count('D<&IAlbumControlService::NotifyAlbumStorageIsUnavailable>')==1
        assert caps_c_cpp.count('D<&IAlbumControlService::RegisterAppletResourceUserId>')==1
        assert caps_c_cpp.count('D<&IAlbumControlService::UnregisterAppletResourceUserId>')==1
        assert caps_c_cpp.count('D<&IAlbumControlService::GetApplicationIdFromAruid>')==1
        assert caps_c_cpp.count('D<&IAlbumControlService::CheckApplicationIdRegistered>')==1
        assert caps_c_cpp.count('nullptr')==11
        print('NS1_CAPS_C_EXACT_POST_BACKPORT_REPLAY_PASS',
              'movie_rejections=22', 'remaining_slots=11',
              'pinned_sources=immutable')

        # ACC_SU successor: close only the Nintendo Account/auth network paths.
        # Prove the new owner reverses exactly to the previously accepted ACC blob.
        acc_rel='src/core/hle/service/acc/acc.cpp'
        assert acc_rel in observed and acc_rel in spec['entries'], ('Missing ACC shipping owner',acc_rel)
        assert observed[acc_rel]['active']=='f4f16cb50903e66cf1c320c8ccefec2c457e32221c38238230c76af92243f5bf'
        assert observed[acc_rel]['bytes']==90909
        acc_current=(ACTIVE/acc_rel).read_text()
        assert len(acc_current.encode())==91522
        assert sha(acc_current.encode())=='fd20d50067f508f246e7857f9d92cb634a8bc07584ae02a4c191502cf6c181c6'
        acc_prior=acc_current
        acc_names=(
            'CheckNetworkServiceAvailabilityAsync',
            'AuthenticateApplicationAsync',
            'EnsureSignedDeviceIdentifierCacheForNintendoAccountAsync',
            'LoadSignedDeviceIdentifierCacheForNintendoAccount',
            'CreateFloatingRegistrationRequest',
            'CreateProcedureToRegisterUserWithNintendoAccount',
            'ResumeProcedureToRegisterUserWithNintendoAccount',
            'AuthenticateServiceAsync',
            'ProxyProcedureForGuestLoginWithNintendoAccount',
            'ProxyProcedureForFloatingRegistrationWithNintendoAccount',
            'SuspendBackgroundDaemon',
        )
        for name in acc_names:
            after=f'&ACC_SU::RejectUnavailableNintendoAccount, "{name}"'
            before=f'nullptr, "{name}"'
            assert acc_prior.count(after)==1, name
            acc_prior=acc_prior.replace(after,before,1)
        acc_handler='''    void RejectUnavailableNintendoAccount(HLERequestContext& ctx) {
        LOG_DEBUG(Service_ACC, "Rejected acc:su Nintendo Account/auth backend operation");
        IPC::ResponseBuilder rb{ctx, 2};
        rb.Push(ResultUnknown);
    }

'''
        assert acc_prior.count(acc_handler)==1
        acc_prior=acc_prior.replace(acc_handler,'',1)
        assert len(acc_prior.encode())==90909
        assert sha(acc_prior.encode())=='f4f16cb50903e66cf1c320c8ccefec2c457e32221c38238230c76af92243f5bf'
        assert spec['entries'][acc_rel]['active']=='fd20d50067f508f246e7857f9d92cb634a8bc07584ae02a4c191502cf6c181c6'
        assert spec['entries'][acc_rel]['bytes']==91522
        assert spec['entries'][acc_rel]['upstream']=='95857946c85c42721f123d4e591d880a57e2cfd9bc74ec995741e633975af02b'
        observed[acc_rel]=spec['entries'][acc_rel]
        print('NS1_ACC_SU_AUTH_SUCCESSOR_REPLAY_PASS',
              'rejected_slots=11', 'local_nulls_preserved=18')

        # CAPS:A successor: make existing AlbumManager accessors shipping, implement
        # thumbnail Ex0, and fail closed only the movie-read backend.
        caps_a_overlays={
            'src/core/hle/service/caps/caps_a.cpp': {
                'before_sha256':'87b0ddbd87dfb576b3c3b04132ae4a2b5b4d82b2c47697b894d9e27144614070',
                'before_bytes':8845,
                'after_sha256':'2dbc991930f11b5a1b9610466707bc0c98057d4b69ab2cf8bc2945a33fc41709',
                'after_bytes':16414,
            },
            'src/core/hle/service/caps/caps_a.h': {
                'before_sha256':'8cd0a0575d2bc624f0feed26930c4f9378a56f36afb287d1431a6d5ce76c3450',
                'before_bytes':2398,
                'after_sha256':'d3e63d69825bec5b2ca29d44b53e45257e62b1732255df3b1260ba041344fb18',
                'after_bytes':5512,
            },
        }
        for rel,entry in caps_a_overlays.items():
            assert rel not in observed, ('CAPS:A unexpectedly changed by frozen replay',rel)
            assert rel in spec['entries'], ('Missing CAPS:A shipping overlay',rel)
            generated=(stage/rel).read_bytes()
            current=(ACTIVE/rel).read_bytes()
            assert len(generated)==entry['before_bytes'] and sha(generated)==entry['before_sha256'], ('CAPS:A pinned drift',rel)
            assert spec['entries'][rel]['upstream']==entry['before_sha256'], rel
            assert len(current)==entry['after_bytes'] and sha(current)==entry['after_sha256'], ('CAPS:A active drift',rel)
            assert spec['entries'][rel]['active']==entry['after_sha256'], rel
            assert spec['entries'][rel]['bytes']==entry['after_bytes'], rel
            observed[rel]=spec['entries'][rel]
        caps_a_cpp=(ACTIVE/'src/core/hle/service/caps/caps_a.cpp').read_text()
        assert caps_a_cpp.count('&IAlbumAccessorService::RejectUnavailableMovieBackend')==9
        assert caps_a_cpp.count('D<&IAlbumAccessorService::LoadAlbumScreenShotThumbnailImageEx0>')==1
        assert caps_a_cpp.count('nullptr')==15
        print('NS1_CAPS_A_EXACT_POST_BACKPORT_REPLAY_PASS',
              'movie_rejections=9', 'thumbnail_ex0=real', 'remaining_slots=15')

        # CAPS:U application album accessors are backed by AlbumManager. Only movie
        # streams and the unmodeled accessor session fail closed; two potentially
        # implementable application-list/precheck commands remain open.
        caps_u_overlays={
            'src/core/hle/service/caps/caps_u.cpp': {
                'before_sha256':'38fbee7328ffedd64a646d9c8ff6cf0daa9995ac14ec28cd54fbf4b136205189',
                'before_bytes':8440,
                'after_sha256':'bba7c8662e2e6e55ff330657bdc10526bd4d392bc58ca2f332485ff21659799f',
                'after_bytes':10431,
            },
            'src/core/hle/service/caps/caps_u.h': {
                'before_sha256':'90deaea4f1586080accec3509a9b63a185aa666f6cc6eb969cced2a8d38185f0',
                'before_bytes':3387,
                'after_sha256':'f3b41e0522c459a0da773b4f080e6d1cdaac1740d503cce56961e6ce90a0fecb',
                'after_bytes':4135,
            },
        }
        for rel,entry in caps_u_overlays.items():
            assert rel not in observed, ('CAPS:U unexpectedly changed by frozen replay',rel)
            assert rel in spec['entries'], ('Missing CAPS:U shipping overlay',rel)
            generated=(stage/rel).read_bytes()
            current=(ACTIVE/rel).read_bytes()
            assert len(generated)==entry['before_bytes'] and sha(generated)==entry['before_sha256'], ('CAPS:U pinned drift',rel)
            assert spec['entries'][rel]['upstream']==entry['before_sha256'], rel
            assert len(current)==entry['after_bytes'] and sha(current)==entry['after_sha256'], ('CAPS:U active drift',rel)
            assert spec['entries'][rel]['active']==entry['after_sha256'], rel
            assert spec['entries'][rel]['bytes']==entry['after_bytes'], rel
            observed[rel]=spec['entries'][rel]
        caps_u_cpp=(ACTIVE/'src/core/hle/service/caps/caps_u.cpp').read_text()
        assert caps_u_cpp.count('&IAlbumApplicationService::RejectUnavailableMovieOrSessionBackend')==6
        assert caps_u_cpp.count('nullptr')==2
        print('NS1_CAPS_U_EXACT_POST_BACKPORT_REPLAY_PASS',
              'movie_session_rejections=6', 'remaining_slots=2')

        # NOTIF alarm CRUD keeps the exact application parameter bytes alongside
        # each AlarmSetting. This removes the previous data-loss TODO without claiming
        # persistent Horizon scheduling across process restarts.
        notif_overlays={
            'src/core/hle/service/glue/notif.cpp': {
                'before_sha256':'e8a7f633f1ca9e577fe9d7125d490bb32846204ebc65e5b3a2b16fa7da8b2716',
                'before_bytes':12051,
                'after_sha256':'2a4006fbb09233ffc2cfdfd812a8bec7aa14ac79edc839c4b5f086c0069f931c',
                'after_bytes':13885,
            },
            'src/core/hle/service/glue/notif.h': {
                'before_sha256':'593c6fff73fcbc2b3a27d16d4106dfcea51ea548072b3ec2fc5e5bbc73758d36',
                'before_bytes':5452,
                'after_sha256':'4dfa482df32a60c34314fd7c036c044f989494b351e46c46f871e57c5458294d',
                'after_bytes':5698,
            },
        }
        for rel,entry in notif_overlays.items():
            assert rel not in observed, ('NOTIF unexpectedly changed by frozen replay',rel)
            assert rel in spec['entries'], ('Missing NOTIF shipping overlay',rel)
            generated=(stage/rel).read_bytes()
            current=(ACTIVE/rel).read_bytes()
            assert len(generated)==entry['before_bytes'] and sha(generated)==entry['before_sha256'], ('NOTIF pinned drift',rel)
            assert spec['entries'][rel]['upstream']==entry['before_sha256'], rel
            assert len(current)==entry['after_bytes'] and sha(current)==entry['after_sha256'], ('NOTIF active drift',rel)
            assert spec['entries'][rel]['active']==entry['after_sha256'], rel
            assert spec['entries'][rel]['bytes']==entry['after_bytes'], rel
            observed[rel]=spec['entries'][rel]
        notif_cpp=(ACTIVE/'src/core/hle/service/glue/notif.cpp').read_text()
        notif_h=(ACTIVE/'src/core/hle/service/glue/notif.h').read_text()
        assert 'alarms.size() >= MaxAlarms' in notif_cpp
        assert 'application_parameters.push_back(stored);' in notif_cpp
        assert 'application_parameters.erase(application_parameters.begin() + index);' in notif_cpp
        assert 'StoredApplicationParameter' in notif_h
        assert 'TODO: Save application parameter data' not in notif_cpp
        assert 'TODO: Read application parameter related to this setting id' not in notif_cpp
        assert notif_cpp.count('&INotificationServices::RejectUnsupportedNotificationCommand')==12
        assert notif_h.count('RejectUnsupportedNotificationCommand')==1
        print('NS1_NOTIF_ALARM_PARAMETER_REPLAY_PASS',
              'shared_crud=notif_a+notif_s', 'parameter_bytes=preserved',
              'unsupported_notification_slots=12')


        # GRC and OLSC: the PS5 build must not advertise Switch hardware
        # movie capture or Nintendo online-save transfers that have no backend.
        # Reverse precisely the reviewed owner edits to the frozen patch replay.
        secondary = {
            'src/core/hle/service/grc/grc.cpp': (
                '0cfefe15f41358b3b97534237c49a9b41399f2d1f7162872accfa071572e59e7',
                1733,
                '2250f140013ac91886c68af289685244ab6157ca86967d67f123bc4685971f39',
                2493),
            'src/core/hle/service/olsc/transfer_task_list_controller.cpp': (
                'c391738f09c3d46478de2e86b7b52818d6658493195c79c91319d1c36e7778e6',
                4631,
                '8cc97fdba504fa7de0d8ca893239b5674217bd81a134bef27436f3ec3483b57d',
                6179),
            'src/core/hle/service/olsc/transfer_task_list_controller.h': (
                '686ae36cbe673f1038b936882b822b342ab7cc674d40fc290f9325afd609e594',
                1252,
                '359e9311b0d99b74353edac18b61ffab0c6182826edba8108d3390ff37549a28',
                1317),
        }
        for rel, (before_sha, before_len, after_sha, after_len) in secondary.items():
            assert rel in observed and rel in spec['entries'], ('Missing replay owner', rel)
            before = (stage / rel).read_bytes()
            after = (ACTIVE / rel).read_bytes()
            assert len(before) == before_len and sha(before) == before_sha, ('GRC/OLSC prior drift', rel)
            assert len(after) == after_len and sha(after) == after_sha, ('GRC/OLSC owner drift', rel)
            assert spec['entries'][rel]['active'] == after_sha
            assert spec['entries'][rel]['bytes'] == after_len
            reconstructed = after.decode('utf-8')
            if rel.endswith('/grc/grc.cpp'):
                for owner, count in (('GRC', 5), ('GRC_D', 3)):
                    pointer = '&' + owner + '::RejectUnavailableGameRecording'
                    assert reconstructed.count(pointer) == count
                    reconstructed = reconstructed.replace(pointer, 'nullptr')
                method = (
                    '\nprivate:\n'
                    '    void RejectUnavailableGameRecording(HLERequestContext& ctx) {\n'
                    '        // No Horizon recording or trimming backend; never report a fabricated movie.\n'
                    '        IPC::ResponseBuilder rb{ctx, 2};\n'
                    '        rb.Push(ResultUnknown);\n'
                    '    }\n'
                )
                assert reconstructed.count(method) == 2
                reconstructed = reconstructed.replace(method, '\n')
                assert reconstructed.count('#include "core/hle/service/ipc_helpers.h"\n') == 1
                reconstructed = reconstructed.replace('#include "core/hle/service/ipc_helpers.h"\n', '', 1)
            elif rel.endswith('.cpp'):
                pointer = '&ITransferTaskListController::RejectUnavailableCloudTransfer'
                assert reconstructed.count(pointer) == 24
                reconstructed = reconstructed.replace(pointer, 'nullptr')
                method = (
                    '\n\nvoid ITransferTaskListController::RejectUnavailableCloudTransfer(HLERequestContext& ctx) {\n'
                    '    // No Nintendo cloud-backup transfer backend or task scheduler on PS5.\n'
                    '    IPC::ResponseBuilder rb{ctx, 2};\n'
                    '    rb.Push(ResultUnknown);\n'
                    '}'
                )
                assert reconstructed.count(method) == 1
                reconstructed = reconstructed.replace(method, '', 1)
                assert reconstructed.count('#include "core/hle/service/ipc_helpers.h"\n') == 1
                reconstructed = reconstructed.replace('#include "core/hle/service/ipc_helpers.h"\n', '', 1)
            else:
                method = '    void RejectUnavailableCloudTransfer(HLERequestContext& ctx);\n'
                assert reconstructed.count(method) == 1
                reconstructed = reconstructed.replace(method, '', 1)
            assert reconstructed.encode('utf-8') == before, ('GRC/OLSC reverse mismatch', rel)
            observed[rel] = spec['entries'][rel]
        print('NS1_GRC_OLSC_EXACT_POST_BACKPORT_REPLAY_PASS',
              'physical_nulls=32', 'reconstructed_owners=3', 'native_handlers_preserved')


        # NS1 acc:e/u1/u2 supersede the removed acc:u0/u1 on HOS 13+.
        # Reuse the implemented local profile + persistent-thumbnail handlers.
        # Reverse each exact owner binding to the historic nullptr before
        # accepting the new shipping acc.cpp in the frozen Eden replay.
        acc_rel = 'src/core/hle/service/acc/acc.cpp'

        # A second exact successor adds explicit offline errors ONLY for Nintendo
        # online, firmware-debug and remote migration requests. Retain the
        # previously reviewed 45 real local handlers and reverse this layer
        # first so the historical ACC replay remains strict.
        acc_newest = (ACTIVE / acc_rel).read_bytes()
        assert len(acc_newest) == 102756 and sha(acc_newest) == '933ea9c58805cb783518ae3b49a420885d15e8c874a0496efc59792e99c9e9f9'
        assert spec['entries'][acc_rel]['active'] == sha(acc_newest)
        assert spec['entries'][acc_rel]['bytes'] == len(acc_newest)
        import re

        remaining_acc_owners = {
            'INotifier':1, 'IManagerForApplication':2, 'ACC_SU':18, 'ACC_U0':6,
            'ACC_U1':22, 'ACC_E':23, 'ACC_E_U1':7, 'ACC_E_U2':12,
        }
        newest_lines = acc_newest.decode('utf-8').splitlines(keepends=True)
        remaining_owner = ''
        remaining_counts = dict.fromkeys(remaining_acc_owners, 0)
        for i, line in enumerate(newest_lines):
            class_match = re.match(r'^class ([A-Za-z0-9_]+) final', line)
            if class_match:
                remaining_owner = class_match.group(1)
            if line.startswith('void LoopProcess'):
                remaining_owner = ''
            if remaining_owner not in remaining_acc_owners:
                continue
            pointer = '&' + remaining_owner + '::RejectUnsupportedRemainingAccountCommand'
            if pointer in line:
                assert line.count(pointer) == 1
                newest_lines[i] = line.replace(pointer, 'nullptr', 1)
                remaining_counts[remaining_owner] += 1
        assert remaining_counts == remaining_acc_owners

        remaining_method = (
            '\nprivate:\n'
            '    void RejectUnsupportedRemainingAccountCommand(HLERequestContext& ctx) {\n'
            '        // Local profile/user commands already implemented above remain untouched.\n'
            '        // Remaining entries require Nintendo Account, notification, PIN policy,\n'
            '        // debug, thumbnail or firmware services not modeled by Encore.\n'
            '        IPC::ResponseBuilder rb{ctx, 2};\n'
            '        rb.Push(IPC::ResultNotSupported);\n'
            '    }\n'
        )
        acc_reconstructed = ''.join(newest_lines)
        assert acc_reconstructed.count(remaining_method) == 8
        acc_reconstructed = acc_reconstructed.replace(remaining_method, '')

        dummy_pointer = '&ISessionObject::AcceptDummy'
        assert acc_reconstructed.count(dummy_pointer) == 1
        acc_reconstructed = acc_reconstructed.replace(dummy_pointer, 'nullptr', 1)
        dummy_method = (
            '\nprivate:\n'
            '    void AcceptDummy(HLERequestContext& ctx) {\n'
            '        IPC::ResponseBuilder rb{ctx, 2};\n'
            '        rb.Push(ResultSuccess);\n'
            '    }\n'
        )
        assert acc_reconstructed.count(dummy_method) == 1
        acc_reconstructed = acc_reconstructed.replace(dummy_method, '', 1)
        acc_current = acc_reconstructed.encode('utf-8')
        assert len(acc_current) == 95439 and sha(acc_current) == '71c34670cc93158e954ac7a04b3b52cbe60306aaf5c6948ce50ca2ee663d2595'
        assert len(re.findall(rb'\{\s*\d+\s*,\s*nullptr\s*,', acc_newest)) == 0
        print('NS1_ACC_REMAINING_EXACT_REVERSE_PASS',
              'physical_closed=92', 'fail_closed=91', 'dummy_success=1',
              'local_profile_handlers_preserved=1')

        offline_commands = {"ACC_E":[99,103,105,106,151,152,170,210,211,212,213,214,215,230,251,290,291,292,293,299,350,351,352,353,900,901,902,910,997,998,999,10105],"ACC_E_U1":[99,103,105,106,151,152,170,997,998,999],"ACC_E_U2":[99,103,105,106,151,152,170,997,998,999]}
        offline_lines = acc_current.decode('utf-8').splitlines(keepends=True)
        offline_owner = ''
        offline_counts = dict.fromkeys(offline_commands, 0)
        for i, line in enumerate(offline_lines):
            class_match = re.match(r'^class (ACC_E(?:_U1|_U2)?) final : public Module::Interface', line)
            if class_match:
                offline_owner = class_match.group(1)
            if line.startswith('void LoopProcess'):
                offline_owner = ''
            if offline_owner == '':
                continue
            match = re.match(r'^\s*\{\s*(\d+),\s*&(\w+)::RejectUnsupportedOnlineOrDebugCommand,', line)
            if match:
                assert match.group(2) == offline_owner
                assert int(match.group(1)) in offline_commands[offline_owner]
                pointer = '&' + offline_owner + '::RejectUnsupportedOnlineOrDebugCommand'
                assert offline_lines[i].count(pointer) == 1
                offline_lines[i] = line.replace(pointer, 'nullptr', 1)
                offline_counts[offline_owner] += 1
        assert offline_counts == {'ACC_E': 32, 'ACC_E_U1': 10, 'ACC_E_U2': 10}
        offline_method = (
            '\nprivate:\n'
            '    void RejectUnsupportedOnlineOrDebugCommand(HLERequestContext& ctx) {\n'
            '        // No Nintendo Account network, migration, or firmware debug backend on PS5.\n'
            '        IPC::ResponseBuilder rb{ctx, 2};\n'
            '        rb.Push(ResultUnknown);\n'
            '    }\n'
        )
        offline_reconstructed = ''.join(offline_lines)
        assert offline_reconstructed.count(offline_method) == 3
        offline_reconstructed = offline_reconstructed.replace(offline_method, '\n')
        acc_after = offline_reconstructed.encode('utf-8')
        assert len(acc_after) == 92665 and sha(acc_after) == 'ea76666ba632cf71542eb38b9a9468a608ef2de769b5d152dd9f9c8501ee07a5'
        print('NS1_ACC_ENTITY_OFFLINE_EXACT_REVERSE_PASS',
              'closed_online_debug=52', 'owners=3', 'prior_local_bindings=preserved')

        acc_before = (stage / acc_rel).read_bytes()
        assert acc_rel in observed and acc_rel in spec['entries']
        assert len(acc_before) == 91522 and sha(acc_before) == 'fd20d50067f508f246e7857f9d92cb634a8bc07584ae02a4c191502cf6c181c6'
        assert len(acc_after) == 92665 and sha(acc_after) == 'ea76666ba632cf71542eb38b9a9468a608ef2de769b5d152dd9f9c8501ee07a5'
        assert spec['entries'][acc_rel]['active'] == sha(acc_newest)
        assert spec['entries'][acc_rel]['bytes'] == len(acc_newest)
        import re
        acc_bindings = {"ACC_E":{"0":"GetUserCount","1":"GetUserExistence","2":"ListAllUsers","3":"ListOpenUsers","4":"GetLastOpenedUser","5":"GetProfile","50":"IsUserRegistrationRequestPermitted","51":"TrySelectUserWithoutInteractionDeprecated","52":"TrySelectUserWithoutInteraction","102":"GetBaasAccountManagerForSystemService","110":"StoreSaveDataThumbnailSystem","111":"ClearSaveDataThumbnail","112":"LoadSaveDataThumbnail","113":"GetSaveDataThumbnailExistence","140":"ListQualifiedUsers"},"ACC_E_U1":{"0":"GetUserCount","1":"GetUserExistence","2":"ListAllUsers","3":"ListOpenUsers","4":"GetLastOpenedUser","5":"GetProfile","50":"IsUserRegistrationRequestPermitted","51":"TrySelectUserWithoutInteractionDeprecated","102":"GetBaasAccountManagerForSystemService","110":"StoreSaveDataThumbnailSystem","111":"ClearSaveDataThumbnail","112":"LoadSaveDataThumbnail","113":"GetSaveDataThumbnailExistence","140":"ListQualifiedUsers"},"ACC_E_U2":{"0":"GetUserCount","1":"GetUserExistence","2":"ListAllUsers","3":"ListOpenUsers","4":"GetLastOpenedUser","5":"GetProfile","50":"IsUserRegistrationRequestPermitted","51":"TrySelectUserWithoutInteractionDeprecated","52":"TrySelectUserWithoutInteraction","102":"GetBaasAccountManagerForSystemService","110":"StoreSaveDataThumbnailSystem","111":"ClearSaveDataThumbnail","112":"LoadSaveDataThumbnail","113":"GetSaveDataThumbnailExistence","140":"ListQualifiedUsers","205":"GetProfileEditor"}}
        lines = acc_after.decode('utf-8').splitlines(keepends=True)
        owner = ''
        restored = dict.fromkeys(acc_bindings, 0)
        for i, line in enumerate(lines):
            service_match = re.match(r'^class (ACC_E(?:_U1|_U2)?) final : public Module::Interface', line)
            if service_match:
                owner = service_match.group(1)
            if line.startswith('void LoopProcess'):
                owner = ''
            if not owner:
                continue
            command = re.match(r'^\s*\{\s*(\d+),\s*&(\w+)::(\w+),', line)
            if command and command.group(1) in acc_bindings[owner]:
                assert command.group(2) == owner
                assert command.group(3) == acc_bindings[owner][command.group(1)]
                pointer = '&' + owner + '::' + command.group(3)
                assert lines[i].count(pointer) == 1
                lines[i] = line.replace(pointer, 'nullptr', 1)
                restored[owner] += 1
        assert restored == {'ACC_E': 15, 'ACC_E_U1': 14, 'ACC_E_U2': 16}
        assert ''.join(lines).encode('utf-8') == acc_before, 'ACC entity exact reverse mismatch'
        observed[acc_rel] = spec['entries'][acc_rel]
        print('NS1_ACC_ENTITY_EXACT_POST_BACKPORT_REPLAY_PASS',
              'real_local_bindings=45', 'owners=acc:e+acc:e:u1+acc:e:u2',
              'pinned_sources=immutable')



        # Real HOS23 NS cmd92: derive the current running ProgramId from the
        # actual main applet rather than leaving an indexed IMPL-SRC false
        # positive with a native nullptr. Reverse CPP+header exactly.
        ns_rel = 'src/core/hle/service/ns/application_manager_interface.cpp'
        ns_latest = (ACTIVE / ns_rel).read_bytes()
        assert len(ns_latest) == 69568 and sha(ns_latest) == '4e56c70f94896da6ddbd885bb178091b367c8de5b76b0bca0ca624ee6d4d0ee0'
        assert spec['entries'][ns_rel]['active'] == sha(ns_latest)
        ns_view_pointer = '{3, D<&IApplicationManagerInterface::GetApplicationViewDeprecated>, "GetApplicationViewDeprecated"},'
        ns_view_pointer_old = '{3, nullptr, "GetApplicationViewDeprecated"},'
        ns_text = ns_latest.decode('utf-8')
        assert ns_text.count(ns_view_pointer) == 1
        ns_text = ns_text.replace(ns_view_pointer, ns_view_pointer_old, 1)
        ns_latest_cmd92 = ns_text.encode('utf-8')
        assert len(ns_latest_cmd92) == 69513 and sha(ns_latest_cmd92) == '1c0af884c3144a0b8bf9ef798c5fe918706e4abe5e7b32557b5b4a72800aaa84'
        ns_method = "Result IApplicationManagerInterface::GetRunningApplicationProgramId(\n    Out<u64> out_program_id) {\n    auto* const window_system = system.GetAppletManager().GetWindowSystem();\n    R_UNLESS(window_system != nullptr, AM::ResultApplicationRecordNotFound);\n    const auto applet = window_system->GetMainApplet();\n    R_UNLESS(applet != nullptr, AM::ResultApplicationRecordNotFound);\n\n    *out_program_id = applet->program_id;\n    R_SUCCEED();\n}\n\n"
        ns_pointer = '{92, D<&IApplicationManagerInterface::GetRunningApplicationProgramId>, "GetRunningApplicationProgramId"},'
        ns_pointer_old = '{92, nullptr, "GetRunningApplicationProgramId"},'
        ns_text = ns_latest_cmd92.decode('utf-8')
        assert ns_text.count(ns_method) == 1 and ns_text.count(ns_pointer) == 1
        ns_text = ns_text.replace(ns_method, '', 1).replace(ns_pointer, ns_pointer_old, 1)
        ns_owner_prior = ns_text.encode('utf-8')
        assert len(ns_owner_prior) == 69013 and sha(ns_owner_prior) == '5af90686a31c4c719fedade39cef9278f0bb05370d7a17964d8f53f515006aba'
        ns_header_rel = 'src/core/hle/service/ns/application_manager_interface.h'
        ns_header_latest = (ACTIVE / ns_header_rel).read_bytes()
        assert len(ns_header_latest) == 7313 and sha(ns_header_latest) == '450200ef9e54f2f7989f46960055e4591d00c4ca5a870b7141d2bb1f69163908'
        assert spec['entries'][ns_header_rel]['active'] == sha(ns_header_latest)
        ns_signature = '    Result GetRunningApplicationProgramId(Out<u64> out_program_id);\n'
        assert ns_header_latest.decode('utf-8').count(ns_signature) == 1
        ns_header_prior = ns_header_latest.decode('utf-8').replace(ns_signature, '', 1).encode('utf-8')
        assert len(ns_header_prior) == 7245 and sha(ns_header_prior) == '01e6fac84b59172c95c1d59b82cf3809f46be6229951d3e53585a85f14e9c7e0'
        assert ns_header_prior == (stage / ns_header_rel).read_bytes(), 'NS native header source mismatch'
        observed[ns_header_rel] = spec['entries'][ns_header_rel]
        print('NS1_NS_RUNNING_PROGRAMID_EXACT_REVERSE_PASS',
              'real_applet_identity=1', 'fake_cpp_implementation_receipt_fixed=1',
              'application_view_deprecated_bound=1')

        # NS1 rights-environment system services lack a PS5 entitlement
        # manager. Fail closed using the existing NS error handler. Reverse
        # exactly these fourteen pointer bindings against the shipping owner.
        ns_rel = 'src/core/hle/service/ns/application_manager_interface.cpp'
        ns_active = ns_owner_prior
        ns_previous = (stage / ns_rel).read_bytes()
        assert len(ns_previous) == 68229 and sha(ns_previous) == '48f61cb0d94e9b7f850a0b7baf2c33699ab8211fba9335d15fe0939f63fd03e6'
        assert len(ns_active) == 69013 and sha(ns_active) == '5af90686a31c4c719fedade39cef9278f0bb05370d7a17964d8f53f515006aba'
        assert spec['entries'][ns_rel]['active'] == sha(ns_latest)
        import re
        ns_ids = [2150,2151,2152,2153,2154,2155,2160,2161,2170,2171,2180,2181,2182,2190]
        ns_lines = ns_active.decode('utf-8').splitlines(keepends=True)
        ns_found = []
        for i, line in enumerate(ns_lines):
            match = re.match(r'^\s*\{\s*(\d+),\s*&IApplicationManagerInterface::RejectUnavailablePlatformCommand,', line)
            if match and int(match.group(1)) in ns_ids:
                assert int(match.group(1)) not in ns_found
                ns_lines[i] = line.replace(
                    '&IApplicationManagerInterface::RejectUnavailablePlatformCommand',
                    'nullptr', 1)
                ns_found.append(int(match.group(1)))
        assert sorted(ns_found) == sorted(ns_ids)
        assert ''.join(ns_lines).encode('utf-8') == ns_previous, 'NS rights owner exact reverse mismatch'
        observed[ns_rel] = spec['entries'][ns_rel]
        print('NS1_NS_RIGHTS_ENVIRONMENT_EXACT_REVERSE_PASS',
              'closed=14', 'current_fw=23', 'pinned_source_unchanged')




        # HOS 13+: ndrm:lu/ndrm:la are registered by this ES translation
        # unit but ABSENT from the legacy 4853 catalog. Reverse their full
        # error-only closure so both physical owners remain provenance-checked.
        ndrm_rel = 'src/core/hle/service/es/es.cpp'
        # Exact reverse of the eight live eTicket first-use query fixes.
        es_newest = (ACTIVE / ndrm_rel).read_bytes()
        assert len(es_newest) == 21899 and sha(es_newest) == '0df4c4ffce351e618d94d767043fffc0032fb579353a26e7613873521523fda6'
        assert spec['entries'][ndrm_rel]['active'] == sha(es_newest)
        es_restored = es_newest.decode('utf-8')
        for family in ('Common', 'Personalized'):
            start = es_restored.index(f'    void List{family}TicketRightsIds(HLERequestContext& ctx) {{')
            end = es_restored.index('\n    void ', start + 10)
            body = es_restored[start:end]
            newer = f'        const auto& tickets = keys.Get{family}Tickets();'
            older = f'        keys.PopulateTickets();\n        const auto tickets = keys.Get{family}Tickets();'
            assert body.count(newer) == 1
            es_restored = es_restored[:start] + body.replace(newer, older, 1) + es_restored[end:]
        for name in ('CountCommonTicket', 'CountPersonalizedTicket',
                     'ListCommonTicketRightsIds', 'ListPersonalizedTicketRightsIds',
                     'GetCommonTicketSize', 'GetPersonalizedTicketSize',
                     'GetCommonTicketData', 'GetPersonalizedTicketData'):
            old = f'    void {name}(HLERequestContext& ctx) {{\n'
            new = old + '        keys.PopulateTickets();\n'
            assert es_restored.count(new) == 1, ('Ticket reader owner drift', name)
            es_restored = es_restored.replace(new, old, 1)
        ndrm_source = es_restored.encode('utf-8')
        assert len(ndrm_source) == 21705 and sha(ndrm_source) == 'cecad076878369841f655d7e36b754ef45a1d6e5454b1b02642f2bdc2ed84d09'
        print('NS1_ES_TICKET_FIRST_USE_EXACT_REVERSE_PASS', 'queries=8')
        ndrm_text = ndrm_source.decode('utf-8')
        ndrm_method = (
            '\nprivate:\n'
            '    // NDRM relies on Nintendo entitlement services, not available to the PS5 guest.\n'
            '    void RejectUnavailableNdrm(HLERequestContext& ctx) {\n'
            '        IPC::ResponseBuilder rb{ctx, 2};\n'
            '        rb.Push(ResultUnknown);\n'
            '    }\n'
        )
        assert ndrm_text.count(ndrm_method) == 2
        ndrm_text = ndrm_text.replace(ndrm_method, '\n')
        for ndrm_class, expected in [('NDRM_LU', 5), ('NDRM_LA', 54)]:
            pointer = '&' + ndrm_class + '::RejectUnavailableNdrm'
            assert ndrm_text.count(pointer) == expected, ('NDRM rejected-slot drift', ndrm_class)
            ndrm_text = ndrm_text.replace(pointer, 'nullptr')
        ndrm_previous = ndrm_text.encode('utf-8')
        assert len(ndrm_previous) == 19829 and sha(ndrm_previous) == 'ce91acfa09973cbdf79303eb44488a9723e88bcec468cd22972da21314fac66e'
        print('NS1_NDRM_EXACT_REVERSE_PASS', 'unindexed=59',
              'owners=ndrm:lu+ndrm:la', 'legacy_pool_not_falsified')

        # Next HOS23 ES successor: restore exactly the preceding eTicket owner
        # and the key-manager parsing owner before historical replay comparison.
        es_rel = 'src/core/hle/service/es/es.cpp'
        es_shipping = ndrm_previous
        assert len(es_shipping) == 19829 and sha(es_shipping) == 'ce91acfa09973cbdf79303eb44488a9723e88bcec468cd22972da21314fac66e'
        assert spec['entries'][es_rel]['active'] == sha(es_newest)
        es_old = es_shipping.decode('utf-8')
        es_new_ticket_methods = "    void CountTicket(HLERequestContext& ctx) {\n        keys.PopulateTickets();\n        const auto count = static_cast<u32>(\n            keys.GetCommonTickets().size() + keys.GetPersonalizedTickets().size());\n        IPC::ResponseBuilder rb{ctx, 3};\n        rb.Push(ResultSuccess);\n        rb.Push<u32>(count);\n    }\n\n    void ListTicketRightsIds(HLERequestContext& ctx) {\n        keys.PopulateTickets();\n        const auto& common = keys.GetCommonTickets();\n        const auto& personalized = keys.GetPersonalizedTickets();\n        std::vector<u128> ids;\n        ids.reserve(common.size() + personalized.size());\n        for (const auto& [rights_id, ticket] : common) {\n            ids.push_back(rights_id);\n        }\n        for (const auto& [rights_id, ticket] : personalized) {\n            ids.push_back(rights_id);\n        }\n        std::sort(ids.begin(), ids.end());\n        const auto count = (std::min)(ids.size(), ctx.GetWriteBufferNumElements<u128>());\n        if (count != 0) {\n            ctx.WriteBuffer(ids.data(), count * sizeof(u128));\n        }\n        IPC::ResponseBuilder rb{ctx, 3};\n        rb.Push(ResultSuccess);\n        rb.Push<u32>(static_cast<u32>(count));\n    }\n\n"
        es_raw_variant_write = "std::visit(\n            [&](const auto& ticket_variant) {\n                using T = std::decay_t<decltype(ticket_variant)>;\n                if constexpr (!std::is_same_v<T, std::monostate>) {\n                    ctx.WriteBuffer(&ticket_variant, write_size);\n                }\n            },\n            ticket.data);"
        def reverse_exact_owner(text, newer, older, expected_count):
            assert text.count(newer) == expected_count, ('Unreviewed successor span', newer[:75])
            return text.replace(newer, older)
        es_old = reverse_exact_owner(es_old,
            es_raw_variant_write, 'ctx.WriteBuffer(&ticket, write_size);', 2)
        es_old = reverse_exact_owner(es_old, "const auto& tickets = keys.GetCommonTickets();\n        const auto ticket_it = tickets.find(rights_id);\n        if (ticket_it == tickets.end() || !ticket_it->second.IsValid()) {\n            IPC::ResponseBuilder rb{ctx, 2};\n            rb.Push(ERROR_INVALID_RIGHTS_ID);\n            return;\n        }\n        const auto& ticket = ticket_it->second;", "const auto ticket = keys.GetCommonTickets().at(rights_id);", 2)
        es_old = reverse_exact_owner(es_old, "const auto& tickets = keys.GetPersonalizedTickets();\n        const auto ticket_it = tickets.find(rights_id);\n        if (ticket_it == tickets.end() || !ticket_it->second.IsValid()) {\n            IPC::ResponseBuilder rb{ctx, 2};\n            rb.Push(ERROR_INVALID_RIGHTS_ID);\n            return;\n        }\n        const auto& ticket = ticket_it->second;", "const auto ticket = keys.GetPersonalizedTickets().at(rights_id);", 2)
        es_old = reverse_exact_owner(es_old,
            es_new_ticket_methods + '    void ListCommonTicketRightsIds',
            '    void ListCommonTicketRightsIds', 1)
        es_old = reverse_exact_owner(es_old,
            'if (!ticket.IsValid() || raw_ticket.size() < ticket.GetSize() ||\n'
            '            !keys.AddTicket(ticket)) {',
            'if (!keys.AddTicket(ticket)) {', 1)
        es_old = reverse_exact_owner(es_old,
            'raw_ticket.size() < sizeof(Core::Crypto::SignatureType)',
            'raw_ticket.size() < sizeof(Core::Crypto::Ticket)', 1)
        es_old = reverse_exact_owner(es_old,
            '{30, &ETicket::CountTicket, "CountTicket"},',
            '{30, nullptr, "CountTicket"},', 1)
        es_old = reverse_exact_owner(es_old,
            '{31, &ETicket::ListTicketRightsIds, "ListTicketRightsIds"},',
            '{31, nullptr, "ListTicketRightsIds"},', 1)
        es_old = reverse_exact_owner(es_old,
            '#include <algorithm>\n#include <type_traits>\n#include <variant>\n'
            '#include <vector>\n\n#include "core/crypto/key_manager.h"',
            '#include "core/crypto/key_manager.h"', 1)
        es_previous_active = es_old.encode('utf-8')
        assert len(es_previous_active) == 16737 and sha(es_previous_active) == 'e5bd1ed9088fa00c7e5758aaf5d09142dbe90c440b0104259005b7b281d042ff'

        key_rel = 'src/core/crypto/key_manager.cpp'
        key_latest = (ACTIVE / key_rel).read_bytes()
        assert len(key_latest) == 47847 and sha(key_latest) == 'fe6a5a0077dc71cfc5ef31c3d1768a4c79c0cd3b3253ede9d609bbbb027137f8'
        assert spec['entries'][key_rel]['active'] == sha(key_latest)
        key_restored = key_latest.decode('utf-8')
        raw_ticket_span = '            auto ticket = Ticket::Read(std::span{buffer.data() + offset, sizeof(RSA2048Ticket)});'
        ticket_tail_guard = ('            // A signature near the end of a save does not imply a complete ticket.\n'
                             '            if (buffer.size() - offset < sizeof(RSA2048Ticket)) {\n'
                             '                break;\n'
                             '            }\n')
        assert key_restored.count(ticket_tail_guard + raw_ticket_span) == 1
        key_restored = key_restored.replace(ticket_tail_guard + raw_ticket_span, raw_ticket_span, 1)
        assert key_restored.count('            offset += sizeof(RSA2048Ticket) - 1;') == 1
        key_restored = key_restored.replace('            offset += sizeof(RSA2048Ticket) - 1;',
                                            '            offset += sizeof(RSA2048Ticket);', 1)
        key_active = key_restored.encode('utf-8')
        assert len(key_active) == 47656 and sha(key_active) == '4618f776b9d3e4f857444ed99c09592132f1bce7addce595bfd4baa7fe96426b'
        print('NS1_TICKET_SAVE_BOUNDS_EXACT_REVERSE_PASS', 'bounds=1', 'adjacent=1')
        key_prev = reverse_exact_owner(key_active.decode('utf-8'),
            'std::memcpy(&ticket, raw_data.data(), std::min(raw_data.size(), sizeof(ticket)));',
            'std::memcpy(&ticket, raw_data.data(), sizeof(ticket));', 3).encode('utf-8')
        assert len(key_prev) == 47575 and sha(key_prev) == 'b177b95a6e6c1d2d43004d77478a64695a03d5b983f895ca99427b56e3af9bd8'
        assert key_prev == (stage / key_rel).read_bytes(), 'KeyManager bounded decode not derivable from replay'
        observed[key_rel] = spec['entries'][key_rel]
        print('NS1_ES_TICKET_IO_MEMORY_SAFETY_EXACT_REVERSE_PASS',
              'bounded_import=1', 'safe_lookup=4', 'serialized_variant=2',
              'bounded_crypto_ticket_parse=3', 'real_handlers=2')

        # HOS23 ES: a shipping overlay closes unsupported ticket mutation
        # and prepurchase operations, without changing local ticket/key reads.
        es_rel = 'src/core/hle/service/es/es.cpp'
        es_original = (stage / es_rel).read_bytes()
        es_upstream = (ORIGINAL / es_rel).read_bytes()
        assert es_original == es_upstream
        assert len(es_upstream) == 15733 and sha(es_upstream) == 'fb2386ef1e53f8a5e8ede1f8d11d98c312b205a337ed0350c72210520c8da605'
        es_active = es_previous_active
        assert len(es_active) == 16737 and sha(es_active) == 'e5bd1ed9088fa00c7e5758aaf5d09142dbe90c440b0104259005b7b281d042ff'
        assert es_rel in spec['entries']
        assert spec['entries'][es_rel]['active'] == sha(es_newest)
        assert spec['entries'][es_rel]['upstream'] == sha(es_upstream)
        es_ids = [2,3,5,6,7,13,22,23,24,25,26,27,28,29,32,34,35,39,40]
        es_reviewed_method = (
            '    // Switch eTicket mutation and prepurchase service lacks an authenticated backend.\n'
            '    // Preserve local ticket reads and title-key access on the existing KeyManager.\n'
            '    void RejectUnavailableTicketManagement(HLERequestContext& ctx) {\n'
            '        IPC::ResponseBuilder rb{ctx, 2};\n'
            '        rb.Push(ResultUnknown);\n'
            '    }\n\n'
        )
        es_reversed = es_active.decode('utf-8')
        assert es_reversed.count(es_reviewed_method) == 1
        es_reversed = es_reversed.replace(es_reviewed_method, '', 1)
        for cmd in es_ids:
            pointer = '{' + str(cmd) + ', &ETicket::RejectUnavailableTicketManagement,'
            assert es_reversed.count(pointer) == 1, ('ES exact reverse changed', cmd)
            es_reversed = es_reversed.replace(
                pointer, '{' + str(cmd) + ', nullptr,', 1)
        assert es_reversed.encode('utf-8') == es_upstream, 'ES owner exact reverse mismatch'
        observed[es_rel] = spec['entries'][es_rel]
        print('NS1_ES_TICKET_MANAGEMENT_EXACT_REVERSE_PASS',
              'offline_commands=19', 'upstream_ticket_reads=immutable')


        # WLAN HOS15+: modern service ownership, not a fake coverage gain.
        # Verify exact current byte hash, strip the one approved successor,
        # then demand byte-exact parity with the previous maintained source.
        wlan_rel = 'src/core/hle/service/wlan/wlan.cpp'
        wlan_current = (ACTIVE / wlan_rel).read_bytes()
        assert len(wlan_current) == 18713 and sha(wlan_current) == 'b71e93829ea39fc9ae9eea3d045e78a57d809d72d46c21a6bd10fd7a423cdfee'
        assert spec['entries'][wlan_rel]['active'] == sha(wlan_current)
        wlan_text = wlan_current.decode('utf-8')
        creator_gated = (
            '    if (FirmwareManager::GetFirmwareVersion(system).first.major >= 15) {\n'
            '        server_manager->RegisterNamedService("wlan:p",\n'
            '                                             std::make_shared<IPrivateServiceCreator>(system), 30);\n'
            '        server_manager->RegisterNamedService("wlan:nd",\n'
            '                                             std::make_shared<ISfDriverServiceCreator>(system), 5);\n'
            '    }'
        )
        creator_legacy = (
            '    server_manager->RegisterNamedService("wlan:p", std::make_shared<IPrivateServiceCreator>(system), 30);\n'
            '    server_manager->RegisterNamedService("wlan:nd", std::make_shared<ISfDriverServiceCreator>(system), 5);'
        )
        assert wlan_text.count(creator_gated) == 1
        wlan_text = wlan_text.replace(creator_gated, creator_legacy, 1)
        creator_method = (
            '\nprivate:\n'
            '    void RejectUnavailableCreator(HLERequestContext& ctx) {\n'
            '        IPC::ResponseBuilder rb{ctx, 2};\n'
            '        rb.Push(ResultUnknown);\n'
            '    }\n'
        )
        for cls, count in (('IPrivateServiceCreator', 2), ('ISfDriverServiceCreator', 1)):
            pointer = '&' + cls + '::RejectUnavailableCreator'
            assert wlan_text.count(pointer) == count, ('WLAN creator pointer drift', cls)
            wlan_text = wlan_text.replace(pointer, 'nullptr')
        assert wlan_text.count(creator_method) == 2
        wlan_text = wlan_text.replace(creator_method, '')
        wlan_creator_prev = wlan_text.encode('utf-8')
        assert len(wlan_creator_prev) == 18111 and sha(wlan_creator_prev) == '46fe01d4bb77e8a72f2c9d61972b0437684dcc29050983db3a31499fc64ebfbe'
        wlan_current_registers = "    // Horizon 15 replaced the six legacy WLAN endpoints with \"wlan\".\n    if (FirmwareManager::GetFirmwareVersion(system).first.major >= 15) {\n        server_manager->RegisterNamedService(\n            \"wlan\", std::make_shared<IGeneralServiceCreator>(system), 10);\n    } else {\n        server_manager->RegisterNamedService(\"wlan:lcl\", std::make_shared<ILocalManager>(system), 10);\n        server_manager->RegisterNamedService(\"wlan:lg\", std::make_shared<ILocalGetFrame>(system), 10);\n        server_manager->RegisterNamedService(\"wlan:lga\", std::make_shared<ILocalGetActionFrame>(system), 10);\n        server_manager->RegisterNamedService(\"wlan:sg\", std::make_shared<ISocketGetFrame>(system), 10);\n        server_manager->RegisterNamedService(\"wlan:soc\", std::make_shared<ISocketManager>(system), 10);\n        server_manager->RegisterNamedService(\"wlan:dtc\", std::make_shared<IDetectManager>(system), 4);\n    }"
        wlan_legacy_registers = "    server_manager->RegisterNamedService(\"wlan:lcl\", std::make_shared<ILocalManager>(system), 10);\n    server_manager->RegisterNamedService(\"wlan:lg\", std::make_shared<ILocalGetFrame>(system), 10);\n    server_manager->RegisterNamedService(\"wlan:lga\", std::make_shared<ILocalGetActionFrame>(system), 10);\n    server_manager->RegisterNamedService(\"wlan:sg\", std::make_shared<ISocketGetFrame>(system), 10);\n    server_manager->RegisterNamedService(\"wlan:soc\", std::make_shared<ISocketManager>(system), 10);\n    server_manager->RegisterNamedService(\"wlan:dtc\", std::make_shared<IDetectManager>(system), 4);"
        assert wlan_text.count(wlan_current_registers) == 1
        wlan_text = wlan_text.replace(wlan_current_registers, wlan_legacy_registers, 1)
        wlan_class_prefix = '\nclass IWirelessCommunicationService final : public ServiceFramework<IWirelessCommunicationService> {'
        wlan_loop = 'void LoopProcess(Core::System& system) {'
        assert wlan_text.count(wlan_class_prefix) == 1
        wlan_a = wlan_text.index(wlan_class_prefix)
        wlan_b = wlan_text.index(wlan_loop, wlan_a)
        wlan_new_classes = wlan_text[wlan_a:wlan_b]
        assert wlan_new_classes.count('class IGeneralServiceCreator final') == 1
        assert wlan_new_classes.count('RegisterHandlers(functions);') == 2
        assert wlan_new_classes.count('RejectUnavailableRadio') == 62
        wlan_text = wlan_text[:wlan_a] + wlan_text[wlan_b:]
        assert wlan_text.count('#include "frontend_common/firmware_manager.h"\n') == 1
        wlan_text = wlan_text.replace('#include "frontend_common/firmware_manager.h"\n', '', 1)
        wlan_prev = wlan_text.encode('utf-8')
        assert len(wlan_prev) == 10653 and sha(wlan_prev) == 'df1a2a35a3cfa6e6925cebf38df42c17114668277eb84f52a573593d1b658b37'
        assert wlan_prev == (stage / wlan_rel).read_bytes(), 'WLAN firmware owner reverse mismatch'
        observed[wlan_rel] = spec['entries'][wlan_rel]
        print('NS1_WLAN_HOS15_NATIVE_SERVICE_EXACT_REVERSE_PASS',
              'new_service=wlan', 'modern_dispatch=61',
              'legacy_ports_retired=6', 'legacy_source_preserved=144')


        # NS1 OLSC online backup/repair paths: preserve existing local
        # transfer/event interfaces and prove 100 explicit errors reverse
        # to the unchanged pinned Eden sources (six shipping overlays).
        olsc_review = [{"stem":"olsc_service_for_system_service","cls":"IOlscServiceForSystemService","total":55,"cpp":[6394,"8559d301b3754dd3501a25edcbaef81c0fac076785a7aeaa8a6005a28e08945c",9601,"9f9df2f68ea4d09f92f1dce9f1fce1751ce7ad6ad9ddf83488edcbe3910feac3"],"h":[1736,"73e3339dfce8c8c0040b0a15aadf9f8d492f4556ac0685356a226bba20653222",1800,"49dcf923894dde7eead1a5e69ab73d4d65eae3560c886aa16bec2bf6b2a88c7b"]},{"stem":"remote_storage_controller","cls":"IRemoteStorageController","total":26,"cpp":[3476,"5fa3abd9dbebf13c56f7029111289b7f7c23b335f11f4d7738d8de567f43ac91",5038,"8a2aefc2418aa22ceb2739b668eb14387ec8827fd323ddb5595b44cf5de6b71b"],"h":[898,"2900c4246f1f035304c426f8daf7dc9a9776acd0703864d4a7866b47364fefe2",962,"c527516fe2652bf38681c2a0a8c74e5a0e232cd3d2e75fe7d53a1df615b43007"]},{"stem":"olsc_service_for_application","cls":"IOlscServiceForApplication","total":19,"cpp":[2900,"851c3ddf254b7468a9bdce025b9767bb1082d8a807876e0c0788a00fd5130667",4159,"492bcad65f8ee6c531ccf4d0bdd7e4b8a75f1be88887f63cc91121dcb3cdeb51"],"h":[866,"c7967190b4067f71d434d71bead934694226403931002ae71ace67ffd1cbc86d",930,"adba6f6793229d9f20d42cb6ff42ea50c430842cc26cbe8ca6f86fd50c1e5815"]}]
        for checked in olsc_review:
            cls = checked['cls']
            for suffix, bounds in [('cpp', checked['cpp']), ('h', checked['h'])]:
                rel = 'src/core/hle/service/olsc/' + checked['stem'] + '.' + suffix
                active_source = (ACTIVE / rel).read_bytes()
                before_size, before_hash, after_size, after_hash = bounds
                assert len(active_source) == after_size and sha(active_source) == after_hash
                assert spec['entries'][rel]['active'] == after_hash
                assert spec['entries'][rel]['upstream'] == before_hash
                assert spec['entries'][rel]['bytes'] == after_size
                prior = active_source.decode('utf-8')
                if suffix == 'cpp':
                    method = (
                        'void ' + cls + '::RejectUnavailableCloudBackend(HLERequestContext& ctx) {\n'
                        '    // OLSC backup/transfer operations require Nintendo cloud authorization and storage.\n'
                        '    IPC::ResponseBuilder rb{ctx, 2};\n'
                        '    rb.Push(ResultUnknown);\n'
                        '}\n\n'
                    )
                    ptr = '&' + cls + '::RejectUnavailableCloudBackend'
                    assert prior.count(ptr) == checked['total'], (rel, 'unreviewed cloud reject count')
                    assert prior.count(method) == 1, (rel, 'unreviewed cloud method')
                    prior = prior.replace(ptr, 'nullptr').replace(method, '', 1)
                    inc = '#include "core/hle/service/cmif_serialization.h"\n#include "core/hle/service/ipc_helpers.h"\n'
                    assert prior.count(inc) == 1
                    prior = prior.replace(inc, '#include "core/hle/service/cmif_serialization.h"\n', 1)
                else:
                    signature = '    void RejectUnavailableCloudBackend(HLERequestContext& ctx);\n'
                    assert prior.count(signature) == 1
                    prior = prior.replace(signature, '', 1)
                assert len(prior.encode('utf-8')) == before_size
                assert sha(prior.encode('utf-8')) == before_hash
                assert prior.encode('utf-8') == (stage / rel).read_bytes(), (
                    'OLSC native owner reverse mismatch', rel)
                observed[rel] = spec['entries'][rel]
        print('NS1_OLSC_CLOUD_BACKEND_EXACT_REVERSE_PASS',
              'physical_closed=100', 'native_overlays=6',
              'local_handlers=untouched', 'pinned_upstream=immutable')




        # HOS23 migrations expose mig:usr, not the unregistered mig:user.
        # Reverse the service name first, then the legacy 36-slot closure.
        mig_rel = 'src/core/hle/service/mig/mig.cpp'
        mig_latest = (ACTIVE / mig_rel).read_bytes()
        assert len(mig_latest) == 4474 and sha(mig_latest) == '95a32643a3c4cad5036a467b10a09274f1508ecd3e7eddfe06d69ea86312aa88'
        assert spec['entries'][mig_rel]['active'] == sha(mig_latest)
        mig_correct = 'server_manager->RegisterNamedService("mig:usr", std::make_shared<MIG_USR>(system));'
        mig_wrong = 'server_manager->RegisterNamedService("mig:user", std::make_shared<MIG_USR>(system));'
        mig_text = mig_latest.decode('utf-8')
        assert mig_text.count(mig_correct) == 1 and mig_text.count(mig_wrong) == 0
        mig_previous = mig_text.replace(mig_correct, mig_wrong, 1).encode('utf-8')
        assert len(mig_previous) == 4475 and sha(mig_previous) == 'b53691cfaa0184daf17dd82987bf94fac66b2a0c1000ddb32529496fa7e35763'
        print('NS1_MIG_SERVICE_NAME_EXACT_REVERSE_PASS', 'modern_ns1=mig:usr',
              'phantom_service=mig:user', 'cloud_backend=unsupported')

        # NS1 migration, Switch PCIe and dynamic rights are native owners,
        # but lack corresponding PS5 backend devices or Nintendo services.
        # Prove every pointer and method mutation reverses to pinned bytes.
        unsupported_sources = [{"rel":"src/core/hle/service/mig/mig.cpp","old":[3091,"5387c8803d0ba6de4cebff8ca332bda476f48812c8b6c6e47091bd09ffd3fff6"],"new":[4475,"b53691cfaa0184daf17dd82987bf94fac66b2a0c1000ddb32529496fa7e35763"],"classes":[["MIG_USR",36]],"include":"service/service.h"},{"rel":"src/core/hle/service/pcie/pcie.cpp","old":[3102,"d7ad1a55a92e91b5e28fc62e7b7f64a9195532b0d80544661078057eb79107ec"],"new":[4550,"78592f53eaee50b23dc63648a8b8d9057524d9c969ee5a8f1d3da540f572afe4"],"classes":[["ISession",24],["PCIE",2],["PCIE_LOG",2]],"include":"service/service.h"},{"rel":"src/core/hle/service/ns/dynamic_rights_interface.cpp","old":[3617,"39d255c2a905b49aa78830470901d32f3edcd348d449867dc507b55e852dd132"],"new":[5039,"241b1a5060032e58e33579b3d5bf23abc9929ec92393d168b9a9b1352a0cea0a"],"classes":[["IDynamicRightsInterface",25]],"include":"cmif_serialization.h"},{"rel":"src/core/hle/service/ns/dynamic_rights_interface.h","old":[855,"42c21b40cb4264eecacc570d8cf8413b25ffd6f56bf2b1303d4d12d73aba78c7"],"new":[920,"60a4afe05c0425fb13e620b77be80adb6be491755dc0358391a7af812135d19f"],"classes":[]}]
        inline_method = (
            '\nprivate:\n'
            '    void RejectUnavailableSwitchBackend(HLERequestContext& ctx) {\n'
            '        IPC::ResponseBuilder rb{ctx, 2};\n'
            '        rb.Push(ResultUnknown);\n'
            '    }\n'
        )
        for doc in unsupported_sources:
            rel = doc['rel']
            active = mig_previous if rel == mig_rel else (ACTIVE / rel).read_bytes()
            before_size, before_sha = doc['old']
            after_size, after_sha = doc['new']
            assert len(active) == after_size and sha(active) == after_sha
            assert spec['entries'][rel]['active'] == (
                sha(mig_latest) if rel == mig_rel else after_sha)
            assert spec['entries'][rel]['upstream'] == before_sha
            assert spec['entries'][rel]['bytes'] == after_size
            reversed_owner = active.decode('utf-8')
            if rel.endswith('.h'):
                declaration = '    void RejectUnavailableSwitchBackend(HLERequestContext& ctx);\n'
                assert reversed_owner.count(declaration) == 1
                reversed_owner = reversed_owner.replace(declaration, '', 1)
            else:
                if doc['rel'].endswith('dynamic_rights_interface.cpp'):
                    method = (
                        'void IDynamicRightsInterface::RejectUnavailableSwitchBackend(HLERequestContext& ctx) {\n'
                        '    IPC::ResponseBuilder rb{ctx, 2};\n'
                        '    rb.Push(ResultUnknown);\n'
                        '}\n\n'
                    )
                    assert reversed_owner.count(method) == 1
                    reversed_owner = reversed_owner.replace(method, '', 1)
                else:
                    assert reversed_owner.count(inline_method) == len(doc['classes'])
                    reversed_owner = reversed_owner.replace(inline_method, '\n')
                for cls, n in doc['classes']:
                    ptr = '&' + cls + '::RejectUnavailableSwitchBackend'
                    assert reversed_owner.count(ptr) == n, ('Unreviewed native failure path', cls)
                    reversed_owner = reversed_owner.replace(ptr, 'nullptr')
                include_before = '#include "core/hle/service/' + doc['include'] + '"\n'
                include_after = include_before + '#include "core/hle/service/ipc_helpers.h"\n'
                assert reversed_owner.count(include_after) == 1
                reversed_owner = reversed_owner.replace(include_after, include_before, 1)
            previous = reversed_owner.encode('utf-8')
            assert len(previous) == before_size and sha(previous) == before_sha
            assert previous == (stage / rel).read_bytes(), 'Unsupported Switch backend replay owner changed'
            observed[rel] = spec['entries'][rel]
        print('NS1_MIG_PCIE_DYNAMIC_RIGHTS_EXACT_REVERSE_PASS',
              'physical_fail_closed=89', 'native_overlays=4',
              'firmware_specific_backends_not_faked=true')


        # OMM/SPSM share real guest dock mode with AM; unsupported power
        # transitions must return an error, never manipulate the host PS5.
        omm_owners = [
            ('operation_mode_manager.cpp', 2055, '608d4d783dfce7c7a1e6b1ccc4f903acb686eb18070e9efb42a55af379372b93',
             4497, '105f9ab1292bec4a49a6b477fbcd907f3c9fd716904b043a87f1811564e1608b'),
            ('operation_mode_manager.h', 446, '1443851d46bdc6559852b2988fa8c651975119ffff2d60ede4f3d7cd55824f2f',
             679, 'b5fd33cc7be4a210bed4e3d0bd027d6a34489405c89f8d9ed5e07faaff17204d'),
            ('power_state_interface.cpp', 1112, '8a8f647a8650614ad51494a6b83e642c2b12b347adc7e80fcb5d642da62a2876',
             1999, 'd51935cfe62c9d956778d3ab6b30ba0660ec12cf7d56da2f07178a1ea59bd528'),
            ('power_state_interface.h', 442, '650897d9c03aedb21a713aa50e91cf51218bc2378b7e6923fd8532f042a4803c',
             516, '557a3c3b7341880d7893bedbaefe8b84ffe8a0ae14937f8b2b6b1725ccd3621b'),
        ]
        omm_cmake = (ACTIVE / 'src/core/CMakeLists.txt').read_text()
        for name, before_bytes, before_hash, after_bytes, after_hash in omm_owners:
            rel = 'src/core/hle/service/omm/' + name
            before = (stage / rel).read_bytes()
            upstream = (ORIGINAL / rel).read_bytes()
            current = (ACTIVE / rel).read_bytes()
            assert before == upstream and len(before) == before_bytes and sha(before) == before_hash, rel
            assert len(current) == after_bytes and sha(current) == after_hash, rel
            assert spec['entries'][rel] == {
                'active': after_hash, 'bytes': after_bytes, 'upstream': before_hash
            }, rel
            if name.endswith('.cpp'):
                assert omm_cmake.count('hle/service/omm/' + name) == 1, rel
            observed[rel] = spec['entries'][rel]
        omm_live = (ACTIVE / 'src/core/hle/service/omm/operation_mode_manager.cpp').read_text()
        spsm_live = (ACTIVE / 'src/core/hle/service/omm/power_state_interface.cpp').read_text()
        for name in ('GetOperationMode', 'GetCradleStatus', 'GetDefaultDisplayResolution'):
            assert omm_live.count('&IOperationModeManager::' + name) == 1, name
        assert omm_live.count('&IOperationModeManager::RejectUnavailableHardware') == 26
        assert spsm_live.count('&IPowerStateInterface::RejectUnavailablePowerControl') == 12
        assert omm_live.count('Settings::IsDockedMode()') == 3
        assert 'VI::DisplayResolution::DockedWidth' in omm_live
        assert 'VI::DisplayResolution::UndockedHeight' in omm_live
        print('NS1_OMM_SPSM_NATIVE_OWNER_PASS', 'real_docked_queries=3',
              'unsupported_power_commands=38', 'selected_cpp=2', 'no_host_power=1')


        # PCV, PSC/HSHL and audrec have no PS5 guest hardware backend.
        # Reconstruct the frozen Eden files from the four shipping overlays.
        # Both immutable SHA256 receipts and the exact inverse are required.
        unsupported_hw = [
            ('src/core/hle/service/pcv/pcv.cpp', 11296, '80648faaf1103f71df863a9f29107aa24e3b6efb5dd386771ae1092cc5934090', 13864, 'c2fda0b5766f25f242fa2e1bd242ece41271610d9e441e852bd3447a092e3714'),
            ('src/core/hle/service/psc/psc.cpp', 5106, 'bdf44cd651a7b6eaa0e273959fa15314514fed0e3763601649462349ef18fd96', 7924, '5cb40750e568b2fd35feb11ef29dddae7d9ffcfd178d73fc8d6106f3eaf9eba4'),
            ('src/core/hle/service/audio/final_output_recorder_manager.cpp', 1620, '9a800607a59ea78ab3c33e0c147855973edab8155555402318e287f0533ebffd', 2780, '0ba9b25d81b4f723445e257b0430709a417a7615537a6376faea60615bb8cce3'),
            ('src/core/hle/service/audio/final_output_recorder_manager.h', 474, '9987c004a6c9f3973b3ac139be7783b5c2188ce7104ed209c7bb90d87103b9eb', 542, '154a4bae6d4d5f65af9024ead1ac41cab106ee368aea7c2149c481b24cd53dcf'),
        ]
        hardware_rejection = (
            '\nprivate:\n'
            '    void RejectUnsupportedDevice(HLERequestContext& ctx) {\n'
            '        // Missing physical Switch power/clock/capture peripheral on the PS5.\n'
            '        // Do not manufacture successful completion for guest requests.\n'
            '        IPC::ResponseBuilder rb{ctx, 2};\n'
            '        rb.Push(ResultUnknown);\n'
            '    }\n'
        )
        pcv_old_ports = (
            '    server_manager->RegisterNamedService("pcv", std::make_shared<PCV>(system));\n'
            '    server_manager->RegisterNamedService("pcv:arb", std::make_shared<PCV_ARB>(system));\n'
            '    server_manager->RegisterNamedService("pcv:imm", std::make_shared<PCV_IMM>(system));\n'
            '    server_manager->RegisterNamedService("clkrst", std::make_shared<CLKRST>(system, "clkrst"));\n'
            '    server_manager->RegisterNamedService("clkrst:i", std::make_shared<CLKRST>(system, "clkrst:i"));\n'
            '    server_manager->RegisterNamedService("clkrst:a", std::make_shared<CLKRST_A>(system));'
        )
        pcv_hos8_ports = (
            '    server_manager->RegisterNamedService("pcv", std::make_shared<PCV>(system));\n'
            '    // HOS 8 replaced pcv:arb/imm with clkrst. Keep old ports for old guests.\n'
            '    const auto major = FirmwareManager::GetFirmwareVersion(system).first.major;\n'
            '    if (major < 8) {\n'
            '        server_manager->RegisterNamedService("pcv:arb", std::make_shared<PCV_ARB>(system));\n'
            '        server_manager->RegisterNamedService("pcv:imm", std::make_shared<PCV_IMM>(system));\n'
            '    } else {\n'
            '        server_manager->RegisterNamedService("clkrst", std::make_shared<CLKRST>(system, "clkrst"));\n'
            '        server_manager->RegisterNamedService("clkrst:i", std::make_shared<CLKRST>(system, "clkrst:i"));\n'
            '        server_manager->RegisterNamedService("clkrst:a", std::make_shared<CLKRST_A>(system));\n'
            '    }'
        )
        audio_manager_method = (
            'void IFinalOutputRecorderManager::RejectUnsupportedDevice(HLERequestContext& ctx) {\n'
            '    // No guest final-output recording backend. Playback continues through\n'
            '    // the existing audio rendering path without this optional capture device.\n'
            '    IPC::ResponseBuilder rb{ctx, 2};\n'
            '    rb.Push(ResultUnknown);\n'
            '}\n\n'
        )
        cmake_native = (ACTIVE/'src/core/CMakeLists.txt').read_text()
        for rel, old_bytes, old_hash, new_bytes, new_hash in unsupported_hw:
            original = (stage/rel).read_bytes()
            pristine = (ORIGINAL/rel).read_bytes()
            current = (ACTIVE/rel).read_bytes()
            assert original == pristine and len(original) == old_bytes and sha(original) == old_hash, rel
            assert len(current) == new_bytes and sha(current) == new_hash, rel
            assert spec['entries'][rel] == {
                'active': new_hash, 'bytes': new_bytes, 'upstream': old_hash
            }, rel
            if rel.endswith('.cpp'):
                cmake_owner = rel.removeprefix('src/core/')
                assert cmake_native.count(cmake_owner) == 1, rel
            reversed_cpp = current.decode('utf-8')
            if rel.endswith('/pcv/pcv.cpp'):
                classes = [('PCV',30), ('PCV_ARB',1), ('PCV_IMM',1),
                           ('CLKRST',3), ('CLKRST_A',1)]
                assert reversed_cpp.count(pcv_hos8_ports) == 1
                reversed_cpp = reversed_cpp.replace(pcv_hos8_ports, pcv_old_ports, 1)
                assert reversed_cpp.count('#include "frontend_common/firmware_manager.h"\n') == 1
                reversed_cpp = reversed_cpp.replace('#include "frontend_common/firmware_manager.h"\n', '', 1)
            elif rel.endswith('/psc/psc.cpp'):
                classes = [('PSC_L',5), ('INS_R',2), ('INS_S',1),
                           ('HSHL_SYS',16), ('HSHL_SET',6)]
                for start, stop, cls in ((16,22,'HSHL_SYS'), (6,8,'HSHL_SET')):
                    for n in range(start,stop):
                        line = f'            {{{n}, &{cls}::RejectUnsupportedDevice, "Cmd{n}"}},\n'
                        assert reversed_cpp.count(line) == 1
                        reversed_cpp = reversed_cpp.replace(line,'',1)
                assert reversed_cpp.count('#include "core/hle/service/ipc_helpers.h"\n') == 1
                reversed_cpp = reversed_cpp.replace('#include "core/hle/service/ipc_helpers.h"\n', '', 1)
            elif rel.endswith('/audio/final_output_recorder_manager.cpp'):
                classes = [('IFinalOutputRecorder',12)]
                assert reversed_cpp.count('&IFinalOutputRecorderManager::RejectUnsupportedDevice') == 1
                reversed_cpp = reversed_cpp.replace('&IFinalOutputRecorderManager::RejectUnsupportedDevice', 'nullptr', 1)
                assert reversed_cpp.count(audio_manager_method) == 1
                reversed_cpp = reversed_cpp.replace(audio_manager_method, '', 1)
                assert reversed_cpp.count('#include "core/hle/service/ipc_helpers.h"\n') == 1
                reversed_cpp = reversed_cpp.replace('#include "core/hle/service/ipc_helpers.h"\n', '', 1)
            else:
                classes = []
                declaration = '\nprivate:\n    void RejectUnsupportedDevice(HLERequestContext& ctx);'
                assert reversed_cpp.count(declaration) == 1
                reversed_cpp = reversed_cpp.replace(declaration, '', 1)
            for cls, count in classes:
                pointer = '&'+cls+'::RejectUnsupportedDevice'
                assert reversed_cpp.count(pointer) == count, (rel,cls)
                reversed_cpp = reversed_cpp.replace(pointer,'nullptr')
            assert reversed_cpp.count(hardware_rejection) == len(classes), rel
            reversed_cpp = reversed_cpp.replace(hardware_rejection,'')
            assert reversed_cpp.encode('utf-8') == original, ('NS1 PCV/PSC/audrec exact reverse drift',rel)
            observed[rel] = spec['entries'][rel]
        print('NS1_PCV_PSC_AUDIO_HARDWARE_EXACT_REVERSE_PASS',
              'physical_closed=79', 'hos23_hshl_added=8', 'native_overlays=4',
              'legacy_ports_versioned=1', 'playback_untouched=1')



        # NS1 batch: modern retail/runtime pruning and explicit fail-closed
        # owners for cloud, local-network and unreachable hardware services.
        # Derive every maintained file exactly from the post-backport stage.
        import re
        batch_contracts = {
            'src/core/hle/service/mnpp/mnpp.cpp': (2706, '1c0423d7b471cb4c0fde484bc622637504d8e063b9ce5f0bbfff984ce122d859',
                                                    3558, 'a14e5af5f2162dd500496c3ddfad34913077d4723aa9e7083702593e0bb5b650'),
            'src/core/hle/service/fgm/fgm.cpp': (2503, '8aecb71864066ab38ed1f88b67a34d56e86237c917ce21b33c3eeda48fbdf37d',
                                                  2278, 'ed94950adff398bc825051e46386fe0af4c8eeedd7859fc1890bcde7eaee82e4'),
            'src/core/hle/service/ptm/ptm.cpp': (1855, 'ce5f5c76f5b97c70c9635575db979fe8920ad4c6a461eaa0cc3bcba07969be89',
                                                  803, 'a8b2537f5a61ec82d04947a50e5b409762a84af57ea5d7b6e3629c579856181f'),
            'src/core/hle/service/i2c/i2c.cpp': (3499, '56458000c97abab5cc361ee859f8c8fd3c750dc01d260f9d78b5fc8167fd722b',
                                                   3800, '4882be0a73353ad6aaa6a7ac59f9629348ed8834136026e29ff0b404c1a0dfbe'),
            'src/core/hle/service/ldn/sf_service.cpp': (1332, 'e4cb9c9104ddf629c40782cfd0adb759ef3d85404ee053996cafcbef7fc98553',
                                                         2050, '8b94f50318e47db6283faf839366e43c4587a656fb5b8fa8fe75b6741eec945d'),
            'src/core/hle/service/ldn/sf_service.h': (443, 'c63d32507ba049731f6ef3ec56e4d5a7803f8b97c52399ffc875754eeafe8f35',
                                                       512, '18007dd388a2722d2a13f5a5c855a877244c6814b6c6789b139c672ecd671969'),
        }
        cmake_batch = (ACTIVE/'src/core/CMakeLists.txt').read_text()
        for rel, (before_bytes, before_hash, after_bytes, after_hash) in batch_contracts.items():
            before = (stage/rel).read_bytes()
            current = (ACTIVE/rel).read_bytes()
            assert len(before) == before_bytes and sha(before) == before_hash, ('NS1 batch prior drift', rel)
            assert len(current) == after_bytes and sha(current) == after_hash, ('NS1 batch active drift', rel)
            assert spec['entries'][rel] == {
                'active': after_hash, 'bytes': after_bytes, 'upstream': before_hash
            }, ('NS1 batch manifest drift', rel)
            if rel.endswith('.cpp'):
                owner = rel.removeprefix('src/core/')
                assert cmake_batch.count(owner) == 1, ('NS1 batch CMake owner drift', rel)

        def bind_null_class(text, class_name, method_name, expected, end_marker, method_block):
            start = text.index(f'class {class_name} final')
            end = text.index(end_marker, start)
            chunk = text[start:end]
            pattern = re.compile(r'\{(\s*\d+\s*),\s*nullptr,\s*"([^"]+)"')
            count = 0
            def repl(match):
                nonlocal count
                count += 1
                return f'{{{match.group(1)}, &{class_name}::{method_name}, "{match.group(2)}"'
            chunk = pattern.sub(repl, chunk)
            assert count == expected, ('NS1 batch NULL owner drift', class_name, count)
            close = chunk.rfind('\n};')
            assert close >= 0
            chunk = chunk[:close] + method_block + chunk[close:]
            return text[:start] + chunk + text[end:]

        # MNPP: preserve application-side local handlers, reject only system/web
        # Nintendo mission/reporting commands for which Encore has no backend.
        rel = 'src/core/hle/service/mnpp/mnpp.cpp'
        expected = (stage/rel).read_text()
        mnpp_method = (
            '\nprivate:\n'
            '    void RejectUnavailableMissionPlatform(HLERequestContext& ctx) {\n'
            '        // Nintendo mission/reporting backend is not available on PS5.\n'
            '        IPC::ResponseBuilder rb{ctx, 2};\n'
            '        rb.Push(ResultUnknown);\n'
            '    }\n'
        )
        expected = bind_null_class(expected, 'MNPP_SYS', 'RejectUnavailableMissionPlatform',
                                   6, '\nclass MNPP_WEB', mnpp_method)
        expected = bind_null_class(expected, 'MNPP_WEB', 'RejectUnavailableMissionPlatform',
                                   5, '\nvoid LoopProcess', mnpp_method)
        assert expected.encode() == (ACTIVE/rel).read_bytes()
        observed[rel] = spec['entries'][rel]

        # fgm:dbg disappeared long before HOS23; remove the obsolete debugger
        # class and service registration while preserving fgm/fgm:0/fgm:9.
        rel = 'src/core/hle/service/fgm/fgm.cpp'
        expected = (stage/rel).read_text()
        start = expected.index('class FGM_DBG final')
        end = expected.index('\nvoid LoopProcess', start)
        expected = expected[:start] + expected[end:]
        line = '    server_manager->RegisterNamedService("fgm:dbg", std::make_shared<FGM_DBG>(system));\n'
        assert expected.count(line) == 1
        expected = expected.replace(line, '', 1)
        fgm_method = (
            '\nprivate:\n'
            '    void RejectUnavailableClockRequest(HLERequestContext& ctx) {\n'
            '        IPC::ResponseBuilder rb{ctx, 2};\n'
            '        rb.Push(ResultUnknown);\n'
            '    }\n'
        )
        expected = bind_null_class(expected, 'IRequest', 'RejectUnavailableClockRequest',
                                   4, '\nclass FGM final', fgm_method)
        assert expected.encode() == (ACTIVE/rel).read_bytes()
        observed[rel] = spec['entries'][rel]

        # psm:manu and powctl are manufacture/non-retail services.
        rel = 'src/core/hle/service/ptm/ptm.cpp'
        expected = (stage/rel).read_text()
        start = expected.index('class PSM_MANU final')
        end = expected.index('\nvoid LoopProcess', start)
        expected = expected[:start] + expected[end:]
        non_retail = (
            '    if (1 /* not retail */) {\n'
            '        server_manager->RegisterNamedService("psm:manu", std::make_shared<PSM_MANU>(system));\n'
            '        server_manager->RegisterNamedService("powctl", std::make_shared<POWCTL>(system));\n'
            '    }\n'
        )
        assert expected.count(non_retail) == 1
        expected = expected.replace(non_retail, '', 1)
        assert expected.encode() == (ACTIVE/rel).read_bytes()
        observed[rel] = spec['entries'][rel]

        # I2C sessions are already unreachable because all OpenSession variants
        # fail without Switch hardware. Harden the six dormant transaction slots.
        rel = 'src/core/hle/service/i2c/i2c.cpp'
        expected = (stage/rel).read_text()
        i2c_method = (
            '\nprivate:\n'
            '    void RejectUnavailableI2C(HLERequestContext& ctx) {\n'
            '        IPC::ResponseBuilder rb{ctx, 2};\n'
            '        rb.Push(ResultUnknown);\n'
            '    }\n'
        )
        expected = bind_null_class(expected, 'I2CSession', 'RejectUnavailableI2C',
                                   6, '\nenum class I2CDevice', i2c_method)
        assert expected.encode() == (ACTIVE/rel).read_bytes()
        observed[rel] = spec['entries'][rel]

        # LDN SF has no native local-wireless backend on PS5. Keep the service
        # surface deterministic and fail closed instead of unknown dispatch.
        rel = 'src/core/hle/service/ldn/sf_service.cpp'
        expected = (stage/rel).read_text()
        inc = '#include "core/hle/service/ldn/sf_service.h"'
        assert expected.count(inc) == 1
        expected = expected.replace(inc, '#include "core/hle/service/ipc_helpers.h"\n' + inc, 1)
        ldn_pattern = re.compile(r'\{(\s*\d+\s*),\s*nullptr,\s*"([^"]+)"')
        matches = list(ldn_pattern.finditer(expected))
        assert len(matches) == 18
        expected = ldn_pattern.sub(
            lambda m: f'{{{m.group(1)}, &ISfService::RejectUnavailableNetwork, "{m.group(2)}"',
            expected)
        dtor = 'ISfService::~ISfService() = default;'
        ldn_method = (
            'void ISfService::RejectUnavailableNetwork(HLERequestContext& ctx) {\n'
            '    IPC::ResponseBuilder rb{ctx, 2};\n'
            '    rb.Push(ResultUnknown);\n'
            '}\n\n'
        )
        assert expected.count(dtor) == 1
        expected = expected.replace(dtor, ldn_method + dtor, 1)
        assert expected.encode() == (ACTIVE/rel).read_bytes()
        observed[rel] = spec['entries'][rel]

        rel = 'src/core/hle/service/ldn/sf_service.h'
        expected = (stage/rel).read_text()
        old = '    ~ISfService() override;'
        new = old + '\n\nprivate:\n    void RejectUnavailableNetwork(HLERequestContext& ctx);'
        assert expected.count(old) == 1
        expected = expected.replace(old, new, 1)
        assert expected.encode() == (ACTIVE/rel).read_bytes()
        observed[rel] = spec['entries'][rel]

        # NGCT legacy management was part of the pre-21 surface. The previous
        # replay already produces the maintained NGC/STPL owner; derive the
        # HOS21+ ngct:s retirement and nine fail-closed legacy slots from it.
        rel = 'src/core/hle/service/ngc/ngc.cpp'
        prior = (stage/rel).read_bytes()
        assert len(prior) == 10435 and sha(prior) == 'afae15d9fc27afccce5f830aae5e7f040ef70d5135a719e210bdadf35af54bc8'
        current = (ACTIVE/rel).read_bytes()
        assert len(current) == 12012 and sha(current) == 'c1f1ef432dbd348f9fdede30a8b92f465bb6f2f6a6959b4cf011c716e9d1d4f1'
        assert spec['entries'][rel]['active'] == sha(current)
        assert spec['entries'][rel]['bytes'] == len(current)
        expected = prior.decode()
        ngct_method = (
            '\nprivate:\n'
            '    void RejectUnavailableManagementApi(HLERequestContext& ctx) {\n'
            '        IPC::ResponseBuilder rb{ctx, 2};\n'
            '        rb.Push(ResultUnknown);\n'
            '    }\n'
        )
        expected = bind_null_class(expected, 'IServiceWithManagementApi',
                                   'RejectUnavailableManagementApi', 9,
                                   '\nstruct SaveDataHandle', ngct_method)
        old_reg = '    server_manager->RegisterNamedService("ngct:s", std::make_shared<IServiceWithManagementApi>(system), 4);'
        new_reg = (
            '    if (FirmwareManager::GetFirmwareVersion(system).first.major < 21) {\n'
            '        server_manager->RegisterNamedService("ngct:s",\n'
            '                                             std::make_shared<IServiceWithManagementApi>(system), 4);\n'
            '    }'
        )
        assert expected.count(old_reg) == 1
        expected = expected.replace(old_reg, new_reg, 1)
        user_shim_method = (
            '\n    void RejectUnavailableSaveData(HLERequestContext& ctx) {\n'
            '        IPC::ResponseBuilder rb{ctx, 2};\n'
            '        rb.Push(IPC::ResultNotSupported);\n'
            '    }\n'
        )
        expected = bind_null_class(expected, 'IUserShimScopedObject',
                                   'RejectUnavailableSaveData', 5,
                                   '\nclass IUserService', user_shim_method)
        system_shim_method = (
            '\n    void RejectUnavailableSystemShim(HLERequestContext& ctx) {\n'
            '        IPC::ResponseBuilder rb{ctx, 2};\n'
            '        rb.Push(IPC::ResultNotSupported);\n'
            '    }\n'
        )
        expected = bind_null_class(expected, 'ISystemShimScopedObject',
                                   'RejectUnavailableSystemShim', 7,
                                   '\nclass ISystemService', system_shim_method)
        assert expected.encode() == current
        observed[rel] = spec['entries'][rel]

        print('NS1_CLOUD_DEBUG_NETWORK_BATCH_EXACT_REPLAY_PASS',
              'physical_closed=67', 'mnpp=11', 'fgm_dbg_removed=3', 'fgm_request=4',
              'ptm_nonretail_removed=4', 'i2c=6', 'ngct_s=9', 'stpl=12', 'ldn_sf=18')

        # LDN cmd303 ConnectPrivate: reconstruct both user/system CMIF owners and
        # the shared LANDiscovery scan-match backend exactly. Private connect uses
        # already discovered NetworkInfo and never invents a host address.
        ldn_private_contracts = {
            'src/core/hle/service/ldn/lan_discovery.cpp':
                (17814, 'e0dc813cd13fd8a44fd35e8ea61bb3e4ee786a6099da74fbfdffc9134c693235',
                 19554, '91ff5de90476905497fcfafacfaec9c900d6c52d1f2c9b6d43efefd0812d9e25'),
            'src/core/hle/service/ldn/lan_discovery.h':
                (3989, '603829307bb5df88199beb4c98ef6a450cff12e68539dc64313245eaaa99cfe6',
                 4301, 'c905fad3cdf47b92ae41e666ba449ea2e2ee6338db14d5ab5eddace42806047c'),
            'src/core/hle/service/ldn/user_local_communication_service.cpp':
                (13957, '915368e033067a7a5dc9182bf59cf8ce3f7d52d7b061e5679fa605437430928d',
                 14849, '4b3e806c7c25532ee31308eb3dff3236bb346ff1e50e28c4a41af2b2d85f09f8'),
            'src/core/hle/service/ldn/user_local_communication_service.h':
                (3471, 'e30df6060a832c4016e9f7c36a9ccb4b7969133cc9dd564b46d54850e4afe058',
                 3784, 'c61c8a2517cf78ab4f6c49431b8459f37032b5f601912cc3b1e60513fd38a1a8'),
            'src/core/hle/service/ldn/system_local_communication_service.cpp':
                (12209, '09d019e4111e71e6f4d8b7e6f711b66c69b9e8cfcb114c4c4094070236e80c60',
                 13105, 'ea23edb79cd15fc5116ee5134b50f8879778e0ec8525c8bc88f6a6de46e987e3'),
            'src/core/hle/service/ldn/system_local_communication_service.h':
                (3214, 'ab4633368634aaa026497c9157ee9721492abcbe1d5c09a197057ecffcd8542f',
                 3527, 'f2ab513f40a1878b580c0332625a31fb1fecdc5a14ef5dfab50808c8631135a5'),
        }
        ldn_cmake = (ACTIVE/'src/core/CMakeLists.txt').read_text()
        for rel, (before_bytes, before_hash, after_bytes, after_hash) in ldn_private_contracts.items():
            before = (stage/rel).read_bytes()
            current = (ACTIVE/rel).read_bytes()
            assert len(before)==before_bytes and sha(before)==before_hash, ('LDN private prior drift',rel)
            assert len(current)==after_bytes and sha(current)==after_hash, ('LDN private active drift',rel)
            assert spec['entries'][rel] == {
                'active':after_hash, 'bytes':after_bytes, 'upstream':before_hash
            }, ('LDN private manifest drift',rel)
            if rel.endswith('.cpp'):
                assert ldn_cmake.count(rel.removeprefix('src/core/')) == 1, ('LDN private CMake owner drift',rel)

        rel = 'src/core/hle/service/ldn/lan_discovery.h'
        expected = (stage/rel).read_text()
        old = (
            '    Result Connect(const NetworkInfo& network_info_, const UserConfig& user_config,\n'
            '                   u16 local_communication_version);\n'
            '    Result Disconnect();'
        )
        new = (
            '    Result Connect(const NetworkInfo& network_info_, const UserConfig& user_config,\n'
            '                   u16 local_communication_version);\n'
            '    Result ConnectPrivate(const SecurityConfig& security_config,\n'
            '                          const SecurityParameter& security_parameter,\n'
            '                          const UserConfig& user_config, u16 local_communication_version,\n'
            '                          ConnectOption option, const NetworkConfig& network_config);\n'
            '    Result Disconnect();'
        )
        assert expected.count(old)==1
        expected = expected.replace(old,new,1)
        assert expected.encode()==(ACTIVE/rel).read_bytes()
        observed[rel]=spec['entries'][rel]

        rel = 'src/core/hle/service/ldn/lan_discovery.cpp'
        expected = (stage/rel).read_text()
        private_method = (
            'Result LANDiscovery::ConnectPrivate(const SecurityConfig& security_config,\n'
            '                                    const SecurityParameter& security_parameter,\n'
            '                                    const UserConfig& user_config, u16 local_communication_version,\n'
            '                                    ConnectOption option, const NetworkConfig& network_config) {\n'
            '    [[maybe_unused]] const auto connect_option = option;\n'
            '    NetworkInfo matched_network{};\n'
            '    bool found{};\n\n'
            '    {\n'
            '        std::scoped_lock lock{packet_mutex};\n'
            '        for (const auto& [mac_address, info] : scan_results) {\n'
            '            [[maybe_unused]] const auto& scanned_mac = mac_address;\n'
            '            const auto& intent = info.network_id.intent_id;\n'
            '            const bool intent_matches =\n'
            '                intent.local_communication_id == network_config.intent_id.local_communication_id &&\n'
            '                intent.scene_id == network_config.intent_id.scene_id;\n'
            '            const bool session_matches =\n'
            '                info.network_id.session_id == security_parameter.session_id;\n'
            '            const bool security_matches =\n'
            '                info.ldn.security_parameter == security_parameter.data &&\n'
            '                info.ldn.security_mode == security_config.security_mode;\n'
            '            const bool channel_matches =\n'
            '                network_config.channel == WifiChannel::Default ||\n'
            '                info.common.channel == network_config.channel;\n\n'
            '            if (intent_matches && session_matches && security_matches && channel_matches) {\n'
            '                matched_network = info;\n'
            '                found = true;\n'
            '                break;\n'
            '            }\n'
            '        }\n'
            '    }\n\n'
            '    R_UNLESS(found, ResultConnectionFailed);\n'
            '    R_RETURN(Connect(matched_network, user_config, local_communication_version));\n'
            '}\n\n'
        )
        marker='Result LANDiscovery::Disconnect() {\n'
        assert expected.count(marker)==1
        expected=expected.replace(marker,private_method+marker,1)
        assert expected.encode()==(ACTIVE/rel).read_bytes()
        observed[rel]=spec['entries'][rel]

        service_specs = (
            ('user', 'IUserLocalCommunicationService',
             'src/core/hle/service/ldn/user_local_communication_service.cpp',
             'src/core/hle/service/ldn/user_local_communication_service.h'),
            ('system', 'ISystemLocalCommunicationService',
             'src/core/hle/service/ldn/system_local_communication_service.cpp',
             'src/core/hle/service/ldn/system_local_communication_service.h'),
        )
        for label, cls, cpp_rel, header_rel in service_specs:
            expected=(stage/cpp_rel).read_text()
            first_include=expected.index('#include ')
            expected=expected[:first_include]+'#include <limits>\n'+expected[first_include:]
            old='{303, nullptr, "ConnectPrivate"}'
            new=f'{{303, D<&{cls}::ConnectPrivate>, "ConnectPrivate"}}'
            assert expected.count(old)==1
            expected=expected.replace(old,new,1)
            disconnect=f'Result {cls}::Disconnect() {{'
            method=(
                f'Result {cls}::ConnectPrivate(\n'
                '    const SecurityConfig& security_config, const SecurityParameter& security_parameter,\n'
                '    const UserConfig& user_config, s32 local_communication_version, ConnectOption option,\n'
                '    const NetworkConfig& network_config) {\n'
                '    LOG_INFO(Service_LDN,\n'
                '             "called, security_mode={}, local_communication_version={}, channel={}",\n'
                '             security_config.security_mode, local_communication_version, network_config.channel);\n\n'
                '    R_UNLESS(local_communication_version >= 0 &&\n'
                '                 local_communication_version <= std::numeric_limits<u16>::max(),\n'
                '             ResultBadInput);\n'
                '    R_RETURN(lan_discovery.ConnectPrivate(\n'
                '        security_config, security_parameter, user_config,\n'
                '        static_cast<u16>(local_communication_version), option, network_config));\n'
                '}\n\n'
            )
            assert expected.count(disconnect)==1
            expected=expected.replace(disconnect,method+disconnect,1)
            assert expected.encode()==(ACTIVE/cpp_rel).read_bytes(), ('LDN ConnectPrivate cpp reverse mismatch',label)
            observed[cpp_rel]=spec['entries'][cpp_rel]

            expected=(stage/header_rel).read_text()
            old='    Result Disconnect();'
            new=(
                '    Result ConnectPrivate(const SecurityConfig& security_config,\n'
                '                          const SecurityParameter& security_parameter,\n'
                '                          const UserConfig& user_config, s32 local_communication_version,\n'
                '                          ConnectOption option, const NetworkConfig& network_config);\n\n'
                '    Result Disconnect();'
            )
            assert expected.count(old)==1
            expected=expected.replace(old,new,1)
            assert expected.encode()==(ACTIVE/header_rel).read_bytes(), ('LDN ConnectPrivate header reverse mismatch',label)
            observed[header_rel]=spec['entries'][header_rel]

        print('NS1_LDN_CONNECT_PRIVATE_EXACT_REPLAY_PASS',
              'real_handlers=2', 'scan_match=1', 'shared_connect_backend=1',
              'session_intent_security_channel_match=1', 'fabricated_host=0')

        # idle:sys: emulate the absence of an automatic guest power-down
        # policy without touching host PS5 power state. The readable event is real
        # but remains unsignalled while the emulated policy never requests sleep.
        idle_contracts = {
            'src/core/hle/service/omm/policy_manager_system.cpp':
                (878, '49b7fae920c0fdb0ef065c14fb68ebb8d63acad8a6951847340ccd688e1ffb8f',
                 2116, '7a85fc0cb07a316fc581292298a865b37278e94ea7bbf9a1e2af2e03d0300687'),
            'src/core/hle/service/omm/policy_manager_system.h':
                (446, '5c96ae7620d3c051ae804cc1b0e2f0c3d9afdc6bba27ef5f8e53ee3d4b51b028',
                 853, '81098a83a7e4f870e4478908632ac95aadb169e3ba0ceb00a0ef3d94aac8fc77'),
        }
        for rel, (before_bytes, before_hash, after_bytes, after_hash) in idle_contracts.items():
            before=(stage/rel).read_bytes()
            current=(ACTIVE/rel).read_bytes()
            assert len(before)==before_bytes and sha(before)==before_hash, ('idle prior drift',rel)
            assert len(current)==after_bytes and sha(current)==after_hash, ('idle active drift',rel)
            assert spec['entries'][rel] == {
                'active':after_hash, 'bytes':after_bytes, 'upstream':before_hash
            }, ('idle manifest drift',rel)
        idle_cmake=(ACTIVE/'src/core/CMakeLists.txt').read_text()
        assert idle_cmake.count('hle/service/omm/policy_manager_system.cpp')==1

        rel='src/core/hle/service/omm/policy_manager_system.cpp'
        expected=(stage/rel).read_text()
        expected=expected.replace(
            '#include "core/hle/service/omm/policy_manager_system.h"',
            '#include "core/hle/kernel/k_event.h"\n'
            '#include "core/hle/service/ipc_helpers.h"\n'
            '#include "core/hle/service/kernel_helpers.h"\n'
            '#include "core/hle/service/omm/policy_manager_system.h"', 1)
        replacements = (
            ('{0, nullptr, "GetAutoPowerDownEvent"}',
             '{0, &IPolicyManagerSystem::GetAutoPowerDownEvent, "GetAutoPowerDownEvent"}'),
            ('{1, nullptr, "IsAutoPowerDownRequested"}',
             '{1, &IPolicyManagerSystem::IsAutoPowerDownRequested, "IsAutoPowerDownRequested"}'),
            ('{2, nullptr, "Unknown2"}',
             '{2, &IPolicyManagerSystem::RejectUnknownPolicyCommand, "Unknown2"}'),
            ('{3, nullptr, "SetHandlingContext"}',
             '{3, &IPolicyManagerSystem::AcceptPolicyNoop, "SetHandlingContext"}'),
            ('{4, nullptr, "LoadAndApplySettings"}',
             '{4, &IPolicyManagerSystem::AcceptPolicyNoop, "LoadAndApplySettings"}'),
            ('{5, nullptr, "ReportUserIsActive"}',
             '{5, &IPolicyManagerSystem::AcceptPolicyNoop, "ReportUserIsActive"}'),
        )
        for old,new in replacements:
            assert expected.count(old)==1
            expected=expected.replace(old,new,1)
        ctor='    RegisterHandlers(functions);\n}'
        assert expected.count(ctor)==1
        expected=expected.replace(
            ctor,
            '    RegisterHandlers(functions);\n'
            '    auto_power_down_event = service_context.CreateEvent("IPolicyManagerSystem::AutoPowerDownEvent");\n'
            '}', 1)
        old='IPolicyManagerSystem::~IPolicyManagerSystem() = default;'
        methods=(
            'IPolicyManagerSystem::~IPolicyManagerSystem() {\n'
            '    service_context.CloseEvent(auto_power_down_event);\n'
            '}\n\n'
            'void IPolicyManagerSystem::GetAutoPowerDownEvent(HLERequestContext& ctx) {\n'
            '    IPC::ResponseBuilder rb{ctx, 2, 1};\n'
            '    rb.Push(ResultSuccess);\n'
            '    rb.PushCopyObjects(ctx, auto_power_down_event->GetReadableEvent());\n'
            '}\n\n'
            'void IPolicyManagerSystem::IsAutoPowerDownRequested(HLERequestContext& ctx) {\n'
            '    IPC::ResponseBuilder rb{ctx, 3};\n'
            '    rb.Push(ResultSuccess);\n'
            '    rb.Push(false);\n'
            '}\n\n'
            'void IPolicyManagerSystem::AcceptPolicyNoop(HLERequestContext& ctx) {\n'
            "    // Encore does not run Horizon's automatic guest sleep timer. Applying idle\\n"
            '    // settings or reporting guest activity therefore leaves the host PS5 untouched.\n'
            '    IPC::ResponseBuilder rb{ctx, 2};\n'
            '    rb.Push(ResultSuccess);\n'
            '}\n\n'
            'void IPolicyManagerSystem::RejectUnknownPolicyCommand(HLERequestContext& ctx) {\n'
            '    IPC::ResponseBuilder rb{ctx, 2};\n'
            '    rb.Push(ResultUnknown);\n'
            '}'
        )
        assert expected.count(old)==1
        expected=expected.replace(old,methods,1)
        assert expected.encode()==(ACTIVE/rel).read_bytes()
        observed[rel]=spec['entries'][rel]

        rel='src/core/hle/service/omm/policy_manager_system.h'
        expected=(stage/rel).read_text()
        old='#include "core/hle/service/service.h"'
        new='#include "core/hle/service/kernel_helpers.h"\n#include "core/hle/service/service.h"'
        assert expected.count(old)==1
        expected=expected.replace(old,new,1)
        old='    ~IPolicyManagerSystem() override;'
        new=(
            '    ~IPolicyManagerSystem() override;\n\n'
            'private:\n'
            '    void GetAutoPowerDownEvent(HLERequestContext& ctx);\n'
            '    void IsAutoPowerDownRequested(HLERequestContext& ctx);\n'
            '    void AcceptPolicyNoop(HLERequestContext& ctx);\n'
            '    void RejectUnknownPolicyCommand(HLERequestContext& ctx);\n\n'
            '    KernelHelpers::ServiceContext service_context{system, "IPolicyManagerSystem"};\n'
            '    Kernel::KEvent* auto_power_down_event{};'
        )
        assert expected.count(old)==1
        expected=expected.replace(old,new,1)
        assert expected.encode()==(ACTIVE/rel).read_bytes()
        observed[rel]=spec['entries'][rel]
        print('NS1_IDLE_POLICY_NEUTRAL_EXACT_REPLAY_PASS',
              'physical_closed=6', 'real_event=1', 'auto_power_down_requested=false',
              'host_power_untouched=1', 'unknown23_rejected=1')

        # PSM battery charge events: return stable Horizon events and signal the
        # charge-info event only when already-emulated charge policy fields change.
        psm_event_contracts = {
            'src/core/hle/service/ptm/psm.cpp':
                (11776, 'f16c0d350be649221e93c7d76728245f0a84bf0331a5f68359422740c3e98af3',
                 14379, '73ad237a6fdbfde40cf584a10d99265311882d2688c740591d8e31d991a3058f'),
            'src/core/hle/service/ptm/psm.h':
                (1718, '57ba579b672d7757a3708a3696fd77bed64354cf1ea59a9f2b8841ff4f7e80bb',
                 2255, '5d9df80981089a775d4efd6d8fd0f7b573ee9dd6092e5b9e1ccdb0b9f603f302'),
        }
        psm_cmake=(ACTIVE/'src/core/CMakeLists.txt').read_text()
        assert psm_cmake.count('hle/service/ptm/psm.cpp')==1
        for rel, (before_bytes, before_hash, after_bytes, after_hash) in psm_event_contracts.items():
            before=(stage/rel).read_bytes()
            current=(ACTIVE/rel).read_bytes()
            assert len(before)==before_bytes and sha(before)==before_hash, ('PSM event prior drift',rel)
            assert len(current)==after_bytes and sha(current)==after_hash, ('PSM event active drift',rel)
            assert spec['entries'][rel] == {
                'active':after_hash, 'bytes':after_bytes, 'upstream':before_hash
            }, ('PSM event manifest drift',rel)
            observed[rel]=spec['entries'][rel]
        psm_cpp=(ACTIVE/'src/core/hle/service/ptm/psm.cpp').read_text()
        psm_h=(ACTIVE/'src/core/hle/service/ptm/psm.h').read_text()
        assert psm_cpp.count('{16, &PSM::GetBatteryChargeInfoEvent, "GetBatteryChargeInfoEvent"}')==1
        assert psm_cpp.count('{18, &PSM::GetBatteryChargeCalibratedEvent, "GetBatteryChargeCalibratedEvent"}')==1
        assert psm_cpp.count('service_context.CreateEvent("PSM::BatteryChargeInfoEvent")')==1
        assert psm_cpp.count('service_context.CreateEvent("PSM::BatteryChargeCalibratedEvent")')==1
        assert psm_cpp.count('service_context.CloseEvent(battery_charge_info_event)')==1
        assert psm_cpp.count('service_context.CloseEvent(battery_charge_calibrated_event)')==1
        assert psm_cpp.count('SignalBatteryChargeInfoChanged();')==6
        assert psm_cpp.count('battery_charge_info_event->Signal(system.Kernel())')==1
        assert psm_cpp.count('battery_charge_calibrated_event->Signal')==0
        assert psm_h.count('Kernel::KEvent* battery_charge_info_event{};')==1
        assert psm_h.count('Kernel::KEvent* battery_charge_calibrated_event{};')==1
        print('NS1_PSM_BATTERY_EVENTS_EXACT_SOURCE_PASS',
              'real_handlers=2', 'stable_handles=2', 'charge_info_signal_sites=6',
              'calibration_fabricated=0', 'host_power_untouched=1')

        # Low-risk retail/sessionless owners: PREPO local statistics, retail LM
        # no-op extensions and NFC session bookkeeping. Preserve existing data paths.
        low_risk_contracts = {
            'src/core/hle/service/prepo/prepo.cpp':
                (14311, '9fc008ff8edebb5fb661ab6e54905c3e85da73bb4926b0365bf648486e602060',
                 14467, '7b714291320e150a4ff77ddea2bcdd8f89d167e9ebe0efa8b324b1336cb1ad4c'),
            'src/core/hle/service/lm/lm.cpp':
                (13032, 'ae16237f1447fb221c35627528c36c8778c70b7b6159a404bbe8bebaa8199561',
                 13277, '21cc95aa002c2901f72e993ab28bb98e15bdfd282f1e3ae49ca7dd81bd7591f1'),
            'src/core/hle/service/nfc/nfc.cpp':
                (9184, 'c2dbe38ad9c7d4b09b01d37bc667cbaaa757e9f699a7706451dfd298582a68ca',
                 10160, '10725d237d49c6c56bf8c303f46fd2f0087bfbf5b264870a8921e8911af0538b'),
        }
        low_risk_cmake=(ACTIVE/'src/core/CMakeLists.txt').read_text()
        for rel, (before_bytes, before_hash, after_bytes, after_hash) in low_risk_contracts.items():
            before=(stage/rel).read_bytes()
            current=(ACTIVE/rel).read_bytes()
            assert len(before)==before_bytes and sha(before)==before_hash, ('low-risk prior drift',rel)
            assert len(current)==after_bytes and sha(current)==after_hash, ('low-risk active drift',rel)
            assert spec['entries'][rel] == {
                'active':after_hash, 'bytes':after_bytes, 'upstream':before_hash
            }, ('low-risk manifest drift',rel)
            assert low_risk_cmake.count(rel.removeprefix('src/core/'))==1, ('low-risk CMake drift',rel)
            observed[rel]=spec['entries'][rel]

        prepo=(ACTIVE/'src/core/hle/service/prepo/prepo.cpp').read_text()
        assert prepo.count('&PlayReport::GetStatistics')==2
        assert prepo.count('&PlayReport::GetThroughputHistory')==2
        assert prepo.count('&PlayReport::GetLastUploadError')==2
        assert prepo.count('&PlayReport::RejectUnknownModernCommand')==2
        assert prepo.count('nullptr')==0

        lm=(ACTIVE/'src/core/hle/service/lm/lm.cpp').read_text()
        assert lm.count('&ILogger::AcceptRetailNoop')==2
        assert lm.count('&ILogger::Log')==1
        assert lm.count('&ILogger::SetDestination')==1
        assert lm.count('rb.Push(ResultSuccess);')>=1
        assert lm.count('nullptr')==0

        nfc=(ACTIVE/'src/core/hle/service/nfc/nfc.cpp').read_text()
        assert nfc.count('&IUser::AcceptSessionlessPassThrough')==2
        assert nfc.count('&ISystem::AcceptSessionlessPassThrough')==2
        assert nfc.count('&IAm::AcceptAppletLifecycle')==3
        assert nfc.count('&NfcInterface::SendCommandByPassThrough')==2
        assert nfc.count('nullptr')==0
        print('NS1_PREPO_LM_NFC_LOW_RISK_SOURCE_PASS',
              'physical_closed=14', 'prepo_real=3', 'prepo_rejected=2',
              'lm_retail_noop=2', 'nfc_sessionless_noop=7',
              'local_reporting_preserved=1', 'nfc_pass_through_preserved=1')

        # NS1 acceleration batch: preserve existing local backends while
        # replacing unknown dispatch for unsupported cloud/capture/database APIs,
        # and removing the non-retail ncm:v service from the shipping graph.
        acceleration_contracts = {
            'src/core/hle/service/olsc/daemon_controller.cpp':
                (5116, '8b99413c7065bdaf4942d61fe3bab7f94e761ee8a34d35f96f8ec07178436966',
                 5415, 'c348f3a7e34d0959b91421cee009b3f1b3c8dba64f8eb8f6950bb565e2d94ea3',
                 '8b99413c7065bdaf4942d61fe3bab7f94e761ee8a34d35f96f8ec07178436966'),
            'src/core/hle/service/olsc/daemon_controller.h':
                (2578, '73d2ef77ba1b75fc47eada17fc61c8aff768e0c5de5522e843a62f67a3fa262c',
                 2648, '9cc6b393992214c83309c7844ac04a64e9856b124b7f2096961859afe98cd55d',
                 '73d2ef77ba1b75fc47eada17fc61c8aff768e0c5de5522e843a62f67a3fa262c'),
            'src/core/hle/service/olsc/olsc.cpp':
                (1426, 'adcf67ec6f356fca510b32c6743610bcf93c63992fe1819705d6544c3c1e093d',
                 1679, 'f7bd765cae1ed45ac71033aaf0f00b276921335980b6ef26bd5f234123dcbd31',
                 'adcf67ec6f356fca510b32c6743610bcf93c63992fe1819705d6544c3c1e093d'),
            'src/core/hle/service/ncm/ncm.cpp':
                (86771, '136b67a32b2024c4d9512455f4bb041624e2050b511264377470af631cb2d822',
                 86523, 'd415c8e6c70f6751294cb90363175b2243021e554529d2ed02b21bca679e1fef',
                 '136b67a32b2024c4d9512455f4bb041624e2050b511264377470af631cb2d822'),
            'src/core/hle/service/mii/mii.cpp':
                (15496, 'e3d71bc7189d3675e16aa03bc03ea032581249625cbe3c5dc330c86f1e2dacbd',
                 15733, 'e636313feb0b2de5f8e8529f203fd03b2dd45b2346ada86551a1576c4ea09891',
                 '5cefdb565a5abd82233f60875d7a0e93fa5d41f16d21df3a86b3cd73d50b826d'),
            'src/core/hle/service/caps/caps_a.cpp':
                (16414, '2dbc991930f11b5a1b9610466707bc0c98057d4b69ab2cf8bc2945a33fc41709',
                 17390, 'bfa3e3f139b0830270b6502822e4d486b078f8ef2ac7dc891a65f2ad8a6464f2',
                 '87b0ddbd87dfb576b3c3b04132ae4a2b5b4d82b2c47697b894d9e27144614070'),
            'src/core/hle/service/caps/caps_a.h':
                (5512, 'd3e63d69825bec5b2ca29d44b53e45257e62b1732255df3b1260ba041344fb18',
                 5578, 'f88394b90e3d77394cbb406b043e09ffccd6b1009b39d6531edd7d882db3d447',
                 '8cd0a0575d2bc624f0feed26930c4f9378a56f36afb287d1431a6d5ce76c3450'),
            'src/core/hle/service/caps/caps_c.cpp':
                (7549, '8e3d804411b15d512abf536914c4cc52ba81ec63e13900976d0b7024619b3eb6',
                 8323, '9af073dde8ad2513c9cb98dfe125da39ac16d9bb408ff46bd7059f62f6154f3e',
                 '4207c00db15d28949c3299ec36814d35ba77625594a454857bf1c97d4ca6bd95'),
            'src/core/hle/service/caps/caps_c.h':
                (1734, '74f731531f62a7e26e33a09ffd9623b0613f89075cacab1c052e062a0ef96722',
                 1800, '5bc82758389b796d72e896654c4291dc9dfd33b1fa6afa11f6da7fb0d8d7b6fd',
                 '2f6b8e4567725287f959b54928bd74f3516d6a67a404ea48a52d408eafab4d17'),
        }
        accel_cmake=(ACTIVE/'src/core/CMakeLists.txt').read_text()
        for rel,(prior_bytes,prior_hash,after_bytes,after_hash,upstream_hash) in acceleration_contracts.items():
            current=(ACTIVE/rel).read_bytes()
            assert len(current)==after_bytes and sha(current)==after_hash, ('NS1 acceleration active drift',rel)
            assert spec['entries'][rel] == {
                'active':after_hash, 'bytes':after_bytes, 'upstream':upstream_hash
            }, ('NS1 acceleration manifest drift',rel)
            if rel.endswith('.cpp'):
                assert accel_cmake.count(rel.removeprefix('src/core/'))==1, ('NS1 acceleration CMake drift',rel)
            observed[rel]=spec['entries'][rel]

        olsc=(ACTIVE/'src/core/hle/service/olsc/daemon_controller.cpp').read_text()
        assert olsc.count('&IDaemonController::RejectUnsupportedRemoteSaveCommand')==2
        olsc_root=(ACTIVE/'src/core/hle/service/olsc/olsc.cpp').read_text()
        assert olsc_root.count('&ISProfileBgAgentForSystemProcess::RejectUnsupportedBgAgent')==1
        mii=(ACTIVE/'src/core/hle/service/mii/mii.cpp').read_text()
        assert mii.count('&IDatabaseService::RejectUnsupportedImportExport')==2
        ncm=(ACTIVE/'src/core/hle/service/ncm/ncm.cpp').read_text()
        assert 'class NCM_V final' not in ncm and 'RegisterNamedService("ncm:v"' not in ncm
        caps_a=(ACTIVE/'src/core/hle/service/caps/caps_a.cpp').read_text()
        caps_c=(ACTIVE/'src/core/hle/service/caps/caps_c.cpp').read_text()
        assert caps_a.count('&IAlbumAccessorService::RejectUnavailableCaptureCommand')==15
        assert caps_c.count('&IAlbumControlService::RejectUnavailableCaptureCommand')==11
        assert len(re.findall(r'\{\s*\d+\s*,\s*nullptr\s*,', caps_a))==0
        assert len(re.findall(r'\{\s*\d+\s*,\s*nullptr\s*,', caps_c))==0
        print('NS1_ACCELERATION_OLSC_MII_NCM_CAPS_SOURCE_PASS',
              'physical_closed=32', 'olsc=3', 'mii=2', 'ncm_nonretail=1',
              'caps=26', 'local_album_handlers_preserved=1')

        # NS1 hardware/policy acceleration: deterministic fail-closed owners for
        # Switch Bluetooth, fatal-process state and unmodeled APM/PTM/NIFM mutation APIs.
        policy_hw_contracts = {
            'src/core/hle/service/btm/btm_system_core.cpp':
                (8111, '728b136a36cd5abfc0f01365adf4e559dff5e5bd0c00157e841257ce3ec7d0bc',
                 'c6cef4acb0099f4965dd0918c0f6f9b20f52e7442489f89181741e0a43b40492'),
            'src/core/hle/service/btm/btm_system_core.h':
                (2723, '6fc2f8d3dc8324b681406f3cfdd09114c479a0adf87dadd39ec43c035c51c416',
                 'b99cf033f85c185f50509c8966b8f9386a3c0eb9bb06f388e8f090a6caee359e'),
            'src/core/hle/service/btm/btm_user_core.cpp':
                (7158, 'efe9818cdfaf0925ca394dd15803f830c18224a92cb1e44f4932d52d505780ba',
                 'ff77ce3fdd4068e5713a76c3220877d633bc6797d6391baafdf975fa70f5c22b'),
            'src/core/hle/service/btm/btm_user_core.h':
                (2164, '8cba276bbf8d6f237e4d7452368453dccdaceb07a026b01181086c2024d3b3e4',
                 '58ec851477b6999dbc7a9768b6e44c22d792fa9318a05bbd6b31d0f698487e3b'),
            'src/core/hle/service/fatal/fatal_p.cpp':
                (815, '466a2a1f93f7ec64e2cf0143a07421153f5ff65640a9d41d6a3b8d8a317efd69',
                 'faf19671d145f16f26a06aa938d1adbc405839ad168c51882507ad8df4177353'),
            'src/core/hle/service/fatal/fatal_p.h':
                (468, 'a7ff910cb51bb52753cabb60cf86c9c2407fa7553abc105c2936cb3dd5428e06',
                 '4760f1c6d25904b8e6821c645012dd82c0d30778756952919cc29b809b02eb67'),
            'src/core/hle/service/apm/apm_interface.cpp':
                (5844, '252998fe90a169de45a0c5e8c2dfb8d590a6cdf2b27e12958078153bb390947d',
                 'a913465bd636989f8635cff0321568d4510cc82f9ed14ddfcda8f61b0b480819'),
            'src/core/hle/service/apm/apm_interface.h':
                (1130, 'd993aa28169aaa98a4ca58e24ab19655a1a24f09a3552a31d69edf61884a5475',
                 '46a35cb9bf0381ce95529dd9df2932647f0fad3abbff183c318a7eae206d4a3d'),
            'src/core/hle/service/ptm/ts.cpp':
                (3317, 'e3d2e26aa808e9d4d26517cef05bf7aab4fb67c9b79ca34dbb0d2f10e603d4a1',
                 '44fd9b1bf56b212a75afa56a86b732115493033f62c84d518d3c9c176d468a57'),
            'src/core/hle/service/ptm/ts.h':
                (595, 'c49fe8933d6b98b3f9977a325760d8f7b033551a11aa329c60c32d5a533c93c9',
                 '2d94395fdb8a007547c56a4d86095321e48748e77769cfdf471b077d548b7506'),
            'src/core/hle/service/nifm/nifm.cpp':
                (64300, '51e3479cd7ecc087d31a590d01abb66ae395f52208d7eaa727c8659aae1a5a6c',
                 'bef2eaecc5c5a07b217277b691999845b66c3ad8e006ec101881d3218db76a22'),
        }
        policy_hw_cmake=(ACTIVE/'src/core/CMakeLists.txt').read_text()
        for rel,(after_bytes,after_hash,upstream_hash) in policy_hw_contracts.items():
            current=(ACTIVE/rel).read_bytes()
            assert len(current)==after_bytes and sha(current)==after_hash, ('policy/hw active drift',rel)
            assert spec['entries'][rel] == {
                'active':after_hash, 'bytes':after_bytes, 'upstream':upstream_hash
            }, ('policy/hw manifest drift',rel)
            if rel.endswith('.cpp'):
                assert policy_hw_cmake.count(rel.removeprefix('src/core/'))==1, ('policy/hw CMake drift',rel)
            observed[rel]=spec['entries'][rel]

        btm_sys=(ACTIVE/'src/core/hle/service/btm/btm_system_core.cpp').read_text()
        btm_usr=(ACTIVE/'src/core/hle/service/btm/btm_user_core.cpp').read_text()
        fatal_p=(ACTIVE/'src/core/hle/service/fatal/fatal_p.cpp').read_text()
        apm_sys=(ACTIVE/'src/core/hle/service/apm/apm_interface.cpp').read_text()
        ptm_ts=(ACTIVE/'src/core/hle/service/ptm/ts.cpp').read_text()
        nifm=(ACTIVE/'src/core/hle/service/nifm/nifm.cpp').read_text()
        assert btm_sys.count('&IBtmSystemCore::RejectUnsupportedBluetoothAudio')==3
        assert btm_usr.count('&IBtmUserCore::RejectUnsupportedBleOperation')==20
        assert fatal_p.count('&Fatal_P::RejectUnavailableFatalProcessState')==2
        assert apm_sys.count('&APM_Sys::RejectUnsupportedSystemPolicy')==5
        assert ptm_ts.count('::RejectUnsupportedThermalControl')==4
        assert nifm.count('&IRequest::RejectUnsupportedNetworkAccessStatus')==1
        assert nifm.count('&INetworkProfile::RejectUnsupportedProfileMutation')==3
        for name,text_value in (
            ('btm_system',btm_sys),('btm_user',btm_usr),('fatal_p',fatal_p),
            ('apm_sys',apm_sys),('ptm_ts',ptm_ts),
        ):
            assert len(re.findall(r'\{\s*\d+\s*,\s*nullptr\s*,', text_value))==0, name
        assert len(re.findall(r'\{\s*\d+\s*,\s*nullptr\s*,', nifm))==0
        print('NS1_BTM_FATAL_APM_PTM_NIFM_SOURCE_PASS',
              'physical_closed=38', 'btm=23', 'fatal=2', 'apm=5',
              'ptm=4', 'nifm=4', 'host_hardware_untouched=1')

        # Remaining capture/power-control owners: keep implemented screenshot/album
        # paths, but make unsupported JPEG/capture variants and PSC power controls
        # deterministic instead of unknown dispatch.
        caps_psc_contracts = {
            'src/core/hle/service/caps/caps.cpp':
                (2713, '00a8980a3630e0ff3f8ef6ee77cc4e160e38c29563c66e91d2621535375cd4a7',
                 '4354e34b2e05bc9f2ec762e0c08bedd353b3c391d56c7f1d1e217a765f72436f'),
            'src/core/hle/service/caps/caps_ss.cpp':
                (3549, '3d89d1353a18f3382de6b78148f727e5530e66ef47c07b8bde12d148d64dc128',
                 'ceea1a083cfd55a88b49ee4b1b80cb1a9b0b285288681fe053fd4bb9721ed7f5'),
            'src/core/hle/service/caps/caps_ss.h':
                (1580, '6705096697e4dad795a055a6373de9b9e9b1007aaf808f7856cf782bc61de1a5',
                 '92a4704e15d01ade3d379f4e1d339ce7bcf212fc1bdc5d0e56344bd7f9a8e99f'),
            'src/core/hle/service/caps/caps_su.cpp':
                (4664, '181957111129a55e71b332553ece4ec38df16d6f22a1300a65c86bb8bd2bc9e4',
                 'b63555a4fba4a099db970dc910695100c9ac5305a81a07879e92591c26011950'),
            'src/core/hle/service/caps/caps_su.h':
                (2007, '74e17658e4adc9f5299bd7949bbd5fb440dee14cf08fcd30b1e8dd0ee506fa03',
                 'fbda52fb80c49bb513950ef5bb22558432ef9ee93124a748c55923375220e8f6'),
            'src/core/hle/service/caps/caps_u.cpp':
                (10694, '781c5aaf6e34a747f152b2b06a7985e63756f5639b9157b7ab13f665f44ccc7a',
                 '38fbee7328ffedd64a646d9c8ff6cf0daa9995ac14ec28cd54fbf4b136205189'),
            'src/core/hle/service/caps/caps_u.h':
                (4199, '7abdd9083fe5d0df3feebe3167228c01c34e62cd784b815c0b319cb96c05d3e7',
                 '90deaea4f1586080accec3509a9b63a185aa666f6cc6eb969cced2a8d38185f0'),
            'src/core/hle/service/psc/pm_control.cpp':
                (1403, '074785a5522279f4865253db08530e62e709b42bfac85999f5384b849028365d',
                 'b622cc64d4f2daf955dae3f9fdf14eae2223fcf8f7883e00d176037eb6fe4141'),
            'src/core/hle/service/psc/pm_control.h':
                (442, 'fdf1629c6a8d010da0275a53bb67735689ec3ab2f375e49645acc1cdbcc8e6b6',
                 'fdb94bffa979e8356befec107c0a01151c38ba7a5142f4e910cf5e439dde9858'),
            'src/core/hle/service/psc/pm_module.cpp':
                (1106, 'ee35bf86d8b4e0959d6fb905524e1970528e51184e66ea59bd1bc2861850c268',
                 'fa6c3ed863947c5346b1be5a3ee994dde3253471ae97bd6a5cb4e85a4abb79b1'),
            'src/core/hle/service/psc/pm_module.h':
                (437, '2cb2e055fba7f1db8242cd4832216edf91d5b1383e66994dfd8b193c62f63b40',
                 '5b996783d1823e9cefd7b10722f5932ffe6160f058a384b7b1f79213e7316f77'),
        }
        caps_psc_cmake=(ACTIVE/'src/core/CMakeLists.txt').read_text()
        for rel,(after_bytes,after_hash,upstream_hash) in caps_psc_contracts.items():
            current=(ACTIVE/rel).read_bytes()
            assert len(current)==after_bytes and sha(current)==after_hash, ('caps/psc active drift',rel)
            assert spec['entries'][rel] == {
                'active':after_hash, 'bytes':after_bytes, 'upstream':upstream_hash
            }, ('caps/psc manifest drift',rel)
            if rel.endswith('.cpp'):
                assert caps_psc_cmake.count(rel.removeprefix('src/core/'))==1, ('caps/psc CMake drift',rel)
            observed[rel]=spec['entries'][rel]

        caps_root=(ACTIVE/'src/core/hle/service/caps/caps.cpp').read_text()
        caps_ss=(ACTIVE/'src/core/hle/service/caps/caps_ss.cpp').read_text()
        caps_su=(ACTIVE/'src/core/hle/service/caps/caps_su.cpp').read_text()
        caps_u=(ACTIVE/'src/core/hle/service/caps/caps_u.cpp').read_text()
        psc_control=(ACTIVE/'src/core/hle/service/psc/pm_control.cpp').read_text()
        psc_module=(ACTIVE/'src/core/hle/service/psc/pm_module.cpp').read_text()
        assert caps_root.count('&IDecoderControlService::RejectUnavailableJpegControl')==3
        assert caps_ss.count('&IScreenShotService::RejectUnavailableCaptureVariant')==5
        assert caps_su.count('&IScreenShotApplicationService::RejectUnavailableCaptureVariant')==2
        assert caps_u.count('&IAlbumApplicationService::RejectUnavailableAlbumVariant')==2
        assert psc_control.count('&IPmControl::RejectUnavailablePowerControl')==9
        assert psc_module.count('&IPmModule::RejectUnavailablePowerModule')==5
        for name,text_value in (
            ('caps_root',caps_root),('caps_ss',caps_ss),('caps_su',caps_su),
            ('caps_u',caps_u),('psc_control',psc_control),('psc_module',psc_module),
        ):
            assert len(re.findall(r'\{\s*\d+\s*,\s*nullptr\s*,', text_value))==0, name
        print('NS1_CAPS_PSC_REMAINING_SOURCE_PASS',
              'physical_closed=26', 'caps=12', 'psc=14',
              'existing_album_paths_preserved=1', 'host_power_untouched=1')

        # GLUE + SET acceleration: ARP/ECTX unsupported extensions become
        # deterministic; ECTX_W registrar remains functional; SET HOS17+ monaural
        # state is implemented while unmodeled modern settings fail closed.
        glue_set_contracts = {
            'src/core/hle/service/glue/arp.cpp':
                (10368, 'b48a3db4b741a938b1497b296ac5e9272ce0c5470272c37a2eb1f8f4d3696fe9',
                 '21fe3fe2716fc6f34a5cc2908aa561f3a5b8ac594ce68c511f159b492827a043'),
            'src/core/hle/service/glue/arp.h':
                (1222, '9bd338bbf4c03eb2dea34f60ee22b13ea0a0b8c1e573017606623c96ccf34308',
                 '7c264b1e502db1573498743b85fb3bf100b8b8054d7b9f1a2e3b9b0d18e0bf1b'),
            'src/core/hle/service/glue/ectx.cpp':
                (3470, '6fbbb428db5bae1d46a65cfb48fd376f139aba5e536520d54278bea80b2712e2',
                 'eb64936c8a3f2bbeec85e138cfe354a40e8c97941375d5bb4fde22d73a863c59'),
            'src/core/hle/service/glue/ectx.h':
                (1114, 'e2257adfa29d04a8e4b5c45f571d56a65e1c05292d31cc1f180b6d62870f400f',
                 '1e4f227954f4a0b0301158c6be73f9e482217682326c3efc10f6fd942ad14752'),
            'src/core/hle/service/set/system_settings_server.cpp':
                (108310, '7c8a67a55832b3848e29b91b967b3dbf443036ec9a0c426feb96391bbd78976b',
                 '1127251469dd98e57cb475102ea310f6a34e2e64ac3b87ddcef16d0da580f2f2'),
            'src/core/hle/service/set/system_settings_server.h':
                (20188, '80e06a2450be4989f43308c80acbb14c5f6392f8b5f31605de45e3284222125a',
                 '6510e7bc080143ca9468d28b1968597ac599fb8c5fa2ff6e27bc8433aa4b0e55'),
        }
        glue_set_cmake=(ACTIVE/'src/core/CMakeLists.txt').read_text()
        for rel,(after_bytes,after_hash,upstream_hash) in glue_set_contracts.items():
            current=(ACTIVE/rel).read_bytes()
            assert len(current)==after_bytes and sha(current)==after_hash, ('GLUE/SET active drift',rel)
            assert spec['entries'][rel] == {
                'active':after_hash, 'bytes':after_bytes, 'upstream':upstream_hash
            }, ('GLUE/SET manifest drift',rel)
            if rel.endswith('.cpp'):
                assert glue_set_cmake.count(rel.removeprefix('src/core/'))==1, ('GLUE/SET CMake drift',rel)
            observed[rel]=spec['entries'][rel]

        arp=(ACTIVE/'src/core/hle/service/glue/arp.cpp').read_text()
        ectx=(ACTIVE/'src/core/hle/service/glue/ectx.cpp').read_text()
        set_sys=(ACTIVE/'src/core/hle/service/set/system_settings_server.cpp').read_text()
        assert arp.count('&ARP_R::RejectUnsupportedReaderCommand')==6
        assert arp.count('&ARP_W::RejectUnsupportedWriterCommand')==1
        assert ectx.count('&ECTX_W::CreateContextRegistrar')==1
        assert ectx.count('RejectUnsupportedContextCommand')>=9
        assert set_sys.count('C<&ISystemSettingsServer::GetForceMonauralOutputFlag>')==1
        assert set_sys.count('C<&ISystemSettingsServer::SetForceMonauralOutputFlag>')==1
        assert set_sys.count('&ISystemSettingsServer::RejectUnsupportedModernSettingCommand')==13
        for name,text_value in (('arp',arp),('ectx',ectx),('set_sys',set_sys),('notif',notif_cpp)):
            assert len(re.findall(r'\{\s*\d+\s*,\s*nullptr\s*,', text_value))==0, name
        print('NS1_GLUE_SET_ACCELERATION_SOURCE_PASS',
              'physical_closed=41', 'glue=26', 'set=15',
              'real_handlers=ectx_registrar+set_monaural_pair',
              'unsupported_slots=38')

        # PM debug/resource-limit + PSC wake-lock + TMA host-environment batch.
        pm_psc_tma_contracts = {
            'src/core/hle/service/pm/pm.cpp':
                (13340, '7136735f7e157cd353baa126ca85b8a589ba683205151510180487c7c9f3ae73',
                 'e6d2758d23ee1760c07d85fbf6edabd2222fec1c17e813e8809a346a93c94cfd'),
            'src/core/hle/service/psc/time/alarms.cpp':
                (6833, '0053f2f14fc8ac5061aa967f4626a5737c5eeef6b137e5dc606da75c5189e406',
                 '79227ed7e721631f4557bf03b9a3ec7cfbb33939c9a6b202c39ff8cc78b07623'),
            'src/core/hle/service/psc/time/alarms.h':
                (3730, '27e55ca7155ce98142c58b84a4ac07b4f6337026376c3b3f447933b053f8c184',
                 'a1c08e78e6adb0077f3de9ff6687cf6af158f2cd46f4fc72c54fe0e350df665b'),
            'src/core/hle/service/tma/tma.cpp':
                (1519, '41de1e88443d7a9c1fd82c26e5d26e76f9ea4f75f8e70a829f2e8ec20463b351',
                 '2205080fe0a08efd7dcb59796d779933e864a24a30773fc9ebc4dfd982919afc'),
        }
        pm_psc_tma_cmake=(ACTIVE/'src/core/CMakeLists.txt').read_text()
        for rel,(after_bytes,after_hash,upstream_hash) in pm_psc_tma_contracts.items():
            current=(ACTIVE/rel).read_bytes()
            assert len(current)==after_bytes and sha(current)==after_hash, ('PM/PSC/TMA active drift',rel)
            assert spec['entries'][rel] == {
                'active':after_hash, 'bytes':after_bytes, 'upstream':upstream_hash
            }, ('PM/PSC/TMA manifest drift',rel)
            if rel.endswith('.cpp'):
                assert pm_psc_tma_cmake.count(rel.removeprefix('src/core/'))==1, ('PM/PSC/TMA CMake drift',rel)
            observed[rel]=spec['entries'][rel]

        pm_cpp=(ACTIVE/'src/core/hle/service/pm/pm.cpp').read_text()
        psc_alarm=(ACTIVE/'src/core/hle/service/psc/time/alarms.cpp').read_text()
        tma_cpp=(ACTIVE/'src/core/hle/service/tma/tma.cpp').read_text()
        assert pm_cpp.count('&DebugMonitor::RejectUnsupportedDebugControl')==6
        assert pm_cpp.count('&Info::RejectUnsupportedAtmosphereInfo')==2
        assert pm_cpp.count('&Shell::AcceptResourceLimitNoop')==3
        assert len(re.findall(r'\{\s*\d+\s*,\s*nullptr\s*,', pm_cpp))==3
        assert psc_alarm.count('&ISteadyClockAlarm::AcceptWakeLockNoop')==2
        assert len(re.findall(r'\{\s*\d+\s*,\s*nullptr\s*,', psc_alarm))==0
        assert tma_cpp.count('&HTC_TENV::RejectUnavailableHostEnvironment')==1
        assert len(re.findall(r'\{\s*\d+\s*,\s*nullptr\s*,', tma_cpp))==0
        print('NS1_PM_PSC_TMA_ACCELERATION_SOURCE_PASS',
              'physical_closed=14', 'pm=11', 'psc_time=2', 'tma=1',
              'pm_launch_and_process_events_untouched=1')

        # LDN monitoring surfaces are kept separate from the functional
        # LANDiscovery user/system backend. Unsupported monitor-only queries fail
        # closed; NCM path resolvers remain untouched and only memory-report is closed.
        ldn_monitor_contracts = {
            'src/core/hle/service/ldn/monitor_service.cpp':
                (2053, 'a59e09fa47757d5990de1055dbbad835a367ccc3bf7e1164290d89f4db60c477',
                 '4203f4f772df022d31f9b69052aaa28b6483cb60fe0848115efcb51aeaf3786c'),
            'src/core/hle/service/ldn/monitor_service.h':
                (727, '126a124325410fb68c743a4bf65016a670a29612dd6a4e6c58878d2a3f37c8af',
                 '896a9167547d3c66ea986d1dbcff83114117bf2dfcfa50302c0e94c37d934ce5'),
            'src/core/hle/service/ldn/sf_monitor_service.cpp':
                (1557, '3b3481bab7eda307ff5043bc71bd40a820e00496fd49459b2e8a4867e9270795',
                 'e9511dad0b52f9d378ab602dcf9de795b404fff0b145ac9295aa5407b0367402'),
            'src/core/hle/service/ldn/sf_monitor_service.h':
                (700, '7d64b5e3a6469f1ba9cc684d310cb40c9a44f90fb86bf81f15b27006ecfa2e5f',
                 'ae7102777c0784c66f689abccd2d598477b8e29213ea412174127be8b554275c'),
            'src/core/hle/service/ldn/sf_service_monitor.cpp':
                (2512, 'f45bacefdd621e2724ea8a931b456159807708b6d9260222dea394f3f5f5d39d',
                 '1163e5d1b73b93fa54cc27b9f55a5d87b747bd549fada45c34e76b553b9c7fad'),
            'src/core/hle/service/ldn/sf_service_monitor.h':
                (749, '5b6f70d453bb4e2bf7a38ce2077fe2abd9407f3c42caabbde17260f92099ff9b',
                 '3a7517076f5f80fa9bd6e3bdd44aa0d05cc4e9a34206797a533989c71e1b5e73'),
        }
        ldn_monitor_cmake=(ACTIVE/'src/core/CMakeLists.txt').read_text()
        for rel,(after_bytes,after_hash,upstream_hash) in ldn_monitor_contracts.items():
            current=(ACTIVE/rel).read_bytes()
            assert len(current)==after_bytes and sha(current)==after_hash, ('LDN monitor active drift',rel)
            assert spec['entries'][rel] == {
                'active':after_hash, 'bytes':after_bytes, 'upstream':upstream_hash
            }, ('LDN monitor manifest drift',rel)
            if rel.endswith('.cpp'):
                assert ldn_monitor_cmake.count(rel.removeprefix('src/core/'))==1, ('LDN monitor CMake drift',rel)
            observed[rel]=spec['entries'][rel]

        ldn_mon=(ACTIVE/'src/core/hle/service/ldn/monitor_service.cpp').read_text()
        ldn_sf_mon=(ACTIVE/'src/core/hle/service/ldn/sf_monitor_service.cpp').read_text()
        ldn_sf_service_mon=(ACTIVE/'src/core/hle/service/ldn/sf_service_monitor.cpp').read_text()
        ncm_cpp=(ACTIVE/'src/core/hle/service/ncm/ncm.cpp').read_text()
        assert ldn_mon.count('&IMonitorService::RejectUnsupportedMonitorQuery')==5
        assert ldn_sf_mon.count('&ISfMonitorService::RejectUnsupportedSfMonitorQuery')==1
        assert ldn_sf_service_mon.count('&ISfServiceMonitor::RejectUnsupportedSfMonitorQuery')==11
        assert ncm_cpp.count('&NCM::RejectUnavailableMemoryReport')==1
        assert ncm_cpp.count('{4, nullptr, "ResolveDataPath"}')==1
        assert ncm_cpp.count('{0, nullptr, "ResolveAddOnContentPath"}')==1
        for name,text_value in (
            ('ldn_monitor',ldn_mon),('ldn_sf_monitor',ldn_sf_mon),
            ('ldn_sf_service_monitor',ldn_sf_service_mon),
        ):
            assert len(re.findall(r'\{\s*\d+\s*,\s*nullptr\s*,', text_value))==0, name
        print('NS1_LDN_MONITOR_NCM_MEMORY_SOURCE_PASS',
              'physical_closed=18', 'ldn_monitor=17', 'ncm_memory=1',
              'ldn_core_backend_untouched=1', 'ncm_path_resolvers_untouched=1')

        # AOC: retain process-based local DLC Count/List/BaseId/Prepare paths and
        # close only application-id/debug/host/cache extensions without a backend.
        aoc_contracts = {
            'src/core/hle/service/aoc/addon_content_manager.cpp':
                (9681, '3993f73ae8a466ea0a5c3d2be55c85dfaec86d0ea6f70a9ed54bce61dde25818',
                 'b09d37fd974e17f55f6425836d2e7f981755ed005e617d1ebda1f0cbf45edfe9'),
            'src/core/hle/service/aoc/addon_content_manager.h':
                (1812, '77450091cbe4d57b827b2c7f7d10f1d118b58fbb2bcf14c5cec2025286cb32b8',
                 '0bfabeb189026b2ebc9b4c0ad12cff9e919c46b7b67ae2ebeef895cfb8df3b52'),
        }
        aoc_cmake=(ACTIVE/'src/core/CMakeLists.txt').read_text()
        for rel,(after_bytes,after_hash,upstream_hash) in aoc_contracts.items():
            current=(ACTIVE/rel).read_bytes()
            assert len(current)==after_bytes and sha(current)==after_hash, ('AOC active drift',rel)
            assert spec['entries'][rel] == {
                'active':after_hash, 'bytes':after_bytes, 'upstream':upstream_hash
            }, ('AOC manifest drift',rel)
            if rel.endswith('.cpp'):
                assert aoc_cmake.count(rel.removeprefix('src/core/'))==1, ('AOC CMake drift',rel)
            observed[rel]=spec['entries'][rel]

        aoc_cpp=(ACTIVE/'src/core/hle/service/aoc/addon_content_manager.cpp').read_text()
        assert aoc_cpp.count('&IAddOnContentManager::RejectUnsupportedAocExtension')==11
        assert len(re.findall(r'\{\s*\d+\s*,\s*nullptr\s*,', aoc_cpp))==0
        for local_handler in (
            'D<&IAddOnContentManager::CountAddOnContent>',
            'D<&IAddOnContentManager::ListAddOnContent>',
            'D<&IAddOnContentManager::GetAddOnContentBaseId>',
            'D<&IAddOnContentManager::PrepareAddOnContent>',
        ):
            assert aoc_cpp.count(local_handler)>=1, local_handler
        print('NS1_ACC_AOC_SUB1000_SOURCE_PASS',
              'physical_closed=103', 'acc=92', 'aoc=11',
              'acc_fail_closed=91', 'real_local_dlc_preserved=1')

        if observed!=spec['entries']:
            missing=sorted(set(observed)-set(spec['entries']))
            extra=sorted(set(spec['entries'])-set(observed))
            mismatched=sorted(n for n in observed.keys()&spec['entries'].keys() if observed[n]!=spec['entries'][n])
            # A hash alone does not show which reviewed source edit drifted.
            # Keep the parity gate strict and include a bounded textual diff
            # for the FIRST mismatch so a native backport can be repaired at
            # its source instead of copying the generated tree over it.
            import difflib
            sample = ''
            if mismatched:
                name = mismatched[0]
                generated = (stage / name).read_text(errors='replace').splitlines()
                maintained = (ACTIVE / name).read_text(errors='replace').splitlines()
                sample = '\n'.join(list(difflib.unified_diff(
                    maintained, generated, fromfile=f'maintained/{name}',
                    tofile=f'replayed/{name}', lineterm='', n=4))[:100])
            raise RuntimeError(f'Active Eden backports differ from full replay: missing={missing},extra={extra},mismatched={mismatched}\n{sample}')
        receipts={p.name:p.read_text().strip() for p in stage.glob('.encore-backport-*.sha256')}
        if receipts!=spec['shipping_receipts']:raise RuntimeError('Missing or stale patch receipts')
        print(f'EDEN_COMPLETE_PATCH_REPLAY_OK files={len(observed)} receipts={len(receipts)}')

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
