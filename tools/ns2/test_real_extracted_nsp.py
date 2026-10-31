#!/usr/bin/env python3
"""Compile the maintained Eden PFS0 constructor against the public NSP fixture.

No PS5 or commercial title data. Real PartitionFilesystem C++ constructor and
IsDirectoryExeFS are extracted byte-for-byte from the pinned vendor; only VFS
objects and peripheral APIs are substituted with host-memory mock classes.
The full NSP constructor, Core::System and KProcess are NOT executed here.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "vendor/sources/eden/src/core"
PARTITION = SRC / "file_sys/partition_filesystem.cpp"
CONTENT = SRC / "file_sys/content_archive.h"
NSP = SRC / "file_sys/submission_package.cpp"
NSP_LOADER = SRC / "loader/nsp.cpp"


def slice_between(source: str, begin: str, end: str) -> str:
    if source.count(begin) != 1:
        raise AssertionError(f"maintained source anchor changed: {begin}")
    suffix = source.split(begin, 1)[1]
    if suffix.count(end) < 1:
        raise AssertionError(f"maintained source owner changed: {end}")
    return begin + suffix.split(end, 1)[0]


def extract_maintained() -> tuple[str, str, str]:
    partition = PARTITION.read_text()
    archive = CONTENT.read_text()
    nsp = NSP.read_text()
    loader = NSP_LOADER.read_text()
    magic = slice_between(
        partition, "bool PartitionFilesystem::Header::HasValidMagicValue() const {",
        "\nPartitionFilesystem::PartitionFilesystem(")
    constructor = slice_between(
        partition, "PartitionFilesystem::PartitionFilesystem(VirtualFile file) {",
        "\nPartitionFilesystem::~PartitionFilesystem()")
    is_exefs = slice_between(
        archive, "inline bool IsDirectoryExeFS(const VirtualDir& pfs) {",
        "\ninline bool IsDirectoryLogoPartition")
    if not all(part in nsp for part in (
        "if (IsDirectoryExeFS(pfs)) {", "extracted = true;",
        "InitializeExeFSAndRomFS(files);", "exefs = pfs;")):
        raise AssertionError("Real NSP extracted-type route no longer confirmed")
    if not all(part in loader for part in (
        "nsp->IsExtractedType()", "GetExeFS()",
        "AppLoader_DeconstructedRomDirectory", "secondary_loader->Load(process, system)")):
        raise AssertionError("Real NSP loader no longer chains extracted ExeFS")
    return magic, constructor, is_exefs


HOST_PREFIX = r"""
#include <algorithm>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iostream>
#include <iterator>
#include <map>
#include <memory>
#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

using u8 = std::uint8_t;
using u16 = std::uint16_t;
using u32_le = std::uint32_t;
using u64_le = std::uint64_t;

namespace Common {
constexpr std::uint32_t MakeMagic(char a, char b, char c, char d) {
    return static_cast<std::uint32_t>(static_cast<unsigned char>(a)) |
        (static_cast<std::uint32_t>(static_cast<unsigned char>(b)) << 8) |
        (static_cast<std::uint32_t>(static_cast<unsigned char>(c)) << 16) |
        (static_cast<std::uint32_t>(static_cast<unsigned char>(d)) << 24);
}
}
namespace Loader {
enum class ResultStatus {
    Success, ErrorBadPFSHeader, ErrorIncorrectPFSFileSize
};
}

namespace FileSys {
class MemoryFile {
public:
    std::shared_ptr<const std::vector<u8>> storage;
    std::size_t offset, length;
    std::string name;
    MemoryFile(std::vector<u8> bytes, std::string label)
        : storage(std::make_shared<const std::vector<u8>>(std::move(bytes))),
          offset(0), length(storage->size()), name(std::move(label)) {}
    MemoryFile(std::shared_ptr<const std::vector<u8>> backing,
               std::size_t first, std::size_t size, std::string label)
        : storage(std::move(backing)), offset(first), length(size),
          name(std::move(label)) {}
    std::size_t GetSize() const { return length; }
    std::string GetName() const { return name; }
    std::size_t Read(u8* out, std::size_t n, std::size_t pos = 0) const {
        if (pos > length || offset > storage->size() ||
            pos > storage->size() - offset)
            return 0;
        const auto avail = std::min(length - pos, storage->size() - offset - pos);
        const auto count = std::min(n, avail);
        if (count) std::memcpy(out, storage->data() + offset + pos, count);
        return count;
    }
    template<class T>
    std::size_t ReadObject(T* out) const {
        return Read(reinterpret_cast<u8*>(out), sizeof(T));
    }
    std::vector<u8> ReadBytes(std::size_t n) const {
        std::vector<u8> result(n);
        result.resize(Read(result.data(), n));
        return result;
    }
};
using VirtualFile = std::shared_ptr<MemoryFile>;

class OffsetVfsFile final : public MemoryFile {
public:
    OffsetVfsFile(VirtualFile f, std::size_t size, std::size_t first,
                  std::string label)
        : MemoryFile(f->storage, f->offset + first, size, std::move(label)) {}
};

class PartitionFilesystem {
public:
    struct Header {
        u32_le magic{}, num_entries{}, strtab_size{}, reserved{};
        bool HasValidMagicValue() const;
    };
    static_assert(sizeof(Header) == 16);
#pragma pack(push, 1)
    struct FSEntry {
        u64_le offset{}, size{};
        u32_le strtab_offset{};
    };
    struct PFSEntry { FSEntry fs_entry; std::uint32_t reserved{}; };
    struct HFSEntry {
        FSEntry fs_entry;
        std::uint32_t hash_region_size{};
        std::uint8_t reserved[8]{};
        std::uint8_t hash[32]{};
    };
#pragma pack(pop)
    static_assert(sizeof(FSEntry) == 20);
    static_assert(sizeof(PFSEntry) == 24);
    static_assert(sizeof(HFSEntry) == 64);
    explicit PartitionFilesystem(VirtualFile file);
    Loader::ResultStatus GetStatus() const { return status; }
    std::vector<VirtualFile> GetFiles() const { return pfs_files; }
    VirtualFile GetFile(std::string_view name) const {
        for (const auto& f : pfs_files) if (f->GetName() == name) return f;
        return {};
    }
    Loader::ResultStatus status{};
    Header pfs_header{};
    bool is_hfs = false;
    std::size_t content_offset = 0;
    std::map<std::string, std::uint64_t> offsets, sizes;
    std::vector<VirtualFile> pfs_files;
};
using VirtualDir = std::shared_ptr<PartitionFilesystem>;
"""
HOST_MIDDLE = "}\nnamespace FileSys {\n"
HOST_TEST = r"""
}
static void Check(bool ok, const char* what) {
    if (!ok) throw std::runtime_error(what);
}
static std::vector<u8> ReadFile(const char* file) {
    std::ifstream f(file, std::ios::binary);
    Check(bool(f), "cannot open fixture");
    return {std::istreambuf_iterator<char>{f}, std::istreambuf_iterator<char>{}};
}
static void Validate(const char* nsp_name, const char* nso_name,
                     const char* npdm_name) {
    const auto bytes = ReadFile(nsp_name);
    const auto nso = ReadFile(nso_name);
    const auto npdm = ReadFile(npdm_name);
    auto pfs = std::make_shared<FileSys::PartitionFilesystem>(
        std::make_shared<FileSys::MemoryFile>(bytes, "fc27-synthetic.nsp"));
    Check(pfs->GetStatus() == Loader::ResultStatus::Success,
          "maintained PartitionFilesystem rejected PFS0");
    Check(FileSys::IsDirectoryExeFS(pfs),
          "maintained ExeFS gate did not accept main and main.npdm");
    Check(pfs->GetFiles().size() == 6,
          "missing synthetic stress texture members");
    const auto check_member = [&](std::string_view name,
                                  const std::vector<u8>& expected) {
        auto file = pfs->GetFile(name);
        Check(bool(file) && file->GetSize() == expected.size(),
              "PFS0 virtual file size/name mismatch");
        std::vector<u8> real(expected.size());
        Check(file->Read(real.data(), real.size()) == real.size() &&
              real == expected, "PFS0 real parser payload offset mismatch");
    };
    check_member("main", nso);
    check_member("main.npdm", npdm);
    for (const auto name : {"hud.rgba", "pitch.rgba", "kits.rgba"}) {
        auto f = pfs->GetFile(name);
        Check(bool(f) && f->GetSize() >= 1024 &&
              f->GetSize() <= 32U * 1024U * 1024U, "missing texture stress asset");
        std::uint8_t lead[32]{};
        Check(f->Read(lead, sizeof(lead)) == sizeof(lead),
              "real PFS0 file produced truncated texture data");
    }
    // Real constructor rejects bad magic and a genuinely truncated file table.
    auto bad = bytes;
    bad[0] ^= 0x20;
    auto invalid = std::make_shared<FileSys::PartitionFilesystem>(
        std::make_shared<FileSys::MemoryFile>(std::move(bad), "bad-magic.nsp"));
    Check(invalid->GetStatus() == Loader::ResultStatus::ErrorBadPFSHeader,
          "real PFS0 parser accepted corrupt magic");
    std::vector<u8> truncated(bytes.begin(), bytes.begin() + 20);
    invalid = std::make_shared<FileSys::PartitionFilesystem>(
        std::make_shared<FileSys::MemoryFile>(std::move(truncated), "truncated.nsp"));
    Check(invalid->GetStatus() == Loader::ResultStatus::ErrorIncorrectPFSFileSize,
          "real PFS0 parser accepted truncated table");
    auto wrong_exefs = bytes;
    // All valid offsets unchanged; only rewrite the first entry's filename.
    const std::uint32_t entry_count =
        static_cast<std::uint32_t>(pfs->GetFiles().size());
    const std::size_t string_table = 16U + entry_count * 24U;
    Check(string_table < wrong_exefs.size() && wrong_exefs[string_table] == 'm',
          "unexpected PFS0 string table");
    wrong_exefs[string_table] = 'z';
    auto partial = std::make_shared<FileSys::PartitionFilesystem>(
        std::make_shared<FileSys::MemoryFile>(std::move(wrong_exefs), "absent-main.nsp"));
    Check(partial->GetStatus() == Loader::ResultStatus::Success &&
          !FileSys::IsDirectoryExeFS(partial),
          "real extracted route accepted missing main entry");
    std::cout << "REAL_ENCORE_EXTRACTED_NSP_PFS0_PASS "
              << "members=6 valid_exefs=1 ns2_public_main_bytes="
              << nso.size() << " npdm_bytes=" << npdm.size()
              << " bad_magic_rejected=1 truncated_table_rejected=1"
              << " missing_main_rejected=1"
              << " source=maintained_PartitionFilesystem_and_IsDirectoryExeFS"
              << " full_NSP_and_KProcess_not_executed=1\n";
}
int main(int argc, char** argv) {
    try {
        Check(argc == 4, "usage: parser nsp main main.npdm");
        Validate(argv[1], argv[2], argv[3]);
        return 0;
    } catch (const std::exception& ex) {
        std::cerr << "REAL_ENCORE_EXTRACTED_NSP_PFS0_FAIL: " << ex.what() << '\n';
        return 1;
    }
}
"""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--nsp", required=True, type=Path)
    ap.add_argument("--main", required=True, type=Path)
    ap.add_argument("--npdm", required=True, type=Path)
    args = ap.parse_args()
    magic, constructor, predicate = extract_maintained()
    source = HOST_PREFIX + magic + constructor + HOST_MIDDLE + predicate + HOST_TEST
    with tempfile.TemporaryDirectory(prefix="ns2-real-extracted-nsp-") as tmp:
        src = Path(tmp) / "extracted_nsp.cpp"
        src.write_text(source)
        for compiler, opt in (("clang++", "-O1"), ("g++", "-O2")):
            if not shutil.which(compiler):
                raise RuntimeError(f"missing required compiler {compiler}")
            exe = Path(tmp) / ("extracted_" + compiler.replace("+", "p"))
            cmd = [compiler, "-std=c++20", opt, "-Wall", "-Wextra",
                   "-fsanitize=address,undefined", "-fno-sanitize-recover=all",
                   "-fno-omit-frame-pointer", str(src), "-o", str(exe)]
            built = subprocess.run(cmd, capture_output=True, text=True, timeout=70)
            if built.returncode:
                raise RuntimeError(f"{compiler} compile failed:\n{built.stderr[-6500:]}")
            run = subprocess.run([str(exe), str(args.nsp), str(args.main),
                                  str(args.npdm)], capture_output=True,
                                 text=True, timeout=45)
            if run.returncode:
                raise RuntimeError(f"{compiler} test failed:\n{run.stdout}\n"
                                   f"{run.stderr[-6500:]}")
            print(run.stdout.strip(), compiler, opt, flush=True)
    print("REAL_EXTRACTED_NSP_ROUTE_SOURCE_GUARD_PASS")


if __name__ == "__main__":
    main()
