// SPDX-License-Identifier: GPL-3.0-or-later
// Hermetic R21 release-metadata validation: zero network and zero PS5 access.
#include "launcher_update_release.hpp"

#include <cassert>
#include <iostream>
#include <string>
#include <nlohmann/json.hpp>

using Eden::EncoreUpdate::AssessStableRelease;
using Eden::EncoreUpdate::ReleaseAssessment;
using Status = ReleaseAssessment::Status;

static std::string digest() {
    return "sha256:" + std::string(64, 'a');
}
static nlohmann::json fixture(std::string tag = "encore-R2-abcdef12") {
    return {
        {"tag_name", tag},
        {"draft", false},
        {"prerelease", false},
        {"body", "# Features\n\nStable UI updates.\n"},
        {"assets", nlohmann::json::array({
            {
                {"name", "PPSA99008-R2.ffpfsc"},
                {"size", 50000000u},
                {"digest", digest()},
                {"browser_download_url",
                 "https://github.com/niakw/Prospero.Eden-Encore/releases/download/" +
                 tag + "/PPSA99008-R2.ffpfsc"}
            }
        })}
    };
}

int main() {
    auto expect = [](const nlohmann::json& input, Status status,
                     std::string installed = "R1") {
        const auto result = AssessStableRelease(input.dump(), installed);
        if (result.status != status) { std::cerr << "EXPECTED " << int(status) << " GOT " << int(result.status) << " tag=" << input.value("tag_name", std::string("?")) << " asset=" << (input.contains("assets") && input["assets"].is_array() ? input["assets"].dump().substr(0,130) : "none") << "\n"; }
        assert(result.status == status);
        return result;
    };
    assert(AssessStableRelease("", "R1").status == Status::malformed);
    assert(AssessStableRelease("{bad", "R1").status == Status::malformed);
    assert(AssessStableRelease(std::string(512 * 1024 + 1, 'x'), "R1")
        .status == Status::malformed);
    auto j = fixture();
    {
        const auto r = expect(j, Status::newer_package_candidate);
        assert(r.latest_version == "R2");
        assert(r.package_name == "PPSA99008-R2.ffpfsc");
        assert(r.sha256.size() == 64);
        assert(r.package_bytes == 50000000u);
        assert(r.notes.find("Stable UI") != std::string::npos);
    }
    // Shape of the actual public R1 FTP release: trustworthy metadata,
    // but the ZIP is not a PS5 in-place installation format.
    {
        auto copy = fixture("encore-R1-56293953");
        copy["assets"][0]["name"] = "Eden-Encore-56293953-FTP-PPSA99008.zip";
        expect(copy, Status::newer_without_package, "R0");
        expect(copy, Status::current, "R1");
    }
    expect(j, Status::current, "R2");
    expect(j, Status::current, "R3");
    expect(j, Status::malformed, "R1-preview");
    {
        auto copy = j;
        copy["draft"] = true;
        expect(copy, Status::malformed);
    }
    {
        auto copy = j;
        copy["prerelease"] = true;
        expect(copy, Status::malformed);
    }
    {
        auto copy = j;
        copy.erase("prerelease");
        expect(copy, Status::malformed);
    }
    {
        auto copy = j;
        copy["tag_name"] = "R2-preview";
        expect(copy, Status::malformed);
    }
    {
        auto copy = j;
        copy["tag_name"] = "encore-R2-abcdef12/other";
        expect(copy, Status::malformed);
    }
    {
        auto copy = j;
        copy["assets"][0]["name"] = "PPSA99008-R2.zip";
        expect(copy, Status::newer_without_package);
    }
    {
        auto copy = j;
        copy["assets"][0]["name"] = "PPSA99008-R2.pkg";
        expect(copy, Status::newer_without_package);
    }
    {
        auto copy = j;
        copy["assets"][0]["name"] = "notPPSA99008-R2.ffpfsc";
        expect(copy, Status::newer_without_package);
    }
    {
        auto copy = j;
        copy["assets"][0]["name"] = "PPSA99999-R2.ffpfsc";
        expect(copy, Status::newer_without_package);
    }
    {
        auto copy = j;
        copy["assets"][0]["size"] = 10;
        expect(copy, Status::newer_without_package);
    }
    {
        auto copy = j;
        copy["assets"][0]["size"] = -1;
        expect(copy, Status::newer_without_package);
    }
    {
        auto copy = j;
        copy["assets"][0]["digest"] = "sha256:" + std::string(64, 'X');
        expect(copy, Status::newer_without_package);
    }
    {
        auto copy = j;
        copy["assets"][0]["browser_download_url"] = "https://malicious.test/update.ffpfsc";
        expect(copy, Status::newer_without_package);
    }
    {
        auto copy = j;
        copy["assets"][0]["browser_download_url"] =
            "https://github.com/niakw/Prospero.Eden-Encore/releases/download/"
            "encore-R1-old/PPSA99008-R2.ffpfsc";
        expect(copy, Status::newer_without_package);
    }
    {
        auto copy = j;
        copy["assets"] = "unexpected";
        expect(copy, Status::newer_without_package);
    }
    {
        auto copy = j;
        copy["assets"] = nlohmann::json::array();
        for (int i = 0; i < 81; ++i) copy["assets"].push_back(j["assets"][0]);
        expect(copy, Status::newer_without_package);
    }
    {
        auto copy = j;
        copy["body"] = std::string("Hi\n\t") + char(1) +
                       std::string(500, 'x');
        const auto r = expect(copy, Status::newer_package_candidate);
        assert(r.notes.size() <= 240);
        assert(r.notes.find('\n') == std::string::npos);
        assert(r.notes.find(char(1)) == std::string::npos);
    }
    {
        auto copy = j;
        copy["body"] = std::string(239, 'x') + std::string({char(0xC3), char(0xA9)}) + "more";
        const auto r = expect(copy, Status::newer_package_candidate);
        assert(r.notes.size() == 239);
    }
    {
        auto copy = j;
        copy["body"] = std::string("Hi") + std::string({char(0xC2), char(0x85)}) + "there";
        const auto r = expect(copy, Status::newer_package_candidate);
        assert(r.notes == "Hithere");
    }
    {
        auto copy = fixture("encore-R10-abcdef12");
        expect(copy, Status::current, "R11");
        expect(copy, Status::newer_package_candidate, "R9"); // Numeric R9 < R10; filename only proves package identity
    }
    std::cout << "R21 release metadata: hermetic scenario matrix passed\n";
}
