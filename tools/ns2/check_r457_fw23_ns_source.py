#!/usr/bin/env python3
"""R23 #147 FW23: check exact pinned maintained NS HLE source + CMake owner.

Source/host-only structural gate, NOT a genuine PS5 IPC test or ELF compile.
The full maintained original is copied byte-for-byte except a single cmd23
dispatch-table entry to precisely the same existing cmd19 handler.
"""
from pathlib import Path
import subprocess
import re
ROOT=Path(__file__).resolve().parents[2]
original=ROOT/"vendor/sources/eden/src/core/hle/service/ns/read_only_application_control_data_interface.cpp"
modified=ROOT/"headless/fw23_ns_application_control_ps5.cpp"
cmake=(ROOT/"headless/CMakeLists.txt").read_text()
original_sha=subprocess.check_output(["git","hash-object",str(original)],text=True).strip()
assert original_sha=="c7606a83bf771c9251ef8a44add72b72a2589870",original_sha
a=original.read_text()
b=modified.read_text()
line='        {19, D<&IReadOnlyApplicationControlDataInterface::GetApplicationControlData3>, "GetApplicationControlData"},\n'
line23='        {23, D<&IReadOnlyApplicationControlDataInterface::GetApplicationControlData3>, "GetApplicationControlData"},\n'
assert a.count(line)==1 and line23 not in a
assert b==a.replace(line,line+line23),"Nontrivial NS semantics changed"
assert b.count(line23)==1
assert re.search(r"if\(PS5_NATIVE\).*?EDEN_FW23_NS_CMD23_SOURCE.*?set_property\(TARGET core PROPERTY SOURCES",cmake,re.S)
assert cmake.count('hle/service/ns/read_only_application_control_data_interface.cpp')>=2
assert "EDEN_FW23_NS_CMD23_SOURCE" in cmake
print("R457_FW23_NS_CMD23_EXACT_SINGLE_LINE_OWNER_PASS host/source only")
