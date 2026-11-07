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
    "${_r09_shader_include}"
    "${_r09_active}/include"
    "${ENCORE_R09_ROOT}/headless"
    "${ENCORE_R09_ROOT}/extras/graphics")
add_executable(r09-full-gpu-host
    "${ENCORE_R09_ROOT}/tools/graphics/r09_full_gpu_host.cpp")
target_compile_features(r09-full-gpu-host PRIVATE cxx_std_20)
target_include_directories(r09-full-gpu-host BEFORE PRIVATE
    "${_r09_shader_include}"
    "${_r09_active}/include"
    "${ENCORE_R09_ROOT}/headless"
    "${ENCORE_R09_ROOT}/extras/graphics"
    "${_r09_vendor}/sources/eden/src")
target_link_libraries(r09-full-gpu-host PRIVATE video_core)
message(STATUS "R09 genuine Linux host target configured: ${_r09_n} GPU owners")
