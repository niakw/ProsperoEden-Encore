#!/usr/bin/env python3
"""P2.7: source-owner audit of live guest GPFIFO fetch against NX2 snapshots.

Eglantine fae3bc6 changes selection of *submitted GPU command words* after
GPU writes. Encore's maintained DmaPusher has a different interface: ioctl
copies guest command HEADERS only; the pusher reads the actual command words
at execution time. Prove the source-level SafeRead/FlushRegion/DownloadMemory/
scheduler.Finish chain, without treating that as a PS5 GPU completion test.
"""
from pathlib import Path
import subprocess

root = Path(__file__).resolve().parents[2]
vendor = root / "vendor"
cmake = (root / "headless/CMakeLists.txt").read_text()
assert '"${EDEN_MAINTAINED_GUEST_GPU_ROOT}/dma_pusher.cpp"' in cmake
assert '"${EDEN_MAINTAINED_GUEST_GPU_ROOT}/dma_pusher_dev.cpp"' not in cmake
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
    assert "#ifdef PS5_NATIVE" in step
    assert 'NativeGpuChannelRegistry::Instance().IsNative(&channel_state);' in step
    assert step.index('NativeGpuChannelRegistry::Instance().IsNative(&channel_state);') < step.index(
        'GpuGuestMemory<Tegra::CommandHeader,')
    assert 'target_compile_definitions(video_core PRIVATE EDEN_NS2_NATIVE_GPU_DISPATCH=1)' not in cmake
    assert 'EDEN_NS2_NATIVE_GPU_PULLER' in cmake
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
# The two ioctl owners now allocate only after validating entry counts and
# catch host OOM before guest reads or GPU fence publication. Verify both
# live methods rather than demanding their superseded throwing constructor.
base1 = nvdrv.split("NvResult nvhost_gpu::SubmitGPFIFOBase1(", 1)[1].split(
    "NvResult nvhost_gpu::SubmitGPFIFOBase2(", 1)[0]
base2 = nvdrv.split("NvResult nvhost_gpu::SubmitGPFIFOBase2(", 1)[1].split(
    "NvResult nvhost_gpu::GetWaitbase(", 1)[0]
assert nvdrv.count("Tegra::CommandList entries;") == 2
for submission in (base1, base2):
    assert submission.count("Tegra::CommandList entries;") == 1
    assert submission.count("entries.command_lists.resize(params.num_entries, boost::container::default_init);") == 1
    assert submission.count("catch (const std::bad_alloc&)") == 1
    assert "return NvResult::InsufficientMemory;" in submission
    assert submission.index("entries.command_lists.resize(") < submission.index("SubmitGPFIFOImpl(")
    assert "if (params.num_entries != 0)" in submission
    assert "params.num_entries > commands.size()" in submission
    assert "return SubmitGPFIFOImpl(params, std::move(entries), fd);" in submission
assert "params.num_entries > MaxKickoffEntries" in base1
assert "NativeGpfifoGuestHeadersReadable(" in base1
assert "session->process->GetMemory().IsValidVirtualAddressRange(" in base1
assert "this->GetSessionMemory(fd).ReadBlock(" in base1
assert nvdrv.count("entries.command_lists.data()") >= 3
# The maintained NVDRV now installs the GSV address-space revocation lease on
# EVERY published native GPU list (including increment/wait packets).
# A direct push of the original "entries" bypasses this guard and is invalid.
submit = nvdrv.split("NvResult nvhost_gpu::SubmitGPFIFOImpl(", 1)[1].split(
    "Core::Memory::Memory& nvhost_gpu::GetSessionMemory(", 1
)[0]
lambda_marker = "const auto push_gpu_entries = [&](Tegra::CommandList&& list) {"
assert lambda_marker in submit
publish = submit.split(lambda_marker, 1)[1].split("\n    };", 1)[0]
assert "if (native)" in publish
assert publish.index("list.native_submission_lease = native_submission_lease;") < publish.index(
    "gpu.PushGPUEntries(bind_id, std::move(list));"
)
assert submit.count("gpu.PushGPUEntries(") == 1, "native lists bypass the lease publisher"
assert submit.index(lambda_marker) < submit.index("push_gpu_entries(std::move(entries));")
assert "push_gpu_entries(Tegra::CommandList{BuildWaitCommandList(params.fence)});" in submit
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
cache_blob = subprocess.check_output(
    ["git", "hash-object", str(owner / "buffer_cache/buffer_cache.h")],
    text=True).strip()
if cache_blob == "469eddd0ea9e0a3498446bf08ab473caac3b76f9":
    write_marker = "device_memory.WriteBlockUnsafe(copy_device_addr, copy_mapped_memory, copy.size);"
elif cache_blob in {
    "c4ed79a1fe6aec09da8040b7af3901f6184f910b",
    "09e1578dec6dcbcb0b8f54d4bb819b71d0eed972",
    "505ee80a37d5991b7925019282e71926c1648e02",
    "c6bab56cbd4e58458d010e423d74df9f933a8f8d",  # vendor #189: reviewed pinned RangeSet native ABI adaptation
    "6bbbae48f3c45fa5fd68d82940f5c5c508cbfd7b", "6aa9754506ee82b4d25a4e36d4f3be646a62456b", "7f07e392ea0cc828d862da29d32ada1ebc3966aa", "4ce33d21debc33c9625129cbd545bf9b1c084272", "fce19742529b21bca0f92f3f67c4e420dcd493c7",  # NS1 FC27: page-wide ownership sampled before CPU write; GPU siblings retained; all-channel binding scrub
}:
    write_marker = "WriteDownloadedMemory(cpu_written, copy_device_addr, copy_mapped_memory, copy.size);"
    assert "void BufferCache<P>::WriteDownloadedMemory" in buffer_cache
    assert "device_memory.WriteBlockUnsafe(start, data + (start - device_addr), end - start);" in buffer_cache
    if cache_blob in {"09e1578dec6dcbcb0b8f54d4bb819b71d0eed972",
                       "505ee80a37d5991b7925019282e71926c1648e02", "c6bab56cbd4e58458d010e423d74df9f933a8f8d", "6bbbae48f3c45fa5fd68d82940f5c5c508cbfd7b", "6aa9754506ee82b4d25a4e36d4f3be646a62456b", "7f07e392ea0cc828d862da29d32ada1ebc3966aa", "4ce33d21debc33c9625129cbd545bf9b1c084272", "fce19742529b21bca0f92f3f67c4e420dcd493c7"}:
        assert "Upstream Lichii/Eglantine b13c4c1" in buffer_cache
        assert "keep_page_gpu_data" in buffer_cache
    if cache_blob == "505ee80a37d5991b7925019282e71926c1648e02":
        assert "Lichii 44bf47d" in buffer_cache
        assert "!gpu_modified_ranges.Intersects(page_begin, page_end - page_begin)" in buffer_cache
    if cache_blob in {"c6bab56cbd4e58458d010e423d74df9f933a8f8d", "6bbbae48f3c45fa5fd68d82940f5c5c508cbfd7b", "6aa9754506ee82b4d25a4e36d4f3be646a62456b"}:
        assert "Lichii 44bf47d" in buffer_cache
        assert "gpu_modified_ranges.Intersects(" not in buffer_cache
        if cache_blob == "c6bab56cbd4e58458d010e423d74df9f933a8f8d":
            assert "!IsRegionGpuModified(page_begin, page_end - page_begin)" in buffer_cache
        if cache_blob in {"6bbbae48f3c45fa5fd68d82940f5c5c508cbfd7b", "6aa9754506ee82b4d25a4e36d4f3be646a62456b"}:
            # Source commit e81e4017 samples the page before subtracting the CPU
            # span; it must still download GPU-owned sibling bytes afterward.
            assert "const bool page_has_gpu_writes = keep_page_gpu_data &&" in buffer_cache
            assert "const bool overlaps_cpu_write = IsRegionGpuModified(device_addr, size);" in buffer_cache
            assert "if (page_has_gpu_writes &&" in buffer_cache
            assert "(!overlaps_cpu_write || IsRegionGpuModified(page_begin, page_end - page_begin))" in buffer_cache
            assert buffer_cache.index("gpu_modified_ranges.Subtract(device_addr, size);") < buffer_cache.index(
                "if (page_has_gpu_writes &&")
        region = buffer_cache.split("bool BufferCache<P>::IsRegionGpuModified(DAddr addr, size_t size)", 1)[1].split("\n}",1)[0]
        assert "gpu_modified_ranges.ForEachInRange(addr, size," in region
else:
    raise AssertionError(("Unreviewed live-fetch BufferCache owner", cache_blob))
assert download.index("runtime.CopyBuffer(") < download.index("runtime.Finish();") < download.index(write_marker)
runtime = (vendor / "encore-active/eden-vulkan/vk_buffer_cache_cost.cpp").read_text()
assert "void BufferCacheRuntime::Finish() {" in runtime
assert "scheduler.Finish();" in runtime.split("void BufferCacheRuntime::Finish() {", 1)[1].split("}", 1)[0]
assert (root / "tools/ns2/test_native_gpu_command_saferead.cpp").is_file()
print("P2_7_NATIVE_GPU_COMMAND_FETCH_OWNER_PASS real_dma=2"
      " guest_words=live_fetch synthetic_prefetch=fences_only"
      " upstream_submitted_snapshot=inapplicable"
      " gpu_write_readback=SOURCE_CHAIN_PRESENT hardware_completion=P5")
