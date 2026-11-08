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

**État actuel : ne pas relancer le test complet sans nouvel exécutable.**
L'ancienne liaison publique du workflow
[42465459699](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42465459699)
a reproduit sous GDB un crash de cache de requêtes nul, **avant
Vulkan GPU**. Le correctif est intégré aux deux `main`, mais pas
au binaire publié. Le lanceur refuse expressément cet artefact
obsolète avant tout téléchargement du binaire, import privé ou build
Docker. Les commandes ci-dessus ne deviennent exploitables qu'après
publication d'une **nouvelle** liaison Linux publique avec le vendor
corrigé ; le lancement nécessitera alors les variables
`R09_HOST_LINKED_RUN_ID` et `R09_HOST_LINKED_SHA256` vérifiées.
La compilation syntaxique GitHub ne suffit pas.
Aucune DLL NVIDIA et aucun poids ne doivent être transmis à CI.

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

## Diagnostic après SIGSEGV (139) sur Colima

Le GDB du 8 novembre 2026 a **localisé le premier crash** dans
`VideoCommon::QueryCacheBase<Vulkan::QueryCacheParams>::CounterClose`
avec un objet `this` nul (`rdi=0`). La pile mène de
`Vulkan::Scheduler::EndPendingOperations` à `Scheduler::Finish`, puis
`UploadImage` : le crash intervient pendant le téléversement de
l'image d'entrée, **avant toute opération DLSS-NR**.

Cause confirmée dans le code source : le scheduler autonome R09 n'installe
aucun `QueryCache` de rendu de jeux, alors que `EndPendingOperations`
déréférençait toujours ce pointeur. Le vendor a été corrigé sur
`main` (`0f47339c2190`) par un garde de présence du cache ; le
gitlink du moteur a été synchronisé (`5390307c8412`).
Le parcours normal avec `QueryCache` conserve exactement son appel de
fermeture de compteur. **Ce correctif source n'est pas encore qualifié
par la liaison et l'exécution d'un nouveau binaire Linux.**

Le binaire du workflow `42465459699` reste **défectueux et
incompatible avec la correction** ; ses succès de build et ses tests
d'arguments invalides ne prouvent pas la réussite de `UploadImage`.
Le lanceur Mac rejette désormais cet artefact AVANT l'import privé de
165 Mo. Pour l'utiliser après une nouvelle liaison autorisée,
renseigner explicitement les deux valeurs vérifiées
`R09_HOST_LINKED_RUN_ID` (workflow GitHub) et
`R09_HOST_LINKED_SHA256` (SHA-256 du binaire extrait).
Ne jamais substituer une ancienne version juste pour dépasser le garde.

Le journal GDB privé actuel constitue la preuve de la panne initiale.
Une nouvelle exécution authentique reste requise pour confirmer que ce
correctif permet la soumission Vulkan, puis vérifier chaque opération
et la sortie RGBA32F contre une référence indépendante.

Un outil privé réutilise le dossier et les binaires du précédent essai,
la capture RGBA8 déjà préparée, et compile uniquement une image Linux
de diagnostic avec GDB si elle n'est pas présente. Il ne retélécharge pas
d'artefact GitHub et ne reconstruit **pas Eden** :

```bash
cd /tmp/eden-encore-fix
git pull --ff-only origin main
DOCKER_CONTEXT=colima-r09 \
  bash tools/graphics/r09_debug_existing_mac.sh \
    "$HOME/.cache/eden-encore-r09-private/full-network-H9tHXJUY" \
    "$HOME/Downloads/nvngx_dlssnr.dll.zip"
```

La DLL est extraite de nouveau **localement** pour la seule analyse ; les
599 tenseurs sont revérifiés, puis GDB exécute le **même** hôte avec la
**même** capture. Le conteneur reçoit la capacité limitée
`SYS_PTRACE` requise pour déboguer son propre processus ; aucune
option `--privileged` ni désactivation globale de seccomp.

Le rapport `r09_gdb_backtrace.log` est créé dans l'ancien dossier
`full-network-H9tHXJUY`. Partager ce **journal de pile** seulement,
pas les fichiers `.dll`, `.nrmodel`, `.rgba8`, `.rgba32f` ni les
captures privées. Le script efface de nouveau le modèle/DLL temporaire
à la sortie. Si le crash est dû au moteur ou au pilote, la pile indiquera
le premier symbole fautif ; il faudra distinguer cette panne des
limitations QEMU/Lavapipe.

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

## Mise à jour du 8 novembre — exécution réelle sous Lavapipe

Le nouveau binaire Linux authentiquement lié a été produit par le run
[`42488585951`](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42488585951).
Le journal privé utilisateur `r09_full_network(3).log` montre maintenant
`R09_PRIVATE_ORIGINAL_599_SHA256_PASS`, l'ouverture de l'ICD Lavapipe,
puis `R09_AUTHENTIC_152_GRAPH_EXECUTION_ATTEMPT`. Cette étape franchit
le téléversement d'image qui provoquait auparavant le crash du scheduler.

**Premier refus effectivement observé :**
`R09_HOST_ORIGINAL_INIT_REJECTED phase=preblock_and_texture`. Le réseau
n'a pas été exécuté : « execution attempt » ne démontre aucun des 152
dispatchs, ni une image DLSS-NR authentique.

Le même journal affiche
`EDEN_VULKAN_MEMORY integrated=0 heaps=1 local=4100476928 initial_usage=552566784 device_access=3587917312 capacity=0`.
Le champ `capacity` est alimenté par une sonde de mémoire libre
**facultative** dans `vulkan_device.cpp`; zéro ne démontre donc **pas**
une allocation GPU impossible ou un manque de VRAM. La phase combinée
précédente pouvait masquer aussi bien un refus de buffer qu'un refus de
descripteur image ou un contrôle des poids appris.

Le vendor `8ef5009141386185ae84a9972e6947a33ecb0c94` et le gitlink
moteur `7ff299abd25291a8cb007e185935f785c00029ee` isolent désormais
les six allocations et les étapes texture, features, FSwIN, lift et pooling
dans `LastInitializePhaseName()`. Ces modifications ne modifient ni
l'ordre des commandes ni les poids et n'ont **pas encore** été confirmées
par une nouvelle exécution privée. Il faut une nouvelle liaison Linux
avec ce gitlink avant de réutiliser le kit Mac ; le binaire antérieur
reste incapable d'indiquer ces phases fines. Aucun nouveau build global
PS5 n'est requis pour ce diagnostic.
