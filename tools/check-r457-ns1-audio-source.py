#!/usr/bin/env python3
"""Fail-closed source-owner proof for PS5 native AudioOut (host only).

This is not a PS5 firmware execution or a guest FC27 boot proof.
"""
from pathlib import Path
import hashlib
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "vendor"
# Both exact cross-repo graphs are reviewed. No arbitrary vendor SHA allowed.
KNOWN_VENDOR_GRAPH = {
    "97ac02f263ec90f40a029f4aa62980c76bc25d5c": "reviewed NS2 SVC-only #190 successor; NS1 audio owners are unchanged",
    "1ec7b429238d1175a76dc94b7c0a7f1c2eb62864": "original",
    "fe9edd661d6f0824c7339865d50aa9cf99cab150": "integrated",
    "c339fd06f02e42e67d5416ae82194ba619b7ee68": "integrated+jxr",
    "47568425c71d534b72cc966d1500412c9ae4fc16": "integrated+jxr-cache-page-table",
    "447e08718c9b6625508da6ce63796ed1f4285d2f": "integrated+jxr-cache-page-table-vfs",
    "97fdc316fcf5b42e08c26845887f298feac2a424": "integrated+jxr-cache-page-table-vfs-nca",
    "99ca67babe955398e157c6b28b22a79cbb88967e": "integrated+jxr-cache-page-table-vfs-nca-scalar",
    "7bd7a85e6c1886035c75395c86b05b231375bbf5": "integrated+jxr-cache-page-table-vfs-nca-spirv-romfs",
    "7b42e7f4ba6887fe6d7b539a1d2c50e6782603f6": "integrated+jxr-cache-page-table-vfs-nca-spirv-romfs-bfs",
    "0267753219c4b6a6f3fa086a356b698cd5295f78": "integrated+jxr-cache-page-table-vfs-nca-spirv-romfs-bfs-null-tic",
    "78a903a7479f0f58f3cbd3c2fcfd329012a11e10": "integrated+jxr-cache-page-table-vfs-nca-spirv-romfs-bfs-null-tic-host1x",
    "13ee2fff7be6c0bac225b377a4367b1d0b3073a0": "integrated+jxr-cache-page-table-vfs-nca-spirv-romfs-bfs-null-tic-host1x-geometry-mask",
    "c8e6f2f8dd2b0554e1c7d5bf6e31ef66a9885767": "integrated+jxr-cache-page-table-vfs-nca-spirv-romfs-bfs-null-tic-host1x-geometry-mask-blit",
    "4c252a3f4ccbbdc0ef945727da8c0e4b31a7d028": "integrated+jxr-cache-page-table-vfs-nca-spirv-romfs-bfs-null-tic-host1x-geometry-mask-blit-typed-phi",
    "72faa8edd26f6fcb16b08f321211fb94427c4ebb": "integrated+jxr-cache-page-table-vfs-nca-spirv-romfs-bfs-null-tic-host1x-geometry-mask-blit-typed-phi+am-language-reply",
    "a946785d1ad02752ae47f9b32032e99bdbb53e02": "integrated+jxr-cache-page-table-vfs-nca-spirv-romfs-bfs-null-tic-host1x-geometry-mask-blit-typed-phi+am-language-reply+fc-opus-buffer",
    "db33f8ad0c325c84bd80047d992fafa5c2908151": "same reviewed audio owners + gpu-submit diagnostics + channel-shared-mme-dram",
    "0264f2ae94ef5889e8585171b5bfcb11fd3659ff": "same reviewed audio owners + gpu-submit diagnostics + channel-shared-mme-dram + constant-pool cleanup + NVDEC/VIC witness",
    "bc78a7610425e95d6645685cbd023a67b729ec24": "previous integrated graph + native EmitInvalid parameter cleanup + reviewed branch maintenance metadata",
    "7b7c4d2a37f9b0b248d3f3d6d9cce40596ed0c99": "previous reviewed graph + native MSAA split texture handle fallback",
    "b9f6052a65ef01e23ca4a46ba1654ed3a58cf181": "same reviewed runtime graph + Dynarmic warning cleanup + bounded Bananza/MKW diagnostics",
    "76c5efe8cc6d706e1c2ab0a00ddcce96e2d0adf3": "same reviewed runtime graph + FC27 block-local SSA + SSBO failed-search pruning",
    "6f4bb38594b273fe7cc4fba960dfe62cdb9f508e": "same reviewed runtime graph + FC27 SSA/SSBO/scalar/XMAD/dynamic texture sampler + Bananza low-write + descriptor fastpath",
    "4572e581d011c444fd59428d5c042098f05dcfca": "same final reviewed graph + CPU6 A64 Bananza low-write diagnostic parity",
    "f7ee793f1ee1bb1c2b1a35f68073844163658262": "same reviewed graph + bounded FC27 NVDEC/VIC detailed-log witnesses",
    "3f019c64c2907ac3e84baa9b6200de8898f30636": "same reviewed graph + bounded detailed-only NS2 real-SVC witness",
    "f0324324768bdc090a003079bbf121df862bc7f7": "same reviewed graph + bounded detailed-only NS2 GPFIFO pre-submit witness",
    "0ae51658a5d93e368408cad2484b99083ed7309f": "same reviewed graph + Maxwell PRMT rc/cr default-form candidate",
    "b1bb49abea63b6664e0945df8431e10aac128c2f": "same reviewed audio owners + FC27 memory coherence and NS2 shader/queue candidates",
    "89d70eb505594447b3ca98658311002e74dac8ad": "same production owners + test-only #161 warning-clean host model",
    "b68126c9cd95eef6c6656ff6d7834c62c092aa46": "same production owners + test-only #162 generated-C++ newline correction",
    "0fc157b7ccef428e675ff945bc48eceb08fff607": "same production lineage + upstream-confirmed Maxwell CB_BIND bounds guard #163",
    "42459a7893c51a178ecd0c2f74f3951cc20fa12d": "same reviewed graph + Eden #4559 DrawTexture state successor",
    "d1f8696448ed481e36380c3ea8431e3dc722304e": "same reviewed graph + Eden #4559 DrawTexture plus bounded NS2 AM graphics-scale and HID JCMS owners",
    "c5614d3c7ef75958965bac93c9e343eccdbc0fbe": "same reviewed graph + Lichii #1825 BitFieldUExtract constant-fold UB fix",
    "67926ea4b6960eefebf0427929cf299e8e056013": "same reviewed graph + NS2 GetInfo 29/30 VAMM range + 0x21/33 4 KiB page-size contracts",
    "50a849a93494f442d47573b8ce8b8797c3cecd26": "same reviewed graph + NS2 GetInfo 29/30/33 + GPU-access SVC header parity",
    "2c85d0e8ed192c5eec79423e6be8d883fa0bd7ab": "same reviewed graph + exact native GPU dirty-manager complete-type includes; vendor maintenance/tests only otherwise",
    "053acc8ddf30fe65f6376564bbd6efef58f07ddc": "same reviewed NS1/audio/GPU graph + NS2 A64 RETAA/RETAB maintained owner only",
    "ffa519db0f68fb0d5d2acf791e381c898a34a175": "same reviewed graph + RETAA/RETAB + bounded HTTPS JSON POST active backport; no NS1 audio source change",
    "9e38066a508716fd959477eccf32c7fb2fde3356": "same reviewed NS1/audio owners + PS5 fragment-shuffle fallback; no audio owner change",
    "e298a9b05732346141b685eb4c9850bfa02d9e58": "same reviewed NS1/audio owners + FC27 fragment fallback + targeted NS2 pre-kernel generation; no audio owner change",
    "f7ccfda091fd7429f44159318a07391881a3e7c0": "same reviewed NS1/audio owners; NS2 generation logging only after vendor #182; no audio owner change",
    "92c480e17fedecc21ab4882b76e8507b5aed3771": "same reviewed NS1/audio owners + selected PS5 texture-page publication + NS2 generation receipts; no audio owner change",
    "7039d7752c5d8b1a53db50be0d8f2f7803867e13": "same reviewed NS1/audio owners + selected PS5 texture-page publication + NS2 generation receipts; parser logger bounded to PS5; no audio owner change",
    "d3fca0aa188052f0efd2bad102950aeaeeb36ab0": "same reviewed NS1/audio owners + direct extracted-ExeFS NPDM prekernel resolution; no audio owner change",
    "dfc39fcc087738955b0373b45fa97facdeb2fc47": "same reviewed NS1/audio owners + extracted-ExeFS NPDM + upstream KProcess memory budget; no audio owner change",
    "b806bc497049819e716ef6de81f2a85312b188ce": "same reviewed NS1/audio owners + bounded PS5 KProcess stack/context receipts; no audio owner change",
    "a0e17271e94342c32b02acdc3199c3f258a8aecf": "same runtime owners as merged vendor #183; cleanup-only vendor main successor",
    "772f06c8f5b12fdc81066e61f3db2dedfe3eed81": "same runtime owners as vendor main; security receipt-only successor",
    "568ae541c07691518e9663aa0fc5f3b017a98d53": "same NS1/audio owners plus reviewed PS5 alpha-pipeline and ThreadWorker lost-wake fixes",
    "dcfe3d2384bd800c6139ede672518ea2c66922a6": "same NS1/audio owners plus reviewed PS5 full-clear texture upload elision; audio owners unchanged",
    "697159fd0c183f8a164d0493929ae3b4bcb391d1": "same reviewed graph + NS2 NVK M2MF default-subchannel candidate",
    "d0246caf58a3127597bba1edfc1f8dcbe0c5cfdc": "same byte-sealed NS1/audio owners + reviewed NS2 A64 v8.1-v8.5 and 64GiB-alias/32GiB-VAMM successors",
    "8153654a2f1fe809fb2caa28dcadca90a7661446": "same exact AudioOut owners + reviewed PS5 FC27 deferred buffer-cache publication/race-barrier vendor #194",
    "6c38328fbef33de747f5c31ea30d13541a513a4a": "same byte-sealed AudioOut/FC27 owners + reviewed PS5 A64 64Ki fast-dispatch tables (EglantinePS5 #104)",
    "8e564f61e6c8b86149ce0a0d6d2aa323a268dda6": "same sealed AudioOut/FC27 owners; P0 uniform 16MiB A64 dispatch ABI restored",
    "67759611edc13414c112ea9d2b6664d54827a200": "unchanged sealed NS1/AudioOut owners + reviewed program-index-zero RomFS only",
    "c15cdfe96a3d836bf32ba21b8070088add81cdc9": "same sealed NS1/AudioOut owners + reviewed RomFS and synchronous FC27 page-protection restoration",
    "729f7e5a734b5a890a7bbf3ab60ce1100492af13": "same sealed NS1/AudioOut owners + reviewed quiet NS2 IPC and wait SVC receipts",
    "1a09972eea6f473fda1b714efe84cd52219bf681": "same sealed NS1/AudioOut owners + restored active NS1/NS2 F07 TextureCache lifetime and freshness",
    "3e6647827122c34704c2699a6f5e9b20fff3e9a6": "same sealed NS1/AudioOut owners + F07 BCn-3D unswizzle safety in selected NS1/NS2 runtime",
    "6d64217ea5804fb86dbf57685a3da0cb1d45ba32": "same owners + selected async texture decode zero-fill elimination",
    "3f1fcfef119ca50dd630f0518a7fae1b96c7a85a": "same FC27 owners + NS2 real GPU TIPC-0 handshake compatibility",
    "0e4e96df638fc29c3bd2a8fcfe9f50821c5e5b3a": "same FC27 owners + NS2 TIPC handshake input preservation",
    "9136d2e88c43233bcd029f22bdfda0e5c94a552f": "same C++ owners + corrected token-preservation regression test",
    "75ef34d7ef7f68b5eb4f1c6d0d99b6cbc55742d6": "same FC27 owners + real NS2 VI2 handshake and session rollback",
    "34f02a3800cb6fb5330c099c81571ab03fd69ae1": "same runtime owners as reviewed NS2 VI2 handshake; unsafe FC27 coarse claim withdrawn",
    "0d75406e36a3676b45184670093f0ecf652aab2f": "same NS1 FC27 GPU runtime owners plus NS2 VI2 real display-capacity contract",
    "372a83d95622f152211fe91afa05d1e60ce84bea": "same NS1 audio/FC27 owners plus reviewed shared 32-slot BufferCache capacity",
    "a3cc07ff68f8154543f2b07a6b3e6c01f9922ab9": "same FC27 audio/cache and NS2 BufferCache owners plus reviewed PS5 VFS128 source",
    "ab417b59c5f7f4613ff27386be05c0644d0ed776": "same FC27 audio/cache plus PS5 NS2-only HLE IPC wake and VFS128 owners",
    "7fc673495b2ee18d5216023280057a42aa78d46c": "same FC27 audio/cache plus reviewed MKW NS2 GameChat/GSV boot services",
}
KNOWN_VENDOR_GRAPH["fd6eee4933c36ed93d6ef59e2ae5d23fd975f9f2"] = "same NS1 audio owners; NS2 demand-zero guest-memory successor"
KNOWN_VENDOR_GRAPH["56959a23273ea2ee82d2e59628c92cc9e1144fe9"] = "same NS1 audio owners; NS2 zero metadata stays demand-backed"
KNOWN_VENDOR_GRAPH["d3c76f07cd82f7766be7b5e3fc3c399a3be15291"] = "same NS1 audio owners; NS2 no-op zero bitmap writes stay demand-backed"
KNOWN_VENDOR_GRAPH["436e702cc970417455c088c4bc38ce5fec8e0762"] = "same NS1 audio owners; NS2 optimized bitmap OOM is recoverable"
KNOWN_VENDOR_GRAPH["6489896230a030cf28d31961c7c8f242cab73f27"] = "same NS1 audio owners; NS2 ZeroBlock keeps shared demand-zero backing"
KNOWN_VENDOR_GRAPH["05de9e8e7f75e9a7400a351b18f2b1e83165108e"] = "same NS1 audio owners; NS2 page-heap freed slots return to ZERO"
KNOWN_VENDOR_GRAPH["ee64fac70671126c9b6ab9aa3b3885a40538cf16"] = "same NS1 audio owners; page-heap ZERO return plus joined service-worker teardown"
KNOWN_VENDOR_GRAPH["603e0d5c70b04fa84a19cca8f580ed1bdb230be0"] = "same NS1 audio owners; server workers joined and SM dynamic session capacity preserved"
KNOWN_VENDOR_GRAPH["593bc9ee6ddfcf38e488325ccf318f1a0a109d8e"] = "same runtime owners as 603; GSV 1121 parity test corrected"
KNOWN_VENDOR_GRAPH["6b48e6734e738306dd57ceed8be9b003631eb8cb"] = "same NS1 audio owners; native guest ZeroBlock is generation-neutral sparse backing"
KNOWN_VENDOR_GRAPH["d554e257ae82db66d9542f472dcde067510bfa1f"] = "same C++ owners as 6b48; sparse OOM qualification test corrected"
KNOWN_VENDOR_GRAPH["93c3dd6c86627e91999f965c45c05cd8e50e17eb"] = "same NS1 audio and guest-memory owners; gpu-time fail-closed compile fix only"
KNOWN_VENDOR_GRAPH["eb9a454db4d21a3aff2642c72eea3ca01bf2b3bb"] = "same NS1 audio/guest-memory owners; FC27 NONE render-target Vulkan fix only"
KNOWN_VENDOR_GRAPH["93da3b707ef147385380eb0690e0d93fc8e907ad"] = "same runtime owners as eb9a454d; FC27 NONE qualification test only"
KNOWN_VENDOR_GRAPH["a6240909b823492d9ff20070c09387a732d83007"] = "same runtime owners as eb9a454d; unified FC27 cache receipt tests only"
selected = subprocess.check_output(["git", "-C", str(VENDOR), "rev-parse", "HEAD"], text=True).strip()
assert selected in KNOWN_VENDOR_GRAPH, f"Unexpected vendor submodule {selected}"

def git_blob(path: Path) -> str:
    body = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(body)).encode() + b"\0" + body).hexdigest()
cmake = (ROOT / "headless/CMakeLists.txt").read_text()
checks = (
    'get_target_property(eden_ns1_audio_units audio_core SOURCES)',
    'list(REMOVE_ITEM eden_ns1_audio_units "device/device_session.cpp")',
    'list(APPEND eden_ns1_audio_units "${EDEN_NS1_AUDIO_SOURCE}")',
    'set_property(TARGET audio_core PROPERTY SOURCES "${eden_ns1_audio_units}")',
    'target_include_directories(audio_core BEFORE PRIVATE',
    'target_include_directories(core BEFORE PUBLIC',
    'APPEND PROPERTY COMPILE_DEFINITIONS "PS5_NATIVE=1"',
    'memory_native_a32.cpp',
    'memory_native_standard.cpp',
)
for check in checks:
    assert check in cmake, f"Missing active AudioOut source owner: {check}"
start = cmake.index('# R457 NS1 AudioOut: ')
end = cmake.index('# Maintained service source:', start)
owner = cmake[start:end]
assert owner.count('if(PS5_NATIVE)') == 1
assert owner.count("list(APPEND eden_ns1_audio_units") == 1
assert owner.count("list(REMOVE_ITEM eden_ns1_audio_units") == 1
h = VENDOR / "encore-active/eden-core/overrides/core/memory.h"
audio = VENDOR / "encore-active/eden-core/src/audio_core/device/device_session.cpp"
backends = [VENDOR / f"encore-active/eden-core/src/core/memory_native_{name}.cpp"
            for name in ("a32", "standard")]
# These four audio/guest-memory owners are byte-for-byte the same in the
# historical and integrated vendor SHAs (verified through raw Git blobs).
for owner, expected in (
    (h, "d4273c4539971285711a8e26c39bae046ccbbad6"),
    (audio, "893e5e5352149555ac15895d86e79068ab0ee7ae"),
    (backends[0], "3e3b07af30032ce14ca68e8482986d2f1a7201da" if selected in {"6b48e6734e738306dd57ceed8be9b003631eb8cb", "d554e257ae82db66d9542f472dcde067510bfa1f", "93c3dd6c86627e91999f965c45c05cd8e50e17eb", "eb9a454db4d21a3aff2642c72eea3ca01bf2b3bb", "93da3b707ef147385380eb0690e0d93fc8e907ad", "a6240909b823492d9ff20070c09387a732d83007"} else "aa08b4af80e22109495f8dfbec1fec129f2261e9" if selected in {"6489896230a030cf28d31961c7c8f242cab73f27", "05de9e8e7f75e9a7400a351b18f2b1e83165108e", "ee64fac70671126c9b6ab9aa3b3885a40538cf16", "603e0d5c70b04fa84a19cca8f580ed1bdb230be0", "593bc9ee6ddfcf38e488325ccf318f1a0a109d8e"} else "8007c91fd1757acf66f5f5b6a67d862afa0c475c" if selected in {"fd6eee4933c36ed93d6ef59e2ae5d23fd975f9f2", "56959a23273ea2ee82d2e59628c92cc9e1144fe9", "d3c76f07cd82f7766be7b5e3fc3c399a3be15291", "436e702cc970417455c088c4bc38ce5fec8e0762"} else "1b506bac747a3c492d4393016ca2b7dc29bfcc57"),
    (backends[1], "96663d23335fe7448712a15416003a975a3f8023" if selected in {"6b48e6734e738306dd57ceed8be9b003631eb8cb", "d554e257ae82db66d9542f472dcde067510bfa1f", "93c3dd6c86627e91999f965c45c05cd8e50e17eb", "eb9a454db4d21a3aff2642c72eea3ca01bf2b3bb", "93da3b707ef147385380eb0690e0d93fc8e907ad", "a6240909b823492d9ff20070c09387a732d83007"} else "9dad056a223b90f27470c6a5b55977217238993a" if selected in {"6489896230a030cf28d31961c7c8f242cab73f27", "05de9e8e7f75e9a7400a351b18f2b1e83165108e", "ee64fac70671126c9b6ab9aa3b3885a40538cf16", "603e0d5c70b04fa84a19cca8f580ed1bdb230be0", "593bc9ee6ddfcf38e488325ccf318f1a0a109d8e"} else "3757b123153c66584ec0dde8bd01334ec41ec9e2" if selected in {"fd6eee4933c36ed93d6ef59e2ae5d23fd975f9f2", "56959a23273ea2ee82d2e59628c92cc9e1144fe9", "d3c76f07cd82f7766be7b5e3fc3c399a3be15291", "436e702cc970417455c088c4bc38ce5fec8e0762"} else "c8f197810af244c3f2d66413352533734d031620"),
):
    assert git_blob(owner) == expected, ("Unreviewed audio owner drift", owner)
assert 'ReadyForAudioRead() const noexcept' in h.read_text()
assert 'if (!handle || !handle->GetMemory().ReadyForAudioRead())' in audio.read_text()
for b in backends:
    source = b.read_text()
    assert source.count('bool Memory::ReadyForAudioRead() const noexcept') == 1
    assert 'return impl && impl->current_page_table != nullptr;' in source
# Pinned original source tree must remain unchanged for downstream vendored checks.
assert 'ReadyForAudioRead' not in (VENDOR / "sources/eden/src/core/memory.h").read_text()
assert 'ReadyForAudioRead' not in (VENDOR / "sources/eden/src/audio_core/device/device_session.cpp").read_text()
subprocess.run([sys.executable, "-B", str(VENDOR / "tools/ns1/check_r457_audio_unready_host.py")], check=True)
subprocess.run([sys.executable, "-B", str(VENDOR / "tools/ns1/check_c00_r457_unified_audio.py")], check=True)
print("R457_AUDIO_SELECTED_NATIVE_SOURCE_PASS audio_tu=1 memory_backends=2 vendor_pin=exact reviewed="+KNOWN_VENDOR_GRAPH[selected])
