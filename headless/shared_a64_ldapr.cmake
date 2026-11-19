# P0.2: stage the exact reviewed ARMv8.1-v8.5 A64 owners from vendor #192.
# The vendor source is an exact backport of Lichii 11aac324 onto the
# byte-identical pinned Dynarmic parent. Keep this as source-complete COPYONLY
# staging: no generated C++, no title-specific decoder and no research flag.
if(NOT DEFINED EDEN_A64_V81_V85_SOURCE_ROOT OR NOT DEFINED EDEN_A64_V81_V85_OUTPUT_ROOT)
    message(FATAL_ERROR "A64 v8.1-v8.5 requires explicit pinned source and output directories")
endif()
set(eden_ldapr_source "${EDEN_A64_V81_V85_SOURCE_ROOT}/dynarmic/frontend/A64")
set(eden_ldapr_output "${EDEN_A64_V81_V85_OUTPUT_ROOT}/dynarmic/frontend/A64")
set(eden_ldapr_static "${CMAKE_CURRENT_LIST_DIR}/../vendor/encore-active/ns2-runtime/ldapr/maintained/dynarmic/frontend/A64")
# Lichii 11aac324 adds three implementation units absent from the pinned
# Dynarmic base. The other five owners modify files already present there.
# The copied maintained sources have independent exact-blob vendor checks.
set(eden_ldapr_added_sources
    "translate/impl/load_store_atomic.cpp"
    "translate/impl/memory_tagging.cpp"
    "translate/impl/pointer_authentication.cpp")
foreach(eden_ldapr_file IN ITEMS
        "decoder/a64.h" "decoder/a64.inc"
        "translate/impl/impl.h" "translate/impl/load_store_exclusive.cpp"
        "translate/impl/a64_branch.cpp"
        "translate/impl/load_store_atomic.cpp"
        "translate/impl/memory_tagging.cpp"
        "translate/impl/pointer_authentication.cpp")
    if(NOT EXISTS "${eden_ldapr_static}/${eden_ldapr_file}")
        message(FATAL_ERROR "Missing reviewed maintained A64 source: ${eden_ldapr_file}")
    endif()
    # Also runs under cmake -P: avoid IN_LIST (CMP0057 defaults to OLD there).
    list(FIND eden_ldapr_added_sources "${eden_ldapr_file}" eden_ldapr_new_index)
    if(NOT eden_ldapr_new_index EQUAL -1)
        if(EXISTS "${eden_ldapr_source}/${eden_ldapr_file}")
            message(FATAL_ERROR "Unexpected new A64 owner in pinned base; requalify overlay: ${eden_ldapr_file}")
        endif()
    elseif(NOT EXISTS "${eden_ldapr_source}/${eden_ldapr_file}")
        message(FATAL_ERROR "Missing reviewed baseline A64 source: ${eden_ldapr_file}")
    endif()
    get_filename_component(eden_ldapr_dir
        "${eden_ldapr_output}/${eden_ldapr_file}" DIRECTORY)
    file(MAKE_DIRECTORY "${eden_ldapr_dir}")
    configure_file("${eden_ldapr_static}/${eden_ldapr_file}"
        "${eden_ldapr_output}/${eden_ldapr_file}" COPYONLY)
endforeach()
