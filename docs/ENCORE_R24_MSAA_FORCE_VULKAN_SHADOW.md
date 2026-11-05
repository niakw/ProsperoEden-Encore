# R24 — MSAA forcé : architecture réelle Vulkan, périmètre et contraintes

Révision 6 novembre 2026. **La PR #24 ne livre pas encore de réglage actif
de MSAA forcé.** Le GPU émulé conserve la prise en charge automatique
du MSAA 1×/2×/4×/8×/16× demandé par les jeux.

## Piste Vulkan vérifiée

L'extension Vulkan
[VK_EXT_multisampled_render_to_single_sampled](https://docs.vulkan.org/features/latest/features/proposals/VK_EXT_multisampled_render_to_single_sampled.html)
sait dessiner avec N échantillons dans une cible 1× et résoudre
implicitement la couleur. Dans le RADV **épinglé** de PS5 :
`encore-active/ps5-mesa/src/amd/vulkan/radv_physical_device.c`,
`radv_msrtss_enabled` l'annonce uniquement sous Android ou
quand `RADV_EXPERIMENTAL_MSRTSS` est demandé. Pour une compilation
PS5 standard, **cette extension n'est donc pas présumée disponible**.
Ne pas contourner son garde-fou ni l'activer expérimentalement.

## Primitive Vulkan native ajoutée

Le vendor fournit :
- `msaa_color_shadow_pass.cpp` et son header : création effective
  d'une **image Vulkan multisample** à N échantillons, puis framebuffer
  et **render pass Vulkan avec `pResolveAttachments`** pointant vers
  la vue 1× originale du jeu. L'image du jeu n'est jamais recréée
  avec une topologie mémoire modifiée.
- `MsaaForce::Evaluate` : vérifie la capacité N réellement
  disponible, le format couleur, dimensions, budget mémoire,
  échantillons déjà demandés par le guest et l'absence d'alias.
- Le chemin actuel refuse toutes les passes sauf une **seule
  attache couleur**, couche 1, **clear intégral**, **sans profondeur**
  ni texture lue/écrite en alias. Le buffer MSAA transitoire
  doit être invalidé avant la passe et résolu à sa fin.
- Réinitialisation/déstruction des objets seulement après
  `scheduler.Finish`. Un échec d'allocation renvoie un refus.

## Ce qui reste nécessaire pour l'activer

Le pipeline graphique du jeu doit être instancié avec la même valeur
`VkPipelineMultisampleStateCreateInfo.rasterizationSamples` que le
framebuffer multisample. L'implémentation ne peut pas se limiter à
`MaxwellToVK::MsaaMode` global : le jeu peut simultanément dessiner
dans des targets 1×, 2× et profondeur, avec écriture CPU/GPU et
alias invités. Il faut router un **draw/pass complet** uniquement si
ses cibles et ses lectures sont sûres, invalider les caches concernés,
et revenir à l'ancien chemin pour toute passe incompatibles.
Les passes LOAD/clear partiel, profondeur/stencil, plusieurs MRT et
accès texture concurrents sont donc **non prises en charge à ce jour**.

La primitive est incluse au `video_core` natif dans CMake et passe
une compilation syntaxique Clang contre le renderer Eden.
**Elle n'est pas encore raccordée aux pipelines de dessin du jeu.**
Aucun menu Auto/2×/4×/8×/16× n'est présenté comme fonctionnel.

Ce n'est **pas** du SMAA/FXAA répété : la primitive crée
réellement des attachments `VK_SAMPLE_COUNT_2/4/8/16_BIT` quand
le GPU et le format le permettent, avec resolve Vulkan natif.
Mais jusqu'à son raccordement guest, il n'y a pas d'amélioration
graphique observable à revendiquer sur PS5.
