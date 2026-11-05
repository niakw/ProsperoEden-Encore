// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
// Streaming preflight for the exact GitHub ZIP selected by the stable-release
// parser. Uses bounded memory; no download may become installable on size or
// digest alone without the helper's independent archive/target validation.
#include "self_update_sha256.h"
#include <cstdint>
#include <cstring>
#include <string>
#include <string_view>

namespace Eden::EncoreUpdate {
class VerifiedArchive final {
public:
    VerifiedArchive(std::uint64_t expected_bytes, std::string_view sha256)
        : expected_(expected_bytes), valid_(expected_bytes >= (1ull << 20) &&
                expected_bytes <= (1ull << 30) && IsDigest(sha256)) {
        if (valid_) {
            expected_digest_ = std::string(sha256);
            self_update_sha256_start(&hash_);
        }
    }

    bool Valid() const noexcept { return valid_ && !failed_; }
    std::uint64_t Bytes() const noexcept { return received_; }

    // Caller persists chunks before passing them to Accept (or fails closed).
    bool Accept(const void* data, std::size_t length) noexcept {
        if (!Valid() || finished_ || (!data && length != 0) ||
            received_ > expected_ || length > expected_ - received_) {
            failed_ = true;
            return false;
        }
        self_update_sha256_add(&hash_, data, length);
        received_ += length;
        return true;
    }

    bool Finish() noexcept {
        if (!Valid() || finished_ || received_ != expected_) {
            failed_ = true;
            return false;
        }
        unsigned char digest[32]{};
        self_update_sha256_finish(&hash_, digest);
        finished_ = self_update_sha256_matches(digest, expected_digest_.c_str()) == 1;
        if (!finished_) failed_ = true;
        return finished_;
    }

    bool Finished() const noexcept { return finished_ && !failed_; }
private:
    static bool IsDigest(std::string_view text) noexcept {
        if (text.size() != 64) return false;
        for (char c : text)
            if (!((c >= '0' && c <= '9') || (c >= 'a' && c <= 'f')))
                return false;
        return true;
    }
    std::uint64_t expected_{};
    std::uint64_t received_{};
    std::string expected_digest_;
    self_update_sha256 hash_{};
    bool valid_ = false;
    bool failed_ = false;
    bool finished_ = false;
};
} // namespace Eden::EncoreUpdate
