// SPDX-FileCopyrightText: Copyright 2026 Eden Emulator Project
// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once

// Isolated ABI and allocation ledger for NS2 GPU worker TIPC 211/212/213.
// NO guest handler is registered here. A future native 4-KiB NVDRV backend
// must commit a map only after successful GPU page-table modification.
#include <array>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <map>
#include <optional>
#include <span>
#include <utility>

#include "core/hle/service/nvdrv/devices/native_gpu_kind.h"

namespace Service::AM::GpuWorkerProtocol {
using U8 = std::uint8_t;
using U32 = std::uint32_t;
using U64 = std::uint64_t;
constexpr U64 PageSize = 0x1000;
constexpr U32 MaxNotifications = 64;
constexpr U32 MaxDevices = 256;
constexpr std::size_t MaxMappings = 4096;

constexpr U64 Pair(U32 lo, U32 hi) {
    return U64{lo} | (U64{hi} << 32);
}
constexpr bool Aligned(U64 number) { return (number & (PageSize - 1)) == 0; }
constexpr std::optional<U64> RangeSize(U64 begin, U64 end) {
    // Inclusive end. A wrapped end+1 must never become a zero-size mapping.
    if (!Aligned(begin) || end < begin || end == std::numeric_limits<U64>::max())
        return {};
    const U64 size = end - begin + 1;
    if (!size || !Aligned(size) || (size >> 12) > std::numeric_limits<U32>::max())
        return {};
    return size;
}

struct Map4K {
    U32 address_space{};
    U32 memory{};
    U32 device{};
    U32 notification{};
    U64 address{};
    U64 size{};
    U64 memory_offset{};
    U8 selected_kind{};
    U8 backend_kind{};
    U8 cache{};
    U8 sync{};
};
struct Unmap4K {
    U32 address_space{};
    U32 notification{};
    U64 address{};
    U64 size{};
    U8 sync{};
};
struct Modify4K {
    U32 address_space{};
    U32 notification{};
    U64 address{};
    U64 size{};
    U8 selected_kind{};
    U8 backend_kind{};
    U8 sync{};
};

// SDK TIPC byte parameters can carry arbitrary high padding bits.
// Mirror upstream's low-byte handling without accepting invalid payloads.
inline std::optional<Map4K> DecodeMap(std::span<const U32> packet) {
    if (packet.size() != 18 || packet[0] != 0xe3 || packet[1] != 16 ||
        !packet[2] || !packet[7] || !(packet[15] & 0xff) ||
        packet[17] >= MaxNotifications || (packet[10] & 0xff) != 0 ||
        (packet[11] & 0xff) > 1 || (packet[14] & 0xff) != 0 ||
        (packet[16] & 0xff) > 1)
        return {};
    const U64 begin = Pair(packet[3], packet[4]);
    const auto size = RangeSize(begin, Pair(packet[5], packet[6]));
    const U64 offset = Pair(packet[8], packet[9]);
    if (!size || !Aligned(offset) || offset > std::numeric_limits<U64>::max() - *size)
        return {};
    const auto kind = Nvidia::Devices::SelectNativeMemoryKind(
        static_cast<U8>(packet[12]), static_cast<U8>(packet[13]));
    if (!kind) return {};
    return Map4K{
        packet[2], packet[7], packet[15] & 0xff, packet[17],
        begin, *size, offset, kind->selected, kind->backend,
        static_cast<U8>(packet[11]), static_cast<U8>(packet[16])};
}
inline std::optional<Unmap4K> DecodeUnmap(std::span<const U32> packet) {
    if (packet.size() != 9 || packet[0] != 0xe5 || packet[1] != 7 ||
        !packet[2] || (packet[7] & 0xff) > 1 || packet[8] >= MaxNotifications)
        return {};
    const U64 begin = Pair(packet[3], packet[4]);
    const auto size = RangeSize(begin, Pair(packet[5], packet[6]));
    if (!size) return {};
    return Unmap4K{packet[2], packet[8], begin, *size,
                   static_cast<U8>(packet[7])};
}
inline std::optional<Modify4K> DecodeModify(std::span<const U32> packet) {
    if (packet.size() != 11 || packet[0] != 0xe4 || packet[1] != 9 ||
        !packet[2] || (packet[9] & 0xff) > 1 || packet[10] >= MaxNotifications)
        return {};
    const U64 begin = Pair(packet[3], packet[4]);
    const auto size = RangeSize(begin, Pair(packet[5], packet[6]));
    if (!size) return {};
    const auto kind = Nvidia::Devices::SelectNativeMemoryKind(
        static_cast<U8>(packet[7]), static_cast<U8>(packet[8]));
    if (!kind) return {};
    return Modify4K{packet[2], packet[10], begin, *size, kind->selected,
                    kind->backend, static_cast<U8>(packet[9])};
}

struct Mapping {
    U32 address_space{};
    U32 memory{};
    U32 device{};
    U64 address{};
    U64 size{};
    U8 selected_kind{};
    U8 backend_kind{};
};

enum class LedgerStatus {
    Success,
    Invalid,
    Overlap,
    NotFound,
    OutOfResource,
};

// No allocation or GPU command is made by the ledger. All callbacks must
// run under the future worker's mutex, with a stable owner process + FD.
class MappingLedger {
public:
    LedgerStatus CanMap(const Map4K& request) const {
        if (!request.address_space || !request.memory || !request.device ||
            request.device >= MaxDevices || !request.size ||
            !Aligned(request.address) || !Aligned(request.size) ||
            !Aligned(request.memory_offset) ||
            request.address > std::numeric_limits<U64>::max() - request.size ||
            request.memory_offset > std::numeric_limits<U64>::max() - request.size)
            return LedgerStatus::Invalid;
        if (mappings.size() >= MaxMappings) return LedgerStatus::OutOfResource;
        const auto next = mappings.lower_bound({request.address_space, request.address});
        if (next != mappings.end() && next->first.first == request.address_space &&
            next->second.address - request.address < request.size)
            return LedgerStatus::Overlap;
        if (next != mappings.begin()) {
            const auto previous = std::prev(next);
            if (previous->first.first == request.address_space &&
                request.address - previous->second.address < previous->second.size)
                return LedgerStatus::Overlap;
        }
        return LedgerStatus::Success;
    }
    LedgerStatus RecordMapped(const Map4K& request) {
        const auto result = CanMap(request);
        if (result != LedgerStatus::Success) return result;
        const Mapping mapping{request.address_space, request.memory, request.device,
                              request.address, request.size, request.selected_kind,
                              request.backend_kind};
        mappings.emplace(std::make_pair(request.address_space, request.address), mapping);
        return LedgerStatus::Success;
    }
    LedgerStatus CanUnmap(const Unmap4K& request) const {
        if (!request.size || !Aligned(request.address) || !Aligned(request.size))
            return LedgerStatus::Invalid;
        const auto it = mappings.find({request.address_space, request.address});
        return it != mappings.end() && it->second.size == request.size
            ? LedgerStatus::Success : LedgerStatus::NotFound;
    }
    LedgerStatus RecordUnmapped(const Unmap4K& request) {
        const auto result = CanUnmap(request);
        if (result != LedgerStatus::Success) return result;
        mappings.erase({request.address_space, request.address});
        return LedgerStatus::Success;
    }
    LedgerStatus CanModify(const Modify4K& request) const {
        if (!request.size || !Aligned(request.address) || !Aligned(request.size) ||
            request.address > std::numeric_limits<U64>::max() - request.size)
            return LedgerStatus::Invalid;
        auto next = mappings.upper_bound({request.address_space, request.address});
        if (next == mappings.begin()) return LedgerStatus::NotFound;
        --next;
        const Mapping& m = next->second;
        if (m.address_space != request.address_space ||
            request.address < m.address || request.address - m.address >= m.size ||
            request.size > m.size - (request.address - m.address))
            return LedgerStatus::NotFound;
        return LedgerStatus::Success;
    }
    [[nodiscard]] std::size_t Count() const { return mappings.size(); }
private:
    std::map<std::pair<U32, U64>, Mapping> mappings;
};
} // namespace Service::AM::GpuWorkerProtocol
