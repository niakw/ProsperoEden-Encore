# R09 — Neural Rendering : réglages directs

## Choix affichés (dans le même sélecteur)
1. Désactivé — `off`
2. A4K — Détails améliorés — `a4k_detail`
3. A4K — Image adoucie — `a4k_soft`
4. A4K — Image nettoyée — `a4k_denoise`
5. DLSS-NR — Original — `dlss_nr_original`
6. DLSS-NR — Compact — `dlss_nr_compact`

Pas de sous-menu « moteur » suivi d'un second sélecteur « modèle ».
`video.neural_strength` reste une valeur de 0 à 100 %, qui
n'a d'effet que pour les deux modes DLSS-NR. Un changement de mode
ne détruit pas le réglage utilisateur ou par jeu existant.

NR et Frame Generation sont `off` par défaut. Les combinaisons
NR + générateur d'images, NR + suréchantillonneur concurrent,
NR + MSAA forcé sont provisoirement refusées, faute de preuve
de leur composition sur le renderer PS5. OpenGL est exclu.

Les trois A4K sont de véritables options de Neural Rendering dans
l'UI. Leurs pipelines de présentation Vulkan historiques
restent désignés en interne par les indices 7 à 9, mais les
options ne figurent plus dans le choix d'Upscaling spatial.

**Portée :** l'interface et la persistance autorisent la sélection
de DLSS-NR Original/Compact comme demandé, même si le port
ne dispose pas encore d'un graphe neuronal complet produisant
une frame sur GPU PS5. Ne pas confondre cela avec une validation
fonctionnelle. Les optimisations sont encore reportées.

Voir `ENCORE_R09_NEURAL_RENDERING_UI_OVERRIDES.md` pour le schéma.
