#!/usr/bin/env python3
"""Exact pinned service parity plus bounded guest version metadata diagnostic."""
from pathlib import Path
root=Path(__file__).resolve().parents[1]
base=(root/"vendor/sources/eden/src/core/hle/service/am/service/application_functions.cpp").read_text()
current=(root/"vendor/encore-active/eden-core/src/core/hle/service/am/service/application_functions.cpp").read_text()
seed="    auto const seed = res.first->raw.seed_for_pseudo_device_id;"
assert base.count(seed)==1
assert current.count("res.first != nullptr ? res.first->raw.seed_for_pseudo_device_id : u64_le{0};")==1
assert 'EDEN_GUEST_TITLE_VERSION title={:016X} metadata={} version={}' in current
assert current.count("last_reported_title.exchange(title_id, std::memory_order_relaxed)") == 1
assert '#ifdef EDEN_GUEST_TITLE_VERSION_DIAG' in current
assert '"unknown"' in current
assert "GetDisplayVersion" in current
cmake=(root/"headless/CMakeLists.txt").read_text()
assert 'list(APPEND core_sources "__DOLLAR__{EDEN_APP_FUNCTION_SOURCE}")'.replace("__DOLLAR__","$") in cmake
# Diagnostic implementation stays in the maintained source for review, but
# the single shipping PS5 runtime does not enable noisy title-version logging.
assert 'EDEN_GUEST_TITLE_VERSION_DIAG' not in cmake
assert 'write_derived("__DOLLAR__{PORT_BUILD_DIR}/application_functions.cpp"'.replace("__DOLLAR__","$") not in cmake
print("GUEST_TITLE_VERSION_SOURCE_PASS parity=guarded runtime-quiet=1")

# Shipping PS5 uses the shared NS2 AM owner for BOTH generations. The
# historical host/legacy owner above remains byte-identical.
import hashlib
selected = root/"vendor/encore-active/ns2-runtime/am/core/hle/service/am/service/application_functions.cpp"
selected_h = root/"vendor/encore-active/ns2-runtime/am/core/hle/service/am/service/application_functions.h"
raw = selected.read_bytes()
raw_h = selected_h.read_bytes()
gitblob = lambda data: hashlib.sha1(
    b"blob "+str(len(data)).encode()+bytes([0])+data).hexdigest()
assert gitblob(raw) == "db44446a39249e38f54fbc30d016338696e3bddc"
assert gitblob(raw_h) == "e91e412211f9c9e964d19560e2226338426be65e"
source = raw.decode()
source_h = raw_h.decode()

# The preceding green shared-AM receipt pinned blobs
# 5a455267e3a8d0e313a9e9aa35f087d076a569b9 /
# 656c270f5dabe25ccfbc382370b04d7d4f4f94ad. The selected final override had
# silently fallen behind the maintained NS1 backport for nineteen methods.
# Require exact body parity for those reviewed methods while preserving the
# NS2-only commands below.
maintained_am = (
    root/"vendor/encore-active/eden-backports/src/core/hle/service/am/service/application_functions.cpp"
).read_text()

def result_method_body(contents, name):
    start = contents.index(f"Result IApplicationFunctions::{name}(")
    ends = [
        p for p in (
            contents.find("\nResult IApplicationFunctions::", start + 10),
            contents.find("\nvoid IApplicationFunctions::", start + 10),
            contents.find("\n} // namespace Service::AM", start + 10),
        ) if p >= 0
    ]
    assert ends, name
    return contents[start:min(ends)]

synced_methods = (
    "CreateCacheStorage",
    "GetSaveDataSizeMax",
    "BeginBlockingHomeButtonShortAndLongPressed",
    "EndBlockingHomeButtonShortAndLongPressed",
    "BeginBlockingHomeButton",
    "EndBlockingHomeButton",
    "NotifyRunning",
    "IsGamePlayRecordingSupported",
    "SetMediaPlaybackStateForApplication",
    "SetGamePlayRecordingState",
    "EnableApplicationCrashReport",
    "InitializeApplicationCopyrightFrameBuffer",
    "SetApplicationCopyrightImage",
    "SetApplicationCopyrightVisibility",
    "QueryApplicationPlayStatistics",
    "QueryApplicationPlayStatisticsByUid",
    "GetPreviousProgramIndex",
    "GetGpuErrorDetectedSystemEvent",
    "PrepareForJit",
)
for name in synced_methods:
    assert result_method_body(source, name) == result_method_body(maintained_am, name), (
        "selected shared AM regressed maintained NS1 method", name
    )

# The selected header must also retain the state required by the synchronized
# copyright/play-statistics implementations.
for fragment in (
    "std::unique_ptr<PlayTime::PlayTimeManager> m_play_time_manager;",
    "std::mutex m_copyright_mutex;",
    "bool m_copyright_framebuffer_initialized{};",
    "CopyrightImageState m_copyright_image{};",
):
    assert fragment in source_h, fragment

cmd37_new = '{37, D<&IApplicationFunctions::GetLimitedApplicationLicenseUpgradableEvent>, "GetLimitedApplicationLicenseUpgradableEvent"}'
cmd37_impl = '''Result IApplicationFunctions::GetLimitedApplicationLicenseUpgradableEvent(
    OutCopyHandle<Kernel::KReadableEvent> out_event) {
    // GetLimitedApplicationLicense reports the normal/full-license path (0), so there is
    // no pending limited-license upgrade to signal. Reuse the applet's persistent,
    // currently-unsignaled event rather than manufacturing a successful upgrade.
    LOG_DEBUG(Service_AM, "called, no limited application license upgrade pending");
    *out_event = m_applet->unknown_event.GetHandle();
    R_SUCCEED();
}

'''
cmd37_decl = '''    Result GetLimitedApplicationLicenseUpgradableEvent(
        OutCopyHandle<Kernel::KReadableEvent> out_event);
'''
assert source.count(cmd37_new) == source.count(cmd37_impl) == 1
assert source_h.count(cmd37_decl) == 1
assert 'm_applet->unknown_event.Signal' not in source
# The merged native AM owner also exposes NS2 command 321 with one byte,
# without changing the previously reviewed language response path.
assert '{321, D<&IApplicationFunctions::Unknown321>, "Unknown321"}' in source
assert 'Result IApplicationFunctions::Unknown321(Out<u8> out)' in source
assert '*out = 0;' in source.split('Result IApplicationFunctions::Unknown321(Out<u8> out)', 1)[1].split('}', 1)[0]
assert source.index("R_TRY(app_man->ConvertApplicationLanguageToLanguageCode(out_language_code, desired_language));") < source.index("const GuestLanguageReply reply{")
assert "EDEN_GUEST_LANGUAGE_REPLY title=" in source
assert "emitted >= 32" in source
assert 'set(EDEN_SHARED_NS2_AM ON)' in cmake
assert 'list(APPEND eden_ns2_am_sources "${EDEN_NS2_AM_ROOT}/core/hle/service/am/service/application_functions.cpp")' in cmake
assert '*out_event = m_applet->unknown_event.GetHandle();' in source
print("SHARED_NATIVE_AM_LANGUAGE_REPLY_SOURCE_PASS exact_blob=1 real_return=1 bounded=32 native_execution=0")
print("NS1_SHARED_AM_COMPLETENESS_PARITY_PASS methods=19 selected_final_override=1")
print("NS1_AM_LIMITED_LICENSE_EVENT_PASS command=37 full_license=1 event_unsignaled=1")
