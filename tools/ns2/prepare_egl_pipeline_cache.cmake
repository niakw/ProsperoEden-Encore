# SPDX-License-Identifier: GPL-3.0-or-later
# N56: inject only the truncated-driver-cache guard into the maintained PS5 owner.
foreach(var IN ITEMS INPUT OUTPUT)
    if(NOT DEFINED ${var})
        message(FATAL_ERROR "N56 missing ${var}")
    endif()
endforeach()
if(NOT EXISTS "${INPUT}")
    message(FATAL_ERROR "N56 missing maintained native Vulkan cache owner: ${INPUT}")
endif()
file(READ "${INPUT}" body)
set(before [==[        u32 cache_version;
        file.read(magic_number.data(), magic_number.size())]==])
set(after [==[        u32 cache_version;
        // N56: reject truncated (including failed tellg) Vulkan driver caches
        // before reading their header or subtracting a size_t header length.
        if (end < std::streampos{static_cast<std::streamoff>(
                      magic_number.size() + sizeof(cache_version))}) {
            file.close();
            LOG_WARNING(Common_Filesystem, "Short Vulkan driver cache; rebuilding fresh");
            Common::FS::RemoveFile(filename);
            return create_pipeline_cache(0, nullptr);
        }
        file.read(magic_number.data(), magic_number.size())]==])
string(FIND "${body}" "${before}" first)
if(first LESS 0)
    message(FATAL_ERROR "N56 PS5 pipeline-cache source owner drift")
endif()
string(LENGTH "${before}" length)
math(EXPR start "${first} + ${length}")
string(SUBSTRING "${body}" ${start} -1 remainder)
string(FIND "${remainder}" "${before}" duplicate)
if(NOT duplicate LESS 0)
    message(FATAL_ERROR "N56 ambiguous pipeline-cache source owner")
endif()
# Existing native PS5 atomic writer MUST remain; never backport the PC writer.
string(FIND "${body}" "Saved PS5 driver pipeline cache atomically" atomic_writer)
if(atomic_writer LESS 0)
    message(FATAL_ERROR "N56 native PS5 atomic save path missing")
endif()
string(REPLACE "${before}" "${after}" body "${body}")
get_filename_component(folder "${OUTPUT}" DIRECTORY)
file(MAKE_DIRECTORY "${folder}")
file(WRITE "${OUTPUT}" "${body}")
