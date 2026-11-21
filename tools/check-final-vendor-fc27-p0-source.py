#!/usr/bin/env python3
"""Final engine/vendor source qualification for FC27 + P0 additions.

Host/source only. This proves the engine selects the exact reviewed vendor
graph and replays the vendor's own focused contracts. It is not a PS5 build,
FC27 visual pass, Bananza boot proof, or performance measurement.
"""
from pathlib import Path
import hashlib
import subprocess

ROOT=Path(__file__).resolve().parents[1]
V=ROOT/"vendor"
# Vendor #192/#193 touch only reviewed NS2 A64/kernel owners and their tests.
# The FC27 GPU owners remain byte-sealed by the focused tests below.
REVIEWED_PINS={"1a09972eea6f473fda1b714efe84cd52219bf681", "3e6647827122c34704c2699a6f5e9b20fff3e9a6", "6d64217ea5804fb86dbf57685a3da0cb1d45ba32", "3f1fcfef119ca50dd630f0518a7fae1b96c7a85a", "0e4e96df638fc29c3bd2a8fcfe9f50821c5e5b3a", "9136d2e88c43233bcd029f22bdfda0e5c94a552f", "75ef34d7ef7f68b5eb4f1c6d0d99b6cbc55742d6", "34f02a3800cb6fb5330c099c81571ab03fd69ae1", "0d75406e36a3676b45184670093f0ecf652aab2f", "372a83d95622f152211fe91afa05d1e60ce84bea", "a3cc07ff68f8154543f2b07a6b3e6c01f9922ab9", "ab417b59c5f7f4613ff27386be05c0644d0ed776", "2ccc4b0a714ca621ac2879768f87118a64ed65f6", "97ac02f263ec90f40a029f4aa62980c76bc25d5c", "9a83a6ba1cb464c9e5d14457cab18ad511c1104b", "d0246caf58a3127597bba1edfc1f8dcbe0c5cfdc", "8153654a2f1fe809fb2caa28dcadca90a7661446", "6c38328fbef33de747f5c31ea30d13541a513a4a", "8e564f61e6c8b86149ce0a0d6d2aa323a268dda6", "67759611edc13414c112ea9d2b6664d54827a200", "c15cdfe96a3d836bf32ba21b8070088add81cdc9", "729f7e5a734b5a890a7bbf3ab60ce1100492af13", "7fc673495b2ee18d5216023280057a42aa78d46c", "510f1efde545357fe8095a812df32251ee546285", "2a450d43d1d23d3e8b1667e396613f62c69c26d7", "17c95ef233a9a0e508e50ada4ae9dc53a300c46c", "082cd1b77c7df80dc422eae5ba59d9cd33e48dc4", "e0fced3a091495e70362d8c4ca072942f027af24", "491fa7e2388d46e23827b1459360a5d7f4a2814b", "b177deb8282b14e1521485f5ac63bd7ccc9ca7ef", "06fc7dc2e0a00e00f831dfd78ae78087736276a3", "850086c79ec40838663989a81f33ba8ea2f15f6a", "917ccdc1cf772b9312b19888eea181b8e114334b", "0c1bd95c896f6ddc7870a245ffca51b2ac7e2932", "eadc6e798def18417e50db6a03a291440429d795"}
REVIEWED_PINS.add("03b264ee3e5ac7d7bbf89d3a9c51a3aff93a4433")
REVIEWED_PINS.add("ac55a39658c8029a0ec900475234012ae6bf6289")
REVIEWED_PINS.add("a7b9008340ccf03e4f63c180d820631858fe935e")
REVIEWED_PINS.add("565f143c27443553b60ca1b21cc1094caa23ceb5")
REVIEWED_PINS.add("010d5c61cefd62cbb5d27102cd9a2350fa0e69ce")
REVIEWED_PINS.add("3460d10e60bff7dd8b057f592eb671cc35eddd25")
REVIEWED_PINS.add("6f6f7f4cb154aa227eaf4d54330ff9d817b77ecb")
REVIEWED_PINS.add("ce27bdd184c60d1f096ef1495c0ef7e5b7f0cdf0")
REVIEWED_PINS.add("01c942171fea39c1f7cf31d13ab36895aebb593a")
REVIEWED_PINS.add("dcf7116dd2c536e05c80d83ff9dbf30caa5cc109")
REVIEWED_PINS.add("b65d8d9673475433f0b6eac72eb304bf23141666")
REVIEWED_PINS.add("266080b4df8f56bb5a9b52c8c3ec253254c1578b")
REVIEWED_PINS.add("ac33c63d7c53bfbd6df5f2f164f1fe078fdfddc7")
REVIEWED_PINS.add("dfbba1e690128a44da755494c422ed1e6bdeb3c3")
REVIEWED_PINS.add("47e9735a63c94ca42ec80412c6fcfd84a4910a53")
REVIEWED_PINS.add("f007f3d539a523607fbef8b8895c2833e5b7af8c")
REVIEWED_PINS.add("b3e6f9943bd46fda050ecb8151c4bb06e5251117")
REVIEWED_PINS.add("7535dc9e5e7f0060b8e448da843f96882a2ce320")
selected=subprocess.check_output(["git","rev-parse","HEAD:vendor"],cwd=ROOT,text=True).strip()
original_vendor_pin = selected
ns2_gsv_497_v2 = selected in {"a7b9008340ccf03e4f63c180d820631858fe935e", "565f143c27443553b60ca1b21cc1094caa23ceb5"}
ns2_gsv_497_dual = selected in {"010d5c61cefd62cbb5d27102cd9a2350fa0e69ce", "3460d10e60bff7dd8b057f592eb671cc35eddd25", "6f6f7f4cb154aa227eaf4d54330ff9d817b77ecb", "ce27bdd184c60d1f096ef1495c0ef7e5b7f0cdf0", "01c942171fea39c1f7cf31d13ab36895aebb593a", "dcf7116dd2c536e05c80d83ff9dbf30caa5cc109", "b65d8d9673475433f0b6eac72eb304bf23141666"}
checked=subprocess.check_output(["git","-C",str(V),"rev-parse","HEAD"],text=True).strip()
assert selected==checked and selected in REVIEWED_PINS,(selected,checked)
# The reviewed NS2 HID successor is exactly two fast-forward commits after
# b65d8d9 and changes only the live hid_server.cpp/.h (verified by GitHub
# compare b65d8d9...266080b4). Seal both new blobs before replaying all
# the unchanged FC27/NS2 source receipts of the reviewed parent. Do not add
# a blanket allowlist exception: a drifted runtime source remains fatal.
gsv_syncpt_201_revision = selected in {"ac33c63d7c53bfbd6df5f2f164f1fe078fdfddc7", "dfbba1e690128a44da755494c422ed1e6bdeb3c3", "47e9735a63c94ca42ec80412c6fcfd84a4910a53", "f007f3d539a523607fbef8b8895c2833e5b7af8c", "b3e6f9943bd46fda050ecb8151c4bb06e5251117", "7535dc9e5e7f0060b8e448da843f96882a2ce320"}
gsv_gpu_403_revision = selected in {"47e9735a63c94ca42ec80412c6fcfd84a4910a53", "f007f3d539a523607fbef8b8895c2833e5b7af8c", "b3e6f9943bd46fda050ecb8151c4bb06e5251117", "7535dc9e5e7f0060b8e448da843f96882a2ce320"}
gsv_native_115_revision = selected in {"f007f3d539a523607fbef8b8895c2833e5b7af8c", "b3e6f9943bd46fda050ecb8151c4bb06e5251117", "7535dc9e5e7f0060b8e448da843f96882a2ce320"}
gsv_transfer_memory_revision = selected in {"b3e6f9943bd46fda050ecb8151c4bb06e5251117", "7535dc9e5e7f0060b8e448da843f96882a2ce320"}
vi2_indexed_event_revision = selected == "7535dc9e5e7f0060b8e448da843f96882a2ce320"
if selected in {"266080b4df8f56bb5a9b52c8c3ec253254c1578b", "ac33c63d7c53bfbd6df5f2f164f1fe078fdfddc7", "dfbba1e690128a44da755494c422ed1e6bdeb3c3", "47e9735a63c94ca42ec80412c6fcfd84a4910a53", "f007f3d539a523607fbef8b8895c2833e5b7af8c", "b3e6f9943bd46fda050ecb8151c4bb06e5251117", "7535dc9e5e7f0060b8e448da843f96882a2ce320"}:
    for relative, expected in (
        ("encore-active/ns2-runtime/hle/core/hle/service/hid/hid_server.cpp",
         ("b83f519fef3905eabb0bef65cab4d989033b5287"
           if selected in {"dfbba1e690128a44da755494c422ed1e6bdeb3c3", "47e9735a63c94ca42ec80412c6fcfd84a4910a53", "f007f3d539a523607fbef8b8895c2833e5b7af8c", "b3e6f9943bd46fda050ecb8151c4bb06e5251117", "7535dc9e5e7f0060b8e448da843f96882a2ce320"} else "dcceb2051105866bb6f9a702ccdd7271969e0763")),
        ("encore-active/ns2-runtime/hle/core/hle/service/hid/hid_server.h",
         ("1f3b144324b9014d4e5db64f796019f0e9f4c9a6"
           if selected in {"dfbba1e690128a44da755494c422ed1e6bdeb3c3", "47e9735a63c94ca42ec80412c6fcfd84a4910a53", "f007f3d539a523607fbef8b8895c2833e5b7af8c", "b3e6f9943bd46fda050ecb8151c4bb06e5251117", "7535dc9e5e7f0060b8e448da843f96882a2ce320"} else "e82f2486c79ac6aa2da5549619fb555c628d7afb")),
    ):
        raw = (V / relative).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        assert actual == expected, ("Reviewed NS2 HID source drift", relative, actual)
    if gsv_syncpt_201_revision:
        # GSV cmd201 is admitted only because the real per-KProcess
        # NativeSyncptState is already allocated by the active constructor.
        # Verify the EXACT GSV owner pair, then reuse unchanged source seals.
        for relative, expected in (
            ("encore-active/ns2-runtime/graphics_supervisor/core/hle/service/am/service/graphics_supervisor.cpp",
             ("15302603f3713b5a80be053d2d58a0f410cffaa7" if vi2_indexed_event_revision else
               "91cdef4f7f28f5600ecd668904cf7d47ee0e9180" if gsv_transfer_memory_revision else
               "085e934b85fe6289988641b8ea2d64bf1a9a6d91" if gsv_native_115_revision else
               "38b2aed6deeec62ed82e173e6362ab1ba3e46737" if gsv_gpu_403_revision else
               "5e621a6cff708c5a2e2ab1b856990d0b5afc96f7")),
            ("encore-active/ns2-runtime/graphics_supervisor/core/hle/service/am/service/graphics_supervisor.h",
             ("dad20285d5e14e28c268d9616b2662cc0be3a68a" if gsv_native_115_revision else
               "20bcdf77ac18db399d064a22da4a4cdf8cddcd9d" if gsv_gpu_403_revision else
               "d0837e45e672ee8043c01f1593af2a4d33658453")),
        ):
            raw = (V / relative).read_bytes()
            actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
            assert actual == expected, ("Reviewed NS2 GSV syncpoint context drift", relative, actual)
    selected = "b65d8d9673475433f0b6eac72eb304bf23141666"
    original_vendor_pin = selected
    ns2_gsv_497_dual = True
# The NS2 GSV COPY-descriptor correction is two commits beyond the
# previously sealed vendor tree. Only graphics_supervisor.cpp and its source
# contract changed; check both exact blobs, then replay all unchanged FC27,
# BufferCache, NVDRV and kernel source receipts under their reviewed baseline.
if selected in {"ac55a39658c8029a0ec900475234012ae6bf6289", "a7b9008340ccf03e4f63c180d820631858fe935e", "565f143c27443553b60ca1b21cc1094caa23ceb5", "010d5c61cefd62cbb5d27102cd9a2350fa0e69ce", "3460d10e60bff7dd8b057f592eb671cc35eddd25", "6f6f7f4cb154aa227eaf4d54330ff9d817b77ecb", "ce27bdd184c60d1f096ef1495c0ef7e5b7f0cdf0", "01c942171fea39c1f7cf31d13ab36895aebb593a", "dcf7116dd2c536e05c80d83ff9dbf30caa5cc109", "b65d8d9673475433f0b6eac72eb304bf23141666"}:
    for relative, expected in (
        ("encore-active/ns2-runtime/graphics_supervisor/core/hle/service/am/service/graphics_supervisor.cpp",
         ("15302603f3713b5a80be053d2d58a0f410cffaa7" if vi2_indexed_event_revision else
               "91cdef4f7f28f5600ecd668904cf7d47ee0e9180" if gsv_transfer_memory_revision else
               "085e934b85fe6289988641b8ea2d64bf1a9a6d91" if gsv_native_115_revision else
           "38b2aed6deeec62ed82e173e6362ab1ba3e46737" if gsv_gpu_403_revision else
           "5e621a6cff708c5a2e2ab1b856990d0b5afc96f7" if gsv_syncpt_201_revision else
           "747c9a0b5461fc1975fa373997064e3dc401a9a3")),
        ("tests/ns2_syncpt_bootstrap_source.py",
         "69723ef7bd1d47af5086052882d0749cc817f64a"),
    ):
        raw = (V / relative).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        assert actual == expected, ("Selected NS2 GSV COPY descriptor source drift", relative, actual)
    if selected in {"565f143c27443553b60ca1b21cc1094caa23ceb5", "010d5c61cefd62cbb5d27102cd9a2350fa0e69ce", "3460d10e60bff7dd8b057f592eb671cc35eddd25", "6f6f7f4cb154aa227eaf4d54330ff9d817b77ecb", "ce27bdd184c60d1f096ef1495c0ef7e5b7f0cdf0", "01c942171fea39c1f7cf31d13ab36895aebb593a", "dcf7116dd2c536e05c80d83ff9dbf30caa5cc109", "b65d8d9673475433f0b6eac72eb304bf23141666"}:
        protocol = (V / "encore-active/ns2-runtime/hle/core/hle/service/am/service/graphics_supervisor_protocol.h").read_bytes()
        protocol_blob = hashlib.sha1(b"blob " + str(len(protocol)).encode() + bytes([0]) + protocol).hexdigest()
        expected_protocol = "e416a9d4a9611c501e1349c7cbcfa83e2640712e" if vi2_indexed_event_revision else "2ab3a49da7843d2b1b0aa7b0d66c702cdbc9326d" if gsv_transfer_memory_revision else "661ff841efe8ea16fe0da557bb791596f334c6b5" if gsv_native_115_revision else "54f295b1ef7a0482a851a93579e66952b335ba9b" if gsv_gpu_403_revision else "4a35519c4f01cc4c1b604787bfbb139161f64a05" if selected in {"3460d10e60bff7dd8b057f592eb671cc35eddd25", "6f6f7f4cb154aa227eaf4d54330ff9d817b77ecb", "ce27bdd184c60d1f096ef1495c0ef7e5b7f0cdf0", "01c942171fea39c1f7cf31d13ab36895aebb593a", "dcf7116dd2c536e05c80d83ff9dbf30caa5cc109", "b65d8d9673475433f0b6eac72eb304bf23141666"} else "6ce5ba02c2032237f81d9684da9e56cfbfb831c0"
        assert protocol_blob == expected_protocol, ("NS2 GSV bootstrap hint source drift", protocol_blob)
    if selected in {"ce27bdd184c60d1f096ef1495c0ef7e5b7f0cdf0", "01c942171fea39c1f7cf31d13ab36895aebb593a", "dcf7116dd2c536e05c80d83ff9dbf30caa5cc109", "b65d8d9673475433f0b6eac72eb304bf23141666"}:
        # appletOE retry ABI: only the reviewed NS2 owner and its existing source
        # regression changed after the last pinned vendor revision.
        for relative, expected in (
            ("encore-active/ns2-runtime/hle/core/hle/service/am/service/application_proxy_service.cpp",
             ("b1acd90a74bceb03c900a505e217f484f6ecd18f" if original_vendor_pin == "b65d8d9673475433f0b6eac72eb304bf23141666" else "849baf7bfe243734ee49c9e7617462665746d5f1")),
            ("tests/ns2_early_hle_services_source.py",
             ("86a8c538ebed7dd17021b54e35dd43a19802c3d6" if original_vendor_pin == "b65d8d9673475433f0b6eac72eb304bf23141666" else "c644d7e6d9a95a0a9718acd70188cd83c3ae6310")),
        ):
            raw = (V / relative).read_bytes()
            actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
            assert actual == expected, ("NS2 appletOE retry ABI source drift", relative, actual)
    selected = "eadc6e798def18417e50db6a03a291440429d795"
# This revert commit has the same complete vendor Git tree as the
# reviewed pre-rollback pin. Reject any different source tree, including
# newly added or removed files, before reusing its byte-exact source gates.
if selected == "03b264ee3e5ac7d7bbf89d3a9c51a3aff93a4433":
    actual_tree = subprocess.check_output(
        ["git", "-C", str(ROOT / "vendor"), "rev-parse", "HEAD^{tree}"],
        text=True).strip()
    assert actual_tree == "301f91c2ee0eb4e5d86baba9b1036c57f6d5aa04", ("Vendor revert tree drift", actual_tree)
    selected = "eadc6e798def18417e50db6a03a291440429d795"
# The GSV 4->101->1402 correction changes only the selected bootstrap
# state machine; retain an exact source seal on the newly admitted runtime.
if selected in {"917ccdc1cf772b9312b19888eea181b8e114334b", "0c1bd95c896f6ddc7870a245ffca51b2ac7e2932", "eadc6e798def18417e50db6a03a291440429d795"}:
    owner = V / "encore-active/ns2-runtime/hle/core/hle/service/am/service/graphics_supervisor_bootstrap.h"
    raw = owner.read_bytes()
    actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
    expected = ("024d652f5fbcbd9043507de6b6518c5b86d1e212" if gsv_transfer_memory_revision else
                "703eae24222c4d19d635fc4aa9a24d69f9520275" if gsv_gpu_403_revision else
                "11d548eb338a5b75bf3a87a6adb6aa6aa302e017" if ns2_gsv_497_dual else
                "11e7c9d0569a175567083367e485cbf75cbc2207" if ns2_gsv_497_v2 else
                "0f6b6960687501ef88b65ae0f3f4d0fd0693826a")
    assert actual == expected, (
        "NS2 GSV optional-bind bootstrap source drift", actual)

# The FC27 corrected rasterizer is the exact reviewed fail-closed successor.
# Its new source cannot silently fall back to an unrelated integer varying.
if selected in {"0c1bd95c896f6ddc7870a245ffca51b2ac7e2932", "eadc6e798def18417e50db6a03a291440429d795"}:
    owner = V / "encore-active/eden-vulkan/vulkan_rasterizer.cpp"
    raw = owner.read_bytes()
    actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
    expected_raster = ("71d097b9a83028dfad9370792c905bb3bfccfd5a"
                       if original_vendor_pin in {"01c942171fea39c1f7cf31d13ab36895aebb593a", "dcf7116dd2c536e05c80d83ff9dbf30caa5cc109", "b65d8d9673475433f0b6eac72eb304bf23141666"}
                       else "f23ad861761d53b59b8c83ae6003c089ae688060")
    assert actual == expected_raster, actual
    source = raw.decode("utf-8")
    assert "if (!source && !attribute_handle_source) {" in source

# The 2nd merge preserves the newer NS1 DMA/cache owner from main
# together with the NS2 IPC/ExeFS owners. Seal *both* the real GPU owner and
# new service files before accepting the merged gitlink. No fallback hashes.
if selected in {"17c95ef233a9a0e508e50ada4ae9dc53a300c46c", "082cd1b77c7df80dc422eae5ba59d9cd33e48dc4", "e0fced3a091495e70362d8c4ca072942f027af24", "491fa7e2388d46e23827b1459360a5d7f4a2814b", "b177deb8282b14e1521485f5ac63bd7ccc9ca7ef", "06fc7dc2e0a00e00f831dfd78ae78087736276a3", "850086c79ec40838663989a81f33ba8ea2f15f6a"}:
    for relative, expected in (
        ("encore-active/ns2-runtime/am/core/hle/service/am/service/application_functions.cpp", "9719348d36515464724ce82f62aafac1d5182647"),
        ("encore-active/ns2-runtime/am/core/hle/service/am/service/application_functions.h", "76f1283f30304f1c4b9d7db2ad0e7c833a0da487"),
        ("encore-active/ns2-runtime/hle/core/hle/service/am/service/application_proxy_service.cpp", "696b11e0418b27325204f6775d62f438fcba4923"),
        ("encore-active/ns2-runtime/hle/core/hle/service/am/service/application_proxy_service.h", "e534f8da6c4b88fe042cff8098dd386dcc29a8e4"),
        ("encore-active/ns2-runtime/hle/core/hle/service/am/service/application_proxy.cpp", "d6b14213485b56aefbd9736c8f0e6a2a2b4fa38c"),
        ("encore-active/ns2-runtime/hle/core/hle/service/am/service/application_proxy.h", "03cf286dd642a3e517c7fa4950850603038c6d6b"),
        ("encore-active/ns2-runtime/hle/core/hle/service/am/service/performance_functions.h", "be4ce2bee44ac77e4f8b8bbe9e18cad11ab47b19"),
        ("encore-active/ns2-runtime/metadata/core/loader/deconstructed_rom_directory.cpp", "60adeedefd3bb7c68132b9ef525eb1a0d41a3415"),
        ("encore-active/eden-core/src/video_core/buffer_cache/buffer_cache.h", "d40082a0c849790d25a4d1d28e003087eefd84a1"),
        ("encore-active/eden-vulkan/vulkan_rasterizer.cpp", "9da620ea3f4a4e0ab22e9747bf4e1058c09ce20b"),
        ("tests/ns2-extracted-update-romfs-source.py", "85daa8f4eb6aca2c6ec4bd24a2556e594e51a646"),
        ("tests/ns2_early_hle_services_source.py", "3e3377c8feeab37f392959fcdbb8906289bf7b86"),
    ):
        body = (V / relative).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(body)).encode() + bytes([0]) + body).hexdigest()
        assert actual == expected, ("Merged engine/vendor source drift", relative, actual)
    print("ENCORE_MERGED_NS1_DMA_NS2_BOOT_SOURCE_PASS owners=12")

# The follow-up vendor change affects only the compiled NS2 GSV control
# plane and its pre-existing test; GPU/BufferCache and AM still pass the exact
# source seals above. A failed TIPC 305/497 must never move a null handle.
if selected in {"082cd1b77c7df80dc422eae5ba59d9cd33e48dc4", "e0fced3a091495e70362d8c4ca072942f027af24", "491fa7e2388d46e23827b1459360a5d7f4a2814b", "b177deb8282b14e1521485f5ac63bd7ccc9ca7ef", "06fc7dc2e0a00e00f831dfd78ae78087736276a3", "850086c79ec40838663989a81f33ba8ea2f15f6a"}:
    for relative, expected in (
        ("encore-active/ns2-runtime/graphics_supervisor/core/hle/service/am/service/graphics_supervisor.cpp",
         ("90be32737f454554125156cf468f58154dde40d4" if selected == "850086c79ec40838663989a81f33ba8ea2f15f6a" else
          "c9193e7ce505353c87f57e8a063cbdbf5b072f43" if selected == "06fc7dc2e0a00e00f831dfd78ae78087736276a3" else
          "8457d9a9a53725e6c1f15575c1151038f2457643")),
        ("tests/ns2_syncpt_bootstrap_source.py",
         ("21fb7c886286a39eaec5ca4495bfba1bb55584b1" if selected == "850086c79ec40838663989a81f33ba8ea2f15f6a" else
          "41d6f0514f281bfb65cad052c2fb61cfa9d749b2" if selected == "06fc7dc2e0a00e00f831dfd78ae78087736276a3" else
          "51beddbe0454039c23728f39f7c84d05325fd8cf" if selected in {"e0fced3a091495e70362d8c4ca072942f027af24", "491fa7e2388d46e23827b1459360a5d7f4a2814b", "b177deb8282b14e1521485f5ac63bd7ccc9ca7ef", "06fc7dc2e0a00e00f831dfd78ae78087736276a3", "850086c79ec40838663989a81f33ba8ea2f15f6a"} else
          "eb150745a18068366885299f82eacf42045cb50e")),
    ):
        body = (V / relative).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(body)).encode() + bytes([0]) + body).hexdigest()
        assert actual == expected, ("NS2 GPU/VI2 session source drift", relative, actual)
    print("ENCORE_NS2_GSV_NO_NULL_SESSION_SOURCE_PASS owners=2")

# Active GPU session and worker must roll back incomplete native VA
# identity transactions before a failed handle can be retried.
if selected in {"491fa7e2388d46e23827b1459360a5d7f4a2814b", "b177deb8282b14e1521485f5ac63bd7ccc9ca7ef", "06fc7dc2e0a00e00f831dfd78ae78087736276a3", "850086c79ec40838663989a81f33ba8ea2f15f6a"}:
    for relative, expected in (
        ("encore-active/ns2-runtime/gpu_session/core/hle/service/am/service/gpu_session.cpp",
         "fc9f0c7b99b6905876143975ecc16e8d2c580141"),
        ("encore-active/ns2-runtime/gpu_session/core/hle/service/am/service/gpu_worker.cpp",
         "c65544f3a337b8ef5673041da07cafc7c1133ff5"),
        ("tests/ns2_gpu_identity_mapping_source.py",
         ("955c5cbc1171d2d594d4bed1935280ca418365ce" if selected in {"b177deb8282b14e1521485f5ac63bd7ccc9ca7ef", "06fc7dc2e0a00e00f831dfd78ae78087736276a3", "850086c79ec40838663989a81f33ba8ea2f15f6a"} else
          "4f942ba7f8f75ac9d7501cecf5be17fa70903a52")),
    ):
        body = (V / relative).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(body)).encode() + bytes([0]) + body).hexdigest()
        assert actual == expected, ("NS2 GPU VA identity rollback drift", relative, actual)
    print("ENCORE_NS2_GPU_VA_ROLLBACK_SOURCE_PASS owners=3")

# A native Switch 2 GPU session may only be published after process
# generation registration succeeds; channel Bind and shader tickets require it.
if selected in {"b177deb8282b14e1521485f5ac63bd7ccc9ca7ef", "06fc7dc2e0a00e00f831dfd78ae78087736276a3", "850086c79ec40838663989a81f33ba8ea2f15f6a"}:
    path = "encore-active/ns2-runtime/gpu_session/core/hle/service/am/service/gpu_worker_shared.cpp"
    body = (V / path).read_bytes()
    actual = hashlib.sha1(b"blob " + str(len(body)).encode() + bytes([0]) + body).hexdigest()
    assert actual == "34142613b8ee0389509406da540811ba35eae9d6", (
        "NS2 native process admission source drift", path, actual)
    print("ENCORE_NS2_GPU_PROCESS_ADMISSION_SOURCE_PASS owners=1")

# NS2 GSV 1402: the native graphics SDK requires a process-bound
# nvsrv INvDrvServices child. Seal all compiled C++ owners: both GSV service
# and the unchanged NS1 NVDRV protocol with a new explicit NS2 init helper.
if selected in {"06fc7dc2e0a00e00f831dfd78ae78087736276a3", "850086c79ec40838663989a81f33ba8ea2f15f6a"}:
    for relative, expected in (
        ("encore-active/ns2-runtime/graphics_supervisor/core/hle/service/am/service/graphics_supervisor.h",
         ("55e82ad0667cd925fd72b4c5b45c150f3d743708" if selected == "850086c79ec40838663989a81f33ba8ea2f15f6a" else
          "8950a03e698f65b5682849d19baf038c5756145c")),
        ("sources/eden/src/core/hle/service/nvdrv/nvdrv_interface.h",
         "b32fe29a11b0ffee941eb32043043553e67a28b5"),
        ("sources/eden/src/core/hle/service/nvdrv/nvdrv_interface.cpp",
         "a47b4a447c74e2710678c4e881b6b2f949a373cf"),
    ):
        body = (V / relative).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(body)).encode() + bytes([0]) + body).hexdigest()
        assert actual == expected, ("NS2 GSV nvsrv CMIF source drift", relative, actual)
    print("ENCORE_NS2_GSV_REAL_NVSRV_SOURCE_PASS owners=3")

if selected == "2a450d43d1d23d3e8b1667e396613f62c69c26d7":
    # Verify every newly selected Switch 2 IPC owner plus the reviewed
    # GPU source and M2MF owner, not merely the vendor gitlink.
    for relative, expected in (
        ("encore-active/ns2-runtime/hle/core/hle/service/am/service/application_proxy_service.cpp", "696b11e0418b27325204f6775d62f438fcba4923"),
        ("encore-active/ns2-runtime/hle/core/hle/service/am/service/application_proxy_service.h", "e534f8da6c4b88fe042cff8098dd386dcc29a8e4"),
        ("encore-active/ns2-runtime/hle/core/hle/service/am/service/application_proxy.cpp", "7064b86080d5a114129d1dd080aee52c1c5fe408"),
        ("encore-active/ns2-runtime/hle/core/hle/service/am/service/application_proxy.h", "03494ac7cbb75d7a7c2e7d914fda68e7301f21c7"),
        ("encore-active/ns2-runtime/hle/core/hle/service/am/service/performance_functions.h", "5ea8a369340ea0700dfb3ede774591b2ce2f5220"),
        ("encore-active/ns2-runtime/gpu_dispatch/video_core/control/channel_state.cpp", "dd30183f72a9a9dfc2a17700db263f85e4d77596"),
        ("encore-active/eden-vulkan/vulkan_rasterizer.cpp", "9da620ea3f4a4e0ab22e9747bf4e1058c09ce20b"),
    ):
        raw = (V / relative).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        assert actual == expected, ("Selected NS2 IPC source drift", relative, actual)
    print("ENCORE_NS2_TYPED_PROXY_SOURCE_PASS owners=7")

if selected == "510f1efde545357fe8095a812df32251ee546285":
    # The sole two-file successor introduces the typed Switch 2 appletOE
    # command 10 owner and its existing source contract. All historical
    # FC27/NS2 owner receipts remain byte-identical to the reviewed parent.
    for path, expected in (
        ("encore-active/ns2-runtime/hle/core/hle/service/am/service/application_proxy_service.cpp",
         "1e6f2592e34845d9b9b3aa3d152c78c4fed66639"),
        ("tests/ns2_early_hle_services_source.py",
         "86c342996d7e77f53c13d265c977cc18f470339f"),
    ):
        raw = (V/path).read_bytes()
        actual = hashlib.sha1(b"blob "+str(len(raw)).encode()+bytes([0])+raw).hexdigest()
        assert actual == expected, ("NS2 appletOE selected owner drift", path, actual)
    selected = "7fc673495b2ee18d5216023280057a42aa78d46c"
if selected == "7fc673495b2ee18d5216023280057a42aa78d46c":
    for path, expected in (
        ("encore-active/ns2-runtime/gamechat/core/hle/service/friend/friend.cpp", "ceb8b4afa7c0f19af3fe209fd8ca8d848a66d2cb"),
        ("encore-active/ns2-runtime/graphics_supervisor/core/hle/service/am/service/graphics_supervisor.cpp", "5d83ac9f7e7c3df2201b1ddf5e9458a7d802bcc4"),
        ("encore-active/ns2-runtime/graphics_supervisor/core/hle/service/am/service/graphics_supervisor.h", "be4d6eaaa43ee247b61d835a7b280fe26aa8eb63"),
        ("encore-active/ns2-runtime/hle/core/hle/service/am/service/native_image_layout.h", "978b0a162c0fa6043942e96e57c7c464dd167c53"),
    ):
        raw=(V/path).read_bytes()
        actual=hashlib.sha1(b"blob "+str(len(raw)).encode()+bytes([0])+raw).hexdigest()
        assert actual == expected, ("NS2 GameChat owner drift", path, actual)
    selected = "ab417b59c5f7f4613ff27386be05c0644d0ed776"
if selected in {"372a83d95622f152211fe91afa05d1e60ce84bea", "a3cc07ff68f8154543f2b07a6b3e6c01f9922ab9", "ab417b59c5f7f4613ff27386be05c0644d0ed776"}:
    raw=(V/"encore-active/eden-core/src/video_core/buffer_cache/buffer_cache_base.h").read_bytes()
    actual=hashlib.sha1(b"blob "+str(len(raw)).encode()+bytes([0])+raw).hexdigest()
    assert actual == "63ef9b07b37bdc4bc9588dd77639358010e545dc", ("Shared 32-slot BufferCacheBase drift",actual)
if selected in {"a3cc07ff68f8154543f2b07a6b3e6c01f9922ab9", "ab417b59c5f7f4613ff27386be05c0644d0ed776"}:
    raw=(V/"encore-active/eden-core/src/core/file_sys/vfs/vfs_real.cpp").read_bytes()
    actual=hashlib.sha1(b"blob "+str(len(raw)).encode()+bytes([0])+raw).hexdigest()
    assert actual == "097335e42a0f569a51f58417f0cfd6239f474136", ("PS5 VFS128 owner drift",actual)
if selected == "ab417b59c5f7f4613ff27386be05c0644d0ed776":
    for path, expected in (("encore-active/eden-threading/src/core/hle/kernel/k_server_session.cpp", "5bd8cd81c2bf8d32f0d65406881b8286a06ca771"),
                           ("encore-active/eden-threading/native-hle-overrides.cmake", "0ed9f8520019c07874c157c97ded3864c07a8a32")):
        raw=(V/path).read_bytes()
        actual=hashlib.sha1(b"blob "+str(len(raw)).encode()+bytes([0])+raw).hexdigest()
        assert actual == expected, ("NS2 IPC peer owner drift", path, actual)
if selected == "67759611edc13414c112ea9d2b6664d54827a200":
    # Confirm the new release modifies only its reviewed RomFS owner/test;
    # actual GitHub commit comparison is documented in the incident register.
    for relative, expected in {
        "encore-active/eden-core/src/core/file_sys/romfs_factory.cpp":
            "4775cf98c3bfbc587402928bad424dcb471047a0",
        "tests/ns2_romfs_program_index_fallback_host.py":
            "abac08b40623febec02c58d2703b4ec3676b88f0",
        "encore-active/ns2-runtime/gpu_dispatch/video_core/control/channel_state.cpp":
            "dd30183f72a9a9dfc2a17700db263f85e4d77596",
    }.items():
        raw = (V/relative).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        assert actual == expected, ("RomFS-only successor drift",relative,actual)

if selected in {"c15cdfe96a3d836bf32ba21b8070088add81cdc9",
                "729f7e5a734b5a890a7bbf3ab60ce1100492af13", "1a09972eea6f473fda1b714efe84cd52219bf681", "3e6647827122c34704c2699a6f5e9b20fff3e9a6", "6d64217ea5804fb86dbf57685a3da0cb1d45ba32", "3f1fcfef119ca50dd630f0518a7fae1b96c7a85a", "0e4e96df638fc29c3bd2a8fcfe9f50821c5e5b3a", "9136d2e88c43233bcd029f22bdfda0e5c94a552f", "75ef34d7ef7f68b5eb4f1c6d0d99b6cbc55742d6", "34f02a3800cb6fb5330c099c81571ab03fd69ae1", "0d75406e36a3676b45184670093f0ecf652aab2f", "372a83d95622f152211fe91afa05d1e60ce84bea", "a3cc07ff68f8154543f2b07a6b3e6c01f9922ab9", "ab417b59c5f7f4613ff27386be05c0644d0ed776", "372a83d95622f152211fe91afa05d1e60ce84bea", "a3cc07ff68f8154543f2b07a6b3e6c01f9922ab9", "ab417b59c5f7f4613ff27386be05c0644d0ed776"}:
    # PR #194 is rolled back only in production GPU cache protection.
    # Preserve newly reviewed NS2 RomFS and A64 uniform 16MiB ABI.
    for relative, expected in {
        "encore-active/eden-core/overrides/core/device_memory_manager.inc":
            "daf493ce6e863397ec44bfae467c4f7533570477",
        "encore-active/eden-vulkan/vulkan_rasterizer.cpp":
            "01c6880e5a8836da45601b0a3cb7c0fd6c46cf35",
        "encore-active/eden-core/src/core/file_sys/romfs_factory.cpp":
            "4775cf98c3bfbc587402928bad424dcb471047a0",
        "tests/fc27_deferred_page_protection_host.py":
            ("ae967badcfef7e098ac2620b789a1138fad79058" if selected in {"6d64217ea5804fb86dbf57685a3da0cb1d45ba32", "3f1fcfef119ca50dd630f0518a7fae1b96c7a85a", "0e4e96df638fc29c3bd2a8fcfe9f50821c5e5b3a", "9136d2e88c43233bcd029f22bdfda0e5c94a552f", "75ef34d7ef7f68b5eb4f1c6d0d99b6cbc55742d6", "34f02a3800cb6fb5330c099c81571ab03fd69ae1", "0d75406e36a3676b45184670093f0ecf652aab2f", "372a83d95622f152211fe91afa05d1e60ce84bea", "a3cc07ff68f8154543f2b07a6b3e6c01f9922ab9", "ab417b59c5f7f4613ff27386be05c0644d0ed776", "372a83d95622f152211fe91afa05d1e60ce84bea", "a3cc07ff68f8154543f2b07a6b3e6c01f9922ab9", "ab417b59c5f7f4613ff27386be05c0644d0ed776"} else "876ebf0f43ffc3999d7ed6d983160d3447bc15f0" if selected == "3e6647827122c34704c2699a6f5e9b20fff3e9a6" else "cb821c1aaab3f968ce25d7ac92d489e01ba3b8f6" if selected == "1a09972eea6f473fda1b714efe84cd52219bf681" else "7051e22341bf7a5374221700834917fc74e4f746"),
    }.items():
        raw = (V/relative).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        assert actual == expected, ("Sync rollback source drift",relative,actual)
    if selected in {"729f7e5a734b5a890a7bbf3ab60ce1100492af13", "1a09972eea6f473fda1b714efe84cd52219bf681", "3e6647827122c34704c2699a6f5e9b20fff3e9a6", "6d64217ea5804fb86dbf57685a3da0cb1d45ba32", "3f1fcfef119ca50dd630f0518a7fae1b96c7a85a", "0e4e96df638fc29c3bd2a8fcfe9f50821c5e5b3a", "9136d2e88c43233bcd029f22bdfda0e5c94a552f", "75ef34d7ef7f68b5eb4f1c6d0d99b6cbc55742d6", "34f02a3800cb6fb5330c099c81571ab03fd69ae1", "0d75406e36a3676b45184670093f0ecf652aab2f", "372a83d95622f152211fe91afa05d1e60ce84bea", "a3cc07ff68f8154543f2b07a6b3e6c01f9922ab9", "ab417b59c5f7f4613ff27386be05c0644d0ed776", "372a83d95622f152211fe91afa05d1e60ce84bea", "a3cc07ff68f8154543f2b07a6b3e6c01f9922ab9", "ab417b59c5f7f4613ff27386be05c0644d0ed776"}:
        for relative, expected in {
            "encore-active/ns2-helpers/include/core/loader/ns2_svc_trace.h":
                "86e8e7e96b5eda5b6b98ccd3c7e6ce76d4275c86",
            "encore-active/ns2-runtime/gpu_access_svc/core/hle/kernel/svc.cpp":
                "09ae2494b2b6f620a25ab549c06c69045a9fb73d",
            "tests/ns2_recent_svc_fault_trace_host.py":
                "79d8d7294e37e141d6c669d9b55fa5a02d94287e",
        }.items():
            raw = (V/relative).read_bytes()
            actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
            assert actual == expected, ("Quiet NS2 SVC witness drift",relative,actual)
    if selected in {"1a09972eea6f473fda1b714efe84cd52219bf681", "3e6647827122c34704c2699a6f5e9b20fff3e9a6", "6d64217ea5804fb86dbf57685a3da0cb1d45ba32", "3f1fcfef119ca50dd630f0518a7fae1b96c7a85a", "0e4e96df638fc29c3bd2a8fcfe9f50821c5e5b3a", "9136d2e88c43233bcd029f22bdfda0e5c94a552f", "75ef34d7ef7f68b5eb4f1c6d0d99b6cbc55742d6", "34f02a3800cb6fb5330c099c81571ab03fd69ae1", "0d75406e36a3676b45184670093f0ecf652aab2f", "372a83d95622f152211fe91afa05d1e60ce84bea", "a3cc07ff68f8154543f2b07a6b3e6c01f9922ab9", "ab417b59c5f7f4613ff27386be05c0644d0ed776", "372a83d95622f152211fe91afa05d1e60ce84bea", "a3cc07ff68f8154543f2b07a6b3e6c01f9922ab9", "ab417b59c5f7f4613ff27386be05c0644d0ed776"}:
        for relative, expected in {
            "encore-active/ns2-astc/include/video_core/texture_cache/texture_cache.h": ("c7cb95ecaf388b925fc29582499bbd4b54a77f75" if selected in {"6d64217ea5804fb86dbf57685a3da0cb1d45ba32", "3f1fcfef119ca50dd630f0518a7fae1b96c7a85a", "0e4e96df638fc29c3bd2a8fcfe9f50821c5e5b3a", "9136d2e88c43233bcd029f22bdfda0e5c94a552f", "75ef34d7ef7f68b5eb4f1c6d0d99b6cbc55742d6", "34f02a3800cb6fb5330c099c81571ab03fd69ae1", "0d75406e36a3676b45184670093f0ecf652aab2f", "372a83d95622f152211fe91afa05d1e60ce84bea", "a3cc07ff68f8154543f2b07a6b3e6c01f9922ab9", "ab417b59c5f7f4613ff27386be05c0644d0ed776", "372a83d95622f152211fe91afa05d1e60ce84bea", "a3cc07ff68f8154543f2b07a6b3e6c01f9922ab9", "ab417b59c5f7f4613ff27386be05c0644d0ed776"} else "859a9e46fb63a97fee82c8ea6b1566317264f98f" if selected == "3e6647827122c34704c2699a6f5e9b20fff3e9a6" else "0d99f9a861c645562519f71d62f4f49bfedd8101"),
            "tests/ns1_r23_18_tir_host.py": ("753df3ca146cba983057801df36dcf9db0b5fc6b" if selected in {"6d64217ea5804fb86dbf57685a3da0cb1d45ba32", "3f1fcfef119ca50dd630f0518a7fae1b96c7a85a", "0e4e96df638fc29c3bd2a8fcfe9f50821c5e5b3a", "9136d2e88c43233bcd029f22bdfda0e5c94a552f", "75ef34d7ef7f68b5eb4f1c6d0d99b6cbc55742d6", "34f02a3800cb6fb5330c099c81571ab03fd69ae1", "0d75406e36a3676b45184670093f0ecf652aab2f", "372a83d95622f152211fe91afa05d1e60ce84bea", "a3cc07ff68f8154543f2b07a6b3e6c01f9922ab9", "ab417b59c5f7f4613ff27386be05c0644d0ed776", "372a83d95622f152211fe91afa05d1e60ce84bea", "a3cc07ff68f8154543f2b07a6b3e6c01f9922ab9", "ab417b59c5f7f4613ff27386be05c0644d0ed776"} else "7c225ac2065a1721eb53cc034ea3bc4e3b581770" if selected == "3e6647827122c34704c2699a6f5e9b20fff3e9a6" else "520c5eb05f23c5fc6ad4438c9f6df774533644e1"),
            "tests/fc27_deferred_page_protection_host.py": ("ae967badcfef7e098ac2620b789a1138fad79058" if selected in {"6d64217ea5804fb86dbf57685a3da0cb1d45ba32", "3f1fcfef119ca50dd630f0518a7fae1b96c7a85a", "0e4e96df638fc29c3bd2a8fcfe9f50821c5e5b3a", "9136d2e88c43233bcd029f22bdfda0e5c94a552f", "75ef34d7ef7f68b5eb4f1c6d0d99b6cbc55742d6", "34f02a3800cb6fb5330c099c81571ab03fd69ae1", "0d75406e36a3676b45184670093f0ecf652aab2f", "372a83d95622f152211fe91afa05d1e60ce84bea", "a3cc07ff68f8154543f2b07a6b3e6c01f9922ab9", "ab417b59c5f7f4613ff27386be05c0644d0ed776", "372a83d95622f152211fe91afa05d1e60ce84bea", "a3cc07ff68f8154543f2b07a6b3e6c01f9922ab9", "ab417b59c5f7f4613ff27386be05c0644d0ed776"} else "876ebf0f43ffc3999d7ed6d983160d3447bc15f0" if selected == "3e6647827122c34704c2699a6f5e9b20fff3e9a6" else "cb821c1aaab3f968ce25d7ac92d489e01ba3b8f6"),
        }.items():
            raw = (V/relative).read_bytes()
            actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
            assert actual == expected, ("Selected PS5 F07 TextureCache source drift", relative, actual)
    assert not (V/"encore-active/eden-core/overrides/core/deferred_cached_updates.h").exists()
    subprocess.run(["python3", "-B", str(V/"tests/fc27_deferred_page_protection_host.py")],
                   check=True, timeout=240)
    print("FC27_SYNCHRONOUS_PROTECTION_RESTORED source=exact test=host ps5=unverified")

if selected in {"8153654a2f1fe809fb2caa28dcadca90a7661446", "6c38328fbef33de747f5c31ea30d13541a513a4a", "8e564f61e6c8b86149ce0a0d6d2aa323a268dda6", "67759611edc13414c112ea9d2b6664d54827a200"}:
    reviewed_fc27_owners = {
        "encore-active/eden-core/overrides/core/deferred_cached_updates.h": "33262f511777cdd1b4a74ac0cd6dc39caa12c9d0",
        "encore-active/eden-core/overrides/core/device_memory_manager.inc": "852a0272696c7ce182bc05aee92bc7cbb195446b",
        "encore-active/eden-vulkan/vulkan_rasterizer.cpp": "38d5630570675088a0620ef533112bb314a40ae8",
    }
    for relative, expected_blob in reviewed_fc27_owners.items():
        body = (V/relative).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(body)).encode() + bytes([0]) + body).hexdigest()
        assert actual == expected_blob, ("FC27 reviewed source changed", relative, actual)
    if selected == "6c38328fbef33de747f5c31ea30d13541a513a4a":
        # One reviewed PS5-only A64 table capacity delta; the FC27 source
        # seal above still requires exact unchanged Vulkan/guest-write blobs.
        reviewed_dispatch = (V/"encore-active/eden-core/src/dynarmic/backend/x64/"
                             "a64_emit_x64_standard.h").read_bytes()
        dispatch_blob = hashlib.sha1(b"blob " + str(len(reviewed_dispatch)).encode()
                                     + bytes([0]) + reviewed_dispatch).hexdigest()
        assert dispatch_blob == "633dceaf5e7adf2b17a6b97af3862e9c7ecd1147", dispatch_blob
    elif selected in {"8e564f61e6c8b86149ce0a0d6d2aa323a268dda6", "67759611edc13414c112ea9d2b6664d54827a200"}:
        # Source-exact P0 rollback: stable A64 class has no PS5_NATIVE-dependent member size.
        repaired_dispatch = (V/"encore-active/eden-core/src/dynarmic/backend/x64/"
                             "a64_emit_x64_standard.h").read_bytes()
        dispatch_blob = hashlib.sha1(b"blob " + str(len(repaired_dispatch)).encode()
                                     + bytes([0]) + repaired_dispatch).hexdigest()
        assert dispatch_blob == "205e73772861ce5036370bbe114d60275daf186e", dispatch_blob
    subprocess.run(["python3", "-B", str(V/"tests/fc27_deferred_page_protection_host.py")],
                   check=True, timeout=240)
    print("FC27_DEFERRED_PAGE_PROTECTION_REVIEWED_SOURCE_PASS source=exact host=pass ps5=unverified")

cmake=(ROOT/"headless/CMakeLists.txt").read_text()
for needle in (
    'set(EDEN_R23_ATTRIBUTE_TEXTURE_PASS',
    'ir_opt/texture_pass.cpp',
    'foreach(eden_r23_subgroup_relative IN ITEMS',
    '"ir_opt/constant_propagation_pass.cpp"',
    'set(EDEN_FC27_SSA_SOURCE',
    'set(EDEN_FC27_SSBO_SOURCE',
    'set(EDEN_G11_PROFILE normal)',
    'arm_dynarmic_${bits}_${EDEN_G11_PLATFORM}_${EDEN_G11_PROFILE}.cpp',
    'target_include_directories(video_core BEFORE PRIVATE "${EDEN_SMALL_VECTOR_ROOT}")',
    'set(EDEN_MAINTAINED_THREAD_WORKER_ROOT',
    'eden-core/overrides/thread-worker',
):
    assert needle in cmake,needle

tests=(
    "fc27_xmad_pointer_fold_host.py",
    "fc27_dynamic_texture_static_sampler_host.py",
    "fc27_descriptor_page_fastpath_host.py",
    "fc27_storage_offset_current_host.py",
    "p0_bananza_low_write_current_source.py",
    "ps5_spirv_scalar_constant_cache_host.py",
    "fc27_maxwell_prmt_operand_forms_source.py",
    "shader_bitfield_uextract_fold_host.py",
    "ns2_getinfo_page_size_source.py",
    "ns2_getinfo_vamm_region_source.py",
    "ps5-late-upstream-fixes-source.py",
    "ps5-full-clear-skip-upload-source.py",
    "vulkan_static_pipeline_cache_source.py",
    "shutdown_teardown_lifetime_source.py",
    "shutdown_general_channel_lifetime_source.py",
    "ns2_ampere_imad_negated_addend_host.py",
    "ns2_dynamic_texture_found_bit_limit_host.py",
    "ns2_duskbloods_tld4_imad_host.py",
    "fc27_gpu_page_sibling_preservation_host.py",
    "ns2_ampere_hsetp2_cbuf_host.py",
    "ns2-kprocess-memory-budget-source.py",
    "ns2_alias_64g_upstream_parity_host.py",
    "fc27_waited_pipeline_inline_source.py",
    "fc27_pipeline_teardown_and_syncwait_source.py",
    "ps5_host1x_wait_notification_host.py",
    "ns2_gpu_partition_new_sdk_source.py",
    "ns2_syncpt_bootstrap_source.py",
    "ns2_recent_svc_fault_trace_host.py",
    "ns2_ipc_started_thread_handoff_source.py",
    "ns2_gpu_access_svc_info_types_source.py",
    "ns2_gpu_identity_mapping_source.py",
    "ns2_nvhost_unknown_node_fallback_source.py",
    "ns2_smmu_34bit_capacity_source.py",
    "ns2_syncpoint_shim_source.py",
    "ns2_font_service_source.py",
    "ns2_backport_manifest_preserved_source.py",
    "ns2_sw_blitter_native_tiling_source.py",
    "ns2_native_tiling_activation_source.py",
    "fc27_release_npad_detailed_source.py",
)
for name in tests:
    subprocess.run(["python3","-B",str(V/"tests"/name)],check=True,timeout=240)

print("ENCORE_FINAL_VENDOR_FC27_P0_PASS pin=exact xmad=1 dynamic_sampler=1 descriptor_fastpath=1 storage_audit=1 bananza_low_write=1 scalar_cache=1 bitfield_uextract=1 ns2_getinfo_page_size=1 ns2_getinfo_vamm=1 alpha_ref=1 worker_lost_wake=1 full_clear_upload_elision=1 dynamic_texture_limit=1 duskbloods_shader=1 fc27_sibling_preservation=1 hsetp2_cbuf=1 alias64_vamm32=1 kprocess_abi=1 fc27_pipeline=1 ns2_gpu_memory=1 native_tiling=auth+blitter host1x_wait=1 ipc_handoff=1 ps5=unverified")
