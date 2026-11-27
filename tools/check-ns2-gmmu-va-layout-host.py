#!/usr/bin/env python3
"""Compile the actual 4K GMMU partition helper and verify its source owner."""
from pathlib import Path
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
AS = ROOT / "vendor/encore-active/eden/src_as"
OWNER = AS / "core/hle/service/nvdrv/devices/nvhost_as_gpu.cpp"
HELPER = AS / "core/hle/service/nvdrv/devices/native_gpu_va_layout.h"
TEST = ROOT / "tools/ns2/test_native_gpu_va_layout.cpp"

def main():
    if not all(p.is_file() for p in (OWNER, HELPER, TEST)):
        print("NS2 4K GMMU source owner missing", file=sys.stderr)
        return 2
    owner = OWNER.read_text()
    markers = (
        'PlanNativeGpuVaLayout(start, split, end, big_page_size)',
        'if (!layout) return NvResult::BadValue;',
        'vm.small_page_allocator.emplace(layout->small_begin, layout->small_end);',
        'vm.big_page_allocator.emplace(layout->big_begin, layout->big_end);',
        'if (!vm.initialised || !gmmu || !m_native_process)',
        'const std::scoped_lock lock{mutex, gpu_channel_device->channel_mutex};',
        'if (!session || session->process != m_native_process)',
        'if (channel.memory_manager && channel.memory_manager != gmmu.get())',
        'NativePinnedPhysicalSpan(pinned, source, size)',
        'NativePinnedPhysicalSpan(pinned, range.source_offset, range.size)',
    )
    if not all(x in owner for x in markers):
        print("NS2 real GMMU layout owner not wired to validated helper", file=sys.stderr)
        return 2
    if owner.count('NativePinnedPhysicalSpan(pinned, source, size)') != 2:
        print("Native 4K/image pin paths are not both checked", file=sys.stderr)
        return 2
    # A:0x0D/A:0x14 and GSV216 use the selected RemapNativeSparse owner:
    # preflight EVERY physical pin/span before publishing pins or any PTE.
    # The historical single 4K MapSparse(..., false) call no longer exists;
    # accepting its absence would silently drop the safety check.
    remap_marker = (
        'NvResult nvhost_as_gpu::RemapNativeSparse('
        'std::span<const NativeSparseRemapEntry> entries) {'
    )
    if owner.count(remap_marker) != 1:
        print("Native sparse remap owner missing or duplicated", file=sys.stderr)
        return 2
    remap = owner.split(remap_marker, 1)[1].split('\n}', 1)[0]
    ordered = (
        'for (std::size_t i = 0; i < ranges.size(); ++i) {',
        'if (!NativePinnedPhysicalSpan(pinned, range.source_offset, range.size)',
        'native_sparse_pins.merge(newly_pinned);',
        'gmmu->MapSparse(range.address, range.size, big_page_ranges[i]);',
        'gmmu->Map(range.address, pinned->second + range.source_offset, range.size,',
    )
    if any(remap.count(token) < 1 for token in ordered):
        print("Native sparse preflight or GPU mutation missing", file=sys.stderr)
        return 2
    preflight = remap.index(ordered[1])
    pin_publish = remap.index(ordered[2])
    first_sparse_map = remap.index(ordered[3])
    first_physical_map = remap.index(ordered[4])
    if not (remap.index(ordered[0]) < preflight < pin_publish <
            min(first_sparse_map, first_physical_map)):
        print("Native sparse preflight runs after pin/PTE publication", file=sys.stderr)
        return 2
    if remap.count(ordered[0]) < 2:
        print("Native sparse preflight and map passes are not both present", file=sys.stderr)
        return 2
    if '(vm.va_range_end - vm.va_range_split) >> vm.big_page_size_bits' in owner:
        print("Relative GPU VA allocator bound reintroduced", file=sys.stderr)
        return 2
    compiler = shutil.which("g++") or shutil.which("clang++")
    host_env = dict(os.environ)
    pinned_sdk = Path("/Library/Developer/CommandLineTools/SDKs/MacOSX15.4.sdk")
    if pinned_sdk.is_dir():
        host_env["SDKROOT"] = str(pinned_sdk)
    if not compiler:
        print("C++20 compiler missing", file=sys.stderr)
        return 2
    with tempfile.TemporaryDirectory(prefix="encore-ns2-gmmu-va-") as folder:
        for opt in ("-O0", "-O2"):
            exe = Path(folder) / ("test" + opt)
            command = [compiler, "-std=c++20", opt, "-Wall", "-Wextra", "-Werror",
                       "-pedantic", "-fsanitize=undefined", "-fno-sanitize-recover=all",
                       "-I", str(AS), str(TEST), "-o", str(exe)]
            subprocess.run(command, check=True, env=host_env)
            subprocess.run([str(exe)], check=True,
                           env={**host_env, "UBSAN_OPTIONS": "halt_on_error=1"})
    print("Native GMMU bounds and absolute VA limit: PASS (O0/O2 UBSan)")
    print("No native GPU worker, Ampere shaders or PS5 first frame inferred.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
