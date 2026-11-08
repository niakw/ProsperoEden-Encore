# Neural Rendering locale update — 8 November 2026

The 29 maintained locale catalogs now include the 41 latest Neural Rendering, A4K, DLSS-NR and Frame Generation user-facing strings. Four priority FR/ES locales already had these strings. German, Italian and Portuguese (BR/PT) were completed in commit b243ea3; this commit completes the 21 remaining catalogs.

The translations are machine-assisted and require fluent human review; complete key coverage and placeholder checks are not linguistic acceptance or a proof that the PS5 system fonts render every character. Specifically review Arabic RTL presentation, CJK glyph fallback, Polish/Czech/Hungarian diacritics, Greek, Thai, and the differences between regional Portuguese variants. Do not replace non-English text with English solely to pass an audit.

The original AMD FSR 1 filter, RCAS sharpness and EASU help remain independent of Neural Rendering. Historic FSR msgids stay archived as inactive gettext entries in the affected French and Spanish catalogs. No renderer or game logic was modified for this catalog-only update.

Host verification: tools/launcher/strings.py check; tools/check-launcher-translation-coverage.py; tools/check-switch-theme-layout.py; launcher production-preview workflow. P0–P4 final qualification requires green checks on one engine/vendor SHA. P5 console verification remains separate.
