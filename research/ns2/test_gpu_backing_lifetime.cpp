// SPDX-License-Identifier: MIT
// Research model of NS2 backing ownership / aliases, NOT production service code.
#include <algorithm>
#include <cassert>
#include <cstdint>
#include <iostream>
#include <limits>
#include <optional>
#include <vector>

namespace {
using u64 = std::uint64_t;
enum class Status { Ok, Invalid, NotFound, Busy };
struct Backing { u64 cpu{}, bytes{}, generation{}, pending_fences{}; bool alive{}; };
struct Alias { u64 gpu{}, cpu{}, bytes{}, generation{}; bool alive{}; };
constexpr bool Inside(u64 start, u64 len, u64 base, u64 extent) {
    return len && extent && start >= base && start - base < extent && len <= extent - (start - base);
}
constexpr bool Overlap(u64 a, u64 len_a, u64 b, u64 len_b) {
    return a < b + len_b && b < a + len_a;
}
struct Registry {
    std::vector<Backing> backings;
    std::vector<Alias> aliases;
    u64 next_epoch = 1;
    std::optional<u64> Register(u64 cpu, u64 bytes) {
        if (!bytes || cpu > std::numeric_limits<u64>::max() - bytes) return {};
        for (const auto& b : backings) {
            if (b.alive && Overlap(cpu, bytes, b.cpu, b.bytes)) return {};
        }
        const auto generation = next_epoch++;
        backings.push_back({cpu, bytes, generation, 0, true});
        return generation;
    }
    bool Map(u64 gpu, u64 cpu, u64 bytes, u64 generation) {
        if (!bytes || gpu > std::numeric_limits<u64>::max() - bytes ||
            cpu > std::numeric_limits<u64>::max() - bytes) return false;
        const auto owner = std::find_if(backings.begin(), backings.end(), [&](const Backing& b) {
            return b.alive && b.generation == generation && Inside(cpu, bytes, b.cpu, b.bytes);
        });
        if (owner == backings.end()) return false;
        for (const auto& a : aliases) {
            if (a.alive && Overlap(gpu, bytes, a.gpu, a.bytes)) return false;
        }
        aliases.push_back({gpu, cpu, bytes, generation, true});
        return true;
    }
    bool Resolve(u64 gpu, u64 generation) const {
        for (const auto& a : aliases) {
            if (!a.alive || a.generation != generation || !Inside(gpu, 1, a.gpu, a.bytes)) continue;
            for (const auto& b : backings) {
                if (b.alive && b.generation == a.generation &&
                    Inside(a.cpu + (gpu - a.gpu), 1, b.cpu, b.bytes)) return true;
            }
        }
        return false;
    }
    Status BeginFence(u64 generation) {
        for (auto& b : backings) if (b.alive && b.generation == generation) {
            ++b.pending_fences; return Status::Ok;
        }
        return Status::NotFound;
    }
    Status CompleteFence(u64 generation) {
        for (auto& b : backings) if (b.alive && b.generation == generation) {
            if (!b.pending_fences) return Status::Invalid;
            --b.pending_fences; return Status::Ok;
        }
        return Status::NotFound;
    }
    Status Destroy(u64 generation) {
        for (auto& b : backings) if (b.alive && b.generation == generation) {
            if (b.pending_fences) return Status::Busy;
            for (auto& a : aliases) if (a.generation == generation) a.alive = false;
            b.alive = false;
            return Status::Ok;
        }
        return Status::NotFound;
    }
};
}

int main() {
    int cases = 0;
    const auto check = [&](bool pass) { assert(pass); ++cases; };
    Registry r;
    auto first = r.Register(0x100000, 0x8000);
    check(first.has_value());
    check(r.Map(0x400000, 0x100000, 0x4000, *first));
    check(r.Map(0x500000, 0x102000, 0x4000, *first));
    check(r.Resolve(0x402000, *first) && r.Resolve(0x503000, *first));
    check(!r.Map(0x402000, 0x102000, 0x1000, *first)); // GPU alias collision.
    check(!r.Map(0x600000, 0x107000, 0x2000, *first)); // CPU backing gap.
    check(r.BeginFence(*first) == Status::Ok);
    check(r.Destroy(*first) == Status::Busy); // GPU work must finish first.
    check(r.Resolve(0x402000, *first));      // Busy must preserve mapping.
    check(r.CompleteFence(*first) == Status::Ok);
    check(r.Destroy(*first) == Status::Ok);
    check(!r.Resolve(0x402000, *first) && !r.Resolve(0x503000, *first));
    check(r.Destroy(*first) == Status::NotFound); // No double-free.
    auto second = r.Register(0x100000, 0x8000);
    check(second && *second != *first);
    check(!r.Map(0x400000, 0x100000, 0x1000, *first)); // Old epoch rejected.
    check(r.Map(0x400000, 0x100000, 0x1000, *second));
    check(r.Resolve(0x400000, *second) && !r.Resolve(0x400000, *first));
    check(!r.Register(0x101000, 0x1000)); // Overlapping live CPU registration.
    check(!r.Register(std::numeric_limits<u64>::max() - 4, 16));
    check(!r.Map(std::numeric_limits<u64>::max() - 4, 0x100000, 16, *second));
    auto disjoint = r.Register(0x200000, 0x1000);
    check(disjoint.has_value() && r.Map(0x900000, 0x200000, 0x1000, *disjoint));
    check(r.Destroy(*second) == Status::Ok && r.Resolve(0x900000, *disjoint));
    check(r.CompleteFence(*first) == Status::NotFound);
    std::cout << "PASS: " << cases << " NS2 backing lifetime research contracts\n";
}
