#!/usr/bin/env python3
"""Three-way Lichii/Eglantine baseline: validate selected Encore owners without changing NS1."""
from __future__ import annotations
import hashlib
import re
import subprocess
from pathlib import Path

R = Path(__file__).resolve().parents[2]
V = R / "vendor"
assert V.is_dir(), "Initialize exact pinned vendor submodule before running this source gate"
pinned = subprocess.check_output(["git", "rev-parse", "HEAD:vendor"], cwd=R, text=True).strip()
head = subprocess.check_output(["git", "-C", str(V), "rev-parse", "HEAD"], text=True).strip()
assert pinned == head, f"incorrect vendor owner: {pinned} != {head}"
cmake = (R / "headless/CMakeLists.txt").read_text()
for token in (
    "set(EDEN_REVIEWED_DUAL_NPDM OFF)",
    "if(PS5_NATIVE AND EDEN_REVIEWED_DUAL_NPDM)",
    "set(EDEN_SHARED_NS2_AM OFF)",
    "EDEN_NS2_SERVICE_PARITY_ROOT",
    "EDEN_NS2_EARLY_HLE_ROOT",
    "EDEN_NS2_AM_ROOT",
    "EDEN_NS2_KERNEL_ROOT",
    "EDEN_NS2_KPROCESS_SOURCE",
    "EDEN_NS2_METADATA_OVERLAY",
    "EDEN_NS2_NVDRV_AS_ROOT",
    "EDEN_R23_APPLET_WINDOW_SOURCE",
):
    assert token in cmake, ("CMake native owner selector", token)

prefix = "encore-active/eden/src/core/hle/service/"
owners = {
    "am": ("encore-active/eden/src/core/hle/service/am/service/application_functions.cpp", 1, 74),
    "hid": (prefix+"hid/hid_server.cpp", 1, 235),
    "nifm": (prefix+"nifm/nifm.cpp", 5, 86),
    "acc": (prefix+"acc/acc.cpp", 24, 505),
    "caps_u": (prefix+"caps/caps_u.cpp", 1, 23),
    "caps_su": (prefix+"caps/caps_su.cpp", 1, 5),
    "set": (prefix+"set/settings_server.cpp", 1, 18),
    "mii": (prefix+"mii/mii.cpp", 3, 44),
    "lm": (prefix+"lm/lm.cpp", 3, 10),
    "audio_device": (prefix+"audio/audio_device.cpp", 1, 22),
    "audio_renderer": (prefix+"audio/audio_renderer_manager.cpp", 1, 5),
    "fsp": ("encore-active/eden/src/core/hle/service/filesystem/fsp/fsp_srv.cpp", 1, 134),
}
files = {}
summary = {}
for kind, (rel, expected_tables, expected_rows) in owners.items():
    data = (V / rel).read_bytes()
    src = data.decode("utf-8")
    files[kind] = src
    tables = []
    for match in re.finditer(r"\bFunctionInfo\s+functions\[\]\s*=\s*\{", src):
        end = src.find("};", match.end())
        assert end >= 0, (kind, "unterminated FunctionInfo")
        records = [
            (int(m.group(1)), m.group(2).strip(), m.group(3))
            for m in re.finditer(r'\{\s*(\d+)\s*,\s*([^,\n]*?),\s*"([^"]+)"', src[match.end():end])
        ]
        assert len({r[0] for r in records}) == len(records), (kind, "duplicate ID in one table")
        tables.append(records)
    total = sum(map(len, tables))
    assert (len(tables), total) == (expected_tables, expected_rows), (
        kind, len(tables), total, expected_tables, expected_rows)
    summary[kind] = (len(tables), total)
assert "ScratchSystemAccount" not in files["acc"], "Re-audit conditional scratch profile ownership"
assert '{2, &ILogger::TransmitHashedLog, "TransmitHashedLog"}' in files["lm"]
assert "if (process && (process->GetProgramId() >> 56) == 0x04)" in files["lm"]
assert "IPC::ResponseBuilder rb{ctx, 2};" in files["lm"]
# The selected FSP owner now intentionally layers reviewed NS1/HOS additions
# on top of the earlier Eglantine baseline. Pin the structural additions
# directly instead of requiring the obsolete whole-file blob.
for token in (
    '{10, D<&FSP_SRV::OpenFileSystemWithId>, "OpenFileSystemWithId"}',
    '{207, D<&FSP_SRV::OpenDataFileSystemByDataId>, "OpenDataFileSystemByDataId"}',
    '{211, D<&FSP_SRV::OpenDataStorageByProgramIdForBatchRead>, "OpenDataStorageByProgramIdForBatchRead"}',
    '{212, D<&FSP_SRV::OpenDataStorageWithProgramIndexForBatchRead>, "OpenDataStorageWithProgramIndexForBatchRead"}',
    '{213, D<&FSP_SRV::OpenDataStorageByPathForBatchRead>, "OpenDataStorageByPathForBatchRead"}',
    '{618, D<&FSP_SRV::GetProgramIdByPath>, "GetProgramId"}',
):
    assert token in files["fsp"], ("Reviewed FSP convergence drift", token)
w = (V / "encore-active/eden/src/core/hle/service/am/window_system.cpp").read_text()
h = (V / "sources/eden/src/core/hle/service/am/window_system.h").read_text()
desktop = (V / "sources/eden/src/core/hle/service/am/window_system.cpp").read_text()
assert "if (m_applets.empty() && !m_exit_sent)" in w
assert "m_exit_sent = true;" in w
assert "bool m_exit_sent{};" in h
assert "if (m_applets.empty())" in desktop
assert "m_exit_sent" not in desktop
assert "z_index = this->IsOverlayOpenLocked(*applet) ? Overlay : Background;" in w
npdm = (V / "encore-active/eden/src/core/file_sys/program_metadata.cpp").read_text()
kp = (V / "encore-active/eden/src/core/hle/kernel/k_process.cpp").read_text()
assert "Eden::NS2::FindAcidBody(" in npdm
assert "uses_extended_acid = false;" in npdm and "is_switch2 = false;" in npdm
assert "if (metadata.IsSwitch2())" in kp
assert "m_page_table.GetHeapRegionSize() + m_page_table.GetAliasRegionSize()" in kp
print("NS2_THREE_WAY_SELECTED_OWNER_SOURCE_PASS vendor=" + pinned[:12] +
      " tables=" + str(sum(x[0] for x in summary.values())) +
      " rows=" + str(sum(x[1] for x in summary.values())) +
      " fsp_reviewed_convergence=1 lm_ns1_abi_retained=1 window_ns1_overlay_retained=1")
