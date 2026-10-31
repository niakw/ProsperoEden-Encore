<table width="100%">
  <tr><td align="center">
    <strong>🌐 LANGUAGES</strong> &nbsp; · &nbsp; <a href="../../README.md">English</a> &nbsp; · &nbsp; <a href="../../README.md">English UK</a> &nbsp; · &nbsp; <a href="README.zh-Hans.md">简体中文</a> &nbsp; · &nbsp; <a href="README.zh-Hant.md">繁體中文</a> &nbsp; · &nbsp; <a href="README.es-419.md">Español LatAm</a> &nbsp; · &nbsp; <a href="README.es.md">Español ES</a> &nbsp; · &nbsp; <strong>Français</strong> &nbsp; · &nbsp; <a href="README.fr-CA.md">Français CA</a> &nbsp; · &nbsp; <a href="README.pt-BR.md">Português BR</a><br>
    <a href="README.pt-PT.md">Português PT</a> &nbsp; · &nbsp; <a href="README.ru.md">Русский</a> &nbsp; · &nbsp; <a href="README.de.md">Deutsch</a> &nbsp; · &nbsp; <a href="README.ja.md">日本語</a> &nbsp; · &nbsp; <a href="README.ko.md">한국어</a> &nbsp; · &nbsp; <a href="README.it.md">Italiano</a> &nbsp; · &nbsp; <a href="README.th.md">ไทย</a> &nbsp; · &nbsp; <a href="README.pl.md">Polski</a> &nbsp; · &nbsp; <a href="README.nl.md">Nederlands</a> &nbsp; · &nbsp; <a href="../../LANGUAGES.md"><strong>All languages</strong></a>
  </td></tr>
</table>

<table width="100%">
  <tr>
    <td width="21%" align="center" valign="middle"><a href="../../README.md"><img src="../../assets/icon0.png" alt="Prospero.Eden Encore logo" width="148"></a></td>
    <td width="79%" align="left" valign="middle">
      <h1>Prospero.Eden Encore</h1>
      <p><strong>L'émulation native, pensée pour jouer depuis son canapé.</strong></p>
      <p>Un fork d'émulateur natif PS5 pour le firmware 13.60 : chargeurs NSP, XCI, NSZ, XCZ, NRO, NSO, NCA, NAX et KIP, décompression LZ4 + ZBIC/zstd, interface TV et compilation reproductible.</p>
      <p><kbd>Firmware 13.60 · testé sur PS5</kbd> &nbsp; <kbd>Vulkan + OpenGL</kbd> &nbsp; <kbd>Interface TV</kbd> &nbsp; <kbd>Dynarmic</kbd></p>
    </td>
  </tr>
</table>

<table width="100%">
  <tr>
    <td align="center"><a href="https://github.com/niakw/ProsperoEden-Encore/releases"><strong>Télécharger</strong></a></td>
    <td align="center"><a href="INSTALL.fr-FR.md"><strong>Installer</strong></a></td>
    <td align="center"><a href="#getting-started"><strong>Démarrer</strong></a></td>
    <td align="center"><a href="#compatibility"><strong>Compatibilité</strong></a></td>
    <td align="center"><a href="#faq"><strong>FAQ</strong></a></td>
    <td align="center"><a href="../../TROUBLESHOOTING.md"><strong>Aide</strong></a></td>
    <td align="center"><a href="https://github.com/niakw/ProsperoEden-Encore/blob/feat/graphics-network-achievements/docs/ROADMAP_ENCORE_COLLAB_2026-10-25.md"><strong>Roadmap</strong></a></td>
  </tr>
</table>

<p align="center"><img src="../../assets/screenshots/eden-encore-home-sample-art.png" alt="Eden Encore Home in English with the original wallpaper and fictional sample game artwork" width="860"></p>

<sub>Aperçu : les jeux, jaquettes illustrées et descriptions sont **fictifs** et servent uniquement à présenter l’interface. La capture est produite par le véritable lanceur Encore.</sub>

> [!IMPORTANT]
> **FC27 — tableau maître :** [priorités F07 P0/P1/P2, sparse JIT et validation matérielle](../../docs/FC27_F07_MASTER_TRACKER.md). Les [critères F01–F06 validés sur hôte](../../docs/FC27_EXIT_GATES_2026-10-22.md) ne prouvent pas la jouabilité sur console. Le nombre de sources examinées ne mesure pas les optimisations restantes.
>
> **Firmware recommandé/testé pour Encore : 13.60, seule version effectivement essayée sur notre PS5.** Les versions **antérieures devraient pouvoir fonctionner dans certains environnements homebrew compatibles**, mais cela reste **à vérifier sur Encore** et aucun firmware minimum n'est établi. Les firmwares ultérieurs ne sont pas qualifiés non plus. Même sur 13.60, les saccades et gels en jeu restent à résoudre. « Recommandé » ne signifie **pas** qu'il faut mettre à jour sa console.
>
> **Avant un test console :** [audit des logs, mises à jour, build et fichiers à conserver](../../docs/PRETEST_AUDIT_2026-10-14.md). Vérifier le SHA exact du paquet et des symboles.

---

<a id="getting-started"></a>
## Démarrer en quatre étapes

1. Télécharger une archive **complète** des [Releases Encore](https://github.com/niakw/ProsperoEden-Encore/releases). Une CI verte ne prouve pas une version testée sur console.
2. **Sauvegarder** l’ancienne application `/data/homebrew/PPSA99008/`, le stockage `/data/prosperoeden/` et les supports externes. Le port d’origine partage le **même identifiant PS5**.
3. Suivre [le guide d’installation français](INSTALL.fr-FR.md) pour ZIP/FTP ou FFPFSC/ShadowMountPlus. Copier **tout** `PPSA99008/` et `ui/lang/`, jamais uniquement `eboot.bin`.
4. Contrôler **Settings → Storage / Language**, la bibliothèque et les sauvegardes. En cas de souci, consulter le [dépannage (EN)](../../TROUBLESHOOTING.md).

**Seul le firmware 13.60 a été testé sur console.** Aucun minimum antérieur n’est qualifié ; ce n’est pas un conseil de mise à jour. [18 choix linguistiques](../../LANGUAGES.md).

---

## ✨ Pourquoi Encore ?

Une bonne expérience d'émulation ne se résume pas à lancer un jeu. Il faut pouvoir naviguer depuis la télévision, comprendre ses réglages, retrouver ses données et identifier précisément les problèmes. **Pour commencer :** [installation](../../INSTALL.md), [limites actuelles](#-compatibilité-et-limites) et [questions fréquentes](#faq).

| | Ce qu'apporte Encore |
| --- | --- |
| **🎮 Interface TV** | Interface pensée pour la télévision, jeux récents, visuels, bibliothèque et navigation manette. |
| **🧩 Fichiers et compression** | Sélection NSP, XCI, NSZ, XCZ, NRO, NSO, NCA, NAX, KIP ; décodage LZ4 et ZBIC/zstd. Certains fichiers ne démarrent qu'avec des contenus supplémentaires. |
| **🛟 Mode récupération** | Safe Launch temporaire, remises à zéro confirmées et migration sécurisée. |
| **⚙️ Profils par jeu** | **Minimum, Recommandé, Haute, Ultra**, puis **Personnalisé** en cas de modification. |
| **🎨 Graphismes natifs** | Vulkan/RADV et OpenGL, filtres, mise à l'échelle, anticrénelage et caches. |
| **🔎 Diagnostics** | Mesures CPU/JIT, frames lentes, mémoire, verrous et services invités, au-delà du simple compteur FPS. |
| **🔐 Intégration maîtrisée** | Sources épinglées, vérification des archives compilées et précautions d'accès aux fichiers. |

<details>
<summary><strong>Qu'est-ce qui change par rapport au projet d'origine ?</strong></summary>

<br>

| Domaine | Évolution Encore |
| --- | --- |
| **Firmware** | Qualification prioritaire sur **13.60**, sans extrapolation aux autres versions |
| **Interface** | Accueil, bibliothèque, récents et paramètres rapides repensés pour la TV |
| **Chargement** | NSP, XCI, NSZ, XCZ, NRO, NSO, NCA, NAX, KIP ; LZ4 + ZBIC/zstd |
| **Récupération** | Safe Launch sur une seule session, sans écraser les préférences enregistrées |
| **Stockage** | Même structure de dossiers sur stockage interne ou externe ; migration prudente |
| **Manette** | Profils du launcher et réglages personnels ; actions enregistrées en jeu encore à qualifier |
| **Graphismes** | Adaptations GPU vérifiées du code source jusqu'à l'archive native |
| **Qualité** | Tests hôtes, compilation native et validation sur console clairement distingués |

Encore est un dépôt communautaire indépendant, issu d'un fork historique, et non une version officielle des projets amont.

</details>

---

## 🗺️ Roadmaps, branche fonctionnalités et mises à jour

- **[Roadmap collaborative complète R00–R25](https://github.com/niakw/ProsperoEden-Encore/blob/feat/graphics-network-achievements/docs/ROADMAP_ENCORE_COLLAB_2026-10-25.md)** sur la [branche de développement des fonctionnalités](https://github.com/niakw/ProsperoEden-Encore/tree/feat/graphics-network-achievements) : FSR, génération de frames, AA, thèmes, interface, réseau, trophées, contenus et **mise à jour intégrée R21**. **Une spécification ou un prototype n’est pas une fonction déjà livrée.**
- **[Branche expérimentale Switch 2](https://github.com/niakw/ProsperoEden-Encore/tree/research/ns2-ps5-compatibility)** avec son [rapport technique](https://github.com/niakw/ProsperoEden-Encore/blob/research/ns2-ps5-compatibility/docs/NS2_PS5_FEASIBILITY_2026-10-30.md) : chargeurs, CPU/IR et shaders NSW2, **sans intégration au paquet PS5 actuel**.
- **[Priorités PS5/F07 sur main](../../docs/FC27_F07_MASTER_TRACKER.md)** : référence actuelle des optimisations et de la stabilité du moteur PS5.
- **Les mises à jour du projet natif ProsperoEden ne sont pas synchronisées automatiquement.** Encore part de **ProsperoEden v1.000.040** ([base documentée](../../docs/FORK_NOTES.md)) et reprend individuellement les correctifs utiles après audits ([registre d’écarts](../../docs/UPSTREAM_GAP_REGISTER_2026-10-14.md)). **L’updater Encore R21 est prévu, mais n’est pas encore livré.**

---

## 📦 Formats de jeux et compression

| Catégorie | Formats | Portée actuelle |
| --- | --- | --- |
| Jeux dans la bibliothèque | **NSP** (`.nsp`), **XCI** (`.xci`) | Détection et lancement déjà présents |
| Jeux compressés | **NSZ** (`.nsz`), **XCZ** (`.xcz`) | Lecteur NCZ expérimental, jeux, mises à jour et DLC ; compilation native et console encore à qualifier |
| Compression interne des exécutables | **LZ4**, **ZBIC / zstd** | Décompression des segments NSO ; **ce ne sont pas des extensions de jeux** |
| Fichiers chargeables directement | **NRO, NSO, NCA, NAX, KIP** | Sélectionnables ; le démarrage dépend des données complètes et compatibles. |

**Les dossiers ExeFS décompressés** sont également détectés lorsque `roms/<titre>/` contient les fichiers réguliers `main` et `main.npdm`, sans liens symboliques. Ils apparaissent sous `EXEFS` dans la bibliothèque ; c'est un agencement de dossier, pas une extension supplémentaire.

La compression NCZ par blocs se lit directement. Un fichier « solid » peut être décompressé temporairement dans `/data/prosperoeden/user/cache/nsz/`, ce qui nécessite de l'espace pour sa taille décompressée. La lecture des métadonnées hors jeu conserve des fragments vérifiés et bornés. Il s'agit d'un support en développement, **pas encore d'une version qualifiée sur console**.

[Guide de stockage et des fichiers compressés](../../INSTALL.md#compressed-nsz-and-xcz-games) · [Lecteur et tests](../../headless/ncz.h) · [Matrice complète des formats](../../docs/CONTENT_FORMAT_MATRIX_2026-10-23.md)

---

## 🚀 Installation

> [!TIP]
> Pour une version publiée et qualifiée, commence par [les releases GitHub](https://github.com/niakw/ProsperoEden-Encore/releases). Les artefacts d'une CI verte sont des **versions de développement**, pas une garantie de fonctionnement en match.

Le paquet ZIP contient le dossier natif `PPSA99008/`. Une image FFPFSC peut également être proposée selon la release.

**Installation du dossier :** `/data/homebrew/PPSA99008/`.

**Stockage persistant par défaut :** `/data/prosperoeden/` avec `keys/`, `firmware/`, `roms/`, `updates/`, `mods/`, `save-import/` et `save-export/`.

Avec un disque externe, seule la racine change : les sous-dossiers restent identiques. **Ne supprime pas les anciennes données persistantes avant une migration**. Aucun jeu, clé, firmware propriétaire ou DLC n'est fourni.

**Pour remplacer le dossier natif ProsperoEden :** les deux applications partagent l'identifiant `PPSA99008` et le dossier `/data/homebrew/PPSA99008/`. **Sauvegarde intégralement le dossier de l'application (ancien `assets/` inclus), `/data/prosperoeden/` et toute racine externe** ; copie ensuite le dossier complet de l'application Encore à la place des fichiers natifs **sans supprimer les données historiques**, puis vérifie la migration au lancement. Ce n'est **pas une seconde installation indépendante**. Procédure détaillée : **[passer de ProsperoEden natif à Encore](../../INSTALL.md#upgrade-from-native)**. Un ZIP du port natif amont n'est pas une mise à jour Encore.

**Guide complet :** [INSTALL.md](../../INSTALL.md) · [Compiler Encore](../../docs/BUILDING.md) · [Aide](../../SUPPORT.md).

---

## 🎛️ Réglages et navigation

| Fonction | Description |
| --- | --- |
| **Accueil, Bibliothèque, Récents** | Navigation à la manette et métadonnées des jeux, avec repli hors ligne |
| **Lancement animé** | Véritable boîtier 3D : chaque scan recto/verso disponible reste prioritaire ; à défaut, reconstruction native avec artworks, captures distinctes, titre et descriptif, sans génération d'image. [Détails](../../docs/LAUNCH_CASE_ARTWORK.md) |
| **Paramètres rapides** | Ajustements vidéo et préférences par titre |
| **Profils vidéo** | **Minimum → Recommandé → Haute → Ultra**, puis **Personnalisé** |
| **Safe Launch** | Pour une seule session : OpenGL, 1×, 1080p, bilinéaire, portable, 60 Hz, mods désactivés |
| **Manettes** | Profils du launcher, vibrations, zones mortes et préférences |
| **Langues** | Catalogues de l'interface pour **29 langues** |
| **Image** | Définition, filtrage, mise à l'échelle, netteté et anticrénelage |

Le mapping physique du launcher et la configuration des actions mémorisée **à l'intérieur d'un jeu** sont deux mécanismes distincts. Le bon chargement des actions personnalisées pendant le match n'est pas encore démontré.

<details>
<summary><strong>Architecture : CPU, JIT, Vulkan et mémoire</strong></summary>

- **Dynarmic reste le JIT de référence.** Le JIT partagé et certaines compilations anticipées ne sont pas activés aveuglément.
- **Vulkan/RADV et OpenGL** sont deux chemins natifs. Les adaptations GPU sont vérifiées contre les sources et l'archive produite.
- **Cache shaders :** une taille de cache configurée ne démontre pas que les shaders sont réellement réutilisés.
- **Mémoire :** déclaration du paquet, mémoire invitée, tables clairsemées et cache JIT ne désignent pas la même ressource. L'unique profil PS5 intègre désormais un JIT sparse RX/RW avec engagement physique à la demande et libération après invalidation complète et quiescente. Ce comportement est testé sur hôte, mais ses économies et sa stabilité sur firmware 13.60 restent à qualifier.
- **Performances :** les fenêtres de télémétrie, verrous et IPC doivent expliquer les ralentissements et les gels, pas simplement afficher des FPS.

[Architecture](../../docs/PS5_NATIVE_ARCHITECTURE.md) · [Feuille de route performance](../../docs/PERFORMANCE_ROADMAP.md) · [Audit des adaptations](../../docs/INTEGRATION_AUDIT_CPU_GPU_JIT_2026-10-14.md)

</details>

---

<a id="compatibility"></a>
## 🧪 Compatibilité et limites

| Cas | État vérifié |
| --- | --- |
| **Firmware 13.60** | Cible matérielle testée : launcher et sessions sur certains jeux |
| Firmwares **antérieurs** (minimum inconnu) | **Potentiellement compatibles** selon le loader/homebrew, les API natives et les accès aux fichiers ; non testés sur Encore |
| Firmwares **plus récents** | **Non qualifiés** |
| Chargement NSO ZBIC/zstd et LZ4 | Implémenté ; dépend du logiciel |
| Match complet du jeu de référence | **Saccades et gel final toujours ouverts** |
| Contrôles personnalisés en match | **Application des actions du jeu non encore démontrée** |
| HUD en jeu | Fraîcheur des images et des données toujours étudiée |

Sur le dernier match intégral archivé (`2efd8b3c`), nous avons mesuré **858 images à plus de 50 ms**, dont **10 au-delà de 500 ms**, ainsi qu'une longue période durant laquelle la présentation continue sans progression normale des services du jeu. Des correctifs plus récents compilent, mais **aucun nouveau test sur console ne prouve encore un gain de fluidité ou la disparition du freeze**.

[Rapport de simulations et logs](../../docs/FC27_STRESS_REPLAY_2026-10-14.md) · [Plan de résolution](../../docs/GAMEPLAY_FREEZE_RECOVERY_PLAN.md)

---

## 📦 Compilations et validations

**Branche officielle unique pour les nouveaux changements : `main`.**

1. **Tests source/hôtes :** contrôlent le code, les adaptations, la mémoire, les entrées et les régressions.
2. **Compilation native :** vérifie les exécutables et le contenu réel de l'archive téléchargeable.
3. **Console :** valide ensuite le lancement, la réactivité, la qualité d'image, les commandes et la progression du jeu.

[Tests du code](https://github.com/niakw/ProsperoEden-Encore/actions/workflows/encore-core-preflight.yml?query=branch%3Amain) · [Paquets natifs](https://github.com/niakw/ProsperoEden-Encore/actions/workflows/build-040-zbic.yml?query=branch%3Amain)

Ne pas confondre une CI verte avec une version stable ou des performances validées sur la console.

---


<a id="faq"></a>
## ❓ FAQ — questions de X et de la communauté

Cliquez sur une question pour afficher sa réponse. La première réponse est volontairement très développée : **l'historique d'Encore commence le 4 octobre 2026**, et non lors du changement de dépôt du 30 octobre.

<details>
<summary><strong>• Quelle différence avec le projet ProsperoEden original ? Quels sont TOUS les changements depuis le début ?</strong></summary>

**Encore a commencé le 4 octobre 2026**, dans [le fork historique](https://github.com/niakw/Prospero.Eden-Encore), puis a rejoint ce dépôt indépendant le **30 octobre 2026**. Il s'agit d'un travail de fond, **pas simplement d'un nouveau nom**. Les auteurs des projets d'origine conservent leur attribution.

L'inventaire ci-dessous regroupe les modifications et optimisations **effectivement intégrées**, les analyses, les tests, les corrections et les développements expérimentaux. Attention : certaines fonctions existaient déjà dans ProsperoEden et ont été conservées, adaptées ou renforcées. Une **revue de code n'est pas une optimisation**, une **CI verte n'est pas une preuve de FPS sur PS5**, et une expérimentation n'est pas une fonction livrée. Pour les détails par fichier, correctif, commit et retour arrière : [journal complet du projet](../../MEMORY.md), [331 sources actives et backports](../../docs/EDEN_ACTIVE_SOURCE_CATALOG.md), [registre d'audit technique](../../docs/EDEN_CORE_AUDIT_DEPENDENCIES.md), [suivi F07 par fonction](../../docs/F07_FUNCTION_SCOPE_2026-10-28.md) et [historique des commits](https://github.com/niakw/ProsperoEden-Encore/commits/main/).

**1. Architecture PS5, organisation du projet, packaging et distribution**
- Ciblage et tests réels de la **PS5 en firmware 13.60**, sans promesse de compatibilité avec les firmwares non testés.
- Conservation et adaptation du port natif PS5, du cœur Eden, du compilateur Dynarmic, d'OpenGL et de Vulkan/Mesa/RADV.
- Harmonisation du Title ID **PPSA99008**, du dossier d'application, des chemins d'installation et des données persistantes.
- Simplification de la distribution en **un seul profil natif RELEASE** : abandon des différentes variantes expérimentales comme produits à installer.
- Sécurisation du démarrage et des erreurs, du retour au launcher, des journaux bornés et des protections des opérations sensibles.
- Paquets reproductibles : véritable <code>eboot.bin</code>, <code>sce_sys/param.json</code>, ZIP sans archive imbriquée, FFPFSC optionnel et symboles associés au même SHA.
- Intégration sélective des corrections amont Eden, des adaptations compilateur, SDK PS5, OpenGL, Vulkan et RADV ; refus d'assimiler une simple copie de fichier à une intégration compilée.
- Ajout de vérifications d'empreintes, de sources actives, de backports, de manifests et de correspondance avec les archives natives finales.
- Externalisation de <code>vendor/</code> dans un **sous-module Git épinglé**, en conservant la traçabilité et les licences des dépendances.
- Nettoyage/compactage de l'historique Git avec sauvegarde récupérable, puis création du **nouveau dépôt indépendant** et conservation des branches, tags, releases et références historiques lorsque possible.
- Prévalidation hôte rapide/complète, contrôles des paquets natifs, analyses de sécurité CodeQL, tests reproductibles et checklist de tests sur console séparés.
- Ajout de témoins source extraits, comparaisons O0/O2, ASan/UBSan, simulations de concurrence GPU/HLE et contrôles automatiques des régressions.
- Documentation d'architecture, inventaires de couverture, tests par SHA, consignes de migration, sécurité, crédits des auteurs et suivi des problèmes ouverts.
- Détails : [build natif](../../docs/BUILDING.md) · [profil RELEASE](../../docs/EDEN_ONE_SHIPPING_PROFILE_2026-10-26.md) · [migration du dépôt](../../docs/STANDALONE_REPOSITORY_MIGRATION_2026-10-30.md) · [vendor](../../docs/VENDOR_SUBMODULE_MIGRATION.md) · [historique Git](../../docs/REPO_HISTORY_COMPACTION_2026-10-30.md).

**2. Chargement des jeux, fichiers compressés, contenu et stockage**
- Extension des exécutables **NSO** avec décompression **ZBIC/zstd**, en plus de **LZ4**, et contrôles des tailles/segments.
- Conservation et évolution de la détection/sélection de **NSP, XCI, NRO, NSO, NCA, NAX et KIP** ; un fichier visible dans la bibliothèque ne garantit pas qu'il soit exécutable isolément.
- Introduction expérimentale de **NSZ/XCZ / NCZ** pour jeux, mises à jour et DLC, avec lecture aléatoire des blocs, métadonnées bornées et extraction temporaire contrôlée des formats « solid ».
- Détection des dossiers **ExeFS** contenant des fichiers réels <code>main</code> et <code>main.npdm</code>, sans accepter de liens symboliques dangereux.
- Vérifications des entrées invalides, limites de taille, accès aux fichiers, compression, annulations, caches temporaires et manque d'espace disque.
- Structure cohérente de <code>/data/prosperoeden/</code> sur stockage interne/externe : clés, firmware, ROM, mises à jour, mods, sauvegardes et caches.
- Migration protégée des anciennes données, réinitialisations confirmées et mode de récupération sans écraser silencieusement les préférences.
- Audits des métadonnées de titres, mises à jour, gestion de contenu, chargeurs et services HLE liés au stockage.
- Détails : [matrice exhaustive des formats](../../docs/CONTENT_FORMAT_MATRIX_2026-10-23.md) · [installation](../../INSTALL.md) · [écarts avec l'amont](../../docs/UPSTREAM_GAP_REGISTER_2026-10-14.md).

**3. CPU, Dynarmic A32/A64, JIT sparse, RAM et fastmem**
- Étude des points chauds du compilateur **Dynarmic**, des interruptions, atomiques, invalidations, threads invités, accès mémoire et processeurs logiques PS5.
- Création du **JIT sparse RX/RW** unique pour le paquet natif, avec deux alias virtuels et engagement physique par blocs de **2 Mio** à la demande.
- Test préalable de disponibilité des alias avant lancement ; pas de repli aveugle sur l'ancien JIT dense.
- Récupération de mémoire physique en fin d'invalidation **complète et quiescente** du cache JIT, sans casser les permissions ni la durée de vie des blocs.
- Amélioration des tables de pages sparse : allocation bornée, tailles initiales, scans, générations, caches de correspondances positives/négatives et recherches entre arènes.
- Mise en cache des recherches RX→RW et des misses stables, optimisation des recherches alternées et protections contre les adresses périmées.
- Optimisation de **Map/Unmap/Protect fastmem** : suppression de reconstructions d'alias et de changements de permissions identiques, chemins rapides une page / granularité 16 Kio / traversées courtes.
- Vérification des bornes d'adresses invitées, alignement, régions sales GPU, accès multi-pages, invalidations de plage et états d'échec/réessai.
- Réduction ciblée des allocations, piles de fibres/threads et coûts de consultation, sans proclamer de gain FPS matériel non mesuré.
- Audits de pression mémoire, JIT, RAM invitée, VRAM, caches graphiques, allocation physique réelle et risques d'OOM avec des réglages 4×.
- **Non activés en RELEASE :** JIT partagé inter-cœurs, traduction anticipée spéculative et autres expérimentations de concurrence insuffisamment qualifiées.
- Détails : [architecture native](../../docs/PS5_NATIVE_ARCHITECTURE.md) · [durée de vie JIT](../../docs/DEFERRED_JIT_QUIESCENCE_ARCHITECTURE_2026-10-17.md) · [audit CPU/JIT](../../docs/EDEN_CPU_JIT_G11_G12_MIGRATION_MAP.md).

**4. Maxwell, GPU, DMA, buffers et synchronisation**
- Corrections/revues de **Maxwell DMA**, Host1x, gestionnaire de commandes, FIFO, fences, file de travail GPU et durée de vie des emplacements.
- Regroupement ciblé des copies DMA et des invalidations, sans réordonner des dépendances ni rejouer des commandes invitées.
- Suivi plus fin des segments modifiés CPU/GPU, des transferts, des lectures synchrones/asynchrones et des frontières de buffers.
- Contrôles des bindings indirects, des descripteurs nuls, des index/sommets, des ressources graphiques et des limites mémoire.
- Optimisation des sondes de possession de page GPU, enregistrement de buffers/textures sur une seule page et opérations sur petits segments.
- Diminution d'allocations et de synchronisations inutiles sur certaines files de travail et vérification de leur publication atomique.
- Distinction fondamentale entre un **GPU qui continue à présenter** et un **jeu dont les threads invités sont bloqués**.
- Détails : [DMA Maxwell](../../docs/EDEN_MAXWELL_DMA_CONTIGUOUS_BATCH_2026-10-21.md) · [GPU/FC27](../../docs/FC27_GPU_SOURCE_TARGETS_2026-10-21.md).

**5. Vulkan, RADV, shaders, pipelines, textures et affichage**
- Adaptations et verrouillage des versions **Mesa/RADV**, du chemin Vulkan PS5 et de ses composants réellement compilés.
- Optimisation des identités de shaders de sommets, petites tables de mémorisation des pipelines compute, recherches répétées et invalidations par génération.
- Publication mémoire acquire/release des pipelines prêts, gestion prudente des compilations optionnelles, des descripteurs et des transitions.
- Revue du cache shaders, compilation IR/SPIR-V, attente du worker Vulkan, construction des pipelines, descripteurs et prévalidation hors verrous.
- Corrections/revues des caches textures **TIC/TSC**, samplers, vues absentes/nulles, alias d'images, cohérence CPU/GPU et invalidations.
- Sécurisation du décodage de textures asynchrone, des BCn/3D, unswizzle, uploads/downloads et rollback après erreurs de staging.
- Préservation des états « GPU dirty » et refus d'évincer une image modifiée lorsqu'une lecture/récupération échoue.
- Synchronisation de **DrawTexture → état du scheduler**, copies blit/resolve, framebuffer/pitch/stride, mises à jour et présentation des images.
- Suppression de calculs inutiles lorsque le framebuffer invité est absent, amélioration des copies raw et du choix des dimensions de pixels.
- Gestion plus sûre des swapchains, pertes de surface, acquire/present, recréation des framebuffers et libération d'anciennes ressources selon les vrais ticks GPU.
- Regroupement des notifications de présentation, diminution de broadcasts inutiles, verrou de recyclage GPU libéré avant allocations froides.
- Réduction des reconstructions AA désactivées et d'éléments de HUD/diagnostics cachés qui consommaient inutilement du CPU.
- Revue **F07 de 38 fonctions ciblées dans 8 fichiers** : shaders, pipelines/descripteurs, rasterizer, caches et HUD ; nombreux correctifs de bornes, durée de vie, staging et gestion d'échec.
- **Restent ouverts :** traduction des nouveaux shaders parfois synchrone, attente obligatoire d'un pipeline, contention réelle des caches et images HUD noires/en retard.
- Détails : [38 fonctions et correctifs](../../docs/F07_FUNCTION_SCOPE_2026-10-28.md) · [checklist F07](../../docs/F07_REMAINING_OPTIMIZATION_CHECKLIST.md) · [audit GPU transversal](../../docs/FC27_F07_CROSS_SYSTEM_OPTIMIZATION_AUDIT_2026-10-26.md) · [priorités HUD](../../docs/FC27_F07_STUTTER_HUD_PRIORITY_2026-10-26.md).

**6. HLE, IPC, audio, réseau et exécution**
- Audit des services HLE, threads, réveils, attentes **IPC**, durée de vie des services, ordonnancement, exceptions et arrêts sûrs.
- Diagnostic de **NVNflinger, BufferQueue, SurfaceFlinger, NvDisp**, couches d'affichage et progression du jeu indépendamment du compteur FPS.
- Corrections/contrôles des débordements PCM, initialisation audio, ring buffers, mixage, upmix et durée de vie de la sortie audio.
- Réduction des copies et allocations inutiles dans certains traitements audio, avec tests hôte de concurrence.
- Révisions des sockets, DNS, **NanoDNS**, stratégie réseau invitée, erreurs de connexion et initialisation ; aucune promesse de services Nintendo en ligne.
- Optimisation des traitements silencieux (« quiet »), diagnostic à la demande et journalisation de crash plutôt qu'écriture permanente sur les chemins critiques.
- Détails : [IPC](../../docs/PS5_R393_2026-10-12_GUEST_IPC_THREAD_DIAGNOSTICS.md) · [réseau](../../docs/PS5_R296_2026-10-10_NETWORK_AUDIT_NANODNS.md) · [audit moteur](../../docs/EDEN_CORE_AUDIT_DEPENDENCIES.md).

**7. Manette DualSense, contrôles, interface, artwork et langues**
- Refonte/extension des pages **Accueil / Bibliothèque / Récents**, navigation TV à la manette, jaquettes, médias, aperçus et paramètres rapides.
- Boîtiers de jeux **3D animés**, scans distincts recto/verso et reconstruction native à partir des arts disponibles lorsqu'il manque une face.
- Profils par jeu **Minimum, Recommandé, Haute, Ultra et Personnalisé**, réglages graphiques et **Safe Launch** temporaire sur une seule session.
- Exposition des options Vulkan/OpenGL, résolution interne, filtres, upscaling, netteté et anticrénelage dans les limites matérielles.
- Traduction de l'interface dans **29 langues**, améliorations des polices, textes longs, Unicode, langues bidirectionnelles et écritures complexes.
- Optimisation de la mise en forme des polices, des buffers SDF, du flux audio de l'interface et des chargements médias asynchrones.
- Ajustements **DualSense** : correspondances manette physiques, boutons PS/Capture/Options/Touchpad, vibrations, zones mortes et courbes analogiques pré-calculées.
- Suppression de copies inutiles des échantillons manette, de remises à zéro de scratch fréquentes, de scans de diagnostics et de traitements pour manettes déconnectées.
- Exploration de l'**avatar de profil PS5** via lecture protégée et asynchrone ; disponibilité universelle sur console non validée.
- Travaux sur les **glyphes des boutons PlayStation en jeu**, inventaire des mods et correspondances par titre ; remplacement universel **non livré**.
- Documentation d'accessibilité, contraste, réduction des mouvements, confirmations de réinitialisation et préservation des préférences.
- Captures d'écran produites par le véritable moteur du launcher, mais avec des **jeux fictifs** pour la démonstration.
- Détails : [audit launcher](../../docs/EDEN_RELEASE_LAUNCHER_SOURCE_OPTIMIZATION_AUDIT_2026-10-26.md) · [boîtiers](../../docs/LAUNCH_CASE_ARTWORK.md) · [glyphes](../../docs/PS5_INGAME_GLYPHS.md) · [accessibilité](../../ACCESSIBILITY.md).

**8. Tests console, performances, stabilité et corrections FC27**
- Ajout de métriques par fenêtre d'images, latences longues, GPU présent, attente pipeline, files GPU, verrous, pression JIT et progression CPU/HLE.
- Tests sur **FC27** : match jouable par moments, mais saccades, lenteur/absence de HUD, problèmes de manette pendant le match et gels pause/mi-temps/fin.
- Sessions de comparaison sur **Zelda: Breath of the Wild**, plus fluides dans plusieurs configurations, sans déduire que les autres jeux le seront.
- Tests A/B sur caches anciens/vidés, journaux activés/désactivés, résolution, FSR et modes vidéo ; identification de l'impact des logs détaillés.
- Analyse des demandes mémoire à haute résolution et du risque d'OOM lié notamment aux options AA/rendu élevées.
- Établissement des quatre priorités P0 **shader à la première utilisation**, **attente des pipelines Vulkan**, **contention caches buffers/textures**, **fraîcheur des images HUD**.
- Séparation des critères F01–F06 vérifiables sur hôte, des audits F07 et des vrais tests de jouabilité PS5 ; aucun compteur de fichiers n'est une estimation fiable du travail restant.
- Détails : [tableau maître FC27/F07](../../docs/FC27_F07_MASTER_TRACKER.md) · [rapport de session](../../docs/FC27_STRESS_REPLAY_2026-10-14.md) · [plan anti-freeze](../../docs/GAMEPLAY_FREEZE_RECOVERY_PLAN.md) · [critères de clôture](../../docs/PS5_CLOSURE_CRITERIA.md).

**9. Expérimentations et roadmap — ne pas confondre avec les fonctions livrées**
- **Frame generation :** retour prévu dans une solution plus maîtrisée, après stabilisation de la cadence et du rendu ; pas actuellement certifiée dans une release.
- **FSR spatial/temporel, interpolation, 60/120 Hz, AA x2/x4 :** évolutions souhaitées ou étudiées, sans garantie de compatibilité générale.
- **Switch 2 / NSW2 :** recherche isolée sur une **branche dédiée**, nouveaux chemins de chargement, NSO homebrew, CPU/IR/Dynarmic, shaders/GPU ; **pas intégrée à la release PS5**.
- **JIT partagé, compilation anticipée, traitements GPU différés :** prototypes ou études désactivés lorsque la sûreté et les dépendances ne sont pas démontrées.
- **Glyphes PlayStation en jeu, avatar, contrôles persistants en match et 60 FPS par titre :** chantiers distincts, sans promesse de prise en charge universelle.
- Détails : [roadmap](../../docs/PERFORMANCE_ROADMAP.md) · [branches de recherche](../../docs/DEVELOPMENT_BRANCH_POLICY.md) · [pipeline des glyphes](../../docs/PS_GLYPH_INPUT_PIPELINE.md).

Ce recensement présente **tous les grands périmètres de changements depuis le début du projet**, et renvoie à leurs registres de détail pour les correctifs mineurs, versions intermédiaires, revues sans modification et commits de CI. Il n'affirme ni que toutes les fonctions du moteur ont été réécrites ni que les gains attendus sont tous prouvés en jeu. [Journal historique complet](../../MEMORY.md) · [Commits](https://github.com/niakw/ProsperoEden-Encore/commits/main/).

</details>

<details>
<summary><strong>• « Han quitado la generación de frames… » — Pourquoi la génération de frames a-t-elle disparu ?</strong></summary>

- Les optimisations techniques, la stabilité et la fluidité **réelle** passent avant l'interpolation de nouvelles images.
- Notre objectif est une **meilleure gestion de la génération d'images que dans le projet d'origine**, une fois les blocages CPU/GPU, l'image HUD et le rythme de présentation stabilisés.
- C'est une priorité de court terme après ces correctifs, **pas une date de sortie garantie**. [Feuille de route](../../docs/PERFORMANCE_ROADMAP.md).

</details>

<details>
<summary><strong>• « Permite jugar a la Switch 2? » — Est-ce compatible Nintendo Switch 2 ?</strong></summary>

- **Non, pas dans la version PS5 actuelle.** La [branche de recherche NSW2](https://github.com/niakw/ProsperoEden-Encore/tree/research/ns2-ps5-compatibility) et son [rapport de faisabilité](https://github.com/niakw/ProsperoEden-Encore/blob/research/ns2-ps5-compatibility/docs/NS2_PS5_FEASIBILITY_2026-10-30.md) détaillent les essais indépendants.
- Les chemins NSO homebrew, traduction CPU/IR et shaders en cours d'étude ne prouvent **aucune compatibilité stable avec les jeux commerciaux Switch 2**.
- Aucun résultat 30 FPS sur Mario Kart World ou prise en charge générale d'un format Switch 2 n'est annoncé. L'optimisation Switch 1/PS5 reste prioritaire.

</details>

<details>
<summary><strong>• « Y qué tal es su funcionamiento en PS5 ? » — Comment tourne Encore sur PS5 ?</strong></summary>

- Le **firmware 13.60** est notre base d'essai réelle.
- FC27 peut atteindre le match, mais présente encore des saccades, des problèmes de HUD et des gels en pause/mi-temps/fin de match dans les tests enregistrés.
- Zelda: Breath of the Wild a produit des sessions nettement plus fluides ; cela ne vaut pas liste de compatibilité universelle.
- Pas de promesse générale de **30 FPS verrouillés**, ni de 60/120 FPS. [Résultats](../../docs/FC27_F07_MASTER_TRACKER.md).

</details>

<details>
<summary><strong>• Est-ce un simple rebranding ou y a-t-il des optimisations du moteur ?</strong></summary>

- Les modifications concernent CPU/JIT, fastmem, GPU/Vulkan, caches, textures, HLE, contrôleurs, formats, frontend et outillage CI.
- **Une optimisation du code vérifiée sur hôte ne prouve pas un gain de FPS sur la vraie PS5.** Les résultats finaux dépendent de tests comparables sur console.
- Le but est une expérience stable, pas un chiffre FPS artificiellement élevé.

</details>

<details>
<summary><strong>• Peut-on jouer à 60/120 FPS, utiliser FSR temporel ou un AA x2/x4 ?</strong></summary>

- Résolution, filtrage, mise à l'échelle et AA disposent de réglages, mais chaque jeu a ses propres limites de simulation et d'affichage.
- FSR avancé, interpolation, 60/120 Hz et qualité d'AA renforcée font partie des évolutions étudiées ; **leur disponibilité et leur efficacité ne sont pas garanties aujourd'hui**.
- Une définition ou un AA élevés peuvent épuiser la mémoire GPU. [Roadmap](../../docs/PERFORMANCE_ROADMAP.md).

</details>

<details>
<summary><strong>• Quels firmwares PS5 sont pris en charge ?</strong></summary>

- **Recommandé/testé : 13.60** pour Encore. Ce n’est **pas une incitation à mettre à jour la console**.
- Les firmwares **antérieurs peuvent être compatibles** si l’environnement jailbreak/homebrew, les API natives, le pilote graphique et les permissions le permettent. **Firmware minimum : inconnu ; aucune autre version testée sur Encore.**
- ProsperoEden natif mentionne des essais du **composant Lapy** sur **6.02** et **12.70** ([notes d’origine](https://github.com/Swordpdf/ProsperoEden/blob/main/README.md)). **Encore utilise toutefois un autre mécanisme d’accès aux fichiers**, issu de sa base 1.000.040 ([notes du fork](../../docs/FORK_NOTES.md)). Ces tests **ne certifient donc pas Encore** sur ces versions.
- Firmwares ultérieurs non qualifiés. Voir les notes et le SHA de chaque release.

</details>

<details>
<summary><strong>• Quels formats de jeux sont pris en charge ? NSP, XCI, NSZ, XCZ ?</strong></summary>

- **NSP/XCI** : conteneurs de jeux détectés.
- **NSZ/XCZ** : lecture compressée expérimentale, qualification matérielle encore incomplète.
- **NRO/NSO/NCA/NAX/KIP**, plus dossiers ExeFS correctement structurés : sélection possible, lancement dépendant du contenu.
- **LZ4 et ZBIC/zstd** sont des compressions internes NSO, pas des extensions de ROM. [Matrice complète](../../docs/CONTENT_FORMAT_MATRIX_2026-10-23.md).

</details>

<details>
<summary><strong>• Les manettes PS5 et les boutons PlayStation sont-ils utilisables dans les jeux ?</strong></summary>

- Navigation et profil **DualSense dans le launcher** : oui, avec réglages de mappings, zones mortes et vibrations.
- Les actions personnalisées **à l'intérieur du jeu** et les glyphes Switch affichés par le jeu sont distincts. Ils ne sont pas encore automatiquement et universellement convertis en boutons PlayStation.
- [État technique](../../docs/PS5_INGAME_GLYPHS.md).

</details>

<details>
<summary><strong>• Une CI verte signifie-t-elle que le jeu marche sur PS5 ?</strong></summary>

- **Non.** Code, tests hôte, compilation native et tests de jeu sur PS5 sont **quatre niveaux différents**.
- Pour installer une version testée, consulter les [Releases](https://github.com/niakw/ProsperoEden-Encore/releases), les notes de firmware/jeux et les empreintes du build.
- Un artefact de développement GitHub Actions n'est pas automatiquement une version stable.

</details>

<details>
<summary><strong>• Encore est-il officiel ? Fournissez-vous des jeux, des clés ou des firmwares ?</strong></summary>

- C'est un fork communautaire **non officiel**, héritier de ProsperoEden/Eden, avec crédits et licences préservés.
- Aucun jeu commercial, firmware propriétaire, clé ni DLC n'est distribué. Utiliser uniquement des contenus dont l'usage est autorisé.
- [Crédits](../../README.md#credits) · [Licences tierces](../../THIRD_PARTY_NOTICES.md).

</details>

<details>
<summary><strong>• Encore reçoit-il les mises à jour de ProsperoEden natif ? Peut-on mettre à jour Encore depuis la PS5 ?</strong></summary>

- **Pas de synchronisation automatique de l’amont.** Notre base traçable est **ProsperoEden v1.000.040** ; les correctifs des nouvelles versions du port natif et du cœur Eden sont comparés puis intégrés **sélectivement**, sous contrôle des dépendances, de Vulkan, du JIT, de la mémoire et des régressions. Une nouveauté chez ProsperoEden n’est **pas automatiquement présente dans Encore**.
- **Pas encore de fonction de mise à jour intégrée d’Encore.** Le jalon **R21** définit un contrôle manuel, une éventuelle recherche au lancement, l’affichage des versions, un téléchargement vérifié, une confirmation de l’installation et une récupération sûre. C’est **une spécification, pas une fonctionnalité livrée**. [Roadmap R21](https://github.com/niakw/ProsperoEden-Encore/blob/feat/graphics-network-achievements/docs/ROADMAP_ENCORE_COLLAB_2026-10-25.md).
- En attendant, utiliser les **[Releases d’Encore](https://github.com/niakw/ProsperoEden-Encore/releases)** et le [guide de migration](../../INSTALL.md). **Ne pas écraser Encore avec un ZIP ProsperoEden d’origine** uniquement parce que sa version est plus récente : les applications peuvent partager l’identifiant **PPSA99008** et des dossiers, sans partager le même code ni les mêmes migrations.
- [Projet natif ProsperoEden](https://github.com/blackbearreloaded/ProsperoEden) · [audit des écarts amont](../../docs/UPSTREAM_GAP_REGISTER_2026-10-14.md) · [comparaison d’une version native](../../docs/UPSTREAM_PROSPEROEDEN_1001000_R428.md).

</details>

<details>
<summary><strong>• Que reste-t-il à faire et quand arrive la prochaine version ?</strong></summary>

- Les priorités sont les shaders de première utilisation, l'attente des pipelines Vulkan, la contention des caches GPU, les images HUD, les gels de progression et leurs validations sur console.
- De nombreux petits commits sont des tests ou des correctifs CI, **pas autant de nouveautés promises**.
- Le chantier avance rapidement, mais aucune **date vérifiée** de release ne peut être annoncée. [Commits](https://github.com/niakw/ProsperoEden-Encore/commits/main/) · [Releases](https://github.com/niakw/ProsperoEden-Encore/releases).

</details>

---

## 🛡️ Sécurité, licences et crédits

**Historique d'Encore — développement commencé le 4 octobre 2026.** Notre travail a débuté le **4 octobre 2026** sur [l'ancien fork `niakw/Prospero.Eden-Encore`](https://github.com/niakw/Prospero.Eden-Encore). Le **30 octobre 2026**, nous avons transféré ces travaux vers [ce dépôt indépendant](https://github.com/niakw/ProsperoEden-Encore), afin de rendre Encore plus facile à trouver sur GitHub. L'ancien fork reste référencé pour conserver l'historique du projet. Ce changement de dépôt ne remet pas la date de début à zéro et ne remplace pas les crédits des projets d'origine.

Encore est un fork communautaire non officiel, distribué sous **GPL-3.0-or-later**. Le durcissement de l'accès aux fichiers n'est **pas** un bac à sable après élévation de privilèges.

**Sources et auteurs :** [crédits détaillés dans le README principal](../../README.md#credits) · [composants tiers](../../THIRD_PARTY_NOTICES.md) · [textes complets](../../LICENSES/).

[Accessibilité (EN)](../../ACCESSIBILITY.md) · [Licence](../../LICENSE) · [Sécurité](../../SECURITY.md) · [Contribuer](../../CONTRIBUTING.md) · [Support](../../SUPPORT.md) · [Code de conduite](../../CODE_OF_CONDUCT.md).

Ce projet ne distribue aucun jeu commercial, aucune clé, aucun firmware ni aucun contenu propriétaire. Il ne confère aucun droit de redistribution sur les logiciels tiers.
