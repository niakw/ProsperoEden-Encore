// SPDX-License-Identifier: MIT
// Research-only Fermi2D 3D slice-copy selection model, not renderer-linked.
#include <algorithm>
#include <array>
#include <cassert>
#include <cstdint>
#include <iostream>
#include <limits>
#include <optional>
#include <stdexcept>
#include <vector>
using u32 = std::uint32_t;
using u64 = std::uint64_t;
using s32 = std::int32_t;
enum class Layout { BlockLinear, Pitch };
enum class Op { SrcCopy=3, Blend=2, Rop=4 };
enum class Filter { Point=0, Bilinear=1 };
struct Surface { u64 address{}; u32 width{16}, height{16}, depth{16}, layer{}; u32 format{8}; Layout layout{Layout::BlockLinear}; };
struct Copy { s32 sx0{},sy0{},dx0{},dy0{},sx1{16},sy1{16},dx1{16},dy1{16}; Op op{Op::SrcCopy}; Filter filter{Filter::Point}; };
struct Subresource { u32 level{},layer{}; };
struct CachedImage { u32 id{}; u64 address{}; u64 mapped_bytes{1ULL<<20}; u32 width{16},height{16},depth{16},format{8}; bool volume{true}; std::vector<u32> slice_offsets{0,1024,2048,3072}; std::vector<Subresource> slice_subresources{{0,0},{0,1},{0,2},{1,3}}; };
struct Slice { u32 id{}; u32 depth{}; };
struct Decision { bool accepted{}; Slice src{},dst{}; };
// Policy transcribed from Lichii nx2@879b616b; no real GPU allocation.
Decision UpstreamModel(const Surface& dst,const Surface& src,const Copy& copy,const std::vector<CachedImage>& images){
    const auto is_volume=[](const Surface& s){return s.depth>1 && s.layout==Layout::BlockLinear && s.layer==0;};
    const bool whole = copy.sx0==0 && copy.sy0==0 && copy.dx0==0 && copy.dy0==0 &&
        copy.sx1==static_cast<s32>(src.width) && copy.sy1==static_cast<s32>(src.height) &&
        copy.dx1==static_cast<s32>(dst.width) && copy.dy1==static_cast<s32>(dst.height);
    if(!is_volume(src)||!is_volume(dst)||!whole||src.format!=dst.format||src.width!=dst.width||src.height!=dst.height)return {};
    const auto find_slice=[&](const Surface& surface)->std::optional<Slice>{
        for(const auto& image:images){
            if(surface.address<image.address || surface.address-image.address>=image.mapped_bytes)continue;
            if(!image.volume || image.format!=surface.format || image.width!=surface.width || image.height!=surface.height || image.depth!=surface.depth)continue;
            // Upstream uses static_cast<u32> here: provenance of the actual
            // mapped image region must bound the GPU address before narrowing.
            const auto offset=static_cast<u32>(surface.address-image.address);
            auto it=std::find(image.slice_offsets.begin(),image.slice_offsets.end(),offset);
            if(it==image.slice_offsets.end())continue;
            const auto index=static_cast<std::size_t>(it-image.slice_offsets.begin());
            if(index>=image.slice_subresources.size() || image.slice_subresources[index].level!=0)continue;
            return Slice{image.id,image.slice_subresources[index].layer};
        }
        return std::nullopt;
    };
    const auto source=find_slice(src), target=find_slice(dst);
    if(!source || !target || source->id==target->id)return {};
    return {true,*source,*target};
}
// Fail-closed proposed *additional* gate; never assume source-blit semantics
// for blend/ROP, bilinear sampling, or malformed/cross-volume metadata.
Decision StrictCandidate(const Surface& dst,const Surface& src,const Copy& copy,const std::vector<CachedImage>& images){
    if(copy.op!=Op::SrcCopy || copy.filter!=Filter::Point)return {};
    if(src.width==0||src.height==0||dst.width==0||dst.height==0||src.depth==0||dst.depth==0)return {};
    for(const auto& image:images){
        if(image.slice_offsets.size()!=image.slice_subresources.size())return {};
        if(image.mapped_bytes>std::numeric_limits<u32>::max())return {};
        if(image.volume){
            for(const auto& sub:image.slice_subresources)if(sub.layer>=image.depth)return {};
        }
    }
    return UpstreamModel(dst,src,copy,images);
}
int main(){
    int n=0;const auto ck=[&](bool ok){++n;if(!ok)throw std::runtime_error("3D volume slice test #"+std::to_string(n));};
    Surface src{0x100000},dst{0x200000};
    Copy c{};
    std::vector<CachedImage> imgs{{1,src.address},{2,dst.address}};
    auto test=[&](bool expected){const bool actual=UpstreamModel(dst,src,c,imgs).accepted;ck(actual==expected);};
    test(true);
    auto d=UpstreamModel(dst,src,c,imgs);ck(d.src.id==1&&d.dst.id==2&&d.src.depth==0&&d.dst.depth==0);
    src.address+=1024;dst.address+=2048;d=UpstreamModel(dst,src,c,imgs);ck(d.accepted&&d.src.depth==1&&d.dst.depth==2);
    src.address=0x100000;dst.address=0x200000;
    src.depth=1;test(false);src.depth=16;
    dst.depth=1;test(false);dst.depth=16;
    src.layout=Layout::Pitch;test(false);src.layout=Layout::BlockLinear;
    dst.layout=Layout::Pitch;test(false);dst.layout=Layout::BlockLinear;
    src.layer=1;test(false);src.layer=0;
    dst.layer=1;test(false);dst.layer=0;
    src.format=9;test(false);src.format=8;
    dst.format=9;test(false);dst.format=8;
    src.width=17;test(false);src.width=16;
    dst.width=17;test(false);dst.width=16;
    src.height=17;test(false);src.height=16;
    dst.height=17;test(false);dst.height=16;
    for(s32* field:{&c.sx0,&c.sy0,&c.dx0,&c.dy0}){*field=1;test(false);*field=0;}
    for(s32* field:{&c.sx1,&c.sy1,&c.dx1,&c.dy1}){*field=15;test(false);*field=16;}
    src.address+=3072;test(false);src.address-=3072; // mip != 0
    dst.address+=3072;test(false);dst.address-=3072;
    imgs[0].volume=false;test(false);imgs[0].volume=true;
    imgs[1].volume=false;test(false);imgs[1].volume=true;
    imgs[0].format=99;test(false);imgs[0].format=8;
    imgs[1].format=99;test(false);imgs[1].format=8;
    imgs[0].width=17;test(false);imgs[0].width=16;
    imgs[1].height=18;test(false);imgs[1].height=16;
    imgs[0].depth=15;test(false);imgs[0].depth=16;
    imgs[1].depth=15;test(false);imgs[1].depth=16;
    imgs[0].mapped_bytes=0;test(false);imgs[0].mapped_bytes=1ULL<<20;
    imgs[1].mapped_bytes=0;test(false);imgs[1].mapped_bytes=1ULL<<20;
    auto backup=imgs;imgs.pop_back();test(false);imgs=backup;
    imgs={imgs[0]};dst.address=src.address+1024;test(false); // same cached image forbidden
    imgs=backup;dst.address=0x200000;
    c.op=Op::Blend;test(true);ck(!StrictCandidate(dst,src,c,imgs).accepted);c.op=Op::Rop;test(true);ck(!StrictCandidate(dst,src,c,imgs).accepted);c.op=Op::SrcCopy;
    c.filter=Filter::Bilinear;test(true);ck(!StrictCandidate(dst,src,c,imgs).accepted);c.filter=Filter::Point;
    ck(StrictCandidate(dst,src,c,imgs).accepted);
    imgs[0].slice_subresources[0].layer=99;test(true);ck(!StrictCandidate(dst,src,c,imgs).accepted);imgs=backup;
    imgs[0].mapped_bytes=u64{1}<<32;test(true);ck(!StrictCandidate(dst,src,c,imgs).accepted);imgs=backup;
    // The same image's destination volume is not supported by upstream.
    dst.address=src.address;test(false);dst.address=0x200000;
    ck(StrictCandidate(dst,src,c,imgs).accepted);
    std::cout<<"PASS: "<<n<<" Fermi2D 3D volume slice source-policy host checks; Blend/ROP/Bilinear bypass recorded\n";
}
