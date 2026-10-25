#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Contract tests for the isolated, optional offline Switch trophy catalog."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from catalog import seed_games, title_id, validate_manifest


class CatalogTests(unittest.TestCase):
    def test_title_id_and_no_path_escape(self):
        self.assertEqual(title_id("0100c49025d3e000"), "0100C49025D3E000")
        for bad in ("../../passwd", "abc", "0100C49025D3E00Z", None):
            with self.assertRaises(ValueError):
                title_id(bad)

    def test_seed_preserves_curation_and_never_unlocks(self):
        with tempfile.TemporaryDirectory() as root:
            here = Path(root)
            installed = here / "installed.json"
            installed.write_text(json.dumps({"games": [
                {"title_id": "0100C49025D3E000", "title": "Example"},
                {"title_id": "01007EF00011E000", "title": "Another"},
            ]}))
            output = here / "trophies"
            self.assertEqual(seed_games(installed, output, "fr-FR"), (2, 0))
            data = json.loads((output / "0100C49025D3E000.json").read_text())
            self.assertEqual(data["trophies"], [])
            data["trophies"] = [{"id": "sample", "name": "Manual goal",
                                "description": "Manually checked",
                                "unlock_source": "manual"}]
            (output / "0100C49025D3E000.json").write_text(json.dumps(data))
            self.assertEqual(seed_games(installed, output, "fr-FR"), (0, 2))
            self.assertEqual(len(json.loads((output / "0100C49025D3E000.json").read_text())
                                 ["trophies"]), 1)

    def test_rejects_unverified_automated_unlock_and_duplicate_ids(self):
        base = {"schema_version": 1, "title_id": "0100C49025D3E000",
                "game_name": "Example", "locale": "fr-FR", "trophies": []}
        for obj in (
            {"id": "dup", "name": "A", "description": "Test", "unlock_source": "manual",
             "earned": True},
            {"id": "auto", "name": "A", "description": "Test",
             "unlock_source": "verified_game_event"},
        ):
            with self.assertRaises(ValueError):
                validate_manifest({**base, "trophies": [obj]})
        item = {"id": "same", "name": "A", "description": "Test",
                "unlock_source": "manual"}
        with self.assertRaises(ValueError):
            validate_manifest({**base, "trophies": [item, item]})

    def test_bad_duplicate_installed_titles(self):
        with tempfile.TemporaryDirectory() as root:
            here = Path(root)
            installed = here / "installed.json"
            installed.write_text(json.dumps({"games": [
                {"title_id": "0100C49025D3E000", "title": "A"},
                {"title_id": "0100c49025d3e000", "title": "B"},
            ]}))
            with self.assertRaises(ValueError):
                seed_games(installed, here / "out", "fr-FR")


if __name__ == "__main__":
    unittest.main()
