# SPDX-License-Identifier: GPL-3.0-or-later
# N3v: inject a bounded diagnostic into the actual pinned kernel SVC owner.
# The generated C++ is build-only; vendor stays immutable.
if(NOT DEFINED INPUT OR NOT DEFINED OUTPUT)
    message(FATAL_ERROR "Usage: cmake -DINPUT=<svc.cpp> -DOUTPUT=<generated.cpp> -P script")
endif()
if(NOT EXISTS "${INPUT}")
    message(FATAL_ERROR "Missing maintained SVC owner: ${INPUT}")
endif()
file(READ "${INPUT}" svc_source)
set(include_anchor "#include \"core/hle/kernel/svc.h\"")
set(call_anchor "    auto& process = GetCurrentProcess(kernel);\n    std::array<uint64_t, 8> args;")
foreach(anchor IN ITEMS include_anchor call_anchor)
    string(FIND "${svc_source}" "${${anchor}}" first)
    if(first EQUAL -1)
        message(FATAL_ERROR "Native kernel SVC owner changed: missing ${anchor}")
    endif()
    string(SUBSTRING "${svc_source}" 0 ${first} before)
    string(LENGTH "${${anchor}}" length)
    math(EXPR beyond "${first} + ${length}")
    string(SUBSTRING "${svc_source}" ${beyond} -1 after)
    string(FIND "${after}" "${${anchor}}" duplicate)
    if(NOT duplicate EQUAL -1)
        message(FATAL_ERROR "Native kernel SVC owner changed: ambiguous ${anchor}")
    endif()
endforeach()
string(REPLACE "${include_anchor}"
    "${include_anchor}\n#include \"core/loader/ns2_svc_trace.h\""
    svc_source "${svc_source}")
string(REPLACE "${call_anchor}"
    "    auto& process = GetCurrentProcess(kernel);\n    if (const auto sample = Eden::NS2::SvcTrace::Next(process.GetProcessId())) {\n        LOG_INFO(Kernel_SVC, \"NS2 real HLE SVC[{}] pid={} imm={:#x} permitted={}\",\n                 *sample, process.GetProcessId(), imm, process.IsPermittedSvc(imm));\n    }\n    std::array<uint64_t, 8> args;"
    svc_source "${svc_source}")
get_filename_component(output_dir "${OUTPUT}" DIRECTORY)
file(MAKE_DIRECTORY "${output_dir}")
file(WRITE "${OUTPUT}" "${svc_source}")
