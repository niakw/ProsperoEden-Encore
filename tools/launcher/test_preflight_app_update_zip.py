#!/usr/bin/env python3
"""R21 host tests: bad archive, wrong title, unsafe file and rollback limits."""
import hashlib
import json
import stat
import tempfile
import unittest
import zipfile
from pathlib import Path

from preflight_app_update_zip import CONTENT_ID, UnsafeUpdate, inspect_zip


class ZipPreflightTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "release.zip"

    def make_zip(self, changes=None, *, prefix="PPSA99008/", compression=zipfile.ZIP_STORED):
        param = {
            "titleId": "PPSA99008",
            "contentId": CONTENT_ID,
            "contentVersion": "01.000.042",
        }
        files = {
            prefix + "eboot.bin": b"x" * 2800,
            prefix + "sce_module/libc.prx": b"shim",
            prefix + "sce_sys/param.json": json.dumps(param).encode(),
            prefix + "legal/LICENSE": b"".join(
                hashlib.sha256(f"licence-{i}".encode()).digest() for i in range(64)
            ),
        }
        if changes:
            files.update(changes)
        with zipfile.ZipFile(self.path, "w", compression=compression) as archive:
            for filename, content in files.items():
                archive.writestr(filename, content)
        return hashlib.sha256(self.path.read_bytes()).hexdigest()

    def check(self, *, digest=None):
        if digest is None:
            digest = hashlib.sha256(self.path.read_bytes()).hexdigest()
        return inspect_zip(self.path, digest, "01.000.041")

    def test_valid_title_and_monotonic_version(self):
        digest = self.make_zip()
        result = self.check(digest=digest)
        self.assertTrue(result["ok"])
        self.assertEqual(result["content_version"], "01.000.042")
        self.assertEqual(result["files"], 4)

    def test_flat_install_folder_is_supported(self):
        self.make_zip(prefix="")
        self.assertEqual(self.check()["title_id"], "PPSA99008")

    def test_altered_archive_fails_official_digest(self):
        digest = self.make_zip()
        self.path.write_bytes(self.path.read_bytes() + b"tamper")
        with self.assertRaisesRegex(UnsafeUpdate, "SHA-256"):
            self.check(digest=digest)

    def test_wrong_title_id_rejected(self):
        self.make_zip({"PPSA99008/sce_sys/param.json": json.dumps({
            "titleId": "PPSA99999", "contentId": CONTENT_ID,
            "contentVersion": "01.000.042"
        })})
        with self.assertRaisesRegex(UnsafeUpdate, "identity"):
            self.check()

    def test_wrong_content_id_rejected(self):
        self.make_zip({"PPSA99008/sce_sys/param.json": json.dumps({
            "titleId": "PPSA99008", "contentId": "other",
            "contentVersion": "01.000.042"
        })})
        with self.assertRaisesRegex(UnsafeUpdate, "identity"):
            self.check()

    def test_version_not_newer_rejected(self):
        self.make_zip({"PPSA99008/sce_sys/param.json": json.dumps({
            "titleId": "PPSA99008", "contentId": CONTENT_ID,
            "contentVersion": "01.000.041"
        })})
        with self.assertRaisesRegex(UnsafeUpdate, "not newer"):
            self.check()

    def test_wrong_version_format_rejected(self):
        self.make_zip({"PPSA99008/sce_sys/param.json": json.dumps({
            "titleId": "PPSA99008", "contentId": CONTENT_ID,
            "contentVersion": "R2"
        })})
        with self.assertRaisesRegex(UnsafeUpdate, "contentVersion"):
            self.check()

    def test_unsafe_parent_traversal_rejected(self):
        self.make_zip({"PPSA99008/../../user/keys.dat": "malicious"})
        with self.assertRaisesRegex(UnsafeUpdate, "traversal"):
            self.check()

    def test_absolute_path_rejected(self):
        self.make_zip({"/tmp/a": "malicious"})
        with self.assertRaisesRegex(UnsafeUpdate, "absolute"):
            self.check()

    def test_protected_user_data_rejected(self):
        self.make_zip({"PPSA99008/keys/prod.keys": "malicious"})
        with self.assertRaisesRegex(UnsafeUpdate, "user-owned"):
            self.check()

    def test_assets_keys_folder_rejected(self):
        self.make_zip({"PPSA99008/assets/keys/prod.keys": "malicious"})
        with self.assertRaisesRegex(UnsafeUpdate, "user-owned"):
            self.check()

    def test_unsupported_zip_algorithm_rejected(self):
        self.make_zip(compression=zipfile.ZIP_BZIP2)
        with self.assertRaisesRegex(UnsafeUpdate, "unsupported ZIP compression"):
            self.check()

    def test_empty_eboot_rejected(self):
        self.make_zip({"PPSA99008/eboot.bin": b""})
        with self.assertRaisesRegex(UnsafeUpdate, "empty required"):
            self.check()

    def test_symlink_rejected(self):
        digest = self.make_zip()
        with zipfile.ZipFile(self.path, "a") as archive:
            link = zipfile.ZipInfo("PPSA99008/eboot-link")
            link.create_system = 3
            link.external_attr = (stat.S_IFLNK | 0o777) << 16
            archive.writestr(link, "eboot.bin")
        with self.assertRaisesRegex(UnsafeUpdate, "symlink"):
            self.check()

    def test_duplicate_case_insensitive_path_rejected(self):
        self.make_zip({"PPSA99008/EBOOT.BIN": b"other"})
        with self.assertRaisesRegex(UnsafeUpdate, "case-colliding"):
            self.check()

    def test_unexpected_missing_runtime_rejected(self):
        self.make_zip()
        with zipfile.ZipFile(self.path, "w", compression=zipfile.ZIP_STORED) as archive:
            archive.writestr("PPSA99008/eboot.bin", b"x" * 4000)
        with self.assertRaisesRegex(UnsafeUpdate, "required"):
            self.check()

    def test_not_zip_rejected(self):
        self.path.write_bytes(b"not a zip" * 300)
        with self.assertRaisesRegex(UnsafeUpdate, "ZIP archive"):
            self.check()

    def test_high_expansion_ratio_rejected(self):
        self.make_zip({"PPSA99008/ui/zeros.bin": b"\0" * (2 * 1024 * 1024)},
                      compression=zipfile.ZIP_DEFLATED)
        with self.assertRaisesRegex(UnsafeUpdate, "compression ratio"):
            self.check()

    def test_invalid_param_json_rejected(self):
        self.make_zip({"PPSA99008/sce_sys/param.json": "{truncated"})
        with self.assertRaisesRegex(UnsafeUpdate, "param.json"):
            self.check()


if __name__ == "__main__":
    unittest.main()
