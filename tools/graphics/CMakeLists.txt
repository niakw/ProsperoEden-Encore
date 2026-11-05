cmake_minimum_required(VERSION 3.20)
project(eden_r08_mihawk_host_checks LANGUAGES C CXX)
# Host-only: compile exactly the source files used by the Encore PS5
# qualification target. No renderer or SDK, and no PS5 packaging.
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
enable_testing()
get_filename_component(EDEN_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/../.." ABSOLUTE)
set(FG_ROOT "${EDEN_ROOT}/third_party/PS5_MihawkGen")
set(FSR3_OF_ROOT "${EDEN_ROOT}/third_party/PS5_FSR3OpticalFlow")
if(NOT EXISTS "${FSR3_OF_ROOT}/src/framegen/fg_shaders.inc")
    message(FATAL_ERROR "Missing git submodule third_party/PS5_FSR3OpticalFlow")
endif()
set(FG_CORE "${FG_ROOT}/framegen/src")
set(FG_INCLUDE "${FG_ROOT}/framegen/include")
set(FG_EXT "${FG_ROOT}/external")
set(EDEN_H "${EDEN_ROOT}/headless")
set(FG_QUAL "${EDEN_ROOT}/extras/graphics")
set(VOLK_HEADER "${FG_ROOT}/ps5/third_party/volk/volk.h")
foreach(REQUIRED "${FG_INCLUDE}/framegen.h" "${VOLK_HEADER}")
    if(NOT EXISTS "${REQUIRED}")
        message(FATAL_ERROR "Run git submodule update --init third_party/PS5_MihawkGen: ${REQUIRED}")
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
eden_r08_test(test_fsr1_sharpness_policy)
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
