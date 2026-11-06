#!/usr/bin/env python3
"""R24 native AA pass source audit, no PS5 build or fake quality presets."""
from pathlib import Path

root = Path(__file__).resolve().parents[2]
read = lambda name: (root / name).read_text()
cmake = read("headless/vulkan.cmake")
layer = read("headless/vulkan_present_layer_r24.cpp")
header = read("headless/vulkan_present_layer_r24.h")
extent = read("extras/graphics/aa_source_extent.h")
launcher = read("headless/main.cpp")
settings = read("headless/settings_store.h")

assert 'vulkan_present_layer_r24.cpp' in cmake
assert 'vulkan_present_layer_r24.h' in cmake
assert 'renderer_vulkan/present/layer.h" COPYONLY' in cmake
assert 'vulkan_present_layer.cpp"' not in cmake
assert "void Layer::SetAntiAliasPass(const Device& device, VkExtent2D source_extent)" in layer
assert 'SetAntiAliasPass(device, {aa_source.width, aa_source.height})' in layer
assert 'Eden::Graphics::AaSourceExtent(' in layer
assert 'Eden::Graphics::AaValid(' in layer
assert 'anti_alias_extent.width' in layer
assert 'anti_alias_extent.height' in layer
assert 'anti_alias_extent = source_extent' in layer
assert 'scheduler.Finish()' in layer and 'device.GetLogical().WaitIdle()' in layer
assert 'Settings::values.resolution_info.ScaleUp(raw_width)' not in layer
assert 'VkExtent2D anti_alias_extent{}' in header
assert 'AaSourceExtent(' in extent and 'AaValid(' in extent
# Actual AA before spatial upscale, with real Vulkan FXAA/SMAA passes.
aa = layer.index('fxaa->Draw(')
smaa = layer.index('smaa->Draw(')
fsr = layer.index('fsr->Draw(')
assert aa < fsr and smaa < fsr
# Upstream's imported SMAA uses PRESET_ULTRA already; preserve its
# historic enum/index and append the separate FXAA Quality SPIR-V option.
assert 'kAntiAliasingKeys[] = {"none", "fxaa", "smaa", "fxaa_quality"}' in settings
assert 'Settings::AntiAliasing::Smaa, Settings::AntiAliasing::Fxaa' in launcher
assert 'SetEnhancedFxaa(' in launcher and 'anti_aliasing == 3' in launcher
# The exact persisted filter must reach the runtime rather than being a
# UI-only control or overwritten by a per-game profile silently.
assert 'Settings::values.anti_aliasing.SetValue(aa[' in launcher
assert 'game_video.anti_aliasing >= 0 ? game_video.anti_aliasing : profile_aa' in launcher
print("PASS R24 source: existing None/FXAA/SMAA preserved, distinct FXAA+ renderer, actual source extent, resize, AA before upscale")
