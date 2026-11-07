# Enter the pinned Eden Linux CMake build without editing its immutable tree.
# -DENCORE_R09_ROOT=<absolute engine checkout> must be provided by the caller.
# Registered only for the main Eden project, not any CPM dependency project.
if(PROJECT_NAME STREQUAL "yuzu" AND DEFINED ENCORE_R09_ROOT)
    cmake_language(DEFER DIRECTORY "${CMAKE_SOURCE_DIR}"
        CALL include "${ENCORE_R09_ROOT}/tools/graphics/r09_host_link_after.cmake")
endif()
