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
assert blob(t) == "b0786ea0a9f993b5804fe92cfbd5ee4c565320ac"
assert HELPER.is_file() and "CutContinuityAt(" in HELPER.read_text()
t = once(t,
    '#include "core/device_memory_manager.h"\n'
    '#ifdef EDEN_NS2_DEVICE_CONTINUITY\n'
    '#include "core/ns2_egl_continuity_guard.h"\n#endif',
    '#include "core/device_memory_manager.h"')
call = (
    "#ifdef EDEN_NS2_DEVICE_CONTINUITY\n"
    "    // End a previously tracked physical run before mapping state changes.\n"
    "    Eden::NS2::Eglantine::CutContinuityAt(start_page_d,\n"
    "        [&](size_t index) { return AtomicLoadContinuity(tracked_entries[index]); },\n"
    "        [&](size_t index, u32 new_count) {\n"
    "            AtomicStoreContinuity(tracked_entries.GetUnchecked(index), new_count);\n"
    "        });\n"
    "#endif\n"
)
assert t.count(call) == 2
t = t.replace(call, "")
assert blob(t) == "5b30e44b9295e75b1e6719d97764d1a88c0bbc55", "N50 changed unrelated PS5 atomic/reverse-map code"
assert "EDEN_NS2_CONTINUITY_EXPERIMENTAL OR" in CMAKE
assert "EDEN_NS2_DEVICE_CONTINUITY=1" in CMAKE
assert "headless/ns2/eglantine/core/device_memory_manager.inc" not in CMAKE
print("N50_NATIVE_DEVICE_MEMORY_SINGLE_VENDOR_OWNER_AND_BASELINE_PASS")
