#!/usr/bin/env python3
"""Verify tracked native Vulkan C++ fork exactly matches validated R337 source generator."""
from pathlib import Path
import filecmp
import json
import hashlib
import runpy
import os
import shutil
import subprocess
import sys
import tempfile
from ci.ps5_cache_diag_receipt import (
    normalize_for_historical_proof, reverse_immutable_snapshot_successor,
    reverse_reviewed_source, PARALLEL_TIMING_REVERSES, PARALLEL_TRANSLATION_REVERSES,
    PARALLEL_SNAPSHOT_RETRY_REVERSES, PREWARM_CHANNEL_REVERSES, PREWARM_WORKER_REVERSES,
    PREWARM_WORKER_GENERATED_REVERSES, reverse_distinct_prewarm,
)
def git_blob_sha(text):
    data=text.encode('utf-8')
    return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()

root=Path(__file__).resolve().parents[1]
active=root/'vendor/encore-active/eden-vulkan'
upstream=root/'vendor/sources/eden'
assert (upstream/'VENDOR-ORIGIN.json').exists()
assert (active/'vulkan_renderer.cpp').exists()
# FC27 first-use pipeline completion is owned by the maintained C++,
# never by the historical Eden generator. Seal both complete source blobs
# and the move-before-publication ordering before replaying old oracles.
for relative, reviewed_blob in (
    ('vk_graphics_pipeline_cost.cpp', 'f3c82781675b6979a8be96a333184e048ef57f81'),
    ('vk_compute_pipeline_cost.cpp', 'bb9552866e26e502839eed646be9af6ea0a0db0a'),
):
    owner = active / relative
    raw = owner.read_text()
    raw_blob = subprocess.check_output(
        ['git', 'hash-object', str(owner)], text=True).strip()
    if relative == 'vk_graphics_pipeline_cost.cpp' and raw_blob == (
            'df36d210d04411b87e1fdad7fbd0689b1e4d3488'):
        # GPU-49 is a later fragment-output ownership fix. Rewind only its
        # two graphics-pipeline hunks before checking the older build-task
        # lifetime owner; never restamp that historical receipt.
        gpu49_ctor = """    // Maxwell leaves render-target components not written by the fragment shader untouched.
    // Vulkan otherwise permits undefined values there, which is visible on AMD/RADV.
    for (size_t rt = 0; rt < Maxwell::NumRenderTargets; ++rt) {
        color_output_mask |= u32{stage_infos[NUM_STAGES - 1].frag_color_components[rt]}
                             << (rt * 4);
    }

"""
        gpu49_mask = "        write_mask &= ColorOutputMask(index);\n"
        assert raw.count(gpu49_ctor) == raw.count(gpu49_mask) == 1
        raw = raw.replace(gpu49_ctor, "\n", 1).replace(gpu49_mask, "", 1)
        data = raw.encode()
        assert hashlib.sha1(b'blob '+str(len(data)).encode()+bytes([0])+data).hexdigest() == reviewed_blob
        print('ENCORE_NS1_GPU49_GRAPHICS_BUILD_OWNER_EXACT_REVERSE_PASS')
    else:
        assert raw_blob == reviewed_blob, relative
    assert raw.count('    auto task = std::move(build_task);\n'
                     '    build_task = nullptr;\n'
                     '    task();\n}') == 1, relative
    assert '    build_task();\n    build_task = nullptr;\n}' not in raw, relative
with tempfile.TemporaryDirectory(prefix='eden-vulkan-fork-compare-') as d:
    temp=Path(d)
    # The *production* renderer has always consumed Eden AFTER the ordered
    # 43 shipping backports, not the pristine archive. Reproduce that exact
    # working source before comparing the versioned Vulkan C++ translation
    # units; otherwise stale GPU lifetime / texture-cache patches leak in.
    patched=temp/'patched-eden'
    shutil.copytree(upstream,patched,symlinks=True)
    (patched/'GIT-COMMIT').write_text('5f142c7926d0c7fcbbd0ce30794d72f638a43b2a\n')
    backport_install = subprocess.run(
        [sys.executable, '-B',
         str(root / 'tools/install-vendored-eden-backports.py'), str(patched)],
        timeout=50, capture_output=True, text=True)
    if backport_install.returncode:
        # A captured CalledProcessError alone concealed the failing source
        # path after the graphics merge. Keep strict failure and show the
        # actual bounded installer diagnostics for reproducible repair.
        raise RuntimeError(
            'Vulkan backport staging failed: ' +
            backport_install.stderr[-2800:] + ' ' +
            backport_install.stdout[-1200:])
    # Pin shader input text separately from binary reproducibility. Avoid
    # depending on a nondeterministic host glslangValidator version in CI.
    expected_shader_sha256={
        'vert':'b7efb0f17a2cfb2ac044d0d678dfd7f970323deef86c10d25dde8ed723ef0290',
    }
    for stage, digest in expected_shader_sha256.items():
        source=root/'headless'/f'vulkan_hud.{stage}'
        assert hashlib.sha256(source.read_bytes()).hexdigest()==digest,source
        assert (active/f'vulkan_hud.{stage}.spv').is_file()
    # The maintained fragment changed for the Unicode quick menu. Pin its
    # exact Git blob while keeping the immutable historical oracle SPIR-V
    # below; native CI rebuilds and validates the maintained source separately.
    fragment=root/'headless'/'vulkan_hud.frag'
    assert subprocess.check_output(
        ['git','hash-object',str(fragment)],cwd=root,text=True).strip()==(
            '9fde027ac8dbbd9bca6bfd133e7415bab014e7f8'
        ),fragment
    assert (active/'vulkan_hud.frag.spv').is_file()
    # The vendored oracle SPIR-V stays immutable for historical Vulkan-fork
    # reproduction. The native Encore renderer no longer consumes this fragment
    # after the Montserrat quick-menu change: headless/vulkan.cmake generates
    # eden_vulkan_hud_shaders.h from the maintained GLSL and validates it with
    # spirv-val. Keep the old oracle binary pinned instead of pretending it
    # corresponds to the new maintained fragment source.
    assert hashlib.sha256((active/'vulkan_hud.frag.spv').read_bytes()).hexdigest()==(
        '029a4bb7c594cc3beadefc731a67768e9f80987ae10a2cb20a5a197a8ebea10b'
    ), 'Historical Vulkan HUD oracle SPIR-V drifted'
    env=os.environ.copy()
    env['EDEN_VULKAN_ORACLE_SPV_DIR']=str(active)
    oracle_script=(root/'tools/prepare-vulkan-port.py').read_text()
    vulkan_cmake=(root/'headless/vulkan.cmake').read_text()
    assert "vulkan_oracle = Path(__file__).resolve().parents[1] / 'vendor/encore-active/eden-vulkan-oracles'" in oracle_script
    for part in ("vulkan_loading.inc", "vulkan_hud_prepare.inc", "vulkan_hud_draw.inc",
                 "vulkan_gc_downloads.inc", "vulkan_download_batch.inc"):
        assert (root/'vendor/encore-active/eden-vulkan-oracles'/part).is_file()
        assert not (root/'headless'/part).exists()
        assert (f"vulkan_oracle / '{part}'") in oracle_script
        assert part not in vulkan_cmake, ("oracle accidentally tracked as compiled Vulkan input", part)
    subprocess.run([sys.executable,'-B',str(root/'tools/prepare-vulkan-port.py'),str(patched),str(temp/'generated')],check=True,timeout=150,env=env)
    actual={str(p.relative_to(temp/'generated')):p for p in (temp/'generated').rglob('*') if p.is_file()}
    expected={str(p.relative_to(active)):p for p in active.rglob('*') if p.is_file()}

    # NS1 guest CPU readback: reverse ONLY the new buffer-dirty read decision
    # on audit copies before replaying all historical Vulkan-source receipts.
    # This proves the new Vulkan and bridge methods are byte-exact deltas,
    # without legitimizing arbitrary edits to either maintained source.
    def _ns1_read_blob(data):
        encoded=data.encode('utf-8')
        return hashlib.sha1(b'blob '+str(len(encoded)).encode()+bytes([0])+encoded).hexdigest()
    def reverse_attribute_index_batch_successor(source):
        current = _ns1_read_blob(source)
        if current == "39b2ed67e51937aecad666de4113ce792d32132d":
            newer, older = "VideoCore::RasterizerDownloadArea RasterizerVulkan::GetFlushArea(DAddr addr, u64 size) {\n    ::Eden::Performance::DiagnosticTimer guest_read_timer(::Eden::Performance::guest_cpu_read);\n    const VideoCore::RasterizerDownloadArea clean_area{\n        .start_address = Common::AlignDown(addr, Core::DEVICE_PAGESIZE),\n        .end_address = Common::AlignUp(addr + size, Core::DEVICE_PAGESIZE),\n        .preemtive = true,\n    };\n    // A clean/never-held texture page does not prove that a GPU-written\n    // storage buffer is current in guest memory. Query each cache independently:\n    // never-owned pages remain lock-free, and no two cache locks are nested.\n    std::optional<VideoCore::RasterizerDownloadArea> texture_area;\n    if (!::Eden::ImagePages::NeverHeld(addr, size)) {\n        ::Eden::Performance::GuestCacheLock(texture_cache.mutex, true);\n        std::lock_guard lock{texture_cache.mutex, std::adopt_lock};\n        texture_area = texture_cache.GetFlushArea(addr, size);\n    }\n    if (texture_area && !texture_area->preemtive) {\n        // The existing GPU sync flushes both cache domains.\n        return *texture_area;\n    }\n    auto area = texture_area.value_or(clean_area);\n    // Core::Memory caches the returned interval, not just the original\n    // scalar read. A preemptive texture can extend over other GPU-written\n    // buffers. Check EVERY byte the caller may subsequently read without\n    // re-entering GetFlushArea. Keep the original texture extent when clean.\n    const DAddr buffer_start = area.start_address;\n    const u64 buffer_size = area.end_address - buffer_start;\n    if (!::Eden::BufferPages::NeverRegistered(buffer_start, buffer_size)) {\n        ::Eden::Performance::GuestCacheLock(buffer_cache.mutex, false);\n        std::lock_guard lock{buffer_cache.mutex, std::adopt_lock};\n        if (buffer_cache.IsRegionGpuModified(buffer_start, buffer_size)) {\n            // Preserve the real GPU ownership and the existing ordered\n            // FlushRegion on the GPU worker. Do not certify stale siblings.\n            area.preemtive = false;\n        }\n    }\n    return area;\n}\n", "VideoCore::RasterizerDownloadArea RasterizerVulkan::GetFlushArea(DAddr addr, u64 size) {\n    ::Eden::Performance::DiagnosticTimer guest_read_timer(::Eden::Performance::guest_cpu_read);\n    const VideoCore::RasterizerDownloadArea clean_area{\n        .start_address = Common::AlignDown(addr, Core::DEVICE_PAGESIZE),\n        .end_address = Common::AlignUp(addr + size, Core::DEVICE_PAGESIZE),\n        .preemtive = true,\n    };\n    // A clean/never-held texture page does not prove that a GPU-written\n    // storage buffer is current in guest memory. Query each cache independently:\n    // never-owned pages remain lock-free, and no two cache locks are nested.\n    std::optional<VideoCore::RasterizerDownloadArea> texture_area;\n    if (!::Eden::ImagePages::NeverHeld(addr, size)) {\n        ::Eden::Performance::GuestCacheLock(texture_cache.mutex, true);\n        std::lock_guard lock{texture_cache.mutex, std::adopt_lock};\n        texture_area = texture_cache.GetFlushArea(addr, size);\n    }\n    if (texture_area && !texture_area->preemtive) {\n        // The existing GPU sync flushes both cache domains.\n        return *texture_area;\n    }\n    if (!::Eden::BufferPages::NeverRegistered(addr, size)) {\n        ::Eden::Performance::GuestCacheLock(buffer_cache.mutex, false);\n        std::lock_guard lock{buffer_cache.mutex, std::adopt_lock};\n        if (buffer_cache.IsRegionGpuModified(\n                clean_area.start_address, clean_area.end_address - clean_area.start_address)) {\n            // GPU::OnCPURead must not return early for buffer-only GPU writes.\n            // Keep any texture-covered extent, including its sibling bytes.\n            return VideoCore::RasterizerDownloadArea{\n                .start_address = texture_area\n                    ? (std::min)(texture_area->start_address, clean_area.start_address)\n                    : clean_area.start_address,\n                .end_address = texture_area\n                    ? (std::max)(texture_area->end_address, clean_area.end_address)\n                    : clean_area.end_address,\n                .preemtive = false,\n            };\n        }\n    }\n    return texture_area.value_or(clean_area);\n}\n"
            assert source.count(newer) == 1, "Guest readback extent successor drift"
            source = source.replace(newer, older, 1)
            current = _ns1_read_blob(source)
            assert current == "d8c093893b882175c46fb07c87193468da5f0f7a"
        if current == "d8c093893b882175c46fb07c87193468da5f0f7a":
            for newer, older in (("        // Indirect arguments are read, not overwritten. Preserve GPU dirty bytes.\n        const auto post_op = VideoCommon::ObtainBufferOperation::DoNothing;", "        const auto post_op = VideoCommon::ObtainBufferOperation::DiscardWrite;"), ("        buffer->MarkUsage(offset, 12);\n        scheduler.RequestOutsideRenderPassOperationContext();\n        // Lichii #1246: keep the input barrier in the dispatch command.", "        scheduler.RequestOutsideRenderPassOperationContext();\n        // Lichii #1246: keep the input barrier in the dispatch command.")):
                assert source.count(newer) == 1, "Indirect dispatch ownership successor drift"
                source = source.replace(newer, older, 1)
            current = _ns1_read_blob(source)
            assert current == "4a7ba88e47d686e3d277bee9df48f9b0d81a1248"
        if current == "4a7ba88e47d686e3d277bee9df48f9b0d81a1248":
            indirect_new = "        scheduler.RequestOutsideRenderPassOperationContext();\n        // Lichii #1246: keep the input barrier in the dispatch command. Vulkan\n        // ordering is unchanged, but one scheduler/worker command disappears.\n        scheduler.Record([pipeline, indirect_buffer = buffer->Handle(),\n                          indirect_offset = offset](vk::CommandBuffer cmdbuf) {\n            if (::Eden::DevVulkan::compute_barriers) {\n                cmdbuf.PipelineBarrier(vk::PIPELINE_STAGE_GRAPHICS_COMPUTE_TRANSFER,\n                                       VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT |\n                                           VK_PIPELINE_STAGE_DRAW_INDIRECT_BIT,\n                                       0, COMPUTE_INPUT_BARRIER);\n            }\n            if (!pipeline->IsBound()) {\n                return;\n            }"
            indirect_old = "        scheduler.RequestOutsideRenderPassOperationContext();\n        if (::Eden::DevVulkan::compute_barriers) {\n            scheduler.Record([](vk::CommandBuffer cmdbuf) {\n                cmdbuf.PipelineBarrier(vk::PIPELINE_STAGE_GRAPHICS_COMPUTE_TRANSFER,\n                                       VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT | VK_PIPELINE_STAGE_DRAW_INDIRECT_BIT,\n                                       0, COMPUTE_INPUT_BARRIER);\n            });\n        }\n        scheduler.Record([pipeline, indirect_buffer = buffer->Handle(),\n                          indirect_offset = offset](vk::CommandBuffer cmdbuf) {\n            if (!pipeline->IsBound()) {\n                return;\n            }"
            direct_new = "    static constexpr VkMemoryBarrier READ_BARRIER{\n        .sType = VK_STRUCTURE_TYPE_MEMORY_BARRIER,\n        .pNext = nullptr,\n        .srcAccessMask = VK_ACCESS_MEMORY_WRITE_BIT,\n        .dstAccessMask = VK_ACCESS_MEMORY_READ_BIT,\n    };\n    // Lichii #1246: this barrier was a separate scheduler command although\n    // nothing records Vulkan work between it and the dispatch.\n    scheduler.Record([pipeline, dim](vk::CommandBuffer cmdbuf) {\n        cmdbuf.PipelineBarrier(vk::PIPELINE_STAGE_GRAPHICS_COMPUTE_TRANSFER,\n                               VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT, 0, READ_BARRIER);\n        if (!pipeline->IsBound()) {"
            direct_old = "    static constexpr VkMemoryBarrier READ_BARRIER{\n        .sType = VK_STRUCTURE_TYPE_MEMORY_BARRIER,\n        .pNext = nullptr,\n        .srcAccessMask = VK_ACCESS_MEMORY_WRITE_BIT,\n        .dstAccessMask = VK_ACCESS_MEMORY_READ_BIT,\n    };\n    scheduler.Record([](vk::CommandBuffer cmdbuf) { cmdbuf.PipelineBarrier(vk::PIPELINE_STAGE_GRAPHICS_COMPUTE_TRANSFER, VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,\n                               0, READ_BARRIER); });\n    scheduler.Record([pipeline, dim](vk::CommandBuffer cmdbuf) {\n        if (!pipeline->IsBound()) {"
            assert source.count(indirect_new) == source.count(direct_new) == 1, "Compute barrier folding successor drift"
            source = source.replace(indirect_new, indirect_old, 1).replace(direct_new, direct_old, 1)
            current = _ns1_read_blob(source)
            assert current == "7049700a833c9e6cb239de8b01b5015dd7e3d163", ("Compute barrier folding predecessor drift", current)
        if current == "7049700a833c9e6cb239de8b01b5015dd7e3d163":
            newer = "void RasterizerVulkan::FlushCommands() {\n#ifdef PS5_NATIVE\n    // draw_counter measures graphics batching, not whether Vulkan work exists.\n    // DMA fills/copies and image transfers can record scheduler commands without\n    // any graphics draw. Conversely, a fence/explicit scheduler flush may have\n    // already submitted the current recording. Use the selected native\n    // scheduler's command epoch as the end-of-list authority.\n    draw_counter = 0;\n    if (!scheduler.RecordedSinceSubmit()) {\n        return;\n    }\n#else\n    if (draw_counter == 0) {\n        return;\n    }\n    draw_counter = 0;\n#endif\n    scheduler.Flush();\n}"
            older = "void RasterizerVulkan::FlushCommands() {\n    if (draw_counter == 0) {\n        return;\n    }\n    draw_counter = 0;\n    scheduler.Flush();\n}"
            assert source.count(newer) == 1, "DMA-only submit successor drift"
            source = source.replace(newer, older, 1)
            current = _ns1_read_blob(source)
            assert current == "f79943f596b8a95cdcb05ce74a964a2141ae10ac", ("DMA-only submit predecessor drift", current)
        if current != "f79943f596b8a95cdcb05ce74a964a2141ae10ac":
            return source
        newer = "#ifdef PS5_NATIVE\n    // FC27 uses a vertex-attribute texture handle on indexed triangle draws.\n    // OnCPUWrite is serialized by buffer_cache.mutex before guest memcpy, so\n    // this scan must stay under that lock. Reduce only repeated GMMU walks:\n    // prefetch a small, fully-mapped index span and decode sampled indices\n    // from it. Authenticated NS2 channels retain the original per-index path.\n    struct AttributeIndexBatch {\n        std::array<u8, 256> bytes{};\n        u32 first_position{};\n        u32 position_count{};\n        size_t index_width{};\n        bool valid{};\n    } index_batch;\n#endif\n    const auto read_index = [&](u32 position) {\n        const auto& indices = state.index_buffer;\n        const size_t index_width = indices.FormatSizeInBytes();\n        if (index_width == 0 || index_width > sizeof(u32)) return u32{};\n#ifdef PS5_NATIVE\n        if (!gpu_memory->UsesNativeTiling()) {\n            if (index_batch.valid && index_batch.index_width == index_width &&\n                position >= index_batch.first_position &&\n                position - index_batch.first_position < index_batch.position_count) {\n                u32 index{};\n                const size_t byte_offset =\n                    static_cast<size_t>(position - index_batch.first_position) * index_width;\n                std::memcpy(&index, index_batch.bytes.data() + byte_offset, index_width);\n                return index;\n            }\n            if (position < total) {\n                const size_t max_positions = index_batch.bytes.size() / index_width;\n                const u32 position_count =\n                    (std::min)(total - position, static_cast<u32>(max_positions));\n                const GPUVAddr offset = static_cast<GPUVAddr>(position) * index_width;\n                const GPUVAddr start = indices.IndexStart();\n                const GPUVAddr address = start + offset;\n                const size_t read_bytes = static_cast<size_t>(position_count) * index_width;\n                const bool address_ok =\n                    (position == 0 || offset / index_width == position) &&\n                    address >= start && read_bytes != 0 &&\n                    address <= ~GPUVAddr{0} - static_cast<GPUVAddr>(read_bytes);\n                if (position_count > 1 && address_ok &&\n                    gpu_memory->IsFullyMappedRange(address, read_bytes)) {\n                    gpu_memory->ReadBlockUnsafe(address, index_batch.bytes.data(), read_bytes);\n                    index_batch.first_position = position;\n                    index_batch.position_count = position_count;\n                    index_batch.index_width = index_width;\n                    index_batch.valid = true;\n                    u32 index{};\n                    std::memcpy(&index, index_batch.bytes.data(), index_width);\n                    return index;\n                }\n            }\n        }\n#endif\n        const GPUVAddr address = indices.IndexStart() +\n                                 static_cast<GPUVAddr>(position) * index_width;\n        u32 index{};\n        gpu_memory->ReadBlockUnsafe(address, &index, index_width);\n        return index;\n    };\n    const auto read_handle = [&](u32 position) {\n        const u32 vertex =\n            is_indexed ? static_cast<u32>(state.base_index + read_index(position))\n                       : state.vertex_buffer.first + position;"
        older = "    const auto read_handle = [&](u32 position) {\n        u32 vertex{};\n        if (is_indexed) {\n            const auto& indices = state.index_buffer;\n            const size_t index_width = indices.FormatSizeInBytes();\n            if (index_width == 0 || index_width > sizeof(u32)) return u32{};\n            const GPUVAddr address = indices.IndexStart() +\n                                     static_cast<GPUVAddr>(position) * index_width;\n            u32 index{};\n            gpu_memory->ReadBlockUnsafe(address, &index, index_width);\n            vertex = static_cast<u32>(state.base_index + index);\n        } else {\n            vertex = state.vertex_buffer.first + position;\n        }"
        assert source.count(newer) == 1
        source = source.replace(newer, older, 1)
        assert _ns1_read_blob(source) == "fcd174ed2326f3c205365b192c98f9d2f4d82ec3"
        return source

    def reverse_collected_batch_preflight_successor(source):
        if _ns1_read_blob(source) != "fcd174ed2326f3c205365b192c98f9d2f4d82ec3":
            return source
        newer = "    // One owner-witness pass for the complete collected batch, as in\n    // InnerInvalidation. Each witness is monotonic and fails closed; once both\n    // cache domains may overlap, no later range can change the lock decision.\n    bool may_claim_buffer = false;\n    bool may_touch_texture = false;\n    for (const auto& [addr, size] : ranges) {\n        if (addr == 0 || size == 0) continue;\n        if (!may_claim_buffer && !::Eden::BufferPages::NeverRegistered(addr, size))\n            may_claim_buffer = true;\n        if (!may_touch_texture && !::Eden::ImagePages::NeverHeld(addr, size))\n            may_touch_texture = true;\n        if (may_claim_buffer && may_touch_texture) break;\n    }\n    // GPU-collected write batches acquire each cache domain only once. Claim\n    // still precedes every BufferCache write/readback below.\n"
        older = "    // Remove the complete CPU-write batch from GPU-owned ranges before any\n    // individual invalidation can download stale bytes over a later write.\n    // No registered buffer page in this CPU-write batch means no buffer can\n    // own GPU bytes to claim. Avoid the buffer mutex entirely in that case.\n    // NeverRegistered is monotonic and fails closed on unknown address spans.\n    bool may_claim_buffer = false;\n    for (const auto& [addr, size] : ranges) {\n        if (addr != 0 && size != 0 && !::Eden::BufferPages::NeverRegistered(addr, size)) {\n            may_claim_buffer = true;\n            break;\n        }\n    }\n    // The single-range invalidation callback takes the texture and buffer\n    // mutex once PER range. GPU-collected write batches often contain many\n    // pages; acquire each domain only once, as InnerInvalidation already\n    // does for the same texture -> buffer -> shader ordering. The prior\n    // ClaimCpuWrites still precedes every possible GPU sibling readback.\n    bool may_touch_texture = false;\n    for (const auto& [addr, size] : ranges) {\n        if (addr != 0 && size != 0 && !::Eden::ImagePages::NeverHeld(addr, size)) {\n            may_touch_texture = true;\n            break;\n        }\n    }\n"
        assert source.count(newer) == 1
        source = source.replace(newer, older, 1)
        assert _ns1_read_blob(source) == "e4948333ed15fba8024aeb4ffaa143a2e010f991"
        return source

    def reverse_collected_batch_lock_successor(source):
        if _ns1_read_blob(source) != "e4948333ed15fba8024aeb4ffaa143a2e010f991":
            return source
        newer = "    if (may_claim_buffer) {\n        // Lichii 5e428570 / f5edeab: claim and apply the complete buffer batch\n        // under ONE acquisition. Texture state was handled above and is independent.\n        // Claim must precede BufferCache::WriteMemory so a sibling GPU download\n        // cannot overwrite a later CPU write from this same collected batch.\n        std::scoped_lock lock{buffer_cache.mutex};\n        buffer_cache.ClaimCpuWrites(ranges);\n        for (const auto& [addr, size] : ranges) {\n"
        older = "    if (may_claim_buffer) {\n        std::scoped_lock lock{buffer_cache.mutex};\n        for (const auto& [addr, size] : ranges) {\n"
        marker = "    // The single-range invalidation callback takes the texture and buffer\n"
        first = "    if (may_claim_buffer) {\n        std::scoped_lock lock{buffer_cache.mutex};\n        buffer_cache.ClaimCpuWrites(ranges);\n    }\n\n"
        assert source.count(newer) == source.count(marker) == 1
        source = source.replace(newer, older, 1).replace(marker, first + marker, 1)
        assert _ns1_read_blob(source) == "e5baa7f438d8caf11327989087db38ed1ca053a4"
        return source

    old_read_area="VideoCore::RasterizerDownloadArea RasterizerVulkan::GetFlushArea(DAddr addr, u64 size) {\n    ::Eden::Performance::DiagnosticTimer guest_read_timer(::Eden::Performance::guest_cpu_read);\n    // A guest read cannot overlap a registered image when no page in this\n    // range has ever appeared in the image slot map. Skip the GPU-held mutex.\n    // Unknown/out-of-range/large ranges retain the original blocking path.\n    if (::Eden::ImagePages::NeverHeld(addr, size)) {\n        return VideoCore::RasterizerDownloadArea{\n            .start_address = Common::AlignDown(addr, Core::DEVICE_PAGESIZE),\n            .end_address = Common::AlignUp(addr + size, Core::DEVICE_PAGESIZE),\n            .preemtive = true,\n        };\n    }\n    {\n        ::Eden::Performance::GuestCacheLock(texture_cache.mutex, true);\n        std::lock_guard lock{texture_cache.mutex, std::adopt_lock};\n        auto area = texture_cache.GetFlushArea(addr, size);\n        if (area) {\n            return *area;\n        }\n    }\n    VideoCore::RasterizerDownloadArea new_area{\n        .start_address = Common::AlignDown(addr, Core::DEVICE_PAGESIZE),\n        .end_address = Common::AlignUp(addr + size, Core::DEVICE_PAGESIZE),\n        .preemtive = true,\n    };\n    return new_area;\n}\n"
    new_read_area="VideoCore::RasterizerDownloadArea RasterizerVulkan::GetFlushArea(DAddr addr, u64 size) {\n    ::Eden::Performance::DiagnosticTimer guest_read_timer(::Eden::Performance::guest_cpu_read);\n    const VideoCore::RasterizerDownloadArea clean_area{\n        .start_address = Common::AlignDown(addr, Core::DEVICE_PAGESIZE),\n        .end_address = Common::AlignUp(addr + size, Core::DEVICE_PAGESIZE),\n        .preemtive = true,\n    };\n    // A clean/never-held texture page does not prove that a GPU-written\n    // storage buffer is current in guest memory. Query each cache independently:\n    // never-owned pages remain lock-free, and no two cache locks are nested.\n    std::optional<VideoCore::RasterizerDownloadArea> texture_area;\n    if (!::Eden::ImagePages::NeverHeld(addr, size)) {\n        ::Eden::Performance::GuestCacheLock texture_wait(texture_cache.mutex, true);\n        std::lock_guard lock{texture_cache.mutex, std::adopt_lock};\n        texture_area = texture_cache.GetFlushArea(addr, size);\n    }\n    if (texture_area && !texture_area->preemtive) {\n        // The existing GPU sync flushes both cache domains.\n        return *texture_area;\n    }\n    if (!::Eden::BufferPages::NeverRegistered(addr, size)) {\n        ::Eden::Performance::GuestCacheLock buffer_wait(buffer_cache.mutex, true);\n        std::lock_guard lock{buffer_cache.mutex, std::adopt_lock};\n        if (buffer_cache.IsRegionGpuModified(\n                clean_area.start_address, clean_area.end_address - clean_area.start_address)) {\n            // GPU::OnCPURead must not return early for buffer-only GPU writes.\n            // Keep any texture-covered extent, including its sibling bytes.\n            return VideoCore::RasterizerDownloadArea{\n                .start_address = texture_area\n                    ? (std::min)(texture_area->start_address, clean_area.start_address)\n                    : clean_area.start_address,\n                .end_address = texture_area\n                    ? (std::max)(texture_area->end_address, clean_area.end_address)\n                    : clean_area.end_address,\n                .preemtive = false,\n            };\n        }\n    }\n    return texture_area.value_or(clean_area);\n}\n"
    # NS2 strict completion adds only the native fence entry points.
    # Authenticate both maintained bytes and the exact predecessor before
    # replaying the historical NS1/Vulkan receipt graph on audit copies.
    strict_cpp_delta="#ifdef PS5_NATIVE\nbool RasterizerVulkan::SignalNativeSyncPoint(u32 value) {\n    fence_manager.SignalNativeSyncPoint(value);\n    return true;\n}\n#endif\n\n"
    strict_hdr_delta="#ifdef PS5_NATIVE\n    bool SignalNativeSyncPoint(u32 value) override;\n#endif\n"
    strict_hdr_name='include/video_core/renderer_vulkan/vk_rasterizer.h'
    strict_hdr=expected[strict_hdr_name].read_text()
    # 26/11 exact C797/C7C0 Vulkan retire ABI successor: prove the full
    # shipping header blob and remove ONLY the new native-fence declaration
    # from this audit copy, preserving the earlier NS2 syncpoint receipt.
    if _ns1_read_blob(strict_hdr)=="0d22781acbc4e0f32424beb6b0f494b6aa2b034f":
        native_fence_decl="    bool SignalNativeFence(std::function<void()>&& func) override;\n"
        assert strict_hdr.count(native_fence_decl)==1
        strict_hdr=strict_hdr.replace(native_fence_decl,"",1)
        assert _ns1_read_blob(strict_hdr)=="8bd6f2a4e489aa608fc4420d2ff5847b7c12e165"
    if _ns1_read_blob(strict_hdr)=="8bd6f2a4e489aa608fc4420d2ff5847b7c12e165":
        assert strict_hdr.count(strict_hdr_delta)==1
        strict_hdr=strict_hdr.replace(strict_hdr_delta,"",1)
        assert _ns1_read_blob(strict_hdr)=="6e0bf7ab2a3a2147f9db0c630070db30d9b35d56"
        strict_hdr_path=temp/'normalized-ns2-strict-fence'/strict_hdr_name
        strict_hdr_path.parent.mkdir(parents=True,exist_ok=True)
        strict_hdr_path.write_text(strict_hdr)
        expected[strict_hdr_name]=strict_hdr_path
    for relative, current, previous in (
        ('encore-active/eden-vulkan/vulkan_rasterizer.cpp', '0633e3cf41c615f46791d3943ff40ac22399b047', '1544c6aecbc8cac5bede5a3119e551b1f760dee9'),
        ('encore-active/eden-core/guest-bridge/vulkan_rasterizer.cpp', 'edaa82feb71665e4b6fbfd3ff34d80378e3bca73', '802233b8d5eb72439203a699253c3010c2909ae4'),
    ):
        source_path=root/'vendor'/relative
        source=source_path.read_text()
        if relative.endswith("eden-vulkan/vulkan_rasterizer.cpp"):
            # Normalize only the exact newly selected native fence wrapper
            # before the immutable NS1 readback/FC27 replay chain. The guest
            # path and page-protection methods must remain byte-identical.
            if _ns1_read_blob(source)=="ff8ad79ef203456063dbd848eab3ea575628edfc":
                native_fence_method=(
                    "bool RasterizerVulkan::SignalNativeFence(std::function<void()>&& func) {\n"
                    "    fence_manager.SignalNativeFence(std::move(func));\n"
                    "    return true;\n"
                    "}\n"
                )
                assert source.count(native_fence_method)==1
                source=source.replace(native_fence_method,"",1)
                assert _ns1_read_blob(source)=="39b2ed67e51937aecad666de4113ce792d32132d"
            # Prove the two corrected call-site deltas on an audit copy,
            # then reuse the pre-integration readback and Vulkan receipts.
            source=reverse_attribute_index_batch_successor(source)
            source=reverse_collected_batch_preflight_successor(source)
            source=reverse_collected_batch_lock_successor(source)
            if _ns1_read_blob(source)=="e5baa7f438d8caf11327989087db38ed1ca053a4":
                assert source.count(strict_cpp_delta)==1
                source=source.replace(strict_cpp_delta,"",1)
            assert _ns1_read_blob(source)=="f67815618d25657dcf64a87944b0c0bc5c2d8993"
            begin="VideoCore::RasterizerDownloadArea RasterizerVulkan::GetFlushArea("
            end="\nvoid RasterizerVulkan::InvalidateRegion("
            assert source.count(begin)==source.count(end)==1
            i=source.index(begin)
            j=source.index(end,i)
            section=source[i:j]
            for newer,older in (
                ("::Eden::Performance::GuestCacheLock(texture_cache.mutex, true);",
                 "::Eden::Performance::GuestCacheLock texture_wait(texture_cache.mutex, true);"),
                ("::Eden::Performance::GuestCacheLock(buffer_cache.mutex, false);",
                 "::Eden::Performance::GuestCacheLock buffer_wait(buffer_cache.mutex, true);"),
            ):
                assert section.count(newer)==1 and older not in section
                section=section.replace(newer,older,1)
            source=source[:i]+section+source[j:]
        assert _ns1_read_blob(source)==current, ('NS1 CPU readback owner drift',relative)
        assert source.count(new_read_area)==1, ('NS1 CPU readback method moved',relative)
        restored=source.replace(new_read_area,old_read_area,1)
        assert _ns1_read_blob(restored)==previous, ('NS1 CPU readback predecessor drift',relative)
        if relative.endswith('eden-vulkan/vulkan_rasterizer.cpp'):
            normalized=temp/'normalized-ns1-cpu-read'/'vulkan_rasterizer.cpp'
            normalized.parent.mkdir(parents=True,exist_ok=True)
            normalized.write_text(restored)
            expected['vulkan_rasterizer.cpp']=normalized
    print('ENCORE_NS1_BUFFER_CPU_READ_EXACT_REVERSE_PASS owners=2')

    # GPU-51 (Lichii #7): X8_D24 <-> ABGR8 conversion support changes only
    # three maintained Vulkan owners. Reverse those exact hunks on audit copies
    # before GPU-50 and the frozen historical generator receipts.
    def _gpu51_blob(text):
        data=text.encode('utf-8')
        return hashlib.sha1(b'blob '+str(len(data)).encode()+bytes([0])+data).hexdigest()

    gpu51_edits={
        'blit_image.cpp': (
            '4ba93afb6594213d5bde82be2693f0e08cb1cd63',
            'bbde031a184b93745fa0449aef74f351355fb70d',
            (
                ('''#include "video_core/host_shaders/convert_abgr8_to_d24s8_frag_spv.h"
#include "video_core/host_shaders/convert_abgr8_to_x8d24_frag_spv.h"
#include "video_core/host_shaders/convert_x8d24_to_abgr8_frag_spv.h"
#include "video_core/host_shaders/convert_abgr8_to_d32f_frag_spv.h"''',
                 '''#include "video_core/host_shaders/convert_abgr8_to_d24s8_frag_spv.h"
#include "video_core/host_shaders/convert_abgr8_to_d32f_frag_spv.h"'''),
                ('''      convert_abgr8_to_d24s8_frag(device.IsExtShaderStencilExportSupported()
                                 ? BuildShader(device, CONVERT_ABGR8_TO_D24S8_FRAG_SPV)
                                 : vk::ShaderModule{}),
      convert_abgr8_to_x8d24_frag(BuildShader(device, CONVERT_ABGR8_TO_X8D24_FRAG_SPV)),
      convert_x8d24_to_abgr8_frag(BuildShader(device, CONVERT_X8D24_TO_ABGR8_FRAG_SPV)),
      convert_abgr8_to_d32f_frag(BuildShader(device, CONVERT_ABGR8_TO_D32F_FRAG_SPV)),''',
                 '''      convert_abgr8_to_d24s8_frag(device.IsExtShaderStencilExportSupported()
                                 ? BuildShader(device, CONVERT_ABGR8_TO_D24S8_FRAG_SPV)
                                 : vk::ShaderModule{}),
      convert_abgr8_to_d32f_frag(BuildShader(device, CONVERT_ABGR8_TO_D32F_FRAG_SPV)),'''),
                ('''void BlitImageHelper::ConvertABGR8ToX8D24(const Framebuffer* dst_framebuffer,
                                          const ImageView& src_image_view) {
    ConvertPipelineDepthTargetEx(convert_abgr8_to_x8d24_pipeline, dst_framebuffer->RenderPass(),
                                 convert_abgr8_to_x8d24_frag);
    Convert(*convert_abgr8_to_x8d24_pipeline, dst_framebuffer, src_image_view);
}

void BlitImageHelper::ConvertX8D24ToABGR8(const Framebuffer* dst_framebuffer,
                                          const ImageView& src_image_view) {
    ConvertPipelineEx(convert_x8d24_to_abgr8_pipeline, dst_framebuffer->RenderPass(),
                      convert_x8d24_to_abgr8_frag, true, false);
    Convert(*convert_x8d24_to_abgr8_pipeline, dst_framebuffer, src_image_view);
}

''', ''),
            ),
        ),
        'include/video_core/renderer_vulkan/blit_image.h': (
            'a38cfcf655adcb8ceebfce955b39a2312a239768',
            '81eda086f50e04d3e1537aebff404a6097a07069',
            (
                ('''    void ConvertABGR8ToX8D24(const Framebuffer* dst_framebuffer, const ImageView& src_image_view);

    void ConvertX8D24ToABGR8(const Framebuffer* dst_framebuffer, const ImageView& src_image_view);

''', ''),
                ('''    vk::ShaderModule convert_abgr8_to_x8d24_frag;
    vk::ShaderModule convert_x8d24_to_abgr8_frag;
''', ''),
                ('''    vk::Pipeline convert_abgr8_to_x8d24_pipeline;
    vk::Pipeline convert_x8d24_to_abgr8_pipeline;
''', ''),
            ),
        ),
        'vk_texture_cache_cost.cpp': (
            'e9191238ccddd94aa22570eba501fb05fff5b207',
            '16a8ad80677d992b557ec90283a8f3b483b97440',
            (
                ('''        if (src_view.format == PixelFormat::X8_D24_UNORM) {
            return blit_image_helper.ConvertX8D24ToABGR8(dst, src_view);
        }
''', ''),
                ('''    case PixelFormat::X8_D24_UNORM:
        if (src_view.format == PixelFormat::A8B8G8R8_UNORM) {
            return blit_image_helper.ConvertABGR8ToX8D24(dst, src_view);
        }
        break;
''', ''),
            ),
        ),
    }
    for gpu51_name,(current_blob,predecessor_blob,edits) in gpu51_edits.items():
        raw=expected[gpu51_name].read_text()
        assert _gpu51_blob(raw)==current_blob, ("GPU-51 owner drift",gpu51_name,_gpu51_blob(raw))
        normalized=raw
        for newer,older in edits:
            assert normalized.count(newer)==1, ("GPU-51 audit hunk drift",gpu51_name,newer[:100])
            normalized=normalized.replace(newer,older,1)
        assert _gpu51_blob(normalized)==predecessor_blob, (
            "GPU-51 predecessor reconstruction failed",gpu51_name,_gpu51_blob(normalized))
        out=temp/'normalized-vendor-gpu51'/gpu51_name
        out.parent.mkdir(parents=True,exist_ok=True)
        out.write_text(normalized)
        expected[gpu51_name]=out
    print("ENCORE_NS1_GPU51_X8D24_CONVERSION_EXACT_REVERSE_PASS owners=3")

    # GPU-54 (Lichii #295 / 73bcdc059d): WFI must be repeatable and memory-visible.
    # Reverse the exact production changes only on audit copies before GPU-50/49 and
    # frozen R23 receipts. Shipping source keeps the barrier and no reusable event.
    gpu54_edits={
        'vulkan_rasterizer.cpp': (
            '1544c6aecbc8cac5bede5a3119e551b1f760dee9',
            '8473aa19cd3cdcf8546dce994ceb69cbee2b1220',
            (
                (
"""      fence_manager(*this, gpu, texture_cache, buffer_cache, query_cache, device, scheduler) {
""",
"""      fence_manager(*this, gpu, texture_cache, buffer_cache, query_cache, device, scheduler),
      wfi_event(device.GetLogical().CreateEvent()) {
"""
                ),
                (
"""    scheduler.RequestOutsideRenderPassOperationContext();
    scheduler.Record([flags](vk::CommandBuffer cmdbuf) {
        // A reusable event that is never reset only orders its first signal and, without a
        // memory barrier, does not make earlier GPU writes visible to subsequent commands.
        // A pipeline barrier expresses both the execution dependency and the guest WFI memory
        // visibility on every invocation. Adapted from Lichii #295 / 73bcdc059d.
        static constexpr VkMemoryBarrier WFI_BARRIER{
            .sType = VK_STRUCTURE_TYPE_MEMORY_BARRIER,
            .pNext = nullptr,
            .srcAccessMask = VK_ACCESS_MEMORY_WRITE_BIT,
            .dstAccessMask = VK_ACCESS_MEMORY_READ_BIT | VK_ACCESS_MEMORY_WRITE_BIT,
        };
        cmdbuf.PipelineBarrier(flags, VK_PIPELINE_STAGE_ALL_COMMANDS_BIT, 0, WFI_BARRIER);
    });
    fence_manager.SignalOrdering();
""",
"""    scheduler.RequestOutsideRenderPassOperationContext();
    scheduler.Record([event = *wfi_event, flags](vk::CommandBuffer cmdbuf) {
        cmdbuf.SetEvent(event, flags);
        cmdbuf.WaitEvents(event, flags, VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT, {}, {}, {});
    });
    fence_manager.SignalOrdering();
"""
                ),
            ),
        ),
        'include/video_core/renderer_vulkan/vk_rasterizer.h': (
            '6e0bf7ab2a3a2147f9db0c630070db30d9b35d56',
            'f18e79dfece6eba3e4984b3ec0645abbfe1760e1',
            (
                ("    FenceManager fence_manager;\n\n\n#ifdef PS5_NATIVE\n",
                 "    FenceManager fence_manager;\n\n    vk::Event wfi_event;\n\n#ifdef PS5_NATIVE\n"),
            ),
        ),
    }
    def gpu54_blob(text):
        raw=text.encode('utf-8')
        return hashlib.sha1(b'blob '+str(len(raw)).encode()+bytes([0])+raw).hexdigest()
    for gpu54_name,(current_blob,predecessor_blob,edits) in gpu54_edits.items():
        raw=expected[gpu54_name].read_text()
        actual_blob=gpu54_blob(raw)
        if actual_blob == current_blob:
            if gpu54_name == 'vulkan_rasterizer.cpp':
                wfi=raw.split('void RasterizerVulkan::WaitForIdle() {',1)[1].split(
                    '\nvoid RasterizerVulkan::FragmentBarrier()',1)[0]
                assert 'VK_ACCESS_MEMORY_WRITE_BIT' in wfi
                assert 'VK_ACCESS_MEMORY_READ_BIT | VK_ACCESS_MEMORY_WRITE_BIT' in wfi
                assert 'VK_PIPELINE_STAGE_ALL_COMMANDS_BIT' in wfi
                assert 'cmdbuf.PipelineBarrier(' in wfi
                assert 'cmdbuf.SetEvent(' not in wfi and 'cmdbuf.WaitEvents(' not in wfi
            else:
                assert 'wfi_event' not in raw
            normalized=raw
            for newer,older in edits:
                assert normalized.count(newer)==1, ('GPU-54 audit hunk drift',gpu54_name)
                normalized=normalized.replace(newer,older,1)
            assert gpu54_blob(normalized)==predecessor_blob, (
                'GPU-54 predecessor reconstruction failed',gpu54_name,gpu54_blob(normalized))
            out=temp/'normalized-vendor-gpu54'/gpu54_name
            out.parent.mkdir(parents=True,exist_ok=True)
            out.write_text(normalized)
            expected[gpu54_name]=out
        else:
            assert actual_blob == predecessor_blob, ('Unexpected GPU-54 owner',gpu54_name,actual_blob)
    print("ENCORE_NS1_GPU54_WFI_BARRIER_EXACT_REVERSE_PASS owners=2 repeatable=1 memory_visible=1")

    # GPU-50 (Lichii #2047): reverse only the reviewed Maxwell DMA cache
    # notification on an audit COPY; shipping NS1 retains granular coherency.
    # GPU-49 and older Vulkan receipts must compare against their exact owner.
    gpu50_owner='vulkan_rasterizer.cpp'
    gpu50_shipped=expected[gpu50_owner].read_text()
    def gpu50_blob(data):
        raw=data.encode('utf-8')
        return hashlib.sha1(b'blob '+str(len(raw)).encode()+bytes([0])+raw).hexdigest()
    assert gpu50_blob(gpu50_shipped)=="8473aa19cd3cdcf8546dce994ceb69cbee2b1220", 'GPU-50 raster owner drift'
    gpu50_new_method="bool AccelerateDMA::BufferCopy(GPUVAddr src_address, GPUVAddr dest_address, u64 amount) {\n    // Invalid DMA byte counts have no GPU buffer range; return to the\n    // software path without contending on the guest buffer cache mutex.\n    if (amount == 0 || amount > static_cast<u64>(~u32{0})) {\n        return false;\n    }\n    // A buffer DMA updates guest memory without invoking the texture-cache\n    // CPU-write callback. Hold both cache locks over the ownership decision\n    // and copy so another thread cannot publish a newer image in between.\n    // Lichii c84935f / 47d2368 / 36bfb77: only invalidate destination images\n    // whose latest bytes are already in guest memory. Skip the unsafe case\n    // rather than uploading stale CPU bytes over GPU-owned image contents.\n    std::scoped_lock lock{buffer_cache.mutex, texture_cache.mutex};\n    bool copied_gpu_bytes = false;\n    boost::container::small_vector<std::pair<DAddr, size_t>, 4> gpu_written_dest;\n    if (!buffer_cache.DMACopy(src_address, dest_address, amount, &copied_gpu_bytes,\n                              &gpu_written_dest)) {\n        return false;\n    }\n    if (gpu_memory && gpu_memory->UsesNativeTiling()) {\n        // GPU-50 is an NS1 Maxwell coherency fix. Keep the separately owned\n        // native-tiling/NS2 policy byte-for-byte equivalent to its old guard.\n        if (!copied_gpu_bytes &&\n            !texture_cache.IsGpuMemoryGpuModified(src_address, amount) &&\n            !texture_cache.IsGpuMemoryGpuModified(dest_address, amount)) {\n            texture_cache.WriteGpuMemory(dest_address, amount);\n        }\n    } else {\n        texture_cache.WriteDmaCopy(src_address, dest_address, static_cast<size_t>(amount),\n                                   gpu_written_dest);\n    }\n    return true;\n}\n"
    gpu50_old_method="bool AccelerateDMA::BufferCopy(GPUVAddr src_address, GPUVAddr dest_address, u64 amount) {\n    // Invalid DMA byte counts have no GPU buffer range; return to the\n    // software path without contending on the guest buffer cache mutex.\n    if (amount == 0 || amount > static_cast<u64>(~u32{0})) {\n        return false;\n    }\n    // A buffer DMA updates guest memory without invoking the texture-cache\n    // CPU-write callback. Hold both cache locks over the ownership decision\n    // and copy so another thread cannot publish a newer image in between.\n    // Lichii c84935f / 47d2368 / 36bfb77: only invalidate destination images\n    // whose latest bytes are already in guest memory. Skip the unsafe case\n    // rather than uploading stale CPU bytes over GPU-owned image contents.\n    std::scoped_lock lock{buffer_cache.mutex, texture_cache.mutex};\n    bool copied_gpu_bytes = false;\n    if (!buffer_cache.DMACopy(src_address, dest_address, amount, &copied_gpu_bytes)) {\n        return false;\n    }\n    if (!copied_gpu_bytes &&\n        !texture_cache.IsGpuMemoryGpuModified(src_address, amount) &&\n        !texture_cache.IsGpuMemoryGpuModified(dest_address, amount)) {\n        texture_cache.WriteGpuMemory(dest_address, amount);\n    }\n    return true;\n}\n"
    assert gpu50_shipped.count(gpu50_new_method)==1, 'GPU-50 method hunk drift'
    gpu50_predecessor=gpu50_shipped.replace(gpu50_new_method,gpu50_old_method,1)
    assert gpu50_blob(gpu50_predecessor)=="6cb282532b308478ca0d9237d399fe4259e42fca", 'GPU-50 predecessor mismatch'
    gpu50_audit=temp/'normalized-vendor-gpu50'/gpu50_owner
    gpu50_audit.parent.mkdir(parents=True,exist_ok=True)
    gpu50_audit.write_text(gpu50_predecessor)
    expected[gpu50_owner]=gpu50_audit
    print("ENCORE_NS1_GPU50_DMA_TEXTURE_EXACT_REVERSE_PASS")

    # GPU-49 (Lichii #353) is newer than the frozen Vulkan generator receipts.
    # Reverse its exact production hunks on audit COPIES, proving every owner
    # reconstructs its immediate GPU-48/GPU-47 predecessor byte-for-byte.
    def _gpu49_blob(text):
        data=text.encode('utf-8')
        return hashlib.sha1(b'blob '+str(len(data)).encode()+bytes([0])+data).hexdigest()

    gpu49_edits={
        'vk_graphics_pipeline_cost.cpp': (
            'df36d210d04411b87e1fdad7fbd0689b1e4d3488',
            'f3c82781675b6979a8be96a333184e048ef57f81',
            (
                ("""    // Maxwell leaves render-target components not written by the fragment shader untouched.
    // Vulkan otherwise permits undefined values there, which is visible on AMD/RADV.
    for (size_t rt = 0; rt < Maxwell::NumRenderTargets; ++rt) {
        color_output_mask |= u32{stage_infos[NUM_STAGES - 1].frag_color_components[rt]}
                             << (rt * 4);
    }

""", "\n"),
                ("        write_mask &= ColorOutputMask(index);\n", ""),
            ),
        ),
        'include/video_core/renderer_vulkan/vk_graphics_pipeline.h': (
            'c1ed0200afd3666056dfe0ef60705015a923dac7',
            'cc53133dd516e2d1d245326866ab3ce0c852b36b',
            (
                ("""    [[nodiscard]] VkColorComponentFlags ColorOutputMask(size_t render_target) const noexcept {
        return (color_output_mask >> (render_target * 4)) & 0xF;
    }

    [[nodiscard]] u32 ColorOutputMask() const noexcept {
        return color_output_mask;
    }

""", ""),
                ("    bool fragment_has_color0_output{};\n    u32 color_output_mask{};\n",
                 "    bool fragment_has_color0_output{};\n"),
            ),
        ),
        'vulkan_rasterizer.cpp': (
            '6cb282532b308478ca0d9237d399fe4259e42fca',
            '891343dabc62855110ac1139ac2b817022eb97b5',
            (
                ("""    if (device.IsExtExtendedDynamicState3BlendingSupported()) {
        // prepared_pipeline is set only for a real guest draw. DrawTexture leaves it null,
        // so its raw blit keeps the full write mask and avoids a cold pipeline lookup.
        UpdateBlending(regs, prepared_pipeline);
    } else if (device.IsExtColorWriteEnableSupported()) {
""",
                 """    if (device.IsExtExtendedDynamicState3BlendingSupported()) {
        UpdateBlending(regs);
    } else if (device.IsExtColorWriteEnableSupported()) {
"""),
                ("""void RasterizerVulkan::UpdateBlending(Tegra::Engines::Maxwell3D::Regs& regs,
                                      const GraphicsPipeline* pipeline) {
    const u32 color_output_mask = pipeline ? pipeline->ColorOutputMask() : ~0U;
    const bool color_output_changed = color_output_mask != last_color_output_mask;
    if (!state_tracker.TouchBlending() && !color_output_changed) {
        return;
    }

    if (state_tracker.TouchColorMask() || color_output_changed) {
        last_color_output_mask = color_output_mask;
        std::array<VkColorComponentFlags, Maxwell::NumRenderTargets> setup_masks{};
""",
                 """void RasterizerVulkan::UpdateBlending(Tegra::Engines::Maxwell3D::Regs& regs) {
    if (!state_tracker.TouchBlending()) {
        return;
    }

    if (state_tracker.TouchColorMask()) {
        std::array<VkColorComponentFlags, Maxwell::NumRenderTargets> setup_masks{};
"""),
                ("            current &= (color_output_mask >> (index * 4)) & 0xF;\n", ""),
            ),
        ),
        'include/video_core/renderer_vulkan/vk_rasterizer.h': (
            'f18e79dfece6eba3e4984b3ec0645abbfe1760e1',
            'db60043206cc66a284bd3e9327a9fed7b011b25a',
            (
                ("""    void UpdateBlending(Tegra::Engines::Maxwell3D::Regs& regs,
                        const GraphicsPipeline* pipeline);
""",
                 "    void UpdateBlending(Tegra::Engines::Maxwell3D::Regs& regs);\n"),
                ("    u32 draw_counter = 0;\n    u32 last_color_output_mask{};\n",
                 "    u32 draw_counter = 0;\n"),
            ),
        ),
    }
    gpu49_predecessor_paths={}
    for gpu49_name,(current_blob,predecessor_blob,edits) in gpu49_edits.items():
        raw=expected[gpu49_name].read_text()
        actual_blob=_gpu49_blob(raw)
        if actual_blob == current_blob:
            normalized=raw
            for newer,older in edits:
                assert normalized.count(newer)==1, ("GPU-49 audit hunk drift",gpu49_name,newer[:90])
                normalized=normalized.replace(newer,older,1)
            assert _gpu49_blob(normalized)==predecessor_blob, (
                "GPU-49 predecessor reconstruction failed",gpu49_name,_gpu49_blob(normalized))
            out=temp/'normalized-vendor-gpu49'/gpu49_name
            out.parent.mkdir(parents=True,exist_ok=True)
            out.write_text(normalized)
            expected[gpu49_name]=out
            gpu49_predecessor_paths[gpu49_name]=out
        else:
            assert actual_blob == predecessor_blob, ("Unexpected GPU-49 owner",gpu49_name,actual_blob)
            gpu49_predecessor_paths[gpu49_name]=expected[gpu49_name]
    print("ENCORE_NS1_GPU49_FRAGMENT_OUTPUT_EXACT_REVERSE_PASS owners=4")

    # GPU-47 is the framebuffer-limit subset of Lichii #427 only. Reverse its
    # exact texture-cache hunk before GPU-46; StreamBuffer is intentionally
    # untouched because it is a separate upstream change.
    gpu47_texture_name='vk_texture_cache_cost.cpp'
    gpu47_current='16a8ad80677d992b557ec90283a8f3b483b97440'
    gpu47_predecessor='a12ef3892565ce80f17c30b3cb54fa337718ccff'
    gpu47_text=expected[gpu47_texture_name].read_text()
    gpu47_blob=hashlib.sha1(
        b'blob '+str(len(gpu47_text.encode())).encode()+bytes([0])+gpu47_text.encode()
    ).hexdigest()
    if gpu47_blob == gpu47_current:
        gpu47_block=(
            "    // Vulkan framebuffer dimensions are device limits, not guest clip limits.\n"
            "    // Attachment-less draws can retain a 32768x32768 surface clip even when\n"
            "    // the host only exposes 16384. Clamp every framebuffer before creation.\n"
            "    const auto clamp_extent = [&runtime](VkExtent2D extent) {\n"
            "        extent.width =\n"
            "            (std::max)(1U, (std::min)(extent.width, runtime.device.GetMaxFramebufferWidth()));\n"
            "        extent.height =\n"
            "            (std::max)(1U, (std::min)(extent.height, runtime.device.GetMaxFramebufferHeight()));\n"
            "        return extent;\n"
            "    };\n"
            "    layers = (std::max)(1U, (std::min)(layers, runtime.device.GetMaxFramebufferLayers()));\n"
        )
        assert gpu47_text.count(gpu47_block)==1, "GPU-47 texture limit block drift"
        gpu47_text=gpu47_text.replace(gpu47_block,"",1)
        gpu47_new_mixed=(
            "        const VkExtent2D extent = clamp_extent(\n"
            "            {(std::min)(render_area.width, width), (std::min)(render_area.height, height)});"
        )
        gpu47_old_mixed=(
            "        const VkExtent2D extent{(std::min)(render_area.width, width),\n"
            "                                (std::min)(render_area.height, height)};"
        )
        assert gpu47_text.count(gpu47_new_mixed)==1, "GPU-47 mixed extent drift"
        gpu47_text=gpu47_text.replace(gpu47_new_mixed,gpu47_old_mixed,1)
        assert gpu47_text.count("    render_area = clamp_extent(render_area);\n")==1
        gpu47_text=gpu47_text.replace("    render_area = clamp_extent(render_area);\n","",1)
        data=gpu47_text.encode()
        assert hashlib.sha1(b'blob '+str(len(data)).encode()+bytes([0])+data).hexdigest()==gpu47_predecessor, (
            "GPU-47 texture reversal did not restore GPU-46 predecessor")
        out=temp/'normalized-vendor-gpu47'/gpu47_texture_name
        out.parent.mkdir(parents=True,exist_ok=True)
        out.write_text(gpu47_text)
        expected[gpu47_texture_name]=out
        print("ENCORE_NS1_GPU47_VULKAN_LIMIT_EXACT_REVERSE_PASS texture=1",flush=True)
    else:
        assert gpu47_blob==gpu47_predecessor, ("Unexpected GPU-47 texture owner",gpu47_blob)

    # GPU-46 is a reviewed production successor to the historical Vulkan
    # generator: Vulkan framebuffer layers are bounded by the smallest
    # attachment and clear ranges are clipped to that exact count. Reverse
    # ONLY these exact hunks on audit copies; shipping owners stay untouched.
    def _blob_text(text):
        data=text.encode('utf-8')
        return hashlib.sha1(b'blob '+str(len(data)).encode()+bytes([0])+data).hexdigest()

    gpu46_edits={
        'include/video_core/renderer_vulkan/vk_texture_cache.h': (
            '6623a5d5164d4b09f1ea9089b62b7c5fdfdfaa05',
            '1b725abab76168d9787d9b062d7406df733cf49d',
            (
                ("    [[nodiscard]] u32 Layers() const noexcept {\n"
                 "        return layers;\n"
                 "    }\n\n", ""),
                ("    u32 num_images = 0;\n"
                 "    u32 layers = 1;\n",
                 "    u32 num_images = 0;\n"),
            ),
        ),
        'vk_texture_cache_cost.cpp': (
            'a12ef3892565ce80f17c30b3cb54fa337718ccff',
            '88c2221eae24b0b3c46e81dfdb27c3a833f77fc6',
            (
                ("    s32 num_layers = (std::numeric_limits<s32>::max)();",
                 "    s32 num_layers = 1;"),
                ("        num_layers = (std::min)(num_layers, color_buffer->range.extent.layers);",
                 "        num_layers = (std::max)(num_layers, color_buffer->range.extent.layers);"),
                ("        num_layers = (std::min)(num_layers, depth_buffer->range.extent.layers);",
                 "        num_layers = (std::max)(num_layers, depth_buffer->range.extent.layers);"),
                ("    if (num_layers == (std::numeric_limits<s32>::max)()) {\n"
                 "        num_layers = 1;\n"
                 "    }\n"
                 "    layers = static_cast<u32>((std::max)(num_layers, 1));\n", ""),
                ("        CreateMixedSamplesFramebuffer(runtime, color_buffers, attachments, renderpass_key,\n"
                 "                                      layers, extent);",
                 "        CreateMixedSamplesFramebuffer(runtime, color_buffers, attachments, renderpass_key,\n"
                 "                                      static_cast<u32>((std::max)(num_layers, 1)), extent);"),
                ("    if (do_resolve_color) {\n"
                 "        for (size_t index = 0; index < NUM_RT; ++index) {",
                 "    if (do_resolve_color) {\n"
                 "        const u32 layers = static_cast<u32>((std::max)(num_layers, 1));\n"
                 "        for (size_t index = 0; index < NUM_RT; ++index) {"),
                ("    if (do_resolve_depth_stencil) {\n"
                 "        const VkFormat vk_format =",
                 "    if (do_resolve_depth_stencil) {\n"
                 "        const u32 layers = static_cast<u32>((std::max)(num_layers, 1));\n"
                 "        const VkFormat vk_format ="),
                ("    CreateVkFramebuffer(runtime, attachments, layers);",
                 "    CreateVkFramebuffer(runtime, attachments, static_cast<u32>((std::max)(num_layers, 1)));"),
            ),
        ),
        'vulkan_rasterizer.cpp': (
            '891343dabc62855110ac1139ac2b817022eb97b5',
            'fdd5a73ccf795fd58100469c546b544a86a68e5b',
            (
                ("    const u32 framebuffer_layers = framebuffer->Layers();\n"
                 "    const u32 clear_base_layer = regs.clear_surface.layer;\n"
                 "    if (layer_count == 0 || clear_base_layer >= framebuffer_layers) {\n"
                 "        return;\n"
                 "    }\n"
                 "    const u32 clear_layer_count =\n"
                 "        (std::min)(layer_count, framebuffer_layers - clear_base_layer);\n"
                 "    const bool clear_covers_all_layers =\n"
                 "        clear_base_layer == 0 && clear_layer_count == framebuffer_layers;\n\n", "\n"),
                ("        .baseArrayLayer = clear_base_layer,\n"
                 "        .layerCount = clear_layer_count,",
                 "        .baseArrayLayer = regs.clear_surface.layer,\n"
                 "        .layerCount = layer_count,"),
                ("                                 clear_covers_all_layers &&\n",
                 "                                 regs.clear_surface.layer == 0 &&\n"),
                ("                can_defer_clear && !ds_used && clear_layer_count == 1 &&\n"
                 "                framebuffer_layers == 1 &&\n",
                 "                can_defer_clear && !ds_used && layer_count == 1 &&\n"),
            ),
        ),
    }
    for gpu46_name,(current_blob,predecessor_blob,edits) in gpu46_edits.items():
        raw=expected[gpu46_name].read_text()
        actual_blob=_blob_text(raw)
        if actual_blob == current_blob:
            normalized=raw
            for newer,older in edits:
                assert normalized.count(newer)==1, ("GPU-46 audit hunk drift",gpu46_name,newer[:80])
                normalized=normalized.replace(newer,older,1)
            assert _blob_text(normalized)==predecessor_blob, (
                "GPU-46 predecessor reconstruction failed",gpu46_name,_blob_text(normalized))
            out=temp/'normalized-vendor-gpu46'/gpu46_name
            out.parent.mkdir(parents=True,exist_ok=True)
            out.write_text(normalized)
            expected[gpu46_name]=out
        elif (gpu46_name == 'include/video_core/renderer_vulkan/vk_texture_cache.h' and
              actual_blob == 'ecdadfd6b699d1d4ec58be58f7e37287c1986717'):
            # The generic Vulkan header now shares GPU-46's layer storage with
            # the PS5 ASTC header, but intentionally does not expose Layers().
            # Reverse exactly that one declaration on this audit copy.
            newer, older = edits[1]
            assert raw.count(newer) == 1 and edits[0][0] not in raw, (
                "GPU-46 generic header parity drift", actual_blob)
            normalized = raw.replace(newer, older, 1)
            assert _blob_text(normalized) == predecessor_blob, (
                "GPU-46 generic predecessor reconstruction failed", _blob_text(normalized))
            out = temp/'normalized-vendor-gpu46'/gpu46_name
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(normalized)
            expected[gpu46_name] = out
        else:
            assert actual_blob == predecessor_blob, ("Unexpected GPU-46 owner",gpu46_name,actual_blob)
    print("ENCORE_NS1_GPU46_VULKAN_LAYER_EXACT_REVERSE_PASS owners=3")
    # c30f46 publishes build completion from the task and can let cache
    # teardown destroy the pipeline before RunBuild returns. Shipping code
    # moves the callback out before invocation. Reverse that exact one-method
    # lifetime fix ONLY on the audit copy so the older transition receipt can
    # be replayed in chronological order: f3c827 -> bae8f3 -> 2834a1.
    transition_cpp = 'vk_graphics_pipeline_cost.cpp'
    transition_source = expected[transition_cpp].read_text()
    if subprocess.check_output(
        ['git', 'hash-object', str(expected[transition_cpp])], text=True
    ).strip() == 'f3c82781675b6979a8be96a333184e048ef57f81':
        release_after = """    // The build callback publishes is_built before it returns. Cache teardown
    // may then destroy this pipeline; never access its members afterward.
    // Transfer ownership while this instance is still guaranteed alive.
    auto task = std::move(build_task);
    build_task = nullptr;
    task();
"""
        release_before = """    build_task();
    build_task = nullptr;
"""
        assert transition_source.count(release_after) == 1
        transition_source = transition_source.replace(release_after, release_before, 1)
        transition_path = temp/'normalized-vendor-graphics-build-task-lifetime'/transition_cpp
        transition_path.parent.mkdir(parents=True, exist_ok=True)
        transition_path.write_text(transition_source)
        assert subprocess.check_output(
            ['git', 'hash-object', str(transition_path)], text=True
        ).strip() == 'bae8f3c36fc4e595e9b630ca55cc50496468e173'
        expected[transition_cpp] = transition_path
        print('ENCORE_GRAPHICS_BUILD_TASK_LIFETIME_EXACT_REVERSE_PASS')

    # Per-pipeline successor memo is a hint, never an owner. Reverse the
    # bounded PS5-native hot-edge ring on an audit COPY before historical
    # generated Vulkan oracles, sealing both complete active C++ blobs.
    # Applicability follows the two complete reviewed source owners, not the
    # moving vendor gitlink. Later NS1 DMA / NS2-only commits preserve these
    # bytes; any real transition-owner drift skips reversal and fails below.
    if (
        subprocess.check_output(
            ['git', 'hash-object', str(expected['vk_graphics_pipeline_cost.cpp'])],
            text=True).strip() == 'bae8f3c36fc4e595e9b630ca55cc50496468e173'
        and subprocess.check_output(
            ['git', 'hash-object',
             str(expected['include/video_core/renderer_vulkan/vk_graphics_pipeline.h'])],
            text=True).strip() == 'cc53133dd516e2d1d245326866ab3ce0c852b36b'
    ):
        transitions = {
            'vk_graphics_pipeline_cost.cpp': ('bae8f3c36fc4e595e9b630ca55cc50496468e173', '2834a18fe7638749ec83cc8f5feb1fcde6c71a9a', "void GraphicsPipeline::AddTransition(GraphicsPipeline* transition) {\n#ifdef PS5_NATIVE\n    // Only a fast-path hint: the canonical graphics_cache still owns ALL\n    // pipelines. A pipeline with hundreds of different successors must not\n    // accumulate unbounded state or scan every former successor on each miss.\n    // The two HUD/overlay hot indices remain pinned across ring replacement.\n    if (transition_keys.size() >= kNativeTransitionHintLimit) {\n        size_t slot = next_transition_replacement;\n        for (size_t skipped = 0; skipped < 2; ++skipped) {\n            if (slot != hot_transition_indices[0] &&\n                slot != hot_transition_indices[1]) break;\n            slot = (slot + 1) % kNativeTransitionHintLimit;\n        }\n        // Both vectors are already fully allocated here. Replacing a hint\n        // cannot invalidate a live shader pipeline or allocate GPU objects.\n        transition_keys[slot] = transition->key;\n        transitions[slot] = transition;\n        next_transition_replacement = (slot + 1) % kNativeTransitionHintLimit;\n        return;\n    }\n    // Before the hint ring is full, preserve the exception-safe pairing\n    // of keys and pointers on the GPU owner.\n    try {\n        transition_keys.push_back(transition->key);\n    } catch (...) {\n        return;\n    }\n#else\n    transition_keys.push_back(transition->key);\n#endif\n#ifdef PS5_NATIVE\n    try {\n        transitions.push_back(transition);\n    } catch (...) {\n        transition_keys.pop_back();\n        return;\n    }\n#else\n    transitions.push_back(transition);\n#endif\n}", "void GraphicsPipeline::AddTransition(GraphicsPipeline* transition) {\n#ifdef PS5_NATIVE\n    // Both appends are optional memoization. The canonical graphics cache\n    // already owns the target and will resolve a missing edge on demand.\n    try {\n        transition_keys.push_back(transition->key);\n    } catch (...) {\n        return;\n    }\n#else\n    transition_keys.push_back(transition->key);\n#endif\n#ifdef PS5_NATIVE\n    // Both arrays must describe the same transition index. An allocation\n    // failure while appending the pointer must not leave an orphaned key:\n    // Next() would later index past transitions and corrupt a guest draw.\n    try {\n        transitions.push_back(transition);\n    } catch (...) {\n        // Transition memoization is optional. The primary graphics cache\n        // already owns the pipeline; a later lookup can use its slow path.\n        // Do not abort a guest draw solely because this edge could not fit.\n        transition_keys.pop_back();\n        return;\n    }\n#else\n    transitions.push_back(transition);\n#endif\n}"),
            'include/video_core/renderer_vulkan/vk_graphics_pipeline.h': ('cc53133dd516e2d1d245326866ab3ce0c852b36b', '515a766a6cc4d6fcba7692ad396f45396b746d28', "    // Transition hints are not the pipeline owners. Limit their memory\n    // growth and the O(N) unsuccessful Next() search on shader-heavy titles.\n    // The canonical graphics_cache remains complete and handles all misses.\n    static constexpr size_t kNativeTransitionHintLimit = 64;\n    // GPU owner only: the two hot indices stay valid across vector growth\n    // and are never replaced when the bounded ring rolls over.\n    std::array<size_t, 2> hot_transition_indices{};\n    size_t next_transition_replacement{};\n", "    // GPU owner only. Two valid indices remain stable across vector growth.\n    std::array<size_t, 2> hot_transition_indices{};\n"),
        }
        for name, (new_blob, old_blob, new_hunk, old_hunk) in transitions.items():
            active_blob = subprocess.check_output(['git', 'hash-object', str(expected[name])], text=True).strip()
            assert active_blob == new_blob, ('bounded transition source changed', name, active_blob)
            active_text = expected[name].read_text()
            assert active_text.count(new_hunk) == 1, ('bounded transition hunk changed', name)
            restored = active_text.replace(new_hunk, old_hunk, 1)
            oracle_path = temp/'fc27-bounded-graphics-transition-oracle'/name
            oracle_path.parent.mkdir(parents=True, exist_ok=True)
            oracle_path.write_text(restored)
            reconstructed = subprocess.check_output(['git', 'hash-object', str(oracle_path)], text=True).strip()
            assert reconstructed == old_blob, ('bounded transition historical mismatch', name, reconstructed)
            expected[name] = oracle_path
        print('ENCORE_FC27_BOUNDED_GRAPHICS_TRANSITION_REVERSE_PASS')
    # A reviewed, startup-only vendor diagnostic may add seven tiny source
    # blocks. Check its EXACT raw Git blob and reverse ONLY those blocks
    # before the immutable R23/P24 and generated-Vulkan source oracles.
    # Never edit the pinned vendor source or normalize other Vulkan owners.
    native_cache_owner = 'vk_pipeline_cache_cost.cpp'
    cache_source = expected[native_cache_owner].read_text()
    # FC27: for modest title shader caches restore the LAST saved 32
    # accepted shaders, rather than the oldest 32. Verify the complete active
    # C++ blob and reverse only this hunk + include on the audit COPY.
    # Applicability is a source ABI, not the changing vendor gitlink:
    # the exact reviewed FC27 prewarm owner is provable at every newer pin.
    # Unknown blobs still fail the strict historical source validator below.
    if subprocess.check_output(
        ['git', 'hash-object', str(expected[native_cache_owner])], text=True
    ).strip() == 'cfac496d574010b8121611c8616d38bf7cdcbc41':
        assert subprocess.check_output(
            ['git', 'hash-object', str(expected[native_cache_owner])],
            text=True).strip() == 'cfac496d574010b8121611c8616d38bf7cdcbc41'
        current_preloader = "void PipelineCache::LoadDiskResources(u64 title_id, std::stop_token stop_loading,\n                                      const VideoCore::DiskResourceLoadCallback& callback) {\n    if (title_id == 0) {\n        return;\n    }\n    if (!pipeline_cache_filename.empty()) {\n        serialization_thread.WaitForRequests();\n        if (use_vulkan_pipeline_cache && !vulkan_pipeline_cache_filename.empty()) {\n            SerializeVulkanPipelineCache(vulkan_pipeline_cache_filename, vulkan_pipeline_cache,\n                                         CACHE_VERSION);\n        }\n    }\n\n    const auto shader_dir{Common::FS::GetEdenPath(Common::FS::EdenPath::ShaderDir)};\n    const auto base_dir{shader_dir / fmt::format(\"{:016x}\", title_id)};\n    if (!Common::FS::CreateDir(shader_dir) || !Common::FS::CreateDir(base_dir)) {\n        LOG_ERROR(Common_Filesystem, \"Failed to create pipeline cache directories\");\n        return;\n    }\n    pipeline_cache_filename = base_dir / \"vulkan.bin\";\n\n    if (use_vulkan_pipeline_cache) {\n        vulkan_pipeline_cache_filename = base_dir / \"vulkan_pipelines.bin\";\n        vulkan_pipeline_cache =\n            LoadVulkanPipelineCache(vulkan_pipeline_cache_filename, CACHE_VERSION);\n    }\n\n#ifdef PS5_NATIVE\n    // ENCORE_PS5_CACHE_DIAG_BEGIN\n    // Once per game load only: separate a missing per-title environment log,\n    // a header-only log, and an existing cache whose records get rejected.\n    // Never inspect or walk these files in the draw/submit hot path.\n    struct DiskCacheProbe {\n        bool present{};\n        std::uintmax_t bytes{};\n    };\n    const auto probe_cache = [](const std::filesystem::path& path) -> DiskCacheProbe {\n        std::error_code error;\n        const auto bytes = std::filesystem::file_size(path, error);\n        return {!error, error ? std::uintmax_t{} : bytes};\n    };\n    const auto env_before = probe_cache(pipeline_cache_filename);\n    const auto driver_before = use_vulkan_pipeline_cache\n                                   ? probe_cache(vulkan_pipeline_cache_filename)\n                                   : DiskCacheProbe{};\n    std::printf(\"EDEN_PS5_SHADER_CACHE_DISK title=%016llX stage=before\"\n                \" env_present=%u env_bytes=%llu driver_enabled=%u\"\n                \" driver_present=%u driver_bytes=%llu cache_version=%u\\n\",\n                static_cast<unsigned long long>(title_id),\n                unsigned(env_before.present),\n                static_cast<unsigned long long>(env_before.bytes),\n                unsigned(use_vulkan_pipeline_cache), unsigned(driver_before.present),\n                static_cast<unsigned long long>(driver_before.bytes),\n                unsigned(CACHE_VERSION));\n    // ENCORE_PS5_CACHE_DIAG_END\n    // The PS5 is launching one foreground game, so do not delay it by\n    // compiling the full backlog of shaders from earlier sessions.\n    // An already-stopped token is a special initialization-only request:\n    // after naming the per-title cache, leave workers RUNNING for later jobs.\n    if (stop_loading.stop_requested()) {\n        LOG_INFO(Render_Vulkan, \"PS5 lazy shader cache ready for {:016x}\", title_id);\n        return;\n    }\n#endif\n\n#ifdef PS5_NATIVE\n    // FC27: the old fixed 32-entry PREFIX admitted 18 compute and only\n    // 14 graphics shaders from a 28.7 MiB cache. Thousands of newer records\n    // were ignored and the GPU owner still translated 303 new graphics keys.\n    // Parse modest caches once and retain only the newest 32 valid builders;\n    // a large cache keeps the existing fast prefix cap to avoid startup I/O.\n    constexpr size_t kStartupPrewarmPipelines = 32;\n    constexpr std::uintmax_t kRecentShaderCacheScanLimit = 64ULL << 20;\n    const bool prefer_recent_cache =\n        env_before.present && env_before.bytes > 12 &&\n        env_before.bytes <= kRecentShaderCacheScanLimit;\n    std::deque<Common::UniqueFunction<void>> recent_cache_builds;\n    const auto startup_prewarm_started = std::chrono::steady_clock::now();\n    std::stop_source startup_reader;\n#endif\n    struct {\n        std::mutex mutex;\n        size_t total{};\n        size_t built{};\n        size_t valid{};\n        bool has_loaded{};\n        // ENCORE_PS5_CACHE_DIAG_BEGIN\n#ifdef PS5_NATIVE\n        // Updated only by the disk reader; the main thread reads after drain.\n        size_t disk_compute_records{};\n        size_t disk_graphics_records{};\n        size_t disk_graphics_admitted{};\n#endif\n        // ENCORE_PS5_CACHE_DIAG_END\n        std::unique_ptr<PipelineStatistics> statistics;\n    } state;\n\n    if (device.IsKhrPipelineExecutablePropertiesEnabled()) {\n        state.statistics = std::make_unique<PipelineStatistics>(device);\n    }\n    const auto schedule_prewarm = [&](Common::UniqueFunction<void> build) {\n#ifdef PS5_NATIVE\n        if (prefer_recent_cache) {\n            // No driver work while scanning the file. Move-only jobs own all\n            // shader environments and cannot outlive this loading function.\n            // Discard oldest unstarted work without creating GPU pipelines.\n            if (recent_cache_builds.size() == kStartupPrewarmPipelines)\n                recent_cache_builds.pop_front();\n            recent_cache_builds.emplace_back(std::move(build));\n            return;\n        }\n#endif\n        workers.QueueWork(std::move(build));\n        {\n            std::scoped_lock lock{state.mutex};\n            ++state.total;\n        }\n#ifdef PS5_NATIVE\n        if (state.total == kStartupPrewarmPipelines)\n            startup_reader.request_stop();\n#endif\n    };\n    const auto load_compute{[&](std::ifstream& file, FileEnvironment env) {\n        // ENCORE_PS5_CACHE_DIAG_BEGIN\n#ifdef PS5_NATIVE\n        ++state.disk_compute_records;\n#endif\n        // ENCORE_PS5_CACHE_DIAG_END\n        ComputePipelineCacheKey key;\n        file.read(reinterpret_cast<char*>(&key), sizeof(key));\n\n        schedule_prewarm([this, key, env_ = std::move(env), &state, &callback]() mutable {\n            ShaderPools pools;\n            auto pipeline{CreateComputePipeline(pools, key, env_, state.statistics.get(), false)};\n            std::scoped_lock lock{state.mutex};\n            // Do not seed a failed Vulkan compute pipeline for future dispatches.\n            if (pipeline && pipeline->IsBound()) {\n                compute_cache.emplace(key, std::move(pipeline));\n                ++state.valid;\n            }\n            ++state.built;\n            if (state.has_loaded) {\n                callback(VideoCore::LoadCallbackStage::Build, state.built, state.total);\n            }\n        });\n    }};\n    const auto load_graphics{[&](std::ifstream& file, std::vector<FileEnvironment> envs) {\n        // ENCORE_PS5_CACHE_DIAG_BEGIN\n#ifdef PS5_NATIVE\n        ++state.disk_graphics_records;\n#endif\n        // ENCORE_PS5_CACHE_DIAG_END\n        GraphicsPipelineCacheKey key;\n        file.read(reinterpret_cast<char*>(&key), sizeof(key));\n\n        if ((key.state.extended_dynamic_state != 0) !=\n                dynamic_features.has_extended_dynamic_state ||\n            (key.state.extended_dynamic_state_2 != 0) !=\n                dynamic_features.has_extended_dynamic_state_2 ||\n            (key.state.extended_dynamic_state_2_logic_op != 0) !=\n                dynamic_features.has_extended_dynamic_state_2_logic_op ||\n            (key.state.extended_dynamic_state_3_blend != 0) !=\n                dynamic_features.has_extended_dynamic_state_3_blend ||\n            (key.state.extended_dynamic_state_3_enables != 0) !=\n                dynamic_features.has_extended_dynamic_state_3_enables ||\n            (key.state.color_write_enable_dynamic != 0) !=\n                dynamic_features.has_color_write_enable ||\n            ((key.state.dynamic_vertex_input != 0) !=\n                 dynamic_features.has_dynamic_vertex_input &&\n             !(dynamic_features.has_dynamic_vertex_input &&\n               ::Eden::DevVulkan::static_vertex_input &&\n               EdenAttributelessStaticKey(key.state)))) {\n            return;\n        }\n\n        const bool key_requests_provoking_last = key.state.provoking_vertex_last != 0;\n        if (key_requests_provoking_last && !dynamic_features.has_provoking_vertex_last_mode) {\n            return;\n        }\n\n        const bool key_uses_transform_feedback = key.state.xfb_enabled != 0;\n        if (key_uses_transform_feedback && key_requests_provoking_last &&\n            !dynamic_features.has_provoking_vertex_tf_preserve) {\n            return;\n        }\n\n        schedule_prewarm([this, key, envs_ = std::move(envs), &state, &callback]() mutable {\n            ShaderPools pools;\n            boost::container::static_vector<Shader::Environment*, 5> env_ptrs;\n            for (auto& env : envs_) {\n                env_ptrs.push_back(&env);\n            }\n            auto pipeline{CreateGraphicsPipeline(pools, key, MakeSpan(env_ptrs),\n                                                 state.statistics.get(), false)};\n\n            std::scoped_lock lock{state.mutex};\n            // Leave a failed Vulkan build absent from the prewarm map,\n            // so the normal first-use path may try the key again.\n#ifdef PS5_NATIVE\n            if (pipeline && pipeline->CanExecuteDraw()) {\n#else\n            if (pipeline) {\n#endif\n                graphics_cache.emplace(key, std::move(pipeline));\n                ++state.valid;\n            }\n            ++state.built;\n            if (state.has_loaded) {\n                callback(VideoCore::LoadCallbackStage::Build, state.built, state.total);\n            }\n        });\n        // ENCORE_PS5_CACHE_DIAG_BEGIN\n#ifdef PS5_NATIVE\n        ++state.disk_graphics_admitted;\n#endif\n        // ENCORE_PS5_CACHE_DIAG_END\n    }};\n    // Only the reader observes the quota stop. Passing this token to\n    // workers.WaitForRequests() would permanently request_stop() on the\n    // shader-builder pool, breaking first-use shaders later in gameplay.\n#ifdef PS5_NATIVE\n    // Newest-entry mode must read to the last VALID record (also repairing\n    // a corrupt tail); large caches retain the old first-32 stop token.\n    const std::stop_token reader_token{\n        prefer_recent_cache ? stop_loading : startup_reader.get_token()};\n#else\n    const std::stop_token reader_token{stop_loading};\n#endif\n#ifdef PS5_NATIVE\n    // The progress callback below also runs before the normal drain and can\n    // throw. Keep locally borrowed prewarm state alive on EVERY exceptional\n    // exit, not only failures of the disk reader. No extra wait on success.\n    struct PrewarmDrain {\n        Common::ThreadWorker& compiler;\n        bool joined{};\n        ~PrewarmDrain() {\n            if (!joined) compiler.WaitForRequests();\n        }\n    } prewarm_drain{workers};\n#endif\n#ifdef PS5_NATIVE\n    // A damaged disk cache or an enqueue failure can interrupt the reader\n    // after jobs borrowed local state. Always reach the non-cancelling drain.\n    try {\n#endif\n        VideoCommon::LoadPipelines(reader_token, pipeline_cache_filename, CACHE_VERSION, load_compute,\n                                   load_graphics);\n#ifdef PS5_NATIVE\n        if (prefer_recent_cache && !stop_loading.stop_requested()) {\n            for (auto& build : recent_cache_builds) {\n                workers.QueueWork(std::move(build));\n                std::scoped_lock lock{state.mutex};\n                ++state.total;\n            }\n            recent_cache_builds.clear();\n        }\n    } catch (const std::exception& error) {\n        LOG_WARNING(Render_Vulkan, \"PS5 shader prewarm aborted: {}\", error.what());\n    } catch (...) {\n        LOG_WARNING(Render_Vulkan, \"PS5 shader prewarm aborted: unknown exception\");\n    }\n#endif\n\n    LOG_INFO(Render_Vulkan, \"Total Pipeline Count: {}\", state.total);\n\n    std::unique_lock lock{state.mutex};\n    callback(VideoCore::LoadCallbackStage::Build, 0, state.total);\n    state.has_loaded = true;\n    lock.unlock();\n\n#ifdef PS5_NATIVE\n    // A cancelled title-cache load must never stop the persistent shader\n    // compiler pool: StatefulThreadWorker::WaitForRequests(stop_token)\n    // requests stop on every worker when that token is cancelled.\n    // Only the disk reader observes cancellation. The bounded queued jobs\n    // must complete before their borrowed stack state can be destroyed.\n    workers.WaitForRequests();\n    prewarm_drain.joined = true;\n#else\n    workers.WaitForRequests(stop_loading);\n#endif\n#ifdef PS5_NATIVE\n    // Completed attempts include failed native handles; track valid results.\n    // One startup summary, never a per-frame or per-draw instrumentation cost.\n    const auto startup_prewarm_ms = std::chrono::duration_cast<std::chrono::milliseconds>(\n        std::chrono::steady_clock::now() - startup_prewarm_started).count();\n    std::printf(\"EDEN_PS5_SHADER_PREWARM queued=%zu completed=%zu valid=%zu rejected=%zu prebuild_ms=%lld limit=%zu\\n\",\n                state.total, state.built, state.valid, state.built - state.valid,\n                static_cast<long long>(startup_prewarm_ms), kStartupPrewarmPipelines);\n    // ENCORE_PS5_CACHE_DIAG_BEGIN\n    const auto env_after = probe_cache(pipeline_cache_filename);\n    std::printf(\"EDEN_PS5_SHADER_CACHE_ADMISSION title=%016llX\"\n                \" env_before_present=%u env_before_bytes=%llu\"\n                \" env_after_present=%u env_after_bytes=%llu\"\n                \" compute_records=%zu graphics_records=%zu graphics_filtered=%zu\"\n                \" queued=%zu cache_version=%u\\n\",\n                static_cast<unsigned long long>(title_id),\n                unsigned(env_before.present),\n                static_cast<unsigned long long>(env_before.bytes),\n                unsigned(env_after.present),\n                static_cast<unsigned long long>(env_after.bytes),\n                state.disk_compute_records, state.disk_graphics_records,\n                state.disk_graphics_records - state.disk_graphics_admitted,\n                state.total, unsigned(CACHE_VERSION));\n    // ENCORE_PS5_CACHE_DIAG_END\n#endif\n\n    if (use_vulkan_pipeline_cache) {\n        SerializeVulkanPipelineCache(vulkan_pipeline_cache_filename, vulkan_pipeline_cache,\n                                     CACHE_VERSION);\n        size_t size = 0;\n        vulkan_pipeline_cache.Read(&size, nullptr);\n        last_cache_size.store(size, std::memory_order_relaxed);\n        last_flush = std::chrono::steady_clock::now();\n    }\n\n    if (state.statistics) {\n        state.statistics->Report();\n    }\n}\n"
        previous_preloader = "void PipelineCache::LoadDiskResources(u64 title_id, std::stop_token stop_loading,\n                                      const VideoCore::DiskResourceLoadCallback& callback) {\n    if (title_id == 0) {\n        return;\n    }\n    if (!pipeline_cache_filename.empty()) {\n        serialization_thread.WaitForRequests();\n        if (use_vulkan_pipeline_cache && !vulkan_pipeline_cache_filename.empty()) {\n            SerializeVulkanPipelineCache(vulkan_pipeline_cache_filename, vulkan_pipeline_cache,\n                                         CACHE_VERSION);\n        }\n    }\n\n    const auto shader_dir{Common::FS::GetEdenPath(Common::FS::EdenPath::ShaderDir)};\n    const auto base_dir{shader_dir / fmt::format(\"{:016x}\", title_id)};\n    if (!Common::FS::CreateDir(shader_dir) || !Common::FS::CreateDir(base_dir)) {\n        LOG_ERROR(Common_Filesystem, \"Failed to create pipeline cache directories\");\n        return;\n    }\n    pipeline_cache_filename = base_dir / \"vulkan.bin\";\n\n    if (use_vulkan_pipeline_cache) {\n        vulkan_pipeline_cache_filename = base_dir / \"vulkan_pipelines.bin\";\n        vulkan_pipeline_cache =\n            LoadVulkanPipelineCache(vulkan_pipeline_cache_filename, CACHE_VERSION);\n    }\n\n#ifdef PS5_NATIVE\n    // ENCORE_PS5_CACHE_DIAG_BEGIN\n    // Once per game load only: separate a missing per-title environment log,\n    // a header-only log, and an existing cache whose records get rejected.\n    // Never inspect or walk these files in the draw/submit hot path.\n    struct DiskCacheProbe {\n        bool present{};\n        std::uintmax_t bytes{};\n    };\n    const auto probe_cache = [](const std::filesystem::path& path) -> DiskCacheProbe {\n        std::error_code error;\n        const auto bytes = std::filesystem::file_size(path, error);\n        return {!error, error ? std::uintmax_t{} : bytes};\n    };\n    const auto env_before = probe_cache(pipeline_cache_filename);\n    const auto driver_before = use_vulkan_pipeline_cache\n                                   ? probe_cache(vulkan_pipeline_cache_filename)\n                                   : DiskCacheProbe{};\n    std::printf(\"EDEN_PS5_SHADER_CACHE_DISK title=%016llX stage=before\"\n                \" env_present=%u env_bytes=%llu driver_enabled=%u\"\n                \" driver_present=%u driver_bytes=%llu cache_version=%u\\n\",\n                static_cast<unsigned long long>(title_id),\n                unsigned(env_before.present),\n                static_cast<unsigned long long>(env_before.bytes),\n                unsigned(use_vulkan_pipeline_cache), unsigned(driver_before.present),\n                static_cast<unsigned long long>(driver_before.bytes),\n                unsigned(CACHE_VERSION));\n    // ENCORE_PS5_CACHE_DIAG_END\n    // The PS5 is launching one foreground game, so do not delay it by\n    // compiling the full backlog of shaders from earlier sessions.\n    // An already-stopped token is a special initialization-only request:\n    // after naming the per-title cache, leave workers RUNNING for later jobs.\n    if (stop_loading.stop_requested()) {\n        LOG_INFO(Render_Vulkan, \"PS5 lazy shader cache ready for {:016x}\", title_id);\n        return;\n    }\n#endif\n\n#ifdef PS5_NATIVE\n    // Restore a bounded prefix of a title's saved pipelines before gameplay.\n    // Games with fewer cached entries load only those entries. This policy\n    // applies to every title (NS1 and NS2) without any title ID exceptions.\n    // Keep the worker queue, draw order and GPU fences unchanged.\n    constexpr size_t kStartupPrewarmPipelines = 32;\n    const auto startup_prewarm_started = std::chrono::steady_clock::now();\n    std::stop_source startup_reader;\n#endif\n    struct {\n        std::mutex mutex;\n        size_t total{};\n        size_t built{};\n        size_t valid{};\n        bool has_loaded{};\n        // ENCORE_PS5_CACHE_DIAG_BEGIN\n#ifdef PS5_NATIVE\n        // Updated only by the disk reader; the main thread reads after drain.\n        size_t disk_compute_records{};\n        size_t disk_graphics_records{};\n        size_t disk_graphics_admitted{};\n#endif\n        // ENCORE_PS5_CACHE_DIAG_END\n        std::unique_ptr<PipelineStatistics> statistics;\n    } state;\n\n    if (device.IsKhrPipelineExecutablePropertiesEnabled()) {\n        state.statistics = std::make_unique<PipelineStatistics>(device);\n    }\n    const auto load_compute{[&](std::ifstream& file, FileEnvironment env) {\n        // ENCORE_PS5_CACHE_DIAG_BEGIN\n#ifdef PS5_NATIVE\n        ++state.disk_compute_records;\n#endif\n        // ENCORE_PS5_CACHE_DIAG_END\n        ComputePipelineCacheKey key;\n        file.read(reinterpret_cast<char*>(&key), sizeof(key));\n\n        workers.QueueWork([this, key, env_ = std::move(env), &state, &callback]() mutable {\n            ShaderPools pools;\n            auto pipeline{CreateComputePipeline(pools, key, env_, state.statistics.get(), false)};\n            std::scoped_lock lock{state.mutex};\n            // Do not seed a failed Vulkan compute pipeline for future dispatches.\n            if (pipeline && pipeline->IsBound()) {\n                compute_cache.emplace(key, std::move(pipeline));\n                ++state.valid;\n            }\n            ++state.built;\n            if (state.has_loaded) {\n                callback(VideoCore::LoadCallbackStage::Build, state.built, state.total);\n            }\n        });\n        // Workers read total while holding state.mutex. Publish reader\n        // increments under the same lock to avoid a cache-prewarm data race.\n        {\n            std::scoped_lock count_lock{state.mutex};\n            ++state.total;\n        }\n#ifdef PS5_NATIVE\n        if (state.total == kStartupPrewarmPipelines)\n            startup_reader.request_stop();\n#endif\n    }};\n    const auto load_graphics{[&](std::ifstream& file, std::vector<FileEnvironment> envs) {\n        // ENCORE_PS5_CACHE_DIAG_BEGIN\n#ifdef PS5_NATIVE\n        ++state.disk_graphics_records;\n#endif\n        // ENCORE_PS5_CACHE_DIAG_END\n        GraphicsPipelineCacheKey key;\n        file.read(reinterpret_cast<char*>(&key), sizeof(key));\n\n        if ((key.state.extended_dynamic_state != 0) !=\n                dynamic_features.has_extended_dynamic_state ||\n            (key.state.extended_dynamic_state_2 != 0) !=\n                dynamic_features.has_extended_dynamic_state_2 ||\n            (key.state.extended_dynamic_state_2_logic_op != 0) !=\n                dynamic_features.has_extended_dynamic_state_2_logic_op ||\n            (key.state.extended_dynamic_state_3_blend != 0) !=\n                dynamic_features.has_extended_dynamic_state_3_blend ||\n            (key.state.extended_dynamic_state_3_enables != 0) !=\n                dynamic_features.has_extended_dynamic_state_3_enables ||\n            (key.state.color_write_enable_dynamic != 0) !=\n                dynamic_features.has_color_write_enable ||\n            ((key.state.dynamic_vertex_input != 0) !=\n                 dynamic_features.has_dynamic_vertex_input &&\n             !(dynamic_features.has_dynamic_vertex_input &&\n               ::Eden::DevVulkan::static_vertex_input &&\n               EdenAttributelessStaticKey(key.state)))) {\n            return;\n        }\n\n        const bool key_requests_provoking_last = key.state.provoking_vertex_last != 0;\n        if (key_requests_provoking_last && !dynamic_features.has_provoking_vertex_last_mode) {\n            return;\n        }\n\n        const bool key_uses_transform_feedback = key.state.xfb_enabled != 0;\n        if (key_uses_transform_feedback && key_requests_provoking_last &&\n            !dynamic_features.has_provoking_vertex_tf_preserve) {\n            return;\n        }\n\n        workers.QueueWork([this, key, envs_ = std::move(envs), &state, &callback]() mutable {\n            ShaderPools pools;\n            boost::container::static_vector<Shader::Environment*, 5> env_ptrs;\n            for (auto& env : envs_) {\n                env_ptrs.push_back(&env);\n            }\n            auto pipeline{CreateGraphicsPipeline(pools, key, MakeSpan(env_ptrs),\n                                                 state.statistics.get(), false)};\n\n            std::scoped_lock lock{state.mutex};\n            // Leave a failed Vulkan build absent from the prewarm map,\n            // so the normal first-use path may try the key again.\n#ifdef PS5_NATIVE\n            if (pipeline && pipeline->CanExecuteDraw()) {\n#else\n            if (pipeline) {\n#endif\n                graphics_cache.emplace(key, std::move(pipeline));\n                ++state.valid;\n            }\n            ++state.built;\n            if (state.has_loaded) {\n                callback(VideoCore::LoadCallbackStage::Build, state.built, state.total);\n            }\n        });\n        // ENCORE_PS5_CACHE_DIAG_BEGIN\n#ifdef PS5_NATIVE\n        ++state.disk_graphics_admitted;\n#endif\n        // ENCORE_PS5_CACHE_DIAG_END\n        // Workers read total while holding state.mutex. Publish reader\n        // increments under the same lock to avoid a cache-prewarm data race.\n        {\n            std::scoped_lock count_lock{state.mutex};\n            ++state.total;\n        }\n#ifdef PS5_NATIVE\n        if (state.total == kStartupPrewarmPipelines)\n            startup_reader.request_stop();\n#endif\n    }};\n    // Only the reader observes the quota stop. Passing this token to\n    // workers.WaitForRequests() would permanently request_stop() on the\n    // shader-builder pool, breaking first-use shaders later in gameplay.\n#ifdef PS5_NATIVE\n    const std::stop_token reader_token{startup_reader.get_token()};\n#else\n    const std::stop_token reader_token{stop_loading};\n#endif\n#ifdef PS5_NATIVE\n    // The progress callback below also runs before the normal drain and can\n    // throw. Keep locally borrowed prewarm state alive on EVERY exceptional\n    // exit, not only failures of the disk reader. No extra wait on success.\n    struct PrewarmDrain {\n        Common::ThreadWorker& compiler;\n        bool joined{};\n        ~PrewarmDrain() {\n            if (!joined) compiler.WaitForRequests();\n        }\n    } prewarm_drain{workers};\n#endif\n#ifdef PS5_NATIVE\n    // A damaged disk cache or an enqueue failure can interrupt the reader\n    // after jobs borrowed local state. Always reach the non-cancelling drain.\n    try {\n#endif\n        VideoCommon::LoadPipelines(reader_token, pipeline_cache_filename, CACHE_VERSION, load_compute,\n                                   load_graphics);\n#ifdef PS5_NATIVE\n    } catch (const std::exception& error) {\n        LOG_WARNING(Render_Vulkan, \"PS5 shader prewarm aborted: {}\", error.what());\n    } catch (...) {\n        LOG_WARNING(Render_Vulkan, \"PS5 shader prewarm aborted: unknown exception\");\n    }\n#endif\n\n    LOG_INFO(Render_Vulkan, \"Total Pipeline Count: {}\", state.total);\n\n    std::unique_lock lock{state.mutex};\n    callback(VideoCore::LoadCallbackStage::Build, 0, state.total);\n    state.has_loaded = true;\n    lock.unlock();\n\n#ifdef PS5_NATIVE\n    // A cancelled title-cache load must never stop the persistent shader\n    // compiler pool: StatefulThreadWorker::WaitForRequests(stop_token)\n    // requests stop on every worker when that token is cancelled.\n    // Only the disk reader observes cancellation. The bounded queued jobs\n    // must complete before their borrowed stack state can be destroyed.\n    workers.WaitForRequests();\n    prewarm_drain.joined = true;\n#else\n    workers.WaitForRequests(stop_loading);\n#endif\n#ifdef PS5_NATIVE\n    // Completed attempts include failed native handles; track valid results.\n    // One startup summary, never a per-frame or per-draw instrumentation cost.\n    const auto startup_prewarm_ms = std::chrono::duration_cast<std::chrono::milliseconds>(\n        std::chrono::steady_clock::now() - startup_prewarm_started).count();\n    std::printf(\"EDEN_PS5_SHADER_PREWARM queued=%zu completed=%zu valid=%zu rejected=%zu prebuild_ms=%lld limit=%zu\\n\",\n                state.total, state.built, state.valid, state.built - state.valid,\n                static_cast<long long>(startup_prewarm_ms), kStartupPrewarmPipelines);\n    // ENCORE_PS5_CACHE_DIAG_BEGIN\n    const auto env_after = probe_cache(pipeline_cache_filename);\n    std::printf(\"EDEN_PS5_SHADER_CACHE_ADMISSION title=%016llX\"\n                \" env_before_present=%u env_before_bytes=%llu\"\n                \" env_after_present=%u env_after_bytes=%llu\"\n                \" compute_records=%zu graphics_records=%zu graphics_filtered=%zu\"\n                \" queued=%zu cache_version=%u\\n\",\n                static_cast<unsigned long long>(title_id),\n                unsigned(env_before.present),\n                static_cast<unsigned long long>(env_before.bytes),\n                unsigned(env_after.present),\n                static_cast<unsigned long long>(env_after.bytes),\n                state.disk_compute_records, state.disk_graphics_records,\n                state.disk_graphics_records - state.disk_graphics_admitted,\n                state.total, unsigned(CACHE_VERSION));\n    // ENCORE_PS5_CACHE_DIAG_END\n#endif\n\n    if (use_vulkan_pipeline_cache) {\n        SerializeVulkanPipelineCache(vulkan_pipeline_cache_filename, vulkan_pipeline_cache,\n                                     CACHE_VERSION);\n        size_t size = 0;\n        vulkan_pipeline_cache.Read(&size, nullptr);\n        last_cache_size.store(size, std::memory_order_relaxed);\n        last_flush = std::chrono::steady_clock::now();\n    }\n\n    if (state.statistics) {\n        state.statistics->Report();\n    }\n}\n"
        assert cache_source.count(current_preloader) == 1
        cache_source = cache_source.replace(current_preloader, previous_preloader, 1)
        assert cache_source.count('#include <deque>\n') == 1
        cache_source = cache_source.replace('#include <deque>\n', '', 1)
        restored_file = temp/'fc27-recent-shader-prewarm-historical'/native_cache_owner
        restored_file.parent.mkdir(parents=True, exist_ok=True)
        restored_file.write_text(cache_source)
        assert subprocess.check_output(
            ['git', 'hash-object', str(restored_file)], text=True
        ).strip() == 'e3910d11f33376097a90858118ba276f7e02cb70'
        expected[native_cache_owner] = restored_file
        print('ENCORE_FC27_RECENT_SHADER_PREWARM_EXACT_REVERSE_PASS')
    cache_historic, cache_has_diag = normalize_for_historical_proof(cache_source)
    if cache_has_diag:
        cache_historic_file = temp/'normalized-vendor-ps5-cache-diagnostics'/native_cache_owner
        cache_historic_file.parent.mkdir(parents=True, exist_ok=True)
        cache_historic_file.write_text(cache_historic)
        expected[native_cache_owner] = cache_historic_file
    print("ENCORE_PS5_SHADER_CACHE_SOURCE_RECEIPT_PASS",
          "diagnostics=" + str(int(cache_has_diag)),
          "R23_original_blob_preserved=1")
    # R457: verify the exact production handle-owner repair before historic
    # R23/P24 reversal. This normalizes only the audit copy, never vendor.
    raster_owner = 'vulkan_rasterizer.cpp'
    raster_source = expected[raster_owner].read_text()
    def raster_blob(text):
        data = text.encode('utf-8')
        return hashlib.sha1(b'blob ' + str(len(data)).encode() + bytes([0]) + data).hexdigest()
    raster_sha = raster_blob(raster_source)
    exact_vendor_pin = subprocess.check_output(
        ['git', '-C', str(root / 'vendor'), 'rev-parse', 'HEAD'], text=True).strip()
    actual_vendor_pin = exact_vendor_pin
    if exact_vendor_pin in {"ac880cd408116e6eb53ba2400abc52970b81f539", "95343060f948601930f2e62b919da0789f0830bb", "12ab9a8411f5c9df1b5cc73f01c923ad9479c8af", "224b05e6f8b1a266b0d55d1ded5332f7a2eaed7c", "150a3a79ca103061f73a9a50ca8f463a3b4712f3", "fcd62408fdbc33af01a4caebc8fd44c8500b628f", "b6b9e98e0dd16c4702f21f2e0b5e322126abeecb", "dbef23055897b1649f83c20cf7a0516e64f3d5cd", "dc526f06d277dfa0a4afa48b4cf8b3153ebe7267", "87964d15e91b6b6523c88682e5ca017f6e1a808b", "ae6f59a9865a3f4f178c4d836a3e04c93cceb69a", "f5c80c900b58b57808f609b5ffdc0e6ab9de7bd0", "d22b7066410c627230f9bfa8b3b5be8baff4fcdf", "f4f5d53596879960b19a3701bbd2272ef1f3c634"}:
        # Merge commit retains precisely the source tree of the reviewed
        # GuestCacheLock predecessor; historical rollback uses its receipts.
        reviewed_tree = subprocess.check_output(
            ['git', '-C', str(root / 'vendor'), 'rev-parse', 'HEAD^{tree}'],
            text=True).strip()
        assert reviewed_tree == {
            'ac880cd408116e6eb53ba2400abc52970b81f539': '01c09ec124779e7d976718af09a0e5e94cb4ac20',
            '95343060f948601930f2e62b919da0789f0830bb': 'efa6548c57f7823d4e8b2c975944c6846b765ff3',
            '12ab9a8411f5c9df1b5cc73f01c923ad9479c8af': '64179fcce4962f9b2b7c738504a6fa0e00b2b292',
            '224b05e6f8b1a266b0d55d1ded5332f7a2eaed7c': '3f7f1523cef730ad153bf658fbb3567222d6e956',
            '150a3a79ca103061f73a9a50ca8f463a3b4712f3': '39fb9a3efe65f67115dfcdebe39a55334a702f2d',
            'fcd62408fdbc33af01a4caebc8fd44c8500b628f': '8447712e2cecf661910fd1a32613f0b844ceaeb0',
            'b6b9e98e0dd16c4702f21f2e0b5e322126abeecb': '067c72d30a71a79faefd1ad14876e2a46f02755c',
            'dbef23055897b1649f83c20cf7a0516e64f3d5cd': '9e28e5b83cf9c0f4086a33d6838904353a8fd541',
            'dc526f06d277dfa0a4afa48b4cf8b3153ebe7267': 'e21b2c70c00c50fc7d682150cb62e87fe856306c',
            '87964d15e91b6b6523c88682e5ca017f6e1a808b': 'c1cbb8a3ca0b7231e260fdb5e9f6a1c7964097ab',
            'ae6f59a9865a3f4f178c4d836a3e04c93cceb69a': 'e125210acec0eaef51c6c038d200cc9c12981ace',
            'f5c80c900b58b57808f609b5ffdc0e6ab9de7bd0': '68acadcd14d23135fd02df0a0e508c668917168c',
            'd22b7066410c627230f9bfa8b3b5be8baff4fcdf': '805d74f7ccf0ddf060782615d2bd94bb8d26b412',
            'f4f5d53596879960b19a3701bbd2272ef1f3c634': 'e1e3fa4878d6203a51c7aa6ec93e09f81a175cdf',
        }[exact_vendor_pin], ('Vendor reviewed source tree drift', exact_vendor_pin, reviewed_tree)
        if exact_vendor_pin in {'dc526f06d277dfa0a4afa48b4cf8b3153ebe7267', '87964d15e91b6b6523c88682e5ca017f6e1a808b', 'ae6f59a9865a3f4f178c4d836a3e04c93cceb69a', 'f5c80c900b58b57808f609b5ffdc0e6ab9de7bd0', 'd22b7066410c627230f9bfa8b3b5be8baff4fcdf', 'f4f5d53596879960b19a3701bbd2272ef1f3c634'}:
            for relative, expected_sha in {
                'encore-active/ns2-runtime/self_controller/core/hle/service/am/service/self_controller.cpp':
                    ('01d0f8a05faaa30b01a1802680a954aebfbf118b' if exact_vendor_pin in {'f5c80c900b58b57808f609b5ffdc0e6ab9de7bd0', 'd22b7066410c627230f9bfa8b3b5be8baff4fcdf', 'f4f5d53596879960b19a3701bbd2272ef1f3c634'} else '7783c917d8b2f2e8d26c091d5507964fcf9d44dd' if exact_vendor_pin == 'ae6f59a9865a3f4f178c4d836a3e04c93cceb69a' else '743bd9c9a4b9a3550c853ffa8fc06898c01618ff'),
                'tests/r23_fw23_selfcontroller_240.py':
                    ('367b99a467a7cf1559973af65c69f7c2231764f4' if exact_vendor_pin in {'f5c80c900b58b57808f609b5ffdc0e6ab9de7bd0', 'd22b7066410c627230f9bfa8b3b5be8baff4fcdf', 'f4f5d53596879960b19a3701bbd2272ef1f3c634'} else 'ed80a6d62d5328c394a133b5f28112443e893f36' if exact_vendor_pin == 'ae6f59a9865a3f4f178c4d836a3e04c93cceb69a' else 'b03d2015ac00a0ce2e52bea002c931b330a55d96'),
            }.items():
                raw = (root / 'vendor' / relative).read_bytes()
                digest = hashlib.sha1(b'blob ' + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
                assert digest == expected_sha, ('NS2 SelfController 2400 successor drift', relative)
        if exact_vendor_pin in {'87964d15e91b6b6523c88682e5ca017f6e1a808b', 'ae6f59a9865a3f4f178c4d836a3e04c93cceb69a', 'f5c80c900b58b57808f609b5ffdc0e6ab9de7bd0', 'd22b7066410c627230f9bfa8b3b5be8baff4fcdf', 'f4f5d53596879960b19a3701bbd2272ef1f3c634'}:
            for relative, expected_sha in {
                    "encore-active/eden-core/src/core/hle/service/service.cpp": ('e388765fb2cf372adc01c2c3ec174955659ccc2a' if exact_vendor_pin in {'f5c80c900b58b57808f609b5ffdc0e6ab9de7bd0', 'd22b7066410c627230f9bfa8b3b5be8baff4fcdf', 'f4f5d53596879960b19a3701bbd2272ef1f3c634'} else "e2d52974d419b9ed4089da8baed104dd1dbd282d"),
                    "encore-active/ns2-runtime/process/core/core.cpp": "a2721a630b8b32222ff586ea2db19ee726d4d5b9",
                    "tests/ns1_r23_54_storage_pacing.py": ('eb88e3701448c3b3572155a00158b3a5955eb45e' if exact_vendor_pin in {'f5c80c900b58b57808f609b5ffdc0e6ab9de7bd0', 'd22b7066410c627230f9bfa8b3b5be8baff4fcdf', 'f4f5d53596879960b19a3701bbd2272ef1f3c634'} else "9abec8ca14bfaaed76128fab34592f0b3911afe9"),
                    "tests/shutdown_general_channel_lifetime_source.py": "4bb0ef388211b1c9110afce55ef80983e5050782",
                    "tests/shutdown_teardown_lifetime_source.py": "e40deaae0b1f3aab6a5a12f7978be470b3ee0463"
            }.items():
                raw = (root / 'vendor' / relative).read_bytes()
                digest = hashlib.sha1(b'blob ' + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
                assert digest == expected_sha, ('NS2 NUP/IPC source drift', relative, digest)
        if exact_vendor_pin == 'ae6f59a9865a3f4f178c4d836a3e04c93cceb69a':
            raw = (root/'vendor/encore-active/ns2-runtime/self_controller/core/hle/service/am/service/self_controller.h').read_bytes()
            assert hashlib.sha1(b'blob '+str(len(raw)).encode()+bytes([0])+raw).hexdigest() == '571793025a886f3878e7b61ec9569faba84647f2'
        if exact_vendor_pin == 'f5c80c900b58b57808f609b5ffdc0e6ab9de7bd0':
            for relative, qualified_blob in {
                "encore-active/eden-core/include/core/hle/service/service.h": "b871694b3b865465ec8e08e358d6799449092498",
                "encore-active/eden-core/src/core/hle/service/service.cpp": "e388765fb2cf372adc01c2c3ec174955659ccc2a",
                "encore-active/ns2-runtime/am/core/hle/service/am/service/application_functions.cpp": "a26850d9addcd35c483fa1da28d440537896ee13",
                "encore-active/ns2-runtime/hle/core/hle/service/am/service/application_proxy.cpp": "92de53cfc78a028c7fd8ccd57ec73b0b81ab0912",
                "encore-active/ns2-runtime/hle/core/hle/service/am/service/application_proxy.h": "ed88acba848071d6c9e2c0b080c3234925003b50",
                "encore-active/ns2-runtime/hle/core/hle/service/am/service/application_proxy_service.cpp": "0d2ed417d23f11a97f91cf18e733fad6515d0756",
                "encore-active/ns2-runtime/hle/core/hle/service/nx2_stub_interface.h": "68c087899680b8a3a764d6cd3c362b0e98237ae0",
                "encore-active/ns2-runtime/self_controller/core/hle/service/am/service/self_controller.cpp": "01d0f8a05faaa30b01a1802680a954aebfbf118b",
                "tests/ns1_r23_126_uuid_sha1.py": "4a565a3c5fd53dff3ca157aa0793fb86f7827791",
                "tests/ns1_r23_54_storage_pacing.py": "eb88e3701448c3b3572155a00158b3a5955eb45e",
                "tests/r23_fw23_selfcontroller_240.py": "367b99a467a7cf1559973af65c69f7c2231764f4",
            }.items():
                raw = (root/'vendor'/relative).read_bytes()
                digest = hashlib.sha1(b'blob '+str(len(raw)).encode()+bytes([0])+raw).hexdigest()
                assert digest == qualified_blob, ('Lichii structural source drift',relative,digest)
        if exact_vendor_pin in {'d22b7066410c627230f9bfa8b3b5be8baff4fcdf', 'f4f5d53596879960b19a3701bbd2272ef1f3c634'}:
            for relative, expected_blob in {
                "encore-active/ns2-runtime/am_structure/core/hle/service/am/service/application_accessor.cpp": "25e75933c344a75f108ff1c7f40845feb405c5fd",
                "encore-active/ns2-runtime/am_structure/core/hle/service/am/service/application_accessor.h": "48ec3effbf4af4df285dc98fbd6c5cf7a3ada21a",
                "encore-active/ns2-runtime/am_structure/core/hle/service/am/service/audio_controller.cpp": "0b9efbe1cfdb3072828709170bbefa202114d08d",
                "encore-active/ns2-runtime/am_structure/core/hle/service/am/service/common_state_getter.cpp": "2c5e5364146b125c038b239056bf06f2aaea5ef3",
                "encore-active/ns2-runtime/am_structure/core/hle/service/am/service/display_controller.cpp": "7e7db23708718f6513b784c489edf61d8d555fac",
                "encore-active/ns2-runtime/am_structure/core/hle/service/am/service/library_applet_accessor.cpp": "7119c605968dd50372d5d62097bb2f9d017ab6e6",
                "encore-active/ns2-runtime/am_structure/core/hle/service/am/service/library_applet_creator.cpp": "1157033948e6a6f015ef14dedda30a40ff750b54",
                "encore-active/ns2-runtime/am_structure/core/hle/service/am/service/window_controller.cpp": "6b19368d91035f6372cf8540c4b45caf371c1cd3",
            }.items():
                raw = (root/'vendor'/relative).read_bytes()
                digest = hashlib.sha1(b'blob '+str(len(raw)).encode()+bytes([0])+raw).hexdigest()
                assert digest == expected_blob, ('NS2 Lichii AM source drift',relative,digest)
        if actual_vendor_pin == 'f4f5d53596879960b19a3701bbd2272ef1f3c634':
            for relative, expected_blob in {
                "encore-active/eden-core/src/core/file_sys/card_image.cpp": "5d5e6b40099b18768dadd39ba839881989e7ff6f",
                "encore-active/eden-core/src/core/file_sys/content_archive.cpp": "d31f75bf354f3ce5af1ac2f1ac170586503b1877",
                "encore-active/eden-core/src/core/file_sys/fssystem/fssystem_nca_reader.cpp": "49841fbbde5bd086f23aba601c80b19176ed8ae4",
                "encore-active/eden-core/src/core/loader/loader.cpp": "0b4448bcf4bef93b9d2a54cf96256d5b81d9424e",
            }.items():
                raw = (root / 'vendor' / relative).read_bytes()
                digest = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
                assert digest == expected_blob, ("DNSP/DXCI exact source drift", relative, digest)
        exact_vendor_pin = '17253dc91e9fe1eb2d9980f261f59d227bfcd1a1'
        actual_vendor_pin = exact_vendor_pin
    # GPU-30 is compiled from this pinned C++ owner, but the frozen R23/P24
    # receipts predate its segmented-GMMU inline DMA guard. Verify the complete
    # native blob and reverse only this one block on the historical audit copy.
    if raster_sha == 'fdd5a73ccf795fd58100469c546b544a86a68e5b':
        reviewed = "#ifdef PS5_NATIVE\n    // One GPU VA range can cross discontiguous device-memory pages. InlineMemory,\n    // texture invalidation and shader/query invalidation accept ONE CPU span:\n    // their first translated DAddr must never stand in for later GMMU pages.\n    // Single device-page writes keep the existing O(1) hot path. For fragmented\n    // but fully mapped spans, WriteBlock invalidates EACH translated physical\n    // segment before writing; it owns the same normal cache notifications.\n    if (!gpu_memory->IsGranularRange(address, copy_size) &&\n        !gpu_memory->IsContinuousRange(address, copy_size)) {\n        if (!gpu_memory->IsFullyMappedRange(address, copy_size)) {\n            return; // No partial writes into an invalid guest DMA mapping.\n        }\n        gpu_memory->WriteBlock(address, memory.data(), copy_size);\n        return;\n    }\n#endif\n"
        assert raster_source.count(reviewed) == 1, 'GPU-30 inline DMA owner changed'
        raster_source = raster_source.replace(reviewed, '', 1)
        raster_sha = raster_blob(raster_source)
        assert raster_sha == '771e922890142b1f0d39f935bbf0be1a478e0f9e', 'GPU-30 predecessor not exact'
        snapshot = temp/'ns1-gpu30-inline-dma-audit'/raster_owner
        snapshot.parent.mkdir(parents=True, exist_ok=True)
        snapshot.write_text(raster_source)
        expected[raster_owner] = snapshot
        print('ENCORE_NS1_GPU30_EXACT_REVERSE_PASS')
    # GPU-22: keep the current-channel GMMU contiguous buffer-image DMA fix
    # compiled; reverse only its complete, exact source delta for historical
    # Vulkan/R23 byte proofs. The predecessor is independently pinned.
    if raster_sha == '771e922890142b1f0d39f935bbf0be1a478e0f9e':
        native = "      accelerate_dma(buffer_cache, texture_cache, scheduler, gpu_memory),\n"
        historical = "      accelerate_dma(buffer_cache, texture_cache, scheduler),\n"
        assert raster_source.count(native) == 1, 'GPU-22 rasterizer receipt drift'
        raster_source = raster_source.replace(native, historical, 1)
        native = "AccelerateDMA::AccelerateDMA(BufferCache& buffer_cache_, TextureCache& texture_cache_,\n                             Scheduler& scheduler_, Tegra::MemoryManager* const& gpu_memory_)\n    : buffer_cache{buffer_cache_}, texture_cache{texture_cache_}, scheduler{scheduler_},\n      gpu_memory{gpu_memory_} {}\n"
        historical = "AccelerateDMA::AccelerateDMA(BufferCache& buffer_cache_, TextureCache& texture_cache_,\n                             Scheduler& scheduler_)\n    : buffer_cache{buffer_cache_}, texture_cache{texture_cache_}, scheduler{scheduler_} {}\n"
        assert raster_source.count(native) == 1, 'GPU-22 rasterizer receipt drift'
        raster_source = raster_source.replace(native, historical, 1)
        native = "#ifdef PS5_NATIVE\n    // ObtainBuffer translates only the first GPU VA into one CPU interval.\n    // A buffer spanning noncontiguous GMMU pages would upload/download\n    // unrelated physical memory. The normal MaxwellDMA CPU fallback\n    // supports a page-aware transfer for both image-copy directions.\n    // Test the channel currently bound to this rasterizer; no stale GMMU.\n    if (!gpu_memory ||\n        (!gpu_memory->IsGranularRange(buffer_operand.address, checked_bytes) &&\n         !gpu_memory->IsContinuousRange(buffer_operand.address, checked_bytes))) {\n        return false;\n    }\n#endif\n"
        historical = ""
        assert raster_source.count(native) == 1, 'GPU-22 rasterizer receipt drift'
        raster_source = raster_source.replace(native, historical, 1)
        raster_sha = raster_blob(raster_source)
        assert raster_sha == '71d097b9a83028dfad9370792c905bb3bfccfd5a', raster_sha
        snapshot = temp/'ns1-gpu22-gmmu-rasterizer-audit'/raster_owner
        snapshot.parent.mkdir(parents=True, exist_ok=True)
        snapshot.write_text(raster_source)
        expected[raster_owner] = snapshot
        print('ENCORE_NS1_GPU22_EXACT_REVERSE_PASS')
    # Share one GPU budget sample between native TextureCache and BufferCache.
    # Reverse the exact reviewed TickFrame only on the historical audit copy.
    # Reverse this exact shipping TickFrame on the historical audit copy.
    # Gate on the complete, SHA-sealed rasterizer C++ owner, not the moving
    # vendor commit ID: B0B5/NS1 and NS2-only vendor successors do not edit it.
    # Unrecognized rasterizer bytes still fail the frozen oracle below.
    if raster_sha == '71d097b9a83028dfad9370792c905bb3bfccfd5a':
        assert raster_sha == '71d097b9a83028dfad9370792c905bb3bfccfd5a', raster_sha
        shared_method = "void RasterizerVulkan::TickFrame() {\n    draw_counter = 0;\n    guest_descriptor_queue.TickFrame();\n    compute_pass_descriptor_queue.TickFrame();\n    descriptor_buffer_ring.TickFrame();\n    fence_manager.TickFrame();\n    staging_pool.TickFrame();\n#ifdef PS5_NATIVE\n    // C01/C03: identify who holds the cache lock during frame housekeeping.\n    // One of 16 frames with detailed logging; no clocks or changed locks in\n    // quiet release. Wait and held intervals use disjoint timer scopes.\n    const bool frame_sample = ::Eden::Performance::ShouldSampleCacheFrame();\n#endif\n#ifdef PS5_NATIVE\n    // Both native caches share the same RADV/PS5 GPU-memory budget.\n    // Query ONCE before either guest cache mutex, retaining original\n    // texture and buffer GC thresholds and retirement ordering.\n    const std::optional<u64> frame_memory_usage =\n        texture_cache_runtime.CanReportMemoryUsage()\n            ? std::optional<u64>{texture_cache_runtime.GetDeviceMemoryUsage()}\n            : std::nullopt;\n#endif\n    {\n#ifdef PS5_NATIVE\n        ::Eden::Performance::CachePhaseTimer texture_wait{\n            ::Eden::Performance::CachePhase::FrameTextureWait, frame_sample};\n#endif\n        std::scoped_lock lock{texture_cache.mutex};\n#ifdef PS5_NATIVE\n        texture_wait.Stop();\n        ::Eden::Performance::CachePhaseTimer texture_held{\n            ::Eden::Performance::CachePhase::FrameTextureHeld, frame_sample};\n#endif\n#ifdef PS5_NATIVE\n        texture_cache.TickFrame(frame_memory_usage);\n#else\n        texture_cache.TickFrame();\n#endif\n    }\n\n    {\n#ifdef PS5_NATIVE\n        ::Eden::Performance::CachePhaseTimer buffer_wait{\n            ::Eden::Performance::CachePhase::FrameBufferWait, frame_sample};\n#endif\n        std::scoped_lock lock{buffer_cache.mutex};\n#ifdef PS5_NATIVE\n        buffer_wait.Stop();\n        ::Eden::Performance::CachePhaseTimer buffer_held{\n            ::Eden::Performance::CachePhase::FrameBufferHeld, frame_sample};\n#endif\n#ifdef PS5_NATIVE\n        buffer_cache.TickFrame(frame_memory_usage);\n#else\n        buffer_cache.TickFrame();\n#endif\n    }\n}\n"
        previous_method = "void RasterizerVulkan::TickFrame() {\n    draw_counter = 0;\n    guest_descriptor_queue.TickFrame();\n    compute_pass_descriptor_queue.TickFrame();\n    descriptor_buffer_ring.TickFrame();\n    fence_manager.TickFrame();\n    staging_pool.TickFrame();\n#ifdef PS5_NATIVE\n    // C01/C03: identify who holds the cache lock during frame housekeeping.\n    // One of 16 frames with detailed logging; no clocks or changed locks in\n    // quiet release. Wait and held intervals use disjoint timer scopes.\n    const bool frame_sample = ::Eden::Performance::ShouldSampleCacheFrame();\n#endif\n    {\n#ifdef PS5_NATIVE\n        ::Eden::Performance::CachePhaseTimer texture_wait{\n            ::Eden::Performance::CachePhase::FrameTextureWait, frame_sample};\n#endif\n        std::scoped_lock lock{texture_cache.mutex};\n#ifdef PS5_NATIVE\n        texture_wait.Stop();\n        ::Eden::Performance::CachePhaseTimer texture_held{\n            ::Eden::Performance::CachePhase::FrameTextureHeld, frame_sample};\n#endif\n        texture_cache.TickFrame();\n    }\n#ifdef PS5_NATIVE\n    // Poll the driver while neither guest cache mutex is held. CPU writes\n    // must not wait for the PS5 memory-budget callback every sampled frame.\n    const std::optional<u64> frame_memory_usage = buffer_cache.PollFrameMemoryUsage();\n#endif\n    {\n#ifdef PS5_NATIVE\n        ::Eden::Performance::CachePhaseTimer buffer_wait{\n            ::Eden::Performance::CachePhase::FrameBufferWait, frame_sample};\n#endif\n        std::scoped_lock lock{buffer_cache.mutex};\n#ifdef PS5_NATIVE\n        buffer_wait.Stop();\n        ::Eden::Performance::CachePhaseTimer buffer_held{\n            ::Eden::Performance::CachePhase::FrameBufferHeld, frame_sample};\n#endif\n#ifdef PS5_NATIVE\n        buffer_cache.TickFrame(frame_memory_usage);\n#else\n        buffer_cache.TickFrame();\n#endif\n    }\n}\n"
        assert raster_source.count(shared_method) == 1
        raster_source = raster_source.replace(shared_method, previous_method, 1)
        raster_sha = raster_blob(raster_source)
        assert raster_sha == '41c1ff0f1b9c9f47e0414cfa77ef8de5c1165b3d', raster_sha
        auditor = temp/'fc27-shared-graphics-budget-historical'/raster_owner
        auditor.parent.mkdir(parents=True, exist_ok=True)
        auditor.write_text(raster_source)
        expected[raster_owner] = auditor
        exact_vendor_pin = '62f57caa5f1efd2069ae3b8eaf4f9fc8b501c44d'
        print('ENCORE_FC27_SHARED_GPU_BUDGET_EXACT_REVERSE_PASS')
    # Native Vulkan memory-budget query moved outside the guest BufferCache
    # critical section. Reverse ONLY its SHA-sealed TickFrame method on an
    # audit copy before historical Vulkan fork replay.
    if exact_vendor_pin == '62f57caa5f1efd2069ae3b8eaf4f9fc8b501c44d':
        assert raster_sha == '41c1ff0f1b9c9f47e0414cfa77ef8de5c1165b3d', raster_sha
        polled_method = "void RasterizerVulkan::TickFrame() {\n    draw_counter = 0;\n    guest_descriptor_queue.TickFrame();\n    compute_pass_descriptor_queue.TickFrame();\n    descriptor_buffer_ring.TickFrame();\n    fence_manager.TickFrame();\n    staging_pool.TickFrame();\n#ifdef PS5_NATIVE\n    // C01/C03: identify who holds the cache lock during frame housekeeping.\n    // One of 16 frames with detailed logging; no clocks or changed locks in\n    // quiet release. Wait and held intervals use disjoint timer scopes.\n    const bool frame_sample = ::Eden::Performance::ShouldSampleCacheFrame();\n#endif\n    {\n#ifdef PS5_NATIVE\n        ::Eden::Performance::CachePhaseTimer texture_wait{\n            ::Eden::Performance::CachePhase::FrameTextureWait, frame_sample};\n#endif\n        std::scoped_lock lock{texture_cache.mutex};\n#ifdef PS5_NATIVE\n        texture_wait.Stop();\n        ::Eden::Performance::CachePhaseTimer texture_held{\n            ::Eden::Performance::CachePhase::FrameTextureHeld, frame_sample};\n#endif\n        texture_cache.TickFrame();\n    }\n#ifdef PS5_NATIVE\n    // Poll the driver while neither guest cache mutex is held. CPU writes\n    // must not wait for the PS5 memory-budget callback every sampled frame.\n    const std::optional<u64> frame_memory_usage = buffer_cache.PollFrameMemoryUsage();\n#endif\n    {\n#ifdef PS5_NATIVE\n        ::Eden::Performance::CachePhaseTimer buffer_wait{\n            ::Eden::Performance::CachePhase::FrameBufferWait, frame_sample};\n#endif\n        std::scoped_lock lock{buffer_cache.mutex};\n#ifdef PS5_NATIVE\n        buffer_wait.Stop();\n        ::Eden::Performance::CachePhaseTimer buffer_held{\n            ::Eden::Performance::CachePhase::FrameBufferHeld, frame_sample};\n#endif\n#ifdef PS5_NATIVE\n        buffer_cache.TickFrame(frame_memory_usage);\n#else\n        buffer_cache.TickFrame();\n#endif\n    }\n}\n"
        earlier_method = "void RasterizerVulkan::TickFrame() {\n    draw_counter = 0;\n    guest_descriptor_queue.TickFrame();\n    compute_pass_descriptor_queue.TickFrame();\n    descriptor_buffer_ring.TickFrame();\n    fence_manager.TickFrame();\n    staging_pool.TickFrame();\n#ifdef PS5_NATIVE\n    // C01/C03: identify who holds the cache lock during frame housekeeping.\n    // One of 16 frames with detailed logging; no clocks or changed locks in\n    // quiet release. Wait and held intervals use disjoint timer scopes.\n    const bool frame_sample = ::Eden::Performance::ShouldSampleCacheFrame();\n#endif\n    {\n#ifdef PS5_NATIVE\n        ::Eden::Performance::CachePhaseTimer texture_wait{\n            ::Eden::Performance::CachePhase::FrameTextureWait, frame_sample};\n#endif\n        std::scoped_lock lock{texture_cache.mutex};\n#ifdef PS5_NATIVE\n        texture_wait.Stop();\n        ::Eden::Performance::CachePhaseTimer texture_held{\n            ::Eden::Performance::CachePhase::FrameTextureHeld, frame_sample};\n#endif\n        texture_cache.TickFrame();\n    }\n    {\n#ifdef PS5_NATIVE\n        ::Eden::Performance::CachePhaseTimer buffer_wait{\n            ::Eden::Performance::CachePhase::FrameBufferWait, frame_sample};\n#endif\n        std::scoped_lock lock{buffer_cache.mutex};\n#ifdef PS5_NATIVE\n        buffer_wait.Stop();\n        ::Eden::Performance::CachePhaseTimer buffer_held{\n            ::Eden::Performance::CachePhase::FrameBufferHeld, frame_sample};\n#endif\n        buffer_cache.TickFrame();\n    }\n}\n"
        assert raster_source.count(polled_method) == 1
        raster_source = raster_source.replace(polled_method, earlier_method, 1)
        raster_sha = raster_blob(raster_source)
        assert raster_sha == 'f8f27a5ed489c49f5de5a72bfa575416088ce472', raster_sha
        audit_owner = temp/'fc27-buffer-budget-before-lock'/raster_owner
        audit_owner.parent.mkdir(parents=True, exist_ok=True)
        audit_owner.write_text(raster_source)
        expected[raster_owner] = audit_owner
        exact_vendor_pin = '3b73e72d434fdd328c71ab37971f025f3ad8263b'
        print('ENCORE_FC27_BUFFER_BUDGET_LOCK_EXACT_REVERSE_PASS')
    # A GPU-collected CPU-write batch now reuses one mutex per cache domain.
    # Reverse exactly its independently SHA-sealed method on the audit COPY
    # before replaying the historical Vulkan oracle. Shipping C++ is intact.
    if exact_vendor_pin in {'ffb78672112a00a8df1da033ff462baf7d3c4d31',
                               '3b73e72d434fdd328c71ab37971f025f3ad8263b'}:
        assert raster_sha == 'f8f27a5ed489c49f5de5a72bfa575416088ce472', raster_sha
        batched_method = "void RasterizerVulkan::OnCacheInvalidations(std::span<const std::pair<DAddr, u64>> ranges) {\n    // Remove the complete CPU-write batch from GPU-owned ranges before any\n    // individual invalidation can download stale bytes over a later write.\n    // No registered buffer page in this CPU-write batch means no buffer can\n    // own GPU bytes to claim. Avoid the buffer mutex entirely in that case.\n    // NeverRegistered is monotonic and fails closed on unknown address spans.\n    bool may_claim_buffer = false;\n    for (const auto& [addr, size] : ranges) {\n        if (addr != 0 && size != 0 && !::Eden::BufferPages::NeverRegistered(addr, size)) {\n            may_claim_buffer = true;\n            break;\n        }\n    }\n    if (may_claim_buffer) {\n        std::scoped_lock lock{buffer_cache.mutex};\n        buffer_cache.ClaimCpuWrites(ranges);\n    }\n\n    // The single-range invalidation callback takes the texture and buffer\n    // mutex once PER range. GPU-collected write batches often contain many\n    // pages; acquire each domain only once, as InnerInvalidation already\n    // does for the same texture -> buffer -> shader ordering. The prior\n    // ClaimCpuWrites still precedes every possible GPU sibling readback.\n    bool may_touch_texture = false;\n    for (const auto& [addr, size] : ranges) {\n        if (addr != 0 && size != 0 && !::Eden::ImagePages::NeverHeld(addr, size)) {\n            may_touch_texture = true;\n            break;\n        }\n    }\n    if (may_touch_texture) {\n        std::scoped_lock lock{texture_cache.mutex};\n        for (const auto& [addr, size] : ranges) {\n            if (addr != 0 && size != 0 && !::Eden::ImagePages::NeverHeld(addr, size)) {\n                texture_cache.WriteMemory(addr, size);\n            }\n        }\n    }\n    if (may_claim_buffer) {\n        std::scoped_lock lock{buffer_cache.mutex};\n        for (const auto& [addr, size] : ranges) {\n            if (addr != 0 && size != 0 && !::Eden::BufferPages::NeverRegistered(addr, size)) {\n                buffer_cache.WriteMemory(addr, size);\n            }\n        }\n    }\n    // Guest shaders always observe invalidation, including writes into\n    // pages that have never held a BufferCache or TextureCache allocation.\n    for (const auto& [addr, size] : ranges) {\n        if (addr != 0 && size != 0) {\n            pipeline_cache.InvalidateRegion(addr, size);\n        }\n    }\n}\n"
        previous_method = "void RasterizerVulkan::OnCacheInvalidations(std::span<const std::pair<DAddr, u64>> ranges) {\n    // Remove the complete CPU-write batch from GPU-owned ranges before any\n    // individual invalidation can download stale bytes over a later write.\n    // No registered buffer page in this CPU-write batch means no buffer can\n    // own GPU bytes to claim. Avoid the buffer mutex entirely in that case.\n    // NeverRegistered is monotonic and fails closed on unknown address spans.\n    bool may_claim_buffer = false;\n    for (const auto& [addr, size] : ranges) {\n        if (addr != 0 && size != 0 && !::Eden::BufferPages::NeverRegistered(addr, size)) {\n            may_claim_buffer = true;\n            break;\n        }\n    }\n    if (may_claim_buffer) {\n        std::scoped_lock lock{buffer_cache.mutex};\n        buffer_cache.ClaimCpuWrites(ranges);\n    }\n    for (const auto& [addr, size] : ranges) OnCacheInvalidation(addr, size);\n}\n"
        assert raster_source.count(batched_method) == 1
        raster_source = raster_source.replace(batched_method, previous_method, 1)
        raster_sha = raster_blob(raster_source)
        assert raster_sha == '1921bf328af024a9ca001b9691e278a16fdf03ce', raster_sha
        historical = temp/'fc27-cache-batch-historical'/raster_owner
        historical.parent.mkdir(parents=True, exist_ok=True)
        historical.write_text(raster_source)
        expected[raster_owner] = historical
        exact_vendor_pin = 'fd43897f59dafe34ff110259c9f872bfc1c474cb'
        print('ENCORE_FC27_CACHE_BATCH_EXACT_REVERSE_PASS')
    # FC27 same-page CPU-write fix: reverse only its verified four-line hunk
    # on the historical audit COPY. The compiled vendor remains untouched.
    if exact_vendor_pin == 'fd43897f59dafe34ff110259c9f872bfc1c474cb':
        assert raster_sha == '1921bf328af024a9ca001b9691e278a16fdf03ce', raster_sha
        claim_hunk = (
            '        // Claim the ENTIRE CPU-write batch before WriteMemory on any range.\n'
            '        // Otherwise its GPU sibling download may overwrite a later write\n'
            '        // within the same page (Lichii #1328). The lock and draw order stay.\n'
            '        buffer_cache.ClaimCpuWrites(sequences);\n'
        )
        claim_hunk = ''.join(claim_hunk)
        assert raster_source.count(claim_hunk) == 1
        raster_source = raster_source.replace(claim_hunk, '', 1)
        raster_sha = raster_blob(raster_source)
        assert raster_sha == 'f23ad861761d53b59b8c83ae6003c089ae688060', raster_sha
        previous_raster = temp/'fc27-claim-batch-historical'/raster_owner
        previous_raster.parent.mkdir(parents=True, exist_ok=True)
        previous_raster.write_text(raster_source)
        expected[raster_owner] = previous_raster
        exact_vendor_pin = 'ac55a39658c8029a0ec900475234012ae6bf6289'
        print('ENCORE_FC27_CPU_BATCH_CLAIM_EXACT_REVERSE_PASS')
    # The GSV response ABI correction only changes its selected C++ owner
    # and paired source test. Verify both exact blobs before replaying the
    # unchanged FC27 Vulkan/BufferCache historical source proofs.
    if actual_vendor_pin in {
        "ac55a39658c8029a0ec900475234012ae6bf6289",
        "a7b9008340ccf03e4f63c180d820631858fe935e",
        "565f143c27443553b60ca1b21cc1094caa23ceb5",
        "010d5c61cefd62cbb5d27102cd9a2350fa0e69ce",
        "3460d10e60bff7dd8b057f592eb671cc35eddd25",
        "6f6f7f4cb154aa227eaf4d54330ff9d817b77ecb",
        "ce27bdd184c60d1f096ef1495c0ef7e5b7f0cdf0",
        "01c942171fea39c1f7cf31d13ab36895aebb593a",
        "dcf7116dd2c536e05c80d83ff9dbf30caa5cc109",
        "b65d8d9673475433f0b6eac72eb304bf23141666",
    }:
        for relative, expected_blob in (
            ("encore-active/ns2-runtime/graphics_supervisor/core/hle/service/am/service/graphics_supervisor.cpp",
             "747c9a0b5461fc1975fa373997064e3dc401a9a3"),
            ("tests/ns2_syncpt_bootstrap_source.py",
             "69723ef7bd1d47af5086052882d0749cc817f64a"),
        ):
            raw = (root / "vendor" / relative).read_bytes()
            found_blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
            assert found_blob == expected_blob, ("GSV COPY session source drift", relative, found_blob)
        if actual_vendor_pin != "ac55a39658c8029a0ec900475234012ae6bf6289":
            # Keep native GSV ABI revisions tied to their reviewed bytes.
            owner = root / "vendor/encore-active/ns2-runtime/hle/core/hle/service/am/service/graphics_supervisor_bootstrap.h"
            source = owner.read_bytes()
            found = hashlib.sha1(b"blob " + str(len(source)).encode() + bytes([0]) + source).hexdigest()
            expected_gsv_bootstrap = {
                "a7b9008340ccf03e4f63c180d820631858fe935e": "11e7c9d0569a175567083367e485cbf75cbc2207",
                "565f143c27443553b60ca1b21cc1094caa23ceb5": "11e7c9d0569a175567083367e485cbf75cbc2207",
                "010d5c61cefd62cbb5d27102cd9a2350fa0e69ce": "11d548eb338a5b75bf3a87a6adb6aa6aa302e017",
                "3460d10e60bff7dd8b057f592eb671cc35eddd25": "11d548eb338a5b75bf3a87a6adb6aa6aa302e017",
                "6f6f7f4cb154aa227eaf4d54330ff9d817b77ecb": "11d548eb338a5b75bf3a87a6adb6aa6aa302e017",
                "ce27bdd184c60d1f096ef1495c0ef7e5b7f0cdf0": "11d548eb338a5b75bf3a87a6adb6aa6aa302e017",
                "01c942171fea39c1f7cf31d13ab36895aebb593a": "11d548eb338a5b75bf3a87a6adb6aa6aa302e017",
                "dcf7116dd2c536e05c80d83ff9dbf30caa5cc109": "11d548eb338a5b75bf3a87a6adb6aa6aa302e017",
                "b65d8d9673475433f0b6eac72eb304bf23141666": "11d548eb338a5b75bf3a87a6adb6aa6aa302e017",
            }[actual_vendor_pin]
            assert found == expected_gsv_bootstrap, ("GSV 497 ABI owner drift", found)
            if actual_vendor_pin in {"565f143c27443553b60ca1b21cc1094caa23ceb5", "010d5c61cefd62cbb5d27102cd9a2350fa0e69ce", "3460d10e60bff7dd8b057f592eb671cc35eddd25", "6f6f7f4cb154aa227eaf4d54330ff9d817b77ecb", "ce27bdd184c60d1f096ef1495c0ef7e5b7f0cdf0", "01c942171fea39c1f7cf31d13ab36895aebb593a", "dcf7116dd2c536e05c80d83ff9dbf30caa5cc109", "b65d8d9673475433f0b6eac72eb304bf23141666"}:
                owner = root / "vendor/encore-active/ns2-runtime/hle/core/hle/service/am/service/graphics_supervisor_protocol.h"
                source = owner.read_bytes()
                found = hashlib.sha1(b"blob " + str(len(source)).encode() + bytes([0]) + source).hexdigest()
                expected_protocol = "4a35519c4f01cc4c1b604787bfbb139161f64a05" if actual_vendor_pin in {"3460d10e60bff7dd8b057f592eb671cc35eddd25", "6f6f7f4cb154aa227eaf4d54330ff9d817b77ecb", "ce27bdd184c60d1f096ef1495c0ef7e5b7f0cdf0", "01c942171fea39c1f7cf31d13ab36895aebb593a", "dcf7116dd2c536e05c80d83ff9dbf30caa5cc109", "b65d8d9673475433f0b6eac72eb304bf23141666"} else "6ce5ba02c2032237f81d9684da9e56cfbfb831c0"
                assert found == expected_protocol, ("GSV bootstrap hint ABI owner drift", found)
        exact_vendor_pin = "eadc6e798def18417e50db6a03a291440429d795"
    # This revert commit has the same complete vendor Git tree as the
    # reviewed pre-rollback pin. Reject any different source tree, including
    # newly added or removed files, before reusing its byte-exact source gates.
    if exact_vendor_pin == "03b264ee3e5ac7d7bbf89d3a9c51a3aff93a4433":
        actual_tree = subprocess.check_output(
            ["git", "-C", str(root / "vendor"), "rev-parse", "HEAD^{tree}"],
            text=True).strip()
        assert actual_tree == "301f91c2ee0eb4e5d86baba9b1036c57f6d5aa04", ("Vendor revert tree drift", actual_tree)
        exact_vendor_pin = "eadc6e798def18417e50db6a03a291440429d795"
    # The fail-closed FC27 draw fix is a single reviewed predicate change.
    # Reverse it only on the audit COPY, then replay the unchanged five-owner
    # attribute-source receipt and historical Vulkan oracle.
    # This reversal is safe by complete source identity, not by the moving
    # vendor gitlink. Later NS1 DMA / NS2 service commits do not edit this
    # owner; the following five-owner receipt still rejects any real drift.
    if raster_sha == 'f23ad861761d53b59b8c83ae6003c089ae688060':
        source_before = ("    if (!source && !attribute_handle_source) {\n"
                         "        // Only legacy shaders without an explicit source may use the old lookup")
        source_after = ("    if (!source) {\n"
                        "        // Legacy cached shader metadata (offset=0) retains its old lookup")
        assert raster_source.count(source_before) == 1
        raster_source = raster_source.replace(source_before, source_after, 1)
        assert raster_blob(raster_source) == '046269f8484776e22c8aee308b75c7b98f8bf5c6'
        reviewed_raster = temp/'fc27-failclosed-historical'/raster_owner
        reviewed_raster.parent.mkdir(parents=True, exist_ok=True)
        reviewed_raster.write_text(raster_source)
        expected[raster_owner] = reviewed_raster
        exact_vendor_pin = '917ccdc1cf772b9312b19888eea181b8e114334b'
        print('ENCORE_FC27_INVALID_ATTRIBUTE_FAILCLOSED_EXACT_REVERSE_PASS')
    # FC27 shader attribute-source fix: reverse only the exact reviewed
    # vendor successor on an audit COPY. The compiled native code stays
    # untouched; every full source blob and its exact historic preimage are
    # checked before the old Vulkan generator/R23 receipt runs.
    reviewed_fc27_hunks = {"shader_recompiler/ir_opt/texture_pass.cpp":{"current":"0010ffd43e7ac3fb482c46277c854ab9a76b06ab","predecessor":"889456a31ddeb87e411ce4d0d2d41078b9593244","hunks":[["    };\n}\n\n// Preserve the exact guest varying component supplying a bindless handle.\n// The old bool discarded this identity and the rasterizer guessed the first\n// integer input, which may be an unrelated vertex attribute.\nstd::optional<u32> IsAttributeSourcedHandle(const IR::Value& handle) {\n    if (handle.IsImmediate()) return std::nullopt;\n    const IR::Inst* inst{handle.InstRecursive()};\n    if (!inst) return std::nullopt;\n    if (inst->GetOpcode() == IR::Opcode::BitCastU32F32 && !inst->Arg(0).IsImmediate()) {\n        inst = inst->Arg(0).InstRecursive();\n    }\n    if (!inst || (inst->GetOpcode() != IR::Opcode::GetAttribute &&\n                  inst->GetOpcode() != IR::Opcode::GetAttributeU32))\n        return std::nullopt;\n    // Only generic varyings map to vertex attribute slots. System values\n    // (PrimitiveId, VertexId, etc.) are not valid texture-handle sources.\n    constexpr u32 first = static_cast<u32>(IR::Attribute::Generic0X);\n    constexpr u32 last = static_cast<u32>(IR::Attribute::Generic31W);\n    const u32 attribute = static_cast<u32>(inst->Arg(0).Attribute());\n    if (attribute < first || attribute > last) return std::nullopt;\n    if (!inst->Arg(1).IsEmpty() &&\n        (!inst->Arg(1).IsImmediate() || inst->Arg(1).U32() != 0))\n        return std::nullopt;\n    return attribute;\n}\n\nTextureInst MakeInst(Environment& env, IR::Block* block, IR::Inst& inst, const HostTranslateInfo& host_info) {\n    ConstBufferAddr addr;\n    if (IsBindless(inst)) {\n        const std::optional<ConstBufferAddr> track_addr{TrackCached(inst.Arg(0), env, host_info, block)};\n\n        const auto attribute_source = host_info.support_attribute_texture_handle\n                                          ? IsAttributeSourcedHandle(inst.Arg(0))\n                                          : std::nullopt;\n        if (track_addr) {\n            addr = *track_addr;\n        } else if (attribute_source) {\n            addr = ConstBufferAddr{\n                .index = ATTRIBUTE_HANDLE_CBUF_INDEX,\n                // No descriptor ABI change: this field is unused for the\n                // sentinel and can carry the exact GenericN component.\n                .offset = *attribute_source,\n                .shift_left = 0,\n                .secondary_index = 0,\n                .secondary_offset = 0,\n","    };\n}\n\nbool IsAttributeSourcedHandle(const IR::Value& handle) {\n    if (handle.IsImmediate()) {\n        return false;\n    }\n    const IR::Inst* inst{handle.InstRecursive()};\n    if (inst->GetOpcode() == IR::Opcode::BitCastU32F32 && !inst->Arg(0).IsImmediate()) {\n        inst = inst->Arg(0).InstRecursive();\n    }\n    return inst->GetOpcode() == IR::Opcode::GetAttribute ||\n           inst->GetOpcode() == IR::Opcode::GetAttributeU32;\n}\n\nTextureInst MakeInst(Environment& env, IR::Block* block, IR::Inst& inst, const HostTranslateInfo& host_info) {\n    ConstBufferAddr addr;\n    if (IsBindless(inst)) {\n        const std::optional<ConstBufferAddr> track_addr{TrackCached(inst.Arg(0), env, host_info, block)};\n\n        if (track_addr) {\n            addr = *track_addr;\n        } else if (host_info.support_attribute_texture_handle &&\n                   IsAttributeSourcedHandle(inst.Arg(0))) {\n            addr = ConstBufferAddr{\n                .index = ATTRIBUTE_HANDLE_CBUF_INDEX,\n                .offset = 0,\n                .shift_left = 0,\n                .secondary_index = 0,\n                .secondary_offset = 0,\n"]]},"include/video_core/renderer_vulkan/vk_graphics_pipeline.h":{"current":"515a766a6cc4d6fcba7692ad396f45396b746d28","predecessor":"bafff9a441a60b3dfb7e7d5a7a260741f45f59dc","hunks":[["#include <condition_variable>\n#include <functional>\n#include <mutex>\n#include <optional>\n#include <type_traits>\n#include <vector>\n\n","#include <condition_variable>\n#include <functional>\n#include <mutex>\n#include <type_traits>\n#include <vector>\n\n"],["    [[nodiscard]] bool UsesAttributeHandle() const noexcept {\n        return uses_attribute_handle;\n    }\n    [[nodiscard]] std::optional<u32> AttributeHandleSource() const noexcept {\n        return attribute_handle_source;\n    }\n    void SetAttributeHandle(u32 handle) noexcept {\n        attribute_handle = handle;\n    }\n","    [[nodiscard]] bool UsesAttributeHandle() const noexcept {\n        return uses_attribute_handle;\n    }\n    void SetAttributeHandle(u32 handle) noexcept {\n        attribute_handle = handle;\n    }\n"],["    u32 num_textures{};\n    u32 attribute_handle{};\n    bool uses_attribute_handle{};\n    // GenericN component encoded in the existing sentinel descriptor offset.\n    // Empty for legacy cached shaders or conflicting attributes across stages.\n    std::optional<u32> attribute_handle_source{};\n    // Immutable shader layout: no UBO/SSBO/TBO means no host buffer work.\n    std::array<bool, NUM_STAGES> stage_has_host_buffer_bindings{};\n    std::array<bool, NUM_STAGES> stage_has_image_bindings{};\n","    u32 num_textures{};\n    u32 attribute_handle{};\n    bool uses_attribute_handle{};\n    // Immutable shader layout: no UBO/SSBO/TBO means no host buffer work.\n    std::array<bool, NUM_STAGES> stage_has_host_buffer_bindings{};\n    std::array<bool, NUM_STAGES> stage_has_image_bindings{};\n"]]},"include/video_core/renderer_vulkan/vk_rasterizer.h":{"current":"6467fd4d704de6b77deb7e6cba4b8e33f70f5a08","predecessor":"7c754c82c12c4f4c934abd3d7f2cdb25222e8d2a","hunks":[["    void CollectAttributeHandleRuns(bool is_indexed);\n    std::vector<AttributeHandleRun> attribute_handle_runs;\n    GraphicsPipeline* attribute_handle_pipeline{};\n    std::optional<u32> attribute_handle_source{};\n    bool split_attribute_handles{};\n\n    void FlushWork();\n","    void CollectAttributeHandleRuns(bool is_indexed);\n    std::vector<AttributeHandleRun> attribute_handle_runs;\n    GraphicsPipeline* attribute_handle_pipeline{};\n    bool split_attribute_handles{};\n\n    void FlushWork();\n"]]},"vk_graphics_pipeline_cost.cpp":{"current":"2834a18fe7638749ec83cc8f5feb1fcde6c71a9a","predecessor":"526aa16b22ba3918c29ce85c884d606dcfd185a1","hunks":[["        num_image_elements += storage_views;\n        num_descriptor_entries += NumDescriptorEntries(*info);\n        for (const auto& desc : info->texture_descriptors) {\n            if (desc.cbuf_index != Shader::ATTRIBUTE_HANDLE_CBUF_INDEX)\n                continue;\n            if (!uses_attribute_handle) {\n                attribute_handle_source = desc.cbuf_offset;\n            } else if (attribute_handle_source &&\n                       *attribute_handle_source != desc.cbuf_offset) {\n                // A single per-run handle cannot represent two different\n                // shader varyings. Preserve the old unspecialized path.\n                attribute_handle_source.reset();\n            }\n            uses_attribute_handle = true;\n        }\n    }\n    fragment_has_color0_output = stage_infos[NUM_STAGES - 1].stores_frag_color[0];\n","        num_image_elements += storage_views;\n        num_descriptor_entries += NumDescriptorEntries(*info);\n        for (const auto& desc : info->texture_descriptors) {\n            uses_attribute_handle |= desc.cbuf_index == Shader::ATTRIBUTE_HANDLE_CBUF_INDEX;\n        }\n    }\n    fragment_has_color0_output = stage_infos[NUM_STAGES - 1].stores_frag_color[0];\n"]]},"vulkan_rasterizer.cpp":{"current":"046269f8484776e22c8aee308b75c7b98f8bf5c6","predecessor":"9da620ea3f4a4e0ab22e9747bf4e1058c09ce20b","hunks":[["    // draw calls may be split into handle-homogeneous runs.\n    const auto prepare_attribute_handles = [&] {\n        attribute_handle_pipeline = nullptr;\n        attribute_handle_source.reset();\n        attribute_handle_runs.clear();\n        if (split_attribute_handles && !pipeline->IsMeshPipeline() && pipeline->UsesAttributeHandle()) {\n            attribute_handle_source = pipeline->AttributeHandleSource();\n            CollectAttributeHandleRuns(is_indexed);\n            if (!attribute_handle_runs.empty()) {\n                attribute_handle_pipeline = pipeline;\n","    // draw calls may be split into handle-homogeneous runs.\n    const auto prepare_attribute_handles = [&] {\n        attribute_handle_pipeline = nullptr;\n        attribute_handle_runs.clear();\n        if (split_attribute_handles && !pipeline->IsMeshPipeline() && pipeline->UsesAttributeHandle()) {\n            CollectAttributeHandleRuns(is_indexed);\n            if (!attribute_handle_runs.empty()) {\n                attribute_handle_pipeline = pipeline;\n"],["    if (total == 0) return;\n\n    const VertexAttribute* source{};\n    u32 component_byte_offset{};\n    if (attribute_handle_source) {\n        // Generic0X..Generic31W are four consecutive IR values per input.\n        // Only 32-bit components can be read as an unmodified texture handle.\n        constexpr u32 first = static_cast<u32>(Shader::IR::Attribute::Generic0X);\n        constexpr u32 last = static_cast<u32>(Shader::IR::Attribute::Generic31W);\n        const u32 encoded = *attribute_handle_source;\n        if (encoded >= first && encoded <= last) {\n            const u32 generic = (encoded - first) / 4;\n            const u32 component = (encoded - first) % 4;\n            if (generic < regs.vertex_attrib_format.size()) {\n                const auto& attr = regs.vertex_attrib_format[generic];\n                const bool is_32bit =\n                    attr.size == VertexAttribute::Size::Size_R32 ||\n                    attr.size == VertexAttribute::Size::Size_R32_G32 ||\n                    attr.size == VertexAttribute::Size::Size_R32_G32_B32 ||\n                    attr.size == VertexAttribute::Size::Size_R32_G32_B32_A32;\n                if (!attr.constant && is_32bit && component < attr.ComponentCount() &&\n                    (attr.type == VertexAttribute::Type::UInt ||\n                     attr.type == VertexAttribute::Type::SInt ||\n                     attr.type == VertexAttribute::Type::Float)) {\n                    source = &attr;\n                    component_byte_offset = component * sizeof(u32);\n                }\n            }\n        }\n    }\n    if (!source) {\n        // Legacy cached shader metadata (offset=0) retains its old lookup\n        // until the shader is recompiled. Never guess a component on an\n        // unsupported packed or normalized attribute format.\n        for (const auto& attr : regs.vertex_attrib_format) {\n            if (attr.constant || attr.size == VertexAttribute::Size::Invalid) continue;\n            if (attr.type == VertexAttribute::Type::UInt ||\n                attr.type == VertexAttribute::Type::SInt) {\n                source = &attr;\n                break;\n            }\n        }\n    }\n    if (!source) {\n","    if (total == 0) return;\n\n    const VertexAttribute* source{};\n    for (const auto& attr : regs.vertex_attrib_format) {\n        if (attr.constant || attr.size == VertexAttribute::Size::Invalid) continue;\n        if (attr.type == VertexAttribute::Type::UInt ||\n            attr.type == VertexAttribute::Type::SInt) {\n            source = &attr;\n            break;\n        }\n    }\n    if (!source) {\n"],["\n    const u32 primitive_size =\n        state.topology == Maxwell::PrimitiveTopology::Triangles ? 3 : total;\n    const GPUVAddr base_address = stream.Address() + source->offset +\n                                 component_byte_offset;\n    const auto read_handle = [&](u32 position) {\n        u32 vertex{};\n        if (is_indexed) {\n","\n    const u32 primitive_size =\n        state.topology == Maxwell::PrimitiveTopology::Triangles ? 3 : total;\n    const GPUVAddr base_address = stream.Address() + source->offset;\n    const auto read_handle = [&](u32 position) {\n        u32 vertex{};\n        if (is_indexed) {\n"],["    SCOPE_EXIT {\n        split_attribute_handles = false;\n        attribute_handle_pipeline = nullptr;\n        attribute_handle_source.reset();\n        attribute_handle_runs.clear();\n    };\n    PrepareDraw(is_indexed, [this, is_indexed, instance_count] {\n","    SCOPE_EXIT {\n        split_attribute_handles = false;\n        attribute_handle_pipeline = nullptr;\n        attribute_handle_runs.clear();\n    };\n    PrepareDraw(is_indexed, [this, is_indexed, instance_count] {\n"]]}}
    if exact_vendor_pin in {
        'ce1c02b1ce14697003798e3f9872015035984719',
        'c47770d49dc8ed5f09838004f5bd08d9b1d5abc8',
        '917ccdc1cf772b9312b19888eea181b8e114334b',
    } or raster_sha == '046269f8484776e22c8aee308b75c7b98f8bf5c6':
        for name, witness in reviewed_fc27_hunks.items():
            if name.startswith('shader_recompiler/'):
                raw_path = root/'vendor/encore-active/eden-shader/src'/name
            else:
                raw_path = active/name
            # Use the already byte-sealed audit-only predecessor for the
            # rasterizer; every other owner must still match shipping bytes.
            # Bounded native transition hints were reversed above on exact
            # SHA-sealed audit copies. The older FC27 attribute-source
            # witness must inspect those restored owners, NOT the shipping
            # successor with its added optional transition-hint cap.
            # If an earlier exact-source reversal already reconstructed this
            # transition owner to the FC27 witness blob, consume that audit
            # copy. Applicability is proven by bytes, never by a stale vendor SHA.
            exact_restored = (
                name in expected and
                raster_blob(expected[name].read_text()) == witness['current']
            )
            gpu49_restored = name in gpu49_edits
            real_source = (expected[name].read_text()
                           if name == raster_owner or exact_restored or gpu49_restored
                           else raw_path.read_text())
            # GPU-22 current-channel GMMU owner also changes this header's
            # constructor/reference. Rewind only its two SHA-sealed hunks on
            # the historical audit copy; PS5 still compiles the new header.
            if name == 'include/video_core/renderer_vulkan/vk_rasterizer.h' and \
                    raster_blob(real_source) == 'db60043206cc66a284bd3e9327a9fed7b011b25a':
                reviewed = "    explicit AccelerateDMA(BufferCache& buffer_cache, TextureCache& texture_cache,\n                           Scheduler& scheduler, Tegra::MemoryManager* const& gpu_memory);"
                original = "    explicit AccelerateDMA(BufferCache& buffer_cache, TextureCache& texture_cache,\n                           Scheduler& scheduler);"
                assert real_source.count(reviewed) == 1, 'GPU-22 header hunk drift'
                real_source = real_source.replace(reviewed, original, 1)
                reviewed = "    // The GPU address space changes on channel binds. Reference the\n    // rasterizer's active pointer, not a stale construction-time channel.\n    Tegra::MemoryManager* const& gpu_memory;\n"
                original = ""
                assert real_source.count(reviewed) == 1, 'GPU-22 header hunk drift'
                real_source = real_source.replace(reviewed, original, 1)
                assert raster_blob(real_source) == '6467fd4d704de6b77deb7e6cba4b8e33f70f5a08'
                print('ENCORE_NS1_GPU22_HEADER_EXACT_REVERSE_PASS')
            # GPU-56 / Lichii #273: depth-compare sampled images must remain
            # floating-point even when the TIC format is integer/unknown. Reverse
            # only this exact one-line semantic delta on the audit copy before
            # the earlier FC27 TexturePass receipts.
            if name == 'shader_recompiler/ir_opt/texture_pass.cpp' and \
                    raster_blob(real_source) == '4301e9dbc19c4e07e7c24af23177cf5fa2142f1a':
                current_depth_compare = (
                    "                // Depth-compare sampling returns floating-point values in Vulkan even when the\n"
                    "                // TIC format itself is integer or unknown. Never build an integer sampled image.\n"
                    "                const bool is_integer{flags.is_depth == 0 && is_texture_pixel_format_integer(cbuf)};\n"
                )
                historical_depth_compare = (
                    "                const bool is_integer{is_texture_pixel_format_integer(cbuf)};\n"
                )
                assert real_source.count(current_depth_compare) == 1
                real_source = real_source.replace(current_depth_compare,
                                                  historical_depth_compare, 1)
                assert raster_blob(real_source) == '30c9a612a88fa6cd832a40ad0f717b4944db45a1'
                print('ENCORE_NS1_GPU56_DEPTH_COMPARE_FLOAT_EXACT_REVERSE_PASS')

            # NS1 f710080 changes only descriptor-array budget accounting.
            # Reverse that SHA-sealed owner on the audit COPY so the older
            # five-owner FC27 attribute-source receipt remains comparable.
            if name == 'shader_recompiler/ir_opt/texture_pass.cpp' and \
                    raster_blob(real_source) == '30c9a612a88fa6cd832a40ad0f717b4944db45a1':
                current_texture_budget = "u32 DynamicSampledTextureArrayCount(const TextureInstVector& to_replace) {\n    // Count DISTINCT sampled descriptor arrays, not shader sample instructions.\n    // Descriptors::Add(TextureDescriptor) merges repeated uses of an identical\n    // array. Counting each instruction used to divide the descriptor budget by\n    // the number of samples, then clamp valid dynamic indices to a wrong slot.\n    // Mirror that descriptor identity, excluding the flags Add combines with OR.\n    using ArrayKey = std::array<u32, 11>;\n    boost::container::small_vector<ArrayKey, 16> arrays;\n    for (const TextureInst& inst : to_replace) {\n        const auto flags{inst.inst->Flags<IR::TextureInstInfo>()};\n        if (inst.cbuf.count <= 1 || IsStorageImageOpcode(IndexedInstruction(*inst.inst)) ||\n            flags.type == TextureType::Buffer) {\n            continue;\n        }\n        const auto& cbuf = inst.cbuf;\n        const ArrayKey key{\n            static_cast<u32>(flags.type.Value()), flags.is_depth != 0 ? 1U : 0U,\n            cbuf.has_secondary ? 1U : 0U, cbuf.index, cbuf.offset, cbuf.shift_left,\n            cbuf.secondary_index, cbuf.secondary_offset, cbuf.secondary_shift_left,\n            cbuf.count, DynamicDescriptorSizeShift(cbuf.dynamic_offset),\n        };\n        if (std::ranges::find(arrays, key) == arrays.end()) {\n            arrays.push_back(key);\n        }\n    }\n    return static_cast<u32>(arrays.size());\n}\n"
                historical_texture_budget = "u32 DynamicSampledTextureArrayCount(const TextureInstVector& to_replace) {\n    u32 count{};\n    for (const TextureInst& inst : to_replace) {\n        const auto flags{inst.inst->Flags<IR::TextureInstInfo>()};\n        if (inst.cbuf.count > 1 && !IsStorageImageOpcode(IndexedInstruction(*inst.inst)) &&\n            flags.type != TextureType::Buffer) {\n            ++count;\n        }\n    }\n    return count;\n}\n"
                assert real_source.count('#include <array>\n') == 1
                assert real_source.count(current_texture_budget) == 1
                real_source = real_source.replace('#include <array>\n', '', 1)
                real_source = real_source.replace(current_texture_budget,
                                                  historical_texture_budget, 1)
                assert raster_blob(real_source) == '0010ffd43e7ac3fb482c46277c854ab9a76b06ab'
                print('ENCORE_NS1_DYNAMIC_TEXTURE_ARRAY_BUDGET_EXACT_REVERSE_PASS')
            assert raster_blob(real_source) == witness['current'], (
                'FC27 exact reviewed runtime drift', name)
            predecessor = real_source
            for after, before in witness['hunks']:
                assert predecessor.count(after) == 1, (
                    'FC27 reviewed source hunk moved', name)
                predecessor = predecessor.replace(after, before, 1)
            assert raster_blob(predecessor) == witness['predecessor'], (
                'FC27 exact predecessor reconstruction failed', name)
            if not name.startswith('shader_recompiler/'):
                reviewed_path = temp/'fc27-reviewed-historical'/name
                reviewed_path.parent.mkdir(parents=True, exist_ok=True)
                reviewed_path.write_text(predecessor)
                expected[name] = reviewed_path
        raster_source = expected[raster_owner].read_text()
        raster_sha = raster_blob(raster_source)
        # The remaining historical matrices apply to the exact reconstructed
        # 850086c7 predecessor, not to the shipping gitlink.
        exact_vendor_pin = '850086c79ec40838663989a81f33ba8ea2f15f6a'
        print('ENCORE_FC27_EXACT_ATTRIBUTE_SOURCE_REVERSE_PASS',
              'owners=5', 'historical_vendor=850086c7')
    # The reviewed intervening vendor DMA/image invalidation changes are
    # removed on this audit COPY only, to compare with the old frozen R23 tree.
    # Exact source before and normalized SHA1 were separately verified.
    if exact_vendor_pin in {'2a450d43d1d23d3e8b1667e396613f62c69c26d7',
                             '17c95ef233a9a0e508e50ada4ae9dc53a300c46c', '082cd1b77c7df80dc422eae5ba59d9cd33e48dc4', 'e0fced3a091495e70362d8c4ca072942f027af24', '491fa7e2388d46e23827b1459360a5d7f4a2814b', 'b177deb8282b14e1521485f5ac63bd7ccc9ca7ef', '06fc7dc2e0a00e00f831dfd78ae78087736276a3', '850086c79ec40838663989a81f33ba8ea2f15f6a'}:
        assert raster_sha == '9da620ea3f4a4e0ab22e9747bf4e1058c09ce20b'
        new_batch = "    // No registered buffer page in this CPU-write batch means no buffer can\n    // own GPU bytes to claim. Avoid the buffer mutex entirely in that case.\n    // NeverRegistered is monotonic and fails closed on unknown address spans.\n    bool may_claim_buffer = false;\n    for (const auto& [addr, size] : ranges) {\n        if (addr != 0 && size != 0 && !::Eden::BufferPages::NeverRegistered(addr, size)) {\n            may_claim_buffer = true;\n            break;\n        }\n    }\n    if (may_claim_buffer) {\n        std::scoped_lock lock{buffer_cache.mutex};\n        buffer_cache.ClaimCpuWrites(ranges);\n    }"
        old_batch = "    {\n        std::scoped_lock lock{buffer_cache.mutex};\n        buffer_cache.ClaimCpuWrites(ranges);\n    }"
        new_dma = "    // A buffer DMA updates guest memory without invoking the texture-cache\n    // CPU-write callback. Hold both cache locks over the ownership decision\n    // and copy so another thread cannot publish a newer image in between.\n    // Lichii c84935f / 47d2368 / 36bfb77: only invalidate destination images\n    // whose latest bytes are already in guest memory. Skip the unsafe case\n    // rather than uploading stale CPU bytes over GPU-owned image contents.\n    std::scoped_lock lock{buffer_cache.mutex, texture_cache.mutex};\n    bool copied_gpu_bytes = false;\n    if (!buffer_cache.DMACopy(src_address, dest_address, amount, &copied_gpu_bytes)) {\n        return false;\n    }\n    if (!copied_gpu_bytes &&\n        !texture_cache.IsGpuMemoryGpuModified(src_address, amount) &&\n        !texture_cache.IsGpuMemoryGpuModified(dest_address, amount)) {\n        texture_cache.WriteGpuMemory(dest_address, amount);\n    }\n    return true;"
        old_dma = "    std::scoped_lock lock{buffer_cache.mutex};\n    return buffer_cache.DMACopy(src_address, dest_address, amount);"
        assert raster_source.count(new_batch) == raster_source.count(new_dma) == 1
        raster_source = raster_source.replace(new_batch, old_batch, 1)
        raster_source = raster_source.replace(new_dma, old_dma, 1)
        raster_sha = raster_blob(raster_source)
        assert raster_sha == '01c6880e5a8836da45601b0a3cb7c0fd6c46cf35'
        print('ENCORE_NS2_VENDOR_EXACT_RASTERIZER_REVERSE_PASS')
    if exact_vendor_pin in {'8153654a2f1fe809fb2caa28dcadca90a7661446', '6c38328fbef33de747f5c31ea30d13541a513a4a', '8e564f61e6c8b86149ce0a0d6d2aa323a268dda6', '67759611edc13414c112ea9d2b6664d54827a200'}:
        assert raster_sha == '38d5630570675088a0620ef533112bb314a40ae8', 'Unexpected new PS5 FC27 rasterizer blob'
        receipt_path = root/'vendor/tests/native_msaa_handle_receipt.py'
        receipt_text = receipt_path.read_text()
        assert raster_blob(receipt_text) == '236713fa06672b39e2a4b9a84907882bbbb1bbbd'
        receipt = runpy.run_path(str(receipt_path))
        assert receipt['CURRENT_DEFERRED_PAGE_PROTECTION'] == raster_sha
        assert receipt['CURRENT_PAGE_SIBLING'] == '01c6880e5a8836da45601b0a3cb7c0fd6c46cf35'
        before, after = receipt['DEFERRED_BEFORE'], receipt['DEFERRED_AFTER']
        inc = receipt['DEFERRED_INCLUDE']
        assert raster_source.count(inc) == raster_source.count(after) == 1
        assert before not in raster_source
        raster_source = raster_source.replace(inc, '', 1).replace(after, before, 1)
        raster_sha = raster_blob(raster_source)
        assert raster_sha == '01c6880e5a8836da45601b0a3cb7c0fd6c46cf35', 'FC27 deferred audit reversal changed other code'
        print('ENCORE_FC27_DEFERRED_PROTECTION_EXACT_REVERSE_PASS')
    # Vendor b13c4c1 successor: UnmapMemory deliberately disables sibling-page
    # preservation because the mapping is being destroyed. Reverse exactly that
    # reviewed call-site flag in the audit copy before the immutable R23/P24
    # provenance chain; shipping source remains unchanged.
    if raster_sha == '01c6880e5a8836da45601b0a3cb7c0fd6c46cf35':
        current_unmap = '        buffer_cache.WriteMemory(addr, size, false);\n'
        historical_unmap = '        buffer_cache.WriteMemory(addr, size);\n'
        assert raster_source.count(current_unmap) == 1
        raster_source = raster_source.replace(current_unmap, historical_unmap, 1)
        raster_sha = raster_blob(raster_source)
        assert raster_sha == 'aa3ff8baf97f075d1adf44a9d19335c89403c8e1'
        print('ENCORE_FC27_GPU_PAGE_SIBLING_UNMAP_EXACT_REVERSE_PASS')
    # Eden #4559 is a later, independently reviewed DrawTexture delta.
    # Reuse the vendor's exact immutable before/after receipt ONLY to reverse
    # that one delta in the audit copy, then continue all historical engine
    # proofs below unchanged.
    if raster_sha == 'aa3ff8baf97f075d1adf44a9d19335c89403c8e1':
        receipt_path = root/'vendor/tests/native_msaa_handle_receipt.py'
        receipt_text = receipt_path.read_text()
        receipt_sha = raster_blob(receipt_text)
        assert receipt_sha in {
            '236713fa06672b39e2a4b9a84907882bbbb1bbbd',
            '18bf879c31b6d29b77b8fc6cc3026f8bd7fc0ec2',
            '0175833f4758b6b694e1e4528afee6e5f8fd24a1',
            # New helper reconstructs exactly the two corrected GuestCacheLock
            # calls before the 16-hunk immutable rasterizer predecessor.
            '40bbd965be330cfa024005931be98533232971ac',
        }, ('Unreviewed native MSAA receipt source', receipt_sha)
        if receipt_sha == '40bbd965be330cfa024005931be98533232971ac':
            # The vendor HEAD can advance for HLE/loader-only changes. Keep the
            # *actual rasterizer* exactly sealed, then replay the immutable
            # predecessor reconstruction; do not key this GPU proof to an
            # unrelated old vendor commit ID.
            fixture = runpy.run_path(str(receipt_path))
            source = (root/'vendor/encore-active/eden-vulkan/vulkan_rasterizer.cpp').read_text()
            # The second immutable FC27 DrawTexture receipt reads the current
            # rasterizer independently of the main Vulkan audit path. Reverse
            # the same exact PS5 Ampere-only method before NS1 replays.
            if raster_blob(source) == "ff8ad79ef203456063dbd848eab3ea575628edfc":
                only_native_release = (
                    "bool RasterizerVulkan::SignalNativeFence(std::function<void()>&& func) {\n"
                    "    fence_manager.SignalNativeFence(std::move(func));\n"
                    "    return true;\n"
                    "}\n"
                )
                assert source.count(only_native_release)==1
                source=source.replace(only_native_release,"",1)
                assert raster_blob(source)=="39b2ed67e51937aecad666de4113ce792d32132d"
            source=reverse_attribute_index_batch_successor(source)
            source=reverse_collected_batch_preflight_successor(source)
            source=reverse_collected_batch_lock_successor(source)
            if raster_blob(source) == 'e5baa7f438d8caf11327989087db38ed1ca053a4':
                assert source.count(strict_cpp_delta)==1
                source=source.replace(strict_cpp_delta,"",1)
            assert raster_blob(source) == 'f67815618d25657dcf64a87944b0c0bc5c2d8993'
            normalized = fixture['restore_guest_cache_lock_successor'](source)
            assert raster_blob(normalized) == '0633e3cf41c615f46791d3943ff40ac22399b047'
        receipt = runpy.run_path(str(receipt_path))
        assert receipt['CURRENT_DRAWTEXTURE'] == raster_sha
        draw_after = receipt['DRAW_TEXTURE_AFTER']
        draw_before = receipt['DRAW_TEXTURE_BEFORE']
        assert raster_source.count('#include <optional>\n') == 1
        assert raster_source.count(draw_after) == 1 and draw_before not in raster_source
        raster_source = raster_source.replace('#include <optional>\n', '', 1)
        raster_source = raster_source.replace(draw_after, draw_before, 1)
        raster_sha = raster_blob(raster_source)
        assert raster_sha == '1c40cc3b968c76fc505f5cea63218b93e89b4529'
        print('ENCORE_EDEN4559_DRAWTEXTURE_EXACT_REVERSE_PASS')
    pair_vendor_pin = exact_vendor_pin
    if pair_vendor_pin == '510f1efde545357fe8095a812df32251ee546285':
        new_proxy = root / 'vendor/encore-active/ns2-runtime/hle/core/hle/service/am/service/application_proxy_service.cpp'
        assert subprocess.check_output(
            ['git', 'hash-object', str(new_proxy)], text=True).strip() == '1e6f2592e34845d9b9b3aa3d152c78c4fed66639', (
            'Native NS2 appletOE cmd10 owner drift')
    if pair_vendor_pin in {"ce25655b08751aa0c2f9efb10ff05fd8fcbf7a93", "7fc673495b2ee18d5216023280057a42aa78d46c", "510f1efde545357fe8095a812df32251ee546285"}:
        pair_vendor_pin = "ab417b59c5f7f4613ff27386be05c0644d0ed776"
    if pair_vendor_pin in {
        "c15cdfe96a3d836bf32ba21b8070088add81cdc9",
        "729f7e5a734b5a890a7bbf3ab60ce1100492af13",
        "1a09972eea6f473fda1b714efe84cd52219bf681", "3e6647827122c34704c2699a6f5e9b20fff3e9a6", "6d64217ea5804fb86dbf57685a3da0cb1d45ba32", "3f1fcfef119ca50dd630f0518a7fae1b96c7a85a", "0e4e96df638fc29c3bd2a8fcfe9f50821c5e5b3a", "9136d2e88c43233bcd029f22bdfda0e5c94a552f", "75ef34d7ef7f68b5eb4f1c6d0d99b6cbc55742d6", "34f02a3800cb6fb5330c099c81571ab03fd69ae1", "0d75406e36a3676b45184670093f0ecf652aab2f", "372a83d95622f152211fe91afa05d1e60ce84bea", "a3cc07ff68f8154543f2b07a6b3e6c01f9922ab9", "ab417b59c5f7f4613ff27386be05c0644d0ed776",
    }:
        # New vendor changes only the selected NS2 SVC trace owners; seal their
        # exact bytes without weakening the preserved Vulkan reverse-oracle.
        if pair_vendor_pin in {"729f7e5a734b5a890a7bbf3ab60ce1100492af13", "1a09972eea6f473fda1b714efe84cd52219bf681", "3e6647827122c34704c2699a6f5e9b20fff3e9a6", "6d64217ea5804fb86dbf57685a3da0cb1d45ba32", "3f1fcfef119ca50dd630f0518a7fae1b96c7a85a", "0e4e96df638fc29c3bd2a8fcfe9f50821c5e5b3a", "9136d2e88c43233bcd029f22bdfda0e5c94a552f", "75ef34d7ef7f68b5eb4f1c6d0d99b6cbc55742d6", "34f02a3800cb6fb5330c099c81571ab03fd69ae1", "0d75406e36a3676b45184670093f0ecf652aab2f", "372a83d95622f152211fe91afa05d1e60ce84bea", "a3cc07ff68f8154543f2b07a6b3e6c01f9922ab9", "ab417b59c5f7f4613ff27386be05c0644d0ed776", "372a83d95622f152211fe91afa05d1e60ce84bea", "a3cc07ff68f8154543f2b07a6b3e6c01f9922ab9", "ab417b59c5f7f4613ff27386be05c0644d0ed776"}:
            for owner, expected_blob in (
                ("encore-active/ns2-helpers/include/core/loader/ns2_svc_trace.h",
                 "86e8e7e96b5eda5b6b98ccd3c7e6ce76d4275c86"),
                ("encore-active/ns2-runtime/gpu_access_svc/core/hle/kernel/svc.cpp",
                 "09ae2494b2b6f620a25ab549c06c69045a9fb73d"),
                ("tests/ns2_recent_svc_fault_trace_host.py",
                 "79d8d7294e37e141d6c669d9b55fa5a02d94287e"),
            ):
                actual_blob = subprocess.check_output(
                    ["git", "hash-object", str(root / "vendor" / owner)],
                    text=True,
                ).strip()
                assert actual_blob == expected_blob, ("NS2 quiet SVC source drift", owner)
        if pair_vendor_pin in {"1a09972eea6f473fda1b714efe84cd52219bf681", "3e6647827122c34704c2699a6f5e9b20fff3e9a6", "6d64217ea5804fb86dbf57685a3da0cb1d45ba32", "3f1fcfef119ca50dd630f0518a7fae1b96c7a85a", "0e4e96df638fc29c3bd2a8fcfe9f50821c5e5b3a", "9136d2e88c43233bcd029f22bdfda0e5c94a552f", "75ef34d7ef7f68b5eb4f1c6d0d99b6cbc55742d6", "34f02a3800cb6fb5330c099c81571ab03fd69ae1", "0d75406e36a3676b45184670093f0ecf652aab2f", "372a83d95622f152211fe91afa05d1e60ce84bea", "a3cc07ff68f8154543f2b07a6b3e6c01f9922ab9", "ab417b59c5f7f4613ff27386be05c0644d0ed776", "372a83d95622f152211fe91afa05d1e60ce84bea", "a3cc07ff68f8154543f2b07a6b3e6c01f9922ab9", "ab417b59c5f7f4613ff27386be05c0644d0ed776"}:
            actual_blob = subprocess.check_output(
                ["git", "hash-object", str(root / "vendor/encore-active/ns2-astc/include/video_core/texture_cache/texture_cache.h")],
                text=True,
            ).strip()
            assert actual_blob == ("c7cb95ecaf388b925fc29582499bbd4b54a77f75" if pair_vendor_pin in {"6d64217ea5804fb86dbf57685a3da0cb1d45ba32", "3f1fcfef119ca50dd630f0518a7fae1b96c7a85a", "0e4e96df638fc29c3bd2a8fcfe9f50821c5e5b3a", "9136d2e88c43233bcd029f22bdfda0e5c94a552f", "75ef34d7ef7f68b5eb4f1c6d0d99b6cbc55742d6", "34f02a3800cb6fb5330c099c81571ab03fd69ae1", "0d75406e36a3676b45184670093f0ecf652aab2f", "372a83d95622f152211fe91afa05d1e60ce84bea", "a3cc07ff68f8154543f2b07a6b3e6c01f9922ab9", "ab417b59c5f7f4613ff27386be05c0644d0ed776", "372a83d95622f152211fe91afa05d1e60ce84bea", "a3cc07ff68f8154543f2b07a6b3e6c01f9922ab9", "ab417b59c5f7f4613ff27386be05c0644d0ed776"} else "859a9e46fb63a97fee82c8ea6b1566317264f98f" if pair_vendor_pin == "3e6647827122c34704c2699a6f5e9b20fff3e9a6" else "0d99f9a861c645562519f71d62f4f49bfedd8101"), ("Selected F07 texture owner drift", actual_blob)
        # The exact reverted synchronous rasterizer is byte-identical
        # to the old d024 path before the F07 historical replay.
        assert raster_blob((root/'vendor/encore-active/eden-vulkan/vulkan_rasterizer.cpp').read_text()) == '01c6880e5a8836da45601b0a3cb7c0fd6c46cf35'
        assert raster_sha == '1c40cc3b968c76fc505f5cea63218b93e89b4529'
        pair_vendor_pin = 'd0246caf58a3127597bba1edfc1f8dcbe0c5cfdc'
    # Only AFTER exact receipt reversal, the historical R23/P24 oracle
    # uses the old pin's unchanged owner/provenance applicability matrix.
    if pair_vendor_pin in {'8153654a2f1fe809fb2caa28dcadca90a7661446', '6c38328fbef33de747f5c31ea30d13541a513a4a', '8e564f61e6c8b86149ce0a0d6d2aa323a268dda6', '67759611edc13414c112ea9d2b6664d54827a200'}:
        pair_vendor_pin = 'd0246caf58a3127597bba1edfc1f8dcbe0c5cfdc'
    if pair_vendor_pin in {'b1bb49abea63b6664e0945df8431e10aac128c2f', '89d70eb505594447b3ca98658311002e74dac8ad', 'b68126c9cd95eef6c6656ff6d7834c62c092aa46', '0fc157b7ccef428e675ff945bc48eceb08fff607', '42459a7893c51a178ecd0c2f74f3951cc20fa12d', 'd1f8696448ed481e36380c3ea8431e3dc722304e', 'c5614d3c7ef75958965bac93c9e343eccdbc0fbe', '67926ea4b6960eefebf0427929cf299e8e056013', '50a849a93494f442d47573b8ce8b8797c3cecd26', '2c85d0e8ed192c5eec79423e6be8d883fa0bd7ab', '053acc8ddf30fe65f6376564bbd6efef58f07ddc', 'ffa519db0f68fb0d5d2acf791e381c898a34a175', '9e38066a508716fd959477eccf32c7fb2fde3356', 'e298a9b05732346141b685eb4c9850bfa02d9e58','f7ccfda091fd7429f44159318a07391881a3e7c0','92c480e17fedecc21ab4882b76e8507b5aed3771','7039d7752c5d8b1a53db50be0d8f2f7803867e13','d3fca0aa188052f0efd2bad102950aeaeeb36ab0','dfc39fcc087738955b0373b45fa97facdeb2fc47','b806bc497049819e716ef6de81f2a85312b188ce','a0e17271e94342c32b02acdc3199c3f258a8aecf','772f06c8f5b12fdc81066e61f3db2dedfe3eed81','568ae541c07691518e9663aa0fc5f3b017a98d53','dcfe3d2384bd800c6139ede672518ea2c66922a6','affa3c761f70268c89e9f7c7de24eec958c7f889','edcc311c09eed3a33e5acc373c63a436f662cb5b','945385cb96f539a5b2ab2edf269683dd1e9ebad9','2acf67ac8c6b8b1973ba29043206782a13ac8f41','ab38816078a53b81d4c59152ec660fcb653d4e7f','3cac7130d6626dced483d038cbf034274a0463d8','ec3757b3f17d974577b304faa0d54279e01d0a5a','2a8d841c4c7e34e89254e532fc75fd23e16f01fe','3b3a26afd70fbfbfb706e5b9964e3303c07a944c','49070af1bfee1ef67ed8037221345baf71d02373','388f0bda53806cd89d9c2f85139ec0491f212654','c92ce9a8b90808869be76d02e73d35636857a0d4','1e51d1f3383f149a599e36052aba7d887d4b1f77', 'b79c774d5d976b7d374b7f851354a652f6aa69c4', '9d324ca5ca2cdd84053f2d3dfadde5b86084c13d', 'cd476e6e93e8a786bef6260006baec134f5df71f', '2ccc4b0a714ca621ac2879768f87118a64ed65f6', '97ac02f263ec90f40a029f4aa62980c76bc25d5c', '9a83a6ba1cb464c9e5d14457cab18ad511c1104b', 'd0246caf58a3127597bba1edfc1f8dcbe0c5cfdc'}:
        # Vendor #156: only reverse the two exact reviewed cache-coherence
        # additions on an audit copy, as vendor's native_msaa_handle_receipt
        # does. Shipping source and historical oracle remain untouched.
        assert raster_sha == '1c40cc3b968c76fc505f5cea63218b93e89b4529'
        constructor = """    buffer_cache.SetPendingCpuWrites(
        [this](const std::function<void(DAddr, size_t)>& callback) {
            gpu.ForEachPendingCpuWrite(callback);
        });
"""
        batch = """void RasterizerVulkan::OnCacheInvalidations(std::span<const std::pair<DAddr, u64>> ranges) {
    // Remove the complete CPU-write batch from GPU-owned ranges before any
    // individual invalidation can download stale bytes over a later write.
    {
        std::scoped_lock lock{buffer_cache.mutex};
        buffer_cache.ClaimCpuWrites(ranges);
    }
    for (const auto& [addr, size] : ranges) OnCacheInvalidation(addr, size);
}

"""
        assert raster_source.count(constructor) == raster_source.count(batch) == 1
        raster_source = raster_source.replace(constructor, '', 1).replace(batch, '', 1)
        raster_sha = raster_blob(raster_source)
        assert raster_sha == 'efd77028f0710ea9e50cbbe77b04eebf3f306610'
        header_name = 'include/video_core/renderer_vulkan/vk_rasterizer.h'
        header_source = expected[header_name].read_text()
        assert raster_blob(header_source) == '7c754c82c12c4f4c934abd3d7f2cdb25222e8d2a'
        declaration = '    void OnCacheInvalidations(std::span<const std::pair<DAddr, u64>> ranges) override;\n'
        assert header_source.count(declaration) == 1
        header_source = header_source.replace(declaration, '', 1)
        assert raster_blob(header_source) == 'cb35d183c8a9c2ea05f5eb8949a167ea295f8ce7'
        header_audit = temp / 'normalized-vendor-cpu-write-race' / header_name
        header_audit.parent.mkdir(parents=True, exist_ok=True)
        header_audit.write_text(header_source)
        expected[header_name] = header_audit
        print('ENCORE_FC27_CPU_WRITE_RACE_EXACT_REVERSE_PARITY_PASS', 'owners=2')
    # R457 GPU CPU-write race: the shipping Vulkan rasterizer installs a
    # PendingCpuWrites callback and claims an entire invalidation batch before
    # individual downloads. This source predated the NS2 quiet-SVC work;
    # remove only these two exact chunks from the audit COPY before the
    # independent MSAA and frozen R23 oracle comparisons.
    if raster_sha == '1c40cc3b968c76fc505f5cea63218b93e89b4529':
        cpu_writes_ctor = """    buffer_cache.SetPendingCpuWrites(
        [this](const std::function<void(DAddr, size_t)>& callback) {
            gpu.ForEachPendingCpuWrite(callback);
        });
"""
        cpu_writes_batch = """void RasterizerVulkan::OnCacheInvalidations(std::span<const std::pair<DAddr, u64>> ranges) {
    // Remove the complete CPU-write batch from GPU-owned ranges before any
    // individual invalidation can download stale bytes over a later write.
    {
        std::scoped_lock lock{buffer_cache.mutex};
        buffer_cache.ClaimCpuWrites(ranges);
    }
    for (const auto& [addr, size] : ranges) OnCacheInvalidation(addr, size);
}

"""
        assert raster_source.count(cpu_writes_ctor) == 1
        assert raster_source.count(cpu_writes_batch) == 1
        raster_source = raster_source.replace(cpu_writes_ctor, "", 1)
        raster_source = raster_source.replace(cpu_writes_batch, "", 1)
        raster_sha = raster_blob(raster_source)
        assert raster_sha == 'efd77028f0710ea9e50cbbe77b04eebf3f306610', raster_sha
        print("ENCORE_R457_GPU_CPU_WRITE_RACE_EXACT_REVERSE_PASS owner=1 prior=efd77028")
    if raster_sha == 'efd77028f0710ea9e50cbbe77b04eebf3f306610':
        before = "    // Mesh draw workgroups are not indexed vertices. Only standard vertex\n    // draw calls may be split into handle-homogeneous runs.\n    attribute_handle_pipeline = nullptr;\n    attribute_handle_runs.clear();\n    if (split_attribute_handles && !mesh_draw && pipeline->UsesAttributeHandle()) {\n        CollectAttributeHandleRuns(is_indexed);\n        if (!attribute_handle_runs.empty()) {\n            attribute_handle_pipeline = pipeline;\n            pipeline->SetAttributeHandle(attribute_handle_runs.front().handle);\n        }\n    }\n    bool pipeline_ok = pipeline->Configure(is_indexed);\n    if (!pipeline_ok && pipeline->UsesForcedMsaaShadow()) {\n        // The shader may read/store its destination or the texture cache\n        // may have ended the shadow pass while binding descriptors.\n        // Resolve and RETRY this draw via the unchanged guest 1x pipeline.\n        if (native_msaa_shadow) (void)native_msaa_shadow->EndPrepared();\n        native_msaa_clear.reset();\n        native_samples = VK_SAMPLE_COUNT_1_BIT;\n        pipeline = pipeline_cache.CurrentGraphicsPipeline();\n        if (pipeline) {\n            prepared_pipeline = pipeline;\n            probe_pipeline = pipeline;\n            pipeline->SetEngine(maxwell3d, gpu_memory);\n            pipeline_ok = pipeline->Configure(is_indexed);\n        }\n    }\n"
        after = "    // Mesh draw workgroups are not indexed vertices. Only standard vertex\n    // draw calls may be split into handle-homogeneous runs.\n    const auto prepare_attribute_handles = [&] {\n        attribute_handle_pipeline = nullptr;\n        attribute_handle_runs.clear();\n        if (split_attribute_handles && !pipeline->IsMeshPipeline() && pipeline->UsesAttributeHandle()) {\n            CollectAttributeHandleRuns(is_indexed);\n            if (!attribute_handle_runs.empty()) {\n                attribute_handle_pipeline = pipeline;\n                pipeline->SetAttributeHandle(attribute_handle_runs.front().handle);\n            }\n        }\n    };\n    prepare_attribute_handles();\n    bool pipeline_ok = pipeline->Configure(is_indexed);\n    if (!pipeline_ok && pipeline->UsesForcedMsaaShadow()) {\n        // The shader may read/store its destination or the texture cache\n        // may have ended the shadow pass while binding descriptors.\n        // Resolve and RETRY this draw via the unchanged guest 1x pipeline.\n        if (native_msaa_shadow) (void)native_msaa_shadow->EndPrepared();\n        native_msaa_clear.reset();\n        native_samples = VK_SAMPLE_COUNT_1_BIT;\n        pipeline = pipeline_cache.CurrentGraphicsPipeline();\n        if (pipeline) {\n            prepared_pipeline = pipeline;\n            probe_pipeline = pipeline;\n            pipeline->SetEngine(maxwell3d, gpu_memory);\n            // The 1x pipeline owns its own descriptor/attribute state. The\n            // rejected shadow is not a valid owner for later split draws.\n            prepare_attribute_handles();\n            pipeline_ok = pipeline->Configure(is_indexed);\n        }\n    }\n"
        assert raster_source.count(after) == 1 and before not in raster_source
        historical_raster = raster_source.replace(after, before, 1)
        assert raster_blob(historical_raster) == '5b04321fa45d6b5e6af1d4b17bcf695348d0dd90'
        audit_raster = temp/'normalized-vendor-msaa-handle'/raster_owner
        audit_raster.parent.mkdir(parents=True, exist_ok=True)
        audit_raster.write_text(historical_raster)
        expected[raster_owner] = audit_raster
        print("ENCORE_R457_MSAA_HANDLE_EXACT_RECEIPT_PASS")
    else:
        assert raster_sha == '5b04321fa45d6b5e6af1d4b17bcf695348d0dd90', raster_sha
    # FC27 dynamic-texture/static-sampler repair changes one descriptor
    # offset in the selected graphics pipeline owner. Vendor's focused test
    # proves the exact source successor and its cache-version pair. Reverse
    # only that reviewed line in the audit copy before the frozen R23/P24
    # comparisons; the compiled vendor source remains unchanged.
    graphics_owner = 'vk_graphics_pipeline_cost.cpp'
    graphics_source = expected[graphics_owner].read_text()
    graphics_sha = raster_blob(graphics_source)
    if graphics_sha == '526aa16b22ba3918c29ce85c884d606dcfd185a1':
        runbuild_after = "    configure_func = ConfigureFunc(spv_modules, stage_infos);\n    build_task = std::move(func);\n    if (worker_thread) {\n#ifdef PS5_NATIVE\n        if (::Eden::DevVulkan::fast_first_pipelines) {\n            pending_first_use_graphics_builds.fetch_add(1, std::memory_order_release);\n            try {\n                worker_thread->QueueWork([this] {\n                    SCOPE_EXIT {\n                        pending_first_use_graphics_builds.fetch_sub(1, std::memory_order_release);\n                    };\n                    RunBuild();\n                });\n            } catch (...) {\n                pending_first_use_graphics_builds.fetch_sub(1, std::memory_order_release);\n                throw;\n            }\n        } else\n#endif\n        {\n            worker_thread->QueueWork([this] { RunBuild(); });\n        }\n        build_handed_off = true;\n    } else {\n        build_handed_off = true;\n        RunBuild();\n    }\n}\n\nvoid GraphicsPipeline::RunBuild() {\n    if (build_claimed.exchange(true, std::memory_order_acq_rel)) {\n        return;\n    }\n    build_task();\n    build_task = nullptr;\n}\n\n"
        runbuild_before = "    configure_func = ConfigureFunc(spv_modules, stage_infos);\n    if (worker_thread) {\n#ifdef PS5_NATIVE\n        if (::Eden::DevVulkan::fast_first_pipelines) {\n            // Cold first-use compilation has priority over speculative optimization.\n            // Publish BEFORE enqueuing, including work waiting in the builder queue.\n            pending_first_use_graphics_builds.fetch_add(1, std::memory_order_release);\n            try {\n                worker_thread->QueueWork([build = std::move(func)]() mutable {\n                    SCOPE_EXIT {\n                        pending_first_use_graphics_builds.fetch_sub(1, std::memory_order_release);\n                    };\n                    build();\n                });\n            } catch (...) {\n                pending_first_use_graphics_builds.fetch_sub(1, std::memory_order_release);\n                throw;\n            }\n        } else\n#endif\n        {\n            worker_thread->QueueWork(std::move(func));\n        }\n        // QueueWork returned successfully; the worker now owns completion,\n        // including paths where pipeline validation or compilation fails.\n        build_handed_off = true;\n    } else {\n        // Synchronous func() owns the completion callback from this point.\n        build_handed_off = true;\n        func();\n    }\n}\n\n"
        scheduler_after = "        // Wait for the pipeline to be built\n        scheduler.Record([this](vk::CommandBuffer) {\n            RunBuild();\n"
        scheduler_before = "        // Wait for the pipeline to be built\n        scheduler.Record([this](vk::CommandBuffer) {\n"
        assert graphics_source.count(runbuild_after) == 1
        assert graphics_source.count(scheduler_after) == 1
        graphics_source = graphics_source.replace(runbuild_after, runbuild_before, 1)
        graphics_source = graphics_source.replace(scheduler_after, scheduler_before, 1)
        graphics_sha = raster_blob(graphics_source)
        assert graphics_sha == 'efa8fd4d73c111655fced67fe7dd1e6b7c0178ba'
        print("ENCORE_FC27_GRAPHICS_RUNBUILD_EXACT_REVERSE_PASS")
    if graphics_sha == 'efa8fd4d73c111655fced67fe7dd1e6b7c0178ba':
        fixed_sampler = 'const u32 second_offset{desc.secondary_cbuf_offset};'
        indexed_sampler = 'const u32 second_offset{desc.secondary_cbuf_offset + index_offset};'
        assert graphics_source.count(fixed_sampler) == 1 and indexed_sampler not in graphics_source
        historical_graphics = graphics_source.replace(fixed_sampler, indexed_sampler, 1)
        assert raster_blob(historical_graphics) == 'd7563d41b74d780f4512899e2fda1b2f362f5523'
        audit_graphics = temp/'normalized-vendor-fc27-static-sampler'/graphics_owner
        audit_graphics.parent.mkdir(parents=True, exist_ok=True)
        audit_graphics.write_text(historical_graphics)
        expected[graphics_owner] = audit_graphics
        print("ENCORE_FC27_STATIC_SAMPLER_EXACT_RECEIPT_PASS")
    else:
        assert graphics_sha == 'd7563d41b74d780f4512899e2fda1b2f362f5523', graphics_sha
    # The compute owner carries the same fixed-secondary-sampler rule, but it
    # is outside the R23/P24 owner set. Require the exact shipping successor,
    # then normalize its sole reviewed line in the audit copy.
    compute_owner = 'vk_compute_pipeline_cost.cpp'
    compute_source = expected[compute_owner].read_text()
    compute_sha = raster_blob(compute_source)
    # 63208f3 mirrors the graphics lifetime repair: move build_task out before
    # invoking it because the callback may publish readiness and let teardown
    # destroy this pipeline. Reverse ONLY this SHA-sealed method on the audit
    # copy before replaying the older first-use/static-sampler receipts.
    if compute_sha == 'bb9552866e26e502839eed646be9af6ea0a0db0a':
        compute_release_after = """    // The build callback publishes is_built before it returns. Cache teardown
    // may then destroy this pipeline; never access its members afterward.
    // Transfer ownership while this instance is still guaranteed alive.
    auto task = std::move(build_task);
    build_task = nullptr;
    task();
"""
        compute_release_before = """    build_task();
    build_task = nullptr;
"""
        assert compute_source.count(compute_release_after) == 1
        compute_source = compute_source.replace(
            compute_release_after, compute_release_before, 1)
        compute_sha = raster_blob(compute_source)
        assert compute_sha == '7122e9ad2d0d5e8af812223c85d0d9cdb6ae5600'
        print("ENCORE_COMPUTE_BUILD_TASK_LIFETIME_EXACT_REVERSE_PASS")
    if compute_sha == '7122e9ad2d0d5e8af812223c85d0d9cdb6ae5600':
        runbuild_after = "    build_task = std::move(func);\n    if (thread_worker) {\n#ifdef PS5_NATIVE\n        pending_first_use_compute_builds.fetch_add(1, std::memory_order_release);\n        try {\n            thread_worker->QueueWork([this] {\n                SCOPE_EXIT {\n                    pending_first_use_compute_builds.fetch_sub(1, std::memory_order_release);\n                };\n                RunBuild();\n            });\n        } catch (...) {\n            pending_first_use_compute_builds.fetch_sub(1, std::memory_order_release);\n            throw;\n        }\n        build_handed_off = true;\n#else\n        thread_worker->QueueWork([this] { RunBuild(); });\n#endif\n    } else {\n#ifdef PS5_NATIVE\n        build_handed_off = true;\n#endif\n        RunBuild();\n    }\n}\n\nvoid ComputePipeline::RunBuild() {\n    if (build_claimed.exchange(true, std::memory_order_acq_rel)) {\n        return;\n    }\n    build_task();\n    build_task = nullptr;\n}\n\n"
        runbuild_before = "    if (thread_worker) {\n#ifdef PS5_NATIVE\n        // Reserve a slot BEFORE QueueWork: a pending compute shader has\n        // priority over a speculative optimized graphics rebuild.\n        pending_first_use_compute_builds.fetch_add(1, std::memory_order_release);\n        try {\n            thread_worker->QueueWork([build = std::move(func)]() mutable {\n                SCOPE_EXIT {\n                    pending_first_use_compute_builds.fetch_sub(1, std::memory_order_release);\n                };\n                build();\n            });\n        } catch (...) {\n            pending_first_use_compute_builds.fetch_sub(1, std::memory_order_release);\n            throw;\n        }\n        build_handed_off = true;\n#else\n        thread_worker->QueueWork(std::move(func));\n#endif\n    } else {\n#ifdef PS5_NATIVE\n        // Inline func() has its own completion guard.\n        build_handed_off = true;\n#endif\n        func();\n    }\n}\n\n"
        scheduler_after = "        // Wait for the pipeline to be built\n        scheduler.Record([this](vk::CommandBuffer) {\n            RunBuild();\n"
        scheduler_before = "        // Wait for the pipeline to be built\n        scheduler.Record([this](vk::CommandBuffer) {\n"
        assert compute_source.count(runbuild_after) == 1
        assert compute_source.count(scheduler_after) == 1
        compute_source = compute_source.replace(runbuild_after, runbuild_before, 1)
        compute_source = compute_source.replace(scheduler_after, scheduler_before, 1)
        compute_sha = raster_blob(compute_source)
        assert compute_sha == '7d9fa72ce2afff5a7b1b75a05fc894b1d99ce6a2'
        print("ENCORE_FC27_COMPUTE_RUNBUILD_EXACT_REVERSE_PASS")
    if compute_sha == '7d9fa72ce2afff5a7b1b75a05fc894b1d99ce6a2':
        fixed_compute = 'const u32 secondary_offset{desc.secondary_cbuf_offset};'
        indexed_compute = 'const u32 secondary_offset{desc.secondary_cbuf_offset + index_offset};'
        assert compute_source.count(fixed_compute) == 1 and indexed_compute not in compute_source
        historical_compute = compute_source.replace(fixed_compute, indexed_compute, 1)
        assert raster_blob(historical_compute) == '53a545c32a034cfdd3421f381f354a28b306c259'
        audit_compute = temp/'normalized-vendor-fc27-static-sampler'/compute_owner
        audit_compute.parent.mkdir(parents=True, exist_ok=True)
        audit_compute.write_text(historical_compute)
        expected[compute_owner] = audit_compute
        print("ENCORE_FC27_STATIC_SAMPLER_COMPUTE_EXACT_RECEIPT_PASS")
    else:
        assert compute_sha == '53a545c32a034cfdd3421f381f354a28b306c259', compute_sha
    # Lichii f8f29b5 adds only a first-use build claim to the two pipeline
    # headers. Reverse those exact fields in the audit copy before comparing
    # with the frozen generated Vulkan tree.
    for header_name, current_blob, previous_blob in (
        ('include/video_core/renderer_vulkan/vk_graphics_pipeline.h',
         'bafff9a441a60b3dfb7e7d5a7a260741f45f59dc',
         'd49090a476f6a9bf61026331f59c9fbb1d918729'),
        ('include/video_core/renderer_vulkan/vk_compute_pipeline.h',
         'bb6f143cc66b4f1e3dd3eddc312194bd751eb91b',
         'bafd78ae572ba40ac2d3964a4df45831ae4d5e36'),
    ):
        header_source = expected[header_name].read_text()
        header_sha = raster_blob(header_source)
        if header_sha == current_blob:
            for addition in (
                '#include <functional>\n',
                '    // Lichii f8f29b5: first use may claim a queued build instead of waiting\n'
                '    // behind unrelated worker jobs.\n'
                '    void RunBuild();\n\n',
                '    std::function<void()> build_task;\n'
                '    std::atomic_bool build_claimed{false};\n',
            ):
                assert header_source.count(addition) == 1, (header_name, addition)
                header_source = header_source.replace(addition, '', 1)
            assert raster_blob(header_source) == previous_blob, header_name
            historical_header = temp/'normalized-vendor-first-use-runbuild'/header_name
            historical_header.parent.mkdir(parents=True, exist_ok=True)
            historical_header.write_text(header_source)
            expected[header_name] = historical_header
            print("ENCORE_FC27_PIPELINE_HEADER_RUNBUILD_EXACT_REVERSE_PASS", header_name)
        else:
            assert header_sha == previous_blob, (header_name, header_sha)

    # Shader IR successors #142/#145 deliberately advance the persistent
    # Vulkan cache ABI 19 -> 20 -> 21. Historical R23/P24 receipts predate
    # both changes, so normalize only this exact constant in the audit copy.
    cache_owner = 'vk_pipeline_cache_cost.cpp'
    cache_source = expected[cache_owner].read_text()
    cache_sha = raster_blob(cache_source)
    if cache_sha == 'e10c4893c03da57dce7f607d3e0af46d62e343f1':
        post_programs = "    std::array<Shader::IR::Program, Maxwell::MaxShaderProgram> programs;\n#ifdef PS5_NATIVE\n    // Eden #4503 drops known-broken non-NVIDIA fragment shaders entirely.\n    // On PS5 that visibly removes guest draws. Keep the exact predicate but\n    // route only matching programs through the newer Lichii/Eglantine\n    // broadcast/select SPIR-V fallback.\n    std::array<bool, Maxwell::MaxShaderProgram> fragment_shuffle_fallback{};\n#endif\n"
        pre_programs = "    std::array<Shader::IR::Program, Maxwell::MaxShaderProgram> programs;\n"
        post_skip = "        // Avoid native subgroup shuffle for the known PositionXY fragment\n        // pattern on non-NVIDIA drivers. Desktop/mobile preserve Eden #4503's\n        // fail-closed skip. PS5 instead uses the newer upstream broadcast\n        // fallback so the whole guest draw is not silently discarded.\n        if (device.GetDriverID() != VK_DRIVER_ID_NVIDIA_PROPRIETARY &&\n            Shader::Optimization::HasBrokenPattern(programs[index])) {\n#ifdef PS5_NATIVE\n            fragment_shuffle_fallback[index] = true;\n            LOG_WARNING(Render_Vulkan,\n                        \"0x{:016x}: using PS5 fragment shuffle fallback\",\n                        key.unique_hashes[index]);\n#else\n            LOG_WARNING(Render_Vulkan,\n                        \"0x{:016x}: skipping fragment shuffle with known driver issue\",\n                        key.unique_hashes[index]);\n            return nullptr;\n#endif\n        }"
        pre_skip = "        // Avoid compiling a known-broken fragment shuffle sourced from\n        // PositionXY on non-NVIDIA drivers (notably RADV/RDNA2). Recognize\n        // the IR pattern, not a broad title or vendor blacklist.\n        if (device.GetDriverID() != VK_DRIVER_ID_NVIDIA_PROPRIETARY &&\n            Shader::Optimization::HasBrokenPattern(programs[index])) {\n            LOG_WARNING(Render_Vulkan,\n                        \"0x{:016x}: skipping fragment shuffle with known driver issue\",\n                        key.unique_hashes[index]);\n            return nullptr;\n        }"
        post_emit = "        auto emit_profile = profile;\n#ifdef PS5_NATIVE\n        emit_profile.has_broken_spirv_fragment_shuffle = fragment_shuffle_fallback[index];\n#endif\n        const std::vector<u32> code{([&] { auto cost = Eden::Performance::VulkanTimer(22); ::Eden::Performance::CachePhaseTimer stage_cost{::Eden::Performance::CachePhase::ShaderSpirv, ::Eden::Performance::detailed_gpu_profile.load(std::memory_order_relaxed)}; return EmitSPIRV(emit_profile, runtime_info, program, binding); }())};"
        pre_emit = "        const std::vector<u32> code{([&] { auto cost = Eden::Performance::VulkanTimer(22); ::Eden::Performance::CachePhaseTimer stage_cost{::Eden::Performance::CachePhase::ShaderSpirv, ::Eden::Performance::detailed_gpu_profile.load(std::memory_order_relaxed)}; return EmitSPIRV(profile, runtime_info, program, binding); }())};"
        assert cache_source.count(post_programs) == cache_source.count(post_skip) == cache_source.count(post_emit) == 1
        cache_source = cache_source.replace(post_programs, pre_programs, 1)
        cache_source = cache_source.replace(post_skip, pre_skip, 1)
        cache_source = cache_source.replace(post_emit, pre_emit, 1)
        cache_sha = raster_blob(cache_source)
        assert cache_sha == 'be5d48abd44996502b0829a6e0501d130a151455', 'fragment-shuffle predecessor drift'
        print("ENCORE_FC27_FRAGMENT_SHUFFLE_EXACT_RECEIPT_PASS")
    if cache_sha == 'be5d48abd44996502b0829a6e0501d130a151455':
        assert cache_source.count('constexpr u32 CACHE_VERSION = 21;') == 1
        historical_cache = cache_source.replace('constexpr u32 CACHE_VERSION = 21;',
                                                'constexpr u32 CACHE_VERSION = 19;', 1)
        assert raster_blob(historical_cache) == '6efe1b10862135056c1df1b78007a1c9cb5a9610'
        audit_cache = temp/'normalized-vendor-fc27-static-sampler'/cache_owner
        audit_cache.parent.mkdir(parents=True, exist_ok=True)
        audit_cache.write_text(historical_cache)
        expected[cache_owner] = audit_cache
        print("ENCORE_FC27_CACHE_VERSION_EXACT_RECEIPT_PASS version=21 historical=19")
    else:
        assert cache_sha == '6efe1b10862135056c1df1b78007a1c9cb5a9610', cache_sha
    # Two intentional native-only sources are not generator outputs:
    # a synchronization helper and the F07 Vulkan allocator OOM diagnostics.
    # All generated Vulkan translation units still remain byte-identical.
    helper='include/video_core/renderer_vulkan/striped_wait.h'
    allocator='vulkan_memory_allocator.cpp'
    # Shared native GPU budget admission owner, usable by both NS1 and NS2.
    # It is additive, never regenerated from the original upstream Vulkan.
    pool_policy='include/video_core/renderer_vulkan/vk_shared_gpu_budget.h'
    # A common NS1/NS2 SPIR-V reflection primitive. The generator owns both
    # call sites, but this standalone header has no upstream equivalent.
    storage_layout='include/video_core/renderer_vulkan/vk_compute_storage_layout.h'
    assert storage_layout not in actual, 'common storage layout falsely regenerated'
    assert subprocess.check_output(
        ['git','hash-object',str(expected[storage_layout])],text=True
    ).strip() == 'f1cb4c7d91a30c56d55807ae62d796702ad1362f', (
        'common compute reflection owner drift')
    assert pool_policy not in actual, 'native GPU budget leaked into generator'
    assert subprocess.check_output(
        ['git','hash-object',str(expected[pool_policy])],text=True
    ).strip() == '85cc400399ee8daf82037dfc0f070d3d66eebb68', 'shared GPU policy drift'
    oom_check = subprocess.run(
        [sys.executable, '-B', str(root/'tools/check-ps5-vulkan-oom-source.py')],
        timeout=15, capture_output=True, text=True)
    if oom_check.returncode != 0:
        raise RuntimeError('F07 allocator source parity failed (code %d):\n%s\n%s' % (
            oom_check.returncode, oom_check.stdout, oom_check.stderr))
    assert allocator not in actual, 'generated Vulkan port unexpectedly owns the allocator'
    # The native Task/Mesh device extension header is a genuine maintained
    # header; require exact two-hunk parity with the pinned vendor snapshot.
    native_mesh_device_header='include/video_core/vulkan_common/vulkan_device.h'
    assert native_mesh_device_header not in actual
    mesh_device = expected[native_mesh_device_header].read_text()
    mesh_feature_line = "    FEATURE(EXT, MeshShader, MESH_SHADER, mesh_shader)                                             \\\n"
    mesh_feature_method = "    /// Returns true if the device supports task and mesh shaders (VK_EXT_mesh_shader).\n    bool IsExtMeshShaderSupported() const {\n        return extensions.mesh_shader && features.mesh_shader.taskShader &&\n               features.mesh_shader.meshShader;\n    }\n\n"
    # The N58 sparse-residency header is an independently reviewed
    # additive feature. Our single Vulkan Device ABI must retain BOTH that
    # feature and Task/Mesh. Prove both deltas against immutable Eden.
    pinned_device = (upstream/'src/video_core/vulkan_common/vulkan_device.h').read_text()
    sparse_device = (root/'vendor/encore-active/ns2-helpers/include/video_core/vulkan_common/vulkan_device.h').read_text()
    sparse_start = sparse_device.index('    // N58: image sparse residency')
    sparse_end = sparse_device.index('    /// Returns true for tile-based deferred renderers.', sparse_start)
    sparse_delta = sparse_device[sparse_start:sparse_end]
    assert sparse_device.count(sparse_delta) == 1 and sparse_device.replace(sparse_delta, '') == pinned_device, (
        "N58 source ABI must be a complete exact additive sparse residency guard")
    assert mesh_device.count(mesh_feature_line) == 1
    assert mesh_device.count(mesh_feature_method) == 1
    assert mesh_device.count(sparse_delta) == 1, (
        "Native Task/Mesh device header lost the sparse residency method")
    # GPU-47 adds only Vulkan's three framebuffer-limit getters to the
    # already reviewed combined Device ABI. Reverse those exact lines on the
    # audit text before applying the frozen R23 combined-blob receipt.
    gpu47_device_current='e20048f23ab416706ea6bad55bb863022e4d505f'
    gpu47_device_predecessor='acab7cf039c2be7bcc830ac684be2fff285a3e8a'
    mesh_device_blob=_blob_text(mesh_device)
    if mesh_device_blob == gpu47_device_current:
        old_tail="    FN_MAX_LIMIT_ELEM(DescriptorSetInputAttachments)\n"
        new_tail=(
            "    FN_MAX_LIMIT_ELEM(DescriptorSetInputAttachments) \\\n"
            "    FN_MAX_LIMIT_ELEM(FramebufferWidth) \\\n"
            "    FN_MAX_LIMIT_ELEM(FramebufferHeight) \\\n"
            "    FN_MAX_LIMIT_ELEM(FramebufferLayers)\n"
        )
        assert mesh_device.count(new_tail)==1, "GPU-47 Device limit-list drift"
        mesh_device=mesh_device.replace(new_tail,old_tail,1)
        assert _blob_text(mesh_device)==gpu47_device_predecessor, (
            "GPU-47 Device reversal did not restore combined predecessor")
        print("ENCORE_NS1_GPU47_VULKAN_DEVICE_EXACT_REVERSE_PASS",flush=True)
    else:
        assert mesh_device_blob==gpu47_device_predecessor, (
            "Unexpected GPU-47 Device owner",mesh_device_blob)
    # Combined R23 EDS3 + subgroup + mesh + sparse-residency ABI is now a
    # maintained source blob, not only the two-hunk original Task/Mesh delta.
    combined_device_sha = gpu47_device_predecessor
    assert _blob_text(mesh_device) == combined_device_sha, (
        'Reviewed R23 combined Vulkan Device ABI blob drift')
    assert mesh_device.count('GetMaxSubgroupSize() const') == 1
    assert mesh_device.count('IsExtDepthClipEnableSupported() const') == 1
    # The immutable upstream generator owns the historic Vulkan ports, not
    # post-generator R09 neural shaders/owners, FSR31 and native additions.
    # Pin the *exact* 241-path additive inventory rather than ignoring
    # unexpected extras or pretending they were generated from Eden upstream.
    additive_manifest = root / 'tools/vendor-vulkan-native-additions.txt'
    approved_native_additions = {
        row.strip()
        for row in additive_manifest.read_text(encoding='utf-8').splitlines()
        if row.strip() and not row.lstrip().startswith('#')
    }
    assert len(approved_native_additions) == 241, (
        'Reviewed native additive inventory count changed',
        len(approved_native_additions))
    assert not set(actual) - set(expected), (
        'Generator emitted a Vulkan file absent from the active vendor',
        sorted(set(actual) - set(expected)))
    # R2 and R09 maintained native additions are admitted only when the
    # source-owner marker exists, independent of the vendor gitlink's commit
    # SHA. Individual file blob hashes, the core owner hash and the complete
    # additive inventory are still checked below. This accepts reviewed
    # follow-up vendor commits without silently accepting new Vulkan files.
    r2_marker = 'include/video_core/renderer_vulkan/ns2_staging_upload_bounds.h'
    r2_production = r2_marker in expected
    if r2_production:
        r2_extra = {
            'include/video_core/renderer_vulkan/ns2_staging_upload_bounds.h':
                '8905d42732b2d5848aa49b5800340e031cd214c9',
            'include/video_core/renderer_vulkan/ns2_gpu_retirement_hold.h':
                '33e077863e503a956cabf2b99edb73f8967b89a8',
            'include/video_core/renderer_vulkan/ns2_verified_upload_batch.h':
                'b12cc0489ebbb463b4ec9e4c39b2d2be41ab2376',
            'include/video_core/renderer_vulkan/vk_staging_buffer_pool.h':
                '10693299137d1d36aace5a2399f20ba3bbf4e49c',
            'tests/test_ns2_verified_upload_batch.cpp':
                '2bb3d3389565f06c7eb2ea46a57acae06c28c53a',
            'tests/test_ns2_gpu_retirement_hold.cpp':
                '0de5c2e112ce21a9736031879830ff377ba7f307',
            'tests/test_ns2_cache_shutdown_order.cpp':
                '472860e5ddc853197ec79b63d16800daffa372cc',
            'vk_staging_buffer_pool.cpp':
                '22cc2218f0ea78daee968dee275a2560e58e3930',
        }
        for name, sha in r2_extra.items():
            assert subprocess.check_output(
                ['git', 'hash-object', str(expected[name])],
                text=True).strip() == sha, ('R2 research-only source blob drift', name)
        approved_native_additions |= set(r2_extra)
        # R09 native additions belong to this single production vendor pin.
        # Verify each exact blob; preserve the immutable 241-path generator list.
        r09_extra = {
                  "include/rdna2_nr_fswin_scratch_pool_policy.h": "091b9734e93e33478d58a20a111d7a3be4b016e0",
                  "include/rdna2_nr_vit_min_pool_policy.h": "75354460bd4857229d86e023c0e620dd33d47787",
                  "include/video_core/renderer_vulkan/nr_rdna2_readback_dimensions.h": "9175c9ec02a5bf2a4990f2c8f1a175cabd52de61",
                  "r09_rdna2_nr/vit_attention_tiled_min_rdna2.comp": "239ac76328be0170905e6fea999910f3a7e453c7"
        }
        for name, blob in r09_extra.items():
            assert subprocess.check_output(
                ['git', 'hash-object', str(expected[name])], text=True
            ).strip() == blob, ('R09 maintained native additional owner drift', name)
        approved_native_additions |= set(r09_extra)
        if 'blit_image.cpp' in expected:
            # Keep DrawTexture's independently reviewed two-file receipt
            # applicable across vendor commits; exact blob seals below remain
            # mandatory for both added owners.
            drawtexture_extra = {
                'blit_image.cpp': 'bbde031a184b93745fa0449aef74f351355fb70d',
                'include/video_core/renderer_vulkan/blit_image.h':
                    '81eda086f50e04d3e1537aebff404a6097a07069',
            }
            for name, blob in drawtexture_extra.items():
                assert subprocess.check_output(
                    ['git', 'hash-object', str(expected[name])], text=True
                ).strip() == blob, ('Eden #4559 maintained DrawTexture owner drift', name)
            approved_native_additions |= set(drawtexture_extra)
        core_owner = root / 'vendor/encore-active/eden-core/src/video_core/buffer_cache/buffer_cache.h'
        core_blob = subprocess.check_output(
            ['git', 'hash-object', str(core_owner)], text=True).strip()
        # Lichii #1328: verify the only C++ template-signature delta before
        # replaying the unchanged native BufferCache historical source seal.
        # Applicability follows exact source-owner blobs, never a moving vendor
        # gitlink. This keeps old reviewed variants valid while newer NS1/NS2
        # commits that do not edit these owners cannot break the audit chain.
        base_owner = root / 'vendor/encore-active/eden-core/src/video_core/buffer_cache/buffer_cache_base.h'
        base_blob = subprocess.check_output(
            ['git', 'hash-object', str(base_owner)], text=True).strip()
        # Vendor 7acfc6be repairs channel-owned bindings on deletion.
        # Reverse ONLY this exact method on the historical audit copy.
        # The real multi-channel scrub remains compiled unchanged.
        selected = core_owner.read_text()
        if actual_vendor_pin in {"57be62ed6bcc872a850676f92f55de92ace7a290", "334915ab48a2beb33a5eb0639c5f2b8dd554fcae", "2adfca5489b3f107847e0a1a9cdc06e497fc656f", "a47b6b20a8e7b7db748a82610a9b08685ba03eeb", "4b63376eb7057015d70295ecd7df4ce96be80607"} and core_blob == "30e7c389851a5a0f2b6369c35a313f93a0fc6826":
            # FC27 successor: reverse ONLY the nine idempotent BufferCache
            # fast-guards on the audit copy. The compiled source remains
            # untouched; reconstructed bytes must equal the reviewed 8d3
            # predecessor before the existing historical chain continues.
            for newer, older in (
                ("void BufferCache<P>::BindHostStageBuffers(size_t stage) {\n    BindHostGraphicsUniformBuffers(stage);\n    if (channel_state->enabled_storage_buffers[stage] != 0) {\n        BindHostGraphicsStorageBuffers(stage);\n    }\n    if (channel_state->enabled_texture_buffers[stage] != 0) {\n        BindHostGraphicsTextureBuffers(stage);\n    }\n}", "void BufferCache<P>::BindHostStageBuffers(size_t stage) {\n    BindHostGraphicsUniformBuffers(stage);\n    BindHostGraphicsStorageBuffers(stage);\n    BindHostGraphicsTextureBuffers(stage);\n}"),
                ("void BufferCache<P>::BindHostComputeBuffers() {\n    BindHostComputeUniformBuffers();\n    if (channel_state->enabled_compute_storage_buffers != 0) {\n        BindHostComputeStorageBuffers();\n    }\n    if (channel_state->enabled_compute_texture_buffers != 0) {\n        BindHostComputeTextureBuffers();\n    }", "void BufferCache<P>::BindHostComputeBuffers() {\n    BindHostComputeUniformBuffers();\n    BindHostComputeStorageBuffers();\n    BindHostComputeTextureBuffers();"),
                ("void BufferCache<P>::SetUniformBuffersState(const std::array<u32, NUM_STAGES>& mask,\n                                            const UniformBufferSizes* sizes) {\n    if (channel_state->enabled_uniform_buffer_masks == mask &&\n        channel_state->uniform_buffer_sizes == sizes) [[likely]] {\n        return;\n    }\n    if (channel_state->enabled_uniform_buffer_masks != mask) {", "void BufferCache<P>::SetUniformBuffersState(const std::array<u32, NUM_STAGES>& mask,\n                                            const UniformBufferSizes* sizes) {\n    if (channel_state->enabled_uniform_buffer_masks != mask) {"),
                ("void BufferCache<P>::UnbindGraphicsStorageBuffers(size_t stage) {\n    if (channel_state->enabled_storage_buffers[stage] == 0) {\n        return;\n    }\n    if constexpr", "void BufferCache<P>::UnbindGraphicsStorageBuffers(size_t stage) {\n    if constexpr"),
                ("void BufferCache<P>::UnbindGraphicsTextureBuffers(size_t stage) {\n    if (channel_state->enabled_texture_buffers[stage] == 0) {\n        return;\n    }\n    channel_state->enabled_texture_buffers[stage] = 0;", "void BufferCache<P>::UnbindGraphicsTextureBuffers(size_t stage) {\n    channel_state->enabled_texture_buffers[stage] = 0;"),
                ("void BufferCache<P>::DisableGraphicsUniformBuffer(size_t stage, u32 index) {\n    auto& current = channel_state->uniform_buffers[stage][index];\n    if (current.device_addr == 0 && current.size == 0 && !current.buffer_id) [[likely]] {\n        return;\n    }\n    current = NULL_BINDING;\n}", "void BufferCache<P>::DisableGraphicsUniformBuffer(size_t stage, u32 index) {\n    channel_state->uniform_buffers[stage][index] = NULL_BINDING;\n}"),
                ("void BufferCache<P>::UpdateUniformBuffers(size_t stage) {\n    if (channel_state->enabled_uniform_buffer_masks[stage] == 0) [[likely]] {\n        return;\n    }\n    ForEachEnabledBit", "void BufferCache<P>::UpdateUniformBuffers(size_t stage) {\n    ForEachEnabledBit"),
                ("void BufferCache<P>::UpdateStorageBuffers(size_t stage) {\n    if (channel_state->enabled_storage_buffers[stage] == 0) [[likely]] {\n        return;\n    }\n    ForEachEnabledBit", "void BufferCache<P>::UpdateStorageBuffers(size_t stage) {\n    ForEachEnabledBit"),
                ("void BufferCache<P>::UpdateTextureBuffers(size_t stage) {\n    if (channel_state->enabled_texture_buffers[stage] == 0) [[likely]] {\n        return;\n    }\n    ForEachEnabledBit", "void BufferCache<P>::UpdateTextureBuffers(size_t stage) {\n    ForEachEnabledBit"),
            ):
                assert selected.count(newer) == 1, ("FC27 BufferCache fast-guard span drift", newer[:80])
                selected = selected.replace(newer, older, 1)
            raw = selected.encode("utf-8")
            core_blob = hashlib.sha1(
                b"blob " + str(len(raw)).encode() + bytes([0]) + raw
            ).hexdigest()
            assert core_blob == "4577de4f63bc0393a1e14e89534d6f8aedf50d67", ("FC27 BufferCache predecessor drift", core_blob)
            restored = temp / "normalized-fc27-buffer-fast-guards" / "buffer_cache.h"
            restored.parent.mkdir(parents=True, exist_ok=True)
            restored.write_text(selected)
            core_owner = restored
            print("ENCORE_FC27_BUFFERCACHE_FAST_GUARDS_EXACT_REVERSE_PASS", "guards=9")
        if core_blob == "4577de4f63bc0393a1e14e89534d6f8aedf50d67":
            # Exact inverse of the reviewed bounded GC batching change on the audit copy only.
            newer, older = "void BufferCache<P>::RunGarbageCollector() {\n    const bool aggressive_gc = total_used_memory >= critical_memory;\n    const u64 ticks_to_destroy = aggressive_gc ? 60 : 120;\n#ifdef PS5_NATIVE\n    // Before a buffer reaches the GC age, subtracting from this unsigned\n    // frame tick wraps to a huge LRU threshold. On startup/pressure bursts\n    // that wrongly evicts young buffers and can force guest downloads.\n    if (frame_tick < ticks_to_destroy) {\n        return;\n    }\n#endif\n#ifdef PS5_NATIVE\n    if constexpr (USE_MEMORY_MAPS && !IS_OPENGL) {\n        // Lichii batches GC readbacks rather than finishing the GPU once\n        // per dirty eviction. Keep the existing LRU age and eviction count.\n        constexpr u64 staging_budget = 16ULL * 1024 * 1024;\n        constexpr size_t max_regions = 4096;\n        std::array<BufferId, 64> candidates{};\n        size_t candidate_count = 0;\n        const size_t limit = aggressive_gc ? 64 : 32;\n        lru_cache.ForEachItemBelow(frame_tick - ticks_to_destroy, [&](BufferId id) {\n            if (candidate_count == limit) return true;\n            candidates[candidate_count++] = id;\n            return false;\n        });\n        struct Download {\n            BufferId id;\n            BufferCopy copy;\n        };\n        const auto download_batch = [&](std::span<const BufferId> ids) {\n            boost::container::small_vector<Download, 16> downloads;\n            u64 total = 0;\n            bool oversized = false;\n            for (const BufferId id : ids) {\n                const auto& buffer = slot_buffers[id];\n                // Plan without clearing GPU ownership. A staging allocation\n                // failure must leave the original buffers readable.\n                memory_tracker.ForEachDownloadRange(\n                    buffer.CpuAddr(), buffer.SizeBytes(), false,\n                    [&](u64 start, u64 bytes) {\n                        if (oversized) return;\n                        gpu_modified_ranges.ForEachInRange(start, bytes,\n                            [&](DAddr first, DAddr end) {\n                                if (oversized) return;\n                                const u64 size = end - first;\n                                if (size > staging_budget ||\n                                    downloads.size() == max_regions) {\n                                    oversized = true;\n                                    return;\n                                }\n                                const u64 aligned = (size + 63) & ~u64{63};\n                                if (aligned > staging_budget - total) {\n                                    oversized = true;\n                                    return;\n                                }\n                                downloads.push_back({id, BufferCopy{\n                                    .src_offset = first - buffer.CpuAddr(),\n                                    .dst_offset = total,\n                                    .size = size,\n                                }});\n                                total += aligned;\n                            });\n                    });\n                if (oversized) break;\n            }\n            if (oversized) {\n                // Do not grow the new batch's staging or metadata without\n                // bound. The existing single-buffer path handles rare large\n                // or highly fragmented evictions with its original contract.\n                for (const BufferId id : ids) {\n                    DownloadBufferMemory(slot_buffers[id]);\n                    DeleteBuffer(id);\n                }\n                return;\n            }\n            if (total) {\n                // Catch only allocation failure, before recording GPU copies.\n                // A failed retirement is not a recoverable allocation error.\n                std::optional<decltype(runtime.DownloadStagingBuffer(total))> staging;\n                try {\n                    staging.emplace(runtime.DownloadStagingBuffer(total));\n                } catch (const std::bad_alloc&) {\n                    return;\n                }\n                runtime.PreCopyBarrier();\n                for (size_t first = 0; first < downloads.size();) {\n                    const BufferId id = downloads[first].id;\n                    auto& buffer = slot_buffers[id];\n                    std::array<BufferCopy, 8> copies{};\n                    size_t count = 0;\n                    do {\n                        auto copy = downloads[first++].copy;\n                        copy.dst_offset += staging->offset;\n                        buffer.MarkUsage(copy.src_offset, copy.size);\n                        copies[count++] = copy;\n                    } while (first < downloads.size() && count < copies.size() &&\n                             downloads[first].id == id);\n                    runtime.CopyBuffer(staging->buffer, buffer,\n                        std::span<const BufferCopy>{copies.data(), count}, false);\n                }\n                runtime.PostCopyBarrier();\n                runtime.Finish();\n                // Keep the established pending CPU-write protection. Sample\n                // after retirement so writes queued during the wait are visible.\n                const auto cpu_written = PendingCpuWriteRanges();\n                for (const auto& download : downloads) {\n                    const auto& copy = download.copy;\n                    const auto& buffer = slot_buffers[download.id];\n                    WriteDownloadedMemory(cpu_written, buffer.CpuAddr() + copy.src_offset,\n                        staging->mapped_span.data() + copy.dst_offset, copy.size);\n                }\n            }\n            // Publish ownership only after every readback in this batch\n            // completed. Buffer allocations are page-aligned and disjoint.\n            for (const BufferId id : ids) {\n                auto& buffer = slot_buffers[id];\n                memory_tracker.ForEachDownloadRangeAndClear(\n                    buffer.CpuAddr(), buffer.SizeBytes(), [&](u64 start, u64 bytes) {\n                        ClearDownload(start, bytes);\n                        gpu_modified_ranges.Subtract(start, bytes);\n                    });\n                DeleteBuffer(id);\n            }\n        };\n        // Bound the nominal batch by the owners' sizes; the planner above\n        // independently caps the actual aligned readback size and region count.\n        for (size_t first = 0; first < candidate_count;) {\n            size_t end = first;\n            u64 bytes = 0;\n            do {\n                const u64 size = slot_buffers[candidates[end]].SizeBytes();\n                if (end != first && (bytes >= staging_budget ||\n                                     size > staging_budget - bytes)) break;\n                bytes += size;\n                ++end;\n            } while (end < candidate_count);\n            download_batch(std::span<const BufferId>{candidates.data() + first, end - first});\n            first = end;\n        }\n        return;\n    }\n#endif\n    int num_iterations = aggressive_gc ? 64 : 32;\n    const auto clean_up = [this, &num_iterations](BufferId buffer_id) {\n        if (num_iterations == 0) {\n            return true;\n        }\n        --num_iterations;\n        auto& buffer = slot_buffers[buffer_id];\n        DownloadBufferMemory(buffer);\n        DeleteBuffer(buffer_id);\n        return false;\n    };\n    lru_cache.ForEachItemBelow(frame_tick - ticks_to_destroy, clean_up);\n}\n\n", "void BufferCache<P>::RunGarbageCollector() {\n    const bool aggressive_gc = total_used_memory >= critical_memory;\n    const u64 ticks_to_destroy = aggressive_gc ? 60 : 120;\n#ifdef PS5_NATIVE\n    // Before a buffer reaches the GC age, subtracting from this unsigned\n    // frame tick wraps to a huge LRU threshold. On startup/pressure bursts\n    // that wrongly evicts young buffers and can force guest downloads.\n    if (frame_tick < ticks_to_destroy) {\n        return;\n    }\n#endif\n    int num_iterations = aggressive_gc ? 64 : 32;\n    const auto clean_up = [this, &num_iterations](BufferId buffer_id) {\n        if (num_iterations == 0) {\n            return true;\n        }\n        --num_iterations;\n        auto& buffer = slot_buffers[buffer_id];\n        DownloadBufferMemory(buffer);\n        DeleteBuffer(buffer_id);\n        return false;\n    };\n    lru_cache.ForEachItemBelow(frame_tick - ticks_to_destroy, clean_up);\n}\n\n"
            assert selected.count(newer) == 1, "BufferCache successor drift"
            selected = selected.replace(newer, older, 1)
            raw = selected.encode("utf-8")
            core_blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
            assert core_blob == "0ecca19b38d4d40ce03e4f9392c5b6ef042e1e86", core_blob
        if core_blob == "0ecca19b38d4d40ce03e4f9392c5b6ef042e1e86":
            # Exact inverse of the reviewed per-owner synchronous download change on the audit copy only.
            newer, older = "void BufferCache<P>::DownloadMemory(DAddr device_addr, u64 size) {\n    // The cache page table covers 16 GiB of guest physical memory.\n    constexpr DAddr address_limit = DAddr{1} << 34;\n    if (!size || device_addr >= address_limit || size > address_limit - device_addr) {\n        return;\n    }\n    const DAddr end_addr = device_addr + size;\n    ForEachBufferInRange(device_addr, size, [&](BufferId, Buffer& buffer) {\n        // The memory tracker is shared across buffers. Never clear or copy\n        // another buffer's GPU-written pages using this buffer's offsets.\n        // Match Lichii's per-owner intersection before the destructive readback.\n        const DAddr start = (std::max)(device_addr, buffer.CpuAddr());\n        const DAddr end = (std::min)(end_addr, buffer.CpuAddr() + buffer.SizeBytes());\n        if (start < end) {\n            DownloadBufferMemory(buffer, start, end - start);\n        }\n    });\n}\n", "void BufferCache<P>::DownloadMemory(DAddr device_addr, u64 size) {\n    ForEachBufferInRange(device_addr, size, [&](BufferId, Buffer& buffer) {\n        DownloadBufferMemory(buffer, device_addr, size);\n    });\n}\n"
            assert selected.count(newer) == 1, "BufferCache successor drift"
            selected = selected.replace(newer, older, 1)
            raw = selected.encode("utf-8")
            core_blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
            assert core_blob == "24323ea00c4088d45d5357a6df5382a7447669ab", core_blob
        if core_blob == "24323ea00c4088d45d5357a6df5382a7447669ab":
            newer, older = "    // Adjacent download regions from the same source buffer share the\n    // already-established transfer barriers. Their staging offsets are\n    // distinct, and no guest draw or fence is recorded between these copies.\n    // Bound each batch to the Vulkan runtime's inline copy-vector capacity:\n    // this removes repeated scheduler callbacks without adding heap work\n    // under BufferCache::mutex or changing normalized readback ownership.\n    for (size_t first = 0; first < downloads.size();) {\n        const BufferId buffer_id = downloads[first].second;\n        Buffer& buffer = slot_buffers[buffer_id];\n        std::array<BufferCopy, 8> copies{};\n        size_t count = 0;\n        do {\n            auto& copy = downloads[first].first;\n            copy.dst_offset += download_staging.offset;\n            BufferCopy second_copy{copy};\n            second_copy.src_offset = static_cast<size_t>(buffer.CpuAddr()) + copy.src_offset;\n            const DAddr orig_device_addr = static_cast<DAddr>(second_copy.src_offset);\n            async_downloads.Add(orig_device_addr, copy.size);\n            buffer.MarkUsage(copy.src_offset, copy.size);\n            copies[count++] = copy;\n            normalized_copies.push_back(second_copy);\n            ++first;\n        } while (first < downloads.size() && count < copies.size() &&\n                 downloads[first].second == buffer_id);\n        runtime.CopyBuffer(download_staging.buffer, buffer,\n                           std::span<const BufferCopy>{copies.data(), count}, false);\n    }", "    for (auto& [copy, buffer_id] : downloads) {\n        copy.dst_offset += download_staging.offset;\n        const std::array copies{copy};\n        BufferCopy second_copy{copy};\n        Buffer& buffer = slot_buffers[buffer_id];\n        second_copy.src_offset = static_cast<size_t>(buffer.CpuAddr()) + copy.src_offset;\n        const DAddr orig_device_addr = static_cast<DAddr>(second_copy.src_offset);\n        async_downloads.Add(orig_device_addr, copy.size);\n        buffer.MarkUsage(copy.src_offset, copy.size);\n        runtime.CopyBuffer(download_staging.buffer, buffer, copies, false);\n        normalized_copies.push_back(second_copy);\n    }"
            assert selected.count(newer) == 1, "Fence readback batching successor drift"
            selected = selected.replace(newer, older, 1)
            raw = selected.encode("utf-8")
            core_blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
            assert core_blob == "fce19742529b21bca0f92f3f67c4e420dcd493c7"
        if core_blob == "fce19742529b21bca0f92f3f67c4e420dcd493c7":
            # Historical reconstruction only: review and reverse the exact
            # readback publication fast path before older source witnesses.
            successor = "    if (size == 0) {\n        return;\n    }\n#ifdef PS5_NATIVE\n    // Lichii: completed GPU readback may land directly when no newer CPU\n    // write overlaps. Avoid a temporary RangeSet/subtractions for every\n    // uncontended download while the BufferCache mutex is held.\n    // Intersects fails closed on invalid or overflowing spans.\n    if (!cpu_written.Intersects(device_addr, size)) {\n        device_memory.WriteBlockUnsafe(device_addr, data, size);\n        return;\n    }\n#endif\n"
            assert selected.count(successor) == 1, "FC27 readback owner drift"
            selected = selected.replace(successor, "", 1)
            raw = selected.encode("utf-8")
            core_blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
            assert core_blob == "4ce33d21debc33c9625129cbd545bf9b1c084272", core_blob
        if core_blob == "4ce33d21debc33c9625129cbd545bf9b1c084272":
            successor = "#ifdef PS5_NATIVE\n    // Native RangeSet owner is selected together with this BufferCache.\n    // Avoid walking every fragmented GPU-written interval under the cache mutex.\n    return gpu_modified_ranges.Intersects(addr, size);\n#else\n    bool is_dirty = false;\n    gpu_modified_ranges.ForEachInRange(addr, size, [&](DAddr, DAddr) { is_dirty = true; });\n    return is_dirty;\n#endif"
            predecessor = "    bool is_dirty = false;\n    gpu_modified_ranges.ForEachInRange(addr, size, [&](DAddr, DAddr) { is_dirty = true; });\n    return is_dirty;"
            assert selected.count(successor) == 1
            selected = selected.replace(successor, predecessor, 1)
            raw = selected.encode("utf-8")
            core_blob = __import__("hashlib").sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
            assert core_blob == "7f07e392ea0cc828d862da29d32ada1ebc3966aa"
        if core_blob == "7f07e392ea0cc828d862da29d32ada1ebc3966aa":
            reviewed = "void BufferCache<P>::DeleteBuffer(BufferId buffer_id, bool do_not_mark) {\n    if constexpr (requires { runtime.OnBufferDeleted(slot_buffers[buffer_id]); }) {\n        runtime.OnBufferDeleted(slot_buffers[buffer_id]);\n    }\n    const auto scalar_replace = [buffer_id](Binding& binding) {\n        if (binding.buffer_id == buffer_id) {\n            binding.buffer_id = BufferId{};\n        }\n    };\n    const auto replace = [scalar_replace](auto& bindings) {\n        std::ranges::for_each(bindings, scalar_replace);\n    };\n\n    // Bindings are channel-owned. A deleted slot left in an inactive channel\n    // can be reused by a new buffer while the old address/offset survives,\n    // causing stale uniforms, texture buffers or indirect data after a switch.\n    const auto scrub_channel = [&](BufferCacheChannelInfo& channel) {\n        auto& flags = channel.maxwell3d.dirty.flags;\n        if (channel.index_buffer.buffer_id == buffer_id) {\n            channel.index_buffer.buffer_id = BufferId{};\n            flags[Dirty::IndexBuffer] = true;\n        }\n        for (u32 index = 0; index < channel.vertex_buffers.size(); ++index) {\n            auto& binding = channel.vertex_buffers[index];\n            if (binding.buffer_id != buffer_id) {\n                continue;\n            }\n            binding.buffer_id = BufferId{};\n            if (&channel == channel_state) {\n                UpdateVertexBufferSlot(index, binding);\n            }\n            flags[Dirty::VertexBuffers] = true;\n            flags[Dirty::VertexBuffer0 + index] = true;\n        }\n        std::ranges::for_each(channel.uniform_buffers, replace);\n        std::ranges::for_each(channel.storage_buffers, replace);\n        std::ranges::for_each(channel.texture_buffers, replace);\n        replace(channel.transform_feedback_buffers);\n        scalar_replace(channel.count_buffer_binding);\n        scalar_replace(channel.indirect_buffer_binding);\n        replace(channel.compute_uniform_buffers);\n        replace(channel.compute_storage_buffers);\n        replace(channel.compute_texture_buffers);\n        if constexpr (HAS_PERSISTENT_UNIFORM_BUFFER_BINDINGS) {\n            channel.dirty_uniform_buffers.fill(~u32{0});\n            channel.uniform_buffer_binding_sizes.fill({});\n        }\n        channel.has_deleted_buffers = true;\n    };\n\n    scrub_channel(*channel_state);\n    for (const size_t channel_id : active_channel_ids) {\n        auto& channel = channel_storage[channel_id];\n        if (&channel != channel_state) {\n            scrub_channel(channel);\n        }\n    }\n\n    // Mark the whole buffer as CPU written to stop tracking CPU writes\n    if (!do_not_mark) {\n        Buffer& buffer = slot_buffers[buffer_id];\n        memory_tracker.MarkRegionAsCpuModified(buffer.CpuAddr(), buffer.SizeBytes());\n    }\n\n    Unregister(buffer_id);\n\n#ifdef YUZU_LEGACY\n    if (!do_not_mark || !immediately_free) {\n#endif\n#if defined(PS5_NATIVE) && defined(EDEN_NS2_STAGE_BACKING)\n        // R2 only: do not reclaim a deleted Vulkan owner by frame age.\n        // The runtime owns the moved Buffer until real GPU completion.\n        if constexpr (!P::IS_OPENGL) {\n            runtime.RetainDeletedBuffer(slot_buffers[buffer_id]);\n        } else {\n            delayed_destruction_ring.Push(std::move(slot_buffers[buffer_id]));\n        }\n#else\n        delayed_destruction_ring.Push(std::move(slot_buffers[buffer_id]));\n#endif\n#ifdef YUZU_LEGACY\n    }\n#endif\n\n    slot_buffers.erase(buffer_id);\n}"
            prior = "void BufferCache<P>::DeleteBuffer(BufferId buffer_id, bool do_not_mark) {\n    if constexpr (requires { runtime.OnBufferDeleted(slot_buffers[buffer_id]); }) {\n        runtime.OnBufferDeleted(slot_buffers[buffer_id]);\n    }\n    bool dirty_index{false};\n    boost::container::small_vector<u64, NUM_VERTEX_BUFFERS> dirty_vertex_buffers;\n    const auto scalar_replace = [buffer_id](Binding& binding) {\n        if (binding.buffer_id == buffer_id) {\n            binding.buffer_id = BufferId{};\n        }\n    };\n    const auto replace = [scalar_replace](std::span<Binding> bindings) {\n        std::ranges::for_each(bindings, scalar_replace);\n    };\n\n    if (channel_state->index_buffer.buffer_id == buffer_id) {\n        channel_state->index_buffer.buffer_id = BufferId{};\n        dirty_index = true;\n    }\n\n    for (u32 index = 0; index < channel_state->vertex_buffers.size(); index++) {\n        auto& binding = channel_state->vertex_buffers[index];\n        if (binding.buffer_id == buffer_id) {\n            binding.buffer_id = BufferId{};\n            UpdateVertexBufferSlot(index, binding);\n            dirty_vertex_buffers.push_back(index);\n        }\n    }\n    std::ranges::for_each(channel_state->uniform_buffers, replace);\n    std::ranges::for_each(channel_state->storage_buffers, replace);\n    replace(channel_state->transform_feedback_buffers);\n    replace(channel_state->compute_uniform_buffers);\n    replace(channel_state->compute_storage_buffers);\n\n    // Mark the whole buffer as CPU written to stop tracking CPU writes\n    if (!do_not_mark) {\n        Buffer& buffer = slot_buffers[buffer_id];\n        memory_tracker.MarkRegionAsCpuModified(buffer.CpuAddr(), buffer.SizeBytes());\n    }\n\n    Unregister(buffer_id);\n\n#ifdef YUZU_LEGACY\n    if (!do_not_mark || !immediately_free) {\n#endif\n#if defined(PS5_NATIVE) && defined(EDEN_NS2_STAGE_BACKING)\n        // R2 only: do not reclaim a deleted Vulkan owner by frame age.\n        // The runtime owns the moved Buffer until real GPU completion.\n        if constexpr (!P::IS_OPENGL) {\n            runtime.RetainDeletedBuffer(slot_buffers[buffer_id]);\n        } else {\n            delayed_destruction_ring.Push(std::move(slot_buffers[buffer_id]));\n        }\n#else\n        delayed_destruction_ring.Push(std::move(slot_buffers[buffer_id]));\n#endif\n#ifdef YUZU_LEGACY\n    }\n#endif\n\n    slot_buffers.erase(buffer_id);\n\n    if constexpr (HAS_PERSISTENT_UNIFORM_BUFFER_BINDINGS) {\n        channel_state->dirty_uniform_buffers.fill(~u32{0});\n        channel_state->uniform_buffer_binding_sizes.fill({});\n    }\n\n    auto& flags = maxwell3d->dirty.flags;\n    if (dirty_index) {\n        flags[Dirty::IndexBuffer] = true;\n    }\n\n    if (dirty_vertex_buffers.size() > 0) {\n        flags[Dirty::VertexBuffers] = true;\n        for (auto index : dirty_vertex_buffers) {\n            flags[Dirty::VertexBuffer0 + index] = true;\n        }\n    }\n    channel_state->has_deleted_buffers = true;\n}"
            assert selected.count(reviewed) == 1, "Channel-binding lifetime successor drift"
            assert "for (const size_t channel_id : active_channel_ids)" in reviewed
            assert "channel_storage[channel_id]" in reviewed
            assert "channel.has_deleted_buffers = true;" in reviewed
            original = selected.replace(reviewed, prior, 1)
            old_raw = original.encode("utf-8")
            old_sha = hashlib.sha1(
                b"blob " + str(len(old_raw)).encode() + bytes([0]) + old_raw
            ).hexdigest()
            assert old_sha == "6aa9754506ee82b4d25a4e36d4f3be646a62456b", old_sha
            restored = temp / "normalized-buffer-channel-teardown" / "buffer_cache.h"
            restored.parent.mkdir(parents=True, exist_ok=True)
            restored.write_text(original)
            core_owner = restored
            core_blob = old_sha
            print("ENCORE_NS1_NS2_BUFFER_CHANNEL_TEARDOWN_EXACT_REVERSE_PASS")

        if core_blob == '6aa9754506ee82b4d25a4e36d4f3be646a62456b':
            # Normalize the exact reduced clean-page path only in the
            # historical proof copy. The compiled vendor source is unchanged.
            current = core_owner.read_text()
            successor = "    if (!IsRegionGpuModified(aligned_start, aligned_end - aligned_start)) {\n        // WriteMemory's clean-page branch does exactly this mark. Re-entering\n        // it would scan the same GPU-modified ranges again under the buffer\n        // cache mutex, even though this full-page query already proved that\n        // no GPU-owned sibling bytes need a download.\n        memory_tracker.MarkRegionAsCpuModified(device_addr, size);\n        return;\n    }"
            predecessor = "    if (!IsRegionGpuModified(aligned_start, aligned_end - aligned_start)) {\n        WriteMemory(device_addr, size);\n        return;\n    }"
            assert current.count(successor) == 1, "Unexpected BufferCache CPU path"
            previous = current.replace(successor, predecessor, 1)
            raw = previous.encode('utf-8')
            digest = hashlib.sha1(b'blob ' + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
            assert digest == '6bbbae48f3c45fa5fd68d82940f5c5c508cbfd7b', ("Clean-page owner predecessor drift", digest)
            restored = temp/'normalized-clean-cpu-write'/'buffer_cache.h'
            restored.parent.mkdir(parents=True, exist_ok=True)
            restored.write_text(previous)
            core_owner = restored
            core_blob = digest
        if core_blob == '6bbbae48f3c45fa5fd68d82940f5c5c508cbfd7b':
            # NS1: the selected stream-overlap owner clamps low-address
            # backward expansion without moving the existing buffer start
            # forwards. Reverse ONLY that proven guard, then apply the
            # historical GPU-50 receipt on the unmodified old owner.
            new_guard = """        // A stream near the start of physical memory may begin before
        // min_page. Subtraction in the original test then wraps around and
        // turns an ordinary backward leap into a huge invalid GPU buffer.
        // Never move begin forwards past the range we already own.
        if (begin <= min_page || add_value > begin - min_page) {
            begin = (std::min)(begin, min_page);
            device_addr = Core::DEVICE_PAGESIZE;
            return;
        }"""
            old_guard = """        if (add_value > begin - min_page) {
            begin = min_page;
            device_addr = Core::DEVICE_PAGESIZE;
            return;
        }"""
            source = core_owner.read_text()
            assert source.count(new_guard) == 1
            previous = source.replace(new_guard, old_guard, 1)
            raw = previous.encode('utf-8')
            original_blob = hashlib.sha1(
                b'blob ' + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
            assert original_blob == '764cc03616d89cda91f902aabac85d10f309d9f3'
            restored = temp/'normalized-ns1-stream'/'buffer_cache.h'
            restored.parent.mkdir(parents=True, exist_ok=True)
            restored.write_text(previous)
            core_owner = restored
            core_blob = original_blob
            print('ENCORE_NS1_BUFFERCACHE_STREAM_BOUNDARY_EXACT_REVERSE_PASS')

        if core_blob == '764cc03616d89cda91f902aabac85d10f309d9f3':
            # GPU-50 changes only DMACopy's range report and its matching
            # declaration. Reconstruct the previous audited C++ owners exactly,
            # on copies; keep the shipping BufferCache/TextureCache untouched.
            assert base_blob == 'fd9708571ef61c83c399042a5200c87b2e3784d6'
            before_signature = """bool BufferCache<P>::DMACopy(
    GPUVAddr src_address, GPUVAddr dest_address, u64 amount, bool* gpu_written,
    boost::container::small_vector<std::pair<DAddr, size_t>, 4>* gpu_written_dest) {
    if (gpu_written_dest) {
        gpu_written_dest->clear();
    }
"""
            after_signature = """bool BufferCache<P>::DMACopy(GPUVAddr src_address, GPUVAddr dest_address, u64 amount,
                             bool* gpu_written) {
"""
            before_report = """    if (gpu_written_dest) {
        *gpu_written_dest = tmp_intervals;
    }
"""
            corrected_core = core_owner.read_text()
            assert corrected_core.count(before_signature) == corrected_core.count(before_report) == 1
            corrected_core = corrected_core.replace(before_signature, after_signature, 1)
            corrected_core = corrected_core.replace(before_report, '', 1)
            def _gpu50_hash(contents):
                raw = contents.encode('utf-8')
                return hashlib.sha1(b'blob '+str(len(raw)).encode()+bytes([0])+raw).hexdigest()
            assert _gpu50_hash(corrected_core) == '96d933edbf271aa17853748905eeb9c5276c41c2'
            restored_core = temp/'normalized-vendor-gpu50'/'buffer_cache.h'
            restored_core.parent.mkdir(parents=True, exist_ok=True)
            restored_core.write_text(corrected_core)
            core_owner = restored_core
            core_blob = _gpu50_hash(corrected_core)

            before_decl = """    /// Optionally report whether the copied source contains GPU-owned buffer bytes.
    /// gpu_written_dest names the exact destination subranges whose newest bytes stay GPU-owned.
    bool DMACopy(
        GPUVAddr src_address, GPUVAddr dest_address, u64 amount, bool* gpu_written = nullptr,
        boost::container::small_vector<std::pair<DAddr, size_t>, 4>* gpu_written_dest = nullptr);
"""
            after_decl = """    /// Optionally report whether the copied source contains GPU-owned buffer bytes.
    /// A caller must not re-upload the destination texture from stale guest memory.
    bool DMACopy(GPUVAddr src_address, GPUVAddr dest_address, u64 amount,
                 bool* gpu_written = nullptr);
"""
            corrected_base = base_owner.read_text()
            assert corrected_base.count(before_decl) == 1
            corrected_base = corrected_base.replace(before_decl, after_decl, 1)
            assert _gpu50_hash(corrected_base) == '716634290574ed4dfc8fd3be0d0ea0ad582980f8'
            restored_base = temp/'normalized-vendor-gpu50'/'buffer_cache_base.h'
            restored_base.write_text(corrected_base)
            base_owner = restored_base
            base_blob = _gpu50_hash(corrected_base)
            print('ENCORE_NS1_GPU50_BUFFERCACHE_ABI_EXACT_REVERSE_PASS owners=2')
        if core_blob in {
            '41239f19b9e16741d49e31145c504e0086b1095e',
            'b127ceea4006395e9b9bc9727c059dcfdf4a898d',
            '1cf7484e07c1f6f86b4980a7489ab2d4784f9409',
        }:
            if core_blob == '41239f19b9e16741d49e31145c504e0086b1095e':
                # CMake-selected PS5 source: one budget sample feeds two
                # independently locked cache GC passes without a driver query
                # in either critical section. Original fallback remains.
                assert base_blob == '716634290574ed4dfc8fd3be0d0ea0ad582980f8', base_blob
                for relative, expected_blob in (
                    ('encore-active/ns2-astc/include/video_core/texture_cache/texture_cache_base.h',
                     'ce3e85dcb8e502b2763fa53689ae3e737cd0e708'),
                    ('encore-active/ns2-astc/include/video_core/texture_cache/texture_cache.h',
                     'c797eb9e3f4432b6ba19fe8a17a7289b23b75864'),
                ):
                    found_blob = subprocess.check_output(
                        ['git', 'hash-object', str(root/'vendor'/relative)], text=True).strip()
                    assert found_blob == expected_blob, ('native texture budget owner drift', relative, found_blob)
                assert 'PollFrameMemoryUsage' not in core_owner.read_text()
                assert 'total_used_memory = *externally_sampled_usage;' in core_owner.read_text()
                core_blob = '1cf7484e07c1f6f86b4980a7489ab2d4784f9409'
                print('ENCORE_SHARED_GPU_BUDGET_BUFFER_SOURCE_PASS')
            elif core_blob == 'b127ceea4006395e9b9bc9727c059dcfdf4a898d':
                # Previous independently verified off-lock BufferCache probe.
                assert base_blob == '3da34e11ed76a400a6be6bab622191883610d672', base_blob
                core_text = core_owner.read_text()
                assert 'PollFrameMemoryUsage() {' in core_text
                assert 'if (externally_sampled_usage)' in core_text
                assert 'total_used_memory = *externally_sampled_usage;' in core_text
                assert 'total_used_memory = runtime.GetDeviceMemoryUsage();' in core_text
                assert 'void TickFrame(std::optional<u64> externally_sampled_usage' in base_owner.read_text()
                core_blob = '1cf7484e07c1f6f86b4980a7489ab2d4784f9409'
            else:
                assert base_blob == '64be0018b1ff977fc744529d9882d6a264b45f1a', base_blob
            assert ('template <typename RangeSize>\n'
                    'void BufferCache<P>::ClaimCpuWrites(') in core_owner.read_text()
            core_blob = 'd40082a0c849790d25a4d1d28e003087eefd84a1'
            print('ENCORE_FC27_BATCH_CLAIM_BUFFER_SIGNATURE_SOURCE_PASS')
        # The current NS1 BufferCache includes the reviewed Vulkan/GMMU
        # physical-overlap guard. Seal the exact C++ blob and check that
        # rejection precedes cache mutation; historical variants remain below.
        if core_blob == '96d933edbf271aa17853748905eeb9c5276c41c2':
            selected_buffer = core_owner.read_text()
            dma_copy = selected_buffer.split('bool BufferCache<P>::DMACopy(', 1)[1].split('bool BufferCache<P>::DMAClear(', 1)[0]
            for contract in (
                'gpu_memory->IsContinuousRange(src_address, amount)',
                'gpu_memory->IsContinuousRange(dest_address, amount)',
                'const DAddr source = *cpu_src_address;',
                'const DAddr destination = *cpu_dest_address;',
                'destination - source < amount',
                'source - destination < amount',
                'ClearDownload(*cpu_dest_address, amount);',
            ):
                assert contract in dma_copy, ('NS1 physical DMA guard missing', contract)
            assert dma_copy.index('destination - source < amount') < dma_copy.index('ClearDownload(*cpu_dest_address, amount);')
            assert 'const bool page_has_gpu_writes = keep_page_gpu_data && page_end > page_begin &&' in selected_buffer
            assert '!gpu_modified_ranges.Intersects(' not in selected_buffer
            print('ENCORE_NS1_PHYSICAL_DMA_BUFFERCACHE_SOURCE_PASS')
        elif pair_vendor_pin in {'2ccc4b0a714ca621ac2879768f87118a64ed65f6', '97ac02f263ec90f40a029f4aa62980c76bc25d5c', '9a83a6ba1cb464c9e5d14457cab18ad511c1104b', 'd0246caf58a3127597bba1edfc1f8dcbe0c5cfdc', '2a450d43d1d23d3e8b1667e396613f62c69c26d7', '17c95ef233a9a0e508e50ada4ae9dc53a300c46c', '082cd1b77c7df80dc422eae5ba59d9cd33e48dc4', 'e0fced3a091495e70362d8c4ca072942f027af24', '491fa7e2388d46e23827b1459360a5d7f4a2814b', 'b177deb8282b14e1521485f5ac63bd7ccc9ca7ef', '06fc7dc2e0a00e00f831dfd78ae78087736276a3', '850086c79ec40838663989a81f33ba8ea2f15f6a'}:
            # Vendor #189 fixes a real native build ABI mismatch. The reviewed
            # BufferCache header uses the pinned ForEachInRange-backed query;
            # every other Vulkan fork receipt below stays byte-for-byte exact.
            assert core_blob == (
                'd40082a0c849790d25a4d1d28e003087eefd84a1'
                if pair_vendor_pin in {'17c95ef233a9a0e508e50ada4ae9dc53a300c46c', '082cd1b77c7df80dc422eae5ba59d9cd33e48dc4', 'e0fced3a091495e70362d8c4ca072942f027af24', '491fa7e2388d46e23827b1459360a5d7f4a2814b', 'b177deb8282b14e1521485f5ac63bd7ccc9ca7ef', '06fc7dc2e0a00e00f831dfd78ae78087736276a3', '850086c79ec40838663989a81f33ba8ea2f15f6a'} else
                'c6bab56cbd4e58458d010e423d74df9f933a8f8d'
            ), ('reviewed native BufferCache DMA source drift', core_blob)
            selected_buffer = core_owner.read_text()
            if pair_vendor_pin in {'17c95ef233a9a0e508e50ada4ae9dc53a300c46c',
                                   '082cd1b77c7df80dc422eae5ba59d9cd33e48dc4',
                                   'e0fced3a091495e70362d8c4ca072942f027af24', '491fa7e2388d46e23827b1459360a5d7f4a2814b', 'b177deb8282b14e1521485f5ac63bd7ccc9ca7ef', '06fc7dc2e0a00e00f831dfd78ae78087736276a3', '850086c79ec40838663989a81f33ba8ea2f15f6a'}:
                # The latest NS1 DMA release avoids duplicate GPU page queries
                # while preserving sibling bytes. The exact d40082a0 owner
                # above remains mandatory; this checks its active semantics.
                assert 'const bool page_has_gpu_writes = keep_page_gpu_data && page_end > page_begin &&' in selected_buffer
                assert 'IsRegionGpuModified(page_begin, page_end - page_begin)' in selected_buffer
                assert 'if (keep_page_gpu_data && !page_has_gpu_writes)' in selected_buffer
                assert 'const bool overlaps_cpu_write = IsRegionGpuModified(device_addr, size);' in selected_buffer
                assert 'if (page_has_gpu_writes &&' in selected_buffer
                assert '(!overlaps_cpu_write || IsRegionGpuModified(page_begin, page_end - page_begin))' in selected_buffer
            else:
                assert '!IsRegionGpuModified(page_begin, page_end - page_begin)' in selected_buffer
            assert '!gpu_modified_ranges.Intersects(' not in selected_buffer
        elif pair_vendor_pin in {'945385cb96f539a5b2ab2edf269683dd1e9ebad9','2acf67ac8c6b8b1973ba29043206782a13ac8f41','ab38816078a53b81d4c59152ec660fcb653d4e7f','3cac7130d6626dced483d038cbf034274a0463d8','ec3757b3f17d974577b304faa0d54279e01d0a5a','2a8d841c4c7e34e89254e532fc75fd23e16f01fe','3b3a26afd70fbfbfb706e5b9964e3303c07a944c','49070af1bfee1ef67ed8037221345baf71d02373','388f0bda53806cd89d9c2f85139ec0491f212654','c92ce9a8b90808869be76d02e73d35636857a0d4','1e51d1f3383f149a599e36052aba7d887d4b1f77', 'b79c774d5d976b7d374b7f851354a652f6aa69c4', '9d324ca5ca2cdd84053f2d3dfadde5b86084c13d', 'cd476e6e93e8a786bef6260006baec134f5df71f', '2ccc4b0a714ca621ac2879768f87118a64ed65f6', '97ac02f263ec90f40a029f4aa62980c76bc25d5c', '9a83a6ba1cb464c9e5d14457cab18ad511c1104b', 'd0246caf58a3127597bba1edfc1f8dcbe0c5cfdc'}:
            assert core_blob == '505ee80a37d5991b7925019282e71926c1648e02'
            selected_buffer = core_owner.read_text()
            assert 'Lichii 44bf47d' in selected_buffer
            assert '!gpu_modified_ranges.Intersects(page_begin, page_end - page_begin)' in selected_buffer
        elif pair_vendor_pin == 'edcc311c09eed3a33e5acc373c63a436f662cb5b':
            # Vendor b13c4c1 predecessor remains historically pinned.
            assert core_blob == '09e1578dec6dcbcb0b8f54d4bb819b71d0eed972'
        else:
            assert core_blob == (
            'c4ed79a1fe6aec09da8040b7af3901f6184f910b'
            if pair_vendor_pin in {'b1bb49abea63b6664e0945df8431e10aac128c2f', '89d70eb505594447b3ca98658311002e74dac8ad', 'b68126c9cd95eef6c6656ff6d7834c62c092aa46', '0fc157b7ccef428e675ff945bc48eceb08fff607', '0fc157b7ccef428e675ff945bc48eceb08fff607', '42459a7893c51a178ecd0c2f74f3951cc20fa12d', 'd1f8696448ed481e36380c3ea8431e3dc722304e', 'c5614d3c7ef75958965bac93c9e343eccdbc0fbe', '67926ea4b6960eefebf0427929cf299e8e056013', '50a849a93494f442d47573b8ce8b8797c3cecd26', '2c85d0e8ed192c5eec79423e6be8d883fa0bd7ab', '053acc8ddf30fe65f6376564bbd6efef58f07ddc', 'ffa519db0f68fb0d5d2acf791e381c898a34a175', '9e38066a508716fd959477eccf32c7fb2fde3356', 'e298a9b05732346141b685eb4c9850bfa02d9e58','f7ccfda091fd7429f44159318a07391881a3e7c0','92c480e17fedecc21ab4882b76e8507b5aed3771','7039d7752c5d8b1a53db50be0d8f2f7803867e13','d3fca0aa188052f0efd2bad102950aeaeeb36ab0','dfc39fcc087738955b0373b45fa97facdeb2fc47','b806bc497049819e716ef6de81f2a85312b188ce','a0e17271e94342c32b02acdc3199c3f258a8aecf','772f06c8f5b12fdc81066e61f3db2dedfe3eed81','568ae541c07691518e9663aa0fc5f3b017a98d53','dcfe3d2384bd800c6139ede672518ea2c66922a6','affa3c761f70268c89e9f7c7de24eec958c7f889','edcc311c09eed3a33e5acc373c63a436f662cb5b','945385cb96f539a5b2ab2edf269683dd1e9ebad9','2acf67ac8c6b8b1973ba29043206782a13ac8f41','ab38816078a53b81d4c59152ec660fcb653d4e7f','3cac7130d6626dced483d038cbf034274a0463d8','ec3757b3f17d974577b304faa0d54279e01d0a5a','2a8d841c4c7e34e89254e532fc75fd23e16f01fe','3b3a26afd70fbfbfb706e5b9964e3303c07a944c','49070af1bfee1ef67ed8037221345baf71d02373','388f0bda53806cd89d9c2f85139ec0491f212654','c92ce9a8b90808869be76d02e73d35636857a0d4','1e51d1f3383f149a599e36052aba7d887d4b1f77', 'b79c774d5d976b7d374b7f851354a652f6aa69c4', '9d324ca5ca2cdd84053f2d3dfadde5b86084c13d', 'cd476e6e93e8a786bef6260006baec134f5df71f', '2ccc4b0a714ca621ac2879768f87118a64ed65f6', '97ac02f263ec90f40a029f4aa62980c76bc25d5c', '9a83a6ba1cb464c9e5d14457cab18ad511c1104b', 'd0246caf58a3127597bba1edfc1f8dcbe0c5cfdc'}
            else '469eddd0ea9e0a3498446bf08ab473caac3b76f9'), (
                'R2 real deleted-buffer source owner changed')
    # Nov23 reviewed native presentation owners are deliberate additions to
    # the historical generated Vulkan tree, never generated upstream files.
    # Seal their complete bytes and the guest-frame pacing contract.
    presentation_headers = {
        'include/video_core/renderer_vulkan/frame_pacer.h':
            'c3f6f99dd427fb9fd0acb84bb50ba88dc25d9a89',
        'include/video_core/renderer_vulkan/vk_swapchain.h':
            'c4df1ab813495b8014e0eda5ed4bcd8fb0be855c',
    }
    for name, sha in presentation_headers.items():
        assert name in expected and name not in actual, (
            'Native presentation header ownership drift', name)
        assert subprocess.check_output(
            ['git', 'hash-object', str(expected[name])], text=True
        ).strip() == sha, ('Native presentation header changed', name)
    pacer = expected['include/video_core/renderer_vulkan/frame_pacer.h'].read_text()
    swapchain = expected['include/video_core/renderer_vulkan/vk_swapchain.h'].read_text()
    assert 'game_frame_presents == 0 ? 1 : game_frame_presents' in pacer
    assert 'frames += 1.0 / static_cast<double>(presents)' in pacer
    assert 'bool AcquireNextImage(u32 game_frame_presents = 1)' in swapchain
    approved_native_additions |= set(presentation_headers)
    unexpected_additions = set(expected) - set(actual)
    assert unexpected_additions == approved_native_additions, (
        'Vulkan active native additive inventory drift',
        'unreviewed:', sorted(unexpected_additions - approved_native_additions),
        'missing:', sorted(approved_native_additions - unexpected_additions))
    # Byte-for-byte parity of every generated owner remains mandatory below.
    helper_file=expected[helper]
    assert subprocess.check_output(['git','hash-object',str(helper_file)],text=True).strip()==(
        '16749faa8c0f1047de0485af53ff2de65d66be7d'), 'upstream wait primitive drift'
    for name in (
        'include/video_core/renderer_vulkan/vk_graphics_pipeline.h',
        'include/video_core/renderer_vulkan/vk_compute_pipeline.h',
    ):
        source=actual[name].read_text()
        old='    std::condition_variable build_condvar;\n    std::mutex build_mutex;'
        new='    ::Eden::StripedCondition build_condvar;\n    ::Eden::StripedMutex build_mutex;'
        inc='#include "common/thread_worker.h"'
        assert source.count(old)==source.count(inc)==1, ('pipeline source moved',name)
        modified=source.replace(inc,inc+'\n#include "video_core/renderer_vulkan/striped_wait.h"').replace(old,new)
        actual[name].write_text(modified)
    # The selected native rasterizer intentionally fails closed on an absent
    # indirect-command/count binding. Mirror ONLY those two reviewed guards
    # in the temporary oracle; the production source stays in encore-active.
    raster_path = actual['vulkan_rasterizer.cpp']
    raster = raster_path.read_text()
    native_guards = (
        (
            "        const auto& buffer = indirect_buffer.first;\n"
            "        const auto& offset = indirect_buffer.second;\n"
            "        if (params.is_byte_count) {",
            "        const auto& buffer = indirect_buffer.first;\n"
            "        const auto& offset = indirect_buffer.second;\n"
            "        // UpdateDrawIndirect can deliberately reject an unmapped/overflowing\n"
            "        // guest command span. Never record a Vulkan draw with a null buffer.\n"
            "        if (!buffer) {\n"
            "            return;\n"
            "        }\n"
            "        if (params.is_byte_count) {",
        ),
        (
            "            const auto& draw_buffer = count.first;\n"
            "            const auto& offset_base = count.second;\n"
            "            scheduler.Record([draw_buffer_obj = draw_buffer->Handle(),",
            "            const auto& draw_buffer = count.first;\n"
            "            const auto& offset_base = count.second;\n"
            "            if (!draw_buffer) {\n"
            "                return;\n"
            "            }\n"
            "            scheduler.Record([draw_buffer_obj = draw_buffer->Handle(),",
        ),
    )
    for old, new in native_guards:
        assert raster.count(old) == 1, "pinned Vulkan indirect draw moved"
        raster = raster.replace(old, new)
    # The pinned draw path has its own null-pointer guard. Compute-indirect
    # and DMA image now also require a live Vulkan handle, not just Buffer*.
    # Verify all three paths independently, not a combined obsolete count.
    assert raster.count("if (!buffer)") == 1, "draw indirect pointer guard drift"
    native_vk_guard = "if (!buffer || buffer->Handle() == VK_NULL_HANDLE)"
    assert raster.count(native_vk_guard) == 4, "compute/DMA/native QMD/texel Vulkan handle guard drift"
    native_commit = raster.split('Deferred GPU write tracking is a commit',1)[1].split(
        'const auto dim = launch.grid;',1)[0]
    assert native_commit.count(native_vk_guard)==2, "native SSBO/texel post-admission VkBuffer guard missing"
    assert raster.count("if (!draw_buffer)") == 1, "counted draw buffer guard drift"
    dispatch = raster.split("void RasterizerVulkan::DispatchCompute() {", 1)[1].split(
        "void RasterizerVulkan::ResetCounter(", 1)[0]
    assert dispatch.count(native_vk_guard) == 1, "compute indirect VkBuffer guard drift"
    dma = raster.split("bool AccelerateDMA::DmaBufferImageCopy(", 1)[1].split(
        "bool AccelerateDMA::ImageToBuffer(", 1)[0]
    assert dma.count(native_vk_guard) == 1, "DMA image VkBuffer guard drift"
    assert "if (!buffer)" in raster.split("void RasterizerVulkan::DrawIndirect() {", 1)[1].split(
        "void RasterizerVulkan::DispatchCompute() {", 1)[0], "draw indirect guard drift"

    # P2.3: reconstruct the exact reviewed mutable-QMD CBUF/SSBO
    # revalidation in the generated rasterizer. Preserve full-file parity:
    # do not substitute the checked-in implementation as the oracle.
    # P2.2b generator now reproduces the entire historical QMD owner and
    # the real native image/sampler descriptor pins. Older archived oracles
    # still take the exact previous patch chain below. Full-file parity is
    # checked afterward in both cases: no source bypass or vendor copy.
    if "native_images.reserve(typed_descriptors->size())" in raster:
        assert "texture_cache.PinNativeImageView(id)" in raster
        assert "std::move(pinned_lifetime)" in raster
    else:
        qmd_binding_previous = "        scheduler.RequestOutsideRenderPassOperationContext();\n        {\n            std::scoped_lock lock{buffer_cache.mutex};\n            if (!pipeline->ConfigureNative(\n                    *resources, *gpu_memory, scheduler, buffer_cache)) return false;\n        }\n        if (!registry.IsComputeCurrent(kepler_compute, *ticket)) {"
        qmd_binding_reviewed = "        // The original QMD resource plan was read before shader compilation.\n        // CBUF descriptors are mutable even when both GPU address ranges\n        // remain mapped. Refuse stale/aliased captures before staging Vulkan.\n        const auto before_binding = resource_owner->BuildResourcePlan(*compiled.info);\n        if (!before_binding || !resources->SameBufferBindings(*before_binding) ||\n            !registry.IsComputeCurrent(kepler_compute, *ticket))\n            return false;\n        scheduler.RequestOutsideRenderPassOperationContext();\n        native_recording_started = true;\n        {\n            std::scoped_lock lock{buffer_cache.mutex};\n            if (!pipeline->ConfigureNative(\n                    *resources, *gpu_memory, scheduler, buffer_cache)) return false;\n        }\n        // ConfigureNative may have recorded descriptor closures already.\n        // Validate CBUF bytes one final time after staging; an inconsistent\n        // dispatch must retain its Vulkan owner until those commands retire.\n        bool current_after_staging = false;\n        try {\n            const auto after_binding = resource_owner->BuildResourcePlan(*compiled.info);\n            current_after_staging = after_binding &&\n                resources->SameBufferBindings(*after_binding);\n        } catch (...) {\n            // A guest CBUF may become unmapped while re-reading it. A failed\n            // read is a refused dispatch, never early pipeline destruction.\n        }\n        if (!current_after_staging ||\n            !registry.IsComputeCurrent(kepler_compute, *ticket)) {"
        assert raster.count(qmd_binding_previous) == 1, "pinned QMD binding path moved"
        assert expected["vulkan_rasterizer.cpp"].read_text().count(qmd_binding_reviewed) == 1, (
            "reviewed native QMD mutation protection drifted")
        raster = raster.replace(qmd_binding_previous, qmd_binding_reviewed)
        # P2.3: the two real rasterizer owners retain native pipelines after
        # a rejected/throwing descriptor-stage closure. Mirror only reviewed
        # changes in the historical generator; final full-file parity stays on.
        native_pipeline_retirement_deltas = (
            ("        std::shared_ptr<ComputePipeline> pipeline{std::move(owned)};", "        std::shared_ptr<ComputePipeline> pipeline{std::move(owned)};\n        // ConfigureNative and Scheduler::Record can throw AFTER recording\n        // closures that capture ComputePipeline*. A normal return-false or\n        // exception must not release that owner before its GPU timeline.\n        // The scope guard is armed only after descriptor staging can start.\n        bool native_recording_started = false;\n        auto native_compute_retirement = SCOPE_GUARD {\n            if (!native_recording_started || !pipeline) return;\n            try {\n                Shader::Ampere::RetainNativeComputeUntilGpuTick(\n                    scheduler, fence_manager, pipeline);\n            } catch (...) {\n                // The retention helper already waits a submitted tick on\n                // callback-registration failure. Keep this final emergency\n                // drain noexcept while unwinding another exception.\n                try { scheduler.Finish(); } catch (...) {}\n            }\n        };"),
            ("            // ConfigureNative has already recorded a Vulkan descriptor-bind\n            // closure that captures ComputePipeline*. Even when this QMD is\n            // refused, retain the object until those queued commands retire.\n            Shader::Ampere::RetainNativeComputeUntilGpuTick(\n                scheduler, fence_manager, std::move(pipeline));\n            return false;", "            // Scope retirement also handles this rejection; do not release\n            // already recorded Vulkan descriptor-bind closures early.\n            return false;"),
            ("        Shader::Ampere::RetainNativeComputeUntilGpuTick(\n                scheduler, fence_manager, std::move(pipeline));\n        return true;", "        // Successful submissions already hold their exact timeline owner.\n        // Cancel exception/early-return recovery before normal retirement.\n        native_compute_retirement.Cancel();\n        Shader::Ampere::RetainNativeComputeUntilGpuTick(\n                scheduler, fence_manager, std::move(pipeline));\n        return true;"),
        )
        for old, new in native_pipeline_retirement_deltas:
            assert raster.count(old) == 1, "native pipeline retirement source drift"
            assert expected["vulkan_rasterizer.cpp"].read_text().count(new) == 1, (
                "native pipeline retirement reviewed source drift")
            raster = raster.replace(old, new)
        # P2.2: the native table-register lifetime check is shared by both
        # Vulkan owners. Mirror only this audited delta from the pinned source,
        # preserving the generator's final full-file byte-for-byte comparison.
        table_register_previous = "                same_cache_channel = texture_cache.NativeChannelMatches(\n                    kepler_compute, *gpu_memory);\n                // TIC/TSC can be rewritten while the shader is compiled."
        table_register_reviewed = "                same_cache_channel = texture_cache.NativeChannelMatches(\n                    kepler_compute, *gpu_memory);\n                // The engine epoch can stay valid while guest code rewrites\n                // TIC/TSC base/limit registers. Never authenticate bytes from\n                // an OLD table and bind them as the currently active one.\n                if (same_cache_channel) {\n                    const auto& live_regs = kepler_compute.regs;\n                    same_cache_channel = tables.SameRegisters(\n                        live_regs.tic.Address(), live_regs.tic.limit,\n                        live_regs.tsc.Address(), live_regs.tsc.limit,\n                        launch.linked_tsc);\n                }\n                // TIC/TSC can be rewritten while the shader is compiled."
        assert raster.count(table_register_previous) == 1, (
            "generated native TIC/TSC table ownership drift")
        assert expected["vulkan_rasterizer.cpp"].read_text().count(
            table_register_reviewed) == 1, "reviewed TIC/TSC register guard drift"
        raster = raster.replace(table_register_previous, table_register_reviewed)
        # P2.2: native SPIR-V dimensions must match the same typed TIC
        # snapshot in both renderer owners before any cache view acquisition.
        typed_previous = ("            if (!typed_descriptors ||\\n"
                          "                !registry.IsComputeCurrent(kepler_compute, *ticket))\\n"
                          "                return false;").replace("\\n", "\n")
        typed_reviewed = ("            if (!typed_descriptors ||\\n"
                          "                !Shader::Ampere::NativeQmdTypedImageLayoutMatches(\\n"
                          "                    *compiled.info, *typed_descriptors) ||\\n"
                          "                !registry.IsComputeCurrent(kepler_compute, *ticket))\\n"
                          "                return false;").replace("\\n", "\n")
        assert raster.count(typed_previous) == 1, "generated native TIC type contract drift"
        assert expected["vulkan_rasterizer.cpp"].read_text().count(typed_reviewed) == 1, (
            "reviewed native TIC reflected type contract drift")
        raster = raster.replace(typed_previous, typed_reviewed)
        # P2.2: shader translation must reject invalid TIC layout/size/MSAA
        # using the SAME admission contract as the later typed cache replay.
        shader_tic_previous = (
            '        if (static_cast<u32>(entry.header_version.Value()) >\n'
            '            static_cast<u32>(Tegra::Texture::TICHeaderVersion::BlockLinearColorKey))\n'
            '            throw std::runtime_error{"unsupported native Compute TIC header"};'
        )
        shader_tic_reviewed = (
            '        // Shader metadata must not be translated from a TIC the later\n'
            '        // shared TextureCache cannot admit. Reject an invalid format layout,\n'
            '        // MSAA mode or overflow budget before spending CPU on native SPIR-V.\n'
            '        if (!Shader::Ampere::NativeQmdTicLayoutSupported(entry))\n'
            '            throw std::runtime_error{"unsupported native Compute TIC layout"};'
        )
        assert raster.count(shader_tic_previous) == 1, "generated TIC translation guard moved"
        assert expected["vulkan_rasterizer.cpp"].read_text().count(shader_tic_reviewed) == 1, (
            "reviewed early TIC shader admission guard drift")
        raster = raster.replace(shader_tic_previous, shader_tic_reviewed)
    # Always commit the two independently reviewed indirect-draw null guards
    # to the generated oracle, including the new fully generated QMD3 path.
    raster_path.write_text(raster)
    # Native GPU hot-path deltas are audited against the pinned generated
    # Vulkan source. Reconstruct exactly; never silently accept another drift.
    pipeline_src = actual['vk_graphics_pipeline_cost.cpp']
    pipeline_text = pipeline_src.read_text()
    optimized_pipeline_deltas = (
        ("        for (const auto& desc : info.texture_descriptors) {\n            for (u32 index = 0; index < desc.count; ++index) {\n                const auto handle{read_handle(desc, index)};\n                views.push_back({handle.first});\n\n                VideoCommon::SamplerId sampler{texture_cache.GetSamplerId(handle.second, false)};\n                samplers.push_back(sampler);\n            }\n        }", "        // A descriptor array frequently shares its sampler handle.\n        // Reuse only consecutive equal handles within this stage/configuration:\n        // no sampler id survives a pipeline change or guest invalidation.\n        bool last_sampler_valid = false;\n        u32 last_sampler_handle{};\n        VideoCommon::SamplerId last_sampler_id{};\n        for (const auto& desc : info.texture_descriptors) {\n            for (u32 index = 0; index < desc.count; ++index) {\n                const auto handle{read_handle(desc, index)};\n                views.push_back({handle.first});\n\n                if (!last_sampler_valid || last_sampler_handle != handle.second) {\n                    last_sampler_id = texture_cache.GetSamplerId(handle.second, false);\n                    last_sampler_handle = handle.second;\n                    last_sampler_valid = true;\n                }\n                samplers.push_back(last_sampler_id);\n            }\n        }"),
        ("    { ::Eden::Performance::CachePhaseTimer cost{::Eden::Performance::CachePhase::TextureFillImageViews};\n        texture_cache.FillImageViews(std::span(views.data(), views.size()), false, Spec::has_images);\n    }", "    // FillImageViews resets the image-deletion/retry latch even for no images.\n    // Keep that state transition for graphics as for compute; no TIC is resolved.\n    { ::Eden::Performance::CachePhaseTimer cost{\n        ::Eden::Performance::CachePhase::TextureFillImageViews};\n        texture_cache.FillImageViews(std::span(views.data(), views.size()), false,\n                                     Spec::has_images);\n    }"),
    )
    for pinned_fragment, native_fragment in optimized_pipeline_deltas:
        assert pipeline_text.count(pinned_fragment) == 1, "pinned sampler stage moved"
        pipeline_text = pipeline_text.replace(pinned_fragment, native_fragment)
    # Reconstruct the reviewed per-draw sampler memo separately from the
    # older consecutive-only optimization. Fail on source/anchor drift.
    sampler_previous = "        // A descriptor array frequently shares its sampler handle.\n        // Reuse only consecutive equal handles within this stage/configuration:\n        // no sampler id survives a pipeline change or guest invalidation.\n        bool last_sampler_valid = false;\n        u32 last_sampler_handle{};\n        VideoCommon::SamplerId last_sampler_id{};\n        for (const auto& desc : info.texture_descriptors) {\n            for (u32 index = 0; index < desc.count; ++index) {\n                const auto handle{read_handle(desc, index)};\n                views.push_back({handle.first});\n\n                if (!last_sampler_valid || last_sampler_handle != handle.second) {\n                    last_sampler_id = texture_cache.GetSamplerId(handle.second, false);\n                    last_sampler_handle = handle.second;\n                    last_sampler_valid = true;\n                }\n                samplers.push_back(last_sampler_id);\n            }\n        }"
    sampler_current = "        for (const auto& desc : info.texture_descriptors) {\n            for (u32 index = 0; index < desc.count; ++index) {\n                const auto handle{read_handle(desc, index)};\n                views.push_back({handle.first});\n                samplers.push_back(resolve_sampler(handle.second));\n            }\n        }"
    sampler_memo = "    // Sampler table mapping is stable while the paired guest cache locks are\n    // held. Cache repeated handles only for this draw: never reuse an ID after\n    // a later guest descriptor invalidation, channel switch or pipeline change.\n    // Keep all 16 distinct sampler handles in one draw even if they share\n    // the low four bits. A direct-mapped memo re-resolved each alternating\n    // handle under the GPU texture-cache mutex. Open addressing has no heap\n    // allocations; saturation falls back to the original lookup, never a\n    // stale ID. Descriptor invalidation cannot cross this draw-local scope.\n    struct SamplerMemo {\n        u32 handle;\n        VideoCommon::SamplerId id;\n    };\n    // A single occupancy mask replaces per-entry valid-byte clearing on\n    // every graphics draw. A slot becomes visible only after lookup success.\n    std::array<SamplerMemo, 16> sampler_memo;\n    u32 occupied_sampler_slots{};\n    const auto resolve_sampler{[&](u32 handle) -> VideoCommon::SamplerId {\n        const std::size_t first = (handle ^ (handle >> 4)) & 15U;\n        for (std::size_t offset = 0; offset < sampler_memo.size(); ++offset) {\n            const std::size_t slot = (first + offset) & 15U;\n            const u32 bit = u32{1} << slot;\n            auto& entry = sampler_memo[slot];\n            if (occupied_sampler_slots & bit) {\n                if (entry.handle == handle) return entry.id;\n                continue;\n            }\n            // A failed sampler lookup never publishes the occupied bit.\n            entry.id = texture_cache.GetSamplerId(handle, false);\n            entry.handle = handle;\n            occupied_sampler_slots |= bit;\n            return entry.id;\n        }\n        return texture_cache.GetSamplerId(handle, false);\n    }};\n"
    sampler_stage = '    const auto config_stage{[&](size_t stage) LAMBDA_FORCEINLINE {'
    assert pipeline_text.count(sampler_previous) == 1
    assert pipeline_text.count(sampler_stage) == 1
    assert pipeline_text.count('#include <algorithm>\n') == 1
    assert '#include <array>\n' not in pipeline_text
    pipeline_text = pipeline_text.replace('#include <algorithm>\n',
                                          '#include <algorithm>\n#include <array>\n', 1)
    pipeline_text = pipeline_text.replace(sampler_previous, sampler_current)
    pipeline_text = pipeline_text.replace(sampler_stage, sampler_memo + sampler_stage)
    assert pipeline_text.count('std::array<SamplerMemo, 16> sampler_memo;') == 1
    assert pipeline_text.count('samplers.push_back(resolve_sampler(handle.second));') == 1
    pipeline_src.write_text(pipeline_text)

    # AMD logic-op host-state projection: never mutate guest Maxwell regs.
    # Replay exact source deltas against the pinned Vulkan renderer.
    raster_src = actual['vulkan_rasterizer.cpp']
    raster_data = raster_src.read_text()
    for old, new in (
        ("        // AMD Workaround: LogicOp incompatible with float render targets\n        if (device.GetDriverID() == VkDriverIdKHR::VK_DRIVER_ID_AMD_OPEN_SOURCE ||\n            device.GetDriverID() == VkDriverIdKHR::VK_DRIVER_ID_AMD_PROPRIETARY) {\n            const auto has_float = std::any_of(\n                regs.vertex_attrib_format.begin(), regs.vertex_attrib_format.end(),\n                [](const auto& attrib) {\n                    return attrib.type == Maxwell3D::Regs::VertexAttribute::Type::Float;\n                }\n            );\n            if (regs.logic_op.enable) {\n                regs.logic_op.enable = static_cast<u32>(!has_float);\n            }\n        }\n        UpdateLogicOpEnable(regs);", "        // The AMD host workaround depends on vertex formats as well as the\n        // guest logic-op register. A vertex format change must rebind the\n        // effective Vulkan state without overwriting the guest register.\n        if (regs.logic_op.enable != 0 && flags[Dirty::VertexInput] &&\n            (device.GetDriverID() == VkDriverIdKHR::VK_DRIVER_ID_AMD_OPEN_SOURCE ||\n             device.GetDriverID() == VkDriverIdKHR::VK_DRIVER_ID_AMD_PROPRIETARY)) {\n            flags[Dirty::LogicOpEnable] = true;\n        }\n        UpdateLogicOpEnable(regs);"),
        ("void RasterizerVulkan::UpdateLogicOpEnable(Tegra::Engines::Maxwell3D::Regs& regs) {\n    if (!state_tracker.TouchLogicOpEnable()) {\n        return;\n    }\n    if (!device.SupportsDynamicState3LogicOpEnable()) {\n        return;\n    }\n    scheduler.Record([enable = regs.logic_op.enable](vk::CommandBuffer cmdbuf) {\n        cmdbuf.SetLogicOpEnableEXT(enable != 0);\n    });\n}", "void RasterizerVulkan::UpdateLogicOpEnable(Tegra::Engines::Maxwell3D::Regs& regs) {\n    if (!state_tracker.TouchLogicOpEnable()) {\n        return;\n    }\n    if (!device.SupportsDynamicState3LogicOpEnable()) {\n        return;\n    }\n    bool enable = regs.logic_op.enable != 0;\n    if (enable &&\n        (device.GetDriverID() == VkDriverIdKHR::VK_DRIVER_ID_AMD_OPEN_SOURCE ||\n         device.GetDriverID() == VkDriverIdKHR::VK_DRIVER_ID_AMD_PROPRIETARY)) {\n        // The existing AMD float-vertex workaround applies to Vulkan only.\n        // Never mutate a Maxwell register: the guest can reuse its original\n        // logic-op value on a later draw with a different vertex format.\n        enable = !std::any_of(\n            regs.vertex_attrib_format.begin(), regs.vertex_attrib_format.end(),\n            [](const auto& attrib) {\n                return attrib.type ==\n                       Tegra::Engines::Maxwell3D::Regs::VertexAttribute::Type::Float;\n            });\n    }\n    scheduler.Record([enable](vk::CommandBuffer cmdbuf) {\n        cmdbuf.SetLogicOpEnableEXT(enable);\n    });\n}"),
    ):
        assert raster_data.count(old) == 1, "pinned Vulkan AMD logic-op path moved"
        raster_data = raster_data.replace(old, new)
    raster_src.write_text(raster_data)
    # F04: reconstruct ONLY the reviewed upload-barrier stage/access deltas
    # from the pinned source. Never replace this with the active file or
    # weaken the full-file oracle: unrelated Vulkan drift must still fail.
    upload_path = actual["vk_texture_cache_cost.cpp"]
    upload_source = upload_path.read_text()
    upload_deltas = (
        # The native missing-pass guard is replayed by prepare-vulkan-port.py.
        # Only five independent post-generator source transformations are here.
    # F07 P0.4: a device without image-format-list still needs its optional
    # BCn 3D compute-buffer pass to complete native asynchronous uploads.
    ("    if (!device.IsKhrImageFormatListSupported()) {\n        return;\n    }",
     "    if (!device.IsKhrImageFormatListSupported()) {\n#ifdef PS5_NATIVE\n        // BCn 3D unswizzle is a compute-buffer pass; it does not require\n        // VK_KHR_image_format_list. Without a pass here, native queued 3D\n        // uploads can be marked complete without ever submitting pixels.\n        if (Settings::values.gpu_unswizzle_enabled.GetValue()) {\n            bl3d_unswizzle_pass.emplace(device, scheduler, descriptor_pool,\n                                       staging_buffer_pool, compute_pass_descriptor_queue);\n        }\n#endif\n        return;\n    }"),
    ("VK_ACCESS_DEPTH_STENCIL_ATTACHMENT_WRITE_BIT;\n    static constexpr VkAccessFlags READ_ACCESS_FLAGS",
     "VK_ACCESS_DEPTH_STENCIL_ATTACHMENT_WRITE_BIT | VK_ACCESS_TRANSFER_WRITE_BIT;\n    static constexpr VkAccessFlags READ_ACCESS_FLAGS"),
    ("VK_ACCESS_DEPTH_STENCIL_ATTACHMENT_READ_BIT;\n\n    //  Compute exact mip/layer range being written to",
     "VK_ACCESS_DEPTH_STENCIL_ATTACHMENT_READ_BIT | VK_ACCESS_TRANSFER_READ_BIT;\n\n    //  Compute exact mip/layer range being written to"),
    ("    cmdbuf.PipelineBarrier(VK_PIPELINE_STAGE_LATE_FRAGMENT_TESTS_BIT |\n                           VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT |\n                           VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT, VK_PIPELINE_STAGE_TRANSFER_BIT, 0,\n                           read_barrier);",
     "    // Include shader and transfer producers of the previous contents. Color\n    // attachment and late-depth alone cannot order vertex/fragment writers,\n    // early depth, or a preceding copy to the same image.\n    cmdbuf.PipelineBarrier(VK_PIPELINE_STAGE_VERTEX_SHADER_BIT |\n                           VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT |\n                           VK_PIPELINE_STAGE_EARLY_FRAGMENT_TESTS_BIT |\n                           VK_PIPELINE_STAGE_LATE_FRAGMENT_TESTS_BIT |\n                           VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT |\n                           VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT |\n                           VK_PIPELINE_STAGE_TRANSFER_BIT,\n                           VK_PIPELINE_STAGE_TRANSFER_BIT, 0, read_barrier);"),
    ("    cmdbuf.PipelineBarrier(\n            VK_PIPELINE_STAGE_TRANSFER_BIT,\n            VK_PIPELINE_STAGE_LATE_FRAGMENT_TESTS_BIT |\n            VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT |\n            VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT,\n            0, nullptr, nullptr, write_barrier);",
     "    // After copying, fragment/vertex texture sampling must see the upload.\n    // The existing destination access mask already names shader reads, but\n    // without those stage bits they are outside the destination scope.\n    cmdbuf.PipelineBarrier(\n            VK_PIPELINE_STAGE_TRANSFER_BIT,\n            VK_PIPELINE_STAGE_VERTEX_SHADER_BIT |\n            VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT |\n            VK_PIPELINE_STAGE_EARLY_FRAGMENT_TESTS_BIT |\n            VK_PIPELINE_STAGE_LATE_FRAGMENT_TESTS_BIT |\n            VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT |\n            VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT |\n            VK_PIPELINE_STAGE_TRANSFER_BIT,\n            0, nullptr, nullptr, write_barrier);"),
    )
    for pinned_fragment, reviewed_fragment in upload_deltas:
        assert upload_source.count(pinned_fragment) == 1, "pinned image upload barrier moved"
        upload_source = upload_source.replace(pinned_fragment, reviewed_fragment)
    upload_path.write_text(upload_source)
    # The renderer retains its pinned SPIR-V for the regular in-game HUD.
    # Replay only the reviewed source-owned no-second-splash handoff change,
    # preserving byte-for-byte comparison of EVERY generated native file.
    loader_path = actual["vulkan_window_adapt_pass.cpp"]
    loader_source = loader_path.read_text()
    for before, after in (
        ("    const auto hud = draw_hud ? Eden::GetVulkanHud() : Eden::HudSnapshot{};\n    if (hud.width && !hud_pipeline) {",
         "    const auto hud = draw_hud ? Eden::GetVulkanHud() : Eden::HudSnapshot{};\n    // The 3D jacket in the native launcher is the ONE authored loading\n    // animation. The checked-in Vulkan SPIR-V includes an obsolete purple\n    // loading scene; keep the shader binary pinned for normal FPS HUD only.\n    // Rendering the loader without an overlay retains the GPU warm-up\n    // swapchain presents, acquire/release order and first-frame handoff.\n    const bool quiet_loading_handoff = hud.loading != 0;\n    if (hud.width && !quiet_loading_handoff && !hud_pipeline) {"),
        ("        const f32 bg_red = Settings::values.bg_red.GetValue() / 255.0f;\n        const f32 bg_green = Settings::values.bg_green.GetValue() / 255.0f;\n        const f32 bg_blue = Settings::values.bg_blue.GetValue() / 255.0f;",
         "        // The launcher has already faded to this ink. Avoid a visibly\n        // different second loading screen, without dropping empty-frame\n        // presents while Vulkan/guest shaders initialize.\n        const f32 bg_red = quiet_loading_handoff ? 0.024f :\n            Settings::values.bg_red.GetValue() / 255.0f;\n        const f32 bg_green = quiet_loading_handoff ? 0.035f :\n            Settings::values.bg_green.GetValue() / 255.0f;\n        const f32 bg_blue = quiet_loading_handoff ? 0.039f :\n            Settings::values.bg_blue.GetValue() / 255.0f;"),
        ("        if (hud.width && (hud.loading || (render_area.width >= hud_units(hud.width + 16) &&\n                                          render_area.height >= hud_units(64)))) {",
         "        if (hud.width && !quiet_loading_handoff &&\n            render_area.width >= hud_units(hud.width + 16) &&\n            render_area.height >= hud_units(64)) {"),
        ("            const VkRect2D scissor = hud.loading ? VkRect2D{{0, 0}, render_area} :\n                VkRect2D{{static_cast<int32_t>(hud_units(16)), static_cast<int32_t>(hud_units(16))},\n                         {hud_units(hud.width), hud_units(48)}};",
         "            const VkRect2D scissor{\n                {static_cast<int32_t>(hud_units(16)), static_cast<int32_t>(hud_units(16))},\n                {hud_units(hud.width), hud_units(48)}};"),
        ("            if (hud.loading) {\n                // The loading scene fills the picture: tell it how large that is.\n                constants.x = render_area.width;\n                constants.y = render_area.height;\n            } else {\n                // Where the text starts in this picture, and the picture's height for its size.\n                constants.x = hud_units(hud.x);\n                constants.y = hud_units(hud.y);\n                constants.width = render_area.height;\n            }",
         "            // Only the regular FPS overlay reaches this pass. No second\n            // full-screen splash is submitted on the warm-up swapchain.\n            constants.x = hud_units(hud.x);\n            constants.y = hud_units(hud.y);\n            constants.width = render_area.height;"),
    ):
        assert loader_source.count(before) == 1, "pinned native loader overlay moved"
        assert expected["vulkan_window_adapt_pass.cpp"].read_text().count(after) == 1, "native loader delta changed"
        loader_source = loader_source.replace(before, after)
    loader_path.write_text(loader_source)
    # R01: the generated loader now owns its own frame metrics and includes.\n    # Reconstruct the remaining opt-in graphics telemetry deltas on top
    # of the formerly validated generator output. The active Vulkan fork and
    # shader owners remain full checked-in sources; generator only acts as a
    # BYTE-FOR-BYTE parity oracle, never as production patcher.
    metrics_deltas = {
        "vulkan_renderer.cpp": [
            ("    RenderScreenshot(framebuffers);\n    if (::Eden::Display::SkipFrame()) {", "    RenderScreenshot(framebuffers);\n    // Count a source callback separately from submitted or displayed frames.\n    ::Eden::FrameMetrics::OnSourceComposite();\n    if (::Eden::Display::SkipFrame()) {\n        ::Eden::FrameMetrics::OnSourceSkipped();"),
            ("        present_manager.Present(generated);\n    }\n#endif", "        present_manager.Present(generated);\n        ::Eden::FrameMetrics::OnGeneratedQueued();\n    }\n#endif"),
            ("    present_manager.Present(frame);\n    scheduler.DispatchWork();", "    present_manager.Present(frame);\n    ::Eden::FrameMetrics::OnRealQueued();\n    scheduler.DispatchWork();"),
        ],
        "vulkan_present_manager.cpp": [
            ("#include \"common/settings.h\"", "#include \"common/settings.h\"\n#include \"frame_metrics.h\""),
            ("    // Present\n    swapchain.Present(render_semaphore);\n}", "    // CPU API return only, not proof of HDMI scanout.\n    swapchain.Present(render_semaphore);\n    ::Eden::FrameMetrics::OnSwapchainPresentReturned();\n}"),
        ],
    }
    for file_name, replacements in metrics_deltas.items():
        path = actual[file_name]
        contents = path.read_text()
        for old, updated in replacements:
            assert contents.count(old) == 1, ("R01 pinned Vulkan site drift", file_name, old[:75])
            contents = contents.replace(old, updated)
        assert contents.count('::Eden::FrameMetrics::') == (5 if file_name == 'vulkan_renderer.cpp' else 1), ("telemetry count drift", file_name)
        path.write_text(contents)

    # N65: vendor's generic sparse requirements query is a reviewed
    # additive API. Reconstruct the exact generator baseline from the
    # maintained vendor header/implementation, not by skipping those files.
    # The independent N65 compiled host oracle checks behavior and failures.
    normalized_expected = {}
    # Both the scheduler header and active scheduler TU have branch-only
    # epoch markers. Normalize their exact SHA-pinned R2 hunks BEFORE
    # historic N72/P04 MSAA source-oracle checks. No production exemption.
    if r2_production:
        r2_scheduler_pre_msaa = {
            'include/video_core/renderer_vulkan/vk_scheduler.h': (
                '0d07f85c09d4ef0a420ce93f36ce5beb61365be1',
                [
                    ('#if defined(PS5_NATIVE) && defined(EDEN_NS2_STAGE_BACKING)\\n'
                     '    // An owner-thread observation', '#endif\\n\\n'),
                    ('#if defined(PS5_NATIVE) && defined(EDEN_NS2_STAGE_BACKING)\\n'
                     '    // Producer-thread command chunk rollover', '#endif\\n'),
                ]),
            'vulkan_scheduler.cpp': (
                '70bc538c71ba1327a0c2a51a6bcb57d1835db2e0',
                [
                    ('#if defined(PS5_NATIVE) && defined(EDEN_NS2_STAGE_BACKING)\\n'
                     '        // The FIFO chunk moved', '#endif\\n'),
                ]),
        }
        for name, (sha, edits) in r2_scheduler_pre_msaa.items():
            source = expected[name].read_text()
            observed = subprocess.check_output(
                ['git', 'hash-object', str(expected[name])],
                text=True).strip()
            # Native callback registration shares the worker execution lock.
            if name == 'include/video_core/renderer_vulkan/vk_scheduler.h' and observed == '0a150f61ea637fc8ce9849379da7ebf241deb6d4':
                current = "    void RegisterOnSubmit(std::function<void()>&& func) {\n#ifdef PS5_NATIVE\n        // The submit callback executes inside WorkerThread's execution lock.\n        // Registration is owner-only (renderer construction/teardown).\n        std::scoped_lock lock{execution_mutex};\n#endif\n        on_submit = std::move(func);\n    }"
                previous = "    void RegisterOnSubmit(std::function<void()>&& func) {\n        on_submit = std::move(func);\n    }"
                assert source.count(current) == 1
                source = source.replace(current, previous, 1)
                observed = git_blob_sha(source)
                assert observed == 'c82ae5986c5028795093ff8573c33068d12c6de3'
            # Frame pacing successor: reverse the exact reviewed Scheduler::Wait ABI
            # and pacing state extraction before the sealed historical R2 comparison.
            if name == 'include/video_core/renderer_vulkan/vk_scheduler.h' and observed == 'c82ae5986c5028795093ff8573c33068d12c6de3':
                for current, previous in (
                    ("#include \"common/common_types.h\"\n#include \"common/polyfill_thread.h\"\n#include \"common/settings.h\"\n#include \"video_core/renderer_vulkan/frame_pacer.h\"\n#include \"video_core/renderer_vulkan/vk_master_semaphore.h\"\n#include \"video_core/vulkan_common/vulkan_wrapper.h\"\n",
                     "#include \"common/common_types.h\"\n#include \"common/polyfill_thread.h\"\n#include \"common/settings.h\"\n#include \"video_core/renderer_vulkan/vk_master_semaphore.h\"\n#include \"video_core/vulkan_common/vulkan_wrapper.h\"\n"),
                    ("    }\n\n    /// Waits for the given GPU tick, optionally pacing frames.\n    /// Generated presents share one game-frame pacing slot.\n    void Wait(u64 tick, double target_fps = 0.0, u32 game_frame_presents = 1) {\n        if (tick > 0) {\n            if (tick >= master_semaphore->CurrentTick()) {\n                Flush();\n            }\n            master_semaphore->Wait(tick);\n        }\n        if (Settings::values.use_speed_limit.GetValue() && target_fps > 0.0) {\n            const auto now = std::chrono::steady_clock::now();\n            if (const auto paced = frame_pacer.Next(now, target_fps, game_frame_presents)) {\n                const auto target_time = *paced;\n                constexpr auto spin_tail = std::chrono::milliseconds(1);\n                const auto sleep_time = target_time - now;\n                if (sleep_time > spin_tail * 2) {\n                    std::this_thread::sleep_for(sleep_time - spin_tail);\n                }\n                while (std::chrono::steady_clock::now() < target_time) {\n                    std::this_thread::yield();\n                }\n            }\n        }\n    }",
                     "    }\n\n    /// Waits for the given GPU tick, optionally pacing frames.\n    void Wait(u64 tick, double target_fps = 0.0) {\n        if (tick > 0) {\n            if (tick >= master_semaphore->CurrentTick()) {\n                Flush();\n            }\n            master_semaphore->Wait(tick);\n        }\n        if (Settings::values.use_speed_limit.GetValue() && target_fps > 0.0) {\n            auto now = std::chrono::steady_clock::now();\n            if (last_target_fps != target_fps) {\n                frame_interval = std::chrono::duration_cast<std::chrono::steady_clock::duration>(std::chrono::duration<double>(1.0 / target_fps));\n                max_frame_count = static_cast<int>(0.1 * target_fps);\n                last_target_fps = target_fps;\n                frame_counter = 0;\n                start_time = now;\n            }\n            frame_counter++;\n            auto target_time = start_time + frame_interval * frame_counter;\n            if (target_time >= now) {\n                constexpr auto spin_tail = std::chrono::milliseconds(1);\n                auto sleep_time = target_time - now;\n                if (sleep_time > spin_tail * 2) {\n                    std::this_thread::sleep_for(sleep_time - spin_tail);\n                }\n                while (std::chrono::steady_clock::now() < target_time) {\n                    std::this_thread::yield();\n                }\n            } else if (frame_counter > max_frame_count) {\n                frame_counter = 0;\n                start_time = now;\n            }\n        }\n    }"),
                    ("    bool worker_in_flight{};\n    std::jthread worker_thread;\n\n    FramePacer frame_pacer;\n};\n\n} // namespace Vulkan",
                     "    bool worker_in_flight{};\n    std::jthread worker_thread;\n\n    std::chrono::steady_clock::duration frame_interval{};\n    std::chrono::steady_clock::time_point start_time{};\n    double last_target_fps{};\n    u64 max_frame_count{};\n    u64 frame_counter{};\n};\n\n} // namespace Vulkan"),
                ):
                    assert source.count(current) == 1, 'pacing scheduler successor changed'
                    source = source.replace(current, previous)
                observed = git_blob_sha(source)
            assert observed == sha, ('R2 real scheduler source changed', name)
            # R457 FC27: require the exact, reviewed borrowed-pointer
            # release method on the ACTIVE header, then remove ONLY it from
            # the historical generator's equivalence comparison. A missing
            # destructor teardown remains a separate mandatory host gate.
            if name == 'include/video_core/renderer_vulkan/vk_scheduler.h':
                begin = '    // Rasterizer query cache is destroyed before the buffer cache.'
                after = '    // Registers a callback to perform on queue submission.'
                assert source.count(begin) == 1 and source.count(after) == 1
                first_at = source.index(begin)
                last_at = source.index(after, first_at)
                released = source[first_at:last_at]
                assert released.count('void ClearQueryCache() noexcept') == 1
                assert released.count('query_cache = nullptr;') == 1
                source = source[:first_at] + source[last_at:]
            for first, last in edits:
                start = first.replace('\\n', '\n')
                stop = last.replace('\\n', '\n')
                assert source.count(start) == 1, ('R2 scheduler marker drift', name)
                a = source.index(start)
                b = source.index(stop, a) + len(stop)
                source = source[:a] + source[b:]
            normalized = temp/'normalized-vendor-r2-pre-msaa'/name
            normalized.parent.mkdir(parents=True, exist_ok=True)
            normalized.write_text(source)
            normalized_expected[name] = normalized
    # FC27 shutdown fix: prove the production rasterizer revokes its
    # non-owning QueryCache pointer after draining, then compare the rest of
    # the renderer against the exact pinned source-generation baseline.
    raster_name = 'vulkan_rasterizer.cpp'
    raster_source = expected[raster_name].read_text()
    begin = 'RasterizerVulkan::~RasterizerVulkan() {'
    assert raster_source.count(begin) == 1
    old_body = '''RasterizerVulkan::~RasterizerVulkan() {
    scheduler.WaitWorker();
    scheduler.Finish();
}'''
    end = raster_source.index('}', raster_source.index(begin)) + 1
    new_body = raster_source[raster_source.index(begin):end]
    assert new_body.count('scheduler.ClearQueryCache();') == 1
    assert new_body.index('scheduler.Finish();') < new_body.index('scheduler.ClearQueryCache();')
    normalized_raster = raster_source.replace(new_body, old_body)
    normalized_path = temp/'normalized-vendor-fc27-teardown'/raster_name
    normalized_path.parent.mkdir(parents=True, exist_ok=True)
    normalized_path.write_text(normalized_raster)
    normalized_expected[raster_name] = normalized_path
    hname = 'include/video_core/vulkan_common/vulkan_wrapper.h'
    cname = 'vulkan_wrapper.cpp'
    # N66: keep the production generator deterministic. The one additive
    # research native sparse queue API is maintained in vendor, and its actual
    # implementation is executed by check_native_sparse_bind.py (UBSan).
    # For byte parity remove only that exact method, never waive the header.
    n66_header = expected[hname].read_text()
    n66_start = '    VkResult BindSparse(Span<VkBindSparseInfo> bind_infos,'
    n66_end = '    VkResult Present(const VkPresentInfoKHR& present_info)'
    assert n66_header.count(n66_start) == 1 and n66_header.count(n66_end) == 1
    n66_begin = n66_header.index(n66_start)
    n66_finish = n66_header.index(n66_end, n66_begin)
    n66_extension = n66_header[n66_begin:n66_finish]
    assert n66_extension.count('BindSparseImage(VkImage image') == 1
    assert 'if (!queue || !dld || !dld->vkQueueBindSparse)' in n66_extension
    assert 'return BindSparse(submit, completion);' in n66_extension
    assert 'VkSparseImageMemoryBindInfo image_info' in n66_extension
    assert 'VkSparseImageOpaqueMemoryBindInfo tail_info' in n66_extension
    assert 'wait_semaphore ? &wait_semaphore : nullptr' in n66_extension
    assert 'signal_semaphore ? &signal_semaphore : nullptr' in n66_extension
    assert 'wait_semaphore == signal_semaphore' in n66_extension
    baseline_queue = '''    VkResult BindSparse(Span<VkBindSparseInfo> bind_infos,
                        VkFence fence = VK_NULL_HANDLE) const noexcept {
        return dld->vkQueueBindSparse(queue, bind_infos.size(), bind_infos.data(), fence);
    }

'''
    stripped_n66 = n66_header[:n66_begin] + baseline_queue + n66_header[n66_finish:]
    n66_path = temp / 'normalized-vendor-n66' / hname
    n66_path.parent.mkdir(parents=True, exist_ok=True)
    n66_path.write_text(stripped_n66)
    normalized_expected[hname] = n66_path

    header = normalized_expected[hname].read_text()
    anchor = '    VkMemoryRequirements GetImageMemoryRequirements(VkImage image) const noexcept;'
    extension = '''

    // N65: query the actual sparse 2D tile/mip-tail requirements.
    // No DeviceDispatch layout change: resolve entrypoint on demand.
    [[nodiscard]] std::vector<VkSparseImageMemoryRequirements>
        GetSparseImageMemoryRequirements(VkImage image) const;'''
    assert header.count(anchor + extension) == 1, 'N65 vendor sparse header changed'
    normalized_h = header.replace(anchor + extension, anchor)
    source = expected[cname].read_text()
    begin = 'std::vector<VkSparseImageMemoryRequirements>\nDevice::GetSparseImageMemoryRequirements(VkImage image) const {'
    end = 'std::vector<VkPipelineExecutablePropertiesKHR> Device::GetPipelineExecutablePropertiesKHR('
    assert source.count(begin) == 1 and source.count(end) == 1, 'N65 wrapper owner moved'
    start = source.index(begin)
    finish = source.index(end, start)
    ext = source[start:finish]
    assert ext.count('GetSparseImageMemoryRequirements(VkImage image)') == 1
    assert 'vkGetImageSparseMemoryRequirements' in ext
    assert 'if (!fn) return {};' in ext
    assert 'if (!count || count > 64) return {};' in ext
    assert 'if (!count || count > requirements.size()) return {};' in ext
    normalized_c = source[:start] + source[finish:]
    for name, value in ((hname, normalized_h), (cname, normalized_c)):
        p = temp/'normalized-vendor-n65'/name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(value)
        normalized_expected[name] = p

    # N56: compare the source generator to the exact pre-experiment owner.
    # The driver-cache guard is compiled only by opt-in NS2 research builds.
    n56_name = 'vk_pipeline_cache_cost.cpp'
    n56_before = '        u32 cache_version;\n        file.read(magic_number.data(), magic_number.size())'
    n56_after = '''        u32 cache_version;
#ifdef EDEN_NS2_PIPELINE_CACHE_GUARD
        // Reject truncated (including failed tellg) Vulkan driver cache headers
        // before reading or subtracting an unsigned header size.
        if (end < std::streampos{static_cast<std::streamoff>(
                      magic_number.size() + sizeof(cache_version))}) {
            file.close();
            LOG_WARNING(Common_Filesystem, "Short Vulkan driver cache; rebuilding fresh");
            Common::FS::RemoveFile(filename);
            return create_pipeline_cache(0, nullptr);
        }
#endif
        file.read(magic_number.data(), magic_number.size())'''
    n56_current = expected[n56_name].read_text()
    assert n56_current.count(n56_after) == 1, 'N56 vendor guard differs from exact owner'
    assert n56_current.count('Saved PS5 driver pipeline cache atomically') == 1
    n56_baseline = n56_current.replace(n56_after, n56_before)
    # prepare-vulkan-port.py already regenerates the 32-entry prewarm
    # exactly. Only N56's opt-in cache-header guard is removed here.
    # A separate N56 immutable baseline checker reverses all three reviewed
    # native prewarm deltas before checking the historic Git blob SHA.
    n56_file = temp/'normalized-vendor-n56'/n56_name
    n56_file.parent.mkdir(parents=True, exist_ok=True)
    n56_file.write_text(n56_baseline)
    normalized_expected[n56_name] = n56_file
    # N3m: the unified PS5-native GPU pipeline is now reproduced exactly by the
    # maintained Vulkan generator, including four additional exact graphics
    # epoch/CBUF guards. Pin the three principal blocks separately, then
    # compare the COMPLETE generated C++ byte-for-byte
    # against the vendor (after the separate N56 driver-cache normalization).
    # Never strip these source blocks from parity: doing so would mask drift.
    n3m = normalized_expected[n56_name].read_text()
    # Only the platform guard remains. Never accidentally resurrect the
    # removed experimental build profile, or silently change any native C++
    # block in the generated source. The exact hashes below pin three
    # independently reviewed native shader/graphics owner blocks.
    n3m_flag = '#ifdef PS5_NATIVE\n'
    assert 'EDEN_NS2_VULKAN_SHADER_BRIDGE_EXPERIMENTAL' not in n3m, (
        'Removed NS2 research compile profile returned in vendor')
    assert n3m.count(n3m_flag) >= 10, 'Native PS5 pipeline guards missing'
    def n3m_hash(data):
        value = 0xcbf29ce484222325
        for byte in data.encode('ascii'):
            value = ((value ^ byte) * 0x100000001b3) & 0xffffffffffffffff
        return f'{value:016x}'
    marker_positions = (
        n3m.index(n3m_flag, n3m.index('#include "video_core/vulkan_common/vulkan_wrapper.h"')),
        n3m.index(n3m_flag, n3m.index('GraphicsPipeline* PipelineCache::CurrentGraphicsPipeline()')),
        n3m.rfind(n3m_flag, 0, n3m.index('// Research-only real GPU bridge')),
    )
    assert len(set(marker_positions)) == 3 and min(marker_positions) >= 0
    marker_hashes = (
        'ca47d210fd98b7cb',
        'fb55f953f416aeb7',
        '017496a2d145513d',
    )
    pinned = []
    for start, digest in zip(marker_positions, marker_hashes):
        end = n3m.index('#endif\n', start) + len('#endif\n')
        fragment = n3m[start:end]
        assert n3m_hash(fragment) == digest, 'Unreviewed NS2 renderer code drift'
        pinned.append(fragment)
    assert '#else\n    if (!RefreshStages(graphics_key.unique_hashes)) {\n#endif\n' in pinned[1], (
        'NS1 RefreshStages branch was not preserved')
    assert 'CaptureGraphicsTicket(maxwell3d)' in pinned[1] and (
        'CaptureNs2GraphicsShaderFromGpu(' in pinned[1]), 'NS2 dispatch must use GMMU'
    assert 'CreateNs2GraphicsShaderEnvironment(' in pinned[2] and (
        'IsGraphicsCurrent(maxwell3d, *ticket)' in pinned[2]), 'NS2 pipeline owner drift'
    # P2.4 TessControl/TessEval must be paired before reading source, with
    # distinct live CBUF stage banks rechecked after compilation. Do not
    # merely whitelist a changed hash without checking the new contract.
    native_stage_policy = (root / 'vendor/encore-active/ns2-runtime/ampere/shader_recompiler/frontend/ampere/native_graphics_stage_policy.h').read_text()
    native_shader_reader = (root / 'vendor/encore-active/ns2-runtime/ampere/video_core/native_shader_capture.cpp').read_text()
    assert 'active_tessellation == 0 || active_tessellation == tessellation' in native_stage_policy
    assert 'NativeGraphicsCbufBank(Shader::Stage stage)' in native_stage_policy
    assert 'NativeGraphicsCbufBank(' in native_shader_reader
    assert 'required_bank == ~u32{0}' in native_shader_reader
    assert n3m.count('NativeGraphicsCbufBank(stage)') == 3
    assert 'NativeMeshGraphicsStageMaskSupported(' in pinned[1]
    assert 'NativeMeshGraphicsStageMaskSupported(' in pinned[2]
    # P2.4: the Vulkan Task/Mesh changes are versioned as exact reversible
    # source deltas. Full-file equality remains mandatory after reversing ONLY
    # these checked hunks; do not substitute a trusted vendor copy as oracle.
    p24 = json.loads((root/'tools/fixtures/p24-task-mesh-vulkan-deltas.json').read_text())
    assert p24['schema_version'] == 1
    p24_by_path = {entry['path']: entry for entry in p24['files']}
    assert len(p24_by_path) == len(p24['files']) == 8
    assert set(p24_by_path) == {
        'include/video_core/renderer_vulkan/vk_graphics_pipeline.h',
        'include/video_core/renderer_vulkan/vk_rasterizer.h',
        'include/video_core/vulkan_common/vulkan_wrapper.h',
        'vk_graphics_pipeline_cost.cpp', 'vk_pipeline_cache_cost.cpp',
        'vulkan_device.cpp', 'vulkan_rasterizer.cpp', 'vulkan_wrapper.cpp',
    }
    # Later native MSAA work is a separate, EXACT reversible source layer.
    # Preserve all eight original P24 snapshots and their pinned SHA proofs.
    # The new record contains the real maintained vendor raw blobs and
    # context-anchored reverse patches, never an opportunistic hash restamp.
    post = json.loads((root/'tools/fixtures/p24-post-msaa-reversible-deltas.json').read_text())
    assert post['schema_version'] == 1
    assert post['source_vendor_gitlink'] == '8ef5009141386185ae84a9972e6947a33ecb0c94'
    post_by_path = {entry['path']: entry for entry in post['files']}
    assert len(post_by_path) == len(post['files']) == 7
    assert set(post_by_path) == set(p24_by_path) - {'vulkan_device.cpp'}
    for name, entry in post_by_path.items():
        assert entry['pre_change_maintained_blob_sha'] == p24_by_path[name]['maintained_blob_sha']
        assert len(entry['reverse_hunks']) in range(1, 15)
        for hunk in entry['reverse_hunks']:
            assert hunk['after'] and hunk['before'] and hunk['after'] != hunk['before']
    # Lichii #2100 is a reviewed successor to the merged R23 Vulkan device
    # owner. Reverse its two exact cache-hardening hunks before immutable
    # R23/P24 receipts; unrelated vulkan_device.cpp edits remain rejected.
    def reverse_static_pipeline_cache_2100(name, text, verify_hash=True):
        if name != 'vulkan_device.cpp':
            return text
        current = git_blob_sha(text)
        if current == 'c1126bd34a026ccc5c46acea49c9b4a3deeb5d26':
            load_after = '''    try {
        create(data.size(), data.empty() ? nullptr : data.data());
    } catch (const vk::Exception& e) {
        LOG_ERROR(Render_Vulkan,
                  "Driver rejected the static pipeline cache ({}), starting empty", e.what());
        create(0, nullptr);
    }
}'''
            load_before = '''    create(data.size(), data.empty() ? nullptr : data.data());
}'''
            save_after = '''    // Lichii #2100: keep the last known-good cache if the app exits or
    // crashes while a replacement is being written.
    auto temporary = filename;
    temporary += ".tmp";
    try {
        std::ofstream file(temporary, std::ios::binary | std::ios::trunc);
        file.exceptions(std::ofstream::failbit);
        if (!file.is_open()) {
            return;
        }
        file.write(STATIC_CACHE_MAGIC_NUMBER.data(), STATIC_CACHE_MAGIC_NUMBER.size())
            .write(reinterpret_cast<const char*>(&STATIC_CACHE_VERSION),
                   sizeof(STATIC_CACHE_VERSION))
            .write(data.data(), static_cast<std::streamsize>(size));
        file.close();
    } catch (const std::ios_base::failure& e) {
        Common::FS::RemoveFile(temporary);
        return;
    }
    std::error_code error;
    std::filesystem::rename(temporary, filename, error);
    if (error) {
        LOG_ERROR(Render_Vulkan, "Couldn't replace the static pipeline cache: {}", error.message());
        Common::FS::RemoveFile(temporary);
    }
}'''
            save_before = '''    try {
        std::ofstream file(filename, std::ios::binary | std::ios::trunc);
        file.exceptions(std::ofstream::failbit);
        if (!file.is_open()) {
            return;
        }
        file.write(STATIC_CACHE_MAGIC_NUMBER.data(), STATIC_CACHE_MAGIC_NUMBER.size())
            .write(reinterpret_cast<const char*>(&STATIC_CACHE_VERSION),
                   sizeof(STATIC_CACHE_VERSION))
            .write(data.data(), static_cast<std::streamsize>(size));
    } catch (const std::ios_base::failure& e) {
        Common::FS::RemoveFile(filename);
    }
}'''
            assert text.count(load_after) == text.count(save_after) == 1
            text = text.replace(load_after, load_before, 1).replace(save_after, save_before, 1)
            assert git_blob_sha(text) == '50578df547b769bd45cf4964ffa3f793c1749273', (
                'Lichii #2100 predecessor reconstruction drift')
            print('ENCORE_LICHII_2100_STATIC_CACHE_EXACT_REVERSE_PASS')
            return text
        if verify_hash:
            assert current == '50578df547b769bd45cf4964ffa3f793c1749273', (
                'Unreviewed late vulkan_device.cpp successor', current)
        return text
    # Full source-verified reverse of the six post-P24 R23 Vulkan patches:
    # preserve immutable P24/N57 generator receipts without accepting any
    # unreviewed vendor edit. Every reverse hunk has unique context and
    # reconstructs the exact previous Git blob.
    r23_reverse_receipt = json.loads(
        (root/'tools/fixtures/r23-merged-vulkan-reverse.json').read_text())
    assert r23_reverse_receipt['schema_version'] == 1
    assert r23_reverse_receipt['source_vendor_baseline'] == (
        '87ef285eae969388a7c9ad98467ff7fd6c314cba')
    r23_reverse_by_path = {entry['path']: entry for entry in r23_reverse_receipt['files']}
    assert set(r23_reverse_by_path) == set(r23_combined_owners) if 'r23_combined_owners' in locals() else len(r23_reverse_by_path) == 6
    def reverse_r23(name, text, verify_hash=True):
        text = reverse_static_pipeline_cache_2100(name, text, verify_hash)
        receipt = r23_reverse_by_path.get(name)
        if receipt is None:
            return text
        # Warning-only field reorder in the actual HostTranslateInfo owner.
        # Reverse exactly this unique four-field block before comparing to
        # the immutable pre-warning R23 receipt. Never relax its SHA.
        if name == 'vk_pipeline_cache_cost.cpp':
            ordered = (
                '        .support_viewport_index_layer = device.IsExtShaderViewportIndexLayerSupported(),\\n'
                '        .support_viewport_mask = device.IsNvViewportArray2Supported(),\\n'
                '        .support_geometry_shader_passthrough = device.IsNvGeometryShaderPassthroughSupported(),\\n'
                '        .support_conditional_barrier = device.SupportsConditionalBarriers(),'
            ).replace('\\n', '\n')
            prior = (
                '        .support_viewport_index_layer = device.IsExtShaderViewportIndexLayerSupported(),\\n'
                '        .support_geometry_shader_passthrough = device.IsNvGeometryShaderPassthroughSupported(),\\n'
                '        .support_conditional_barrier = device.SupportsConditionalBarriers(),\\n'
                '        .support_viewport_mask = device.IsNvViewportArray2Supported(),'
            ).replace('\\n', '\n')
            assert text.count(ordered) == 1, 'Reviewed Vulkan initializer field order drift'
            if verify_hash:
                assert git_blob_sha(text) == '6efe1b10862135056c1df1b78007a1c9cb5a9610', (
                    'Unreviewed post-warning Vulkan source', name)
            text = text.replace(ordered, prior, 1)
        # FC27 crash-owner fix postdates the immutable R23 source receipt.
        # Verify the exact destructor and normalize ONLY its borrowed-pointer
        # revocation before reversing historical Vulkan source patches.
        if name == 'vulkan_rasterizer.cpp':
            marker = 'RasterizerVulkan::~RasterizerVulkan() {'
            assert text.count(marker) == 1
            a = text.index(marker)
            z = text.index('}', a) + 1
            body = text[a:z]
            prior = (marker + '\n'
                     '    scheduler.WaitWorker();\n'
                     '    scheduler.Finish();\n'
                     '}')
            if body != prior:
                assert body.count('scheduler.ClearQueryCache();') == 1
                assert body.index('scheduler.WaitWorker();') < body.index(
                    'scheduler.Finish();') < body.index('scheduler.ClearQueryCache();')
                assert 'buffer cache' in body.lower() or 'query' in body.lower()
                text = text[:a] + prior + text[z:]
        if verify_hash:
            assert git_blob_sha(text) == receipt['post_r23_blob'], (
                'Unreviewed R23 merged native source', name)
        for hunk in reversed(receipt['patches']):
            assert text.count(hunk['after']) == 1, (
                'R23 native reverse context moved', name)
            text = text.replace(hunk['after'], hunk['before'], 1)
        if verify_hash:
            assert git_blob_sha(text) == receipt['pre_r23_blob'], (
                'R23 native source failed exact historic reconstruction', name)
        return text

    def reverse_native_kepler_pointer_abi(name, text, verify_hash):
        # The maintained native QMD3 renderer uses RasterizerInterface's
        # KeplerCompute pointer, not a reference. Reverse only 5 member
        # accesses, 6 borrowed-reference calls and the null admission guard.
        # Recreate the ORIGINAL reviewed blob byte-for-byte before P24 reversal,
        # so we never bless unrelated vendor changes or weaken the hash oracle.
        if name != 'vulkan_rasterizer.cpp':
            return text
        start_marker = 'bool RasterizerVulkan::DispatchNativeCompute('
        assert text.count(start_marker) == 1, 'Native QMD3 renderer ABI owner moved'
        start = text.index(start_marker)
        finish = text.index('\nvoid RasterizerVulkan::', start)
        part = text[start:finish]
        guard = (
            '    // ChannelStateCache binds a KeplerCompute pointer; only native process\n'
            '    // tickets authorize dereference, and the channel may be unbound.\n'
            '    if (!kepler_compute) return false;\n'
        )
        assert part.count(guard) == 1, 'Native compute null-guard drift'
        assert part.count('kepler_compute->regs') == 5, 'QMD3 registers ABI drift'
        assert part.count('*kepler_compute, *gpu_memory') == 6, 'QMD3 texture owner ABI drift'
        part = part.replace(guard, '')
        part = part.replace('kepler_compute->regs', 'kepler_compute.regs')
        part = part.replace('*kepler_compute, *gpu_memory', 'kepler_compute, *gpu_memory')
        baseline = text[:start] + part + text[finish:]
        if verify_hash:
            assert git_blob_sha(baseline) == p24_by_path[name]['maintained_blob_sha'], (
                'Unreviewed native KeplerCompute ABI edit', name)
        return baseline

    def reverse_p24(name, text, verify_hash=True):
        receipt=p24_by_path.get(name)
        if receipt is None:
            return text
        # G07 write-commit is an independently reviewed post-P24 production
        # fix, not a historical Task/Mesh or MSAA source change. Reverse its
        # one exact hunk before checking the IMMUTABLE old raw-blob receipt.
        # Any unrelated edit still fails the original Git blob SHA check.
        if name == 'vulkan_rasterizer.cpp':
            before = "            if (!resources->ValidateGpuBufferMappings(\n                    [this](u64 address, u32 bytes) {\n                        return Shader::Ampere::NativeQmdContiguousGpuSpan(\n                            address, bytes, [this](u64 page) {\n                                return gpu_memory->GpuToCpuAddress(page);\n                            });\n                    }))\n                return false;"
            after = "            // A VA can stay mapped while a guest remaps its physical pages.\n            // Recheck the exact pre-staging backing here, under the commit\n            // lock, not merely contiguous coverage. Matches also validates\n            // the full 49-bit span, so no second mapping walk is needed.\n            if (!staged_buffer_mappings.Matches(\n                    *resources, [this](u64 address) {\n                        return gpu_memory->GpuToCpuAddress(address);\n                    }))\n                return false;"
            assert text.count(after) == 1, (
                'G07 physical-backing write-commit reversible hunk drift', name)
            text = text.replace(after, before, 1)
        later=post_by_path.get(name)
        if later and verify_hash:
            assert git_blob_sha(text) == later['post_change_raw_blob_sha'], (
                'Post-P24 reviewed Vulkan raw source drift', name)
        # Keep the separate native KeplerCompute pointer ABI proof. Its
        # normalization happens before reversing the later MSAA additions.
        text = reverse_native_kepler_pointer_abi(name, text, verify_hash=False)
        if later:
            for hunk in reversed(later['reverse_hunks']):
                assert text.count(hunk['after']) == 1, (
                    'Post-P24 MSAA reverse hunk drift', name)
                text=text.replace(hunk['after'],hunk['before'])
        if verify_hash:
            assert git_blob_sha(text) == receipt['maintained_blob_sha'], (
                'Task/Mesh maintained owner drift after MSAA reversal', name)
        for hunk in reversed(receipt['hunks']):
            assert text.count(hunk['after']) == 1, ('Task/Mesh delta hunk drift',name)
            text=text.replace(hunk['after'],hunk['before'])
        if verify_hash:
            assert git_blob_sha(text) == receipt['pinned_blob_sha'], (
                'Task/Mesh source reverse parity failed', name)
        return text
    # FC27's reviewed Lichii #397 batch-invalidation hook postdates the
    # frozen R23 Vulkan receipt. Reverse precisely that single declaration
    # only for the fully qualified vendor blob; keep the old SHA immutable.
    def reverse_reviewed_fc27_batch_header(name, text):
        if name != 'include/video_core/renderer_vulkan/vk_rasterizer.h':
            return text
        baseline = 'cb35d183c8a9c2ea05f5eb8949a167ea295f8ce7'
        if git_blob_sha(text) == baseline:
            return text
        assert git_blob_sha(text) == '7c754c82c12c4f4c934abd3d7f2cdb25222e8d2a', (
            'Unreviewed post-R23 FC27 Vulkan header bytes', name)
        reviewed = '    void OnCacheInvalidations(std::span<const std::pair<DAddr, u64>> ranges) override;\\n'.replace('\\n', '\n')
        assert text.count(reviewed) == 1, ('FC27 batch-invalidation header drift', name)
        text = text.replace(reviewed, '', 1)
        assert git_blob_sha(text) == baseline, ('FC27 R23 header reversal drift', name)
        return text

    # Verify EVERY owner and show precise refusals without weakening the
    # historical SHA or accepting a changed vendor submodule by coincidence.
    # The merged vendor graph contains reviewed R23 full-source integrations
    # on top of P24 and post-MSAA. Historic reverse hunks cannot describe
    # these newer shader/EDS3/TIR changes. Qualify their *exact combined blobs*
    # independently; keep the original reverse proof for unaffected owners.
    r23_combined_owners = {
        'include/video_core/renderer_vulkan/vk_graphics_pipeline.h':
            'd49090a476f6a9bf61026331f59c9fbb1d918729',
        'include/video_core/renderer_vulkan/vk_rasterizer.h':
            'cb35d183c8a9c2ea05f5eb8949a167ea295f8ce7',
        'vk_graphics_pipeline_cost.cpp':
            'd7563d41b74d780f4512899e2fda1b2f362f5523',
        'vk_pipeline_cache_cost.cpp':
            '6efe1b10862135056c1df1b78007a1c9cb5a9610',
        'vulkan_device.cpp':
            '50578df547b769bd45cf4964ffa3f793c1749273',
        'vulkan_rasterizer.cpp':
            '5b04321fa45d6b5e6af1d4b17bcf695348d0dd90',
    }
    r23_required_semantics = {
        'include/video_core/renderer_vulkan/vk_graphics_pipeline.h':
            ('UsesAttributeHandle()', 'SetAttributeHandle('),
        'include/video_core/renderer_vulkan/vk_rasterizer.h':
            ('struct AttributeHandleRun', 'attribute_handle_runs'),
        'vk_graphics_pipeline_cost.cpp':
            ('ATTRIBUTE_HANDLE_CBUF_INDEX', 'VkPipelineRasterizationDepthClipStateCreateInfoEXT'),
        'vk_pipeline_cache_cost.cpp':
            ('HasBrokenPattern(programs[index])', 'single_lane_geometry_subgroups',
             'support_attribute_texture_handle = true',
             'dynamic_features.has_depth_clip_enable'),
        'vulkan_device.cpp':
            ('depthClipEnable', 'mesh_shader'),
        'vulkan_rasterizer.cpp':
            ('CollectAttributeHandleRuns(', 'MaxwellDepthClampClip(',
             'CanExecuteRecordedDraw()', 'DrawMeshTasksEXT'),
    }
    assert set(r23_combined_owners) <= set(p24_by_path)
    for name, receipt_sha in r23_combined_owners.items():
        combined = reverse_static_pipeline_cache_2100(
            name, reverse_reviewed_fc27_batch_header(name, expected[name].read_text()))
        assert git_blob_sha(combined) == receipt_sha, (
            'Unreviewed merged R23 Vulkan source bytes', name)
        assert all(token in combined for token in r23_required_semantics[name]), (
            'Missing merged R23 shader/Vulkan ABI semantic', name)
    # The FC27 teardown is independently source-qualified before the
    # historical combined Vulkan blob is accepted. QueryCache is destroyed
    # ahead of BufferCache: the scheduler must not retain the borrowed owner.
    destructor = expected['vulkan_rasterizer.cpp'].read_text().split(
        'RasterizerVulkan::~RasterizerVulkan() {', 1)[1].split('}', 1)[0]
    assert destructor.count('scheduler.ClearQueryCache();') == 1
    assert destructor.index('scheduler.WaitWorker();') < destructor.index('scheduler.Finish();') < destructor.index('scheduler.ClearQueryCache();')
    print("ENCORE_R23_COMBINED_VULKAN_BLOB_PASS",
          f"reviewed_owners={len(r23_combined_owners)}",
          "historical_P24_reverse_receipt=1")

    maintained_errors = []
    for name in p24_by_path:
        assert name in expected and name in actual, (
            'missing Task/Mesh Vulkan source', name)
        try:
            reverse_p24(name, reverse_r23(
                name, reverse_reviewed_fc27_batch_header(name, expected[name].read_text())))
        except AssertionError as exc:
            maintained_errors.append({'path': name, 'error': str(exc)})
    if maintained_errors:
        print("ENCORE_P24_MAINTAINED_SOURCE_DRIFTS_JSON=" +
              json.dumps(maintained_errors, separators=(',', ':')),
              flush=True)
    assert not maintained_errors, ("P24 post-MSAA reversible source drift", maintained_errors)
    print("ENCORE_P24_POST_MSAA_REVERSIBLE_PASS",
          "historical_reversed_owners=8",
          f"checked_hunks={sum(len(row['reverse_hunks']) for row in post['files'])}",
          "historic_p24_sha_preserved=1")

    # The generator owns the guarded NS2 blocks as well as NS1; every byte
    # must match the pinned vendor after only the existing N56 normalization.
    # GPU-23 is shipped in BOTH the maintained native renderer and the
    # generator, but this N3m comparison intentionally replays an older
    # cache-owner snapshot (cache-version 19 / pre-fragment-shuffle). Check
    # the EXACT production GPU-23 block on both inputs, then reverse ONLY
    # the generated AUDIT COPY to that historical baseline. Never remove
    # PS5's typed integer fragment outputs from the shipping C++ source.
    typed_output_after = """        // Vulkan requires signed/unsigned fragment outputs to match the
        // attachment's numeric class. Previously this was enabled only on
        // MoltenVK: native PS5 RADV would emit floats for integer targets,
        // making color writes poison/undefined (Vulkan shader interfaces).
        // Keep the existing desktop policy; fix the PS5 renderer's ABI.
        const bool require_typed_fragment_outputs =
#ifdef PS5_NATIVE
            true;
#else
            device.IsMoltenVK();
#endif
        if (require_typed_fragment_outputs) {"""
    typed_output_before = '        if (device.IsMoltenVK()) {'
    generated_raw_n3m = actual[n56_name].read_text()
    native_raw_n3m = (active / n56_name).read_text()
    # Compile the actual retry caller, not a second implementation of it.
    # The fake compiler makes partial cache mutation and allocation failure
    # observable without a Vulkan device or guest memory.
    retry_start = "    // Keep the original cached shader bytes and pristine environment state for a\n"
    retry_end = "    auto& serialized_environments = parallel_environments ? *parallel_environments : environments;\n"
    assert native_raw_n3m.count(retry_start) == native_raw_n3m.count(retry_end) == 1
    retry_body = native_raw_n3m.split(retry_start, 1)[1].split(retry_end, 1)[0] + retry_end
    retry_test = r'''
#include <algorithm>
#include <array>
#include <cassert>
#include <cstddef>
#include <memory>
#include <new>
#include <optional>
#include <span>
#include <stdexcept>
struct Maxwell { static constexpr size_t MaxShaderProgram = 6; };
struct Env {
    int cache{};
    static inline bool fail_copy{};
    Env& operator=(const Env& rhs) {
        if (fail_copy) throw std::bad_alloc{};
        cache = rhs.cache;
        return *this;
    }
};
struct GraphicsEnvironments {
    std::array<Env, 6> envs;
    std::array<Env*, 6> env_ptrs{};
    std::span<Env* const> Span() const {
        return {env_ptrs.begin(), std::find(env_ptrs.begin(), env_ptrs.end(), nullptr)};
    }
};
struct GraphicsPipeline {};
struct ParallelGraphicsRetry {};
struct Key { std::array<int, 6> unique_hashes{0, 1, 0, 1, 0, 0}; };
void run(int scenario) {
    GraphicsEnvironments environments{};
    environments.env_ptrs[0] = &environments.envs[1];
    environments.env_ptrs[1] = &environments.envs[3];
    Key graphics_key{};
    int main_pools{};
    bool parallel_translate_stages = scenario != 3;
    Env::fail_copy = scenario == 2;
    int parallel_calls{}, serial_calls{};
    auto CreateGraphicsPipeline = [&](int&, Key&, std::span<Env* const> envs,
                                      std::nullptr_t, bool, bool parallel) {
        assert(envs.size() == 2);
        if (parallel) {
            ++parallel_calls;
            assert(envs[0] != &environments.envs[1]);
            assert(envs[1] != &environments.envs[3]);
            envs[0]->cache = 99;
            envs[1]->cache = 100;
            if (scenario == 1) throw ParallelGraphicsRetry{};
            if (scenario == 4) throw std::logic_error("unrelated");
        } else {
            ++serial_calls;
            assert(envs[0] == &environments.envs[1]);
            assert(envs[1] == &environments.envs[3]);
            assert(envs[0]->cache == 0 && envs[1]->cache == 0);
            envs[0]->cache = 11;
            envs[1]->cache = 12;
        }
        return std::make_unique<GraphicsPipeline>();
    };
    try {
''' + retry_body + r'''
        assert(pipeline);
        assert(scenario != 4);
        assert(parallel_calls == (scenario == 0 || scenario == 1));
        assert(serial_calls == (scenario != 0));
        assert(serialized_environments.envs[1].cache == (scenario == 0 ? 99 : 11));
        assert(serialized_environments.envs[3].cache == (scenario == 0 ? 100 : 12));
        assert((scenario == 0) == (&serialized_environments != &environments));
    } catch (const std::logic_error&) {
        assert(scenario == 4 && parallel_calls == 1 && serial_calls == 0);
    }
    Env::fail_copy = false;
}
int main() { for (int i = 0; i < 5; ++i) run(i); }
'''
    retry_cpp = temp / "shader-retry.cpp"
    retry_cpp.write_text(retry_test)
    for optimization in ("-O0", "-O2"):
        retry_exe = temp / ("shader-retry" + optimization)
        subprocess.run([os.environ.get("CXX", "c++"), "-std=c++20", optimization,
                        str(retry_cpp), "-o", str(retry_exe)], check=True, timeout=60)
        subprocess.run([str(retry_exe)], check=True, timeout=15)
    print("ENCORE_NS1_PARALLEL_RETRY_HOST_PASS cases=5 O0/O2")
    # Check the complete reviewed retry hunks in both owners before replaying
    # the older snapshot receipt. The generated source has independent
    # diagnostic differences, so the native raw hash is checked separately.
    # The prewarm worker must not touch the currently bound guest channel.
    native_raw_n3m = reverse_distinct_prewarm(native_raw_n3m)
    assert git_blob_sha(native_raw_n3m) == "c92e3dbbf4de08030589d9776dded974accf11eb"
    native_raw_n3m = reverse_reviewed_source(native_raw_n3m, PREWARM_WORKER_REVERSES, "native prewarm exception handoff")
    generated_raw_n3m = reverse_reviewed_source(generated_raw_n3m, PREWARM_WORKER_GENERATED_REVERSES, "generated prewarm exception handoff")
    assert git_blob_sha(native_raw_n3m) == "206d845256bbdc1d5f8d660aeed718ad4f607063"
    native_raw_n3m = reverse_reviewed_source(
        native_raw_n3m, PREWARM_CHANNEL_REVERSES, "native disk prewarm independence")
    assert git_blob_sha(native_raw_n3m) == "b246cf9562f8f0c37d287f7049874f04561a4b8f"
    generated_raw_n3m = reverse_reviewed_source(
        generated_raw_n3m, PREWARM_CHANNEL_REVERSES, "generated disk prewarm independence")
    native_raw_n3m = reverse_reviewed_source(
        native_raw_n3m, PARALLEL_SNAPSHOT_RETRY_REVERSES, "native NS1 serial retry")
    assert git_blob_sha(native_raw_n3m) == "fc537323bb9f63d70ef5f8cedd65886e6a0099c0"
    generated_raw_n3m = reverse_reviewed_source(
        generated_raw_n3m, PARALLEL_SNAPSHOT_RETRY_REVERSES, "generated NS1 serial retry")
    assert generated_raw_n3m.count(typed_output_after) == 1, (
        'GPU-23 generated integer fragment output gate drift')
    assert native_raw_n3m.count(typed_output_after) == 1, (
        'GPU-23 shipping integer fragment output gate drift')
    none_rt_guard = """                // Unused color slots are encoded as RenderTargetFormat::NONE.
                // They have no attachment whose numeric class needs decoding.
                // Avoid the generic surface fallback/log and preserve the
                // historical default Float type, matching Lichii's path.
                if (format == Tegra::RenderTargetFormat::NONE) {
                    info.color_output_types[i] = Shader::AttributeType::Float;
                    continue;
                }
"""
    assert generated_raw_n3m.count(none_rt_guard) == 1, (
        'GPU-23 generated NONE render-target guard drift')
    assert native_raw_n3m.count(none_rt_guard) == 1, (
        'GPU-23 shipping NONE render-target guard drift')
    assert n3m.count(typed_output_before) == 1 and typed_output_after not in n3m, (
        'GPU-23 historical cache owner unexpectedly changed')
    # Later generator-oracle checks operate on the same historical copy,
    # while GPU-23 remains byte-identical in the original C++ and generator.
    generated_n3m = generated_raw_n3m.replace(
        typed_output_after, typed_output_before, 1)
    generated_n3m = generated_n3m.replace(none_rt_guard, "", 1)
    # The generator now emits the reviewed parallel/snapshot successor, but
    # n3m is the frozen pre-parallel owner. Reverse only exact reviewed hunks
    # in the temporary generated copy, preserving the full byte-parity test.
    drain_hunks = [
        ("        // QueueWork and pool allocation may throw after earlier tasks borrowed\n        // these locals. Drain before unwinding, without stopping persistent workers.\n        struct TranslationDrain {\n            Common::ThreadWorker& worker;\n            bool joined{};\n            ~TranslationDrain() {\n                if (!joined) worker.WaitForRequests();\n            }\n        } translation_drain{shader_translation_workers};\n", ""),
        ("        translation_drain.joined = true;\n", ""),
    ]
    # The snapshot helper removes a contiguous block: prove that block is
    # byte-identical to the already hash-verified native shipping source.
    block_begin = "    // Worker translation must never traverse the live guest GMMU. Snapshot\n"
    block_end = "    if (parallel_translate_stages) {\n" + "        // QueueWork and pool allocation may throw after earlier tasks borrowed\n        // these locals. Drain before unwinding, without stopping persistent workers.\n        struct TranslationDrain {\n            Common::ThreadWorker& worker;\n            bool joined{};\n            ~TranslationDrain() {\n                if (!joined) worker.WaitForRequests();\n            }\n        } translation_drain{shader_translation_workers};\n        size_t parallel_env_index{};\n"
    def snapshot_block(src):
        assert src.count(block_begin) == src.count(block_end) == 1
        start = src.index(block_begin)
        end = src.index(block_end, start)
        return src[start:end]
    assert snapshot_block(generated_raw_n3m) == snapshot_block(native_raw_n3m), (
        "Generated immutable shader inputs differ from reviewed owner")
    generated_n3m = reverse_reviewed_source(generated_n3m, drain_hunks,
                                           "generated translation drain")
    generated_n3m = reverse_immutable_snapshot_successor(generated_n3m)
    generated_n3m = reverse_reviewed_source(generated_n3m, PARALLEL_TIMING_REVERSES,
                                           "generated parallel timing")
    # The historical generator has no cache diagnostic marker in its include
    # prefix, and its preflush declaration was inserted independently of the
    # Vulkan namespace suffix. Retain the exact hunks for the other six edits.
    generated_n3m = reverse_reviewed_source(generated_n3m, [
        ("#include <exception>\n", ""),
        ("#include <stdexcept>\n", ""),
        ("#ifdef PS5_NATIVE\nnamespace VideoCommon {\n"
         "void SetShaderTexturePoolPreflushedForThread(bool preflushed) noexcept;\n"
         "}\n#endif\n\n", ""),
        *PARALLEL_TRANSLATION_REVERSES[2:],
    ], "generated parallel translation")
    actual[n56_name].write_text(generated_n3m)
    print('ENCORE_NS1_GPU23_GENERATOR_EXACT_REVERSE_PASS')
    if generated_n3m.count(n3m_flag) != n3m.count(n3m_flag):
        # A total-count-only failure cannot identify whether the generated
        # or maintained shipping owner omitted a guarded C++ block. Show
        # bounded, exact neighboring source contexts before any repair.
        from collections import Counter
        def guard_contexts(data):
            return Counter(tuple(piece.splitlines()[:3])
                           for piece in data.split(n3m_flag)[1:])
        generated_guards = guard_contexts(generated_n3m)
        maintained_guards = guard_contexts(n3m)
        missing = list((maintained_guards - generated_guards).elements())[:16]
        extra = list((generated_guards - maintained_guards).elements())[:16]
        raise AssertionError('Native PS5 GPU generator lost source guard parity: ' +
            json.dumps({'generator_count': generated_n3m.count(n3m_flag),
                        'owner_count': n3m.count(n3m_flag),
                        'missing_in_generator': missing,
                        'extra_in_generator': extra}, separators=(',', ':')))
    assert 'EDEN_NS2_VULKAN_SHADER_BRIDGE_EXPERIMENTAL' not in generated_n3m, (
        'Removed NS2 research compile profile returned in generator')
    native_compute_guard = "ComputePipeline* PipelineCache::CurrentComputePipeline() {\n#ifdef PS5_NATIVE\n    // An authenticated Ampere compute engine must never enter the legacy\n    // Maxwell ShaderCache::ComputeShader() path: those 128-bit instructions\n    // need the new QMD-scoped native SPIR-V pipeline and resource binding.\n    // Until the renderer owns that real pipeline and submits the dispatch,\n    // reject instead of compiling native bytes as Switch 1 Maxwell.\n    if (Service::Nvidia::Devices::NativeGpuChannelRegistry::Instance()\n            .CaptureComputeTicket(kepler_compute))\n        return nullptr;\n#endif\n\n"
    assert n3m.count(native_compute_guard) == 1, (
        'Native Compute cache admission gate missing from pinned vendor')
    assert generated_n3m.count(native_compute_guard) == 1, (
        'Native Compute cache admission gate missing from generator')
    # First reverse the exact P24 hunks on raw vendor, then N56: both
    # independent receipts must remain valid without conflating their SHAs.
    n3m_pre_mesh = reverse_p24(n56_name, reverse_r23(n56_name, n56_current))
    assert n3m_pre_mesh.count(n56_after) == 1
    n3m_pre_mesh = n3m_pre_mesh.replace(n56_after, n56_before)
    assert generated_n3m == n3m_pre_mesh, (
        'NS2 generator differs from exact R23/P24/N56 reverse-reconstructed vendor')
    print("ENCORE_R23_NATIVE_VS_GENERATOR_REVERSE_PASS",
          "native_R23_unchanged=1 old_generator_equivalent=1")

    # N57's optional ASTC methods are owned by these SAME vendor Vulkan TUs.
    # Reverse only exact reviewed additions, then require original F07 SHA
    # and full generated-source byte parity. No generator files or exemptions.
    from ns2.native_astc_vendor_parity import (
        normalized as normalize_n57, strip_p25_reinterpret,
        strip_gpu18_d32_depth_plane,
    )
    # N57's historical F07 audit deliberately excludes the independently
    # reviewed later P2.5 aspect/scratch additions. Normalize the *generated*
    # owner by those exact, hash-pinned P2.5 deltas as well: the shipped vendor
    # and generator must both retain those corrections before normalization.
    normalized_generated = dict(actual)
    # The GPU-18 D32S8/D32 depth-plane fix is younger than the P2.5
    # source digest. Verify exact newer clauses in the generator and the
    # SHA-pinned shipping vendor, then reverse them solely on the audit copy.
    generated_texture = actual['vk_texture_cache_cost.cpp'].read_text()
    vendor_texture = (active / 'vk_texture_cache_cost.cpp').read_text()
    assert 'mixed_d32_depth_plane' in generated_texture
    assert 'mixed_d32_depth_plane' in vendor_texture
    assert generated_texture.count('mixed_d32_depth_plane') == 5
    assert vendor_texture.count('mixed_d32_depth_plane') == 5
    generated_p25 = strip_p25_reinterpret(
        strip_gpu18_d32_depth_plane(generated_texture))
    print('ENCORE_NS1_GPU18_GENERATOR_EXACT_REVERSE_PASS')
    p25_generated = temp/'normalized-generated-p25'/'vk_texture_cache_cost.cpp'
    p25_generated.parent.mkdir(parents=True,exist_ok=True)
    p25_generated.write_text(generated_p25)
    normalized_generated['vk_texture_cache_cost.cpp'] = p25_generated
    for name, baseline in normalize_n57(root).items():
        p = temp/'normalized-vendor-n57'/name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(baseline)
        normalized_expected[name] = p

    # PS5/Lichii 0078 is a reviewed maintained-source successor to the
    # historical Vulkan generator. Pin both complete shadow TextureCache blobs,
    # remove ONLY the full-clear upload elision in memory, and require the exact
    # pre-0078 owners before ordinary generated-source parity continues.
    shadow_tex_name = 'vulkan-cache/video_core/texture_cache/texture_cache.h'
    shadow_base_name = 'vulkan-cache/video_core/texture_cache/texture_cache_base.h'
    shadow_tex = expected[shadow_tex_name].read_text()
    shadow_base = expected[shadow_base_name].read_text()
    if git_blob_sha(shadow_tex) == '469092ca2a7348b6382d42823d4561e2e1890498':
        # Exact framebuffer compatibility guard; historical audit copy only.
        guard = "        // A newer incompatible alias must not create an invalid Vulkan view,\n        // nor silently promote an older compatible image. Preserve the raw\n        // framebuffer fallback when the freshest candidate cannot be viewed.\n        if (!VideoCore::Surface::IsViewCompatible(\n                slot_images[freshest_id].info.format, view_format,\n                runtime.HasBrokenTextureViewFormats(), runtime.HasNativeBgr())) {\n            return {};\n        }\n"
        assert shadow_tex.count(guard) == 1
        shadow_tex = shadow_tex.replace(guard, '', 1)
        # The current generated and shipping C++ both carry this exact
        # fail-closed framebuffer view guard. Rewind it from BOTH temporary
        # historical comparison copies, never from production sources.
        generated_shadow_tex = normalized_generated[shadow_tex_name].read_text()
        assert generated_shadow_tex.count(guard) == 1, (
            'Generated framebuffer format guard moved or disappeared')
        generated_shadow_tex = generated_shadow_tex.replace(guard, '', 1)
        generated_guard_path = temp/'normalized-generated-ps5-viewguard'/shadow_tex_name
        generated_guard_path.parent.mkdir(parents=True, exist_ok=True)
        generated_guard_path.write_text(generated_shadow_tex)
        normalized_generated[shadow_tex_name] = generated_guard_path
        assert git_blob_sha(shadow_tex) == 'd3252c6ee7726d4536cdb3e27d3c1105837f5e56'
    assert git_blob_sha(shadow_tex) == 'd3252c6ee7726d4536cdb3e27d3c1105837f5e56', (
        'Unreviewed PS5 0078 shadow TextureCache owner')
    assert git_blob_sha(shadow_base) == 'e51b171adae9b7d2e67f72629ef8e49de06f8e9c', (
        'Unreviewed PS5 0078 shadow CacheBase owner')
    scope_begin = '    // Lichii/PS5 patch 0078: a full clear may create a target'
    scope_end = '    auto& flags = maxwell3d->dirty.flags;'
    assert shadow_tex.count(scope_begin) == 1
    lo = shadow_tex.index(scope_begin)
    hi = shadow_tex.index(scope_end, lo)
    shadow_tex = shadow_tex[:lo] + shadow_tex[hi:]
    clear_begin = '    // A new render target that the clear binding overwrites whole needs no'
    clear_end = '\n    if (can_rescale)'
    assert shadow_tex.count(clear_begin) == 1
    lo = shadow_tex.index(clear_begin)
    hi = shadow_tex.index(clear_end, lo)
    shadow_tex = (shadow_tex[:lo] +
                  '    // TODO: Only upload what we need\n'
                  '    RefreshContents(new_image, new_image_id);\n' +
                  shadow_tex[hi:])
    clear_flag = ('    /// True only while UpdateRenderTargets(true) binds a clear target; JoinImages\n'
                  '    /// uses it to skip an initial upload that a proven full clear overwrites.\n'
                  '    bool clearing_render_targets = false;\n')
    assert shadow_base.count(clear_flag) == 1
    shadow_base = shadow_base.replace(clear_flag, '', 1)
    assert git_blob_sha(shadow_tex) == '9f7f0d4633b61b9bc06d6572ad68350e34241f4e', (
        'PS5 0078 shadow normalization did not recover prior TextureCache')
    assert git_blob_sha(shadow_base) == '9a7a8bdcabc860c97f56ca86d5e5f30b8a59169c', (
        'PS5 0078 shadow normalization did not recover prior CacheBase')
    for name, text_value in ((shadow_tex_name, shadow_tex), (shadow_base_name, shadow_base)):
        output = temp/'normalized-vendor-ps5-0078'/name
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text_value)
        normalized_expected[name] = output
    print('ENCORE_PS5_0078_GENERATOR_REVERSE_PARITY_PASS',
          'owners=2', 'current_blobs_pinned=1', 'historical_generator_unchanged=1', flush=True)

    # N72: exact vendor-owned serialized sparse submit API. Preserve full
    # baseline byte-equivalence after removing only these additive guards.
    n72_additions = {
        'include/video_core/renderer_vulkan/vk_scheduler.h': (
            '    // NS2 N72 BEGIN: route sparse page binds through the same submit mutex',
            '    // NS2 N72 END\n',
        ),
        'vulkan_scheduler.cpp': (
            '// NS2 N72 BEGIN: serialized sparse Vulkan page submission',
            '// NS2 N72 END\n\n',
        ),
    }
    for name, (begin, end) in n72_additions.items():
        source = normalized_expected.get(name, expected[name]).read_text()
        assert source.count(begin) == 1 and source.count(end) == 1, (name, 'N72 owner changed')
        first, last = source.index(begin), source.index(end)
        extension = source[first:last + len(end)]
        assert '#ifdef EDEN_NS2_SPARSE_QUEUE_BRIDGE' in extension
        assert 'BindSparseImage(' in extension
        if name.endswith('.cpp'):
            assert 'std::scoped_lock lock{submit_mutex};' in extension
            assert 'device.GetGraphicsQueue().BindSparseImage(' in extension
            assert extension.index('std::scoped_lock lock{submit_mutex};') < extension.index(
                'device.GetGraphicsQueue().BindSparseImage(')
        suffix = last + len(end)
        # Header integration inserted one spacer newline beyond the marker.
        if name.endswith('vk_scheduler.h'):
            assert source[suffix:suffix + 2] == '\n\n', 'N72 header spacing changed'
            suffix += 2
        baseline = source[:first] + source[suffix:]
        normalized = temp/'normalized-vendor-n72'/name
        normalized.parent.mkdir(parents=True, exist_ok=True)
        normalized.write_text(baseline)
        normalized_expected[name] = normalized

    # Reproduce the exact reviewed PS5 presentation-layer high-water policy.
    # Normalization removes only the bounded native replacement; the active
    # renderer still keeps up to 8 idle layers without a device-wide stall.
    blit_name = 'vulkan_blit_screen.cpp'
    blit = expected[blit_name].read_text()
    generated_blit = actual[blit_name].read_text()
    native_layer_policy = (
        "    // The compositor reads exactly framebuffers.size() layers. Preserve a\n"
        "    // bounded high-water reserve so transient HUD layer shrink/growth does\n"
        "    // not destroy GPU-referenced resources and force a device-wide idle.\n"
        "    // More than eight retained layers are reclaimed only after an ordinary\n"
        "    // GPU drain; active layers are never capped or skipped.\n"
        "    constexpr size_t kMaxRetainedLayers = 8;\n"
        "    const bool retire_excess_layers =\n"
        "        layers.size() > kMaxRetainedLayers && layers.size() > framebuffers.size();\n"
        "    if (!rebuild_layers && !retire_excess_layers &&\n"
        "        layers.size() < framebuffers.size()) {"
    )
    baseline_layer_policy = "    if (!rebuild_layers && layers.size() < framebuffers.size()) {"
    native_retirement = (
        "    } else if (rebuild_layers || retire_excess_layers) {\n"
        "        // Only true layout changes or over-budget retirement can destroy\n"
        "        // resources still captured by queued Vulkan command buffers."
    )
    baseline_retirement = (
        "    } else if (rebuild_layers || layers.size() != framebuffers.size()) {\n"
        "        // Removal destroys GPU-referenced descriptors/images. Reconfiguration\n"
        "        // has already waited in the resource_update_required block above."
    )
    assert blit.count(native_layer_policy) == 1, 'PS5 bounded Vulkan layer policy moved'
    assert blit.count(native_retirement) == 1, 'PS5 layer retirement policy moved'
    assert blit.count('WaitIdle(device);') >= 1, 'PS5 layer GPU fence guard absent'
    if blit != generated_blit:
        # Older reviewed generator versions emitted the pre-high-water branch.
        # Current generator reproduces the native change verbatim: do not
        # normalize away a fix the generator already owns.
        baseline_blit = blit.replace(native_layer_policy, baseline_layer_policy)
        baseline_blit = baseline_blit.replace(native_retirement, baseline_retirement)
        assert baseline_blit == generated_blit, 'Unexpected Vulkan presentation delta'
        blit_path = temp / 'normalized-vendor-present-layers' / blit_name
        blit_path.parent.mkdir(parents=True, exist_ok=True)
        blit_path.write_text(baseline_blit)
        normalized_expected[blit_name] = blit_path

    for name in p24_by_path:
        # The 6 reviewed R23 native owners are qualified above by their
        # exact merged source SHA and runtime semantic invariants. The
        # 2026-10 P24 reverse-hunk recipe is not applicable to those files.
        # Reconstruct original exact R23 baseline before applying P24 proof.
        reverse_p24(name, reverse_r23(
            name, reverse_reviewed_fc27_batch_header(name, expected[name].read_text())))
        baseline=reverse_p24(
            name,
            reverse_r23(name, reverse_reviewed_fc27_batch_header(
                name, normalized_expected.get(name, expected[name]).read_text()),
                verify_hash=False),
            verify_hash=False)
        path=temp/'normalized-vendor-p24'/name
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(baseline)
        normalized_expected[name]=path
    # Distinguish maintained SOURCE evolution from the historical test
    # generator: the R09 present-source ABI now carries exact Vulkan
    # sampled-format/sample-count metadata, while an older GPU pipeline
    # header changed only the native MSAA selector documentation and its
    # argument name. Pin the REAL vendor raw Git blobs BEFORE reversing
    # these two changes. Keep the generated artifact itself immutable.
    # The actual NS1/NS2 renderer uses the newer maintained headers.
    post_generator_headers = {
        "include/video_core/renderer_vulkan/vk_blit_screen.h": (
            "dae3449987b134683664d94b5bc13c72724700c2",
            [(
                "    // The sampled native image's exact view format and sample count are\n"
                "    // needed for strict neural LDR/HDR and MSAA source admission.\n"
                "    VkFormat sampled_format{VK_FORMAT_UNDEFINED};\n"
                "    VkSampleCountFlagBits sample_count{VK_SAMPLE_COUNT_1_BIT};\n",
                "",
            )],
        ),
        "include/video_core/renderer_vulkan/vk_pipeline_cache.h": (
            "fcf26ecce586e3cedc17abe6d111ee35f76ad705",
            [
            (
                "    std::unique_ptr<GraphicsPipeline> CreateGraphicsPipeline(\n"
                "        ShaderPools& pools, const GraphicsPipelineCacheKey& key,\n"
                "        std::span<Shader::Environment* const> envs, PipelineStatistics* statistics,\n"
                "        bool build_in_parallel, bool parallel_translate_stages = false);\n",
                "    std::unique_ptr<GraphicsPipeline> CreateGraphicsPipeline(\n"
                "        ShaderPools& pools, const GraphicsPipelineCacheKey& key,\n"
                "        std::span<Shader::Environment* const> envs, PipelineStatistics* statistics,\n"
                "        bool build_in_parallel);\n",
            ),
            (
                "    ShaderPools main_pools;\n"
                "#ifdef PS5_NATIVE\n"
                "    // First-use graphics IR is latency critical and must not wait behind\n"
                "    // driver-pipeline/prewarm jobs queued on the existing builder pool.\n"
                "    Common::ThreadWorker shader_translation_workers;\n"
                "#endif\n",
                "    ShaderPools main_pools;\n",
            ),
            (
                "    // Shared 1x/2x/4x/8x/16x selector. The default NS1 path calls this\n"
                "    // with VK_SAMPLE_COUNT_1_BIT; PS5-native retains authenticated GMMU\n"
                "    // shader capture and the strict forced-MSAA admission path.\n"
                "    [[nodiscard]] GraphicsPipeline* CurrentGraphicsPipelineForMsaa(\n"
                "        VkSampleCountFlagBits requested_samples);\n",
                "    // Creates/selects a distinct native MSAA variant without modifying guest\n"
                "    // registers, image sample counts, or the ordinary 1x pipeline cache key.\n"
                "    // Caller must prove a clear, single colour RT, no depth/aliasing.\n"
                "    [[nodiscard]] GraphicsPipeline* CurrentGraphicsPipelineForMsaa(\n"
                "        VkSampleCountFlagBits samples);\n",
            ),
            ],
        ),
    }
    for name, (raw_sha, edits) in post_generator_headers.items():
        raw = expected[name].read_text()
        assert git_blob_sha(raw) == raw_sha, (
            "Unexpected shipping Vulkan ABI header; no historical normalization", name)
        normalized = raw
        for added, former in edits:
            assert normalized.count(added) == 1, (
                "Reviewed Vulkan ABI header delta moved or duplicated", name)
            normalized = normalized.replace(added, former)
        output = temp/'normalized-vendor-post-generator-headers'/name
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(normalized)
        normalized_expected[name] = output
        if name == "include/video_core/renderer_vulkan/vk_pipeline_cache.h":
            # Both parallel API hunks are also generated today; reverse them
            # on the audit copy before comparison to the historical ABI.
            generated_header = reverse_reviewed_source(
                normalized_generated[name].read_text(), edits[:2],
                "generated parallel graphics ABI")
            generated_path = temp/'normalized-generated-parallel-header'/name
            generated_path.parent.mkdir(parents=True, exist_ok=True)
            generated_path.write_text(generated_header)
            normalized_generated[name] = generated_path
    # N73's strict source normalizer already reverses the SIX native guest
    # colour-attachment capture statements in the maintained texture TU.
    # The historic generator emits these exact statements; reverse them
    # there too, rather than misreporting an otherwise equal texture owner.
    # The real production TU and its N57/N73 SHA receipts are untouched.
    from ns2.native_astc_vendor_parity import strip_post_n73_msaa_framebuffer_source
    tex_name = 'vk_texture_cache_cost.cpp'
    generated_texture = normalized_generated[tex_name].read_text()
    baseline_texture = strip_post_n73_msaa_framebuffer_source(generated_texture)
    assert baseline_texture != generated_texture, (
        "Historical generator has unexpectedly lost native MSAA capture")
    tex_output = temp/'normalized-generated-post-n73'/tex_name
    tex_output.parent.mkdir(parents=True, exist_ok=True)
    tex_output.write_text(baseline_texture)
    normalized_generated[tex_name] = tex_output
    print("ENCORE_POST_GENERATOR_REVIEWED_SOURCE_PARITY",
          "headers=2", "native_texture_capture_statements=6",
          "current_vulkan_source_preserved=1", flush=True)
    # The maintained native MSAA path superseded three historical
    # generator owners. Reconstruct the CI-observed exact source delta
    # instead of weakening parity or rewriting the old generation oracle.
    # BOTH input (original generated) and output (current normalized vendor)
    # must have independently pinned SHA256 from the same real CI run.
    # This recognizes a reviewed post-generator integration layer; it does
    # not claim that the old generator directly emits the new implementation.
    resolve_receipt = json.loads(
        (root / 'tools/fixtures/p04-post-generator-native-resolve-parity.json').read_text())
    assert resolve_receipt['schema_version'] == 1
    assert resolve_receipt['source_vendor_gitlink'] == post['source_vendor_gitlink']
    resolve_paths = {x['path'] for x in resolve_receipt['files']}
    assert resolve_paths == {
        'include/video_core/renderer_vulkan/vk_rasterizer.h',
        'include/video_core/renderer_vulkan/vk_scheduler.h',
        'vulkan_scheduler.cpp',
    }
    # GPU-22 updated the generator's AccelerateDMA header AFTER this
    # frozen P04 resolution receipt was taken. The shipping vendor was
    # already SHA-checked and reversed in the FC27 header witness above;
    # reverse the SAME two exact hunks on the generator's AUDIT COPY
    # before the historical SHA256 and full-file reconstruction.
    raster_header = 'include/video_core/renderer_vulkan/vk_rasterizer.h'
    generated_header = normalized_generated[raster_header].read_text()
    shipping_header = gpu49_predecessor_paths[raster_header].read_text()
    assert git_blob_sha(shipping_header) == (
        'db60043206cc66a284bd3e9327a9fed7b011b25a'), (
        'GPU-22 native Vulkan rasterizer header drift')
    gpu22_header_hunks = (
        ('    explicit AccelerateDMA(BufferCache& buffer_cache, TextureCache& texture_cache,\n'
         '                           Scheduler& scheduler, Tegra::MemoryManager* const& gpu_memory);',
         '    explicit AccelerateDMA(BufferCache& buffer_cache, TextureCache& texture_cache,\n'
         '                           Scheduler& scheduler);'),
        ('    // The GPU address space changes on channel binds. Reference the\n'
         '    // rasterizer\'s active pointer, not a stale construction-time channel.\n'
         '    Tegra::MemoryManager* const& gpu_memory;\n', ''),
    )
    for modern, historic in gpu22_header_hunks:
        assert generated_header.count(modern) == shipping_header.count(modern) == 1, (
            'GPU-22 exact generated header method drift')
        generated_header = generated_header.replace(modern, historic, 1)
    p04_header = temp / 'normalized-generated-gpu22' / raster_header
    p04_header.parent.mkdir(parents=True, exist_ok=True)
    p04_header.write_text(generated_header)
    normalized_generated[raster_header] = p04_header
    print('ENCORE_NS1_GPU22_GENERATOR_HEADER_EXACT_REVERSE_PASS')
    # The native submit-callback registration delta is generated as well.
    # Reverse it on the historical audit copy, not on the shipping header.
    scheduler_header = 'include/video_core/renderer_vulkan/vk_scheduler.h'
    scheduler_generated = normalized_generated[scheduler_header].read_text()
    scheduler_current = "    void RegisterOnSubmit(std::function<void()>&& func) {\n#ifdef PS5_NATIVE\n        // The submit callback executes inside WorkerThread's execution lock.\n        // Registration is owner-only (renderer construction/teardown).\n        std::scoped_lock lock{execution_mutex};\n#endif\n        on_submit = std::move(func);\n    }"
    scheduler_previous = "    void RegisterOnSubmit(std::function<void()>&& func) {\n        on_submit = std::move(func);\n    }"
    assert scheduler_generated.count(scheduler_current) == 1
    scheduler_generated = scheduler_generated.replace(scheduler_current, scheduler_previous, 1)
    scheduler_output = temp / 'normalized-generated-submit-callback' / scheduler_header
    scheduler_output.parent.mkdir(parents=True, exist_ok=True)
    scheduler_output.write_text(scheduler_generated)
    normalized_generated[scheduler_header] = scheduler_output
    resolve_hunks = 0
    for entry in resolve_receipt['files']:
        name = entry['path']
        generated_text = normalized_generated[name].read_text()
        shipping_text = normalized_expected.get(name, expected[name]).read_text()
        digest = lambda x: hashlib.sha256(x.encode('utf-8')).hexdigest()
        assert digest(generated_text) == entry['generated_sha256'], (
            'Unreviewed Vulkan historical generator drift', name)
        assert digest(shipping_text) == entry['normalized_maintained_sha256'], (
            'Unreviewed Vulkan maintained scheduler/MSAA source drift', name)
        normalized = generated_text
        assert 1 <= len(entry['hunks']) <= 4
        for patch in entry['hunks']:
            assert patch['before'] != patch['after']
            assert patch['before'] and patch['after']
            assert normalized.count(patch['before']) == 1, (
                'Native MSAA generator reconstruction anchor drift', name)
            normalized = normalized.replace(patch['before'], patch['after'], 1)
            resolve_hunks += 1
        assert digest(normalized) == entry['normalized_maintained_sha256'], (
            'Native MSAA reconstruction changed a non-reviewed byte', name)
        assert normalized == shipping_text, (
            'Vulkan generated/native resolve source mismatch', name)
        out = temp/'normalized-generator-post-native-resolve'/name
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(normalized)
        normalized_generated[name] = out
    print('ENCORE_NATIVE_MSAA_GENERATOR_RECONSTRUCTION_PASS',
          f'owners={len(resolve_paths)}',
          f'exact_hunks={resolve_hunks}',
          'source_sha256_pinned=1',
          'historical_generator_unchanged=1', flush=True)
    # Native G07: exact production-only pipeline/descriptor-layout gate.
    # The older reviewed source generator does not include this later fail-
    # closed QMD3 path; reverse ONLY its actual hunk for strict byte parity.
    # A changed generator or any unrelated maintained byte still fails.
    compute_name = 'vk_compute_pipeline_cost.cpp'
    g07_previous = "        if (!pipeline) return false;"
    g07_current = "        // A successful native QMD3 dispatch must have both the Vulkan\n        // pipeline layout and every required descriptor-set layout. The\n        // recorded lambda would otherwise silently skip descriptor binding\n        // while the renderer could still mark guest SSBOs as GPU-written.\n        // Empty shaders are allowed to omit a descriptor-set layout.\n        if (!pipeline || !pipeline_layout ||\n            (num_descriptor_entries && !descriptor_set_layout))\n            return false;"
    active_compute = expected[compute_name].read_text()
    # Same reviewed FC27 fixed-sampler repair as the graphics owner above.
    # Normalize its exact current blob to the prior G07-qualified owner first.
    compute_sha = raster_blob(active_compute)
    if compute_sha == '7d9fa72ce2afff5a7b1b75a05fc894b1d99ce6a2':
        fixed_sampler = 'const u32 secondary_offset{desc.secondary_cbuf_offset};'
        indexed_sampler = 'const u32 secondary_offset{desc.secondary_cbuf_offset + index_offset};'
        assert active_compute.count(fixed_sampler) == 1 and indexed_sampler not in active_compute
        active_compute = active_compute.replace(fixed_sampler, indexed_sampler, 1)
        assert raster_blob(active_compute) == '53a545c32a034cfdd3421f381f354a28b306c259'
        print("ENCORE_FC27_COMPUTE_STATIC_SAMPLER_EXACT_RECEIPT_PASS")
    else:
        assert compute_sha == '53a545c32a034cfdd3421f381f354a28b306c259', compute_sha
    assert active_compute.count(g07_current) == 1, (
        'G07 native compute pipeline-layout fail-closed hunk drift')
    historical_compute = active_compute.replace(g07_current, g07_previous, 1)
    native_pipeline_path = temp / 'normalized-vendor-g07' / compute_name
    native_pipeline_path.parent.mkdir(parents=True, exist_ok=True)
    native_pipeline_path.write_text(historical_compute)
    normalized_expected[compute_name] = native_pipeline_path
    print('ENCORE_G07_COMPUTE_LAYOUT_REVERSE_PARITY_PASS',
          'historical_generator=immutable', 'native_guard=fail_closed', flush=True)

    # Reverse ONLY reviewed R2 additions on the isolated research pin. The
    # immutable generator and historical shipping Vulkan parity remain strict.
    if r2_production:
        r2_replacements = {
            'include/video_core/renderer_vulkan/vk_buffer_cache.h': (
                '08b0ad3a99c1509eb23bd6317fdbd9c4b3251b52',
                [
                    ('#ifdef PS5_NATIVE\\n    // Passive source-owner snapshot',
                     '#endif\\n\\n'),
                    ('#if defined(PS5_NATIVE) && defined(EDEN_NS2_STAGE_BACKING)\\n'
                     '    // Strong destination',
                     '#endif\\n\\n'),
                    ('#if defined(PS5_NATIVE) && defined(EDEN_NS2_STAGE_BACKING)\\n'
                     '#include "video_core/renderer_vulkan/ns2_gpu_retirement_hold.h"',
                     '#endif\\n'),
                    ('#if defined(PS5_NATIVE) && defined(EDEN_NS2_STAGE_BACKING)\\n'
                     '    ~BufferCacheRuntime() noexcept;',
                     '#endif\\n\\n'),
                    ('#if defined(PS5_NATIVE) && defined(EDEN_NS2_STAGE_BACKING)\\n'
                     '    // Strong owner type deliberately',
                     '#endif\\n\\n'),
                ]),
            'vk_buffer_cache_cost.cpp': (
                '1877d43aa8facfabf193dac16b8beea3ff7e188e',
                [
                    ('#if defined(PS5_NATIVE) && defined(EDEN_NS2_STAGE_BACKING)\\n'
                     '#include "video_core/renderer_vulkan/ns2_staging_upload_bounds.h"',
                     '#endif\\n\\n'),
                    ('#if defined(PS5_NATIVE) && defined(EDEN_NS2_STAGE_BACKING)\\n'
                     'void BufferCacheRuntime::CopyStagingUpload',
                     '#endif\\n\\n'),
                    ('#if defined(PS5_NATIVE) && defined(EDEN_NS2_STAGE_BACKING)\\n'
                     'BufferCacheRuntime::~BufferCacheRuntime() noexcept',
                     '#endif\\n\\n'),
                    ('#if defined(PS5_NATIVE) && defined(EDEN_NS2_STAGE_BACKING)\\n'
                     '    // Reclaim even with no resident buffers',
                     '#endif\\n'),
                ]),
        }
        for name, (sha, edits) in r2_replacements.items():
            raw = expected[name].read_text()
            if name == 'vk_buffer_cache_cost.cpp' and git_blob_sha(raw) == '873b5552b429f42294c8d410070df0572b4ff84c':
                # Lichii #414 replaces only quad LUT GPU-retirement policy.
                # The frozen R2 staging oracle predates it.
                for after, before in [["#include \"dev_vulkan.h\"\n#include <array>\n#include <cstring>\n#include <limits>\n#include <new>\n#include <span>\n#include <vector>\n","#include \"dev_vulkan.h\"\n#include <array>\n#include <cstring>\n#include <new>\n#include <span>\n#include <vector>\n"],["    virtual ~QuadIndexBuffer() = default;\n\n    void UpdateBuffer(u32 num_indices_) {\n        // Lichii #414: the old LUT can remain referenced by recorded GPU\n        // commands. Reclaim it only after its real submission tick completes,\n        // rather than stalling all GPU work on every index-buffer growth.\n        while (!retired_buffers.empty() && scheduler.IsFree(retired_buffers.front().first)) {\n            retired_buffers.erase(retired_buffers.begin());\n        }\n        if (num_indices_ <= num_indices) {\n            return;\n        }\n\n        if (buffer) {\n            retired_buffers.emplace_back(scheduler.CurrentTick(), std::move(buffer));\n        }\n\n        // Geometric growth avoids repeatedly replacing the LUT for small\n        // draw-count increases. Do not overflow the guest-provided u32 count.\n        const u32 headroom = std::numeric_limits<u32>::max() - num_indices;\n        const u32 grown = num_indices + (std::min)(num_indices / 2, headroom);\n        num_indices = (std::max)(num_indices_, grown);\n        index_type = IndexTypeFromNumElements(device, num_indices);\n\n        const u32 num_quads = GetQuadsNum(num_indices);\n","    virtual ~QuadIndexBuffer() = default;\n\n    void UpdateBuffer(u32 num_indices_) {\n        if (num_indices_ <= num_indices) {\n            return;\n        }\n\n        // The very first LUT has no previous device buffer to protect.\n        // Keep the original GPU fence when replacing an already-used buffer.\n        if (buffer) {\n            { auto timer = Eden::Performance::VulkanTimer(7); scheduler.Finish(); }\n        }\n\n        num_indices = num_indices_;\n        index_type = IndexTypeFromNumElements(device, num_indices);\n\n        const u32 num_quads = GetQuadsNum(num_indices);\n"],["    StagingBufferPool& staging_pool;\n\n    vk::Buffer buffer{};\n    std::vector<std::pair<u64, vk::Buffer>> retired_buffers;\n    MemoryCommit memory_commit{};\n    VkIndexType index_type{};\n    u32 num_indices = 0;\n","    StagingBufferPool& staging_pool;\n\n    vk::Buffer buffer{};\n    MemoryCommit memory_commit{};\n    VkIndexType index_type{};\n    u32 num_indices = 0;\n"]]:
                    assert raw.count(after) == 1, ('Quad LUT exact reverse drift', name)
                    raw = raw.replace(after, before, 1)
                assert git_blob_sha(raw) == '1877d43aa8facfabf193dac16b8beea3ff7e188e', (
                    'Quad LUT predecessor drift', name)
            if name == 'include/video_core/renderer_vulkan/vk_buffer_cache.h':
                # R23 #49 adds a checked descriptor-buffer guard after R2.
                # Reverse that exact full-source fix before testing R2's
                # still-immutable historic header blob.
                r23_new = (
                    "        // In descriptor-buffer mode there is no VkBufferView: creating one\n"
                    "        // before checking a missing address can attempt SurfaceFormat(255).\n"
                    "        // Match Eden upstream 3e6a5566 while keeping legacy views intact.\n"
                    "        if (guest_descriptor_queue.UsesDescriptorBuffer()) {\n"
                    "            const VkDeviceAddress address = buffer.DeviceAddress();\n"
                    "            const VkFormat vk_format = address == 0 ? VK_FORMAT_UNDEFINED : TexelBufferFormat(format);\n"
                    "            guest_descriptor_queue.AddTexelBuffer(VK_NULL_HANDLE, address, offset, size, vk_format);\n"
                    "        } else {\n"
                    "            guest_descriptor_queue.AddTexelBuffer(buffer.View(offset, size, format));\n"
                    "        }")
                r23_old = (
                    "        guest_descriptor_queue.AddTexelBuffer(buffer.View(offset, size, format),\n"
                    "                                              buffer.DeviceAddress(), offset, size,\n"
                    "                                              TexelBufferFormat(format));")
                assert git_blob_sha(raw) == (
                    '76228c0ed7cdb2c2cfa02a473c59365c46e9a466'), 'Unreviewed R23 texel source'
                assert raw.count(r23_new) == 1, 'R23 texel fallback moved'
                raw = raw.replace(r23_new, r23_old)
            assert git_blob_sha(raw) == sha, ('R2 maintained owner changed', name)
            for first, last in edits:
                # The delimiters are exact, nonnested source-owned blocks.
                start = raw.index(first.replace('\\n', '\n'))
                terminator = last.replace('\\n', '\n')
                end = raw.index(terminator, start) + len(terminator)
                assert raw.find(first.replace('\\n', '\n'), end) < 0
                raw = raw[:start] + raw[end:]
            if name == 'vk_buffer_cache_cost.cpp':
                # The guarded include replaced the original blank separator.
                # Restore that one byte-equivalent empty line for oracle parity.
                inc = '#include "video_core/renderer_vulkan/vk_buffer_cache.h"\n'
                after = '#include "video_core/renderer_vulkan/maxwell_to_vk.h"'
                assert raw.count(inc + after) == 1
                raw = raw.replace(inc + after, inc + '\n' + after, 1)
            normalized = temp/'normalized-vendor-r2'/name
            normalized.parent.mkdir(parents=True, exist_ok=True)
            normalized.write_text(raw)
            normalized_expected[name] = normalized
    # The final full-source parity compares a historical R23/P04 audit copy.
    # GPU-22's actual native rasterizer is SHA-pinned above and STILL contains
    # the live-channel GMMU continuity guard. Reverse these THREE exact newer
    # C++ hunks on the generated AUDIT COPY only, matching the previously
    # verified FC27 vendor rewind (not the shipping renderer).
    dma_raster = 'vulkan_rasterizer.cpp'
    # GPU-49 is newer than this GPU-46/GPU-22 checkpoint. Consume the
    # exact pre-GPU49 audit owner already SHA-reconstructed above rather than
    # accepting or restamping the shipping rasterizer.
    current_raster = gpu49_predecessor_paths[dma_raster].read_text()
    # GPU-46 is already exact-reversed above from its three shipping owners.
    # Reuse that SAME pinned edit table before this older GPU-22/GPU-30
    # checkpoint; never accept a new raster hash directly here.
    gpu46_current, gpu46_predecessor, gpu46_raster_edits = gpu46_edits[dma_raster]
    current_raster_blob = git_blob_sha(current_raster)
    if current_raster_blob == gpu46_current:
        for newer, older in gpu46_raster_edits:
            assert current_raster.count(newer) == 1, (
                'GPU-46 direct raster checkpoint hunk drift', newer[:80])
            current_raster = current_raster.replace(newer, older, 1)
        assert git_blob_sha(current_raster) == gpu46_predecessor, (
            'GPU-46 direct raster checkpoint failed to restore predecessor')
        print('ENCORE_NS1_GPU46_DIRECT_RASTER_EXACT_REVERSE_PASS', flush=True)
    else:
        assert current_raster_blob == gpu46_predecessor, (
            'Unreviewed GPU-46 direct raster checkpoint', current_raster_blob)
    # The normalized owner contains reviewed GPU-30 plus GPU-22. Keep the
    # complete predecessor blob strict; later generator-only reversals establish
    # byte equivalence with the frozen historic baseline.
    assert git_blob_sha(current_raster) == (
        'fdd5a73ccf795fd58100469c546b544a86a68e5b'), (
        'Unreviewed GPU-22/GPU-30 normalized Vulkan rasterizer bytes')
    generated_raster = normalized_generated[dma_raster].read_text()
    gpu22_dma_hunks = (
        ('      accelerate_dma(buffer_cache, texture_cache, scheduler, gpu_memory),',
         '      accelerate_dma(buffer_cache, texture_cache, scheduler),'),
        ('AccelerateDMA::AccelerateDMA(BufferCache& buffer_cache_, TextureCache& texture_cache_,\n'
         '                             Scheduler& scheduler_, Tegra::MemoryManager* const& gpu_memory_)\n'
         '    : buffer_cache{buffer_cache_}, texture_cache{texture_cache_}, scheduler{scheduler_},\n'
         '      gpu_memory{gpu_memory_} {}',
         'AccelerateDMA::AccelerateDMA(BufferCache& buffer_cache_, TextureCache& texture_cache_,\n'
         '                             Scheduler& scheduler_)\n'
         '    : buffer_cache{buffer_cache_}, texture_cache{texture_cache_}, scheduler{scheduler_} {}'),
        ('#ifdef PS5_NATIVE\n'
         '    // ObtainBuffer translates only the first GPU VA into one CPU interval.\n'
         '    // A buffer spanning noncontiguous GMMU pages would upload/download\n'
         '    // unrelated physical memory. The normal MaxwellDMA CPU fallback\n'
         '    // supports a page-aware transfer for both image-copy directions.\n'
         '    // Test the channel currently bound to this rasterizer; no stale GMMU.\n'
         '    if (!gpu_memory ||\n'
         '        (!gpu_memory->IsGranularRange(buffer_operand.address, checked_bytes) &&\n'
         '         !gpu_memory->IsContinuousRange(buffer_operand.address, checked_bytes))) {\n'
         '        return false;\n'
         '    }\n'
         '#endif\n', ''),
    )
    for modern, old in gpu22_dma_hunks:
        assert generated_raster.count(modern) == current_raster.count(modern) == 1, (
            'GPU-22 current/native C++ continuity guard drift')
        generated_raster = generated_raster.replace(modern, old, 1)
    historical_raster = temp / 'normalized-generated-gpu22' / dma_raster
    historical_raster.parent.mkdir(parents=True, exist_ok=True)
    historical_raster.write_text(generated_raster)
    normalized_generated[dma_raster] = historical_raster
    print('ENCORE_NS1_GPU22_GENERATOR_CPP_EXACT_REVERSE_PASS')
    # The final byte-parity oracle also compares its generated historical
    # copy after the frozen R23/P04 reconstructions. Require GPU-30's EXACT
    # production block in BOTH the generator and active pinned renderer,
    # then reverse it on the temporary generated audit copy only.
    generated_raster = normalized_generated[dma_raster].read_text()
    # Reuse the GPU-46-normalized shipping owner established at the prior
    # GPU-22 checkpoint. Do not reopen the raw active file and bypass that
    # exact predecessor proof.
    native_raster = current_raster
    reviewed_inline = "#ifdef PS5_NATIVE\n    // One GPU VA range can cross discontiguous device-memory pages. InlineMemory,\n    // texture invalidation and shader/query invalidation accept ONE CPU span:\n    // their first translated DAddr must never stand in for later GMMU pages.\n    // Single device-page writes keep the existing O(1) hot path. For fragmented\n    // but fully mapped spans, WriteBlock invalidates EACH translated physical\n    // segment before writing; it owns the same normal cache notifications.\n    if (!gpu_memory->IsGranularRange(address, copy_size) &&\n        !gpu_memory->IsContinuousRange(address, copy_size)) {\n        if (!gpu_memory->IsFullyMappedRange(address, copy_size)) {\n            return; // No partial writes into an invalid guest DMA mapping.\n        }\n        gpu_memory->WriteBlock(address, memory.data(), copy_size);\n        return;\n    }\n#endif\n"
    assert git_blob_sha(native_raster) == 'fdd5a73ccf795fd58100469c546b544a86a68e5b', (
        'GPU-30 active Vulkan owner changed')
    assert generated_raster.count(reviewed_inline) == 1
    assert native_raster.count(reviewed_inline) == 1
    generated_raster = generated_raster.replace(reviewed_inline, '', 1)
    audit_raster = temp/'normalized-generated-gpu30'/dma_raster
    audit_raster.parent.mkdir(parents=True, exist_ok=True)
    audit_raster.write_text(generated_raster)
    normalized_generated[dma_raster] = audit_raster
    print('ENCORE_NS1_GPU30_GENERATOR_EXACT_REVERSE_PASS')
    mismatches=[name for name in sorted(actual) if not filecmp.cmp(normalized_generated[name],normalized_expected.get(name, expected[name]),shallow=False)]
    if mismatches:
        # Print a tightly bounded exact diff before failing. The generator and
        # active files previously looked equivalent in high-level assertions,
        # forcing repeated CI runs to diagnose a single byte of drift.
        from difflib import unified_diff
        from itertools import islice
        for name in mismatches:
            generated, versioned = normalized_generated[name], normalized_expected.get(name, expected[name])
            # Print BOTH exact bytes' SHA for every failing owner. Without this,
            # the earlier first-five display hid the scheduler and HUD drift,
            # forcing multiple long CI cycles to identify a known mismatch.
            print("VULKAN_ORACLE_OWNER_SHA",
                  name,
                  "generated_sha256=" + hashlib.sha256(generated.read_bytes()).hexdigest(),
                  "maintained_normalized_sha256=" + hashlib.sha256(versioned.read_bytes()).hexdigest(),
                  flush=True)
            if not name.endswith(('.cpp', '.h', '.py', '.cmake')):
                print(f'VULKAN_ORACLE_BINARY_DIFF {name} SHA256={hashlib.sha256(generated.read_bytes()).hexdigest()} '
                      f'active_SHA256={hashlib.sha256(versioned.read_bytes()).hexdigest()}', flush=True)
                continue
            diff = unified_diff(generated.read_text().splitlines(keepends=True),
                                versioned.read_text().splitlines(keepends=True),
                                fromfile=f'generated/{name}', tofile=f'active/{name}')
            for line in islice(diff, 130):
                print(line, end='', flush=True)
        raise AssertionError(f'vendored Vulkan C++ differs from pinned generated source: {mismatches}')
    # Versioned code must compile after fresh clone at a different checkout
    # path: forbids CMake/host absolute paths embedded in generated C++.
    for name, file in expected.items():
        if name.endswith(('.cpp', '.h')):
            data=file.read_text()
            assert '#include "/private/tmp/' not in data and '#include "/home/runner/' not in data,(name,'checkout-specific include')
    assert '#include "performance.h"' in expected['vk_pipeline_cache_cost.cpp'].read_text()
    assert len(actual)>=35
    cmake=(root/'headless/vulkan.cmake').read_text()
    assert 'vendor/encore-active/eden-vulkan' in cmake
    assert 'file(COPY "${EDEN_ACTIVE_VULKAN}/" DESTINATION "${PORT_BUILD_DIR}")' in cmake
    assert 'execute_process(COMMAND python3 "${PORT_ROOT}/tools/prepare-vulkan-port.py"' not in cmake
    print(f'VENDORED_VULKAN_FORK_EQUIVALENT_OK files={len(actual)} active=versioned not regenerated')
