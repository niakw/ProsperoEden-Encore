// SPDX-License-Identifier: MIT
// Research-only proposed optimization admission. NOT wired into Encore.
// The existing native GMMU owner has NO demonstrated read lease spanning
// all descriptor stages. Never deploy this model until that lease exists.
#include <array>
#include <cassert>
#include <cstdint>
#include <iostream>
#include <limits>
#include <mutex>
#include <optional>
#include <shared_mutex>
#include <unordered_map>

namespace {
using u64 = std::uint64_t;
using u32 = std::uint32_t;
constexpr u64 Page = 4096;
constexpr u64 Limit = u64{1} << 49;
constexpr u64 Cap = 256ULL * 1024 * 1024;
struct Owner {
    mutable std::shared_mutex mutex;
    std::unordered_map<u64, u64> page_to_cpu;
    struct ReadLease {
        const Owner& owner;
        std::shared_lock<std::shared_mutex> lock;
        explicit ReadLease(const Owner& o) : owner(o), lock(o.mutex) {}
    };
    [[nodiscard]] ReadLease Acquire() const { return ReadLease{*this}; }
    u64 process_generation{1};
    u64 map_revision{1};
    void Set(u64 gpu_page, std::optional<u64> cpu_page) {
        std::unique_lock lock{mutex};
        if (cpu_page) page_to_cpu[gpu_page / Page] = *cpu_page;
        else page_to_cpu.erase(gpu_page / Page);
        ++map_revision;
    }
    void NewProcess() {
        std::unique_lock lock{mutex};
        ++process_generation;
        ++map_revision;
        page_to_cpu.clear();
    }
    std::optional<u64> LookupUnderLease(u64 address, u64& probes) const {
        ++probes;
        auto it = page_to_cpu.find(address / Page);
        if (it == page_to_cpu.end()) return {};
        return it->second + (address % Page);
    }
};
struct Key { const Owner* owner{}; u64 generation{}, revision{}, address{}; u32 bytes{}; };
struct Entry { Key key{}; bool proven{}; };
class Memo {
    std::array<Entry, 16> entries{};
    u64 underlying_lookups{};
    u64 cache_hits{};
    static constexpr std::size_t Slot(u64 addr, u32 size) {
        return ((addr >> 12) ^ (addr >> 20) ^ size) & 15;
    }
public:
    // A real read lease MUST cover both the check and use of the result.
    // We hold it for the duration of this synthetic check only. DO NOT use
    // a cached result across Vulkan submission or any unlocked callback.
    bool CheckUnderLease(const Owner::ReadLease& lease, u64 address, u32 bytes) {
        const Owner& owner = lease.owner;
        if (!address || !bytes || bytes > Cap || address >= Limit ||
            bytes > Limit - address) return false;
        auto& entry = entries[Slot(address, bytes)];
        const Key key{&owner, owner.process_generation, owner.map_revision, address, bytes};
        const bool hit = entry.proven && entry.key.owner == key.owner &&
            entry.key.generation == key.generation && entry.key.revision == key.revision &&
            entry.key.address == key.address && entry.key.bytes == key.bytes;
        if (hit) { ++cache_hits; return true; }
        const auto map = [&](u64 x) { return owner.LookupUnderLease(x, underlying_lookups); };
        const auto start = map(address);
        if (!start || *start > std::numeric_limits<u64>::max() - bytes) return false;
        for (u64 delta = Page - (address & (Page - 1)); delta < bytes; delta += Page) {
            const auto page = map(address + delta);
            if (!page || *page != *start + delta) return false;
        }
        const auto last = map(address + bytes - 1);
        if (!last || *last != *start + bytes - 1) return false;
        entry = {key, true};
        return true;
    }
    u64 Probes() const { return underlying_lookups; }
    u64 Hits() const { return cache_hits; }
};
}

int main() {
    int tests{};
    const auto check = [&](bool ok) { assert(ok); ++tests; };
    Owner owner;
    constexpr u64 gpu = 0x100000;
    constexpr u64 cpu = 0x50000000;
    for (u64 i = 0; i < 8192; ++i) owner.Set(gpu + i * Page, cpu + i * Page);
    Memo memo;
    { const auto lease = owner.Acquire();
      check(memo.CheckUnderLease(lease, gpu, 32U * 1024 * 1024));
      check(memo.Probes() == 8193);
      for (int i = 0; i < 5; ++i) check(memo.CheckUnderLease(lease, gpu, 32U * 1024 * 1024)); }
    check(memo.Probes() == 8193); // Five redundant walks eliminated, under lease.
    check(memo.Hits() == 5);
    owner.Set(gpu + 4096, cpu + 9999 * Page);
    check(!memo.CheckUnderLease(owner.Acquire(), gpu, 32U * 1024 * 1024)); // Unmapped/non-contiguous rejected.
    check(memo.Probes() > 8193); // Revision invalidated cached success.
    owner.Set(gpu + 4096, cpu + 4096);
    check(memo.CheckUnderLease(owner.Acquire(), gpu, 32U * 1024 * 1024));
    owner.Set(gpu, {});
    check(!memo.CheckUnderLease(owner.Acquire(), gpu, 32U * 1024 * 1024));
    owner.Set(gpu, cpu);
    check(memo.CheckUnderLease(owner.Acquire(), gpu, 32U * 1024 * 1024));
    owner.NewProcess();
    check(!memo.CheckUnderLease(owner.Acquire(), gpu, 32U * 1024 * 1024)); // Old GPU VA not sufficient.
    check(!memo.CheckUnderLease(owner.Acquire(), 0, 4096));
    check(!memo.CheckUnderLease(owner.Acquire(), Limit - 4096, 8192));
    check(!memo.CheckUnderLease(owner.Acquire(), gpu, 256U * 1024 * 1024 + 1));
    owner.Set(gpu, cpu);
    check(memo.CheckUnderLease(owner.Acquire(), gpu, 1));
    check(memo.CheckUnderLease(owner.Acquire(), gpu, 1));
    check(!memo.CheckUnderLease(owner.Acquire(), gpu, 8192)); // No mapped second page.
    check(memo.Hits() >= 6);
    std::cout << "PASS: " << tests << " leased GMMU memo research contracts; "
              << "first 32MiB scan=8193, six scans under unchanged lease=8193 probes\n";
}
