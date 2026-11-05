// SPDX-License-Identifier: GPL-3.0-or-later
#include "mihawk_native_session.h"
#include "mihawk_volk.h"
#include "diagnostics.h"
#include <array>
#include <cstdio>
#include <vector>

namespace Eden::FeatureLab {
namespace {
// Pinned MihawkGen v1 network: an unexpected size must never be loaded
// accidentally as an arbitrary memory blob.
constexpr std::size_t kModelBytes = 1'757'240;
}
MihawkNativeSession::~MihawkNativeSession() { Destroy(); }

bool MihawkNativeSession::Create(const MihawkSessionCreate& setup) noexcept {
    Destroy();
    if (!setup.instance_proc || !setup.instance || !setup.physical || !setup.device ||
        setup.width == 0 || setup.height == 0 || setup.model_path.empty())
        return false;

    // Initialise the SAME Vulkan device as RendererVulkan. volk is
    // namespaced so Encore's RADV vkGetInstanceProcAddr stays a real function.
    volkInitializeCustom(setup.instance_proc);
    volkLoadInstance(setup.instance);
    volkLoadDevice(setup.device);
    if (!vkCreateImage || !vkCmdPipelineBarrier || !vkCmdDispatch ||
        !vkCreateComputePipelines || !vkQueueSubmit || !vkDeviceWaitIdle) {
        Eden::Report("framegen", "native Vulkan dispatch missing for MihawkGen");
        return false;
    }

    FILE* f = std::fopen(setup.model_path.c_str(), "rb");
    if (!f) {
        Eden::Report("framegen", "MihawkGen model is absent from the application");
        return false;
    }
    if (std::fseek(f, 0, SEEK_END) != 0) { std::fclose(f); return false; }
    const long length = std::ftell(f);
    if (length != static_cast<long>(kModelBytes) || std::fseek(f, 0, SEEK_SET) != 0) {
        std::fclose(f);
        Eden::Report("framegen", "MihawkGen model has an unexpected size");
        return false;
    }
    std::vector<std::uint8_t> bytes;
    try {
        bytes.resize(kModelBytes);
    } catch (...) {
        std::fclose(f);
        Eden::Report("framegen", "MihawkGen model allocation failed");
        return false;
    }
    const bool read_ok = std::fread(bytes.data(), 1, bytes.size(), f) == bytes.size();
    const bool close_ok = std::fclose(f) == 0;
    if (!read_ok || !close_ok) return false;

    fg_create_info init{};
    init.device = setup.device;
    init.physical_device = setup.physical;
    init.width = setup.width;
    init.height = setup.height;
    init.slots = 1;  // serial GPU fence gate also protects descriptor reuse
    init.output_format = VK_FORMAT_R8G8B8A8_UNORM;
    std::array<char, 256> error{};
    if (fg_context_create(&init, &context_, error.data(), error.size()) != VK_SUCCESS) {
        context_ = nullptr;
        Eden::Report("framegen", error.data());
        return false;
    }
    if (fg_context_load_network(context_, bytes.data(), bytes.size(),
                                error.data(), error.size()) != VK_SUCCESS) {
        Eden::Report("framegen", error.data());
        Destroy();
        return false;
    }
    model_loaded_ = true;
    const auto alloc = owned_.Create(setup.device, setup.physical, setup.width, setup.height,
                                     setup.compositor_format);
    if (alloc != MihawkAllocateError::None) {
        Eden::Report("framegen", "MihawkGen private history allocation failed");
        Destroy();
        return false;
    }
    Eden::Report("framegen", "MihawkGen private Vulkan history and neural context initialized");
    return true;
}

void MihawkNativeSession::Destroy() noexcept {
    // Never release neural pipelines or descriptor sets while GPU reads are
    // still running. The renderer owns VkDevice and destroys us first.
    if (context_) {
        // The owning renderer already waits idle at shutdown; if invoked
        // earlier, the private resource destructor supplies device wait.
        owned_.Destroy();
        fg_context_destroy(context_);
        context_ = nullptr;
    } else {
        owned_.Destroy();
    }
    model_loaded_ = false;
    // Destroy waited for private resources to finish. All GPU serials
    // associated with this allocation generation are now retired.
    encoder_.ResetAfterDeviceIdle();
}
} // namespace Eden::FeatureLab
