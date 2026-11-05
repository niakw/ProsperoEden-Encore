# P0.2: generate only the architecturally reviewed LDAPR acquire translation.
# Do not copy the research A64 overlay: its RETAA/RETAB PAC bypass and
# experimental LSE/CAS retry model are not admitted into the shipping JIT.
# This script is CMake -P compatible, so the exact source transformations can
# be exercised by a host-only test without a PS5 toolchain or executable.
if(NOT DEFINED EDEN_A64_LDAPR_SOURCE_ROOT OR NOT DEFINED EDEN_A64_LDAPR_OUTPUT_ROOT)
    message(FATAL_ERROR "LDAPR requires explicit pinned source and output directories")
endif()
set(eden_ldapr_source "${EDEN_A64_LDAPR_SOURCE_ROOT}/dynarmic/frontend/A64")
set(eden_ldapr_output "${EDEN_A64_LDAPR_OUTPUT_ROOT}/dynarmic/frontend/A64")
foreach(eden_ldapr_file IN ITEMS
        "decoder/a64.h" "decoder/a64.inc"
        "translate/impl/impl.h" "translate/impl/load_store_exclusive.cpp")
    if(NOT EXISTS "${eden_ldapr_source}/${eden_ldapr_file}")
        message(FATAL_ERROR "Missing pinned A64 LDAPR source: ${eden_ldapr_file}")
    endif()
    get_filename_component(eden_ldapr_dir "${eden_ldapr_output}/${eden_ldapr_file}" DIRECTORY)
    file(MAKE_DIRECTORY "${eden_ldapr_dir}")
endforeach()
configure_file("${eden_ldapr_source}/decoder/a64.h"
    "${eden_ldapr_output}/decoder/a64.h" COPYONLY)

file(READ "${eden_ldapr_source}/decoder/a64.inc" eden_ldapr_decoder)
set(eden_ldapr_decode_anchor "INST(RET, \"RET\", \"1101011001011111000000nnnnn00000\")")
if(NOT eden_ldapr_decoder MATCHES "INST\\(RET," OR
   eden_ldapr_decoder MATCHES "INST\\(LDAPR,")
    message(FATAL_ERROR "Pinned A64 decoder changed: re-audit LDAPR insertion")
endif()
string(REPLACE "${eden_ldapr_decode_anchor}"
    "${eden_ldapr_decode_anchor}\nINST(LDAPR, \"LDAPR\", \"ss11100010111111110000nnnnnttttt\")"
    eden_ldapr_decoder_out "${eden_ldapr_decoder}")
if(eden_ldapr_decoder_out STREQUAL eden_ldapr_decoder)
    message(FATAL_ERROR "Pinned A64 return decoder anchor absent")
endif()
file(WRITE "${eden_ldapr_output}/decoder/a64.inc" "${eden_ldapr_decoder_out}")

file(READ "${eden_ldapr_source}/translate/impl/impl.h" eden_ldapr_impl)
set(eden_ldapr_decl "bool LDAPR(Reg Rn, Reg Rt);")
if(NOT eden_ldapr_impl MATCHES "bool LDAPR\\(Reg Rn, Reg Rt\\)\\;" OR
   eden_ldapr_impl MATCHES "bool LDAPR\\(Imm<2> size,")
    message(FATAL_ERROR "Pinned A64 LDAPR declaration changed")
endif()
string(REPLACE "${eden_ldapr_decl}" "bool LDAPR(Imm<2> size, Reg Rn, Reg Rt);"
    eden_ldapr_impl_out "${eden_ldapr_impl}")
file(WRITE "${eden_ldapr_output}/translate/impl/impl.h" "${eden_ldapr_impl_out}")

file(READ "${eden_ldapr_source}/translate/impl/load_store_exclusive.cpp" eden_ldapr_exclusive)
set(eden_ldapr_namespace "namespace Dynarmic::A64 {\n")
if(NOT eden_ldapr_exclusive MATCHES "namespace Dynarmic::A64" OR
   eden_ldapr_exclusive MATCHES "TranslatorVisitor::LDAPR\\(")
    message(FATAL_ERROR "Pinned A64 load/store translation changed")
endif()
# LDAPR (RCpc acquire) is conservatively implemented by LDAR (stronger
# acquire ordering), preserving original register width, SP and Rt semantics.
# No architecture-wide flag is set; NS1 keeps every existing decoder rule.
string(REPLACE "${eden_ldapr_namespace}"
    "${eden_ldapr_namespace}\n// Reviewed RCpc LDAPR: LDAR's acquire ordering is strictly stronger.\nbool TranslatorVisitor::LDAPR(Imm<2> size, Reg Rn, Reg Rt) {\n    return LDAR(size, Rn, Rt);\n}\n"
    eden_ldapr_exclusive_out "${eden_ldapr_exclusive}")
if(eden_ldapr_exclusive_out STREQUAL eden_ldapr_exclusive)
    message(FATAL_ERROR "Pinned A64 exclusive translator namespace changed")
endif()
file(WRITE "${eden_ldapr_output}/translate/impl/load_store_exclusive.cpp"
    "${eden_ldapr_exclusive_out}")
