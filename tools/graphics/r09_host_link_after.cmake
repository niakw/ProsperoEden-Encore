# SPDX-License-Identifier: MIT
# Appended AFTER the immutable upstream Eden CMake tree defines video_core.
# Host Linux only: NO PS5_NATIVE, PS5 SDK or PS5 global packaging.
if(NOT CMAKE_SYSTEM_NAME STREQUAL "Linux")
    message(FATAL_ERROR "R09 full host integration requires Linux")
endif()
if(NOT TARGET video_core OR NOT TARGET common)
    message(FATAL_ERROR "Missing genuine upstream Eden Vulkan/core libraries")
endif()
if(NOT IS_ABSOLUTE "${ENCORE_R09_ROOT}")
    message(FATAL_ERROR "Provide absolute ENCORE_R09_ROOT")
endif()
set(_r09_vendor "${ENCORE_R09_ROOT}/vendor")
set(_r09_active "${_r09_vendor}/encore-active/eden-vulkan")
set(_r09_shader_include "${CMAKE_BINARY_DIR}/r09-host-generated")
# Derive the linked owner set from the shipping PS5 native source list.
# Do NOT invent a synthetic 73rd source: split_to_vit_bridge is not linked.
file(STRINGS "${ENCORE_R09_ROOT}/headless/vulkan.cmake"
    _r09_cpp_lines REGEX "nr_rdna2_[a-z0-9_]+[.]cpp")
set(_r09_cpp "")
foreach(_r09_line IN LISTS _r09_cpp_lines)
    string(REGEX MATCH "nr_rdna2_[a-z0-9_]+[.]cpp" _r09_name "${_r09_line}")
    if(_r09_name)
        list(APPEND _r09_cpp "${_r09_active}/${_r09_name}")
    endif()
endforeach()
list(REMOVE_DUPLICATES _r09_cpp)
list(LENGTH _r09_cpp _r09_n)
if(_r09_n LESS 72)
    message(FATAL_ERROR "R09 operator set incomplete (${_r09_n})")
endif()
find_package(Python3 REQUIRED COMPONENTS Interpreter)
find_program(R09_GLSLANG glslangValidator REQUIRED)
find_program(R09_SPIRV_VAL spirv-val REQUIRED)
execute_process(
    COMMAND "${Python3_EXECUTABLE}"
        "${ENCORE_R09_ROOT}/tools/graphics/r09_generate_host_spirv.py"
        --vendor "${_r09_vendor}"
        --output "${_r09_shader_include}/video_core/host_shaders"
    RESULT_VARIABLE _r09_shader_rc
    OUTPUT_VARIABLE _r09_shader_out ERROR_VARIABLE _r09_shader_err)
if(NOT _r09_shader_rc EQUAL 0)
    message(FATAL_ERROR "R09 genuine SPIR-V generation failed: ${_r09_shader_out} ${_r09_shader_err}")
endif()
message(STATUS "${_r09_shader_out}")

# The host compiles pristine Eden Vulkan implementation .cpp files.
# PS5-maintained fork headers alter these ABIs for console presentation,
# Task/Mesh shaders and GPU cache ticks. Do not mix those declarations with
# unmodified Linux implementations. Select exact pinned Linux headers only
# in this opt-in host target; no PS5 source/header is modified.
set(_r09_compat "${CMAKE_BINARY_DIR}/r09-host-compat")
foreach(_r09_header IN ITEMS
    video_core/renderer_vulkan/vk_graphics_pipeline.h
    video_core/renderer_vulkan/vk_buffer_cache.h
    video_core/renderer_vulkan/vk_blit_screen.h
    video_core/renderer_vulkan/present/window_adapt_pass.h)
    get_filename_component(_r09_header_dir "${_r09_header}" DIRECTORY)
    file(MAKE_DIRECTORY "${_r09_compat}/${_r09_header_dir}")
    configure_file(
        "${_r09_vendor}/sources/eden/src/${_r09_header}"
        "${_r09_compat}/${_r09_header}" COPYONLY)
endforeach()

# Reduce known compiler-warning floods only in the R09 Linux host build.
# Never edit the SHA-pinned Eden upstream directory or the native PS5 headers.
execute_process(
    COMMAND "${Python3_EXECUTABLE}"
        "${ENCORE_R09_ROOT}/tools/graphics/r09_prepare_host_warning_overlays.py"
        "${_r09_vendor}/sources/eden/src" "${_r09_compat}"
    RESULT_VARIABLE _r09_warning_patch_rc
    OUTPUT_VARIABLE _r09_warning_patch_out ERROR_VARIABLE _r09_warning_patch_err)
if(NOT _r09_warning_patch_rc EQUAL 0)
    message(FATAL_ERROR
        "R09 host-only warning overlay refused: ${_r09_warning_patch_out} ${_r09_warning_patch_err}")
endif()
message(STATUS "${_r09_warning_patch_out}")
foreach(_r09_target IN ITEMS
        common core video_core audio_core frontend_common
        hid_core input_common shader_recompiler)
    if(TARGET ${_r09_target})
        target_include_directories(${_r09_target} BEFORE PRIVATE "${_r09_compat}")
    endif()
endforeach()

# The scheduler/device/allocator are ABI-coupled with maintained neural
# owners. Remove the three pristine implementations, never compile duplicates.
get_target_property(_r09_video_sources video_core SOURCES)
foreach(_r09_pinned IN ITEMS
        renderer_vulkan/vk_scheduler.cpp
        vulkan_common/vulkan_device.cpp
        vulkan_common/vulkan_memory_allocator.cpp)
    list(FIND _r09_video_sources "${_r09_pinned}" _r09_old_index)
    if(_r09_old_index EQUAL -1)
        message(FATAL_ERROR "Pinned source changed: ${_r09_pinned}")
    endif()
    list(REMOVE_ITEM _r09_video_sources "${_r09_pinned}")
endforeach()
set_property(TARGET video_core PROPERTY SOURCES "${_r09_video_sources}")
target_sources(video_core PRIVATE ${_r09_cpp}
    "${_r09_active}/vulkan_scheduler.cpp"
    "${_r09_active}/vulkan_device.cpp"
    "${_r09_active}/vulkan_memory_allocator.cpp")
target_include_directories(video_core BEFORE PRIVATE
    "${_r09_compat}"
    "${_r09_shader_include}"
    "${_r09_active}/include"
    "${ENCORE_R09_ROOT}/headless"
    "${ENCORE_R09_ROOT}/extras/graphics")
# Host-only concrete implementations missing from the upstream video's
# header-only GPUOpen::VulkanMemoryAllocator linkage and standalone no-UI
# executable. Compile the real Vulkan Memory Allocator implementation exactly
# once and reuse pinned Eden's real PlayTimeManager source (no stubs).
add_executable(r09-full-gpu-host
    "${ENCORE_R09_ROOT}/tools/graphics/r09_full_gpu_host.cpp"
    "${ENCORE_R09_ROOT}/tools/graphics/r09_host_vma_impl.cpp"
    "${_r09_vendor}/sources/eden/src/frontend_common/play_time_manager.cpp")
target_compile_features(r09-full-gpu-host PRIVATE cxx_std_20)
# Research-only 720p Original GPU entry. OFF by default, never set by the
# production PS5 pipeline or normal Linux host link. Requires an actual
# user-authorized, SHA-256 authenticated model and 1280x720 raw capture.
option(ENCORE_R09_MIN_720_HOST_RESEARCH
    "Permit manual Linux-host-only 720p Original neural research trial" OFF)
if(ENCORE_R09_MIN_720_HOST_RESEARCH)
    target_compile_definitions(r09-full-gpu-host PRIVATE
        EDEN_R09_MIN_720_HOST_EXPERIMENTAL=1)
    message(WARNING
        "R09 720p Original research GPU entry ON for LINUX HOST ONLY; "
        "GPU/model/PS5 performance NOT yet qualified")
else()
    target_compile_definitions(r09-full-gpu-host PRIVATE
        EDEN_R09_MIN_720_HOST_EXPERIMENTAL=0)
endif()
target_include_directories(r09-full-gpu-host BEFORE PRIVATE
    "${_r09_compat}"
    "${_r09_shader_include}"
    "${_r09_active}/include"
    "${ENCORE_R09_ROOT}/headless"
    "${ENCORE_R09_ROOT}/extras/graphics"
    "${_r09_vendor}/sources/eden/src")
target_link_libraries(r09-full-gpu-host PRIVATE video_core)
message(STATUS "R09 genuine Linux host target configured: ${_r09_n} GPU owners")
