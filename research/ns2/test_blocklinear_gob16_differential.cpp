// SPDX-License-Identifier: MIT
// Host-only research oracle: maintained Encore per-pixel GOB mapping vs
// Lichii 16-byte-unit fast path. This is NOT production source integration.
#include <algorithm>
#include <array>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <random>
#include <stdexcept>
#include <vector>
using u8=std::uint8_t; using u32=std::uint32_t; using u64=std::uint64_t;
constexpr u32 X_MASK=0b100101111U, Y_MASK=0b011010000U, GOB_SHIFT=9U;
constexpr u32 ceildiv(u32 x,u32 n){return (x+n-1)/n;}
template<u32 Mask> constexpr u32 pdep(u32 val){u32 out=0,m=Mask;for(u32 bit=1;m;bit<<=1){if(val&bit)out|=m&(~m+1U);m&=m-1U;}return out;}
constexpr u32 nativeGob(u32 at,bool native){if(!native)return at;const u32 swap=((at>>5)^(at>>6))&1U;return at^(swap<<5)^(swap<<6);}
struct Shape {
    u32 width{},height{},depth{},bpp{},bh{},bd{};
    bool native{};
    u32 pitch{};
    [[nodiscard]] u32 gobsX()const{return ceildiv(width*bpp,64);}
    [[nodiscard]] u32 blockSize()const{return gobsX()<<(9+bh+bd);}
    [[nodiscard]] u32 sliceSize()const{return ceildiv(height,8U<<bh)*blockSize();}
    [[nodiscard]] u32 swizzledSize()const{return ceildiv(depth,1U<<bd)*sliceSize();}
    [[nodiscard]] u32 linearSize()const{return depth*pitch*height;}
    [[nodiscard]] u32 offset(u32 xByte,u32 y,u32 z)const{
        const u32 offZ=(z>>bd)*sliceSize()+((z&((1U<<bd)-1))<<(GOB_SHIFT+bh));
        const u32 blockY=y>>3;
        const u32 offY=(blockY>>bh)*blockSize()+((blockY&((1U<<bh)-1))<<GOB_SHIFT);
        const u32 offX=(xByte>>6)<<(GOB_SHIFT+bh+bd);
        return nativeGob(offZ+offY+offX+(pdep<X_MASK>(xByte)|pdep<Y_MASK>(y)),native);
    }
    [[nodiscard]] u32 gobUnit(u32 xByte,u32 y,u32 z)const{
        // Lichii's 16-byte fast map: one entry per (row, x-unit) inside GOB.
        const u32 offZ=(z>>bd)*sliceSize()+((z&((1U<<bd)-1))<<(GOB_SHIFT+bh));
        const u32 blockY=y>>3;
        const u32 offY=(blockY>>bh)*blockSize()+((blockY&((1U<<bh)-1))<<GOB_SHIFT);
        const u32 offX=(xByte>>6)<<(GOB_SHIFT+bh+bd);
        const u32 unit=pdep<X_MASK>((xByte>>4 & 3U)*16U)|pdep<Y_MASK>(y&7U);
        return offZ+offY+offX+nativeGob(unit,native)+(xByte&15U);
    }
};
void require(bool okay,const char* reason){if(!okay)throw std::runtime_error(reason);}
void fullReference(const Shape& s,const std::vector<u8>& in,std::vector<u8>& out,bool toTiled){
    for(u32 z=0;z<s.depth;++z)for(u32 y=0;y<s.height;++y)for(u32 x=0;x<s.width;++x){
        const u32 lin=z*s.pitch*s.height+y*s.pitch+x*s.bpp;
        const u32 sw=s.offset(x*s.bpp,y,z);
        const u32 dst=toTiled?sw:lin,src=toTiled?lin:sw;
        require(dst+s.bpp<=out.size()&&src+s.bpp<=in.size(),"full bounds oracle");
        std::memcpy(out.data()+dst,in.data()+src,s.bpp);
    }
}
void fullFast16(const Shape&s,const std::vector<u8>&in,std::vector<u8>&out,bool toTiled){
    require(s.bpp==16,"fast16 only");
    for(u32 z=0;z<s.depth;++z)for(u32 y=0;y<s.height;++y)
        for(u32 group=0;group<ceildiv(s.width,4);++group){
            const u32 units=std::min(4U,s.width-group*4U);
            for(u32 unit=0;unit<units;++unit){
                const u32 xByte=(group*4U+unit)*16U;
                const u32 lin=z*s.pitch*s.height+y*s.pitch+xByte;
                const u32 sw=s.gobUnit(xByte,y,z);
                const u32 dst=toTiled?sw:lin,src=toTiled?lin:sw;
                require(dst+16<=out.size()&&src+16<=in.size(),"full fast16 bounds");
                std::memcpy(out.data()+dst,in.data()+src,16);
            }
        }
}
void partial(const Shape&s,const std::vector<u8>&in,std::vector<u8>&out,
             u32 originX,u32 originY,u32 extentX,u32 numLines,bool fast,bool toTiled){
    u32 unprocessed=numLines;const u32 extentY=std::min(numLines,s.height-originY);
    for(u32 z=0;z<s.depth && unprocessed;++z){
        const u32 lines=std::min(unprocessed,extentY);
        for(u32 line=0;line<lines;++line){
            const u32 y=line+originY;
            const u32 row=z*s.pitch*s.height+line*s.pitch;
            if(fast && (s.bpp==1||s.bpp==2||s.bpp==4||s.bpp==8||s.bpp==16)){
                const u32 begin=originX*s.bpp,end=(originX+extentX)*s.bpp;
                for(u32 x=begin;x<end;){
                    const u32 run=std::min(16U-(x&15U),end-x);
                    const u32 sw=s.gobUnit(x,y,z),lin=row+(x-begin);
                    const u32 dst=toTiled?sw:lin,src=toTiled?lin:sw;
                    require(dst+run<=out.size()&&src+run<=in.size(),"partial fast bounds");
                    std::memcpy(out.data()+dst,in.data()+src,run);
                    x+=run;
                }
            }else{
                for(u32 col=0;col<extentX;++col){
                    const u32 x=(originX+col)*s.bpp,sw=s.offset(x,y,z);
                    const u32 lin=row+col*s.bpp;
                    const u32 dst=toTiled?sw:lin,src=toTiled?lin:sw;
                    require(dst+s.bpp<=out.size()&&src+s.bpp<=in.size(),"partial ref bounds");
                    std::memcpy(out.data()+dst,in.data()+src,s.bpp);
                }
            }
        }
        unprocessed-=lines;
    }
}
int main(){
    std::mt19937 gen(0xEC0A2026U);
    constexpr std::array<u32,8> bpps{1,2,3,4,6,8,12,16};
    u64 assertions=0;
    for(int i=0;i<1536;++i){
        // Every BPP x block-height x block-depth x tiling profile, 8 shapes each.
        const u32 profile=static_cast<u32>(i)%192U;
        Shape s{static_cast<u32>(1U+gen()%73U),static_cast<u32>(1U+gen()%47U),
                static_cast<u32>(1U+gen()%4U),bpps[profile%8U],
                (profile/8U)%4U,(profile/32U)%3U,((profile/96U)&1U)!=0,0};
        s.pitch=s.width*s.bpp+16U*(gen()%3U);
        const u32 volume=s.swizzledSize(),linear=s.linearSize();
        require(volume>0&&linear>0,"size positive");
        std::vector<u8> tiled(volume+64,0xCC),reference(volume+64,0xCC);
        std::vector<u8> input(linear+64);
        for(auto& x:input)x=static_cast<u8>(gen()%256U);
        // Reference must agree with the per-GOB unit map for each interior byte.
        for(u32 z=0;z<s.depth;++z)for(u32 y=0;y<s.height;++y)
            for(u32 x=0;x<s.width*s.bpp;++x){
                require(s.offset(x,y,z)==s.gobUnit(x,y,z),"gob unit oracle mismatch");
                ++assertions;
            }
        if(s.bpp==16){
            fullReference(s,input,reference,true);
            fullFast16(s,input,tiled,true);
            require(tiled==reference,"whole GOB16 swizzle mismatch");++assertions;
            std::vector<u8> linearReference(linear+64,0xDD),linearFast(linear+64,0xDD);
            fullReference(s,tiled,linearReference,false);
            fullFast16(s,tiled,linearFast,false);
            require(linearReference==linearFast,"whole GOB16 unswizzle mismatch");++assertions;
            for(u32 z=0;z<s.depth;++z)for(u32 y=0;y<s.height;++y)
                for(u32 x=0;x<s.width*16;++x)
                    require(linearReference[z*s.pitch*s.height+y*s.pitch+x]==input[z*s.pitch*s.height+y*s.pitch+x],"whole roundtrip");
        }
        const u32 ox=gen()%s.width,oy=gen()%s.height;
        const u32 ex=1+gen()%(s.width-ox),lines=1+gen()%(s.height-oy);
        // For partial subrect the linear view is packed by copied row, with
        // pitch >= row bytes. Current Encore uses the supplied pitch_linear.
        std::vector<u8> partialRef(volume+64,0xCB),partialFast(volume+64,0xCB);
        partial(s,input,partialRef,ox,oy,ex,lines,false,true);
        partial(s,input,partialFast,ox,oy,ex,lines,true,true);
        require(partialRef==partialFast,"subrect swizzle mismatch");++assertions;
        std::vector<u8> readRef(linear+64,0xEF),readFast(linear+64,0xEF);
        partial(s,partialRef,readRef,ox,oy,ex,lines,false,false);
        partial(s,partialRef,readFast,ox,oy,ex,lines,true,false);
        require(readRef==readFast,"subrect unswizzle mismatch");++assertions;
        // Non-power BPP (3, 6, 12) is legacy fallback; pixel copies may cross
        // swizzle-unit boundaries. Test exact output equivalence but only
        // assert source roundtrips on admitted power-of-two fast-path BPP.
        if(s.bpp==1||s.bpp==2||s.bpp==4||s.bpp==8||s.bpp==16) {
            for(u32 line=0;line<lines;++line)for(u32 x=0;x<ex*s.bpp;++x) {
                require(readRef[line*s.pitch+x]==input[line*s.pitch+x],
                        "subrect roundtrip");
            }
        }
    }
    std::cout<<"PASS: 1536 seeded GOB layouts (all 192 BPP/block/tiling profiles x 8 shapes), "
             <<assertions<<" byte-offset oracle checks plus swizzle/unswizzle/roundtrips\n";
}
