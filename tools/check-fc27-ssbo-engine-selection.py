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
# NS1 secondary audit: GPIO/IPC, NCM placeholder cache and FSP fail-closed
# only. The GPU-53 blobs below remain checked byte-for-byte.
expected.add("fe5a389ac04fa3c26c1756fc18e73a962e196da4")
# NS1 FSP source remains reviewed; only its existing backport manifest digest is repaired.
expected.add("e329e52f7de79302bfcc1b658431777501d5edd9")
# NS1 secondary CAPS tables and NCM cacheless rights-ID invalidation; GPU-53 owners unchanged.
expected.add("ff0822695ec03ac7d9d2c75b4703adf12eec544f")
# NS1 NCM content-storage helpers; GPU-53 owners remain unchanged.
expected.add("c3dc80c83d468e04c794b3d7d36bc1316b342bd4")
# NCM capacity/lifecycle follow-up; GPU source owners unchanged.
expected.add("60bd03e6e5ad083ee050887028fa33d514a3050e")
# NCM read/revert handlers; GPU source owners unchanged.
expected.add("488475c8c3867af07892a7f53cc6e15a54d09542")
# ContentMetaDatabase CNMT lookups; GPU owners unchanged.
expected.add("8d1d9eac331b2b8db218617edff7aa4425503a95")
# CNMT extended metadata + full ContentMetaDatabase query coverage; GPU owners unchanged.
expected.add("22e47d3b88d669048a4460b0e8b0a9d315f4ca22")
# NCM path commands now fail closed instead of leaking host VFS paths.
expected.add("b9e23460efcf82c3f3e86de303f9a27568004b24")
# IRS explicit no-ops and telemetry/news fallbacks; GPU source owners unchanged.
expected.add("569c8e2ae6fe3dfaecb578be4c104381329f53df")
expected.add("229ebbc5b25776604c061ebdb93ca31330fa5745")
# FSP cmd203 patch-data + cache-only save reader; concurrent HID/BCAT retained.
expected.add("8e387b641aa5c227db2d14d06b0457a91be043fc")
# FSP cache-size semantics + fail-closed unresolved save extension.
expected.add("e2da4886884f9dec2c6753db1de6e1048cfa095b")
# Friend offline ABI fixes, Palma classification, and mm:u reply fix.
expected.add("51e5cbde026b62038ac7f3b2845d3d00d95eeff6")
# BLE/hidbus, erpt, and active pctl backport follow-ups; GPU source owners unchanged.
expected.add("45ea626b6579cfa3eaabf56f6ca362e77e34f346")
expected.add("6bb62bfe4b830511f219e6cb0e50ced131a4b170")
expected.add("61e8993c8057ca9536f8997185118d072130497f")
# Stable hardware fallback state (BTM/LBL/PSM/TS); GPU source owners unchanged.
expected.add("4936c5528e0641e2176fc77a376cfb8d2da2d1b5")
# Persisted platform-region and synchronous NTC semantics; GPU source owners unchanged.
expected.add("be7f995c13675eeb3af8c1addac536876ed1e90b")
# FSP save filtering + immutable read-only filesystem; unrelated GPU owners unchanged.
expected.add("c3c3b6d23925dbe287e5a239663b9a04db6a0d21")
# Host-directory SaveDataExtraData validation; GPU owners unchanged.
expected.add("61ab696e00da26fca41e899323acb480e1770d15")
# FSP SD capability + NS installed-record/event/update policy; GPU owners unchanged.
expected.add("a691b5535f9c69539b466a926359d805d734acce")
# Host-directory synchronous commit + bounded multi-commit participant tracking.
expected.add("f6deaab8efa7a0c86e70d816a66792d7ce1811c3")
# NS1 NS vulnerability policy + FSP program-index registry/access-log ABI.
expected.add("ad27e09c7135c3c92ef0202b58ee35423fe74300")
# NS lifecycle state + game-card query + false-stub cleanup.
expected.add("4483c6a35526d9dc8fc77c70b140ff2358d76dc9")
# AM launchable-event ordering + stateful applet handlers.
expected.add("6fc24667f81ce27d07979ad25c0e4743e331f7d0")
# Main-applet identity/storage + inactive NS update policy.
expected.add("1b5b609d3022c5a54a4e3c72613435491c7f9e24")
# Home-button lifecycle + inactive HID firmware/Npad policies.
expected.add("2faf00b1d44881bdaebb24e27ecf08938eb83144")
# Active IApplicationAccessor lifecycle queries + child/display state.
expected.add("dff1bdb769d9d92738ff424aa3f0fe24f92016a2")
# NIFM IRequest state machine + legacy scan ABI.
expected.add("76de6f60e3a3e3982bac17ca45b34fa646388a89")
# NIFM ClientId/request accounting + legacy AP + library-applet creator NULLs.
expected.add("50f086881d16f4c6fb89e710ee1e4c6ce6336a04")
# Common applet terminate/Home state + out-of-focus lifecycle suspension.
expected.add("c8b1acd969db74a8250c49bf84dd480e5cd4f7c4")
# Active overlay out-of-focus fix + applet performance + NS application records.
expected.add("6f797482091484fcf3c926ed287ee4afd7618598")
# Stateful firmware/keyboard applet + NS active-header provenance fix.
expected.add("aea996472c7c7146795f3bbbb9e04e9bc0895a47")
# NULL recheck: self-header receipt + System NAND query + NIFM default IP state.
expected.add("40596a94e35789a57e9ee8236e0e6c4362cd1765")
# NULL recheck: NS terminate-result + NIFM control-state bindings.
expected.add("bc3d538f2c413489b2d881259b57a4c44b6698f9")
# NULL recheck: NS language conversion + desired-language selection.
expected.add("0897a295624827e95d9248d85ea8274e75584693")
# NULL recheck: GameCard state + FSP data storage / aggregate save reader.
expected.add("a7c2afb34048ff001b9ff80aad4ec6aa32aff703")
# NULL recheck: Horizon-official applet stubs + NIFM sleep/wake no-ops.
expected.add("36100c1740ad18d53949761846f21ffeb8a0f472")
# NULL recheck: real library-applet ExtraStorage channel.
expected.add("ebc5a68a9b5ac4316aa8c7ba3f6bebeab5817e5c")
# NULL recheck: NIFM exclusive-client/network-type policy state.
expected.add("05784b605535c987e1619c9b28e36f7752ba735b")
# NULL recheck: Friend Invitation / Notification storage channels.
expected.add("d1e41151f5e23b1ff2653c937b04ff5e344e29b0")
# NULL recheck: applet-bound IStorage channel.
expected.add("b217369d3f01b2958eae58815f190080a8b77296")
# NS1 persistent system-settings pairs.
expected.add("694becfbf6a27cecb907d8be5b0315c269654fa7")
# NS1 persisted PTM, RTC, calibration, USB system settings.
expected.add("9aa3b2568b3f74bd124f3923e88116a52c1c589a")
# NS1 extra persisted settings and theme policies.
expected.add("407b42a985c1d8558a516d41d5c03a216f4da433")
# NS1 RTC repair and hearing safeguard state; all other vendor shader blobs remain pinned.
expected.add("b0228bfc2c634ee3b7c61bec56d513b1c4673601")
# NS1 six-axis calibration settings only; exact tree below.
expected.add("0aa309cfbc3489073cc5586b5745be41c2d23e19")
# NS1 typed ThemeId state; checked against the exact reviewed vendor tree below.
expected.add("b84e58810ccd509acfbd00a8dda6ada8c0dcdabc")
# NS1 ThemeId ABI correction: aligned u64[16] payload, verified vendor tree.
expected.add("c8688e83435eb085285a18b581cea39b701ad266")
# NS1 persisted repair/discovery/theme-key settings, exact reviewed tree.
expected.add("33858387c023030896e649c84e1df806a3352889")
# NS1 BLE/account persisted arrays, exact reviewed tree.
expected.add("3b564c2d141b94fecc78e3f68753e00aea009180")
# NS1 persisted EDID/SSL-host/HostFS settings, exact reviewed tree.
expected.add("29b1cb6de394dc0ecc168481a8059e8f70a1b92d")
# NS1 BacklightSettingsEx raw persisted 0x2c block, exact reviewed tree.
expected.add("131cb5828f196fcd46f78a217eec43953e0bd083")
if selected in {"ac880cd408116e6eb53ba2400abc52970b81f539", "95343060f948601930f2e62b919da0789f0830bb", "12ab9a8411f5c9df1b5cc73f01c923ad9479c8af", "224b05e6f8b1a266b0d55d1ded5332f7a2eaed7c", "fe5a389ac04fa3c26c1756fc18e73a962e196da4", "e329e52f7de79302bfcc1b658431777501d5edd9", "ff0822695ec03ac7d9d2c75b4703adf12eec544f", "c3dc80c83d468e04c794b3d7d36bc1316b342bd4", "60bd03e6e5ad083ee050887028fa33d514a3050e", "488475c8c3867af07892a7f53cc6e15a54d09542", "8d1d9eac331b2b8db218617edff7aa4425503a95", "22e47d3b88d669048a4460b0e8b0a9d315f4ca22", "b9e23460efcf82c3f3e86de303f9a27568004b24", "569c8e2ae6fe3dfaecb578be4c104381329f53df", "229ebbc5b25776604c061ebdb93ca31330fa5745", "8e387b641aa5c227db2d14d06b0457a91be043fc", "e2da4886884f9dec2c6753db1de6e1048cfa095b", "51e5cbde026b62038ac7f3b2845d3d00d95eeff6", "45ea626b6579cfa3eaabf56f6ca362e77e34f346", "6bb62bfe4b830511f219e6cb0e50ced131a4b170", "61e8993c8057ca9536f8997185118d072130497f", "4936c5528e0641e2176fc77a376cfb8d2da2d1b5", "be7f995c13675eeb3af8c1addac536876ed1e90b", "c3c3b6d23925dbe287e5a239663b9a04db6a0d21", "61ab696e00da26fca41e899323acb480e1770d15", "a691b5535f9c69539b466a926359d805d734acce", "f6deaab8efa7a0c86e70d816a66792d7ce1811c3", "ad27e09c7135c3c92ef0202b58ee35423fe74300", "4483c6a35526d9dc8fc77c70b140ff2358d76dc9", "6fc24667f81ce27d07979ad25c0e4743e331f7d0", "1b5b609d3022c5a54a4e3c72613435491c7f9e24", "2faf00b1d44881bdaebb24e27ecf08938eb83144", "dff1bdb769d9d92738ff424aa3f0fe24f92016a2", "76de6f60e3a3e3982bac17ca45b34fa646388a89", "50f086881d16f4c6fb89e710ee1e4c6ce6336a04", "c8b1acd969db74a8250c49bf84dd480e5cd4f7c4", "6f797482091484fcf3c926ed287ee4afd7618598", "aea996472c7c7146795f3bbbb9e04e9bc0895a47", "40596a94e35789a57e9ee8236e0e6c4362cd1765", "bc3d538f2c413489b2d881259b57a4c44b6698f9", "0897a295624827e95d9248d85ea8274e75584693", "a7c2afb34048ff001b9ff80aad4ec6aa32aff703", "36100c1740ad18d53949761846f21ffeb8a0f472", "ebc5a68a9b5ac4316aa8c7ba3f6bebeab5817e5c", "05784b605535c987e1619c9b28e36f7752ba735b", "d1e41151f5e23b1ff2653c937b04ff5e344e29b0", "b217369d3f01b2958eae58815f190080a8b77296", "694becfbf6a27cecb907d8be5b0315c269654fa7", "9aa3b2568b3f74bd124f3923e88116a52c1c589a", "407b42a985c1d8558a516d41d5c03a216f4da433", "b0228bfc2c634ee3b7c61bec56d513b1c4673601", "0aa309cfbc3489073cc5586b5745be41c2d23e19", "b84e58810ccd509acfbd00a8dda6ada8c0dcdabc", "c8688e83435eb085285a18b581cea39b701ad266", "33858387c023030896e649c84e1df806a3352889", "3b564c2d141b94fecc78e3f68753e00aea009180", "29b1cb6de394dc0ecc168481a8059e8f70a1b92d", "131cb5828f196fcd46f78a217eec43953e0bd083"}:
    reviewed_tree = subprocess.check_output(
        ["git", "-C", str(V), "rev-parse", "HEAD^{tree}"], text=True
    ).strip()
    assert reviewed_tree == {
        "ac880cd408116e6eb53ba2400abc52970b81f539": "01c09ec124779e7d976718af09a0e5e94cb4ac20",
        "95343060f948601930f2e62b919da0789f0830bb": "efa6548c57f7823d4e8b2c975944c6846b765ff3",
        "12ab9a8411f5c9df1b5cc73f01c923ad9479c8af": "64179fcce4962f9b2b7c738504a6fa0e00b2b292",
        "224b05e6f8b1a266b0d55d1ded5332f7a2eaed7c": "3f7f1523cef730ad153bf658fbb3567222d6e956",
        "fe5a389ac04fa3c26c1756fc18e73a962e196da4": "d30f26b0ea1bd88ee9c326d7d46aaf5ebc2fbce9",
        "e329e52f7de79302bfcc1b658431777501d5edd9": "c8e22a89d88275ddd57a556bf0e4e715e133f473",
        "ff0822695ec03ac7d9d2c75b4703adf12eec544f": "39d199d468eeae1494a3942bbf13c1fffa05e948",
        "c3dc80c83d468e04c794b3d7d36bc1316b342bd4": "ec21773d1511a78da2bc3056ffc2b48b2971da7e",
        "60bd03e6e5ad083ee050887028fa33d514a3050e": "68f85f8f6c1d0cae8c56fde1cb8a2e8c1a03a087",
        "488475c8c3867af07892a7f53cc6e15a54d09542": "c46a26583a3bcdb672f9a8adfd25b66da592d66c",
        "8d1d9eac331b2b8db218617edff7aa4425503a95": "bbbc72a4967fb0192996d8f4ccc577e254c40acc",
        "22e47d3b88d669048a4460b0e8b0a9d315f4ca22": "80f98ebd869bb4db01c7de0fbc4dd302c9cc5a49",
        "b9e23460efcf82c3f3e86de303f9a27568004b24": "edde367d50df7d016bbd0a0d36fad550e4c1e3c3",
        "569c8e2ae6fe3dfaecb578be4c104381329f53df": "837bf41ef8f54530a06f3da8fbe1b372bbdf61e6",
        "229ebbc5b25776604c061ebdb93ca31330fa5745": "84142bbf8d1c4fc947dbaf0887fc43542349b318",
        "8e387b641aa5c227db2d14d06b0457a91be043fc": "94c9d09b3a1d47d9a0c10bd20a8b271862556eb6",
        "e2da4886884f9dec2c6753db1de6e1048cfa095b": "d1971e7a571833820a29c83257c661a21c036b39",
        "51e5cbde026b62038ac7f3b2845d3d00d95eeff6": "caf1395b6cc5504ca2c0711394f125dc66a05f88",
        "45ea626b6579cfa3eaabf56f6ca362e77e34f346": "5ef05afacc24cef4cb3e413211743b8883afc70c",
        "6bb62bfe4b830511f219e6cb0e50ced131a4b170": "eab5bd486d56590745c0a0e2454d9d90cacf4a8b",
        "61e8993c8057ca9536f8997185118d072130497f": "1d02e7fb6925dfa4dddf943c42a3e8583db83671",
        "4936c5528e0641e2176fc77a376cfb8d2da2d1b5": "4cf0ae3a76996c35c517be900561d5c09cd17023",
        "be7f995c13675eeb3af8c1addac536876ed1e90b": "054f6943d2456d3287b925cc50f35355dc2f3c08",
        "c3c3b6d23925dbe287e5a239663b9a04db6a0d21": "92f3fb7fdecc94c4691265f955d54165deb65991",
        "61ab696e00da26fca41e899323acb480e1770d15": "fc9c49905f9a4d3a10a077d74aaf66a5c7152f54",
        "a691b5535f9c69539b466a926359d805d734acce": "dfe1ef22dacebde8a6b110f9e006318e1d77f466",
        "f6deaab8efa7a0c86e70d816a66792d7ce1811c3": "0a2a081d41bc7400a25ff833b08d085826345478",
        "ad27e09c7135c3c92ef0202b58ee35423fe74300": "e6ddae9ffeaca9bc0319e056b7fd38ffb35eb056",
        "4483c6a35526d9dc8fc77c70b140ff2358d76dc9": "7ac58de8cc59a33b21de52fae13371d4f85801fa",
        "6fc24667f81ce27d07979ad25c0e4743e331f7d0": "28da2f872d33edf2ad11947991a0cf6c4e592475",
        "1b5b609d3022c5a54a4e3c72613435491c7f9e24": "a7c6437660846d69a4b049de5641561bd08b96cb",
        "2faf00b1d44881bdaebb24e27ecf08938eb83144": "18e76d6b282831c59c343950fac922d0130d1e09",
        "dff1bdb769d9d92738ff424aa3f0fe24f92016a2": "8cc006223327f14da5664476491da0ea364fabf6",
        "76de6f60e3a3e3982bac17ca45b34fa646388a89": "5508124e6fbc16279e5870434b331154cb7f62b6",
        "50f086881d16f4c6fb89e710ee1e4c6ce6336a04": "4f015ccf16419403354a03463a79edb4856b501f",
        "c8b1acd969db74a8250c49bf84dd480e5cd4f7c4": "30ada5ee51cd74e474250c3132e7a48eb82f3b1d",
        "6f797482091484fcf3c926ed287ee4afd7618598": "12879f10b2d866ba5b4536e62bedfcc0c28bb34e",
        "aea996472c7c7146795f3bbbb9e04e9bc0895a47": "b3b59fda00af67a52aa5bf5b8125df90ae312c26",
        "40596a94e35789a57e9ee8236e0e6c4362cd1765": "b6631a93395622feea9f86abdbb0b79dd6c4993d",
        "bc3d538f2c413489b2d881259b57a4c44b6698f9": "8307e210806b858beea5f87c49434685fe93831d",
        "0897a295624827e95d9248d85ea8274e75584693": "06e36212834c87b6d464f5349bf26851e336362f",
        "a7c2afb34048ff001b9ff80aad4ec6aa32aff703": "9b7cefd10652c20bdd3c0a62599e42e35e40c568",
        "36100c1740ad18d53949761846f21ffeb8a0f472": "c9042596bcfece3250e1574ab44061c182ff54ee",
        "ebc5a68a9b5ac4316aa8c7ba3f6bebeab5817e5c": "7a96cbc2af79a866e194c28fa33e438d9c897712",
        "05784b605535c987e1619c9b28e36f7752ba735b": "7502d3834222f5e3b35e4cb13f48d2755ab79bfe",
        "d1e41151f5e23b1ff2653c937b04ff5e344e29b0": "34dbfc91c0b5b086ef220eaee856627e37ac20e3",
        "b217369d3f01b2958eae58815f190080a8b77296": "d788055b10aa228029f24699acd653609c972baa",
        "694becfbf6a27cecb907d8be5b0315c269654fa7": "ba9035d2e9289d05d89a611c19477b91f3243d1f",
        "9aa3b2568b3f74bd124f3923e88116a52c1c589a": "fbd04c1ab3bc6858e873e48fb6c32c17db7a335e",
        "407b42a985c1d8558a516d41d5c03a216f4da433": "d49fdafca026f9a973a84ad42cf0981a0ead8b10",
        "b0228bfc2c634ee3b7c61bec56d513b1c4673601": "1375ddf53289af9de4d2e9cc34f03ffe3940ed30",
        "0aa309cfbc3489073cc5586b5745be41c2d23e19": "77e74e92fbfeb95d6c43628f5805937065611b9a",
        "b84e58810ccd509acfbd00a8dda6ada8c0dcdabc": "1dfe1ab8ff6006a263a72409f6232ee64f692cca",
        "c8688e83435eb085285a18b581cea39b701ad266": "79a660baca78426c374467f7e2b725824a260665",
        "33858387c023030896e649c84e1df806a3352889": "8bfc545041776e2c88592fb5561020aaed20fc82",
        "3b564c2d141b94fecc78e3f68753e00aea009180": "46f035e4e6a40dee8cb751651f9c4f2c0a307a8b",
        "29b1cb6de394dc0ecc168481a8059e8f70a1b92d": "449492017d849f1669f327d9ca8dd06b6f78daf0",
        "131cb5828f196fcd46f78a217eec43953e0bd083": "e193ac362ae443d8e96fb575fd199df38aea83be",
    }[selected], ("Vendor reviewed source tree drift", selected, reviewed_tree)
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
assert blob(active_ctx)=="a3c36f45fd9b2b89f096258f54dd9189287a82d0"
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
