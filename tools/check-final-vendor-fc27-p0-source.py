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
REVIEWED_PINS.add("f69176d429723da5d79251f6b858afc72c5d99e2")
REVIEWED_PINS.add("4795f0a884c06f029c9d06a0a3d09cc0b9cfb791")
REVIEWED_PINS.add("fcd2e6e38bbfd01ab78f56fe8ba5d8039d120531")
REVIEWED_PINS.add("86cbe7ac73a28dcd1e3cdc3609eafca1c7b5dc37")
REVIEWED_PINS.add("a93bc45a1a5858fe1e4bc718a84a2a5a8841ab38")
REVIEWED_PINS.add("e95c1dea796b209b8561c253b82fa69e75fb72b6")
REVIEWED_PINS.add("019e810c5c6c489eab8541f282de6b6379833015")
REVIEWED_PINS.add("de4a6c24d1f118152c849fc87af2783c96348735")
REVIEWED_PINS.add("788badb79f0566c56f51e64fb9aa727f72fdb065")
REVIEWED_PINS.add("0015d90da841622e1642180b9f9de5e2d0c354c9")
REVIEWED_PINS.add("bb575bd8396d78187d2bd56713e84c398ebce512")
REVIEWED_PINS.add("9bd8de9081cc5ad431ecfc62696e9a6f8f2d1ffc")
REVIEWED_PINS.add("2bf3a9a1dab0b8dc6b4157d9084ac66e5e2e547f")
REVIEWED_PINS.add("889b142aa5616d3d00733a7cc1db1562eed291f4")
REVIEWED_PINS.add("201b09121ebbfe0a37a56710b2b7ac118ae5acbb")
REVIEWED_PINS.add("713e18162cf9a0d629cd39ae00b43fb55f9c2823")
REVIEWED_PINS.add("35d639ad802910cfabbaf46bdcfd48a0d2f09ab6")
REVIEWED_PINS.add("f66969397724ab8467c3380ca9c6db1631f79bf3")
REVIEWED_PINS.add("b6e3ecc6943118ba9d321ef5baca9f79b241961f")
REVIEWED_PINS.add("99832a312b1281401c187f381f4826191387eb73")
REVIEWED_PINS.add("258914fc564e223274728b409ee48e39465df7f6")
REVIEWED_PINS.add("932dc1b3c09b172322d65432c26cc017b4922266")
REVIEWED_PINS.add("5062767868c17b1ffe59fd6c5b6c2c4326b9a4bf")
REVIEWED_PINS.add("d4508480fc859cb7a6cb97f259caefe1cd18ba54")
REVIEWED_PINS.add("e3ac953ea0fae3bdecb6850a65ec6ec57984aaeb")
REVIEWED_PINS.add("3a0cf78a9b2c98bed100d817537b4375a48bf72f")
REVIEWED_PINS.add("eb62d96583999c5d159b837dfb9b1b02e8173a9c")
REVIEWED_PINS.add("b0afacfc891bc75da81be3886e5c40430ccbfe6d")
REVIEWED_PINS.add("21bc63493de105c1eb025f3ce5b67011deee72da")
REVIEWED_PINS.add("a9cca6aa9c63722b918b92362c237eed448ff56c")
REVIEWED_PINS.add("0ec5337f26c31e6926bf327411634422c9043369")
REVIEWED_PINS.add("997b4885c045469f09dedf2a5f4e69995a5b1c9a")
REVIEWED_PINS.add("9eefc8f5131350e8ddfb11e617e2e25007925212")
REVIEWED_PINS.add("29350dfa0049885d953ad206fd3ce2b163140cdb")
REVIEWED_PINS.add("bb6285e1998989101adbdc6adecbf9c1e1c17ec0")
selected=subprocess.check_output(["git","rev-parse","HEAD:vendor"],cwd=ROOT,text=True).strip()
gitlink_vendor_pin = selected
# Native NVDRV A:0x0D remap / 4K kind-change successor. Verify the
# exact three current files, then replay inherited immutable source stamps.
if selected == "bb6285e1998989101adbdc6adecbf9c1e1c17ec0":
    for relative, expected in (
        ("encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.cpp", "e120fcee7c85ad7a874c8ffc10f2b3804b707199"),
        ("encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.h", "078f5eef7cf2d24670361d6724ebb3497016ceff"),
        ("tests/ns2_gpu_identity_mapping_source.py", "1c460d3c584914a600e660d141971b99be99f858"),
    ):
        raw = (V / relative).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        assert actual == expected, ("NS2 40-byte remap source drift", relative, actual)
    selected = "29350dfa0049885d953ad206fd3ce2b163140cdb"

# During archival receipt replay, normalize ONLY the three already sealed
# successor blobs to their predecessor identities. All other source files
# retain their real hashes and remain subject to every historical gate.
def archival_receipt_sha(relative, actual):
    if gitlink_vendor_pin != "bb6285e1998989101adbdc6adecbf9c1e1c17ec0":
        return actual
    known = {
        "encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.cpp": ("e120fcee7c85ad7a874c8ffc10f2b3804b707199", "f01d11f32d3f17847cb5c91a740eb070da67c118"),
        "encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.h": ("078f5eef7cf2d24670361d6724ebb3497016ceff", "88fb8a8aec60c98e3b07f1002262c081cd3a3e2d"),
        "tests/ns2_gpu_identity_mapping_source.py": ("1c460d3c584914a600e660d141971b99be99f858", "59b47cf531c961906de13f29ee5b52b9d361dbc2"),
    }
    pair = known.get(relative)
    if pair is None:
        return actual
    assert actual == pair[0], ("NS2 normalized source drift", relative, actual)
    return pair[1]
# Source-only assertion correction: the first cursor variable declaration
# must not be mistaken for the second mapping stage. Check the one new blob
# and replay every previous source receipt without hiding other differences.
if selected == "29350dfa0049885d953ad206fd3ce2b163140cdb":
    relative = "tests/ns2_gpu_identity_mapping_source.py"
    raw = (V / relative).read_bytes()
    actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
    assert actual == ("1c460d3c584914a600e660d141971b99be99f858" if gitlink_vendor_pin == "bb6285e1998989101adbdc6adecbf9c1e1c17ec0" else
                      "59b47cf531c961906de13f29ee5b52b9d361dbc2"), ("NS2 mapping-kind host contract drift", actual)
    selected = "9eefc8f5131350e8ddfb11e617e2e25007925212"
# Real Switch 2 kind-change ioctl source contract. Verify all mutated
# vendor blobs, then replay earlier immutable source ownership receipts.
if selected == "9eefc8f5131350e8ddfb11e617e2e25007925212":
    for relative, expected in (
        ("encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.cpp", "f01d11f32d3f17847cb5c91a740eb070da67c118"),
        ("encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.h", "88fb8a8aec60c98e3b07f1002262c081cd3a3e2d"),
        ("tests/ns2_gpu_identity_mapping_source.py", "2b75cb68b569d9746f0c6726af23a78aca57b884"),
    ):
        raw = (V / relative).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        actual = archival_receipt_sha(relative, actual)
        assert actual == ("59b47cf531c961906de13f29ee5b52b9d361dbc2" if gitlink_vendor_pin in {"29350dfa0049885d953ad206fd3ce2b163140cdb", "bb6285e1998989101adbdc6adecbf9c1e1c17ec0"} and relative == "tests/ns2_gpu_identity_mapping_source.py" else expected), ("NS2 mapping-kind ioctl drift", relative, actual)
    selected = "997b4885c045469f09dedf2a5f4e69995a5b1c9a"
# Native NS2 big-page sparse-VA reservation successor. Only two blobs
# changed; pin them, then replay the complete preceding source graph.
if selected == "997b4885c045469f09dedf2a5f4e69995a5b1c9a":
    for relative, expected in (
        ("encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.cpp", "285ea0dda6807ab44f18277e8b5a5be734fb6b1f"),
        ("tests/ns2_gpu_identity_mapping_source.py", "bd5f668076d9b9b522ee407dad8d60760da2411b"),
    ):
        raw = (V / relative).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        actual = archival_receipt_sha(relative, actual)
        assert actual == ("f01d11f32d3f17847cb5c91a740eb070da67c118" if gitlink_vendor_pin in {"9eefc8f5131350e8ddfb11e617e2e25007925212", "29350dfa0049885d953ad206fd3ce2b163140cdb"} and relative == "encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.cpp" else
                          "88fb8a8aec60c98e3b07f1002262c081cd3a3e2d" if gitlink_vendor_pin in {"9eefc8f5131350e8ddfb11e617e2e25007925212", "29350dfa0049885d953ad206fd3ce2b163140cdb"} and relative == "encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.h" else
                          "59b47cf531c961906de13f29ee5b52b9d361dbc2" if gitlink_vendor_pin in {"29350dfa0049885d953ad206fd3ce2b163140cdb", "bb6285e1998989101adbdc6adecbf9c1e1c17ec0"} and relative == "tests/ns2_gpu_identity_mapping_source.py" else
                          "2b75cb68b569d9746f0c6726af23a78aca57b884" if gitlink_vendor_pin in {"9eefc8f5131350e8ddfb11e617e2e25007925212", "29350dfa0049885d953ad206fd3ce2b163140cdb"} and relative == "tests/ns2_gpu_identity_mapping_source.py" else expected), ("Native big-page sparse VA drift", relative, actual)
    selected = "0ec5337f26c31e6926bf327411634422c9043369"
# Native big-page ioctl remap ledger and focused source contract.
# Check only the new blobs before replaying strict predecessor receipts.
if selected == "0ec5337f26c31e6926bf327411634422c9043369":
    for relative, expected in (
        ("encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.cpp", "c1cdea91a84e7e9e1654a3b86c3be66d1c607393"),
        ("encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.h", "4d77c6f17c96086627df565acf6d78d2b799824c"),
        ("tests/ns2_gpu_identity_mapping_source.py", "7910960b9184efb76e6ebb323e04e08043fcb8c5"),
    ):
        raw = (V / relative).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        actual = archival_receipt_sha(relative, actual)
        assert actual == ("f01d11f32d3f17847cb5c91a740eb070da67c118" if gitlink_vendor_pin in {"9eefc8f5131350e8ddfb11e617e2e25007925212", "29350dfa0049885d953ad206fd3ce2b163140cdb"} and relative == "encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.cpp" else
                          "88fb8a8aec60c98e3b07f1002262c081cd3a3e2d" if gitlink_vendor_pin in {"9eefc8f5131350e8ddfb11e617e2e25007925212", "29350dfa0049885d953ad206fd3ce2b163140cdb"} and relative == "encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.h" else
                          "59b47cf531c961906de13f29ee5b52b9d361dbc2" if gitlink_vendor_pin in {"29350dfa0049885d953ad206fd3ce2b163140cdb", "bb6285e1998989101adbdc6adecbf9c1e1c17ec0"} and relative == "tests/ns2_gpu_identity_mapping_source.py" else
                          "2b75cb68b569d9746f0c6726af23a78aca57b884" if gitlink_vendor_pin in {"9eefc8f5131350e8ddfb11e617e2e25007925212", "29350dfa0049885d953ad206fd3ce2b163140cdb"} and relative == "tests/ns2_gpu_identity_mapping_source.py" else ("285ea0dda6807ab44f18277e8b5a5be734fb6b1f" if gitlink_vendor_pin == "997b4885c045469f09dedf2a5f4e69995a5b1c9a" and relative == "encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.cpp" else
                          "59b47cf531c961906de13f29ee5b52b9d361dbc2" if gitlink_vendor_pin in {"29350dfa0049885d953ad206fd3ce2b163140cdb", "bb6285e1998989101adbdc6adecbf9c1e1c17ec0"} and relative == "tests/ns2_gpu_identity_mapping_source.py" else
                          "2b75cb68b569d9746f0c6726af23a78aca57b884" if gitlink_vendor_pin in {"9eefc8f5131350e8ddfb11e617e2e25007925212", "29350dfa0049885d953ad206fd3ce2b163140cdb"} and relative == "tests/ns2_gpu_identity_mapping_source.py" else
                          "bd5f668076d9b9b522ee407dad8d60760da2411b" if gitlink_vendor_pin == "997b4885c045469f09dedf2a5f4e69995a5b1c9a" and relative == "tests/ns2_gpu_identity_mapping_source.py" else expected)), (
            "NS2 ioctl remap pin source drift", relative, actual)
    selected = "a9cca6aa9c63722b918b92362c237eed448ff56c"
# This successor contains only the reviewed NS2 transactional GPU AS
# mapping owner. The legacy Maxwell branch is unchanged. Verify exact blob
# before replaying all previous strict vendor source and provenance receipts.
if selected == "a9cca6aa9c63722b918b92362c237eed448ff56c":
    relative = "encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.cpp"
    raw = (V / relative).read_bytes()
    actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
    actual = archival_receipt_sha(relative, actual)
    assert actual == ("f01d11f32d3f17847cb5c91a740eb070da67c118" if gitlink_vendor_pin in {"9eefc8f5131350e8ddfb11e617e2e25007925212", "29350dfa0049885d953ad206fd3ce2b163140cdb"} else
                      "285ea0dda6807ab44f18277e8b5a5be734fb6b1f" if gitlink_vendor_pin == "997b4885c045469f09dedf2a5f4e69995a5b1c9a" else
                      "e252d390e5c08c933487ca351230636158bc1abe"), ("NS2 MapBufferEx transaction source drift", actual)
    selected = "21bc63493de105c1eb025f3ce5b67011deee72da"
# Shared native GPU VA source is corrected for FIFO fragmentation via Lichii
# #1896/#1911. Verify every changed blob (including C++ Catch2 cases) before
# replaying the earlier NS2 native ioctl/FC27 provenance. Shared NS1 source
# uses the same strictly nonoverlapping allocation invariant.
if selected == "21bc63493de105c1eb025f3ce5b67011deee72da":
    for relative, expected in (
        ("sources/eden/src/common/address_space.inc", "9722012ed1aa6eb243232c64f97cd293202e0694"),
        ("sources/eden/src/tests/CMakeLists.txt", "11115237edcfc91e1837659b9b7910d9d9b7857f"),
        ("tests/ns2_gpu_identity_mapping_source.py", "9091197c985c247aaee998319b64b5e637f2c799"),
        ("sources/eden/src/tests/common/flat_allocator.cpp", "ecf6f8fd66f4000fc9b76fd49522169c626da811"),
    ):
        raw = (V / relative).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        actual = archival_receipt_sha(relative, actual)
        assert actual == ("59b47cf531c961906de13f29ee5b52b9d361dbc2" if gitlink_vendor_pin in {"29350dfa0049885d953ad206fd3ce2b163140cdb", "bb6285e1998989101adbdc6adecbf9c1e1c17ec0"} and relative == "tests/ns2_gpu_identity_mapping_source.py" else
                          "2b75cb68b569d9746f0c6726af23a78aca57b884" if gitlink_vendor_pin in {"9eefc8f5131350e8ddfb11e617e2e25007925212", "29350dfa0049885d953ad206fd3ce2b163140cdb"} and relative == "tests/ns2_gpu_identity_mapping_source.py" else
                          "bd5f668076d9b9b522ee407dad8d60760da2411b" if gitlink_vendor_pin == "997b4885c045469f09dedf2a5f4e69995a5b1c9a" and relative == "tests/ns2_gpu_identity_mapping_source.py" else
                          "7910960b9184efb76e6ebb323e04e08043fcb8c5" if gitlink_vendor_pin == "0ec5337f26c31e6926bf327411634422c9043369" and relative == "tests/ns2_gpu_identity_mapping_source.py" else expected), (
            "GPU VA allocator upstream successor drift", relative, actual)
    selected = "b0afacfc891bc75da81be3886e5c40430ccbfe6d"
# Native NS2 controller: only a real GA10F process may query runlists and
# virtual SM topology. Verify both changed blobs before replaying all older
# immutable vendor/FC27 graph receipts without changing NS1 owners.
if selected == "b0afacfc891bc75da81be3886e5c40430ccbfe6d":
    for relative, expected in (
        ("encore-active/ns2-runtime/nvdrv/core/hle/service/nvdrv/devices/nvhost_ctrl_gpu.cpp", "2bd5023b5177cfd89d43fcc759643553fe0c745f"),
        ("tests/ns2_gpu_identity_mapping_source.py", "000cdd09038696e3291a30ac6f332c24b2adcecd"),
    ):
        raw = (V / relative).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        actual = archival_receipt_sha(relative, actual)
        assert actual == ("59b47cf531c961906de13f29ee5b52b9d361dbc2" if gitlink_vendor_pin in {"29350dfa0049885d953ad206fd3ce2b163140cdb", "bb6285e1998989101adbdc6adecbf9c1e1c17ec0"} and relative == "tests/ns2_gpu_identity_mapping_source.py" else
                          "2b75cb68b569d9746f0c6726af23a78aca57b884" if gitlink_vendor_pin in {"9eefc8f5131350e8ddfb11e617e2e25007925212", "29350dfa0049885d953ad206fd3ce2b163140cdb"} and relative == "tests/ns2_gpu_identity_mapping_source.py" else
                          "bd5f668076d9b9b522ee407dad8d60760da2411b" if gitlink_vendor_pin == "997b4885c045469f09dedf2a5f4e69995a5b1c9a" and relative == "tests/ns2_gpu_identity_mapping_source.py" else
                           "7910960b9184efb76e6ebb323e04e08043fcb8c5" if gitlink_vendor_pin == "0ec5337f26c31e6926bf327411634422c9043369" and
                           relative == "tests/ns2_gpu_identity_mapping_source.py" else
                           "9091197c985c247aaee998319b64b5e637f2c799" if gitlink_vendor_pin in {"21bc63493de105c1eb025f3ce5b67011deee72da", "a9cca6aa9c63722b918b92362c237eed448ff56c"} and
                           relative == "tests/ns2_gpu_identity_mapping_source.py" else expected), (
            "NS2 native NVDRV ABI isolation drift", relative, actual)
    selected = "eb62d96583999c5d159b837dfb9b1b02e8173a9c"
original_vendor_pin = selected
native_self_controller_rollback_revision = selected == "eb62d96583999c5d159b837dfb9b1b02e8173a9c"
native_va_region_widen_revision = selected in {"3a0cf78a9b2c98bed100d817537b4375a48bf72f", "eb62d96583999c5d159b837dfb9b1b02e8173a9c"}
native_rounded_unmap_revision = selected in {"e3ac953ea0fae3bdecb6850a65ec6ec57984aaeb", "3a0cf78a9b2c98bed100d817537b4375a48bf72f", "eb62d96583999c5d159b837dfb9b1b02e8173a9c"}
native_gpu_alias_guard_revision = selected in {"d4508480fc859cb7a6cb97f259caefe1cd18ba54", "e3ac953ea0fae3bdecb6850a65ec6ec57984aaeb", "3a0cf78a9b2c98bed100d817537b4375a48bf72f", "eb62d96583999c5d159b837dfb9b1b02e8173a9c"}
native_sparse_small_4k_revision = selected in {"5062767868c17b1ffe59fd6c5b6c2c4326b9a4bf", "d4508480fc859cb7a6cb97f259caefe1cd18ba54", "e3ac953ea0fae3bdecb6850a65ec6ec57984aaeb", "3a0cf78a9b2c98bed100d817537b4375a48bf72f", "eb62d96583999c5d159b837dfb9b1b02e8173a9c"}
native_video_pool_991_revision = selected in {"932dc1b3c09b172322d65432c26cc017b4922266", "5062767868c17b1ffe59fd6c5b6c2c4326b9a4bf", "d4508480fc859cb7a6cb97f259caefe1cd18ba54", "e3ac953ea0fae3bdecb6850a65ec6ec57984aaeb", "3a0cf78a9b2c98bed100d817537b4375a48bf72f", "eb62d96583999c5d159b837dfb9b1b02e8173a9c"}
native_preemption_wfi_revision = selected in {"258914fc564e223274728b409ee48e39465df7f6", "932dc1b3c09b172322d65432c26cc017b4922266", "5062767868c17b1ffe59fd6c5b6c2c4326b9a4bf", "d4508480fc859cb7a6cb97f259caefe1cd18ba54", "e3ac953ea0fae3bdecb6850a65ec6ec57984aaeb", "3a0cf78a9b2c98bed100d817537b4375a48bf72f", "eb62d96583999c5d159b837dfb9b1b02e8173a9c"}
# Preserve exact GSV source identity across historical receipt replays. The
# real 1402 child is NS2-only and can precede GPU session 497; both C++
# revisions fix the same compiled scoped-handle type.
native_worker_teardown_epoch = selected in {"99832a312b1281401c187f381f4826191387eb73", "258914fc564e223274728b409ee48e39465df7f6", "932dc1b3c09b172322d65432c26cc017b4922266", "5062767868c17b1ffe59fd6c5b6c2c4326b9a4bf", "d4508480fc859cb7a6cb97f259caefe1cd18ba54", "e3ac953ea0fae3bdecb6850a65ec6ec57984aaeb", "3a0cf78a9b2c98bed100d817537b4375a48bf72f", "eb62d96583999c5d159b837dfb9b1b02e8173a9c"}
native_gsv_registration = selected in {"b6e3ecc6943118ba9d321ef5baca9f79b241961f", "99832a312b1281401c187f381f4826191387eb73", "258914fc564e223274728b409ee48e39465df7f6", "932dc1b3c09b172322d65432c26cc017b4922266", "5062767868c17b1ffe59fd6c5b6c2c4326b9a4bf", "d4508480fc859cb7a6cb97f259caefe1cd18ba54", "e3ac953ea0fae3bdecb6850a65ec6ec57984aaeb", "3a0cf78a9b2c98bed100d817537b4375a48bf72f", "eb62d96583999c5d159b837dfb9b1b02e8173a9c"}
native_gsv_compiled_handle_fix = selected in {"f66969397724ab8467c3380ca9c6db1631f79bf3", "b6e3ecc6943118ba9d321ef5baca9f79b241961f", "99832a312b1281401c187f381f4826191387eb73", "258914fc564e223274728b409ee48e39465df7f6", "932dc1b3c09b172322d65432c26cc017b4922266", "5062767868c17b1ffe59fd6c5b6c2c4326b9a4bf", "d4508480fc859cb7a6cb97f259caefe1cd18ba54", "e3ac953ea0fae3bdecb6850a65ec6ec57984aaeb", "3a0cf78a9b2c98bed100d817537b4375a48bf72f", "eb62d96583999c5d159b837dfb9b1b02e8173a9c"}
native_gsv_active_cpp = "a806f2a6d2c9689a8b1e24f0c292a8d95c0d29a7" if native_video_pool_991_revision else "3bbc03df5ef568369667882e9394de6b1120cb03" if native_gsv_registration else "5aced8f423f654a3ed4648a711ee2fe4b95c118c"
native_gsv_active_test = "ae41e4bc89b33e455381f25470717af6766cd0b3" if native_video_pool_991_revision else "6d04679a771a3919434351b377fbc0f23ead4b82" if native_gsv_registration else "69723ef7bd1d47af5086052882d0749cc817f64a"
# Preserve the active AS/GMMU owner revision during recursive source-pin
# replay: the GA10F controller itself is unchanged but binds this new AS TU.
native_as_lease_revision = selected in {"2bf3a9a1dab0b8dc6b4157d9084ac66e5e2e547f", "889b142aa5616d3d00733a7cc1db1562eed291f4"}
native_as_session_revision = selected == "889b142aa5616d3d00733a7cc1db1562eed291f4"
ns2_gsv_497_v2 = selected in {"a7b9008340ccf03e4f63c180d820631858fe935e", "565f143c27443553b60ca1b21cc1094caa23ceb5"}
ns2_gsv_497_dual = selected in {"010d5c61cefd62cbb5d27102cd9a2350fa0e69ce", "3460d10e60bff7dd8b057f592eb671cc35eddd25", "6f6f7f4cb154aa227eaf4d54330ff9d817b77ecb", "ce27bdd184c60d1f096ef1495c0ef7e5b7f0cdf0", "01c942171fea39c1f7cf31d13ab36895aebb593a", "dcf7116dd2c536e05c80d83ff9dbf30caa5cc109", "b65d8d9673475433f0b6eac72eb304bf23141666"}
# NS2 native 4-KiB sparse VA is an additive change to the exact
# selected NVDRV AS TU and its focused source test. Every older receipt
# remains strict for every other file and every older vendor revision.
def reviewed_blob(relative, expected):
    if gitlink_vendor_pin == "bb6285e1998989101adbdc6adecbf9c1e1c17ec0":
        exact = {
            "encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.cpp": "e120fcee7c85ad7a874c8ffc10f2b3804b707199",
            "encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.h": "078f5eef7cf2d24670361d6724ebb3497016ceff",
            "tests/ns2_gpu_identity_mapping_source.py": "1c460d3c584914a600e660d141971b99be99f858",
        }
        if relative in exact:
            return exact[relative]
    if gitlink_vendor_pin in {"29350dfa0049885d953ad206fd3ce2b163140cdb", "bb6285e1998989101adbdc6adecbf9c1e1c17ec0"} and relative == "tests/ns2_gpu_identity_mapping_source.py":
        return "59b47cf531c961906de13f29ee5b52b9d361dbc2"
    if gitlink_vendor_pin in {"9eefc8f5131350e8ddfb11e617e2e25007925212", "29350dfa0049885d953ad206fd3ce2b163140cdb"}:
        if relative == "encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.cpp": return "f01d11f32d3f17847cb5c91a740eb070da67c118"
        if relative == "encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.h": return "88fb8a8aec60c98e3b07f1002262c081cd3a3e2d"
        if relative == "tests/ns2_gpu_identity_mapping_source.py": return "2b75cb68b569d9746f0c6726af23a78aca57b884"
    if gitlink_vendor_pin == "997b4885c045469f09dedf2a5f4e69995a5b1c9a":
        if relative == "encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.cpp":
            return "285ea0dda6807ab44f18277e8b5a5be734fb6b1f"
        if relative == "tests/ns2_gpu_identity_mapping_source.py":
            return "bd5f668076d9b9b522ee407dad8d60760da2411b"
    if gitlink_vendor_pin == "0ec5337f26c31e6926bf327411634422c9043369":
        reviewed = {
            "encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.cpp": "c1cdea91a84e7e9e1654a3b86c3be66d1c607393",
            "encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.h": "4d77c6f17c96086627df565acf6d78d2b799824c",
            "tests/ns2_gpu_identity_mapping_source.py": "7910960b9184efb76e6ebb323e04e08043fcb8c5",
        }
        if relative in reviewed:
            return reviewed[relative]
    if gitlink_vendor_pin == "a9cca6aa9c63722b918b92362c237eed448ff56c" and relative == "encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.cpp":
        return "e252d390e5c08c933487ca351230636158bc1abe"
    if gitlink_vendor_pin in {"21bc63493de105c1eb025f3ce5b67011deee72da", "a9cca6aa9c63722b918b92362c237eed448ff56c", "0ec5337f26c31e6926bf327411634422c9043369", "997b4885c045469f09dedf2a5f4e69995a5b1c9a", "9eefc8f5131350e8ddfb11e617e2e25007925212", "29350dfa0049885d953ad206fd3ce2b163140cdb", "bb6285e1998989101adbdc6adecbf9c1e1c17ec0"}:
        if relative == "encore-active/ns2-runtime/nvdrv/core/hle/service/nvdrv/devices/nvhost_ctrl_gpu.cpp":
            return "2bd5023b5177cfd89d43fcc759643553fe0c745f"
        if relative == "tests/ns2_gpu_identity_mapping_source.py":
            return "9091197c985c247aaee998319b64b5e637f2c799"
    # The current vendor successor changes exactly two already sealed files:
    # native NVDRV ioctl3 topology ABI and its focused static host contract.
    # Historical receipts compare against the selected successor rather
    # than incorrectly expecting byte-identical predecessor blobs.
    if gitlink_vendor_pin == "b0afacfc891bc75da81be3886e5c40430ccbfe6d":
        if relative == "encore-active/ns2-runtime/nvdrv/core/hle/service/nvdrv/devices/nvhost_ctrl_gpu.cpp":
            return "2bd5023b5177cfd89d43fcc759643553fe0c745f"
        if relative == "tests/ns2_gpu_identity_mapping_source.py":
            return "000cdd09038696e3291a30ac6f332c24b2adcecd"
    if native_va_region_widen_revision:
        if relative == "encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.cpp":
            return "e7832741b238f4c25858f8309d8ccf9aed7a77d3"
        if relative == "tests/ns2_gpu_identity_mapping_source.py":
            return "678dc58f5efc8c72a1ebad1632d5c276fd983faa"
    if native_rounded_unmap_revision:
        if relative == "encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.cpp":
            return "d9a041b6d0f203e54942632943337f9e92eea6be"
        if relative == "tests/ns2_gpu_identity_mapping_source.py":
            return "ea8899dc76834e8c83eb6527187c32661c5fedfd"
    if native_gpu_alias_guard_revision:
        if relative == "encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.cpp":
            return "1b99bac6d3a7831833fa1471523c6714f08c4496"
        if relative == "tests/ns2_gpu_identity_mapping_source.py":
            return "bddae3ce26cc694c10c93491c28b6a9f47007b01"
    if native_sparse_small_4k_revision:
        if relative == "encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.cpp":
            return "35bef222790b19521059aa6dd2c1acef198ff625"
        if relative == "tests/ns2_gpu_identity_mapping_source.py":
            return "90b1d4e0fec9379c99c717eac54e3fdc0fb9cc54"
    return expected

checked=subprocess.check_output(["git","-C",str(V),"rev-parse","HEAD"],text=True).strip()
assert gitlink_vendor_pin==checked and selected in REVIEWED_PINS,(gitlink_vendor_pin,selected,checked)
# GPU 497 must remain authenticated while its final native AS FDs and
# NvCore session are closed; then revoke its process epoch once. Keep the
# exact new real owner/test blobs and replay the complete earlier reviewed
# source graph for all unaffected units.
# Match Allocate()'s rounded page span at NS2 dynamic UnmapBuffer,
# preserving the existing Maxwell path and all previous exact receipts.
# NS2 NVDRV returns 64-bit byte offsets, not truncated 32-bit shifts.
# Requalify the exact two changed blobs before replaying unmap and aliases.
# NS2 SelfController cmd2000 now reserves and rolls back the real GSV
# kernel session exactly as the existing GPU 497 child creation does. Seal
# only these two changed blobs; all older vendor owner receipts still apply.
if native_self_controller_rollback_revision:
    for relative, expected in (
        ("encore-active/ns2-runtime/self_controller/core/hle/service/am/service/self_controller.cpp",
         "45e02dc11f49bf66b736b31786931de5b20ce9cd"),
        ("tests/r23_fw23_selfcontroller_240.py",
         "1f92b520eeb1700cd84f25aa88694955bc9541cf"),
    ):
        raw = (V / relative).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        assert actual == expected, ("NS2 GSV parent session rollback source drift", relative, actual)
    selected = "3a0cf78a9b2c98bed100d817537b4375a48bf72f"
    original_vendor_pin = selected

if native_va_region_widen_revision:
    for relative, expected in (
        ("encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.cpp", "e7832741b238f4c25858f8309d8ccf9aed7a77d3"),
        ("tests/ns2_gpu_identity_mapping_source.py", "678dc58f5efc8c72a1ebad1632d5c276fd983faa"),
    ):
        raw = (V / relative).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        assert actual == reviewed_blob(relative, expected), (
            "NS2 64-bit GPU VA region source drift", relative, actual)
    selected = "e3ac953ea0fae3bdecb6850a65ec6ec57984aaeb"
    original_vendor_pin = selected

if native_rounded_unmap_revision:
    for relative, expected in (
        ("encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.cpp",
         "d9a041b6d0f203e54942632943337f9e92eea6be"),
        ("tests/ns2_gpu_identity_mapping_source.py",
         "ea8899dc76834e8c83eb6527187c32661c5fedfd"),
    ):
        raw = (V / relative).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        assert actual == reviewed_blob(relative, expected), (
            "NS2 dynamic GPU VA unmap rounding source drift", relative, actual)
    selected = "d4508480fc859cb7a6cb97f259caefe1cd18ba54"
    original_vendor_pin = selected

# Native NS2 fixed GPU mappings cannot overwrite a live mapping or
# accept a foreign NVMap owner; stale unmap tokens cannot dereference a
# freed mapping. Seal the two changed blobs before replaying the 4K gate.
if native_gpu_alias_guard_revision:
    for relative, expected in (
        ("encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.cpp",
         "1b99bac6d3a7831833fa1471523c6714f08c4496"),
        ("tests/ns2_gpu_identity_mapping_source.py",
         "bddae3ce26cc694c10c93491c28b6a9f47007b01"),
    ):
        raw = (V / relative).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        assert actual == reviewed_blob(relative, expected), (
            "NS2 fixed GPU alias/stale-unmap owner drift", relative, actual)
    selected = "5062767868c17b1ffe59fd6c5b6c2c4326b9a4bf"
    original_vendor_pin = selected

# Verify the new native sparse VA owner/test, then replay the unchanged
# GSV, WFI, GA10F, memory lifetime and FC27 source contracts below.
if native_sparse_small_4k_revision:
    for relative, expected in (
        ("encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.cpp",
         "35bef222790b19521059aa6dd2c1acef198ff625"),
        ("tests/ns2_gpu_identity_mapping_source.py",
         "90b1d4e0fec9379c99c717eac54e3fdc0fb9cc54"),
    ):
        raw = (V / relative).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        assert actual == reviewed_blob(relative, expected), ("NS2 native 4K sparse VA source drift", relative, actual)
    selected = "932dc1b3c09b172322d65432c26cc017b4922266"
    original_vendor_pin = selected

# Real native GSV 991 decoder backing and corrected NVGPU WFI bit0.
# Validate exactly the five changed blobs; all earlier source receipts
# remain active for unchanged files, including FC27 and NS1 owners.
if native_video_pool_991_revision:
    for relative, expected in (
        ("encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/nvhost_gpu.cpp", "941873af1123ef764a35e9712ce054e5a1c90b53"),
        ("encore-active/ns2-runtime/graphics_supervisor/core/hle/service/am/service/graphics_supervisor.cpp", "a806f2a6d2c9689a8b1e24f0c292a8d95c0d29a7"),
        ("encore-active/ns2-runtime/graphics_supervisor/core/hle/service/am/service/graphics_supervisor.h", "4ae0674d5ed96a363f66df7eb788fa42f6bbd8e3"),
        ("tests/ns2_syncpt_bootstrap_source.py", "ae41e4bc89b33e455381f25470717af6766cd0b3"),
        ("tests/ns2_gpu_identity_mapping_source.py", "bd0ad8fd91cf67c57936ed65df2c29b55f839250"),
    ):
        raw = (V / relative).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        assert actual == reviewed_blob(relative, expected), ("NS2 native GSV991/WFI selected source drift", relative, actual)
    selected = "258914fc564e223274728b409ee48e39465df7f6"
    original_vendor_pin = selected

# Switch 2 H:0x1F is 0xC008481F (preemption). Only WFI/WFI is
# implemented by Encore's existing software GPU scheduler. Seal the
# exact new NVDRV owner and focused regression, then replay all prior
# receipts; every unrelated C++ file must retain its historical SHA.
if native_preemption_wfi_revision:
    for relative, expected in (
        ("encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/nvhost_gpu.cpp",
         "941873af1123ef764a35e9712ce054e5a1c90b53" if native_video_pool_991_revision else
         "f1fcf207091c51daca138341f275c700334a57aa"),
        ("tests/ns2_gpu_identity_mapping_source.py",
         "bd0ad8fd91cf67c57936ed65df2c29b55f839250" if native_video_pool_991_revision else
         "e03f39df1b9efceb398d0e34ebf60a5bf67211c3"),
    ):
        raw = (V / relative).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        assert actual == reviewed_blob(relative, expected), ("NS2 channel preemption WFI owner drift", relative, actual)
    selected = "99832a312b1281401c187f381f4826191387eb73"
    original_vendor_pin = selected
if selected == "99832a312b1281401c187f381f4826191387eb73":
    for relative, expected in (
        ("encore-active/ns2-runtime/gpu_session/core/hle/service/am/service/gpu_worker_shared.cpp", "b613ba93b07003570f206d66ace34d7a488e603d"),
        ("tests/ns2_gpu_identity_mapping_source.py",
         "bd0ad8fd91cf67c57936ed65df2c29b55f839250" if native_video_pool_991_revision else
         "e03f39df1b9efceb398d0e34ebf60a5bf67211c3" if native_preemption_wfi_revision else
         "8deadd56ec6f12ae2f1da491337d694631f8e19f"),
    ):
        raw = (V / relative).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        assert actual == reviewed_blob(relative, expected), ("NS2 GPU 497 teardown process-ticket lifetime drift", relative, actual)
    selected = "b6e3ecc6943118ba9d321ef5baca9f79b241961f"
    original_vendor_pin = selected
# GSV's KScopedAutoObject is a mutable scoped handle: its only operator->
# is non-const. Fix the *compiled* GSV1/1401/496 C++ locals without altering
# TIPC buffer admission, GPU identity or any NS1 source. Replay the exact
# prior complete source receipt after validating the one changed TU.
if selected in {"f66969397724ab8467c3380ca9c6db1631f79bf3", "b6e3ecc6943118ba9d321ef5baca9f79b241961f"}:
    relative = "encore-active/ns2-runtime/graphics_supervisor/core/hle/service/am/service/graphics_supervisor.cpp"
    raw = (V / relative).read_bytes()
    actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
    assert actual == native_gsv_active_cpp, ("NS2 native GSV compiled source drift", actual)
    if native_gsv_registration:
        for relative, expected in (
            ("tests/ns2_syncpt_bootstrap_source.py", native_gsv_active_test),
            ("encore-active/ns2-runtime/hle/core/hle/service/nvdrv/devices/native_gpu_process_registry.h", "09cb1ca6494b6d6866239eba0bb45801a237536c"),
            ("encore-active/ns2-runtime/gpu_session/core/hle/service/am/service/gpu_worker_shared.cpp",
             "b613ba93b07003570f206d66ace34d7a488e603d" if native_worker_teardown_epoch else
             "34142613b8ee0389509406da540811ba35eae9d6"),
            ("sources/eden/src/core/hle/service/nvdrv/nvdrv_interface.cpp", "a47b4a447c74e2710678c4e881b6b2f949a373cf"),
            ("sources/eden/src/core/hle/service/nvdrv/nvdrv_interface.h", "b32fe29a11b0ffee941eb32043043553e67a28b5"),
        ):
            raw = (V / relative).read_bytes()
            actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
            assert actual == reviewed_blob(relative, expected), ("Native GSV 1402/497 process ticket source drift", relative, actual)
    selected = "35d639ad802910cfabbaf46bdcfd48a0d2f09ab6"
    original_vendor_pin = selected

# NS2 native channel retirement is now a *GPU-worker* operation.
# This seal includes the pre-existing GA10F, NVCore session and AS owners
# plus the exact scheduler, GPU, NVDRV and source regression changed here.
# Host/non-PS5 GPU::ReleaseChannel retains its legacy implementation.
if selected in {"201b09121ebbfe0a37a56710b2b7ac118ae5acbb", "713e18162cf9a0d629cd39ae00b43fb55f9c2823", "35d639ad802910cfabbaf46bdcfd48a0d2f09ab6"}:
    worker_shutdown_guard = selected == "35d639ad802910cfabbaf46bdcfd48a0d2f09ab6"
    process_scoped_lease = selected in {"713e18162cf9a0d629cd39ae00b43fb55f9c2823", "35d639ad802910cfabbaf46bdcfd48a0d2f09ab6"}
    for relative, expected in (
        ("encore-active/ns2-runtime/gpu_dispatch/video_core/control/scheduler.h", "fe45aa0e8e9943034cbf61e620ee132d33adf887"),
        ("encore-active/ns2-runtime/gpu_dispatch/video_core/control/scheduler.cpp", "e74f82cd604ba8e60bc7b1005f60a92d66013563"),
        ("encore-active/eden-core/src/video_core/gpu_vulkan.cpp", "fc921425b67b634b4aaeb2363dcabdf9b53b6be8"),
        ("encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/nvhost_gpu.cpp",
         "941873af1123ef764a35e9712ce054e5a1c90b53" if native_video_pool_991_revision else
         "f1fcf207091c51daca138341f275c700334a57aa" if native_preemption_wfi_revision else
         "c0cc9b26f6af13d6e1a3b60d92a0dfabd93c51d1"),
        ("tests/ns2_gpu_identity_mapping_source.py",
         "bd0ad8fd91cf67c57936ed65df2c29b55f839250" if native_video_pool_991_revision else
         "e03f39df1b9efceb398d0e34ebf60a5bf67211c3" if native_preemption_wfi_revision else
         "8deadd56ec6f12ae2f1da491337d694631f8e19f" if native_worker_teardown_epoch else
         "d9ac33e7d4f83e7198b23f6ab48a0f57bf76a8c5" if worker_shutdown_guard else
         "fa8389fe2513f09133c5cdb14d662e65e83c79d4" if process_scoped_lease else
         "027fee436eea6292e59caa852d76282473d41688"),
        ("encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/native_gpu_channel_registry.h", "8ca13a81c05c272347f7dfd0f8189b5c2b2fd946"),
        ("encore-active/ns2-runtime/nvdrv/core/hle/service/nvdrv/devices/native_gpu_characteristics.h", "ba96b6a240b31519afc89a15e7d683d0c2f32f32"),
        ("encore-active/ns2-runtime/nvdrv/core/hle/service/nvdrv/devices/nvhost_ctrl_gpu.cpp", "8c90a441fc50e656be3d39c582e85241aabcfb75"),
        ("sources/eden/src/video_core/control/channel_state.h", "dfbb776d9b03f68439efa33f02806a15782c2e21"),
        ("sources/eden/src/core/hle/service/nvdrv/core/container.h", "14f84ba43cb83451d8b8dc5fc707e894f43ac2c7"),
        ("encore-active/eden-core/src/core/hle/service/nvdrv/core/container.cpp", "eec4677538f53cd709f8f6bee9975f3cba0426a0"),
        ("encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.h", "f2ed8c5407974f131fceb6f43a9597334d641477"),
        ("encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.cpp",
         "0c32fa40c796706ea4687e8d6e8fa34bc6e7c036" if process_scoped_lease else
         "9c4f369d4909a49c69ca58a10d3b141b29214ed7"),
        ("encore-active/ns2-runtime/process/core/core.cpp", "a30c7bbe1bf719b196f1f0805e83b1276ee74472"),
        ("sources/eden/src/core/hle/service/nvdrv/nvdrv.cpp", "ee1eab4c6417bdeda24de75e36f86fe68d9802b2"),
        ("tests/shutdown_teardown_lifetime_source.py", "f96f8a58681fd13e46b1a54a49f1ce5f9cdbf3dd"),
        ("tests/shutdown_general_channel_lifetime_source.py", "d18a8646f71b7285425397b74bf51853de4e4684"),
    ):
        raw = (V / relative).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        assert actual == reviewed_blob(relative, expected), ("Native channel retirement/AS session source drift", relative, actual)
    if worker_shutdown_guard:
        relative = "encore-active/ns2-runtime/gpu_session/core/hle/service/am/service/gpu_worker.cpp"
        raw = (V / relative).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        assert actual == "5ff69e424b4b77d16732df37dbb5ecd56f3d4964", ("GPU worker shutdown-guard drift", relative, actual)
    selected = "4795f0a884c06f029c9d06a0a3d09cc0b9cfb791"
    original_vendor_pin = selected
# A GPU channel's AS shared_ptr owns the GMMU but cannot keep NVMap
# backing mapped after its final NvCore session is closed. The PS5-selected
# Container retains the exact live session; the channel's last owner
# releases it only after unpinning its mapped memory.
if selected == "889b142aa5616d3d00733a7cc1db1562eed291f4":
    for relative, expected in (
        ("sources/eden/src/core/hle/service/nvdrv/core/container.h", "14f84ba43cb83451d8b8dc5fc707e894f43ac2c7"),
        ("encore-active/eden-core/src/core/hle/service/nvdrv/core/container.cpp", "eec4677538f53cd709f8f6bee9975f3cba0426a0"),
        ("encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.h", "f2ed8c5407974f131fceb6f43a9597334d641477"),
        ("encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.cpp", "9c4f369d4909a49c69ca58a10d3b141b29214ed7"),
        ("tests/ns2_gpu_identity_mapping_source.py", "adaddc673e3a36de3e3ff5079871595f21226195"),
        ("sources/eden/src/video_core/control/channel_state.h", "dfbb776d9b03f68439efa33f02806a15782c2e21"),
        ("encore-active/ns2-runtime/process/core/core.cpp", "a30c7bbe1bf719b196f1f0805e83b1276ee74472"),
        ("encore-active/eden-core/src/video_core/gpu_vulkan.cpp", "842a0289f75bc2a0763285173e4616060348ec22"),
        ("encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/nvhost_gpu.cpp", "245942ef561b727546a0897658ce73f04f3ae269"),
    ):
        raw = (V / relative).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        assert actual == reviewed_blob(relative, expected), ("Native session/GMMU channel ownership drift", relative, actual)
    selected = "bb575bd8396d78187d2bd56713e84c398ebce512"
    original_vendor_pin = selected
# A GPU channel (including queued work in the scheduler) must retain
# its actual GMMU address-space owner after NVDRV closes the AS FD.
# The PS5 teardown order of the prior reviewed pin is unchanged; seal
# the complete changed channel/AS/test group and the unchanged GPU graph.
if selected == "2bf3a9a1dab0b8dc6b4157d9084ac66e5e2e547f":
    for relative, expected in (
        ("sources/eden/src/video_core/control/channel_state.h", "dfbb776d9b03f68439efa33f02806a15782c2e21"),
        ("encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.h", "0fc63bab41e86982a5d2cbeba1b2ebd7675c608a"),
        ("encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.cpp", "dda472d0cf7277f870540758243d242ee7fe80eb"),
        ("tests/ns2_gpu_identity_mapping_source.py", "f7f4dcc1c562171a7fe37a7b1a42ef07ab42177e"),
        ("encore-active/ns2-runtime/process/core/core.cpp", "a30c7bbe1bf719b196f1f0805e83b1276ee74472"),
        ("tests/shutdown_teardown_lifetime_source.py", "f96f8a58681fd13e46b1a54a49f1ce5f9cdbf3dd"),
        ("tests/shutdown_general_channel_lifetime_source.py", "d18a8646f71b7285425397b74bf51853de4e4684"),
        ("encore-active/eden-core/src/video_core/gpu_vulkan.cpp", "842a0289f75bc2a0763285173e4616060348ec22"),
        ("encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/nvhost_gpu.cpp", "245942ef561b727546a0897658ce73f04f3ae269"),
    ):
        raw = (V / relative).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        assert actual == reviewed_blob(relative, expected), ("Native AS/GMMU channel-lifetime drift", relative, actual)
    selected = "bb575bd8396d78187d2bd56713e84c398ebce512"
    original_vendor_pin = selected
# NS2 runtime exit: retire the actual PS5 Vulkan worker/renderer before
# kernel.CloseServices can drop NVDRV's pinned NvMap/GMMU address spaces.
# Preserve existing historical kernel/cheat-teardown receipts by checking
# the actual core and only the two updated in-place provenance tests.
if selected == "9bd8de9081cc5ad431ecfc62696e9a6f8f2d1ffc":
    for relative, expected in (
        ("encore-active/ns2-runtime/process/core/core.cpp", "a30c7bbe1bf719b196f1f0805e83b1276ee74472"),
        ("tests/shutdown_teardown_lifetime_source.py", "f96f8a58681fd13e46b1a54a49f1ce5f9cdbf3dd"),
        ("tests/shutdown_general_channel_lifetime_source.py", "d18a8646f71b7285425397b74bf51853de4e4684"),
        ("encore-active/eden-core/src/video_core/gpu_vulkan.cpp", "842a0289f75bc2a0763285173e4616060348ec22"),
        ("encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.cpp", "ca0574dc36e56ad727c63552231872002465bc99"),
        ("encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/nvhost_gpu.cpp", "245942ef561b727546a0897658ce73f04f3ae269"),
    ):
        raw = (V / relative).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        assert actual == reviewed_blob(relative, expected), ("Native GPU worker/AS teardown owner drift", relative, actual)
    selected = "bb575bd8396d78187d2bd56713e84c398ebce512"
    original_vendor_pin = selected
# The PS5/native control reply retains the original host C++ constructor
# and TPC mask member signatures. Seal both native owners and the unchanged
# common/AS/GPU parents before accepting this ABI compatibility revision.
if selected in {"788badb79f0566c56f51e64fb9aa727f72fdb065", "0015d90da841622e1642180b9f9de5e2d0c354c9", "bb575bd8396d78187d2bd56713e84c398ebce512"}:
    for relative, expected in (
        ("encore-active/ns2-runtime/nvdrv/core/hle/service/nvdrv/devices/native_gpu_characteristics.h", "ba96b6a240b31519afc89a15e7d683d0c2f32f32"),
        ("encore-active/ns2-runtime/nvdrv/core/hle/service/nvdrv/devices/nvhost_ctrl_gpu.cpp",
         ("8c90a441fc50e656be3d39c582e85241aabcfb75" if selected == "bb575bd8396d78187d2bd56713e84c398ebce512" else
          "cfea80650d97206ad2a9c8b9ef968366ba844285" if selected == "0015d90da841622e1642180b9f9de5e2d0c354c9" else
          "384457a096e6f460915436a2bd6a873fd7f6efb9")),
        ("sources/eden/src/core/hle/service/nvdrv/devices/nvhost_ctrl_gpu.h", "eaccce6e08fc9fbe2b19ad621682e638fb019ba4"),
        ("sources/eden/src/core/hle/service/nvdrv/nvdrv.cpp", "ee1eab4c6417bdeda24de75e36f86fe68d9802b2"),
        ("sources/eden/src/core/hle/service/nvdrv/devices/nvdevice.h", "1db3172a604b9aed2c64765a84786d675029f6eb"),
        ("encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/nvhost_gpu.h", "50ff41f87e154b4b534792efe679d721d741eec4"),
        ("encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/nvhost_gpu.cpp", "245942ef561b727546a0897658ce73f04f3ae269"),
        ("encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.cpp",
         "9c4f369d4909a49c69ca58a10d3b141b29214ed7" if native_as_session_revision else
         "dda472d0cf7277f870540758243d242ee7fe80eb" if native_as_lease_revision else
         "ca0574dc36e56ad727c63552231872002465bc99"),
        ("sources/eden/src/core/hle/service/nvdrv/devices/nx2_stub_device.h", "26798a34076b12d8f3cd32ede81851757f6bb121"),
    ):
        raw = (V / relative).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        assert actual == reviewed_blob(relative, expected), ("Native/legacy NVDRV controller ABI drift", relative, actual)
    selected = "4795f0a884c06f029c9d06a0a3d09cc0b9cfb791"
    original_vendor_pin = selected
# Native GA10F topology is coherent only if characteristics, TPC mask,
# VSMS_MAPPING and the per-FD controller constructor all compile together.
# Verify their exact blobs plus the unchanged FD/TSG/AS owner group before
# replaying the original FC27/P0 receipts. NS1 stays on Maxwell (2 TPC).
if selected == "de4a6c24d1f118152c849fc87af2783c96348735":
    for relative, expected in (
        ("encore-active/ns2-runtime/nvdrv/core/hle/service/nvdrv/devices/native_gpu_characteristics.h", "ba96b6a240b31519afc89a15e7d683d0c2f32f32"),
        ("encore-active/ns2-runtime/nvdrv/core/hle/service/nvdrv/devices/nvhost_ctrl_gpu.cpp", "77bcb4907302119e95589b52162ab67ec87c6ac3"),
        ("sources/eden/src/core/hle/service/nvdrv/devices/nvhost_ctrl_gpu.h", "155bea31994af11ac09e39f5e64033e1868235a6"),
        ("sources/eden/src/core/hle/service/nvdrv/nvdrv.cpp", "fe60e19fb76eeb3df8921b741290b3dbc18354c6"),
        ("sources/eden/src/core/hle/service/nvdrv/devices/nvdevice.h", "1db3172a604b9aed2c64765a84786d675029f6eb"),
        ("encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/nvhost_gpu.h", "50ff41f87e154b4b534792efe679d721d741eec4"),
        ("encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/nvhost_gpu.cpp", "245942ef561b727546a0897658ce73f04f3ae269"),
        ("encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.cpp", "ca0574dc36e56ad727c63552231872002465bc99"),
        ("sources/eden/src/core/hle/service/nvdrv/devices/nx2_stub_device.h", "26798a34076b12d8f3cd32ede81851757f6bb121"),
    ):
        raw = (V / relative).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        assert actual == reviewed_blob(relative, expected), ("Native GA10F topology/FD owner drift", relative, actual)
    selected = "4795f0a884c06f029c9d06a0a3d09cc0b9cfb791"
    original_vendor_pin = selected
# The AS BindChannel owner previously performed an unchecked nvhost_gpu
# downcast after verifying only that the FD existed. Seal the real C++ owners
# for the device-family check and leave every other runtime blob unchanged.
if selected in {"e95c1dea796b209b8561c253b82fa69e75fb72b6", "019e810c5c6c489eab8541f282de6b6379833015"}:
    for relative, expected in (
        ("sources/eden/src/core/hle/service/nvdrv/devices/nvdevice.h", "1db3172a604b9aed2c64765a84786d675029f6eb"),
        ("encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/nvhost_gpu.h", "50ff41f87e154b4b534792efe679d721d741eec4"),
        ("encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.cpp",
         ("ca0574dc36e56ad727c63552231872002465bc99" if selected == "019e810c5c6c489eab8541f282de6b6379833015" else
          "99133d3000fb0c3b43a0a653221c1453072fd6dd")),
        ("encore-active/ns2-runtime/nvdrv/core/hle/service/nvdrv/devices/nvhost_ctrl_gpu.cpp", "6d59efa437c5415267e5db0a2c86174d785fb2c2"),
        ("encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/nvhost_gpu.cpp", "245942ef561b727546a0897658ce73f04f3ae269"),
        ("sources/eden/src/core/hle/service/nvdrv/devices/nx2_stub_device.h", "26798a34076b12d8f3cd32ede81851757f6bb121"),
        ("sources/eden/src/core/hle/service/nvdrv/nvdrv.cpp", "6d72ba1851e21227ad196bbdd7db5226f77c9500"),
    ):
        raw = (V / relative).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        assert actual == reviewed_blob(relative, expected), ("Native channel FD type-check owner drift", relative, actual)
    selected = "4795f0a884c06f029c9d06a0a3d09cc0b9cfb791"
    original_vendor_pin = selected
# Native NS2 GPU controller and channel handlers: match all reviewed
# C++ owners before replaying the previous TSG/FC27 provenance receipts.
# The new GET_ENGINE_INFO is read-only; CHANNEL_OPEN authenticates the
# actual process and records an advertised runlist on its live ChannelState.
if selected == "a93bc45a1a5858fe1e4bc718a84a2a5a8841ab38":
    for relative, expected in (
        ("encore-active/ns2-runtime/nvdrv/core/hle/service/nvdrv/devices/nvhost_ctrl_gpu.cpp", "6d59efa437c5415267e5db0a2c86174d785fb2c2"),
        ("encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/nvhost_gpu.cpp", "245942ef561b727546a0897658ce73f04f3ae269"),
        ("encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/nvhost_gpu.h", "7d486218f7d1667ed9e38ab75d4c1421fa09c814"),
        # The other three TSG predecessors are unchanged and must still be sealed
        # because skipping the earlier full receipt also skips their old checks.
        ("sources/eden/src/core/hle/service/nvdrv/devices/nvdevice.h", "5a3ce8871ff52ed917969e2935f6837f5f1537ad"),
        ("sources/eden/src/core/hle/service/nvdrv/devices/nx2_stub_device.h", "26798a34076b12d8f3cd32ede81851757f6bb121"),
        ("sources/eden/src/core/hle/service/nvdrv/nvdrv.cpp", "6d72ba1851e21227ad196bbdd7db5226f77c9500"),
    ):
        raw = (V / relative).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        assert actual == reviewed_blob(relative, expected), ("Native GPU runlist owner drift", relative, actual)
    selected = "4795f0a884c06f029c9d06a0a3d09cc0b9cfb791"
    original_vendor_pin = selected
# NS2 native VSMS mapping: one selected Ampere controller source changed.
# Validate its exact compiled blob, then replay the unchanged TSG/FC27 receipts.
if selected == "86cbe7ac73a28dcd1e3cdc3609eafca1c7b5dc37":
    relative = "encore-active/ns2-runtime/nvdrv/core/hle/service/nvdrv/devices/nvhost_ctrl_gpu.cpp"
    raw = (V / relative).read_bytes()
    actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
    assert actual == reviewed_blob(relative, "3124fe780213da7a62251829fb24bf30f1582b1a"), ("Native VSMS GPU controller drift", actual)
    selected = "fcd2e6e38bbfd01ab78f56fe8ba5d8039d120531"
    original_vendor_pin = selected
# The revised native TSG driver adds process-checked bind/unbind ioctl
# semantics and no longer acknowledges unimplemented TSG commands.
# All five live source blobs must exactly match the reviewed vendor commit.
# Replay previous FC27/NS2 receipts only after proving that the other
# compiled owners did not change.
if selected == "fcd2e6e38bbfd01ab78f56fe8ba5d8039d120531":
    for relative, expected in (
        ("sources/eden/src/core/hle/service/nvdrv/devices/nvdevice.h", "5a3ce8871ff52ed917969e2935f6837f5f1537ad"),
        ("sources/eden/src/core/hle/service/nvdrv/devices/nx2_stub_device.h", "26798a34076b12d8f3cd32ede81851757f6bb121"),
        ("sources/eden/src/core/hle/service/nvdrv/nvdrv.cpp", "6d72ba1851e21227ad196bbdd7db5226f77c9500"),
        ("encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/nvhost_gpu.h", "a899fd5fabffef8e98b030381d8d894356c67a80"),
        ("encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/nvhost_gpu.cpp", "10fc74076686e0c9c27c7c74b6363ecec9361d7b"),
    ):
        raw = (V / relative).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        assert actual == reviewed_blob(relative, expected), ("Native TSG GPU owner drift", relative, actual)
    selected = "4795f0a884c06f029c9d06a0a3d09cc0b9cfb791"
    original_vendor_pin = selected
# The only difference from the last reviewed vendor pin is the real GPU
# worker TIPC 22 reply descriptor. Seal its exact new source before replaying
# every unchanged FC27/NS2 source receipt from the previously approved pin.
if selected == "4795f0a884c06f029c9d06a0a3d09cc0b9cfb791":
    relative = "encore-active/ns2-runtime/gpu_session/core/hle/service/am/service/gpu_session.cpp"
    data = (V / relative).read_bytes()
    actual = hashlib.sha1(b"blob " + str(len(data)).encode() + bytes([0]) + data).hexdigest()
    assert actual == "37236a90479c1913cec33ad95d768a3fc80a1504", (
        "GPU worker TIPC 22 COPY owner drift", actual)
    selected = "f69176d429723da5d79251f6b858afc72c5d99e2"
    original_vendor_pin = selected
# The reviewed NS2 HID successor is exactly two fast-forward commits after
# b65d8d9 and changes only the live hid_server.cpp/.h (verified by GitHub
# compare b65d8d9...266080b4). Seal both new blobs before replaying all
# the unchanged FC27/NS2 source receipts of the reviewed parent. Do not add
# a blanket allowlist exception: a drifted runtime source remains fatal.
gsv_syncpt_201_revision = selected in {"ac33c63d7c53bfbd6df5f2f164f1fe078fdfddc7", "dfbba1e690128a44da755494c422ed1e6bdeb3c3", "47e9735a63c94ca42ec80412c6fcfd84a4910a53", "f007f3d539a523607fbef8b8895c2833e5b7af8c", "b3e6f9943bd46fda050ecb8151c4bb06e5251117", "7535dc9e5e7f0060b8e448da843f96882a2ce320", "f69176d429723da5d79251f6b858afc72c5d99e2"}
gsv_gpu_403_revision = selected in {"47e9735a63c94ca42ec80412c6fcfd84a4910a53", "f007f3d539a523607fbef8b8895c2833e5b7af8c", "b3e6f9943bd46fda050ecb8151c4bb06e5251117", "7535dc9e5e7f0060b8e448da843f96882a2ce320", "f69176d429723da5d79251f6b858afc72c5d99e2"}
gsv_native_115_revision = selected in {"f007f3d539a523607fbef8b8895c2833e5b7af8c", "b3e6f9943bd46fda050ecb8151c4bb06e5251117", "7535dc9e5e7f0060b8e448da843f96882a2ce320", "f69176d429723da5d79251f6b858afc72c5d99e2"}
gsv_transfer_memory_revision = selected in {"b3e6f9943bd46fda050ecb8151c4bb06e5251117", "7535dc9e5e7f0060b8e448da843f96882a2ce320", "f69176d429723da5d79251f6b858afc72c5d99e2"}
vi2_indexed_event_revision = selected in {"7535dc9e5e7f0060b8e448da843f96882a2ce320", "f69176d429723da5d79251f6b858afc72c5d99e2"}
gsv_transfer_bootstrap_revision = selected == "f69176d429723da5d79251f6b858afc72c5d99e2"
if selected in {"266080b4df8f56bb5a9b52c8c3ec253254c1578b", "ac33c63d7c53bfbd6df5f2f164f1fe078fdfddc7", "dfbba1e690128a44da755494c422ed1e6bdeb3c3", "47e9735a63c94ca42ec80412c6fcfd84a4910a53", "f007f3d539a523607fbef8b8895c2833e5b7af8c", "b3e6f9943bd46fda050ecb8151c4bb06e5251117", "7535dc9e5e7f0060b8e448da843f96882a2ce320", "f69176d429723da5d79251f6b858afc72c5d99e2"}:
    for relative, expected in (
        ("encore-active/ns2-runtime/hle/core/hle/service/hid/hid_server.cpp",
         ("b83f519fef3905eabb0bef65cab4d989033b5287"
           if selected in {"dfbba1e690128a44da755494c422ed1e6bdeb3c3", "47e9735a63c94ca42ec80412c6fcfd84a4910a53", "f007f3d539a523607fbef8b8895c2833e5b7af8c", "b3e6f9943bd46fda050ecb8151c4bb06e5251117", "7535dc9e5e7f0060b8e448da843f96882a2ce320", "f69176d429723da5d79251f6b858afc72c5d99e2"} else "dcceb2051105866bb6f9a702ccdd7271969e0763")),
        ("encore-active/ns2-runtime/hle/core/hle/service/hid/hid_server.h",
         ("1f3b144324b9014d4e5db64f796019f0e9f4c9a6"
           if selected in {"dfbba1e690128a44da755494c422ed1e6bdeb3c3", "47e9735a63c94ca42ec80412c6fcfd84a4910a53", "f007f3d539a523607fbef8b8895c2833e5b7af8c", "b3e6f9943bd46fda050ecb8151c4bb06e5251117", "7535dc9e5e7f0060b8e448da843f96882a2ce320", "f69176d429723da5d79251f6b858afc72c5d99e2"} else "e82f2486c79ac6aa2da5549619fb555c628d7afb")),
    ):
        raw = (V / relative).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        assert actual == reviewed_blob(relative, expected), ("Reviewed NS2 HID source drift", relative, actual)
    if gsv_syncpt_201_revision:
        # GSV cmd201 is admitted only because the real per-KProcess
        # NativeSyncptState is already allocated by the active constructor.
        # Verify the EXACT GSV owner pair, then reuse unchanged source seals.
        for relative, expected in (
            ("encore-active/ns2-runtime/graphics_supervisor/core/hle/service/am/service/graphics_supervisor.cpp",
             (native_gsv_active_cpp if native_gsv_compiled_handle_fix else
              "54bc84b2602d814312b6291cc104137de33afa53" if gsv_transfer_bootstrap_revision else
               "15302603f3713b5a80be053d2d58a0f410cffaa7" if vi2_indexed_event_revision else
               "91cdef4f7f28f5600ecd668904cf7d47ee0e9180" if gsv_transfer_memory_revision else
               "085e934b85fe6289988641b8ea2d64bf1a9a6d91" if gsv_native_115_revision else
               "38b2aed6deeec62ed82e173e6362ab1ba3e46737" if gsv_gpu_403_revision else
               "5e621a6cff708c5a2e2ab1b856990d0b5afc96f7")),
            ("encore-active/ns2-runtime/graphics_supervisor/core/hle/service/am/service/graphics_supervisor.h",
             ("4ae0674d5ed96a363f66df7eb788fa42f6bbd8e3" if native_video_pool_991_revision else
              "dad20285d5e14e28c268d9616b2662cc0be3a68a" if gsv_native_115_revision else
               "20bcdf77ac18db399d064a22da4a4cdf8cddcd9d" if gsv_gpu_403_revision else
               "d0837e45e672ee8043c01f1593af2a4d33658453")),
        ):
            raw = (V / relative).read_bytes()
            actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
            assert actual == reviewed_blob(relative, expected), ("Reviewed NS2 GSV syncpoint context drift", relative, actual)
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
         (native_gsv_active_cpp if native_gsv_compiled_handle_fix else
              "54bc84b2602d814312b6291cc104137de33afa53" if gsv_transfer_bootstrap_revision else
               "15302603f3713b5a80be053d2d58a0f410cffaa7" if vi2_indexed_event_revision else
               "91cdef4f7f28f5600ecd668904cf7d47ee0e9180" if gsv_transfer_memory_revision else
               "085e934b85fe6289988641b8ea2d64bf1a9a6d91" if gsv_native_115_revision else
           "38b2aed6deeec62ed82e173e6362ab1ba3e46737" if gsv_gpu_403_revision else
           "5e621a6cff708c5a2e2ab1b856990d0b5afc96f7" if gsv_syncpt_201_revision else
           "747c9a0b5461fc1975fa373997064e3dc401a9a3")),
        ("tests/ns2_syncpt_bootstrap_source.py",
         native_gsv_active_test if native_gsv_compiled_handle_fix else "69723ef7bd1d47af5086052882d0749cc817f64a"),
    ):
        raw = (V / relative).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        assert actual == reviewed_blob(relative, expected), ("Selected NS2 GSV COPY descriptor source drift", relative, actual)
    if selected in {"565f143c27443553b60ca1b21cc1094caa23ceb5", "010d5c61cefd62cbb5d27102cd9a2350fa0e69ce", "3460d10e60bff7dd8b057f592eb671cc35eddd25", "6f6f7f4cb154aa227eaf4d54330ff9d817b77ecb", "ce27bdd184c60d1f096ef1495c0ef7e5b7f0cdf0", "01c942171fea39c1f7cf31d13ab36895aebb593a", "dcf7116dd2c536e05c80d83ff9dbf30caa5cc109", "b65d8d9673475433f0b6eac72eb304bf23141666"}:
        protocol = (V / "encore-active/ns2-runtime/hle/core/hle/service/am/service/graphics_supervisor_protocol.h").read_bytes()
        protocol_blob = hashlib.sha1(b"blob " + str(len(protocol)).encode() + bytes([0]) + protocol).hexdigest()
        expected_protocol = "182467544d693433015e27e87d03fb62a43ec10b" if gsv_transfer_bootstrap_revision else "e416a9d4a9611c501e1349c7cbcfa83e2640712e" if vi2_indexed_event_revision else "2ab3a49da7843d2b1b0aa7b0d66c702cdbc9326d" if gsv_transfer_memory_revision else "661ff841efe8ea16fe0da557bb791596f334c6b5" if gsv_native_115_revision else "54f295b1ef7a0482a851a93579e66952b335ba9b" if gsv_gpu_403_revision else "4a35519c4f01cc4c1b604787bfbb139161f64a05" if selected in {"3460d10e60bff7dd8b057f592eb671cc35eddd25", "6f6f7f4cb154aa227eaf4d54330ff9d817b77ecb", "ce27bdd184c60d1f096ef1495c0ef7e5b7f0cdf0", "01c942171fea39c1f7cf31d13ab36895aebb593a", "dcf7116dd2c536e05c80d83ff9dbf30caa5cc109", "b65d8d9673475433f0b6eac72eb304bf23141666"} else "6ce5ba02c2032237f81d9684da9e56cfbfb831c0"
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
            assert actual == reviewed_blob(relative, expected), ("NS2 appletOE retry ABI source drift", relative, actual)
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
    expected = ("20dceafdc02e9436a81ac20b71b97ef7cf30d789" if gsv_transfer_bootstrap_revision else
                "024d652f5fbcbd9043507de6b6518c5b86d1e212" if gsv_transfer_memory_revision else
                "703eae24222c4d19d635fc4aa9a24d69f9520275" if gsv_gpu_403_revision else
                "11d548eb338a5b75bf3a87a6adb6aa6aa302e017" if ns2_gsv_497_dual else
                "11e7c9d0569a175567083367e485cbf75cbc2207" if ns2_gsv_497_v2 else
                "0f6b6960687501ef88b65ae0f3f4d0fd0693826a")
    assert actual == reviewed_blob(relative, expected), (
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
        assert actual == reviewed_blob(relative, expected), ("Merged engine/vendor source drift", relative, actual)
    print("ENCORE_MERGED_NS1_DMA_NS2_BOOT_SOURCE_PASS owners=12")

# The follow-up vendor change affects only the compiled NS2 GSV control
# plane and its pre-existing test; GPU/BufferCache and AM still pass the exact
# source seals above. A failed TIPC 305/497 must never move a null handle.
if selected in {"082cd1b77c7df80dc422eae5ba59d9cd33e48dc4", "e0fced3a091495e70362d8c4ca072942f027af24", "491fa7e2388d46e23827b1459360a5d7f4a2814b", "b177deb8282b14e1521485f5ac63bd7ccc9ca7ef", "06fc7dc2e0a00e00f831dfd78ae78087736276a3", "850086c79ec40838663989a81f33ba8ea2f15f6a"}:
    for relative, expected in (
        ("encore-active/ns2-runtime/graphics_supervisor/core/hle/service/am/service/graphics_supervisor.cpp",
         (native_gsv_active_cpp if native_gsv_compiled_handle_fix else
           "90be32737f454554125156cf468f58154dde40d4" if selected == "850086c79ec40838663989a81f33ba8ea2f15f6a" else
          "c9193e7ce505353c87f57e8a063cbdbf5b072f43" if selected == "06fc7dc2e0a00e00f831dfd78ae78087736276a3" else
          "8457d9a9a53725e6c1f15575c1151038f2457643")),
        ("tests/ns2_syncpt_bootstrap_source.py",
         (native_gsv_active_test if native_gsv_compiled_handle_fix else
           "21fb7c886286a39eaec5ca4495bfba1bb55584b1" if selected == "850086c79ec40838663989a81f33ba8ea2f15f6a" else
          "41d6f0514f281bfb65cad052c2fb61cfa9d749b2" if selected == "06fc7dc2e0a00e00f831dfd78ae78087736276a3" else
          "51beddbe0454039c23728f39f7c84d05325fd8cf" if selected in {"e0fced3a091495e70362d8c4ca072942f027af24", "491fa7e2388d46e23827b1459360a5d7f4a2814b", "b177deb8282b14e1521485f5ac63bd7ccc9ca7ef", "06fc7dc2e0a00e00f831dfd78ae78087736276a3", "850086c79ec40838663989a81f33ba8ea2f15f6a"} else
          "eb150745a18068366885299f82eacf42045cb50e")),
    ):
        body = (V / relative).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(body)).encode() + bytes([0]) + body).hexdigest()
        assert actual == reviewed_blob(relative, expected), ("NS2 GPU/VI2 session source drift", relative, actual)
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
        assert actual == reviewed_blob(relative, expected), ("NS2 GPU VA identity rollback drift", relative, actual)
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
        assert actual == reviewed_blob(relative, expected), ("NS2 GSV nvsrv CMIF source drift", relative, actual)
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
        assert actual == reviewed_blob(relative, expected), ("Selected NS2 IPC source drift", relative, actual)
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
        assert actual == reviewed_blob(relative, expected), ("NS2 appletOE selected owner drift", path, actual)
    selected = "7fc673495b2ee18d5216023280057a42aa78d46c"
if selected == "7fc673495b2ee18d5216023280057a42aa78d46c":
    for path, expected in (
        ("encore-active/ns2-runtime/gamechat/core/hle/service/friend/friend.cpp", "ceb8b4afa7c0f19af3fe209fd8ca8d848a66d2cb"),
        ("encore-active/ns2-runtime/graphics_supervisor/core/hle/service/am/service/graphics_supervisor.cpp", native_gsv_active_cpp if native_gsv_compiled_handle_fix else "5d83ac9f7e7c3df2201b1ddf5e9458a7d802bcc4"),
        ("encore-active/ns2-runtime/graphics_supervisor/core/hle/service/am/service/graphics_supervisor.h", "be4d6eaaa43ee247b61d835a7b280fe26aa8eb63"),
        ("encore-active/ns2-runtime/hle/core/hle/service/am/service/native_image_layout.h", "978b0a162c0fa6043942e96e57c7c464dd167c53"),
    ):
        raw=(V/path).read_bytes()
        actual=hashlib.sha1(b"blob "+str(len(raw)).encode()+bytes([0])+raw).hexdigest()
        assert actual == reviewed_blob(relative, expected), ("NS2 GameChat owner drift", path, actual)
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
        assert actual == reviewed_blob(relative, expected), ("NS2 IPC peer owner drift", path, actual)
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
        assert actual == reviewed_blob(relative, expected), ("RomFS-only successor drift",relative,actual)

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
        assert actual == reviewed_blob(relative, expected), ("Sync rollback source drift",relative,actual)
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
            assert actual == reviewed_blob(relative, expected), ("Quiet NS2 SVC witness drift",relative,actual)
    if selected in {"1a09972eea6f473fda1b714efe84cd52219bf681", "3e6647827122c34704c2699a6f5e9b20fff3e9a6", "6d64217ea5804fb86dbf57685a3da0cb1d45ba32", "3f1fcfef119ca50dd630f0518a7fae1b96c7a85a", "0e4e96df638fc29c3bd2a8fcfe9f50821c5e5b3a", "9136d2e88c43233bcd029f22bdfda0e5c94a552f", "75ef34d7ef7f68b5eb4f1c6d0d99b6cbc55742d6", "34f02a3800cb6fb5330c099c81571ab03fd69ae1", "0d75406e36a3676b45184670093f0ecf652aab2f", "372a83d95622f152211fe91afa05d1e60ce84bea", "a3cc07ff68f8154543f2b07a6b3e6c01f9922ab9", "ab417b59c5f7f4613ff27386be05c0644d0ed776", "372a83d95622f152211fe91afa05d1e60ce84bea", "a3cc07ff68f8154543f2b07a6b3e6c01f9922ab9", "ab417b59c5f7f4613ff27386be05c0644d0ed776"}:
        for relative, expected in {
            "encore-active/ns2-astc/include/video_core/texture_cache/texture_cache.h": ("c7cb95ecaf388b925fc29582499bbd4b54a77f75" if selected in {"6d64217ea5804fb86dbf57685a3da0cb1d45ba32", "3f1fcfef119ca50dd630f0518a7fae1b96c7a85a", "0e4e96df638fc29c3bd2a8fcfe9f50821c5e5b3a", "9136d2e88c43233bcd029f22bdfda0e5c94a552f", "75ef34d7ef7f68b5eb4f1c6d0d99b6cbc55742d6", "34f02a3800cb6fb5330c099c81571ab03fd69ae1", "0d75406e36a3676b45184670093f0ecf652aab2f", "372a83d95622f152211fe91afa05d1e60ce84bea", "a3cc07ff68f8154543f2b07a6b3e6c01f9922ab9", "ab417b59c5f7f4613ff27386be05c0644d0ed776", "372a83d95622f152211fe91afa05d1e60ce84bea", "a3cc07ff68f8154543f2b07a6b3e6c01f9922ab9", "ab417b59c5f7f4613ff27386be05c0644d0ed776"} else "859a9e46fb63a97fee82c8ea6b1566317264f98f" if selected == "3e6647827122c34704c2699a6f5e9b20fff3e9a6" else "0d99f9a861c645562519f71d62f4f49bfedd8101"),
            "tests/ns1_r23_18_tir_host.py": ("753df3ca146cba983057801df36dcf9db0b5fc6b" if selected in {"6d64217ea5804fb86dbf57685a3da0cb1d45ba32", "3f1fcfef119ca50dd630f0518a7fae1b96c7a85a", "0e4e96df638fc29c3bd2a8fcfe9f50821c5e5b3a", "9136d2e88c43233bcd029f22bdfda0e5c94a552f", "75ef34d7ef7f68b5eb4f1c6d0d99b6cbc55742d6", "34f02a3800cb6fb5330c099c81571ab03fd69ae1", "0d75406e36a3676b45184670093f0ecf652aab2f", "372a83d95622f152211fe91afa05d1e60ce84bea", "a3cc07ff68f8154543f2b07a6b3e6c01f9922ab9", "ab417b59c5f7f4613ff27386be05c0644d0ed776", "372a83d95622f152211fe91afa05d1e60ce84bea", "a3cc07ff68f8154543f2b07a6b3e6c01f9922ab9", "ab417b59c5f7f4613ff27386be05c0644d0ed776"} else "7c225ac2065a1721eb53cc034ea3bc4e3b581770" if selected == "3e6647827122c34704c2699a6f5e9b20fff3e9a6" else "520c5eb05f23c5fc6ad4438c9f6df774533644e1"),
            "tests/fc27_deferred_page_protection_host.py": ("ae967badcfef7e098ac2620b789a1138fad79058" if selected in {"6d64217ea5804fb86dbf57685a3da0cb1d45ba32", "3f1fcfef119ca50dd630f0518a7fae1b96c7a85a", "0e4e96df638fc29c3bd2a8fcfe9f50821c5e5b3a", "9136d2e88c43233bcd029f22bdfda0e5c94a552f", "75ef34d7ef7f68b5eb4f1c6d0d99b6cbc55742d6", "34f02a3800cb6fb5330c099c81571ab03fd69ae1", "0d75406e36a3676b45184670093f0ecf652aab2f", "372a83d95622f152211fe91afa05d1e60ce84bea", "a3cc07ff68f8154543f2b07a6b3e6c01f9922ab9", "ab417b59c5f7f4613ff27386be05c0644d0ed776", "372a83d95622f152211fe91afa05d1e60ce84bea", "a3cc07ff68f8154543f2b07a6b3e6c01f9922ab9", "ab417b59c5f7f4613ff27386be05c0644d0ed776"} else "876ebf0f43ffc3999d7ed6d983160d3447bc15f0" if selected == "3e6647827122c34704c2699a6f5e9b20fff3e9a6" else "cb821c1aaab3f968ce25d7ac92d489e01ba3b8f6"),
        }.items():
            raw = (V/relative).read_bytes()
            actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
            assert actual == reviewed_blob(relative, expected), ("Selected PS5 F07 TextureCache source drift", relative, actual)
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
