#!/usr/bin/env python3
"""P0.2: execute actual native QMD and per-engine shader cache owners on OOM.

Extracts three complete C++ class method bodies, unchanged, from maintained
vendor sources; supplies small opaque native session/cache types on host. The
process/channel generation and ownership classes are REAL maintained headers.
No PS5 render, link, or GPU dispatch is inferred from the host test.
"""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[2]
PULLER=ROOT/'vendor/encore-active/ns2-runtime/gpu_dispatch/video_core/engines/puller.cpp'
SHADER=ROOT/'vendor/encore-active/ns2-runtime/ampere/video_core/native_shader_capture.cpp'
REGISTRY=ROOT/'vendor/encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/native_gpu_channel_registry.h'
PROCESS=ROOT/'vendor/encore-active/ns2-runtime/hle/core/hle/service/nvdrv/devices/native_gpu_process_registry.h'
assert all(p.is_file() for p in (PULLER,SHADER,REGISTRY,PROCESS))

def owner(source:Path,methods:tuple[str,...])->str:
    full=source.read_text()
    prefix='namespace Service::Nvidia::Devices {'
    suffix='} // namespace Service::Nvidia::Devices'
    assert full.count(prefix)==1
    block=full.split(prefix,1)[1].split(suffix,1)[0]
    assert all(block.count(name+'(')==1 for name in methods)
    assert block.count('catch (const std::bad_alloc&)')==len(methods)
    assert '#include <new>' in full
    return prefix+'\n'+block+'\n'+suffix+'\n'

source=owner(PULLER,('NativeGpuChannelRegistry::AcquireNativeQmdSession',))
source+=owner(SHADER,('NativeGpuChannelRegistry::AcquireGraphicsTranslationCache',
                      'NativeGpuChannelRegistry::AcquireComputeTranslationCache'))
assert 'qmd_sessions[ticket.process] = {ticket.generation, session};' in source
assert source.count('std::make_shared<Shader::Ampere::NativeTranslationCache>')==2
assert 'last_channel_generation + 1' in REGISTRY.read_text()

HOST=r'''
#include <atomic>
#include <cassert>
#include <cstddef>
#include <cstdlib>
#include <memory>
#include <new>
#include <cstdio>
namespace Kernel { class KProcess {}; }
namespace Tegra {
struct NativeQmdSession { unsigned proof{42}; };
namespace Control { struct ChannelState {}; }
}
namespace Shader::Ampere {
class NativeTranslationCache {
public:
    NativeTranslationCache(std::size_t limit,std::size_t count) {
        assert(limit==4*1024*1024 && count==32);
    }
};
}
#include "core/hle/service/nvdrv/devices/native_gpu_channel_registry.h"
namespace {
std::atomic<int> fail_at{0};
std::atomic<int> allocation_index{0};
void FailAt(int n) { allocation_index.store(0);fail_at.store(n); }
void StopFailure() {fail_at.store(0);allocation_index.store(0);}
void ConfirmUsed(int n) { assert(allocation_index.load()>=n); StopFailure(); }
}
void* operator new(std::size_t size) {
    int index=allocation_index.fetch_add(1)+1;
    if (index == fail_at.load()) throw std::bad_alloc{};
    if (void* ptr=std::malloc(size?size:1)) return ptr;
    throw std::bad_alloc{};
}
void operator delete(void* ptr) noexcept {std::free(ptr);}
void operator delete(void* ptr,std::size_t) noexcept {std::free(ptr);}
__ACTUAL_OWNER_METHODS__
int main() {
    using namespace Service::Nvidia::Devices;
    auto& processes=NativeGpuProcessRegistry::Instance();
    auto& channels=NativeGpuChannelRegistry::Instance();
    Kernel::KProcess p{};
    Tegra::Control::ChannelState c{};
    int graphics{},compute{};
    assert(processes.Register(&p));
    assert(channels.Bind(&c,&p));
    const auto ticket=channels.CaptureTicket(&c);
    assert(ticket);
    assert(channels.BindGraphicsEngine(&c,&graphics,1));
    assert(channels.BindComputeEngine(&c,&compute,2));
    // QMD allocation 1: make_shared; allocation 2: process-owned map node.
    FailAt(1);
    assert(!channels.AcquireNativeQmdSession(&c));
    ConfirmUsed(1);
    FailAt(2);
    assert(!channels.AcquireNativeQmdSession(&c));
    ConfirmUsed(2);
    const auto qmd=channels.AcquireNativeQmdSession(&c);
    assert(qmd && qmd->proof==42);
    assert(channels.AcquireNativeQmdSession(&c)==qmd);
    assert(channels.IsCurrent(&c,*ticket));
    // Both shader domains refuse allocation without corrupting their
    // existing bind epochs, then retain separate per-engine caches.
    FailAt(1);
    assert(!channels.AcquireGraphicsTranslationCache(&graphics,*ticket));
    ConfirmUsed(1);
    const auto gcache=channels.AcquireGraphicsTranslationCache(&graphics,*ticket);
    assert(gcache && channels.AcquireGraphicsTranslationCache(&graphics,*ticket)==gcache);
    FailAt(1);
    assert(!channels.AcquireComputeTranslationCache(&compute,*ticket));
    ConfirmUsed(1);
    const auto ccache=channels.AcquireComputeTranslationCache(&compute,*ticket);
    assert(ccache && ccache!=gcache &&
           channels.AcquireComputeTranslationCache(&compute,*ticket)==ccache);
    channels.Unbind(&c);
    assert(!channels.AcquireNativeQmdSession(&c));
    assert(!channels.AcquireGraphicsTranslationCache(&graphics,*ticket));
    assert(!channels.AcquireComputeTranslationCache(&compute,*ticket));
    assert(channels.Bind(&c,&p));
    const auto new_ticket=channels.CaptureTicket(&c);
    assert(new_ticket && new_ticket->channel_generation != ticket->channel_generation);
    assert(!channels.AcquireGraphicsTranslationCache(&graphics,*ticket));
    assert(!channels.AcquireComputeTranslationCache(&compute,*ticket));
    const auto new_qmd=channels.AcquireNativeQmdSession(&c);
    assert(new_qmd && new_qmd!=qmd);
    channels.Unbind(&c);
    processes.Unregister(&p);
    std::puts("P0_2_GPU_REAL_QMD_AND_SHADER_CACHE_OWNER_OOM_PASS");
}
'''

compiler=shutil.which('clang++') or shutil.which('g++')
assert compiler
sdk=Path('/Library/Developer/CommandLineTools/SDKs/MacOSX15.4.sdk')
env=os.environ.copy()
if sdk.is_dir():env['SDKROOT']=str(sdk)
with tempfile.TemporaryDirectory(prefix='encore-gpu-cache-alloc-') as temp:
    generated=Path(temp)/'source_methods.cpp'
    generated.write_text(HOST.replace('__ACTUAL_OWNER_METHODS__',source))
    for opt in (0,2):
        exe=Path(temp)/f'gpu-cache-O{opt}'
        command=[compiler,'-std=c++20',f'-O{opt}', '-Wall','-Wextra','-Werror',
                 '-fsanitize=undefined','-fno-sanitize-recover=all',
                 '-I'+str(ROOT/'vendor/encore-active/ns2-runtime/hle'),
                 '-I'+str(ROOT/'vendor/encore-active/ns2-runtime/nvdrv_gpu'),
                 str(generated),'-o',str(exe)]
        build=subprocess.run(command,capture_output=True,text=True,env=env,timeout=70)
        assert build.returncode==0,build.stderr[-5300:]
        run=subprocess.run([str(exe)],capture_output=True,text=True,env=env,timeout=20)
        assert run.returncode==0,run.stderr[-5300:]
        assert 'P0_2_GPU_REAL_QMD_AND_SHADER_CACHE_OWNER_OOM_PASS' in run.stdout
        print('P0_2_NATIVE_GPU_CACHE_ALLOC_HOST_PASS',Path(compiler).name,f'O{opt}',flush=True)
