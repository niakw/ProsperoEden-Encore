#!/usr/bin/env python3
"""Fail closed if any of the three reviewed release owner contracts drift.

This is a selection/source audit, not an FPS benchmark or console test.
"""
from pathlib import Path
import hashlib

root=Path(__file__).resolve().parents[2]
paths={
 "sm": "vendor/encore-active/eden-core/src/core/hle/service/sm/sm.h",
 "thread": "vendor/encore-active/eden-threading/src/core/hle/kernel/k_thread.h",
 "jit": "vendor/encore-active/eden-core/src/dynarmic/backend/x64/a64_interface_standard.cpp",
}
expected={
 "sm": "afaad1b58658c9fe7807756410b7f1a82d0e3c7d",
 "thread": "89bbcbd2b0d3627210a980496d00f30a45c7d944",
 # J10 was a "reviewed without edit" historical source. The JIT drain
 # is now a source correction; retain the old hash below as provenance and
 # pin the new reviewed source with the source-extracted reentrant witness.
 "jit": "aaff079cedf068b1d032af6cb3abc5f8b5e72178",
}
# The Lichii/Eglantine AM/LM vendor successor carries the previously
# audited FC27 SM/NVDRV shutdown interface. Keep the old literal baseline
# for older vendors; require the exact new SM header blob on selected main.
import subprocess
pin = subprocess.check_output(["git","rev-parse","HEAD:vendor"], cwd=root, text=True).strip()
if pin in {"6affc4ad869a3eaab9d1bed1e65de8872d93363b", "b92d4183cec69e65216162cf61e451eff643caa0", "84d3b0398ae7db1618899815bc1f98894453fbf6", "1949a57c930d3ebd32bdd93093763ae22681a4a4", "2ecccebce83cd169f1820d9c4674698f6353fa48", "d40e212b2c8124225ff8d6adc06f459955e42a6a", "b3458252ec923444b3add94ff50a4a76e2bc4570", "f3322eb09b8b4bbf1c589d1e96ff454cd5fb2c5d", "bc94e99cbedd19b3f6bc75aff02a9b5b914d5189", "f337bb8c0484fef5b9a2d763b9775566ff797eef", "da339b1393d1386bc6af667d243e97860a40d096", "5ddd9d778b2fab5e7e8a29cac44aa0c80e4df015", "94d352bdc9b2ee8e6ea0881d85f4673585b98bf4", "be9e46213070e5cb57a7dbd8a184ffb480106b4f", "096761112103fac069b56a22c77f07492001e26e", "fa76dceebca2fae6acbf2b2a6b9840061e07ecc6", "df6a83b4ad06a689674e111a793995663a8d4eb3", "db9c5e6725264412218c3cabdb1d284e6dcb8a5f", "d254110d5551a246530a3665995e876e752e7565", "2af2f2c4bfccfcb53a5a1099844e36fa5dd9756a", "22a5ccda624de9c42f5c772f39844242621c9289", "dc47b157c607c739b43f67aecbf36448507b9557", "f4a90f02ad5383998d08b45cca534d1b73b166c1", "47f91da1f0179652eecbff150e09a4ddb6122157"} or pin in {"0390980a5752808dfba7b8edaa7d113cc4e4e6eb", "273680a5b33bff15c9ca12685cfadb2aa15ff9f1", "84b9975726092a32d1cb2aa714b96e4f5f85d7c4", "84ec89ce112b83603b2095a9f6bb785f8e999ef6", "97fa38381d9ce23b63b3bf3751615dc254ab3634", "b099bd7cbefaa1a35d6626d4fd3161afcefa1b48", "bfdf39014db15f237a16d4a50e6cdfd68bdd87b8", "4626d87be155c0b42904610323098c1205515450", "c32704e63844449b1c18a03deb2cd92939999b90", "fab5ebbfda09ebd3fc414b3127e135c66025ccb8", "acb42e2a2b18fee17673d07e06b2f29709de2fb5", "99df05ff50a7a4a9591c17b08f4ed0f8cb0374a3", "04e252186aa42bacde0899e0c9224035c83a6b0d", "44f5b75bc93bcea146ad6fba3ac294405ae8709b", "70789b12dea4d72ce9e7f054c5b6f552ec488f5d", "9db97fb12db1a390d6b2410f0c18333aa31e37da", "b5c6f089a6aecd321d08a40238f3cd502f505b26", "dc9f5f95b1f784bb358d6480e53de7247d61d777", "a441295022b23834f8531c54d2b0965f84023278", "7c5d5220dd4df4a531418458ab623ef86c41348c", "44540549ee9a65eb8078e271f43ccded0e8e984f", "d63d82dfb9c2afbacac4c9dc1491f743fb083d52", "d634b381d85dae30492dd6291fc4e6e96143f363", "3522d8578fbcd7b46d2a439d5d718dfb570beb7b", "042204fde8e5b74aa5048c6213a8af4450d26fe5", "294442004543aeecc5f3c61cc1b73b2feaff2f92", "53d0ad1f9d50b9f1a72cbecacdacdff7fb4e69eb", "7e137d362f9679125726ef4876355a09d788795e", "973d45ae0da5d9612d30900e39118d67d039b31a", "6b8fd06606f12be187f73e8809e56a49864794f9", "652f88555e8bb16ffeffd9d1fa3d0c49e7925dfc", "38e19d4be0d99bbba35558af2c0620cd9b46f12e", "4c51642038c4a3cc04c0f8f0b8267b17aafd4045", "881f6fb23c818ecfc387d2b134e1cd7328fc5995", "d8155325107dbbb1f8ef44f75553595fe4c8ec8c", "101eae5edb76fefc40b039009eb35bbaaae99386", "3abd88bc1a3c334f53f345998b72e9cf8ae87abf"}:
    expected["sm"] = "7069439e66a6f28ffa56229e08906a21222e2801"

def gitblob(data: bytes)->str:
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()
# Historical pre-pressure-rollback source: 26ae49088a528c4cf27712f639948604de2260d4.
# Reviewed delta at new SHA: the two unprotected invalidate_entire_cache=true
# writes on low JIT code-space and bad_alloc now use ClearCache(), which
# publishes under invalidation_mutex. The source-extracted host witness
# checks both paths and reentrant guest requests.
JIT_PREVIOUS_REVIEW_BLOB = "20362a046adfe89d65225c1822104f2910eeb2c5"
THREAD_PREVIOUS_REVIEW_BLOB = "e2f359a54cb6b879bdd41f092cf1ea19fb03e4e6"
SM_PREVIOUS_REVIEW_BLOB = "83e0b7e26a867d578eb869389a807fe3b9c7035b"
assert expected["jit"] != JIT_PREVIOUS_REVIEW_BLOB
assert expected["thread"] != THREAD_PREVIOUS_REVIEW_BLOB
assert expected["sm"] != SM_PREVIOUS_REVIEW_BLOB
sources={key:(root/path).read_text() for key,path in paths.items()}
for key,path in paths.items():
    assert gitblob((root/path).read_bytes())==expected[key], (key,"source changed; re-audit")
sm=sources["sm"]
for invariant in (
 "#include <condition_variable>",
 "bool WaitForService(const std::string& name);",
 "void Close();",
 "bool closing{};",
 "u32 service_waiters{};",
 "std::condition_variable waiters_changed;",
):
    assert invariant in sm, invariant
getter=sm.split("std::shared_ptr<T> GetService(",1)[1].split("\n    void InvokeControlRequest(",1)[0]
for invariant in (
 "std::scoped_lock l{lock};",
 "const auto it = registered_services.find(name);",
 "factory = it->second;",
 "std::static_pointer_cast<T>(factory())",
 "Kernel::GetCurrentThread(kernel).IsDummyThread()",
 "std::this_thread::sleep_for(1ms);",
 "Kernel::Svc::SleepThread(",
):
    assert invariant in getter,invariant
assert getter.index("factory = it->second;")<getter.index("std::static_pointer_cast<T>(factory())")
# Service construction must happen AFTER the block closing the map lock.
assert "}\n            if (factory) {" in getter
assert getter.count("SleepThread(")==1
header=sources["thread"]
for invariant in ("std::binary_semaphore m_context_guard{1};",
                  "std::atomic<ThreadState> m_thread_state{};",
                  "m_dummy_thread_cv{}", "m_dummy_thread_mutex{}",
                  "std::vector<KThread*>& GetPendingStartedThreads()",
                  "std::vector<KThread*> m_pending_started_threads;"):
    assert invariant in header, invariant
thread_cmake=(root/"vendor/encore-active/eden-threading/native-hle-overrides.cmake").read_text()
scheduler=(root/"vendor/encore-active/eden-threading/src/core/hle/kernel/k_scheduler.cpp").read_text()
assert "if(EDEN_BLOCKING_GUEST_CONTEXT_LOCKS)" in thread_cmake
assert 'target_include_directories(core BEFORE PUBLIC "${_encore_thread_root}")' in thread_cmake
assert "m_context_guard.try_acquire()" in scheduler
assert "m_context_guard.release()" in scheduler
jit=sources["jit"]
for invariant in ("#if defined(EDEN_JIT_A64_BATCH)",
                  "#if defined(EDEN_JIT_A64_DEV_PROFILE)",
                  "std::unique_lock lock{invalidation_mutex};",
                  "block_of_code.ClearCache();",
                  "emitter.InvalidateCacheRanges(ranges);",
                  "ranges.swap(invalid_cache_ranges);",
                  "clear_all = invalidate_entire_cache;",
                  "invalidate_entire_cache = false;",
                  "if (length - 1 > (~u64{0} - start_address))"):
    assert invariant in jit,invariant
assert jit.index("ranges.swap(invalid_cache_ranges);") < jit.index("emitter.InvalidateCacheRanges(ranges);")
assert jit.count("Publish the full-clear request under invalidation_mutex;") == 2
assert "emitter.InvalidateCacheRanges(invalid_cache_ranges);" not in jit
# Reviewed source must be tied to a HOST proof, not just a new opaque digest.
proof = (root/"tools/check-native-jit-invalidation-snapshot-host.py").read_text()
assert "PerformRequestedCacheInvalidation" in proof
assert "invalid_cache_ranges" in proof and "p.InvalidateCacheRange(" in proof
cmake=(root/"headless/CMakeLists.txt").read_text()
# The production CMake selects one maintained standard A64 JIT TU.
# Historical shared/batch/DEV variants remain source-level witnesses above;
# none may be introduced as another executable profile. The normal JIT
# retains the reviewed full-clear/invalidation fixes and host proof.
for invariant in (
    'set(EDEN_A64_INTERFACE_UNIT "${EDEN_A64_INTERFACE_ROOT}/a64_interface_standard.cpp")',
    'configure_file("${EDEN_A64_INTERFACE_UNIT}" "${PORT_BUILD_DIR}/a64_interface.cpp" COPYONLY)',
    'set(EDEN_G11_PROFILE normal)',
    'EDEN_JIT_COMPILE_BATCH_AVAILABLE=0',
    'EDEN_SHARED_JIT_AVAILABLE=0',
    'if(EDEN_A32_FASTMEM)',
):
    assert invariant in cmake,invariant
for obsolete in ('a64_interface_shared.cpp', 'EDEN_JIT_A64_BATCH=1',
                 'EDEN_JIT_A64_DEV_PROFILE=1', 'EDEN_DEV_PROFILE',
                 'EDEN_FINAL_RELEASE_PROFILE'):
    assert obsolete not in cmake, obsolete
assert 'option(EDEN_BLOCKING_GUEST_CONTEXT_LOCKS' in cmake
preflight=(root/".github/workflows/encore-core-preflight.yml").read_text()
for path in ("tools/check-maintained-a64-interface.py",
             "tools/check-native-a64-cache-invalidation-host.py",
             "tools/check-native-jit-invalidation-snapshot-host.py",
             "tools/verify/hle/check-hle-overlay-layout.py",
             "tools/check-native-hle-suspend-noop-host.py",
             "tools/install-active-core-backports.py"):
    assert "python3 -B "+path in preflight,path
assert "python3 -B tools/ci/check-final-engine-owner-contracts.py" in preflight
print("ENCORE_FINAL_ENGINE_OWNERS_PASS standard_JIT_only=1 host_SM_lock_safe=1 context_permit=1 source_hashes=3 jit_fix_witness=1")
