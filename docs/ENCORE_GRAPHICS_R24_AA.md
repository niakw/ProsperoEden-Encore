# Eden Encore — R24 Antialiasing Vulkan : audit et correctif

Statut au 5 novembre 2026 : **code R24 source intégré dans une branche dédiée**,
pas de build PS5 complet ni capture graphique de console.

## Ce qui existait réellement

- Le réglage global et l'override par titre propagent déjà
  `none / fxaa / smaa` à `Settings::values.anti_aliasing`.
- L'implémentation Vulkan possède de vraies passes FXAA et SMAA. Le
  shader SMAA de l'upstream sélectionne **`SMAA_PRESET_ULTRA`** dans
  ses passes. Créer un niveau « Ultra » de plus dans le menu aurait
  été mensonger.
- La couche de présentation exécute FXAA/SMAA **avant** FSR spatial.
  Le HUD natif PS5 est dessiné séparément à la fin du composite.
  Le HUD *du jeu invité* reste intégré à la framebuffer Switch.
- Aucun MSAA 2x/4x/8x ni TAA temporel complet ne peut être annoncé :
  l'AA postprocess ne sait pas fabriquer les vrais échantillons de
  rasterization ; les motion vectors et la depth guest ne sont pas
  suffisamment fiables pour un TAA complet.

## Défaut corrigé

Le fork Vulkan R08 créait les surfaces FXAA/SMAA avec
`ScaleUp(raw_width/raw_height)`. Or l'image passée au filtre n'a
pas nécessairement cette dimension : le chemin de copie raw n'est
pas une texture multipliée par le facteur de résolution ; une
image accélérée a des `scaled_width/scaled_height` effectifs qui
peuvent changer indépendamment du réglage demandé.

La nouvelle unité maintenue `headless/vulkan_present_layer_r24.cpp`
utilise **la dimension de l'image source réelle** au moment de
`ConfigureDraw` :

1. Pas de source accélérée : dimension native de la framebuffer.
2. Source accélérée : dimension `scaled_width/scaled_height`.
3. Dimension nulle ou plus de 8192 : pas de pass AA créé.
4. Changement de dimension après resize ou ajustement dynamique :
   destruction/recréation des surfaces et descriptors après le
   `Scheduler::Finish` / `WaitIdle` déjà présents sur PS5.
5. Mode None : aucune allocation AA, pas de reconstruction par image.

`vulkan_present_layer_r24.h` est le header unique compilé avec la
source dans le port natif. Le CMake change uniquement la source
maintenue du port, pas le vendor épinglé. L'ancien fork reste
disponible pour audit. L'ordre AA → FSR → composite HUD n'a pas été
changé ; les choix sauvegardés non plus.

## Preuves hôte et limites

- Test `AaSourceExtent` compile en C++20 (dimensions raw, escaladées,
  dynamiques, hors limites et nulles), avec ASan/UBSan, assertions
  actives aussi en Release.
- Contrôle source des deux unités et de leur sélection par CMake,
  maintien des overrides de titre et des modes existants.
- **À faire sur PS5** : compiler le jeu complet et comparer les mêmes
  images fixes/mobiles sur FC27/BOTW, ainsi que coût GPU/VRAM.
  Les tests hôte prouvent le bon routage des dimensions, pas l'effet
  perceptuel sur un téléviseur.
