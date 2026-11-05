#!/usr/bin/env python3
"""Release publishing metadata tests (no network/console)."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

P = Path(__file__).with_name("resolve-encore-release.py")
spec = importlib.util.spec_from_file_location("resolve_encore_release", P)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
SOURCE = "a" * 40


class ReleaseVersionTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.app = Path(self.temp.name) / "PPSA99008"
        (self.app / "sce_sys").mkdir(parents=True)
        self.native = {
            "titleId": module.TITLE,
            "contentId": module.CONTENT_ID,
            "contentVersion": "01.000.065",
        }
        self.write_native()
        self.manifest = {
            "build_revision": "R25",
            "source_sha": SOURCE,
            "native_content_version": "01.000.065",
        }
        self.write_manifest()

    def write_native(self):
        (self.app / "sce_sys/param.json").write_text(json.dumps(self.native))

    def write_manifest(self):
        (self.app / "encore-release.json").write_text(json.dumps(self.manifest))

    def test_real_revision_used_everywhere(self):
        result = module.resolve(self.app, SOURCE)
        self.assertEqual(result["label"], "R25")
        self.assertEqual(result["tag"], "encore-R25-aaaaaaaa")
        self.assertEqual(result["zip"], "Eden-Encore-R25-aaaaaaaa-FTP-PPSA99008.zip")
        self.assertFalse(result["legacy"])

    def test_correct_r_label_wrong_native_version_refused(self):
        self.native["contentVersion"] = "01.000.064"
        self.manifest["native_content_version"] = "01.000.064"
        self.write_native()
        self.write_manifest()
        with self.assertRaisesRegex(ValueError, "does not match compiled R revision"):
            module.resolve(self.app, SOURCE)

    def test_mismatch_source_refused(self):
        with self.assertRaisesRegex(ValueError, "source SHA"):
            module.resolve(self.app, "b" * 40)

    def test_mismatch_native_version_refused(self):
        self.native["contentVersion"] = "01.000.064"
        self.write_native()
        with self.assertRaisesRegex(ValueError, "contentVersion mismatch"):
            module.resolve(self.app, SOURCE)

    def test_invalid_label_refused(self):
        for value in ("R0", "R", "R1-dev", "../R2", "v1.0"):
            self.manifest["build_revision"] = value
            self.write_manifest()
            with self.assertRaisesRegex(ValueError, "compiled R revision"):
                module.resolve(self.app, SOURCE)

    def test_wrong_title_and_content_refused(self):
        self.native["titleId"] = "PPSA99000"
        self.write_native()
        with self.assertRaisesRegex(ValueError, "title identity"):
            module.resolve(self.app, SOURCE)
        self.native["titleId"] = module.TITLE
        self.native["contentId"] = "unexpected"
        self.write_native()
        with self.assertRaisesRegex(ValueError, "title identity"):
            module.resolve(self.app, SOURCE)

    def test_missing_manifest_new_release_refused(self):
        (self.app / "encore-release.json").unlink()
        with self.assertRaisesRegex(ValueError, "attestation missing"):
            module.resolve(self.app, SOURCE)

    def test_original_r1_exception(self):
        (self.app / "encore-release.json").unlink()
        self.native["contentVersion"] = "01.000.041"
        self.write_native()
        result = module.resolve(self.app, module.LEGACY_SHA)
        self.assertEqual(result["label"], "R1")
        self.assertEqual(result["tag"], "encore-R1-56293953")
        self.assertTrue(result["legacy"])

    def test_legacy_exception_refuses_other_native_version(self):
        (self.app / "encore-release.json").unlink()
        self.native["contentVersion"] = "01.000.043"
        self.write_native()
        with self.assertRaisesRegex(ValueError, "attestation missing"):
            module.resolve(self.app, module.LEGACY_SHA)

    def test_publishers_no_longer_hardcode_release_r1(self):
        root = Path(__file__).resolve().parents[2]
        modern = (root / ".github/workflows/publish-validated-build.yml").read_text()
        legacy = (root / ".github/workflows/build-040-zbic.yml").read_text()
        dist = (root / "tools/ci/make-dist.py").read_text()
        package = (root / "tools/package-headless-native.sh").read_text()
        cmake = (root / "headless/CMakeLists.txt").read_text()
        self.assertIn("steps.package.outputs.label", modern)
        self.assertNotIn('tag="encore-R1-', legacy)
        self.assertIn('release = release_info["label"]', dist)
        self.assertIn("encore-release.json", package)
        self.assertIn('set(EDEN_LAUNCHER_BUILD_LABEL "" CACHE STRING', cmake)


if __name__ == "__main__":
    unittest.main()
