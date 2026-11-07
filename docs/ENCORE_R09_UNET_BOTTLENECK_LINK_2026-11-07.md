# R09 — pont U-Net descente → bottleneck natif (7 novembre 2026)

**Statut : source intégrée sur `main`, qualification CI à établir. Aucune image PS5 validée.**

Le propriétaire `NrRdna2UNetBottleneckLink` reçoit la sortie C512 d'une
`NrRdna2UNetDownSequence` dont le `Record()` a déjà réussi, puis
raccorde ce même `VkBuffer` à l'input-view du premier Split-Swin
et à `NrRdna2NeuralBottleneck` sur le même scheduler Vulkan.

Le contrat extrait les vrais blocs des plans Original et Compact :
- Original : dernier DS 22 → premier Split 23 → dernier Split 47 → up 48.
- Compact : dernier DS 8 → premier Split 9 → dernier Split 21 → up 22.

Pour ces deux modèles, la géométrie C512 est **33×60 en raster Vulkan**
(soit le plan natif 60×33). Les trois capacités, les identités de buffers,
l'ordre des blocs, les dimensions et les propriétaires scheduler sont
vérifiés. Le bottleneck est enregistré **une seule fois**. La sortie ne
devient accessible pour `NrRdna2UNetUpSequence::Prepare()` qu'après
réussite de `Record()` ; ce dernier reçoit alors les skips précédemment
enregistrés sur le même scheduler.

Les deux propriétaires `NrRdna2SplitSwinRun` et
`NrRdna2NeuralBottleneck` refusent désormais de rejouer une tentative
d'enregistrement partiellement échouée ; `Result()` ne signale plus
une réussite si la séquence interne a échoué.

**Non résolu :** prébloc appris de pleine vers demi-résolution,
poids/gains C64–C256 incomplets, postbloc, HDR/compositing, acquisition
des guides du renderer, intégration effective de l'ordonnanceur
par frame et vérification console P5. Cette CI valide des contrats
et une syntaxe hôte, pas une inférence ni des FPS.
