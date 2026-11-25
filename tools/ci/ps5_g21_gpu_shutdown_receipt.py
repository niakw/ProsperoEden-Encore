#!/usr/bin/env python3
"""Strict source receipt for the reviewed PS5 G21 GPU shutdown lifetime fix.

The five historical G21 CMake/source parity oracles are kept immutable.
A vendor PR #112 candidate is normalized IN MEMORY solely for historical
source comparison, never for production native C++ compilation.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

OLD = {
    "gpu_vulkan.cpp": "8d43de2a7176f90c294e91a9dfcd6c0647292211",
    "gpu_gl_native.cpp": "ccd81a7930d129b2f3b35fd0a21217e4fd9d78f9",
    "gpu_gl_host.cpp": "0a1585073fa44e2500269ea275bac4f1b6002dbb",
    "gpu_gl_native_dev.cpp": "8ce31eb1c997c88b46a35be501e8c171d6473073",
    "gpu_gl_host_dev.cpp": "7beae3b46e921f160e7bbc8fd43b9d97d333106b",
}
REVIEWED = {
    "gpu_vulkan.cpp": "186be29abbb51e199cc52bf85e5bad938587b89e",
    "gpu_gl_native.cpp": "87edefe7cc5d8da45ca0797257e71e81f87175a9",
    "gpu_gl_host.cpp": "33fc3039d52a568585b7aa84cdf7e097aa339def",
    "gpu_gl_native_dev.cpp": "856f3259bb29cb07822c14f83819ebd10aaba647",
    "gpu_gl_host_dev.cpp": "848ead02e3b128c498e0ac08232d391f6b8b4085",
}
OLD_VULKAN = "    ~Impl() = default;\n\n"
OLD_OPENGL = (
    "    ~Impl() { gpu_thread.Stop(); if (renderer && Settings::IsOpenGL()) "
    "{ renderer->Context().MakeCurrent(); glFinish(); } }\n\n"
)
START = "    ~Impl() {"
NEXT_OWNER = "    std::shared_ptr<Control::ChannelState> CreateChannel("

POST_FC27_CPU_WRITE = {
    "gpu_vulkan.cpp": "a1b9f68ba5de5c0e5ae09bac5fc5652a986c9c8f",
    "gpu_gl_native.cpp": "9e8bc036d0ed9d1d71024aa241f3e835d61be3e1",
    "gpu_gl_native_dev.cpp": "8dddf44da8d6306fa52f801a88127e29b3d1c7a8",
}
POST_GPU_DIRTY_COMPLETE_TYPE = {
    "gpu_vulkan.cpp": "842a0289f75bc2a0763285173e4616060348ec22",
    "gpu_gl_native.cpp": "8abd4f3652b4a10f27281a2fd43a3764bd6d5c6e",
    "gpu_gl_native_dev.cpp": "091431333f6f05e7e81c691051d64771cab4a5dd",
}
GPU_DIRTY_COMPLETE_TYPE_INCLUDE = '#include "core/gpu_dirty_memory_manager.h"\n'

# NS1/NS2 GPU lifetime and channel safety successors in the maintained
# Vulkan owner. These exact reviewed hunks are reversed ONLY for the G21
# historical oracle; no shipping GPU source is modified.
VULKAN_LIFETIME_CURRENT = "90b8f8c99878b21558b3996e8b1e95a5fc6ad9a6"
VULKAN_LIFETIME_PREVIOUS = "842a0289f75bc2a0763285173e4616060348ec22"
VULKAN_LIFETIME_REVERSE = (
    ("\n    void ReleaseChannel(Control::ChannelState& to_release) {\n#if defined(PS5_NATIVE)\n        // Queue retirement on the existing GPU worker. Only the worker\n        // reads/mutates the channels map: the NVDRV service thread must not\n        // race GPU::BindChannel while looking up a channel on FD close.\n        // The caller keeps to_release alive until this synchronous barrier\n        // completes. Verify the exact owner epoch on the worker side.\n        const s32 channel_id = to_release.bind_id;\n        const auto* expected = &to_release;\n        const u64 fence = RequestSyncOperation([this, channel_id, expected] {\n            const auto it = channels.find(channel_id);\n            if (it == channels.end() || it->second.get() != expected)\n                return; // An old FD cannot retire a reused channel ID.\n            const auto owner = it->second;\n            scheduler.RetireChannel(owner.get());\n            if (current_channel == owner.get()) {\n                current_channel = nullptr;\n                bound_channel = -1;\n            }\n            if (owner->initialized)\n                renderer->ReadRasterizer()->ReleaseChannel(owner->bind_id);\n            channels.erase(it);\n        });\n        gpu_thread.TickGPU(is_async);\n        WaitForSyncOperation(fence);\n#else\n        // Host/non-PS5 scheduler has no native epoch-retirement API.\n        // Preserve its original behavior; no platform-wide ABI change.\n        UNIMPLEMENTED();\n#endif\n    }\n",
     "\n    void ReleaseChannel(Control::ChannelState& to_release) {\n        UNIMPLEMENTED();\n    }\n"),
    ("    [[nodiscard]] u64 RequestSyncOperation(Func&& action) {\n        std::unique_lock lck{sync_request_mutex};\n        // Publish a fence only AFTER the queue owns its callback. If\n        // allocating this node throws, no fence is skipped: subsequent waits\n        // must still be reachable by TickWork's completed-request counter.\n        sync_requests.emplace_back(std::forward<Func>(action));\n        return ++last_sync_fence;\n    }\n",
     "    [[nodiscard]] u64 RequestSyncOperation(Func&& action) {\n        std::unique_lock lck{sync_request_mutex};\n        const u64 fence = ++last_sync_fence;\n        sync_requests.emplace_back(std::forward<Func>(action));\n        return fence;\n    }\n"),
    ("    void WaitForSyncOperation(const u64 fence) {\n        std::unique_lock lck{sync_request_mutex};\n        while (!shutting_down.load(std::memory_order_relaxed) &&\n               CurrentSyncRequestFence() < fence) {\n            // A failed GPU worker cannot advance this fence. Preserve the\n            // published exception for every waiter instead of hanging the\n            // launcher/guest-stop path indefinitely.\n            if (auto failure = ::Eden::PeekGpuFailure()) {\n                std::rethrow_exception(failure);\n            }\n            sync_request_cv.wait_for(lck, std::chrono::milliseconds(100));\n        }\n        if (auto failure = ::Eden::PeekGpuFailure()) {\n            std::rethrow_exception(failure);\n        }\n    }\n",
     "    void WaitForSyncOperation(const u64 fence) {\n        std::unique_lock lck{sync_request_mutex};\n        sync_request_cv.wait(lck, [this, fence] { return CurrentSyncRequestFence() >= fence; });\n    }\n"),
    ("            auto request = std::move(sync_requests.front());\n            sync_requests.pop_front();\n            // Keep the RAII lock's ownership state consistent if a GPU\n            // callback throws. Unlocking the raw mutex left lck owning an\n            // already-unlocked mutex during exception unwinding.\n            lck.unlock();\n            request();\n            current_sync_fence.fetch_add(1, std::memory_order_release);\n            lck.lock();\n            sync_request_cv.notify_all();\n        }",
     "            auto request = std::move(sync_requests.front());\n            sync_requests.pop_front();\n            sync_request_mutex.unlock();\n            request();\n            current_sync_fence.fetch_add(1, std::memory_order_release);\n            sync_request_mutex.lock();\n            sync_request_cv.notify_all();\n        }"),
    ("        }\n        raster_area.preemtive = true;\n        const u64 fence = RequestSyncOperation([this, raster_area]() {\n            renderer->ReadRasterizer()->FlushRegion(raster_area.start_address, raster_area.end_address - raster_area.start_address);\n        });",
     "        }\n        raster_area.preemtive = true;\n        const u64 fence = RequestSyncOperation([this, &raster_area]() {\n            renderer->ReadRasterizer()->FlushRegion(raster_area.start_address, raster_area.end_address - raster_area.start_address);\n        });"),
    ("    Tegra::Control::Scheduler scheduler;\n    ::Common::unordered_map<s32, std::shared_ptr<Tegra::Control::ChannelState>> channels;\n    // A guest may close an NVDRV GPU FD before its first successful bind.\n    // ReleaseChannel compares this pointer even for an uninitialized owner.\n    Tegra::Control::ChannelState* current_channel{};\n    s32 bound_channel{-1};\n",
     "    Tegra::Control::Scheduler scheduler;\n    ::Common::unordered_map<s32, std::shared_ptr<Tegra::Control::ChannelState>> channels;\n    Tegra::Control::ChannelState* current_channel;\n    s32 bound_channel{-1};\n"),
)
CPU_WRITE_OLD = """        std::function<void(PAddr, size_t)> callback_writes([this](PAddr address, size_t size) {
            renderer->ReadRasterizer()->OnCacheInvalidation(address, size);
        });
        system.GatherGPUDirtyMemory(callback_writes);"""
CPU_WRITE_NEW = """        std::vector<std::pair<DAddr, u64>> writes;
        std::function<void(PAddr, size_t)> callback_writes(
            [&writes](PAddr address, size_t size) { writes.emplace_back(address, size); });
        system.GatherGPUDirtyMemory(callback_writes);
        if (!writes.empty()) renderer->ReadRasterizer()->OnCacheInvalidations(writes);
    }

    void ForEachPendingCpuWrite(const std::function<void(DAddr, size_t)>& callback) {
        for (auto& manager : system.GetGPUDirtyMemoryManager()) manager.ForEachPending(callback);"""
CPU_WRITE_FORWARDER = """void GPU::ForEachPendingCpuWrite(const std::function<void(DAddr, size_t)>& callback) {
    impl->ForEachPendingCpuWrite(callback);
}

"""

def git_blob(source: str) -> str:
    raw = source.encode("utf-8")
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()

def normalize_g21_shutdown_source(filename: str, source: str) -> tuple[str, bool]:
    """Accept EXACT old or new Git blob and reconstruct prior byte-for-byte."""
    if filename not in OLD:
        raise AssertionError(("Unrecognized G21 source owner", filename))
    current = git_blob(source)
    if filename == "gpu_gl_native.cpp" and current == "7720e5a347817e67c0a964d3a80644b01b99d733":
        # Reconstruct only the immutable historical audit copy; production uses the new owner.
        for newer, older in (
            ("    Tegra::Control::Scheduler scheduler;\n    std::mutex channel_mutex;\n    ::Common::unordered_map<s32, std::shared_ptr<Tegra::Control::ChannelState>> channels;\n    Tegra::Control::ChannelState* current_channel{};", "    Tegra::Control::Scheduler scheduler;\n    ::Common::unordered_map<s32, std::shared_ptr<Tegra::Control::ChannelState>> channels;\n    Tegra::Control::ChannelState* current_channel;"),
            ("    std::atomic<u64> last_sync_fence{};", "    u64 last_sync_fence{};"),
            ("    std::vector<u8> GetAppletCaptureBuffer() {\n        // Shutdown or a worker failure can end the wait before the queued\n        // callback runs. Its result must not refer to the caller's stack.\n        auto out = std::make_shared<std::vector<u8>>();\n        const auto wait_fence = RequestSyncOperation([this, out] {\n            *out = renderer->GetAppletCaptureBuffer();\n        });\n        gpu_thread.TickGPU(is_async);\n        WaitForSyncOperation(wait_fence);\n        // Only access the vector after the callback's release fence. A\n        // cancelled wait must not race a still-running capture operation.\n        if (CurrentSyncRequestFence() < wait_fence) {\n            return {};\n        }\n        return std::move(*out);\n    }\n\n\n", "    std::vector<u8> GetAppletCaptureBuffer() {\n        std::vector<u8> out;\n\n        const auto wait_fence =\n            RequestSyncOperation([&] { out = renderer->GetAppletCaptureBuffer(); });\n        gpu_thread.TickGPU(is_async);\n        WaitForSyncOperation(wait_fence);\n\n        return out;\n    }\n\n\n"),
            ("    [[nodiscard]] u64 GetTicks() const {\n#if defined(PS5_NATIVE) && defined(EDEN_NS2_GUEST_COUNTER)\n        // The reviewed ExeFS loader selects the guest counter from NPDM\n        // before the first guest JIT instruction. Native Ampere reports\n        // and CPU/GPU calibration are in nanoseconds, not the Maxwell\n        // 614.4-MHz GPU-tick domain. This switch is shared across titles:\n        // when an NS1 program is selected again, SelectProgram(false)\n        // restores the original tick units without a title-specific hack.\n        if (Eden::GuestCounter::Rate() == Eden::GuestCounter::Switch2Hz) {\n            const auto elapsed_ns = system.CoreTiming().GetGlobalTimeNs().count();\n            return elapsed_ns > 0 ? static_cast<u64>(elapsed_ns) : 0ULL;\n        }\n#endif\n        const u64 gpu_tick = system.CoreTiming().GetGPUTicks();\n        return gpu_tick / GpuClockMultiplier(Settings::values.gpu_clock.GetValue());\n    }\n\n", "    [[nodiscard]] u64 GetTicks() const {\n        const u64 gpu_tick = system.CoreTiming().GetGPUTicks();\n        return gpu_tick / GpuClockMultiplier(Settings::values.gpu_clock.GetValue());\n    }\n\n"),
            ("    void TickWork() {\n        // Skip the mutex on the common draw path with no queued sync work.\n        // Keep the existing bounded snapshot drain and shutdown protocol.\n        if (last_sync_fence.load(std::memory_order_acquire) ==\n            current_sync_fence.load(std::memory_order_acquire)) {\n            return;\n        }\n        std::unique_lock lck{sync_request_mutex};\n        for (auto remaining = sync_requests.size(); remaining != 0; --remaining) {\n            auto request = std::move(sync_requests.front());\n            sync_requests.pop_front();\n            lck.unlock();\n            request();\n            current_sync_fence.fetch_add(1, std::memory_order_release);\n            lck.lock();\n            sync_request_cv.notify_all();\n        }\n    }\n\n", "    void TickWork() {\n        std::unique_lock lck{sync_request_mutex};\n        for (auto remaining = sync_requests.size(); remaining != 0; --remaining) {\n            auto request = std::move(sync_requests.front());\n            sync_requests.pop_front();\n            lck.unlock();\n            request();\n            current_sync_fence.fetch_add(1, std::memory_order_release);\n            lck.lock();\n            sync_request_cv.notify_all();\n        }\n    }\n\n"),
            ("return current_sync_fence.load(std::memory_order_acquire);", "return current_sync_fence.load(std::memory_order_relaxed);"),
            ("    void InvalidateGPUCache() {\n#if defined(PS5_NATIVE)\n        // Maxwell issues this barrier very frequently, including frames with\n        // no guest CPU writes. Avoid allocating a vector/function and taking\n        // every dirty-manager gather lock when no manager can contribute.\n        // A Collect racing after this acquire load is ordered after this\n        // barrier and remains visible to the next invalidation.\n        bool may_have_pending = false;\n        for (const auto& manager : system.GetGPUDirtyMemoryManager()) {\n            if (manager.MayHavePending()) {\n                may_have_pending = true;\n                break;\n            }\n        }\n        if (!may_have_pending) {\n            return;\n        }\n#endif\n        std::vector<std::pair<DAddr, u64>> writes;\n        std::function<void(PAddr, size_t)> callback_writes(\n            [&writes](PAddr address, size_t size) { writes.emplace_back(address, size); });\n        system.GatherGPUDirtyMemory(callback_writes);\n        if (!writes.empty()) renderer->ReadRasterizer()->OnCacheInvalidations(writes);\n    }\n\n", "    void InvalidateGPUCache() {\n        std::vector<std::pair<DAddr, u64>> writes;\n        std::function<void(PAddr, size_t)> callback_writes(\n            [&writes](PAddr address, size_t size) { writes.emplace_back(address, size); });\n        system.GatherGPUDirtyMemory(callback_writes);\n        if (!writes.empty()) renderer->ReadRasterizer()->OnCacheInvalidations(writes);\n    }\n\n"),
            ("    // The NVDRV service creates channels while the GPU worker binds and retires them.\n    // Protect only registry operations; never hold this mutex over scheduler or renderer calls.\n    std::shared_ptr<Control::ChannelState> FindChannel(s32 channel_id) {\n        std::scoped_lock lock{channel_mutex};\n        const auto it = channels.find(channel_id);\n        return it == channels.end() ? nullptr : it->second;\n    }\n\n    // Caller owns channel_mutex, including allocation of the next bind ID.\n    std::shared_ptr<Control::ChannelState> CreateChannel(s32 channel_id) {\n        auto channel_state = std::make_shared<Tegra::Control::ChannelState>(channel_id);\n        channels.emplace(channel_id, channel_state);\n        return channel_state;\n    }\n\n    void BindChannel(s32 channel_id) {\n        if (bound_channel != channel_id) {\n            const auto owner = FindChannel(channel_id);\n            ASSERT(owner);\n            bound_channel = channel_id;\n            current_channel = owner.get();\n            renderer->ReadRasterizer()->BindChannel(*current_channel);\n        }\n    }\n\n    std::shared_ptr<Control::ChannelState> AllocateChannel() {\n        std::scoped_lock lock{channel_mutex};\n        return CreateChannel(new_channel_id++);\n    }\n\n    void InitChannel(Control::ChannelState& to_init, u64 program_id) {\n        to_init.Init(system, program_id);\n        to_init.BindRasterizer(renderer->ReadRasterizer());\n        renderer->ReadRasterizer()->InitializeChannel(to_init);\n        // Never publish an owner until its payload AND rasterizer state are ready.\n        // The strict scheduler rejects empty payloads; GPU work must not race\n        // the rasterizer's native per-channel initialization either.\n        const auto owner = FindChannel(to_init.bind_id);\n        ASSERT(owner.get() == &to_init);\n        scheduler.DeclareChannel(owner);\n    }\n\n    void InitAddressSpace(Tegra::MemoryManager& memory_manager) {\n        memory_manager.BindRasterizer(renderer->ReadRasterizer());\n    }\n\n    void ReleaseChannel(Control::ChannelState& to_release) {\n#if defined(PS5_NATIVE)\n        // TickWork also runs inside draws, under Scheduler::Push's shared\n        // epoch lease and GPU execution mutex. RetireChannel needs both\n        // locks exclusively. Queue a distinct, blocking FIFO worker command\n        // instead: it runs after the earlier dispatches and releases.\n        const s32 channel_id = to_release.bind_id;\n        const auto owner = FindChannel(channel_id);\n        if (owner.get() != &to_release)\n            return;\n        gpu_thread.RetireChannelAtBoundary([this, channel_id, owner] {\n            if (FindChannel(channel_id) != owner)\n                return; // An old FD cannot retire a reused channel ID.\n            scheduler.RetireChannel(owner.get());\n            if (current_channel == owner.get()) {\n                current_channel = nullptr;\n                bound_channel = -1;\n            }\n            if (owner->initialized)\n                renderer->ReadRasterizer()->ReleaseChannel(owner->bind_id);\n            // No scheduler or renderer calls while holding the registry lock.\n            std::scoped_lock lock{channel_mutex};\n            const auto it = channels.find(channel_id);\n            if (it != channels.end() && it->second == owner)\n                channels.erase(it);\n        }, is_async);\n#else\n        // Host/non-PS5 scheduler has no native epoch-retirement API.\n        // Preserve its original behavior; no platform-wide ABI change.\n        UNIMPLEMENTED();\n#endif\n    }\n\n", "    std::shared_ptr<Control::ChannelState> CreateChannel(s32 channel_id) {\n        auto channel_state = std::make_shared<Tegra::Control::ChannelState>(channel_id);\n        channels.emplace(channel_id, channel_state);\n        return channel_state;\n    }\n\n    void BindChannel(s32 channel_id) {\n        if (bound_channel != channel_id) {\n            auto it = channels.find(channel_id);\n            ASSERT(it != channels.end());\n            bound_channel = channel_id;\n            current_channel = it->second.get();\n            renderer->ReadRasterizer()->BindChannel(*current_channel);\n        }\n    }\n\n    std::shared_ptr<Control::ChannelState> AllocateChannel() {\n        return CreateChannel(new_channel_id++);\n    }\n\n    void InitChannel(Control::ChannelState& to_init, u64 program_id) {\n        to_init.Init(system, program_id);\n        to_init.BindRasterizer(renderer->ReadRasterizer());\n        renderer->ReadRasterizer()->InitializeChannel(to_init);\n        // Never publish an owner until its payload AND rasterizer state are ready.\n        // The strict scheduler rejects empty payloads; GPU work must not race\n        // the rasterizer's native per-channel initialization either.\n        const auto it = channels.find(to_init.bind_id);\n        ASSERT(it != channels.end() && it->second.get() == &to_init);\n        scheduler.DeclareChannel(it->second);\n    }\n\n    void InitAddressSpace(Tegra::MemoryManager& memory_manager) {\n        memory_manager.BindRasterizer(renderer->ReadRasterizer());\n    }\n\n    void ReleaseChannel(Control::ChannelState& to_release) {\n        UNIMPLEMENTED();\n    }\n\n"),
            ("#include \"video_core/shader_notify.h\"\n\n#if defined(PS5_NATIVE) && defined(EDEN_NS2_GUEST_COUNTER)\n#include \"encore/guest_counter_policy.h\"\n#endif\n", "#include \"video_core/shader_notify.h\"\n"),
        ):
            assert source.count(newer) == 1
            source = source.replace(newer, older, 1)
        current = git_blob(source)
        assert current == "8abd4f3652b4a10f27281a2fd43a3764bd6d5c6e"
    # 65112443: reverse the exact empty-gather fast path on the audit copy.
    if filename == "gpu_vulkan.cpp" and current == "2de0ed20172755c0dac82e7e4031232281c115f5":
        for newer, older in (("    // The NVDRV service creates channels while the GPU worker binds and retires them.\n    // Protect only registry operations; never hold this mutex over scheduler or renderer calls.\n    std::shared_ptr<Control::ChannelState> FindChannel(s32 channel_id) {\n        std::scoped_lock lock{channel_mutex};\n        const auto it = channels.find(channel_id);\n        return it == channels.end() ? nullptr : it->second;\n    }\n\n    // Caller owns channel_mutex, including allocation of the next bind ID.\n    std::shared_ptr<Control::ChannelState> CreateChannel(s32 channel_id) {\n        auto channel_state = std::make_shared<Tegra::Control::ChannelState>(channel_id);\n        channels.emplace(channel_id, channel_state);\n        return channel_state;\n    }\n\n    void BindChannel(s32 channel_id) {\n        if (bound_channel != channel_id) {\n            const auto owner = FindChannel(channel_id);\n            ASSERT(owner);\n            bound_channel = channel_id;\n            current_channel = owner.get();\n            renderer->ReadRasterizer()->BindChannel(*current_channel);\n        }\n    }\n\n    std::shared_ptr<Control::ChannelState> AllocateChannel() {\n        std::scoped_lock lock{channel_mutex};\n        return CreateChannel(new_channel_id++);\n    }\n\n    void InitChannel(Control::ChannelState& to_init, u64 program_id) {\n        to_init.Init(system, program_id);\n        to_init.BindRasterizer(renderer->ReadRasterizer());\n        renderer->ReadRasterizer()->InitializeChannel(to_init);\n        // Never publish an owner until its payload AND rasterizer state are ready.\n        // The strict scheduler rejects empty payloads; GPU work must not race\n        // the rasterizer's native per-channel initialization either.\n        const auto owner = FindChannel(to_init.bind_id);\n        ASSERT(owner.get() == &to_init);\n        scheduler.DeclareChannel(owner);\n    }\n\n", "    std::shared_ptr<Control::ChannelState> CreateChannel(s32 channel_id) {\n        auto channel_state = std::make_shared<Tegra::Control::ChannelState>(channel_id);\n        channels.emplace(channel_id, channel_state);\n        return channel_state;\n    }\n\n    void BindChannel(s32 channel_id) {\n        if (bound_channel != channel_id) {\n            auto it = channels.find(channel_id);\n            ASSERT(it != channels.end());\n            bound_channel = channel_id;\n            current_channel = it->second.get();\n            renderer->ReadRasterizer()->BindChannel(*current_channel);\n        }\n    }\n\n    std::shared_ptr<Control::ChannelState> AllocateChannel() {\n        return CreateChannel(new_channel_id++);\n    }\n\n    void InitChannel(Control::ChannelState& to_init, u64 program_id) {\n        to_init.Init(system, program_id);\n        to_init.BindRasterizer(renderer->ReadRasterizer());\n        renderer->ReadRasterizer()->InitializeChannel(to_init);\n        // Never publish an owner until its payload AND rasterizer state are ready.\n        // The strict scheduler rejects empty payloads; GPU work must not race\n        // the rasterizer's native per-channel initialization either.\n        const auto it = channels.find(to_init.bind_id);\n        ASSERT(it != channels.end() && it->second.get() == &to_init);\n        scheduler.DeclareChannel(it->second);\n    }\n\n"), ("    void ReleaseChannel(Control::ChannelState& to_release) {\n#if defined(PS5_NATIVE)\n        // TickWork also runs inside draws, under Scheduler::Push's shared\n        // epoch lease and GPU execution mutex. RetireChannel needs both\n        // locks exclusively. Queue a distinct, blocking FIFO worker command\n        // instead: it runs after the earlier dispatches and releases.\n        const s32 channel_id = to_release.bind_id;\n        const auto owner = FindChannel(channel_id);\n        if (owner.get() != &to_release)\n            return;\n        gpu_thread.RetireChannelAtBoundary([this, channel_id, owner] {\n            if (FindChannel(channel_id) != owner)\n                return; // An old FD cannot retire a reused channel ID.\n            scheduler.RetireChannel(owner.get());\n            if (current_channel == owner.get()) {\n                current_channel = nullptr;\n                bound_channel = -1;\n            }\n            if (owner->initialized)\n                renderer->ReadRasterizer()->ReleaseChannel(owner->bind_id);\n            // No scheduler or renderer calls while holding the registry lock.\n            std::scoped_lock lock{channel_mutex};\n            const auto it = channels.find(channel_id);\n            if (it != channels.end() && it->second == owner)\n                channels.erase(it);\n        }, is_async);\n#else\n        // Host/non-PS5 scheduler has no native epoch-retirement API.\n        // Preserve its original behavior; no platform-wide ABI change.\n        UNIMPLEMENTED();\n#endif\n    }\n\n", "    void ReleaseChannel(Control::ChannelState& to_release) {\n#if defined(PS5_NATIVE)\n        // Queue retirement on the existing GPU worker. Only the worker\n        // reads/mutates the channels map: the NVDRV service thread must not\n        // race GPU::BindChannel while looking up a channel on FD close.\n        // The caller keeps to_release alive until this synchronous barrier\n        // completes. Verify the exact owner epoch on the worker side.\n        const s32 channel_id = to_release.bind_id;\n        const auto* expected = &to_release;\n        const u64 fence = RequestSyncOperation([this, channel_id, expected] {\n            const auto it = channels.find(channel_id);\n            if (it == channels.end() || it->second.get() != expected)\n                return; // An old FD cannot retire a reused channel ID.\n            const auto owner = it->second;\n            scheduler.RetireChannel(owner.get());\n            if (current_channel == owner.get()) {\n                current_channel = nullptr;\n                bound_channel = -1;\n            }\n            if (owner->initialized)\n                renderer->ReadRasterizer()->ReleaseChannel(owner->bind_id);\n            channels.erase(it);\n        });\n        gpu_thread.TickGPU(is_async);\n        WaitForSyncOperation(fence);\n#else\n        // Host/non-PS5 scheduler has no native epoch-retirement API.\n        // Preserve its original behavior; no platform-wide ABI change.\n        UNIMPLEMENTED();\n#endif\n    }\n\n"), ("    std::mutex channel_mutex;\n    ::Common::unordered_map<s32, std::shared_ptr<Tegra::Control::ChannelState>> channels;", "    ::Common::unordered_map<s32, std::shared_ptr<Tegra::Control::ChannelState>> channels;"),):
            assert source.count(newer) == 1, ("GPU channel retirement owner drift", newer[:100])
            source = source.replace(newer, older, 1)
        current = git_blob(source)
        assert current == "99a33e50f6e3c0df8142ad64a03de04077e08912"
    if filename == "gpu_vulkan.cpp" and current == "99a33e50f6e3c0df8142ad64a03de04077e08912":
        for newer, older in (("    [[nodiscard]] u64 CurrentSyncRequestFence() const {\n        // A completed callback publishes its result before incrementing the fence.\n        return current_sync_fence.load(std::memory_order_acquire);\n    }\n", "    [[nodiscard]] u64 CurrentSyncRequestFence() const {\n        return current_sync_fence.load(std::memory_order_relaxed);\n    }\n"), ("    void TickWork() {\n        // Lichii: draws tick even when no CPU sync operation is queued.\n        // The producer increments only after successful callback insertion;\n        // an enqueue racing this empty check still schedules its GPU tick.\n        if (last_sync_fence.load(std::memory_order_acquire) ==\n            current_sync_fence.load(std::memory_order_acquire)) {\n            return;\n        }\n        std::unique_lock lck{sync_request_mutex};\n        while (!sync_requests.empty()) {\n            auto request = std::move(sync_requests.front());\n            sync_requests.pop_front();\n            // Keep the RAII lock's ownership state consistent if a GPU\n            // callback throws. Unlocking the raw mutex left lck owning an\n            // already-unlocked mutex during exception unwinding.\n            lck.unlock();\n            request();\n            current_sync_fence.fetch_add(1, std::memory_order_release);\n            lck.lock();\n            sync_request_cv.notify_all();\n        }\n    }\n", "    void TickWork() {\n        std::unique_lock lck{sync_request_mutex};\n        while (!sync_requests.empty()) {\n            auto request = std::move(sync_requests.front());\n            sync_requests.pop_front();\n            // Keep the RAII lock's ownership state consistent if a GPU\n            // callback throws. Unlocking the raw mutex left lck owning an\n            // already-unlocked mutex during exception unwinding.\n            lck.unlock();\n            request();\n            current_sync_fence.fetch_add(1, std::memory_order_release);\n            lck.lock();\n            sync_request_cv.notify_all();\n        }\n    }\n"), ("    std::vector<u8> GetAppletCaptureBuffer() {\n        // Shutdown or a worker failure can end the wait before the queued\n        // callback runs. Its result must not refer to the caller's stack.\n        auto out = std::make_shared<std::vector<u8>>();\n        const auto wait_fence = RequestSyncOperation([this, out] {\n            *out = renderer->GetAppletCaptureBuffer();\n        });\n        gpu_thread.TickGPU(is_async);\n        WaitForSyncOperation(wait_fence);\n        // Only access the vector after the callback's release fence. A\n        // cancelled wait must not race a still-running capture operation.\n        if (CurrentSyncRequestFence() < wait_fence) {\n            return {};\n        }\n        return std::move(*out);\n    }\n", "    std::vector<u8> GetAppletCaptureBuffer() {\n        std::vector<u8> out;\n\n        const auto wait_fence =\n            RequestSyncOperation([&] { out = renderer->GetAppletCaptureBuffer(); });\n        gpu_thread.TickGPU(is_async);\n        WaitForSyncOperation(wait_fence);\n\n        return out;\n    }\n"), ("    std::atomic<u64> last_sync_fence{};", "    u64 last_sync_fence{};"),):
            assert source.count(newer) == 1, ("GPU sync/capture owner drift", newer[:100])
            source = source.replace(newer, older, 1)
        current = git_blob(source)
        assert current == "f083c985451563dcfe387d1bc61f54bd02ed762e"
    if filename == "gpu_vulkan.cpp" and current == "f083c985451563dcfe387d1bc61f54bd02ed762e":
        fast_path = "#if defined(PS5_NATIVE)\n        // Maxwell issues this barrier very frequently, including frames with\n        // no guest CPU writes. Avoid allocating a vector/function and taking\n        // every dirty-manager gather lock when no manager can contribute.\n        // A Collect racing after this acquire load is ordered after this\n        // barrier and remains visible to the next invalidation.\n        bool may_have_pending = false;\n        for (const auto& manager : system.GetGPUDirtyMemoryManager()) {\n            if (manager.MayHavePending()) {\n                may_have_pending = true;\n                break;\n            }\n        }\n        if (!may_have_pending) {\n            return;\n        }\n#endif\n"
        assert source.count(fast_path) == 1, "Reviewed empty gather delta drift"
        source = source.replace(fast_path, "", 1)
        current = git_blob(source)
        assert current == "90b8f8c99878b21558b3996e8b1e95a5fc6ad9a6", ("GPU dirty gather predecessor drift", current)
    if filename == "gpu_vulkan.cpp" and current == VULKAN_LIFETIME_CURRENT:
        for newer, older in VULKAN_LIFETIME_REVERSE:
            assert source.count(newer) == 1, ("Vulkan lifetime owner drift", newer[:100])
            source = source.replace(newer, older, 1)
        current = git_blob(source)
        assert current == VULKAN_LIFETIME_PREVIOUS, (
            "Reviewed Vulkan lifetime reconstruction changed unrelated source", current)
    if filename in POST_GPU_DIRTY_COMPLETE_TYPE and current == POST_GPU_DIRTY_COMPLETE_TYPE[filename]:
        assert source.count(GPU_DIRTY_COMPLETE_TYPE_INCLUDE) == 1, filename
        source = source.replace(GPU_DIRTY_COMPLETE_TYPE_INCLUDE, "", 1)
        current = git_blob(source)
        assert current == POST_FC27_CPU_WRITE[filename], (
            "GPU dirty-manager complete-type normalization changed unrelated bytes",
            filename, current)
    if filename in POST_FC27_CPU_WRITE and current == POST_FC27_CPU_WRITE[filename]:
        assert source.count(CPU_WRITE_NEW) == source.count(CPU_WRITE_FORWARDER) == 1
        source = source.replace(CPU_WRITE_NEW, CPU_WRITE_OLD, 1)
        source = source.replace(CPU_WRITE_FORWARDER, "", 1)
        current = git_blob(source)
        assert current == REVIEWED[filename], (
            "FC27 CPU-write normalization changed unrelated G21 bytes", filename, current)
    if current == OLD[filename]:
        return source, False
    assert current == REVIEWED[filename], (
        "Unreviewed selected G21 source drift; never relax old oracle",
        filename, current)
    assert source.count(START) == 1 and source.count(NEXT_OWNER) == 1
    first = source.index(START)
    last = source.index(NEXT_OWNER, first)
    updated_destructor = source[first:last]
    for marker in ("NotifyShutdown();", "gpu_thread.Stop();", "renderer.reset();"):
        assert updated_destructor.count(marker) == 1, (filename, marker)
    assert updated_destructor.index("NotifyShutdown();") < updated_destructor.index(
        "gpu_thread.Stop();") < updated_destructor.index("renderer.reset();")
    if filename != "gpu_vulkan.cpp":
        for marker in ("renderer->Context().MakeCurrent();", "glFinish();"):
            assert updated_destructor.count(marker) == 1, (filename, marker)
        assert updated_destructor.index("glFinish();") < updated_destructor.index(
            "renderer.reset();")
    else:
        assert "glFinish();" not in updated_destructor
    assert source.index("std::unique_ptr<VideoCore::RendererBase> renderer;") < source.index(
        "::Common::unordered_map<s32, std::shared_ptr<Tegra::Control::ChannelState>> channels;")
    assert source.index("::Common::unordered_map<s32, std::shared_ptr<Tegra::Control::ChannelState>> channels;") < source.index(
        "VideoCommon::GPUThread::ThreadManager gpu_thread;")
    historic = OLD_VULKAN if filename == "gpu_vulkan.cpp" else OLD_OPENGL
    restored = source[:first] + historic + source[last:]
    assert git_blob(restored) == OLD[filename], (
        "Reviewed GPU shutdown normalization changed historical G21 owner", filename)
    return restored, True
