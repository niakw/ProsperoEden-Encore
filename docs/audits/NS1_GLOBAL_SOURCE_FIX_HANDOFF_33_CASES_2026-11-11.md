# NS1/global — matrice corrective et relais de branches (11 nov. 2026)

**Ce document est un instantané des corrections préparées, PAS la clôture E3/E4 sur console.** L'audit source général a classifié 155/155 changements amont (E1), mais la liste historique des 33 cas a des situations différentes: code déjà installé, PR draft, refactor/no-port motivé, sémantique encore ouverte. Un groupe de PR toutes vertes en host **ne prouve ni compilation native complète ni FC27 démarrant sur PS5**.

## Registre des 33 cas (E1 et état du port)

| Cas | Référent technique | État source | PR candidates | Bloquant matériel/sémantique |
|---|---|---|---|---|
| #1 | FW23.5 NS qlaunch 3250–3262 | source candidate (stubs) | V#65 + E#67 (V#60 duplicate byte-identique) | IPC FW23.5/events PS5 |
| #119 | FW23 stpl:u / stpl:sys | source candidate; guest save slot returns NotSupported | V#66 + E#68 | IPC FW22 vs FW23, handles/saves |
| #120 | SSL Peek/Poll/renegotiation | source candidate, host sanitizer green | V#64 + E#66 | native OpenSSL, guest IPC handshake |
| #126 | LDN pseudo-device UUID | partial source fix SHA1 buffer | V#53 | common/uuid API pair, LDN game |
| #153 | Opus 24 concurrent decoders | source candidate, host quota sanitizer green | V#50 + E#59 | native decoder ABI, 25th guest |
| #154 | FW23 selected AM SelfController 240 | source candidate, source parity green | V#51 | native selected owner and FW23 guest |
| #2 | EDS3 DepthClip + async side-effect shader | OPEN coherent GPU graph | — | 9 shader/Vulkan owners; RADV depth/async GPU proof |
| #18 | TIR mixed MSAA raster/depth | OPEN coherent GPU graph | — | 5 files, NS2 ASTC selected header, GPU scratch/resolve |
| #35 | Texture handles from vertex attributes | OPEN coherent shader/Vulkan graph | — | shader handles, descriptors, rasterizer and draw order |
| #49 | Invalid Vulkan texel format 255 | source candidate, header+fixture green | V#56 + E#72 | real PS5 descriptor buffer/legacy image test |
| #58 | Conditional Phi bindless handles | source candidate, C++ CFG sanitizer green | V#68 + E#70 | shared shader native link + SPIR-V + NS2 smoke |
| #64 | GPU/threading historical refactor | DEFER due ownership/race interactions | — | native fence proof; no mass refactor without evidence |
| #72 | Missing subgroup on Qualcomm Turnip | NO-PORT for PS5 RDNA2, device gate | — | verify RADV capability; no Turnip-specific workaround |
| #80 | Skip broken shaders on non-NVIDIA | NO-PORT of blanket skip on PS5 RADV | — | would drop draws/black screen; IR golden/driver proof |
| #144 | Android LSFG UI | NO-PORT Android-only UI on PS5 native | — | separate native LSFG mode matrix handled by renderer integration |
| #10 | A32 debugger memory-access halt | source candidate, guard host green | V#63 | actual GDB watchpoint/A32 guest |
| #11 | Dynarmic A32 SHA1 & x64 seven correctness fixes | multiple source candidates, source host green | V#47/#57/#58 + E#61/#62 | merge non-overlap in vector TU, PS5 native JIT golden |
| #17 | PageTable sign bit 55 | source candidate | V#47 | native page-table includes, mapped/unmapped tests |
| #32 | Dynarmic A64 WFE/WFI hints config | DEFER ABI scheduler policy | — | native HLE scheduler hint/wakeup trace |
| #33 | x64 ConstantPool dedup upstream refactor | NO-PORT W^X risk | — | maintained writableAddress alias must not regress |
| #41 | Dynarmic CMake cleanup / 128-bit exclusives | DEFER broad upstream CMake | — | Zen2 CMPXCHG16B+W^X golden |
| #114 | RDTSC nanoseconds 1–4 GHz | source candidate, host sanitizer green | V#52 + E#73 | real CPU clock and PS5 native link |
| #136 | A32 page-table sign extension x64 | NO-PORT incompatible shift-count patch | V#47 explicitly excludes | G11 ABI uses count not index; native JIT test |
| #19 | Controller assignment/gyro/Steam UI | PARTIAL: PS5 guest semantics only | V#67 + E#69 for #95 separate | DualSense gyro/orientation and game applets |
| #84 | None frontend applet | source candidate | E#55 | native 3-TU syntax green, guest IPC lifecycle |
| #95 | HID stale connected state | source candidate, test host green | V#67 + E#69 | DualSense reconnect gyro and NPad |
| #97 | Applet overlay z-order + SGSR black screen | source candidate, host tests green | V#69 + E#71 | all PS5 AA/upscale/neural/FG combinations |
| #46 | Cheat master toggle and parser | PARTIAL: safe parser; not full runtime toggles | V#55 + E#60 | cheat master/toggle VM guest/thread/memory |
| #103 | Sparse zero-page/decommit | ALREADY selected native source partly covers E1 | — | page/T size, free/recommit memory pressure PS5 |
| #113 | Bundled-program parent resources | source candidate, host green | V#59 + E#63 (V#61/E#64 overlap) | save/title mod isolation and user consent |
| #152 | Temp save cleanup per app | source candidate, host green | V#54 | paired #113 savedata TU; guest savedata |
| #48 | VP9 segmentation probabilities | source candidate, host bitstream sanitizer green | V#62 + E#65 | real NVDEC/FFmpeg movie and guest frame order |
| #54 | NVDEC/HLE freeze read pacing | DEFER upstream sleeps/global bool | — | upstream global boolean loses multi-session semantics; guest video and scheduler tracing |

**Ne pas transformer « source candidate » en « correctif livré PS5 ».** Le registre frozen historise des écarts de *qualification* : les décisions no-port ciblées ne constituent pas un échec de portage si leur exclusion x64/RDNA2/PS5 est attestée, mais la preuve E4 de non-régression reste distincte. Les cas #2/#18/#35/#19/#46/#54 et la qualification des autres ne sont pas entièrement résolus. E1 ≠ E2 ≠ E3 ≠ E4.

## Liste exhaustive de transmission des branches de recherche

Les PR sont **indépendantes** et **non fusionnées** dans le cadre de cet audit. Une branche contenant un gitlink expérimental ne peut être fusionnée telle quelle dans le vendor de production; le responsable intégration reprend les vrais fichiers maintenus + CMake à la SHA cible.

### Moteur — niakw/ProsperoEden-Encore

| PR | Branche |
|---|---|
| [#45](https://github.com/niakw/ProsperoEden-Encore/pull/45) | [`audit/ab-ns1-upstream-2026-11-10`](https://github.com/niakw/ProsperoEden-Encore/tree/audit/ab-ns1-upstream-2026-11-10) |
| [#46](https://github.com/niakw/ProsperoEden-Encore/pull/46) | [`dev/ab-ns1-corrective-batches-2026-11-10`](https://github.com/niakw/ProsperoEden-Encore/tree/dev/ab-ns1-corrective-batches-2026-11-10) |
| [#52](https://github.com/niakw/ProsperoEden-Encore/pull/52) | [`integration/r457-ns1-abi-launcher-20261111`](https://github.com/niakw/ProsperoEden-Encore/tree/integration/r457-ns1-abi-launcher-20261111) |
| [#55](https://github.com/niakw/ProsperoEden-Encore/pull/55) | [`research/ns1-am-applets-mainline-20261111`](https://github.com/niakw/ProsperoEden-Encore/tree/research/ns1-am-applets-mainline-20261111) |
| [#58](https://github.com/niakw/ProsperoEden-Encore/pull/58) | [`research/ns1-c03-radv-native-selected-20261111`](https://github.com/niakw/ProsperoEden-Encore/tree/research/ns1-c03-radv-native-selected-20261111) |
| [#59](https://github.com/niakw/ProsperoEden-Encore/pull/59) | [`research/ns1-r23-opus-native-owner-20261111`](https://github.com/niakw/ProsperoEden-Encore/tree/research/ns1-r23-opus-native-owner-20261111) |
| [#60](https://github.com/niakw/ProsperoEden-Encore/pull/60) | [`research/ns1-r23-cheat-parser-native-20261111`](https://github.com/niakw/ProsperoEden-Encore/tree/research/ns1-r23-cheat-parser-native-20261111) |
| [#61](https://github.com/niakw/ProsperoEden-Encore/pull/61) | [`research/ns1-r23-jit-x64-native-20261111`](https://github.com/niakw/ProsperoEden-Encore/tree/research/ns1-r23-jit-x64-native-20261111) |
| [#62](https://github.com/niakw/ProsperoEden-Encore/pull/62) | [`research/ns1-r23-a32-sha1-native-20261111`](https://github.com/niakw/ProsperoEden-Encore/tree/research/ns1-r23-a32-sha1-native-20261111) |
| [#63](https://github.com/niakw/ProsperoEden-Encore/pull/63) | [`research/ns1-r23-parent-program-native-20261111`](https://github.com/niakw/ProsperoEden-Encore/tree/research/ns1-r23-parent-program-native-20261111) |
| [#64](https://github.com/niakw/ProsperoEden-Encore/pull/64) | [`research/ns1-r23-bundled-parent-fs-native-20261111`](https://github.com/niakw/ProsperoEden-Encore/tree/research/ns1-r23-bundled-parent-fs-native-20261111) |
| [#65](https://github.com/niakw/ProsperoEden-Encore/pull/65) | [`research/ns1-r23-vp9-native-20261111`](https://github.com/niakw/ProsperoEden-Encore/tree/research/ns1-r23-vp9-native-20261111) |
| [#66](https://github.com/niakw/ProsperoEden-Encore/pull/66) | [`research/ns1-r23-ssl-native-20261111`](https://github.com/niakw/ProsperoEden-Encore/tree/research/ns1-r23-ssl-native-20261111) |
| [#67](https://github.com/niakw/ProsperoEden-Encore/pull/67) | [`research/ns1-r23-fw235-qlaunch-native-20261111`](https://github.com/niakw/ProsperoEden-Encore/tree/research/ns1-r23-fw235-qlaunch-native-20261111) |
| [#68](https://github.com/niakw/ProsperoEden-Encore/pull/68) | [`research/ns1-r23-stpl-hos23-native-20261111`](https://github.com/niakw/ProsperoEden-Encore/tree/research/ns1-r23-stpl-hos23-native-20261111) |
| [#69](https://github.com/niakw/ProsperoEden-Encore/pull/69) | [`research/ns1-r23-hid95-native-20261111`](https://github.com/niakw/ProsperoEden-Encore/tree/research/ns1-r23-hid95-native-20261111) |
| [#70](https://github.com/niakw/ProsperoEden-Encore/pull/70) | [`research/ns1-r23-bindless-phi-native-20261111`](https://github.com/niakw/ProsperoEden-Encore/tree/research/ns1-r23-bindless-phi-native-20261111) |
| [#71](https://github.com/niakw/ProsperoEden-Encore/pull/71) | [`research/ns1-r23-applet-sgsr-overlay-20261111`](https://github.com/niakw/ProsperoEden-Encore/tree/research/ns1-r23-applet-sgsr-overlay-20261111) |
| [#72](https://github.com/niakw/ProsperoEden-Encore/pull/72) | [`research/ns1-r23-vk-texel-native-20261111`](https://github.com/niakw/ProsperoEden-Encore/tree/research/ns1-r23-vk-texel-native-20261111) |
| [#73](https://github.com/niakw/ProsperoEden-Encore/pull/73) | [`research/ns1-r23-rdtsc-native-20261111`](https://github.com/niakw/ProsperoEden-Encore/tree/research/ns1-r23-rdtsc-native-20261111) |

### Vendor — niakw/Prospero.Eden-Encore-vendor

| PR | Branche |
|---|---|
| [#46](https://github.com/niakw/Prospero.Eden-Encore-vendor/pull/46) | [`research/ns1-c03-radv-transfer-barrier-20261111`](https://github.com/niakw/Prospero.Eden-Encore-vendor/tree/research/ns1-c03-radv-transfer-barrier-20261111) |
| [#47](https://github.com/niakw/Prospero.Eden-Encore-vendor/pull/47) | [`research/ns1-c04-jit-page-sign-20261111`](https://github.com/niakw/Prospero.Eden-Encore-vendor/tree/research/ns1-c04-jit-page-sign-20261111) |
| [#48](https://github.com/niakw/Prospero.Eden-Encore-vendor/pull/48) | [`research/ns1-c01-romfs-lifetime-20261111`](https://github.com/niakw/Prospero.Eden-Encore-vendor/tree/research/ns1-c01-romfs-lifetime-20261111) |
| [#49](https://github.com/niakw/Prospero.Eden-Encore-vendor/pull/49) | [`research/ns1-c02-shared-spirv-nan-20261111`](https://github.com/niakw/Prospero.Eden-Encore-vendor/tree/research/ns1-c02-shared-spirv-nan-20261111) |
| [#50](https://github.com/niakw/Prospero.Eden-Encore-vendor/pull/50) | [`research/ns1-r23-opus-24-instances-20261111`](https://github.com/niakw/Prospero.Eden-Encore-vendor/tree/research/ns1-r23-opus-24-instances-20261111) |
| [#51](https://github.com/niakw/Prospero.Eden-Encore-vendor/pull/51) | [`research/r23-fw23-selfcontroller-240-20261111`](https://github.com/niakw/Prospero.Eden-Encore-vendor/tree/research/r23-fw23-selfcontroller-240-20261111) |
| [#52](https://github.com/niakw/Prospero.Eden-Encore-vendor/pull/52) | [`research/ns1-r23-rdtsc-ticks-20261111`](https://github.com/niakw/Prospero.Eden-Encore-vendor/tree/research/ns1-r23-rdtsc-ticks-20261111) |
| [#53](https://github.com/niakw/Prospero.Eden-Encore-vendor/pull/53) | [`research/ns1-r23-ldn-pseudodevice-uuid-20261111`](https://github.com/niakw/Prospero.Eden-Encore-vendor/tree/research/ns1-r23-ldn-pseudodevice-uuid-20261111) |
| [#54](https://github.com/niakw/Prospero.Eden-Encore-vendor/pull/54) | [`research/ns1-r23-temp-lifetime-20261111`](https://github.com/niakw/Prospero.Eden-Encore-vendor/tree/research/ns1-r23-temp-lifetime-20261111) |
| [#55](https://github.com/niakw/Prospero.Eden-Encore-vendor/pull/55) | [`research/ns1-r23-cheat-parser-bounds-20261111`](https://github.com/niakw/Prospero.Eden-Encore-vendor/tree/research/ns1-r23-cheat-parser-bounds-20261111) |
| [#56](https://github.com/niakw/Prospero.Eden-Encore-vendor/pull/56) | [`research/ns1-r23-vk-texel-format-20261111`](https://github.com/niakw/Prospero.Eden-Encore-vendor/tree/research/ns1-r23-vk-texel-format-20261111) |
| [#57](https://github.com/niakw/Prospero.Eden-Encore-vendor/pull/57) | [`research/ns1-r23-jit-x64-followups-20261111`](https://github.com/niakw/Prospero.Eden-Encore-vendor/tree/research/ns1-r23-jit-x64-followups-20261111) |
| [#58](https://github.com/niakw/Prospero.Eden-Encore-vendor/pull/58) | [`research/ns1-r23-a32-sha1-20261111`](https://github.com/niakw/Prospero.Eden-Encore-vendor/tree/research/ns1-r23-a32-sha1-20261111) |
| [#59](https://github.com/niakw/Prospero.Eden-Encore-vendor/pull/59) | [`research/ns1-r23-parent-program-resources-20261111`](https://github.com/niakw/Prospero.Eden-Encore-vendor/tree/research/ns1-r23-parent-program-resources-20261111) |
| [#60](https://github.com/niakw/Prospero.Eden-Encore-vendor/pull/60) | [`research/ns1-r23-fw235-ns-commands-20261111`](https://github.com/niakw/Prospero.Eden-Encore-vendor/tree/research/ns1-r23-fw235-ns-commands-20261111) |
| [#61](https://github.com/niakw/Prospero.Eden-Encore-vendor/pull/61) | [`research/ns1-r23-bundled-parent-fs-20261111`](https://github.com/niakw/Prospero.Eden-Encore-vendor/tree/research/ns1-r23-bundled-parent-fs-20261111) |
| [#62](https://github.com/niakw/Prospero.Eden-Encore-vendor/pull/62) | [`research/ns1-r23-vp9-segmentation-20261111`](https://github.com/niakw/Prospero.Eden-Encore-vendor/tree/research/ns1-r23-vp9-segmentation-20261111) |
| [#63](https://github.com/niakw/Prospero.Eden-Encore-vendor/pull/63) | [`research/ns1-r23-a32-debug-halt-20261111`](https://github.com/niakw/Prospero.Eden-Encore-vendor/tree/research/ns1-r23-a32-debug-halt-20261111) |
| [#64](https://github.com/niakw/Prospero.Eden-Encore-vendor/pull/64) | [`research/ns1-r23-ssl-ipc-20261111`](https://github.com/niakw/Prospero.Eden-Encore-vendor/tree/research/ns1-r23-ssl-ipc-20261111) |
| [#65](https://github.com/niakw/Prospero.Eden-Encore-vendor/pull/65) | [`research/ns1-r23-fw235-qlaunch-20261111`](https://github.com/niakw/Prospero.Eden-Encore-vendor/tree/research/ns1-r23-fw235-qlaunch-20261111) |
| [#66](https://github.com/niakw/Prospero.Eden-Encore-vendor/pull/66) | [`research/ns1-r23-stpl-hos23-20261111`](https://github.com/niakw/Prospero.Eden-Encore-vendor/tree/research/ns1-r23-stpl-hos23-20261111) |
| [#67](https://github.com/niakw/Prospero.Eden-Encore-vendor/pull/67) | [`research/ns1-r23-hid-controller-reconnect-20261111`](https://github.com/niakw/Prospero.Eden-Encore-vendor/tree/research/ns1-r23-hid-controller-reconnect-20261111) |
| [#68](https://github.com/niakw/Prospero.Eden-Encore-vendor/pull/68) | [`research/ns1-r23-bindless-phi-20261111`](https://github.com/niakw/Prospero.Eden-Encore-vendor/tree/research/ns1-r23-bindless-phi-20261111) |
| [#69](https://github.com/niakw/Prospero.Eden-Encore-vendor/pull/69) | [`research/ns1-r23-applet-overlay-zorder-20261111`](https://github.com/niakw/Prospero.Eden-Encore-vendor/tree/research/ns1-r23-applet-overlay-zorder-20261111) |

### À éviter absolument lors du merge

1. **Doubles travaux** : vendor #59 / #61 portent presque le même lot FS #113, accompagnés par moteur #63 / #64. Même code de `registered_cache.cpp` et `savedata_factory.cpp`, divergence locale de `patch_manager.cpp` ; choisir/réconcilier **une seule** implémentation, sans compiler deux propriétaires. Vendor #60 / #65 ont les mêmes blobs FW23.5 (#1) — moteur #67 pointe #65, ne pas importer #60 deux fois.
2. **Autres chevauchements** : C04 vendor #47 et vendor #57 x64 partagent `emit_x64_vector.cpp` ; préserver SDIV, saturating shift et CLZ lanes. Le `savedata_factory.cpp` de #113 (vendor #59/#61) et l'amélioration de durée de stockage temporaire (#152 vendor #54) sont deux changements non superposables par remplacement de TU entier. Vendor #49 shared SPIR-V et #68 Phi doivent s'accorder avec NS2.
3. **Correctifs déjà livrés** : #109 applet child teardown, #128 missing NS icon guard, #147 NS cmd23, et huit backports source de Pass28 ne sont pas des PR à ajouter une nouvelle fois. [Moteur #54 fermé sans merge](https://github.com/niakw/ProsperoEden-Encore/pull/54).
4. **Audit exceptionnel** : PR moteur #45 contient uniquement les preuves E1, PR #46 C00 AudioIn et révisions historiques; C01/C02/C03/C04 sont à prendre sur vendor #48/#49/#46/#47 en priorité avec leurs propres propriétaires. #52 CPU6/launcher est hors des 33 cas mais dans le même périmètre release.
5. **Native release incomplet** : les workflows de contrôle **généraux** des branches moteur de recherche échouent parfois parce qu'ils exigent le gitlink vendor exact de `main`, alors que chaque branche est justement isolée sur une révision expérimentale. Ne pas supprimer ces checks de production pour obtenir du vert artificiel. Refaire sur le vendor final recomposé.
6. **Preuves restantes** : CMake `compile_commands.json`, objets/ELF, linker SDK PS5, tous les headers externes R18, 22 hash CPM, archive SBOM licences/CVE, sign/staging ZIP unique, démarrage NS1 à cache vidé, ouverture applet, manettes/gyro, audio input/output, ROMFS/save, GPU FSR/SGSR/NR/FG/AA, et smoke NS2 sur les shaders et Vulkan partagés.

## Verdict sincère

- **Audit source E1** : classification complète et historique conservé.
- **Source correctifs E2 partiels** : nombreuses PR propres et tests hôte/sanitizer verts; quelques lots sont seulement des pré-candidats ou des non-ports justifiés.
- **E3/E4 / production** : **NON QUALIFIÉ** ; aucun test console/ELF complet de l'ensemble des branches n'est démontré. Ce document doit être remis au responsable merge/adaptation comme **liste de travail**, pas comme certificat de fin.
