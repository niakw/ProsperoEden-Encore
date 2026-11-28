// SPDX-License-Identifier: GPL-3.0-or-later
#include "nup_v1_native_content.h"

#include <limits>
#include <map>
#include <optional>
#include <utility>

#include "core/file_sys/common_funcs.h"
#include "core/file_sys/program_metadata.h"
#include "core/loader/loader.h" // Loader::ResultStatus has only a forward declaration in program_metadata.h
#include "core/file_sys/romfs.h"
#include "core/file_sys/vfs/vfs.h"
#include "core/file_sys/vfs/vfs_layered.h"

namespace Eden::NupV1::Native {
namespace {

// Lichii FindUpgradePack also recognizes Switch 2 resource table names.
// Inspect directory metadata only; never read or decompress file contents.
// The NUP parser admits at most 2,000,000 file/directory nodes per archive.
bool HasUpgradePackMarker(const FileSys::VirtualDir& root) {
    if (!root) return false;
    const auto system = root->GetSubdirectory("System");
    if (system && system->GetFile("AoCUpgradeVersion.txt")) return true;

    constexpr std::size_t MaxNodes = 2'000'000;
    std::vector<FileSys::VirtualDir> pending{root};
    std::size_t remaining = MaxNodes;
    while (!pending.empty()) {
        if (!remaining) return false;
        --remaining;
        auto directory = std::move(pending.back());
        pending.pop_back();
        for (const auto& file : directory->GetFiles()) {
            if (!remaining) return false;
            --remaining;
            if (file && file->GetName().find(".Nin_Ounce") != std::string::npos)
                return true;
        }
        auto children = directory->GetSubdirectories();
        if (children.size() > remaining ||
            pending.size() > remaining - children.size())
            return false;
        for (auto& child : children)
            if (child) pending.push_back(std::move(child));
    }
    return false;
}

struct EmbeddedSwitch2Program {
    FileSys::VirtualDir exefs;
    FileSys::VirtualDir romfs;
    std::uint64_t program_id{};
};

// Lichii SelectProgram: a Switch 1 update NUP with no base ExeFS may carry
// a Switch 2 Edition as program1/exefs. The package need not be tagged as a
// standalone update: that flag describes container topology, not the guest
// program generation. Never infer this from filenames; the embedded NPDM must
// identify the exact NS2 program-index-1 counterpart of the packaged NS1 update.
std::optional<EmbeddedSwitch2Program> FindEmbeddedSwitch2Program(const Mount& mount) {
    const auto& packages = mount.Packages();
    std::optional<std::size_t> newest;
    std::optional<std::size_t> base;
    for (std::size_t i = 0; i < packages.size(); ++i) {
        const auto& p = packages[i];
        if (p.kind == 0 && !base) base = i;
        if (p.kind == 1 && (!newest || p.version > packages[*newest].version))
            newest = i;
    }
    // Match Lichii SelectProgram: program1/exefs is considered when no base
    // ExeFS is actually present, not merely when no base package record exists.
    const auto base_exefs =
        base ? mount.PackageView(*base, ContentView::ExeFS) : FileSys::VirtualDir{};
    if (!newest || base_exefs || (packages[*newest].title_id >> 56) != 0x01)
        return std::nullopt;
    const auto root = mount.PackageRoot(*newest);
    const auto program1 = root ? root->GetSubdirectory("program1") : FileSys::VirtualDir{};
    const auto exefs = program1 ? program1->GetSubdirectory("exefs") : FileSys::VirtualDir{};
    const auto npdm = exefs ? exefs->GetFile("main.npdm") : FileSys::VirtualFile{};
    constexpr std::size_t MaxNpdmBytes = 4U * 1024U * 1024U;
    if (!exefs || !exefs->GetFile("main") || !npdm ||
        npdm->GetSize() == 0 || npdm->GetSize() > MaxNpdmBytes)
        return std::nullopt;
    FileSys::ProgramMetadata metadata;
    constexpr std::uint64_t LowTitleMask = 0x00FFFFFFFFFFFFFFULL;
    const auto expected_id = 0x0400000000000000ULL |
        ((FileSys::GetBaseTitleID(packages[*newest].title_id) + 1) & LowTitleMask);
    if (metadata.Load(npdm) != Loader::ResultStatus::Success ||
        !metadata.IsSwitch2() || metadata.GetTitleID() != expected_id)
        return std::nullopt;
    return EmbeddedSwitch2Program{
        exefs, program1->GetSubdirectory("romfs"), expected_id};
}
} // namespace

ContentSet::ContentSet(std::shared_ptr<Mount> mount,
                       std::optional<std::uint64_t> caller_program_id,
                       std::optional<std::uint64_t> nacp_aoc_base_id)
    : mount_(std::move(mount)) {
    if (!mount_) return;
    const auto& packages = mount_->Packages();

    // Mirror the existing aoc:u service's GetBaseTitleID contract. This
    // prevents packages belonging to unrelated games from appearing as DLC.
    std::optional<std::uint64_t> active_base;
    for (const auto& package : packages) {
        if (package.kind == 0) {
            active_base = FileSys::GetBaseTitleID(package.title_id);
            break;
        }
    }
    if (!active_base) {
        const Package* newest = nullptr;
        for (const auto& package : packages) {
            if (package.kind == 1 && (!newest || package.version > newest->version))
                newest = &package;
        }
        if (newest) active_base = FileSys::GetBaseTitleID(newest->title_id);
    }

    if (caller_program_id) {
        const auto requested = FileSys::GetBaseTitleID(*caller_program_id);
        if (active_base && *active_base != requested) {
            // A verified program1 runs with a 04-platform program ID but its
            // standalone update and AoC content belong to the 01-platform
            // family. Retain that family only after the exact embedded NPDM
            // was authenticated; never grant unrelated callers DLC access.
            const auto embedded = FindEmbeddedSwitch2Program(*mount_);
            if (!embedded || embedded->program_id != *caller_program_id) {
                // A regular NS1 base + NS2 Edition update can also select
                // an exact 04-platform program (ValidateProgramIdentity).
                // Keep its NS1 AoC family only after verifying the selected
                // executable against the declared base and caller.
                constexpr std::uint64_t PlatformMask = 0xFF00000000000000ULL;
                constexpr std::uint64_t LowTitleMask = ~PlatformMask;
                bool matching_base = false;
                for (const auto& package : packages) {
                    if (package.kind == 0 &&
                        (package.title_id & PlatformMask) == 0x0100000000000000ULL &&
                        (*caller_program_id & PlatformMask) == 0x0400000000000000ULL &&
                        (*caller_program_id & LowTitleMask) ==
                            ((package.title_id + 1) & LowTitleMask)) {
                        matching_base = true;
                        break;
                    }
                }
                if (!matching_base) return;
                const auto exefs = ExeFS();
                const auto npdm = exefs ? exefs->GetFile("main.npdm") : FileSys::VirtualFile{};
                constexpr std::size_t MaxNpdmBytes = 4U * 1024U * 1024U;
                if (!npdm || npdm->GetSize() == 0 || npdm->GetSize() > MaxNpdmBytes)
                    return;
                FileSys::ProgramMetadata metadata;
                if (metadata.Load(npdm) != Loader::ResultStatus::Success ||
                    !metadata.IsSwitch2() || metadata.GetTitleID() != *caller_program_id)
                    return;
            }
            // The verified cross-platform executable retains the NS1
            // application family for explicit Switch 2 upgrade packs.
            edition_upgrade_base_ = *active_base;
        } else {
            active_base = requested;
        }
    }
    // Add-on-only archives carry no owning executable title: callers must
    // supply the program identity instead of seeing cross-title content.
    if (!active_base) return;
    // A non-default NACP-declared AoC family is only meaningful when bound to
    // a known caller. Do not grant blanket visibility from an unscoped mount.
    if (nacp_aoc_base_id && !caller_program_id) return;
    // The AoC base must identify the start of an 0x800-title range.
    // Reject a malformed NACP base instead of registering a shifted range
    // or falling back to unrelated conventional DLC.
    if (nacp_aoc_base_id && (*nacp_aoc_base_id & FileSys::AOC_TITLE_ID_MASK))
        return;
    if (*active_base > std::numeric_limits<std::uint64_t>::max() - FileSys::AOC_TITLE_ID_OFFSET)
        return;
    const auto aoc_base = nacp_aoc_base_id.value_or(
        *active_base + FileSys::AOC_TITLE_ID_OFFSET);
    addon_base_id_ = aoc_base;

    // Select DLC from the declared AoC base, never by blindly treating every
    // title with a similar high prefix as belonging to the application.
    // Custom bases are inputs from trusted NACP metadata, not per-game hacks.
    // Two revisions of one DLC use the highest NCM version.
    std::map<std::uint64_t, std::size_t> selected;
    for (std::size_t i = 0; i < packages.size(); ++i) {
        const auto& package = packages[i];
        if (package.kind != 2) continue;
        if (package.title_id < aoc_base ||
            package.title_id - aoc_base > FileSys::AOC_TITLE_ID_MASK)
            continue;
        const auto it = selected.find(package.title_id);
        if (it == selected.end() ||
            package.version > packages[it->second].version) {
            selected.insert_or_assign(package.title_id, i);
        }
    }

    for (const auto& [title_id, index] : selected) {
        const auto directory = mount_->PackageView(index, ContentView::RomFS);
        if (!directory) continue;
        addons_.push_back(AddOnDirectory{
            index, title_id, packages[index].version, directory});
    }
}

FileSys::VirtualDir ContentSet::ExeFS() const {
    if (!mount_) return {};
    // Lichii SelectProgram prefers a verified standalone NS2 program1 even
    // when that NS1 update also has a valid legacy ExeFS. The embedded NPDM
    // must authenticate platform 04 and the exact program-index-1 title.
    if (const auto embedded = FindEmbeddedSwitch2Program(*mount_); embedded)
        return embedded->exefs;
    // An update's ExeFS is one executable, not a per-file patch over base
    // modules. Never combine a new main with an old main.npdm or SDK.
    // Lichii SelectProgram likewise chooses a single program package.
    const auto& packages = mount_->Packages();
    std::optional<std::size_t> newest_update;
    std::optional<std::size_t> base;
    for (std::size_t i = 0; i < packages.size(); ++i) {
        const auto& package = packages[i];
        if (package.kind == 0) base = i;
        if (package.kind == 1 &&
            (!newest_update || package.version > packages[*newest_update].version))
            newest_update = i;
    }
    if (newest_update) {
        const auto update = mount_->PackageView(*newest_update, ContentView::ExeFS);
        if (update) {
            // Incomplete executable updates cannot be repaired by mixing
            // their code and NPDM with a different package's revision.
            if (!update->GetFile("main") || !update->GetFile("main.npdm"))
                return {};
            return update;
        }
    }
    if (base) {
        const auto base_exefs = mount_->PackageView(*base, ContentView::ExeFS);
        if (base_exefs && base_exefs->GetFile("main") &&
            base_exefs->GetFile("main.npdm"))
            return base_exefs;
    }
    return {};

}

FileSys::VirtualFile ContentSet::CreateRomFS(bool allow_upgrade_pack) const {
    if (!mount_) return {};
    auto directory = mount_->Effective(ContentView::RomFS);
    const auto embedded = FindEmbeddedSwitch2Program(*mount_);
    // The upgrade pack is selected from the verified conventional NS1
    // family, independently of a NACP override for ordinary AoC listing.
    // A native program1 RomFS is sufficient when no regular tree exists.
    if (allow_upgrade_pack && edition_upgrade_base_ && addon_base_id_ &&
        (directory || (embedded && embedded->romfs)) &&
        *edition_upgrade_base_ <=
            std::numeric_limits<std::uint64_t>::max() - FileSys::AOC_TITLE_ID_OFFSET) {
        const auto upgrade_base = *edition_upgrade_base_ + FileSys::AOC_TITLE_ID_OFFSET;
        const auto& packages = mount_->Packages();
        FileSys::VirtualDir upgrade;
        std::uint32_t upgrade_version{};
        for (std::size_t i = 0; i < packages.size(); ++i) {
            const auto& package = packages[i];
            if (package.kind != 2 || package.title_id < upgrade_base ||
                package.title_id - upgrade_base > FileSys::AOC_TITLE_ID_MASK ||
                (upgrade && package.version <= upgrade_version))
                continue;
            auto candidate = mount_->PackageView(i, ContentView::RomFS);
            if (!HasUpgradePackMarker(candidate)) continue;
            upgrade_version = package.version;
            upgrade = std::move(candidate);
        }
        if (upgrade) {
            if (directory) {
                directory = FileSys::LayeredVfsDirectory::MakeLayeredDirectory(
                    {std::move(upgrade), std::move(directory)}, "romfs");
                if (!directory) return {};
            } else {
                directory = std::move(upgrade);
            }
        }
    }
    // The native program1 tree overlays, rather than replaces, the regular
    // update RomFS. The existing read-only layered VFS merges shared nested
    // directories and gives program1 files precedence (Lichii ReadRomFS).
    // CreateRomFS's second parameter is an IPS/stub patch directory, not an
    // ordinary file overlay: merge in VFS BEFORE serializing.
    if (embedded && embedded->romfs) {
        if (directory) {
            directory = FileSys::LayeredVfsDirectory::MakeLayeredDirectory(
                {embedded->romfs, std::move(directory)}, "romfs");
            if (!directory) return {};
        } else {
            directory = embedded->romfs;
        }
    }
    return directory ? FileSys::CreateRomFS(std::move(directory), nullptr)
                     : FileSys::VirtualFile{};
}

FileSys::VirtualFile ContentSet::CreateAddOnRomFS(std::size_t package_index) const {
    for (const auto& addon : addons_) {
        if (addon.package_index == package_index && addon.romfs) {
            return FileSys::CreateRomFS(addon.romfs, nullptr);
        }
    }
    return {};
}

bool ContentSet::HasExecutableMain() const {
    const auto exefs = ExeFS();
    return exefs && exefs->GetFile("main") && exefs->GetFile("main.npdm");
}

} // namespace Eden::NupV1::Native
