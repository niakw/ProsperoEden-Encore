#!/usr/bin/env python3
"""Pin exact selected NS2 self-controller command 240 C++/header ABI pairing."""
from pathlib import Path
import hashlib
root = Path(__file__).resolve().parents[2]
base = root / "vendor/encore-active/ns2-runtime/self_controller/core/hle/service/am/service/self_controller.h"
cpp = root / "vendor/encore-active/ns2-runtime/self_controller/core/hle/service/am/service/self_controller.cpp"
selected = root / "headless/r23_self_controller_240_ps5.h"
cm = (root / "headless/CMakeLists.txt").read_text()
def blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + bytes([0]) + data).hexdigest()
original = base.read_text()
s = selected.read_text()
needle = "    Result Unknown230(u32 in_val, Out<u16> out_val);\n"
extra = "    Result Unknown240(u32 in_val);\n"
comment = "// Selected PS5 NS1/NS2 SelfController ABI header; exact vendor base + command 240.\n"
assert blob(base.read_bytes()) == "b7762da79b357e34adf096da3574c9cd130943f9"
# The selected vendor already carries command 240 exactly once.
# Preserve that ABI unchanged; do not add another declaration to an
# already-integrated base header or silently discard the selected overlay.
assert original.count(needle) == 1
assert original.count(extra) == 1
assert s == comment + original
assert s.count(extra) == 1
implementation = cpp.read_text()
assert implementation.count("Result ISelfController::Unknown240(u32 in_val)") == 1
assert implementation.count("D<&ISelfController::Unknown240>") == 1
assert "r23_self_controller_240_ps5.h" in cm
assert "target_include_directories(core BEFORE PRIVATE" in cm
assert "EDEN_R23_SELF_CONTROLLER_INCLUDE" in cm
assert "EDEN_NS2_SELF_ROOT" in cm and "self_controller.cpp" in cm
print("NS2_SELF_CONTROLLER_240_SELECTED_HEADER_AND_CPP_SOURCE_PASS one_CPP=1 owner=matched")
