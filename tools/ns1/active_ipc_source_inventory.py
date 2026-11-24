#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Count native NS1 IPC FunctionInfo slots in the CMake-selected Eden owners.

The dated SwitchBrew reference is incomplete. These are physical declarations,
not proof of reachable commands, matching Horizon ABI or PS5 gameplay.
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
ENTRIES = json.loads((ACTIVE / "manifest.json").read_text())["entries"]

SELECTED = sorted(set(re.findall(
    r"^\\s*(hle/service/[\\w./-]+\\.cpp)\\s*$", CM.read_text(), re.M)))
if len(SELECTED) < 300:
    raise SystemExit(f"NS1 native CMake service source list missing: {len(SELECTED)}")

TABLE = re.compile(r"\\bFunctionInfo\\s+\\w+\\s*\\[\\s*\\]\\s*=\\s*\\{")
ENTRY = re.compile(r'^\\s*\\{\\s*(\\d+)\\s*,\\s*([^,\\n]+),\\s*"([^"]+)"', re.M)
by_owner = []
missing = []
total = Counter()
for rel in SELECTED:
    native_rel = "src/core/" + rel
    chosen = (ACTIVE if native_rel in ENTRIES else ORIGINAL) / native_rel
    if not chosen.is_file():
        missing.append(native_rel)
        continue
    body = chosen.read_text(errors="replace")
    tables = list(TABLE.finditer(body))
    cmd_rows = []
    for table in tables:
        end = body.find("};", table.end())
        if end == -1:
            raise SystemExit(f"Unterminated FunctionInfo owner: {native_rel}")
        cmd_rows.extend(ENTRY.findall(body[table.end():end]))
    nulls = [(cmd, name) for cmd, handler, name in cmd_rows
             if handler.strip() == "nullptr"]
    if cmd_rows:
        family = rel.split("/")[2]
        by_owner.append((rel, family, len(tables), len(cmd_rows), len(nulls)))
    total["physical_slots"] += len(cmd_rows)
    total["physical_nulls"] += len(nulls)
    total["tables"] += len(tables)
    total["native_source_files"] += 1
    total["maintained_source_files"] += int(native_rel in ENTRIES)

if missing:
    raise SystemExit("NS1 selected files have no resolvable owner: " + ", ".join(missing))
if not by_owner or total["physical_slots"] < 1200:
    raise SystemExit("NS1 IPC parser did not enumerate selected source tables")

by_family = Counter()
for rel, family, tables, commands, nulls in by_owner:
    by_family[family] += nulls
es = [x for x in by_owner if x[0] == "hle/service/es/es.cpp"]
if len(es) != 1 or es[0][4] != 63:
    raise SystemExit(f"ES/NDRM physical count mismatch; parser or owner drift: {es}")

pin = subprocess.check_output(
    ["git", "-C", str(VENDOR), "rev-parse", "HEAD"], text=True).strip()
print("NS1_SELECTED_NATIVE_IPC_INVENTORY",
      f"vendor={pin}",
      f"cmake_cpp={len(SELECTED)}",
      f"owners_with_tables={len(by_owner)}",
      f"tables={total['tables']}",
      f"physical_slots={total['physical_slots']}",
      f"physical_nulls={total['physical_nulls']}",
      f"physical_handlers={total['physical_slots'] - total['physical_nulls']}",
      f"maintained_cpp={total['maintained_source_files']}",
      "firmware_reachability=NOT_PROVEN")
for rel, family, tables, count, nulls in sorted(
        by_owner, key=lambda x: (-x[4], x[0]))[:32]:
    print(f"NS1_IPC_NULL_OWNER remaining={nulls} total={count} tables={tables} source={rel}")
print("NS1_IPC_NULL_FAMILY_TOP32", json.dumps(
    by_family.most_common(32), ensure_ascii=False))
