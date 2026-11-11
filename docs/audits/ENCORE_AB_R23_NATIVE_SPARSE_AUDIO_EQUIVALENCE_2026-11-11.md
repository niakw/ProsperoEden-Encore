# R23 — équivalences sélectionnées : mémoire sparse PS5 et volume audio natif

**11 novembre 2026**, audit isolé [PR #45](https://github.com/niakw/ProsperoEden-Encore/pull/45). Décisions fondées sur le code réellement possédé et non sur le titre des commits. **Niveau E1 source uniquement, pas E3/E4**.

## #93 — gestion d'un échec de commit d'une page sparse

- [Amont `37fe91195`](https://github.com/eden-emulator/mirror/commit/37fe9119526c03ca064166130cc983c55b9a9e86) : modifie `sparse_large_vector.cpp/.h` pour traiter les échecs de réservation et protéger le gestionnaire d'exceptions **Win32**.
- **PS5 sélectionne** la version maintenue `vendor/encore-active/eden-core/src/common/sparse_large_vector.h` (blob Git `802510144fc117b62aeb8999c39b7cc5ba2f9f9f`). Le chemin non-Windows appelle `CommitSparsePage(page)` et ne marque la page engagée qu'après cette opération. La fonction native `src/memory_pages.cpp` appelle `OwnSlot` et **abandonne le processus immédiatement** si l'allocation échoue, avant la mise à jour du bitmap. Le cas dense ne requiert aucun nouveau commit de page.
- **Disposition** : l'objectif de ne pas continuer avec une page non engagée est déjà réalisé sur l'allocateur natif PS5, mais par un mécanisme différent du `mprotect` upstream. Le correctif de handler Win32 n'est pas exécutable sur PS5. Aucune importation globale. Les politiques de crash/retry et tests console restent distincts et ouverts ; cette décision n'affirme pas l'égalité API générale des backends.

## #145 — volume qui persiste après fermeture des streams

- [Amont `93318ef69`](https://github.com/eden-emulator/mirror/commit/93318ef69) : stocke le volume du périphérique dans les sinks Cubeb/SDL3/Null puis le transmet aux nouveaux streams.
- **PS5 sélectionne un sink distinct** `headless/audio.cpp` (sur `main`, blob `a927dcc543fea01f7f548a9a614abf81180e923d`) et `headless/devices.h` (blob `274035c427532e0c0340a4d7187f99876a90af58`). `AudioSink::SetDeviceVolume` enregistre `device_volume`; `GetDeviceVolume` renvoie ce même état ; `AcquireSinkStream` appelle `stream->SetDeviceVolume(device_volume)` avant d'ajouter un nouveau stream ; `CloseStreams` ne détruit que le vecteur des streams. Le volume est donc **conservé dans le sink entre deux sessions**.
- **Disposition** : source/contrat natifs équivalents pour cet effet PS5, aucun copier-coller de Cubeb/SDL3/Null. Un test d'exécution de la fermeture/réouverture et une vérification console restent souhaitables pour l'acceptation E3/E4, sans requalifier ce commit comme un manque de fonctionnalité.

**Résultat : 2 décisions sémantiques supplémentaires ; registre R23 de 84 à 82 commits runtime encore à qualifier.** Aucun changement `main` ni `vendor` et aucun build/release déclenché dans cette branche d'audit.
