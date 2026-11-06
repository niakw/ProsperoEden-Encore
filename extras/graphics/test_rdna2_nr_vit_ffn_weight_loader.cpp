// SPDX-License-Identifier: MIT
// Entire local NRMODEL1 FFN/Proj model: no trained weights distributed.
#include "video_core/renderer_vulkan/nr_rdna2_vit_projection_layer_weight_loader.h"
#include <cassert>
#include <chrono>
#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <span>
#include <string>
#include <vector>
using namespace Eden::Graphics::NeuralRDNA2;
namespace {
void Put32(std::vector<std::uint8_t>& out,std::uint32_t n){
    for(unsigned j=0;j<4u;++j)out.push_back(std::uint8_t(n>>(j*8u)));
}
void Put64(std::vector<std::uint8_t>& out,std::uint64_t n){
    for(unsigned j=0;j<8u;++j)out.push_back(std::uint8_t(n>>(j*8u)));
}
void Write64(std::vector<std::uint8_t>& out,std::size_t at,
             std::uint64_t n){
    for(unsigned j=0;j<8u;++j)out[at+j]=std::uint8_t(n>>(j*8u));
}
struct Entry{
    std::string name;
    std::vector<std::uint8_t> bytes;
};
std::vector<std::uint8_t> Pack(const std::vector<Entry>& entries){
    std::vector<std::uint8_t> out{'N','R','M','O','D','E','L','1'};
    Put32(out,static_cast<std::uint32_t>(entries.size()));
    Put32(out,0u);
    std::vector<std::size_t> positions;
    for(const auto& e:entries){
        Put32(out,static_cast<std::uint32_t>(e.name.size()));
        out.insert(out.end(),e.name.begin(),e.name.end());
        positions.push_back(out.size());
        Put64(out,0u);Put64(out,e.bytes.size());
    }
    for(std::size_t i=0;i<entries.size();++i){
        out.resize((out.size()+255u)&~std::size_t(255u),0u);
        Write64(out,positions[i],out.size());
        out.insert(out.end(),entries[i].bytes.begin(),entries[i].bytes.end());
    }
    return out;
}
void Save(const std::filesystem::path& path,
          const std::vector<Entry>& entries){
    const auto bytes=Pack(entries);
    std::ofstream file(path,std::ios::binary|std::ios::trunc);
    assert(file.good());
    file.write(reinterpret_cast<const char*>(bytes.data()),
               static_cast<std::streamsize>(bytes.size()));
    assert(file.good());
}
std::vector<Entry> Fixture(){
    const std::string base="unpacked-vit/block31.layer";
    std::vector<std::uint8_t> expand(4096u*1024u,0x38u);
    std::vector<std::uint8_t> contract(1024u*4096u,0x40u);
    std::vector<std::uint8_t> projection(1024u*1024u,0x48u);
    std::vector<std::uint8_t> gain(2048u,0u);
    for(std::size_t i=0;i<1024u;++i)gain[2u*i+1u]=0x3cu;
    expand[0]=0u;
    return {
        {base+"0.layer.weight.bin",std::move(expand)},
        {base+"1.layer.weight.bin",std::move(contract)},
        {base+"1.layer.skip_weight.bin",gain},
        {base+"4.layer.weight.bin",std::move(projection)},
        {base+"4.layer.skip_weight.bin",gain}};
}
}
int main(){
    auto fixture=Fixture();
    const auto file=std::filesystem::temp_directory_path()/
        ("encore-vitffn-"+std::to_string(
            std::chrono::steady_clock::now().time_since_epoch().count())+
         ".nrmodel1");
    Save(file,fixture);
    NeuralModelFile model;
    assert(model.Open(file.string()));
    VitFfnBlockWeights whole;
    assert(PrepareVitFfnBlockWeights(model,31u,whole));
    assert(whole.expansion.size()==4096u*1024u);
    assert(whole.contraction.size()==1024u*4096u);
    assert(whole.projection.size()==1024u*1024u);
    assert(whole.contract_gain_f16.size()==2048u);
    assert(whole.projection_gain_f16.size()==2048u);
    assert(whole.expansion[0]==0x80u);
    assert(whole.expansion[1]==0x38u);
    assert(whole.contraction[0]==0x40u);
    assert(whole.projection[0]==0x48u);
    assert(whole.contract_gain_f16[1]==0x3cu);
    VitProjectionLayerWeights layer;
    assert(PrepareVitProjectionLayerWeights(
        model,31u,VitProjectionKind::Expand,layer));
    assert(layer.matrix.size()==4096u*1024u);
    assert(layer.gain_f16.empty());
    assert(PrepareVitProjectionLayerWeights(
        model,31u,VitProjectionKind::Contract,layer));
    assert(layer.matrix.size()==1024u*4096u);
    assert(layer.gain_f16.size()==2048u);
    assert(PrepareVitProjectionLayerWeights(
        model,31u,VitProjectionKind::ResidualProjection,layer));
    assert(layer.matrix.size()==1024u*1024u);
    assert(layer.gain_f16.size()==2048u);
    assert(!PrepareVitProjectionLayerWeights(
        model,512u,VitProjectionKind::Expand,layer));
    assert(layer.matrix.empty()&&layer.gain_f16.empty());
    // Invalid E4M3 source is fatal: never discard a layer silently.
    fixture[0].bytes[200u]=0x7fu;
    Save(file,fixture);assert(model.Open(file.string()));
    assert(!PrepareVitFfnBlockWeights(model,31u,whole));
    assert(whole.expansion.empty()&&whole.contraction.empty());
    fixture[0].bytes[200u]=0x38u;
    fixture[3].bytes.resize(1024u*1024u-1u);
    Save(file,fixture);assert(model.Open(file.string()));
    assert(!PrepareVitFfnBlockWeights(model,31u,whole));
    assert(whole.expansion.empty()&&whole.contraction.empty());
    fixture[3].bytes.resize(1024u*1024u,0x48u);
    fixture[2].bytes[0]=0u;fixture[2].bytes[1]=0x7eu;
    Save(file,fixture);assert(model.Open(file.string()));
    assert(!PrepareVitFfnBlockWeights(model,31u,whole));
    assert(whole.expansion.empty()&&whole.contraction.empty());
    std::filesystem::remove(file);
}
