#!/usr/bin/env python3
"""Install maintained CPU I-cache and host service-wait sources unconditionally.

Production copies complete checked-in sources from vendor/encore-active.
The two historical patches are replayed only into a temporary comparison
tree to prove byte-for-byte parity. Any difference fails closed.
The quarantined dummy-thread workaround remains excluded (unsafe wait queue).
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = ROOT / "vendor/sources/eden"
ACTIVE = ROOT / "vendor/encore-active/eden"
PATCHES = (
    ROOT / "headless/backports/eden-dynarmic-icache-coherence.patch",
    ROOT / "headless/backports/eden-sm-host-wait.patch",
)
PIN = "5f142c7926d0c7fcbbd0ce30794d72f638a43b2a"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_blob_sha1(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def affected() -> list[str]:
    names = set()
    for patch in PATCHES:
        data = patch.read_text(encoding="utf-8")
        for line in data.splitlines():
            if line.startswith("+++ b/"):
                rel = line[6:]
                if not rel.startswith("src/") or ".." in Path(rel).parts:
                    raise RuntimeError(f"Invalid target in {patch}: {rel}")
                names.add(rel)
    if len(names) != 5:
        raise RuntimeError(f"Expected exactly five core patch sources: {sorted(names)}")
    return sorted(names)


def derive() -> dict[str, tuple[bytes, bytes]]:
    files = affected()
    with tempfile.TemporaryDirectory(prefix="encore-active-core-") as temp:
        stage = Path(temp)
        for relative in files:
            source = ORIGINAL / relative
            target = stage / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        for patch in PATCHES:
            result = subprocess.run(
                ["patch", "--batch", "--fuzz=0", "-p1", "-d", str(stage)],
                input=patch.read_bytes(), capture_output=True, timeout=20,
            )
            if result.returncode:
                raise RuntimeError(
                    f"{patch.name}: pinned source does not accept patch: "
                    f"{result.stderr.decode(errors='replace')[-1200:]} "
                    f"{result.stdout.decode(errors='replace')[-1200:]}"
                )
        result = {}
        for relative in files:
            old = (ORIGINAL / relative).read_bytes()
            new = (stage / relative).read_bytes()
            if old == new:
                raise RuntimeError(f"Unapplied active patch: {relative}")
            result[relative] = (old, new)
        return result


# CI 41258590941 identified one previous local A64 overlay in the disposable
# owned source cache. Recover only that exact SHA-256, never arbitrary bytes.
KNOWN_STALE_A64_SHA256 = "08ae577aa069b589faaa8cc6659baa66c80661d78abc15381907d63b343c17b0"
A64_OWNER = "src/core/arm/dynarmic/arm_dynarmic_64.cpp"
SM_SOURCE_OWNER = "src/core/hle/service/sm/sm.cpp"
SM_SHIPPING_SOURCE = ROOT / "vendor/encore-active/eden" / SM_SOURCE_OWNER
SM_SHIPPING_GIT_BLOB = "c75c5437dfae5176d25a9994ff8aa7164d8b6713"
SM_SHUTDOWN_PREVIOUS_GIT_BLOB = "494ee50d2880a491b07c2b981193df1a686c696a"
SM_FACTORY_RETIREMENT_GIT_BLOB = "34c7c85f1476a3ba819ad20b8a4f8150cca86e16"
SM_SHUTDOWN_GIT_BLOB = "2ef914e3f1b24442e1fa0130d5f8175111e7d316"
SM_HEADER_OWNER = "src/core/hle/service/sm/sm.h"
SM_HEADER_PREVIOUS_GIT_BLOB = "afaad1b58658c9fe7807756410b7f1a82d0e3c7d"
SM_HEADER_GIT_BLOB = "7069439e66a6f28ffa56229e08906a21222e2801"


def preserve_known_owned_cache_source(destination: Path, target: Path, digest: str) -> None:
    scratch = destination.parent
    owner = scratch / "owner"
    if (digest != KNOWN_STALE_A64_SHA256 or destination.is_symlink() or
            destination.name != "source" or scratch.is_symlink() or
            not scratch.name.startswith("ps5-eden-headless.") or
            not owner.is_file() or owner.is_symlink() or
            owner.read_text().strip() != str(ROOT.resolve()) or
            target.is_symlink() or
            not target.parent.resolve().is_relative_to(destination.resolve())):
        raise RuntimeError("Refusing repair outside the exact owner-stamped A64 cache")
    backup_dir = scratch / ".eden-known-stale-a64"
    if backup_dir.is_symlink():
        raise RuntimeError("Cached A64 backup path is a symlink")
    backup_dir.mkdir(exist_ok=True)
    backup = backup_dir / f"arm_dynarmic_64.cpp.{digest[:16]}"
    if backup.is_symlink():
        raise RuntimeError("Cached A64 backup file is a symlink")
    if not backup.exists():
        with tempfile.NamedTemporaryFile(dir=backup_dir, delete=False) as handle:
            staged = Path(handle.name)
        try:
            shutil.copyfile(target, staged)
            if sha(staged.read_bytes()) != digest:
                raise RuntimeError("Cached A64 bytes changed during backup")
            staged.replace(backup)
        finally:
            staged.unlink(missing_ok=True)
    elif sha(backup.read_bytes()) != digest:
        raise RuntimeError("Cached A64 backup has a different SHA-256")
    print(f"EDEN_KNOWN_STALE_A64_PRESERVED sha256={digest}", flush=True)


def normalize_sm_factory_retirement(data: bytes) -> bytes:
    """Replay the exact NVDRV-last successor (6d9fc808) for provenance only."""
    if git_blob_sha1(data) == SM_FACTORY_RETIREMENT_GIT_BLOB:
        return data
    if git_blob_sha1(data) != SM_SHUTDOWN_GIT_BLOB:
        raise RuntimeError("Shutdown SM owner drift")
    header = b"#include <array>\n"
    successor = "void ServiceManager::ReleaseRegisteredHandlersForShutdown() {\n    // Closing/waking host service waiters and joining their work happens first.\n    // Keep SM itself and its kernel-owned ports alive until process shutdown,\n    // but retire factories (NVDRV included) while KProcess/Host1x still exist.\n    decltype(registered_services) retired;\n    {\n        std::unique_lock l{lock};\n        if (!closing || service_waiters != 0) {\n            LOG_ERROR(Service_SM, \"Refusing to retire service handlers before SM close\");\n            return;\n        }\n        retired.swap(registered_services);\n    }\n    // GPU supervisor / worker factories may hold an AS shared_ptr after its\n    // originating NVDRV FD closes. nvhost_as_gpu references Module::Container\n    // and NvMap: destroying NVDRV first leaves those references dangling, and\n    // later AS retirement tries to lock an already-destroyed mutex. Retire all\n    // other service factories before the three NVDRV aliases. Service loops\n    // are already joined and the kernel/Host1x remain alive. Moving the\n    // std::function owners costs no allocations and keeps this out of SM's lock.\n    std::array<SessionRequestHandlerFactory, 3> nvdrv_keepers{};\n    for (auto& [name, factory] : retired) {\n        if (name == \"nvdrv\") {\n            nvdrv_keepers[0] = std::move(factory);\n        } else if (name == \"nvdrv:a\") {\n            nvdrv_keepers[1] = std::move(factory);\n        } else if (name == \"nvdrv:s\") {\n            nvdrv_keepers[2] = std::move(factory);\n        }\n    }\n    retired.clear();\n    // Only now may NVDRV's module close its NvMap/Container and their mutexes.\n    for (auto& factory : nvdrv_keepers) {\n        factory = {};\n    }\n}\n\n"
    predecessor = "void ServiceManager::ReleaseRegisteredHandlersForShutdown() {\n    // Closing/waking host service waiters and joining their work happens first.\n    // Keep SM itself and its kernel-owned ports alive until process shutdown,\n    // but retire factories (NVDRV included) while KProcess/Host1x still exist.\n    decltype(registered_services) retired;\n    {\n        std::unique_lock l{lock};\n        if (!closing || service_waiters != 0) {\n            LOG_ERROR(Service_SM, \"Refusing to retire service handlers before SM close\");\n            return;\n        }\n        retired.swap(registered_services);\n    }\n    // A factory may own an NVDRV handler -> module -> nvhost_as_gpu. The latter\n    // calls KProcess::Close and must never run after ShutdownCores. Destroy\n    // OUTSIDE SM's lock because final release can re-enter service cleanup.\n    retired.clear();\n}\n\n"
    successor_bytes = successor.encode("utf-8")
    predecessor_bytes = predecessor.encode("utf-8")
    if data.count(header) != 1 or data.count(successor_bytes) != 1:
        raise RuntimeError("SM NVDRV-last successor shape drift")
    restored = data.replace(header, b"", 1).replace(successor_bytes, predecessor_bytes, 1)
    if git_blob_sha1(restored) != SM_FACTORY_RETIREMENT_GIT_BLOB:
        raise RuntimeError("SM NVDRV-last successor modified unrelated source")
    return restored


def stage_selected_sm_source(destination: Path, *, check: bool) -> bool:
    """Keep the shutdown-aware SM header and implementation under one owner."""
    target = destination / SM_SOURCE_OWNER
    maintained = ACTIVE / SM_SOURCE_OWNER
    predecessor = SM_SHIPPING_SOURCE
    if not target.is_file() or target.is_symlink():
        raise RuntimeError("Missing staged SM source")
    if not maintained.is_file() or not predecessor.is_file():
        raise RuntimeError("Missing reviewed SM source owner")
    maintained_bytes = maintained.read_bytes()
    predecessor_bytes = predecessor.read_bytes()
    if git_blob_sha1(predecessor_bytes) != SM_SHIPPING_GIT_BLOB:
        raise RuntimeError("Shipping SM predecessor drift")
    historical = normalize_sm_factory_retirement(maintained_bytes)
    # The current SM factory-retirement owner is an exact successor of the
    # reviewed close/wait implementation. Seal its unchanged predecessor too.
    begin = b"void ServiceManager::ReleaseRegisteredHandlersForShutdown() {\n"
    end = b"ServiceManager::~ServiceManager() {"
    if historical.count(begin) != 1 or historical.count(end) != 1:
        raise RuntimeError("SM handler retirement source shape drift")
    first = historical.index(begin)
    last = historical.index(end, first)
    if git_blob_sha1(historical[:first] + historical[last:]) != SM_SHUTDOWN_PREVIOUS_GIT_BLOB:
        raise RuntimeError("SM handler retirement changed unrelated source")
    current = target.read_bytes()
    if current == maintained_bytes:
        return False
    if check:
        raise RuntimeError(
            f"Active SM source check found predecessor: current={git_blob_sha1(current)} "
            f"active={SM_SHUTDOWN_GIT_BLOB}"
        )
    if current != predecessor_bytes and git_blob_sha1(current) not in (
            SM_SHUTDOWN_PREVIOUS_GIT_BLOB, SM_FACTORY_RETIREMENT_GIT_BLOB):
        raise RuntimeError(
            f"Refusing unknown staged SM source: current={git_blob_sha1(current)} "
            f"shipping={SM_SHIPPING_GIT_BLOB}"
        )
    with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as handle:
        tmp = Path(handle.name)
    try:
        shutil.copyfile(maintained, tmp)
        tmp.replace(target)
    finally:
        tmp.unlink(missing_ok=True)
    return True


def stage_source(destination: Path, expected: dict[str, tuple[bytes, bytes]], *, check: bool, repair_owned_cache: bool = False) -> None:
    if (destination / "GIT-COMMIT").read_text().strip() != PIN:
        raise RuntimeError("Wrong pinned core revision")
    changed = 0
    for relative, (old, new) in expected.items():
        target = destination / relative
        # The old patches are replayed to a temporary tree as a parity oracle.
        # The source installed into the native build comes only from Encore.
        maintained = ACTIVE / relative
        if not maintained.is_file():
            raise RuntimeError(f"Missing maintained active-core source: {relative}")
        maintained_bytes = maintained.read_bytes()
        if maintained_bytes != new:
            if relative == SM_HEADER_OWNER:
                # The shutdown-lifetime successor extends the already-reviewed
                # host-wait header only. Reverse those exact additive pieces
                # and require byte-for-byte parity with the patch oracle.
                if git_blob_sha1(maintained_bytes) != SM_HEADER_GIT_BLOB:
                    raise RuntimeError("SM handler retirement header drift")
                declaration = (
                    b"    // Drop service-owned guest/device references before guest KProcesses retire.\n"
                    b"    // Does not destroy SM ports or the SM object itself.\n"
                    b"    void ReleaseRegisteredHandlersForShutdown();\n"
                )
                if maintained_bytes.count(declaration) != 1:
                    raise RuntimeError("SM handler retirement declaration drift")
                shutdown = maintained_bytes.replace(declaration, b"", 1)
                if git_blob_sha1(shutdown) != SM_HEADER_PREVIOUS_GIT_BLOB:
                    raise RuntimeError("SM handler retirement header predecessor drift")
                additions = (
                    (b"#include <condition_variable>\n", b""),
                    (b"    bool WaitForService(const std::string& name);\n"
                     b"    void Close();\n\n", b""),
                    (b"    bool closing{};\n"
                     b"    u32 service_waiters{};\n"
                     b"    std::condition_variable waiters_changed;\n\n", b""),
                )
                for added, replacement in additions:
                    if shutdown.count(added) != 1:
                        raise RuntimeError("SM shutdown successor shape drift")
                    shutdown = shutdown.replace(added, replacement, 1)
                if shutdown != new:
                    raise RuntimeError("SM shutdown successor modified unrelated host-wait source")
            elif relative == "src/core/arm/dynarmic/arm_dynarmic_64.cpp":
                # N76 is a guarded, exact additive extension of the canonical
                # A64 JIT source; reject all other source drift.
                header = "#ifdef EDEN_NS2_GUEST_COUNTER\n#include \"encore/guest_counter_policy.h\"\n#endif\n".encode()
                guest_counter = "#ifdef EDEN_NS2_GUEST_COUNTER\n    // Set before JIT is instantiated; never hardcode a game-specific name.\n    config.cntfrq_el0 = static_cast<u32>(Eden::GuestCounter::Rate());\n#else\n    config.cntfrq_el0 = Hardware::CNTFREQ;\n#endif".encode()
                original_counter = b"    config.cntfrq_el0 = Hardware::CNTFREQ;"
                if (maintained_bytes.count(header) != 1 or
                        maintained_bytes.count(guest_counter) != 1 or
                        maintained_bytes.replace(header, b"").replace(
                            guest_counter, original_counter) != new):
                    raise RuntimeError("N76 modified unrelated native A64 source")
            else:
                raise RuntimeError(f"Unreviewed active-core patch drift: {relative}")
        current = target.read_bytes()
        if current == maintained_bytes:
            continue
        # --check is a pure validator: never rewrite a staged source.
        if check:
            raise RuntimeError(
                f"Active source check found non-maintained revision: {relative} "
                f"current={sha(current)} active={sha(maintained_bytes)}"
            )
        if current not in (old, new) and not (
                relative == SM_HEADER_OWNER and
                git_blob_sha1(current) == SM_HEADER_PREVIOUS_GIT_BLOB):
            # Only the exact previously observed pre-N76 cached A64 bytes
            # may be repaired; keep a content-addressed copy for diagnosis.
            if (check or not repair_owned_cache or relative != A64_OWNER or
                    sha(current) != KNOWN_STALE_A64_SHA256):
                raise RuntimeError(
                    f"Active source missing/unknown revision: {relative} "
                    f"current={sha(current)} base={sha(old)} active={sha(maintained_bytes)}"
                )
            preserve_known_owned_cache_source(destination, target, sha(current))
        with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as handle:
            tmp = Path(handle.name)
        try:
            shutil.copyfile(maintained, tmp)
            tmp.replace(target)
        finally:
            tmp.unlink(missing_ok=True)
        changed += 1
    if stage_selected_sm_source(destination, check=check):
        changed += 1
    print(f"EDEN_ACTIVE_CORE_BACKPORTS files={len(expected) + 1} changed={changed} "
          "icache=on service_wait=on sm_shutdown=on dummy_wait=quarantined")



# The immutable Eden archive predates the reviewed AM lifetime fixes.
# These eight full, paired sources are already maintained in the vendor
# snapshot; native preparation must select those exact bytes, not stale
# archive headers or a different layout in another translation unit.
AM_SOURCE_ROOT = Path("src/core/hle/service/am")
AM_SOURCE_BLOBS = {
    "applet.h": ("571fa65219ca27e56c27abc21ad2e0f4aef5d299", "a8309188928c796d439cd828b756e481f3f6fa2c"),
    "applet_manager.cpp": ("05bcf6cc05810f46dece33292b8f9411ca026dd9", "f16d7c2585595d91e89ff34f3223e0b8fe905220"),
    "applet_manager.h": ("2b0714adf74a6ce70fe1485e55c2c2ffd51591ef", "9724a70f172cbb48130f5c1bfa8703cac119a3cb"),
    "event_observer.cpp": ("520000b64f224c1ca0de4e23910e94b84e524929", "4a132abde4b6e70407b3267ea2298e8a6f0ce239"),
    "event_observer.h": ("c66eb711c8c898241cabc1e0b401c9a272948ddd", "2213d4bac622dc1476a4f1821e2e4fdfe6096acd"),
    "process_holder.cpp": ("21ef5bf838ea6661d7eb3cf1ce0019cfb21a8201", "deb72de87cbb46c158a88e84eb2ef5c692079dd7"),
    "process_holder.h": ("3a9b81dfb4d98087bbd06884a7c2097afb4d95b1", "a2df53cbd7c25ed43cdf9cd97f453e65816c7202"),
    "window_system.h": ("824ae14a1d4bde11aad7e4151059ef5577d011d8", "d29e37adff7b62e790b26c4b5eba0d9ac667ad92"),
}


def stage_selected_am_sources(destination: Path, *, check: bool,
                              repair_owned_cache: bool = False) -> int:
    if (destination / "GIT-COMMIT").read_text().strip() != PIN:
        raise RuntimeError("Wrong pinned AM source revision")
    scratch = destination.parent
    owner = scratch / "owner"
    owned = (repair_owned_cache and not destination.is_symlink() and
             destination.name == "source" and not scratch.is_symlink() and
             scratch.name.startswith("ps5-eden-headless.") and
             owner.is_file() and not owner.is_symlink() and
             owner.read_text().strip() == str(ROOT.resolve()))
    pending = []
    for name, (previous, expected) in AM_SOURCE_BLOBS.items():
        relative = AM_SOURCE_ROOT / name
        maintained = ORIGINAL / relative
        target = destination / relative
        if (not target.is_file() or target.is_symlink() or
                not target.parent.resolve().is_relative_to(destination.resolve())):
            raise RuntimeError(f"Missing or unsafe staged AM source: {relative}")
        data = maintained.read_bytes()
        if git_blob_sha1(data) != expected:
            raise RuntimeError(f"Unreviewed maintained AM source drift: {relative}")
        current = target.read_bytes()
        if current == data:
            continue
        if check:
            raise RuntimeError(f"Staged AM source mismatch: {relative}")
        # Exact reviewed predecessor is safe to replace anywhere. An older
        # archive/cache version can ONLY be replaced in our owned scratch,
        # after retaining its original bytes. Never compile unknown bytes.
        if git_blob_sha1(current) != previous and not owned:
            raise RuntimeError(f"Refusing unknown staged AM source: {relative}")
        pending.append((relative, target, current, data))

    # Validate the whole ABI family before writing any member.
    for relative, target, current, data in pending:
        if target.read_bytes() != current:
            raise RuntimeError(f"Concurrent AM cache modification: {relative}")
        if owned:
            backup_root = scratch / ".eden-stale-am-backup"
            if backup_root.is_symlink():
                raise RuntimeError("Unsafe AM backup directory")
            backup_root.mkdir(exist_ok=True)
            backup = backup_root / (relative.name + "." + sha(current))
            if backup.is_symlink():
                raise RuntimeError("Unsafe AM backup file")
            if not backup.exists():
                with tempfile.NamedTemporaryFile(dir=backup_root, delete=False) as out:
                    saved = Path(out.name)
                    out.write(current)
                try:
                    saved.replace(backup)
                finally:
                    saved.unlink(missing_ok=True)
            if backup.read_bytes() != current:
                raise RuntimeError(f"AM backup mismatch: {relative}")
        with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as out:
            staged = Path(out.name)
            out.write(data)
        try:
            staged.replace(target)
        finally:
            staged.unlink(missing_ok=True)
    print(f"EDEN_ACTIVE_AM_SOURCES files={len(AM_SOURCE_BLOBS)} changed={len(pending)} check={check}")
    return len(pending)


def check_am_materializer() -> None:
    with tempfile.TemporaryDirectory(prefix="ps5-eden-headless.am-test-") as temp:
        scratch = Path(temp)
        destination = scratch / "source"
        destination.mkdir()
        (scratch / "owner").write_text(str(ROOT.resolve()) + "\n")
        (destination / "GIT-COMMIT").write_text(PIN + "\n")
        stale = b"disposable archive-era AM fixture\n"
        for name in AM_SOURCE_BLOBS:
            target = destination / AM_SOURCE_ROOT / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(stale + name.encode())
        # Unowned/unknown source must fail before any replacement.
        try:
            stage_selected_am_sources(destination, check=False)
        except RuntimeError as error:
            assert "Refusing unknown staged AM source" in str(error)
        else:
            raise AssertionError("Unknown AM source was accepted")
        assert all((destination / AM_SOURCE_ROOT / name).read_bytes() ==
                   stale + name.encode() for name in AM_SOURCE_BLOBS)
        assert stage_selected_am_sources(destination, check=False,
                                         repair_owned_cache=True) == len(AM_SOURCE_BLOBS)
        assert stage_selected_am_sources(destination, check=True) == 0
        assert stage_selected_am_sources(destination, check=False) == 0
        for name in AM_SOURCE_BLOBS:
            old = stale + name.encode()
            assert (scratch / ".eden-stale-am-backup" /
                    (name + "." + sha(old))).read_bytes() == old
        print("EDEN_ACTIVE_AM_STAGE_REPLAY_PASS files=8 owned_cache=1 unknown_rejected=1 idempotent=1")

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("destination", nargs="?", type=Path)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--repair-owned-cache", action="store_true")
    args = parser.parse_args()
    expected = derive()
    if args.destination:
        stage_source(args.destination, expected, check=args.check,
                     repair_owned_cache=args.repair_owned_cache)
        stage_selected_am_sources(args.destination, check=args.check,
                                  repair_owned_cache=args.repair_owned_cache)
    else:
        check_am_materializer()
        # Exercise the production materializer as well as the historical
        # patch replay. Use only disposable exact pinned inputs, no SDK/build.
        with tempfile.TemporaryDirectory(prefix="encore-active-core-stage-") as temp:
            destination = Path(temp)
            (destination / "GIT-COMMIT").write_text(PIN + "\n")
            for relative, (old, _) in expected.items():
                target = destination / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(old)
            sm_target = destination / SM_SOURCE_OWNER
            sm_target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(SM_SHIPPING_SOURCE, sm_target)
            stage_source(destination, expected, check=False)
            stage_source(destination, expected, check=True)
            stage_source(destination, expected, check=False)
            # Reproduce the exact previous shutdown owner in a restored cache.
            header_target = destination / SM_HEADER_OWNER
            header = header_target.read_bytes()
            declaration = (
                b"    // Drop service-owned guest/device references before guest KProcesses retire.\n"
                b"    // Does not destroy SM ports or the SM object itself.\n"
                b"    void ReleaseRegisteredHandlersForShutdown();\n"
            )
            previous_header = header.replace(declaration, b"", 1)
            assert git_blob_sha1(previous_header) == SM_HEADER_PREVIOUS_GIT_BLOB
            header_target.write_bytes(previous_header)
            body = sm_target.read_bytes()
            factory_body = normalize_sm_factory_retirement(body)
            first = factory_body.index(b"void ServiceManager::ReleaseRegisteredHandlersForShutdown() {\n")
            last = factory_body.index(b"ServiceManager::~ServiceManager() {", first)
            previous_body = factory_body[:first] + factory_body[last:]
            assert git_blob_sha1(previous_body) == SM_SHUTDOWN_PREVIOUS_GIT_BLOB
            sm_target.write_bytes(previous_body)
            stage_source(destination, expected, check=False)
            stage_source(destination, expected, check=True)
            assert header_target.read_bytes() == header
            assert sm_target.read_bytes() == body
            # A cache from the immediately preceding factory-retirement revision
            # is also admissible; --check must reject it without rewriting it.
            if factory_body != body:
                sm_target.write_bytes(factory_body)
                try:
                    stage_source(destination, expected, check=True)
                except RuntimeError as error:
                    assert "Active SM source check found predecessor" in str(error)
                else:
                    raise AssertionError("Stale SM factory owner passed --check")
                assert sm_target.read_bytes() == factory_body
                stage_source(destination, expected, check=False)
                stage_source(destination, expected, check=True)
                assert sm_target.read_bytes() == body
            # Unknown source bytes must still fail closed.
            sm_target.write_bytes(body + b"\n// unreviewed staging drift\n")
            try:
                stage_source(destination, expected, check=False)
            except RuntimeError as error:
                assert "Refusing unknown staged SM source" in str(error)
            else:
                raise AssertionError("Unknown SM source was accepted")
        print("EDEN_ACTIVE_CORE_STAGE_REPLAY_PASS clean=1 previous=1 idempotent=1 unknown_rejected=1")
        print(f"EDEN_ACTIVE_CORE_PATCH_REPLAY_OK files={len(expected)} "
              "icache=on service_wait=on")
if __name__ == "__main__":
    main()
