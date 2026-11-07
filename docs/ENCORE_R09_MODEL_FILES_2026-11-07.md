# R09 — contrat d'import : **une seule DLL utilisateur**

**Décision produit confirmée — 7 novembre 2026.** L'utilisateur
fournit **un seul fichier `nvngx_dlssnr.dll`**. Eden Encore doit
détecter ce fichier, identifier les ressources neuronales réellement
présentes, importer et vérifier les poids compatibles, et gérer
son cache automatiquement. **Aucune extraction Python, aucun pack
`.nrmodel` et aucun second fichier ne doivent être exigés de
l'utilisateur.** Ne pas distribuer la DLL ni les poids extraits dans
les dépôts, releases ou artifacts de CI.

## Constat vérifié sur la DLL de référence apportée par l'utilisateur

- SHA-256 du fichier entier :
  `dcc0dc2414aedec4a8e084647070383be068554042587180c20c784d4772d36f`.
- DLL PE32+ x64 : `165840496` octets.
- Ressource interne `WEIGHTS_HT` : `147695410` octets, SHA-256
  `836f445d06ecd2e59bb9f17b84b91c143396fd76ccda1c9dc7fe81d5edd548f4`.
- Enveloppe de poids `WEIGHTS_HT` : **153 records** valides à
  l'inspection structurelle. Ressource `WEIGHTS_CC_SMALL_FP8`
  **absente** dans le fichier examiné.

Ne **jamais** rejeter une ressource Original parce que le SHA-256
de la DLL entière diffère d'une liste figée, si les poids extraits
peuvent être validés individuellement contre les **599 empreintes**
de référence. Le SHA du binaire complet et le contenu des ressources
sont deux niveaux d'intégrité différents. Une correspondance
d'empreinte de ressource ne prouve pas automatiquement la validité
de la signature Authenticode de l'ensemble du PE.

Le mode **Original** peut être importé depuis `WEIGHTS_HT` sous
réserve de validation complète des 599 tenseurs par SHA-256 et
d'exécution GPU du graphe. Le mode **Compact** ne doit **jamais**
réutiliser les poids Original ou afficher un faux succès : si la
ressource Compact n'existe pas dans la DLL fournie, il est signalé
indisponible (sélection persistante conservée). **Ne pas demander
une deuxième DLL** à l'utilisateur pour contourner cette absence.

## État réel de l'implémentation

Le commit `2bfbeae` intègre **l'importeur natif**
`headless/nr_dll_model_import.h`, raccordé à
`Layer::ConfigureDraw` dans `headless/vulkan_present_layer_r24.cpp`.

Si le jeu utilise Original et qu'aucun pack validé n'est encore présent,
le présentateur recherche le **seul fichier** `nvngx_dlssnr.dll`
dans les emplacements privés suivants (dans cet ordre) :

1. **Chemin utilisateur recommandé** : `/data/prosperoeden/user/dlssnr/nvngx_dlssnr.dll`
   (ou `<UserDir>/dlssnr/nvngx_dlssnr.dll` en mode sandbox).
2. Compatibilité anciens dépôts : `<ConfigDir>/neural/nvngx_dlssnr.dll`.
3. Compatibilité anciens dépôts : `<ConfigDir>/nvngx_dlssnr.dll`.
4. Compatibilité anciens dépôts : `<UserDir>/nvngx_dlssnr.dll`.

Le dossier `user/dlssnr/` suit exactement la convention du dossier
`user/lossless/` pour `Lossless.dll`. Il n'y a qu'une DLL à fournir ;
les autres chemins sont des fallbacks de migration et non des fichiers à installer.

Il analyse les ressources du PE **sans exécuter la DLL**, vérifie
le SHA-256 exact de `WEIGHTS_HT`, reconstruit tous les tenseurs,
écrit un pack NRMODEL1 temporaire puis publie
`<ConfigDir>/neural/original.nrmodel` dans le cache privé.
Aucun script ou deuxième fichier n'est nécessaire à l'utilisateur.
Le mode Compact ne reçoit jamais les poids Original par substitution.

**Qualification hôte réelle, sur la DLL utilisateur (hors GitHub)** :
les 599/599 noms ET empreintes SHA-256 de la sortie native
correspondent aux 599 références publiques, dont 24 tensors bruts,
400 Swin, 115 Split-Swin, 40 ViT, 9 prébloc et 11 postbloc.
Le pack de sortie mesure environ 141 MiB et n'est **pas diffusé**.
La CI publique compile l'importeur et teste le refus d'entrées
non conformes sans distribuer aucune donnée NVIDIA.

**Restes distincts** : l'interface graphique de sélection/import de
DLL (les trois chemins ci-dessus étant le raccord moteur actuel),
l'exécution Vulkan intégrale du modèle Original avec image numérique
de référence, ainsi que le mode Compact lorsque ses propres poids
sont réellement présents. Les tests console restent reportés.

Le moteur utilise `NrRdna2FrameSession` avec les plans natifs
Original (152 étapes) ou Compact (76) et précontrôle les matrices
d'entrée/sortie. La preuve de bout en bout avec les vrais poids
et une image calculée reste également nécessaire. Aucune évaluation
ou construction PS5 n'est demandée pendant cette phase.

Les anciens chemins `original.nrmodel` / `compact.nrmodel`,
`dlssnr.bin` / `dlssnr-small.bin` sont des noms **internes du
cache moteur**, pas des prérequis à imposer à l'utilisateur.
