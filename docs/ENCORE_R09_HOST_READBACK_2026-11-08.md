# R09 — véritable lecture GPU synchronisée, distincte du banc Linux complet

Date : 8 novembre 2026. Vendor `43378dc1b6edb620acac95625d6875cdbcd87621`.

## Code intégré

Le vendor contient `NrRdna2FrameGpuReadback` et
`ExecuteR09FrameAndReadback` (`nr_rdna2_frame_readback.cpp`).
C'est un raccord **fonctionnel et explicitement opt-in**, appelé par un hôte
qui possède **déjà** `Vulkan::Device`, `MemoryAllocator`, `Scheduler`,
les images et leurs vues et un `NrRdna2FrameSession` préparé avec le
véritable pack personnel.

Le raccord réserve **avant** `Record` un buffer de téléchargement 1920×1080
RGBA32F, refuse une image ou une file étrangère, déclenche la **vraie**
séquence complète via `NrRdna2FrameSession::Record`, enregistre une vraie
copie image→buffer avec barrières compute→transfer→host, utilise
`Scheduler::Finish` pour soumettre et attendre le GPU, invalide le cache
du staging puis renvoie les octets réels. En cas de refus après
enregistrement partiel, il fait un `Finish` avant de laisser détruire les
propriétaires du modèle.

Ce n'est **pas** une multiplication d'images synthétiques, ni une copie de
données de test. La méthode n'invente aucun compte de `vkCmdDispatch`.

## Limites non masquées

- L'adaptateur **n'est pas un exécutable Linux autonome** : il reste à
  initialiser le runtime Vulkan du moteur (Device, Scheduler, VMA, pipelines),
  importer une véritable capture 1920×1080, appeler ce raccord et exporter le
  buffer reçu dans un outil hôte exécutable.
- Un compteur de callbacks enregistrés n'est **pas** la preuve d'exécution
  de chacune des 152 opérations du plan Original. Un véritable traceur
  de commandes/pipelines par étape est requis pour produire cette preuve.
- Aucun accès aux poids NVIDIA privés n'est fourni à GitHub Actions ; aucun
  résultat de ce raccord n'est encore certifié contre une référence d'image
  indépendante. Les références 599/599 et le préflight ne remplacent pas
  l'exécution.
- Ni build PS5, ni test console. Aucun changement d'option utilisateur ;
  l'appel est opt-in et n'est pas automatiquement déclenché en jeu.

**Critère de sortie R09 inchangé** : lancer un exécutable hôte avec le vrai
modèle et une véritable image de source, observer le passage complet des 152
opérations, attendre le GPU et obtenir une sortie RGBA32F comparée à un oracle
indépendant. Tant que ce critère n'est pas démontré, annoncer R09 « terminé »
serait incorrect.
