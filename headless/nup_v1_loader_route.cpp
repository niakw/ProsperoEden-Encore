// SPDX-License-Identifier: GPL-3.0-or-later
// Native NUP v1 loader-factory bridge, selected in the unified PS5 build.
// All ordinary NS1/NS2 formats continue through the original vendor factory.
#include "nup_v1_native_loader.h"
#include "nup_v1_native_vfs.h"

#include <cstdio>
#include <memory>
#include <string>
#include <utility>

#include "core/file_sys/common_funcs.h"
#include "core/loader/loader.h"

namespace Loader {

// The original pinned loader.cpp is compiled with the source-local
// GetLoader=EdenOriginalGetLoader token alias. No vendor C++ is rewritten,
// and all non-NUP requests continue to use the exact existing implementation.
std::unique_ptr<AppLoader> EdenOriginalGetLoader(
    Core::System& system, FileSys::VirtualFile file,
    u64 program_id, std::size_t program_index);

std::unique_ptr<AppLoader> GetLoader(
    Core::System& system, FileSys::VirtualFile file,
    u64 program_id, std::size_t program_index) {
    if (!file) return nullptr;
    if (!Eden::NupV1::Native::HasNupV1Header(file)) {
        // The file extension is NOT an admission rule. It is used only for
        // one targeted rejection diagnostic: Core status 2 otherwise hides
        // whether a purported NUP failed before the TOC was ever parsed.
        const auto name = file->GetName();
        if (name.ends_with(".nup") || name.ends_with(".NUP")) {
            std::fprintf(stderr, "EDEN_NUP_REJECT stage=signature_or_header\n");
        }
        return EdenOriginalGetLoader(system, std::move(file),
                                     program_id, program_index);
    }
    // A NUP bundles one effective application. Never select a guessed NCA
    // program index, and never fall back to interpreting failed NUP as NSP.
    if (program_index != 0) {
        std::fprintf(stderr, "EDEN_NUP_REJECT stage=program_index\n");
        return nullptr;
    }
    std::string error;
    auto loader = Eden::NupV1::Native::NupAppLoader::Open(
        std::move(file), &error);
    if (!loader) {
        std::fprintf(stderr, "EDEN_NUP_REJECT stage=archive reason=%s\n",
                     error.empty() ? "not_admitted" : error.c_str());
        return nullptr;
    }
    u64 actual_program_id{};
    if (loader->ReadProgramId(actual_program_id) != ResultStatus::Success) {
        std::fprintf(stderr, "EDEN_NUP_REJECT stage=program_identity\n");
        return nullptr;
    }
    constexpr u64 PlatformMask = 0xFF00000000000000ULL;
    constexpr u64 LowTitleMask = ~PlatformMask;
    const bool matching_ns2_edition =
        (program_id & PlatformMask) == 0x0100000000000000ULL &&
        (actual_program_id & PlatformMask) == 0x0400000000000000ULL &&
        (actual_program_id & LowTitleMask) == ((program_id + 1) & LowTitleMask);
    if (program_id != 0 &&
        FileSys::GetBaseTitleID(program_id) !=
            FileSys::GetBaseTitleID(actual_program_id) && !matching_ns2_edition) {
        std::fprintf(stderr, "EDEN_NUP_REJECT stage=program_id_mismatch\n");
        return nullptr;
    }
    return loader;
}

} // namespace Loader
