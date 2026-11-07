// SPDX-License-Identifier: MIT
// Synthetic NRMODEL1 only. Exact canonical FP16 weight lengths, names,
// Original and Compact postblocks; fail-atomic for NaN and truncation.
#include "video_core/renderer_vulkan/nr_rdna2_image_feature_weight_loader.h"
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
void Put32(std::vector<std::uint8_t>& o,std::uint32_t n){
    for(unsigned i=0u;i<4u;++i)o.push_back(std::uint8_t(n>>(8u*i)));
}
void Put64(std::vector<std::uint8_t>& o,std::uint64_t n){
    for(unsigned i=0u;i<8u;++i)o.push_back(std::uint8_t(n>>(8u*i)));
}
void Write64(std::vector<std::uint8_t>& o,std::size_t at,std::uint64_t n){
    for(unsigned i=0u;i<8u;++i)o[at+i]=std::uint8_t(n>>(8u*i));
}
void Save(const std::filesystem::path& path,const std::vector<Entry>& entries){
    std::vector<std::uint8_t> data{'N','R','M','O','D','E','L','1'};
    Put32(data,static_cast<std::uint32_t>(entries.size()));Put32(data,0u);
    std::vector<std::size_t> headers;
    for(const auto& e:entries){
        Put32(data,static_cast<std::uint32_t>(e.name.size()));
        data.insert(data.end(),e.name.begin(),e.name.end());
        headers.push_back(data.size());
        Put64(data,0u);Put64(data,e.bytes.size());
    }
    for(std::size_t i=0;i<entries.size();++i){
        data.resize((data.size()+255u)&~std::size_t(255u),0u);
        Write64(data,headers[i],data.size());
        data.insert(data.end(),entries[i].bytes.begin(),entries[i].bytes.end());
    }
    std::ofstream f(path,std::ios::binary|std::ios::trunc);
    assert(f.good());
    f.write(reinterpret_cast<const char*>(data.data()),
            static_cast<std::streamsize>(data.size()));
    assert(f.good());
}
}
int main(){
    const auto file=std::filesystem::temp_directory_path()/
        ("encore-nr-feature-"+std::to_string(
            std::chrono::steady_clock::now().time_since_epoch().count())+
         ".nrmodel1");
    const auto half=[](){
        std::vector<std::uint8_t> data(1024u);
        for(std::size_t i=0;i<512u;++i)
            data[2u*i+1u]=0x3cu;
        return data;
    };
    std::vector<Entry> records{
        {"unpacked-preblock/block0.layer0.layer.input_lift.bin",half()},
        {"unpacked-postblock/block70.layer0.layer.out_project.bin",half()},
        {"unpacked-postblock/block30.layer0.layer.out_project.bin",half()}};
    Save(file,records);
    NeuralModelFile model;
    assert(model.Open(file.string()));
    std::vector<std::uint8_t> result;
    assert(PrepareImageFeatureWeights(
        model,ImageFeatureDirection::Lift,0u,result));
    assert(result==records[0].bytes);
    assert(PrepareImageFeatureWeights(
        model,ImageFeatureDirection::Project,70u,result));
    assert(result==records[1].bytes);
    assert(PrepareImageFeatureWeights(
        model,ImageFeatureDirection::Project,30u,result));
    assert(result==records[2].bytes);
    assert(!PrepareImageFeatureWeights(
        model,ImageFeatureDirection::Project,71u,result));
    assert(result.empty());
    assert(!PrepareImageFeatureWeights(
        model,ImageFeatureDirection::Lift,30u,result));
    assert(result.empty());
    records[0].bytes[1u]=0x7cu; // infinity FP16 invalid
    Save(file,records);
    assert(model.Open(file.string()));
    assert(!PrepareImageFeatureWeights(
        model,ImageFeatureDirection::Lift,0u,result));
    assert(result.empty());
    records[0].bytes[1u]=0x3cu;
    records[1].bytes.resize(1022u);
    Save(file,records);
    assert(model.Open(file.string()));
    assert(!PrepareImageFeatureWeights(
        model,ImageFeatureDirection::Project,70u,result));
    assert(result.empty());
    std::filesystem::remove(file);
}
