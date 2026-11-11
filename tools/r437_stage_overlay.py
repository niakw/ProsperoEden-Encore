#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""SHA-pinned R2 rollback for comparing the shipping buffer cache to R437.

The five reviewed R2 insertions remain active in the production header.
Only the verifier reverses them; no runtime code is changed or bypassed.
"""
from pathlib import Path
import subprocess

_PRODUCTION_BUFFER_BLOB = "469eddd0ea9e0a3498446bf08ab473caac3b76f9"
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
    assert actual == _PRODUCTION_BUFFER_BLOB, "Production R2 buffer-cache owner drift"
    source = path.read_text()
    assert len(r437_r2_reversal) == 5
    for inserted, baseline in reversed(r437_r2_reversal):
        assert source.count(inserted) == 1, "Production R2 hunk drift"
        source = source.replace(inserted, baseline, 1)
    return source
