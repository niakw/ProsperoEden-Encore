# Eden Encore — protocole obligatoire de diagnostic upstream-first

**Date de référence : 13 novembre 2026.** Dépôts de livraison : [moteur](https://github.com/niakw/ProsperoEden-Encore) et [vendor](https://github.com/niakw/Prospero.Eden-Encore-vendor). Ce protocole complète [la roadmap #15](https://github.com/niakw/ProsperoEden-Encore/issues/15). Il ne certifie aucun jeu ni aucune correction sur console.

## Règle impérative : chaque anomalie passe par les sources et les upstream

À **chaque** incident (nouveau ou récurrent), et avant de proposer un correctif spéculatif, inspecter les **issues, commentaires, PR ouvertes et fusionnées, diffs, commits, tags/releases et branches** des dépôts pertinents : Eden et son issue tracker, Eglantine, Lichii, nxnative, forks PS5, upstream des dépendances (Mesa/RADV, Dynarmic, FFmpeg, codecs, NVDEC, etc.). Les sources primaires et la chronologie du correctif priment sur un titre d'issue ressemblant.

Cette règle vaut pour **toute** la matrice utilisateur : crash système/guest NS1 et NS2, PC=4, chargement infini/première image, texture/alpha/géométrie, textes/font atlas/HUD/vidéos, saccades frame pacing/pipelines, mise en cache froide/chaude et début de match, JIT, GPU sparse, RAM, shader cache persistant, jaquettes/visuels, chargement du launcher, retour après jeu, paramètres et aides, traductions, wallpaper/galerie, compilateur, CodeQL/Dependabot et packaging.

### Protocole de preuve pour chaque ligne du registre

1. **Incident précis** : titre/TitleID, version de jeu, firmware PS5, configuration (AA/résolution/filtrage/cache), horodatage, SHA du **binaire installé**, SHA moteur, gitlink vendor, sortie/stderr/heap et segment exact du lancement. Les logs privés restent privés.
2. **Distinguer les couches** : plantage natif PS5 vs faute invitée ; CPU guest vs GPU guest ; écran de chargement Vulkan du launcher vs présentation de la première image du jeu ; corruption de données vs simple problème d'affichage. Ne jamais fusionner deux incidents sur la seule signature PC=4.
3. **Chercher en amont** : requêtes par symptôme, appels/fonctions, TitleID, adresse et signatures de log, puis inspecter *code et discussion*. Enregistrer PR ouverte/merge, commit, date, correctif exact et limitations. Privilégier des diffs ciblés plutôt qu'un gros sync de fork.
4. **Vérifier l'owner réellement compilé** : CMake du moteur PS5 + overrides installés + sources vendor sélectionnées et SHA. Les fichiers sources historiques/non sélectionnés ne prouvent pas l'état de l'eboot. Comparer ABI/architecture et support Vulkan RDNA2/PS5, sûreté des fences, locks, mapping et cycle de vie.
5. **Décider** : déjà intégré / applicable à porter / piste à instrumenter / hors champ / régression probable / preuve insuffisante. Décrire les hypothèses rejetées. Ne pas marquer « corrigé » au seul motif qu'un autre émulateur a un patch.
6. **Port ciblé et vérification** : tests négatifs et positifs sur le vrai owner, CI host/sanitizers, source-integrity, rendu et perf. Sans désactiver une CI ou supprimer des warnings. Native PS5 et test console seulement selon la priorité/gates utilisateur en vigueur. Noter build SHA, artefacts, symboles, mesures comparables.
7. **Clôture et hygiène** : issue fermée uniquement après ses critères de sortie ; PR fusionnée uniquement si dépendances/CI/compatibilité sont qualifiées ; supprimer ref/branche seulement après compare main et récupération du travail distinct sur **moteur ET vendor**. Préserver l'historique et les SHA. Un build vert n'est pas un gameplay vert.

## Matrice de diagnostic et métriques requises

| Axe | Observations à isoler | Sources et conditions de sortie |
| --- | --- | --- |
| NS1 FC27 — saccades/début de match | première visite vs deuxième, pipeline wait, shader miss, cache buffer/texture lock, GPU fence et CPU guest ; compter frames >16.7/33.3/50/100 ms, p50/p95/p99 ; cache « warm » vérifié par présence réelle, pas message « ready » | [moteur #100](https://github.com/niakw/ProsperoEden-Encore/issues/100), [Lichii pipeline warm #579](https://github.com/zortos293/Lichii/pull/579), [Lichii shader reuse #1378](https://github.com/zortos293/Lichii/pull/1378). NVIDIA/Linux et branches ouvertes ne valent pas qualification PS5 |
| NS1 FC27 — textures/bras/maillots/HUD | sampler/descripteurs, barrières, MSAA offset non nul, écritures font atlas, locale guest, texture invalidation, draw sans profondeur | [vendor draft #108](https://github.com/niakw/Prospero.Eden-Encore-vendor/pull/108), [Lichii #1296](https://github.com/zortos293/Lichii/pull/1296), [Lichii #1447](https://github.com/zortos293/Lichii/pull/1447). Aucune causalité FC27 établie |
| NS1 FC27 — intro vidéo noire | NVDEC guest → paquets H.264/VP8/VP9 acceptés ou EAGAIN → frames de sortie → upload texture → présentation | [vendor draft #107](https://github.com/niakw/Prospero.Eden-Encore-vendor/pull/107). [Lichii #809](https://github.com/zortos293/Lichii/pull/809) concerne **NS2 vdecsvc**, ne pas transplanter au décodeur NS1 |
| NS2 Bananza PC4 | vraie branche invitée et premier accès invalide, FS/AM commands précédentes, ExeFS/NPDM cohérents, RomFS update-only réellement accessible | [moteur #123](https://github.com/niakw/ProsperoEden-Encore/issues/123), [Eglantine #335](https://github.com/Eglantine-Community/Eglantine/issues/335), [vendor draft #105](https://github.com/niakw/Prospero.Eden-Encore-vendor/pull/105), [vendor #109](https://github.com/niakw/Prospero.Eden-Encore-vendor/pull/109). PC4 seul n'identifie pas le sous-système |
| NS2 MKW chargement infini | distinguer PresentVulkanLoading du GPFIFO/QMD guest, retraite CPU, attentes SVC/threads, GPU sparse, locks, première image guest | [Lichii #1413](https://github.com/zortos293/Lichii/pull/1413) a supprimé un deadlock sparse GPU vérifié sur PC ; **Encore n'a pas encore prouvé le même cycle**. [Eglantine #609](https://github.com/Eglantine-Community/Eglantine/pull/609) ne vaut que pour pacing après rendu |
| Fermeture/reprise | ordre arrêt guest / GPU / services / mémoire, attente de sémaphore avec pointeur de session antérieure, autoréactivation après crash | [moteur #97](https://github.com/niakw/ProsperoEden-Encore/issues/97), [Lichii #1592](https://github.com/zortos293/Lichii/pull/1592), [#1450](https://github.com/zortos293/Lichii/pull/1450). Pas de copie sans retrouver l'owner équivalent |
| Launcher et média | premier rendu Home, tuiles carrées, jacket avant init Vulkan, changements de sélection, metadata-cover d'abord puis box-back/screens uniquement sur demande, decode/upload et retour FC27 | [moteur #101](https://github.com/niakw/ProsperoEden-Encore/issues/101), [#124](https://github.com/niakw/ProsperoEden-Encore/issues/124), drafts [#122](https://github.com/niakw/ProsperoEden-Encore/pull/122), [#126](https://github.com/niakw/ProsperoEden-Encore/pull/126), [#127](https://github.com/niakw/ProsperoEden-Encore/pull/127). Captures PS5 JXR sélectionnées seulement ; n'inférer aucune accélération de la CI source |
| Build, sécurité | recompilation propre et sans cache pour mesurer 510 warnings de référence, ne pas contourner la vérification PSBC, CodeQL #79–85 sur le SHA effectivement analysé | [moteur #108](https://github.com/niakw/ProsperoEden-Encore/issues/108), [#118](https://github.com/niakw/ProsperoEden-Encore/issues/118), [draft #107](https://github.com/niakw/ProsperoEden-Encore/pull/107). Le correctif NIR #107 reste bloqué par la vérification d'intégrité PSBC |

## Incidents de référence non interchangeables

- Archive console privée 1302261840.zip, application installée **f859b1c514a0430c078f25164b9dfa2a4ccb3c2e**. Le fichier stderr de MKW contient un **préfixe Bananza** : faute invitée PC=0x4/LR=0 pour Bananza uniquement ; le vrai MKW atteint guest_run_begin, affiche 10s/30s de chargement et guest_frame_handoff=0. Un submit RADV du loading ne prouve pas une commande du jeu.
- FC27 : la dernière session atteint le match mais conserve vidéo noire, HUD glyphes/numéros manquants, textures/alpha corrompues et fort hitching au premier match. Les 108 fenêtres Vulkan/34 waits pipeline et le pire frame à 835.9 ms proviennent d'un **autre build**, donc ne pas réattribuer ces mesures au binaire f859b1c.
- Le crash natif PS5 SIGSEGV antérieur et la source de memset shared 17 MiB corrigée sont des incidents distincts. Un grand bloc mémoire libre ne prouve ni absence de fuite ni absence de problème d'allocation.

## Inventaire GitHub au 13 novembre (instantané, à réinterroger avant toute action)

- **Moteur main d62d75a83b5089f2b1a11c533313b69f70de661c** : issues ouvertes #15, #97, #100, #101, #108, #118, #123, #124 ; PR ouvertes #107 (warning NIR), #122 (gallery), #125 (ExeFS), #126 (JXR), #127 (lazy Library) ; 6 branches total dont main. **#122 → #126 → #127 est une pile**, ne pas fusionner la dernière directement dans main.
- **Vendor main 1ec7b429238d1175a76dc94b7c0a7f1c2eb62864** : 0 issue ouverte ; PR ouvertes #105 (RomFS), #106 (codec JXR), #107 (NVDEC), #108 (MSAA offset), #109 (CMIF UID) ; 7 branches dont main. La ref feat/ps5-jxr-selected-only-decode pointe sur le même SHA que main, mais confirmer dépendances et policy avant retrait.
- Le correctif CodeQL stb vendor #101 est **déjà fusionné et gitlink pin équivalent** sur moteur/main ; ne pas ouvrir un double repin. CodeQL doit réellement passer les sept alertes en fixed avant fermeture de #118.
- **Aucune de ces dix PR ne doit être proclamée testée console** : les descriptions mentionnent source/host et des vérifications manquantes. Les PR et issues ne sont pas du « déchet » tant que leur travail ou leurs preuves sont actifs.

## Format minimal d'un suivi nouveau

| Incident | SHA/log et repro | upstream (issue/PR/commit) | owner PS5 comparé | décision + patch SHA | tests (source/host/native/console) | statut et issue |
| --- | --- | --- | --- | --- | --- | --- |
| Exemple : MKW ne passe pas loading | f859b1c ; guest_frame_handoff=0 | Lichii #1413 | GPU sparse PS5 à confronter | piste, **pas un port validé** | preuve deadlock PS5 manquante | **OPEN #123** |

**Règle de vocabulaire :** distinguer « repéré en amont », « confirmé dans source », « patch rédigé », « CI hôte verte », « build natif vert », « testé sur PS5 », « jeu fonctionnel ». Ne jamais remplacer plusieurs de ces états par « terminé ».
