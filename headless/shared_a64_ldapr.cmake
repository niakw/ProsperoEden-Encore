# Validate the canonical ARMv8.1-v8.5 Dynarmic owner set.
# Selection is direct from encore-active; this file never copies or generates C++.
if(NOT DEFINED EDEN_A64_V81_V85_ACTIVE_ROOT)
    message(FATAL_ERROR "A64 v8.1-v8.5 requires the canonical active Dynarmic root")
endif()
set(eden_a64_owner "${EDEN_A64_V81_V85_ACTIVE_ROOT}/dynarmic/frontend/A64")
foreach(eden_a64_file IN ITEMS
        "decoder/a64.h" "decoder/a64.inc"
        "translate/impl/impl.h"
        "translate/impl/load_store_exclusive.cpp"
        "translate/impl/a64_branch.cpp"
        "translate/impl/load_store_atomic.cpp"
        "translate/impl/memory_tagging.cpp"
        "translate/impl/pointer_authentication.cpp")
    if(NOT EXISTS "${eden_a64_owner}/${eden_a64_file}")
        message(FATAL_ERROR "Missing canonical maintained A64 owner: ${eden_a64_file}")
    endif()
endforeach()
