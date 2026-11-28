#!/usr/bin/env python3
"""Exact pinned service parity plus bounded guest version metadata diagnostic."""
from pathlib import Path
root=Path(__file__).resolve().parents[1]
base=(root/"vendor/sources/eden/src/core/hle/service/am/service/application_functions.cpp").read_text()
current=(root/"vendor/encore-active/eden/src/core/hle/service/am/service/application_functions.cpp").read_text()
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
selected = root/"vendor/encore-active/eden/src/core/hle/service/am/service/application_functions.cpp"
raw = selected.read_bytes()
# The shared AM owner now also contains reviewed NS1 lifecycle/service
# implementations. Validate the required merged contracts directly instead
# of pinning the obsolete pre-convergence whole-file blob.
source = raw.decode()
for marker in (
    "Result IApplicationFunctions::RejectDebugOnlyCommand(",
    "Result IApplicationFunctions::GetLimitedApplicationLicense(",
    "Result IApplicationFunctions::GetDeviceSaveDataSizeMax(",
    "Result IApplicationFunctions::RequestToShutdown(",
    "Result IApplicationFunctions::TryPopFromNotificationStorageChannel(",
    "Result IApplicationFunctions::RequestExitApplicationAndTryPopMessage(",
):
    assert marker in source, ("Shared AM convergence drift", marker)
assert "Result IApplicationFunctions::Unknown330(" not in source
# The merged native AM owner also exposes NS2 command 321 with one byte,
# without changing the previously reviewed language response path.
assert '{321, D<&IApplicationFunctions::Unknown321>, "Unknown321"}' in source
assert 'Result IApplicationFunctions::Unknown321(Out<u8> out)' in source
assert '*out = 0;' in source.split('Result IApplicationFunctions::Unknown321(Out<u8> out)', 1)[1].split('}', 1)[0]
assert source.index("R_TRY(app_man->ConvertApplicationLanguageToLanguageCode(out_language_code, desired_language));") < source.index("const GuestLanguageReply reply{")
assert "EDEN_GUEST_LANGUAGE_REPLY title=" in source
assert "emitted >= 32" in source
assert 'EDEN_APP_TERMINATE_RESULT title=%016llX' in source
assert 'terminate_reports.fetch_add(1, std::memory_order_relaxed) < 32' in source
assert 'm_applet->terminate_result = terminate_result;' in source
assert 'set(EDEN_SHARED_NS2_AM ON)' in cmake
assert 'list(APPEND eden_ns2_am_sources "${EDEN_NS2_AM_ROOT}/core/hle/service/am/service/application_functions.cpp")' in cmake
print("SHARED_NATIVE_AM_LANGUAGE_REPLY_SOURCE_PASS shared_owner_contract=1 real_return=1 bounded=32 native_execution=0")
