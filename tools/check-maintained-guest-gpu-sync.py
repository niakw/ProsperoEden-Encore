#!/usr/bin/env python3
"""G20/P2.7 maintained GPU source parity (single shipping owner + retained DEV reference)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACTIVE = ROOT / "vendor/encore-active/eden-core/src/video_core"
DMA = (ROOT / "vendor/encore-active/eden-backports/src/video_core/dma_pusher.cpp").read_text()
PULLER = (ROOT / "vendor/sources/eden/src/video_core/engines/puller.cpp").read_text()
CMAKE = (ROOT / "headless/CMakeLists.txt").read_text()

def once(source, old, new):
    assert source.count(old) == 1, (old, source.count(old))
    return source.replace(old, new)

OLD_WAIT = "        sync_cv.wait(lk, [this]() { return synced; });"
WAIT = ("        while (!synced && !system.IsShuttingDown())\n"
        "            sync_cv.wait_for(lk, std::chrono::milliseconds(10));")
DMA_FAULT_INC = '#ifdef PS5_NATIVE\n#include "gpu_failure.h"\n#endif\n#include "common/settings.h"'
DMA_FAULT_WAIT = "        while (!synced && !system.IsShuttingDown()) {\n#ifdef PS5_NATIVE\n            // A failed GPU worker cannot deliver this pending fence.\n            if (auto failure = ::Eden::PeekGpuFailure())\n                std::rethrow_exception(failure);\n#endif\n            sync_cv.wait_for(lk, std::chrono::milliseconds(10));\n        }\n#ifdef PS5_NATIVE\n        // A failure published together with the final notification must not\n        // be mistaken for a successful DMA fence acknowledgement.\n        if (auto failure = ::Eden::PeekGpuFailure())\n            std::rethrow_exception(failure);\n#endif"
OLD_SEM = "    while (word != value) {"
SEM = "    while (word != value && !dma_pusher.system.IsShuttingDown()) {"
GPU_FAULT_INC = '#ifdef PS5_NATIVE\n#include "gpu_failure.h"\n#endif\n#include "common/assert.h"'
GPU_FAULT_INIT = """    const auto value = regs.semaphore_acquire;
#ifdef PS5_NATIVE
    // On a failed graphics worker, a stale GPU semaphore can never progress.
    // Sample failure once per 64 unsuccessful polls, starting with the first.
    unsigned acquire_polls = 0;
#endif
"""
GPU_FAULT_LOOP = """    while (word != value && !dma_pusher.system.IsShuttingDown()) {
#ifdef PS5_NATIVE
        if ((acquire_polls++ & 63u) == 0u) {
            if (auto failure = ::Eden::PeekGpuFailure())
                std::rethrow_exception(failure);
        }
#endif
"""

def expected(kind, dev):
    if kind == "dma":
        source = once(DMA, OLD_WAIT, WAIT + "\n        if (system.IsShuttingDown()) return false;")
        source = once(source, '#include "common/settings.h"', DMA_FAULT_INC)
        if dev:
            timer = ("        { ::Eden::Performance::DiagnosticActiveTimer dma_fence_timer(\n"
                     "            ::Eden::Performance::gpu_dma_sync_wait, ::Eden::Performance::gpu_dma_sync_active_since_ns,\n"
                     "            !synced && !system.IsShuttingDown());\n" + WAIT + "\n        }")
            source = once(source, WAIT, timer)
        source = once(source, WAIT, DMA_FAULT_WAIT)
    else:
        source = once(PULLER, OLD_SEM, SEM)
        source = once(source, '#include "common/assert.h"', GPU_FAULT_INC)
        source = once(source, '    const auto value = regs.semaphore_acquire;\n', GPU_FAULT_INIT)
        source = once(source, SEM + '\n', GPU_FAULT_LOOP)
        if dev:
            timer = ("    ::Eden::Performance::DiagnosticActiveTimer semaphore_timer(\n"
                     "        ::Eden::Performance::gpu_puller_semaphore_wait,\n"
                     "        ::Eden::Performance::gpu_puller_semaphore_active_since_ns,\n"
                     "        word != value && !dma_pusher.system.IsShuttingDown());\n" + SEM)
            source = once(source, SEM, timer)
    if kind == "dma":
        inc = '#include "video_core/guest_memory.h"\n'
        source = once(source, inc, inc +
            '#ifdef EDEN_NS2_NATIVE_GPU_DISPATCH\n'
            '#include "core/hle/service/nvdrv/devices/native_gpu_channel_registry.h"\n'
            '#endif\n')
        policy = ('        const bool use_safe = Settings::IsDMALevelDefault() ? '
                  'Settings::IsGPULevelHigh() : Settings::IsDMALevelSafe();')
        native = '''        bool use_safe = Settings::IsDMALevelDefault() ? Settings::IsGPULevelHigh() : Settings::IsDMALevelSafe();
#ifdef EDEN_NS2_NATIVE_GPU_DISPATCH
        // P2.7: C7x0 native GPFIFO command words can have been produced by
        // an earlier GPU dispatch. A guest setting for UNSAFE DMA must never
        // bypass GPU cache coherency for an authenticated NS2 channel.
        // SafeRead flushes the actual guest GPU region before consuming the
        // live words, including the non-contiguous backing fallback.
        use_safe |= Service::Nvidia::Devices::NativeGpuChannelRegistry::Instance().IsNative(&channel_state);
#endif'''
        source = once(source, policy, native)
    if dev:
        source = '#include "performance.h"\n' + source
    return "#include <chrono>\n" + source

# G20 pinned full-source parity is retained after P2.7's reviewed native
# GPFIFO fetch, explicit fence policy and null-subchannel protections.
# These three literals are an exact snapshot of the pinned maintained
# PS5 owner, not dynamically copied from the file under test.
P27_NATIVE_FETCH = "#ifdef PS5_NATIVE\n        // Command headers are validated by NVDRV at submission, but the\n        // address space can change before the GPU worker consumes the live\n        // command words. Revalidate after the inter-list fence wait and\n        // before dirty-memory probes, SafeRead, or ProcessCommands. Never\n        // acknowledge a revoked native GPFIFO as an all-zero pushbuffer.\n        if (Service::Nvidia::Devices::NativeGpuChannelRegistry::Instance().IsNative(\n                &channel_state) &&\n            !Service::Nvidia::Devices::NativeGpfifoFetchMapped(\n                dma_state.dma_get, static_cast<u64>(header.size),\n                [this](u64 addr, u64 bytes) {\n                    return memory_manager.IsFullyMappedRange(addr, bytes);\n                })) {\n            LOG_ERROR(HW_GPU, \"Native GPFIFO command unmapped at fetch: address={:#x} words={}\",\n                      dma_state.dma_get, static_cast<u64>(header.size));\n#ifdef PS5_NATIVE\n            // Returning false silently finishes DispatchCalls; its caller\n            // would then publish a completed GPU queue fence and process\n            // later syncpoint increments for work that was never executed.\n            // The maintained PS5 GPU pthread entry catches this exception,\n            // records its fatal cause and requests worker stop before any\n            // queue fence is signaled. No exception leaves the OS thread.\n            throw std::runtime_error(\"Native GPFIFO command unmapped at GPU fetch\");\n#else\n            return false;\n#endif\n        }\n#endif\n"
P27_NATIVE_FENCE = "        const bool explicit_sync = command_list.command_lists[dma_pushbuffer_subindex].sync;\n        const bool user_sync = Settings::values.sync_memory_operations.GetValue();\n#ifdef PS5_NATIVE\n        // A native NS2 GPFIFO fence is part of the guest-visible ordering\n        // contract, not an optional host quality preset. Its previous\n        // Compute/3D writes must retire BEFORE the next live command list\n        // is read, even if the user's NS1 sync optimization is disabled.\n        signal_sync = explicit_sync &&\n            (user_sync || Service::Nvidia::Devices::NativeGpuChannelRegistry::\n                              Instance().IsNative(&channel_state));\n#else\n        signal_sync = explicit_sync && user_sync;\n#endif"
# P2 G10: pin the exact live owner body including native queue-retirement.
# The old snapshot expected a silent return; that is unsafe for native queues.
# Retain exact byte parity and verify two native guarded sites.
P27_UNBOUND = "        if (!subchannel) {\n            // A guest may submit methods before binding an engine. Never\n            // dereference a missing subchannel or replay it as a valid method.\n            LOG_ERROR(HW_GPU, \"GPFIFO method {:#x} on unbound subchannel {}\",\n                      dma_state.method, dma_state.subchannel);\n#ifdef PS5_NATIVE\n            // Ignoring an unbound engine on an authenticated native queue\n            // would let GPFIFO publish completion for commands never run.\n            // An invalid SET_OBJECT already unbinds this channel: retire its\n            // queue instead of manufacturing a successful guest fence.\n            if (Service::Nvidia::Devices::NativeGpuChannelRegistry::Instance().IsNative(\n                    &channel_state)) {\n                throw std::runtime_error(\"Native GPFIFO method on unbound subchannel\");\n            }\n#endif\n            return;\n        }\n"


def expected_dma_unified(source):
    old_macro = '#ifdef EDEN_NS2_NATIVE_GPU_DISPATCH'
    assert source.count(old_macro) == 2
    source = source.replace(old_macro, '#ifdef PS5_NATIVE')
    source = once(source,
        '#ifdef PS5_NATIVE\n#include "gpu_failure.h"\n#endif\n#include "common/settings.h"',
        '#ifdef PS5_NATIVE\n#include "gpu_failure.h"\n#include <stdexcept>\n#endif\n#include "common/logging.h"\n#include "common/settings.h"')
    source = once(source,
        '#include "core/hle/service/nvdrv/devices/native_gpu_channel_registry.h"\n',
        '#include "core/hle/service/nvdrv/devices/native_gpu_channel_registry.h"\n'
        '#include "core/hle/service/nvdrv/devices/native_gpu_fetch_admission.h"\n')
    source = once(source,
        '    if (header.size > 0) {\n'
        '        if (subchannels[dma_state.subchannel] && dma_state.method_count) {',
        '    if (header.size > 0) {\n' + P27_NATIVE_FETCH +
        '        if (subchannels[dma_state.subchannel] && dma_state.method_count) {')
    source = once(source,
        '        signal_sync = command_list.command_lists[dma_pushbuffer_subindex].sync && Settings::values.sync_memory_operations.GetValue();',
        P27_NATIVE_FENCE)
    subchannel = '        auto subchannel = subchannels[dma_state.subchannel];\n'
    assert source.count(subchannel) == 2
    source = source.replace(subchannel, subchannel + P27_UNBOUND)
    assert source.count('throw std::runtime_error("Native GPFIFO method on unbound subchannel")') == 2
    assert source.count('#ifdef PS5_NATIVE\n            // Ignoring an unbound engine') == 2
    return source


# G10 reviewed native GPFIFO acquire/replay delta on the *shipping* normal
# owner only. DEV is a retained exact backport + diagnostics and MUST NOT
# inherit the experimental native scheduler. This table contains exact source
# hunks relative to expected_dma_unified() and rejects every unreviewed
# source change. It is NOT a synthetic execution witness.
G10_NATIVE_GPFIFO_REPLAY_HUNKS = [
  {
    "at": 41,
    "removed": [],
    "added": [
      "#ifdef PS5_NATIVE",
      "    if (!Service::Nvidia::Devices::NativeGpuChannelRegistry::Instance().IsNative(",
      "            &channel_state)) {",
      "        dma_pushbuffer_subindex = 0; // Preserve exact NS1 submission behavior.",
      "    }",
      "#else"
    ]
  },
  {
    "at": 42,
    "removed": [],
    "added": [
      "#endif"
    ]
  },
  {
    "at": 56,
    "removed": [],
    "added": [
      "#ifdef PS5_NATIVE",
      "    // The unresolved comparison stops this GPU channel without blocking the",
      "    // worker, which can process releases from other channels in the meantime.",
      "    if (!ResumeNativeAcquire()) {",
      "        return false;",
      "    }",
      "#endif"
    ]
  },
  {
    "at": 65,
    "removed": [],
    "added": [
      "#ifdef PS5_NATIVE",
      "        command_resume_offset = 0;",
      "#endif"
    ]
  },
  {
    "at": 69,
    "removed": [],
    "added": [
      "#ifdef PS5_NATIVE",
      "        if (command_resume_offset > prefetch_size) {",
      "            throw std::runtime_error(\"Native GPFIFO prefetch resume cursor invalid\");",
      "        }",
      "        const auto commands = std::span<const CommandHeader>{",
      "            command_list.prefetch_command_list.data(), prefetch_size};",
      "        ProcessCommands(commands.subspan(command_resume_offset));",
      "        if (HasPendingNativeAcquire()) {",
      "            return false;",
      "        }",
      "        command_resume_offset = 0;",
      "#else"
    ]
  },
  {
    "at": 70,
    "removed": [],
    "added": [
      "#endif"
    ]
  },
  {
    "at": 148,
    "removed": [],
    "added": [
      "#ifdef PS5_NATIVE",
      "            if (command_resume_offset > headers.size()) {",
      "                throw std::runtime_error(\"Native GPFIFO entry shortened during acquire\");",
      "            }",
      "            ProcessCommands(std::span<const CommandHeader>{",
      "                headers.data(), headers.size()}.subspan(command_resume_offset));",
      "#else"
    ]
  },
  {
    "at": 149,
    "removed": [],
    "added": [
      "#endif"
    ]
  },
  {
    "at": 151,
    "removed": [],
    "added": [
      "#ifdef PS5_NATIVE",
      "            if (command_resume_offset > headers.size()) {",
      "                throw std::runtime_error(\"Native GPFIFO entry shortened during acquire\");",
      "            }",
      "            ProcessCommands(std::span<const CommandHeader>{",
      "                headers.data(), headers.size()}.subspan(command_resume_offset));",
      "#else"
    ]
  },
  {
    "at": 152,
    "removed": [],
    "added": [
      "#endif"
    ]
  },
  {
    "at": 155,
    "removed": [],
    "added": [
      "#ifdef PS5_NATIVE",
      "    if (HasPendingNativeAcquire()) {",
      "        // Keep both the queue entry and its method state; completing the",
      "        // entry now would wrongly acknowledge unexecuted guest commands.",
      "        return false;",
      "    }",
      "    command_resume_offset = 0;",
      "#endif"
    ]
  },
  {
    "at": 186,
    "removed": [],
    "added": [
      "#ifdef PS5_NATIVE",
      "    const size_t offset_before = command_resume_offset;",
      "#endif"
    ]
  },
  {
    "at": 190,
    "removed": [
      "            dma_state.dma_word_offset = u32(index * sizeof(u32));",
      "            const u32 max_write = u32(std::min<std::size_t>(index + dma_state.method_count, commands.size()) - index);"
    ],
    "added": [
      "            dma_state.dma_word_offset = u32(",
      "#ifdef PS5_NATIVE",
      "                offset_before +",
      "#endif",
      "                index) * sizeof(u32);",
      "            u32 max_write = u32(std::min<std::size_t>(",
      "                index + dma_state.method_count, commands.size()) - index);",
      "#ifdef PS5_NATIVE",
      "            // No puller batching across a native SEM_EXECUTE: it may park",
      "            // the channel after its first word.",
      "            if (dma_state.method < non_puller_methods &&",
      "                Service::Nvidia::Devices::NativeGpuChannelRegistry::Instance().IsNative(",
      "                    &channel_state)) {",
      "                max_write = 1;",
      "            }",
      "#endif"
    ]
  },
  {
    "at": 198,
    "removed": [
      "            dma_state.dma_word_offset = u32(index * sizeof(u32));"
    ],
    "added": [
      "            dma_state.dma_word_offset = u32(",
      "#ifdef PS5_NATIVE",
      "                offset_before +",
      "#endif",
      "                index) * sizeof(u32);"
    ]
  },
  {
    "at": 237,
    "removed": [],
    "added": [
      "#ifdef PS5_NATIVE",
      "        if (HasPendingNativeAcquire()) {",
      "            // All words through the semaphore were consumed, but nothing",
      "            // following it; begin exactly at this word after release.",
      "            command_resume_offset = offset_before + index;",
      "            return;",
      "        }",
      "#endif"
    ]
  }
]

def apply_reviewed_native_gpfifo_replay(source):
    lines = source.split("\n")
    rebuilt = []
    cursor = 0
    for hunk in G10_NATIVE_GPFIFO_REPLAY_HUNKS:
        start = hunk["at"]
        before = hunk["removed"]
        after = hunk["added"]
        assert cursor <= start <= len(lines), ("non-monotonic G10 source hunk", start)
        assert lines[start:start+len(before)] == before, (
            "reviewed native DMA source hunk drift", start)
        rebuilt.extend(lines[cursor:start])
        rebuilt.extend(after)
        cursor = start+len(before)
    rebuilt.extend(lines[cursor:])
    owner = "\n".join(rebuilt)
    assert owner.count("HasPendingNativeAcquire()") >= 2
    assert "ResumeNativeAcquire()" in owner
    assert "Native GPFIFO prefetch resume cursor invalid" in owner
    assert "Native GPFIFO entry shortened during acquire" in owner
    assert owner.count('throw std::runtime_error("Native GPFIFO method on unbound subchannel")') == 2
    return owner

for kind, name in (("dma", "dma_pusher"), ("puller", "engines/puller")):
    for dev in (False, True):
        path = name + ("_dev" if dev else "") + ".cpp"
        base = expected(kind, dev)
        expected_owner = (apply_reviewed_native_gpfifo_replay(expected_dma_unified(base)) if not dev else expected_dma_unified(base)) if kind == "dma" else base
        assert (ACTIVE / path).read_text() == expected_owner, path
assert "foreach(unit dma_pusher engines/puller)" not in CMAKE
assert 'write_derived("${PORT_BUILD_DIR}/${unit_name}.cpp" "${command_source}")' not in CMAKE
for marker in ('list(REMOVE_ITEM video_sources dma_pusher.cpp engines/puller.cpp)',
               'list(APPEND video_sources "${EDEN_MAINTAINED_GPU_DMA}" "${EDEN_MAINTAINED_GPU_PULLER}")',
               'target_include_directories(video_core PRIVATE "${EDEN_PORT_DIR}")',
               ):
    assert marker in CMAKE, marker
assert 'dma_pusher_dev.cpp' not in CMAKE
assert 'engines/puller_dev.cpp' not in CMAKE
print("ENCORE_G20_GUEST_GPU_PARITY_PASS normal=2 dev=2")
