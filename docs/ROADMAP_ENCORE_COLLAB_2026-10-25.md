# Eden Encore — Roadmap collaborative (2026-10-25)

**Source de vérité du chantier expérimental**, branche `feat/graphics-network-achievements`.  
**Branche de référence console** : `dev/ps5-sparse-jit` (validation technique F01–F06 = 6/6, F07 = test réel FC27 toujours ouvert).  
**Attention au décalage de branches** : la branche expérimentale a été créée depuis `366104d` et **n'intègre pas encore** les huit commits ultérieurs de la branche principale (dont F06). Aucune fusion dans la branche console avant rebase/merge contrôlé, tests complets et qualification matérielle.

## Journal d'exécution — chantier R00/R04

- **R00 code fusionné** : [PR #18](https://github.com/niakw/Prospero.Eden-Encore/pull/18), commit `925661f`. La branche feature possède désormais les huit commits F06 validés. La branche principale n'a pas été modifiée.
- **R04 implémenté sur la branche feature uniquement** : AudioIn PS5 ouvre un `SilentInputStream` qui produit un vrai tableau de samples à zéro, `main.cpp` route les sessions AudioIn vers l'adaptateur, `devices_check.cpp` vérifie les tailles et les échantillons. Le destructeur natif RomFS détache les chaînes `sibling/child/file`; `romfs_check.cpp` teste 32768 voisins fichiers puis répertoires sur pile de 256 KiB.
- **Preuve complémentaire source-extracted** : `tools/check-feature-r04-native-boundary-host.py`, compile les corps *exacts* du C++ AudioIn et RomFS avec UBSan, en `-O0` et `-O2`. Ne remplace pas le test intégré `eden-romfs-check` ou `eden-devices-check`.
- **Première exécution réelle** : le test source-extracted AudioIn/RomFS est passé sur [GitHub Actions #40237741910](https://github.com/niakw/Prospero.Eden-Encore/actions/runs/40237741910), job `source-extracted-native-r04`. L'audit de cohérence a ensuite signalé qu'il comparait encore RomFS à l'ancienne version. Le contrôleur `tools/check-vendor-consolidation-debt.py` a été **adapté pour vérifier exactement la nouvelle destruction non récursive** ; correctif natif non désactivé.
- **Validation non anticipée** : les contrôles de propriété de sources, la prévalidation complète, CodeQL et la compilation PS5 sont en cours de requalification sur le nouveau SHA. R04 n'est pas considéré terminé avant les résultats correspondants.
- **F07** : toujours réservé au test de base FC27 sur `cd4857c8`, sans ces changements.

## Convention de suivi : pas de faux progrès

- Statuts : **À faire**, **Audit**, **Prototype host**, **Intégré natif**, **CI verte**, **Validé console**, **Reporté**. Un document ou un test de politique ne vaut pas intégration fonctionnelle.
- Responsable **Assistant** : investigation, sélection/licences, codes sources, correctifs, compilation, tests hôtes, workflows, nettoyage, documentation, package reproductible et matrice de preuve.
- Responsable **Utilisateur** : choix perceptifs (qualité/style/ergonomie), fourniture de deux PS5 si test multi-console exigé, test console **uniquement après** publication d'un build vert qualifié, retours visuels et logs. Ne pas faire du test console un substitut aux tests d'intégration hôte.
- **Droit de refus** technique : si coût GPU, licence, sérialisation, sécurité ou gameplay insuffisants, garder une option désactivée et tracer la raison. Pas de promesses de 30→60 FPS « natifs ».
- Un seul tableau ci-dessous fait foi ; enregistrer SHA, preuves, test et décision pour chaque livraison.

## Ordre global des jalons et séparation des rôles

| Phase | ID | Livrable réellement attendu | Assistant — exécution/preuve | Utilisateur — intervention | État |
|---|---|---|---|---|---|
| 0 — garde-fous | R00 | Remettre à niveau la branche feature sans détériorer la validation F01–F06 ; verrouiller baseline F07 | Comparaison commits, résolution des conflits, diff natif, gates host, PS5 build, CodeQL | Aucun test demandé | Code fusionné, CI feature en cours |
| 0 — mesure | R01 | Banc de mesures commun : guest FPS, present FPS, displayed FPS, CPU/GPU frametime, latence pad, RAM/VRAM, caches, qualité HUD, audio, pause/mi-temps | Instrumentation bornée, test de non-régression des compteurs, export d'un rapport JSON | Choix des scènes FC27/BOTW, validation A/B seulement au jalon console | À faire |
| 1 — correctifs | R02 | Audit des corrections Swordpdf/ProsperoEden et forks directs : classifications déjà présent/pertinent/incompatible | Comparer patches aux **sources compilées** vendor/overrides, numéro SHA, licences, régression host | Aucun | Audit en cours |
| 1 — correctifs | R03 | Patches ciblés : shader NaN `e34338d`, transferts RADV `1862764` | Modifier la vraie source propriétaire/patch RADV, tests shaders, stress barrières/transferts et rebuild complet | Validation visuelle FC27 uniquement si build global vert | À faire |
| 1 — robustesse | R04 | RomFS vaste arborescence `4f813a3`, AudioIn buffer silencieux `01e81e1`, durée de vie et arrêt corrects | Tests sanitizer à 256 KiB/32768 entrées, AudioIn longueur/données et zéro régression AudioOut | Aucun | Correctifs natifs intégrés ; CI en cours |
| 1 — opportunités | R05 | GPU page table `1390bf5`, RAM allocation, source pins, JIT, locks/pipelines, cache sérialisé et suppression des doubles correctifs | Comparer à Encore : vertex input, 512 draws, striped waits, écriture atomique déjà présents ; n'importer que les écarts | Aucun | Audit |
| 2 — interface de rendu | R06 | **Rendu graphique modulaire** sous trois familles indépendantes : résolution améliorée, fluidité améliorée, rendu neuronal IA | Points d'insertion Vulkan (avant/après HUD), images/queues/fences, copie zero-copy si possible, toggles opt-in, recovery/fallback, profil par jeu | Choix des libellés et défauts | À faire |
| 2 — résolution | R07 | Upscaling : Natif / FSR spatial / FSR temporel 3.1 si infos validées ; AA/FSR et HUD séparé | Vérifier depth, jitter et motion vectors issus du rendu émulé ; calcul du coût GPU et A/B fidélité | Retour sur netteté et textures de FC27/BOTW | À faire |
| 2 — fluidité | R08 | MihawkGen (priorité native PS5), comparaison FSR 3 frame generation, LSFG facultatif si juridiquement/native viable | Porter petites unités isolées, poids + licence, pipeline de présentation, 30→60 *affichés* avec FPS du jeu constants, reset à la pause/menu | Test visuel et ressenti input après CI | À faire |
| 2 — neurones | R09 | **Neural Rendering AMD/Vulkan** : visages/peau/matériaux/lumière, sans modifier les vraies textures jeu | POC Vulkan natif SPIR-V, analyser RDNA2, budget mémoire+compute, pré-upscale vs post-upscale, alpha/UI, couleur HDR/gamma, scènes statiques et mouvement | Qualité artistique et artefacts visage, comparaison captures A/B | Recherche ; pas de runtime |
| 2 — textures | R10 | **Textures HD IA** séparées du rendu neuronal : packs optionnels par Title ID, prétraitement hors PS5 si nécessaire | Pipeline autorisé modèles ouverts (Real-ESRGAN ou équivalent), validation dims/formats/quantification, ram budget, cache, fallback GPU | Choix éventuel des packs / style ; aucun fichier protégé demandé | À faire |
| 3 — multimédia launcher | R11 | Jaquettes Switch 3D front/back recomposées : couche support plastique, vraie composition `cover`, haut du back complet, pas de double tranche ; logo et description GameDB | Cas réels sans box images, chargement LaunchBox **à la sélection uniquement**, placeholder opaque, WebP 80% avec décodeur natif, cache/quotas | Validation visuelle sur maquettes et photos une fois testable | À faire |
| 3 — UI | R12 | Launcher : navigation L1/R1 des tâches de fond, profil/avatar si PS5 l'autorise, FR/EN, formats Go, focus/manette, 3D L2/R2, description README capture réelle | Tests hors console de génération/rendu et snapshots de composition, compat bibliothèque et mémoire | Validation ergonomie, seulement sur build de qualification | À faire |
| 3 — containers | R13 | Formats Switch NSP/XCI/NSZ/XCZ, ZBIC/ZSTD et NRO/NSO/NCA/NAX/KIP, LZ4 selon contenu, mods/DLC/updates sans extraction fragile | Inventaire matrice **par forme d'entrée**, parsers concrets, corpus légal synthétique, fuzz/quotas, chemin happy+failure, pas d'affirmation sans lancement | Essais finaux uniquement des formats que l'utilisateur possède légalement | Audit/À faire |
| 4 — réseau | R14 | Multijoueur privé LDN `eden-room` compatible mode local wireless des jeux Switch | Adapter Swordpdf multiplayer et pont HLE LDN, chiffrement/auth réseau privé, mot de passe session (pas plaintext disque), UDP borné, DNS/IPv4, reconnection, nettoyage | Fournir si possible seconde instance/console, test partie complète | Audit ; non intégré |
| 5 — trophées | R15 | Dépôt isolé de catalogues Switch 1 avec IDs/versions + licences/curation ; progression **manuelle** locale | Extraire module `extras/switch-trophies` quand API/version stable, persistance atomique, UI, notifications, aucun faux déblocage | Définition des règles de trophées souhaitées et visuels | Prototype host partiel |
| 5 — trophées auto | R16 | Déblocage automatique seulement si évènement fiable HLE/observation versionnée ; jamais « tous les jeux » automatiquement sans preuve | APIs d'événements, détecteurs tests, invalidation après mise à jour et faux positifs, mode manuel pour les jeux inconnus | Validation sur jeux pilotes ; autoriser notifications | À faire |
| 6 — PS5SX2 | R17 | Audit technique PS5SX2 : préchargement atlas/jaquettes, packs HD, cache, UX notifications, processus de démarrage | Comparer propriétaires et contraintes mémoire, porter concepts uniquement avec preuves | Aucun avant prototype console | Audit |
| 6 — hygiène | R18 | Nettoyage source/vendor/CMake/tools/test/README, permissions CI, code scanning, secrets/IP, licences, formats, fichiers morts | Rejouer `check-repo-hygiene.py`, `check-active-source-inventory.py`, `check-vendor-consolidation-debt.py`, `check-eden-optimization-coverage.py`, scan de fuites + builds | Aucun | Contrôles host déjà verts ; audit manuel restant |
| 7 — intégration | R19 | Builds indépendants par fonctionnalité avec désactivation sûre + scénarios concurrents (NR+FG, FSR+FG, HUD) | CI hôte/sanitizers, bundle PS5, A/B baseline FC27/BOTW, latence GPU/cache, tableaux comparatifs | Un seul cycle de qualification consolidé, pas un test à chaque commit | À faire |
| 7 — produit | R20 | Décision de fusion, release notes FR/EN, guide sécurité/limites, suivi par fonctionnalité | Merge seulement des modules validés, changelog/permissions et rollback, package avec SHA | Acceptation console matérielle par l'utilisateur | À faire |

### Séquence critique et dépendances

`R00 → R01 → R03/R04/R05 → R06 → {R07,R08,R09,R10} → R19 → R20`.

En parallèle sans modifier la branche F07 : `{R11,R12,R13}`, `R14`, `{R15,R16}`, `R17/R18`. LDN et trophées ont des tests indépendants de la frame generation.

**Point de départ le plus rationnel** : compiler et mesurer les fixes avérés puis construire une abstraction Vulkan commune aux modules de rendu. Sans ownership clair des images/fences/swapchain, MihawkGen+FSR+NR risque de recréer les défauts de HUD et les blocages de FC27.

## Registre de recherche — IA « DLSS 5-like » sur AMD (état au 25/10/2026)

Ne pas confondre **RDNA2 PC**, **Vulkan PC** et **PS5 native**. Aucune des implémentations NR suivantes n'a été qualifiée par nous sur la PS5 13.60 ; ne pas expédier d'exécutables DLL Windows, de modèles propriétaires ou de poids extraits d'un runtime NVIDIA.

| Référence | Pourquoi | Blocage / preuve à demander | Classement |
|---|---|---|---|
| [mochizuki0323/DLSSNR-AMD](https://github.com/mochizuki0323/DLSSNR-AMD) | Réimplémentation compute Vulkan SPIR-V, sélection de petits modèles ; c'est la piste la plus proche d'un module natif | Testé publiquement sur RX 9070 XT RDNA4 et Mesa Linux, modèles obtenus séparément d'une DLL NVIDIA ; RDNA2 sans validation | **R09-A** : étude prioritaire du scheduler/compute et des licences |
| [shakhbazian/OptiScaler-RDNA2NR](https://github.com/shakhbazian/OptiScaler-RDNA2NR) | Travail GPU `gfx1030` RDNA2 et traitement détails/couleurs avant ou après upscale | RX 6900 XT PC HIP/DirectX12 ≠ PS5, prix GPU fortement sensible à résolution ; modèles non librement distribuables | **R09-B** : algorithmes/quantification RDNA2 |
| [danielblnc/DLSS-NR-on-AMD](https://github.com/danielblnc/DLSS-NR-on-AMD) | Port NR AMD incluant RDNA2 expérimental et réglages de structure/peau/teinte | HIP 7, Windows/DX12, modèles utilisateur ; code/livrables/propriété intellectuelle à auditer | **R09-C** : référence fonctionnelle, pas binaire embarqué |
| [zmodelerlover/OpenNR-ReShade](https://github.com/zmodelerlover/OpenNR-ReShade) et [kibblerz/DLSS5-Reshade-AIO](https://github.com/kibblerz/DLSS5-Reshade-AIO) | Hooks rendu, mouvement estimé et interface des effets | ReShade/injection Windows ; port PS5 nul à ce jour | **R09-D** : idées d'intégration seulement |
| [Overclockers/DLSSNR-AMD-upstream](https://github.com/Overclockers/DLSSNR-AMD-upstream) | Optimisations Vulkan et comparaison quantitative au modèle original | Bibliothèque modèle, RDNA4 uniquement validé | **R09-E** : vérification mathématique/visuelle |
| [3zwr1/AMD-NR---OptiScaler](https://github.com/3zwr1/AMD-NR---OptiScaler) | Masque personnage, profils de teinte, mise à l'échelle du modèle, réduction charge, parallélisme | Ecosystème Windows/HIP, nombreuses dépendances/licences | **R09-F** : UX, stylisation et scheduler |
| [maanHimself/OpenDLSS-NR](https://github.com/maanHimself/OpenDLSS-NR) | Topologie 71 blocs et version browser/WebGPU sans Tensor Cores | Modèle ~141 MiB, coût et droits des poids, GPU RDNA2 | **R09-G** : portabilité algorithmique |
| [bloc97/Anime4K](https://github.com/bloc97/Anime4K) | Mode netteté/ligne stylisée à faible coût et shaders portables | Favorise dessin/anime, pas reconstruction de visage photoréaliste | **R09-Lite** : solution sûre si gros NR trop lent |
| [eFMann/shadPS4-Bloodborne-DLSS-FSR](https://github.com/eFMann/shadPS4-Bloodborne-DLSS-FSR) | Vraie stratégie d'émulateur : profondeur + mouvement caméra/personnage, jitter, UI après upscale, FSR FG | Code shadPS4 PC/PS4 spécifique non drop-in et statut licence à confirmer | **R07/R08** : design d'interface |
| [mihawk-99/PS5_MihawkGen](https://github.com/mihawk-99/PS5_MihawkGen) et [Swordpdf/ProsperoEden `650306c`](https://github.com/Swordpdf/ProsperoEden/commit/650306c9fd4b309720e87b58b2e5f8311f02badc) | Petite interpolation par réseau GPU PS5 avec source, shaders, outils et tests | Vérifier mesures réelles sur 13.60, licence et compat backend | **R08-A** : cible FG prioritaire |
| [GPUOpen FidelityFX SDK](https://github.com/GPUOpen-LibrariesAndSDKs/FidelityFX-SDK) | FSR 3.1, FG et APIs publiques | Ne pas confondre AMD Redstone FSR4/ML DX12/RDNA4 et anciens chemins FSR3 compatibles PS5 ; motion/depth difficiles | **R07/R08-B** |

**NR = transformation des pixels** (matériaux/peau/éclairage) ; **textures HD = ressources GPU modifiées**, éventuellement produites par IA en amont ; **FG = interpolation d'images** ; **SR = reconstruction/résolution**. Ces fonctions sont composables, mais multiplient potentiellement la latence et le coût.

### Contrat de validation graphique

1. A/B de la **même frame source** : fidélité couleur, rendu personnage, tissus, visage, texte, HUD, textures et déformations.
2. Séries animées : stabilité temporelle, occlusions, doubles contours, entrées manette, pause/reprise, mi-temps, cache shader, changement de résolution, retour menu.
3. Chiffres séparés : `guest_fps`, `present_real_fps`, `displayed_fps`, `framegen_ms`, `neural_ms`, `gpu_frame_ms`, `input_to_photon` ou proxy clairement étiqueté, RAM/VRAM.
4. Aucune option ne peut changer la sémantique des JIT/sync/audio ou se présenter comme « 60 FPS de gameplay » si le jeu reste à 30 FPS.
5. Retour au mode normal sans perte de données si pilote ne supporte pas un mode, mémoire insuffisante, échec shader, mauvais modèle ou latence insupportable.
6. Vérifier licences **source, poids, datasets et binaires** séparément ; noms « AMD Neural Rendering » ou « Encore Neural » en interface, jamais fausse appellation DLSS NVIDIA natif.

## Bons correctifs des forks : éviter les re-cherry-picks

- **Déjà vérifiés chez Encore (ne pas recopier)** : fix vertex dynamique [`1b6ffb8`](https://github.com/Swordpdf/ProsperoEden/commit/1b6ffb887), limite 512 draws [`0dd9dd0`](https://github.com/Swordpdf/ProsperoEden/commit/0dd9dd0fd), caches pipeline atomiques [`207e77f`](https://github.com/Swordpdf/ProsperoEden/commit/207e77fe4), locks pipeline mutualisés [`737152f`](https://github.com/Swordpdf/ProsperoEden/commit/737152f6f).
- **A développer sous tests** : NaN shader `e34338d`, transferts RADV `1862764`, RomFS wide-tree `4f813a3`, AudioIn silence `01e81e1`. Les sources maintenues Encore incluent actuellement un destructeur RomFS par défaut et `NullSinkStreamImpl` côté AudioIn.
- **À auditer et non activer directement** : sparse address `1390bf5`, vitesse par jeu `23e0424`, packs/update/cheats `47cce6b`/`da39bc4`.
- **PS5SX2** : préchargement des ressources, polices/atlas et notifications trophées sont des inspirations UX, pas un code exécutable Switch transposable.

## Porte de sortie : qui fait quoi et quand on teste

**Assistant publie un paquet de preuves avant toute demande de test** :
- SHA stable + liste exacte des fichiers modifiés + état des conflits avec F01–F06 ;
- build PS5 + CI fast/full + CodeQL + tests host propres à chaque fonctionnalité ;
- modifications visuelles documentées et paramètres de rollback ;
- journal technique : correctifs validés, refusés, raisons, et **compteurs « reste à intégrer » distincts de « reste à qualifier »**.

**Utilisateur ne teste la console qu'à trois points utiles** :
1. **F07 baseline** : FC27 avec `dev/ps5-sparse-jit` code validé `cd4857c8`, enregistrer jeu/firmware/réglages, freeze/HUD/texture/frametime/input ; cela ne valide aucune feature branch.
2. **RC Graphics** : version native stabilisée de R03/R06/R07/R08/R09, A/B en conditions identiques, qualité/cadence/manette/HUD.
3. **RC fonctionnalités** : R11–R17 réunis, puis test deux instances pour LDN et trophées réels par jeux pilotes.

Pas de durée chiffrée inventée : la fin d'une phase dépend de ses **preuves** et de la disponibilité réelle des outils/hardware.

## Compteur au moment de la création de ce document

- **F01–F06 pré-console** : 6/6 prouvés sur tests host, build PS5 et sécurité GitHub sur `cd4857c8`.
- **F07 vraie session de jeu** : pas encore réalisée.
- **Branche feature** : audit en cours, `framegen_capabilities.h` (contrat de choix, pas moteur), catalogues de trophées vides + tests CI hôtes ; pas de FG/NR/FSR temporel/LDN natif intégré.
- **R00–R20** : toutes les lignes sont un **backlog**, non un 21/21 validé. Le présent document accomplit uniquement la planification/traçabilité.
