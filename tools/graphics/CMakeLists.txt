cmake_minimum_required(VERSION 3.20)
project(eden_r08_mihawk_host_checks LANGUAGES C CXX)
# Host-only: compile exactly the source files used by the Encore PS5
# qualification target. No renderer or SDK, and no PS5 packaging.
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
enable_testing()
find_package(Python3 COMPONENTS Interpreter REQUIRED)
add_test(NAME test_fsr31_spirv_abi_parser
    COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/test-fsr31-spirv-abi.py")
# If the pinned vendor submodule is populated (normal CI checkout),
# check actual model hashes, three independent CNN graphs and labels.
# RDNA2 1x1 neural projection is one Vulkan compute primitive, not DLSS:
# validate that no FP8 WMMA/cooperative matrix instruction leaked into SPIR-V.
if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/../../vendor/encore-active/eden-vulkan/r09_rdna2_nr/fswin_raster_layout_rdna2.comp")
    add_test(NAME test_rdna2_nr_fswin_raster_spirv_abi
        COMMAND "${Python3_EXECUTABLE}"
            "${CMAKE_CURRENT_SOURCE_DIR}/test-rdna2-fswin-raster-layout-spv.py"
            --vendor "${CMAKE_CURRENT_SOURCE_DIR}/../../vendor")
endif()
if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/../../vendor/encore-active/eden-vulkan/r09_rdna2_nr/fswin_window_repack_rdna2.comp")
    add_test(NAME test_rdna2_nr_fswin_window_repack_spirv_abi
        COMMAND "${Python3_EXECUTABLE}"
            "${CMAKE_CURRENT_SOURCE_DIR}/test-rdna2-fswin-window-repack-spv.py"
            --vendor "${CMAKE_CURRENT_SOURCE_DIR}/../../vendor")
endif()
if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/../../vendor/encore-active/eden-vulkan/r09_rdna2_nr/fswin_qkv_rdna2.comp")
    add_test(NAME test_rdna2_nr_fswin_qkv_spirv_abi
        COMMAND "${Python3_EXECUTABLE}"
            "${CMAKE_CURRENT_SOURCE_DIR}/test-rdna2-fswin-qkv-spv.py"
            --vendor "${CMAKE_CURRENT_SOURCE_DIR}/../../vendor")
endif()
if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/../../vendor/encore-active/eden-vulkan/r09_rdna2_nr/fswin_upsample_rdna2.comp")
    add_test(NAME test_rdna2_nr_fswin_upsample_spirv_abi
        COMMAND "${Python3_EXECUTABLE}"
            "${CMAKE_CURRENT_SOURCE_DIR}/test-rdna2-fswin-upsample-spv.py"
            --vendor "${CMAKE_CURRENT_SOURCE_DIR}/../../vendor")
endif()
if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/../../vendor/encore-active/eden-vulkan/r09_rdna2_nr/float_quantize_rdna2.comp")
    add_test(NAME test_rdna2_nr_float_quantize_spirv_abi
        COMMAND "${Python3_EXECUTABLE}"
            "${CMAKE_CURRENT_SOURCE_DIR}/test-rdna2-float-quantize-spv.py"
            --vendor "${CMAKE_CURRENT_SOURCE_DIR}/../../vendor")
endif()
if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/../../vendor/encore-active/eden-vulkan/r09_rdna2_nr/fswin_downsample_rdna2.comp")
    add_test(NAME test_rdna2_nr_fswin_downsample_spirv_abi
        COMMAND "${Python3_EXECUTABLE}"
            "${CMAKE_CURRENT_SOURCE_DIR}/test-rdna2-fswin-downsample-spv.py"
            --vendor "${CMAKE_CURRENT_SOURCE_DIR}/../../vendor")
endif()
if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/../../vendor/encore-active/eden-vulkan/r09_rdna2_nr/fswin_dense_rdna2.comp")
    add_test(NAME test_rdna2_nr_fswin_dense_spirv_abi
        COMMAND "${Python3_EXECUTABLE}"
            "${CMAKE_CURRENT_SOURCE_DIR}/test-rdna2-fswin-dense-spv.py"
            --vendor "${CMAKE_CURRENT_SOURCE_DIR}/../../vendor")
endif()
if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/../../vendor/encore-active/eden-vulkan/r09_rdna2_nr/vit_attention_rdna2.comp")
    add_test(NAME test_rdna2_nr_vit_spirv_abi
        COMMAND "${Python3_EXECUTABLE}"
            "${CMAKE_CURRENT_SOURCE_DIR}/test-rdna2-vit-attention-spv.py"
            --vendor "${CMAKE_CURRENT_SOURCE_DIR}/../../vendor")
endif()
if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/../../vendor/encore-active/eden-vulkan/r09_rdna2_nr/ffwd3_group_rdna2.comp")
    add_test(NAME test_rdna2_nr_ffwd3_spirv_abi
        COMMAND "${Python3_EXECUTABLE}"
            "${CMAKE_CURRENT_SOURCE_DIR}/test-rdna2-ffwd3-spv.py"
            --vendor "${CMAKE_CURRENT_SOURCE_DIR}/../../vendor")
endif()
if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/../../vendor/encore-active/eden-vulkan/r09_rdna2_nr/qkv_projection_rdna2.comp")
    add_test(NAME test_rdna2_nr_qkv_spirv_abi
        COMMAND "${Python3_EXECUTABLE}"
            "${CMAKE_CURRENT_SOURCE_DIR}/test-rdna2-qkv-spv.py"
            --vendor "${CMAKE_CURRENT_SOURCE_DIR}/../../vendor")
endif()
if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/../../vendor/encore-active/eden-vulkan/r09_rdna2_nr/window_attention_rdna2.comp")
    add_test(NAME test_rdna2_nr_attention_spirv_abi
        COMMAND "${Python3_EXECUTABLE}"
            "${CMAKE_CURRENT_SOURCE_DIR}/test-rdna2-attention-spv.py"
            --vendor "${CMAKE_CURRENT_SOURCE_DIR}/../../vendor")
endif()
if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/../../vendor/encore-active/eden-vulkan/r09_rdna2_nr/decoder_upsample_rdna2.comp")
    add_test(NAME test_rdna2_nr_decoder_spirv_abi
        COMMAND "${Python3_EXECUTABLE}"
            "${CMAKE_CURRENT_SOURCE_DIR}/test-rdna2-decoder-spv.py"
            --vendor "${CMAKE_CURRENT_SOURCE_DIR}/../../vendor")
endif()
if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/../../vendor/encore-active/eden-vulkan/r09_rdna2_nr/noise_field_rdna2.comp")
    add_test(NAME test_rdna2_nr_noise_spirv_abi
        COMMAND "${Python3_EXECUTABLE}"
            "${CMAKE_CURRENT_SOURCE_DIR}/test-rdna2-noise-spv.py"
            --vendor "${CMAKE_CURRENT_SOURCE_DIR}/../../vendor")
endif()
if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/../../vendor/encore-active/eden-vulkan/r09_rdna2_nr/upsample_view_rdna2.comp")
    add_test(NAME test_rdna2_nr_upview_spirv_abi
        COMMAND "${Python3_EXECUTABLE}"
            "${CMAKE_CURRENT_SOURCE_DIR}/test-rdna2-upview-spv.py"
            --vendor "${CMAKE_CURRENT_SOURCE_DIR}/../../vendor")
endif()
if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/../../vendor/encore-active/eden-vulkan/r09_rdna2_nr/repack_tokens_rdna2.comp")
    add_test(NAME test_rdna2_nr_repack_spirv_abi
        COMMAND "${Python3_EXECUTABLE}"
            "${CMAKE_CURRENT_SOURCE_DIR}/test-rdna2-repack-spv.py"
            --vendor "${CMAKE_CURRENT_SOURCE_DIR}/../../vendor")
endif()
if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/../../vendor/encore-active/eden-vulkan/r09_rdna2_nr/fp8_proj_rdna2.comp")
    add_test(NAME test_rdna2_nr_spirv_baseline
        COMMAND "${Python3_EXECUTABLE}"
            "${CMAKE_CURRENT_SOURCE_DIR}/test-rdna2-nr-spv.py"
            --vendor "${CMAKE_CURRENT_SOURCE_DIR}/../../vendor")
endif()
if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/../../vendor/encore-active/eden-vulkan/anime4k_3d.cpp")
    add_test(NAME test_a4k_three_neural_profiles
        COMMAND "${Python3_EXECUTABLE}"
            "${CMAKE_CURRENT_SOURCE_DIR}/test-a4k-profiles.py"
            --root "${CMAKE_CURRENT_SOURCE_DIR}/../.."
            --vendor "${CMAKE_CURRENT_SOURCE_DIR}/../../vendor")
endif()
get_filename_component(EDEN_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/../.." ABSOLUTE)
set(FG_ROOT "${EDEN_ROOT}/vendor/sources/ps5-mihawkgen")
set(FSR3_OF_ROOT "${EDEN_ROOT}/vendor/sources/ps5-fsr3-optical-flow")
if(NOT EXISTS "${FSR3_OF_ROOT}/src/framegen/fg_shaders.inc")
    message(FATAL_ERROR "Missing pinned FSR3 Optical Flow sources in vendor")
endif()
set(FG_CORE "${FG_ROOT}/framegen/src")
set(FG_INCLUDE "${FG_ROOT}/framegen/include")
set(FG_EXT "${FG_ROOT}/external")
set(EDEN_H "${EDEN_ROOT}/headless")
set(FG_QUAL "${EDEN_ROOT}/extras/graphics")
set(VOLK_HEADER "${FG_ROOT}/ps5/third_party/volk/volk.h")
foreach(REQUIRED "${FG_INCLUDE}/framegen.h" "${VOLK_HEADER}")
    if(NOT EXISTS "${REQUIRED}")
        message(FATAL_ERROR "Missing pinned MihawkGen sources in vendor: ${REQUIRED}")
    endif()
endforeach()
add_library(eden-r08-native-objects OBJECT
    "${FG_CORE}/fg_common.cpp"
    "${FG_CORE}/fg_vulkan.cpp"
    "${FG_CORE}/fg_neural.cpp"
    "${FG_CORE}/fg_splat.cpp"
    "${EDEN_H}/mihawk_vulkan_stage.cpp"
    "${EDEN_H}/mihawk_vulkan_resources.cpp"
    "${EDEN_H}/mihawk_vulkan_encoder.cpp"
    "${EDEN_H}/mihawk_native_session.cpp"
    "${FG_ROOT}/ps5/third_party/volk/volk.c")
target_include_directories(eden-r08-native-objects PRIVATE
    "${FG_INCLUDE}" "${FG_CORE}" "${FG_EXT}" "${FG_QUAL}" "${EDEN_H}")
set_source_files_properties("${FG_ROOT}/ps5/third_party/volk/volk.c"
    PROPERTIES LANGUAGE CXX)
target_compile_definitions(eden-r08-native-objects PRIVATE
    VK_NO_PROTOTYPES=1 VOLK_NAMESPACE=1)
target_compile_options(eden-r08-native-objects PRIVATE
    -Wall -Wextra -Wno-missing-designated-field-initializers
    "SHELL:-include ${EDEN_H}/mihawk_volk.h")
set_target_properties(eden-r08-native-objects PROPERTIES EXCLUDE_FROM_ALL OFF)
add_library(eden-r08-fsr3-optical OBJECT
    "${FSR3_OF_ROOT}/src/ps5_framegen.cpp"
    "${EDEN_H}/fsr3_optical_session.cpp")
target_include_directories(eden-r08-fsr3-optical PRIVATE
    "${FSR3_OF_ROOT}/src" "${FG_EXT}" "${EDEN_H}" "${FG_QUAL}")
target_compile_definitions(eden-r08-fsr3-optical PRIVATE
    PS5_FRAMEGEN_VULKAN_HEADER="mihawk_volk.h")
target_compile_options(eden-r08-fsr3-optical PRIVATE
    -Wall -Wextra -Wno-unused-parameter -Wno-missing-field-initializers)


function(eden_r08_test NAME)
    add_executable("${NAME}" "${EDEN_ROOT}/extras/graphics/${NAME}.cpp" ${ARGN})
    target_include_directories("${NAME}" PRIVATE "${FG_EXT}" "${FG_INCLUDE}" "${EDEN_H}" "${FG_QUAL}")
    # Assertions must stay active even under Release/-DNDEBUG.
    target_compile_options("${NAME}" PRIVATE -Wall -Wextra -UNDEBUG)
    add_test(NAME "${NAME}" COMMAND "${NAME}")
endfunction()
eden_r08_test(test_aa_source_extent)
eden_r08_test(test_fsr31_temporal_contract)
eden_r08_test(test_fsr31_native_resource_contract)
eden_r08_test(test_msaa_force_policy)
eden_r08_test(test_fsr31_vram_budget)
eden_r08_test(test_rdna2_nr_projection_policy)
eden_r08_test(test_rdna2_nr_token_repack_policy)
eden_r08_test(test_rdna2_nr_upsample_view_policy)
eden_r08_test(test_rdna2_nr_noise_field_policy)
eden_r08_test(test_rdna2_nr_decoder_upsample_policy)
eden_r08_test(test_rdna2_nr_decoder_projection_policy)
add_test(NAME test_rdna2_nr_decoder_fp32_to_fp16_spirv_abi
    COMMAND "${Python3_EXECUTABLE}"
        "${CMAKE_CURRENT_SOURCE_DIR}/test-rdna2-decoder-fp32-to-fp16-spv.py"
        --vendor "${EDEN_ROOT}/vendor")

eden_r08_test(test_rdna2_nr_window_attention_policy)
eden_r08_test(test_rdna2_nr_qkv_projection_policy)
eden_r08_test(test_rdna2_nr_ffwd3_policy)
eden_r08_test(test_rdna2_nr_vit_attention_policy)
eden_r08_test(test_rdna2_nr_vit_qkv_norm_policy)
eden_r08_test(test_rdna2_nr_vit_projection_stage_policy)
eden_r08_test(test_rdna2_nr_vit_epilogue_policy)
eden_r08_test(test_rdna2_nr_split_context_repack_policy)
eden_r08_test(test_rdna2_nr_vit_qkv_batches_policy)
eden_r08_test(test_rdna2_nr_vit_gpu_tensors_policy)
eden_r08_test(test_rdna2_nr_fswin_dense_policy)
eden_r08_test(test_rdna2_nr_fswin_qkv_policy)
eden_r08_test(test_rdna2_nr_fswin_graph_policy)
eden_r08_test(test_rdna2_nr_fswin_plan)
eden_r08_test(test_rdna2_nr_fswin_window_repack_policy)
eden_r08_test(test_rdna2_nr_fswin_chain_layout_policy)
eden_r08_test(test_rdna2_nr_native_plan_bridge)
eden_r08_test(test_rdna2_nr_fswin_output_view_policy)
eden_r08_test(test_rdna2_nr_fswin_downsample_policy)
eden_r08_test(test_rdna2_nr_float_quantize_policy)
eden_r08_test(test_rdna2_nr_projection_quantized_policy)
eden_r08_test(test_rdna2_nr_fswin_level_link_policy)
add_executable(test_neural_video_policy
    "${EDEN_ROOT}/tools/graphics/test_neural_video_policy.cpp")
target_include_directories(test_neural_video_policy PRIVATE "${EDEN_ROOT}/headless")
target_compile_options(test_neural_video_policy PRIVATE -Wall -Wextra -UNDEBUG)
add_test(NAME test_neural_video_policy COMMAND test_neural_video_policy)
add_executable(test_rdna2_nr_unet_skip_cache_policy
    "${EDEN_ROOT}/extras/graphics/test_rdna2_nr_unet_skip_cache_policy.cpp")
target_include_directories(test_rdna2_nr_unet_skip_cache_policy PRIVATE
    "${EDEN_ROOT}/vendor/encore-active/eden-vulkan/include"
    "${EDEN_ROOT}/extras/graphics")
target_compile_options(test_rdna2_nr_unet_skip_cache_policy PRIVATE
    -Wall -Wextra -UNDEBUG)
add_test(NAME test_rdna2_nr_unet_skip_cache_policy
    COMMAND test_rdna2_nr_unet_skip_cache_policy
    "${EDEN_ROOT}/extras/graphics/fixtures/r09_nr_original_1920x1080.txt"
    "${EDEN_ROOT}/extras/graphics/fixtures/r09_nr_small_1920x1080.txt")
# R09 native JSON storage regression; build only when host JSON header is present.
include(CheckIncludeFileCXX)
check_include_file_cxx("nlohmann/json.hpp" EDEN_R09_HAS_NLOHMANN_JSON)
if(EDEN_R09_HAS_NLOHMANN_JSON)
    add_executable(test_rdna2_nr_settings_store
        "${EDEN_ROOT}/tools/graphics/test_rdna2_nr_settings_store.cpp")
    target_include_directories(test_rdna2_nr_settings_store PRIVATE
        "${EDEN_ROOT}/headless")
    target_compile_options(test_rdna2_nr_settings_store PRIVATE -UNDEBUG)
    add_test(NAME test_rdna2_nr_settings_store COMMAND test_rdna2_nr_settings_store)
else()
    message(STATUS "R09 neural settings host test skipped: nlohmann/json.hpp unavailable")
endif()
eden_r08_test(test_rdna2_nr_fswin_upsample_policy)
# Check exact native U-Net upsample edges and odd-resolution lower bounds.
add_executable(test_rdna2_nr_unet_upsample_edges
    "${EDEN_ROOT}/extras/graphics/test_rdna2_nr_unet_upsample_edges.cpp")
target_include_directories(test_rdna2_nr_unet_upsample_edges PRIVATE
    "${EDEN_ROOT}/extras/graphics"
    "${EDEN_ROOT}/vendor/encore-active/eden-vulkan/include")
target_compile_options(test_rdna2_nr_unet_upsample_edges PRIVATE
    -Wall -Wextra -UNDEBUG)
add_test(NAME test_rdna2_nr_unet_upsample_edges
    COMMAND test_rdna2_nr_unet_upsample_edges
    "${EDEN_ROOT}/extras/graphics/fixtures/r09_nr_original_1920x1080.txt"
    "${EDEN_ROOT}/extras/graphics/fixtures/r09_nr_small_1920x1080.txt")

target_include_directories(test_rdna2_nr_fswin_output_view_policy PRIVATE
    "${EDEN_ROOT}/vendor/encore-active/eden-vulkan/include")
# R09: validate recovered full native graph structural manifests.
# Decode EVERY native NR graph stage, no implicit skip.
add_executable(test_rdna2_nr_native_graph_schedule
    "${EDEN_ROOT}/extras/graphics/test_rdna2_nr_native_graph_schedule.cpp")
target_include_directories(test_rdna2_nr_native_graph_schedule PRIVATE
    "${EDEN_ROOT}/vendor/encore-active/eden-vulkan/include"
    "${EDEN_ROOT}/extras/graphics")
target_compile_options(test_rdna2_nr_native_graph_schedule PRIVATE
    -Wall -Wextra -UNDEBUG)
add_test(NAME test_rdna2_nr_native_graph_schedule
    COMMAND test_rdna2_nr_native_graph_schedule
    "${EDEN_ROOT}/extras/graphics/fixtures/r09_nr_original_1920x1080.txt"
    "${EDEN_ROOT}/extras/graphics/fixtures/r09_nr_small_1920x1080.txt")

add_executable(test_rdna2_nr_native_plan_corpus
    "${EDEN_ROOT}/extras/graphics/test_rdna2_nr_native_plan_corpus.cpp")
target_include_directories(test_rdna2_nr_native_plan_corpus PRIVATE
    "${EDEN_ROOT}/vendor/encore-active/eden-vulkan/include"
    "${EDEN_ROOT}/extras/graphics")
target_compile_options(test_rdna2_nr_native_plan_corpus PRIVATE
    -Wall -Wextra -UNDEBUG)
add_executable(test_rdna2_nr_unet_skip_map
    "${EDEN_ROOT}/extras/graphics/test_rdna2_nr_unet_skip_map.cpp")
target_include_directories(test_rdna2_nr_unet_skip_map PRIVATE
    "${EDEN_ROOT}/vendor/encore-active/eden-vulkan/include"
    "${EDEN_ROOT}/extras/graphics")
target_compile_options(test_rdna2_nr_unet_skip_map PRIVATE
    -Wall -Wextra -UNDEBUG)
add_test(NAME test_rdna2_nr_unet_skip_map
    COMMAND test_rdna2_nr_unet_skip_map
    "${EDEN_ROOT}/extras/graphics/fixtures/r09_nr_original_1920x1080.txt"
    "${EDEN_ROOT}/extras/graphics/fixtures/r09_nr_small_1920x1080.txt")

add_test(NAME test_rdna2_nr_native_plan_corpus
    COMMAND test_rdna2_nr_native_plan_corpus
    "${EDEN_ROOT}/extras/graphics/fixtures/r09_nr_original_1920x1080.txt"
    "${EDEN_ROOT}/extras/graphics/fixtures/r09_nr_small_1920x1080.txt")
target_include_directories(test_rdna2_nr_native_plan_bridge PRIVATE
    "${EDEN_ROOT}/vendor/encore-active/eden-vulkan/include")
eden_r08_test(test_rdna2_nr_fswin_raster_layout_policy)
eden_r08_test(test_rdna2_nr_fswin_raster_host)
target_include_directories(test_rdna2_nr_fswin_raster_host PRIVATE
    "${EDEN_ROOT}/vendor/encore-active/eden-vulkan/include")
eden_r08_test(test_rdna2_nr_e4m3_requantize)
target_include_directories(test_rdna2_nr_e4m3_requantize PRIVATE
    "${EDEN_ROOT}/vendor/encore-active/eden-vulkan/include")
target_include_directories(test_rdna2_nr_fswin_plan PRIVATE
    "${EDEN_ROOT}/vendor/encore-active/eden-vulkan/include")
eden_r08_test(test_rdna2_nr_model_pack)
target_include_directories(test_rdna2_nr_model_pack PRIVATE
    "${EDEN_ROOT}/vendor/encore-active/eden-vulkan/include")
eden_r08_test(test_rdna2_nr_model_file)
target_include_directories(test_rdna2_nr_model_file PRIVATE
    "${EDEN_ROOT}/vendor/encore-active/eden-vulkan/include")
eden_r08_test(test_rdna2_nr_weight_decode)
eden_r08_test(test_rdna2_nr_fswin_qkv_layout)
target_include_directories(test_rdna2_nr_fswin_qkv_layout PRIVATE
    "${EDEN_ROOT}/vendor/encore-active/eden-vulkan/include")
eden_r08_test(test_rdna2_nr_fswin_bindings)
target_include_directories(test_rdna2_nr_fswin_bindings PRIVATE
    "${EDEN_ROOT}/vendor/encore-active/eden-vulkan/include")
target_include_directories(test_rdna2_nr_weight_decode PRIVATE
    "${EDEN_ROOT}/vendor/encore-active/eden-vulkan/include")
eden_r08_test(test_rdna2_nr_tile_layout)
target_include_directories(test_rdna2_nr_tile_layout PRIVATE
    "${EDEN_ROOT}/vendor/encore-active/eden-vulkan/include")
eden_r08_test(test_fsr1_sharpness_policy)
eden_r08_test(test_sgsr_sharpness_policy)
eden_r08_test(test_fxaa_quality_select "${EDEN_H}/fxaa_quality_select.cpp")
eden_r08_test(test_framegen_capabilities)
eden_r08_test(test_graphics_pipeline_policy)
eden_r08_test(test_framegen_present_gate)
eden_r08_test(test_mihawk_native_surface_contract)
eden_r08_test(test_mihawk_submission_timeline)
eden_r08_test(test_mihawk_capture_fences)
eden_r08_test(test_mihawk_vulkan_history_barriers)
eden_r08_test(test_mihawk_post_hud_barriers)
eden_r08_test(test_mihawk_session_resize)
eden_r08_test(test_lossless_user_file)
eden_r08_test(test_mihawk_vulkan_record
    "${EDEN_H}/mihawk_vulkan_stage.cpp"
    "${EDEN_H}/mihawk_vulkan_encoder.cpp")
eden_r08_test(test_mihawk_vulkan_resources "${EDEN_H}/mihawk_vulkan_resources.cpp")

add_executable(test_fsr3_optical_pacing
    "${FSR3_OF_ROOT}/tests/test_pacing.cpp")
target_include_directories(test_fsr3_optical_pacing PRIVATE "${FSR3_OF_ROOT}/src")
target_compile_options(test_fsr3_optical_pacing PRIVATE -UNDEBUG)
add_test(NAME test_fsr3_optical_pacing COMMAND test_fsr3_optical_pacing)

# R09: QKV producer -> attention consumer: same GPU tensors, no skipped pass.
add_executable(test_rdna2_nr_split_window_link
    "${EDEN_ROOT}/extras/graphics/test_rdna2_nr_split_window_link.cpp")
target_include_directories(test_rdna2_nr_split_window_link PRIVATE
    "${EDEN_ROOT}/vendor/encore-active/eden-vulkan/include"
    "${EDEN_ROOT}/extras/graphics")
target_compile_options(test_rdna2_nr_split_window_link PRIVATE
    -Wall -Wextra -UNDEBUG)
add_test(NAME test_rdna2_nr_split_window_link
    COMMAND test_rdna2_nr_split_window_link)
# Compare actual GLSL semantic binding numbers to BOTH C++ Vulkan writers.
add_test(NAME test_rdna2_nr_attention_descriptor_abi
    COMMAND "${Python3_EXECUTABLE}"
        "${CMAKE_CURRENT_SOURCE_DIR}/test-rdna2-attention-binding-order.py"
        --vendor "${EDEN_ROOT}/vendor")


# Real RDNA2 ViT normalization compute shader (Vulkan 1.1 + SPIR-V ABI).
if(EXISTS "${EDEN_ROOT}/vendor/encore-active/eden-vulkan/r09_rdna2_nr/vit_qkv_norm_rdna2.comp")
    add_test(NAME test_rdna2_nr_vit_qkv_norm_spirv_abi
        COMMAND "${Python3_EXECUTABLE}"
            "${CMAKE_CURRENT_SOURCE_DIR}/test-rdna2-vit-qkv-norm-spv.py"
            --vendor "${EDEN_ROOT}/vendor")
endif()

# Import native ViT 32-head QKV matrices and FP32 temperatures from synthetic
# NRMODEL1 fixture, including failure-atomic invalid tensors.
add_executable(test_rdna2_nr_vit_qkv_weight_loader
    "${EDEN_ROOT}/extras/graphics/test_rdna2_nr_vit_qkv_weight_loader.cpp")
target_include_directories(test_rdna2_nr_vit_qkv_weight_loader PRIVATE
    "${EDEN_ROOT}/vendor/encore-active/eden-vulkan/include"
    "${EDEN_ROOT}/extras/graphics")
target_compile_options(test_rdna2_nr_vit_qkv_weight_loader PRIVATE
    -Wall -Wextra -UNDEBUG)
add_test(NAME test_rdna2_nr_vit_qkv_weight_loader
    COMMAND test_rdna2_nr_vit_qkv_weight_loader)

# Split-Swin native model data: exact QKV head-major layout and FP16 bias.
add_executable(test_rdna2_nr_split_window_weight_loader
    "${EDEN_ROOT}/extras/graphics/test_rdna2_nr_split_window_weight_loader.cpp")
target_include_directories(test_rdna2_nr_split_window_weight_loader PRIVATE
    "${EDEN_ROOT}/vendor/encore-active/eden-vulkan/include"
    "${EDEN_ROOT}/extras/graphics")
target_compile_options(test_rdna2_nr_split_window_weight_loader PRIVATE
    -Wall -Wextra -UNDEBUG)
add_test(NAME test_rdna2_nr_split_window_weight_loader
    COMMAND test_rdna2_nr_split_window_weight_loader)

# Native Split-Swin FFWD: two canonical source matrices -> W1/W2/W3,
# roundtrip and every address verified against the upstream bit maps.
add_executable(test_rdna2_nr_split_ffwd_weights
    "${EDEN_ROOT}/extras/graphics/test_rdna2_nr_split_ffwd_weights.cpp")
target_include_directories(test_rdna2_nr_split_ffwd_weights PRIVATE
    "${EDEN_ROOT}/vendor/encore-active/eden-vulkan/include"
    "${EDEN_ROOT}/extras/graphics")
target_compile_options(test_rdna2_nr_split_ffwd_weights PRIVATE
    -Wall -Wextra -UNDEBUG)
add_test(NAME test_rdna2_nr_split_ffwd_weights
    COMMAND test_rdna2_nr_split_ffwd_weights)

add_test(NAME test_rdna2_nr_vit_epilogues_spirv_abi
    COMMAND "${Python3_EXECUTABLE}"
        "${CMAKE_CURRENT_SOURCE_DIR}/test-rdna2-vit-epilogues-spv.py"
        --vendor "${EDEN_ROOT}/vendor")

# Local model Split-Swin residual projection: [512,512] FP8 plus 512 FP16
# gain values, reject bad input and preserve complete output.
add_executable(test_rdna2_nr_split_residual_weights
    "${EDEN_ROOT}/extras/graphics/test_rdna2_nr_split_residual_weights.cpp")
target_include_directories(test_rdna2_nr_split_residual_weights PRIVATE
    "${EDEN_ROOT}/vendor/encore-active/eden-vulkan/include"
    "${EDEN_ROOT}/extras/graphics")
target_compile_options(test_rdna2_nr_split_residual_weights PRIVATE
    -Wall -Wextra -UNDEBUG)
add_test(NAME test_rdna2_nr_split_residual_weights
    COMMAND test_rdna2_nr_split_residual_weights)

add_test(NAME test_rdna2_nr_split_context_repack_spirv_abi
    COMMAND "${Python3_EXECUTABLE}"
        "${CMAKE_CURRENT_SOURCE_DIR}/test-rdna2-split-context-repack-spv.py"
        --vendor "${EDEN_ROOT}/vendor")

# One native, fully bound (non-pooled) Split-Swin16H block: CPU shape and
# buffer-limit coverage before GPU command recording.
add_executable(test_rdna2_nr_split_block_policy
    "${EDEN_ROOT}/extras/graphics/test_rdna2_nr_split_block_policy.cpp")
target_include_directories(test_rdna2_nr_split_block_policy PRIVATE
    "${EDEN_ROOT}/vendor/encore-active/eden-vulkan/include"
    "${EDEN_ROOT}/extras/graphics")
target_compile_options(test_rdna2_nr_split_block_policy PRIVATE
    -Wall -Wextra -UNDEBUG)
add_test(NAME test_rdna2_nr_split_block_policy
    COMMAND test_rdna2_nr_split_block_policy)

# Native CCSplitSwin16HProjPool's actual second output: source mapping,
# half-res 4x4 tiles, borders, zero-fill tail, strict descriptor bounds.
add_executable(test_rdna2_nr_split_projection_pool_policy
    "${EDEN_ROOT}/extras/graphics/test_rdna2_nr_split_projection_pool_policy.cpp")
target_include_directories(test_rdna2_nr_split_projection_pool_policy PRIVATE
    "${EDEN_ROOT}/extras/graphics")
target_compile_options(test_rdna2_nr_split_projection_pool_policy PRIVATE
    -Wall -Wextra -UNDEBUG)
add_test(NAME test_rdna2_nr_split_projection_pool_policy
    COMMAND test_rdna2_nr_split_projection_pool_policy)
add_test(NAME test_rdna2_nr_split_projection_pool_spirv_abi
    COMMAND "${Python3_EXECUTABLE}"
        "${CMAKE_CURRENT_SOURCE_DIR}/test-rdna2-split-projection-pool-spv.py"
        --vendor "${EDEN_ROOT}/vendor")

# Native FinalHead 512->1024 projection: local NRMODEL1, FP8 GEMM and
# FP32->FP8 quantizer on the same scheduler.
add_executable(test_rdna2_nr_split_final_head_weights
    "${EDEN_ROOT}/extras/graphics/test_rdna2_nr_split_final_head_weights.cpp")
target_include_directories(test_rdna2_nr_split_final_head_weights PRIVATE
    "${EDEN_ROOT}/vendor/encore-active/eden-vulkan/include"
    "${EDEN_ROOT}/extras/graphics")
target_compile_options(test_rdna2_nr_split_final_head_weights PRIVATE
    -Wall -Wextra -UNDEBUG)
add_test(NAME test_rdna2_nr_split_final_head_weights
    COMMAND test_rdna2_nr_split_final_head_weights)

# Validate all native 16/4 Split-Swin blocks and their routed shifts from
# the complete 152/76-row original/compact corpus (host-only, no GPU).
add_executable(test_rdna2_nr_split_native_routes_policy
    "${EDEN_ROOT}/extras/graphics/test_rdna2_nr_split_native_routes_policy.cpp")
target_include_directories(test_rdna2_nr_split_native_routes_policy PRIVATE
    "${EDEN_ROOT}/vendor/encore-active/eden-vulkan/include"
    "${EDEN_ROOT}/extras/graphics")
target_compile_options(test_rdna2_nr_split_native_routes_policy PRIVATE
    -Wall -Wextra -UNDEBUG)
add_test(NAME test_rdna2_nr_split_native_routes_policy
    COMMAND test_rdna2_nr_split_native_routes_policy
        "${EDEN_ROOT}/extras/graphics/fixtures/r09_nr_original_1920x1080.txt"
        "${EDEN_ROOT}/extras/graphics/fixtures/r09_nr_small_1920x1080.txt")

# Local-only NRMODEL1 learned ViT FFN: 4096x1024, 1024x4096,
# 1024x1024, and both exact 1024-value FP16 residual gains.
add_executable(test_rdna2_nr_vit_ffn_weight_loader
    "${EDEN_ROOT}/extras/graphics/test_rdna2_nr_vit_ffn_weight_loader.cpp")
target_include_directories(test_rdna2_nr_vit_ffn_weight_loader PRIVATE
    "${EDEN_ROOT}/vendor/encore-active/eden-vulkan/include"
    "${EDEN_ROOT}/extras/graphics")
target_compile_options(test_rdna2_nr_vit_ffn_weight_loader PRIVATE
    -Wall -Wextra -UNDEBUG)
add_test(NAME test_rdna2_nr_vit_ffn_weight_loader
    COMMAND test_rdna2_nr_vit_ffn_weight_loader)

# Exactly five operations per native ViT block and eight blocks per model;
# prove real split FinalHead->ViT->decoder dependencies on both corpora.
add_executable(test_rdna2_nr_vit_native_route_policy
    "${EDEN_ROOT}/extras/graphics/test_rdna2_nr_vit_native_route_policy.cpp")
target_include_directories(test_rdna2_nr_vit_native_route_policy PRIVATE
    "${EDEN_ROOT}/vendor/encore-active/eden-vulkan/include"
    "${EDEN_ROOT}/extras/graphics")
target_compile_options(test_rdna2_nr_vit_native_route_policy PRIVATE
    -Wall -Wextra -UNDEBUG)
add_test(NAME test_rdna2_nr_vit_native_route_policy
    COMMAND test_rdna2_nr_vit_native_route_policy
        "${EDEN_ROOT}/extras/graphics/fixtures/r09_nr_original_1920x1080.txt"
        "${EDEN_ROOT}/extras/graphics/fixtures/r09_nr_small_1920x1080.txt")

# R09 restored FinalHead/ViT tile-raster buffer ABI (no device required).
add_executable(test_rdna2_nr_vit_boundary_repack_policy
    "${EDEN_ROOT}/extras/graphics/test_rdna2_nr_vit_boundary_repack_policy.cpp")
target_include_directories(test_rdna2_nr_vit_boundary_repack_policy PRIVATE
    "${EDEN_ROOT}/vendor/encore-active/eden-vulkan/include")
target_compile_options(test_rdna2_nr_vit_boundary_repack_policy PRIVATE -Wall -Wextra -Werror -UNDEBUG)
add_test(NAME test_rdna2_nr_vit_boundary_repack_policy
    COMMAND test_rdna2_nr_vit_boundary_repack_policy)
add_test(NAME test_rdna2_nr_vit_boundary_repack_spirv_abi
    COMMAND "${Python3_EXECUTABLE}"
        "${CMAKE_CURRENT_SOURCE_DIR}/test-rdna2-vit-boundary-repack-spv.py"
        --vendor "${EDEN_ROOT}/vendor")

# Learned native Original/Compact decoder: local NRMODEL1
# [512,1024] FP8 matrix plus FP16[512] skip gains.
add_executable(test_rdna2_nr_decoder_model_loader
    "${EDEN_ROOT}/extras/graphics/test_rdna2_nr_decoder_model_loader.cpp")
target_include_directories(test_rdna2_nr_decoder_model_loader PRIVATE
    "${EDEN_ROOT}/vendor/encore-active/eden-vulkan/include"
    "${EDEN_ROOT}/extras/graphics")
target_compile_options(test_rdna2_nr_decoder_model_loader PRIVATE
    -Wall -Wextra -UNDEBUG)
add_test(NAME test_rdna2_nr_decoder_model_loader
    COMMAND test_rdna2_nr_decoder_model_loader)

# GPU-native 8x8-window FP8[512] skip -> 4x4 token / 16x16 channel
# decoder layout; exhaustive host oracle incl 180 padded 1080p tokens.
eden_r08_test(test_rdna2_nr_split_decoder_skip_repack_policy)
add_test(NAME test_rdna2_nr_split_decoder_skip_spirv_abi
    COMMAND "${Python3_EXECUTABLE}"
        "${CMAKE_CURRENT_SOURCE_DIR}/test-rdna2-split-decoder-skip-spv.py"
        --vendor "${EDEN_ROOT}/vendor")

# Decoder's 4x4 tiled C1024 E4M3FN input must be raster-major before GEMM.
eden_r08_test(test_rdna2_nr_decoder_tile_to_linear_policy)
add_test(NAME test_rdna2_nr_decoder_tile_linear_spirv_abi
    COMMAND "${Python3_EXECUTABLE}"
        "${CMAKE_CURRENT_SOURCE_DIR}/test-rdna2-decoder-tile-linear-spv.py"
        --vendor "${EDEN_ROOT}/vendor")

# Native central Original/Compact route; IDs, geometry, and dependencies.
add_executable(test_rdna2_nr_bottleneck_route_policy
    "${EDEN_ROOT}/extras/graphics/test_rdna2_nr_bottleneck_route_policy.cpp")
target_include_directories(test_rdna2_nr_bottleneck_route_policy PRIVATE
    "${EDEN_ROOT}/vendor/encore-active/eden-vulkan/include"
    "${EDEN_ROOT}/extras/graphics")
target_compile_options(test_rdna2_nr_bottleneck_route_policy PRIVATE
    -Wall -Wextra -Werror -UNDEBUG)
add_test(NAME test_rdna2_nr_bottleneck_route_policy
    COMMAND test_rdna2_nr_bottleneck_route_policy
        "${EDEN_ROOT}/extras/graphics/fixtures/r09_nr_original_1920x1080.txt"
        "${EDEN_ROOT}/extras/graphics/fixtures/r09_nr_small_1920x1080.txt")

# Imported pre/post matrix weights are local NRMODEL1, never shipped;
# this stage handles 16-feature tensors, not raw game RGB/HDR.
eden_r08_test(test_rdna2_nr_image_feature_policy)
add_executable(test_rdna2_nr_image_feature_weights
    "${EDEN_ROOT}/extras/graphics/test_rdna2_nr_image_feature_weights.cpp")
target_include_directories(test_rdna2_nr_image_feature_weights PRIVATE
    "${EDEN_ROOT}/vendor/encore-active/eden-vulkan/include"
    "${EDEN_ROOT}/extras/graphics")
target_compile_options(test_rdna2_nr_image_feature_weights PRIVATE
    -Wall -Wextra -Werror -UNDEBUG)
add_test(NAME test_rdna2_nr_image_feature_weights
    COMMAND test_rdna2_nr_image_feature_weights)
add_test(NAME test_rdna2_nr_image_feature_spirv_abi
    COMMAND "${Python3_EXECUTABLE}"
        "${CMAKE_CURRENT_SOURCE_DIR}/test-rdna2-image-feature-spv.py"
        --vendor "${EDEN_ROOT}/vendor")

# No-history proxy RGBA32F -> sixteen FP16 channels (model entry primitive).
eden_r08_test(test_rdna2_nr_proxy_feature_policy)
add_test(NAME test_rdna2_nr_proxy_feature_spirv_abi
    COMMAND "${Python3_EXECUTABLE}"
        "${CMAKE_CURRENT_SOURCE_DIR}/test-rdna2-proxy-features-spv.py"
        --vendor "${EDEN_ROOT}/vendor")

# The pre-normalized first frame and learned local NRMODEL1 lift must use
# one scheduler, one exact FP16[16] intermediate and a C32 output tensor.
eden_r08_test(test_rdna2_nr_proxy_lift_link_policy)
