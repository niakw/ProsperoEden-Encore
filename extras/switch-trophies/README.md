# Switch Trophies — isolated offline catalog prototype

This optional module is **not compiled into Eden Encore** and does not modify F01–F07. It is intended to become a separate repository/service after its API and licenses are reviewed.

It creates empty achievement catalogs for **all installed Switch title IDs supplied to it**, not imaginary achievements for Nintendo's full game catalog. Trophies stay manual until a title/version-specific, reliable game-event observer is implemented and tested.

## Minimal usage

Input `installed.json`:

```json
{"games":[{"title_id":"0100C49025D3E000","title":"Example game"}]}
```

Seed one empty catalog per game, preserving existing curated manifests:

```sh
python3 extras/switch-trophies/catalog.py seed installed.json ./my-trophies --locale fr-FR
python3 extras/switch-trophies/catalog.py validate ./my-trophies/0100C49025D3E000.json
python3 -m unittest discover -s extras/switch-trophies -p 'test_*.py'
```

A manual trophy record may be authored as:

```json
{
  "schema_version": 1,
  "title_id": "0100C49025D3E000",
  "game_name": "Example game",
  "locale": "fr-FR",
  "trophies": [
    {
      "id": "first-goal",
      "name": "First goal",
      "description": "Mark this achievement manually.",
      "unlock_source": "manual"
    }
  ]
}
```

Automatic progress is **not** implemented. `verified_game_event` entries require a validated provenance rule ID, but the importer still does not unlock anything. Earned state must be stored separately from definitions.

## Before connecting to Encore

Define a versioned API for catalog lookup, title IDs, save-state rollback/reconciliation, version-specific unlock rules, active-profile isolation, notification throttling, offline storage and safe reset. Do not infer a trophy from a picture, LLM-generated description, game title metadata or arbitrary RAM value. Keep output clearly labeled **unofficial** and separate from PlayStation trophies.

See [the upstream / feature audit](../../docs/FEATURE_FORK_AUDIT_2026-10-25.md).
