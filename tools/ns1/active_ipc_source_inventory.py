#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Count physical IPC FunctionInfo slots in the final native PS5 service graph.

The Eden CMake list is only the starting graph. headless/CMakeLists.txt replaces
several service translation units for the one shared NS1/NS2 PS5 binary and
adds a small set of native service owners. This inventory follows those final
owners rather than counting an intermediate staged source tree.

Physical handler slots are not proof of firmware reachability or functional
emulation. Explicit rejects remain handlers and are reported as such.
"""
from collections import Counter
from pathlib import Path
import json
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
VENDOR = ROOT / "vendor"
ACTIVE = VENDOR / "encore-active/eden-backports"
ORIGINAL = VENDOR / "sources/eden"
CM = ACTIVE / "src/core/CMakeLists.txt"
HEADLESS = ROOT / "headless/CMakeLists.txt"
ENTRIES = json.loads((ACTIVE / "manifest.json").read_text())["entries"]

SELECTED = sorted(set(re.findall(
    r"^\s*(hle/service/[\w./-]+\.cpp)\s*$", CM.read_text(), re.M)))
if len(SELECTED) < 300:
    raise SystemExit(f"NS1 native CMake service source list missing: {len(SELECTED)}")

# Final replacements made by headless/CMakeLists.txt which can own physical
# FunctionInfo tables. Entries with no tables are harmless to omit here.
FINAL_OVERRIDES = {
    "src/core/hle/service/aoc/addon_content_manager.cpp":
        VENDOR / "encore-active/eden-core/src/core/hle/service/aoc/addon_content_manager.cpp",
    "src/core/hle/service/audio/audio.cpp":
        ROOT / "headless/r23_audren_debug_ps5.cpp",
    "src/core/hle/service/bcat/delivery_cache_file_service.cpp":
        ROOT / "headless/r23_bcat_delivery_cache_file_ps5.cpp",
    "src/core/hle/service/am/service/application_functions.cpp":
        VENDOR / "encore-active/ns2-runtime/am/core/hle/service/am/service/application_functions.cpp",
    "src/core/hle/service/am/service/application_proxy.cpp":
        VENDOR / "encore-active/ns2-runtime/hle/core/hle/service/am/service/application_proxy.cpp",
    "src/core/hle/service/am/service/application_proxy_service.cpp":
        VENDOR / "encore-active/ns2-runtime/hle/core/hle/service/am/service/application_proxy_service.cpp",
    "src/core/hle/service/am/service/self_controller.cpp":
        VENDOR / "encore-active/ns2-runtime/self_controller/core/hle/service/am/service/self_controller.cpp",
    "src/core/hle/service/hid/hid_server.cpp":
        VENDOR / "encore-active/ns2-runtime/hle/core/hle/service/hid/hid_server.cpp",
    "src/core/hle/service/friend/friend.cpp":
        VENDOR / "encore-active/ns2-runtime/gamechat/core/hle/service/friend/friend.cpp",
    "src/core/hle/service/ns/platform_service_manager.cpp":
        VENDOR / "encore-active/ns2-runtime/font_service/core/hle/service/ns/platform_service_manager.cpp",
    "src/core/hle/service/ssl/ssl.cpp":
        VENDOR / "encore-active/eden-core/src/core/hle/service/ssl/ssl.cpp",
    "src/core/hle/service/sockets/bsd.cpp":
        VENDOR / "encore-active/eden-core/src/core/hle/service/sockets/bsd.cpp",
    "src/core/hle/service/sockets/sfdnsres.cpp":
        VENDOR / "encore-active/eden-core/src/core/hle/service/sockets/sfdnsres.cpp",
    "src/core/hle/service/filesystem/fsp/fs_i_storage.cpp":
        VENDOR / "encore-active/eden-core/src/core/hle/service/filesystem/fsp/fs_i_storage.cpp",
}

# Native service TUs appended after the Eden core target is created. Only
# additions that physically contain FunctionInfo tables belong in this count.
FINAL_ADDITIONS = [
    ("hle/service/am/service/gpu_session.cpp",
     VENDOR / "encore-active/ns2-runtime/gpu_session/core/hle/service/am/service/gpu_session.cpp"),
    ("hle/service/am/service/gpu_worker.cpp",
     VENDOR / "encore-active/ns2-runtime/gpu_session/core/hle/service/am/service/gpu_worker.cpp"),
    ("hle/service/am/service/graphics_video_decoder_session.cpp",
     VENDOR / "encore-active/ns2-runtime/video_decoder/core/hle/service/am/service/graphics_video_decoder_session.cpp"),
    ("hle/service/am/service/graphics_supervisor.cpp",
     VENDOR / "encore-active/ns2-runtime/graphics_supervisor/core/hle/service/am/service/graphics_supervisor.cpp"),
]

headless_text = HEADLESS.read_text()
for marker in (
    "set(EDEN_REVIEWED_DUAL_NPDM ON)",
    "r23_audren_debug_ps5.cpp",
    "r23_bcat_delivery_cache_file_ps5.cpp",
    "hle/service/aoc/addon_content_manager.cpp",
    "encore-active/eden-core/src/core/hle/service/ssl",
    "encore-active/eden-core/src/core/hle/service/sockets/bsd.cpp",
    "encore-active/ns2-runtime/gamechat",
    "encore-active/ns2-runtime/font_service",
    "encore-active/ns2-runtime/gpu_session",
    "encore-active/ns2-runtime/graphics_supervisor",
):
    if marker not in headless_text:
        raise SystemExit(f"Final PS5 service-owner marker missing from headless CMake: {marker}")

TABLE = re.compile(r"\bFunctionInfo\s+\w+\s*\[\s*\]\s*=\s*\{")
ENTRY = re.compile(r'^\s*\{\s*(\d+)\s*,\s*([^,\n]+),\s*"([^"]+)"', re.M)

owners = []
for rel in SELECTED:
    native_rel = "src/core/" + rel
    if native_rel in FINAL_OVERRIDES:
        chosen = FINAL_OVERRIDES[native_rel]
        origin = "final_override"
    else:
        chosen = (ACTIVE if native_rel in ENTRIES else ORIGINAL) / native_rel
        origin = "backport" if native_rel in ENTRIES else "original"
    owners.append((rel, native_rel, chosen, origin))

base_logical = {rel for rel, _, _, _ in owners}
for rel, chosen in FINAL_ADDITIONS:
    if rel in base_logical:
        raise SystemExit(f"Final PS5 IPC addition duplicates base owner: {rel}")
    owners.append((rel, "additive:" + rel, chosen, "final_addition"))

by_owner = []
missing = []
total = Counter()
for rel, native_rel, chosen, origin in owners:
    if not chosen.is_file():
        missing.append(f"{native_rel} -> {chosen}")
        continue
    body = chosen.read_text(errors="replace")
    tables = list(TABLE.finditer(body))
    cmd_rows = []
    for table in tables:
        end = body.find("};", table.end())
        if end == -1:
            raise SystemExit(f"Unterminated FunctionInfo owner: {native_rel} -> {chosen}")
        cmd_rows.extend(ENTRY.findall(body[table.end():end]))
    nulls = [(cmd, name) for cmd, handler, name in cmd_rows
             if handler.strip() == "nullptr"]
    if cmd_rows:
        family = rel.split("/")[2]
        by_owner.append((rel, family, len(tables), len(cmd_rows), len(nulls), origin, chosen))
    total["physical_slots"] += len(cmd_rows)
    total["physical_nulls"] += len(nulls)
    total["tables"] += len(tables)
    total["source_owners"] += 1
    total["final_overrides"] += int(origin == "final_override")
    total["final_additions"] += int(origin == "final_addition")

if missing:
    raise SystemExit("Final PS5 selected files have no resolvable owner: " + ", ".join(missing))
if not by_owner or total["physical_slots"] < 6500:
    raise SystemExit(
        f"Final PS5 IPC parser did not enumerate full native graph: {total['physical_slots']} slots")

by_family = Counter()
for rel, family, tables, commands, nulls, origin, chosen in by_owner:
    by_family[family] += nulls

# Source-graph sentinels. These are physical table contracts, not functional
# firmware claims. They catch a late CMake replacement silently regressing to
# an older service owner.
expected_final = {
    "hle/service/aoc/addon_content_manager.cpp": (1, 22, 4),
    "hle/service/am/service/application_functions.cpp": (1, 74, 1),
    "hle/service/am/service/application_proxy.cpp": (1, 15, 0),
    "hle/service/am/service/application_proxy_service.cpp": (1, 3, 0),
    "hle/service/am/service/self_controller.cpp": (1, 66, 0),
    "hle/service/hid/hid_server.cpp": (1, 234, 33),
    "hle/service/friend/friend.cpp": (6, 164, 0),
    "hle/service/ns/platform_service_manager.cpp": (2, 22, 0),
    "hle/service/ssl/ssl.cpp": (4, 76, 14),
    "hle/service/sockets/bsd.cpp": (3, 69, 6),
    "hle/service/sockets/sfdnsres.cpp": (2, 19, 0),
    "hle/service/audio/audio.cpp": (10, 44, 0),
    "hle/service/audio/audio_controller.cpp": (1, 60, 0),
    "hle/service/bcat/delivery_cache_file_service.cpp": (1, 4, 0),
    "hle/service/am/service/gpu_session.cpp": (1, 21, 0),
    "hle/service/am/service/gpu_worker.cpp": (1, 14, 0),
    "hle/service/am/service/graphics_video_decoder_session.cpp": (1, 17, 0),
    "hle/service/am/service/graphics_supervisor.cpp": (5, 186, 0),
}
actual = {rel: (tables, commands, nulls)
          for rel, family, tables, commands, nulls, origin, chosen in by_owner}
for rel, expected in expected_final.items():
    if actual.get(rel) != expected:
        raise SystemExit(
            f"Final PS5 IPC owner drift: {rel} expected={expected} actual={actual.get(rel)}")

es = [x for x in by_owner if x[0] == "hle/service/es/es.cpp"]
if len(es) != 1 or es[0][2] != 3 or es[0][3] != 153 or es[0][4] > 63:
    raise SystemExit(f"ES/NDRM owner regression or parser drift: {es}")

pin = subprocess.check_output(
    ["git", "-C", str(VENDOR), "rev-parse", "HEAD"], text=True).strip()
print("NS1_FINAL_PS5_IPC_INVENTORY",
      f"vendor={pin}",
      f"base_cmake_cpp={len(SELECTED)}",
      f"final_source_owners={total['source_owners']}",
      f"owners_with_tables={len(by_owner)}",
      f"tables={total['tables']}",
      f"physical_slots={total['physical_slots']}",
      f"physical_nulls={total['physical_nulls']}",
      f"physical_handlers={total['physical_slots'] - total['physical_nulls']}",
      f"final_overrides={total['final_overrides']}",
      f"final_additions={total['final_additions']}",
      "firmware_reachability=NOT_PROVEN")
for rel, family, tables, count, nulls, origin, chosen in sorted(
        by_owner, key=lambda x: (-x[4], x[0]))[:40]:
    print(
        f"NS1_IPC_NULL_OWNER remaining={nulls} total={count} tables={tables} "
        f"origin={origin} source={rel} physical={chosen.relative_to(ROOT)}")
print("NS1_IPC_NULL_FAMILY_TOP32", json.dumps(
    by_family.most_common(32), ensure_ascii=False))
