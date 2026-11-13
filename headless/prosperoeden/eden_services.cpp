// SPDX-License-Identifier: GPL-3.0-or-later
#include "eden_services.h"
#include <webp/decode.h>
#include <webp/encode.h>
#ifdef PS5_NATIVE
#include "ps5_profile_avatar_staging.hpp"
#include "jxr_decoder.h"
#endif

#include "assets_dir.h"
#include "ns2_title_catalog.h"
#include "crash_report.h"
#ifdef PS5_NATIVE
#include "boot_trace.h"
#include "log_pipe.h"
#include "performance.h"
#endif
#include "diagnostics.h"
#include "encore_overrides_runtime.h"
#include "metadata_bridge.h"
#include "title_id_fallback.h"
#include "mods.h"
#include "native_directory.h"
#include "pe/core/strings.hpp"
#include "pe/gfx/image.hpp"
#include "common/net/net.h"
#include "network_audit.h"
#include "radio_input.h"
#include "settings_store.h"
#include "version.h"
#include "lossless_user_file.h"
#include "nr_dll_user_file.h"
#include "network/room.h"
#include "network/network.h"
#include "network/room_member.h"
#include "enet/enet.h"
#include "launcher_update_version.hpp"
#include "launcher_update_release.hpp"
#include "native_app_update.hpp"
#include <string_view>

#include <algorithm>
#include <array>
#include <chrono>
#include <cctype>
#include <cerrno>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <cstdlib>
#include <ctime>
#include <dirent.h>
#include <exception>
#include <fcntl.h>
#include <filesystem>
#include <fstream>
#include <future>
#include <initializer_list>
#include <mutex>
#include <optional>
#include <nlohmann/json.hpp>
#include <stb_image.h>
#include <sys/stat.h>
#include <system_error>
#include <thread>
#include <unordered_map>
#include <unordered_set>
#include <unistd.h>

#ifdef PS5_NATIVE
// Resolve the foreground console user's cached image only. This is a
// read-only platform call; no account, PSN, registry or cache modification.
extern "C" int sceUserServiceInitialize(void* params);
extern "C" int sceUserServiceGetForegroundUser(std::int32_t* user_id);
#endif

namespace {

using pe::fill;
using pe::tr;

bool IsFile(const std::string& path) {
    struct stat info {};
    if (lstat(path.c_str(), &info) == 0) return S_ISREG(info.st_mode);
    if (errno != EPERM && errno != EACCES) return false;
    return stat(path.c_str(), &info) == 0 && S_ISREG(info.st_mode);
}

#ifdef PS5_NATIVE
bool IsReadableAvatarFile(const std::string& path) {
    if (!IsFile(path)) return false;
    // stat() can succeed even when a sandboxed title cannot open the
    // privileged cache. Do not choose an unreadable PNG over a valid DDS.
    const int fd = ::open(path.c_str(), O_RDONLY | O_NOFOLLOW | O_NONBLOCK);
    if (fd < 0) return false;
    struct stat info{};
    const bool readable = ::fstat(fd, &info) == 0 &&
                          S_ISREG(info.st_mode) && info.st_size >= 128 &&
                          info.st_size <= 4 * 1024 * 1024;
    (void)::close(fd);
    return readable;
}
// Check actual image decodability off the UI thread, not merely stat/open.
// A readable but corrupt PS5 PNG must not shadow the same user's valid DDS.
bool IsDecodableAvatarFile(const std::string& path) {
    if (!IsReadableAvatarFile(path)) return false;
    if (path.ends_with(".dds")) {
        pe::gfx::Image decoded;
        const bool valid = pe::gfx::load_avatar_dds(path, &decoded) && !decoded.empty();
        if (!valid) {
            static std::atomic_flag warned = ATOMIC_FLAG_INIT;
            if (!warned.test_and_set())
                std::fprintf(stderr, "EDEN_PROFILE_AVATAR status=dds_decode_failed\n");
        }
        return valid;
    }
    int width = 0, height = 0, channels = 0;
    const bool header_ok = stbi_info(path.c_str(), &width, &height, &channels) != 0 &&
                           width > 0 && height > 0 && width <= 1024 && height <= 1024;
    stbi_uc* rgba = header_ok ? stbi_load(path.c_str(), &width, &height, &channels, 4) : nullptr;
    const bool valid = rgba != nullptr;
    if (rgba) stbi_image_free(rgba);
    if (!valid) {
        static std::atomic_flag warned = ATOMIC_FLAG_INIT;
        if (!warned.test_and_set())
            std::fprintf(stderr, "EDEN_PROFILE_AVATAR status=png_decode_failed fallback=dds\n");
    }
    return valid;
}

#endif

// Only a deconstructed title's base content counts towards its Library size.
// Its executable 'main' is just one 20-40 MiB NSO; counting that alone makes
// a multi-gigabyte game appear as a 32 MB title. Do NOT add updates or DLC,
// follow symlinks, block on network media, or guess if traversal is incomplete.
// The entire walk runs on the cancellable Library background scan.
std::optional<std::uint64_t> ExtractedBaseBytes(const std::filesystem::path& title,
                                                 const std::atomic<bool>* cancel) {
    namespace fs = std::filesystem;
    const auto fail = [&](const char* reason, const fs::path& where, int code,
                          std::size_t examined) -> std::optional<std::uint64_t> {
        // Never expose a full user's filesystem path or log once per entry.
        const std::string name = where.filename().string();
        std::fprintf(stderr,
            "EDEN_EXEFS_SIZE_SCAN_FAIL title=%.64s entry=%.64s reason=%s error=%d entries=%zu\n",
            title.filename().string().c_str(), name.c_str(), reason, code, examined);
        return std::nullopt;
    };
    if (!Eden::IsSafeExtractedDirectory(title))
        return fail("root_not_safe", title, 0, 0);
    std::uint64_t total = 0;
    std::size_t examined = 0;
    // Real extracted RomFS trees may exceed 40,000 files and 16 levels.
    // Never call this from the drawing thread; cancellation is checked on
    // the Library worker between entries and directories.
    constexpr std::size_t kMaxExtractedFiles = 1000000;
    constexpr int kMaxExtractedDepth = 64;
#if defined(PS5_NATIVE)
    // PS5 mounted filesystems need the same 64KiB sceKernelGetdents reader
    // already used by the top-level Library scan. The libc-backed C++
    // recursive iterator may fail to enumerate nested game directories even
    // though roms/<title>/main was found through the native reader.
    struct PendingDirectory { fs::path path; int depth; };
    std::vector<PendingDirectory> pending{{title, 0}};
    while (!pending.empty()) {
        if (cancel && cancel->load(std::memory_order_acquire)) return std::nullopt;
        auto current = std::move(pending.back());
        pending.pop_back();
        std::error_code listing_error;
        const auto children = Eden::ReadNativeDirectory(current.path, listing_error);
        if (listing_error)
            return fail("getdents", current.path, listing_error.value(), examined);
        for (const auto& entry : children) {
            if (cancel && cancel->load(std::memory_order_acquire)) return std::nullopt;
            if (++examined > kMaxExtractedFiles)
                return fail("entry_limit", entry.path(), 0, examined);
            struct stat info {};
            if (::lstat(entry.path().c_str(), &info) != 0)
                return fail("lstat", entry.path(), errno, examined);
            if (S_ISLNK(info.st_mode)) continue;
            if (S_ISDIR(info.st_mode)) {
                // Updates/DLC never contribute to the base-game size.
                if (Eden::IsReservedAddOnPackageStem(entry.path().filename().string())) continue;
                if (current.depth >= kMaxExtractedDepth)
                    return fail("depth_limit", entry.path(), 0, examined);
                pending.push_back({entry.path(), current.depth + 1});
                continue;
            }
            if (!S_ISREG(info.st_mode)) continue;
            if (info.st_size < 0)
                return fail("negative_size", entry.path(), 0, examined);
            const auto bytes = static_cast<std::uint64_t>(info.st_size);
            if (bytes > UINT64_MAX - total)
                return fail("overflow", entry.path(), 0, examined);
            total += bytes;
        }
    }
#else
    std::error_code error;
    fs::recursive_directory_iterator it(title, fs::directory_options::skip_permission_denied, error);
    if (error) return fail("iterator_init", title, error.value(), examined);
    const fs::recursive_directory_iterator end;
    for (; it != end; it.increment(error)) {
        if (error || ++examined > kMaxExtractedFiles ||
            it.depth() > kMaxExtractedDepth ||
            (cancel && cancel->load(std::memory_order_acquire))) {
            if (cancel && cancel->load(std::memory_order_acquire)) return std::nullopt;
            return fail(error ? "iterator_next" : examined > kMaxExtractedFiles ?
                        "entry_limit" : "depth_limit",
                        it != end ? it->path() : title, error.value(), examined);
        }
        const auto status = it->symlink_status(error);
        if (error) return fail("symlink_status", it->path(), error.value(), examined);
        if (fs::is_symlink(status)) {
            it.disable_recursion_pending();
            continue;
        }
        if (fs::is_directory(status)) {
            if (Eden::IsReservedAddOnPackageStem(it->path().filename().string()))
                it.disable_recursion_pending();
            continue;
        }
        if (!fs::is_regular_file(status)) continue;
        const auto bytes = it->file_size(error);
        if (error) return fail("file_size", it->path(), error.value(), examined);
        if (bytes > UINT64_MAX - total)
            return fail("overflow", it->path(), 0, examined);
        total += static_cast<std::uint64_t>(bytes);
    }
    if (error) return fail("iterator_finish", title, error.value(), examined);
#endif
    return total > 0 ? std::optional<std::uint64_t>{total} : std::nullopt;
}

// Local user-supplied covers are a safe offline fallback for extracted titles
// with no packaged Control NCA or Nlib match. No game-name-specific artwork.
// Read user-supplied Control NACP without NCA keys or external title databases.
// The legacy NACP language table has up to sixteen 0x300-byte records
// (0x200-byte name + 0x100-byte developer). The compressed/extended variant
// is intentionally not guessed. This is metadata-only, never guest authority.
struct ExtractedSidecarMetadata {
    std::string name;
    std::string developer;
};

bool ValidSidecarText(std::string_view value) {
    if (value.empty()) return false;
    for (std::size_t i = 0; i < value.size();) {
        const unsigned char c = static_cast<unsigned char>(value[i]);
        if (c < 0x20 || c == 0x7f) return false;
        if (c < 0x80) { ++i; continue; }
        const std::size_t n = c >= 0xc2 && c <= 0xdf ? 2 :
                              c >= 0xe0 && c <= 0xef ? 3 :
                              c >= 0xf0 && c <= 0xf4 ? 4 : 0;
        if (!n || n > value.size() - i) return false;
        for (std::size_t j = 1; j < n; ++j)
            if ((static_cast<unsigned char>(value[i+j]) & 0xc0u) != 0x80u) return false;
        const auto second = static_cast<unsigned char>(value[i+1]);
        if ((c == 0xe0 && second < 0xa0) || (c == 0xed && second >= 0xa0) ||
            (c == 0xf0 && second < 0x90) || (c == 0xf4 && second >= 0x90)) return false;
        i += n;
    }
    return true;
}
std::string NacpString(const char* bytes, std::size_t capacity) {
    const auto* end = static_cast<const char*>(std::memchr(bytes, '\0', capacity));
    if (!end) return {};
    const std::string value(bytes, end);
    return ValidSidecarText(value) ? value : std::string{};
}
ExtractedSidecarMetadata ExtractedLocalNacp(const std::filesystem::path& title,
                                                  int language_choice) {
    namespace fs = std::filesystem;
    if (!Eden::IsSafeExtractedDirectory(title)) return {};
    // Order matches the existing extracted ExeFS/main layout. Never use
    // update/DLC control data to relabel a base game.
    for (const char* relative : {"control.nacp", "base/control.nacp",
                                 "exefs/control.nacp", "base/exefs/control.nacp"}) {
        fs::path parent = title;
        bool safe = true;
        for (const auto& part : fs::path(relative).parent_path()) {
            parent /= part;
            if (!Eden::IsSafeExtractedDirectory(parent)) { safe = false; break; }
        }
        if (!safe) continue;
        const fs::path candidate = title / relative;
        std::error_code ec;
        const auto status = fs::symlink_status(candidate, ec);
        if (ec || !fs::is_regular_file(status) || fs::is_symlink(status)) continue;
        const auto size = fs::file_size(candidate, ec);
        if (ec || size < 0x3000 || size > 0x20000) continue;
        std::ifstream input(candidate, std::ios::binary);
        if (!input) continue;
        // Map launcher language catalog indices to the 16 uncompressed
        // NACP slots; Polish/Thai use the compressed 18-language variant and
        // correctly fall back to available uncompressed entries instead.
        constexpr std::array<int, 18> to_nacp{
            0,1,3,9,4,7,6,5,10,15,8,11,-1,2,12,14,13,-1
        };
        const int preferred = language_choice >= 0 &&
            static_cast<std::size_t>(language_choice) < to_nacp.size()
            ? to_nacp[static_cast<std::size_t>(language_choice)] : -1;
        constexpr std::array<unsigned, 16> fallback{
            0,1,3,9,2,4,5,6,7,8,10,11,12,13,14,15
        };
        // Preferred language first, then English, French and other populated
        // entries. Never silently impose French on English-speaking users.
        for (std::size_t attempt = 0; attempt < fallback.size() + 1; ++attempt) {
            const unsigned language = attempt == 0 && preferred >= 0
                ? static_cast<unsigned>(preferred)
                : fallback[attempt == 0 ? 0 : attempt - 1];
            if (language >= 16 || (attempt != 0 && preferred >= 0 &&
                                   language == static_cast<unsigned>(preferred)))
                continue;
            std::array<char, 0x300> record{};
            input.clear();
            input.seekg(static_cast<std::streamoff>(language * record.size()));
            if (!input.read(record.data(), record.size())) continue;
            auto name = NacpString(record.data(), 0x200);
            if (name.empty() || name == "Application") continue;
            auto developer = NacpString(record.data() + 0x200, 0x100);
            return {std::move(name), std::move(developer)};
        }
    }
    return {};
}

std::string ExtractedLocalCover(const std::filesystem::path& title) {
    namespace fs = std::filesystem;
    if (!Eden::IsSafeExtractedDirectory(title)) return {};
    // Borrow the upstream loose-ExeFS sidecar discovery contract (Eglantine
    // 4d2cf41837): the game icon may live next to main or in base/exefs.
    // No synthetic thumbnails or fabricated rear art are needed.
    for (const char* relative : {"cover.tga", "cover.png", "cover.jpg", "cover.jpeg",
                                 "icon.tga", "icon.png", "icon.jpg",
                                 "exefs/cover.png", "exefs/cover.jpg",
                                 "exefs/icon.png", "exefs/icon.jpg",
                                 "base/cover.tga", "base/cover.png", "base/cover.jpg",
                                 "base/icon.png", "base/icon.jpg",
                                 "base/exefs/cover.png", "base/exefs/cover.jpg",
                                 "base/exefs/icon.png", "base/exefs/icon.jpg"}) {
        // symlink_status(candidate) does not detect symlinked ancestors.
        // Check each ancestor before reading a user-supplied sidecar.
        fs::path parent = title;
        bool safe = true;
        for (const auto& segment : fs::path(relative).parent_path()) {
            parent /= segment;
            if (!Eden::IsSafeExtractedDirectory(parent)) { safe = false; break; }
        }
        if (!safe) continue;
        const fs::path candidate = title / relative;
        std::error_code error;
        const auto status = fs::symlink_status(candidate, error);
        if (error || !fs::is_regular_file(status) || fs::is_symlink(status)) continue;
        const auto size = fs::file_size(candidate, error);
        if (!error && size >= 128 && size <= (16u << 20)) return candidate.string();
    }
    // Eglantine's loose ExeFS sidecars are often JPEG images named
    // icon_<language>.dat rather than *.jpg. The launcher decodes image
    // CONTENT with stb_image, independently of the extension. Scan only
    // known filenames at bounded depth; never follow symlinked parents.
    constexpr const char* languages[] = {
        "French", "CanadianFrench", "AmericanEnglish", "BritishEnglish",
        "Japanese", "German", "Spanish", "LatinAmericanSpanish", "Italian",
        "Dutch", "Portuguese", "Russian", "Korean", "SimplifiedChinese",
        "TraditionalChinese"
    };
    for (const char* base : {"exefs", "base/exefs", ".", "base"}) {
        const fs::path dir = title / base;
        // Check all ancestors, including base/; symlink_status(final) is not
        // sufficient because it follows symlinked intermediate directories.
        fs::path ancestor = title;
        bool safe = true;
        for (const auto& segment : fs::path(base)) {
            ancestor /= segment;
            if (!Eden::IsSafeExtractedDirectory(ancestor)) { safe = false; break; }
        }
        if (!safe) continue;
        for (const char* language : languages) {
            const fs::path candidate = dir / (std::string("icon_") + language + ".dat");
            std::error_code error;
            const auto status = fs::symlink_status(candidate, error);
            if (error || !fs::is_regular_file(status) || fs::is_symlink(status)) continue;
            const auto size = fs::file_size(candidate, error);
            if (error || size < 128 || size > (16u << 20)) continue;
            // Only JPEG/PNG sidecars. Other binary .dat resources must NOT be
            // handed to the cover decoder as images.
            std::ifstream input(candidate, std::ios::binary);
            char signature[8]{};
            input.read(signature, sizeof(signature));
            if (input.gcount() != static_cast<std::streamsize>(sizeof(signature))) continue;
            const bool jpeg = static_cast<unsigned char>(signature[0]) == 0xff &&
                              static_cast<unsigned char>(signature[1]) == 0xd8;
            const bool png = std::memcmp(signature, "\x89PNG\r\n\x1a\n", 8) == 0;
            if (jpeg || png) return candidate.string();
        }
    }
    return {};
}

std::uint64_t ResolveTitleId(const std::string& path, const std::string& file) {
    const std::uint64_t metadata_id = eden_game_title_id(path.c_str());
    if (metadata_id != 0) return metadata_id;
    const std::uint64_t filename_id = Eden::TitleIdFromRomFilename(file);
    if (filename_id != 0)
        std::fprintf(stderr, "EDEN_TITLE_ID_FALLBACK file=%s title_id=%016llX\n", file.c_str(),
                     static_cast<unsigned long long>(filename_id));
    return filename_id;
}

std::string NlibHeroPath(std::uint64_t title_id) {
    char id[17]{};
    std::snprintf(id, sizeof(id), "%016llX", static_cast<unsigned long long>(title_id));
    return Eden::CoversDir() + "/hero-" + id + ".webp";
}

std::string NlibIconPath(std::uint64_t title_id) {
    char id[17]{};
    std::snprintf(id, sizeof(id), "%016llX", static_cast<unsigned long long>(title_id));
    return Eden::CoversDir() + "/nlib-icon-" + id + ".webp";
}

std::string NlibScreenshotPath(std::uint64_t title_id, int index) {
    char id[17]{};
    std::snprintf(id, sizeof(id), "%016llX", static_cast<unsigned long long>(title_id));
    return Eden::CoversDir() + "/screen-" + id + "-" + std::to_string(index) + ".webp";
}


std::string NlibLanguageCode(int language) {
    language = std::clamp(language, 0, static_cast<int>(std::size(Eden::kLanguageKeys)) - 1);
    std::string key = Eden::kLanguageKeys[static_cast<std::size_t>(language)];
    const std::size_t dash = key.find('-');
    std::string base = dash == std::string::npos ? key : key.substr(0, dash);
    static constexpr const char* supported[] = {
        "en", "ja", "es", "de", "fr", "nl", "pt", "it", "zh", "ko", "ru"};
    for (const char* code : supported)
        if (base == code) return base;
    return "en";
}

std::string NlibMetadataPath(std::uint64_t title_id, const std::string& language) {
    char id[17]{};
    std::snprintf(id, sizeof(id), "%016llX", static_cast<unsigned long long>(title_id));
    return Eden::CoversDir() + "/nlib-" + id + "-" + language + ".json";
}

std::string JoinJsonStrings(const nlohmann::json& value) {
    if (!value.is_array()) return {};
    std::string result;
    for (const auto& item : value) {
        if (!item.is_string()) continue;
        if (!result.empty()) result += " · ";
        result += item.get<std::string>();
    }
    return result;
}

bool AtomicWriteText(const std::string& path, const std::string& body) {
    std::error_code directory_error;
    const std::filesystem::path parent = std::filesystem::path(path).parent_path();
    if (!parent.empty()) std::filesystem::create_directories(parent, directory_error);
    if (directory_error) return false;
    const std::string staged = path + ".new";
    std::FILE* file = std::fopen(staged.c_str(), "wb");
    if (!file) return false;
    const bool written = std::fwrite(body.data(), 1, body.size(), file) == body.size();
    const bool closed = std::fclose(file) == 0;
    if (!written || !closed || std::rename(staged.c_str(), path.c_str()) != 0) {
        (void)std::remove(staged.c_str());
        return false;
    }
    return true;
}

std::mutex& ArtworkCodecMutex() {
    static std::mutex mutex;
    return mutex;
}

bool WriteJpegWebP(const std::string& encoded, const std::string& output,
                   bool tall_case = false) {
    // JPEG/PNG source -> WebP directly, one lossy encode at quality 80.
    // Runs only on the bounded network worker; never during GL navigation.
    if (encoded.empty() || encoded.size() > (16u << 20)) return false;
    int width = 0, height = 0, channels = 0;
    if (!stbi_info_from_memory(
            reinterpret_cast<const stbi_uc*>(encoded.data()), static_cast<int>(encoded.size()),
            &width, &height, &channels) ||
        width <= 0 || height <= 0 || width > 4096 || height > 4096 ||
        (!tall_case && height > 2160) ||
        static_cast<std::uint64_t>(width) * height > 3840u * 2160u)
        return false;
    // Keep expensive 1080p/box encodes serial while HTTP downloads stay
    // concurrent. This bounds peak PS5 RAM usage across background jobs.
    std::scoped_lock codec_lock(ArtworkCodecMutex());
    stbi_uc* rgba = stbi_load_from_memory(
        reinterpret_cast<const stbi_uc*>(encoded.data()), static_cast<int>(encoded.size()),
        &width, &height, &channels, 4);
    if (!rgba) return false;
    const float scale = tall_case ?
        std::min({1.0f, 1500.0f / width, 2100.0f / height}) : 1.0f;
    const int w = std::max(1, static_cast<int>(width * scale));
    const int h = std::max(1, static_cast<int>(height * scale));
    const std::uint8_t* pixels = rgba;
    std::vector<std::uint8_t> resized;
    if (w != width || h != height) {
        resized.resize(static_cast<std::size_t>(w) * h * 4u);
        for (int y = 0; y < h; ++y) {
            const auto* row = rgba + static_cast<std::size_t>(y * height / h) * width * 4u;
            auto* dst = resized.data() + static_cast<std::size_t>(y) * w * 4u;
            for (int x = 0; x < w; ++x) {
                const auto* src = row + static_cast<std::size_t>(x * width / w) * 4u;
                std::memcpy(dst + static_cast<std::size_t>(x) * 4u, src, 4u);
            }
        }
        pixels = resized.data();
    }
    std::uint8_t* compressed = nullptr;
    const std::size_t length = WebPEncodeRGBA(pixels, w, h, w * 4, 80.0f, &compressed);
    stbi_image_free(rgba);
    if (!length || !compressed || length > (16u << 20)) {
        WebPFree(compressed);
        return false;
    }
    int checked_w = 0, checked_h = 0;
    const bool valid = WebPGetInfo(compressed, length, &checked_w, &checked_h) &&
                       checked_w == w && checked_h == h;
    std::FILE* file = valid ? std::fopen(output.c_str(), "wb") : nullptr;
    if (!file) { WebPFree(compressed); return false; }
    const bool written = std::fwrite(compressed, 1, length, file) == length;
    const bool closed = std::fclose(file) == 0;
    WebPFree(compressed);
    if (!written || !closed) { (void)std::remove(output.c_str()); return false; }
    return true;
}

std::string NlibPlayersPath(std::uint64_t title_id) {
    char id[17]{};
    std::snprintf(id, sizeof(id), "%016llX", static_cast<unsigned long long>(title_id));
    return Eden::CoversDir() + "/players-" + id + ".txt";
}

// The old uncompressed BGRA TGA cache remains readable during WebP migration.
// A filename alone is not sufficient: incomplete/old files previously showed
// permanently empty tiles and prevented download retries. Validate the header
// and complete payload without allocating or decoding image buffers.
bool ValidNlibTga(const std::string& path) {
    struct stat info{};
    if (stat(path.c_str(), &info) != 0 || !S_ISREG(info.st_mode) ||
        info.st_size < 18) return false;
    std::FILE* file = std::fopen(path.c_str(), "rb");
    if (!file) return false;
    unsigned char header[18]{};
    const bool readable = std::fread(header, 1, sizeof(header), file) == sizeof(header);
    std::fclose(file);
    if (!readable || header[1] != 0 || header[2] != 2 || header[16] != 32)
        return false;
    const unsigned width = static_cast<unsigned>(header[12]) |
                           (static_cast<unsigned>(header[13]) << 8);
    const unsigned height = static_cast<unsigned>(header[14]) |
                            (static_cast<unsigned>(header[15]) << 8);
    if (width == 0 || height == 0 || width > 4096 || height > 2160 ||
        static_cast<std::uint64_t>(width) * height > 3840u * 2160u)
        return false;
    const std::uint64_t bytes = 18u + header[0] +
        static_cast<std::uint64_t>(width) * height * 4u;
    return static_cast<std::uint64_t>(info.st_size) >= bytes;
}

bool ValidNlibWebP(const std::string& path, int* out_width = nullptr,
                   int* out_height = nullptr) {
    struct stat info{};
    if (stat(path.c_str(), &info) != 0 || !S_ISREG(info.st_mode) ||
        info.st_size < 30 || info.st_size > (16LL << 20)) return false;
    std::FILE* file = std::fopen(path.c_str(), "rb");
    if (!file) return false;
    unsigned char header[256]{};
    const auto count = std::fread(header, 1,
                    std::min(sizeof(header), static_cast<std::size_t>(info.st_size)), file);
    std::fclose(file);
    if (count < 30 || std::memcmp(header, "RIFF", 4) != 0 ||
        std::memcmp(header + 8, "WEBP", 4) != 0) return false;
    const std::uint64_t declared = 8ull + static_cast<std::uint32_t>(header[4]) +
        (static_cast<std::uint32_t>(header[5]) << 8) +
        (static_cast<std::uint32_t>(header[6]) << 16) +
        (static_cast<std::uint32_t>(header[7]) << 24);
    if (declared != static_cast<std::uint64_t>(info.st_size)) return false;
    int width = 0, height = 0;
    if (!WebPGetInfo(header, count, &width, &height) ||
        width <= 0 || height <= 0 || width > 4096 || height > 4096 ||
        static_cast<std::uint64_t>(width) * height > 3840u * 2160u)
        return false;
    if (out_width) *out_width = width;
    if (out_height) *out_height = height;
    return true;
}

// One-time offline migration, only for artwork known to be generated by
// Encore. A user's own retail-scans must never be silently deleted.
// No HTTP round-trip and no UI-thread I/O. A failed encode keeps legacy TGA.
bool MigrateGeneratedTga(const std::string& preferred, bool require_receipt) {
    if (!preferred.ends_with(".webp")) return false;
    const std::string legacy = preferred.substr(0, preferred.size() - 5) + ".tga";
    const std::string old_receipt = legacy + ".source";
    std::string provenance;
    if (require_receipt) {
        std::ifstream receipt(old_receipt);
        if (!receipt || !std::getline(receipt, provenance) || provenance.empty())
            return false;
    }
    if (!ValidNlibTga(legacy)) return false;

    // Restrict the migration to our own uncompressed top-left BGRA TGA
    // contract. A manually edited, RLE, indexed or inverted asset is kept.
    std::scoped_lock codec_lock(ArtworkCodecMutex());
    struct stat info{};
    if (stat(legacy.c_str(), &info) != 0 || !S_ISREG(info.st_mode) ||
        info.st_size < 18 || info.st_size > 18LL + 3840LL * 2160 * 4) return false;
    std::FILE* input = std::fopen(legacy.c_str(), "rb");
    if (!input) return false;
    std::uint8_t header[18]{};
    const bool header_ok = std::fread(header, 1, 18, input) == 18;
    const unsigned w = static_cast<unsigned>(header[12]) |
                      (static_cast<unsigned>(header[13]) << 8);
    const unsigned h = static_cast<unsigned>(header[14]) |
                      (static_cast<unsigned>(header[15]) << 8);
    const std::size_t payload = static_cast<std::size_t>(w) * h * 4u;
    const bool is_generated = header_ok && header[0] == 0 && header[1] == 0 &&
        header[2] == 2 && header[16] == 32 && header[17] == 0x28 &&
        w > 0 && h > 0 && w <= 4096 && h <= 2160 &&
        payload <= static_cast<std::size_t>(3840u) * 2160u * 4u &&
        static_cast<std::uint64_t>(info.st_size) == 18u + payload;
    if (!is_generated) { std::fclose(input); return false; }

    if (!ValidNlibWebP(preferred)) {
        std::vector<std::uint8_t> bgra(payload);
        const bool read = std::fread(bgra.data(), 1, bgra.size(), input) == bgra.size();
        std::fclose(input);
        if (!read) return false;
        std::uint8_t* encoded = nullptr;
        const std::size_t size = WebPEncodeBGRA(
            bgra.data(), static_cast<int>(w), static_cast<int>(h),
            static_cast<int>(w * 4), 80.0f, &encoded);
        if (!size || !encoded || size > (16u << 20)) {
            WebPFree(encoded);
            return false;
        }
        const std::string staged = preferred + ".new";
        std::FILE* output = std::fopen(staged.c_str(), "wb");
        bool written = output && std::fwrite(encoded, 1, size, output) == size;
        if (output) written = std::fclose(output) == 0 && written;
        WebPFree(encoded);
        if (!written || !ValidNlibWebP(staged) ||
            std::rename(staged.c_str(), preferred.c_str()) != 0) {
            (void)std::remove(staged.c_str());
            return false;
        }
    } else {
        std::fclose(input);
    }
    // Preserve edition/region receipts before releasing source bytes.
    if (require_receipt && !IsFile(preferred + ".source") &&
        !AtomicWriteText(preferred + ".source", provenance + "\n")) return true;
    if (ValidNlibWebP(preferred)) {
        (void)std::remove(legacy.c_str());
        if (require_receipt) (void)std::remove(old_receipt.c_str());
    }
    return true;
}

bool ValidCachedArtwork(const std::string& path) {
    if (path.ends_with(".webp")) return ValidNlibWebP(path);
    return ValidNlibTga(path);
}

// Keep legacy TGA usable until a validated WebP replacement arrives.
std::string AvailableArtwork(const std::string& preferred) {
    if (ValidCachedArtwork(preferred)) return preferred;
    if (preferred.ends_with(".webp")) {
        const std::string legacy = preferred.substr(0, preferred.size() - 5) + ".tga";
        if (ValidNlibTga(legacy)) return legacy;
    }
    return {};
}

std::string CachedNlibHero(std::uint64_t title_id) {
    if (title_id == 0) return {};
    const std::string path = NlibHeroPath(title_id);
    return AvailableArtwork(path);
}

int CachedNlibPlayers(std::uint64_t title_id) {
    if (title_id == 0) return 0;
    std::FILE* file = std::fopen(NlibPlayersPath(title_id).c_str(), "rb");
    if (!file) return 0;
    int players = 0;
    const int read = std::fscanf(file, "%d", &players);
    (void)std::fclose(file);
    return read == 1 && players > 0 && players <= 16 ? players : 0;
}

void CacheNlibPlayers(std::uint64_t title_id, int players) {
    if (title_id == 0 || players <= 0 || players > 16) return;
    (void)mkdir(Eden::CoversDir().c_str(), 0777);
    const std::string path = NlibPlayersPath(title_id);
    const std::string staged = path + ".new";
    std::FILE* file = std::fopen(staged.c_str(), "wb");
    if (!file) return;
    const bool written = std::fprintf(file, "%d\n", players) > 0;
    const bool closed = std::fclose(file) == 0;
    if (!written || !closed || std::rename(staged.c_str(), path.c_str()) != 0)
        (void)std::remove(staged.c_str());
}

constexpr int kNlibCacheSchema = 3; // v3 persists artwork refresh epochs

struct NlibEnrichment {
    bool artwork_changed = false; // a cached image was replaced
    std::string icon;
    std::string hero;
    std::vector<std::string> screenshots;
    int max_players = 0;
    std::string name;
    std::string intro;
    std::string description;
    std::string publisher;
    std::string developer;
    std::string release_date;
    std::string categories;
};

std::string CachedNlibIcon(std::uint64_t title_id) {
    if (title_id == 0) return {};
    const std::string path = NlibIconPath(title_id);
    return AvailableArtwork(path);
}

std::vector<std::string> CachedNlibScreens(std::uint64_t title_id) {
    std::vector<std::string> screens;
    if (title_id == 0) return screens;
    for (int index = 1; index <= 3; ++index) {
        const std::string path = NlibScreenshotPath(title_id, index);
        if (auto available = AvailableArtwork(path); !available.empty()) screens.push_back(available);
    }
    return screens;
}

bool LoadNlibMetadata(std::uint64_t title_id, const std::string& language, nlohmann::json* out) {
    if (out == nullptr) return false;
    std::ifstream file(NlibMetadataPath(title_id, language), std::ios::binary);
    if (!file) return false;
    try {
        file >> *out;
        return out->is_object();
    } catch (...) {
        return false;
    }
}

void ApplyNlibMetadata(const nlohmann::json& json, NlibEnrichment* result) {
    if (result == nullptr || !json.is_object()) return;
    const auto string_value = [&](const char* key) -> std::string {
        const auto it = json.find(key);
        return it != json.end() && it->is_string() ? it->get<std::string>() : std::string{};
    };
    result->name = string_value("name");
    result->intro = string_value("intro");
    result->description = string_value("description");
    result->publisher = string_value("publisher");
    result->developer = string_value("developer");
    result->release_date = string_value("releaseDate");
    result->categories = json.contains("category") ? JoinJsonStrings(json["category"]) : std::string{};
    const auto players_it = json.find("numberOfPlayers");
    const int players = players_it != json.end() && players_it->is_number_integer() ?
        players_it->get<int>() : 0;
    if (players > 0 && players <= 16) result->max_players = players;
}

bool CacheNlibJpeg(const std::string& endpoint, const std::string& path,
                   std::size_t minimum_bytes = 1024,
                   const std::atomic<bool>* cancel = nullptr) {
    // Cancellation avoids new network requests and expensive JPEG/PNG-to-WebP
    // conversion; an HTTP request already in flight must time out naturally.
    if (cancel && cancel->load(std::memory_order_acquire)) return false;
    const auto response = Common::Net::MakeRequest("https://api.nlib.cc", endpoint);
    if (!response || (cancel && cancel->load(std::memory_order_acquire)))
        return false;
    const std::string& body = *response;
    const bool jpeg = body.size() >= 2 &&
        static_cast<unsigned char>(body[0]) == 0xff &&
        static_cast<unsigned char>(body[1]) == 0xd8;
    const bool png = body.size() >= 8 &&
        std::memcmp(body.data(), "\x89PNG\r\n\x1a\n", 8) == 0;
    // stb_image decodes both; reject unexpected HTML/error responses instead
    // of persisting them as permanently broken thumbnails.
    if (body.size() < minimum_bytes || body.size() > (16u << 20) || (!jpeg && !png))
        return false;
    if (cancel && cancel->load(std::memory_order_acquire)) return false;
    (void)mkdir(Eden::CoversDir().c_str(), 0777);
    const std::string staged = path + ".new";
    if (WriteJpegWebP(body, staged) && std::rename(staged.c_str(), path.c_str()) == 0)
        return true;
    (void)std::remove(staged.c_str());
    return false;
}

// Optional real retail case images from the build-time filtered public catalog.
// No full metadata archive, credentials, HTTP or XML parsing on the console.
// Matching is exact and skips colliding release editions at index-generation time.
using BoxIndex = std::unordered_map<std::string, std::array<std::vector<std::string>, 8>>;

std::string CaseKey(const std::string& title) {
    std::string key;
    key.reserve(title.size());
    bool spaced = false;
    for (unsigned char byte : title) {
        char c = static_cast<char>(byte);
        if (c >= 'A' && c <= 'Z') c = static_cast<char>(c - 'A' + 'a');
        if ((c >= 'a' && c <= 'z') || (c >= '0' && c <= '9')) {
            key.push_back(c);
            spaced = false;
        } else if (!key.empty() && !spaced) {
            key.push_back(' ');
            spaced = true;
        }
    }
    while (!key.empty() && key.back() == ' ') key.pop_back();
    return key;
}

bool SafeCaseFilename(const std::string& file) {
    if (file.size() < 40 || file.size() > 48) return false;
    for (unsigned char c : file)
        if (!((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') ||
              (c >= '0' && c <= '9') || c == '-' || c == '_' || c == '.'))
            return false;
    const auto dot = file.rfind('.');
    if (dot == std::string::npos) return false;
    const std::string ext = file.substr(dot);
    return ext == ".jpg" || ext == ".jpeg" || ext == ".png";
}

// The host index carries region:filename for each actual flat scan.
// Select a localized physical edition independently for front/back/spine.
// Fallbacks remain available (including North American scans for EN users).
bool SafeCaseCandidate(const std::string& token) {
    const auto colon = token.find(':');
    if (colon == std::string::npos) return SafeCaseFilename(token); // v3 fallback
    if (colon == 0 || colon > 12) return false;
    for (std::size_t i = 0; i < colon; ++i) {
        const char c = token[i];
        if (!((c >= 'a' && c <= 'z') || (c >= '0' && c <= '9')))
            return false;
    }
    return SafeCaseFilename(token.substr(colon + 1));
}

std::vector<std::string> LocaleCaseCandidates(
    const std::vector<std::string>& entries, int language_choice, int face) {
    language_choice = std::clamp(language_choice, 0,
        static_cast<int>(std::size(Eden::kLanguageKeys)) - 1);
    const std::string locale = Eden::kLanguageKeys[language_choice];
    std::vector<std::string> regions;
    if (locale == "en-US" || locale == "es-419" || locale == "pt-BR")
        regions = {"us", "ca", "world", "uk", "eu", "fr"};
    else if (locale == "en-GB")
        // UK rear copy should stay English; use the US scan before an
        // unlocalized European back. PEGI European fronts remain preferred.
        regions = face == 1 ? std::vector<std::string>{"uk", "us", "ca", "world", "eu"} :
                              std::vector<std::string>{"uk", "eu", "us", "world", "ca"};
    else if (locale == "fr-CA")
        regions = {"ca", "fr", "us", "world", "eu"};
    else if (locale == "fr")
        regions = {"fr", "eu", "world", "uk", "ca", "us"};
    else if (locale == "ja")
        regions = {"jp", "asia", "world", "us", "eu"};
    else if (locale == "ko" || locale.rfind("zh", 0) == 0)
        regions = {"asia", "kr", "jp", "world", "us", "eu"};
    else {
        const auto hyphen = locale.find('-');
        const std::string lang = locale.substr(0, hyphen);
        regions = {lang, "eu", "world", "uk", "us", "ca"};
    }
    struct Candidate { int priority; std::size_t order; std::string file; };
    std::vector<Candidate> choices;
    choices.reserve(entries.size());
    for (std::size_t i = 0; i < entries.size(); ++i) {
        const std::string& token = entries[i];
        if (!SafeCaseCandidate(token)) continue;
        const auto colon = token.find(':');
        const std::string region = colon == std::string::npos ?
            "other" : token.substr(0, colon);
        const std::string file = colon == std::string::npos ?
            token : token.substr(colon + 1);
        int priority = 100;
        for (std::size_t position = 0; position < regions.size(); ++position)
            if (region == regions[position]) {
                priority = static_cast<int>(position);
                break;
            }
        choices.push_back({priority, i, file});
    }
    std::stable_sort(choices.begin(), choices.end(),
        [](const Candidate& a, const Candidate& b) {
            return a.priority < b.priority;
        });
    std::vector<std::string> sorted;
    sorted.reserve(choices.size());
    // The original linear duplicate scan was quadratic in the size of a
    // game's LaunchBox case index. Preserve the stable region-first ordering,
    // but admit each distinct filename in expected constant time.
    std::unordered_set<std::string> seen;
    seen.reserve(choices.size());
    for (const auto& candidate : choices)
        if (seen.insert(candidate.file).second)
            sorted.push_back(candidate.file);
    return sorted;
}

const BoxIndex& RetailCaseIndex() {
    static const BoxIndex index = [] {
        BoxIndex items;
        // Mounted titles can expose eboot.bin but omit auxiliary ui/ files.
        // Use the same fallback search as fonts, translations and launcher art.
        const std::string catalog_path = Eden::AppResourceFile("ui/box-art-index.tsv");
        std::ifstream input(catalog_path);
        const bool opened = static_cast<bool>(input);
        if (!opened) {
            std::fprintf(stderr, "EDEN_CASE_INDEX status=missing path=%s\n",
                         catalog_path.c_str());
        }
        // A tiny, source-verified fallback index is packaged independently
        // from the optional multi-thousand-title LaunchBox build snapshot.
        // The full snapshot always wins; fallback fills missing NS2 faces.
        const auto load_rows = [&](std::istream& source, bool supplemental) {
        std::string row;
        while (std::getline(source, row) && (items.size() < 20000 || supplemental)) {
            if (row.empty() || row[0] == '#' || row.size() > 5000) continue;
            const auto a = row.find('\t');
            if (a == std::string::npos) continue;
            const auto b = row.find('\t', a + 1);
            if (b == std::string::npos) continue;
            const auto c = row.find('\t', b + 1);
            const std::string title = row.substr(0, a);
            const std::string front = row.substr(a + 1, b - a - 1);
            const std::string back = row.substr(b + 1,
                c == std::string::npos ? c : c - b - 1);
            const auto d = c == std::string::npos ? c : row.find('\t', c + 1);
            const std::string spine = c == std::string::npos ? "-" :
                row.substr(c + 1, d == std::string::npos ? d : d - c - 1);
            std::array<std::string, 5> scene_columns{"-", "-", "-", "-", "-"};
            std::size_t start = d;
            for (std::string& scene : scene_columns) {
                if (start == std::string::npos) break; // v4 index remains supported
                const std::size_t end = row.find('\t', start + 1);
                scene = row.substr(start + 1,
                    end == std::string::npos ? end : end - start - 1);
                start = end;
            }
            if (title.empty() || title.size() > 170) continue;
            const auto split_candidates = [](const std::string& value) {
                std::vector<std::string> found;
                if (value == "-") return found;
                std::size_t start = 0;
                while (start < value.size() && found.size() < 12) {
                    const auto end = value.find(';', start);
                    const std::string part = value.substr(
                        start, end == std::string::npos ? end : end - start);
                    if (!SafeCaseCandidate(part)) {
                        found.clear();
                        break; // reject an invalid indexed row
                    }
                    found.push_back(part);
                    if (end == std::string::npos) break;
                    start = end + 1;
                }
                return found;
            };
            auto fronts = split_candidates(front);
            auto backs = split_candidates(back);
            auto spines = split_candidates(spine);
            if ((front != "-" && fronts.empty()) ||
                (back != "-" && backs.empty()) ||
                (spine != "-" && spines.empty())) continue;
            std::array<std::vector<std::string>, 5> scenes{};
            for (int i = 0; i < 5; ++i)
                scenes[i] = split_candidates(scene_columns[i]);
            // Invalid optional scene metadata must never invalidate valid
            // original front/back/spine entries from the same row.
            std::array<std::vector<std::string>, 8> faces{
                std::move(fronts), std::move(backs), std::move(spines),
                std::move(scenes[0]), std::move(scenes[1]), std::move(scenes[2]),
                std::move(scenes[3]), std::move(scenes[4])};
            auto [it, inserted] = items.emplace(title, faces);
            if (supplemental && !inserted) {
                for (std::size_t side = 0; side < faces.size(); ++side) {
                    if (it->second[side].empty())
                        it->second[side] = std::move(faces[side]);
                }
            }
        }
        };
        load_rows(input, false);
        const auto primary_count = items.size();
        const std::string fallback_path = Eden::AppResourceFile("ui/box-art-fallback.tsv");
        std::ifstream fallback(fallback_path);
        if (fallback) load_rows(fallback, true);
        std::fprintf(stderr,
                     "EDEN_CASE_FALLBACK status=%s added=%zu path=%s\n",
                     fallback ? "loaded" : "missing",
                     items.size() - primary_count, fallback_path.c_str());
        std::fprintf(stderr, "EDEN_CASE_INDEX status=%s entries=%zu path=%s\n",
                     opened ? "loaded" : "missing", items.size(), catalog_path.c_str());
        return items;
    }();
    return index;
}

std::string CaseFacePath(std::uint64_t title_id, const char* side) {
    char id[17]{};
    std::snprintf(id, sizeof(id), "%016llX", static_cast<unsigned long long>(title_id));
    return Eden::CoversDir() + "/box-" + side + "-" + id + ".webp";
}

// Scenic images are actual LaunchBox screenshots/fanart, cached separately
// from genuine physical box scans. Original covers never read these paths.
std::vector<std::string> CachedCaseScenes(std::uint64_t title_id) {
    std::vector<std::string> scenes;
    if (title_id == 0) return scenes;
    for (int i : {3, 4, 5, 1, 2}) {
        const std::string side = "scene-" + std::to_string(i);
        const std::string path = CaseFacePath(title_id, side.c_str());
        if (auto available = AvailableArtwork(path); !available.empty()) scenes.push_back(available);
    }
    return scenes;
}

// Nlib screenshots are retained first; independent LaunchBox pictures fill
// empty slots and support the rear collage, never the actual back scan.
void AppendCaseScenes(std::vector<std::string>& screens, std::uint64_t title_id) {
    for (const auto& scene : CachedCaseScenes(title_id)) {
        if (screens.size() >= 6) break;
        if (std::find(screens.begin(), screens.end(), scene) == screens.end())
            screens.push_back(scene);
    }
}

bool FetchCaseFace(const std::vector<std::string>& candidates,
                   const std::string& destination, bool narrow_spine,
                   const std::atomic<bool>* cancel) {
    if (candidates.empty() ||
        (cancel && cancel->load(std::memory_order_acquire))) return false;
    std::string best;
    std::string best_source;
    std::size_t attempts = 0;
    std::size_t transport_failures = 0;
    std::size_t invalid_responses = 0;
    // The index is ranked by REGION, then by alternative. Take the first
    // DECODABLE face from the highest available region, not the face with the
    // most pixels across regions (which wrongly selected North America over
    // Europe). Generated older cached covers are migrated by .source markers.
    // Manual .png/.jpg/.jpeg overrides are protected in EnsureRetailCase.
    // No network activity occurs on the launch/render thread.
    // A verified Mario Kart World front has seven real Box - Front
    // candidates, but its three highest-ranked PNGs fail native stb decode.
    // Keep a bounded budget while permitting real JPEG alternatives in the
    // SAME source category. Never substitute Reconstructed/merchandise art.
    for (const std::string& filename : candidates) {
        if (attempts >= 7 ||
            (cancel && cancel->load(std::memory_order_acquire))) break;
        if (!SafeCaseFilename(filename)) {
            ++invalid_responses;
            continue;
        }
        ++attempts;
        // Current LaunchBox metadata has both legacy UUID files and newer
        // r2_ files hosted on the GamesDB image CDN. Trying the legacy host
        // for an r2_ image made genuine NS2 boxes silently disappear.
        const bool r2 = filename.rfind("r2_", 0) == 0;
        const char* image_host = r2 ? "https://gamesdb-images.launchbox.gg" :
                                     "https://images.launchbox-app.com";
        const auto response = Common::Net::MakeRequest(image_host, "/" + filename);
        if (!response) {
            ++transport_failures;
            std::fprintf(stderr, "EDEN_CASE_CDN status=network-failed file=%s attempt=%zu side=%s\n",
                         filename.c_str(), attempts, narrow_spine ? "spine" : "face");
            continue;
        }
        if (cancel && cancel->load(std::memory_order_acquire)) break;
        const std::string& body = *response;
        const bool jpeg = body.size() >= 2 &&
            static_cast<unsigned char>(body[0]) == 0xff &&
            static_cast<unsigned char>(body[1]) == 0xd8;
        const bool png = body.size() >= 8 &&
            std::memcmp(body.data(), "\x89PNG\r\n\x1a\n", 8) == 0;
        if (body.size() < 1024 || body.size() > (16u << 20) || (!jpeg && !png)) {
            ++invalid_responses;
            std::fprintf(stderr, "EDEN_CASE_CDN status=invalid-body file=%s bytes=%zu jpeg=%d png=%d\n",
                         filename.c_str(), body.size(), jpeg, png);
            continue;
        }
        int w = 0, h = 0, channels = 0;
        if (!stbi_info_from_memory(
                reinterpret_cast<const unsigned char*>(body.data()),
                static_cast<int>(body.size()), &w, &h, &channels) ||
            w < (narrow_spine ? 16 : 128) ||
            h < (narrow_spine ? 250 : 200) || w > 4096 || h > 4096 ||
            static_cast<std::uint64_t>(w) * h > 3840u * 2160u ||
            ((destination.find("/box-front-") != std::string::npos ||
              destination.find("/box-back-") != std::string::npos) &&
             static_cast<std::uint64_t>(h) * 4 < static_cast<std::uint64_t>(w) * 5)) {
            ++invalid_responses;
            std::fprintf(stderr, "EDEN_CASE_CDN status=invalid-image file=%s bytes=%zu width=%d height=%d reason=%s\n",
                         filename.c_str(), body.size(), w, h,
                         stbi_failure_reason() ? stbi_failure_reason() : "invalid-dimensions");
            continue;
        }
        // A larger image from a different region is NOT a better scan of
        // this edition. Once the first region-ranked usable candidate
        // decodes, do not replace it with an unrelated region.
        best = body;
        best_source = filename;
        break;
    }
    if (best.empty() || (cancel && cancel->load(std::memory_order_acquire))) {
        std::fprintf(stderr,
                     "EDEN_CASE_FETCH status=unavailable side=%s attempts=%zu network=%zu invalid=%zu\n",
                     narrow_spine ? "spine" : "face",
                     attempts, transport_failures, invalid_responses);
        return false;
    }
    (void)mkdir(Eden::CoversDir().c_str(), 0777);
    const std::string staged = destination + ".new";
    if (WriteJpegWebP(best, staged, true) &&
        std::rename(staged.c_str(), destination.c_str()) == 0) {
        // Provenance for a generated WebP. A newer index can replace stale
        // US artwork even when the cached US image has higher resolution.
        // The WebP remains usable if this tiny receipt write fails.
        std::ofstream receipt(destination + ".source", std::ios::trunc);
        if (receipt) receipt << best_source << '\n';
        std::fprintf(stderr, "EDEN_CASE_FETCH status=stored side=%s source=%s attempts=%zu bytes=%zu\n",
                     narrow_spine ? "spine" : "face", best_source.c_str(), attempts, best.size());
        return true;
    }
    (void)std::remove(staged.c_str());
    std::fprintf(stderr, "EDEN_CASE_FETCH status=write-failed side=%s attempts=%zu\n",
                 narrow_spine ? "spine" : "face", attempts);
    return false;
}

// All physical box scans, NS1 and NS2, come exclusively from the verified
// region-ranked LaunchBox index. No retail-product-photo fallback is allowed.
// Missing scans use the same opaque procedural case renderer as NS1.
unsigned EnsureRetailCase(std::uint64_t title_id, const std::string& name,
                      const std::string& alternate_name, int language_choice,
                      const std::atomic<bool>* cancel) {
    if (title_id == 0 || (cancel && cancel->load(std::memory_order_acquire))) return 0;
    const auto& index = RetailCaseIndex();
    const auto selected = [&]() -> BoxIndex::const_iterator {
        auto it = index.find(CaseKey(name));
        if (it != index.end()) return it;
        return index.find(CaseKey(alternate_name));
    }();
    if (selected == index.end()) {
        std::fprintf(stderr, "EDEN_CASE_LOOKUP title=%016llX status=no-match name=%s alternate=%s index_entries=%zu\n",
                     static_cast<unsigned long long>(title_id), name.c_str(),
                     alternate_name.c_str(), index.size());
        // A retailer product photo is NOT a flat box scan: its white
        // surrounding canvas was rendered as the physical jacket front.
        // Keep the true extracted icon/hero for procedural fallback rather
        // than writing a counterfeit "box-front" from a shop photo.
        return 0u;
    }
    std::fprintf(stderr,
                 "EDEN_CASE_LOOKUP title=%016llX status=match front=%zu back=%zu spine=%zu scenes=%zu/%zu/%zu\n",
                 static_cast<unsigned long long>(title_id),
                 selected->second[0].size(), selected->second[1].size(),
                 selected->second[2].size(), selected->second[3].size(),
                 selected->second[4].size(), selected->second[5].size());
    // Both Home and Library may enrich the same title at once. Serialize
    // background fetches so the second worker reads the first worker's
    // finished cache, but never hold launcher teardown hostage to this wait.
    // No socket request or mutex sleep runs on the UI/render thread.
    static std::array<std::mutex, 64> locks;
    std::unique_lock guard(locks[title_id % locks.size()], std::defer_lock);
    while (!guard.try_lock()) {
        if (cancel && cancel->load(std::memory_order_acquire)) return 0;
        std::this_thread::sleep_for(std::chrono::milliseconds(50));
    }
    if (cancel && cancel->load(std::memory_order_acquire)) return 0;
    // The physical scans supplied by users have no Encore .source receipt.
    // Migrate and reclaim ONLY our previously downloaded retail cases.
    unsigned migrated_faces = 0;
    unsigned side_index = 0;
    for (const char* side : {"front", "back", "spine",
                             "scene-1", "scene-2", "scene-3", "scene-4", "scene-5"}) {
        if (cancel && cancel->load(std::memory_order_acquire)) return 0;
        if (MigrateGeneratedTga(CaseFacePath(title_id, side), true))
            migrated_faces |= 1u << side_index;
        ++side_index;
    }
    static std::mutex retry_mutex;
    static std::unordered_map<std::uint64_t, std::chrono::steady_clock::time_point> retries;
    {
        std::lock_guard retry(retry_mutex);
        const auto it = retries.find(title_id);
        if (it != retries.end() && std::chrono::steady_clock::now() < it->second)
            return 0;
        // Failed image hosts, cancellation or an incomplete side must not
        // disable all retries for four hours on a newly installed game.
        retries[title_id] = std::chrono::steady_clock::now() + std::chrono::minutes(5);
    }
    bool all_ready = true;
    // Migration to WebP also changes the art; notify the UI even when the
    // underlying CDN candidate was already in cache.
    unsigned changed_faces = migrated_faces;
    // Even compact genuine spine scans are preferable to a fabricated title.
    // NS2 games may have a real front and spine but NO uploaded back.
    // Their spine must not depend on the existence of a back scan.
    for (int side = 0; side < 8; ++side) {
        if (cancel && cancel->load(std::memory_order_acquire)) {
            // Aborted title switch must not lock the next attempt out for
            // five minutes after a partial or cancelled CDN transaction.
            all_ready = false;
            break;
        }
        // Front and back always fetch first. A successful first-pass pair
        // can be followed by its spine in the SAME background enrichment;
        // otherwise the 5-minute retry could leave a complete paper wrap
        // without its printed spine until the next launcher session.
        // Gameplay previews remain independent of real back paper.
        const auto candidates = LocaleCaseCandidates(selected->second[side], language_choice, side);
        if (candidates.empty()) continue;
        const char* const names[] = {
            "front", "back", "spine", "scene-1", "scene-2", "scene-3", "scene-4", "scene-5"};
        const std::string path = CaseFacePath(title_id, names[side]);
        // User-provided original scans win. Cached low-resolution CDN scans
        // may be upgraded when a better ranked alternative becomes available.
        const std::string base = path.substr(0, path.size() - 5);
        if (IsFile(base + ".png") || IsFile(base + ".jpg") ||
            IsFile(base + ".jpeg")) continue;
        // Revalidate region provenance when the package index changes.
        // Older TGA files without .source (or from another region) must be
        // re-fetched, not silently accepted solely for their pixel count.
        std::ifstream receipt(path + ".source");
        std::string cached_source;
        if (receipt) std::getline(receipt, cached_source);
        if (cached_source == candidates.front()) {
            int width = 0;
            int height = 0;
            // Preserve narrow authentic NS2 spines even with no back scan.
            if (ValidNlibWebP(path, &width, &height) &&
                ((side == 2 && width >= 16 && height >= 250) ||
                 (side >= 3 && width >= 128 && height >= 200) ||
                 ((side == 0 || side == 1) && width >= 128 && height >= 200 &&
                  static_cast<std::uint64_t>(height) * 4 >= static_cast<std::uint64_t>(width) * 5))) {
                continue;
            }
        }
        // If network retrieval fails, existing cached artwork remains usable;
        // migration can be retried without blocking rendering.
        if (!FetchCaseFace(candidates, path, side == 2, cancel)) {
            all_ready = false;
            std::fprintf(stderr, "EDEN_CASE_FACE title=%016llX side=%d status=unavailable\n",
                         static_cast<unsigned long long>(title_id), side);
        } else {
            changed_faces |= (1u << side); // Only successful atomic replacements.
            // A fallback candidate remains usable, but only retry its higher
            // priority European/locale scan on the next bounded refresh.
            std::ifstream refreshed(path + ".source");
            std::string actual;
            if (refreshed) std::getline(refreshed, actual);
            if (actual != candidates.front()) all_ready = false;
        }
    }
    if (all_ready || (cancel && cancel->load(std::memory_order_acquire))) {
        // A fully successful refresh needs no retry guard; a cancelled
        // refresh is immediately retryable on the next launcher session.
        std::lock_guard retry(retry_mutex);
        retries.erase(title_id);
    }
    return changed_faces;
}

NlibEnrichment CachedNlibEnrichment(std::uint64_t title_id, int language_choice) {
    NlibEnrichment result;
    if (title_id == 0) return result;
    result.icon = CachedNlibIcon(title_id);
    result.hero = CachedNlibHero(title_id);
    result.screenshots = CachedNlibScreens(title_id);
    result.max_players = CachedNlibPlayers(title_id);
    nlohmann::json metadata;
    if (LoadNlibMetadata(title_id, NlibLanguageCode(language_choice), &metadata))
        ApplyNlibMetadata(metadata, &result);
    if (result.hero.empty() && !result.screenshots.empty())
        result.hero = result.screenshots.front();
    return result;
}

// Nlib enriches the launcher only; no game ever depends on the network. The ROM icon stays the
// offline fallback. Cards prefer Nlib's square icon, Home prefers its 16:9 banner, and Library
// details use all available gameplay screenshots (up to the current API cap). Every
// title is queued for complete artwork at startup, not only on Library selection.
NlibEnrichment EnsureNlibEnrichment(std::uint64_t title_id, int language_choice,
                                       const std::atomic<bool>* cancel = nullptr) {
    const auto cancelled = [cancel] {
        return cancel && cancel->load(std::memory_order_acquire);
    };
    if (title_id == 0 || cancelled()) return {};

    // Home and Library can request the same title at the same time. Cache writes use
    // the same .new staging path, so serialize per hash bucket while leaving other
    // titles free to enrich in parallel.
    static std::array<std::mutex, 16> title_locks;
    std::scoped_lock title_lock{title_locks[title_id % title_locks.size()]};
    if (cancelled()) return {};

    // Every Nlib legacy TGA was generated by Encore, unlike arbitrary
    // user-provided case artwork. Convert once locally; do not redownload
    // existing banners/icons/screens or leave old multi-megabyte files.
    bool migrated = MigrateGeneratedTga(NlibHeroPath(title_id), false);
    migrated |= MigrateGeneratedTga(NlibIconPath(title_id), false);
    for (int index = 1; index <= 3; ++index) {
        if (cancelled()) return {};
        migrated |= MigrateGeneratedTga(NlibScreenshotPath(title_id, index), false);
    }

    NlibEnrichment result = CachedNlibEnrichment(title_id, language_choice);
    result.artwork_changed |= migrated;
    const std::string language = NlibLanguageCode(language_choice);
    nlohmann::json metadata;
    const bool cached_metadata = LoadNlibMetadata(title_id, language, &metadata);
    const bool current_metadata_cache = cached_metadata && metadata.is_object() &&
        metadata.value("_encore_cache_schema", 0) >= kNlibCacheSchema;
    const auto now_seconds = std::chrono::duration_cast<std::chrono::seconds>(
        std::chrono::system_clock::now().time_since_epoch()).count();
    std::int64_t last_metadata_check = 0;
    std::int64_t last_artwork_check = 0;
    if (cached_metadata && metadata.is_object()) {
        const auto checked = metadata.find("_encore_checked_at");
        if (checked != metadata.end() && checked->is_number_integer())
            last_metadata_check = checked->get<std::int64_t>();
        const auto artwork = metadata.find("_encore_artwork_checked_at");
        if (artwork != metadata.end() && artwork->is_number_integer())
            last_artwork_check = artwork->get<std::int64_t>();
    }
    // Legacy schema-v2 metadata (including negative art results) must expire.
    // Use persisted timestamps rather than PS5 filesystem mtime syscalls.
    const bool metadata_expired = !current_metadata_cache ||
        last_metadata_check <= 0 || now_seconds < last_metadata_check ||
        now_seconds - last_metadata_check >= 7LL * 24 * 60 * 60;
    // Valid but outdated images are refreshed monthly, atomically.
    const bool artwork_expired = last_artwork_check <= 0 ||
        now_seconds < last_artwork_check ||
        now_seconds - last_artwork_check >= 30LL * 24 * 60 * 60;

    char id[17]{};
    std::snprintf(id, sizeof(id), "%016llX", static_cast<unsigned long long>(title_id));
    // Bounded retry map is launcher-only and independent of PS5 filesystem
    // timestamps. Old filesystem::last_write_time caused an unnecessary native
    // syscall on every selection, even for a title absent from Nlib.
    static std::mutex retry_guard;
    static std::unordered_map<std::string, std::chrono::steady_clock::time_point> next_retry;
    const std::string retry_key = std::string{id} + ":" + language;
    std::fprintf(stderr,
                 "EDEN_NLIB_BEGIN title_id=%s lang=%s cached_meta=%d cache_schema=%d cached_icon=%d cached_hero=%d cached_screens=%zu cached_players=%d\n",
                 id, language.c_str(), cached_metadata, current_metadata_cache, !result.icon.empty(), !result.hero.empty(),
                 result.screenshots.size(), result.max_players);

    try {
        bool refreshed_metadata = false;
        // One localized metadata request tells us which media exist and fills the selected game's
        // actual title/intro/publisher/etc. The response is cached separately per Nlib language.
        bool has_icon = cached_metadata && metadata.contains("icon") && metadata["icon"].is_string();
        bool has_banner = cached_metadata && metadata.contains("banner") && metadata["banner"].is_string();
        int screen_count = static_cast<int>(result.screenshots.size());
        if (cached_metadata && metadata.contains("screens") && metadata["screens"].is_object())
            screen_count = std::max(screen_count, metadata["screens"].value("count", 0));
        // A title can acquire Nlib artwork after it was first catalogued.
        // Refresh sparse metadata periodically without filesystem timestamp
        // calls, and never suppress downloads already described by cached
        // metadata just because a refresh is temporarily rate-limited.
        const bool sparse_metadata = current_metadata_cache &&
                                    (!has_icon || !has_banner || screen_count == 0);
        const bool needs_metadata = metadata_expired || sparse_metadata;
        bool may_request_metadata = needs_metadata;
        if (needs_metadata) {
            std::lock_guard lock(retry_guard);
            const auto it = next_retry.find(retry_key);
            if (it != next_retry.end() && std::chrono::steady_clock::now() < it->second)
                may_request_metadata = false;
        }
        if (needs_metadata && !may_request_metadata && !current_metadata_cache)
            return result;
        if (may_request_metadata) {
            if (cancelled()) return result;
            const std::string metadata_endpoint = std::string{"/nx/"} + id + "?lang=" + language +
                "&fields=name,intro,description,publisher,developer,releaseDate,category,languages,"
                "numberOfPlayers,icon,banner,screens";
            if (const auto response = Common::Net::MakeRequest("https://api.nlib.cc", metadata_endpoint)) {
                metadata = nlohmann::json::parse(*response);
                if (metadata.is_object()) {
                    refreshed_metadata = true;
                    metadata["_encore_cache_schema"] = kNlibCacheSchema;
                    metadata["_encore_checked_at"] = now_seconds;
                    metadata["_encore_artwork_checked_at"] = last_artwork_check;
                    (void)AtomicWriteText(NlibMetadataPath(title_id, language), metadata.dump());
                    ApplyNlibMetadata(metadata, &result);
                    has_icon = metadata.contains("icon") && metadata["icon"].is_string();
                    has_banner = metadata.contains("banner") && metadata["banner"].is_string();
                    if (metadata.contains("screens") && metadata["screens"].is_object())
                        screen_count = std::max(screen_count, metadata["screens"].value("count", 0));
                }
                std::lock_guard lock(retry_guard);
                if (!metadata.is_object() || !has_icon || !has_banner || screen_count == 0)
                    next_retry[retry_key] = std::chrono::steady_clock::now() +
                                            std::chrono::minutes(30);
                else
                    next_retry.erase(retry_key);
            } else {
                // Keep previously cached image links on a transient timeout.
                // A newly discovered title retries in five minutes.
                std::lock_guard lock(retry_guard);
                next_retry[retry_key] = std::chrono::steady_clock::now() +
                                        std::chrono::minutes(5);
                if (!current_metadata_cache) return result;
            }
        }
        if (cancelled()) return result;
        if (result.max_players > 0) CacheNlibPlayers(title_id, result.max_players);
        const bool refresh_existing_artwork = refreshed_metadata && artwork_expired;

        // Nlib banner, icon and every advertised screenshot are fetched in
        // ONE pass for every installed title. Independent HTTPS requests run
        // concurrently on this background worker, not serially at 3 seconds
        // each. No hidden "screens later in Library" scheduling.
        std::vector<std::future<bool>> downloads;
        const auto request_media = [&](std::string endpoint, std::string path,
                                       std::size_t minimum = 1024) {
            if (cancelled()) return;
            downloads.emplace_back(std::async(std::launch::async,
                [endpoint = std::move(endpoint), path = std::move(path), minimum, cancel] {
                    return CacheNlibJpeg(endpoint, path, minimum, cancel);
                }));
        };

        // A screenshot-backed hero does not prove a real banner was cached.
        if (has_banner && (!ValidNlibWebP(NlibHeroPath(title_id)) || refresh_existing_artwork))
            request_media(std::string{"/nx/"} + id + "/banner/1080p",
                          NlibHeroPath(title_id), 4096);
        if (has_icon && (!ValidNlibWebP(NlibIconPath(title_id)) || refresh_existing_artwork))
            request_media(std::string{"/nx/"} + id + "/icon/512",
                          NlibIconPath(title_id));

        const int wanted_screens = std::clamp(screen_count, 0, 3);
        for (int index = 1; index <= wanted_screens; ++index) {
            if (cancelled()) break;
            const std::string path = NlibScreenshotPath(title_id, index);
            if (!ValidCachedArtwork(path) || refresh_existing_artwork)
                request_media(std::string{"/nx/"} + id + "/screen/" + std::to_string(index),
                              path, 4096);
        }
        // Join only in the background enrichment task. The UI thread remains
        // free to render/input; title mutex excludes duplicate .new file writes.
        int failed_media = 0;
        for (auto& pending : downloads) {
            if (pending.get()) result.artwork_changed = true;
            else ++failed_media;
        }
        if (!cancelled() && refreshed_metadata && artwork_expired && failed_media == 0) {
            metadata["_encore_artwork_checked_at"] = now_seconds;
            (void)AtomicWriteText(NlibMetadataPath(title_id, language), metadata.dump());
        }
        if (failed_media > 0)
            std::fprintf(stderr, "EDEN_NLIB_ASSETS title_id=%s failed=%d attempted=%zu\n",
                         id, failed_media, downloads.size());

        const NlibEnrichment complete = CachedNlibEnrichment(title_id, language_choice);
        if (!complete.icon.empty()) result.icon = complete.icon;
        if (!complete.hero.empty()) result.hero = complete.hero;
        result.screenshots = complete.screenshots;
        if (result.hero.empty() && !result.screenshots.empty())
            result.hero = result.screenshots.front();
    } catch (const std::exception& error) {
        Eden::Report("artwork", (std::string{"Nlib unavailable: "} + error.what()).c_str());
    }

    std::fprintf(stderr,
                 "EDEN_NLIB_RESULT title_id=%s icon=%d hero=%d screens=%zu players=%d\n", id,
                 !result.icon.empty(), !result.hero.empty(), result.screenshots.size(),
                 result.max_players);
    return result;
}

std::uintmax_t TreeBytes(const std::filesystem::path& root,
                        const std::atomic<bool>* cancel = nullptr) {
    if (cancel && cancel->load(std::memory_order_acquire)) return 0;
    std::error_code error;
    if (!std::filesystem::exists(root, error)) return 0;
    std::uintmax_t bytes = 0;
    std::filesystem::recursive_directory_iterator it(
        root, std::filesystem::directory_options::skip_permission_denied, error), end;
    while (!error && it != end) {
        if (cancel && cancel->load(std::memory_order_acquire)) return 0;
        std::error_code entry_error;
        if (it->is_regular_file(entry_error)) {
            const auto size = it->file_size(entry_error);
            if (!entry_error) bytes += size;
        }
        it.increment(error);
        if (error) error.clear(); // Skip an unreadable entry and continue where possible.
    }
    return bytes;
}

std::string StorageSize(std::uintmax_t bytes) {
    constexpr std::uintmax_t KiB = 1024;
    constexpr std::uintmax_t MiB = KiB * 1024;
    constexpr std::uintmax_t GiB = MiB * 1024;
    char text[64];
    if (bytes >= GiB)
        std::snprintf(text, sizeof(text), "%.1f GB", static_cast<double>(bytes) / static_cast<double>(GiB));
    else if (bytes >= MiB)
        std::snprintf(text, sizeof(text), "%.1f MB", static_cast<double>(bytes) / static_cast<double>(MiB));
    else
        std::snprintf(text, sizeof(text), "%.0f KB", static_cast<double>(bytes) / static_cast<double>(KiB));
    return text;
}


// A game's update and DLC: "Update 1.2.0, 2 DLC"; brief leaves the word out ("v1.2.0, 2 DLC") for
// places with little room.
std::string AddOnSummary(uint64_t title_id, bool brief = false) {
    char update[64]{};
    unsigned dlc = 0;
    eden_game_addons(title_id, update, sizeof(update), &dlc);
    std::string text;
    if (update[0]) text = brief ? (update[0] == 'v' ? std::string{update} : "v" + std::string{update}) :
                                  fill(tr("Update {0}"), {update});
    if (dlc) text += (text.empty() ? "" : ", ") + fill(tr("{0} DLC"), {std::to_string(dlc)});
    return text;
}

// The language a game will use for the chosen one (Settings > Language), and a note when the game
// does not offer the choice and falls back to another language.
struct GameLanguage {
    std::string label;
    std::string note;
};
GameLanguage LanguageFor(const std::string& path, uint64_t title_id, int choice) {
    const int chosen = Eden::kLanguageSettings[choice];
    const int used = eden_game_language(path.c_str(), Eden::AssetsPath("keys").c_str(), title_id, chosen);
    // The 13 additional official PS5 interface locales use a supported English
    // guest-language fallback. Never label the game's language as the chosen UI locale.
    GameLanguage result{tr(Eden::kLanguageLabels[choice < 18 ? choice : 0]), {}};
    if (used == chosen) return result;
    result.label = tr("Another language");
    // Only the legacy 18 selectors have distinct, supported guest-language enums.
    // The 13 new PS5 interface locales all map to English; scanning those as
    // guest-language names would falsely label an English game "Vietnamese".
    for (std::size_t i = 0; i < 18; ++i)
        if (Eden::kLanguageSettings[i] == used) result.label = tr(Eden::kLanguageLabels[i]);
    result.note = fill(tr("{0} not available"), {tr(Eden::kLanguageLabels[choice])});
    return result;
}

// Why a game did not start, as headless/main.cpp reports it. The reasons that are whole sentences
// are shown in the player's language; the others carry codes and file names and stay as they are.
// (tools/launcher/strings.py checks that main.cpp still says these.)
constexpr const char* kLaunchErrors[] = {
    TR("Selected ROM is no longer available"),
    TR("PS5 controller initialization failed"),
    TR("The game could not allocate PS5 memory. Close Eden Encore completely before retrying to release memory retained between games."),
    TR("Graphics backend initialization failed. Try another backend in Settings; see stderr.log and eden_log.txt for "
       "driver details."),
    TR("The game ran out of graphics memory. Lower the resolution in Settings, Video (or in the game's own settings) "
       "and start it again."),
};
std::string LaunchError(const std::string& reason) {
    std::string text = reason;
    for (const char* known : kLaunchErrors)
        if (reason == known) text = tr(known);
    // "Details:" follows it: a reason without its own full stop gets one.
    if (!text.empty() && text.back() != '.' && text.back() != '!' && text.back() != '?') text += '.';
    return text;
}

// Names of the subfolders (folders = true) or regular files in path, sorted without regard
// to case. Unlike ReadNativeDirectory, an odd entry is skipped rather than failing the
// folder: the Storage browser walks available roots/directories so an external root can be chosen.
std::vector<std::string> ListEntries(const std::string& path, bool folders, bool& ok) {
    ok = false;
    std::vector<std::string> names;
    const int fd = open(path.c_str(), O_RDONLY | O_DIRECTORY);
    if (fd < 0) return names;
    std::vector<char> buffer(65536);
    for (;;) {
        const int count = sceKernelGetdents(fd, buffer.data(), static_cast<int>(buffer.size()));
        if (count == 0) { ok = true; break; }
        if (count < 0 || count > static_cast<int>(buffer.size())) break;
        for (std::size_t offset = 0; offset + offsetof(dirent, d_name) < static_cast<std::size_t>(count);) {
            uint16_t length;
            uint8_t type;
            std::memcpy(&length, buffer.data() + offset + offsetof(dirent, d_reclen), sizeof(length));
            std::memcpy(&type, buffer.data() + offset + offsetof(dirent, d_type), sizeof(type));
            if (length <= offsetof(dirent, d_name) || offset + length > static_cast<std::size_t>(count)) break;
            const char* name = buffer.data() + offset + offsetof(dirent, d_name);
            const std::string entry(name, strnlen(name, length - offsetof(dirent, d_name)));
            offset += length;
            if (entry.empty() || entry == "." || entry == "..") continue;
            if (type == DT_LNK) continue;
            bool is_folder = type == DT_DIR, is_file = type == DT_REG;
            if (type == DT_UNKNOWN) {
                struct stat info {};
                const std::string full = path == "/" ? "/" + entry : path + "/" + entry;
                if (lstat(full.c_str(), &info) == 0) {
                    if (S_ISLNK(info.st_mode)) continue;
                } else if (errno != EPERM && errno != EACCES) {
                    continue;
                } else if (stat(full.c_str(), &info) != 0) {
                    continue;
                }
                is_folder = S_ISDIR(info.st_mode);
                is_file = S_ISREG(info.st_mode);
            }
            if (folders ? is_folder : is_file) names.push_back(entry);
        }
    }
    close(fd);
    const auto lower = [](std::string text) {
        for (char& c : text) c = static_cast<char>(std::tolower(static_cast<unsigned char>(c)));
        return text;
    };
    std::sort(names.begin(), names.end(), [&](const std::string& a, const std::string& b) {
        return lower(a) < lower(b);
    });
    return names;
}

std::string JoinPath(const std::string& directory, const std::string& name) {
    return directory == "/" ? "/" + name : directory + "/" + name;
}

// Files in directory with one of the (lower-case) extensions; -1 when it cannot be read.
int CountFiles(const std::string& directory, std::initializer_list<const char*> extensions) {
    bool ok = false;
    int count = 0;
    for (const auto& name : ListEntries(directory, false, ok)) {
        std::string lower = name;
        for (char& c : lower) c = static_cast<char>(std::tolower(static_cast<unsigned char>(c)));
        for (const char* extension : extensions)
            if (lower.size() > std::strlen(extension) && lower.ends_with(extension)) { ++count; break; }
    }
    return ok ? count : -1;
}

// Preserve the original count entry point while including BOTH extracted
// ExeFS and packaged base inputs inside a title folder. The Home setup
// counter must agree with the actual Library and CountInstalledGames.
int CountExeFsFolders(const std::string& directory) {
    bool ok = false;
    int count = 0;
    for (const auto& name : ListEntries(directory, true, ok)) {
        if (!Eden::FindGameFolderInput(std::filesystem::path(directory) / name).empty())
            ++count;
    }
    return ok ? count : -1;
}

unsigned int HashPath(const std::string& path) {
    unsigned int hash = 2166136261u;
    for (const unsigned char byte : path) hash = (hash ^ byte) * 16777619u;
    return hash;
}

// A title from the file's name: without its extension and the tags dumps carry
// ("Name [0100...][v0]", "Name (USA)").
std::string CleanTitle(const std::string& filename) {
    const auto selected_path = std::filesystem::path(filename);
    const std::string base = Eden::IsDeconstructedGameSelection(filename) ||
                             Eden::IsNestedGameFileSelection(filename)
                                 ? (*selected_path.begin()).string()
                                 : selected_path.stem().string();
    std::string title = base;
    if (title.rfind("[Game] ", 0) == 0) title.erase(0, 7);
    if (const auto tag = title.find_first_of("[("); tag != std::string::npos && tag > 0) title.erase(tag);
    while (!title.empty() && (title.back() == ' ' || title.back() == '_' || title.back() == '-')) title.pop_back();
    return title.empty() ? base : title;
}

// Covers are keyed by the ROM's file name, not its full path, so they survive a new game
// files folder.
std::string CoverPath(const std::string& filename) {
    char name[16]{};
    std::snprintf(name, sizeof(name), "/%08x.tga", HashPath(filename));
    return Eden::CoversDir() + name;
}

// The game's own name is kept beside its cover once the ROM has been read, so the home screen
// can name its games without opening them.
std::string NamePath(const std::string& filename) {
    char name[16]{};
    std::snprintf(name, sizeof(name), "/%08x.name", HashPath(filename));
    return Eden::CoversDir() + name;
}

std::string SavedTitle(const std::string& filename) {
    char text[513]{};
    if (std::FILE* file = std::fopen(NamePath(filename).c_str(), "rb")) {
        const std::size_t size = std::fread(text, 1, sizeof(text) - 1, file);
        std::fclose(file);
        text[size] = '\0';
    }
    return text;
}

void SaveTitle(const std::string& filename, const std::string& title) {
    if (title.empty() || SavedTitle(filename) == title) return;
    const std::string path = NamePath(filename);
    const std::string staged = path + ".new";
    std::FILE* file = std::fopen(staged.c_str(), "wb");
    if (!file) return;
    const bool written = std::fwrite(title.data(), 1, title.size(), file) == title.size();
    if (std::fclose(file) != 0 || !written || std::rename(staged.c_str(), path.c_str()) != 0)
        (void)std::remove(staged.c_str());
}

std::string GameTitle(const std::string& filename) {
    const std::string saved = SavedTitle(filename);
    return saved.empty() ? CleanTitle(filename) : saved;
}

// The cached cover of a ROM, extracted from it when missing; empty when it has none.
std::string EnsureCover(const std::string& filename, std::string* title = nullptr) {
    const std::string cover = CoverPath(filename);
    if (Eden::FileExists(cover) && !title) return cover;
    const std::string rom = Eden::AssetsPath("roms/" + filename);
    if (!Eden::FileExists(rom)) return {};
    (void)mkdir(Eden::CoversDir().c_str(), 0777);
    char extracted[513]{};
    const int metadata = eden_extract_game_metadata(rom.c_str(), Eden::AssetsPath("keys").c_str(), cover.c_str(),
                                                    extracted, sizeof(extracted));
    if (metadata & EDEN_METADATA_TITLE) {
        SaveTitle(filename, extracted);
        if (title) *title = extracted;
    }
    if (metadata & EDEN_METADATA_COVER) return cover;
    Eden::Report("cover", ("No cover extracted from " + filename).c_str());
    return Eden::FileExists(cover) ? cover : std::string{};
}

int CountInstalledGames() {
    std::error_code error;
    const auto entries = Eden::ReadNativeDirectory(Eden::AssetsPath("roms"), error);
    if (error) return 0;
    int count = 0;
    for (const auto& entry : entries) {
        const std::string filename = entry.path().filename().string();
        const auto discovered = Eden::FindGameFolderInput(entry.path());
        const std::string selection = discovered.empty() ? filename : filename + "/" + discovered;
        if (Eden::ValidRomFilename(selection) &&
            IsFile(Eden::AssetsPath("roms/" + selection))) ++count;
    }
    return count;
}

// The labels of a setting, in the player's language (tools/launcher/strings.py lists them).
template <std::size_t N>
std::vector<std::string> Labels(const char* const (&values)[N]) {
    std::vector<std::string> labels;
    for (const char* value : values) labels.emplace_back(tr(value));
    return labels;
}

// What is missing from the setup, as metadata_bridge.cpp words it, in the player's language. Each
// message is one of these texts, with a folder or a code where it says {0}.
std::string SetupMessage(const std::string& english) {
    static constexpr const char* kMessages[] = {
        TR("Missing or empty keys/prod.keys in {0}."),
        TR("prod.keys could not supply an NCA header key. Replace it with a valid key dump."),
        TR("Cannot read firmware/ in {0}. Install extracted firmware NCAs."),
        TR("A firmware NCA cannot be read. Reinstall the firmware dump."),
        TR("Firmware NCA validation failed (code {0}). Check that firmware and prod.keys are compatible."),
        TR("No firmware NCAs found in {0}."),
        TR("Firmware SystemVersion data is missing or unreadable. Install a complete firmware dump."),
        TR("Setup validation failed. Check that firmware and key files are readable and valid."),
    };
    for (const std::string_view pattern : kMessages) {
        const std::size_t hole = pattern.find("{0}");
        if (hole == std::string_view::npos) {
            if (english == pattern) return tr(english);
            continue;
        }
        const std::string_view before = pattern.substr(0, hole);
        const std::string_view after = pattern.substr(hole + 3);
        if (english.size() >= before.size() + after.size() && english.starts_with(before) &&
            english.ends_with(after))
            return fill(tr(std::string(pattern)),
                        {std::string_view{english}.substr(before.size(),
                                                           english.size() - before.size() - after.size())});
    }
    return english;
}

void RefreshEncoreOverridesManifest() {
    try {
        constexpr std::string_view kHost = "https://raw.githubusercontent.com";
        constexpr std::string_view kPath = "/niakw/encore-overrides/main/runtime-manifest.json";
        const auto response = Common::Net::MakeRequest(std::string{kHost}, std::string{kPath});
        if (!response) {
            Eden::Report("overrides", "Remote runtime manifest unavailable; using embedded snapshot");
            return;
        }
        Eden::EncoreOverridesRuntime::State checked;
        if (!Eden::EncoreOverridesRuntime::ParseManifestText(*response, &checked)) {
            Eden::Report("overrides", "Remote runtime manifest rejected; using embedded snapshot");
            return;
        }
        if (!AtomicWriteText(Eden::EncoreOverridesRuntime::ManifestPath(), *response)) {
            Eden::Report("overrides", "Could not cache remote runtime manifest");
            return;
        }
        Eden::Report("overrides",
                     ("Runtime manifest cached: revision " +
                      std::to_string(checked.database_revision) + ", " +
                      std::to_string(checked.titles.size()) + " specific title(s)").c_str());
    } catch (const std::exception& error) {
        Eden::Report("overrides", (std::string{"Remote runtime manifest failed: "} + error.what()).c_str());
    }
}

void StartEncoreOverridesRefresh() {
    static std::once_flag once;
    std::call_once(once, [] {
        // Never block launcher startup on GitHub. The validated cache becomes authoritative on the
        // next process start (or before first profile lookup if the fetch finishes early enough).
        std::thread(RefreshEncoreOverridesManifest).detach();
    });
}

} // namespace

EdenServices::EdenServices(std::string launch_error)
    : launch_error_(std::move(launch_error)),
      resolution_labels_(Labels(Eden::kResolutionLabels)),
      resolution_keys_(Labels(Eden::kResolutionKeys)),
      filter_labels_(Labels(Eden::kUpscalingFilterLabels)),
      anti_aliasing_labels_(Labels(Eden::kAntiAliasingLabels)),
      performance_profile_labels_(Labels(Eden::kPerformanceProfileLabels)),
      language_labels_(Labels(Eden::kLanguageLabels)) {
    (void)mkdir(Eden::ConfigDir().c_str(), 0777);
    // The repository currently publishes no runtime-manifest.json; a silent
    // HTTPS request on every boot can only fail and is not required when all
    // authored game profiles are compiled from our pinned vendored catalogue.
    // Keep explicit diagnostic/dev opt-in for future validated remote manifests.
    const char* remote_overrides = std::getenv("EDEN_OVERRIDES_REMOTE_REFRESH");
    if (remote_overrides != nullptr && std::strcmp(remote_overrides, "1") == 0)
        StartEncoreOverridesRefresh();
    setup_ = eden_startup_error();
    Eden::Report("setup", setup_.empty() ? "Keys and firmware startup checks passed" : setup_.c_str());
}

pe::ui::Home EdenServices::home() {
    return home(nullptr);
}

pe::ui::Home EdenServices::home(const std::atomic<bool>* cancel) {
    const auto cancelled = [cancel] {
        return cancel && cancel->load(std::memory_order_acquire);
    };
    if (cancelled()) return {};
    const std::lock_guard lock(bridge_);
    if (cancelled()) return {};
    pe::ui::Home home;
    home.setup_ready = setup_.empty();
    if (!home.setup_ready) {
        home.status = fill(tr("Setup required: {0} Open Settings, Storage to choose the root that holds the standard "
                              "keys, firmware and roms folders (or add the files to {1}), then reopen Encore."),
                           {SetupMessage(setup_), Eden::AssetsDir()});
    } else if (launch_error_.starts_with(Eden::Crash::kNotice)) {
        // The previous run ended with a crash report (headless/crash_report.h).
        home.status = fill(tr("ProsperoEden stopped because of an error. A report was saved to {0}."),
                           {launch_error_.substr(Eden::Crash::kNotice.size())});
        home.launch_failed = true;
    } else if (!launch_error_.empty()) {
        home.status = fill(tr("Game could not start: {0} Details: {1}"),
                           {LaunchError(launch_error_), Eden::LogFile("stderr.log")});
        home.launch_failed = true;
    }

    home.last_file = Eden::LoadLastGame();
    // If the last game was removed, fall back to the most recent one that still exists.
    if (!home.last_file.empty() && !IsFile(Eden::AssetsPath("roms/" + home.last_file))) {
        home.last_file.clear();
        for (const auto& name : Eden::LoadRecentGames()) {
            if (Eden::ValidRomFilename(name) && IsFile(Eden::AssetsPath("roms/" + name))) {
                home.last_file = name;
                break;
            }
        }
    }
    if (cancelled()) return {};
    const std::string last_path = Eden::AssetsPath("roms/" + home.last_file);
    home.last_exists = !home.last_file.empty() && IsFile(last_path);
    if (!home.last_file.empty()) {
        std::string title = GameTitle(home.last_file);
        std::string cover = CoverPath(home.last_file);
        bool has_cover = Eden::FileExists(cover);
        if (home.last_exists && home.setup_ready && !has_cover) {
            cover = EnsureCover(home.last_file, &title);
            has_cover = !cover.empty();
        }
        home.last_title = title;
        home.last_caption = home.last_exists ? tr("Last game opened") :
                                               tr("ROM missing from the storage root");
        home.last_caption_warning = !home.last_exists;
        if (has_cover) home.last_cover = cover;
    }
    // The last game's update and DLC and the language it will use; when it does not offer the
    // chosen one, the caption says so. The same metadata is reused by Recent cards so selecting
    // one can become the Home hero without opening the full library first.
    if (cancelled()) return {};
    const int selected_language = Eden::LoadPreferences().language;
    if (home.setup_ready)
        eden_scan_addons(Eden::AssetsPath("updates").c_str(), Eden::AssetsPath("keys").c_str(),
                         Eden::AssetsPath("roms").c_str());
    if (cancelled()) return {};
    if (home.setup_ready && home.last_exists) {
        const uint64_t title_id = ResolveTitleId(last_path, home.last_file);
        const GameLanguage language = LanguageFor(last_path, title_id, selected_language);
        home.last_title_id = title_id;
        const NlibEnrichment nlib = CachedNlibEnrichment(title_id, selected_language);
        if (!nlib.icon.empty()) home.last_cover = nlib.icon;
        home.last_hero = nlib.hero;
        home.last_screenshot = nlib.screenshots.empty() ? std::string{} : nlib.screenshots.front();
        home.last_max_players = nlib.max_players;
        home.last_intro = nlib.intro;
        home.last_description = nlib.description;
        if (!nlib.name.empty()) home.last_title = nlib.name;
        home.last_addons = AddOnSummary(title_id);
        home.last_language = language.label;
        if (!language.note.empty()) {
            home.last_caption = language.note;
            home.last_caption_warning = true;
        }
    }

    auto history = Eden::LoadRecentGames();
    if (history.empty() && home.last_exists) {
        if (!Eden::SaveRecentGame(home.last_file))
            Eden::Report("history", "Could not seed recent games from last played game");
        history.push_back(home.last_file);
    }
    // Home is not only launch history. Fill unused software tiles from the
    // installed ROM catalog, without writing synthetic play history. Preserve
    // real MRU ordering first; alphabetical installed entries are the stable
    // fallback on a brand-new installation. Only shallow folder discovery is
    // needed here (never an ExeFS full-size walk or a network request).
    const std::unordered_set<std::string> played(history.begin(), history.end());
    std::unordered_set<std::string> known = played;
    std::vector<std::string> unplayed_installed;
    std::error_code installed_error;
    const auto installed_entries = Eden::ReadNativeDirectory(
        Eden::AssetsPath("roms"), installed_error);
    int installed = 0;
    if (!installed_error) {
        for (const auto& entry : installed_entries) {
            if (cancelled()) return {};
            const std::string filename = entry.path().filename().string();
            const std::string nested = Eden::FindGameFolderInput(entry.path());
            const std::string name = nested.empty() ? filename : filename + "/" + nested;
            if (!Eden::ValidRomFilename(name) ||
                !IsFile(Eden::AssetsPath("roms/" + name))) continue;
            ++installed;
            if (known.insert(name).second)
                unplayed_installed.push_back(name);
        }
        std::sort(unplayed_installed.begin(), unplayed_installed.end());
        history.insert(history.end(), unplayed_installed.begin(),
                       unplayed_installed.end());
    } else {
        // Do not claim a vanished library when the native mount is temporarily
        // unavailable. Existing verified play history remains usable.
        Eden::Report("history", "Installed Home tile scan unavailable; retaining play history");
        installed = CountInstalledGames();
    }
    std::unordered_set<std::string> admitted;
    for (const auto& name : history) {
        if (cancelled()) return {};
        if (!Eden::ValidRomFilename(name) || !admitted.insert(name).second)
            continue;
        const std::string recent_path = Eden::AssetsPath("roms/" + name);
        if (!IsFile(recent_path)) continue;
        pe::ui::Recent recent;
        recent.file = name;
        recent.title = GameTitle(name);
        // A fallback tile must not extract an entire game's metadata before
        // Home can appear. The background Library scan fills missing art.
        if (played.contains(name))
            recent.cover = EnsureCover(name);
        else {
            const std::string cached_cover = CoverPath(name);
            if (IsFile(cached_cover)) recent.cover = cached_cover;
        }
        if (home.setup_ready) {
            recent.title_id = ResolveTitleId(recent_path, name);
            if (recent.title_id != 0) {
                const NlibEnrichment nlib = CachedNlibEnrichment(recent.title_id, selected_language);
                if (!nlib.icon.empty()) recent.cover = nlib.icon;
                recent.hero = nlib.hero;
                recent.screenshot = nlib.screenshots.empty() ? std::string{} : nlib.screenshots.front();
                recent.max_players = nlib.max_players;
                recent.intro = nlib.intro;
                recent.description = nlib.description;
                if (!nlib.name.empty()) recent.title = nlib.name;
                recent.addons = AddOnSummary(recent.title_id);
                recent.language = LanguageFor(recent_path, recent.title_id, selected_language).label;
            }
        }
        home.recents.push_back(std::move(recent));
        if (home.recents.size() == 7) break;
    }
    if (cancelled()) return {};
    home.system_status = fill(installed == 1 ? tr("{0} game installed") : tr("{0} games installed"),
                              {std::to_string(installed)}) +
        "  /  " + (home.setup_ready ? tr("Firmware ready") : tr("Setup required"));
    return home;
}

std::string EdenServices::clock() {
    const std::time_t now = std::time(nullptr);
    char label[32]{};
    if (const std::tm* local = std::localtime(&now))
        (void)std::strftime(label, sizeof(label), "%H:%M", local);
    return label;
}

std::string EdenServices::profile_avatar() {
#ifdef PS5_NATIVE
    // Do not scan another account's cache if the active-user lookup fails.
    // Query is deliberately issued on the launcher's background worker.
    // The controller can already have initialized UserService; calling
    // Initialize again must not cause it to be terminated underneath Pad.
    static std::once_flag user_service_once;
    std::call_once(user_service_once, [] {
        (void)sceUserServiceInitialize(nullptr);
    });
    std::int32_t user_id = -1;
    const int foreground_status = sceUserServiceGetForegroundUser(&user_id);
    // Zero is a possible foreground user ID: NiakPS5's broker accepts
    // >= 0. Rejecting zero here silently hid that user's own real avatar.
    if (foreground_status != 0 || user_id < 0) {
        static std::atomic_flag reported = ATOMIC_FLAG_INIT;
        if (!reported.test_and_set())
            std::fprintf(stderr,
                         "EDEN_PROFILE_AVATAR status=foreground_unavailable rc=%d\n",
                         foreground_status);
        return {};
    }

// Only consume NiakPS5's optional, local, explicitly owner-bound stage.
// A title is not entitled to read another account's portrait. This remains
// optional: Encore still reads its own foreground PS5 user cache directly.
    constexpr const char* staged_root="/data/NiakPS5/assets/";
    constexpr const char* staged_marker="/data/NiakPS5/assets/niak-profile-source.txt";
    if (pe::ps5::avatar_owner_marker_matches(staged_marker,
            static_cast<std::uint32_t>(user_id), "png") &&
        IsDecodableAvatarFile(std::string(staged_root)+"niak-profile.png")) {
        std::fprintf(stderr,"EDEN_PROFILE_AVATAR format=staged_png status=found\n");
        return std::string(staged_root)+"niak-profile.png";
    }
    if (pe::ps5::avatar_owner_marker_matches(staged_marker,
            static_cast<std::uint32_t>(user_id), "dds") &&
        IsDecodableAvatarFile(std::string(staged_root)+"niak-profile.dds")) {
        std::fprintf(stderr,"EDEN_PROFILE_AVATAR format=staged_dds status=found\n");
        return std::string(staged_root)+"niak-profile.dds";
    }

    // Account-scoped native cache remains the independent fallback.
    // Keep the lookup bound to the active user, never enumerate all users.
    // Some console caches contain only pre-scaled DDS avatars (no PNG).
    // Prefer the full-colour PNG, then a 128px DDS suitable for the 54px UI.
    // Directory prefixes vary between local cache revisions.
    for (const char* digits : {"%08x", "%08X"}) {
        char id[16]{};
        if (std::snprintf(id, sizeof(id), digits,
                          static_cast<unsigned>(user_id)) != 8)
            continue;
        for (const char* prefix : {"0x", "0X", ""}) {
            const std::string root =
                std::string("/system_data/priv/cache/profile/") + prefix + id + "/";
            if (IsDecodableAvatarFile(root + "avatar.png")) {
                std::fprintf(stderr, "EDEN_PROFILE_AVATAR format=png status=found\n");
                return root + "avatar.png";
            }
            for (const char* name : {"avatar128.dds", "avatar260.dds",
                                     "avatar64.dds", "avatar440.dds"}) {
                if (IsDecodableAvatarFile(root + name)) {
                    std::fprintf(stderr, "EDEN_PROFILE_AVATAR format=dds status=found\n");
                    return root + name;
                }
            }
        }
    }
    // Make the next console log actionable without exposing user identity or
    // ever searching another account's private profile cache.
    static std::atomic_flag reported_missing = ATOMIC_FLAG_INIT;
    if (!reported_missing.test_and_set()) {
        const bool marker = IsFile(staged_marker);
        const bool png = IsFile(std::string(staged_root) + "niak-profile.png");
        const bool dds = IsFile(std::string(staged_root) + "niak-profile.dds");
        std::fprintf(stderr,
                     "EDEN_PROFILE_AVATAR status=missing_for_active_user staged_marker=%d staged_png=%d staged_dds=%d\n",
                     marker, png, dds);
    }
#endif
    return {};
}

unsigned EdenServices::controllers() { return radio_input_controllers(); }

std::string EdenServices::version() {
    return Eden::kBuildVersion;
}

std::vector<pe::ui::Game> EdenServices::games() {
    return games(nullptr);
}

std::vector<pe::ui::Game> EdenServices::games(const std::atomic<bool>* cancel) {
    // The launcher reads the list beside its menu (pe/ui/library.cpp), so the metadata reader
    // is used by one thread at a time. Cancellation is sampled between titles,
    // not in the middle of metadata extraction or an in-flight file operation.
    if (cancel && cancel->load(std::memory_order_acquire)) return {};
    std::unique_lock lock(bridge_);
    std::vector<pe::ui::Game> games;
    (void)mkdir(Eden::ConfigDir().c_str(), 0777);
    (void)mkdir(Eden::CoversDir().c_str(), 0777);
    std::error_code directory_error;
    const auto entries = Eden::ReadNativeDirectory(Eden::AssetsPath("roms"), directory_error);
    if (directory_error) {
        Eden::Report("library", ("EDEN_ROM_SCAN directory_error=" +
                                 directory_error.message()).c_str());
        // Do not publish a spurious empty library on a transient PS5 mount/
        // getdents failure. Launcher::finish_scan catches the exception and
        // preserves the previous complete snapshot.
        throw std::system_error(directory_error, "ROM directory scan failed");
    }
    if (cancel && cancel->load(std::memory_order_acquire)) return games;
    eden_scan_addons(Eden::AssetsPath("updates").c_str(), Eden::AssetsPath("keys").c_str(),
                         Eden::AssetsPath("roms").c_str());
    if (cancel && cancel->load(std::memory_order_acquire)) return {};
    const int language_choice = Eden::LoadPreferences().language;
    // A failed stat or unexpected file type previously hid a title with no
    // diagnostic. Keep the UI thread free of IO: report only on this worker.
    std::size_t rom_candidates = 0;
    std::size_t stat_failures = 0;
    std::size_t non_regular = 0;
    // Enumerate local assets immediately. Enrichment is independently queued for
    // all installed titles by Launcher, so even games never selected acquire Nlib
    // banners/icons/screenshots. Disk scanning itself must stay network-free.
    for (const auto& entry : entries) {
        if (cancel && cancel->load(std::memory_order_acquire))
            return {}; // discard partial results and stop per-title disk work
        const std::string entry_name = entry.path().filename().string();
        const std::string extracted = Eden::FindDeconstructedGameMain(entry.path());
        const std::string nested_package = extracted.empty() ?
            Eden::FindNestedGamePackage(entry.path()) : std::string{};
        const bool deconstructed = !extracted.empty();
        // Persist a validated relative base input as one library entry,
        // without listing the update and DLC subtrees as independent games.
        const std::string discovered = deconstructed ? extracted : nested_package;
        const std::string file = discovered.empty() ? entry_name : entry_name + "/" + discovered;
        if (!Eden::ValidRomFilename(file)) continue;
        const std::size_t dot = file.find_last_of('.');
        std::string format = deconstructed ? "EXEFS" :
            (dot == std::string::npos ? std::string{} : file.substr(dot + 1));
        std::transform(format.begin(), format.end(), format.begin(),
                       [](unsigned char c) { return static_cast<char>(std::toupper(c)); });
        ++rom_candidates;
        const std::string path = Eden::AssetsPath("roms/" + file);
        struct stat info {};
        if (stat(path.c_str(), &info) != 0) {
            // ENOENT/ENOTDIR prove only this title was removed. EIO,
            // EACCES, ENODEV and other unexpected errors are UNKNOWN,
            // not missing: publishing a partial scan would evict usable
            // ROMs and their enriched box art from the current snapshot.
            const int stat_error = errno;
            ++stat_failures;
            if (stat_failures <= 3)
                Eden::Report("library", ("EDEN_ROM_SCAN stat_failed=" + file +
                                         " errno=" + std::to_string(stat_error)).c_str());
            if (stat_error != ENOENT && stat_error != ENOTDIR)
                throw std::system_error{stat_error, std::generic_category(),
                                        "ROM stat failed; keep the last-good library"};
            continue;
        }
        if (!S_ISREG(info.st_mode)) {
            ++non_regular;
            continue;
        }
        char size[32]{};
        const auto complete_base_size = deconstructed ?
            ExtractedBaseBytes(entry.path(), cancel) :
            std::optional<std::uint64_t>{static_cast<std::uint64_t>(info.st_size)};
        if (cancel && cancel->load(std::memory_order_acquire)) return {};
        if (deconstructed) {
            // Distinguish an incomplete/unreadable extracted directory from
            // an actual zero-byte game. Never mislabel a 32 MiB main NSO as
            // the total multi-GiB title size.
            std::fprintf(stderr,
                "EDEN_EXEFS_SIZE folder=%s status=%s bytes=%llu\n",
                entry_name.c_str(), complete_base_size ? "measured" : "unknown",
                static_cast<unsigned long long>(complete_base_size.value_or(0)));
        }
        if (complete_base_size) {
            const double bytes = static_cast<double>(*complete_base_size);
            if (bytes >= 1073741824.0)
                std::snprintf(size, sizeof(size), "%.1f GB", bytes / 1073741824.0);
            else
                std::snprintf(size, sizeof(size), "%.1f MB", bytes / 1048576.0);
        }
        pe::ui::Game game;
        game.name = CleanTitle(entry_name);
        game.format = format;
        // Unknown size is more truthful than the 32 MB 'main' executable.
        game.size = complete_base_size ? std::string{size} : std::string{"—"};
        game.file = file;
        // A game whose data cannot be read is still listed, by its file name.
        try {
            char title[513]{};
            // The cover is replaced in one step: the menu may be loading the old one right now.
            const std::string cover = CoverPath(file);
            const std::string staged = cover + ".new";
            const int metadata = eden_extract_game_metadata(path.c_str(), Eden::AssetsPath("keys").c_str(),
                                                            staged.c_str(), title, sizeof(title));
            if (metadata & EDEN_METADATA_TITLE) {
                game.name = title;
                SaveTitle(file, game.name);
            }
            if ((metadata & EDEN_METADATA_COVER) && std::rename(staged.c_str(), cover.c_str()) == 0)
                game.cover = cover;
            else {
                (void)std::remove(staged.c_str());
                if (IsFile(cover)) game.cover = cover; // previous successful extraction
                else if (deconstructed) game.cover = ExtractedLocalCover(entry.path());
            }
            if (cancel && cancel->load(std::memory_order_acquire))
                return {}; // extraction finished; skip ID/Nlib/add-on metadata
            game.title_id = ResolveTitleId(path, file);
            const auto local_control = deconstructed ? ExtractedLocalNacp(entry.path(), language_choice)
                                                      : ExtractedSidecarMetadata{};
            if (const auto* known = Eden::Ns2Catalog::Find(game.title_id)) {
                if (local_control.name.empty()) game.name = std::string(known->name);
                SaveTitle(file, game.name);
                if (!known->publisher.empty()) game.publisher = std::string(known->publisher);
                if (!known->release_date.empty()) game.release_date = std::string(known->release_date);
                if (!known->genre.empty()) game.categories = std::string(known->genre);
                // Nlib's NX endpoint has no metadata for some retail NS2
                // titles. Retain verified local text instead of a blank back.
                const std::string_view locale = Eden::kLanguageKeys[std::clamp(
                    language_choice, 0, static_cast<int>(std::size(Eden::kLanguageKeys)) - 1)];
                const auto overview = Eden::Ns2Catalog::Description(
                    game.title_id, locale.starts_with("fr"));
                if (!overview.empty()) {
                    game.description = std::string(overview);
                    game.intro = game.description;
                }
                std::fprintf(stderr, "EDEN_NS2_TITLE_RESOLVED id=%016llX name=%s source=%s\n",
                             static_cast<unsigned long long>(game.title_id), game.name.c_str(),
                             local_control.name.empty() ? "offline" : "local-nacp");
            }
            if (!local_control.name.empty()) {
                game.name = local_control.name;
                if (!local_control.developer.empty()) game.developer = local_control.developer;
                SaveTitle(file, game.name);
                std::fprintf(stderr, "EDEN_EXEFS_NACP title=%016llX local_name=1 developer=%d\n",
                             static_cast<unsigned long long>(game.title_id),
                             !local_control.developer.empty());
            }
            if (game.title_id != 0) {
                const NlibEnrichment nlib = CachedNlibEnrichment(game.title_id, language_choice);
                if (!nlib.icon.empty()) game.cover = nlib.icon;
                game.hero = nlib.hero;
                game.screenshots = nlib.screenshots;
                AppendCaseScenes(game.screenshots, game.title_id);
                game.max_players = nlib.max_players;
                if (!nlib.name.empty()) game.name = nlib.name;
                // Nlib's API primarily indexes NS1 releases; an empty NS2
                // response must NOT erase the localized offline Title-ID
                // description already admitted above.
                if (!nlib.intro.empty()) game.intro = nlib.intro;
                if (!nlib.description.empty()) game.description = nlib.description;
                if (!nlib.publisher.empty()) game.publisher = nlib.publisher;
                game.developer = nlib.developer;
                if (!nlib.release_date.empty()) game.release_date = nlib.release_date;
                if (!nlib.categories.empty()) game.categories = nlib.categories;
                // Render already-cached real paper scans immediately during
                // local enumeration, without waiting for network enrichment.
                const pe::ui::BoxArt cached_case = box_art(game.title_id);
                game.box_front = cached_case.front;
                game.box_back = cached_case.back;
                if (game.cover.empty() && !game.box_front.empty()) game.cover = game.box_front;
            }
            const GameLanguage language = LanguageFor(path, game.title_id, language_choice);
            game.addons = AddOnSummary(game.title_id);
            game.addons_short = AddOnSummary(game.title_id, true);
            game.language = language.label;
            game.language_note = language.note;
        } catch (const std::exception& error) {
            Eden::Report("library", (file + ": " + error.what()).c_str());
        }
        games.push_back(std::move(game));
    }

    // Metadata bridge work is finished. Home and Library start complete Nlib
    // enrichment of every installed title in background, independently of user
    // selection. A library enumeration itself must remain local/cache-only.
    lock.unlock();
    Eden::Report("library", ("EDEN_ROM_SCAN entries=" + std::to_string(entries.size()) +
                             " candidates=" + std::to_string(rom_candidates) +
                             " visible=" + std::to_string(games.size()) +
                             " stat_failures=" + std::to_string(stat_failures) +
                             " non_regular=" + std::to_string(non_regular)).c_str());

    std::sort(games.begin(), games.end(),
              [](const pe::ui::Game& a, const pe::ui::Game& b) { return a.name < b.name; });
    return games;
}

pe::ui::Game EdenServices::enrich_game_media(pe::ui::Game game) {
    return enrich_game_media(std::move(game), nullptr);
}

pe::ui::Game EdenServices::enrich_game_media(pe::ui::Game game,
                                             const std::atomic<bool>* cancel) {
    if (game.title_id == 0 ||
        (cancel && cancel->load(std::memory_order_acquire))) return game;
    const int language_choice = Eden::LoadPreferences().language;
    const std::string scanned_name = game.name;
    // Prioritize the requested ORIGINAL retail scans before any optional
    // metadata/banner/icon requests. Nlib may perform multiple slow calls;
    // previously a complete retail front could remain invisible for minutes.
    // Resolve canonical retail names locally before any Nlib request. NS2
    // extracted folders often omit spaces (e.g. DonkeyKongBananza).
    // NS1 preserves the exact previous name/filename fallback.
    if (const auto* ns2 = Eden::Ns2Catalog::Find(game.title_id)) {
        game.case_artwork_changed = EnsureRetailCase(
            game.title_id, std::string(ns2->name), scanned_name,
            language_choice, cancel);
    } else {
        game.case_artwork_changed = EnsureRetailCase(game.title_id, scanned_name, CleanTitle(game.file),
                         language_choice, cancel);
    }
    if (!(cancel && cancel->load(std::memory_order_acquire))) {
        const auto cached_case = box_art(game.title_id);
        game.box_front = cached_case.front;
        game.box_back = cached_case.back;
    }
    if (cancel && cancel->load(std::memory_order_acquire)) return game;
    NlibEnrichment enrichment = EnsureNlibEnrichment(game.title_id, language_choice, cancel);
    game.artwork_changed = enrichment.artwork_changed;
    if (!enrichment.icon.empty()) game.cover = std::move(enrichment.icon);
    else if (game.cover.empty() && !game.box_front.empty()) game.cover = game.box_front;
    if (!enrichment.hero.empty()) game.hero = std::move(enrichment.hero);
    if (!enrichment.screenshots.empty()) game.screenshots = std::move(enrichment.screenshots);
    if (enrichment.max_players > 0) game.max_players = enrichment.max_players;
    if (!enrichment.name.empty()) game.name = std::move(enrichment.name);
    else if (const auto* known = Eden::Ns2Catalog::Find(game.title_id)) game.name = std::string(known->name);
    if (!enrichment.intro.empty()) game.intro = std::move(enrichment.intro);
    if (!enrichment.description.empty()) game.description = std::move(enrichment.description);
    else if (game.description.empty()) {
        // Preserve a localized, Title-ID-qualified offline description when
        // a refreshed Nlib result has no NS2 record.
        const std::string_view locale = Eden::kLanguageKeys[std::clamp(
            language_choice, 0, static_cast<int>(std::size(Eden::kLanguageKeys)) - 1)];
        game.description = Eden::Ns2Catalog::Description(
            game.title_id, locale.starts_with("fr"));
    }
    if (!enrichment.publisher.empty()) game.publisher = std::move(enrichment.publisher);
    if (!enrichment.developer.empty()) game.developer = std::move(enrichment.developer);
    if (!enrichment.release_date.empty()) game.release_date = std::move(enrichment.release_date);
    if (!enrichment.categories.empty()) game.categories = std::move(enrichment.categories);
    // A newly fetched localized Nlib name may match a catalog title that the
    // ROM header did not. Give it its own lookup, but never perform any HTTP
    // from the launcher draw or game-start path.
    if ((game.box_front.empty() || game.box_back.empty()) &&
        scanned_name != game.name) {
        game.case_artwork_changed |= EnsureRetailCase(game.title_id, game.name, scanned_name,
                         language_choice, cancel);
    }
    if (!(cancel && cancel->load(std::memory_order_acquire))) {
        const auto box = box_art(game.title_id);
        if (!box.front.empty()) game.box_front = box.front;
        if (!box.back.empty()) game.box_back = box.back;
        // A late local/NX2 retail-cover fetch may complete after the first
        // Nlib/cache snapshot. Always expose its real front to the game tile.
        if (game.cover.empty() && !game.box_front.empty()) game.cover = game.box_front;
        AppendCaseScenes(game.screenshots, game.title_id);
        if (game.case_artwork_changed & 0xF8u)
            game.artwork_changed = true; // refresh GPU copies after replacement
    }
    return game;
}

pe::ui::BoxArt EdenServices::box_art(std::uint64_t title_id) {
    pe::ui::BoxArt artwork;
    if (title_id == 0) return artwork;

    // Optional local media only. Remote services need independent credentials /
    // redistribution terms; the native game-start path must never make requests.
    char id[17]{};
    std::snprintf(id, sizeof(id), "%016llX", static_cast<unsigned long long>(title_id));
    const std::string root = Eden::CoversDir() + "/box-";

    const auto find_face = [&](const char* side) -> std::string {
        for (const char* ext : {"png", "jpg", "jpeg", "webp", "tga"}) {
            const std::string path = root + side + "-" + id + "." + ext;
            struct stat info{};
            if (!IsFile(path) || stat(path.c_str(), &info) != 0 ||
                info.st_size <= 0 || info.st_size > (16LL << 20))
                continue;
            int width = 0, height = 0, channels = 0;
            bool valid = false;
            if (std::strcmp(ext, "webp") == 0) {
                valid = ValidNlibWebP(path, &width, &height);
            } else if (std::strcmp(ext, "tga") == 0) {
                // Old NS2 emergency covers were product photos, not flat
                // retail scans. Do not render their white studio canvas
                // as a genuine paper face; the worker can replace the cache
                // with region-ranked GamesDB artwork when it becomes ready.
                if (std::strcmp(side, "front") == 0) {
                    std::ifstream provenance(path + ".source");
                    std::string origin;
                    if (provenance) std::getline(provenance, origin);
                    if (origin.rfind("https://www.powerplanetonline.com", 0) == 0 ||
                        origin.rfind("https://www.euronics.ee", 0) == 0)
                        continue;
                }
                // Generated scans use uncompressed BGRA TGA. Check the whole
                // payload, then use the SAME header convention as load_tga().
                // Format sniffing through stbi_info can reject a usable TGA.
                if (ValidNlibTga(path)) {
                    std::FILE* input = std::fopen(path.c_str(), "rb");
                    if (input) {
                        unsigned char header[18]{};
                        if (std::fread(header, 1, sizeof(header), input) == sizeof(header)) {
                            width = static_cast<int>(header[12]) |
                                    (static_cast<int>(header[13]) << 8);
                            height = static_cast<int>(header[14]) |
                                     (static_cast<int>(header[15]) << 8);
                            valid = true;
                        }
                        std::fclose(input);
                    }
                }
            } else {
                valid = stbi_info(path.c_str(), &width, &height, &channels) != 0;
            }
            // Square CDN jacket photos are not flat retail scans. Manual
            // imports (no generated provenance receipt) remain allowed.
            if (valid && (std::strcmp(side, "front") == 0 ||
                          std::strcmp(side, "back") == 0) &&
                IsFile(path + ".source") &&
                static_cast<std::uint64_t>(height) * 4 <
                    static_cast<std::uint64_t>(width) * 5)
                valid = false;
            if (!valid ||
                width < (std::strcmp(side, "spine") == 0 ? 16 : 128) ||
                height < (std::strcmp(side, "spine") == 0 ? 250 : 128) ||
                width > 4096 || height > 4096 ||
                static_cast<std::uint64_t>(width) * height > 3840u * 2160u) {
                std::fprintf(stderr,
                    "EDEN_CASE_RESOLVE title=%016llX side=%s status=rejected ext=%s bytes=%lld dimensions=%dx%d path=%s\n",
                    static_cast<unsigned long long>(title_id), side, ext,
                    static_cast<long long>(info.st_size), width, height, path.c_str());
                continue;
            }
            std::fprintf(stderr,
                "EDEN_CASE_RESOLVE title=%016llX side=%s status=ready ext=%s bytes=%lld dimensions=%dx%d path=%s\n",
                static_cast<unsigned long long>(title_id), side, ext,
                static_cast<long long>(info.st_size), width, height, path.c_str());
            return path;
        }
        return {};
    };
    artwork.front = find_face("front");
    artwork.back = find_face("back");
    artwork.spine = find_face("spine");
    std::fprintf(stderr,
        "EDEN_CASE_RESULT title=%016llX front=%d back=%d spine=%d\n",
        static_cast<unsigned long long>(title_id),
        !artwork.front.empty(), !artwork.back.empty(), !artwork.spine.empty());
    return artwork;
}

std::string EdenServices::game_path(const std::string& file) { return Eden::AssetsPath("roms/" + file); }

bool EdenServices::game_exists(const std::string& file) {
    if (!Eden::ValidRomFilename(file)) return false;
    // A failed lstat can mean an I/O error on mounted external storage,
    // not a deleted ROM. The background presence scanner must distinguish
    // ENOENT/ENOTDIR from an indeterminate mount/EIO/permission failure,
    // otherwise two transient polls remove a valid FC27/BOTW tile.
    const std::string path = Eden::AssetsPath("roms/" + file);
    struct stat info{};
    if (lstat(path.c_str(), &info) == 0)
        return S_ISREG(info.st_mode);
    if (errno == EPERM || errno == EACCES) {
        if (stat(path.c_str(), &info) == 0)
            return S_ISREG(info.st_mode);
    }
    // Unknown != removed: keep the previous library snapshot, and let
    // subsequent polls or an explicit launch establish real file status.
    return errno != ENOENT && errno != ENOTDIR;
}

bool EdenServices::game_storage_available() {
    std::error_code error;
    return std::filesystem::is_directory(Eden::AssetsPath("roms"), error) && !error;
}

void EdenServices::arm_safe_launch() {
    // Same process: main.cpp consumes and unsets this before applying the game's settings.
    setenv("EDEN_SAFE_LAUNCH", "1", 1);
    Eden::Report("launch", "Safe launch armed for the next game only");
}

namespace {
// Share the exact override precedence between live modal reads and the
// batch catalog snapshot: only the source of the global profile changes.
bool EffectiveDockedMode(std::uint64_t title_id, const Eden::GameSettings& game,
                         int global_profile) {
    if (game.console_mode >= 0) return game.console_mode == 1;
    const int tier = game.performance_profile >= 0 &&
                             game.performance_profile < Eden::EncoreOverrides::kAuthoredProfileCount ?
                         game.performance_profile :
                     global_profile >= 0 &&
                             global_profile < Eden::EncoreOverrides::kAuthoredProfileCount ?
                         global_profile : -1;
    return tier >= 0 ? Eden::EncoreOverridesRuntime::ProfileForTitle(title_id, tier).docked : true;
}
} // namespace

bool EdenServices::docked(std::uint64_t title_id) {
    if (title_id == 0) return true;
    const Eden::GameSettings game = Eden::LoadGameSettings(title_id);
    // Keep the previous no-global-JSON fastpath for explicit per-title mode.
    if (game.console_mode >= 0) return game.console_mode == 1;
    return EffectiveDockedMode(title_id, game, Eden::LoadPreferences().performance_profile);
}

bool EdenServices::docked_for_scan(std::uint64_t title_id,
                                   const pe::ui::Preferences& snapshot) {
    if (title_id == 0) return true;
    const Eden::GameSettings game = Eden::LoadGameSettings(title_id);
    return EffectiveDockedMode(title_id, game, snapshot.performance_profile);
}

bool EdenServices::set_docked(std::uint64_t title_id, bool docked) {
    Eden::GameSettings settings = Eden::LoadGameSettings(title_id);
    settings.console_mode = docked ? 1 : 0;
    return Eden::SaveGameSettings(title_id, settings);
}

pe::ui::GameSettings EdenServices::game_settings(std::uint64_t title_id) {
    const Eden::GameSettings saved = Eden::LoadGameSettings(title_id);
    pe::ui::GameSettings result;
    result.console_mode = saved.console_mode;
    result.renderer = saved.renderer;
    result.output = saved.output;
    result.resolution = saved.resolution;
    result.filter = saved.upscaling_filter;
    result.fsr_sharpness = saved.fsr_sharpness;
    result.anti_aliasing = saved.anti_aliasing;
    result.texture_anisotropy = saved.texture_anisotropy;
    result.refresh = saved.refresh;
    result.frame_generation = saved.frame_generation;
    result.neural_mode = saved.neural_mode;
    result.neural_model = saved.neural_model;
    result.neural_strength = saved.neural_strength;
    result.performance_profile = saved.performance_profile;
    result.controller_layout = saved.controller_layout;
    result.own_mapping = saved.own_mapping;
    result.mapping = saved.mapping;
    return result;
}

bool EdenServices::set_game_settings(std::uint64_t title_id, const pe::ui::GameSettings& settings) {
    Eden::GameSettings value;
    value.console_mode = settings.console_mode;
    value.renderer = settings.renderer;
    value.output = settings.output;
    value.resolution = settings.resolution;
    value.upscaling_filter = settings.filter;
    value.fsr_sharpness = settings.fsr_sharpness;
    value.anti_aliasing = settings.anti_aliasing;
    value.texture_anisotropy = settings.texture_anisotropy;
    value.refresh = settings.refresh;
    value.frame_generation = settings.frame_generation;
    value.neural_mode = settings.neural_mode;
    value.neural_model = settings.neural_model;
    value.neural_strength = settings.neural_strength;
    value.performance_profile = settings.performance_profile;
    value.controller_layout = settings.controller_layout;
    value.own_mapping = settings.own_mapping;
    value.mapping = settings.mapping;
    const bool saved = Eden::SaveGameSettings(title_id, value);
    if (!saved) Eden::Report("settings", "Could not write game settings");
    return saved;
}

pe::ui::Preferences EdenServices::preferences() {
    const Eden::Preferences saved = Eden::LoadPreferences();
    pe::ui::Preferences result;
    result.hud = saved.hud;
    result.volume = saved.volume;
    result.mute = saved.mute;
    result.detailed_logging = saved.detailed_logging;
    result.renderer = saved.backend == Eden::GraphicsBackend::OpenGL ? 0 : 1;
    result.resolution = saved.resolution;
    result.filter = saved.upscaling_filter;
    result.fsr_sharpness = saved.fsr_sharpness;
    result.anti_aliasing = saved.anti_aliasing;
    result.texture_anisotropy = saved.texture_anisotropy;
    result.refresh = saved.refresh;
    result.frame_generation = saved.frame_generation;
    result.neural_mode = saved.neural_mode;
    result.neural_model = saved.neural_model;
    result.neural_strength = saved.neural_strength;
    result.output = saved.output;
    result.performance_profile = saved.performance_profile;
    result.controller_layout = saved.controller_layout;
    result.mapping = saved.mapping;
    result.vibration = saved.vibration;
    result.vibration_strength = saved.vibration_strength;
    result.stick_deadzone = saved.stick_deadzone;
    result.language = saved.language;
    result.menu_volume = saved.menu_volume;
    result.large_text = saved.large_text;
    result.high_contrast = saved.high_contrast;
    result.reduce_motion = saved.reduce_motion;
    result.ui_theme = saved.ui_theme;
    result.color_palette = saved.color_palette;
    result.accent_color = saved.accent_color;
    result.background_style = saved.background_style;
    result.check_updates_on_start = saved.check_updates_on_start;
    result.logo_choice = saved.logo_choice;
    result.glow_enabled = saved.glow_enabled;
    result.glow_strength = saved.glow_strength;
    result.background_color = saved.background_color;
    result.background_color2 = saved.background_color2;
    result.background_overlay = saved.background_overlay;
    result.panel_opacity = saved.panel_opacity;
    result.background_animate = saved.background_animate;
    result.background_fit = saved.background_fit;
    result.show_game_background = saved.show_game_background;
    result.wallpaper_file = saved.wallpaper_file;
    return result;
}

bool EdenServices::set_preferences(const pe::ui::Preferences& preferences) {
    Eden::Preferences value;
    value.hud = preferences.hud;
    value.volume = preferences.volume;
    value.mute = preferences.mute;
    value.detailed_logging = preferences.detailed_logging;
    value.backend = preferences.renderer == 0 ? Eden::GraphicsBackend::OpenGL : Eden::GraphicsBackend::Vulkan;
    value.resolution = preferences.resolution;
    value.upscaling_filter = preferences.filter;
    value.fsr_sharpness = preferences.fsr_sharpness;
    value.anti_aliasing = preferences.anti_aliasing;
    value.texture_anisotropy = preferences.texture_anisotropy;
    value.refresh = preferences.refresh;
    value.frame_generation = preferences.frame_generation;
    value.neural_mode = preferences.neural_mode;
    value.neural_model = preferences.neural_model;
    value.neural_strength = preferences.neural_strength;
    value.output = preferences.output;
    value.performance_profile = preferences.performance_profile;
    value.controller_layout = preferences.controller_layout;
    value.mapping = preferences.mapping;
    value.vibration = preferences.vibration;
    value.vibration_strength = preferences.vibration_strength;
    value.stick_deadzone = preferences.stick_deadzone;
    value.language = preferences.language;
    value.menu_volume = preferences.menu_volume;
    value.large_text = preferences.large_text;
    value.high_contrast = preferences.high_contrast;
    value.reduce_motion = preferences.reduce_motion;
    value.ui_theme = preferences.ui_theme;
    value.color_palette = preferences.color_palette;
    value.accent_color = preferences.accent_color;
    value.background_style = preferences.background_style;
    value.check_updates_on_start = preferences.check_updates_on_start;
    value.logo_choice = preferences.logo_choice;
    value.glow_enabled = preferences.glow_enabled;
    value.glow_strength = preferences.glow_strength;
    value.background_color = preferences.background_color;
    value.background_color2 = preferences.background_color2;
    value.background_overlay = preferences.background_overlay;
    value.panel_opacity = preferences.panel_opacity;
    value.background_animate = preferences.background_animate;
    value.background_fit = preferences.background_fit;
    value.show_game_background = preferences.show_game_background;
    value.wallpaper_file = preferences.wallpaper_file;
    const bool saved = Eden::SavePreferences(value);
    if (!saved) Eden::Report("settings", "Could not write preferences");
#ifdef PS5_NATIVE
    if (saved) {
        // Apply the toggle immediately in the launcher: no hidden running
        // stderr/stdout writers and no growing emulator log when disabled.
        Eden::NativeLogs::SetDetailed(value.detailed_logging);
        // The deep GPU/JIT hot-path counters must follow the live toggle.
        // Otherwise disabling logs leaves costly diagnostics in-game.
        Eden::Performance::detailed_gpu_profile.store(value.detailed_logging,
                                                       std::memory_order_relaxed);
        eden_network_audit_enable(value.detailed_logging ? 1 : 0);
        if (!value.detailed_logging) {
            Eden::BootTrace::Quiet(Eden::LogsDir());
            for (const char* name : {
                    "eden_log.txt", "eden_log.txt.first.txt", "eden_log.txt.old.txt"})
                (void)std::remove((Eden::UserDir() + "/log/" + name).c_str());
        }
    }
#endif
    return saved;
}

namespace {
// Treat all user wallpaper names as opaque BASENAMES under Eden's own data dir.
// Never traverse the PS5 system gallery or accept a symlink to other app data.
bool ValidWallpaperName(const std::string& name) {
    if (name.empty() || name.size() > 120 || name == "." || name == ".." ||
        name.find("..") != std::string::npos ||
        name.find_first_of("/\\") != std::string::npos)
        return false;
    const auto pos = name.find_last_of('.');
    if (pos == std::string::npos) return false;
    std::string ext = name.substr(pos);
    std::transform(ext.begin(), ext.end(), ext.begin(), [](unsigned char c) {
        return static_cast<char>(std::tolower(c)); });
    // Personal imports retain PNG/JPEG/TGA; packaged art uses WebP.
    // The same bounded PS5 decoder accepts an imported WebP too.
    return ext == ".png" || ext == ".jpg" || ext == ".jpeg" ||
           ext == ".tga" || ext == ".webp" || ext == ".jxr";
}
bool IsJxrWallpaper(std::string_view name) {
    if (name.size() < 4) return false;
    name.remove_prefix(name.size() - 4);
    return name[0] == '.' &&
           std::tolower(static_cast<unsigned char>(name[1])) == 'j' &&
           std::tolower(static_cast<unsigned char>(name[2])) == 'x' &&
           std::tolower(static_cast<unsigned char>(name[3])) == 'r';
}
std::string CheckedWallpaper(const std::filesystem::path& folder, const std::string& name) {
    if (!ValidWallpaperName(name)) return {};
    std::error_code ec;
    const auto path = folder / name;
    const auto info = std::filesystem::symlink_status(path, ec);
    if (ec || !std::filesystem::is_regular_file(info)) return {};
    const auto bytes = std::filesystem::file_size(path, ec);
    const bool jpeg_xr = IsJxrWallpaper(name);
    const std::uintmax_t limit = jpeg_xr ? 48u * 1024u * 1024u
                                          : 12u * 1024u * 1024u;
    if (ec || bytes < 32 || bytes > limit) return {};
    return path.string();
}
#if defined(PS5_NATIVE)
// Only a chosen JXR is decoded, never the Media Gallery enumeration.
// Original HDR files stay read-only, WebP conversion is one-at-a-time,
// cached under app-owned data and committed by atomic rename.
std::string SelectedJxrWebp(const std::string& original) {
    namespace fs = std::filesystem;
    if (original.empty() || !IsJxrWallpaper(original))
        return original;
    struct stat source{};
    if (::lstat(original.c_str(), &source) != 0 ||
        !S_ISREG(source.st_mode) || source.st_size < 32 ||
        source.st_size > (48ll << 20))
        return {};
    const fs::path cache = fs::path(Eden::UserDir()) /
                           "wallpapers" / ".jxr-cache";
    std::error_code ec;
    const auto before = fs::symlink_status(cache, ec);
    if (!ec && fs::is_symlink(before)) return {};
    ec.clear();
    fs::create_directories(cache, ec);
    if (ec || !fs::is_directory(cache, ec) || ec) return {};

    // Stable, non-traversable cache key includes file identity/version,
    // but does not disclose an account name or the source's full path.
    const std::string identity = original + ":" +
        std::to_string(static_cast<long long>(source.st_size)) + ":" +
        std::to_string(static_cast<long long>(source.st_mtime)) + ":" +
        std::to_string(static_cast<unsigned long long>(source.st_ino));
    std::uint64_t digest = 14695981039346656037ull;
    for (unsigned char c : identity) {
        digest ^= c;
        digest *= 1099511628211ull;
    }
    char hex[17]{};
    std::snprintf(hex, sizeof(hex), "%016llx",
                  static_cast<unsigned long long>(digest));
    const std::string basename = std::string("selected-") + hex + ".webp";
    const auto target = cache / basename;

    static std::mutex codec_mutex;
    std::scoped_lock lock(codec_mutex);
    if (!CheckedWallpaper(cache, basename).empty())
        return target.string();

    // A partial conversion never becomes a selectable/renderable image.
    const auto staging = cache /
        (std::string("pending-") + hex + "-" +
         std::to_string(static_cast<unsigned long long>(::getpid())) + ".part");
    // Fail closed if a previous unexpected file or symlink occupies staging.
    ec.clear();
    const auto stage_status = fs::symlink_status(staging, ec);
    if ((ec && ec != std::errc::no_such_file_or_directory) ||
        (!ec && stage_status.type() != fs::file_type::not_found))
        return {};
    ec.clear();
    if (!encore_jxr_to_webp(original.c_str(), staging.c_str())) {
        fs::remove(staging, ec);
        std::fprintf(stderr, "EDEN_JXR_SELECT decode=failed\n");
        return {};
    }
    ec.clear();
    const auto bytes = fs::file_size(staging, ec);
    if (ec || bytes < 32 || bytes > 12u * 1024u * 1024u) {
        fs::remove(staging, ec);
        return {};
    }
    ec.clear();
    fs::rename(staging, target, ec);
    if (ec) {
        fs::remove(staging, ec);
        return {};
    }
    std::fprintf(stderr, "EDEN_JXR_SELECT decode=cached bytes=%llu\n",
                 static_cast<unsigned long long>(bytes));
    return CheckedWallpaper(cache, basename);
}

// The foreground user's PS5 Media Gallery mount; independent of Encore's
// personal wallpapers directory. This is read-only and never copies, renames
// or alters PS5 screenshots. The capture service's NPXS40087 photos use
// /user/av_contents/photo/NPXS40087/<title>/<folder>/<image>.
struct SystemWallpaper {
    std::string selection;
    std::filesystem::path photo;
    std::time_t modified = 0;
};

std::string CaptureWallpaperSelection(const std::filesystem::path& photo) {
    // Opaque, stable and non-traversable selection key: persisted settings
    // may contain only a validated basename, NEVER a PS5 system path.
    const std::string source = photo.string();
    std::uint64_t hash = 14695981039346656037ull;
    for (const unsigned char byte : source) {
        hash ^= byte;
        hash *= 1099511628211ull;
    }
    char digest[17]{};
    std::snprintf(digest, sizeof(digest), "%016llx",
                  static_cast<unsigned long long>(hash));
    std::string stem;
    for (const unsigned char byte : photo.stem().string()) {
        if (stem.size() >= 36u) break;
        if (std::isalnum(byte) && byte < 128)
            stem.push_back(static_cast<char>(byte));
        else if (byte == '_' || byte == '-')
            stem.push_back(static_cast<char>(byte));
    }
    if (stem.empty()) stem = "Capture";
    auto extension = photo.extension().string();
    std::transform(extension.begin(), extension.end(), extension.begin(),
                   [](unsigned char c) { return static_cast<char>(std::tolower(c)); });
    return "PS5_" + stem + "_" + digest + extension;
}

std::vector<SystemWallpaper> SystemCaptureWallpapers() {
    namespace fs = std::filesystem;
    std::vector<SystemWallpaper> found;
    // Do not probe any account or gallery until the foreground user is known.
    // /user is the PS5 mount belonging to the console foreground context.
    std::int32_t foreground = -1;
    if (sceUserServiceGetForegroundUser(&foreground) != 0 || foreground < 0)
        return found;
    const fs::path root{"/user/av_contents/photo/NPXS40087"};
    // Try the same native open/getdents path that works for PS5 mounted ROMs.
    // access(2) checks real credentials, which can incorrectly reject a
    // readable mount when the launcher's effective credentials differ.
    struct Pending { fs::path folder; unsigned depth; };
    std::vector<Pending> pending{{root, 0u}};
    std::size_t directories = 0, examined = 0;
    // Only aggregate diagnostics: never log private screenshot names or paths.
    std::size_t unreadable_dirs = 0, hdr_jxr = 0, ignored_size = 0, ignored_format = 0;
    const auto scan_started = std::chrono::steady_clock::now();
    // Thousands of user screenshots are normal; keep safe finite bounds.
    constexpr std::size_t kMaxDirs = 1024, kMaxEntries = 32768;
    constexpr unsigned kMaxDepth = 8;
    while (!pending.empty() && directories < kMaxDirs &&
           examined < kMaxEntries) {
        const auto current = std::move(pending.back());
        pending.pop_back();
        ++directories;
        std::error_code read_error;
        const auto entries = Eden::ReadNativeDirectory(current.folder, read_error);
        if (read_error) {
            ++unreadable_dirs; // inaccessible mount is not an app failure
            continue;
        }
        for (const auto& entry : entries) {
            if (++examined > kMaxEntries) break;
            struct stat native{};
            if (::lstat(entry.path().c_str(), &native) != 0 ||
                S_ISLNK(native.st_mode)) continue;
            if (S_ISDIR(native.st_mode)) {
                if (current.depth < kMaxDepth &&
                    pending.size() + directories < kMaxDirs)
                    pending.push_back({entry.path(), current.depth + 1u});
                continue;
            }
            if (!S_ISREG(native.st_mode)) continue;
            auto ext = entry.path().extension().string();
            std::transform(ext.begin(), ext.end(), ext.begin(),
                [](unsigned char c) { return static_cast<char>(std::tolower(c)); });
            // Scan only directory metadata. JXR is listed alongside the
            // JPG/PNG files, but never decoded or converted by this scan.
            const bool is_jxr = ext == ".jxr";
            if (is_jxr) ++hdr_jxr;
            const auto max_bytes = is_jxr ? (48ll << 20) : (12ll << 20);
            if (native.st_size < 32 || native.st_size > max_bytes) {
                ++ignored_size;
                continue;
            }
            const std::string filename = entry.path().filename().string();
            if (!ValidWallpaperName(filename) ||
                (!is_jxr && ext != ".jpg" && ext != ".jpeg" && ext != ".png")) {
                ++ignored_format;
                continue;
            }
            SystemWallpaper item{
                CaptureWallpaperSelection(entry.path()), entry.path(),
                native.st_mtime};
            if (ValidWallpaperName(item.selection))
                found.push_back(std::move(item));
        }
    }
    std::sort(found.begin(), found.end(), [](const auto& a, const auto& b) {
        return a.modified != b.modified ? a.modified > b.modified :
               a.selection < b.selection;
    });
    // Hash collisions must never silently select a different source file.
    std::unordered_set<std::string> seen;
    found.erase(std::remove_if(found.begin(), found.end(),
        [&](const SystemWallpaper& item) {
            return !seen.insert(item.selection).second;
        }), found.end());
    const auto scan_ms = std::chrono::duration_cast<std::chrono::milliseconds>(
        std::chrono::steady_clock::now() - scan_started).count();
    std::fprintf(stderr,
        "EDEN_WALLPAPER_SCAN dirs=%zu entries=%zu accepted=%zu jxr=%zu "
        "size_rejected=%zu format_rejected=%zu read_errors=%zu capped=%d elapsed_ms=%lld\n",
        directories, examined, found.size(), hdr_jxr, ignored_size,
        ignored_format, unreadable_dirs,
        int(!pending.empty() || examined >= kMaxEntries),
        static_cast<long long>(scan_ms));
    return found;
}
#endif

std::string LocalDay() {
    const auto now = std::time(nullptr);
    const std::tm* local = std::localtime(&now);
    if (!local) return {};
    char date[11]{};
    if (std::strftime(date, sizeof(date), "%Y-%m-%d", local) == 0) return {};
    return date;
}
} // namespace

static pe::ui::AppUpdateInfo QueryAppReleaseMetadata(const std::string& current) {
    using Report = pe::ui::AppUpdateInfo;
    Report report;
    report.installed_version = current;
    // The checked URL is a constant; never derive a download address from
    // release notes, redirects or arbitrary GitHub API JSON.
    const auto response = Common::Net::MakeRequest(
        "https://api.github.com", "/repos/niakw/ProsperoEden-Encore/releases/latest");
    if (!response || response->empty() || response->size() > 512u * 1024u) {
        report.state = Report::State::offline;
        report.summary = "GitHub Releases unavailable. The launcher stays usable offline.";
        return report;
    }
    const auto result = Eden::EncoreUpdate::AssessStableRelease(*response, current);
    report.latest_version = result.latest_version;
    report.notes = result.notes;
    report.package_name = result.package_name;
    report.package_path = result.package_path;
    report.package_sha256 = result.sha256;
    report.package_bytes = result.package_bytes;
    switch (result.status) {
    case Eden::EncoreUpdate::ReleaseAssessment::Status::malformed:
        report.state = Report::State::incompatible;
        report.summary = "No eligible stable release metadata or comparable version.";
        break;
    case Eden::EncoreUpdate::ReleaseAssessment::Status::current:
        report.state = Report::State::up_to_date;
        report.summary = "Already up to date (" + result.latest_version + ").";
        break;
    case Eden::EncoreUpdate::ReleaseAssessment::Status::newer_without_package:
        report.state = Report::State::newer_uninstallable;
        report.summary = "Stable " + result.latest_version +
            " exists, but no compatible PPSA99008 package is published.";
        break;
    case Eden::EncoreUpdate::ReleaseAssessment::Status::newer_package_candidate: {
        // The updater may be advertised only if this app actually carries
        // its separately built helper ELF, never on host/preview builds.
        bool helper_ready = false;
#ifdef PS5_NATIVE
        std::error_code ec;
        const auto status =
            std::filesystem::symlink_status("/app0/self-updater.elf", ec);
        if (!ec && std::filesystem::is_regular_file(status) &&
            !std::filesystem::is_symlink(status)) {
            const auto bytes =
                std::filesystem::file_size("/app0/self-updater.elf", ec);
            helper_ready = !ec && bytes >= 4096 && bytes <= (16u << 20);
        }
#endif
        report.state = helper_ready ? Report::State::available
                                    : Report::State::newer_uninstallable;
        report.summary = helper_ready
            ? "Stable PS5 update is available; installation requires confirmation."
            : "Stable PS5 package exists but its native helper is unavailable.";
        break;
    }
    }
    // Even a valid SHA-256 in a trusted release is only a candidate. An
    // independently audited installer, title-ID check, download verification,
    // restart and recovery proof are required before State::available is used.
    return report;
}

namespace {
struct NativeRoomSession {
    std::mutex mutex;
    bool initialized = false;
    bool hosting = false;

    bool EnsureNetwork() {
        if (initialized) return true;
        // The active emulator may already own Network::Init. Reuse its
        // RoomMember; a second call would replace the guest HLE bridge.
        if (!Network::GetRoomMember().expired()) {
            initialized = true;
            return true;
        }
        initialized = Network::Init();
        return initialized;
    }
};
NativeRoomSession& RoomSession() {
    // Intentionally process-lifetime: a detached network worker may still
    // be running during launcher destruction. Never destroy the Room/ENet
    // objects concurrently from a static global destructor.
    static auto* session = new NativeRoomSession;
    return *session;
}

Eden::Multiplayer::RoomActionResult RoomAction(
    Eden::Multiplayer::RoomAction action, Eden::Multiplayer::PublicRoom room) {
    using Eden::Multiplayer::RoomAction;
    auto& session = RoomSession();
    std::lock_guard lock(session.mutex);
    if (action == RoomAction::Join &&
        !Eden::Multiplayer::CanJoinPublicRoom(room))
        return {false, "Room is incompatible, protected, full or unsafe."};
    if (action != RoomAction::Leave && !session.EnsureNetwork())
        return {false, "Network initialization failed."};
    auto member = Network::GetRoomMember().lock();
    auto host = Network::GetRoom().lock();
    if (!member || !host)
        return {action == RoomAction::Leave, "Network room is unavailable."};
    if (action == RoomAction::Leave) {
        if (member->IsConnected()) member->Leave();
        if (host->GetState() == Network::Room::State::Open) host->Destroy();
        session.hosting = false;
        return {true, "Disconnected from room."};
    }

    // Preflight the native ENet socket: upstream Join asserts on failure
    // to create its own client, which would otherwise crash the console.
    ENetHost* probe = enet_host_create(nullptr, 1, Network::NumChannels, 0, 0);
    if (!probe) return {false, "Network socket unavailable."};
    enet_host_destroy(probe);

    if (member->IsConnected()) member->Leave();
    if (host->GetState() == Network::Room::State::Open) host->Destroy();
    session.hosting = false;
    const bool hosting = action == RoomAction::HostPrivate;
    if (hosting &&
        !host->Create("Eden Encore PS5", "", "", Network::DefaultRoomPort,
                      "", 8))
        return {false, "Could not host private room."};
    session.hosting = hosting;
    const std::string address = hosting ? "127.0.0.1" : room.address;
    const auto port = hosting ? Network::DefaultRoomPort : room.port;
    // Per-session nickname avoids recurring collisions without reading
    // a PSN identity or transmitting any console identifier.
    const auto timestamp = static_cast<unsigned long long>(
        std::chrono::steady_clock::now().time_since_epoch().count());
    const std::string nickname = "Encore-" + std::to_string(timestamp % 100000000ull);
    member->Join(nickname, address.c_str(), port);

    // Join establishes ENet first, then the room-version/password handshake
    // completes on its dedicated event loop. Poll on this worker only.
    for (int i = 0; i < 100; ++i) {
        const auto state = member->GetState();
        if (state == Network::RoomMember::State::Joined ||
            state == Network::RoomMember::State::Moderator)
            return {true, hosting ? "Private LAN room hosted." : "Connected to room."};
        if (state == Network::RoomMember::State::Idle) break;
        std::this_thread::sleep_for(std::chrono::milliseconds(50));
    }
    if (member->IsConnected()) member->Leave();
    if (hosting && host->GetState() == Network::Room::State::Open)
        host->Destroy();
    session.hosting = false;
    return {false, "Room handshake failed or timed out."};
}
} // namespace

std::function<Eden::Multiplayer::RoomActionResult()>
EdenServices::detached_room_action_task(
    Eden::Multiplayer::RoomAction action,
    const Eden::Multiplayer::PublicRoom& room) {
    return [action, room] { return RoomAction(action, room); };
}

bool EdenServices::room_connected() const {
    auto member = Network::GetRoomMember().lock();
    if (!member) return false;
    const auto state = member->GetState();
    return state == Network::RoomMember::State::Joined ||
           state == Network::RoomMember::State::Moderator;
}

bool EdenServices::room_hosting() const {
    auto& session = RoomSession();
    std::lock_guard lock(session.mutex);
    return session.hosting;
}

std::function<Eden::Multiplayer::RoomDirectory()>
EdenServices::detached_room_directory_task()
{
    // No live networking occurs on the UI thread. The parser isolates
    // untrusted directory data; guest traffic is NOT enabled by this feature.
    return []() -> Eden::Multiplayer::RoomDirectory {
        const auto response =
            Common::Net::MakeRequest("https://api.ynet-fun.xyz", "/lobby");
        if (!response)
            return {{}, "Public room service could not be reached."};
        if (response->size() > Eden::Multiplayer::MaxDirectoryBytes)
            return {{}, "Public room response exceeded the safe size limit."};
        // Protocol compatibility is not asserted before the LDN bridge is
        // connected to the pinned emulator network version.
        // The actual linked Room/RoomMember and LDN HLE use this exact
        // network protocol. Zero makes every real room appear incompatible.
        return Eden::Multiplayer::ParseRoomDirectory(
            *response, Network::network_version);
    };
}

bool EdenServices::has_lossless_dll() const {
    return Eden::Graphics::LosslessUserFileLooksValid(Eden::UserDir());
}

bool EdenServices::has_dlssnr_dll() const {
    return Eden::Graphics::DlssNrUserFileLooksValid(
        Eden::UserDir(), Eden::ConfigDir());
}

pe::ui::AppUpdateInfo EdenServices::check_app_update(const std::string& current) {
    return QueryAppReleaseMetadata(current);
}

std::function<pe::ui::AppUpdateInstallResult()>
EdenServices::detached_app_update_install_task(
    const pe::ui::AppUpdateInfo& candidate) {
    // The archived metadata is not sufficient by itself: re-query the same
    // official stable release before downloading anything, rejecting changes.
    return [candidate] {
        const auto current = QueryAppReleaseMetadata(candidate.installed_version);
        if (current.latest_version.empty() ||
            current.latest_version != candidate.latest_version ||
            current.package_name.empty() ||
            current.package_name != candidate.package_name ||
            current.package_path != candidate.package_path ||
            current.package_bytes != candidate.package_bytes ||
            current.package_sha256 != candidate.package_sha256)
            return pe::ui::AppUpdateInstallResult{
                false, "Release metadata changed. Run a new update check."};
        const auto result = Eden::EncoreUpdate::InstallNativeApp({
            candidate.installed_version, candidate.latest_version,
            candidate.package_name, candidate.package_path,
            candidate.package_sha256, candidate.package_bytes
        });
        return pe::ui::AppUpdateInstallResult{result.applying,result.message};
    };
}

std::function<pe::ui::AppUpdateInfo()> EdenServices::detached_app_update_task(
    const std::string& current) {
    // Never capture this: HTTP may still be in progress when the app launches
    // a game and destroys the launcher/frontend Services instance.
    return [installed = current] { return QueryAppReleaseMetadata(installed); };
}

std::vector<std::string> EdenServices::wallpapers() {
    std::vector<std::string> names;
    const auto folder = std::filesystem::path(Eden::UserDir()) / "wallpapers";
    std::error_code ec;
    for (std::filesystem::directory_iterator it(folder,
              std::filesystem::directory_options::skip_permission_denied, ec), end;
         !ec && it != end && names.size() < 64; it.increment(ec)) {
        const std::string name = it->path().filename().string();
        if (!CheckedWallpaper(folder, name).empty()) names.push_back(name);
    }
    // User imports are always the first, alphabetized group in this chooser.
    // Do not globally sort opaque PS5 capture keys ahead of personal files.
    std::sort(names.begin(), names.end());
#if defined(PS5_NATIVE)
    // Merge the current PS5 user's Media Gallery with app-local files; no
    // user-import step and no blocking scan on the drawing/input thread.
    const std::size_t imported = names.size();
    // System captures are already ordered newest first by the scanner.
    const auto captures = SystemCaptureWallpapers();
    for (const auto& capture : captures)
        names.push_back(capture.selection);
    std::fprintf(stderr, "EDEN_WALLPAPER_SOURCES app=%zu ps5=%zu shown=%zu\n",
                 imported, captures.size(), names.size());
#endif
    return names;
}
std::string EdenServices::wallpaper_path(const std::string& file) {
    const auto local = CheckedWallpaper(
        std::filesystem::path(Eden::UserDir()) / "wallpapers", file);
    if (!local.empty()) {
#if defined(PS5_NATIVE)
        return SelectedJxrWebp(local);
#else
        return local;
#endif
    }
#if defined(PS5_NATIVE)
    // A persisted selection is only a validated opaque filename. Resolve it
    // again against the foreground user's read-only, bounded Media Gallery.
    // Decode *only that chosen JXR*, not every item while listing or browsing.
    if (file.starts_with("PS5_") && ValidWallpaperName(file)) {
        for (const auto& capture : SystemCaptureWallpapers()) {
            if (capture.selection == file) {
                const auto checked = CheckedWallpaper(capture.photo.parent_path(),
                                                     capture.photo.filename().string());
                return checked.empty() ? std::string{} : SelectedJxrWebp(checked);
            }
        }
    }
#endif
    return {};
}

namespace {
struct DailyOnlineCandidate {
    std::string title;
    std::string platform;
    std::string released;
    std::string host;
    std::string endpoint;
    std::time_t timestamp = 0;
};

std::optional<std::string> DailyRequest(const std::string& host,
                                        const std::string& path,
                                        std::size_t max_bytes) {
    // Every host is fixed by the caller; all remote paths stay bounded.
    if (path.empty() || path[0] != '/' || path.size() > 2048 ||
        path.find_first_of("\r\n\t\\") != std::string::npos) return {};
    const auto response = Common::Net::MakeRequest(host, path);
    if (!response || response->empty() || response->size() > max_bytes)
        return {};
    return *response;
}

std::optional<std::time_t> DailyReleaseTime(const std::string& day,
                                             bool display_name) {
    int year = 0, month = 0, date = 0;
    if (display_name) {
        char mon[4]{};
        char tail[2]{};
        if (std::sscanf(day.c_str(), "%3s %d, %d%1s",
                        mon, &date, &year, tail) != 3) return {};
        static constexpr std::array<const char*, 12> months = {
            "Jan","Feb","Mar","Apr","May","Jun",
            "Jul","Aug","Sep","Oct","Nov","Dec"};
        for (int i = 0; i < 12; ++i)
            if (std::strcmp(mon, months[i]) == 0) month = i + 1;
    } else {
        if (day.size() != 10 || day[4] != '-' || day[7] != '-' ||
            !std::all_of(day.begin(), day.end(), [](unsigned char ch) {
                return (ch >= '0' && ch <= '9') || ch == '-';
            })) return {};
        year = std::atoi(day.substr(0, 4).c_str());
        month = std::atoi(day.substr(5, 2).c_str());
        date = std::atoi(day.substr(8, 2).c_str());
    }
    if (year < 2020 || year > 2100 || month < 1 || month > 12 ||
        date < 1 || date > 31) return {};
    std::tm tm{};
    tm.tm_year = year - 1900;
    tm.tm_mon = month - 1;
    tm.tm_mday = date;
    tm.tm_hour = 12;
    tm.tm_isdst = -1;
    const std::time_t result = std::mktime(&tm);
    if (result == static_cast<std::time_t>(-1) ||
        tm.tm_year != year - 1900 || tm.tm_mon != month - 1 ||
        tm.tm_mday != date) return {};
    const auto now = std::time(nullptr);
    if (result > now + 12 * 3600 ||
        now - result > static_cast<std::time_t>(180 * 86400)) return {};
    return result;
}

std::string DailyDate(std::time_t timestamp) {
    const std::tm* date = std::localtime(&timestamp);
    if (!date) return {};
    char output[11]{};
    if (!std::strftime(output, sizeof(output), "%Y-%m-%d", date)) return {};
    return output;
}

bool DailyApprovedArt(const std::string& url,
                      std::string& host, std::string& endpoint) {
    static constexpr std::array<const char*, 3> origins = {
        "https://api.nlib.cc",
        "https://www.nintendo.com",
        "https://assets.nintendo.eu"
    };
    for (const char* candidate : origins) {
        const std::string prefix{candidate};
        if (url.size() > prefix.size() && url.compare(0, prefix.size(), prefix) == 0 &&
            url[prefix.size()] == '/') {
            host = prefix;
            endpoint = url.substr(prefix.size());
            return endpoint.size() <= 2048 &&
                endpoint.find_first_of("\r\n\t\\") == std::string::npos;
        }
    }
    return false;
}

// JPEG EXIF orientation: preserve the natural top-left orientation of the
// source image before encoding it to WebP. Never rely on an OpenGL double flip.
int DailyExifOrientation(const std::string& bytes) {
    const auto* b = reinterpret_cast<const unsigned char*>(bytes.data());
    const std::size_t size = bytes.size();
    if (size < 16 || b[0] != 0xff || b[1] != 0xd8) return 1;
    for (std::size_t p = 2; p + 12 < size;) {
        if (b[p] != 0xff) break;
        const unsigned char marker = b[p + 1];
        if (marker == 0xda || marker == 0xd9) break;
        if (p + 4 > size) break;
        const std::size_t length = (static_cast<unsigned>(b[p+2]) << 8) | b[p+3];
        if (length < 2 || length > size - p - 2) break;
        if (marker == 0xe1 && length >= 16 &&
            std::memcmp(b + p + 4, "Exif\0\0", 6) == 0) {
            const std::size_t tiff = p + 10;
            const bool little = b[tiff] == 'I' && b[tiff+1] == 'I';
            const bool big = b[tiff] == 'M' && b[tiff+1] == 'M';
            if (!little && !big) return 1;
            const auto u16 = [&](std::size_t i) {
                return little ? (static_cast<unsigned>(b[i]) |
                                 static_cast<unsigned>(b[i+1]) << 8) :
                                (static_cast<unsigned>(b[i]) << 8 |
                                 static_cast<unsigned>(b[i+1]));
            };
            const auto u32 = [&](std::size_t i) {
                return little ? (static_cast<std::uint32_t>(u16(i)) |
                                 static_cast<std::uint32_t>(u16(i+2)) << 16) :
                                (static_cast<std::uint32_t>(u16(i)) << 16 |
                                 static_cast<std::uint32_t>(u16(i+2)));
            };
            const std::size_t bound = p + 2 + length;
            if (tiff + 8 > bound || u16(tiff+2) != 42) return 1;
            const std::size_t ifd = tiff + u32(tiff+4);
            if (ifd + 2 > bound) return 1;
            const unsigned count = std::min(u16(ifd), 256u);
            for (unsigned j = 0; j < count; ++j) {
                const std::size_t entry = ifd + 2 + 12u * j;
                if (entry + 12 > bound) break;
                if (u16(entry) == 0x0112 && u16(entry + 2) == 3 &&
                    u32(entry + 4) == 1) {
                    const unsigned orientation = u16(entry + 8);
                    return orientation >= 1 && orientation <= 8 ?
                        static_cast<int>(orientation) : 1;
                }
            }
            return 1;
        }
        p += 2 + length;
    }
    return 1;
}

std::optional<std::string> DailyEncodeWebP(const std::string& source) {
    if (source.size() < 32 || source.size() > (7u << 20)) return {};
    int width = 0, height = 0, channels = 0;
    std::scoped_lock codec_lock(ArtworkCodecMutex());
    const auto* data = reinterpret_cast<const stbi_uc*>(source.data());
    if (!stbi_info_from_memory(data, static_cast<int>(source.size()),
                               &width, &height, &channels) ||
        width < 300 || height < 200 || width > 4096 || height > 4096 ||
        static_cast<std::uint64_t>(width) * height > 12000000u) return {};
    stbi_uc* pixels = stbi_load_from_memory(
        data, static_cast<int>(source.size()), &width, &height, &channels, 4);
    if (!pixels) return {};
    const int orientation = DailyExifOrientation(source);
    const bool swap = orientation >= 5;
    const int ow = swap ? height : width;
    const int oh = swap ? width : height;
    constexpr int out_w = 1280, out_h = 720;
    std::vector<std::uint8_t> target(out_w * out_h * 4u);
    const bool portrait = static_cast<double>(ow) / oh < 1.40;
    const double scale = std::max(static_cast<double>(out_w)/ow,
                                  static_cast<double>(out_h)/oh);
    const double overlay_scale = std::min(1180.0 / ow, 680.0 / oh);
    auto sample = [&](int x, int y, double s, bool darken) {
        const int u = std::clamp(static_cast<int>(
            (x - out_w / 2.0) / s + ow / 2.0), 0, ow - 1);
        const int v = std::clamp(static_cast<int>(
            (y - out_h / 2.0) / s + oh / 2.0), 0, oh - 1);
        int sx = u, sy = v;
        switch (orientation) {
        case 2: sx = width - 1 - u; break;
        case 3: sx = width - 1 - u; sy = height - 1 - v; break;
        case 4: sy = height - 1 - v; break;
        case 5: sx = v; sy = u; break;
        case 6: sx = v; sy = height - 1 - u; break;
        case 7: sx = width - 1 - v; sy = height - 1 - u; break;
        case 8: sx = width - 1 - v; sy = u; break;
        default: break;
        }
        const auto* src = pixels + (static_cast<std::size_t>(sy)*width + sx)*4u;
        const auto at = (static_cast<std::size_t>(y)*out_w + x)*4u;
        for (int c = 0; c < 3; ++c)
            target[at + c] = static_cast<std::uint8_t>(
                darken ? static_cast<unsigned>(src[c])*55u/100u : src[c]);
        target[at + 3] = 255;
    };
    for (int y = 0; y < out_h; ++y) {
        for (int x = 0; x < out_w; ++x)
            sample(x, y, scale, portrait);
    }
    if (portrait) {
        const int fw = std::min(out_w, static_cast<int>(ow * overlay_scale));
        const int fh = std::min(out_h, static_cast<int>(oh * overlay_scale));
        for (int y = (out_h-fh)/2; y < (out_h+fh)/2; ++y)
            for (int x = (out_w-fw)/2; x < (out_w+fw)/2; ++x)
                sample(x, y, overlay_scale, false);
    }
    stbi_image_free(pixels);
    std::uint8_t* webp = nullptr;
    const std::size_t length = WebPEncodeRGBA(
        target.data(), out_w, out_h, out_w*4, 80.0f, &webp);
    if (!length || !webp || length > (7u << 20)) {
        WebPFree(webp);
        return {};
    }
    std::string result(reinterpret_cast<const char*>(webp), length);
    WebPFree(webp);
    return result;
}

void RefreshDailyOnlyAfterSelection(const std::filesystem::path& folder,
                                    const std::string& today) {
    // This function runs exclusively on Launcher::daily_wallpaper_scan_'s
    // std::async worker. The UI calls it only when background_style == 5.
    // A persisted daily receipt prevents repeat download after restart.
    if (today.empty()) return;
    std::error_code ec;
    std::filesystem::create_directories(folder, ec);
    if (ec || std::filesystem::is_symlink(folder, ec) || ec) return;
    const auto marker = folder / ".checked-day";
    std::ifstream previous(marker);
    std::string last;
    std::getline(previous, last);
    if (last == today) return;
    const auto staged_marker = folder / ".checked-day.tmp";
    {
        std::ofstream receipt(staged_marker, std::ios::binary | std::ios::trunc);
        if (!receipt || !(receipt << today << '\n')) return;
    }
    if (std::rename(staged_marker.string().c_str(),
                    marker.string().c_str()) != 0) return;

    std::vector<DailyOnlineCandidate> candidates;
    auto add = [&](std::string title, std::string platform,
                   const std::string& date, bool named_date,
                   const std::string& image) {
        if (title.empty() || title.size() > 160 || candidates.size() >= 3000) return;
        auto timestamp = DailyReleaseTime(date, named_date);
        std::string host, path;
        if (!timestamp || !DailyApprovedArt(image, host, path)) return;
        const std::string iso = DailyDate(*timestamp);
        if (iso.empty()) return;
        candidates.push_back({std::move(title), std::move(platform),
                              iso, std::move(host), std::move(path), *timestamp});
    };

    if (auto response = DailyRequest(
            "https://raw.githubusercontent.com",
            "/codemaverick-hub/switch2-tracker/main/data/games.json",
            3u << 20)) {
        const auto feed = nlohmann::json::parse(*response, nullptr, false);
        if (feed.is_object() && feed.contains("games") && feed["games"].is_array()) {
            std::size_t visited = 0;
            for (const auto& item : feed["games"]) {
                if (++visited > 3000) break;
                if (!item.is_object() || !item.contains("status") ||
                    !item["status"].is_string() ||
                    item["status"].get<std::string>() != "r")
                    continue;
                if (!item.contains("title") || !item["title"].is_string() ||
                    !item.contains("date") || !item["date"].is_string() ||
                    !item.contains("art") || !item["art"].is_string()) continue;
                add(item["title"].get<std::string>(), "ns2",
                    item["date"].get<std::string>(), true,
                    item["art"].get<std::string>());
            }
        }
    }
    if (auto response = DailyRequest(
            "https://raw.githubusercontent.com",
            "/Langegen/switch-game-collection/main/new_release.json",
            3u << 20)) {
        const auto feed = nlohmann::json::parse(*response, nullptr, false);
        if (feed.is_array()) {
            std::size_t visited = 0, verified = 0;
            for (const auto& item : feed) {
                if (++visited > 50 || verified >= 16) break;
                if (!item.is_object() || !item.contains("title_id") ||
                    !item["title_id"].is_string()) continue;
                std::string tid = item["title_id"].get<std::string>();
                if (tid.size() != 16 ||
                    !std::all_of(tid.begin(), tid.end(), [](unsigned char ch) {
                        return std::isxdigit(ch) != 0;
                    })) continue;
                std::transform(tid.begin(), tid.end(), tid.begin(),
                               [](unsigned char ch){ return static_cast<char>(std::toupper(ch)); });
                auto detail = DailyRequest(
                    "https://api.nlib.cc", "/nx/" + tid +
                    "?fields=name,releaseDate,console,type,isDemo,banner", 8192);
                if (!detail) continue;
                const auto record = nlohmann::json::parse(*detail, nullptr, false);
                if (!record.is_object() ||
                    !record.contains("id") || !record["id"].is_string() ||
                    record["id"].get<std::string>() != tid ||
                    !record.contains("type") || !record["type"].is_string() ||
                    record["type"].get<std::string>() != "base" ||
                    !record.contains("console") || !record["console"].is_string() ||
                    record["console"].get<std::string>() != "nx" ||
                    (record.contains("isDemo") &&
                     (!record["isDemo"].is_boolean() || record["isDemo"].get<bool>())) ||
                    !record.contains("name") || !record["name"].is_string() ||
                    !record.contains("releaseDate") ||
                    !record["releaseDate"].is_string()) continue;
                const std::size_t count = candidates.size();
                add(record["name"].get<std::string>(), "ns1",
                    record["releaseDate"].get<std::string>(), false,
                    "https://api.nlib.cc/nx/" + tid + "/banner/720p");
                if (candidates.size() > count) ++verified;
            }
        }
    }
    std::sort(candidates.begin(), candidates.end(),
              [](const auto& a, const auto& b) {
        return a.timestamp == b.timestamp ? a.title < b.title :
               a.timestamp > b.timestamp;
    });

    struct Download { DailyOnlineCandidate info; std::string webp; };
    std::vector<Download> images;
    std::unordered_set<std::string> seen;
    for (const auto& candidate : candidates) {
        if (images.size() >= 8) break;
        std::string key = candidate.title;
        std::transform(key.begin(), key.end(), key.begin(),
                       [](unsigned char ch){ return static_cast<char>(std::tolower(ch)); });
        if (!seen.insert(key).second) continue;
        const auto source = DailyRequest(candidate.host, candidate.endpoint, 7u << 20);
        if (!source) continue;
        auto webp = DailyEncodeWebP(*source);
        if (!webp) continue;
        images.push_back({candidate, std::move(*webp)});
    }
    if (images.empty()) return; // existing complete snapshot is retained
    nlohmann::json manifest = {
        {"schema", 1}, {"generated", today}, {"entries", nlohmann::json::array()}};
    std::unordered_set<std::string> keep;
    for (std::size_t i = 0; i < images.size(); ++i) {
        char name[24]{};
        std::snprintf(name, sizeof(name), "wall-%02u.webp", static_cast<unsigned>(i));
        const auto path = folder / name;
        const auto tmp = folder / (std::string(name) + ".tmp");
        std::ofstream file(tmp, std::ios::binary | std::ios::trunc);
        if (!file.write(images[i].webp.data(), images[i].webp.size())) return;
        file.close();
        if (!file || std::rename(tmp.string().c_str(),
                                 path.string().c_str()) != 0) return;
        keep.insert(name);
        manifest["entries"].push_back({
            {"filename", name}, {"title", images[i].info.title},
            {"platform", images[i].info.platform},
            {"release_date", images[i].info.released},
            {"source", images[i].info.host == "https://api.nlib.cc" ? "Nlib" : "Nintendo"},
            {"approved", true}
        });
    }
    const auto index_tmp = folder / "index.json.tmp";
    const auto index = folder / "index.json";
    {
        std::ofstream file(index_tmp, std::ios::binary | std::ios::trunc);
        if (!file || !(file << manifest.dump(2) << '\n')) return;
    }
    if (std::rename(index_tmp.string().c_str(), index.string().c_str()) != 0)
        return;
    for (std::filesystem::directory_iterator it(folder, ec), end;
         !ec && it != end; it.increment(ec)) {
        const auto name = it->path().filename().string();
        if (name.rfind("wall-", 0) == 0 && keep.count(name) == 0 &&
            !std::filesystem::is_symlink(it->symlink_status()) &&
            it->is_regular_file())
            std::filesystem::remove(it->path(), ec);
    }
}
} // namespace

std::string EdenServices::daily_wallpaper() {
    // This method is invoked ONLY by the asynchronous texture/appearance
    // worker after the user explicitly chooses the Daily background. A fresh
    // install does not contain even a single preloaded daily artwork image.
    const auto folder = std::filesystem::path(Eden::UserDir()) / "wallpapers" / "daily";
    const auto today = LocalDay();
    RefreshDailyOnlyAfterSelection(folder, today);
    for (int selected_source = 0; selected_source < 1; ++selected_source) {
        const auto index = folder / "index.json";
        std::error_code ec;
        if (std::filesystem::is_symlink(std::filesystem::symlink_status(index, ec)) ||
            ec || !std::filesystem::is_regular_file(index, ec) ||
            std::filesystem::file_size(index, ec) > 256u * 1024u || ec) continue;
        std::ifstream stream(index, std::ios::binary);
        if (!stream) continue;
        nlohmann::json parsed = nlohmann::json::parse(stream, nullptr, false);
        if (parsed.is_discarded() || !parsed.is_object() || !parsed.contains("entries") ||
            !parsed["entries"].is_array()) continue;
        const auto today = LocalDay();
        if (today.empty()) return {};
        struct Candidate { std::string date; std::string path; };
        std::vector<Candidate> candidates;
        for (const auto& item : parsed["entries"]) {
            if (candidates.size() >= 64) break;
            if (!item.is_object()) continue;
            if (!item.contains("approved") || !item["approved"].is_boolean() ||
                !item["approved"].get<bool>()) continue;
            if (!item.contains("filename") || !item["filename"].is_string() ||
                !item.contains("release_date") || !item["release_date"].is_string() ||
                !item.contains("platform") || !item["platform"].is_string()) continue;
            const std::string platform = item["platform"].get<std::string>();
            if (platform != "ns1" && platform != "ns2") continue;
            const std::string date = item["release_date"].get<std::string>();
            if (date.size() != 10 || date[4] != '-' || date[7] != '-' || date > today ||
                !std::all_of(date.begin(), date.end(), [](char c) {
                    return (c >= '0' && c <= '9') || c == '-'; })) continue;
            const std::string file = item["filename"].get<std::string>();
            const auto path = CheckedWallpaper(folder, file);
            if (!path.empty()) candidates.push_back({date, path});
        }
        if (candidates.empty()) continue;
        std::sort(candidates.begin(), candidates.end(), [](const auto& a, const auto& b) {
            return a.date > b.date || (a.date == b.date && a.path < b.path);
        });
        // Strictly eight user-downloaded recent releases; never use app art.
        if (candidates.size() > 8) candidates.resize(8);
        const std::time_t now = std::time(nullptr);
        const std::tm* local = std::localtime(&now);
        // Use a stable per-day index, not process randomness.
        const int day = local ? (local->tm_year * 366 + local->tm_yday) : 0;
        return candidates[static_cast<std::size_t>(day) % candidates.size()].path;
    }
    return {};
}


std::string EdenServices::daily_wallpaper_caption(const std::string& path,
                                                  int language_choice) {
    // The image was already selected by the verified daily manifest worker.
    // Never present a guessed title, date or attribution from the filename.
    if (path.empty()) return {};
    namespace fs = std::filesystem;
    const fs::path folder = fs::path(Eden::UserDir()) / "wallpapers" / "daily";
    const fs::path file{path};
    if (file.parent_path() != folder || CheckedWallpaper(folder, file.filename().string()).empty())
        return {};
    const auto index = folder / "index.json";
    std::error_code ec;
    const auto status = fs::symlink_status(index, ec);
    if (ec || fs::is_symlink(status) || !fs::is_regular_file(status) ||
        fs::file_size(index, ec) > (256u << 10) || ec) return {};
    std::ifstream input(index, std::ios::binary);
    if (!input) return {};
    const auto doc = nlohmann::json::parse(input, nullptr, false);
    if (!doc.is_object() || !doc.contains("entries") || !doc["entries"].is_array())
        return {};
    const auto lang = Eden::kLanguageKeys[std::clamp(language_choice, 0,
                      static_cast<int>(std::size(Eden::kLanguageKeys)) - 1)];
    const std::string_view region{lang};
    for (const auto& entry : doc["entries"]) {
        if (!entry.is_object() ||
            !entry.contains("filename") || !entry["filename"].is_string() ||
            entry["filename"].get<std::string>() != file.filename().string() ||
            !entry.contains("approved") || !entry["approved"].is_boolean() ||
            !entry["approved"].get<bool>() ||
            !entry.contains("title") || !entry["title"].is_string() ||
            !entry.contains("release_date") || !entry["release_date"].is_string())
            continue;
        const auto title = entry["title"].get<std::string>();
        const auto iso = entry["release_date"].get<std::string>();
        if (title.empty() || title.size() > 160 ||
            iso.size() != 10 || iso[4] != '-' || iso[7] != '-')
            return {};
        const auto digits = [](std::string_view text) {
            return std::all_of(text.begin(), text.end(), [](unsigned char x) {
                return x >= '0' && x <= '9';
            });
        };
        if (!digits(std::string_view(iso).substr(0, 4)) ||
            !digits(std::string_view(iso).substr(5, 2)) ||
            !digits(std::string_view(iso).substr(8, 2))) return {};
        const std::string date =
            region == "en-US" ? iso.substr(5,2) + "/" + iso.substr(8,2) + "/" + iso.substr(0,4) :
            (region.starts_with("fr") || region.starts_with("en-GB") ||
             region.starts_with("es") || region.starts_with("it") ||
             region.starts_with("pt") || region.starts_with("de"))
                ? iso.substr(8,2) + "/" + iso.substr(5,2) + "/" + iso.substr(0,4) : iso;
        // Older cache snapshots omit source: display an explicit unknown
        // rather than falsely attributing Nintendo art to GamesDB.
        // A legacy receipt without provider does not prove Nlib/GamesDB origin.
        std::string source;
        if (entry.contains("source") && entry["source"].is_string()) {
            const auto known = entry["source"].get<std::string>();
            if (known == "Nlib" || known == "Nintendo") source = known;
        }
        return title + " · " + date + (source.empty() ? "" : " · " + source);
    }
    return {};
}

const std::vector<std::string>& EdenServices::resolution_labels() {
    return resolution_labels_;
}

const std::vector<std::string>& EdenServices::resolution_keys() {
    return resolution_keys_;
}

const std::vector<std::string>& EdenServices::filter_labels() {
    return filter_labels_;
}

const std::vector<std::string>& EdenServices::anti_aliasing_labels() {
    return anti_aliasing_labels_;
}

const std::vector<std::string>& EdenServices::performance_profile_labels() {
    return performance_profile_labels_;
}

const std::vector<std::string>& EdenServices::language_labels() {
    return language_labels_;
}

std::string EdenServices::language_region(int language) {
    static constexpr const char* kRegions[] = {TR("Japan"), TR("USA"), TR("Europe"), TR("Australia"), TR("China"),
                                               TR("Korea"), TR("Taiwan")};
    if (language < 0 || language >= int(std::size(Eden::kLanguageRegions))) return {};
    return tr(kRegions[Eden::kLanguageRegions[language]]);
}

std::string EdenServices::setup_details() {
    return setup_.empty() ?
        tr("Keys and firmware: startup checks passed. Game-specific compatibility is checked at launch.") :
        SetupMessage(setup_);
}

pe::ui::DiagnosticsInfo EdenServices::diagnostics() {
    return diagnostics(nullptr);
}

pe::ui::DiagnosticsInfo EdenServices::diagnostics(const std::atomic<bool>* cancel) {
    if (cancel && cancel->load(std::memory_order_acquire)) return {};
    pe::ui::DiagnosticsInfo result;
    result.filesystem = Eden::FilesystemAccess() ? tr("Full filesystem") : tr("Sandbox only");
    result.data_path = Eden::FilesystemAccess() ? Eden::kDataDir : Eden::UserDir();

    // RELEASE-SAFETY (FW 13.60): do not call libc statfs/statvfs, which
    // previously raised SYSTEM_ILLEGAL_FUNCTION_CALL. This directory inventory
    // now runs on a cancellable background worker; the console's filesystem
    // view also does not establish physical SSD capacity.
    result.storage_root = Eden::AssetsDir();

    const std::filesystem::path cache = std::filesystem::path{Eden::UserDir()} / "cache";
    const std::uintmax_t shader_bytes =
        TreeBytes(cache / "shader", cancel) + TreeBytes(cache / "radv", cancel) +
        TreeBytes(cache / "native-opengl", cancel) + TreeBytes(cache / "jit", cancel);
    if (cancel && cancel->load(std::memory_order_acquire)) return {};
    result.shader_cache_bytes = static_cast<std::uint64_t>(shader_bytes);
    result.shader_caches = StorageSize(shader_bytes);
    result.logs = StorageSize(TreeBytes(Eden::LogsDir(), cancel));
    if (cancel && cancel->load(std::memory_order_acquire)) return {};
    return result;
}

bool EdenServices::clear_shader_caches(std::string* message) {
    const std::filesystem::path cache = std::filesystem::path{Eden::UserDir()} / "cache";
    const std::uintmax_t before =
        TreeBytes(cache / "shader") + TreeBytes(cache / "radv") +
        TreeBytes(cache / "native-opengl") + TreeBytes(cache / "jit");
    bool ok = true;
    // Eden's per-title Vulkan/OpenGL pipeline cache lives under cache/shader. The other
    // directories are backend/JIT auxiliaries. A maintenance clear must remove all of them,
    // otherwise the launcher can report success while the active game's pipelines survive.
    for (const char* name : {"shader", "radv", "native-opengl", "jit"}) {
        std::error_code error;
        std::filesystem::remove_all(cache / name, error);
        ok = ok && !error;
    }
    if (message) {
        if (ok)
            *message = fill(tr("Cleared {0} of cache."), {StorageSize(before)});
        else
            *message = tr("Some cache files could not be removed.");
    }
    if (ok) Eden::Report("cache", "Shader/JIT caches cleared from Diagnostics");
    return ok;
}

bool EdenServices::folders(const std::string& directory, std::vector<std::string>* names) {
    bool ok = false;
    *names = ListEntries(directory, true, ok);
    return ok;
}

pe::ui::FolderInfo EdenServices::folder_info(const std::string& directory) {
    pe::ui::FolderInfo info;
    info.keys = Eden::FileExists(JoinPath(directory, "keys/prod.keys"));
    // Match the same recognized formats and explicit family directory precedence
    // as the actual firmware resolver; a folder alone is not a valid firmware.
    // Never follow symlinked directories via DetectFirmwareFormat.
    const std::filesystem::path fw_root = JoinPath(directory, "firmware");
    info.firmware = CountFiles(fw_root.string(), {".nca"});
    const auto format_name = [](Eden::FirmwareFormat f) -> const char* {
        switch (f) {
        case Eden::FirmwareFormat::Nca: return "NCA";
        case Eden::FirmwareFormat::Extracted: return "EXEFS";
        case Eden::FirmwareFormat::Zip: return "ZIP";
        default: return nullptr;
        }
    };
    const auto family = [&](std::initializer_list<const char*> names) {
        for (const char* child : names) {
            const auto folder = fw_root / child;
            if (const char* format = format_name(Eden::DetectFirmwareFormat(folder))) {
                const int nca = CountFiles(folder.string(), {".nca"});
                if (nca > 0) info.firmware = std::max(info.firmware, 0) + nca;
                return std::string(format);
            }
        }
        return std::string{};
    };
    const std::string ns1 = family({"ns1", "switch1", "ns1-extracted", "switch1-extracted"});
    const std::string ns2 = family({"ns2", "switch2", "ns2-extracted", "switch2-extracted"});
    const auto flat = Eden::DetectFirmwareFormat(fw_root);
    info.firmware_ready = !ns1.empty() || !ns2.empty() || flat != Eden::FirmwareFormat::None;
    if (info.firmware_ready) {
        info.firmware_detail = "NS1: " + (ns1.empty() ? "-" : ns1) +
                               "  |  NS2: " + (ns2.empty() ? "-" : ns2);
        if (const char* legacy = format_name(flat))
            info.firmware_detail += std::string("  |  root: ") + legacy;
    }
    const std::string roms_path = JoinPath(directory, "roms");
    const int regular = CountFiles(roms_path,
                                  {".nsp", ".xci", ".nsz", ".xcz", ".nro", ".nso",
                                   ".nca", ".nax", ".kip"});
    const int extracted = CountExeFsFolders(roms_path);
    info.games = regular < 0 || extracted < 0 ? -1 : regular + extracted;
    return info;
}

std::string EdenServices::files_folder() { return Eden::AssetsDir(); }
std::string EdenServices::saved_files_folder() { return Eden::LoadSavedAssetsDir(); }
std::string EdenServices::default_files_folder() { return Eden::kDefaultAssetsDir; }

bool EdenServices::set_files_folder(const std::string& directory) {
    if (!Eden::FilesystemAccess() || !Eden::ValidAssetsDir(directory)) return false;

    std::error_code error;
    const auto status = std::filesystem::symlink_status(directory, error);
    if (error || std::filesystem::is_symlink(status) || !std::filesystem::is_directory(status))
        return false;

    // Selecting external storage changes only the root. Every root has the exact same Encore
    // layout; individual keys/firmware/roms/etc. paths are never configurable.
    for (const char* name : {"keys", "firmware", "roms", "updates", "mods",
                             "save-import", "save-export", "ryujinx"}) {
        const std::filesystem::path child = std::filesystem::path{directory} / name;
        error.clear();
        const auto child_status = std::filesystem::symlink_status(child, error);
        if (!error && std::filesystem::exists(child_status) &&
            (std::filesystem::is_symlink(child_status) || !std::filesystem::is_directory(child_status))) {
            Eden::Report("storage", (std::string{"Unsafe storage entry: "} + child.string()).c_str());
            return false;
        }
        error.clear();
        std::filesystem::create_directories(child, error);
        if (error) {
            Eden::Report("storage", (std::string{"Could not prepare "} + name + ": " + error.message()).c_str());
            return false;
        }
    }
    const bool saved = Eden::SaveAssetsDir(directory);
    if (!saved) Eden::Report("settings", "Could not write the storage root");
    return saved;
}

int EdenServices::filesystem_access() { return Eden::FilesystemAccessStatus(); }

#ifdef EDEN_SAVE_IMPORT
// Save transfer (ryujinx_saves.h): a save comes in from save-import/<title ID>/ or a Ryujinx data
// folder in ryujinx/, and goes out to save-export/, all next to roms/.
bool EdenServices::save_transfer_available() { return true; }

pe::ui::SaveSource EdenServices::save_import_source(std::uint64_t title_id) {
    switch (eden_save_import_source(title_id)) {
    case EDEN_SAVE_FOLDER: return pe::ui::SaveSource::folder;
    case EDEN_SAVE_RYUJINX: return pe::ui::SaveSource::ryujinx;
    default: return pe::ui::SaveSource::none;
    }
}

bool EdenServices::save_import(std::uint64_t title_id, std::string* message) {
    char backup[256]{};
    switch (eden_save_import(title_id, backup, sizeof(backup))) {
    case EDEN_SAVE_DONE:
        *message = backup[0] ? tr("Imported. The save it replaced was backed up.") : tr("Imported.");
        return true;
    case EDEN_SAVE_NOTHING: {
        char title[17]{};
        std::snprintf(title, sizeof(title), "%016llX", static_cast<unsigned long long>(title_id));
        *message = fill(tr("To import, copy a Ryujinx folder to ryujinx/ or a save to save-import/{0}/, next to roms/."),
                        {title});
        return false;
    }
    case EDEN_SAVE_NO_USER:
        *message = tr("Start any game once before importing a save.");
        return false;
    default:
        *message = tr("Import failed. The current save is unchanged.");
        return false;
    }
}

bool EdenServices::save_export(std::uint64_t title_id, std::string* message) {
    char folder[256]{};
    switch (eden_save_export(title_id, folder, sizeof(folder))) {
    case EDEN_SAVE_DONE: {
        // The end of the path tells it apart: save-export/<title ID>-<date>-<time>.
        const std::string path = folder;
        const std::size_t name = path.rfind("save-export/");
        *message = fill(tr("Exported to {0}."), {name == std::string::npos ? path : path.substr(name)});
        return true;
    }
    case EDEN_SAVE_NOTHING:
        *message = tr("This game has no save to export yet.");
        return false;
    default:
        *message = tr("Export failed. Check that the storage root can be written.");
        return false;
    }
}
#else
bool EdenServices::save_transfer_available() { return false; }
pe::ui::SaveSource EdenServices::save_import_source(std::uint64_t) { return pe::ui::SaveSource::none; }
bool EdenServices::save_import(std::uint64_t, std::string*) { return false; }
bool EdenServices::save_export(std::uint64_t, std::string*) { return false; }
#endif

// Mods (headless/mods.h): what the selected storage root's mods/<title ID>/ holds for a game, and
// which of them are switched off (settings_store.h).
std::vector<pe::ui::Mod> EdenServices::mods(std::uint64_t title_id) {
    std::vector<pe::ui::Mod> result;
    const auto off = Eden::LoadDisabledMods(title_id);
    for (const Eden::Mods::Mod& mod : Eden::Mods::List(Eden::AssetsPath("mods"), title_id)) {
        std::string kind;
        const auto add = [&kind](const char* text) {
            if (!kind.empty()) kind += ", ";
            kind += tr(text);
        };
        if (mod.kinds & Eden::Mods::kCode) add(TR("Patch"));
        if (mod.kinds & Eden::Mods::kFiles) add(TR("Files"));
        if (mod.kinds & Eden::Mods::kCheats) add(TR("Cheats"));
        result.push_back({mod.name, kind, std::find(off.begin(), off.end(), mod.name) == off.end()});
    }
    return result;
}

bool EdenServices::set_mod_enabled(std::uint64_t title_id, const std::string& name, bool enabled) {
    const bool saved = Eden::SaveModEnabled(title_id, name, enabled);
    if (!saved) Eden::Report("settings", "Could not write the game's mods");
    return saved;
}

bool EdenServices::mods_enabled(std::uint64_t title_id) { return Eden::LoadModsEnabled(title_id); }

bool EdenServices::set_mods_enabled(std::uint64_t title_id, bool enabled) {
    const bool saved = Eden::SaveModsEnabled(title_id, enabled);
    if (!saved) Eden::Report("settings", "Could not write the game's mods switch");
    return saved;
}

std::string EdenServices::mods_folder(std::uint64_t title_id) {
    return "mods/" + Eden::Mods::TitleName(title_id) + "/";
}

bool EdenServices::make_mods_folder(std::uint64_t title_id) {
    const std::string root = Eden::AssetsPath("mods");
    if (!Eden::Mods::TitleFolder(root, title_id).empty()) return true;
    (void)mkdir(root.c_str(), 0777);
    return mkdir(Eden::Mods::TitleFolderToCreate(root, title_id).c_str(), 0777) == 0;
}

bool EdenServices::load_image(const std::string& path, pe::gfx::Image* image) {
    // Covers have full paths; the launcher's own art is named from its ui folder.
    const std::string resolved =
        !path.empty() && path[0] == '/' ? path : Eden::AppFile("ui/" + path);
    if (resolved.size() >= 4 && resolved.compare(resolved.size() - 4, 4, ".dds") == 0)
        return pe::gfx::load_avatar_dds(resolved, image);
    if (pe::gfx::load_tga(resolved, image))
        return true;
    if (resolved.ends_with(".webp")) {
        // WebP decoding belongs to the bounded asynchronous cover worker.
        struct stat info{};
        if (stat(resolved.c_str(), &info) != 0 || !S_ISREG(info.st_mode) ||
            info.st_size < 30 || info.st_size > (16LL << 20)) return false;
        std::FILE* file = std::fopen(resolved.c_str(), "rb");
        if (!file) return false;
        std::vector<std::uint8_t> bytes(static_cast<std::size_t>(info.st_size));
        const bool read = std::fread(bytes.data(), 1, bytes.size(), file) == bytes.size();
        std::fclose(file);
        if (!read) return false;
        int width = 0, height = 0;
        if (!WebPGetInfo(bytes.data(), bytes.size(), &width, &height) ||
            width <= 0 || height <= 0 || width > 4096 || height > 4096 ||
            static_cast<std::uint64_t>(width) * height > 3840u * 2160u) return false;
        std::uint8_t* rgba = WebPDecodeRGBA(bytes.data(), bytes.size(), &width, &height);
        if (!rgba) return false;
        image->width = width;
        image->height = height;
        image->rgba.assign(rgba, rgba + static_cast<std::size_t>(width) * height * 4u);
        WebPFree(rgba);
        return true;
    }

    // Remote enrichment (Nlib) is cached as JPEG. Decode it with the same stb_image
    // implementation already linked for game metadata/icon extraction.
    int width = 0;
    int height = 0;
    int channels = 0;
    stbi_uc* rgba = stbi_load(resolved.c_str(), &width, &height, &channels, 4);
    if (!rgba || width <= 0 || height <= 0 || width > 8192 || height > 8192) {
        if (rgba) stbi_image_free(rgba);
        return false;
    }
    image->width = width;
    image->height = height;
    image->rgba.assign(rgba, rgba + static_cast<std::size_t>(width) *
                                      static_cast<std::size_t>(height) * 4u);
    stbi_image_free(rgba);
    return true;
}
