#!/usr/bin/env python3
"""Exact G14 normal/native Core::System parity and maintained CMake selection."""
from pathlib import Path
import hashlib
import subprocess
import tempfile

def git_blob(text: str) -> str:
    raw = text.encode()
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()

EARLY_1952 = """        Settings::values.use_squashed_iterated_blend = false;

        // Lichii #1952: the cheat VM runs on CoreTiming. Stop it before
        // SyncPause(false), guest suspension, or service/process teardown.
        // Its destructor unschedules the timer event and joins an active run.
        cheat_engine.reset();
"""
OLD_FLAG = """        Settings::values.use_squashed_iterated_blend = false;
"""

def reverse_1952(text: str, native: bool) -> str:
    assert text.count(EARLY_1952) == 1
    text = text.replace(EARLY_1952, OLD_FLAG, 1)
    if native:
        anchor = (
            '        ::Eden::ReportStep("shutdown", '
            '"Completed kernel.SuspendEmulation(true)");\n'
            "        kernel.CloseServices();"
        )
        assert text.count(anchor) == 1
        text = text.replace(
            anchor,
            '        ::Eden::ReportStep("shutdown", '
            '"Completed kernel.SuspendEmulation(true)");\n'
            "        cheat_engine.reset();\n"
            "        kernel.CloseServices();", 1)
    else:
        anchor = "        kernel.SuspendEmulation(true);\n        kernel.CloseServices();"
        assert text.count(anchor) == 1
        text = text.replace(
            anchor,
            "        kernel.SuspendEmulation(true);\n"
            "        cheat_engine.reset();\n"
            "        kernel.CloseServices();", 1)
    late = "        fs_controller.Reset();\n        core_timing.ClearPendingEvents();"
    assert text.count(late) == 1
    return text.replace(
        late,
        "        fs_controller.Reset();\n"
        "        cheat_engine.reset();\n"
        "        core_timing.ClearPendingEvents();", 1)

root = Path(__file__).resolve().parents[1]
base = root / "vendor/sources/eden/src/core/core.cpp"
active = root / "vendor/encore-active/eden-core/src/core"
oracle = root / "tools/fixtures/retired-g14-core.cmake"
cmake = (root / "headless/CMakeLists.txt").read_text()
assert base.is_file() and oracle.is_file()
assert 'file(READ "${PROJECT_SOURCE_DIR}/src/core/core.cpp" system_source)' not in cmake
assert 'write_derived("${PORT_BUILD_DIR}/core.cpp"' not in cmake
assert cmake.count('configure_file("${EDEN_MAINTAINED_CORE_SYSTEM}" "${PORT_BUILD_DIR}/core.cpp" COPYONLY)') == 1
assert 'target_include_directories(core PRIVATE "${EDEN_PORT_DIR}")' in cmake
assert 'set(EDEN_MAINTAINED_CORE_SYSTEM "${EDEN_MAINTAINED_CORE_SYSTEM_ROOT}/core_standard.cpp")' in cmake
assert 'set(EDEN_MAINTAINED_CORE_SYSTEM "${EDEN_MAINTAINED_CORE_SYSTEM_ROOT}/core_native.cpp")' in cmake
for native in (False, True):
    with tempfile.TemporaryDirectory(prefix="encore-core-g14-") as tmp:
        subprocess.run([
            "cmake", f"-DPS5_NATIVE={'ON' if native else 'OFF'}",
            f"-DPROJECT_SOURCE_DIR={root / 'vendor/sources/eden'}",
            f"-DPORT_BUILD_DIR={tmp}",
            f"-DEDEN_PORT_DIR={root / 'headless'}",
            "-P", str(oracle),
        ], check=True, capture_output=True, text=True)
        generated = (Path(tmp) / "core.cpp").read_text()
        if native:
            generated = generated.replace(
                '#include "' + (root / "headless/diagnostics.h").as_posix() + '"',
                '#include "diagnostics.h"')
        filename = "core_native.cpp" if native else "core_standard.cpp"
        actual = (active / filename).read_text()
        expected_current = {
            False: "5fbd4b90de30d20bff7a9fe07be85e4fc187fa93",
            True: "ba5b2cf06c5885bafc2e16c424bc146e24455b00",
        }[native]
        assert git_blob(actual) == expected_current, ("reviewed #1952 source drift", filename)
        predecessor = reverse_1952(actual, native)
        assert generated == predecessor, ("G14 byte parity after #1952 reverse", filename)
        shutdown = actual.split("    void ShutdownMainProcess() {", 1)[1].split(
            "\n    bool IsShuttingDown()", 1)[0]
        assert shutdown.count("cheat_engine.reset();") == 1
        assert shutdown.index("cheat_engine.reset();") < shutdown.index(
            "core_timing.SyncPause(false);")
        assert actual.count("process.reset();\n            ShutdownMainProcess()") == 2
        assert 'GameSettings::LoadOverrides(params.program_id,' in actual
        assert ("::Eden::ReportStep" in actual) == native

# The release PS5 graph replaces core_native with the NS2-capable derivative.
ns2 = (root / "vendor/encore-active/ns2-runtime/process/core/core.cpp").read_text()
assert git_blob(ns2) == "7e3159eb648e92cca3543cfd01bcfd26a0caa135"
assert git_blob(reverse_1952(ns2, True)) == "ac37dcd3d33373d6f5189dc4963f3dfbce898391"
ns2_shutdown = ns2.split("    void ShutdownMainProcess() {", 1)[1].split(
    "\n    bool IsShuttingDown()", 1)[0]
assert ns2_shutdown.count("cheat_engine.reset();") == 1
assert ns2_shutdown.index("cheat_engine.reset();") < ns2_shutdown.index(
    "core_timing.SyncPause(false);")
assert 'vendor/encore-active/ns2-runtime/process/core/core.cpp' not in cmake
assert 'ns2-runtime/process/core/core.cpp' in cmake
print("ENCORE_MAINTAINED_CORE_SYSTEM_PARITY_PASS G14=retired variants=2"
      " lichii1952=3 exact_reverse=3 ns2_release=1")
