# GitHub Actions — migration du checkout Node.js 20 vers Node.js 24 (11 novembre 2026)

Périmètre : **quatre workflows encore épinglés à `actions/checkout` v4** sur le `main` `ec8b519182532d3864c5a67dd27aa41aa9d43ff3`, identifiés par recherche dans les 43 workflows. Migration vers `actions/checkout` **v7.0.1**, SHA complet `3d3c42e5aac5ba805825da76410c181273ba90b1`, déjà testé dans le fast gate P5 de [PR #47](https://github.com/niakw/ProsperoEden-Encore/pull/47).

- `prepare-encore-r2-draft.yml` : deux checkouts, conserve ses gardes `draft=true`, `prerelease=true` et `assets=0`. **Aucune publication de release** et aucun changement de source/candidat inclus dans cette PR.
- `encore-overrides-source-integrity.yml` : un checkout, `submodules: recursive` conservé. Un contrôle ciblé PR doit vérifier l'exécution.
- `r09-host-link.yml` : un checkout, reste un workflow de link host sur déclenchement manuel ou marqueur explicitement autorisé sur `main`. Aucune compilation R09 lancée par cette migration sur sa branche.
- `r09-vit-boundary-qualification.yml` : trois checkouts sur jobs isolés, les règles `push: main` et `workflow_dispatch` sont conservées.

Le passage à v7 n'est **pas** un changement de logique métier, de dépendance de l'émulateur ou de `vendor`. Il adopte Node.js 24 et corrige l'alerte de dépréciation Node.js 20 du runner. Les exigences de sécurité propres à v7 et le comportement sur les workflows réels doivent être vérifiés en CI avant toute fusion. Le fast gate P5 spécifique est déjà traité sur la PR #47 ; il ne fait pas partie de ces quatre fichiers.

**État : PR en brouillon, sans merge, release et artefact natif.**
