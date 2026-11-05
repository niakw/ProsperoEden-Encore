#!/usr/bin/env python3
"""No full PS5 build: check real FSR1 and LSFG source attachment/capability."""
from pathlib import Path
root=Path(__file__).resolve().parents[2]
read=lambda name:(root/name).read_text()
native=read("headless/vulkan.cmake")
main=read("headless/main.cpp")
render=read("headless/vulkan_renderer_r08.cpp")
reader=read("headless/lossless_dll_r08.cpp")
vendor=root/"vendor"
assert vendor.exists(), "pinned source vendor is needed"
# The FSR1 EASU/RCAS Vulkan renderer is an actual filter, not FSR3 framegen.
assert "Settings::ScalingFilter::Fsr" in main
assert "Settings::values.fsr_sharpening_slider.SetValue(" in main
assert "Fsr3Vulkan" in read("extras/graphics/framegen_capabilities.h")
assert "Fsr3Vulkan" not in render, "do not fake an FSR3 runtime"
# Android-only upstream LSFG option is not enough on PS5; compile ALL C++
# components in production and resolve the exact per-title user selection.
lsfg_sources=[
 "frame_gen/lsfg_translate.cpp", "renderer_vulkan/present/frame_gen.cpp",
 "renderer_vulkan/present/frame_gen_pacer.cpp",
 "renderer_vulkan/present/lsfg_alpha.cpp",
 "renderer_vulkan/present/lsfg_beta.cpp",
 "renderer_vulkan/present/lsfg_chain.cpp",
 "renderer_vulkan/present/lsfg_common.cpp",
 "renderer_vulkan/present/lsfg_delta.cpp",
 "renderer_vulkan/present/lsfg_gamma.cpp",
 "renderer_vulkan/present/lsfg_generate.cpp",
 "renderer_vulkan/present/lsfg_mipmaps.cpp",
 "renderer_vulkan/present/lsfg_shaders.cpp",
]
for source in lsfg_sources:
    assert source in native, f"Missing LSFG source {source}"
assert "target_compile_definitions(video_core PUBLIC HAS_LSFG)" in native
assert 'lossless_dll_r08.cpp' in native
assert "Settings::values.frame_gen.SetValue(lossless_available)" in main
assert "Eden::Display::frame_generation_method.load" in render
assert "frame_gen.Process(" in render and "frame_gen.GenerateInto(" in render
assert "Settings::values.frame_gen.SetValue(lossless_available)" in main
assert "(native_fg_method == 1 || native_fg_method == 3)" in render
assert "blit_swapchain.DrawHudOverlay(device, generated, postprocess_hud);" in render
assert "if (postprocess_hud_required)" in render
assert "present_manager.Present(generated);" in render
assert "FrameGen::" not in read("headless/mihawk_vulkan_stage.cpp")
assert 'VK_NO_PROTOTYPES' in native, "MihawkGen loader must remain namespace-isolated"
# The DLL is private, never linked, mapped, or included in an app zip.
assert "LoadLibrary" not in reader and "dlopen" not in reader
assert "kMaxUserDllBytes = 256ull * 1024 * 1024" in reader
assert "std::filesystem::is_symlink(status)" in reader
assert "std::filesystem::is_regular_file(status)" in reader
assert "file.GetSize() > kMaxUserDllBytes" in reader
assert "GetLosslessDllPath()" in reader
assert "LOSSLESS_DLL_FILE" in reader
pack=read("tools/package-headless-native.sh")
assert 'Lossless.dll' not in pack and 'lossless_dll_r08.cpp' not in pack
assert "model.fgw" not in reader
print("GRAPHICS SOURCES OK: Vulkan FSR spatial active, LSFG native sources attached, user DLL-only, FSR3 not misrepresented")

status = read("headless/lossless_user_file.h")
menu = read("headless/prosperoeden/pe/ui/settings.cpp")
game_ui = read("headless/prosperoeden/pe/ui/library.cpp")
service = read("headless/prosperoeden/eden_services.cpp")
assert "LosslessUserFileLooksValid" in status
assert "symlink_status" in status
assert "file_size" in status
assert 'kLosslessRelative = "lossless/Lossless.dll"' in status
assert 'kLosslessConsolePath' in status
assert 'services_.has_lossless_dll()' in menu
assert 'services_.has_lossless_dll()' in game_ui
assert 'Graphics::LosslessUserFileLooksValid(Eden::UserDir())' in service
assert 'frame_generation_method.store(active_framegen)' in main
assert "Enhanced smoothness" in menu and "Enhanced smoothness" in game_ui
print("LSFG UI PASS: missing file alerted, option not saved, game runtime falls back to real frames")
