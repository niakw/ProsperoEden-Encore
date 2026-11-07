// SPDX-License-Identifier: MIT
// R09 exact upstream manifest names, no NVIDIA proprietary weights.
#include "video_core/renderer_vulkan/nr_rdna2_model_manifest.h"
#include <algorithm>
#include <cassert>
#include <cstdint>
#include <string>
#include <vector>
using namespace Eden::Graphics::NeuralRDNA2;
template<std::size_t N>
static void CheckManifest(const std::array<std::string_view,N>& manifest,
                          R09ModelVariant expected_variant,
                          R09ModelVariant wrong_variant){
    std::vector<NeuralModelEntry> entries;
    entries.reserve(manifest.size());
    for(const auto name:manifest)
        entries.push_back({std::string(name),256u,2u});
    assert(ValidateR09ModelManifest(entries,expected_variant));
    assert(!ValidateR09ModelManifest(entries,wrong_variant));
    // The disk index preserves pack order, not sorted order.
    std::reverse(entries.begin(),entries.end());
    assert(ValidateR09ModelManifest(entries,expected_variant));
    entries.pop_back();
    assert(!ValidateR09ModelManifest(entries,expected_variant));
    // Replace the omitted name with another already present name.
    entries.emplace_back(std::string(manifest.back()),256u,2u);
    assert(!ValidateR09ModelManifest(entries,expected_variant));
    entries.front().name="unpacked/unknown-tensor.bin";
    assert(!ValidateR09ModelManifest(entries,expected_variant));
    entries.clear();
    for(const auto name:manifest)
        entries.push_back({std::string(name),256u,2u});
    entries[entries.size()/2u].size=0u;
    assert(!ValidateR09ModelManifest(entries,expected_variant));
}
int main(){
    static_assert(R09OriginalManifest.size()==599u);
    static_assert(R09CompactManifest.size()==255u);
    assert(std::is_sorted(R09OriginalManifest.begin(),
                          R09OriginalManifest.end()));
    assert(std::is_sorted(R09CompactManifest.begin(),
                          R09CompactManifest.end()));
    CheckManifest(R09OriginalManifest,R09ModelVariant::Original,
                  R09ModelVariant::Compact);
    CheckManifest(R09CompactManifest,R09ModelVariant::Compact,
                  R09ModelVariant::Original);
}
