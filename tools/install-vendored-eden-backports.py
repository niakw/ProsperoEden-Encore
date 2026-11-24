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
                'after_sha256':'c42fa4f0c72cb96fcab8be8f5da35de8cf8a8058b8e231ad198c886118335bea',
                'after_bytes':7097,
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
        assert bcat_cpp.count('&IBcatService::RejectUnavailableDeliveryTask')==19
        assert bcat_cpp.count('{20100, nullptr, "RequestSyncDeliveryCacheWithApplicationId"}')==1
        assert bcat_cpp.count('{20101, nullptr, "RequestSyncDeliveryCacheWithApplicationIdAndDirectoryName"}')==1
        assert bcat_cpp.count('D<&IBcatService::RequestSyncDeliveryCache>')==1
        assert bcat_cpp.count('D<&IBcatService::RequestSyncDeliveryCacheWithDirectoryName>')==1
        assert bcat_cpp.count('D<&IBcatService::RegisterSystemApplicationDeliveryTasks>')==1
        print('NS1_BCAT_EXACT_POST_BACKPORT_REPLAY_PASS',
              'successors=2', 'rejected_slots=19', 'sync_slots_left=2',
              'pinned_sources=immutable')

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
                'after_sha256':'cf5b5014ac388fbcb94f5448f9d14a1b1a16ce89eed4fbf93640cb44b451421f',
                'after_bytes':6968,
            },
            'src/core/hle/service/ns/query_service.h': {
                'before_sha256':'c892d6cc75b1b7df5d87bb2f39540096765a0569397a31dc07b71cc2947a3dbd',
                'before_bytes':2326,
                'after_sha256':'259d4b74611d366535dd44bcc2d35b5481629fdb894b8848bee8114eecef19db',
                'after_bytes':2762,
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
        assert pdm_query.count('D<&IQueryService::QueryPlayStatisticsByApplicationId>')==1
        assert pdm_query.count('&IQueryService::RejectUnavailablePlayLogQuery')==6
        assert pdm_query.count('D<&IQueryService::QueryPlayStatisticsByApplicationIdAndUserAccountId>')==1
        print('NS1_PDM_QUERY_EXACT_POST_BACKPORT_REPLAY_PASS',
              'successors=2', 'real_application_stats=1',
              'raw_playlog_rejections=6', 'pinned_sources=immutable')

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
                'after_sha256':'76fa32489de5befb16d0dc141c843fd65e0f5de5a78b287232571b356ad50bd7',
                'after_bytes':12913,
            },
            'src/core/hle/service/glue/notif.h': {
                'before_sha256':'593c6fff73fcbc2b3a27d16d4106dfcea51ea548072b3ec2fc5e5bbc73758d36',
                'before_bytes':5452,
                'after_sha256':'149d671724b9a599ecf3df99223015b1f58095063b3c6d24a345ca8cfa6d2b9d',
                'after_bytes':5627,
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
        print('NS1_NOTIF_ALARM_PARAMETER_REPLAY_PASS',
              'shared_crud=notif_a+notif_s', 'parameter_bytes=preserved')


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
        acc_current = (ACTIVE / acc_rel).read_bytes()
        assert len(acc_current) == 95439 and sha(acc_current) == '71c34670cc93158e954ac7a04b3b52cbe60306aaf5c6948ce50ca2ee663d2595'
        import re
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
        assert spec['entries'][acc_rel]['active'] == sha(acc_current)
        assert spec['entries'][acc_rel]['bytes'] == len(acc_current)
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


        # NS1 rights-environment system services lack a PS5 entitlement
        # manager. Fail closed using the existing NS error handler. Reverse
        # exactly these fourteen pointer bindings against the shipping owner.
        ns_rel = 'src/core/hle/service/ns/application_manager_interface.cpp'
        ns_active = (ACTIVE / ns_rel).read_bytes()
        ns_previous = (stage / ns_rel).read_bytes()
        assert len(ns_previous) == 68229 and sha(ns_previous) == '48f61cb0d94e9b7f850a0b7baf2c33699ab8211fba9335d15fe0939f63fd03e6'
        assert len(ns_active) == 69013 and sha(ns_active) == '5af90686a31c4c719fedade39cef9278f0bb05370d7a17964d8f53f515006aba'
        assert spec['entries'][ns_rel]['active'] == sha(ns_active)
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


        # HOS23 ES: a shipping overlay closes unsupported ticket mutation
        # and prepurchase operations, without changing local ticket/key reads.
        es_rel = 'src/core/hle/service/es/es.cpp'
        es_original = (stage / es_rel).read_bytes()
        es_upstream = (ORIGINAL / es_rel).read_bytes()
        assert es_original == es_upstream
        assert len(es_upstream) == 15733 and sha(es_upstream) == 'fb2386ef1e53f8a5e8ede1f8d11d98c312b205a337ed0350c72210520c8da605'
        es_active = (ACTIVE / es_rel).read_bytes()
        assert len(es_active) == 16737 and sha(es_active) == 'e5bd1ed9088fa00c7e5758aaf5d09142dbe90c440b0104259005b7b281d042ff'
        assert es_rel in spec['entries']
        assert spec['entries'][es_rel]['active'] == sha(es_active)
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
