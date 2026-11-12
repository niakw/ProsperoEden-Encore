// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once

// Research-only accounting model. No PS5 allocation, mapping, fault handling,
// GPU aliasing or runtime opt-in is implemented by this header. Do NOT expose
// its reserved 12 GiB virtual capacity as committed physical guest RAM.
#include <cstddef>
#include <cstdint>
#include <limits>
#include <optional>
#include <utility>
#include <vector>

namespace Eden::PS5::GuestBacking {

constexpr std::uint64_t kGranule = 2ull << 20;
constexpr std::uint64_t kNs2Dram = 12ull << 30;

enum class State : std::uint8_t { Unmapped, Staging, Resident, Retiring };
struct Chunk {
    State state{State::Unmapped};
    std::int64_t physical{-1};
    std::uint64_t lease{};
};
struct Lease {
    std::uint64_t id{};
    std::size_t first{};
    std::size_t count{};
    std::size_t newcomers{};
};
struct Reclaim {
    std::size_t index{};
    std::int64_t physical{-1};
};

// SERIAL OWNER: the eventual native caller must lock across Begin -> Stage ->
// Publish or Begin -> Stage -> Abort -> ReleaseAcknowledged -> FinishAbort.
// Retiring physical owners cannot be reused until the kernel has confirmed
// CPU and GPU aliases are unmapped AND the owned physical block is released.
class Plan {
public:
    Plan(std::uint64_t virtual_bytes, std::uint64_t physical_budget)
        : virtual_bytes_{virtual_bytes}, budget_{physical_budget},
          chunks_(valid_size(virtual_bytes, physical_budget)
                      ? static_cast<std::size_t>(virtual_bytes / kGranule) : 0) {}

    [[nodiscard]] bool Valid() const noexcept { return !chunks_.empty(); }
    [[nodiscard]] std::uint64_t VirtualBytes() const noexcept { return virtual_bytes_; }
    [[nodiscard]] std::uint64_t UsedBytes() const noexcept { return used_chunks_ * kGranule; }
    [[nodiscard]] std::uint64_t BudgetBytes() const noexcept { return budget_; }
    [[nodiscard]] std::size_t ChunkCount() const noexcept { return chunks_.size(); }
    [[nodiscard]] const Chunk& At(std::size_t index) const { return chunks_.at(index); }

    [[nodiscard]] std::optional<Lease> Begin(std::uint64_t offset,
                                              std::uint64_t size) {
        if (!Valid() || outstanding_ || !size || offset % kGranule ||
            size % kGranule || offset >= virtual_bytes_ ||
            size > virtual_bytes_ - offset) return std::nullopt;
        const auto first = static_cast<std::size_t>(offset / kGranule);
        const auto count = static_cast<std::size_t>(size / kGranule);
        std::size_t newcomers = 0;
        for (std::size_t i = first; i < first + count; ++i) {
            const auto state = chunks_[i].state;
            if (state == State::Staging || state == State::Retiring) return std::nullopt;
            if (state == State::Unmapped) ++newcomers;
        }
        if (newcomers > static_cast<std::size_t>((budget_ - UsedBytes()) / kGranule))
            return std::nullopt;
        if (!next_id_) return std::nullopt; // never reuse lease id on wrap
        const std::uint64_t id = next_id_++;
        for (std::size_t i = first; i < first + count; ++i)
            if (chunks_[i].state == State::Unmapped) {
                chunks_[i].state = State::Staging;
                chunks_[i].lease = id;
            }
        used_chunks_ += newcomers; // budget reserved before syscalls
        outstanding_ = Lease{id, first, count, newcomers};
        return outstanding_;
    }

    // Record an independently owned, 2 MiB-aligned physical allocation.
    // The eventual backend must separately MAP it at the matching guest VA.
    [[nodiscard]] bool Stage(const Lease& lease, std::size_t index,
                             std::int64_t physical) noexcept {
        if (!matches(lease) || index < lease.first ||
            index - lease.first >= lease.count || physical < 0 ||
            (static_cast<std::uint64_t>(physical) % kGranule) != 0) return false;
        auto& chunk = chunks_[index];
        if (chunk.state != State::Staging || chunk.lease != lease.id ||
            chunk.physical != -1) return false;
        for (const auto& other : chunks_)
            if (other.physical == physical) return false;
        chunk.physical = physical;
        return true;
    }

    // Caller MUST verify all kernel mappings and coherent CPU/GPU aliases.
    // This method cannot and does not verify hardware mapping itself.
    [[nodiscard]] bool Publish(const Lease& lease) noexcept {
        if (!matches(lease)) return false;
        std::size_t prepared = 0;
        for (std::size_t i = lease.first; i < lease.first + lease.count; ++i) {
            const auto& chunk = chunks_[i];
            if (chunk.state == State::Staging && chunk.lease == lease.id &&
                chunk.physical >= 0) ++prepared;
            else if (chunk.state != State::Resident) return false;
        }
        if (prepared != lease.newcomers) return false;
        for (std::size_t i = lease.first; i < lease.first + lease.count; ++i)
            if (chunks_[i].state == State::Staging) {
                chunks_[i].state = State::Resident;
                chunks_[i].lease = 0;
            }
        outstanding_.reset();
        return true;
    }

    // Return only NEW physical owners to release. Existing resident chunks
    // in a reused range must NOT be released during failed new admission.
    [[nodiscard]] std::optional<std::vector<Reclaim>> Abort(const Lease& lease) {
        if (!matches(lease)) return std::nullopt;
        std::vector<Reclaim> release;
        release.reserve(lease.newcomers);
        for (std::size_t i = lease.first; i < lease.first + lease.count; ++i) {
            auto& chunk = chunks_[i];
            if (chunk.state != State::Staging || chunk.lease != lease.id) continue;
            if (chunk.physical >= 0) {
                chunk.state = State::Retiring;
                release.push_back({i, chunk.physical});
            } else {
                chunk = {};
                --used_chunks_;
            }
        }
        return release;
    }

    // Acknowledge ONLY AFTER the kernel confirms unmap and physical release.
    [[nodiscard]] bool ReleaseAcknowledged(const Lease& lease, std::size_t index,
                                           std::int64_t physical) noexcept {
        if (!matches(lease) || index < lease.first ||
            index - lease.first >= lease.count) return false;
        auto& chunk = chunks_[index];
        if (chunk.state != State::Retiring || chunk.lease != lease.id ||
            chunk.physical != physical) return false;
        chunk = {};
        --used_chunks_;
        return true;
    }

    [[nodiscard]] bool FinishAbort(const Lease& lease) noexcept {
        if (!matches(lease)) return false;
        for (std::size_t i = lease.first; i < lease.first + lease.count; ++i)
            if (chunks_[i].lease == lease.id) return false;
        outstanding_.reset();
        return true;
    }

private:
    [[nodiscard]] static bool valid_size(std::uint64_t virtual_bytes,
                                          std::uint64_t budget) noexcept {
        return virtual_bytes && !(virtual_bytes % kGranule) && budget &&
               !(budget % kGranule) && budget <= virtual_bytes &&
               std::in_range<std::size_t>(virtual_bytes / kGranule);
    }
    [[nodiscard]] bool matches(const Lease& lease) const noexcept {
        return outstanding_ && outstanding_->id == lease.id &&
               outstanding_->first == lease.first &&
               outstanding_->count == lease.count &&
               outstanding_->newcomers == lease.newcomers;
    }
    std::uint64_t virtual_bytes_{};
    std::uint64_t budget_{};
    std::vector<Chunk> chunks_;
    std::uint64_t used_chunks_{};
    std::uint64_t next_id_{1};
    std::optional<Lease> outstanding_;
};

} // namespace Eden::PS5::GuestBacking
