#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Source-only guard for the shipping CPU/JIT stability configuration."""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
cmake = (root / 'headless/CMakeLists.txt').read_text()
main = (root / 'headless/main.cpp').read_text()
jit_list = (root / 'headless/jit_list.h').read_text()
jit_links = (root / 'vendor/encore-active/eden-core/dynarmic/shared-jit/jit_links.inc').read_text()

# The production CMake graph was consolidated: no experiment selector is
# defined, and the standard A64 owner is unconditionally selected.  The old
# test demanded obsolete OFF options and shared-JIT variant branches and
# blocked a correctly configured native build.
assert 'option(EDEN_SHARED_JIT' not in cmake
assert 'option(EDEN_JIT_COMPILE_BATCH' not in cmake
assert 'set(EDEN_SHARED_JIT ON)' not in cmake
assert 'if(EDEN_SHARED_JIT)' not in cmake
assert 'if(EDEN_JIT_COMPILE_BATCH)' not in cmake
assert 'set(EDEN_A64_EMITTER_UNIT "${EDEN_MAINTAINED_EMIT_ROOT}/a64_emit_x64_standard.cpp")' in cmake
assert 'set(EDEN_A64_EMITTER_HEADER "${EDEN_MAINTAINED_EMIT_ROOT}/a64_emit_x64_standard.h")' in cmake
assert 'set(EDEN_A64_INTERFACE_UNIT "${EDEN_A64_INTERFACE_ROOT}/a64_interface_standard.cpp")' in cmake
assert 'configure_file("${EDEN_A64_INTERFACE_UNIT}" "${PORT_BUILD_DIR}/a64_interface.cpp" COPYONLY)' in cmake
assert 'target_sources(dynarmic PRIVATE "${PORT_BUILD_DIR}/a64_interface.cpp")' in cmake
assert 'target_compile_definitions(eden-memory-check PRIVATE EDEN_SHARED_JIT_AVAILABLE=0)' in cmake
assert 'EDEN_SHARED_JIT_AVAILABLE=0' in cmake
assert 'EDEN_JIT_COMPILE_BATCH_AVAILABLE=0' in cmake
native = (root / 'tools/build-headless-native.sh').read_text()
host = (root / 'tools/build-headless-host.sh').read_text()
package_build = (root / 'tools/build-package.sh').read_text()
package_script = (root / 'tools/package-headless-native.sh').read_text()
# Host compatibility flags stay explicitly OFF; native release has no
# experimental selector at all and packaging fails closed on a forced ON.
assert '-DEDEN_SHARED_JIT=OFF -DEDEN_JIT_COMPILE_BATCH=OFF' in host
for script in (native, package_build):
    assert '-DEDEN_SHARED_JIT=ON' not in script
    assert '-DEDEN_JIT_COMPILE_BATCH=ON' not in script
assert "for experimental in ('EDEN_SHARED_JIT', 'EDEN_JIT_COMPILE_BATCH'):" in package_script
assert "assert experimental + ':BOOL=ON' not in profile" in package_script
assert "assert experimental + ':UNINITIALIZED=ON' not in profile" in package_script
memory_check = (root / 'headless/memory_check.cpp').read_text()
assert '#if EDEN_SHARED_JIT_AVAILABLE\n// Shared compiled code' in memory_check
assert '#if EDEN_SHARED_JIT_AVAILABLE\n// Dispatcher lookups' in memory_check

# Shipping builds cannot accidentally retain link-time references to JitGroup helpers.
assert '#if EDEN_SHARED_JIT_AVAILABLE\nextern "C" bool eden_jit_shared;' in main
assert '#if EDEN_SHARED_JIT_AVAILABLE\n#include "performance.h"' in jit_list
assert 'Production stability mode: saved-block precompilation is structurally unavailable' in jit_list

# Normal profiles always start with saved-block precompilation off.
assert 'Eden::JitList::enabled = false;' in main
assert 'CPU JIT: Dynarmic per-core; Encore cross-core sharing, successor batching and saved-block compile-ahead disabled' in main


# Wall-clock multicore must remain pre-emptible inside direct guest loops. Dynarmic's stock
# LinkBlockFast has no halt check; Encore guards only backward/self links to avoid a global cost.
assert 'wall_clock_back_edge = !e.conf.enable_cycle_counting && next_pc <= from_pc' in jit_links
assert 'wall_clock_back_edge ? EdenLinkCheck::Halt : EdenLinkCheck::None' in jit_links

print('Shipping JIT stability defaults PASS (per-core Dynarmic, no compile-ahead/batching/shared JIT)')
