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
- Le vrai chargeur NSP attend des archives programme **NCA**. Ce PFS0 **n’en contient aucune** : **il n’est pas jouable, installable comme titre ni capable de produire des FPS/du HUD réel**.
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

## 6. Bloquants avant une véritable conclusion PS5

1. **Démarrer un ExeFS autorisé dans le vrai `KProcess` PS5** et relever les PID, autorisations et appels HLE du homebrew. La réussite séparée du JIT et du parseur NPDM ne prouve pas cette étape.
2. **Instrumenter le contenu**, pas seulement le rythme : identifiant de génération, compteur de textures/HUD, CRC ou hachage de la surface rendue, identifiant de buffer présenté. Détecter les images réémises sans progression.
3. **Relier le chemin CPU → GPU** : écriture invité, DMA/remap, invalidation TIC/TSC, enregistrement et lecture de vue, pipeline, présentation, fence, et temps d’attente, avec marqueurs de scène pause/mi-temps.
4. **Tester sur console** une build expérimentale explicite, sans confondre ses timings avec les chiffres historiques : rafales shader/JIT, HUD noir, saccades en match, écran pause et gel de fin de période.
5. **Vérifier les régressions réelles Switch 1** avant toute généralisation vers NSW2 ; la compatibilité Switch 2 complète et la prise en charge de jeux commerciaux **ne sont pas démontrées**.

### Mise à jour de validation

Au moment de la première rédaction, le run complémentaire [host guards 41149975928](https://github.com/niakw/ProsperoEden-Encore/actions/runs/41149975928) a **1 job vert et 1 job de compilation en cours**, sans échec observé. Il doit être marqué séparément une fois GitHub Actions terminé ; son statut ne change pas le résultat **2/2 vert** du banc stress `41149975993`.

**Règle de suivi :** conserver systématiquement SHA de source, run CI, données réellement mesurées, données simulées, cas négatifs, niveau de preuve, et validations PS5 encore ouvertes. Ne jamais transformer un succès hôte en affirmation de FPS ou de textures corrigées sur console.
