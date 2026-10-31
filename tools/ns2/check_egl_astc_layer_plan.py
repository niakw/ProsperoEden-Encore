#!/usr/bin/env python3
"""N55: compile real isolated ASTC layer staging planner and source owner guard."""
from pathlib import Path
import subprocess
import tempfile
ROOT=Path(__file__).resolve().parents[2]
HEADER=ROOT/'vendor/encore-active/ns2-helpers/include/video_core/texture_cache/ns2_astc_layer_plan.h'
TEST=ROOT/'tools/ns2/test_egl_astc_layer_plan.cpp'
SOURCE=(ROOT/'vendor/sources/eden/src/video_core/texture_cache/texture_cache.h').read_text()
IMAGE=(ROOT/'vendor/sources/eden/src/video_core/texture_cache/image_base.h').read_text()
VK=(ROOT/'vendor/encore-active/eden-vulkan/vk_texture_cache_cost.cpp').read_text()
for needle in ('void TextureCache<P>::WriteMemory(DAddr cpu_addr, size_t size)',
               'void TextureCache<P>::RefreshContents(Image& image, ImageId image_id)',
               'runtime.AccelerateImageUpload(image, staging,'):
    assert needle in SOURCE,'ASTC texture owner changed: '+needle
for needle in ('u32 guest_size_bytes = 0;', 'ImageFlagBits::CpuModified'):
    assert needle in IMAGE,'image bookkeeping changed: '+needle
assert 'TextureCacheRuntime::AccelerateImageUpload' in VK,'native PS5 ASTC upload owner changed'
assert 'No GPU dispatch or Vulkan sparse residency is enabled' in HEADER.read_text()
with tempfile.TemporaryDirectory(prefix='n55-astc-layer-') as tmp:
    for cxx in ('clang++','g++'):
        exe=Path(tmp)/('n55-'+cxx.replace('+','p'))
        subprocess.run([cxx,'-std=c++20','-O2','-Wall','-Wextra','-Werror',
                        '-fsanitize=undefined','-fno-sanitize-recover=all',
                        '-I',str(ROOT/'vendor/encore-active/ns2-helpers/include'),
                        str(TEST),'-o',str(exe)],check=True)
        subprocess.run([str(exe)],check=True)
print('N55_ASTC_LAYER_PLAN_OWNER_AND_HOST_PASS')
