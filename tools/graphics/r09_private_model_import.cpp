// SPDX-License-Identifier: MIT
// User-private CPU import for the last linked R09 Linux host binary.
// Reads the Windows NVIDIA DLL as data, never executes it, never emits weights.
#include "nr_dll_launch_preflight.h"
#include <filesystem>
#include <iostream>
#include <string>

int main(int argc, char** argv) {
    if (argc != 3 || std::string(argv[1]) == "--help") {
        std::cerr << "Usage: r09-private-model-import nvngx_dlssnr.dll original.nrmodel\n";
        return 64;
    }
    namespace NR = Eden::Graphics::NeuralRDNA2;
    namespace fs = std::filesystem;
    const fs::path dll = argv[1];
    const fs::path output = argv[2];
    std::error_code ec;
    const auto status = fs::symlink_status(dll, ec);
    if (ec || fs::is_symlink(status) || !fs::is_regular_file(status) ||
        fs::exists(output)) {
        std::cerr << "R09_PRIVATE_IMPORT_INPUT_OR_OUTPUT_REJECTED\n";
        return 65;
    }
    const auto result = Eden::NRDllImport::ImportOriginal(
        dll, output, NR::R09OriginalManifest);
    if (!result.imported) {
        fs::remove(output, ec);
        std::cerr << "R09_PRIVATE_IMPORT_REJECTED: " << result.reason << "\n";
        return 66;
    }
    if (!Eden::Graphics::R09UsableCachedPack(output, NR::R09ModelVariant::Original)) {
        fs::remove(output, ec);
        std::cerr << "R09_PRIVATE_IMPORT_599_SHA256_REJECTED\n";
        return 67;
    }
    fs::permissions(output, fs::perms::owner_read | fs::perms::owner_write,
                    fs::perm_options::replace, ec);
    if (ec) {
        fs::remove(output, ec);
        std::cerr << "R09_PRIVATE_IMPORT_PERMISSIONS_REJECTED\n";
        return 68;
    }
    std::cout << "R09_PRIVATE_ORIGINAL_599_SHA256_PASS\n";
    return 0;
}
