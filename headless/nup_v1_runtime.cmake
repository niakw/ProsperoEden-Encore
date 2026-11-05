# NUP is part of the unified, production NS1/NS2 content loader.
# Use the single existing vendor loader, VFS and AoC owners for all builds.
# This is ordinary source selection, not a release-policy or roadmap gate.
get_target_property(eden_nup_core_sources core SOURCES)
set(eden_nup_loader_owners)
foreach(eden_nup_owner IN LISTS eden_nup_core_sources)
    if(eden_nup_owner MATCHES "(^|/)loader/loader\\.cpp$")
        list(APPEND eden_nup_loader_owners "${eden_nup_owner}")
    endif()
endforeach()
list(LENGTH eden_nup_loader_owners eden_nup_owner_count)
if(NOT eden_nup_owner_count EQUAL 1)
    message(FATAL_ERROR
        "NUP route requires exactly one pinned loader.cpp owner; re-audit source selection")
endif()
list(GET eden_nup_loader_owners 0 eden_nup_original_loader)
# Compile-only token alias changes the original entrypoint's *symbol*
# to EdenOriginalGetLoader while preserving its unmodified implementation.
# The wrapper in nup_v1_loader_route.cpp is the only public GetLoader.
set_property(SOURCE "${eden_nup_original_loader}" TARGET_DIRECTORY core
    APPEND PROPERTY COMPILE_DEFINITIONS GetLoader=EdenOriginalGetLoader)
target_sources(core PRIVATE
    "${EDEN_PORT_DIR}/nup_v1_vfs.cpp"
    "${EDEN_PORT_DIR}/nup_v1_native_vfs.cpp"
    "${EDEN_PORT_DIR}/nup_v1_native_content.cpp"
    "${EDEN_PORT_DIR}/nup_v1_native_aoc.cpp"
    "${EDEN_PORT_DIR}/nup_v1_native_loader.cpp"
    "${EDEN_PORT_DIR}/nup_v1_loader_route.cpp")
# Share maintained AoC enumeration and RomFS lookup with NUP. Preserve
# their NCA/extracted logic, adding a caller-scoped NUP source owner.
get_target_property(eden_nup_runtime_sources core SOURCES)
foreach(eden_nup_pair IN ITEMS
        "file_sys/romfs_factory.cpp|nup_v1_romfs_factory.cpp"
        "hle/service/aoc/addon_content_manager.cpp|nup_v1_aoc_service.cpp")
    string(REPLACE "|" ";" eden_nup_parts "${eden_nup_pair}")
    list(GET eden_nup_parts 0 eden_nup_previous_suffix)
    list(GET eden_nup_parts 1 eden_nup_new_name)
    set(eden_nup_matches)
    foreach(eden_nup_source IN LISTS eden_nup_runtime_sources)
        if(eden_nup_source MATCHES "(^|/)${eden_nup_previous_suffix}$")
            list(APPEND eden_nup_matches "${eden_nup_source}")
        endif()
    endforeach()
    list(LENGTH eden_nup_matches eden_nup_match_count)
    if(NOT eden_nup_match_count EQUAL 1)
        message(FATAL_ERROR
            "NUP requires exactly one existing AoC/ROMFS source owner: ${eden_nup_previous_suffix}")
    endif()
    list(GET eden_nup_matches 0 eden_nup_old_source)
    list(REMOVE_ITEM eden_nup_runtime_sources "${eden_nup_old_source}")
    list(APPEND eden_nup_runtime_sources
        "${EDEN_PORT_DIR}/${eden_nup_new_name}")
endforeach()
set_property(TARGET core PROPERTY SOURCES "${eden_nup_runtime_sources}")
set(eden_nup_extracted_aoc_headers
    "${PORT_ROOT}/vendor/encore-active/eden-core/src/core/file_sys")
if(NOT EXISTS "${eden_nup_extracted_aoc_headers}/extracted_aoc.h")
    message(FATAL_ERROR "NUP AoC requires maintained existing extracted-aoc interface")
endif()
target_include_directories(core PRIVATE
    "${EDEN_PORT_DIR}" "${eden_nup_extracted_aoc_headers}")
# The single unified build always compiles NUP metadata/game selection.
# This is an internal source-definition shared by the headless frontend and
# metadata unit, never a selectable DEV/release/roadmap build variant.
target_compile_definitions(eden-headless PRIVATE EDEN_NUP_V1_RUNTIME=1)
target_compile_definitions(eden-metadata PRIVATE EDEN_NUP_V1_RUNTIME=1)
if(NOT TARGET libzstd_static OR NOT TARGET ZLIB::ZLIB)
    message(FATAL_ERROR "NUP requires existing pinned zstd and zlib targets")
endif()
target_link_libraries(core PRIVATE libzstd_static ZLIB::ZLIB)
# OpenSSL hashing comes from the pinned core's existing crypto linkage;
# no new library version is downloaded or bundled.
