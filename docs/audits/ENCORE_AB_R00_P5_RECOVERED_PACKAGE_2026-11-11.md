# R00 — récupération PS5 native vérifiée depuis cache (11 novembre 2026)

**Périmètre : traçabilité du build de `main`, constatée dans l'audit A/B PR #45, aucun changement de production.**

| Objet | Preuve |
|---|---|
| Exécution GitHub | [Récupération native #42942150990](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42942150990), **SUCCESS** (job #130266259901) |
| Commit du produit | `niakw/ProsperoEden-Encore@ec8b519182532d3864c5a67dd27aa41aa9d43ff3` |
| Compilation | Cache de la 12ᵉ tentative native réutilisé et cinq TUs recompilées en complément, sans ré-exécuter la compilation complète des 1399 objets; `P5_REPLAY_NATIVE_SHA_RECOMPILE_PASS` |
| Edition de liens | `P5_REPLAY_FINAL_LINK_PASS`; candidat binaire natif **199 322 632 octets** avant staging |
| Conversion ELF | `build/headless-native/eboot.elf`, 78 783 756 octets; SHA-256 `5fc9ee413fdf970e28b417f3d73368f9294e67473fd2606b0308a5f63391e99f` |
| Exécutable PS5 signé/stagé | `PPSA99008/eboot.bin`, 76 701 641 octets; SHA-256 `438fdf4398c9238d5696e925d35b7af6ce8a5a7cc1985a8ce7cde4f5a8b20f4f` |
| Rapport de liaison | `link.map`, 54 464 368 octets, SHA-256 `899d6cc0e9156a0a557c2066e7cbeb490bb41a93389275a0e6224d10e51260de` |
| FTP | [Artéfact GitHub Actions `Eden-Encore-PS5-FTP-PPSA99008`](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42942150990), taille d'archive indiquée 39 616 672 octets |
| Distribution | [Artéfact `Prospero.Eden-Encore-recovered-bundle`](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42942150990), 155 439 473 octets; `dist/SHA256SUMS` vérifié |
| ZIP package complet | `Prospero.Eden-Encore-R457.zip`, SHA-256 `3b39c603fb97e558e5fe815fb0f77def475ab874adaf43ae9b8bdae488f3df3a` |
| ZIP FTP | `Eden-Encore-R457-ec8b5191-FTP-PPSA99008.zip`, SHA-256 `7b87abb567247cf06cdfc7adc7cd498e7826367d1a5548b8d000a3a19e63f474` |

Le workflow a vérifié les empreintes de la distribution, la configuration `PPSA99008`, les imports et l'absence de composants expérimentaux de JIT partagé. Son témoin `EDEN_CRASH_SYMBOL_PROVENANCE` déclare explicitement `confirmed_same_console_binary: false` : aucune console ne s'est encore authentifiée par son hash `eboot.bin`.

## Ce que cette preuve clôt — et ne clôt pas

- **Clôture de la question « un binaire PS5 natif signé et packagé existe-t-il ? » pour `ec8b519` : OUI**, au vu des étapes réussies et des artefacts présents.
- **Pas de reprise du verdict ancien « pas d'ELF à cause du 11ᵉ build » comme verdict actuel.** Les erreurs libwebp SIMD et `Experimental` relevaient de l'ancien SHA, et la récupération ultérieure passe le linker. Cela ne prouve pas une correction générique de ces erreurs à d'autres SHAs.
- **Ne clôt pas R05/R18 et les 17 inclusions d'en-têtes.** Le lien a produit une carte native; l'audit doit récupérer le manifeste et la carte pour les **objets compilés effectifs** et le graphe complet d'en-têtes, au SHA `ec8b519`. Le cache historique de la 9ᵉ tentative n'est pas équivalent aux artefacts de récupération.
- **Ne clôt pas E4.** L'installation, le lancement, les images NS1, l'AudioIn, le JIT et la stabilité PS5 restent sans test corrélé à l'exécutable `438fdf43…`; le statut du workflow n'est pas un test de gameplay.

Aucun nouveau build, merge, pin vendor ni changement à `main` n'a été déclenché par la présente vérification.
