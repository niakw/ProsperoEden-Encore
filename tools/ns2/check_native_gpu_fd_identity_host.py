#!/usr/bin/env python3
"""H06: execute the real GPU shared FD/process identity owner.

Use the maintained FindOwnedAddressSpace C++ method verbatim. Exercise stale,
recycled, foreign-type and cross-process descriptors without publishing a GPU
partition or worker handle. This is not the entire H06 IPC command matrix.
"""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
vendor = ROOT / "vendor"
source = (vendor / "encore-active/ns2-runtime/gpu_session/core/hle/service/am/service/gpu_worker_shared.cpp").read_text()
begin = "std::shared_ptr<Nvidia::Devices::nvhost_as_gpu>\nGpuWorkerSharedState::FindOwnedAddressSpace("
end = "\nGpuWorkerSharedState::~GpuWorkerSharedState()"
assert source.count(begin) == source.count(end) == 1
owner = begin + source.split(begin, 1)[1].split(end, 1)[0]
for fragment in ("address_spaces.Owns(id)", "module->VerifyFD(",
                 "opened_gpu_as.find(id)", "it->second.lock()",
                 "GetDevice<Nvidia::Devices::nvdevice>", "owned.get() == live.get()",
                 "owned->OwnsNativeProcess(native_process)"):
    assert fragment in owner, fragment

fixture = r"""
#include <cassert>
#include <cstdint>
#include <limits>
#include <map>
#include <memory>
#include <set>
#include "core/hle/service/am/service/gpu_session_protocol.h"

namespace Kernel { struct KProcess { int pid{}; }; }
namespace Nvidia {
using DeviceFD = int;
enum class NvResult { Success, InvalidState };
namespace Devices {
struct nvdevice { virtual ~nvdevice() = default; };
struct nvhost_as_gpu : nvdevice {
    Kernel::KProcess* process{};
    bool OwnsNativeProcess(Kernel::KProcess* p) const { return p == process; }
};
struct foreign_device : nvdevice {};
}
struct Module {
    std::map<int, std::shared_ptr<Devices::nvdevice>> live;
    std::set<int> valid;
    NvResult VerifyFD(DeviceFD fd) const {
        return valid.contains(fd) ? NvResult::Success : NvResult::InvalidState;
    }
    template <class T> std::shared_ptr<T> GetDevice(DeviceFD fd) const {
        auto it = live.find(fd);
        if (it == live.end()) return {};
        return std::static_pointer_cast<T>(it->second);
    }
};
}
namespace Service::AM {
struct GpuWorkerSharedState {
    GpuSessionProtocol::AddressSpaceSlots address_spaces{};
    std::shared_ptr<Nvidia::Module> module{std::make_shared<Nvidia::Module>()};
    std::map<std::uint32_t, std::weak_ptr<Nvidia::Devices::nvhost_as_gpu>> opened_gpu_as{};
    Kernel::KProcess* native_process{};
    std::shared_ptr<Nvidia::Devices::nvhost_as_gpu>
        FindOwnedAddressSpace(std::uint32_t id) const;
};
__REAL_OWNER__
}

int main() {
    using Service::AM::GpuWorkerSharedState;
    using Service::AM::GpuSessionProtocol::Status;
    using Nvidia::Devices::nvhost_as_gpu;
    Kernel::KProcess first{1}, foreign{2};
    GpuWorkerSharedState shared;
    shared.native_process = &first;
    auto owned = std::make_shared<nvhost_as_gpu>();
    owned->process = &first;
    assert(shared.address_spaces.Add(17) == Status::Success);
    shared.opened_gpu_as.emplace(17, owned);
    shared.module->valid.insert(17);
    shared.module->live[17] = owned;
    assert(shared.FindOwnedAddressSpace(17) == owned);

    assert(!shared.FindOwnedAddressSpace(0));
    assert(!shared.FindOwnedAddressSpace(std::numeric_limits<std::uint32_t>::max()));
    // A valid live device is not enough: the session must own that slot.
    shared.module->valid.insert(18);
    shared.module->live[18] = owned;
    assert(!shared.FindOwnedAddressSpace(18));
    shared.module->valid.erase(18);
    shared.module->live.erase(18);

    shared.module->valid.erase(17);
    assert(!shared.FindOwnedAddressSpace(17)); // guest already closed FD
    shared.module->valid.insert(17);
    shared.module->live[17] = std::make_shared<Nvidia::Devices::foreign_device>();
    assert(!shared.FindOwnedAddressSpace(17)); // recycled FD with foreign type
    auto replacement = std::make_shared<nvhost_as_gpu>();
    replacement->process = &first;
    shared.module->live[17] = replacement;
    assert(!shared.FindOwnedAddressSpace(17)); // recycled with same device type
    shared.module->live[17] = owned;

    shared.native_process = &foreign;
    assert(!shared.FindOwnedAddressSpace(17)); // different guest KProcess
    shared.native_process = &first;
    assert(shared.FindOwnedAddressSpace(17) == owned);

    shared.opened_gpu_as.erase(17);
    assert(!shared.FindOwnedAddressSpace(17)); // no registered original identity
    shared.opened_gpu_as.emplace(17, owned);
    shared.module->live.erase(17);
    owned.reset(); // only a weak entry remains
    assert(!shared.FindOwnedAddressSpace(17)); // original owner expired
}
""".replace("__REAL_OWNER__", owner)

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
                       "-I" + str(vendor / "encore-active/ns2-runtime/hle"),
                       str(src), "-o", str(executable)]
            build = subprocess.run(command, capture_output=True, text=True, timeout=60,
                                   env=os.environ.copy())
            assert build.returncode == 0, build.stderr[-5000:]
            run = subprocess.run([str(executable)], capture_output=True, text=True, timeout=20)
            assert run.returncode == 0, run.stderr[-5000:]
            print("H06_REAL_GPU_FD_IDENTITY_PASS", Path(compiler).name, opt,
                  "valid=1 stale=1 recycled=2 foreign_process=1 expired=1", flush=True)
