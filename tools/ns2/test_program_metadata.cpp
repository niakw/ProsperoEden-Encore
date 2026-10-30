// SPDX-License-Identifier: GPL-3.0-or-later
// Synthetic metadata only. Exercises the *actual* experimental ProgramMetadata::Load.
#include <algorithm>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <fstream>
#include <iterator>
#include <array>
#include "core/loader/ns2_nso_preflight.h"
#include <memory>
#include <optional>
#include <string>
#include <vector>
#include "core/file_sys/program_metadata.h"
#include "core/file_sys/vfs/vfs.h"
#include "core/loader/loader.h"

// This executable links the real parser, not the full emulator filesystem.
// Supply only the missing VFS base defaults required for a standalone fixture.
namespace FileSys {
VfsFile::~VfsFile() = default;
std::string VfsFile::GetExtension() const { return {}; }
std::optional<u8> VfsFile::ReadByte(std::size_t offset) const {
    u8 value{};
    return Read(&value, 1, offset) == 1 ? std::optional{value} : std::nullopt;
}
std::vector<u8> VfsFile::ReadBytes(std::size_t size, std::size_t offset) const {
    std::vector<u8> bytes(size);
    bytes.resize(Read(bytes.data(), size, offset));
    return bytes;
}
std::vector<u8> VfsFile::ReadAllBytes() const { return ReadBytes(GetSize()); }
bool VfsFile::WriteByte(u8, std::size_t) { return false; }
std::size_t VfsFile::WriteBytes(const std::vector<u8>&, std::size_t) { return 0; }
std::string VfsFile::GetFullPath() const { return "main.npdm"; }
} // namespace FileSys

class FixtureFile final : public FileSys::VfsFile {
public:
    explicit FixtureFile(std::vector<u8> b) : bytes(std::move(b)) {}
    std::string GetName() const override { return "main.npdm"; }
    std::size_t GetSize() const override { return bytes.size(); }
    bool Resize(std::size_t) override { return false; }
    FileSys::VirtualDir GetContainingDirectory() const override { return {}; }
    bool IsWritable() const override { return false; }
    bool IsReadable() const override { return true; }
    std::size_t Read(u8* output, std::size_t length, std::size_t offset) const override {
        if (offset > bytes.size()) return 0;
        const std::size_t count = std::min(length, bytes.size() - offset);
        if (count) std::memcpy(output, bytes.data() + offset, count);
        return count;
    }
    std::size_t Write(const u8*, std::size_t, std::size_t) override { return 0; }
    bool Rename(std::string_view) override { return false; }
private:
    std::vector<u8> bytes;
};

static void put32(std::vector<u8>& b, std::size_t off, std::uint32_t n) {
    for (unsigned i=0;i<4;++i) b.at(off+i) = static_cast<u8>(n >> (8*i));
}
static void put64(std::vector<u8>& b, std::size_t off, std::uint64_t n) {
    for (unsigned i=0;i<8;++i) b.at(off+i) = static_cast<u8>(n >> (8*i));
}
static void magic(std::vector<u8>& b, std::size_t off, const char* bytes) {
    for (int i=0;i<4;++i) b.at(off+i) = static_cast<u8>(bytes[i]);
}
static void require(bool ok, const char* what) {
    if (!ok) { std::cerr << "FAILED: " << what << '\n'; std::exit(1); }
}
static std::vector<u8> valid(bool extended) {
    std::vector<u8> b(0x600);
    const std::uint32_t prefix = extended ? 0x300 : 0x200;
    magic(b,0,"META");
    put32(b,0x70,0x80);  // ACI offset
    put32(b,0x74,0x80);  // ACI size
    put32(b,0x78,0x100); // ACID offset
    put32(b,0x7c,0x400); // ACID size

    magic(b,0x80,"ACI0");
    put64(b,0x80+0x10,0x0100000000000420ULL); // program id
    put32(b,0x80+0x20,0x40); // FAH offset
    put32(b,0x80+0x24,0x40); // FAH size
    put32(b,0x80+0x38,0x78); // KAC offset
    put32(b,0x80+0x3c,0);    // KAC size
    b.at(0x80+0x40) = 1;     // FAH version
    put64(b,0x80+0x40+4,0xdeadbeefULL);

    const std::size_t acid=0x100+prefix;
    magic(b,acid,"ACID");
    put32(b,acid+0x20,prefix+0x40); // FAC offset relative to ACID start
    put32(b,acid+0x24,0x40);        // FAC size
    b.at(0x100+prefix+0x40)=1;      // FAC version
    put64(b,0x100+prefix+0x40+4,0x4321ULL);
    return b;
}
static Loader::ResultStatus parse(const std::vector<u8>& bytes, bool* ns2=nullptr,
                                  std::uint64_t* program_id=nullptr) {
    FileSys::ProgramMetadata metadata;
    const auto status=metadata.Load(std::make_shared<FixtureFile>(bytes));
    if (ns2) *ns2=metadata.IsSwitch2();
    if (program_id && status==Loader::ResultStatus::Success)
        *program_id=metadata.GetTitleID();
    return status;
}
int main(int argc, char** argv) {
    require(argc == 1 || argc == 3,
            "usage: test_program_metadata [main.npdm main]");
    bool ns2=false;
    std::uint64_t id=0;
    const auto legacy=valid(false);
    require(parse(legacy,&ns2,&id)==Loader::ResultStatus::Success,"legacy NPDM load");
    require(!ns2 && id==0x0100000000000420ULL,"legacy identity");
    auto extended=valid(true);
    require(parse(extended,&ns2,&id)==Loader::ResultStatus::Success,"extended NPDM load");
    require(ns2 && id==0x0100000000000420ULL,"NS2 identity");
    // If both bodies exist, legacy wins, preserving Switch 1 compatibility.
    auto ambiguous=extended;
    magic(ambiguous,0x100+0x200,"ACID");
    put32(ambiguous,0x100+0x200+0x20,0x240);
    put32(ambiguous,0x100+0x200+0x24,0x40);
    ambiguous.at(0x100+0x240)=1;
    require(parse(ambiguous,&ns2)==Loader::ResultStatus::Success && !ns2,
            "ambiguous magic conservatively selects legacy");
    extended.at(0x100+0x300)=0;
    require(parse(extended)==Loader::ResultStatus::ErrorBadACIDHeader,
            "invalid ACID rejected");
    auto truncated=valid(true);
    truncated.resize(0x420);
    require(parse(truncated)!=Loader::ResultStatus::Success,"truncated ACID rejected");
    auto invalid=valid(true);
    put32(invalid,0x7c,0xffffffffU);
    require(parse(invalid)==Loader::ResultStatus::ErrorBadACIDHeader,
            "overflowing ACID rejected");
    require(parse(std::vector<u8>(0x20))==Loader::ResultStatus::ErrorBadNPDMHeader,
            "truncated META rejected");
    if (argc == 3) {
        const auto read_file = [](const char* name) {
            std::ifstream f(name, std::ios::binary);
            require(bool(f), "ExeFS file cannot be opened");
            return std::vector<u8>(std::istreambuf_iterator<char>{f},
                                   std::istreambuf_iterator<char>{});
        };
        const auto npdm = read_file(argv[1]);
        const auto main_nso = read_file(argv[2]);
        require(npdm.size() == 0x600 && main_nso.size() >= Eden::NS2::ExeFS::NsoHeaderBytes,
                "Invalid ExeFS research fixture size");
        FileSys::ProgramMetadata actual;
        require(actual.Load(std::make_shared<FixtureFile>(npdm)) ==
                    Loader::ResultStatus::Success, "Real parser rejected ExeFS main.npdm");
        require(actual.IsSwitch2() && actual.Is64BitProgram() &&
                    actual.GetAddressSpaceType() == FileSys::ProgramAddressSpaceType::Is39Bit &&
                    actual.GetPoolPartition() == FileSys::PoolPartition::Application &&
                    actual.GetMainThreadCore() == 0 &&
                    actual.GetMainThreadPriority() == 0x2C &&
                    actual.GetMainThreadStackSize() == 0x100000 &&
                    actual.GetTitleID() == 0x0100000000000420ULL &&
                    actual.GetKernelCapabilities().empty(),
                "Real parser rejected expected AArch64 NS2 process attributes");
        std::array<std::uint8_t, Eden::NS2::ExeFS::NsoHeaderBytes> header{};
        std::copy_n(main_nso.data(), header.size(), header.data());
        require(Eden::NS2::ExeFS::PreflightNso(header, main_nso.size()).Ready(),
                "Real NS2 ExeFS header guard rejected homebrew main");
        constexpr char guest_text[] = "hello from HOS\n";
        require(std::search(main_nso.begin(), main_nso.end(),
                            guest_text, guest_text + sizeof(guest_text) - 1)
                    != main_nso.end(), "Unexpected AArch64 public NSO test text");
        std::cout << "Real parser + NSO0 guard: paired public ExeFS fixture PASS"
                  << " (no KProcess or HLE boot)\\n";
    }
    std::cout << "real ProgramMetadata::Load synthetic NPDM: PASS\\n";
}
