// SPDX-License-Identifier: GPL-3.0-or-later
// Host-only generator for the descriptor-free Vulkan quick-menu glyph atlas.
#define STB_TRUETYPE_IMPLEMENTATION
#include "stb_truetype.h"

#include <algorithm>
#include <array>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <iterator>
#include <sstream>
#include <string>
#include <vector>

namespace {
constexpr int kPixel = 20;
constexpr int kRange = 4;
constexpr int kCellW = 48;
constexpr int kCellH = 36;
constexpr int kWords = 2;
constexpr std::uint32_t kMaxSlots = 0x7fffu;

struct FontSpec {
    const char* locale;
    const char* file;
    std::filesystem::path path;
    std::uint32_t base{};
    std::uint32_t glyphs{};
};
struct Slot {
    int left{}, top{}, w{}, h{};
    std::array<std::uint32_t, kCellH * kWords> low{};
    std::array<std::uint32_t, kCellH * kWords> high{};
};

std::vector<unsigned char> read(const std::filesystem::path& path) {
    std::ifstream in(path, std::ios::binary);
    return {std::istreambuf_iterator<char>(in), std::istreambuf_iterator<char>()};
}
void put_level(Slot& out, int x, int y, unsigned level) {
    if (x < 0 || x >= kCellW || y < 0 || y >= kCellH || level == 0) return;
    const int word = x / 32;
    const std::uint32_t bit = 1u << (31 - (x % 32));
    const std::size_t at = static_cast<std::size_t>(y) * kWords + word;
    if (level & 1u) out.low[at] |= bit;
    if (level & 2u) out.high[at] |= bit;
}
Slot raster(stbtt_fontinfo& font, int glyph) {
    Slot out;
    const float scale = stbtt_ScaleForMappingEmToPixels(&font, static_cast<float>(kPixel));
    int w=0,h=0,xoff=0,yoff=0;
    unsigned char* sdf = stbtt_GetGlyphSDF(&font, scale, glyph, kRange, 128,
                                            128.0f / kRange, &w, &h, &xoff, &yoff);
    out.left=xoff; out.top=yoff; out.w=w; out.h=h;
    if (w > kCellW || h > kCellH) {
        std::cerr << "glyph " << glyph << " exceeds cell " << w << "x" << h << "\n";
        std::exit(1);
    }
    for (int y=0; sdf && y<h; ++y) for (int x=0; x<w; ++x) {
        const unsigned v=sdf[y*w+x];
        const unsigned level=v<96?0u:v<120?1u:v<144?2u:3u;
        put_level(out,x,y,level);
    }
    stbtt_FreeSDF(sdf,nullptr);
    return out;
}
std::string q(std::string_view s) {
    std::string out{"\""};
    for(char c:s){ if(c=='\\'||c=='\"') out.push_back('\\'); out.push_back(c); }
    out.push_back('\"'); return out;
}
template<class T>
void emit_uint_chunks(std::ostream& out,const char* name,const std::vector<T>& values) {
    // SPIR-V encodes instruction word counts in 16 bits. A single atlas-sized
    // OpConstantComposite can overflow that field; split constants well below it.
    constexpr std::size_t kChunk = 16384;
    const std::size_t chunks=(values.size()+kChunk-1)/kChunk;
    for(std::size_t c=0;c<chunks;++c){
        const std::size_t first=c*kChunk;
        const std::size_t count=std::min(kChunk,values.size()-first);
        out<<"const uint "<<name<<"_"<<c<<"["<<count<<"] = uint["<<count<<"](\n";
        for(std::size_t i=0;i<count;++i){
            if(i%8==0) out<<"    ";
            out<<"0x"<<std::hex<<std::setw(8)<<std::setfill('0')
               <<static_cast<std::uint32_t>(values[first+i])<<"u"<<std::dec;
            if(i+1!=count) out<<", ";
            if(i%8==7||i+1==count) out<<"\n";
        }
        out<<");\n";
    }
    out<<"uint "<<name<<"At(int index) {\n"
       <<"    int chunk = index / "<<kChunk<<";\n"
       <<"    int local = index - chunk * "<<kChunk<<";\n"
       <<"    switch (chunk) {\n";
    for(std::size_t c=0;c<chunks;++c)
        out<<"    case "<<c<<": return "<<name<<"_"<<c<<"[local];\n";
    out<<"    default: return 0u;\n    }\n}\n";
}
} // namespace

int main(int argc,char** argv) {
    if(argc!=5){
        std::cerr<<"usage: "<<argv[0]<<" Montserrat-Medium.ttf fallback-dir out.glsl out-map.h\n";
        return 2;
    }
    const std::filesystem::path montserrat=argv[1], fallback=argv[2];
    std::vector<FontSpec> fonts{
        {"", "Montserrat-Medium.ttf", montserrat},
        {"el-GR","NotoSans-Greek.ttf",fallback/"NotoSans-Greek.ttf"},
        {"ar","NotoSansArabic.ttf",fallback/"NotoSansArabic.ttf"},
        {"th-TH","NotoSansThai.ttf",fallback/"NotoSansThai.ttf"},
        {"ja-JP","NotoSansJP.ttf",fallback/"NotoSansJP.ttf"},
        {"ko-KR","NotoSansKR.ttf",fallback/"NotoSansKR.ttf"},
        {"zh-Hans","NotoSansSC.ttf",fallback/"NotoSansSC.ttf"},
        {"zh-Hant","NotoSansTC.ttf",fallback/"NotoSansTC.ttf"},
    };
    std::vector<Slot> slots(1); // slot zero is transparent/missing.
    for(auto& spec:fonts){
        auto bytes=read(spec.path);
        if(bytes.empty()){ std::cerr<<"cannot read "<<spec.path<<"\n"; return 1; }
        stbtt_fontinfo font{};
        const int off=stbtt_GetFontOffsetForIndex(bytes.data(),0);
        if(off<0||!stbtt_InitFont(&font,bytes.data(),off)){
            std::cerr<<"invalid font "<<spec.path<<"\n"; return 1;
        }
        spec.base=static_cast<std::uint32_t>(slots.size());
        spec.glyphs=static_cast<std::uint32_t>(font.numGlyphs);
        if(spec.base+spec.glyphs>kMaxSlots){
            std::cerr<<"atlas slot budget exceeded\n"; return 1;
        }
        for(std::uint32_t gid=0;gid<spec.glyphs;++gid)
            slots.push_back(raster(font,static_cast<int>(gid)));
        std::cout<<"VULKAN_MENU_FACE locale="<<(spec.locale[0]?spec.locale:"montserrat")
                 <<" glyphs="<<spec.glyphs<<" base="<<spec.base<<"\n";
    }

    std::vector<std::uint32_t> low,high;
    low.reserve(slots.size()*kCellH*kWords);
    high.reserve(slots.size()*kCellH*kWords);
    std::ofstream glsl(argv[3]);
    glsl<<"// Generated by bake_vulkan_menu_font.cpp. Do not hand-edit.\n"
        <<"const int MENU_FONT_CELL_W = "<<kCellW<<";\n"
        <<"const int MENU_FONT_CELL_H = "<<kCellH<<";\n"
        <<"const int MENU_FONT_WORDS = "<<kWords<<";\n"
        <<"const int MENU_FONT_BASELINE = 26;\n"
        <<"const int MENU_FONT_SLOT_COUNT = "<<slots.size()<<";\n";
    glsl<<"const ivec4 MENU_FONT_METRICS["<<slots.size()<<"] = ivec4["<<slots.size()<<"](\n";
    for(std::size_t i=0;i<slots.size();++i){
        const auto& s=slots[i];
        glsl<<"    ivec4("<<s.left<<","<<s.top<<","<<s.w<<","<<s.h<<")";
        if(i+1!=slots.size()) glsl<<",";
        glsl<<"\n";
        low.insert(low.end(),s.low.begin(),s.low.end());
        high.insert(high.end(),s.high.begin(),s.high.end());
    }
    glsl<<");\n";
    emit_uint_chunks(glsl,"MENU_FONT_LOW",low);
    emit_uint_chunks(glsl,"MENU_FONT_HIGH",high);
    glsl<<R"GLSL(
float menuFontSlotAlpha(uint slot, int x, int y) {
    if (slot == 0u || slot >= uint(MENU_FONT_SLOT_COUNT) ||
        x < 0 || y < 0 || x >= MENU_FONT_CELL_W || y >= MENU_FONT_CELL_H) return 0.0;
    int word = x >> 5;
    int bit_index = 31 - (x & 31);
    int index = (int(slot) * MENU_FONT_CELL_H + y) * MENU_FONT_WORDS + word;
    uint bit = 1u << uint(bit_index);
    uint level = ((MENU_FONT_LOWAt(index) & bit) != 0u ? 1u : 0u) |
                 ((MENU_FONT_HIGHAt(index) & bit) != 0u ? 2u : 0u);
    return float(level) / 3.0;
}
)GLSL";
    glsl.close();

    std::ofstream map(argv[4]);
    map<<"// Generated by bake_vulkan_menu_font.cpp. Do not hand-edit.\n#pragma once\n"
       <<"#include <array>\n#include <cstdint>\n#include <string_view>\n"
       <<"namespace Eden::QuickOverlay::FontMap {\n"
       <<"inline constexpr float kPixelSize="<<kPixel<<".0f;\n"
       <<"struct Face { std::string_view locale; std::string_view file; std::uint16_t base; std::uint16_t glyphs; };\n"
       <<"inline constexpr std::array<Face,"<<fonts.size()<<"> kFaces{{\n";
    for(const auto& spec:fonts)
        map<<"    Face{"<<q(spec.locale)<<","<<q(spec.file)<<","<<spec.base<<","<<spec.glyphs<<"},\n";
    map<<"}};\n}\n";
    map.close();
    std::cout<<"VULKAN_MENU_UNICODE_ATLAS_PASS faces="<<fonts.size()
             <<" slots="<<slots.size()<<" glsl_bytes="<<std::filesystem::file_size(argv[3])<<"\n";
}
