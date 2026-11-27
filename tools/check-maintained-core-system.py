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


# Lichii #1932 (merged upstream a3b4397): the three maintained Core owners
# contain four additional exact, already-qualified teardown/lifetime edits.
# Reconstruct the #1952 predecessors before comparing them to the retired G14
# oracle; neither historic snapshot nor production source is changed here.
loader_after = """            // The kernel was initialized before loader admission. Leaving it
            // alive retains lists into device memory already being destroyed,
            // and can crash during failed-launch teardown or next title.
            // Lichii #1932: the local KProcess must die while its kernel is alive.
            process.reset();
            ShutdownMainProcess();"""
loader_before = """            // The kernel was initialized before loader admission. Leaving it
            // alive retains lists into device memory already being destroyed,
            // and can crash during failed-launch teardown or next title.
            ShutdownMainProcess();"""
shutdown_after = """        debugger.reset();
        {
            // Lichii #1932: these are kernel-owned objects. Destroy them while
            // the kernel still exists; keep queued general-channel bytes for
            // the next kernel/session.
            std::scoped_lock lk{general_channel_mutex};
            general_channel_event.reset();
            general_channel_context.reset();
        }
        kernel.Shutdown();"""
shutdown_before = """        debugger.reset();
        kernel.Shutdown();"""
ensure_after = """            general_channel_context.emplace(system, "GeneralChannel");
            general_channel_event.emplace(*general_channel_context);
            if (!general_channel.empty()) {
                general_channel_event->Signal(kernel);
            }
        }"""
ensure_before = """            general_channel_context.emplace(system, "GeneralChannel");
            general_channel_event.emplace(*general_channel_context);
        }"""
pop_after = """bool System::TryPopGeneralChannel(std::vector<u8>& out_data) {
    std::scoped_lock lk{impl->general_channel_mutex};
    if (impl->general_channel.empty()) {
        return false;
    }
    // A queue can survive a kernel restart while its old Event cannot.
    impl->EnsureGeneralChannelInitialized(*this);
    out_data = std::move(impl->general_channel.back());"""
pop_before = """bool System::TryPopGeneralChannel(std::vector<u8>& out_data) {
    std::scoped_lock lk{impl->general_channel_mutex};
    if (!impl->general_channel_event || impl->general_channel.empty()) {
        return false;
    }
    out_data = std::move(impl->general_channel.back());"""

def reverse_1932(text: str) -> str:
    for after, before, label in (
        (loader_after, loader_before, "failed-loader"),
        (shutdown_after, shutdown_before, "teardown"),
        (ensure_after, ensure_before, "recreate"),
        (pop_after, pop_before, "pop"),
    ):
        assert text.count(after) == 1, ("#1932 source drift", label)
        text = text.replace(after, before, 1)
    return text


GPU_TEARDOWN_AFTER = """        // GPU::Impl owns the Vulkan worker, scheduler, channel states and
        // renderer; native NVDRV address spaces own the GMMU/NvMap backing
        // those channel states reference. Once guest CPU cores are suspended,
        // join and destroy the GPU BEFORE CloseServices can release the
        // channel's address space. The old order could let the GPU worker or
        // renderer touch already-unpinned guest memory during exit/relaunch.
        // Keep Host1x and the NVDRV containers alive throughout GPU teardown.
        gpu_core.reset();
        ::Eden::ReportStep("shutdown", "Completed gpu_core.reset()");
        kernel.CloseServices();"""
GPU_TEARDOWN_BEFORE = """        kernel.CloseServices();"""
GPU_TEARDOWN_LATE_AFTER = """        app_loader.reset();
        audio_core.reset();
        host1x_core.reset();"""
GPU_TEARDOWN_LATE_BEFORE = """        app_loader.reset();
        audio_core.reset();
        gpu_core.reset();
        ::Eden::ReportStep("shutdown", "Completed gpu_core.reset()");
        host1x_core.reset();"""


# FC27 PS5 shutdown: NVDRV retains KProcess references. Release AS/service
# owners before ShutdownCores so the kernel's scheduler is still valid.
# Strip exactly this qualified runtime delta before replaying old source SHAs.
NVDRV_EXIT_LIFETIME_NEW = "        kernel.CloseServices();\n        ::Eden::ReportStep(\"shutdown\", \"Completed kernel.CloseServices()\");\n        // NVDRV's nvhost_as_gpu destructor can unpin NVMap pages and release\n        // its retained KProcess reference. Release those service owners while\n        // the process and scheduler are still alive; ShutdownCores terminates\n        // the guest processes and must come AFTER this cleanup. The GPU worker\n        // was joined above, so no GPU task can reuse the retired mappings.\n        services.reset();\n        ::Eden::ReportStep(\"shutdown\", \"Completed services.reset()\");\n        service_manager.reset();\n        kernel.ShutdownCores();\n        ::Eden::ReportStep(\"shutdown\", \"Completed kernel.ShutdownCores()\");"
NVDRV_EXIT_LIFETIME_PREVIOUS = "        kernel.CloseServices();\n        ::Eden::ReportStep(\"shutdown\", \"Completed kernel.CloseServices()\");\n        kernel.ShutdownCores();\n        ::Eden::ReportStep(\"shutdown\", \"Completed kernel.ShutdownCores()\");\n        services.reset();\n        ::Eden::ReportStep(\"shutdown\", \"Completed services.reset()\");\n        service_manager.reset();"

def reverse_nvdrv_exit_lifetime(text: str) -> str:
    assert text.count(NVDRV_EXIT_LIFETIME_NEW) == 1
    shutdown = text.split("    void ShutdownMainProcess() {", 1)[1].split(
        "\n    bool IsShuttingDown()", 1)[0]
    order = ("gpu_core.reset();", "kernel.CloseServices();", "services.reset();",
             "service_manager.reset();", "kernel.ShutdownCores();")
    positions = [shutdown.index(needle) for needle in order]
    assert positions == sorted(positions), ("NVDRV/KProcess exit order", positions)
    return text.replace(NVDRV_EXIT_LIFETIME_NEW, NVDRV_EXIT_LIFETIME_PREVIOUS, 1)


def reverse_gpu_teardown(text: str) -> str:
    assert text.count(GPU_TEARDOWN_AFTER) == 1
    assert text.count(GPU_TEARDOWN_LATE_AFTER) == 1
    text = text.replace(GPU_TEARDOWN_AFTER, GPU_TEARDOWN_BEFORE, 1)
    return text.replace(GPU_TEARDOWN_LATE_AFTER, GPU_TEARDOWN_LATE_BEFORE, 1)


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
        current_1932 = {
            False: "024e35e6e4274c0c8fc8fcb4450176c8c97bd984",
            True: "9a62448fa07ce437da719b8a08e6a241541cbb29",
        }[native]
        assert git_blob(actual) == current_1932, ("reviewed #1932 source drift", filename)
        before_1932 = reverse_1932(actual)
        assert git_blob(before_1932) == expected_current, ("reviewed #1932 reverse drift", filename)
        predecessor = reverse_1952(before_1932, native)
        assert generated == predecessor, ("G14 byte parity after #1952 reverse", filename)
        shutdown = actual.split("    void ShutdownMainProcess() {", 1)[1].split(
            "\n    bool IsShuttingDown()", 1)[0]
        assert shutdown.count("cheat_engine.reset();") == 1
        assert shutdown.index("cheat_engine.reset();") < shutdown.index(
            "core_timing.SyncPause(false);")
        assert actual.count("process.reset();\n            ShutdownMainProcess()") == 3
        assert 'GameSettings::LoadOverrides(params.program_id,' in actual
        assert ("::Eden::ReportStep" in actual) == native

# The release PS5 graph replaces core_native with the NS2-capable derivative.
# The current successor has accumulated reviewed NUP/process tracing and the
# FC27 shutdown lifetime fixes after the original GPU-teardown snapshot. Seal
# the exact shipping blob here (also independently sealed by active-source,
# R457 sparse and final FC27/P0 provenance gates) and verify the live lifetime
# order directly rather than replaying an incomplete historical reverse chain.
ns2 = (root / "vendor/encore-active/eden/src/core/core.cpp").read_text()
# 20d278d9: release SM GPU factories before Services while kernel lives.
assert git_blob(ns2) == "0f854ca3eab4dd0435d6ac58d401f8359301c168", (
    "reviewed current NS2 Core source drift")
ns2_shutdown = ns2.split("    void ShutdownMainProcess() {", 1)[1].split(
    "\n    bool IsShuttingDown()", 1)[0]
assert ns2_shutdown.count("cheat_engine.reset();") == 1
assert ns2_shutdown.index("cheat_engine.reset();") < ns2_shutdown.index(
    "core_timing.SyncPause(false);")
shutdown_order = (
    "gpu_core.reset();",
    "service_manager->Close();",
    "kernel.CloseServices();",
    "service_manager->ReleaseRegisteredHandlersForShutdown();",
    "services.reset();",
    "kernel.ShutdownCores();",
    "service_manager.reset();",
    "fs_controller.Reset();",
    "kernel.Shutdown();",
)
shutdown_positions = [ns2_shutdown.index(needle) for needle in shutdown_order]
assert shutdown_positions == sorted(shutdown_positions), (
    "current NS2 GPU/NVDRV/SM/kernel teardown order drift", shutdown_positions)
# Native dual-NPDM uses this maintained NS2 Core owner intentionally.
# Verify the exact conditional selection, not the pre-NS2 G14 exclusion.
ns2_selected_core = """if(PS5_NATIVE AND EDEN_REVIEWED_DUAL_NPDM)
    set(EDEN_MAINTAINED_CORE_SYSTEM
        "${PORT_ROOT}/vendor/encore-active/eden/src/core/core.cpp")
endif()"""
assert cmake.count(ns2_selected_core) == 1, "NS2 Core owner or admission guard changed"
assert cmake.count("ns2-runtime/process/core/core.cpp") == 1, (
    "unexpected duplicate NS2 Core source selection")
print("ENCORE_MAINTAINED_CORE_SYSTEM_PARITY_PASS G14=retired variants=2"
      " lichii1952=3 lichii1932=3 exact_reverse=3 ns2_release=1")
