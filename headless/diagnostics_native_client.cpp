// SPDX-License-Identifier: GPL-3.0-or-later
#include "diagnostics_native_client.h"

#include "diagnostics_report_queue.h"
#include "crash_report.h"
#include "settings_store.h"
#include "storage_paths.h"
#include "common/net/net.h"

#include <nlohmann/json.hpp>

#include <algorithm>
#include <array>
#include <atomic>
#include <chrono>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <memory>
#include <thread>
#include <iterator>
#include <limits>
#include <optional>
#include <random>
#include <string>
#include <string_view>
#include <sys/stat.h>
#include <utility>
#include <vector>

#ifdef PS5_NATIVE
extern "C" int sceRandomGetRandomNumber(std::uint8_t* buffer, std::size_t size);
#endif

namespace Eden::DiagnosticsClient {
namespace {

using Queue = DiagnosticsSharing::Queue;
using Category = DiagnosticsSharing::Category;
using Phase = DiagnosticsSharing::Phase;
using Clock = std::chrono::steady_clock;
using Json = nlohmann::json;

constexpr std::string_view kCollector = "https://encore.dynv6.net";
constexpr std::string_view kReportsPath = "/api/diagnostics/v1/reports";
constexpr std::string_view kErasePath = "/api/diagnostics/v1/erase";
constexpr std::size_t kMaxReadBytes = 2u * 1024u * 1024u;
constexpr std::size_t kMaxStateBytes = 144u * 1024u;
constexpr std::size_t kMaxReceipts = 32;

struct Pending {
    Category category{};
    std::string id;
    std::string envelope;
};
struct Receipt {
    Category category{};
    std::string id;
    std::string token;
    bool erase_pending{};
};
struct TransferResult {
    enum class Kind { Report, Erase } kind = Kind::Report;
    std::uint64_t ticket{};
    std::string id;
    Queue::Result result = Queue::Result::Retry;
    std::string server_result;
};
struct TransferState {
    TransferResult result;
    std::atomic_bool completed{false};
};
struct State {
    bool initialized{};
    bool idle{};
    bool game_pending{};
    bool standard{};
    bool advanced{};
    std::string source_sha;
    std::uint64_t last_activity{};
    std::uint64_t game_log_offset{};
    Queue queue;
    std::vector<Pending> pending;
    std::vector<Receipt> receipts;
    std::shared_ptr<TransferState> transfer;
    std::string erase_in_flight;
    std::uint32_t erase_attempts{};
    std::uint64_t erase_last_attempt{};
};
State state;

std::uint64_t Now() noexcept {
    return static_cast<std::uint64_t>(
        std::chrono::duration_cast<std::chrono::seconds>(
            Clock::now().time_since_epoch()).count());
}
bool HexLower(std::string_view value, std::size_t size) {
    if (value.size() != size) return false;
    return std::all_of(value.begin(), value.end(), [](char c) {
        return (c >= '0' && c <= '9') || (c >= 'a' && c <= 'f');
    });
}
bool SourceSha(std::string_view value) {
    return HexLower(value, 40);
}
bool ValidId(std::string_view id) {
    if (id.size() != 36 || id[8] != '-' || id[13] != '-' || id[18] != '-' ||
        id[23] != '-' || id[14] != '4' ||
        (id[19] != '8' && id[19] != '9' && id[19] != 'a' && id[19] != 'b'))
        return false;
    for (std::size_t i = 0; i < id.size(); ++i) {
        if (i == 8 || i == 13 || i == 18 || i == 23) continue;
        const char c = id[i];
        if (!((c >= '0' && c <= '9') || (c >= 'a' && c <= 'f'))) return false;
    }
    return true;
}
const char* CategoryName(Category c) {
    return c == Category::Standard ? "standard" : "advanced";
}
std::optional<Category> ParseCategory(std::string_view value) {
    if (value == "standard") return Category::Standard;
    if (value == "advanced") return Category::Advanced;
    return std::nullopt;
}

bool RandomBytes(std::uint8_t* output, std::size_t size) {
#ifdef PS5_NATIVE
    return output && size && sceRandomGetRandomNumber(output, size) == 0;
#else
    if (!output || !size) return false;
    std::random_device random;
    for (std::size_t i = 0; i < size; ++i)
        output[i] = static_cast<std::uint8_t>(random());
    return true;
#endif
}
std::string Hex(const std::uint8_t* data, std::size_t size) {
    static constexpr char digits[] = "0123456789abcdef";
    std::string out(size * 2, '0');
    for (std::size_t i = 0; i < size; ++i) {
        out[i * 2] = digits[data[i] >> 4];
        out[i * 2 + 1] = digits[data[i] & 15];
    }
    return out;
}
std::optional<std::pair<std::string, std::string>> NewIdentity() {
    std::array<std::uint8_t, 16> uuid{};
    std::array<std::uint8_t, 32> erase{};
    if (!RandomBytes(uuid.data(), uuid.size()) || !RandomBytes(erase.data(), erase.size()))
        return std::nullopt;
    uuid[6] = static_cast<std::uint8_t>((uuid[6] & 0x0f) | 0x40);
    uuid[8] = static_cast<std::uint8_t>((uuid[8] & 0x3f) | 0x80);
    const std::string raw = Hex(uuid.data(), uuid.size());
    std::string id;
    id.reserve(36);
    id.append(raw, 0, 8); id.push_back('-');
    id.append(raw, 8, 4); id.push_back('-');
    id.append(raw, 12, 4); id.push_back('-');
    id.append(raw, 16, 4); id.push_back('-');
    id.append(raw, 20, 12);
    return std::pair{id, Hex(erase.data(), erase.size())};
}

std::uint64_t FileSize(const std::string& path) {
    struct stat info{};
    if (::stat(path.c_str(), &info) != 0 || !S_ISREG(info.st_mode) || info.st_size < 0)
        return 0;
    return static_cast<std::uint64_t>(info.st_size);
}
std::string ReadRange(const std::string& path, std::uint64_t offset) {
    struct stat info{};
    if (::lstat(path.c_str(), &info) != 0 || !S_ISREG(info.st_mode) || S_ISLNK(info.st_mode) ||
        info.st_size <= 0)
        return {};
    const auto end = static_cast<std::uint64_t>(info.st_size);
    std::uint64_t begin = std::min(offset, end);
    if (end - begin > kMaxReadBytes) begin = end - kMaxReadBytes;
    std::ifstream file(path, std::ios::binary);
    if (!file) return {};
    file.seekg(static_cast<std::streamoff>(begin));
    std::string data(static_cast<std::size_t>(end - begin), '\0');
    file.read(data.data(), static_cast<std::streamsize>(data.size()));
    data.resize(static_cast<std::size_t>(std::max<std::streamsize>(0, file.gcount())));
    return data;
}
std::string ReadSmallFile(const std::string& path, std::size_t maximum) {
    struct stat info{};
    if (::lstat(path.c_str(), &info) != 0 || !S_ISREG(info.st_mode) || S_ISLNK(info.st_mode) ||
        info.st_size <= 0 || static_cast<std::uint64_t>(info.st_size) > maximum)
        return {};
    std::ifstream file(path, std::ios::binary);
    if (!file) return {};
    return std::string(std::istreambuf_iterator<char>{file}, {});
}

std::optional<std::uint64_t> DecimalAfter(std::string_view text, std::string_view prefix) {
    const auto at = text.find(prefix);
    if (at == std::string_view::npos) return std::nullopt;
    std::size_t pos = at + prefix.size();
    if (pos >= text.size() || text[pos] < '0' || text[pos] > '9') return std::nullopt;
    std::uint64_t value = 0;
    for (; pos < text.size() && text[pos] >= '0' && text[pos] <= '9'; ++pos) {
        const unsigned digit = static_cast<unsigned>(text[pos] - '0');
        if (value > (999999999999ULL - digit) / 10) return std::nullopt;
        value = value * 10 + digit;
    }
    return value;
}
std::optional<std::string> CrashSignal(std::string_view text) {
    static constexpr std::string_view allowed[] = {
        "SIGSEGV", "SIGBUS", "SIGILL", "SIGFPE", "SIGABRT", "SIGSYS", "SIGTRAP"};
    const auto at = text.find("what: ");
    if (at == std::string_view::npos) return std::nullopt;
    const std::string_view tail = text.substr(at + 6);
    for (const auto signal : allowed)
        if (tail.starts_with(signal)) return std::string{signal};
    return std::nullopt;
}
Json StandardReport(std::string_view text) {
    Json report;
    const auto signal = CrashSignal(text);
    if (!signal) return {};
    report["schema"] = 1;
    report["category"] = "standard";
    report["source_sha"] = state.source_sha;
    report["signal"] = *signal;
    for (const auto& [label, key] : std::array<std::pair<std::string_view, const char*>, 4>{{
        {"gpu submitted lists (sample 1/2/3 then 64-step): ", "gpu_submitted_sample"},
        {"gpu completed commands (64-step sample): ", "gpu_completed_floor64"},
        {"watchdog suspected stalls: ", "watchdog_stalls"},
        {"invalid guest-memory accesses: ", "invalid_guest_accesses"},
    }}) {
        if (const auto value = DecimalAfter(text, label)) report[key] = *value;
    }
    return report;
}
bool FiniteBound(double value) {
    return std::isfinite(value) && value >= 0.0 && value <= 1.0e8;
}
Json AdvancedReport(std::string_view text) {
    Json frames = Json::array();
    Json waits = Json::array();
    std::size_t from = 0;
    while (from < text.size()) {
        const auto end = text.find('\n', from);
        std::string line{text.substr(from, end == std::string_view::npos ? text.size() - from : end - from)};
        from = end == std::string_view::npos ? text.size() : end + 1;
        if (line.size() > 512) continue;
        const auto frame_at = line.find("EDEN_GAME_FRAME ");
        if (frame_at != std::string::npos && frames.size() < 120) {
            unsigned long long frame_count = 0, total = 0;
            double seconds = 0, fps = 0, worst = 0;
            if (std::sscanf(line.c_str() + frame_at,
                    "EDEN_GAME_FRAME frames=%llu seconds=%lf fps=%lf worst_ms=%lf total=%llu",
                    &frame_count, &seconds, &fps, &worst, &total) == 5 &&
                frame_count <= 999999999999ULL && total <= 999999999999ULL &&
                FiniteBound(seconds) && FiniteBound(fps) && FiniteBound(worst)) {
                frames.push_back(Json::array({frame_count, seconds, fps, worst, total}));
            }
            continue;
        }
        const auto wait_at = line.find("EDEN_VULKAN_LOADING_WAIT ");
        if (wait_at != std::string::npos && waits.size() < 8) {
            unsigned stage = 0, idle = 0, presents = 0, reset = 0;
            unsigned long long submitted = 0, completed = 0, delta = 0;
            if (std::sscanf(line.c_str() + wait_at,
                    "EDEN_VULKAN_LOADING_WAIT stage=%us idle=%u loading_presents=%u guest_frame_handoff=0 gpu_submit_sample=%llu gpu_worker_completed_floor64=%llu gpu_worker_delta_floor64=%llu gpu_worker_counter_reset=%u",
                    &stage, &idle, &presents, &submitted, &completed, &delta, &reset) == 7 &&
                (stage == 10 || stage == 30) && idle <= 1 && reset <= 1 &&
                submitted <= 999999999999ULL && completed <= 999999999999ULL &&
                delta <= 999999999999ULL) {
                waits.push_back(Json::array({stage, idle, presents, submitted, completed, delta, reset}));
            }
        }
    }
    if (frames.empty() && waits.empty()) return {};
    return Json{{"schema", 1}, {"category", "advanced"}, {"source_sha", state.source_sha},
                {"frames", std::move(frames)}, {"loading_waits", std::move(waits)}};
}

std::optional<Pending> Envelope(Category category, Json report) {
    if (!report.is_object()) return std::nullopt;
    const auto identity = NewIdentity();
    if (!identity) return std::nullopt;
    Json envelope{{"report_id", identity->first}, {"erase_token", identity->second},
                  {"report", std::move(report)}};
    const std::string body = envelope.dump();
    if (body.empty() || body.size() > DiagnosticsSharing::kMaxReportBytes) return std::nullopt;
    return Pending{category, identity->first, body};
}
std::optional<std::string> EnvelopeToken(std::string_view body) {
    try {
        const Json value = Json::parse(body);
        if (!value.is_object() || !value.contains("erase_token") ||
            !value["erase_token"].is_string()) return std::nullopt;
        const std::string token = value["erase_token"].get<std::string>();
        return HexLower(token, 64) ? std::optional<std::string>{token} : std::nullopt;
    } catch (...) {
        return std::nullopt;
    }
}

void PrunePendingStore() {
    state.pending.erase(std::remove_if(state.pending.begin(), state.pending.end(), [](const Pending& item) {
        return !state.queue.Contains(item.id);
    }), state.pending.end());
}
std::string StatePath() { return Eden::ConfigFile("diagnostics-sharing-state.json"); }
void SaveState() {
    if (!state.initialized) return;
    Json pending = Json::array();
    for (const auto& item : state.pending)
        pending.push_back({{"category", CategoryName(item.category)}, {"id", item.id},
                           {"envelope", item.envelope}});
    Json receipts = Json::array();
    for (const auto& item : state.receipts)
        receipts.push_back({{"category", CategoryName(item.category)}, {"id", item.id},
                            {"token", item.token}, {"erase_pending", item.erase_pending}});
    Json root{{"schema", 1}, {"pending", std::move(pending)}, {"receipts", std::move(receipts)}};
    const std::string body = root.dump();
    if (body.size() > kMaxStateBytes) return;
    const std::string path = StatePath();
    const std::string staged = path + ".new";
    {
        std::ofstream file(staged, std::ios::binary | std::ios::trunc);
        if (!file) return;
        file.write(body.data(), static_cast<std::streamsize>(body.size()));
        if (!file) {
            file.close();
            std::remove(staged.c_str());
            return;
        }
    }
    (void)::chmod(staged.c_str(), 0600);
    if (std::rename(staged.c_str(), path.c_str()) != 0) std::remove(staged.c_str());
}
bool EnvelopeLooksSafe(const Pending& pending) {
    if (!ValidId(pending.id) || pending.envelope.empty() ||
        pending.envelope.size() > DiagnosticsSharing::kMaxReportBytes) return false;
    try {
        const Json env = Json::parse(pending.envelope);
        if (!env.is_object() || env.size() != 3 || !env.contains("report_id") ||
            !env.contains("erase_token") || !env.contains("report") ||
            env["report_id"] != pending.id || !env["erase_token"].is_string() ||
            !HexLower(env["erase_token"].get_ref<const std::string&>(), 64) ||
            !env["report"].is_object()) return false;
        const auto& report = env["report"];
        return report.value("schema", 0) == 1 &&
               report.value("category", std::string{}) == CategoryName(pending.category) &&
               SourceSha(report.value("source_sha", std::string{}));
    } catch (...) {
        return false;
    }
}
void LoadState() {
    const std::string raw = ReadSmallFile(StatePath(), kMaxStateBytes);
    if (raw.empty()) return;
    try {
        const Json root = Json::parse(raw);
        if (!root.is_object() || root.value("schema", 0) != 1) return;
        if (root.contains("pending") && root["pending"].is_array()) {
            for (const auto& row : root["pending"]) {
                if (state.pending.size() >= DiagnosticsSharing::kMaxQueuedReports ||
                    !row.is_object()) break;
                const auto category = ParseCategory(row.value("category", std::string{}));
                Pending item{category.value_or(Category::Standard),
                             row.value("id", std::string{}),
                             row.value("envelope", std::string{})};
                const bool allowed = category &&
                    (*category == Category::Standard ? state.standard : state.advanced);
                if (!allowed || !EnvelopeLooksSafe(item)) continue;
                item.category = *category;
                if (state.queue.Enqueue({item.category, state.queue.Epoch(item.category),
                                         item.id, item.envelope}))
                    state.pending.push_back(std::move(item));
            }
        }
        if (root.contains("receipts") && root["receipts"].is_array()) {
            for (const auto& row : root["receipts"]) {
                if (state.receipts.size() >= kMaxReceipts || !row.is_object()) break;
                const auto category = ParseCategory(row.value("category", std::string{}));
                Receipt receipt{category.value_or(Category::Standard),
                                row.value("id", std::string{}),
                                row.value("token", std::string{}),
                                row.value("erase_pending", false)};
                if (!category || !ValidId(receipt.id) || !HexLower(receipt.token, 64)) continue;
                receipt.category = *category;
                if ((*category == Category::Standard && !state.standard) ||
                    (*category == Category::Advanced && !state.advanced))
                    receipt.erase_pending = true;
                state.receipts.push_back(std::move(receipt));
            }
        }
    } catch (...) {
        return;
    }
}
bool QueueProjected(Category category, const Json& report) {
    const auto item = Envelope(category, report);
    if (!item) return false;
    const auto epoch = state.queue.Epoch(category);
    if (!epoch || !state.queue.Enqueue({category, epoch, item->id, item->envelope})) return false;
    state.pending.push_back(*item);
    PrunePendingStore();
    SaveState();
    return true;
}
void RemovePending(std::string_view id) {
    state.pending.erase(std::remove_if(state.pending.begin(), state.pending.end(),
        [&](const Pending& item) { return item.id == id; }), state.pending.end());
}
void AddReceipt(Category category, std::string id, std::string token) {
    const auto found = std::find_if(state.receipts.begin(), state.receipts.end(),
        [&](const Receipt& item) { return item.id == id; });
    if (found != state.receipts.end()) return;
    if (state.receipts.size() >= kMaxReceipts)
        state.receipts.erase(state.receipts.begin());
    state.receipts.push_back({category, std::move(id), std::move(token), false});
}

TransferResult SendReport(Queue::Work work) {
    TransferResult out{TransferResult::Kind::Report, work.ticket, work.report->id,
                       Queue::Result::Retry, {}};
    if (work.cancelled->load(std::memory_order_acquire)) return out;
    const auto response = Common::Net::PostJson(
        std::string{kCollector}, std::string{kReportsPath}, work.report->envelope, 1);
    if (!response) return out;
    try {
        const Json body = Json::parse(response->body);
        out.server_result = body.value("result", std::string{});
    } catch (...) {
        out.server_result.clear();
    }
    if ((response->status == 200 || response->status == 201) &&
        (out.server_result == "accepted" || out.server_result == "duplicate" ||
         out.server_result == "erased")) {
        out.result = Queue::Result::Delivered;
    } else if (response->status == 429 || response->status >= 500) {
        out.result = Queue::Result::Retry;
    } else {
        out.result = Queue::Result::Rejected;
    }
    return out;
}
TransferResult SendErase(const Receipt& receipt) {
    TransferResult out{TransferResult::Kind::Erase, 0, receipt.id, Queue::Result::Retry, {}};
    const Json body{{"report_id", receipt.id}, {"erase_token", receipt.token}};
    const auto response = Common::Net::PostJson(
        std::string{kCollector}, std::string{kErasePath}, body.dump(), 1);
    if (!response) return out;
    try {
        out.server_result = Json::parse(response->body).value("result", std::string{});
    } catch (...) {
        out.server_result.clear();
    }
    if (response->status == 200 && out.server_result == "processed")
        out.result = Queue::Result::Delivered;
    else if (response->status == 429 || response->status >= 500)
        out.result = Queue::Result::Retry;
    else
        out.result = Queue::Result::Rejected;
    return out;
}
bool TransferReady() {
    return state.transfer &&
           state.transfer->completed.load(std::memory_order_acquire);
}
template <typename Task>
void StartTransfer(Task task) {
    auto transfer = std::make_shared<TransferState>();
    state.transfer = transfer;
    std::thread([transfer, task = std::move(task)]() mutable {
        transfer->result = task();
        transfer->completed.store(true, std::memory_order_release);
    }).detach();
}
void FinishTransfer() {
    if (!TransferReady()) return;
    const TransferResult result = std::move(state.transfer->result);
    state.transfer.reset();
    if (result.kind == TransferResult::Kind::Report) {
        auto pending = std::find_if(state.pending.begin(), state.pending.end(),
            [&](const Pending& item) { return item.id == result.id; });
        if (result.result == Queue::Result::Delivered && pending != state.pending.end() &&
            result.server_result != "erased") {
            if (const auto token = EnvelopeToken(pending->envelope))
                AddReceipt(pending->category, pending->id, *token);
        }
        (void)state.queue.Finish(result.ticket, result.result);
        if (result.result != Queue::Result::Retry) RemovePending(result.id);
        PrunePendingStore();
    } else {
        if (result.result == Queue::Result::Delivered) {
            state.receipts.erase(std::remove_if(state.receipts.begin(), state.receipts.end(),
                [&](const Receipt& item) { return item.id == result.id; }), state.receipts.end());
        }
        state.erase_in_flight.clear();
    }
    SaveState();
}

} // namespace

void Initialize(std::string_view source_sha) {
    if (state.initialized) return;
    state.source_sha.assign(source_sha);
    if (!SourceSha(state.source_sha)) return;
    state.initialized = true;
    const auto prefs = Eden::LoadPreferences();
    state.standard = prefs.share_standard_logs;
    state.advanced = prefs.share_advanced_logs;
    state.queue.Conditions(true, true);
    state.queue.SetConsent({state.standard, state.advanced});
    state.last_activity = Now();
    state.game_log_offset = FileSize(Eden::LogFile("stderr.log"));
    LoadState();
    SaveState();
}
bool Available() noexcept {
    return state.initialized;
}

void SetConsent(bool standard, bool advanced) {
    if (!state.initialized) return;
    const bool revoke_standard = state.standard && !standard;
    const bool revoke_advanced = state.advanced && !advanced;
    state.standard = standard;
    state.advanced = advanced;
    state.queue.SetConsent({standard, advanced});
    state.pending.erase(std::remove_if(state.pending.begin(), state.pending.end(),
        [&](const Pending& item) {
            return item.category == Category::Standard ? !standard : !advanced;
        }), state.pending.end());
    for (auto& receipt : state.receipts)
        if ((revoke_standard && receipt.category == Category::Standard) ||
            (revoke_advanced && receipt.category == Category::Advanced))
            receipt.erase_pending = true;
    SaveState();
}

void EnterLauncher(std::string_view launch_error) {
    if (!state.initialized) return;
    const auto now = Now();
    state.idle = true;
    state.last_activity = now;
    state.erase_attempts = 0;
    state.queue.Conditions(true, true);
    state.queue.SetPhase(Phase::LauncherIdle, now);

    if (state.standard && launch_error.starts_with(Eden::Crash::kNotice)) {
        const std::string path{launch_error.substr(Eden::Crash::kNotice.size())};
        const std::string root = Eden::LogsDir() + "/";
        if (path.starts_with(root) && path.find('/', root.size()) == std::string::npos) {
            const std::string crash = ReadSmallFile(path, kMaxReadBytes);
            if (!crash.empty()) (void)QueueProjected(Category::Standard, StandardReport(crash));
        }
    }
    if (state.game_pending && state.advanced) {
        const std::string log = ReadRange(Eden::LogFile("stderr.log"), state.game_log_offset);
        if (!log.empty()) (void)QueueProjected(Category::Advanced, AdvancedReport(log));
    }
    state.game_pending = false;
    SaveState();
}
void Activity() noexcept {
    if (!state.initialized || !state.idle) return;
    state.last_activity = Now();
    state.queue.Activity(state.last_activity);
}
void Poll() {
    if (!state.initialized) return;
    FinishTransfer();
    if (state.transfer || !state.idle) return;
    const auto now = Now();
    if (now < state.last_activity || now - state.last_activity < DiagnosticsSharing::kIdleSeconds)
        return;

    // Privacy erasure takes precedence over sending another report.
    if (state.erase_attempts < DiagnosticsSharing::kMaxAttemptsPerVisit &&
        (!state.erase_last_attempt ||
         now - state.erase_last_attempt >= DiagnosticsSharing::kMinIntervalSeconds)) {
        const auto erase = std::find_if(state.receipts.begin(), state.receipts.end(),
            [](const Receipt& item) { return item.erase_pending; });
        if (erase != state.receipts.end()) {
            state.erase_in_flight = erase->id;
            state.erase_last_attempt = now;
            ++state.erase_attempts;
            const Receipt copy = *erase;
            StartTransfer([copy] { return SendErase(copy); });
            return;
        }
    }
    if (const auto work = state.queue.TryStart(now)) {
        StartTransfer([work] { return SendReport(work); });
    }
}
void GameStarting() noexcept {
    if (!state.initialized) return;
    state.idle = false;
    state.queue.SetPhase(Phase::GameStarting, Now());
    state.game_log_offset = FileSize(Eden::LogFile("stderr.log"));
    state.game_pending = true;
}
void Shutdown() noexcept {
    if (!state.initialized) return;
    state.idle = false;
    state.queue.SetPhase(Phase::Stopping, Now());
    SaveState();
}

} // namespace Eden::DiagnosticsClient
