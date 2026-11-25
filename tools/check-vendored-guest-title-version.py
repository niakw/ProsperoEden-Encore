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
assert gitblob(raw) == "5a455267e3a8d0e313a9e9aa35f087d076a569b9"
assert gitblob(raw_h) == "656c270f5dabe25ccfbc382370b04d7d4f4f94ad"
source = raw.decode()
source_h = raw_h.decode()

# ca0407f9 is the reviewed predecessor that merged the NS1 application-function
# handlers into this final shared owner. The old 9719348d receipt pre-dated that
# merge and was stale. Reverse only command 37 and require exact ca0407f9 bytes.
cmd37_new = '{37, D<&IApplicationFunctions::GetLimitedApplicationLicenseUpgradableEvent>, "GetLimitedApplicationLicenseUpgradableEvent"}'
cmd37_old = '{37, nullptr, "GetLimitedApplicationLicenseUpgradableEvent"}'
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
prior = source.replace(cmd37_new, cmd37_old, 1).replace(cmd37_impl, '', 1).encode()
prior_h = source_h.replace(cmd37_decl, '', 1).encode()
assert gitblob(prior) == "1984972ed8f49218ff41520695ad879e644af81f"
assert gitblob(prior_h) == "01ee6d224088ae3fa03ee797806397f83baad679"
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
print("NS1_AM_LIMITED_LICENSE_EVENT_PASS command=37 full_license=1 event_unsignaled=1 exact_reverse=ca0407f9")
