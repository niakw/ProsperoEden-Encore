// SPDX-License-Identifier: MIT
// NRMODEL1 parser unit tests: valid model index, corruptions, path isolation.
#include <cassert>
#include <cstdint>
#include <string>
#include <vector>
#include "video_core/renderer_vulkan/nr_rdna2_model_pack.h"
using namespace Eden::Graphics::NeuralRDNA2;
static void u32(std::vector<std::uint8_t>& v,std::uint32_t x){
    for(unsigned i=0;i<4u;++i)v.push_back(std::uint8_t(x>>(8u*i)));
}
static void u64(std::vector<std::uint8_t>& v,std::uint64_t x){
    for(unsigned i=0;i<8u;++i)v.push_back(std::uint8_t(x>>(8u*i)));
}
static void entry(std::vector<std::uint8_t>& v,
    const std::string& name,std::uint64_t off,std::uint64_t size){
    u32(v,static_cast<std::uint32_t>(name.size()));
    for(char c:name)v.push_back(std::uint8_t(c));
    u64(v,off);u64(v,size);
}
static std::vector<std::uint8_t> model(const std::string& one,
    const std::string& two,std::uint64_t first_off=256u,
    std::uint64_t first_size=8u,std::uint64_t second_off=512u){
    std::vector<std::uint8_t> b{'N','R','M','O','D','E','L','1'};
    u32(b,2u);u32(b,0u);
    entry(b,one,first_off,first_size);
    entry(b,two,second_off,7u);
    return b;
}
int main(){
    std::vector<NeuralModelEntry> entries;
    auto header=model("fswin/layer0.bin","vit/layer1.bin");
    assert(ParseNeuralModelIndex(header,1024u,entries)==NeuralModelError::Ok);
    assert(entries.size()==2u);
    assert(entries[0].name=="fswin/layer0.bin");
    assert(entries[0].offset==256u&&entries[0].size==8u);
    assert(entries[1].offset==512u&&entries[1].size==7u);
    assert(!ValidNeuralWeightName("../escape"));
    assert(!ValidNeuralWeightName("/absolute"));
    assert(!ValidNeuralWeightName("folder/../escape"));
    assert(!ValidNeuralWeightName("folder\\escape"));
    assert(!ValidNeuralWeightName("folder//escape"));
    assert(ValidNeuralWeightName("model/layer.0.bin"));

    const auto bad=[&](const std::vector<std::uint8_t>& h,
                       NeuralModelError expected,std::uint64_t length=1024u) {
        assert(ParseNeuralModelIndex(h,length,entries)==expected);
        assert(entries.empty());
    };
    auto v=header;v[0]='X';bad(v,NeuralModelError::BadMagic);
    v=header;v[12]=1u;bad(v,NeuralModelError::BadHeader);
    v=header;v[8]=0u;bad(v,NeuralModelError::BadCount);
    v=header;v.resize(25);bad(v,NeuralModelError::TruncatedIndex);
    bad(model("../escape","vit/layer1.bin"),NeuralModelError::UnsafePath);
    bad(model("same","same"),NeuralModelError::DuplicateName);
    bad(model("first","second",257u),NeuralModelError::MisalignedData);
    bad(model("first","second",256u,300u,512u),NeuralModelError::Overlap);
    bad(model("first","second",256u,1024u),NeuralModelError::OutOfRange);
    bad(header,NeuralModelError::OutOfRange,128u);
}
