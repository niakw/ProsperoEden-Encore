#!/usr/bin/env python3
"""Monotonic PS5 package version / R revision contract. No console dependency."""
import importlib.util
import unittest
from pathlib import Path

path = Path(__file__).with_name("native-content-version.py")
spec = importlib.util.spec_from_file_location("native_content_version", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class NativeContentVersionTest(unittest.TestCase):
    def test_new_release_revision_one_starts_at_400(self):
        self.assertEqual(module.package_version("R1"), "01.400.001")

    def test_increments_for_every_released_revision(self):
        self.assertEqual(module.package_version("R2"), "01.400.002")
        self.assertEqual(module.package_version("R25"), "01.400.025")
        self.assertEqual(module.package_version("R323"), "01.400.323")
        self.assertEqual(module.package_version("R385"), "01.400.385")
        self.assertEqual(module.package_version("R999"), "01.400.999")

    def test_strict_increasing_numeric_versions(self):
        last = (0, 0, 0)
        for revision in range(1, 1000):
            current = tuple(map(int, module.package_version(f"R{revision}").split(".")))
            self.assertGreater(current, last)
            last = current

    def test_refuses_bad_or_overflowing_revisions(self):
        for value in ("R0", "R01", "R", "R1-rc", "v2", "R1000000",
                      "R1000", "R999960", "../R25", "R-2", "R1.0"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    module.package_version(value)


if __name__ == "__main__":
    unittest.main()
