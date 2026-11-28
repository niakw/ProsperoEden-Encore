#!/usr/bin/env python3
"""Source + C++20 host witness for NS2-only GPU access SVC 0x80 admission."""
from pathlib import Path
import hashlib
import shutil
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
vendor = root / "vendor/encore-active"
base = vendor / "eden/src"
src = (base / "core/hle/kernel/svc.cpp").read_text()
helper = (base / "core/hle/kernel/ns2_gpu_memory_attribute.h").read_text()
pid = (vendor / "eden/src/core/loader/ns2_svc_trace.h").read_text()
recipe = (root / "headless/CMakeLists.txt").read_text()
assert recipe.count("set(EDEN_SHARED_NS2_GPU_ACCESS_SVC ON)") == 1
assert 'if(PS5_NATIVE AND EDEN_REVIEWED_DUAL_NPDM)' in recipe
assert 'EDEN_FINAL_RELEASE_PROFILE' not in recipe
assert 'list(REMOVE_ITEM eden_ns2_gpu_access_sources "hle/kernel/svc.cpp")' in recipe
assert 'target_include_directories(core BEFORE PUBLIC "${EDEN_NS2_GPU_ACCESS_ROOT}")' in recipe
assert 'Eden::NS2::SvcTrace::IsActive(process.GetProcessId())' in src
assert 'Settings::values.memory_layout_mode.GetValue() == Settings::MemoryLayout::Memory_12Gb' in src
assert 'process.Is64Bit()' in src
assert 'process.GetPageTable().Contains(address, size)' in src
assert 'process.GetPageTable().SetMemoryAttribute(' in src
assert 'static_cast<KMemoryAttribute>(mask)' in src
assert 'static_cast<KMemoryAttribute>(attribute)' in src
svc_enum = (base / "core/hle/kernel/svc_types.h").read_text()
block_enum = (base / "core/hle/kernel/k_memory_block.h").read_text()
assert 'GpuAccessible = (1 << 5)' in svc_enum

def git_blob(text: str) -> str:
    raw = text.encode("utf-8")
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()

# The old NS2 overlay and the maintained Eden header were consolidated into
# one canonical encore-active owner. Validate the exact reviewed successor
# and reconstruct its exact predecessor instead of comparing that file to
# itself plus the same additions.
assert git_blob(svc_enum) == "093441f9da4f3232ea884f1241417ef2dcc93a5f"
gpu_attribute = '    GpuAccessible = (1 << 5), // NS2 SVC 0x80; preserve maintained NS1 source ABI\n'
wait64 = '    WaitIfEqual64 = 3, // 8-byte aligned compare, no truncated upper word\n'
assert svc_enum.count(gpu_attribute) == 1
assert svc_enum.count(wait64) == 1
svc_predecessor = svc_enum.replace(gpu_attribute, "", 1).replace(wait64, "", 1)
assert git_blob(svc_predecessor) == "cc37a063101f85b8cdd0eb2c1bea97df32ab9969"
# Six-core Switch 2 processes may query thread ticks on physical cores 4/5.
# Preserve the legacy four-core range for non-extended processes.
info_source = (vendor / "eden/src/core/hle/kernel/svc/svc_info.cpp").read_text()
cpu6_header = (vendor / "eden/src/core/hardware_properties.h").read_text()
assert "constexpr u32 NUM_CPU_CORES = 6;" in cpu6_header
assert "GetPhysicalCoreMask();" in info_source
assert "const u64 num_cpus = (physical_core_mask & (u64{3} << 4)) != 0" in info_source
assert "? Core::Hardware::NUM_CPU_CORES : 4;" in info_source
assert '    PermissionLocked = (1 << 4),' in svc_enum
assert '    WaitIfEqual = 2,' in svc_enum
assert 'Unknown37 = 37' in svc_enum and 'Unknown38 = 38' in svc_enum
# Native 4K worker research must run against the SAME persisted SVC 0x80
# attribute. Never silently pin non-GPU guest pages or use trace-only SVC.
worker = (vendor / "eden/src/core/hle/service/am/service/gpu_worker.cpp").read_text()
assert 'True(info.m_attribute & Kernel::KMemoryAttribute::GpuAccessible)' in worker
assert 'LockForMapDeviceAddressSpace(' in worker
# Source selected through the shared native owner, never an optional
# research SVC shim; preserve the real SVC, PID and attribute checks below.
assert 'set(EDEN_NS2_GPU_ACCESS_SOURCE' in recipe
assert 'list(REMOVE_ITEM eden_ns2_gpu_access_sources "hle/kernel/svc.cpp")' in recipe
assert 'list(APPEND eden_ns2_gpu_access_sources "${EDEN_NS2_GPU_ACCESS_SOURCE}")' in recipe
svc_compile_block = recipe.split('set_property(SOURCE "${EDEN_NS2_GPU_ACCESS_SOURCE}"', 1)[1].split(')', 1)[0]
assert 'TARGET_DIRECTORY core APPEND PROPERTY COMPILE_DEFINITIONS' in svc_compile_block
assert '"PS5_NATIVE=1" "EDEN_NS2_SVC_TRACE=1"' in svc_compile_block
assert 'EDEN_NS2_EXEFS_EXPERIMENTAL' not in recipe
assert '#ifdef EDEN_NS2_SVC_TRACE' in src
assert 'SvcTrace::Next(process.GetProcessId())' in src
assert 'GpuAccessible = static_cast<u8>(Svc::MemoryAttribute::GpuAccessible)' in block_enum
assert 'SetMask = Uncached | PermissionLocked | GpuAccessible' in block_enum
assert 'target_include_directories(core BEFORE PUBLIC "${EDEN_NS2_GPU_ACCESS_ROOT}")' in recipe
assert 'target_include_directories(video_core BEFORE PRIVATE "${EDEN_NS2_GPU_ACCESS_ROOT}")' in recipe
assert 'if (imm == 0x80' in src
assert 'case Eden::NS2::GpuAccess::Status::InvalidAddress:' in src
assert 'case Eden::NS2::GpuAccess::Status::InvalidSize:' in src
assert 'case Eden::NS2::GpuAccess::Status::InvalidAttribute:' in src
assert 'result = ResultInvalidCurrentMemory;' in src
assert 'SetArg64(args, 0, result.raw);' in src
assert 'else if (process.Is64Bit())' in src and 'Call64(system, imm, args);' in src
assert 'active_pid.load(std::memory_order_acquire) == pid' in pid
assert '#ifdef PS5_NATIVE' in pid
assert 'eden_native_detailed_logging() noexcept __attribute__((weak))' in pid
assert 'return eden_native_detailed_logging && eden_native_detailed_logging();' in pid
assert 'if (!IsActive(pid) || !DetailedEnabled())' in pid
assert 'constexpr std::uint32_t RecentSamples = 64;' in pid
assert 'inline std::uint64_t RecordRecent(' in pid
assert 'inline void RecordOutcome(' in pid
assert 'outcome=completed' in pid and 'outcome=pending' in pid
assert 'GetContext(svc_context)' in src
assert 'SvcTrace::RecordOutcome(' in src
assert 'inline void DumpRecent(' in pid
assert 'entry.sequence.store(seq, std::memory_order_release);' in pid
assert 'inline void ResetForTitle() noexcept' in pid
assert 'active_pid.store(0, std::memory_order_release)' in pid
core = (vendor / "eden/src/core/core.cpp").read_text()
load = core.split('SystemResultStatus Load(System& system', 1)[1].split('InitializeKernel(system);', 1)[0]
assert 'Eden::NS2::SvcTrace::ResetForTitle();' in load
assert core.count('Eden::NS2::SvcTrace::ResetForTitle();') == 2
shutdown = core.split('void ShutdownMainProcess()', 1)[1].split('bool IsShuttingDown()', 1)[0]
assert shutdown.index('kernel.Shutdown();') < shutdown.index('Eden::NS2::SvcTrace::ResetForTitle();')
assert shutdown.index('Eden::NS2::SvcTrace::ResetForTitle();') < shutdown.index('RestoreNs2MemoryLayout();')
assert 'GpuAccessibleMask = 0x20' in helper
compiler = shutil.which("clang++-18") or shutil.which("clang++") or shutil.which("g++")
assert compiler, "C++20 host compiler unavailable"
fixture = r"""
#include "core/hle/kernel/ns2_gpu_memory_attribute.h"
#include "core/loader/ns2_svc_trace.h"
#include <cassert>
#include <cstdint>
#include <limits>
using Eden::NS2::GpuAccess::Validate;
using Eden::NS2::GpuAccess::Status;
static_assert(Validate(0x1000, 0x1000, 0x20, 0x20) == Status::Success);
static_assert(Validate(0x1000, 0x2000, 0x20, 0) == Status::Success);
static_assert(Validate(0x1000, 0x1000, 0, 0) == Status::Success);
static_assert(Validate(0x1001, 0x1000, 0x20, 0x20) == Status::InvalidAddress);
static_assert(Validate(0x1000, 0, 0x20, 0x20) == Status::InvalidSize);
static_assert(Validate(0x1000, 0x1001, 0x20, 0x20) == Status::InvalidSize);
static_assert(Validate(std::numeric_limits<std::uint64_t>::max()-0xfff, 0x2000, 0x20, 0x20) == Status::InvalidSize);
static_assert(Validate(0x1000, 0x1000, 0x10, 0x20) == Status::InvalidAttribute);
static_assert(Validate(0x1000, 0x1000, 0x20, 0x10) == Status::InvalidAttribute);
int main() {
    using namespace Eden::NS2::SvcTrace;
    assert(!IsActive(0));
    assert(!IsActive(123));
    Register(123);
    assert(IsActive(123) && !IsActive(124));
    Unregister(124);
    assert(IsActive(123));
    Unregister(123);
    assert(!IsActive(123));
    Register(123);
    assert(IsActive(123));
    ResetForTitle();
    assert(!IsActive(123) && !Next(123).has_value());
    // The next guest kernel can recycle the same process ID; it stays
    // unauthorized until the NS2 ExeFS loader explicitly registers it.
    assert(!IsActive(123));
    Register(123);
    assert(IsActive(123) && Next(123).has_value());
    ResetForTitle();
    assert(!IsActive(123) && !Next(123).has_value());
}
"""
with tempfile.TemporaryDirectory(prefix="encore-ns2-gpu-access-") as d:
    p = Path(d)
    (p / "test.cpp").write_text(fixture)
    exe = p / "test"
    subprocess.run([compiler, "-std=c++20", "-Wall", "-Wextra", "-Werror",
                    "-I", str(base), "-I", str(vendor / "eden/src"),
                    str(p / "test.cpp"), "-o", str(exe)], check=True)
    subprocess.run([str(exe)], check=True)
# Engine controls must exercise the exact *pinned* vendor witness. This is
# the full selected dispatcher TU, not only a mock of its logging header.
for vendor_test, receipt in (
    ("ns2_recent_svc_fault_trace_host.py", "NS2_RECENT_SVC_OUTCOME_HOST_PASS"),
    ("ns2_svc_real_native_tu_host.py", "NS2_SVC_REAL_NATIVE_TU_HOST_PASS"),
):
    run = subprocess.run([shutil.which("python3") or "python3", "-B",
                          str(root / "vendor/tests" / vendor_test)],
                         capture_output=True, text=True, timeout=200)
    assert run.returncode == 0 and receipt in run.stdout, (
        vendor_test, run.returncode, run.stdout[-1600:], run.stderr[-4000:])
print("ENCORE_NS2_GPU_ACCESS_SVC_HOST_PASS pid=exact mask=0x20 alignment=4k overflow=guarded ns1=unchanged stale_pid=blocked returned_outcomes=1 real_TU=1")
