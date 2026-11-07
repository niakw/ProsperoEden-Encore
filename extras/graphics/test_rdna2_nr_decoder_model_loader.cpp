// SPDX-License-Identifier: MIT
// Generated NRMODEL1 only: matrix [512,1024], finite FP16[512], fail-atomic.
#include "video_core/renderer_vulkan/nr_rdna2_decoder_model_loader.h"
#include <cassert>
#include <chrono>
#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <string>
#include <vector>
using namespace Eden::Graphics::NeuralRDNA2;
namespace {
struct Entry{std::string name;std::vector<std::uint8_t> body;};
void U32(std::vector<std::uint8_t>& d,std::uint32_t n){
    for(unsigned k=0u;k<4u;++k)d.push_back(std::uint8_t(n>>(k*8u)));
}
void U64(std::vector<std::uint8_t>& d,std::uint64_t n){
    for(unsigned k=0u;k<8u;++k)d.push_back(std::uint8_t(n>>(k*8u)));
}
void PatchU64(std::vector<std::uint8_t>& d,std::size_t at,
              std::uint64_t n){
    for(unsigned k=0u;k<8u;++k)d[at+k]=std::uint8_t(n>>(k*8u));
}
void Save(const std::filesystem::path& file,const std::vector<Entry>& entries){
    std::vector<std::uint8_t> bytes{'N','R','M','O','D','E','L','1'};
    U32(bytes,std::uint32_t(entries.size()));U32(bytes,0u);
    std::vector<std::size_t> slots;
    for(const auto& entry:entries){
        U32(bytes,std::uint32_t(entry.name.size()));
        bytes.insert(bytes.end(),entry.name.begin(),entry.name.end());
        slots.push_back(bytes.size());
        U64(bytes,0u);U64(bytes,entry.body.size());
    }
    for(std::size_t i=0;i<entries.size();++i){
        bytes.resize((bytes.size()+255u)&~std::size_t(255u),0u);
        PatchU64(bytes,slots[i],bytes.size());
        bytes.insert(bytes.end(),entries[i].body.begin(),entries[i].body.end());
    }
    std::ofstream f(file,std::ios::binary|std::ios::trunc);
    assert(f.good());
    f.write(reinterpret_cast<const char*>(bytes.data()),
            static_cast<std::streamsize>(bytes.size()));
    assert(f.good());
}
}
int main(){
    const auto path=std::filesystem::temp_directory_path()/
        ("encore-decoder-model-"+std::to_string(
            std::chrono::steady_clock::now().time_since_epoch().count())+
         ".nrmodel1");
    const std::string prefix="unpacked-splitswin/block39.layer0.layer";
    std::vector<Entry> data{
        {prefix+".weight.bin",std::vector<std::uint8_t>(512u*1024u,0x38u)},
        {prefix+".skip_weight.bin",std::vector<std::uint8_t>(1024u,0u)}};
    for(std::size_t i=0;i<512u;++i)data[1].body[2u*i+1u]=0x3cu;
    data[0].body[0u]=0u;
    Save(path,data);
    NeuralModelFile model;
    assert(model.Open(path.string()));
    NativeDecoderModelWeights out;
    assert(PrepareNativeDecoderModelWeights(model,39u,out));
    assert(out.matrix.size()==512u*1024u);
    assert(out.matrix[0]==0x80u&&out.matrix[1]==0x38u);
    assert(out.skip_gain.size()==1024u);
    assert(out.skip_gain[0]==0u&&out.skip_gain[1]==0x3cu);
    assert(!PrepareNativeDecoderModelWeights(model,19u,out));
    assert(out.matrix.empty()&&out.skip_gain.empty());
    assert(!PrepareNativeDecoderModelWeights(model,512u,out));
    assert(out.matrix.empty());
    data[0].body[100u]=0x7fu;Save(path,data);
    assert(model.Open(path.string()));
    assert(!PrepareNativeDecoderModelWeights(model,39u,out));
    assert(out.matrix.empty()&&out.skip_gain.empty());
    data[0].body[100u]=0x38u;
    data[1].body[1u]=0x7cu; // FP16 +inf is rejected
    Save(path,data);assert(model.Open(path.string()));
    assert(!PrepareNativeDecoderModelWeights(model,39u,out));
    assert(out.matrix.empty()&&out.skip_gain.empty());
    data[1].body[1u]=0x3cu;
    data[1].body.pop_back();Save(path,data);
    assert(model.Open(path.string()));
    assert(!PrepareNativeDecoderModelWeights(model,39u,out));
    assert(out.matrix.empty()&&out.skip_gain.empty());
    std::filesystem::remove(path);
}
