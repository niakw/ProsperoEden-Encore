# R09 — entrée Vulkan depuis l'image réelle du guest

7 novembre 2026. Travaux sur les deux main uniquement.

`NrRdna2TextureProxy` peut maintenant convertir une vraie texture
Vulkan échantillonnable du renderer en buffer RGBA32F transposé,
pré-normalisé pour les 16 caractéristiques neuronales.

- Format explicite : R8G8B8A8_UNORM/B8G8R8A8_UNORM en LDR déjà
  encodé, ou R16G16B16A16_SFLOAT/R32G32B32A32_SFLOAT pour HDR
  linéaire normalisé par paper-white et une épaule.
- Les formats sRGB avec décodage implicite sont refusés plutôt que
  traités comme de l'UNORM.
- La texture physique 1920×1080 se transpose explicitement vers
  le raster du plan natif 1080×1920 (et inversement à la sortie).
- View et sampler doivent rester vivants et accessibles depuis
  le même Vulkan scheduler ; l'entrée est en GENERAL avant usage.
- Les buffers internes sont bornés et distincts, et les modes
  de couleur/étendues invalides sont refusés sans dispatch.
- L'orchestrateur `NrRdna2CoreFeatureSequence` accepte cette
  entrée comme source alternative à `NrRdna2HDRProxy`, sans
  laisser les deux sources publier sur le même buffer.

Cette primitive complète les extrémités source/sortie du graphe
sur des ressources Vulkan réelles. **Elle ne suffit pas à
brancher automatiquement le système d'images du jeu au rendu
DLSS-NR** : la session native doit encore construire les
modules et tous leurs buffers, sélectionner l'entrée depuis
`Layer::ConfigureDraw`, gérer histoire/mouvement et passer
une première image de modèle complet sur GPU.

CI hôte SPIR-V + syntaxe réelles requises. Pas de build PS5
global, pas de branche/PR ni paramètres NR activés par défaut.
Ce travail reste distinct de la roadmap moteur #15.
