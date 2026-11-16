// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include "diagnostics_sharing_policy.h"
#include <array>
#include <atomic>
#include <cstdint>
#include <memory>
#include <string>
#include <string_view>
#include <utility>

namespace Eden::DiagnosticsSharing {
// Launcher-owner queue; never call from a render, guest or crash thread.
// Transport receives an immutable, already projected envelope and a cancellation
// flag. A cancelled request must acknowledge completion before another starts.
// Persistent storage and a platform transport are deliberately separate owners.
class Queue {
public:
    struct Report {
        Category category;
        std::uint64_t epoch;
        std::string id;       // random, per report; never a device identifier
        std::string envelope; // sanitized bounded JSON, including erasure secret
    };
    struct Work {
        std::uint64_t ticket{};
        std::shared_ptr<const Report> report;
        std::shared_ptr<std::atomic_bool> cancelled;
        explicit operator bool() const noexcept { return bool(report); }
    };
    enum class Result { Delivered, Retry, Rejected };

    void SetConsent(Consent next) {
        ChangeConsent(Category::Standard, next.standard);
        ChangeConsent(Category::Advanced, next.advanced);
    }
    std::uint64_t Epoch(Category category) const noexcept {
        return consent_.Allows(category) ? epochs_[Index(category)] : 0;
    }
    void Conditions(bool service, bool network) noexcept {
        service_ = service; network_ = network;
        if (!service_ || !network_) Cancel();
    }
    // now is monotonic seconds observed by the launcher, not wall time.
    void SetPhase(Phase next, std::uint64_t now) noexcept {
        if (next == phase_) return;
        phase_ = next;
        if (next == Phase::LauncherIdle) {
            idle_since_ = now;
            attempts_ = 0;
        } else {
            Cancel();
        }
    }
    void Activity(std::uint64_t now) noexcept {
        if (phase_ == Phase::LauncherIdle) {
            idle_since_ = now;
            Cancel();
        }
    }

    bool Enqueue(Report item) {
        if (!service_ || item.epoch == 0 || item.epoch != Epoch(item.category) ||
            item.envelope.empty() || item.envelope.size() > kMaxReportBytes ||
            !ValidId(item.id)) return false;
        for (std::size_t i = 0; i < count_; ++i)
            if (items_[i]->id == item.id) return false;
        if (active_ && active_.report->id == item.id) return false;
        auto report = std::make_shared<const Report>(std::move(item));
        if (count_ == kMaxQueuedReports) {
            // Never evict the active transfer. Prefer old advanced reports
            // over standard crash reports; a full crash queue rejects advanced.
            std::size_t victim = count_;
            for (std::size_t i = 0; i < count_; ++i)
                if (items_[i]->category == Category::Advanced && !IsActive(items_[i])) {
                    victim = i; break;
                }
            if (victim == count_ && report->category == Category::Standard) {
                for (std::size_t i = 0; i < count_; ++i)
                    if (!IsActive(items_[i])) { victim = i; break; }
            }
            if (victim == count_) return false;
            EraseAt(victim);
        }
        items_[count_++] = std::move(report);
        return true;
    }
    bool Contains(std::string_view id) const noexcept {
        for (std::size_t i = 0; i < count_; ++i)
            if (items_[i]->id == id) return true;
        return active_ && active_.report->id == id;
    }
    std::size_t Count() const noexcept { return count_; }
    std::size_t Bytes() const noexcept {
        std::size_t bytes = 0;
        for (std::size_t i = 0; i < count_; ++i) bytes += items_[i]->envelope.size();
        return bytes;
    }
    Work TryStart(std::uint64_t now) {
        Poll(now);
        if (active_ || !count_ || now < idle_since_ ||
            (has_attempt_ && now < last_attempt_)) return {};
        const auto elapsed = [](std::uint64_t n) {
            return static_cast<std::uint32_t>(n > UINT32_MAX ? UINT32_MAX : n);
        };
        Gate gate{};
        gate.phase = phase_; gate.consent = consent_; gate.service_available = service_;
        gate.network_available = network_; gate.retry_due = true;
        gate.idle_seconds = elapsed(now-idle_since_);
        gate.attempts_this_visit = attempts_;
        gate.seconds_since_attempt = has_attempt_ ? elapsed(now-last_attempt_) : kMinIntervalSeconds;
        for (auto category : {Category::Standard, Category::Advanced})
            for (std::size_t i = 0; i < count_; ++i) {
                const auto& item = items_[i];
                if (item->category != category ||
                    !gate.MayStart(category, static_cast<std::uint32_t>(item->envelope.size()),
                                   item->epoch == Epoch(category))) continue;
                if (next_ticket_ == UINT64_MAX) return {};
                auto cancelled = std::make_shared<std::atomic_bool>(false);
                active_ = Work{++next_ticket_, item, std::move(cancelled)};
                has_attempt_ = true; last_attempt_ = now; started_ = now; ++attempts_;
                return active_;
            }
        return {};
    }
    void Poll(std::uint64_t now) noexcept {
        if (active_ && (now < started_ || now-started_ >= kMaxTransferSeconds)) Cancel();
    }
    bool Finish(std::uint64_t ticket, Result outcome) noexcept {
        if (!active_ || ticket != active_.ticket) return false;
        const auto report = active_.report;
        const bool cancelled = active_.cancelled->load(std::memory_order_acquire);
        // A response may race cancellation. Keep a pending report for
        // idempotent retry; a revoked report was already purged.
        if (!cancelled && report->epoch == Epoch(report->category) &&
            outcome != Result::Retry) {
            for (std::size_t i = 0; i < count_; ++i)
                if (items_[i] == report) { EraseAt(i); break; }
        }
        if (cancelled || outcome == Result::Retry)
            attempts_ = kMaxAttemptsPerVisit; // defer failure to a later visit
        active_ = {};
        return true;
    }
private:
    static constexpr std::size_t Index(Category c) noexcept {
        return c == Category::Standard ? 0 : 1;
    }
    static bool ValidId(const std::string& id) {
        if (id.size() != 36 || id[14] != '4' ||
            (id[19] != '8' && id[19] != '9' && id[19] != 'a' && id[19] != 'b')) return false;
        for (std::size_t i = 0; i < id.size(); ++i) {
            const auto c = id[i];
            const bool dash = i==8 || i==13 || i==18 || i==23;
            if (dash ? c!='-' : !((c>='0'&&c<='9')||(c>='a'&&c<='f'))) return false;
        }
        return true;
    }
    void Cancel() noexcept {
        if (active_) active_.cancelled->store(true,std::memory_order_release);
    }
    bool IsActive(const std::shared_ptr<const Report>& item) const noexcept {
        return active_ && active_.report == item;
    }
    void EraseAt(std::size_t index) noexcept {
        for (std::size_t i = index+1; i < count_; ++i) items_[i-1] = std::move(items_[i]);
        items_[--count_].reset();
    }
    void ChangeConsent(Category category, bool value) {
        bool& allowed = category == Category::Standard ? consent_.standard : consent_.advanced;
        if (allowed == value) return;
        auto& epoch = epochs_[Index(category)];
        if (epoch == UINT64_MAX) value = false; else ++epoch;
        allowed = value;
        if (active_ && active_.report->category == category) Cancel();
        for (std::size_t i = count_; i > 0; --i)
            if (items_[i-1]->category == category) EraseAt(i-1);
    }
    std::array<std::shared_ptr<const Report>, kMaxQueuedReports> items_{};
    std::size_t count_{};
    std::array<std::uint64_t,2> epochs_{};
    Consent consent_{};
    Phase phase_ = Phase::Starting;
    bool service_{}, network_{}, has_attempt_{};
    std::uint64_t idle_since_{}, last_attempt_{}, started_{}, next_ticket_{};
    std::uint32_t attempts_{};
    Work active_{};
};
} // namespace Eden::DiagnosticsSharing
