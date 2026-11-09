#!/usr/bin/env python3
"""P2.3: compile real QMD3 SSBO write-commit code AFTER stage validation.

Exercises actual renderer commit hunk with real NativeQmdResourcePlan and
NativeQmdContiguousGpuSpan; no Vulkan driver or PS5 build is involved.
"""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[2]
VENDOR=ROOT/'vendor/encore-active'
RENDERERS=[VENDOR/'eden-vulkan/vulkan_rasterizer.cpp',
           VENDOR/'eden-core/guest-bridge/vulkan_rasterizer.cpp']
PIPELINE=(VENDOR/'eden-vulkan/vk_compute_pipeline_cost.cpp').read_text()
configure=PIPELINE.split('bool ComputePipeline::ConfigureNative(',1)[1].split(
    '\n#endif',1)[0]
assert 'ObtainBufferOperation::MarkAsWritten' not in configure
assert 'Do not mark any guest SSBO written yet.' in configure
# Extract the shipping native ConfigureNative layout guard verbatim. A
# missing VkPipeline/VkPipelineLayout or required VkDescriptorSetLayout must
# abort BEFORE descriptor reservation and guest write tracking.
LAYOUT_START='        if (!pipeline || !pipeline_layout ||'
assert configure.count(LAYOUT_START) == 1
layout_guard = LAYOUT_START + configure.split(LAYOUT_START,1)[1].split(
    '            return false;',1)[0] + '            return false;'
assert configure.index(layout_guard) < configure.index('struct BoundBuffer')
# Execute actual ConfigureNative image/texel descriptor admission, rather
# than asserting that the producer happens to contain source fragments.
IMG_BEGIN='    for (size_t i = 0; i < images.size(); ++i) {'
IMG_END='    // Refuse a mismatched TIC-backed texel span'
TEX_BEGIN='    for (size_t i = 0; i < texels.size(); ++i) {'
TEX_END='    // Never bind the wrong bank.'
assert configure.count(IMG_BEGIN)==configure.count(IMG_END)==1
assert configure.count(TEX_BEGIN)==configure.count(TEX_END)==1
image_guard=IMG_BEGIN+configure.split(IMG_BEGIN,1)[1].split(IMG_END,1)[0]
texel_guard=TEX_BEGIN+configure.split(TEX_BEGIN,1)[1].split(TEX_END,1)[0]
assert configure.index(image_guard)<configure.index(texel_guard)<configure.index('struct BoundBuffer')
ANCHOR='        // Deferred GPU write tracking is a commit, not descriptor staging.\n'
END='        const auto dim = launch.grid;'
blocks=[]
for path in RENDERERS:
    code=path.read_text()
    assert code.count(ANCHOR)==1 and code.count(END)==1
    native=code.split('bool RasterizerVulkan::DispatchNativeCompute(',1)[1].split('\n#endif',1)[0]
    check=native.index('staged_image_tables->MatchesSnapshot(')
    commit=native.index('ObtainBufferOperation::MarkAsWritten')
    dispatch=native.index('cmdbuf.Dispatch(dim[0], dim[1], dim[2]);')
    assert native.index('resources->SameBufferBindings(*after_binding)')<check<commit<dispatch
    assert native.index('if (!current_after_staging ||',check)<commit
    chunk=code.split(ANCHOR,1)[1].split(END,1)[0]
    blocks.append(ANCHOR+chunk)
assert blocks[0]==blocks[1], 'real/native and deferred write commits drifted'
assert 'if (!staged_buffer_mappings.Matches(' in blocks[0]
assert 'ValidateGpuBufferMappings(' not in blocks[0]
CPP=r'''
#include <array>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <memory>
#include <mutex>
#include <optional>
#include <utility>
#include <vector>
#include "shader_recompiler/frontend/ampere/native_qmd_compute_environment.h"
#ifndef VK_NULL_HANDLE
#define VK_NULL_HANDLE 0
#endif
namespace VideoCommon {
enum class ObtainBufferSynchronize { NoSynchronize };
enum class ObtainBufferOperation { DoNothing, MarkAsWritten };
}
bool NativeLayoutsReady(bool pipeline, bool pipeline_layout,
                        bool descriptor_set_layout, std::size_t num_descriptor_entries) {
__LAYOUT_GUARD__
    return true;
}
namespace VideoCore::Surface {
enum class PixelFormat { Invalid, RGBA8 };
}
struct MockImage {
    u64 view{1};
    bool image_pin{true};
    bool view_pin{true};
    u64 guest_gpu_address{0x10000};
    u32 guest_bytes{4096};
    bool storage{};
    u64 sampler{7};
    bool sampler_pin{true};
};
bool NativeImageBindingsReady(const std::vector<MockImage>& images,
                              std::size_t sampled) {
__REAL_IMAGE_GUARD__
    return true;
}
struct MockGpuMemory {
    bool refuse{};
    bool moved{};
    bool split{};
    std::optional<u64> GpuToCpuAddress(u64 address) {
        if(refuse && address>=0x20000 && address<0x21000) return {};
        return address+0x4000000+(moved ? 0x1000000 : 0)+
               ((split && address>=0x21000 && address<0x22000) ? 0x1000 : 0);
    }
};
struct MockBuffer {
    u64 handle{11};
    u64 Handle() const {return handle;}
};
struct MockBufferCache {
    std::mutex mutex;
    MockBuffer buffer;
    MockBuffer invalid{0};
    u64 reject_address{};
    std::vector<std::pair<u64,u32>> writes;
    auto ObtainBuffer(u64 address,u32 bytes,VideoCommon::ObtainBufferSynchronize sync,
                      VideoCommon::ObtainBufferOperation operation) {
        assert(sync==VideoCommon::ObtainBufferSynchronize::NoSynchronize);
        if(operation==VideoCommon::ObtainBufferOperation::MarkAsWritten)
            writes.emplace_back(address,bytes);
        return std::make_pair(address==reject_address ? &invalid : &buffer,u32{0});
    }
};
struct MockTexel {
    u64 guest_gpu_address;
    u32 guest_bytes;
    bool is_written;
    VideoCore::Surface::PixelFormat format{VideoCore::Surface::PixelFormat::RGBA8};
    bool storage{};
};
bool NativeTexelBindingsReady(const std::vector<MockTexel>& texels,
                              std::size_t sampled_texel) {
__REAL_TEXEL_GUARD__
    return true;
}
struct MockRasterizer {
    std::unique_ptr<MockGpuMemory> gpu_memory=std::make_unique<MockGpuMemory>();
    MockBufferCache buffer_cache;
    std::vector<MockTexel> texels;
    std::unique_ptr<Shader::Ampere::NativeQmdResourcePlan> resources=
        std::make_unique<Shader::Ampere::NativeQmdResourcePlan>();
    bool Commit(bool remap_after_staging=false) {
        const auto& native_texels=texels;
        Shader::Ampere::NativeQmdPhysicalBufferSnapshot staged_buffer_mappings{};
        if (!staged_buffer_mappings.Capture(
                *resources, [this](u64 address) {
                    return gpu_memory->GpuToCpuAddress(address);
                }))
            return false;
        // Simulate a guest remapping otherwise fully contiguous VA pages
        // after ConfigureNative staged buffers but before write-commit.
        if (remap_after_staging) gpu_memory->moved=true;
__COMMIT__
        return true;
    }
};
int main() {
    assert(!NativeLayoutsReady(false,true,true,1));
    assert(!NativeLayoutsReady(true,false,true,1));
    assert(!NativeLayoutsReady(true,true,false,1));
    assert(NativeLayoutsReady(true,true,false,0)); // no descriptor shader
    assert(NativeLayoutsReady(true,true,true,1));
    std::vector<MockImage> images(2);
    images[1].storage=true; images[1].sampler=VK_NULL_HANDLE;
    assert(NativeImageBindingsReady(images,1));
    images[0].sampler_pin=false;
    assert(!NativeImageBindingsReady(images,1));
    images[0].sampler_pin=true; images[1].view_pin=false;
    assert(!NativeImageBindingsReady(images,1));
    images[1].view_pin=true; images[1].sampler=7;
    assert(!NativeImageBindingsReady(images,1));
    images[1].sampler=VK_NULL_HANDLE; images[1].storage=false;
    assert(!NativeImageBindingsReady(images,1));
    images[1].storage=true; images[0].guest_bytes=0;
    assert(!NativeImageBindingsReady(images,1));
    images[0].guest_bytes=4096; images[0].image_pin=false;
    assert(!NativeImageBindingsReady(images,1));
    images[0].image_pin=true;
    assert(NativeImageBindingsReady(images,1));
    std::vector<MockTexel> checked_texels{
        MockTexel{0x10000,4096,false},MockTexel{0x20000,4096,true}};
    checked_texels[1].storage=true;
    assert(NativeTexelBindingsReady(checked_texels,1));
    checked_texels[0].format=VideoCore::Surface::PixelFormat::Invalid;
    assert(!NativeTexelBindingsReady(checked_texels,1));
    checked_texels[0].format=VideoCore::Surface::PixelFormat::RGBA8;
    checked_texels[1].storage=false;
    assert(!NativeTexelBindingsReady(checked_texels,1));
    checked_texels[1].storage=true;
    checked_texels[0].guest_gpu_address=0;
    assert(!NativeTexelBindingsReady(checked_texels,1));
    checked_texels[0].guest_gpu_address=0x10000;
    assert(NativeTexelBindingsReady(checked_texels,1));
    MockRasterizer renderer;
    auto& plan=*renderer.resources;
    using Shader::Ampere::NativeQmdStorageBinding;
    plan.storage_buffers.push_back(NativeQmdStorageBinding{0x10000,16,false,true});
    plan.storage_buffers.push_back(NativeQmdStorageBinding{0x20000,0x3000,true,true});
    assert(renderer.Commit());
    assert(renderer.buffer_cache.writes.size()==1);
    assert(renderer.buffer_cache.writes[0].first==0x20000);
    renderer.buffer_cache.writes.clear();
    assert(!renderer.Commit(true));
    assert(renderer.buffer_cache.writes.empty());
    renderer.gpu_memory->moved=false;
    assert(renderer.Commit());
    renderer.buffer_cache.writes.clear();
    // A contiguous guest VA with an independently remapped interior
    // 4 KiB page must fail before any GPU-dirty mark, even if its first
    // GMMU page still resolves to the same physical address.
    renderer.gpu_memory->split=true;
    assert(!renderer.Commit());
    assert(renderer.buffer_cache.writes.empty());
    renderer.gpu_memory->split=false;
    assert(renderer.Commit());
    renderer.buffer_cache.writes.clear();
    // Mapping preflight runs to completion before any cache dirty marking.
    renderer.gpu_memory->refuse=true;
    assert(!renderer.Commit());
    assert(renderer.buffer_cache.writes.empty());
    renderer.gpu_memory->refuse=false;
    plan.storage_buffers[1].known_size=false;
    assert(!renderer.Commit());
    assert(renderer.buffer_cache.writes.empty());
    plan.storage_buffers[1].known_size=true;
    plan.storage_buffers[1].gpu_address=0;
    assert(!renderer.Commit());
    assert(renderer.buffer_cache.writes.empty());
    plan.storage_buffers[1].gpu_address=0x20000;
    plan.storage_buffers[1].is_written=false;
    assert(renderer.Commit() && renderer.buffer_cache.writes.empty());
    plan.storage_buffers[1].is_written=true;
    renderer.buffer_cache.buffer.handle=0;
    assert(!renderer.Commit());
    assert(renderer.buffer_cache.writes.empty());
    renderer.buffer_cache.buffer.handle=11;
    // All write targets must be validated before the first dirty mark.
    plan.storage_buffers.push_back(NativeQmdStorageBinding{0x30000,16,true,true});
    renderer.buffer_cache.reject_address=0x30000;
    assert(!renderer.Commit());
    assert(renderer.buffer_cache.writes.empty());
    renderer.buffer_cache.reject_address=0;
    assert(renderer.Commit());
    assert(renderer.buffer_cache.writes.size()==2);
    assert(renderer.buffer_cache.writes[0].first==0x20000);
    assert(renderer.buffer_cache.writes[1].first==0x30000);
    // The newer P2.2 texel path must share the SAME preflight-before-dirty
    // transaction, not be omitted by an obsolete storage-only fixture.
    renderer.buffer_cache.writes.clear();
    renderer.texels.push_back(MockTexel{0x40000,4096,true});
    renderer.buffer_cache.reject_address=0x40000;
    assert(!renderer.Commit());
    assert(renderer.buffer_cache.writes.empty());
    renderer.buffer_cache.reject_address=0;
    assert(renderer.Commit());
    assert(renderer.buffer_cache.writes.size()==3);
    assert(renderer.buffer_cache.writes[2].first==0x40000);
    renderer.buffer_cache.writes.clear();
    renderer.texels[0].is_written=false;
    assert(renderer.Commit());
    assert(renderer.buffer_cache.writes.size()==2);
}
'''.replace('__COMMIT__',blocks[0]).replace('__LAYOUT_GUARD__',layout_guard).replace(
    '__REAL_IMAGE_GUARD__',image_guard).replace('__REAL_TEXEL_GUARD__',texel_guard)
boost_caches=sorted((Path.home()/'.cache').glob(
    'ps5-eden-*/source/.cache/cpm/boost/boost-*/libs'))
includes=[ROOT/'vendor/sources/fmt/include',
          ROOT/'vendor/encore-active/ns2-runtime/ampere',
          ROOT/'vendor/encore-active/ns2-runtime/gpu_dispatch',
          ROOT/'vendor/sources/eden/src']
if boost_caches:
    includes.extend(sorted(p for p in boost_caches[-1].rglob('include')
                           if (p/'boost').is_dir()))
env=dict(os.environ)
sdk=Path('/Library/Developer/CommandLineTools/SDKs/MacOSX15.4.sdk')
if sdk.exists():env['SDKROOT']=str(sdk)
compilers=list(dict.fromkeys(filter(None,(shutil.which('clang++'),shutil.which('g++')))))
assert compilers
with tempfile.TemporaryDirectory(prefix='encore-write-commit-') as temp:
    fixture=Path(temp)/'real-commit.cpp';fixture.write_text(CPP)
    for cxx in compilers:
        for opt in (0,2):
            exe=Path(temp)/f'{Path(cxx).name}-O{opt}'
            cmd=[cxx,'-std=c++20',f'-O{opt}','-Wall','-Wextra','-Werror',
                 '-Wno-unused-parameter','-DFMT_HEADER_ONLY',
                 '-fsanitize=undefined','-fno-sanitize-recover=all']
            cmd+=['-I'+str(p) for p in includes]
            cmd+=[str(fixture),'-o',str(exe)]
            built=subprocess.run(cmd,env=env,capture_output=True,text=True,timeout=70)
            assert built.returncode==0,(cxx,built.stderr[-3500:])
            run=subprocess.run([str(exe)],env=env,capture_output=True,text=True,timeout=20)
            assert run.returncode==0,(cxx,run.stderr[-3500:])
            print('P2_3_NATIVE_STORAGE_COMMIT_AFTER_SNAPSHOT_PASS',Path(cxx).name,
                  f'O{opt}', 'mappings=full', 'physical_remap=refused', 'interior_page=refused',
                  'missing_layout=refused', 'missing_image_pin=refused',
                  'wrong_image_kind=refused', 'invalid_texel_format=refused',
                  'writes=known', 'owners=2',flush=True)
