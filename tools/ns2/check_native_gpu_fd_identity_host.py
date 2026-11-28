#!/usr/bin/env python3
"""Execute the actual NS2 VM-to-AS binding, lookup, replay and unbind owners.
Mock only the GPU page-table operations; verify process identity and rollback."""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[2]
vendor=ROOT/"vendor"
root=vendor/"encore-active/eden/src/core/hle/service/am/service"
source=(root/"gpu_worker_shared.cpp").read_text()
header=(root/"gpu_worker_shared.h").read_text()
begin="std::shared_ptr<Nvidia::Devices::nvhost_as_gpu>\nGpuWorkerSharedState::FindOwnedAddressSpace("
end="\nGpuWorkerSharedState::~GpuWorkerSharedState()"
assert source.count(begin)==source.count(end)==1
owner=begin+source.split(begin,1)[1].split(end,1)[0]
identity="struct IdentityGpuMapping {"+header.split("struct IdentityGpuMapping {",1)[1].split("\n};",1)[0]+"\n};"
assert "address_spaces.Registered(id)" in owner and "owned->OwnsNativeProcess(native_process)" in owner
assert "module->VerifyFD(" not in owner
fixture=r"""
#include <array>
#include <cassert>
#include <cstdint>
#include <map>
#include <memory>
#include <mutex>
#include <new>
#include <vector>
#include "core/hle/service/am/service/gpu_session_protocol.h"
namespace Kernel {struct KProcess {int pid{};};}
namespace Service::Nvidia {
enum class NvResult {Success,InvalidState,BadParameter,InsufficientMemory};
namespace Devices {
struct nvhost_as_gpu {
    Kernel::KProcess* process{};
    bool live{true};
    unsigned map_calls{},fail_at{},unmap_calls{};
    std::map<std::uint64_t,std::uint64_t> mappings;
    bool OwnsNativeProcess(Kernel::KProcess* p) const {return live&&p==process;}
    NvResult MapNative4K(std::uint32_t handle,std::uint64_t address,std::uint64_t source,
                         std::uint64_t size,std::uint8_t kind) {
        assert(handle&&source==0&&kind==0);
        if(++map_calls==fail_at)return NvResult::InsufficientMemory;
        return mappings.emplace(address,size).second?NvResult::Success:NvResult::InvalidState;
    }
    NvResult UnmapNative4K(std::uint64_t address,std::uint64_t size) {
        ++unmap_calls;auto it=mappings.find(address);
        if(it==mappings.end()||it->second!=size)return NvResult::InvalidState;
        mappings.erase(it);return NvResult::Success;
    }
};
}
}
namespace Service::AM {
__IDENTITY__
struct GpuWorkerSharedState {
    std::mutex mutex;
    GpuSessionProtocol::AddressSpaceSlots address_spaces;
    std::map<std::uint32_t,std::weak_ptr<Nvidia::Devices::nvhost_as_gpu>> opened_gpu_as;
    std::vector<IdentityGpuMapping> identity_gpu_mappings;
    Kernel::KProcess* native_process{};
    std::shared_ptr<Nvidia::Devices::nvhost_as_gpu> FindOwnedAddressSpace(std::uint32_t) const;
    Nvidia::NvResult BindImportedAddressSpace(std::uint32_t,const std::shared_ptr<Nvidia::Devices::nvhost_as_gpu>&);
    void UnbindImportedAddressSpace(std::uint32_t,const Nvidia::Devices::nvhost_as_gpu*);
};
__OWNER__
}
int main(){
    using Service::AM::GpuWorkerSharedState;
    using Service::AM::GpuSessionProtocol::Status;
    using Service::Nvidia::NvResult;
    using Service::Nvidia::Devices::nvhost_as_gpu;
    Kernel::KProcess first{1},foreign{2};
    GpuWorkerSharedState s;s.native_process=&first;
    auto a=std::make_shared<nvhost_as_gpu>();a->process=&first;
    auto b=std::make_shared<nvhost_as_gpu>();b->process=&foreign;
    assert(s.address_spaces.Add(17)==Status::Success);
    assert(s.BindImportedAddressSpace(17,a)==NvResult::InvalidState);
    assert(s.address_spaces.Register(17)==Status::Success);
    assert(!s.FindOwnedAddressSpace(17));
    assert(s.BindImportedAddressSpace(17,b)==NvResult::InvalidState);
    s.identity_gpu_mappings.push_back({1,0x20000,0x1000,{},0});
    s.identity_gpu_mappings.push_back({2,0x30000,0x1000,{},0});
    a->fail_at=2;
    assert(s.BindImportedAddressSpace(17,a)==NvResult::InsufficientMemory);
    assert(a->mappings.empty()&&a->unmap_calls==1&&!s.FindOwnedAddressSpace(17));
    for(const auto& m:s.identity_gpu_mappings)assert(!m.HasSpace(17));
    a->fail_at=0;
    assert(s.BindImportedAddressSpace(17,a)==NvResult::Success);
    assert(s.FindOwnedAddressSpace(17)==a&&a->mappings.size()==2);
    for(const auto& m:s.identity_gpu_mappings)assert(m.HasSpace(17));
    assert(!s.FindOwnedAddressSpace(0)&&!s.FindOwnedAddressSpace(18));
    b->process=&first;
    assert(s.BindImportedAddressSpace(17,b)==NvResult::InvalidState);
    s.UnbindImportedAddressSpace(17,b.get());
    assert(s.FindOwnedAddressSpace(17)==a);
    a->live=false;
    assert(!s.FindOwnedAddressSpace(17));
    s.UnbindImportedAddressSpace(17,a.get());
    assert(!s.FindOwnedAddressSpace(17));
    for(const auto& m:s.identity_gpu_mappings)assert(!m.HasSpace(17));
    assert(s.BindImportedAddressSpace(17,b)==NvResult::Success);
    assert(s.FindOwnedAddressSpace(17)==b&&b->mappings.size()==2);
    b.reset();assert(!s.FindOwnedAddressSpace(17));
}
""".replace("__IDENTITY__",identity).replace("__OWNER__",owner)
compilers = list(dict.fromkeys(x for x in (shutil.which("clang++"), shutil.which("g++")) if x))
assert compilers, "Clang or GCC C++20 compiler required"
with tempfile.TemporaryDirectory(prefix="eden-h06-fd-identity-") as directory:
    src = Path(directory) / "owner.cpp"
    src.write_text(fixture)
    for compiler in compilers:
        for opt in ("-O0", "-O2"):
            executable = Path(directory) / (Path(compiler).name + opt)
            command = [compiler, "-std=c++20", opt, "-Wall", "-Wextra", "-Werror",
                       "-fsanitize=undefined", "-fno-sanitize-recover=all",
                       "-I" + str(vendor / "encore-active/eden/src"),
                       str(src), "-o", str(executable)]
            build = subprocess.run(command, capture_output=True, text=True, timeout=60,
                                   env=os.environ.copy())
            assert build.returncode == 0, build.stderr[-5000:]
            run = subprocess.run([str(executable)], capture_output=True, text=True, timeout=20)
            assert run.returncode == 0, run.stderr[-5000:]
            print("H06_REAL_GPU_FD_IDENTITY_PASS", Path(compiler).name, opt,
                  "vm_import=1 foreign_process=1 duplicate=refused close_identity=1 replay_rollback=1 expired=1", flush=True)
