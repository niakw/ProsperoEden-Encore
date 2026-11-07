# R09 — publication de la première image neuronale Vulkan

7 novembre 2026. R09 DLSS-NR, distinct de la roadmap moteur #15.

`NrRdna2NoHistoryPresent` convertit le raster RGBA32F produit
par `NrRdna2NoHistoryCompose` en une image Vulkan exploitable par
le présentateur. Le shader effectue explicitement la transposition
des axes du plan natif : raster 1080×1920 vers image 1920×1080.
La composition, puis la publication, s'enregistrent sur le même
scheduler. Refus des tailles incohérentes et du format inadapté.

L'image cible est détenue par l'appelant, doit utiliser le format
`VK_FORMAT_R32G32B32A32_SFLOAT`, avoir les usages STORAGE et
SAMPLED, être en `VK_IMAGE_LAYOUT_GENERAL` avant le dispatch et
rester vivante jusqu'à la fin de la soumission. Les capacités
de format de l'hôte sont vérifiées. La barrière compute-write →
shader-read est enregistrée avant consommation par le rendu final.

Le code ne sélectionne pas encore automatiquement cette image dans
`Layer::ConfigureDraw`. L'allocation/initialisation d'une session
complète à partir d'un modèle Original/Compact et la capture des
images guest ne sont pas intégrées. Aucune image réelle du modèle
n'est encore démontrée sur GPU. Aucun test console PS5 n'a été lancé.
Ne pas présenter cette primitive comme une fonction utilisateur achevée.
