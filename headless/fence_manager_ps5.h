// SPDX-FileCopyrightText: Copyright 2026 Eden Emulator Project
// SPDX-License-Identifier: GPL-3.0-or-later

// SPDX-FileCopyrightText: Copyright 2020 yuzu Emulator Project
// SPDX-License-Identifier: GPL-2.0-or-later

#pragma once

#include <algorithm>
#include <atomic>
#include <chrono>
#include <exception>
#include <memory>
#include "gpu_failure.h"
#include <condition_variable>
#include <cstring>
#include <deque>
#include <functional>
#include <mutex>
#include <thread>
#include <queue>

#include "common/common_types.h"
#include "common/settings.h"
#include "common/thread.h"
#include "video_core/delayed_destruction_ring.h"
#include "video_core/gpu.h"
#include "video_core/host1x/host1x.h"
#include "video_core/host1x/syncpoint_manager.h"
#include "video_core/rasterizer_interface.h"

namespace VideoCommon {

class FenceBase {
public:
    explicit FenceBase(bool is_stubbed_) : is_stubbed{is_stubbed_} {}

    bool IsStubbed() const {
        return is_stubbed;
    }

protected:
    bool is_stubbed;
};

template <typename Traits>
class FenceManager {
    using TFence = typename Traits::FenceType;
    using TTextureCache = typename Traits::TextureCacheType;
    using TBufferCache = typename Traits::BufferCacheType;
    using TQueryCache = typename Traits::QueryCacheType;
    static constexpr bool can_async_check = Traits::HAS_ASYNC_CHECK;

public:
    /// Notify the fence manager about a new frame
    void TickFrame() {
        std::unique_lock lock(ring_guard);
        delayed_destruction_ring.Tick();
    }

    // Unlike other fences, this one doesn't
    void SignalOrdering() {
        if constexpr (!can_async_check) {
            TryReleasePendingFences<false>();
        }
        std::scoped_lock lock{buffer_cache.mutex};
        buffer_cache.AccumulateFlushes();
    }

    void SignalReference() {
        std::function<void()> do_nothing([] {});
        SignalFence(std::move(do_nothing));
    }

    void SyncOperation(std::function<void()>&& func) {
        uncommitted_operations.emplace_back(std::move(func));
    }

    void SignalFence(std::function<void()>&& func, bool force_retirement = false) {
        // A forced drain is an actual host retirement point, independent
        // of the optional early guest-fence policy used for ordinary work.
        const bool delay_fence = force_retirement ||
            (Settings::IsGPUFenceBehaviorDefault() ? Settings::IsGPULevelHigh() :
             Settings::IsGPUFenceBehaviorBalanced() || Settings::IsGPUFenceBehaviorAccurate());
        const bool should_flush = ShouldFlush();
        if constexpr (!can_async_check) {
            TryReleasePendingFences<false>();
        }
        CommitAsyncFlushes();
        TFence new_fence = CreateFence(!force_retirement && !should_flush);
        std::unique_lock queue_lock{guard, std::defer_lock};
        if constexpr (can_async_check) queue_lock.lock();
        try {
            if (delay_fence) {
                uncommitted_operations.emplace_back(std::move(func));
            }
            pending_operations.emplace_back(std::move(uncommitted_operations));
            QueueFence(new_fence);
            if (!delay_fence) {
                func();
            }
            fences.push(std::move(new_fence));
            if (should_flush) {
                rasterizer.FlushCommands();
            }
        } catch (...) {
            // A failed queue publication is terminal for this title. Do not
            // continue releasing guest operations from a partial publication.
            ::Eden::RecordGpuFailure(std::current_exception());
            if constexpr (can_async_check) {
                queue_lock.unlock();
                cv.notify_all();
            }
            throw;
        }
        if constexpr (can_async_check) {
            queue_lock.unlock();
            cv.notify_all();
        }
        rasterizer.InvalidateGPUCache();
    }

    void SignalSyncPoint(u32 value) {
        syncpoint_manager.IncrementGuest(value);
        std::function<void()> func([this, value] { syncpoint_manager.IncrementHost(value); });
        SignalFence(std::move(func));
    }

    // Native C7xx semaphore completion must be published behind a real GPU
    // fence. Keep the shutdown overlay's exception-safe queue publication so
    // a failed QueueFence cannot leave a partially visible guest completion.
    void SignalNativeFence(std::function<void()>&& complete) {
        if constexpr (!can_async_check) {
            TryReleasePendingFences<false>();
        }
        CommitAsyncFlushes();
        TFence new_fence = CreateFence(false);
        std::unique_lock queue_lock{guard, std::defer_lock};
        if constexpr (can_async_check) queue_lock.lock();
        try {
            uncommitted_operations.emplace_back(std::move(complete));
            pending_operations.emplace_back(std::move(uncommitted_operations));
            // InnerFence::Queue records the scheduler tick and flushes it.
            QueueFence(new_fence);
            fences.push(std::move(new_fence));
        } catch (...) {
            ::Eden::RecordGpuFailure(std::current_exception());
            if constexpr (can_async_check) {
                queue_lock.unlock();
                cv.notify_all();
            }
            throw;
        }
        if constexpr (can_async_check) {
            queue_lock.unlock();
            cv.notify_all();
        }
        rasterizer.InvalidateGPUCache();
    }

    // Native Ampere completion must retire behind a real GPU fence, even
    // when Maxwell's configured policy permits an immediate/stubbed fence.
    // Preserve the shutdown overlay's failure-aware queue publication.
    void SignalNativeSyncPoint(u32 value) {
        if constexpr (!can_async_check) {
            TryReleasePendingFences<false>();
        }
        CommitAsyncFlushes();
        TFence new_fence = CreateFence(false);
        std::function<void()> retire(
            [this, value] { syncpoint_manager.IncrementHost(value); });
        std::unique_lock queue_lock{guard, std::defer_lock};
        if constexpr (can_async_check) queue_lock.lock();
        try {
            uncommitted_operations.emplace_back(std::move(retire));
            syncpoint_manager.IncrementGuest(value);
            pending_operations.emplace_back(std::move(uncommitted_operations));
            // InnerFence::Queue records the scheduler tick and flushes it.
            QueueFence(new_fence);
            fences.push(std::move(new_fence));
        } catch (...) {
            ::Eden::RecordGpuFailure(std::current_exception());
            if constexpr (can_async_check) {
                queue_lock.unlock();
                cv.notify_all();
            }
            throw;
        }
        if constexpr (can_async_check) {
            queue_lock.unlock();
            cv.notify_all();
        }
        rasterizer.InvalidateGPUCache();
    }

    void WaitPendingFences([[maybe_unused]] bool force) {
        if constexpr (!can_async_check) {
            TryReleasePendingFences<true>();
        } else {
            if (!force) {
                return;
            }
            // An exceptional waiter may return before a queued callback is
            // destroyed. The callback must own its completion state.
            struct WaitState {
                std::mutex mutex;
                std::condition_variable cv;
                bool finished{};
            };
            auto state = std::make_shared<WaitState>();
            if (auto failure = ::Eden::PeekGpuFailure()) std::rethrow_exception(failure);
            std::function<void()> func([state] {
                std::scoped_lock lk(state->mutex);
                state->finished = true;
                state->cv.notify_all();
            });
            SignalFence(std::move(func), true);
            std::unique_lock lk(state->mutex);
            while (!state->finished) {
                if (auto failure = ::Eden::PeekGpuFailure()) std::rethrow_exception(failure);
                state->cv.wait_for(lk, std::chrono::milliseconds(10),
                                   [&state] { return state->finished; });
            }
            if (auto failure = ::Eden::PeekGpuFailure()) std::rethrow_exception(failure);
        }
    }

protected:
    explicit FenceManager(VideoCore::RasterizerInterface& rasterizer_, Tegra::GPU& gpu_,
                          TTextureCache& texture_cache_, TBufferCache& buffer_cache_,
                          TQueryCache& query_cache_)
        : rasterizer{rasterizer_}, gpu{gpu_}, syncpoint_manager{gpu.Host1x().GetSyncpointManager()},
          texture_cache{texture_cache_}, buffer_cache{buffer_cache_}, query_cache{query_cache_} {
        if constexpr (can_async_check) {
            fence_thread = std::jthread([this](std::stop_token token) {
                try { ReleaseThreadFunc(token); }
                catch (...) {
                    ::Eden::RecordGpuFailure(std::current_exception());
                    cv.notify_all();
                }
            });
        }
    }

    // The derived Vulkan owner calls this before its virtual dispatch
    // table and scheduler reference disappear. Base fallback also covers
    // a partially constructed derived instance.
    void StopFenceThread() {
        if constexpr (can_async_check) {
            if (!fence_thread.joinable()) return;
            {
                std::scoped_lock lock{guard};
                fence_thread.request_stop();
            }
            cv.notify_all();
            fence_thread.join();
        }
    }

    virtual ~FenceManager() { StopFenceThread(); }

    /// Creates a Fence Interface, does not create a backend fence if 'is_stubbed' is
    /// true
    virtual TFence CreateFence(bool is_stubbed) = 0;
    /// Queues a fence into the backend if the fence isn't stubbed.
    virtual void QueueFence(TFence& fence) = 0;
    /// Notifies that the backend fence has been signaled/reached in host GPU.
    virtual bool IsFenceSignaled(TFence& fence) const = 0;
    /// Waits until a fence has been signalled by the host GPU.
    virtual void WaitFence(TFence& fence) = 0;

    VideoCore::RasterizerInterface& rasterizer;
    Tegra::GPU& gpu;
    Tegra::Host1x::SyncpointManager& syncpoint_manager;
    TTextureCache& texture_cache;
    TBufferCache& buffer_cache;
    TQueryCache& query_cache;

private:
    template <bool force_wait>
    void TryReleasePendingFences() {
        while (!fences.empty()) {
            TFence& current_fence = fences.front();
            if ((force_wait || ShouldWait()) && !IsFenceSignaled(current_fence)) {
                if constexpr (force_wait) {
                    WaitFence(current_fence);
                } else {
                    return;
                }
            }
            PopAsyncFlushes();
            auto operations = std::move(pending_operations.front());
            pending_operations.pop_front();
            for (auto& operation : operations) {
                operation();
            }
            {
                std::unique_lock lock(ring_guard);
                delayed_destruction_ring.Push(std::move(current_fence));
            }
            fences.pop();
        }
    }

    void ReleaseThreadFunc(std::stop_token stop_token) {
        Common::SetCurrentThreadName("GPUFencingThread");
        Common::SetCurrentThreadPriority(Common::ThreadPriority::High);
        Common::SetCurrentThreadToPerformanceCores();

        TFence current_fence;
        std::deque<std::function<void()>> current_operations;
        while (!stop_token.stop_requested()) {
            {
                std::unique_lock lock(guard);
                cv.wait(lock, [&] {
                    return stop_token.stop_requested() || !fences.empty() ||
                           static_cast<bool>(::Eden::PeekGpuFailure());
                });
                if (stop_token.stop_requested() || ::Eden::PeekGpuFailure()) [[unlikely]] {
                    return;
                }
                current_fence = std::move(fences.front());
                current_operations = std::move(pending_operations.front());
                fences.pop();
                pending_operations.pop_front();
            }
            if (!current_fence->IsStubbed()) {
                WaitFence(current_fence);
            }
            if (auto failure = ::Eden::PeekGpuFailure()) std::rethrow_exception(failure);
            PopAsyncFlushes();
            for (auto& operation : current_operations) {
                operation();
            }
            {
                std::unique_lock lock(ring_guard);
                delayed_destruction_ring.Push(std::move(current_fence));
            }
        }
    }

    bool ShouldWait() const {
        std::scoped_lock lock{buffer_cache.mutex, texture_cache.mutex};
        return texture_cache.ShouldWaitAsyncFlushes() || buffer_cache.ShouldWaitAsyncFlushes() ||
               query_cache.ShouldWaitAsyncFlushes();
    }

    bool ShouldFlush() const {
        std::scoped_lock lock{buffer_cache.mutex, texture_cache.mutex};
        return texture_cache.HasUncommittedFlushes() || buffer_cache.HasUncommittedFlushes() ||
               query_cache.HasUncommittedFlushes();
    }

    void PopAsyncFlushes() {
        {
            std::scoped_lock lock{buffer_cache.mutex, texture_cache.mutex};
            texture_cache.PopAsyncFlushes();
            buffer_cache.PopAsyncFlushes();
        }
        query_cache.PopAsyncFlushes();
    }

    void CommitAsyncFlushes() {
        {
            std::scoped_lock lock{buffer_cache.mutex, texture_cache.mutex};
            texture_cache.CommitAsyncFlushes();
            buffer_cache.CommitAsyncFlushes();
        }
        query_cache.CommitAsyncFlushes();
    }

    std::queue<TFence> fences;
    std::deque<std::function<void()>> uncommitted_operations;
    std::deque<std::deque<std::function<void()>>> pending_operations;

    std::mutex guard;
    std::mutex ring_guard;
    std::condition_variable cv;

    std::jthread fence_thread;

    DelayedDestructionRing<TFence, 8> delayed_destruction_ring;
};

} // namespace VideoCommon
