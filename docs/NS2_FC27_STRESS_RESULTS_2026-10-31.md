# NSW2 × FC27 — résultats reproductibles des stress tests (31 octobre 2026)

**Branche de recherche :** `research/ns2-ps5-compatibility` uniquement. **Commit testé :** [`7fec9a5c07826162413f92e6867a5147050c4b75`](https://github.com/niakw/ProsperoEden-Encore/commit/7fec9a5c07826162413f92e6867a5147050c4b75). **Aucune modification de `main`, aucun merge et aucune release.**

**Verdict :** les deux jobs du nouveau banc de stress sont **SUCCESS (2/2)**. Ils prouvent que les régressions exécutées sur Linux et les défauts injectés sont correctement détectés ; **ils ne prouvent ni une amélioration de FC27 sur PS5, ni un rendu de jeu Switch 2, ni une absence de texture noire en conditions réelles.**

- [CI NSW2 FC27 workload stress — run 41149975993](https://github.com/niakw/ProsperoEden-Encore/actions/runs/41149975993), `success`.
- [Job 124383927288 — enveloppe FC27, x1/x4/x8 et PFS0](https://github.com/niakw/ProsperoEden-Encore/actions/runs/41149975993/job/124383927288), `success`.
- [Job 124383927029 — code réel extrait des chemins texture/DMA/Vulkan/HUD](https://github.com/niakw/ProsperoEden-Encore/actions/runs/41149975993/job/124383927029), `success`.
- [Artefact `ns2-fc27-synthetic-stress` — téléchargement GitHub Actions](https://github.com/niakw/ProsperoEden-Encore/actions/runs/41149975993/artifacts/13022108946) (rétention configurée à **7 jours**, pas d’hébergement permanent).
- Les CI NSW2 précédentes [JIT 41149065741](https://github.com/niakw/ProsperoEden-Encore/actions/runs/41149065741) et [host guards 41149065740](https://github.com/niakw/ProsperoEden-Encore/actions/runs/41149065740) sont également **vertes** au commit `17e382c`, avant l’ajout de ce banc.

## 1. Référence mesurée sur vraie PS5 : FC27 Switch 1

**Source historique**, pas une nouvelle session : `tools/fixtures/fc27-2efd8b3c-stutter-windows.json`, capture anonymisée du build `2efd8b3c96608667a2b22f1751eed1a475091cce`. Fichiers du jeu et journaux privés exclus du dépôt.

| Mesure historique | Valeur | Interprétation |
| --- | ---: | --- |
| Fenêtres échantillonnées | **415** | Fenêtres d’environ 5 secondes |
| Callbacks de présentation cumulés | **60 955** | Ce ne sont pas des pixels renouvelés prouvés |
| Intervalles > 50 ms | **858** | Saccades observées dans l’ancienne session |
| Intervalles > 500 ms | **10** | Blocages de présentation importants |
| Pire intervalle | **1 288,129 ms** | Ne donne pas à lui seul la cause |
| SLA de fluidité sur cette trace | **FAIL (attendu)** | Un test vert doit confirmer cet échec historique, pas le masquer |

### Répartition des trois régimes constatés

Agrégation calculée directement depuis les **415 lignes** de la fixture publique (bornes sur le compteur cumulé de présentation, **pas** scènes de jeu identifiées image par image) :

| Régime / compteur `total` | Fenêtres | Gaps >50 ms | Gaps >500 ms | Pire gap | Médiane JIT par fenêtre | Médiane attente cache par fenêtre |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Démarrage / `total ≤ 6 000` | **42** | **109** | **7** | **1 288,129 ms** | **592,853 ms** | **8,552 ms** |
| Match / `6 000 < total ≤ 32 000` | **180** | **679** | **3** | **648,845 ms** | **25,952 ms** | **16,529 ms** |
| Fin à présentation répétitive / `total > 32 000` | **193** | **70** | **0** | **135,3 ms** | **0 ms** | **0,257 ms** |
| **Total** | **415** | **858** | **10** | **1 288,129 ms** | — | — |

**Contre-exemples importants pour le diagnostic :** parmi les trois fenêtres de match avec un gap dépassant 500 ms, celles terminant aux frames **19 562** et **19 633** n'enregistrent que **39,046 ms** et **29,499 ms** de JIT agrégé, avec **32,393 ms** et **71,371 ms** d'attente cache totale. Les longues images ne relèvent donc **pas toutes** d'une phase de compilation initiale massive. En fin de trace, **154/193 fenêtres** ont un compteur JIT égal à zéro ; ce compteur ne prouve **ni** l'absence de travail CPU non mesuré, **ni** une progression effective du jeu. Les médianes d'une fenêtre de plusieurs threads ne sont pas des durées individuelles par frame.

La trace contient trois régimes distincts : compilation JIT très coûteuse au début, saccades persistantes pendant le jeu, puis période où le compositeur reste actif alors que la progression visuelle du match est suspecte. Une file Vulkan non saturée ou un affichage apparent à 30 FPS **ne constituent pas** une preuve de progression du jeu. Les sommes `jit_ms` et `cache_wait_ms` sont calculées sur des fenêtres et plusieurs threads, **pas** par image individuelle.

## 2. Stress synthétique inspiré de FC27

Exécuté par `tools/ns2/fc27_stress_replay.py` à partir des nombres d’images des 415 fenêtres ; les mutations de textures, les commandes du worker, les délais et les défauts sont **entièrement synthétiques**, non extraits d’assets du jeu.

| Contrôle | x1 | x4 | x8 |
| --- | --- | --- | --- |
| Relecture de l’ensemble des 415 fenêtres | PASS | PASS | PASS |
| Dessins avec vue de texture périmée, scénario sain | **0** | **0** | **0** |
| HUD noir/absent, scénario sain | **0** | **0** | **0** |
| Limite du cache de vues (96 entrées) | Respectée | Respectée | **96 au pic** |
| Relecture de charge / file bornée de 32 éléments | Exécutée | Surcharge modélisée détectée | **850 204 unités de backpressure simulées** |

**Détails x8 enregistrés dans la CI :**

| Mesure synthétique x8 | Résultat |
| --- | ---: |
| Dessins de textures HUD/terrain/maillots | **1 462 896** |
| Modifications de révisions | **157 408** |
| Remappages simulés | **40 997** |
| Évictions simulées | **975 192** |
| Pic de vues résidentes | **96/96** |
| Textures périmées / HUD noirs dans la version saine | **0 / 0** |
| Pic file de commandes | **32/32** |
| Pression cumulée dans le worker fictif | **850 204** |

**Mutation testing (des bogues introduits volontairement dans le modèle) :**

| Défaut injecté | Détection |
| --- | ---: |
| Ne pas invalider correctement une vue de texture après révision/remap | **3 032 dessins périmés détectés** |
| Faire disparaître le HUD lors d’un dessin | **129 HUD noirs détectés** |
| Bloquer le producteur invité pendant 750 ms, compositeur maintenu à 30 FPS | **23 images répétées**, avec **0** intervalle compositeur > 50 ms |

Le modèle valide sa propre capacité à **repérer** ces erreurs : le `PASS` n’est **pas** une garantie que le GPU RADV réel ne présente jamais ces défauts. La file `32`/worker `60 unités/s` est une hypothèse contrefactuelle explicite, **pas une mesure de la file Vulkan sur PS5**.

## 3. Régressions exécutant des extraits du vrai code d’Encore

Job [source-extracted FC27 texture and Vulkan renderer guards](https://github.com/niakw/ProsperoEden-Encore/actions/runs/41149975993/job/124383927029) : **SUCCESS**, avec compilation C++ réelle et objets GPU simulés.

| Chaîne / témoin | Ce que la CI a effectivement vérifié |
| --- | --- |
| **F03 TIC/TSC → descripteur → barrière** | **60 images de test**, 1 récupération après vue absente, 1 récupération après remap, **63 barrières** ; variantes `-O0` / `-O2` |
| **F04 remap / DMA / alias / upload** | **3 copies DMA**, **2 copies d’alias**, **1 remap**, **3 révisions** et **3 barrières** ; variantes `-O0` / `-O2` |
| **F04 révision d’upload** | Cas ordinaire, conversion, accélération, asynchrone, MSAA et récupérations d’erreur (staging OOM, mapping court, handle nul) |
| **F07 blit → pipeline Vulkan** | Invalidation correcte de l’état de pipeline après blit brut, protections des changements d’alpha ; `-O0` / `-O2` |
| **F07 fraîcheur TIC HUD** | Vue stable, remappée, supprimée/recréée, blacklist/retry et vue vide ; `PS5_NATIVE` activé/désactivé et `-O0` / `-O2` |
| **F07 propriétaire des caches** | Ordre de verrous, durée de vie des mutex, échantillonnage des phases et mode quiet ; `PS5_NATIVE` activé/désactivé |
| **Classification contention / JIT** | Régressions des signaux de longue image, sans interpréter les temps CPU agrégés comme latence d’une image |

**Niveau de preuve :** chemins C++ de production sélectionnés et compilés/testés sur runner Linux avec faux services GPU ; **pas** d’accès direct à la mémoire vidéo de la PS5, pas de CRC de pixels sur console, pas de match FC27 exécuté par la CI.

## 4. Faux `.nsp` : contenu exact et limites

Le script `tools/ns2/build_fc27_synthetic_nsp.py` construit un **PFS0 structurellement valide** (avec extension `.nsp`) à partir de l’ExeFS homebrew public source-vérifié, puis contrôle la lecture inverse de tous ses membres, leurs SHA-256 et le rejet des données tronquées ou d’un magic erroné.

- Fichier : `fc27-synthetic.nsp` — **8 390 979 octets**, SHA-256 **`97851dd4409d612d24dc5f0c2a89d816f76adb25b5d12a4f8d4214546bf18229`**.
- Membres : `main`, `main.npdm`, `stress.json`, `hud.rgba`, `pitch.rgba`, `kits.rgba` ; les trois dernières charges sont des octets procéduraux, **aucun asset FC27**.
- **Correction après audit du code source :** le chargeur Encore sait aussi charger des **NSP de type ExeFS extrait** (`main` + `main.npdm`) sans NCA. Le PFS0 créé peut donc **atteindre cette route de chargement**. Il n'a toutefois pas été lancé dans le `KProcess` ni sur PS5 : sa capacité à terminer le boot, produire des FPS ou afficher du HUD **reste non démontrée**. Les assets procéduraux ne sont pas utilisés par le programme AArch64 ; ils servent au stress hôte seulement.
- L’ExeFS indépendant `main` + `main.npdm` inclus dans l’artefact sert au futur essai de chargement natif opt-in, sans signature ou contenu Nintendo.

## 5. Exécution reproductible

```bash
python3 tools/check-fc27-stutter-regimes.py --self-test
python3 tools/ns2/fc27_stress_replay.py --out /tmp/fc27-stress-report.json
# Dépend d’un compilateur croisé AArch64 public pour l’ExeFS :
python3 tools/ns2/build_public_nso_fixture.py --output /tmp/fc27-hello.nso
python3 tools/ns2/build_public_exefs_fixture.py --nso /tmp/fc27-hello.nso --output-dir /tmp/fc27-exefs
python3 tools/ns2/build_fc27_synthetic_nsp.py --exefs /tmp/fc27-exefs --out /tmp/fc27-synthetic.nsp --texture-mib 8
```

Les régressions natives sont déclarées dans [`.github/workflows/ns2-fc27-stress.yml`](../.github/workflows/ns2-fc27-stress.yml), et le protocole de test dans [`NS2_FC27_SYNTHETIC_STRESS.md`](NS2_FC27_SYNTHETIC_STRESS.md). Le JSON détaillé `stress-report.json` est disponible dans l’artefact tant que sa rétention n’a pas expiré.

## 6. Périmètre de qualification **sans console** — décision du propriétaire

**Aucun test PS5 ne sera demandé à l'utilisateur.** Le projet clôt ce cycle au niveau de preuve maximal réellement accessible dans les outils et la CI GitHub. Les limites suivantes sont documentées, **pas présentées comme des tâches que l'utilisateur doit effectuer** :

1. **`KProcess` complet non exécuté sur PS5.** Le vrai NSO, le NPDM, l'ExeFS et les SVC ont des validations hôtes indépendantes ; l'enchaînement dans un processus natif complet n'est pas démontré.
2. **Pas de mesure de pixels GPU sur PS5.** Les modèles détectent les révisions de texture périmées et les contenus répétés ; les tests C++ valident les chemins de production sélectionnés avec objets GPU simulés.
3. **Pas de corrélation causale image par image FC27.** Les fenêtres historiques sont réelles et anonymisées mais ne fournissent ni CRC GPU, ni identité de surface présentée, ni progression guest au moment exact d'une saccade.
4. **Pas de nouveau benchmark FC27.** Aucune nouvelle session console n'étant possible, ne pas annoncer un gain de FPS, la disparition du HUD noir, ou la résolution du gel pause/mi-temps.
5. **Pas de compatibilité NSW2 commerciale prouvée.** Un NSP/ExeFS homebrew de recherche peut être reconnu par les couches de chargement, sans valider le HLE complet, les shaders, les services du jeu, ou le rendu matériel.

**Critère de clôture applicable :** CI hôte verte, exécution des parseurs/chemins source disponibles, cas négatifs de corruption et de fraîcheur détectés, résultats et limites consignés dans ce rapport. Tout résultat matériel impossible à obtenir est déclaré **« non vérifié »**, jamais « réussi » ni « corrigé ».

### Mise à jour de validation

**Validation finale après compilation :** le run complémentaire [NS2 host guards 41149975928](https://github.com/niakw/ProsperoEden-Encore/actions/runs/41149975928) est désormais **SUCCESS (2/2 jobs)** au même commit de test `7fec9a5c` : contrôles de sources et compilation C++ AArch64 complète verts. Le banc stress [41149975993](https://github.com/niakw/ProsperoEden-Encore/actions/runs/41149975993) est lui aussi **SUCCESS (2/2)**. Les commits ultérieurs `4c1b24b` et `62d9253` ne changent que la documentation et n'introduisent aucun changement de moteur ou de tests.

**Règle de suivi :** conserver systématiquement SHA de source, run CI, données réellement mesurées, données simulées, cas négatifs, niveau de preuve, et validations PS5 encore ouvertes. Ne jamais transformer un succès hôte en affirmation de FPS ou de textures corrigées sur console.

## 7. Révision N41 — véritable parseur PFS0 et route ExeFS extraite

L'audit des sources maintenues épinglées apporte une correction importante :
`FileSys::NSP::NSP` choisit `extracted = true` dès que
`FileSys::IsDirectoryExeFS(pfs)` constate `main` et `main.npdm`.
`AppLoader_NSP` instancie alors `AppLoader_DeconstructedRomDirectory`
plutôt que de rechercher un programme NCA. Le faux NSP de la section 4
est donc un **candidat réel à la route ExeFS extraite**, et non un NSP
nécessairement rejeté pour absence de NCA. Cela ne valide pas son boot complet.

La CI N41 compile et exécute sans modification le **constructeur C++ réel**
`PartitionFilesystem::PartitionFilesystem`, le vrai
`Header::HasValidMagicValue` et le prédicat original
`IsDirectoryExeFS`. Les objets périphériques VFS sont substitués par
des fichiers mémoires hôtes : **ce n'est ni l'exécution de l'entièreté de
`NSP::NSP`, ni un démarrage `KProcess`**. Les assertions portent sur :
six fichiers récupérés ; identité octet par octet de `main` et
`main.npdm` ; présence des trois charges procédurales ; rejet de
magic corrompu, table tronquée et conteneur sans `main` ; cohérence de
la route NSP extrait. Tests Clang et GCC sous ASan/UBSan.

Le run CI, son commit et les éventuels écarts de validation sont renseignés
une fois la vérification GitHub terminée. Cette étape est menée **sans
solliciter de test console** : la validation s'arrête aux preuves que les
runners et les tests hôtes permettent effectivement d'établir.

## 8. N42 — contrôle CRC de textures intégral et corruption d'un octet

**Commit source :** [`7a86fcee66fbdf253a69acabb23a5635c45eef46`](https://github.com/niakw/ProsperoEden-Encore/commit/7a86fcee66fbdf253a69acabb23a5635c45eef46).
**CI :** [run 41150976739](https://github.com/niakw/ProsperoEden-Encore/actions/runs/41150976739) — **SUCCESS, 2/2 jobs**.
**Artefact :** [`ns2-fc27-synthetic-stress` (ID 13023665238)](https://github.com/niakw/ProsperoEden-Encore/actions/runs/41150976739/artifacts/13023665238), rétention de 7 jours.

- NSP PFS0 de **8 391 065 octets**, SHA-256 `5d090faa03b00be3a30f8a6f43fd479b2543e846b6c5d3d29d376412fa4993cd`. L'augmentation de taille par rapport au premier run provient du manifeste corrigé, et non de nouveaux assets EA.
- `REAL_ENCORE_EXTRACTED_NSP_PFS0_PASS` sous **Clang -O1 et GCC -O2**, avec ASan/UBSan : six entrées, route ExeFS extraite vraie, `main` **407 octets** et `main.npdm` **1536 octets** identiques au référentiel.
- **CRC32 intégral des trois charges** `hud.rgba`, `pitch.rgba`, `kits.rgba` calculé par un parseur Python indépendant et comparé aux octets relus par le constructeur C++ réel, sous les deux compilateurs.
- Mutation négative : **1 octet** altéré dans la fin du payload maillot, avec en-tête PFS0 inchangé ; `REAL_PFS0_TEXTURE_BYTE_CORRUPTION_DETECTED` sous Clang et GCC. Le test échoue si cette mutation échappe au contrôle.
- Les autres rejets (`magic` erroné, table tronquée, `main` absent) continuent de réussir. Les tests F03/F04/F07 précédents restent verts.
- **Limite :** CRC de **fichiers PFS0 lus en mémoire hôte**, pas CRC d'une surface Vulkan réelle. Cela ne valide aucun rendu de maillot, HUD ou terrain sur PS5.

## 9. N43 — extension de la validation des gels et de la fraîcheur du présentateur

Le workflow FC27 a été renforcé avec trois tests de sources de production exécutés avec GPU simulé : récupération TIC → rendu → gestionnaire de présentation F03 ; parcours nvdisp/Host1x → Vulkan → présentation F05 sur **260 soumissions** ; publication d'événements noyau / réveil d'attente F05. **Aucune mesure console n'a été effectuée ni demandée.**

**Historique CI conservé :**

- [Premier run N43, 41151265054](https://github.com/niakw/ProsperoEden-Encore/actions/runs/41151265054) : **FAIL** du job rendu uniquement parce que `boost/container/small_vector.hpp` manquait sur le runner Linux. Les premières assertions F03 étaient déjà vertes. Ce run ne révèle pas de régression de rendu ou de concurrence.
- Commit [`75ed3eb`](https://github.com/niakw/ProsperoEden-Encore/commit/75ed3eb2d61f14893c206ecda8f94e5bdb3a31b3) : installation explicite du paquet de headers `libboost-dev` dans le job hôte.
- [Relance N43, 41151385884](https://github.com/niakw/ProsperoEden-Encore/actions/runs/41151385884) : **SUCCESS, 2/2 jobs**, aucun échec dans les trois scénarios nouvellement intégrés.
- [Artefact NSP / ExeFS / rapport, ID 13023795189](https://github.com/niakw/ProsperoEden-Encore/actions/runs/41151385884/artifacts/13023795189), rétention de 7 jours. Identité du PFS0 inchangée : **8 391 065 octets**, SHA-256 `5d090faa03b00be3a30f8a6f43fd479b2543e846b6c5d3d29d376412fa4993cd`.

**Témoins validés d'après les logs de la relance (Clang, `-O0` et `-O2` selon le fixture) :**

| Chaîne source maintenue | Données vérifiées en CI | Limite explicite |
| --- | --- | --- |
| F03 TIC/HUD → renderer → present | **241 frames**, **241 révisions de HUD distinctes**, **2 remaps**, **1 disparition temporaire**, **12 ticks de pause**, **241 barrières**, et 243 callbacks présentateur | GPU/WSI et pixels de la console simulés |
| F05 binder/BufferQueue/nvdisp → Vulkan | **260 transactions**, **260 frames acquises**, **260 composites**, **260 copies**, **260 callbacks**, file async de **7 frames**, ordre conservé, fences immédiates/différées vérifiées | Pas d'ACK de scanout réel sur PS5 |
| F05 noyau → réveils de threads | **260 cycles**, **2 threads invités simulés**, **520 reprises**, **260 signaux coalescés**, **260 réarmements**, arrêt propre | Ordonnanceur invité et HLE complet non exécutés |
| F07 texture/cache existants | Fraîcheur TIC, durée de vie/ordre des mutex et récupération de vues confirmés sur variantes hôte natives/non natives | Pas d'échantillonnage de pixels FC27 réel |

Ces vérifications ciblent précisément les régressions de **HUD gelé**, **contenu ancien réaffiché**, **queue de présentation désordonnée** et **attente noyau non réveillée**. Les mutations du replay continuent d'être détectées ; le faux NSP reste un **homebrew de recherche au démarrage non vérifié**, sans aucun contenu EA.

**Clôture de ce cycle sans console :** tous les tests FC27/NSW2 ajoutés sont verts sur le dernier run. On ne conclut **ni** à l'absence de saccades matérielles, **ni** à une compatibilité Switch 2 commerciale, **ni** à une correction prouvée de FC27 ; ces résultats sortent du champ vérifiable avec les outils disponibles.
