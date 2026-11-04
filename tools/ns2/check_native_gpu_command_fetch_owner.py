#!/usr/bin/env python3
"""P2.7: source-owner audit of live guest GPFIFO fetch against NX2 snapshots.

Eglantine fae3bc6 changes selection of *submitted GPU command words* after
GPU writes. Encore's maintained DmaPusher has a different interface: ioctl
copies guest command HEADERS only; the pusher reads the actual command words
at execution time. Prove the source-level SafeRead/FlushRegion/DownloadMemory/
scheduler.Finish chain, without treating that as a PS5 GPU completion test.
"""
from pathlib import Path

root = Path(__file__).resolve().parents[2]
vendor = root / "vendor"
cmake = (root / "headless/CMakeLists.txt").read_text()
assert '"${EDEN_MAINTAINED_GUEST_GPU_ROOT}/dma_pusher.cpp"' in cmake
assert '"${EDEN_MAINTAINED_GUEST_GPU_ROOT}/dma_pusher_dev.cpp"' in cmake
assert '"${EDEN_MAINTAINED_GPU_DMA}"' in cmake
owner = vendor / "encore-active/eden-core/src/video_core"
for file in ("dma_pusher.cpp", "dma_pusher_dev.cpp"):
    source = (owner / file).read_text()
    step = source.split("bool DmaPusher::Step() {", 1)[1].split(
        "void DmaPusher::ProcessCommands(", 1
    )[0]
    assert "CommandList& command_list = dma_pushbuffer.front();" in step
    assert "ProcessCommands(command_list.prefetch_command_list);" in step
    assert "command_list.command_lists[dma_pushbuffer_subindex]" in step
    # Eglantine's submission-time user-GPU-word cache is NOT in this
    # maintained owner; do not port its snapshot-selection patch blindly.
    assert "submitted_words" not in step and "submitted_offsets" not in step
    assert "GpuGuestMemory<Tegra::CommandHeader," in step
    assert "GuestMemoryFlags::SafeRead" in step
    assert "GuestMemoryFlags::UnsafeRead" in step
    assert "#ifdef EDEN_NS2_NATIVE_GPU_DISPATCH" in step
    assert 'NativeGpuChannelRegistry::Instance().IsNative(&channel_state);' in step
    assert step.index('NativeGpuChannelRegistry::Instance().IsNative(&channel_state);') < step.index(
        'GpuGuestMemory<Tegra::CommandHeader,')
    assert 'target_compile_definitions(video_core PRIVATE EDEN_NS2_NATIVE_GPU_DISPATCH=1)' in cmake
    assert (root / "tools/ns2/check_native_gpu_fence_policy_host.py").is_file()
    assert 'const bool use_safe =' not in step
    assert 'const bool explicit_sync = command_list.command_lists[dma_pushbuffer_subindex].sync;' in step
    assert 'signal_sync = explicit_sync &&' in step
    assert 'signal_sync = explicit_sync && user_sync;' in step
    assert step.index('signal_sync = explicit_sync &&') < step.index('rasterizer->SignalFence(')
    assert step.index("dma_state.dma_get = header.addr;") < step.index(
        "GpuGuestMemory<Tegra::CommandHeader,"
    ) < step.index("ProcessCommands(headers);")
nvdrv = (vendor / (
    "encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/"
    "devices/nvhost_gpu.cpp"
)).read_text()
assert nvdrv.count("Tegra::CommandList entries(params.num_entries);") == 2
assert nvdrv.count("entries.command_lists.data()") >= 3
assert "gpu.PushGPUEntries(bind_id, std::move(entries));" in nvdrv
for helper in (
    "BuildWaitCommandList(params.fence)",
    "BuildIncrementCommandList(params.fence)",
    "BuildIncrementWithWfiCommandList(params.fence)",
):
    assert helper in nvdrv
assert "submitted_words" not in nvdrv
assert "submitted_offsets" not in nvdrv

# The real source chain is stronger than the older snapshot-only audit:
# 1. A native NS2 channel always selects SafeRead for the live command span.
# 2. Both direct and physically-disjoint reads flush guest GPU pages first.
# 3. The maintained Vulkan buffer cache finishes pending GPU work BEFORE
#    publishing downloaded bytes to the CPU backing used by ProcessCommands.
# Unsupported/unmapped ranges still follow the existing zero-read contract.
guest = (vendor / "sources/eden/src/core/guest_memory.h").read_text()
assert "m_memory->FlushRegion(m_addr, this->size_bytes());" in guest
assert "m_memory->ReadBlock(m_addr, this->data(), this->size_bytes());" in guest
memory = (owner / "memory_manager.cpp").read_text()
read = memory.split("void MemoryManager::ReadBlockImpl(", 1)[1].split(
    "void MemoryManager::ReadBlock(", 1)[0]
assert read.count("rasterizer->FlushRegion(dev_addr_base, copy_amount, which);") == 2
assert "memory.ReadBlockUnsafe(dev_addr_base, dest_buffer, copy_amount);" in read
assert "std::memset(dest_buffer, 0, size);" in read
for rasterizer in ("eden-vulkan/vulkan_rasterizer.cpp",
                   "eden-core/guest-bridge/vulkan_rasterizer.cpp"):
    source = (vendor / "encore-active" / rasterizer).read_text()
    flush = source.split("void RasterizerVulkan::FlushRegion(", 1)[1].split(
        "bool RasterizerVulkan::MustFlushRegion(", 1)[0]
    assert "texture_cache.DownloadMemory(addr, size);" in flush
    assert "buffer_cache.DownloadMemory(addr, size);" in flush
buffer_cache = (owner / "buffer_cache/buffer_cache.h").read_text()
download = buffer_cache.split("void BufferCache<P>::DownloadBufferMemory(Buffer& buffer, DAddr", 1)[1].split(
    "void BufferCache<P>::DeleteBuffer(", 1)[0]
assert "runtime.CopyBuffer(download_staging.buffer, buffer, copies_span, true);" in download
assert download.index("runtime.CopyBuffer(") < download.index("runtime.Finish();") < download.index(
    "device_memory.WriteBlockUnsafe(copy_device_addr, copy_mapped_memory, copy.size);")
runtime = (vendor / "encore-active/eden-vulkan/vk_buffer_cache_cost.cpp").read_text()
assert "void BufferCacheRuntime::Finish() {" in runtime
assert "scheduler.Finish();" in runtime.split("void BufferCacheRuntime::Finish() {", 1)[1].split("}", 1)[0]
assert (root / "tools/ns2/test_native_gpu_command_saferead.cpp").is_file()
print("P2_7_NATIVE_GPU_COMMAND_FETCH_OWNER_PASS real_dma=2"
      " guest_words=live_fetch synthetic_prefetch=fences_only"
      " upstream_submitted_snapshot=inapplicable"
      " gpu_write_readback=SOURCE_CHAIN_PRESENT hardware_completion=P5")
