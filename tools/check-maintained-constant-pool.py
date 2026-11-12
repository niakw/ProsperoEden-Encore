#!/usr/bin/env python3
"""Pin maintained JIT constant-pool source parity and native selection."""
from pathlib import Path
root = Path(__file__).resolve().parents[1]
pinned = (root/"vendor/sources/eden/src/dynarmic/src/dynarmic/backend/x64/constant_pool.cpp").read_text()
maintained = (root/"vendor/encore-active/eden-core/src/dynarmic/backend/x64/constant_pool.cpp").read_text()
selector = (root/"headless/jit-alias.cmake").read_text()
# Unified R23 C00/R2 now uses an indexed pool in addition to the
# independently reviewed writable alias. Replay the exact paired CPP ABI,
# rather than accepting any new content or removing the source check.
before = """    auto it = constant_info.find(constant);
    if (it == constant_info.end()) {
        ASSERT(insertion_point < pool.size());
        ConstantT& target_constant = pool[insertion_point];
        target_constant = constant;
        it = constant_info.insert({constant, &target_constant}).first;
        ++insertion_point;
    }
    return frame[code.rip + it->second];"""
after = """    // Track the slot index rather than a duplicate pointer. Retain the
    // PS5 W^X writable alias: never write constants directly into RX pages.
    const auto next_slot = constant_info.size();
    auto it = constant_info.find(constant);
    if (it == constant_info.end()) {
        ASSERT(next_slot < pool.size());
        const auto slot = static_cast<u32>(next_slot);
        ConstantT& target_constant = pool[slot];
        *reinterpret_cast<ConstantT*>(code.writableAddress(&target_constant)) = constant;
        it = constant_info.emplace(constant, slot).first;
    }
    return frame[code.rip + static_cast<void*>(&pool[it->second])];"""
assert pinned.count(before) == 1
assert maintained == pinned.replace(before, after), "Unreviewed native indexed constant pool drift"
header = (root / "vendor/encore-active/eden-core/include/dynarmic/backend/x64/constant_pool.h").read_text()
assert "::Common::unordered_map<ConstantT, u32, ConstantHash> constant_info;" in header
assert "std::span<ConstantT> pool;" in header
assert selector.count('set(EDEN_MAINTAINED_CONSTANT_POOL') == 1
assert 'target_sources(dynarmic PRIVATE "${EDEN_MAINTAINED_CONSTANT_POOL}")' in selector
assert 'list(FILTER alias_sources EXCLUDE REGEX' in selector
assert 'constant_pool\\\\.cpp$' in selector
assert 'write_derived("${PORT_BUILD_DIR}/constant_pool.cpp"' not in selector
assert 'file(READ "${PROJECT_SOURCE_DIR}/src/dynarmic/src/dynarmic/backend/x64/constant_pool.cpp"' not in selector
# Xbyak is now a complete Encore-maintained header. Preserve the
# actual COPYONLY selection rather than requiring the retired generator.
assert 'configure_file("${EDEN_MAINTAINED_XBYAK_HEADER}"' in selector
assert 'write_derived("${PORT_BUILD_DIR}/include/xbyak/xbyak.h"' not in selector
assert (root / "vendor/encore-active/eden-build/third_party/xbyak/xbyak.h").is_file()
print("VENDOR_MAINTAINED_CONSTANT_POOL_PARITY_PASS: exact edit and compiled target")
