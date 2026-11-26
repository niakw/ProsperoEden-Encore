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
    # Set platform identity before any Eden target or dependency is created.
    # Directory definitions inherit into all child directories, including
    # common, core, video_core, shader_recompiler, audio_core and Dynarmic.
    # A target-local define on the launcher cannot cover shared header ABIs.
    add_compile_definitions(PS5_NATIVE=1)
    # SDL3 is kept only for host-oriented dependencies; Encore removes its
    # SDL audio sink and uses the native PS5 audio path (see CMakeLists.txt).
    # Do not probe the Linux runner for desktop/audio/input backends which cannot
    # become PS5 runtime dependencies. SDL's own CMake FAQ recommends the Unix
    # console profile when no X11/Wayland window is needed; the pinned SDL 3.4.8
    # still probes optional Unix backends unless they are explicitly disabled.
    set(SDL_ALSA OFF CACHE BOOL "PS5 uses the native audio backend, not Linux ALSA" FORCE)
    set(SDL_JACK OFF CACHE BOOL "PS5 does not use Linux JACK" FORCE)
    set(SDL_PIPEWIRE OFF CACHE BOOL "PS5 does not use Linux PipeWire" FORCE)
    set(SDL_PULSEAUDIO OFF CACHE BOOL "PS5 does not use Linux PulseAudio" FORCE)
    set(SDL_SNDIO OFF CACHE BOOL "PS5 does not use Unix sndio" FORCE)
    set(SDL_X11 OFF CACHE BOOL "PS5 has no X11 window system" FORCE)
    set(SDL_WAYLAND OFF CACHE BOOL "PS5 has no Wayland window system" FORCE)
    set(SDL_KMSDRM OFF CACHE BOOL "PS5 does not use Linux KMS/DRM" FORCE)
    set(SDL_FRIBIDI OFF CACHE BOOL "PS5 SDL does not provide X11 text shaping" FORCE)
    set(SDL_LIBTHAI OFF CACHE BOOL "PS5 SDL does not provide X11 Thai input" FORCE)
    set(SDL_IBUS OFF CACHE BOOL "PS5 SDL does not use Linux IBus" FORCE)
    set(SDL_LIBUDEV OFF CACHE BOOL "PS5 SDL does not enumerate Linux udev devices" FORCE)
    set(SDL_HIDAPI_LIBUSB OFF CACHE BOOL "PS5 controllers use the native input path" FORCE)
    set(SDL_LIBURING OFF CACHE BOOL "PS5 SDL does not use Linux io_uring" FORCE)
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
