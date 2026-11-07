# R09 — frontière prébloc natif (7 novembre 2026)

**Contrat de plan hôte, pas encore de shader prébloc appris ni d'image PS5.**

Les plans Original et Compact ont la même frontière : bloc 0
`CCTinlayoutFusedPreBlockSwin1H` à **1920×1080**, puis bloc 1
`CCTinlayoutFusedSwin1H` en `_inpview_fp8` à **960×540 C32**.
Le raster Vulkan de sortie est donc **540×960×32 octets**.
La frontière C32 est celle attendue par la descente U-Net, **pas**
le C32 pleine résolution du proxy actuel.

`CanNativePreblockBoundary` vérifie les deux lignes, l'ordre de dépendance,
les divisions spatiales, les canaux 3 → 32, les fenêtres de dispatch,
l'identité du skip C32 et les capacités (budget 256 Mio). Le test
utilise les plans natifs Original/Compact avec mutations négatives.

Ce verrouillage ne prouve pas les **16 caractéristiques exactes en entrée**,
ni les poids des opérations Swin fusionnées ou leur projection/apprentissage
spatial ; `input_channels=3` compte les canaux texture du plan, pas
un conteneur FP16 de seize canaux directement équivalent.
Le modèle source identifie `input_lift` FP16 [32,16], mais la chaîne
d'acquisition des guides/texture et la fusion Swin/downsample doivent
encore être portées, puis comparées sur GPU.

Le chemin RDNA2 complet reste désactivé tant que prébloc, gains
U-Net manquants, postbloc, compositing et présentation PS5 ne sont
pas qualifiés. Aucun build console lancé.

## Prébloc appris — exécution du corps, sans réduction encore

Le vendor fournit désormais `NrRdna2PreblockRun` : il lit les poids
d'un modèle NRMODEL1 local, projette les 16 caractéristiques FP16 en
C32 E4M3FN avec la matrice réellement apprise, exécute le vrai bloc
FSwin C32 du prébloc (fenêtres 8×8, GPU Vulkan) et exporte sa sortie
pleine résolution comme futur skip `block0`. Les trois buffers
GPU doivent être distincts, avec le même scheduler et un plan
Original/Compact strict. Aucune étape n'est enregistrée si
l'initialisation échoue.

Ce composant reçoit des **caractéristiques déjà préparées**, pas
directement une texture du jeu. Le pooling natif 2×2 sur **sortie
brute FP16**, nécessaire pour alimenter le premier niveau U-Net C32,
n'est pas implémenté. Le raster C32 E4M3FN exporté n'est pas un
substitut numériquement fidèle à cette sortie brute. Le raccord reste
donc volontairement séparé de la descente U-Net, sans raccourci
de quantification ni activation utilisateur.

Aucune optimisation de cadence ou build global PS5.
