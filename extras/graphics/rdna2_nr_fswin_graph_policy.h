// SPDX-License-Identifier: MIT
// Host-validated six-pass RDNA2 FSwin forward path.
// Caller binds all descriptor ranges to the corresponding intermediate output.
#pragma once
#include <array>
#include <cstdint>
#include "rdna2_nr_fswin_dense_policy.h"
#include "rdna2_nr_fswin_qkv_policy.h"
#include "rdna2_nr_window_attention_policy.h"
namespace Eden::Graphics::NeuralRDNA2 {
struct FSwinGraph {
    std::array<FSwinDense,4> dense{};
    std::array<FSwinDenseStorage,4> dense_storage{};
    FSwinQkv qkv{};
    FSwinQkvStorage qkv_storage{};
    WindowAttention attention{};
    AttentionStorage attention_storage{};
};
[[nodiscard]] constexpr bool CanFSwinGraph(const FSwinGraph& p) noexcept {
    const auto C=p.dense[0].channels;
    const auto windows=p.dense[0].windows;
    if(!windows||!C)return false;
    for(std::uint32_t i=0;i<4u;++i){
        // C32 skips the middle group; its contraction consumes 4C.
        if(i==1u&&C==32u){
            if(p.dense[1].windows!=0u||p.dense[1].channels!=0u)
                return false;
            continue;
        }
        if(p.dense[i].stage!=i||p.dense[i].channels!=C||
           p.dense[i].windows!=windows||
           !CanFSwinDense(p.dense[i],p.dense_storage[i]))return false;
    }
    if(p.qkv.windows!=windows||p.qkv.channels!=C||
       p.qkv.heads!=C/32u||
       !CanFSwinQkv(p.qkv,p.qkv_storage))return false;
    if(p.attention.windows!=windows||
       p.attention.heads!=C/32u||
       !CanWindowAttention(p.attention,p.attention_storage))return false;
    // This proves shape, ABI ranges and sequence only.
    // The renderer still has to ensure actual descriptor identity:
    // C32: dense0.out -> dense2.in; C>=64: dense0.out -> dense1.in -> dense2.in;
    // dense2.out -> qkv.in;
    // qkv.{q,k,v} -> attention.{q,k,v};
    // attention.out -> dense3.in; dense2.out -> dense3.residual.
    return true;
}
} // namespace Eden::Graphics::NeuralRDNA2
