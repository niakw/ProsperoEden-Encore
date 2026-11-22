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
OWNER=ROOT/'vendor/encore-active/ns2-runtime/gpu_session/core/hle/service/am/service/gpu_worker.cpp'
source=OWNER.read_text()
method=source.split('IGpuWorker::~IGpuWorker() {',1)[1].split(
    'Result IGpuWorker::HandleSyncRequest(',1)[0]
start='    if (system.IsPoweredOn() && !system.IsShuttingDown() &&'
end='        system.GPU().WaitForIdle();'
assert method.count(start)==method.count(end)==1
policy=method[method.index(start):method.index(end)+len(end)]
assert 'm_dense_regions.empty()' in policy
assert 'm_mappings.Mappings().empty()' in policy
assert 'm_memory.empty()' in policy
assert 'system.GPU().WaitForIdle();' in policy
assert method.index('WaitForIdle();') < method.index('as->ReleaseNativeSparse4K(')
assert method.index('WaitForIdle();') < method.index('as->UnmapNative4K(')
assert method.index('WaitForIdle();') < method.index('nvmap.FreeHandle(id, false)')
# The actual worker destructor must let the final shared GPU AS / process
# registry owner release its resources before closing the worker's last
# KProcess reference. Member destruction after ~IGpuWorker's body is too late.
destructor = source.split('IGpuWorker::~IGpuWorker() {',1)[1].split(
    '\nResult IGpuWorker::BackGpuOnlyRegion(',1)[0]
assert destructor.index('m_shared.reset();') < destructor.index('m_process->Close(kernel);')
assert destructor.index('nvmap.FreeHandle(id, false)') < destructor.index('m_shared.reset();')
cpp=r'''
#include <cassert>
#include <map>
#include <vector>
struct Graphics {
    unsigned waits{};
    void WaitForIdle() {++waits;}
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
    for (unsigned memory=0;memory<2;++memory) {
        Worker worker;
        worker.system.powered_on=powered != 0;
        worker.system.shutting_down=stopping != 0;
        if(dense)worker.m_dense_regions.emplace(2,1);
        if(mapped)worker.m_mappings.mappings.emplace(3,1);
        if(memory)worker.m_memory.push_back(4);
        worker.Destroy();
        assert(worker.system.graphics.waits==(
            powered && !stopping && (dense||mapped||memory) ? 1U:0U));
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
                  f'O{opt}', 'cases=32','powered_shutdown_guard=1','NS1=untouched',flush=True)
