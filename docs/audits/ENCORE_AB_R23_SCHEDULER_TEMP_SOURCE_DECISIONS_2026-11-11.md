# R23 — décisions source #121 et #152 : scheduler et temp savedata

**11 novembre 2026**, audit isolé PR #45. Niveau source E1 ; pas de compilation PS5, mutation vendor, merge ni validation console.

## #121 — faux besoin de portage du workaround libc++ mutex sur PS5

L'amont [`90aafeedc1`](https://github.com/eden-emulator/mirror/commit/90aafeedc1d980849894f5bf251313db95594e8a) rajoute un `try_lock` avant `unlock` pour contourner l'initialisation paresseuse d'un **std::mutex libc++** dans `KScheduler`.

Or le `headless/CMakeLists.txt` PS5 active par défaut `EDEN_BLOCKING_GUEST_CONTEXT_LOCKS=ON` et inclut `vendor/encore-active/eden-threading/native-hle-overrides.cmake`. Ce fichier remplace complètement `k_scheduler.cpp` par `vendor/encore-active/eden-threading/src/core/hle/kernel/k_scheduler.cpp` (blob `6bf49c0165ecac602628679adbb8cee8d8407190`) et met `k_thread.h` cohérent (blob `e2f359a54cb6b879bdd41f092cf1ea19fb03e4e6`) à disposition des dépendances. **`m_context_guard` est déjà `std::binary_semaphore{1}`, pas un mutex**, et `try_acquire` / `release` remplacent acquisition/restitution. Le bootstrap possède un permis explicite.

**Décision :** pas de portage de `try_lock` dans ce backend. Cette clôture de pertinence source concerne le profil de production avec l'option ON, **pas le profil OFF**, ni le comportement des fibres mesuré sur console. Les stress tests multicœurs restent requis.

## #152 — manque réel de déclenchement unique de nettoyage `temp`

L'amont [`f3af5d0c2`](https://github.com/eden-emulator/mirror/commit/f3af5d0c252feba0df73bedddcd8a40f71ebc0fa) déplace la suppression de `savedata/temp` du constructeur `SaveDataFactory` vers `FileSystemController::InitTempStorage()` déclenché pour un **chargement applicatif frontend**, évitant un nettoyage réitéré à chaque programme.

Le `headless/CMakeLists.txt` PS5 sélectionne explicitement la version maintenue `vendor/encore-active/eden-core/src/core/file_sys/savedata_factory.cpp` (blob `021de7c7f2f3cee7d5ad6c6fa458a57fc23a8002`), dont le constructeur appelle **toujours** `dir->DeleteSubdirectoryRecursive("temp")`. Aucune méthode `InitTempStorage` n'est visible dans le code natif ou le vendor. Le différentiel de comportement est réel **au niveau source** ; aucun jeu PS5 n'a été utilisé pour démontrer un bug.

**Décision :** nouveau candidat de correctif manquant à traiter sur un propriétaire complet FS + core, pas dans `vendor/sources` et sans écraser les savedata. Contrats : une initialisation frontend ; programmes secondaires sans relance de purge ; crash/reprise ; données valides de plusieurs programmes ; autorisations FS PS5 ; tests positifs/négatifs et rollback. Ne pas confondre source gap et régression reproduite.

**Compteur R23 : 80 → 78 revues runtime restantes, et 7 → 8 changements source reconnus mais non intégrés/qualifiés nativement.**
