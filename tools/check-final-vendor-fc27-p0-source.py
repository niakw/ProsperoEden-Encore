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
REVIEWED_PINS.add("1ca2828bfccd0d5c8a903f3c503480f1fc1b6ddc")
REVIEWED_PINS.add("7a4ddd589b7a20d75a1a6019a67a16c5f2d39bc5")
REVIEWED_PINS.add("9edb09cf0a720c6b22fe092efd21cc9891225a48")
REVIEWED_PINS.add("d8c1595f187b24b434533c02fe4085a2905f34aa")
REVIEWED_PINS.add("754dc4110ad1e13ea0237e5826599f97d0ccd2f9")
REVIEWED_PINS.add("a773cfa1a5cd95285eab7e8dd4d21ceef848a0a0")
REVIEWED_PINS.add("615ec1b7a73bb26dcff8525cf543aafff04ecbf0")
REVIEWED_PINS.add("95ed29da0eb91af4561154ec3688968959185b9b")
REVIEWED_PINS.add("457f9501c52fcf6ce2aaca967757c0eb9e452f58")
REVIEWED_PINS.add("08972732d0402fa455a4982ed5ffd5d9f2c7e83c")
REVIEWED_PINS.add("c74fb345ac3d8fa752f403369827a432f3503fb5")
REVIEWED_PINS.add("3a97e47a0cfe94ec55227af363d8c289de59d4f8")
REVIEWED_PINS.add("3de91cf284c8ef234c757c046998c4f48165c59a")
REVIEWED_PINS.add("2fd07582db57fdddc67e6fd56cec16624a902c6a")
REVIEWED_PINS.add("4411fc172eef84080ab7de23158349bbe7d08f88")
REVIEWED_PINS.add("0c4eafeb9f197e76a1f0bb06038ef9bbf2c7565d")
REVIEWED_PINS.add("bc6baf037ac3304d4ba81cf7589f7e52e8fa8ae0")
REVIEWED_PINS.add("546e1aa34d2ff183dd4c737f9da8fbf4a62be24e")
REVIEWED_PINS.add("f65ccc439534ffd9ce0a307b23bd511b4e32857a")
REVIEWED_PINS.add("4e6a966508e718d02526d4d220e112591536f28c")
REVIEWED_PINS.add("2d07b5e65baf35c82d0b0e557617aefe730a10b1")
REVIEWED_PINS.add("7baf9cc07c6aceee185032544d964f04a2fed108")
REVIEWED_PINS.add("1f8a3bbaa7fc33118e63ebef829202d825475bfe")
REVIEWED_PINS.add("1e513ae001669127538a346c7f390af55edd6712")
REVIEWED_PINS.add("d31aa01bdfa87165a272473c385040723bf2c1f6")
REVIEWED_PINS.add("20cb62f1be572c8063ce4162d3227c8784a1e5ff")
REVIEWED_PINS.add("19a62450fe8eb2fd3c28a4e940ed412beb9dc7ba")
REVIEWED_PINS.add("76a225552c296686cd1022584d73decd46767f75")
REVIEWED_PINS.add("205c6a3572955c3d8002f5faca68d6ce1359817c")
REVIEWED_PINS.add("bfb9d4da9c0f3811924738311fc2c6056e0e4dcb")
REVIEWED_PINS.add("265609006ea8d76d971cc49af37bac23890ca4f5")
REVIEWED_PINS.add("d32b4280fe6737e1da3b56ed47409422500c756f")
REVIEWED_PINS.add("1e1230f882ac6167ca0e6999875f07971b77985c")
REVIEWED_PINS.add("dd4127535a60ff1b22700edac24ca5a5f7d4fac2")
REVIEWED_PINS.add("b1917364f678ba469c4d817f663d10ca5be5c0c3")
REVIEWED_PINS.add("bc44094d78d0bba088ca0b48f37e9a4c38a9fbc5")
REVIEWED_PINS.add("ed03e467016f5afbcb722c54af374d6916ccd6a0")
REVIEWED_PINS.add("b8396c6483aa8278bd75b6757aed3bb5a9206e52")
REVIEWED_PINS.add("a8c9170802811e7bb19345a461c3ae8dc72c27be")
REVIEWED_PINS.add("42b34a5dc46b594cb029362e8f130900adf4424e")
REVIEWED_PINS.add("77b736148129ffa72c9f6c081695b7c7515c3ed9")
REVIEWED_PINS.add("4354add020afac574198f63d87167f3022bff9c6")
selected=subprocess.check_output(["git","rev-parse","HEAD:vendor"],cwd=ROOT,text=True).strip()
gitlink_vendor_pin = selected
actual_vendor_pin = gitlink_vendor_pin
shipping_vendor_pin = gitlink_vendor_pin
if actual_vendor_pin in {"9632ac089f8b2d89a6856a42e8fb55206cdba1fa", "b5c6f089a6aecd321d08a40238f3cd502f505b26", "dc9f5f95b1f784bb358d6480e53de7247d61d777", "a441295022b23834f8531c54d2b0965f84023278", "7c5d5220dd4df4a531418458ab623ef86c41348c", "44540549ee9a65eb8078e271f43ccded0e8e984f", "d63d82dfb9c2afbacac4c9dc1491f743fb083d52", "d634b381d85dae30492dd6291fc4e6e96143f363", "692e9819a7a1f1b818bf3739c72d8e5252cae661", "166e473e120a86a6edcd32a975ffe19b45ffdd42", "3522d8578fbcd7b46d2a439d5d718dfb570beb7b"}:
    assert subprocess.check_output(["git", "-C", str(V), "rev-parse", "HEAD^{tree}"], text=True).strip() == {
        "9632ac089f8b2d89a6856a42e8fb55206cdba1fa": "51c9a38eba78d69893c48db6f3e48a169ea879e3",
        "b5c6f089a6aecd321d08a40238f3cd502f505b26": "668fb8effa6963be062d780e3bd145a5233d6b7e",
        "dc9f5f95b1f784bb358d6480e53de7247d61d777": "1660883553006cfca7e80465ad5521b4c2ca33b1",
    "a441295022b23834f8531c54d2b0965f84023278": "d53129478299aded8cb8d7432751b43fa74594b9",
    "7c5d5220dd4df4a531418458ab623ef86c41348c": "9ff41b47bfe30a9cef86a5ab7c584c0094f586bf",
    "44540549ee9a65eb8078e271f43ccded0e8e984f": "86d6068c438cc36ffd01513fc178d2590fb010cb",
    "d63d82dfb9c2afbacac4c9dc1491f743fb083d52": "290d8c51e8ab40dd56651d50483abe42e11fa404",
    "d634b381d85dae30492dd6291fc4e6e96143f363": "a51ee73257c13fce70cbaf5d3e26c62010abf2e9",
    "692e9819a7a1f1b818bf3739c72d8e5252cae661": "6743fed9174ee7e3451afbbad230dca6c2e4203c",
    "166e473e120a86a6edcd32a975ffe19b45ffdd42": "3a996079e9de76e0c3d8bd2e595e6c83dadd6ce0",
    "3522d8578fbcd7b46d2a439d5d718dfb570beb7b": "67917388ba3308bacfa3e8da6fff9d83c4efb713",
    }[actual_vendor_pin]
    for relative, expected in {
        "encore-active/eden-vulkan/vk_pipeline_cache_cost.cpp": ("c92e3dbbf4de08030589d9776dded974accf11eb" if actual_vendor_pin in {"44540549ee9a65eb8078e271f43ccded0e8e984f", "d63d82dfb9c2afbacac4c9dc1491f743fb083d52", "d634b381d85dae30492dd6291fc4e6e96143f363", "692e9819a7a1f1b818bf3739c72d8e5252cae661", "166e473e120a86a6edcd32a975ffe19b45ffdd42", "3522d8578fbcd7b46d2a439d5d718dfb570beb7b"} else "206d845256bbdc1d5f8d660aeed718ad4f607063" if actual_vendor_pin in {"a441295022b23834f8531c54d2b0965f84023278", "7c5d5220dd4df4a531418458ab623ef86c41348c"} else "b246cf9562f8f0c37d287f7049874f04561a4b8f" if actual_vendor_pin == "dc9f5f95b1f784bb358d6480e53de7247d61d777" else "fc537323bb9f63d70ef5f8cedd65886e6a0099c0"),
        "tests/fc27_xmad_pointer_fold_host.py": ("5498ea8990e905cb4b2320151a040627681dc77c" if actual_vendor_pin in {"44540549ee9a65eb8078e271f43ccded0e8e984f", "d63d82dfb9c2afbacac4c9dc1491f743fb083d52", "d634b381d85dae30492dd6291fc4e6e96143f363", "692e9819a7a1f1b818bf3739c72d8e5252cae661", "166e473e120a86a6edcd32a975ffe19b45ffdd42", "3522d8578fbcd7b46d2a439d5d718dfb570beb7b"} else "0dc365434b000ae779d8e44546893ed1722994fc" if actual_vendor_pin in {"a441295022b23834f8531c54d2b0965f84023278", "7c5d5220dd4df4a531418458ab623ef86c41348c"} else "ac228172c0fe65b9ccfb2dc2ee30d0b1db9190da" if actual_vendor_pin == "dc9f5f95b1f784bb358d6480e53de7247d61d777" else "3d3f97ec6e3e9d182558908849306d8cc7c4a78e"),
        "tests/fc27_dynamic_texture_static_sampler_host.py": ("0b8eafaaa919dfd838facaf409acb9cc7018ac6e" if actual_vendor_pin in {"44540549ee9a65eb8078e271f43ccded0e8e984f", "d63d82dfb9c2afbacac4c9dc1491f743fb083d52", "d634b381d85dae30492dd6291fc4e6e96143f363", "692e9819a7a1f1b818bf3739c72d8e5252cae661", "166e473e120a86a6edcd32a975ffe19b45ffdd42", "3522d8578fbcd7b46d2a439d5d718dfb570beb7b"} else "e99e5e9216d971cbaf3b48d89a5924ac85c62b33" if actual_vendor_pin in {"a441295022b23834f8531c54d2b0965f84023278", "7c5d5220dd4df4a531418458ab623ef86c41348c"} else "57b30130d9d321b2954de9c35d5cb522a6f76c69" if actual_vendor_pin == "dc9f5f95b1f784bb358d6480e53de7247d61d777" else "7cf6b36d5de4aa93f118a0bea0381cecafe45988")
    }.items():
        raw = (V / relative).read_bytes()
        assert hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest() == expected, relative
if actual_vendor_pin in {"b5c6f089a6aecd321d08a40238f3cd502f505b26", "dc9f5f95b1f784bb358d6480e53de7247d61d777", "a441295022b23834f8531c54d2b0965f84023278", "7c5d5220dd4df4a531418458ab623ef86c41348c", "44540549ee9a65eb8078e271f43ccded0e8e984f", "d63d82dfb9c2afbacac4c9dc1491f743fb083d52", "d634b381d85dae30492dd6291fc4e6e96143f363", "692e9819a7a1f1b818bf3739c72d8e5252cae661", "166e473e120a86a6edcd32a975ffe19b45ffdd42", "3522d8578fbcd7b46d2a439d5d718dfb570beb7b"}:
    for relative, expected in {
        "sources/eden/src/core/hle/service/am/applet.h": "a8309188928c796d439cd828b756e481f3f6fa2c",
        "sources/eden/src/core/hle/service/am/event_observer.cpp": "4a132abde4b6e70407b3267ea2298e8a6f0ce239",
        "sources/eden/src/core/hle/service/am/event_observer.h": "2213d4bac622dc1476a4f1821e2e4fdfe6096acd",
        "sources/eden/src/core/hle/service/am/process_holder.cpp": "deb72de87cbb46c158a88e84eb2ef5c692079dd7",
        "sources/eden/src/core/hle/service/am/process_holder.h": "a2df53cbd7c25ed43cdf9cd97f453e65816c7202",
    }.items():
        raw = (V / relative).read_bytes()
        assert hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest() == expected, ("AM observer owner drift", relative)
if selected in {"17253dc91e9fe1eb2d9980f261f59d227bfcd1a1", "ac880cd408116e6eb53ba2400abc52970b81f539", "95343060f948601930f2e62b919da0789f0830bb", "12ab9a8411f5c9df1b5cc73f01c923ad9479c8af", "224b05e6f8b1a266b0d55d1ded5332f7a2eaed7c", "150a3a79ca103061f73a9a50ca8f463a3b4712f3", "fcd62408fdbc33af01a4caebc8fd44c8500b628f"}:
    if selected in {"ac880cd408116e6eb53ba2400abc52970b81f539", "95343060f948601930f2e62b919da0789f0830bb", "12ab9a8411f5c9df1b5cc73f01c923ad9479c8af", "224b05e6f8b1a266b0d55d1ded5332f7a2eaed7c", "150a3a79ca103061f73a9a50ca8f463a3b4712f3", "fcd62408fdbc33af01a4caebc8fd44c8500b628f"}:
        # A merge commit, but exactly the reviewed 17253dc9 source tree.
        reviewed_tree = subprocess.check_output(
            ["git", "-C", str(V), "rev-parse", "HEAD^{tree}"], text=True
        ).strip()
        assert reviewed_tree == {
            "ac880cd408116e6eb53ba2400abc52970b81f539": "01c09ec124779e7d976718af09a0e5e94cb4ac20",
            "95343060f948601930f2e62b919da0789f0830bb": "efa6548c57f7823d4e8b2c975944c6846b765ff3",
            "12ab9a8411f5c9df1b5cc73f01c923ad9479c8af": "64179fcce4962f9b2b7c738504a6fa0e00b2b292",
            "224b05e6f8b1a266b0d55d1ded5332f7a2eaed7c": "3f7f1523cef730ad153bf658fbb3567222d6e956",
            "150a3a79ca103061f73a9a50ca8f463a3b4712f3": "39fb9a3efe65f67115dfcdebe39a55334a702f2d",
            "fcd62408fdbc33af01a4caebc8fd44c8500b628f": "8447712e2cecf661910fd1a32613f0b844ceaeb0",
        }[selected], ("Vendor reviewed source tree drift", selected, reviewed_tree)
    # Reconstruct only the two corrected source lines before reusing the
    # already-qualified FC27/P0 graph; every other owner remains exact.
    import sys
    sys.path.insert(0, str(V/"tests"))
    from native_msaa_handle_receipt import (
        GUEST_CACHE_LOCK_SUCCESSOR, INTEGRATED_RASTERIZER,
        restore_guest_cache_lock_successor, blob)
    if selected == "fcd62408fdbc33af01a4caebc8fd44c8500b628f":
        # Exact one-owner successor: the 64-bit SIZE_MAX comparison was
        # tautological. Verify both the replacement and the prior complete
        # shipping DMA blob; preserve all other vendor owners byte-for-byte.
        dma=(V/"encore-active/eden-core/src/video_core/engines/maxwell_dma.cpp").read_text()
        assert blob(dma.encode("utf-8"))=="0c186d79194135a5d0b300c3a8a6fb0aa503810b"
        a='#include <utility>' + chr(10)
        guard_new='if (!std::in_range<size_t>(byte_count) ||'
        guard_old='if (byte_count > (std::numeric_limits<size_t>::max)() ||'
        assert dma.count(a)==1 and dma.count(guard_new)==1
        previous=dma.replace(a,'',1).replace(guard_new,guard_old,1)
        assert blob(previous.encode("utf-8"))=="cc9439c3159bdcba091e8040408e462b812d03c0"
    raster=(V/"encore-active/eden-vulkan/vulkan_rasterizer.cpp").read_text()
    assert blob(raster.encode("utf-8"))==GUEST_CACHE_LOCK_SUCCESSOR
    predecessor=restore_guest_cache_lock_successor(raster)
    assert blob(predecessor.encode("utf-8"))==INTEGRATED_RASTERIZER
    REVIEWED_PINS.add(selected)
    gitlink_vendor_pin = "4354add020afac574198f63d87167f3022bff9c6"
    shipping_vendor_pin = "4354add020afac574198f63d87167f3022bff9c6"

# The FC27 2026-11-22 exit crash at nvhost_as_gpu::~nvhost_as_gpu
# required an exact three-file vendor successor. Its root tree is checked so
# no unrelated NS2 or FC27 source gets silently accepted.
# FC27 first-use stalls: the qualified small-cache successor changes only
# the bounded preload admission policy. Reject other vendor changes by the
# complete Git tree and require the exact maintained runtime source blob.
# NS2 SelfController 2400: one production handler binding plus its source
# regression test. Authenticate the exact vendor tree and BOTH changed blobs,
# then replay the already-qualified FC27 prewarm + NVDRV source lineage.
PS5_NS2_SELF_CONTROLLER_2400_PIN = "dc526f06d277dfa0a4afa48b4cf8b3153ebe7267"
PS5_NS2_NUP_IPC_PIN = "87964d15e91b6b6523c88682e5ca017f6e1a808b"
PS5_NS2_LICHII_ZEROED_PIN = "ae6f59a9865a3f4f178c4d836a3e04c93cceb69a"
PS5_NS2_LICHII_AM_PIN = "f5c80c900b58b57808f609b5ffdc0e6ab9de7bd0"
PS5_NS2_LICHII_AM_2_PIN = "d22b7066410c627230f9bfa8b3b5be8baff4fcdf"
PS5_NS2_DECRYPTED_FORMATS_PIN = "f4f5d53596879960b19a3701bbd2272ef1f3c634"
if actual_vendor_pin in {PS5_NS2_SELF_CONTROLLER_2400_PIN, PS5_NS2_NUP_IPC_PIN, PS5_NS2_LICHII_ZEROED_PIN, PS5_NS2_LICHII_AM_PIN, PS5_NS2_LICHII_AM_2_PIN, PS5_NS2_DECRYPTED_FORMATS_PIN}:
    assert selected == actual_vendor_pin
    tree = subprocess.check_output(
        ["git", "-C", str(V), "rev-parse", "HEAD^{tree}"], text=True).strip()
    assert tree == ("e1e3fa4878d6203a51c7aa6ec93e09f81a175cdf" if actual_vendor_pin == PS5_NS2_DECRYPTED_FORMATS_PIN else "805d74f7ccf0ddf060782615d2bd94bb8d26b412" if actual_vendor_pin == PS5_NS2_LICHII_AM_2_PIN else "68acadcd14d23135fd02df0a0e508c668917168c" if actual_vendor_pin == PS5_NS2_LICHII_AM_PIN else "e125210acec0eaef51c6c038d200cc9c12981ace" if actual_vendor_pin == PS5_NS2_LICHII_ZEROED_PIN else "c1cbb8a3ca0b7231e260fdb5e9f6a1c7964097ab" if actual_vendor_pin == PS5_NS2_NUP_IPC_PIN else "e21b2c70c00c50fc7d682150cb62e87fe856306c"), tree
    for relative, expected in {
        "encore-active/ns2-runtime/self_controller/core/hle/service/am/service/self_controller.cpp":
            ("01d0f8a05faaa30b01a1802680a954aebfbf118b" if actual_vendor_pin in {PS5_NS2_LICHII_AM_PIN, PS5_NS2_LICHII_AM_2_PIN, PS5_NS2_DECRYPTED_FORMATS_PIN} else "7783c917d8b2f2e8d26c091d5507964fcf9d44dd" if actual_vendor_pin == PS5_NS2_LICHII_ZEROED_PIN else "743bd9c9a4b9a3550c853ffa8fc06898c01618ff"),
        "tests/r23_fw23_selfcontroller_240.py":
            ("367b99a467a7cf1559973af65c69f7c2231764f4" if actual_vendor_pin in {PS5_NS2_LICHII_AM_PIN, PS5_NS2_LICHII_AM_2_PIN, PS5_NS2_DECRYPTED_FORMATS_PIN} else "ed80a6d62d5328c394a133b5f28112443e893f36" if actual_vendor_pin == PS5_NS2_LICHII_ZEROED_PIN else "b03d2015ac00a0ce2e52bea002c931b330a55d96"),
    }.items():
        raw = (V / relative).read_bytes()
        assert hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest() == expected, relative
    if actual_vendor_pin in {PS5_NS2_NUP_IPC_PIN, PS5_NS2_LICHII_ZEROED_PIN, PS5_NS2_LICHII_AM_PIN, PS5_NS2_LICHII_AM_2_PIN, PS5_NS2_DECRYPTED_FORMATS_PIN}:
        for relative, expected in {
                "encore-active/eden-core/src/core/hle/service/service.cpp": ("e388765fb2cf372adc01c2c3ec174955659ccc2a" if actual_vendor_pin in {PS5_NS2_LICHII_AM_PIN, PS5_NS2_LICHII_AM_2_PIN, PS5_NS2_DECRYPTED_FORMATS_PIN} else "e2d52974d419b9ed4089da8baed104dd1dbd282d"),
                "encore-active/ns2-runtime/process/core/core.cpp": "a2721a630b8b32222ff586ea2db19ee726d4d5b9",
                "tests/ns1_r23_54_storage_pacing.py": ("eb88e3701448c3b3572155a00158b3a5955eb45e" if actual_vendor_pin in {PS5_NS2_LICHII_AM_PIN, PS5_NS2_LICHII_AM_2_PIN, PS5_NS2_DECRYPTED_FORMATS_PIN} else "9abec8ca14bfaaed76128fab34592f0b3911afe9"),
                "tests/shutdown_general_channel_lifetime_source.py": "4bb0ef388211b1c9110afce55ef80983e5050782",
                "tests/shutdown_teardown_lifetime_source.py": "e40deaae0b1f3aab6a5a12f7978be470b3ee0463"
        }.items():
            raw = (V / relative).read_bytes()
            digest = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
            assert digest == expected, ("NS2 NUP/IPC successor drift", relative, digest)
        REVIEWED_PINS.add(PS5_NS2_NUP_IPC_PIN)
    if actual_vendor_pin == PS5_NS2_LICHII_ZEROED_PIN:
        raw = (V/"encore-active/ns2-runtime/self_controller/core/hle/service/am/service/self_controller.h").read_bytes()
        assert hashlib.sha1(b"blob "+str(len(raw)).encode()+bytes([0])+raw).hexdigest() == "571793025a886f3878e7b61ec9569faba84647f2"
        REVIEWED_PINS.add(PS5_NS2_LICHII_ZEROED_PIN)
    if actual_vendor_pin == PS5_NS2_LICHII_AM_PIN:
        for relative, expected in {
            "encore-active/eden-core/include/core/hle/service/service.h": "b871694b3b865465ec8e08e358d6799449092498",
            "encore-active/eden-core/src/core/hle/service/service.cpp": "e388765fb2cf372adc01c2c3ec174955659ccc2a",
            "encore-active/ns2-runtime/am/core/hle/service/am/service/application_functions.cpp": "a26850d9addcd35c483fa1da28d440537896ee13",
            "encore-active/ns2-runtime/hle/core/hle/service/am/service/application_proxy.cpp": "92de53cfc78a028c7fd8ccd57ec73b0b81ab0912",
            "encore-active/ns2-runtime/hle/core/hle/service/am/service/application_proxy.h": "ed88acba848071d6c9e2c0b080c3234925003b50",
            "encore-active/ns2-runtime/hle/core/hle/service/am/service/application_proxy_service.cpp": "0d2ed417d23f11a97f91cf18e733fad6515d0756",
            "encore-active/ns2-runtime/hle/core/hle/service/nx2_stub_interface.h": "68c087899680b8a3a764d6cd3c362b0e98237ae0",
            "encore-active/ns2-runtime/self_controller/core/hle/service/am/service/self_controller.cpp": "01d0f8a05faaa30b01a1802680a954aebfbf118b",
            "tests/ns1_r23_126_uuid_sha1.py": "4a565a3c5fd53dff3ca157aa0793fb86f7827791",
            "tests/ns1_r23_54_storage_pacing.py": "eb88e3701448c3b3572155a00158b3a5955eb45e",
            "tests/r23_fw23_selfcontroller_240.py": "367b99a467a7cf1559973af65c69f7c2231764f4",
        }.items():
            raw = (V/relative).read_bytes()
            actual = hashlib.sha1(b"blob "+str(len(raw)).encode()+bytes([0])+raw).hexdigest()
            assert actual == expected, ("NS2 Lichii structural owner drift",relative,actual)
        REVIEWED_PINS.add(PS5_NS2_LICHII_AM_PIN)
    if actual_vendor_pin in {PS5_NS2_LICHII_AM_2_PIN, PS5_NS2_DECRYPTED_FORMATS_PIN}:
        for relative, expected in {
            "encore-active/ns2-runtime/am_structure/core/hle/service/am/service/application_accessor.cpp": "25e75933c344a75f108ff1c7f40845feb405c5fd",
            "encore-active/ns2-runtime/am_structure/core/hle/service/am/service/application_accessor.h": "48ec3effbf4af4df285dc98fbd6c5cf7a3ada21a",
            "encore-active/ns2-runtime/am_structure/core/hle/service/am/service/audio_controller.cpp": "0b9efbe1cfdb3072828709170bbefa202114d08d",
            "encore-active/ns2-runtime/am_structure/core/hle/service/am/service/common_state_getter.cpp": "2c5e5364146b125c038b239056bf06f2aaea5ef3",
            "encore-active/ns2-runtime/am_structure/core/hle/service/am/service/display_controller.cpp": "7e7db23708718f6513b784c489edf61d8d555fac",
            "encore-active/ns2-runtime/am_structure/core/hle/service/am/service/library_applet_accessor.cpp": "7119c605968dd50372d5d62097bb2f9d017ab6e6",
            "encore-active/ns2-runtime/am_structure/core/hle/service/am/service/library_applet_creator.cpp": "1157033948e6a6f015ef14dedda30a40ff750b54",
            "encore-active/ns2-runtime/am_structure/core/hle/service/am/service/window_controller.cpp": "6b19368d91035f6372cf8540c4b45caf371c1cd3",
        }.items():
            raw = (V/relative).read_bytes()
            actual = hashlib.sha1(b"blob "+str(len(raw)).encode()+bytes([0])+raw).hexdigest()
            assert actual == expected, ("Lichii AM real and stub owner drift",relative,actual)
        if actual_vendor_pin == PS5_NS2_DECRYPTED_FORMATS_PIN:
            for relative, expected in {
                "encore-active/eden-core/src/core/file_sys/card_image.cpp": "5d5e6b40099b18768dadd39ba839881989e7ff6f",
                "encore-active/eden-core/src/core/file_sys/content_archive.cpp": "d31f75bf354f3ce5af1ac2f1ac170586503b1877",
                "encore-active/eden-core/src/core/file_sys/fssystem/fssystem_nca_reader.cpp": "49841fbbde5bd086f23aba601c80b19176ed8ae4",
                "encore-active/eden-core/src/core/loader/loader.cpp": "0b4448bcf4bef93b9d2a54cf96256d5b81d9424e",
            }.items():
                raw = (V / relative).read_bytes()
                digest = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
                assert digest == expected, ("DNSP/DXCI exact source drift", relative, digest)
            REVIEWED_PINS.add(PS5_NS2_DECRYPTED_FORMATS_PIN)
        REVIEWED_PINS.add(PS5_NS2_LICHII_AM_2_PIN)
    REVIEWED_PINS.add(PS5_NS2_SELF_CONTROLLER_2400_PIN)
    selected = "dbef23055897b1649f83c20cf7a0516e64f3d5cd"

PS5_FC27_RECENT_PREWARM_PIN = "dbef23055897b1649f83c20cf7a0516e64f3d5cd"
if actual_vendor_pin in {PS5_FC27_RECENT_PREWARM_PIN, PS5_NS2_SELF_CONTROLLER_2400_PIN, PS5_NS2_NUP_IPC_PIN, PS5_NS2_LICHII_ZEROED_PIN, PS5_NS2_LICHII_AM_PIN, PS5_NS2_LICHII_AM_2_PIN, PS5_NS2_DECRYPTED_FORMATS_PIN}:
    assert selected == PS5_FC27_RECENT_PREWARM_PIN
    new_tree = subprocess.check_output(
        ["git", "-C", str(V), "rev-parse", "HEAD^{tree}"], text=True).strip()
    assert new_tree == ("e1e3fa4878d6203a51c7aa6ec93e09f81a175cdf" if actual_vendor_pin == PS5_NS2_DECRYPTED_FORMATS_PIN else "805d74f7ccf0ddf060782615d2bd94bb8d26b412" if actual_vendor_pin == PS5_NS2_LICHII_AM_2_PIN else "68acadcd14d23135fd02df0a0e508c668917168c" if actual_vendor_pin == PS5_NS2_LICHII_AM_PIN else "e125210acec0eaef51c6c038d200cc9c12981ace" if actual_vendor_pin == PS5_NS2_LICHII_ZEROED_PIN else "c1cbb8a3ca0b7231e260fdb5e9f6a1c7964097ab" if actual_vendor_pin == PS5_NS2_NUP_IPC_PIN else "e21b2c70c00c50fc7d682150cb62e87fe856306c" if actual_vendor_pin == PS5_NS2_SELF_CONTROLLER_2400_PIN else "9e28e5b83cf9c0f4086a33d6838904353a8fd541"), ("FC27 prewarm vendor tree drift", new_tree)
    source_path = V / "encore-active/eden-vulkan/vk_pipeline_cache_cost.cpp"
    raw = source_path.read_bytes()
    current_blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
    assert current_blob == "79660c5cc4ff046f24e7ffa50ab066a86857698c", current_blob
    assert raw.count(b"constexpr size_t kRecentPrewarmPipelines = 128;") == 1
    REVIEWED_PINS.add(PS5_FC27_RECENT_PREWARM_PIN)
    selected = "b6b9e98e0dd16c4702f21f2e0b5e322126abeecb"

PS5_FC27_NVDRV_EXIT_PIN = "b6b9e98e0dd16c4702f21f2e0b5e322126abeecb"
PS5_FC27_NVDRV_EXIT_BLOBS = {
    "encore-active/ns2-runtime/process/core/core.cpp": "0110907a727b5d0ed15286298f851b59b30f1eb6",
    "tests/shutdown_teardown_lifetime_source.py": "6f3ff15f43b456ea79ba8f1dc275b690c1e11606",
    "tests/shutdown_general_channel_lifetime_source.py": "4e25852f84f9bc8e73454ef6ac1bac4d9270ac3a",
}
if actual_vendor_pin in {PS5_FC27_NVDRV_EXIT_PIN, PS5_FC27_RECENT_PREWARM_PIN, PS5_NS2_SELF_CONTROLLER_2400_PIN, PS5_NS2_NUP_IPC_PIN, PS5_NS2_LICHII_ZEROED_PIN, PS5_NS2_LICHII_AM_PIN, PS5_NS2_LICHII_AM_2_PIN, PS5_NS2_DECRYPTED_FORMATS_PIN}:
    assert selected == PS5_FC27_NVDRV_EXIT_PIN
    actual_tree = subprocess.check_output(
        ["git", "-C", str(V), "rev-parse", "HEAD^{tree}"], text=True).strip()
    assert actual_tree == ("e1e3fa4878d6203a51c7aa6ec93e09f81a175cdf" if actual_vendor_pin == PS5_NS2_DECRYPTED_FORMATS_PIN else "805d74f7ccf0ddf060782615d2bd94bb8d26b412" if actual_vendor_pin == PS5_NS2_LICHII_AM_2_PIN else "68acadcd14d23135fd02df0a0e508c668917168c" if actual_vendor_pin == PS5_NS2_LICHII_AM_PIN else "e125210acec0eaef51c6c038d200cc9c12981ace" if actual_vendor_pin == PS5_NS2_LICHII_ZEROED_PIN else "c1cbb8a3ca0b7231e260fdb5e9f6a1c7964097ab" if actual_vendor_pin == PS5_NS2_NUP_IPC_PIN else "e21b2c70c00c50fc7d682150cb62e87fe856306c" if actual_vendor_pin == PS5_NS2_SELF_CONTROLLER_2400_PIN else "9e28e5b83cf9c0f4086a33d6838904353a8fd541" if actual_vendor_pin == PS5_FC27_RECENT_PREWARM_PIN else "067c72d30a71a79faefd1ad14876e2a46f02755c"), actual_tree
    active_nvdrv_blobs = ({**PS5_FC27_NVDRV_EXIT_BLOBS, **{
        "encore-active/ns2-runtime/process/core/core.cpp": "a2721a630b8b32222ff586ea2db19ee726d4d5b9",
        "tests/shutdown_general_channel_lifetime_source.py": "4bb0ef388211b1c9110afce55ef80983e5050782",
        "tests/shutdown_teardown_lifetime_source.py": "e40deaae0b1f3aab6a5a12f7978be470b3ee0463",
    }} if actual_vendor_pin in {PS5_NS2_NUP_IPC_PIN, PS5_NS2_LICHII_ZEROED_PIN, PS5_NS2_LICHII_AM_PIN, PS5_NS2_LICHII_AM_2_PIN, PS5_NS2_DECRYPTED_FORMATS_PIN} else PS5_FC27_NVDRV_EXIT_BLOBS)
    for path, expected_blob in active_nvdrv_blobs.items():
        raw = (V / path).read_bytes()
        actual_blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        assert actual_blob == expected_blob, ("NVDRV exit selected source drift", path, actual_blob)
    REVIEWED_PINS.add(PS5_FC27_NVDRV_EXIT_PIN)
    REVIEWED_PINS.add("fcd62408fdbc33af01a4caebc8fd44c8500b628f")
    # Preserve the exact predecessor's existing qualifications and pin graph;
    # only the above three maintained owners differ.
    selected = "fcd62408fdbc33af01a4caebc8fd44c8500b628f"
    gitlink_vendor_pin = "4354add020afac574198f63d87167f3022bff9c6"
    shipping_vendor_pin = "4354add020afac574198f63d87167f3022bff9c6"

# OunceVK configures native 3D channels with H:0x1F {graphics=0, compute=2}
# before the first H:0x1B submit. NVIDIA defines compute bit1 as CTA.
# Seal exactly the active NVGPU owner/header and focused source contract.
NS2_PREEMPTION_CTA_PIN = "d31aa01bdfa87165a272473c385040723bf2c1f6"
NS2_PREEMPTION_CTA_BLOBS = {
    "encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/nvhost_gpu.cpp":
        "8a8ff1fe64b46bad3280abaa25405cb78346195f",
    "encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/nvhost_gpu.h":
        "da7e7347162d4ff86abebb2c4d8aca9db7d1be37",
    "tests/ns2_gpu_identity_mapping_source.py":
        "427b5fb7994ef320ba082ba6555b150f216f6f75",
}
NS2_PREEMPTION_CTA_TEST_FIX_PIN = "20cb62f1be572c8063ce4162d3227c8784a1e5ff"
NS2_PREEMPTION_CTA_TEST_FIX_BLOBS = {
    **NS2_PREEMPTION_CTA_BLOBS,
    "tests/ns2_gpu_identity_mapping_source.py":
        "069778748d4be07c72859cd28e280cecbcc36ef4",
}
# Nintendo/Switch channel error notifier successor. The final active owner
# follows Switch semantics: H:0x0C stores internal state (no Linux dma-buf),
# H:0x16 exposes no_error/current details, and H:0x17 returns the 16-byte
# notification with status 0xffff.
NS2_CHANNEL_ERROR_PIN = "19a62450fe8eb2fd3c28a4e940ed412beb9dc7ba"
NS2_CHANNEL_ERROR_BLOBS = {
    "encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/nvhost_gpu.cpp":
        "4810a41d584fb74612c8160c3f06a4c717f7d5f8",
    "encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/nvhost_gpu.h":
        "b0f57cbab6c801a201ac389a16beb9bdb59c4e54",
    "tests/ns2_gpu_identity_mapping_source.py":
        "d2e7e0341957a5ce830afe665bf074083977c956",
}
# Native H:0x1B reply successor. Switch documents submit flags as input;
# preserve the accepted native value while Maxwell keeps zero-on-return.
NS2_GPFIFO_FLAGS_PIN = "76a225552c296686cd1022584d73decd46767f75"
NS2_GPFIFO_FLAGS_BLOBS = {
    "encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/nvhost_gpu.cpp":
        "d5693b7377db357fbca342fe4c1276bb9a2375f5",
    "encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/nvhost_gpu.h":
        "b0f57cbab6c801a201ac389a16beb9bdb59c4e54",
    "tests/ns2_gpu_identity_mapping_source.py":
        "d2e7e0341957a5ce830afe665bf074083977c956",
    "tests/p0_ns2_gpfifo_preimpl_trace_source.py":
        "dd4055ab815a9f5ab8d81e3d14608890dbd4d7a1",
}
# Ounce's S2 H:0x12 successor. The 16-byte input is exactly
# {cmd,event_id,u64 zero}; the observed P0 path enables QueryEvent id 2.
NS2_CHANNEL_EVENT_PIN = "205c6a3572955c3d8002f5faca68d6ce1359817c"
NS2_CHANNEL_EVENT_BLOBS = {
    **NS2_GPFIFO_FLAGS_BLOBS,
    "encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/nvhost_gpu.cpp":
        "a96d2ff1637381240fbe83087a9d63842eb4cad3",
    "encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/nvhost_gpu.h":
        "001508fb9b31c91e0388d5c085329ea06ac807ff",
    "tests/ns2_gpu_identity_mapping_source.py":
        "fe85d136c6c8f2fbea00c6809ab48241f57b7e38",
}
# Current P0 successor over the already-reviewed 205c6a35 graph. It adds
# libounce HIPC MOVE worker/event replies, the exact 72-byte VM user-range
# table, real channel/TSG enable-disable state, and Ampere runnable-on-bind.
NS2_P0_BOOTSTRAP_PIN = "bfb9d4da9c0f3811924738311fc2c6056e0e4dcb"
NS2_P0_BOOTSTRAP_BLOBS = {
    "encore-active/ns2-runtime/gpu_session/core/hle/service/am/service/gpu_session.cpp":
        "09cbecdeef852a7e673025ff026881a88a6e490e",
    "tests/ns2_gpu_partition_new_sdk_source.py":
        "7306d167dc8f240b2a05818ce0e5fbbc0f91b114",
    "encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/nvhost_gpu.cpp":
        "a79e3ebd9e7a38f063bc2ab20da82ac5d7577b79",
    "encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/nvhost_gpu.h":
        "b7c8a75f283dcf2dc055e684bdde3e9dbee52303",
    "sources/eden/src/core/hle/service/nvdrv/devices/nvdevice.h":
        "fcf6d9a473a73d8d620c257c3a34e03729a9e616",
    "sources/eden/src/core/hle/service/nvdrv/devices/nx2_stub_device.h":
        "ccc0647e3b76a40e8022a6da85d820fdd47820f8",
    "sources/eden/src/core/hle/service/nvdrv/nvdrv.cpp":
        "a48e0ba56487374753c679e5637a26e0d3a0ab2a",
    "tests/ns2_gpu_identity_mapping_source.py":
        "0f158e58fc4a5b1f5e511327059a5e46fbcc77a4",
    "tests/ns2_nvhost_unknown_node_fallback_source.py":
        "bbaa5b78612aaae58b682253bb57ddc50f350695",
}
# P0 successor over bfb9d4da9c0f3811924738311fc2c6056e0e4dcb: exact native deferred GPFIFO state,
# GSV child MOVE descriptors and host-OOM rollback for owned transfer refs.
# Only six files changed. Replay all prior receipts for unchanged owners.
NS2_GSV_MOVE_OWNERS_PIN = "265609006ea8d76d971cc49af37bac23890ca4f5"
NS2_GSV_MOVE_OWNERS_BLOBS = {
    "encore-active/ns2-runtime/gpu_session/core/hle/service/am/service/gpu_session.cpp":
        "2b8c0f499e714bb684e33f336eac45ae21f55bd7",
    "encore-active/ns2-runtime/graphics_supervisor/core/hle/service/am/service/graphics_supervisor.cpp":
        "909f5cf912fdcce09c5b8f67274db36b7f65b07b",
    "encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/nvhost_gpu.cpp":
        "34431bff90d835fe5de7f647526e8354746eb4e3",
    "tests/ns2_gpu_identity_mapping_source.py":
        "ec6682c0131634ba10e48a201a47768b9437e41a",
    "tests/ns2_gpu_partition_new_sdk_source.py":
        "6d47278bfc205f0aaed5c3d916ad2f2dc29b0481",
    "tests/ns2_syncpt_bootstrap_source.py":
        "366b0a6bd75c2fde26bcc58c3a22f986fb7a99f3",
}
# Native NVGPU ENABLE and TSG ENABLE may precede allocation but cannot
# create a runnable GPFIFO by themselves. This successor only changes three
# active NVDRV owner/host-contract blobs and leaves all GSV/FC27 owners intact.
NS2_GPFIFO_ALLOC_GUARD_PIN = "d32b4280fe6737e1da3b56ed47409422500c756f"
NS2_GPFIFO_ALLOC_GUARD_BLOBS = {
    "encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/nvhost_gpu.h":
        "0e45617307506f0171d058944a3bbc32327e6132",
    "encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/nvhost_gpu.cpp":
        "7b941c9d63b5c89efed6181eea380f36ffc12e38",
    "tests/ns2_gpu_identity_mapping_source.py":
        "8a17814bcf4da34b2cbc32383b1b52bcf15d1c9f",
}
# TIPC session handles for real NS2 video decoding must be MOVE. This
# successor changes only the selected graphics supervisor owner and its
# existing source contract; preserve all earlier NVDRV/FC27 receipts.
NS2_DECODER_SESSION_MOVE_PIN = "1e1230f882ac6167ca0e6999875f07971b77985c"
NS2_DECODER_SESSION_MOVE_BLOBS = {
    "encore-active/ns2-runtime/graphics_supervisor/core/hle/service/am/service/graphics_supervisor.cpp":
        "fcf5bad66857cb10f528acddca9453db93079c65",
    "tests/ns2_syncpt_bootstrap_source.py":
        "af90eaec03e8f86c0519b9665983f7d400f33101",
}
# The real native ALLOC_GPFIFO_EX[2] owner must not publish an empty
# or overflowed ring. Legacy input accepts non-power-of-two sizes, unlike
# CHANNEL_SETUP_BIND. Preserve the exact predecessor receipts.
NS2_LEGACY_GPFIFO_ALLOC_PIN = "dd4127535a60ff1b22700edac24ca5a5f7d4fac2"
NS2_LEGACY_GPFIFO_ALLOC_BLOBS = {
    "encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/nvhost_gpu.cpp":
        "5a4c06e22706bde2f6d659287c5a24837e2503df",
    "encore-active/ns2-runtime/hle/core/hle/service/nvdrv/devices/native_gpu_submission.h":
        "230561aa034822b629eb6da6cb532dc4e58bf29c",
    "tests/ns2_gpu_identity_mapping_source.py":
        "a37f80b7966585fb0367a422cb2b733125f9d723",
}
# Lichii 46c3ee5010 / upstream 8799a851: keep the hot GPFIFO ioctl
# header lists in bounded inline storage and avoid zero-filling command headers
# that are immediately overwritten. Only the selected native submit wrappers
# opt in; all other ioctl wrappers retain InputCapacity=0.
NS2_GPFIFO_INLINE_PIN = "b1917364f678ba469c4d817f663d10ca5be5c0c3"
NS2_GPFIFO_INLINE_BLOBS = {
    "encore-active/eden-core/src/core/hle/service/nvdrv/devices/ioctl_serialization.h":
        "fb508e19110012589de3032fe257236032f098e4",
    "encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/nvhost_gpu.cpp":
        "8613ca2a7437b0e1e8f091ae6ca6c45f9dcbf141",
    "tests/ns2_gpu_identity_mapping_source.py":
        "55e08f386f4a1bdf45834072b0c8d3e8dd12d781",
}
# Lichii/MKW observed 214 generation replacement: the title can grow a
# sparse region at the exact same start VA without issuing 215 first.
NS2_MKW_SPARSE_REPLACE_PIN = "bc44094d78d0bba088ca0b48f37e9a4c38a9fbc5"
NS2_MKW_SPARSE_REPLACE_BLOBS = {
    "encore-active/ns2-runtime/hle/core/hle/service/am/service/gpu_worker_protocol.h":
        "7d3946559e9535a0451d459caba4434d7ace6c25",
    "encore-active/ns2-runtime/gpu_session/core/hle/service/am/service/gpu_worker.cpp":
        "978bedba80952994bc7783016085ee860ee93386",
    "tests/ns2_gpu_identity_mapping_source.py":
        "da75b3dcf00abaaf4d014fbe61c4bd62b486d5b6",
}
# Native NS2 GSV 214: a mid-batch GMMU OOM can retain partial GPU
# PTEs and poison the address space. Freeing its CPU alias/NvMap owner on
# this error is a GPU use-after-free; quarantine only the poisoned case.
NS2_DENSE_GMMU_POISON_PIN = "ed03e467016f5afbcb722c54af374d6916ccd6a0"
NS2_DENSE_GMMU_POISON_BLOBS = {
    "encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.h":
        "e921b3d0e98ab6d2a845297e4fadf61e62ca3b70",
    "encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.cpp":
        "a4925ce958cf38537e3db8f073c60f73e716f772",
    "encore-active/ns2-runtime/gpu_session/core/hle/service/am/service/gpu_worker.cpp":
        "01a11f01f7c3431bde919b4d70d940d8e184b7fc",
    "tests/ns2_gpu_identity_mapping_source.py":
        "7cd2e739532af7395fc92c5c7dadf43bf3436bab",
}
# GPU worker 214 poisoned AS: NvCore CloseSession -> UnmapAllHandles also
# forcibly drops the final NVMap duplicate. Retain the worker session until
# process teardown in the rare poisoned path; normal 214 error cleanup stays.
NS2_POISONED_DENSE_SESSION_PIN = "b8396c6483aa8278bd75b6757aed3bb5a9206e52"
NS2_POISONED_DENSE_SESSION_BLOBS = {
    "encore-active/ns2-runtime/gpu_session/core/hle/service/am/service/gpu_worker.h":
        "933a8c2ff4971420bb7a6160825c5fd0fa4dc9d3",
    "encore-active/ns2-runtime/gpu_session/core/hle/service/am/service/gpu_worker.cpp":
        "bafd64ee8d5491a4e92b3a37487b74b1bd4a8fe2",
    "tests/ns2_gpu_identity_mapping_source.py":
        "b37b3f0329e3e5b0cadf3bdde1578bfbc6375f2c",
}
# Reviewed NS2 GSV 215/216 error: prevent destructor FreeHandle/CloseSession
# on a GMMU with partial PTE writes. Keep every older receipt unchanged.
NS2_POISONED_TEARDOWN_PIN = "a8c9170802811e7bb19345a461c3ae8dc72c27be"
NS2_POISONED_TEARDOWN_BLOBS = {
    "encore-active/ns2-runtime/gpu_session/core/hle/service/am/service/gpu_worker.cpp":
        "15f06d05601458769dfe17124068edca59835793",
    "tests/ns2_gpu_identity_mapping_source.py":
        "a446b8f18209f54e551302521cfcc6c4fe372ff0",
}
NS2_POISONED_TEARDOWN_ACTIVE = actual_vendor_pin == NS2_POISONED_TEARDOWN_PIN
if selected == NS2_POISONED_TEARDOWN_PIN:
    for relative, expected in NS2_POISONED_TEARDOWN_BLOBS.items():
        raw = (V / relative).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        assert actual == expected, ("NS2 GSV 215/216 teardown source drift", relative, actual)
    selected = NS2_POISONED_DENSE_SESSION_PIN
    gitlink_vendor_pin = NS2_POISONED_DENSE_SESSION_PIN
    shipping_vendor_pin = NS2_POISONED_DENSE_SESSION_PIN

def ns2_poisoned_teardown_receipt(relative, previous):
    if NS2_POISONED_TEARDOWN_ACTIVE and relative in NS2_POISONED_TEARDOWN_BLOBS:
        return NS2_POISONED_TEARDOWN_BLOBS[relative]
    return previous

NS2_POISONED_DENSE_SESSION_ACTIVE = actual_vendor_pin in {
    NS2_POISONED_DENSE_SESSION_PIN, NS2_POISONED_TEARDOWN_PIN,
}
if selected == NS2_POISONED_DENSE_SESSION_PIN:
    for relative, expected in NS2_POISONED_DENSE_SESSION_BLOBS.items():
        raw = (V / relative).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        assert actual == ns2_poisoned_teardown_receipt(relative, expected), (
            "NS2 poisoned dense NVDRV session source drift", relative, actual)
    selected = NS2_DENSE_GMMU_POISON_PIN
    gitlink_vendor_pin = NS2_DENSE_GMMU_POISON_PIN
    shipping_vendor_pin = NS2_DENSE_GMMU_POISON_PIN

def ns2_poisoned_dense_session_receipt(relative, previous):
    if NS2_POISONED_TEARDOWN_ACTIVE and relative in NS2_POISONED_TEARDOWN_BLOBS:
        return NS2_POISONED_TEARDOWN_BLOBS[relative]
    if NS2_POISONED_DENSE_SESSION_ACTIVE and relative in NS2_POISONED_DENSE_SESSION_BLOBS:
        return NS2_POISONED_DENSE_SESSION_BLOBS[relative]
    return previous

NS2_DENSE_GMMU_POISON_ACTIVE = actual_vendor_pin in {
    NS2_DENSE_GMMU_POISON_PIN, NS2_POISONED_DENSE_SESSION_PIN, NS2_POISONED_TEARDOWN_PIN, NS2_POISONED_DENSE_SESSION_PIN, NS2_POISONED_TEARDOWN_PIN,
}
if selected == NS2_DENSE_GMMU_POISON_PIN:
    for relative, expected in NS2_DENSE_GMMU_POISON_BLOBS.items():
        raw = (V / relative).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        assert actual == ns2_poisoned_dense_session_receipt(relative, expected), (
            "NS2 poisoned GMMU sparse backing source drift", relative, actual)
    selected = NS2_MKW_SPARSE_REPLACE_PIN
    gitlink_vendor_pin = NS2_MKW_SPARSE_REPLACE_PIN
    shipping_vendor_pin = NS2_MKW_SPARSE_REPLACE_PIN

def ns2_dense_gmmu_poison_receipt(relative, previous):
    if NS2_POISONED_TEARDOWN_ACTIVE and relative in NS2_POISONED_TEARDOWN_BLOBS:
        return NS2_POISONED_TEARDOWN_BLOBS[relative]
    if NS2_POISONED_DENSE_SESSION_ACTIVE and relative in NS2_POISONED_DENSE_SESSION_BLOBS:
        return NS2_POISONED_DENSE_SESSION_BLOBS[relative]
    if NS2_DENSE_GMMU_POISON_ACTIVE and relative in NS2_DENSE_GMMU_POISON_BLOBS:
        return NS2_DENSE_GMMU_POISON_BLOBS[relative]
    return previous

NS2_MKW_SPARSE_REPLACE_ACTIVE = actual_vendor_pin in {
    NS2_MKW_SPARSE_REPLACE_PIN, NS2_DENSE_GMMU_POISON_PIN, NS2_POISONED_DENSE_SESSION_PIN, NS2_POISONED_TEARDOWN_PIN,
}
if selected == NS2_MKW_SPARSE_REPLACE_PIN:
    for relative, expected in NS2_MKW_SPARSE_REPLACE_BLOBS.items():
        raw = (V / relative).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        assert actual == ns2_dense_gmmu_poison_receipt(relative, expected), (
            "NS2 MKW sparse generation source drift", relative, actual)
    selected = NS2_GPFIFO_INLINE_PIN
    gitlink_vendor_pin = NS2_GPFIFO_INLINE_PIN
    shipping_vendor_pin = NS2_GPFIFO_INLINE_PIN

def ns2_mkw_sparse_receipt(relative, previous):
    if NS2_POISONED_TEARDOWN_ACTIVE and relative in NS2_POISONED_TEARDOWN_BLOBS:
        return NS2_POISONED_TEARDOWN_BLOBS[relative]
    if NS2_POISONED_DENSE_SESSION_ACTIVE and relative in NS2_POISONED_DENSE_SESSION_BLOBS:
        return NS2_POISONED_DENSE_SESSION_BLOBS[relative]
    if NS2_DENSE_GMMU_POISON_ACTIVE and relative in NS2_DENSE_GMMU_POISON_BLOBS:
        return NS2_DENSE_GMMU_POISON_BLOBS[relative]
    if NS2_MKW_SPARSE_REPLACE_ACTIVE and relative in NS2_MKW_SPARSE_REPLACE_BLOBS:
        return NS2_MKW_SPARSE_REPLACE_BLOBS[relative]
    return previous

NS2_GPFIFO_INLINE_ACTIVE = actual_vendor_pin in {
    NS2_GPFIFO_INLINE_PIN, NS2_MKW_SPARSE_REPLACE_PIN, NS2_DENSE_GMMU_POISON_PIN, NS2_POISONED_DENSE_SESSION_PIN, NS2_POISONED_TEARDOWN_PIN,
}
if selected == NS2_GPFIFO_INLINE_PIN:
    for relative, expected in NS2_GPFIFO_INLINE_BLOBS.items():
        raw = (V / relative).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        assert actual == ns2_mkw_sparse_receipt(relative, expected), (
            "NS2 GPFIFO inline-storage source drift", relative, actual)
    selected = NS2_LEGACY_GPFIFO_ALLOC_PIN
    gitlink_vendor_pin = NS2_LEGACY_GPFIFO_ALLOC_PIN
    shipping_vendor_pin = NS2_LEGACY_GPFIFO_ALLOC_PIN

NS2_LEGACY_GPFIFO_ALLOC_ACTIVE = actual_vendor_pin in {
    NS2_LEGACY_GPFIFO_ALLOC_PIN, NS2_GPFIFO_INLINE_PIN, NS2_MKW_SPARSE_REPLACE_PIN, NS2_DENSE_GMMU_POISON_PIN, NS2_POISONED_DENSE_SESSION_PIN, NS2_POISONED_TEARDOWN_PIN,
}
if selected == NS2_LEGACY_GPFIFO_ALLOC_PIN:
    for relative, expected in NS2_LEGACY_GPFIFO_ALLOC_BLOBS.items():
        raw = (V / relative).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        expected_current = (NS2_GPFIFO_INLINE_BLOBS.get(relative, expected)
                            if NS2_GPFIFO_INLINE_ACTIVE else expected)
        assert actual == ns2_mkw_sparse_receipt(relative, expected_current), (
            "NS2 GPFIFO legacy allocation source drift", relative, actual)
    selected = NS2_DECODER_SESSION_MOVE_PIN
    gitlink_vendor_pin = NS2_DECODER_SESSION_MOVE_PIN
    shipping_vendor_pin = NS2_DECODER_SESSION_MOVE_PIN

NS2_DECODER_SESSION_MOVE_ACTIVE = actual_vendor_pin in {
    NS2_DECODER_SESSION_MOVE_PIN, NS2_LEGACY_GPFIFO_ALLOC_PIN,
    NS2_GPFIFO_INLINE_PIN, NS2_MKW_SPARSE_REPLACE_PIN, NS2_DENSE_GMMU_POISON_PIN, NS2_POISONED_DENSE_SESSION_PIN, NS2_POISONED_TEARDOWN_PIN,
}
if selected == NS2_DECODER_SESSION_MOVE_PIN:
    for relative, expected in NS2_DECODER_SESSION_MOVE_BLOBS.items():
        raw = (V / relative).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        assert actual == expected, ("NS2 video decoder MOVE session source drift", relative, actual)
    selected = NS2_GPFIFO_ALLOC_GUARD_PIN
    gitlink_vendor_pin = NS2_GPFIFO_ALLOC_GUARD_PIN
    shipping_vendor_pin = NS2_GPFIFO_ALLOC_GUARD_PIN

NS2_GPFIFO_ALLOC_GUARD_ACTIVE = actual_vendor_pin in {
    NS2_GPFIFO_ALLOC_GUARD_PIN, NS2_DECODER_SESSION_MOVE_PIN,
    NS2_LEGACY_GPFIFO_ALLOC_PIN, NS2_GPFIFO_INLINE_PIN, NS2_MKW_SPARSE_REPLACE_PIN, NS2_DENSE_GMMU_POISON_PIN, NS2_POISONED_DENSE_SESSION_PIN, NS2_POISONED_TEARDOWN_PIN,
}
if selected == NS2_GPFIFO_ALLOC_GUARD_PIN:
    for relative, expected in NS2_GPFIFO_ALLOC_GUARD_BLOBS.items():
        raw = (V / relative).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        expected_current = (
            NS2_LEGACY_GPFIFO_ALLOC_BLOBS.get(relative, expected)
            if NS2_LEGACY_GPFIFO_ALLOC_ACTIVE else expected)
        if NS2_GPFIFO_INLINE_ACTIVE:
            expected_current = NS2_GPFIFO_INLINE_BLOBS.get(relative, expected_current)
        expected_current = ns2_mkw_sparse_receipt(relative, expected_current)
        assert actual == expected_current, (
            "NS2 native GPFIFO allocation gate source drift", relative, actual)
    selected = NS2_GSV_MOVE_OWNERS_PIN
    gitlink_vendor_pin = NS2_GSV_MOVE_OWNERS_PIN
    shipping_vendor_pin = NS2_GSV_MOVE_OWNERS_PIN

NS2_GSV_MOVE_OWNERS_ACTIVE = actual_vendor_pin in {
    NS2_GSV_MOVE_OWNERS_PIN, NS2_GPFIFO_ALLOC_GUARD_PIN,
    NS2_DECODER_SESSION_MOVE_PIN, NS2_LEGACY_GPFIFO_ALLOC_PIN,
    NS2_GPFIFO_INLINE_PIN, NS2_MKW_SPARSE_REPLACE_PIN, NS2_DENSE_GMMU_POISON_PIN, NS2_POISONED_DENSE_SESSION_PIN, NS2_POISONED_TEARDOWN_PIN,
}
def ns2_latest_gsv_receipt(relative, previous):
    if NS2_POISONED_TEARDOWN_ACTIVE and relative in NS2_POISONED_TEARDOWN_BLOBS:
        return NS2_POISONED_TEARDOWN_BLOBS[relative]
    if NS2_POISONED_DENSE_SESSION_ACTIVE and relative in NS2_POISONED_DENSE_SESSION_BLOBS:
        return NS2_POISONED_DENSE_SESSION_BLOBS[relative]
    if NS2_DENSE_GMMU_POISON_ACTIVE and relative in NS2_DENSE_GMMU_POISON_BLOBS:
        return NS2_DENSE_GMMU_POISON_BLOBS[relative]
    if NS2_MKW_SPARSE_REPLACE_ACTIVE and relative in NS2_MKW_SPARSE_REPLACE_BLOBS:
        return NS2_MKW_SPARSE_REPLACE_BLOBS[relative]
    if NS2_GPFIFO_INLINE_ACTIVE and relative in NS2_GPFIFO_INLINE_BLOBS:
        return NS2_GPFIFO_INLINE_BLOBS[relative]
    if NS2_LEGACY_GPFIFO_ALLOC_ACTIVE and relative in NS2_LEGACY_GPFIFO_ALLOC_BLOBS:
        return NS2_LEGACY_GPFIFO_ALLOC_BLOBS[relative]
    if NS2_DECODER_SESSION_MOVE_ACTIVE and relative in NS2_DECODER_SESSION_MOVE_BLOBS:
        return NS2_DECODER_SESSION_MOVE_BLOBS[relative]
    if NS2_GPFIFO_ALLOC_GUARD_ACTIVE and relative in NS2_GPFIFO_ALLOC_GUARD_BLOBS:
        return NS2_GPFIFO_ALLOC_GUARD_BLOBS[relative]
    return (NS2_GSV_MOVE_OWNERS_BLOBS.get(relative, previous)
            if NS2_GSV_MOVE_OWNERS_ACTIVE else previous)
if selected == NS2_GSV_MOVE_OWNERS_PIN:
    for relative, expected in NS2_GSV_MOVE_OWNERS_BLOBS.items():
        raw = (V / relative).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        assert actual == ns2_latest_gsv_receipt(relative, expected), (
            "NS2 GSV/GPFIFO MOVE lifetime source drift", relative, actual)
    selected = NS2_P0_BOOTSTRAP_PIN
    gitlink_vendor_pin = NS2_P0_BOOTSTRAP_PIN
    shipping_vendor_pin = NS2_P0_BOOTSTRAP_PIN

NS2_P0_BOOTSTRAP_ACTIVE = actual_vendor_pin in {
    NS2_P0_BOOTSTRAP_PIN, NS2_GSV_MOVE_OWNERS_PIN, NS2_GPFIFO_ALLOC_GUARD_PIN,
    NS2_DECODER_SESSION_MOVE_PIN, NS2_LEGACY_GPFIFO_ALLOC_PIN,
    NS2_GPFIFO_INLINE_PIN, NS2_MKW_SPARSE_REPLACE_PIN, NS2_DENSE_GMMU_POISON_PIN, NS2_POISONED_DENSE_SESSION_PIN, NS2_POISONED_TEARDOWN_PIN,
}
if selected == NS2_P0_BOOTSTRAP_PIN:
    for relative, expected in NS2_P0_BOOTSTRAP_BLOBS.items():
        raw = (V / relative).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        assert actual == ns2_latest_gsv_receipt(relative, expected), (
            "NS2 current P0 bootstrap source drift", relative, actual)
    # From here, replay the exact 205c6a35 predecessor graph. Keep
    # actual_vendor_pin untouched for the final gitlink identity assertion.
    selected = NS2_CHANNEL_EVENT_PIN
    gitlink_vendor_pin = NS2_CHANNEL_EVENT_PIN
    shipping_vendor_pin = NS2_CHANNEL_EVENT_PIN

NS2_CHANNEL_EVENT_ACTIVE = gitlink_vendor_pin == NS2_CHANNEL_EVENT_PIN
NS2_GPFIFO_FLAGS_ACTIVE = gitlink_vendor_pin in {
    NS2_GPFIFO_FLAGS_PIN, NS2_CHANNEL_EVENT_PIN,
}
NS2_CHANNEL_ERROR_ACTIVE = gitlink_vendor_pin in {
    NS2_CHANNEL_ERROR_PIN, NS2_GPFIFO_FLAGS_PIN, NS2_CHANNEL_EVENT_PIN,
}
NS2_PREEMPTION_CTA_ACTIVE = gitlink_vendor_pin in {
    NS2_PREEMPTION_CTA_PIN, NS2_PREEMPTION_CTA_TEST_FIX_PIN,
    NS2_CHANNEL_ERROR_PIN, NS2_GPFIFO_FLAGS_PIN, NS2_CHANNEL_EVENT_PIN,
}

def ns2_preemption_receipt(relative, previous):
    if NS2_POISONED_TEARDOWN_ACTIVE and relative in NS2_POISONED_TEARDOWN_BLOBS:
        return NS2_POISONED_TEARDOWN_BLOBS[relative]
    if NS2_POISONED_DENSE_SESSION_ACTIVE and relative in NS2_POISONED_DENSE_SESSION_BLOBS:
        return NS2_POISONED_DENSE_SESSION_BLOBS[relative]
    if NS2_DENSE_GMMU_POISON_ACTIVE and relative in NS2_DENSE_GMMU_POISON_BLOBS:
        return NS2_DENSE_GMMU_POISON_BLOBS[relative]
    if NS2_MKW_SPARSE_REPLACE_ACTIVE and relative in NS2_MKW_SPARSE_REPLACE_BLOBS:
        return NS2_MKW_SPARSE_REPLACE_BLOBS[relative]
    if NS2_GPFIFO_INLINE_ACTIVE and relative in NS2_GPFIFO_INLINE_BLOBS:
        return NS2_GPFIFO_INLINE_BLOBS[relative]
    if NS2_LEGACY_GPFIFO_ALLOC_ACTIVE and relative in NS2_LEGACY_GPFIFO_ALLOC_BLOBS:
        return NS2_LEGACY_GPFIFO_ALLOC_BLOBS[relative]
    if NS2_DECODER_SESSION_MOVE_ACTIVE and relative in NS2_DECODER_SESSION_MOVE_BLOBS:
        return NS2_DECODER_SESSION_MOVE_BLOBS[relative]
    if NS2_GPFIFO_ALLOC_GUARD_ACTIVE and relative in NS2_GPFIFO_ALLOC_GUARD_BLOBS:
        return NS2_GPFIFO_ALLOC_GUARD_BLOBS[relative]
    if NS2_GSV_MOVE_OWNERS_ACTIVE and relative in NS2_GSV_MOVE_OWNERS_BLOBS:
        return NS2_GSV_MOVE_OWNERS_BLOBS[relative]
    if NS2_P0_BOOTSTRAP_ACTIVE and relative in NS2_P0_BOOTSTRAP_BLOBS:
        return NS2_P0_BOOTSTRAP_BLOBS[relative]
    if NS2_CHANNEL_EVENT_ACTIVE:
        return NS2_CHANNEL_EVENT_BLOBS.get(relative, previous)
    if NS2_GPFIFO_FLAGS_ACTIVE:
        return NS2_GPFIFO_FLAGS_BLOBS.get(relative, previous)
    if NS2_CHANNEL_ERROR_ACTIVE:
        return NS2_CHANNEL_ERROR_BLOBS.get(relative, previous)
    if gitlink_vendor_pin == NS2_PREEMPTION_CTA_TEST_FIX_PIN:
        return NS2_PREEMPTION_CTA_TEST_FIX_BLOBS.get(relative, previous)
    return (NS2_PREEMPTION_CTA_BLOBS.get(relative, previous)
            if NS2_PREEMPTION_CTA_ACTIVE else previous)

if selected == NS2_CHANNEL_EVENT_PIN:
    for relative, expected in NS2_CHANNEL_EVENT_BLOBS.items():
        raw = (V / relative).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        assert actual == ns2_preemption_receipt(relative, expected), (
            "NS2 native channel event-control source drift", relative, actual)
    selected = NS2_GPFIFO_FLAGS_PIN

if selected == NS2_GPFIFO_FLAGS_PIN:
    for relative, expected in NS2_GPFIFO_FLAGS_BLOBS.items():
        raw = (V / relative).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        assert actual == ns2_preemption_receipt(relative, expected), (
            "NS2 native GPFIFO2 reply-flags source drift", relative, actual)
    # Everything else is byte-identical to the reviewed Switch error-state pin.
    shipping_vendor_pin = NS2_CHANNEL_ERROR_PIN
    selected = NS2_CHANNEL_ERROR_PIN

if selected == NS2_CHANNEL_ERROR_PIN:
    for relative, expected in NS2_CHANNEL_ERROR_BLOBS.items():
        raw = (V / relative).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        assert actual == ns2_preemption_receipt(relative, expected), ("NS2 channel error-notifier source drift", relative, actual)
    selected = NS2_PREEMPTION_CTA_TEST_FIX_PIN

if selected == NS2_PREEMPTION_CTA_TEST_FIX_PIN:
    for relative, expected in NS2_PREEMPTION_CTA_TEST_FIX_BLOBS.items():
        raw = (V / relative).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        assert actual == ns2_preemption_receipt(relative, expected), (
            "NS2 CTA source-contract test-fix drift", relative, actual)
    selected = NS2_PREEMPTION_CTA_PIN

if selected == NS2_PREEMPTION_CTA_PIN:
    for relative, expected in NS2_PREEMPTION_CTA_BLOBS.items():
        raw = (V / relative).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        assert actual == ns2_preemption_receipt(relative, expected), ("NS2 native CTA preemption-policy source drift", relative, actual)
    selected = "1e513ae001669127538a346c7f390af55edd6712"

# SwitchBrew GSV 1001/1002 are video ENCODER commands. The earlier
# decoder aliases must not issue Success or create a decoder session.
# This successor changes only these three source/test blobs.
NS2_ENCODER_FAIL_CLOSED_PIN = "1e513ae001669127538a346c7f390af55edd6712"
# Preserve the authentic pinned identity; later historical replay rewrites
# gitlink_vendor_pin to c74, but must not drop these verified successor blobs.
NS2_ENCODER_FAIL_CLOSED_ACTIVE = gitlink_vendor_pin in {
    NS2_ENCODER_FAIL_CLOSED_PIN, NS2_PREEMPTION_CTA_PIN,
    NS2_PREEMPTION_CTA_TEST_FIX_PIN, NS2_CHANNEL_ERROR_PIN, NS2_GPFIFO_FLAGS_PIN,
    NS2_CHANNEL_EVENT_PIN,
}
NS2_ENCODER_FAIL_CLOSED_BLOBS = {
    "encore-active/ns2-runtime/graphics_supervisor/core/hle/service/am/service/graphics_supervisor.cpp": "6934cd5d46c172d029c65123b5d7f19ddafc4853",
    "encore-active/ns2-runtime/graphics_supervisor/core/hle/service/am/service/graphics_supervisor.h": "985cab1d56306096f7630da7f4d6a5b34c859431",
    "tests/ns2_syncpt_bootstrap_source.py": "0b96a52583af112c816b676fec40fca39d194e45"
}
def ns2_encoder_receipt(relative, previous):
    if NS2_POISONED_TEARDOWN_ACTIVE and relative in NS2_POISONED_TEARDOWN_BLOBS:
        return NS2_POISONED_TEARDOWN_BLOBS[relative]
    if NS2_POISONED_DENSE_SESSION_ACTIVE and relative in NS2_POISONED_DENSE_SESSION_BLOBS:
        return NS2_POISONED_DENSE_SESSION_BLOBS[relative]
    if NS2_DENSE_GMMU_POISON_ACTIVE and relative in NS2_DENSE_GMMU_POISON_BLOBS:
        return NS2_DENSE_GMMU_POISON_BLOBS[relative]
    if NS2_MKW_SPARSE_REPLACE_ACTIVE and relative in NS2_MKW_SPARSE_REPLACE_BLOBS:
        return NS2_MKW_SPARSE_REPLACE_BLOBS[relative]
    if NS2_GPFIFO_INLINE_ACTIVE and relative in NS2_GPFIFO_INLINE_BLOBS:
        return NS2_GPFIFO_INLINE_BLOBS[relative]
    if NS2_LEGACY_GPFIFO_ALLOC_ACTIVE and relative in NS2_LEGACY_GPFIFO_ALLOC_BLOBS:
        return NS2_LEGACY_GPFIFO_ALLOC_BLOBS[relative]
    if NS2_DECODER_SESSION_MOVE_ACTIVE and relative in NS2_DECODER_SESSION_MOVE_BLOBS:
        return NS2_DECODER_SESSION_MOVE_BLOBS[relative]
    if NS2_GPFIFO_ALLOC_GUARD_ACTIVE and relative in NS2_GPFIFO_ALLOC_GUARD_BLOBS:
        return NS2_GPFIFO_ALLOC_GUARD_BLOBS[relative]
    if NS2_GSV_MOVE_OWNERS_ACTIVE and relative in NS2_GSV_MOVE_OWNERS_BLOBS:
        return NS2_GSV_MOVE_OWNERS_BLOBS[relative]
    return (NS2_ENCODER_FAIL_CLOSED_BLOBS.get(relative, previous)
            if NS2_ENCODER_FAIL_CLOSED_ACTIVE else previous)

if selected == NS2_ENCODER_FAIL_CLOSED_PIN:
    for relative, expected in NS2_ENCODER_FAIL_CLOSED_BLOBS.items():
        raw = (V / relative).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        assert actual == ns2_preemption_receipt(relative, expected), ("NS2 encoder fail-closed source drift", relative, actual)
    # The TSG owner is unchanged from the immediately preceding pin.
    shipping_vendor_pin = "1f8a3bbaa7fc33118e63ebef829202d825475bfe"
    selected = shipping_vendor_pin

# Final known-TSG fail-closed successor. The final nx2 owner includes the
# validated pre-bind scheduling state/getter plus explicit NotImplemented
# routes for six known stateful/event/cache ioctls. Seal it, then replay 2d07.
if selected == "1f8a3bbaa7fc33118e63ebef829202d825475bfe":
    for relative, expected in (
        ("sources/eden/src/core/hle/service/nvdrv/devices/nx2_stub_device.h", "587ebbd2a129ab38e3c0ec49e2121eb1768bbaa4"),
        ("tests/ns2_nvhost_unknown_node_fallback_source.py", "abdf48b2423a0abdd3d2085c2f3ae9b3a93db9ea"),
    ):
        raw = (V / relative).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        assert actual == ns2_preemption_receipt(relative, expected), ("NS2 known TSG fail-closed source drift", relative, actual)
    selected = "2d07b5e65baf35c82d0b0e557617aefe730a10b1"

# Ounce TSG scheduling-state successor. Seal the final nx2 stub owner and
# its focused source receipt; all GSV/GPU owners are unchanged from 2d07.
if selected == "7baf9cc07c6aceee185032544d964f04a2fed108":
    for relative, expected in (
        ("sources/eden/src/core/hle/service/nvdrv/devices/nx2_stub_device.h", "f287b62c0e001af3d3262a6a253c076a0941b2f8"),
        ("tests/ns2_nvhost_unknown_node_fallback_source.py", "3094b555b32840f613c7567e10787c4f73c668e5"),
    ):
        raw = (V / relative).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        assert actual == ns2_preemption_receipt(relative, expected), ("NS2 Ounce TSG scheduling source drift", relative, actual)
    selected = "2d07b5e65baf35c82d0b0e557617aefe730a10b1"

# GSV TIPC 498 donated TransferMemory usage successor. The only changed
# live owners are the supervisor implementation/header and its existing
# focused bootstrap source receipt. Seal them before replaying 4e unchanged.
if selected == "2d07b5e65baf35c82d0b0e557617aefe730a10b1":
    for relative, expected in (
        ("encore-active/ns2-runtime/graphics_supervisor/core/hle/service/am/service/graphics_supervisor.cpp", "66b5bc32c9286ec2462edd09804a670691ac91d8"),
        ("encore-active/ns2-runtime/graphics_supervisor/core/hle/service/am/service/graphics_supervisor.h", "56e9ddf8b73d4db22559e73fe8d3506bdaa84a1c"),
        ("tests/ns2_syncpt_bootstrap_source.py", "08894a7985e96f4478501dd69aceb56b214b0306"),
    ):
        raw = (V / relative).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        assert actual == ns2_encoder_receipt(relative, expected), ("NS2 GSV 498 donated-memory source drift", relative, actual)
    selected = "4e6a966508e718d02526d4d220e112591536f28c"

# Switch 2 C0504821 response-ABI successor. Seal the active channel owner,
# header and focused source receipt, then replay the fail-closed nvhost pin.
if selected == "4e6a966508e718d02526d4d220e112591536f28c":
    for relative, expected in (
        ("encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/nvhost_gpu.h", "8b22d4e16ba0e3d0e73cc3af9faace2447d3fd9b"),
        ("encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/nvhost_gpu.cpp", "81bac0bb0c1be0be6ed0aca81931fc593b948044"),
        ("tests/p0_ns2_gpfifo_preimpl_trace_source.py", "d78aaea83009616131bcaf68bfb67fd12fe2e575"),
    ):
        raw = (V / relative).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        assert actual == ns2_preemption_receipt(relative, expected), ("NS2 ChannelSetupBind response ABI source drift", relative, actual)
    selected = ("546e1aa34d2ff183dd4c737f9da8fbf4a62be24e"
                if shipping_vendor_pin in {"7baf9cc07c6aceee185032544d964f04a2fed108", "1f8a3bbaa7fc33118e63ebef829202d825475bfe"}
                else "f65ccc439534ffd9ce0a307b23bd511b4e32857a")

# Unknown Switch 2 nvhost-node fail-closed successor. Keep device discovery
# compatible, but authenticate that generic ioctls no longer fabricate Success.
if selected == "f65ccc439534ffd9ce0a307b23bd511b4e32857a":
    for relative, expected in (
        ("sources/eden/src/core/hle/service/nvdrv/devices/nx2_stub_device.h", "24b515a59d2f965a8abfab36175cf71b864340fb"),
        ("tests/ns2_nvhost_unknown_node_fallback_source.py", "9904dd79d295d098ee7431eb31b9cc36e32a3b27"),
    ):
        raw = (V / relative).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        assert actual == ns2_preemption_receipt(relative, expected), ("NS2 unknown nvhost fail-closed source drift", relative, actual)
    selected = "546e1aa34d2ff183dd4c737f9da8fbf4a62be24e"

# Worker 209/210 successor: exact owned GPU address-space segment
# debug-label ABI/runtime and focused ownership receipt.
if selected == "546e1aa34d2ff183dd4c737f9da8fbf4a62be24e":
    for relative, expected in (
        ("encore-active/ns2-runtime/gpu_session/core/hle/service/am/service/gpu_worker.cpp", "ccccfb99af3ffd03ae1a3119b89c7121cc73ac91"),
        ("encore-active/ns2-runtime/gpu_session/core/hle/service/am/service/gpu_worker.h", "2aa6d526e7c876d11adc180f546935503be54a4a"),
        ("encore-active/ns2-runtime/hle/core/hle/service/am/service/gpu_memory_registration.h", "e6223aa74605e50aab30e1fd0a0bf8f3b75c4ecf"),
        ("tests/ns2_gpu_identity_mapping_source.py", "0572833e4e63c5fe7af728c66beea7df53e4219e"),
    ):
        raw = (V / relative).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        assert actual == ns2_preemption_receipt(relative, expected), ("NS2 GPU segment label source drift", relative, actual)
    selected = "bc6baf037ac3304d4ba81cf7589f7e52e8fa8ae0"

# Native ChannelSetupBind H:0x21 successor. The 80-byte ABI and
# kernel-mode-only admission are selected C++, not a universal success stub.
if selected == "bc6baf037ac3304d4ba81cf7589f7e52e8fa8ae0":
    for relative, expected in (
        ("encore-active/ns2-runtime/hle/core/hle/service/nvdrv/devices/native_gpu_submission.h", "9aa4b802c2245cad7b251fff3bc708a906db533d"),
        ("encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/nvhost_gpu.h", "af7df2ba70bbf16d3715257c8c3a2b471ed26227"),
        ("encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/nvhost_gpu.cpp", "24096d0848b560d5e7befe979ecaebd1dcc730ae"),
        ("tests/p0_ns2_gpfifo_preimpl_trace_source.py", "4e7a4fd77cd96ff650edfc74f6a841b266ca2152"),
    ):
        raw = (V / relative).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        # Current setup-bind successors were authenticated above. Replay this
        # predecessor contract with their exact current blob identities rather
        # than comparing a live checkout against the historical bc6 blobs.
        if shipping_vendor_pin in {"4e6a966508e718d02526d4d220e112591536f28c", "2d07b5e65baf35c82d0b0e557617aefe730a10b1", "7baf9cc07c6aceee185032544d964f04a2fed108", "1f8a3bbaa7fc33118e63ebef829202d825475bfe"}:
            expected = {
                "encore-active/ns2-runtime/hle/core/hle/service/nvdrv/devices/native_gpu_submission.h":
                    "9aa4b802c2245cad7b251fff3bc708a906db533d",
                "encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/nvhost_gpu.h":
                    "8b22d4e16ba0e3d0e73cc3af9faace2447d3fd9b",
                "encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/nvhost_gpu.cpp":
                    "81bac0bb0c1be0be6ed0aca81931fc593b948044",
                "tests/p0_ns2_gpfifo_preimpl_trace_source.py":
                    "d78aaea83009616131bcaf68bfb67fd12fe2e575",
            }[relative]
        assert actual == ns2_preemption_receipt(relative, expected), ("NS2 ChannelSetupBind source drift", relative, actual)
    selected = "0c4eafeb9f197e76a1f0bb06038ef9bbf2c7565d"

# Worker 172/173 successor: exact owned NVMap label metadata and its
# registration decoders/test. New labels are discarded on guest release.
if selected == "0c4eafeb9f197e76a1f0bb06038ef9bbf2c7565d":
    for relative, expected in (
        ("encore-active/ns2-runtime/gpu_session/core/hle/service/am/service/gpu_worker.cpp", "0a6c1b39483d8efcff0690f4f677d594863bf09e"),
        ("encore-active/ns2-runtime/gpu_session/core/hle/service/am/service/gpu_worker.h", "676f9f0391e73147f241fc0ece20e9f0560d4e33"),
        ("encore-active/ns2-runtime/hle/core/hle/service/am/service/gpu_memory_registration.h", "47e133e9bec766bbd2d840b215e8e447b70e93f8"),
        ("tests/ns2_gpu_identity_mapping_source.py", "eca64dbb3bd0ac01b62d7229612a8efcf45d567d"),
    ):
        raw = (V / relative).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        # The 225/226 successor was sealed above and contains the full prior
        # 171/172/173 worker semantics. Replay the predecessor contract using
        # only the exact authenticated successor identities for this pin.
        if shipping_vendor_pin in {"546e1aa34d2ff183dd4c737f9da8fbf4a62be24e", "f65ccc439534ffd9ce0a307b23bd511b4e32857a", "4e6a966508e718d02526d4d220e112591536f28c", "2d07b5e65baf35c82d0b0e557617aefe730a10b1", "7baf9cc07c6aceee185032544d964f04a2fed108", "1f8a3bbaa7fc33118e63ebef829202d825475bfe"}:
            expected = {
                "encore-active/ns2-runtime/gpu_session/core/hle/service/am/service/gpu_worker.cpp":
                    "ccccfb99af3ffd03ae1a3119b89c7121cc73ac91",
                "encore-active/ns2-runtime/gpu_session/core/hle/service/am/service/gpu_worker.h":
                    "2aa6d526e7c876d11adc180f546935503be54a4a",
                "encore-active/ns2-runtime/hle/core/hle/service/am/service/gpu_memory_registration.h":
                    "e6223aa74605e50aab30e1fd0a0bf8f3b75c4ecf",
                "tests/ns2_gpu_identity_mapping_source.py":
                    "0572833e4e63c5fe7af728c66beea7df53e4219e",
            }[relative]
        assert actual == ns2_preemption_receipt(relative, expected), ("NS2 GPU worker label source drift", relative, actual)
    selected = "4411fc172eef84080ab7de23158349bbe7d08f88"

# GSV GraphicsFrame 1101/1102/1111-1113 successor. Seal the *selected*
# supervisor/runtime, header, ABI decoder and focused test before replaying
# the earlier 3de worker and GPU-session source receipts.
if selected == "4411fc172eef84080ab7de23158349bbe7d08f88":
    for relative, expected in (
        ("encore-active/ns2-runtime/graphics_supervisor/core/hle/service/am/service/graphics_supervisor.cpp", "8f2ebf9bbf9c23284a0f9e7b788b571485c1135d"),
        ("encore-active/ns2-runtime/graphics_supervisor/core/hle/service/am/service/graphics_supervisor.h", "2d424fb67dc984c1af3a1ee1a0d46c59f704bddf"),
        ("encore-active/ns2-runtime/hle/core/hle/service/am/service/graphics_supervisor_protocol.h", "221173de57178d5408f3c8116fbf4202d26c86f7"),
        ("tests/ns2_syncpt_bootstrap_source.py", "56ab0b57f677683de33dbf6365efa5a1fdfc3875"),
    ):
        raw = (V / relative).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        if shipping_vendor_pin in {"2d07b5e65baf35c82d0b0e557617aefe730a10b1", "7baf9cc07c6aceee185032544d964f04a2fed108", "1f8a3bbaa7fc33118e63ebef829202d825475bfe"} and relative in {
            "encore-active/ns2-runtime/graphics_supervisor/core/hle/service/am/service/graphics_supervisor.cpp",
            "encore-active/ns2-runtime/graphics_supervisor/core/hle/service/am/service/graphics_supervisor.h",
            "tests/ns2_syncpt_bootstrap_source.py",
        }:
            expected = {
                "encore-active/ns2-runtime/graphics_supervisor/core/hle/service/am/service/graphics_supervisor.cpp":
                    "66b5bc32c9286ec2462edd09804a670691ac91d8",
                "encore-active/ns2-runtime/graphics_supervisor/core/hle/service/am/service/graphics_supervisor.h":
                    "56e9ddf8b73d4db22559e73fe8d3506bdaa84a1c",
                "tests/ns2_syncpt_bootstrap_source.py":
                    "08894a7985e96f4478501dd69aceb56b214b0306",
            }[relative]
        assert actual == ns2_encoder_receipt(relative, expected), ("NS2 GraphicsFrame source drift", relative, actual)
    # The 172/173 successor already sealed the changed worker 171/172/173
    # owner. For that pin, continue directly with the earlier GPU-session
    # receipt instead of requiring byte-identical pre-label worker sources.
    selected = ("3a97e47a0cfe94ec55227af363d8c289de59d4f8"
                if shipping_vendor_pin in {"0c4eafeb9f197e76a1f0bb06038ef9bbf2c7565d", "bc6baf037ac3304d4ba81cf7589f7e52e8fa8ae0", "546e1aa34d2ff183dd4c737f9da8fbf4a62be24e"}
                else "3de91cf284c8ef234c757c046998c4f48165c59a")

# GSV TIPC 113 successor: authenticate the exact supervisor/protocol/header
# and existing syncpt/bootstrap receipt, then replay the reviewed 3de graph.
if selected == "2fd07582db57fdddc67e6fd56cec16624a902c6a":
    for relative, expected in (
        ("encore-active/ns2-runtime/graphics_supervisor/core/hle/service/am/service/graphics_supervisor.cpp", "fbbb41f8e281d276bad2174d3d6fe43c05c66b92"),
        ("encore-active/ns2-runtime/graphics_supervisor/core/hle/service/am/service/graphics_supervisor.h", "2701836cbc4448bb6c934c53db49f051de76988c"),
        ("encore-active/ns2-runtime/hle/core/hle/service/am/service/graphics_supervisor_protocol.h", "8b0cfe00cf9f6f450e69cbf4d55ee84336d4d0b8"),
        ("tests/ns2_syncpt_bootstrap_source.py", "688f868e999a707557852730996888c8d6234e56"),
    ):
        raw = (V / relative).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        assert actual == ns2_preemption_receipt(relative, expected), ("NS2 GSV TIPC 113 source drift", relative, actual)
    selected = "3de91cf284c8ef234c757c046998c4f48165c59a"

# Worker TIPC 171 successor: seal only the comptag decoder/handler/header and
# its focused ownership receipt, then replay the reviewed 3a97 graph.
if selected == "3de91cf284c8ef234c757c046998c4f48165c59a":
    for relative, expected in (
        ("encore-active/ns2-runtime/gpu_session/core/hle/service/am/service/gpu_worker.cpp", "1042668b48e71020ee777e0ec0aef6b1606edaf0"),
        ("encore-active/ns2-runtime/gpu_session/core/hle/service/am/service/gpu_worker.h", "0a4ded1cba3fc0ed8163bda05cc32956f6216aa4"),
        ("encore-active/ns2-runtime/hle/core/hle/service/am/service/gpu_memory_registration.h", "c104301566467d973ebf0634580a0fbc4a44daf9"),
        ("tests/ns2_gpu_identity_mapping_source.py", "599f766e76fab45314a77c2fa573b8229cf83de1"),
    ):
        raw = (V / relative).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        if shipping_vendor_pin in {"546e1aa34d2ff183dd4c737f9da8fbf4a62be24e", "f65ccc439534ffd9ce0a307b23bd511b4e32857a", "4e6a966508e718d02526d4d220e112591536f28c", "2d07b5e65baf35c82d0b0e557617aefe730a10b1", "7baf9cc07c6aceee185032544d964f04a2fed108", "1f8a3bbaa7fc33118e63ebef829202d825475bfe"}:
            expected = {
                "encore-active/ns2-runtime/gpu_session/core/hle/service/am/service/gpu_worker.cpp":
                    "ccccfb99af3ffd03ae1a3119b89c7121cc73ac91",
                "encore-active/ns2-runtime/gpu_session/core/hle/service/am/service/gpu_worker.h":
                    "2aa6d526e7c876d11adc180f546935503be54a4a",
                "encore-active/ns2-runtime/hle/core/hle/service/am/service/gpu_memory_registration.h":
                    "e6223aa74605e50aab30e1fd0a0bf8f3b75c4ecf",
                "tests/ns2_gpu_identity_mapping_source.py":
                    "0572833e4e63c5fe7af728c66beea7df53e4219e",
            }[relative]
        assert actual == ns2_preemption_receipt(relative, expected), ("NS2 worker TIPC 171 source drift", relative, actual)
    selected = "3a97e47a0cfe94ec55227af363d8c289de59d4f8"

# TIPC 200 successor: only the selected GPU-session owner/protocol/header and
# its focused source receipt changed. Seal those exact blobs, then replay the
# already reviewed c74 graph for every unaffected FC27/P0 owner.
if selected == "3a97e47a0cfe94ec55227af363d8c289de59d4f8":
    for relative, expected in (
        ("encore-active/ns2-runtime/gpu_session/core/hle/service/am/service/gpu_session.cpp", "be33e5fa3a6f7f2ed4eb4aeac6c7650b204cfa17"),
        ("encore-active/ns2-runtime/gpu_session/core/hle/service/am/service/gpu_session.h", "be6f4f16c9407876ff0f8259cc1c777d05e8056f"),
        ("encore-active/ns2-runtime/hle/core/hle/service/am/service/gpu_session_protocol.h", "b4298a1231aee0f3b675861211bbcf30260dd033"),
        ("tests/ns2_gpu_partition_new_sdk_source.py", "e41711b1822cadffd3b699befb55aa4e9e2f1433"),
    ):
        raw = (V / relative).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        assert actual == ns2_preemption_receipt(relative, expected), ("NS2 GPU session TIPC 200 source drift", relative, actual)
    selected = "c74fb345ac3d8fa752f403369827a432f3503fb5"

# Native GPFIFO fence-wait admission: invalid ID returns a guest error
# before the inherited SyncpointManager asserts or throws on unreserved IDs.
if selected in {"08972732d0402fa455a4982ed5ffd5d9f2c7e83c", "c74fb345ac3d8fa752f403369827a432f3503fb5"}:
    for relative, expected in (
        ("encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/nvhost_gpu.cpp", "ec99bc8bd379bf51ce4971d1d21d5a0d16d6fed4"),
        ("tests/p0_ns2_gpfifo_preimpl_trace_source.py", "35d31053361f392f6dd2a70b4afee28f36cbf56b"),
    ):
        raw = (V / relative).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        # The selected H:0x21 successor sealed exactly these two changed
        # GPFIFO-owner/test blobs above. Do not require the old bytes again
        # after independently proving the new source graph.
        if shipping_vendor_pin in {"bc6baf037ac3304d4ba81cf7589f7e52e8fa8ae0", "546e1aa34d2ff183dd4c737f9da8fbf4a62be24e", "f65ccc439534ffd9ce0a307b23bd511b4e32857a", "4e6a966508e718d02526d4d220e112591536f28c", "2d07b5e65baf35c82d0b0e557617aefe730a10b1", "7baf9cc07c6aceee185032544d964f04a2fed108", "1f8a3bbaa7fc33118e63ebef829202d825475bfe"}:
            expected = {
                "encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/nvhost_gpu.cpp":
                    ("81bac0bb0c1be0be6ed0aca81931fc593b948044"
                     if shipping_vendor_pin in {"4e6a966508e718d02526d4d220e112591536f28c", "2d07b5e65baf35c82d0b0e557617aefe730a10b1", "7baf9cc07c6aceee185032544d964f04a2fed108", "1f8a3bbaa7fc33118e63ebef829202d825475bfe"}
                     else "24096d0848b560d5e7befe979ecaebd1dcc730ae"),
                "tests/p0_ns2_gpfifo_preimpl_trace_source.py":
                    ("d78aaea83009616131bcaf68bfb67fd12fe2e575"
                     if shipping_vendor_pin in {"4e6a966508e718d02526d4d220e112591536f28c", "2d07b5e65baf35c82d0b0e557617aefe730a10b1", "7baf9cc07c6aceee185032544d964f04a2fed108", "1f8a3bbaa7fc33118e63ebef829202d825475bfe"}
                     else "4e7a4fd77cd96ff650edfc74f6a841b266ca2152"),
            }[relative]
        assert actual == ns2_preemption_receipt(relative, expected), ("NS2 GPFIFO wait admission source drift", relative, actual)
    selected = "eb62d96583999c5d159b837dfb9b1b02e8173a9c"

# NS2 read-current user syncpoint: NVIDIA UAPI read_ext_check must
# match the guest syncpoint value shown in the GMMU shim, not future fence max.
if selected == "457f9501c52fcf6ce2aaca967757c0eb9e452f58":
    for relative, expected in (
        ("encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/nvhost_gpu.cpp", "176e9501256347d2c8afbe60d225c130c3c67e6e"),
        ("tests/ns2_syncpoint_shim_source.py", "83636703c71ec50c8e6052f9bc9bec9ed8f54a61"),
    ):
        raw = (V / relative).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        assert actual == ns2_preemption_receipt(relative, expected), ("NS2 user syncpoint source drift", relative, actual)
    selected = "eb62d96583999c5d159b837dfb9b1b02e8173a9c"

# Native A:2 sparse rollback quarantine and remove duplicate A:3/A:5
# WaitForIdle drains, with exact active source and source-contract blobs.
if selected == "95ed29da0eb91af4561154ec3688968959185b9b":
    for relative, expected in (
        ("encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.cpp", "a0f73ad8a4a156e41896264038f96e5e0e893fbb"),
        ("tests/ns2_gpu_identity_mapping_source.py", "0a598e5a77f7de39091fcc175fc40363e8637d88"),
    ):
        raw = (V / relative).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        assert actual == ns2_preemption_receipt(relative, expected), ("NS2 native sparse rollback source drift", relative, actual)
    selected = "eb62d96583999c5d159b837dfb9b1b02e8173a9c"

# P0 native VA allocator page-class guard plus preserved owner tests.
if selected == "615ec1b7a73bb26dcff8525cf543aafff04ecbf0":
    for relative, expected in (
        ("encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.cpp", "0d64b35fdfef15ee0bb8fa8a9b7d59c6ec17fbcb"),
        ("tests/ns2_gpu_identity_mapping_source.py", "f782842092f5bfc2847cbfbdf18d9efdb368af53"),
    ):
        raw = (V / relative).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        assert actual == ns2_preemption_receipt(relative, expected), ("NS2 GPU VA page-class source drift", relative, actual)
    selected = "eb62d96583999c5d159b837dfb9b1b02e8173a9c"

# NS2 native VA/pin retirement WFI: exact selected source seal.
if selected == "a773cfa1a5cd95285eab7e8dd4d21ceef848a0a0":
    for relative, expected in (
        ("encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.cpp", "cbb03b8eed8fb061328b6d86e9d773e015c9cf07"),
        ("tests/ns2_gpu_identity_mapping_source.py", "4d17e7a7c18c8d6e5f87596da87ce6738336efd5"),
    ):
        raw = (V / relative).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        assert actual == ns2_preemption_receipt(relative, expected), ("NS2 GPU retirement source drift", relative, actual)
    selected = "eb62d96583999c5d159b837dfb9b1b02e8173a9c"

# Native NVN 768-GiB user VA partition: exact two changed blobs,
# preserving 1-TiB GMMU capacity and all earlier sealed owner sources.
if selected == "754dc4110ad1e13ea0237e5826599f97d0ccd2f9":
    for relative, expected in (
        ("encore-active/ns2-runtime/gpu_session/core/hle/service/am/service/gpu_session.cpp", "2d9d71e81d7f6e1dbbb8ef37e3f601d68abc88d3"),
        ("tests/ns2_gpu_partition_new_sdk_source.py", "ceaf06587daab525a8229c8186de891e9d3ea9aa"),
    ):
        raw = (V / relative).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        assert actual == ns2_preemption_receipt(relative, expected), ("NS2 NVN VA partition drift", relative, actual)
    selected = "eb62d96583999c5d159b837dfb9b1b02e8173a9c"

# Source-exact native channel user syncpoint ABI (16-byte UAPI).
# Five source owners changed after the immediately preceding prepared pair;
# all previous vendor source receipts stay immutable in its parent commit.
if selected == "d8c1595f187b24b434533c02fe4085a2905f34aa":
    for relative, expected in (
        ("encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/nvhost_gpu.cpp", "ba1c9923a576e9ddc25ddcbf9df628925be45109"),
        ("encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/nvhost_gpu.h", "3dec2b4990d1c8c5cb45d7c5fe87c12a62dff09f"),
        ("encore-active/eden-core/overrides/native-tiling/video_core/memory_manager.h", "c83087f816eb9956a4f7ed565794a2b643512e87"),
        ("encore-active/eden-core/guest-bridge/memory_manager.h", "c670df3eadf42d9d4a5e1d7d3b2f5c674f83bf7e"),
        ("tests/ns2_syncpoint_shim_source.py", "0f696fbe1b02e677a74c6c41fee79d4b00f0f682"),
    ):
        raw = (V / relative).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        assert actual == ns2_preemption_receipt(relative, expected), ("NS2 channel syncpoint source drift", relative, actual)
    selected = "eb62d96583999c5d159b837dfb9b1b02e8173a9c"

# Restore native A:0x0C kind changes on BOTH direct and sparse pinned
# GPU views. Only these two blobs changed after the last sealed successor.
if selected == "9edb09cf0a720c6b22fe092efd21cc9891225a48":
    for relative, expected in (
        ("encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.cpp", "604aa850609983b61a3e5033b4fa1740b3d64c70"),
        ("tests/ns2_gpu_identity_mapping_source.py", "a2afbf6710977594ee27f2abce17446483cc0d59"),
    ):
        raw = (V / relative).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        assert actual == ns2_preemption_receipt(relative, expected), ("NS2 sparse kind-map source drift", relative, actual)
    selected = "eb62d96583999c5d159b837dfb9b1b02e8173a9c"

# Native-only duplicate ALLOC_AS guard: only the selected AS C++ and
# focused source-contract file differ from the fully reviewed predecessor.
# Compare the exact new blobs BEFORE replaying its source graph; no branch
# publication, host test, CI or PS5 console validation is implied here.
if selected == "7a4ddd589b7a20d75a1a6019a67a16c5f2d39bc5":
    for relative, expected in (
        ("encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.cpp", "85b765ca5871f56a7f9f1f883841775d260e121b"),
        ("tests/ns2_gpu_identity_mapping_source.py", "0cf04759ddff657d4a9892e0932bbac789655cc5"),
    ):
        raw = (V / relative).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        assert actual == ns2_preemption_receipt(relative, expected), ("NS2 duplicate AS guard drift", relative, actual)
    selected = "eb62d96583999c5d159b837dfb9b1b02e8173a9c"

# Prepared NS2 consolidation, still NOT a published main or console pass.
# Git's exact pinned commit ID seals its full tree; these seven changed
# compiled/test blobs are additionally checked before selecting the same
# native source-profile receipts as the fully recorded predecessor.
if selected == "1ca2828bfccd0d5c8a903f3c503480f1fc1b6ddc":
    for relative, expected in (
        ("encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.cpp", "284e754886ef59e73120cfa2b8fb691eddc51707"),
        ("encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.h", "24a07c5c5e6810d8d100a73d7ad7da83fd698cbe"),
        ("encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/native_gpu_va_layout.h", "5f3ebf592001119c9686657600066d62db344524"),
        ("encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/nvhost_gpu.cpp", "5be598819854a43c929d570d0a0f6234c1a829e8"),
        ("encore-active/ns2-runtime/nvdrv/core/hle/service/nvdrv/devices/nvhost_ctrl_gpu.cpp", "f57925efd8b032f64b7bc979f8fe4f2765fb66bf"),
        ("encore-active/ns2-runtime/graphics_supervisor/core/hle/service/am/service/graphics_supervisor.cpp", "9d5e1666c015db72c3fa4f8ea501d7c68f826991"),
        ("tests/ns2_gpu_identity_mapping_source.py", "256ad36db2562e4895842a0c2034a83311bbfcbc"),
    ):
        raw = (V / relative).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        assert actual == ns2_preemption_receipt(relative, expected), ("NS2 prepared source drift", relative, actual)
    # The prepared commit descends directly from the reviewed public vendor
    # and changes only these seven owners; all earlier source fingerprints
    # are encoded in the immutable pinned vendor commit tree.
    selected = "eb62d96583999c5d159b837dfb9b1b02e8173a9c"

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
        assert actual == ns2_preemption_receipt(relative, expected), ("NS2 40-byte remap source drift", relative, actual)
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
# Exact six-file NS2 successor over d634: loader size guard and GSV/Syncpt.
# Every changed blob is checked separately; all other receipts remain active.
ns2_boot_successor_blobs = {
        "encore-active/ns2-runtime/graphics_supervisor/core/hle/service/am/service/graphics_supervisor.cpp": "94486279bd7e2edd9b8e84b1c5cd77468b12d1a8",
        "encore-active/ns2-runtime/graphics_supervisor/core/hle/service/am/service/graphics_supervisor.h": "6809796e7d5853c03060b792997fb671f0ac1340",
        "encore-active/ns2-runtime/hle/core/hle/service/am/service/graphics_supervisor_bootstrap.h": "aace3ee0086dc6faf35dd648825b076b620c2025",
        "encore-active/ns2-runtime/hle/core/hle/service/am/service/graphics_supervisor_protocol.h": "f318dfdfe66823a077ddcb736b10a355a8a1fb3a",
        "encore-active/ns2-runtime/nx/core/loader/nx.cpp": "5d999ca68668133ea3f151669ecd6ac6a17ae1c5",
        "tests/ns2_syncpt_bootstrap_source.py": "9b54b4dbf669bca02d40c78411d3ca32c8290efb",
}
if actual_vendor_pin in {"166e473e120a86a6edcd32a975ffe19b45ffdd42", "3522d8578fbcd7b46d2a439d5d718dfb570beb7b"}:
    ns2_boot_successor_blobs = {
        **ns2_boot_successor_blobs,
        "encore-active/eden-core/overrides/video_core/host1x/syncpoint_manager.h": "a62b9a9e8019c2df085fc9d393fcbd4207cd78d7",
        "encore-active/eden-core/src/video_core/host1x/syncpoint_manager.cpp": "59ac07af5eab89e78b7089d1db58918f2506aafe",
        "encore-active/ns2-runtime/graphics_supervisor/core/hle/service/am/service/graphics_supervisor.cpp": "8b4aba07a17021ea2c6ca18516546a2d7e058853",
        "tests/ps5_host1x_wait_notification_host.py": "7f4af55e823c100f476ddfbf64384dd5d900b616",
        "tests/ns2_syncpt_bootstrap_source.py": "b5c9a70a3051c86ad899c023084e8e9f955352cf",
    }
if actual_vendor_pin == "3522d8578fbcd7b46d2a439d5d718dfb570beb7b":
    ns2_boot_successor_blobs.update({
        "encore-active/ns2-runtime/graphics_supervisor/core/hle/service/am/service/graphics_supervisor.cpp": "2d140d794140660f4bf3fa464b85ee3f64c4d490",
        "encore-active/ns2-runtime/graphics_supervisor/core/hle/service/am/service/graphics_supervisor.h": "396f1152a027907f4439ebf6cf68aacf75d20d39",
        "tests/ns2_syncpt_bootstrap_source.py": "2d707d2544bf48d1cbde6f3dd4445b365579b9a4",
    })
if actual_vendor_pin in {"692e9819a7a1f1b818bf3739c72d8e5252cae661", "166e473e120a86a6edcd32a975ffe19b45ffdd42", "3522d8578fbcd7b46d2a439d5d718dfb570beb7b"}:
    for relative, expected in ns2_boot_successor_blobs.items():
        raw = (V / relative).read_bytes()
        assert hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest() == expected, relative

def reviewed_blob(relative, expected):
    if actual_vendor_pin == "84d3b0398ae7db1618899815bc1f98894453fbf6":
        readback_blobs = {"encore-active/ns2-astc/include/video_core/texture_cache/texture_cache.h":"bbb55dc7b1648fa1e6fd730a1b3515f2969221c7","tests/ns1_r23_18_tir_host.py":"ea964bd9dd455f0e1b9a36fa5d0a3b9c5fd42a9b","tests/fc27_deferred_page_protection_host.py":"a4962e7b00c7a8ee6626b359551d2241400feb1f"}
        if relative in readback_blobs:
            return readback_blobs[relative]
    if actual_vendor_pin == "b92d4183cec69e65216162cf61e451eff643caa0":
        readback_blobs = {"encore-active/ns2-astc/include/video_core/texture_cache/texture_cache.h":"45659d2fa8ae336d28e7ccbd02b3104d96229378","tests/ns1_r23_18_tir_host.py":"9e835a870dac4e7728978328814e57cab58d85c5","tests/fc27_deferred_page_protection_host.py":"c4b49d84e9714d64ae4e72942a32274d6fc1bc7f"}
        if relative in readback_blobs:
            return readback_blobs[relative]
    if actual_vendor_pin in {"191dd458c68de13f0f71659e3b4a9598af7de561", "b743e9c7ec9832832711fc0ea34e03a25c973557", "4c8f72f8ba3db320af55cea0f53cac16366c3ea0", "6affc4ad869a3eaab9d1bed1e65de8872d93363b", "b92d4183cec69e65216162cf61e451eff643caa0", "84d3b0398ae7db1618899815bc1f98894453fbf6"}:
        if relative == "encore-active/eden-vulkan/vulkan_rasterizer.cpp":
            return "fcd174ed2326f3c205365b192c98f9d2f4d82ec3" if actual_vendor_pin in {"6affc4ad869a3eaab9d1bed1e65de8872d93363b", "b92d4183cec69e65216162cf61e451eff643caa0", "84d3b0398ae7db1618899815bc1f98894453fbf6"} else "e4948333ed15fba8024aeb4ffaa143a2e010f991"
        if relative == "tests/fc27_cpu_write_download_race_host.py":
            return "7da2cf9b3e6f14c210c14fe201a0a95db92856cc"
        if actual_vendor_pin in {"b743e9c7ec9832832711fc0ea34e03a25c973557", "4c8f72f8ba3db320af55cea0f53cac16366c3ea0", "6affc4ad869a3eaab9d1bed1e65de8872d93363b", "b92d4183cec69e65216162cf61e451eff643caa0", "84d3b0398ae7db1618899815bc1f98894453fbf6"} and relative == "tests/fc27_deferred_page_protection_host.py":
            return "4e10cd67ee80e617becdd751a736f25a4e18aa07" if actual_vendor_pin in {"6affc4ad869a3eaab9d1bed1e65de8872d93363b", "b92d4183cec69e65216162cf61e451eff643caa0", "84d3b0398ae7db1618899815bc1f98894453fbf6"} else "bd92b4e52e7621ff55610e40b862a30b9f575e47"
        if actual_vendor_pin in {"4c8f72f8ba3db320af55cea0f53cac16366c3ea0", "6affc4ad869a3eaab9d1bed1e65de8872d93363b", "b92d4183cec69e65216162cf61e451eff643caa0", "84d3b0398ae7db1618899815bc1f98894453fbf6"} and relative == "encore-active/eden-core/overrides/usage-tracker/video_core/buffer_cache/usage_tracker.h":
            return "f7f1273ba8314689b3fac5bf108205513c21f5d8"
        if actual_vendor_pin in {"4c8f72f8ba3db320af55cea0f53cac16366c3ea0", "6affc4ad869a3eaab9d1bed1e65de8872d93363b", "b92d4183cec69e65216162cf61e451eff643caa0", "84d3b0398ae7db1618899815bc1f98894453fbf6"} and relative == "tests/ps5_buffer_usage_granularity_host.py":
            return "a3e3f90825df12d026b69ab9475a667234696768"
    if actual_vendor_pin in {"ffa7757e98bf42a5abcd5c0b9e845cfdbc01e75e", "752b92033610b294a36254d5747c317aca51c1d5", "1b5256d72072e05a62fb734bc9ef790fc81c1573", "628d01bdc4368e9ad661d749515f788ef7c03802", "191dd458c68de13f0f71659e3b4a9598af7de561", "b743e9c7ec9832832711fc0ea34e03a25c973557", "4c8f72f8ba3db320af55cea0f53cac16366c3ea0", "6affc4ad869a3eaab9d1bed1e65de8872d93363b", "b92d4183cec69e65216162cf61e451eff643caa0", "84d3b0398ae7db1618899815bc1f98894453fbf6"}:
        hotpath_blobs = {"encore-active/eden-core/overrides/buffer-hotpath/common/range_sets.h":"1c90e08bc3c66731aa717e7b17b3249539848016","encore-active/eden-core/overrides/buffer-hotpath/common/range_sets.inc":("bd48ff5cb346981f0937cfddbb042f9100697fd2" if actual_vendor_pin in {"752b92033610b294a36254d5747c317aca51c1d5", "1b5256d72072e05a62fb734bc9ef790fc81c1573", "628d01bdc4368e9ad661d749515f788ef7c03802", "191dd458c68de13f0f71659e3b4a9598af7de561", "b743e9c7ec9832832711fc0ea34e03a25c973557", "4c8f72f8ba3db320af55cea0f53cac16366c3ea0", "6affc4ad869a3eaab9d1bed1e65de8872d93363b", "b92d4183cec69e65216162cf61e451eff643caa0", "84d3b0398ae7db1618899815bc1f98894453fbf6"} else "742dc02b71ada75425fec7e126093634a22d2102"),"encore-active/eden-core/overrides/buffer-hotpath/video_core/buffer_cache/word_manager.h":"0992d01d0b4e262dd4b4a79633affa8b02529795","encore-active/eden-core/src/video_core/buffer_cache/buffer_cache.h":"4ce33d21debc33c9625129cbd545bf9b1c084272","tests/fc27_gpu_page_sibling_preservation_host.py":("f7b1eb205c2614d30809dd0f9f132e43ccf46745" if actual_vendor_pin in {"752b92033610b294a36254d5747c317aca51c1d5", "1b5256d72072e05a62fb734bc9ef790fc81c1573", "628d01bdc4368e9ad661d749515f788ef7c03802", "191dd458c68de13f0f71659e3b4a9598af7de561", "b743e9c7ec9832832711fc0ea34e03a25c973557", "4c8f72f8ba3db320af55cea0f53cac16366c3ea0", "6affc4ad869a3eaab9d1bed1e65de8872d93363b", "b92d4183cec69e65216162cf61e451eff643caa0", "84d3b0398ae7db1618899815bc1f98894453fbf6"} else "c27f87a327a5a371a7810b41dabc2bc8f03fe61d")}
        if relative in hotpath_blobs:
            expected = hotpath_blobs[relative]
    if actual_vendor_pin in {"a8f327c972bd2f84f6e6f9432c96c4a948963073", "ffa7757e98bf42a5abcd5c0b9e845cfdbc01e75e", "752b92033610b294a36254d5747c317aca51c1d5", "1b5256d72072e05a62fb734bc9ef790fc81c1573", "628d01bdc4368e9ad661d749515f788ef7c03802", "191dd458c68de13f0f71659e3b4a9598af7de561", "b743e9c7ec9832832711fc0ea34e03a25c973557", "4c8f72f8ba3db320af55cea0f53cac16366c3ea0", "6affc4ad869a3eaab9d1bed1e65de8872d93363b", "b92d4183cec69e65216162cf61e451eff643caa0", "84d3b0398ae7db1618899815bc1f98894453fbf6"}:
        updated_tests = {
            "tests/fc27_xmad_pointer_fold_host.py": ("405f665e55cc2d94cbbabd54cdeeaaedf3e236c5" if actual_vendor_pin in {"628d01bdc4368e9ad661d749515f788ef7c03802", "191dd458c68de13f0f71659e3b4a9598af7de561", "b743e9c7ec9832832711fc0ea34e03a25c973557", "4c8f72f8ba3db320af55cea0f53cac16366c3ea0", "6affc4ad869a3eaab9d1bed1e65de8872d93363b", "b92d4183cec69e65216162cf61e451eff643caa0", "84d3b0398ae7db1618899815bc1f98894453fbf6"} else "c793db6f19f44e9a7ffdbd512b1bc382ed605fc3"),
            "tests/fc27_dynamic_texture_static_sampler_host.py": ("089755d22314e088a2d4f8366847588f6579db2f" if actual_vendor_pin in {"628d01bdc4368e9ad661d749515f788ef7c03802", "191dd458c68de13f0f71659e3b4a9598af7de561", "b743e9c7ec9832832711fc0ea34e03a25c973557", "4c8f72f8ba3db320af55cea0f53cac16366c3ea0", "6affc4ad869a3eaab9d1bed1e65de8872d93363b", "b92d4183cec69e65216162cf61e451eff643caa0", "84d3b0398ae7db1618899815bc1f98894453fbf6"} else "0ae204dc5bb6b34871816ab48973639ac4439bda"),
        }
        if relative in updated_tests:
            return updated_tests[relative]
    if actual_vendor_pin in {"a8f327c972bd2f84f6e6f9432c96c4a948963073", "ffa7757e98bf42a5abcd5c0b9e845cfdbc01e75e", "752b92033610b294a36254d5747c317aca51c1d5", "1b5256d72072e05a62fb734bc9ef790fc81c1573", "628d01bdc4368e9ad661d749515f788ef7c03802", "191dd458c68de13f0f71659e3b4a9598af7de561", "b743e9c7ec9832832711fc0ea34e03a25c973557", "4c8f72f8ba3db320af55cea0f53cac16366c3ea0", "6affc4ad869a3eaab9d1bed1e65de8872d93363b", "b92d4183cec69e65216162cf61e451eff643caa0", "84d3b0398ae7db1618899815bc1f98894453fbf6"} and relative == "encore-active/eden-vulkan/vk_pipeline_cache_cost.cpp":
        return ("7db0462ad24aa4c6356ce4efa0086b356f171be6" if actual_vendor_pin in {"628d01bdc4368e9ad661d749515f788ef7c03802", "191dd458c68de13f0f71659e3b4a9598af7de561", "b743e9c7ec9832832711fc0ea34e03a25c973557", "4c8f72f8ba3db320af55cea0f53cac16366c3ea0", "6affc4ad869a3eaab9d1bed1e65de8872d93363b", "b92d4183cec69e65216162cf61e451eff643caa0", "84d3b0398ae7db1618899815bc1f98894453fbf6"} else "cdcef0c6ec4cdada8521af43f856e66f98d5b0a9")
    if actual_vendor_pin == "3abd88bc1a3c334f53f345998b72e9cf8ae87abf":
        exact_wait = {
            "encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/nvhost_gpu.cpp": "25aa385480b28a3d828da034222795ac1f150e94",
            "encore-active/ns2-runtime/gpu_dispatch/video_core/dma_pusher.h": "7965c196bff1364f64e747f152bcc314b1db3658",
            "encore-active/eden-core/src/video_core/dma_pusher.cpp": "a8c95c51445ddafc2b8f42a92099359aae33e836",
            "encore-active/eden-sync/overrides/h05-syncpoint/core/hle/service/nvdrv/core/syncpoint_manager.h": "624bd4d84d4a02d509430df651c46997254f8e59",
            "encore-active/eden-sync/src/core/hle/service/nvdrv/core/syncpoint_manager.cpp": "6b09b35a07aabfff0d79df4f098e4f5ea6f5631d",
            "tests/p0_ns2_gpfifo_preimpl_trace_source.py": "3a5c6d75a828b5d867a8dbffbf6337d1c460f135",
        }
        if relative in exact_wait:
            return exact_wait[relative]
    if actual_vendor_pin in {"101eae5edb76fefc40b039009eb35bbaaae99386", "3abd88bc1a3c334f53f345998b72e9cf8ae87abf"}:
        exact_gsv = {
            "encore-active/ns2-runtime/graphics_supervisor/core/hle/service/am/service/graphics_supervisor.cpp": "d25dddc6c3aaf149483552b1ea9b68b4daa8dbe8",
            "encore-active/ns2-runtime/graphics_supervisor/core/hle/service/am/service/graphics_supervisor.h": "e18d391ef7d38a6dfb64feffc796caad212f16bc",
            "tests/ns2_syncpt_bootstrap_source.py": "efbe43477d0068cff8cab5a18de5378aa1fc409d",
        }
        if relative in exact_gsv:
            return exact_gsv[relative]
    if actual_vendor_pin in {"652f88555e8bb16ffeffd9d1fa3d0c49e7925dfc", "38e19d4be0d99bbba35558af2c0620cd9b46f12e", "4c51642038c4a3cc04c0f8f0b8267b17aafd4045", "881f6fb23c818ecfc387d2b134e1cd7328fc5995", "d8155325107dbbb1f8ef44f75553595fe4c8ec8c", "101eae5edb76fefc40b039009eb35bbaaae99386", "3abd88bc1a3c334f53f345998b72e9cf8ae87abf"}:
        exact = {
        "encore-active/ns2-runtime/gpu_session/core/hle/service/am/service/gpu_worker.cpp": ("e6d85e1fb3b7749cf578a73bd446bd2e8d32223c" if actual_vendor_pin in {"d8155325107dbbb1f8ef44f75553595fe4c8ec8c", "101eae5edb76fefc40b039009eb35bbaaae99386", "3abd88bc1a3c334f53f345998b72e9cf8ae87abf"} else "e61820cc289ce24670c4b1056d34914dfe2eaf26" if actual_vendor_pin == "881f6fb23c818ecfc387d2b134e1cd7328fc5995" else "ed0c89a2cfe5fcedb941cc57f4ed294b8cf610c4"),
        "encore-active/ns2-runtime/gpu_session/core/hle/service/am/service/gpu_worker.h": "5c694c92d003b10c58793a356532adc3860e9475",
        "encore-active/ns2-runtime/hle/core/hle/service/am/service/gpu_worker_protocol.h": "d0fcc7e3dd9283f0de1b0ce6756a238b8fe3894d",
        "encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.cpp": "5320f2c99c77b1c178175f19b7996000f5de3286",
        "encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.h": "9603dfd3e2ae0e8a16b29ef8520a8db17340c29d",
        "tests/ns2_gpu_identity_mapping_source.py": ("d0a4eb74022d81046377525bbe56e9042304757c" if actual_vendor_pin in {"d8155325107dbbb1f8ef44f75553595fe4c8ec8c", "101eae5edb76fefc40b039009eb35bbaaae99386", "3abd88bc1a3c334f53f345998b72e9cf8ae87abf"} else "5d752540cd053cd649daf05378f7e3f76577a356" if actual_vendor_pin == "881f6fb23c818ecfc387d2b134e1cd7328fc5995" else "8f7ab34c126da2eb3aee1e0ee6fff5d676eaf018" if actual_vendor_pin == "4c51642038c4a3cc04c0f8f0b8267b17aafd4045" else "2cc85651698aa291a7d146a6a357db4b89709c91" if actual_vendor_pin == "38e19d4be0d99bbba35558af2c0620cd9b46f12e" else "243eb8e6c8127d240e7a151cac44326e71d72280")
}
        if relative in exact:
            return exact[relative]
    if actual_vendor_pin == "6b8fd06606f12be187f73e8809e56a49864794f9":
        if relative == "encore-active/ns2-runtime/gpu_session/core/hle/service/am/service/gpu_worker.cpp":
            return "0f2244f61fcac38d4379d7dda9efaf447d0eea46"
        if relative == "tests/ns2_gpu_identity_mapping_source.py":
            return "c703c4dd653c12c3ed6d594d38d33c9b45d3d850"
    if actual_vendor_pin in {"973d45ae0da5d9612d30900e39118d67d039b31a", "6b8fd06606f12be187f73e8809e56a49864794f9", "652f88555e8bb16ffeffd9d1fa3d0c49e7925dfc", "38e19d4be0d99bbba35558af2c0620cd9b46f12e", "4c51642038c4a3cc04c0f8f0b8267b17aafd4045", "881f6fb23c818ecfc387d2b134e1cd7328fc5995", "d8155325107dbbb1f8ef44f75553595fe4c8ec8c", "101eae5edb76fefc40b039009eb35bbaaae99386", "3abd88bc1a3c334f53f345998b72e9cf8ae87abf"} and relative == "encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.cpp":
        return "2ad45d27a850d56ccc6b49e92f2a5051d07be848"
    if actual_vendor_pin in {"692e9819a7a1f1b818bf3739c72d8e5252cae661", "166e473e120a86a6edcd32a975ffe19b45ffdd42", "3522d8578fbcd7b46d2a439d5d718dfb570beb7b"} and relative in ns2_boot_successor_blobs:
        return ns2_boot_successor_blobs[relative]
    if actual_vendor_pin in {"d634b381d85dae30492dd6291fc4e6e96143f363", "692e9819a7a1f1b818bf3739c72d8e5252cae661", "166e473e120a86a6edcd32a975ffe19b45ffdd42", "3522d8578fbcd7b46d2a439d5d718dfb570beb7b"} and relative == "tests/fc27_deferred_page_protection_host.py":
        return "172989eea550754d8ca19191cb99eb5c08546ab5"
    if actual_vendor_pin in {"9632ac089f8b2d89a6856a42e8fb55206cdba1fa", "b5c6f089a6aecd321d08a40238f3cd502f505b26", "dc9f5f95b1f784bb358d6480e53de7247d61d777", "a441295022b23834f8531c54d2b0965f84023278", "7c5d5220dd4df4a531418458ab623ef86c41348c", "44540549ee9a65eb8078e271f43ccded0e8e984f", "d63d82dfb9c2afbacac4c9dc1491f743fb083d52", "d634b381d85dae30492dd6291fc4e6e96143f363", "692e9819a7a1f1b818bf3739c72d8e5252cae661", "166e473e120a86a6edcd32a975ffe19b45ffdd42", "3522d8578fbcd7b46d2a439d5d718dfb570beb7b"}:
        translation_drain_exact = {
            "encore-active/eden-vulkan/vk_pipeline_cache_cost.cpp": ("c92e3dbbf4de08030589d9776dded974accf11eb" if actual_vendor_pin in {"44540549ee9a65eb8078e271f43ccded0e8e984f", "d63d82dfb9c2afbacac4c9dc1491f743fb083d52", "d634b381d85dae30492dd6291fc4e6e96143f363", "692e9819a7a1f1b818bf3739c72d8e5252cae661", "166e473e120a86a6edcd32a975ffe19b45ffdd42", "3522d8578fbcd7b46d2a439d5d718dfb570beb7b"} else "206d845256bbdc1d5f8d660aeed718ad4f607063" if actual_vendor_pin in {"a441295022b23834f8531c54d2b0965f84023278", "7c5d5220dd4df4a531418458ab623ef86c41348c"} else "b246cf9562f8f0c37d287f7049874f04561a4b8f" if actual_vendor_pin == "dc9f5f95b1f784bb358d6480e53de7247d61d777" else "fc537323bb9f63d70ef5f8cedd65886e6a0099c0"),
            "tests/fc27_xmad_pointer_fold_host.py": ("5498ea8990e905cb4b2320151a040627681dc77c" if actual_vendor_pin in {"44540549ee9a65eb8078e271f43ccded0e8e984f", "d63d82dfb9c2afbacac4c9dc1491f743fb083d52", "d634b381d85dae30492dd6291fc4e6e96143f363", "692e9819a7a1f1b818bf3739c72d8e5252cae661", "166e473e120a86a6edcd32a975ffe19b45ffdd42", "3522d8578fbcd7b46d2a439d5d718dfb570beb7b"} else "0dc365434b000ae779d8e44546893ed1722994fc" if actual_vendor_pin in {"a441295022b23834f8531c54d2b0965f84023278", "7c5d5220dd4df4a531418458ab623ef86c41348c"} else "ac228172c0fe65b9ccfb2dc2ee30d0b1db9190da" if actual_vendor_pin == "dc9f5f95b1f784bb358d6480e53de7247d61d777" else "3d3f97ec6e3e9d182558908849306d8cc7c4a78e"),
            "tests/fc27_dynamic_texture_static_sampler_host.py": ("0b8eafaaa919dfd838facaf409acb9cc7018ac6e" if actual_vendor_pin in {"44540549ee9a65eb8078e271f43ccded0e8e984f", "d63d82dfb9c2afbacac4c9dc1491f743fb083d52", "d634b381d85dae30492dd6291fc4e6e96143f363", "692e9819a7a1f1b818bf3739c72d8e5252cae661", "166e473e120a86a6edcd32a975ffe19b45ffdd42", "3522d8578fbcd7b46d2a439d5d718dfb570beb7b"} else "e99e5e9216d971cbaf3b48d89a5924ac85c62b33" if actual_vendor_pin in {"a441295022b23834f8531c54d2b0965f84023278", "7c5d5220dd4df4a531418458ab623ef86c41348c"} else "57b30130d9d321b2954de9c35d5cb522a6f76c69" if actual_vendor_pin == "dc9f5f95b1f784bb358d6480e53de7247d61d777" else "7cf6b36d5de4aa93f118a0bea0381cecafe45988")
        }
        if relative in translation_drain_exact:
            return translation_drain_exact[relative]
    if actual_vendor_pin in {"44f5b75bc93bcea146ad6fba3ac294405ae8709b", "70789b12dea4d72ce9e7f054c5b6f552ec488f5d", "9db97fb12db1a390d6b2410f0c18333aa31e37da"}:
        keyed_timing_exact = {
            "encore-active/eden-vulkan/vk_pipeline_cache_cost.cpp": ("ad07512d129667a617b49b448d898c5756c99025" if actual_vendor_pin in {"70789b12dea4d72ce9e7f054c5b6f552ec488f5d", "9db97fb12db1a390d6b2410f0c18333aa31e37da", "60fa67b98286bd84bd591987c5690ae9b15bda3f", "bf981e9d39d4a908d0d5b6f8407cca814c609bdb", "8026fcca228d0feda62ffd9625e16ee0429d621e", "887bf44af34999e8b6c5b63dc7c01c6c13b82c8f", "1a928783cce2c2692d8fe9fd958400a2de060bbf", "9632ac089f8b2d89a6856a42e8fb55206cdba1fa", "b5c6f089a6aecd321d08a40238f3cd502f505b26", "dc9f5f95b1f784bb358d6480e53de7247d61d777", "a441295022b23834f8531c54d2b0965f84023278", "7c5d5220dd4df4a531418458ab623ef86c41348c", "44540549ee9a65eb8078e271f43ccded0e8e984f", "d63d82dfb9c2afbacac4c9dc1491f743fb083d52", "d634b381d85dae30492dd6291fc4e6e96143f363", "692e9819a7a1f1b818bf3739c72d8e5252cae661", "166e473e120a86a6edcd32a975ffe19b45ffdd42", "3522d8578fbcd7b46d2a439d5d718dfb570beb7b"} else "52470b6160f6049801d963960adf6952c79a45cf"),
            "tests/fc27_dynamic_texture_static_sampler_host.py": "b30c6b062108ec3414bfc5a5ff4a6fe9b22be331",
            "tests/fc27_xmad_pointer_fold_host.py": "09e566db7ddd141ef6554a1e0b8f649d7551ed6e",
            "tests/ns1_r23_35_attribute_handle.py": "b6a7c5468048987883b7fa12f8803e193e456c2e",
            "tests/ps5_recent_prewarm_receipt.py": "10837a358096cfa5a43550043e6fff27635247cb",
        }
        if relative in keyed_timing_exact:
            return keyed_timing_exact[relative]
    if actual_vendor_pin in {"bfdf39014db15f237a16d4a50e6cdfd68bdd87b8", "4626d87be155c0b42904610323098c1205515450", "c32704e63844449b1c18a03deb2cd92939999b90", "fab5ebbfda09ebd3fc414b3127e135c66025ccb8", "acb42e2a2b18fee17673d07e06b2f29709de2fb5", "99df05ff50a7a4a9591c17b08f4ed0f8cb0374a3", "04e252186aa42bacde0899e0c9224035c83a6b0d", "44f5b75bc93bcea146ad6fba3ac294405ae8709b", "70789b12dea4d72ce9e7f054c5b6f552ec488f5d", "9db97fb12db1a390d6b2410f0c18333aa31e37da"}:
        bfdf_exact = {
            "encore-active/ns2-runtime/ampere/shader_recompiler/frontend/ampere/lower_to_maxwell.h": "9169e95ec14559aa6466c68b7d1e1cd3f9e69557",
            "encore-active/ns2-runtime/hle/core/hle/service/am/service/application_proxy_service.cpp": "a07dae606312e673bdbff5110fbf81d4ce307776",
            "encore-active/ns2-runtime/hle/core/hle/service/am/service/application_proxy_service.h": "7aab2ba6235b33b91819ea78a006129183194194",
            "tests/ns2_early_hle_services_source.py": "a8885d094315e22f9bf0a3c41c969f31463815cb",
        }
        if relative in bfdf_exact:
            return bfdf_exact[relative]
    if actual_vendor_pin in {"b099bd7cbefaa1a35d6626d4fd3161afcefa1b48", "bfdf39014db15f237a16d4a50e6cdfd68bdd87b8", "4626d87be155c0b42904610323098c1205515450", "c32704e63844449b1c18a03deb2cd92939999b90", "fab5ebbfda09ebd3fc414b3127e135c66025ccb8", "acb42e2a2b18fee17673d07e06b2f29709de2fb5", "99df05ff50a7a4a9591c17b08f4ed0f8cb0374a3", "04e252186aa42bacde0899e0c9224035c83a6b0d", "44f5b75bc93bcea146ad6fba3ac294405ae8709b", "70789b12dea4d72ce9e7f054c5b6f552ec488f5d", "9db97fb12db1a390d6b2410f0c18333aa31e37da"} and relative == "encore-active/ns2-runtime/gpu_dispatch/video_core/engines/puller.cpp":
        return "02e406d9209de6029bcc526bf800428268b81ed4"
    if actual_vendor_pin in {"b099bd7cbefaa1a35d6626d4fd3161afcefa1b48", "bfdf39014db15f237a16d4a50e6cdfd68bdd87b8", "4626d87be155c0b42904610323098c1205515450", "c32704e63844449b1c18a03deb2cd92939999b90", "fab5ebbfda09ebd3fc414b3127e135c66025ccb8", "acb42e2a2b18fee17673d07e06b2f29709de2fb5", "99df05ff50a7a4a9591c17b08f4ed0f8cb0374a3", "04e252186aa42bacde0899e0c9224035c83a6b0d", "44f5b75bc93bcea146ad6fba3ac294405ae8709b", "70789b12dea4d72ce9e7f054c5b6f552ec488f5d", "9db97fb12db1a390d6b2410f0c18333aa31e37da"} and relative == "encore-active/ns2-runtime/gpu_dispatch/video_core/native_ampere_macro_state.h":
        return "1f60c4cda2a7d5206082434945f40a1cf2bb546c"
    if actual_vendor_pin in {"53d0ad1f9d50b9f1a72cbecacdacdff7fb4e69eb", "7e137d362f9679125726ef4876355a09d788795e", "973d45ae0da5d9612d30900e39118d67d039b31a", "6b8fd06606f12be187f73e8809e56a49864794f9", "652f88555e8bb16ffeffd9d1fa3d0c49e7925dfc", "38e19d4be0d99bbba35558af2c0620cd9b46f12e", "4c51642038c4a3cc04c0f8f0b8267b17aafd4045", "881f6fb23c818ecfc387d2b134e1cd7328fc5995", "d8155325107dbbb1f8ef44f75553595fe4c8ec8c", "101eae5edb76fefc40b039009eb35bbaaae99386", "3abd88bc1a3c334f53f345998b72e9cf8ae87abf"} and relative == "encore-active/ns2-runtime/nvdrv/core/hle/service/nvdrv/devices/native_gpu_characteristics.h":
        return "f6217651bf15d13e5be80c0b1b0b76679f02949b"
    if actual_vendor_pin in {"97fa38381d9ce23b63b3bf3751615dc254ab3634", "b099bd7cbefaa1a35d6626d4fd3161afcefa1b48", "bfdf39014db15f237a16d4a50e6cdfd68bdd87b8", "4626d87be155c0b42904610323098c1205515450", "c32704e63844449b1c18a03deb2cd92939999b90", "fab5ebbfda09ebd3fc414b3127e135c66025ccb8", "acb42e2a2b18fee17673d07e06b2f29709de2fb5", "99df05ff50a7a4a9591c17b08f4ed0f8cb0374a3", "04e252186aa42bacde0899e0c9224035c83a6b0d", "44f5b75bc93bcea146ad6fba3ac294405ae8709b", "70789b12dea4d72ce9e7f054c5b6f552ec488f5d", "9db97fb12db1a390d6b2410f0c18333aa31e37da"} and relative == "encore-active/ns2-runtime/nvdrv/core/hle/service/nvdrv/devices/native_gpu_characteristics.h":
        return "ff9d81f1e2f5b65b73b2cf233579591e07267870"
    if actual_vendor_pin in {PS5_FC27_NVDRV_EXIT_PIN, PS5_FC27_RECENT_PREWARM_PIN} and relative in PS5_FC27_NVDRV_EXIT_BLOBS:
        return PS5_FC27_NVDRV_EXIT_BLOBS[relative]
    if NS2_POISONED_TEARDOWN_ACTIVE and relative in NS2_POISONED_TEARDOWN_BLOBS:
        return NS2_POISONED_TEARDOWN_BLOBS[relative]
    if NS2_POISONED_DENSE_SESSION_ACTIVE and relative in NS2_POISONED_DENSE_SESSION_BLOBS:
        return NS2_POISONED_DENSE_SESSION_BLOBS[relative]
    if NS2_DENSE_GMMU_POISON_ACTIVE and relative in NS2_DENSE_GMMU_POISON_BLOBS:
        return NS2_DENSE_GMMU_POISON_BLOBS[relative]
    if NS2_MKW_SPARSE_REPLACE_ACTIVE and relative in NS2_MKW_SPARSE_REPLACE_BLOBS:
        return NS2_MKW_SPARSE_REPLACE_BLOBS[relative]
    if NS2_GPFIFO_INLINE_ACTIVE and relative in NS2_GPFIFO_INLINE_BLOBS:
        return NS2_GPFIFO_INLINE_BLOBS[relative]
    if NS2_LEGACY_GPFIFO_ALLOC_ACTIVE and relative in NS2_LEGACY_GPFIFO_ALLOC_BLOBS:
        return NS2_LEGACY_GPFIFO_ALLOC_BLOBS[relative]
    if NS2_DECODER_SESSION_MOVE_ACTIVE and relative in NS2_DECODER_SESSION_MOVE_BLOBS:
        return NS2_DECODER_SESSION_MOVE_BLOBS[relative]
    if NS2_GPFIFO_ALLOC_GUARD_ACTIVE and relative in NS2_GPFIFO_ALLOC_GUARD_BLOBS:
        return NS2_GPFIFO_ALLOC_GUARD_BLOBS[relative]
    if NS2_GSV_MOVE_OWNERS_ACTIVE and relative in NS2_GSV_MOVE_OWNERS_BLOBS:
        return NS2_GSV_MOVE_OWNERS_BLOBS[relative]
    if NS2_P0_BOOTSTRAP_ACTIVE and relative in NS2_P0_BOOTSTRAP_BLOBS:
        return NS2_P0_BOOTSTRAP_BLOBS[relative]
    if NS2_CHANNEL_EVENT_ACTIVE and relative in NS2_CHANNEL_EVENT_BLOBS:
        return NS2_CHANNEL_EVENT_BLOBS[relative]
    if NS2_GPFIFO_FLAGS_ACTIVE and relative in NS2_GPFIFO_FLAGS_BLOBS:
        return NS2_GPFIFO_FLAGS_BLOBS[relative]
    if NS2_CHANNEL_ERROR_ACTIVE and relative in NS2_CHANNEL_ERROR_BLOBS:
        return NS2_CHANNEL_ERROR_BLOBS[relative]
    if NS2_PREEMPTION_CTA_ACTIVE and relative in NS2_PREEMPTION_CTA_BLOBS:
        return NS2_PREEMPTION_CTA_BLOBS[relative]
    if NS2_ENCODER_FAIL_CLOSED_ACTIVE and relative in NS2_ENCODER_FAIL_CLOSED_BLOBS:
        # Current blob was verified above against the exact pinned tree.
        return NS2_ENCODER_FAIL_CLOSED_BLOBS[relative]
    # Successor blobs have already been individually sealed above. Historical
    # receipt replay may revisit them after normalizing gitlink_vendor_pin to
    # c74; return only those exact authenticated successor identities.
    successor_exact = {}
    if shipping_vendor_pin in {
        "3a97e47a0cfe94ec55227af363d8c289de59d4f8",
        "3de91cf284c8ef234c757c046998c4f48165c59a",
        "2fd07582db57fdddc67e6fd56cec16624a902c6a",
        "4411fc172eef84080ab7de23158349bbe7d08f88",
        "0c4eafeb9f197e76a1f0bb06038ef9bbf2c7565d",
        "bc6baf037ac3304d4ba81cf7589f7e52e8fa8ae0",
        "546e1aa34d2ff183dd4c737f9da8fbf4a62be24e",
        "f65ccc439534ffd9ce0a307b23bd511b4e32857a",
        "4e6a966508e718d02526d4d220e112591536f28c",
        "2d07b5e65baf35c82d0b0e557617aefe730a10b1",
        "7baf9cc07c6aceee185032544d964f04a2fed108",
        "1f8a3bbaa7fc33118e63ebef829202d825475bfe",
    }:
        successor_exact.update({
            "encore-active/ns2-runtime/gpu_session/core/hle/service/am/service/gpu_session.cpp": "be33e5fa3a6f7f2ed4eb4aeac6c7650b204cfa17",
            "encore-active/ns2-runtime/gpu_session/core/hle/service/am/service/gpu_session.h": "be6f4f16c9407876ff0f8259cc1c777d05e8056f",
            "encore-active/ns2-runtime/hle/core/hle/service/am/service/gpu_session_protocol.h": "b4298a1231aee0f3b675861211bbcf30260dd033",
            "tests/ns2_gpu_partition_new_sdk_source.py": "e41711b1822cadffd3b699befb55aa4e9e2f1433",
        })
    if shipping_vendor_pin in {
        "3de91cf284c8ef234c757c046998c4f48165c59a",
        "2fd07582db57fdddc67e6fd56cec16624a902c6a",
        "4411fc172eef84080ab7de23158349bbe7d08f88",
        "0c4eafeb9f197e76a1f0bb06038ef9bbf2c7565d",
        "bc6baf037ac3304d4ba81cf7589f7e52e8fa8ae0",
        "546e1aa34d2ff183dd4c737f9da8fbf4a62be24e",
        "f65ccc439534ffd9ce0a307b23bd511b4e32857a",
        "4e6a966508e718d02526d4d220e112591536f28c",
        "2d07b5e65baf35c82d0b0e557617aefe730a10b1",
        "7baf9cc07c6aceee185032544d964f04a2fed108",
        "1f8a3bbaa7fc33118e63ebef829202d825475bfe",
    }:
        successor_exact.update({
            "encore-active/ns2-runtime/gpu_session/core/hle/service/am/service/gpu_worker.cpp": "1042668b48e71020ee777e0ec0aef6b1606edaf0",
            "encore-active/ns2-runtime/gpu_session/core/hle/service/am/service/gpu_worker.h": "0a4ded1cba3fc0ed8163bda05cc32956f6216aa4",
            "encore-active/ns2-runtime/hle/core/hle/service/am/service/gpu_memory_registration.h": "c104301566467d973ebf0634580a0fbc4a44daf9",
            "tests/ns2_gpu_identity_mapping_source.py": "599f766e76fab45314a77c2fa573b8229cf83de1",
        })
    if shipping_vendor_pin in {"2fd07582db57fdddc67e6fd56cec16624a902c6a", "4411fc172eef84080ab7de23158349bbe7d08f88"}:
        successor_exact.update({
            "encore-active/ns2-runtime/graphics_supervisor/core/hle/service/am/service/graphics_supervisor.cpp": "fbbb41f8e281d276bad2174d3d6fe43c05c66b92",
            "encore-active/ns2-runtime/graphics_supervisor/core/hle/service/am/service/graphics_supervisor.h": "2701836cbc4448bb6c934c53db49f051de76988c",
            "encore-active/ns2-runtime/hle/core/hle/service/am/service/graphics_supervisor_protocol.h": "8b0cfe00cf9f6f450e69cbf4d55ee84336d4d0b8",
            "tests/ns2_syncpt_bootstrap_source.py": "688f868e999a707557852730996888c8d6234e56",
        })
    if shipping_vendor_pin in {"4411fc172eef84080ab7de23158349bbe7d08f88", "0c4eafeb9f197e76a1f0bb06038ef9bbf2c7565d", "bc6baf037ac3304d4ba81cf7589f7e52e8fa8ae0", "546e1aa34d2ff183dd4c737f9da8fbf4a62be24e", "f65ccc439534ffd9ce0a307b23bd511b4e32857a", "4e6a966508e718d02526d4d220e112591536f28c", "2d07b5e65baf35c82d0b0e557617aefe730a10b1", "7baf9cc07c6aceee185032544d964f04a2fed108", "1f8a3bbaa7fc33118e63ebef829202d825475bfe"}:
        successor_exact.update({
            "encore-active/ns2-runtime/graphics_supervisor/core/hle/service/am/service/graphics_supervisor.cpp": "8f2ebf9bbf9c23284a0f9e7b788b571485c1135d",
            "encore-active/ns2-runtime/graphics_supervisor/core/hle/service/am/service/graphics_supervisor.h": "2d424fb67dc984c1af3a1ee1a0d46c59f704bddf",
            "encore-active/ns2-runtime/hle/core/hle/service/am/service/graphics_supervisor_protocol.h": "221173de57178d5408f3c8116fbf4202d26c86f7",
            "tests/ns2_syncpt_bootstrap_source.py": "56ab0b57f677683de33dbf6365efa5a1fdfc3875",
        })
    if shipping_vendor_pin in {"0c4eafeb9f197e76a1f0bb06038ef9bbf2c7565d", "bc6baf037ac3304d4ba81cf7589f7e52e8fa8ae0", "546e1aa34d2ff183dd4c737f9da8fbf4a62be24e", "f65ccc439534ffd9ce0a307b23bd511b4e32857a", "4e6a966508e718d02526d4d220e112591536f28c", "2d07b5e65baf35c82d0b0e557617aefe730a10b1", "7baf9cc07c6aceee185032544d964f04a2fed108", "1f8a3bbaa7fc33118e63ebef829202d825475bfe"}:
        successor_exact.update({
            "encore-active/ns2-runtime/gpu_session/core/hle/service/am/service/gpu_worker.cpp": "0a6c1b39483d8efcff0690f4f677d594863bf09e",
            "encore-active/ns2-runtime/gpu_session/core/hle/service/am/service/gpu_worker.h": "676f9f0391e73147f241fc0ece20e9f0560d4e33",
            "encore-active/ns2-runtime/hle/core/hle/service/am/service/gpu_memory_registration.h": "47e133e9bec766bbd2d840b215e8e447b70e93f8",
            "tests/ns2_gpu_identity_mapping_source.py": "eca64dbb3bd0ac01b62d7229612a8efcf45d567d",
        })
    if shipping_vendor_pin in {"bc6baf037ac3304d4ba81cf7589f7e52e8fa8ae0", "546e1aa34d2ff183dd4c737f9da8fbf4a62be24e", "f65ccc439534ffd9ce0a307b23bd511b4e32857a", "4e6a966508e718d02526d4d220e112591536f28c", "2d07b5e65baf35c82d0b0e557617aefe730a10b1", "7baf9cc07c6aceee185032544d964f04a2fed108", "1f8a3bbaa7fc33118e63ebef829202d825475bfe"}:
        successor_exact.update({
            "encore-active/ns2-runtime/hle/core/hle/service/nvdrv/devices/native_gpu_submission.h": "9aa4b802c2245cad7b251fff3bc708a906db533d",
            "encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/nvhost_gpu.h": "af7df2ba70bbf16d3715257c8c3a2b471ed26227",
            "encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/nvhost_gpu.cpp": "24096d0848b560d5e7befe979ecaebd1dcc730ae",
            "tests/p0_ns2_gpfifo_preimpl_trace_source.py": "4e7a4fd77cd96ff650edfc74f6a841b266ca2152",
        })
    if shipping_vendor_pin in {"546e1aa34d2ff183dd4c737f9da8fbf4a62be24e", "f65ccc439534ffd9ce0a307b23bd511b4e32857a", "4e6a966508e718d02526d4d220e112591536f28c", "2d07b5e65baf35c82d0b0e557617aefe730a10b1", "7baf9cc07c6aceee185032544d964f04a2fed108", "1f8a3bbaa7fc33118e63ebef829202d825475bfe"}:
        successor_exact.update({
            "encore-active/ns2-runtime/gpu_session/core/hle/service/am/service/gpu_worker.cpp": "ccccfb99af3ffd03ae1a3119b89c7121cc73ac91",
            "encore-active/ns2-runtime/gpu_session/core/hle/service/am/service/gpu_worker.h": "2aa6d526e7c876d11adc180f546935503be54a4a",
            "encore-active/ns2-runtime/hle/core/hle/service/am/service/gpu_memory_registration.h": "e6223aa74605e50aab30e1fd0a0bf8f3b75c4ecf",
            "tests/ns2_gpu_identity_mapping_source.py": "0572833e4e63c5fe7af728c66beea7df53e4219e",
        })
    if shipping_vendor_pin in {"4e6a966508e718d02526d4d220e112591536f28c", "2d07b5e65baf35c82d0b0e557617aefe730a10b1", "7baf9cc07c6aceee185032544d964f04a2fed108", "1f8a3bbaa7fc33118e63ebef829202d825475bfe"}:
        successor_exact.update({
            "encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/nvhost_gpu.h":
                "8b22d4e16ba0e3d0e73cc3af9faace2447d3fd9b",
            "encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/nvhost_gpu.cpp":
                "81bac0bb0c1be0be6ed0aca81931fc593b948044",
            "tests/p0_ns2_gpfifo_preimpl_trace_source.py":
                "d78aaea83009616131bcaf68bfb67fd12fe2e575",
        })
    if shipping_vendor_pin in {"2d07b5e65baf35c82d0b0e557617aefe730a10b1", "7baf9cc07c6aceee185032544d964f04a2fed108", "1f8a3bbaa7fc33118e63ebef829202d825475bfe"}:
        successor_exact.update({
            "encore-active/ns2-runtime/graphics_supervisor/core/hle/service/am/service/graphics_supervisor.cpp":
                "66b5bc32c9286ec2462edd09804a670691ac91d8",
            "encore-active/ns2-runtime/graphics_supervisor/core/hle/service/am/service/graphics_supervisor.h":
                "56e9ddf8b73d4db22559e73fe8d3506bdaa84a1c",
            "tests/ns2_syncpt_bootstrap_source.py":
                "08894a7985e96f4478501dd69aceb56b214b0306",
        })
    if shipping_vendor_pin in {"7baf9cc07c6aceee185032544d964f04a2fed108", "1f8a3bbaa7fc33118e63ebef829202d825475bfe"}:
        successor_exact.update({
            "sources/eden/src/core/hle/service/nvdrv/devices/nx2_stub_device.h":
                "f287b62c0e001af3d3262a6a253c076a0941b2f8",
            "tests/ns2_nvhost_unknown_node_fallback_source.py":
                "3094b555b32840f613c7567e10787c4f73c668e5",
        })
    if shipping_vendor_pin == "1f8a3bbaa7fc33118e63ebef829202d825475bfe":
        successor_exact.update({
            "sources/eden/src/core/hle/service/nvdrv/devices/nx2_stub_device.h":
                "587ebbd2a129ab38e3c0ec49e2121eb1768bbaa4",
            "tests/ns2_nvhost_unknown_node_fallback_source.py":
                "abdf48b2423a0abdd3d2085c2f3ae9b3a93db9ea",
        })
    if relative in successor_exact:
        return successor_exact[relative]
    if gitlink_vendor_pin in {"08972732d0402fa455a4982ed5ffd5d9f2c7e83c", "c74fb345ac3d8fa752f403369827a432f3503fb5"}:
        exact = {
            "encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.cpp": "a0f73ad8a4a156e41896264038f96e5e0e893fbb",
            "tests/ns2_gpu_identity_mapping_source.py": (
                "5803d1c7d5b23d4833f020b6445505e16fcca8f9" if gitlink_vendor_pin == "c74fb345ac3d8fa752f403369827a432f3503fb5"
                else "0a598e5a77f7de39091fcc175fc40363e8637d88"),
            "encore-active/ns2-runtime/gpu_session/core/hle/service/am/service/gpu_session.cpp": "2d9d71e81d7f6e1dbbb8ef37e3f601d68abc88d3",
            "tests/ns2_gpu_partition_new_sdk_source.py": "ceaf06587daab525a8229c8186de891e9d3ea9aa",
            "encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/nvhost_gpu.h": "3dec2b4990d1c8c5cb45d7c5fe87c12a62dff09f",
            "encore-active/eden-core/overrides/native-tiling/video_core/memory_manager.h": "c83087f816eb9956a4f7ed565794a2b643512e87",
            "encore-active/eden-core/guest-bridge/memory_manager.h": "c670df3eadf42d9d4a5e1d7d3b2f5c674f83bf7e",
            "tests/ns2_syncpoint_shim_source.py": "83636703c71ec50c8e6052f9bc9bec9ed8f54a61",
            "encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.h": "24a07c5c5e6810d8d100a73d7ad7da83fd698cbe",
            "encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/native_gpu_va_layout.h": "5f3ebf592001119c9686657600066d62db344524",
            "encore-active/ns2-runtime/nvdrv/core/hle/service/nvdrv/devices/nvhost_ctrl_gpu.cpp": "f57925efd8b032f64b7bc979f8fe4f2765fb66bf",
            "encore-active/ns2-runtime/graphics_supervisor/core/hle/service/am/service/graphics_supervisor.cpp": "9d5e1666c015db72c3fa4f8ea501d7c68f826991",
            "encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/nvhost_gpu.cpp": "ec99bc8bd379bf51ce4971d1d21d5a0d16d6fed4",
            "tests/p0_ns2_gpfifo_preimpl_trace_source.py": "35d31053361f392f6dd2a70b4afee28f36cbf56b",
        }
        if relative in exact:
            return exact[relative]
    if gitlink_vendor_pin == "457f9501c52fcf6ce2aaca967757c0eb9e452f58":
        exact = {
            "encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.cpp": "a0f73ad8a4a156e41896264038f96e5e0e893fbb",
            "tests/ns2_gpu_identity_mapping_source.py": "0a598e5a77f7de39091fcc175fc40363e8637d88",
            "encore-active/ns2-runtime/gpu_session/core/hle/service/am/service/gpu_session.cpp": "2d9d71e81d7f6e1dbbb8ef37e3f601d68abc88d3",
            "tests/ns2_gpu_partition_new_sdk_source.py": "ceaf06587daab525a8229c8186de891e9d3ea9aa",
            "encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/nvhost_gpu.h": "3dec2b4990d1c8c5cb45d7c5fe87c12a62dff09f",
            "encore-active/eden-core/overrides/native-tiling/video_core/memory_manager.h": "c83087f816eb9956a4f7ed565794a2b643512e87",
            "encore-active/eden-core/guest-bridge/memory_manager.h": "c670df3eadf42d9d4a5e1d7d3b2f5c674f83bf7e",
            "encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.h": "24a07c5c5e6810d8d100a73d7ad7da83fd698cbe",
            "encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/native_gpu_va_layout.h": "5f3ebf592001119c9686657600066d62db344524",
            "encore-active/ns2-runtime/nvdrv/core/hle/service/nvdrv/devices/nvhost_ctrl_gpu.cpp": "f57925efd8b032f64b7bc979f8fe4f2765fb66bf",
            "encore-active/ns2-runtime/graphics_supervisor/core/hle/service/am/service/graphics_supervisor.cpp": "9d5e1666c015db72c3fa4f8ea501d7c68f826991",
            "encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/nvhost_gpu.cpp": "176e9501256347d2c8afbe60d225c130c3c67e6e",
            "tests/ns2_syncpoint_shim_source.py": "83636703c71ec50c8e6052f9bc9bec9ed8f54a61",
        }
        if relative in exact:
            return exact[relative]
    if gitlink_vendor_pin == "95ed29da0eb91af4561154ec3688968959185b9b":
        exact = {
            "encore-active/ns2-runtime/gpu_session/core/hle/service/am/service/gpu_session.cpp": "2d9d71e81d7f6e1dbbb8ef37e3f601d68abc88d3",
            "tests/ns2_gpu_partition_new_sdk_source.py": "ceaf06587daab525a8229c8186de891e9d3ea9aa",
            "encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/nvhost_gpu.cpp": "ba1c9923a576e9ddc25ddcbf9df628925be45109",
            "encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/nvhost_gpu.h": "3dec2b4990d1c8c5cb45d7c5fe87c12a62dff09f",
            "encore-active/eden-core/overrides/native-tiling/video_core/memory_manager.h": "c83087f816eb9956a4f7ed565794a2b643512e87",
            "encore-active/eden-core/guest-bridge/memory_manager.h": "c670df3eadf42d9d4a5e1d7d3b2f5c674f83bf7e",
            "tests/ns2_syncpoint_shim_source.py": "0f696fbe1b02e677a74c6c41fee79d4b00f0f682",
            "encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.h": "24a07c5c5e6810d8d100a73d7ad7da83fd698cbe",
            "encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/native_gpu_va_layout.h": "5f3ebf592001119c9686657600066d62db344524",
            "encore-active/ns2-runtime/nvdrv/core/hle/service/nvdrv/devices/nvhost_ctrl_gpu.cpp": "f57925efd8b032f64b7bc979f8fe4f2765fb66bf",
            "encore-active/ns2-runtime/graphics_supervisor/core/hle/service/am/service/graphics_supervisor.cpp": "9d5e1666c015db72c3fa4f8ea501d7c68f826991",
            "encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.cpp": "a0f73ad8a4a156e41896264038f96e5e0e893fbb",
            "tests/ns2_gpu_identity_mapping_source.py": "0a598e5a77f7de39091fcc175fc40363e8637d88",
        }
        if relative in exact:
            return exact[relative]
    if gitlink_vendor_pin == "615ec1b7a73bb26dcff8525cf543aafff04ecbf0":
        exact = {
            "encore-active/ns2-runtime/gpu_session/core/hle/service/am/service/gpu_session.cpp": "2d9d71e81d7f6e1dbbb8ef37e3f601d68abc88d3",
            "tests/ns2_gpu_partition_new_sdk_source.py": "ceaf06587daab525a8229c8186de891e9d3ea9aa",
            "encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/nvhost_gpu.cpp": "ba1c9923a576e9ddc25ddcbf9df628925be45109",
            "encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/nvhost_gpu.h": "3dec2b4990d1c8c5cb45d7c5fe87c12a62dff09f",
            "encore-active/eden-core/overrides/native-tiling/video_core/memory_manager.h": "c83087f816eb9956a4f7ed565794a2b643512e87",
            "encore-active/eden-core/guest-bridge/memory_manager.h": "c670df3eadf42d9d4a5e1d7d3b2f5c674f83bf7e",
            "tests/ns2_syncpoint_shim_source.py": "0f696fbe1b02e677a74c6c41fee79d4b00f0f682",
            "encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.h": "24a07c5c5e6810d8d100a73d7ad7da83fd698cbe",
            "encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/native_gpu_va_layout.h": "5f3ebf592001119c9686657600066d62db344524",
            "encore-active/ns2-runtime/nvdrv/core/hle/service/nvdrv/devices/nvhost_ctrl_gpu.cpp": "f57925efd8b032f64b7bc979f8fe4f2765fb66bf",
            "encore-active/ns2-runtime/graphics_supervisor/core/hle/service/am/service/graphics_supervisor.cpp": "9d5e1666c015db72c3fa4f8ea501d7c68f826991",
            "encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.cpp": "0d64b35fdfef15ee0bb8fa8a9b7d59c6ec17fbcb",
            "tests/ns2_gpu_identity_mapping_source.py": "f782842092f5bfc2847cbfbdf18d9efdb368af53",
        }
        if relative in exact:
            return exact[relative]
    if gitlink_vendor_pin == "a773cfa1a5cd95285eab7e8dd4d21ceef848a0a0":
        exact = {
            "encore-active/ns2-runtime/gpu_session/core/hle/service/am/service/gpu_session.cpp": "2d9d71e81d7f6e1dbbb8ef37e3f601d68abc88d3",
            "tests/ns2_gpu_partition_new_sdk_source.py": "ceaf06587daab525a8229c8186de891e9d3ea9aa",
            "encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/nvhost_gpu.cpp": "ba1c9923a576e9ddc25ddcbf9df628925be45109",
            "encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/nvhost_gpu.h": "3dec2b4990d1c8c5cb45d7c5fe87c12a62dff09f",
            "encore-active/eden-core/overrides/native-tiling/video_core/memory_manager.h": "c83087f816eb9956a4f7ed565794a2b643512e87",
            "encore-active/eden-core/guest-bridge/memory_manager.h": "c670df3eadf42d9d4a5e1d7d3b2f5c674f83bf7e",
            "tests/ns2_syncpoint_shim_source.py": "0f696fbe1b02e677a74c6c41fee79d4b00f0f682",
            "encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.h": "24a07c5c5e6810d8d100a73d7ad7da83fd698cbe",
            "encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/native_gpu_va_layout.h": "5f3ebf592001119c9686657600066d62db344524",
            "encore-active/ns2-runtime/nvdrv/core/hle/service/nvdrv/devices/nvhost_ctrl_gpu.cpp": "f57925efd8b032f64b7bc979f8fe4f2765fb66bf",
            "encore-active/ns2-runtime/graphics_supervisor/core/hle/service/am/service/graphics_supervisor.cpp": "9d5e1666c015db72c3fa4f8ea501d7c68f826991",
            "encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.cpp": "cbb03b8eed8fb061328b6d86e9d773e015c9cf07",
            "tests/ns2_gpu_identity_mapping_source.py": "4d17e7a7c18c8d6e5f87596da87ce6738336efd5",
        }
        if relative in exact:
            return exact[relative]
    if gitlink_vendor_pin == "754dc4110ad1e13ea0237e5826599f97d0ccd2f9":
        sealed = {
            "encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/nvhost_gpu.cpp": "ba1c9923a576e9ddc25ddcbf9df628925be45109",
            "encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/nvhost_gpu.h": "3dec2b4990d1c8c5cb45d7c5fe87c12a62dff09f",
            "encore-active/eden-core/overrides/native-tiling/video_core/memory_manager.h": "c83087f816eb9956a4f7ed565794a2b643512e87",
            "encore-active/eden-core/guest-bridge/memory_manager.h": "c670df3eadf42d9d4a5e1d7d3b2f5c674f83bf7e",
            "tests/ns2_syncpoint_shim_source.py": "0f696fbe1b02e677a74c6c41fee79d4b00f0f682",
            "encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.cpp": "604aa850609983b61a3e5033b4fa1740b3d64c70",
            "tests/ns2_gpu_identity_mapping_source.py": "a2afbf6710977594ee27f2abce17446483cc0d59",
            "encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.h": "24a07c5c5e6810d8d100a73d7ad7da83fd698cbe",
            "encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/native_gpu_va_layout.h": "5f3ebf592001119c9686657600066d62db344524",
            "encore-active/ns2-runtime/nvdrv/core/hle/service/nvdrv/devices/nvhost_ctrl_gpu.cpp": "f57925efd8b032f64b7bc979f8fe4f2765fb66bf",
            "encore-active/ns2-runtime/graphics_supervisor/core/hle/service/am/service/graphics_supervisor.cpp": "9d5e1666c015db72c3fa4f8ea501d7c68f826991",
            "encore-active/ns2-runtime/gpu_session/core/hle/service/am/service/gpu_session.cpp": "2d9d71e81d7f6e1dbbb8ef37e3f601d68abc88d3",
            "tests/ns2_gpu_partition_new_sdk_source.py": "ceaf06587daab525a8229c8186de891e9d3ea9aa",
        }
        if relative in sealed:
            return sealed[relative]
    if gitlink_vendor_pin == "d8c1595f187b24b434533c02fe4085a2905f34aa":
        exact = {
            "encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.cpp": "604aa850609983b61a3e5033b4fa1740b3d64c70",
            "tests/ns2_gpu_identity_mapping_source.py": "a2afbf6710977594ee27f2abce17446483cc0d59",
            "encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.h": "24a07c5c5e6810d8d100a73d7ad7da83fd698cbe",
            "encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/native_gpu_va_layout.h": "5f3ebf592001119c9686657600066d62db344524",
            "encore-active/ns2-runtime/nvdrv/core/hle/service/nvdrv/devices/nvhost_ctrl_gpu.cpp": "f57925efd8b032f64b7bc979f8fe4f2765fb66bf",
            "encore-active/ns2-runtime/graphics_supervisor/core/hle/service/am/service/graphics_supervisor.cpp": "9d5e1666c015db72c3fa4f8ea501d7c68f826991",
            "encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/nvhost_gpu.cpp": "ba1c9923a576e9ddc25ddcbf9df628925be45109",
            "encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/nvhost_gpu.h": "3dec2b4990d1c8c5cb45d7c5fe87c12a62dff09f",
            "encore-active/eden-core/overrides/native-tiling/video_core/memory_manager.h": "c83087f816eb9956a4f7ed565794a2b643512e87",
            "encore-active/eden-core/guest-bridge/memory_manager.h": "c670df3eadf42d9d4a5e1d7d3b2f5c674f83bf7e",
            "tests/ns2_syncpoint_shim_source.py": "0f696fbe1b02e677a74c6c41fee79d4b00f0f682",
        }
        if relative in exact:
            return exact[relative]
    if gitlink_vendor_pin == "9edb09cf0a720c6b22fe092efd21cc9891225a48":
        matched = {
            "encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.cpp": "604aa850609983b61a3e5033b4fa1740b3d64c70",
            "tests/ns2_gpu_identity_mapping_source.py": "a2afbf6710977594ee27f2abce17446483cc0d59",
            "encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.h": "24a07c5c5e6810d8d100a73d7ad7da83fd698cbe",
            "encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/native_gpu_va_layout.h": "5f3ebf592001119c9686657600066d62db344524",
            "encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/nvhost_gpu.cpp": "5be598819854a43c929d570d0a0f6234c1a829e8",
            "encore-active/ns2-runtime/nvdrv/core/hle/service/nvdrv/devices/nvhost_ctrl_gpu.cpp": "f57925efd8b032f64b7bc979f8fe4f2765fb66bf",
            "encore-active/ns2-runtime/graphics_supervisor/core/hle/service/am/service/graphics_supervisor.cpp": "9d5e1666c015db72c3fa4f8ea501d7c68f826991",
        }
        if relative in matched:
            return matched[relative]
    if gitlink_vendor_pin == "7a4ddd589b7a20d75a1a6019a67a16c5f2d39bc5":
        latest = {
            "encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.cpp": "85b765ca5871f56a7f9f1f883841775d260e121b",
            "tests/ns2_gpu_identity_mapping_source.py": "0cf04759ddff657d4a9892e0932bbac789655cc5",
            "encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.h": "24a07c5c5e6810d8d100a73d7ad7da83fd698cbe",
            "encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/native_gpu_va_layout.h": "5f3ebf592001119c9686657600066d62db344524",
            "encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/nvhost_gpu.cpp": "5be598819854a43c929d570d0a0f6234c1a829e8",
            "encore-active/ns2-runtime/nvdrv/core/hle/service/nvdrv/devices/nvhost_ctrl_gpu.cpp": "f57925efd8b032f64b7bc979f8fe4f2765fb66bf",
            "encore-active/ns2-runtime/graphics_supervisor/core/hle/service/am/service/graphics_supervisor.cpp": "9d5e1666c015db72c3fa4f8ea501d7c68f826991",
        }
        if relative in latest:
            return latest[relative]
    if gitlink_vendor_pin == "1ca2828bfccd0d5c8a903f3c503480f1fc1b6ddc":
        prepared = {
            "encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.cpp": "284e754886ef59e73120cfa2b8fb691eddc51707",
            "encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.h": "24a07c5c5e6810d8d100a73d7ad7da83fd698cbe",
            "encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/native_gpu_va_layout.h": "5f3ebf592001119c9686657600066d62db344524",
            "encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/nvhost_gpu.cpp": "5be598819854a43c929d570d0a0f6234c1a829e8",
            "encore-active/ns2-runtime/nvdrv/core/hle/service/nvdrv/devices/nvhost_ctrl_gpu.cpp": "f57925efd8b032f64b7bc979f8fe4f2765fb66bf",
            "encore-active/ns2-runtime/graphics_supervisor/core/hle/service/am/service/graphics_supervisor.cpp": "9d5e1666c015db72c3fa4f8ea501d7c68f826991",
            "tests/ns2_gpu_identity_mapping_source.py": "256ad36db2562e4895842a0c2034a83311bbfcbc",
        }
        if relative in prepared:
            return prepared[relative]
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

# This exact vendor revision repairs NIFM's handler table and names nine
# fail-closed GPU-session commands. The shader/renderer owners still pass
# the immutable per-file checks below, so qualify this *one* new pin.
REVIEWED_PINS.add("716e069f212b89b6fd13af56b0677343cf41ba07")
REVIEWED_PINS.add("6c15ec8d1143eb1ae3092a2b984f0bc5bfcc364b")  # immutable runtime, shutdown test provenance only
# Current shutdown successor on top of the reviewed demand-zero graph.
# Seal every source changed after ee64; do not blanket-accept later vendors.
if actual_vendor_pin in {"603e0d5c70b04fa84a19cca8f580ed1bdb230be0", "593bc9ee6ddfcf38e488325ccf318f1a0a109d8e", "6b48e6734e738306dd57ceed8be9b003631eb8cb", "d554e257ae82db66d9542f472dcde067510bfa1f", "93c3dd6c86627e91999f965c45c05cd8e50e17eb", "eb9a454db4d21a3aff2642c72eea3ca01bf2b3bb", "93da3b707ef147385380eb0690e0d93fc8e907ad", "a6240909b823492d9ff20070c09387a732d83007"}:
    for relative, expected in {
        "encore-active/eden-core/src/core/hle/service/server_manager.cpp":
            "dd6dc2d8359ac14d36526a9dc88905cabf36a798",
        "encore-active/eden-core/src/core/hle/service/sm/sm.cpp":
            "494ee50d2880a491b07c2b981193df1a686c696a",
        "tests/shutdown_teardown_lifetime_source.py":
            "3f46b0dbed50dcbde294a05693decd602dffa194",
    }.items():
        raw=(V/relative).read_bytes()
        digest=hashlib.sha1(b"blob "+str(len(raw)).encode()+bytes([0])+raw).hexdigest()
        assert digest == expected, ("Current PS5 teardown successor drift", relative, digest)
    if actual_vendor_pin in {"593bc9ee6ddfcf38e488325ccf318f1a0a109d8e", "6b48e6734e738306dd57ceed8be9b003631eb8cb", "d554e257ae82db66d9542f472dcde067510bfa1f", "93c3dd6c86627e91999f965c45c05cd8e50e17eb", "eb9a454db4d21a3aff2642c72eea3ca01bf2b3bb", "93da3b707ef147385380eb0690e0d93fc8e907ad", "a6240909b823492d9ff20070c09387a732d83007"}:
        relative="tests/ns2_syncpt_bootstrap_source.py"
        raw=(V/relative).read_bytes()
        digest=hashlib.sha1(b"blob "+str(len(raw)).encode()+bytes([0])+raw).hexdigest()
        expected_syncpt = (
            "07ee9ba7ca648ae51128f865fa568bde1ffb2916"
            if actual_vendor_pin in {"93c3dd6c86627e91999f965c45c05cd8e50e17eb", "eb9a454db4d21a3aff2642c72eea3ca01bf2b3bb", "93da3b707ef147385380eb0690e0d93fc8e907ad", "a6240909b823492d9ff20070c09387a732d83007"}
            else "74b84b9015d6642ff5627e2897d39f5e1d093e68"
        )
        assert digest == expected_syncpt, (
            "GSV 1121 parity test successor drift", digest)
        if actual_vendor_pin in {"93c3dd6c86627e91999f965c45c05cd8e50e17eb", "eb9a454db4d21a3aff2642c72eea3ca01bf2b3bb", "93da3b707ef147385380eb0690e0d93fc8e907ad", "a6240909b823492d9ff20070c09387a732d83007"}:
            # 93c3dd6c changes exactly this selected GSV C++ owner plus the
            # source receipt above: replace the nonexistent IPC result with
            # the already-used Kernel fail-closed result.
            relative = (
                "encore-active/ns2-runtime/graphics_supervisor/core/hle/service/"
                "am/service/graphics_supervisor.cpp"
            )
            raw = (V / relative).read_bytes()
            gsv_digest = hashlib.sha1(
                b"blob " + str(len(raw)).encode() + bytes([0]) + raw
            ).hexdigest()
            assert gsv_digest == "79855d2276973977b58d523df5b53fc4229759a4", (
                "Compiled GSV gpu-time successor drift", gsv_digest)
        if actual_vendor_pin in {"eb9a454db4d21a3aff2642c72eea3ca01bf2b3bb", "93da3b707ef147385380eb0690e0d93fc8e907ad", "a6240909b823492d9ff20070c09387a732d83007"}:
            relative = "encore-active/eden-vulkan/vk_pipeline_cache_cost.cpp"
            raw = (V / relative).read_bytes()
            pipeline_digest = hashlib.sha1(
                b"blob " + str(len(raw)).encode() + bytes([0]) + raw
            ).hexdigest()
            assert pipeline_digest == "d222fb5565cdf8db30c6d3d464f107ff26a042c8", (
                "FC27 NONE render-target successor drift", pipeline_digest)
        if actual_vendor_pin == "93da3b707ef147385380eb0690e0d93fc8e907ad":
            relative = "tests/fc27_xmad_pointer_fold_host.py"
            raw = (V / relative).read_bytes()
            test_digest = hashlib.sha1(
                b"blob " + str(len(raw)).encode() + bytes([0]) + raw
            ).hexdigest()
            assert test_digest == "8a69d898cf68fe359270dd0523617384bb2fddb2", (
                "FC27 NONE qualification test drift", test_digest)
        if actual_vendor_pin == "a6240909b823492d9ff20070c09387a732d83007":
            for relative, expected in {
                "tests/fc27_dynamic_texture_static_sampler_host.py":
                    "27b78519f5f8f59673b82c812a862ca025aac490",
                "tests/fc27_xmad_pointer_fold_host.py":
                    "47191b5b8f668cdbf892aeedb557b8a2bb9228ac",
                "tests/ns1_r23_35_attribute_handle.py":
                    "9f327a63be711c9121d98a45510b79f389e96c47",
                "tests/ps5_recent_prewarm_receipt.py":
                    "319db8ec1935b13150bc0fa94bc4cfe2ec380976",
            }.items():
                raw = (V / relative).read_bytes()
                receipt_digest = hashlib.sha1(
                    b"blob " + str(len(raw)).encode() + bytes([0]) + raw
                ).hexdigest()
                assert receipt_digest == expected, (
                    "FC27 unified cache receipt test drift", relative, receipt_digest)
    if actual_vendor_pin in {"6b48e6734e738306dd57ceed8be9b003631eb8cb", "d554e257ae82db66d9542f472dcde067510bfa1f", "93c3dd6c86627e91999f965c45c05cd8e50e17eb", "eb9a454db4d21a3aff2642c72eea3ca01bf2b3bb", "93da3b707ef147385380eb0690e0d93fc8e907ad", "a6240909b823492d9ff20070c09387a732d83007"}:
        # Exact successor of 593bc9ee: only the two native guest memory
        # backends changed, making ZeroBlock generation-neutral for NS1/NS2.
        for relative, expected in {
            "encore-active/eden-core/src/core/memory_native_a32.cpp":
                "3e3b07af30032ce14ca68e8482986d2f1a7201da",
            "encore-active/eden-core/src/core/memory_native_standard.cpp":
                "96663d23335fe7448712a15416003a975a3f8023",
        }.items():
            raw=(V/relative).read_bytes()
            digest=hashlib.sha1(b"blob "+str(len(raw)).encode()+bytes([0])+raw).hexdigest()
            assert digest == expected, ("NS1/NS2 sparse memory successor drift", relative, digest)
        if actual_vendor_pin in {"d554e257ae82db66d9542f472dcde067510bfa1f", "93c3dd6c86627e91999f965c45c05cd8e50e17eb", "eb9a454db4d21a3aff2642c72eea3ca01bf2b3bb", "93da3b707ef147385380eb0690e0d93fc8e907ad", "a6240909b823492d9ff20070c09387a732d83007"}:
            relative = "tests/ns2_r457_kernel_slab_precommit_host.py"
            raw = (V / relative).read_bytes()
            digest = hashlib.sha1(
                b"blob " + str(len(raw)).encode() + bytes([0]) + raw
            ).hexdigest()
            assert digest == "ca72b7015432803495cbd57986085bb9ed0f6953", (
                "Sparse OOM qualification test-only successor drift", digest)
        # Replay every unaffected historical receipt through the qualified
        # predecessor after sealing the C++ delta and optional test-only receipt.
        selected = "593bc9ee6ddfcf38e488325ccf318f1a0a109d8e"
REVIEWED_PINS.add("603e0d5c70b04fa84a19cca8f580ed1bdb230be0")
REVIEWED_PINS.add("593bc9ee6ddfcf38e488325ccf318f1a0a109d8e")
REVIEWED_PINS.add("6b48e6734e738306dd57ceed8be9b003631eb8cb")
REVIEWED_PINS.add("d554e257ae82db66d9542f472dcde067510bfa1f")
REVIEWED_PINS.add("93c3dd6c86627e91999f965c45c05cd8e50e17eb")
REVIEWED_PINS.add("eb9a454db4d21a3aff2642c72eea3ca01bf2b3bb")
REVIEWED_PINS.add("93da3b707ef147385380eb0690e0d93fc8e907ad")
REVIEWED_PINS.add("a6240909b823492d9ff20070c09387a732d83007")
# PS5 23/11 FC27 shutdown + NS2 NUP/AM diagnostics on the latest qualified
# vendor main: read the four changed full blobs and immutable sparse owners
# before admitting the updated gitlink to the historical receipts.
if shipping_vendor_pin == "0390980a5752808dfba7b8edaa7d113cc4e4e6eb":
    verified_changed_and_unchanged={
    "encore-active/eden-core/src/core/hle/service/sm/sm.cpp": "34c7c85f1476a3ba819ad20b8a4f8150cca86e16",
    "encore-active/eden-core/src/core/hle/service/sm/sm.h": "7069439e66a6f28ffa56229e08906a21222e2801",
    "encore-active/ns2-runtime/process/core/core.cpp": "83fc9a903b05ed9fd096c35102db54a966d736c2",
    "encore-active/ns2-runtime/am/core/hle/service/am/service/application_functions.cpp": "9bfaa26664361994902d5b7f73d6a41ff0eadb07",
    "encore-active/ns2-runtime/sparse-residency/core/hle/kernel/k_memory_manager.cpp": "2b5be4eba2500da2993db2ed1c86d44ddfa5554f",
    "encore-active/ns2-runtime/sparse-residency/core/hle/kernel/init/init_slab_setup.cpp": "130eb7bd53e29b816bb81fec3fa053a584cd4b6e",
    "encore-active/eden-core/overrides/core/device_memory_manager.inc": "daf493ce6e863397ec44bfae467c4f7533570477",
}
    for relative, expected_blob in verified_changed_and_unchanged.items():
        raw=(V/relative).read_bytes()
        digest=hashlib.sha1(b"blob "+str(len(raw)).encode()+bytes([0])+raw).hexdigest()
        assert digest == expected_blob,("NS1/NS2 latest reviewed vendor drift",relative,digest)
REVIEWED_PINS.add("0390980a5752808dfba7b8edaa7d113cc4e4e6eb")
# Lichii/Eglantine source-only AM WindowSystem + LM hashes with preserved NS1 ABI;
# retain the full reviewed FC27/P0 vendor graph tests below.
REVIEWED_PINS.add("273680a5b33bff15c9ca12685cfadb2aa15ff9f1")
# The native NS2 GPU exception-mask reader is the only 273680 -> 84b997
# delta. Verify the exact selected C++ blob before admitting this successor;
# all other vendor-owner receipts remain unchanged and are replayed below.
if actual_vendor_pin in {"bfdf39014db15f237a16d4a50e6cdfd68bdd87b8", "4626d87be155c0b42904610323098c1205515450", "c32704e63844449b1c18a03deb2cd92939999b90", "fab5ebbfda09ebd3fc414b3127e135c66025ccb8", "acb42e2a2b18fee17673d07e06b2f29709de2fb5", "99df05ff50a7a4a9591c17b08f4ed0f8cb0374a3", "04e252186aa42bacde0899e0c9224035c83a6b0d", "44f5b75bc93bcea146ad6fba3ac294405ae8709b", "70789b12dea4d72ce9e7f054c5b6f552ec488f5d", "9db97fb12db1a390d6b2410f0c18333aa31e37da"}:
    for relative, expected in {
        "encore-active/ns2-runtime/ampere/shader_recompiler/frontend/ampere/lower_to_maxwell.h": "9169e95ec14559aa6466c68b7d1e1cd3f9e69557",
        "encore-active/ns2-runtime/hle/core/hle/service/am/service/application_proxy_service.cpp": "a07dae606312e673bdbff5110fbf81d4ce307776",
        "encore-active/ns2-runtime/hle/core/hle/service/am/service/application_proxy_service.h": "7aab2ba6235b33b91819ea78a006129183194194",
        "tests/ns2_early_hle_services_source.py": "a8885d094315e22f9bf0a3c41c969f31463815cb",
    }.items():
        raw = (V / relative).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        assert actual == expected, ("bfdf exact reviewed delta drift", relative, actual)
    REVIEWED_PINS.add("bfdf39014db15f237a16d4a50e6cdfd68bdd87b8")
REVIEWED_PINS.add("4626d87be155c0b42904610323098c1205515450")
REVIEWED_PINS.add("c32704e63844449b1c18a03deb2cd92939999b90")
REVIEWED_PINS.add("fab5ebbfda09ebd3fc414b3127e135c66025ccb8")
# FC27 shader parallelism successor: only these three active runtime owners
# changed over fab5. Seal them before admitting the new vendor pin; all other
# P0/P1/NS2 receipts inherit fab5 byte-for-byte.
if actual_vendor_pin in {"acb42e2a2b18fee17673d07e06b2f29709de2fb5", "99df05ff50a7a4a9591c17b08f4ed0f8cb0374a3", "04e252186aa42bacde0899e0c9224035c83a6b0d", "44f5b75bc93bcea146ad6fba3ac294405ae8709b", "70789b12dea4d72ce9e7f054c5b6f552ec488f5d", "9db97fb12db1a390d6b2410f0c18333aa31e37da"}:
    for relative, expected in {
        "encore-active/eden-core/src/video_core/shader_environment.cpp":
            ("2ed48cbbcc9b1c5ee963c78410a6e5caeeafaab1" if actual_vendor_pin in {"70789b12dea4d72ce9e7f054c5b6f552ec488f5d", "9db97fb12db1a390d6b2410f0c18333aa31e37da", "60fa67b98286bd84bd591987c5690ae9b15bda3f", "bf981e9d39d4a908d0d5b6f8407cca814c609bdb", "8026fcca228d0feda62ffd9625e16ee0429d621e", "887bf44af34999e8b6c5b63dc7c01c6c13b82c8f", "1a928783cce2c2692d8fe9fd958400a2de060bbf", "9632ac089f8b2d89a6856a42e8fb55206cdba1fa", "b5c6f089a6aecd321d08a40238f3cd502f505b26", "dc9f5f95b1f784bb358d6480e53de7247d61d777", "a441295022b23834f8531c54d2b0965f84023278", "7c5d5220dd4df4a531418458ab623ef86c41348c", "44540549ee9a65eb8078e271f43ccded0e8e984f", "d63d82dfb9c2afbacac4c9dc1491f743fb083d52", "d634b381d85dae30492dd6291fc4e6e96143f363", "692e9819a7a1f1b818bf3739c72d8e5252cae661", "166e473e120a86a6edcd32a975ffe19b45ffdd42", "3522d8578fbcd7b46d2a439d5d718dfb570beb7b"} else "253771ae3f57ec04afa4e41ef081f9d730246276"),
        "encore-active/eden-vulkan/include/video_core/renderer_vulkan/vk_pipeline_cache.h":
            "fcf26ecce586e3cedc17abe6d111ee35f76ad705",
        "encore-active/eden-vulkan/vk_pipeline_cache_cost.cpp":
            ("ad07512d129667a617b49b448d898c5756c99025"
             if actual_vendor_pin in {"70789b12dea4d72ce9e7f054c5b6f552ec488f5d", "9db97fb12db1a390d6b2410f0c18333aa31e37da", "60fa67b98286bd84bd591987c5690ae9b15bda3f", "bf981e9d39d4a908d0d5b6f8407cca814c609bdb", "8026fcca228d0feda62ffd9625e16ee0429d621e", "887bf44af34999e8b6c5b63dc7c01c6c13b82c8f", "1a928783cce2c2692d8fe9fd958400a2de060bbf", "9632ac089f8b2d89a6856a42e8fb55206cdba1fa", "b5c6f089a6aecd321d08a40238f3cd502f505b26", "dc9f5f95b1f784bb358d6480e53de7247d61d777", "a441295022b23834f8531c54d2b0965f84023278", "7c5d5220dd4df4a531418458ab623ef86c41348c", "44540549ee9a65eb8078e271f43ccded0e8e984f", "d63d82dfb9c2afbacac4c9dc1491f743fb083d52", "d634b381d85dae30492dd6291fc4e6e96143f363", "692e9819a7a1f1b818bf3739c72d8e5252cae661", "166e473e120a86a6edcd32a975ffe19b45ffdd42", "3522d8578fbcd7b46d2a439d5d718dfb570beb7b"}
             else "52470b6160f6049801d963960adf6952c79a45cf"
             if actual_vendor_pin == "44f5b75bc93bcea146ad6fba3ac294405ae8709b"
             else "b28a190e92ca80b0385148a0b558828353326f12"),
    }.items():
        raw = (V / relative).read_bytes()
        actual = hashlib.sha1(
            b"blob " + str(len(raw)).encode() + bytes([0]) + raw
        ).hexdigest()
        assert actual == expected, ("parallel shader owner drift", relative, actual)
if actual_vendor_pin in {"99df05ff50a7a4a9591c17b08f4ed0f8cb0374a3", "04e252186aa42bacde0899e0c9224035c83a6b0d", "44f5b75bc93bcea146ad6fba3ac294405ae8709b", "70789b12dea4d72ce9e7f054c5b6f552ec488f5d", "9db97fb12db1a390d6b2410f0c18333aa31e37da"}:
    relative = "encore-active/ps5-mesa/src/vulkan/wsi/wsi_common_videoout.c"
    raw = (V / relative).read_bytes()
    actual = hashlib.sha1(
        b"blob " + str(len(raw)).encode() + bytes([0]) + raw
    ).hexdigest()
    assert actual == "89c1e891c90d1357552bfbeeef27f91d4fbce5ee", (
        "integrated VideoOut handoff owner drift", actual)
if actual_vendor_pin in {"44f5b75bc93bcea146ad6fba3ac294405ae8709b", "70789b12dea4d72ce9e7f054c5b6f552ec488f5d", "9db97fb12db1a390d6b2410f0c18333aa31e37da"}:
    for relative, expected in {
            "encore-active/eden-vulkan/vk_pipeline_cache_cost.cpp": ("ad07512d129667a617b49b448d898c5756c99025" if actual_vendor_pin in {"70789b12dea4d72ce9e7f054c5b6f552ec488f5d", "9db97fb12db1a390d6b2410f0c18333aa31e37da", "60fa67b98286bd84bd591987c5690ae9b15bda3f", "bf981e9d39d4a908d0d5b6f8407cca814c609bdb", "8026fcca228d0feda62ffd9625e16ee0429d621e", "887bf44af34999e8b6c5b63dc7c01c6c13b82c8f", "1a928783cce2c2692d8fe9fd958400a2de060bbf", "9632ac089f8b2d89a6856a42e8fb55206cdba1fa", "b5c6f089a6aecd321d08a40238f3cd502f505b26", "dc9f5f95b1f784bb358d6480e53de7247d61d777", "a441295022b23834f8531c54d2b0965f84023278", "7c5d5220dd4df4a531418458ab623ef86c41348c", "44540549ee9a65eb8078e271f43ccded0e8e984f", "d63d82dfb9c2afbacac4c9dc1491f743fb083d52", "d634b381d85dae30492dd6291fc4e6e96143f363", "692e9819a7a1f1b818bf3739c72d8e5252cae661", "166e473e120a86a6edcd32a975ffe19b45ffdd42", "3522d8578fbcd7b46d2a439d5d718dfb570beb7b"} else "52470b6160f6049801d963960adf6952c79a45cf"),
            "tests/fc27_dynamic_texture_static_sampler_host.py": "b30c6b062108ec3414bfc5a5ff4a6fe9b22be331",
            "tests/fc27_xmad_pointer_fold_host.py": "09e566db7ddd141ef6554a1e0b8f649d7551ed6e",
            "tests/ns1_r23_35_attribute_handle.py": "b6a7c5468048987883b7fa12f8803e193e456c2e",
            "tests/ps5_recent_prewarm_receipt.py": "10837a358096cfa5a43550043e6fff27635247cb",
    }.items():
        raw = (V / relative).read_bytes()
        actual = hashlib.sha1(
            b"blob " + str(len(raw)).encode() + bytes([0]) + raw
        ).hexdigest()
        assert actual == expected, ("keyed shader timing successor drift", relative, actual)
REVIEWED_PINS.add("acb42e2a2b18fee17673d07e06b2f29709de2fb5")
REVIEWED_PINS.add("99df05ff50a7a4a9591c17b08f4ed0f8cb0374a3")
REVIEWED_PINS.add("04e252186aa42bacde0899e0c9224035c83a6b0d")
REVIEWED_PINS.add("44f5b75bc93bcea146ad6fba3ac294405ae8709b")
REVIEWED_PINS.add("70789b12dea4d72ce9e7f054c5b6f552ec488f5d")
REVIEWED_PINS.add("9db97fb12db1a390d6b2410f0c18333aa31e37da")
if actual_vendor_pin in {"84b9975726092a32d1cb2aa714b96e4f5f85d7c4", "84ec89ce112b83603b2095a9f6bb785f8e999ef6", "97fa38381d9ce23b63b3bf3751615dc254ab3634", "b099bd7cbefaa1a35d6626d4fd3161afcefa1b48", "bfdf39014db15f237a16d4a50e6cdfd68bdd87b8", "4626d87be155c0b42904610323098c1205515450", "c32704e63844449b1c18a03deb2cd92939999b90", "fab5ebbfda09ebd3fc414b3127e135c66025ccb8", "acb42e2a2b18fee17673d07e06b2f29709de2fb5", "99df05ff50a7a4a9591c17b08f4ed0f8cb0374a3", "04e252186aa42bacde0899e0c9224035c83a6b0d", "44f5b75bc93bcea146ad6fba3ac294405ae8709b", "70789b12dea4d72ce9e7f054c5b6f552ec488f5d", "9db97fb12db1a390d6b2410f0c18333aa31e37da"}:
    relative = "encore-active/ns2-runtime/nvdrv/core/hle/service/nvdrv/devices/nvhost_ctrl_gpu.cpp"
    raw = (V / relative).read_bytes()
    actual_blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
    assert actual_blob == ("332ae7800c2639a1185ed417bf3a5a9508058d86" if actual_vendor_pin in {"84ec89ce112b83603b2095a9f6bb785f8e999ef6", "97fa38381d9ce23b63b3bf3751615dc254ab3634", "b099bd7cbefaa1a35d6626d4fd3161afcefa1b48", "bfdf39014db15f237a16d4a50e6cdfd68bdd87b8", "4626d87be155c0b42904610323098c1205515450", "c32704e63844449b1c18a03deb2cd92939999b90", "fab5ebbfda09ebd3fc414b3127e135c66025ccb8", "acb42e2a2b18fee17673d07e06b2f29709de2fb5", "99df05ff50a7a4a9591c17b08f4ed0f8cb0374a3", "04e252186aa42bacde0899e0c9224035c83a6b0d", "44f5b75bc93bcea146ad6fba3ac294405ae8709b", "70789b12dea4d72ce9e7f054c5b6f552ec488f5d", "9db97fb12db1a390d6b2410f0c18333aa31e37da"} else "32ba64b4b83848c0cd8f82af52429e3dea42609f"), ("Native NVDRV native query owner drift", actual_blob)
REVIEWED_PINS.add("84b9975726092a32d1cb2aa714b96e4f5f85d7c4")
REVIEWED_PINS.add("84ec89ce112b83603b2095a9f6bb785f8e999ef6")
REVIEWED_PINS.add("97fa38381d9ce23b63b3bf3751615dc254ab3634")
REVIEWED_PINS.add("b099bd7cbefaa1a35d6626d4fd3161afcefa1b48")
REVIEWED_PINS.add("bfdf39014db15f237a16d4a50e6cdfd68bdd87b8")
REVIEWED_PINS.add("4626d87be155c0b42904610323098c1205515450")
REVIEWED_PINS.add("c32704e63844449b1c18a03deb2cd92939999b90")
REVIEWED_PINS.add("fab5ebbfda09ebd3fc414b3127e135c66025ccb8")
REVIEWED_PINS.add("acb42e2a2b18fee17673d07e06b2f29709de2fb5")
REVIEWED_PINS.add("99df05ff50a7a4a9591c17b08f4ed0f8cb0374a3")
REVIEWED_PINS.add("04e252186aa42bacde0899e0c9224035c83a6b0d")
REVIEWED_PINS.add("44f5b75bc93bcea146ad6fba3ac294405ae8709b")
REVIEWED_PINS.add("70789b12dea4d72ce9e7f054c5b6f552ec488f5d")
REVIEWED_PINS.add("9db97fb12db1a390d6b2410f0c18333aa31e37da")
# Nov23 stabilization successor: runtime shutdown/cache/fidelity plus guest-frame pacing.
# Seal every changed selected owner exactly; all older audit receipts remain immutable.
if actual_vendor_pin in {"60fa67b98286bd84bd591987c5690ae9b15bda3f", "bf981e9d39d4a908d0d5b6f8407cca814c609bdb", "8026fcca228d0feda62ffd9625e16ee0429d621e", "887bf44af34999e8b6c5b63dc7c01c6c13b82c8f", "1a928783cce2c2692d8fe9fd958400a2de060bbf", "9632ac089f8b2d89a6856a42e8fb55206cdba1fa", "b5c6f089a6aecd321d08a40238f3cd502f505b26", "dc9f5f95b1f784bb358d6480e53de7247d61d777", "a441295022b23834f8531c54d2b0965f84023278", "7c5d5220dd4df4a531418458ab623ef86c41348c", "44540549ee9a65eb8078e271f43ccded0e8e984f", "d63d82dfb9c2afbacac4c9dc1491f743fb083d52", "d634b381d85dae30492dd6291fc4e6e96143f363", "692e9819a7a1f1b818bf3739c72d8e5252cae661", "166e473e120a86a6edcd32a975ffe19b45ffdd42", "3522d8578fbcd7b46d2a439d5d718dfb570beb7b"}:
    for relative, expected in {
        "encore-active/eden-core/overrides/core/gpu_dirty_memory_manager.h": "7769e314fbefeb8393e6d11b115c88bc0a8a0e58",
        "encore-active/eden-core/src/core/hle/kernel/kernel_dev.cpp": "48c48318f2d6587bc8d7dc4ca7bbe9f73d107c6e",
        "encore-active/eden-core/src/core/hle/kernel/kernel_standard.cpp": "6ca8f7a848a2c39cba906374049b55badf418d46",
        "encore-active/eden-core/src/video_core/buffer_cache/buffer_cache.h": "7f07e392ea0cc828d862da29d32ada1ebc3966aa",
        "encore-active/eden-core/src/video_core/gpu_vulkan.cpp": "f083c985451563dcfe387d1bc61f54bd02ed762e",
        "encore-active/ns2-astc/include/video_core/texture_cache/texture_cache.h": ("27ea4e0e665d3f94e173c1335cb19211efc03646" if actual_vendor_pin in {"d63d82dfb9c2afbacac4c9dc1491f743fb083d52", "d634b381d85dae30492dd6291fc4e6e96143f363", "692e9819a7a1f1b818bf3739c72d8e5252cae661", "166e473e120a86a6edcd32a975ffe19b45ffdd42", "3522d8578fbcd7b46d2a439d5d718dfb570beb7b"} else "5c6d015cf207d63de31b577411972606145d9f2e"),
        "encore-active/ns2-runtime/process/core/core.cpp": "0e0aadb72c8de5bb2c66ce9105b1dd2d381b5f98",
        "sources/eden/src/core/hle/service/am/applet_manager.cpp": "f16d7c2585595d91e89ff34f3223e0b8fe905220",
        "sources/eden/src/core/hle/service/am/applet_manager.h": "9724a70f172cbb48130f5c1bfa8703cac119a3cb",
        "encore-active/eden-vulkan/include/video_core/renderer_vulkan/frame_pacer.h": "c3f6f99dd427fb9fd0acb84bb50ba88dc25d9a89",
        "encore-active/eden-vulkan/include/video_core/renderer_vulkan/vk_present_manager.h": "5e4b021612130d5e297b38f34dec2ed3295ad143",
        "encore-active/eden-vulkan/include/video_core/renderer_vulkan/vk_scheduler.h": ("0a150f61ea637fc8ce9849379da7ebf241deb6d4" if actual_vendor_pin in {"7c5d5220dd4df4a531418458ab623ef86c41348c", "44540549ee9a65eb8078e271f43ccded0e8e984f", "d63d82dfb9c2afbacac4c9dc1491f743fb083d52", "d634b381d85dae30492dd6291fc4e6e96143f363", "692e9819a7a1f1b818bf3739c72d8e5252cae661", "166e473e120a86a6edcd32a975ffe19b45ffdd42", "3522d8578fbcd7b46d2a439d5d718dfb570beb7b"} else "c82ae5986c5028795093ff8573c33068d12c6de3"),
        "encore-active/eden-vulkan/include/video_core/renderer_vulkan/vk_swapchain.h": "c4df1ab813495b8014e0eda5ed4bcd8fb0be855c",
        "encore-active/eden-vulkan/vulkan_present_manager.cpp": "87575a627c3bf2d8280d9ad7916d86988177e67b",
        "encore-active/eden-vulkan/vulkan_swapchain.cpp": "135aed0cc6a30caf43caefdd2d6a81256c359bfc",
    }.items():
        raw = (V / relative).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        assert actual == expected, ("Nov23 stabilization owner drift", relative, actual)
    if actual_vendor_pin in {"bf981e9d39d4a908d0d5b6f8407cca814c609bdb", "8026fcca228d0feda62ffd9625e16ee0429d621e", "887bf44af34999e8b6c5b63dc7c01c6c13b82c8f", "1a928783cce2c2692d8fe9fd958400a2de060bbf", "9632ac089f8b2d89a6856a42e8fb55206cdba1fa", "b5c6f089a6aecd321d08a40238f3cd502f505b26", "dc9f5f95b1f784bb358d6480e53de7247d61d777", "a441295022b23834f8531c54d2b0965f84023278", "7c5d5220dd4df4a531418458ab623ef86c41348c", "44540549ee9a65eb8078e271f43ccded0e8e984f", "d63d82dfb9c2afbacac4c9dc1491f743fb083d52", "d634b381d85dae30492dd6291fc4e6e96143f363", "692e9819a7a1f1b818bf3739c72d8e5252cae661", "166e473e120a86a6edcd32a975ffe19b45ffdd42", "3522d8578fbcd7b46d2a439d5d718dfb570beb7b"}:
        reviewed_blob("tests/fc27_xmad_pointer_fold_host.py",
                      "11bd172c540b19eeb9a920afb6213c6e95d111f9")
    if actual_vendor_pin in {"8026fcca228d0feda62ffd9625e16ee0429d621e", "887bf44af34999e8b6c5b63dc7c01c6c13b82c8f", "1a928783cce2c2692d8fe9fd958400a2de060bbf", "9632ac089f8b2d89a6856a42e8fb55206cdba1fa", "b5c6f089a6aecd321d08a40238f3cd502f505b26", "dc9f5f95b1f784bb358d6480e53de7247d61d777", "a441295022b23834f8531c54d2b0965f84023278", "7c5d5220dd4df4a531418458ab623ef86c41348c", "44540549ee9a65eb8078e271f43ccded0e8e984f", "d63d82dfb9c2afbacac4c9dc1491f743fb083d52", "d634b381d85dae30492dd6291fc4e6e96143f363", "692e9819a7a1f1b818bf3739c72d8e5252cae661", "166e473e120a86a6edcd32a975ffe19b45ffdd42", "3522d8578fbcd7b46d2a439d5d718dfb570beb7b"}:
        reviewed_blob("tests/fc27_dynamic_texture_static_sampler_host.py",
                      "756534a44355dafa43809ac012ccb69a0de35660")
    if actual_vendor_pin in {"887bf44af34999e8b6c5b63dc7c01c6c13b82c8f", "1a928783cce2c2692d8fe9fd958400a2de060bbf", "9632ac089f8b2d89a6856a42e8fb55206cdba1fa", "b5c6f089a6aecd321d08a40238f3cd502f505b26", "dc9f5f95b1f784bb358d6480e53de7247d61d777", "a441295022b23834f8531c54d2b0965f84023278", "7c5d5220dd4df4a531418458ab623ef86c41348c", "44540549ee9a65eb8078e271f43ccded0e8e984f", "d63d82dfb9c2afbacac4c9dc1491f743fb083d52", "d634b381d85dae30492dd6291fc4e6e96143f363", "692e9819a7a1f1b818bf3739c72d8e5252cae661", "166e473e120a86a6edcd32a975ffe19b45ffdd42", "3522d8578fbcd7b46d2a439d5d718dfb570beb7b"}:
        reviewed_blob("tests/shutdown_teardown_lifetime_source.py",
                      "b15fd52a0a3b5e39d5f80c71b88d7357a81026fb")
        reviewed_blob("tests/shutdown_general_channel_lifetime_source.py",
                      "fee3dfced900d8a7bba70ab6748451db2a2b6e79")
    if actual_vendor_pin in {"1a928783cce2c2692d8fe9fd958400a2de060bbf", "9632ac089f8b2d89a6856a42e8fb55206cdba1fa", "b5c6f089a6aecd321d08a40238f3cd502f505b26", "dc9f5f95b1f784bb358d6480e53de7247d61d777", "a441295022b23834f8531c54d2b0965f84023278", "7c5d5220dd4df4a531418458ab623ef86c41348c", "44540549ee9a65eb8078e271f43ccded0e8e984f", "d63d82dfb9c2afbacac4c9dc1491f743fb083d52", "d634b381d85dae30492dd6291fc4e6e96143f363", "692e9819a7a1f1b818bf3739c72d8e5252cae661", "166e473e120a86a6edcd32a975ffe19b45ffdd42", "3522d8578fbcd7b46d2a439d5d718dfb570beb7b"}:
        reviewed_blob("tests/ns1_r23_18_tir_host.py", "9ec2e122bee4c7ef3a0889fbf5e8202ae9516339" if actual_vendor_pin in {"d63d82dfb9c2afbacac4c9dc1491f743fb083d52", "d634b381d85dae30492dd6291fc4e6e96143f363", "692e9819a7a1f1b818bf3739c72d8e5252cae661", "166e473e120a86a6edcd32a975ffe19b45ffdd42", "3522d8578fbcd7b46d2a439d5d718dfb570beb7b"} else "005280fde5bbd862d64a4def0d17d90a35bbe5e9")
    if actual_vendor_pin in {"d634b381d85dae30492dd6291fc4e6e96143f363", "692e9819a7a1f1b818bf3739c72d8e5252cae661", "166e473e120a86a6edcd32a975ffe19b45ffdd42", "3522d8578fbcd7b46d2a439d5d718dfb570beb7b"}:
        raw = (V / "tests/fc27_deferred_page_protection_host.py").read_bytes()
        assert hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest() == "172989eea550754d8ca19191cb99eb5c08546ab5"
    REVIEWED_PINS.add(actual_vendor_pin)
if actual_vendor_pin == "042204fde8e5b74aa5048c6213a8af4450d26fe5":
    # libounce-reviewed direct successor: only decoder lease + GPU worker 213 ABI changed.
    assert subprocess.check_output(["git", "-C", str(V), "rev-parse", "HEAD^{tree}"], text=True).strip() == "08ff1d3ef45b03cbe3396079bcb91fa5dce4f160"
    for relative, expected_blob in {
        "encore-active/ns2-runtime/gpu_session/core/hle/service/am/service/gpu_worker.cpp": "64bc5c0728dc023ff2a2793cb424560f36ddcfed",
        "encore-active/ns2-runtime/graphics_supervisor/core/hle/service/am/service/graphics_supervisor.cpp": "aabe3379c6d2a2961f4725423c11fb149b10d9ea",
        "encore-active/ns2-runtime/graphics_supervisor/core/hle/service/am/service/graphics_supervisor.h": "ca001d8f2bf787f01026000199a9bbf4b87f61c2",
    }.items():
        raw=(V/relative).read_bytes()
        actual=hashlib.sha1(b"blob "+str(len(raw)).encode()+bytes([0])+raw).hexdigest()
        assert actual == expected_blob, ("libounce NS2 successor drift", relative, actual)
    REVIEWED_PINS.add(actual_vendor_pin)
if actual_vendor_pin in {"294442004543aeecc5f3c61cc1b73b2feaff2f92", "53d0ad1f9d50b9f1a72cbecacdacdff7fb4e69eb", "7e137d362f9679125726ef4876355a09d788795e", "973d45ae0da5d9612d30900e39118d67d039b31a", "6b8fd06606f12be187f73e8809e56a49864794f9", "652f88555e8bb16ffeffd9d1fa3d0c49e7925dfc", "38e19d4be0d99bbba35558af2c0620cd9b46f12e", "4c51642038c4a3cc04c0f8f0b8267b17aafd4045", "881f6fb23c818ecfc387d2b134e1cd7328fc5995", "d8155325107dbbb1f8ef44f75553595fe4c8ec8c", "101eae5edb76fefc40b039009eb35bbaaae99386", "3abd88bc1a3c334f53f345998b72e9cf8ae87abf"}:
    if actual_vendor_pin in {"7e137d362f9679125726ef4876355a09d788795e", "973d45ae0da5d9612d30900e39118d67d039b31a", "6b8fd06606f12be187f73e8809e56a49864794f9", "652f88555e8bb16ffeffd9d1fa3d0c49e7925dfc", "38e19d4be0d99bbba35558af2c0620cd9b46f12e", "4c51642038c4a3cc04c0f8f0b8267b17aafd4045", "881f6fb23c818ecfc387d2b134e1cd7328fc5995", "d8155325107dbbb1f8ef44f75553595fe4c8ec8c", "101eae5edb76fefc40b039009eb35bbaaae99386", "3abd88bc1a3c334f53f345998b72e9cf8ae87abf"}:
        raw = (V / "encore-active/eden-core/src/video_core/memory_manager.cpp").read_bytes()
        assert hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest() == "9a9479580fb2037cc49fe2ed5c6a284331a78b97"
    if actual_vendor_pin in {"53d0ad1f9d50b9f1a72cbecacdacdff7fb4e69eb", "7e137d362f9679125726ef4876355a09d788795e", "973d45ae0da5d9612d30900e39118d67d039b31a", "6b8fd06606f12be187f73e8809e56a49864794f9", "652f88555e8bb16ffeffd9d1fa3d0c49e7925dfc", "38e19d4be0d99bbba35558af2c0620cd9b46f12e", "4c51642038c4a3cc04c0f8f0b8267b17aafd4045", "881f6fb23c818ecfc387d2b134e1cd7328fc5995", "d8155325107dbbb1f8ef44f75553595fe4c8ec8c", "101eae5edb76fefc40b039009eb35bbaaae99386", "3abd88bc1a3c334f53f345998b72e9cf8ae87abf"}:
        raw = (V / "encore-active/ns2-runtime/nvdrv/core/hle/service/nvdrv/devices/native_gpu_characteristics.h").read_bytes()
        assert hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest() == "f6217651bf15d13e5be80c0b1b0b76679f02949b"
    if actual_vendor_pin in {"6b8fd06606f12be187f73e8809e56a49864794f9", "652f88555e8bb16ffeffd9d1fa3d0c49e7925dfc", "38e19d4be0d99bbba35558af2c0620cd9b46f12e", "4c51642038c4a3cc04c0f8f0b8267b17aafd4045", "881f6fb23c818ecfc387d2b134e1cd7328fc5995", "d8155325107dbbb1f8ef44f75553595fe4c8ec8c", "101eae5edb76fefc40b039009eb35bbaaae99386", "3abd88bc1a3c334f53f345998b72e9cf8ae87abf"}:
        raw = (V / "encore-active/ns2-runtime/gpu_session/core/hle/service/am/service/gpu_worker.cpp").read_bytes()
        expected_worker = "e6d85e1fb3b7749cf578a73bd446bd2e8d32223c" if actual_vendor_pin in {"d8155325107dbbb1f8ef44f75553595fe4c8ec8c", "101eae5edb76fefc40b039009eb35bbaaae99386", "3abd88bc1a3c334f53f345998b72e9cf8ae87abf"} else "e61820cc289ce24670c4b1056d34914dfe2eaf26" if actual_vendor_pin == "881f6fb23c818ecfc387d2b134e1cd7328fc5995" else "ed0c89a2cfe5fcedb941cc57f4ed294b8cf610c4" if actual_vendor_pin in {"652f88555e8bb16ffeffd9d1fa3d0c49e7925dfc", "38e19d4be0d99bbba35558af2c0620cd9b46f12e", "4c51642038c4a3cc04c0f8f0b8267b17aafd4045", "881f6fb23c818ecfc387d2b134e1cd7328fc5995", "d8155325107dbbb1f8ef44f75553595fe4c8ec8c", "101eae5edb76fefc40b039009eb35bbaaae99386", "3abd88bc1a3c334f53f345998b72e9cf8ae87abf"} else "0f2244f61fcac38d4379d7dda9efaf447d0eea46"
        assert hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest() == expected_worker
    if actual_vendor_pin in {"d8155325107dbbb1f8ef44f75553595fe4c8ec8c", "101eae5edb76fefc40b039009eb35bbaaae99386", "3abd88bc1a3c334f53f345998b72e9cf8ae87abf"}:
        for relative, expected in {
            "encore-active/eden-core/src/core/hle/service/nvdrv/core/nvmap.cpp": "365e436ac270e0474403d54ceddc41c68d78bf1b",
            "sources/eden/src/core/hle/service/nvdrv/core/nvmap.h": "f89b21297d77a41a6e937f6946f03ac542165834",
        }.items():
            raw = (V / relative).read_bytes()
            assert hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest() == expected
    if actual_vendor_pin in {"101eae5edb76fefc40b039009eb35bbaaae99386", "3abd88bc1a3c334f53f345998b72e9cf8ae87abf"}:
        for relative, expected in {
            "encore-active/ns2-runtime/graphics_supervisor/core/hle/service/am/service/graphics_supervisor.cpp": "d25dddc6c3aaf149483552b1ea9b68b4daa8dbe8",
            "encore-active/ns2-runtime/graphics_supervisor/core/hle/service/am/service/graphics_supervisor.h": "e18d391ef7d38a6dfb64feffc796caad212f16bc",
            "tests/ns2_syncpt_bootstrap_source.py": "efbe43477d0068cff8cab5a18de5378aa1fc409d",
        }.items():
            raw = (V / relative).read_bytes()
            assert hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest() == expected
    if actual_vendor_pin == "3abd88bc1a3c334f53f345998b72e9cf8ae87abf":
        for relative, expected in {
            "encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/nvhost_gpu.cpp": "25aa385480b28a3d828da034222795ac1f150e94",
            "encore-active/ns2-runtime/gpu_dispatch/video_core/dma_pusher.h": "7965c196bff1364f64e747f152bcc314b1db3658",
            "encore-active/eden-core/src/video_core/dma_pusher.cpp": "a8c95c51445ddafc2b8f42a92099359aae33e836",
            "encore-active/eden-sync/overrides/h05-syncpoint/core/hle/service/nvdrv/core/syncpoint_manager.h": "624bd4d84d4a02d509430df651c46997254f8e59",
            "encore-active/eden-sync/src/core/hle/service/nvdrv/core/syncpoint_manager.cpp": "6b09b35a07aabfff0d79df4f098e4f5ea6f5631d",
            "tests/p0_ns2_gpfifo_preimpl_trace_source.py": "3a5c6d75a828b5d867a8dbffbf6337d1c460f135",
        }.items():
            raw = (V / relative).read_bytes()
            assert hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest() == expected, relative
    # Exact VM import, channel health, descriptor QueryEvent and image format
    # successor; keep the previous FC27 and sparse owners byte-identical.
    assert subprocess.check_output(["git", "-C", str(V), "rev-parse", "HEAD^{tree}"], text=True).strip() == ("b82ce9bb3b543bf85d535bdfdfb6d725fe88be56" if actual_vendor_pin == "3abd88bc1a3c334f53f345998b72e9cf8ae87abf" else "8e42496a1f01a94cc6b17f57eee6ebdff2698ff6" if actual_vendor_pin == "101eae5edb76fefc40b039009eb35bbaaae99386" else "a6451d095d44e8b9968635320d3bba34d5722fa5" if actual_vendor_pin == "d8155325107dbbb1f8ef44f75553595fe4c8ec8c" else "ba3ad593fb37ac3dc62f2c8b6064328c55cabb3b" if actual_vendor_pin == "881f6fb23c818ecfc387d2b134e1cd7328fc5995" else "77add4864dbadc2c2246c339b215c3d79b40a549" if actual_vendor_pin == "4c51642038c4a3cc04c0f8f0b8267b17aafd4045" else "a27660a134453d2895e23d5c56ac64e6f12d9960" if actual_vendor_pin == "38e19d4be0d99bbba35558af2c0620cd9b46f12e" else "57a6ef072ad018954d493cb9064b5c722a5af827" if actual_vendor_pin == "652f88555e8bb16ffeffd9d1fa3d0c49e7925dfc" else "6ecf485d48b3c29c5e058de99a09c5c495cd537d" if actual_vendor_pin == "6b8fd06606f12be187f73e8809e56a49864794f9" else "1d991da378f711312faf34125f1d4cfe1378bcaa" if actual_vendor_pin == "973d45ae0da5d9612d30900e39118d67d039b31a" else "6861e052a9824450c7eeaa91b53334c153ca9865" if actual_vendor_pin == "7e137d362f9679125726ef4876355a09d788795e" else "a21aa2b63cfb9cae4dd9ba386982c3bd57a7ef1f" if actual_vendor_pin == "53d0ad1f9d50b9f1a72cbecacdacdff7fb4e69eb" else "50ba35725b57b59cae76a67c7c1d4ba6ad894e2f")
    for relative, expected_blob in {
        "encore-active/ns2-runtime/gpu_session/core/hle/service/am/service/gpu_session.cpp": "c082c25491f3783543e787fce43197d8b3fe78d3",
        "encore-active/ns2-runtime/gpu_session/core/hle/service/am/service/gpu_worker_shared.cpp": "ae2708f662937a5069afe355425cf43e424fcd9c",
        "encore-active/ns2-runtime/gpu_session/core/hle/service/am/service/gpu_worker_shared.h": "74b87878c2a73d6918b7f3e4144419fc07a0e15f",
        "encore-active/ns2-runtime/hle/core/hle/service/am/service/native_image_layout.h": "e5aa688d9e685b9de2a4204a8da8cdb0c6eedff0",
        "encore-active/ns2-runtime/hle/core/hle/service/nvdrv/devices/native_gpu_process_registry.h": "248581eb2c87a5b5eaa9bdb7e4ad095e860584ce",
        "encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.cpp": ("5320f2c99c77b1c178175f19b7996000f5de3286" if actual_vendor_pin in {"652f88555e8bb16ffeffd9d1fa3d0c49e7925dfc", "38e19d4be0d99bbba35558af2c0620cd9b46f12e", "4c51642038c4a3cc04c0f8f0b8267b17aafd4045", "881f6fb23c818ecfc387d2b134e1cd7328fc5995", "d8155325107dbbb1f8ef44f75553595fe4c8ec8c", "101eae5edb76fefc40b039009eb35bbaaae99386", "3abd88bc1a3c334f53f345998b72e9cf8ae87abf"} else "2ad45d27a850d56ccc6b49e92f2a5051d07be848" if actual_vendor_pin in {"973d45ae0da5d9612d30900e39118d67d039b31a", "6b8fd06606f12be187f73e8809e56a49864794f9"} else "38f13e8983228509f4f378d27a3244367ec50878"),
        "encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.h": ("9603dfd3e2ae0e8a16b29ef8520a8db17340c29d" if actual_vendor_pin in {"652f88555e8bb16ffeffd9d1fa3d0c49e7925dfc", "38e19d4be0d99bbba35558af2c0620cd9b46f12e", "4c51642038c4a3cc04c0f8f0b8267b17aafd4045", "881f6fb23c818ecfc387d2b134e1cd7328fc5995", "d8155325107dbbb1f8ef44f75553595fe4c8ec8c", "101eae5edb76fefc40b039009eb35bbaaae99386", "3abd88bc1a3c334f53f345998b72e9cf8ae87abf"} else "a228adddcc987c9c110068780b16e43d9bd4303e"),
        "encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/nvhost_gpu.cpp": ("25aa385480b28a3d828da034222795ac1f150e94" if actual_vendor_pin == "3abd88bc1a3c334f53f345998b72e9cf8ae87abf" else "964da0fe2338a7a67cbb9d14416af3ce1a309e09"),
        "encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/nvhost_gpu.h": "0a80ea7464d8643c75903bcd4655687173792274",
        "sources/eden/src/core/hle/service/nvdrv/devices/nvdevice.h": "175ae92472adfe6311d0847772aa52a11b682c24",
        "sources/eden/src/core/hle/service/nvdrv/nvdrv.cpp": "e271be36535169af9181cb8fe00ccdc5e1983922",
        "tests/ns2_gpu_identity_mapping_source.py": ("d0a4eb74022d81046377525bbe56e9042304757c" if actual_vendor_pin in {"d8155325107dbbb1f8ef44f75553595fe4c8ec8c", "101eae5edb76fefc40b039009eb35bbaaae99386", "3abd88bc1a3c334f53f345998b72e9cf8ae87abf"} else "5d752540cd053cd649daf05378f7e3f76577a356" if actual_vendor_pin == "881f6fb23c818ecfc387d2b134e1cd7328fc5995" else "8f7ab34c126da2eb3aee1e0ee6fff5d676eaf018" if actual_vendor_pin == "4c51642038c4a3cc04c0f8f0b8267b17aafd4045" else "2cc85651698aa291a7d146a6a357db4b89709c91" if actual_vendor_pin == "38e19d4be0d99bbba35558af2c0620cd9b46f12e" else "243eb8e6c8127d240e7a151cac44326e71d72280" if actual_vendor_pin == "652f88555e8bb16ffeffd9d1fa3d0c49e7925dfc" else "c703c4dd653c12c3ed6d594d38d33c9b45d3d850" if actual_vendor_pin == "6b8fd06606f12be187f73e8809e56a49864794f9" else "d0455a33826429dcda267bae2eb91299b561cad3"),
        "tests/ns2_gpu_partition_new_sdk_source.py": "e20113c02c3397214e9707ab4cc545d3b8770df5",
    }.items():
        raw=(V/relative).read_bytes()
        actual=hashlib.sha1(b"blob "+str(len(raw)).encode()+bytes([0])+raw).hexdigest()
        assert actual == expected_blob, ("libounce VM/channel successor drift", relative, actual)
    REVIEWED_PINS.add(actual_vendor_pin)
if actual_vendor_pin == "06705357e48b33d837b1f97dbb1c3979cb3d7c31":
    # Exact NS2 GPU lifecycle/VA successor. The downstream FC27/P0 source
    # receipts remain authoritative; this only qualifies the selected tree.
    assert subprocess.check_output(
        ["git", "-C", str(V), "rev-parse", "HEAD^{tree}"], text=True
    ).strip() == "8bd2b8d1378cefffaf0f4e397289ba62ef009112"
    # Seal every changed owner in the NS2 strict-completion successor.
    # Later FC27/P0 checks may replay historical receipts only after these
    # exact blobs and the complete vendor tree have been authenticated.
    for relative, expected_blob in {
        "encore-active/eden-backports/manifest.json": "9e7289bbf316d4f23c4e559c1503d24250043291",
        "encore-active/eden-backports/src/video_core/fence_manager.h": "f1c72747a9d8ecd38eb042bcffadb1209cc9fe80",
        "encore-active/eden-core/src/video_core/host1x/syncpoint_manager.cpp": "abe89b570a18508123a5c14c49cf5a43935f620c",
        "encore-active/eden-vulkan/include/video_core/renderer_vulkan/vk_rasterizer.h": "8bd6f2a4e489aa608fc4420d2ff5847b7c12e165",
        "encore-active/eden-vulkan/vulkan_rasterizer.cpp": "e5baa7f438d8caf11327989087db38ed1ca053a4",
        "encore-active/ns2-runtime/gpu_dispatch/video_core/engines/puller.cpp": "0eef39a957e2413b07a6d92b7295479248a88a60",
        "encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.cpp": "52b446565074b4a8d20bbf147aece99af4a116a1",
        "encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.h": "e5fa0694ff4ef754fb0316803f1812dfd8651ef1",
        "encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/nvhost_gpu.cpp": "5946911f40fed8e1eb622b73e3c0736031d94b9a",
        "encore-active/ns2-runtime/video_decoder/core/hle/service/am/service/graphics_video_decoder_session.cpp": "c917dfa128d05792edd942e562eab62d83808abf",
        "encore-active/ns2-runtime/vulkan_abi/video_core/rasterizer_interface.h": "74587c78870735bb23d2430415f3742b9e7cca68",
        "sources/eden/src/common/address_space.inc": "9cdbbd21f10c593147df35ddcaec45d98dd6db38",
        "tests/fc27_deferred_page_protection_host.py": "552298832efad742a0cf8f0619e6da197a4b3427",
        "tests/ns2_gpu_identity_mapping_source.py": "1d7b4561a6182de5fc910e89d4a9b47715e5af12",
        "tests/ns2_gpu_partition_new_sdk_source.py": "12492668d6492884b417dfcdbce4966c5d60028e",
        "encore-active/ns2-runtime/gpu_session/core/hle/service/am/service/gpu_worker_shared.cpp": "5a683ab0ef40dd71c7919d07d59bac3e07402d12",
        "tests/ns2_syncpt_bootstrap_source.py": "22383b8e49626e1ac3f022563adad446616f5420",
        "tests/ps5_host1x_wait_notification_host.py": "3365c5e9b857cca98d80a4bc8134306695feb171",
    }.items():
        raw=(V/relative).read_bytes()
        actual=hashlib.sha1(b"blob "+str(len(raw)).encode()+bytes([0])+raw).hexdigest()
        assert actual == expected_blob, ("NS2 strict-completion successor drift", relative, actual)
    REVIEWED_PINS.add(actual_vendor_pin)

if actual_vendor_pin in {"191dd458c68de13f0f71659e3b4a9598af7de561", "b743e9c7ec9832832711fc0ea34e03a25c973557", "4c8f72f8ba3db320af55cea0f53cac16366c3ea0", "6affc4ad869a3eaab9d1bed1e65de8872d93363b", "b92d4183cec69e65216162cf61e451eff643caa0", "84d3b0398ae7db1618899815bc1f98894453fbf6"}:
    assert subprocess.check_output(
        ["git", "-C", str(V), "rev-parse", "HEAD^{tree}"], text=True
    ).strip() == ("2c722077f49013766b80b561ecf446562450faa5" if actual_vendor_pin == "84d3b0398ae7db1618899815bc1f98894453fbf6" else "79254f62ba6a12bcdcda9024953ba10e6b84706a" if actual_vendor_pin == "b92d4183cec69e65216162cf61e451eff643caa0" else "34b43b1a3d669be0482aca97a28f988516df615c" if actual_vendor_pin == "6affc4ad869a3eaab9d1bed1e65de8872d93363b" else "b300d82e0aa31c9ddde01703bdf446579ce4e0c2" if actual_vendor_pin in {"4c8f72f8ba3db320af55cea0f53cac16366c3ea0", "6affc4ad869a3eaab9d1bed1e65de8872d93363b"} else "c6eea7dfe0603bfccb44da9b82c95ca1429761fe" if actual_vendor_pin in {"b743e9c7ec9832832711fc0ea34e03a25c973557", "4c8f72f8ba3db320af55cea0f53cac16366c3ea0"} else "f98956d2a6ce68c6af51bf5e8b53b7516b02bd2e")
    successor_blobs = {
        "encore-active/eden-vulkan/vulkan_rasterizer.cpp": ("fcd174ed2326f3c205365b192c98f9d2f4d82ec3" if actual_vendor_pin in {"6affc4ad869a3eaab9d1bed1e65de8872d93363b", "b92d4183cec69e65216162cf61e451eff643caa0", "84d3b0398ae7db1618899815bc1f98894453fbf6"} else "e4948333ed15fba8024aeb4ffaa143a2e010f991"),
        "tests/fc27_cpu_write_download_race_host.py": "7da2cf9b3e6f14c210c14fe201a0a95db92856cc",
    }
    if actual_vendor_pin in {"b743e9c7ec9832832711fc0ea34e03a25c973557", "4c8f72f8ba3db320af55cea0f53cac16366c3ea0", "6affc4ad869a3eaab9d1bed1e65de8872d93363b", "b92d4183cec69e65216162cf61e451eff643caa0", "84d3b0398ae7db1618899815bc1f98894453fbf6"}:
        successor_blobs["tests/fc27_deferred_page_protection_host.py"] = ("4e10cd67ee80e617becdd751a736f25a4e18aa07" if actual_vendor_pin in {"6affc4ad869a3eaab9d1bed1e65de8872d93363b", "b92d4183cec69e65216162cf61e451eff643caa0", "84d3b0398ae7db1618899815bc1f98894453fbf6"} else "bd92b4e52e7621ff55610e40b862a30b9f575e47")
    if actual_vendor_pin in {"4c8f72f8ba3db320af55cea0f53cac16366c3ea0", "6affc4ad869a3eaab9d1bed1e65de8872d93363b", "b92d4183cec69e65216162cf61e451eff643caa0", "84d3b0398ae7db1618899815bc1f98894453fbf6"}:
        successor_blobs["encore-active/eden-core/overrides/usage-tracker/video_core/buffer_cache/usage_tracker.h"] = "f7f1273ba8314689b3fac5bf108205513c21f5d8"
        successor_blobs["tests/ps5_buffer_usage_granularity_host.py"] = "a3e3f90825df12d026b69ab9475a667234696768"
    if actual_vendor_pin == "b92d4183cec69e65216162cf61e451eff643caa0":
        successor_blobs.update({"encore-active/ns2-astc/include/video_core/texture_cache/texture_cache.h":"45659d2fa8ae336d28e7ccbd02b3104d96229378","tests/ns1_r23_18_tir_host.py":"9e835a870dac4e7728978328814e57cab58d85c5","tests/fc27_deferred_page_protection_host.py":"c4b49d84e9714d64ae4e72942a32274d6fc1bc7f"})
    for relative, expected_blob in successor_blobs.items():
        raw = (V / relative).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        assert actual == expected_blob, ("FC27 collected-batch successor drift", relative, actual)
    REVIEWED_PINS.add(actual_vendor_pin)

if actual_vendor_pin in {"cd5ce4dabef1d32e0441d22dccdee358ebf23287", "a8f327c972bd2f84f6e6f9432c96c4a948963073", "ffa7757e98bf42a5abcd5c0b9e845cfdbc01e75e", "752b92033610b294a36254d5747c317aca51c1d5", "1b5256d72072e05a62fb734bc9ef790fc81c1573", "628d01bdc4368e9ad661d749515f788ef7c03802", "191dd458c68de13f0f71659e3b4a9598af7de561", "b743e9c7ec9832832711fc0ea34e03a25c973557", "4c8f72f8ba3db320af55cea0f53cac16366c3ea0", "6affc4ad869a3eaab9d1bed1e65de8872d93363b", "b92d4183cec69e65216162cf61e451eff643caa0", "84d3b0398ae7db1618899815bc1f98894453fbf6"}:
    # Queued-GPFIFO AS revocation + complete native Puller/Ampere H:17 successor. Seal the
    # complete tree and every owner changed since the last qualified GPU
    # lifecycle snapshot before admitting historical receipts for untouched
    # FC27/P0 owners.
    assert subprocess.check_output(
        ["git", "-C", str(V), "rev-parse", "HEAD^{tree}"], text=True
    ).strip() == ("2c722077f49013766b80b561ecf446562450faa5" if actual_vendor_pin == "84d3b0398ae7db1618899815bc1f98894453fbf6" else "79254f62ba6a12bcdcda9024953ba10e6b84706a" if actual_vendor_pin == "b92d4183cec69e65216162cf61e451eff643caa0" else "34b43b1a3d669be0482aca97a28f988516df615c" if actual_vendor_pin == "6affc4ad869a3eaab9d1bed1e65de8872d93363b" else "b300d82e0aa31c9ddde01703bdf446579ce4e0c2" if actual_vendor_pin in {"4c8f72f8ba3db320af55cea0f53cac16366c3ea0", "6affc4ad869a3eaab9d1bed1e65de8872d93363b"} else "c6eea7dfe0603bfccb44da9b82c95ca1429761fe" if actual_vendor_pin in {"b743e9c7ec9832832711fc0ea34e03a25c973557", "4c8f72f8ba3db320af55cea0f53cac16366c3ea0"} else "f98956d2a6ce68c6af51bf5e8b53b7516b02bd2e" if actual_vendor_pin in {"191dd458c68de13f0f71659e3b4a9598af7de561", "b743e9c7ec9832832711fc0ea34e03a25c973557"} else "48f75fca37a128f9425cc3484d22ab994a1a17a8" if actual_vendor_pin in {"628d01bdc4368e9ad661d749515f788ef7c03802", "191dd458c68de13f0f71659e3b4a9598af7de561"} else "c54279c46295cc71d27c74af213dcacff0d08810" if actual_vendor_pin == "1b5256d72072e05a62fb734bc9ef790fc81c1573" else "7ab98eb5286021a9e070397ef6673f61934cf5e0" if actual_vendor_pin == "752b92033610b294a36254d5747c317aca51c1d5" else "af3fb89c9c6bb96c19bd2e099273019840536267" if actual_vendor_pin == "ffa7757e98bf42a5abcd5c0b9e845cfdbc01e75e" else "747569d1bafefc23fb235e1929bda0f5c0d48de3" if actual_vendor_pin == "a8f327c972bd2f84f6e6f9432c96c4a948963073" else "2a8d99c8a9912041a286c747c7dcebf5a8cc6f89")
    if actual_vendor_pin in {"a8f327c972bd2f84f6e6f9432c96c4a948963073", "ffa7757e98bf42a5abcd5c0b9e845cfdbc01e75e", "752b92033610b294a36254d5747c317aca51c1d5", "1b5256d72072e05a62fb734bc9ef790fc81c1573", "628d01bdc4368e9ad661d749515f788ef7c03802", "191dd458c68de13f0f71659e3b4a9598af7de561", "b743e9c7ec9832832711fc0ea34e03a25c973557", "4c8f72f8ba3db320af55cea0f53cac16366c3ea0", "6affc4ad869a3eaab9d1bed1e65de8872d93363b", "b92d4183cec69e65216162cf61e451eff643caa0", "84d3b0398ae7db1618899815bc1f98894453fbf6"}:
        raw = (V/"encore-active/eden-vulkan/vk_pipeline_cache_cost.cpp").read_bytes()
        assert hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest() == ("7db0462ad24aa4c6356ce4efa0086b356f171be6" if actual_vendor_pin in {"628d01bdc4368e9ad661d749515f788ef7c03802", "191dd458c68de13f0f71659e3b4a9598af7de561", "b743e9c7ec9832832711fc0ea34e03a25c973557", "4c8f72f8ba3db320af55cea0f53cac16366c3ea0", "6affc4ad869a3eaab9d1bed1e65de8872d93363b", "b92d4183cec69e65216162cf61e451eff643caa0", "84d3b0398ae7db1618899815bc1f98894453fbf6"} else "cdcef0c6ec4cdada8521af43f856e66f98d5b0a9")
    for relative, expected_blob in {
        "encore-active/eden-core/src/video_core/dma_pusher.cpp": "5cf42158c7cc4462bc9a12a18b482cbd6de20bf8",
        "encore-active/ns2-runtime/gpu_dispatch/video_core/dma_pusher.h": "4cb9f79deeb56ab7397c6209939c94dffbb7575b",
        "encore-active/ns2-runtime/gpu_dispatch/video_core/engines/puller.cpp": "78497f6f85386d75e9a8b75f80798880cc5f8df7",
        "encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.cpp": "8826183bd03a090e797f41e79d5b27a7603ea207",
        "encore-active/ns2-runtime/nvdrv_as/core/hle/service/nvdrv/devices/nvhost_as_gpu.h": "55db762d0322bd2621adf8e72aafcf30751d43e0",
        "encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/native_gpu_channel_registry.h": "e43cc46223fd95fe9ad0f63e8311539c68c86807",
        "encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/nvhost_gpu.cpp": "5bd4ede78cd44b4a2ad7c98ea8c5b90aec20c302",
        "encore-active/ns2-runtime/nvdrv_gpu/core/hle/service/nvdrv/devices/nvhost_gpu.h": "4106f73b369e9a667854f48c387dc03186dd1145",
        "tests/ns2_gpu_identity_mapping_source.py": "ab93f14505625ef3b1e2fc50945371a2e1f7e05e",
        "tests/ns2_native_tiling_activation_source.py": "7946e58a7e499fa8a63e718da77af6094352699c",
        "tools/ns2/check_g10_qmd_release_callback_host.py": "92280b84fd16a5c7ba37e6f584cb8e3cf0bfad77",
    }.items():
        raw=(V/relative).read_bytes()
        actual=hashlib.sha1(b"blob "+str(len(raw)).encode()+bytes([0])+raw).hexdigest()
        assert actual == expected_blob, ("queued GPFIFO/Puller H17 successor drift", relative, actual)
    REVIEWED_PINS.add(actual_vendor_pin)
if actual_vendor_pin in {"ffa7757e98bf42a5abcd5c0b9e845cfdbc01e75e", "752b92033610b294a36254d5747c317aca51c1d5", "1b5256d72072e05a62fb734bc9ef790fc81c1573", "628d01bdc4368e9ad661d749515f788ef7c03802", "191dd458c68de13f0f71659e3b4a9598af7de561", "b743e9c7ec9832832711fc0ea34e03a25c973557", "4c8f72f8ba3db320af55cea0f53cac16366c3ea0", "6affc4ad869a3eaab9d1bed1e65de8872d93363b", "b92d4183cec69e65216162cf61e451eff643caa0", "84d3b0398ae7db1618899815bc1f98894453fbf6"}:
    for relative, expected in {"encore-active/eden-core/overrides/buffer-hotpath/common/range_sets.h":"1c90e08bc3c66731aa717e7b17b3249539848016","encore-active/eden-core/overrides/buffer-hotpath/common/range_sets.inc":("bd48ff5cb346981f0937cfddbb042f9100697fd2" if actual_vendor_pin in {"752b92033610b294a36254d5747c317aca51c1d5", "1b5256d72072e05a62fb734bc9ef790fc81c1573", "628d01bdc4368e9ad661d749515f788ef7c03802", "191dd458c68de13f0f71659e3b4a9598af7de561", "b743e9c7ec9832832711fc0ea34e03a25c973557", "4c8f72f8ba3db320af55cea0f53cac16366c3ea0", "6affc4ad869a3eaab9d1bed1e65de8872d93363b", "b92d4183cec69e65216162cf61e451eff643caa0", "84d3b0398ae7db1618899815bc1f98894453fbf6"} else "742dc02b71ada75425fec7e126093634a22d2102"),"encore-active/eden-core/overrides/buffer-hotpath/video_core/buffer_cache/word_manager.h":"0992d01d0b4e262dd4b4a79633affa8b02529795","encore-active/eden-core/src/video_core/buffer_cache/buffer_cache.h":"4ce33d21debc33c9625129cbd545bf9b1c084272","tests/fc27_gpu_page_sibling_preservation_host.py":("f7b1eb205c2614d30809dd0f9f132e43ccf46745" if actual_vendor_pin in {"752b92033610b294a36254d5747c317aca51c1d5", "1b5256d72072e05a62fb734bc9ef790fc81c1573", "628d01bdc4368e9ad661d749515f788ef7c03802", "191dd458c68de13f0f71659e3b4a9598af7de561", "b743e9c7ec9832832711fc0ea34e03a25c973557", "4c8f72f8ba3db320af55cea0f53cac16366c3ea0", "6affc4ad869a3eaab9d1bed1e65de8872d93363b", "b92d4183cec69e65216162cf61e451eff643caa0", "84d3b0398ae7db1618899815bc1f98894453fbf6"} else "c27f87a327a5a371a7810b41dabc2bc8f03fe61d")}.items():
        raw = (V / relative).read_bytes()
        assert hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest() == expected, relative
    assert "EDEN_MAINTAINED_BUFFER_HOTPATH" in (V.parent / "headless/CMakeLists.txt").read_text()
checked=subprocess.check_output(["git","-C",str(V),"rev-parse","HEAD"],text=True).strip()
assert actual_vendor_pin==checked and selected in REVIEWED_PINS,(actual_vendor_pin,selected,checked)
# The 3a97 successor's four changed blobs were sealed above. From this point
# replay the predecessor's exact historical receipt graph for all unaffected
# owners; otherwise reviewed_blob() sees the successor SHA and misses c74's
# already-qualified per-file revisions.
if gitlink_vendor_pin in {
    "3a97e47a0cfe94ec55227af363d8c289de59d4f8",
    "3de91cf284c8ef234c757c046998c4f48165c59a",
    "2fd07582db57fdddc67e6fd56cec16624a902c6a",
    "4411fc172eef84080ab7de23158349bbe7d08f88",
    "0c4eafeb9f197e76a1f0bb06038ef9bbf2c7565d",
    "bc6baf037ac3304d4ba81cf7589f7e52e8fa8ae0",
    "546e1aa34d2ff183dd4c737f9da8fbf4a62be24e",
    "f65ccc439534ffd9ce0a307b23bd511b4e32857a",
    "4e6a966508e718d02526d4d220e112591536f28c",
    "2d07b5e65baf35c82d0b0e557617aefe730a10b1",
    "7baf9cc07c6aceee185032544d964f04a2fed108",
    "1f8a3bbaa7fc33118e63ebef829202d825475bfe",
    "1e513ae001669127538a346c7f390af55edd6712",
    "d31aa01bdfa87165a272473c385040723bf2c1f6",
    "20cb62f1be572c8063ce4162d3227c8784a1e5ff",
    "19a62450fe8eb2fd3c28a4e940ed412beb9dc7ba",
    "76a225552c296686cd1022584d73decd46767f75",
    "205c6a3572955c3d8002f5faca68d6ce1359817c",
}:
    gitlink_vendor_pin = "c74fb345ac3d8fa752f403369827a432f3503fb5"
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
        assert actual == ns2_preemption_receipt(relative, expected), ("NS2 GSV parent session rollback source drift", relative, actual)
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
    assert actual == reviewed_blob(relative, native_gsv_active_cpp), ("NS2 native GSV compiled source drift", actual)
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
        assert actual == reviewed_blob(relative, "5ff69e424b4b77d16732df37dbb5ecd56f3d4964"), ("GPU worker shutdown-guard drift", relative, actual)
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
    assert actual == reviewed_blob(relative, "37236a90479c1913cec33ad95d768a3fc80a1504"), (
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
        assert protocol_blob == reviewed_blob(
            "encore-active/ns2-runtime/hle/core/hle/service/am/service/graphics_supervisor_protocol.h",
            expected_protocol), ("NS2 GSV bootstrap hint source drift", protocol_blob)
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
