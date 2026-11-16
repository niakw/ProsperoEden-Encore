// SPDX-License-Identifier: GPL-3.0-or-later
#include "quick_overlay_font.h"

#include "assets_dir.h"
#include "pe/gfx/bidi.hpp"
#include "pe/gfx/font.hpp"
#include "pe/gfx/system_fonts.hpp"
#include "settings_store.h"
#include "vulkan_menu_font_map.h"

#include <algorithm>
#include <cmath>
#include <memory>
#include <mutex>
#include <string>
#include <vector>

namespace Eden::QuickOverlay {
namespace {
constexpr std::uint32_t kSlotMask=0x7fffu;
constexpr int kMaxX=1023;
constexpr int kMinY=-64;
constexpr int kMaxY=63;

std::uint32_t pack(std::uint32_t slot,int x,int y) {
    if(slot==0||slot>kSlotMask) return 0;
    x=std::clamp(x,0,kMaxX);
    y=std::clamp(y,kMinY,kMaxY);
    return slot | (static_cast<std::uint32_t>(x)&0x3ffu)<<15u |
           (static_cast<std::uint32_t>(y)&0x7fu)<<25u;
}
std::vector<char32_t> decode(std::string_view text) {
    std::vector<char32_t> out;
    for(std::size_t i=0;i<text.size();) out.push_back(pe::gfx::next_codepoint(text,&i));
    return out;
}
bool shaping_control(char32_t c) {
    switch(c) {
    case U'\u061c': case U'\u200b': case U'\u200c': case U'\u200d':
    case U'\u200e': case U'\u200f': return true;
    default: return false;
    }
}
const FontMap::Face& fallback_for(int language) {
    language=std::clamp(language,0,static_cast<int>(std::size(Eden::kLanguageCatalogTags))-1);
    const std::string_view tag=Eden::kLanguageCatalogTags[language];
    for(std::size_t i=1;i<FontMap::kFaces.size();++i)
        if(FontMap::kFaces[i].locale==tag) return FontMap::kFaces[i];
    return FontMap::kFaces[0];
}
struct Shaper {
    std::mutex mutex;
    int language=-1;
    const FontMap::Face* fallback=nullptr;
    std::unique_ptr<pe::gfx::SystemFonts> fonts;

    bool ensure(int requested) {
        requested=std::clamp(requested,0,static_cast<int>(std::size(Eden::kLanguageCatalogTags))-1);
        const FontMap::Face& wanted=fallback_for(requested);
        if(fonts && language==requested && fallback==&wanted) return true;
        auto next=std::make_unique<pe::gfx::SystemFonts>();
        std::vector<std::string> paths{
            Eden::AppFile("ui/fonts/fallback/"+std::string(FontMap::kFaces[0].file))
        };
        if(&wanted!=&FontMap::kFaces[0])
            paths.push_back(Eden::AppFile("ui/fonts/fallback/"+std::string(wanted.file)));
        next->set(std::move(paths),Eden::kLanguageCatalogTags[requested]);
        // Montserrat is always face zero and is required for common UI text.
        if(next->face_for(U'A')!=0) return false;
        language=requested; fallback=&wanted; fonts=std::move(next);
        return true;
    }
    const FontMap::Face* atlas_face(int face) const {
        if(face==0) return &FontMap::kFaces[0];
        if(face==1 && fallback && fallback!=&FontMap::kFaces[0]) return fallback;
        return nullptr;
    }
};
Shaper& state(){ static Shaper value; return value; }
} // namespace

std::array<std::uint32_t,24> EncodeMenuText(std::string_view text,int language) {
    std::array<std::uint32_t,24> encoded{};
    auto chars=decode(text);
    if(chars.empty()) return encoded;
    auto& s=state();
    std::lock_guard lock{s.mutex};
    if(!s.ensure(language)||!s.fallback) return encoded;

    std::vector<int> faces(chars.size(),-1);
    for(std::size_t i=0;i<chars.size();++i)
        if(!shaping_control(chars[i])) faces[i]=s.fonts->face_for(chars[i]);
    // Default-ignorable shaping controls generally have no nominal glyph.
    // Keep them in the adjacent script run so HarfBuzz can apply them.
    for(std::size_t i=0;i<faces.size();++i)
        if(faces[i]<0 && i>0) faces[i]=faces[i-1];
    for(std::size_t i=faces.size();i-- > 0;)
        if(faces[i]<0 && i+1<faces.size()) faces[i]=faces[i+1];
    for(int& face:faces)
        if(face<0) face=0; // CI guarantees all drawable catalog characters.

    std::vector<std::uint8_t> levels;
    pe::gfx::bidi::resolve(chars,&levels);
    const auto visual=pe::gfx::bidi::visual_order(levels);
    std::vector<int> rank(chars.size());
    for(std::size_t pos=0;pos<visual.size();++pos)
        rank[static_cast<std::size_t>(visual[pos])]=static_cast<int>(pos);
    struct Run{std::size_t first,last;std::uint8_t level;int rank;int face;};
    std::vector<Run> runs;
    for(std::size_t i=0;i<chars.size();++i){
        if(!runs.empty()&&runs.back().level==levels[i]&&runs.back().face==faces[i]&&
           runs.back().last==i){
            runs.back().last=i+1;
            runs.back().rank=std::min(runs.back().rank,rank[i]);
        }else runs.push_back({i,i+1,levels[i],rank[i],faces[i]});
    }
    std::sort(runs.begin(),runs.end(),[](const Run&a,const Run&b){return a.rank<b.rank;});

    std::vector<pe::gfx::RunGlyph> shaped;
    float pen=0.0f;
    std::size_t out=0;
    for(const Run& run:runs){
        const FontMap::Face* spec=s.atlas_face(run.face);
        if(!spec) continue;
        s.fonts->shape(run.face,chars.data()+run.first,static_cast<int>(run.last-run.first),
                       (run.level&1u)!=0,&shaped);
        for(const auto& glyph:shaped){
            if(out>=encoded.size()) return encoded;
            if(glyph.id>=spec->glyphs) continue;
            const float px=FontMap::kPixelSize;
            const int x=static_cast<int>(std::lround((pen+glyph.x_offset)*px));
            const int y=static_cast<int>(std::lround(-glyph.y_offset*px));
            encoded[out++]=pack(static_cast<std::uint32_t>(spec->base)+glyph.id,x,y);
            pen+=glyph.advance;
        }
    }
    return encoded;
}
} // namespace Eden::QuickOverlay
