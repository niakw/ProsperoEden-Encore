# R23 — deux nouvelles décisions NS1, IPS >256 et constructeur HLE

**11 novembre 2026.** Analyse A/B sur [PR #45](https://github.com/niakw/ProsperoEden-Encore/pull/45), code correctif isolé dans [PR #46](https://github.com/niakw/ProsperoEden-Encore/pull/46). Aucun merge, gitlink ni build PS5 déclenché par cet audit.

## #116 — buffer fixe de 256 octets pour les lignes IPSwitch

- [Amont Eden `14235dc0`](https://github.com/eden-emulator/mirror/commit/14235dc0d0543c7397dd19eb1a677e76114c08f3) : `src/core/file_sys/ips_layer.cpp` remplace une structure de `std::array<uint8_t, 256-sizeof(size_t)>` + compteur par `std::vector<uint8_t>`. Les écritures de `EscapeStringSequences` deviennent `push_back`; les remplacements hexadécimaux dimensionnent la sortie avant `memcpy` et l'application du patch utilise `data.size()`.
- **Pinned `vendor/sources/eden` :** ancienne unité Git blob `9d46549bf0fae3ec5fd0ab6c65bc432dcff68818`, encore sensible à la longueur.
- **PR #46, propriétaire préparé, non fusionné :** `headless/r23_ips_layer_ps5.cpp`, Git blob au constat `5e01ee8f931798e972031ee5b10e5d31815d2be3`. Le code utilise `std::vector<uint8_t> data`, `push_back`, `data.resize(hs.size())`, et `replace_size = record.second.data.size()`; le remplacement par CMake PS5 est présent. La source originale vendor reste immuable.
- **Test préparé :** `tools/audit/check-r23-ips-long-line-host.py` contient une extraction réelle de `IPSwitchRecord` / `EscapeStringSequences` et des cas de 249 et 4 096 caractères, 1 024 octets hexadécimaux, échappements et sentinelles sous ASan/UBSan. **Attention : le dernier run R23 vert #42931313765 portait sur le blob plus ancien `0a2ad961...`, pas sur le blob actuel `5e01ee8...`; ne pas le présenter comme preuve de réussite à ce dernier SHA.**
- **Disposition :** source NS1 manquante dans le pin, **correctif spécifique préparé hors production** ; exact HEAD du correctif doit repasser en CI, puis compilation du vrai `core` et essais PSP/PS5, fichiers malformés et cas limites. **Niveau E1, E3/E4 encore ouverts.**

## #141 — constructeur constexpr des tables HLE (compatibilité MSVC)

- [Amont Eden `5adaa5b0`](https://github.com/eden-emulator/mirror/commit/5adaa5b0f7e19df9bf9dbd883fe921dfe4952125) : **une seule ligne** `src/core/hle/service/service.h`, suppression de `constexpr` sur `FunctionInfoTyped(u32, HandlerFnP<T>, const char*)`. Corps du constructeur et conversion du pointeur de gestionnaire strictement inchangés.
- Le pin a encore `constexpr FunctionInfoTyped(...)` (blob `df56b6984731070f5b0472c883d46626e3cbc30a`); l'en-tête amont final est `68b0d636d8be79de1d05af2c6113addab0caffa7`.
- **Disposition E1 :** correctif de compatibilité de compilation MSVC, **pas de changement du corps d'exécution ni de dispatch des services HLE**. Il n'y a pas de portage NS1 comportemental à effectuer vers la compilation PS5 Clang actuelle. Les évolutions d'ABI/toolchain MSVC éventuelles n'appartiennent pas au même test que la console PS5.
- Ne pas déduire qu'un en-tête réécrit sous CMake est inclus dans chaque objet : la provenance native des 17 en-têtes historiquement divergents reste une exigence séparée.

**Effet sur le registre R23:** deux décisions sémantiques E1 classées explicitement, de **73** à **71** cas runtime sans décision. Il reste **6** cas de build/dépendances, **7** gaps sources distincts, **5** autres patchs hôte préparés, et **1** IPS long-line préparé mais sans CI au SHA courant; ce sont des files d'actions indépendantes, non interchangeables.
