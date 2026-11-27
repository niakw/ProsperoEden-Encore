#!/usr/bin/env python3
"""P2.7: test real GPU worker destructor drain for every live GPU resource.

The drain is required for ordinary 211 mappings, 111 NVMap handles and
214 dense backing; it is not itself proof of GPU driver completion on PS5.
"""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[2]
OWNER=ROOT/'vendor/encore-active/eden/src/core/hle/service/am/service/gpu_worker.cpp'
source=OWNER.read_text()
method=source.split('IGpuWorker::~IGpuWorker() {',1)[1].split(
    'Result IGpuWorker::HandleSyncRequest(',1)[0]
start='    if (system.IsPoweredOn() && !system.IsShuttingDown() &&'
end='    // A failed native 215/216'
assert method.count(start)==method.count(end)==1
policy=method[method.index(start):method.index(end)]
assert 'catch (...)' in policy and 'm_quarantined_nv_session = true;' in policy
assert 'm_dense_regions.empty()' in policy
assert 'm_mappings.Mappings().empty()' in policy
assert 'm_memory.empty()' in policy
assert 'system.GPU().WaitForIdle();' in policy
assert method.index('WaitForIdle();') < method.index('as->ReleaseNativeSparse4K(')
assert method.index('WaitForIdle();') < method.index('as->UnmapNative4K(')
assert method.index('WaitForIdle();') < method.index('nvmap.FreeHandleIfUnpinned(id)')
# The actual worker destructor must let the final shared GPU AS / process
# registry owner release its resources before closing the worker's last
# KProcess reference. Member destruction after ~IGpuWorker's body is too late.
destructor = source.split('IGpuWorker::~IGpuWorker() {',1)[1].split(
    '\nResult IGpuWorker::BackGpuOnlyRegion(',1)[0]
assert destructor.index('m_shared.reset();') < destructor.index('m_process->Close(kernel);')
assert destructor.index('nvmap.FreeHandleIfUnpinned(id)') < destructor.index('m_shared.reset();')
cpp=r'''
#include <cassert>
#include <map>
#include <vector>
#include <stdexcept>
struct Graphics {
    unsigned waits{};
    bool fail{};
    void WaitForIdle() {++waits; if (fail) throw std::runtime_error("GPU drain failure");}
};
struct System {
    Graphics graphics;
    bool powered_on{true};
    bool shutting_down{};
    Graphics& GPU() {return graphics;}
    bool IsPoweredOn() const {return powered_on;}
    bool IsShuttingDown() const {return shutting_down;}
};
struct Ledger {
    std::map<unsigned,unsigned> mappings;
    const auto& Mappings() const {return mappings;}
};
struct Worker {
    System system;
    std::map<unsigned,unsigned> m_dense_regions;
    Ledger m_mappings;
    Ledger m_sparse_overlays;
    bool m_quarantined_nv_session{};
    std::vector<unsigned> m_memory;
    void Destroy() {
__POLICY__
    }
};
int main() {
    for (unsigned powered=0;powered<2;++powered)
    for (unsigned stopping=0;stopping<2;++stopping)
    for (unsigned dense=0;dense<2;++dense)
    for (unsigned mapped=0;mapped<2;++mapped)
    for (unsigned memory=0;memory<2;++memory)
    for (unsigned overlay=0;overlay<2;++overlay)
    for (unsigned fail=0;fail<2;++fail) {
        Worker worker;
        worker.system.graphics.fail=fail!=0;
        worker.system.powered_on=powered != 0;
        worker.system.shutting_down=stopping != 0;
        if(dense)worker.m_dense_regions.emplace(2,1);
        if(mapped)worker.m_mappings.mappings.emplace(3,1);
        if(memory)worker.m_memory.push_back(4);
        if(overlay)worker.m_sparse_overlays.mappings.emplace(5,1);
        worker.Destroy();
        const bool should_drain=powered && !stopping && (dense||mapped||memory||overlay);
        assert(worker.system.graphics.waits==(should_drain ? 1U:0U));
        assert(worker.m_quarantined_nv_session==(should_drain && fail));
    }
}
'''.replace('__POLICY__',policy)
env=dict(os.environ)
sdk=Path('/Library/Developer/CommandLineTools/SDKs/MacOSX15.4.sdk')
if sdk.exists():env['SDKROOT']=str(sdk)
compilers=list(dict.fromkeys(filter(None,(shutil.which('clang++'),shutil.which('g++')))))
assert compilers
with tempfile.TemporaryDirectory(prefix='encore-worker-drain-') as temp:
    fixture=Path(temp)/'actual-destructor.cpp';fixture.write_text(cpp)
    for compiler in compilers:
        for opt in (0,2):
            exe=Path(temp)/f'{Path(compiler).name}-{opt}'
            cmd=[compiler,'-std=c++20',f'-O{opt}','-Wall','-Wextra','-Werror',
                 '-pedantic','-fsanitize=undefined','-fno-sanitize-recover=all',
                 str(fixture),'-o',str(exe)]
            built=subprocess.run(cmd,env=env,capture_output=True,text=True,timeout=45)
            assert built.returncode==0,(compiler,built.stderr[-2500:])
            test=subprocess.run([str(exe)],env=env,capture_output=True,text=True,timeout=20)
            assert test.returncode==0,(compiler,test.stderr[-2000:])
            print('P2_7_GPU_WORKER_DRAIN_ALL_OWNERS_PASS',Path(compiler).name,
                  f'O{opt}', 'cases=128','powered_shutdown_guard=1','failed_drain_quarantine=1','NS1=untouched',flush=True)


# The native build must pair this maintained implementation with the one header
# that declares its retirement ABI. This source-level ownership check prevents
# the exact PS5 compiler failure where cached Eden's older nvmap.h hid
# native_retired / FreeHandleIfUnpinned.
nvmap_header=ROOT/'vendor/sources/eden/src/core/hle/service/nvdrv/core/nvmap.h'
header_text=nvmap_header.read_text()
for token in ('bool native_retired{};', 'FreeHandleIfUnpinned(Handle::Id handle);',
              'FreeHandleImpl(Handle::Id handle, bool internal_session,'):
    assert token in header_text, token
cmake=(ROOT/'headless/CMakeLists.txt').read_text()
assert 'set(EDEN_NATIVE_NVMAP_HEADER' in cmake
assert 'vendor/sources/eden/src/core/hle/service/nvdrv/core/nvmap.h' in cmake
assert 'target_include_directories(core BEFORE PUBLIC "${EDEN_NATIVE_NVMAP_INCLUDE}")' in cmake
for overlay in ('vendor/encore-active/eden-core/include',
                'vendor/encore-active/eden/src',
                'vendor/encore-active/eden/src_as',
                'vendor/encore-active/eden/src_gpu'):
    assert not (ROOT/overlay/'core/hle/service/nvdrv/core/nvmap.h').exists(), overlay

# Compile the exact maintained NvMap final-free methods. Only the device
# mapping backend is simulated; the exclusive ownership check, mutex,
# destructive count, native retirement and weak lifetime are production C++.
nvmap_source=(ROOT/'vendor/encore-active/eden-core/src/core/hle/service/nvdrv/core/nvmap.cpp').read_text()
start='std::optional<NvMap::FreeInfo> NvMap::FreeHandle('
end='void NvMap::UnmapAllHandles('
actual=nvmap_source[nvmap_source.index(start):nvmap_source.index(end)]
assert 'if (handle_description->native_retired) return 0;' in nvmap_source
assert 'if (!allocated || native_retired)' in nvmap_source
exclusive=r"""
#include <cassert>
#include <cstdint>
#include <memory>
#include <mutex>
#include <optional>
#include <unordered_map>
#include <stdexcept>
#define LOG_WARNING(...) ((void)0)
#define LOG_DEBUG(...) ((void)0)
struct NvMap {
    struct Handle {
        using Id=unsigned;
        Id id{};
        std::mutex mutex;
        int dupes{1}, internal_dupes{}, pins{};
        bool native_retired{};
        std::uint64_t d_address{0x1000}, address{0x2000}, size{0x1000};
        struct { struct { bool Value() const {return false;} } map_uncached; } flags;
    };
    struct FreeInfo {std::uint64_t address,size; bool was_uncached,can_unlock;};
    std::unordered_map<unsigned,std::shared_ptr<Handle>> handles;
    std::mutex unmap_queue_lock;
    unsigned unmapped{};
    bool fail_unmap{};
    std::shared_ptr<Handle> GetHandle(unsigned id) {
        auto it=handles.find(id);return it==handles.end()?nullptr:it->second;
    }
    void UnmapHandle(Handle& h) {
        if(fail_unmap)throw std::bad_alloc{};
        ++unmapped; h.d_address=0;
    }
    bool TryRemoveHandle(const Handle& h){
        if(h.dupes || h.internal_dupes)return false;
        handles.erase(h.id);return true;
    }
    void Add(unsigned id){
        auto h=std::make_shared<Handle>();h->id=id;handles.emplace(id,std::move(h));
    }
    std::optional<FreeInfo> FreeHandle(Handle::Id handle,bool internal_session);
    std::optional<FreeInfo> FreeHandleIfUnpinned(Handle::Id handle);
    std::optional<FreeInfo> FreeHandleImpl(Handle::Id handle,bool internal_session,bool exclusive_native);
};
__ACTUAL__
int main(){
    NvMap n;
    for(unsigned i=1;i<=3;++i){
        n.Add(i); auto h=n.GetHandle(i);
        if(i==1)h->pins=1;
        if(i==2)h->dupes=2;
        if(i==3)h->internal_dupes=1;
        assert(!n.FreeHandleIfUnpinned(i));
        assert(!h->native_retired&&h->d_address&&n.unmapped==0&&n.GetHandle(i));
    }
    n.Add(4);
    auto f=n.FreeHandleIfUnpinned(4);
    assert(f&&f->can_unlock&&n.unmapped==1&&!n.GetHandle(4));
    assert(!n.FreeHandleIfUnpinned(4));
    n.Add(5);auto stale=n.GetHandle(5);
    f=n.FreeHandleIfUnpinned(5);
    assert(f&&!f->can_unlock&&stale->native_retired&&stale->dupes==0&&n.unmapped==2);
    n.Add(6);n.GetHandle(6)->pins=1;
    f=n.FreeHandle(6,false);
    assert(f&&f->can_unlock&&n.unmapped==3);
    n.Add(7);n.fail_unmap=true;auto bad=n.GetHandle(7);
    try{n.FreeHandleIfUnpinned(7);assert(false);}catch(const std::bad_alloc&){}
    assert(bad->native_retired&&bad->dupes==0&&bad->d_address&&n.GetHandle(7));
    assert(!n.FreeHandleIfUnpinned(7));
}
""".replace('__ACTUAL__',actual)
with tempfile.TemporaryDirectory(prefix='encore-exclusive-nvmap-free-') as temp:
    fixture=Path(temp)/'actual-nvmap-free.cpp';fixture.write_text(exclusive)
    for compiler in compilers:
        for opt in (0,2):
            exe=Path(temp)/f'{Path(compiler).name}-{opt}'
            cmd=[compiler,'-std=c++20',f'-O{opt}','-Wall','-Wextra','-Werror',
                 '-pedantic','-fsanitize=undefined','-fno-sanitize-recover=all',
                 str(fixture),'-o',str(exe)]
            built=subprocess.run(cmd,env=env,capture_output=True,text=True,timeout=45)
            assert built.returncode==0,(compiler,built.stderr[-2500:])
            test=subprocess.run([str(exe)],env=env,capture_output=True,text=True,timeout=20)
            assert test.returncode==0,(compiler,test.stderr[-2000:])
            print('NS2_EXCLUSIVE_NVMAP_FINAL_FREE_PASS',Path(compiler).name,
                  f'O{opt}','external_pins=refused','dupes=refused','stale=retired',
                  'legacy=unchanged','destructive_failure=no_retry',flush=True)
