# Eden Encore — classement théorique de qualité graphique (R07/R24)

**6 novembre 2026 · PR #24 (DRAFT) · ordre cible théorique, rendu PS5 non validé.**

Il n'existe pas de classement universel. L'ordre ci-dessous vise la restitution
spatiale d'une image 3D sous-résolue et le traitement de contours, **sur le
papier uniquement**. Scintillement, transparence, finesse du HUD, budget GPU
et échelle interne peuvent inverser plusieurs positions. Ce document classe les traitements par qualité estimée, **pas par
ID ni par ordre d'énumération** dans le launcher. Les anciens indices
enregistrés 0-3 restent identiques ; les nouveaux MSAA sont ajoutés
en 4-7, sans présumer d'un résultat visuel sur PS5.

## Un seul ordre effectif par réglage — pas deux modes de tri

Le menu PS5 présente une **ligne Upscaling** et une
**ligne Anti-aliasing**, chacune avec un choix à la fois et des
flèches gauche/droite. Il existe bien **deux familles de méthodes**,
mais **pas deux modes de tri** dans l'interface.

- Upscaling : **10 filtres sélectionnables en code** dans le menu (7
  historiques et 3 profils A4K). FSR 3.1 temporel reste un choix futur
  tant que les ressources invitées n'alimentent pas son backend.
  Les IDs des anciens filtres restent inchangés.
- Anti-aliasing : **8 positions théoriques**. Les quatre anciens filtres
  restent aux index 0-3 du launcher ; MSAA 2×/4×/8×/16× aux nouveaux
  index 4-7. Les modes MSAA ont maintenant un chemin Vulkan réel en code
  (seulement couleur, clear complet, sans profondeur/alias), non encore
  mesuré sur console ni qualifié pour une release.
- **MSAA Auto** est le comportement natif (respect du nombre d'échantillons demandé par le jeu), **hors classement de qualité** ; « Off » retire le post-AA, pas le MSAA demandé par le GPU invité.
- La colonne **coût GPU estimé** renseigne un deuxième **critère
  de comparaison**, pas un deuxième ordre de sélection. Aucune option
  de tri par FPS/performance n'est livrée.
- Sur OpenGL, la navigation saute les options non prises en charge
  (SGSR / SGSR Edge / A4K ; FXAA+ et MSAA forcé pour l'anticrénelage). Pour un jeu,
  le choix « Hériter du global » s'ajoute avant les méthodes.
- Les indices persistés des préférences **ne sont pas renumérotés**,
  même si l'ordre de navigation ne correspond pas à l'ordre historique
  de l'énumération.

## Upscaling — ordre cible pour les jeux 3D

| Rang | Filtre | Qualité présumée / limites | Coût GPU relatif non mesuré | Statut |
| --- | --- | --- | --- | --- |
| 1 | **AMD FSR 3.1 Super Resolution (temporel)** | Reconstruction avec historique, mouvement et profondeur réels ; peut réduire l'aliasing temporel mais produire du ghosting si les données ne sont pas fiables | Élevé / variable | **Futur, non sélectionnable** |
| A4K-1 | **A4K — Détails améliorés** | CNN 3D ×2, 4 passes ; qualité variable selon le jeu | Élevé (non mesuré) | Intégré en code, test PS5 requis |
| A4K-2 | **A4K — Image adoucie** | CNN Restore Soft puis 3D ×2, 8 passes | Très élevé (non mesuré) | Intégré en code, test PS5 requis |
| A4K-3 | **A4K — Image nettoyée** | CNN Denoise ×2, 5 passes | Élevé (non mesuré) | Intégré en code, test PS5 requis |
| 2 | SGSR Edge | Reconstruction spatiale orientée contours ; halos possibles | Moyen / élevé | Sélectionnable, validation visuelle PS5 à faire |
| 3 | SGSR | Reconstruction spatiale avancée ; qualité dépendante du contenu | Moyen | Sélectionnable, validation visuelle PS5 à faire |
| 4 | AMD FSR 1 (EASU/RCAS) | Agrandissement spatial avec netteté réglable | Moyen | Sélectionnable |
| 5 | Lanczos | Détails nets ; possibles halos (ringing) | Faible / moyen | Sélectionnable |
| 6 | Bicubic | Interpolation douce avec davantage de détails que le bilinéaire selon la scène | Faible | Sélectionnable |
| 7 | Bilinear | Stable, doux, peu coûteux | Très faible | Sélectionnable |
| 8 | Nearest | Fort aliasing sur jeux 3D, mais pertinent pour le pixel art | Très faible | Sélectionnable |

**FSR 3.1 temporel arrive en tête uniquement si le renderer peut fournir de vraies données invitées cohérentes** : couleur avant HUD, profondeur, motion vectors, jitter, projection, masques et historique GPU correctement synchronisé. Le moteur Vulkan est présent, mais le producteur générique et le dispatch réel ne sont pas encore achevés. Il ne figure donc **pas parmi les 10 filtres navigables aujourd'hui**. Ne pas confondre avec **FSR 3 Frame Generation (R08)**, qui génère des images intermédiaires plutôt que de faire de la reconstruction spatiale/temporelle.

SGSR Edge, SGSR et FSR 1 peuvent changer de place après comparaison sur console. Seul Vulkan propose les deux SGSR ; Lanczos est aussi disponible avec OpenGL. Le curseur Netteté (%) ne s'applique actuellement qu'à FSR 1 et SGSR, avec des échelles différentes.

## Anti-aliasing — ordre cible unique pour les contours

| Rang | Filtre | Atout principal | Limite / risque | Statut |
| --- | --- | --- | --- | --- |
| 1 | **SMAA Ultra** | Lissage de contours sur l'image finale, y compris une partie des arêtes issues des shaders | Ne supprime pas tout le scintillement temporel | Sélectionnable |
| 2 | **MSAA forcé 16×** | Couverture géométrique très fine lorsque le rendu natif l'accepte | VRAM/bande passante élevées ; ne traite pas tout l'aliasing des shaders | **Raccordé en code, validation console requise** |
| 3 | **MSAA forcé 8×** | Couverture géométrique élevée | Coût et formats contraignants | **Raccordé en code, validation console requise** |
| 4 | **MSAA forcé 4×** | Bon lissage géométrique à coût moindre que 8×/16× | Ne traite pas forcément alpha-test, reflets, textures ou HUD | **Raccordé en code, validation console requise** |
| 5 | **FXAA+** | Atténue différents contours dans l'image finale | Peut flouter texte et détails | Sélectionnable |
| 6 | **MSAA forcé 2×** | Amélioration géométrique modérée sans post-flou | Bénéfice limité sur l'aliasing non géométrique | **Raccordé en code, validation console requise** |
| 7 | **FXAA** | Rapide et généraliste | Peut flouter les détails et laisser des escaliers | Sélectionnable |
| 8 | **Off** | Aucun lissage post-traitement ajouté | Escaliers visibles si aucune autre technique n'intervient | Sélectionnable |

**Pourquoi SMAA Ultra avant MSAA 16× ?** Cet ordre indicatif privilégie la qualité **globale** attendue sur des jeux Switch hétérogènes, pas uniquement la précision de rasterisation des triangles. Sur une scène dominée par les arêtes géométriques, **MSAA 16× peut être supérieur**, tandis que SMAA Ultra peut avoir une couverture plus large de contours déjà présents dans l'image finale. MSAA 2× n'est donc pas automatiquement supérieur à FXAA+. Aucun classement universel ni promesse de gain sur FC 27, BOTW ou NS2.

**MSAA Auto n'est pas un neuvième rang.** Il ne force rien : le renderer honore le nombre d'échantillons 1×/2×/4×/8×/16× demandé par le GPU invité. Les modes forcés exigent, eux, des surfaces hôtes MSAA distinctes, un pipeline graphique avec le bon sample count, les resolves couleur/depth/stencil appropriés et le respect strict des vues/aliasing/layouts invités. Le composant Vulkan couleur shadow/resolve **est maintenant raccordé
aux draws invités compatibles** ; il reste non qualifié tant que le
rendu PS5, la VRAM, la latence et les transitions ne sont pas validés.

Le classement FXAA+/FXAA reste à confronter à des captures. **Off** désactive seulement les traitements post-AA du menu, sans supprimer l'éventuel MSAA **natif du jeu**.

Le supersampling (SSAA) via la résolution interne est distinct : 1,25× ≈ 1,56× pixels ; 1,5× = 2,25× pixels ; 2× = 4× pixels. Cela ne devient pas du MSAA.

## Revue des recommandations encore-overrides

Minimum et Recommended : **conserver les réglages stables** jusqu'à
preuve console, sans généraliser SGSR Edge, FXAA+ ou SMAA Ultra.
High et Ultra : évaluer SGSR Edge / FSR 1 / SMAA Ultra par captures et frametimes. Réserver l'évaluation FSR 3.1 temporel et MSAA forcé aux configurations dont la prise en charge réelle est prouvée ; les overrides manuels pourront prendre des risques supplémentaires une fois les modes effectivement opérationnels.

Les fiches Title ID héritées du catalogue sont souvent de simples
copies des profils généraux, sans mesure du jeu concerné. Le simple
fait que la méthode soit compilée ne justifie pas de réécrire ces
fiches. Un changement de recommandation doit conserver la priorité
des overrides manuels, la compatibilité du renderer, et s'appuyer
sur des captures, des vidéos et des frametimes **mesurés sur PS5**.

Scènes prioritaires : FC 27 (pelouse, public, lignes et HUD, plans fixes
et panoramiques) et Zelda BOTW (feuillage, arêtes fines, mouvements).
Vérifier l'absence de régression NS1 ; aucune conclusion sur NS2 tant
que les frames invitées ne sont pas réellement présentées.

**Statut : ordre théorique documenté ; menu de base conservé, modes
MSAA 2×/4×/8×/16× ajoutés après FXAA+ (index 4-7). Le chemin Vulkan
couleur-only Clear→Draw→Resolve est intégré, mais non testé sur PS5.
FSR 3.1 temporel n'a pas de producteur générique qualifié et reste
non sélectionnable. Aucune valeur par défaut ni ID existant modifié.**
