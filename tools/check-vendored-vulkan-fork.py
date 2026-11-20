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
from ci.ps5_cache_diag_receipt import normalize_for_historical_proof
root=Path(__file__).resolve().parents[1]
active=root/'vendor/encore-active/eden-vulkan'
upstream=root/'vendor/sources/eden'
assert (upstream/'VENDOR-ORIGIN.json').exists()
assert (active/'vulkan_renderer.cpp').exists()
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
            '8bab5ee14daa1d316fbac6b3643823967d53e376'
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
    # A reviewed, startup-only vendor diagnostic may add seven tiny source
    # blocks. Check its EXACT raw Git blob and reverse ONLY those blocks
    # before the immutable R23/P24 and generated-Vulkan source oracles.
    # Never edit the pinned vendor source or normalize other Vulkan owners.
    native_cache_owner = 'vk_pipeline_cache_cost.cpp'
    cache_source = expected[native_cache_owner].read_text()
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
    # FC27 shader attribute-source fix: reverse only the exact reviewed
    # vendor successor on an audit COPY. The compiled native code stays
    # untouched; every full source blob and its exact historic preimage are
    # checked before the old Vulkan generator/R23 receipt runs.
    reviewed_fc27_hunks = {"shader_recompiler/ir_opt/texture_pass.cpp":{"current":"0010ffd43e7ac3fb482c46277c854ab9a76b06ab","predecessor":"889456a31ddeb87e411ce4d0d2d41078b9593244","hunks":[["    };\n}\n\n// Preserve the exact guest varying component supplying a bindless handle.\n// The old bool discarded this identity and the rasterizer guessed the first\n// integer input, which may be an unrelated vertex attribute.\nstd::optional<u32> IsAttributeSourcedHandle(const IR::Value& handle) {\n    if (handle.IsImmediate()) return std::nullopt;\n    const IR::Inst* inst{handle.InstRecursive()};\n    if (!inst) return std::nullopt;\n    if (inst->GetOpcode() == IR::Opcode::BitCastU32F32 && !inst->Arg(0).IsImmediate()) {\n        inst = inst->Arg(0).InstRecursive();\n    }\n    if (!inst || (inst->GetOpcode() != IR::Opcode::GetAttribute &&\n                  inst->GetOpcode() != IR::Opcode::GetAttributeU32))\n        return std::nullopt;\n    // Only generic varyings map to vertex attribute slots. System values\n    // (PrimitiveId, VertexId, etc.) are not valid texture-handle sources.\n    constexpr u32 first = static_cast<u32>(IR::Attribute::Generic0X);\n    constexpr u32 last = static_cast<u32>(IR::Attribute::Generic31W);\n    const u32 attribute = static_cast<u32>(inst->Arg(0).Attribute());\n    if (attribute < first || attribute > last) return std::nullopt;\n    if (!inst->Arg(1).IsEmpty() &&\n        (!inst->Arg(1).IsImmediate() || inst->Arg(1).U32() != 0))\n        return std::nullopt;\n    return attribute;\n}\n\nTextureInst MakeInst(Environment& env, IR::Block* block, IR::Inst& inst, const HostTranslateInfo& host_info) {\n    ConstBufferAddr addr;\n    if (IsBindless(inst)) {\n        const std::optional<ConstBufferAddr> track_addr{TrackCached(inst.Arg(0), env, host_info, block)};\n\n        const auto attribute_source = host_info.support_attribute_texture_handle\n                                          ? IsAttributeSourcedHandle(inst.Arg(0))\n                                          : std::nullopt;\n        if (track_addr) {\n            addr = *track_addr;\n        } else if (attribute_source) {\n            addr = ConstBufferAddr{\n                .index = ATTRIBUTE_HANDLE_CBUF_INDEX,\n                // No descriptor ABI change: this field is unused for the\n                // sentinel and can carry the exact GenericN component.\n                .offset = *attribute_source,\n                .shift_left = 0,\n                .secondary_index = 0,\n                .secondary_offset = 0,\n","    };\n}\n\nbool IsAttributeSourcedHandle(const IR::Value& handle) {\n    if (handle.IsImmediate()) {\n        return false;\n    }\n    const IR::Inst* inst{handle.InstRecursive()};\n    if (inst->GetOpcode() == IR::Opcode::BitCastU32F32 && !inst->Arg(0).IsImmediate()) {\n        inst = inst->Arg(0).InstRecursive();\n    }\n    return inst->GetOpcode() == IR::Opcode::GetAttribute ||\n           inst->GetOpcode() == IR::Opcode::GetAttributeU32;\n}\n\nTextureInst MakeInst(Environment& env, IR::Block* block, IR::Inst& inst, const HostTranslateInfo& host_info) {\n    ConstBufferAddr addr;\n    if (IsBindless(inst)) {\n        const std::optional<ConstBufferAddr> track_addr{TrackCached(inst.Arg(0), env, host_info, block)};\n\n        if (track_addr) {\n            addr = *track_addr;\n        } else if (host_info.support_attribute_texture_handle &&\n                   IsAttributeSourcedHandle(inst.Arg(0))) {\n            addr = ConstBufferAddr{\n                .index = ATTRIBUTE_HANDLE_CBUF_INDEX,\n                .offset = 0,\n                .shift_left = 0,\n                .secondary_index = 0,\n                .secondary_offset = 0,\n"]]},"include/video_core/renderer_vulkan/vk_graphics_pipeline.h":{"current":"515a766a6cc4d6fcba7692ad396f45396b746d28","predecessor":"bafff9a441a60b3dfb7e7d5a7a260741f45f59dc","hunks":[["#include <condition_variable>\n#include <functional>\n#include <mutex>\n#include <optional>\n#include <type_traits>\n#include <vector>\n\n","#include <condition_variable>\n#include <functional>\n#include <mutex>\n#include <type_traits>\n#include <vector>\n\n"],["    [[nodiscard]] bool UsesAttributeHandle() const noexcept {\n        return uses_attribute_handle;\n    }\n    [[nodiscard]] std::optional<u32> AttributeHandleSource() const noexcept {\n        return attribute_handle_source;\n    }\n    void SetAttributeHandle(u32 handle) noexcept {\n        attribute_handle = handle;\n    }\n","    [[nodiscard]] bool UsesAttributeHandle() const noexcept {\n        return uses_attribute_handle;\n    }\n    void SetAttributeHandle(u32 handle) noexcept {\n        attribute_handle = handle;\n    }\n"],["    u32 num_textures{};\n    u32 attribute_handle{};\n    bool uses_attribute_handle{};\n    // GenericN component encoded in the existing sentinel descriptor offset.\n    // Empty for legacy cached shaders or conflicting attributes across stages.\n    std::optional<u32> attribute_handle_source{};\n    // Immutable shader layout: no UBO/SSBO/TBO means no host buffer work.\n    std::array<bool, NUM_STAGES> stage_has_host_buffer_bindings{};\n    std::array<bool, NUM_STAGES> stage_has_image_bindings{};\n","    u32 num_textures{};\n    u32 attribute_handle{};\n    bool uses_attribute_handle{};\n    // Immutable shader layout: no UBO/SSBO/TBO means no host buffer work.\n    std::array<bool, NUM_STAGES> stage_has_host_buffer_bindings{};\n    std::array<bool, NUM_STAGES> stage_has_image_bindings{};\n"]]},"include/video_core/renderer_vulkan/vk_rasterizer.h":{"current":"6467fd4d704de6b77deb7e6cba4b8e33f70f5a08","predecessor":"7c754c82c12c4f4c934abd3d7f2cdb25222e8d2a","hunks":[["    void CollectAttributeHandleRuns(bool is_indexed);\n    std::vector<AttributeHandleRun> attribute_handle_runs;\n    GraphicsPipeline* attribute_handle_pipeline{};\n    std::optional<u32> attribute_handle_source{};\n    bool split_attribute_handles{};\n\n    void FlushWork();\n","    void CollectAttributeHandleRuns(bool is_indexed);\n    std::vector<AttributeHandleRun> attribute_handle_runs;\n    GraphicsPipeline* attribute_handle_pipeline{};\n    bool split_attribute_handles{};\n\n    void FlushWork();\n"]]},"vk_graphics_pipeline_cost.cpp":{"current":"2834a18fe7638749ec83cc8f5feb1fcde6c71a9a","predecessor":"526aa16b22ba3918c29ce85c884d606dcfd185a1","hunks":[["        num_image_elements += storage_views;\n        num_descriptor_entries += NumDescriptorEntries(*info);\n        for (const auto& desc : info->texture_descriptors) {\n            if (desc.cbuf_index != Shader::ATTRIBUTE_HANDLE_CBUF_INDEX)\n                continue;\n            if (!uses_attribute_handle) {\n                attribute_handle_source = desc.cbuf_offset;\n            } else if (attribute_handle_source &&\n                       *attribute_handle_source != desc.cbuf_offset) {\n                // A single per-run handle cannot represent two different\n                // shader varyings. Preserve the old unspecialized path.\n                attribute_handle_source.reset();\n            }\n            uses_attribute_handle = true;\n        }\n    }\n    fragment_has_color0_output = stage_infos[NUM_STAGES - 1].stores_frag_color[0];\n","        num_image_elements += storage_views;\n        num_descriptor_entries += NumDescriptorEntries(*info);\n        for (const auto& desc : info->texture_descriptors) {\n            uses_attribute_handle |= desc.cbuf_index == Shader::ATTRIBUTE_HANDLE_CBUF_INDEX;\n        }\n    }\n    fragment_has_color0_output = stage_infos[NUM_STAGES - 1].stores_frag_color[0];\n"]]},"vulkan_rasterizer.cpp":{"current":"046269f8484776e22c8aee308b75c7b98f8bf5c6","predecessor":"9da620ea3f4a4e0ab22e9747bf4e1058c09ce20b","hunks":[["    // draw calls may be split into handle-homogeneous runs.\n    const auto prepare_attribute_handles = [&] {\n        attribute_handle_pipeline = nullptr;\n        attribute_handle_source.reset();\n        attribute_handle_runs.clear();\n        if (split_attribute_handles && !pipeline->IsMeshPipeline() && pipeline->UsesAttributeHandle()) {\n            attribute_handle_source = pipeline->AttributeHandleSource();\n            CollectAttributeHandleRuns(is_indexed);\n            if (!attribute_handle_runs.empty()) {\n                attribute_handle_pipeline = pipeline;\n","    // draw calls may be split into handle-homogeneous runs.\n    const auto prepare_attribute_handles = [&] {\n        attribute_handle_pipeline = nullptr;\n        attribute_handle_runs.clear();\n        if (split_attribute_handles && !pipeline->IsMeshPipeline() && pipeline->UsesAttributeHandle()) {\n            CollectAttributeHandleRuns(is_indexed);\n            if (!attribute_handle_runs.empty()) {\n                attribute_handle_pipeline = pipeline;\n"],["    if (total == 0) return;\n\n    const VertexAttribute* source{};\n    u32 component_byte_offset{};\n    if (attribute_handle_source) {\n        // Generic0X..Generic31W are four consecutive IR values per input.\n        // Only 32-bit components can be read as an unmodified texture handle.\n        constexpr u32 first = static_cast<u32>(Shader::IR::Attribute::Generic0X);\n        constexpr u32 last = static_cast<u32>(Shader::IR::Attribute::Generic31W);\n        const u32 encoded = *attribute_handle_source;\n        if (encoded >= first && encoded <= last) {\n            const u32 generic = (encoded - first) / 4;\n            const u32 component = (encoded - first) % 4;\n            if (generic < regs.vertex_attrib_format.size()) {\n                const auto& attr = regs.vertex_attrib_format[generic];\n                const bool is_32bit =\n                    attr.size == VertexAttribute::Size::Size_R32 ||\n                    attr.size == VertexAttribute::Size::Size_R32_G32 ||\n                    attr.size == VertexAttribute::Size::Size_R32_G32_B32 ||\n                    attr.size == VertexAttribute::Size::Size_R32_G32_B32_A32;\n                if (!attr.constant && is_32bit && component < attr.ComponentCount() &&\n                    (attr.type == VertexAttribute::Type::UInt ||\n                     attr.type == VertexAttribute::Type::SInt ||\n                     attr.type == VertexAttribute::Type::Float)) {\n                    source = &attr;\n                    component_byte_offset = component * sizeof(u32);\n                }\n            }\n        }\n    }\n    if (!source) {\n        // Legacy cached shader metadata (offset=0) retains its old lookup\n        // until the shader is recompiled. Never guess a component on an\n        // unsupported packed or normalized attribute format.\n        for (const auto& attr : regs.vertex_attrib_format) {\n            if (attr.constant || attr.size == VertexAttribute::Size::Invalid) continue;\n            if (attr.type == VertexAttribute::Type::UInt ||\n                attr.type == VertexAttribute::Type::SInt) {\n                source = &attr;\n                break;\n            }\n        }\n    }\n    if (!source) {\n","    if (total == 0) return;\n\n    const VertexAttribute* source{};\n    for (const auto& attr : regs.vertex_attrib_format) {\n        if (attr.constant || attr.size == VertexAttribute::Size::Invalid) continue;\n        if (attr.type == VertexAttribute::Type::UInt ||\n            attr.type == VertexAttribute::Type::SInt) {\n            source = &attr;\n            break;\n        }\n    }\n    if (!source) {\n"],["\n    const u32 primitive_size =\n        state.topology == Maxwell::PrimitiveTopology::Triangles ? 3 : total;\n    const GPUVAddr base_address = stream.Address() + source->offset +\n                                 component_byte_offset;\n    const auto read_handle = [&](u32 position) {\n        u32 vertex{};\n        if (is_indexed) {\n","\n    const u32 primitive_size =\n        state.topology == Maxwell::PrimitiveTopology::Triangles ? 3 : total;\n    const GPUVAddr base_address = stream.Address() + source->offset;\n    const auto read_handle = [&](u32 position) {\n        u32 vertex{};\n        if (is_indexed) {\n"],["    SCOPE_EXIT {\n        split_attribute_handles = false;\n        attribute_handle_pipeline = nullptr;\n        attribute_handle_source.reset();\n        attribute_handle_runs.clear();\n    };\n    PrepareDraw(is_indexed, [this, is_indexed, instance_count] {\n","    SCOPE_EXIT {\n        split_attribute_handles = false;\n        attribute_handle_pipeline = nullptr;\n        attribute_handle_runs.clear();\n    };\n    PrepareDraw(is_indexed, [this, is_indexed, instance_count] {\n"]]}}
    if exact_vendor_pin in {
        'ce1c02b1ce14697003798e3f9872015035984719',
        'c47770d49dc8ed5f09838004f5bd08d9b1d5abc8',
    }:
        for name, witness in reviewed_fc27_hunks.items():
            if name.startswith('shader_recompiler/'):
                raw_path = root/'vendor/encore-active/eden-shader/src'/name
            else:
                raw_path = active/name
            real_source = raw_path.read_text()
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
        assert raster_blob(receipt_text) == (
            '236713fa06672b39e2a4b9a84907882bbbb1bbbd'
            if exact_vendor_pin in {'8153654a2f1fe809fb2caa28dcadca90a7661446', '6c38328fbef33de747f5c31ea30d13541a513a4a', '8e564f61e6c8b86149ce0a0d6d2aa323a268dda6', '67759611edc13414c112ea9d2b6664d54827a200'} else
            '18bf879c31b6d29b77b8fc6cc3026f8bd7fc0ec2')
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
    # Combined R23 EDS3 + subgroup + mesh + sparse-residency ABI is now a
    # maintained source blob, not only the two-hunk original Task/Mesh delta.
    # Keep a hard content pin so unrelated header drift remains rejected.
    combined_device_sha = 'acab7cf039c2be7bcc830ac684be2fff285a3e8a'
    assert subprocess.check_output(
        ['git', 'hash-object', str(expected[native_mesh_device_header])],
        text=True).strip() == combined_device_sha, (
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
        if pair_vendor_pin in {'2ccc4b0a714ca621ac2879768f87118a64ed65f6', '97ac02f263ec90f40a029f4aa62980c76bc25d5c', '9a83a6ba1cb464c9e5d14457cab18ad511c1104b', 'd0246caf58a3127597bba1edfc1f8dcbe0c5cfdc', '2a450d43d1d23d3e8b1667e396613f62c69c26d7', '17c95ef233a9a0e508e50ada4ae9dc53a300c46c', '082cd1b77c7df80dc422eae5ba59d9cd33e48dc4', 'e0fced3a091495e70362d8c4ca072942f027af24', '491fa7e2388d46e23827b1459360a5d7f4a2814b', 'b177deb8282b14e1521485f5ac63bd7ccc9ca7ef', '06fc7dc2e0a00e00f831dfd78ae78087736276a3', '850086c79ec40838663989a81f33ba8ea2f15f6a'}:
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
    def git_blob_sha(text):
        data=text.encode('utf-8')
        return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
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
    generated_n3m = actual[n56_name].read_text()
    assert generated_n3m.count(n3m_flag) == n3m.count(n3m_flag), (
        'Native PS5 GPU generator lost source guard parity')
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
    )
    # N57's historical F07 audit deliberately excludes the independently
    # reviewed later P2.5 aspect/scratch additions. Normalize the *generated*
    # owner by those exact, hash-pinned P2.5 deltas as well: the shipped vendor
    # and generator must both retain those corrections before normalization.
    normalized_generated = dict(actual)
    generated_p25 = strip_p25_reinterpret(actual['vk_texture_cache_cost.cpp'].read_text())
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
            "343383c7b5ed55f181cee9d840e6b59fae0409d0",
            [(
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
            )],
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
