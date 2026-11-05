# P0.2: stage three complete, reviewed six-core source owners as plain copies.
# Never synthesize or rewrite C++ during a production CMake configure.
# tools/ns2/check_cpu6_scheduler_tick_host.py asserts the exact static
# overlay equals pinned upstream/G11 with only the three audited differences.
if(NOT DEFINED EDEN_CPU6_SOURCE_ROOT OR NOT DEFINED EDEN_CPU6_OUTPUT_ROOT OR
   NOT DEFINED EDEN_CPU6_A64_SOURCE OR NOT EXISTS "${EDEN_CPU6_A64_SOURCE}")
    message(FATAL_ERROR "CPU6 requires pinned source roots, G11 and destination")
endif()
file(READ "${EDEN_CPU6_A64_SOURCE}" eden_cpu6_g11_identity)
if(NOT eden_cpu6_g11_identity MATCHES "EDEN_NS2_GUEST_COUNTER" OR
   NOT eden_cpu6_g11_identity MATCHES "jit-startup-retry.h")
    message(FATAL_ERROR "CPU6 A64 input must be the maintained G11/N76 source")
endif()
set(eden_cpu6_static_root "${CMAKE_CURRENT_LIST_DIR}/../vendor/encore-active/ns2-runtime/cpu6/maintained/core")
foreach(eden_cpu6_file IN ITEMS
        "hle/kernel/global_scheduler_context.cpp"
        "arm/dynarmic/arm_dynarmic_32.cpp"
        "arm/dynarmic/arm_dynarmic_64.cpp")
    set(eden_cpu6_static "${eden_cpu6_static_root}/${eden_cpu6_file}")
    if(NOT EXISTS "${EDEN_CPU6_SOURCE_ROOT}/core/${eden_cpu6_file}" OR
       NOT EXISTS "${eden_cpu6_static}")
        message(FATAL_ERROR "Missing reviewed CPU6 source owner: ${eden_cpu6_file}")
    endif()
    # A64's reviewed owner is based on the selected maintained G11, not
    # the older unoptimized Dynarmic source with the same relative name.
    get_filename_component(eden_cpu6_dest_dir
        "${EDEN_CPU6_OUTPUT_ROOT}/core/${eden_cpu6_file}" DIRECTORY)
    file(MAKE_DIRECTORY "${eden_cpu6_dest_dir}")
    configure_file("${eden_cpu6_static}"
        "${EDEN_CPU6_OUTPUT_ROOT}/core/${eden_cpu6_file}" COPYONLY)
endforeach()
