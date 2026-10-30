// SPDX-FileCopyrightText: Copyright 2026 Eden Emulator Project
// SPDX-License-Identifier: GPL-3.0-or-later
// Scoped subset from supplied Eden-NS2 research patch. Do not include its newer
// sparse-map handling until the native sparse-remap owner has been ported.
#pragma once
#include <optional>
#include <span>
#include "common/common_types.h"

namespace Service::AM {
struct GpuMemoryRegistration {
    u64 begin;
    u64 end;
    u8 flags;
    u8 device;
};
constexpr std::optional<GpuMemoryRegistration> DecodeGpuMemoryRegistration(
    std::span<const u32> packet) {
    if (packet.size() < 8 || packet[0] != 0x75 || packet[1] != 6) return std::nullopt;
    // SDK packs flags/device into one low byte each; high bytes are padding.
    return GpuMemoryRegistration{u64{packet[2]} | (u64{packet[3]} << 32),
        u64{packet[4]} | (u64{packet[5]} << 32),
        static_cast<u8>(packet[6]), static_cast<u8>(packet[7])};
}
} // namespace Service::AM
