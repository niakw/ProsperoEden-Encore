#!/usr/bin/env python3
"""R457 exact source graph: guest PTE + raw kernel fill -> resident PA -> GPU.

Host-only structural audit. It does not execute guest code or confirm
physical alias lifetime, PS5 SDK, GPU fences, or first frame.
"""
from pathlib import Path
import hashlib
import subprocess
import sys

root=Path(__file__).resolve().parents[2]
# Only the exact historical and reviewed integrated vendor commits are
# admitted. The sparse PTE/slab/GPU publisher owners are byte-identical.
reviewed_vendors={
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
    "4572e581d011c444fd59428d5c042098f05dcfca","f7ee793f1ee1bb1c2b1a35f68073844163658262","3f019c64c2907ac3e84baa9b6200de8898f30636","f0324324768bdc090a003079bbf121df862bc7f7","0ae51658a5d93e368408cad2484b99083ed7309f","697159fd0c183f8a164d0493929ae3b4bcb391d1","b1bb49abea63b6664e0945df8431e10aac128c2f","89d70eb505594447b3ca98658311002e74dac8ad", "b68126c9cd95eef6c6656ff6d7834c62c092aa46", "0fc157b7ccef428e675ff945bc48eceb08fff607", "42459a7893c51a178ecd0c2f74f3951cc20fa12d", "d1f8696448ed481e36380c3ea8431e3dc722304e", "c5614d3c7ef75958965bac93c9e343eccdbc0fbe", "67926ea4b6960eefebf0427929cf299e8e056013", "50a849a93494f442d47573b8ce8b8797c3cecd26", "2c85d0e8ed192c5eec79423e6be8d883fa0bd7ab", "053acc8ddf30fe65f6376564bbd6efef58f07ddc", "ffa519db0f68fb0d5d2acf791e381c898a34a175",
    "9e38066a508716fd959477eccf32c7fb2fde3356",
    "e298a9b05732346141b685eb4c9850bfa02d9e58",
    "f7ccfda091fd7429f44159318a07391881a3e7c0","92c480e17fedecc21ab4882b76e8507b5aed3771",
    "7039d7752c5d8b1a53db50be0d8f2f7803867e13","d3fca0aa188052f0efd2bad102950aeaeeb36ab0",
    "dfc39fcc087738955b0373b45fa97facdeb2fc47",
    "b806bc497049819e716ef6de81f2a85312b188ce",
    "a0e17271e94342c32b02acdc3199c3f258a8aecf",
    "772f06c8f5b12fdc81066e61f3db2dedfe3eed81",
    "568ae541c07691518e9663aa0fc5f3b017a98d53",
    "dcfe3d2384bd800c6139ede672518ea2c66922a6",
    # Vendor PR #185: shim+tiling header/test/workflow only;
    # sparse kernel and GPU publisher blobs are still checked below.
    "9d324ca5ca2cdd84053f2d3dfadde5b86084c13d", "cd476e6e93e8a786bef6260006baec134f5df71f", "2ccc4b0a714ca621ac2879768f87118a64ed65f6", "97ac02f263ec90f40a029f4aa62980c76bc25d5c", "9a83a6ba1cb464c9e5d14457cab18ad511c1104b", "d0246caf58a3127597bba1edfc1f8dcbe0c5cfdc", "8153654a2f1fe809fb2caa28dcadca90a7661446", "6c38328fbef33de747f5c31ea30d13541a513a4a", "8e564f61e6c8b86149ce0a0d6d2aa323a268dda6", "67759611edc13414c112ea9d2b6664d54827a200", "c15cdfe96a3d836bf32ba21b8070088add81cdc9", "729f7e5a734b5a890a7bbf3ab60ce1100492af13", "1a09972eea6f473fda1b714efe84cd52219bf681", "3e6647827122c34704c2699a6f5e9b20fff3e9a6", "6d64217ea5804fb86dbf57685a3da0cb1d45ba32", "3f1fcfef119ca50dd630f0518a7fae1b96c7a85a", "0e4e96df638fc29c3bd2a8fcfe9f50821c5e5b3a", "9136d2e88c43233bcd029f22bdfda0e5c94a552f", "75ef34d7ef7f68b5eb4f1c6d0d99b6cbc55742d6", "34f02a3800cb6fb5330c099c81571ab03fd69ae1", "0d75406e36a3676b45184670093f0ecf652aab2f", "372a83d95622f152211fe91afa05d1e60ce84bea", "a3cc07ff68f8154543f2b07a6b3e6c01f9922ab9", "ab417b59c5f7f4613ff27386be05c0644d0ed776",
}
reviewed_vendors.add("42b34a5dc46b594cb029362e8f130900adf4424e")
reviewed_vendors.add("77b736148129ffa72c9f6c081695b7c7515c3ed9")
reviewed_vendors.add("4354add020afac574198f63d87167f3022bff9c6")
# Exact successor: optimized sparse OOM rollback and tracking before PTE.
reviewed_vendors.add("ced1b9cdd6f0fa4e0ca7949b404f450aae0055df")
reviewed_vendors.add("06b453171af26b5703e2fcc5e68c4e8288d758b7")
reviewed_vendors.add("fd6eee4933c36ed93d6ef59e2ae5d23fd975f9f2")
reviewed_vendors.add("56959a23273ea2ee82d2e59628c92cc9e1144fe9")
reviewed_vendors.add("d3c76f07cd82f7766be7b5e3fc3c399a3be15291")
reviewed_vendors.add("436e702cc970417455c088c4bc38ce5fec8e0762")
reviewed_vendors.add("6489896230a030cf28d31961c7c8f242cab73f27")
reviewed_vendors.add("05de9e8e7f75e9a7400a351b18f2b1e83165108e")
reviewed_vendors.add("ee64fac70671126c9b6ab9aa3b3885a40538cf16")
reviewed_vendors.add("603e0d5c70b04fa84a19cca8f580ed1bdb230be0")
reviewed_vendors.add("593bc9ee6ddfcf38e488325ccf318f1a0a109d8e")
reviewed_vendors.add("6b48e6734e738306dd57ceed8be9b003631eb8cb")
reviewed_vendors.add("d554e257ae82db66d9542f472dcde067510bfa1f")
reviewed_vendors.add("93c3dd6c86627e91999f965c45c05cd8e50e17eb")
reviewed_vendors.add("eb9a454db4d21a3aff2642c72eea3ca01bf2b3bb")
reviewed_vendors.add("93da3b707ef147385380eb0690e0d93fc8e907ad")
reviewed_vendors.add("a6240909b823492d9ff20070c09387a732d83007")
# FC27 SM/NVDRV + NS2 trace successor leaves sparse kernel/GPU owners intact.
reviewed_vendors.add("0390980a5752808dfba7b8edaa7d113cc4e4e6eb")
# Selected AM WindowSystem/LM contracts changed without touching sparse kernel/GMMU;
# the exact sparse-owner blobs remain sealed by this source test below.
reviewed_vendors.add("273680a5b33bff15c9ca12685cfadb2aa15ff9f1")
reviewed_vendors.add("84b9975726092a32d1cb2aa714b96e4f5f85d7c4")
reviewed_vendors.add("84ec89ce112b83603b2095a9f6bb785f8e999ef6")
reviewed_vendors.add("97fa38381d9ce23b63b3bf3751615dc254ab3634")
reviewed_vendors.add("b099bd7cbefaa1a35d6626d4fd3161afcefa1b48")
reviewed_vendors.add("bfdf39014db15f237a16d4a50e6cdfd68bdd87b8")
reviewed_vendors.add("4626d87be155c0b42904610323098c1205515450")
reviewed_vendors.add("c32704e63844449b1c18a03deb2cd92939999b90")
reviewed_vendors.add("fab5ebbfda09ebd3fc414b3127e135c66025ccb8")
reviewed_vendors.add("acb42e2a2b18fee17673d07e06b2f29709de2fb5")
reviewed_vendors.add("99df05ff50a7a4a9591c17b08f4ed0f8cb0374a3")
reviewed_vendors.add("04e252186aa42bacde0899e0c9224035c83a6b0d")
reviewed_vendors.add("44f5b75bc93bcea146ad6fba3ac294405ae8709b")
reviewed_vendors.add("70789b12dea4d72ce9e7f054c5b6f552ec488f5d")
reviewed_vendors.add("9db97fb12db1a390d6b2410f0c18333aa31e37da")
reviewed_vendors.add("60fa67b98286bd84bd591987c5690ae9b15bda3f")
reviewed_vendors.add("bf981e9d39d4a908d0d5b6f8407cca814c609bdb")
reviewed_vendors.add("8026fcca228d0feda62ffd9625e16ee0429d621e")
reviewed_vendors.add("887bf44af34999e8b6c5b63dc7c01c6c13b82c8f")
reviewed_vendors.add("1a928783cce2c2692d8fe9fd958400a2de060bbf")
reviewed_vendors.add("9632ac089f8b2d89a6856a42e8fb55206cdba1fa")
pinned=subprocess.check_output(["git","rev-parse","HEAD:vendor"],
                               cwd=root,text=True).strip()
selected=subprocess.check_output(["git","-C",str(root/"vendor"),"rev-parse","HEAD"],
                                 text=True).strip()
if selected in {"b5c6f089a6aecd321d08a40238f3cd502f505b26", "dc9f5f95b1f784bb358d6480e53de7247d61d777", "a441295022b23834f8531c54d2b0965f84023278", "7c5d5220dd4df4a531418458ab623ef86c41348c", "44540549ee9a65eb8078e271f43ccded0e8e984f", "d63d82dfb9c2afbacac4c9dc1491f743fb083d52", "d634b381d85dae30492dd6291fc4e6e96143f363", "692e9819a7a1f1b818bf3739c72d8e5252cae661", "166e473e120a86a6edcd32a975ffe19b45ffdd42", "3522d8578fbcd7b46d2a439d5d718dfb570beb7b", "042204fde8e5b74aa5048c6213a8af4450d26fe5", "294442004543aeecc5f3c61cc1b73b2feaff2f92", "53d0ad1f9d50b9f1a72cbecacdacdff7fb4e69eb", "7e137d362f9679125726ef4876355a09d788795e", "973d45ae0da5d9612d30900e39118d67d039b31a", "6b8fd06606f12be187f73e8809e56a49864794f9", "652f88555e8bb16ffeffd9d1fa3d0c49e7925dfc", "38e19d4be0d99bbba35558af2c0620cd9b46f12e", "4c51642038c4a3cc04c0f8f0b8267b17aafd4045", "881f6fb23c818ecfc387d2b134e1cd7328fc5995", "d8155325107dbbb1f8ef44f75553595fe4c8ec8c", "101eae5edb76fefc40b039009eb35bbaaae99386", "3abd88bc1a3c334f53f345998b72e9cf8ae87abf"}:
    # AM lifetime successor changes no shader or sparse kernel owner.
    assert subprocess.check_output(["git", "-C", str(root / "vendor"), "rev-parse", "HEAD^{tree}"], text=True).strip() == ("b82ce9bb3b543bf85d535bdfdfb6d725fe88be56" if selected == "3abd88bc1a3c334f53f345998b72e9cf8ae87abf" else "8e42496a1f01a94cc6b17f57eee6ebdff2698ff6" if selected == "101eae5edb76fefc40b039009eb35bbaaae99386" else "a6451d095d44e8b9968635320d3bba34d5722fa5" if selected == "d8155325107dbbb1f8ef44f75553595fe4c8ec8c" else "ba3ad593fb37ac3dc62f2c8b6064328c55cabb3b" if selected == "881f6fb23c818ecfc387d2b134e1cd7328fc5995" else "77add4864dbadc2c2246c339b215c3d79b40a549" if selected == "4c51642038c4a3cc04c0f8f0b8267b17aafd4045" else "a27660a134453d2895e23d5c56ac64e6f12d9960" if selected == "38e19d4be0d99bbba35558af2c0620cd9b46f12e" else "57a6ef072ad018954d493cb9064b5c722a5af827" if selected == "652f88555e8bb16ffeffd9d1fa3d0c49e7925dfc" else "6ecf485d48b3c29c5e058de99a09c5c495cd537d" if selected == "6b8fd06606f12be187f73e8809e56a49864794f9" else "1d991da378f711312faf34125f1d4cfe1378bcaa" if selected == "973d45ae0da5d9612d30900e39118d67d039b31a" else "6861e052a9824450c7eeaa91b53334c153ca9865" if selected == "7e137d362f9679125726ef4876355a09d788795e" else "a21aa2b63cfb9cae4dd9ba386982c3bd57a7ef1f" if selected == "53d0ad1f9d50b9f1a72cbecacdacdff7fb4e69eb" else "50ba35725b57b59cae76a67c7c1d4ba6ad894e2f" if selected == "294442004543aeecc5f3c61cc1b73b2feaff2f92" else "08ff1d3ef45b03cbe3396079bcb91fa5dce4f160" if selected == "042204fde8e5b74aa5048c6213a8af4450d26fe5" else "67917388ba3308bacfa3e8da6fff9d83c4efb713" if selected == "3522d8578fbcd7b46d2a439d5d718dfb570beb7b" else "3a996079e9de76e0c3d8bd2e595e6c83dadd6ce0" if selected == "166e473e120a86a6edcd32a975ffe19b45ffdd42" else "6743fed9174ee7e3451afbbad230dca6c2e4203c" if selected == "692e9819a7a1f1b818bf3739c72d8e5252cae661" else "a51ee73257c13fce70cbaf5d3e26c62010abf2e9" if selected == "d634b381d85dae30492dd6291fc4e6e96143f363" else "290d8c51e8ab40dd56651d50483abe42e11fa404" if selected == "d63d82dfb9c2afbacac4c9dc1491f743fb083d52" else "86d6068c438cc36ffd01513fc178d2590fb010cb" if selected == "44540549ee9a65eb8078e271f43ccded0e8e984f" else "9ff41b47bfe30a9cef86a5ab7c584c0094f586bf" if selected == "7c5d5220dd4df4a531418458ab623ef86c41348c" else "d53129478299aded8cb8d7432751b43fa74594b9" if selected == "a441295022b23834f8531c54d2b0965f84023278" else "1660883553006cfca7e80465ad5521b4c2ca33b1" if selected == "dc9f5f95b1f784bb358d6480e53de7247d61d777" else "668fb8effa6963be062d780e3bd145a5233d6b7e")
    reviewed_vendors.add(selected)
if pinned in {"17253dc91e9fe1eb2d9980f261f59d227bfcd1a1", "95343060f948601930f2e62b919da0789f0830bb", "12ab9a8411f5c9df1b5cc73f01c923ad9479c8af", "224b05e6f8b1a266b0d55d1ded5332f7a2eaed7c", "150a3a79ca103061f73a9a50ca8f463a3b4712f3", "fcd62408fdbc33af01a4caebc8fd44c8500b628f", "b6b9e98e0dd16c4702f21f2e0b5e322126abeecb", "dbef23055897b1649f83c20cf7a0516e64f3d5cd"}:
    if pinned in {"95343060f948601930f2e62b919da0789f0830bb", "12ab9a8411f5c9df1b5cc73f01c923ad9479c8af", "224b05e6f8b1a266b0d55d1ded5332f7a2eaed7c", "150a3a79ca103061f73a9a50ca8f463a3b4712f3", "fcd62408fdbc33af01a4caebc8fd44c8500b628f", "b6b9e98e0dd16c4702f21f2e0b5e322126abeecb", "dbef23055897b1649f83c20cf7a0516e64f3d5cd"}:
        tree_sha = subprocess.check_output(
            ["git", "-C", str(root / "vendor"), "rev-parse", "HEAD^{tree}"], text=True
        ).strip()
        assert tree_sha == {
            "95343060f948601930f2e62b919da0789f0830bb": "efa6548c57f7823d4e8b2c975944c6846b765ff3",
            "12ab9a8411f5c9df1b5cc73f01c923ad9479c8af": "64179fcce4962f9b2b7c738504a6fa0e00b2b292",
            "224b05e6f8b1a266b0d55d1ded5332f7a2eaed7c": "3f7f1523cef730ad153bf658fbb3567222d6e956",
            "150a3a79ca103061f73a9a50ca8f463a3b4712f3": "39fb9a3efe65f67115dfcdebe39a55334a702f2d",
            "fcd62408fdbc33af01a4caebc8fd44c8500b628f": "8447712e2cecf661910fd1a32613f0b844ceaeb0",
            "b6b9e98e0dd16c4702f21f2e0b5e322126abeecb": "067c72d30a71a79faefd1ad14876e2a46f02755c",
            "dbef23055897b1649f83c20cf7a0516e64f3d5cd": "9e28e5b83cf9c0f4086a33d6838904353a8fd541",
        }[pinned], ("R457 vendor tree drift", pinned, tree_sha)
    # Admission requires exact C++ predecessor replay, not a SHA alone.
    sys.path.insert(0,str(root/"vendor/tests"))
    from native_msaa_handle_receipt import (
        GUEST_CACHE_LOCK_SUCCESSOR, INTEGRATED_RASTERIZER,
        restore_guest_cache_lock_successor, blob)
    raster=(root/"vendor/encore-active/eden-vulkan/vulkan_rasterizer.cpp").read_text()
    assert blob(raster.encode("utf-8"))==GUEST_CACHE_LOCK_SUCCESSOR
    assert blob(restore_guest_cache_lock_successor(raster).encode("utf-8"))==INTEGRATED_RASTERIZER
    reviewed_vendors.add(pinned)
if selected in {"0390980a5752808dfba7b8edaa7d113cc4e4e6eb", "273680a5b33bff15c9ca12685cfadb2aa15ff9f1", "84b9975726092a32d1cb2aa714b96e4f5f85d7c4", "84ec89ce112b83603b2095a9f6bb785f8e999ef6", "97fa38381d9ce23b63b3bf3751615dc254ab3634", "b099bd7cbefaa1a35d6626d4fd3161afcefa1b48", "bfdf39014db15f237a16d4a50e6cdfd68bdd87b8", "4626d87be155c0b42904610323098c1205515450", "c32704e63844449b1c18a03deb2cd92939999b90", "fab5ebbfda09ebd3fc414b3127e135c66025ccb8", "acb42e2a2b18fee17673d07e06b2f29709de2fb5", "99df05ff50a7a4a9591c17b08f4ed0f8cb0374a3", "04e252186aa42bacde0899e0c9224035c83a6b0d", "44f5b75bc93bcea146ad6fba3ac294405ae8709b", "70789b12dea4d72ce9e7f054c5b6f552ec488f5d", "9db97fb12db1a390d6b2410f0c18333aa31e37da", "60fa67b98286bd84bd591987c5690ae9b15bda3f", "bf981e9d39d4a908d0d5b6f8407cca814c609bdb", "8026fcca228d0feda62ffd9625e16ee0429d621e", "887bf44af34999e8b6c5b63dc7c01c6c13b82c8f", "1a928783cce2c2692d8fe9fd958400a2de060bbf", "9632ac089f8b2d89a6856a42e8fb55206cdba1fa", "b5c6f089a6aecd321d08a40238f3cd502f505b26", "dc9f5f95b1f784bb358d6480e53de7247d61d777", "a441295022b23834f8531c54d2b0965f84023278", "7c5d5220dd4df4a531418458ab623ef86c41348c", "44540549ee9a65eb8078e271f43ccded0e8e984f", "d63d82dfb9c2afbacac4c9dc1491f743fb083d52", "d634b381d85dae30492dd6291fc4e6e96143f363", "692e9819a7a1f1b818bf3739c72d8e5252cae661", "166e473e120a86a6edcd32a975ffe19b45ffdd42", "3522d8578fbcd7b46d2a439d5d718dfb570beb7b", "042204fde8e5b74aa5048c6213a8af4450d26fe5", "294442004543aeecc5f3c61cc1b73b2feaff2f92", "53d0ad1f9d50b9f1a72cbecacdacdff7fb4e69eb", "7e137d362f9679125726ef4876355a09d788795e", "973d45ae0da5d9612d30900e39118d67d039b31a", "6b8fd06606f12be187f73e8809e56a49864794f9", "652f88555e8bb16ffeffd9d1fa3d0c49e7925dfc", "38e19d4be0d99bbba35558af2c0620cd9b46f12e", "4c51642038c4a3cc04c0f8f0b8267b17aafd4045", "881f6fb23c818ecfc387d2b134e1cd7328fc5995", "d8155325107dbbb1f8ef44f75553595fe4c8ec8c", "101eae5edb76fefc40b039009eb35bbaaae99386", "3abd88bc1a3c334f53f345998b72e9cf8ae87abf"}:
    # SHA admission is never sufficient: prove exact stable kernel/publisher
    # blobs and the four reviewed release C++ successor owners.
    import hashlib
    new_owner_blobs={
    "encore-active/eden-core/src/core/hle/service/sm/sm.cpp": "34c7c85f1476a3ba819ad20b8a4f8150cca86e16",
    "encore-active/eden-core/src/core/hle/service/sm/sm.h": "7069439e66a6f28ffa56229e08906a21222e2801",
    "encore-active/ns2-runtime/process/core/core.cpp": "0e0aadb72c8de5bb2c66ce9105b1dd2d381b5f98",
    "encore-active/ns2-runtime/am/core/hle/service/am/service/application_functions.cpp": "9bfaa26664361994902d5b7f73d6a41ff0eadb07",
    "encore-active/ns2-runtime/sparse-residency/core/hle/kernel/k_memory_manager.cpp": "2b5be4eba2500da2993db2ed1c86d44ddfa5554f",
    "encore-active/ns2-runtime/sparse-residency/core/hle/kernel/init/init_slab_setup.cpp": "130eb7bd53e29b816bb81fec3fa053a584cd4b6e",
    "encore-active/eden-core/overrides/core/device_memory_manager.inc": "daf493ce6e863397ec44bfae467c4f7533570477",
}
    if selected in {"273680a5b33bff15c9ca12685cfadb2aa15ff9f1", "84b9975726092a32d1cb2aa714b96e4f5f85d7c4", "84ec89ce112b83603b2095a9f6bb785f8e999ef6", "97fa38381d9ce23b63b3bf3751615dc254ab3634", "b099bd7cbefaa1a35d6626d4fd3161afcefa1b48", "bfdf39014db15f237a16d4a50e6cdfd68bdd87b8", "4626d87be155c0b42904610323098c1205515450", "c32704e63844449b1c18a03deb2cd92939999b90", "fab5ebbfda09ebd3fc414b3127e135c66025ccb8", "acb42e2a2b18fee17673d07e06b2f29709de2fb5", "99df05ff50a7a4a9591c17b08f4ed0f8cb0374a3", "04e252186aa42bacde0899e0c9224035c83a6b0d", "44f5b75bc93bcea146ad6fba3ac294405ae8709b", "70789b12dea4d72ce9e7f054c5b6f552ec488f5d", "9db97fb12db1a390d6b2410f0c18333aa31e37da", "60fa67b98286bd84bd591987c5690ae9b15bda3f", "bf981e9d39d4a908d0d5b6f8407cca814c609bdb", "8026fcca228d0feda62ffd9625e16ee0429d621e", "887bf44af34999e8b6c5b63dc7c01c6c13b82c8f", "1a928783cce2c2692d8fe9fd958400a2de060bbf", "9632ac089f8b2d89a6856a42e8fb55206cdba1fa", "b5c6f089a6aecd321d08a40238f3cd502f505b26", "dc9f5f95b1f784bb358d6480e53de7247d61d777", "a441295022b23834f8531c54d2b0965f84023278", "7c5d5220dd4df4a531418458ab623ef86c41348c", "44540549ee9a65eb8078e271f43ccded0e8e984f", "d63d82dfb9c2afbacac4c9dc1491f743fb083d52", "d634b381d85dae30492dd6291fc4e6e96143f363", "692e9819a7a1f1b818bf3739c72d8e5252cae661", "166e473e120a86a6edcd32a975ffe19b45ffdd42", "3522d8578fbcd7b46d2a439d5d718dfb570beb7b", "042204fde8e5b74aa5048c6213a8af4450d26fe5", "294442004543aeecc5f3c61cc1b73b2feaff2f92", "53d0ad1f9d50b9f1a72cbecacdacdff7fb4e69eb", "7e137d362f9679125726ef4876355a09d788795e", "973d45ae0da5d9612d30900e39118d67d039b31a", "6b8fd06606f12be187f73e8809e56a49864794f9", "652f88555e8bb16ffeffd9d1fa3d0c49e7925dfc", "38e19d4be0d99bbba35558af2c0620cd9b46f12e", "4c51642038c4a3cc04c0f8f0b8267b17aafd4045", "881f6fb23c818ecfc387d2b134e1cd7328fc5995", "d8155325107dbbb1f8ef44f75553595fe4c8ec8c", "101eae5edb76fefc40b039009eb35bbaaae99386", "3abd88bc1a3c334f53f345998b72e9cf8ae87abf"}:
        # Exact additive AM/LM delta from audited Lichii/Eglantine owners;
        # the sparse/GPFIFO owners above are still checked byte-for-byte.
        new_owner_blobs.update({
            "encore-active/eden-core/src/core/hle/service/am/window_system.cpp":
                "bbacbc9b8dde82c29b72a2272776d631f3e95fef",
            "sources/eden/src/core/hle/service/am/window_system.h":
                "d29e37adff7b62e790b26c4b5eba0d9ac667ad92",
            "encore-active/ns2-runtime/hle/core/hle/service/lm/lm.cpp":
                "9136cf19b1176e96fb17609fd401e4592028d1e2",
        })
    if selected in {"84b9975726092a32d1cb2aa714b96e4f5f85d7c4", "84ec89ce112b83603b2095a9f6bb785f8e999ef6", "97fa38381d9ce23b63b3bf3751615dc254ab3634", "b099bd7cbefaa1a35d6626d4fd3161afcefa1b48", "bfdf39014db15f237a16d4a50e6cdfd68bdd87b8", "4626d87be155c0b42904610323098c1205515450", "c32704e63844449b1c18a03deb2cd92939999b90", "fab5ebbfda09ebd3fc414b3127e135c66025ccb8", "acb42e2a2b18fee17673d07e06b2f29709de2fb5", "99df05ff50a7a4a9591c17b08f4ed0f8cb0374a3", "04e252186aa42bacde0899e0c9224035c83a6b0d", "44f5b75bc93bcea146ad6fba3ac294405ae8709b", "70789b12dea4d72ce9e7f054c5b6f552ec488f5d", "9db97fb12db1a390d6b2410f0c18333aa31e37da", "60fa67b98286bd84bd591987c5690ae9b15bda3f", "bf981e9d39d4a908d0d5b6f8407cca814c609bdb", "8026fcca228d0feda62ffd9625e16ee0429d621e", "887bf44af34999e8b6c5b63dc7c01c6c13b82c8f", "1a928783cce2c2692d8fe9fd958400a2de060bbf", "9632ac089f8b2d89a6856a42e8fb55206cdba1fa", "b5c6f089a6aecd321d08a40238f3cd502f505b26", "dc9f5f95b1f784bb358d6480e53de7247d61d777", "a441295022b23834f8531c54d2b0965f84023278", "7c5d5220dd4df4a531418458ab623ef86c41348c", "44540549ee9a65eb8078e271f43ccded0e8e984f", "d63d82dfb9c2afbacac4c9dc1491f743fb083d52", "d634b381d85dae30492dd6291fc4e6e96143f363", "692e9819a7a1f1b818bf3739c72d8e5252cae661", "166e473e120a86a6edcd32a975ffe19b45ffdd42", "3522d8578fbcd7b46d2a439d5d718dfb570beb7b", "042204fde8e5b74aa5048c6213a8af4450d26fe5", "294442004543aeecc5f3c61cc1b73b2feaff2f92", "53d0ad1f9d50b9f1a72cbecacdacdff7fb4e69eb", "7e137d362f9679125726ef4876355a09d788795e", "973d45ae0da5d9612d30900e39118d67d039b31a", "6b8fd06606f12be187f73e8809e56a49864794f9", "652f88555e8bb16ffeffd9d1fa3d0c49e7925dfc", "38e19d4be0d99bbba35558af2c0620cd9b46f12e", "4c51642038c4a3cc04c0f8f0b8267b17aafd4045", "881f6fb23c818ecfc387d2b134e1cd7328fc5995", "d8155325107dbbb1f8ef44f75553595fe4c8ec8c", "101eae5edb76fefc40b039009eb35bbaaae99386", "3abd88bc1a3c334f53f345998b72e9cf8ae87abf"}:
        # Exact native controller blob: the successors add only reviewed read-only
        # native GPU query behavior; all sparse-memory owners remain immutable.
        new_owner_blobs["encore-active/ns2-runtime/nvdrv/core/hle/service/nvdrv/devices/nvhost_ctrl_gpu.cpp"] = (
            "332ae7800c2639a1185ed417bf3a5a9508058d86" if selected in {"84ec89ce112b83603b2095a9f6bb785f8e999ef6", "97fa38381d9ce23b63b3bf3751615dc254ab3634", "b099bd7cbefaa1a35d6626d4fd3161afcefa1b48", "bfdf39014db15f237a16d4a50e6cdfd68bdd87b8", "4626d87be155c0b42904610323098c1205515450", "c32704e63844449b1c18a03deb2cd92939999b90", "fab5ebbfda09ebd3fc414b3127e135c66025ccb8", "acb42e2a2b18fee17673d07e06b2f29709de2fb5", "99df05ff50a7a4a9591c17b08f4ed0f8cb0374a3", "04e252186aa42bacde0899e0c9224035c83a6b0d", "44f5b75bc93bcea146ad6fba3ac294405ae8709b", "70789b12dea4d72ce9e7f054c5b6f552ec488f5d", "9db97fb12db1a390d6b2410f0c18333aa31e37da", "60fa67b98286bd84bd591987c5690ae9b15bda3f", "bf981e9d39d4a908d0d5b6f8407cca814c609bdb", "8026fcca228d0feda62ffd9625e16ee0429d621e", "887bf44af34999e8b6c5b63dc7c01c6c13b82c8f", "1a928783cce2c2692d8fe9fd958400a2de060bbf", "9632ac089f8b2d89a6856a42e8fb55206cdba1fa", "b5c6f089a6aecd321d08a40238f3cd502f505b26", "dc9f5f95b1f784bb358d6480e53de7247d61d777", "a441295022b23834f8531c54d2b0965f84023278", "7c5d5220dd4df4a531418458ab623ef86c41348c", "44540549ee9a65eb8078e271f43ccded0e8e984f", "d63d82dfb9c2afbacac4c9dc1491f743fb083d52", "d634b381d85dae30492dd6291fc4e6e96143f363", "692e9819a7a1f1b818bf3739c72d8e5252cae661", "166e473e120a86a6edcd32a975ffe19b45ffdd42", "3522d8578fbcd7b46d2a439d5d718dfb570beb7b", "042204fde8e5b74aa5048c6213a8af4450d26fe5", "294442004543aeecc5f3c61cc1b73b2feaff2f92", "53d0ad1f9d50b9f1a72cbecacdacdff7fb4e69eb", "7e137d362f9679125726ef4876355a09d788795e", "973d45ae0da5d9612d30900e39118d67d039b31a", "6b8fd06606f12be187f73e8809e56a49864794f9", "652f88555e8bb16ffeffd9d1fa3d0c49e7925dfc", "38e19d4be0d99bbba35558af2c0620cd9b46f12e", "4c51642038c4a3cc04c0f8f0b8267b17aafd4045", "881f6fb23c818ecfc387d2b134e1cd7328fc5995", "d8155325107dbbb1f8ef44f75553595fe4c8ec8c", "101eae5edb76fefc40b039009eb35bbaaae99386", "3abd88bc1a3c334f53f345998b72e9cf8ae87abf"} else "32ba64b4b83848c0cd8f82af52429e3dea42609f"
        )
    if selected in {"97fa38381d9ce23b63b3bf3751615dc254ab3634", "b099bd7cbefaa1a35d6626d4fd3161afcefa1b48", "bfdf39014db15f237a16d4a50e6cdfd68bdd87b8", "4626d87be155c0b42904610323098c1205515450", "c32704e63844449b1c18a03deb2cd92939999b90", "fab5ebbfda09ebd3fc414b3127e135c66025ccb8", "acb42e2a2b18fee17673d07e06b2f29709de2fb5", "99df05ff50a7a4a9591c17b08f4ed0f8cb0374a3", "04e252186aa42bacde0899e0c9224035c83a6b0d", "44f5b75bc93bcea146ad6fba3ac294405ae8709b", "70789b12dea4d72ce9e7f054c5b6f552ec488f5d", "9db97fb12db1a390d6b2410f0c18333aa31e37da", "60fa67b98286bd84bd591987c5690ae9b15bda3f", "bf981e9d39d4a908d0d5b6f8407cca814c609bdb", "8026fcca228d0feda62ffd9625e16ee0429d621e", "887bf44af34999e8b6c5b63dc7c01c6c13b82c8f", "1a928783cce2c2692d8fe9fd958400a2de060bbf", "9632ac089f8b2d89a6856a42e8fb55206cdba1fa", "b5c6f089a6aecd321d08a40238f3cd502f505b26", "dc9f5f95b1f784bb358d6480e53de7247d61d777", "a441295022b23834f8531c54d2b0965f84023278", "7c5d5220dd4df4a531418458ab623ef86c41348c", "44540549ee9a65eb8078e271f43ccded0e8e984f", "d63d82dfb9c2afbacac4c9dc1491f743fb083d52", "d634b381d85dae30492dd6291fc4e6e96143f363", "692e9819a7a1f1b818bf3739c72d8e5252cae661", "166e473e120a86a6edcd32a975ffe19b45ffdd42", "3522d8578fbcd7b46d2a439d5d718dfb570beb7b", "042204fde8e5b74aa5048c6213a8af4450d26fe5", "294442004543aeecc5f3c61cc1b73b2feaff2f92", "53d0ad1f9d50b9f1a72cbecacdacdff7fb4e69eb", "7e137d362f9679125726ef4876355a09d788795e", "973d45ae0da5d9612d30900e39118d67d039b31a", "6b8fd06606f12be187f73e8809e56a49864794f9", "652f88555e8bb16ffeffd9d1fa3d0c49e7925dfc", "38e19d4be0d99bbba35558af2c0620cd9b46f12e", "4c51642038c4a3cc04c0f8f0b8267b17aafd4045", "881f6fb23c818ecfc387d2b134e1cd7328fc5995", "d8155325107dbbb1f8ef44f75553595fe4c8ec8c", "101eae5edb76fefc40b039009eb35bbaaae99386", "3abd88bc1a3c334f53f345998b72e9cf8ae87abf"}:
        # ZBC capability successor: only the NS2 native characteristics header changed.
        # Seal it separately; all sparse-memory and controller owners remain unchanged.
        new_owner_blobs["encore-active/ns2-runtime/nvdrv/core/hle/service/nvdrv/devices/native_gpu_characteristics.h"] = ("f6217651bf15d13e5be80c0b1b0b76679f02949b" if selected in {"53d0ad1f9d50b9f1a72cbecacdacdff7fb4e69eb", "7e137d362f9679125726ef4876355a09d788795e", "973d45ae0da5d9612d30900e39118d67d039b31a", "6b8fd06606f12be187f73e8809e56a49864794f9", "652f88555e8bb16ffeffd9d1fa3d0c49e7925dfc", "38e19d4be0d99bbba35558af2c0620cd9b46f12e", "4c51642038c4a3cc04c0f8f0b8267b17aafd4045", "881f6fb23c818ecfc387d2b134e1cd7328fc5995", "d8155325107dbbb1f8ef44f75553595fe4c8ec8c", "101eae5edb76fefc40b039009eb35bbaaae99386", "3abd88bc1a3c334f53f345998b72e9cf8ae87abf"} else "ff9d81f1e2f5b65b73b2cf233579591e07267870")
    if selected in {"b099bd7cbefaa1a35d6626d4fd3161afcefa1b48", "bfdf39014db15f237a16d4a50e6cdfd68bdd87b8", "4626d87be155c0b42904610323098c1205515450", "c32704e63844449b1c18a03deb2cd92939999b90", "fab5ebbfda09ebd3fc414b3127e135c66025ccb8", "acb42e2a2b18fee17673d07e06b2f29709de2fb5", "99df05ff50a7a4a9591c17b08f4ed0f8cb0374a3", "04e252186aa42bacde0899e0c9224035c83a6b0d", "44f5b75bc93bcea146ad6fba3ac294405ae8709b", "70789b12dea4d72ce9e7f054c5b6f552ec488f5d", "9db97fb12db1a390d6b2410f0c18333aa31e37da", "60fa67b98286bd84bd591987c5690ae9b15bda3f", "bf981e9d39d4a908d0d5b6f8407cca814c609bdb", "8026fcca228d0feda62ffd9625e16ee0429d621e", "887bf44af34999e8b6c5b63dc7c01c6c13b82c8f", "1a928783cce2c2692d8fe9fd958400a2de060bbf", "9632ac089f8b2d89a6856a42e8fb55206cdba1fa", "b5c6f089a6aecd321d08a40238f3cd502f505b26", "dc9f5f95b1f784bb358d6480e53de7247d61d777", "a441295022b23834f8531c54d2b0965f84023278", "7c5d5220dd4df4a531418458ab623ef86c41348c", "44540549ee9a65eb8078e271f43ccded0e8e984f", "d63d82dfb9c2afbacac4c9dc1491f743fb083d52", "d634b381d85dae30492dd6291fc4e6e96143f363", "692e9819a7a1f1b818bf3739c72d8e5252cae661", "166e473e120a86a6edcd32a975ffe19b45ffdd42", "3522d8578fbcd7b46d2a439d5d718dfb570beb7b", "042204fde8e5b74aa5048c6213a8af4450d26fe5", "294442004543aeecc5f3c61cc1b73b2feaff2f92", "53d0ad1f9d50b9f1a72cbecacdacdff7fb4e69eb", "7e137d362f9679125726ef4876355a09d788795e", "973d45ae0da5d9612d30900e39118d67d039b31a", "6b8fd06606f12be187f73e8809e56a49864794f9", "652f88555e8bb16ffeffd9d1fa3d0c49e7925dfc", "38e19d4be0d99bbba35558af2c0620cd9b46f12e", "4c51642038c4a3cc04c0f8f0b8267b17aafd4045", "881f6fb23c818ecfc387d2b134e1cd7328fc5995", "d8155325107dbbb1f8ef44f75553595fe4c8ec8c", "101eae5edb76fefc40b039009eb35bbaaae99386", "3abd88bc1a3c334f53f345998b72e9cf8ae87abf"}:
        # Native MME DMA_READ/FIFOED successor: seal the two active GPU-dispatch owners.
        new_owner_blobs["encore-active/ns2-runtime/gpu_dispatch/video_core/engines/puller.cpp"] = "02e406d9209de6029bcc526bf800428268b81ed4"
        new_owner_blobs["encore-active/ns2-runtime/gpu_dispatch/video_core/native_ampere_macro_state.h"] = "1f60c4cda2a7d5206082434945f40a1cf2bb546c"
    for relative, expected_blob in new_owner_blobs.items():
        payload=(root/"vendor"/relative).read_bytes()
        actual=hashlib.sha1(
            b"blob "+str(len(payload)).encode()+bytes([0])+payload
        ).hexdigest()
        assert actual==expected_blob, ("R457 successor owner drift",relative,actual)
if selected in {"1a928783cce2c2692d8fe9fd958400a2de060bbf", "9632ac089f8b2d89a6856a42e8fb55206cdba1fa", "b5c6f089a6aecd321d08a40238f3cd502f505b26", "dc9f5f95b1f784bb358d6480e53de7247d61d777", "a441295022b23834f8531c54d2b0965f84023278", "7c5d5220dd4df4a531418458ab623ef86c41348c", "44540549ee9a65eb8078e271f43ccded0e8e984f", "d63d82dfb9c2afbacac4c9dc1491f743fb083d52", "d634b381d85dae30492dd6291fc4e6e96143f363", "692e9819a7a1f1b818bf3739c72d8e5252cae661", "166e473e120a86a6edcd32a975ffe19b45ffdd42", "3522d8578fbcd7b46d2a439d5d718dfb570beb7b", "042204fde8e5b74aa5048c6213a8af4450d26fe5", "294442004543aeecc5f3c61cc1b73b2feaff2f92", "53d0ad1f9d50b9f1a72cbecacdacdff7fb4e69eb", "7e137d362f9679125726ef4876355a09d788795e", "973d45ae0da5d9612d30900e39118d67d039b31a", "6b8fd06606f12be187f73e8809e56a49864794f9", "652f88555e8bb16ffeffd9d1fa3d0c49e7925dfc", "38e19d4be0d99bbba35558af2c0620cd9b46f12e", "4c51642038c4a3cc04c0f8f0b8267b17aafd4045", "881f6fb23c818ecfc387d2b134e1cd7328fc5995", "d8155325107dbbb1f8ef44f75553595fe4c8ec8c", "101eae5edb76fefc40b039009eb35bbaaae99386", "3abd88bc1a3c334f53f345998b72e9cf8ae87abf"}:
    successor = (root/"vendor/tests/ns1_r23_18_tir_host.py").read_bytes()
    assert hashlib.sha1(
        b"blob "+str(len(successor)).encode()+bytes([0])+successor
    ).hexdigest() == ("9ec2e122bee4c7ef3a0889fbf5e8202ae9516339" if selected in {"d63d82dfb9c2afbacac4c9dc1491f743fb083d52", "d634b381d85dae30492dd6291fc4e6e96143f363", "692e9819a7a1f1b818bf3739c72d8e5252cae661", "166e473e120a86a6edcd32a975ffe19b45ffdd42", "3522d8578fbcd7b46d2a439d5d718dfb570beb7b", "042204fde8e5b74aa5048c6213a8af4450d26fe5", "294442004543aeecc5f3c61cc1b73b2feaff2f92", "53d0ad1f9d50b9f1a72cbecacdacdff7fb4e69eb", "7e137d362f9679125726ef4876355a09d788795e", "973d45ae0da5d9612d30900e39118d67d039b31a", "6b8fd06606f12be187f73e8809e56a49864794f9", "652f88555e8bb16ffeffd9d1fa3d0c49e7925dfc", "38e19d4be0d99bbba35558af2c0620cd9b46f12e", "4c51642038c4a3cc04c0f8f0b8267b17aafd4045", "881f6fb23c818ecfc387d2b134e1cd7328fc5995", "d8155325107dbbb1f8ef44f75553595fe4c8ec8c", "101eae5edb76fefc40b039009eb35bbaaae99386", "3abd88bc1a3c334f53f345998b72e9cf8ae87abf"} else "005280fde5bbd862d64a4def0d17d90a35bbe5e9"), "Vendor host-only successor drift"
if selected in {"06705357e48b33d837b1f97dbb1c3979cb3d7c31",
                 "cd5ce4dabef1d32e0441d22dccdee358ebf23287", "a8f327c972bd2f84f6e6f9432c96c4a948963073", "ffa7757e98bf42a5abcd5c0b9e845cfdbc01e75e", "752b92033610b294a36254d5747c317aca51c1d5", "1b5256d72072e05a62fb734bc9ef790fc81c1573", "628d01bdc4368e9ad661d749515f788ef7c03802", "191dd458c68de13f0f71659e3b4a9598af7de561", "b743e9c7ec9832832711fc0ea34e03a25c973557", "4c8f72f8ba3db320af55cea0f53cac16366c3ea0"}:
    # These reviewed NS2 GPU lifecycle successors do not touch the sparse
    # PTE/slab owners checked below. Authenticate the complete selected tree
    # before replaying the earlier sparse receipt graph.
    expected_tree = {
        "06705357e48b33d837b1f97dbb1c3979cb3d7c31":
            "8bd2b8d1378cefffaf0f4e397289ba62ef009112",
        "cd5ce4dabef1d32e0441d22dccdee358ebf23287":
            "2a8d99c8a9912041a286c747c7dcebf5a8cc6f89",
        "a8f327c972bd2f84f6e6f9432c96c4a948963073":
            "747569d1bafefc23fb235e1929bda0f5c0d48de3",
        "ffa7757e98bf42a5abcd5c0b9e845cfdbc01e75e":
            "af3fb89c9c6bb96c19bd2e099273019840536267",
        "752b92033610b294a36254d5747c317aca51c1d5":
            "7ab98eb5286021a9e070397ef6673f61934cf5e0",
        "1b5256d72072e05a62fb734bc9ef790fc81c1573":
            "c54279c46295cc71d27c74af213dcacff0d08810",
        "628d01bdc4368e9ad661d749515f788ef7c03802":
            "48f75fca37a128f9425cc3484d22ab994a1a17a8",
        "191dd458c68de13f0f71659e3b4a9598af7de561":
            "f98956d2a6ce68c6af51bf5e8b53b7516b02bd2e",
        "b743e9c7ec9832832711fc0ea34e03a25c973557":
            "c6eea7dfe0603bfccb44da9b82c95ca1429761fe",
        "4c8f72f8ba3db320af55cea0f53cac16366c3ea0":
            "b300d82e0aa31c9ddde01703bdf446579ce4e0c2",
    }[selected]
    assert subprocess.check_output(
        ["git", "-C", str(root/"vendor"), "rev-parse", "HEAD^{tree}"], text=True
    ).strip() == expected_tree
    reviewed_vendors.add(selected)
assert pinned==selected and pinned in reviewed_vendors,(pinned,selected)
# The reviewed NS2 strict-completion/VA-lifecycle successor changes no sparse PTE/slab owner.
# Its sparse-residency owners are byte-identical to the reviewed 3abd88bc
# baseline, so replay that exact sparse receipt graph after proving the new
# full vendor tree above. This avoids duplicating the successor SHA through
# every historical sparse-era set.
if selected in {"06705357e48b33d837b1f97dbb1c3979cb3d7c31",
                 "cd5ce4dabef1d32e0441d22dccdee358ebf23287", "a8f327c972bd2f84f6e6f9432c96c4a948963073", "ffa7757e98bf42a5abcd5c0b9e845cfdbc01e75e", "752b92033610b294a36254d5747c317aca51c1d5", "1b5256d72072e05a62fb734bc9ef790fc81c1573", "628d01bdc4368e9ad661d749515f788ef7c03802", "191dd458c68de13f0f71659e3b4a9598af7de561", "b743e9c7ec9832832711fc0ea34e03a25c973557", "4c8f72f8ba3db320af55cea0f53cac16366c3ea0"}:
    selected = "3abd88bc1a3c334f53f345998b72e9cf8ae87abf"
def read(path): return (root/path).read_text()
def gitblob(path):
    raw=(root/path).read_bytes()
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+bytes([0])+raw).hexdigest()
for path,expected in (
    ("vendor/encore-active/ns2-runtime/sparse-residency/core/hle/kernel/k_memory_manager.cpp",
     "2b5be4eba2500da2993db2ed1c86d44ddfa5554f" if selected in {"436e702cc970417455c088c4bc38ce5fec8e0762", "6489896230a030cf28d31961c7c8f242cab73f27", "05de9e8e7f75e9a7400a351b18f2b1e83165108e", "ee64fac70671126c9b6ab9aa3b3885a40538cf16", "603e0d5c70b04fa84a19cca8f580ed1bdb230be0", "593bc9ee6ddfcf38e488325ccf318f1a0a109d8e", "6b48e6734e738306dd57ceed8be9b003631eb8cb", "d554e257ae82db66d9542f472dcde067510bfa1f", "93c3dd6c86627e91999f965c45c05cd8e50e17eb", "eb9a454db4d21a3aff2642c72eea3ca01bf2b3bb", "93da3b707ef147385380eb0690e0d93fc8e907ad", "a6240909b823492d9ff20070c09387a732d83007", "0390980a5752808dfba7b8edaa7d113cc4e4e6eb", "273680a5b33bff15c9ca12685cfadb2aa15ff9f1", "84b9975726092a32d1cb2aa714b96e4f5f85d7c4", "84ec89ce112b83603b2095a9f6bb785f8e999ef6", "97fa38381d9ce23b63b3bf3751615dc254ab3634", "b099bd7cbefaa1a35d6626d4fd3161afcefa1b48", "bfdf39014db15f237a16d4a50e6cdfd68bdd87b8", "4626d87be155c0b42904610323098c1205515450", "c32704e63844449b1c18a03deb2cd92939999b90", "fab5ebbfda09ebd3fc414b3127e135c66025ccb8", "acb42e2a2b18fee17673d07e06b2f29709de2fb5", "99df05ff50a7a4a9591c17b08f4ed0f8cb0374a3", "04e252186aa42bacde0899e0c9224035c83a6b0d", "44f5b75bc93bcea146ad6fba3ac294405ae8709b", "70789b12dea4d72ce9e7f054c5b6f552ec488f5d", "9db97fb12db1a390d6b2410f0c18333aa31e37da", "60fa67b98286bd84bd591987c5690ae9b15bda3f", "bf981e9d39d4a908d0d5b6f8407cca814c609bdb", "8026fcca228d0feda62ffd9625e16ee0429d621e", "887bf44af34999e8b6c5b63dc7c01c6c13b82c8f", "1a928783cce2c2692d8fe9fd958400a2de060bbf", "9632ac089f8b2d89a6856a42e8fb55206cdba1fa", "b5c6f089a6aecd321d08a40238f3cd502f505b26", "dc9f5f95b1f784bb358d6480e53de7247d61d777", "a441295022b23834f8531c54d2b0965f84023278", "7c5d5220dd4df4a531418458ab623ef86c41348c", "44540549ee9a65eb8078e271f43ccded0e8e984f", "d63d82dfb9c2afbacac4c9dc1491f743fb083d52", "d634b381d85dae30492dd6291fc4e6e96143f363", "692e9819a7a1f1b818bf3739c72d8e5252cae661", "166e473e120a86a6edcd32a975ffe19b45ffdd42", "3522d8578fbcd7b46d2a439d5d718dfb570beb7b", "042204fde8e5b74aa5048c6213a8af4450d26fe5", "294442004543aeecc5f3c61cc1b73b2feaff2f92", "53d0ad1f9d50b9f1a72cbecacdacdff7fb4e69eb", "7e137d362f9679125726ef4876355a09d788795e", "973d45ae0da5d9612d30900e39118d67d039b31a", "6b8fd06606f12be187f73e8809e56a49864794f9", "652f88555e8bb16ffeffd9d1fa3d0c49e7925dfc", "38e19d4be0d99bbba35558af2c0620cd9b46f12e", "4c51642038c4a3cc04c0f8f0b8267b17aafd4045", "881f6fb23c818ecfc387d2b134e1cd7328fc5995", "d8155325107dbbb1f8ef44f75553595fe4c8ec8c", "101eae5edb76fefc40b039009eb35bbaaae99386", "3abd88bc1a3c334f53f345998b72e9cf8ae87abf"}
     else "6397dd2c4a9c9c10674ab87b344f5c6956b79e0c" if selected == "d3c76f07cd82f7766be7b5e3fc3c399a3be15291"
     else "aeee7f62a3fc609936ff5dc6a64722ca8d860c2e" if selected == "56959a23273ea2ee82d2e59628c92cc9e1144fe9"
     else "12d3d0ddc59308b80df46bc54e6e8ee54011d568" if selected == "fd6eee4933c36ed93d6ef59e2ae5d23fd975f9f2"
     else "c5b5dd99bb9a65286783f4b220d991f422d19e67" if selected in {"ced1b9cdd6f0fa4e0ca7949b404f450aae0055df", "06b453171af26b5703e2fcc5e68c4e8288d758b7"}
     else "88f3e2c9220ee03fd6600ef12441d7ece7527c9d"),
    ("vendor/encore-active/ns2-runtime/sparse-residency/core/hle/kernel/init/init_slab_setup.cpp",
     "130eb7bd53e29b816bb81fec3fa053a584cd4b6e"),
    ("vendor/encore-active/eden-core/overrides/core/device_memory_manager.inc",
     "852a0272696c7ce182bc05aee92bc7cbb195446b" if selected in {"8153654a2f1fe809fb2caa28dcadca90a7661446", "6c38328fbef33de747f5c31ea30d13541a513a4a", "8e564f61e6c8b86149ce0a0d6d2aa323a268dda6", "67759611edc13414c112ea9d2b6664d54827a200"} else "daf493ce6e863397ec44bfae467c4f7533570477"),
):
    assert gitblob(path)==expected,("Unexpected sparse kernel source owner",path)

if selected in {"8153654a2f1fe809fb2caa28dcadca90a7661446", "6c38328fbef33de747f5c31ea30d13541a513a4a", "8e564f61e6c8b86149ce0a0d6d2aa323a268dda6", "67759611edc13414c112ea9d2b6664d54827a200"}:
    deferred_header = "vendor/encore-active/eden-core/overrides/core/deferred_cached_updates.h"
    assert gitblob(deferred_header) == "33262f511777cdd1b4a74ac0cd6dc39caa12c9d0"
    device = read("vendor/encore-active/eden-core/overrides/core/device_memory_manager.inc")
    assert device.count('::Eden::DeferredCachedUpdates::WaitForPublished();') == 1
    assert device.count('::Eden::DeferredCachedUpdates::active_collector') == 1
    assert device.count('::Eden::DeferredCachedUpdates::BeginPublish();') == 0
    assert device.count('#include "core/deferred_cached_updates.h"') == 1
cmake=read("headless/CMakeLists.txt")
kernel_rel="vendor/encore-active/ns2-runtime/sparse-residency/core/hle/kernel/k_memory_manager.cpp"
kernel=read(kernel_rel)
# Preserve every upstream kernel behavior except the four PS5 residency
# precommit guards. A new unreviewed kernel semantic delta blocks admission.
import re
baseline=read("vendor/sources/eden/src/core/hle/kernel/k_memory_manager.cpp")
guarded=(r"^#if defined\(PS5_NATIVE\) && "
         r"defined\(EDEN_NS2_SPARSE_BACKING\)\n"
         r"[\s\S]*?^#endif\n")
guard_count = len(re.findall(guarded,kernel,flags=re.MULTILINE))
normalize=lambda source: re.sub(r"\n\s*\n","\n\n",source).strip()
if selected in {"ced1b9cdd6f0fa4e0ca7949b404f450aae0055df", "06b453171af26b5703e2fcc5e68c4e8288d758b7", "fd6eee4933c36ed93d6ef59e2ae5d23fd975f9f2", "56959a23273ea2ee82d2e59628c92cc9e1144fe9", "d3c76f07cd82f7766be7b5e3fc3c399a3be15291", "436e702cc970417455c088c4bc38ce5fec8e0762", "6489896230a030cf28d31961c7c8f242cab73f27", "05de9e8e7f75e9a7400a351b18f2b1e83165108e", "ee64fac70671126c9b6ab9aa3b3885a40538cf16", "603e0d5c70b04fa84a19cca8f580ed1bdb230be0", "593bc9ee6ddfcf38e488325ccf318f1a0a109d8e", "6b48e6734e738306dd57ceed8be9b003631eb8cb", "d554e257ae82db66d9542f472dcde067510bfa1f", "93c3dd6c86627e91999f965c45c05cd8e50e17eb", "eb9a454db4d21a3aff2642c72eea3ca01bf2b3bb", "93da3b707ef147385380eb0690e0d93fc8e907ad", "a6240909b823492d9ff20070c09387a732d83007", "0390980a5752808dfba7b8edaa7d113cc4e4e6eb", "273680a5b33bff15c9ca12685cfadb2aa15ff9f1", "84b9975726092a32d1cb2aa714b96e4f5f85d7c4", "84ec89ce112b83603b2095a9f6bb785f8e999ef6", "97fa38381d9ce23b63b3bf3751615dc254ab3634", "b099bd7cbefaa1a35d6626d4fd3161afcefa1b48", "bfdf39014db15f237a16d4a50e6cdfd68bdd87b8", "4626d87be155c0b42904610323098c1205515450", "c32704e63844449b1c18a03deb2cd92939999b90", "fab5ebbfda09ebd3fc414b3127e135c66025ccb8", "acb42e2a2b18fee17673d07e06b2f29709de2fb5", "99df05ff50a7a4a9591c17b08f4ed0f8cb0374a3", "04e252186aa42bacde0899e0c9224035c83a6b0d", "44f5b75bc93bcea146ad6fba3ac294405ae8709b", "70789b12dea4d72ce9e7f054c5b6f552ec488f5d", "9db97fb12db1a390d6b2410f0c18333aa31e37da", "60fa67b98286bd84bd591987c5690ae9b15bda3f", "bf981e9d39d4a908d0d5b6f8407cca814c609bdb", "8026fcca228d0feda62ffd9625e16ee0429d621e", "887bf44af34999e8b6c5b63dc7c01c6c13b82c8f", "1a928783cce2c2692d8fe9fd958400a2de060bbf", "9632ac089f8b2d89a6856a42e8fb55206cdba1fa", "b5c6f089a6aecd321d08a40238f3cd502f505b26", "dc9f5f95b1f784bb358d6480e53de7247d61d777", "a441295022b23834f8531c54d2b0965f84023278", "7c5d5220dd4df4a531418458ab623ef86c41348c", "44540549ee9a65eb8078e271f43ccded0e8e984f", "d63d82dfb9c2afbacac4c9dc1491f743fb083d52", "d634b381d85dae30492dd6291fc4e6e96143f363", "692e9819a7a1f1b818bf3739c72d8e5252cae661", "166e473e120a86a6edcd32a975ffe19b45ffdd42", "3522d8578fbcd7b46d2a439d5d718dfb570beb7b", "042204fde8e5b74aa5048c6213a8af4450d26fe5", "294442004543aeecc5f3c61cc1b73b2feaff2f92", "53d0ad1f9d50b9f1a72cbecacdacdff7fb4e69eb", "7e137d362f9679125726ef4876355a09d788795e", "973d45ae0da5d9612d30900e39118d67d039b31a", "6b8fd06606f12be187f73e8809e56a49864794f9", "652f88555e8bb16ffeffd9d1fa3d0c49e7925dfc", "38e19d4be0d99bbba35558af2c0620cd9b46f12e", "4c51642038c4a3cc04c0f8f0b8267b17aafd4045", "881f6fb23c818ecfc387d2b134e1cd7328fc5995", "d8155325107dbbb1f8ef44f75553595fe4c8ec8c", "101eae5edb76fefc40b039009eb35bbaaae99386", "3abd88bc1a3c334f53f345998b72e9cf8ae87abf"}:
    # This exact runtime blob carries the OOM rollback and optimized
    # preflight reviewed after the original R457 source-only parity gate.
    # Its full SHA is already checked above; do not silently normalize an
    # arbitrary new kernel semantic delta.
    if selected in {"436e702cc970417455c088c4bc38ce5fec8e0762",
                    "6489896230a030cf28d31961c7c8f242cab73f27",
                    "05de9e8e7f75e9a7400a351b18f2b1e83165108e",
                    "ee64fac70671126c9b6ab9aa3b3885a40538cf16",
                    "603e0d5c70b04fa84a19cca8f580ed1bdb230be0",
                    "593bc9ee6ddfcf38e488325ccf318f1a0a109d8e",
                    "6b48e6734e738306dd57ceed8be9b003631eb8cb", "d554e257ae82db66d9542f472dcde067510bfa1f", "93c3dd6c86627e91999f965c45c05cd8e50e17eb", "eb9a454db4d21a3aff2642c72eea3ca01bf2b3bb", "93da3b707ef147385380eb0690e0d93fc8e907ad", "a6240909b823492d9ff20070c09387a732d83007", "0390980a5752808dfba7b8edaa7d113cc4e4e6eb", "273680a5b33bff15c9ca12685cfadb2aa15ff9f1", "84b9975726092a32d1cb2aa714b96e4f5f85d7c4", "84ec89ce112b83603b2095a9f6bb785f8e999ef6", "97fa38381d9ce23b63b3bf3751615dc254ab3634", "b099bd7cbefaa1a35d6626d4fd3161afcefa1b48", "bfdf39014db15f237a16d4a50e6cdfd68bdd87b8", "4626d87be155c0b42904610323098c1205515450", "c32704e63844449b1c18a03deb2cd92939999b90", "fab5ebbfda09ebd3fc414b3127e135c66025ccb8", "acb42e2a2b18fee17673d07e06b2f29709de2fb5", "99df05ff50a7a4a9591c17b08f4ed0f8cb0374a3", "04e252186aa42bacde0899e0c9224035c83a6b0d", "44f5b75bc93bcea146ad6fba3ac294405ae8709b", "70789b12dea4d72ce9e7f054c5b6f552ec488f5d", "9db97fb12db1a390d6b2410f0c18333aa31e37da", "60fa67b98286bd84bd591987c5690ae9b15bda3f", "bf981e9d39d4a908d0d5b6f8407cca814c609bdb", "8026fcca228d0feda62ffd9625e16ee0429d621e", "887bf44af34999e8b6c5b63dc7c01c6c13b82c8f", "1a928783cce2c2692d8fe9fd958400a2de060bbf", "9632ac089f8b2d89a6856a42e8fb55206cdba1fa", "b5c6f089a6aecd321d08a40238f3cd502f505b26", "dc9f5f95b1f784bb358d6480e53de7247d61d777", "a441295022b23834f8531c54d2b0965f84023278", "7c5d5220dd4df4a531418458ab623ef86c41348c", "44540549ee9a65eb8078e271f43ccded0e8e984f", "d63d82dfb9c2afbacac4c9dc1491f743fb083d52", "d634b381d85dae30492dd6291fc4e6e96143f363", "692e9819a7a1f1b818bf3739c72d8e5252cae661", "166e473e120a86a6edcd32a975ffe19b45ffdd42", "3522d8578fbcd7b46d2a439d5d718dfb570beb7b", "042204fde8e5b74aa5048c6213a8af4450d26fe5", "294442004543aeecc5f3c61cc1b73b2feaff2f92", "53d0ad1f9d50b9f1a72cbecacdacdff7fb4e69eb", "7e137d362f9679125726ef4876355a09d788795e", "973d45ae0da5d9612d30900e39118d67d039b31a", "6b8fd06606f12be187f73e8809e56a49864794f9", "652f88555e8bb16ffeffd9d1fa3d0c49e7925dfc", "38e19d4be0d99bbba35558af2c0620cd9b46f12e", "4c51642038c4a3cc04c0f8f0b8267b17aafd4045", "881f6fb23c818ecfc387d2b134e1cd7328fc5995", "d8155325107dbbb1f8ef44f75553595fe4c8ec8c", "101eae5edb76fefc40b039009eb35bbaaae99386", "3abd88bc1a3c334f53f345998b72e9cf8ae87abf"}:
        # Exact blob 2b5be4eb adds a guarded try/catch pair around optimized
        # metadata initialization, so the textual guard count is seven.
        assert guard_count == 7
    else:
        assert guard_count == 5
    allocation = kernel.split("Result KMemoryManager::AllocateForProcess(",1)[1].split(
        "size_t KMemoryManager::Impl::Initialize(",1)[0]
    assert allocation.index("CommitKernelDirectGuestRange(m_system, block.GetAddress()") < (
        allocation.index("manager.ProcessOptimizedAllocation("))
    assert "any_new |= manager.ProcessOptimizedAllocation(" in allocation
    assert allocation.count("R_THROW(ResultOutOfMemory);") == 2
else:
    assert guard_count == 4
    stripped=re.sub(guarded,"",kernel,flags=re.MULTILINE)
    stripped=stripped.replace("#include <new>\n#include <limits>\n","")
    assert normalize(stripped)==normalize(baseline), "kernel semantics drift"
assert "set(EDEN_NS2_SPARSE_BACKING OFF)" in cmake
assert "set(EDEN_NS2_SPARSE_BACKING ON)" in cmake
# KPort and KPageBuffer both write guest physical pages before a process
# maps them. The linked sparse direct-memory owner must commit both first.
assert 'EDEN_R457_SPARSE_SLAB_SRC' in cmake
assert 'list(REMOVE_ITEM eden_r457_sparse_kernel_units' in cmake
assert 'set_property(SOURCE "${EDEN_R457_SPARSE_SLAB_SRC}"' in cmake
subprocess.run([sys.executable, "-B",
    str(root / "vendor/tests/ns2_r457_kernel_slab_precommit_host.py")], check=True)

assert kernel_rel.replace("vendor/","") in cmake
assert 'list(REMOVE_ITEM eden_r457_sparse_kernel_units' in cmake
assert 'hle/kernel/k_memory_manager.cpp' in cmake

# Slabs are direct host writes before the kernel PTE/metadata paths.
# Preserve exactly the original source with only two sparse/native guards,
# including one call before DeviceMemory::GetPointer or freelist initialization.
slab_rel = "vendor/encore-active/ns2-runtime/sparse-residency/core/hle/kernel/init/init_slab_setup.cpp"
slab = read(slab_rel)
slab_baseline = read("vendor/sources/eden/src/core/hle/kernel/init/init_slab_setup.cpp")
slab_guarded = re.findall(guarded, slab, flags=re.MULTILINE)
assert len(slab_guarded) == 3, "slab direct-memory diff exceeded declaration and two reviewed guards"
assert normalize(re.sub(guarded, "", slab, flags=re.MULTILINE)) == normalize(slab_baseline), (
    "unreviewed slab kernel semantics drift")
start = slab.index("    if (size > 0) {")
end = slab.index("    return start + size;", start)
direct_slab = slab[start:end]
assert direct_slab.count("EdenNs2CommitGuestBacking(") == 1
assert direct_slab.index("EdenNs2CommitGuestBacking(") < direct_slab.index(
    "void* backing_kernel_memory")
assert 'throw std::bad_alloc{};' in direct_slab
page_slab = slab.split("void KPageBufferSlabHeap::Initialize(",1)[1]
assert page_slab.count("EdenNs2CommitGuestBacking(") == 1
assert page_slab.index("EdenNs2CommitGuestBacking(") < page_slab.index(
    "KPageBuffer::InitializeSlabHeap(")
assert 'physical - Core::DramMemoryMap::Base, slab_size' in page_slab

assert slab_rel.replace("vendor/", "") in cmake
assert 'hle/kernel/init/init_slab_setup.cpp" eden_r457_sparse_slab_original' in cmake
assert 'TARGET_DIRECTORY core APPEND PROPERTY COMPILE_DEFINITIONS "PS5_NATIVE=1"' in cmake

for variant in ("memory_native_a32.cpp","memory_native_standard.cpp"):
    owner=read("vendor/encore-active/eden-core/src/core/"+variant)
    begin=owner.index("    void MapMemoryRegion(")
    end=owner.index("    void UnmapRegion(",begin)
    section=owner[begin:end]
    if selected in {"fd6eee4933c36ed93d6ef59e2ae5d23fd975f9f2", "56959a23273ea2ee82d2e59628c92cc9e1144fe9", "d3c76f07cd82f7766be7b5e3fc3c399a3be15291", "436e702cc970417455c088c4bc38ce5fec8e0762", "6489896230a030cf28d31961c7c8f242cab73f27", "05de9e8e7f75e9a7400a351b18f2b1e83165108e", "ee64fac70671126c9b6ab9aa3b3885a40538cf16", "603e0d5c70b04fa84a19cca8f580ed1bdb230be0", "593bc9ee6ddfcf38e488325ccf318f1a0a109d8e", "6b48e6734e738306dd57ceed8be9b003631eb8cb", "d554e257ae82db66d9542f472dcde067510bfa1f", "93c3dd6c86627e91999f965c45c05cd8e50e17eb", "eb9a454db4d21a3aff2642c72eea3ca01bf2b3bb", "93da3b707ef147385380eb0690e0d93fc8e907ad", "a6240909b823492d9ff20070c09387a732d83007", "0390980a5752808dfba7b8edaa7d113cc4e4e6eb", "273680a5b33bff15c9ca12685cfadb2aa15ff9f1", "84b9975726092a32d1cb2aa714b96e4f5f85d7c4", "84ec89ce112b83603b2095a9f6bb785f8e999ef6", "97fa38381d9ce23b63b3bf3751615dc254ab3634", "b099bd7cbefaa1a35d6626d4fd3161afcefa1b48", "bfdf39014db15f237a16d4a50e6cdfd68bdd87b8", "4626d87be155c0b42904610323098c1205515450", "c32704e63844449b1c18a03deb2cd92939999b90", "fab5ebbfda09ebd3fc414b3127e135c66025ccb8", "acb42e2a2b18fee17673d07e06b2f29709de2fb5", "99df05ff50a7a4a9591c17b08f4ed0f8cb0374a3", "04e252186aa42bacde0899e0c9224035c83a6b0d", "44f5b75bc93bcea146ad6fba3ac294405ae8709b", "70789b12dea4d72ce9e7f054c5b6f552ec488f5d", "9db97fb12db1a390d6b2410f0c18333aa31e37da", "60fa67b98286bd84bd591987c5690ae9b15bda3f", "bf981e9d39d4a908d0d5b6f8407cca814c609bdb", "8026fcca228d0feda62ffd9625e16ee0429d621e", "887bf44af34999e8b6c5b63dc7c01c6c13b82c8f", "1a928783cce2c2692d8fe9fd958400a2de060bbf", "9632ac089f8b2d89a6856a42e8fb55206cdba1fa", "b5c6f089a6aecd321d08a40238f3cd502f505b26", "dc9f5f95b1f784bb358d6480e53de7247d61d777", "a441295022b23834f8531c54d2b0965f84023278", "7c5d5220dd4df4a531418458ab623ef86c41348c", "44540549ee9a65eb8078e271f43ccded0e8e984f", "d63d82dfb9c2afbacac4c9dc1491f743fb083d52", "d634b381d85dae30492dd6291fc4e6e96143f363", "692e9819a7a1f1b818bf3739c72d8e5252cae661", "166e473e120a86a6edcd32a975ffe19b45ffdd42", "3522d8578fbcd7b46d2a439d5d718dfb570beb7b", "042204fde8e5b74aa5048c6213a8af4450d26fe5", "294442004543aeecc5f3c61cc1b73b2feaff2f92", "53d0ad1f9d50b9f1a72cbecacdacdff7fb4e69eb", "7e137d362f9679125726ef4876355a09d788795e", "973d45ae0da5d9612d30900e39118d67d039b31a", "6b8fd06606f12be187f73e8809e56a49864794f9", "652f88555e8bb16ffeffd9d1fa3d0c49e7925dfc", "38e19d4be0d99bbba35558af2c0620cd9b46f12e", "4c51642038c4a3cc04c0f8f0b8267b17aafd4045", "881f6fb23c818ecfc387d2b134e1cd7328fc5995", "d8155325107dbbb1f8ef44f75553595fe4c8ec8c", "101eae5edb76fefc40b039009eb35bbaaae99386", "3abd88bc1a3c334f53f345998b72e9cf8ae87abf"}:
        assert section.count("EdenNs2EnsureGuestBackingReadable(")==1,variant
        assert "EdenNs2CommitGuestBacking(" not in section,variant
        assert section.index("EdenNs2EnsureGuestBackingReadable(")<section.index(
            "MapPages(page_table"),variant
    else:
        assert section.count("EdenNs2CommitGuestBacking(")==1,variant
        assert section.index("EdenNs2CommitGuestBacking(")<section.index(
            "MapPages(page_table"),variant
    assert 'throw std::bad_alloc{};' in section,variant
    if selected in {"6489896230a030cf28d31961c7c8f242cab73f27", "05de9e8e7f75e9a7400a351b18f2b1e83165108e", "ee64fac70671126c9b6ab9aa3b3885a40538cf16", "603e0d5c70b04fa84a19cca8f580ed1bdb230be0", "593bc9ee6ddfcf38e488325ccf318f1a0a109d8e", "6b48e6734e738306dd57ceed8be9b003631eb8cb", "d554e257ae82db66d9542f472dcde067510bfa1f", "93c3dd6c86627e91999f965c45c05cd8e50e17eb", "eb9a454db4d21a3aff2642c72eea3ca01bf2b3bb", "93da3b707ef147385380eb0690e0d93fc8e907ad", "a6240909b823492d9ff20070c09387a732d83007", "0390980a5752808dfba7b8edaa7d113cc4e4e6eb", "273680a5b33bff15c9ca12685cfadb2aa15ff9f1", "84b9975726092a32d1cb2aa714b96e4f5f85d7c4", "84ec89ce112b83603b2095a9f6bb785f8e999ef6", "97fa38381d9ce23b63b3bf3751615dc254ab3634", "b099bd7cbefaa1a35d6626d4fd3161afcefa1b48", "bfdf39014db15f237a16d4a50e6cdfd68bdd87b8", "4626d87be155c0b42904610323098c1205515450", "c32704e63844449b1c18a03deb2cd92939999b90", "fab5ebbfda09ebd3fc414b3127e135c66025ccb8", "acb42e2a2b18fee17673d07e06b2f29709de2fb5", "99df05ff50a7a4a9591c17b08f4ed0f8cb0374a3", "04e252186aa42bacde0899e0c9224035c83a6b0d", "44f5b75bc93bcea146ad6fba3ac294405ae8709b", "70789b12dea4d72ce9e7f054c5b6f552ec488f5d", "9db97fb12db1a390d6b2410f0c18333aa31e37da", "60fa67b98286bd84bd591987c5690ae9b15bda3f", "bf981e9d39d4a908d0d5b6f8407cca814c609bdb", "8026fcca228d0feda62ffd9625e16ee0429d621e", "887bf44af34999e8b6c5b63dc7c01c6c13b82c8f", "1a928783cce2c2692d8fe9fd958400a2de060bbf", "9632ac089f8b2d89a6856a42e8fb55206cdba1fa", "b5c6f089a6aecd321d08a40238f3cd502f505b26", "dc9f5f95b1f784bb358d6480e53de7247d61d777", "a441295022b23834f8531c54d2b0965f84023278", "7c5d5220dd4df4a531418458ab623ef86c41348c", "44540549ee9a65eb8078e271f43ccded0e8e984f", "d63d82dfb9c2afbacac4c9dc1491f743fb083d52", "d634b381d85dae30492dd6291fc4e6e96143f363", "692e9819a7a1f1b818bf3739c72d8e5252cae661", "166e473e120a86a6edcd32a975ffe19b45ffdd42", "3522d8578fbcd7b46d2a439d5d718dfb570beb7b", "042204fde8e5b74aa5048c6213a8af4450d26fe5", "294442004543aeecc5f3c61cc1b73b2feaff2f92", "53d0ad1f9d50b9f1a72cbecacdacdff7fb4e69eb", "7e137d362f9679125726ef4876355a09d788795e", "973d45ae0da5d9612d30900e39118d67d039b31a", "6b8fd06606f12be187f73e8809e56a49864794f9", "652f88555e8bb16ffeffd9d1fa3d0c49e7925dfc", "38e19d4be0d99bbba35558af2c0620cd9b46f12e", "4c51642038c4a3cc04c0f8f0b8267b17aafd4045", "881f6fb23c818ecfc387d2b134e1cd7328fc5995", "d8155325107dbbb1f8ef44f75553595fe4c8ec8c", "101eae5edb76fefc40b039009eb35bbaaae99386", "3abd88bc1a3c334f53f345998b72e9cf8ae87abf"}:
        zero=owner.split("    bool ZeroBlock(",1)[1].split(
            "    bool CopyBlock(",1)[0]
        assert "buffer.ClearBackingRegion(" in zero,variant
        if selected in {"6b48e6734e738306dd57ceed8be9b003631eb8cb", "d554e257ae82db66d9542f472dcde067510bfa1f", "93c3dd6c86627e91999f965c45c05cd8e50e17eb", "eb9a454db4d21a3aff2642c72eea3ca01bf2b3bb", "93da3b707ef147385380eb0690e0d93fc8e907ad", "a6240909b823492d9ff20070c09387a732d83007", "0390980a5752808dfba7b8edaa7d113cc4e4e6eb", "273680a5b33bff15c9ca12685cfadb2aa15ff9f1", "84b9975726092a32d1cb2aa714b96e4f5f85d7c4", "84ec89ce112b83603b2095a9f6bb785f8e999ef6", "97fa38381d9ce23b63b3bf3751615dc254ab3634", "b099bd7cbefaa1a35d6626d4fd3161afcefa1b48", "bfdf39014db15f237a16d4a50e6cdfd68bdd87b8", "4626d87be155c0b42904610323098c1205515450", "c32704e63844449b1c18a03deb2cd92939999b90", "fab5ebbfda09ebd3fc414b3127e135c66025ccb8", "acb42e2a2b18fee17673d07e06b2f29709de2fb5", "99df05ff50a7a4a9591c17b08f4ed0f8cb0374a3", "04e252186aa42bacde0899e0c9224035c83a6b0d", "44f5b75bc93bcea146ad6fba3ac294405ae8709b", "70789b12dea4d72ce9e7f054c5b6f552ec488f5d", "9db97fb12db1a390d6b2410f0c18333aa31e37da", "60fa67b98286bd84bd591987c5690ae9b15bda3f", "bf981e9d39d4a908d0d5b6f8407cca814c609bdb", "8026fcca228d0feda62ffd9625e16ee0429d621e", "887bf44af34999e8b6c5b63dc7c01c6c13b82c8f", "1a928783cce2c2692d8fe9fd958400a2de060bbf", "9632ac089f8b2d89a6856a42e8fb55206cdba1fa", "b5c6f089a6aecd321d08a40238f3cd502f505b26", "dc9f5f95b1f784bb358d6480e53de7247d61d777", "a441295022b23834f8531c54d2b0965f84023278", "7c5d5220dd4df4a531418458ab623ef86c41348c", "44540549ee9a65eb8078e271f43ccded0e8e984f", "d63d82dfb9c2afbacac4c9dc1491f743fb083d52", "d634b381d85dae30492dd6291fc4e6e96143f363", "692e9819a7a1f1b818bf3739c72d8e5252cae661", "166e473e120a86a6edcd32a975ffe19b45ffdd42", "3522d8578fbcd7b46d2a439d5d718dfb570beb7b", "042204fde8e5b74aa5048c6213a8af4450d26fe5", "294442004543aeecc5f3c61cc1b73b2feaff2f92", "53d0ad1f9d50b9f1a72cbecacdacdff7fb4e69eb", "7e137d362f9679125726ef4876355a09d788795e", "973d45ae0da5d9612d30900e39118d67d039b31a", "6b8fd06606f12be187f73e8809e56a49864794f9", "652f88555e8bb16ffeffd9d1fa3d0c49e7925dfc", "38e19d4be0d99bbba35558af2c0620cd9b46f12e", "4c51642038c4a3cc04c0f8f0b8267b17aafd4045", "881f6fb23c818ecfc387d2b134e1cd7328fc5995", "d8155325107dbbb1f8ef44f75553595fe4c8ec8c", "101eae5edb76fefc40b039009eb35bbaaae99386", "3abd88bc1a3c334f53f345998b72e9cf8ae87abf"}:
            assert "(12ull << 30)" not in zero,variant
            assert "either NS1 or NS2" in zero,variant
        else:
            assert "(12ull << 30)" in zero,variant
        assert zero.index("buffer.ClearBackingRegion(") < zero.index("std::memset(ptr, 0, copy_amount)"),variant

metadata=kernel.split("void KMemoryManager::Impl::InitializeOptimizedMemory",1)[1].split(
    "void KMemoryManager::Impl::TrackUnoptimizedAllocation",1)[0]
if selected in {"56959a23273ea2ee82d2e59628c92cc9e1144fe9", "d3c76f07cd82f7766be7b5e3fc3c399a3be15291"}:
    assert "buffer.ClearBackingRegion(" in metadata
    assert "CommitKernelDirectGuestRange(" not in metadata
    assert "GetPointer<u64>(" not in metadata
    assert "std::memset(" not in metadata
else:
    assert metadata.index("CommitKernelDirectGuestRange(")<metadata.index("GetPointer<u64>(")
    assert metadata.index("CommitKernelDirectGuestRange(")<metadata.index("std::memset(")

optimized=kernel.split("bool KMemoryManager::Impl::ProcessOptimizedAllocation",1)[1].split(
    "size_t KMemoryManager::Impl::CalculateManagementOverheadSize",1)[0]
if selected in {"fd6eee4933c36ed93d6ef59e2ae5d23fd975f9f2", "56959a23273ea2ee82d2e59628c92cc9e1144fe9", "d3c76f07cd82f7766be7b5e3fc3c399a3be15291", "436e702cc970417455c088c4bc38ce5fec8e0762", "6489896230a030cf28d31961c7c8f242cab73f27", "05de9e8e7f75e9a7400a351b18f2b1e83165108e", "ee64fac70671126c9b6ab9aa3b3885a40538cf16", "603e0d5c70b04fa84a19cca8f580ed1bdb230be0", "593bc9ee6ddfcf38e488325ccf318f1a0a109d8e", "6b48e6734e738306dd57ceed8be9b003631eb8cb", "d554e257ae82db66d9542f472dcde067510bfa1f", "93c3dd6c86627e91999f965c45c05cd8e50e17eb", "eb9a454db4d21a3aff2642c72eea3ca01bf2b3bb", "93da3b707ef147385380eb0690e0d93fc8e907ad", "a6240909b823492d9ff20070c09387a732d83007", "0390980a5752808dfba7b8edaa7d113cc4e4e6eb", "273680a5b33bff15c9ca12685cfadb2aa15ff9f1", "84b9975726092a32d1cb2aa714b96e4f5f85d7c4", "84ec89ce112b83603b2095a9f6bb785f8e999ef6", "97fa38381d9ce23b63b3bf3751615dc254ab3634", "b099bd7cbefaa1a35d6626d4fd3161afcefa1b48", "bfdf39014db15f237a16d4a50e6cdfd68bdd87b8", "4626d87be155c0b42904610323098c1205515450", "c32704e63844449b1c18a03deb2cd92939999b90", "fab5ebbfda09ebd3fc414b3127e135c66025ccb8", "acb42e2a2b18fee17673d07e06b2f29709de2fb5", "99df05ff50a7a4a9591c17b08f4ed0f8cb0374a3", "04e252186aa42bacde0899e0c9224035c83a6b0d", "44f5b75bc93bcea146ad6fba3ac294405ae8709b", "70789b12dea4d72ce9e7f054c5b6f552ec488f5d", "9db97fb12db1a390d6b2410f0c18333aa31e37da", "60fa67b98286bd84bd591987c5690ae9b15bda3f", "bf981e9d39d4a908d0d5b6f8407cca814c609bdb", "8026fcca228d0feda62ffd9625e16ee0429d621e", "887bf44af34999e8b6c5b63dc7c01c6c13b82c8f", "1a928783cce2c2692d8fe9fd958400a2de060bbf", "9632ac089f8b2d89a6856a42e8fb55206cdba1fa", "b5c6f089a6aecd321d08a40238f3cd502f505b26", "dc9f5f95b1f784bb358d6480e53de7247d61d777", "a441295022b23834f8531c54d2b0965f84023278", "7c5d5220dd4df4a531418458ab623ef86c41348c", "44540549ee9a65eb8078e271f43ccded0e8e984f", "d63d82dfb9c2afbacac4c9dc1491f743fb083d52", "d634b381d85dae30492dd6291fc4e6e96143f363", "692e9819a7a1f1b818bf3739c72d8e5252cae661", "166e473e120a86a6edcd32a975ffe19b45ffdd42", "3522d8578fbcd7b46d2a439d5d718dfb570beb7b", "042204fde8e5b74aa5048c6213a8af4450d26fe5", "294442004543aeecc5f3c61cc1b73b2feaff2f92", "53d0ad1f9d50b9f1a72cbecacdacdff7fb4e69eb", "7e137d362f9679125726ef4876355a09d788795e", "973d45ae0da5d9612d30900e39118d67d039b31a", "6b8fd06606f12be187f73e8809e56a49864794f9", "652f88555e8bb16ffeffd9d1fa3d0c49e7925dfc", "38e19d4be0d99bbba35558af2c0620cd9b46f12e", "4c51642038c4a3cc04c0f8f0b8267b17aafd4045", "881f6fb23c818ecfc387d2b134e1cd7328fc5995", "d8155325107dbbb1f8ef44f75553595fe4c8ec8c", "101eae5edb76fefc40b039009eb35bbaaae99386", "3abd88bc1a3c334f53f345998b72e9cf8ae87abf"}:
    assert "device_memory.buffer.ClearBackingRegion(" in optimized
    assert "CommitKernelDirectGuestRange(kernel.System(), block" not in optimized
else:
    assert optimized.index("CommitKernelDirectGuestRange(")<optimized.index("GetPointer<u64>(")
    assert optimized.index("CommitKernelDirectGuestRange(")<optimized.index("std::memset(")
assert 'Core::DramMemoryMap::Base' in kernel
if selected in {"d3c76f07cd82f7766be7b5e3fc3c399a3be15291", "436e702cc970417455c088c4bc38ce5fec8e0762", "6489896230a030cf28d31961c7c8f242cab73f27", "05de9e8e7f75e9a7400a351b18f2b1e83165108e", "ee64fac70671126c9b6ab9aa3b3885a40538cf16", "603e0d5c70b04fa84a19cca8f580ed1bdb230be0", "593bc9ee6ddfcf38e488325ccf318f1a0a109d8e", "6b48e6734e738306dd57ceed8be9b003631eb8cb", "d554e257ae82db66d9542f472dcde067510bfa1f", "93c3dd6c86627e91999f965c45c05cd8e50e17eb", "eb9a454db4d21a3aff2642c72eea3ca01bf2b3bb", "93da3b707ef147385380eb0690e0d93fc8e907ad", "a6240909b823492d9ff20070c09387a732d83007", "0390980a5752808dfba7b8edaa7d113cc4e4e6eb", "273680a5b33bff15c9ca12685cfadb2aa15ff9f1", "84b9975726092a32d1cb2aa714b96e4f5f85d7c4", "84ec89ce112b83603b2095a9f6bb785f8e999ef6", "97fa38381d9ce23b63b3bf3751615dc254ab3634", "b099bd7cbefaa1a35d6626d4fd3161afcefa1b48", "bfdf39014db15f237a16d4a50e6cdfd68bdd87b8", "4626d87be155c0b42904610323098c1205515450", "c32704e63844449b1c18a03deb2cd92939999b90", "fab5ebbfda09ebd3fc414b3127e135c66025ccb8", "acb42e2a2b18fee17673d07e06b2f29709de2fb5", "99df05ff50a7a4a9591c17b08f4ed0f8cb0374a3", "04e252186aa42bacde0899e0c9224035c83a6b0d", "44f5b75bc93bcea146ad6fba3ac294405ae8709b", "70789b12dea4d72ce9e7f054c5b6f552ec488f5d", "9db97fb12db1a390d6b2410f0c18333aa31e37da", "60fa67b98286bd84bd591987c5690ae9b15bda3f", "bf981e9d39d4a908d0d5b6f8407cca814c609bdb", "8026fcca228d0feda62ffd9625e16ee0429d621e", "887bf44af34999e8b6c5b63dc7c01c6c13b82c8f", "1a928783cce2c2692d8fe9fd958400a2de060bbf", "9632ac089f8b2d89a6856a42e8fb55206cdba1fa", "b5c6f089a6aecd321d08a40238f3cd502f505b26", "dc9f5f95b1f784bb358d6480e53de7247d61d777", "a441295022b23834f8531c54d2b0965f84023278", "7c5d5220dd4df4a531418458ab623ef86c41348c", "44540549ee9a65eb8078e271f43ccded0e8e984f", "d63d82dfb9c2afbacac4c9dc1491f743fb083d52", "d634b381d85dae30492dd6291fc4e6e96143f363", "692e9819a7a1f1b818bf3739c72d8e5252cae661", "166e473e120a86a6edcd32a975ffe19b45ffdd42", "3522d8578fbcd7b46d2a439d5d718dfb570beb7b", "042204fde8e5b74aa5048c6213a8af4450d26fe5", "294442004543aeecc5f3c61cc1b73b2feaff2f92", "53d0ad1f9d50b9f1a72cbecacdacdff7fb4e69eb", "7e137d362f9679125726ef4876355a09d788795e", "973d45ae0da5d9612d30900e39118d67d039b31a", "6b8fd06606f12be187f73e8809e56a49864794f9", "652f88555e8bb16ffeffd9d1fa3d0c49e7925dfc", "38e19d4be0d99bbba35558af2c0620cd9b46f12e", "4c51642038c4a3cc04c0f8f0b8267b17aafd4045", "881f6fb23c818ecfc387d2b134e1cd7328fc5995", "d8155325107dbbb1f8ef44f75553595fe4c8ec8c", "101eae5edb76fefc40b039009eb35bbaaae99386", "3abd88bc1a3c334f53f345998b72e9cf8ae87abf"}:
    track_unoptimized=kernel.split("void KMemoryManager::Impl::TrackUnoptimizedAllocation",1)[1].split(
        "void KMemoryManager::Impl::TrackOptimizedAllocation",1)[0]
    assert "if (word & mask)" in track_unoptimized
    assert "word &= ~mask;" in track_unoptimized

gpu=read("vendor/encore-active/eden-core/overrides/core/device_memory_manager.inc")
mapping=gpu.split("void DeviceMemoryManager<Traits>::Map(",1)[1].split(
    "void DeviceMemoryManager<Traits>::Unmap(",1)[0]
assert mapping.count("AtomicStorePhysical(valid, phys_addr);")==1
assert mapping.index("process_memory->GetPointerSilent(")<mapping.index(
    "AtomicStorePhysical(valid, phys_addr);")
assert gpu.count("AtomicStorePhysical(")==3, "Unexpected new GPU PA publisher: review separately"

if selected in {"05de9e8e7f75e9a7400a351b18f2b1e83165108e", "ee64fac70671126c9b6ab9aa3b3885a40538cf16", "603e0d5c70b04fa84a19cca8f580ed1bdb230be0", "593bc9ee6ddfcf38e488325ccf318f1a0a109d8e", "6b48e6734e738306dd57ceed8be9b003631eb8cb", "d554e257ae82db66d9542f472dcde067510bfa1f", "93c3dd6c86627e91999f965c45c05cd8e50e17eb", "eb9a454db4d21a3aff2642c72eea3ca01bf2b3bb", "93da3b707ef147385380eb0690e0d93fc8e907ad", "a6240909b823492d9ff20070c09387a732d83007", "0390980a5752808dfba7b8edaa7d113cc4e4e6eb", "273680a5b33bff15c9ca12685cfadb2aa15ff9f1", "84b9975726092a32d1cb2aa714b96e4f5f85d7c4", "84ec89ce112b83603b2095a9f6bb785f8e999ef6", "97fa38381d9ce23b63b3bf3751615dc254ab3634", "b099bd7cbefaa1a35d6626d4fd3161afcefa1b48", "bfdf39014db15f237a16d4a50e6cdfd68bdd87b8", "4626d87be155c0b42904610323098c1205515450", "c32704e63844449b1c18a03deb2cd92939999b90", "fab5ebbfda09ebd3fc414b3127e135c66025ccb8", "acb42e2a2b18fee17673d07e06b2f29709de2fb5", "99df05ff50a7a4a9591c17b08f4ed0f8cb0374a3", "04e252186aa42bacde0899e0c9224035c83a6b0d", "44f5b75bc93bcea146ad6fba3ac294405ae8709b", "70789b12dea4d72ce9e7f054c5b6f552ec488f5d", "9db97fb12db1a390d6b2410f0c18333aa31e37da", "60fa67b98286bd84bd591987c5690ae9b15bda3f", "bf981e9d39d4a908d0d5b6f8407cca814c609bdb", "8026fcca228d0feda62ffd9625e16ee0429d621e", "887bf44af34999e8b6c5b63dc7c01c6c13b82c8f", "1a928783cce2c2692d8fe9fd958400a2de060bbf", "9632ac089f8b2d89a6856a42e8fb55206cdba1fa", "b5c6f089a6aecd321d08a40238f3cd502f505b26", "dc9f5f95b1f784bb358d6480e53de7247d61d777", "a441295022b23834f8531c54d2b0965f84023278", "7c5d5220dd4df4a531418458ab623ef86c41348c", "44540549ee9a65eb8078e271f43ccded0e8e984f", "d63d82dfb9c2afbacac4c9dc1491f743fb083d52", "d634b381d85dae30492dd6291fc4e6e96143f363", "692e9819a7a1f1b818bf3739c72d8e5252cae661", "166e473e120a86a6edcd32a975ffe19b45ffdd42", "3522d8578fbcd7b46d2a439d5d718dfb570beb7b", "042204fde8e5b74aa5048c6213a8af4450d26fe5", "294442004543aeecc5f3c61cc1b73b2feaff2f92", "53d0ad1f9d50b9f1a72cbecacdacdff7fb4e69eb", "7e137d362f9679125726ef4876355a09d788795e", "973d45ae0da5d9612d30900e39118d67d039b31a", "6b8fd06606f12be187f73e8809e56a49864794f9", "652f88555e8bb16ffeffd9d1fa3d0c49e7925dfc", "38e19d4be0d99bbba35558af2c0620cd9b46f12e", "4c51642038c4a3cc04c0f8f0b8267b17aafd4045", "881f6fb23c818ecfc387d2b134e1cd7328fc5995", "d8155325107dbbb1f8ef44f75553595fe4c8ec8c", "101eae5edb76fefc40b039009eb35bbaaae99386", "3abd88bc1a3c334f53f345998b72e9cf8ae87abf"}:
    page_heap=read("vendor/encore-active/ns2-runtime/sparse-residency/core/hle/kernel/k_page_heap.cpp")
    assert "EdenNs2GuestBackingFreed(" in page_heap
    if selected in {"ee64fac70671126c9b6ab9aa3b3885a40538cf16", "603e0d5c70b04fa84a19cca8f580ed1bdb230be0", "593bc9ee6ddfcf38e488325ccf318f1a0a109d8e", "6b48e6734e738306dd57ceed8be9b003631eb8cb", "d554e257ae82db66d9542f472dcde067510bfa1f", "93c3dd6c86627e91999f965c45c05cd8e50e17eb", "eb9a454db4d21a3aff2642c72eea3ca01bf2b3bb", "93da3b707ef147385380eb0690e0d93fc8e907ad", "a6240909b823492d9ff20070c09387a732d83007", "0390980a5752808dfba7b8edaa7d113cc4e4e6eb", "273680a5b33bff15c9ca12685cfadb2aa15ff9f1", "84b9975726092a32d1cb2aa714b96e4f5f85d7c4", "84ec89ce112b83603b2095a9f6bb785f8e999ef6", "97fa38381d9ce23b63b3bf3751615dc254ab3634", "b099bd7cbefaa1a35d6626d4fd3161afcefa1b48", "bfdf39014db15f237a16d4a50e6cdfd68bdd87b8", "4626d87be155c0b42904610323098c1205515450", "c32704e63844449b1c18a03deb2cd92939999b90", "fab5ebbfda09ebd3fc414b3127e135c66025ccb8", "acb42e2a2b18fee17673d07e06b2f29709de2fb5", "99df05ff50a7a4a9591c17b08f4ed0f8cb0374a3", "04e252186aa42bacde0899e0c9224035c83a6b0d", "44f5b75bc93bcea146ad6fba3ac294405ae8709b", "70789b12dea4d72ce9e7f054c5b6f552ec488f5d", "9db97fb12db1a390d6b2410f0c18333aa31e37da", "60fa67b98286bd84bd591987c5690ae9b15bda3f", "bf981e9d39d4a908d0d5b6f8407cca814c609bdb", "8026fcca228d0feda62ffd9625e16ee0429d621e", "887bf44af34999e8b6c5b63dc7c01c6c13b82c8f", "1a928783cce2c2692d8fe9fd958400a2de060bbf", "9632ac089f8b2d89a6856a42e8fb55206cdba1fa", "b5c6f089a6aecd321d08a40238f3cd502f505b26", "dc9f5f95b1f784bb358d6480e53de7247d61d777", "a441295022b23834f8531c54d2b0965f84023278", "7c5d5220dd4df4a531418458ab623ef86c41348c", "44540549ee9a65eb8078e271f43ccded0e8e984f", "d63d82dfb9c2afbacac4c9dc1491f743fb083d52", "d634b381d85dae30492dd6291fc4e6e96143f363", "692e9819a7a1f1b818bf3739c72d8e5252cae661", "166e473e120a86a6edcd32a975ffe19b45ffdd42", "3522d8578fbcd7b46d2a439d5d718dfb570beb7b", "042204fde8e5b74aa5048c6213a8af4450d26fe5", "294442004543aeecc5f3c61cc1b73b2feaff2f92", "53d0ad1f9d50b9f1a72cbecacdacdff7fb4e69eb", "7e137d362f9679125726ef4876355a09d788795e", "973d45ae0da5d9612d30900e39118d67d039b31a", "6b8fd06606f12be187f73e8809e56a49864794f9", "652f88555e8bb16ffeffd9d1fa3d0c49e7925dfc", "38e19d4be0d99bbba35558af2c0620cd9b46f12e", "4c51642038c4a3cc04c0f8f0b8267b17aafd4045", "881f6fb23c818ecfc387d2b134e1cd7328fc5995", "d8155325107dbbb1f8ef44f75553595fe4c8ec8c", "101eae5edb76fefc40b039009eb35bbaaae99386", "3abd88bc1a3c334f53f345998b72e9cf8ae87abf"}:
        assert "size >= (std::size_t{2} << 20)" in page_heap
    else:
        assert "size >= (2_MiB)" in page_heap
    assert "EDEN_R457_SPARSE_PAGE_HEAP_SRC" in cmake
physical=read("src/ns2_sparse_guest.cpp")
start=physical.index("    bool CommitLocked(std::size_t offset, std::size_t length)")
end=physical.index("\n    bool Commit(std::size_t offset",start)
transaction=physical[start:end]
assert transaction.index("Common::CommitMemoryRange(")<transaction.index(
    "plan.Publish(*admit)")
assert "RestoreZero(at, zero_physical, part.physical);" in transaction
failed_map = transaction.index("if (!Common::CommitMemoryRange(")
assert transaction.index("if (!MapPhysical(at, PROT_READ, zero_physical))", failed_map) < transaction.index(
    "rollback();", failed_map)
assert "MapPhysical(base + index * kGranule, PROT_READ, zero_physical)" in physical
assert "GuestSignal(int signal, siginfo_t* info, void* context)" in physical
assert "plan.CancelSingleUnstaged(*admit)" in physical
assert "if (state == State::Resident) return lock.waited;" in physical
assert "active_guest_signal.store(this, std::memory_order_release)" in physical
assert "EdenNs2EnsureGuestBackingReadable" in physical
if selected in {"05de9e8e7f75e9a7400a351b18f2b1e83165108e", "ee64fac70671126c9b6ab9aa3b3885a40538cf16", "603e0d5c70b04fa84a19cca8f580ed1bdb230be0", "593bc9ee6ddfcf38e488325ccf318f1a0a109d8e", "6b48e6734e738306dd57ceed8be9b003631eb8cb", "d554e257ae82db66d9542f472dcde067510bfa1f", "93c3dd6c86627e91999f965c45c05cd8e50e17eb", "eb9a454db4d21a3aff2642c72eea3ca01bf2b3bb", "93da3b707ef147385380eb0690e0d93fc8e907ad", "a6240909b823492d9ff20070c09387a732d83007", "0390980a5752808dfba7b8edaa7d113cc4e4e6eb", "273680a5b33bff15c9ca12685cfadb2aa15ff9f1", "84b9975726092a32d1cb2aa714b96e4f5f85d7c4", "84ec89ce112b83603b2095a9f6bb785f8e999ef6", "97fa38381d9ce23b63b3bf3751615dc254ab3634", "b099bd7cbefaa1a35d6626d4fd3161afcefa1b48", "bfdf39014db15f237a16d4a50e6cdfd68bdd87b8", "4626d87be155c0b42904610323098c1205515450", "c32704e63844449b1c18a03deb2cd92939999b90", "fab5ebbfda09ebd3fc414b3127e135c66025ccb8", "acb42e2a2b18fee17673d07e06b2f29709de2fb5", "99df05ff50a7a4a9591c17b08f4ed0f8cb0374a3", "04e252186aa42bacde0899e0c9224035c83a6b0d", "44f5b75bc93bcea146ad6fba3ac294405ae8709b", "70789b12dea4d72ce9e7f054c5b6f552ec488f5d", "9db97fb12db1a390d6b2410f0c18333aa31e37da", "60fa67b98286bd84bd591987c5690ae9b15bda3f", "bf981e9d39d4a908d0d5b6f8407cca814c609bdb", "8026fcca228d0feda62ffd9625e16ee0429d621e", "887bf44af34999e8b6c5b63dc7c01c6c13b82c8f", "1a928783cce2c2692d8fe9fd958400a2de060bbf", "9632ac089f8b2d89a6856a42e8fb55206cdba1fa", "b5c6f089a6aecd321d08a40238f3cd502f505b26", "dc9f5f95b1f784bb358d6480e53de7247d61d777", "a441295022b23834f8531c54d2b0965f84023278", "7c5d5220dd4df4a531418458ab623ef86c41348c", "44540549ee9a65eb8078e271f43ccded0e8e984f", "d63d82dfb9c2afbacac4c9dc1491f743fb083d52", "d634b381d85dae30492dd6291fc4e6e96143f363", "692e9819a7a1f1b818bf3739c72d8e5252cae661", "166e473e120a86a6edcd32a975ffe19b45ffdd42", "3522d8578fbcd7b46d2a439d5d718dfb570beb7b", "042204fde8e5b74aa5048c6213a8af4450d26fe5", "294442004543aeecc5f3c61cc1b73b2feaff2f92", "53d0ad1f9d50b9f1a72cbecacdacdff7fb4e69eb", "7e137d362f9679125726ef4876355a09d788795e", "973d45ae0da5d9612d30900e39118d67d039b31a", "6b8fd06606f12be187f73e8809e56a49864794f9", "652f88555e8bb16ffeffd9d1fa3d0c49e7925dfc", "38e19d4be0d99bbba35558af2c0620cd9b46f12e", "4c51642038c4a3cc04c0f8f0b8267b17aafd4045", "881f6fb23c818ecfc387d2b134e1cd7328fc5995", "d8155325107dbbb1f8ef44f75553595fe4c8ec8c", "101eae5edb76fefc40b039009eb35bbaaae99386", "3abd88bc1a3c334f53f345998b72e9cf8ae87abf"}:
    release=physical.split("    void ReleaseFreed(",1)[1].split(
        "    bool PromoteFault(",1)[0]
    assert "plan.ReleaseResident(index, old_physical)" in release
    assert release.index("MapPhysical(at, PROT_READ, zero_physical)") < release.index(
        "sceKernelReleaseDirectMemory(old_physical, kGranule)") < release.index(
        "plan.ReleaseResident(index, old_physical)")

# Source-level device-alias lifetime proof shared by NS1/NS2. A physical page
# reaches KPageHeap::Free only when its kernel refcount becomes zero, while a
# live device mapping marks the guest range DeviceShared. Heap shrink and
# physical unmap both require attributes to be clear before they can retire
# those pages. Hardware queue/fence completion remains a console qualification.
memory_manager_h=read("vendor/sources/eden/src/core/hle/kernel/k_memory_manager.h")
ref_close=memory_manager_h.rsplit(
    "void Close(KPhysicalAddress address, size_t num_pages) {",1
)[1].split("    private:",1)[0]
assert ref_close.index(
    "const RefCount ref_count = (--m_page_reference_counts[index]);"
) < ref_close.index("if (ref_count == 0)") < ref_close.index("this->Free(")

page_table=read("vendor/encore-active/eden-core/src/core/hle/kernel/k_page_table_base.cpp")
device_map=page_table.split(
    "Result KPageTableBase::LockForMapDeviceAddressSpace",1
)[1].split("Result KPageTableBase::LockForUnmapDeviceAddressSpace",1)[0]
assert "KMemoryAttribute::DeviceShared" in device_map
assert "&KMemoryBlock::ShareToDevice" in device_map

heap_shrink=page_table.split(
    "Result KPageTableBase::SetHeapSize",1
)[1].split("Result KPageTableBase::SetMaxHeapSize",1)[0]
assert "KMemoryAttribute::All, KMemoryAttribute::None" in heap_shrink
assert heap_shrink.index("CheckMemoryState(") < heap_shrink.index(
    "OperationType::Unmap")

physical_unmap=page_table.split(
    "Result KPageTableBase::UnmapPhysicalMemory",1
)[1].split("Result KPageTableBase::MapPhysicalMemoryUnsafe",1)[0]
assert "info.GetAttribute() == KMemoryAttribute::None" in physical_unmap
assert physical_unmap.index(
    "info.GetAttribute() == KMemoryAttribute::None"
) < physical_unmap.index("OperationType::UnmapPhysical")
host=read("src/host_memory.cpp")
assert "const bool supported_guest_layout =" in host
for gib in (4, 6, 8, 10, 12):
    assert f"requested == {gib}ull * GiB" in host, gib
assert "const auto budget = (std::min)(requested, PhysicalBudget);" in host
assert '"PS5 sparse guest VA reservation"' in host
assert host.index("if (supported_guest_layout)") < host.index(
    "AllocateMemoryPages(requested)")
assert "impl->sparse->Clear(offset, length, fill)" in host
assert "return; // sparse owner performed the exact clear" in host
assert "if (state == State::Unmapped) continue;" in physical
assert "std::memset(base + begin, 0, end - begin);" in physical
print("R457_NS1_NS2_KERNEL_PTE_GPU_RESIDENCY_CHAIN_SOURCE_PASS"
      " device_alias_retirement_source=1 native_runtime_host_mock=1"
      " hardware_gpu_fences_unqualified=1")
