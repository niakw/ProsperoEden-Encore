// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
// Original projective launcher geometry and materials, shared by both loading APIs.
namespace Eden::LoadingCase {
inline constexpr const char *kVertex = R"(
#ifdef EDEN_CASE_VULKAN
layout(push_constant) uniform CaseBlock {
    vec4 rect;vec4 top;vec4 bottom;vec4 border;vec4 params;vec4 extra;vec4 output_info;
} pc;
vec4 caseViewport(){
    float scale=min(pc.output_info.x/1920.0,pc.output_info.y/1080.0);
    return vec4(scale,(pc.output_info.xy-vec2(1920.0,1080.0)*scale)*0.5,0.0);
}
#define u_viewport caseViewport()
#define u_surface pc.output_info.xy
#define CASE_IO(n) layout(location=n)
#else
#define CASE_IO(n)
#endif
#if defined(EDEN_CASE_VULKAN)
#define a_rect pc.rect
#define a_top pc.top
#define a_bottom pc.bottom
#define a_border pc.border
#define a_params pc.params
#define a_extra pc.extra
#elif defined(EDEN_CASE_HANDOFF_GL)
uniform vec4 a_rect,a_top,a_bottom,a_border,a_params,a_extra;
uniform vec4 u_viewport;
uniform vec2 u_surface;
#else
layout(location = 0) in vec4 a_rect;
layout(location = 1) in vec4 a_top;
layout(location = 2) in vec4 a_bottom;
layout(location = 3) in vec4 a_border;
layout(location = 4) in vec4 a_params;
layout(location = 5) in vec4 a_extra;
layout(location = 0) uniform vec4 u_viewport; // scale, offset x, offset y
layout(location = 1) uniform vec2 u_surface;
#endif
CASE_IO(0) out vec2 v_local;
CASE_IO(1) out vec2 v_virtual;
CASE_IO(2) out vec2 v_uv;
CASE_IO(3) out vec2 v_st;
CASE_IO(4) flat out vec2 v_half;
CASE_IO(5) flat out vec4 v_top;
CASE_IO(6) flat out vec4 v_bottom;
CASE_IO(7) flat out vec4 v_border;
CASE_IO(8) flat out vec4 v_params;
CASE_IO(9) flat out vec4 v_extra;
#ifdef EDEN_CASE_VULKAN
const vec2 kCorners[4]=vec2[4](vec2(0,0),vec2(1,0),vec2(0,1),vec2(1,1));
#else
const vec2 kCorners[6] = vec2[6](vec2(0.0, 0.0), vec2(1.0, 0.0), vec2(0.0, 1.0),
                                 vec2(1.0, 0.0), vec2(1.0, 1.0), vec2(0.0, 1.0));
#endif
void main()
{
#ifdef EDEN_CASE_VULKAN
    vec2 corner=kCorners[gl_VertexIndex];
#else
    vec2 corner=kCorners[gl_VertexID];
#endif
    int shape = int(a_params.w + 0.5);
    vec2 size = a_rect.zw;
    // Grow shapes by their softness plus one output pixel for anti-aliasing;
    // glyph and image quads map texels exactly and are not grown.
    float pad = (shape == 1 || shape == 3 || shape == 9 || shape == 10 || shape == 11 || shape == 12 || shape == 13 || shape == 14 || shape == 15) ?
        0.0 : a_params.z + 1.0 / u_viewport.x;
    vec2 local = mix(vec2(-pad), size + vec2(pad), corner);
    vec2 virt = a_rect.xy + local;
    vec2 unit = local / max(size, vec2(1e-3));
    v_virtual = virt;
    v_local = local - 0.5 * size;
    v_half = 0.5 * size;
    v_st = clamp(unit, 0.0, 1.0);
    v_uv = mix(a_extra.xy, a_extra.zw, unit);
    v_top = a_top;
    v_bottom = a_bottom;
    v_border = a_border;
    v_params = a_params;
    v_extra = a_extra;
    float clip_w = 1.0;
    if (shape == 9 || shape == 10 || shape == 11 || shape == 12 || shape == 13 || shape == 14 || shape == 15) {
        // A real projective quad, not a horizontally squashed 2D image.
        // Shared retail-case geometry across all titles and console/host.
        float a = a_params.x;
        float cs = cos(a), sn = sin(a);
        vec2 centre = a_rect.xy + 0.5 * size;
        vec2 local = (corner - 0.5) * size;
        float x, z;
        if (shape == 9 || shape == 11) {
            // Place a real back surface on the FAR plane of the case.
            // It must not occupy the same Z as the front artwork.
            float depth = a_params.y > 0.5 ? 44.0 : 0.0;
            x = local.x * cs - depth * sn;
            z = -local.x * sn - depth * cs;
            vec2 oriented = vec2(a_params.y > 0.5 ? 1.0 - corner.x : corner.x,
                                 corner.y);
            v_uv = mix(a_extra.xy, a_extra.zw, oriented);
        } else if (shape == 10 || shape == 14 || shape == 15) {
            // The side lies between two parallel printed planes. It occupies
            // real space in Z rather than being a 2D strip in screen-space.
            float side = a_extra.x < -0.5 ? -0.5 :
                         a_extra.x > 0.5 ? 0.5 :
                         (sn > 0.0 ? -0.5 : 0.5);
            float edge_x = side * size.x;
            float depth = a_params.z + corner.x * a_params.y;
            x = edge_x * cs - depth * sn;
            z = -edge_x * sn - depth * cs;
            // The projected side reverses screen X; mirror the ink only.
            if (shape == 14) v_uv = vec2(1.0 - corner.x, corner.y);
        } else if (shape == 12) {
            float depth = corner.y * a_params.z;
            x = local.x * cs - depth * sn;
            z = -local.x * sn - depth * cs;
        } else {
            // True rounded corner: eight 3D quarter-arc segments, extruded
            // along the full case depth. This is an actual curved silhouette,
            // NOT a 2D rounded border or a flat image on the side.
            const float pi = 3.14159265358979323846;
            int quadrant = int(a_extra.x + 0.5);
            float theta0 = quadrant == 0 ? pi :
                           quadrant == 1 ? 1.5*pi :
                           quadrant == 2 ? 0.0 : 0.5*pi;
            float theta = theta0 +
                (a_extra.y + corner.y) / max(1.0, a_extra.z) * 0.5*pi;
            float radius = a_params.y;
            float side_x = (quadrant == 0 || quadrant == 3 ? -1.0 : 1.0);
            float side_y = (quadrant <= 1 ? -1.0 : 1.0);
            float rounded_x = side_x * (0.5 * size.x - radius) +
                              radius * cos(theta);
            float rounded_y = side_y * (0.5 * size.y - radius) +
                              radius * sin(theta);
            float depth = corner.x * a_params.z;
            x = rounded_x * cs - depth * sn;
            z = -rounded_x * sn - depth * cs;
            // Normal on curved side, consumed by the lit plastic material.
            v_uv = vec2(cos(theta), sin(theta));
            virt.y = rounded_y;
        }
        // One rigid transform for all six surfaces. Previously the caps
        // faked a separate vertical slope, leaving visibly disconnected
        // white triangles at the plastic corners.
        float world_y = shape == 12 ?
            (a_params.y > 0.5 ? 0.5 : -0.5) * size.y :
            shape == 13 ? virt.y : local.y;
        const float pitch = 0.055;
        float pitched_y = world_y * cos(pitch) - z * sin(pitch);
        float pitched_z = world_y * sin(pitch) + z * cos(pitch);
        clip_w = max(0.65, 1.0 - pitched_z / 820.0);
        // Small camera roll exposes the shell while preserving the paper's
        // perspective (and retaining the same camera for front/back/corners).
        virt = centre + vec2(x + pitched_y * 0.018,
                             pitched_y + x * 0.045) / clip_w;
        v_virtual = virt;
    }
    vec2 surface = virt * u_viewport.x + u_viewport.yz;
    vec2 ndc = surface / u_surface * 2.0 - 1.0;
    // Non-unit W gives hardware perspective-correct image UV interpolation.
#ifdef EDEN_CASE_VULKAN
    gl_Position=vec4(ndc*clip_w,0.0,clip_w);
#else
    gl_Position = vec4(ndc.x * clip_w, -ndc.y * clip_w, 0.0, clip_w);
#endif
}
)";

inline constexpr const char *kFragment = R"(
#ifdef EDEN_CASE_VULKAN
layout(push_constant) uniform CaseBlock {
    vec4 rect;vec4 top;vec4 bottom;vec4 border;vec4 params;vec4 extra;vec4 output_info;
} pc;
vec4 caseViewport(){
    float scale=min(pc.output_info.x/1920.0,pc.output_info.y/1080.0);
    return vec4(scale,(pc.output_info.xy-vec2(1920.0,1080.0)*scale)*0.5,0.0);
}
#define u_viewport caseViewport()
#define u_surface pc.output_info.xy
#define CASE_IO(n) layout(location=n)
#else
#define CASE_IO(n)
#endif
#if defined(EDEN_CASE_VULKAN)
layout(std430,set=0,binding=0) readonly buffer LoadingArt { uint pixels[]; } artwork;
#define CASE_SLOT int(pc.output_info.z+0.5)
#elif defined(EDEN_CASE_HANDOFF_GL)
uniform vec4 u_viewport;
uniform sampler2D u_texture;
uniform int u_slot;
#define CASE_SLOT u_slot
#else
layout(location = 0) uniform vec4 u_viewport;
layout(location = 2) uniform sampler2D u_texture;
#endif
#if defined(EDEN_CASE_VULKAN) || defined(EDEN_CASE_HANDOFF_GL)
vec4 casePaperRect(){
    int slot=CASE_SLOT;
    return slot==1?vec4(0,0,960,1536):slot==2?vec4(960,0,960,1536):vec4(1920,0,128,1536);
}
#ifdef EDEN_CASE_VULKAN
vec4 casePixel(ivec2 p){
    return unpackUnorm4x8(artwork.pixels[1920u*1080u+uint(p.y)*2048u+uint(p.x)]);
}
#endif
vec4 caseTexture(vec2 uv){
    vec4 r=casePaperRect();
    vec2 p=clamp(r.xy+clamp(uv,vec2(0),vec2(1))*r.zw,r.xy+vec2(0.5),r.xy+r.zw-vec2(0.5));
#ifdef EDEN_CASE_VULKAN
    vec2 q=p-0.5;ivec2 lo=ivec2(floor(q)),hi=min(lo+1,ivec2(r.xy+r.zw)-1);vec2 f=fract(q);
    return mix(mix(casePixel(lo),casePixel(ivec2(hi.x,lo.y)),f.x),
               mix(casePixel(ivec2(lo.x,hi.y)),casePixel(hi),f.x),f.y);
#else
    return texture(u_texture,p/vec2(2048,1536));
#endif
}
#else
#define caseTexture(uv) texture(u_texture,uv)
#endif
CASE_IO(0) in vec2 v_local;
CASE_IO(1) in vec2 v_virtual;
CASE_IO(2) in vec2 v_uv;
CASE_IO(3) in vec2 v_st;
CASE_IO(4) flat in vec2 v_half;
CASE_IO(5) flat in vec4 v_top;
CASE_IO(6) flat in vec4 v_bottom;
CASE_IO(7) flat in vec4 v_border;
CASE_IO(8) flat in vec4 v_params;
CASE_IO(9) flat in vec4 v_extra;
CASE_IO(0) out vec4 frag_color;

float round_box(vec2 p, vec2 b, float r)
{
    vec2 q = abs(p) - b + r;
    return length(max(q, 0.0)) + min(max(q.x, q.y), 0.0) - r;
}

float triangle(vec2 p, vec2 p0, vec2 p1, vec2 p2)
{
    vec2 e0 = p1 - p0, e1 = p2 - p1, e2 = p0 - p2;
    vec2 v0 = p - p0, v1 = p - p1, v2 = p - p2;
    vec2 q0 = v0 - e0 * clamp(dot(v0, e0) / dot(e0, e0), 0.0, 1.0);
    vec2 q1 = v1 - e1 * clamp(dot(v1, e1) / dot(e1, e1), 0.0, 1.0);
    vec2 q2 = v2 - e2 * clamp(dot(v2, e2) / dot(e2, e2), 0.0, 1.0);
    float s = sign(e0.x * e2.y - e0.y * e2.x);
    vec2 d = min(min(vec2(dot(q0, q0), s * (v0.x * e0.y - v0.y * e0.x)),
                     vec2(dot(q1, q1), s * (v1.x * e1.y - v1.y * e1.x))),
                 vec2(dot(q2, q2), s * (v2.x * e2.y - v2.y * e2.x)));
    return -sqrt(d.x) * sign(d.y);
}

void main()
{
    float px = 1.0 / u_viewport.x; // virtual units per output pixel
    int shape = int(v_params.w + 0.5);
    vec4 fill = mix(v_top, v_bottom, shape == 7 ? v_st.x : v_st.y);
    vec4 color;
    if (shape == 0 || shape == 7)
    {
        float radius = min(v_params.x, min(v_half.x, v_half.y));
        float d = round_box(v_local, v_half, radius);
        color = fill;
        if (v_params.y > 0.0)
        {
            float inner = clamp(0.5 - (d + v_params.y) / px, 0.0, 1.0);
            color = mix(v_border, fill, inner);
        }
        color.a *= clamp(0.5 - d / px, 0.0, 1.0);
    }
    else if (shape == 1)
    {
        float sdf = caseTexture(v_uv).r;
        float distance = (sdf - 0.5) * 2.0 * v_params.x + v_params.y;
        color = vec4(fill.rgb, fill.a * clamp(distance / px + 0.5, 0.0, 1.0));
    }
    else if (shape == 2)
    {
        float radius = min(v_params.x, min(v_half.x, v_half.y));
        float d = round_box(v_local, v_half, radius);
        color = vec4(fill.rgb, fill.a * (1.0 - smoothstep(-v_params.z, v_params.z, d)));
    }
    else if (shape == 3)
    {
        color = caseTexture(v_uv) * fill;
    }
    else if (shape == 9)
    {
        // The paper is a square-cornered continuous wrap, not three
        // individually rounded rectangles separated from the side print.
        float d = round_box(v_local, v_half, 0.0);
        color = v_params.z > 0.5 ? caseTexture(clamp(v_uv, 0.0, 1.0)) * v_top : v_top;
        float scan_inside = v_params.z > 0.5 ?
            step(0.0, v_uv.x) * step(v_uv.x, 1.0) *
            step(0.0, v_uv.y) * step(v_uv.y, 1.0) : 1.0;
        color.a *= scan_inside * (1.0 - smoothstep(-1.0, 1.0, d));
    }
    else if (shape == 14)
    {
        // A flat original scan is texture-mapped onto our own dimensional
        // side plane. The scan carries ink only, not any 3D shell pixels.
        vec4 ink = caseTexture(v_uv);
        float side_light = 0.81 + 0.19 * (1.0 - v_st.x);
        color = vec4(ink.rgb * v_top.rgb * side_light, ink.a * v_top.a);
    }
    else if (shape == 15)
    {
        // User's red empty-spine reference rendered as clean vector features
        // directly on our physical side plane. No low-resolution texture or
        // fake game title is ever stretched to cover the height.
        vec2 p = vec2((1.0 - v_st.x) * 44.0, v_st.y * 730.0);
        vec3 red = v_top.rgb * (0.85 + 0.15 * (1.0 - v_st.x));
        float left_outer = 1.0 - smoothstep(-0.9, 0.9,
            round_box(p - vec2(14.5, 34.0), vec2(8.0, 20.0), 7.7));
        float left_inner = 1.0 - smoothstep(-0.9, 0.9,
            round_box(p - vec2(14.5, 34.0), vec2(5.1, 17.0), 5.0));
        float right_body = 1.0 - smoothstep(-0.9, 0.9,
            round_box(p - vec2(30.0, 34.0), vec2(7.8, 20.0), 7.5));
        float left_dot = 1.0 - smoothstep(2.3, 3.9,
            length(p - vec2(14.5, 25.5)));
        float right_dot = 1.0 - smoothstep(2.3, 3.9,
            length(p - vec2(30.0, 42.0)));
        float footer = 1.0 - smoothstep(-0.8, 0.8,
            round_box(p - vec2(22.0, 683.0), vec2(12.0, 26.0), 9.0));
        float footer_inset = 1.0 - smoothstep(-0.8, 0.8,
            round_box(p - vec2(22.0, 683.0), vec2(8.7, 22.0), 6.0));
        float symbol = max(max(left_outer - left_inner, right_body),
                           max(left_dot, footer - footer_inset));
        vec3 white = vec3(0.96, 0.97, 1.0);
        vec3 ink = mix(red, white, clamp(symbol, 0.0, 1.0));
        ink = mix(ink, red, right_dot * 0.92);
        color = vec4(ink, v_top.a);
    }
    else if (shape == 10)
    {
        // An inked side wall, not a red overlay on a flat poster. Near/far
        // planes receive different light; a narrow front-facing lip catches
        // the rim light without turning the whole wall bright white.
        float rim = exp(-70.0 * min(v_st.x, 1.0 - v_st.x));
        float broad = 0.77 + 0.20 * (1.0 - v_st.x);
        color = mix(v_top, v_bottom, v_st.x);
        color.rgb = min(vec3(1.0), color.rgb * broad +
            vec3(0.44, 0.34, 0.36) * rim * 0.18);
    }
    else if (shape == 12)
    {
        // Rounded top/bottom plastic cap: half-transparent near rim, brighter
        // distal reflection, subdued middle to retain physical depth.
        // Solid top/bottom surfaces: diffused light in the plastic, distinct
        // bright front-edge refraction, and a darker rear-facing inner wall.
        float front_glint = exp(-48.0 * v_st.y);
        float rear_shadow = smoothstep(0.58, 1.0, v_st.y);
        float near_edge = smoothstep(0.0, 0.02, v_st.x) *
                          smoothstep(0.0, 0.02, 1.0 - v_st.x);
        color = mix(v_top, v_bottom, v_st.y);
        color.rgb = min(vec3(1.0), color.rgb * (0.96 - 0.24 * rear_shadow) +
                        vec3(0.17, 0.19, 0.22) * front_glint);
        color.a *= near_edge * (0.86 + 0.10 * front_glint);
    }
    else if (shape == 13)
    {
        // Soft plastic with a curved normal-derived highlight and an
        // illuminated front rim, darkening naturally toward the rear plane.
        vec2 n = normalize(v_uv);
        vec2 key_light = normalize(vec2(-0.58, -0.82));
        vec2 secondary = normalize(vec2(0.92, -0.39));
        float diffuse = 0.48 + 0.37 * max(dot(n, key_light), 0.0);
        float highlight = pow(max(dot(n, key_light), 0.0), 20.0);
        float fill = 0.11 * max(dot(n, secondary), 0.0);
        // Curved corner normals interpolate across eight physical strips.
        // The highlight tracks their actual curvature, not a screen border.
        float near_glint = 0.20 * exp(-20.0 * v_st.x);
        float rear_shadow = 1.0 - 0.23 * v_st.x;
        vec4 material = mix(v_top, v_bottom, v_st.x);
        material.rgb = min(vec3(1.0), material.rgb *
            (diffuse + fill + near_glint) * rear_shadow +
            vec3(0.62, 0.72, 0.83) * highlight * 0.41);
        material.a *= 0.90 - 0.15 * v_st.x;
        color = material;
    }
    else if (shape == 11)
    {
        // One molded shell around the SAME paper, projected on its face.
        // Only the 12px RIGHT opening, 13px TOP and 13px BOTTOM are lit.
        // The rest is fully transparent, never a second overlay on the ink.
        float from_edge = (1.0 - v_st.x) * (v_half.x * 2.0);
        float from_cap = min(v_st.y, 1.0 - v_st.y) * (v_half.y * 2.0);
        float bevel = 1.0 - smoothstep(8.0, 13.0, from_edge);
        float outer_glint = exp(-0.5 * pow((from_edge - 2.3) / 1.25, 2.0));
        float inner_ridge = exp(-0.5 * pow((from_edge - 9.0) / 1.55, 2.0));
        float grazing = 0.15 + 0.20 * pow(abs(sin(v_params.x)), 1.5);
        // A visible molded front/rear cap line even when the horizontal
        // depth surface projects almost edge-on (especially at the bottom).
        float cap_band = 1.0 - smoothstep(11.5, 13.2, from_cap);
        float cap_outer = exp(-0.5 * pow((from_cap - 1.8) / 1.25, 2.0));
        float cap_inner = exp(-0.5 * pow((from_cap - 11.5) / 1.6, 2.0));
        float cap_sheen = 0.78 + 0.22 * cos(v_st.x * 5.8 + v_params.x);
        float cap_intensity = (0.53 * cap_band + 0.30 * cap_outer +
                               0.25 * cap_inner) * cap_sheen;
        float rim_intensity = (0.27 + grazing) * bevel +
                              0.44 * outer_glint + 0.22 * inner_ridge;
        // Fine manufacturing grain on PLASTIC ONLY, never on the scan.
        float grain = 0.96 + 0.04 * sin(v_st.y * 670.0);
        float sheen = 0.5 + 0.5 * sin(v_st.y * 7.0 + v_params.x * 0.65);
        vec3 material = mix(v_top.rgb, vec3(0.99, 0.995, 1.0),
                            0.29 + 0.19 * sheen);
        float shell = 1.0 - smoothstep(-1.0, 1.0,
                            round_box(v_local, v_half, 22.0));
        color = vec4(material, v_top.a * shell *
                     clamp(max(rim_intensity, cap_intensity) * grain,
                           0.0, 0.96));
    }
    else if (shape == 8)
    {
        float radius = min(v_params.x, min(v_half.x, v_half.y));
        float d = round_box(v_local, v_half, radius);
        color = caseTexture(v_uv) * fill;
        color.a *= clamp(0.5 - d / px, 0.0, 1.0);
    }
    else if (shape == 4)
    {
        vec2 pa = v_virtual - v_extra.xy;
        vec2 ba = v_extra.zw - v_extra.xy;
        float h = clamp(dot(pa, ba) / max(dot(ba, ba), 1e-6), 0.0, 1.0);
        float d = length(pa - ba * h) - 0.5 * v_params.y;
        color = vec4(fill.rgb, fill.a * clamp(0.5 - d / px, 0.0, 1.0));
    }
    else
    {
        float d = triangle(v_local, vec2(0.0, -v_half.y), vec2(-v_half.x, v_half.y),
                           vec2(v_half.x, v_half.y));
        if (v_params.y > 0.0)
            d = abs(d + 0.5 * v_params.y) - 0.5 * v_params.y;
        color = vec4(fill.rgb, fill.a * clamp(0.5 - d / px, 0.0, 1.0));
    }
    if (color.a <= 0.0)
        discard;
#ifdef EDEN_CASE_VULKAN
    if(pc.output_info.w>0.5)
        color.rgb=mix(color.rgb/12.92,pow((color.rgb+0.055)/1.055,vec3(2.4)),
                      greaterThan(color.rgb,vec3(0.04045)));
#endif
    frag_color = color;
}
)";

} // namespace Eden::LoadingCase
