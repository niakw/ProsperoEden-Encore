# R09 — learned temporal head and honest first-frame fallback

Date : 7 novembre 2026. Intégration sur les deux `main`.

`NrRdna2TemporalCompose` effectue le compositing du **quatrième canal
FP16 appris** (logit de conservation de l'historique) avec la sortie
RGB résiduelle (canaux 0–2), un véritable champ de mouvement courant
→ précédent et un historique neuronal d'une frame antérieure.

La reconstruction de l'historique utilise cinq taps Catmull–Rom,
la vérification par pixel du drapeau de validité et une troncature
FP16 avant réinjection. L'image courante et l'historique suivant
restent des VkBuffers RGBA32F distincts avec ownership/fences
gérés par le renderer appelant.

La composition temporelle est alternative à
`NrRdna2NoHistoryCompose`. `NrRdna2CoreFeatureSequence` interdit
les deux à la fois et peut publier l'image résultante vers un
`VkImageView`. Le chargement exige le vrai coefficient
`unpacked-postblock/blockN.layer0.layer.blend_scale.bin`
du pack `NRMODEL1` : exactement 2 octets FP16, fini, dans [0,1].
Aucun coefficient inventé ou historique présumé valide n'est accepté.

**Frontière maintenue :** l'extracteur MIT historique n'inclut
pas toujours cette entrée. Le test hôte fabrique un mini-modèle
pour vérifier le format et les refus, non pour prétendre disposer
du coefficient original. Le chemin entier Original/Compact et
l'intégration au renderer `Layer::ConfigureDraw` restent à
assembler/valider, tout comme la provenance du mouvement réel,
la parité GPU du réseau et la gestion des deux historiques.

Pas de PS5 global build, pas de branche ni PR.
