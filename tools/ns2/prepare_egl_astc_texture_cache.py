#!/usr/bin/env python3
"""N60 opt-in ASTC CPU-write to actual texture-cache Vulkan path source adapter."""
from pathlib import Path
import argparse
def once(s,a,b):
    if s.count(a)!=1: raise RuntimeError("N60 maintained owner drift: "+a[:80])
    return s.replace(a,b)
def adapt(image,base,tex):
    image=once(image,'#include "video_core/texture_cache/image_info.h"',
        '#include "video_core/texture_cache/image_info.h"\n#include "video_core/texture_cache/ns2_astc_layer_plan.h"')
    image=once(image,'    u32 guest_size_bytes = 0;',
        '''    u32 guest_size_bytes = 0;
    std::optional<Eden::NS2::Eglantine::AstcDirtyLayerPlanner> ns2_astc_dirty;''')
    base=once(base,'    struct PendingUnswizzle {','''    bool Ns2AstcEligible(const ImageBase&) const noexcept;
    bool Ns2UploadDirtyLayers(Image&);

    struct PendingUnswizzle {''')
    tex=once(tex,'#include "video_core/texture_cache/texture_cache_base.h"',
        '#include "video_core/texture_cache/texture_cache_base.h"\n#include "video_core/texture_cache/ns2_astc_staging_bridge.h"')
    tex=once(tex,'''    ForEachImageInRegion(cpu_addr, size, [this](ImageId image_id, Image& image) {
        if (True(image.flags & ImageFlagBits::CpuModified)) {''',
    '''    ForEachImageInRegion(cpu_addr, size, [this, cpu_addr, size](ImageId image_id, Image& image) {
        if (image.ns2_astc_dirty) {
            if (image.ns2_astc_dirty->MarkWrite(cpu_addr, size)) {
                image.flags |= ImageFlagBits::CpuModified;
                return; // keep tracking each CPU write, including subsequent writes
            }
            image.ns2_astc_dirty.reset();
        }
        if (True(image.flags & ImageFlagBits::CpuModified)) {''')
    tex=once(tex,'''    for (const ImageId id : deleted_images) {
        Image& image = slot_images[id];
        if (False(image.flags & ImageFlagBits::CpuModified)) {''',
    '''    for (const ImageId id : deleted_images) {
        Image& image = slot_images[id];
        image.ns2_astc_dirty.reset(); // all prior layer residency is invalid
        if (False(image.flags & ImageFlagBits::CpuModified)) {''')
    tex=once(tex,'''    image.flags &= ~ImageFlagBits::CpuModified;

    TrackImage(image, image_id);

    if (image.info.num_samples > 1''',
    '''    image.flags &= ~ImageFlagBits::CpuModified;

    if (image.ns2_astc_dirty && Ns2AstcEligible(image)) {
        try {
            if (Ns2UploadDirtyLayers(image)) {
                if (False(image.flags & ImageFlagBits::Tracked))
                    TrackImage(image, image_id);
                runtime.InsertUploadMemoryBarrier();
                return;
            }
        } catch (...) {
            // No partial result can acknowledge a failed write.
        }
    }
    image.ns2_astc_dirty.reset();
    if (False(image.flags & ImageFlagBits::Tracked))
        TrackImage(image, image_id);

    if (image.info.num_samples > 1''')
    tex=once(tex,'''    UploadImageContents(image, staging);
    runtime.InsertUploadMemoryBarrier();
}

template <class P>
template <typename StagingBuffer>''',
    '''    UploadImageContents(image, staging);
    runtime.InsertUploadMemoryBarrier();
    if (Ns2AstcEligible(image)) {
        image.ns2_astc_dirty.emplace(
            image.cpu_addr, image.guest_size_bytes, image.info.layer_stride,
            static_cast<u32>(image.info.resources.layers), 0, u64{64} << 20);
        if (!image.ns2_astc_dirty->ResetAfterFullUpload())
            image.ns2_astc_dirty.reset();
    }
}

template <class P>
bool TextureCache<P>::Ns2AstcEligible(const ImageBase& image) const noexcept {
    if constexpr (requires { &Runtime::AccelerateImageUploadLayers; }) {
        constexpr ImageFlagBits unsafe = ImageFlagBits::Sparse |
            ImageFlagBits::Remapped | ImageFlagBits::Alias |
            ImageFlagBits::GpuModified | ImageFlagBits::Converted |
            ImageFlagBits::Rescaled | ImageFlagBits::AsynchronousDecode |
            ImageFlagBits::IsDecoding;
        return True(image.flags & ImageFlagBits::AcceleratedUpload) &&
            IsPixelFormatASTC(image.info.format) && False(image.flags & unsafe) &&
            image.info.type == ImageType::e2D &&
            image.info.resources.levels > 0 && image.info.resources.levels <= 16 &&
            image.info.resources.layers > 1 && image.info.resources.layers <= 4096 &&
            image.info.layer_stride > 0 && image.info.layer_stride <= (u64{64} << 20) &&
            image.guest_size_bytes >= (u64{64} << 20) && image.cpu_addr != 0;
    }
    return false;
}

template <class P>
bool TextureCache<P>::Ns2UploadDirtyLayers(Image& image) {
    if constexpr (requires { &Runtime::AccelerateImageUploadLayers; }) {
        if (!image.ns2_astc_dirty || !image.ns2_astc_dirty->Valid()) return false;
        const auto swizzles = FullUploadSwizzles(image.info);
        // N57 intentionally rejects skipped or trimmed mip chains.
        if (swizzles.empty() || swizzles.front().level != 0 ||
            swizzles.front().buffer_offset != 0) return false;
        std::optional<decltype(runtime.UploadStagingBuffer(size_t{}))> staging;
        const auto result = Eden::NS2::Eglantine::UploadAstcDirtyLayerBatches(
            *image.ns2_astc_dirty, image.gpu_addr,
            [&](u32, u64 bytes) {
                staging.emplace(runtime.UploadStagingBuffer(static_cast<size_t>(bytes)));
                return staging && staging->mapped_span.size_bytes() >= bytes;
            },
            [&](u64 guest, u64 offset, u64 count) {
                if (!staging || offset > staging->mapped_span.size_bytes() ||
                    count > staging->mapped_span.size_bytes() - offset) return false;
                gpu_memory->ReadBlock(guest, staging->mapped_span.data() + offset, count,
                    VideoCommon::CacheType::NoTextureCache);
                return true;
            },
            [&](u32, std::span<const u32> layers) {
                if (!staging) return false;
                runtime.AccelerateImageUploadLayers(
                    image, *staging, FixSmallVectorADL(swizzles), layers);
                staging.reset(); // N57 synchronous Vulkan flush completed
                return true;
            });
        return result.status == Eden::NS2::Eglantine::AstcTransferStatus::Completed ||
               result.status == Eden::NS2::Eglantine::AstcTransferStatus::NoChanges;
    }
    return false;
}

template <class P>
template <typename StagingBuffer>''')
    return {"video_core/texture_cache/image_base.h":image,
            "video_core/texture_cache/texture_cache_base.h":base,
            "video_core/texture_cache/texture_cache.h":tex}
def main():
    p=argparse.ArgumentParser()
    for arg in ("image","base","texture","output"):p.add_argument("--"+arg,required=True)
    a=p.parse_args()
    files=adapt(Path(a.image).read_text(),Path(a.base).read_text(),Path(a.texture).read_text())
    for name,content in files.items():
        target=Path(a.output)/name;target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(content)
    print("N60_NATIVE_TEXTURE_CACHE_BRIDGE_OWNER_GENERATED")
if __name__=="__main__":main()
