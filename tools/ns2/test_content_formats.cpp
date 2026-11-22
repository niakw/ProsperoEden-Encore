// SPDX-License-Identifier: GPL-3.0-or-later
// File/filename fixtures ONLY: never assert that a Switch 2 game decrypts,
// installs, boots, renders, or reaches any FPS.
#include <cstdio>
#include <cstdlib>
#include <string_view>
#include "core/loader/ns2_content_formats.h"

using namespace Eden::NS2::Content;
static void check(bool ok, const char* message) {
    if (!ok) {
        std::fprintf(stderr, "NS2 content formats: FAILED: %s\n", message);
        std::exit(1);
    }
}
int main() {
    struct Fixture { std::string_view name; Kind type; Route route; };
    constexpr Fixture cases[] = {
        {"main", Kind::ExeFSMain, Route::Executable},
        {"00", Kind::NCA, Route::ExistingArchive},
        {"build.NRO", Kind::NRO, Route::Executable},
        {"main.NSO", Kind::NSO, Route::Executable},
        {"update.NCA", Kind::NCA, Route::ExistingArchive},
        {"registered.NAX", Kind::NAX, Route::ExistingArchive},
        {"mkw.XCI", Kind::XCI, Route::ExistingContainer},
        {"mkw.XCZ", Kind::XCZ, Route::ExistingContainer},
        {"mkw.DXCI", Kind::DXCI, Route::ExistingContainer},
        {"mkw.NSP", Kind::NSP, Route::ExistingContainer},
        {"mkw.NSZ", Kind::NSZ, Route::ExistingContainer},
        {"mkw.DNSP", Kind::DNSP, Route::ExistingContainer},
        {"game.NX", Kind::NX, Route::ExistingContainer},
        {"boot.KIP", Kind::KIP, Route::Executable},
        {"main.npdm", Kind::NPDMMetadata, Route::MetadataOnly},
        {"RomFS", Kind::RomFSData, Route::AssetsOnly},
        {"romfs.bin", Kind::RomFSData, Route::AssetsOnly},
        {"mkw.xci2", Kind::Unsupported, Route::Unknown},
        {"mkw.nsp2", Kind::Unsupported, Route::Unknown},
        {"mkw.nca2", Kind::Unsupported, Route::Unknown},
        {"mkw.mkw", Kind::Unsupported, Route::Unknown},
        {"exefs", Kind::Unsupported, Route::Unknown},
        {"main2", Kind::Unsupported, Route::Unknown},
        {"romfs.ncz", Kind::Unsupported, Route::Unknown},
        {"", Kind::Unsupported, Route::Unknown},
    };
    for (const auto& test : cases) {
        const auto kind = IdentifyName(test.name);
        check(kind == test.type && LoaderRoute(kind) == test.route,
              "filename classification must reflect existing Eden route");
        check(HasExistingLoaderRoute(kind) ==
              (test.route == Route::Executable ||
               test.route == Route::ExistingArchive ||
               test.route == Route::ExistingContainer),
              "unknown/metadata/asset-only content must not be called bootable");
    }
    check(IdentifyName("MAIN") == Kind::Unsupported,
          "ExeFS magic basename is an exact target, not a generic extension");
    check(IdentifyName("00") == Kind::NCA,
          "legacy registered 00 may still be NCA or NAX, magic wins");
    check(IdentifyName("nca2") == Kind::Unsupported,
          "NCA2 archive variant label is not a Switch 2 file extension");
    // Compressed/decrypted aliases and NX must fail closed if magic probes fail.
    // NSP/XCI/NCA retain ordinary fallback only where their native loader can
    // subsequently validate the content; a suffix never certifies a game.
    check(RequiresRecognizedContent(Kind::XCZ) &&
          RequiresRecognizedContent(Kind::NSZ) &&
          RequiresRecognizedContent(Kind::DNSP) &&
          RequiresRecognizedContent(Kind::DXCI) &&
          RequiresRecognizedContent(Kind::NX) &&
          !RequiresRecognizedContent(Kind::XCI) &&
          !RequiresRecognizedContent(Kind::NSP) &&
          !RequiresRecognizedContent(Kind::NCA),
          "new aliases require a recognized content signature");
    for (const auto name : {"mkw.xcz", "mkw.XCZ", "mkw.nsz", "mkw.NSZ",
                            "mkw.dnsp", "mkw.DNSP", "mkw.dxci", "mkw.DXCI",
                            "title.nx", "title.NX"}) {
        check(!MayFallbackByName(IdentifyName(name)),
              "new container must not enter loader through extension alone");
    }
    for (const auto name : {"mkw.xci", "mkw.nsp", "mkw.nca", "main", "00"}) {
        check(MayFallbackByName(IdentifyName(name)),
              "existing regular file routes retain backwards-compatible handling");
    }
    check(MayFallbackByName(Kind::Unsupported),
          "unknown files remain controlled by existing loader unsupported routing");
    check(IdentifyName("game-card-key") == Kind::Unsupported,
          "game-key card is a distribution entitlement, not a ROM image");
    std::puts("NS2 content filename recognition: PASS (no Switch 2 boot claim)");
}
