#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Offline-only Switch achievements catalogue v1; no emulator hooks.

Seed empty, human-authored manifests for installed title IDs. This does not
derive achievements or unlocks from gameplay, third-party catalogs or AI.
Designed to live in a separate repository and remain optional in Encore.
"""
import argparse
import json
import os
import re
from pathlib import Path

TITLE_ID = re.compile(r"[0-9A-Fa-f]{16}\Z")
TROPHY_ID = re.compile(r"[a-z0-9][a-z0-9_.-]{0,63}\Z")


def title_id(value: str) -> str:
    if not isinstance(value, str) or not TITLE_ID.fullmatch(value):
        raise ValueError("invalid 16-character hexadecimal Switch title ID")
    return value.upper()


def validate_manifest(data: dict) -> dict:
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise ValueError("expected schema_version=1")
    ident = title_id(data.get("title_id"))
    name = data.get("game_name")
    locale = data.get("locale")
    if not isinstance(name, str) or not 1 <= len(name.strip()) <= 240:
        raise ValueError("game_name required (1-240 characters)")
    if not isinstance(locale, str) or not re.fullmatch(r"[a-z]{2}-[A-Z]{2}", locale):
        raise ValueError("locale must be a language-country tag, e.g. fr-FR")
    achievements = data.get("trophies")
    if not isinstance(achievements, list) or len(achievements) > 256:
        raise ValueError("trophies must be a list of at most 256 entries")
    seen = set()
    for item in achievements:
        if not isinstance(item, dict):
            raise ValueError("each trophy must be an object")
        trophy_id = item.get("id")
        if not isinstance(trophy_id, str) or not TROPHY_ID.fullmatch(trophy_id):
            raise ValueError("invalid trophy id")
        if trophy_id in seen:
            raise ValueError("duplicate trophy id")
        seen.add(trophy_id)
        for field in ("name", "description"):
            value = item.get(field)
            if not isinstance(value, str) or not 1 <= len(value.strip()) <= 512:
                raise ValueError("each trophy needs a non-empty " + field)
        if item.get("unlock_source") not in ("manual", "verified_game_event"):
            raise ValueError("unlock_source must be manual or verified_game_event")
        if item.get("unlock_source") == "verified_game_event":
            if not isinstance(item.get("verified_rule_id"), str) or not item["verified_rule_id"]:
                raise ValueError("verified events require a provenance rule ID")
        if "earned" in item or "unlocked" in item:
            raise ValueError("catalog entries must not store earned/unlocked state")
    return {**data, "title_id": ident}


def seed_games(infile: Path, outdir: Path, locale: str) -> tuple[int, int]:
    data = json.loads(infile.read_text(encoding="utf-8"))
    games = data.get("games") if isinstance(data, dict) else None
    if not isinstance(games, list):
        raise ValueError('input must contain {"games":[{"title_id":"...","title":"..."}]}')
    if not re.fullmatch(r"[a-z]{2}-[A-Z]{2}", locale):
        raise ValueError("invalid locale")
    outdir.mkdir(parents=True, exist_ok=True)
    created, unchanged, seen = 0, 0, set()
    for game in games:
        if not isinstance(game, dict):
            raise ValueError("game entry must be an object")
        ident = title_id(game.get("title_id"))
        if ident in seen:
            raise ValueError("duplicate installed game title ID")
        seen.add(ident)
        name = game.get("title") or ident
        manifest = validate_manifest({
            "schema_version": 1, "title_id": ident,
            "game_name": name, "locale": locale,
            "catalog_kind": "local_optional_unofficial",
            "trophies": [],
        })
        target = outdir / (ident + ".json")
        if target.exists():
            validate_manifest(json.loads(target.read_text(encoding="utf-8")))
            unchanged += 1
            continue
        # Exclusive creation preserves any curated existing definitions.
        with target.open("x", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)
            f.write("\n")
        created += 1
    return created, unchanged


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    seed = sub.add_parser("seed", help="create empty manifests for installed Switch games")
    seed.add_argument("installed_titles", type=Path)
    seed.add_argument("out_dir", type=Path)
    seed.add_argument("--locale", default="fr-FR")
    check = sub.add_parser("validate", help="validate an optional manual trophy catalog")
    check.add_argument("manifest", type=Path)
    args = parser.parse_args()
    if args.action == "seed":
        created, unchanged = seed_games(args.installed_titles, args.out_dir, args.locale)
        print(f"TROPHY_CATALOG_SEEDED created={created} preserved={unchanged} "
              "unlock_source=none")
    else:
        checked = validate_manifest(json.loads(args.manifest.read_text(encoding="utf-8")))
        print("TROPHY_CATALOG_VALID title_id=" + checked["title_id"] +
              " count=" + str(len(checked["trophies"])))


if __name__ == "__main__":
    main()
