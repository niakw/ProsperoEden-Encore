#!/usr/bin/env python3
"""Hermetic R25 daily-art tests: no network, console or proprietary game data."""
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, main
from unittest.mock import patch
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fetch_daily_switch as daily


class DailyWallpaperTests(TestCase):
    def setUp(self):
        self.today = date(2026, 11, 5)

    def test_release_dates_are_bounded(self):
        self.assertEqual(daily.valid_day("Nov 3, 2026", self.today, "%b %d, %Y"),
                         date(2026, 11, 3))
        self.assertIsNone(daily.valid_day("Nov 6, 2026", self.today, "%b %d, %Y"))
        self.assertIsNone(daily.valid_day("Nov 3, 2020", self.today, "%b %d, %Y"))
        self.assertIsNone(daily.valid_day("not a date", self.today, "%b %d, %Y"))

    def test_recent_ns2_filters_preorders_duplicates_and_hosts(self):
        feed = {"games": [
            {"title": "Latest", "status": "r", "date": "Nov 3, 2026",
             "art": "https://www.nintendo.com/eu/latest.jpg"},
            {"title": "Latest", "status": "r", "date": "Nov 3, 2026",
             "art": "https://www.nintendo.com/eu/other.jpg"},
            {"title": "Future", "status": "r", "date": "Nov 7, 2026",
             "art": "https://www.nintendo.com/eu/future.jpg"},
            {"title": "Preview", "status": "u", "date": "Nov 3, 2026",
             "art": "https://www.nintendo.com/eu/preview.jpg"},
            {"title": "Untrusted", "status": "r", "date": "Nov 3, 2026",
             "art": "https://attacker.example/a.jpg"},
            {"title": "Older", "status": "r", "date": "Oct 30, 2026",
             "art": "https://assets.nintendo.eu/foo"},
        ]}
        candidates = daily.ns2_candidates(feed, self.today)
        self.assertEqual([x["title"] for x in candidates], ["Latest", "Older"])

    def test_ns1_is_cross_checked_against_verified_metadata(self):
        def fake_fetch(url, *_args, **_kwargs):
            self.assertEqual(url.split("/nx/")[1][:16], "0100C49025D3E000")
            return json.dumps({"id": "0100C49025D3E000", "name": "Test Game",
                               "releaseDate": "2026-10-30", "type": "base",
                               "console": "nx", "isDemo": False,
                               "banner": "http://api.nlib.cc/a"}).encode()
        with patch.object(daily, "fetch", side_effect=fake_fetch):
            game = daily.verified_ns1({"title_id": "0100C49025D3E000"}, self.today)
            self.assertIsNotNone(game)
            self.assertEqual(game["platform"], "ns1")
            self.assertEqual(game["day"], date(2026, 10, 30))
            self.assertTrue(game["art"].startswith("https://api.nlib.cc/"))
            self.assertIsNone(daily.verified_ns1({"title_id": "../../bad"}, self.today))

    def test_manifest_is_atomic_and_keeps_valid_snapshot_on_failure(self):
        candidates = [
            {"title": "Switch 1", "day": date(2026, 10, 30), "platform": "ns1",
             "art": "https://api.nlib.cc/nx/0100C49025D3E000/banner/720p"},
            {"title": "Switch 2", "day": date(2026, 11, 3), "platform": "ns2",
             "art": "https://www.nintendo.com/eu/game.jpg"},
        ]
        with TemporaryDirectory() as temp:
            folder = Path(temp)
            def fake_convert(_source, target):
                payload = b"VP8 " + b"X"*4100
                target.write_bytes(b"RIFF" + (len(payload) + 4).to_bytes(4, "little") + b"WEBP" + payload)
            with patch.object(daily, "fetch", return_value=b"\xff\xd8" + b"J"*100), \
                 patch.object(daily, "convert_art", side_effect=fake_convert):
                self.assertEqual(daily.build(folder, self.today, candidates), 2)
            manifest = json.loads((folder/"index.json").read_text())
            self.assertEqual([x["platform"] for x in manifest["entries"]], ["ns1","ns2"])
            self.assertEqual([x["release_date"] for x in manifest["entries"]],
                             ["2026-10-30","2026-11-03"])
            self.assertTrue(all(x["approved"] is True for x in manifest["entries"]))
            self.assertEqual([x["filename"] for x in manifest["entries"]],
                             ["wall-00.webp", "wall-01.webp"])
            self.assertFalse(list(folder.glob("wall-*.jpg")))
            self.assertFalse((folder/"index.json.tmp").exists())
            before = (folder/"index.json").read_bytes()
            with patch.object(daily, "fetch", side_effect=TimeoutError()):
                self.assertEqual(daily.build(folder, self.today, candidates), 0)
            self.assertEqual((folder/"index.json").read_bytes(), before)

    def test_rejects_unapproved_hosts(self):
        for url in ("http://api.nlib.cc/x", "https://attacker.example/x",
                    "https://api.nlib.cc.attacker.example/x"):
            with self.assertRaises(ValueError):
                daily.fetch(url, daily.ART_HOSTS, 1000)


if __name__ == "__main__":
    main()
