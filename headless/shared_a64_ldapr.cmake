# P0.2: stage audited full A64/LDAPR owner sources, never generate C++.
# The retained host contract compares these files byte-for-byte against
# pinned Dynarmic + only the reviewed stronger-acquire LDAPR adaptation.
# RETAA/PAC and CAS/LSE experimental decoders are not selected.
if(NOT DEFINED EDEN_A64_LDAPR_SOURCE_ROOT OR NOT DEFINED EDEN_A64_LDAPR_OUTPUT_ROOT)
    message(FATAL_ERROR "LDAPR requires explicit pinned source and output directories")
endif()
set(eden_ldapr_source "${EDEN_A64_LDAPR_SOURCE_ROOT}/dynarmic/frontend/A64")
set(eden_ldapr_output "${EDEN_A64_LDAPR_OUTPUT_ROOT}/dynarmic/frontend/A64")
set(eden_ldapr_static "${CMAKE_CURRENT_LIST_DIR}/../vendor/encore-active/ns2-runtime/ldapr/maintained/dynarmic/frontend/A64")
foreach(eden_ldapr_file IN ITEMS
        "decoder/a64.h" "decoder/a64.inc"
        "translate/impl/impl.h" "translate/impl/load_store_exclusive.cpp")
    if(NOT EXISTS "${eden_ldapr_source}/${eden_ldapr_file}" OR
       NOT EXISTS "${eden_ldapr_static}/${eden_ldapr_file}")
        message(FATAL_ERROR "Missing reviewed LDAPR source: ${eden_ldapr_file}")
    endif()
    get_filename_component(eden_ldapr_dir
        "${eden_ldapr_output}/${eden_ldapr_file}" DIRECTORY)
    file(MAKE_DIRECTORY "${eden_ldapr_dir}")
    configure_file("${eden_ldapr_static}/${eden_ldapr_file}"
        "${eden_ldapr_output}/${eden_ldapr_file}" COPYONLY)
endforeach()
