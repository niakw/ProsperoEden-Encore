#!/usr/bin/env python3
"""R23 #95 source policy: active HID Connect branch versus Eden upstream.

No PS5, NPad or real controller API exercised. Read-only source + truth table.
"""
from __future__ import annotations
import itertools
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "vendor/encore-active/eden-core/src/hid_core/frontend/emulated_controller.cpp"
HDR = ROOT / "vendor/sources/eden/src/hid_core/frontend/emulated_controller.h"
CMAKE = ROOT / "headless/CMakeLists.txt"

def pinned(is_connected, handheld, slot, player_enabled, seen_slot):
    if is_connected:
        return False
    if handheld:
        return slot == "Handheld"
    if slot == "Player1":
        return True
    return player_enabled and not seen_slot

def upstream(is_connected, handheld, slot, player_enabled, seen_slot):
    # Eden 87d2f03c39bc: if (player.connected) { Connect(); }
    return player_enabled

def main():
    code = SRC.read_text()
    cmake = CMAKE.read_text()
    header = HDR.read_text()
    begin, end = "void EmulatedController::SetButton(", "void EmulatedController::SetStick("
    assert code.count(begin) == 1 and code.count(end) == 1
    body = code.split(begin, 1)[1].split(end, 1)[0]
    required = (
        "if (!is_connected) {",
        "npad_type == NpadStyleIndex::Handheld",
        "npad_id_type == NpadIdType::Handheld",
        "npad_id_type == NpadIdType::Player1",
        "player.connected && !controller_connected[player_index]",
        "controller_connected[player_index] = true;",
    )
    assert all(token in body for token in required)
    assert "HIDCore::available_controllers> controller_connected" in header
    assert "eden-core/src/hid_core/frontend/emulated_controller.cpp" in cmake
    assert "list(APPEND controller_sources" in cmake
    assert "EDEN_MAINTAINED_RUMBLE_CONTROLLER" in cmake
    cases = list(itertools.product((False, True), (False, True),
                                   ("Handheld", "Player1", "Player2"),
                                   (False, True), (False, True)))
    changed = [(values, pinned(*values), upstream(*values))
               for values in cases if pinned(*values) != upstream(*values)]
    assert len(cases) == 48 and changed
    assert pinned(False, True, "Handheld", False, False)
    assert not upstream(False, True, "Handheld", False, False)
    assert not pinned(True, False, "Player1", True, False)
    assert upstream(True, False, "Player1", True, False)
    print("R23_HID_CONNECT_BRANCH_SOURCE_DIFFERENCE_PASS",
          f"cases={len(cases)}", f"changed={len(changed)}",
          "console_runtime_verified=false")

if __name__ == "__main__":
    main()
