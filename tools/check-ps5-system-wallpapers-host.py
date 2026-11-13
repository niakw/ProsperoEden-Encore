#!/usr/bin/env python3
"""Check the selected native PS5 screenshot wallpaper source contract.

Compiles the actual opaque capture-token routine on host and checks the
bounded, read-only PS5 directory scan in source. Not a PS5 mount/ACL proof.
"""
from pathlib import Path
import shutil
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
source = (root / "headless/prosperoeden/eden_services.cpp").read_text()
settings = (root / "headless/prosperoeden/pe/ui/settings.cpp").read_text()
header = (root / "headless/prosperoeden/eden_services.h").read_text()
begin = source.index("std::string CaptureWallpaperSelection(")
end = source.index("std::vector<SystemWallpaper> SystemCaptureWallpapers()", begin)
token = source[begin:end]
scan = source[end:source.index("#endif\n\nstd::string LocalDay()",end)]
listing = source[source.index("std::vector<std::string> EdenServices::wallpapers()"):source.index("namespace {\nstruct DailyOnlineCandidate", source.index("std::vector<std::string> EdenServices::wallpapers()"))]
assert "/user/av_contents/photo/NPXS40087" in scan
assert "sceUserServiceGetForegroundUser(&foreground)" in scan
assert "Eden::ReadNativeDirectory(current.folder, read_error)" in scan
assert "::lstat(entry.path().c_str(), &native)" in scan
assert "S_ISLNK(native.st_mode)" in scan
assert "kMaxDirs = 1024, kMaxEntries = 32768" in scan
assert "kMaxDepth = 8" in scan
assert 'ext != ".jpg" && ext != ".jpeg" && ext != ".png"' in scan
assert 'const bool is_jxr = ext == ".jxr";' in scan
assert 'if (is_jxr) ++hdr_jxr;' in scan
assert 'const auto max_bytes = is_jxr ? (48ll << 20) : (12ll << 20);' in scan
assert 'SelectedJxrWebp(' not in scan  # zero decode during enumeration
assert 'encore_jxr_to_webp(' in source
assert 'if (!local.empty()) {' in listing and 'return SelectedJxrWebp(local);' in listing
assert 'SelectedJxrWebp(checked)' in listing
assert source.count('encore_jxr_to_webp(') == 1
assert 'std::sort(names.begin(), names.end());' in listing
assert listing.index('std::sort(names.begin(), names.end());') < listing.index('SystemCaptureWallpapers()')
assert 'std::sort(names.begin(), names.end());' not in listing[listing.index('SystemCaptureWallpapers()'):]
assert 'if (ext == ".jxr")' in scan and '++hdr_jxr;' in scan
assert '++ignored_size;' in scan and '++unreadable_dirs;' in scan
assert 'EDEN_WALLPAPER_SCAN dirs=%zu entries=%zu accepted=%zu jxr=%zu' in scan
assert 'size_rejected=%zu format_rejected=%zu read_errors=%zu capped=%d elapsed_ms=%lld' in scan
assert "found.push_back(std::move(item))" in scan
assert "SystemCaptureWallpapers()" in listing
assert "for (const auto& capture : captures)" in listing
assert "names.push_back(capture.selection)" in listing
assert "i < 64u" not in listing
assert "names.size() - captures.size()" in listing
assert "CheckedWallpaper(capture.photo.parent_path()," in listing
assert 'file.starts_with("PS5_") && ValidWallpaperName(file)' in listing
assert "std::filesystem::path(Eden::UserDir()) / \"wallpapers\"" in listing
assert "App wallpapers: /data/prosperoeden/user/wallpapers." in settings
assert "wallpaper_path(const std::string& file)" in header

compiler = shutil.which("clang++") or shutil.which("g++")
assert compiler, "C++20 compiler required"
harness = """#include <algorithm>
#include <cassert>
#include <cctype>
#include <cstdint>
#include <cstdio>
#include <filesystem>
#include <string>
""" + token + """
int main() {
    const std::string a = CaptureWallpaperSelection(
        "/user/av_contents/photo/NPXS40087/PPSA12345/306/20261113_123456.JPG");
    const std::string b = CaptureWallpaperSelection(
        "/user/av_contents/photo/NPXS40087/PPSA99999/306/20261113_123456.JPG");
    assert(a != b);
    assert(a.starts_with("PS5_"));
    assert(a.ends_with(".jpg"));
    assert(a.size() < 120 && a.find('/') == std::string::npos);
    assert(a == CaptureWallpaperSelection(
        "/user/av_contents/photo/NPXS40087/PPSA12345/306/20261113_123456.JPG"));
    const std::string c = CaptureWallpaperSelection(
        "/user/av_contents/photo/NPXS40087/PPSA12345/306/very!!!long file.png");
    assert(c.ends_with(".png") && c.find('!') == std::string::npos);
}
"""
with tempfile.TemporaryDirectory(prefix="ps5-wallpapers-") as directory:
    cpp = Path(directory) / "test.cpp"
    exe = Path(directory) / "test"
    cpp.write_text(harness, encoding="utf-8")
    subprocess.run([compiler, "-std=c++20", "-Wall", "-Wextra", "-Werror",
                    str(cpp), "-o", str(exe)], check=True, timeout=30)
    subprocess.run([str(exe)], check=True, timeout=15)

print("PS5_SYSTEM_WALLPAPERS_HOST_PASS read_only=1 opaque_tokens=1 local_first=1 system_jxr_list_only=1 selected_only_conversion=1")
