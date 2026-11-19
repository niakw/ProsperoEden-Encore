#!/usr/bin/env python3
"""Validate the machine-readable NS2/PS5 compatibility catalogue against selected source owners.

This is a host/source gate. It deliberately rejects absolute game addresses:
those are runtime mapping state, not portable compatibility data.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "docs/audits/NS2_PS5_COMPATIBILITY_CATALOG.json"


def fail(message: str) -> None:
    raise AssertionError(message)


def main() -> None:
    data = json.loads(CATALOG.read_text())
    if data.get("schema_version") != 2:
        fail("unexpected compatibility catalogue schema")

    policy = data["generated_policy"]
    if policy.get("absolute_guest_addresses") != "runtime_only":
        fail("guest absolute addresses must remain runtime-only")
    if policy.get("absolute_gpu_addresses") != "runtime_only":
        fail("GPU absolute addresses must remain runtime-only")

    stable = data["stable_abi"]
    expected = {
        "native_page_size": 4096,
        "ampere_storage_buffers": 32,
        "ns2_cpu_cores": 6,
        "native_texture_address_bits": 49,
        "ns2_alias_region_gib": 64,
    }
    for key, value in expected.items():
        if stable.get(key) != value:
            fail(f"stable ABI drift: {key}={stable.get(key)!r}")

    classes = {value.upper() for value in stable.get("ampere_engine_classes", [])}
    if classes != {"0XC797", "0XC7C0", "0XC7B5", "0XC56F"}:
        fail(f"Ampere class list drift: {sorted(classes)}")

    capabilities = data["capabilities"]
    for name, capability in capabilities.items():
        implemented = capability.get("implemented")
        if implemented is True:
            owners = capability.get("owners")
            if not isinstance(owners, dict) or not owners:
                fail(f"{name}: implemented capability has no source owners")
            for relative, needles in owners.items():
                path = ROOT / relative
                if not path.is_file():
                    fail(f"{name}: missing selected owner {relative}")
                source = path.read_text(errors="strict")
                if not needles:
                    fail(f"{name}: {relative} has no contract needles")
                for needle in needles:
                    if needle not in source:
                        fail(f"{name}: selected owner {relative} lost {needle!r}")
        elif implemented is False:
            if "upstream" not in capability or "reason" not in capability:
                fail(f"{name}: explicit gap must retain upstream evidence and reason")
        else:
            fail(f"{name}: implemented must be boolean")

    required_by_games: set[str] = set()
    for title_id, game in data["known_games"].items():
        if len(title_id) != 16 or any(c not in "0123456789ABCDEF" for c in title_id):
            fail(f"invalid title id {title_id!r}")
        if game.get("generation") != "NS2":
            fail(f"{title_id}: this catalogue currently accepts NS2 profiles only")
        required = game.get("required_capabilities", [])
        if not required:
            fail(f"{title_id}: empty capability profile")
        for capability in required:
            required_by_games.add(capability)
            if capability not in capabilities:
                fail(f"{title_id}: unknown capability {capability}")
            if capabilities[capability].get("implemented") is not True:
                fail(f"{title_id}: requires unimplemented capability {capability}")

    if "gamefile_shader_warm_extract" in required_by_games:
        fail("static shader extraction is not yet a shipping compatibility requirement")

    future = data.get("future_profiles", {})
    if not isinstance(future, dict) or not future:
        fail("future NS2 profiles must remain explicit")
    for title_id, profile in future.items():
        if len(title_id) != 16 or any(c not in "0123456789ABCDEF" for c in title_id):
            fail(f"invalid future title id {title_id!r}")
        if profile.get("generation") != "NS2":
            fail(f"{title_id}: future catalogue accepts NS2 profiles only")
        if profile.get("console_validated") is not False:
            fail(f"{title_id}: source/upstream profile must not claim console validation")
        refs = profile.get("upstream_refs")
        if not isinstance(refs, list) or not refs:
            fail(f"{title_id}: future profile lost pinned upstream evidence")
        required = profile.get("required_capabilities", [])
        if not required:
            fail(f"{title_id}: future profile has no capability contract")
        missing = []
        for capability in required:
            if capability not in capabilities:
                fail(f"{title_id}: unknown future capability {capability}")
            if capabilities[capability].get("implemented") is not True:
                missing.append(capability)
        expected_status = "upstream_gap" if missing else "covered_host_only"
        if profile.get("source_status") != expected_status:
            fail(
                f"{title_id}: source_status={profile.get('source_status')!r}, "
                f"expected {expected_status!r} for missing={missing}"
            )

    raw = CATALOG.read_text()
    forbidden_keys = (
        '"absolute_guest_address"',
        '"absolute_gpu_address"',
        '"shader_address"',
        '"texture_address"',
        '"host_pointer"',
    )
    for key in forbidden_keys:
        if key in raw:
            fail(f"catalogue must not persist transient address field {key}")

    primary = data["console_gate"].get("primary", [])
    if len(primary) != 2:
        fail("minimal console gate must remain two primary scenarios")
    if not any("FC27" in item for item in primary) or not any("Mario Kart World" in item for item in primary):
        fail("minimal console gate lost NS1/NS2 coverage")

    print(
        "NS2_PS5_COMPATIBILITY_CATALOG_PASS",
        f"capabilities={len(capabilities)}",
        f"implemented={sum(1 for value in capabilities.values() if value['implemented'])}",
        f"known_games={len(data['known_games'])}",
        f"future_profiles={len(data['future_profiles'])}",
        "console_primary=2",
        "absolute_addresses=runtime_only",
    )


if __name__ == "__main__":
    main()
