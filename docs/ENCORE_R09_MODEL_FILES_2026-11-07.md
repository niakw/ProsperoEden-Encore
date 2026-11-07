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

Le code actuel `headless/vulkan_present_layer_r24.cpp`
recherche encore des packs `NRMODEL1` préextraits dans le
dossier `neural/` de la configuration ; il **ne sait pas encore
consommer directement `nvngx_dlssnr.dll`**. Le test de
prérequis CI Original/Compact, la reconstruction du pack, la gestion
du cache utilisateur et les messages d'import sont **à intégrer
dans l'application** avant de déclarer ce contrat livré.

Le moteur utilise `NrRdna2FrameSession` avec les plans natifs
Original (152 étapes) ou Compact (76) et précontrôle les matrices
d'entrée/sortie. La preuve de bout en bout avec les vrais poids
et une image calculée reste également nécessaire. Aucune évaluation
ou construction PS5 n'est demandée pendant cette phase.

Les anciens chemins `original.nrmodel` / `compact.nrmodel`,
`dlssnr.bin` / `dlssnr-small.bin` sont des noms **internes du
cache moteur**, pas des prérequis à imposer à l'utilisateur.
