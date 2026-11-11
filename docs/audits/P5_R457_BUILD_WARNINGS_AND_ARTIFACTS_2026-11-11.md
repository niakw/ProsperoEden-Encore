# Eden Encore R457 — audit des artefacts et avertissements CI (11 novembre 2026)

## Périmètre et limites de preuve

- Code de référence : moteur `ec8b519182532d3864c5a67dd27aa41aa9d43ff3`, vendor épinglé `90c9c8a203a27181e23349a889a8f2a7d1cd9dd2`.
- [Run R457 récupéré #42942150990](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42942150990) : SUCCESS (13/13 étapes du job) ; restauration de cache, liaison, signature/staging, deux ZIP, SHA-256 et upload.
- Archives inspectées **localement**, par ouverture ZIP et contrôle CRC des membres, SHA-256 et comparaison byte-for-byte des fichiers communs : bundle Actions (6 entrées), ZIP complet (258), FTP ZIP (78), artifact FTP brut (185). Absence de corruption, doublons et chemin ZIP dangereux sur les deux ZIP de distribution.
- Empreintes du `dist/SHA256SUMS` vérifiées : complet `3b39c603fb97e558e5fe815fb0f77def475ab874adaf43ae9b8bdae488f3df3a`, FTP minimal `7b87abb567247cf06cdfc7adc7cd498e7826367d1a5548b8d000a3a19e63f474`.
- Le ZIP FTP est intentionnellement réduit : `tools/ci/make-dist.py` exclut les notices légales et les compagnons `.txt` (FTP ASCII auto), mais conserve 31 catalogues `.po`. Le bundle complet conserve tout. Ce **n'est pas** un manque de langues dans le ZIP FTP.
- **Limite :** ceci n'est ni une installation réelle sur console, ni une vérification des FPS, de l'audio, de l'image NS1/NS2 ou de la concordance avec un dump PS5 exécuté.

## Anomalies de packaging réellement observées

| Priorité | Diagnostic | Run / effet | Correction préparée |
| --- | --- | --- | --- |
| P0 | `crash-provenance.json` référence `link.map` (54 464 368 octets), mais l'artefact de symboles ne l'embarque pas | #42942150990 : bundle incomplet pour analyse avancée des crashs | Copier `build/headless-native/link.map` sous `build/symbols/link.map` et comparer taille et SHA-256 au reçu, bloquer si écart |
| P1 | Fond quotidien optionnel : `fetch_daily_switch.py` exige `magick` ImageMagick 7, alors que l'Ubuntu runner expose `convert` et `identify` ImageMagick 6 | #42942150990 : repli sur le fond Encore | Choisir correctement les commandes 6/7, conserver limites mémoire et dimensions, vérification hôte sans réseau |
| P2 | `iCCP` : profil ICC RGB incorrect sur un PNG gris `switch-rear-footer.png` | #42942150990 : warning ImageMagick, conversion poursuivie | **Corrigé sur cette branche** par suppression du seul chunk ancillaire `iCCP` (276 octets), IDAT inchangé ; contrôle PNG standard-library ajouté, sans masquer stderr |
| Réglé en CI | ZIP de distribution inexistant / mauvais nom puis `SHA256SUMS` vérifié depuis mauvais répertoire | #42938625487, #42941245433 rouges | Correctifs déjà présents dans R457 : fichier attendu contrôlé et `(cd dist && sha256sum --check --strict SHA256SUMS)` |

## Inventaire exhaustif des douze tentatives natives lourdes de P5

Tous les 12 runs ci-dessous ont été contrôlés par leurs jobs GitHub Actions, leur étape en échec et leur inventaire d'artefacts (**0/12 artefact téléchargeable**). Leurs logs de job ont été relus et catégorisés ; les messages répétitifs de même origine ont été regroupés.

| Tentative | Run | Blocage observé dans les logs |
| --- | --- | --- |
| 1 | [#42846319389](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42846319389) | Deux assertions de preflight devenues obsolètes : JIT et catalogue Nlib |
| 2 | [#42848349739](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42848349739) | Assertions JIT/Nlib non réalignées entièrement |
| 3 | [#42850915181](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42850915181) | Erreurs CMake `add_subdirectory` en phase différée et owner de l'arbitre d'adresses |
| 4 | [#42856587272](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42856587272) | `check-ci-cache.py` testait un intitulé d'étape qui n'existait plus |
| 5 | [#42858138767](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42858138767) | CMake ne retrouvait plus l'owner A32 CPU6/G11 correctement sélectionné |
| 6 | [#42865547895](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42865547895) | C++ : noms `EncoreOverrides` non qualifiés, `AppUpdateInfo.package_name` non initialisé, variable inutilisée |
| 7 | [#42873646669](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42873646669) | Assertion de performance JIT sur une option CMake abandonnée |
| 8 | [#42876772744](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42876772744) | `check-native-gpu-thread.py` rejetait le nouveau worker GPU maintenu |
| 9 | [#42880572712](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42880572712) | Ninja : `fsr31_temporal_upscaler.h` déclaré deux fois comme output |
| 10 | [#42887138500](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42887138500) | C++ réel : `forced_color_resolve` manquant et `SCOPE_EXIT` non déclaré |
| 11 | [#42911552038](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42911552038) | `libwebp` SSE2 interdit + owner du diagnostic frame Vulkan |
| 12 | [#42924336057](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42924336057) | Échec LLD au lien sur symboles Vulkan et atomiques shader (après 1 398 étapes Ninja) |

**Runs de récupération (pas de compilation globale)** : #42936540352 et #42937511728 n'ont produit aucun artefact ; [#42938625487](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42938625487) a fourni un FTP brut mais échoué pendant l'assemblage des ZIP ; [#42941245433](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42941245433) a fourni un FTP brut mais échoué au contrôle SHA depuis un répertoire incorrect ; **[#42942150990](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42942150990) a fourni les deux artefacts FTP et bundle, CI SUCCESS**. Le [run #42934160729](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42934160729) a qualifié le relink cache, mais ne fournissait pas de paquet.

### P2 — SDL ALSA : cause et correction isolée

Le journal R457 rapporte `Unable to find the alsa development library` lors du configure SDL3, alors que le CMake Encore désactive explicitement la source `sink/sdl3_sink`, retire `SDL3::SDL3` de l'audio et utilise l'interface native PS5. La branche PR #47 demande donc `SDL_ALSA=OFF` **uniquement sous `PS5_NATIVE`**, avant la configuration des dépendances. Ce choix de backend n'affecte pas les builds hôtes et évite de sonder la machine Linux pour un périphérique audio inexistant sur PS5. Contrôle de propriétaire hôte ajouté ; le prochain configure natif devra confirmer la disparition effective du warning.

## Journaux natifs lourds et warnings — triage par propriétaire

- [Run #42911552038](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42911552038) (11e tentative environ) : compilation native effective, échec `libwebp` avec `SSE2 register return with SSE2 disabled` sur `sharpyuv_gamma.c`, autres TUs WebP et `graphics.cpp`. Défaut bloquant historique ; le run R457 a depuis produit un paquet, sans prouver à lui seul qu'une nouvelle compilation complète aurait réussi avec le même graphe.
- [Run #42924336057](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42924336057) (12e tentative) : les 1 398 étapes avant lien avaient progressé, échec de l'édition de liens sur fonctions Vulkan et émetteurs atomiques du shader (`vkCmdDispatch`, `vkCmdBindDescriptorSets`, `EmitStorageAtomicCompareExchange32`, etc.). Les reconstructions ciblées et le relink de #42942150990 ont résolu l'échec de lien **pour le binaire candidat**.
- **Mesa/NIR/RADV (bibliothèques de préparation tierces)** : très nombreux `-Wunused-but-set-variable` à partir de `nir.h`, `radv_shader.c`, `radv_postprocess_nir_standalone.c`, `psbc_compile.c`. Ce sont des warnings récurrents de la même famille, pas autant de régressions indépendantes. Ne pas modifier les snapshots externes ni retirer globalement les avertissements.
- **Mesa SPIR-V (priorité haute à qualifier)** : `-Wreturn-type` sur plusieurs `spirv_to_nir.c`, `vtn_alu.c`, `vtn_variables.c`, `vtn_structured_cfg.c` ; `-Wmaybe-uninitialized` (ex. `vtn_subgroup.c`, `vtn_variables.c`). Examiner macros abort/unreachable, versions de compilateur et préconditions avant de décider si vrai problème de flot ou faux positif.
- **Vendor NS2 Ampere (priorité haute à qualifier)** : conversions signées/non signées et pertes de précision dans `frontend/ampere/lower_to_maxwell.h`, `capture.cpp` et `probe.cpp`. Réserver un audit de domaines des valeurs sur une branche vendor isolée ; des casts pour faire disparaître les warnings peuvent introduire des régressions shader NS1/NS2.
- **CMake/paquets tiers** : Opus `Could not get package version` (source épinglée `a3f0ec02b3`, correctif de provenance préparé sur cette PR, configure natif encore à confirmer) ; SDL3 `Unable to find the alsa development library` (sonde ALSA hôte). Qualifier le mode de compilation et les fonctionnalités effectivement activées avant de modifier la configuration. Absence d'ALSA sur un hôte de build PS5 n'est pas automatiquement un défaut audio PS5.
- **UI/i18n** : avertissements de dépassement de libellés en plusieurs langues et glyphes non vérifiés pour certaines polices. Ne pas raccourcir massivement les traductions sans vérifier le sens et les composants UI réels.

### P1 — PSBC SPIR-V : vraie cause des diagnostics de flot

La commande GCC du run natif #42942150990 utilise `-DHAVE_FUNC_ATTRIBUTE_PACKED=1`, mais **pas** `-DHAVE_FUNC_ATTRIBUTE_NORETURN=1`. Or `src/util/macros.h` de la dépendance PSBC ne définit `NORETURN` que lorsque ce macro est présent. `src/compiler/spirv/vtn_private.h` déclare `NORETURN void _vtn_fail(...)` et l'implémentation appelle `vtn_longjmp(...)`. L'attribut perdu explique directement des diagnostics `-Wreturn-type`, et peut expliquer certains `-Wmaybe-uninitialized`, lorsque le compilateur croit qu'un chemin `vtn_fail()` revient.

**Correction isolée :** ajouter le macro supporté par GCC/Clang temporairement dans les configurations PSBC hôte et PS5 pendant `build-opengl-sdk.sh`, avec sauvegarde/restauration byte-for-byte des fichiers sources épinglés. Le test hôte reproduit sous `-Werror=return-type` un avertissement sans attribut et vérifie sa disparition avec attribut. Aucun fichier Mesa original ne reste modifié et aucune option `-Wno-...` n'est ajoutée. La suppression effective de l'ensemble des warnings doit être confirmée lors de la prochaine construction de dépendances volontaire.

## Complément de qualification du 11 novembre — CI et versions

### Propriété des sauvegardes OpenGL/PSBC

- `eeb75f3b` déplace le `trap cleanup EXIT` avant toute modification du cross-file PS5 ; les sauvegardes des deux fichiers PSBC utilisent le PID Bash `$`.
- Le test hôte `tools/check-psbc-noreturn-host.py` exécute désormais **la véritable fonction de nettoyage extraite du script**, contre des fichiers temporaires, en simulant un échec précoce et un échec après les modifications PSBC. Il vérifie les quatre restaurations et la disparition de tous les backups et du répertoire de staging.
- [Fast gate #42989520055](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42989520055) : **SUCCESS** au commit `6cdf2278`. Cela ne constitue pas une construction complète de Mesa/PSBC ni un test physique.

### Opus : identité vérifiable sans retoucher la source

Le snapshot Opus réellement utilisé est `vendor/sources/eden-cpm/opus/a3f0ec02b3`, équivalent au commit upstream `a3f0ec02b34281c38aefdaf4bbbd5787ad641d62`. La comparaison GitHub entre la release upstream signée `v1.6.1` (`22244de5a79bd1d6d623c32e72bf1954b56235be`) et le commit épinglé montre **six commits d'avance et zéro de retard**. Le format de provenance `1.6.1-6-ga3f0ec02b342` est donc un identifiant de *snapshot de développement*, non une revendication que ses octets correspondent exactement à la release `1.6.1`.

`OpusPackageVersion.cmake` attend un dépôt Git ou un fichier `package_version`, absents du snapshot vendorisé ; il revient autrement sur `PROJECT_VERSION=0`. Le `PACKAGE_VERSION` produit par la configuration peut aussi se retrouver dans `opus_get_version_string()` (dans `celt/celt.c`) : c'est donc une **erreur de version exposée au diagnostic**, sans preuve de défaut d'encodage/décodage.

La branche PR #47 renseigne désormais `OPUS_PACKAGE_VERSION` par une variable CMake **non mise en cache et active uniquement sous `PS5_NATIVE` et si le chemin du snapshot épinglé existe**, via `headless/inject.cmake`. Elle ne change aucun octet du vendor ou de la bibliothèque. Le garde `tools/check-opus-version-host.py` valide le format, la portée PS5 et l'extraction de `PROJECT_VERSION=1.6.1` par CMake. [Fast gate #42990670701](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42990670701) : **SUCCESS** sur `96050597`. La disparition effective du warning dans le **véritable configure Opus PS5** n'est pas encore mesurée.

### Traductions : 31 catalogues, 125 avertissements

Le journal natif [#42924336057](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42924336057), relu par catalogue, indique **31 langues/catalogues**, **0 erreur bloquante** et **125 avertissements** agrégés. Les plus nombreux : `el-GR` 16, `pl-PL` 14, `it-IT` 13, `de-DE` 12 et `pt-BR` 10.

`tools/launcher/strings.py` émet un avertissement de longueur lorsque `len(traduction) > max(1.7 × len(source), len(source) + 12)` ; il s'agit d'un *indicateur heuristique*, pas de la preuve d'un dépassement visuel mesuré sur console. Le script n'affiche que les douze premiers détails par catalogue : ne pas confondre le nombre de lignes détaillées avec le total agrégé.

Sept locales ont des caractères des polices système PS5 **non vérifiés** faute de ressources de police lors du contrôle : `ar`, `el-GR`, `th-TH`, `ja-JP`, `ko-KR`, `zh-Hans`, `zh-Hant`. La somme des compteurs *par langue* représente 2 261 caractères à qualifier, sans prétendre qu'il s'agit de glyphes uniques. Ne jamais inventer les traductions ni les raccourcir en bloc pour faire baisser un indicateur : contrôler les écrans concernés et la couverture des polices avant correction.

### Mesa NIR : un warning d'impression séparé

Le `-Wformat-truncation` de `src/compiler/nir/nir_print.c:877` correspond à `snprintf(buf, 4, "%u", location)`, appelé avec un tableau `char buf[4]`. Un entier de plus de trois chiffres peut être **tronqué dans l'affichage de diagnostic**, sans débordement mémoire grâce à `snprintf`. Les trois snapshots Mesa examinés contiennent la même forme. L'agrandissement cohérent du buffer et de la taille d'écriture pourrait être proposé à leur propriétaire ; **aucun patch Mesa tiers supplémentaire n'est intégré** pour ce warning.

### Frontière NS2

Le journal [#42924336057](https://github.com/niakw/ProsperoEden-Encore/actions/runs/42924336057) comporte **35 coordonnées source Ampere distinctes** dans `capture.cpp` (15), `lower_to_maxwell.h` (18), `probe.cpp` (1) et `program_capture.h` (1), dont 11 réductions 64→32 bits dans `capture.cpp`. Elles relèvent d'une étude de domaines et de gardes sur branche de recherche NS2, sans casts silencieux, merge vendor ni modification sur `main`.

## Règles de clôture

1. **Pas de nouveau build PS5 lourd** pour nettoyer des logs. Corriger par propriétaire, utiliser source-preflight et témoins hôtes, puis seulement un nouveau build explicitement approuvé.
2. Garder `main` et `vendor` inchangés tant que le correctif de packaging et les tests ciblés ne sont pas validés sur branche.
3. **Aucune release publiée** ; le brouillon R2 reste séparé et sans assets.
4. Actualiser ce rapport et les preuves après exécution des CI de branche ; ne pas écrire « tous warnings réglés » avant validation.
