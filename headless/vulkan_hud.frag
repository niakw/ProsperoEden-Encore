// SPDX-License-Identifier: GPL-3.0-or-later
#version 450
#extension GL_GOOGLE_include_directive : enable
layout(push_constant) uniform Text { uint glyphs[24]; uint width; uint x; uint y; uint loading; } text;
layout(location = 0) out vec4 color;
#include "loading_wordmark.glsl"
#include "loading_scene.glsl"
#ifdef EDEN_LOADING_ARTWORK
// First image: 2D title scene. The second is flat paper consumed by the
// shared original case vertex/fragment shader.
layout(std430, set = 0, binding = 0) readonly buffer LoadingArt { uint pixels[]; } artwork;
vec3 artPixel(ivec2 p){
    ivec2 dim=ivec2(text.glyphs[1],text.glyphs[2]);p=clamp(p,ivec2(0),dim-1);
    return unpackUnorm4x8(artwork.pixels[uint(p.y*dim.x+p.x)]).rgb;
}
vec3 artSample(vec2 uv){
    vec2 dim=vec2(text.glyphs[1],text.glyphs[2]);
    vec2 p=clamp(uv,vec2(0),vec2(1))*dim-0.5;ivec2 lo=ivec2(floor(p));vec2 f=fract(p);
    return mix(mix(artPixel(lo),artPixel(lo+ivec2(1,0)),f.x),
               mix(artPixel(lo+ivec2(0,1)),artPixel(lo+ivec2(1,1)),f.x),f.y);
}
void main(){
    vec2 size=vec2(text.x,text.y),source=vec2(text.glyphs[1],text.glyphs[2]);
    float scale=min(size.x/source.x,size.y/source.y);vec2 fit=source*scale;
    vec2 uv=clamp((gl_FragCoord.xy-(size-fit)*0.5)/fit,vec2(0),vec2(1));
    vec3 base=artSample(uv);
    // Captured pixels are already display-encoded. SRGB attachments encode
    // the shader's output themselves, so undo that encoding only for them.
    if (text.glyphs[3] != 0u)
        base = mix(base / 12.92, pow((base + 0.055) / 1.055, vec3(2.4)),
                   greaterThan(base, vec3(0.04045)));
    color = vec4(base, 1.0);
}
#else
#ifdef EDEN_QUICK_MENU
#include "vulkan_menu_font.glsl"
#endif
// Matches pe::ui::theme::apply_palette: 4 palettes × 5 accents.
vec3 color24(uint rgb) {
    return vec3(float((rgb>>16u)&255u),float((rgb>>8u)&255u),
                float(rgb&255u))/255.0;
}
vec3 menuAccent(uint palette,uint accent) {
    const uint normal[5]=uint[5](0u,0x347fc4u,0x278b70u,0xb17724u,0xc04f72u);
    const uint bright[5]=uint[5](0u,0x9ccbf7u,0x8bd9b5u,0xf7cc87u,0xf5a6c4u);
    if(accent>0u&&accent<5u)
        return color24(palette==3u?normal[accent]:bright[accent]);
    if(palette==0u)return color24(0xff70e4u);
    if(palette==1u)return color24(0x8ab8ecu);
    if(palette==2u)return color24(0xffffffu);
    return color24(0x135eaau);
}
vec3 menuPanel(uint palette) {
    if(palette==1u)return color24(0x171b22u);
    if(palette==2u)return color24(0x16171bu);
    if(palette==3u)return color24(0xffffffu);
    return color24(0x120f1cu);
}
void main() {
    // High sentinel values describe a native quick-menu primitive, NOT
    // milliseconds of the loading scene. No texture or guest frame readback.
    // Menu-only bit tag. The normal FPS HUD and loading-time path
    // keep their previous push-constant contract.
#ifdef EDEN_QUICK_MENU
    bool quick = (text.loading & 0xfff00000u) == 0xff100000u;
#else
    const bool quick = false;
#endif
    uint kind = text.loading & 15u;
    uint style = (text.loading >> 8u) & 63u;
    uint palette = style % 4u;
    uint accent = (style / 4u) % 5u;
    bool contrast = style >= 20u;
    bool light = palette == 3u;
    vec3 highlight = menuAccent(palette,accent);
    vec3 surface = menuPanel(palette);
    if (quick && kind == 1u) {
        vec2 uv = gl_FragCoord.xy / max(vec2(text.x,text.y),vec2(1.0));
        float panel = step(0.53,uv.x) * (1.0-step(0.985,uv.x)) *
                      step(0.055,uv.y) * (1.0-step(0.945,uv.y));
        vec3 backdrop = light ? color24(0x1a2938u) : color24(0x04040au);
        vec3 panel_rgb = mix(surface,highlight,
                             (palette==0u?0.20:0.10)*clamp(uv.y,0.0,1.0));
        color = vec4(mix(backdrop,panel_rgb,panel),
                     mix(contrast?0.75:0.60,contrast?0.98:0.91,panel));
        return;
    }
    bool warning_row = quick && kind == 4u;
    bool menu_row = quick && (kind == 2u || kind == 3u || warning_row);
    if (text.loading != 0u && !menu_row) {
        // The loading screen: x and y carry the picture's size, loading the milliseconds since
        // it began (plus one). Vulkan counts rows from the top.
        vec2 size = vec2(float(text.x), float(text.y));
        vec4 dots = loading_artwork_indicator(
            vec2(gl_FragCoord.x, size.y - gl_FragCoord.y), size,
            float(text.loading - 1u) * 0.001);
        // glyphs[0] is reserved for artwork availability only in loading mode.
        // No purple fallback or opaque overwrite of a valid jacket.
        color = text.glyphs[0] == 1u ? dots :
            vec4(mix(vec3(0.055, 0.075, 0.105), dots.rgb, dots.a), 1.0);
        return;
    }
    // The overlay: x and y are where its text starts, width the picture's height. The text is
    // laid out for a picture 1080 rows high (a glyph's cell is 4 pixels there).
    ivec2 p = ivec2(gl_FragCoord.xy) - ivec2(text.x, text.y);
    float cell_size = 4.0 * float(text.width) / 1080.0;
    // Vulkan push-constant arrays require dynamically uniform indices. Load
    // each word at a constant index before the per-pixel local-array lookup.
    uint glyphs[24] = uint[24](
        text.glyphs[0], text.glyphs[1], text.glyphs[2], text.glyphs[3],
        text.glyphs[4], text.glyphs[5], text.glyphs[6], text.glyphs[7],
        text.glyphs[8], text.glyphs[9], text.glyphs[10], text.glyphs[11],
        text.glyphs[12], text.glyphs[13], text.glyphs[14], text.glyphs[15],
        text.glyphs[16], text.glyphs[17], text.glyphs[18], text.glyphs[19],
        text.glyphs[20], text.glyphs[21], text.glyphs[22], text.glyphs[23]);
    // The quick menu uses the launcher's Montserrat Medium raster, generated
    // from the same .pefont. The ordinary FPS HUD retains the compact legacy
    // 3x5 path below, so this change cannot perturb its established ABI.
    float menu_alpha = 0.0;
#ifdef EDEN_QUICK_MENU
    if (menu_row && p.x >= 0 && p.y >= 0) {
        float menu_scale = max(float(text.width) / 1080.0, 0.001);
        ivec2 menu_px = ivec2(vec2(p) / menu_scale);
        // Quick-menu words pack: 15-bit atlas slot, 10-bit absolute X,
        // signed 7-bit Y offset. HarfBuzz positions combining marks and
        // contextual Arabic glyphs on the CPU; the fragment shader only
        // samples the immutable generated atlas. The ordinary FPS HUD below
        // keeps its legacy 3x5 bitfield interpretation.
        for (int i = 0; i < 24; ++i) {
            uint packed = glyphs[i];
            if (packed == 0u) continue;
            uint slot = packed & 0x7fffu;
            int origin_x = int((packed >> 15u) & 0x3ffu);
            int origin_y = int((packed >> 25u) & 0x7fu);
            if (origin_y >= 64) origin_y -= 128;
            if (slot == 0u || slot >= uint(MENU_FONT_SLOT_COUNT)) continue;
            ivec4 metric = menuFontMetric(slot);
            int gx = menu_px.x - (origin_x + metric.x);
            int gy = menu_px.y - (MENU_FONT_BASELINE + origin_y + metric.y);
            if (gx >= 0 && gy >= 0 && gx < metric.z && gy < metric.w)
                menu_alpha = max(menu_alpha, menuFontSlotAlpha(slot, gx, gy));
        }
    }
#endif
    bool ink = false;
    if (!menu_row && p.x >= 0 && p.y >= 0) {
        ivec2 cell = ivec2(vec2(p) / cell_size);
        int i = cell.x / 4;
        int x = cell.x % 4;
        if (i < 24 && x < 3 && cell.y < 5)
            ink = ((glyphs[i] >> uint((4 - cell.y) * 3 + 2 - x)) & 1u) != 0u;
    }
    if (menu_row) {
        bool selected = kind == 3u;
        vec3 row_rgb = mix(surface,highlight,
                           selected?(light?0.24:0.36):(light?0.04:0.08));
        float alpha = selected?(contrast?0.98:0.84):
                               (contrast?0.87:0.48);
        vec4 base = warning_row ? vec4(0.30,0.17,0.05,0.84)
                                : vec4(row_rgb,alpha);
        vec4 ink_color = warning_row ? vec4(1.0,0.83,0.41,1.0)
                                     : vec4(light ? color24(0x16202cu)
                                                  : color24(0xf4f2f8u),1.0);
        color = mix(base, ink_color, menu_alpha);
        return;
    }
    color = ink ? vec4(0.9, 0.95, 1.0, 1.0) : vec4(0.025, 0.04, 0.075, 0.5);
}
#endif // EDEN_LOADING_ARTWORK
