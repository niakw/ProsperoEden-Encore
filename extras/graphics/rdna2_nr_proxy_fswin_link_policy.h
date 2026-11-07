// SPDX-License-Identifier: MIT
// First-segment R09 GPU shape contract: normalized proxy -> FP16 C16 ->
// learned FP8 C32 raster -> FSwin C32 8x8 window tensor.
// This is NOT a colour image, full U-Net, or runnable presenter.
#pragma once
#include "rdna2_nr_proxy_lift_link_policy.h"
#include "rdna2_nr_fswin_chain_layout_policy.h"
#include "rdna2_nr_fswin_raster_layout_policy.h"
namespace Eden::Graphics::NeuralRDNA2 {
[[nodiscard]] constexpr bool CanNeuralProxyFSwinLink(
    const NeuralProxyFeatures& proxy,
    const ImageFeatureShape& lift,
    const FSwinWindowLayout& first_window,
    std::uint32_t channels,
    const FSwinRasterLayoutStorage& buffers) noexcept {
    if(!CanNeuralProxyLiftLink(proxy,lift)||channels!=32u||
       first_window.shift_x<-1||first_window.shift_x>1||
       first_window.shift_y<-1||first_window.shift_y>1||
       first_window.windows_x!=(proxy.full_width+7u)/8u||
       first_window.windows_y!=(proxy.full_height+7u)/8u)
        return false;
    return CanFSwinRasterLayout({
        proxy.full_width,proxy.full_height,
        first_window.windows_x,first_window.windows_y,channels,0u},
        buffers);
}
} // namespace Eden::Graphics::NeuralRDNA2
