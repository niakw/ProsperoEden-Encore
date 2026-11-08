# R09 — exécuteur Linux autonome pour DLSS-NR Original

Source : `tools/graphics/r09_full_gpu_host.cpp`.

## Chaîne implémentée

Le programme accepte directement **la seule DLL utilisateur `nvngx_dlssnr.dll`** :
l'importeur natif la traite comme des données (sans exécuter le PE), crée
un pack NRMODEL1 dans un répertoire temporaire privé (0700) et le supprime
au terme du programme, succès comme échec. Un pack NRMODEL1 déjà importé
reste accepté pour diagnostic interne. Dans les deux cas, les **599 empreintes
SHA-256 des vrais tenseurs** doivent être vérifiées avant Vulkan.

Le banc lit ensuite une capture RGBA8 1920×1080 (8 294 400 octets).
Il prépare les objets Eden `Device`,
`MemoryAllocator` et `Scheduler`, téléverse la capture sur Vulkan,
initialise `NrRdna2FrameSession` avec le plan Original de 152 lignes,
enregistre les étapes neuronales, attend le GPU et tente de produire
un readback RGBA32F de 33 177 600 octets.

Le chemin de sortie GPU est ouvert en accès privé (0600) et avec
création exclusive : il ne peut pas écraser un résultat existant, la
DLL NVIDIA ou la capture source. Un échec d'écriture ou de synchronisation
supprime le fichier de résultat incomplet. Utiliser un nouveau nom de
sortie à chaque essai.

Avant publication, le résultat RGB du readback doit avoir la taille
correcte, contenir uniquement des flottants finis et ne pas être
quasi constant. Cela n'est **ni une preuve de qualité ni une référence
indépendante**, et cela ne prouve pas les 152 étapes.

L'exécution complète **n'a pas encore été démontrée** sur un modèle
authentique dans la session hôte courante. Le code source, sa compilation
et une inférence effectivement terminée sont trois preuves distinctes.
Les nouveaux changements hôte restent non qualifiés par recompilation ;
l'ancien binaire publié ne les inclut pas. Pas de relance du build long
sans nouvelle autorisation.

## Qualification des sources et liaison Linux

- `R09 neural Vulkan host / SPIR-V ABI` : qualification hôte des **72**
  propriétaires C++ utilisés par la production, des **35** shaders RDNA2
  Vulkan 1.1 et des frontières CPU/Vulkan.
- `R09 full Vulkan host binary link (public-only)` :
  `.github/workflows/r09-host-link.yml`. La CI construit l'Eden amont
  et substitue seulement les interfaces Linux compatibles, compile
  les objets et cherche à lier `r09-full-gpu-host`. Les logs de cette
  CI sont le seul élément faisant foi pour annoncer une liaison réussie.
- Aucun build PS5, aucun test console, aucune DLL NVIDIA ni poids
  utilisateurs dans les artefacts GitHub.

L'ancienne vérification `r09_vulkan_io_smoke` ne suffit pas pour
valider le réseau : elle couvre seulement des opérations Vulkan
isolées.

## Contrôler un résultat réel (après exécution)

Le rapport JSON d'une session ne vaut pas en soi une trace GPU indépendante.
La commande de vérification exige le modèle, le plan, **les octets de la
capture réelle**, le readback GPU et une référence indépendante :

```bash
python3 tools/graphics/r09_verify_full_gpu_evidence.py \
  --evidence evidence.json \
  --model original.nrmodel \
  --plan original-plan.txt \
  --input capture-1920x1080.rgba8 \
  --output output.rgba32f \
  --reference independent-reference.rgba32f
```

Le vérificateur recalcule notamment les SHA-256 des 599 tenseurs, de la
capture, du plan et de la sortie ; il refuse un nombre d'opérations différent
de 152, l'absence de preuve déclarée de dispatch GPU et une référence qui
est le fichier de sortie ou une copie bit à bit de celui-ci. Ces tests
éliminent plusieurs faux positifs ; ils ne prouvent **pas** à eux seuls
qu'un JSON autodéclaré correspond à 152 dispatchs réellement effectués.
Une trace instrumentée et un oracle de référence de provenance indépendante
restent obligatoires avant d'annoncer une image DLSS-NR Original validée.

Pour exporter des aperçus PNG après un vrai readback, utiliser
`tools/graphics/r09_authentic_preview_png.py` ; ce convertisseur n'effectue
aucune inférence.

Les fichiers locaux (capture, modèle, référence, résultat) doivent rester
privés. Ne jamais les committer dans les dépôts publics.
