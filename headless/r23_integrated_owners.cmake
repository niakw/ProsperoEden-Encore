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


# Engine research PR #68
# R23 #119 HOS23: two HLE backport TUs and two new guest IPC
# headers must have the same versioned owner; no extra service target.
if(PS5_NATIVE)
    set(EDEN_R23_STPL_BACKPORT
        "${PORT_ROOT}/vendor/encore-active/eden-backports/src/core/hle/service")
    set(EDEN_R23_STPL_HEADER
        "${PORT_ROOT}/vendor/encore-active/eden-core/include/core/hle/service")
    set(EDEN_R23_STPL_INCLUDE "${PORT_BUILD_DIR}/r23-stpl/include")
    foreach(eden_r23_stpl_name IN ITEMS
            "ngc/ngc.cpp" "filesystem/fsp/fsp_srv.cpp")
        if(NOT EXISTS "${EDEN_R23_STPL_BACKPORT}/${eden_r23_stpl_name}")
            message(FATAL_ERROR "R23 #119 missing maintained HOS23 service ${eden_r23_stpl_name}")
        endif()
    endforeach()
    foreach(eden_r23_stpl_header IN ITEMS
            "acc/profile_manager.h" "ipc_helpers.h")
        if(NOT EXISTS "${EDEN_R23_STPL_HEADER}/${eden_r23_stpl_header}")
            message(FATAL_ERROR "R23 #119 missing service header ${eden_r23_stpl_header}")
        endif()
        configure_file("${EDEN_R23_STPL_HEADER}/${eden_r23_stpl_header}"
            "${EDEN_R23_STPL_INCLUDE}/core/hle/service/${eden_r23_stpl_header}" COPYONLY)
    endforeach()
    get_target_property(eden_r23_stpl_units core SOURCES)
    foreach(eden_r23_stpl_source IN ITEMS
            "ngc/ngc.cpp" "filesystem/fsp/fsp_srv.cpp")
        list(FIND eden_r23_stpl_units
             "hle/service/${eden_r23_stpl_source}" eden_r23_stpl_old)
        if(eden_r23_stpl_old LESS 0)
            message(FATAL_ERROR "R23 #119 original stpl source owner drift")
        endif()
        list(REMOVE_ITEM eden_r23_stpl_units
             "hle/service/${eden_r23_stpl_source}")
        list(APPEND eden_r23_stpl_units
             "${EDEN_R23_STPL_BACKPORT}/${eden_r23_stpl_source}")
    endforeach()
    set_property(TARGET core PROPERTY SOURCES "${eden_r23_stpl_units}")
    target_include_directories(core BEFORE PUBLIC "${EDEN_R23_STPL_INCLUDE}")
    message(STATUS "R23 #119: two supported HOS23 service TUs and coherent IPC headers")
endif()


# Engine research PR #72
# R23 #49: the Vulkan buffer cache's descriptor-buffer and legacy
# paths are inline in its public header. The correct vendor header must
# precede the pinned original for all three consumers, without another TU.
if(PS5_NATIVE)
    set(EDEN_R23_TEXEL_HEADER
        "${PORT_ROOT}/vendor/encore-active/eden-vulkan/include/video_core/renderer_vulkan/vk_buffer_cache.h")
    set(EDEN_R23_TEXEL_INCLUDE "${PORT_BUILD_DIR}/r23-texel/include")
    if(NOT EXISTS "${EDEN_R23_TEXEL_HEADER}")
        message(FATAL_ERROR "R23 #49 maintained Vulkan texel buffer header missing")
    endif()
    configure_file("${EDEN_R23_TEXEL_HEADER}"
        "${EDEN_R23_TEXEL_INCLUDE}/video_core/renderer_vulkan/vk_buffer_cache.h" COPYONLY)
    foreach(eden_r23_texel_target IN ITEMS video_core core)
        target_include_directories(${eden_r23_texel_target} BEFORE PRIVATE
            "${EDEN_R23_TEXEL_INCLUDE}")
    endforeach()
    message(STATUS "R23 #49: one reviewed Vulkan texel buffer header for native consumers")
endif()


# Engine research PR #73
# R23 #114: WallClock nanoseconds-to-host ticks must use the matching
# maintained header: the old Q0.64 factor overflows at >1 GHz. Compile
# exactly one replacement common/cpu_features.cpp and stage its header.
if(PS5_NATIVE)
    set(EDEN_R23_CLOCK
        "${PORT_ROOT}/vendor/encore-active/eden-core/src/common/cpu_features.cpp")
    set(EDEN_R23_CLOCK_HEADER
        "${PORT_ROOT}/vendor/encore-active/eden-core/include/common/cpu_features.h")
    set(EDEN_R23_CLOCK_INCLUDE "${PORT_BUILD_DIR}/r23-clock/include")
    if(NOT EXISTS "${EDEN_R23_CLOCK}" OR NOT EXISTS "${EDEN_R23_CLOCK_HEADER}")
        message(FATAL_ERROR "R23 #114 maintained WallClock pair unavailable")
    endif()
    configure_file("${EDEN_R23_CLOCK_HEADER}"
        "${EDEN_R23_CLOCK_INCLUDE}/common/cpu_features.h" COPYONLY)
    get_target_property(eden_r23_clock_tus common SOURCES)
    list(FIND eden_r23_clock_tus "cpu_features.cpp" eden_r23_clock_original)
    if(eden_r23_clock_original LESS 0)
        message(FATAL_ERROR "R23 #114 pinned common/cpu_features.cpp owner drift")
    endif()
    list(REMOVE_ITEM eden_r23_clock_tus "cpu_features.cpp")
    list(APPEND eden_r23_clock_tus "${EDEN_R23_CLOCK}")
    set_property(TARGET common PROPERTY SOURCES "${eden_r23_clock_tus}")
    target_include_directories(common BEFORE PUBLIC "${EDEN_R23_CLOCK_INCLUDE}")
    message(STATUS "R23 #114: source/headers match 2–4 GHz WallClock conversion")
endif()


# Engine research PR #74
# R23 #33 — ConstantPool C++ and header must agree on mapped slot type.
# Keep the code cache W^X writableAddress semantics from maintained PS5.
if(PS5_NATIVE)
    set(EDEN_R23_POOL_ROOT
        "${PORT_ROOT}/vendor/encore-active/eden-core")
    set(EDEN_R23_POOL_UNIT
        "${EDEN_R23_POOL_ROOT}/src/dynarmic/backend/x64/constant_pool.cpp")
    set(EDEN_R23_POOL_HEADER
        "${EDEN_R23_POOL_ROOT}/include/dynarmic/backend/x64/constant_pool.h")
    if(NOT EXISTS "${EDEN_R23_POOL_UNIT}" OR NOT EXISTS "${EDEN_R23_POOL_HEADER}")
        message(FATAL_ERROR "Missing coherent R23 #33 native W^X constant pool pair")
    endif()
    configure_file("${EDEN_R23_POOL_HEADER}"
        "${PORT_BUILD_DIR}/include/dynarmic/backend/x64/constant_pool.h" COPYONLY)
    get_target_property(eden_r23_pool_units dynarmic SOURCES)
    list(FIND eden_r23_pool_units
         "backend/x64/constant_pool.cpp" eden_r23_pool_old)
    if(eden_r23_pool_old LESS 0)
        message(FATAL_ERROR "R23 #33 original native ConstantPool TU changed")
    endif()
    list(REMOVE_ITEM eden_r23_pool_units "backend/x64/constant_pool.cpp")
    list(APPEND eden_r23_pool_units "${EDEN_R23_POOL_UNIT}")
    set_property(TARGET dynarmic PROPERTY SOURCES "${eden_r23_pool_units}")
    target_include_directories(dynarmic BEFORE PUBLIC "${PORT_BUILD_DIR}/include")
    message(STATUS "R23 #33: one maintained indexed W^X ConstantPool C++ and header")
endif()


# Engine research PR #75
# R23 #95 - the native maintained EmulatedController C++ source above
# removes the stale 48-state controller_connected member. Its original header
# must be replaced in exactly the same native source build graph.
if(PS5_NATIVE)
    set(EDEN_R23_HID_HEADER
        "${PORT_ROOT}/vendor/encore-active/eden-core/include/hid_core/frontend/emulated_controller.h")
    if(NOT EXISTS "${EDEN_R23_HID_HEADER}")
        message(FATAL_ERROR "R23 #95 missing matched HID controller header")
    endif()
    set(EDEN_R23_HID_ROOT "${PORT_BUILD_DIR}/r23-hid/include")
    configure_file("${EDEN_R23_HID_HEADER}"
        "${EDEN_R23_HID_ROOT}/hid_core/frontend/emulated_controller.h" COPYONLY)
    target_include_directories(hid_core BEFORE PUBLIC "${EDEN_R23_HID_ROOT}")
    message(STATUS "R23 #95: selected controller implementation/header in one HID native graph")
endif()


# Engine research PR #77

# R23 #54: a per-instance paced IStorage + matching service dispatcher
# replaces the old 600us generic IPC sleep; never replace the native
# process-refcounted NVDEC registry with an upstream global bool.
if(PS5_NATIVE)
    set(EDEN_R23_STORAGE_ROOT
        "${PORT_ROOT}/vendor/encore-active/eden-core")
    set(EDEN_R23_STORAGE_HEADERS "${PORT_BUILD_DIR}/r23-storage/include")
    foreach(eden_r23_storage_header IN ITEMS
            "core/hle/service/service.h"
            "core/hle/service/filesystem/fsp/fs_i_storage.h")
        if(NOT EXISTS "${EDEN_R23_STORAGE_ROOT}/include/${eden_r23_storage_header}")
            message(FATAL_ERROR "R23 #54 missing matched native storage header")
        endif()
        configure_file("${EDEN_R23_STORAGE_ROOT}/include/${eden_r23_storage_header}"
            "${EDEN_R23_STORAGE_HEADERS}/${eden_r23_storage_header}" COPYONLY)
    endforeach()
    get_target_property(eden_r23_storage_units core SOURCES)
    foreach(eden_r23_storage_source IN ITEMS
            "hle/service/service.cpp"
            "hle/service/filesystem/fsp/fs_i_storage.cpp")
        list(FIND eden_r23_storage_units
            "${eden_r23_storage_source}" eden_r23_storage_old)
        if(eden_r23_storage_old EQUAL -1)
            message(FATAL_ERROR "R23 #54 native core source owner changed: ${eden_r23_storage_source}")
        endif()
        if(NOT EXISTS "${EDEN_R23_STORAGE_ROOT}/src/core/${eden_r23_storage_source}")
            message(FATAL_ERROR "R23 #54 missing reviewed storage source: ${eden_r23_storage_source}")
        endif()
        list(REMOVE_ITEM eden_r23_storage_units "${eden_r23_storage_source}")
        list(APPEND eden_r23_storage_units
            "${EDEN_R23_STORAGE_ROOT}/src/core/${eden_r23_storage_source}")
    endforeach()
    set_property(TARGET core PROPERTY SOURCES "${eden_r23_storage_units}")
    target_include_directories(core BEFORE PUBLIC "${EDEN_R23_STORAGE_HEADERS}")
    message(STATUS "R23 #54: one paced storage source and one normal service dispatcher")
endif()

# Engine research PR #78

# R23 #97: match applet overlay compositor to the selected native SGSR bypass.
if(PS5_NATIVE)
    set(EDEN_R23_APPLET_WINDOW_SOURCE
        "${PORT_ROOT}/vendor/encore-active/eden-core/src/core/hle/service/am/window_system.cpp")
    if(NOT EXISTS "${EDEN_R23_APPLET_WINDOW_SOURCE}")
        message(FATAL_ERROR "R23 #97 matched applet WindowSystem source missing")
    endif()
    get_target_property(eden_r23_applet_window_units core SOURCES)
    list(FIND eden_r23_applet_window_units
         "hle/service/am/window_system.cpp" eden_r23_applet_old)
    if(eden_r23_applet_old EQUAL -1)
        message(FATAL_ERROR "R23 #97 selected native applet window owner changed")
    endif()
    list(REMOVE_ITEM eden_r23_applet_window_units
         "hle/service/am/window_system.cpp")
    list(APPEND eden_r23_applet_window_units "${EDEN_R23_APPLET_WINDOW_SOURCE}")
    set_property(TARGET core PROPERTY SOURCES "${eden_r23_applet_window_units}")
    message(STATUS "R23 #97: one applet z-order TU and selected SGSR bypass")
endif()

# Engine research PR #79

# NS1 #19 guest HID ABI: matched atomic orientation and reload mutex must be
# compiled for ALL consumers of HIDCore, not just NPad. The currently
# selected maintained rumble and NPad TUs are preserved intact.
if(PS5_NATIVE)
    set(EDEN_R23_HIDCORE_ROOT
        "${PORT_ROOT}/vendor/encore-active/eden-core")
    set(EDEN_R23_HIDCORE_CPP
        "${EDEN_R23_HIDCORE_ROOT}/src/hid_core/hid_core.cpp")
    set(EDEN_R23_HIDCORE_HEADER
        "${EDEN_R23_HIDCORE_ROOT}/include/hid_core/hid_core.h")
    if(NOT EXISTS "${EDEN_R23_HIDCORE_CPP}" OR NOT EXISTS "${EDEN_R23_HIDCORE_HEADER}")
        message(FATAL_ERROR "R23 #19 native HIDCore ABI pair is missing")
    endif()
    set(EDEN_R23_HIDCORE_INCLUDE "${PORT_BUILD_DIR}/r23-hidcore/include")
    configure_file("${EDEN_R23_HIDCORE_HEADER}"
        "${EDEN_R23_HIDCORE_INCLUDE}/hid_core/hid_core.h" COPYONLY)
    get_target_property(eden_r23_hidcore_units hid_core SOURCES)
    list(FIND eden_r23_hidcore_units "hid_core.cpp" eden_r23_hidcore_old)
    if(eden_r23_hidcore_old EQUAL -1)
        message(FATAL_ERROR "R23 #19 native HIDCore original source owner changed")
    endif()
    list(REMOVE_ITEM eden_r23_hidcore_units "hid_core.cpp")
    list(APPEND eden_r23_hidcore_units "${EDEN_R23_HIDCORE_CPP}")
    set_property(TARGET hid_core PROPERTY SOURCES "${eden_r23_hidcore_units}")
    foreach(eden_r23_hid_consumer IN ITEMS hid_core core video_core input_common eden-headless)
        if(TARGET ${eden_r23_hid_consumer})
            target_include_directories(${eden_r23_hid_consumer}
                BEFORE PRIVATE "${EDEN_R23_HIDCORE_INCLUDE}")
        endif()
    endforeach()
    message(STATUS "R23 #19: one native HIDCore ABI and retained maintained NPad owner")
endif()

# Engine research PR #81
# NS1 R23 #64: visible HWC composition must preserve waited buffer
# retirement. Select exactly one full maintained native HWC source owner.
if(PS5_NATIVE)
    set(EDEN_R23_HWC_SOURCE
        "${PORT_ROOT}/vendor/encore-active/eden-core/src/core/hle/service/nvnflinger/hardware_composer.cpp")
    if(NOT EXISTS "${EDEN_R23_HWC_SOURCE}")
        message(FATAL_ERROR "R23 #64 native HWC visibility source missing")
    endif()
    get_target_property(eden_r23_hwc_units core SOURCES)
    list(FIND eden_r23_hwc_units
         "hle/service/nvnflinger/hardware_composer.cpp" eden_r23_hwc_old)
    if(eden_r23_hwc_old LESS 0)
        message(FATAL_ERROR "R23 #64 expected HWC source owner was replaced")
    endif()
    list(REMOVE_ITEM eden_r23_hwc_units "hle/service/nvnflinger/hardware_composer.cpp")
    list(APPEND eden_r23_hwc_units "${EDEN_R23_HWC_SOURCE}")
    set_property(TARGET core PROPERTY SOURCES "${eden_r23_hwc_units}")
endif()


# Engine research PR #82
# R23 #126: shared RFC4122 UUIDv5 16-byte signature must compile in
# both common and the ACTUAL PS5-selected ns2-runtime/AM service source.
# The earlier Eden-core AM unit is shadowed by EDEN_SHARED_NS2_AM; do not
# report a changed but unselected source as a console fix.
if(PS5_NATIVE)
    set(EDEN_R23_UUID_ROOT
        "${PORT_ROOT}/vendor/encore-active/eden-core")
    set(EDEN_R23_UUID_INCLUDE "${PORT_BUILD_DIR}/r23-uuid16/include")
    foreach(p IN ITEMS
            "${EDEN_R23_UUID_ROOT}/src/common/uuid.cpp"
            "${EDEN_R23_UUID_ROOT}/include/common/uuid.h"
            "${PORT_ROOT}/vendor/encore-active/ns2-runtime/am/core/hle/service/am/service/application_functions.cpp")
        if(NOT EXISTS "${p}")
            message(FATAL_ERROR "R23 #126 native UUID16 source/selected AM owner missing: ${p}")
        endif()
    endforeach()
    configure_file("${EDEN_R23_UUID_ROOT}/include/common/uuid.h"
        "${EDEN_R23_UUID_INCLUDE}/common/uuid.h" COPYONLY)
    get_target_property(eden_r23_uuid_sources common SOURCES)
    list(FIND eden_r23_uuid_sources "uuid.cpp" eden_r23_uuid_orig)
    if(eden_r23_uuid_orig LESS 0)
        message(FATAL_ERROR "R23 #126 original UUID.cpp source owner changed")
    endif()
    list(REMOVE_ITEM eden_r23_uuid_sources "uuid.cpp")
    list(APPEND eden_r23_uuid_sources "${EDEN_R23_UUID_ROOT}/src/common/uuid.cpp")
    set_property(TARGET common PROPERTY SOURCES "${eden_r23_uuid_sources}")
    target_include_directories(common BEFORE PUBLIC "${EDEN_R23_UUID_INCLUDE}")
    target_include_directories(core BEFORE PUBLIC "${EDEN_R23_UUID_INCLUDE}")
    message(STATUS "R23 #126 UUID 16-byte ABI and PS5-selected AM source staged")
endif()


# Engine research PR #84
# R23 #35: one native shader texture-pass TU with matched host texture
# metadata, while the maintained Vulkan source fork is materialized by
# headless/vulkan.cmake from this same branch's vendor commit.
if(PS5_NATIVE)
    set(EDEN_R23_ATTRIBUTE_SOURCE
        "${PORT_ROOT}/vendor/encore-active/eden-shader/src/shader_recompiler")
    set(EDEN_R23_ATTRIBUTE_HEADERS
        "${PORT_BUILD_DIR}/r23-attribute-handle/include")
    foreach(eden_r23_attr_header IN ITEMS
            "host_translate_info.h" "shader_info.h")
        if(NOT EXISTS "${EDEN_R23_ATTRIBUTE_SOURCE}/${eden_r23_attr_header}")
            message(FATAL_ERROR "R23 #35 maintained shader header missing: ${eden_r23_attr_header}")
        endif()
        configure_file("${EDEN_R23_ATTRIBUTE_SOURCE}/${eden_r23_attr_header}"
            "${EDEN_R23_ATTRIBUTE_HEADERS}/shader_recompiler/${eden_r23_attr_header}" COPYONLY)
    endforeach()
    set(EDEN_R23_ATTRIBUTE_TEXTURE_PASS
        "${EDEN_R23_ATTRIBUTE_SOURCE}/ir_opt/texture_pass.cpp")
    if(NOT EXISTS "${EDEN_R23_ATTRIBUTE_TEXTURE_PASS}")
        message(FATAL_ERROR "R23 #35 maintained shader texture pass missing")
    endif()
    get_target_property(eden_r23_attr_units shader_recompiler SOURCES)
    list(FIND eden_r23_attr_units "ir_opt/texture_pass.cpp" eden_r23_attr_original)
    if(eden_r23_attr_original LESS 0)
        message(FATAL_ERROR "R23 #35 source owner changed; refuse duplicate texture pass")
    endif()
    list(REMOVE_ITEM eden_r23_attr_units "ir_opt/texture_pass.cpp")
    list(APPEND eden_r23_attr_units "${EDEN_R23_ATTRIBUTE_TEXTURE_PASS}")
    set_property(TARGET shader_recompiler PROPERTY SOURCES "${eden_r23_attr_units}")
    target_include_directories(shader_recompiler BEFORE PUBLIC "${EDEN_R23_ATTRIBUTE_HEADERS}")
    target_include_directories(video_core BEFORE PRIVATE "${EDEN_R23_ATTRIBUTE_HEADERS}")
    foreach(eden_r23_vulkan_file IN ITEMS
            "vk_graphics_pipeline_cost.cpp" "vk_pipeline_cache_cost.cpp"
            "vulkan_rasterizer.cpp"
            "include/video_core/renderer_vulkan/vk_graphics_pipeline.h"
            "include/video_core/renderer_vulkan/vk_rasterizer.h")
        if(NOT EXISTS
           "${PORT_ROOT}/vendor/encore-active/eden-vulkan/${eden_r23_vulkan_file}")
            message(FATAL_ERROR "R23 #35 missing maintained Vulkan owner: ${eden_r23_vulkan_file}")
        endif()
    endforeach()
    message(STATUS "R23 #35: selected one bindless attribute texture-pass TU and five Vulkan owners")
endif()


# Engine research PR #85
# R23 #80 — vendor workaround IR and VkPipelineCache need the SAME
# HasBrokenPattern ABI. Compile the maintained shader TU exactly once and
# stage the public IR declaration before video_core/shader_recompiler.
if(PS5_NATIVE)
    set(EDEN_R23_FRAG_IR
        "${PORT_ROOT}/vendor/encore-active/eden-shader/src/shader_recompiler/ir_opt")
    set(EDEN_R23_FRAG_VK
        "${PORT_ROOT}/vendor/encore-active/eden-vulkan/vk_pipeline_cache_cost.cpp")
    if(NOT EXISTS "${EDEN_R23_FRAG_IR}/passes.h"
       OR NOT EXISTS "${EDEN_R23_FRAG_IR}/vendor_workaround_pass.cpp"
       OR NOT EXISTS "${EDEN_R23_FRAG_VK}")
        message(FATAL_ERROR "R23 #80 missing matched IR predicate and Vulkan caller")
    endif()
    set(EDEN_R23_FRAG_HEADERS "${PORT_BUILD_DIR}/r23-fragpattern/include")
    configure_file("${EDEN_R23_FRAG_IR}/passes.h"
        "${EDEN_R23_FRAG_HEADERS}/shader_recompiler/ir_opt/passes.h" COPYONLY)
    get_target_property(eden_r23_frag_units shader_recompiler SOURCES)
    list(FIND eden_r23_frag_units "ir_opt/vendor_workaround_pass.cpp" eden_r23_frag_old)
    if(eden_r23_frag_old LESS 0)
        message(FATAL_ERROR "R23 #80 original shader workaround owner changed")
    endif()
    list(REMOVE_ITEM eden_r23_frag_units "ir_opt/vendor_workaround_pass.cpp")
    list(APPEND eden_r23_frag_units "${EDEN_R23_FRAG_IR}/vendor_workaround_pass.cpp")
    set_property(TARGET shader_recompiler PROPERTY SOURCES "${eden_r23_frag_units}")
    target_include_directories(shader_recompiler BEFORE PUBLIC "${EDEN_R23_FRAG_HEADERS}")
    target_include_directories(video_core BEFORE PRIVATE "${EDEN_R23_FRAG_HEADERS}")
    message(STATUS "R23 #80: one shader IR predicate and matched native Vulkan caller")
endif()


# Engine PRs #70/#76 — preserve shared ConditionalPhi resolver header.
# The sole texture_pass.cpp TU replacement is owned by PR #84 above;
# vendor now contains both Phi and attribute-handle source transformations.
if(PS5_NATIVE)
    set(EDEN_R23_PHI_HEADER
        "${PORT_ROOT}/vendor/encore-active/eden-shader/include/shader_recompiler/frontend/ir/breadth_first_search.h")
    if(NOT EXISTS "${EDEN_R23_PHI_HEADER}")
        message(FATAL_ERROR "Missing shared R23 Phi BreadthFirstSearch header")
    endif()
    configure_file("${EDEN_R23_PHI_HEADER}"
        "${PORT_BUILD_DIR}/r23-phi/include/shader_recompiler/frontend/ir/breadth_first_search.h"
        COPYONLY)
    target_include_directories(shader_recompiler BEFORE PUBLIC "${PORT_BUILD_DIR}/r23-phi/include")
endif()
