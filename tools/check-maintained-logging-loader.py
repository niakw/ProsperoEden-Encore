#!/usr/bin/env python3
"""Check maintained translation-unit parity against pinned sources (host-only)."""
from pathlib import Path
import hashlib

root = Path(__file__).resolve().parents[1]
base = root / "vendor/sources/eden/src"
active = root / "vendor/encore-active/eden-core/src"
cmake = (root / "headless/CMakeLists.txt").read_text()

loader = (base / "core/loader/deconstructed_rom_directory.cpp").read_text()
old = "? ::Settings::values.rng_seed.GetValue() : Common::Random::Random64(0)) << 12) & 0xfff000;"
new = "? ::Settings::values.rng_seed.GetValue() : Common::Random::Random64(0)) << 14) & 0xffc000;"
assert loader.count(old) == 1
# The maintained loader now contains a reviewed native RNG policy change
# PLUS the extracted ExeFS/RomFS bridge and versioned update-file overlays.
# Keep immutable-source provenance and verify the entire audited new Git blob:
# never weaken this to checking only a few loosely selected snippets.
loader_path = active / "core/loader/deconstructed_rom_directory.cpp"
loader_data = loader_path.read_bytes()
loader_text = loader_data.decode("utf-8")
assert loader_text.count(new) == 1 and old not in loader_text
assert loader_text.count("FileSys::CreateRomFS(std::move(extracted_romfs), nullptr)") == 1
assert loader_text.count("FileSys::LayeredVfsDirectory::MakeLayeredDirectory(") >= 2
assert "UpdateCandidate" in loader_text and "candidate.depth >= 5" in loader_text
assert "cursor == game_root" in loader_text
loader_git_blob = hashlib.sha1(
    b"blob " + str(len(loader_data)).encode() + b"\0" + loader_data
).hexdigest()
assert loader_git_blob == "6b2f529fb09083fab4abd47b2605d16f42d93300", (
    "maintained loader changed: repeat owner review", loader_git_blob
)

logging = (base / "common/logging.cpp").read_text()
old_flush = """            if (write_limit_exceeded)
                enabled = false;
            file->Flush();"""
new_flush = """            if (write_limit_exceeded)
                enabled = false;
            const auto flush_now = std::chrono::duration_cast<std::chrono::milliseconds>(
                std::chrono::steady_clock::now().time_since_epoch()).count();
            if (write_limit_exceeded ||
                flush_now - error_flushed_ms.load(std::memory_order_relaxed) >= 100) {
                error_flushed_ms.store(flush_now, std::memory_order_relaxed);
                file->Flush();
            }"""
field = "    std::optional<FS::IOFile> file;"
assert logging.count(old_flush) == logging.count(field) == 1
expected = ("#include <atomic>\n#include <chrono>\n" +
            logging.replace(old_flush, new_flush).replace(
                field, field + "\n    std::atomic<long long> error_flushed_ms{-1000};"))
# Native output is console-only; preserve the exact quiet-backend fast path.
log_entry = "void FmtLogMessageImpl(Class log_class, Level log_level, const char* filename, unsigned int line_num, const char* function, fmt::string_view format, const fmt::format_args& args) {"
native_guard = "\n#ifdef __OPENORBIS__\n    // Native builds have no file/debugger/logcat backend. When the only\n    // console backend is OFF, do not format messages that nobody can read.\n    // Toggling it back on preserves filtering and the existing log format.\n    if (logging_instance &&\n        !logging_instance->color_console_backend.enabled.load(std::memory_order_relaxed))\n        return;\n#endif"
assert expected.count(log_entry) == 1
expected = expected.replace(log_entry, log_entry + native_guard)
assert (active / "common/logging.cpp").read_text() == expected

assert 'list(APPEND core_sources "${EDEN_MAINTAINED_CODE_LOADER}")' in cmake
assert 'list(APPEND eden_common_sources "${EDEN_MAINTAINED_LOGGING}")' in cmake
assert 'write_derived("${PORT_BUILD_DIR}/deconstructed_rom_directory.cpp"' not in cmake
assert 'write_derived("${PORT_BUILD_DIR}/logging.cpp"' not in cmake
assert cmake.count("EDEN_MAINTAINED_CODE_LOADER") >= 3
assert cmake.count("EDEN_MAINTAINED_LOGGING") >= 3
print("MAINTAINED_LOADER_LOGGING_PARITY_PASS")
