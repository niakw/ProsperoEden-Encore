// SPDX-License-Identifier: GPL-3.0-or-later
#include <cassert>
#include <cstdint>
#include <limits>
#include <vector>
#include "video_core/renderer_vulkan/ns2_astc_decode_preflight.h"
using Eden::NS2::Eglantine::AstcMipSlice;
using Eden::NS2::Eglantine::PreflightAstcLayerDecode;
int main() {
    const std::vector<std::uint32_t> layers{0,3,20,42,67};
    const std::vector<AstcMipSlice> mips{{0,0},{4096,1},{8192,2}};
    assert(PreflightAstcLayerDecode(68,3,21ULL<<20,5ULL*(21ULL<<20),layers,mips));
    assert(!PreflightAstcLayerDecode(68,3,21ULL<<20,4ULL*(21ULL<<20),layers,mips));
    assert(!PreflightAstcLayerDecode(68,3,0,5ULL*(21ULL<<20),layers,mips));
    assert(!PreflightAstcLayerDecode(68,0,21ULL<<20,5ULL*(21ULL<<20),layers,mips));
    assert(!PreflightAstcLayerDecode(68,3,21ULL<<20,5ULL*(21ULL<<20),
                                   std::vector<std::uint32_t>{0,0},mips));
    assert(!PreflightAstcLayerDecode(68,3,21ULL<<20,5ULL*(21ULL<<20),
                                   std::vector<std::uint32_t>{68},mips));
    assert(!PreflightAstcLayerDecode(68,3,21ULL<<20,5ULL*(21ULL<<20),layers,
                                   std::vector<AstcMipSlice>{{21ULL<<20,0}}));
    assert(!PreflightAstcLayerDecode(68,3,21ULL<<20,5ULL*(21ULL<<20),layers,
                                   std::vector<AstcMipSlice>{{0,0},{1,0}}));
    assert(!PreflightAstcLayerDecode(68,3,
        (std::numeric_limits<std::uint32_t>::max)()+1ULL,
        (std::numeric_limits<std::uint64_t>::max)(),layers,mips));
}
