// SPDX-License-Identifier: MIT
// Regression for an executable full-resolution PREBLOCK C32 allocation.
// The QKV tensors may occupy disjoint portions of the dead expanded
// buffer, but must never overlap each other or live tensor resources.
#include <algorithm>
#include <cassert>
#include <cstdint>
#include "video_core/renderer_vulkan/nr_rdna2_fswin_plan.h"
#include "video_core/renderer_vulkan/nr_rdna2_fswin_qkv_alias_policy.h"
using namespace Eden::Graphics::NeuralRDNA2;
int main() {
    static_assert(CanFSwinQkvReuseExpanded({256u,256u,256u,768u}));
    static_assert(!CanFSwinQkvReuseExpanded({256u,256u,257u,768u}));
    static_assert(!CanFSwinQkvReuseExpanded({256u,257u,256u,1024u}));
    static_assert(!CanFSwinQkvReuseExpanded({257u,256u,256u,1024u}));
    static_assert(!CanFSwinQkvReuseExpanded({0u,256u,256u,1024u}));
    static_assert(!CanFSwinQkvReuseExpanded({256u,256u,256u,767u}));
    FSwinGraph plan{};
    // The real Original plan starts with the 135 x 240 C32 window grid.
    assert(MakeFSwinGraphPlan(32u,135u*240u,plan));
    const auto q=std::max(plan.qkv_storage.q_bytes,
                          plan.attention_storage.q_bytes);
    const auto k=std::max(plan.qkv_storage.k_bytes,
                          plan.attention_storage.k_bytes);
    const auto v=std::max(plan.qkv_storage.v_bytes,
                          plan.attention_storage.v_bytes);
    const auto expanded=plan.dense_storage[0].output_bytes;
    assert(CanFSwinQkvReuseExpanded({q,k,v,expanded}));
    // Seven live tensor allocations plus the 4x expanded tensor.
    const std::uint64_t reused=
        std::max(plan.dense_storage[0].input_bytes,
                 plan.dense_storage[2].residual_bytes)+
        expanded+
        std::max({plan.dense_storage[2].output_bytes,
                  plan.dense_storage[3].residual_bytes,
                  plan.qkv_storage.activation_bytes})+
        std::max(plan.attention_storage.out_bytes,
                 plan.dense_storage[3].input_bytes)+
        plan.dense_storage[3].output_bytes;
    const auto prior=reused+q+k+v;
    assert(prior>(512ull<<20));
    assert(reused<=(512ull<<20));
    assert(expanded<=(256ull<<20));
    assert(q>0u&&k>0u&&v>0u);
}
