// SPDX-License-Identifier: MIT
// R09 CPU-only gate for an authentic user-owned Original NRMODEL1 pack.
// No weight bytes are committed, uploaded to CI, or printed in diagnostics.
#include "video_core/renderer_vulkan/nr_rdna2_session_preflight.h"
#include <cstdint>
#include <fstream>
#include <iostream>
#include <iterator>
#include <string>

int main(int argc, char** argv) {
    if (argc == 2 && std::string(argv[1]) == "--help") {
        std::cout << "Usage: r09_real_original_preflight MODEL_PATH ORIGINAL_PLAN.txt\n";
        return 0;
    }
    if (argc != 3) {
        std::cerr << "Pass a private user NRMODEL1 file and a public native plan.\n";
        return 64;
    }
    std::ifstream plan_file(argv[2], std::ios::binary);
    if (!plan_file) {
        std::cerr << "R09_REAL_ORIGINAL_PREFLIGHT_PLAN_MISSING\n";
        return 65;
    }
    const std::string text((std::istreambuf_iterator<char>(plan_file)),
                           std::istreambuf_iterator<char>());
    namespace NR = Eden::Graphics::NeuralRDNA2;
    NR::R09SessionCPUPlan ready{};
    if (!NR::PreflightR09Session(argv[1], text,
                                 1920u, 1080u, 1920u, 1080u, ready)) {
        std::cerr << "R09_REAL_ORIGINAL_PREFLIGHT_REJECTED\n";
        return 66;
    }
    if (ready.model.Entries().size() != 599u || ready.graph.count != 4u ||
        ready.routes.run_count != 2u || ready.vit_route.count != 8u ||
        ready.raster_width != 1080u || ready.raster_height != 1920u) {
        std::cerr << "R09_REAL_ORIGINAL_PREFLIGHT_GRAPH_MISMATCH\n";
        return 67;
    }
    // Do not describe the index/graph as GPU-ready until all four
    // genuine upsample matrices and recovered learned gain vectors load.
    if (!NR::ValidateR09LearnedUpsampleInputs(ready)) {
        std::cerr << "R09_REAL_ORIGINAL_LEARNED_UPSAMPLE_PREFLIGHT_REJECTED\\n";
        return 68;
    }
    std::cout << "R09_REAL_ORIGINAL_CPU_GRAPH_PREFLIGHT_PASS "
              << ready.model.Entries().size() << " tensors, "
              << ready.graph.count << " UNet depths, "
              << ready.routes.run_count << " Split runs, "
              << ready.vit_route.count << " ViT blocks\n";
    std::cout << "This is CPU-only. No Vulkan dispatch or final image is proven.\n";
    return 0;
}
