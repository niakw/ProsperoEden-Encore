# Eden Encore — classement théorique de qualité graphique (R07/R24)

**5 novembre 2026 · PR #24 · code hôte vérifié, rendu PS5 non validé.**

Il n'existe pas de classement universel. L'ordre ci-dessous vise la restitution
spatiale d'une image 3D sous-résolue et le traitement de contours, **sur le
papier uniquement**. Scintillement, transparence, finesse du HUD, budget GPU
et échelle interne peuvent inverser plusieurs positions. Dans l'interface,
le parcours suit cet ordre du meilleur présumé au plus simple, **sans
changer les IDs sauvegardés**. Les options non compatibles sont sautées.

## Upscaling spatial — classement pour jeux 3D

| Rang | Filtre | Qualité présumée | Coût relatif non mesuré |
| --- | --- | --- | --- |
| 1 | SGSR Edge | Reconstruction dirigée par les contours ; risque de halos | Moyen / élevé |
| 2 | SGSR | Reconstruction spatiale avancée, parfois plus douce | Moyen |
| 3 | AMD FSR 1 (EASU/RCAS) | Bon compromis agrandissement / détails, netteté réglable | Moyen |
| 4 | Lanczos | Netteté élevée, possibles halos (ringing) | Faible / moyen |
| 5 | Bicubic | Interpolation supérieure au bilinéaire sur détails | Faible |
| 6 | Bilinear | Stable, doux, économe | Très faible |
| 7 | Nearest | Escaliers sur les jeux 3D ; **préférable en pixel art** | Très faible |

SGSR Edge, SGSR et FSR 1 peuvent échanger leur place après de vrais tests.
Seul Vulkan propose les deux SGSR ; Lanczos fonctionne également avec OpenGL.
Netteté (%) est actif seulement pour FSR 1 et SGSR (échelles différentes).

**FSR 3.1 temporel n'est pas livré et n'est PAS une option de ce tableau.**
Sa reconstruction nécessite historique couleur, motion vectors, profondeur,
jitter et masques réactifs fiables, avec resynchronisation et résolution.
Bien alimenté, il pourrait réduire le scintillement mieux que les filtres
spatiaux ; avec de fausses entrées, il produit du ghosting. Ne pas le
confondre avec FSR 3 frame generation, qui synthétise des frames affichées.

## Anti-aliasing — classement pour les contours

| Rang | Filtre | Avantage | Risque |
| --- | --- | --- | --- |
| 1 | SMAA Ultra | Passe multiphase, contours précis | Plus coûteux, n'élimine pas le shimmer |
| 2 | FXAA+ | FXAA avec recherche de contours étendue | Texte et textures potentiellement plus flous |
| 3 | FXAA | Léger, rapide | Détection moins détaillée |
| 4 | Off | Aucun coût/aucun flou ajouté | Escaliers visibles |

L'ordre de FXAA+ et FXAA peut s'inverser si l'on privilégie la netteté
plutôt que la force du lissage. SMAA Ultra existait déjà ; FXAA+ est un
shader distinct non encore jugé visuellement sur PS5.

**MSAA x2/x4/x8 NON livré.** Ce sont des nombres d'échantillons de
rasterisation, non des intensités du post-AA. Ils exigent des render
targets multisamples, un resolve et la compatibilité sémantique avec
les surfaces du GPU invité : aucune de ces preuves n'est acquise.
Le supersampling (SSAA) est déjà offert par la résolution interne :
1,25x = ~1,56x pixels, 1,5x = 2,25x pixels, 2x = 4x pixels.
Ce n'est pas du MSAA.

## Revue des recommandations encore-overrides

Minimum et Recommended : **conserver les réglages stables** jusqu'à
preuve console, sans généraliser SGSR Edge, FXAA+ ou SMAA Ultra.
High et Ultra : ajouter SGSR Edge / FSR 1 / SMAA Ultra à la file
d'évaluation A/B, mais aucune promotion automatique.

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

**Statut : classement théorique documenté, tests hôtes seulement.
R07 temporel et R24 MSAA demeurent ouverts.**
