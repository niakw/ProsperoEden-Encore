# R09 — validation du manifest Original/Compact avant allocation GPU

État du 7 novembre 2026, dépôts `main` uniquement.

Un pack `NRMODEL1` peut être structurellement valide tout en contenant
un inventaire incomplet ou issu du **mauvais modèle**. Avant ce
correctif, le runtime pouvait commencer à allouer des centaines
de ressources Vulkan avant de détecter cette incohérence.

Le loader R09 vérifie dorénavant, dès l'ouverture de la session,
la **liste exhaustive des noms de tenseurs** attendus :

- Original : exactement **599 entrées**.
- Compact : exactement **255 entrées**.
- Noms, doublons, tailles nulles et familles incorrectes sont refusés,
  avant le premier tampon Vulkan alloué par la session.
- La vérification compare des listes de noms, **jamais les poids**.
- Une différence d'ordre des entrées reste acceptable ; les noms
  doivent correspondre exactement. Les variantes modifiées ou
  enrichies ne sont pas acceptées sans qualification distincte.

Source de données de référence (textes MIT, aucun poids NVIDIA) :
[DLSSNR-AMD model-files.txt](https://github.com/Overclockers/DLSSNR-AMD/blob/main/linux/package/model-tools/model-files.txt)
et [model-files-small.txt](https://github.com/Overclockers/DLSSNR-AMD/blob/main/linux/package/model-tools/model-files-small.txt).

Ce contrôle ne remplace **pas** la vérification des poids,
les chargements matriciels, l'exécution de tous les shaders ni
la validation numérique d'une image sur GPU. Aucune DLL/aucun
modèle propriétaire n'est embarqué.
