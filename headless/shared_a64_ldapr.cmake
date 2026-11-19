# P0.2: stage reviewed Switch 2 ARMv8.1-8.5 A64 owner sources, never generate C++.
# Vendor #192 promotes the exact Lichii 11aac324 decoder/translator blobs for
# LDAPR, RETAA/B, LSE/CAS/CASP/SWP, pointer-auth compatibility and the MTE
# subset used by NX2. The engine enables their translator units only on the
# reviewed native dual-NPDM target; NS1 source selection remains unchanged.
if(NOT DEFINED EDEN_A64_LDAPR_SOURCE_ROOT OR NOT DEFINED EDEN_A64_LDAPR_OUTPUT_ROOT)
    message(FATAL_ERROR "LDAPR requires explicit pinned source and output directories")
endif()
set(eden_ldapr_source "${EDEN_A64_LDAPR_SOURCE_ROOT}/dynarmic/frontend/A64")
set(eden_ldapr_output "${EDEN_A64_LDAPR_OUTPUT_ROOT}/dynarmic/frontend/A64")
set(eden_ldapr_static "${CMAKE_CURRENT_LIST_DIR}/../vendor/encore-active/ns2-runtime/ldapr/maintained/dynarmic/frontend/A64")
foreach(eden_ldapr_file IN ITEMS
        "decoder/a64.h" "decoder/a64.inc"
        "translate/impl/impl.h" "translate/impl/load_store_exclusive.cpp"
        "translate/impl/a64_branch.cpp"
        "translate/impl/load_store_atomic.cpp"
        "translate/impl/memory_tagging.cpp"
        "translate/impl/pointer_authentication.cpp")
    if(NOT EXISTS "${eden_ldapr_source}/${eden_ldapr_file}" OR
       NOT EXISTS "${eden_ldapr_static}/${eden_ldapr_file}")
        message(FATAL_ERROR "Missing reviewed A64 source: ${eden_ldapr_file}")
    endif()
    get_filename_component(eden_ldapr_dir
        "${eden_ldapr_output}/${eden_ldapr_file}" DIRECTORY)
    file(MAKE_DIRECTORY "${eden_ldapr_dir}")
    configure_file("${eden_ldapr_static}/${eden_ldapr_file}"
        "${eden_ldapr_output}/${eden_ldapr_file}" COPYONLY)
endforeach()
