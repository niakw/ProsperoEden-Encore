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
file(GLOB_RECURSE EDEN_VULKAN_FORK_FILES CONFIGURE_DEPENDS "${EDEN_ACTIVE_VULKAN}/*")
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS ${EDEN_VULKAN_FORK_FILES})
# These shaders are build inputs; the five older .inc injections only
# reconstruct the historical generator oracle and are NOT compiled here.
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS
    "${EDEN_PORT_DIR}/vulkan_hud.vert" "${EDEN_PORT_DIR}/vulkan_hud.frag")
list(REMOVE_ITEM video_sources vulkan_common/vulkan_device.cpp renderer_vulkan/vk_scheduler.cpp)
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
list(APPEND video_sources "${PORT_BUILD_DIR}/vulkan_device.cpp" "${PORT_BUILD_DIR}/vulkan_scheduler.cpp")
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

target_include_directories(video_core BEFORE PUBLIC "${PORT_BUILD_DIR}/include")
target_include_directories(video_core BEFORE PUBLIC "${PORT_BUILD_DIR}/vulkan-cache")
target_include_directories(video_core PRIVATE
    "${PORT_BUILD_DIR}" "${EDEN_PORT_DIR}" "${PORT_ROOT}/extras/graphics"
    "${PORT_ROOT}/third_party/PS5_MihawkGen/framegen/include"
    "${PORT_ROOT}/third_party/PS5_MihawkGen/external")
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
set(EDEN_MIHAWKGEN_ROOT "${PORT_ROOT}/third_party/PS5_MihawkGen")
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
target_sources(video_core PRIVATE $<TARGET_OBJECTS:eden-mihawkgen-native>)

# R08 AMD candidate: FSR3 optical-flow shaders and a PS5-native Vulkan
# interpolator, from Swordpdf/ps5-framegen. Not an official FSR3 backend.
set(EDEN_FSR3_OF_ROOT "${PORT_ROOT}/third_party/PS5_FSR3OpticalFlow")
if(NOT EXISTS "${EDEN_FSR3_OF_ROOT}/src/framegen/fg_shaders.inc")
    message(FATAL_ERROR "Missing pinned PS5 FSR3 optical-flow source")
endif()
target_sources(video_core PRIVATE
    "${EDEN_FSR3_OF_ROOT}/src/ps5_framegen.cpp"
    "${EDEN_PORT_DIR}/fsr3_optical_session.cpp")
set_source_files_properties("${EDEN_FSR3_OF_ROOT}/src/ps5_framegen.cpp"
    PROPERTIES COMPILE_DEFINITIONS "PS5_FRAMEGEN_VULKAN_HEADER=\"mihawk_volk.h\"")
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
target_sources(video_core PRIVATE ${EDEN_LSFG_NATIVE_SOURCES})
target_compile_definitions(video_core PUBLIC HAS_LSFG)
