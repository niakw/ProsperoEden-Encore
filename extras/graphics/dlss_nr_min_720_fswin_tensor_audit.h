// SPDX-License-Identifier: GPL-3.0-or-later
// Host-only account of the REAL per-layer FSwin tensor-owner allocation
// policy in pinned native nr_rdna2_fswin_gpu_tensors.cpp. Not a Vulkan
// allocation, not model weights, not GPU VRAM residency or PS5 admission.
// All FSwinLayerRuntime objects currently own independent tensor buffers.
#pragma once
#include "dlss_nr_min_720_route_trial.h"
#include "video_core/renderer_vulkan/nr_rdna2_fswin_plan.h"
#include <algorithm>
#include <array>
#include <cstdint>
#include <string_view>

namespace Eden::Graphics::DlssNrMin {
enum class FSwin720TensorIssue : std::uint8_t {
    None, Graph, Plan, BadBuffer, PerLayerCap, IncorrectCoverage
};
struct FSwin720TensorEstimate {
    FSwin720TensorIssue issue{FSwin720TensorIssue::None};
    std::array<std::uint32_t,4u> layers_by_channels{};
    std::array<std::uint64_t,4u> bytes_by_channels{};
    std::uint64_t requested_bytes{},largest_buffer{},largest_layer{};
    std::uint32_t layers{},buffer_count{},chain_count{};
    bool includes_gpu_weights{false},gpu_executable{false};
};
[[nodiscard]] inline bool AuditFSwin720OwnedTensorBuffers(
    std::string_view reference,FSwin720TensorEstimate& output) {
    output={};
    Route720Trial route{};
    if(!BuildR09Min720Routes(reference,route)) {
        output.issue=FSwin720TensorIssue::Graph;return false;
    }
    const auto chains=NR::ExtractNativeFSwinSegments(route.rows);
    if(chains.size()!=8u) {
        output.issue=FSwin720TensorIssue::IncorrectCoverage;
        return false;
    }
    FSwin720TensorEstimate staged{};
    staged.chain_count=static_cast<std::uint32_t>(chains.size());
    for(const auto& chain:chains){
        for(const auto& layer:chain.layers){
            NR::FSwinGraph plan{};
            if(!NR::MakeFSwinGraphPlan(
                layer.channels,layer.windows,plan)) {
                output.issue=FSwin720TensorIssue::Plan;return false;
            }
            const bool c32=layer.channels==32u;
            const std::array<std::uint64_t,9u> requested{
                std::max(plan.dense_storage[0].input_bytes,
                         plan.dense_storage[2].residual_bytes),
                plan.dense_storage[0].output_bytes,
                c32?0u:plan.dense_storage[1].output_bytes,
                std::max({plan.dense_storage[2].output_bytes,
                          plan.dense_storage[3].residual_bytes,
                          plan.qkv_storage.activation_bytes}),
                0u,0u,0u, // REAL shader Q,K,V alias into expanded
                std::max(plan.attention_storage.out_bytes,
                         plan.dense_storage[3].input_bytes),
                plan.dense_storage[3].output_bytes
            };
            constexpr std::uint64_t max_per=256ull<<20;
            constexpr std::uint64_t max_layer=512ull<<20;
            std::uint64_t layer_total{};
            unsigned buffers{};
            for(unsigned i=0u;i<requested.size();++i){
                const auto bytes=requested[i];
                if(bytes==0u) {
                    if((i==2u&&c32)||(i>=4u&&i<=6u))continue;
                    output.issue=FSwin720TensorIssue::BadBuffer;return false;
                }
                if((bytes&3u)||bytes>max_per||
                   bytes>max_layer||layer_total>max_layer-bytes) {
                    output.issue=FSwin720TensorIssue::PerLayerCap;
                    return false;
                }
                ++buffers;
                layer_total+=bytes;
                if(bytes>staged.largest_buffer)staged.largest_buffer=bytes;
            }
            if(buffers!=(c32?5u:6u)||!layer_total) {
                output.issue=FSwin720TensorIssue::IncorrectCoverage;
                return false;
            }
            const unsigned idx=layer.channels==32u?0u:
                layer.channels==64u?1u:layer.channels==128u?2u:3u;
            ++staged.layers_by_channels[idx];
            staged.bytes_by_channels[idx]+=layer_total;
            staged.requested_bytes+=layer_total;
            staged.buffer_count+=buffers;
            ++staged.layers;
            if(layer_total>staged.largest_layer)
                staged.largest_layer=layer_total;
        }
    }
    unsigned counted{};
    std::uint64_t bytes{};
    for(unsigned i=0u;i<4u;++i){
        counted+=staged.layers_by_channels[i];
        bytes+=staged.bytes_by_channels[i];
    }
    if(staged.layers!=counted||staged.requested_bytes!=bytes||
       staged.layers!=route.mapped_fswin_dispatches||!staged.buffer_count||
       staged.chain_count!=8u) {
        output.issue=FSwin720TensorIssue::IncorrectCoverage;
        return false;
    }
    staged.includes_gpu_weights=false;
    staged.gpu_executable=false;
    output=staged;
    return true;
}
} // namespace Eden::Graphics::DlssNrMin
