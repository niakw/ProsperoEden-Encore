# Eden Encore — réparation de la fusion sur main (7 novembre 2026)

## État vérifié

- Moteur `niakw/ProsperoEden-Encore`, uniquement `main`.
- Vendor `niakw/Prospero.Eden-Encore-vendor`, uniquement `main`.
- PR historique [#24](https://github.com/niakw/ProsperoEden-Encore/pull/24) fusionnée et fermée ; ne plus pousser sur l'ancienne branche.
- Gitlink du moteur épinglé au vendor, ne pas oublier de le mettre à jour après chaque commit vendor.
- Une PR vendor distincte [#8](https://github.com/niakw/Prospero.Eden-Encore-vendor/pull/8) a déjà intégré `NrRdna2VitBoundaryRepack` pour `FinalHead` ↔ ViT ; ne pas refaire ce composant.
- Priorité : **première chaîne neuronale complète et correcte**, non optimisation temps réel ; pré/post-image, FSwin, Split, ViT, décodeur, guide GPU et sortie. Aucune preuve PS5/RDNA2 tant que le graphe entier n'est pas exécuté et qualifié.

## Incident confirmé dans la CI

[Core fast gate #42314835664](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42314835664) a échoué sur l'étape `Pinned Vulkan source reproduction`. Le log de l'exécution indique précisément :

```text
RuntimeError: Vendored upstream has changed: src/common/settings_enums.h
```

La source amont `vendor/sources/eden/src/common/settings_enums.h` avait été modifiée dans trois commits R24/R09 (nouveaux indices FXAA+/MSAA puis A4K), en contradiction avec son verrou `f2a3ae93…` dans le manifeste des 83 backports. Restaurer le fichier original seul ferait disparaître les identifiants demandés du build PS5.

### Correction sans perte fonctionnelle

1. Restaurer `vendor/sources/eden/src/common/settings_enums.h` depuis le commit antérieur `3b6ea83d` (SHA256 exact du manifeste : `f2a3ae93b4257611958fab5a0c652f89c8158d2e16da31fb196a27960cf467ba`).
2. Le nouveau `tools/stage-ps5-graphics-enums.py` vérifie **à la fois** les deux SHA-256 amont/overlay et ajoute uniquement sur la copie temporaire de compilation PS5 les cinq indices AA et les trois indices A4K, dans les mêmes ordres qu'avant la restauration.
3. La préparation `tools/prepare-build.sh` appelle le stage après les backports/core/header/surface, puis un `--check`. La copie doit se trouver dans un cache `ps5-eden-headless.*` avec fichier `owner` de ce checkout. L'outil rejette symlinks, dérives, sources inconnues et options dupliquées, écrit atomiquement et reste idempotent.
4. `tools/graphics/test-a4k-profiles.py` vérifie maintenant les profils **dans l'en-tête obtenu par transformation contrôlée**, plutôt que d'exiger illégalement des modifications du miroir source. La CI fast gate effectue une vérification hôte précoce de l'overlay.

## Suivi technique R09

[Source MIT en amont](https://github.com/Overclockers/DLSSNR-AMD) et [travaux précédents sur les blocs](https://github.com/niakw/ProsperoEden-Encore/blob/main/docs/ENCORE_R09_VIT_8BLOCK_VULKAN.md).

**Présents en source** : shaders Vulkan 1.1 RDNA2, import NRMODEL1 local, deux parcours Split-Swin (16/4 blocs Original/Compact), huit blocs ViT (40 opérations par modèle), décalage QKV, ProjPool/FinalHead et repack `FinalHead ↔ ViT`. **Ne constitue pas une preuve de rendu neuronal complet.**

**Restant à fermer** : graphe global FSwin/Skip/ViT/décodeur, extraction fidèle des gains, pré/post-image et raccord du renderer, génération et compilation SPIR-V, tests C++/CTS, puis PS5 à la phase P5. Préserver NS1, ne jamais interpréter une compilation hôte verte comme un rendu PS5 testé. Aucun nouveau branch/PR, travaux seulement sur `main`.
