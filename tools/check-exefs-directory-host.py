#!/usr/bin/env python3
"""Host-proof the selected ExeFS game folder and saved ROM path contract.

Compile the *real* game_files.h and actual ValidRomFilename function in a
standalone host fixture, with and without optimisation and under UBSan.
This is not PS5 load/runtime qualification.
"""
from pathlib import Path
import shutil
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
header = (root / "headless/game_files.h").read_text()
settings = (root / "headless/settings_store.h").read_text()
library = (root / "headless/prosperoeden/eden_services.cpp").read_text()
main = (root / "headless/main.cpp").read_text()
start_key = "inline bool ValidRomFilename(std::string_view name) {"
assert settings.count(start_key) == 1
start = settings.index(start_key)
end = settings.index("\n}\n", start) + 2
actual_validator = settings[start:end]
assert "IsDeconstructedGameSelection(name)" in actual_validator
assert "c == '/' && !exefs" in actual_validator
assert 'FindDeconstructedGameMain(entry.path())' in library
assert 'if (!Eden::ValidRomFilename(file)) continue;' in library
assert 'game.name = CleanTitle(entry_name);' in library
assert 'game.format = format;' in library
assert 'CountExeFsFolders(roms_path)' in library
directory_counter = library.split("int CountExeFsFolders(", 1)[1].split("unsigned int HashPath(", 1)[0]
assert "ListEntries(directory, true, ok)" in directory_counter
assert 'IsSafeDeconstructedGamePath(selected_root, selected_relative)' in main
assert 'Eden::FindDeconstructedGameMain(entry.path())' in main
assert 'selected_path.filename() == "main"' in main
assert 'IsSafeDeconstructedGamePath(selected_root, selected_relative)' in main
assert "symlink_status(folder / name, error)" in header

source = r"""
#include <cassert>
#include <cstdio>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <string>
#include <string_view>
#include <unistd.h>
#include "game_files.h"
namespace Eden {
VALIDATOR
}
int main() {
    namespace fs = std::filesystem;
    char format[] = "/tmp/eden-exefs-XXXXXX";
    char* tmp = ::mkdtemp(format);
    assert(tmp != nullptr);
    fs::path root{tmp};
    const fs::path rom = root / "My Game";
    fs::create_directories(rom);
    std::ofstream(rom / "main") << "code";
    std::ofstream(rom / "main.npdm") << "metadata";
    assert(Eden::IsDeconstructedGameDirectory(rom));
    assert(Eden::FindDeconstructedGameMain(rom) == "main");
    assert(Eden::IsSafeDeconstructedGamePath(root, "My Game/main"));
    assert(Eden::IsDeconstructedGameSelection("My Game/main"));
    assert(Eden::ValidRomFilename("My Game/main"));
    assert(Eden::ValidRomFilename("game.NSZ"));
    assert(Eden::ValidRomFilename("game.NAX"));
    assert(!Eden::ValidRomFilename("../main"));
    assert(!Eden::ValidRomFilename("My Game/../main"));
    assert(!Eden::ValidRomFilename("My Game/sub/main"));
    assert(Eden::ValidRomFilename("My Game/base/exefs/main"));
    assert(Eden::ValidRomFilename("My Game/base/extra/sub/exefs/main"));
    assert(!Eden::ValidRomFilename("My Game/updates/458752/exefs/main"));
    assert(!Eden::ValidRomFilename("updates/458752/exefs/main"));
    assert(!Eden::ValidRomFilename("dlc/exefs/main"));
    assert(!Eden::ValidRomFilename("My Game/dlc/0/exefs/main"));
    assert(!Eden::ValidRomFilename("My Game/../base/exefs/main"));
    assert(!Eden::ValidRomFilename("/main"));
    assert(!Eden::ValidRomFilename("main"));
    assert(!Eden::ValidRomFilename("My Game\\main"));
    assert(!Eden::ValidRomFilename("game.zst"));
    assert(!Eden::ValidRomFilename("folder/main/extra"));
    fs::remove(rom / "main.npdm");
    assert(!Eden::IsDeconstructedGameDirectory(rom));
    fs::create_symlink(rom / "main", rom / "main.npdm");
    assert(!Eden::IsDeconstructedGameDirectory(rom));
    fs::remove(rom / "main.npdm");
    std::ofstream(rom / "main.npdm") << "metadata";
    fs::rename(rom / "main", rom / "real_main");
    fs::create_symlink(rom / "real_main", rom / "main");
    assert(!Eden::IsDeconstructedGameDirectory(rom));
    fs::remove(rom / "main");
    fs::rename(rom / "real_main", rom / "main");
    assert(Eden::IsDeconstructedGameDirectory(rom));
    const fs::path linked = root / "symlinked-game";
    fs::create_directory_symlink(rom, linked);
    assert(!Eden::IsDeconstructedGameDirectory(linked));
    const fs::path nested = root / "Nested Game";
    fs::create_directories(nested / "base" / "exefs");
    fs::create_directories(nested / "base" / "romfs");
    fs::create_directories(nested / "updates" / "458752" / "exefs");
    fs::create_directories(nested / "dlc" / "040074a01bf13001" / "0" / "romfs");
    std::ofstream(nested / "base" / "exefs" / "main") << "code";
    std::ofstream(nested / "base" / "exefs" / "main.npdm") << "metadata";
    std::ofstream(nested / "updates" / "458752" / "exefs" / "main") << "patch";
    std::ofstream(nested / "updates" / "458752" / "exefs" / "main.npdm") << "patchmeta";
    assert(Eden::FindDeconstructedGameMain(nested) == "base/exefs/main");
    assert(Eden::IsSafeDeconstructedGamePath(root, "Nested Game/base/exefs/main"));
    // Top-level content stores cannot surface as independent library games.
    const fs::path external_updates = root / "updates" / "458752" / "exefs";
    fs::create_directories(external_updates);
    std::ofstream(external_updates / "main") << "update";
    std::ofstream(external_updates / "main.npdm") << "meta";
    assert(Eden::FindDeconstructedGameMain(root / "updates").empty());
    const fs::path external_dlc = root / "dlc" / "abc" / "exefs";
    fs::create_directories(external_dlc);
    std::ofstream(external_dlc / "main") << "addon";
    std::ofstream(external_dlc / "main.npdm") << "meta";
    assert(Eden::FindDeconstructedGameMain(root / "dlc").empty());
    const fs::path deeper = root / "Deep Game";
    fs::create_directories(deeper / "base" / "some" / "path" / "exefs");
    std::ofstream(deeper / "base" / "some" / "path" / "exefs" / "main") << "code";
    std::ofstream(deeper / "base" / "some" / "path" / "exefs" / "main.npdm") << "meta";
    assert(Eden::FindDeconstructedGameMain(deeper) == "base/some/path/exefs/main");
    const fs::path bad = root / "Unsafe Game";
    fs::create_directory(bad);
    fs::create_directory_symlink(nested / "base", bad / "base");
    assert(Eden::FindDeconstructedGameMain(bad).empty());
    assert(!Eden::IsSafeDeconstructedGamePath(root, "Unsafe Game/base/exefs/main"));
    fs::remove_all(root);
    std::puts("EXEFS_DIRECTORY_AND_SELECTION_PASS");
}
""".replace("VALIDATOR", actual_validator)

compilers = [exe for exe in (shutil.which("clang++"), shutil.which("g++"))
             if exe]
assert compilers, "C++20 host compiler required"
with tempfile.TemporaryDirectory(prefix="encore-exefs-host-") as temp:
    cpp = Path(temp) / "test.cpp"
    cpp.write_text(source)
    for compiler in dict.fromkeys(compilers):
        for opt in ("-O0", "-O2"):
            exe = Path(temp) / (Path(compiler).name + opt)
            built = subprocess.run(
                [compiler, "-std=c++20", opt, "-Wall", "-Wextra", "-Werror",
                 "-fsanitize=undefined", "-fno-sanitize-recover=all",
                 "-I", str(root / "headless"), str(cpp), "-o", str(exe)],
                capture_output=True, text=True, timeout=60
            )
            assert built.returncode == 0, (compiler, opt, built.stderr[-4000:])
            check = subprocess.run([str(exe)], capture_output=True, text=True, timeout=20)
            assert check.returncode == 0 and "EXEFS_DIRECTORY_AND_SELECTION_PASS" in check.stdout, (
                compiler, opt, check.stdout, check.stderr[-4000:]
            )
            print("EXEFS_REAL_SOURCE_HOST_PASS", Path(compiler).name, opt)
