# P0.2 CPU6: derive exactly three owned sources from pinned Eden.
# The six-core kernel must preempt application cores 4/5, and the host tick
# amortization must continue using four cores for Switch 1 NPDM processes.
# Kept behind the explicit research selector pending full release validation.
if(NOT DEFINED EDEN_CPU6_SOURCE_ROOT OR NOT DEFINED EDEN_CPU6_OUTPUT_ROOT OR
   NOT DEFINED EDEN_CPU6_A64_SOURCE OR NOT EXISTS "${EDEN_CPU6_A64_SOURCE}")
    message(FATAL_ERROR "CPU6 bridge requires pinned root, G11 source and destination")
endif()
# An isolated CPU6 overlay must retain the already-selected G11 profile,
# including N76 guest counter policy and the maintained PS5 JIT fast paths.
file(READ "${EDEN_CPU6_A64_SOURCE}" eden_cpu6_g11_identity)
if(NOT eden_cpu6_g11_identity MATCHES "EDEN_NS2_GUEST_COUNTER" OR
   NOT eden_cpu6_g11_identity MATCHES "jit-startup-retry.h")
    message(FATAL_ERROR "CPU6 A64 source is not the maintained G11/N76 owner")
endif()
set(eden_cpu6_expected_files
    "core/hle/kernel/global_scheduler_context.cpp"
    "core/arm/dynarmic/arm_dynarmic_32.cpp"
    "core/arm/dynarmic/arm_dynarmic_64.cpp")
foreach(eden_cpu6_file IN LISTS eden_cpu6_expected_files)
    if(NOT EXISTS "${EDEN_CPU6_SOURCE_ROOT}/${eden_cpu6_file}")
        message(FATAL_ERROR "Missing pinned CPU6 source ${eden_cpu6_file}")
    endif()
    get_filename_component(eden_cpu6_dir "${EDEN_CPU6_OUTPUT_ROOT}/${eden_cpu6_file}" DIRECTORY)
    file(MAKE_DIRECTORY "${eden_cpu6_dir}")
    if(eden_cpu6_file MATCHES "arm_dynarmic_64.cpp$")
        file(READ "${EDEN_CPU6_A64_SOURCE}" eden_cpu6_source)
    else()
        file(READ "${EDEN_CPU6_SOURCE_ROOT}/${eden_cpu6_file}" eden_cpu6_source)
    endif()
    if(eden_cpu6_file MATCHES "global_scheduler_context.cpp$")
        set(eden_cpu6_anchor [=[    static constexpr std::array<u32, Core::Hardware::NUM_CPU_CORES> per_core{
        59,
        59,
        59,
        63,
    };]=])
        set(eden_cpu6_replacement [=[    // Application cores 4 and 5 must have the same preemption priority as
    // application cores 0..2, never zero-initialized (priority 0 is highest).
    // Preserve the system/core-3 priority 63 from the Switch 1 scheduler.
    static constexpr std::array<u32, Core::Hardware::NUM_CPU_CORES> per_core{
        59, 59, 59, 63, 59, 59,
    };]=])
    else()
        set(eden_cpu6_anchor "    u64 amortized_ticks = ticks / Core::Hardware::NUM_CPU_CORES;")
        set(eden_cpu6_replacement [=[    // Switch 1 retains the original four-core tick cadence even when the
    // common native kernel exposes six physical cores. NS2 is selected by
    // its actually granted physical affinity, not by title or global flags.
    const u64 extended_cores = m_process->GetPhysicalCoreMask() & ((u64{1} << 4) | (u64{1} << 5));
    u64 amortized_ticks = ticks / (extended_cores ? Core::Hardware::NUM_CPU_CORES
                                                     : Core::Hardware::NUM_LEGACY_CPU_CORES);]=])
    endif()
    string(FIND "${eden_cpu6_source}" "${eden_cpu6_anchor}" eden_cpu6_index)
    if(eden_cpu6_index EQUAL -1)
        message(FATAL_ERROR "Pinned CPU6 owner changed, re-audit ${eden_cpu6_file}")
    endif()
    # Reject a duplicate anchor before replacing anything. Deleting all
    # matches first would incorrectly accept an additional unrelated owner.
    string(LENGTH "${eden_cpu6_anchor}" eden_cpu6_anchor_size)
    math(EXPR eden_cpu6_after_first "${eden_cpu6_index} + ${eden_cpu6_anchor_size}")
    string(SUBSTRING "${eden_cpu6_source}" ${eden_cpu6_after_first} -1 eden_cpu6_remainder)
    string(FIND "${eden_cpu6_remainder}" "${eden_cpu6_anchor}" eden_cpu6_extra)
    if(NOT eden_cpu6_extra EQUAL -1)
        message(FATAL_ERROR "Ambiguous CPU6 patch anchor ${eden_cpu6_file}")
    endif()
    string(REPLACE "${eden_cpu6_anchor}" "${eden_cpu6_replacement}"
        eden_cpu6_generated "${eden_cpu6_source}")
    file(WRITE "${EDEN_CPU6_OUTPUT_ROOT}/${eden_cpu6_file}" "${eden_cpu6_generated}")
endforeach()
