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
- Le **vrai MSAA 2×/4×/8×/16× demandé par le guest** existe
  dans les pipelines Vulkan de l'émulateur. Le **forçage utilisateur**
  n'existe pas encore : il faut des surfaces hôtes temporaires et
  un resolve compatible guest, et non multiplier les passes SMAA.
- Le moteur AMD FSR 3.1 temporel est compilable dans le vendor,
  sans source générique de motion/profondeur/projection pour
  les jeux ; il n'est pas encore effectif dans les rendus PS5.

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

## FXAA+ — deuxième shader FXAA (nouveau R24)

- L'algorithme FXAA original, léger, garde son identifiant 1. SMAA
  Ultra garde l'identifiant 2 et ses 3 passes historiques.
- Nouvelle option 3 : **FXAA+**, recherche spatiale étendue ;
  shader dans headless/fxaa_quality.frag. Le choix ne redirige pas
  le même shader : Vulkan utilise un second module SPIR-V compilé
  via glslangValidator, sans modification du vendor.
- Distinctions : FXAA_SPAN_MAX 12 au lieu de 8 ;
  FXAA_REDUCE_MUL 1/16 au lieu de 1/8 ;
  FXAA_REDUCE_MIN 1/256 au lieu de 1/128. Cela modifie
  le comportement sur des contours faibles/fins, mais peut flouter ;
  **aucune supériorité visuelle n'est affirmée avant capture PS5**.
- Les identifiants et les profils antérieurs restent stables.
  L'option est proposée globalement et par jeu sur Vulkan ;
  l'app refuse le nouveau choix si le renderer est OpenGL.
- Tests : compilation des deux modules SPIR-V, validation spirv-val,
  empreintes différentes, source native de sélection, atomique
  inter-threads, persistence des préférences et des overrides titres.

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
