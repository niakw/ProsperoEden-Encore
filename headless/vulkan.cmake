if(NOT PS5_NATIVE)
    message(FATAL_ERROR "EDEN_PS5_VULKAN requires PS5_NATIVE")
endif()
# R342: compile our versioned patched Vulkan sources directly, not transient
# string replacements applied at every CMake configure. Upstream originals
# remain in vendor/sources/eden and their Git bundle; this tree is OUR fork.
set(EDEN_ACTIVE_VULKAN "${PORT_ROOT}/vendor/encore-active/eden-vulkan")
if(NOT EXISTS "${EDEN_ACTIVE_VULKAN}/vulkan_renderer.cpp")
    message(FATAL_ERROR "Missing checked-in Encore Vulkan fork")
endif()
file(COPY "${EDEN_ACTIVE_VULKAN}/" DESTINATION "${PORT_BUILD_DIR}")
# P5: the extracted native Eden cache can carry an older FixedPipelineState
# header without the native forced-colour-resolve bit used by the maintained
# Vulkan pipeline. Select the *pinned vendor source header* (same POD layout,
# its reserved bit 22 now named) for ALL native consumers, not a CMake-generated
# reconstruction or a local copy of the definition.
set(EDEN_P5_FIXED_PIPELINE_HEADER
    "${EDEN_ACTIVE_VULKAN}/include/video_core/renderer_vulkan/fixed_pipeline_state.h")
if(NOT EXISTS "${EDEN_P5_FIXED_PIPELINE_HEADER}")
    message(FATAL_ERROR "Missing pinned fixed pipeline state ABI header")
endif()
file(MAKE_DIRECTORY "${PORT_BUILD_DIR}/include/video_core/renderer_vulkan"
                    "${PORT_BUILD_DIR}/include/video_core/texture_cache")
configure_file("${EDEN_P5_FIXED_PIPELINE_HEADER}"
    "${PORT_BUILD_DIR}/include/video_core/renderer_vulkan/fixed_pipeline_state.h" COPYONLY)
# Keep the pinned ns2-astc texture-cache source itself immutable. Its native
# channel lease relies on SCOPE_EXIT; make that existing macro visible through
# a thin include-only bridge, then include_next the same maintained header.
configure_file("${EDEN_PORT_DIR}/ns2_astc_texture_cache_scope_bridge.h"
    "${PORT_BUILD_DIR}/include/video_core/texture_cache/texture_cache.h" COPYONLY)
# Encore owns the versioned native renderer and its header; no generated
# source injection or changes to the pinned vendor repository.
configure_file("${EDEN_PORT_DIR}/renderer_vulkan_r08.h"
    "${PORT_BUILD_DIR}/include/video_core/renderer_vulkan/renderer_vulkan.h" COPYONLY)
configure_file("${EDEN_PORT_DIR}/vk_present_manager_r08.h"
    "${PORT_BUILD_DIR}/include/video_core/renderer_vulkan/vk_present_manager.h" COPYONLY)
configure_file("${EDEN_PORT_DIR}/window_adapt_pass_r08.h"
    "${PORT_BUILD_DIR}/include/video_core/renderer_vulkan/present/window_adapt_pass.h" COPYONLY)
configure_file("${EDEN_PORT_DIR}/vulkan_present_layer_r24.h"
    "${PORT_BUILD_DIR}/include/video_core/renderer_vulkan/present/layer.h" COPYONLY)
configure_file("${EDEN_PORT_DIR}/vulkan_fxaa_r24.h"
    "${PORT_BUILD_DIR}/include/video_core/renderer_vulkan/present/fxaa.h" COPYONLY)

# R07: REAL AMD FSR 3.1.4 temporal upscaler shader passes (MIT SDK
# source pinned in our vendor), never substituted with spatial FSR1.
# Always compile in native PS5 video_core; release decisions are external.
set(EDEN_AMD_FSR31_SOURCE_DIR "${PORT_ROOT}/vendor/encore-active/amd-fsr31")
set(EDEN_AMD_FSR31_BACKEND_DIR "${PORT_ROOT}/vendor/encore-active/eden-vulkan")
if(NOT EXISTS "${EDEN_AMD_FSR31_SOURCE_DIR}/LICENSE.txt")
    message(FATAL_ERROR "Missing versioned FidelityFX SDK FSR3.1.4 and MIT license in vendor")
endif()
find_package(Python3 COMPONENTS Interpreter REQUIRED)
find_program(EDEN_R07_FSR31_GLSLANG NAMES glslangValidator REQUIRED)
find_program(EDEN_R07_FSR31_SPIRV_VAL NAMES spirv-val REQUIRED)
find_program(EDEN_R07_FSR31_SPIRV_DIS NAMES spirv-dis REQUIRED)
set(EDEN_FSR31_SHADER_DIR "${PORT_BUILD_DIR}/include/video_core/host_shaders")
set(EDEN_FSR31_NAMES
    prepare_inputs luma_pyramid luma_pyramid_nowave
    shading_change_pyramid shading_change_pyramid_nowave
    shading_change prepare_reactivity luma_instability
    accumulate accumulate_sharpen rcas)
set(EDEN_FSR31_HEADERS "")
set(EDEN_FSR31_BINARIES "")
foreach(shader IN LISTS EDEN_FSR31_NAMES)
    list(APPEND EDEN_FSR31_HEADERS
        "${EDEN_FSR31_SHADER_DIR}/fsr3_upscaler_${shader}_comp_spv.h")
    list(APPEND EDEN_FSR31_BINARIES
        "${EDEN_FSR31_SHADER_DIR}/fsr3_upscaler_${shader}.spv")
endforeach()
file(GLOB_RECURSE EDEN_FSR31_SDK_FILES CONFIGURE_DEPENDS
    "${EDEN_AMD_FSR31_SOURCE_DIR}/include/*"
    "${EDEN_AMD_FSR31_SOURCE_DIR}/shaders/*")
add_custom_command(
    OUTPUT ${EDEN_FSR31_HEADERS}
    BYPRODUCTS ${EDEN_FSR31_BINARIES}
    COMMAND "${Python3_EXECUTABLE}"
        "${PORT_ROOT}/tools/graphics/build-fsr31-amd-shaders.py"
        --vendor "${EDEN_AMD_FSR31_SOURCE_DIR}"
        --output "${EDEN_FSR31_SHADER_DIR}" --keep-spv
    # Fail the native build if AMD's actual SPIR-V descriptor or UBO ABI
    # differs from the C++ Vulkan host layouts (no runtime bind mismatch).
    COMMAND "${Python3_EXECUTABLE}"
        "${PORT_ROOT}/tools/graphics/check-fsr31-spirv-abi.py"
        --shader-dir "${EDEN_FSR31_SHADER_DIR}"
        --backend-source "${EDEN_AMD_FSR31_BACKEND_DIR}/fsr31_temporal_upscaler.cpp"
        --spirv-dis "${EDEN_R07_FSR31_SPIRV_DIS}"
    DEPENDS
        "${PORT_ROOT}/tools/graphics/build-fsr31-amd-shaders.py"
        "${PORT_ROOT}/tools/graphics/check-fsr31-spirv-abi.py"
        "${EDEN_AMD_FSR31_BACKEND_DIR}/fsr31_temporal_upscaler.cpp"
        ${EDEN_FSR31_SDK_FILES}
    VERBATIM)
add_custom_target(eden-r07-fsr31-shaders DEPENDS ${EDEN_FSR31_HEADERS})
add_dependencies(video_core eden-r07-fsr31-shaders)
# Descriptor pools in upstream Eden only allocate combined image-samplers;
# FSR31 requires real SAMPLED_IMAGE and immutable SAMPLER descriptor counts.
# Override the shared bank layout and pool allocator TOGETHER, not one alone.
configure_file("${EDEN_AMD_FSR31_BACKEND_DIR}/include/video_core/renderer_vulkan/vk_descriptor_pool.h"
    "${PORT_BUILD_DIR}/include/video_core/renderer_vulkan/vk_descriptor_pool.h"
    COPYONLY)
configure_file("${EDEN_AMD_FSR31_BACKEND_DIR}/fsr31_temporal_upscaler.h"
    "${PORT_BUILD_DIR}/include/video_core/renderer_vulkan/vk_fsr3_upscaler.h"
    COPYONLY)
configure_file("${EDEN_AMD_FSR31_BACKEND_DIR}/include/video_core/renderer_vulkan/fsr31_native_bridge.h"
    "${PORT_BUILD_DIR}/include/video_core/renderer_vulkan/fsr31_native_bridge.h"
    COPYONLY)
# R24 real Vulkan multisample colour shadow+resolve primitive (not yet wired
# into guest pipeline sample selection; no active forced-MSAA menu).
configure_file("${EDEN_AMD_FSR31_BACKEND_DIR}/include/video_core/renderer_vulkan/msaa_color_shadow_pass.h"
    "${PORT_BUILD_DIR}/include/video_core/renderer_vulkan/msaa_color_shadow_pass.h"
    COPYONLY)
list(REMOVE_ITEM video_sources renderer_vulkan/vk_descriptor_pool.cpp)
list(APPEND video_sources
    "${EDEN_AMD_FSR31_BACKEND_DIR}/fsr31_descriptor_pool.cpp"
    "${EDEN_AMD_FSR31_BACKEND_DIR}/fsr31_temporal_upscaler.cpp"
    "${EDEN_AMD_FSR31_BACKEND_DIR}/fsr31_native_bridge.cpp"
    "${EDEN_AMD_FSR31_BACKEND_DIR}/msaa_color_shadow_pass.cpp"
    "${EDEN_AMD_FSR31_BACKEND_DIR}/anime4k_3d.cpp"
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_projection.cpp"
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_token_repack.cpp"
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_upsample_view.cpp"
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_noise_field.cpp"
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_decoder_upsample.cpp"
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_decoder_fp32_to_fp16.cpp"
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_native_decoder_link.cpp"
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_decoder_tile_to_linear.cpp"
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_neural_bottleneck.cpp"
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_image_feature_stage.cpp"
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_postblock_mix.cpp"
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_postblock_run.cpp"
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_preblock_run.cpp"
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_preblock_pool.cpp"
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_proxy_feature_stage.cpp"
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_proxy_lift_link.cpp"
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_proxy_fswin_link.cpp"
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_split_decoder_skip_repack.cpp"
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_window_attention.cpp"
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_qkv_projection.cpp"
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_split_window_link.cpp"
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_split_window_model_buffers.cpp"
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_ffwd3.cpp"
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_split_ffwd_layer.cpp"
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_split_residual_projection.cpp"
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_split_context_repack.cpp"
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_split_swin_block.cpp"
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_split_swin_run.cpp"
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_split_projection_pool.cpp"
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_split_final_head.cpp"
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_vit_attention.cpp"
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_vit_qkv_norm.cpp"
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_vit_epilogue.cpp"
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_vit_qkv_attention_link.cpp"
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_vit_projection_stage.cpp"
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_vit_block.cpp"
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_vit_run.cpp"
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_vit_boundary_repack.cpp"
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_vit_model_buffers.cpp"
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_vit_gpu_tensors.cpp"
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_vit_qkv_subgraph.cpp"
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_float_quantize.cpp"
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_projection_quantized.cpp"
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_fswin_dense.cpp"
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_fswin_qkv.cpp"
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_fswin_graph.cpp"
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_gpu_weights.cpp"
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_fswin_descriptors.cpp"
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_fswin_gpu_tensors.cpp"
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_fswin_layer_runtime.cpp"
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_fswin_chain.cpp"
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_fswin_window_repack.cpp"
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_fswin_raster_layout.cpp"
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_fswin_output_view.cpp"
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_fswin_downsample.cpp"
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_fswin_downsample_output.cpp"
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_fswin_level_link.cpp"
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_unet_skip_cache.cpp"
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_unet_down_sequence.cpp"
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_unet_bottleneck_link.cpp"
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_unet_up_sequence.cpp"
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_core_feature_sequence.cpp"
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_frame_session.cpp"
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_frame_readback.cpp"
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_nohistory_compose.cpp"
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_temporal_compose.cpp"
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_hdr_proxy.cpp"
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_nohistory_present.cpp"
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_texture_proxy.cpp"
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_fswin_upsample.cpp"
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_fswin_upsample_output.cpp"
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_unet_upsample_link.cpp")
set_property(SOURCE
    "${EDEN_AMD_FSR31_BACKEND_DIR}/fsr31_temporal_upscaler.cpp"
    "${EDEN_AMD_FSR31_BACKEND_DIR}/fsr31_native_bridge.cpp"
    TARGET_DIRECTORY video_core APPEND PROPERTY OBJECT_DEPENDS
    ${EDEN_FSR31_HEADERS})
set_property(SOURCE
    "${PROJECT_SOURCE_DIR}/src/video_core/renderer_vulkan/vk_compute_pass.cpp"
    "${PROJECT_SOURCE_DIR}/src/video_core/renderer_vulkan/vk_compute_pipeline.cpp"
    "${PROJECT_SOURCE_DIR}/src/video_core/renderer_vulkan/vk_pipeline_cache.cpp"
    TARGET_DIRECTORY video_core APPEND PROPERTY OBJECT_DEPENDS
    "${PORT_BUILD_DIR}/include/video_core/renderer_vulkan/vk_descriptor_pool.h")

# R09: genuine MIT Anime4K-v4 3D CNN x2 neural spatial super-resolution.
# Source/weights and deterministic translator are pinned in vendor. All
# four Vulkan compute stages are built and validated on HOST, never PS5.
# This is separate from non-neural SGSR/FSR1 and from temporal FSR 3.1.
set(EDEN_R09_CNN_DIR "${EDEN_AMD_FSR31_BACKEND_DIR}/r09_anime4k_3d")
set(EDEN_R09_CNN_HEADERS "")
foreach(stage RANGE 0 3)
    list(APPEND EDEN_R09_CNN_HEADERS
        "${EDEN_FSR31_SHADER_DIR}/anime4k_3d_us_stage_${stage}_comp_spv.h")
endforeach()
add_custom_command(
    OUTPUT ${EDEN_R09_CNN_HEADERS}
    COMMAND "${Python3_EXECUTABLE}"
        "${EDEN_R09_CNN_DIR}/compile_anime4k_3d.py"
        --output "${EDEN_FSR31_SHADER_DIR}" --validate
    DEPENDS
        "${EDEN_R09_CNN_DIR}/Anime4K_3DGraphics_Upscale_x2_US.glsl"
        "${EDEN_R09_CNN_DIR}/compile_anime4k_3d.py"
    COMMENT "Build original Anime4K v4 3D CNN x2 MIT model as 4 Vulkan compute SPIR-V stages"
    VERBATIM)
# Two additional pinned neural CNNs. Build all kernels on the host.
set(EDEN_R09_PROFILE_HEADERS "")
foreach(stage RANGE 0 3)
    list(APPEND EDEN_R09_PROFILE_HEADERS
        "${EDEN_FSR31_SHADER_DIR}/anime4k_soft_stage_${stage}_comp_spv.h")
endforeach()
foreach(stage RANGE 0 4)
    list(APPEND EDEN_R09_PROFILE_HEADERS
        "${EDEN_FSR31_SHADER_DIR}/anime4k_denoise_stage_${stage}_comp_spv.h")
endforeach()
add_custom_command(
    OUTPUT ${EDEN_R09_PROFILE_HEADERS}
    COMMAND "${Python3_EXECUTABLE}"
        "${EDEN_R09_CNN_DIR}/compile_anime4k_profiles.py"
        --output "${EDEN_FSR31_SHADER_DIR}" --validate
    DEPENDS
        "${EDEN_R09_CNN_DIR}/Anime4K_Restore_CNN_Soft_S.glsl"
        "${EDEN_R09_CNN_DIR}/Anime4K_Upscale_Denoise_CNN_x2_S.glsl"
        "${EDEN_R09_CNN_DIR}/compile_anime4k_profiles.py"
    COMMENT "Compile nine pinned CNN restore/denoise stages for Vulkan"
    VERBATIM)
add_custom_target(eden-r09-anime4k-profiles DEPENDS ${EDEN_R09_PROFILE_HEADERS})
add_custom_target(eden-r09-anime4k-3d-shaders DEPENDS ${EDEN_R09_CNN_HEADERS})
add_dependencies(video_core eden-r09-anime4k-profiles eden-r09-anime4k-3d-shaders)
set_property(SOURCE "${EDEN_AMD_FSR31_BACKEND_DIR}/anime4k_3d.cpp"
    TARGET_DIRECTORY video_core APPEND PROPERTY OBJECT_DEPENDS
    ${EDEN_R09_CNN_HEADERS} ${EDEN_R09_PROFILE_HEADERS})

# R09: RDNA2-compatible base GEMM for a future verified neural graph.
# This compiled primitive is NOT a DLSS menu/release option. It implements
# one 1x1 projection with E4M3FN byte weights, FP32 compute and strict
# descriptor/push ABI; unlike RDNA4 it requires no FP8/cooperative matrices.
set(EDEN_R09_RDNA2_PROJ_HEADER
    "${EDEN_FSR31_SHADER_DIR}/rdna2_nr_fp8_proj_comp_spv.h")
add_custom_command(
    OUTPUT "${EDEN_R09_RDNA2_PROJ_HEADER}"
    COMMAND "${Python3_EXECUTABLE}"
        "${EDEN_PORT_DIR}/../tools/graphics/test-rdna2-nr-spv.py"
        --vendor "${EDEN_AMD_FSR31_BACKEND_DIR}/../.."
        --header "${EDEN_R09_RDNA2_PROJ_HEADER}"
    DEPENDS
        "${EDEN_AMD_FSR31_BACKEND_DIR}/r09_rdna2_nr/fp8_proj_rdna2.comp"
        "${EDEN_PORT_DIR}/../tools/graphics/test-rdna2-nr-spv.py"
    COMMENT "Compile and ABI-validate a portable RDNA2 neural 1x1 projection"
    VERBATIM)
add_custom_target(eden-r09-rdna2-nr-projection-spv
    DEPENDS "${EDEN_R09_RDNA2_PROJ_HEADER}")
add_dependencies(video_core eden-r09-rdna2-nr-projection-spv)
set_property(SOURCE "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_projection.cpp"
    TARGET_DIRECTORY video_core APPEND PROPERTY OBJECT_DEPENDS
    "${EDEN_R09_RDNA2_PROJ_HEADER}")

# R09 RDNA2: lossless 4x4-token permutation, one shader storage buffer.
# Separate source and destination byte ranges must not overlap (host policy).
set(EDEN_R09_RDNA2_REPACK_HEADER
    "${EDEN_FSR31_SHADER_DIR}/rdna2_nr_repack_tokens_comp_spv.h")
add_custom_command(
    OUTPUT "${EDEN_R09_RDNA2_REPACK_HEADER}"
    COMMAND "${Python3_EXECUTABLE}"
        "${EDEN_PORT_DIR}/../tools/graphics/test-rdna2-repack-spv.py"
        --vendor "${EDEN_AMD_FSR31_BACKEND_DIR}/../.."
        --header "${EDEN_R09_RDNA2_REPACK_HEADER}"
    DEPENDS
        "${EDEN_AMD_FSR31_BACKEND_DIR}/r09_rdna2_nr/repack_tokens_rdna2.comp"
        "${EDEN_PORT_DIR}/../tools/graphics/test-rdna2-repack-spv.py"
    COMMENT "Compile and validate portable RDNA2 neural token layout permutation"
    VERBATIM)
add_custom_target(eden-r09-rdna2-nr-repack-spv
    DEPENDS "${EDEN_R09_RDNA2_REPACK_HEADER}")
add_dependencies(video_core eden-r09-rdna2-nr-repack-spv)
set_property(SOURCE "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_token_repack.cpp"
    TARGET_DIRECTORY video_core APPEND PROPERTY OBJECT_DEPENDS
    "${EDEN_R09_RDNA2_REPACK_HEADER}")

# Third RDNA2 neural building block: padded upsample view using uvec4
# token copies. No model weight, no GPU cooperative matrix requirement.
set(EDEN_R09_RDNA2_UPVIEW_HEADER
    "${EDEN_FSR31_SHADER_DIR}/rdna2_nr_upsample_view_comp_spv.h")
add_custom_command(
    OUTPUT "${EDEN_R09_RDNA2_UPVIEW_HEADER}"
    COMMAND "${Python3_EXECUTABLE}"
        "${EDEN_PORT_DIR}/../tools/graphics/test-rdna2-upview-spv.py"
        --vendor "${EDEN_AMD_FSR31_BACKEND_DIR}/../.."
        --header "${EDEN_R09_RDNA2_UPVIEW_HEADER}"
    DEPENDS
        "${EDEN_AMD_FSR31_BACKEND_DIR}/r09_rdna2_nr/upsample_view_rdna2.comp"
        "${EDEN_PORT_DIR}/../tools/graphics/test-rdna2-upview-spv.py"
    COMMENT "Compile and ABI-validate RDNA2 neural padded view conversion"
    VERBATIM)
add_custom_target(eden-r09-rdna2-nr-upview-spv
    DEPENDS "${EDEN_R09_RDNA2_UPVIEW_HEADER}")
add_dependencies(video_core eden-r09-rdna2-nr-upview-spv)
set_property(SOURCE "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_upsample_view.cpp"
    TARGET_DIRECTORY video_core APPEND PROPERTY OBJECT_DEPENDS
    "${EDEN_R09_RDNA2_UPVIEW_HEADER}")

# R09 RDNA2: deterministic noise features for the neural input pre-block.
# Vulkan 1.1 FP16 packing (core packHalf2x16), no cooperative matrices.
set(EDEN_R09_RDNA2_NOISE_HEADER
    "${EDEN_FSR31_SHADER_DIR}/rdna2_nr_noise_field_comp_spv.h")
add_custom_command(
    OUTPUT "${EDEN_R09_RDNA2_NOISE_HEADER}"
    COMMAND "${Python3_EXECUTABLE}"
        "${EDEN_PORT_DIR}/../tools/graphics/test-rdna2-noise-spv.py"
        --vendor "${EDEN_AMD_FSR31_BACKEND_DIR}/../.."
        --header "${EDEN_R09_RDNA2_NOISE_HEADER}"
    DEPENDS
        "${EDEN_AMD_FSR31_BACKEND_DIR}/r09_rdna2_nr/noise_field_rdna2.comp"
        "${EDEN_PORT_DIR}/../tools/graphics/test-rdna2-noise-spv.py"
    COMMENT "Compile and ABI-validate RDNA2 neural noise field"
    VERBATIM)
add_custom_target(eden-r09-rdna2-nr-noise-spv
    DEPENDS "${EDEN_R09_RDNA2_NOISE_HEADER}")
add_dependencies(video_core eden-r09-rdna2-nr-noise-spv)
set_property(SOURCE "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_noise_field.cpp"
    TARGET_DIRECTORY video_core APPEND PROPERTY OBJECT_DEPENDS
    "${EDEN_R09_RDNA2_NOISE_HEADER}")

# R09 RDNA2: nearest-2x neural decoder FP16 skip + FP8 quantization.
set(EDEN_R09_RDNA2_DECODER_HEADER
    "${EDEN_FSR31_SHADER_DIR}/rdna2_nr_decoder_upsample_comp_spv.h")
add_custom_command(
    OUTPUT "${EDEN_R09_RDNA2_DECODER_HEADER}"
    COMMAND "${Python3_EXECUTABLE}"
        "${EDEN_PORT_DIR}/../tools/graphics/test-rdna2-decoder-spv.py"
        --vendor "${EDEN_AMD_FSR31_BACKEND_DIR}/../.."
        --header "${EDEN_R09_RDNA2_DECODER_HEADER}"
    DEPENDS
        "${EDEN_AMD_FSR31_BACKEND_DIR}/r09_rdna2_nr/decoder_upsample_rdna2.comp"
        "${EDEN_PORT_DIR}/../tools/graphics/test-rdna2-decoder-spv.py"
    COMMENT "Compile and ABI-validate RDNA2 neural decoder upsample"
    VERBATIM)
add_custom_target(eden-r09-rdna2-nr-decoder-spv
    DEPENDS "${EDEN_R09_RDNA2_DECODER_HEADER}")
add_dependencies(video_core eden-r09-rdna2-nr-decoder-spv)
set_property(SOURCE "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_decoder_upsample.cpp"
    TARGET_DIRECTORY video_core APPEND PROPERTY OBJECT_DEPENDS
    "${EDEN_R09_RDNA2_DECODER_HEADER}")

# R09 native geometry bridge: convert ViT 4x4 C1024 FP8 tiles to
# raster-major GEMM tokens. Required for 33x60, Original + Compact.
set(EDEN_R09_DECODER_TILE_LINEAR_HEADER
    "${EDEN_FSR31_SHADER_DIR}/rdna2_nr_decoder_tile_linear_comp_spv.h")
add_custom_command(
    OUTPUT "${EDEN_R09_DECODER_TILE_LINEAR_HEADER}"
    COMMAND "${Python3_EXECUTABLE}"
        "${PORT_ROOT}/tools/graphics/test-rdna2-decoder-tile-linear-spv.py"
        --vendor "${PORT_ROOT}/vendor"
        --header "${EDEN_R09_DECODER_TILE_LINEAR_HEADER}"
    DEPENDS
        "${EDEN_AMD_FSR31_BACKEND_DIR}/r09_rdna2_nr/decoder_tile_linear_rdna2.comp"
        "${PORT_ROOT}/tools/graphics/test-rdna2-decoder-tile-linear-spv.py"
    COMMENT "Compile and ABI-validate native ViT->GEMM tiled raster conversion"
    VERBATIM)
add_custom_target(eden-r09-decoder-tile-linear-spv
    DEPENDS "${EDEN_R09_DECODER_TILE_LINEAR_HEADER}")
add_dependencies(video_core eden-r09-decoder-tile-linear-spv)
set_property(SOURCE
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_decoder_tile_to_linear.cpp"
    TARGET_DIRECTORY video_core APPEND PROPERTY OBJECT_DEPENDS
    "${EDEN_R09_DECODER_TILE_LINEAR_HEADER}")

# R09: real sampled guest VkImage -> normalized, transposed first-frame
# feature input raster. Source format and lifetime are externally checked.
set(EDEN_R09_TEXTURE_PROXY_HEADER
    "${EDEN_FSR31_SHADER_DIR}/rdna2_nr_texture_proxy_comp_spv.h")
add_custom_command(
    OUTPUT "${EDEN_R09_TEXTURE_PROXY_HEADER}"
    COMMAND "${Python3_EXECUTABLE}"
        "${PORT_ROOT}/tools/graphics/test-rdna2-texture-proxy-spv.py"
        --vendor "${EDEN_AMD_FSR31_BACKEND_DIR}/../.."
        --header "${EDEN_R09_TEXTURE_PROXY_HEADER}"
    DEPENDS
        "${EDEN_AMD_FSR31_BACKEND_DIR}/r09_rdna2_nr/texture_proxy_rdna2.comp"
        "${PORT_ROOT}/tools/graphics/test-rdna2-texture-proxy-spv.py"
    COMMENT "Validate Vulkan 1.1 guest image neural proxy ABI"
    VERBATIM)
add_custom_target(eden-r09-texture-proxy-spv
    DEPENDS "${EDEN_R09_TEXTURE_PROXY_HEADER}")
add_dependencies(video_core eden-r09-texture-proxy-spv)
set_property(SOURCE
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_texture_proxy.cpp"
    TARGET_DIRECTORY video_core APPEND PROPERTY OBJECT_DEPENDS
    "${EDEN_R09_TEXTURE_PROXY_HEADER}")

# R09: publish native transposed FP32 RGB to a sampled RGBA32F Vulkan
# image, owned and synchronized by the embedding renderer.
set(EDEN_R09_NOHISTORY_PRESENT_HEADER
    "${EDEN_FSR31_SHADER_DIR}/rdna2_nr_nohistory_present_comp_spv.h")
add_custom_command(
    OUTPUT "${EDEN_R09_NOHISTORY_PRESENT_HEADER}"
    COMMAND "${Python3_EXECUTABLE}"
        "${PORT_ROOT}/tools/graphics/test-rdna2-nohistory-present-spv.py"
        --vendor "${EDEN_AMD_FSR31_BACKEND_DIR}/../.."
        --header "${EDEN_R09_NOHISTORY_PRESENT_HEADER}"
    DEPENDS
        "${EDEN_AMD_FSR31_BACKEND_DIR}/r09_rdna2_nr/nohistory_present_rdna2.comp"
        "${PORT_ROOT}/tools/graphics/test-rdna2-nohistory-present-spv.py"
    COMMENT "Compile and ABI-validate neural first-frame image publication"
    VERBATIM)
add_custom_target(eden-r09-nohistory-present-spv
    DEPENDS "${EDEN_R09_NOHISTORY_PRESENT_HEADER}")
add_dependencies(video_core eden-r09-nohistory-present-spv)
set_property(SOURCE
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_nohistory_present.cpp"
    TARGET_DIRECTORY video_core APPEND PROPERTY OBJECT_DEPENDS
    "${EDEN_R09_NOHISTORY_PRESENT_HEADER}")

# R09: HDR linear RGBA32F -> verified sRGB proxy before neural features.
set(EDEN_R09_HDR_PROXY_HEADER
    "${EDEN_FSR31_SHADER_DIR}/rdna2_nr_hdr_proxy_comp_spv.h")
add_custom_command(
    OUTPUT "${EDEN_R09_HDR_PROXY_HEADER}"
    COMMAND "${Python3_EXECUTABLE}"
        "${PORT_ROOT}/tools/graphics/test-rdna2-hdr-proxy-spv.py"
        --vendor "${EDEN_AMD_FSR31_BACKEND_DIR}/../.."
        --header "${EDEN_R09_HDR_PROXY_HEADER}"
    DEPENDS
        "${EDEN_AMD_FSR31_BACKEND_DIR}/r09_rdna2_nr/hdr_proxy_rdna2.comp"
        "${PORT_ROOT}/tools/graphics/test-rdna2-hdr-proxy-spv.py"
    COMMENT "Compile and ABI-validate R09 paper-white HDR image proxy"
    VERBATIM)
add_custom_target(eden-r09-hdr-proxy-spv
    DEPENDS "${EDEN_R09_HDR_PROXY_HEADER}")
add_dependencies(video_core eden-r09-hdr-proxy-spv)
set_property(SOURCE
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_hdr_proxy.cpp"
    TARGET_DIRECTORY video_core APPEND PROPERTY OBJECT_DEPENDS
    "${EDEN_R09_HDR_PROXY_HEADER}")

# R09 learned four-channel head and real temporal-history blending.
set(EDEN_R09_TEMPORAL_COMPOSE_HEADER
    "${EDEN_FSR31_SHADER_DIR}/rdna2_nr_temporal_compose_comp_spv.h")
add_custom_command(
    OUTPUT "${EDEN_R09_TEMPORAL_COMPOSE_HEADER}"
    COMMAND "${Python3_EXECUTABLE}"
        "${PORT_ROOT}/tools/graphics/test-rdna2-temporal-compose-spv.py"
        --vendor "${EDEN_AMD_FSR31_BACKEND_DIR}/../.."
        --header "${EDEN_R09_TEMPORAL_COMPOSE_HEADER}"
    DEPENDS
        "${EDEN_AMD_FSR31_BACKEND_DIR}/r09_rdna2_nr/temporal_compose_rdna2.comp"
        "${PORT_ROOT}/tools/graphics/test-rdna2-temporal-compose-spv.py"
    COMMENT "Validate R09 neural learned temporal history shader"
    VERBATIM)
add_custom_target(eden-r09-temporal-compose-spv
    DEPENDS "${EDEN_R09_TEMPORAL_COMPOSE_HEADER}")
add_dependencies(video_core eden-r09-temporal-compose-spv)
set_property(SOURCE
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_temporal_compose.cpp"
    TARGET_DIRECTORY video_core APPEND PROPERTY OBJECT_DEPENDS
    "${EDEN_R09_TEMPORAL_COMPOSE_HEADER}")

# R09: first-frame-only RGB residual output from the learned post-head.
# No HDR, temporal history, source capture or presentation is implied.
set(EDEN_R09_NR_NOHISTORY_HEADER
    "${EDEN_FSR31_SHADER_DIR}/rdna2_nr_nohistory_compose_comp_spv.h")
add_custom_command(
    OUTPUT "${EDEN_R09_NR_NOHISTORY_HEADER}"
    COMMAND "${Python3_EXECUTABLE}"
        "${PORT_ROOT}/tools/graphics/test-rdna2-nohistory-compose-spv.py"
        --vendor "${EDEN_AMD_FSR31_BACKEND_DIR}/../.."
        --header "${EDEN_R09_NR_NOHISTORY_HEADER}"
    DEPENDS
        "${EDEN_AMD_FSR31_BACKEND_DIR}/r09_rdna2_nr/nohistory_compose_rdna2.comp"
        "${PORT_ROOT}/tools/graphics/test-rdna2-nohistory-compose-spv.py"
    COMMENT "Compile and validate R09 learned RGB residual no-history compositor"
    VERBATIM)
add_custom_target(eden-r09-nohistory-image-spv
    DEPENDS "${EDEN_R09_NR_NOHISTORY_HEADER}")
add_dependencies(video_core eden-r09-nohistory-image-spv)
set_property(SOURCE
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_nohistory_compose.cpp"
    TARGET_DIRECTORY video_core APPEND PROPERTY OBJECT_DEPENDS
    "${EDEN_R09_NR_NOHISTORY_HEADER}")

# R09 no-history 16-channel neural proxy from pre-normalized RGBA32F.
set(EDEN_R09_PROXY_FEATURE_HEADER
    "${EDEN_FSR31_SHADER_DIR}/rdna2_nr_proxy_features_comp_spv.h")
add_custom_command(
    OUTPUT "${EDEN_R09_PROXY_FEATURE_HEADER}"
    COMMAND "${Python3_EXECUTABLE}"
        "${PORT_ROOT}/tools/graphics/test-rdna2-proxy-features-spv.py"
        --vendor "${PORT_ROOT}/vendor"
        --header "${EDEN_R09_PROXY_FEATURE_HEADER}"
    DEPENDS
        "${EDEN_AMD_FSR31_BACKEND_DIR}/r09_rdna2_nr/proxy_features_rdna2.comp"
        "${PORT_ROOT}/tools/graphics/test-rdna2-proxy-features-spv.py"
    COMMENT "Validate Vulkan 1.1 first-frame neural proxy feature shader"
    VERBATIM)
add_custom_target(eden-r09-proxy-feature-spv
    DEPENDS "${EDEN_R09_PROXY_FEATURE_HEADER}")
add_dependencies(video_core eden-r09-proxy-feature-spv)
set_property(SOURCE
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_proxy_feature_stage.cpp"
    TARGET_DIRECTORY video_core APPEND PROPERTY OBJECT_DEPENDS
    "${EDEN_R09_PROXY_FEATURE_HEADER}")

# R09 learned pre/post **feature** matrices (not an RGB/depth adapter).
# The model-provided [32,16] and [16,32] matrices remain external.
set(EDEN_R09_IMAGE_FEATURE_HEADER
    "${EDEN_FSR31_SHADER_DIR}/rdna2_nr_image_feature_comp_spv.h")
add_custom_command(
    OUTPUT "${EDEN_R09_IMAGE_FEATURE_HEADER}"
    COMMAND "${Python3_EXECUTABLE}"
        "${PORT_ROOT}/tools/graphics/test-rdna2-image-feature-spv.py"
        --vendor "${PORT_ROOT}/vendor"
        --header "${EDEN_R09_IMAGE_FEATURE_HEADER}"
    DEPENDS
        "${EDEN_AMD_FSR31_BACKEND_DIR}/r09_rdna2_nr/image_feature_rdna2.comp"
        "${PORT_ROOT}/tools/graphics/test-rdna2-image-feature-spv.py"
    COMMENT "Compile and validate RDNA2 learned pre/post feature matrices"
    VERBATIM)
add_custom_target(eden-r09-image-feature-spv
    DEPENDS "${EDEN_R09_IMAGE_FEATURE_HEADER}")
add_dependencies(video_core eden-r09-image-feature-spv)
set_property(SOURCE
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_image_feature_stage.cpp"
    TARGET_DIRECTORY video_core APPEND PROPERTY OBJECT_DEPENDS
    "${EDEN_R09_IMAGE_FEATURE_HEADER}")

# R09: genuine FP16 raw preblock output 2x2 pool; no FP8 skip shortcut.
set(EDEN_R09_PREBLOCK_POOL_HEADER
    "${EDEN_FSR31_SHADER_DIR}/rdna2_nr_preblock_pool_comp_spv.h")
add_custom_command(
    OUTPUT "${EDEN_R09_PREBLOCK_POOL_HEADER}"
    COMMAND "${Python3_EXECUTABLE}"
        "${PORT_ROOT}/tools/graphics/test-rdna2-preblock-pool-spv.py"
        --vendor "${PORT_ROOT}/vendor"
        --header "${EDEN_R09_PREBLOCK_POOL_HEADER}"
    DEPENDS
        "${EDEN_AMD_FSR31_BACKEND_DIR}/r09_rdna2_nr/preblock_pool_rdna2.comp"
        "${PORT_ROOT}/tools/graphics/test-rdna2-preblock-pool-spv.py"
    COMMENT "Build raw FP16 preblock C32 2x2 pool Vulkan shader"
    VERBATIM)
add_custom_target(eden-r09-preblock-pool-spv
    DEPENDS "${EDEN_R09_PREBLOCK_POOL_HEADER}")
add_dependencies(video_core eden-r09-preblock-pool-spv)
set_property(SOURCE
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_preblock_pool.cpp"
    TARGET_DIRECTORY video_core APPEND PROPERTY OBJECT_DEPENDS
    "${EDEN_R09_PREBLOCK_POOL_HEADER}")

# R09: learned postblock C32 2x main/skip mixer.
set(EDEN_R09_POSTBLOCK_MIX_HEADER
    "${EDEN_FSR31_SHADER_DIR}/rdna2_nr_postblock_mix_comp_spv.h")
add_custom_command(
    OUTPUT "${EDEN_R09_POSTBLOCK_MIX_HEADER}"
    COMMAND "${Python3_EXECUTABLE}"
        "${PORT_ROOT}/tools/graphics/test-rdna2-postblock-mix-spv.py"
        --vendor "${PORT_ROOT}/vendor"
        --header "${EDEN_R09_POSTBLOCK_MIX_HEADER}"
    DEPENDS
        "${EDEN_AMD_FSR31_BACKEND_DIR}/r09_rdna2_nr/postblock_mix_rdna2.comp"
        "${PORT_ROOT}/tools/graphics/test-rdna2-postblock-mix-spv.py"
    COMMENT "Compile RDNA2 native learned postblock main/skip mixer"
    VERBATIM)
add_custom_target(eden-r09-postblock-mix-spv
    DEPENDS "${EDEN_R09_POSTBLOCK_MIX_HEADER}")
add_dependencies(video_core eden-r09-postblock-mix-spv)
set_property(SOURCE
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_postblock_mix.cpp"
    TARGET_DIRECTORY video_core APPEND PROPERTY OBJECT_DEPENDS
    "${EDEN_R09_POSTBLOCK_MIX_HEADER}")

# R09: learned native decoder [512,1024] uses a shared FP32->FP16
# Vulkan 1.1 epilogue before the independent-buffer skip/upsample pass.
set(EDEN_R09_DECODER_FP16_HEADER
    "${EDEN_FSR31_SHADER_DIR}/rdna2_nr_decoder_fp32_to_fp16_comp_spv.h")
add_custom_command(
    OUTPUT "${EDEN_R09_DECODER_FP16_HEADER}"
    COMMAND "${Python3_EXECUTABLE}"
        "${PORT_ROOT}/tools/graphics/test-rdna2-decoder-fp32-to-fp16-spv.py"
        --vendor "${PORT_ROOT}/vendor"
        --header "${EDEN_R09_DECODER_FP16_HEADER}"
    DEPENDS
        "${EDEN_AMD_FSR31_BACKEND_DIR}/r09_rdna2_nr/decoder_fp32_to_fp16_rdna2.comp"
        "${PORT_ROOT}/tools/graphics/test-rdna2-decoder-fp32-to-fp16-spv.py"
    COMMENT "Compile and validate native decoder FP32->FP16 Vulkan compute"
    VERBATIM)
add_custom_target(eden-r09-decoder-fp16-spv
    DEPENDS "${EDEN_R09_DECODER_FP16_HEADER}")
add_dependencies(video_core eden-r09-decoder-fp16-spv)
set_property(SOURCE
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_decoder_fp32_to_fp16.cpp"
    TARGET_DIRECTORY video_core APPEND PROPERTY OBJECT_DEPENDS
    "${EDEN_R09_DECODER_FP16_HEADER}")

# R09 native Split-Swin ProjPool primary tensor -> decoder tile/channel
# ABI. Both layouts are model-owned and require an exact GPU conversion.
set(EDEN_R09_SPLIT_DECODER_SKIP_REPACK_HEADER
    "${EDEN_FSR31_SHADER_DIR}/rdna2_nr_split_decoder_skip_repack_comp_spv.h")
add_custom_command(
    OUTPUT "${EDEN_R09_SPLIT_DECODER_SKIP_REPACK_HEADER}"
    COMMAND "${Python3_EXECUTABLE}"
        "${PORT_ROOT}/tools/graphics/test-rdna2-split-decoder-skip-spv.py"
        --vendor "${PORT_ROOT}/vendor"
        --header "${EDEN_R09_SPLIT_DECODER_SKIP_REPACK_HEADER}"
    DEPENDS
        "${EDEN_AMD_FSR31_BACKEND_DIR}/r09_rdna2_nr/split_decoder_skip_repack_rdna2.comp"
        "${PORT_ROOT}/tools/graphics/test-rdna2-split-decoder-skip-spv.py"
    COMMENT "Compile and validate Split-Swin native decoder skip layout"
    VERBATIM)
add_custom_target(eden-r09-split-decoder-skip-spv
    DEPENDS "${EDEN_R09_SPLIT_DECODER_SKIP_REPACK_HEADER}")
add_dependencies(video_core eden-r09-split-decoder-skip-spv)
set_property(SOURCE
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_split_decoder_skip_repack.cpp"
    TARGET_DIRECTORY video_core APPEND PROPERTY OBJECT_DEPENDS
    "${EDEN_R09_SPLIT_DECODER_SKIP_REPACK_HEADER}")

# R09 RDNA2: unfused 64-token x 32-channel attention/context pass.
# Host already provides Q/K/V in normalized preprojected E4M3FN layout.
set(EDEN_R09_RDNA2_ATTN_HEADER
    "${EDEN_FSR31_SHADER_DIR}/rdna2_nr_window_attention_comp_spv.h")
add_custom_command(
    OUTPUT "${EDEN_R09_RDNA2_ATTN_HEADER}"
    COMMAND "${Python3_EXECUTABLE}"
        "${EDEN_PORT_DIR}/../tools/graphics/test-rdna2-attention-spv.py"
        --vendor "${EDEN_AMD_FSR31_BACKEND_DIR}/../.."
        --header "${EDEN_R09_RDNA2_ATTN_HEADER}"
    DEPENDS
        "${EDEN_AMD_FSR31_BACKEND_DIR}/r09_rdna2_nr/window_attention_rdna2.comp"
        "${EDEN_PORT_DIR}/../tools/graphics/test-rdna2-attention-spv.py"
    COMMENT "Compile and ABI-validate RDNA2 unfused neural attention"
    VERBATIM)
add_custom_target(eden-r09-rdna2-nr-attention-spv
    DEPENDS "${EDEN_R09_RDNA2_ATTN_HEADER}")
add_dependencies(video_core eden-r09-rdna2-nr-attention-spv)
set_property(SOURCE "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_window_attention.cpp"
    TARGET_DIRECTORY video_core APPEND PROPERTY OBJECT_DEPENDS
    "${EDEN_R09_RDNA2_ATTN_HEADER}")

# R09 RDNA2: baseline row-major QKV projection.
set(EDEN_R09_RDNA2_QKV_HEADER
    "${EDEN_FSR31_SHADER_DIR}/rdna2_nr_qkv_projection_comp_spv.h")
add_custom_command(
    OUTPUT "${EDEN_R09_RDNA2_QKV_HEADER}"
    COMMAND "${Python3_EXECUTABLE}"
        "${EDEN_PORT_DIR}/../tools/graphics/test-rdna2-qkv-spv.py"
        --vendor "${EDEN_AMD_FSR31_BACKEND_DIR}/../.."
        --header "${EDEN_R09_RDNA2_QKV_HEADER}"
    DEPENDS
        "${EDEN_AMD_FSR31_BACKEND_DIR}/r09_rdna2_nr/qkv_projection_rdna2.comp"
        "${EDEN_PORT_DIR}/../tools/graphics/test-rdna2-qkv-spv.py"
    COMMENT "Compile and ABI-validate RDNA2 QKV projection"
    VERBATIM)
add_custom_target(eden-r09-rdna2-nr-qkv-spv
    DEPENDS "${EDEN_R09_RDNA2_QKV_HEADER}")
add_dependencies(video_core eden-r09-rdna2-nr-qkv-spv)
set_property(SOURCE "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_qkv_projection.cpp"
    TARGET_DIRECTORY video_core APPEND PROPERTY OBJECT_DEPENDS
    "${EDEN_R09_RDNA2_QKV_HEADER}")

# R09 RDNA2: grouped feed-forward 512->64->256->64 using scalar FP8.
set(EDEN_R09_RDNA2_FFWD3_HEADER
    "${EDEN_FSR31_SHADER_DIR}/rdna2_nr_ffwd3_comp_spv.h")
add_custom_command(
    OUTPUT "${EDEN_R09_RDNA2_FFWD3_HEADER}"
    COMMAND "${Python3_EXECUTABLE}"
        "${EDEN_PORT_DIR}/../tools/graphics/test-rdna2-ffwd3-spv.py"
        --vendor "${EDEN_AMD_FSR31_BACKEND_DIR}/../.."
        --header "${EDEN_R09_RDNA2_FFWD3_HEADER}"
    DEPENDS
        "${EDEN_AMD_FSR31_BACKEND_DIR}/r09_rdna2_nr/ffwd3_group_rdna2.comp"
        "${EDEN_PORT_DIR}/../tools/graphics/test-rdna2-ffwd3-spv.py"
    COMMENT "Compile and ABI-validate RDNA2 grouped FFWD3"
    VERBATIM)
add_custom_target(eden-r09-rdna2-nr-ffwd3-spv
    DEPENDS "${EDEN_R09_RDNA2_FFWD3_HEADER}")
add_dependencies(video_core eden-r09-rdna2-nr-ffwd3-spv)
set_property(SOURCE "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_ffwd3.cpp"
    TARGET_DIRECTORY video_core APPEND PROPERTY OBJECT_DEPENDS
    "${EDEN_R09_RDNA2_FFWD3_HEADER}")

# R09 RDNA2: scalar 32-head ViT attention context.
set(EDEN_R09_RDNA2_VIT_HEADER
    "${EDEN_FSR31_SHADER_DIR}/rdna2_nr_vit_attention_comp_spv.h")
add_custom_command(
    OUTPUT "${EDEN_R09_RDNA2_VIT_HEADER}"
    COMMAND "${Python3_EXECUTABLE}"
        "${EDEN_PORT_DIR}/../tools/graphics/test-rdna2-vit-attention-spv.py"
        --vendor "${EDEN_AMD_FSR31_BACKEND_DIR}/../.."
        --header "${EDEN_R09_RDNA2_VIT_HEADER}"
    DEPENDS
        "${EDEN_AMD_FSR31_BACKEND_DIR}/r09_rdna2_nr/vit_attention_rdna2.comp"
        "${EDEN_PORT_DIR}/../tools/graphics/test-rdna2-vit-attention-spv.py"
    COMMENT "Compile and ABI-validate RDNA2 ViT global attention"
    VERBATIM)
add_custom_target(eden-r09-rdna2-nr-vit-spv
    DEPENDS "${EDEN_R09_RDNA2_VIT_HEADER}")
add_dependencies(video_core eden-r09-rdna2-nr-vit-spv)
set_property(SOURCE "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_vit_attention.cpp"
    TARGET_DIRECTORY video_core APPEND PROPERTY OBJECT_DEPENDS
    "${EDEN_R09_RDNA2_VIT_HEADER}")


# R09 RDNA2: three-dispatch ViT path (FP32 GEMM -> FP8 QKV normalization
# -> global attention). All shader bytes generated and ABI checked on host.
set(EDEN_R09_RDNA2_VIT_QKV_NORM_HEADER
    "${EDEN_FSR31_SHADER_DIR}/rdna2_nr_vit_qkv_norm_comp_spv.h")
add_custom_command(
    OUTPUT "${EDEN_R09_RDNA2_VIT_QKV_NORM_HEADER}"
    COMMAND "${Python3_EXECUTABLE}"
        "${PORT_ROOT}/tools/graphics/test-rdna2-vit-qkv-norm-spv.py"
        --vendor "${EDEN_AMD_FSR31_BACKEND_DIR}/../.."
        --header "${EDEN_R09_RDNA2_VIT_QKV_NORM_HEADER}"
    DEPENDS
        "${EDEN_AMD_FSR31_BACKEND_DIR}/r09_rdna2_nr/vit_qkv_norm_rdna2.comp"
        "${PORT_ROOT}/tools/graphics/test-rdna2-vit-qkv-norm-spv.py"
    COMMENT "Compile and ABI-check RDNA2 ViT 32-head QKV normalization"
    VERBATIM)
add_custom_target(eden-r09-rdna2-nr-vit-qkv-spv
    DEPENDS "${EDEN_R09_RDNA2_VIT_QKV_NORM_HEADER}")
add_dependencies(video_core eden-r09-rdna2-nr-vit-qkv-spv)
set_property(SOURCE
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_vit_qkv_norm.cpp"
    TARGET_DIRECTORY video_core APPEND PROPERTY OBJECT_DEPENDS
    "${EDEN_R09_RDNA2_VIT_QKV_NORM_HEADER}")


# R09: real native FinalHead 4x4 tiles <-> padded ViT raster buffer bridge.
# The shader is compiled to SPIR-V with a strict Vulkan 1.1 ABI check.
set(EDEN_R09_VIT_BOUNDARY_HEADER
    "${EDEN_FSR31_SHADER_DIR}/rdna2_nr_vit_boundary_repack_comp_spv.h")
add_custom_command(
    OUTPUT "${EDEN_R09_VIT_BOUNDARY_HEADER}"
    COMMAND "${Python3_EXECUTABLE}"
        "${PORT_ROOT}/tools/graphics/test-rdna2-vit-boundary-repack-spv.py"
        --vendor "${PORT_ROOT}/vendor"
        --header "${EDEN_R09_VIT_BOUNDARY_HEADER}"
    DEPENDS
        "${EDEN_AMD_FSR31_BACKEND_DIR}/r09_rdna2_nr/vit_boundary_repack_rdna2.comp"
        "${PORT_ROOT}/tools/graphics/test-rdna2-vit-boundary-repack-spv.py"
    COMMENT "Compile and verify RDNA2 FinalHead-ViT tile/raster bridge"
    VERBATIM)
add_custom_target(eden-r09-vit-boundary-spv
    DEPENDS "${EDEN_R09_VIT_BOUNDARY_HEADER}")
add_dependencies(video_core eden-r09-vit-boundary-spv)
set_property(SOURCE
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_vit_boundary_repack.cpp"
    TARGET_DIRECTORY video_core APPEND PROPERTY OBJECT_DEPENDS
    "${EDEN_R09_VIT_BOUNDARY_HEADER}")

# R09: native RDNA2 ViT expansion and residual epilogues, portable Vulkan.
set(EDEN_R09_VIT_EPILOGUE_HEADERS
    "${EDEN_FSR31_SHADER_DIR}/rdna2_nr_vit_activation_comp_spv.h"
    "${EDEN_FSR31_SHADER_DIR}/rdna2_nr_vit_residual_comp_spv.h")
add_custom_command(
    OUTPUT ${EDEN_R09_VIT_EPILOGUE_HEADERS}
    COMMAND "${Python3_EXECUTABLE}"
        "${PORT_ROOT}/tools/graphics/test-rdna2-vit-epilogues-spv.py"
        --vendor "${PORT_ROOT}/vendor"
        --output "${EDEN_FSR31_SHADER_DIR}"
    DEPENDS
        "${EDEN_AMD_FSR31_BACKEND_DIR}/r09_rdna2_nr/vit_activation_rdna2.comp"
        "${EDEN_AMD_FSR31_BACKEND_DIR}/r09_rdna2_nr/vit_residual_rdna2.comp"
        "${PORT_ROOT}/tools/graphics/test-rdna2-vit-epilogues-spv.py"
    COMMENT "Compile and ABI-validate RDNA2 ViT activation and residual"
    VERBATIM)
add_custom_target(eden-r09-vit-epilogues-spv
    DEPENDS ${EDEN_R09_VIT_EPILOGUE_HEADERS})
add_dependencies(video_core eden-r09-vit-epilogues-spv)
set_property(SOURCE
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_vit_epilogue.cpp"
    TARGET_DIRECTORY video_core APPEND PROPERTY OBJECT_DEPENDS
    "${EDEN_FSR31_SHADER_DIR}/rdna2_nr_vit_activation_comp_spv.h"
    "${EDEN_FSR31_SHADER_DIR}/rdna2_nr_vit_residual_comp_spv.h")


# R09: transpose GPU attention context to contiguous token-major FP8.
set(EDEN_R09_SPLIT_CONTEXT_REPACK_SPV
    "${EDEN_FSR31_SHADER_DIR}/rdna2_nr_split_context_repack_comp_spv.h")
add_custom_command(
    OUTPUT "${EDEN_R09_SPLIT_CONTEXT_REPACK_SPV}"
    COMMAND "${Python3_EXECUTABLE}"
        "${PORT_ROOT}/tools/graphics/test-rdna2-split-context-repack-spv.py"
        --vendor "${PORT_ROOT}/vendor"
        --header "${EDEN_R09_SPLIT_CONTEXT_REPACK_SPV}"
    DEPENDS
        "${EDEN_AMD_FSR31_BACKEND_DIR}/r09_rdna2_nr/split_context_repack_rdna2.comp"
        "${PORT_ROOT}/tools/graphics/test-rdna2-split-context-repack-spv.py"
    COMMENT "Compile and ABI-validate RDNA2 Split-Swin context layout transpose"
    VERBATIM)
add_custom_target(eden-r09-split-context-repack-spv
    DEPENDS "${EDEN_R09_SPLIT_CONTEXT_REPACK_SPV}")
add_dependencies(video_core eden-r09-split-context-repack-spv)
set_property(SOURCE
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_split_context_repack.cpp"
    TARGET_DIRECTORY video_core APPEND PROPERTY OBJECT_DEPENDS
    "${EDEN_R09_SPLIT_CONTEXT_REPACK_SPV}")


# R09: Split-Swin ProjPool real half-precision second output, not a
# quantized-average shortcut. All compiler and ABI gates are mandatory.
set(EDEN_R09_SPLIT_POOL_SPV
    "${EDEN_FSR31_SHADER_DIR}/rdna2_nr_split_projection_pool_comp_spv.h")
add_custom_command(
    OUTPUT "${EDEN_R09_SPLIT_POOL_SPV}"
    COMMAND "${Python3_EXECUTABLE}"
        "${PORT_ROOT}/tools/graphics/test-rdna2-split-projection-pool-spv.py"
        --vendor "${PORT_ROOT}/vendor"
        --header "${EDEN_R09_SPLIT_POOL_SPV}"
    DEPENDS
        "${EDEN_AMD_FSR31_BACKEND_DIR}/r09_rdna2_nr/split_projection_pool_rdna2.comp"
        "${PORT_ROOT}/tools/graphics/test-rdna2-split-projection-pool-spv.py"
    COMMENT "Compile and ABI-validate RDNA2 Split-Swin ProjPool"
    VERBATIM)
add_custom_target(eden-r09-split-pool-spv
    DEPENDS "${EDEN_R09_SPLIT_POOL_SPV}")
add_dependencies(video_core eden-r09-split-pool-spv)
set_property(SOURCE
    "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_split_projection_pool.cpp"
    TARGET_DIRECTORY video_core APPEND PROPERTY OBJECT_DEPENDS
    "${EDEN_R09_SPLIT_POOL_SPV}")

# R09 RDNA2 FSwin dense: shader SPIR-V Vulkan 1.1 ABI.
set(EDEN_R09_RDNA2_FSWIN_DENSE_HEADER
    "${EDEN_FSR31_SHADER_DIR}/rdna2_nr_fswin_dense_comp_spv.h")
add_custom_command(
    OUTPUT "${EDEN_R09_RDNA2_FSWIN_DENSE_HEADER}"
    COMMAND "${Python3_EXECUTABLE}"
        "${EDEN_PORT_DIR}/../tools/graphics/test-rdna2-fswin-dense-spv.py"
        --vendor "${EDEN_AMD_FSR31_BACKEND_DIR}/../.."
        --header "${EDEN_R09_RDNA2_FSWIN_DENSE_HEADER}"
    DEPENDS
        "${EDEN_AMD_FSR31_BACKEND_DIR}/r09_rdna2_nr/fswin_dense_rdna2.comp"
        "${EDEN_PORT_DIR}/../tools/graphics/test-rdna2-fswin-dense-spv.py"
    COMMENT "Compile and ABI-validate RDNA2 FSwin dense"
    VERBATIM)
add_custom_target(eden-r09-rdna2-nr-fswin-dense-spv
    DEPENDS "${EDEN_R09_RDNA2_FSWIN_DENSE_HEADER}")
add_dependencies(video_core eden-r09-rdna2-nr-fswin-dense-spv)
set_property(SOURCE "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_fswin_dense.cpp"
    TARGET_DIRECTORY video_core APPEND PROPERTY OBJECT_DEPENDS
    "${EDEN_R09_RDNA2_FSWIN_DENSE_HEADER}")

# R09 RDNA2: FSwin QKV for C=32,64,128,256.
set(EDEN_R09_RDNA2_FSWIN_QKV_HEADER
    "${EDEN_FSR31_SHADER_DIR}/rdna2_nr_fswin_qkv_comp_spv.h")
add_custom_command(
    OUTPUT "${EDEN_R09_RDNA2_FSWIN_QKV_HEADER}"
    COMMAND "${Python3_EXECUTABLE}"
        "${EDEN_PORT_DIR}/../tools/graphics/test-rdna2-fswin-qkv-spv.py"
        --vendor "${EDEN_AMD_FSR31_BACKEND_DIR}/../.."
        --header "${EDEN_R09_RDNA2_FSWIN_QKV_HEADER}"
    DEPENDS
        "${EDEN_AMD_FSR31_BACKEND_DIR}/r09_rdna2_nr/fswin_qkv_rdna2.comp"
        "${EDEN_PORT_DIR}/../tools/graphics/test-rdna2-fswin-qkv-spv.py"
    COMMENT "Compile and ABI-validate RDNA2 FSwin QKV"
    VERBATIM)
add_custom_target(eden-r09-rdna2-nr-fswin-qkv-spv
    DEPENDS "${EDEN_R09_RDNA2_FSWIN_QKV_HEADER}")
add_dependencies(video_core eden-r09-rdna2-nr-fswin-qkv-spv)
set_property(SOURCE "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_fswin_qkv.cpp"
    TARGET_DIRECTORY video_core APPEND PROPERTY OBJECT_DEPENDS
    "${EDEN_R09_RDNA2_FSWIN_QKV_HEADER}")

# R09 RDNA2: retile between shifted 8x8 FSwin windows.
set(EDEN_R09_RDNA2_FSWIN_REPACK_HEADER
    "${EDEN_FSR31_SHADER_DIR}/rdna2_nr_fswin_window_repack_comp_spv.h")
add_custom_command(
    OUTPUT "${EDEN_R09_RDNA2_FSWIN_REPACK_HEADER}"
    COMMAND "${Python3_EXECUTABLE}"
        "${EDEN_PORT_DIR}/../tools/graphics/test-rdna2-fswin-window-repack-spv.py"
        --vendor "${EDEN_AMD_FSR31_BACKEND_DIR}/../.."
        --header "${EDEN_R09_RDNA2_FSWIN_REPACK_HEADER}"
    DEPENDS
        "${EDEN_AMD_FSR31_BACKEND_DIR}/r09_rdna2_nr/fswin_window_repack_rdna2.comp"
        "${EDEN_PORT_DIR}/../tools/graphics/test-rdna2-fswin-window-repack-spv.py"
    COMMENT "Validate RDNA2 shifted FSwin window retile"
    VERBATIM)
add_custom_target(eden-r09-rdna2-nr-fswin-window-spv
    DEPENDS "${EDEN_R09_RDNA2_FSWIN_REPACK_HEADER}")
add_dependencies(video_core eden-r09-rdna2-nr-fswin-window-spv)
set_property(SOURCE "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_fswin_window_repack.cpp"
    TARGET_DIRECTORY video_core APPEND PROPERTY OBJECT_DEPENDS
    "${EDEN_R09_RDNA2_FSWIN_REPACK_HEADER}")

# R09 RDNA2: feature raster to 8x8 FSwin tokens, Vulkan 1.1.
set(EDEN_R09_RDNA2_FSWIN_RASTER_HEADER
    "${EDEN_FSR31_SHADER_DIR}/rdna2_nr_fswin_raster_layout_comp_spv.h")
add_custom_command(
    OUTPUT "${EDEN_R09_RDNA2_FSWIN_RASTER_HEADER}"
    COMMAND "${Python3_EXECUTABLE}"
        "${EDEN_PORT_DIR}/../tools/graphics/test-rdna2-fswin-raster-layout-spv.py"
        --vendor "${EDEN_AMD_FSR31_BACKEND_DIR}/../.."
        --header "${EDEN_R09_RDNA2_FSWIN_RASTER_HEADER}"
    DEPENDS
        "${EDEN_AMD_FSR31_BACKEND_DIR}/r09_rdna2_nr/fswin_raster_layout_rdna2.comp"
        "${EDEN_PORT_DIR}/../tools/graphics/test-rdna2-fswin-raster-layout-spv.py"
    COMMENT "Validate RDNA2 feature-raster FSwin SPIR-V ABI"
    VERBATIM)
add_custom_target(eden-r09-rdna2-nr-fswin-raster-spv
    DEPENDS "${EDEN_R09_RDNA2_FSWIN_RASTER_HEADER}")
add_dependencies(video_core eden-r09-rdna2-nr-fswin-raster-spv)
set_property(SOURCE "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_fswin_raster_layout.cpp"
    TARGET_DIRECTORY video_core APPEND PROPERTY OBJECT_DEPENDS
    "${EDEN_R09_RDNA2_FSWIN_RASTER_HEADER}")

# R09 RDNA2: learned FSwin DS 2x2 pooling/projection, host SPIR-V.
set(EDEN_R09_RDNA2_FSWIN_DOWNSAMPLE_HEADER
    "${EDEN_FSR31_SHADER_DIR}/rdna2_nr_fswin_downsample_comp_spv.h")
add_custom_command(
    OUTPUT "${EDEN_R09_RDNA2_FSWIN_DOWNSAMPLE_HEADER}"
    COMMAND "${Python3_EXECUTABLE}"
        "${EDEN_PORT_DIR}/../tools/graphics/test-rdna2-fswin-downsample-spv.py"
        --vendor "${EDEN_AMD_FSR31_BACKEND_DIR}/../.."
        --header "${EDEN_R09_RDNA2_FSWIN_DOWNSAMPLE_HEADER}"
    DEPENDS
        "${EDEN_AMD_FSR31_BACKEND_DIR}/r09_rdna2_nr/fswin_downsample_rdna2.comp"
        "${EDEN_PORT_DIR}/../tools/graphics/test-rdna2-fswin-downsample-spv.py"
    COMMENT "Compile and ABI-validate RDNA2 FSwin learned downsample"
    VERBATIM)
add_custom_target(eden-r09-rdna2-nr-fswin-downsample-spv
    DEPENDS "${EDEN_R09_RDNA2_FSWIN_DOWNSAMPLE_HEADER}")
add_dependencies(video_core eden-r09-rdna2-nr-fswin-downsample-spv)
set_property(SOURCE "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_fswin_downsample.cpp"
    TARGET_DIRECTORY video_core APPEND PROPERTY OBJECT_DEPENDS
    "${EDEN_R09_RDNA2_FSWIN_DOWNSAMPLE_HEADER}")

# R09 RDNA2: FSwin upsample projection/skip blend Vulkan SPIR-V.
set(EDEN_R09_RDNA2_FSWIN_UPSAMPLE_HEADER
    "${EDEN_FSR31_SHADER_DIR}/rdna2_nr_fswin_upsample_comp_spv.h")
add_custom_command(
    OUTPUT "${EDEN_R09_RDNA2_FSWIN_UPSAMPLE_HEADER}"
    COMMAND "${Python3_EXECUTABLE}"
        "${EDEN_PORT_DIR}/../tools/graphics/test-rdna2-fswin-upsample-spv.py"
        --vendor "${EDEN_AMD_FSR31_BACKEND_DIR}/../.."
        --header "${EDEN_R09_RDNA2_FSWIN_UPSAMPLE_HEADER}"
    DEPENDS
        "${EDEN_AMD_FSR31_BACKEND_DIR}/r09_rdna2_nr/fswin_upsample_rdna2.comp"
        "${EDEN_PORT_DIR}/../tools/graphics/test-rdna2-fswin-upsample-spv.py"
    COMMENT "Compile and ABI-validate RDNA2 FSwin learned upsample"
    VERBATIM)
add_custom_target(eden-r09-rdna2-nr-fswin-upsample-spv
    DEPENDS "${EDEN_R09_RDNA2_FSWIN_UPSAMPLE_HEADER}")
add_dependencies(video_core eden-r09-rdna2-nr-fswin-upsample-spv)
set_property(SOURCE "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_fswin_upsample.cpp"
    TARGET_DIRECTORY video_core APPEND PROPERTY OBJECT_DEPENDS
    "${EDEN_R09_RDNA2_FSWIN_UPSAMPLE_HEADER}")

# R09: FP32 projection -> E4M3FN GPU quantization, Vulkan 1.1 / RDNA2.
set(EDEN_R09_RDNA2_FLOAT_QUANTIZE_HEADER
    "${EDEN_FSR31_SHADER_DIR}/rdna2_nr_float_quantize_comp_spv.h")
add_custom_command(
    OUTPUT "${EDEN_R09_RDNA2_FLOAT_QUANTIZE_HEADER}"
    COMMAND "${Python3_EXECUTABLE}"
        "${EDEN_PORT_DIR}/../tools/graphics/test-rdna2-float-quantize-spv.py"
        --vendor "${EDEN_AMD_FSR31_BACKEND_DIR}/../.."
        --header "${EDEN_R09_RDNA2_FLOAT_QUANTIZE_HEADER}"
    DEPENDS
        "${EDEN_AMD_FSR31_BACKEND_DIR}/r09_rdna2_nr/float_quantize_rdna2.comp"
        "${EDEN_PORT_DIR}/../tools/graphics/test-rdna2-float-quantize-spv.py"
    COMMENT "Compile FP32-to-E4M3FN neural bridge (RDNA2 Vulkan)"
    VERBATIM)
add_custom_target(eden-r09-rdna2-nr-float-quantize-spv
    DEPENDS "${EDEN_R09_RDNA2_FLOAT_QUANTIZE_HEADER}")
add_dependencies(video_core eden-r09-rdna2-nr-float-quantize-spv)
set_property(SOURCE "${EDEN_AMD_FSR31_BACKEND_DIR}/nr_rdna2_float_quantize.cpp"
    TARGET_DIRECTORY video_core APPEND PROPERTY OBJECT_DEPENDS
    "${EDEN_R09_RDNA2_FLOAT_QUANTIZE_HEADER}")

# R24: compile a distinct FXAA Quality shader on the HOST for SPIR-V 1.3.
# The PS5 image contains only the compiled shader, no runtime compiler.
find_program(EDEN_R24_GLSLANG NAMES glslangValidator REQUIRED)
set(EDEN_R24_FXAA_HEADER
    "${PORT_BUILD_DIR}/include/video_core/host_shaders/fxaa_quality_frag_spv.h")
add_custom_command(
    OUTPUT "${EDEN_R24_FXAA_HEADER}"
    COMMAND "${CMAKE_COMMAND}" -E make_directory
            "${PORT_BUILD_DIR}/include/video_core/host_shaders"
    COMMAND "${EDEN_R24_GLSLANG}" -V --target-env spirv1.3
            -DUseUniformBlock=1 --variable-name FXAA_QUALITY_FRAG_SPV
            -o "${EDEN_R24_FXAA_HEADER}" "${EDEN_PORT_DIR}/fxaa_quality.frag"
    DEPENDS "${EDEN_PORT_DIR}/fxaa_quality.frag"
    VERBATIM)
add_custom_target(eden-r24-fxaa-quality-spv DEPENDS "${EDEN_R24_FXAA_HEADER}")
add_dependencies(video_core eden-r24-fxaa-quality-spv)

configure_file("${EDEN_PORT_DIR}/vk_blit_screen_r08.h"
    "${PORT_BUILD_DIR}/include/video_core/renderer_vulkan/vk_blit_screen.h" COPYONLY)
# The native build driver explicitly re-runs CMake before every build,
# refreshing file(COPY) even when the pinned fork's file content has changed.
# GLOB CONFIGURE_DEPENDS also tracks additions/removals for direct Ninja use.
# Do NOT register this full list again as CMAKE_CONFIGURE_DEPENDS: some of
# these headers are already tracked by configure_file() above, and the
# duplicate "missing CMake input" phony outputs make build.ninja unparseable.
file(GLOB_RECURSE EDEN_VULKAN_FORK_FILES CONFIGURE_DEPENDS "${EDEN_ACTIVE_VULKAN}/*")
# These shaders are build inputs; the five older .inc injections only
# reconstruct the historical generator oracle and are NOT compiled here.
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS
    "${EDEN_PORT_DIR}/vulkan_hud.vert" "${EDEN_PORT_DIR}/vulkan_hud.frag")
# R23 #2: fixed state source AND its POD header must match. The native
# fork is copied above; the generated build TU is compiled only once.
if(NOT EXISTS "${EDEN_ACTIVE_VULKAN}/fixed_pipeline_state.cpp")
    message(FATAL_ERROR "R23 #2 native EDS3 state source missing")
endif()
list(REMOVE_ITEM video_sources renderer_vulkan/fixed_pipeline_state.cpp)
list(APPEND video_sources "${PORT_BUILD_DIR}/fixed_pipeline_state.cpp")
list(REMOVE_ITEM video_sources vulkan_common/vulkan_device.cpp
    vulkan_common/vulkan_memory_allocator.cpp renderer_vulkan/vk_scheduler.cpp)
# Spatial FSR1 stock percentage was reversed relative to RCAS stops:
# 0=strongest, higher stops=weaker. Replace native source only, not vendor.
list(REMOVE_ITEM video_sources renderer_vulkan/present/fsr.cpp)
list(APPEND video_sources "${EDEN_PORT_DIR}/vulkan_fsr1_r07.cpp")
# FXAA+ (quality) has separate Vulkan SPIR-V. No fake MSAA or 2x FXAA run.
# SGSR has two distinct PS5 Vulkan shaders already shipped by upstream.
# Give their edge-sharpness slider the same visible 0..100% semantics.
list(REMOVE_ITEM video_sources renderer_vulkan/present/sgsr.cpp)
list(APPEND video_sources "${EDEN_PORT_DIR}/vulkan_sgsr_r07.cpp")
list(REMOVE_ITEM video_sources renderer_vulkan/present/fxaa.cpp)
list(APPEND video_sources
    "${EDEN_PORT_DIR}/vulkan_fxaa_r24.cpp"
    "${EDEN_PORT_DIR}/fxaa_quality_select.cpp")
set_property(SOURCE "${EDEN_PORT_DIR}/vulkan_fxaa_r24.cpp"
    TARGET_DIRECTORY video_core APPEND PROPERTY OBJECT_DEPENDS
    "${EDEN_R24_FXAA_HEADER}")
list(APPEND video_sources "${PORT_BUILD_DIR}/vulkan_device.cpp"
    "${PORT_BUILD_DIR}/vulkan_memory_allocator.cpp" "${PORT_BUILD_DIR}/vulkan_scheduler.cpp")
list(REMOVE_ITEM video_sources vulkan_common/vulkan_instance.cpp vulkan_common/vulkan_wrapper.cpp
    vulkan_common/vulkan_library.cpp vulkan_common/vulkan_surface.cpp
    renderer_vulkan/vk_rasterizer.cpp renderer_vulkan/vk_blit_screen.cpp
    renderer_vulkan/present/window_adapt_pass.cpp renderer_vulkan/present/layer.cpp
    renderer_vulkan/renderer_vulkan.cpp
    renderer_vulkan/vk_present_manager.cpp renderer_vulkan/vk_swapchain.cpp
    renderer_vulkan/vk_query_cache.cpp)
list(APPEND video_sources "${PORT_BUILD_DIR}/vulkan_instance.cpp" "${PORT_BUILD_DIR}/vulkan_wrapper.cpp"
    "${PORT_BUILD_DIR}/vulkan_rasterizer.cpp" "${EDEN_PORT_DIR}/vulkan_blit_screen_r08.cpp"
    "${EDEN_PORT_DIR}/vulkan_window_adapt_r08.cpp" "${EDEN_PORT_DIR}/vulkan_present_layer_r24.cpp"
    "${EDEN_PORT_DIR}/vulkan_renderer_r08.cpp"
    "${PORT_BUILD_DIR}/vulkan_library.cpp" "${EDEN_PORT_DIR}/vulkan_surface.cpp" "${EDEN_PORT_DIR}/vulkan_allocator.cpp"
    "${PORT_BUILD_DIR}/vulkan_present_manager.cpp" "${PORT_BUILD_DIR}/vulkan_swapchain.cpp"
    "${PORT_BUILD_DIR}/vulkan_query_cache.cpp")
foreach(name vk_fence_manager vk_buffer_cache vk_texture_cache vk_descriptor_buffer vk_multi_range_buffer vk_compute_pass vk_graphics_pipeline vk_compute_pipeline vk_pipeline_cache)
    list(REMOVE_ITEM video_sources renderer_vulkan/${name}.cpp)
    list(APPEND video_sources "${PORT_BUILD_DIR}/${name}_cost.cpp")
endforeach()

# The cache's PS5-only failed-key recovery metadata changes its class layout.
# Explicitly rebuild consumers when an earlier depfile still names the
# untouched pinned upstream header instead of our checked-in override.
set_property(SOURCE
    "${PORT_BUILD_DIR}/vk_pipeline_cache_cost.cpp"
    "${PORT_BUILD_DIR}/vulkan_rasterizer.cpp"
    "${PORT_BUILD_DIR}/vulkan_renderer.cpp"
    TARGET_DIRECTORY video_core APPEND PROPERTY OBJECT_DEPENDS
    "${PORT_BUILD_DIR}/include/video_core/renderer_vulkan/vk_pipeline_cache.h")
target_include_directories(video_core BEFORE PUBLIC "${PORT_BUILD_DIR}/include")
target_include_directories(video_core BEFORE PUBLIC "${PORT_BUILD_DIR}/vulkan-cache")
target_include_directories(video_core PRIVATE
    "${PORT_BUILD_DIR}" "${EDEN_PORT_DIR}" "${PORT_ROOT}/extras/graphics"
    "${PORT_ROOT}/vendor/sources/ps5-mihawkgen/framegen/include"
    "${PORT_ROOT}/vendor/sources/ps5-mihawkgen/external")
# The descriptor-buffer writer override (null descriptors): rebuild its callers once,
# since existing depfiles still name the upstream header.
set_property(SOURCE
    "${PORT_BUILD_DIR}/vk_graphics_pipeline_cost.cpp" "${PORT_BUILD_DIR}/vk_compute_pipeline_cost.cpp"
    "${PORT_BUILD_DIR}/vk_pipeline_cache_cost.cpp" "${PORT_BUILD_DIR}/vulkan_rasterizer.cpp"
    TARGET_DIRECTORY video_core APPEND PROPERTY OBJECT_DEPENDS
    "${PORT_BUILD_DIR}/include/video_core/renderer_vulkan/pipeline_helper.h")
# PresentManager is embedded by value in RendererVulkan. Rebuild consumers whose
# old depfiles still name the upstream header when adding the failure field.
set_property(SOURCE
    "${PROJECT_SOURCE_DIR}/src/video_core/video_core.cpp"
    "${PROJECT_SOURCE_DIR}/src/video_core/renderer_vulkan/vk_turbo_mode.cpp"
    "${PROJECT_SOURCE_DIR}/src/video_core/renderer_vulkan/present/frame_gen.cpp"
    "${EDEN_PORT_DIR}/vulkan_renderer_r08.cpp" "${EDEN_PORT_DIR}/vulkan_blit_screen_r08.cpp"
    "${PORT_BUILD_DIR}/vulkan_rasterizer.cpp" "${EDEN_PORT_DIR}/vulkan_window_adapt_r08.cpp"
    TARGET_DIRECTORY video_core APPEND PROPERTY OBJECT_DEPENDS
    "${PORT_BUILD_DIR}/include/video_core/renderer_vulkan/vk_present_manager.h")
# Existing depfiles name the original header; rebuild all filter consumers once
# when introducing the override so the shared struct layout stays consistent.
set_property(SOURCE
    "${PROJECT_SOURCE_DIR}/src/video_core/renderer_opengl/present/layer.cpp"
    "${PROJECT_SOURCE_DIR}/src/video_core/renderer_opengl/renderer_opengl.cpp"
    "${PROJECT_SOURCE_DIR}/src/video_core/renderer_opengl/gl_blit_screen.cpp"
    "${EDEN_PORT_DIR}/vulkan_present_layer_r24.cpp"
    TARGET_DIRECTORY video_core APPEND PROPERTY OBJECT_DEPENDS
    "${PORT_BUILD_DIR}/include/video_core/present.h")
# Layer grows an AA extent field; rebuild all clients against the single
# maintained header (including cached objects from previous PS5 builds).
set_property(SOURCE
    "${EDEN_PORT_DIR}/vulkan_present_layer_r24.cpp"
    "${EDEN_PORT_DIR}/vulkan_blit_screen_r08.cpp"
    "${EDEN_PORT_DIR}/vulkan_renderer_r08.cpp"
    TARGET_DIRECTORY video_core APPEND PROPERTY OBJECT_DEPENDS
    "${PORT_BUILD_DIR}/include/video_core/renderer_vulkan/present/layer.h")
# BlitScreen stores WindowAdaptPass by value through unique_ptr; all consumers
# must see the extended resource layout, including cached objects predating it.
set_property(SOURCE
    "${PROJECT_SOURCE_DIR}/src/video_core/renderer_vulkan/present/filters.cpp"
    TARGET_DIRECTORY video_core APPEND PROPERTY OBJECT_DEPENDS
    "${PORT_BUILD_DIR}/include/video_core/renderer_vulkan/present/window_adapt_pass.h")
# A newly generated override is not in old depfiles until the sources rebuild.
# Track it explicitly for the API wrappers and allocator/device setup callers.
set_property(SOURCE
    "${PROJECT_SOURCE_DIR}/src/video_core/vulkan_common/vulkan_wrapper.cpp"
    "${PROJECT_SOURCE_DIR}/src/video_core/vulkan_common/vulkan_device.cpp"
    TARGET_DIRECTORY video_core APPEND PROPERTY OBJECT_DEPENDS
    "${PORT_BUILD_DIR}/include/video_core/vulkan_common/vulkan_wrapper.h")
target_compile_definitions(video_core PRIVATE PS5_NATIVE=1)
# Keep incompatible Mesa/PSBC globals private to the Vulkan archives.
if(EDEN_VULKAN_DRIVER STREQUAL "RADV")
    set(radv_archive "${PORT_ROOT}/build/radv-isolated/libvulkan_radeon.ps5.a")
    if(NOT EXISTS "${radv_archive}")
        message(FATAL_ERROR "Build and isolate the pinned RADV release archive first")
    endif()
    target_link_libraries(video_core PRIVATE "${radv_archive}"
        "${PORT_ROOT}/build/stubs/libSceAgcDriver.so"
        "${sdk}/target/lib/libSceSysmodule.so")
else()
set(vk_isolated "${PORT_ROOT}/build/vulkan-isolated")
foreach(archive libps5vk.a libpsbc.a)
    if(NOT EXISTS "${vk_isolated}/${archive}")
        message(FATAL_ERROR "Stage isolated Vulkan compiler archives before building")
    endif()
endforeach()
target_link_libraries(video_core PRIVATE "${vk_isolated}/libps5vk.a" "${vk_isolated}/libpsbc.a"
    "${PORT_ROOT}/build/stubs/libSceAgcDriver.so"
    "${sdk}/target/lib/libSceSysmodule.so")
endif()

# Native MihawkGen always compiles into the production Vulkan renderer.
# The selected method and measured device capabilities decide runtime use;
# no dev/release/roadmap profile controls this integration.
set(EDEN_MIHAWKGEN_ROOT "${PORT_ROOT}/vendor/sources/ps5-mihawkgen")
set(EDEN_MIHAWKGEN_INC "${EDEN_MIHAWKGEN_ROOT}/framegen/include")
set(EDEN_MIHAWKGEN_SRC "${EDEN_MIHAWKGEN_ROOT}/framegen/src")
set(EDEN_MIHAWKGEN_VOLK "${EDEN_MIHAWKGEN_ROOT}/ps5/third_party/volk/volk.c")
set(EDEN_MIHAWKGEN_NAMESPACED_HEADER "${EDEN_PORT_DIR}/mihawk_volk.h")
foreach(path "${EDEN_MIHAWKGEN_INC}/framegen.h"
             "${EDEN_MIHAWKGEN_VOLK}"
             "${EDEN_MIHAWKGEN_NAMESPACED_HEADER}"
             "${EDEN_MIHAWKGEN_SRC}/shaders/nn_conv.comp.h")
    if(NOT EXISTS "${path}")
        message(FATAL_ERROR "Missing pinned native MihawkGen source: ${path}")
    endif()
endforeach()
set(EDEN_MIHAWKGEN_SOURCES
    "${EDEN_MIHAWKGEN_SRC}/fg_common.cpp"
    "${EDEN_MIHAWKGEN_SRC}/fg_vulkan.cpp"
    "${EDEN_MIHAWKGEN_SRC}/fg_neural.cpp"
    "${EDEN_MIHAWKGEN_SRC}/fg_splat.cpp"
    "${EDEN_MIHAWKGEN_VOLK}"
    "${EDEN_PORT_DIR}/mihawk_vulkan_stage.cpp"
    "${EDEN_PORT_DIR}/mihawk_vulkan_resources.cpp"
    "${EDEN_PORT_DIR}/mihawk_vulkan_encoder.cpp"
    "${EDEN_PORT_DIR}/mihawk_native_session.cpp")
# Keep volk's function-pointer symbols inside namespace volk. In particular
# vkGetInstanceProcAddr must not collide with the RADV function exported by
# Encore's existing Vulkan driver.
set_source_files_properties("${EDEN_MIHAWKGEN_VOLK}" PROPERTIES LANGUAGE CXX)
add_library(eden-mihawkgen-native OBJECT ${EDEN_MIHAWKGEN_SOURCES})
target_compile_features(eden-mihawkgen-native PRIVATE cxx_std_20)
target_compile_definitions(eden-mihawkgen-native PRIVATE
    VK_NO_PROTOTYPES=1 VOLK_NAMESPACE=1 PS5_NATIVE=1)
target_compile_options(eden-mihawkgen-native PRIVATE
    "SHELL:-include ${EDEN_MIHAWKGEN_NAMESPACED_HEADER}")
target_include_directories(eden-mihawkgen-native PRIVATE
    "${EDEN_MIHAWKGEN_INC}" "${EDEN_MIHAWKGEN_SRC}"
    "${EDEN_MIHAWKGEN_ROOT}/external" "${EDEN_MIHAWKGEN_ROOT}/ps5/third_party/volk"
    "${PORT_ROOT}/extras/graphics" "${EDEN_PORT_DIR}")
# This module is included before headless/CMakeLists.txt commits video_sources
# with set_property(TARGET video_core PROPERTY SOURCES ...). Append to that
# canonical list, otherwise the later assignment silently discards the link.
list(APPEND video_sources "$<TARGET_OBJECTS:eden-mihawkgen-native>")

# R08 AMD candidate: FSR3 optical-flow shaders and a PS5-native Vulkan
# interpolator, from Swordpdf/ps5-framegen. Not an official FSR3 backend.
set(EDEN_FSR3_OF_ROOT "${PORT_ROOT}/vendor/sources/ps5-fsr3-optical-flow")
if(NOT EXISTS "${EDEN_FSR3_OF_ROOT}/src/framegen/fg_shaders.inc")
    message(FATAL_ERROR "Missing pinned PS5 FSR3 optical-flow source")
endif()
list(APPEND video_sources
    "${EDEN_FSR3_OF_ROOT}/src/ps5_framegen.cpp"
    "${EDEN_PORT_DIR}/fsr3_optical_session.cpp")
# The native FrameGen TU is owned by the src/video_core directory, NOT
# this deferred root CMake directory. TARGET_DIRECTORY is essential: without
# it, the source-only PS5_FRAMEGEN_VULKAN_HEADER property does not reach Clang.
# Avoid unmangled vkCreate*/vkDestroy* external references: all FSR3 calls
# must use the same isolated volk:: dispatch pointers as MihawkGen.
set_source_files_properties("${EDEN_FSR3_OF_ROOT}/src/ps5_framegen.cpp"
    TARGET_DIRECTORY video_core
    PROPERTIES
        COMPILE_DEFINITIONS "PS5_FRAMEGEN_VULKAN_HEADER=\"mihawk_volk.h\";VK_NO_PROTOTYPES=1;VOLK_NAMESPACE=1"
        COMPILE_OPTIONS "-include;${EDEN_MIHAWKGEN_NAMESPACED_HEADER}")
target_include_directories(video_core PRIVATE "${EDEN_FSR3_OF_ROOT}/src")


# R08 / LSFG: reuse the GPL-3 Vulkan shader extraction/interpolation
# engine on PS5, rather than duplicate it. Android is its default upstream.
# The private Lossless.dll is supplied by the user, NEVER packaged.
set(EDEN_LSFG_SOURCES_ROOT "${PROJECT_SOURCE_DIR}/src/video_core")
set(EDEN_LSFG_NATIVE_SOURCES
    "${EDEN_PORT_DIR}/lossless_dll_r08.cpp"
    "${EDEN_LSFG_SOURCES_ROOT}/frame_gen/lsfg_translate.cpp"
    "${EDEN_LSFG_SOURCES_ROOT}/renderer_vulkan/present/frame_gen.cpp"
    "${EDEN_LSFG_SOURCES_ROOT}/renderer_vulkan/present/frame_gen_pacer.cpp"
    "${EDEN_LSFG_SOURCES_ROOT}/renderer_vulkan/present/lsfg_alpha.cpp"
    "${EDEN_LSFG_SOURCES_ROOT}/renderer_vulkan/present/lsfg_beta.cpp"
    "${EDEN_LSFG_SOURCES_ROOT}/renderer_vulkan/present/lsfg_chain.cpp"
    "${EDEN_LSFG_SOURCES_ROOT}/renderer_vulkan/present/lsfg_common.cpp"
    "${EDEN_LSFG_SOURCES_ROOT}/renderer_vulkan/present/lsfg_delta.cpp"
    "${EDEN_LSFG_SOURCES_ROOT}/renderer_vulkan/present/lsfg_gamma.cpp"
    "${EDEN_LSFG_SOURCES_ROOT}/renderer_vulkan/present/lsfg_generate.cpp"
    "${EDEN_LSFG_SOURCES_ROOT}/renderer_vulkan/present/lsfg_mipmaps.cpp"
    "${EDEN_LSFG_SOURCES_ROOT}/renderer_vulkan/present/lsfg_shaders.cpp")
foreach(path IN LISTS EDEN_LSFG_NATIVE_SOURCES)
    if(NOT EXISTS "${path}")
        message(FATAL_ERROR "Missing maintained LSFG native input: ${path}")
    endif()
endforeach()
list(APPEND video_sources ${EDEN_LSFG_NATIVE_SOURCES})
target_compile_definitions(video_core PUBLIC HAS_LSFG)
