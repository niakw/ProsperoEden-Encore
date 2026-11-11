// SPDX-License-Identifier: GPL-3.0-or-later
//
// Real 6-core kernel ABI witness compiled into core, audio_core and
// video_core on PS5. R457's original audio TU used a 4-core KProcess layout,
// reading m_memory from +0x160 while KProcess constructed it at +0x1b0.
// A link success alone cannot detect this C++ One Definition Rule violation.
#include <array>
#include <cstdint>
#include <type_traits>
#include <utility>

#include "core/hardware_properties.h"
#include "core/hle/kernel/k_process.h"

#ifdef PS5_NATIVE
static_assert(Core::Hardware::NUM_CPU_CORES == 6,
              "R457 KProcess ABI: all consumers must see six CPU cores");
static_assert(sizeof(std::array<void*, Core::Hardware::NUM_CPU_CORES>) ==
                  6 * sizeof(void*),
              "R457 KProcess ABI: per-core array layout drift");
static_assert(
    std::is_same_v<decltype(std::declval<Kernel::KProcess&>().GetMemory()),
                   Core::Memory::Memory&>,
    "R457 KProcess ABI: guest memory accessor contract changed");

// Compile an actual KProcess::GetMemory reference in every consumer target.
// No runtime call or guest memory access is made by this witness.
namespace {
[[maybe_unused]] std::uintptr_t KernelMemoryMemberOffset(
    Kernel::KProcess* process) noexcept {
    return reinterpret_cast<std::uintptr_t>(&process->GetMemory()) -
           reinterpret_cast<std::uintptr_t>(process);
}
} // namespace
#endif
