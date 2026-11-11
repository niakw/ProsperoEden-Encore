# SPDX-License-Identifier: GPL-3.0-or-later
# Add our frontend after the pinned project's real core targets exist.
set(EDEN_PORT_DIR "${CMAKE_CURRENT_LIST_DIR}")
function(add_eden_headless)
    include("${EDEN_PORT_DIR}/CMakeLists.txt")
endfunction()
cmake_language(DEFER CALL add_eden_headless)
# One header is replaced for every target: common/sparse_large_vector.h, whose inline functions
# decide how Eden's large tables take their memory (headless/CMakeLists.txt copies the complete
# Encore-maintained header). This runs before any target exists, so the folder leads every include path: a source
# file that saw the original would mix two ways of committing the same table.
include_directories(BEFORE "${CMAKE_BINARY_DIR}/headless/sparse")
# The program names its sources in log lines and assertions. In a console build they are written
# relative to the trees they come from (src/..., build/..., headless/...), not with the folders of
# the machine that built it: a package must not carry those. Before any target exists, so it holds
# for every one.
if(PS5_NATIVE)
    # SDL3 is kept only for host-oriented dependencies; Encore removes its
    # SDL audio sink and uses the native PS5 audio path (see CMakeLists.txt).
    # Do not probe the host runner for Linux ALSA on the PS5 target.
    set(SDL_ALSA OFF CACHE BOOL "PS5 uses the native audio backend, not Linux ALSA" FORCE)
    get_filename_component(EDEN_PORT_ROOT "${EDEN_PORT_DIR}/.." ABSOLUTE)
    # The pinned Opus CPM snapshot is Xiph v1.6.1 + 6 commits
    # (upstream a3f0ec02b342, after signed v1.6.1 tag 22244de5).
    # Its archive has neither .git nor package_version, so upstream CMake
    # otherwise reports an invented project version "0" at configure time,
    # also affecting opus_get_version_string(). Supply its traceable
    # git-describe identity ONLY for this exact PS5 snapshot. The normal
    # variable is intentionally not cached, and no vendor file is patched.
    if(EXISTS "${EDEN_PORT_ROOT}/vendor/sources/eden-cpm/opus/a3f0ec02b3/cmake/OpusPackageVersion.cmake")
        set(OPUS_PACKAGE_VERSION "1.6.1-6-ga3f0ec02b342")
    endif()
    # CMake forbids add_subdirectory() in cmake_language(DEFER) callbacks.
    # Register the pinned WebP target during the real project(yuzu) configure
    # phase; the deferred Encore frontend may only link the existing target.
    set(EDEN_WEBP_ROOT "${EDEN_PORT_ROOT}/vendor/sources/libwebp")
    if(NOT EXISTS "${EDEN_WEBP_ROOT}/CMakeLists.txt")
        message(FATAL_ERROR "Pinned libwebp sources absent from sole vendor submodule")
    endif()
    set(WEBP_ENABLE_SIMD OFF CACHE BOOL "" FORCE)
    set(WEBP_USE_THREAD OFF CACHE BOOL "" FORCE)
    set(WEBP_BUILD_CWEBP OFF CACHE BOOL "" FORCE)
    set(WEBP_BUILD_DWEBP OFF CACHE BOOL "" FORCE)
    set(WEBP_BUILD_GIF2WEBP OFF CACHE BOOL "" FORCE)
    set(WEBP_BUILD_IMG2WEBP OFF CACHE BOOL "" FORCE)
    set(WEBP_BUILD_VWEBP OFF CACHE BOOL "" FORCE)
    set(WEBP_BUILD_WEBPINFO OFF CACHE BOOL "" FORCE)
    set(WEBP_BUILD_WEBPMUX OFF CACHE BOOL "" FORCE)
    set(WEBP_BUILD_LIBWEBPMUX OFF CACHE BOOL "" FORCE)
    set(WEBP_BUILD_ANIM_UTILS OFF CACHE BOOL "" FORCE)
    set(WEBP_BUILD_EXTRAS OFF CACHE BOOL "" FORCE)
    set(WEBP_LINK_STATIC ON CACHE BOOL "" FORCE)
    add_subdirectory("${EDEN_WEBP_ROOT}" "${CMAKE_BINARY_DIR}/headless/libwebp" EXCLUDE_FROM_ALL)
    add_compile_options("-ffile-prefix-map=${CMAKE_SOURCE_DIR}/="
                        "-ffile-prefix-map=${CMAKE_BINARY_DIR}/=build/"
                        "-ffile-prefix-map=${EDEN_PORT_ROOT}/=")
endif()
