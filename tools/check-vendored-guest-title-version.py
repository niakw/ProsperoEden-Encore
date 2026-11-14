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
raw = selected.read_bytes()
assert hashlib.sha1(b"blob "+str(len(raw)).encode()+bytes([0])+raw).hexdigest() == "b8787c322258fcccd7c5d53a74097a5619e2211c"
source = raw.decode()
assert source.index("R_TRY(app_man->ConvertApplicationLanguageToLanguageCode(out_language_code, desired_language));") < source.index("const GuestLanguageReply reply{")
assert "EDEN_GUEST_LANGUAGE_REPLY title=" in source
assert "emitted >= 32" in source
assert 'set(EDEN_SHARED_NS2_AM ON)' in cmake
assert 'list(APPEND eden_ns2_am_sources "${EDEN_NS2_AM_ROOT}/core/hle/service/am/service/application_functions.cpp")' in cmake
print("SHARED_NATIVE_AM_LANGUAGE_REPLY_SOURCE_PASS exact_blob=1 real_return=1 bounded=32 native_execution=0")
