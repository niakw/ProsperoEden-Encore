#!/usr/bin/env python3
"""P2.2b: replay the real post-staging QMD image physical remap check on host.

No synthetic pass claims a physical PS5 image or GPU command execution.
"""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
VENDOR = ROOT / "vendor/encore-active"
RENDERERS = (
    VENDOR / "eden-vulkan/vulkan_rasterizer.cpp",
    VENDOR / "eden-core/guest-bridge/vulkan_rasterizer.cpp",
)
START = "            if (current_after_staging && pinned_lifetime) {\n"
END = "            }\n        }\n        // Texel buffer VkBufferViews"
extracted = []
for file in RENDERERS:
    text = file.read_text()
    assert text.count(START) == text.count(END) == 1, file
    body = text.split(START, 1)[1].split(END, 1)[0]
    extracted.append(START + body + "            }\n")
    assert "image.guest_gpu_address, image.guest_bytes," in extracted[-1]
    assert "*cpu != image.guest_cpu_address" in extracted[-1]
assert extracted[0] == extracted[1], "native and deferred Vulkan remap checks drift"

for file in (
    VENDOR / "eden-vulkan/vulkan-cache/video_core/texture_cache/texture_cache.h",
    VENDOR / "ns2-astc/include/video_core/texture_cache/texture_cache.h",
):
    text = file.read_text()
    body = text.split("TextureCache<P>::PinNativeImageView(ImageViewId id)", 1)[1].split(
        "TextureCache<P>::PinNativeSampler(", 1
    )[0]
    assert "gpu_memory->GpuToCpuAddress(image.gpu_addr)" in body, file
    assert "*mapped_base != image.cpu_addr" in body, file
    assert "image.flags |= ImageFlagBits::Remapped;" in body, file
    # The "requires" capability probe mentions PinNativeGpu() before the
    # physical mapping guard; only the actual pin acquisition matters.
    # Never accept a GPU owner acquired ahead of the remap refusal.
    assert body.count("auto image_pin = image.PinNativeGpu();") == 1, file
    assert body.index("*mapped_base != image.cpu_addr") < body.index(
        "auto image_pin = image.PinNativeGpu();"), file

header = (VENDOR / "eden-vulkan/include/video_core/renderer_vulkan/vk_compute_pipeline.h").read_text()
pipeline = (VENDOR / "eden-vulkan/vk_compute_pipeline_cost.cpp").read_text()
for field in ("guest_gpu_address", "guest_cpu_address", "guest_bytes"):
    assert field in header
    assert "image." + field in extracted[0] or field == "guest_bytes"
assert "!image.guest_gpu_address || !image.guest_bytes" in pipeline
for file in RENDERERS:
    code = file.read_text()
    assert code.index("native.guest_cpu_address = *guest_cpu_base;") < code.index(
        "if (!pipeline->ConfigureNative("
    ) < code.index(START)

fixture = r'''
#include <algorithm>
#include <cassert>
#include <cstdint>
#include <memory>
#include <optional>
#include <vector>
#include "shader_recompiler/frontend/ampere/native_qmd_compute_environment.h"
struct FakeImage {
    u64 guest_gpu_address{}, guest_cpu_address{};
    u32 guest_bytes{};
};
struct FakeLifetime { std::vector<FakeImage> images; };
struct FakeGpu {
    bool moved{}, hole{}, split{};
    std::optional<u64> GpuToCpuAddress(u64 va) const {
        if (va < 0x10000 || va >= 0x50000) return {};
        if (hole && va >= 0x11000 && va < 0x12000) return {};
        return 0x800000 + (va - 0x10000) +
            (moved ? 0x100000 : 0) +
            (split && va >= 0x11000 ? 0x1000 : 0);
    }
};
struct MockRasterizer {
    std::unique_ptr<FakeGpu> gpu_memory = std::make_unique<FakeGpu>();
    std::shared_ptr<FakeLifetime> pinned_lifetime =
        std::make_shared<FakeLifetime>();
    bool Check() {
        bool current_after_staging = true;
__BLOCK__
        return current_after_staging;
    }
};
int main() {
    MockRasterizer renderer;
    renderer.pinned_lifetime->images.push_back({0x10000, 0x800000, 0x3000});
    assert(renderer.Check());
    renderer.gpu_memory->moved = true;
    assert(!renderer.Check()); // all raw TIC/TSC bytes may still match
    renderer.gpu_memory->moved = false;
    renderer.gpu_memory->split = true;
    assert(!renderer.Check()); // start/end alone are insufficient
    renderer.gpu_memory->split = false;
    renderer.gpu_memory->hole = true;
    assert(!renderer.Check()); // an intermediate page is missing
    renderer.gpu_memory->hole = false;
    renderer.pinned_lifetime->images.push_back({0x20000, 0x820000, 0x1000});
    assert(!renderer.Check()); // every independent image backing matters
    renderer.pinned_lifetime->images.back().guest_cpu_address = 0x810000;
    assert(renderer.Check());
    renderer.pinned_lifetime->images.back().guest_bytes = 0;
    assert(!renderer.Check());
    renderer.pinned_lifetime.reset();
    assert(renderer.Check()); // buffer-only QMD has no texture lease
}
'''.replace("__BLOCK__", extracted[0])
env = dict(os.environ)
sdk = Path("/Library/Developer/CommandLineTools/SDKs/MacOSX15.4.sdk")
if sdk.is_dir():
    env["SDKROOT"] = str(sdk)
includes = (
    ROOT / "vendor/sources/fmt/include",
    ROOT / "vendor/encore-active/ns2-runtime/ampere",
    ROOT / "vendor/encore-active/ns2-runtime/gpu_dispatch",
    ROOT / "vendor/sources/eden/src",
)
boost_caches = sorted((Path.home() / ".cache").glob(
    "ps5-eden-*/source/.cache/cpm/boost/boost-*/libs"
))
if boost_caches:
    includes += tuple(sorted(
        path for path in boost_caches[-1].rglob("include") if (path / "boost").is_dir()
    ))
compilers = list(dict.fromkeys(filter(None, (shutil.which("clang++"), shutil.which("g++")))))
assert compilers
with tempfile.TemporaryDirectory(prefix="encore-native-image-remap-") as temp:
    unit = Path(temp) / "image-remap.cpp"
    unit.write_text(fixture)
    for compiler in compilers:
        for optimization in (0, 2):
            exe = Path(temp) / (Path(compiler).name + str(optimization))
            command = [
                compiler, "-std=c++20", f"-O{optimization}", "-Wall", "-Wextra",
                "-Werror", "-Wno-unused-parameter", "-DFMT_HEADER_ONLY",
                "-fsanitize=undefined", "-fno-sanitize-recover=all",
            ]
            command += [f"-I{inc}" for inc in includes]
            command += [str(unit), "-o", str(exe)]
            build = subprocess.run(command, text=True, capture_output=True, env=env, timeout=70)
            assert build.returncode == 0, (compiler, build.stderr[-4000:])
            check = subprocess.run([str(exe)], text=True, capture_output=True, env=env, timeout=15)
            assert check.returncode == 0, (compiler, check.stderr[-4000:])
            print("P2_2B_NATIVE_IMAGE_PHYSICAL_REMAP_PASS", Path(compiler).name,
                  f"O{optimization}", "full_pages=checked", "owners=2",
                  "Vulkan_commands=not_executed", flush=True)
