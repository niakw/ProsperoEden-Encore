#!/usr/bin/env python3
"""FW23 command23: verify the *installed* native source; never override it.

E1 source/host-only proof, NOT native PS5 ELF or guest HIPC execution.
The old isolated one-line research file shadowed shipping #128 icon guards.
"""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
original = ROOT / "vendor/sources/eden/src/core/hle/service/ns/read_only_application_control_data_interface.cpp"
shipping = ROOT / "vendor/encore-active/eden-backports/src/core/hle/service/ns/read_only_application_control_data_interface.cpp"
cmake = (ROOT / "headless/CMakeLists.txt").read_text()
prepare = (ROOT / "tools/prepare-build.sh").read_text()
manifest = json.loads((ROOT / "vendor/encore-active/eden-backports/manifest.json").read_text())

def git_blob(path: Path) -> str:
    b = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(b)).encode() + b"\0" + b).hexdigest()

assert git_blob(original) == "c7606a83bf771c9251ef8a44add72b72a2589870"
assert git_blob(shipping) == "1359cdbb9507fb7c22ca57459a0a03ab95e58f2f"
assert "src/core/hle/service/ns/read_only_application_control_data_interface.cpp" in manifest["entries"]
assert 'install-vendored-eden-backports.py --repair-owned-cache' in prepare

cmd23 = '{23, D<&IReadOnlyApplicationControlDataInterface::GetApplicationControlData3>'
cmd19 = '{19, D<&IReadOnlyApplicationControlDataInterface::GetApplicationControlData3>'
icon_guard = 'if (const auto control = pm.GetControlMetadata(); control.second)'
old, active = original.read_text(), shipping.read_text()
assert cmd19 in old and cmd23 not in old
assert active.count(cmd19) == 1 and active.count(cmd23) == 1
assert icon_guard not in old and active.count(icon_guard) >= 2
assert 'research/r23/fw23_ns_application_control_ps5.cpp' not in cmake
assert 'EDEN_FW23_NS_CMD23_SOURCE' not in cmake
for token in (cmd23, icon_guard, 'eden_r23_fw23_ns_prepared',
              'Selected FW23 NS source lost installed cmd23 or icon null guard'):
    assert token in cmake, token
print("R457_FW23_NS23_SELECTED_SHIPPING_BACKPORT_AND_ICON_GUARDS_PASS")
