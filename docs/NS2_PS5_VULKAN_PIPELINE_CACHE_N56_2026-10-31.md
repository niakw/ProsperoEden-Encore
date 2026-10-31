# NSW2 N56 — maintained native Vulkan driver cache admission (2026-10-31)

The PS5 renderer already has a qualified atomic driver pipeline cache writer. Eglantine's read-side guard is integrated into that **same maintained source**:
`vendor/encore-active/eden-vulkan/vk_pipeline_cache_cost.cpp`.

The optional macro `EDEN_NS2_PIPELINE_CACHE_GUARD` rejects files shorter than the 12-byte magic/version header **before any read or unsigned subtraction**. It closes and removes invalid cache files and creates a new empty Vulkan cache; the normal Vulkan pipeline writer, valid cache loading, and all default Switch 1 code remain unchanged.

The research CMake option `EDEN_NS2_EGLANTINE_PIPELINE_CACHE_EXPERIMENTAL=ON` defines the guard only with native PS5 Vulkan, NS2 metadata, and a non-final profile. It is OFF by default. The previous generator and temporary copy of the complete Vulkan translation unit are deleted.

Host checks reconstruct the exact pre-N56 Git blob and compare its fixed SHA-1, preserving strict native source parity, while a Clang/GCC UBSan source-extracted fixture verifies all cache lengths 0–24 bytes. No PS5 execution, FPS claim, or full game boot is inferred.
