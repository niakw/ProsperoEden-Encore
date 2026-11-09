// SPDX-License-Identifier: MIT
// Import user-owned nvngx_dlssnr.dll weights as a private NRMODEL1 pack.
// The Windows PE is parsed as DATA. Its code is never loaded or executed.
// The proprietary DLL and learned weights are NOT distributed by Eden Encore.
#pragma once
#include "glyph_sha256.h"
#include <algorithm>
#include <array>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <functional>
#include <span>
#include <stdexcept>
#include <string>
#include <string_view>
#include <unordered_map>
#include <utility>
#include <vector>

namespace Eden::NRDllImport {
namespace detail {
struct BadModel final : std::runtime_error {
    using std::runtime_error::runtime_error;
};
struct Bytes {
    const std::uint8_t* ptr{};
    std::size_t size{};
    [[nodiscard]] Bytes Sub(std::size_t off,std::size_t len) const {
        if(off>size||len>size-off)throw BadModel("DLL/resource bounds violated");
        return {ptr+off,len};
    }
    [[nodiscard]] std::uint8_t U8(std::size_t p) const {
        return Sub(p,1).ptr[0];
    }
    [[nodiscard]] std::uint16_t U16(std::size_t p) const {
        auto a=Sub(p,2).ptr;
        return std::uint16_t(a[0])|(std::uint16_t(a[1])<<8);
    }
    [[nodiscard]] std::uint32_t U32(std::size_t p) const {
        return std::uint32_t(U16(p))|(std::uint32_t(U16(p+2))<<16);
    }
    [[nodiscard]] std::uint64_t U64(std::size_t p) const {
        return std::uint64_t(U32(p))|(std::uint64_t(U32(p+4))<<32);
    }
    [[nodiscard]] std::string Text(std::size_t p,std::size_t n) const {
        auto s=Sub(p,n);
        return {reinterpret_cast<const char*>(s.ptr),s.size};
    }
};
[[nodiscard]] inline bool Starts(std::string_view s,std::string_view prefix) {
    return s.starts_with(prefix);
}
[[nodiscard]] inline bool Ends(std::string_view s,std::string_view suffix) {
    return s.ends_with(suffix);
}
// Read only the named RCDATA/WEIGHTS_HT resource. No guessed image offsets.
[[nodiscard]] inline Bytes FindOriginalResource(Bytes file) {
    if(file.size<1024u||file.size>(512u<<20)||file.Text(0,2)!="MZ")
        throw BadModel("not a bounded PE DLL");
    const auto pe=static_cast<std::size_t>(file.U32(0x3c));
    if(file.Text(pe,4)!=std::string_view{"PE\0\0",4}||
       file.U16(pe+4)!=0x8664u)
        throw BadModel("not an AMD64 Windows PE");
    const auto sections=file.U16(pe+6),optional=file.U16(pe+20);
    const auto op=pe+24;
    if(!sections||sections>64u||optional<144u||file.U16(op)!=0x20bu)
        throw BadModel("invalid PE32+ structure");
    (void)file.Sub(op,optional);
    const auto resource_rva=file.U32(op+128);
    const auto resource_length=file.U32(op+132);
    const auto table=op+optional;
    (void)file.Sub(table,std::size_t(sections)*40u);
    const auto translate=[&](std::uint32_t rva,std::uint32_t count){
        for(std::size_t i=0;i<sections;++i){
            const auto o=table+40u*i;
            const auto base=file.U32(o+12),size=file.U32(o+16);
            const auto offset=file.U32(o+20);
            if(rva>=base&&std::uint64_t(rva)-base+count<=size){
                const auto p=std::uint64_t(offset)+rva-base;
                if(p<=file.size&&count<=file.size-p)
                    return static_cast<std::size_t>(p);
            }
        }
        throw BadModel("resource RVA not backed by file bytes");
    };
    if(!resource_rva||!resource_length||resource_length>(256u<<20))
        throw BadModel("missing/oversized PE resource tree");
    const Bytes tree=file.Sub(translate(resource_rva,resource_length),
                              resource_length);
    std::array<std::string,4> labels{};
    Bytes found{};
    std::size_t matches=0;
    std::array<std::uint32_t,4> active{};
    const auto read_name=[&](std::uint32_t value){
        if(!(value&0x80000000u))return std::to_string(value);
        const auto at=static_cast<std::size_t>(value&0x7fffffffu);
        const auto length=tree.U16(at);
        if(length>256u)throw BadModel("resource name too long");
        (void)tree.Sub(at+2u,std::size_t(length)*2u);
        std::string result;
        for(std::size_t i=0;i<length;++i){
            const auto c=tree.U16(at+2u+i*2u);
            if(c<32u||c>126u)throw BadModel("unsupported resource name");
            result.push_back(static_cast<char>(c));
        }
        return result;
    };
    std::function<void(std::size_t,unsigned)> walk;
    walk=[&](std::size_t at,unsigned depth){
        if(depth>3u)throw BadModel("resource recursion limit exceeded");
        for(unsigned i=0;i<depth;++i)
            if(active[i]==at)throw BadModel("cyclic PE resource tree");
        active[depth]=static_cast<std::uint32_t>(at);
        const auto count=std::size_t(tree.U16(at+12u))+tree.U16(at+14u);
        if(count>1024u)throw BadModel("too many PE resources");
        (void)tree.Sub(at+16u,count*8u);
        for(std::size_t i=0;i<count;++i){
            const auto p=at+16u+8u*i;
            const auto name=read_name(tree.U32(p));
            const auto child=tree.U32(p+4u);
            labels[depth]=name;
            if(depth==0u&&name!="10")continue;
            if(depth==1u&&name!="WEIGHTS_HT")continue;
            if(child&0x80000000u){
                if(depth==3u)throw BadModel("resource tree too deep");
                walk(child&0x7fffffffu,depth+1u);
            }else if(depth==2u&&labels[0]=="10"&&
                     labels[1]=="WEIGHTS_HT"){
                const auto data=std::size_t(child);
                const auto rva=tree.U32(data),size=tree.U32(data+4u);
                if(!size||size>(256u<<20))
                    throw BadModel("bad neural payload size");
                found=file.Sub(translate(rva,size),size);
                ++matches;
            }
        }
    };
    walk(0u,0u);
    if(matches!=1u)
        throw BadModel("exactly one WEIGHTS_HT resource required");
    // Trust the model payload, not a fixed SHA of the entire DLL: Windows
    // DLLs may differ while carrying the same exact learned-weight resource.
    constexpr auto expected=
        "836f445d06ecd2e59bb9f17b84b91c143396fd76ccda1c9dc7fe81d5edd548f4";
    GlyphIntegrity::Sha256 hash;
    hash.Update(found.ptr,found.size);
    if(hash.FinishHex()!=expected)
        throw BadModel("WEIGHTS_HT SHA-256 differs from canonical Original");
    return found;
}
using Records=std::unordered_map<std::string,Bytes>;
[[nodiscard]] inline Records ReadRecords(Bytes resource){
    if(resource.size<8u||resource.U64(0)!=resource.size)
        throw BadModel("WEIGHTS_HT envelope size mismatch");
    Records records;
    std::size_t at=8u;
    while(at<resource.size){
        const auto n=resource.U64(at);at+=8u;
        if(!n||n>4096u)throw BadModel("bad weight name size");
        auto name=resource.Text(at,static_cast<std::size_t>(n));at+=n;
        if(!Starts(name,"block")||name.size()>120u)
            throw BadModel("unexpected weight name");
        for(char c:name)
            if(!((c>='0'&&c<='9')||c=='.'||c=='_'||
                 (c>='a'&&c<='z')))
                throw BadModel("invalid weight record name");
        const auto outer=resource.U64(at);at+=8u;
        if(outer<36u||outer>resource.size-at)
            throw BadModel("bad weight record byte count");
        auto body=resource.Sub(at,static_cast<std::size_t>(outer));
        const auto inner=body.U64(0),payload=body.U64(8);
        const auto device=body.U32(16);
        if(inner!=outer||!payload||payload>outer-36u||device>1u)
            throw BadModel("bad weight envelope");
        const auto meta=static_cast<std::size_t>(20u+payload);
        const auto dims=body.U64(meta+8u);
        if(dims>32u||meta+16u+4u*dims!=outer)
            throw BadModel("invalid weight dimension metadata");
        auto span=body.Sub(20u,static_cast<std::size_t>(payload));
        if(!records.emplace(std::move(name),span).second)
            throw BadModel("duplicate weight record");
        at+=static_cast<std::size_t>(outer);
        if(records.size()>512u)throw BadModel("too many weight records");
    }
    if(at!=resource.size||records.size()!=153u)
        throw BadModel("incomplete canonical Original resource");
    return records;
}
enum class Kind {Raw, Swin, Split, PostFP16, VitQKV};
struct Region {
    std::string name;
    std::size_t off{},size{};
    std::uint32_t n{},k{},inner{};
    Kind kind{Kind::Raw};
};
using Layout=std::vector<Region>;
inline void Add(Layout& out,std::string_view name,std::size_t size,
                std::uint32_t n=0u,std::uint32_t k=0u,
                std::uint32_t inner=0u,Kind kind=Kind::Raw){
    const auto start=out.empty()?0u:out.back().off+out.back().size;
    out.push_back({std::string(name),start,size,n,k,inner,kind});
}
[[nodiscard]] inline Layout SwinLayout(std::uint32_t c,
                                     std::uint32_t in,std::uint32_t out){
    const std::uint32_t heads=c/32u,h=4u*c;
    Layout a;
    if(heads==1u){
        Add(a,"mlp_expand",c*h,h,c,h/16u,Kind::Swin);
        Add(a,"mlp_contract",c*h,c,h,c/16u,Kind::Swin);
    }else{
        Add(a,"mlp_expand",c*h,h,c,h/heads/16u,Kind::Swin);
        Add(a,"mlp_mid",c*h/heads,c,h/heads,c/heads/16u,Kind::Swin);
        Add(a,"mlp_contract",c*c,c,c,c/16u,Kind::Swin);
    }
    const auto resample=in!=out?in*out:0u;
    const bool up=resample&&out<in;
    if(up)Add(a,"resample",resample,out,in,out/16u,Kind::Swin);
    Add(a,"residual_scale",2u*c+32u);
    if(up)Add(a,"upsample_gain",c==32u?2u*c:2u*c-32u);
    Add(a,"qkv",3u*c*c,3u*c,c,3u*c/16u,Kind::Swin);
    Add(a,"attn_pos_bias",heads*8192u);
    Add(a,"scalars_b",std::max(16u,4u*heads));
    Add(a,"attn_out_proj",c*c,c,c,c/16u,Kind::Swin);
    if(resample&&!up){
        Add(a,"attn_residual_scale",2u*c);
        Add(a,"resample",resample,out,in,out/16u,Kind::Swin);
        if(c==32u)Add(a,"tail",16u);
    }else Add(a,"attn_residual_scale",2u*c+16u);
    return a;
}
[[nodiscard]] inline Layout FixedLayout(bool post){
    Layout a;
    Add(a,"mlp_expand",4096u,128u,32u,8u,Kind::Swin);
    Add(a,"mlp_contract",4096u,32u,128u,2u,Kind::Swin);
    if(!post){
        Add(a,"pad",16u);
        Add(a,"input_lift",1024u);
        Add(a,"residual_scale",80u);
        Add(a,"qkv",3072u,96u,32u,6u,Kind::Swin);
        Add(a,"attn_pos_bias",8192u);
        Add(a,"scalars_b",16u);
        Add(a,"attn_out_proj",1024u,32u,32u,2u,Kind::Swin);
        Add(a,"attn_residual_scale",80u);
    }else{
        Add(a,"pad",16u);
        Add(a,"residual_scale",64u);
        Add(a,"main_gain",64u);
        Add(a,"skip_gain",64u);
        Add(a,"qkv",3072u,96u,32u,6u,Kind::Swin);
        Add(a,"attn_pos_bias",8192u);
        Add(a,"scalars_b",16u);
        Add(a,"attn_out_proj",1024u,32u,32u,2u,Kind::Swin);
        Add(a,"attn_residual_scale",80u);
        Add(a,"out_project",1024u,16u,32u,0u,Kind::PostFP16);
    }
    return a;
}
[[nodiscard]] inline Layout SplitLayout(std::size_t raw){
    Layout a;
    if(raw==524288u){
        Add(a,"ffwd_a",262144u,512u,512u,0u,Kind::Split);
        Add(a,"ffwd_b",262144u,512u,512u,0u,Kind::Split);
    }else if(raw==263168u){
        Add(a,"weight",262144u,512u,512u,0u,Kind::Split);
        Add(a,"skip_weight",1024u);
    }else if(raw==917568u){
        Add(a,"qkv",786432u,1536u,512u,0u,Kind::Split);
        Add(a,"attn_pos_bias",131072u);
        Add(a,"tail",64u);
    }else if(raw==524304u){
        Add(a,"weight",524288u,1024u,512u,0u,Kind::Split);
        Add(a,"tail",16u);
    }else if(raw==525312u){
        Add(a,"weight",524288u,512u,1024u,0u,Kind::Split);
        Add(a,"skip_weight",1024u);
    }
    return a;
}
[[nodiscard]] inline Layout VitLayout(std::size_t raw){
    Layout a;
    if(raw==3145856u){
        Add(a,"header",128u);
        Add(a,"q",1048576u,1024u,1024u,0u,Kind::VitQKV);
        Add(a,"k",1048576u,1024u,1024u,1u,Kind::VitQKV);
        Add(a,"v",1048576u,1024u,1024u,2u,Kind::VitQKV);
    }else if(raw==4194320u){
        Add(a,"weight",4194304u,4096u,1024u,0u,Kind::Split);
        Add(a,"tail",16u);
    }else if(raw==4196352u){
        Add(a,"weight",4194304u,1024u,4096u,0u,Kind::Split);
        Add(a,"skip_weight",2048u);
    }else if(raw==1050624u){
        Add(a,"weight",1048576u,1024u,1024u,0u,Kind::Split);
        Add(a,"skip_weight",2048u);
    }
    return a;
}
[[nodiscard]] inline Layout ForFamily(std::string_view family,std::size_t raw){
    if(family=="unpacked-preblock")return FixedLayout(false);
    if(family=="unpacked-postblock")return FixedLayout(true);
    if(family=="unpacked-splitswin")return SplitLayout(raw);
    if(family=="unpacked-vit")return VitLayout(raw);
    if(family!="unpacked")throw BadModel("unknown neural tensor family");
    Layout found;
    for(std::uint32_t c:{32u,64u,128u,256u})
        for(std::uint32_t direction=0u;direction<3u;++direction){
            const auto in=direction==2u?2u*c:c;
            const auto out=direction==1u?2u*c:c;
            auto layout=SwinLayout(c,in,out);
            if(layout.back().off+layout.back().size==raw){
                if(!found.empty())
                    throw BadModel("ambiguous Swin input/output shape");
                found=std::move(layout);
            }
        }
    if(found.empty())throw BadModel("unrecognized Swin record geometry");
    return found;
}
[[nodiscard]] inline std::vector<std::uint8_t> DeswizzleSwin(
    Bytes raw,const Region& r){
    if(r.kind!=Kind::Swin||!r.n||!r.k||!r.inner||
       r.n%16u||r.k%32u)throw BadModel("invalid Swin tile geometry");
    std::vector<std::uint8_t> dst(std::size_t(r.n)*r.k);
    const auto slices=r.k/32u;
    for(std::uint32_t t=0;t<r.n/16u;++t)
        for(std::uint32_t g=0;g<slices;++g){
            const auto base=r.off+std::size_t(t%r.inner)*512u+
                std::size_t(g)*512u*r.inner+
                std::size_t(t/r.inner)*512u*r.inner*slices;
            for(std::uint32_t half=0;half<2u;++half)
                for(std::uint32_t n=0;n<8u;++n)
                    for(std::uint32_t k=0;k<32u;++k){
                        const auto lane=4u*n+(k%8u)/2u;
                        const auto src=base+lane*16u+half*8u+
                            2u*(k/8u)+(k%2u);
                        dst[(std::size_t(t)*16u+half*8u+n)*r.k+g*32u+k]=
                            raw.U8(src);
                    }
        }
    return dst;
}
[[nodiscard]] inline std::vector<std::uint8_t> DeswizzleSplit(
    Bytes raw,const Region& r){
    if(r.kind!=Kind::Split||!r.n||!r.k||
       r.n%16u||r.k%32u)throw BadModel("invalid Split/ViT tile geometry");
    std::vector<std::uint8_t> dst(std::size_t(r.n)*r.k);
    const auto groups=r.n/16u;
    for(std::uint32_t gk=0;gk<r.k/32u;++gk)
        for(std::uint32_t gn=0;gn<groups;++gn){
            const auto base=r.off+(std::size_t(gk)*groups+gn)*512u;
            for(std::uint32_t half=0;half<2u;++half)
                for(std::uint32_t lane=0;lane<32u;++lane)
                    for(std::uint32_t b=0;b<8u;++b){
                        const auto n=gn*16u+half*8u+lane/4u;
                        const auto k=gk*32u+8u*(b>>1u)+
                            2u*(lane%4u)+(b&1u);
                        dst[std::size_t(n)*r.k+k]=
                            raw.U8(base+lane*16u+half*8u+b);
                    }
        }
    return dst;
}
[[nodiscard]] inline std::vector<std::uint8_t> DeswizzleVitQKV(
    Bytes raw,const Region& r){
    if(r.kind!=Kind::VitQKV||r.size!=1048576u||r.inner>2u)
        throw BadModel("invalid ViT QKV shape");
    std::vector<std::uint8_t> dst(r.size);
    for(std::uint32_t row=0;row<1024u;++row)
        for(std::uint32_t k=0;k<1024u;++k){
            const auto b=(k&1u)|((k>>1u&1u)<<4u)|((k>>2u&1u)<<5u)|
                ((k>>3u&1u)<<1u)|((k>>4u&1u)<<2u)|
                ((row&1u)<<6u)|((row>>1u&1u)<<7u)|
                ((row>>2u&1u)<<8u)|((row>>3u&1u)<<3u)|
                ((row>>4u&1u)<<9u);
            const auto tile=(row>>5u)|((k>>5u)<<5u);
            dst[std::size_t(row)*1024u+k]=
                raw.U8(128u+(3u*tile+r.inner)*1024u+b);
        }
    return dst;
}
[[nodiscard]] inline std::vector<std::uint8_t> DeswizzlePostFP16(
    Bytes raw,const Region& r){
    if(r.kind!=Kind::PostFP16||r.size!=1024u)
        throw BadModel("invalid postblock FP16 projection");
    std::vector<std::uint8_t> dst(r.size);
    for(std::uint32_t n=0;n<16u;++n)
        for(std::uint32_t k=0;k<32u;++k){
            const auto i=(k/16u)*256u+32u*(n%8u)+
                8u*((k%8u)/2u)+4u*(n/8u)+k%2u+2u*((k%16u)/8u);
            const auto source=r.off+2u*i;
            const auto target=2u*(n*32u+k);
            dst[target]=raw.U8(source);
            dst[target+1u]=raw.U8(source+1u);
        }
    return dst;
}
[[nodiscard]] inline std::vector<std::uint8_t> Tensor(
    std::string_view path,const Records& records){
    const auto slash=path.find('/');
    if(slash==std::string_view::npos||!Ends(path,".bin"))
        throw BadModel("invalid canonical model path");
    const auto family=path.substr(0,slash);
    const auto stem=path.substr(slash+1u,path.size()-slash-5u);
    std::string base;
    if(family=="inventory"){
        if(!Starts(stem,"weights/"))throw BadModel("invalid inventory path");
        base=std::string(stem.substr(8u));
    }else{
        const auto pos=stem.find(".layer");
        if(pos==std::string_view::npos)throw BadModel("invalid weight name");
        const auto second=stem.find(".layer",pos+6u);
        if(second==std::string_view::npos)throw BadModel("invalid model layer");
        base=std::string(stem.substr(0,second+6u));
    }
    const auto it=records.find(base);
    if(it==records.end())
        throw BadModel("missing source weight record: "+base);
    const Bytes raw=it->second;
    if(family=="inventory")return {raw.ptr,raw.ptr+raw.size};
    const auto layout=ForFamily(family,raw.size);
    if(layout.empty()||layout.back().off+layout.back().size!=raw.size)
        throw BadModel("unrecognized neural layer record size: "+base);
    const auto suffix=stem.substr(base.size()+1u);
    const auto selected=std::find_if(layout.begin(),layout.end(),
        [&](const Region& r){return suffix==r.name;});
    if(selected==layout.end())
        throw BadModel("unrecognized canonical tensor: "+std::string(path));
    const auto& r=*selected;
    (void)raw.Sub(r.off,r.size);
    switch(r.kind){
    case Kind::Raw:return {raw.ptr+r.off,raw.ptr+r.off+r.size};
    case Kind::Swin:return DeswizzleSwin(raw,r);
    case Kind::Split:return DeswizzleSplit(raw,r);
    case Kind::VitQKV:return DeswizzleVitQKV(raw,r);
    case Kind::PostFP16:return DeswizzlePostFP16(raw,r);
    }
    throw BadModel("unsupported tensor kind");
}
inline void WriteLE32(std::vector<std::uint8_t>& bytes,std::uint32_t n){
    for(unsigned j=0;j<4;++j)bytes.push_back(std::uint8_t(n>>(8u*j)));
}
inline void WriteLE64(std::vector<std::uint8_t>& bytes,std::uint64_t n){
    for(unsigned j=0;j<8;++j)bytes.push_back(std::uint8_t(n>>(8u*j)));
}
[[nodiscard]] inline bool WritePack(
    const std::filesystem::path& target,
    const std::span<const std::string_view> manifest,
    const Records& records){
    if(manifest.empty()||manifest.size()>4096u)return false;
    std::size_t index_length=16u;
    for(auto name:manifest){
        if(name.empty()||name.size()>4096u)return false;
        index_length+=4u+name.size()+16u;
    }
    std::vector<std::uint8_t> index;
    index.reserve(index_length);
    for(char c:std::string_view{"NRMODEL1"})
        index.push_back(std::uint8_t(c));
    WriteLE32(index,static_cast<std::uint32_t>(manifest.size()));
    WriteLE32(index,0u);
    std::error_code error;
    std::filesystem::create_directories(target.parent_path(),error);
    if(error)return false;
    const auto temp=target.string()+".importing";
    struct Cleanup {
        std::string path;
        ~Cleanup(){std::error_code ec;std::filesystem::remove(path,ec);}
    } cleanup{temp};
    std::fstream out(temp,std::ios::binary|std::ios::out|std::ios::trunc);
    if(!out)return false;
    out.seekp(static_cast<std::streamoff>(index_length),std::ios::beg);
    if(!out)return false;
    std::uint64_t position=(index_length+255u)&~std::uint64_t{255u};
    for(auto name:manifest){
        const auto tensor=Tensor(name,records);
        if(tensor.empty()||tensor.size()>(256u<<20))return false;
        WriteLE32(index,static_cast<std::uint32_t>(name.size()));
        for(char c:name)index.push_back(std::uint8_t(c));
        WriteLE64(index,position);
        WriteLE64(index,tensor.size());
        out.seekp(static_cast<std::streamoff>(position),std::ios::beg);
        if(!out)return false;
        out.write(reinterpret_cast<const char*>(tensor.data()),
                  static_cast<std::streamsize>(tensor.size()));
        if(!out)return false;
        position=(position+tensor.size()+255u)&~std::uint64_t{255u};
    }
    if(index.size()!=index_length)return false;
    out.seekp(0,std::ios::beg);
    out.write(reinterpret_cast<const char*>(index.data()),
              static_cast<std::streamsize>(index.size()));
    out.flush();
    if(!out)return false;
    out.close();
    if(!out)return false;
    std::ifstream verify(temp,std::ios::binary|std::ios::ate);
    if(!verify)return false;
    const auto final_size=verify.tellg();
    if(final_size<=static_cast<std::streamoff>(index_length))return false;
    verify.seekg(0);
    std::vector<std::uint8_t> saved(index_length);
    verify.read(reinterpret_cast<char*>(saved.data()),
                static_cast<std::streamsize>(saved.size()));
    if(!verify||saved!=index)return false;
    verify.close();
    std::filesystem::rename(temp,target,error);
    return !error;
}
} // namespace detail

struct Result {
    bool imported{};
    std::string reason{};
};
// A single user-supplied DLL can supply the Original network. Its resource
// is authenticated by SHA-256; unsupported/missing Compact never receives
// substituted Original tensor data or an invented success status.
[[nodiscard]] inline Result ImportOriginal(
    const std::filesystem::path& user_dll,
    const std::filesystem::path& model_cache,
    std::span<const std::string_view> public_manifest){
    try{
        std::ifstream stream(user_dll,std::ios::binary|std::ios::ate);
        if(!stream)return {false,"user DLL is not installed"};
        const auto n=stream.tellg();
        if(n<1024||n>static_cast<std::streamoff>(512u<<20))
            return {false,"invalid DLL file size"};
        std::vector<std::uint8_t> dll(static_cast<std::size_t>(n));
        stream.seekg(0);
        stream.read(reinterpret_cast<char*>(dll.data()),n);
        if(!stream||stream.gcount()!=n)
            return {false,"unable to read complete user DLL"};
        const detail::Bytes file{dll.data(),dll.size()};
        const auto resource=detail::FindOriginalResource(file);
        const auto records=detail::ReadRecords(resource);
        if(!detail::WritePack(model_cache,public_manifest,records))
            return {false,"unable to publish verified private model cache"};
        return {true,"authenticated Original model imported from user DLL"};
    }catch(const std::exception& e){return {false,e.what()};}
}
} // namespace Eden::NRDllImport
