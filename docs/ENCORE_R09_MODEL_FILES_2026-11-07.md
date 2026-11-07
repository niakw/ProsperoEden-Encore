# R09 — contrat des modèles Original et Compact

État au 7 novembre 2026 : raccord moteur→vendor synchronisé, CI hôte
et tests GPU de composition validés. Les poids réels ne sont **pas**
fournis ni embarqués dans Eden Encore.

La sélection du jeu est explicite et demeure facultative. Les deux
modèles prennent en charge un pack au format `NRMODEL1` validé par
`NrRdna2FrameSession`. Le présentateur cherche uniquement dans le
répertoire de configuration de l'application sous `neural/` :

| Choix | Nom Encore prioritaire | Nom issu de l'extracteur amont |
| --- | --- | --- |
| DLSS-NR Original (152 étapes) | `original.nrmodel` | `dlssnr.bin` |
| DLSS-NR Compact (76 étapes) | `compact.nrmodel` | `dlssnr-small.bin` |

Le modèle utilisateur doit correspondre au graphe sélectionné, avec
les véritables blocs et tenseurs nécessaires. Si les deux noms
existent, le fichier au nom Encore est prioritaire ; un pack
incomplet est refusé sans nouvelle tentative silencieuse sur
l'autre modèle. Aucun téléchargement non sollicité et aucune
recherche sur tout le disque ne sont effectués.

Les noms `dlssnr.bin` et `dlssnr-small.bin` sont les sorties du
script MIT `linux/package/model-tools/extract_model.sh` de
`Overclockers/DLSSNR-AMD`. Il extrait les données d'une copie
licite de `nvngx_dlssnr.dll` détenue par l'utilisateur. Les
modèles NVIDIA ne sont pas redistribués par le projet amont.

Ce support de nom de fichier ne constitue pas une preuve
d'équivalence neuronale : une vraie image calculée par le graphe
complet Original et Compact sur GPU, sa lecture et sa présentation
restent à valider avant de marquer R09 terminé.
