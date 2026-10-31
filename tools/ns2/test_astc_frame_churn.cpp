// SPDX-License-Identifier: GPL-3.0-or-later
// N61 deterministic, synthetic frame-churn ASTC freshness/staging stress.
#include <array>
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <span>
#include <vector>
#include "video_core/texture_cache/ns2_astc_staging_bridge.h"

using namespace Eden::NS2::Eglantine;
constexpr std::uint64_t base=0x400000;
constexpr std::uint64_t stride=21ULL<<20;
constexpr std::uint32_t count=68;
struct Snapshot { std::uint32_t layer; std::uint64_t epoch; };
int main() {
    AstcDirtyLayerPlanner planner(base,stride*count,stride,count,0,64ULL<<20);
    assert(planner.Valid() && planner.ResetAfterFullUpload());
    std::array<std::uint64_t,count> guest{};
    std::array<std::uint64_t,count> rendered{};
    std::uint64_t rng=0x9e3779b97f4a7c15ULL;
    std::uint64_t frames=0, partial=0, races=0, fallbacks=0, transferred=0;
    auto next=[&] {
        rng^=rng<<13;rng^=rng>>7;rng^=rng<<17;return rng;
    };
    for(std::uint32_t frame=0;frame<2400;++frame) {
        const std::uint32_t changed=1+static_cast<std::uint32_t>(next()%5);
        for(std::uint32_t i=0;i<changed;++i) {
            const auto layer=static_cast<std::uint32_t>(next()%count);
            ++guest[layer];
            assert(planner.MarkWrite(base+std::uint64_t{layer}*stride+16,256));
        }
        const bool fail=(frame>0 && frame%149==0);
        const bool race=(frame>0 && frame%47==0 && !fail);
        bool failed_once=false, raced=false;
        std::vector<Snapshot> staged;
        std::uint64_t batch_bytes=0, bytes_staged=0;
        auto result=UploadAstcDirtyLayerBatches(planner,base,
            [&](std::uint32_t, std::uint64_t total) {
                assert(total<=64ULL<<20 && total>=stride);
                batch_bytes=total;
                staged.clear();
                bytes_staged=0;
                return true;
            },
            [&](std::uint64_t address,std::uint64_t offset,std::uint64_t bytes) {
                assert(address>=base && address<base+count*stride);
                const auto index=static_cast<std::uint32_t>((address-base)/stride);
                assert(index<count && (address-base)%stride==0);
                assert(bytes==stride && offset==bytes_staged);
                assert(bytes<=batch_bytes-offset);
                bytes_staged+=bytes;
                if(fail && !failed_once) { failed_once=true;return false; }
                staged.push_back({index,guest[index]});
                return true;
            },
            [&](std::uint32_t, std::span<const std::uint32_t> layers) {
                assert(staged.size()==layers.size());
                for(std::size_t i=0;i<layers.size();++i) {
                    assert(staged[i].layer==layers[i]);
                    rendered[layers[i]]=staged[i].epoch;
                }
                if(race && !raced) {
                    // An actual CPU write while a Vulkan batch is being decoded.
                    ++guest[67];
                    assert(planner.MarkWrite(base+67ULL*stride+32,96));
                    raced=true;
                }
                return true;
            });
        if(fail) {
            assert(failed_once && result.status==AstcTransferStatus::ReadFailure);
            assert(planner.Snapshot().status==LayerPlanStatus::FullUpload);
            rendered=guest; // explicit traditional full-image fallback
            assert(planner.ResetAfterFullUpload());
            ++fallbacks;
        } else if(race) {
            assert(raced && result.status==AstcTransferStatus::ConcurrentWrite);
            assert(planner.Snapshot().status==LayerPlanStatus::Partial);
            ++races;
        } else {
            assert(result.status==AstcTransferStatus::Completed);
            assert(planner.Snapshot().status==LayerPlanStatus::NoChanges);
            for(std::uint32_t layer=0;layer<count;++layer) assert(guest[layer]==rendered[layer]);
            transferred+=result.uploaded_bytes;
            ++partial;
        }
        ++frames;
    }
    assert(frames==2400 && fallbacks>=10 && races>=35 && partial>=2300);
    assert(transferred>0 && transferred<frames*count*stride);
    std::printf("N61_ASTC_SYNTHETIC_FRAME_CHURN_PASS frames=%llu partial=%llu races=%llu fallbacks=%llu bytes=%llu\n",
      static_cast<unsigned long long>(frames),static_cast<unsigned long long>(partial),
      static_cast<unsigned long long>(races),static_cast<unsigned long long>(fallbacks),
      static_cast<unsigned long long>(transferred));
}
