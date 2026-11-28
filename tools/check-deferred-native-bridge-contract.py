#!/usr/bin/env python3
"""Host gate for the inactive developer-only cache replay source bridge.

Validates pinned anchors and CMake OFF parsing, not a native compilation or
correct GPU execution; opt-in ON remains explicitly unqualified.
"""
from pathlib import Path
import json
import hashlib
import runpy
import subprocess
import tempfile

root=Path(__file__).resolve().parents[1]
bridge=root/"headless/guest_write_deferred_bridge.cmake"
code=bridge.read_text()
legacy_bridge=root/"tools/fixtures/legacy-guest-write-deferred-bridge.cmake"
legacy_code=legacy_bridge.read_text()
maintained_m06 = root/"vendor/encore-active/eden/src/video_core/memory_manager_deferred.cpp"
maintained_m07 = root/"vendor/encore-active/eden/src/video_core/renderer_vulkan/vk_rasterizer_deferred.cpp"
maintained_m08 = root/"vendor/encore-active/eden/src/video_core/dma_pusher_deferred.cpp"
maintained_m09 = root/"vendor/encore-active/eden/src/video_core/engines/maxwell_dma_deferred.cpp"
maintained_m10 = root/"vendor/encore-active/eden/src/video_core/engines/kepler_compute_deferred.cpp"
maintained_m11 = root/"vendor/encore-active/eden/src/video_core/engines/engine_upload_deferred.cpp"
bridge_runtime = (legacy_code + "\n" + maintained_m06.read_text() +
                  "\n" + maintained_m07.read_text() +
                  "\n" + maintained_m08.read_text() +
                  "\n" + maintained_m09.read_text() + "\n" +
                  maintained_m10.read_text() + "\n" + maintained_m11.read_text())
base=(root/"headless/CMakeLists.txt").read_text()
replay=(root/"headless/gpu_deferred_replay.h").read_text()
perf=(root/"headless/performance.h").read_text()
assert 'option(EDEN_GUEST_WRITE_BRIDGE_DEV "Compile inactive native deferred-write bridge" OFF)' in code
assert "NOT EDEN_DEV_PROFILE" in code and "NOT EDEN_PS5_VULKAN" in code
assert 'include("${CMAKE_CURRENT_LIST_DIR}/guest_write_deferred_bridge.cmake")' not in base
assert 'EDEN_GUEST_WRITE_BRIDGE_DEV' not in base
assert "cpu_write_defer{false}" in perf
assert "cpu_write_defer.store(true" not in code
assert "ScopedReplay" in replay and "replaying_guest_write" in replay
assert "ScopedGuestWriteOrigin" in replay and "guest_write_origin_core = previous" in replay
assert "enum class GuestWriteIntent { NoStore, StoreFollows };" in replay
assert "ScopedGuestStoreIntent" in replay
assert "ScopedGuestCacheMaintenanceIntent" in replay
assert "guest_write_intent = GuestWriteIntent::NoStore;" in replay
assert "Expected exactly two cache-maintenance write callbacks" in legacy_code
assert 'string(REPLACE "${intent_maintenance}" "" maintenance_without "${bridge_cpu}")' in legacy_code
assert "math(EXPR maintenance_count" in legacy_code
assert "guest_write_intent = previous;" in replay
assert "guest_write_intent = GuestWriteIntent::StoreFollows;" in replay
# Fail-closed runtime qualification, independent of any developer toggle.
assert "inline constexpr bool kNativePostStorePublicationReady = false;" in replay
assert bridge_runtime.count("::Eden::GpuDeferredWrite::kNativePostStorePublicationReady") == 2
assert bridge_runtime.index("!::Eden::GpuDeferredWrite::kNativePostStorePublicationReady") < bridge_runtime.index("deferred_cpu_write_queue.Enqueue(core, address, size)")
assert "const bool defer_candidate =\n        ::Eden::GpuDeferredWrite::kNativePostStorePublicationReady &&" in maintained_m07.read_text()
assert bridge_runtime.count("::Eden::GpuDeferredWrite::GuestWriteIntent::StoreFollows") == 2
assert "::Eden::GpuDeferredWrite::ScopedGuestStoreIntent store_intent;" in legacy_code
assert 'string(FIND "${bridge_cpu}" "${${anchor}}" found)' in legacy_code
assert 'string(FIND "${bridge_cpu}" "${NESTED_ANCHOR}" found)' not in legacy_code
# Fail-closed documentation contract: the inactive candidate does not yet
# synchronize deferred writes before either CPU-read fast path. Pin BOTH bypass
# sites so a future change must replace this negative proof with a real ordered
# read/drain qualification before runtime activation can be contemplated.
reader=(root/"vendor/sources/eden/src/core/memory.cpp").read_text()
download=reader.split("void HandleRasterizerDownload(",1)[1].split("void HandleRasterizerWrite(",1)[0]
assert download.index("if (current_area.start_address <= address") < download.index("system.GPU().OnCPURead(address, size)")
gpu_src=(root/"vendor/sources/eden/src/video_core/gpu.cpp").read_text()
gpu_read=gpu_src.split("VideoCore::RasterizerDownloadArea OnCPURead(",1)[1].split("void InvalidateRegion(",1)[0]
assert gpu_read.index("if (raster_area.preemtive)") < gpu_read.index("RequestSyncOperation(")
assert "FlushCaching(" not in gpu_read
assert "HandleRasterizerDownload" not in code
# Known unresolved publication hazard: guest writes can enqueue deferred GPU
# invalidations BEFORE the backing RAM write has occurred. A replay-completion
# ticket is NOT sufficient to assert the new payload has become visible.
# Pin the real source ordering until there is an explicit post-store publication
# protocol and a native read-fence qualification.
write_block=reader.split("bool WriteBlockImpl(",1)[1].split("bool ZeroBlock(",1)[0]
tracked_store=write_block.rsplit("HandleRasterizerWrite(GetInteger(current_vaddr), copy_amount);",1)[1]
assert "std::memcpy(ptr, reinterpret_cast<u8 const*>(buffer) + offset, copy_amount);" in tracked_store
zero_block=reader.split("bool ZeroBlock(",1)[1].split("bool CopyBlock(",1)[0]
assert zero_block.index("HandleRasterizerWrite(GetInteger(current_vaddr), copy_amount);") < zero_block.rindex("std::memset(ptr, 0, copy_amount);")
scalar_write=reader.split("inline void Write(Common::ProcessAddress vaddr,",1)[1].split("bool WriteExclusive(",1)[0]
assert scalar_write.index("HandleRasterizerWrite(addr, sizeof(T));") < scalar_write.index("std::memcpy(ptr, &data, sizeof(T));")
# Exhaustive dispatch-site audit in this pinned implementation. These paths
# cannot all be rewritten by patching WriteBlockImpl alone.
assert reader.count("HandleRasterizerWrite(") == 8
exclusive=reader.split("bool WriteExclusive(Common::ProcessAddress vaddr,",1)[1].split("void HandleRasterizerDownload(",1)[0]
assert exclusive.count("HandleRasterizerWrite(") == 2
assert "Common::AtomicCompareAndSwap(reinterpret_cast<T*>(ptr), data, expected)" in exclusive
assert "Common::AtomicCompareAndSwap(reinterpret_cast<u64*>(ptr), data, expected)" in exclusive
cache_ops=reader.split("Result StoreDataCache(",1)[1].split("void MarkRegionDebug(",1)[0]
assert "Result FlushDataCache(" in cache_ops
assert cache_ops.count("HandleRasterizerWrite(GetInteger(current_vaddr), block_size);") == 2
copy_block=reader.split("bool CopyBlock(",1)[1].split("template <typename Callback>",1)[0]
assert "WriteBlockImpl(dest_addr + offset, ptr, copy_amount, false)" in copy_block
assert "HandleRasterizerDownload(GetInteger(current_vaddr), copy_amount);" in copy_block
# These memory-side callbacks are NOT a complete proof of JIT/fastmem
# publication; the native candidate must remain unreachable.
# The host queue now exposes a completion model. It must not be mistaken for
# a native CPU-read barrier: the real reader still has no GPU-drain request.
queue=(root/"headless/gpu_deferred_write_queue.h").read_text()
for symbol in ("EnqueueTracked", "AcceptedSequence", "CompletedSequence",
               "DrainThrough", "WaitUntil", "Close"):
    assert symbol in queue, symbol
assert "return DrainThrough(target, std::forward<Replay>(replay));" in queue
assert "DrainThrough(Ticket target, Replay&& replay)" in queue
assert "target.generation != generation_" in queue
# Prevent cross-address-space ticket aliasing even when sequence and session
# counters align. The queue epoch generator is global to the process.
assert "static inline std::atomic<std::uint64_t> next_generation_{0};" in queue
assert "generation_{FreshGeneration()}" in queue
assert "generation_ = FreshGeneration();" in queue
assert "bool WaitUntil(Sequence sequence)" not in queue
assert "std::optional<Ticket> EnqueueTracked" in queue
# Bounded backlog counts accepted but UNACKNOWLEDGED sequence IDs, not
# vector entries: a GPU snapshot in progress and coalesced eager writes
# must both consume the budget. Rejected reservations require a safe
# synchronous producer fallback, never a silently lost invalidation.
assert "static constexpr Sequence MaxOutstandingWrites = 8192;" in queue
assert "std::optional<Ticket> ReserveOrdered(" in queue
ordered=queue.split("std::optional<Ticket> ReserveOrdered(",1)[1].split("// Host-only legacy publication",1)[0]
for guard in ("if (auto ticket = Reserve(core, address, size)) return ticket;",
              "if (accepted_ - completed_ < MaxOutstandingWrites) continue;",
              "barrier = {accepted_, generation_};",
              "++pending_wake_callbacks_;", "--pending_wake_callbacks_;",
              "if (!WaitUntil(barrier)) return std::nullopt;",
              "failed_ = true;"):
    assert guard in ordered, guard
assert ordered.index("barrier = {accepted_, generation_};") < ordered.index("RequestGpuOrThrow(request_gpu);")
assert ordered.index("RequestGpuOrThrow(request_gpu);") < ordered.index("WaitUntil(barrier)")
assert "deferred_cpu_write_queue.ReserveOrdered(" not in bridge_runtime
assert "CommitPostStore(" not in bridge_runtime
assert "accepted_ - completed_ >= MaxOutstandingWrites" in queue
# Publishing thousands of reservations out of order must not turn the FIFO
# into a quadratic per-frame CPU hotspot. Last-sequence keys are monotone
# across tail merges and prefix drains, allowing log-time lookup.
publish_body=queue.split("std::optional<bool> PublishImpl(Ticket ticket, bool arm_wake = false, bool cancel = false) {",1)[1].split("static std::uint64_t FreshGeneration()",1)[0]
assert "std::lower_bound(" in publish_body
assert "write.last_sequence < sequence" in publish_body
assert "entry->last_sequence != ticket.sequence" in publish_body
# A post-store producer must wake the GPU when a previously blocked FIFO head
# first becomes replayable. RequestGpu runs OUTSIDE the queue mutex, so a
# synchronous callback can acquire the queue and renderer locks safely.
notify_body=queue.split("bool ResolveAndWake(Ticket ticket, bool cancel, RequestGpu&& request_gpu) {",1)[1].split("// Returning true means a blocked/unready FIFO head",1)[0]
assert "PublishImpl(ticket, true, cancel)" in notify_body
assert "return ResolveAndWake(ticket, false, std::forward<RequestGpu>(request_gpu));" in queue
assert "return ResolveAndWake(ticket, true, std::forward<RequestGpu>(request_gpu));" in queue
assert "RequestGpuOrThrow(std::forward<RequestGpu>(request_gpu));" in notify_body
request_guard=queue.split("static void RequestGpuOrThrow(RequestGpu&& request_gpu) {",1)[1].split("bool ResolveAndWake(",1)[0]
assert "std::is_same_v<std::invoke_result_t<RequestGpu>, bool>" in request_guard
assert "if (!std::forward<RequestGpu>(request_gpu)())" in request_guard
assert "throw std::runtime_error" in request_guard
assert "std::forward<RequestGpu>(request_gpu)();" in request_guard
assert "failed_ = true;" in notify_body and "throw;" in notify_body
assert "const bool became_ready = !was_ready && !queue_.empty()" in publish_body
assert "if (arm_wake && became_ready) ++pending_wake_callbacks_;" in publish_body
assert "std::optional<bool> PublishImpl(Ticket ticket, bool arm_wake = false, bool cancel = false)" in queue
assert "entry->cancelled = cancel;" in publish_body
assert "tail.published && !tail.cancelled && tail.core == core" in queue
assert "bool Cancel(Ticket ticket)" in queue
assert "bool CancelAndWake(Ticket ticket, RequestGpu&& request_gpu)" in queue
assert "wake_cv_.wait(lock, [&] { return pending_wake_callbacks_ == 0; });" in queue
assert "pending_wake_callbacks_ != 0" in queue
assert "active_wake_callback_ == this" in queue
assert "active_wake_callback_ = this;" in notify_body
assert "deferred_cpu_write_queue.PublishAndWake(" not in bridge_runtime
assert "deferred_cpu_write_queue.CancelAndWake(" not in bridge_runtime
# Shutdown must be a replay-lifetime barrier, not just a waiter wake-up.
# Without this, the GPU callback can still touch freed rasterizer resources.
close_body=queue.split("void Close() {",1)[1].split("bool ResetAfterQuiescence()",1)[0]
assert close_body.index("closed_ = true;") < close_body.index("std::lock_guard owner(consumer_mutex_);")
assert "completed_cv_.notify_all()" in close_body
assert "if (active_consumer_ == this || active_wake_callback_ == this)" in close_body
drain_body=queue.split("std::uint64_t DrainThrough(Ticket target, Replay&& replay)",1)[1].split("std::uint64_t Drain(Replay&& replay)",1)[0]
assert "std::unique_lock owner(consumer_mutex_);" in drain_body
assert "if (item.cancelled) continue;" in drain_body
assert "return replayed;" in drain_body
assert "if (closed_ || failed_ || target.generation != generation_" in drain_body
# A thrown rasterizer callback has potentially non-atomic side effects.
# Never let the queue acknowledge, retry or accept fresh work after failure.
assert "catch (...)" in drain_body
assert drain_body.index("failed_ = true;") < drain_body.index("throw;")
assert "bool Failed() const" in queue
assert "closed_ || failed_ || ticket.generation != generation_" in queue
assert "completed_ >= ticket.sequence || closed_ || failed_" in queue
# A title that is closing or poisoned must never return a successful read,
# even when its GPU callback previously acknowledged the ticket's watermark.
wait_body=queue.split("bool WaitUntil(Ticket ticket) {",1)[1].split("std::uint64_t DrainThrough(",1)[0]
assert "return !closed_ && !failed_ && generation_ == ticket.generation" in wait_body
assert "if (closed_ || failed_ || accepted_" in queue
assert "failed_ = false;" in queue
# Reset is destructive: it must not race any GPU callback or reopen a live
# title merely because producers have momentarily become idle.
reset_body=queue.split("bool ResetAfterQuiescence() {",1)[1].split("private:",1)[0]
assert reset_body.index("std::lock_guard owner(consumer_mutex_);") < reset_body.index("std::lock_guard lock(mutex_);")
assert "if (active_consumer_ == this) return false;" in reset_body
assert "if (!closed_ || !close_completed_ || pending_wake_callbacks_ != 0)" in reset_body
assert reset_body.index("if (!closed_ || !close_completed_ || pending_wake_callbacks_ != 0)") < reset_body.index("queue_.clear();")
assert "close_completed_ = false;" in queue
assert "close_completed_ = true;" in close_body
assert close_body.index("std::lock_guard owner(consumer_mutex_);") < close_body.index("close_completed_ = true;")
assert "completed_cv_.notify_all()" in queue
assert "WaitUntil(" not in bridge_runtime
# The host candidate now has a publish-after-store contract; the real bridge
# still uses eager Enqueue and must NOT be presented as correctly integrated.
for symbol in ("struct Ticket", "Reserve(", "Publish(Ticket", "WaitUntil(Ticket",
               "generation_", "queue_[ready].published"):
    assert symbol in queue, symbol
assert "deferred_cpu_write_queue.Enqueue(core, address, size)" in bridge_runtime
# A GPU replay exception poisons the session; even if upstream catches it,
# no later native command may silently proceed through FlushCaching().
assert "if (deferred_cpu_write_queue.Failed()) std::terminate();" in bridge_runtime
assert bridge_runtime.index("if (deferred_cpu_write_queue.Failed()) std::terminate();") < bridge_runtime.index("if (deferred_cpu_write_queue.Pending())")

assert "deferred_cpu_write_queue.Reserve(" not in bridge_runtime
assert "deferred_cpu_write_queue.Publish(" not in bridge_runtime
assert "cpu_write_defer{false}" in perf
for signature in (
    "EnqueueDeferredCPUWrite",
    "ScopedGuestWriteOrigin guest_origin",
    "deferred_cpu_write_queue",
    "ReplayQueued(",
    "dirty[core].Collect(address, size);",
    "rasterizer->OnCPUWrite(address, size);",
    "gpu_memory->EnqueueDeferredCPUWrite(addr, size)",
    "memory_manager.FlushCaching();",
    "void MaxwellDMA::Launch()",
    "void KeplerCompute::ProcessLaunch()",
    "void State::ProcessData(std::span<const u8> read_buffer)",
    "void DmaPusher::DispatchCalls()",
    "system.GPU().OnCommandListEnd();",
):
    assert signature in bridge_runtime, signature
# M04: maintained complete header must equal its former two pinned rewrites.
# Only the absolute CMake-specific include prefix is normalized to the
# existing headless include directory of core and video_core.
maintained_m04 = root/"vendor/encore-active/eden/src/video_core/memory_manager_deferred.h"
pinned_m04 = (root/"vendor/sources/eden/src/video_core/memory_manager.h").read_text()
assert pinned_m04.count("    void FlushCaching();") == 1
assert pinned_m04.count("    Core::System& system;") == 1
assert "SetNativeSyncpointShim" not in pinned_m04
assert "native_syncpoint_shim" not in pinned_m04
expected_m04 = ('#include "gpu_deferred_replay.h"\n' +
    pinned_m04.replace(
        "    ~MemoryManager();\n\n    static constexpr bool HAS_FLUSH_INVALIDATION = true;",
        "    ~MemoryManager();\n\n"
        "    // Lichii 12125bc / NX2 blocker #46: NVN reads Host1x syncpoints\n"
        "    // through a read-only GPU virtual shim. Zero leaves NS1 unchanged.\n"
        "    void SetNativeSyncpointShim(GPUVAddr address);\n"
        "    static constexpr u32 NumShimSyncpoints = 192;\n\n"
        "    static constexpr bool HAS_FLUSH_INVALIDATION = true;").replace(
        "    void FlushCaching();",
        "    bool EnqueueDeferredCPUWrite(u64 address, u64 size);\n    void FlushCaching();").replace(
        "    Core::System& system;",
        "    ::Eden::GpuDeferredWrite::Queue deferred_cpu_write_queue;\n    Core::System& system;").replace(
        "    static std::atomic<size_t> unique_identifier_generator;\n\n"
        "    Common::ScratchBuffer<u8> tmp_buffer;",
        "    static std::atomic<size_t> unique_identifier_generator;\n"
        "    std::atomic<GPUVAddr> native_syncpoint_shim{0};\n\n"
        "    Common::ScratchBuffer<u8> tmp_buffer;"))
# This active M04 successor adds one read-only, acquire-load shim getter.
# Reconstruct the frozen source byte-for-byte after removing only that
# reviewed getter; retain the existing full header parity check.
current_m04 = maintained_m04.read_text()
shim_getter = (
    "    // A channel may expose only an existing, initialized shim mapping,\n"
    "    // never a guessed GPU virtual address.\n"
    "    [[nodiscard]] GPUVAddr GetNativeSyncpointShim() const noexcept {\n"
    "        return native_syncpoint_shim.load(std::memory_order_acquire);\n"
    "    }\n"
)
assert current_m04.count(shim_getter) == 1, "M04 selected getter source drift"
assert current_m04.replace(shim_getter, "", 1) == expected_m04, "M04 maintained header parity drift"
assert 'configure_file("${EDEN_DEFERRED_MEMORY_HEADER}"' in code
assert 'write_derived("${PORT_BUILD_DIR}/include/video_core/memory_manager.h"' not in code
assert 'target_include_directories(core PRIVATE "${EDEN_PORT_DIR}")' in base
assert 'target_include_directories(video_core PRIVATE "${EDEN_PORT_DIR}")' in base
assert "void SetNativeSyncpointShim(GPUVAddr address);" in maintained_m04.read_text()
assert "std::atomic<GPUVAddr> native_syncpoint_shim{0};" in maintained_m04.read_text()
print("ENCORE_M04_MAINTAINED_HEADER_PARITY_PASS", "ns2_syncpoint_shim=selected")

# M05: preserve the exactly generated experimental GPU-dirty collector.
pinned_dirty = (root/"vendor/sources/eden/src/core/gpu_dirty_memory_manager.h").read_text()
dirty_entry = "    void Collect(PAddr address, size_t size) {\n        TransformAddress t = BuildTransform(address, size);"
dirty_nested = "                    std::scoped_lock lk(guard);\n                    back_buffer.emplace_back(tmp);"
assert pinned_dirty.count(dirty_entry) == 1
assert pinned_dirty.count(dirty_nested) == 1
expected_dirty = pinned_dirty.replace(dirty_entry,
    "    void Collect(PAddr address, size_t size) {\n        std::scoped_lock lk(guard);\n        TransformAddress t = BuildTransform(address, size);").replace(
    dirty_nested, "                    back_buffer.emplace_back(tmp);")
maintained_dirty = root/"vendor/encore-active/eden/src/core/gpu_dirty_memory_manager_deferred.h"
assert maintained_dirty.read_text() == expected_dirty, "M05 maintained source differs from generated source"
assert 'configure_file("${EDEN_DEFERRED_DIRTY_HEADER}"' in code
assert 'write_derived("${PORT_BUILD_DIR}/deferred-core/core/gpu_dirty_memory_manager.h"' not in code
print("ENCORE_M05_MAINTAINED_DIRTY_HEADER_PARITY_PASS")

# M06: independently replay the former CMake replacement from a test-only
# oracle. CMake must never consume this fixture during a normal build.
original_m06 = (root/"vendor/sources/eden/src/video_core/memory_manager.cpp").read_text()
oracle_m06 = (root/"tools/fixtures/deferred-memory-manager-flush-oracle.inc").read_text()
assert original_m06.count('#include "memory_manager.h"') == 1
assert original_m06.count("void MemoryManager::FlushCaching() {") == 1
assert oracle_m06.count("bool MemoryManager::EnqueueDeferredCPUWrite(") == 1
assert oracle_m06.count("void MemoryManager::FlushCaching() {") == 1
expected_m06 = ('#include "core/gpu_dirty_memory_manager.h"\n'
    '#include "performance.h"\n'
    '#include "gpu_deferred_replay.h"\n' +
    original_m06.replace('#include "memory_manager.h"',
        '#include "video_core/memory_manager.h"').replace(
        "void MemoryManager::FlushCaching() {", oracle_m06))
assert maintained_m06.read_text() == expected_m06, "M06 source deviates from former generator"
assert 'configure_file("${EDEN_DEFERRED_MEMORY_SOURCE}"' in code
assert 'write_derived("${PORT_BUILD_DIR}/memory_manager_deferred.cpp"' not in code
print("ENCORE_M06_MAINTAINED_MEMORY_SOURCE_PARITY_PASS")

# M07 is the historic two-replacement Vulkan source, now owned as a
# full experimental translation unit. Normalize only the old absolute
# configure-time include path to the existing explicit video_core include root.
# The inactive guest-bridge intentionally uses CanExecuteDraw() in four
# callbacks; the native renderer uses CanExecuteRecordedDraw() to enforce
# the newer FIFO worker-bind latch. This is a deliberate integration variant,
# not a reason to silently change the guest draw path.
original_m07 = (root/"vendor/encore-active/eden/src/video_core/renderer_vulkan/vulkan_rasterizer.cpp").read_text()
# M07 was pinned before native MSAA. This later, independently reviewed
# Vulkan overlay is exactly reversible; first match the currently SELECTED
# vendor source blob, then revert its complete, context-anchored hunks.
# The original historical Task/Mesh SHA checks below remain unchanged.
# R23 #35 added a source-extracted vertex-attribute texture run path on
# top of the old M07 renderer. Reverse its exact full-source delta first,
# preserving the original M07/P24/MSAA witnesses verbatim.
r23_m07 = json.loads(
    (root / "tools/fixtures/r23-merged-vulkan-reverse.json").read_text())
assert r23_m07["schema_version"] == 1
r23_raster = next(item for item in r23_m07["files"]
                  if item["path"] == "vulkan_rasterizer.cpp")
def m07_source_blob(value):
    raw = value.encode("utf-8")
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
def reverse_attribute_index_batch_successor(source):
    current = m07_source_blob(source)
    if current == "39b2ed67e51937aecad666de4113ce792d32132d":
        newer, older = "VideoCore::RasterizerDownloadArea RasterizerVulkan::GetFlushArea(DAddr addr, u64 size) {\n    ::Eden::Performance::DiagnosticTimer guest_read_timer(::Eden::Performance::guest_cpu_read);\n    const VideoCore::RasterizerDownloadArea clean_area{\n        .start_address = Common::AlignDown(addr, Core::DEVICE_PAGESIZE),\n        .end_address = Common::AlignUp(addr + size, Core::DEVICE_PAGESIZE),\n        .preemtive = true,\n    };\n    // A clean/never-held texture page does not prove that a GPU-written\n    // storage buffer is current in guest memory. Query each cache independently:\n    // never-owned pages remain lock-free, and no two cache locks are nested.\n    std::optional<VideoCore::RasterizerDownloadArea> texture_area;\n    if (!::Eden::ImagePages::NeverHeld(addr, size)) {\n        ::Eden::Performance::GuestCacheLock(texture_cache.mutex, true);\n        std::lock_guard lock{texture_cache.mutex, std::adopt_lock};\n        texture_area = texture_cache.GetFlushArea(addr, size);\n    }\n    if (texture_area && !texture_area->preemtive) {\n        // The existing GPU sync flushes both cache domains.\n        return *texture_area;\n    }\n    auto area = texture_area.value_or(clean_area);\n    // Core::Memory caches the returned interval, not just the original\n    // scalar read. A preemptive texture can extend over other GPU-written\n    // buffers. Check EVERY byte the caller may subsequently read without\n    // re-entering GetFlushArea. Keep the original texture extent when clean.\n    const DAddr buffer_start = area.start_address;\n    const u64 buffer_size = area.end_address - buffer_start;\n    if (!::Eden::BufferPages::NeverRegistered(buffer_start, buffer_size)) {\n        ::Eden::Performance::GuestCacheLock(buffer_cache.mutex, false);\n        std::lock_guard lock{buffer_cache.mutex, std::adopt_lock};\n        if (buffer_cache.IsRegionGpuModified(buffer_start, buffer_size)) {\n            // Preserve the real GPU ownership and the existing ordered\n            // FlushRegion on the GPU worker. Do not certify stale siblings.\n            area.preemtive = false;\n        }\n    }\n    return area;\n}\n", "VideoCore::RasterizerDownloadArea RasterizerVulkan::GetFlushArea(DAddr addr, u64 size) {\n    ::Eden::Performance::DiagnosticTimer guest_read_timer(::Eden::Performance::guest_cpu_read);\n    const VideoCore::RasterizerDownloadArea clean_area{\n        .start_address = Common::AlignDown(addr, Core::DEVICE_PAGESIZE),\n        .end_address = Common::AlignUp(addr + size, Core::DEVICE_PAGESIZE),\n        .preemtive = true,\n    };\n    // A clean/never-held texture page does not prove that a GPU-written\n    // storage buffer is current in guest memory. Query each cache independently:\n    // never-owned pages remain lock-free, and no two cache locks are nested.\n    std::optional<VideoCore::RasterizerDownloadArea> texture_area;\n    if (!::Eden::ImagePages::NeverHeld(addr, size)) {\n        ::Eden::Performance::GuestCacheLock(texture_cache.mutex, true);\n        std::lock_guard lock{texture_cache.mutex, std::adopt_lock};\n        texture_area = texture_cache.GetFlushArea(addr, size);\n    }\n    if (texture_area && !texture_area->preemtive) {\n        // The existing GPU sync flushes both cache domains.\n        return *texture_area;\n    }\n    if (!::Eden::BufferPages::NeverRegistered(addr, size)) {\n        ::Eden::Performance::GuestCacheLock(buffer_cache.mutex, false);\n        std::lock_guard lock{buffer_cache.mutex, std::adopt_lock};\n        if (buffer_cache.IsRegionGpuModified(\n                clean_area.start_address, clean_area.end_address - clean_area.start_address)) {\n            // GPU::OnCPURead must not return early for buffer-only GPU writes.\n            // Keep any texture-covered extent, including its sibling bytes.\n            return VideoCore::RasterizerDownloadArea{\n                .start_address = texture_area\n                    ? (std::min)(texture_area->start_address, clean_area.start_address)\n                    : clean_area.start_address,\n                .end_address = texture_area\n                    ? (std::max)(texture_area->end_address, clean_area.end_address)\n                    : clean_area.end_address,\n                .preemtive = false,\n            };\n        }\n    }\n    return texture_area.value_or(clean_area);\n}\n"
        assert source.count(newer) == 1, "Guest readback extent successor drift"
        source = source.replace(newer, older, 1)
        current = m07_source_blob(source)
        assert current == "d8c093893b882175c46fb07c87193468da5f0f7a"
    if current == "d8c093893b882175c46fb07c87193468da5f0f7a":
        for newer, older in (("        // Indirect arguments are read, not overwritten. Preserve GPU dirty bytes.\n        const auto post_op = VideoCommon::ObtainBufferOperation::DoNothing;", "        const auto post_op = VideoCommon::ObtainBufferOperation::DiscardWrite;"), ("        buffer->MarkUsage(offset, 12);\n        scheduler.RequestOutsideRenderPassOperationContext();\n        // Lichii #1246: keep the input barrier in the dispatch command.", "        scheduler.RequestOutsideRenderPassOperationContext();\n        // Lichii #1246: keep the input barrier in the dispatch command.")):
            assert source.count(newer) == 1, "Indirect dispatch ownership successor drift"
            source = source.replace(newer, older, 1)
        current = m07_source_blob(source)
        assert current == "4a7ba88e47d686e3d277bee9df48f9b0d81a1248"
    if current == "4a7ba88e47d686e3d277bee9df48f9b0d81a1248":
        indirect_new = "        scheduler.RequestOutsideRenderPassOperationContext();\n        // Lichii #1246: keep the input barrier in the dispatch command. Vulkan\n        // ordering is unchanged, but one scheduler/worker command disappears.\n        scheduler.Record([pipeline, indirect_buffer = buffer->Handle(),\n                          indirect_offset = offset](vk::CommandBuffer cmdbuf) {\n            if (::Eden::DevVulkan::compute_barriers) {\n                cmdbuf.PipelineBarrier(vk::PIPELINE_STAGE_GRAPHICS_COMPUTE_TRANSFER,\n                                       VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT |\n                                           VK_PIPELINE_STAGE_DRAW_INDIRECT_BIT,\n                                       0, COMPUTE_INPUT_BARRIER);\n            }\n            if (!pipeline->IsBound()) {\n                return;\n            }"
        indirect_old = "        scheduler.RequestOutsideRenderPassOperationContext();\n        if (::Eden::DevVulkan::compute_barriers) {\n            scheduler.Record([](vk::CommandBuffer cmdbuf) {\n                cmdbuf.PipelineBarrier(vk::PIPELINE_STAGE_GRAPHICS_COMPUTE_TRANSFER,\n                                       VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT | VK_PIPELINE_STAGE_DRAW_INDIRECT_BIT,\n                                       0, COMPUTE_INPUT_BARRIER);\n            });\n        }\n        scheduler.Record([pipeline, indirect_buffer = buffer->Handle(),\n                          indirect_offset = offset](vk::CommandBuffer cmdbuf) {\n            if (!pipeline->IsBound()) {\n                return;\n            }"
        direct_new = "    static constexpr VkMemoryBarrier READ_BARRIER{\n        .sType = VK_STRUCTURE_TYPE_MEMORY_BARRIER,\n        .pNext = nullptr,\n        .srcAccessMask = VK_ACCESS_MEMORY_WRITE_BIT,\n        .dstAccessMask = VK_ACCESS_MEMORY_READ_BIT,\n    };\n    // Lichii #1246: this barrier was a separate scheduler command although\n    // nothing records Vulkan work between it and the dispatch.\n    scheduler.Record([pipeline, dim](vk::CommandBuffer cmdbuf) {\n        cmdbuf.PipelineBarrier(vk::PIPELINE_STAGE_GRAPHICS_COMPUTE_TRANSFER,\n                               VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT, 0, READ_BARRIER);\n        if (!pipeline->IsBound()) {"
        direct_old = "    static constexpr VkMemoryBarrier READ_BARRIER{\n        .sType = VK_STRUCTURE_TYPE_MEMORY_BARRIER,\n        .pNext = nullptr,\n        .srcAccessMask = VK_ACCESS_MEMORY_WRITE_BIT,\n        .dstAccessMask = VK_ACCESS_MEMORY_READ_BIT,\n    };\n    scheduler.Record([](vk::CommandBuffer cmdbuf) { cmdbuf.PipelineBarrier(vk::PIPELINE_STAGE_GRAPHICS_COMPUTE_TRANSFER, VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,\n                               0, READ_BARRIER); });\n    scheduler.Record([pipeline, dim](vk::CommandBuffer cmdbuf) {\n        if (!pipeline->IsBound()) {"
        assert source.count(indirect_new) == source.count(direct_new) == 1, "Compute barrier folding successor drift"
        source = source.replace(indirect_new, indirect_old, 1).replace(direct_new, direct_old, 1)
        current = m07_source_blob(source)
        assert current == "7049700a833c9e6cb239de8b01b5015dd7e3d163", ("Compute barrier folding predecessor drift", current)
    if current == "7049700a833c9e6cb239de8b01b5015dd7e3d163":
        newer = "void RasterizerVulkan::FlushCommands() {\n#ifdef PS5_NATIVE\n    // draw_counter measures graphics batching, not whether Vulkan work exists.\n    // DMA fills/copies and image transfers can record scheduler commands without\n    // any graphics draw. Conversely, a fence/explicit scheduler flush may have\n    // already submitted the current recording. Use the selected native\n    // scheduler's command epoch as the end-of-list authority.\n    draw_counter = 0;\n    if (!scheduler.RecordedSinceSubmit()) {\n        return;\n    }\n#else\n    if (draw_counter == 0) {\n        return;\n    }\n    draw_counter = 0;\n#endif\n    scheduler.Flush();\n}"
        older = "void RasterizerVulkan::FlushCommands() {\n    if (draw_counter == 0) {\n        return;\n    }\n    draw_counter = 0;\n    scheduler.Flush();\n}"
        assert source.count(newer) == 1, "DMA-only submit successor drift"
        source = source.replace(newer, older, 1)
        current = m07_source_blob(source)
        assert current == "f79943f596b8a95cdcb05ce74a964a2141ae10ac", ("DMA-only submit predecessor drift", current)
    if current != "f79943f596b8a95cdcb05ce74a964a2141ae10ac":
        return source
    newer = "#ifdef PS5_NATIVE\n    // FC27 uses a vertex-attribute texture handle on indexed triangle draws.\n    // OnCPUWrite is serialized by buffer_cache.mutex before guest memcpy, so\n    // this scan must stay under that lock. Reduce only repeated GMMU walks:\n    // prefetch a small, fully-mapped index span and decode sampled indices\n    // from it. Authenticated NS2 channels retain the original per-index path.\n    struct AttributeIndexBatch {\n        std::array<u8, 256> bytes{};\n        u32 first_position{};\n        u32 position_count{};\n        size_t index_width{};\n        bool valid{};\n    } index_batch;\n#endif\n    const auto read_index = [&](u32 position) {\n        const auto& indices = state.index_buffer;\n        const size_t index_width = indices.FormatSizeInBytes();\n        if (index_width == 0 || index_width > sizeof(u32)) return u32{};\n#ifdef PS5_NATIVE\n        if (!gpu_memory->UsesNativeTiling()) {\n            if (index_batch.valid && index_batch.index_width == index_width &&\n                position >= index_batch.first_position &&\n                position - index_batch.first_position < index_batch.position_count) {\n                u32 index{};\n                const size_t byte_offset =\n                    static_cast<size_t>(position - index_batch.first_position) * index_width;\n                std::memcpy(&index, index_batch.bytes.data() + byte_offset, index_width);\n                return index;\n            }\n            if (position < total) {\n                const size_t max_positions = index_batch.bytes.size() / index_width;\n                const u32 position_count =\n                    (std::min)(total - position, static_cast<u32>(max_positions));\n                const GPUVAddr offset = static_cast<GPUVAddr>(position) * index_width;\n                const GPUVAddr start = indices.IndexStart();\n                const GPUVAddr address = start + offset;\n                const size_t read_bytes = static_cast<size_t>(position_count) * index_width;\n                const bool address_ok =\n                    (position == 0 || offset / index_width == position) &&\n                    address >= start && read_bytes != 0 &&\n                    address <= ~GPUVAddr{0} - static_cast<GPUVAddr>(read_bytes);\n                if (position_count > 1 && address_ok &&\n                    gpu_memory->IsFullyMappedRange(address, read_bytes)) {\n                    gpu_memory->ReadBlockUnsafe(address, index_batch.bytes.data(), read_bytes);\n                    index_batch.first_position = position;\n                    index_batch.position_count = position_count;\n                    index_batch.index_width = index_width;\n                    index_batch.valid = true;\n                    u32 index{};\n                    std::memcpy(&index, index_batch.bytes.data(), index_width);\n                    return index;\n                }\n            }\n        }\n#endif\n        const GPUVAddr address = indices.IndexStart() +\n                                 static_cast<GPUVAddr>(position) * index_width;\n        u32 index{};\n        gpu_memory->ReadBlockUnsafe(address, &index, index_width);\n        return index;\n    };\n    const auto read_handle = [&](u32 position) {\n        const u32 vertex =\n            is_indexed ? static_cast<u32>(state.base_index + read_index(position))\n                       : state.vertex_buffer.first + position;"
    older = "    const auto read_handle = [&](u32 position) {\n        u32 vertex{};\n        if (is_indexed) {\n            const auto& indices = state.index_buffer;\n            const size_t index_width = indices.FormatSizeInBytes();\n            if (index_width == 0 || index_width > sizeof(u32)) return u32{};\n            const GPUVAddr address = indices.IndexStart() +\n                                     static_cast<GPUVAddr>(position) * index_width;\n            u32 index{};\n            gpu_memory->ReadBlockUnsafe(address, &index, index_width);\n            vertex = static_cast<u32>(state.base_index + index);\n        } else {\n            vertex = state.vertex_buffer.first + position;\n        }"
    assert source.count(newer) == 1
    source = source.replace(newer, older, 1)
    assert m07_source_blob(source) == "fcd174ed2326f3c205365b192c98f9d2f4d82ec3"
    return source

def reverse_collected_batch_preflight_successor(source):
    if m07_source_blob(source) != "fcd174ed2326f3c205365b192c98f9d2f4d82ec3":
        return source
    newer = "    // One owner-witness pass for the complete collected batch, as in\n    // InnerInvalidation. Each witness is monotonic and fails closed; once both\n    // cache domains may overlap, no later range can change the lock decision.\n    bool may_claim_buffer = false;\n    bool may_touch_texture = false;\n    for (const auto& [addr, size] : ranges) {\n        if (addr == 0 || size == 0) continue;\n        if (!may_claim_buffer && !::Eden::BufferPages::NeverRegistered(addr, size))\n            may_claim_buffer = true;\n        if (!may_touch_texture && !::Eden::ImagePages::NeverHeld(addr, size))\n            may_touch_texture = true;\n        if (may_claim_buffer && may_touch_texture) break;\n    }\n    // GPU-collected write batches acquire each cache domain only once. Claim\n    // still precedes every BufferCache write/readback below.\n"
    older = "    // Remove the complete CPU-write batch from GPU-owned ranges before any\n    // individual invalidation can download stale bytes over a later write.\n    // No registered buffer page in this CPU-write batch means no buffer can\n    // own GPU bytes to claim. Avoid the buffer mutex entirely in that case.\n    // NeverRegistered is monotonic and fails closed on unknown address spans.\n    bool may_claim_buffer = false;\n    for (const auto& [addr, size] : ranges) {\n        if (addr != 0 && size != 0 && !::Eden::BufferPages::NeverRegistered(addr, size)) {\n            may_claim_buffer = true;\n            break;\n        }\n    }\n    // The single-range invalidation callback takes the texture and buffer\n    // mutex once PER range. GPU-collected write batches often contain many\n    // pages; acquire each domain only once, as InnerInvalidation already\n    // does for the same texture -> buffer -> shader ordering. The prior\n    // ClaimCpuWrites still precedes every possible GPU sibling readback.\n    bool may_touch_texture = false;\n    for (const auto& [addr, size] : ranges) {\n        if (addr != 0 && size != 0 && !::Eden::ImagePages::NeverHeld(addr, size)) {\n            may_touch_texture = true;\n            break;\n        }\n    }\n"
    assert source.count(newer) == 1
    source = source.replace(newer, older, 1)
    assert m07_source_blob(source) == "e4948333ed15fba8024aeb4ffaa143a2e010f991"
    return source

def reverse_collected_batch_lock_successor(source):
    if m07_source_blob(source) != "e4948333ed15fba8024aeb4ffaa143a2e010f991":
        return source
    newer = "    if (may_claim_buffer) {\n        // Lichii 5e428570 / f5edeab: claim and apply the complete buffer batch\n        // under ONE acquisition. Texture state was handled above and is independent.\n        // Claim must precede BufferCache::WriteMemory so a sibling GPU download\n        // cannot overwrite a later CPU write from this same collected batch.\n        std::scoped_lock lock{buffer_cache.mutex};\n        buffer_cache.ClaimCpuWrites(ranges);\n        for (const auto& [addr, size] : ranges) {\n"
    older = "    if (may_claim_buffer) {\n        std::scoped_lock lock{buffer_cache.mutex};\n        for (const auto& [addr, size] : ranges) {\n"
    marker = "    // The single-range invalidation callback takes the texture and buffer\n"
    first = "    if (may_claim_buffer) {\n        std::scoped_lock lock{buffer_cache.mutex};\n        buffer_cache.ClaimCpuWrites(ranges);\n    }\n\n"
    assert source.count(newer) == source.count(marker) == 1
    source = source.replace(newer, older, 1).replace(marker, first + marker, 1)
    assert m07_source_blob(source) == "e5baa7f438d8caf11327989087db38ed1ca053a4"
    return source

# FC27 / Lichii #1518 remains available only in the inactive M07 developer
# replay source. Production was rolled back to synchronous page protection
# because Encore does not prove Lichii's scheduler-ownership guard. Authenticate
# both states, then reverse only the developer rasterizer hunk in memory so the
# historical M07 oracle below remains usable.
if m07_source_blob(original_m07) == "6f3378f1bb611c74ecfe1f5cd37283137462012a":
    subprocess.check_call(
        ["python3", "-B", "tools/check-source-tree-layout.py"],
        cwd=root / "vendor",
    )
    rasterizer_owner = root / "vendor/encore-active/eden/src/video_core/renderer_vulkan/vulkan_rasterizer.cpp"
    word_owner = root / "vendor/encore-active/eden/src/video_core/buffer_cache/word_manager.h"
    device_h = root / "vendor/encore-active/eden/src/core/device_memory_manager.h"
    device_inc = root / "vendor/encore-active/eden/src/core/device_memory_manager.inc"
    for owner in (rasterizer_owner, word_owner, device_h, device_inc):
        assert owner.is_file(), owner
    rasterizer_text = rasterizer_owner.read_text()
    word_text = word_owner.read_text()
    device_h_text = device_h.read_text()
    device_inc_text = device_inc.read_text()
    for forbidden in (
        "VideoCommon::DeferredPageCaching",
        "VideoCommon::t_deferred_page_caching",
        "device_memory.BeginDeferredCachedUpdates()",
        "device_memory.EndDeferredCachedUpdates()",
    ):
        assert forbidden not in rasterizer_text, forbidden
    for forbidden in ("class DeferredPageCaching", "t_deferred_page_caching"):
        assert forbidden not in word_text, forbidden
    for forbidden in (
        "BeginDeferredCachedUpdates",
        "EndDeferredCachedUpdates",
        "deferred_cached_updates",
    ):
        assert forbidden not in device_h_text + device_inc_text, forbidden
    for marker in (
        "GuestCacheLock(buffer_cache.mutex, false)",
        "if (buffer_cache.OnCPUWrite(addr, size))",
        "BufferWriteAhead::MarkFollowingPages",
    ):
        assert marker in rasterizer_text, marker

    current_page_untrack = """bool RasterizerVulkan::OnCPUWrite(DAddr addr, u64 size) {
    ::Eden::Performance::BatchedGuestWriteTimer guest_write_timer;
    const bool sample_guest_write = ::Eden::Performance::ShouldSampleGuestWrite();
    DEBUG_ASSERT(addr != 0 || size != 0);
    // Buffer and texture page evidence independently guards their mutexes.
    // Shader invalidation always runs, even if neither cache ever owned a page.
    if (!::Eden::BufferPages::NeverRegistered(addr, size)) {
        // Lichii #1518, adapted to Encore's single GPU worker: changing host
        // page protection can take microseconds and must not happen while the
        // guest CPU owns buffer_cache.mutex. Only non-GPU-owner threads defer
        // UNTRACK (-1) updates; tracking (+1) remains immediate. The device
        // memory epoch keeps Unmap from recycling a backing before those
        // deferred changes have landed.
        static thread_local VideoCommon::DeferredPageCaching deferred;
        const bool defer =
            VideoCommon::t_deferred_page_caching == nullptr &&
            !VideoCommon::GPUThread::IsWorkerThread();
        bool gpu_modified = false;
        bool apply_deferred = false;
        {
            ::Eden::Performance::CachePhaseTimer buffer_wait{
                ::Eden::Performance::CachePhase::GuestWriteBufferWait,
                sample_guest_write};
            ::Eden::Performance::GuestCacheLock(buffer_cache.mutex, false);
            buffer_wait.Stop();
            std::lock_guard lock{buffer_cache.mutex, std::adopt_lock};
            ::Eden::Performance::CachePhaseTimer buffer_work{
                ::Eden::Performance::CachePhase::GuestWriteBufferWork,
                sample_guest_write};
            if (defer) {
                VideoCommon::t_deferred_page_caching = &deferred;
            }
            gpu_modified = buffer_cache.OnCPUWrite(addr, size);
            if (!gpu_modified) {
                (void)::Eden::BufferWriteAhead::MarkFollowingPages(
                    static_cast<std::uint64_t>(addr),
                    static_cast<std::uint64_t>(size),
                    ::Eden::Performance::cpu_write_ahead.load(
                        std::memory_order_relaxed),
                    [&](std::uint64_t page, std::uint64_t span) {
                        return buffer_cache.IsRegionRegistered(
                            static_cast<DAddr>(page), span);
                    },
                    [&](std::uint64_t page, std::uint64_t span) {
                        return buffer_cache.OnCPUWrite(
                            static_cast<DAddr>(page), span);
                    });
            }
            if (defer) {
                VideoCommon::t_deferred_page_caching = nullptr;
                if (!deferred.Empty()) {
                    device_memory.BeginDeferredCachedUpdates();
                    apply_deferred = true;
                }
            }
        }
        if (apply_deferred) {
            deferred.ApplyAll();
            device_memory.EndDeferredCachedUpdates();
        }
        if (gpu_modified) {
            return true;
        }
    }
    // ImagePages is monotonically published before texture slot insertion.
    // Only never-held small ranges may skip the texture-cache mutex; unknown
    // and previously registered pages retain the full invalidation path.
    if (!::Eden::ImagePages::NeverHeld(addr, size)) {
        ::Eden::Performance::CachePhaseTimer texture_wait{
            ::Eden::Performance::CachePhase::GuestWriteTextureWait, sample_guest_write};
        ::Eden::Performance::GuestCacheLock(texture_cache.mutex, true);
        texture_wait.Stop();
        std::lock_guard lock{texture_cache.mutex, std::adopt_lock};
        ::Eden::Performance::CachePhaseTimer texture_work{
            ::Eden::Performance::CachePhase::GuestWriteTextureWork, sample_guest_write};
        texture_cache.WriteMemory(addr, size);
    }
    ::Eden::Performance::CachePhaseTimer shader_invalidate{
        ::Eden::Performance::CachePhase::GuestWriteShaderInvalidate, sample_guest_write};
    pipeline_cache.InvalidateRegion(addr, size);
    return false;
}
"""
    predecessor_page_untrack = rasterizer_text[
        rasterizer_text.index("bool RasterizerVulkan::OnCPUWrite("):
        rasterizer_text.index("\nvoid RasterizerVulkan::OnCacheInvalidations(")
    ]
    gpu_thread_include = '#include "video_core/gpu_thread.h"\n'
    assert original_m07.count(current_page_untrack) == 1
    assert original_m07.count(gpu_thread_include) == 1
    original_m07 = original_m07.replace(gpu_thread_include, "", 1)
    original_m07 = original_m07.replace(
        current_page_untrack, predecessor_page_untrack, 1
    )
    assert m07_source_blob(original_m07) == "ff8ad79ef203456063dbd848eab3ea575628edfc"
    print("ENCORE_M07_FC27_1518_INACTIVE_REPLAY_REVERSE_PASS production_sync=1")

# R457 MSAA fallback is later than the frozen R23/M07 source receipt.
# Verify both full blobs and undo only the reviewed owner hunk in memory.
# Keep the original source checks below; never modify the selected vendor.
# Native C797/C7C0 strict fence is a separate, reviewed Vulkan ABI owner.
# Reverse exactly its added method on this historical audit copy before
# replaying the older M07/FC27 rasterizer ownership graph.
if m07_source_blob(original_m07) == "ff8ad79ef203456063dbd848eab3ea575628edfc":
    native_fence_method = ("bool RasterizerVulkan::SignalNativeFence(std::function<void()>&& func) {\n"
                           "    fence_manager.SignalNativeFence(std::move(func));\n"
                           "    return true;\n"
                           "}\n")
    assert original_m07.count(native_fence_method) == 1, "Native fence source moved"
    original_m07 = original_m07.replace(native_fence_method, "", 1)
    assert m07_source_blob(original_m07) == "39b2ed67e51937aecad666de4113ce792d32132d", (
        "Native strict-fence predecessor drift")
    print("ENCORE_M07_NATIVE_STRICT_FENCE_EXACT_REVERSE_PASS")
m07_selected_sha = m07_source_blob(original_m07)
original_m07 = reverse_attribute_index_batch_successor(original_m07)
original_m07 = reverse_collected_batch_preflight_successor(original_m07)
original_m07 = reverse_collected_batch_lock_successor(original_m07)
m07_selected_sha = m07_source_blob(original_m07)
if m07_selected_sha == "e5baa7f438d8caf11327989087db38ed1ca053a4":
    strict_completion = "#ifdef PS5_NATIVE\nbool RasterizerVulkan::SignalNativeSyncPoint(u32 value) {\n    fence_manager.SignalNativeSyncPoint(value);\n    return true;\n}\n#endif\n\n"
    assert original_m07.count(strict_completion) == 1
    original_m07 = original_m07.replace(strict_completion, "", 1)
    m07_selected_sha = m07_source_blob(original_m07)
    assert m07_selected_sha == "f67815618d25657dcf64a87944b0c0bc5c2d8993"
if m07_selected_sha == "f67815618d25657dcf64a87944b0c0bc5c2d8993":
    # The merged native rasterizer has two independently qualified successors.
    # The vendor's source witness proves GuestCacheLock and all 16 integrated
    # C++ edits. Replay the next 15 historical differences on the audit copy
    # alone, then execute the original M07/R23 source and behavior receipts.
    receipt = runpy.run_path(str(root/"vendor/tests/native_msaa_handle_receipt.py"))
    assert receipt["GUEST_CACHE_LOCK_SUCCESSOR"] == m07_selected_sha
    original_m07 = receipt["restore_integrated_rasterizer"](original_m07)
    assert m07_source_blob(original_m07) == "71d097b9a83028dfad9370792c905bb3bfccfd5a"
    m07_lines = original_m07.split("\n")
    merged_m07_reversal = (
        (17, ["#include <optional>","","#include <fmt/format.h>",""], ["","#include <fmt/format.h>",""]),
        (296, ["    buffer_cache.SetPendingCpuWrites(","        [this](const std::function<void(DAddr, size_t)>& callback) {","            gpu.ForEachPendingCpuWrite(callback);","        });","#ifdef PS5_NATIVE","    native_compute_device_limits = device.GetPhysical().GetProperties().limits;","#endif"], ["#ifdef PS5_NATIVE","    native_compute_device_limits = device.GetPhysical().GetProperties().limits;","#endif"]),
        (617, ["    const auto prepare_attribute_handles = [&] {","        attribute_handle_pipeline = nullptr;","        attribute_handle_source.reset();","        attribute_handle_runs.clear();","        if (split_attribute_handles && !pipeline->IsMeshPipeline() && pipeline->UsesAttributeHandle()) {","            attribute_handle_source = pipeline->AttributeHandleSource();","            CollectAttributeHandleRuns(is_indexed);","            if (!attribute_handle_runs.empty()) {","                attribute_handle_pipeline = pipeline;","                pipeline->SetAttributeHandle(attribute_handle_runs.front().handle);","            }","        }","    };","    prepare_attribute_handles();","    bool pipeline_ok = pipeline->Configure(is_indexed);","    if (!pipeline_ok && pipeline->UsesForcedMsaaShadow()) {"], ["    attribute_handle_pipeline = nullptr;","    attribute_handle_runs.clear();","    if (split_attribute_handles && !mesh_draw && pipeline->UsesAttributeHandle()) {","        CollectAttributeHandleRuns(is_indexed);","        if (!attribute_handle_runs.empty()) {","            attribute_handle_pipeline = pipeline;","            pipeline->SetAttributeHandle(attribute_handle_runs.front().handle);","        }","    }","    bool pipeline_ok = pipeline->Configure(is_indexed);","    if (!pipeline_ok && pipeline->UsesForcedMsaaShadow()) {"]),
        (644, ["            // The 1x pipeline owns its own descriptor/attribute state. The","            // rejected shadow is not a valid owner for later split draws.","            prepare_attribute_handles();","            pipeline_ok = pipeline->Configure(is_indexed);","        }","    }"], ["            pipeline_ok = pipeline->Configure(is_indexed);","        }","    }"]),
        (679, ["    u32 component_byte_offset{};","    if (attribute_handle_source) {","        // Generic0X..Generic31W are four consecutive IR values per input.","        // Only 32-bit components can be read as an unmodified texture handle.","        constexpr u32 first = static_cast<u32>(Shader::IR::Attribute::Generic0X);","        constexpr u32 last = static_cast<u32>(Shader::IR::Attribute::Generic31W);","        const u32 encoded = *attribute_handle_source;","        if (encoded >= first && encoded <= last) {","            const u32 generic = (encoded - first) / 4;","            const u32 component = (encoded - first) % 4;","            if (generic < regs.vertex_attrib_format.size()) {","                const auto& attr = regs.vertex_attrib_format[generic];","                const bool is_32bit =","                    attr.size == VertexAttribute::Size::Size_R32 ||","                    attr.size == VertexAttribute::Size::Size_R32_G32 ||","                    attr.size == VertexAttribute::Size::Size_R32_G32_B32 ||","                    attr.size == VertexAttribute::Size::Size_R32_G32_B32_A32;","                if (!attr.constant && is_32bit && component < attr.ComponentCount() &&","                    (attr.type == VertexAttribute::Type::UInt ||","                     attr.type == VertexAttribute::Type::SInt ||","                     attr.type == VertexAttribute::Type::Float)) {","                    source = &attr;","                    component_byte_offset = component * sizeof(u32);","                }","            }","        }","    }","    if (!source && !attribute_handle_source) {","        // Only legacy shaders without an explicit source may use the old lookup","        // until the shader is recompiled. Never guess a component on an","        // unsupported packed or normalized attribute format.","        for (const auto& attr : regs.vertex_attrib_format) {","            if (attr.constant || attr.size == VertexAttribute::Size::Invalid) continue;","            if (attr.type == VertexAttribute::Type::UInt ||","                attr.type == VertexAttribute::Type::SInt) {","                source = &attr;","                break;","            }","        }","    }","    if (!source) {"], ["    for (const auto& attr : regs.vertex_attrib_format) {","        if (attr.constant || attr.size == VertexAttribute::Size::Invalid) continue;","        if (attr.type == VertexAttribute::Type::UInt ||","            attr.type == VertexAttribute::Type::SInt) {","            source = &attr;","            break;","        }","    }","    if (!source) {"]),
        (731, ["    const GPUVAddr base_address = stream.Address() + source->offset +","                                 component_byte_offset;","    const auto read_handle = [&](u32 position) {","        u32 vertex{};","        if (is_indexed) {"], ["    const GPUVAddr base_address = stream.Address() + source->offset;","    const auto read_handle = [&](u32 position) {","        u32 vertex{};","        if (is_indexed) {"]),
        (783, ["        attribute_handle_source.reset();","        attribute_handle_runs.clear();","    };","    PrepareDraw(is_indexed, [this, is_indexed, instance_count] {"], ["        attribute_handle_runs.clear();","    };","    PrepareDraw(is_indexed, [this, is_indexed, instance_count] {"]),
        (991, ["","    std::optional<VkRect2D> scissor;","    if (maxwell3d->regs.scissor_test[0].enable) {","        u32 up_scale = 1;","        u32 down_shift = 0;","        if (dst_rescaling) {","            up_scale = Settings::values.resolution_info.up_scale;","            down_shift = Settings::values.resolution_info.down_shift;","        }","        scissor = GetScissorState(maxwell3d->regs, 0, up_scale, down_shift);","    }","","    const auto& fb_images = framebuffer->Images();","    const auto fb_end = fb_images.begin() + framebuffer->NumImages();","    const bool src_is_target =","        std::find(fb_images.begin(), fb_end, texture.ImageHandle()) != fb_end;","    if (src_is_target && src_rescaling == dst_rescaling &&","        src_region.start.x == dst_region.start.x && src_region.start.y == dst_region.start.y &&","        src_region.end.x == dst_region.end.x && src_region.end.y == dst_region.end.y &&","        maxwell3d->regs.blend.enable[0] == 0) {","        return;","    }","","    blit_image.BlitColor(framebuffer, texture.RenderTarget(), texture.ImageHandle(),","                         sampler->Handle(), dst_region, src_region, src_size, scissor);","}",""], ["    blit_image.BlitColor(framebuffer, texture.RenderTarget(), texture.ImageHandle(),","                         sampler->Handle(), dst_region, src_region, src_size);","#ifdef PS5_NATIVE","    // Raw-image blit directly binds its own Vulkan graphics pipeline.","    // It does not invalidate Scheduler's cached guest graphics state.","    // Ensure the following guest draw rebinds pipeline and descriptors.","    scheduler.InvalidateState();","#endif","}",""]),
        (2445, ["        // Claim the ENTIRE CPU-write batch before WriteMemory on any range.","        // Otherwise its GPU sibling download may overwrite a later write","        // within the same page (Lichii #1328). The lock and draw order stay.","        buffer_cache.ClaimCpuWrites(sequences);","        for (const auto& [addr, size] : sequences) {","            if (!::Eden::BufferPages::NeverRegistered(addr, size)) {","                buffer_cache.WriteMemory(addr, size);"], ["        for (const auto& [addr, size] : sequences) {","            if (!::Eden::BufferPages::NeverRegistered(addr, size)) {","                buffer_cache.WriteMemory(addr, size);"]),
        (2509, ["void RasterizerVulkan::OnCacheInvalidations(std::span<const std::pair<DAddr, u64>> ranges) {","    // Remove the complete CPU-write batch from GPU-owned ranges before any","    // individual invalidation can download stale bytes over a later write.","    // No registered buffer page in this CPU-write batch means no buffer can","    // own GPU bytes to claim. Avoid the buffer mutex entirely in that case.","    // NeverRegistered is monotonic and fails closed on unknown address spans.","    bool may_claim_buffer = false;","    for (const auto& [addr, size] : ranges) {","        if (addr != 0 && size != 0 && !::Eden::BufferPages::NeverRegistered(addr, size)) {","            may_claim_buffer = true;","            break;","        }","    }","    if (may_claim_buffer) {","        std::scoped_lock lock{buffer_cache.mutex};","        buffer_cache.ClaimCpuWrites(ranges);","    }","","    // The single-range invalidation callback takes the texture and buffer","    // mutex once PER range. GPU-collected write batches often contain many","    // pages; acquire each domain only once, as InnerInvalidation already","    // does for the same texture -> buffer -> shader ordering. The prior","    // ClaimCpuWrites still precedes every possible GPU sibling readback.","    bool may_touch_texture = false;","    for (const auto& [addr, size] : ranges) {","        if (addr != 0 && size != 0 && !::Eden::ImagePages::NeverHeld(addr, size)) {","            may_touch_texture = true;","            break;","        }","    }","    if (may_touch_texture) {","        std::scoped_lock lock{texture_cache.mutex};","        for (const auto& [addr, size] : ranges) {","            if (addr != 0 && size != 0 && !::Eden::ImagePages::NeverHeld(addr, size)) {","                texture_cache.WriteMemory(addr, size);","            }","        }","    }","    if (may_claim_buffer) {","        std::scoped_lock lock{buffer_cache.mutex};","        for (const auto& [addr, size] : ranges) {","            if (addr != 0 && size != 0 && !::Eden::BufferPages::NeverRegistered(addr, size)) {","                buffer_cache.WriteMemory(addr, size);","            }","        }","    }","    // Guest shaders always observe invalidation, including writes into","    // pages that have never held a BufferCache or TextureCache allocation.","    for (const auto& [addr, size] : ranges) {","        if (addr != 0 && size != 0) {","            pipeline_cache.InvalidateRegion(addr, size);","        }","    }","}","","void RasterizerVulkan::OnCacheInvalidation(DAddr addr, u64 size) {","    if (addr == 0 || size == 0) {","        return;"], ["void RasterizerVulkan::OnCacheInvalidation(DAddr addr, u64 size) {","    if (addr == 0 || size == 0) {","        return;"]),
        (2601, ["        buffer_cache.WriteMemory(addr, size, false);","    }","    pipeline_cache.OnCacheInvalidation(addr, size);","}"], ["        buffer_cache.WriteMemory(addr, size);","    }","    pipeline_cache.OnCacheInvalidation(addr, size);","}"]),
        (2700, ["#ifdef PS5_NATIVE","    // Both native caches share the same RADV/PS5 GPU-memory budget.","    // Query ONCE before either guest cache mutex, retaining original","    // texture and buffer GC thresholds and retirement ordering.","    const std::optional<u64> frame_memory_usage =","        texture_cache_runtime.CanReportMemoryUsage()","            ? std::optional<u64>{texture_cache_runtime.GetDeviceMemoryUsage()}","            : std::nullopt;","#endif","    {","#ifdef PS5_NATIVE","        ::Eden::Performance::CachePhaseTimer texture_wait{"], ["    {","#ifdef PS5_NATIVE","        ::Eden::Performance::CachePhaseTimer texture_wait{"]),
        (2720, ["#ifdef PS5_NATIVE","        texture_cache.TickFrame(frame_memory_usage);","#else","        texture_cache.TickFrame();","#endif","    }","","    {"], ["        texture_cache.TickFrame();","    }","    {"]),
        (2738, ["#ifdef PS5_NATIVE","        buffer_cache.TickFrame(frame_memory_usage);","#else","        buffer_cache.TickFrame();","#endif","    }","}"], ["        buffer_cache.TickFrame();","    }","}"]),
        (2886, ["    // A buffer DMA updates guest memory without invoking the texture-cache","    // CPU-write callback. Hold both cache locks over the ownership decision","    // and copy so another thread cannot publish a newer image in between.","    // Lichii c84935f / 47d2368 / 36bfb77: only invalidate destination images","    // whose latest bytes are already in guest memory. Skip the unsafe case","    // rather than uploading stale CPU bytes over GPU-owned image contents.","    std::scoped_lock lock{buffer_cache.mutex, texture_cache.mutex};","    bool copied_gpu_bytes = false;","    if (!buffer_cache.DMACopy(src_address, dest_address, amount, &copied_gpu_bytes)) {","        return false;","    }","    if (!copied_gpu_bytes &&","        !texture_cache.IsGpuMemoryGpuModified(src_address, amount) &&","        !texture_cache.IsGpuMemoryGpuModified(dest_address, amount)) {","        texture_cache.WriteGpuMemory(dest_address, amount);","    }","    return true;","}","","template <bool IS_IMAGE_UPLOAD>"], ["    std::scoped_lock lock{buffer_cache.mutex};","    return buffer_cache.DMACopy(src_address, dest_address, amount);","}","","template <bool IS_IMAGE_UPLOAD>"]),
    )
    for index, selected, predecessor in reversed(merged_m07_reversal):
        assert m07_lines[index:index+len(selected)] == selected, ("M07 merged hunk drift", index)
        m07_lines[index:index+len(selected)] = predecessor
    original_m07 = "\n".join(m07_lines)
    m07_selected_sha = m07_source_blob(original_m07)
    assert m07_selected_sha == "5b04321fa45d6b5e6af1d4b17bcf695348d0dd90"
    print("ENCORE_M07_NS1_NS2_SELECTED_PREDECESSOR_PASS", "integrated_hunks=16", "historical_hunks=15")
# Vendor #194: the exact shipping FC27 post-buffer-lock page-protection
# publication is newer than M07. Remove only its reviewed hunk AND header
# from the historical audit copy, then keep all M07/R23/MSAA proofs intact.
if m07_selected_sha == "38d5630570675088a0620ef533112bb314a40ae8":
    receipt_path = root / "vendor/tests/native_msaa_handle_receipt.py"
    receipt_text = receipt_path.read_text()
    assert m07_source_blob(receipt_text) == "236713fa06672b39e2a4b9a84907882bbbb1bbbd"
    receipt = runpy.run_path(str(receipt_path))
    assert receipt["CURRENT_DEFERRED_PAGE_PROTECTION"] == m07_selected_sha
    assert receipt["CURRENT_PAGE_SIBLING"] == "01c6880e5a8836da45601b0a3cb7c0fd6c46cf35"
    before, after = receipt["DEFERRED_BEFORE"], receipt["DEFERRED_AFTER"]
    include = receipt["DEFERRED_INCLUDE"]
    assert original_m07.count(after) == original_m07.count(include) == 1
    assert before not in original_m07
    original_m07 = original_m07.replace(include, "", 1).replace(after, before, 1)
    m07_selected_sha = m07_source_blob(original_m07)
    assert m07_selected_sha == receipt["CURRENT_PAGE_SIBLING"]
    print("ENCORE_M07_FC27_DEFERRED_PAGE_EXACT_REVERSE_PASS")
# FC27 sibling-page preservation was added after the frozen M07/R23 chain.
# Unmap is the one call site where page siblings must NOT be downloaded because
# the mapping is being destroyed. Reverse that reviewed call-site flag only.
if m07_selected_sha == "01c6880e5a8836da45601b0a3cb7c0fd6c46cf35":
    current_unmap = "        buffer_cache.WriteMemory(addr, size, false);\n"
    historical_unmap = "        buffer_cache.WriteMemory(addr, size);\n"
    assert original_m07.count(current_unmap) == 1
    original_m07 = original_m07.replace(current_unmap, historical_unmap, 1)
    m07_selected_sha = m07_source_blob(original_m07)
    assert m07_selected_sha == "aa3ff8baf97f075d1adf44a9d19335c89403c8e1"
    print("ENCORE_M07_FC27_GPU_PAGE_SIBLING_UNMAP_EXACT_REVERSE_PASS")
if m07_selected_sha == "aa3ff8baf97f075d1adf44a9d19335c89403c8e1":
    receipt_path = root / "vendor/tests/native_msaa_handle_receipt.py"
    receipt_text = receipt_path.read_text()
    assert m07_source_blob(receipt_text) == (
        "236713fa06672b39e2a4b9a84907882bbbb1bbbd"
        if (
            subprocess.check_output(["git", "-C", str(root/"vendor"), "rev-parse", "HEAD"],
                                    text=True).strip() == "87b5a4d674e2a1616cd19b5234203e80920abcc4" or
            (root/"vendor/encore-active/eden/src/video_core/renderer_vulkan/vulkan_rasterizer.cpp").read_text().find(
                'core/deferred_cached_updates.h') >= 0
        ) else
        "18bf879c31b6d29b77b8fc6cc3026f8bd7fc0ec2")
    receipt = runpy.run_path(str(receipt_path))
    assert receipt["CURRENT_DRAWTEXTURE"] == m07_selected_sha
    draw_after = receipt["DRAW_TEXTURE_AFTER"]
    draw_before = receipt["DRAW_TEXTURE_BEFORE"]
    assert original_m07.count("#include <optional>\n") == 1
    assert original_m07.count(draw_after) == 1 and draw_before not in original_m07
    original_m07 = original_m07.replace("#include <optional>\n", "", 1)
    original_m07 = original_m07.replace(draw_after, draw_before, 1)
    m07_selected_sha = m07_source_blob(original_m07)
    assert m07_selected_sha == "1c40cc3b968c76fc505f5cea63218b93e89b4529"
    print("ENCORE_M07_EDEN4559_DRAWTEXTURE_REVERSE_EXACT_PASS")
if m07_selected_sha == "1c40cc3b968c76fc505f5cea63218b93e89b4529":
    fc27_constructor = """    buffer_cache.SetPendingCpuWrites(
        [this](const std::function<void(DAddr, size_t)>& callback) {
            gpu.ForEachPendingCpuWrite(callback);
        });
"""
    fc27_batch = """void RasterizerVulkan::OnCacheInvalidations(std::span<const std::pair<DAddr, u64>> ranges) {
    // Remove the complete CPU-write batch from GPU-owned ranges before any
    // individual invalidation can download stale bytes over a later write.
    {
        std::scoped_lock lock{buffer_cache.mutex};
        buffer_cache.ClaimCpuWrites(ranges);
    }
    for (const auto& [addr, size] : ranges) OnCacheInvalidation(addr, size);
}

"""
    assert original_m07.count(fc27_constructor) == original_m07.count(fc27_batch) == 1
    original_m07 = original_m07.replace(fc27_constructor, "", 1).replace(fc27_batch, "", 1)
    m07_selected_sha = m07_source_blob(original_m07)
    assert m07_selected_sha == "efd77028f0710ea9e50cbbe77b04eebf3f306610"
    print("ENCORE_M07_FC27_CPU_WRITE_REVERSE_EXACT_PASS")
if m07_selected_sha == "efd77028f0710ea9e50cbbe77b04eebf3f306610":
    m07_msaa_before = "    // Mesh draw workgroups are not indexed vertices. Only standard vertex\n    // draw calls may be split into handle-homogeneous runs.\n    attribute_handle_pipeline = nullptr;\n    attribute_handle_runs.clear();\n    if (split_attribute_handles && !mesh_draw && pipeline->UsesAttributeHandle()) {\n        CollectAttributeHandleRuns(is_indexed);\n        if (!attribute_handle_runs.empty()) {\n            attribute_handle_pipeline = pipeline;\n            pipeline->SetAttributeHandle(attribute_handle_runs.front().handle);\n        }\n    }\n    bool pipeline_ok = pipeline->Configure(is_indexed);\n    if (!pipeline_ok && pipeline->UsesForcedMsaaShadow()) {\n        // The shader may read/store its destination or the texture cache\n        // may have ended the shadow pass while binding descriptors.\n        // Resolve and RETRY this draw via the unchanged guest 1x pipeline.\n        if (native_msaa_shadow) (void)native_msaa_shadow->EndPrepared();\n        native_msaa_clear.reset();\n        native_samples = VK_SAMPLE_COUNT_1_BIT;\n        pipeline = pipeline_cache.CurrentGraphicsPipeline();\n        if (pipeline) {\n            prepared_pipeline = pipeline;\n            probe_pipeline = pipeline;\n            pipeline->SetEngine(maxwell3d, gpu_memory);\n            pipeline_ok = pipeline->Configure(is_indexed);\n        }\n    }\n"
    m07_msaa_after = "    // Mesh draw workgroups are not indexed vertices. Only standard vertex\n    // draw calls may be split into handle-homogeneous runs.\n    const auto prepare_attribute_handles = [&] {\n        attribute_handle_pipeline = nullptr;\n        attribute_handle_runs.clear();\n        if (split_attribute_handles && !pipeline->IsMeshPipeline() && pipeline->UsesAttributeHandle()) {\n            CollectAttributeHandleRuns(is_indexed);\n            if (!attribute_handle_runs.empty()) {\n                attribute_handle_pipeline = pipeline;\n                pipeline->SetAttributeHandle(attribute_handle_runs.front().handle);\n            }\n        }\n    };\n    prepare_attribute_handles();\n    bool pipeline_ok = pipeline->Configure(is_indexed);\n    if (!pipeline_ok && pipeline->UsesForcedMsaaShadow()) {\n        // The shader may read/store its destination or the texture cache\n        // may have ended the shadow pass while binding descriptors.\n        // Resolve and RETRY this draw via the unchanged guest 1x pipeline.\n        if (native_msaa_shadow) (void)native_msaa_shadow->EndPrepared();\n        native_msaa_clear.reset();\n        native_samples = VK_SAMPLE_COUNT_1_BIT;\n        pipeline = pipeline_cache.CurrentGraphicsPipeline();\n        if (pipeline) {\n            prepared_pipeline = pipeline;\n            probe_pipeline = pipeline;\n            pipeline->SetEngine(maxwell3d, gpu_memory);\n            // The 1x pipeline owns its own descriptor/attribute state. The\n            // rejected shadow is not a valid owner for later split draws.\n            prepare_attribute_handles();\n            pipeline_ok = pipeline->Configure(is_indexed);\n        }\n    }\n"
    assert original_m07.count(m07_msaa_after) == 1 and m07_msaa_before not in original_m07
    original_m07 = original_m07.replace(m07_msaa_after, m07_msaa_before, 1)
    assert m07_source_blob(original_m07) == "5b04321fa45d6b5e6af1d4b17bcf695348d0dd90"
    print("ENCORE_M07_R457_MSAA_HANDLE_REVERSE_EXACT_PASS")
else:
    assert m07_selected_sha == "5b04321fa45d6b5e6af1d4b17bcf695348d0dd90", m07_selected_sha
# The selected vendor added the reviewed FC27 teardown UAF fix AFTER R23.
# Strip ONLY its exact destructor hunk in memory before comparing the
# historical R23 source hash. Never rewrite the frozen R23/MSAA receipts.
post_query_revoke = (
    "RasterizerVulkan::~RasterizerVulkan() {\n"
    "    // QueryCache has a shorter lifetime than BufferCache. BufferCache::~\n"
    "    // triggers a final scheduler.Finish() AFTER QueryCache is destroyed.\n"
    "    // Drain outstanding queries while alive, then revoke the borrowed pointer\n"
    "    // to prevent the shutdown path from reading freed QueryCache storage.\n"
    "    scheduler.WaitWorker();\n"
    "    scheduler.Finish();\n"
    "    scheduler.ClearQueryCache();\n"
    "}\n"
)
pre_query_revoke = (
    "RasterizerVulkan::~RasterizerVulkan() {\n"
    "    scheduler.WaitWorker();\n"
    "    scheduler.Finish();\n"
    "}\n"
)
assert original_m07.count(post_query_revoke) == 1, (
    "FC27 teardown lifetime guard missing/moved; do not silently bypass")
original_m07 = original_m07.replace(post_query_revoke, pre_query_revoke, 1)
print("ENCORE_M07_QUERYCACHE_TEARDOWN_REVERSIBLE_PASS")
assert m07_source_blob(original_m07) == r23_raster["post_r23_blob"], (
    "Unreviewed R23 renderer source in M07")
for reverse_hunk in reversed(r23_raster["patches"]):
    assert original_m07.count(reverse_hunk["after"]) == 1, (
        "R23 M07 reverse hunk moved")
    original_m07 = original_m07.replace(
        reverse_hunk["after"], reverse_hunk["before"], 1)
assert m07_source_blob(original_m07) == r23_raster["pre_r23_blob"], (
    "R23 renderer failed to reconstruct M07 source")
print("ENCORE_M07_R23_REVERSE_EXACT_PASS", "native_R23_preserved=1")
post_msaa_receipt = json.loads(
    (root / "tools/fixtures/p24-post-msaa-reversible-deltas.json").read_text())
assert post_msaa_receipt["schema_version"] == 1
msaa_owner = next(item for item in post_msaa_receipt["files"]
                  if item["path"] == "vulkan_rasterizer.cpp")
def m07_git_blob(text):
    data = text.encode("utf-8")
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
# G07 is a separately reviewed post-MSAA write-commit transaction change.
# Reverse exactly this one hunk for historical proof; never restamp the
# P24/M07 receipt or allow unrelated vendor bytes to pass its old SHA.
g07_old_commit = "            if (!resources->ValidateGpuBufferMappings(\n                    [this](u64 address, u32 bytes) {\n                        return Shader::Ampere::NativeQmdContiguousGpuSpan(\n                            address, bytes, [this](u64 page) {\n                                return gpu_memory->GpuToCpuAddress(page);\n                            });\n                    }))\n                return false;"
g07_new_commit = "            // A VA can stay mapped while a guest remaps its physical pages.\n            // Recheck the exact pre-staging backing here, under the commit\n            // lock, not merely contiguous coverage. Matches also validates\n            // the full 49-bit span, so no second mapping walk is needed.\n            if (!staged_buffer_mappings.Matches(\n                    *resources, [this](u64 address) {\n                        return gpu_memory->GpuToCpuAddress(address);\n                    }))\n                return false;"
assert original_m07.count(g07_new_commit) == 1, (
    "M07 native G07 physical-remap hunk drift")
historical_m07 = original_m07.replace(g07_new_commit, g07_old_commit, 1)
assert m07_git_blob(historical_m07) == msaa_owner["post_change_raw_blob_sha"], (
    "M07 unreviewed post-P24 MSAA rasterizer source")
m07_premesh_source = historical_m07
# Post-P24 MSAA spans were recorded AFTER the native KeplerCompute pointer
# change. The pointer guard belongs to the separate, older ABI receipt.
# Normalize the pointer ABI FIRST, matching the same order as the
# strict Vulkan fork parity check.
# M07 was created before the reviewed P2.4 Task/Mesh Vulkan deltas.
# Reverse exactly the separately SHA-pinned mesh hunks to compare the
# historical inactive variant; NEVER remove mesh functionality from shipping.
receipt = json.loads((root/"tools/fixtures/p24-task-mesh-vulkan-deltas.json").read_text())
mesh_rasterizer = next(item for item in receipt["files"]
                       if item["path"] == "vulkan_rasterizer.cpp")
# Reverse only the separately reviewed KeplerCompute pointer ABI
# correction before normalizing the historical Task/Mesh and DEV variants.
# This is an exact proof against the original recorded maintained blob.
native_begin = "bool RasterizerVulkan::DispatchNativeCompute("
assert historical_m07.count(native_begin) == 1
native_start = historical_m07.index(native_begin)
native_end = historical_m07.index("\nvoid RasterizerVulkan::", native_start)
native_body = historical_m07[native_start:native_end]
null_guard = """    // ChannelStateCache binds a KeplerCompute pointer; only native process
    // tickets authorize dereference, and the channel may be unbound.
    if (!kepler_compute) return false;
"""
assert native_body.count(null_guard) == 1
assert native_body.count("kepler_compute->regs") == 5
assert native_body.count("*kepler_compute, *gpu_memory") == 6
native_body = native_body.replace(null_guard, "").replace(
    "kepler_compute->regs", "kepler_compute.regs").replace(
    "*kepler_compute, *gpu_memory", "kepler_compute, *gpu_memory")
m07_before_mesh = historical_m07[:native_start] + native_body + historical_m07[native_end:]
for hunk in reversed(msaa_owner["reverse_hunks"]):
    assert m07_before_mesh.count(hunk["after"]) == 1, (
        "M07 post-P24 MSAA reversible owner drift")
    m07_before_mesh = m07_before_mesh.replace(hunk["after"], hunk["before"])
reviewed_bytes = m07_before_mesh.encode("utf-8")
reviewed_sha = hashlib.sha1(b"blob " + str(len(reviewed_bytes)).encode() + b"\0" + reviewed_bytes).hexdigest()
assert reviewed_sha == mesh_rasterizer["maintained_blob_sha"], (
    "M07 unreviewed KeplerCompute ABI change")
for hunk in reversed(mesh_rasterizer["hunks"]):
    assert m07_before_mesh.count(hunk["after"]) == 1, "P2.4 native mesh hunk moved"
    m07_before_mesh = m07_before_mesh.replace(hunk["after"], hunk["before"])
m07_data = m07_before_mesh.encode("utf-8")
m07_sha = hashlib.sha1(b"blob " + str(len(m07_data)).encode() + b"\0" + m07_data).hexdigest()
assert m07_sha == mesh_rasterizer["pinned_blob_sha"], "M07 historical native baseline drift"
m07_entry = "bool RasterizerVulkan::OnCPUWrite(DAddr addr, u64 size) {"
m07_buffer_lock = "        ::Eden::Performance::GuestCacheLock(buffer_cache.mutex, false);"
assert original_m07.count(m07_entry) == original_m07.count(m07_buffer_lock) == 1
m07_entry_with_guard = """bool RasterizerVulkan::OnCPUWrite(DAddr addr, u64 size) {
    const bool defer_candidate =
        ::Eden::GpuDeferredWrite::kNativePostStorePublicationReady &&
        ::Eden::Performance::cpu_write_defer.load(std::memory_order_relaxed) &&
        ::Eden::GpuDeferredWrite::guest_write_origin_core < ::Eden::GpuDeferredWrite::Queue::Cores &&
        ::Eden::GpuDeferredWrite::guest_write_intent ==
            ::Eden::GpuDeferredWrite::GuestWriteIntent::StoreFollows &&
        !::Eden::GpuDeferredWrite::replaying_guest_write;"""
m07_lock_with_fallback = """
        if (!defer_candidate) {
            ::Eden::Performance::GuestCacheLock(buffer_cache.mutex, false);
        } else if (!buffer_cache.mutex.try_lock()) {
            if (gpu_memory->EnqueueDeferredCPUWrite(addr, size)) return false;
            ::Eden::Performance::GuestCacheLock(buffer_cache.mutex, false);
        }"""
# Require exactly the four known Draw/DrawIndirect callback differences.
# Keep byte-for-byte parity for everything else, including F07 HUD flushing.
m07_native_draw_guard = "CanExecuteRecordedDraw()"
m07_guest_draw_guard = "CanExecuteDraw()"
maintained_m07_text = maintained_m07.read_text()
assert original_m07.count(m07_native_draw_guard) == 4
assert original_m07.count(m07_guest_draw_guard) == 0
assert maintained_m07_text.count(m07_guest_draw_guard) == 4
assert maintained_m07_text.count(m07_native_draw_guard) == 0
expected_m07 = ('#include "gpu_deferred_replay.h"\n'
                '#include "video_core/memory_manager.h"\n' +
                m07_before_mesh.replace(m07_entry, m07_entry_with_guard).replace(
                    m07_buffer_lock, m07_lock_with_fallback).replace(
                    m07_native_draw_guard, m07_guest_draw_guard))
# The inactive guest bridge must retain the SAME reviewed G07 write-commit
# safety fix, not merely match the historical pre-G07 decoder snapshot.
# The historical renderer has TWO independent mapped-span guards:
# pre-stage admission and final write-commit. Replace ONLY the latter;
# accidentally replacing initial admission would mask a real GMMU regression.
assert expected_m07.count(g07_old_commit) == 2
last_commit_guard = expected_m07.rfind(g07_old_commit)
assert last_commit_guard > expected_m07.index("bool RasterizerVulkan::DispatchNativeCompute(")
expected_m07 = (expected_m07[:last_commit_guard] + g07_new_commit +
                expected_m07[last_commit_guard + len(g07_old_commit):])
assert expected_m07.count(g07_old_commit) == 1
# The maintained guest bridge carries the same reviewed FC27 unmap policy as
# the active renderer. Re-apply ONLY that call-site flag after reconstructing
# the historical M07 body, so parity still rejects every unrelated byte.
bridge_unmap_before = """    if (!::Eden::BufferPages::NeverRegistered(addr, size)) {
        std::scoped_lock lock{buffer_cache.mutex};
        buffer_cache.WriteMemory(addr, size);
    }
"""
bridge_unmap_after = """    if (!::Eden::BufferPages::NeverRegistered(addr, size)) {
        std::scoped_lock lock{buffer_cache.mutex};
        buffer_cache.WriteMemory(addr, size, false);
    }
"""
# Guest-bridge is an inactive DEV variant, not the compiled release
# rasterizer. The merged vendor retains three independently reviewed runtime
# fixes for guest-read BufferCache dirty bytes and fragmented GMMU writes.
# Preserve those in the source; reverse only an audit copy to the exact
# historic DEV witness, then run the existing whole-header/source comparisons.
if m07_source_blob(maintained_m07_text) == "edaa82feb71665e4b6fbfd3ff34d80378e3bca73":
    for protection in (
        "buffer_cache.IsRegionGpuModified(",
        "gpu_memory->IsFullyMappedRange(address, copy_size)",
        "gpu_memory->WriteBlock(address, memory.data(), copy_size)",
    ):
        assert protection in maintained_m07_text, ("DEV bridge safeguard missing", protection)
    m07_lines = maintained_m07_text.split("\n")
    bridge_delta = (
        (1979, ["    const VideoCore::RasterizerDownloadArea clean_area{","        .start_address = Common::AlignDown(addr, Core::DEVICE_PAGESIZE),","        .end_address = Common::AlignUp(addr + size, Core::DEVICE_PAGESIZE),","        .preemtive = true,"], ["    // A guest read cannot overlap a registered image when no page in this","    // range has ever appeared in the image slot map. Skip the GPU-held mutex.","    // Unknown/out-of-range/large ranges retain the original blocking path.","    if (::Eden::ImagePages::NeverHeld(addr, size)) {","        return VideoCore::RasterizerDownloadArea{","            .start_address = Common::AlignDown(addr, Core::DEVICE_PAGESIZE),","            .end_address = Common::AlignUp(addr + size, Core::DEVICE_PAGESIZE),","            .preemtive = true,","        };","    }","    {","        ::Eden::Performance::GuestCacheLock(texture_cache.mutex, true);","        std::lock_guard lock{texture_cache.mutex, std::adopt_lock};","        auto area = texture_cache.GetFlushArea(addr, size);","        if (area) {","            return *area;","        }","    }","    VideoCore::RasterizerDownloadArea new_area{","        .start_address = Common::AlignDown(addr, Core::DEVICE_PAGESIZE),","        .end_address = Common::AlignUp(addr + size, Core::DEVICE_PAGESIZE),","        .preemtive = true,"]),
        (1984, ["    // A clean/never-held texture page does not prove that a GPU-written","    // storage buffer is current in guest memory. Query each cache independently:","    // never-owned pages remain lock-free, and no two cache locks are nested.","    std::optional<VideoCore::RasterizerDownloadArea> texture_area;","    if (!::Eden::ImagePages::NeverHeld(addr, size)) {","        ::Eden::Performance::GuestCacheLock texture_wait(texture_cache.mutex, true);","        std::lock_guard lock{texture_cache.mutex, std::adopt_lock};","        texture_area = texture_cache.GetFlushArea(addr, size);","    }","    if (texture_area && !texture_area->preemtive) {","        // The existing GPU sync flushes both cache domains.","        return *texture_area;","    }","    if (!::Eden::BufferPages::NeverRegistered(addr, size)) {","        ::Eden::Performance::GuestCacheLock buffer_wait(buffer_cache.mutex, true);","        std::lock_guard lock{buffer_cache.mutex, std::adopt_lock};","        if (buffer_cache.IsRegionGpuModified(","                clean_area.start_address, clean_area.end_address - clean_area.start_address)) {","            // GPU::OnCPURead must not return early for buffer-only GPU writes.","            // Keep any texture-covered extent, including its sibling bytes.","            return VideoCore::RasterizerDownloadArea{","                .start_address = texture_area","                    ? (std::min)(texture_area->start_address, clean_area.start_address)","                    : clean_area.start_address,","                .end_address = texture_area","                    ? (std::max)(texture_area->end_address, clean_area.end_address)","                    : clean_area.end_address,","                .preemtive = false,","            };","        }","    }","    return texture_area.value_or(clean_area);","}","","void RasterizerVulkan::InvalidateRegion(DAddr addr, u64 size, VideoCommon::CacheType which) {"], ["    return new_area;","}","","void RasterizerVulkan::InvalidateRegion(DAddr addr, u64 size, VideoCommon::CacheType which) {"]),
        (2338, ["#ifdef PS5_NATIVE","    // One GPU VA range can cross discontiguous device-memory pages. InlineMemory,","    // texture invalidation and shader/query invalidation accept ONE CPU span:","    // their first translated DAddr must never stand in for later GMMU pages.","    // Single device-page writes keep the existing O(1) hot path. For fragmented","    // but fully mapped spans, WriteBlock invalidates EACH translated physical","    // segment before writing; it owns the same normal cache notifications.","    if (!gpu_memory->IsGranularRange(address, copy_size) &&","        !gpu_memory->IsContinuousRange(address, copy_size)) {","        if (!gpu_memory->IsFullyMappedRange(address, copy_size)) {","            return; // No partial writes into an invalid guest DMA mapping.","        }","        gpu_memory->WriteBlock(address, memory.data(), copy_size);","        return;","    }","#endif","    gpu_memory->WriteBlockUnsafe(address, memory.data(), copy_size);","    // P0.3: an unregistered page has no buffer-backed GPU dirty bytes.","    // Unknown, large and previously owned spans retain the original lock."], ["    gpu_memory->WriteBlockUnsafe(address, memory.data(), copy_size);","    // P0.3: an unregistered page has no buffer-backed GPU dirty bytes.","    // Unknown, large and previously owned spans retain the original lock."]),
    )
    for index, selected, historical in reversed(bridge_delta):
        assert m07_lines[index:index+len(selected)] == selected, ("DEV bridge edit drift", index)
        m07_lines[index:index+len(selected)] = historical
    maintained_m07_text = "\n".join(m07_lines)
assert m07_source_blob(maintained_m07_text) == "055e1cb9c53a8fa430c0027a95e098696296e5c0"
# OnCacheInvalidation has the same BufferPages block, so never use a global
# count/replace here. Only UnmapMemory disables sibling preservation because
# that mapping is being destroyed. Keep OnCacheInvalidation conservative.
unmap_marker = "void RasterizerVulkan::UnmapMemory(DAddr addr, u64 size) {"
assert expected_m07.count(unmap_marker) == 1
unmap_start = expected_m07.index(unmap_marker)
unmap_end = expected_m07.index("\nvoid RasterizerVulkan::", unmap_start + len(unmap_marker))
expected_unmap = expected_m07[unmap_start:unmap_end]
assert expected_unmap.count(bridge_unmap_before) == 1
assert bridge_unmap_after not in expected_unmap
expected_unmap = expected_unmap.replace(bridge_unmap_before, bridge_unmap_after, 1)
expected_m07 = expected_m07[:unmap_start] + expected_unmap + expected_m07[unmap_end:]
assert expected_m07.count(bridge_unmap_before) == 1
assert expected_m07.count(bridge_unmap_after) == 1
assert maintained_m07_text == expected_m07, "M07 maintained Vulkan variant parity drift"
print("ENCORE_M07_GUEST_BRIDGE_FC27_UNMAP_PARITY_PASS")
# The inactive deferred-write bridge shares the *entire* maintained rasterizer
# except its two historic DEV write-interception substitutions. Keep the F07
# present remap drain as well, ahead of the texture-cache mutex: losing this
# in the variant could silently regress the HUD if DEV were enabled later.
display_tag = "RasterizerVulkan::AccelerateDisplay("
for selection in (original_m07, maintained_m07.read_text(), expected_m07):
    assert selection.count(display_tag) == 1
    display = selection.split(display_tag, 1)[1].split(
        "return info;", 1)[0]
    assert display.count("gpu_memory->FlushCaching();") == 1
    assert display.index("gpu_memory->FlushCaching();") < display.index(
        "std::scoped_lock lock{texture_cache.mutex};")
    assert display.count("if (info.image == VK_NULL_HANDLE || info.image_view == VK_NULL_HANDLE)") == 1
    assert display.index("if (info.image == VK_NULL_HANDLE || info.image_view == VK_NULL_HANDLE)") < display.index(
        "query_cache.NotifySegment(false);")
assert 'configure_file("${EDEN_DEFERRED_VULKAN_SOURCE}"' in code
assert 'write_derived("${PORT_BUILD_DIR}/vulkan_rasterizer_deferred.cpp"' not in code
assert 'target_include_directories(video_core PRIVATE "${EDEN_PORT_DIR}")' in base
assert '"${PORT_BUILD_DIR}/vulkan_rasterizer.cpp"' in code
assert '"${PORT_BUILD_DIR}/vulkan_rasterizer_deferred.cpp"' in code
print("ENCORE_M07_MAINTAINED_VULKAN_PARITY_PASS")

# M08: DEV G20 DMA source plus two exact former bridge flush insertions.
g20_dev_dma = (root/"vendor/encore-active/eden/src/video_core/dma_pusher_dev.cpp").read_text()
m08_entry = "void DmaPusher::DispatchCalls() {"
m08_fence = "    system.GPU().OnCommandListEnd();"
assert g20_dev_dma.count(m08_entry) == g20_dev_dma.count(m08_fence) == 1
expected_m08 = g20_dev_dma.replace(
    m08_entry, m08_entry + "\n    memory_manager.FlushCaching();").replace(
    m08_fence, "    memory_manager.FlushCaching();\n" + m08_fence)
assert maintained_m08.read_text() == expected_m08, "M08 maintained DEV DMA source drift"
assert 'configure_file("${EDEN_DEFERRED_DMA_SOURCE}"' in code
assert 'write_derived("${PORT_BUILD_DIR}/dma_pusher_deferred.cpp"' not in code
assert '"${EDEN_MAINTAINED_GPU_DMA}"' in code
assert 'list(APPEND video_sources "${EDEN_MAINTAINED_GPU_DMA}" "${EDEN_MAINTAINED_GPU_PULLER}")' in base
print("ENCORE_M08_MAINTAINED_DMA_PARITY_PASS")

# M09-M11: parity oracles; no source rewriting in CMake.
original_m09 = (root/"vendor/sources/eden/src/video_core/engines/maxwell_dma.cpp").read_text()
anchor_m09 = "void MaxwellDMA::Launch() {"
assert original_m09.count(anchor_m09) == 1, "M09 original anchor drift"
expected_m09 = original_m09.replace(anchor_m09,
    anchor_m09 + "\n    memory_manager.FlushCaching();")
assert maintained_m09.read_text() == expected_m09, "M09 maintained source parity drift"
assert 'configure_file("${EDEN_DEFERRED_MAXWELL_SOURCE}"' in code
assert 'write_derived("${PORT_BUILD_DIR}/maxwell_dma_deferred.cpp"' not in code
print("ENCORE_M09_MAINTAINED_ENGINE_PARITY_PASS")

original_m10 = (root/"vendor/sources/eden/src/video_core/engines/kepler_compute.cpp").read_text()
anchor_m10 = "void KeplerCompute::ProcessLaunch() {"
assert original_m10.count(anchor_m10) == 1, "M10 original anchor drift"
expected_m10 = original_m10.replace(anchor_m10,
    anchor_m10 + "\n    memory_manager.FlushCaching();")
assert maintained_m10.read_text() == expected_m10, "M10 maintained source parity drift"
assert 'configure_file("${EDEN_DEFERRED_KEPLER_SOURCE}"' in code
assert 'write_derived("${PORT_BUILD_DIR}/kepler_compute_deferred.cpp"' not in code
print("ENCORE_M10_MAINTAINED_ENGINE_PARITY_PASS")

original_m11 = (root/"vendor/sources/eden/src/video_core/engines/engine_upload.cpp").read_text()
anchor_m11 = "void State::ProcessData(std::span<const u8> read_buffer) {"
assert original_m11.count(anchor_m11) == 1, "M11 original anchor drift"
expected_m11 = original_m11.replace(anchor_m11,
    anchor_m11 + "\n    memory_manager.FlushCaching();")
# Lichii nx2 native tiling extends SwizzleSubrect with a layout selector.
# Encore's guest bridge must retain BOTH that reviewed NS2 argument and the
# M11 cache-coherency flush; accepting either change alone would hide a
# regression in the other contract.
m11_swizzle_old = """                                       regs.dest.BlockDepth(), regs.line_length_in);"""
m11_swizzle_native = """                                       regs.dest.BlockDepth(), regs.line_length_in,
                                       memory_manager.UsesNativeTiling());"""
assert expected_m11.count(m11_swizzle_old) == 1, "M11 pinned swizzle anchor drift"
expected_m11 = expected_m11.replace(m11_swizzle_old, m11_swizzle_native)
maintained_m11_text = maintained_m11.read_text()
assert maintained_m11_text == expected_m11, "M11 maintained source parity drift"
assert maintained_m11_text.count("memory_manager.FlushCaching();") == 1
assert maintained_m11_text.count("memory_manager.UsesNativeTiling()") == 1
assert 'configure_file("${EDEN_DEFERRED_UPLOAD_SOURCE}"' in code
assert 'write_derived("${PORT_BUILD_DIR}/engine_upload_deferred.cpp"' not in code
print("ENCORE_M11_MAINTAINED_ENGINE_PARITY_PASS")

pins={
    "video_core/memory_manager.h":["    void FlushCaching();","    Core::System& system;"],
    "video_core/memory_manager.cpp":['#include "memory_manager.h"',"void MemoryManager::FlushCaching() {"],
    "video_core/engines/maxwell_dma.cpp":["void MaxwellDMA::Launch() {"],
    "video_core/engines/engine_upload.cpp":["void State::ProcessData(std::span<const u8> read_buffer) {"],
    "video_core/engines/kepler_compute.cpp":["void KeplerCompute::ProcessLaunch() {"],
    "video_core/dma_pusher.cpp":["void DmaPusher::DispatchCalls() {","    system.GPU().OnCommandListEnd();"],
}
for file, anchors in pins.items():
    text=(root/"vendor/sources/eden/src"/file).read_text()
    for needle in anchors:assert needle in text,(file,needle)
vk=(root/"vendor/encore-active/eden/src/video_core/renderer_vulkan/vulkan_rasterizer.cpp").read_text()
for needle in ("bool RasterizerVulkan::OnCPUWrite(DAddr addr, u64 size) {",
               "GuestCacheLock(buffer_cache.mutex, false)",
               "GuestCacheLock(texture_cache.mutex, true)"):
    assert needle in vk,needle
with tempfile.TemporaryDirectory(prefix="encore-bridge-config-") as d:
    subprocess.run(["cmake","-P",str(bridge)],cwd=d,check=True,
                   timeout=20,capture_output=True,text=True)
# Configure the development CMake path using dummy host targets. This
# exercises source translation without the native SDK or a console build.
with tempfile.TemporaryDirectory(prefix="encore-bridge-on-") as d:
    fake=Path(d)
    (fake/"empty.cpp").write_text("int bridge_host_stub() { return 0; }\n")
    stage=fake/"stage"
    stage.mkdir()
    # Reconstruct the real G13 native memory TU before testing M12. The
    # previous bridge fixture copied the original pinned source directly,
    # skipping the shipping backport and all G13 safeguards.
    g13_start = '    file(READ "${eden_cpu_memory_tu}" eden_cpu_memory)'
    g13_source = (root/"tools/fixtures/legacy-native-memory-g13.cmake").read_text()
    assert g13_source.count(g13_start) == 1
    assert g13_source.count('write_derived("${eden_native_memory_tu}"') == 1
    assert 'set(EDEN_NATIVE_GUEST_SOURCE "${EDEN_NATIVE_MEMORY_ROOT}/memory_native_a32.cpp")' in base
    assert 'set(EDEN_NATIVE_GUEST_SOURCE "${EDEN_NATIVE_MEMORY_ROOT}/memory_native_standard.cpp")' in base
    assert 'set_property(SOURCE "${EDEN_NATIVE_GUEST_SOURCE}" TARGET_DIRECTORY core' in base
    def generate_g13(source, output_dir, label):
        output_dir.mkdir(parents=True, exist_ok=True)
        config = """set(EDEN_PORT_DIR "__ROOT__/headless")
set(PORT_ROOT "__ROOT__")
set(PORT_BUILD_DIR "__STAGE__")
set(eden_cpu_memory_tu "__SOURCE__")
function(write_derived path content)
    file(WRITE "${path}" "${content}")
endfunction()
""" + g13_source
        config = (config.replace("__ROOT__", str(root))
                        .replace("__STAGE__", str(output_dir))
                        .replace("__SOURCE__", str(source)))
        script = fake/("g13-" + label + ".cmake")
        script.write_text(config)
        result = subprocess.run(["cmake", "-P", str(script)], cwd=fake,
                                capture_output=True, text=True, timeout=45)
        if result.returncode:
            print(result.stdout[-3000:], result.stderr[-3000:])
            raise AssertionError("G13 " + label + " materialization failed")
        generated = (output_dir/"memory-ps5.cpp").read_text()
        assert generated.count("ShouldLogUnmappedAccess()") == 11, label
        assert "thread_local Common::ScratchBuffer<u32> read_scratch;" in generated
        assert "::Eden::GpuDirty::ForEachRegion(address, size," in generated
        assert "const auto end_page = (addr + size - 1) >> YUZU_PAGEBITS;" in generated
        assert "std::numeric_limits<u64>::max() - GetInteger(base)" in generated
        return generated
    shipping = root/"vendor/encore-active/eden/src/core/memory.cpp"
    a32 = root/"vendor/encore-active/eden/src/core/memory.cpp"
    native_default = generate_g13(shipping, stage, "shipping")
    native_a32 = generate_g13(a32, fake/"g13-a32", "a32")
    assert native_default != native_a32, "G13 A32 source identity lost"
    assert "process.IsApplication() && !process.Is64Bit()" not in native_default
    assert "process.IsApplication() && !process.Is64Bit()" in native_a32

    project=r"""cmake_minimum_required(VERSION 3.24)
project(InactiveBridgeConfigure LANGUAGES CXX)
set(PS5_NATIVE ON)
set(EDEN_PS5_VULKAN ON)
set(EDEN_DEV_PROFILE ON)
set(EDEN_GUEST_WRITE_BRIDGE_DEV ON CACHE BOOL "" FORCE)
set(PORT_ROOT "__ROOT__")
set(EDEN_PORT_DIR "__ROOT__/headless")
set(PROJECT_SOURCE_DIR "__ROOT__/vendor/sources/eden")
set(PORT_BUILD_DIR "__STAGE__")
set(EDEN_MAINTAINED_GPU_DMA "__ROOT__/vendor/encore-active/eden/src/video_core/dma_pusher_dev.cpp")
add_library(video_core STATIC "@{CMAKE_CURRENT_SOURCE_DIR}/empty.cpp")
add_library(core STATIC "@{CMAKE_CURRENT_SOURCE_DIR}/empty.cpp")
set_property(TARGET core PROPERTY SOURCES "@{PORT_BUILD_DIR}/memory-ps5.cpp")
set_property(TARGET video_core PROPERTY SOURCES
    "memory_manager.cpp"
    "@{PORT_BUILD_DIR}/vulkan_rasterizer.cpp"
    "@{EDEN_MAINTAINED_GPU_DMA}"
    "engines/maxwell_dma.cpp"
    "engines/kepler_compute.cpp"
    "engines/engine_upload.cpp")
function(write_derived path content)
    file(WRITE "@{path}" "@{content}")
endfunction()
include("__BRIDGE__")
""".replace("@{",chr(36)+"{").replace("__ROOT__",str(root)).replace("__STAGE__",str(stage)).replace("__BRIDGE__",str(legacy_bridge))
    (fake/"CMakeLists.txt").write_text(project)
    result=subprocess.run(["cmake","-S",str(fake),"-B",str(fake/"build")],
                          capture_output=True,text=True,timeout=45)
    if result.returncode:
        print(result.stdout[-3500:])
        print(result.stderr[-3500:])
        raise AssertionError("native ON CMake source translation failed")
    sources={p.name:p.read_text() for p in stage.iterdir() if p.is_file()}
    for name in ("memory_manager_deferred.cpp","vulkan_rasterizer_deferred.cpp",
                 "dma_pusher_deferred.cpp","maxwell_dma_deferred.cpp",
                 "kepler_compute_deferred.cpp","engine_upload_deferred.cpp"):
        assert name in sources and len(sources[name])>200,name
    mm=sources["memory_manager_deferred.cpp"]
    assert mm == maintained_m06.read_text(), "M06 staged source differs from maintained cpp"
    assert not (stage/"dma_pusher.cpp").exists(), "M08 must not rely on a synthetic DMA source"
    assert "deferred_cpu_write_queue.Enqueue(core, address, size)" in mm
    assert "rasterizer->OnCPUWrite(address, size)" in mm
    assert "dirty[core].Collect(address, size)" in mm
    vk=sources["vulkan_rasterizer_deferred.cpp"]
    assert vk == maintained_m07.read_text(), "M07 configured Vulkan source differs from maintained variant"
    assert vk.count("EnqueueDeferredCPUWrite(addr, size)") == 1
    # DEV bridge is only staged; its historic GetFlushArea still carries a
    # typed trace object. The shipping Vulkan rasterizer has TWO callable
    # locks and is checked separately, never inferred from the DEV text.
    shipping_vk = (root/"vendor/encore-active/eden/src/video_core/renderer_vulkan/vulkan_rasterizer.cpp").read_text()
    assert shipping_vk.count("GuestCacheLock(texture_cache.mutex, true)") >= 2
    assert "GuestCacheLock(buffer_cache.mutex, false)" in shipping_vk
    assert vk.count("GuestCacheLock(texture_cache.mutex, true)") == 1
    assert vk.count("GuestCacheLock texture_wait(texture_cache.mutex, true)") == 1
    assert "texture_cache.mutex.try_lock()" not in vk
    assert "!::Eden::GpuDeferredWrite::replaying_guest_write" in vk
    assert "std::lock_guard lock{buffer_cache.mutex, std::adopt_lock};" in vk
    assert "std::lock_guard lock{texture_cache.mutex, std::adopt_lock};" in vk
    assert sources["dma_pusher_deferred.cpp"] == maintained_m08.read_text()
    assert sources["maxwell_dma_deferred.cpp"] == maintained_m09.read_text()
    assert sources["kepler_compute_deferred.cpp"] == maintained_m10.read_text()
    upload=sources["engine_upload_deferred.cpp"]
    assert upload == maintained_m11.read_text()
    h=(stage/"include/video_core/memory_manager.h").read_text()
    assert h == maintained_m04.read_text()
    assert "GpuDeferredWrite::Queue deferred_cpu_write_queue" in h
    guest=(stage/"memory-ps5-deferred.cpp").read_text()
    assert 'write_derived("' not in code
    assert 'set(bridge_cpu_source "${EDEN_NATIVE_GUEST_SOURCE}")' in code
    assert 'list(APPEND bridge_core_sources "${EDEN_DEFERRED_CPU_SOURCE}")' in code
    assert 'set_property(SOURCE "${EDEN_DEFERRED_CPU_SOURCE}" TARGET_DIRECTORY core' in code
    for mode, native_file, deferred_file in (
        ("standard","memory_native_standard.cpp","memory_ps5_standard.cpp"),
        ("a32","memory_native_a32.cpp","memory_ps5_a32.cpp")):
        actual_stage=fake/("actual-"+mode)
        actual_stage.mkdir()
        actual=project.replace(str(stage),str(actual_stage))
        actual=actual.replace(str(legacy_bridge),str(bridge))
        native_path=(root/"vendor/encore-active/eden/src/core"/native_file)
        deferred_path=(root/"vendor/encore-active/eden/guest-bridge"/deferred_file)
        actual=actual.replace(
            'set_property(TARGET core PROPERTY SOURCES "${PORT_BUILD_DIR}/memory-ps5.cpp")',
            'set(EDEN_A32_FASTMEM '+('ON' if mode=="a32" else 'OFF')+')\n'
            'set(EDEN_NATIVE_GUEST_SOURCE "'+str(native_path)+'")\n'
            'set_property(TARGET core PROPERTY SOURCES "${EDEN_NATIVE_GUEST_SOURCE}")')
        actual+='''
get_target_property(eden_selected_core core SOURCES)
list(FIND eden_selected_core "${EDEN_NATIVE_GUEST_SOURCE}" eden_old_idx)
list(FIND eden_selected_core "${EDEN_DEFERRED_CPU_SOURCE}" eden_new_idx)
if(NOT eden_old_idx EQUAL -1 OR eden_new_idx EQUAL -1)
    message(FATAL_ERROR "DEV memory profile selection drift")
endif()
get_source_file_property(eden_defs "${EDEN_DEFERRED_CPU_SOURCE}"
    TARGET_DIRECTORY core COMPILE_DEFINITIONS)
if(NOT eden_defs MATCHES "PS5_NATIVE=1")
    message(FATAL_ERROR "M12 DEV source lost native per-TU define")
endif()
'''
        (fake/"CMakeLists.txt").write_text(actual)
        result=subprocess.run(
            ["cmake","-S",str(fake),"-B",str(fake/("actual-build-"+mode))],
            capture_output=True,text=True,timeout=45)
        if result.returncode:
            print(result.stdout[-2500:],result.stderr[-2500:])
            raise AssertionError("M12 selected DEV profile CMake failed: "+mode)
        assert deferred_path.is_file()
    print("ENCORE_M12_REAL_SELECTOR_BOTH_PROFILES_PASS per_tu_native_define=1")
    assert guest.count("ScopedGuestWriteOrigin guest_origin") == 1
    assert guest.count("ScopedGuestStoreIntent store_intent;") == 5
    block=guest.split("bool WriteBlockImpl(",1)[1].split("bool ZeroBlock(",1)[0]
    assert block.index("ScopedGuestStoreIntent store_intent;") < block.index("HandleRasterizerWrite(")
    tracked_store=block.split("ScopedGuestStoreIntent store_intent;",1)[1]
    assert tracked_store.index("HandleRasterizerWrite(") < tracked_store.index(
        "std::memcpy(ptr, reinterpret_cast<u8 const*>(buffer) + offset, copy_amount);")
    assert tracked_store.index("std::memcpy(ptr, reinterpret_cast<u8 const*>(buffer) + offset, copy_amount);") < tracked_store.index(
        "} else {")
    assert block.count("std::memcpy(ptr, reinterpret_cast<u8 const*>(buffer) + offset, copy_amount);") == 3
    zero=guest.split("bool ZeroBlock(",1)[1].split("bool CopyBlock(",1)[0]
    assert zero.index("ScopedGuestStoreIntent store_intent;") < zero.index("HandleRasterizerWrite(")
    assert zero.index("HandleRasterizerWrite(") < zero.rindex("std::memset(ptr, 0, copy_amount);")
    scalar=guest.split("inline void Write(Common::ProcessAddress vaddr,",1)[1].split("bool WriteExclusive(",1)[0]
    assert scalar.count("ScopedGuestStoreIntent store_intent;") == 1
    assert scalar.index("ScopedGuestStoreIntent store_intent;") < scalar.index("GetPointerImpl(")
    assert scalar.index("ScopedGuestStoreIntent store_intent;") < scalar.index("std::memcpy(ptr, &data, sizeof(T));")
    exclusive=guest.split("bool WriteExclusive(Common::ProcessAddress vaddr,",1)[1].split("void HandleRasterizerDownload(",1)[0]
    assert exclusive.count("ScopedGuestStoreIntent store_intent;") == 2
    for fn in (exclusive.split("bool WriteExclusive128(",1)[0],
               exclusive.split("bool WriteExclusive128(",1)[1]):
        assert fn.index("ScopedGuestStoreIntent store_intent;") < fn.index("GetPointerImpl(")
        assert fn.index("ScopedGuestStoreIntent store_intent;") < fn.index("Common::AtomicCompareAndSwap(")
    maintenance=guest.split("Result StoreDataCache(",1)[1].split("void MarkRegionDebug(",1)[0]
    assert maintenance.count("HandleRasterizerWrite(") == 2
    assert maintenance.count("ScopedGuestCacheMaintenanceIntent maintenance_intent;") == 2
    assert "ScopedGuestStoreIntent store_intent;" not in maintenance
    assert "guest_write_intent" in vk and "guest_write_intent" in mm
    assert "system.GPU().OnCPUWrite(address, size)" in guest
    assert "GetCurrentHostThreadID()" not in mm.split("bool MemoryManager::EnqueueDeferredCPUWrite",1)[1].split("void MemoryManager::FlushCaching",1)[0]
    assert "guest_write_origin_core" in mm
    assert "guest_write_origin_core < ::Eden::GpuDeferredWrite::Queue::Cores" in vk
    # Validate M12 against BOTH real native G13 variants. The prior
    # host fixture materialized A32 but only configured the bridge for
    # shipping/default memory, so an A32-only source drift could go unseen.
    a32_stage = fake/"g13-a32"
    assert (a32_stage/"memory-ps5.cpp").read_text() == native_a32
    a32_project = project.replace(str(stage), str(a32_stage))
    assert a32_project != project and str(stage) not in a32_project
    (fake/"CMakeLists.txt").write_text(a32_project)
    result_a32 = subprocess.run(
        ["cmake", "-S", str(fake), "-B", str(fake/"build-a32")],
        capture_output=True, text=True, timeout=45)
    if result_a32.returncode:
        print(result_a32.stdout[-3500:])
        print(result_a32.stderr[-3500:])
        raise AssertionError("M12 A32 native ON CMake source translation failed")
    a32_guest = (a32_stage/"memory-ps5-deferred.cpp").read_text()
    assert a32_guest != guest, "M12 ignored selected A32 memory variant"
    a32_guard = "process.IsApplication() && !process.Is64Bit() && Settings::IsFastmemEnabled()"
    normal_guard = "process.IsApplication() && Settings::IsFastmemEnabled()"
    assert a32_guest.count(a32_guard) == 1
    assert guest.count(normal_guard) == 1
    assert a32_guest.replace(a32_guard, normal_guard) == guest, (
        "M12 A32/standard divergence beyond intended fastmem guard")
    for token in ("ScopedGuestWriteOrigin guest_origin",
                  "ScopedGuestStoreIntent store_intent;",
                  "ScopedGuestCacheMaintenanceIntent maintenance_intent;",
                  "ShouldLogUnmappedAccess()",
                  "thread_local Common::ScratchBuffer<u32> read_scratch;",
                  "std::numeric_limits<u64>::max() - GetInteger(base)"):
        assert a32_guest.count(token) == guest.count(token), (
            "M12 lost shared native contract", token)
    assert (a32_stage/"vulkan_rasterizer_deferred.cpp").read_text() == maintained_m07.read_text()
    assert (a32_stage/"dma_pusher_deferred.cpp").read_text() == maintained_m08.read_text()
    print("ENCORE_M12_BOTH_NATIVE_MEMORY_PROFILES_PASS default=1 a32=1 bridge_disabled_by_default=1")

    # Verify four full Encore sources against CMake-generated historical
    # code, including both native A32/standard memory profiles. Only absolute
    # local header prefixes are normalized for the maintained include search.
    def normalize_native_legacy(source):
        for header in ("performance.h", "gpu_dirty_region_split.h",
                       "gpu_deferred_replay.h"):
            source = source.replace(
                '#include "' + str(root/"headless"/header) + '"',
                '#include "' + header + '"')
        return source
    # Only the two selected PS5 native TUs carry the reviewed 27d087f
    # null-page-table crash guard. Reconstruct the exact historical source
    # by removing *only* that known addition, then compare all remaining bytes.
    # Guest bridge variants must remain byte-for-byte equivalent as before.
    native_span_old = (
        "        if (!size || !AddressSpaceContains(*current_page_table, addr, size)) return nullptr;"
    )
    native_span_guard = (
        "        // AudioOut can request its initial guest buffer before the process\n"
        "        // page table is installed. Never dereference a missing table: the\n"
        "        // GuestMemory fallback performs a checked ReadBlockUnsafe instead.\n"
        "        if (!size || current_page_table == nullptr ||\n"
        "            !AddressSpaceContains(*current_page_table, addr, size)) return nullptr;"
    )
    native_walk_old = "        if (!AddressSpaceContains(*current_page_table, addr, size)) {"
    native_walk_guard = (
        "        // An uninitialized process has no active guest page table.\n"
        "        // Never dereference it during early NSO/ExeFS BSS clearing.\n"
        "        // Propagate a failed walk; the loader must report an error, not SIGSEGV.\n"
        "        if (current_page_table == nullptr ||\n"
        "            !AddressSpaceContains(*current_page_table, addr, size)) {"
    )
    for owner, historic in (
        ("eden/src/core/memory_native_standard.cpp", native_default),
        ("eden/src/core/memory_native_a32.cpp", native_a32),
        ("eden/src/core/memory_native_standard_deferred.cpp", guest),
        ("eden/src/core/memory_native_a32_deferred.cpp", a32_guest)):
        maintained = (root/"vendor/encore-active"/owner).read_text()
        baseline = normalize_native_legacy(historic)
        if owner.startswith("eden/src/core/memory_native_"):
            assert baseline.count(native_walk_old) == 1, (
                "Historical native WalkBlock owner moved", owner)
            assert maintained.count(native_walk_guard) == 1, (
                "PS5 null-page-table crash guard missing or duplicated", owner)
            baseline = baseline.replace(native_walk_old, native_walk_guard)
            assert baseline.count(native_span_old) == 1, (
                "Historical native GetSpan owner moved", owner)
            assert maintained.count(native_span_guard) == 1, (
                "PS5 early audio GetSpan null-table guard missing or duplicated", owner)
            baseline = baseline.replace(native_span_old, native_span_guard)
        # The PS5 NS2 demand-zero path has three reviewed sparse guards:
        # admission before PTE publication, the native declaration, and
        # ZeroBlock's no-op-zero bypass. Reverse only their exact source
        # regions to compare against immutable G13/M12 history; retain the
        # real production checks independently.
        if owner.startswith("eden/src/core/memory_native_"):
            marker = "#if defined(PS5_NATIVE) && defined(EDEN_NS2_SPARSE_BACKING)"
            assert maintained.count(marker) == 3, ("NS2 sparse guard locations", owner)
            assert maintained.count('extern "C" bool EdenNs2EnsureGuestBackingReadable(') == 1
            assert 'EdenNs2CommitGuestBacking(' not in maintained
            call_start = marker + "\n        // PTE publication only needs readable backing."
            point = maintained.index(call_start)
            call_end = maintained.index("#endif\n", point) + len("#endif\n")
            before_map = maintained.index("        MapPages(page_table", point)
            assert call_end <= before_map, ("sparse admission after PTE", owner)
            admission = maintained[point:call_end]
            assert 'EdenNs2EnsureGuestBackingReadable(' in admission
            assert 'throw std::bad_alloc{};' in admission
            assert admission.index('EdenNs2EnsureGuestBackingReadable(') < admission.index(
                'throw std::bad_alloc{};')
            # A zero-fill of genuinely unowned NS2 backing must not promote
            # the whole 2 MiB granule. Non-direct aliases still use memset.
            zero_start = maintained.index(
                marker + "\n            // A normal guest-memory ZERO page")
            zero_end = maintained.index("#endif\n", zero_start) + len("#endif\n")
            zero_owner = maintained.index("    bool ZeroBlock(", before_map)
            zero_memset = maintained.index(
                "            std::memset(ptr, 0, copy_amount);", zero_start)
            assert zero_owner < zero_start < zero_end == zero_memset, owner
            zero_guard = maintained[zero_start:zero_end]
            for witness in (
                'either NS1 or NS2',
                'IsDirectBackingAlias(reinterpret_cast<std::uintptr_t>(ptr), copy_amount)',
                'buffer.ClearBackingRegion(',
                'return;',
            ):
                assert witness in zero_guard, ("PS5 guest zero-owner safety guard", owner, witness)
            assert 'GetIntendedMemorySize() ==' not in zero_guard, owner
            assert '(12ull << 30)' not in zero_guard, owner
            alias_start = maintained.index(
                "#ifdef PS5_NATIVE\n    // Delta-zero page pointers")
            alias_end = maintained.index("#endif\n\n", alias_start) + len("#endif\n\n")
            alias_method = maintained[alias_start:alias_end]
            for witness in (
                'IsDirectBackingAlias(u64 address, std::size_t bytes) const',
                'base != 0 && address >= base && bytes <= capacity',
                'address - base <= capacity - bytes',
            ):
                assert witness in alias_method, ("direct alias bounds guard", owner, witness)
            assert maintained.count("IsDirectBackingAlias(") == 5, owner
            decl_start = maintained.index(marker)
            decl_end = maintained.index("#endif\n", decl_start) + len("#endif\n")
            assert decl_end < alias_start < point < zero_start, owner
            reviewed = maintained[:zero_start] + maintained[zero_end:]
            # 648989 changed this one direct ZeroBlock lambda from [=] to [&]
            # only so the sparse path can reach system.DeviceMemory().
            zero_lambda = (
                "        [&](const std::size_t offset, const std::size_t copy_amount, u8* const ptr) {\n"
                "            std::memset(ptr, 0, copy_amount);"
            )
            historical_zero_lambda = (
                "        [=](const std::size_t offset, const std::size_t copy_amount, u8* const ptr) {\n"
                "            std::memset(ptr, 0, copy_amount);"
            )
            assert reviewed.count(zero_lambda) == 1, owner
            reviewed = reviewed.replace(zero_lambda, historical_zero_lambda, 1)
            reviewed = reviewed[:point] + reviewed[call_end:]
            # The direct-alias helper and its three historical call sites
            # already belong to the G13 baseline: keep them for parity.
            # Remove only the standalone NS2-gated declaration and separator.
            assert reviewed[decl_end:decl_end+1] == "\n", owner
            reviewed = reviewed[:decl_start] + reviewed[decl_end+1:]
            assert reviewed.count("#include <new>\n") == 1, owner
            maintained = reviewed.replace("#include <new>\n", "", 1)
        # C00/R457 adds exactly one reviewed, native-only readiness method
        # to BOTH selected memory backends. Reverse just this fixed addition
        # for the historical G13/M12 parity check; all older bytes remain
        # accounted for by the original source oracle.
        if owner.startswith("eden/src/core/memory_native_"):
            audio_readiness = """#ifdef PS5_NATIVE
bool Memory::ReadyForAudioRead() const noexcept {
    // Guard the same selected page-table owner as native GetSpan.
    // AudioOut will enqueue silence until the owning process has mapped memory.
    return impl && impl->current_page_table != nullptr;
}
#endif

"""
            assert maintained.count(audio_readiness) == 1, (
                "C00/R457 native audio memory readiness missing or duplicated", owner)
            maintained = maintained.replace(audio_readiness, "", 1)
        assert maintained == baseline, (
            "G13 X05 M12 historical source parity drift", owner)
    print("ENCORE_FOUR_NATIVE_GUEST_MEMORY_VARIANTS_PARITY_PASS")

    dirty_h=(stage/"deferred-core/core/gpu_dirty_memory_manager.h").read_text()
    assert dirty_h == maintained_dirty.read_text()
    assert dirty_h.count("void Collect(PAddr address, size_t size) {") == 1
    assert "void Collect(PAddr address, size_t size) {\n        std::scoped_lock lk(guard);" in dirty_h
    assert "std::scoped_lock lk(guard);\n                    back_buffer.emplace_back(tmp);" not in dirty_h
    assert '#include "core/gpu_dirty_memory_manager.h"' in mm
    # Compile the historically equivalent maintained GPU-dirty collector
    # against a minimal pinned-page-size shim under ASan and UBSan.
    stub=stage/"fixture/core"
    stub.mkdir(parents=True,exist_ok=True)
    (stub/"device_memory_manager.h").write_text(
        "#pragma once\n#include <cstddef>\n#include <cstdint>\n"
        "using PAddr = std::uint64_t;\nusing u32 = std::uint32_t;\n"
        "using u64 = std::uint64_t;\n"
        "namespace Core { inline constexpr std::size_t DEVICE_PAGEBITS = 12; }\n"
    )
    stress = r'''
#include "core/gpu_dirty_memory_manager.h"
#include <array>
#include <atomic>
#include <cassert>
#include <cstdint>
#include <functional>
#include <thread>
#include <vector>
int main() {
    static constexpr unsigned Cores=4, Writes=400;
    Core::GPUDirtyMemoryManager dirty;
    std::array<std::atomic<bool>,Cores> finished{};
    std::vector<unsigned char> seen(Cores*Writes,0);
    auto receive = [&](PAddr a, std::size_t length) {
        assert(a>=2048 && a%2048==0 && length==64);
        const auto index=a/2048-1;
        assert(index<seen.size());
        ++seen[index];
    };
    std::function<void(PAddr,std::size_t)> callback=receive;
    std::vector<std::thread> writers;
    for(unsigned core=0;core<Cores;++core) writers.emplace_back([&,core] {
        for(unsigned i=0;i<Writes;++i) {
            const auto address=std::uint64_t(core*Writes+i+1)*2048;
            dirty.Collect(address,64);
            if((i%11)==0) std::this_thread::yield();
        }
        finished[core].store(true,std::memory_order_release);
    });
    while(true) {
        dirty.Gather(callback);
        bool all=true;
        for(auto& done:finished) all &= done.load(std::memory_order_acquire);
        if(all) break;
        std::this_thread::yield();
    }
    for(auto& w:writers) w.join();
    dirty.Gather(callback);
    for(unsigned i=0;i<seen.size();++i) assert(seen[i]!=0);

    // Same-region disjoint writes must union their 64-byte dirty masks.
    Core::GPUDirtyMemoryManager blocks;
    std::vector<std::thread> union_writers;
    for(unsigned c=0;c<4;++c) union_writers.emplace_back([&,c] {
        for(unsigned j=0;j<8;++j) blocks.Collect(0x200000+c*512+j*64,64);
    });
    for(auto& w:union_writers) w.join();
    std::vector<std::pair<PAddr,std::size_t>> combined;
    std::function<void(PAddr,std::size_t)> union_callback =
        [&](PAddr a,std::size_t n){combined.emplace_back(a,n);};
    blocks.Gather(union_callback);
    assert(combined.size()==1);
    assert(combined[0].first==0x200000 && combined[0].second==2048);
}
'''
    cpp=stage/"dirty_collector_stress.cpp"
    binary=stage/"dirty_collector_stress"
    cpp.write_text(stress)
    subprocess.run(["clang++","-std=c++20","-O1","-g","-pthread",
                    "-Wall","-Wextra","-Werror","-fsanitize=address,undefined",
                    "-fno-sanitize-recover=all",
                    "-I",str(stage/"deferred-core"),"-I",str(stage/"fixture"),
                    str(cpp),"-o",str(binary)],
                   check=True,timeout=45)
    subprocess.run([str(binary)],check=True,timeout=45)
    print("DEFERRED_GPU_DIRTY_STRESS_PASS producers=4 regions=1600 live_gather=1 mask_union=32")

print("NATIVE_GUEST_WRITE_BRIDGE_SOURCE_PASS default_off=1 dev_on_translations=6 no_runtime_enable=1")
