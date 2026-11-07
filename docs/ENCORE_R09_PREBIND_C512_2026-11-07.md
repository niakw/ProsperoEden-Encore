# R09 — liaison C512 préparée avant enregistrement GPU

7 novembre 2026, uniquement les deux branches `main`.

Le raccord C512 entre la descente U-Net et le premier Split-Swin
est désormais **prévalidé avant toute commande** dans le scheduler.

- `PreparedLowRaster()` ne publie que l'identité et la capacité
  du tampon du downpath, sans prétendre que ses pixels existent.
- `NrRdna2UNetBottleneckLink::Bind()` compare cette identité
  préparée aux deux consommateurs Split-Swin et bottleneck, et
  valide les formes du graphe natif avant le dispatch.
- `Record()` exige ensuite `down.LowRaster()`, qui n'existe
  **qu'après** l'enregistrement réussi des quatre producteurs
  C32/C64/C128/C256. La liaison refuse tout appel prématuré.
- L'orchestrateur prévalide cette liaison avant d'enregistrer
  les shaders source, proxy et prébloc.
- Ces validations conservent les garde-fous de transaction,
  sans réutilisation d'objets partiellement soumis.

Le workflow R09 vérifie la syntaxe des propriétaires natifs,
et les tests du modèle de données restent distincts de l'exécution
réelle sur Vulkan. Ni P5 ni le build PS5 global ne sont déclenchés.
