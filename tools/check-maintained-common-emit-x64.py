#!/usr/bin/env python3
"""Pin common x64 Patch()/Unpatch() implementation and native perf-map removal."""
from pathlib import Path
import hashlib
import shutil
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
active = root / "vendor/encore-active/eden/src/dynarmic/src/dynarmic/backend/x64"
pinned = root / "vendor/sources/eden/src/dynarmic/src/dynarmic/backend/x64/emit_x64.cpp"
cmake = (root / "headless/CMakeLists.txt").read_text()
old = pinned.read_text()
host = (active / "emit_x64_host.cpp").read_text()
native = (active / "emit_x64_native.cpp").read_text()
lookup = "    const PatchInformation& patch_info = patch_information[target_desc];"
fixed = (
    "    const auto patch = patch_information.find(target_desc);\n"
    "    if (patch == patch_information.end()) return;\n"
    "    const PatchInformation& patch_info = patch->second;"
)
perf = "    PerfMapRegister(entrypoint, code.getCurr(), LocationDescriptorToFriendlyName(descriptor));"
assert old.count(lookup) == old.count(perf) == 1
before_invalid = "void EmitX64::EmitInvalid(EmitContext&, IR::Inst* inst) {\n    UNREACHABLE();\n}"
after_invalid = "void EmitX64::EmitInvalid(EmitContext&, IR::Inst*) {\n    UNREACHABLE();\n}"
expected_host = old.replace(lookup, fixed)
host_blob = hashlib.sha1(
    b"blob " + str(len(host.encode())).encode() + bytes([0]) + host.encode()
).hexdigest()
if host_blob == "1a7a1516afe196a64f646a3daf6d180d87d22048":
    assert expected_host.count(before_invalid) == 1
    expected_host = expected_host.replace(before_invalid, after_invalid, 1)
    subprocess.run(["python3", "-B", str(root / "vendor/tests/r457_native_emit_invalid_warning_host.py")],
                   check=True, timeout=120)
else:
    assert host_blob == "b2ec3288f0b4d939422ff70d5a3716d722e6b842", "Unreviewed host emitter blob"
assert host == expected_host, "common emitter exact source drift"
empty_invalidation = "void EmitX64::InvalidateBasicBlocks(const ::Common::unordered_set<IR::LocationDescriptor>& locations) {\n    code.EnableWriting();"
guarded_invalidation = "void EmitX64::InvalidateBasicBlocks(const ::Common::unordered_set<IR::LocationDescriptor>& locations) {\n    // Unmapped guest writes often invalidate no compiled code. Do not flip\n    // RX/RW permissions when there are no machine instructions to patch.\n    if (locations.empty()) return;\n    code.EnableWriting();"
expected_native = host.replace(perf, "")
assert expected_native.count(empty_invalidation) == 1
expected_native = expected_native.replace(empty_invalidation, guarded_invalidation)
# Vendor #135 applies the same ABI-neutral unused-name cleanup to both
# maintained host/native definitions. The pinned upstream source remains immutable.
raw_native = (active / "emit_x64_native.cpp").read_bytes()
native_blob = hashlib.sha1(b"blob " + str(len(raw_native)).encode() + bytes([0]) + raw_native).hexdigest()
if native_blob == "46dfa1e0da81d15d5e6a0e5b6020dbf51c84b4ef":
    # expected_native is derived from the selected host. Older host graphs
    # still name the parameter, while vendor #135 already has the cleaned form.
    if expected_native.count(before_invalid) == 1:
        expected_native = expected_native.replace(before_invalid, after_invalid, 1)
    else:
        assert expected_native.count(after_invalid) == 1
    subprocess.run(["python3", "-B", str(root / "vendor/tests/r457_native_emit_invalid_warning_host.py")],
                   check=True, timeout=120)
else:
    assert native_blob == "205aa034f0ec2330aec5a81a628ce3ae326856ab", "Unreviewed native emitter blob"
    if expected_native.count(after_invalid) == 1:
        expected_native = expected_native.replace(after_invalid, before_invalid, 1)
    else:
        assert expected_native.count(before_invalid) == 1
assert native == expected_native, "native emitter exact source drift"
assert native.count(guarded_invalidation) == 1
assert "LocationDescriptorToFriendlyName(descriptor)" not in native
assert "patch_information.find(target_desc)" in native
assert 'write_derived("${PORT_BUILD_DIR}/emit_x64.cpp"' not in cmake
assert 'configure_file("${EDEN_EMIT_X64_SOURCE}" "${PORT_BUILD_DIR}/emit_x64.cpp" COPYONLY)' in cmake

first = cmake.index('set(EDEN_MAINTAINED_EMIT_X64_ROOT "')
last = cmake.index('get_target_property(jit_sources dynarmic SOURCES)', first)
selection = cmake[first:last]
assert shutil.which("cmake"), "CMake unavailable for profile selection proof"
with tempfile.TemporaryDirectory(prefix="encore-x64-patch-owner-") as folder:
    root_temp = Path(folder)
    for native_mode in (False, True):
        folder_profile = root_temp / ("native" if native_mode else "host")
        folder_profile.mkdir()
        script = root_temp / ("native.cmake" if native_mode else "host.cmake")
        script.write_text(
            "cmake_minimum_required(VERSION 3.25)\n"
            + f'set(PORT_ROOT "{root.as_posix()}")\n'
            + f'set(PORT_BUILD_DIR "{folder_profile.as_posix()}")\n'
            + f'set(PS5_NATIVE {"ON" if native_mode else "OFF"})\n'
            + selection
        )
        subprocess.run(["cmake", "-P", str(script)], check=True, timeout=30)
        assert (folder_profile / "emit_x64.cpp").read_text() == (native if native_mode else host)
print("ENCORE_MAINTAINED_COMMON_EMITTER_PASS host/native=2 lookup=exact perfmap=native-removed")
