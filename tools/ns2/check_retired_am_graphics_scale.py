#!/usr/bin/env python3
"""Prevent reintroduction of the unqualified NS2 AM graphics scale stub.

That prototype's command 60 supplied a hard-coded 10/1/1 success without
implementing Switch 2 display state or notifications. It was never selected
in final builds; removal is safer than preserving a non-working toggle.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
cmake = (ROOT / "headless/CMakeLists.txt").read_text()
script = (ROOT / "tools/build-headless-native.sh").read_text()
research = (ROOT / ".github/workflows/ns2-native-ps5-research.yml").read_text()
host = (ROOT / ".github/workflows/ns2-research-host.yml").read_text()
retired = ROOT / "vendor/encore-active/ns2-runtime/am/core/hle/service/am/service"
for name in ("application_proxy.cpp", "application_proxy.h",
             "graphics_scaling_parameters_functions.cpp",
             "graphics_scaling_parameters_functions.h"):
    assert not (retired / name).exists(), "Obsolete graphics scaling source still active: " + name

assert "EDEN_NS2_GRAPHICS_SCALE_EXPERIMENTAL" not in cmake
# The single shipping product no longer offers any retired research selector.
assert "EDEN_NS2_GRAPHICS_SCALE_EXPERIMENTAL" not in script
assert "EDEN_NS2_SPARSE_QUEUE_EXPERIMENTAL" not in script
assert "EDEN_NS2_GRAPHICS_SCALE_EXPERIMENTAL" not in research
assert "graphics_scaling_parameters_functions" not in host
assert "EDEN_SHARED_NS2_AM" in cmake
assert "EDEN_NS2_AM_ROOT}/core/hle/service/am/service/application_functions.cpp" in cmake
# The pinned proxy owner must remain the real input for all other AM calls.
proxy = ROOT / "vendor/sources/eden/src/core/hle/service/am/service/application_proxy.cpp"
assert proxy.is_file()
assert "IApplicationProxy::IApplicationProxy" in proxy.read_text()
assert "GetGraphicsScalingParameters" not in proxy.read_text()
print("P0_2_AM_GRAPHICS_SCALE_STUB_RETIRED_PASS false_success=removed "
      "shared_AM320=preserved pinned_proxy=preserved")
