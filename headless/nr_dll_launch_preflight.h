// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
// One user-supplied DLL, one private cache. All CPU work is performed at
// game launch, never during the guest frame's Vulkan presentation.
#include "neural_video_policy.h"
#include "nr_dll_user_file.h"
#include "nr_dll_model_import.h"
#include "video_core/renderer_vulkan/nr_rdna2_model_file.h"
#include "video_core/renderer_vulkan/nr_rdna2_model_manifest.h"
#include <array>
#include <filesystem>
#include <string>
#include <system_error>

namespace Eden::Graphics {
struct R09LaunchModelResult {
    bool ready{};
    bool imported{};
    const char* reason{};
};
[[nodiscard]] inline bool R09UsableCachedPack(
    const std::filesystem::path& path,
    Eden::Graphics::NeuralRDNA2::R09ModelVariant variant) {
    namespace NR=Eden::Graphics::NeuralRDNA2;
    NR::NeuralModelFile model;
    if(!model.Open(path.string())||
       !NR::ValidateR09ModelManifest(model.Entries(),variant))
        return false;
    const auto* input=model.Find(
        "unpacked-preblock/block0.layer0.layer.input_lift.bin");
    const auto* output=model.Find(variant==NR::R09ModelVariant::Original?
        "unpacked-postblock/block70.layer0.layer.out_project.bin":
        "unpacked-postblock/block30.layer0.layer.out_project.bin");
    return input&&output&&input->size==1024u&&output->size==1024u;
}
[[nodiscard]] inline R09LaunchModelResult PrepareR09UserModel(
    int mode,const std::filesystem::path& user,
    const std::filesystem::path& config) {
    namespace fs=std::filesystem;
    namespace NR=Eden::Graphics::NeuralRDNA2;
    if(!Eden::NeuralVideo::IsDlss(mode))
        return {true,false,nullptr};
    const auto original=mode==Eden::NeuralVideo::kDlssOriginal;
    const auto variant=original?NR::R09ModelVariant::Original:
                                NR::R09ModelVariant::Compact;
    const auto dir=config/"neural";
    const auto cache=dir/(original?"original.nrmodel":"compact.nrmodel");
    const auto legacy=dir/(original?"dlssnr.bin":"dlssnr-small.bin");
    // Never accept an unverified file only because a matching filename
    // exists; cache missing/invalid must remain fail-closed.
    if(R09UsableCachedPack(cache,variant)||
       R09UsableCachedPack(legacy,variant))
        return {true,false,nullptr};
    if(!DlssNrUserFileLooksValid(user,config))
        return {false,false,"DLSS-NR: nvngx_dlssnr.dll missing or invalid. Place your own file in /data/prosperoeden/user/dlssnr/nvngx_dlssnr.dll."};
    // The user DLL available in this project contains authentic Original
    // only; never silently substitute its tensors for Compact.
    if(!original)
        return {false,false,"DLSS-NR Compact: compatible Compact weights are unavailable in the installed DLL; Original remains selectable."};
    const std::array<fs::path,4> candidates{
        user/kDlssNrRelative,
        config/"neural/nvngx_dlssnr.dll",
        config/"nvngx_dlssnr.dll",
        user/"nvngx_dlssnr.dll"};
    for(const auto& dll:candidates) {
        std::error_code ec;
        const auto status=fs::symlink_status(dll,ec);
        if(ec||fs::is_symlink(status)||!fs::is_regular_file(status))
            continue;
        const auto imported=Eden::NRDllImport::ImportOriginal(
            dll,cache,NR::R09OriginalManifest);
        if(!imported.imported)
            return {false,false,
                "DLSS-NR Original: user DLL is present but its neural weight resource failed integrity/import checks."};
        if(!R09UsableCachedPack(cache,variant))
            return {false,false,
                "DLSS-NR Original: imported cache failed the exact native model manifest."};
        return {true,true,nullptr};
    }
    return {false,false,
        "DLSS-NR: no safe regular user DLL could be opened for import."};
}
} // namespace Eden::Graphics
