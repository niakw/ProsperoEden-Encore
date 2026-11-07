# R09 — Prévalidation CPU avant construction GPU

Date : 7 novembre 2026. Travail exclusivement sur les deux branches `main`.

**Correctif** : `NrRdna2FrameSession::Initialize` ne construit plus
`State`, ses propriétaires de pipelines, modules SPIR-V et descripteurs
Vulkan, avant d'avoir vérifié le fichier NRMODEL1 de l'utilisateur.

La nouvelle frontière précoce impose dans cet ordre :

1. Ouverture et vérification de l'index de poids sans objet Vulkan.
2. Parsing du plan natif et sélection strictement fondée sur 152 ou
   76 opérations.
3. Vérification du manifest exact Original/Compact (599 ou 255 noms,
   avec au plus un vrai coefficient temporel FP16 supplémentaire).
4. Construction **CPU** du graphe U-Net, routes Split-Swin et ViT,
   puis validation de la géométrie et du format d'image.
5. **Uniquement après tout cela** : création de l'état Vulkan, transfert
   des structures prévalidées, puis préparation des poids et buffers GPU.

Ainsi un pack manquant, corrompu, incomplet ou du mauvais modèle
ne demande plus la construction d'une session Vulkan coûteuse.
La reconstruction échoue de manière conservatrice avant tout
enregistrement de commandes.

La qualification hôte contrôle la compilation complète des classes
Vulkan R09 mais **ne prouve pas** une image entière inférée avec des
poids NVIDIA authentiques sur GPU. C'est la frontière de validation
fonctionnelle finale non résolue. Aucun build PS5 global.
