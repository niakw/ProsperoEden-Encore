# P0 NS2: stage the reviewed ARMv8.1-ARMv8.5 A64 owners as complete files.
# Upstream source: Lichii 11aac324, whose parent Dynarmic blobs are identical
# to Encore's pinned base. No C++ is generated or text-patched here.
if(NOT DEFINED EDEN_A64_V81_V85_SOURCE_ROOT OR
   NOT DEFINED EDEN_A64_V81_V85_OUTPUT_ROOT)
    message(FATAL_ERROR "NS2 A64 v8.1-v8.5 requires explicit pinned source and output directories")
endif()

set(eden_a64_source "${EDEN_A64_V81_V85_SOURCE_ROOT}/dynarmic/frontend/A64")
set(eden_a64_output "${EDEN_A64_V81_V85_OUTPUT_ROOT}/dynarmic/frontend/A64")
# Historical directory name 'ldapr' remains the versioned vendor owner path;
# its content is now the reviewed full ARMv8.1-v8.5 promotion.
set(eden_a64_static
    "${CMAKE_CURRENT_LIST_DIR}/../vendor/encore-active/ns2-runtime/ldapr/maintained/dynarmic/frontend/A64")

foreach(eden_a64_file IN ITEMS
        "decoder/a64.h"
        "decoder/a64.inc"
        "translate/impl/impl.h"
        "translate/impl/load_store_exclusive.cpp"
        "translate/impl/a64_branch.cpp"
        "translate/impl/load_store_atomic.cpp"
        "translate/impl/memory_tagging.cpp"
        "translate/impl/pointer_authentication.cpp")
    if(NOT EXISTS "${eden_a64_source}/${eden_a64_file}" OR
       NOT EXISTS "${eden_a64_static}/${eden_a64_file}")
        message(FATAL_ERROR "Missing reviewed NS2 A64 owner: ${eden_a64_file}")
    endif()
    get_filename_component(eden_a64_dir
        "${eden_a64_output}/${eden_a64_file}" DIRECTORY)
    file(MAKE_DIRECTORY "${eden_a64_dir}")
    configure_file("${eden_a64_static}/${eden_a64_file}"
        "${eden_a64_output}/${eden_a64_file}" COPYONLY)
endforeach()
