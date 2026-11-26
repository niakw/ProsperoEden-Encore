#!/usr/bin/env python3
"""N50 exact source baseline: no second PS5 device-memory translation unit."""
from pathlib import Path
import hashlib

ROOT = Path(__file__).resolve().parents[2]
OWNER = ROOT / "vendor/encore-active/eden-core/overrides/core/device_memory_manager.inc"
HELPER = ROOT / "vendor/encore-active/ns2-helpers/include/core/ns2_egl_continuity_guard.h"
CMAKE = (ROOT / "headless/CMakeLists.txt").read_text()

def blob(t):
    b = t.encode()
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()

def once(t, old, new):
    assert t.count(old) == 1, ("N50 maintained source drift", old[:70])
    return t.replace(old, new)

t = OWNER.read_text()
# R457 renderer lifetime: reverse the exact reviewed delta on the audit copy only.
if blob(t) == "8acbdfe9ac970d24fecd334ca7b943f6bcd958f4":
    for newer, older in (
        ("#ifdef PS5_NATIVE\n#include \"core/hle/kernel/board/nintendo/nx/k_system_control.h\"\n#include \"gpu_fault_rate_limit.h\"\n#include \"core/native_renderer_lifetime.h\"\n#endif\n\nnamespace Core {\n", "#ifdef PS5_NATIVE\n#include \"core/hle/kernel/board/nintendo/nx/k_system_control.h\"\n#include \"gpu_fault_rate_limit.h\"\n#endif\n\nnamespace Core {\n"),
        ("    // renderer callback may itself gather translated GPU addresses.\n    lk.unlock();\n    if (replaced_gpu_mapping && device_inter != nullptr) {\n        const ::Eden::NativeRendererLifetime::MappingCallbackLease lease;\n        if (lease) {\n            device_inter->InvalidateRegion(address, size);\n            ::Eden::GpuFault::remap_cache_evictions.fetch_add(1, std::memory_order_relaxed);\n        }\n    }\n#endif\n}\n", "    // renderer callback may itself gather translated GPU addresses.\n    lk.unlock();\n    if (replaced_gpu_mapping && device_inter != nullptr) {\n        device_inter->InvalidateRegion(address, size);\n        ::Eden::GpuFault::remap_cache_evictions.fetch_add(1, std::memory_order_relaxed);\n    }\n#endif\n}\n"),
        ("#endif\n    size_t start_page_d = address >> Memory::YUZU_PAGEBITS;\n    size_t num_pages = Common::AlignUp(size, Memory::YUZU_PAGESIZE) >> Memory::YUZU_PAGEBITS;\n    {\n#ifdef PS5_NATIVE\n        const ::Eden::NativeRendererLifetime::MappingCallbackLease lease;\n        if (lease)\n#endif\n        device_inter->InvalidateRegion(address, size);\n    }\n    std::scoped_lock lk(mapping_guard);\n\n    tracked_entries.CommitRegion(start_page_d, start_page_d + num_pages); // should already be committed, but just in case\n", "#endif\n    size_t start_page_d = address >> Memory::YUZU_PAGEBITS;\n    size_t num_pages = Common::AlignUp(size, Memory::YUZU_PAGESIZE) >> Memory::YUZU_PAGEBITS;\n    device_inter->InvalidateRegion(address, size);\n    std::scoped_lock lk(mapping_guard);\n\n    tracked_entries.CommitRegion(start_page_d, start_page_d + num_pages); // should already be committed, but just in case\n"),
    ):
        assert t.count(newer) == 1
        t = t.replace(newer, older, 1)
    assert blob(t) == "daf493ce6e863397ec44bfae467c4f7533570477"
# Vendor #194's reviewed native FC27 publication is later than the N50
# source witness. Reverse exactly its three additions in this AUDIT COPY,
# then retain the original N50 source baseline checksum unchanged.
if blob(t) == "852a0272696c7ce182bc05aee92bc7cbb195446b":
    new_header = ROOT/"vendor/encore-active/eden-core/overrides/core/deferred_cached_updates.h"
    assert blob(new_header.read_text()) == "33262f511777cdd1b4a74ac0cd6dc39caa12c9d0"
    t = once(t, '#include "core/deferred_cached_updates.h"\n', '')
    wait_block = (
        "#ifdef PS5_NATIVE\n"
        "    // A guest CPU write may already have changed buffer-cache word state but\n"
        "    // deliberately publish its host page-protection decrement after dropping\n"
        "    // buffer_cache.mutex. InvalidateRegion orders us behind that cache lock;\n"
        "    // wait before removing backing so the deferred decrement cannot be lost\n"
        "    // against a later remap.\n"
        "    ::Eden::DeferredCachedUpdates::WaitForPublished();\n"
        "#endif\n"
    )
    batch_block = (
        "#ifdef PS5_NATIVE\n"
        "    if (auto* deferred = ::Eden::DeferredCachedUpdates::active_collector) {\n"
        "        if (delta < 0) {\n"
        "            if (deferred->TryAdd(\n"
        "                    this,\n"
        "                    [](void* owner, std::span<const ::Eden::DeferredCachedUpdates::Range> runs,\n"
        "                       s32 run_delta) {\n"
        "                        static_cast<DeviceMemoryManager<Traits>*>(owner)\n"
        "                            ->UpdatePagesCachedBatch(runs, run_delta);\n"
        "                    },\n"
        "                    ranges, delta)) {\n"
        "                return;\n"
        "            }\n"
        "        } else if (!deferred->Empty()) {\n"
        "            // Tracking must never lag behind the word state. Flush any older\n"
        "            // decrements synchronously before a +1/zero update, preserving the\n"
        "            // exact call order and falling back to the original locked path.\n"
        "            deferred->Flush();\n"
        "        }\n"
        "    }\n"
        "#endif\n"
    )
    t = once(t, wait_block, '')
    t = once(t, batch_block, '')
    assert blob(t) == "daf493ce6e863397ec44bfae467c4f7533570477", "FC27 native N50 reverse changed other code"
    print("FC27_N50_DEFERRED_PAGE_NATIVE_EXACT_REVERSE_PASS")
assert blob(t) == "daf493ce6e863397ec44bfae467c4f7533570477"
assert HELPER.is_file() and "CutContinuityAt(" in HELPER.read_text()
t = once(t,
    '#include "core/device_memory_manager.h"\n'
    '#ifdef EDEN_NS2_DEVICE_CONTINUITY\n'
    '#include "core/ns2_egl_continuity_guard.h"\n#endif',
    '#include "core/device_memory_manager.h"')
call = (
    "#ifdef EDEN_NS2_DEVICE_CONTINUITY\n"
    "    // End a previously tracked physical run before mapping state changes.\n"
    "    Eden::NS2::GpuMemory::CutContinuityAt(start_page_d,\n"
    "        [&](size_t index) { return AtomicLoadContinuity(tracked_entries[index]); },\n"
    "        [&](size_t index, u32 new_count) {\n"
    "            AtomicStoreContinuity(tracked_entries.GetUnchecked(index), new_count);\n"
    "        });\n"
    "#endif\n"
)
assert t.count(call) == 2
t = t.replace(call, "")
assert blob(t) == "5b30e44b9295e75b1e6719d97764d1a88c0bbc55", "N50 changed unrelated PS5 atomic/reverse-map code"
assert "option(EDEN_NS2_CONTINUITY_EXPERIMENTAL" not in CMAKE
assert "# N50: shared native PS5 device-memory contiguous page-run safety." in CMAKE
assert "if(PS5_NATIVE)" in CMAKE
assert "EDEN_NS2_DEVICE_CONTINUITY=1" in CMAKE
assert "headless/ns2/eglantine/core/device_memory_manager.inc" not in CMAKE
print("N50_NATIVE_DEVICE_MEMORY_SINGLE_VENDOR_OWNER_AND_BASELINE_PASS")
