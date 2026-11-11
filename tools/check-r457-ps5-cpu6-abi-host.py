#!/usr/bin/env python3
"""R457 4-core/6-core KProcess ABI ODR regression source gate.

Real R457 ELF: KProcess constructor +0x1b0, AudioOut initial-buffer
read +0x160. Five 8-byte per-core arrays x two extra cores = 0x50.
Host-only: proves the actual ABI probe refuses 4 cores, accepts 6.
"""
from pathlib import Path
import shutil
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
cmake = (root / "headless/CMakeLists.txt").read_text()
probe = (root / "headless/ps5_cpu6_abi_probe.cpp").read_text()

assert cmake.count('set(EDEN_NS2_CPU6_ROOT "') == 1
assert 'if(PS5_NATIVE AND EDEN_REVIEWED_DUAL_NPDM)' in cmake
for target, visibility in (("core", "PUBLIC"), ("dynarmic", "PUBLIC"),
                           ("audio_core", "PRIVATE"), ("video_core", "PRIVATE"),
                           ("hid_core", "PRIVATE"),
                           ("eden-headless", "PRIVATE")):
    call = (f'target_include_directories({target} BEFORE {visibility} '
            '"${EDEN_NS2_CPU6_ROOT}")')
    assert cmake.count(call) == 1, call
assert 'foreach(eden_cpu6_abi_consumer IN ITEMS core audio_core video_core hid_core)' in cmake
assert 'target_sources(${eden_cpu6_abi_consumer} PRIVATE' in cmake
assert '"${EDEN_PORT_DIR}/ps5_cpu6_abi_probe.cpp")' in cmake
assert 'static_assert(Core::Hardware::NUM_CPU_CORES == 6,' in probe
assert '#include "core/hle/kernel/k_process.h"' in probe
assert 'std::declval<Kernel::KProcess&>().GetMemory()' in probe
assert 5 * (6 - 4) * 8 == 0x1B0 - 0x160 == 0x50

cc = shutil.which("clang++") or shutil.which("g++")
assert cc, "C++20 compiler required"
with tempfile.TemporaryDirectory(prefix="r457-cpu6-abi-") as temp:
    location = Path(temp)
    for cores in (4, 6):
        include = location / f"cores{cores}" / "core"
        (include / "hle" / "kernel").mkdir(parents=True)
        (include / "hardware_properties.h").write_text(
            "#pragma once\nnamespace Core::Hardware { inline constexpr "
            f"unsigned NUM_CPU_CORES={cores}; }}\n")
        (include / "hle" / "kernel" / "k_process.h").write_text(
            "#pragma once\n"
            '#include "core/hardware_properties.h"\n'
            "namespace Core::Memory { class Memory {}; }\n"
            "namespace Kernel { struct KProcess { "
            "Core::Memory::Memory& GetMemory(); }; }\n")
        run = subprocess.run([
            cc, "-std=c++20", "-DPS5_NATIVE", "-Wall", "-Wextra", "-Werror",
            "-fsyntax-only", f"-I{include.parent}",
            str(root / "headless/ps5_cpu6_abi_probe.cpp")],
            capture_output=True, text=True)
        if cores == 6:
            assert run.returncode == 0, run.stderr
        else:
            assert run.returncode != 0, "ABI probe silently accepted a 4-core module"
            assert "NUM_CPU_CORES == 6" in run.stderr, run.stderr
print("R457_NATIVE_KPROCESS_ABI_SOURCE_GATE_PASS core6=1 audio6=1 video6=1 hid6=1 rejects4=1")
