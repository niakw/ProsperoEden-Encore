// SPDX-License-Identifier: GPL-3.0-or-later
#include "room_directory.hpp"
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <algorithm>
#include <nlohmann/json.hpp>

namespace Eden::Multiplayer {
namespace {
std::string Text(const nlohmann::json& row, const char* key, std::size_t limit) {
    auto value = row.at(key).get<std::string>();
    if (value.size() > limit || value.find('\0') != std::string::npos)
        throw std::runtime_error("invalid room text");
    // Directory text is untrusted; keep it on its own row.
    for (char& c : value) if (static_cast<unsigned char>(c) < 32 || c == 127) c = ' ';
    return value;
}
// A directory entry must not point a console at its own network or at itself: loopback,
// private, carrier-grade NAT, link-local, multicast, reserved and broadcast are refused.
bool PublicAddress(const in_addr& address) {
    const std::uint32_t ip = ntohl(address.s_addr);
    const auto in = [ip](std::uint32_t network, int bits) { return (ip >> (32 - bits)) == (network >> (32 - bits)); };
    return !(in(0x00000000, 8) || in(0x0A000000, 8) || in(0x64400000, 10) || in(0x7F000000, 8) ||
             in(0xA9FE0000, 16) || in(0xAC100000, 12) || in(0xC0A80000, 16) || ip >= 0xE0000000);
}
// The JSON parser refuses the whole document for one malformed byte; a single room's bad name
// would hide every other room. Malformed UTF-8 becomes '?' before parsing.
std::string WellFormed(std::string_view text) {
    std::string result;
    result.reserve(text.size());
    for (std::size_t i = 0; i < text.size();) {
        const auto byte = [&](std::size_t k) { return static_cast<unsigned char>(text[i + k]); };
        const unsigned char lead = byte(0);
        const std::size_t length = lead < 0x80 ? 1 : lead >= 0xC2 && lead <= 0xDF ? 2 :
            lead >= 0xE0 && lead <= 0xEF ? 3 : lead >= 0xF0 && lead <= 0xF4 ? 4 : 0;
        bool valid = length != 0 && length <= text.size() - i;
        for (std::size_t k = 1; valid && k < length; ++k) valid = (byte(k) & 0xC0) == 0x80;
        // No overlong forms, surrogates or values past U+10FFFF.
        if (valid && length == 3) valid = !(lead == 0xE0 && byte(1) < 0xA0) && !(lead == 0xED && byte(1) > 0x9F);
        if (valid && length == 4) valid = !(lead == 0xF0 && byte(1) < 0x90) && !(lead == 0xF4 && byte(1) > 0x8F);
        if (valid) result.append(text, i, length);
        else result += '?';
        i += valid ? length : 1;
    }
    return result;
}
unsigned Number(const nlohmann::json& value, unsigned maximum) {
    if (!value.is_number_unsigned() || value.get<std::uint64_t>() > maximum)
        throw std::runtime_error("invalid room number");
    return value.get<unsigned>();
}
}

bool CanJoinPublicRoom(const PublicRoom& room) {
    if (!room.compatible || room.password || room.port == 0 ||
        room.capacity == 0 || room.players >= room.capacity)
        return false;
    in_addr addr{};
    return inet_pton(AF_INET, room.address.c_str(), &addr) == 1 &&
           PublicAddress(addr);
}

RoomDirectory ParseRoomDirectory(std::string_view body, unsigned protocol) {
    RoomDirectory result;
    if (body.size() > MaxDirectoryBytes) return {{}, "The public room list is too large."};
    try {
        // Limit nesting before the parser can exhaust the console stack.
        auto document = nlohmann::json::parse(WellFormed(body), [](int depth, auto, auto&) {
            if (depth > 16) throw std::runtime_error("room list nesting limit");
            return true;
        });
        const auto& rows = document.at("rooms");
        if (!rows.is_array()) throw std::runtime_error("invalid room list");
        if (rows.size() > 2048) return {{}, "The public room list is too large."};
        for (const auto& row : rows) {
            try {
                PublicRoom room;
                room.name = Text(row, "name", 512);
                room.game = Text(row, "preferredGameName", 512);
                room.address = Text(row, "address", 15);
                in_addr address{};
                if (room.name.empty() || inet_pton(AF_INET, room.address.c_str(), &address) != 1 ||
                    !PublicAddress(address))
                    throw std::runtime_error("unsupported address");
                room.port = static_cast<std::uint16_t>(Number(row.at("port"), 65535));
                room.capacity = Number(row.at("maxPlayers"), 65535);
                if (!room.port || !room.capacity) throw std::runtime_error("invalid room limits");
                room.password = row.at("hasPassword").get<bool>();
                room.compatible = Number(row.at("netVersion"), UINT32_MAX) == protocol;
                if (row.contains("players")) {
                    if (!row.at("players").is_array() || row.at("players").size() > 65535)
                        throw std::runtime_error("invalid player list");
                    room.players = static_cast<unsigned>(row.at("players").size());
                }
                if (room.players > room.capacity)
                    throw std::runtime_error("room population exceeds capacity");
                result.rooms.push_back(std::move(room));
            } catch (const std::exception&) { ++result.rejected; }
        }
        if (!rows.empty() && result.rooms.empty()) result.error = "No usable rooms were returned.";
        std::stable_sort(result.rooms.begin(), result.rooms.end(), [](const auto& a, const auto& b) {
            if (a.compatible != b.compatible) return a.compatible > b.compatible;
            if (a.players != b.players) return a.players > b.players; // where people are, first
            return a.name < b.name;
        });
    } catch (const std::exception&) { result = {{}, "The public room list could not be read."}; }
    return result;
}

} // namespace Eden::Multiplayer
