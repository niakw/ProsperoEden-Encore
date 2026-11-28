#!/usr/bin/env python3
"""Check maintained translation-unit parity against pinned sources (host-only)."""
from pathlib import Path
import hashlib

root = Path(__file__).resolve().parents[1]
base = root / "vendor/sources/eden/src"
active = root / "vendor/encore-active/eden/src"
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
assert loader_text.count("FileSys::CreateRomFS(own_romfs, nullptr)") == 1
assert loader_text.count("FileSys::CreateRomFS(std::move(layered), nullptr)") == 1
assert loader_text.count("FileSys::LayeredVfsDirectory::MakeLayeredDirectory(") == 1
assert "struct Candidate" in loader_text and "candidate.depth >= 5" in loader_text
assert "cursor == game_root" in loader_text
loader_git_blob = hashlib.sha1(
    b"blob " + str(len(loader_data)).encode() + b"\0" + loader_data
).hexdigest()
assert loader_git_blob == "bb99dccad28234f246395d4d010211a41d928763", (
    "maintained loader changed: repeat owner review", loader_git_blob
)

logging = (base / "common/logging.cpp").read_text()
maintained_logging = (active / "common/logging.cpp").read_text()

# The frozen vendor source remains the unmodified Eden baseline.
old_flush = """            if (write_limit_exceeded)
                enabled = false;
            file->Flush();"""
assert logging.count(old_flush) == 1
assert "eden_native_detailed_logging" not in logging
assert "void RotatePs5() noexcept" not in logging

# The canonical owner keeps the later host flush-throttling optimization.
for needle in (
    "#include <atomic>",
    "#include <chrono>",
    "flush_now - error_flushed_ms.load(std::memory_order_relaxed) >= 100",
    "error_flushed_ms.store(flush_now, std::memory_order_relaxed);",
    'std::atomic<long long> error_flushed_ms{-1000};',
):
    assert maintained_logging.count(needle) == 1, needle

# PS5 detailed logging is opt-in and bounded. Preserve both the first segment
# and rolling recent tail while avoiding formatting work when logging is off.
for needle in (
    'extern "C" bool eden_native_detailed_logging() noexcept;',
    'extern "C" unsigned eden_native_logging_generation() noexcept;',
    'if (!eden_native_detailed_logging()) return;',
    'const auto generation = eden_native_logging_generation();',
    'constexpr auto write_limit = 8_MiB;',
    'void RotatePs5() noexcept {',
    'first_filename += ".first.txt";',
    '"[Eden Encore] log tail rotated; storage remains bounded\\n"',
    'error_events == 1 || error_events % 64 == 0',
):
    assert needle in maintained_logging, needle
assert maintained_logging.count("void RotatePs5() noexcept {") == 1
assert maintained_logging.count("eden_native_logging_generation()") >= 2

# Native console-only output retains its quiet-backend fast path in addition
# to the detailed-logging gate; these are complementary, not alternatives.
log_entry = "void FmtLogMessageImpl(Class log_class, Level log_level, const char* filename, unsigned int line_num, const char* function, fmt::string_view format, const fmt::format_args& args) {"
fmt = maintained_logging[maintained_logging.index(log_entry):]
assert fmt.index("#ifdef PS5_NATIVE") < fmt.index("#ifdef __OPENORBIS__")
assert 'if (!eden_native_detailed_logging()) return;' in fmt
assert '!logging_instance->color_console_backend.enabled.load(std::memory_order_relaxed)' in fmt

assert 'list(APPEND core_sources "${EDEN_MAINTAINED_CODE_LOADER}")' in cmake
assert 'list(APPEND eden_common_sources "${EDEN_MAINTAINED_LOGGING}")' in cmake
assert 'write_derived("${PORT_BUILD_DIR}/deconstructed_rom_directory.cpp"' not in cmake
assert 'write_derived("${PORT_BUILD_DIR}/logging.cpp"' not in cmake
assert cmake.count("EDEN_MAINTAINED_CODE_LOADER") >= 3
assert cmake.count("EDEN_MAINTAINED_LOGGING") >= 3
print("MAINTAINED_LOADER_LOGGING_PARITY_PASS")
