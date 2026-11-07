# R09 — préparation transactionnelle des étages natifs avant dispatch

7 novembre 2026. Travaux uniquement sur `main`.

## Problème traité

Le premier ordonnanceur R09 enregistrait déjà les commandes du prébloc,
de la descente et du bottleneck avant de tenter l'allocation des poids et
des buffers de la remontée U-Net, puis avant de préparer le postbloc FP16.
Un modèle incomplet ou une allocation refusée pouvait laisser des
commandes GPU partielles dans le scheduler ; cet état ne doit jamais
être relancé silencieusement.

## Changement

- `NrRdna2PreblockRun::PreparedFullSkip` publie uniquement l'identité
  de stockage prévue pour le skip full-resolution, avant production de pixels.
- Le postbloc prépare sa projection FP16 complète **avant** tout Record GPU.
- Les quatre `NrRdna2UNetUpsampleLink` préparent leurs gains,
  descriptors et sorties grâce à `PreparedForUpsample` sur des skips
  déjà liés à leurs producteurs par `NrRdna2UNetDownSequence`.
- `ForUpsample` reste strictement réservé aux skips dont le producteur
  a été effectivement enregistré sur le même scheduler.
- Au moment de `UpSequence::Record`, les quatre dépendances doivent
  avoir été enregistrées : toute omission entraîne un refus avant les
  dispatches de la montée.
- Le tampon préparé C512 du bottleneck est comparé par identité et
  capacités à celui du `NrRdna2UNetBottleneckLink::Record`.

Tous ces éléments restent des opérations de **préparation et de
raccordement au même VkCommandBuffer** : pas de readback CPU, pas de
supposition qu'une tâche GPU terminée est égale à une tâche enregistrée,
pas de replay après enregistrement partiel.

## Qualification et frontière

La syntaxe C++ réelle de ces propriétaires est inscrite dans le
contrôle R09, et les tests hôte couvrent le modèle de poids reconstruit.

Ce n'est pas encore une preuve d'exécution GPU du graphe **entier**,
de rendu temporel, d'acquisition des couleurs du guest ou de présentation
PS5. La validation de la première image réelle, avec poids authentiques,
reste obligatoire avant de déclarer DLSS-NR disponible.
