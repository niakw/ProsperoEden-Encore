// SPDX-License-Identifier: MIT
// Bind the original-model, no-history proxy feature stage to the learned
// FP16[16] -> E4M3FN[32] input-lift without inventing image semantics.
#pragma once
#include "rdna2_nr_proxy_feature_policy.h"
#include "rdna2_nr_image_feature_policy.h"
namespace Eden::Graphics::NeuralRDNA2 {
[[nodiscard]] constexpr bool CanNeuralProxyLiftLink(
    const NeuralProxyFeatures& proxy,
    const ImageFeatureShape& lift) noexcept {
    if(lift.direction!=0u||
       lift.width!=proxy.full_width||
       lift.height!=proxy.full_height)
        return false;
    const auto source=std::uint64_t(proxy.source_width)*
                      proxy.source_height*16u;
    const auto intermediate=std::uint64_t(proxy.full_width)*
                            proxy.full_height*32u;
    if(!CanNeuralProxyFeatures(proxy,{source,intermediate}))
        return false;
    return CanImageFeatureStage(lift,{
        intermediate,1024u,intermediate});
}
} // namespace Eden::Graphics::NeuralRDNA2
