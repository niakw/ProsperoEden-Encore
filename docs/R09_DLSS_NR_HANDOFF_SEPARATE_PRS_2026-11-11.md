# R09 DLSS-NR Min 720p — transmission des PR indépendantes

Dernière vérification : 11 novembre 2026, 16 h 53–17 h (Europe/Paris).

**Périmètre de cette discussion : préparation, audit, corrections source et tests sur les branches de recherche. AUCUNE fusion, rebase, fermeture de PR, suppression de branche, changement sur main, changement du pointeur vendor de production, activation PS5 ou publication de release. L'autre discussion décide de l'intégration.**

## Branches et PR exactes

| Domaine | PR | Branche (SHA vérifié) | Travail |
|---|---|---|---|
| Moteur | [#43](https://github.com/niakw/ProsperoEden-Encore/pull/43) | `feature/dlss-nr-min-rdna2-ps5` (consulter le dernier HEAD après l'ajout de ce document) | Plan Original 720p, preflight, runner Linux, lanceur privé Mac, graphe optionnel AA/Neural/Upscale/FG, sélection de parcours mesurés, CI |
| Vendor ViT | [#34](https://github.com/niakw/Prospero.Eden-Encore-vendor/pull/34) | `research/r09-dlss-nr-min-vit-pool` — `a9081717cfee17b256e17d02fcf5bdafdc340008` | Pooling neuf buffers ViT et profil 720p, désactivé par défaut |
| Vendor FSwin | [#39](https://github.com/niakw/Prospero.Eden-Encore-vendor/pull/39) | `research/r09-fswin-chain-scratch-pool` — `447c352cd0567e8a96218864058554eb80817c3a` | Réutilisation scratch FSwin, comparaison de plusieurs fenêtres GPU, désactivée par défaut |
| Vendor A4K | [#40](https://github.com/niakw/Prospero.Eden-Encore-vendor/pull/40) | `research/r09-a4k-output-image-handoff-20261111` — `f1d0aa1b42462bfcfc12ad090b16391e43b06ffd` | Véritables API image+view A4K/FSR/SGSR ; passage possible à l'upscale/FG |
| Vendor readback | [#42](https://github.com/niakw/Prospero.Eden-Encore-vendor/pull/42) | `research/r09-min-720-readback-20261111` — `b26075ab190460014cbffd6c744faf897088375c` | Readback RGBA32F strict aux dimensions 720p/1080p, rejet des incohérences |

Toutes ces PR sont **ouvertes et draft**, et restent **séparées**. Le gitlink vendor de production du moteur était `22b69d6053db41b74edac2633c012f925b84f69e` au dernier contrôle. Le workflow hôte #43 utilise uniquement le SHA vendor **#42** en checkout détaché ; il ne compose PAS #34, #39 et #40 dans un runtime commun. Ne jamais présenter ce checkout temporaire comme un vendor de production validé.

## Preuves acquises, à conserver

- Vendor #34 : [CI pool ViT #42908627555](https://github.com/niakw/Prospero.Eden-Encore-vendor/actions/runs/42908627555) et sécurité #42908627599 vertes au SHA ci-dessus. Source et allocations testées avec profil 720p ; pas un modèle entraîné exécuté de bout en bout.
- Vendor #39 : [CI scratch FSwin #42946536767](https://github.com/niakw/Prospero.Eden-Encore-vendor/actions/runs/42946536767) et sécurité #42946536879 vertes au SHA ci-dessus. Les preuves Vulkan multi-fenêtres utilisent des poids publics de test ; **pas 44 couches FSwin entraînées** sur PS5.
- Vendor #40 : [sécurité #42996524526](https://github.com/niakw/Prospero.Eden-Encore-vendor/actions/runs/42996524526) verte. L'API C++ image+view est qualifiée en syntaxe ; l'ancienne preuve [GPU FSR1/SGSR #43018833843](https://github.com/niakw/ProsperoEden-Encore/actions/runs/43018833843) a exécuté les vrais shaders, **pas** les nouvelles méthodes C++ A4K `DrawFrame`.
- Vendor #42 : [sécurité #43020784921](https://github.com/niakw/Prospero.Eden-Encore-vendor/actions/runs/43020784921) et [syntaxe native engine #43021118509](https://github.com/niakw/ProsperoEden-Encore/actions/runs/43021118509) vertes. Readback exact de 14 745 600 octets en 720p et 33 177 600 en 1080p ; les poids privés et la vraie image neuronale ne sont pas prouvés.
- Moteur #43 : [CI universelle GCC+Clang UBSan #43041610607](https://github.com/niakw/ProsperoEden-Encore/actions/runs/43041610607) et [CI de vérification hors réseau #43044916661](https://github.com/niakw/ProsperoEden-Encore/actions/runs/43044916661) vertes. 19 531 séquences (0–6 étapes), 20 480 permutations de méthodes et positions (NR/FG/AA/Spatial facultatifs), 80 contrôles d'intensité/netteté, 16/16 masques de présence, source MSAA, v3 et déduplication. **Contrats hôte et algorithmiques**, pas exécution des 152 opérateurs Original sur la PS5.

## Points de collision ou de reprise (critiques pour l'autre discussion)

1. Les PR vendor **#34 et #42 modifient le même fichier** `encore-active/eden-vulkan/nr_rdna2_frame_session.cpp`. Un merge séparé peut nécessiter une résolution sémantique des allocations ViT, des extents, du modèle et de la lecture GPU. Ne pas écraser le correctif #42 en appliquant #34, ni inversement. Les PR restent individuelles ; le suivi d'intégration se fait ailleurs.
2. La PR **#39** modifie le cœur des couches FSwin ; vérifier son raccordement de sessions et la compatibilité allocations/fences avec #34 avant toute activation, tout en préservant leurs branches.
3. La PR **#40** ajoute des sorties natives pour A4K/FSR/SGSR ; les tests shader GPU séparés ne prouvent pas encore l'utilisation de ces nouvelles API dans le compositeur réel avec Neural/FG.
4. Le moteur #43 ne doit pas recopier les filtres, le menu ou les conversions existants : l'implémentation des shaders AA/FSR/SGSR est déjà dans les changements antérieurs (#24), les réglages dans #30. Le seul nouvel objet est **l'ordonnancement** et la qualification des ressources et paramètres par étape. Les chemins avant/après FG exigent un traitement indépendant des deux flux réels/synthétiques.
5. Le MSAA forcé agit pendant la rasterisation et exige resolve + vérifications de format/échantillons, pas un filtre 2D déplaçable. Le TAA, FSR3.1 temporel et le 540p neural ne sont pas qualifiés. Ne pas transformer les essais de politique hôte en options automatiquement activées en production.
6. Les recettes R09 sont en **version 3** ; migration explicite de v1/v2 obligatoire, et preuve native (pas préférence sauvegardée) pour un traitement post-FG touchant les deux flux. Les nettoyages d'étapes redondantes ne sont pas des réordonnancements supposés visuellement neutres. Netteté FSR1/SGSR et intensité Original sont des paramètres **indépendants par étape** (-1 hérite, 0–100% explicite) et font partie de la clé de déduplication.

## Build Linux : état exact / pas de preuve artificielle

- Les anciens runs [#43022421489](https://github.com/niakw/ProsperoEden-Encore/actions/runs/43022421489) et [#43029338449](https://github.com/niakw/ProsperoEden-Encore/actions/runs/43029338449) ont exécuté la vraie compilation puis rencontré successivement deux symboles absents à la liaison : destructeur `MsaaColorClearShadowPass`, puis `PhysicalDevice::GetImageFormatProperties`. La branche moteur #43 inclut les correctifs ciblés de sources Vulkan hôte et le chargement de dispatch, **non revalidés par un nouveau lien complet réussi**.
- Le run [#43034547912](https://github.com/niakw/ProsperoEden-Encore/actions/runs/43034547912) a été annulé après blocage prolongé sur APT ; le [run de contrôle DNS #43044439356](https://github.com/niakw/ProsperoEden-Encore/actions/runs/43044439356) a échoué sur la résolution de `archive.ubuntu.com`, sans compiler les sources. Le workflow a un préflight réseau court et un fallback APT officiel signé à installation bornée. Le **test de cette réécriture APT est vert** dans la CI sans réseau ci-dessus.
- Aucun nouveau binaire complet téléchargeable n'a été confirmé. Les nouvelles erreurs DNS APT dans des CI Vulkan ne sont PAS des régressions compilateur du DLSS-NR.
- Le Mac private-runner pointe sur un run précis et des SHA précis, refuse un artefact non conforme, et attend une vraie DLL/modèle original + image du jeu sur la machine de l'utilisateur ; ne pas publier ces données.
- Le sérialiseur 720p `extras/graphics/dlss_nr_min_720_plan_emit.h` conserve `gpu_executable=false` et `ready_to_enable_720p=false` : **un plan structurel à 152 lignes n'équivaut pas encore à un chemin neuronal GPU bout-en-bout.** Ne pas supprimer ces garde-fous par affirmation.

## Conditions de sortie avant qualification effective PS5

A. Rétablir un runner Linux avec résolution DNS fonctionnelle. Faire **une seule** compilation/liens natifs réussis, puis exécution d'un rejet de modèle factice et publication d'un artefact public sans poids.

B. Fournir en local un modèle Original authentique (599 tenseurs vérifiés) et une vraie capture pour le test hôte ; vérifier l'inférence de toutes les **152 opérations à 1280×720**, la sortie RGBA32F non dégénérée, un oracle indépendant, traces GPU/barrrières et une image A/B. Un simple succès de Vulkan, un rendu de couleurs synthétiques ou des hashes de tensors seuls ne suffisent pas.

C. Mesurer sur PS5 RDNA2 : mémoire partagée maximale, temps GPU de chaque étape, stabilité sur titres NS1/NS2, synchronisation, HUD/alpha/HDR et historique FG, qualité d'image, résolution/TV, gestion de source perdue ou de crash ; garder un repli stable sans Neural.

D. Ne choisir et activer un parcours que via preuves natives. Le sélecteur de recherche `neural_pipeline_path_selection.h` exige mesures GPU/VRAM + A/B acceptée, supprime les recettes exactement identiques (y compris les intensités), et **ne modifie jamais les flags runtime PS5**.

## Règle de transmission

**Chaque PR doit rester identifiable, testable et intégrable individuellement par l'autre discussion.** Les modifications de ce chantier n'ont pas été fusionnées à `main`. La revue de compatibilité, l'éventuelle reprise des commits, les décisions de merge et les builds consoles appartiennent à la phase d'intégration de l'autre discussion. Ne pas considérer le DLSS-NR Original 720p/Compact comme matériellement terminé avant les preuves A–D.
