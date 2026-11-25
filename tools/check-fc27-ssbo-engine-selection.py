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
# NS1 Bluetooth/NX controller persisted arrays, exact reviewed tree.
expected.add("032e41924a3d82f654ebbab15601eb609dbf4fcf")
# NS1 NetworkSettings + SSL host count fix, exact reviewed tree.
expected.add("3d97ca836c8825fedfc23de76a0c3295a93469fb")
# NS1 location-resolver manager child objects, exact reviewed tree.
expected.add("682f74ead16c33caff0da4d9e89d025a4cb85ea5")
# NS1 NCM cache verification and lifecycle semantics, exact reviewed tree.
expected.add("67db89c1195d79ee731fc783088ec38083804050")
# NS1 pre-provisioned NCM create contracts, exact reviewed tree.
expected.add("400974b505e47e85952469aeceb959bbbee41948")
# NS1 SSL connection state getters; exact reviewed vendor tree.
expected.add("6b477c04581797bc3a5677c6c849b297f3a4587f")
# NS1 persistent ButtonConfig commands 189-200, exact reviewed tree.
expected.add("5fdfa239cb6e148abac1ef2d6393b8950132bc2b")
# NS1 legacy BacklightSettings bridge, exact reviewed tree.
expected.add("9a5401c93d9c87bc0fcb3f955f35bd54744046a4")
# NS1 Terra flag mapped to persisted PlatformRegion, exact reviewed tree.
expected.add("bb450eb2e61d2e28856c5beb9fcc6fa1afc8adab")
# NS1 FSP SD-card accessibility policy, exact reviewed tree.
expected.add("be00691dcb6abbf888cc00a4a5dcbf10b377fac5")
# NS1 PCTL PIN storage/change event, exact reviewed tree.
expected.add("6f487f76b88c2ca12f81c189fddcc2a8f083c74c")
# NS1 PCTL unlock/restricted-session/unlinked event state, exact reviewed tree.
expected.add("6a4ef643a90629e005844cd7be6ea7d8f3cb3c6e")
# NS1 NCM cleanup/FS-content activation, exact reviewed tree.
expected.add("1a2a614892cde741adb10ba7dfc23dfee4d8ff06")
# NS1 PCTL custom restrictions + HOS23 PDM surface cleanup, exact reviewed tree.
expected.add("70829977dbe1e534887c4baa2ddd6c9a1252acc5")
# NS1 set:sys AudioVolume persisted device mapping, exact reviewed tree.
expected.add("73fea5e303c074b8c8d16d096f4245f8cfa5c15c")
# NS1 inert telemetry/fatal dirty-flag events, exact reviewed tree.
expected.add("d833c0f790973b53be9abf24df8d328377557494")
# NS1 HOS23 removal of set:sys firmware digest, exact reviewed tree.
expected.add("c1b7768aa16f8a731de420783cd1e31ca2f58104")
# NS1 HOS23 AHID service removal, exact reviewed tree.
expected.add("d6b9b3ff6dc8ffc8898fcc286569e6fc77750277")
# NS1 HOS23 removal of legacy acc:u0/u1 registrations, exact reviewed tree.
expected.add("b4297d22a50b391540e3b89f9c9a5afd1f9f1985")
# NS1 account-service exposure correction + refreshed exact backport manifest.
expected.add("1de640e1e347314a7cc95a7854414ca2d1ad53ce")
# NS1 persistent Account thumbnails + exact refreshed active backport manifests.
expected.add("2990b313b00f739b7a8863e3b3d896aede75f712")
# NS1 offline Friend contracts on exact reviewed vendor tree.
expected.add("f5ae5e2073add91752d510195a6f2d9f454b92de")
# NS1 stateful registered location resolver, exact reviewed vendor tree.
expected.add("0e261f9ce092ade8243443175ffc3b977772616c")
# NS1 AddOnContent resolver storage state, exact reviewed vendor tree.
expected.add("da41c660c92a9d8cfddeac29ec30e2148203aa27")
# NS1 normal LocationResolver redirection state, exact reviewed tree.
expected.add("9b1c483eea8e013f1907ede3c235fe7a8216a6b6")
# NS1 PCTL default rating organization state + refreshed active backport manifest.
expected.add("909c764d244ac0cd80ec2930085dbf672504ff84")
# NS1 PCTL stateful FreeCommunication list + refreshed active backport manifest.
expected.add("0baa3af3f57d883be26587f11ab7bc586e4f79d5")
# NS1 explicit APM guest-overclock policy; no host clock mutation.
expected.add("cff675360f1985a856a91f587565c79b79567818")
# NS1 local NIFM policy commands + refreshed active backport manifest.
expected.add("f918ebdbae5c375ab2eb5887031f26d14bec5976")
# NS1 CAPS shim-version compatibility hints made explicit no-ops.
expected.add("7dfbe3cc1409cc4b5f3bba145ba7fd4134cf271f")
# NS1 NIFM profile UUID preservation/removal and corrected request ABI.
expected.add("d1524eb55acb905c694a46cdb1333e32c0e4bdbf")
# NS1 set:sys wireless certification reads the real PRODINFOF calibration file.
expected.add("822662c72f38324e1f6eb56eeb4e0f55f3bc45d0")
# NS1 set:cal non-secret CAL0 fields, exact reviewed vendor tree.
expected.add("8b62686225121d894e40e7853083f636ac344c3c")
# NS1 set:cal additional non-secret CAL0 hardware fields.
expected.add("5e77bf80aacb96088b281487525e5c73d7884d22")
# NS1 Friend offline detail/relationship outputs, exact reviewed vendor tree.
expected.add("a12fa5d6eec6350470374088e011bc93684e5763")
# NS1 Friend offline profile/key/url reads, exact reviewed vendor tree.
expected.add("b5bdec17c65914db77f8dac4a6eb4f740c8bb1f0")
# NS1 Friend offline image/NNID/catalog reads, exact reviewed vendor tree.
expected.add("e15f20df4dd3765b1c3df3ee3fcfc4ab3e155590")
# NS1 Friend daemon session + offline info refresh, exact reviewed vendor tree.
expected.add("c1ae766d44a4871387232eefdeefd47a2dc00ff0")
# NS1 Friend V1 offline lists reconciled to exact SwIPC ABI.
expected.add("de2daec43b71d2f13e00b154f96e39770c4bd8c9")
# NS1 Friend empty-state clears are explicit idempotent no-ops.
expected.add("ab4f28f4d8f3b118c1d64d2f6744598860c388b6")
# NS1 Friend HOS19/20+ offline list/availability handlers.
expected.add("8e8e29be0c571686ca9852b6a968d440e20cd88e")
# NS1 Friend modern profile getters plus HOS23 catalogue requalification.
expected.add("4ce41124344107322445092db240e74fa824dbc6")
# NS1 FSP program mounts, save free-space and hash-salt path.
expected.add("fca87f6aed972e9326a1b2e616649c9cbd884ee6")
# NS1 FSP integrity receipts refreshed after runtime changes.
expected.add("209549e1e3cb877e70e88ffc3001880af01ba9ad")
# NS1 Friend modern aliases proven against Lichii ABI routing.
expected.add("170c613138dfa7d8740459239f2ee9cb54a936b1")
# NS1 FSP DeleteCacheStorage deletes the real per-program cache slot.
expected.add("3234390c8fa29100b3d64b637ed1abf822e6b223")
# NS1 FSP filtered save-data reader enumerates all matching real saves.
expected.add("9f4f9bef141c33a3bce353f68cf5b58bd94603e5")
# NS1 FSP masked ExtraData write validates real save target.
expected.add("8a721e38520792fdc1e0f474ec2ef07d7c16a665")
# NS1 NIFM IRequest preserves HOS23 0x24-byte Requirement state.
expected.add("62660c058f2a76353dba6bc208f165857460000e")
# NS1 NIFM persistent requests preserve OnHold across connectivity loss.
expected.add("2a7dfec8c6e31b4ba004501a666a4836443d3787")
# NS1 native SSL system contexts now return real IPC objects and CreateConnectionEx.
expected.add("d449cce2968bd306801b4ecbb5f3756134a540ae")
# NS1 NIFM IRequest policy state and socket registration.
expected.add("1e7f7911c5601714733c53e3b5b73a15ec44c9b7")
# NS1 NIFM live connection notification and WoWLAN delay state.
expected.add("0e9652b4f19ca998fe7d60d34460bd4bbdb1be30")
# NS1 PSM host-backed power state and HOS17 charge-info ABI fix.
expected.add("5f7e92ebb9600809d81ee6fbb898c7011b95c719")
# NS1 audctl target/default/master-volume state on maintained eden-core owner.
expected.add("c67f77d5b33e71ca70621ab4637f559a420d998d")
# NS1 audctl persistent output/headphone modes.
expected.add("d23a6e5bbb235f4b277e523baeac668330eb5982")
# NS1 FSP cmd606 returns the real Program NCA RightsId.
expected.add("83acc5124b1cdb62ba4b65ed8607968c832757a4")
# NS1 FSP transient external title-key overlay.
expected.add("0d4246090dac222c344cb3bed912728c56d79c7b")
# NS1 legacy BTM radio commands share set:sys state.
expected.add("0fcec5e76502b0def90d946bffdc29ff3e19000f")
expected.add("a243ecb09ad7853c9be5f1d9d192c5206c1ef3cc")
expected.add("f20f6736b79259cb325f6a44b7b994749e458bec")
expected.add("ecb8ae0e177cf5ac2015b26bff722f70a147f6cd")
expected.add("81cf89d58b0b4081ea3e276668368040a6a75355")
expected.add("2f294bbfaa54440eaf9dafe9cabd2c104ba3a439")
# NS1 HLE-only follow-ups + BLE/NSD; retain exact vendor tree and GPU source checks.
expected.add("5c16e26b1c6ff11145e47a0e7a810eb76d0541a4")
# NS1 HID manifest-only digest repair; keep the exact reviewed tree guard.
expected.add("67f68874018169305ebdd44ea06dd32855cb3667")
# NS1 NPNS correct user token owner; GPU sources unchanged.
expected.add("dd88a95f547dd1fa7f7a2536a41846d73203b213")
# NS1 NPNS ListenTo 64-bit IPC ABI; no GPU source change.
expected.add("c6e0b135e0aa565fe596298971c7e38add0ca3d3")
# NS1 NS overlay repair and NX audio notification rejection; GPU sources unchanged.
expected.add("ffb2182af7f137179cd2f68792d4b00c2a54cef5")
# HID guest virtual keyboard lock state and shared IPC ABI; GPU sources unchanged.
expected.add("be709442d734683ffd9725c7035a932a73bf5c87")
# NS1 PM manifest provenance repair; GPU sources unchanged.
expected.add("4534ccde306a715d0fe61698be23522ac5b2d44e")
# NS1 AM owner transfer; exact reviewed tree, GPU source checks unchanged.
expected.add("fd43ea21e70e2f16a76d7723b4578813cb28468c")
# NS1 AM legacy errors and CPU boost cancellation; GPU source checks unchanged.
expected.add("bdb10101b495c52d14a4afe17a30d52fcbcf32d6")
# NS1 VI layer stack mask update; exact reviewed tree.
expected.add("15b31ec775aea551bd126188c8e6e03987474bd2")
# NS1 BTM offline IPC batch; exact reviewed tree.
expected.add("18c93c2e711cc8477156176f051874f8473497ef")
# NS1 BTM legacy offline kernel events; exact reviewed tree.
expected.add("4bf2174fa0aa6649efad1130a8b69a127a69f83b")
# NS1 BGTC and NS lifecycle queries; exact reviewed tree.
expected.add("9bddf300fbfe814a48f57adc5dee6197afd34ad9")
# NS1 HID seven-axis transfer-memory lifetime; exact reviewed tree.
expected.add("b1a597f87c6de6f473cc533a0668f4d7d27ee092")
# NS1 LDN monitor lifecycle; exact reviewed tree.
expected.add("8597725202341eb5bf2086977c4d7d60b89e976b")
# NS1 AM play statistics runtime batch; exact reviewed tree.
expected.add("d12a06afee1436debb6d691cc098513daed0cd24")
# NS1 audio active-device/input-event contracts; exact reviewed tree.
expected.add("fe95e74d1c59f5a064ee81d98d630446bddd508d")
# NS1 nvdrv GetStatus ABI/init contract; exact reviewed tree.
expected.add("f828515505b9dcc6b5571d45815c6bca1ce62a9a")
# NS1 SSL interface-version HLE no-op; exact reviewed tree.
expected.add("1a42d4aed7974212294424c370f9e4e9e47ff08a")
# NS1 AM capture pool reads/copies; exact reviewed tree.
expected.add("99879eef9fb743cf2757b2d76f765487db70e337")
# NS1 I2C fail-closed hardware-session batch; exact reviewed tree.
expected.add("3b25cbfba01518d17cf27e4869db986c70d70b82")
# NS1 HID console six-axis sampling lifecycle; exact reviewed tree.
expected.add("a68dd1eb50cc71bffe385baaa54da5dddb0926aa")
# NS1 AM visible-error frontend routing; exact reviewed tree.
expected.add("a0c5a3beb7ab54a67a6d463002ab94e6d838f435")
# NS1 PDM HOS23 play-statistics ABI and persisted values; exact reviewed tree.
expected.add("175b4f2d6c9511f01aee10757a6255d84d16aab0")
# NS1 async ErrorContext output contract; exact reviewed tree.
expected.add("05646df19d6ec2db27c54ebff88fa2db9775d409")
# NS1 AM rights-environment fail-closed contract; exact reviewed tree.
expected.add("9248992c51c0c446e47e6cdb03e407d20c2a69dd")
# NS1 SSL PKI and NIFM event lifetime; GPU source and receipt unchanged.
expected.add("b2c0a25ec04f0e90668bf1d1a4b85948aa844c52")
# NS1 indexed application cache storage; exact reviewed source tree below.
expected.add("670673aff581924cc430d600f07ebfeea5559e07")
# NS1 SPL general service: real RSA expmod + shared boot reason state.
expected.add("594eacbef099b3f97f7975e19b5b64d57910ae77")
# NS1 NS read-only application record: real FS DataCorrupted classification.
expected.add("25d561a0fd182584da68d53bca65f5ec6dbee3c8")
# NS1 NPNS local state + HOS23 system ListenToByName ABI.
expected.add("b882a41e0b35a91051fb362cdf2082175d433748")
# NS1 maintained NVDEC owner retains SET_SUBMIT_TIMEOUT state.
expected.add("a11b70417f1c981580a86bf5391b4a24fe0890e9")
# NS1 AM save-data maxima now come from NACP, including cmd35.
expected.add("afac75c2d5e4e494335bbc48f18cbf8a9a3e17a3")
# NS1 LBL guest backlight state: applied brightness + explicit host-noop fade.
expected.add("c24bcfa3fb9da644d31689ae4d16f2745f240227")
# NS1 AM HDCP state is shared with CommonStateGetter and transition event.
expected.add("67219c2d7f5b88e3c20f148fbfab7c9bba3f087c")
# NS1 NIFM request policy: explicit no-op setters + applet-not-required result.
expected.add("100be854211d10cb02b96e8f0059e1d924fa09c3")
# NS1 AM ApproveToDisplay now publishes visibility through WindowSystem.
expected.add("0837393bd5c8c3c48f5681dea1ac1dba76a6d6c8")
expected.add("dab56d88cbbe166575546fff3346feb4727afbf4")
expected.add("94c61421e27d837e28b7331690305a72baad4d93")
expected.add("65cffbdeed0bf25fe1bf5b840450a426e1f3b255")
expected.add("4ee2d58ce739af8e91d78794d6859b4662f8cb86")
expected.add("301c0bda4d9e5d81320361ea5ca24ab5a8cffcd2")
# NS1 HID UniquePad: connected emulated slots + 64-bit count ABI.
expected.add("aa6c39c16c8229d322869a70e7be7a71e1237d5b")
expected.add("69e90bc940df1cfefcd9e3f6d0d7b5a5d7984413")
expected.add("945a4a0a9c4b535fa509f1ffed992d41632ddab7")
expected.add("08f3042aecf16bf086d5463c55c1c9a150603d0f")
expected.add("d2e93fb0fa67548d2ae500f1bde6c19c941ecb7a")
expected.add("b57ce2770c82aef425bc34e2fed2492f63adfe4d")
expected.add("95089b809f5eb4d3621eaddec92638e8c82f7fa4")
expected.add("3260a2ecf296b08d923e2cfe1205689b652cb9f1")
expected.add("1bd95def9ee03b841171924716280f6d5ccb3a09")
expected.add("54f03c30bac3ebd4d1b3bb04ab2df298bc565a87")
expected.add("3ae8cda53774da47ad69bdb4f91ef2434acf1fb5")
expected.add("695b49c4255c816f8212d2c8a17fe81daa6e4a77")
expected.add("e7137658964ed0ed011be58939a71519fb543b9a")
expected.add("ab5fa3bd3d8e4e2a90b43379d40760203c7520da")
expected.add("9ff0457f18f3d06771f450a665f75c454dae2f61")
expected.add("f48a197733474dd1b12400eec775a88e9f89828f")
expected.add("230caf1fd48d5f03c9dbdab77178a12c6738a65e")
expected.add("b6d141e0398d673ad115f76c67a86fa3908e3395")
expected.add("beb364e21f1942527a1321684d37ae07acfc5191")
expected.add("5842c124617c80cf26cc4efe5a9e53f968661d38")
expected.add("10432c439e6c591685634a3a42d341aaa419e87c")
expected.add("5fb4bec2cda9b8307a115b18d97f91cc8f095730")
expected.add("72810dae5e9dc201060381b134eadccd209c347c")
expected.add("616154a4bd8f224d0d881c9bc38cea3ffaabd3b8")
expected.add("cc1c05ca9dd3597690c0d2adc3f97ef2e5f32543")
expected.add("65fc254db8d34830d01329b39658a711af792286")
expected.add("85b37ea44ef1ca0d8c3c001ee4186aa42bd051d5")
expected.add("ea322a8365ee7190757a7389c8538971e467b9a6")
expected.add("114aafbd10411faa65d0194775fd93f4a358fc21")
expected.add("a6c0444213541f747a85bd7936b1f5046ca0023f")
expected.add("3c0eec8055735d537ca4cc59c57961ddc049caf5")
expected.add("1c35f384381a9ef52e3d8055186f3e30f7495bde")
expected.add("6693426e3aca6318b7305a001205c14f216d9658")
expected.add("5fa1a189b96500929514986a86d2926fe2ff9f5c")
expected.add("694561edac085c49be40022a574d9e6481bb5448")
expected.add("61637939907bcc513b7869936144ad083e712856")
expected.add("b6d4bdf90dbce6fe685a09a578e064a77f6293c7")
expected.add("aea632e0144cb4721a6469300fbdfda7d8d2f3eb")
expected.add("0ca719fa2b0c93e5cd77ec2e181f588bef34bc65")
expected.add("aaf3aaed779d10df89128073a9a3b304a69422a6")
expected.add("80f4972be4e5bf4a16247a8393ccbf0420bfd96c")
expected.add("eedfedbd8513a047ba393d48287c37dd196566cd")
expected.add("b322c48fce30b49df1d49bfae041535bd60bb307")
expected.add("43ccd9f0ad4d9563ed7a2cd9a4d36a29322ee48c")
expected.add("1bf7529e72295266f92beb180ae602ec9a954db4")
expected.add("224bac056b368bf4edf3f0575de187d40d4edb76")
expected.add("6a593a4466bf9b98220dfc0139239ae5d52c5437")
expected.add("8aeb5a99bc36d5a01a1cd409bb24d8bed990ab05")
expected.add("829c7964df4ea7dd6e16cb666e139561d920f737")
expected.add("f1e8c0b32320e6c08dd662b9e5f5d1ac71808226")
expected.add("a12ddefce7725faeeb98495ceb8ccb8cf3cd5f8f")
expected.add("001fea6ade91e82ec360e5bb2197f130680d6d6a")
expected.add("a06bccfd645add1c7d06063f5abfa8e1ba525c04")
expected.add("a520a7e9c054b25f02dfb2d0887bca127cb871ef")
expected.add("21bf94d43f07fcf66b37a6be82fb16b1099adaff")
expected.add("76b7356cbc63eae67ff7e73a66fc655ce1896b6d")
expected.add("d1b05d1e94eed35bc6d35f5f9db5d99156f4e5b5")
expected.add("72b6186f2d1248a332d580b7727e6161a930ca09")
expected.add("c9e6af612c60b047ed43de57d2465fe18b8df7cf")
expected.add("285b0c8646cfc8d7331ca63758c4d34161460bac")
expected.add("64fe70db980b3f60dd9fce1175a13f0ce3435b52")
expected.add("2493221582e7a41528c53546bed61180035fec4e")
expected.add("2c0ff436b2798f6c028b504b56d15a158794aa40")
expected.add("8f2137659278d52c71825939501b7aad466edc3e")
expected.add("b162bfe9925eba2e1a11a4bee4acad1218a62876")
expected.add("993a5e9ae75aa37f92527cc99d2d26bdcae54dfb")
expected.add("d1b965f49a76649392576551be724c0ee642d809")
expected.add("ef32954266481977a0c9c5eef2ff52f637fa45bb")
expected.add("3a1bbc0ffb3e3b8b4472997fb2f45e05908ee5de")
expected.add("5a0460f5a51a239ed0a9d9db806cb8bae88f645d")
expected.add("1f2e5c4d2a5243d850b855969474786e281d08d2")
expected.add("a64bcf8c38473234474aca49b4013ed3617e0dec")
expected.add("dc460d59824f532705781f8df8e72d951ebbd446")
expected.add("95313ec1089b64f884abe3106eb2996ff74a5f90")
expected.add("9b2333d972bca1fd03814d58fcc7ae9f4834820e")
expected.add("fb8384b5673beeeed268ee38fa021421ac51061f")
expected.add("6e2212b52d96463d74d17e90e260e372eee7aa80")
expected.add("c2063ba7d1a8acc7596fff3bbde994e9de9bb4be")
expected.add("6bcf1cb61b190766a459334ee462fb74f978e5f2")
expected.add("506bcfd7c74cf131029abeba02a3e37e793dd8c7")
expected.add("fc4894a72071fcabf7ad7363d5783f6c0d0bf609")
expected.add("4915afc7bebe87da64c5eeb64843a24727a887dd")
expected.add("04f219188c2c187e5bda6e462d871e5a9ff0b841")
expected.add("8b0b3b8b8622bb00f72b411ae324446ccaf22935")
expected.add("11bdd31265db39c90a67b92c923e97bd9960968c")
expected.add("683af96eb36362e89c0e0faecfa49cd9e6ab8059")
expected.add("8d14c398fd604733cfcc05d4dcd1d612ee53a921")
expected.add("4df98ff0a70343fca54c12146303ac84e0337546")
expected.add("f8e15a9c11ed569facf06edce7ca1b77c9c1fd3d")
expected.add("f9856b407eebd3533ea4687089849887c769240b")
expected.add("7ea2306eee8d69671336252a2018697b98f46112")
expected.add("aca5aba40ab556d32a2ae9aec25c2fbd6f783f00")
expected.add("518176771ae50589313b7dc5955fe118f9f2c0d1")
expected.add("1c1f244beddb9e1620830a352e6b4c0adb9424f9")
expected.add("0e5f7b03f26bae7f950e9293d632b6bd7b80d280")
expected.add("ee53db178e3bb04fb41792602d5d47e68b3f0b21")
expected.add("727d6de6ab259ce3103f5f244985fb1632e1202b")
expected.add("b3f8efa1d434a1d5d1568302f83ed18d4e33e9f1")
expected.add("69c1c7adda95aaa854f311011a50552d3036ebd8")
expected.add("f5a1d9b7e439084203d901bfddd4371d2fe33718")
expected.add("e964a6879a29531bcad73ac219225fb065ee2d81")
expected.add("cf2237b8d710536a5c75ce1e36b62eeccb2e6c53")
expected.add("535e1ee030ff343554f5c8b194f3b869a00b6894")
expected.add("3411fc67c3c5bce5947fb5561c43ea44bb53e377")
expected.add("34c62dbcf8d5b1ffedc4931b447fd52077866625")
expected.add("157de42f41e8574d699da4a077c93b314ab7e293")
expected.add("ad021a102fbb7edeadb5356c098b8625f5f8d44f")
expected.add("8b8227178f5e8062d95e7692e087d7fb0ac37abb")
expected.add("202667f02b0ebe909bf0e5c93af15f8966fc5814")
expected.add("84a8db4464e4989a067779b86605905e0f52ca52")
expected.add("b57110e18a26f3a4e518765a02726579866d02c4")
expected.add("9aeb0c4c87c3776318378084eb1803f627b0d694")
expected.add("f1c2e246ffbfa0327ad49aeff10d6541cffefe87")
expected.add("2a1baf9350e04b1d973c7f751e59098b192dccdc")
expected.add("4a68cca38b2622d2250931b74ac524a7fe580d2d")
expected.add("3aea5d5402fb282cc7f3691dc468063f88eace78")
expected.add("7a0047acd3329a10ae4162ec7feff4e6a32bc1aa")
expected.add("107de63757c661e3084fcd7acc4c3c1fabca536e")
expected.add("c499a3118340dc899091f9c98a2d03da584fceda")
expected.add("f1d3c7f2cfc23836b1fe4020ba989b440da0fe62")
expected.add("a1ae39a3ef6e56c88d47a6425a26ad71cf40f502")
expected.add("5db9e6dd27b777b28867a1add277e3fba2c0d821")
expected.add("7cbc3897ac97ddcd0c2bb3915e56a09e6e589d1e")
expected.add("a1d47a90e418d3bd12e20f6151bcb31a34d0c594")
expected.add("1452e213198f1dfbf508fe37fd1b548d6186ca2c")
expected.add("d461fda9a65f10e409ec50eb6b92396990bbac9c")
expected.add("4751b7f1fec2920f77913706423b0abe5b6e51c8")
expected.add("21df36e8ef5963b50765cbafb9428a744940c419")
expected.add("50009086f7a428c11ff75f4cbac9567a8bcb8df5")
expected.add("94ae95f0a556ff8b79cb54e9cb1c9bc8b05ec8b2")
# NS1 SPL/ES/SSL only: compare 94ae95f0..7b314d26 preserves every GPU-53 owner.
expected.add("7b314d266f958768ec311dd21cac5f1836af1b8a")
# SPL module .cpp/.h are now selected by the content-addressed overlay manifest.
expected.add("918ea63bfa46e5e9020672547b5632a9bcf979f4")
# HLE-only dual-runtime reconciliation; GPU-53 owners are byte-identical.
expected.add("60fd2bde523a8b4c21bd1613e14ac9781f368f68")
# HLE-only SSL/HID/audctl coverage; GPU-53 owners remain byte-identical.
expected.add("9deb12b4b53c82d426a938cf25486014664595f4")
# HLE-only audctl state/owner reconciliation; GPU owners unchanged.
expected.add("37ac6d1253b47e6ae7fdc8724e806c47d52ad6ab")
# HLE-only audio-device/manual-renderer completion; GPU owners unchanged.
expected.add("f4ed96b315893772761626bfbc4888e1dea89b7a")
# HLE-only VI/audctl/IRS completion; GPU owners remain byte-identical.
expected.add("611ad385f58616daa987415daf160f2ededd9136")
# HLE-only NVDRV service-table correction; GPU owners remain byte-identical.
expected.add("88e5a7cd6c3979f2aa887eae2757f606bf9206d6")
# HLE-only bounded IStorage write/resize completion; GPU owners unchanged.
expected.add("f314e762a3a44e0a860496c6ca49c9e5d5d50f0f")
# HID-bus lifecycle and publication correction; GPU owners unchanged.
expected.add("ce8e61b92958321bab3cc530ed7b27474b8e4c08")
# Font bounds and truncated-archive protection; GPU sources unchanged.
expected.add("657774c538584ffda9823958b29918e8d8dff00d")
# NS1 VI display query handlers; no shader/GPU ownership change.
expected.add("29c1065d976f19904a350a7d8379781646f62acc")
# NS1 query playtime bounds and VI docked resolution; GPU sources unchanged.
expected.add("05d914feda6f54b156b6ba5071dc192dfa573fcc")
if selected in {"7b314d266f958768ec311dd21cac5f1836af1b8a", "918ea63bfa46e5e9020672547b5632a9bcf979f4", "60fd2bde523a8b4c21bd1613e14ac9781f368f68", "9deb12b4b53c82d426a938cf25486014664595f4", "37ac6d1253b47e6ae7fdc8724e806c47d52ad6ab", "f4ed96b315893772761626bfbc4888e1dea89b7a", "611ad385f58616daa987415daf160f2ededd9136", "88e5a7cd6c3979f2aa887eae2757f606bf9206d6", "f314e762a3a44e0a860496c6ca49c9e5d5d50f0f", "ce8e61b92958321bab3cc530ed7b27474b8e4c08", "657774c538584ffda9823958b29918e8d8dff00d", "29c1065d976f19904a350a7d8379781646f62acc", "05d914feda6f54b156b6ba5071dc192dfa573fcc"} or selected in {"ac880cd408116e6eb53ba2400abc52970b81f539", "95343060f948601930f2e62b919da0789f0830bb", "12ab9a8411f5c9df1b5cc73f01c923ad9479c8af", "224b05e6f8b1a266b0d55d1ded5332f7a2eaed7c", "fe5a389ac04fa3c26c1756fc18e73a962e196da4", "e329e52f7de79302bfcc1b658431777501d5edd9", "ff0822695ec03ac7d9d2c75b4703adf12eec544f", "c3dc80c83d468e04c794b3d7d36bc1316b342bd4", "60bd03e6e5ad083ee050887028fa33d514a3050e", "488475c8c3867af07892a7f53cc6e15a54d09542", "8d1d9eac331b2b8db218617edff7aa4425503a95", "22e47d3b88d669048a4460b0e8b0a9d315f4ca22", "b9e23460efcf82c3f3e86de303f9a27568004b24", "569c8e2ae6fe3dfaecb578be4c104381329f53df", "229ebbc5b25776604c061ebdb93ca31330fa5745", "8e387b641aa5c227db2d14d06b0457a91be043fc", "e2da4886884f9dec2c6753db1de6e1048cfa095b", "51e5cbde026b62038ac7f3b2845d3d00d95eeff6", "45ea626b6579cfa3eaabf56f6ca362e77e34f346", "6bb62bfe4b830511f219e6cb0e50ced131a4b170", "61e8993c8057ca9536f8997185118d072130497f", "4936c5528e0641e2176fc77a376cfb8d2da2d1b5", "be7f995c13675eeb3af8c1addac536876ed1e90b", "c3c3b6d23925dbe287e5a239663b9a04db6a0d21", "61ab696e00da26fca41e899323acb480e1770d15", "a691b5535f9c69539b466a926359d805d734acce", "f6deaab8efa7a0c86e70d816a66792d7ce1811c3", "ad27e09c7135c3c92ef0202b58ee35423fe74300", "4483c6a35526d9dc8fc77c70b140ff2358d76dc9", "6fc24667f81ce27d07979ad25c0e4743e331f7d0", "1b5b609d3022c5a54a4e3c72613435491c7f9e24", "2faf00b1d44881bdaebb24e27ecf08938eb83144", "dff1bdb769d9d92738ff424aa3f0fe24f92016a2", "76de6f60e3a3e3982bac17ca45b34fa646388a89", "50f086881d16f4c6fb89e710ee1e4c6ce6336a04", "c8b1acd969db74a8250c49bf84dd480e5cd4f7c4", "6f797482091484fcf3c926ed287ee4afd7618598", "aea996472c7c7146795f3bbbb9e04e9bc0895a47", "40596a94e35789a57e9ee8236e0e6c4362cd1765", "bc3d538f2c413489b2d881259b57a4c44b6698f9", "0897a295624827e95d9248d85ea8274e75584693", "a7c2afb34048ff001b9ff80aad4ec6aa32aff703", "36100c1740ad18d53949761846f21ffeb8a0f472", "ebc5a68a9b5ac4316aa8c7ba3f6bebeab5817e5c", "05784b605535c987e1619c9b28e36f7752ba735b", "d1e41151f5e23b1ff2653c937b04ff5e344e29b0", "b217369d3f01b2958eae58815f190080a8b77296", "694becfbf6a27cecb907d8be5b0315c269654fa7", "9aa3b2568b3f74bd124f3923e88116a52c1c589a", "407b42a985c1d8558a516d41d5c03a216f4da433", "b0228bfc2c634ee3b7c61bec56d513b1c4673601", "0aa309cfbc3489073cc5586b5745be41c2d23e19", "b84e58810ccd509acfbd00a8dda6ada8c0dcdabc", "c8688e83435eb085285a18b581cea39b701ad266", "33858387c023030896e649c84e1df806a3352889", "3b564c2d141b94fecc78e3f68753e00aea009180", "29b1cb6de394dc0ecc168481a8059e8f70a1b92d", "131cb5828f196fcd46f78a217eec43953e0bd083", "032e41924a3d82f654ebbab15601eb609dbf4fcf", "3d97ca836c8825fedfc23de76a0c3295a93469fb", "682f74ead16c33caff0da4d9e89d025a4cb85ea5", "67db89c1195d79ee731fc783088ec38083804050", "400974b505e47e85952469aeceb959bbbee41948", "6b477c04581797bc3a5677c6c849b297f3a4587f", "5fdfa239cb6e148abac1ef2d6393b8950132bc2b", "9a5401c93d9c87bc0fcb3f955f35bd54744046a4", "bb450eb2e61d2e28856c5beb9fcc6fa1afc8adab", "be00691dcb6abbf888cc00a4a5dcbf10b377fac5", "6f487f76b88c2ca12f81c189fddcc2a8f083c74c", "6a4ef643a90629e005844cd7be6ea7d8f3cb3c6e", "1a2a614892cde741adb10ba7dfc23dfee4d8ff06", "70829977dbe1e534887c4baa2ddd6c9a1252acc5", "73fea5e303c074b8c8d16d096f4245f8cfa5c15c", "d833c0f790973b53be9abf24df8d328377557494", "c1b7768aa16f8a731de420783cd1e31ca2f58104", "d6b9b3ff6dc8ffc8898fcc286569e6fc77750277", "b4297d22a50b391540e3b89f9c9a5afd1f9f1985", "1de640e1e347314a7cc95a7854414ca2d1ad53ce", "2990b313b00f739b7a8863e3b3d896aede75f712", "f5ae5e2073add91752d510195a6f2d9f454b92de", "0e261f9ce092ade8243443175ffc3b977772616c", "da41c660c92a9d8cfddeac29ec30e2148203aa27", "9b1c483eea8e013f1907ede3c235fe7a8216a6b6", "909c764d244ac0cd80ec2930085dbf672504ff84", "0baa3af3f57d883be26587f11ab7bc586e4f79d5", "cff675360f1985a856a91f587565c79b79567818", "f918ebdbae5c375ab2eb5887031f26d14bec5976", "7dfbe3cc1409cc4b5f3bba145ba7fd4134cf271f", "d1524eb55acb905c694a46cdb1333e32c0e4bdbf", "822662c72f38324e1f6eb56eeb4e0f55f3bc45d0", "8b62686225121d894e40e7853083f636ac344c3c", "5e77bf80aacb96088b281487525e5c73d7884d22", "a12fa5d6eec6350470374088e011bc93684e5763", "b5bdec17c65914db77f8dac4a6eb4f740c8bb1f0", "e15f20df4dd3765b1c3df3ee3fcfc4ab3e155590", "c1ae766d44a4871387232eefdeefd47a2dc00ff0", "de2daec43b71d2f13e00b154f96e39770c4bd8c9", "ab4f28f4d8f3b118c1d64d2f6744598860c388b6", "8e8e29be0c571686ca9852b6a968d440e20cd88e", "4ce41124344107322445092db240e74fa824dbc6", "fca87f6aed972e9326a1b2e616649c9cbd884ee6", "209549e1e3cb877e70e88ffc3001880af01ba9ad", "170c613138dfa7d8740459239f2ee9cb54a936b1", "3234390c8fa29100b3d64b637ed1abf822e6b223", "9f4f9bef141c33a3bce353f68cf5b58bd94603e5", "8a721e38520792fdc1e0f474ec2ef07d7c16a665", "62660c058f2a76353dba6bc208f165857460000e", "2a7dfec8c6e31b4ba004501a666a4836443d3787", "d449cce2968bd306801b4ecbb5f3756134a540ae", "1e7f7911c5601714733c53e3b5b73a15ec44c9b7", "0e9652b4f19ca998fe7d60d34460bd4bbdb1be30", "5f7e92ebb9600809d81ee6fbb898c7011b95c719", "c67f77d5b33e71ca70621ab4637f559a420d998d", "d23a6e5bbb235f4b277e523baeac668330eb5982", "83acc5124b1cdb62ba4b65ed8607968c832757a4", "0d4246090dac222c344cb3bed912728c56d79c7b", "0fcec5e76502b0def90d946bffdc29ff3e19000f", "a243ecb09ad7853c9be5f1d9d192c5206c1ef3cc", "f20f6736b79259cb325f6a44b7b994749e458bec", "ecb8ae0e177cf5ac2015b26bff722f70a147f6cd", "81cf89d58b0b4081ea3e276668368040a6a75355", "2f294bbfaa54440eaf9dafe9cabd2c104ba3a439" ,"5c16e26b1c6ff11145e47a0e7a810eb76d0541a4", "67f68874018169305ebdd44ea06dd32855cb3667", "dd88a95f547dd1fa7f7a2536a41846d73203b213", "c6e0b135e0aa565fe596298971c7e38add0ca3d3", "ffb2182af7f137179cd2f68792d4b00c2a54cef5", "be709442d734683ffd9725c7035a932a73bf5c87", "4534ccde306a715d0fe61698be23522ac5b2d44e", "fd43ea21e70e2f16a76d7723b4578813cb28468c", "bdb10101b495c52d14a4afe17a30d52fcbcf32d6", "15b31ec775aea551bd126188c8e6e03987474bd2", "18c93c2e711cc8477156176f051874f8473497ef", "4bf2174fa0aa6649efad1130a8b69a127a69f83b", "9bddf300fbfe814a48f57adc5dee6197afd34ad9", "b1a597f87c6de6f473cc533a0668f4d7d27ee092", "8597725202341eb5bf2086977c4d7d60b89e976b", "d12a06afee1436debb6d691cc098513daed0cd24", "fe95e74d1c59f5a064ee81d98d630446bddd508d", "f828515505b9dcc6b5571d45815c6bca1ce62a9a", "1a42d4aed7974212294424c370f9e4e9e47ff08a", "99879eef9fb743cf2757b2d76f765487db70e337", "3b25cbfba01518d17cf27e4869db986c70d70b82", "a68dd1eb50cc71bffe385baaa54da5dddb0926aa", "a0c5a3beb7ab54a67a6d463002ab94e6d838f435", "175b4f2d6c9511f01aee10757a6255d84d16aab0", "05646df19d6ec2db27c54ebff88fa2db9775d409", "9248992c51c0c446e47e6cdb03e407d20c2a69dd", "b2c0a25ec04f0e90668bf1d1a4b85948aa844c52", "670673aff581924cc430d600f07ebfeea5559e07", "594eacbef099b3f97f7975e19b5b64d57910ae77", "25d561a0fd182584da68d53bca65f5ec6dbee3c8", "b882a41e0b35a91051fb362cdf2082175d433748", "a11b70417f1c981580a86bf5391b4a24fe0890e9", "afac75c2d5e4e494335bbc48f18cbf8a9a3e17a3", "c24bcfa3fb9da644d31689ae4d16f2745f240227", "67219c2d7f5b88e3c20f148fbfab7c9bba3f087c", "100be854211d10cb02b96e8f0059e1d924fa09c3", "0837393bd5c8c3c48f5681dea1ac1dba76a6d6c8", "dab56d88cbbe166575546fff3346feb4727afbf4", "94c61421e27d837e28b7331690305a72baad4d93", "65cffbdeed0bf25fe1bf5b840450a426e1f3b255", "4ee2d58ce739af8e91d78794d6859b4662f8cb86", "301c0bda4d9e5d81320361ea5ca24ab5a8cffcd2", "aa6c39c16c8229d322869a70e7be7a71e1237d5b", "69e90bc940df1cfefcd9e3f6d0d7b5a5d7984413", "945a4a0a9c4b535fa509f1ffed992d41632ddab7", "08f3042aecf16bf086d5463c55c1c9a150603d0f", "d2e93fb0fa67548d2ae500f1bde6c19c941ecb7a", "b57ce2770c82aef425bc34e2fed2492f63adfe4d", "95089b809f5eb4d3621eaddec92638e8c82f7fa4", "3260a2ecf296b08d923e2cfe1205689b652cb9f1", "1bd95def9ee03b841171924716280f6d5ccb3a09", "54f03c30bac3ebd4d1b3bb04ab2df298bc565a87", "3ae8cda53774da47ad69bdb4f91ef2434acf1fb5", "695b49c4255c816f8212d2c8a17fe81daa6e4a77", "e7137658964ed0ed011be58939a71519fb543b9a", "ab5fa3bd3d8e4e2a90b43379d40760203c7520da", "9ff0457f18f3d06771f450a665f75c454dae2f61", "f48a197733474dd1b12400eec775a88e9f89828f", "230caf1fd48d5f03c9dbdab77178a12c6738a65e", "b6d141e0398d673ad115f76c67a86fa3908e3395", "beb364e21f1942527a1321684d37ae07acfc5191", "5842c124617c80cf26cc4efe5a9e53f968661d38", "10432c439e6c591685634a3a42d341aaa419e87c", "5fb4bec2cda9b8307a115b18d97f91cc8f095730", "72810dae5e9dc201060381b134eadccd209c347c", "616154a4bd8f224d0d881c9bc38cea3ffaabd3b8", "cc1c05ca9dd3597690c0d2adc3f97ef2e5f32543", "65fc254db8d34830d01329b39658a711af792286", "85b37ea44ef1ca0d8c3c001ee4186aa42bd051d5", "ea322a8365ee7190757a7389c8538971e467b9a6", "114aafbd10411faa65d0194775fd93f4a358fc21", "a6c0444213541f747a85bd7936b1f5046ca0023f", "3c0eec8055735d537ca4cc59c57961ddc049caf5", "1c35f384381a9ef52e3d8055186f3e30f7495bde", "6693426e3aca6318b7305a001205c14f216d9658", "5fa1a189b96500929514986a86d2926fe2ff9f5c", "694561edac085c49be40022a574d9e6481bb5448", "61637939907bcc513b7869936144ad083e712856", "b6d4bdf90dbce6fe685a09a578e064a77f6293c7", "aea632e0144cb4721a6469300fbdfda7d8d2f3eb", "0ca719fa2b0c93e5cd77ec2e181f588bef34bc65", "aaf3aaed779d10df89128073a9a3b304a69422a6", "80f4972be4e5bf4a16247a8393ccbf0420bfd96c", "eedfedbd8513a047ba393d48287c37dd196566cd", "b322c48fce30b49df1d49bfae041535bd60bb307", "43ccd9f0ad4d9563ed7a2cd9a4d36a29322ee48c", "1bf7529e72295266f92beb180ae602ec9a954db4", "224bac056b368bf4edf3f0575de187d40d4edb76", "6a593a4466bf9b98220dfc0139239ae5d52c5437", "8aeb5a99bc36d5a01a1cd409bb24d8bed990ab05", "829c7964df4ea7dd6e16cb666e139561d920f737", "f1e8c0b32320e6c08dd662b9e5f5d1ac71808226", "a12ddefce7725faeeb98495ceb8ccb8cf3cd5f8f", "001fea6ade91e82ec360e5bb2197f130680d6d6a", "a06bccfd645add1c7d06063f5abfa8e1ba525c04", "a520a7e9c054b25f02dfb2d0887bca127cb871ef", "21bf94d43f07fcf66b37a6be82fb16b1099adaff", "76b7356cbc63eae67ff7e73a66fc655ce1896b6d", "d1b05d1e94eed35bc6d35f5f9db5d99156f4e5b5", "72b6186f2d1248a332d580b7727e6161a930ca09", "c9e6af612c60b047ed43de57d2465fe18b8df7cf", "285b0c8646cfc8d7331ca63758c4d34161460bac", "64fe70db980b3f60dd9fce1175a13f0ce3435b52", "2493221582e7a41528c53546bed61180035fec4e", "2c0ff436b2798f6c028b504b56d15a158794aa40", "8f2137659278d52c71825939501b7aad466edc3e", "b162bfe9925eba2e1a11a4bee4acad1218a62876", "993a5e9ae75aa37f92527cc99d2d26bdcae54dfb", "d1b965f49a76649392576551be724c0ee642d809", "ef32954266481977a0c9c5eef2ff52f637fa45bb", "3a1bbc0ffb3e3b8b4472997fb2f45e05908ee5de", "5a0460f5a51a239ed0a9d9db806cb8bae88f645d", "1f2e5c4d2a5243d850b855969474786e281d08d2", "a64bcf8c38473234474aca49b4013ed3617e0dec", "dc460d59824f532705781f8df8e72d951ebbd446", "95313ec1089b64f884abe3106eb2996ff74a5f90", "9b2333d972bca1fd03814d58fcc7ae9f4834820e", "fb8384b5673beeeed268ee38fa021421ac51061f", "6e2212b52d96463d74d17e90e260e372eee7aa80", "c2063ba7d1a8acc7596fff3bbde994e9de9bb4be", "6bcf1cb61b190766a459334ee462fb74f978e5f2", "506bcfd7c74cf131029abeba02a3e37e793dd8c7", "fc4894a72071fcabf7ad7363d5783f6c0d0bf609", "4915afc7bebe87da64c5eeb64843a24727a887dd", "04f219188c2c187e5bda6e462d871e5a9ff0b841", "8b0b3b8b8622bb00f72b411ae324446ccaf22935", "11bdd31265db39c90a67b92c923e97bd9960968c", "683af96eb36362e89c0e0faecfa49cd9e6ab8059", "8d14c398fd604733cfcc05d4dcd1d612ee53a921", "4df98ff0a70343fca54c12146303ac84e0337546", "f8e15a9c11ed569facf06edce7ca1b77c9c1fd3d", "f9856b407eebd3533ea4687089849887c769240b", "7ea2306eee8d69671336252a2018697b98f46112", "aca5aba40ab556d32a2ae9aec25c2fbd6f783f00", "518176771ae50589313b7dc5955fe118f9f2c0d1", "1c1f244beddb9e1620830a352e6b4c0adb9424f9", "0e5f7b03f26bae7f950e9293d632b6bd7b80d280", "ee53db178e3bb04fb41792602d5d47e68b3f0b21", "727d6de6ab259ce3103f5f244985fb1632e1202b", "b3f8efa1d434a1d5d1568302f83ed18d4e33e9f1", "69c1c7adda95aaa854f311011a50552d3036ebd8", "f5a1d9b7e439084203d901bfddd4371d2fe33718", "e964a6879a29531bcad73ac219225fb065ee2d81", "cf2237b8d710536a5c75ce1e36b62eeccb2e6c53", "535e1ee030ff343554f5c8b194f3b869a00b6894", "3411fc67c3c5bce5947fb5561c43ea44bb53e377", "34c62dbcf8d5b1ffedc4931b447fd52077866625"}:
    reviewed_tree = subprocess.check_output(
        ["git", "-C", str(V), "rev-parse", "HEAD^{tree}"], text=True
    ).strip()
    assert reviewed_tree == {
        "7b314d266f958768ec311dd21cac5f1836af1b8a": "a861b3466be3e4995c5f9d832397c5041c199ebb",
        "918ea63bfa46e5e9020672547b5632a9bcf979f4": "3049baab5148e518c003d776798968e9140a44d2",
        "60fd2bde523a8b4c21bd1613e14ac9781f368f68": "8aac71034203499ea3432ece7b194b797ea4aab5",
        "9deb12b4b53c82d426a938cf25486014664595f4": "01b65400794973e7a5d1b7b56b5c5ac1707e8778",
        "37ac6d1253b47e6ae7fdc8724e806c47d52ad6ab": "7dcf27a900b9ccf833cdb8f6b127e4c844cf22f0",
        "f4ed96b315893772761626bfbc4888e1dea89b7a": "e3452a3dac9374a9db84867ad959ae6494b5c4bc",
        "611ad385f58616daa987415daf160f2ededd9136": "da3a9bcce6ef04d4dcc7ba416cada6786722727c",
        "88e5a7cd6c3979f2aa887eae2757f606bf9206d6": "fe2c55a5c97947487027682d5a5cffa5fcfa1cd3",
        "f314e762a3a44e0a860496c6ca49c9e5d5d50f0f": "b349fb5f938010934ba6f546b72d05d3c2c5e8a0",
        "ce8e61b92958321bab3cc530ed7b27474b8e4c08": "b554050cc9692a9e61f6e207386d33bffe3ebaff",
        "657774c538584ffda9823958b29918e8d8dff00d": "c3531228561170a862d9e031732cd4e9caa3b1f8",
        "29c1065d976f19904a350a7d8379781646f62acc": "e7691d67139af3d1ad0260424b9c6b9b0fafbfd0",
        "05d914feda6f54b156b6ba5071dc192dfa573fcc": "40d8985dcf17ff8ed7de98ab5ea76f1999dbb180",
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
        "032e41924a3d82f654ebbab15601eb609dbf4fcf": "e1e916b5e51b17b542eea5010889dacc850077fb",
        "3d97ca836c8825fedfc23de76a0c3295a93469fb": "1971dc01df3359a0dc74df18be6ef1e90d60937b",
        "682f74ead16c33caff0da4d9e89d025a4cb85ea5": "51965f0e80d8c18df8c5f829276daed7089ca0e1",
        "67db89c1195d79ee731fc783088ec38083804050": "a477fa09a667ba6144e31aaf59921386067ce4ee",
        "400974b505e47e85952469aeceb959bbbee41948": "6fda5c117836e91b18c76796121f9e58b4fe17a0",
        "6b477c04581797bc3a5677c6c849b297f3a4587f": "9f16c143a040213aa2429acbceaf5b2250ce5b30",
        "5fdfa239cb6e148abac1ef2d6393b8950132bc2b": "dbfc5e1a0e5ff72834206bb4cbe066ce1ab85246",
        "9a5401c93d9c87bc0fcb3f955f35bd54744046a4": "e4da559826dccca47deb8d35a4fdfb0882404733",
        "bb450eb2e61d2e28856c5beb9fcc6fa1afc8adab": "8b5f9570428f539fb4a414659eb2afefc5c9fe70",
        "be00691dcb6abbf888cc00a4a5dcbf10b377fac5": "982c71474dbabaa0b4829af66c5c6c59847004ec",
        "6f487f76b88c2ca12f81c189fddcc2a8f083c74c": "34ca4655b3822ed3ba9d47622d4399bae9f3ff3b",
        "6a4ef643a90629e005844cd7be6ea7d8f3cb3c6e": "f24749580d8cf74dfacee33dd11ebce7836c8629",
        "1a2a614892cde741adb10ba7dfc23dfee4d8ff06": "e6e631075d5e4ffbd8895fcfc6741363ae4b2bf8",
        "70829977dbe1e534887c4baa2ddd6c9a1252acc5": "7dc7ba8a5ecbc75cf37f2f54efeb0cdbd04f24f8",
        "73fea5e303c074b8c8d16d096f4245f8cfa5c15c": "e016ea5e3aa9d92d3477a258487745658420c425",
        "d833c0f790973b53be9abf24df8d328377557494": "53e0136353a64f4cfaa86e24541d634764d8e318",
        "c1b7768aa16f8a731de420783cd1e31ca2f58104": "ae8748e568d9ad38d40e32ae95bb342a3a08daa6",
        "d6b9b3ff6dc8ffc8898fcc286569e6fc77750277": "dad2460f1464a2a98122be21d9389d579af75a94",
        "b4297d22a50b391540e3b89f9c9a5afd1f9f1985": "c192126108c3780633116955500f3f25c406c825",
        "1de640e1e347314a7cc95a7854414ca2d1ad53ce": "c9b36db79d19295a5454c6c054f728151320990c",
        "2990b313b00f739b7a8863e3b3d896aede75f712": "a2c8c7999086be1afad86466c4f9a5c867671ff7",
        "f5ae5e2073add91752d510195a6f2d9f454b92de": "c4eb1151a2007ff263b547be5d09fce431064c97",
        "0e261f9ce092ade8243443175ffc3b977772616c": "8dd9abffeab8f3e2c75ec39806570881c7d30b12",
        "da41c660c92a9d8cfddeac29ec30e2148203aa27": "bfcb971ca0c7c6fdff2fb5732b594c1259c14e2d",
        "9b1c483eea8e013f1907ede3c235fe7a8216a6b6": "bfd2db62ed954aefa1c6b50ee7ea4e48db7f6f08",
        "909c764d244ac0cd80ec2930085dbf672504ff84": "d95cd18c5a0156428f8e09be246a4bcca13b3cdc",
        "0baa3af3f57d883be26587f11ab7bc586e4f79d5": "6ea443768cb417cace310e087f52b4250d14f3a2",
        "cff675360f1985a856a91f587565c79b79567818": "1ca6e84c217e6a85bf9a686e378f05192b44c68c",
        "f918ebdbae5c375ab2eb5887031f26d14bec5976": "c52752f61475b9ac2e2e4e7ff2374106b989ced0",
        "7dfbe3cc1409cc4b5f3bba145ba7fd4134cf271f": "4a8902e36b4c0d429b0bf1071fedc8f7f85c0109",
        "d1524eb55acb905c694a46cdb1333e32c0e4bdbf": "b4b65ea5bffc675c996d4e8eae4b7dc530a6ea53",
        "822662c72f38324e1f6eb56eeb4e0f55f3bc45d0": "7a9fe224d54a0c73e014a0e6f32f0229dfbb2dce",
        "8b62686225121d894e40e7853083f636ac344c3c": "b52c35e5b39352a3a86c44c45f0ee17892fbb066",
        "5e77bf80aacb96088b281487525e5c73d7884d22": "94d3a154d9b897032cc75da54b62fb33a870e89a",
        "a12fa5d6eec6350470374088e011bc93684e5763": "855c15d239a1cd44547a3cda8de29cace9bee328",
        "b5bdec17c65914db77f8dac4a6eb4f740c8bb1f0": "ee52c1bb868bc0e1bf28566bb7bae0c9a314c768",
        "e15f20df4dd3765b1c3df3ee3fcfc4ab3e155590": "ef8803c118f902adac0ed1edd6aa914371317ad6",
        "c1ae766d44a4871387232eefdeefd47a2dc00ff0": "b20ef68916315f21a52e2b76b637f3bd9b04d717",
        "de2daec43b71d2f13e00b154f96e39770c4bd8c9": "5b4f442159c08643686b78fc5dd82146c4141f2a",
        "ab4f28f4d8f3b118c1d64d2f6744598860c388b6": "ee3b73db16643181b54d520d98cf2cb0fbc60533",
        "8e8e29be0c571686ca9852b6a968d440e20cd88e": "6e41aa672a4f4098b982204ad00c8060b2e846dc",
        "4ce41124344107322445092db240e74fa824dbc6": "620e78545ee2775dbdfa0716fff9a64f789a3812",
        "fca87f6aed972e9326a1b2e616649c9cbd884ee6": "31ae4572584d1216be8bdc81a446a6f8110e94dc",
        "209549e1e3cb877e70e88ffc3001880af01ba9ad": "44d0ee931f0bdf865b787cd33dbc10611185ecfe",
        "170c613138dfa7d8740459239f2ee9cb54a936b1": "006b451ddc375575b35ec37778356243273f01e5",
        "3234390c8fa29100b3d64b637ed1abf822e6b223": "24772de52fe6c3837ff71231e2121b5bcebd47a0",
        "9f4f9bef141c33a3bce353f68cf5b58bd94603e5": "bf9097bdaf82c025fc15f2a4cd9e1541adbdb152",
        "8a721e38520792fdc1e0f474ec2ef07d7c16a665": "72e68b086fb0911c6211d0550c753f87feb3f966",
        "62660c058f2a76353dba6bc208f165857460000e": "1b4a906b11137ad31c9b45a3063e70d6686a0eeb",
        "2a7dfec8c6e31b4ba004501a666a4836443d3787": "463636f6351a0b366b0e226fc88e3f0ad91f0f1b",
        "d449cce2968bd306801b4ecbb5f3756134a540ae": "cb9fd5e6168e4134898c5e9b4516a5c9f55a1c53",
        "1e7f7911c5601714733c53e3b5b73a15ec44c9b7": "f7cdef676a8b47790971e20c2b6ba03e0d66cb81",
        "0e9652b4f19ca998fe7d60d34460bd4bbdb1be30": "d8fcbce6d134cdcd8716060d7817c94cf5f89df7",
        "5f7e92ebb9600809d81ee6fbb898c7011b95c719": "faf1ab63c88c0c408b42c74735e2072d90818c84",
        "c67f77d5b33e71ca70621ab4637f559a420d998d": "9e60f3bc7e6a85b5f6c5fb6d4ce79ece460be73e",
        "d23a6e5bbb235f4b277e523baeac668330eb5982": "3c893de47856e787abf50ca4b0b86429b243225b",
        "83acc5124b1cdb62ba4b65ed8607968c832757a4": "b7bf7c18140e7af806bccb2aab1ee99733a09937",
        "0d4246090dac222c344cb3bed912728c56d79c7b": "181d4d1a18dedf20c4e28fb4c1a48a8fde2be1d9",
        "0fcec5e76502b0def90d946bffdc29ff3e19000f": "562294e7a9742631cdaab84d2924f6454486a4a3",
        "a243ecb09ad7853c9be5f1d9d192c5206c1ef3cc": "f53f4750d84de2bbb941984508a885241e7e6f41",
        "f20f6736b79259cb325f6a44b7b994749e458bec": "c467583c2cc4dd86e59461792c31a0d43f6f82cc",
        "ecb8ae0e177cf5ac2015b26bff722f70a147f6cd": "f54da66c6c41185383dcf9df07f0211aee96df5c",
        "81cf89d58b0b4081ea3e276668368040a6a75355": "147ec9af95f283aad866c61ed853cb76be98c270",
        "2f294bbfaa54440eaf9dafe9cabd2c104ba3a439": "0675e1f32d05e13c3ae0c8bbf0c20d841be03ecf",
        "5c16e26b1c6ff11145e47a0e7a810eb76d0541a4": "843f4bdabbe807edb1679c68fee31e4849394604",
        "67f68874018169305ebdd44ea06dd32855cb3667": "662d7b45bcac38f5f6ce03ab767d123deae1b44a",
        "dd88a95f547dd1fa7f7a2536a41846d73203b213": "7297f02ef7cc81efdb3ff9a5cb810f8f3a272c97",
        "c6e0b135e0aa565fe596298971c7e38add0ca3d3": "dfad655b555a171b732226b843657830686140ec",
        "ffb2182af7f137179cd2f68792d4b00c2a54cef5": "9ba87635a1f63500e41f2a919116e670b586853c",
        "be709442d734683ffd9725c7035a932a73bf5c87": "f8d52386be5394d8c0e38ae36be3425aa15fbbb3",
        "4534ccde306a715d0fe61698be23522ac5b2d44e": "eb3a012c82a899a84b2c880c6c36d9720c580f76",
        "fd43ea21e70e2f16a76d7723b4578813cb28468c": "e5957ed4b34177996fa5128497723beea14c0638",
        "bdb10101b495c52d14a4afe17a30d52fcbcf32d6": "c71a3257d1502deb656a18eb10447beb3ccf8c76",
        "15b31ec775aea551bd126188c8e6e03987474bd2": "ec3b523351afadd87211d06003622e25a4ade230",
        "18c93c2e711cc8477156176f051874f8473497ef": "e8da916fb10c23d84a0a97ef80b82033a676a13d",
        "4bf2174fa0aa6649efad1130a8b69a127a69f83b": "94e016679149bb468786379c2a9287a9ab90df9e",
        "9bddf300fbfe814a48f57adc5dee6197afd34ad9": "27bd7434ba71529fdc6d460f9685a1330c4fdacb",
        "b1a597f87c6de6f473cc533a0668f4d7d27ee092": "cc6b646340864a099f50b2c79820a7d4e0f64934",
        "8597725202341eb5bf2086977c4d7d60b89e976b": "2cdac7bf33faae8d08b557bc51bc6b19723cfac6",
        "d12a06afee1436debb6d691cc098513daed0cd24": "97c9df2b20e787e263265f951c77f45cb21d0748",
        "fe95e74d1c59f5a064ee81d98d630446bddd508d": "b64f12072c06ae36463c3d5a5705d64ff1b88ffc",
        "f828515505b9dcc6b5571d45815c6bca1ce62a9a": "eb80d6d52a058ef73d86f9c40ab5ae740beebf2f",
        "1a42d4aed7974212294424c370f9e4e9e47ff08a": "49a709167175824731fc121c5e05eca4be27ba41",
        "99879eef9fb743cf2757b2d76f765487db70e337": "14376bc19cc2b7a7ab94f28b4ed81382094b5954",
        "3b25cbfba01518d17cf27e4869db986c70d70b82": "f4ca8d88acc88ac46dad3f4b4ace6c0fc643bab6",
        "a68dd1eb50cc71bffe385baaa54da5dddb0926aa": "17d40397c66925a304776c545ccb9509fefa6fb8",
        "a0c5a3beb7ab54a67a6d463002ab94e6d838f435": "c4d6d7d1a107143b39ebaa38139e0169f470dd6b",
        "175b4f2d6c9511f01aee10757a6255d84d16aab0": "b19f6a65bdee666df6bd59a1691574200568c538",
        "05646df19d6ec2db27c54ebff88fa2db9775d409": "d2c90ee3b0a0b60cad03ed8bfb9c434c31243464",
        "9248992c51c0c446e47e6cdb03e407d20c2a69dd": "247415d930f7fccb14b51c22b6ae2128fbad70ec",
        "b2c0a25ec04f0e90668bf1d1a4b85948aa844c52": "413984847db7974d648ae1e0c170c0394e422676",
        "670673aff581924cc430d600f07ebfeea5559e07": "8c8bd0f82127872cc89bbff3cc5e5afc9aaea031",
        "594eacbef099b3f97f7975e19b5b64d57910ae77": "9da3bf26d82d360f75972482e33cf9dbbb67878e",
        "25d561a0fd182584da68d53bca65f5ec6dbee3c8": "3fd49f5abb77fe59eb8bc7f128663532fbea5824",
        "b882a41e0b35a91051fb362cdf2082175d433748": "a69f0624939699f8f407f5f8f75ad5a149c04574",
        "a11b70417f1c981580a86bf5391b4a24fe0890e9": "04fc2d52c10f340a98a5184c352e9cd6ab2e779d",
        "afac75c2d5e4e494335bbc48f18cbf8a9a3e17a3": "a5e87e7f4539436f64628bedea087a02b198f40f",
        "c24bcfa3fb9da644d31689ae4d16f2745f240227": "0744fd9e1969f2f6001b95c52bf4a980d4b7223b",
        "67219c2d7f5b88e3c20f148fbfab7c9bba3f087c": "68d49f0a19d5ef2bd4d3c772a2b7caeb9ba9e8a9",
        "100be854211d10cb02b96e8f0059e1d924fa09c3": "f54d37d854efbb377e915d21780f3422059c1a8a",
        "0837393bd5c8c3c48f5681dea1ac1dba76a6d6c8": "33fef214ac58418a9778851ff08769fe45d22e60",
        "dab56d88cbbe166575546fff3346feb4727afbf4": "c9c1ab05488df66de87c7b5f14e36f34c9452a06",
        "94c61421e27d837e28b7331690305a72baad4d93": "99d70d203eb482eb1747b15b1bfc79ccb3302cb8",
        "65cffbdeed0bf25fe1bf5b840450a426e1f3b255": "69db10d6012453532201640c652fa9ff66a60240",
        "4ee2d58ce739af8e91d78794d6859b4662f8cb86": "6de36772e5143943cd6cb78672bab6507c54a326",
        "301c0bda4d9e5d81320361ea5ca24ab5a8cffcd2": "a5604ef1859adc790744d9743bf88046e1690e74",
        "aa6c39c16c8229d322869a70e7be7a71e1237d5b": "59cef88c8a6f8a5cc5501e8956fa82354ed29cb1",
        "69e90bc940df1cfefcd9e3f6d0d7b5a5d7984413": "e2df7b684e2c59c36b2808f3a54a068092d0052a",
        "945a4a0a9c4b535fa509f1ffed992d41632ddab7": "72f19137323e0107754a956c1db3a97fb2108330",
        "08f3042aecf16bf086d5463c55c1c9a150603d0f": "eca369629eca554e10e47b59dc856aea0f088118",
        "d2e93fb0fa67548d2ae500f1bde6c19c941ecb7a": "047f2bac6232529939df7d39d9dc277275efa95a",
        "b57ce2770c82aef425bc34e2fed2492f63adfe4d": "aa6507b08000e0adb240496e5ce12629edddda66",
        "95089b809f5eb4d3621eaddec92638e8c82f7fa4": "932de326214bb5577984b70aa14034a8454ce36a",
        "3260a2ecf296b08d923e2cfe1205689b652cb9f1": "6b87ffc686c700c0d0bb3b77ca1e1d97dbfd1ccd",
        "1bd95def9ee03b841171924716280f6d5ccb3a09": "09f8509f6867ec3716f6096b5e1c686f32a8a2d9",
        "54f03c30bac3ebd4d1b3bb04ab2df298bc565a87": "16cca46351104437e0ec91be899a3c0d7583faae",
        "3ae8cda53774da47ad69bdb4f91ef2434acf1fb5": "17b8a3ac46e5607ed41fa867ef95212bdb2114d8",
        "695b49c4255c816f8212d2c8a17fe81daa6e4a77": "846c705822dc999ae91ba3cc8969c726ccf7b878",
        "e7137658964ed0ed011be58939a71519fb543b9a": "30da2608fdefa47c293ddaf34d137d566b64b6a9",
        "ab5fa3bd3d8e4e2a90b43379d40760203c7520da": "bdf139bdb2e8b2ab38f24a3bde41955ba4d4af99",
        "9ff0457f18f3d06771f450a665f75c454dae2f61": "5f77432e5f9479c678c56b1a4aee4a732bed2743",
        "f48a197733474dd1b12400eec775a88e9f89828f": "4bcd14a3fd3360675fba3cc89e8ae1fcf89a1f06",
        "230caf1fd48d5f03c9dbdab77178a12c6738a65e": "236d745e425c15964100fe3c7cb5f9d1dbbfb45d",
        "b6d141e0398d673ad115f76c67a86fa3908e3395": "7d1a7feb9ff0cc10e6d4d1140eb5bc1004a47dc0",
        "beb364e21f1942527a1321684d37ae07acfc5191": "91c5ff3e873e9a38b1fbb1b86659196d75d55eba",
        "5842c124617c80cf26cc4efe5a9e53f968661d38": "b79656fc83bb6e7d6c54872895d9e341c115261c",
        "10432c439e6c591685634a3a42d341aaa419e87c": "028d86b20b67cb5ed277d7f2691419acdccccd1a",
        "5fb4bec2cda9b8307a115b18d97f91cc8f095730": "3523faf7f107e1f2a456113e8eb909e17e4e573c",
        "72810dae5e9dc201060381b134eadccd209c347c": "f34c812ab0f2df852a8a2cb5634be5a6fb686d03",
        "616154a4bd8f224d0d881c9bc38cea3ffaabd3b8": "d654e7f4b01e4da891fdd0072d542094eff1a1c8",
        "cc1c05ca9dd3597690c0d2adc3f97ef2e5f32543": "2fb8385e71a043f97e4f24e951344a1cd0d9ed5b",
        "65fc254db8d34830d01329b39658a711af792286": "780c29dfc4dc7218ce7398aa1aca3ae4ec535e88",
        "85b37ea44ef1ca0d8c3c001ee4186aa42bd051d5": "dd2e63db9da538a726f3267f6748daa448d19ac6",
        "ea322a8365ee7190757a7389c8538971e467b9a6": "1729ab835d101818e43b84e416a35ea6b21f711d",
        "114aafbd10411faa65d0194775fd93f4a358fc21": "272d60fe8210f937b2afbf9f3fbfff81aec80f84",
        "a6c0444213541f747a85bd7936b1f5046ca0023f": "0b7804a02bb0dd66a68024393ca57dd28ea40422",
        "3c0eec8055735d537ca4cc59c57961ddc049caf5": "38b41d0ffcf0a19be007c73db0074fda1bb5f72f",
        "1c35f384381a9ef52e3d8055186f3e30f7495bde": "d60f1513d0e8c4c970fd3388281ce45e87677509",
        "6693426e3aca6318b7305a001205c14f216d9658": "a190fb97ce8ef393ea7382a3357add0ff0d69fa0",
        "5fa1a189b96500929514986a86d2926fe2ff9f5c": "b60660342a0b3281a3676cb0535e46f3b511ad06",
        "694561edac085c49be40022a574d9e6481bb5448": "1c2995e7f2dc443346a5d5954dd4591d6bac4364",
        "61637939907bcc513b7869936144ad083e712856": "7021afa88dfa3dd4bf24a64c24122d929428ea3d",
        "b6d4bdf90dbce6fe685a09a578e064a77f6293c7": "053aefb96fb98bcfd1a31c39a25dd9d860126ea8",
        "aea632e0144cb4721a6469300fbdfda7d8d2f3eb": "f6e45be6aee7ea690d3ff536f273d05880f121d3",
        "0ca719fa2b0c93e5cd77ec2e181f588bef34bc65": "e584e7e4f8881d4cdd1f34c03dc2fbf92e6dd085",
        "aaf3aaed779d10df89128073a9a3b304a69422a6": "c28aaac0917fa6c4a88fc6bc83861a37b48232e3",
        "80f4972be4e5bf4a16247a8393ccbf0420bfd96c": "9a323105726ff49d20732c8ee2c0e669209eb3c0",
        "eedfedbd8513a047ba393d48287c37dd196566cd": "8f1964a7ffb664843e9b6ca0c13ae14ea57d1859",
        "b322c48fce30b49df1d49bfae041535bd60bb307": "4228c4679f84924ee72513f832858e5bd55a1e24",
        "43ccd9f0ad4d9563ed7a2cd9a4d36a29322ee48c": "0dd1d59f2079ae2fb9a85cce2050c873cf4eaffd",
        "1bf7529e72295266f92beb180ae602ec9a954db4": "8f4723a5cf7a494bdfcd1fbe1b005f150e494bab",
        "224bac056b368bf4edf3f0575de187d40d4edb76": "a9f6f46a9b2cd2a92c7c4afe1bb429258ed62678",
        "6a593a4466bf9b98220dfc0139239ae5d52c5437": "795303c86a90d8bd30d42f0c900788bbad0c77f6",
        "8aeb5a99bc36d5a01a1cd409bb24d8bed990ab05": "f1de8a6ad42394726eb0a7d617db8e80ed10e40d",
        "829c7964df4ea7dd6e16cb666e139561d920f737": "f6cb7671445a96aea4219339c82687249bf6c55b",
        "f1e8c0b32320e6c08dd662b9e5f5d1ac71808226": "7693cb0d757bb0baafa21aad2a48cc92be073879",
        "a12ddefce7725faeeb98495ceb8ccb8cf3cd5f8f": "5fa9abbd9d0e4e2fbed2650ac8dd62234119c6ba",
        "001fea6ade91e82ec360e5bb2197f130680d6d6a": "9299ef59b76b8c3ee6abe4b3516ba2b2276990ae",
        "a06bccfd645add1c7d06063f5abfa8e1ba525c04": "e3eb80698a9cbd31714458536af1661e031a991f",
        "a520a7e9c054b25f02dfb2d0887bca127cb871ef": "6b36e1a7cb541b189ecbc4b3b8b9365de121afd5",
        "21bf94d43f07fcf66b37a6be82fb16b1099adaff": "41761e9e75201826aee403115b2cf21af83a92d2",
        "76b7356cbc63eae67ff7e73a66fc655ce1896b6d": "8a524572a69a0a56fd51f2780c32f5c92ab1fd06",
        "d1b05d1e94eed35bc6d35f5f9db5d99156f4e5b5": "528675121d7a71d65d6b9f98e45ef8912197dd3e",
        "72b6186f2d1248a332d580b7727e6161a930ca09": "8a681ff7cf8b4eadae1b34669c5a20e738a98d2c",
        "c9e6af612c60b047ed43de57d2465fe18b8df7cf": "198530ee8ee07677aa9e333be71cf810b6b0c3e1",
        "285b0c8646cfc8d7331ca63758c4d34161460bac": "0ad54c8c7c65c7ada3c8457c30a3306ee6006abf",
        "64fe70db980b3f60dd9fce1175a13f0ce3435b52": "afb8e76b784a95cc622b587eb63007e4453d4c1b",
        "2493221582e7a41528c53546bed61180035fec4e": "13bd6cedd6714433f1f0acdcb27296b8021a5d55",
        "2c0ff436b2798f6c028b504b56d15a158794aa40": "c0cd9e97a5acb5a9b3f94ce5ec018394140df70e",
        "8f2137659278d52c71825939501b7aad466edc3e": "a799aa9226d5590cd66cb2b618f70ef0b49ba31c",
        "b162bfe9925eba2e1a11a4bee4acad1218a62876": "39d9eafd427685b0d2355a3c4db8d157ec550d61",
        "993a5e9ae75aa37f92527cc99d2d26bdcae54dfb": "1d716467679132d3d0f10bd0c1c9f3b48e3cc103",
        "d1b965f49a76649392576551be724c0ee642d809": "854d53d140855be6a4c15a0e385d233707c777b8",
        "ef32954266481977a0c9c5eef2ff52f637fa45bb": "20ae0ca419b04a37e11ff4f6fe4341da7fde5658",
        "3a1bbc0ffb3e3b8b4472997fb2f45e05908ee5de": "d310d65e0eea0fe9bf7615749da81df14ab72d73",
        "5a0460f5a51a239ed0a9d9db806cb8bae88f645d": "195091341c22be3aef98b71a962c67ae6a0bfeac",
        "1f2e5c4d2a5243d850b855969474786e281d08d2": "7336993a5473b3617629aefabd9ea6ffec67c444",
        "a64bcf8c38473234474aca49b4013ed3617e0dec": "daa7a14f82668be14a54bc5360dd6846f272506a",
        "dc460d59824f532705781f8df8e72d951ebbd446": "dab560a49f46024bf2a4b63b4a9c8ed855ddb11a",
        "95313ec1089b64f884abe3106eb2996ff74a5f90": "dadbea07be796c3c32b9976d022b4db6013c8215",
        "9b2333d972bca1fd03814d58fcc7ae9f4834820e": "d602aea3551da2de430f3107a017f7d0c3bce597",
        "fb8384b5673beeeed268ee38fa021421ac51061f": "7fedb2712c826361f81e47bc91397b39c3f34f4a",
        "6e2212b52d96463d74d17e90e260e372eee7aa80": "868c0f0a999454750f3fbe28c97559bae259fd94",
        "c2063ba7d1a8acc7596fff3bbde994e9de9bb4be": "7ea4a35cd38ce8917571be3aec0cbce25e2cdabf",
        "6bcf1cb61b190766a459334ee462fb74f978e5f2": "107aaa858bc41ac5dde7e5a4f12753ef706c5c6e",
        "506bcfd7c74cf131029abeba02a3e37e793dd8c7": "3a0d7f330c7de8cfe55a82c41aa75324afc3376e",
        "fc4894a72071fcabf7ad7363d5783f6c0d0bf609": "573a93f12f75abe89c3717d5218e3fd990673336",
        "4915afc7bebe87da64c5eeb64843a24727a887dd": "583222478d661bdf71dd577c3481ce98a718f45e",
        "04f219188c2c187e5bda6e462d871e5a9ff0b841": "f2076f9e0aa167d25439251a4c3ba61be166e7f2",
        "8b0b3b8b8622bb00f72b411ae324446ccaf22935": "33857a76c812e389a6ffed2f735a3a40a5b8630e",
        "11bdd31265db39c90a67b92c923e97bd9960968c": "16f2dc070f4d2bd764d312dccbdc8db71951ea44",
        "683af96eb36362e89c0e0faecfa49cd9e6ab8059": "5a4bc4ad9d0def0c8aad25f7a4db82c2aba09504",
        "8d14c398fd604733cfcc05d4dcd1d612ee53a921": "5626b00cc5d3be56be5905c633977f2594f8cbaf",
        "4df98ff0a70343fca54c12146303ac84e0337546": "f72a9553af69dc4f600dacd664b19b3e44c9935a",
        "f8e15a9c11ed569facf06edce7ca1b77c9c1fd3d": "19ff8d77cf82cc7424ba8f2b1da90a10b15e04c3",
        "f9856b407eebd3533ea4687089849887c769240b": "e30487c99edb021e189d973a84c6285bea032be1",
        "7ea2306eee8d69671336252a2018697b98f46112": "62d0f29046caf5346ec5c26e1531d60ed6a89265",
        "aca5aba40ab556d32a2ae9aec25c2fbd6f783f00": "f8c74d5c7c07a9e1eb7a4d2a41c76cac38f5a9d3",
        "518176771ae50589313b7dc5955fe118f9f2c0d1": "36a676e02b79ccfe12f9d0dd55beeea16b6d64ff",
        "1c1f244beddb9e1620830a352e6b4c0adb9424f9": "55859e6bccf14afec48b17a5354729da229f68b6",
        "0e5f7b03f26bae7f950e9293d632b6bd7b80d280": "54bf93fb13947af1c95180a08cb86b820723476e",
        "ee53db178e3bb04fb41792602d5d47e68b3f0b21": "c4ff9b197aa3c10a2387bee35457982d499f4cdd",
        "727d6de6ab259ce3103f5f244985fb1632e1202b": "65e92fa5deaf52b8e5053b56e7a5c326ad8276bc",
        "b3f8efa1d434a1d5d1568302f83ed18d4e33e9f1": "6de98fe0c6f9926c1a5540442ad6a76072cf7a11",
        "69c1c7adda95aaa854f311011a50552d3036ebd8": "3d10f01a90ad2cdc4a67da4dca91e8434fe361d4",
        "f5a1d9b7e439084203d901bfddd4371d2fe33718": "471a191c4c9e113ca6e1416f910ef12092a0d696",
        "e964a6879a29531bcad73ac219225fb065ee2d81": "b70b8ad6e7613cf651f9361b16b2985a995e9f4f",
        "cf2237b8d710536a5c75ce1e36b62eeccb2e6c53": "160e4b16bd1af1538ab9e20b0a46882d62e97545",
        "535e1ee030ff343554f5c8b194f3b869a00b6894": "1a892ee0dc61931c24a92396d2d41c249cb638ea",
        "3411fc67c3c5bce5947fb5561c43ea44bb53e377": "60e8107ba9818aa9236f26625604024098319162",
        "34c62dbcf8d5b1ffedc4931b447fd52077866625": "95bb316622368b88ab46f73a038c158deac92d90",
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
