#!/usr/bin/env python3
"""Fail early if the PS5-selected NS2 pseudo-device UUID call drifts from its real owner ABI."""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
vendor = root / "vendor/encore-active"
header = (vendor / "eden-core/include/common/uuid.h").read_text()
implementation = (vendor / "eden-core/src/common/uuid.cpp").read_text()
ns2 = (vendor / "ns2-runtime/am/core/hle/service/am/service/application_functions.cpp").read_text()

def exactly_one(contents, fragment, path):
    if contents.count(fragment) != 1:
        raise SystemExit(f"UUID_ABI_DRIFT {path}: expected exactly one {fragment!r}")

# A valid SHA-1 digest is 20 bytes; the maintained UUID helper explicitly
# consumes its first 16 bytes and writes a 16-byte UUID. All three selected
# production owners MUST agree, independent of the old immutable Eden archive.
exactly_one(header, "static UUID MakeRFC4122V5(std::span<u8, 16> sha1);", "uuid.h")
exactly_one(implementation, "UUID UUID::MakeRFC4122V5(std::span<u8, 16> sha1)", "uuid.cpp")
exactly_one(implementation, "std::memcpy(&uuid.uuid, sha1.data(), sha1.size());", "uuid.cpp")
exactly_one(ns2, "R_UNLESS(ok && hash_len == 20, ResultUnknown);", "ns2 AM")
exactly_one(
    ns2,
    "Common::UUID::MakeRFC4122V5(std::span<u8, 16>{hash, 16});",
    "ns2 AM",
)
print("NS2_NATIVE_UUID_ABI_PASS sha1=20 UUID=16 owners=3")
