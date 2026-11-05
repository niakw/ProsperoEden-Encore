#!/usr/bin/env python3
"""R07 true FSR 3.1.4 native backend source/packaging contract (no PS5 build).

Submodules must be pinned to the exact vendored original AMD SDK shader
subset + maintained host implementation. This test never claims that
temporal input images are available in a running game.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import re
root=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser()
p.add_argument("--vendor-root",type=Path,default=root/"vendor")
args=p.parse_args()
vendor=args.vendor_root
sdk=vendor/"encore-active/amd-fsr31"
backend=vendor/"encore-active/eden-vulkan"
cmake=(root/"headless/vulkan.cmake").read_text()
generator=(root/"tools/graphics/build-fsr31-amd-shaders.py").read_text()
upscaler=(backend/"fsr31_temporal_upscaler.cpp").read_text()
bridge=(backend/"fsr31_native_bridge.cpp").read_text()
pool=(backend/"fsr31_descriptor_pool.cpp").read_text()
pool_h=(backend/"include/video_core/renderer_vulkan/vk_descriptor_pool.h").read_text()
contract=(root/"extras/graphics/fsr31_temporal_contract.h").read_text()
assert "c6efa6bf7f2027b3ec94f28578bb5965eabb9e55" in (sdk/"README.md").read_text()
assert "Permission is hereby granted" in (sdk/"LICENSE.txt").read_text()
assert "EDEN_FSR31_NAMES" in cmake and "eden-r07-fsr31-shaders" in cmake
assert "add_dependencies(video_core eden-r07-fsr31-shaders)" in cmake
assert "fsr31_temporal_upscaler.cpp" in cmake
assert "fsr31_native_bridge.cpp" in cmake
assert "fsr31_descriptor_pool.cpp" in cmake
assert "renderer_vulkan/vk_descriptor_pool.cpp)" in cmake
assert "vk_fsr3_upscaler.h" in cmake
assert "VK_DESCRIPTOR_TYPE_SAMPLED_IMAGE" in pool
assert "VK_DESCRIPTOR_TYPE_SAMPLER" in pool
assert "u32 sampled_images" in pool_h and "u32 samplers" in pool_h
assert "shaderStorageImageExtendedFormats" in upscaler
assert "FSR3_UPSCALER_PREPARE_INPUTS_COMP_SPV" in upscaler
assert "FSR3_UPSCALER_ACCUMULATE_COMP_SPV" in upscaler
assert "FSR3_UPSCALER_RCAS_COMP_SPV" in upscaler
assert "in.device_to_view_depth" in upscaler
assert "in.tan_half_fov" in upscaler
assert "CAMERA_NEAR" not in upscaler
assert "CAMERA_FOV" not in upscaler
assert "Temporal::FrameContinuity" in (backend/"include/video_core/renderer_vulkan/fsr31_native_bridge.h").read_text()
assert "continuity.Observe(frame.metadata)" in bridge
assert "std::isfinite(frame.sharpness)" in bridge
assert "std::nullopt" in bridge and "ResetHistory()" in bridge
assert "scheduler.Finish()" in bridge
assert "native_hud_is_separate" in contract and "guest_hud_is_separate" in contract
assert "GuestGpuVerified" in contract
assert "InvalidProjection" in contract
assert "InvalidVulkanImageLayout" in contract
names=re.findall(r'\("([a-z_]+)","([a-z_]+)",(True|False),(True|False)\)',generator)
assert len(names)==11 and len({item[0] for item in names})==11
for name,shader,_,_ in names:
    assert (sdk/"shaders/fsr3upscaler"/("ffx_fsr3upscaler_"+shader+"_pass.glsl")).exists()
assert "fsr3upscaler" in generator and "spirv-val" in generator
# This is NOT a runtime mode in the frontend. Source alone cannot make the
# PS5 perform temporal reconstruction unless a verified guest producer exists.
settings=(root/"headless/settings_store.h").read_text()
assert '"sgsr_edge"' in settings
assert '"fsr3_temporal"' not in settings
print("PASS FSR31 vendor: AMD MIT 11 GPU passes, C++ scheduler backend, real sampler descriptor pools, verified guest input bridge and no fake active menu")
