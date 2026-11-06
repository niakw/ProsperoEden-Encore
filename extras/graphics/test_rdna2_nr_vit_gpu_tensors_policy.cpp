// SPDX-License-Identifier: MIT
#include "rdna2_nr_vit_gpu_tensors_policy.h"
#include <cassert>
#include <cstdint>
using namespace Eden::Graphics::NeuralRDNA2;
int main() {
    constexpr std::uint64_t MiB=1024u*1024u;
    VitQkvTensorLayout p{};
    assert(BuildVitQkvTensorLayout(2560u,256u*MiB,p));
    assert(p.batch_tokens==2048u);
    assert(p.sizes[0]==2048u*3072u*4u);
    for(unsigned i=1u;i<5u;++i)assert(p.sizes[i]==2560u*1024u);
    assert(p.total_bytes==p.sizes[0]+4ull*2560u*1024u);
    assert(BuildVitQkvTensorLayout(4096u,16u*MiB,p));
    assert(p.batch_tokens>=256u&&p.batch_tokens<2048u);
    assert(p.sizes[0]<=16u*MiB);
    assert(BuildVitQkvTensorLayout(4096u,256u*MiB,p));
    assert(p.batch_tokens==2048u);
    assert(!BuildVitQkvTensorLayout(4097u,256u*MiB,p));
    assert(p.total_bytes==0u);
    assert(!BuildVitQkvTensorLayout(0u,256u*MiB,p));
    assert(!BuildVitQkvTensorLayout(4096u,1024u,p));
    assert(p.total_bytes==0u);
}
