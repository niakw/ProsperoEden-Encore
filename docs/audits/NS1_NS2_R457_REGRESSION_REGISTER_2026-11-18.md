# PS5 R457 — registre FC27 et NS2, suivi du lot correctif (18 novembre 2026)

**Moteur et vendor concernés :** [moteur](https://github.com/niakw/ProsperoEden-Encore), [vendor](https://github.com/niakw/Prospero.Eden-Encore-vendor).

**Build PS5 testé :** R457, moteur `e8493417f914783069e09d7f8fae19b5fd4049fe`, vendor `edcc311c09eed3a33e5acc373c63a436f662cb5b`, archive de logs utilisateur `17112259.zip`. Pas de backtrace native terminale FC27 dans cette archive.

**Lot source candidat :** vendor `49070af1bfee1ef67ed8037221345baf71d02373`, successeur du lot `ec3757b3f17d974577b304faa0d54279e01d0a5a`, incluant le service de polices NS2, Lichii #1199 pour les remaps GPU, #2085 pour I2M et l'adaptation de la PR Lichii #2121 pour les blits 2D en tiling natif. Encore ajoute l'activation du layout uniquement après authentification du canal GPU NS2 afin de conserver le layout Maxwell par défaut pour NS1. **Pas encore de build PS5 ni de validation console de ce candidat.**

| Priorité | Symptôme / jeu | Logs R457 | Cause candidate / modification | Amont | Validation restante |
|---|---|---|---|---|---|
| P0 | FC27 NS1 crash avant mi-temps | Capture stderr terminée à 500 lignes; crash utilisateur; aucune signature native terminale | Teardown pipeline asynchrone ou autre faute native; `workers.WaitForRequests()` avant destruction | Lichii `499e2e4`; Eden Issue-Reports #771, autre contexte | Liaison native + crash ELF, console |
| P1 | FC27 HUD/pause tardifs et saccades | 14 Options publiés; attente pipeline 2,014 s / frame 2,036 s; contention buffer | `RunBuild()` prioritaire à la première utilisation, fastpath buffer, diagnostic `EDEN_NVHOST_STALL` | Lichii `f8f29b5`, `44bf47d` | Host, puis une session FC27 jusqu'à mi-temps ; mesurer HUD/Options |
| P0 | MKW NS2 `0400C3F00006E000` `PC=0x4` | `ns2/stderr.log` SP sous la pile initiale; initialisation guest atteinte | Contrats IPC/SVC/GPU/Host1x, ordre démarrage threads, syncpt shim; suppression des alias 216 vers mémoire détruite et restauration du backing dense 214 | Lichii `NX2_NOTES.md` #42-48; Lichii #1199; Eglantine #74 | Host #1199, compile PS5, première guest frame |
| P0 | Bananza NS2 `040074A01BF12000` `PC=0x4` | Même signature PC/LR, SP distinct | Runtime NS2 ou cohérence base/update | Eglantine #350, cas où contenu non conforme | Pas de cause certaine ; ne tester que si MKW ne discrimine pas |
| P1 | Shader prewarm absent | `queued=0 completed=0` | Inventaire pipelines non prêt; first-use attendait ses workers | Lichii cache/prewarm | Mesures cold/warm sans conclure à correction complète |

## Qualification sans multiplier les tests console

1. Rejouer les anciens tests vendor et les 13 tests spécifiques du lot nouveau depuis le moteur, avec contrôle du SHA gitlink exact.
2. Examiner les gates moteur, les nouveaux symboles/ABI et la compilation native avant **tout** déploiement PS5.
3. Réserver **une** validation console groupée : FC27 froid puis chaud, pause/HUD, stabilité jusqu'à mi-temps, sortie normale ; MKW NS2 jusqu'au premier rendu réel. Bananza seulement si un second diagnostic est nécessaire.
4. Ne jamais classer le problème corrigé sur la base de la CI seule. Ne pas confondre la cause du crash FC27 avec les retards de pause sans pile native.

Références : [Lot vendor candidat](https://github.com/niakw/Prospero.Eden-Encore-vendor/compare/edcc311c09eed3a33e5acc373c63a436f662cb5b...3b3a26afd70fbfbfb706e5b9964e3303c07a944c), [Lichii #1199](https://github.com/zortos293/Lichii/pull/1199), [Lichii #2085](https://github.com/zortos293/Lichii/pull/2085), [Lichii #2042](https://github.com/zortos293/Lichii/issues/2042), [Lichii #2121](https://github.com/zortos293/Lichii/pull/2121), [Lichii NX2_NOTES](https://github.com/zortos293/Lichii/blob/nx2/NX2_NOTES.md), [Eglantine #350](https://github.com/Eglantine-Community/Eglantine/issues/350), [Eglantine #74](https://github.com/Djihads80/Eglantine/issues/74), [Eden Issue-Reports #771](https://github.com/eden-emulator/Issue-Reports/issues/771).

## Source provenance follow-up

- The immutable pinned Eden original `sources/eden/src/core/device_memory_manager.h` was restored from vendor `edcc311c09eed3a33e5acc373c63a436f662cb5b`. The PS5-only 34-bit SMMU successor remains in `encore-active/eden-backports/`.
- Updated shipping SHA256 and byte sizes for exactly three changed maintained source files, plus a byte-reversing review fixture: `tools/fixtures/ns2-memory-service-backports-reverse.json`.
- Host tests remain to be rerun; this is not native PS5/FC27/MKW qualification.

- Host CI R457 successor: requalified exact pipeline-drain source against the R23 diagnostic admission oracle; updated bounded SVC fatal-ring and maintained GPFIFO owner checks without relaxing source contracts.

- Host1x qualification updated for the numeric `u64` action-handle implementation: pending cancellation, running cancellation, waiter publication, same-id progress and 256-action stress are exercised at O0/O2 before any console build.

- Vendor `ec3757b3f17d974577b304faa0d54279e01d0a5a`: snapshot Eden `sources/eden/src/video_core/memory_manager.h` restauré immuable; déclarations NVN syncpoint shim déplacées vers `encore-active/eden-core/guest-bridge/memory_manager.h`, propriétaire réellement sélectionné par le build PS5. Le contrôle M04 reconstruit désormais byte-for-byte la composition deferred bridge + shim NS2.

## Detailed-log successor ab388160

- Shipping NPad now emits bounded `EDEN_NPAD_PLUS_LIFO` only while Detailed Logging is enabled; each rising Plus edge carries the guest LIFO sample number and monotonic timestamp.
- Quiet mode performs no NPad diagnostic counters or clock reads. Mapping, sampling cadence and LIFO writes are unchanged.
- Vendor regression reverses the diagnostic byte-for-byte to previous NPad blob `454138c445bc140568068737646349cac98a686d`.

## NS2 built-in font service — upstream blocker #36

- Lichii `NX2_NOTES.md` records blocker #36 as a built-in-font header check on a wild pointer when `pl:u` command 2010/2000 is absent.
- The maintained overlay preserves legacy NS1 commands 0–6 and adds NS2 commands 2000/2010/2020/2100 plus `font_merge.cpp`.
- Release CMake replaces the single Eden `platform_service_manager.cpp` owner and adds the merge TU; the four files remain post-F07 and do not alter historical audit counts.
- Source/host qualification only until a native PS5 build and NS2 launch.


## NS2 native tiling — upstream #2042 / PR #2121

- Le premier backport Lichii #2085/commit `7702ac4` couvre les écritures I2M, mais le retour de test upstream #2042 indique que les bandes sombres persistaient.
- L'analyse upstream a ensuite identifié le blitter logiciel Fermi2D comme second écrivain restant en layout Switch 1 ; la PR Lichii #2121 transmet `UsesNativeTiling()` aux chemins `UnswizzleSubrect` et `SwizzleSubrect`.
- Vendor Encore `49070af1bfee1ef67ed8037221345baf71d02373` porte ces deux appels, ajoute le flag `MemoryManager` par défaut à `false` et ne l'active qu'après `NativeGpuChannelRegistry::Bind` réussi pour un canal NS2 prêt.
- Le moteur sélectionne le même header `MemoryManager` pour `core` et `video_core`, plus un seul owner I2M et un seul owner software-blitter. NS1 reste sur le layout Maxwell tant qu'aucun canal natif NS2 n'est authentifié.
- Qualification source/host uniquement à ce stade ; ni la disparition des bandes dans DKB/Bananza, ni le premier rendu MKW, ni les crashs `PC=0x4` ne sont déclarés corrigés avant test PS5.
