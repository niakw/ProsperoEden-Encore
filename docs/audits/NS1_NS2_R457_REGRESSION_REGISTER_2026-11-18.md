# PS5 R457 — registre FC27 et NS2, suivi du lot correctif (18 novembre 2026)

**Moteur et vendor concernés :** [moteur](https://github.com/niakw/ProsperoEden-Encore), [vendor](https://github.com/niakw/Prospero.Eden-Encore-vendor).

**Build PS5 testé :** R457, moteur `e8493417f914783069e09d7f8fae19b5fd4049fe`, vendor `edcc311c09eed3a33e5acc373c63a436f662cb5b`, archive de logs utilisateur `17112259.zip`. Pas de backtrace native terminale FC27 dans cette archive.

**Lot source candidat :** vendor `3cac7130d6626dced483d038cbf034274a0463d8` (15 commits), incluant le service de polices NS2 `f43a3696`, non encore sélectionné pour la compilation par le moteur. Tests source et host vendor verts, **pas de build PS5 ni de test console de ce candidat**.

| Priorité | Symptôme / jeu | Logs R457 | Cause candidate / modification | Amont | Validation restante |
|---|---|---|---|---|---|
| P0 | FC27 NS1 crash avant mi-temps | Capture stderr terminée à 500 lignes; crash utilisateur; aucune signature native terminale | Teardown pipeline asynchrone ou autre faute native; `workers.WaitForRequests()` avant destruction | Lichii `499e2e4`; Eden Issue-Reports #771, autre contexte | Liaison native + crash ELF, console |
| P1 | FC27 HUD/pause tardifs et saccades | 14 Options publiés; attente pipeline 2,014 s / frame 2,036 s; contention buffer | `RunBuild()` prioritaire à la première utilisation, fastpath buffer, diagnostic `EDEN_NVHOST_STALL` | Lichii `f8f29b5`, `44bf47d` | Host, puis une session FC27 jusqu'à mi-temps ; mesurer HUD/Options |
| P0 | MKW NS2 `0400C3F00006E000` `PC=0x4` | `ns2/stderr.log` SP sous la pile initiale; initialisation guest atteinte | Contrats IPC/SVC/GPU/Host1x, ordre démarrage threads, syncpt shim | Lichii `NX2_NOTES.md` #42-48; Eglantine #74 | C++ source selection, compile PS5, première guest frame |
| P0 | Bananza NS2 `040074A01BF12000` `PC=0x4` | Même signature PC/LR, SP distinct | Runtime NS2 ou cohérence base/update | Eglantine #350, cas où contenu non conforme | Pas de cause certaine ; ne tester que si MKW ne discrimine pas |
| P1 | Shader prewarm absent | `queued=0 completed=0` | Inventaire pipelines non prêt; first-use attendait ses workers | Lichii cache/prewarm | Mesures cold/warm sans conclure à correction complète |

## Qualification sans multiplier les tests console

1. Rejouer les anciens tests vendor et les 13 tests spécifiques du lot nouveau depuis le moteur, avec contrôle du SHA gitlink exact.
2. Examiner les gates moteur, les nouveaux symboles/ABI et la compilation native avant **tout** déploiement PS5.
3. Réserver **une** validation console groupée : FC27 froid puis chaud, pause/HUD, stabilité jusqu'à mi-temps, sortie normale ; MKW NS2 jusqu'au premier rendu réel. Bananza seulement si un second diagnostic est nécessaire.
4. Ne jamais classer le problème corrigé sur la base de la CI seule. Ne pas confondre la cause du crash FC27 avec les retards de pause sans pile native.

Références : [Lot vendor figé](https://github.com/niakw/Prospero.Eden-Encore-vendor/compare/edcc311c09eed3a33e5acc373c63a436f662cb5b...3cac7130d6626dced483d038cbf034274a0463d8), [Lichii NX2_NOTES](https://github.com/zortos293/Lichii/blob/nx2/NX2_NOTES.md), [Eglantine #350](https://github.com/Eglantine-Community/Eglantine/issues/350), [Eglantine #74](https://github.com/Djihads80/Eglantine/issues/74), [Eden Issue-Reports #771](https://github.com/eden-emulator/Issue-Reports/issues/771).

## Source provenance follow-up

- The immutable pinned Eden original `sources/eden/src/core/device_memory_manager.h` was restored from vendor `edcc311c09eed3a33e5acc373c63a436f662cb5b`. The PS5-only 34-bit SMMU successor remains in `encore-active/eden-backports/`.
- Updated shipping SHA256 and byte sizes for exactly three changed maintained source files, plus a byte-reversing review fixture: `tools/fixtures/ns2-memory-service-backports-reverse.json`.
- Host tests remain to be rerun; this is not native PS5/FC27/MKW qualification.

- Host CI R457 successor: requalified exact pipeline-drain source against the R23 diagnostic admission oracle; updated bounded SVC fatal-ring and maintained GPFIFO owner checks without relaxing source contracts.

- Host1x qualification updated for the numeric `u64` action-handle implementation: pending cancellation, running cancellation, waiter publication, same-id progress and 256-action stress are exercised at O0/O2 before any console build.

- Vendor `3cac7130d6626dced483d038cbf034274a0463d8`: snapshot Eden `sources/eden/src/video_core/memory_manager.h` restauré immuable; déclarations NVN syncpoint shim déplacées vers `encore-active/eden-core/guest-bridge/memory_manager.h`, propriétaire réellement sélectionné par le build PS5. Le contrôle M04 reconstruit désormais byte-for-byte la composition deferred bridge + shim NS2.

## Detailed-log successor ab388160

- Shipping NPad now emits bounded `EDEN_NPAD_PLUS_LIFO` only while Detailed Logging is enabled; each rising Plus edge carries the guest LIFO sample number and monotonic timestamp.
- Quiet mode performs no NPad diagnostic counters or clock reads. Mapping, sampling cadence and LIFO writes are unchanged.
- Vendor regression reverses the diagnostic byte-for-byte to previous NPad blob `454138c445bc140568068737646349cac98a686d`.
