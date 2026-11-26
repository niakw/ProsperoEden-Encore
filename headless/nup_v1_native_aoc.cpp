// SPDX-License-Identifier: GPL-3.0-or-later
#include "nup_v1_native_aoc.h"
#include <iterator>
#include <mutex>
#include <unordered_map>
#include <utility>
#include "core/file_sys/common_funcs.h"

namespace Eden::NupV1::Native {
namespace {
struct ActiveRegistry {
    std::mutex mutex;
    std::unordered_map<const Loader::AppLoader*,
                       std::shared_ptr<const AddOnIndex>> entries;
};
ActiveRegistry& Registry() {
    static ActiveRegistry registry;
    return registry;
}
} // namespace

void PublishActiveAddOns(const Loader::AppLoader* loader,
                         std::shared_ptr<const AddOnIndex> index) {
    if (!loader || !index) return;
    auto& registry = Registry();
    std::lock_guard guard(registry.mutex);
    registry.entries.insert_or_assign(loader, std::move(index));
}

void ForgetActiveAddOns(const Loader::AppLoader* loader) {
    auto& registry = Registry();
    std::lock_guard guard(registry.mutex);
    registry.entries.erase(loader);
}

std::shared_ptr<const AddOnIndex> ActiveAddOnsForLoader(
    const Loader::AppLoader* loader) {
    if (!loader) return {};
    auto& registry = Registry();
    std::lock_guard guard(registry.mutex);
    const auto found = registry.entries.find(loader);
    return found == registry.entries.end() ? nullptr : found->second;
}

std::shared_ptr<const AddOnIndex> SoleActiveAddOns() {
    auto& registry = Registry();
    std::lock_guard guard(registry.mutex);
    return registry.entries.size() == 1 ?
           registry.entries.begin()->second : nullptr;
}

AddOnIndex::AddOnIndex(std::shared_ptr<Mount> mount,
                       std::uint64_t caller_program_id,
                       std::optional<std::uint64_t> nacp_aoc_base_id) {
    if (!mount || !caller_program_id) return;
    owner_base_id_ = FileSys::GetBaseTitleID(caller_program_id);
    // ContentSet validates the exact selected NPDM for the NS1-to-NS2
    // Edition mapping and admits the AoC family (including a trusted NACP
    // override). Do not reject that mapping with a second platform check
    // or recompute its default AoC base from the 04-platform caller.
    auto content = std::make_unique<ContentSet>(
        mount, caller_program_id, nacp_aoc_base_id);
    const auto admitted_base = content->AddOnBaseId();
    if (!admitted_base) {
        owner_base_id_ = 0;
        return;
    }
    constexpr std::uint64_t PlatformMask = 0xFF00000000000000ULL;
    constexpr std::uint64_t LowTitleMask = ~PlatformMask;
    for (const auto& pkg : mount->Packages()) {
        if (pkg.kind == 2) continue;
        const auto package_base = FileSys::GetBaseTitleID(pkg.title_id);
        if (package_base == owner_base_id_) continue;
        // Only the verified NS2 Edition may cross the platform boundary.
        if ((owner_base_id_ & PlatformMask) != 0x0400000000000000ULL ||
            (package_base & PlatformMask) != 0x0100000000000000ULL ||
            (package_base & LowTitleMask) != (owner_base_id_ & LowTitleMask)) {
            owner_base_id_ = 0;
            return;
        }
    }
    aoc_base_id_ = admitted_base;
    content_ = std::move(content);
    for (const auto& addon : content_->AddOns()) {
        if (addon.title_id < *aoc_base_id_ ||
            addon.title_id - *aoc_base_id_ > FileSys::AOC_TITLE_ID_MASK)
            continue;
        indexes_.emplace(
            static_cast<std::uint32_t>(addon.title_id - *aoc_base_id_),
            addon.package_index);
    }
}

bool AddOnIndex::MatchesCaller(std::uint64_t caller_program_id) const {
    return content_ && caller_program_id &&
           FileSys::GetBaseTitleID(caller_program_id) == owner_base_id_;
}

std::optional<std::uint64_t> AddOnIndex::BaseId(
    std::uint64_t caller_program_id) const {
    return MatchesCaller(caller_program_id) ? aoc_base_id_ : std::nullopt;
}

std::size_t AddOnIndex::Count(std::uint64_t caller_program_id) const {
    return MatchesCaller(caller_program_id) ? indexes_.size() : 0;
}

std::vector<std::uint32_t> AddOnIndex::ListIds(
    std::uint64_t caller_program_id, std::size_t offset,
    std::size_t limit) const {
    std::vector<std::uint32_t> result;
    if (!MatchesCaller(caller_program_id) || offset >= indexes_.size() ||
        limit == 0) return result;
    auto it = indexes_.begin();
    std::advance(it, static_cast<std::ptrdiff_t>(offset));
    for (; it != indexes_.end() && result.size() < limit; ++it)
        result.push_back(it->first);
    return result;
}

FileSys::VirtualFile AddOnIndex::OpenRomFS(
    std::uint64_t caller_program_id, std::uint32_t aoc_index) const {
    if (!MatchesCaller(caller_program_id)) return {};
    const auto it = indexes_.find(aoc_index);
    return it == indexes_.end() ? FileSys::VirtualFile{} :
           content_->CreateAddOnRomFS(it->second);
}

} // namespace Eden::NupV1::Native
