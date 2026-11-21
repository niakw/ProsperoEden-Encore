#!/usr/bin/env python3
"""Exercise the REAL native GPFIFO admission block before GPU mutations.

Extracts the verified owner source block and executes it with process, FD,
fence and channel stand-ins. Native invalid flags and cross-process FDs
must not initialize a channel, reserve a fence or bind a GPU owner.
Desktop/NS1 remains governed by its old submission rules.
"""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
OWNER = (ROOT / "vendor/encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/nvhost_gpu.cpp").read_text()
entry = OWNER.split("NvResult nvhost_gpu::SubmitGPFIFOImpl(", 1)[1].split(
    "Core::Memory::Memory& nvhost_gpu::GetSessionMemory(", 1)[0]
start = "    const bool native = UsesNativeAbi(fd);"
end = "    // P2.7: every native GPFIFO entry must refer to a fully mapped GMMU"
assert entry.count(start) == entry.count(end) == 1
admission = entry[entry.index(start):entry.index(end)]
assert "if (native && !native_plan)" in admission
native_plan_guard = admission.split("if (native && !native_plan)", 1)[1].split(
    "// A native GPU device may expose multiple FDs.", 1)[0]
assert "return NvResult::BadParameter;" in native_plan_guard
assert "EDEN_NS2_GPFIFO_REJECT" in native_plan_guard
assert "if (!opened || opened->process != native_owner)" in admission
assert "if (!native_channel_enabled)" in admission
assert "if (!native_gpfifo_configured)" in admission
assert admission.index("if (!native_channel_enabled)") < admission.index(
    "if (!native_gpfifo_configured)") < admission.index(
    "for (const auto& [other_fd, session_id] : sessions)")
assert admission.index("if (!native_channel_enabled)") < admission.index(
    "for (const auto& [other_fd, session_id] : sessions)")
assert "return NvResult::InvalidState;" in admission.split(
    "if (!native_channel_enabled)",1)[1].split(
    "for (const auto& [other_fd, session_id] : sessions)",1)[0]
assert "NativeGpuChannelRegistry::Instance().Bind(" not in admission
assert "system.GPU().InitChannel(" not in admission
assert "IncrementSyncpointMaxExt(" not in admission
assert "params.fence.id =" not in admission
assert entry.index("if (native && !native_plan)") < entry.index(
    "system.GPU().InitChannel(") < entry.index(
    "NativeGpuChannelRegistry::Instance().Bind(") < entry.index(
    "IncrementSyncpointMaxExt(")
assert "const u32 increment = native\n        ? native_plan->increment_total" in entry
assert "BuildIncrementCommandList(params.fence, native_completion)" in entry
assert "BuildIncrementWithWfiCommandList(params.fence, native_completion)" in entry
print("P2_7_GPFIFO_ORDERED_NATIVE_OWNER_SOURCE_PASS", flush=True)

cpp = r'''
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <map>
#include <optional>
#include "core/hle/service/nvdrv/devices/native_gpu_submission.h"
using u32 = std::uint32_t;
using Service::Nvidia::Devices::PlanNativeSubmission;
using Service::Nvidia::Devices::NativeSubmissionPlan;
namespace Kernel { struct KProcess { int identity{}; }; }
enum class NvResult { Success, BadParameter, InvalidState, NotImplemented };
struct SubmissionFlags {
    u32 raw{};
    struct FenceWait {
        bool set{};
        bool Value() const { return set; }
    } fence_wait{};
};
struct Fence { u32 id{}; u32 value{}; };
struct SyncpointManager {
    bool satisfied{};
    // Model only the live native channel syncpoint, never trust an arbitrary
    // guest-provided fence ID. The extracted C++ owner must reject 0/99.
    bool IsSyncpointAllocated(u32 id) const { return id == 1; }
    bool IsFenceSignalled(const Fence&) const { return satisfied; }
};
struct Params { SubmissionFlags flags{}; Fence fence{}; };
struct Session { const Kernel::KProcess* process{}; };
struct SessionRegistry {
    std::map<int, Session> entries;
    const Session* GetSession(int id) const {
        auto it = entries.find(id);
        return it == entries.end() ? nullptr : &it->second;
    }
};
struct Gpu {
    bool native{};
    bool native_channel_enabled{};
    bool native_gpfifo_configured{};
    std::map<int,int> sessions;
    SessionRegistry core;
    SyncpointManager syncpoint_manager;
    unsigned initializations{}, binds{}, enqueues{}, reservations{};
    bool UsesNativeAbi(int) const { return native; }
    NvResult Submit(Params& params,int fd) {
__ADMISSION__
        ++initializations;
        if (native) ++binds;
        ++reservations;
        ++enqueues;
        return NvResult::Success;
    }
};
static_assert(!PlanNativeSubmission(0x400, 0, true));
static_assert(!PlanNativeSubmission(0x101, 1, true));
static_assert(PlanNativeSubmission(0x102, 64, true)->increment_total == 66);
// Exercise native legacy allocation admission with the actual selected
// constexpr owner. An arbitrary non-power-of-two size remains legal.
static_assert(!Service::Nvidia::Devices::ValidNativeGpfifoLegacyAllocationCount(0));
static_assert(Service::Nvidia::Devices::ValidNativeGpfifoLegacyAllocationCount(1));
static_assert(Service::Nvidia::Devices::ValidNativeGpfifoLegacyAllocationCount(7));
static_assert(Service::Nvidia::Devices::ValidNativeGpfifoLegacyAllocationCount(1U << 28));
static_assert(!Service::Nvidia::Devices::ValidNativeGpfifoLegacyAllocationCount((1U << 28) + 1));
static_assert(!Service::Nvidia::Devices::ValidNativeGpfifoLegacyAllocationCount(0xFFFF'FFFFU));
int main() {
    Kernel::KProcess alice{1},bob{2};
    Gpu gpu;
    gpu.native=true;
    gpu.native_channel_enabled=true; // successful GPFIFO allocation / setup-bind
    gpu.sessions[42]=1;
    gpu.core.entries[1]={&alice};
    auto denied=[&](u32 flags,u32 count,NvResult expected) {
        Params p{{flags,{(flags&1U)!=0}},{1,count}};
        assert(gpu.Submit(p,42)==expected);
        assert(gpu.initializations==0 && gpu.binds==0 &&
               gpu.enqueues==0 && gpu.reservations==0);
    };
    denied(0x400,0,NvResult::BadParameter); // unknown native bit
    denied(0x100,65,NvResult::BadParameter); // too many completions
    denied(0x101,1,NvResult::BadParameter);  // waiting while completing
    denied(0xFFFF'FFFFU,0,NvResult::BadParameter);
    // CHANNEL_ENABLE without ALLOC_GPFIFO/SETUP_BIND must not publish a
    // native GPU command or reserve even a zero-entry completion fence.
    denied(0x102,3,NvResult::InvalidState);
    gpu.native_gpfifo_configured=true; // actual successful allocation
    gpu.sessions[77]=2;
    gpu.core.entries[2]={&bob};
    denied(0x102,3,NvResult::InvalidState); // other FD foreign process
    gpu.sessions[77]=1;                    // other FD same process allowed
    denied(0x102,65,NvResult::BadParameter);
    gpu.core.entries.erase(1);
    denied(0x102,3,NvResult::InvalidState); // retired session
    gpu.core.entries[1]={&alice};
    gpu.native_channel_enabled=false;
    denied(0x102,3,NvResult::InvalidState); // disabled native channel fails closed
    gpu.native_channel_enabled=true;
    // Execute the newly integrated REAL owner wait admission: no fake
    // native queue publication when the input syncpoint is unsatisfied.
    denied(0x1,7,NvResult::NotImplemented);
    Params invalid_syncpoint{{0x1,{true}},{99,7}};
    assert(gpu.Submit(invalid_syncpoint,42)==NvResult::BadParameter);
    assert(gpu.initializations==0 && gpu.binds==0 &&
           gpu.enqueues==0 && gpu.reservations==0);
    Params valid{{0x102},{1,64}};
    assert(gpu.Submit(valid,42)==NvResult::Success);
    assert(gpu.initializations==1 && gpu.binds==1 &&
           gpu.reservations==1 && gpu.enqueues==1);
    const auto plan=PlanNativeSubmission(valid.flags.raw,valid.fence.value,true);
    assert(plan && plan->increment_total==66 && plan->completion_count==64);
    // Signalled input fence is admitted without a synthetic wait packet.
    gpu.syncpoint_manager.satisfied=true;
    Params ready{{0x1,{true}},{1,7}};
    assert(gpu.Submit(ready,42)==NvResult::Success);
    assert(gpu.initializations==2 && gpu.binds==2 &&
           gpu.reservations==2 && gpu.enqueues==2);
    Gpu maxwell;
    maxwell.native=false;
    Params legacy{{0x400},{1,65}};
    assert(maxwell.Submit(legacy,42)==NvResult::Success);
    assert(maxwell.initializations==1 && maxwell.binds==0 &&
           maxwell.reservations==1 && maxwell.enqueues==1);
    std::puts("P2_7_GPFIFO_PREINIT_NATIVE_REJECTION_PASS flags=4 foreign_fd=1 "
              "retired_fd=1 max_completion=64 ns1_unchanged=1 native_wait_refused=1 bad_syncpoint=1 signalled_wait=1 channel_disable=1 unallocated_submit=1");
}
'''.replace("__ADMISSION__", admission)
includes = ROOT / "vendor/encore-active/ns2-runtime/hle"
assert (includes/"core/hle/service/nvdrv/devices/native_gpu_submission.h").is_file()
env = os.environ.copy()
sdk = Path("/Library/Developer/CommandLineTools/SDKs/MacOSX15.4.sdk")
if sdk.is_dir():
    env["SDKROOT"] = str(sdk)
with tempfile.TemporaryDirectory(prefix="encore-native-preinit-") as temp:
    source = Path(temp)/"native_preinit.cpp"
    source.write_text(cpp)
    for compiler in ("clang++", "g++"):
        binary = shutil.which(compiler)
        assert binary
        for opt in ("-O0","-O2"):
            output=Path(temp)/("test-"+compiler.replace("+","p")+opt)
            proc=subprocess.run([
                binary,"-std=c++20",opt,"-Wall","-Wextra","-Werror",
                "-fsanitize=undefined","-fno-sanitize-recover=all",
                "-I",str(includes),str(source),"-o",str(output),
            ],text=True,capture_output=True,env=env,timeout=80)
            assert proc.returncode==0, (compiler,opt,proc.stderr[-5000:])
            result=subprocess.run([str(output)],text=True,capture_output=True,
                                  env=env,timeout=30)
            assert result.returncode==0,(compiler,opt,result.stderr[-4000:])
            print(compiler,opt,result.stdout.strip(),flush=True)
print("P2_7_GPFIFO_PREFLIGHT_HOST_ALL_PASS",flush=True)
