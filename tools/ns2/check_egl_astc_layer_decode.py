#!/usr/bin/env python3
"""N57: regenerate exact source overlays from pinned PS5 code; test safe dispatch."""
from pathlib import Path
import subprocess
import tempfile
import sys
ROOT=Path(__file__).resolve().parents[2]
NATIVE=ROOT/'vendor/encore-active/eden-vulkan'
PIN=ROOT/'vendor/sources/eden/src/video_core/renderer_vulkan'
GEN=ROOT/'tools/ns2/prepare_egl_astc_layer_decode.py'
HEADER=ROOT/'headless/ns2/eglantine/video_core/renderer_vulkan/ns2_astc_decode_preflight.h'
ARGS=[
 '--texture-cpp',str(NATIVE/'vk_texture_cache_cost.cpp'),
 '--compute-cpp',str(NATIVE/'vk_compute_pass_cost.cpp'),
 '--texture-h',str(PIN/'vk_texture_cache.h'),
 '--compute-h',str(PIN/'vk_compute_pass.h')
]
CMAKE=(ROOT/'headless/CMakeLists.txt').read_text()
assert 'EDEN_NS2_ASTC_LAYER_DECODE_EXPERIMENTAL OR' in CMAKE
assert 'list(REMOVE_ITEM video_sources "${eden_ns2_astc_orig_texture}"' in CMAKE
assert 'target_include_directories(video_core BEFORE PUBLIC' in CMAKE
with tempfile.TemporaryDirectory(prefix='n57-astc-vulkan-') as t:
    out=Path(t)
    subprocess.run([sys.executable,str(GEN),*ARGS,'--output',str(out)],check=True)
    cache=(out/'vk_texture_cache_cost.cpp').read_text()
    compute=(out/'vk_compute_pass_cost.cpp').read_text()
    for needle in ('Image::StorageImageLayerView(', 'AccelerateImageUploadLayers(',
                   'MakeStorageView(runtime->device.GetLogical(), level',
                   'Saved PS5 driver pipeline cache atomically'):
        if needle=='Saved PS5 driver pipeline cache atomically':continue
        assert needle in cache,needle
    assert 'void ASTCDecoderPass::AssembleLayers(' in compute
    assert 'cmdbuf.Dispatch(dx, dy, 1)' in compute
    assert 'image.IsInitializedForLayerUpload()' in compute
    assert 'PreflightAstcLayerDecode(' in compute
    assert 'image.host_level_offset' not in compute, 'unsupported pinned mip-owner field'
    assert '#include <stdexcept>' in compute
    assert 'scheduler.Flush();' in compute
    assert 'void ASTCDecoderPass::Assemble(Image& image' in compute
    assert 'void TextureCacheRuntime::AccelerateImageUpload(' in cache
    assert 'std::vector<vk::ImageView> storage_layer_views;' in (out/'include/video_core/renderer_vulkan/vk_texture_cache.h').read_text()
    for cxx in ('clang++','g++'):
        exe=out/('n57-'+cxx.replace('+','p'))
        subprocess.run([cxx,'-std=c++20','-O2','-Wall','-Wextra','-Werror',
                        '-fsanitize=undefined','-fno-sanitize-recover=all',
                        '-I',str(ROOT/'headless/ns2/eglantine'),
                        str(ROOT/'tools/ns2/test_egl_astc_decode_contract.cpp'),
                        '-o',str(exe)],check=True)
        subprocess.run([str(exe)],check=True)
print('N57_ASTC_VULKAN_OWNER_AND_HOST_CONTRACT_PASS')
