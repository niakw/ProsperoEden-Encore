// SPDX-License-Identifier: GPL-3.0-or-later
// R21: audited, deterministic official-repo/asset plan, with no network.
#include "native_app_update.hpp"
#include <cassert>
#include <string>
int main() {
    using namespace Eden::EncoreUpdate;
    NativeInstallPlan p{
        .installed_revision="R322",
        .latest_revision="R323",
        .package_name="Eden-Encore-R323-abcdef12-FTP-PPSA99008.zip",
        .package_path="/niakw/ProsperoEden-Encore/releases/download/"
                      "encore-R323-abcdef12/Eden-Encore-R323-abcdef12-FTP-PPSA99008.zip",
        .sha256=std::string(64,'a'),
        .bytes=50000000,
    };
    assert(IsSafeNativeInstallPlan(p));
    auto copy=p;
    copy.installed_revision="R323";
    assert(!IsSafeNativeInstallPlan(copy));
    copy=p;
    copy.latest_revision="R1000";
    assert(!IsSafeNativeInstallPlan(copy)); // native PS5 only 01.400.xxx
    copy=p;
    copy.package_path="/evil/releases/download/encore-R323-abcdef12/" + p.package_name;
    assert(!IsSafeNativeInstallPlan(copy));
    copy=p;
    copy.package_path+="?asset=evil";
    assert(!IsSafeNativeInstallPlan(copy));
    copy=p;
    copy.package_name="Eden-Encore-R323-abcdef12-FTP-PPSA99008.pkg";
    assert(!IsSafeNativeInstallPlan(copy));
    copy=p;
    copy.sha256="not-hex";
    assert(!IsSafeNativeInstallPlan(copy));
    copy=p;
    copy.bytes=0;
    assert(!IsSafeNativeInstallPlan(copy));
    copy=p;
    copy.bytes=1ull<<33;
    assert(!IsSafeNativeInstallPlan(copy));
    auto host=InstallNativeApp(p);
    assert(!host.applying); // no PS5 execution on this host
    return 0;
}
