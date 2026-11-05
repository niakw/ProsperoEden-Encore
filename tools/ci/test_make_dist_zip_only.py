#!/usr/bin/env python3
"""R21: release packaging must be deterministic and folder ZIP-only by default."""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

SOURCE_ROOT = Path(__file__).resolve().parents[2]
SHA = "a" * 40


class NativeZipReleaseTest(unittest.TestCase):
    def test_folder_release_uses_exact_compiled_revision_and_no_image(self):
        with tempfile.TemporaryDirectory(prefix="encore-release-qa-") as tmp:
            root = Path(tmp)
            script_dir = root / "tools/ci"
            script_dir.mkdir(parents=True)
            for name in ("make-dist.py", "resolve-encore-release.py"):
                shutil.copyfile(SOURCE_ROOT / "tools/ci" / name, script_dir / name)
            (root / "LICENSES").mkdir()
            (root / "README.md").write_text("# Eden Encore\n")
            (root / "LICENSE").write_text("GPL-3.0-or-later\n")
            app = root / "PPSA99008"
            (app / "sce_sys").mkdir(parents=True)
            (app / "sce_module").mkdir()
            (app / "ui").mkdir()
            (app / "eboot.bin").write_bytes(b"E" * 4096)
            (app / "sce_module/libc.prx").write_bytes(b"L" * 1024)
            (app / "ui/icon0.png").write_bytes(b"placeholder")
            (app / "sce_sys/param.json").write_text(json.dumps({
                "titleId": "PPSA99008",
                "contentId": "UP9000-PPSA99008_00-PROSPEROEDEN0001",
                "contentVersion": "01.000.050",
            }))
            (app / "encore-release.json").write_text(json.dumps({
                "source_sha": SHA,
                "build_revision": "R25",
                "native_content_version": "01.000.050",
            }))
            process = subprocess.run(
                [sys.executable, str(script_dir / "make-dist.py"), str(app)],
                capture_output=True, text=True, cwd=root, timeout=20)
            self.assertEqual(process.returncode, 0, process.stderr)
            dist = root / "dist"
            files = {p.name for p in dist.iterdir()}
            ftp_name = "Eden-Encore-R25-aaaaaaaa-FTP-PPSA99008.zip"
            self.assertEqual(files, {
                ftp_name, "Prospero.Eden-Encore-R25.zip",
                "SHA256SUMS", "release-notes.md"})
            for name in (ftp_name, "Prospero.Eden-Encore-R25.zip"):
                with zipfile.ZipFile(dist / name) as bundle:
                    self.assertIn("PPSA99008/eboot.bin", bundle.namelist())
                    self.assertIn("PPSA99008/encore-release.json", bundle.namelist())
            checksums = dict(
                (name, digest) for digest, name in
                (line.split(maxsplit=1)
                 for line in (dist / "SHA256SUMS").read_text().splitlines()))
            self.assertEqual(set(checksums), {ftp_name, "Prospero.Eden-Encore-R25.zip"})
            for name, digest in checksums.items():
                self.assertEqual(hashlib.sha256((dist / name).read_bytes()).hexdigest(), digest)
            notes = (dist / "release-notes.md").read_text()
            self.assertIn("R25", notes)
            self.assertNotIn("Encore R1", notes)


if __name__ == "__main__":
    unittest.main()
