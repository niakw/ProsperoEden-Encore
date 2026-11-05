// SPDX-License-Identifier: GPL-3.0-or-later
#include "msaa_force_policy.h"
#include <initializer_list>

#include <cassert>
using namespace Eden::Graphics::MsaaForce;

int main() {
    const Limits ps5like{
        .vulkan=true,
        .framebuffer_color_sample_bits=0x1F,
        .framebuffer_depth_sample_bits=0x0F,
        .color_format_sample_bits=0x1F,
        .depth_format_sample_bits=0x0F,
        .max_framebuffer_width=8192,
        .max_framebuffer_height=8192,
        .free_transient_bytes=512ULL*1024*1024,
    };
    const GuestPass guest{.width=1920,.height=1080,
                          .guest_samples=1,.color_bytes_per_pixel=4,
                          .depth_bytes_per_pixel=4,.render_target_count=1,
                          .uses_depth=true};
    assert(Evaluate(Requested::Auto,guest,ps5like).decision==Decision::NativeAuto);
    for (const auto r : {Requested::X2,Requested::X4,Requested::X8}) {
        // Important: a GPU advertising MSAA != a working forced-MSAA path!
        assert(Evaluate(r,guest,ps5like).decision==
               Decision::ShadowRendererNotImplemented);
    }
    assert(Evaluate(Requested::X16,guest,ps5like).decision==
           Decision::UnsupportedFrameFormat); // depth lacks x16
    auto limits=ps5like;
    limits.framebuffer_depth_sample_bits|=0x10;
    limits.depth_format_sample_bits|=0x10;
    assert(Evaluate(Requested::X16,guest,limits).decision==
           Decision::ShadowRendererNotImplemented);
    auto guest4=guest;
    guest4.guest_samples=4;
    assert(Evaluate(Requested::X2,guest4,limits).decision==
           Decision::NativeGuestSamplesAlreadySatisfy);
    assert(Evaluate(Requested::X4,guest4,limits).decision==
           Decision::NativeGuestSamplesAlreadySatisfy);
    assert(Evaluate(Requested::X8,guest4,limits).decision==
           Decision::GuestMultisampleTopologyConflict);
    auto guest16=guest;
    guest16.guest_samples=16;
    assert(Evaluate(Requested::X16,guest16,ps5like).decision==
           Decision::NativeGuestSamplesAlreadySatisfy);
    auto noVulkan=limits;
    noVulkan.vulkan=false;
    assert(Evaluate(Requested::X4,guest,noVulkan).decision==
           Decision::RequiresVulkan);
    auto noFormat=limits;
    noFormat.color_format_sample_bits=0x3;
    assert(Evaluate(Requested::X4,guest,noFormat).decision==
           Decision::UnsupportedFrameFormat);
    auto budget=limits;
    budget.free_transient_bytes=1;
    assert(Evaluate(Requested::X2,guest,budget).decision==
           Decision::UnsupportedBudget);
    budget.free_transient_bytes=0;
    assert(Evaluate(Requested::X2,guest,budget).decision==
           Decision::UnsupportedBudget);
    auto readback=guest;
    readback.multisample_guest_reads=true;
    assert(Evaluate(Requested::X4,readback,limits).decision==
           Decision::UnsupportedMultisampleRead);
    auto aliased=guest;
    aliased.storage_or_alias_attachments=true;
    assert(Evaluate(Requested::X4,aliased,limits).decision==
           Decision::UnsupportedMultisampleRead);
    auto noSize=guest;
    noSize.width=0;
    assert(Evaluate(Requested::X4,noSize,limits).decision==
           Decision::UnsupportedDimensions);
    Implementation full{
        .native_shadow_color=true,.native_shadow_depth=true,
        .resolve_color_to_guest=true,.resolve_depth_to_guest=true,
        .guest_layout_preserved=true,.sampled_guest_reads_coherent=true,
    };
    // CandidateOnly must never be displayed as 'MSAA applied'.
    assert(Evaluate(Requested::X4,guest,limits,full).decision==
           Decision::CandidateOnly);
    auto missing=full;
    missing.resolve_depth_to_guest=false;
    assert(Evaluate(Requested::X4,guest,limits,missing).decision==
           Decision::ShadowRendererNotImplemented);
    auto noDepth=guest;
    noDepth.uses_depth=false;
    assert(Evaluate(Requested::X16,noDepth,ps5like,missing).decision==
           Decision::CandidateOnly);
    assert(Evaluate(static_cast<Requested>(3),guest,limits).decision==
           Decision::UnsupportedRequest);
    const auto usage=Evaluate(Requested::X16,guest,limits,full);
    assert(usage.estimated_attachment_bytes==1920ULL*1080*8*16);
}
