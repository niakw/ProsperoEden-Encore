#!/usr/bin/env python3
"""NS1 Vulkan teardown, NS2 sparse boot and library fixes from the 13 Nov crash bundle.

This is an exact-source / source-extracted host gate, NOT a PS5 gameplay test.
"""
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
read = lambda path: (root / path).read_text(encoding="utf-8")
raster = read("vendor/encore-active/eden-vulkan/vulkan_rasterizer.cpp")
scheduler_h = read("vendor/encore-active/eden-vulkan/include/video_core/renderer_vulkan/vk_scheduler.h")
scheduler = read("vendor/encore-active/eden-vulkan/vulkan_scheduler.cpp")
buffer_cache = read("vendor/encore-active/eden-vulkan/vk_buffer_cache_cost.cpp")
shared = read("vendor/encore-active/ns2-runtime/sparse-residency/core/hle/kernel/k_shared_memory.cpp")
cmake = read("headless/CMakeLists.txt")
lib = read("headless/prosperoeden/pe/ui/library.cpp")
case = read("headless/prosperoeden/pe/ui/case_media_selection.hpp")
services = read("headless/prosperoeden/eden_services.cpp")
textures = read("headless/prosperoeden/pe/ui/textures.cpp")
theme = read("headless/prosperoeden/pe/ui/theme.hpp")

# FC27: QueryCache is destroyed before BufferCache. The latter's destructor
# still submits work, so the scheduler cannot retain its stale QueryCache*.
destructor = raster.split("RasterizerVulkan::~RasterizerVulkan() {", 1)[1].split("\n}", 1)[0]
assert destructor.index("scheduler.WaitWorker();") < destructor.index("scheduler.Finish();")
assert destructor.index("scheduler.Finish();") < destructor.index("scheduler.ClearQueryCache();")
assert "void ClearQueryCache() noexcept" in scheduler_h
assert "query_cache = nullptr;" in scheduler_h.split("void ClearQueryCache() noexcept", 1)[1].split("}", 1)[0]
assert "if (query_cache)" in scheduler.split("void Scheduler::EndPendingOperations()", 1)[1].split("void Scheduler::EndRenderPass()", 1)[0]
assert "scheduler.Finish();" in buffer_cache.split("void BufferCacheRuntime::Finish()", 1)[1].split("}", 1)[0]

# NS2: a reserved 12 GiB guest VA is NOT committed DRAM. The first KSharedMemory
# direct memset must be preceded by a bounded physical-commit admission.
assert "EDEN_NS2_SPARSE_BACKING" in shared
init = shared.split("Result KSharedMemory::Initialize(", 1)[1].split("void KSharedMemory::Finalize(", 1)[0]
assert init.index("EdenNs2CommitGuestBacking(") < init.index("std::memset(")
assert init.index("throw std::bad_alloc{};") < init.index("std::memset(")
assert "physical - Core::DramMemoryMap::Base, block.GetSize()" in init
assert "list(REMOVE_ITEM eden_sparse_core_sources \"hle/kernel/k_shared_memory.cpp\")" in cmake
assert "set_property(TARGET core PROPERTY SOURCES \"${eden_sparse_core_sources}\")" in cmake

# UI: original flat scan must be shown completely; screenshots 4/5 can fill
# missing panels rather than being silently discarded.
sleeve = lib.split("void flat_retail_sleeve(", 1)[1].split("// ONE physical shell:", 1)[0]
assert "fitted.w = paper.h * source;" in sleeve and "fitted.h = paper.w / source;" in sleeve
front = sleeve.split("if (!rear) {", 1)[1].split("} else {", 1)[0]
assert "uv.w =" not in front and "uv.h =" not in front
assert "if (role < '1' || role > '5'" in case
assert "for (auto& slot : fallback)" in case
assert "std::string library_genres(" in lib
assert 'genres.find(" · ", from)' in lib
assert 'std::min(comma, dot)' in lib
assert 'if (attempts >= 7' in services
assert "stbi_failure_reason()" in services
assert "EDEN_EXEFS_SIZE" in services
assert "Eden::Ns2Catalog::Description(" in services
assert "if (it->second.texture == 0) {" in textures
assert "target_pixels >= 1024" in textures
# Library source must provide controller focus over each real screenshot.
# The preview displays the original fitted aspect, not the cropped thumbnail,
# and Cross must never launch while the full-screen viewer owns input.
ui_state = read("headless/prosperoeden/pe/ui/launcher.hpp")
assert "int library_shot_focused_ = -1" in ui_state
assert "int library_shot_viewer_ = -1" in ui_state
assert "if (library_back_zoom_)" in lib
assert "const auto clamp_pan = [&]" in lib
assert "library_shot_focused_ = found" in lib
assert "library_shot_viewer_ = library_shot_focused_" in lib
assert "library_shot_focused_ == i" in lib
assert "if (library_shot_viewer_ >= 0 &&" in lib
assert "const float width = std::min(viewer.w, viewer.h * aspect)" in lib
assert "list.image(shot.texture, fitted, {0.0f, 0.0f, 1.0f, 1.0f}, kWhite)" in lib
assert "return; // Cross never launches a game while inspecting media." in lib

# Color pair from the Neutral Light palette must exceed 7:1 contrast.
def brightness(hex_color):
    rgb = [(hex_color >> channel) & 255 for channel in (16, 8, 0)]
    channels = [(x / 255.0 / 12.92 if x <= 10 else
                 ((x / 255.0 + 0.055) / 1.055) ** 2.4) for x in rgb]
    return sum(w * x for w, x in zip((0.2126, 0.7152, 0.0722), channels))

light = theme.split("} else if (palette == 3)", 1)[1].split("if (accent > 0", 1)[0]
text_colors = [int(value, 16) for value in re.findall(
    r"k(?:Body|Copy|Meta|Label|Muted|Faint) = Color::rgb\(0x([0-9a-f]+)\)", light)]
assert len(text_colors) == 6
background = brightness(0xFFFFFF)
assert all((background + 0.05) / (brightness(ink) + 0.05) >= 7 for ink in text_colors)

# Compile the REAL locale splitting routine with a small independent catalog
# rather than testing a reimplementation of the delimiter logic.
start = lib.index("std::string library_genres(const std::string& genres)")
end = lib.index("std::string library_size(", start)
method = lib[start:end]
compiler = shutil.which("clang++") or shutil.which("g++")
if not compiler:
    raise SystemExit("C++20 compiler required")
harness = '''
#include <algorithm>
#include <cassert>
#include <string>
#include <string_view>
std::string tr(const std::string& key) {
    if (key == "Strategy") return "Stratégie";
    if (key == "Other") return "Autre";
    if (key == "Platformer") return "Plateforme";
    return key;
}
''' + method + '''
int main() {
    assert(library_genres("Strategy · Other") == "Stratégie · Autre");
    assert(library_genres("Strategy, Other") == "Stratégie · Autre");
    assert(library_genres("Action · Platformer") == "Action · Plateforme");
}
'''
with tempfile.TemporaryDirectory(prefix="encore-nov13-") as tmp:
    source = Path(tmp) / "genres.cpp"
    binary = Path(tmp) / "genres"
    source.write_text(harness, encoding="utf-8")
    subprocess.run([compiler, "-std=c++20", "-Wall", "-Wextra", "-Werror",
                    str(source), "-o", str(binary)], check=True, timeout=30)
    subprocess.run([str(binary)], check=True, timeout=10)

print("ENCORE_NOV13_CRASH_UI_SOURCE_AND_GENRE_HOST_PASS physical_commit=1 query_lifetime=1 cover=1 genres=1 contrast=1")
