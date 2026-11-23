#!/usr/bin/env python3
"""Offline fail-closed regression cases for the GitHub Actions artifact reader."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import zipfile
import warnings

script = Path(__file__).with_name("download-verified-artifact.py")
spec = importlib.util.spec_from_file_location("artifact_reader", script)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def makezip(path, files):
    with zipfile.ZipFile(path, "w") as archive:
        for name, data in files:
            archive.writestr(name, data)


class TestVerifiedArtifact(unittest.TestCase):
    def test_good_zip_extracts_and_matches(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "archive.zip"
            makezip(archive, [("PPSA99008/eboot.bin", b"elf"), ("PPSA99008/sce_sys/param.json", b"{}")])
            dest = Path(tmp) / "install"
            self.assertEqual(mod.extract(archive, dest), 2)
            self.assertEqual((dest / "PPSA99008/eboot.bin").read_bytes(), b"elf")

    def test_rejects_zip_slip_absolute_backslash_dotdot(self):
        names = ("../bad", "/bad", "a/../../bad", "C:/evil", "dir\\\\evil", "dir/./file")
        for name in names:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as tmp:
                archive = Path(tmp) / "a.zip"
                makezip(archive, [(name, b"x")])
                with self.assertRaises(ValueError):
                    mod.extract(archive, Path(tmp) / "out")
                self.assertFalse((Path(tmp) / "bad").exists())

    def test_rejects_duplicates_and_existing_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "a.zip"
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                makezip(archive, [("x", b"1"), ("x", b"2")])
            with self.assertRaises(ValueError):
                mod.extract(archive, Path(tmp) / "out")
            makezip(archive, [("x", b"1")])
            dest = Path(tmp) / "out"
            dest.mkdir()
            (dest / "keep").write_text("preserve")
            with self.assertRaises(ValueError):
                mod.extract(archive, dest)
            self.assertEqual((dest / "keep").read_text(), "preserve")

    def test_digest_and_run_validation(self):
        artifact = dict(name="a", id=1, size_in_bytes=100, digest="sha256:" + "0" * 64,
                        expired=False, workflow_run={"id": 44})
        with mock.patch.object(mod, "api_get", return_value={"artifacts": [artifact]}):
            self.assertEqual(mod.select_artifact("x/y", 44, "a", "secret"), artifact)
            with self.assertRaises(ValueError):
                mod.select_artifact("x/y", 45, "a", "secret")
        with mock.patch.object(mod, "api_get", return_value={"artifacts": [dict(artifact, digest=None)]}):
            with self.assertRaises(ValueError):
                mod.select_artifact("x/y", 44, "a", "secret")

    def test_eventually_visible_after_upload(self):
        artifact = dict(name="ready", id=42, size_in_bytes=123,
                        digest="sha256:" + "a" * 64, expired=False,
                        workflow_run={"id": 455})
        # GitHub can return zero artifacts for the first same-second query
        # after upload-artifact succeeded; require a bounded retry.
        with mock.patch.object(mod, "api_get", side_effect=[
            {"artifacts": []}, {"artifacts": [artifact]}
        ]) as api, mock.patch.object(mod.time, "sleep") as pause:
            self.assertEqual(mod.select_artifact("x/y", 455, "ready", "secret"), artifact)
            self.assertEqual(api.call_count, 2)
            pause.assert_called_once_with(3)

        # Never retry duplicate names into a potentially arbitrary choice.
        with mock.patch.object(mod, "api_get", return_value={
            "artifacts": [artifact, dict(artifact, id=43)]
        }), mock.patch.object(mod.time, "sleep") as pause:
            with self.assertRaises(ValueError):
                mod.select_artifact("x/y", 455, "ready", "secret")
            pause.assert_not_called()

    def test_crc_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "a.zip"
            makezip(archive, [("file.txt", b"This-is-a-CRC-check")])
            data = archive.read_bytes().replace(b"This-is-a-CRC-check", b"This-is-a-CrC-check", 1)
            archive.write_bytes(data)
            with self.assertRaises(ValueError):
                mod.inspect_zip(archive)


if __name__ == "__main__":
    unittest.main(verbosity=2)
