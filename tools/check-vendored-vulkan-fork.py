#!/usr/bin/env python3
"""Verify tracked native Vulkan C++ fork exactly matches validated R337 source generator."""
from pathlib import Path
import filecmp
import json
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
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
    expected_shaders={
        'vert':'b7efb0f17a2cfb2ac044d0d678dfd7f970323deef86c10d25dde8ed723ef0290',
        'frag':'3f5287326b7554164449f5f849f46aae3d2f69ff3a0b4c5c822055bd1877c6d6',
    }
    for stage, digest in expected_shaders.items():
        source=root/'headless'/f'vulkan_hud.{stage}'
        assert hashlib.sha256(source.read_bytes()).hexdigest()==digest,source
        assert (active/f'vulkan_hud.{stage}.spv').is_file()
    # The reviewed 2026-11-08 palette/contrast shader source must match
    # its real glslang-compiled, spirv-val-checked Vulkan 1.1 artifact.
    # A source-only pin is insufficient: the old 2026-10-30 SPIR-V was stale.
    assert hashlib.sha256((active/'vulkan_hud.frag.spv').read_bytes()).hexdigest()==(
        '029a4bb7c594cc3beadefc731a67768e9f80987ae10a2cb20a5a197a8ebea10b'
    ), 'Vulkan HUD SPIR-V has drifted from the validated palette shader'
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
        core_owner = root / 'vendor/encore-active/eden-core/src/video_core/buffer_cache/buffer_cache.h'
        assert subprocess.check_output(
            ['git', 'hash-object', str(core_owner)], text=True).strip() == (
            '469eddd0ea9e0a3498446bf08ab473caac3b76f9'), (
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
        combined = expected[name].read_text()
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
            reverse_p24(name, reverse_r23(name, expected[name].read_text()))
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
        reverse_p24(name, reverse_r23(name, expected[name].read_text()))
        baseline=reverse_p24(
            name,
            reverse_r23(name, normalized_expected.get(name, expected[name]).read_text(),
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
