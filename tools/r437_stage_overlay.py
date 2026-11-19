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

def restore_r437_without_production_r2(path: Path) -> str:
    actual = subprocess.check_output(
        ["git", "hash-object", str(path)], text=True).strip()
    source = path.read_text()
    if actual == "1dd743515bae8c2829205ec8b3528666ceba8a73":
        current = "template <class P>\ntemplate <typename Ranges>\nvoid BufferCache<P>::ClaimCpuWrites(const Ranges& ranges) {"
        previous = "template <class P>\nvoid BufferCache<P>::ClaimCpuWrites(std::span<const std::pair<DAddr, u64>> ranges) {"
        assert source.count(current) == 1
        source = source.replace(current, previous, 1)
        data = source.encode("utf-8")
        actual = hashlib.sha1(b"blob " + str(len(data)).encode() + bytes([0]) + data).hexdigest()
        assert actual == _PS5_RANGE_API_BUFFER_BLOB
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
    return source
