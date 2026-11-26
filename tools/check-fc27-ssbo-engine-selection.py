#!/usr/bin/env python3
"""Engine/vendor source-selection proof for FC27 SSBO failed-search pruning."""
from pathlib import Path
import hashlib
import subprocess
import shutil

ROOT=Path(__file__).resolve().parents[1]
V=ROOT/"vendor"
CMAKE=(ROOT/"headless/CMakeLists.txt").read_text()

def blob(path: Path) -> str:
    raw=path.read_bytes()
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+bytes([0])+raw).hexdigest()

selected=subprocess.check_output(["git","-C",str(V),"rev-parse","HEAD"],text=True).strip()
gitlink=subprocess.check_output(["git","rev-parse","HEAD:vendor"],cwd=ROOT,text=True).strip()
expected={"76c5efe8cc6d706e1c2ab0a00ddcce96e2d0adf3","6f4bb38594b273fe7cc4fba960dfe62cdb9f508e","4572e581d011c444fd59428d5c042098f05dcfca","f7ee793f1ee1bb1c2b1a35f68073844163658262","3f019c64c2907ac3e84baa9b6200de8898f30636","f0324324768bdc090a003079bbf121df862bc7f7","0ae51658a5d93e368408cad2484b99083ed7309f","697159fd0c183f8a164d0493929ae3b4bcb391d1","b1bb49abea63b6664e0945df8431e10aac128c2f","89d70eb505594447b3ca98658311002e74dac8ad", "b68126c9cd95eef6c6656ff6d7834c62c092aa46", "0fc157b7ccef428e675ff945bc48eceb08fff607", "42459a7893c51a178ecd0c2f74f3951cc20fa12d", "d1f8696448ed481e36380c3ea8431e3dc722304e", "c5614d3c7ef75958965bac93c9e343eccdbc0fbe", "67926ea4b6960eefebf0427929cf299e8e056013", "50a849a93494f442d47573b8ce8b8797c3cecd26", "2c85d0e8ed192c5eec79423e6be8d883fa0bd7ab", "053acc8ddf30fe65f6376564bbd6efef58f07ddc", "ffa519db0f68fb0d5d2acf791e381c898a34a175", "0fc157b7ccef428e675ff945bc48eceb08fff607", "42459a7893c51a178ecd0c2f74f3951cc20fa12d", "d1f8696448ed481e36380c3ea8431e3dc722304e", "c5614d3c7ef75958965bac93c9e343eccdbc0fbe", "67926ea4b6960eefebf0427929cf299e8e056013", "50a849a93494f442d47573b8ce8b8797c3cecd26", "2c85d0e8ed192c5eec79423e6be8d883fa0bd7ab", "053acc8ddf30fe65f6376564bbd6efef58f07ddc", "ffa519db0f68fb0d5d2acf791e381c898a34a175", "9e38066a508716fd959477eccf32c7fb2fde3356", "e298a9b05732346141b685eb4c9850bfa02d9e58","f7ccfda091fd7429f44159318a07391881a3e7c0","92c480e17fedecc21ab4882b76e8507b5aed3771","7039d7752c5d8b1a53db50be0d8f2f7803867e13","d3fca0aa188052f0efd2bad102950aeaeeb36ab0","dfc39fcc087738955b0373b45fa97facdeb2fc47","b806bc497049819e716ef6de81f2a85312b188ce","e0d4143f55b5d4fee976d241d18ebcf7766ae4cf","1aa641ff566d688fbe34c7ec0ab1e25181e7f3b7","c0d65da6ae50aff83aae83c96bb6acadd34dae9c","b8883667410054db189d00b3a5144088f47d3af9","7eb559a9a2bcf68e91145c241082644c38ff0dfc","3c831706f615566b0eb4c99e9168e6c9236896d2","92d985482a6181c67626794e684f67d9a131a763","fbdd6a44158716d8ba1ae69b85aac30a87af389c","cabc153d337d49871cae36c183d575e834c14383","daff359876ecf35a4f5f4742e483a248c8103d84","463e17ef842b5e230946d47f29409b014a75117f","4bd93a797d922c6234d4a543a36b41462204ce0c","d81f5dd5e08400816b65091645016e97c0dbf3f7","ba3377a0b95db903760c7e7a3c84f60f3c473825","7ccc5721d5525ecacd3d55ea7e59b7f62d0473bb","4934fa18843112cad024ee41f4e28e1dc99d581f","21d480ac95486d545d50371608b038cf98efb24e","20d2457b83e65aa6623ea5d1fed5d2e9d423aeaf","decf9b4a91ca1fc218c33d6829f3e86616b87787","e81e40171ec9e07fd26c1ea8022116ad97e602af","c07a9974d3d91de5fd4780c7849428251a90ed0c","11dcdc5627348a291d7ca0ed89319ffb2049a68f","17b77950adfd0f091e81359cc73cd192e8c18b41","b381340215a07c72075b7114a55bb594cb2bfb86","fa460ecaa86fd6528514ad2283d8fc289639111f","c57862fdec84ef6049fbb24b0fffeba78a81ea9b","6129078b641b12b5ed8028f69b6847a64adf416f","72b27310a39dae20b5a569132133c2486f6d6ce2","69f7e3453d676f7538f62ebe70b9197cd1614f2b","df8a5e2f59895d315b7c3b69f87bb78502afa8c7","bd8424573816c1d80fe4400d0aa4731435bc07d9","0b6214c56f51d59e5a0aa253ea5801b49e2bf475","fde8c9de9e3df8167afe8baa1b40493de7c78758"}
expected.add("42b34a5dc46b594cb029362e8f130900adf4424e")
expected.add("77b736148129ffa72c9f6c081695b7c7515c3ed9")
expected.add("4354add020afac574198f63d87167f3022bff9c6")
# This integration changes only the reviewed GPU readback method and its
# source receipts; the active SSBO shader/CMake blobs are checked below.
expected.add("17253dc91e9fe1eb2d9980f261f59d227bfcd1a1")
# The merged vendor commit has the exact reviewed 17253dc9 source tree.
expected.add("ac880cd408116e6eb53ba2400abc52970b81f539")
expected.add("95343060f948601930f2e62b919da0789f0830bb")
expected.add("12ab9a8411f5c9df1b5cc73f01c923ad9479c8af")
expected.add("224b05e6f8b1a266b0d55d1ded5332f7a2eaed7c")
# Exact two-file SampleMask successor: the native FC27 SSBO owners are unchanged.
expected.add("150a3a79ca103061f73a9a50ca8f463a3b4712f3")
# Source-only MaxwellDMA successor; current SSBO shader graph is unchanged.
expected.add("fcd62408fdbc33af01a4caebc8fd44c8500b628f")
# Release FC27 NVDRV process-lifetime correction; no SSBO owner changed.
expected.add("b6b9e98e0dd16c4702f21f2e0b5e322126abeecb")
# PS5 FC27 cached-pipeline warm admission expands without touching SSBO source.
expected.add("dbef23055897b1649f83c20cf7a0516e64f3d5cd")
# Exact NS2 SelfController and NUP/IPC successors preserve FC27 shader/SSBO owners.
expected.add("dc526f06d277dfa0a4afa48b4cf8b3153ebe7267")
expected.add("87964d15e91b6b6523c88682e5ca017f6e1a808b")
expected.add("ae6f59a9865a3f4f178c4d836a3e04c93cceb69a")
expected.add("f5c80c900b58b57808f609b5ffdc0e6ab9de7bd0")
expected.add("d22b7066410c627230f9bfa8b3b5be8baff4fcdf")
expected.add("f4f5d53596879960b19a3701bbd2272ef1f3c634")
# Subsequent NX2-only supervisor, VI2, content and account source deltas do
# not change FC27's SSBO shader graph. The immutable blobs are verified below.
expected.add("2873d15edcc36e52fe1d7163684b9f78976200bf")
expected.add("ee20b5a00e4fd96c02b5d12d6f4eaabee8623bf3")
# New vendor revision only changes GPU-session HLE table and NIFM comma:
# the SSBO shader owner blobs and CMake source graph are sealed below.
expected.add("716e069f212b89b6fd13af56b0677343cf41ba07")
# Test-only vendor successor: active runtime blobs remain byte-identical.
expected.add("6c15ec8d1143eb1ae3092a2b984f0bc5bfcc364b")
# GPU-time fail-closed successor leaves FC27 shader owners byte-identical.
expected.add("93c3dd6c86627e91999f965c45c05cd8e50e17eb")
expected.add("eb9a454db4d21a3aff2642c72eea3ca01bf2b3bb")
expected.add("93da3b707ef147385380eb0690e0d93fc8e907ad")
expected.add("a6240909b823492d9ff20070c09387a732d83007")
# FC27+NS2 shutdown/trace successor: the complete active SSBO and CMake blobs
# remain byte-sealed below; this pinned vendor was verified against a62409.
expected.add("0390980a5752808dfba7b8edaa7d113cc4e4e6eb")
# Lichii/Eglantine AM window one-shot and LM NS2/NS1 split change no sealed SSBO source.
# Verify shader/BFS owner blobs and CMake selections below before allowing this pin.
expected.add("273680a5b33bff15c9ca12685cfadb2aa15ff9f1")
expected.add("84b9975726092a32d1cb2aa714b96e4f5f85d7c4")
expected.add("84ec89ce112b83603b2095a9f6bb785f8e999ef6")
expected.add("97fa38381d9ce23b63b3bf3751615dc254ab3634")
expected.add("b099bd7cbefaa1a35d6626d4fd3161afcefa1b48")
expected.add("bfdf39014db15f237a16d4a50e6cdfd68bdd87b8")
expected.add("4626d87be155c0b42904610323098c1205515450")
expected.add("c32704e63844449b1c18a03deb2cd92939999b90")
expected.add("fab5ebbfda09ebd3fc414b3127e135c66025ccb8")
expected.add("acb42e2a2b18fee17673d07e06b2f29709de2fb5")
expected.add("99df05ff50a7a4a9591c17b08f4ed0f8cb0374a3")
expected.add("04e252186aa42bacde0899e0c9224035c83a6b0d")
expected.add("44f5b75bc93bcea146ad6fba3ac294405ae8709b")
expected.add("70789b12dea4d72ce9e7f054c5b6f552ec488f5d")
expected.add("9db97fb12db1a390d6b2410f0c18333aa31e37da")
if selected in {"ac880cd408116e6eb53ba2400abc52970b81f539", "95343060f948601930f2e62b919da0789f0830bb", "12ab9a8411f5c9df1b5cc73f01c923ad9479c8af", "224b05e6f8b1a266b0d55d1ded5332f7a2eaed7c", "150a3a79ca103061f73a9a50ca8f463a3b4712f3", "fcd62408fdbc33af01a4caebc8fd44c8500b628f", "b6b9e98e0dd16c4702f21f2e0b5e322126abeecb", "dbef23055897b1649f83c20cf7a0516e64f3d5cd", "dc526f06d277dfa0a4afa48b4cf8b3153ebe7267", "87964d15e91b6b6523c88682e5ca017f6e1a808b", "ae6f59a9865a3f4f178c4d836a3e04c93cceb69a", "f5c80c900b58b57808f609b5ffdc0e6ab9de7bd0", "d22b7066410c627230f9bfa8b3b5be8baff4fcdf", "f4f5d53596879960b19a3701bbd2272ef1f3c634"}:
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
            "b6b9e98e0dd16c4702f21f2e0b5e322126abeecb": "067c72d30a71a79faefd1ad14876e2a46f02755c",
            "dbef23055897b1649f83c20cf7a0516e64f3d5cd": "9e28e5b83cf9c0f4086a33d6838904353a8fd541",
            "dc526f06d277dfa0a4afa48b4cf8b3153ebe7267": "e21b2c70c00c50fc7d682150cb62e87fe856306c",
            "87964d15e91b6b6523c88682e5ca017f6e1a808b": "c1cbb8a3ca0b7231e260fdb5e9f6a1c7964097ab",
            "ae6f59a9865a3f4f178c4d836a3e04c93cceb69a": "e125210acec0eaef51c6c038d200cc9c12981ace",
            "f5c80c900b58b57808f609b5ffdc0e6ab9de7bd0": "68acadcd14d23135fd02df0a0e508c668917168c",
            "d22b7066410c627230f9bfa8b3b5be8baff4fcdf": "805d74f7ccf0ddf060782615d2bd94bb8d26b412",
            "f4f5d53596879960b19a3701bbd2272ef1f3c634": "e1e3fa4878d6203a51c7aa6ec93e09f81a175cdf",
    }[selected], ("Vendor reviewed source tree drift", selected, reviewed_tree)
expected.add("60fa67b98286bd84bd591987c5690ae9b15bda3f")
expected.add("bf981e9d39d4a908d0d5b6f8407cca814c609bdb")
expected.add("8026fcca228d0feda62ffd9625e16ee0429d621e")
expected.add("887bf44af34999e8b6c5b63dc7c01c6c13b82c8f")
expected.add("1a928783cce2c2692d8fe9fd958400a2de060bbf")
expected.add("9632ac089f8b2d89a6856a42e8fb55206cdba1fa")
if selected in {"b5c6f089a6aecd321d08a40238f3cd502f505b26", "dc9f5f95b1f784bb358d6480e53de7247d61d777", "a441295022b23834f8531c54d2b0965f84023278", "7c5d5220dd4df4a531418458ab623ef86c41348c", "44540549ee9a65eb8078e271f43ccded0e8e984f", "d63d82dfb9c2afbacac4c9dc1491f743fb083d52", "d634b381d85dae30492dd6291fc4e6e96143f363", "692e9819a7a1f1b818bf3739c72d8e5252cae661", "166e473e120a86a6edcd32a975ffe19b45ffdd42", "3522d8578fbcd7b46d2a439d5d718dfb570beb7b"}:
    # AM lifetime successor changes no shader or sparse kernel owner.
    assert subprocess.check_output(["git", "-C", str(V), "rev-parse", "HEAD^{tree}"], text=True).strip() == ("67917388ba3308bacfa3e8da6fff9d83c4efb713" if selected == "3522d8578fbcd7b46d2a439d5d718dfb570beb7b" else "3a996079e9de76e0c3d8bd2e595e6c83dadd6ce0" if selected == "166e473e120a86a6edcd32a975ffe19b45ffdd42" else "6743fed9174ee7e3451afbbad230dca6c2e4203c" if selected == "692e9819a7a1f1b818bf3739c72d8e5252cae661" else "a51ee73257c13fce70cbaf5d3e26c62010abf2e9" if selected == "d634b381d85dae30492dd6291fc4e6e96143f363" else "290d8c51e8ab40dd56651d50483abe42e11fa404" if selected == "d63d82dfb9c2afbacac4c9dc1491f743fb083d52" else "86d6068c438cc36ffd01513fc178d2590fb010cb" if selected == "44540549ee9a65eb8078e271f43ccded0e8e984f" else "9ff41b47bfe30a9cef86a5ab7c584c0094f586bf" if selected == "7c5d5220dd4df4a531418458ab623ef86c41348c" else "d53129478299aded8cb8d7432751b43fa74594b9" if selected == "a441295022b23834f8531c54d2b0965f84023278" else "1660883553006cfca7e80465ad5521b4c2ca33b1" if selected == "dc9f5f95b1f784bb358d6480e53de7247d61d777" else "668fb8effa6963be062d780e3bd145a5233d6b7e")
    expected.add(selected)
if selected in {"1a928783cce2c2692d8fe9fd958400a2de060bbf", "9632ac089f8b2d89a6856a42e8fb55206cdba1fa", "b5c6f089a6aecd321d08a40238f3cd502f505b26", "dc9f5f95b1f784bb358d6480e53de7247d61d777", "a441295022b23834f8531c54d2b0965f84023278", "7c5d5220dd4df4a531418458ab623ef86c41348c", "44540549ee9a65eb8078e271f43ccded0e8e984f", "d63d82dfb9c2afbacac4c9dc1491f743fb083d52", "d634b381d85dae30492dd6291fc4e6e96143f363", "692e9819a7a1f1b818bf3739c72d8e5252cae661", "166e473e120a86a6edcd32a975ffe19b45ffdd42", "3522d8578fbcd7b46d2a439d5d718dfb570beb7b"}:
    assert blob(V/"tests/ns1_r23_18_tir_host.py") == ("9ec2e122bee4c7ef3a0889fbf5e8202ae9516339" if selected in {"d63d82dfb9c2afbacac4c9dc1491f743fb083d52", "d634b381d85dae30492dd6291fc4e6e96143f363", "692e9819a7a1f1b818bf3739c72d8e5252cae661", "166e473e120a86a6edcd32a975ffe19b45ffdd42", "3522d8578fbcd7b46d2a439d5d718dfb570beb7b"} else "005280fde5bbd862d64a4def0d17d90a35bbe5e9"), (
        "Vendor host-only TextureCache TIR witness drift")
if selected == "042204fde8e5b74aa5048c6213a8af4450d26fe5":
    # Direct successor of 3522d8578fbcd7b46d2a439d5d718dfb570beb7b; only GSV/Worker NS2 files changed.
    assert subprocess.check_output(["git", "-C", str(V), "rev-parse", "HEAD^{tree}"], text=True).strip() == "08ff1d3ef45b03cbe3396079bcb91fa5dce4f160"
    expected.add(selected)
if selected in {"294442004543aeecc5f3c61cc1b73b2feaff2f92", "53d0ad1f9d50b9f1a72cbecacdacdff7fb4e69eb", "7e137d362f9679125726ef4876355a09d788795e"}:
    # Exact NS2-only successor. FC27 source hashes below are unchanged.
    assert subprocess.check_output(["git", "-C", str(V), "rev-parse", "HEAD^{tree}"], text=True).strip() == ("6861e052a9824450c7eeaa91b53334c153ca9865" if selected == "7e137d362f9679125726ef4876355a09d788795e" else "a21aa2b63cfb9cae4dd9ba386982c3bd57a7ef1f" if selected == "53d0ad1f9d50b9f1a72cbecacdacdff7fb4e69eb" else "50ba35725b57b59cae76a67c7c1d4ba6ad894e2f")
    expected.add(selected)
if selected in {"973d45ae0da5d9612d30900e39118d67d039b31a", "6b8fd06606f12be187f73e8809e56a49864794f9", "652f88555e8bb16ffeffd9d1fa3d0c49e7925dfc", "38e19d4be0d99bbba35558af2c0620cd9b46f12e", "4c51642038c4a3cc04c0f8f0b8267b17aafd4045", "881f6fb23c818ecfc387d2b134e1cd7328fc5995", "d8155325107dbbb1f8ef44f75553595fe4c8ec8c", "101eae5edb76fefc40b039009eb35bbaaae99386", "3abd88bc1a3c334f53f345998b72e9cf8ae87abf"}:
    assert subprocess.check_output(["git", "-C", str(V), "rev-parse", "HEAD^{tree}"], text=True).strip() == (
        "b82ce9bb3b543bf85d535bdfdfb6d725fe88be56" if selected == "3abd88bc1a3c334f53f345998b72e9cf8ae87abf" else "8e42496a1f01a94cc6b17f57eee6ebdff2698ff6" if selected == "101eae5edb76fefc40b039009eb35bbaaae99386" else "a6451d095d44e8b9968635320d3bba34d5722fa5" if selected == "d8155325107dbbb1f8ef44f75553595fe4c8ec8c" else "ba3ad593fb37ac3dc62f2c8b6064328c55cabb3b" if selected == "881f6fb23c818ecfc387d2b134e1cd7328fc5995" else "77add4864dbadc2c2246c339b215c3d79b40a549" if selected == "4c51642038c4a3cc04c0f8f0b8267b17aafd4045" else
        "a27660a134453d2895e23d5c56ac64e6f12d9960" if selected == "38e19d4be0d99bbba35558af2c0620cd9b46f12e" else
        "57a6ef072ad018954d493cb9064b5c722a5af827" if selected == "652f88555e8bb16ffeffd9d1fa3d0c49e7925dfc" else
        "6ecf485d48b3c29c5e058de99a09c5c495cd537d" if selected == "6b8fd06606f12be187f73e8809e56a49864794f9" else
        "1d991da378f711312faf34125f1d4cfe1378bcaa")
    expected.add(selected)
if selected == "06705357e48b33d837b1f97dbb1c3979cb3d7c31":
    # NS2 GPU lifecycle/VA successors only; admit the exact reviewed tree,
    # then retain all immutable FC27 shader/CMake blob checks below.
    assert subprocess.check_output(
        ["git", "-C", str(V), "rev-parse", "HEAD^{tree}"], text=True
    ).strip() == "8bd2b8d1378cefffaf0f4e397289ba62ef009112"
    expected.add(selected)
if selected == "cd5ce4dabef1d32e0441d22dccdee358ebf23287":
    # Exact NS2-only queued-GPFIFO/H:17 successor plus source-guard alignment. Authenticate the complete
    # vendor tree; the immutable FC27 shader/CMake hashes below remain the
    # actual proof that this successor does not alter FC27 source ownership.
    assert subprocess.check_output(
        ["git", "-C", str(V), "rev-parse", "HEAD^{tree}"], text=True
    ).strip() == "2a8d99c8a9912041a286c747c7dcebf5a8cc6f89"
    expected.add(selected)
if selected == "a8f327c972bd2f84f6e6f9432c96c4a948963073":
    assert subprocess.check_output(["git", "-C", str(V), "rev-parse", "HEAD^{tree}"], text=True).strip() == "747569d1bafefc23fb235e1929bda0f5c0d48de3"
    assert blob(V/"encore-active/eden-vulkan/vk_pipeline_cache_cost.cpp") == ("7db0462ad24aa4c6356ce4efa0086b356f171be6" if selected in {"628d01bdc4368e9ad661d749515f788ef7c03802", "191dd458c68de13f0f71659e3b4a9598af7de561", "b743e9c7ec9832832711fc0ea34e03a25c973557", "4c8f72f8ba3db320af55cea0f53cac16366c3ea0", "6affc4ad869a3eaab9d1bed1e65de8872d93363b", "b92d4183cec69e65216162cf61e451eff643caa0", "84d3b0398ae7db1618899815bc1f98894453fbf6", "1949a57c930d3ebd32bdd93093763ae22681a4a4", "2ecccebce83cd169f1820d9c4674698f6353fa48", "d40e212b2c8124225ff8d6adc06f459955e42a6a", "b3458252ec923444b3add94ff50a4a76e2bc4570", "f3322eb09b8b4bbf1c589d1e96ff454cd5fb2c5d", "bc94e99cbedd19b3f6bc75aff02a9b5b914d5189", "f337bb8c0484fef5b9a2d763b9775566ff797eef", "da339b1393d1386bc6af667d243e97860a40d096", "5ddd9d778b2fab5e7e8a29cac44aa0c80e4df015", "94d352bdc9b2ee8e6ea0881d85f4673585b98bf4", "be9e46213070e5cb57a7dbd8a184ffb480106b4f", "096761112103fac069b56a22c77f07492001e26e", "fa76dceebca2fae6acbf2b2a6b9840061e07ecc6", "df6a83b4ad06a689674e111a793995663a8d4eb3", "db9c5e6725264412218c3cabdb1d284e6dcb8a5f", "d254110d5551a246530a3665995e876e752e7565", "2af2f2c4bfccfcb53a5a1099844e36fa5dd9756a", "22a5ccda624de9c42f5c772f39844242621c9289", "dc47b157c607c739b43f67aecbf36448507b9557", "f4a90f02ad5383998d08b45cca534d1b73b166c1", "47f91da1f0179652eecbff150e09a4ddb6122157", "82634fc0f2b2c7ffab2dbb50e658b20f911dbd16", "d70e660ad2c48ae0d8a4268d8e051ac0dee8fb23", "6d4e256d2ce11c531f33c3be3d604cb9a884538b", "720bdb0e81c57462338be480cecae13f2e205110", "bde537edf37e1f21e483993ca8582f44ff0f5555", "e3eb7dc19542bdfbd88964a4aeed85e55d22dafd"} else "cdcef0c6ec4cdada8521af43f856e66f98d5b0a9")
    expected.add(selected)
if selected in {"ffa7757e98bf42a5abcd5c0b9e845cfdbc01e75e", "752b92033610b294a36254d5747c317aca51c1d5", "1b5256d72072e05a62fb734bc9ef790fc81c1573", "628d01bdc4368e9ad661d749515f788ef7c03802", "191dd458c68de13f0f71659e3b4a9598af7de561", "b743e9c7ec9832832711fc0ea34e03a25c973557", "4c8f72f8ba3db320af55cea0f53cac16366c3ea0", "6affc4ad869a3eaab9d1bed1e65de8872d93363b", "b92d4183cec69e65216162cf61e451eff643caa0", "84d3b0398ae7db1618899815bc1f98894453fbf6", "1949a57c930d3ebd32bdd93093763ae22681a4a4", "2ecccebce83cd169f1820d9c4674698f6353fa48", "d40e212b2c8124225ff8d6adc06f459955e42a6a", "b3458252ec923444b3add94ff50a4a76e2bc4570", "f3322eb09b8b4bbf1c589d1e96ff454cd5fb2c5d", "bc94e99cbedd19b3f6bc75aff02a9b5b914d5189", "f337bb8c0484fef5b9a2d763b9775566ff797eef", "da339b1393d1386bc6af667d243e97860a40d096", "5ddd9d778b2fab5e7e8a29cac44aa0c80e4df015", "94d352bdc9b2ee8e6ea0881d85f4673585b98bf4", "be9e46213070e5cb57a7dbd8a184ffb480106b4f", "096761112103fac069b56a22c77f07492001e26e", "fa76dceebca2fae6acbf2b2a6b9840061e07ecc6", "df6a83b4ad06a689674e111a793995663a8d4eb3", "db9c5e6725264412218c3cabdb1d284e6dcb8a5f", "d254110d5551a246530a3665995e876e752e7565", "2af2f2c4bfccfcb53a5a1099844e36fa5dd9756a", "22a5ccda624de9c42f5c772f39844242621c9289", "dc47b157c607c739b43f67aecbf36448507b9557", "f4a90f02ad5383998d08b45cca534d1b73b166c1", "47f91da1f0179652eecbff150e09a4ddb6122157", "82634fc0f2b2c7ffab2dbb50e658b20f911dbd16", "d70e660ad2c48ae0d8a4268d8e051ac0dee8fb23", "6d4e256d2ce11c531f33c3be3d604cb9a884538b", "720bdb0e81c57462338be480cecae13f2e205110", "bde537edf37e1f21e483993ca8582f44ff0f5555", "e3eb7dc19542bdfbd88964a4aeed85e55d22dafd"}:
    assert subprocess.check_output(["git", "-C", str(V), "rev-parse", "HEAD^{tree}"], text=True).strip() == ("c245ee471877e0b0cd77e046bb23b2cf032cf3cd" if selected == "e3eb7dc19542bdfbd88964a4aeed85e55d22dafd" else "d7ac5724fd94d7ee2372e5e2b6e3e3fadbd5d9b7" if selected == "bde537edf37e1f21e483993ca8582f44ff0f5555" else "0eadff0bbeec17fdb1e03ae91834e8ecd0bb7248" if selected == "720bdb0e81c57462338be480cecae13f2e205110" else "20d32728d579b01df5d731a9e86c9442536a1b8b" if selected == "6d4e256d2ce11c531f33c3be3d604cb9a884538b" else "aa9558de1ff14de0d4164bb5171148d5ce1271db" if selected == "d70e660ad2c48ae0d8a4268d8e051ac0dee8fb23" else "8baf67946db717dd0874fd9b4d36a98bdfa0d40a" if selected == "82634fc0f2b2c7ffab2dbb50e658b20f911dbd16" else "16a2e58aa284c80c02c9a2b93ce11eae0252a6f1" if selected == "47f91da1f0179652eecbff150e09a4ddb6122157" else "8fc8d52290178f06a9f9494ecfd9a1444a3d5159" if selected == "f4a90f02ad5383998d08b45cca534d1b73b166c1" else "5bd3d6f913c3ad0de482a63497d24db22e243a10" if selected == "dc47b157c607c739b43f67aecbf36448507b9557" else "7a56b74c79bd0108bcc983d1cc4ed1f0c412a558" if selected == "22a5ccda624de9c42f5c772f39844242621c9289" else "9ad0d1f255dce3e4666e2e5f1f2fdf61c793e89f" if selected == "2af2f2c4bfccfcb53a5a1099844e36fa5dd9756a" else "740dd8bbf66056a85eaf1b28c23bc961580b32b5" if selected == "d254110d5551a246530a3665995e876e752e7565" else "9bf33aa551c37b0c88866181f5a6446a524c691b" if selected == "db9c5e6725264412218c3cabdb1d284e6dcb8a5f" else "0ae03c3481903ac2b1b5faacc8d1daa834a0574e" if selected == "df6a83b4ad06a689674e111a793995663a8d4eb3" else "f188b7c9f89ab2e11ab049c7fff9fb6e6d4c743a" if selected == "fa76dceebca2fae6acbf2b2a6b9840061e07ecc6" else "3133bf53a7d2080e946bfa105957bd1dde1984c3" if selected == "096761112103fac069b56a22c77f07492001e26e" else "d7a1ccb7d3e7379d166932b32d0624a4536b790d" if selected == "be9e46213070e5cb57a7dbd8a184ffb480106b4f" else "ba5a2aca13ad0f9f24f42d79b4ce92b18d8fd900" if selected == "94d352bdc9b2ee8e6ea0881d85f4673585b98bf4" else "79a4614d3390ac925cb870ea36fbaf2c4bed1f58" if selected == "5ddd9d778b2fab5e7e8a29cac44aa0c80e4df015" else "2b56aa5ceb7aeafb0d1e729c47cb10338bf799f4" if selected == "da339b1393d1386bc6af667d243e97860a40d096" else "453b5b1de56f24c6c910bf54949d7970842477cf" if selected == "f337bb8c0484fef5b9a2d763b9775566ff797eef" else "48aed811a8c087443c182aec68ce848fb4b9c897" if selected == "bc94e99cbedd19b3f6bc75aff02a9b5b914d5189" else "9b37d2fa9f4a01b222539218182be12e738ff2fa" if selected == "f3322eb09b8b4bbf1c589d1e96ff454cd5fb2c5d" else "daad0337726ebd845b59ff9c86ce11de8173c599" if selected == "b3458252ec923444b3add94ff50a4a76e2bc4570" else "a1bc0bb572bdec28995c80be66bd6a6d796fb10f" if selected == "d40e212b2c8124225ff8d6adc06f459955e42a6a" else "72633c97a3ad4f2659ec7f45e9e504ab039f549b" if selected == "2ecccebce83cd169f1820d9c4674698f6353fa48" else "0d60046b2708b582c9344108c35e5ca18bc6de40" if selected == "1949a57c930d3ebd32bdd93093763ae22681a4a4" else "2c722077f49013766b80b561ecf446562450faa5" if selected == "84d3b0398ae7db1618899815bc1f98894453fbf6" else "79254f62ba6a12bcdcda9024953ba10e6b84706a" if selected == "b92d4183cec69e65216162cf61e451eff643caa0" else "34b43b1a3d669be0482aca97a28f988516df615c" if selected == "6affc4ad869a3eaab9d1bed1e65de8872d93363b" else "b300d82e0aa31c9ddde01703bdf446579ce4e0c2" if selected in {"4c8f72f8ba3db320af55cea0f53cac16366c3ea0", "6affc4ad869a3eaab9d1bed1e65de8872d93363b"} else "c6eea7dfe0603bfccb44da9b82c95ca1429761fe" if selected in {"b743e9c7ec9832832711fc0ea34e03a25c973557", "4c8f72f8ba3db320af55cea0f53cac16366c3ea0"} else "f98956d2a6ce68c6af51bf5e8b53b7516b02bd2e" if selected in {"191dd458c68de13f0f71659e3b4a9598af7de561", "b743e9c7ec9832832711fc0ea34e03a25c973557"} else "48f75fca37a128f9425cc3484d22ab994a1a17a8" if selected in {"628d01bdc4368e9ad661d749515f788ef7c03802", "191dd458c68de13f0f71659e3b4a9598af7de561"} else "c54279c46295cc71d27c74af213dcacff0d08810" if selected == "1b5256d72072e05a62fb734bc9ef790fc81c1573" else "7ab98eb5286021a9e070397ef6673f61934cf5e0" if selected == "752b92033610b294a36254d5747c317aca51c1d5" else "af3fb89c9c6bb96c19bd2e099273019840536267")
    assert blob(V/"encore-active/eden-vulkan/vk_pipeline_cache_cost.cpp") == ("7db0462ad24aa4c6356ce4efa0086b356f171be6" if selected in {"628d01bdc4368e9ad661d749515f788ef7c03802", "191dd458c68de13f0f71659e3b4a9598af7de561", "b743e9c7ec9832832711fc0ea34e03a25c973557", "4c8f72f8ba3db320af55cea0f53cac16366c3ea0", "6affc4ad869a3eaab9d1bed1e65de8872d93363b", "b92d4183cec69e65216162cf61e451eff643caa0", "84d3b0398ae7db1618899815bc1f98894453fbf6", "1949a57c930d3ebd32bdd93093763ae22681a4a4", "2ecccebce83cd169f1820d9c4674698f6353fa48", "d40e212b2c8124225ff8d6adc06f459955e42a6a", "b3458252ec923444b3add94ff50a4a76e2bc4570", "f3322eb09b8b4bbf1c589d1e96ff454cd5fb2c5d", "bc94e99cbedd19b3f6bc75aff02a9b5b914d5189", "f337bb8c0484fef5b9a2d763b9775566ff797eef", "da339b1393d1386bc6af667d243e97860a40d096", "5ddd9d778b2fab5e7e8a29cac44aa0c80e4df015", "94d352bdc9b2ee8e6ea0881d85f4673585b98bf4", "be9e46213070e5cb57a7dbd8a184ffb480106b4f", "096761112103fac069b56a22c77f07492001e26e", "fa76dceebca2fae6acbf2b2a6b9840061e07ecc6", "df6a83b4ad06a689674e111a793995663a8d4eb3", "db9c5e6725264412218c3cabdb1d284e6dcb8a5f", "d254110d5551a246530a3665995e876e752e7565", "2af2f2c4bfccfcb53a5a1099844e36fa5dd9756a", "22a5ccda624de9c42f5c772f39844242621c9289", "dc47b157c607c739b43f67aecbf36448507b9557", "f4a90f02ad5383998d08b45cca534d1b73b166c1", "47f91da1f0179652eecbff150e09a4ddb6122157", "82634fc0f2b2c7ffab2dbb50e658b20f911dbd16", "d70e660ad2c48ae0d8a4268d8e051ac0dee8fb23", "6d4e256d2ce11c531f33c3be3d604cb9a884538b", "720bdb0e81c57462338be480cecae13f2e205110", "bde537edf37e1f21e483993ca8582f44ff0f5555", "e3eb7dc19542bdfbd88964a4aeed85e55d22dafd"} else "cdcef0c6ec4cdada8521af43f856e66f98d5b0a9")
    expected.add(selected)
# The successor changes only SM shutdown lifetime, not the already-byte-pinned SSBO owners.
if selected == "6d9fc80860ea4324b68b433492ad15e34c35a81d":
    assert subprocess.check_output(["git", "-C", str(V), "rev-parse", "HEAD^{tree}"], text=True).strip() == "0ee1ae75649352ed8ddc79271202af9afca258b2"
    assert blob(V/"encore-active/eden-core/src/core/hle/service/sm/sm.cpp") == "2ef914e3f1b24442e1fa0130d5f8175111e7d316"
    expected.add(selected)
# Keep FC27's shader SSBO owner proof intact: authenticate the new
# vendor tree and only its exact Vulkan prewarm successor.
if selected == "ea4d39d5c9bd17074292b8c6f229c53954f8e21e":
    assert subprocess.check_output(["git", "-C", str(V), "rev-parse", "HEAD^{tree}"], text=True).strip() == "e87b8613fed706ae8f09ee50200c737812ade91c"
    assert blob(V/"encore-active/eden-vulkan/vk_pipeline_cache_cost.cpp") == ("61450e8b8c5e76a59660649ed13941eb50e089cb" if selected in {"a82e561698e07f666be4c85973dc4304c0e37030", "806252e96253489c18d11551bf2dcfd668502719"} else "44b0edc24e847d4cbcd47de0ed86241787bda38a")
    assert blob(V/"encore-active/eden-core/src/common/multi_level_page_table.cpp") == "6dd69f4b09aebc0eb7250975d35b34393e9f5516"
    assert blob(V/"encore-active/eden-core/src/video_core/memory_manager.cpp") == ("60446449c26a68b6e2b665148a8045612beb49ef" if selected in {"c3eb352a6c7b296cf8849cec0d98a3d24eba9df0", "a383ab6f52da989c2c5cd756e62165f0763e8e72", "002593960561e38ec74de982cde70e98c6070fd4", "aece4f82a123a7bd1f4046237a82a0faecbee450", "45952eb648e7eb3502b517c06b3032edd3a9035a", "1dac2565be0161e12c1f9f50613013acd5c6df4b", "96c58f5e2edc6e91813e0b2d67b2699ff2785622", "7f1d859a758e4061ecdc6b5d98bc1356a578fa23", "435d508cdff3059001dc65cb9980d009ab8d6796", "ca3fddeadc37eb1df96d00e5e1506299bef83d82", "f104b06916cf231504ff7f4919cd4a491e526668", "105187759ed6b9d4ef1254d999fe4ca7263ad664", "a82e561698e07f666be4c85973dc4304c0e37030", "806252e96253489c18d11551bf2dcfd668502719"} else "c0ba367f8c4452a5c49015ae0fe201ae7a7bdb86")
    expected.add(selected)
# NS2 queue-semaphore + BCAT successor. The complete vendor tree and all
# seven changed objects are sealed here; the FC27 runtime owners remain exact.
if selected in {"12cd57b091e8f6557b2f00ba35fb80fdc5f0dfea", "68cf19e736158b815629ea74a494c5536706dbc2", "b9dae898866d290d5ce1b15838492854680dc6d6", "7130ede3236e2726f3f1b4718b0618240805e9bc", "203736df06915c10d379a67f52c8614c7010d733", "637edccbbf9dc403008192eaf04b14615b0500e2", "0fa6924891050f7cea9b196dff0a760ad154993d", "6fff7df3b34d2aead3e7de86b1c5919b45c7f0f9", "4f9ea0c9e401ef3d025ed1676ac9a20a201455eb", "ad713526cb573d2051a945badfd3bea71b39565b", "a44d4ecb17d9388f7428d7e56d21685054b38d99", "93e3259c7aea3a88a7fd5f80cf706903fac6ccc9", "c3eb352a6c7b296cf8849cec0d98a3d24eba9df0", "a383ab6f52da989c2c5cd756e62165f0763e8e72", "002593960561e38ec74de982cde70e98c6070fd4", "aece4f82a123a7bd1f4046237a82a0faecbee450", "45952eb648e7eb3502b517c06b3032edd3a9035a", "1dac2565be0161e12c1f9f50613013acd5c6df4b", "96c58f5e2edc6e91813e0b2d67b2699ff2785622", "7f1d859a758e4061ecdc6b5d98bc1356a578fa23", "435d508cdff3059001dc65cb9980d009ab8d6796", "ca3fddeadc37eb1df96d00e5e1506299bef83d82", "f104b06916cf231504ff7f4919cd4a491e526668", "105187759ed6b9d4ef1254d999fe4ca7263ad664", "a82e561698e07f666be4c85973dc4304c0e37030", "806252e96253489c18d11551bf2dcfd668502719"}:
    assert subprocess.check_output(
        ["git", "-C", str(V), "rev-parse", "HEAD^{tree}"], text=True
    ).strip() == {"12cd57b091e8f6557b2f00ba35fb80fdc5f0dfea": "62a3bdbad43931dd19494fc24cb57bf5389211b8", "68cf19e736158b815629ea74a494c5536706dbc2": "c1a6951364c337e8012a6cfb46f31f305271231e", "b9dae898866d290d5ce1b15838492854680dc6d6": "cbb2c60a9bcc11478c4a420b2d03106a58fdcb20", "7130ede3236e2726f3f1b4718b0618240805e9bc": "c518f70d7e3b1e15495af73ccbd1bf29efb91e27", "203736df06915c10d379a67f52c8614c7010d733": "35c8a1e26f95dd48bdacb4f4a32f1ead48a9beee", "637edccbbf9dc403008192eaf04b14615b0500e2": "c4b3a2e07d89caea7327a00dd8b107f12e12166e", "0fa6924891050f7cea9b196dff0a760ad154993d": "6663837e6e411e6954e9934caec368ef045873ea", "6fff7df3b34d2aead3e7de86b1c5919b45c7f0f9": "09ed906f5be3ba79636e6f9330fcca5c902825c4", "4f9ea0c9e401ef3d025ed1676ac9a20a201455eb": "722d3f6d8dc6d6d28e76e63162e70eefc34a56f9", "ad713526cb573d2051a945badfd3bea71b39565b": "08a445432d32483ed51eaad72055059142b236f4", "a44d4ecb17d9388f7428d7e56d21685054b38d99": "e3c172c6e1dd8c482392e7d3831359e8e59dfa25", "93e3259c7aea3a88a7fd5f80cf706903fac6ccc9": "540b44b21d777c5af0465f6694c1aa593f4faab5", "c3eb352a6c7b296cf8849cec0d98a3d24eba9df0": "0a3833e1bea8f0823881eeef1247eacdc422b9ed", "a383ab6f52da989c2c5cd756e62165f0763e8e72": "7771963a0d941a488a8e6caf9e594e6721dbc0d3", "002593960561e38ec74de982cde70e98c6070fd4": "3154d29ec8f33c2434c6482e814d03a8b9f4b2cf", "aece4f82a123a7bd1f4046237a82a0faecbee450": "e43ce45702c00d968a5306b898aad47399d1a9f2", "45952eb648e7eb3502b517c06b3032edd3a9035a": "e331d0bf6fdde57991f78d2c02e1c33c01c1736a", "1dac2565be0161e12c1f9f50613013acd5c6df4b": "f70e6e75738feab1511e9e143b101080c7ef3c81", "96c58f5e2edc6e91813e0b2d67b2699ff2785622": "8c825080c95845b892b8069293348e99ef1c800b", "7f1d859a758e4061ecdc6b5d98bc1356a578fa23": "26568a0771490228e4d8158e7121cd2523d7b24b", "435d508cdff3059001dc65cb9980d009ab8d6796": "67ada267d9bf30f7ca89714dc0dc68f037f14223", "ca3fddeadc37eb1df96d00e5e1506299bef83d82": "5b44c10dee1d3be632c5dc00924b2c9b2a1981b2", "f104b06916cf231504ff7f4919cd4a491e526668": "20da9bdb4ec925b40013e884162f46c67a00a5cf", "105187759ed6b9d4ef1254d999fe4ca7263ad664": "ec485e28ce2f79dcb0f039d765a6abaaa0088aad", "a82e561698e07f666be4c85973dc4304c0e37030": "16adf94840cb5bebae483fdca5ecd84774415ce6", "806252e96253489c18d11551bf2dcfd668502719": "dcf463b5cd23ca8fa4c7899c5efd8c8f75f5b869"}[selected]
    if selected in {"7130ede3236e2726f3f1b4718b0618240805e9bc", "203736df06915c10d379a67f52c8614c7010d733", "637edccbbf9dc403008192eaf04b14615b0500e2", "0fa6924891050f7cea9b196dff0a760ad154993d", "6fff7df3b34d2aead3e7de86b1c5919b45c7f0f9", "4f9ea0c9e401ef3d025ed1676ac9a20a201455eb", "ad713526cb573d2051a945badfd3bea71b39565b", "a44d4ecb17d9388f7428d7e56d21685054b38d99", "93e3259c7aea3a88a7fd5f80cf706903fac6ccc9", "c3eb352a6c7b296cf8849cec0d98a3d24eba9df0", "a383ab6f52da989c2c5cd756e62165f0763e8e72", "002593960561e38ec74de982cde70e98c6070fd4", "aece4f82a123a7bd1f4046237a82a0faecbee450", "45952eb648e7eb3502b517c06b3032edd3a9035a", "1dac2565be0161e12c1f9f50613013acd5c6df4b", "96c58f5e2edc6e91813e0b2d67b2699ff2785622", "7f1d859a758e4061ecdc6b5d98bc1356a578fa23", "435d508cdff3059001dc65cb9980d009ab8d6796", "ca3fddeadc37eb1df96d00e5e1506299bef83d82", "f104b06916cf231504ff7f4919cd4a491e526668", "105187759ed6b9d4ef1254d999fe4ca7263ad664", "a82e561698e07f666be4c85973dc4304c0e37030", "806252e96253489c18d11551bf2dcfd668502719"}:
        assert blob(V/"encore-active/eden-core/src/core/hle/kernel/k_page_table_base.cpp") == "a2d6d658ae391e0acd64e68d495c00333e2032ca"
    if selected == "68cf19e736158b815629ea74a494c5536706dbc2":
        assert blob(V/"tests/ns2_gpu_identity_mapping_source.py") == "3a9a1679bc2795cf08863370403b2bc4ad89a553"
    elif selected in {"b9dae898866d290d5ce1b15838492854680dc6d6", "7130ede3236e2726f3f1b4718b0618240805e9bc", "203736df06915c10d379a67f52c8614c7010d733", "637edccbbf9dc403008192eaf04b14615b0500e2", "0fa6924891050f7cea9b196dff0a760ad154993d", "6fff7df3b34d2aead3e7de86b1c5919b45c7f0f9", "4f9ea0c9e401ef3d025ed1676ac9a20a201455eb", "ad713526cb573d2051a945badfd3bea71b39565b", "a44d4ecb17d9388f7428d7e56d21685054b38d99", "93e3259c7aea3a88a7fd5f80cf706903fac6ccc9", "c3eb352a6c7b296cf8849cec0d98a3d24eba9df0", "a383ab6f52da989c2c5cd756e62165f0763e8e72", "002593960561e38ec74de982cde70e98c6070fd4", "aece4f82a123a7bd1f4046237a82a0faecbee450", "45952eb648e7eb3502b517c06b3032edd3a9035a", "1dac2565be0161e12c1f9f50613013acd5c6df4b", "96c58f5e2edc6e91813e0b2d67b2699ff2785622", "7f1d859a758e4061ecdc6b5d98bc1356a578fa23", "435d508cdff3059001dc65cb9980d009ab8d6796", "ca3fddeadc37eb1df96d00e5e1506299bef83d82", "f104b06916cf231504ff7f4919cd4a491e526668", "105187759ed6b9d4ef1254d999fe4ca7263ad664", "a82e561698e07f666be4c85973dc4304c0e37030", "806252e96253489c18d11551bf2dcfd668502719"}:
        assert blob(V/"tests/ns2_gpu_identity_mapping_source.py") == ("e3fd286527e6c3ad7eca371a2d82b9b46837e9e4" if selected in {"435d508cdff3059001dc65cb9980d009ab8d6796", "f104b06916cf231504ff7f4919cd4a491e526668", "105187759ed6b9d4ef1254d999fe4ca7263ad664", "a82e561698e07f666be4c85973dc4304c0e37030", "806252e96253489c18d11551bf2dcfd668502719"} else "68c27deb4544d414cb7339fc4d093cabe8e61a47" if selected == "7f1d859a758e4061ecdc6b5d98bc1356a578fa23" else "cd96c85a45833525a1849b4ae1519e27e5b51913" if selected == "96c58f5e2edc6e91813e0b2d67b2699ff2785622" else "82ffabe603b97922195fcc08a0436077fd2b5eab" if selected == "1dac2565be0161e12c1f9f50613013acd5c6df4b" else "63291835bc54248fca84422d03ad01b91eb1637a" if selected in {"002593960561e38ec74de982cde70e98c6070fd4", "aece4f82a123a7bd1f4046237a82a0faecbee450", "45952eb648e7eb3502b517c06b3032edd3a9035a", "1dac2565be0161e12c1f9f50613013acd5c6df4b", "96c58f5e2edc6e91813e0b2d67b2699ff2785622", "7f1d859a758e4061ecdc6b5d98bc1356a578fa23", "435d508cdff3059001dc65cb9980d009ab8d6796", "ca3fddeadc37eb1df96d00e5e1506299bef83d82", "f104b06916cf231504ff7f4919cd4a491e526668", "105187759ed6b9d4ef1254d999fe4ca7263ad664", "a82e561698e07f666be4c85973dc4304c0e37030", "806252e96253489c18d11551bf2dcfd668502719"} else "e7c379db1f5d938e5c51a497451f20db142d5394" if selected == "a383ab6f52da989c2c5cd756e62165f0763e8e72" else "4818d6bf9c03e1e64e88af9fa0a91f2f94dd4c39" if selected in {"93e3259c7aea3a88a7fd5f80cf706903fac6ccc9", "c3eb352a6c7b296cf8849cec0d98a3d24eba9df0"} else "3fa08a66de50756376be6905fee407e122868db3" if selected == "a44d4ecb17d9388f7428d7e56d21685054b38d99" else "9755354e5a49f50f75f1f04894686f7838f80ea8")
        if selected in {"93e3259c7aea3a88a7fd5f80cf706903fac6ccc9", "c3eb352a6c7b296cf8849cec0d98a3d24eba9df0", "a383ab6f52da989c2c5cd756e62165f0763e8e72", "002593960561e38ec74de982cde70e98c6070fd4", "aece4f82a123a7bd1f4046237a82a0faecbee450", "45952eb648e7eb3502b517c06b3032edd3a9035a", "1dac2565be0161e12c1f9f50613013acd5c6df4b", "96c58f5e2edc6e91813e0b2d67b2699ff2785622", "7f1d859a758e4061ecdc6b5d98bc1356a578fa23", "435d508cdff3059001dc65cb9980d009ab8d6796", "ca3fddeadc37eb1df96d00e5e1506299bef83d82", "f104b06916cf231504ff7f4919cd4a491e526668", "105187759ed6b9d4ef1254d999fe4ca7263ad664", "a82e561698e07f666be4c85973dc4304c0e37030", "806252e96253489c18d11551bf2dcfd668502719"}:
            assert blob(V/"encore-active/eden-core/src/video_core/gpu_gl_native.cpp") == ("9347e606050ac450a1f98e3f5f462ccc982dc808" if selected in {"c3eb352a6c7b296cf8849cec0d98a3d24eba9df0", "a383ab6f52da989c2c5cd756e62165f0763e8e72", "002593960561e38ec74de982cde70e98c6070fd4", "aece4f82a123a7bd1f4046237a82a0faecbee450", "45952eb648e7eb3502b517c06b3032edd3a9035a", "1dac2565be0161e12c1f9f50613013acd5c6df4b", "96c58f5e2edc6e91813e0b2d67b2699ff2785622", "7f1d859a758e4061ecdc6b5d98bc1356a578fa23", "435d508cdff3059001dc65cb9980d009ab8d6796", "ca3fddeadc37eb1df96d00e5e1506299bef83d82", "f104b06916cf231504ff7f4919cd4a491e526668", "105187759ed6b9d4ef1254d999fe4ca7263ad664", "a82e561698e07f666be4c85973dc4304c0e37030", "806252e96253489c18d11551bf2dcfd668502719"} else "7720e5a347817e67c0a964d3a80644b01b99d733")
        assert blob(V/"encore-active/ns2-runtime/hle/core/hle/service/am/service/gpu_memory_registration.h") == "6e1d185f086969caef3dded1a4b383c34a4d8657"
    for relative, digest in {
        "encore-active/eden-core/overrides/bcat/core/hle/service/bcat/backend/backend.h":
            "8c93a3d6aef8a45f85cb9c2344e3427daff4d131",
        "encore-active/eden-core/overrides/bcat/core/hle/service/bcat/service_creator.h":
            "de582d12ef1025735a741817ac4e365f59789809",
        "encore-active/eden-core/src/core/hle/service/bcat/delivery_cache_storage_service.cpp":
            "9f98f2da3f865da69399467133436e64e4e4d67b",
        "encore-active/eden-core/src/core/hle/service/bcat/service_creator.cpp":
            "1635bc091413a2f118b166216f91410b6338686d",
        "encore-active/ns2-runtime/gpu_dispatch/video_core/engines/puller.cpp":
            "576a9d697da398aa6f42901b1764aa7574155411",
        "encore-active/ns2-runtime/gpu_session/core/hle/service/am/service/gpu_worker.cpp":
            ("770290b8bbc610eb5fc5724b17211ba39dc9caa5" if selected in {"435d508cdff3059001dc65cb9980d009ab8d6796", "f104b06916cf231504ff7f4919cd4a491e526668", "105187759ed6b9d4ef1254d999fe4ca7263ad664", "a82e561698e07f666be4c85973dc4304c0e37030", "806252e96253489c18d11551bf2dcfd668502719"} else "065a9d1fbc2a5a2a397f8a0c448374f304c3fc64" if selected == "7f1d859a758e4061ecdc6b5d98bc1356a578fa23" else "0cb6fa9e2fca1252a74556b217cbbd08f8b86fa1" if selected == "96c58f5e2edc6e91813e0b2d67b2699ff2785622" else "51b3917310e5b29de1948695042596220fd23ee3" if selected == "1dac2565be0161e12c1f9f50613013acd5c6df4b" else "ebcb3c4de5e1406f98c1b3959aba90e1a4c3b813" if selected in {"a383ab6f52da989c2c5cd756e62165f0763e8e72", "002593960561e38ec74de982cde70e98c6070fd4", "aece4f82a123a7bd1f4046237a82a0faecbee450", "45952eb648e7eb3502b517c06b3032edd3a9035a", "1dac2565be0161e12c1f9f50613013acd5c6df4b", "96c58f5e2edc6e91813e0b2d67b2699ff2785622", "7f1d859a758e4061ecdc6b5d98bc1356a578fa23", "435d508cdff3059001dc65cb9980d009ab8d6796", "ca3fddeadc37eb1df96d00e5e1506299bef83d82", "f104b06916cf231504ff7f4919cd4a491e526668", "105187759ed6b9d4ef1254d999fe4ca7263ad664", "a82e561698e07f666be4c85973dc4304c0e37030", "806252e96253489c18d11551bf2dcfd668502719"} else "b1be989fb564a1c9ef269470ca5897af4491c9c2" if selected in {"b9dae898866d290d5ce1b15838492854680dc6d6", "7130ede3236e2726f3f1b4718b0618240805e9bc", "203736df06915c10d379a67f52c8614c7010d733", "637edccbbf9dc403008192eaf04b14615b0500e2", "0fa6924891050f7cea9b196dff0a760ad154993d", "6fff7df3b34d2aead3e7de86b1c5919b45c7f0f9", "4f9ea0c9e401ef3d025ed1676ac9a20a201455eb", "ad713526cb573d2051a945badfd3bea71b39565b", "a44d4ecb17d9388f7428d7e56d21685054b38d99", "93e3259c7aea3a88a7fd5f80cf706903fac6ccc9", "c3eb352a6c7b296cf8849cec0d98a3d24eba9df0", "a383ab6f52da989c2c5cd756e62165f0763e8e72", "002593960561e38ec74de982cde70e98c6070fd4", "aece4f82a123a7bd1f4046237a82a0faecbee450", "45952eb648e7eb3502b517c06b3032edd3a9035a", "1dac2565be0161e12c1f9f50613013acd5c6df4b", "96c58f5e2edc6e91813e0b2d67b2699ff2785622", "7f1d859a758e4061ecdc6b5d98bc1356a578fa23", "435d508cdff3059001dc65cb9980d009ab8d6796", "ca3fddeadc37eb1df96d00e5e1506299bef83d82", "f104b06916cf231504ff7f4919cd4a491e526668", "105187759ed6b9d4ef1254d999fe4ca7263ad664", "a82e561698e07f666be4c85973dc4304c0e37030", "806252e96253489c18d11551bf2dcfd668502719"} else "9c35b43bc4f61d67395897fb63fce57419bc3331"),
        "encore-active/ns2-runtime/hle/core/hle/service/nvdrv/devices/native_gpu_process_registry.h":
            "a22b96c04f6f06aef36c36857dcf124521ca2cb7",
    }.items():
        assert blob(V / relative) == digest, relative
    assert blob(V/"encore-active/eden-vulkan/vk_pipeline_cache_cost.cpp") == ("61450e8b8c5e76a59660649ed13941eb50e089cb" if selected in {"a82e561698e07f666be4c85973dc4304c0e37030", "806252e96253489c18d11551bf2dcfd668502719"} else "44b0edc24e847d4cbcd47de0ed86241787bda38a")
    assert blob(V/"encore-active/eden-core/src/common/multi_level_page_table.cpp") == "87eed0b2319c719d27332c8e24f97a73e496f108"
    assert blob(V/"encore-active/eden-core/src/video_core/memory_manager.cpp") == ("60446449c26a68b6e2b665148a8045612beb49ef" if selected in {"c3eb352a6c7b296cf8849cec0d98a3d24eba9df0", "a383ab6f52da989c2c5cd756e62165f0763e8e72", "002593960561e38ec74de982cde70e98c6070fd4", "aece4f82a123a7bd1f4046237a82a0faecbee450", "45952eb648e7eb3502b517c06b3032edd3a9035a", "1dac2565be0161e12c1f9f50613013acd5c6df4b", "96c58f5e2edc6e91813e0b2d67b2699ff2785622", "7f1d859a758e4061ecdc6b5d98bc1356a578fa23", "435d508cdff3059001dc65cb9980d009ab8d6796", "ca3fddeadc37eb1df96d00e5e1506299bef83d82", "f104b06916cf231504ff7f4919cd4a491e526668", "105187759ed6b9d4ef1254d999fe4ca7263ad664", "a82e561698e07f666be4c85973dc4304c0e37030", "806252e96253489c18d11551bf2dcfd668502719"} else "c0ba367f8c4452a5c49015ae0fe201ae7a7bdb86")
    assert blob(ROOT/"src/memory_pages.cpp") == "e90dd13badd48257c25db6317cc523f97b92e1e6"
    assert blob(V/"tests/fc27_xmad_pointer_fold_host.py") == ("1a87bf825ddd9a18ccd947651fa7848cbb6f4158" if selected in {"a82e561698e07f666be4c85973dc4304c0e37030", "806252e96253489c18d11551bf2dcfd668502719"} else "2456b50bfecf8e25b2f725cff59f823abf3f4e3d")
    assert blob(V/"tests/fc27_dynamic_texture_static_sampler_host.py") == ("80e92cbf003422c1c6af65c0317bde600e7563c0" if selected in {"a82e561698e07f666be4c85973dc4304c0e37030", "806252e96253489c18d11551bf2dcfd668502719"} else "dbf70f23a25cc97d2425f968fb536a92ceaec84e")
    assert blob(V/"tests/ns1_r23_35_attribute_handle.py") == ("8b2089e3ea3ab4bb48e8e359613147bc31892cc5" if selected in {"a82e561698e07f666be4c85973dc4304c0e37030", "806252e96253489c18d11551bf2dcfd668502719"} else "5ee069608e164e0f97a5c38f8c9345823250bbb9")
    expected.add(selected)
# Native GPU sparse table commits now expose a recoverable OOM.
# Verify exact selected tree, shader, GPU table and engine allocator owner.
if selected in {"824a7342a58ad50d399ac0b215155884ced474ea", "3baf191c3b7def3ca158e01cf65dafb1aebaf4ed", "29b91308ba1fc69978cd2cc39222fe7dc59b668c"}:
    expected_tree = "45e1f9d536403dfcb2136ff653bae2e07ba85fd4" if selected == "29b91308ba1fc69978cd2cc39222fe7dc59b668c" else "b7548392480ec7bb16aafdcbb330a60834270d09" if selected == "3baf191c3b7def3ca158e01cf65dafb1aebaf4ed" else "ea890f123433198c30141f9320dd10090d80ecdc"
    assert subprocess.check_output(["git", "-C", str(V), "rev-parse", "HEAD^{tree}"], text=True).strip() == expected_tree
    assert blob(V/"encore-active/eden-vulkan/vk_pipeline_cache_cost.cpp") == ("61450e8b8c5e76a59660649ed13941eb50e089cb" if selected in {"a82e561698e07f666be4c85973dc4304c0e37030", "806252e96253489c18d11551bf2dcfd668502719"} else "44b0edc24e847d4cbcd47de0ed86241787bda38a")
    assert blob(V/"encore-active/eden-core/src/common/multi_level_page_table.cpp") == "87eed0b2319c719d27332c8e24f97a73e496f108"
    assert blob(ROOT/"src/memory_pages.cpp") == "e90dd13badd48257c25db6317cc523f97b92e1e6"
    if selected in {"3baf191c3b7def3ca158e01cf65dafb1aebaf4ed", "29b91308ba1fc69978cd2cc39222fe7dc59b668c"}:
        assert blob(V/"tests/fc27_xmad_pointer_fold_host.py") == "2456b50bfecf8e25b2f725cff59f823abf3f4e3d"
    if selected == "29b91308ba1fc69978cd2cc39222fe7dc59b668c":
        assert blob(V/"tests/fc27_dynamic_texture_static_sampler_host.py") == "dbf70f23a25cc97d2425f968fb536a92ceaec84e"
        assert blob(V/"tests/ns1_r23_35_attribute_handle.py") == "5ee069608e164e0f97a5c38f8c9345823250bbb9"
    expected.add(selected)
assert selected==gitlink and selected in expected,(selected,gitlink)

bfs=V/"encore-active/eden-shader/include/shader_recompiler/frontend/ir/breadth_first_search.h"
active=V/"encore-active/eden-shader/src/shader_recompiler/ir_opt/global_memory_to_storage_buffer_pass.cpp"
pinned=V/"sources/eden/src/shader_recompiler/ir_opt/global_memory_to_storage_buffer_pass.cpp"
assert blob(bfs)=="fa5e7572ef99bba3db17154c63f60dddba7a87c6"
assert blob(active)=="602d45b4d2ad872b138d62ce05f379b5e1103602"
assert blob(pinned)=="4ce1ff6c19c4937855d4460a515aec6a8a1e07e0"

# R23 #58 already stages the maintained BFS header. This integration must
# replace only the global-memory pass and preserve the immutable original.
for needle in (
    'set(EDEN_R23_PHI_HEADER',
    'vendor/encore-active/eden-shader/include/shader_recompiler/frontend/ir/breadth_first_search.h',
    'set(EDEN_FC27_SSBO_SOURCE',
    'list(FIND eden_fc27_ssbo_sources "ir_opt/global_memory_to_storage_buffer_pass.cpp"',
    'list(REMOVE_ITEM eden_fc27_ssbo_sources "ir_opt/global_memory_to_storage_buffer_pass.cpp")',
    'list(APPEND eden_fc27_ssbo_sources "${EDEN_FC27_SSBO_SOURCE}")',
):
    assert CMAKE.count(needle)==1,needle
assert CMAKE.count("global_memory_to_storage_buffer_pass.cpp")==3

source=active.read_text()
header=bfs.read_text()
assert "BreadthFirstSearchPruned(value, pred, exhausted)" in source
assert "biased_exhausted" in source and "unbiased_exhausted" in source
assert source.split("bool IsGlobalMemory(",1)[1].split("bool IsGlobalMemoryWrite(",1)[0].count("case IR::Opcode::GlobalAtomicCompareExchange32:")==1
assert "return IR::Opcode::StorageAtomicCompareExchange32;" in source
assert "BreadthFirstSearchPruned(Value value" in header
assert "BreadthFirstSearchPruned" not in pinned.read_text()

# GPU-53: exact maintained SSBO emitter + shared native SPIR-V context.
active_mem=V/"encore-active/eden-shader/src/shader_recompiler/backend/spirv/emit_spirv_memory.cpp"
pinned_mem=V/"sources/eden/src/shader_recompiler/backend/spirv/emit_spirv_memory.cpp"
active_ctx=V/"encore-active/ns2-runtime/ampere/shader_recompiler/backend/spirv/spirv_emit_context.cpp"
pinned_ctx=V/"sources/eden/src/shader_recompiler/backend/spirv/spirv_emit_context.cpp"
assert blob(active_mem)=="6e6994343df4a1e3930495f8fd575c4329bfa8c4"
assert blob(pinned_mem)=="bef4421fedce6d66af1c6ff0c1dcc835e976eb33"
assert blob(active_ctx)=="0e14a042ab272f701da90a5b62fdeeb626032188"
assert blob(pinned_ctx)=="ef1f3f2ee83d3d44a571c03f19399dbe0697dd7e"

for needle in (
    'set(EDEN_NS1_SSBO_ALIGNMENT_SOURCE',
    'list(FIND eden_ns1_ssbo_emit_sources',
    'backend/spirv/emit_spirv_memory.cpp',
    'list(REMOVE_ITEM eden_ns1_ssbo_emit_sources "backend/spirv/emit_spirv_memory.cpp")',
    'list(APPEND eden_ns1_ssbo_emit_sources "${EDEN_NS1_SSBO_ALIGNMENT_SOURCE}")',
):
    assert needle in CMAKE,needle

mem_text=active_mem.read_text()
pinned_mem_text=pinned_mem.read_text()
assert "static bool VectorViewIsExact" in mem_text
assert "return offset.U32() % size == 0;" in mem_text
assert "return ctx.profile.min_ssbo_alignment >= size;" in mem_text
assert mem_text.count("VectorViewIsExact(ctx, offset, sizeof(u32[2]))")==2
assert mem_text.count("VectorViewIsExact(ctx, offset, sizeof(u32[4]))")==2
assert "VectorViewIsExact" not in pinned_mem_text

ctx_text=active_ctx.read_text()
pinned_ctx_text=pinned_ctx.read_text()
ns1_split="!Shader::Ampere::NativeSpirvCbufBoundsActive() && shift > 2"
assert ctx_text.count(ns1_split)==2
assert "profile.min_ssbo_alignment < (1U << shift)" in ctx_text
assert "std::array<Id, 4> words;" in ctx_text
assert "OpCompositeConstruct(type, std::span{words}.first(count))" in ctx_text
assert "callback(ssbo_pointer, ssbo_id, ssbo_index);" in ctx_text
assert ns1_split not in pinned_ctx_text

# Decision table used by the actual helper.
def vector_exact(aliasing, immediate, offset, alignment, size):
    if not aliasing:
        return False
    if immediate:
        return offset % size == 0
    return alignment >= size
for size in (8,16):
    assert vector_exact(True,True,0,4,size)
    assert vector_exact(True,True,size,4,size)
    assert not vector_exact(True,True,4,16,size) if size==8 else True
    assert not vector_exact(True,True,4,16,size)
    assert not vector_exact(False,True,0,16,size)
    assert not vector_exact(True,False,0,4,size)
assert vector_exact(True,False,0,8,8)
assert not vector_exact(True,False,0,8,16)
assert vector_exact(True,False,0,16,16)

# Compile the two real maintained translation units against the selected headers.
compiler=shutil.which("clang++-18") or shutil.which("clang++")
assert compiler,"Clang required for GPU-53 syntax proof"
cpm=V/"sources/eden-cpm"
includes=[
    V/"encore-active/ns2-runtime/ampere",
    V/"encore-active/ns2-runtime/gpu_dispatch",
    V/"encore-active/ns2-runtime/hle",
    V/"encore-active/eden-shader/src",
    V/"sources/eden/src",
    V/"sources/eden/src/dynarmic/src",
    cpm/"fmt/12.1.0/include",
    cpm/"sirit/v1.0.5/include",
    cpm/"spirv-headers/vulkan-sdk-1.4.341.0/include",
    cpm/"vulkanheaders/v1.4.345/include",
]
boost=cpm/"boost/boost-1.90.0/libs"
assert boost.is_dir()
includes.extend(sorted(boost.glob("*/include")))
cmd=[compiler,"-std=c++20","-fsyntax-only","-Wno-unused-parameter",
     "-DPS5_NATIVE=1","-DFMT_HEADER_ONLY","-DCANNOT_EXPLICITLY_INSTANTIATE",
     *["-I"+str(inc) for inc in includes]]
for source_file in (active_mem,active_ctx):
    proc=subprocess.run(cmd+[str(source_file)],capture_output=True,text=True,timeout=120)
    assert proc.returncode==0,(source_file,proc.stderr[-6000:])
print("NS1_GPU53_SSBO_ALIGNMENT_PASS direct=64+128 global=maxwell_only pinned_immutable=1 syntax=2")

subprocess.run(["python3","-B",str(V/"tests/fc27_ssbo_search_pruning_host.py")],
               check=True,timeout=180)
subprocess.run(["python3","-B",str(V/"tests/ps5_ir_bfs_adaptive_host.py")],
               check=True,timeout=180)
print("FC27_SSBO_ENGINE_VENDOR_PAIR_PASS gitlink=exact source_pass=1 bfs_header=1 pinned_immutable=1 ps5_gameplay=unverified")
