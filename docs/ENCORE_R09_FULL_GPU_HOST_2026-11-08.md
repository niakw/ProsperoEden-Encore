# R09 — source Linux pour l'exécuteur Original autonome

Fichier : `tools/graphics/r09_full_gpu_host.cpp`.

Point d'entrée C++ réel qui ouvre un modèle utilisateur `NRMODEL1` Original,
lit une capture **réelle** 1920×1080 RGBA8 (8 294 400 octets), crée les
objets Eden `Device`, `MemoryAllocator` et `Scheduler` sur un dispositif
Vulkan hôte, téléverse la capture, prépare
`NrRdna2FrameSession` avec le plan Original intégré de 152 lignes,
appelle `ExecuteR09FrameAndReadback`, attend les travaux GPU et écrit
le résultat RGBA32F (33 177 600 octets).

La capture de départ, les poids et les sorties restent exclusivement
sur le poste qui exécute le programme. **Aucune DLL ni poids sur GitHub.**

**Limitations vérifiables** : ce fichier est seulement un point d'entrée
source. Le pipeline GitHub actuel l'inscrit au contrôle de **syntaxe C++**
mais ne le **lie pas en binaire Linux complet**. Sa compilation, son
démarrage et son exécution avec les vraies données et un oracle indépendant
ne sont **pas encore qualifiés**. Le wrapper `DownloadColorImage` produit
une véritable copie GPU mais le compte de callbacks n'est pas un compte
de 152 dispatchs complétés. Sans instrumenter et vérifier le passage des
opérations individuelles, aucune mention de « DLSS-NR complet » n'est permise.

La construction hôte doit lier le moteur Vulkan Eden maintenu et **tous**
les opérateurs R09 + leurs shaders SPIR-V. L'ancienne CI
`r09_vulkan_io_smoke` ne suffit pas : elle ne lance pas ce binaire.
