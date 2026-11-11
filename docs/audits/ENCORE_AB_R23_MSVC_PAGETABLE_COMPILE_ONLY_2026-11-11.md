# R23 — compatibilité compilation seule : #115 MSVC et #118 PageTable constexpr

**11 novembre 2026, PR #45 audit isolé.** Avis E1 fondés sur les diffs Git individuels, non sur un portage de `main`; aucun test PS5 lancé ici.

## #118 — suppression de trois spécificateurs constexpr

[Commit Eden `73e004de`](https://github.com/eden-emulator/mirror/commit/73e004de6eb530567b3022531c11b92f55f265a6) : modifie exclusivement `src/common/page_table.h`. Sur les méthodes `PageEntryData::Store`, `MarkRasterizerCached`, `MarkDebug`, `constexpr` devient `inline`, **sans changer un appel atomic, valeur, ordre mémoire ou corps de fonction**. Le fichier source original épinglé (blob `1588eca6168bdcaf04229d6aa4115c3acb624081`) conserve `constexpr`; la version upstream ultérieure (blob `0368e498630344ab9e05f47f4c86776caa3ba6b0`) conserve les mêmes opérations. `constexpr` impliquait déjà `inline` au niveau C++ : changement de compatibilité de compilation, pas de nouvelle sémantique de lecture/écriture de page à importer en runtime.

**Décision :** source E1 revue, **pas de portage fonctionnel PS5**. Ne pas confondre cette conclusion locale avec les changements de `PageTable` dans d'autres commits ni considérer les 17 reçus d'en-têtes natifs comme validés.

## #115 — « fix MSVC build errors » et sources sélectionnées

[Commit Eden `1203082a`](https://github.com/eden-emulator/mirror/commit/1203082a8f1211ad6ce4d95f0c6947f7ecd27a55) : 4 fichiers modifiés, quatre ajustements de compilation/type.

- `src/common/sparse_large_vector.h` : commente la contrainte `requires std::is_trivially_copyable_v<T>` incompatible avec certaines évaluations MSVC d'un `T` contenant des atomiques. **La version maintenue PS5** `vendor/encore-active/eden-core/src/common/sparse_large_vector.h` (blob `802510144fc117b62aeb8999c39b7cc5ba2f9f9f`) conserve la contrainte et son code de gestion de mémoire natif. Aucune preuve de problème d'instanciation sous Clang PS5 ; ne pas supprimer la contrainte aveuglément.
- `src/core/arm/dynarmic/arm_dynarmic_32.cpp` et `arm_dynarmic_64.cpp` : valeur numérique inchangée, conversion de `0` en `uint8_t(0)` et de `Common::PageTable::SIGN_BIT` en `std::uint8_t(...)`. Les valeurs 0 et 8 utilisées par les chemins natifs restent les mêmes pour leur largeur déclarée; les différences dans l'émission x64 proprement dite sont traitées sous #117/#122/#125/#136, séparément.
- `src/core/hle/service/ssl/ssl.cpp` : conversion explicite `uint32_t(socket->GetFD())` avant l'affectation à `Out<u32>`, équivalente à la conversion implicite lorsqu'un même chemin de service est présent. **Attention : au pin Eden du projet, la commande `GetSocketDescriptor` est encore une entrée `nullptr`** ; le commit #115 seul ne l'implémente pas et ne justifie pas de prétendre la fonctionnalité SSL présente. La parité de service SSL appartient à d'autres commits / tests HLE.

**Décision :** portabilité de compilation MSVC seulement pour les fichiers réellement sélectionnés et les valeurs déjà prises en charge sous le compilateur PS5 actuel. **Aucun correctif de comportement NS1 à transplanter de ce commit isolé**, mais ne pas transformer cette exclusion en certificat de conformité SSL ou de mémoire sparse générale.

## Séparation des preuves

Le [relink PS5 `main@ec8b519`](ENCORE_AB_R00_P5_RECOVERED_PACKAGE_2026-11-11.md) donne un artefact natif complet, pas un test de toutes les configurations compilateur, ni une preuve que ces quatre unités original/amont ont les mêmes octets. Ces deux décisions sont **E1 code-source**, pas E3/E4 console.

**Compteur prévu après classification :** 71 → **69** commits R23 nécessitant toujours une revue sémantique; les **17 en-têtes** et **7 lots correctifs** restent non qualifiés sur console.
