// SPDX-License-Identifier: GPL-3.0-or-later
#version 450
#extension GL_GOOGLE_include_directive : enable
layout(push_constant) uniform Text { uint glyphs[24]; uint width; uint x; uint y; uint loading; } text;
layout(location = 0) out vec4 color;
#include "loading_wordmark.glsl"
#include "loading_scene.glsl"
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
    bool quick = (text.loading & 0xfff00000u) == 0xff100000u;
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
        // One animated loader is shared by the first Vulkan frame and the
        // jacket handoff. Bit 31 selects transparent compositing over the
        // retained jacket; the remaining bits still encode elapsed millis.
        // Normal loading, guest FPS HUD and quick-menu tags are unchanged.
        bool jacket_handoff = !quick && (text.loading & 0x80000000u) != 0u;
        uint elapsed_ms = text.loading & 0x7fffffffu;
        vec2 size = max(vec2(float(text.x), float(text.y)), vec2(1.0));
        vec2 p = vec2(gl_FragCoord.x, size.y - gl_FragCoord.y);
        float seconds = float(max(elapsed_ms, 1u) - 1u) * 0.001;
        vec3 scene = loading_scene(p, size, seconds);
        if (jacket_handoff) {
            // The original 3D jacket remains fully legible while the exact
            // same time-driven scene stays alive as a soft animated accent.
            // A moving lower-edge glint makes a frozen copy impossible.
            vec2 uv = p / size;
            float sweep = fract(seconds * 0.14);
            float distance_to_glint = abs(uv.x - sweep);
            float glint = 1.0 - smoothstep(0.018, 0.07, distance_to_glint);
            float lower_band = smoothstep(0.75, 0.86, uv.y) *
                               (1.0 - smoothstep(0.96, 0.995, uv.y));
            color = vec4(scene, 0.10 + glint * lower_band * 0.62);
        } else {
            color = vec4(scene, 1.0);
        }
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
    bool ink = false;
    if (p.x >= 0 && p.y >= 0) {
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
        vec3 menu_ink = light ? color24(0x16202cu) : color24(0xf4f2f8u);
        color = warning_row
            ? (ink ? vec4(1.0,0.83,0.41,1.0) : vec4(0.30,0.17,0.05,0.84))
            : (ink ? vec4(menu_ink,1.0) : vec4(row_rgb,alpha));
        return;
    }
    color = ink ? vec4(0.9, 0.95, 1.0, 1.0) : vec4(0.025, 0.04, 0.075, 0.5);
}
