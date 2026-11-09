// SPDX-License-Identifier: MIT
// Synthetic NRMODEL1 ViT QKV importer; no proprietary weights bundled.
#include "video_core/renderer_vulkan/nr_rdna2_vit_qkv_weight_loader.h"
#include "video_core/renderer_vulkan/nr_rdna2_split_ffwd_weight_loader.h"
#include <algorithm>
#include <array>
#include <bit>
#include <cassert>
#include <chrono>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <span>
#include <string>
#include <utility>
#include <vector>
using namespace Eden::Graphics::NeuralRDNA2;
namespace {
void Push32(std::vector<std::uint8_t>& b,std::uint32_t value){
    for(unsigned j=0;j<4u;++j)b.push_back(std::uint8_t(value>>(8u*j)));
}
void Push64(std::vector<std::uint8_t>& b,std::uint64_t value){
    for(unsigned j=0;j<8u;++j)b.push_back(std::uint8_t(value>>(8u*j)));
}
void Write64(std::vector<std::uint8_t>& b,std::size_t position,std::uint64_t v){
    for(unsigned j=0;j<8u;++j)b[position+j]=std::uint8_t(v>>(8u*j));
}
struct Entry{
    std::string name;
    std::vector<std::uint8_t> content;
};
std::vector<std::uint8_t> Pack(const std::vector<Entry>& entries){
    std::vector<std::uint8_t> b{'N','R','M','O','D','E','L','1'};
    Push32(b,static_cast<std::uint32_t>(entries.size()));
    Push32(b,0u);
    std::vector<std::size_t> offset_positions;
    for(const auto& entry:entries){
        Push32(b,static_cast<std::uint32_t>(entry.name.size()));
        b.insert(b.end(),entry.name.begin(),entry.name.end());
        offset_positions.push_back(b.size());
        Push64(b,0u);
        Push64(b,entry.content.size());
    }
    for(std::size_t i=0;i<entries.size();++i){
        b.resize((b.size()+255u)&~std::size_t(255u),0u);
        Write64(b,offset_positions[i],b.size());
        b.insert(b.end(),entries[i].content.begin(),entries[i].content.end());
    }
    return b;
}
std::vector<Entry> Fixture(){
    constexpr auto prefix="unpacked/block31.layer2.layer";
    std::vector<std::uint8_t> header(128u);
    for(std::size_t i=0;i<32u;++i){
        const auto word=std::bit_cast<std::uint32_t>(1.0f+float(i)/64.f);
        for(unsigned j=0u;j<4u;++j)
            header[4u*i+j]=std::uint8_t(word>>(8u*j));
    }
    std::vector<std::uint8_t> q(1024u*1024u,0x38u);
    std::vector<std::uint8_t> k(1024u*1024u,0x40u);
    std::vector<std::uint8_t> v(1024u*1024u,0x48u);
    q[0]=0u; // exactly the upstream +0 -> -0 requantization
    return {
        {std::string(prefix)+".header.bin",std::move(header)},
        {std::string(prefix)+".q.bin",std::move(q)},
        {std::string(prefix)+".k.bin",std::move(k)},
        {std::string(prefix)+".v.bin",std::move(v)}};
}
void WriteFile(const std::filesystem::path& name,
               std::span<const std::uint8_t> bytes){
    std::ofstream file(name,std::ios::binary|std::ios::trunc);
    assert(file.good());
    file.write(reinterpret_cast<const char*>(bytes.data()),
               static_cast<std::streamsize>(bytes.size()));
    assert(file.good());
}
}
int main(){
    std::array<float,32> values{};
    auto fixture=Fixture();
    assert(DecodeViTQkvTemperatures(fixture[0].content,values));
    assert(values[0]==1.f);
    assert(values[31]==1.f+31.f/64.f);
    assert(!DecodeViTQkvTemperatures(
        std::span<const std::uint8_t>{
            fixture[0].content.data(),127u},values));
    for(float v:values)assert(v==0.f);
    const auto name=std::filesystem::temp_directory_path()/
        ("encore-vitqkv-host-"+std::to_string(
            std::chrono::steady_clock::now().time_since_epoch().count())+
            ".nrmodel1");
    const auto write=[&](const std::vector<Entry>& entries){
        const auto data=Pack(entries);
        WriteFile(name,data);
    };
    NeuralModelFile model;
    ViTQkvModelPayload output;
    write(fixture);
    assert(model.Open(name.string()));
    assert(PrepareViTQkvModelWeights(
        model,"unpacked/block31.layer2.layer",output));
    assert(output.row_major_qkv.size()==3u*1024u*1024u);
    assert(output.row_major_qkv[0]==0x80u);
    assert(output.row_major_qkv[1]==0x38u);
    assert(output.row_major_qkv[1024u*1024u]==0x40u);
    assert(output.row_major_qkv[2u*1024u*1024u]==0x48u);
    assert(output.temperatures[31]==1.f+31.f/64.f);
    assert(!PrepareViTQkvModelWeights(model,"../unsafe",output));
    assert(output.row_major_qkv.empty());
    // The model index may be valid while a learned temperature is NaN.
    auto broken=fixture;
    const std::uint32_t nan=0x7fc00000u;
    for(unsigned j=0u;j<4u;++j)
        broken[0].content[j]=std::uint8_t(nan>>(8u*j));
    write(broken);
    assert(model.Open(name.string()));
    assert(!PrepareViTQkvModelWeights(
        model,"unpacked/block31.layer2.layer",output));
    assert(output.row_major_qkv.empty());
    // Every learned E4M3 byte must be finite.
    broken=fixture;
    broken[1].content[100u]=0x7fu;
    write(broken);
    assert(model.Open(name.string()));
    assert(!PrepareViTQkvModelWeights(
        model,"unpacked/block31.layer2.layer",output));
    assert(output.row_major_qkv.empty());
    // A truncated/missing K tensor is never accepted.
    broken=fixture;
    broken[2].content.resize(1024u*1024u-1u);
    write(broken);
    assert(model.Open(name.string()));
    assert(!PrepareViTQkvModelWeights(
        model,"unpacked/block31.layer2.layer",output));
    assert(output.row_major_qkv.empty());
    // Real Original packs store 16 FFWD pairs and eight ViT QKV groups
    // as raw inventory records. Exercise BOTH native fallbacks with a
    // synthetic, non-proprietary 2-record NRMODEL1 pack.
    auto raw_head=fixture[0].content;
    std::vector<std::uint8_t> raw_qkv(128u+3u*1024u*1024u);
    std::copy(raw_head.begin(),raw_head.end(),raw_qkv.begin());
    for(std::uint32_t tile=0;tile<1024u;++tile)
        for(std::uint32_t part=0;part<3u;++part){
            const std::uint8_t value=part==0u?0x38u:
                                     part==1u?0x40u:0x48u;
            std::fill_n(raw_qkv.begin()+128u+
                (3u*tile+part)*1024u,1024u,value);
        }
    // Probe a non-uniform K/row placement in the original interleaving.
    constexpr std::uint32_t row=5u,k=37u,which=1u;
    const std::uint32_t b=(k&1u)|(((k>>1u)&1u)<<4u)|
        (((k>>2u)&1u)<<5u)|(((k>>3u)&1u)<<1u)|
        (((k>>4u)&1u)<<2u)|((row&1u)<<6u)|
        (((row>>1u)&1u)<<7u)|(((row>>2u)&1u)<<8u)|
        (((row>>3u)&1u)<<3u)|(((row>>4u)&1u)<<9u);
    const std::uint32_t tile=(row>>5u)|((k>>5u)<<5u);
    raw_qkv[128u+(3u*tile+which)*1024u+b]=0x18u;
    std::vector<Entry> inventory{
        {"inventory/weights/block23.layer0.layer.bin",
            std::vector<std::uint8_t>(524288u,0x80u)},
        {"inventory/weights/block31.layer2.layer.bin",
            std::move(raw_qkv)}};
    write(inventory);
    assert(model.Open(name.string()));
    SplitFFWDWeights split{};
    assert(PrepareSplitFFWDWeights(
        model,"unpacked-splitswin/block23.layer0.layer",split));
    assert(split.w1.size()==262144u&&split.w2.size()==131072u&&
           split.w3.size()==131072u);
    assert(split.w1[0u]==0x80u&&split.w2[0u]==0x80u);
    assert(PrepareViTQkvModelWeights(
        model,"unpacked-vit/block31.layer2.layer",output));
    assert(output.row_major_qkv.size()==3u*1024u*1024u);
    assert(output.row_major_qkv[0u]==0x38u);
    assert(output.row_major_qkv[1024u*1024u]==0x40u);
    assert(output.row_major_qkv[2u*1024u*1024u]==0x48u);
    assert(output.row_major_qkv[
        (std::size_t(which)*1024u+row)*1024u+k]==0x18u);
    assert(output.temperatures[31u]==1.f+31.f/64.f);
    // Partially unpacked, truncated, or unsafe inventory is rejected.
    auto damaged=inventory;
    damaged[0u].content.pop_back();
    write(damaged);
    assert(model.Open(name.string()));
    assert(!PrepareSplitFFWDWeights(
        model,"unpacked-splitswin/block23.layer0.layer",split));
    damaged=inventory;
    damaged[1u].content.pop_back();
    write(damaged);
    assert(model.Open(name.string()));
    assert(!PrepareViTQkvModelWeights(
        model,"unpacked-vit/block31.layer2.layer",output));
    std::filesystem::remove(name);
}
