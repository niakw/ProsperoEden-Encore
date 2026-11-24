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
    for path,contract in meta['entries'].items():
        target=ACTIVE/path
        if sha(target.read_bytes())!=contract['active']:
            raise RuntimeError(f'Vendored patched source hash mismatch: {path}')
        old=ORIGINAL/path
        if (sha(old.read_bytes()) if old.is_file() else None)!=contract['upstream']:
            raise RuntimeError(f'Vendored upstream has changed: {path}')
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
