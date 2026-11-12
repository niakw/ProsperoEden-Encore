# Eden Encore R23 — consolidated native source-owner staging for final vendor main.
# Keep exactly one compiler owner per touched source.

# Engine research PR #59
# R23 #153 — exactly two maintained Opus decoder compiler units on PS5.
# Don't replace the vendor source tree or compile both old/new units.
# Overlay only the two changed public headers, not the whole maintained root.
if(PS5_NATIVE)
    set(EDEN_OPUS_ACTIVE "${PORT_ROOT}/vendor/encore-active/eden-core/src")
    set(EDEN_OPUS_HEADER_ROOT "${PORT_BUILD_DIR}/r23-opus/include")
    foreach(eden_opus_header IN ITEMS
            "audio_core/opus/hardware_opus.h"
            "core/hle/service/audio/errors.h")
        if(NOT EXISTS "${EDEN_OPUS_ACTIVE}/${eden_opus_header}")
            message(FATAL_ERROR "R23 #153 maintained Opus header missing: ${eden_opus_header}")
        endif()
        configure_file("${EDEN_OPUS_ACTIVE}/${eden_opus_header}"
                       "${EDEN_OPUS_HEADER_ROOT}/${eden_opus_header}" COPYONLY)
    endforeach()
    get_target_property(eden_opus_sources audio_core SOURCES)
    foreach(eden_opus_relative IN ITEMS
            "opus/hardware_opus.cpp" "opus/decoder.cpp")
        list(FIND eden_opus_sources "${eden_opus_relative}" eden_opus_original)
        if(eden_opus_original LESS 0)
            message(FATAL_ERROR "R23 #153 pinned Opus TU absent: ${eden_opus_relative}")
        endif()
        if(NOT EXISTS "${EDEN_OPUS_ACTIVE}/audio_core/${eden_opus_relative}")
            message(FATAL_ERROR "R23 #153 maintained Opus TU absent: ${eden_opus_relative}")
        endif()
        list(REMOVE_ITEM eden_opus_sources "${eden_opus_relative}")
        list(APPEND eden_opus_sources
             "${EDEN_OPUS_ACTIVE}/audio_core/${eden_opus_relative}")
    endforeach()
    set_property(TARGET audio_core PROPERTY SOURCES "${eden_opus_sources}")
    target_include_directories(audio_core BEFORE PRIVATE "${EDEN_OPUS_HEADER_ROOT}")
    target_include_directories(core BEFORE PRIVATE "${EDEN_OPUS_HEADER_ROOT}")
    message(STATUS "R23 #153: one PS5-maintained Opus owner per TU and two exact headers")
endif()


# Engine research PR #60
# R23 #46 — compile the bounded cheat parser from exactly one maintained
# full TU, never modify the immutable checked-out Eden source during CMake.
if(PS5_NATIVE)
    set(EDEN_R23_CHEATS
        "${PORT_ROOT}/vendor/encore-active/eden-core/src/core/memory/cheat_engine.cpp")
    if(NOT EXISTS "${EDEN_R23_CHEATS}")
        message(FATAL_ERROR "R23 #46 maintained cheat_engine.cpp source absent")
    endif()
    get_target_property(eden_r23_cheat_sources core SOURCES)
    list(FIND eden_r23_cheat_sources "memory/cheat_engine.cpp" eden_r23_old_cheats)
    if(eden_r23_old_cheats EQUAL -1)
        message(FATAL_ERROR "R23 #46 original cheat TU owner changed")
    endif()
    list(REMOVE_ITEM eden_r23_cheat_sources "memory/cheat_engine.cpp")
    list(APPEND eden_r23_cheat_sources "${EDEN_R23_CHEATS}")
    set_property(TARGET core PROPERTY SOURCES "${eden_r23_cheat_sources}")
    # The runtime cheat API adds a mutex/DTO to the actual CheatEngine class.
    # Compile the selected TU with its matching header, never the pristine ABI.
    set(EDEN_R23_CHEATS_HEADER
        "${PORT_ROOT}/vendor/encore-active/eden-core/include/core/memory/cheat_engine.h")
    if(NOT EXISTS "${EDEN_R23_CHEATS_HEADER}")
        message(FATAL_ERROR "R23 #46 selected synchronized cheat_engine.h missing")
    endif()
    set(EDEN_R23_CHEATS_INCLUDE "${PORT_BUILD_DIR}/r23-cheats/include")
    configure_file("${EDEN_R23_CHEATS_HEADER}"
                   "${EDEN_R23_CHEATS_INCLUDE}/core/memory/cheat_engine.h" COPYONLY)
    target_include_directories(core BEFORE PRIVATE "${EDEN_R23_CHEATS_INCLUDE}")
    message(STATUS "R23 #46 selected bounded cheat parser, runtime toggle and matching header")
endif()


# Engine research PR #61
# R23 #11 — four complete maintained x64 emitter units. Explicitly
# replace original CMake source owners, never append duplicate symbols.
if(PS5_NATIVE)
    set(EDEN_R23_X64_EMIT_ROOT
        "${PORT_ROOT}/vendor/encore-active/eden-core/src/dynarmic/backend/x64")
    get_target_property(eden_r23_jit_units dynarmic SOURCES)
    foreach(eden_r23_jit_name IN ITEMS
            emit_x64_floating_point.cpp
            emit_x64_sm4.cpp
            emit_x64_vector.cpp
            emit_x64_vector_floating_point.cpp)
        if(NOT EXISTS "${EDEN_R23_X64_EMIT_ROOT}/${eden_r23_jit_name}")
            message(FATAL_ERROR "Missing maintained R23 x64 emitter ${eden_r23_jit_name}")
        endif()
        list(FIND eden_r23_jit_units
                  "backend/x64/${eden_r23_jit_name}" eden_r23_jit_old)
        if(eden_r23_jit_old LESS 0)
            message(FATAL_ERROR "R23 x64 emitter source owner changed: ${eden_r23_jit_name}")
        endif()
        list(REMOVE_ITEM eden_r23_jit_units
             "backend/x64/${eden_r23_jit_name}")
        list(APPEND eden_r23_jit_units
             "${EDEN_R23_X64_EMIT_ROOT}/${eden_r23_jit_name}")
    endforeach()
    set_property(TARGET dynarmic PROPERTY SOURCES "${eden_r23_jit_units}")
    message(STATUS "R23 #11: exactly four reviewed maintained x64 emitter owners")
endif()


# Engine research PR #62
# R23 #11 A32 crypto: six opcodes need a coherent four-fragment graph.
# A32 translation includes .cpp fragments; asimd.h includes "./asimd.inc"
# relative to its own file. Shadow both ASIMD neighbors and the translator
# headers/fragments in a private native build include tree, not vendor originals.
if(PS5_NATIVE)
    set(EDEN_R23_A32_SOURCE
        "${PORT_ROOT}/vendor/encore-active/eden-core/src/dynarmic")
    set(EDEN_R23_A32_OVERLAY "${PORT_BUILD_DIR}/r23-a32-sha1")
    foreach(a32_path IN ITEMS
            "frontend/A32/decoder/asimd.inc"
            "frontend/A32/translate/impl/a32_translate_impl.h"
            "frontend/A32/translate/impl/asimd_three_regs.cpp"
            "frontend/A32/translate/impl/asimd_two_regs_misc.cpp")
        if(NOT EXISTS "${EDEN_R23_A32_SOURCE}/${a32_path}")
            message(FATAL_ERROR "R23 #11 missing maintained A32 crypto ${a32_path}")
        endif()
        configure_file("${EDEN_R23_A32_SOURCE}/${a32_path}"
             "${EDEN_R23_A32_OVERLAY}/dynarmic/${a32_path}" COPYONLY)
    endforeach()
    set(EDEN_R23_A32_DECODER_HEADER
        "${PORT_ROOT}/vendor/sources/eden/src/dynarmic/src/dynarmic/frontend/A32/decoder/asimd.h")
    if(NOT EXISTS "${EDEN_R23_A32_DECODER_HEADER}")
        message(FATAL_ERROR "R23 #11 pinned A32 decoder header moved")
    endif()
    configure_file("${EDEN_R23_A32_DECODER_HEADER}"
        "${EDEN_R23_A32_OVERLAY}/dynarmic/frontend/A32/decoder/asimd.h" COPYONLY)
    get_target_property(eden_r23_a32_units dynarmic SOURCES)
    list(FIND eden_r23_a32_units
         "frontend/A32/translate/a32_translate.cpp" eden_r23_a32_owner)
    if(eden_r23_a32_owner EQUAL -1)
        message(FATAL_ERROR "R23 #11 native A32 amalgamating TU changed")
    endif()
    target_include_directories(dynarmic BEFORE PRIVATE "${EDEN_R23_A32_OVERLAY}")
    message(STATUS "R23 #11: selected A32 decoder, visitor and SHA1 .cpp fragment quartet")
endif()


# Engine research PR #64
# NS1 R23 #113: one coherent FS parent-sharing header API for the three
# already selected maintained compiler units. Keep all current NCZ, IPS,
# mod-root-null, and save owner selections above: no duplicate TU compilation.
if(PS5_NATIVE)
    set(EDEN_R23_PARENT_FS_SOURCE
        "${PORT_ROOT}/vendor/encore-active/eden-core")
    set(EDEN_R23_PARENT_FS_INCLUDES
        "${PORT_BUILD_DIR}/r23-parent-fs/include")
    foreach(eden_r23_fs_name IN ITEMS
            "patch_manager"
            "registered_cache"
            "savedata_factory")
        set(eden_r23_fs_header
            "${EDEN_R23_PARENT_FS_SOURCE}/include/core/file_sys/${eden_r23_fs_name}.h")
        set(eden_r23_fs_cpp
            "${EDEN_R23_PARENT_FS_SOURCE}/src/core/file_sys/${eden_r23_fs_name}.cpp")
        if(NOT EXISTS "${eden_r23_fs_header}" OR NOT EXISTS "${eden_r23_fs_cpp}")
            message(FATAL_ERROR
                "R23 #113 full maintained FS owner missing: ${eden_r23_fs_name}")
        endif()
        configure_file("${eden_r23_fs_header}"
            "${EDEN_R23_PARENT_FS_INCLUDES}/core/file_sys/${eden_r23_fs_name}.h"
            COPYONLY)
        get_target_property(eden_r23_fs_units core SOURCES)
        list(FIND eden_r23_fs_units "${eden_r23_fs_cpp}" eden_r23_fs_existing)
        if(eden_r23_fs_existing LESS 0)
            message(FATAL_ERROR
                "R23 #113 native FS TU source owner drift: ${eden_r23_fs_name}")
        endif()
    endforeach()
    target_include_directories(core BEFORE PUBLIC "${EDEN_R23_PARENT_FS_INCLUDES}")
    message(STATUS "R23 #113: three native FS TUs selected once with matched maintained headers")
endif()


# Engine research PR #65
# R23 #48 VP9: this source pair must be selected together. The header
# extends the native Vp9PictureInfo ABI and the .cpp consumes those fields.
if(PS5_NATIVE)
    set(EDEN_R23_VP9_ROOT
        "${PORT_ROOT}/vendor/encore-active/eden-core/src/video_core/host1x")
    set(EDEN_R23_VP9_INCLUDE "${PORT_BUILD_DIR}/r23-vp9/include")
    if(NOT EXISTS "${EDEN_R23_VP9_ROOT}/codec_types.h"
       OR NOT EXISTS "${EDEN_R23_VP9_ROOT}/codecs/vp9.cpp")
        message(FATAL_ERROR "R23 #48 reviewed VP9 source/header pair is incomplete")
    endif()
    configure_file("${EDEN_R23_VP9_ROOT}/codec_types.h"
        "${EDEN_R23_VP9_INCLUDE}/video_core/host1x/codec_types.h" COPYONLY)
    get_target_property(eden_r23_vp9_units video_core SOURCES)
    list(FIND eden_r23_vp9_units "host1x/codecs/vp9.cpp" eden_r23_vp9_old)
    if(eden_r23_vp9_old LESS 0)
        message(FATAL_ERROR "R23 #48 pinned VP9 decoder source owner changed")
    endif()
    list(REMOVE_ITEM eden_r23_vp9_units "host1x/codecs/vp9.cpp")
    list(APPEND eden_r23_vp9_units "${EDEN_R23_VP9_ROOT}/codecs/vp9.cpp")
    set_property(TARGET video_core PROPERTY SOURCES "${eden_r23_vp9_units}")
    target_include_directories(video_core BEFORE PUBLIC "${EDEN_R23_VP9_INCLUDE}")
    target_include_directories(core BEFORE PUBLIC "${EDEN_R23_VP9_INCLUDE}")
    message(STATUS "R23 #48: coherent VP9 frame metadata and single maintained decoder")
endif()


# Engine research PR #66
# R23 #120: SSL IPC API and OpenSSL implementation are inseparable.
# One native source owner per original TU and one matching shared header.
if(PS5_NATIVE)
    set(EDEN_R23_SSL_ROOT
        "${PORT_ROOT}/vendor/encore-active/eden-core/src/core/hle/service/ssl")
    set(EDEN_R23_SSL_OVERLAY "${PORT_BUILD_DIR}/r23-ssl/include")
    foreach(eden_r23_ssl_file IN ITEMS ssl.cpp ssl_backend.h ssl_backend_openssl.cpp)
        if(NOT EXISTS "${EDEN_R23_SSL_ROOT}/${eden_r23_ssl_file}")
            message(FATAL_ERROR "R23 #120 missing native SSL ${eden_r23_ssl_file}")
        endif()
    endforeach()
    configure_file("${EDEN_R23_SSL_ROOT}/ssl_backend.h"
        "${EDEN_R23_SSL_OVERLAY}/core/hle/service/ssl/ssl_backend.h" COPYONLY)
    get_target_property(eden_r23_ssl_units core SOURCES)
    foreach(eden_r23_ssl_unit IN ITEMS ssl.cpp ssl_backend_openssl.cpp)
        list(FIND eden_r23_ssl_units
            "hle/service/ssl/${eden_r23_ssl_unit}" eden_r23_ssl_pinned)
        if(eden_r23_ssl_pinned LESS 0)
            message(FATAL_ERROR "R23 #120 SSL source graph changed: ${eden_r23_ssl_unit}")
        endif()
        list(REMOVE_ITEM eden_r23_ssl_units "hle/service/ssl/${eden_r23_ssl_unit}")
        list(APPEND eden_r23_ssl_units "${EDEN_R23_SSL_ROOT}/${eden_r23_ssl_unit}")
    endforeach()
    set_property(TARGET core PROPERTY SOURCES "${eden_r23_ssl_units}")
    target_include_directories(core BEFORE PRIVATE "${EDEN_R23_SSL_OVERLAY}")
    message(STATUS "R23 #120: exactly two SSL translation units and matched backend header")
endif()


# Engine research PR #67
# R23 #1: the 23.5.0 NS qlaunch event/IPC dispatch needs the exact
# prepared current backport and matching header. Never add a second NS TU.
if(PS5_NATIVE)
    set(EDEN_R23_FW235_NS_SOURCE
        "${PORT_ROOT}/vendor/encore-active/eden-backports/src/core/hle/service/ns")
    set(EDEN_R23_FW235_NS_INCLUDE "${PORT_BUILD_DIR}/r23-fw235-ns/include")
    if(NOT EXISTS "${EDEN_R23_FW235_NS_SOURCE}/application_manager_interface.cpp"
       OR NOT EXISTS "${EDEN_R23_FW235_NS_SOURCE}/application_manager_interface.h")
        message(FATAL_ERROR "R23 #1 maintained FW23.5 NS source/header mismatch")
    endif()
    configure_file("${EDEN_R23_FW235_NS_SOURCE}/application_manager_interface.h"
        "${EDEN_R23_FW235_NS_INCLUDE}/core/hle/service/ns/application_manager_interface.h" COPYONLY)
    get_target_property(eden_r23_fw235_ns_units core SOURCES)
    list(FIND eden_r23_fw235_ns_units
         "hle/service/ns/application_manager_interface.cpp" eden_r23_fw235_ns_old)
    if(eden_r23_fw235_ns_old LESS 0)
        message(FATAL_ERROR "R23 #1 original NS application manager owner changed")
    endif()
    list(REMOVE_ITEM eden_r23_fw235_ns_units "hle/service/ns/application_manager_interface.cpp")
    list(APPEND eden_r23_fw235_ns_units
         "${EDEN_R23_FW235_NS_SOURCE}/application_manager_interface.cpp")
    set_property(TARGET core PROPERTY SOURCES "${eden_r23_fw235_ns_units}")
    target_include_directories(core BEFORE PRIVATE "${EDEN_R23_FW235_NS_INCLUDE}")
    message(STATUS "R23 #1: one native qlaunch NS interface + matched 23.5 header")
endif()

