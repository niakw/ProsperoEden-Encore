#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""SHA-pinned R2 rollback for comparing the shipping buffer cache to R437.

The five reviewed R2 insertions remain active in the production header.
Only the verifier reverses them; no runtime code is changed or bypassed.
"""
from pathlib import Path
import subprocess
import hashlib

_PRODUCTION_BUFFER_BLOB = "469eddd0ea9e0a3498446bf08ab473caac3b76f9"
_FC27_BUFFER_BLOB = "c4ed79a1fe6aec09da8040b7af3901f6184f910b"
_FC27_SIBLING_BUFFER_BLOB = "09e1578dec6dcbcb0b8f54d4bb819b71d0eed972"
_FC27_FAST_WRITE_BUFFER_BLOB = "505ee80a37d5991b7925019282e71926c1648e02"
_PS5_RANGE_API_BUFFER_BLOB = "c6bab56cbd4e58458d010e423d74df9f933a8f8d"
# Reviewed post-range-ABI production deltas: preservation of GPU-owned
# sibling bytes and page-aware DMA copy/clear. The reverse applies ONLY to
# the audit text, not the native PS5 source. Diff against the exact pinned
# predecessor and retain all nine source changes as a closed contract.
_NOV20_BUFFER_BLOB = "d40082a0c849790d25a4d1d28e003087eefd84a1"
nov20_buffer_reversal = [
    ("    // single-query clean CPU-write fast path and b13c4c1 sibling preservation.\n    // Only one page-wide GPU-ownership query is needed before the write.\n    // Keep its result for GPU-written sibling bytes: a second page query is\n    // necessary only after we actually removed an overlapping GPU-owned span.\n    const bool page_has_gpu_writes = keep_page_gpu_data && page_end > page_begin &&\n                                     IsRegionGpuModified(page_begin, page_end - page_begin);\n    if (keep_page_gpu_data && !page_has_gpu_writes) {", "    // single-query clean CPU-write fast path and b13c4c1 sibling preservation.\n    if (keep_page_gpu_data && page_end > page_begin &&\n        !IsRegionGpuModified(page_begin, page_end - page_begin)) {"),
    ("\n    const bool overlaps_cpu_write = IsRegionGpuModified(device_addr, size);\n    if (overlaps_cpu_write) {", "\n    if (IsRegionGpuModified(device_addr, size)) {"),
    ("    // upload can overwrite correct host-buffer data with the stale guest copy.\n    if (page_has_gpu_writes &&\n        (!overlaps_cpu_write || IsRegionGpuModified(page_begin, page_end - page_begin))) {", "    // upload can overwrite correct host-buffer data with the stale guest copy.\n    if (keep_page_gpu_data && page_end > page_begin &&\n        IsRegionGpuModified(page_begin, page_end - page_begin)) {"),
    ("template <class P>\nbool BufferCache<P>::DMACopy(GPUVAddr src_address, GPUVAddr dest_address, u64 amount,\n                             bool* gpu_written) {", "template <class P>\nbool BufferCache<P>::DMACopy(GPUVAddr src_address, GPUVAddr dest_address, u64 amount) {"),
    ("    }\n    // Both buffers are subsequently addressed as single CPU intervals.\n    // Sparse or aliased GMMU pages can map adjacent GPU addresses to\n    // disjoint physical memory: their DMA must use MaxwellDMA's page-aware\n    // guest-memory fallback instead of this contiguous Vulkan copy.\n    // The cheap one-page case avoids a full PTE walk in the common path.\n    const bool source_contiguous =\n        gpu_memory->IsGranularRange(src_address, amount) ||\n        gpu_memory->IsContinuousRange(src_address, amount);\n    const bool dest_contiguous =\n        gpu_memory->IsGranularRange(dest_address, amount) ||\n        gpu_memory->IsContinuousRange(dest_address, amount);\n    if (!source_contiguous || !dest_contiguous) {\n        return false;\n    }", "    }"),
    ("    const bool has_new_downloads = tmp_intervals.size() != 0;\n    if (gpu_written) {\n        *gpu_written = has_new_downloads;\n    }", "    const bool has_new_downloads = tmp_intervals.size() != 0;"),
    ("bool BufferCache<P>::DMAClear(GPUVAddr dst_address, u64 amount, u32 value) {", "bool BufferCache<P>::DMAClear(GPUVAddr dst_address, u64 amount, u32 value) {\n    const std::optional<DAddr> cpu_dst_address = gpu_memory->GpuToCpuAddress(dst_address);\n    if (!cpu_dst_address) {\n        return false;\n    }"),
    ("    const size_t size = amount * sizeof(u32);\n    // As with DMACopy, a GPU-virtual clear cannot be represented by one\n    // physically contiguous cached buffer across noncontiguous guest pages.\n    // MaxwellDMA always writes the CPU guest bytes after this acceleration.\n    if (!gpu_memory->IsGranularRange(dst_address, size) &&\n        !gpu_memory->IsContinuousRange(dst_address, size)) {\n        return false;\n    }\n    const std::optional<DAddr> cpu_dst_address = gpu_memory->GpuToCpuAddress(dst_address);\n    if (!cpu_dst_address) {\n        return false;\n    }", "    const size_t size = amount * sizeof(u32);"),
    ("    Buffer& dest_buffer = slot_buffers[buffer];\n    // Lichii maintained DMAClear: land any pending CPU data before a\n    // partial GPU fill, so its neighbouring bytes survive the next read.\n    SynchronizeBuffer(dest_buffer, *cpu_dst_address, static_cast<u32>(size));", "    Buffer& dest_buffer = slot_buffers[buffer];"),
]

# Vendor #189 ported the reviewed Lichii 44bf47d clean-write guard to
# Encore's pinned RangeSet API. Restore its exact predecessor ONLY in the
# historical verifier; the compiled vendor owner is never rewritten.
ps5_range_api_reversal = [
    (
        """    // Lichii 44bf47d: the written range is wholly inside these pages. If the
    // pages contain no GPU-written bytes, the exact range cannot contain any
    // either. Use the maintained IsRegionGpuModified/ForEachInRange API:
    // this pinned RangeSet has no upstream Intersects member. Keep the
    // single-query clean CPU-write fast path and b13c4c1 sibling preservation.""",
        """    // Lichii 44bf47d: the written range is wholly inside these pages. If the
    // pages contain no GPU-written bytes, the exact range cannot contain any
    // either, so avoid a second interval-tree walk on the overwhelmingly
    // common clean CPU-write path. This preserves b13c4c1 semantics.""",
    ),
    (
        "!IsRegionGpuModified(page_begin, page_end - page_begin)",
        "!gpu_modified_ranges.Intersects(page_begin, page_end - page_begin)",
    ),
]
fc27_fast_write_reversal = [
    ("const DAddr page_begin = Common::AlignDown(device_addr, DEVICE_PAGESIZE);\n    const DAddr page_end = Common::AlignUp(device_addr + size, DEVICE_PAGESIZE);\n\n    // Lichii 44bf47d: the written range is wholly inside these pages. If the\n    // pages contain no GPU-written bytes, the exact range cannot contain any\n    // either, so avoid a second interval-tree walk on the overwhelmingly\n    // common clean CPU-write path. This preserves b13c4c1 semantics.\n    if (keep_page_gpu_data && page_end > page_begin &&\n        !gpu_modified_ranges.Intersects(page_begin, page_end - page_begin)) {\n        memory_tracker.MarkRegionAsCpuModified(device_addr, size);\n        return;\n    }\n\n    if (IsRegionGpuModified(device_addr, size)) {\n        ClearDownload(device_addr, size);\n        gpu_modified_ranges.Subtract(device_addr, size);\n    }\n\n    // Upstream Lichii/Eglantine b13c4c1: the memory tracker owns whole pages.\n    // A small CPU write therefore clears the tracker's GPU state for its page,\n    // even when other bytes on that page are still newer on the GPU. Preserve\n    // those sibling bytes before the page becomes CPU-owned, otherwise a later\n    // upload can overwrite correct host-buffer data with the stale guest copy.", "if (IsRegionGpuModified(device_addr, size)) {\n        ClearDownload(device_addr, size);\n        gpu_modified_ranges.Subtract(device_addr, size);\n    }\n\n    // Upstream Lichii/Eglantine b13c4c1: the memory tracker owns whole pages.\n    // A small CPU write therefore clears the tracker's GPU state for its page,\n    // even when other bytes on that page are still newer on the GPU. Preserve\n    // those sibling bytes before the page becomes CPU-owned, otherwise a later\n    // upload can overwrite correct host-buffer data with the stale guest copy.\n    const DAddr page_begin = Common::AlignDown(device_addr, DEVICE_PAGESIZE);\n    const DAddr page_end = Common::AlignUp(device_addr + size, DEVICE_PAGESIZE);"),
]
fc27_sibling_page_reversal = [
    (
        "void BufferCache<P>::WriteMemory(DAddr device_addr, u64 size, bool keep_page_gpu_data) {",
        "void BufferCache<P>::WriteMemory(DAddr device_addr, u64 size) {",
    ),
    (
        """
    // Upstream Lichii/Eglantine b13c4c1: the memory tracker owns whole pages.
    // A small CPU write therefore clears the tracker's GPU state for its page,
    // even when other bytes on that page are still newer on the GPU. Preserve
    // those sibling bytes before the page becomes CPU-owned, otherwise a later
    // upload can overwrite correct host-buffer data with the stale guest copy.
    const DAddr page_begin = Common::AlignDown(device_addr, DEVICE_PAGESIZE);
    const DAddr page_end = Common::AlignUp(device_addr + size, DEVICE_PAGESIZE);
    if (keep_page_gpu_data && page_end > page_begin &&
        IsRegionGpuModified(page_begin, page_end - page_begin)) {
        DownloadMemory(page_begin, page_end - page_begin);
    }

""",
        "",
    ),
]

fc27_cpu_write_reversal = [
    ("""template <class P>
void BufferCache<P>::ClaimCpuWrites(std::span<const std::pair<DAddr, u64>> ranges) {
    for (const auto& [device_addr, size] : ranges) {
        if (IsRegionGpuModified(device_addr, size)) {
            ClearDownload(device_addr, size);
            gpu_modified_ranges.Subtract(device_addr, size);
        }
    }
}

template <class P>
Common::RangeSet<DAddr> BufferCache<P>::PendingCpuWriteRanges() {
    Common::RangeSet<DAddr> ranges;
    if (pending_cpu_writes) {
        pending_cpu_writes([&ranges](DAddr address, size_t size) {
            ranges.Add(address, size);
        });
    }
    return ranges;
}

template <class P>
void BufferCache<P>::WriteDownloadedMemory(const Common::RangeSet<DAddr>& cpu_written,
                                           DAddr device_addr, const u8* data, u64 size) {
    Common::RangeSet<DAddr> writable;
    writable.Add(device_addr, size);
    cpu_written.ForEachInRange(device_addr, size, [&writable](DAddr start, DAddr end) {
        writable.Subtract(start, end - start);
    });
    writable.ForEach([&](DAddr start, DAddr end) {
        device_memory.WriteBlockUnsafe(start, data + (start - device_addr), end - start);
    });
}

template <class P>""", "template <class P>"),
    ("""    // The fencing thread may land an older GPU snapshot while the guest CPU
    // has already produced newer bytes. Preserve every pending CPU range.
    const Common::RangeSet<DAddr> cpu_written = PendingCpuWriteRanges();
""", ""),
    ("""            WriteDownloadedMemory(cpu_written, start,
                                  &read_mapped_memory[start - device_addr], end - start);""",
     """            device_memory.WriteBlockUnsafe(start, &read_mapped_memory[start - device_addr],
                                           end - start);"""),
    ("    const Common::RangeSet<DAddr> cpu_written = PendingCpuWriteRanges();\n", ""),
    ("            WriteDownloadedMemory(cpu_written, copy_device_addr, copy_mapped_memory, copy.size);",
     "            device_memory.WriteBlockUnsafe(copy_device_addr, copy_mapped_memory, copy.size);"),
    ("            WriteDownloadedMemory(cpu_written, copy_device_addr, immediate_buffer.data(), copy.size);",
     "            device_memory.WriteBlockUnsafe(copy_device_addr, immediate_buffer.data(), copy.size);"),
]
r437_r2_reversal = [
    ("#pragma once\n\n#include <algorithm>\n#if defined(PS5_NATIVE) && defined(EDEN_NS2_STAGE_BACKING)\n#include <exception>\n#endif\n#include <memory>\n#include <numeric>\n", "#pragma once\n\n#include <algorithm>\n#include <memory>\n#include <numeric>\n"),
    ("}\n\ntemplate <class P>\nBufferCache<P>::~BufferCache() {\n#if defined(PS5_NATIVE) && defined(EDEN_NS2_STAGE_BACKING)\n    if constexpr (!P::IS_OPENGL) {\n        // The deleted-buffer retirement queue only owns explicitly deleted\n        // buffers. Resident slot buffers (and the older frame-age ring) are\n        // still members destroyed immediately after this destructor body.\n        // Drain the real GPU before those Vulkan allocations are released.\n        // A failed GPU submit/device loss must never continue destructing\n        // potentially in-flight VkBuffers: fail closed at process shutdown.\n        try {\n            runtime.Finish();\n        } catch (...) {\n            std::terminate();\n        }\n    }\n#endif\n}\n\ntemplate <class P>\nvoid BufferCache<P>::RunGarbageCollector() {", "}\n\ntemplate <class P>\nBufferCache<P>::~BufferCache() = default;\n\ntemplate <class P>\nvoid BufferCache<P>::RunGarbageCollector() {"),
    ("            copy.src_offset += upload_staging.offset;\n        }\n        const bool can_reorder = runtime.CanReorderUpload(buffer, copies);\n#if defined(PS5_NATIVE) && defined(EDEN_NS2_STAGE_BACKING)\n        if constexpr (!P::IS_OPENGL) {\n            runtime.CopyStagingUpload(buffer, upload_staging, copies, true, can_reorder);\n        } else {\n            runtime.CopyBuffer(buffer, upload_staging.buffer, copies, true, can_reorder);\n        }\n#else\n        runtime.CopyBuffer(buffer, upload_staging.buffer, copies, true, can_reorder);\n#endif\n    }\n}\n", "            copy.src_offset += upload_staging.offset;\n        }\n        const bool can_reorder = runtime.CanReorderUpload(buffer, copies);\n        runtime.CopyBuffer(buffer, upload_staging.buffer, copies, true, can_reorder);\n    }\n}\n"),
    ("        u8* const src_pointer = upload_staging.mapped_span.data();\n        std::memcpy(src_pointer, inlined_buffer.data(), copy_size);\n        const bool can_reorder = runtime.CanReorderUpload(buffer, copies);\n#if defined(PS5_NATIVE) && defined(EDEN_NS2_STAGE_BACKING)\n        if constexpr (!P::IS_OPENGL) {\n            runtime.CopyStagingUpload(buffer, upload_staging, copies, true, can_reorder);\n        } else {\n            runtime.CopyBuffer(buffer, upload_staging.buffer, copies, true, can_reorder);\n        }\n#else\n        runtime.CopyBuffer(buffer, upload_staging.buffer, copies, true, can_reorder);\n#endif\n    } else {\n        buffer.ImmediateUpload(buffer.Offset(dest_address), inlined_buffer.first(copy_size));\n    }", "        u8* const src_pointer = upload_staging.mapped_span.data();\n        std::memcpy(src_pointer, inlined_buffer.data(), copy_size);\n        const bool can_reorder = runtime.CanReorderUpload(buffer, copies);\n        runtime.CopyBuffer(buffer, upload_staging.buffer, copies, true, can_reorder);\n    } else {\n        buffer.ImmediateUpload(buffer.Offset(dest_address), inlined_buffer.first(copy_size));\n    }"),
    ("    Unregister(buffer_id);\n\n#ifdef YUZU_LEGACY\n    if (!do_not_mark || !immediately_free) {\n#endif\n#if defined(PS5_NATIVE) && defined(EDEN_NS2_STAGE_BACKING)\n        // R2 only: do not reclaim a deleted Vulkan owner by frame age.\n        // The runtime owns the moved Buffer until real GPU completion.\n        if constexpr (!P::IS_OPENGL) {\n            runtime.RetainDeletedBuffer(slot_buffers[buffer_id]);\n        } else {\n            delayed_destruction_ring.Push(std::move(slot_buffers[buffer_id]));\n        }\n#else\n        delayed_destruction_ring.Push(std::move(slot_buffers[buffer_id]));\n#endif\n#ifdef YUZU_LEGACY\n    }\n#endif\n\n    slot_buffers.erase(buffer_id);\n", "    Unregister(buffer_id);\n\n#ifdef YUZU_LEGACY\n    if (!do_not_mark || !immediately_free)\n#endif\n        delayed_destruction_ring.Push(std::move(slot_buffers[buffer_id]));\n\n    slot_buffers.erase(buffer_id);\n"),
]

# Integrated NS1/NS2 native successor: reverse only the reviewed DMA
# destination/alias and stream-boundary additions on this historical audit copy.
_INTEGRATED_BUFFER_BLOB = "6bbbae48f3c45fa5fd68d82940f5c5c508cbfd7b"
_integrated_buffer_reversal = [
    ("bool BufferCache<P>::DMACopy(\n    GPUVAddr src_address, GPUVAddr dest_address, u64 amount, bool* gpu_written,\n    boost::container::small_vector<std::pair<DAddr, size_t>, 4>* gpu_written_dest) {\n    if (gpu_written_dest) {\n        gpu_written_dest->clear();\n    }\n", "bool BufferCache<P>::DMACopy(GPUVAddr src_address, GPUVAddr dest_address, u64 amount,\n                             bool* gpu_written) {\n"),
    ("    // vkCmdCopyBuffer forbids overlapping source and destination DEVICE\n    // memory (VUID-vkCmdCopyBuffer-pRegions-00117). Distinct GMMU virtual\n    // addresses can alias one physical allocation, and different VkBuffer\n    // handles do not make those overlapping memory accesses legal.\n    // Reject BEFORE dirty-range bookkeeping, ClearDownload, or GPU commands:\n    // MaxwellDMA will read the authoritative source and snapshot the alias.\n    // Compare distances rather than forming a potentially overflowing end.\n    const DAddr source = *cpu_src_address;\n    const DAddr destination = *cpu_dest_address;\n    if ((source <= destination && destination - source < amount) ||\n        (destination < source && source - destination < amount)) {\n        return false;\n    }\n", ""),
    ("    if (gpu_written_dest) {\n        *gpu_written_dest = tmp_intervals;\n    }\n", ""),
    ("        // A stream near the start of physical memory may begin before\n        // min_page. Subtraction in the original test then wraps around and\n        // turns an ordinary backward leap into a huge invalid GPU buffer.\n        // Never move begin forwards past the range we already own.\n        if (begin <= min_page || add_value > begin - min_page) {\n            begin = (std::min)(begin, min_page);\n", "        if (add_value > begin - min_page) {\n            begin = min_page;\n"),
]

def restore_r437_without_production_r2(path: Path) -> str:
    actual = subprocess.check_output(
        ["git", "hash-object", str(path)], text=True).strip()
    source = path.read_text()
    restore_current_overlap_guard = False
    if actual == "6aa9754506ee82b4d25a4e36d4f3be646a62456b":
        # One bounded clean CPU-write fast-path change; normalize on this
        # historical audit copy before replaying the existing GPU-50 proof.
        successor = "    if (!IsRegionGpuModified(aligned_start, aligned_end - aligned_start)) {\n        // WriteMemory's clean-page branch does exactly this mark. Re-entering\n        // it would scan the same GPU-modified ranges again under the buffer\n        // cache mutex, even though this full-page query already proved that\n        // no GPU-owned sibling bytes need a download.\n        memory_tracker.MarkRegionAsCpuModified(device_addr, size);\n        return;\n    }"
        predecessor = "    if (!IsRegionGpuModified(aligned_start, aligned_end - aligned_start)) {\n        WriteMemory(device_addr, size);\n        return;\n    }"
        assert source.count(successor) == 1, "Unexpected clean-page BufferCache delta"
        source = source.replace(successor, predecessor, 1)
        raw = source.encode("utf-8")
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        assert actual == _INTEGRATED_BUFFER_BLOB, ("Clean-page predecessor drift", actual)
    if actual == _INTEGRATED_BUFFER_BLOB:
        restore_current_overlap_guard = True
        assert len(_integrated_buffer_reversal) == 4
        for revised, historical in _integrated_buffer_reversal:
            assert source.count(revised) == 1, "Integrated native BufferCache hunk drift"
            source = source.replace(revised, historical, 1)
        raw = source.encode("utf-8")
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        assert actual == "41239f19b9e16741d49e31145c504e0086b1095e", (
            "Integrated BufferCache failed exact FC27 predecessor replay")
    # FC27 P1: reverse ONLY reviewed PS5 budget sampling / typed CPU write
    # declarations on the audit copy. Do not alter shipping C++ or defer
    # GPU-page protection. Exact two-sided blob identity is mandatory.
    if actual == "41239f19b9e16741d49e31145c504e0086b1095e":
        reviewed_p1 = [["\n\ntemplate <class P>\n#ifdef PS5_NATIVE\nvoid BufferCache<P>::TickFrame(std::optional<u64> externally_sampled_usage) {\n#else\nvoid BufferCache<P>::TickFrame() {\n#endif","\ntemplate <class P>\nvoid BufferCache<P>::TickFrame() {"],["            // The native Vulkan caller already sampled outside the cache\n            // mutex. Other backends and changed frame conditions retain the\n            // original in-lock fallback, so eviction thresholds stay exact.\n            if (externally_sampled_usage) {\n                total_used_memory = *externally_sampled_usage;\n            } else {\n                total_used_memory = runtime.GetDeviceMemoryUsage();\n            }","            total_used_memory = runtime.GetDeviceMemoryUsage();"],["template <class P>\ntemplate <typename RangeSize>\nvoid BufferCache<P>::ClaimCpuWrites(std::span<const std::pair<DAddr, RangeSize>> ranges) {","template <class P>\nvoid BufferCache<P>::ClaimCpuWrites(std::span<const std::pair<DAddr, u64>> ranges) {"]]
        assert len(reviewed_p1) == 3
        for revised, historical in reviewed_p1:
            assert source.count(revised) == 1, "FC27 P1 native BufferCache source hunk drift"
            source = source.replace(revised, historical, 1)
        data = source.encode("utf-8")
        actual = hashlib.sha1(b"blob " + str(len(data)).encode() + bytes([0]) + data).hexdigest()
        assert actual == _NOV20_BUFFER_BLOB, "FC27 P1 BufferCache exact predecessor drift"
    if actual == _NOV20_BUFFER_BLOB:
        # Restore the complete previous R2+FC27 RangeSet owner byte-for-byte.
        # Reverse in source order from the end, preserving adjacent anchors.
        assert len(nov20_buffer_reversal) == 9
        for revised, historical in reversed(nov20_buffer_reversal):
            assert source.count(revised) == 1, "Nov20 BufferCache successor hunk drift"
            source = source.replace(revised, historical, 1)
        data = source.encode("utf-8")
        actual = hashlib.sha1(b"blob " + str(len(data)).encode() + bytes([0]) + data).hexdigest()
        assert actual == _PS5_RANGE_API_BUFFER_BLOB, (
            "Nov20 BufferCache exact predecessor reconstruction drift")
    if actual == _PS5_RANGE_API_BUFFER_BLOB:
        for revised, historical in ps5_range_api_reversal:
            assert source.count(revised) == 1, "Reviewed RangeSet ABI adaptation drift"
            source = source.replace(revised, historical, 1)
        data = source.encode("utf-8")
        actual = hashlib.sha1(b"blob " + str(len(data)).encode() + bytes([0]) + data).hexdigest()
        assert actual == _FC27_FAST_WRITE_BUFFER_BLOB, (
            "RangeSet ABI reversal modified unrelated historical BufferCache bytes")
    if actual == _FC27_FAST_WRITE_BUFFER_BLOB:
        for inserted, baseline in fc27_fast_write_reversal:
            assert source.count(inserted) == 1, "FC27 clean-page fastpath hunk drift"
            source = source.replace(inserted, baseline, 1)
        raw = source.encode("utf-8")
        restored = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        assert restored == _FC27_SIBLING_BUFFER_BLOB, "FC27 fastpath reversal changed unrelated bytes"
        actual = restored
    if actual == _FC27_SIBLING_BUFFER_BLOB:
        for inserted, baseline in fc27_sibling_page_reversal:
            assert source.count(inserted) == 1, "FC27 sibling-page hunk drift"
            source = source.replace(inserted, baseline, 1)
        raw = source.encode("utf-8")
        restored = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        assert restored == _FC27_BUFFER_BLOB, "FC27 sibling-page reversal changed unrelated bytes"
        actual = restored
    if actual == _FC27_BUFFER_BLOB:
        for inserted, baseline in fc27_cpu_write_reversal:
            assert source.count(inserted) == 1, "FC27 CPU-write hunk drift"
            source = source.replace(inserted, baseline, 1)
        raw = source.encode("utf-8")
        restored = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        assert restored == _PRODUCTION_BUFFER_BLOB, "FC27 BufferCache reversal changed unrelated bytes"
    else:
        assert actual == _PRODUCTION_BUFFER_BLOB, "Production R2 buffer-cache owner drift"
    assert len(r437_r2_reversal) == 5
    for inserted, baseline in reversed(r437_r2_reversal):
        assert source.count(inserted) == 1, "Production R2 hunk drift"
        source = source.replace(inserted, baseline, 1)
    if restore_current_overlap_guard:
        overlap_guard = _integrated_buffer_reversal[1][0]
        overlap_anchor = "    const bool source_dirty = IsRegionRegistered(*cpu_src_address, amount);"
        assert source.count(overlap_guard) == 0
        assert source.count(overlap_anchor) == 1
        source = source.replace(overlap_anchor, overlap_guard + overlap_anchor, 1)
    return source
