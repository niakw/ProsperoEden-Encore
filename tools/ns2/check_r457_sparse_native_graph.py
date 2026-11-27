#!/usr/bin/env python3
"""Real configured PS5 native CMake graph and syntax; no ELF, link, gameplay."""
from __future__ import annotations
import json
from pathlib import Path
import shlex
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
REVIEWED_VENDORS={
    "1ec7b429238d1175a76dc94b7c0a7f1c2eb62864",
    "fe9edd661d6f0824c7339865d50aa9cf99cab150",
    "c339fd06f02e42e67d5416ae82194ba619b7ee68",
    "47568425c71d534b72cc966d1500412c9ae4fc16",
    "447e08718c9b6625508da6ce63796ed1f4285d2f",
    "97fdc316fcf5b42e08c26845887f298feac2a424",
    "99ca67babe955398e157c6b28b22a79cbb88967e",
    "7bd7a85e6c1886035c75395c86b05b231375bbf5",
    "7b42e7f4ba6887fe6d7b539a1d2c50e6782603f6",
    "0267753219c4b6a6f3fa086a356b698cd5295f78",
    "78a903a7479f0f58f3cbd3c2fcfd329012a11e10",
    "13ee2fff7be6c0bac225b377a4367b1d0b3073a0",
    "c8e6f2f8dd2b0554e1c7d5bf6e31ef66a9885767",
    "4c252a3f4ccbbdc0ef945727da8c0e4b31a7d028",
    "72faa8edd26f6fcb16b08f321211fb94427c4ebb",
    "a946785d1ad02752ae47f9b32032e99bdbb53e02",
    "db33f8ad0c325c84bd80047d992fafa5c2908151",
    "0264f2ae94ef5889e8585171b5bfcb11fd3659ff",
    "bc78a7610425e95d6645685cbd023a67b729ec24",
    "7b7c4d2a37f9b0b248d3f3d6d9cce40596ed0c99",
    "b9f6052a65ef01e23ca4a46ba1654ed3a58cf181",
    "76c5efe8cc6d706e1c2ab0a00ddcce96e2d0adf3",
    "6f4bb38594b273fe7cc4fba960dfe62cdb9f508e",
    "4572e581d011c444fd59428d5c042098f05dcfca","f7ee793f1ee1bb1c2b1a35f68073844163658262","3f019c64c2907ac3e84baa9b6200de8898f30636","f0324324768bdc090a003079bbf121df862bc7f7","0ae51658a5d93e368408cad2484b99083ed7309f","697159fd0c183f8a164d0493929ae3b4bcb391d1","b1bb49abea63b6664e0945df8431e10aac128c2f","89d70eb505594447b3ca98658311002e74dac8ad", "b68126c9cd95eef6c6656ff6d7834c62c092aa46", "0fc157b7ccef428e675ff945bc48eceb08fff607", "42459a7893c51a178ecd0c2f74f3951cc20fa12d", "d1f8696448ed481e36380c3ea8431e3dc722304e", "c5614d3c7ef75958965bac93c9e343eccdbc0fbe", "67926ea4b6960eefebf0427929cf299e8e056013", "50a849a93494f442d47573b8ce8b8797c3cecd26", "2c85d0e8ed192c5eec79423e6be8d883fa0bd7ab", "053acc8ddf30fe65f6376564bbd6efef58f07ddc", "ffa519db0f68fb0d5d2acf791e381c898a34a175", "9e38066a508716fd959477eccf32c7fb2fde3356", "e298a9b05732346141b685eb4c9850bfa02d9e58","f7ccfda091fd7429f44159318a07391881a3e7c0","92c480e17fedecc21ab4882b76e8507b5aed3771","7039d7752c5d8b1a53db50be0d8f2f7803867e13","d3fca0aa188052f0efd2bad102950aeaeeb36ab0","dfc39fcc087738955b0373b45fa97facdeb2fc47","b806bc497049819e716ef6de81f2a85312b188ce",
}
# Exact vendor successor: revised optimized memory OOM owner, no source drift.
REVIEWED_VENDORS.add("ced1b9cdd6f0fa4e0ca7949b404f450aae0055df")
REVIEWED_VENDORS.add("06b453171af26b5703e2fcc5e68c4e8288d758b7")
REVIEWED_VENDORS.add("fd6eee4933c36ed93d6ef59e2ae5d23fd975f9f2")
REVIEWED_VENDORS.add("56959a23273ea2ee82d2e59628c92cc9e1144fe9")
REVIEWED_VENDORS.add("d3c76f07cd82f7766be7b5e3fc3c399a3be15291")
REVIEWED_VENDORS.add("436e702cc970417455c088c4bc38ce5fec8e0762")
REVIEWED_VENDORS.add("6489896230a030cf28d31961c7c8f242cab73f27")
REVIEWED_VENDORS.add("05de9e8e7f75e9a7400a351b18f2b1e83165108e")
REVIEWED_VENDORS.add("ee64fac70671126c9b6ab9aa3b3885a40538cf16")
REVIEWED_VENDORS.add("603e0d5c70b04fa84a19cca8f580ed1bdb230be0")
REVIEWED_VENDORS.add("593bc9ee6ddfcf38e488325ccf318f1a0a109d8e")
REVIEWED_VENDORS.add("6b48e6734e738306dd57ceed8be9b003631eb8cb")
REVIEWED_VENDORS.add("d554e257ae82db66d9542f472dcde067510bfa1f")
REVIEWED_VENDORS.add("93c3dd6c86627e91999f965c45c05cd8e50e17eb")
REVIEWED_VENDORS.add("eb9a454db4d21a3aff2642c72eea3ca01bf2b3bb")
REVIEWED_VENDORS.add("93da3b707ef147385380eb0690e0d93fc8e907ad")
REVIEWED_VENDORS.add("a6240909b823492d9ff20070c09387a732d83007")
OWNERS=(ROOT/"src/ns2_sparse_guest.cpp",
        ROOT/"src/host_memory.cpp")
NATIVE_GUEST=(ROOT/"vendor/encore-active/eden-core/src/core/memory_native_a32.cpp",
              ROOT/"vendor/encore-active/eden-core/src/core/memory_native_standard.cpp")
NATIVE_SHARED=ROOT/"vendor/encore-active/ns2-runtime/sparse-residency/core/hle/kernel/k_shared_memory.cpp"
NATIVE_KERNEL=ROOT/"vendor/encore-active/ns2-runtime/sparse-residency/core/hle/kernel/k_memory_manager.cpp"
NATIVE_SLAB=ROOT/"vendor/encore-active/ns2-runtime/sparse-residency/core/hle/kernel/init/init_slab_setup.cpp"
NATIVE_PAGE_HEAP=ROOT/"vendor/encore-active/ns2-runtime/sparse-residency/core/hle/kernel/k_page_heap.cpp"

def args(row):
    return list(row["arguments"]) if "arguments" in row else shlex.split(row["command"])

def main():
    native=Path(sys.argv[1]).resolve()
    sha=subprocess.check_output(["git","rev-parse","HEAD:vendor"],cwd=ROOT,text=True).strip()
    actual=subprocess.check_output(["git","-C",str(ROOT/"vendor"),"rev-parse","HEAD"],
                                   text=True).strip()
    if sha!=actual or sha not in REVIEWED_VENDORS:
        raise RuntimeError("Wrong vendor physical owner: "+sha)
    # These selected sparse page table, KSharedMemory, kernel/slab and
    # publisher sources are byte-identical in both reviewed vendor graphs.
    import hashlib
    def gitblob(path):
        raw=path.read_bytes()
        return hashlib.sha1(b"blob "+str(len(raw)).encode()+bytes([0])+raw).hexdigest()
    for owner,expected in (
        (NATIVE_GUEST[0],"3e3b07af30032ce14ca68e8482986d2f1a7201da" if sha in {"6b48e6734e738306dd57ceed8be9b003631eb8cb", "d554e257ae82db66d9542f472dcde067510bfa1f", "93c3dd6c86627e91999f965c45c05cd8e50e17eb", "eb9a454db4d21a3aff2642c72eea3ca01bf2b3bb", "93da3b707ef147385380eb0690e0d93fc8e907ad", "a6240909b823492d9ff20070c09387a732d83007"} else "aa08b4af80e22109495f8dfbec1fec129f2261e9" if sha in {"6489896230a030cf28d31961c7c8f242cab73f27", "05de9e8e7f75e9a7400a351b18f2b1e83165108e", "ee64fac70671126c9b6ab9aa3b3885a40538cf16", "603e0d5c70b04fa84a19cca8f580ed1bdb230be0", "593bc9ee6ddfcf38e488325ccf318f1a0a109d8e", "6b48e6734e738306dd57ceed8be9b003631eb8cb", "d554e257ae82db66d9542f472dcde067510bfa1f", "93c3dd6c86627e91999f965c45c05cd8e50e17eb", "eb9a454db4d21a3aff2642c72eea3ca01bf2b3bb", "93da3b707ef147385380eb0690e0d93fc8e907ad", "a6240909b823492d9ff20070c09387a732d83007"} else "8007c91fd1757acf66f5f5b6a67d862afa0c475c" if sha in {"fd6eee4933c36ed93d6ef59e2ae5d23fd975f9f2", "56959a23273ea2ee82d2e59628c92cc9e1144fe9", "d3c76f07cd82f7766be7b5e3fc3c399a3be15291", "436e702cc970417455c088c4bc38ce5fec8e0762"}
         else "1b506bac747a3c492d4393016ca2b7dc29bfcc57"),
        (NATIVE_GUEST[1],"96663d23335fe7448712a15416003a975a3f8023" if sha in {"6b48e6734e738306dd57ceed8be9b003631eb8cb", "d554e257ae82db66d9542f472dcde067510bfa1f", "93c3dd6c86627e91999f965c45c05cd8e50e17eb", "eb9a454db4d21a3aff2642c72eea3ca01bf2b3bb", "93da3b707ef147385380eb0690e0d93fc8e907ad", "a6240909b823492d9ff20070c09387a732d83007"} else "9dad056a223b90f27470c6a5b55977217238993a" if sha in {"6489896230a030cf28d31961c7c8f242cab73f27", "05de9e8e7f75e9a7400a351b18f2b1e83165108e", "ee64fac70671126c9b6ab9aa3b3885a40538cf16", "603e0d5c70b04fa84a19cca8f580ed1bdb230be0", "593bc9ee6ddfcf38e488325ccf318f1a0a109d8e", "6b48e6734e738306dd57ceed8be9b003631eb8cb", "d554e257ae82db66d9542f472dcde067510bfa1f", "93c3dd6c86627e91999f965c45c05cd8e50e17eb", "eb9a454db4d21a3aff2642c72eea3ca01bf2b3bb", "93da3b707ef147385380eb0690e0d93fc8e907ad", "a6240909b823492d9ff20070c09387a732d83007"} else "3757b123153c66584ec0dde8bd01334ec41ec9e2" if sha in {"fd6eee4933c36ed93d6ef59e2ae5d23fd975f9f2", "56959a23273ea2ee82d2e59628c92cc9e1144fe9", "d3c76f07cd82f7766be7b5e3fc3c399a3be15291", "436e702cc970417455c088c4bc38ce5fec8e0762"}
         else "c8f197810af244c3f2d66413352533734d031620"),
        (NATIVE_SHARED,"515df1ec4a4b231266d6f3e5481c54ca87c94453" if sha in {"06b453171af26b5703e2fcc5e68c4e8288d758b7", "fd6eee4933c36ed93d6ef59e2ae5d23fd975f9f2", "56959a23273ea2ee82d2e59628c92cc9e1144fe9", "d3c76f07cd82f7766be7b5e3fc3c399a3be15291", "436e702cc970417455c088c4bc38ce5fec8e0762", "6489896230a030cf28d31961c7c8f242cab73f27", "05de9e8e7f75e9a7400a351b18f2b1e83165108e", "ee64fac70671126c9b6ab9aa3b3885a40538cf16", "603e0d5c70b04fa84a19cca8f580ed1bdb230be0", "593bc9ee6ddfcf38e488325ccf318f1a0a109d8e", "6b48e6734e738306dd57ceed8be9b003631eb8cb", "d554e257ae82db66d9542f472dcde067510bfa1f", "93c3dd6c86627e91999f965c45c05cd8e50e17eb", "eb9a454db4d21a3aff2642c72eea3ca01bf2b3bb", "93da3b707ef147385380eb0690e0d93fc8e907ad", "a6240909b823492d9ff20070c09387a732d83007"}
         else "9b47d62a6b8503c7a3cdff053888ea47a799cbed"),
        (NATIVE_KERNEL,"2b5be4eba2500da2993db2ed1c86d44ddfa5554f" if sha in {"436e702cc970417455c088c4bc38ce5fec8e0762", "6489896230a030cf28d31961c7c8f242cab73f27", "05de9e8e7f75e9a7400a351b18f2b1e83165108e", "ee64fac70671126c9b6ab9aa3b3885a40538cf16", "603e0d5c70b04fa84a19cca8f580ed1bdb230be0", "593bc9ee6ddfcf38e488325ccf318f1a0a109d8e", "6b48e6734e738306dd57ceed8be9b003631eb8cb", "d554e257ae82db66d9542f472dcde067510bfa1f", "93c3dd6c86627e91999f965c45c05cd8e50e17eb", "eb9a454db4d21a3aff2642c72eea3ca01bf2b3bb", "93da3b707ef147385380eb0690e0d93fc8e907ad", "a6240909b823492d9ff20070c09387a732d83007"}
         else "6397dd2c4a9c9c10674ab87b344f5c6956b79e0c" if sha == "d3c76f07cd82f7766be7b5e3fc3c399a3be15291"
         else "aeee7f62a3fc609936ff5dc6a64722ca8d860c2e" if sha == "56959a23273ea2ee82d2e59628c92cc9e1144fe9"
         else "12d3d0ddc59308b80df46bc54e6e8ee54011d568" if sha == "fd6eee4933c36ed93d6ef59e2ae5d23fd975f9f2"
         else "c5b5dd99bb9a65286783f4b220d991f422d19e67"
         if sha in {"ced1b9cdd6f0fa4e0ca7949b404f450aae0055df", "06b453171af26b5703e2fcc5e68c4e8288d758b7"}
         else "88f3e2c9220ee03fd6600ef12441d7ece7527c9d"),
        (NATIVE_SLAB,"130eb7bd53e29b816bb81fec3fa053a584cd4b6e"),
    ):
        if gitblob(owner)!=expected:
            raise RuntimeError("Unreviewed native sparse owner "+str(owner))
    if sha in {"05de9e8e7f75e9a7400a351b18f2b1e83165108e", "ee64fac70671126c9b6ab9aa3b3885a40538cf16", "603e0d5c70b04fa84a19cca8f580ed1bdb230be0", "593bc9ee6ddfcf38e488325ccf318f1a0a109d8e", "6b48e6734e738306dd57ceed8be9b003631eb8cb", "d554e257ae82db66d9542f472dcde067510bfa1f", "93c3dd6c86627e91999f965c45c05cd8e50e17eb", "eb9a454db4d21a3aff2642c72eea3ca01bf2b3bb", "93da3b707ef147385380eb0690e0d93fc8e907ad", "a6240909b823492d9ff20070c09387a732d83007"}:
        expected_page_heap = ("574c88dc2add018094c3e6db9047881709da6659"
                              if sha in {"ee64fac70671126c9b6ab9aa3b3885a40538cf16", "603e0d5c70b04fa84a19cca8f580ed1bdb230be0", "593bc9ee6ddfcf38e488325ccf318f1a0a109d8e", "6b48e6734e738306dd57ceed8be9b003631eb8cb", "d554e257ae82db66d9542f472dcde067510bfa1f", "93c3dd6c86627e91999f965c45c05cd8e50e17eb", "eb9a454db4d21a3aff2642c72eea3ca01bf2b3bb", "93da3b707ef147385380eb0690e0d93fc8e907ad", "a6240909b823492d9ff20070c09387a732d83007"}
                              else "1183a2455d027d546e069a455d0c3b460065732a")
        if gitblob(NATIVE_PAGE_HEAP) != expected_page_heap:
            raise RuntimeError("Unreviewed native sparse page-heap owner")
        cmake_source=(ROOT/"headless/CMakeLists.txt").read_text()
        if "EDEN_R457_SPARSE_PAGE_HEAP_SRC" not in cmake_source:
            raise RuntimeError("Sparse page heap not selected by native CMake")
    cache=(native/"CMakeCache.txt").read_text()
    if "set(EDEN_NS2_SPARSE_BACKING ON)" not in (ROOT/"headless/CMakeLists.txt").read_text():
        raise RuntimeError("Production sparse PS5 backing not selected")
    if "EDEN_PS5_VULKAN:BOOL=ON" not in cache:
        raise RuntimeError("Real PS5 Vulkan not enabled")
    db=json.loads((native/"compile_commands.json").read_text())
    selected=[]
    for path in OWNERS:
        matches=[r for r in db if Path(r["file"]).resolve()==path.resolve()]
        if len(matches)!=1: raise RuntimeError(f"Expected one {path}; got {len(matches)}")
        selected.append((path.name,matches[0]))
    variants={x.resolve() for x in NATIVE_GUEST}
    vendor_rows=[r for r in db if Path(r["file"]).resolve() in variants]
    if len(vendor_rows)!=1: raise RuntimeError(f"Expected one real PTE TU, got {len(vendor_rows)}")
    selected.append(("native_guest_pte",vendor_rows[0]))
    shared_rows=[r for r in db if Path(r["file"]).resolve()==NATIVE_SHARED.resolve()]
    if len(shared_rows)!=1: raise RuntimeError(
        f"Expected exactly one sparse KSharedMemory TU, got {len(shared_rows)}")
    selected.append(("native_kernel_shared_clear",shared_rows[0]))
    kernel_rows=[r for r in db if Path(r["file"]).resolve()==NATIVE_KERNEL.resolve()]
    if len(kernel_rows)!=1: raise RuntimeError(f"Expected exactly one real native kernel direct owner, got {len(kernel_rows)}")
    selected.append(("native_kernel_direct",kernel_rows[0]))
    slab_rows=[r for r in db if Path(r["file"]).resolve()==NATIVE_SLAB.resolve()]
    if len(slab_rows)!=1:
        raise RuntimeError(f"Expected one real native KPort/KPageBuffer slab owner, got {len(slab_rows)}")
    selected.append(("native_kernel_slabs",slab_rows[0]))
    if sha in {"05de9e8e7f75e9a7400a351b18f2b1e83165108e", "ee64fac70671126c9b6ab9aa3b3885a40538cf16", "603e0d5c70b04fa84a19cca8f580ed1bdb230be0", "593bc9ee6ddfcf38e488325ccf318f1a0a109d8e", "6b48e6734e738306dd57ceed8be9b003631eb8cb", "d554e257ae82db66d9542f472dcde067510bfa1f", "93c3dd6c86627e91999f965c45c05cd8e50e17eb", "eb9a454db4d21a3aff2642c72eea3ca01bf2b3bb", "93da3b707ef147385380eb0690e0d93fc8e907ad", "a6240909b823492d9ff20070c09387a732d83007"}:
        page_heap_rows=[r for r in db if Path(r["file"]).resolve()==NATIVE_PAGE_HEAP.resolve()]
        if len(page_heap_rows)!=1:
            raise RuntimeError(f"Expected one real sparse page-heap owner, got {len(page_heap_rows)}")
        selected.append(("native_kernel_page_heap_free_return",page_heap_rows[0]))
    # R457 storage follow-up: the new six maintained readers were previously
    # tested through source-derived mocks and a script-mode selector. Prove
    # they are each the sole real CMake native compilation owner, then compile
    # the full TUs with the exact SDK command (not replacement mock headers).
    storage_labels = set()
    if sha in {"7bd7a85e6c1886035c75395c86b05b231375bbf5", "7b42e7f4ba6887fe6d7b539a1d2c50e6782603f6", "0267753219c4b6a6f3fa086a356b698cd5295f78", "78a903a7479f0f58f3cbd3c2fcfd329012a11e10", "13ee2fff7be6c0bac225b377a4367b1d0b3073a0", "c8e6f2f8dd2b0554e1c7d5bf6e31ef66a9885767", "4c252a3f4ccbbdc0ef945727da8c0e4b31a7d028", "72faa8edd26f6fcb16b08f321211fb94427c4ebb"}:
        storage_receipts = {
            "file_sys/vfs/vfs.cpp": "70926039977f56c87558270d7655f8de26d1e446",
            "file_sys/vfs/vfs_vector.cpp": "5f9c99b7ed5227c403ceca1d2e04d6c8dafc26cb",
            "file_sys/partition_filesystem.cpp": "350af05f831fe89a05158350f8c8aded988980dd",
            "file_sys/fssystem/fssystem_nca_file_system_driver.cpp": "f6ceeb8d18b88b850c19b86cc3823e40ce5b9afa",
            "file_sys/fssystem/fssystem_integrity_verification_storage.cpp": "5afc754433f6276ffd80bc0af418d31cf5cf496c",
            "file_sys/romfs.cpp": "51eb401e5f2e3a0deefc5fc0e4cc30b0f4b8e4a3",
        }
        for relative, expected in storage_receipts.items():
            path = ROOT/"vendor/encore-active/eden-core/src/core"/relative
            if gitblob(path) != expected:
                raise RuntimeError("Unreviewed real storage owner "+relative)
            suffix = Path("src/core")/relative
            rows = [r for r in db if Path(r["file"]).parts[-len(suffix.parts):] == suffix.parts]
            if len(rows) != 1 or Path(rows[0]["file"]).resolve() != path.resolve():
                raise RuntimeError("Missing, duplicate or wrong native storage TU "+relative)
            label = "storage_"+Path(relative).stem
            storage_labels.add(label)
            selected.append((label, rows[0]))
        print("R457_NATIVE_STORAGE_6_OWNER_GRAPH_PASS exact_receipts=6",flush=True)

    shader_labels = set()
    bfs_header = None
    if sha in {"7b42e7f4ba6887fe6d7b539a1d2c50e6782603f6", "0267753219c4b6a6f3fa086a356b698cd5295f78", "78a903a7479f0f58f3cbd3c2fcfd329012a11e10", "13ee2fff7be6c0bac225b377a4367b1d0b3073a0", "c8e6f2f8dd2b0554e1c7d5bf6e31ef66a9885767", "4c252a3f4ccbbdc0ef945727da8c0e4b31a7d028", "72faa8edd26f6fcb16b08f321211fb94427c4ebb"}:
        relative = Path("shader_recompiler/frontend/ir/breadth_first_search.h")
        bfs_header = native/"headless/r23-shader-phi/include"/relative
        vendor_header = ROOT/"vendor/encore-active/eden/src"/relative
        if gitblob(bfs_header) != "194476705f21bd1c27f532fdd5cc04d99a3cd620" or gitblob(vendor_header) != "194476705f21bd1c27f532fdd5cc04d99a3cd620":
            raise RuntimeError("Wrong native adaptive BFS staged header")
        texture = ROOT/"vendor/encore-active/eden/src/shader_recompiler/ir_opt/texture_pass.cpp"
        if gitblob(texture) != "85c523e435ee8803ef3d2087567aa1a4b5d09369":
            raise RuntimeError("Unexpected conditional Phi texture pass owner")
        rows = [r for r in db if Path(r["file"]).parts[-3:] == ("shader_recompiler","ir_opt","texture_pass.cpp")]
        if len(rows) != 1 or Path(rows[0]["file"]).resolve() != texture.resolve():
            raise RuntimeError("Wrong or duplicate selected texture pass")
        label = "shader_texture_phi_bfs"
        shader_labels.add(label)
        selected.append((label, rows[0]))
        print("R457_NATIVE_BFS_STAGE_GRAPH_PASS exact_header=1 texture_owner=1",flush=True)

    if sha in {"0267753219c4b6a6f3fa086a356b698cd5295f78", "78a903a7479f0f58f3cbd3c2fcfd329012a11e10", "13ee2fff7be6c0bac225b377a4367b1d0b3073a0", "c8e6f2f8dd2b0554e1c7d5bf6e31ef66a9885767", "4c252a3f4ccbbdc0ef945727da8c0e4b31a7d028", "72faa8edd26f6fcb16b08f321211fb94427c4ebb"}:
        env = ROOT/"vendor/encore-active/eden-core/src/video_core/shader_environment.cpp"
        if gitblob(env) != "8b4e883aaad5507652e13be211581e4965b7fe89":
            raise RuntimeError("Unreviewed null-TIC shader environment owner")
        rows = [r for r in db if Path(r["file"]).parts[-2:] == ("video_core","shader_environment.cpp")]
        if len(rows) != 1 or Path(rows[0]["file"]).resolve() != env.resolve():
            raise RuntimeError("Wrong or duplicate shader environment owner")
        shader_labels.add("shader_environment_null_tic")
        selected.append(("shader_environment_null_tic", rows[0]))
        print("R457_NATIVE_NULL_TIC_GRAPH_PASS exact_owner=1",flush=True)

    host1x_labels = set()
    if sha in {"78a903a7479f0f58f3cbd3c2fcfd329012a11e10", "13ee2fff7be6c0bac225b377a4367b1d0b3073a0", "c8e6f2f8dd2b0554e1c7d5bf6e31ef66a9885767", "4c252a3f4ccbbdc0ef945727da8c0e4b31a7d028", "72faa8edd26f6fcb16b08f321211fb94427c4ebb"}:
        sync = ROOT/"vendor/encore-active/eden-core/src/video_core/host1x/syncpoint_manager.cpp"
        if gitblob(sync) != "4e87a03a8d411f0f07a6806bf6aaebbe9ad16b48":
            raise RuntimeError("Unreviewed Host1x counter notification owner")
        pinned_header = ROOT/"vendor/sources/eden/src/video_core/host1x/syncpoint_manager.h"
        if gitblob(pinned_header) != "847ed20c8dccbb0319d95ccbded460c78f661cac":
            raise RuntimeError("Unexpected Host1x handle ABI")
        rows = [r for r in db if Path(r["file"]).parts[-3:] == ("video_core","host1x","syncpoint_manager.cpp")]
        if len(rows) != 1 or Path(rows[0]["file"]).resolve() != sync.resolve():
            raise RuntimeError("Wrong or duplicate native Host1x syncpoint owner")
        host1x_labels.add("host1x_counter_notify")
        selected.append(("host1x_counter_notify", rows[0]))
        print("R457_NATIVE_HOST1X_NOTIFY_GRAPH_PASS exact_owner=1 unchanged_header=1",flush=True)

    if sha in {"13ee2fff7be6c0bac225b377a4367b1d0b3073a0", "c8e6f2f8dd2b0554e1c7d5bf6e31ef66a9885767", "4c252a3f4ccbbdc0ef945727da8c0e4b31a7d028", "72faa8edd26f6fcb16b08f321211fb94427c4ebb"}:
        geometry = ROOT/"vendor/encore-active/eden/src/shader_recompiler/frontend/maxwell/translate_program.cpp"
        if gitblob(geometry) != "2cd894ab009c16a22d953d1cba9359c28ae22149":
            raise RuntimeError("Unreviewed emulated geometry mask source")
        rows = [r for r in db if Path(r["file"]).parts[-3:] == ("frontend","maxwell","translate_program.cpp")]
        if len(rows) != 1 or Path(rows[0]["file"]).resolve() != geometry.resolve():
            raise RuntimeError("Wrong or duplicate shader translation owner")
        shader_labels.add("shader_geometry_passthrough_mask")
        selected.append(("shader_geometry_passthrough_mask", rows[0]))
        print("R457_NATIVE_GEOMETRY_MASK_GRAPH_PASS exact_owner=1",flush=True)

    if sha in {"c8e6f2f8dd2b0554e1c7d5bf6e31ef66a9885767", "4c252a3f4ccbbdc0ef945727da8c0e4b31a7d028", "72faa8edd26f6fcb16b08f321211fb94427c4ebb"}:
        original = ROOT/"vendor/encore-active/eden-vulkan/vk_texture_cache_cost.cpp"
        if gitblob(original) != "27a3c820667b0bf0774b9ab3c88e5a9e00032c4f":
            raise RuntimeError("Unreviewed Vulkan blit layout source")
        rows = [r for r in db if Path(r["file"]).name == "vk_texture_cache_cost.cpp"]
        if len(rows) != 1:
            raise RuntimeError("Missing or duplicate native texture-cache owner")
        staged = Path(rows[0]["file"]).resolve()
        if staged != (native/"headless/vk_texture_cache_cost.cpp").resolve() or gitblob(staged) != gitblob(original):
            raise RuntimeError("Wrong native staged texture-cache source")
        shader_labels.add("vulkan_same_image_blit")
        selected.append(("vulkan_same_image_blit",rows[0]))
        print("R457_NATIVE_BLIT_LAYOUT_GRAPH_PASS exact_staged_owner=1",flush=True)

    if sha in {"4c252a3f4ccbbdc0ef945727da8c0e4b31a7d028", "72faa8edd26f6fcb16b08f321211fb94427c4ebb"}:
        phi = ROOT/"vendor/encore-active/eden/src/shader_recompiler/backend/spirv/emit_spirv.cpp"
        if gitblob(phi) != "b490f372d67f4aabf69aa2b29973835f662382db":
            raise RuntimeError("Unreviewed typed Phi emitter")
        rows = [r for r in db if Path(r["file"]).parts[-3:] == ("backend","spirv","emit_spirv.cpp")]
        if len(rows) != 1 or Path(rows[0]["file"]).resolve() != phi.resolve():
            raise RuntimeError("Wrong or duplicate typed Phi emitter owner")
        shader_labels.add("shader_typed_phi")
        selected.append(("shader_typed_phi", rows[0]))
        print("R457_NATIVE_TYPED_PHI_GRAPH_PASS exact_owner=1",flush=True)

    am_labels = set()
    if sha == "72faa8edd26f6fcb16b08f321211fb94427c4ebb":
        am = ROOT/"vendor/encore-active/ns2-runtime/am/core/hle/service/am/service/application_functions.cpp"
        if gitblob(am) != "b8787c322258fcccd7c5d53a74097a5619e2211c":
            raise RuntimeError("Unreviewed shared native AM language reply owner")
        rows = [r for r in db if Path(r["file"]).parts[-2:] == ("service","application_functions.cpp")]
        if len(rows) != 1 or Path(rows[0]["file"]).resolve() != am.resolve():
            raise RuntimeError("Wrong or duplicate native AM language reply TU")
        am_labels.add("am_guest_language_reply")
        selected.append(("am_guest_language_reply", rows[0]))
        print("R457_NATIVE_GUEST_LANGUAGE_REPLY_GRAPH_PASS exact_owner=1",flush=True)

    # Qualify existing source owners first even when the new sparse TU has a
    # target-SDK header problem; never stop before recording their verdict.
    selected.sort(key=lambda pair: pair[0] == "ns2_sparse_guest.cpp")
    subprocess.run(["ninja","-C",str(native),"-t","targets","all"],
                   check=True,stdout=subprocess.DEVNULL,timeout=30)
    for label,row in selected:
        command=args(row)
        native_definition = any(x=="-DPS5_NATIVE" or x.startswith("-DPS5_NATIVE=") for x in command)
        if label in storage_labels:
            # CMake deliberately scopes PS5_NATIVE to the platform-specific
            # sparse owners. The six common storage TUs have no such guard.
            # Assert the genuine cross target instead of injecting a definition
            # that production core does not use.
            if native_definition:
                raise RuntimeError(label+" unexpected PS5_NATIVE on common storage TU")
            if not any(x=="--target=x86_64-sie-ps5" or
                       (x in ("-target","--target") and i+1<len(command) and
                        command[i+1]=="x86_64-sie-ps5") for i,x in enumerate(command)):
                raise RuntimeError(label+" missing real PS5 compiler target")
        elif label in shader_labels or label in host1x_labels or label in am_labels:
            if not any(x=="--target=x86_64-sie-ps5" or
                       (x in ("-target","--target") and i+1<len(command) and
                        command[i+1]=="x86_64-sie-ps5") for i,x in enumerate(command)):
                raise RuntimeError(label+" missing real PS5 compiler target")
        elif not native_definition:
            raise RuntimeError(label+" missing PS5_NATIVE")
        if label not in (shader_labels | host1x_labels) and not any(x.startswith("-DEDEN_NS2_SPARSE_BACKING") for x in command):
            raise RuntimeError(label+" missing production sparse backing")
        print("R457_NS2_SPARSE_NATIVE_GRAPH_PASS",label,row["file"],flush=True)
        cleaned=[]
        i=0
        while i<len(command):
            if command[i] in ("-o","-MF","-MT","-MQ"):
                if i+1>=len(command): raise RuntimeError(label+" dangling compile flag")
                i+=2;continue
            if command[i] in ("-c","-MD","-MMD","-MP"):
                i+=1;continue
            cleaned.append(command[i]);i+=1
        # The native graph may have PS5_NATIVE defined yet still inherit
        # incomplete C-header search paths. Record the *real* compiler
        # target/sysroot without silently introducing Linux libc into the
        # purported PS5 ABI. A separate non-accepting diagnostic can show
        # whether the C++ changes themselves then have syntax errors.
        markers=[flag for flag in cleaned if
                 flag.startswith(("--target","-target","--sysroot","-isysroot",
                                  "-nostdinc","-stdlib","-isystem"))]
        print("R457_NS2_SPARSE_NATIVE_TOOLCHAIN",label,
              "compiler="+cleaned[0], "flags="+repr(markers[:20]),flush=True)
        # The native PS5 SDK C headers must be the only C-library headers.
        # Clang's implicit Linux search path cannot establish PS5 syntax,
        # even with a PS5 target triple. Keep every CMake-selected include
        # and definition, add only Clang's target builtin headers explicitly.
        import os
        sdk=Path(os.environ["PS5_PAYLOAD_SDK"]).resolve()
        c_root=sdk/"target/include"
        assert (c_root/"stdlib.h").is_file() and (c_root/"sys/cdefs.h").is_file(), (
            "Incomplete native PS5 FreeBSD C header distribution")
        compiler=Path(cleaned[0])
        resource_dir=Path(subprocess.check_output(
            [str(compiler), "-print-resource-dir"],text=True).strip())/"include"
        assert resource_dir.is_dir(), "Native Clang compiler resource headers missing"
        # A configured target must not silently pick any Linux libc header.
        # Show the exact contaminated search flags, not just an opaque failure.
        host_includes=[]
        for pos,flag in enumerate(cleaned):
            if flag in ("-isystem","-I","-idirafter","-iquote") and pos+1<len(cleaned):
                path=cleaned[pos+1]
                if path.startswith(("/usr/include","/usr/local/include")):
                    host_includes.append((flag,path))
            elif flag.startswith(("-I/usr/include","-isystem/usr/include",
                                  "-I/usr/local/include","-isystem/usr/local/include")):
                host_includes.append(("inline",flag))
        print("R457_NS2_NATIVE_INCLUDE_PROVENANCE", label,
              "host_include_flags="+repr(host_includes),
              "sdk_c_headers="+str(c_root),
              "sdk_stdlib="+str((c_root/"stdlib.h").is_file()),flush=True)
        if host_includes:
            raise RuntimeError(label+" configured PS5 native graph contains host libc "+repr(host_includes))
        strict=cleaned+["-nostdinc","-isystem",str(resource_dir),"-fsyntax-only"]
        if label == "shader_texture_phi_bfs":
            strict.append("-H") # record which real header Clang actually includes
        p=subprocess.run(strict,cwd=row["directory"],
                         capture_output=True,text=True,timeout=210)
        if p.returncode:
            if "bits/libc-header-start.h" in p.stderr:
                # Host-only header-path experiment, never accepted as a
                # native SDK success. Continue the strict gate after it.
                mixed=cleaned+["-isystem","/usr/include/x86_64-linux-gnu",
                               "-fsyntax-only"]
                diagnostic=subprocess.run(mixed,cwd=row["directory"],
                           capture_output=True,text=True,timeout=210)
                print("R457_NS2_SPARSE_HOST_LIBC_DIAGNOSTIC",label,
                      "status="+str(diagnostic.returncode),
                      "NOT_REAL_PS5_ABI",flush=True)
                if diagnostic.returncode:
                    print(diagnostic.stderr[-3500:],file=sys.stderr,flush=True)
            raise RuntimeError(label+" genuine SDK syntax: "+p.stderr[-8500:])
        if label == "shader_texture_phi_bfs":
            if not any(str(bfs_header) in line and line.lstrip().startswith(".")
                       for line in p.stderr.splitlines()):
                raise RuntimeError("Actual compiler did not include the staged adaptive BFS header")
            print("R457_NATIVE_BFS_ACTUAL_HEADER_PASS",bfs_header,flush=True)
        # Do not discard diagnostics from successful syntax compiles.
        warnings = [line for line in p.stderr.splitlines() if "warning:" in line]
        for line in warnings:
            print("R457_NATIVE_SYNTAX_WARNING", label, line, flush=True)
        print("R457_NATIVE_SYNTAX_WARNING_COUNT", label, len(warnings),flush=True)
        print("R457_NS2_SPARSE_NATIVE_SYNTAX_PASS",label,flush=True)
        if label in storage_labels:
            print("R457_NATIVE_STORAGE_SYNTAX_PASS",label,flush=True)
        if label in am_labels:
            print("R457_NATIVE_GUEST_LANGUAGE_REPLY_SYNTAX_PASS",label,flush=True)
    print("R457_NS2_SPARSE_ACTUAL_PS5_CMAKE_AND_6_TUS_PASS no link/gameplay",flush=True)
    if storage_labels:
        print("R457_NATIVE_STORAGE_ACTUAL_PS5_CMAKE_AND_6_TUS_PASS no link/gameplay",flush=True)

if __name__=="__main__":
    try: main()
    except Exception as e:
        print("R457_NS2_SPARSE_NATIVE_FAIL",e,file=sys.stderr,flush=True)
        raise SystemExit(1)
