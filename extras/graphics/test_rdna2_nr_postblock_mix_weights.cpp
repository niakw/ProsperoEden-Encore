// SPDX-License-Identifier: MIT
// Synthetic NRMODEL1 only: both learned gains must be finite and complete.
#include "video_core/renderer_vulkan/nr_rdna2_postblock_mix_weight_loader.h"
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
struct Entry{std::string name;std::vector<std::uint8_t> bytes;};
void Put32(std::vector<std::uint8_t>& v,std::uint32_t n){
    for(unsigned i=0;i<4u;++i)v.push_back(std::uint8_t(n>>(8u*i)));
}
void Put64(std::vector<std::uint8_t>& v,std::uint64_t n){
    for(unsigned i=0;i<8u;++i)v.push_back(std::uint8_t(n>>(8u*i)));
}
void Write64(std::vector<std::uint8_t>& v,std::size_t at,std::uint64_t n){
    for(unsigned i=0;i<8u;++i)v[at+i]=std::uint8_t(n>>(8u*i));
}
void Save(const std::filesystem::path& path,const std::vector<Entry>& entries){
    std::vector<std::uint8_t> data{'N','R','M','O','D','E','L','1'};
    Put32(data,static_cast<std::uint32_t>(entries.size()));Put32(data,0u);
    std::vector<std::size_t> positions;
    for(const auto& entry:entries){
        Put32(data,static_cast<std::uint32_t>(entry.name.size()));
        data.insert(data.end(),entry.name.begin(),entry.name.end());
        positions.push_back(data.size());
        Put64(data,0u);Put64(data,entry.bytes.size());
    }
    for(std::size_t i=0;i<entries.size();++i){
        data.resize((data.size()+255u)&~std::size_t(255u),0u);
        Write64(data,positions[i],data.size());
        data.insert(data.end(),entries[i].bytes.begin(),entries[i].bytes.end());
    }
    std::ofstream file(path,std::ios::binary|std::ios::trunc);
    assert(file.good());
    file.write(reinterpret_cast<const char*>(data.data()),
               static_cast<std::streamsize>(data.size()));
    assert(file.good());
}
}
int main(){
    const auto path=std::filesystem::temp_directory_path()/
        ("r09-postmix-"+std::to_string(
            std::chrono::steady_clock::now().time_since_epoch().count())+
         ".nrmodel1");
    std::vector<std::uint8_t> half(64u,0u);
    for(std::size_t i=1u;i<half.size();i+=2u)half[i]=0x3cu;
    std::vector<Entry> entries;
    for(const auto block:{70u,30u})
        for(const char* suffix:{"main_gain.bin","skip_gain.bin"})
            entries.push_back({"unpacked-postblock/block"+
                std::to_string(block)+".layer0.layer."+suffix,half});
    Save(path,entries);
    NeuralModelFile model;
    assert(model.Open(path.string()));
    std::vector<std::uint8_t> result;
    for(const auto block:{70u,30u}){
        assert(PreparePostblockMixGains(model,block,result));
        assert(result.size()==128u);
        for(std::size_t i=0;i<result.size();++i)
            assert(result[i]==half[i%64u]);
    }
    assert(!PreparePostblockMixGains(model,71u,result));
    assert(result.empty());
    entries[1].bytes[1u]=0x7cu; // FP16 infinity, must refuse both gains.
    Save(path,entries);
    assert(model.Open(path.string()));
    assert(!PreparePostblockMixGains(model,70u,result));
    assert(result.empty());
    entries[1].bytes[1u]=0x3cu;
    entries[0].bytes.resize(62u); // one gain incomplete, fail-atomic.
    Save(path,entries);
    assert(model.Open(path.string()));
    assert(!PreparePostblockMixGains(model,70u,result));
    assert(result.empty());
    std::filesystem::remove(path);
}
