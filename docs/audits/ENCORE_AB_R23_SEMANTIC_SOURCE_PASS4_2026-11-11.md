# R23 — revue sémantique 4 : Opus/FFmpeg, SSL et GPU Maxwell

**Branche audit uniquement, 11 novembre 2026.** Comparaison figée des commits individuels Eden et de leur source propriétaire. Aucune modification de `main`, du sous-module ni aucun build natif. Les tests console ne sont pas impliqués.


## Passe sémantique 4 — 4 décisions supplémentaires, sans portage aveugle

**Sources à l'appui :** [#138 SSL](https://github.com/eden-emulator/mirror/commit/ee73920d288586103491d3e2af003b5c40bf4a1c), [#142 revert Opus](https://github.com/eden-emulator/mirror/commit/2b4184dd2bb33da081702263d59c3eadb299e673), [#148 introduction Opus](https://github.com/eden-emulator/mirror/commit/ff8368c6066faf3962e2f77af7da4954e2ff6a43), [#146 GPU null pointer](https://github.com/eden-emulator/mirror/commit/9b649444803bc95423035eba335a1e11c1871793).

- **#142 + #148 : retour arrière prouvé du remplacement libopus → FFmpeg.** Comparaison exacte du parent de #148 `8a22f1845b8b7ec19fbb518b696513e36d42b317` avec #142 : les fichiers `CMakeLists.txt`, `cpmfile.json` et `src/audio_core/adsp/apps/opus/opus_decoder.cpp` sont des blobs Git strictement identiques. Quatre autres fichiers `src/audio_core/adsp/apps/opus/` diffèrent **uniquement** par la notice préfixée Eden GPL-3.0 (suppression exacte des trois lignes de préfixe, comparaison octet-à-octet positive). Des modifications de sink indépendantes dans les 7 commits intermédiaires sont **hors** du couple d'annulation et restent auditées séparément. **Décision comportementale : aucun portage de la migration Opus/FFmpeg annulée**, sans ignorer ses obligations de licence.
- **#138 : SSL.** L'ancien `src/core/CMakeLists.txt` épinglé (`508ace350173f5068bd7531f37e70199134fde3a`) sélectionne sans condition `ssl_backend_openssl.cpp` et lie `OpenSSL::SSL` / `OpenSSL::Crypto`. La nouveauté amont sélectionne le **même backend** lorsque la cible OpenSSL existe, et offre seulement un fallback sans OpenSSL. **Décision : équivalent pour la configuration native figée exigeant OpenSSL**. La gestion d'un build futur sans OpenSSL reste une question de dépendance, pas un correctif de runtime Switch à importer.
- **#146 : GPU Maxwell.** L'amont corrige dans `video_core/control/channel_state_cache.h` un pointeur non initialisé `P* channel_state;` en `P* channel_state = nullptr;`. Le fichier Eden épinglé (`6d70e9be559cc74d88e1204cea909168b4b2d686`) a **encore l'ancienne déclaration**. **Décision : changement pertinent manquant dans la source**, à préparer pour un propriétaire maintenu ; il faut établir l'en-tête vraiment inclus et tester l'initialisation native avant toute affirmation de correction PS5.

**Nouveau compteur R23 : 101 commits runtime encore sans disposition sémantique, 5 correctifs hôte préparés, 1 nouveau candidat GPU #146 à intégrer/vérifier, 12 assets/build à qualifier.** Les 17 en-têtes divergents sans reçu natif, 7 lots correctifs de bout en bout et preuves console restent ouverts. Cette passe clôt **4 avis sémantiques E1**, pas 4 tests PS5.


Sources de vérité : [155 décisions](r23/R23_EDEN_155_APPLICABILITY_2026-11-11.json), [rapport général](ENCORE_AB_R23_155_APPLICABILITY_2026-11-11.md), [registre de clôture](ENCORE_AB_NS1_MASTER_EXIT_REGISTER_2026-11-10.md).
