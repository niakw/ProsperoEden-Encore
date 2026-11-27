#!/usr/bin/env python3
"""Verify the native Vulkan build consumes maintained Encore owners directly.

This is intentionally a current-architecture check, not a historical patch
replay. Upstream Eden remains under vendor/sources/eden; maintained Vulkan
owners live under vendor/encore-active until their canonical Eden-path migration
is complete. No vendor commit/tree/blob allowlist decides source admission.
"""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "vendor"
ACTIVE = VENDOR / "encore-active/eden-vulkan"
UPSTREAM = VENDOR / "sources/eden"

subprocess.check_call(["python3", "-B", "tools/check-source-tree-layout.py"], cwd=VENDOR)
assert UPSTREAM.is_dir() and (UPSTREAM / "VENDOR-ORIGIN.json").is_file()
assert ACTIVE.is_dir()

vulkan_cmake = (ROOT / "headless/vulkan.cmake").read_text()
root_cmake = (ROOT / "headless/CMakeLists.txt").read_text()
native_build = (ROOT / "tools/build-headless-native.sh").read_text()

for token in (
    'set(EDEN_ACTIVE_VULKAN "${PORT_ROOT}/vendor/encore-active/eden-vulkan")',
    'file(COPY "${EDEN_ACTIVE_VULKAN}/" DESTINATION "${PORT_BUILD_DIR}")',
    'file(SHA256 "${EDEN_ACTIVE_VULKAN}/${unit}.cpp" source_sha)',
    'file(SHA256 "${PORT_BUILD_DIR}/${unit}.cpp" selected_sha)',
):
    assert token in vulkan_cmake, ("native Vulkan owner selection drift", token)

# Historical source generators/replayers are not build inputs.
for name, text_body in (
    ("native build", native_build),
    ("Vulkan selector", vulkan_cmake),
    ("CMake root", root_cmake),
):
    assert "prepare-vulkan-port.py" not in text_body, name
    assert "install-vendored-eden-backports.py" not in text_body, name

required = (
    "vulkan_rasterizer.cpp",
    "vk_graphics_pipeline_cost.cpp",
    "vk_compute_pipeline_cost.cpp",
    "vk_pipeline_cache_cost.cpp",
    "vk_texture_cache_cost.cpp",
    "vk_compute_pass_cost.cpp",
    "vulkan_swapchain.cpp",
    "vulkan_renderer.cpp",
)
for relative in required:
    owner = ACTIVE / relative
    assert owner.is_file(), relative
    subprocess.check_call(
        ["git", "ls-files", "--error-unmatch", str(owner.relative_to(VENDOR))],
        cwd=VENDOR, stdout=subprocess.DEVNULL,
    )

print(
    "VENDORED_VULKAN_ACTIVE_OWNER_PASS",
    f"owners={len(required)}",
    "historical_replay=0",
    "revision_allowlists=0",
    "selected_bytes_checked_by_cmake=1",
)
