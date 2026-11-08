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

## Tentative du réseau complet depuis un Mac Apple Silicon

Un nouveau lanceur **différent du kit de fixtures**, `tools/graphics/r09_run_full_network_mac.sh`,
tente l'exécution de `r09-full-gpu-host` en Linux x86-64 émulé par
Docker. Il nécessite `gh` authentifié, Docker lancé et Python 3 sur
macOS. Il **ne compile pas l'ensemble d'Eden** et n'emploie pas la
console PS5.

```bash
cd /tmp/eden-encore-fix
git switch main
git pull --ff-only origin main
git submodule update --init --recursive
gh auth status
docker info >/dev/null
bash tools/graphics/r09_run_full_network_mac.sh \
  "$HOME/Downloads/nvngx_dlssnr.dll.zip" \
  "$HOME/Downloads/une-vraie-capture.png"
```

**Colima Apple Silicon** : une VM `aarch64/arm64` avec
l'ancien constructeur Docker ignore parfois `--platform linux/amd64` :
elle construit une image Ubuntu ARM64, qui ne peut pas charger notre
exécutable Linux x86-64. L'architecture du conteneur est **nécessairement
amd64**, pas seulement celle demandée au constructeur.

Ne pas supprimer le profil Colima existant. Créer à la place une VM
x86-64 QEMU dans un profil séparé :

```bash
# Facultatif mais conseillé sur un Mac M1 à 8 Go : arrête le Colima
# habituel si ses conteneurs ne servent pas, pour libérer la mémoire.
colima stop default
colima start r09 --arch x86_64 --vm-type qemu \
  --cpu 2 --memory 5 --disk 30 --activate=false
DOCKER_CONTEXT=colima-r09 bash tools/graphics/r09_run_full_network_mac.sh \
  "$HOME/Downloads/nvngx_dlssnr.dll.zip" \
  "r2_f0e3f8c4-e731-49bc-af9e-715676f73e14.jpg"
```

`colima stop default` interrompt ses conteneurs mais ne supprime
aucune image ni donnée ; ne le faire que si l'arrêt est acceptable.
Le profil `r09` conserve des conteneurs et volumes séparés.
Le lanceur refuse maintenant très tôt les VM Colima ARM64 et évite de
recompiler/retélécharger inutilement pour aboutir à un mauvais format.
Les fichiers C++ publics sont copiés de `/tmp` vers l'espace privé
`$HOME/.cache`, car une nouvelle VM Colima peut ne pas monter
`/tmp/eden-encore-fix` depuis macOS.

Sans second argument, le lanceur réalise une capture de l'écran Mac.
Elle permet un essai technique du pipeline mais **ne constitue pas une
capture de jeu ou une référence de qualité NVIDIA**. Un fichier RGBA8
1920x1080 peut être donné directement comme deuxième argument.

Le lanceur télécharge l'**ancien binaire lié** du workflow
[42465459699](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42465459699),
puis authentifie la DLL localement et crée un NRMODEL1 privé en
mémoire/disque local, compatible avec cet exécutable. Les extensions
récentes du code hôte ne sont **pas** incorporées dans l'ancien binaire.
La réussite de la compilation C++ sur GitHub n'est pas la preuve de son
exécution. La date d'expiration de cet artefact public est le
**15 novembre 2026** ; à son expiration il faudra publier un nouvel
exécutable public via la CI manuelle, pas transmettre les poids NVIDIA.

La compilation de l'image Docker peut installer plusieurs bibliothèques
Linux, mais **aucune reconstruction complète d'Eden n'est lancée**.
Sur un Mac M1 de 8 Go, l'émulation amd64 et le pipeline 1080p peuvent
épuiser la mémoire ou être très lents ; un refus mémoire ou Vulkan doit
être rapporté, pas interprété comme une validation.

Sorties privées locales : `~/.cache/eden-encore-r09-private/full-network-*/`,
dont `r09_full_network.log`. En cas de succès de l'exécuteur, des
aperçus `r09_before_real.png` et `r09_after_unverified_gpu.png`
sont générés. Le modèle et la copie de la DLL sont supprimés à la fin.
**Seul le journal** est nécessaire au diagnostic, jamais la DLL, le
modèle ou la capture personnelle.

Même une sortie RGBA32F correcte ne démontre pas à elle seule 152
opérations calculées ni une qualité DLSS-NR : il manque encore la
trace GPU instrumentée et la comparaison à une référence indépendante.

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
