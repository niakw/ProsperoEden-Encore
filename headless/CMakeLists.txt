option(EDEN_PS5_VULKAN "Build the native Vulkan renderer alongside OpenGL" OFF)
set(EDEN_VULKAN_DRIVER "CUSTOM" CACHE STRING "Native Vulkan driver: CUSTOM or RADV")
set_property(CACHE EDEN_VULKAN_DRIVER PROPERTY STRINGS CUSTOM RADV)
if(NOT EDEN_VULKAN_DRIVER MATCHES "^(CUSTOM|RADV)$")
    message(FATAL_ERROR "EDEN_VULKAN_DRIVER must be CUSTOM or RADV")
endif()
set(PORT_ROOT "${CMAKE_CURRENT_LIST_DIR}/..")
set(PORT_BUILD_DIR "${CMAKE_BINARY_DIR}/headless")

# N1: one reviewed NPDM owner is shared by ALL native PS5 configurations.
# 2048-bit (NS1) and 3072-bit (NS2) ACID detection is based on guest input,
# not a user-visible emulator mode; never activate GPU/HOS research branches
# merely because the dual parser is selected.
set(EDEN_REVIEWED_DUAL_NPDM OFF)
if(PS5_NATIVE)
    set(EDEN_REVIEWED_DUAL_NPDM ON)
endif()
if(EDEN_REVIEWED_DUAL_NPDM)
    set(EDEN_NS2_METADATA_OVERLAY "${PORT_ROOT}/vendor/encore-active/ns2-runtime/metadata")
    set(EDEN_NS2_CORE_HELPERS "${PORT_ROOT}/vendor/encore-active/ns2-helpers/include")
    if(NOT EXISTS "${EDEN_NS2_METADATA_OVERLAY}/core/file_sys/program_metadata.cpp"
       OR NOT EXISTS "${EDEN_NS2_CORE_HELPERS}/core/file_sys/program_metadata.h")
        message(FATAL_ERROR "Missing unified NS1/NS2 NPDM source/header")
    endif()
    get_target_property(eden_ns2_metadata_core_sources core SOURCES)
    list(FIND eden_ns2_metadata_core_sources
         "file_sys/program_metadata.cpp" eden_ns2_metadata_idx)
    if(eden_ns2_metadata_idx EQUAL -1)
        message(FATAL_ERROR "Eden NPDM owner changed: re-audit NS2 overlay selection")
    endif()
    list(REMOVE_ITEM eden_ns2_metadata_core_sources "file_sys/program_metadata.cpp")
    list(APPEND eden_ns2_metadata_core_sources
         "${EDEN_NS2_METADATA_OVERLAY}/core/file_sys/program_metadata.cpp")
    set_property(TARGET core PROPERTY SOURCES "${eden_ns2_metadata_core_sources}")
    target_include_directories(core BEFORE PUBLIC
        "${EDEN_NS2_CORE_HELPERS}" "${EDEN_NS2_METADATA_OVERLAY}")
endif()


# Scalar-memory source fragments still consumed by modules trigger configure.
set(EDEN_SCALAR_INPUT_DIR
    "${PORT_ROOT}/vendor/encore-active/eden-core/dynarmic/scalar")
set(EDEN_SCALAR_INPUTS
    "${EDEN_SCALAR_INPUT_DIR}/scalar-memory-read.inc"
    "${EDEN_SCALAR_INPUT_DIR}/scalar-memory-write.inc")
foreach(EDEN_SCALAR_SOURCE IN LISTS EDEN_SCALAR_INPUTS)
    if(NOT EXISTS "${EDEN_SCALAR_SOURCE}")
        message(FATAL_ERROR "Missing Encore-maintained scalar source ${EDEN_SCALAR_SOURCE}")
    endif()
endforeach()
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS ${EDEN_SCALAR_INPUTS})
# Stability defaults: use Dynarmic's ordinary per-core JIT in production. The cross-core
# JitGroup and bounded successor compile batching are Encore experiments and stay compile-time
# off unless a development build explicitly opts in.
# Exactly one native PS5 JIT profile: the code-address contract and sparse
# backing are selected by PS5_NATIVE, never by a dev/release toggle.
# Register-allocator bookkeeping visits only the host locations in use (compile time).
include("${CMAKE_CURRENT_LIST_DIR}/dynarmic/reg_alloc.cmake")
file(MAKE_DIRECTORY "${PORT_BUILD_DIR}")
# SlotVector's throwing-constructor repair has one tracked implementation.
# Use a narrow header-only root to avoid shadowing unrelated pinned includes.
set(EDEN_MAINTAINED_SLOT_VECTOR_ROOT
    "${PORT_ROOT}/vendor/encore-active/eden-core/overrides/slot-vector")
if(NOT EXISTS "${EDEN_MAINTAINED_SLOT_VECTOR_ROOT}/common/slot_vector.h")
    message(FATAL_ERROR "Missing maintained native SlotVector header")
endif()
file(REMOVE "${PORT_BUILD_DIR}/include/common/slot_vector.h")
target_include_directories(common BEFORE PUBLIC "${EDEN_MAINTAINED_SLOT_VECTOR_ROOT}")
target_include_directories(video_core BEFORE PRIVATE "${EDEN_MAINTAINED_SLOT_VECTOR_ROOT}")
file(GLOB overlay_inputs CONFIGURE_DEPENDS "${CMAKE_CURRENT_LIST_DIR}/*.inc")
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS ${overlay_inputs})
function(write_derived path content)
    # Preserve timestamps when an overlay is unchanged; otherwise every
    # configure needlessly recompiles hundreds of dependent source files.
    file(WRITE "${path}.in" "${content}")
    configure_file("${path}.in" "${path}" COPYONLY)
endfunction()
# R437: the shipping BufferCache backport is adapted in a single maintained header.
# This only copies tracked bytes into the native include overlay.
if(PS5_NATIVE)
    set(EDEN_MAINTAINED_BUFFER_PAGES
        "${PORT_ROOT}/vendor/encore-active/eden-core/src/video_core/buffer_cache/buffer_cache.h")
    if(NOT EXISTS "${EDEN_MAINTAINED_BUFFER_PAGES}")
        message(FATAL_ERROR "Missing maintained R437 BufferCache header")
    endif()
    file(MAKE_DIRECTORY "${PORT_BUILD_DIR}/buffer-pages/video_core/buffer_cache")
    configure_file("${EDEN_MAINTAINED_BUFFER_PAGES}"
        "${PORT_BUILD_DIR}/buffer-pages/video_core/buffer_cache/buffer_cache.h" COPYONLY)
    # The reviewed R437 body adds an explicit GPU-write tick policy. Select
    # its matching template declarations, not the pinned pre-R437 ABI.
    set(EDEN_MAINTAINED_BUFFER_BASE
        "${PORT_ROOT}/vendor/encore-active/eden-core/src/video_core/buffer_cache/buffer_cache_base.h")
    if(NOT EXISTS "${EDEN_MAINTAINED_BUFFER_BASE}")
        message(FATAL_ERROR "Missing matching native R437 BufferCache base declarations")
    endif()
    configure_file("${EDEN_MAINTAINED_BUFFER_BASE}"
        "${PORT_BUILD_DIR}/buffer-pages/video_core/buffer_cache/buffer_cache_base.h" COPYONLY)
    target_include_directories(video_core BEFORE PRIVATE "${PORT_BUILD_DIR}/buffer-pages" "${EDEN_PORT_DIR}")
endif()
# The texture-cache small-vector Boost version dependency is a complete
# tracked header under vendor/encore-active, not a configure-time replacement.
# Its only modification to the original is #include <boost/version.hpp>.
set(EDEN_SMALL_VECTOR_ROOT "${PORT_ROOT}/vendor/encore-active/eden-core/src")
if(NOT EXISTS "${EDEN_SMALL_VECTOR_ROOT}/video_core/texture_cache/util.h")
    message(FATAL_ERROR "Missing maintained texture-cache type header")
endif()
target_include_directories(video_core BEFORE PRIVATE "${EDEN_SMALL_VECTOR_ROOT}")
# R428: upstream d7f2764 — repeated guest faults must not force a
# synchronous PS5 storage flush for every error line. Keep regular buffer
# flushes and the explicit Flush() API; only coalesce bursts to 100 ms.
# Never edit the immutable Eden logging.cpp source.
set(EDEN_MAINTAINED_LOGGING "${PORT_ROOT}/vendor/encore-active/eden-core/src/common/logging.cpp")
if(NOT EXISTS "${EDEN_MAINTAINED_LOGGING}")
    message(FATAL_ERROR "Missing maintained bounded logging source")
endif()
get_target_property(eden_common_sources common SOURCES)
list(FIND eden_common_sources "logging.cpp" eden_pinned_logging_idx)
if(eden_pinned_logging_idx EQUAL -1)
    message(FATAL_ERROR "Pinned logging source moved; requalify maintained overlay")
endif()
list(REMOVE_ITEM eden_common_sources "logging.cpp")
list(APPEND eden_common_sources "${EDEN_MAINTAINED_LOGGING}")
set_property(TARGET common PROPERTY SOURCES "${eden_common_sources}")
# Maintained HLE source selection lives with its code, not in this launcher.
option(EDEN_BLOCKING_GUEST_CONTEXT_LOCKS
    "Use the paired upstream guest scheduler lock fixes" ON)
include("${PORT_ROOT}/vendor/encore-active/eden-threading/native-hle-overrides.cmake")

# The full JIT assertion header is versioned under vendor/encore-active.
# It is byte-equivalent to the previous pinned header + guarded override;
# only the Dynarmic target sees these exceptional-path assertion semantics.
set(EDEN_JIT_ASSERT_ROOT "${PORT_ROOT}/vendor/encore-active/eden-core/src")
if(NOT EXISTS "${EDEN_JIT_ASSERT_ROOT}/common/assert.h")
    message(FATAL_ERROR "Missing maintained JIT assertions")
endif()
target_include_directories(dynarmic BEFORE PRIVATE "${EDEN_JIT_ASSERT_ROOT}")
# Let the existing compiler inline across the JIT's translation units. Keep the
# rest of the native application on its qualified non-LTO build path.
target_compile_options(dynarmic PRIVATE -flto=thin)
if(PS5_NATIVE)
    # The PS5 CPU is Zen2. Keep the established GPU ThinLTO policy, and tune
    # host scheduling without widening the core/common/fiber instruction set.
    target_compile_options(video_core PRIVATE -flto=thin -march=znver2)
    foreach(eden_cpu_target common core dynarmic)
        target_compile_options(${eden_cpu_target} PRIVATE -mtune=znver2)
    endforeach()
    # DSP and shader translation contain substantial vector/integer work.
    # Enable the CPU's native ISA here while keeping separate multiply/add
    # rounding; this does not enable fast-math or change guest JIT features.
    foreach(eden_simd_target audio_core shader_recompiler)
        target_compile_options(${eden_simd_target} PRIVATE -march=znver2 -ffp-contract=off)
    endforeach()
endif()
if(NOT PS5_NATIVE)
    target_link_options(dynarmic INTERFACE -fuse-ld=lld-18)
endif()

# Clang 18 does not accept the upstream GCC TLS-dialect flag. Use the same
# compiler-rt emulated TLS configuration already qualified by G6 on PS5.
# Linux must match its system libstdc++'s native TLS ABI.
foreach(eden_target common core audio_core video_core hid_core network input_common frontend_common shader_recompiler gpu_logging dynarmic)
    if(TARGET ${eden_target})
        get_target_property(options ${eden_target} COMPILE_OPTIONS)
        if(options)
            list(FILTER options EXCLUDE REGEX "mtls-dialect")
            set_property(TARGET ${eden_target} PROPERTY COMPILE_OPTIONS "${options}")
        endif()
        if(PS5_NATIVE)
            target_compile_options(${eden_target} PRIVATE -femulated-tls)
        endif()
    endif()
endforeach()
if(PS5_NATIVE)
    set(COMPILER_RT "${PORT_ROOT}/.deps/compiler-rt-18.1.8")
    # Versioned compiler-rt native TLS runtime; no CMake source mutation.
    set(EDEN_MAINTAINED_EMUTLS
        "${PORT_ROOT}/vendor/encore-active/compiler-rt/emutls.c")
    if(NOT EXISTS "${EDEN_MAINTAINED_EMUTLS}")
        message(FATAL_ERROR "Missing maintained emulated TLS implementation")
    endif()
    target_sources(common PRIVATE "${EDEN_MAINTAINED_EMUTLS}" "${COMPILER_RT}/cpu_model_x86.c")
    target_include_directories(common PRIVATE "${COMPILER_RT}")
    # RADV's AMD addrlib uses __builtin_cpu_supports(), whose x86 runtime
    # state (__cpu_model/__cpu_features2) lives in compiler-rt. Linux CI gets
    # that from Clang's builtins archive; macOS cross-builds provide the same
    # pinned LLVM 18.1.8 implementation directly so the PS5 binary is identical
    # in semantics and does not depend on a host-Linux runtime archive.
    set_source_files_properties("${COMPILER_RT}/cpu_model_x86.c" PROPERTIES
        COMPILE_OPTIONS "-Wno-unused-function;-Wno-missing-declarations")

    # Switch 22.0+ may store compressed NSO segments as ZBIC, a Nintendo
    # zstd variant. The pinned Eden source predates upstream #4482.
    set(ZBIC_DIR "${PORT_ROOT}/.deps/zbic-11b08f27/src")
    if(NOT EXISTS "${ZBIC_DIR}/zstd.c")
        message(FATAL_ERROR "ZBIC source is missing (${ZBIC_DIR}); run make deps")
    endif()
    target_sources(common PRIVATE "${EDEN_PORT_DIR}/zbic_compression.cpp")
    target_include_directories(common PRIVATE "${ZBIC_DIR}")
    set_source_files_properties("${EDEN_PORT_DIR}/zbic_compression.cpp" PROPERTIES
        COMPILE_OPTIONS "-Wno-unused-function;-Wno-missing-declarations;-Wno-shadow")
    target_include_directories(core PRIVATE "${EDEN_PORT_DIR}")
    target_include_directories(video_core PRIVATE "${EDEN_PORT_DIR}")
endif()
# Use the already-qualified no-arena allocation contract in the full core.
get_target_property(common_sources common SOURCES)
list(REMOVE_ITEM common_sources host_memory.cpp sparse_large_vector.cpp)
set_property(TARGET common PROPERTY SOURCES "${common_sources}")
target_sources(common PRIVATE "${PORT_ROOT}/src/host_memory.cpp" "${PORT_ROOT}/src/memory_pages.cpp")
# Isolated R457 NS2 12 GiB virtual / bounded 2 MiB physical resident owner.
# Real native syscalls and guest PTE precommit; NOT included by default.
# Do not turn this on in production until GPU coherency and PS5 boot pass.
set(EDEN_NS2_SPARSE_BACKING OFF)
if(PS5_NATIVE AND EDEN_REVIEWED_DUAL_NPDM)
    set(EDEN_NS2_SPARSE_BACKING ON)
endif()
if(EDEN_NS2_SPARSE_BACKING)
    if(NOT PS5_NATIVE)
        message(FATAL_ERROR "NS2 sparse PS5 direct-memory owner requires PS5_NATIVE")
    endif()
    target_sources(common PRIVATE "${PORT_ROOT}/src/ns2_sparse_guest.cpp")
    target_include_directories(common PRIVATE "${PORT_ROOT}/headless")
    target_compile_definitions(common PRIVATE EDEN_NS2_SPARSE_BACKING=1)
    target_compile_definitions(core PRIVATE EDEN_NS2_SPARSE_BACKING=1)
endif()
# Sparse JIT trim helpers are shared with Dynarmic. The native release
# uses the one sparse JIT allocator path; these are compile-time helpers.
target_include_directories(common PRIVATE "${EDEN_PORT_DIR}")

# Complete native sparse vector header is owned by Encore, not constructed
# at configure time. Preserve the prior include-overlay selection order.
set(EDEN_MAINTAINED_SPARSE_VECTOR
    "${PORT_ROOT}/vendor/encore-active/eden-core/src/common/sparse_large_vector.h")
if(NOT EXISTS "${EDEN_MAINTAINED_SPARSE_VECTOR}")
    message(FATAL_ERROR "Missing maintained sparse vector header")
endif()
file(MAKE_DIRECTORY "${PORT_BUILD_DIR}/sparse/common")
configure_file("${EDEN_MAINTAINED_SPARSE_VECTOR}"
    "${PORT_BUILD_DIR}/sparse/common/sparse_large_vector.h" COPYONLY)

# The fiber transition fix is a complete, versioned C++ translation unit.
# It was previously regenerated by CMake string(REPLACE) at each configure.
# The pinned original stays immutable in vendor/sources for audit/provenance.
set(EDEN_FIBER_ACTIVE "${PORT_ROOT}/vendor/encore-active/eden-core/src/common/fiber.cpp")
if(NOT EXISTS "${EDEN_FIBER_ACTIVE}")
    message(FATAL_ERROR "Missing tracked Encore fiber source")
endif()
get_target_property(common_sources common SOURCES)
list(REMOVE_ITEM common_sources fiber.cpp)
list(APPEND common_sources "${EDEN_FIBER_ACTIVE}")
set_property(TARGET common PROPERTY SOURCES "${common_sources}")

get_target_property(jit_sources dynarmic SOURCES)
list(FILTER jit_sources EXCLUDE REGEX "exception_handler_posix\\.cpp$")
set_property(TARGET dynarmic PROPERTY SOURCES "${jit_sources}")
# A32 fastmem: src/host_memory.cpp aliases 32-bit guest memory into a 4 GiB window at
# the PS5's 16 KiB page size; this handler sends faulting JIT accesses to their
# page-table fallback. Without it the generic handler keeps fastmem off.
option(EDEN_A32_FASTMEM "A32 fastmem window with JIT fault recovery" ON)
if(EDEN_A32_FASTMEM AND (PS5_NATIVE OR CMAKE_SYSTEM_NAME STREQUAL "Linux"))
    target_sources(dynarmic PRIVATE "${EDEN_PORT_DIR}/fastmem_handler.cpp")
else()
    target_sources(dynarmic PRIVATE "${PROJECT_SOURCE_DIR}/src/dynarmic/src/dynarmic/backend/exception_handler_generic.cpp")
endif()

  # Page-local W^X: constants stay RW/NX; old code stays RX unless patched.
  # Apply the same derivative to Linux host correctness/pressure tests.
if(PS5_NATIVE OR CMAKE_SYSTEM_NAME STREQUAL "Linux")
# Complete BlockOfCode sources are maintained in Encore, staged as byte-exact copies.
include("${EDEN_PORT_DIR}/jit-alias.cmake")
set(EDEN_MAINTAINED_BOC_ROOT "${PORT_ROOT}/vendor/encore-active/eden-core/src/dynarmic/backend/x64")
set(EDEN_BOC_HEADER "${EDEN_MAINTAINED_BOC_ROOT}/block_of_code.h")
if(PS5_NATIVE)
    set(EDEN_BOC_UNIT "${EDEN_MAINTAINED_BOC_ROOT}/block_of_code_native.cpp")
else()
    set(EDEN_BOC_UNIT "${EDEN_MAINTAINED_BOC_ROOT}/block_of_code_host.cpp")
endif()
foreach(EDEN_BOC_INPUT IN ITEMS "${EDEN_BOC_HEADER}" "${EDEN_BOC_UNIT}")
    if(NOT EXISTS "${EDEN_BOC_INPUT}")
        message(FATAL_ERROR "Missing maintained BlockOfCode input ${EDEN_BOC_INPUT}")
    endif()
endforeach()
configure_file("${EDEN_BOC_HEADER}"
    "${PORT_BUILD_DIR}/include/dynarmic/backend/x64/block_of_code.h" COPYONLY)
configure_file("${EDEN_BOC_UNIT}" "${PORT_BUILD_DIR}/block_of_code.cpp" COPYONLY)
target_include_directories(dynarmic BEFORE PUBLIC "${PORT_BUILD_DIR}/include")
target_include_directories(dynarmic PRIVATE "${EDEN_PORT_DIR}")
get_target_property(jit_sources dynarmic SOURCES)
list(FILTER jit_sources EXCLUDE REGEX "(^|/)block_of_code\\.cpp$")
set_property(TARGET dynarmic PROPERTY SOURCES "${jit_sources}")
target_sources(dynarmic PRIVATE "${PORT_BUILD_DIR}/block_of_code.cpp")
if(PS5_NATIVE)
    set_property(SOURCE "${PORT_BUILD_DIR}/block_of_code.cpp"
        TARGET_DIRECTORY dynarmic APPEND PROPERTY COMPILE_DEFINITIONS "PS5_NATIVE=1")
endif()
# Complete A32/A64 emitters and matched headers are maintained under encore-active.
# CMake only selects/copies the source, preserving the exact test build paths.
set(EDEN_MAINTAINED_EMIT_ROOT "${PORT_ROOT}/vendor/encore-active/eden-core/src/dynarmic/backend/x64")
set(EDEN_A64_EMITTER_UNIT "${EDEN_MAINTAINED_EMIT_ROOT}/a64_emit_x64_standard.cpp")
set(EDEN_A64_EMITTER_HEADER "${EDEN_MAINTAINED_EMIT_ROOT}/a64_emit_x64_standard.h")
foreach(EDEN_EMITTER_SOURCE IN ITEMS
        "${EDEN_MAINTAINED_EMIT_ROOT}/a32_emit_x64.cpp"
        "${EDEN_A64_EMITTER_UNIT}" "${EDEN_A64_EMITTER_HEADER}")
    if(NOT EXISTS "${EDEN_EMITTER_SOURCE}")
        message(FATAL_ERROR "Missing Encore-maintained emitter ${EDEN_EMITTER_SOURCE}")
    endif()
endforeach()
configure_file("${EDEN_A64_EMITTER_HEADER}"
    "${PORT_BUILD_DIR}/include/dynarmic/backend/x64/a64_emit_x64.h" COPYONLY)
foreach(bits 32 64)
    if(bits EQUAL 64)
        set(EDEN_EMITTER_UNIT "${EDEN_A64_EMITTER_UNIT}")
    else()
        set(EDEN_EMITTER_UNIT "${EDEN_MAINTAINED_EMIT_ROOT}/a32_emit_x64.cpp")
    endif()
    configure_file("${EDEN_EMITTER_UNIT}" "${PORT_BUILD_DIR}/a${bits}_emit_x64.cpp" COPYONLY)
    get_target_property(jit_sources dynarmic SOURCES)
    list(FILTER jit_sources EXCLUDE REGEX "(^|/)a${bits}_emit_x64\\.cpp$")
    set_property(TARGET dynarmic PROPERTY SOURCES "${jit_sources}")
    target_sources(dynarmic PRIVATE "${PORT_BUILD_DIR}/a${bits}_emit_x64.cpp")
endforeach()

endif()

# Compiled guest block ranges by 4 KiB page. Both the header and its
# translation unit have exactly one maintained owner in encore-active.
# This remains selected regardless of EDEN_SHARED_JIT.
set(EDEN_MAINTAINED_BLOCK_RANGE_DIR
    "${PORT_ROOT}/vendor/encore-active/eden-core/src/dynarmic/backend")
foreach(EDEN_BLOCK_RANGE_FILE IN ITEMS block_range_information.cpp block_range_information.h)
    if(NOT EXISTS "${EDEN_MAINTAINED_BLOCK_RANGE_DIR}/${EDEN_BLOCK_RANGE_FILE}")
        message(FATAL_ERROR "Missing maintained Dynarmic block-range ${EDEN_BLOCK_RANGE_FILE}")
    endif()
endforeach()
configure_file(
    "${EDEN_MAINTAINED_BLOCK_RANGE_DIR}/block_range_information.h"
    "${PORT_BUILD_DIR}/include/dynarmic/backend/block_range_information.h" COPYONLY)
get_target_property(range_sources dynarmic SOURCES)
list(FILTER range_sources EXCLUDE REGEX "(^|/)block_range_information\\.cpp$")
set_property(TARGET dynarmic PROPERTY SOURCES "${range_sources}")
target_sources(dynarmic PRIVATE
    "${EDEN_MAINTAINED_BLOCK_RANGE_DIR}/block_range_information.cpp")
# Keep the native header's original include shadowing and target-wide layout ABI.
target_compile_definitions(dynarmic PRIVATE EDEN_BLOCK_RANGE_PAGES=1)
if(PS5_NATIVE OR CMAKE_SYSTEM_NAME STREQUAL "Linux")
    eden_reg_alloc_sources()
endif()

# Complete x64 patch-lookup units; native omits perf-map formatting entirely.
set(EDEN_MAINTAINED_EMIT_X64_ROOT "${PORT_ROOT}/vendor/encore-active/eden-core/src/dynarmic/backend/x64")
if(PS5_NATIVE)
    set(EDEN_EMIT_X64_SOURCE "${EDEN_MAINTAINED_EMIT_X64_ROOT}/emit_x64_native.cpp")
else()
    set(EDEN_EMIT_X64_SOURCE "${EDEN_MAINTAINED_EMIT_X64_ROOT}/emit_x64_host.cpp")
endif()
if(NOT EXISTS "${EDEN_EMIT_X64_SOURCE}")
    message(FATAL_ERROR "Missing maintained common x64 emitter ${EDEN_EMIT_X64_SOURCE}")
endif()
configure_file("${EDEN_EMIT_X64_SOURCE}" "${PORT_BUILD_DIR}/emit_x64.cpp" COPYONLY)
get_target_property(jit_sources dynarmic SOURCES)
list(FILTER jit_sources EXCLUDE REGEX "(^|/)emit_x64\\.cpp$")
set_property(TARGET dynarmic PROPERTY SOURCES "${jit_sources}")
target_sources(dynarmic PRIVATE "${PORT_BUILD_DIR}/emit_x64.cpp")

# Dynarmic scalar translation and optimizer are tracked complete sources.
# impl/impl.cpp is included once by its adjacent translator.
set(EDEN_MAINTAINED_SCALAR_IMPL
    "${PORT_ROOT}/vendor/encore-active/eden-core/src/dynarmic/frontend/A64/translate/impl/impl.cpp")
set(EDEN_MAINTAINED_SCALAR_TRANSLATOR
    "${PORT_ROOT}/vendor/encore-active/eden-core/src/dynarmic/frontend/A64/translate/a64_translate.cpp")
set(EDEN_MAINTAINED_SCALAR_OPT
    "${PORT_ROOT}/vendor/encore-active/eden-core/src/dynarmic/ir/opt_passes.cpp")
foreach(EDEN_MAINTAINED_SCALAR_SOURCE IN ITEMS
        "${EDEN_MAINTAINED_SCALAR_IMPL}"
        "${EDEN_MAINTAINED_SCALAR_TRANSLATOR}"
        "${EDEN_MAINTAINED_SCALAR_OPT}")
    if(NOT EXISTS "${EDEN_MAINTAINED_SCALAR_SOURCE}")
        message(FATAL_ERROR "Missing maintained Dynarmic scalar file ${EDEN_MAINTAINED_SCALAR_SOURCE}")
    endif()
endforeach()
get_target_property(jit_sources dynarmic SOURCES)
list(FILTER jit_sources EXCLUDE REGEX "(^|/)a64_translate\\.cpp$")
list(FILTER jit_sources EXCLUDE REGEX "(^|/)opt_passes\\.cpp$")
set_property(TARGET dynarmic PROPERTY SOURCES "${jit_sources}")
target_sources(dynarmic PRIVATE
    "${EDEN_MAINTAINED_SCALAR_TRANSLATOR}"
    "${EDEN_MAINTAINED_SCALAR_OPT}")

# G07: single Encore-owned address decoder header, with C++ guards for
# checked A32 and the process-wide shared-JIT reservation policy.
set(EDEN_MAINTAINED_MEMORY_HEADER
    "${PORT_ROOT}/vendor/encore-active/eden-core/src/dynarmic/backend/x64/emit_x64_memory.h")
if(NOT EXISTS "${EDEN_MAINTAINED_MEMORY_HEADER}")
    message(FATAL_ERROR "Missing maintained Dynarmic memory decoder header")
endif()
configure_file("${EDEN_MAINTAINED_MEMORY_HEADER}"
    "${PORT_BUILD_DIR}/include/dynarmic/backend/x64/emit_x64_memory.h" COPYONLY)
if(EDEN_A32_FASTMEM)
    target_compile_definitions(dynarmic PRIVATE EDEN_A32_CHECKED_FASTMEM=1)
endif()

# G06: complete C++ include bodies; checked A32 and standard mode are
# explicit Encore-owned variants. Shared JIT uses compile-time guards.
set(EDEN_MAINTAINED_MEMORY_IMPL_ROOT
    "${PORT_ROOT}/vendor/encore-active/eden-core/src/dynarmic/backend/x64")
if(EDEN_A32_FASTMEM)
    set(EDEN_MAINTAINED_MEMORY_IMPL
        "${EDEN_MAINTAINED_MEMORY_IMPL_ROOT}/emit_x64_memory_checked.cpp.inc")
else()
    set(EDEN_MAINTAINED_MEMORY_IMPL
        "${EDEN_MAINTAINED_MEMORY_IMPL_ROOT}/emit_x64_memory_standard.cpp.inc")
endif()
if(NOT EXISTS "${EDEN_MAINTAINED_MEMORY_IMPL}")
    message(FATAL_ERROR "Missing maintained Dynarmic memory method unit ${EDEN_MAINTAINED_MEMORY_IMPL}")
endif()
configure_file("${EDEN_MAINTAINED_MEMORY_IMPL}"
    "${PORT_BUILD_DIR}/include/dynarmic/backend/x64/emit_x64_memory.cpp.inc" COPYONLY)
# New include overlays do not invalidate objects whose depfile still names
# upstream headers. Derive both translation units so the first build cannot
# silently keep old objects; subsequent depfiles track the overlay normally.
# Memory emitter units are complete Encore sources. Shared mode uses the
# existing target-wide EDEN_SHARED_JIT_LAYOUT compile definition, so
# its three monitor/configuration macros live in the source units.
set(EDEN_MAINTAINED_MEMORY_UNIT_DIR
    "${PORT_ROOT}/vendor/encore-active/eden-core/src/dynarmic/backend/x64")
get_target_property(jit_sources dynarmic SOURCES)
foreach(bits 32 64)
    set(memory_unit "a${bits}_emit_x64_memory.cpp")
    set(EDEN_MAINTAINED_MEMORY_UNIT
        "${EDEN_MAINTAINED_MEMORY_UNIT_DIR}/${memory_unit}")
    if(NOT EXISTS "${EDEN_MAINTAINED_MEMORY_UNIT}")
        message(FATAL_ERROR "Missing maintained memory emitter ${memory_unit}")
    endif()
    configure_file("${EDEN_MAINTAINED_MEMORY_UNIT}"
        "${PORT_BUILD_DIR}/${memory_unit}" COPYONLY)
    list(FILTER jit_sources EXCLUDE REGEX "(^|/)a${bits}_emit_x64_memory\\.cpp$")
    list(APPEND jit_sources "${PORT_BUILD_DIR}/${memory_unit}")
endforeach()
set_property(TARGET dynarmic PROPERTY SOURCES "${jit_sources}")

if(PS5_NATIVE)
    # The native spin-lock adjustment is a complete Encore source.
    set(EDEN_MAINTAINED_SPIN_LOCK
        "${PORT_ROOT}/vendor/encore-active/eden-core/src/dynarmic/common/spin_lock_x64.cpp")
    if(NOT EXISTS "${EDEN_MAINTAINED_SPIN_LOCK}")
        message(FATAL_ERROR "Missing maintained native Dynarmic spin lock")
    endif()
    get_target_property(jit_sources dynarmic SOURCES)
    list(FILTER jit_sources EXCLUDE REGEX "(^|/)spin_lock_x64\\.cpp$")
    set_property(TARGET dynarmic PROPERTY SOURCES "${jit_sources}")
    target_sources(dynarmic PRIVATE "${EDEN_MAINTAINED_SPIN_LOCK}")
endif()

# A64 runtime variants are complete maintained C++ units.
# Compile-batch and DEV are source-defined gates rather than textual CMake rewrites.
set(EDEN_A64_INTERFACE_ROOT "${PORT_ROOT}/vendor/encore-active/eden-core/src/dynarmic/backend/x64")
set(EDEN_A64_INTERFACE_UNIT "${EDEN_A64_INTERFACE_ROOT}/a64_interface_standard.cpp")
if(NOT EXISTS "${EDEN_A64_INTERFACE_UNIT}")
    message(FATAL_ERROR "Missing maintained A64 interface ${EDEN_A64_INTERFACE_UNIT}")
endif()
configure_file("${EDEN_A64_INTERFACE_UNIT}" "${PORT_BUILD_DIR}/a64_interface.cpp" COPYONLY)
get_target_property(jit_sources dynarmic SOURCES)
list(FILTER jit_sources EXCLUDE REGEX "(^|/)a64_interface\\.cpp$")
set_property(TARGET dynarmic PROPERTY SOURCES "${jit_sources}")
target_sources(dynarmic PRIVATE "${PORT_BUILD_DIR}/a64_interface.cpp")
if(PS5_NATIVE)
    set_property(SOURCE "${PORT_BUILD_DIR}/a64_interface.cpp"
        TARGET_DIRECTORY dynarmic APPEND PROPERTY COMPILE_DEFINITIONS "PS5_NATIVE=1")
endif()

# Complete A32 native interface is Encore-owned; host uses the pinned original.
if(PS5_NATIVE)
    set(EDEN_MAINTAINED_A32_INTERFACE
        "${PORT_ROOT}/vendor/encore-active/eden-core/src/dynarmic/backend/x64/a32_interface_native.cpp")
    if(NOT EXISTS "${EDEN_MAINTAINED_A32_INTERFACE}")
        message(FATAL_ERROR "Missing Encore-maintained native A32 JIT interface")
    endif()
    configure_file("${EDEN_MAINTAINED_A32_INTERFACE}"
        "${PORT_BUILD_DIR}/a32_interface.cpp" COPYONLY)
    get_target_property(jit_sources dynarmic SOURCES)
    list(FILTER jit_sources EXCLUDE REGEX "(^|/)a32_interface\\.cpp$")
    set_property(TARGET dynarmic PROPERTY SOURCES "${jit_sources}")
    target_sources(dynarmic PRIVATE "${PORT_BUILD_DIR}/a32_interface.cpp")
endif()

# Dynarmic keeps its Xbyak dependency PRIVATE; the PS5-specific core
# wrapper also needs Xbyak::Error for typed allocator-only startup retries.
# Expose the imported header-only target to core without changing Dynarmic's
# public dependency surface or pulling a new Xbyak version.
if(PS5_NATIVE)
    target_link_libraries(core PRIVATE xbyak::xbyak)
endif()
# Carry both qualified JIT configurations into the maintained core wrappers.
# Select complete Encore source owners; never generate JIT C++ at configure time.
get_target_property(core_sources core SOURCES)
# G11 + X06: one complete Encore JIT translation unit per guest ISA.
# G11's historical C++ transformations are retained as host-test fixtures only.
set(EDEN_G11_INLINE_VALUE 0)
set(EDEN_G11_ROOT "${PORT_ROOT}/vendor/encore-active/eden-core/src/core/arm/dynarmic/g11")
if(PS5_NATIVE)
    set(EDEN_G11_PLATFORM native)
else()
    set(EDEN_G11_PLATFORM host)
endif()
set(EDEN_G11_PROFILE normal)
get_target_property(core_sources core SOURCES)
foreach(bits 32 64)
    set(relative "arm/dynarmic/arm_dynarmic_${bits}.cpp")
    set(EDEN_G11_SOURCE
        "${EDEN_G11_ROOT}/arm_dynarmic_${bits}_${EDEN_G11_PLATFORM}_${EDEN_G11_PROFILE}.cpp")
    if(NOT EXISTS "${EDEN_G11_SOURCE}")
        message(FATAL_ERROR "Missing maintained G11 A${bits} guest JIT unit")
    endif()
    list(FIND core_sources "${relative}" eden_g11_original_owner)
    if(eden_g11_original_owner EQUAL -1)
        message(FATAL_ERROR "G11 original A${bits} source moved; requalify selector")
    endif()
    list(REMOVE_ITEM core_sources "${relative}")
    list(APPEND core_sources "${EDEN_G11_SOURCE}")
    # The experimental opt-in is scoped to this translation unit only.
    set_source_files_properties("${EDEN_G11_SOURCE}" TARGET_DIRECTORY core PROPERTIES
        COMPILE_DEFINITIONS "EDEN_INLINE_EXCLUSIVES=${EDEN_G11_INLINE_VALUE}")
endforeach()
# G12: complete maintained PhysicalCore sources. No build-time C++ patches.
set(EDEN_PHYSICAL_CORE_DIR "${PORT_ROOT}/vendor/encore-active/eden-core/src/core/hle/kernel")
set(EDEN_PHYSICAL_CORE_SOURCE "${EDEN_PHYSICAL_CORE_DIR}/physical_core_standard.cpp")
if(NOT EXISTS "${EDEN_PHYSICAL_CORE_SOURCE}")
    message(FATAL_ERROR "Missing maintained PhysicalCore source ${EDEN_PHYSICAL_CORE_SOURCE}")
endif()
configure_file("${EDEN_PHYSICAL_CORE_SOURCE}" "${PORT_BUILD_DIR}/physical_core.cpp" COPYONLY)
list(REMOVE_ITEM core_sources "hle/kernel/physical_core.cpp")
list(APPEND core_sources "${PORT_BUILD_DIR}/physical_core.cpp")
# Guest scheduler spin lock is maintained as a complete qualified source, not a CMake rewrite.
set(eden_kernel_spin "${PORT_ROOT}/vendor/encore-active/eden-core/src/core/hle/kernel/k_spin_lock.cpp")
if(NOT EXISTS "${eden_kernel_spin}")
    message(FATAL_ERROR "Missing maintained guest scheduler lock source")
endif()
target_include_directories(core PRIVATE "${EDEN_PORT_DIR}")
list(REMOVE_ITEM core_sources "hle/kernel/k_spin_lock.cpp")
list(APPEND core_sources "${eden_kernel_spin}")
# One source owns queue correctness and tracing in the native application.
# Its profiling counters do not change the selected source graph.
set(EDEN_MAINTAINED_PROFILE_DEQUEUE
    "${PORT_ROOT}/vendor/encore-active/eden-core/src/core/hle/service/nvnflinger/buffer_queue_producer.cpp")
if(NOT EXISTS "${EDEN_MAINTAINED_PROFILE_DEQUEUE}")
    message(FATAL_ERROR "Missing maintained buffer queue producer source")
endif()
list(REMOVE_ITEM core_sources "hle/service/nvnflinger/buffer_queue_producer.cpp")
list(APPEND core_sources "${EDEN_MAINTAINED_PROFILE_DEQUEUE}")
# Consumer queue teardown must notify both host dequeue waiters and the
# guest Binder handle. Keep pinned Eden unmodified and select one source owner.
set(EDEN_MAINTAINED_NVNF_CONSUMER
    "${PORT_ROOT}/vendor/encore-active/eden-core/src/core/hle/service/nvnflinger/buffer_queue_consumer.cpp")
if(NOT EXISTS "${EDEN_MAINTAINED_NVNF_CONSUMER}")
    message(FATAL_ERROR "Missing maintained buffer queue consumer source")
endif()
list(REMOVE_ITEM core_sources "hle/service/nvnflinger/buffer_queue_consumer.cpp")
list(APPEND core_sources "${EDEN_MAINTAINED_NVNF_CONSUMER}")
# The native app selects one maintained standard guest IPC unit.
# The old development request-profiler source remains unselected.
set(EDEN_MAINTAINED_SVC_IPC_STANDARD
    "${PORT_ROOT}/vendor/encore-active/eden-core/src/core/hle/kernel/svc/svc_ipc_standard.cpp")
if(NOT EXISTS "${EDEN_MAINTAINED_SVC_IPC_STANDARD}")
    message(FATAL_ERROR "Missing maintained normal IPC SVC source")
endif()
list(REMOVE_ITEM core_sources "hle/kernel/svc/svc_ipc.cpp")
list(APPEND core_sources "${EDEN_MAINTAINED_SVC_IPC_STANDARD}")
if(EDEN_A32_FASTMEM)
    # The window spans 4 GiB: only 32-bit applications get it as their fastmem arena.
    # The production backport materializes core/memory.cpp before configure.
    # Maintain the native A32-only fastmem guard as versioned C++, not a
    # configure-time rewrite of that materialized source.
    set(EDEN_MAINTAINED_A32_MEMORY
        "${PORT_ROOT}/vendor/encore-active/eden-core/src/core/memory.cpp")
    if(NOT EXISTS "${EDEN_MAINTAINED_A32_MEMORY}")
        message(FATAL_ERROR "Missing maintained A32 fastmem memory source")
    endif()
    list(REMOVE_ITEM core_sources "memory.cpp")
    list(APPEND core_sources "${EDEN_MAINTAINED_A32_MEMORY}")
    # Upstream places code at any 4 KiB offset below 16 MiB, which leaves three of four
    # layouts with every module page out of 16 KiB phase with its backing. Keep the same
    # range with 16 KiB steps so module chunks can alias.
    set(EDEN_MAINTAINED_CODE_LOADER
        "${PORT_ROOT}/vendor/encore-active/eden-core/src/core/loader/deconstructed_rom_directory.cpp")
    if(NOT EXISTS "${EDEN_MAINTAINED_CODE_LOADER}")
        message(FATAL_ERROR "Missing maintained aligned code loader")
    endif()
    list(REMOVE_ITEM core_sources "loader/deconstructed_rom_directory.cpp")
    list(APPEND core_sources "${EDEN_MAINTAINED_CODE_LOADER}")
endif()
# NSZ/XCZ: select reviewed full C++ source owners instead of generating C++
# with CMake string replacements. Preserve pinned Eden source unchanged.
foreach(eden_ncz_relative IN ITEMS
        "file_sys/submission_package.cpp"
        "file_sys/card_image.cpp"
        "loader/loader.cpp"
        "loader/nsp.cpp"
        "file_sys/registered_cache.cpp")
    set(eden_ncz_maintained
        "${PORT_ROOT}/vendor/encore-active/eden-core/src/core/${eden_ncz_relative}")
    if(NOT EXISTS "${eden_ncz_maintained}")
        message(FATAL_ERROR "Missing maintained NCZ integration: ${eden_ncz_relative}")
    endif()
    list(FIND core_sources "${eden_ncz_relative}" eden_ncz_pinned_index)
    if(eden_ncz_pinned_index LESS 0)
        message(FATAL_ERROR "Pinned NCZ source selection changed: ${eden_ncz_relative}")
    endif()
    list(REMOVE_ITEM core_sources "${eden_ncz_relative}")
    list(APPEND core_sources "${eden_ncz_maintained}")
endforeach()
# Extracted AOC: use the shared vendor source owners for both NS1 and
# experimental NS2, not duplicated frontend implementations. These are
# complete maintained units selected in place of pristine upstream sources.
foreach(eden_aoc_relative IN ITEMS
        "file_sys/romfs_factory.cpp"
        "hle/service/aoc/addon_content_manager.cpp")
    set(eden_aoc_maintained
        "${PORT_ROOT}/vendor/encore-active/eden-core/src/core/${eden_aoc_relative}")
    if(NOT EXISTS "${eden_aoc_maintained}")
        message(FATAL_ERROR "Missing maintained extracted AOC source: ${eden_aoc_relative}")
    endif()
    list(FIND core_sources "${eden_aoc_relative}" eden_aoc_index)
    if(eden_aoc_index LESS 0)
        message(FATAL_ERROR "Pristine AOC owner missing from core sources: ${eden_aoc_relative}")
    endif()
    list(REMOVE_ITEM core_sources "${eden_aoc_relative}")
    list(APPEND core_sources "${eden_aoc_maintained}")
endforeach()
list(APPEND core_sources "${EDEN_PORT_DIR}/ncz.cpp")
# Both the adapter and the two NCZ-aware full source owners use this header.
target_include_directories(core PRIVATE "${EDEN_PORT_DIR}")
# The decompressor is the same pinned zstd library as the existing native NSO
# ZBIC support; do not download or build an unrelated copy.
if(TARGET libzstd_static)
    target_link_libraries(core PRIVATE libzstd_static)
endif()
set_property(TARGET core PROPERTY SOURCES "${core_sources}")
# The guest title is the owner of a zero-ID cache storage request.
set(EDEN_MAINTAINED_SAVEDATA
    "${PORT_ROOT}/vendor/encore-active/eden-core/src/core/file_sys/savedata_factory.cpp")
if(NOT EXISTS "${EDEN_MAINTAINED_SAVEDATA}")
    message(FATAL_ERROR "Missing maintained per-title cache storage source")
endif()
get_target_property(eden_savedata_sources core SOURCES)
list(REMOVE_ITEM eden_savedata_sources "file_sys/savedata_factory.cpp")
list(APPEND eden_savedata_sources "${EDEN_MAINTAINED_SAVEDATA}")
set_property(TARGET core PROPERTY SOURCES "${eden_savedata_sources}")
# Use a maintained bounded shader local-memory translator, keeping the pinned source untouched.
set(EDEN_MAINTAINED_SHADER_LOCAL
    "${PORT_ROOT}/vendor/encore-active/eden-shader/src/shader_recompiler/frontend/maxwell/translate/impl/load_store_local_shared.cpp")
if(NOT EXISTS "${EDEN_MAINTAINED_SHADER_LOCAL}")
    message(FATAL_ERROR "Missing maintained shader local scratch translator")
endif()
get_target_property(eden_shader_sources shader_recompiler SOURCES)
list(FIND eden_shader_sources "frontend/maxwell/translate/impl/load_store_local_shared.cpp" eden_shader_local_position)
if(eden_shader_local_position LESS 0)
    message(FATAL_ERROR "Pinned shader local translator target changed")
endif()
list(REMOVE_ITEM eden_shader_sources "frontend/maxwell/translate/impl/load_store_local_shared.cpp")
list(APPEND eden_shader_sources "${EDEN_MAINTAINED_SHADER_LOCAL}")
set_property(TARGET shader_recompiler PROPERTY SOURCES "${eden_shader_sources}")
# PS5_NATIVE is a CMake option, not a transitive preprocessor definition for
# core or video_core. Only these two pinned TUs own the address guards below.
# Do NOT enable it broadly for every upstream C++ source.
if(PS5_NATIVE)
    # Keep the pinned collector source immutable. The maintained header fixes
    # an atomic page-transition race only for the native target. Make this
    # sole-header override PUBLIC so consumers share one inline definition.
    set(EDEN_NATIVE_DIRTY_HEADER_ROOT
        "${PORT_ROOT}/vendor/encore-active/eden-core/overrides")
    if(NOT EXISTS "${EDEN_NATIVE_DIRTY_HEADER_ROOT}/core/gpu_dirty_memory_manager.h")
        message(FATAL_ERROR "Missing maintained native GPU dirty collector")
    endif()
    # Override the immutable shipping guest policy on native builds without
    # changing the backport manifest or the host launcher's network clients.
    if(NOT EXISTS "${EDEN_NATIVE_DIRTY_HEADER_ROOT}/core/hle/service/sockets/encore_guest_network_policy.h")
        message(FATAL_ERROR "Missing maintained native guest offline policy")
    endif()
    target_include_directories(core BEFORE PUBLIC "${EDEN_NATIVE_DIRTY_HEADER_ROOT}")
    # The native guest-memory header is shared by core and video_core.
    # The latter instantiates GPU write-back templates in its own TUs.
    if(NOT EXISTS "${EDEN_NATIVE_DIRTY_HEADER_ROOT}/core/guest_memory.h")
        message(FATAL_ERROR "Missing maintained native guest memory bounds")
    endif()
    # The native device-memory instantiation must discard stale contiguous
    # mapping metadata on Unmap and default (untracked) Map. Source-only
    # consumers keep the pinned upstream implementation.
    if(NOT EXISTS "${EDEN_NATIVE_DIRTY_HEADER_ROOT}/core/device_memory_manager.inc")
        message(FATAL_ERROR "Missing maintained native device memory continuity")
    endif()
    target_include_directories(video_core BEFORE PRIVATE "${EDEN_NATIVE_DIRTY_HEADER_ROOT}")
    # G13/X05 consolidated: source-complete native memory units, no
    # source string manipulation and no generator under headless CMake.
    set(EDEN_NATIVE_MEMORY_ROOT "${PORT_ROOT}/vendor/encore-active/eden-core/src/core")
    if(EDEN_A32_FASTMEM)
        set(EDEN_NATIVE_GUEST_SOURCE "${EDEN_NATIVE_MEMORY_ROOT}/memory_native_a32.cpp")
        set(eden_native_memory_owner "${EDEN_MAINTAINED_A32_MEMORY}")
    else()
        set(EDEN_NATIVE_GUEST_SOURCE "${EDEN_NATIVE_MEMORY_ROOT}/memory_native_standard.cpp")
        set(eden_native_memory_owner "memory.cpp")
    endif()
    if(NOT EXISTS "${EDEN_NATIVE_GUEST_SOURCE}")
        message(FATAL_ERROR "Missing maintained native guest memory source")
    endif()
    get_target_property(core_sources core SOURCES)
    list(FIND core_sources "${eden_native_memory_owner}" eden_native_memory_owner_index)
    if(eden_native_memory_owner_index EQUAL -1)
        message(FATAL_ERROR "G13 native memory owner missing from core target")
    endif()
    list(REMOVE_ITEM core_sources "${eden_native_memory_owner}")
    list(APPEND core_sources "${EDEN_NATIVE_GUEST_SOURCE}")
    set_property(TARGET core PROPERTY SOURCES "${core_sources}")
    # This native-only define MUST follow the selected complete translation
    # unit. core's target-level definitions do not transitively imply it.
    set_property(SOURCE "${EDEN_NATIVE_GUEST_SOURCE}" TARGET_DIRECTORY core
        APPEND PROPERTY COMPILE_DEFINITIONS "PS5_NATIVE=1")
    set_property(SOURCE "${PROJECT_SOURCE_DIR}/src/video_core/host1x/gpu_device_memory_manager.cpp"
        TARGET_DIRECTORY video_core APPEND PROPERTY COMPILE_DEFINITIONS "PS5_NATIVE=1")
    # Upstream core is a distinct static target: PS5_NATIVE on eden-headless
    # does NOT propagate here. Disable Switch HOME/Capture applet behavior
    # only in the pinned AM poller, leaving desktop behavior unchanged.
    set_property(SOURCE "${PROJECT_SOURCE_DIR}/src/core/hle/service/am/button_poller.cpp"
        TARGET_DIRECTORY core APPEND PROPERTY COMPILE_DEFINITIONS "PS5_NATIVE=1")
endif()
# Maintained service source: title metadata null handling plus a dev-only
# witness of the version resolved from guest update content.
set(EDEN_APP_FUNCTION_SOURCE "${PORT_ROOT}/vendor/encore-active/eden-core/src/core/hle/service/am/service/application_functions.cpp")
if(NOT EXISTS "${EDEN_APP_FUNCTION_SOURCE}")
    message(FATAL_ERROR "Missing maintained guest application metadata service")
endif()
list(FIND core_sources "hle/service/am/service/application_functions.cpp" eden_app_old)
if(eden_app_old EQUAL -1)
    message(FATAL_ERROR "Pinned application metadata service source moved")
endif()
list(REMOVE_ITEM core_sources "hle/service/am/service/application_functions.cpp")
list(APPEND core_sources "${EDEN_APP_FUNCTION_SOURCE}")
set_property(TARGET core PROPERTY SOURCES "${core_sources}")
# Core's NS query service owns this implementation from frontend_common.
target_sources(core PRIVATE "${PROJECT_SOURCE_DIR}/src/frontend_common/play_time_manager.cpp")

# The Core::System overlay is a fully maintained Encore source in both profiles.
# CMake only chooses and copies the exact variant; no configure-time C++ patches.
set(EDEN_MAINTAINED_CORE_SYSTEM_ROOT
    "${PORT_ROOT}/vendor/encore-active/eden-core/src/core")
if(PS5_NATIVE)
    set(EDEN_MAINTAINED_CORE_SYSTEM "${EDEN_MAINTAINED_CORE_SYSTEM_ROOT}/core_native.cpp")
else()
    set(EDEN_MAINTAINED_CORE_SYSTEM "${EDEN_MAINTAINED_CORE_SYSTEM_ROOT}/core_standard.cpp")
endif()
# After selecting Encore's native Core::System owner, replace it with the
# reviewed derivative for extracted NS2 games in the SINGLE final PS5 binary.
# NS1 keeps its configured memory layout; the native diagnostics and all
# existing fastmem/synchronization behavior are retained in this derivative.
if(PS5_NATIVE AND EDEN_REVIEWED_DUAL_NPDM)
    set(EDEN_MAINTAINED_CORE_SYSTEM
        "${PORT_ROOT}/vendor/encore-active/ns2-runtime/process/core/core.cpp")
endif()
if(NOT EXISTS "${EDEN_MAINTAINED_CORE_SYSTEM}")
    message(FATAL_ERROR "Missing maintained Core::System source")
endif()
configure_file("${EDEN_MAINTAINED_CORE_SYSTEM}" "${PORT_BUILD_DIR}/core.cpp" COPYONLY)
get_target_property(core_sources core SOURCES)
# Native-only complete NSO loader is maintained in encore-active. The
# existing build-tree path is preserved for its runtime and host consumers.
if(PS5_NATIVE)
    set(EDEN_MAINTAINED_NATIVE_NSO
        "${PORT_ROOT}/vendor/encore-active/eden-core/src/core/loader/nso.cpp")
    if(NOT EXISTS "${EDEN_MAINTAINED_NATIVE_NSO}")
        message(FATAL_ERROR "Missing maintained native NSO loader")
    endif()
    configure_file("${EDEN_MAINTAINED_NATIVE_NSO}" "${PORT_BUILD_DIR}/nso.cpp" COPYONLY)
    list(REMOVE_ITEM core_sources loader/nso.cpp)
    list(APPEND core_sources "${PORT_BUILD_DIR}/nso.cpp")
endif()
list(REMOVE_ITEM core_sources core.cpp)
list(APPEND core_sources "${PORT_BUILD_DIR}/core.cpp")
set_property(TARGET core PROPERTY SOURCES "${core_sources}")

# RomFS builder parents are non-owning: the tracked source retains both
# original shared_ptr-to-pointer replacements without CMake rewriting.
set(EDEN_MAINTAINED_ROMFS_BUILDER
    "${PORT_ROOT}/vendor/encore-active/eden-core/src/core/file_sys/fsmitm_romfsbuild.cpp")
if(NOT EXISTS "${EDEN_MAINTAINED_ROMFS_BUILDER}")
    message(FATAL_ERROR "Missing maintained RomFS builder source")
endif()
get_target_property(core_sources core SOURCES)
list(REMOVE_ITEM core_sources file_sys/fsmitm_romfsbuild.cpp)
list(APPEND core_sources "${EDEN_MAINTAINED_ROMFS_BUILDER}")
set_property(TARGET core PROPERTY SOURCES "${core_sources}")

# Pinned source fixes below are direct Encore file selections only.
# Mods (headless/mods.h). The pinned patch code cannot apply an .ips patch (it looks for the
# patch's magic in the game's code, and its end marker test never passes) and writes zeros for
# the text of a .pchtxt string patch, whose record also had a fixed size that a long line
# overran. Eden fixed these after this pin; the same fixes are made here. Its .pchtxt reader also
# takes every line as a record or a flag: the credits at the end of a real patch file then wrote
# over the start of the game's code. Only records and known flags are read here
# (headless/mods_check.cpp checks all of it).
# This IPS/pchtxt parser is a complete, audited Encore source; CMake only
# selects it and must never mutate its functions during configuration.
set(EDEN_MAINTAINED_IPS_LAYER
    "${PORT_ROOT}/vendor/encore-active/eden-core/src/core/file_sys/ips_layer.cpp")
if(NOT EXISTS "${EDEN_MAINTAINED_IPS_LAYER}")
    message(FATAL_ERROR "Missing maintained native IPS layer")
endif()
# The patch manager: a missing mod root must never enter its sorting and dereference loops, and an
# .ips patch is named after the build ID in either case.
# Native patch manager: select a complete Encore-maintained source, never mutate upstream C++ here.
set(EDEN_MAINTAINED_PATCH_MANAGER
    "${PORT_ROOT}/vendor/encore-active/eden-core/src/core/file_sys/patch_manager.cpp")
if(NOT EXISTS "${EDEN_MAINTAINED_PATCH_MANAGER}")
    message(FATAL_ERROR "Missing maintained native patch manager")
endif()
get_target_property(core_sources core SOURCES)
list(REMOVE_ITEM core_sources file_sys/ips_layer.cpp file_sys/patch_manager.cpp)
list(APPEND core_sources "${EDEN_MAINTAINED_IPS_LAYER}" "${EDEN_MAINTAINED_PATCH_MANAGER}")
set_property(TARGET core PROPERTY SOURCES "${core_sources}")

# R23 #113 — the three FS compiler inputs are ALREADY complete
# maintained owners (NCZ registered_cache, per-title savedata and IPS
# patch_manager). Pair their exact patched public headers without adding
# duplicate translation units or ever modifying immutable pinned originals.
if(PS5_NATIVE)
    set(EDEN_R23_PARENT_ROOT
        "${PORT_ROOT}/vendor/encore-active/eden-core")
    set(EDEN_R23_PARENT_INCLUDE
        "${PORT_BUILD_DIR}/r23-parent/include")
    foreach(eden_r23_fs_relative IN ITEMS
            registered_cache.h savedata_factory.h patch_manager.h)
        if(NOT EXISTS
               "${EDEN_R23_PARENT_ROOT}/include/core/file_sys/${eden_r23_fs_relative}")
            message(FATAL_ERROR "R23 #113 missing maintained FS header: ${eden_r23_fs_relative}")
        endif()
        configure_file(
            "${EDEN_R23_PARENT_ROOT}/include/core/file_sys/${eden_r23_fs_relative}"
            "${EDEN_R23_PARENT_INCLUDE}/core/file_sys/${eden_r23_fs_relative}"
            COPYONLY)
    endforeach()
    get_target_property(eden_r23_parent_sources core SOURCES)
    foreach(eden_r23_fs_source IN ITEMS
            registered_cache.cpp savedata_factory.cpp patch_manager.cpp)
        set(eden_r23_fs_path
             "${EDEN_R23_PARENT_ROOT}/src/core/file_sys/${eden_r23_fs_source}")
        list(FIND eden_r23_parent_sources
             "${eden_r23_fs_path}" eden_r23_parent_owner)
        if(eden_r23_parent_owner EQUAL -1)
            message(FATAL_ERROR "R23 #113 actual maintained FS owner drifted: ${eden_r23_fs_source}")
        endif()
    endforeach()
    target_include_directories(core BEFORE PRIVATE "${EDEN_R23_PARENT_INCLUDE}")
    message(STATUS "R23 #113: 3 maintained FS units + matching 3 headers; no duplicate owners")
endif()

# The rate of the vsync clock a game runs on (60 Hz, or what an FPS patch asks for: 120, 240) is
# published for the renderer: frames a display has no refresh for are not presented
# (headless/display_refresh.h).
# Encore's native VSync/compose correction is a complete maintained unit.
set(EDEN_MAINTAINED_VI_CONDUCTOR
    "${PORT_ROOT}/vendor/encore-active/eden-core/src/core/hle/service/vi/conductor.cpp")
if(NOT EXISTS "${EDEN_MAINTAINED_VI_CONDUCTOR}")
    message(FATAL_ERROR "Missing maintained VI conductor")
endif()
target_include_directories(core PRIVATE "${EDEN_PORT_DIR}")
get_target_property(core_sources core SOURCES)
list(REMOVE_ITEM core_sources hle/service/vi/conductor.cpp)
list(APPEND core_sources "${EDEN_MAINTAINED_VI_CONDUCTOR}")
set_property(TARGET core PROPERTY SOURCES "${core_sources}")

# Nvdrv sessions borrow process memory until their final handles are unmapped.
# Retain the process across that interval, including service shutdown ordering.
set(EDEN_MAINTAINED_NVDRV_CONTAINER
    "${PORT_ROOT}/vendor/encore-active/eden-core/src/core/hle/service/nvdrv/core/container.cpp")
if(NOT EXISTS "${EDEN_MAINTAINED_NVDRV_CONTAINER}")
    message(FATAL_ERROR "Missing maintained nvdrv session container")
endif()
get_target_property(core_sources core SOURCES)
list(REMOVE_ITEM core_sources hle/service/nvdrv/core/container.cpp)
list(APPEND core_sources "${EDEN_MAINTAINED_NVDRV_CONTAINER}")
set_property(TARGET core PROPERTY SOURCES "${core_sources}")
# A valid NVDRV FD and a live session are prerequisites for Map/Free/Pin.
# Select complete maintained owners, preserving the PS5 NVMap rollback.
set(EDEN_MAINTAINED_NVDRV_NVMAP_CORE
    "${PORT_ROOT}/vendor/encore-active/eden-core/src/core/hle/service/nvdrv/core/nvmap.cpp")
set(EDEN_MAINTAINED_NVDRV_NVMAP_DEVICE
    "${PORT_ROOT}/vendor/encore-active/eden-core/src/core/hle/service/nvdrv/devices/nvmap.cpp")
if(NOT EXISTS "${EDEN_MAINTAINED_NVDRV_NVMAP_CORE}" OR
   NOT EXISTS "${EDEN_MAINTAINED_NVDRV_NVMAP_DEVICE}")
    message(FATAL_ERROR "Missing maintained NVDRV NVMap session owners")
endif()
get_target_property(core_sources core SOURCES)
list(REMOVE_ITEM core_sources
    hle/service/nvdrv/core/nvmap.cpp
    hle/service/nvdrv/devices/nvmap.cpp)
list(APPEND core_sources
    "${EDEN_MAINTAINED_NVDRV_NVMAP_CORE}"
    "${EDEN_MAINTAINED_NVDRV_NVMAP_DEVICE}")
set_property(TARGET core PROPERTY SOURCES "${core_sources}")
# The shared NVDEC IOCTL must roll back earlier pins if a later handle fails.
set(EDEN_MAINTAINED_NVDRV_NVDEC
    "${PORT_ROOT}/vendor/encore-active/eden-core/src/core/hle/service/nvdrv/devices/nvhost_nvdec_common.cpp")
if(NOT EXISTS "${EDEN_MAINTAINED_NVDRV_NVDEC}")
    message(FATAL_ERROR "Missing maintained NVDEC pin-rollback owner")
endif()
get_target_property(core_sources core SOURCES)
list(FIND core_sources "hle/service/nvdrv/devices/nvhost_nvdec_common.cpp" eden_nvdec_index)
if(eden_nvdec_index EQUAL -1)
    message(FATAL_ERROR "Pinned NVDEC owner changed; re-audit source selection")
endif()
list(REMOVE_ITEM core_sources "hle/service/nvdrv/devices/nvhost_nvdec_common.cpp")
list(APPEND core_sources "${EDEN_MAINTAINED_NVDRV_NVDEC}")
set_property(TARGET core PROPERTY SOURCES "${core_sources}")
# Finalize alone leaves both event references and its owner process open.
# Use the same paired close as the other HID event owners.
# Maintained full-source HID event lifetime correction; immutable upstream preserved.
set(EDEN_HID_RESOURCE "${PORT_ROOT}/vendor/encore-active/eden-core/src/hid_core/resource_manager.cpp")
if(NOT EXISTS "${EDEN_HID_RESOURCE}")
    message(FATAL_ERROR "Missing maintained HID resource manager")
endif()
get_target_property(hid_sources hid_core SOURCES)
list(FIND hid_sources resource_manager.cpp hid_resource_original)
if(hid_resource_original EQUAL -1)
    message(FATAL_ERROR "Pinned HID resource source moved; requalify")
endif()
list(REMOVE_ITEM hid_sources resource_manager.cpp)
list(APPEND hid_sources "${EDEN_HID_RESOURCE}")
set_property(TARGET hid_core PROPERTY SOURCES "${hid_sources}")


# R435 DEV Fullkey LIFO witness is maintained as complete C++ in encore-active.
# hid_core selects one variant in the NPad source selector below.

# Clang 18 trips over libstdc++ range constraints for implicit vector-to-span
# conversions inside these generic lambdas. Use the equivalent pointer/count
# constructor for every variable-argument wrapper.
# Native nvdrv span conversion has one maintained, complete header.
# Keep the existing staged include priority, but never rewrite the header in CMake.
set(ioctl_header "core/hle/service/nvdrv/devices/ioctl_serialization.h")
set(EDEN_MAINTAINED_IOCTL
    "${PORT_ROOT}/vendor/encore-active/eden-core/src/${ioctl_header}")
if(NOT EXISTS "${EDEN_MAINTAINED_IOCTL}")
    message(FATAL_ERROR "Missing maintained nvdrv ioctl serialization header")
endif()
file(MAKE_DIRECTORY "${PORT_BUILD_DIR}/include/core/hle/service/nvdrv/devices")
configure_file("${EDEN_MAINTAINED_IOCTL}"
    "${PORT_BUILD_DIR}/include/${ioctl_header}" COPYONLY)
target_include_directories(core BEFORE PRIVATE "${PORT_BUILD_DIR}/include")

# Cached build trees may still hold the old generated slab header even after
# its CMake rewrite was removed. A stale include would hide the maintained
# mutex and object destructor. Purge only the derived build-tree copy.
file(REMOVE "${PORT_BUILD_DIR}/include/core/hle/kernel/k_slab_heap.h")

# Thread finalization helpers are complete tracked headers in encore-active.
# native-hle-overrides.cmake stages those headers without text replacements.

# Complete kernel page-table finalizer is maintained under encore-active.
# No configure-time C++ lambda rewrites.
set(EDEN_MAINTAINED_PAGE_TABLE
    "${PORT_ROOT}/vendor/encore-active/eden-core/src/core/hle/kernel/k_page_table_base.cpp")
if(NOT EXISTS "${EDEN_MAINTAINED_PAGE_TABLE}")
    message(FATAL_ERROR "Missing maintained page-table finalization source")
endif()
get_target_property(page_table_core_sources core SOURCES)
list(FIND page_table_core_sources hle/kernel/k_page_table_base.cpp eden_original_page_table)
if(eden_original_page_table EQUAL -1)
    message(FATAL_ERROR "Pinned page-table source not present in core SOURCES")
endif()
list(REMOVE_ITEM page_table_core_sources hle/kernel/k_page_table_base.cpp)
list(APPEND page_table_core_sources "${EDEN_MAINTAINED_PAGE_TABLE}")
set_property(TARGET core PROPERTY SOURCES "${page_table_core_sources}")

# A server's stopped flag only covers its inner request loop; stopping the CPU
# immediately after it fires can abandon the applet destructor mid-cleanup.
# G19: full maintained kernel units; legacy source rewrite is test-only.
# ServerManager is maintained as exact full C++ sources, with explicit
# normal/DEV selection. Kernel shutdown calls RequestStop on both variants.
set(server_header "core/hle/service/server_manager.h")
set(EDEN_MAINTAINED_SERVER_ROOT
    "${PORT_ROOT}/vendor/encore-active/eden-core/src/core/hle/service")
set(EDEN_MAINTAINED_SERVER_HEADER "${EDEN_MAINTAINED_SERVER_ROOT}/server_manager.h")
set(EDEN_MAINTAINED_SERVER_SOURCE "${EDEN_MAINTAINED_SERVER_ROOT}/server_manager.cpp")
if(NOT EXISTS "${EDEN_MAINTAINED_SERVER_HEADER}" OR
   NOT EXISTS "${EDEN_MAINTAINED_SERVER_SOURCE}")
    message(FATAL_ERROR "Missing maintained server-manager source/header pair")
endif()
file(MAKE_DIRECTORY "${PORT_BUILD_DIR}/include/core/hle/service")
file(REMOVE "${PORT_BUILD_DIR}/include/${server_header}.in")
configure_file("${EDEN_MAINTAINED_SERVER_HEADER}"
    "${PORT_BUILD_DIR}/include/${server_header}" COPYONLY)
get_target_property(core_sources core SOURCES)
list(FIND core_sources hle/service/server_manager.cpp eden_server_original)
if(eden_server_original EQUAL -1)
    message(FATAL_ERROR "Pinned server-manager source moved; requalify Encore selector")
endif()
list(REMOVE_ITEM core_sources hle/service/server_manager.cpp)
list(APPEND core_sources "${EDEN_MAINTAINED_SERVER_SOURCE}")
set_property(TARGET core PROPERTY SOURCES "${core_sources}")
# G19: compile exactly one complete kernel source from Encore.
set(EDEN_MAINTAINED_KERNEL_ROOT "${PORT_ROOT}/vendor/encore-active/eden-core/src/core/hle/kernel")
set(EDEN_MAINTAINED_KERNEL_SOURCE "${EDEN_MAINTAINED_KERNEL_ROOT}/kernel_standard.cpp")
if(NOT EXISTS "${EDEN_MAINTAINED_KERNEL_SOURCE}")
    message(FATAL_ERROR "Missing maintained G19 kernel source")
endif()
get_target_property(core_sources core SOURCES)
list(FIND core_sources hle/kernel/kernel.cpp eden_g19_pinned_owner)
if(eden_g19_pinned_owner EQUAL -1)
    message(FATAL_ERROR "G19 pinned kernel source moved; requalify owner selection")
endif()
list(REMOVE_ITEM core_sources hle/kernel/kernel.cpp)
list(APPEND core_sources "${EDEN_MAINTAINED_KERNEL_SOURCE}")
set_property(TARGET core PROPERTY SOURCES "${core_sources}")

# Replace SDL audio with the optional native sink; the renderer stays null.
get_target_property(audio_sources audio_core SOURCES)
list(FILTER audio_sources EXCLUDE REGEX "sink/sdl3_sink\\.")
set_property(TARGET audio_core PROPERTY SOURCES "${audio_sources}")
get_target_property(audio_definitions audio_core COMPILE_DEFINITIONS)
list(REMOVE_ITEM audio_definitions HAVE_SDL3)
set_property(TARGET audio_core PROPERTY COMPILE_DEFINITIONS "${audio_definitions}")
get_target_property(audio_libraries audio_core LINK_LIBRARIES)
list(REMOVE_ITEM audio_libraries SDL3::SDL3)
set_property(TARGET audio_core PROPERTY LINK_LIBRARIES "${audio_libraries}")
get_target_property(audio_interface audio_core INTERFACE_LINK_LIBRARIES)
list(REMOVE_ITEM audio_interface SDL3::SDL3 "$<LINK_ONLY:SDL3::SDL3>")
set_property(TARGET audio_core PROPERTY INTERFACE_LINK_LIBRARIES "${audio_interface}")

# Reuse the independently authored native ABI contracts from the research.
set(pad_contract "${PORT_ROOT}/third_party")
set(audio_contract "${PORT_ROOT}/third_party")
file(SHA256 "${pad_contract}/ps5_pad.hpp" pad_hash)
file(SHA256 "${audio_contract}/native_audio.hpp" audio_hash)
if(NOT pad_hash STREQUAL "6a9708fe7ab59afa69899e1981e84decf1492a97e8ebd08194f8e27841a00ee0" OR
   NOT audio_hash STREQUAL "5274633c4f7cd4598fc4cdbfe5b044cbfca908845eb22157e73a80dca8faa0f6")
    message(FATAL_ERROR "Native device contracts changed; review the adapter ABI first.")
endif()
# Guest rumble: with no mapped buttons (this frontend binds the virtual_gamepad engine), send each
# player's left and right vibration to the PS5 controller engine (headless/pad.cpp).
# Rumble fallback is a tracked, versioned C++ source rather than a
# configure-time copy with substitutions. Preserve the hid_core source list.
set(EDEN_MAINTAINED_RUMBLE_CONTROLLER
    "${PORT_ROOT}/vendor/encore-active/eden-core/src/hid_core/frontend/emulated_controller.cpp")
if(NOT EXISTS "${EDEN_MAINTAINED_RUMBLE_CONTROLLER}")
    message(FATAL_ERROR "Missing maintained native rumble controller")
endif()
get_target_property(controller_sources hid_core SOURCES)
list(FILTER controller_sources EXCLUDE REGEX "(^|/)emulated_controller\\.cpp$")
list(APPEND controller_sources "${EDEN_MAINTAINED_RUMBLE_CONTROLLER}")
set_property(TARGET hid_core PROPERTY SOURCES "${controller_sources}")
# A controller update reaches every applet resource that is assigned. One that is assigned but not
# activated yet has no controllers set up (NPad::Activate fills them in), and upstream calls
# through its null device. Buttons rarely changed in that window; the motion sensors change with
# every sample, so a game that registers a second applet resource crashed a few seconds after it
# started (seen on the console: page fault in NPad::ControllerUpdate from the pad thread).
# The active shipping NPad implementation plus the two original native
# null-pointer guards are maintained directly; no CMake source mutation.
set(EDEN_MAINTAINED_NPAD
    "${PORT_ROOT}/vendor/encore-active/eden-core/src/hid_core/resources/npad/npad.cpp")
if(NOT EXISTS "${EDEN_MAINTAINED_NPAD}")
    message(FATAL_ERROR "Missing maintained native NPad controller")
endif()
# Only one NPad implementation is compiled. The DEV instrumentation includes
# the same two null guards as the normal maintained unit.
set(EDEN_NPAD_SELECTED "${EDEN_MAINTAINED_NPAD}")
get_target_property(npad_sources hid_core SOURCES)
list(FILTER npad_sources EXCLUDE REGEX "(^|/)npad\\.cpp$")
list(APPEND npad_sources "${EDEN_NPAD_SELECTED}")
set_property(TARGET hid_core PROPERTY SOURCES "${npad_sources}")
add_library(eden-pad STATIC "${EDEN_PORT_DIR}/pad.cpp"
    "${PROJECT_SOURCE_DIR}/src/input_common/input_engine.cpp"
    "${PROJECT_SOURCE_DIR}/src/input_common/input_poller.cpp"
    "${PROJECT_SOURCE_DIR}/src/input_common/drivers/virtual_gamepad.cpp")
target_include_directories(eden-pad PUBLIC "${EDEN_PORT_DIR}" "${pad_contract}" "${audio_contract}" "${PROJECT_SOURCE_DIR}/src")
target_link_libraries(eden-pad PUBLIC common)
target_compile_options(eden-pad PRIVATE -fno-rtti $<$<BOOL:${PS5_NATIVE}>:-femulated-tls>)
target_sources(audio_core PRIVATE "${EDEN_PORT_DIR}/audio.cpp")
target_include_directories(audio_core PRIVATE "${EDEN_PORT_DIR}" "${pad_contract}" "${audio_contract}")
# The native audio sink's exact pinned-source transform is maintained as C++.
set(EDEN_MAINTAINED_SINK_DETAILS
    "${PORT_ROOT}/vendor/encore-active/eden-core/src/audio_core/sink/sink_details.cpp")
if(NOT EXISTS "${EDEN_MAINTAINED_SINK_DETAILS}")
    message(FATAL_ERROR "Missing maintained native audio sink")
endif()
# Keep native PCM queue/upmix/held-frame behavior in a tracked C++ source.
set(EDEN_MAINTAINED_SINK_STREAM
    "${PORT_ROOT}/vendor/encore-active/eden-core/src/audio_core/sink/sink_stream.cpp")
if(NOT EXISTS "${EDEN_MAINTAINED_SINK_STREAM}")
    message(FATAL_ERROR "Missing maintained native audio stream")
endif()
# A bitfield expression yields 0/1, so explicitly restore the SRC flag's bit position.
# Preserve the source bitfield-position fix without regenerating this TU.
set(EDEN_MAINTAINED_VOICE_INFO
    "${PORT_ROOT}/vendor/encore-active/eden-core/src/audio_core/renderer/voice/voice_info.cpp")
if(NOT EXISTS "${EDEN_MAINTAINED_VOICE_INFO}")
    message(FATAL_ERROR "Missing maintained voice source")
endif()
get_target_property(audio_sources audio_core SOURCES)
list(REMOVE_ITEM audio_sources sink/sink_details.cpp sink/sink_stream.cpp renderer/voice/voice_info.cpp)
list(APPEND audio_sources "${EDEN_MAINTAINED_SINK_DETAILS}" "${EDEN_MAINTAINED_SINK_STREAM}" "${EDEN_MAINTAINED_VOICE_INFO}")
set_property(TARGET audio_core PROPERTY SOURCES "${audio_sources}")
if(PS5_NATIVE)
    target_link_libraries(eden-pad PUBLIC "${sdk}/target/lib/libScePad.so" "${sdk}/target/lib/libSceUserService.so")
    target_link_libraries(audio_core PUBLIC "${sdk}/target/lib/libSceAudioOut.so")
else()
    add_library(eden-device-mock STATIC "${EDEN_PORT_DIR}/mock_devices.cpp")
    target_include_directories(eden-device-mock PUBLIC "${EDEN_PORT_DIR}" "${pad_contract}" "${audio_contract}")
    target_include_directories(eden-device-mock PRIVATE "${PROJECT_SOURCE_DIR}/src")
    target_link_libraries(eden-device-mock PRIVATE common)
    target_link_libraries(audio_core PUBLIC eden-device-mock)
endif()

# The Vulkan factory is byte-identical to the pinned source; only the
# OpenGL-only build requires a distinct maintained unit without Vulkan symbols.
set(EDEN_MAINTAINED_GL_VIDEO_FACTORY
    "${PORT_ROOT}/vendor/encore-active/eden-core/src/video_core/video_core_opengl.cpp")
if(NOT EXISTS "${EDEN_MAINTAINED_GL_VIDEO_FACTORY}")
    message(FATAL_ERROR "Missing maintained OpenGL-only video core factory")
endif()
get_target_property(video_sources video_core SOURCES)
# Runtime-selected index-buffer dirty flags must follow macro draw arguments
# (first/count), not only Maxwell register writes. Keep the single maintained
# override in encore-active, and never build the pinned source alongside it.
if(PS5_NATIVE)
    set(EDEN_MAINTAINED_DRAW_MANAGER
        "${PORT_ROOT}/vendor/encore-active/eden-core/src/video_core/engines/draw_manager.cpp")
    if(NOT EXISTS "${EDEN_MAINTAINED_DRAW_MANAGER}")
        message(FATAL_ERROR "Missing maintained indexed draw manager")
    endif()
    list(REMOVE_ITEM video_sources engines/draw_manager.cpp)
    list(APPEND video_sources "${EDEN_MAINTAINED_DRAW_MANAGER}")
endif()
# A guest span must be rejected BEFORE IsContinuousRange walks GPU page tables.
# An out-of-space or wrapping address would otherwise index the page vectors.
# Preserve the normal range walk and all GPU cache operations for valid spans.
if(PS5_NATIVE)
    # One maintained native source: address-span and granular-page bounds.
    # No C++ replacement string or helper module is evaluated at configure.
    set(EDEN_NATIVE_GPU_MEMORY_MANAGER
        "${PORT_ROOT}/vendor/encore-active/eden-core/src/video_core/memory_manager.cpp")
    if(NOT EXISTS "${EDEN_NATIVE_GPU_MEMORY_MANAGER}")
        message(FATAL_ERROR "Missing Encore-maintained GPU memory manager")
    endif()
    list(REMOVE_ITEM video_sources "memory_manager.cpp")
    list(APPEND video_sources "${EDEN_NATIVE_GPU_MEMORY_MANAGER}")
endif()

# N51: the same PS5 GPU MemoryManager accumulates adjacent changed PTE
# cache invalidations for both guests. A physically remapped but still-Mapped
# PTE triggers the same notification (P1.2); unchanged pages never do.
if(PS5_NATIVE)
    if(NOT EXISTS "${EDEN_NATIVE_GPU_MEMORY_MANAGER}")
        message(FATAL_ERROR "Maintained PS5 GPU memory manager owner missing")
    endif()
    if(NOT EXISTS "${PORT_ROOT}/vendor/encore-active/ns2-helpers/include/video_core/ns2_egl_gpu_range_batch.h")
        message(FATAL_ERROR "Missing N51 vendor range-batching helper")
    endif()
    target_include_directories(video_core BEFORE PRIVATE
        "${PORT_ROOT}/vendor/encore-active/ns2-helpers/include")
    target_compile_definitions(video_core PRIVATE EDEN_NS2_GPU_RANGE_BATCH=1)
endif()
# R411: Eden #4473/#4477 are already applied once by the audited
# version-locked shipping backports to PROJECT_SOURCE_DIR before CMake.
if(PS5_NATIVE)
    foreach(gpu4473_item
        "buffer_cache/buffer_cache.h|gpu_modified_ranges.ForEachInRange(device_addr_out, range_size"
        "buffer_cache/buffer_cache.h|if (IsRegionGpuModified(device_addr, size))"
        "engines/kepler_compute.h|bool upload_dirty{};"
        "engines/kepler_compute.h|bool was_dirty;"
        "engines/kepler_compute.cpp|data.was_dirty || source_dirty"
        "dma_pusher.cpp|dma_state.method == ComputeInline && dma_state.non_incrementing")
        string(REPLACE "|" ";" gpu4473_pair "${gpu4473_item}")
        list(GET gpu4473_pair 0 gpu4473_path)
        list(GET gpu4473_pair 1 gpu4473_anchor)
        file(READ "${PROJECT_SOURCE_DIR}/src/video_core/${gpu4473_path}" gpu4473_source)
        string(FIND "${gpu4473_source}" "${gpu4473_anchor}" gpu4473_at)
        if(gpu4473_at LESS 0)
            message(FATAL_ERROR "Prepared Eden source lacks #4473/#4477: ${gpu4473_path}: ${gpu4473_anchor}")
        endif()
    endforeach()
endif()
if(NOT EDEN_PS5_VULKAN)
    list(FILTER video_sources EXCLUDE REGEX "^(renderer_vulkan|vulkan_common)/")
else()
    include("${EDEN_PORT_DIR}/vulkan.cmake")
endif()
# R2 production staging provenance. This selects real maintained source
# owner/header together; OFF leaves the pinned legacy staging owner intact.
# Upload scheduling retains the verified fail-closed lifetime controls.
set(EDEN_R2_STAGE_HEADER
    "${PORT_BUILD_DIR}/include/video_core/renderer_vulkan/vk_staging_buffer_pool.h")
set(EDEN_R2_BOUNDS_HEADER
    "${PORT_BUILD_DIR}/include/video_core/renderer_vulkan/ns2_staging_upload_bounds.h")
set(EDEN_R2_RETIREMENT_HEADER
    "${PORT_BUILD_DIR}/include/video_core/renderer_vulkan/ns2_gpu_retirement_hold.h")
if(PS5_NATIVE AND EDEN_PS5_VULKAN AND EDEN_REVIEWED_DUAL_NPDM)
    if(NOT PS5_NATIVE OR NOT EDEN_PS5_VULKAN)
        message(FATAL_ERROR "R2 staging backing needs explicit PS5 native Vulkan")
    endif()
    set(EDEN_R2_STAGING_CPP "${PORT_BUILD_DIR}/vk_staging_buffer_pool.cpp")
    if(NOT EXISTS "${EDEN_R2_STAGE_HEADER}" OR
       NOT EXISTS "${EDEN_R2_BOUNDS_HEADER}" OR
       NOT EXISTS "${EDEN_R2_RETIREMENT_HEADER}" OR
       NOT EXISTS "${EDEN_R2_STAGING_CPP}")
        message(FATAL_ERROR "R2 source/header pair missing from maintained vendor")
    endif()
    list(FIND video_sources "renderer_vulkan/vk_staging_buffer_pool.cpp"
         EDEN_R2_ORIGINAL_STAGING_INDEX)
    if(EDEN_R2_ORIGINAL_STAGING_INDEX LESS 0)
        message(FATAL_ERROR "R2 original staging owner moved; re-audit CMake")
    endif()
    list(REMOVE_ITEM video_sources "renderer_vulkan/vk_staging_buffer_pool.cpp")
    list(APPEND video_sources "${EDEN_R2_STAGING_CPP}")
    target_compile_definitions(video_core PRIVATE EDEN_NS2_STAGE_BACKING=1)
    set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS
                 "${EDEN_R2_STAGE_HEADER}" "${EDEN_R2_BOUNDS_HEADER}"
                 "${EDEN_R2_RETIREMENT_HEADER}" "${EDEN_R2_STAGING_CPP}")
else()
    # Vulkan's shared overlay-copy step copies this optional header too.
    # Explicitly remove it when OFF so the old public staging ABI wins.
    file(REMOVE "${EDEN_R2_STAGE_HEADER}" "${EDEN_R2_BOUNDS_HEADER}"
                "${EDEN_R2_RETIREMENT_HEADER}")
endif()

list(REMOVE_ITEM video_sources video_core.cpp gpu.cpp)
if(EDEN_PS5_VULKAN)
    list(APPEND video_sources video_core.cpp)
else()
    list(APPEND video_sources "${EDEN_MAINTAINED_GL_VIDEO_FACTORY}")
endif()
# Remove a derived header left by the isolated classic-uniform experiment.
file(REMOVE "${PORT_BUILD_DIR}/include/video_core/buffer_cache/buffer_cache_base.h")
# Join the worker before its renderer/context and scheduler are destroyed.
# C++ members are destroyed in reverse declaration order.
# G21: compile a single full C++ source from vendor/encore-active.
# Legacy text transformations are retained only in tools/fixtures.
if(EDEN_PS5_OPENGL)
    set(EDEN_MAINTAINED_GL_BUFFER_CACHE
        "${PORT_ROOT}/vendor/encore-active/eden-core/src/video_core/renderer_opengl/gl_buffer_cache.cpp")
    if(NOT EXISTS "${EDEN_MAINTAINED_GL_BUFFER_CACHE}")
        message(FATAL_ERROR "Missing maintained OpenGL buffer cache source")
    endif()
    list(REMOVE_ITEM video_sources renderer_opengl/gl_buffer_cache.cpp)
    list(APPEND video_sources "${EDEN_MAINTAINED_GL_BUFFER_CACHE}")
    if(PS5_NATIVE)
        # PS5 permits reading an ended query while another query is active.
        # Retain the upstream driver-specific workaround on all other builds.
        set(EDEN_MAINTAINED_GL_QUERY_CACHE
            "${PORT_ROOT}/vendor/encore-active/eden-core/src/video_core/renderer_opengl/gl_query_cache.cpp")
        if(NOT EXISTS "${EDEN_MAINTAINED_GL_QUERY_CACHE}")
            message(FATAL_ERROR "Missing maintained native OpenGL query cache")
        endif()
        list(REMOVE_ITEM video_sources renderer_opengl/gl_query_cache.cpp)
        list(APPEND video_sources "${EDEN_MAINTAINED_GL_QUERY_CACHE}")
    endif()
        # Guest draw instrumentation is selected from complete Encore sources.
    # Each profile selects one full translation unit; never splice C++ in CMake.
    set(EDEN_MAINTAINED_GL_RASTERIZER_ROOT
        "${PORT_ROOT}/vendor/encore-active/eden-core/src/video_core/renderer_opengl")
    set(EDEN_MAINTAINED_GL_RASTERIZER
        "${EDEN_MAINTAINED_GL_RASTERIZER_ROOT}/gl_rasterizer.cpp")
    if(NOT EXISTS "${EDEN_MAINTAINED_GL_RASTERIZER}")
        message(FATAL_ERROR "Missing maintained OpenGL rasterizer variant")
    endif()
    list(REMOVE_ITEM video_sources renderer_opengl/gl_rasterizer.cpp)
    list(APPEND video_sources "${EDEN_MAINTAINED_GL_RASTERIZER}")
    # renderer_opengl.cpp is byte-identical to the pinned source. Keep the
    # original in video_sources: copying it into a derived TU adds no behavior.
    # Join the GPU worker before transferring its context to the teardown thread.
    if(PS5_NATIVE)
        # Native MacroJIT exception recovery is selected from Encore, not generated.
        set(EDEN_MAINTAINED_MACRO
            "${PORT_ROOT}/vendor/encore-active/eden-core/src/video_core/macro.cpp")
        if(NOT EXISTS "${EDEN_MAINTAINED_MACRO}")
            message(FATAL_ERROR "Missing maintained native macro unit")
        endif()
        list(REMOVE_ITEM video_sources macro.cpp)
        list(APPEND video_sources "${EDEN_MAINTAINED_MACRO}")
    endif()
    # R345: PS5 compiles our versioned, complete GPU worker and queue sources.
    # No source-code string rewrites execute during native configuration.
    if(PS5_NATIVE)
        set(EDEN_ACTIVE_GPU "${PORT_ROOT}/vendor/encore-active/eden-gpu")
        set(EDEN_GPU_WORKER_VARIANT "gpu_thread_quiet.cpp")
        file(MAKE_DIRECTORY "${PORT_BUILD_DIR}/include/common" "${PORT_BUILD_DIR}/include/video_core")
        configure_file("${EDEN_ACTIVE_GPU}/include/common/bounded_threadsafe_queue.h"
            "${PORT_BUILD_DIR}/include/common/bounded_threadsafe_queue.h" COPYONLY)
        configure_file("${EDEN_ACTIVE_GPU}/include/video_core/gpu_thread.h"
            "${PORT_BUILD_DIR}/include/video_core/gpu_thread.h" COPYONLY)
        configure_file("${EDEN_ACTIVE_GPU}/${EDEN_GPU_WORKER_VARIANT}"
            "${PORT_BUILD_DIR}/gpu_thread.cpp" COPYONLY)
        list(REMOVE_ITEM video_sources gpu_thread.cpp)
        list(APPEND video_sources "${PORT_BUILD_DIR}/gpu_thread.cpp")
    else()
    # PS5 GPU queue is already copied from the complete eden-gpu source above.
    # Host-specific GPU header is a tracked source, not generated C++.
    set(EDEN_MAINTAINED_HOST_GPU_HEADER
        "${PORT_ROOT}/vendor/encore-active/eden-core/host-gpu/include/video_core/gpu_thread.h")
    if(NOT EXISTS "${EDEN_MAINTAINED_HOST_GPU_HEADER}")
        message(FATAL_ERROR "Missing maintained host GPU header")
    endif()
    file(MAKE_DIRECTORY "${PORT_BUILD_DIR}/include/video_core")
    configure_file("${EDEN_MAINTAINED_HOST_GPU_HEADER}"
        "${PORT_BUILD_DIR}/include/video_core/gpu_thread.h" COPYONLY)
    endif()
    target_include_directories(video_core BEFORE PRIVATE "${PORT_BUILD_DIR}/include")
    # G20: select maintained normal/DEV guest GPU command processor units.
    # The DMA input already contains the shipping #4473/#4477 backport.
    set(EDEN_MAINTAINED_GUEST_GPU_ROOT
        "${PORT_ROOT}/vendor/encore-active/eden-core/src/video_core")
    set(EDEN_MAINTAINED_GPU_DMA "${EDEN_MAINTAINED_GUEST_GPU_ROOT}/dma_pusher.cpp")
    set(EDEN_MAINTAINED_GPU_PULLER "${EDEN_MAINTAINED_GUEST_GPU_ROOT}/engines/puller.cpp")
    if(NOT EXISTS "${EDEN_MAINTAINED_GPU_DMA}" OR
       NOT EXISTS "${EDEN_MAINTAINED_GPU_PULLER}")
        message(FATAL_ERROR "Missing maintained GPU command processor variants")
    endif()
    list(REMOVE_ITEM video_sources dma_pusher.cpp engines/puller.cpp)
    list(APPEND video_sources "${EDEN_MAINTAINED_GPU_DMA}" "${EDEN_MAINTAINED_GPU_PULLER}")
endif()
set(EDEN_G21_GPU_ROOT "${PORT_ROOT}/vendor/encore-active/eden-core/src/video_core")
if(EDEN_PS5_OPENGL)
    if(PS5_NATIVE)
        set(EDEN_MAINTAINED_G21_GPU "${EDEN_G21_GPU_ROOT}/gpu_gl_native.cpp")
    else()
        set(EDEN_MAINTAINED_G21_GPU "${EDEN_G21_GPU_ROOT}/gpu_gl_host.cpp")
    endif()
    # The complete GPU source includes portable private headless headers.
    target_include_directories(video_core PRIVATE "${EDEN_PORT_DIR}")
else()
    set(EDEN_MAINTAINED_G21_GPU "${EDEN_G21_GPU_ROOT}/gpu_vulkan.cpp")
endif()
if(NOT EXISTS "${EDEN_MAINTAINED_G21_GPU}")
    message(FATAL_ERROR "Missing maintained G21 GPU translation unit")
endif()
list(APPEND video_sources "${EDEN_MAINTAINED_G21_GPU}")
# Upstream ProsperoEden 673f675 (#72), adapted to pinned Eden 5f142c79:
# salvage complete shader pipeline entries after a damaged tail.
# Shader cache tail recovery is maintained directly in Encore C++.
# CMake selects the source; the adjacent .inc is a tracked, sole-owner header.
set(EDEN_MAINTAINED_SHADER_ENVIRONMENT
    "${PORT_ROOT}/vendor/encore-active/eden-core/src/video_core/shader_environment.cpp")
set(EDEN_MAINTAINED_SHADER_READER
    "${PORT_ROOT}/vendor/encore-active/eden-core/src/video_core/shader_cache_reader.inc")
if(NOT EXISTS "${EDEN_MAINTAINED_SHADER_ENVIRONMENT}" OR
   NOT EXISTS "${EDEN_MAINTAINED_SHADER_READER}")
    message(FATAL_ERROR "Missing maintained shader cache recovery source")
endif()
# R428: port upstream d7f2764 ASTC per-layer scratch without modifying
# the immutable Eden source package. Keep the converted pixel order and BC
# output offsets; only the temporary decode batch width changes.
# The one-layer ASTC scratch optimization is a complete Encore source.
# Keep the original pinned package immutable; CMake only selects this TU.
set(EDEN_MAINTAINED_TEXTURE_UTIL
    "${PORT_ROOT}/vendor/encore-active/eden-core/src/video_core/texture_cache/util.cpp")
if(NOT EXISTS "${EDEN_MAINTAINED_TEXTURE_UTIL}")
    message(FATAL_ERROR "Missing maintained ASTC texture utility")
endif()
list(REMOVE_ITEM video_sources texture_cache/util.cpp)
list(APPEND video_sources "${EDEN_MAINTAINED_TEXTURE_UTIL}")
list(REMOVE_ITEM video_sources shader_environment.cpp)
list(APPEND video_sources "${EDEN_MAINTAINED_SHADER_ENVIRONMENT}")
# Eden #4473/#4477 are already applied once to the pinned source by
# tools/apply-eden-backports.sh and validated there; never shadow headers twice.
# Complete native Maxwell DMA owner; the pinned source remains for host.
if(PS5_NATIVE)
    set(EDEN_MAINTAINED_MAXWELL_DMA
        "${PORT_ROOT}/vendor/encore-active/eden-core/src/video_core/engines/maxwell_dma.cpp")
    if(NOT EXISTS "${EDEN_MAINTAINED_MAXWELL_DMA}")
        message(FATAL_ERROR "Missing maintained native Maxwell DMA")
    endif()
    list(REMOVE_ITEM video_sources engines/maxwell_dma.cpp)
    list(APPEND video_sources "${EDEN_MAINTAINED_MAXWELL_DMA}")
endif()
# Native N04: avoid invoking an already-ready Host1x callback under guard.
# Select a complete maintained TU; never edit the pinned vendor checkout.
set(EDEN_MAINTAINED_HOST1X_SYNCPOINT
    "${PORT_ROOT}/vendor/encore-active/eden-core/src/video_core/host1x/syncpoint_manager.cpp")
if(NOT EXISTS "${EDEN_MAINTAINED_HOST1X_SYNCPOINT}")
    message(FATAL_ERROR "Missing maintained Host1x syncpoint source")
endif()
list(REMOVE_ITEM video_sources host1x/syncpoint_manager.cpp)
list(APPEND video_sources "${EDEN_MAINTAINED_HOST1X_SYNCPOINT}")
# N54: shared PS5 texture-cache scratch ownership, both guests. Only
# transient CPU buffers over 64 MiB are retired on a completed TickFrame;
# smaller NS1 scratch and resident GPU images retain their previous lifetime.
if(PS5_NATIVE)
    set(EDEN_NS2_ASTC_OWNER_ROOT
        "${PORT_ROOT}/vendor/encore-active/ns2-astc/include")
    foreach(eden_ns2_astc_owner IN ITEMS
            "common/scratch_buffer.h"
            "video_core/texture_cache/texture_cache.h")
        if(NOT EXISTS "${EDEN_NS2_ASTC_OWNER_ROOT}/${eden_ns2_astc_owner}")
            message(FATAL_ERROR "N54 maintained vendor ASTC owner missing: ${eden_ns2_astc_owner}")
        endif()
    endforeach()
    # One header identity for all consumers; no generated copies.
    target_include_directories(common BEFORE PUBLIC "${EDEN_NS2_ASTC_OWNER_ROOT}")
    target_include_directories(video_core BEFORE PUBLIC "${EDEN_NS2_ASTC_OWNER_ROOT}")
    target_compile_definitions(video_core PRIVATE EDEN_NS2_ASTC_SCRATCH_TRIM=1)
endif()

# N56: shared production PS5 Vulkan cache admission, NS1 and NS2 alike.
# The maintained vendor owner rejects truncated driver cache files without
# modifying the successful cache read/write path or requiring a research flag.
if(PS5_NATIVE AND EDEN_PS5_VULKAN)
    if(NOT EXISTS "${PORT_ROOT}/vendor/encore-active/eden-vulkan/vk_pipeline_cache_cost.cpp")
        message(FATAL_ERROR "N56 native Vulkan vendor owner missing")
    endif()
    target_compile_definitions(video_core PRIVATE EDEN_NS2_PIPELINE_CACHE_GUARD=1)
endif()

# N57: shared PS5 Vulkan ASTC layer decode; same maintained cache/compute
# translation units as NS1. Additive views/entrypoint and fail-closed layer
# preflight; no alternate renderer, title exception or research dependency.
if(PS5_NATIVE AND EDEN_PS5_VULKAN)
    set(EDEN_NS2_ASTC_OWNER_ROOT
        "${PORT_ROOT}/vendor/encore-active/ns2-astc/include")
    set(EDEN_NS2_HELPERS_ROOT
        "${PORT_ROOT}/vendor/encore-active/ns2-helpers/include")
    foreach(eden_ns2_astc_file IN ITEMS
            "video_core/renderer_vulkan/vk_texture_cache.h"
            "video_core/renderer_vulkan/vk_compute_pass.h"
            "video_core/renderer_vulkan/ns2_astc_assemble_layers.inc")
        if(NOT EXISTS "${EDEN_NS2_ASTC_OWNER_ROOT}/${eden_ns2_astc_file}")
            message(FATAL_ERROR "Missing N57 vendor ASTC owner: ${eden_ns2_astc_file}")
        endif()
    endforeach()
    if(NOT EXISTS "${EDEN_NS2_HELPERS_ROOT}/video_core/renderer_vulkan/ns2_astc_decode_preflight.h")
        message(FATAL_ERROR "N57 ASTC mip/layer preflight vendor owner missing")
    endif()
    foreach(eden_ns2_native IN ITEMS vk_texture_cache_cost.cpp vk_compute_pass_cost.cpp)
        if(NOT EXISTS "${PORT_BUILD_DIR}/${eden_ns2_native}")
            message(FATAL_ERROR "N57 native Vulkan source owner missing: ${eden_ns2_native}")
        endif()
        list(FIND video_sources "${PORT_BUILD_DIR}/${eden_ns2_native}" eden_ns2_astc_native_idx)
        if(eden_ns2_astc_native_idx EQUAL -1)
            message(FATAL_ERROR "N57 PS5 Vulkan source selection changed")
        endif()
    endforeach()
    target_include_directories(video_core BEFORE PUBLIC
        "${EDEN_NS2_ASTC_OWNER_ROOT}" "${EDEN_NS2_HELPERS_ROOT}")
    target_compile_definitions(video_core PRIVATE EDEN_NS2_ASTC_LAYER_DECODE=1)
endif()

# R4 native production: compile the actual N60 ASTC TextureCache
# implementation (the source used by the PS5 renderer), NOT the shadowed
# eden-vulkan/vulkan-cache copy. Explicit opt-in, default OFF on all builds.
if(PS5_NATIVE AND EDEN_PS5_VULKAN AND EDEN_REVIEWED_DUAL_NPDM)
    if(NOT PS5_NATIVE OR NOT EDEN_PS5_VULKAN)
        message(FATAL_ERROR "R4 volume-slice research requires PS5 native Vulkan")
    endif()
    set(EDEN_R4_ACTIVE_TEXTURE_CACHE
        "${PORT_ROOT}/vendor/encore-active/ns2-astc/include/video_core/texture_cache/texture_cache.h")
    if(NOT EXISTS "${EDEN_R4_ACTIVE_TEXTURE_CACHE}")
        message(FATAL_ERROR "R4 N60 maintained TextureCache owner missing")
    endif()
    file(STRINGS "${EDEN_R4_ACTIVE_TEXTURE_CACHE}" EDEN_R4_ACTIVE_OWNER_SOURCE
         REGEX "copy_native_volume_slice")
    if(NOT EDEN_R4_ACTIVE_OWNER_SOURCE MATCHES
           "copy_native_volume_slice")
        message(FATAL_ERROR "R4 wrong active TextureCache owner selected")
    endif()
    list(FIND video_sources "${PORT_BUILD_DIR}/vk_texture_cache_cost.cpp"
         EDEN_R4_CONSUMER_INDEX)
    if(EDEN_R4_CONSUMER_INDEX LESS 0)
        message(FATAL_ERROR "R4 active Vulkan cache consumer missing from native graph")
    endif()
    target_compile_definitions(video_core PRIVATE EDEN_NS2_VOLUME_COPY=1)
    set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS
                 "${EDEN_R4_ACTIVE_TEXTURE_CACHE}")
endif()

# Sparse native GPU probes were diagnostic paths without a production
# consumer. Keep the supported dense Vulkan texture cache until sparse
# mapping integrates with the same normal scheduler and memory ownership.
# N60: one shared PS5 Vulkan texture-cache/ImageBase ABI for both guests.
# Partial ASTC layer upload is admitted by generic image properties only;
# unqualified images retain the original whole-image upload. N57 is selected
# by the same PS5/Vulkan condition and completes before this block.
if(PS5_NATIVE AND EDEN_PS5_VULKAN)
    set(EDEN_NS2_ASTC_OWNER_ROOT
        "${PORT_ROOT}/vendor/encore-active/ns2-astc/include")
    set(EDEN_NS2_HELPERS_ROOT
        "${PORT_ROOT}/vendor/encore-active/ns2-helpers/include")
    foreach(eden_ns2_astc_file IN ITEMS
            "video_core/texture_cache/image_base.h"
            "video_core/texture_cache/texture_cache_base.h"
            "video_core/texture_cache/texture_cache.h"
            "video_core/texture_cache/ns2_astc_texture_cache_bridge.inc")
        if(NOT EXISTS "${EDEN_NS2_ASTC_OWNER_ROOT}/${eden_ns2_astc_file}")
            message(FATAL_ERROR "Missing N60 vendor source: ${eden_ns2_astc_file}")
        endif()
    endforeach()
    if(NOT EXISTS "${EDEN_NS2_HELPERS_ROOT}/video_core/texture_cache/ns2_astc_staging_bridge.h")
        message(FATAL_ERROR "Missing maintained N59 ASTC staging coordinator")
    endif()
    # C++ ImageBase layout must match across consumers; never shadow the
    # primary CMake-generated Vulkan TUs with obsolete snapshot copies.
    target_include_directories(video_core BEFORE PUBLIC
        "${EDEN_NS2_ASTC_OWNER_ROOT}" "${EDEN_NS2_HELPERS_ROOT}")
    target_include_directories(core BEFORE PUBLIC
        "${EDEN_NS2_ASTC_OWNER_ROOT}" "${EDEN_NS2_HELPERS_ROOT}")
    target_compile_definitions(video_core PUBLIC EDEN_NS2_ASTC_CACHE_BRIDGE=1)
    target_compile_definitions(core PUBLIC EDEN_NS2_ASTC_CACHE_BRIDGE=1)
endif()

# Sparse VMA, VkImage factory and requirements are in the shared vendor fork.

# N49: shared production PS5 Vulkan image-view dimensionality guard.
# A 3D shader must not force an incompatible 2D image into an invalid VkImageView.
# The same maintained texture cache owner serves NS1 and NS2.
if(PS5_NATIVE AND EDEN_PS5_VULKAN)
    set(EDEN_NS2_N49_HELPER
        "${PORT_ROOT}/vendor/encore-active/ns2-helpers/include/video_core/renderer_vulkan/ns2_view_type_guard.h")
    if(NOT EXISTS "${EDEN_NS2_N49_HELPER}")
        message(FATAL_ERROR "N49 maintained view-dimension guard missing")
    endif()
    list(FIND video_sources "${PORT_BUILD_DIR}/vk_texture_cache_cost.cpp" eden_ns2_view_owner)
    if(eden_ns2_view_owner EQUAL -1)
        message(FATAL_ERROR "N49 native Vulkan source selection changed")
    endif()
    target_include_directories(video_core BEFORE PRIVATE
        "${PORT_ROOT}/vendor/encore-active/ns2-helpers/include")
    target_compile_definitions(video_core PRIVATE EDEN_NS2_VIEW_DIMENSION_GUARD=1)
endif()
# R3: production selection of the maintained GOB16 decoder TU. Never
# mutate the pinned Eden source tree or include TWO definitions of the public
# SwizzleTexture/UnswizzleTexture/SwizzleSubrect API in a single binary.
# Disabled and select the maintained decoder for normal native PS5 operation.
if(PS5_NATIVE AND EDEN_PS5_VULKAN AND EDEN_REVIEWED_DUAL_NPDM)
    if(NOT PS5_NATIVE OR NOT EDEN_PS5_VULKAN)
        message(FATAL_ERROR
            "R3 GOB16 requires an explicit native PS5 Vulkan research configuration")
    endif()
    set(EDEN_NS2_GOB16_DECODER
        "${PORT_ROOT}/vendor/encore-active/eden-core/src/video_core/textures/decoders.cpp")
    if(NOT EXISTS "${EDEN_NS2_GOB16_DECODER}")
        message(FATAL_ERROR
            "R3 GOB16 maintained decoder missing at the checked out vendor pin")
    endif()
    list(FIND video_sources "textures/decoders.cpp" EDEN_NS2_GOB16_PINNED_INDEX)
    if(EDEN_NS2_GOB16_PINNED_INDEX LESS 0)
        message(FATAL_ERROR
            "R3 GOB16 original translation unit changed; re-audit source selection")
    endif()
    list(FIND video_sources "${EDEN_NS2_GOB16_DECODER}" EDEN_NS2_GOB16_DUPLICATE_INDEX)
    if(NOT EDEN_NS2_GOB16_DUPLICATE_INDEX EQUAL -1)
        message(FATAL_ERROR
            "R3 GOB16 maintained decoder already selected; refusing duplicate TU")
    endif()
    list(REMOVE_ITEM video_sources "textures/decoders.cpp")
    list(APPEND video_sources "${EDEN_NS2_GOB16_DECODER}")
    set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS
                 "${EDEN_NS2_GOB16_DECODER}")
endif()
set_property(TARGET video_core PROPERTY SOURCES "${video_sources}")

if(PS5_NATIVE)
    target_compile_definitions(libzstd_static PRIVATE ZSTD_TRACE=0)
    # The native title cannot chdir. Set the shared path manager's data root
    # directly so every core/log/cache path remains inside its writable mount.
    # The native data/config/cache roots are a tracked C++ override.
    set(EDEN_MAINTAINED_NATIVE_PATHS
        "${PORT_ROOT}/vendor/encore-active/eden-core/src/common/fs/path_util.cpp")
    if(NOT EXISTS "${EDEN_MAINTAINED_NATIVE_PATHS}")
        message(FATAL_ERROR "Missing maintained native filesystem path source")
    endif()
    get_target_property(common_sources common SOURCES)
    # Compile the native common thread-name diagnostic from maintained C++.
    set(EDEN_MAINTAINED_NATIVE_THREAD
        "${PORT_ROOT}/vendor/encore-active/eden-core/src/common/thread.cpp")
    if(NOT EXISTS "${EDEN_MAINTAINED_NATIVE_THREAD}")
        message(FATAL_ERROR "Missing maintained common thread source")
    endif()
    list(REMOVE_ITEM common_sources thread.cpp)
    list(APPEND common_sources "${EDEN_MAINTAINED_NATIVE_THREAD}")
    # PS5 advertises invariant TSC but no CPUID leaf0x15. The original fallback
    # was inside that leaf's branch, leaving frequency zero on this hardware.
    # Native invariant TSC fallback is maintained C++, not configure-time surgery.
    set(EDEN_MAINTAINED_NATIVE_CPU_FEATURES
        "${PORT_ROOT}/vendor/encore-active/eden-core/src/common/cpu_features.cpp")
    if(NOT EXISTS "${EDEN_MAINTAINED_NATIVE_CPU_FEATURES}")
        message(FATAL_ERROR "Missing maintained native CPU frequency source")
    endif()
    list(REMOVE_ITEM common_sources cpu_features.cpp)
    list(APPEND common_sources "${EDEN_MAINTAINED_NATIVE_CPU_FEATURES}")
    # Native directory enumeration retains the prior helper verbatim.
    set(EDEN_MAINTAINED_NATIVE_FS
        "${PORT_ROOT}/vendor/encore-active/eden-core/src/common/fs/fs.cpp")
    if(NOT EXISTS "${EDEN_MAINTAINED_NATIVE_FS}")
        message(FATAL_ERROR "Missing maintained common filesystem source")
    endif()
    list(REMOVE_ITEM common_sources fs/fs.cpp)
    list(APPEND common_sources "${EDEN_MAINTAINED_NATIVE_FS}")
    list(REMOVE_ITEM common_sources fs/path_util.cpp)
    list(APPEND common_sources "${EDEN_MAINTAINED_NATIVE_PATHS}")
    target_include_directories(common PRIVATE "${EDEN_PORT_DIR}")
    set_property(TARGET common PROPERTY SOURCES "${common_sources}")
    # Prefer this build's matching decoder headers over the C dependency
    # bundle's older FFmpeg headers exposed through OpenSSL's include root.
    target_include_directories(video_core BEFORE PRIVATE "${FFmpeg_INCLUDE_DIR}")
    # The older SDK omits DCCP's IP protocol name (wire value 33, also used by
    # Service::Sockets::Protocol). socket() still decides runtime support.
    get_target_property(core_sources core SOURCES)
    # Observe permitted *guest* DNS/traffic at its own HLE IPC/socket boundary,
    # after the cached R295 domain filter patch is applied to pinned Eden.
    # No packets are edited, no host resolver setting is changed, and these
    # wrappers are completely silent when Detailed Logging is disabled.
    # The audited resolver is owned by Encore; no C++ substitutions in CMake.
    set(EDEN_MAINTAINED_GUEST_DNS
        "${PORT_ROOT}/vendor/encore-active/eden-core/src/core/hle/service/sockets/sfdnsres.cpp")
    if(NOT EXISTS "${EDEN_MAINTAINED_GUEST_DNS}")
        message(FATAL_ERROR "Missing maintained guest DNS resolver")
    endif()
    list(REMOVE_ITEM core_sources hle/service/sockets/sfdnsres.cpp)
    list(APPEND core_sources "${EDEN_MAINTAINED_GUEST_DNS}")

    # Guest socket audit instrumentation is a complete Encore-maintained source.
    # Preserve shipping BSD backports; do not rewrite C++ during configure.
    set(EDEN_MAINTAINED_GUEST_BSD
        "${PORT_ROOT}/vendor/encore-active/eden-core/src/core/hle/service/sockets/bsd.cpp")
    if(NOT EXISTS "${EDEN_MAINTAINED_GUEST_BSD}")
        message(FATAL_ERROR "Missing maintained audited guest BSD source")
    endif()
    list(REMOVE_ITEM core_sources hle/service/sockets/bsd.cpp)
    list(APPEND core_sources "${EDEN_MAINTAINED_GUEST_BSD}")

    # Keep immutable firmware outside the small writable title-data quota.
    # Native BISFactory declaration is kept in a narrowly scoped include root.
    # Do not expose the whole encore-core/src tree as an include override.
    set(EDEN_MAINTAINED_BIS_INCLUDE_ROOT
        "${PORT_ROOT}/vendor/encore-active/eden-core/include")
    set(EDEN_MAINTAINED_BIS_HEADER
        "${EDEN_MAINTAINED_BIS_INCLUDE_ROOT}/core/file_sys/bis_factory.h")
    set(EDEN_MAINTAINED_BIS_SOURCE
        "${PORT_ROOT}/vendor/encore-active/eden-core/src/core/file_sys/bis_factory.cpp")
    if(NOT EXISTS "${EDEN_MAINTAINED_BIS_HEADER}" OR NOT EXISTS "${EDEN_MAINTAINED_BIS_SOURCE}")
        message(FATAL_ERROR "Missing maintained native BISFactory pair")
    endif()
    # Prevent an older configure's derived header shadowing the tracked ABI.
    file(REMOVE "${PORT_BUILD_DIR}/include/core/file_sys/bis_factory.h")
    target_include_directories(core BEFORE PUBLIC "${EDEN_MAINTAINED_BIS_INCLUDE_ROOT}")
    list(REMOVE_ITEM core_sources file_sys/bis_factory.cpp)
    list(APPEND core_sources "${EDEN_MAINTAINED_BIS_SOURCE}")
    # Use the tracked source for native firmware lookup.
    set(EDEN_MAINTAINED_NATIVE_FILESYSTEM
        "${PORT_ROOT}/vendor/encore-active/eden-core/src/core/hle/service/filesystem/filesystem.cpp")
    if(NOT EXISTS "${EDEN_MAINTAINED_NATIVE_FILESYSTEM}")
        message(FATAL_ERROR "Missing maintained native filesystem source")
    endif()
    list(REMOVE_ITEM core_sources hle/service/filesystem/filesystem.cpp)
    list(APPEND core_sources "${EDEN_MAINTAINED_NATIVE_FILESYSTEM}")
    # A single checked-in native socket-wakeup implementation; no CMake C++ rewrites.
    set(EDEN_NATIVE_NETWORK_SOURCE
        "${PORT_ROOT}/vendor/encore-active/eden-core/src/core/internal_network/network.cpp")
    if(NOT EXISTS "${EDEN_NATIVE_NETWORK_SOURCE}")
        message(FATAL_ERROR "Missing maintained native network source")
    endif()
    list(REMOVE_ITEM core_sources internal_network/network.cpp)
    list(APPEND core_sources "${EDEN_NATIVE_NETWORK_SOURCE}")
    # Reuse the getifaddrs path instead of newer BSD route-format helpers.
    # Keep its existing zero-gateway fallback; PS5 route discovery is unqualified.
    list(REMOVE_ITEM core_sources internal_network/network_interface.cpp)
    # Native interface enumeration selects the maintained FreeBSD branch.
    set(EDEN_MAINTAINED_NATIVE_NET_INTERFACES
        "${PORT_ROOT}/vendor/encore-active/eden-core/src/core/internal_network/network_interface.cpp")
    if(NOT EXISTS "${EDEN_MAINTAINED_NATIVE_NET_INTERFACES}")
        message(FATAL_ERROR "Missing maintained native network interface source")
    endif()
    list(APPEND core_sources "${EDEN_MAINTAINED_NATIVE_NET_INTERFACES}")
    set_property(TARGET core PROPERTY SOURCES "${core_sources}")
    # Eden only uses Boost.Process v1's header-only async_pipe. Its unused v2
    # library assumes newer FreeBSD process APIs than the PS5 SDK supplies.
    foreach(property LINK_LIBRARIES INTERFACE_LINK_LIBRARIES)
        get_target_property(libraries core ${property})
        list(REMOVE_ITEM libraries Boost::process)
        set_property(TARGET core PROPERTY ${property} "${libraries}")
    endforeach()
    target_include_directories(core PRIVATE "$<TARGET_PROPERTY:boost_process,INTERFACE_INCLUDE_DIRECTORIES>")
    target_link_libraries(core PRIVATE "$<TARGET_PROPERTY:boost_process,INTERFACE_LINK_LIBRARIES>")
    set(native_template "${PORT_ROOT}/../ps5-native-app-boilerplate")
    # Compile one complete maintained allocator variant; never synthesize C here.
    option(EDEN_HEAP_ARENAS "Per-thread arenas inside the owned heap" ON)
        set(EDEN_ACTIVE_HEAP_DIR "${PORT_ROOT}/vendor/encore-active/eden-build/tooling/native")
    if(EDEN_HEAP_ARENAS)
        set(EDEN_HEAP_UNIT "app_heap_arenas.c")
    else()
        set(EDEN_HEAP_UNIT "app_heap_flat.c")
    endif()
    set(EDEN_HEAP_SOURCE "${EDEN_ACTIVE_HEAP_DIR}/${EDEN_HEAP_UNIT}")
    if(NOT EXISTS "${EDEN_HEAP_SOURCE}" OR NOT EXISTS "${EDEN_ACTIVE_HEAP_DIR}/heap_guard.h")
        message(FATAL_ERROR "Missing maintained Encore heap source or guard header")
    endif()
    set(eden_app_crt "${native_template}/tooling/native/app_crt.cpp")
    if(EDEN_PS5_VULKAN AND EDEN_VULKAN_DRIVER STREQUAL "RADV")
        # The native RADV startup is a complete, reviewed boilerplate override.
        # CMake selects it directly; no inline source rewriting.
        set(EDEN_MAINTAINED_RADV_CRT
            "${PORT_ROOT}/vendor/encore-active/eden-build/tooling/native/app_crt_radv.cpp")
        if(NOT EXISTS "${EDEN_MAINTAINED_RADV_CRT}")
            message(FATAL_ERROR "Missing maintained native RADV CRT")
        endif()
        set(eden_app_crt "${EDEN_MAINTAINED_RADV_CRT}")
    endif()
    add_executable(eden-headless "${EDEN_PORT_DIR}/main.cpp" "${PORT_ROOT}/src/aligned_alloc.c"
        "${EDEN_PORT_DIR}/heap_pages.cpp" "${EDEN_PORT_DIR}/performance.cpp"
        "${EDEN_PORT_DIR}/crash_report.cpp" "${EDEN_PORT_DIR}/stop_limit.cpp"
        "${EDEN_PORT_DIR}/elevation/elevation.cpp" "${EDEN_PORT_DIR}/ps5_net_compat.c"
        "${EDEN_PORT_DIR}/network_domain_rules.c"
        "${EDEN_PORT_DIR}/network_audit.c"
        "${EDEN_PORT_DIR}/network_audit_sockets.c"
        "${eden_app_crt}" "${PORT_ROOT}/src/lifecycle.c"
        "${EDEN_HEAP_SOURCE}")
    # Guest DNS IPC and native launcher both call eden_network_host_blocked(),
    # supplied once by eden-headless's native network_domain_rules.c.
    # The guest derived DNS source includes the matching policy prototype.
    target_include_directories(core PRIVATE "${EDEN_PORT_DIR}")
target_compile_definitions(eden-headless PRIVATE PS5_NATIVE=1)
    # Only main.cpp needs to recompile when the SHA changes. The stable
    # video_core and other native app objects keep their incremental caches.
    if(NOT DEFINED EDEN_ENCORE_SOURCE_COMMIT)
        set(EDEN_ENCORE_SOURCE_COMMIT "unknown")
    endif()
    if(NOT EDEN_ENCORE_SOURCE_COMMIT STREQUAL "unknown")
        string(LENGTH "${EDEN_ENCORE_SOURCE_COMMIT}" encore_commit_len)
        if(NOT encore_commit_len EQUAL 40 OR
           NOT EDEN_ENCORE_SOURCE_COMMIT MATCHES "^[0-9a-f]+$")
            message(FATAL_ERROR "EDEN_ENCORE_SOURCE_COMMIT must be a 40-char lowercase Git SHA")
        endif()
    endif()
    set_property(SOURCE "${EDEN_PORT_DIR}/main.cpp" APPEND PROPERTY
        COMPILE_DEFINITIONS "EDEN_NATIVE_SOURCE_COMMIT=\"${EDEN_ENCORE_SOURCE_COMMIT}\"")
    # Native-title libc rejects socket fcntl and its resolver may depend on an
    # unloaded WebKit module. ps5_net_compat.c supplies sceNetResolver DNS and
    # translates only refused socket flags to native SO_NBIO.
    target_link_options(eden-headless PRIVATE -Wl,--wrap=fcntl
        -Wl,--wrap=connect -Wl,--wrap=send -Wl,--wrap=sendto
        -Wl,--wrap=recv -Wl,--wrap=recvfrom)
    set_property(TARGET eden-headless APPEND PROPERTY LINK_DEPENDS
        "${PORT_ROOT}/tools/link-headless-native.sh" "${PORT_ROOT}/tools/unwind.ld"
        "${PORT_ROOT}/tools/app-symbols.map")
    if(EDEN_PS5_VULKAN AND EDEN_VULKAN_DRIVER STREQUAL "RADV")
        set_property(TARGET eden-headless APPEND PROPERTY LINK_DEPENDS
            "${PORT_ROOT}/tools/radv-link-eden.sh"
            "${PORT_ROOT}/../mihawk-vulkan-review/tools/radv-link.sh")
    endif()
    target_compile_definitions(common PRIVATE PS5_NATIVE=1 YUZU_BUNDLED_OPENSSL=1)
else()
    add_executable(eden-headless "${EDEN_PORT_DIR}/main.cpp" "${PORT_ROOT}/src/aligned_alloc.c")
    target_link_options(eden-headless PRIVATE -Wl,--wrap=aligned_alloc)
    add_executable(eden-romfs-check "${EDEN_PORT_DIR}/romfs_check.cpp")
    target_include_directories(eden-romfs-check PRIVATE "${PROJECT_SOURCE_DIR}/src")
    target_link_libraries(eden-romfs-check PRIVATE core)
    target_compile_options(eden-romfs-check PRIVATE -fno-rtti)
    add_executable(eden-scalar-check "${EDEN_PORT_DIR}/scalar_check.cpp")
    target_include_directories(eden-scalar-check PRIVATE "${PROJECT_SOURCE_DIR}/src")
    target_link_libraries(eden-scalar-check PRIVATE dynarmic)
    add_executable(eden-memory-check "${EDEN_PORT_DIR}/memory_check.cpp")
    target_include_directories(eden-memory-check PRIVATE "${PROJECT_SOURCE_DIR}/src")
    target_link_libraries(eden-memory-check PRIVATE dynarmic common)
    target_compile_definitions(eden-memory-check PRIVATE EDEN_SHARED_JIT_AVAILABLE=0)
    target_compile_options(eden-scalar-check PRIVATE -fno-rtti)
    add_executable(eden-ryujinx-check "${EDEN_PORT_DIR}/ryujinx_check.cpp")
    # Run on the host: whole shader cache entries survive a damaged tail.
    add_executable(eden-shader-cache-check "${EDEN_PORT_DIR}/shader_cache_check.cpp")
    target_include_directories(eden-shader-cache-check PRIVATE "${PROJECT_SOURCE_DIR}/src")
    target_link_libraries(eden-shader-cache-check PRIVATE video_core)
    target_compile_options(eden-shader-cache-check PRIVATE -fno-rtti)
    add_executable(eden-mods-check "${EDEN_PORT_DIR}/mods_check.cpp")
    target_include_directories(eden-mods-check PRIVATE "${PROJECT_SOURCE_DIR}/src")
    target_link_libraries(eden-mods-check PRIVATE core)
    target_compile_options(eden-mods-check PRIVATE -fno-rtti)
    # The settings store's check is written with assert(): they stay in a release build.
    add_executable(eden-settings-check "${EDEN_PORT_DIR}/preferences_check.cpp")
    target_link_libraries(eden-settings-check PRIVATE core)
    target_compile_options(eden-settings-check PRIVATE -UNDEBUG)
    add_executable(eden-devices-check "${EDEN_PORT_DIR}/devices_check.cpp")
    target_link_libraries(eden-devices-check PRIVATE core eden-pad eden-device-mock)
    target_compile_options(eden-devices-check PRIVATE -fno-rtti)
endif()
target_include_directories(eden-headless PRIVATE "${PROJECT_SOURCE_DIR}/src")
# The R-label is injected by the native compiler, independently of sce_sys.
set(EDEN_LAUNCHER_BUILD_LABEL "" CACHE STRING "Exact Eden Encore compiled R revision (required for native builds)")
if(NOT EDEN_LAUNCHER_BUILD_LABEL MATCHES "^R[0-9]+$")
    message(FATAL_ERROR "Missing/invalid Eden R revision: provide -DEDEN_LAUNCHER_BUILD_LABEL=R<number> via the native build tool; no default R1")
endif()
set(EDEN_LAUNCHER_PACKAGE_VERSION "" CACHE STRING "Numeric PS5 contentVersion derived from R revision")
if(PS5_NATIVE AND NOT EDEN_LAUNCHER_PACKAGE_VERSION MATCHES "^[0-9][0-9][.][0-9][0-9][0-9][.][0-9][0-9][0-9]$")
    message(FATAL_ERROR "Missing or invalid compiled native PS5 contentVersion")
endif()
target_compile_definitions(eden-headless PRIVATE
    EDEN_LAUNCHER_BUILD_LABEL=\"${EDEN_LAUNCHER_BUILD_LABEL}\"
    EDEN_LAUNCHER_PACKAGE_VERSION=\"${EDEN_LAUNCHER_PACKAGE_VERSION}\"
    EDEN_SHARED_JIT_AVAILABLE=0
    EDEN_JIT_COMPILE_BATCH_AVAILABLE=0)
target_link_libraries(eden-headless PRIVATE core eden-pad)
add_library(eden-metadata STATIC "${EDEN_PORT_DIR}/metadata_bridge.cpp")
target_include_directories(eden-metadata PUBLIC "${EDEN_PORT_DIR}" PRIVATE "${PROJECT_SOURCE_DIR}/src")
target_link_libraries(eden-metadata PUBLIC core stb PRIVATE ZLIB::ZLIB)
target_compile_options(eden-metadata PRIVATE -fno-rtti -Wall -Wextra -Werror -Wno-unused-parameter)
if(PS5_NATIVE)
    target_compile_options(eden-metadata PRIVATE -femulated-tls)
endif()
add_dependencies(eden-headless eden-metadata)

# N76 -- NS2 guest CNTPCT calibration through Encore's shared CPU/JIT.
# Upstream-compatible guest tick semantics selected by the reviewed NPDM; NS1 unchanged.
# N76 now follows the reviewed dual-NPDM loader automatically on PS5.
# A single PS5 release can select the real NS2 31.25 MHz timer per program
# while preserving 19.2 MHz for every first-generation title. The shared
# optimized G11 JIT and common clock are already maintained and host-tested.
# This is NOT the six-core scheduler or experimental A64 decoder.
set(EDEN_SHARED_NS2_GUEST_COUNTER OFF)
if(PS5_NATIVE AND EDEN_REVIEWED_DUAL_NPDM)
    set(EDEN_SHARED_NS2_GUEST_COUNTER ON)
endif()
if(EDEN_SHARED_NS2_GUEST_COUNTER)
    if(NOT PS5_NATIVE OR NOT EDEN_REVIEWED_DUAL_NPDM)
        message(FATAL_ERROR "N76 requires native PS5 with the reviewed dual-NPDM loader")
    endif()
    set(EDEN_N76_CLOCK_ROOT
        "${PORT_ROOT}/vendor/encore-active/eden-core")
    set(EDEN_N76_GUEST_COUNTER_HEADER
        "${EDEN_N76_CLOCK_ROOT}/include/encore/guest_counter_policy.h")
    set(EDEN_N76_NATIVE_CPU_SOURCE
        "${EDEN_N76_CLOCK_ROOT}/src/common/cpu_features.cpp")
    # G11 has already replaced the upstream A64 translation unit.
    # Keep its fully optimized native owner and graft the opt-in counter
    # contract into it; never silently replace it with a legacy source.
    set(EDEN_N76_G11_PROFILE normal)
    set(EDEN_N76_NATIVE_JIT_SOURCE
        "${EDEN_N76_CLOCK_ROOT}/src/core/arm/dynarmic/g11/arm_dynarmic_64_native_${EDEN_N76_G11_PROFILE}.cpp")
    foreach(n76_file IN ITEMS
        "${EDEN_N76_GUEST_COUNTER_HEADER}"
        "${EDEN_N76_CLOCK_ROOT}/include/common/cpu_features.h"
        "${EDEN_N76_NATIVE_CPU_SOURCE}"
        "${EDEN_N76_NATIVE_JIT_SOURCE}")
        if(NOT EXISTS "${n76_file}")
            message(FATAL_ERROR "N76 missing maintained vendor clock owner: ${n76_file}")
        endif()
    endforeach()
    get_target_property(n76_common_sources common SOURCES)
    list(FIND n76_common_sources
        "${EDEN_N76_NATIVE_CPU_SOURCE}" n76_clock_owner_idx)
    if(n76_clock_owner_idx EQUAL -1)
        message(FATAL_ERROR "N76 real native common clock owner is not compiled")
    endif()
    get_target_property(n76_core_sources core SOURCES)
    list(FIND n76_core_sources "${EDEN_N76_NATIVE_JIT_SOURCE}"
         n76_selected_g11_owner_idx)
    if(n76_selected_g11_owner_idx EQUAL -1)
        message(FATAL_ERROR "N76 requires the existing, optimized G11 native A64 owner")
    endif()
    list(FIND n76_core_sources "arm/dynarmic/arm_dynarmic_64.cpp"
         n76_legacy_owner_idx)
    if(NOT n76_legacy_owner_idx EQUAL -1)
        message(FATAL_ERROR "N76 must not compile the unqualified legacy A64 owner")
    endif()
    # Switch 1 selects 19.2 MHz at its original ExeFS handoff, while NS2
    # selects 31.25 MHz only AFTER the full patched-NSO bounds preflight.
    # This keeps malformed NS2 titles from changing the next title's clock;
    # G11 retains the optimized native owner.
    # The dedicated host selector guard verifies the opt-in G11 source bytes.
    # The GPU report-timestamp owner must see the SAME metadata-selected
    # guest generation as the A64/JIT and loader. No global NS2 GPU mode
    # and no compile-time change to NS1's GPU-tick clock domain.
    foreach(n76_target IN ITEMS core common eden-headless video_core)
        target_compile_definitions(${n76_target} PRIVATE EDEN_NS2_GUEST_COUNTER=1)
        target_include_directories(${n76_target} BEFORE PRIVATE
            "${EDEN_N76_CLOCK_ROOT}/include")
    endforeach()
endif()

option(EDEN_HOST_ASAN "Instrument host emulator code for memory diagnostics" OFF)
if(EDEN_HOST_ASAN)
    if(PS5_NATIVE)
        message(FATAL_ERROR "EDEN_HOST_ASAN is a Linux host diagnostic only")
    endif()
    # Generated guest instructions and custom fiber stacks are not covered.
    foreach(asan_target common core audio_core video_core hid_core eden-pad eden-device-mock eden-headless)
        target_compile_options(${asan_target} PRIVATE -fsanitize=address -g1 -fno-omit-frame-pointer
            -fno-sanitize-address-use-after-scope -fsanitize-address-use-after-return=never)
    endforeach()
    target_link_options(eden-headless PRIVATE -fsanitize=address)
endif()
target_compile_options(eden-headless PRIVATE -Wall -Wextra -Werror -Wno-unused-parameter -fwrapv $<$<COMPILE_LANGUAGE:CXX>:-fno-rtti>)
if(PS5_NATIVE)
    target_compile_options(eden-headless PRIVATE -femulated-tls)
    # One maintained native controller/audio frontend source graph.
    target_compile_definitions(eden-headless PRIVATE EDEN_DEVICE_FRONTEND=0)
endif()

# Consume the frozen, relocatable 4.6 SDK as one complete profile.
option(EDEN_PS5_OPENGL "Use the PS5 EGL/OpenGL frontend" OFF)
if(EDEN_PS5_OPENGL)
    if(NOT PS5_NATIVE OR NOT ENABLE_OPENGL)
        message(FATAL_ERROR "PS5 graphics requires the native OpenGL build")
    endif()
    # Audited PS5 OpenGL source snapshot. It includes SDK 1.0.1 plus the reviewed post-release
    # constant-buffer/alignment and scanout-flush fixes; tools/build-opengl-sdk.sh verifies its
    # source commit and installed manifest before CMake sees it.
    set(gl46 "${PORT_ROOT}/.local/ps5-opengl-sdk-ad2807d")
    set(gl46_commit "ad2807d41cef2681882a9ee0d20808779f74b7cd")
    if(NOT EXISTS "${gl46}/lib/libps5_opengl_core33.a" OR NOT EXISTS "${gl46}/manifest.sha256" OR
       NOT EXISTS "${gl46}/ENCORE_SOURCE_COMMIT")
        message(FATAL_ERROR "Missing audited PS5 OpenGL SDK in ${gl46}; run make prepare")
    endif()
    file(READ "${gl46}/ENCORE_SOURCE_COMMIT" gl46_built_commit)
    string(STRIP "${gl46_built_commit}" gl46_built_commit)
    if(NOT gl46_built_commit STREQUAL gl46_commit)
        message(FATAL_ERROR "Frozen OpenGL source commit changed: ${gl46_built_commit}")
    endif()
    file(SHA256 "${gl46}/manifest.sha256" gl46_manifest_hash)
    set(PS5OpenGL_DIR "${gl46}/lib/cmake/PS5OpenGL" CACHE PATH "Frozen Eden graphics SDK" FORCE)
    find_package(PS5OpenGL CONFIG REQUIRED PATHS "${gl46}/lib/cmake/PS5OpenGL" NO_DEFAULT_PATH NO_CMAKE_FIND_ROOT_PATH)
    target_sources(eden-headless PRIVATE "${EDEN_PORT_DIR}/graphics.cpp")
    # The loading screen's shader as a string for the OpenGL window; the Vulkan HUD pass includes
    # the same two files (vulkan_hud.frag).
    file(READ "${EDEN_PORT_DIR}/loading_wordmark.glsl" loading_wordmark)
    file(READ "${EDEN_PORT_DIR}/loading_scene.glsl" loading_scene)
    set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS
        "${EDEN_PORT_DIR}/loading_wordmark.glsl" "${EDEN_PORT_DIR}/loading_scene.glsl")
    write_derived("${PORT_BUILD_DIR}/include/loading_scene_glsl.h"
        "// Generated from loading_wordmark.glsl and loading_scene.glsl.\n#pragma once\ninline constexpr const char* kLoadingSceneGlsl = R\"glsl(\n${loading_wordmark}${loading_scene})glsl\";\n")
    target_compile_definitions(eden-headless PRIVATE EDEN_PS5_OPENGL=1)
    target_link_libraries(eden-headless PRIVATE PS5OpenGL::OpenGL glad)
endif()
    # Launcher UI: its own small OpenGL renderer, mixer and screens (headless/prosperoeden/pe),
    # all gone before a game starts.
    if(PS5_NATIVE)
        set(launcher_dir "${EDEN_PORT_DIR}/prosperoeden")
        # Pinned BSD-licensed libwebp: background one-time encoding and decode.
        # inject.cmake registers the pinned WebP target before the deferred
        # add_eden_headless callback. No subdirectories may be created here.
        if(NOT TARGET webp OR NOT EXISTS "${EDEN_WEBP_ROOT}/CMakeLists.txt")
            message(FATAL_ERROR "Pinned libwebp target was not registered in project(yuzu)")
        endif()
        # The PS5 SDK is x86-64 (Zen 2), where SSE2 is baseline ABI.
        # Our default conservative -mno-sse2 flag breaks libwebp C scalar
        # routines returning doubles: clang reports "SSE2 register return
        # with SSE2 disabled". Restore only SSE2 for the pinned WebP object
        # libraries; keep globally disabled SIMD extensions and the
        # WEBP_ENABLE_SIMD=OFF policy unchanged. These CMake targets own
        # every WebP object linked into eden-headless (including SharpYUV).
        foreach(eden_webp_c_target IN ITEMS
                sharpyuv webpdecode webpdspdecode webputilsdecode
                webpencode webpdsp webputils webp webpdecoder)
            if(NOT TARGET ${eden_webp_c_target})
                message(FATAL_ERROR
                    "Missing pinned WebP ABI target: ${eden_webp_c_target}")
            endif()
            target_compile_options(${eden_webp_c_target} PRIVATE
                $<$<COMPILE_LANGUAGE:C>:-msse2>)
        endforeach()
        target_link_libraries(eden-headless PRIVATE webp)
        target_include_directories(eden-headless PRIVATE "${EDEN_WEBP_ROOT}/src")
        target_sources(eden-headless PRIVATE
            "${launcher_dir}/runtime_shims.cpp"
            "${launcher_dir}/radio_input.c")
        target_include_directories(eden-headless PRIVATE "${launcher_dir}" "${PORT_ROOT}/third_party")
        # native_app_update.cpp consumes the pinned CA bundle generated by
        # tools/build-headless-native.sh at the configured OpenSSL include root.
        target_include_directories(eden-headless PRIVATE "${OPENSSL_INCLUDE_DIR}")
        if(EDEN_PS5_OPENGL)
            set(launcher_sources
                "${launcher_dir}/frontend.cpp"
                "${launcher_dir}/eden_services.cpp"
                "${launcher_dir}/native_app_update.cpp"
                "${EDEN_PORT_DIR}/update_check/self_update_sha256.c"
                "${launcher_dir}/pe/audio/mixer.cpp"
                "${launcher_dir}/pe/audio/sounds.cpp"
                "${launcher_dir}/pe/audio/wav.cpp"
                "${launcher_dir}/pe/core/strings.cpp"
                "${launcher_dir}/pe/gfx/bidi.cpp"
                "${launcher_dir}/pe/gfx/draw_list.cpp"
                "${launcher_dir}/pe/gfx/font.cpp"
                "${launcher_dir}/pe/gfx/gl_batch.cpp"
                "${launcher_dir}/pe/gfx/gl_program.cpp"
                "${launcher_dir}/pe/gfx/harfbuzz.cpp"
                "${launcher_dir}/pe/gfx/image.cpp"
                "${launcher_dir}/pe/gfx/system_fonts.cpp"
                "${launcher_dir}/pe/platform/audio_out.cpp"
                "${launcher_dir}/pe/platform/display_egl.cpp"
                "${launcher_dir}/pe/ui/browse.cpp"
                "${launcher_dir}/pe/ui/home.cpp"
                "${launcher_dir}/room_directory.cpp"
                "${launcher_dir}/pe/ui/multiplayer.cpp"
                "${launcher_dir}/pe/ui/launcher.cpp"
                "${launcher_dir}/pe/ui/library.cpp"
                "${launcher_dir}/pe/ui/mapping.cpp"
                "${launcher_dir}/pe/ui/settings.cpp"
                "${launcher_dir}/pe/ui/switch_theme.cpp"
                "${launcher_dir}/pe/ui/textures.cpp"
                "${launcher_dir}/pe/ui/widgets.cpp")
            target_sources(eden-headless PRIVATE ${launcher_sources})
            # The launcher calls OpenGL by name (the SDK's headers), not through glad.
            set(launcher_definitions "GL_GLEXT_PROTOTYPES=1")
            if(EXISTS "${EDEN_PORT_DIR}/ryujinx_saves.h")
                list(APPEND launcher_definitions "EDEN_SAVE_IMPORT=1")
            endif()
            set_source_files_properties(${launcher_sources}
                PROPERTIES COMPILE_DEFINITIONS "${launcher_definitions}")
            # Text in the scripts the baked font lacks: the console's own fonts, shaped by HarfBuzz
            # (a pinned source release, tools/deps.json) and drawn through stb_truetype.
            set(harfbuzz_dir "${PORT_ROOT}/.deps/harfbuzz-12.3.2/src")
            if(NOT EXISTS "${harfbuzz_dir}/harfbuzz.cc")
                message(FATAL_ERROR "HarfBuzz is missing (${harfbuzz_dir}): run make deps")
            endif()
            set_source_files_properties(
                "${launcher_dir}/pe/gfx/system_fonts.cpp" "${launcher_dir}/pe/gfx/harfbuzz.cpp"
                PROPERTIES INCLUDE_DIRECTORIES "${harfbuzz_dir};${PORT_ROOT}/tools/launcher/stb")
            # HarfBuzz is not ours to tidy: its warnings are off.
            set_source_files_properties("${launcher_dir}/pe/gfx/harfbuzz.cpp" PROPERTIES COMPILE_OPTIONS "-w")
        else()
            target_sources(eden-headless PRIVATE "${launcher_dir}/frontend_stub.cpp")
        endif()
        target_link_libraries(eden-headless PRIVATE eden-metadata)
    endif()

if(EDEN_PS5_VULKAN)
    # Both backends import the same system module; use the superset facade.
    get_target_property(gl_imports PS5OpenGL::OpenGL INTERFACE_LINK_LIBRARIES)
    list(FILTER gl_imports EXCLUDE REGEX "/libSceAgcDriver[.]so$")
    list(APPEND gl_imports "${PORT_ROOT}/build/stubs/libSceAgcDriver.so")
    set_property(TARGET PS5OpenGL::OpenGL PROPERTY INTERFACE_LINK_LIBRARIES "${gl_imports}")
    target_compile_definitions(eden-headless PRIVATE EDEN_PS5_VULKAN=1)
    if(EDEN_VULKAN_DRIVER STREQUAL "RADV")
        target_compile_definitions(eden-headless PRIVATE EDEN_PS5_RADV=1)
    endif()
    target_include_directories(eden-headless BEFORE PRIVATE "${PORT_BUILD_DIR}/include")
endif()


# Capture reproducible GPU compatibility evidence without changing any
# Maxwell/Fermi instructions or swallowing unsupported feature failures.
include("${CMAKE_CURRENT_LIST_DIR}/gpu_native_observability.cmake")
# Disabled native GPU coherency bridge, explicit developer compilation only.
include("${CMAKE_CURRENT_LIST_DIR}/guest_write_deferred_bridge.cmake")

# Experimental ExeFS bridge must be selected AFTER all Encore-owned source
# substitutions (NCZ/XCZ and the PS5 16-KiB aligned NSO loader).
# The same maintained loader owns ordinary NS1 ExeFS and NS2 extracted
# programs in the ONE PS5 shipping binary. Preserve the audited PS5 NSO
# implementation and baseline kernel dispatcher in release; research-only
# NSO/SVC source replacements are not silently shipped.
set(EDEN_SHARED_NS2_EXEFS OFF)
if(PS5_NATIVE AND EDEN_REVIEWED_DUAL_NPDM)
    set(EDEN_SHARED_NS2_EXEFS ON)
endif()
if(EDEN_SHARED_NS2_EXEFS)
    if(NOT EDEN_REVIEWED_DUAL_NPDM)
        message(FATAL_ERROR "NS2 ExeFS requires the reviewed dual-generation NPDM reader")
    endif()
    set(eden_ns2_loader_origin
        "${PORT_ROOT}/vendor/encore-active/eden-core/src/core/loader/loader.cpp")
    if(PS5_NATIVE)
        set(eden_ns2_romdir_origin
            "${PORT_ROOT}/vendor/encore-active/eden-core/src/core/loader/deconstructed_rom_directory.cpp")
    else()
        set(eden_ns2_romdir_origin "loader/deconstructed_rom_directory.cpp")
    endif()
    get_target_property(eden_ns2_exefs_sources core SOURCES)
    foreach(eden_ns2_pair IN ITEMS
            "loader.cpp|${eden_ns2_loader_origin}"
            "deconstructed_rom_directory.cpp|${eden_ns2_romdir_origin}")
        string(REPLACE "|" ";" eden_ns2_parts "${eden_ns2_pair}")
        list(GET eden_ns2_parts 0 eden_ns2_basename)
        list(GET eden_ns2_parts 1 eden_ns2_original)
        list(FIND eden_ns2_exefs_sources "${eden_ns2_original}" eden_ns2_original_idx)
        if(eden_ns2_original_idx EQUAL -1)
            message(FATAL_ERROR "NS2 ExeFS owner changed: ${eden_ns2_original}")
        endif()
        set(eden_ns2_replacement
            "${EDEN_NS2_METADATA_OVERLAY}/core/loader/${eden_ns2_basename}")
        if(NOT EXISTS "${eden_ns2_replacement}")
            message(FATAL_ERROR "Missing NS2 ExeFS source: ${eden_ns2_replacement}")
        endif()
        list(REMOVE_ITEM eden_ns2_exefs_sources "${eden_ns2_original}")
        list(APPEND eden_ns2_exefs_sources "${eden_ns2_replacement}")
    endforeach()
    if(NOT EXISTS "${EDEN_NS2_CORE_HELPERS}/core/loader/deconstructed_rom_directory.h")
        message(FATAL_ERROR "Missing NS2 ExeFS maintained loader header")
    endif()
    # Select a complete maintained native PS5 NSO source, preserving sparse
    # BSS and ZBIC support. Do not accidentally fall back to pinned NSO.
    set_property(TARGET core PROPERTY SOURCES "${eden_ns2_exefs_sources}")
    if(EDEN_SHARED_NS2_EXEFS)
        message(STATUS "Encore unified PS5 ExeFS: NS1/NS2 loader + reviewed NPDM; retain native optimized NSO/SVC")
    endif()

endif()

# The Switch 2 GPU-access memory SVC is a validated kernel admission,
# not a simulated GPU mapping or a successful native submission. A separate
# exact NS2 process PID and memory-profile guard preserves NS1's SVC table.
set(EDEN_SHARED_NS2_GPU_ACCESS_SVC OFF)
if(PS5_NATIVE AND EDEN_REVIEWED_DUAL_NPDM)
    set(EDEN_SHARED_NS2_GPU_ACCESS_SVC ON)
endif()
if(EDEN_SHARED_NS2_GPU_ACCESS_SVC)
    set(EDEN_NS2_GPU_ACCESS_ROOT "${PORT_ROOT}/vendor/encore-active/ns2-runtime/gpu_access_svc")
    set(EDEN_NS2_GPU_ACCESS_SOURCE "${EDEN_NS2_GPU_ACCESS_ROOT}/core/hle/kernel/svc.cpp")
    if(NOT EXISTS "${EDEN_NS2_GPU_ACCESS_SOURCE}" OR
       NOT EXISTS "${EDEN_NS2_GPU_ACCESS_ROOT}/core/hle/kernel/svc_types.h" OR
       NOT EXISTS "${EDEN_NS2_GPU_ACCESS_ROOT}/core/hle/kernel/k_memory_block.h" OR
       NOT EXISTS "${EDEN_NS2_GPU_ACCESS_ROOT}/core/hle/kernel/ns2_gpu_memory_attribute.h" OR
       NOT EXISTS "${EDEN_NS2_CORE_HELPERS}/core/loader/ns2_svc_trace.h")
        message(FATAL_ERROR "Missing validated NS2 GPU-access SVC owner")
    endif()
    get_target_property(eden_ns2_gpu_access_sources core SOURCES)
    list(FIND eden_ns2_gpu_access_sources "hle/kernel/svc.cpp" eden_ns2_gpu_access_index)
    if(eden_ns2_gpu_access_index EQUAL -1)
        message(FATAL_ERROR "NS1 kernel SVC ownership changed: review NS2 GPU-access selector")
    endif()
    list(REMOVE_ITEM eden_ns2_gpu_access_sources "hle/kernel/svc.cpp")
    list(APPEND eden_ns2_gpu_access_sources "${EDEN_NS2_GPU_ACCESS_SOURCE}")
    set_property(TARGET core PROPERTY SOURCES "${eden_ns2_gpu_access_sources}")
    # All consumers of the kernel's u8 memory attributes must agree on the
    # same 0x20 enum value; otherwise QueryMemory may hide the stored bit.
    # The two maintained headers keep the complete pinned NS1 structures.
    target_include_directories(core BEFORE PUBLIC "${EDEN_NS2_GPU_ACCESS_ROOT}")
    target_include_directories(video_core BEFORE PRIVATE "${EDEN_NS2_GPU_ACCESS_ROOT}")
endif()

# P1.3: Switch 2 uses SVC arbitration type 3 (WaitIfEqual64), including
# the high 32 bits. Select one reviewed kernel owner for both guests when
# native dual-NPDM release is configured. Types 0/1/2 retain the original
# 32-bit compare and alignment semantics; no alternate kernel/worker exists.
set(EDEN_SHARED_NS2_WAIT64 OFF)
if(EDEN_SHARED_NS2_GPU_ACCESS_SVC)
    set(EDEN_SHARED_NS2_WAIT64 ON)
    set(EDEN_NS2_WAIT64_ROOT
        "${PORT_ROOT}/vendor/encore-active/ns2-runtime/kernel_wait64")
    foreach(eden_ns2_wait_header IN ITEMS
            "core/hle/kernel/k_address_arbiter.h"
            "core/hle/kernel/k_process.h"
            "core/hle/kernel/svc.h")
        if(NOT EXISTS "${EDEN_NS2_WAIT64_ROOT}/${eden_ns2_wait_header}")
            message(FATAL_ERROR "Missing common NS2 64-bit arbiter header: ${eden_ns2_wait_header}")
        endif()
    endforeach()
    get_target_property(eden_wait64_sources core SOURCES)
    foreach(eden_wait64_owner IN ITEMS
            "hle/kernel/k_address_arbiter.cpp"
            "hle/kernel/svc/svc_address_arbiter.cpp")
        # The PS5 guest-threading CMake module has already promoted its
        # reviewed 32-bit HLE source. Replace THAT exact source with the
        # combined Wait64 + validity/overflow owner, never add two owners.
        set(eden_wait64_selected_source "${eden_wait64_owner}")
        list(FIND eden_wait64_sources "${eden_wait64_selected_source}" eden_wait64_index)
        if(eden_wait64_index LESS 0 AND PS5_NATIVE)
            # The maintained threading module has already replaced pinned HLE
            # sources with absolute paths. PORT_ROOT may still contain /headless/..
            # while CMAKE_CURRENT_LIST_DIR in the module is canonical: compare
            # existing source files by real path, never by their spelling.
            get_filename_component(eden_wait64_reviewed_real
                "${PORT_ROOT}/vendor/encore-active/eden-threading/src/core/${eden_wait64_owner}"
                REALPATH)
            foreach(eden_wait64_candidate IN LISTS eden_wait64_sources)
                if(IS_ABSOLUTE "${eden_wait64_candidate}" AND
                   EXISTS "${eden_wait64_candidate}")
                    get_filename_component(eden_wait64_candidate_real
                        "${eden_wait64_candidate}" REALPATH)
                    if(eden_wait64_candidate_real STREQUAL eden_wait64_reviewed_real)
                        set(eden_wait64_selected_source "${eden_wait64_candidate}")
                        list(FIND eden_wait64_sources
                            "${eden_wait64_selected_source}" eden_wait64_index)
                        break()
                    endif()
                endif()
            endforeach()
        endif()
        if(eden_wait64_index LESS 0)
            message(FATAL_ERROR "Missing unified address arbiter owner: ${eden_wait64_owner}")
        endif()
        set(eden_wait64_replacement
            "${EDEN_NS2_WAIT64_ROOT}/core/${eden_wait64_owner}")
        if(NOT EXISTS "${eden_wait64_replacement}")
            message(FATAL_ERROR "Reviewed address arbiter source missing: ${eden_wait64_replacement}")
        endif()
        list(REMOVE_ITEM eden_wait64_sources "${eden_wait64_selected_source}")
        list(APPEND eden_wait64_sources "${eden_wait64_replacement}")
    endforeach()
    set_property(TARGET core PROPERTY SOURCES "${eden_wait64_sources}")
    # Keep class layouts and inline method signatures identical in every
    # consumer; the GPU service may include KProcess through its core ABI.
    target_include_directories(core BEFORE PUBLIC "${EDEN_NS2_WAIT64_ROOT}")
    target_include_directories(video_core BEFORE PRIVATE "${EDEN_NS2_WAIT64_ROOT}")
    message(STATUS "Encore common kernel arbitration: 32-bit legacy + native WaitIfEqual64")
endif()

# N52: the shared PS5 ExeFS loader registers the actual NS2 KProcess PID.
# Admit a guest only if its native kernel Run succeeds; preserve the original
# NS1 Process::Run path when no NS2 PID is registered, without title hacks.
if(PS5_NATIVE AND EDEN_REVIEWED_DUAL_NPDM AND
   EDEN_SHARED_NS2_EXEFS)
    set(EDEN_NS2_NATIVE_PROCESS_SOURCE
        "${PORT_ROOT}/vendor/encore-active/ns2-runtime/process/core/hle/service/os/process.cpp")
    if(NOT EXISTS "${EDEN_NS2_NATIVE_PROCESS_SOURCE}")
        message(FATAL_ERROR "N52 maintained native Process::Run owner missing")
    endif()
    get_target_property(eden_ns2_process_sources core SOURCES)
    list(FIND eden_ns2_process_sources "hle/service/os/process.cpp" eden_ns2_process_source_idx)
    if(eden_ns2_process_source_idx EQUAL -1)
        message(FATAL_ERROR "N52 original Process::Run owner is not selected")
    endif()
    list(REMOVE_ITEM eden_ns2_process_sources "hle/service/os/process.cpp")
    list(APPEND eden_ns2_process_sources "${EDEN_NS2_NATIVE_PROCESS_SOURCE}")
    set_property(TARGET core PROPERTY SOURCES "${eden_ns2_process_sources}")
    target_compile_definitions(core PRIVATE EDEN_NS2_PROCESS_RUN_GUARD=1)
    target_include_directories(core BEFORE PRIVATE
        "${PORT_ROOT}/vendor/encore-active/ns2-helpers/include")
endif()

# P0.2: limited A64 LDAPR promotion for the unified PS5 JIT. It uses the
# original pinned Dynarmic decoder and load/store owner with one reviewed
# instruction, not the unvalidated RETAA/PAC or LSE research extensions.
# This runs only in the reviewed final dual-NPDM target and is independent
# of the opt-in research flags (which remain explicitly forbidden at release).
set(EDEN_SHARED_NS2_A64_LDAPR OFF)
if(PS5_NATIVE AND EDEN_REVIEWED_DUAL_NPDM)
    set(EDEN_SHARED_NS2_A64_LDAPR ON)
    set(EDEN_A64_LDAPR_SOURCE_ROOT
        "${PORT_ROOT}/vendor/sources/eden/src/dynarmic/src")
    set(EDEN_A64_LDAPR_OUTPUT_ROOT "${PORT_BUILD_DIR}/include")
    include("${CMAKE_CURRENT_LIST_DIR}/shared_a64_ldapr.cmake")
    # Dynarmic's a64.h includes ./a64.inc, and a64_translate.cpp includes
    # load_store_exclusive.cpp as source text. All 4 generated files must
    # resolve under one include root, before the vendored Dynarmic headers.
    target_include_directories(dynarmic BEFORE PRIVATE "${EDEN_A64_LDAPR_OUTPUT_ROOT}")
    message(STATUS "Encore shared A64: reviewed LDAPR acquire (LDAR), no PAC/LSE research")
endif()

# Unified NS2 six-core kernel owner; each process retains its physical
# affinity and NS1 tick cadence. No DEV or roadmap profile selection.
if(PS5_NATIVE AND EDEN_REVIEWED_DUAL_NPDM)
    set(EDEN_NS2_CPU6_ROOT "${PORT_ROOT}/vendor/encore-active/ns2-runtime/cpu6")
    foreach(eden_ns2_cpu6_header IN ITEMS
            "core/hardware_properties.h"
            "dynarmic/interface/exclusive_monitor.h")
        if(NOT EXISTS "${EDEN_NS2_CPU6_ROOT}/${eden_ns2_cpu6_header}")
            message(FATAL_ERROR "Missing experimental NS2 6-core header ${eden_ns2_cpu6_header}")
        endif()
    endforeach()
    target_include_directories(core BEFORE PUBLIC "${EDEN_NS2_CPU6_ROOT}")
    target_include_directories(dynarmic BEFORE PUBLIC "${EDEN_NS2_CPU6_ROOT}")
    target_include_directories(eden-headless BEFORE PRIVATE "${EDEN_NS2_CPU6_ROOT}")
    # The R457 unstripped ELF proves an ODR layout mismatch: core constructs
    # KProcess::m_memory at +0x1b0 (6 cores), while AudioOut accesses +0x160
    # (4 cores). Five per-core arrays × two extra 8-byte entries = 0x50.
    # PUBLIC on core is NOT sufficient if another target's own includes put
    # pristine source/eden/src (4-core hardware_properties.h) first.
    # Force the same 6-core definition before each independent consumer's
    # include root, and compile the real header probe in every independent KProcess consumer.
    target_include_directories(audio_core BEFORE PRIVATE "${EDEN_NS2_CPU6_ROOT}")
    target_include_directories(video_core BEFORE PRIVATE "${EDEN_NS2_CPU6_ROOT}")
    # hid_core has independent build units that also call KProcess::GetMemory.
    # It must see the same member offsets as the constructing core target.
    target_include_directories(hid_core BEFORE PRIVATE "${EDEN_NS2_CPU6_ROOT}")
    foreach(eden_cpu6_abi_consumer IN ITEMS core audio_core video_core hid_core)
        target_sources(${eden_cpu6_abi_consumer} PRIVATE
            "${EDEN_PORT_DIR}/ps5_cpu6_abi_probe.cpp")
    endforeach()
    # The original 4-core scheduler table defaults the two added preemption
    # priorities to zero; the original Dynarmic AddTicks divides even NS1
    # cycles by six. Both defects must be fixed before CPU6 can be exercised.
    # Derive three narrow sources from the pinned baseline without forking
    # unrelated scheduler, kernel or JIT code into the native release.
    # N76 must already have selected the current optimized G11 normal/dev
    # JIT. NEVER replace that TU with the legacy Eden arm_dynarmic_64.cpp.
    if(NOT EDEN_SHARED_NS2_GUEST_COUNTER OR
       NOT DEFINED EDEN_N76_NATIVE_JIT_SOURCE OR
       NOT EXISTS "${EDEN_N76_NATIVE_JIT_SOURCE}")
        message(FATAL_ERROR "CPU6 needs the existing N76/G11 native A64 owner")
    endif()
    set(EDEN_CPU6_SOURCE_ROOT "${PORT_ROOT}/vendor/sources/eden/src")
    set(EDEN_CPU6_A64_SOURCE "${EDEN_N76_NATIVE_JIT_SOURCE}")
    set(EDEN_CPU6_OUTPUT_ROOT "${PORT_BUILD_DIR}/ns2-cpu6")
    include("${CMAKE_CURRENT_LIST_DIR}/ns2_cpu6_source_bridge.cmake")
    get_target_property(eden_cpu6_core_sources core SOURCES)
    foreach(eden_cpu6_file IN ITEMS
            "hle/kernel/global_scheduler_context.cpp"
            "arm/dynarmic/arm_dynarmic_32.cpp")
        # G11 has already replaced the original A32 translation unit.
        # Consume that exact selected native profile, not the removed relative
        # upstream file. The CPU6 A32 static owner is based on this G11 profile
        # and changes only the per-process six-core tick denominator.
        set(eden_cpu6_selected_source "${eden_cpu6_file}")
        if(eden_cpu6_file STREQUAL "arm/dynarmic/arm_dynarmic_32.cpp")
            set(eden_cpu6_selected_source
                "${EDEN_G11_ROOT}/arm_dynarmic_32_${EDEN_G11_PLATFORM}_${EDEN_G11_PROFILE}.cpp")
            if(NOT PS5_NATIVE OR NOT EXISTS "${eden_cpu6_selected_source}")
                message(FATAL_ERROR "CPU6 requires maintained native G11 A32 source")
            endif()
        endif()
        list(FIND eden_cpu6_core_sources "${eden_cpu6_selected_source}" eden_cpu6_owner_idx)
        if(eden_cpu6_owner_idx EQUAL -1)
            message(FATAL_ERROR "Selected CPU6 scheduler/tick owner changed: ${eden_cpu6_selected_source}")
        endif()
        list(REMOVE_ITEM eden_cpu6_core_sources "${eden_cpu6_selected_source}")
        list(APPEND eden_cpu6_core_sources
            "${EDEN_CPU6_OUTPUT_ROOT}/core/${eden_cpu6_file}")
    endforeach()
    list(FIND eden_cpu6_core_sources
         "${EDEN_N76_NATIVE_JIT_SOURCE}" eden_cpu6_g11_owner_idx)
    if(eden_cpu6_g11_owner_idx EQUAL -1)
        message(FATAL_ERROR "CPU6 must retain selected N76/G11 JIT source")
    endif()
    list(REMOVE_ITEM eden_cpu6_core_sources "${EDEN_N76_NATIVE_JIT_SOURCE}")
    list(APPEND eden_cpu6_core_sources
        "${EDEN_CPU6_OUTPUT_ROOT}/core/arm/dynarmic/arm_dynarmic_64.cpp")
    set_property(TARGET core PROPERTY SOURCES "${eden_cpu6_core_sources}")
endif()

# Shared kernel heap admission for Switch 2: the 39-bit guest virtual heap
# may span 16 GiB, but physical pages stay bounded by the selected guest memory
# layout and the existing sparse PS5 allocator. This does NOT allocate 16 GiB.
# Preserve all other Switch 1 kernel/SVC owners and behavior.
set(EDEN_SHARED_NS2_KERNEL_HEAP OFF)
if(PS5_NATIVE AND EDEN_REVIEWED_DUAL_NPDM)
    set(EDEN_SHARED_NS2_KERNEL_HEAP ON)
endif()
if(EDEN_SHARED_NS2_KERNEL_HEAP)
    set(EDEN_NS2_KERNEL_ROOT "${PORT_ROOT}/vendor/encore-active/ns2-runtime/kernel")
    get_target_property(eden_ns2_kernel_sources core SOURCES)
    foreach(eden_ns2_kernel_owner IN ITEMS
            "hle/kernel/k_address_space_info.cpp"
            "hle/kernel/svc/svc_physical_memory.cpp")
        list(FIND eden_ns2_kernel_sources "${eden_ns2_kernel_owner}" eden_ns2_kernel_index)
        if(eden_ns2_kernel_index EQUAL -1)
            message(FATAL_ERROR "NS2 shared kernel owner changed: ${eden_ns2_kernel_owner}")
        endif()
        set(eden_ns2_kernel_overlay
            "${EDEN_NS2_KERNEL_ROOT}/core/${eden_ns2_kernel_owner}")
        if(NOT EXISTS "${eden_ns2_kernel_overlay}")
            message(FATAL_ERROR "Missing reviewed NS2 kernel owner: ${eden_ns2_kernel_overlay}")
        endif()
        list(REMOVE_ITEM eden_ns2_kernel_sources "${eden_ns2_kernel_owner}")
        list(APPEND eden_ns2_kernel_sources "${eden_ns2_kernel_overlay}")
    endforeach()
    set_property(TARGET core PROPERTY SOURCES "${eden_ns2_kernel_sources}")
    message(STATUS "Encore shared NS1/NS2 kernel: extended virtual heap and per-layout heap admission")
endif()

# Shared Switch 2 audio user + virtual device + real Sysmix stream service.
# Select the maintained NS1/NS2 audio sink, retaining all Switch 1 managers.
set(EDEN_SHARED_NS2_AUDIO OFF)
if(PS5_NATIVE AND EDEN_REVIEWED_DUAL_NPDM)
    set(EDEN_SHARED_NS2_AUDIO ON)
endif()
if(EDEN_SHARED_NS2_AUDIO)
    set(EDEN_NS2_AUDIO_ROOT "${PORT_ROOT}/vendor/encore-active/ns2-runtime/audio")
    set(EDEN_NS2_AUDIO_SOURCE "${EDEN_NS2_AUDIO_ROOT}/core/hle/service/audio/audio.cpp")
    if(NOT EXISTS "${EDEN_NS2_AUDIO_SOURCE}" OR
       NOT EXISTS "${EDEN_NS2_AUDIO_ROOT}/core/hle/service/audio/nx2_audio_user_client.h")
        message(FATAL_ERROR "Missing maintained NS2 aud:u owners")
    endif()
    get_target_property(eden_ns2_audio_sources core SOURCES)
    list(FIND eden_ns2_audio_sources "hle/service/audio/audio.cpp" eden_ns2_audio_idx)
    if(eden_ns2_audio_idx EQUAL -1)
        message(FATAL_ERROR "Pinned audio HLE owner changed: review NS2 aud:u selection")
    endif()
    list(REMOVE_ITEM eden_ns2_audio_sources "hle/service/audio/audio.cpp")
    if(NOT EXISTS "${EDEN_NS2_AUDIO_ROOT}/core/hle/service/audio/nx2_sysmix.cpp"
       OR NOT EXISTS "${EDEN_NS2_AUDIO_ROOT}/core/hle/service/audio/nx2_sysmix_user_service.h")
        message(FATAL_ERROR "Missing maintained NS2 Sysmix ring/IPC owners")
    endif()
    list(APPEND eden_ns2_audio_sources
        "${EDEN_NS2_AUDIO_SOURCE}"
        "${EDEN_NS2_AUDIO_ROOT}/core/hle/service/audio/nx2_sysmix.cpp")
    set_property(TARGET core PROPERTY SOURCES "${eden_ns2_audio_sources}")
    target_include_directories(core BEFORE PRIVATE "${EDEN_NS2_AUDIO_ROOT}")
endif()

# N3b: shared native PS5 applet compatibility, selected by reviewed NPDM.
# Command 320 reads the existing locked screenshot and recording state; it
# does not advertise synthetic success or change the legacy NS1 command IDs.
# Keep the original Encore AM owner as ancestor and the advanced GPU proxy/
# graphics scaling path separate until real IPC/event semantics are proven.
set(EDEN_SHARED_NS2_AM OFF)
if(PS5_NATIVE AND EDEN_REVIEWED_DUAL_NPDM)
    set(EDEN_SHARED_NS2_AM ON)
endif()
if(EDEN_SHARED_NS2_AM)
    if(NOT EDEN_REVIEWED_DUAL_NPDM)
        message(FATAL_ERROR "NS2 AM shared command 320 requires reviewed metadata")
    endif()
    set(EDEN_NS2_AM_ROOT "${PORT_ROOT}/vendor/encore-active/ns2-runtime/am")
    if(NOT EXISTS "${EDEN_NS2_AM_ROOT}/core/hle/service/am/service/application_functions.cpp"
       OR NOT EXISTS "${PORT_ROOT}/vendor/encore-active/ns2-runtime/am/core/hle/service/am/service/application_functions.h")
        message(FATAL_ERROR "Missing experimental NS2 AM implementation/header")
    endif()
    get_target_property(eden_ns2_am_sources core SOURCES)
    list(FIND eden_ns2_am_sources "${EDEN_APP_FUNCTION_SOURCE}" eden_ns2_am_idx)
    if(eden_ns2_am_idx EQUAL -1)
        message(FATAL_ERROR "Encore maintained AM owner changed: re-audit NS2 port")
    endif()
    list(REMOVE_ITEM eden_ns2_am_sources "${EDEN_APP_FUNCTION_SOURCE}")
    list(APPEND eden_ns2_am_sources "${EDEN_NS2_AM_ROOT}/core/hle/service/am/service/application_functions.cpp")
    set_property(TARGET core PROPERTY SOURCES "${eden_ns2_am_sources}")
    target_include_directories(core BEFORE PRIVATE "${EDEN_NS2_AM_ROOT}")
endif()

# Retired prototype AM graphics scaling: command 60 used an unverified
# constant response with no event contract. Do not compile/advertise it.
# A future real NS2 implementation must derive values from GPU/display state.

# Native Switch 2 GPU capabilities IOCTLs, experimental only; original
# Maxwell IOCTL path remains active for all other request IDs.
# The native GPU-characteristics IOCTL owner is additive: it recognizes only
# the new, exact NS2 request IDs and falls back to existing NS1 handlers.
# Keep 4K GMMU/GPFIFO source replacements research-only until per-process
# dispatch is validated on PS5; mixing page sizes would regress FC 27.
set(EDEN_SHARED_NS2_NVDRV_CAPS OFF)
if(PS5_NATIVE AND EDEN_REVIEWED_DUAL_NPDM)
    set(EDEN_SHARED_NS2_NVDRV_CAPS ON)
endif()
if(EDEN_SHARED_NS2_NVDRV_CAPS)
    if(NOT EDEN_REVIEWED_DUAL_NPDM)
        message(FATAL_ERROR "Shared NS2 GPU capabilities need reviewed metadata")
    endif()
    set(EDEN_NS2_NVDRV_ROOT "${PORT_ROOT}/vendor/encore-active/ns2-runtime/nvdrv")
    set(EDEN_NS2_NVDRV_SOURCE
        "${EDEN_NS2_NVDRV_ROOT}/core/hle/service/nvdrv/devices/nvhost_ctrl_gpu.cpp")
    if(NOT EXISTS "${EDEN_NS2_NVDRV_SOURCE}" OR
       NOT EXISTS "${EDEN_NS2_NVDRV_ROOT}/core/hle/service/nvdrv/devices/native_gpu_characteristics.h" OR
       NOT EXISTS "${EDEN_NS2_NVDRV_ROOT}/core/hle/service/nvdrv/devices/native_characteristics_ioctl.h")
        message(FATAL_ERROR "Missing NS2 native NVDRV research sources")
    endif()
    get_target_property(eden_ns2_nvdrv_sources core SOURCES)
    list(FIND eden_ns2_nvdrv_sources
        "hle/service/nvdrv/devices/nvhost_ctrl_gpu.cpp" eden_ns2_nvdrv_idx)
    if(eden_ns2_nvdrv_idx EQUAL -1)
        message(FATAL_ERROR "Pinned NVDRV source owner changed: re-audit NS2 overlay")
    endif()
    list(REMOVE_ITEM eden_ns2_nvdrv_sources
        "hle/service/nvdrv/devices/nvhost_ctrl_gpu.cpp")
    list(APPEND eden_ns2_nvdrv_sources "${EDEN_NS2_NVDRV_SOURCE}")
    set_property(TARGET core PROPERTY SOURCES "${eden_ns2_nvdrv_sources}")
    target_include_directories(core BEFORE PRIVATE "${EDEN_NS2_NVDRV_ROOT}")
    # The one native NVDRV owner handles NS1 Maxwell and NS2 Ampere channels.
    set(EDEN_NS2_NVDRV_AS_ROOT "${PORT_ROOT}/vendor/encore-active/ns2-runtime/nvdrv_as")
    set(EDEN_NS2_NVDRV_AS_SOURCE
        "${EDEN_NS2_NVDRV_AS_ROOT}/core/hle/service/nvdrv/devices/nvhost_as_gpu.cpp")
    if(NOT EXISTS "${EDEN_NS2_NVDRV_AS_SOURCE}" OR
       NOT EXISTS "${EDEN_NS2_NVDRV_AS_ROOT}/core/hle/service/nvdrv/devices/nvhost_as_gpu.h")
        message(FATAL_ERROR "Missing NS2 native 4K GPU address-space overlay")
    endif()
    list(FIND eden_ns2_nvdrv_sources
        "hle/service/nvdrv/devices/nvhost_as_gpu.cpp" eden_ns2_as_idx)
    if(eden_ns2_as_idx EQUAL -1)
        message(FATAL_ERROR "Pinned NVDRV AS owner changed: re-audit NS2 overlay")
    endif()
    list(REMOVE_ITEM eden_ns2_nvdrv_sources
        "hle/service/nvdrv/devices/nvhost_as_gpu.cpp")
    list(APPEND eden_ns2_nvdrv_sources "${EDEN_NS2_NVDRV_AS_SOURCE}")
    # Native GPFIFO/CMDDMA adapter: never replace the shipping source owner.
    set(EDEN_NS2_NVDRV_GPU_ROOT "${PORT_ROOT}/vendor/encore-active/ns2-runtime/nvdrv_gpu")
    set(EDEN_NS2_NVDRV_GPU_SOURCE
        "${EDEN_NS2_NVDRV_GPU_ROOT}/core/hle/service/nvdrv/devices/nvhost_gpu.cpp")
    if(NOT EXISTS "${EDEN_NS2_NVDRV_GPU_SOURCE}" OR
       NOT EXISTS "${EDEN_NS2_NVDRV_GPU_ROOT}/core/hle/service/nvdrv/devices/nvhost_gpu.h")
        message(FATAL_ERROR "Missing NS2 native GPU channel adapter")
    endif()
    list(FIND eden_ns2_nvdrv_sources
        "hle/service/nvdrv/devices/nvhost_gpu.cpp" eden_ns2_gpu_idx)
    if(eden_ns2_gpu_idx EQUAL -1)
        message(FATAL_ERROR "Pinned NVDRV GPU channel source changed: re-audit overlay")
    endif()
    list(REMOVE_ITEM eden_ns2_nvdrv_sources
        "hle/service/nvdrv/devices/nvhost_gpu.cpp")
    list(APPEND eden_ns2_nvdrv_sources "${EDEN_NS2_NVDRV_GPU_SOURCE}")
    set_property(TARGET core PROPERTY SOURCES "${eden_ns2_nvdrv_sources}")
    target_include_directories(core BEFORE PRIVATE "${EDEN_NS2_NVDRV_GPU_ROOT}" "${EDEN_NS2_NVDRV_ROOT}" "${EDEN_NS2_NVDRV_AS_ROOT}")
    # Native DMA dispatch: upstream Ampere class 0xc7b5 uses
    # the same DMA engine methods, authenticated by live process generation.
    # Do not replace the shipping NS1 puller or alias Ampere 3D/compute.
    set(EDEN_NS2_NATIVE_GPU_PULLER
        "${PORT_ROOT}/vendor/encore-active/ns2-runtime/gpu_dispatch/video_core/engines/puller.cpp")
    if(NOT EXISTS "${EDEN_NS2_NATIVE_GPU_PULLER}" OR
       NOT EXISTS "${EDEN_NS2_NVDRV_GPU_ROOT}/core/hle/service/nvdrv/devices/native_gpu_channel_registry.h")
        message(FATAL_ERROR "Missing native NS2 DMA channel ownership or puller")
    endif()
    get_target_property(eden_ns2_dispatch_sources video_core SOURCES)
    # G20 already replaced Eden's relative engines/puller.cpp with the
    # versioned Encore normal/dev GPU command processor. The research NS2
    # overlay must replace THAT exact owner, never append a second Puller.
    if(NOT DEFINED EDEN_MAINTAINED_GPU_PULLER OR
       NOT EXISTS "${EDEN_MAINTAINED_GPU_PULLER}")
        message(FATAL_ERROR "Missing G20 maintained GPU puller selected before NS2")
    endif()
    list(FIND eden_ns2_dispatch_sources "${EDEN_MAINTAINED_GPU_PULLER}" eden_ns2_puller_idx)
    if(eden_ns2_puller_idx EQUAL -1)
        message(FATAL_ERROR "Pinned G20 GPU puller changed; re-audit native Ampere dispatch")
    endif()
    list(REMOVE_ITEM eden_ns2_dispatch_sources "${EDEN_MAINTAINED_GPU_PULLER}")
    list(APPEND eden_ns2_dispatch_sources "${EDEN_NS2_NATIVE_GPU_PULLER}")
    set_property(TARGET video_core PROPERTY SOURCES "${eden_ns2_dispatch_sources}")
    # P2.7: native semaphore parking must use exactly one scheduler implementation
    # and one set of ABI-matched Puller/DmaPusher/Scheduler declarations.
    set(EDEN_NS2_GPFIFO_ROOT
        "${PORT_ROOT}/vendor/encore-active/ns2-runtime/gpu_dispatch")
    set(EDEN_NS2_GPFIFO_SCHEDULER
        "${EDEN_NS2_GPFIFO_ROOT}/video_core/control/scheduler.cpp")
    foreach(EDEN_NS2_GPFIFO_OWNER IN ITEMS
        "${EDEN_NS2_GPFIFO_ROOT}/video_core/dma_pusher.h"
        "${EDEN_NS2_GPFIFO_ROOT}/video_core/control/scheduler.h"
        "${EDEN_NS2_GPFIFO_SCHEDULER}")
        if(NOT EXISTS "${EDEN_NS2_GPFIFO_OWNER}")
            message(FATAL_ERROR "Missing maintained native GPFIFO suspend/resume owner")
        endif()
    endforeach()
    get_target_property(eden_ns2_sched_sources video_core SOURCES)
    list(FIND eden_ns2_sched_sources "control/scheduler.cpp" eden_ns2_sched_idx)
    if(eden_ns2_sched_idx EQUAL -1)
        message(FATAL_ERROR "Pinned GPFIFO scheduler owner moved; requalify")
    endif()
    list(REMOVE_ITEM eden_ns2_sched_sources "control/scheduler.cpp")
    list(APPEND eden_ns2_sched_sources "${EDEN_NS2_GPFIFO_SCHEDULER}")
    set_property(TARGET video_core PROPERTY SOURCES "${eden_ns2_sched_sources}")
    # PS5_NATIVE is not a transitive preprocessor definition. Ensure the
    # selected DMA TU actually compiles its native resume/GPFIFO cursor
    # code, including the non-Vulkan PS5 path; do not define it for core.
    set_property(SOURCE "${EDEN_MAINTAINED_GPU_DMA}"
        TARGET_DIRECTORY video_core APPEND PROPERTY COMPILE_DEFINITIONS "PS5_NATIVE=1")
    # Research-only header and .cpp must be the SAME Puller class to keep
    # DmaPusher ABI consistent in every video_core translation unit.
    set(EDEN_NS2_GPU_DISPATCH_ROOT
        "${PORT_ROOT}/vendor/encore-active/ns2-runtime/gpu_dispatch")
    if(NOT EXISTS "${EDEN_NS2_GPU_DISPATCH_ROOT}/video_core/engines/puller.h" OR
       NOT EXISTS "${EDEN_NS2_GPU_DISPATCH_ROOT}/video_core/native_ampere_macro_state.h" OR
       NOT EXISTS "${EDEN_NS2_GPU_DISPATCH_ROOT}/video_core/macro_turing.h")
        message(FATAL_ERROR "Missing isolated Ampere MME/puller dispatch headers")
    endif()
    target_include_directories(video_core BEFORE PRIVATE
        "${EDEN_NS2_GPU_DISPATCH_ROOT}"
        "${EDEN_NS2_NVDRV_GPU_ROOT}" "${EDEN_NS2_NVDRV_ROOT}")
    # Core stores ChannelState payloads containing DmaPusher by value.
    # Do not permit a split Puller/DmaPusher ABI between core and video_core.
    target_include_directories(core BEFORE PRIVATE
        "${EDEN_NS2_GPU_DISPATCH_ROOT}")
    # Native admission follows the actual channel/process registration.
    # Unregistered NS1 Maxwell commands retain the original DMA path.
endif()

# Native GPU session HLE and bounded worker transport: one process-scoped
# runtime for both console generations, selected by actual guest identity.
# Use the already selected real GPU-access SVC kernel owner (SVC 0x80), not
# the old trace-only duplicate SVC source.
if(PS5_NATIVE AND EDEN_REVIEWED_DUAL_NPDM)
    if(NOT DEFINED EDEN_NS2_NVDRV_GPU_SOURCE OR
       NOT EXISTS "${EDEN_NS2_NVDRV_GPU_SOURCE}" OR
       NOT EDEN_SHARED_NS2_GPU_ACCESS_SVC)
        message(FATAL_ERROR "Native GPU session requires unified NVDRV and SVC 0x80 owners")
    endif()
    set(EDEN_NS2_GPU_SESSION_ROOT "${PORT_ROOT}/vendor/encore-active/ns2-runtime/gpu_session")
    set(EDEN_NS2_GPU_SESSION_SOURCE
        "${EDEN_NS2_GPU_SESSION_ROOT}/core/hle/service/am/service/gpu_session.cpp")
    set(EDEN_NS2_GPU_WORKER_SOURCE
        "${EDEN_NS2_GPU_SESSION_ROOT}/core/hle/service/am/service/gpu_worker.cpp")
    set(EDEN_NS2_GPU_SHARED_SOURCE
        "${EDEN_NS2_GPU_SESSION_ROOT}/core/hle/service/am/service/gpu_worker_shared.cpp")
    if(NOT EXISTS "${EDEN_NS2_GPU_SESSION_SOURCE}" OR
       NOT EXISTS "${EDEN_NS2_GPU_WORKER_SOURCE}" OR
       NOT EXISTS "${EDEN_NS2_GPU_SHARED_SOURCE}" OR
       NOT EXISTS "${EDEN_NS2_GPU_SESSION_ROOT}/core/hle/service/am/service/gpu_worker.h" OR
       NOT EXISTS "${EDEN_NS2_GPU_SESSION_ROOT}/core/hle/service/am/service/gpu_session.h" OR
       NOT EXISTS "${PORT_ROOT}/vendor/encore-active/ns2-runtime/hle/core/hle/service/am/service/gpu_session_protocol.h")
        message(FATAL_ERROR "Missing maintained NS2 GPU session source/protocol")
    endif()
    target_sources(core PRIVATE "${EDEN_NS2_GPU_SESSION_SOURCE}"
        "${EDEN_NS2_GPU_WORKER_SOURCE}" "${EDEN_NS2_GPU_SHARED_SOURCE}")
    target_include_directories(core BEFORE PRIVATE
        "${EDEN_NS2_GPU_SESSION_ROOT}"
        "${PORT_ROOT}/vendor/encore-active/ns2-runtime/hle")
endif()

# Shared NS1/NS2 host video decoder: the native NS2 codec path reuses the
# already linked Eden FFmpeg video_core owner. No per-title backend selection.
# Unsupported elementary streams fail at codec construction, never acknowledge
# a decoded image when no decoder exists.
if(PS5_NATIVE AND EDEN_REVIEWED_DUAL_NPDM)
    set(EDEN_SHARED_NATIVE_VIDEO_CODEC_ROOT
        "${PORT_ROOT}/vendor/encore-active/ns2-runtime/video_decoder")
    foreach(eden_native_video_codec_file
        "${EDEN_SHARED_NATIVE_VIDEO_CODEC_ROOT}/video_core/host1x/h264_packet.h"
        "${EDEN_SHARED_NATIVE_VIDEO_CODEC_ROOT}/video_core/host1x/nx2_video_decoder.h"
        "${EDEN_SHARED_NATIVE_VIDEO_CODEC_ROOT}/video_core/host1x/nx2_video_decoder.cpp")
        if(NOT EXISTS "${eden_native_video_codec_file}")
            message(FATAL_ERROR "Missing maintained NS2 video decoder owner: ${eden_native_video_codec_file}")
        endif()
    endforeach()
    target_sources(video_core PRIVATE
        "${EDEN_SHARED_NATIVE_VIDEO_CODEC_ROOT}/video_core/host1x/nx2_video_decoder.cpp")
    target_include_directories(video_core BEFORE PRIVATE
        "${EDEN_SHARED_NATIVE_VIDEO_CODEC_ROOT}")
    target_include_directories(core BEFORE PRIVATE
        "${EDEN_SHARED_NATIVE_VIDEO_CODEC_ROOT}")
    set(EDEN_SHARED_NATIVE_VIDEO_SESSION_SOURCE
        "${EDEN_SHARED_NATIVE_VIDEO_CODEC_ROOT}/core/hle/service/am/service/graphics_video_decoder_session.cpp")
    if(NOT EXISTS "${EDEN_SHARED_NATIVE_VIDEO_SESSION_SOURCE}" OR
       NOT EXISTS "${EDEN_SHARED_NATIVE_VIDEO_CODEC_ROOT}/core/hle/service/am/service/graphics_video_decoder_session.h" OR
       NOT EXISTS "${EDEN_SHARED_NATIVE_VIDEO_CODEC_ROOT}/core/hle/service/am/service/native_video_eos.h" OR
       NOT EXISTS "${EDEN_SHARED_NATIVE_VIDEO_CODEC_ROOT}/core/hle/service/am/service/native_video_work_buffer.h" OR
       NOT EXISTS "${EDEN_SHARED_NATIVE_VIDEO_CODEC_ROOT}/core/hle/service/am/service/native_video_ready_state.h")
        message(FATAL_ERROR "Missing maintained NS2 video IPC session owner")
    endif()
    target_sources(core PRIVATE "${EDEN_SHARED_NATIVE_VIDEO_SESSION_SOURCE}")
endif()

# Unified native GraphicsSupervisor / SelfController IPC and VI2 cadence.
# NS1 service behaviour remains selected by the guest's registered process.
if(PS5_NATIVE AND EDEN_REVIEWED_DUAL_NPDM)
    if(NOT EDEN_SHARED_NS2_AM)
        message(FATAL_ERROR "Native GraphicsSupervisor requires the shared AM owner")
    endif()
    set(EDEN_NS2_SUPERVISOR_ROOT "${PORT_ROOT}/vendor/encore-active/ns2-runtime/graphics_supervisor")
    set(EDEN_NS2_SELF_ROOT "${PORT_ROOT}/vendor/encore-active/ns2-runtime/self_controller")
    foreach(eden_ns2_supervisor_file
        "${EDEN_NS2_SUPERVISOR_ROOT}/core/hle/service/am/service/graphics_supervisor.h"
        "${EDEN_NS2_SUPERVISOR_ROOT}/core/hle/service/am/service/graphics_supervisor.cpp"
        "${EDEN_NS2_SELF_ROOT}/core/hle/service/am/service/self_controller.h"
        "${EDEN_NS2_SELF_ROOT}/core/hle/service/am/service/self_controller.cpp")
        if(NOT EXISTS "${eden_ns2_supervisor_file}")
            message(FATAL_ERROR "Missing NS2 supervisor owner: ${eden_ns2_supervisor_file}")
        endif()
    endforeach()
    get_target_property(eden_ns2_supervisor_sources core SOURCES)
    list(FIND eden_ns2_supervisor_sources
        "hle/service/am/service/self_controller.cpp" eden_ns2_self_idx)
    if(eden_ns2_self_idx EQUAL -1)
        message(FATAL_ERROR "Pinned SelfController owner changed: re-audit NS2 bridge")
    endif()
    list(REMOVE_ITEM eden_ns2_supervisor_sources
        "hle/service/am/service/self_controller.cpp")
    list(APPEND eden_ns2_supervisor_sources
        "${EDEN_NS2_SELF_ROOT}/core/hle/service/am/service/self_controller.cpp"
        "${EDEN_NS2_SUPERVISOR_ROOT}/core/hle/service/am/service/graphics_supervisor.cpp")
    set_property(TARGET core PROPERTY SOURCES "${eden_ns2_supervisor_sources}")
    target_include_directories(core BEFORE PRIVATE
        "${EDEN_NS2_SELF_ROOT}" "${EDEN_NS2_SUPERVISOR_ROOT}")
endif()

# P0.2: Compile the same native Ampere-to-Maxwell frontend in the ONE
# qualified native release source graph. Shader execution is still routed
# exclusively by the separate GPU session/renderer owner: compiling these
# units does not make a Switch 1 shader enter the Ampere translator.
# Guest process and channel identity selects Maxwell or Ampere at runtime.
set(EDEN_SHARED_NS2_AMPERE_CORE OFF)
if(PS5_NATIVE AND
   EDEN_REVIEWED_DUAL_NPDM AND EDEN_PS5_VULKAN)
    set(EDEN_SHARED_NS2_AMPERE_CORE ON)
endif()
if(EDEN_SHARED_NS2_AMPERE_CORE)
    if(NOT EDEN_REVIEWED_DUAL_NPDM)
        message(FATAL_ERROR "NS2 Ampere ISA requires reviewed native NPDM")
    endif()
    # The alternative 32-slot resource header changes BufferCache signatures,
    # NUM_STORAGE_BUFFERS (16 -> 32), and is NOT ABI-safe as a header-only
    # native override. Do not include it in the shared 16-slot NS1 BufferCache ABI.
    set(EDEN_NS2_SHADER_RESOURCE_ROOT
        "${PORT_ROOT}/vendor/encore-active/ns2-runtime/shader_resource/include")
    if(NOT EXISTS "${EDEN_NS2_SHADER_RESOURCE_ROOT}/shader_recompiler/frontend/ir/attribute.h" OR
       NOT EXISTS "${EDEN_NS2_SHADER_RESOURCE_ROOT}/video_core/buffer_cache/buffer_cache_base.h")
        message(FATAL_ERROR "Missing native NS2 shader/texture resource headers")
    endif()
    # The generic31 Y/Z/W classifier is a pure, shared IR fix. Copy
    # only this reviewed header into the common build include tree;
    # do not silently replace the BufferCache layout or methods.
    file(MAKE_DIRECTORY "${PORT_BUILD_DIR}/include/shader_recompiler/frontend/ir")
    configure_file(
        "${EDEN_NS2_SHADER_RESOURCE_ROOT}/shader_recompiler/frontend/ir/attribute.h"
        "${PORT_BUILD_DIR}/include/shader_recompiler/frontend/ir/attribute.h" COPYONLY)
    target_include_directories(shader_recompiler BEFORE PRIVATE "${PORT_BUILD_DIR}/include")
    target_include_directories(video_core BEFORE PRIVATE "${PORT_BUILD_DIR}/include")
    target_include_directories(core BEFORE PRIVATE "${PORT_BUILD_DIR}/include")
    set(EDEN_NS2_AMPERE_ROOT "${PORT_ROOT}/vendor/encore-active/ns2-runtime/ampere")
    set(EDEN_NS2_AMPERE_PROBE
        "${EDEN_NS2_AMPERE_ROOT}/shader_recompiler/frontend/ampere/probe.cpp")
    foreach(eden_ampere_header IN ITEMS ampere_isa_table.h classify.h instruction.h probe.h
            lower_to_maxwell.h lower_bridge.h register_pressure.h maxwell_image.h
            native_stage_buffer.h
            program_address_map.h capture.h program_capture.h translation_cache.h
            maxwell_environment.h ir_bridge.h)
        if(NOT EXISTS
           "${EDEN_NS2_AMPERE_ROOT}/shader_recompiler/frontend/ampere/${eden_ampere_header}")
            message(FATAL_ERROR "Missing NS2 Ampere ISA header: ${eden_ampere_header}")
        endif()
    endforeach()
    if(NOT EXISTS "${EDEN_NS2_AMPERE_PROBE}")
        message(FATAL_ERROR "Missing NS2 Ampere shader instruction decoder")
    endif()
    set(EDEN_NS2_AMPERE_LOWER_BRIDGE
        "${EDEN_NS2_AMPERE_ROOT}/shader_recompiler/frontend/ampere/lower_bridge.cpp")
    if(NOT EXISTS "${EDEN_NS2_AMPERE_LOWER_BRIDGE}")
        message(FATAL_ERROR "Missing NS2 bounded native-to-Maxwell translation bridge")
    endif()
    set(EDEN_NS2_MAXWELL_IMAGE_BRIDGE
        "${EDEN_NS2_AMPERE_ROOT}/shader_recompiler/frontend/ampere/maxwell_image.cpp")
    if(NOT EXISTS "${EDEN_NS2_MAXWELL_IMAGE_BRIDGE}")
        message(FATAL_ERROR "Missing NS2 native-to-Maxwell shader-environment image adapter")
    endif()
    set(EDEN_NS2_NATIVE_SHADER_CAPTURE
        "${EDEN_NS2_AMPERE_ROOT}/shader_recompiler/frontend/ampere/capture.cpp")
    set(EDEN_NS2_NATIVE_GMMU_CAPTURE
        "${EDEN_NS2_AMPERE_ROOT}/video_core/native_shader_capture.cpp")
    if(NOT EXISTS "${EDEN_NS2_NATIVE_SHADER_CAPTURE}" OR
       NOT EXISTS "${EDEN_NS2_NATIVE_GMMU_CAPTURE}" OR
       NOT EXISTS "${EDEN_NS2_AMPERE_ROOT}/video_core/native_shader_capture.h")
        message(FATAL_ERROR "Missing NS2 real GMMU-backed native shader capture owner")
    endif()
    set(EDEN_NS2_NATIVE_TRANSLATION_CACHE
        "${EDEN_NS2_AMPERE_ROOT}/shader_recompiler/frontend/ampere/translation_cache.cpp")
    if(NOT EXISTS "${EDEN_NS2_NATIVE_TRANSLATION_CACHE}")
        message(FATAL_ERROR "Missing bounded, process-owned NS2 translation cache")
    endif()
    set(EDEN_NS2_MAXWELL_ENVIRONMENT_ADAPTER
        "${EDEN_NS2_AMPERE_ROOT}/shader_recompiler/frontend/ampere/maxwell_environment.cpp")
    if(NOT EXISTS "${EDEN_NS2_MAXWELL_ENVIRONMENT_ADAPTER}")
        message(FATAL_ERROR "Missing NS2 Shader::Environment Maxwell frontend adapter")
    endif()
    set(EDEN_NS2_MAXWELL_IR_BRIDGE
        "${EDEN_NS2_AMPERE_ROOT}/shader_recompiler/frontend/ampere/ir_bridge.cpp")
    if(NOT EXISTS "${EDEN_NS2_MAXWELL_IR_BRIDGE}")
        message(FATAL_ERROR "Missing native Ampere Maxwell CFG/IR handoff")
    endif()
    target_sources(shader_recompiler PRIVATE
        "${EDEN_NS2_MAXWELL_IR_BRIDGE}"
        "${EDEN_NS2_AMPERE_PROBE}"
        "${EDEN_NS2_AMPERE_LOWER_BRIDGE}"
        "${EDEN_NS2_MAXWELL_IMAGE_BRIDGE}"
        "${EDEN_NS2_NATIVE_SHADER_CAPTURE}"
        "${EDEN_NS2_NATIVE_TRANSLATION_CACHE}"
        "${EDEN_NS2_MAXWELL_ENVIRONMENT_ADAPTER}")
    target_include_directories(shader_recompiler BEFORE PRIVATE "${EDEN_NS2_AMPERE_ROOT}")
    target_sources(video_core PRIVATE "${EDEN_NS2_NATIVE_GMMU_CAPTURE}")
    target_include_directories(video_core BEFORE PRIVATE "${EDEN_NS2_AMPERE_ROOT}")
endif()

# N3m: compile a renderer-callable, explicitly scoped NS2 VertexB IR -> SPIR-V
# adapter. The active PS5 Vulkan pipeline owner is NOT replaced or modified:
# only a session-verified NS2 caller may invoke this isolated API.
# P0.2: the native SPIR-V compiler and QMD3 bounds emitter are complete
# maintained C++ source owners. Compile them in the PS5 release library,
# while keeping the actual Vulkan dispatch, GPU session and 4K NVDRV
# through the same GPU-owner/process chain. The SPIR-V
# overrides use a thread-local Ampere scope: Maxwell takes its original
# indirect-bank switch, byte-for-byte (see the host source parity test).
set(EDEN_SHARED_NS2_SPIRV_COMPILER OFF)
if(EDEN_SHARED_NS2_AMPERE_CORE)
    set(EDEN_SHARED_NS2_SPIRV_COMPILER ON)
endif()
if(EDEN_SHARED_NS2_SPIRV_COMPILER)
    set(EDEN_NS2_VULKAN_SHADER_BRIDGE
        "${PORT_ROOT}/vendor/encore-active/ns2-runtime/ampere/shader_recompiler/frontend/ampere/renderer_spirv_bridge.cpp")
    if(NOT EXISTS "${EDEN_NS2_VULKAN_SHADER_BRIDGE}")
        message(FATAL_ERROR "Missing NS2 renderer-side SPIR-V compiler")
    endif()
    set(EDEN_NS2_NATIVE_GPU_SPIRV_CAPTURE
        "${PORT_ROOT}/vendor/encore-active/ns2-runtime/ampere/video_core/ns2_shader_spirv_compile.cpp")
    if(NOT EXISTS "${EDEN_NS2_NATIVE_GPU_SPIRV_CAPTURE}" OR
       NOT EXISTS "${PORT_ROOT}/vendor/encore-active/ns2-runtime/ampere/video_core/ns2_shader_spirv_compile.h")
        message(FATAL_ERROR "Missing verified NS2 GMMU-to-SPIR-V pipeline entrypoint")
    endif()
    # P2.3: SPIR-V indirect CBUF dispatch uses exactly the reflected native
    # QMD3 banks, never the generic 14-bank Maxwell switch. Select the
    # complete tracked source with the shared native Ampere compiler.
    set(EDEN_NS2_QMD_CBUF_SPIRV
        "${EDEN_NS2_AMPERE_ROOT}/shader_recompiler/backend/spirv/spirv_emit_context.cpp")
    set(EDEN_NS2_QMD_CBUF_DIRECT_SPIRV
        "${EDEN_NS2_AMPERE_ROOT}/shader_recompiler/backend/spirv/emit_spirv_context_get_set.cpp")
    # Real SPIR-V descriptor arrays must have the same variable type that
    # the shared image emitter indexes, including storage texel buffers.
    set(EDEN_NS2_SPIRV_IMAGE_ARRAY
        "${EDEN_NS2_AMPERE_ROOT}/shader_recompiler/backend/spirv/emit_spirv_image.cpp")
    if(NOT EXISTS "${EDEN_NS2_SPIRV_IMAGE_ARRAY}" OR
       NOT EXISTS "${EDEN_NS2_QMD_CBUF_SPIRV}" OR
       NOT EXISTS "${EDEN_NS2_QMD_CBUF_DIRECT_SPIRV}" OR
       NOT EXISTS "${EDEN_NS2_AMPERE_ROOT}/shader_recompiler/frontend/ampere/native_indirect_cbuf.h" OR
       NOT EXISTS "${EDEN_NS2_AMPERE_ROOT}/shader_recompiler/frontend/ampere/native_global_atomic_binding.h")
        message(FATAL_ERROR "Missing reviewed native QMD3 indirect CBUF compiler")
    endif()
    get_target_property(eden_ns2_shader_sources shader_recompiler SOURCES)
    list(FIND eden_ns2_shader_sources
        "backend/spirv/spirv_emit_context.cpp" eden_ns2_spirv_source_idx)
    if(eden_ns2_spirv_source_idx LESS 0)
        message(FATAL_ERROR "Pinned SPIR-V emitter owner changed: audit QMD3 CBUF selection")
    endif()
    list(REMOVE_ITEM eden_ns2_shader_sources "backend/spirv/spirv_emit_context.cpp")
    list(APPEND eden_ns2_shader_sources "${EDEN_NS2_QMD_CBUF_SPIRV}")
    # Native direct-bank LDC also requires a pre-access bounds check. Replace
    # this FULL companion translation unit for both authenticated guest modes.
    list(FIND eden_ns2_shader_sources
        "backend/spirv/emit_spirv_context_get_set.cpp" eden_ns2_cbuf_direct_source_idx)
    if(eden_ns2_cbuf_direct_source_idx LESS 0)
        message(FATAL_ERROR "Pinned direct CBUF emitter owner changed: audit QMD3 selection")
    endif()
    list(REMOVE_ITEM eden_ns2_shader_sources "backend/spirv/emit_spirv_context_get_set.cpp")
    list(APPEND eden_ns2_shader_sources "${EDEN_NS2_QMD_CBUF_DIRECT_SPIRV}")
    # Exactly one shared SPIR-V image emitter; remove the pinned owner
    # rather than adding a second translation unit or per-title shader.
    list(FIND eden_ns2_shader_sources
        "backend/spirv/emit_spirv_image.cpp" eden_ns2_image_source_idx)
    if(eden_ns2_image_source_idx LESS 0)
        message(FATAL_ERROR "Pinned SPIR-V image emitter owner changed")
    endif()
    list(REMOVE_ITEM eden_ns2_shader_sources "backend/spirv/emit_spirv_image.cpp")
    list(APPEND eden_ns2_shader_sources "${EDEN_NS2_SPIRV_IMAGE_ARRAY}")
    set_property(TARGET shader_recompiler PROPERTY SOURCES "${eden_ns2_shader_sources}")
    target_sources(video_core PRIVATE "${EDEN_NS2_VULKAN_SHADER_BRIDGE}")
    target_sources(video_core PRIVATE "${EDEN_NS2_NATIVE_GPU_SPIRV_CAPTURE}")
    target_include_directories(video_core BEFORE PRIVATE "${PORT_ROOT}/vendor/encore-active/ns2-runtime/hle")
    # The single native PS5 runtime exposes the same Vulkan rasterizer
    # virtual methods. The real channel owner selects native QMD3 dispatch,
    # while legacy NS1 commands keep the maintained Maxwell dispatch.
    # Native Vulkan's RasterizerVulkan::DispatchNativeCompute overrides a
    # RasterizerInterface virtual method. The pinned build-source archive
    # otherwise provides the pre-NS2 interface, causing an 'override' error
    # when unrelated Vulkan consumers compile. Select the REVIEWED vendor
    # interface for every native PS5 compilation target.
    set(EDEN_NS2_RASTERIZER_INTERFACE
        "${PORT_ROOT}/vendor/encore-active/ns2-runtime/vulkan_abi/video_core/rasterizer_interface.h")
    if(NOT EXISTS "${EDEN_NS2_RASTERIZER_INTERFACE}")
        message(FATAL_ERROR "Missing reviewed native QMD3 RasterizerInterface ABI")
    endif()
    file(STRINGS "${EDEN_NS2_RASTERIZER_INTERFACE}" eden_ns2_rasterizer_interface_text
        REGEX "virtual bool DispatchNativeCompute" LIMIT_COUNT 1)
    if(NOT eden_ns2_rasterizer_interface_text MATCHES
           "virtual bool DispatchNativeCompute\\(const Tegra::NativeComputeLaunch&\\)")
        message(FATAL_ERROR "Reviewed native QMD3 RasterizerInterface ABI changed")
    endif()
    file(MAKE_DIRECTORY "${PORT_BUILD_DIR}/include/video_core")
    configure_file("${EDEN_NS2_RASTERIZER_INTERFACE}"
        "${PORT_BUILD_DIR}/include/video_core/rasterizer_interface.h" COPYONLY)
    # The virtual table is shared by core, video_core and their consumers.
    # Do not give video_core a private, incompatible interpretation.
    # Native compute belongs to the PS5 RasterizerInterface for both guests.
    # Channel/process ownership determines whether QMD3 can execute.
endif()

# N50: shared native PS5 device-memory contiguous page-run safety.
# End stale physical continuity before a GPU Map/Unmap, for both generations.
# Reuse the one reviewed PS5 device-memory owner; no extra translation unit.
if(PS5_NATIVE)
    if(NOT EXISTS "${PORT_ROOT}/vendor/encore-active/eden-core/overrides/core/device_memory_manager.inc")
        message(FATAL_ERROR "N50 maintained PS5 device-memory source missing")
    endif()
    if(NOT EXISTS "${PORT_ROOT}/vendor/encore-active/ns2-helpers/include/core/ns2_egl_continuity_guard.h")
        message(FATAL_ERROR "Missing N50 vendor continuity helper")
    endif()
    target_include_directories(core BEFORE PRIVATE
        "${PORT_ROOT}/vendor/encore-active/ns2-helpers/include")
    target_include_directories(video_core BEFORE PRIVATE
        "${PORT_ROOT}/vendor/encore-active/ns2-helpers/include")
    target_compile_definitions(core PRIVATE EDEN_NS2_DEVICE_CONTINUITY=1)
    target_compile_definitions(video_core PRIVATE EDEN_NS2_DEVICE_CONTINUITY=1)
endif()

# The native app always contains the same gameplay renderer and launcher.
# Platform dependencies remain build requirements, never release/DEV gates.
if(PS5_NATIVE AND (NOT EDEN_PS5_VULKAN OR NOT EDEN_PS5_OPENGL OR
                   NOT EDEN_VULKAN_DRIVER STREQUAL "RADV"))
    message(FATAL_ERROR "Native Encore requires Vulkan/RADV and its OpenGL launcher")
endif()

# Shared NUP content loader, metadata and AoC owners for the regular build.
include("${CMAKE_CURRENT_LIST_DIR}/nup_v1_runtime.cmake")

# P2.4 Native Task/Mesh shaders: maintained compiler units and ABI headers.
# Shared shader ABI for NS1/NS2: no alternate emulator mode and no runtime
# patch generation. Existing Maxwell paths retain their legacy behavior.
if(EDEN_SHARED_NS2_SPIRV_COMPILER)
    set(EDEN_NATIVE_TASK_MESH_ROOT
        "${PORT_ROOT}/vendor/encore-active/eden-shader/src")
    set(EDEN_NATIVE_TASK_MESH_VULKAN_HEADERS
        "${PORT_ROOT}/vendor/encore-active/eden-vulkan/include")
    foreach(eden_mesh_header IN ITEMS
        shader_recompiler/backend/glasm/emit_glasm_instructions.h
        shader_recompiler/backend/glsl/emit_glsl_instructions.h
        shader_recompiler/backend/spirv/emit_spirv_instructions.h
        shader_recompiler/backend/spirv/spirv_emit_context.h
        shader_recompiler/environment.h
        shader_recompiler/frontend/ir/ir_emitter.h
        shader_recompiler/frontend/ir/opcodes.h
        shader_recompiler/frontend/ir/opcodes.inc
        shader_recompiler/frontend/ir/program.h
        shader_recompiler/frontend/maxwell/maxwell.inc
        shader_recompiler/frontend/maxwell/opcodes.h
        shader_recompiler/runtime_info.h
        shader_recompiler/shader_info.h
        shader_recompiler/stage.h
        )
        if(NOT EXISTS "${EDEN_NATIVE_TASK_MESH_ROOT}/${eden_mesh_header}")
            message(FATAL_ERROR "Missing maintained Task/Mesh shader header: ${eden_mesh_header}")
        endif()
    endforeach()
    if(NOT EXISTS "${EDEN_NATIVE_TASK_MESH_VULKAN_HEADERS}/video_core/vulkan_common/vulkan_device.h")
        message(FATAL_ERROR "Missing native Task/Mesh Vulkan feature ABI header")
    endif()
    set(eden_mesh_source_paths
        backend/spirv/emit_spirv.cpp
        backend/spirv/emit_spirv_special.cpp
        frontend/ir/ir_emitter.cpp
        frontend/ir/microinstruction.cpp
        frontend/ir/opcodes.cpp
        # ISBE_nx2 adds a reviewed pseudo-opcode. The enum, decoder and
        # name table MUST be built against the same maintained maxwell.inc.
        frontend/maxwell/decode.cpp
        frontend/maxwell/opcodes.cpp
        frontend/maxwell/structured_control_flow.cpp
        frontend/maxwell/translate/impl/internal_stage_buffer_entry_read.cpp
        frontend/maxwell/translate_program.cpp
        ir_opt/collect_shader_info_pass.cpp
    )
    if(ENABLE_OPENGL)
        list(APPEND eden_mesh_source_paths
            backend/glasm/emit_glasm.cpp
            backend/glasm/emit_glasm_not_implemented.cpp
            backend/glasm/glasm_emit_context.cpp
            backend/glsl/emit_glsl_not_implemented.cpp
            backend/glsl/glsl_emit_context.cpp
        )
    endif()
    get_target_property(eden_mesh_shader_target_sources shader_recompiler SOURCES)
    foreach(eden_mesh_relative IN LISTS eden_mesh_source_paths)
        list(FIND eden_mesh_shader_target_sources "${eden_mesh_relative}" eden_mesh_source_idx)
        if(eden_mesh_source_idx LESS 0)
            message(FATAL_ERROR "Pinned Task/Mesh shader owner changed: ${eden_mesh_relative}")
        endif()
        list(REMOVE_ITEM eden_mesh_shader_target_sources "${eden_mesh_relative}")
        list(APPEND eden_mesh_shader_target_sources
            "${EDEN_NATIVE_TASK_MESH_ROOT}/shader_recompiler/${eden_mesh_relative}")
    endforeach()
    list(APPEND eden_mesh_shader_target_sources
        "${EDEN_NATIVE_TASK_MESH_ROOT}/shader_recompiler/backend/spirv/emit_spirv_mesh.cpp")
    set_property(TARGET shader_recompiler PROPERTY SOURCES "${eden_mesh_shader_target_sources}")
    target_include_directories(shader_recompiler BEFORE PRIVATE "${EDEN_NATIVE_TASK_MESH_ROOT}")
    # P5: native Task/Mesh also contributes the original maintained Vulkan
    # include directory. Place the CMake-selected ABI header overlay FIRST:
    # renderer_vulkan_r08, vk_blit_screen_r08 and window_adapt_pass_r08 must
    # be seen by their matching C++ implementations. Otherwise the older
    # vendor headers shadow the selected release headers and compilation
    # breaks on missing HUD/framegen members.
    target_include_directories(video_core BEFORE PRIVATE
        "${PORT_BUILD_DIR}/include"
        "${EDEN_NATIVE_TASK_MESH_ROOT}" "${EDEN_NATIVE_TASK_MESH_VULKAN_HEADERS}")
    target_include_directories(core BEFORE PRIVATE "${EDEN_NATIVE_TASK_MESH_ROOT}")
endif()

# P5 link parity: native shader atomic CAS owners
# The cached original source builds successfully but does not define all
# CAS symbols referenced by the pinned Task/Mesh opcode/dispatch headers.
# Select the COMPLETE audited implementations from the same pinned Eden
# source snapshot, including real SPIR-V OpAtomicCompareExchange, GLSL,
# GLASM fail-closed semantics, and the Maxwell ATOM.CAS translator.
# This is an NS1/NS2 shared compiler fix; no generated stubs or fake symbols.
if(PS5_NATIVE)
    set(EDEN_PINNED_SHADER_CAS_ROOT
        "${PORT_ROOT}/vendor/sources/eden/src/shader_recompiler")
    set(eden_native_cas_paths
        backend/spirv/emit_spirv_atomic.cpp
        frontend/maxwell/translate/impl/atomic_operations_global_memory.cpp)
    if(ENABLE_OPENGL)
        list(APPEND eden_native_cas_paths
            backend/glasm/emit_glasm_memory.cpp
            backend/glsl/emit_glsl_atomic.cpp)
    endif()
    get_target_property(eden_native_cas_sources shader_recompiler SOURCES)
    foreach(eden_cas_path IN LISTS eden_native_cas_paths)
        set(eden_cas_impl "${EDEN_PINNED_SHADER_CAS_ROOT}/${eden_cas_path}")
        if(NOT EXISTS "${eden_cas_impl}")
            message(FATAL_ERROR "Missing pinned shader CAS owner: ${eden_cas_path}")
        endif()
        list(FIND eden_native_cas_sources "${eden_cas_path}" eden_cas_original)
        if(eden_cas_original LESS 0)
            message(FATAL_ERROR "Missing native shader CAS source: ${eden_cas_path}")
        endif()
        list(REMOVE_ITEM eden_native_cas_sources "${eden_cas_path}")
        list(APPEND eden_native_cas_sources "${eden_cas_impl}")
    endforeach()
    set_property(TARGET shader_recompiler PROPERTY SOURCES
        "${eden_native_cas_sources}")
endif()

# R457 NS2 sparse residency: the guest kernel directly writes optimized
# management metadata and page-fill spans BEFORE any process PTE exists.
# The original compiled kernel source would dereference uncommitted 12GiB
# virtual holes. Select one reviewed research-only source with precommit guards.
if(PS5_NATIVE AND EDEN_NS2_SPARSE_BACKING)
    set(EDEN_R457_SPARSE_KERNEL_SRC
        "${PORT_ROOT}/vendor/encore-active/ns2-runtime/sparse-residency/core/hle/kernel/k_memory_manager.cpp")
    if(NOT EXISTS "${EDEN_R457_SPARSE_KERNEL_SRC}")
        message(FATAL_ERROR "R457 sparse physical native kernel owner missing")
    endif()
    get_target_property(eden_r457_sparse_kernel_units core SOURCES)
    list(FIND eden_r457_sparse_kernel_units
         "hle/kernel/k_memory_manager.cpp" eden_r457_sparse_kernel_original)
    if(eden_r457_sparse_kernel_original EQUAL -1)
        message(FATAL_ERROR "R457 sparse kernel must replace exactly the active KMemoryManager TU")
    endif()
    list(REMOVE_ITEM eden_r457_sparse_kernel_units
         "hle/kernel/k_memory_manager.cpp")
    list(APPEND eden_r457_sparse_kernel_units
         "${EDEN_R457_SPARSE_KERNEL_SRC}")
    set_property(TARGET core PROPERTY SOURCES
        "${eden_r457_sparse_kernel_units}")
endif()
