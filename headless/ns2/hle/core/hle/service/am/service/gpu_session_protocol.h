// SPDX-FileCopyrightText: Copyright 2026 Eden Emulator Project
// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once

// Strict subset of the NS2 GPU-session TIPC command ABI.
// Sourced from 0x2593/Eden-NS2@5d2d3cf0 gpu_session.cpp; the execution
// backend, NVDRV fd lifetime and Kernel event ownership are NOT ported here.

#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>

namespace Service::AM::GpuSessionProtocol {
using U32 = std::uint32_t;
using U64 = std::uint64_t;

inline constexpr std::size_t MaxDevices = 256;
inline constexpr std::size_t MaxAddressSpaces = 8;
inline constexpr std::size_t MaxNotificationEvents = 64;
enum class Status {
    Success,
    InvalidPacket,
    Unsupported,
    NotFound,
    OutOfResource,
    InvalidState,
};
struct Device {
    U64 name{};
    U64 debug_label{};
};
struct CreateDeviceRequest {
    U64 name{};
    U64 debug_label{};
};
struct PartitionRequest {
    U32 address_space{};
    bool user{};
};
constexpr U64 ReadPair(U32 lo, U32 hi) {
    return U64{lo} | (U64{hi} << 32);
}
inline constexpr std::optional<CreateDeviceRequest> DecodeCreateDevice(
    std::span<const U32> packet) {
    if (packet.size() != 8 || packet[0] != 0x39 || packet[1] != 6 ||
        ReadPair(packet[4], packet[5]) != 0) {
        return std::nullopt;
    }
    return CreateDeviceRequest{ReadPair(packet[2], packet[3]),
                               ReadPair(packet[6], packet[7])};
}
inline constexpr std::optional<U32> DecodeDestroyDevice(std::span<const U32> packet) {
    if (packet.size() != 3 || packet[0] != 0x3a || packet[1] != 1 ||
        packet[2] == 0 || packet[2] >= MaxDevices) {
        return std::nullopt;
    }
    return packet[2];
}
inline constexpr bool IsGetNotificationRange(std::span<const U32> packet) {
    return packet.size() == 2 && packet[0] == 0x1b && packet[1] == 0;
}
inline constexpr std::optional<U32> DecodeEventIndex(std::span<const U32> packet,
                                                        U32 command) {
    // TIPC command 12 = 0x1c, command 21 = 0x25.
    if (packet.size() != 3 || packet[0] != command ||
        packet[1] != 1 || packet[2] >= MaxNotificationEvents) {
        return std::nullopt;
    }
    return packet[2];
}
inline constexpr std::optional<PartitionRequest> DecodeAddressSpacePartition(
    std::span<const U32> packet, U32 command) {
    if (command != 202 && command != 203) {
        return std::nullopt;
    }
    if (packet.size() != 3 || packet[0] != 16 + command ||
        packet[1] != 1) {
        return std::nullopt;
    }
    return PartitionRequest{packet[2], command == 203};
}
inline constexpr bool IsAcquireWorker(std::span<const U32> packet) {
    return packet.size() == 2 && packet[0] == 0x26 && packet[1] == 0;
}

class DeviceSlots {
public:
    // The upstream session reserves id 0 and selects the first empty id 1..255.
    struct Creation {
        Status status{Status::InvalidPacket};
        U32 id{};
    };
    Creation Create(std::span<const U32> packet) {
        if (packet.size() != 8 || packet[0] != 0x39 || packet[1] != 6)
            return {};
        if (ReadPair(packet[4], packet[5]) != 0)
            return {Status::Unsupported, 0};
        const auto request = DecodeCreateDevice(packet);
        if (!request)
            return {};
        for (std::size_t i = 1; i < devices.size(); ++i) {
            if (!devices[i]) {
                devices[i] = Device{request->name, request->debug_label};
                ++count;
                return {Status::Success, static_cast<U32>(i)};
            }
        }
        return {Status::OutOfResource, 0};
    }
    Status Destroy(std::span<const U32> packet) {
        const auto id = DecodeDestroyDevice(packet);
        if (!id)
            return Status::InvalidPacket;
        auto& selected = devices[*id];
        if (!selected)
            return Status::NotFound;
        selected.reset();
        --count;
        return Status::Success;
    }
    const std::optional<Device>& Get(U32 id) const {
        if (id >= MaxDevices)
            return devices[0];  // reserved null slot, no OOB
        return devices[id];
    }
    [[nodiscard]] std::size_t Count() const { return count; }
private:
    std::array<std::optional<Device>, MaxDevices> devices{};
    std::size_t count{};
};

class NotificationSlots {
public:
    Status MarkEvent(U32 index) {
        if (index >= MaxNotificationEvents)
            return Status::InvalidPacket;
        events[index] = true;
        return Status::Success;
    }
    Status RequestWorker(std::span<const U32> packet) const {
        const auto index = DecodeEventIndex(packet, 0x25);
        if (!index)
            return Status::InvalidPacket;
        return events[*index] ? Status::Success : Status::InvalidState;
    }
    bool HasEvent(U32 index) const {
        return index < MaxNotificationEvents && events[index];
    }
private:
    std::array<bool, MaxNotificationEvents> events{};
};

} // namespace Service::AM::GpuSessionProtocol
