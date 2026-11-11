// SPDX-License-Identifier: GPL-3.0-or-later
// Two TRUE native spatial Vulkan owners in sequence: FSR1, SGSR, SGSR Edge.
// Host-only qualification. No PS5 activation or guest-capture bypass.
#pragma once
#include "neural_pipeline_composer.h"
#include <cstdint>
#include <type_traits>
namespace Eden::Graphics::PipelineComposer {
inline constexpr bool kNativeSpatialVulkanChainQualified=false;
enum class TwoPassReason : std::uint8_t {
    CandidateOnly,UnsupportedStage,WrongSourceOrTarget,InvalidShape,
    MissingNativeImageOwnership,MissingBarrier,MissingFence
};
struct TwoPassInput {
    int first{1},second{5};
    Extent source{1280u,720u},intermediate{2560u,1440u},
           target{3840u,2160u};
    std::uint64_t source_image{},source_view{},first_image{},
                  first_view{},second_image{},second_view{};
    bool same_vulkan_queue{};
    bool first_renderpass_recorded{};
    bool color_write_to_fragment_read_barrier{};
    bool second_renderpass_recorded{};
    bool both_owners_live_through_gpu_tick{};
};
struct TwoPassResult {
    TwoPassReason reason{TwoPassReason::UnsupportedStage};
    bool host_contract_passed{},ps5_runtime_allowed{};
};
// VkImage/VkImageView may be pointers or uint64_t depending on Vulkan
// header configuration. Keep tokens as pure host policy IDs only.
template<typename NativeHandle>
[[nodiscard]] std::uint64_t NativeHandleToken(NativeHandle handle) noexcept {
    if constexpr(std::is_pointer_v<NativeHandle>)
        return static_cast<std::uint64_t>(
            reinterpret_cast<std::uintptr_t>(handle));
    else
        return static_cast<std::uint64_t>(handle);
}
[[nodiscard]] constexpr bool IsTrueSpatialShader(int method) noexcept {
    return method==1||method==5||method==6;
}
[[nodiscard]] constexpr TwoPassResult AssessTwoPass(const TwoPassInput& x) noexcept {
    TwoPassResult v{};
    if(!IsTrueSpatialShader(x.first)||!IsTrueSpatialShader(x.second))
        return v;
    if(x.source!=Extent{1280u,720u}||
       x.target!=Extent{3840u,2160u}) {
        v.reason=TwoPassReason::WrongSourceOrTarget;return v;
    }
    if(!ValidExtent(x.intermediate)||
       x.intermediate.width<=x.source.width||
       x.intermediate.height<=x.source.height||
       x.intermediate.width>=x.target.width||
       x.intermediate.height>=x.target.height) {
        v.reason=TwoPassReason::InvalidShape;return v;
    }
    const auto ids=std::array<std::uint64_t,6>{
        x.source_image,x.source_view,x.first_image,x.first_view,
        x.second_image,x.second_view};
    for(std::size_t i=0;i<ids.size();++i) {
        if(!ids[i]) {
            v.reason=TwoPassReason::MissingNativeImageOwnership;return v;
        }
        for(std::size_t j=0;j<i;++j) {
            if(ids[i]==ids[j]) {
                v.reason=TwoPassReason::MissingNativeImageOwnership;return v;
            }
        }
    }
    if(!x.first_renderpass_recorded||
       !x.second_renderpass_recorded||
       !x.color_write_to_fragment_read_barrier) {
        v.reason=TwoPassReason::MissingBarrier;return v;
    }
    if(!x.same_vulkan_queue||!x.both_owners_live_through_gpu_tick) {
        v.reason=TwoPassReason::MissingFence;return v;
    }
    v.reason=TwoPassReason::CandidateOnly;
    v.host_contract_passed=true;
    v.ps5_runtime_allowed=kComposablePs5RuntimeQualified&&
                          kNativeSpatialVulkanChainQualified;
    return v;
}
} // namespace Eden::Graphics::PipelineComposer
