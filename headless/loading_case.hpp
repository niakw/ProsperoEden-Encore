// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <cstddef>
#include <vector>
namespace Eden::LoadingCase {
inline constexpr float kFrontHold=1.20f,kTurn=0.72f,kBackHold=4.50f,kSettle=0.50f;
inline constexpr float kCycle=kFrontHold+2.0f*kTurn+kBackHold+kSettle;
inline constexpr float kPi=3.14159265358979323846f,kFrontYaw=0.52f,kBackYaw=kPi+0.18f;
inline constexpr int kAtlasWidth=2048,kAtlasHeight=1536;
inline constexpr std::array<std::array<float,4>,3> kPaperRects{{
    {0,0,960,1536},{960,0,960,1536},{1920,0,128,1536}
}};
inline float Ease(float t) noexcept {
    t=std::clamp(t,0.0f,1.0f);
    const float u=2.0f-2.0f*t;
    return t<0.5f?4.0f*t*t*t:1.0f-u*u*u*0.5f;
}
inline float Yaw(double elapsed,bool calm=false) noexcept {
    if(calm||!std::isfinite(elapsed))return kFrontYaw;
    const float t=static_cast<float>(std::fmod(std::max(0.0,elapsed),double(kCycle)));
    const float back=kFrontHold+kTurn,returning=back+kBackHold;
    if(t<kFrontHold)return kFrontYaw;
    if(t<back)return kFrontYaw+(kBackYaw-kFrontYaw)*Ease((t-kFrontHold)/kTurn);
    if(t<returning)return kBackYaw;
    if(t<returning+kTurn)return kBackYaw+(2.0f*kPi+kFrontYaw-kBackYaw)*Ease((t-returning)/kTurn);
    return 2.0f*kPi+kFrontYaw;
}
inline unsigned Pose(float yaw) noexcept {
    return (std::cos(yaw)<0.0f?2u:0u)+(std::sin(yaw)<0.0f?1u:0u);
}
inline constexpr std::array<float,4> kTemplateYaw{kFrontYaw,2.0f*kPi-kFrontYaw,kPi-0.18f,kBackYaw};
// Original six vec4 launcher Instance fields; slot 0 untextured, 1 front,
// 2 back, 3 spine. Textures are flat paper, never rendered box poses.
struct Quad { std::array<float,24> values{}; std::uint32_t slot{}; };
struct Scene { std::array<std::vector<Quad>,4> poses; bool reduce_motion{}; };
inline constexpr std::size_t kMaxQuads=32;
// DrawList runs deliberately share a texture between untextured and textured
// instances. Only the actual textured paper may populate an atlas slot.
inline bool UsesPaper(int shape,float texture_flag,std::uint32_t texture) noexcept {
    return texture!=0 && ((shape==9 && texture_flag>0.5f)||shape==14);
}
inline bool Valid(const Scene& s) noexcept {
    for(const auto& pose:s.poses){
        if(pose.empty()||pose.size()>kMaxQuads)return false;
        for(const auto& q:pose){
            if(q.slot>3)return false;
            for(float v:q.values)if(!std::isfinite(v))return false;
        }
    }
    return true;
}
struct alignas(16) Push { std::array<float,24> values{}; std::array<float,4> output{}; };
static_assert(sizeof(Push)==112);
struct Batch { std::array<Push,kMaxQuads> quads{}; std::size_t count{}; };
inline Batch MakeBatch(const Scene& scene,double seconds,float w,float h,bool srgb=false) noexcept {
    Batch result;
    if(w<=0||h<=0)return result;
    const float yaw=Yaw(seconds-1.0,scene.reduce_motion);
    const auto& pose=scene.poses[Pose(yaw)];
    if(pose.size()>result.quads.size())return result;
    const float width=454.0f*std::abs(std::cos(yaw))+44.0f*std::abs(std::sin(yaw));
    const float mid=601.0f;
    unsigned shadow=0;
    for(const auto& q:pose){
        auto& out=result.quads[result.count++];
        out.values=q.values;out.output={w,h,float(q.slot),srgb?1.0f:0.0f};
        if(int(q.values[19]+0.5f)==2){
            std::array<float,4> rect{};
            switch(shadow++){
            case 0:rect={mid-width*0.5f-72.0f,118.0f,width+144.0f,764.0f};break;
            case 1:rect={mid-width*0.5f-22.0f,132.0f,width+44.0f,724.0f};break;
            default:rect={mid-width*0.39f-50.0f,838.0f,width*0.78f+100.0f,86.0f};break;
            }
            std::copy(rect.begin(),rect.end(),out.values.begin());
        }else out.values[16]=yaw;
    }
    return result;
}
} // namespace Eden::LoadingCase
