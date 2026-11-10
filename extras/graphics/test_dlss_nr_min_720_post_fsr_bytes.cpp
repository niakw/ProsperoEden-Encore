// SPDX-License-Identifier: GPL-3.0-or-later
// Host-only byte calculations for current FSR EASU/RCAS + R09 720p output.
#include "dlss_nr_min_720_post_fsr_bytes.h"
#include <cassert>
#include <cstdint>
#include <iostream>
using namespace Eden::Graphics::DlssNrMin;
int main(){
    constexpr auto a=CountNominalPostFsrImages({1920u,1080u},3u);
    constexpr auto b=CountNominalPostFsrImages({2560u,1440u},3u);
    constexpr auto c=CountNominalPostFsrImages({3840u,2160u},3u);
    static_assert(a.valid&&b.valid&&c.valid);
    static_assert(a.nr_output_per_slot==14745600ull);
    static_assert(a.easu_per_slot==16588800ull);
    static_assert(b.easu_per_slot==29491200ull);
    static_assert(c.easu_per_slot==66355200ull);
    static_assert(a.per_slot==47923200ull);
    static_assert(b.per_slot==73728000ull);
    static_assert(c.per_slot==147456000ull);
    static_assert(a.all_slots==143769600ull);
    static_assert(b.all_slots==221184000ull);
    static_assert(c.all_slots==442368000ull);
    static_assert(!a.measured_gpu_vram&&!c.measured_gpu_vram);
    // Every additional image slot requires an additional 720p RGBA32F
    // output AND a fresh 4K RGBA16F EASU/RCAS pair.
    for(std::uint32_t count=1u;count<=8u;++count){
        const auto shape=CountNominalPostFsrImages({3840u,2160u},count);
        assert(shape.valid&&shape.slots==count);
        assert(shape.all_slots==shape.per_slot*count);
        assert(shape.easu_per_slot==shape.rcas_per_slot);
        assert(shape.nr_output_per_slot==14745600ull);
    }
    assert(!CountNominalPostFsrImages({3840u,2160u},0u).valid);
    assert(!CountNominalPostFsrImages({3840u,2160u},9u).valid);
    assert(!CountNominalPostFsrImages({4096u,2160u},3u).valid);
    assert(!CountNominalPostFsrImages({1280u,720u},3u).valid);
    assert(FitsNominalPostFsrReserve(c,512ull<<20,64ull<<20));
    assert(!FitsNominalPostFsrReserve(c,c.all_slots,64ull<<20));
    assert(!FitsNominalPostFsrReserve(c,c.all_slots,0ull));
    assert(!FitsNominalPostFsrReserve(c,0ull,64ull<<20));
    // Pure arithmetic capacity is necessary, never a claim of physical
    // GPU capacity or a sufficient admission for trained neural inference.
    static_assert(!kPs5MinRuntimeQualified);
    std::cout<<"R09_MIN_720_POST_FSR_SURFACES_PASS slots=3 "
             <<"4k_nominal_bytes="<<c.all_slots
             <<" 1440p_nominal_bytes="<<b.all_slots
             <<" 1080p_nominal_bytes="<<a.all_slots
             <<" measured_gpu_vram=NO runtime=DISABLED\n";
}
