# R09 — première sortie couleur sans historique, 7 novembre 2026

## Travaux intégrés en source

Le GPU Vulkan RDNA2 peut désormais composer une image **RGBA32F normalisée**
à partir d'un proxy RGBA32F déjà normalisé et des seize caractéristiques FP16
de l'out_project appris. Les **trois premiers canaux** sont consommés comme
résidu RGB : `clamp(proxy + residual * 0.25, 0, 1)` puis interpolation
bornée à une intensité 0..1. L'alpha original fini est préservé.

Le shader refuse tout recours à FP8 matériel, matrices coopératives ou
extensions NVIDIA. Son ordonnanceur exige des buffers distincts, une géométrie
explicite, des capacités vérifiées, un identifiant de scheduler partagé et
un seul enregistrement. Entrées NaN/Inf sont neutralisées au pixel plutôt
que propagées dans l'image.

`NrRdna2CoreFeatureSequence` raccorde en code la séquence
prébloc -> U-Net descendant -> Split/ViT/décodeur -> U-Net montant ->
postbloc FP16 -> composition RGB **optionnelle de première image**.
L'entrée proxy FP16 doit être celle du prébloc et le compositeur doit
lire le même proxy d'origine. Le moteur désactive toute reprise silencieuse
après échec partiel. Le résultat GPU n'est déclaré qu'après enregistrement.

## Limites bloquantes (ne pas déclarer DLSS-NR terminé)

- Aucun historique de mouvement ni HDR reconstruit : seul un proxy LDR
  pré-normalisé a une sortie buffer possible. Ce n'est pas un présentateur PS5.
- Les 16 gains de chacun des C64/C128/C256 n'ont pas encore de découpage
  prouvé. Leur loader refuse les modèles incomplets plutôt que de supposer
  la correspondance avec residual_scale.
- Parité numérique avec une capture de référence, source colorimétrique
  réelle, textures jeu et conversion RGBA32F -> présentateur restent à prouver.
- Les tests CI hôte C++/UBSan et SPIR-V Vulkan 1.1 n'établissent ni
  une image effectivement produite sur GPU ni une exécution sur PS5.

Ce lot ne change pas les valeurs par défaut : **DLSS-NR OFF**, FrameGen OFF.
L'issue #15 suit séparément P0-P4 du moteur NS1/NS2 ; elle ne sert pas
de checklist de complétion DLSS. Aucun build console requis à cette étape.

## Entrée HDR externe (R09)
Le module `NrRdna2HDRProxy` relie désormais un buffer externe RGBA32F
linéaire à la création du proxy sRGB en appliquant le facteur paper-white,
l'épaule de hautes lumières et le transfert sRGB. Les vérifications hôte
refusent dimensions, capacités, tailles, poids de référence et géométries
invalides. L'orchestrateur vérifie que le même buffer est consommé par le
prétraitement 16 canaux et par le compositeur RGB. Le GPU enregistre l'ordre
HDR → proxy → prébloc → réseau → composition, uniquement sans historique.
La capture image du renderer, la sémantique des guides NS1/NS2, le chargement
des poids complets et la présentation PS5 ne sont pas validés.
