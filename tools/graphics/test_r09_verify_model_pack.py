#!/usr/bin/env python3
"""Non-proprietary NRMODEL1 verifier regression fixtures."""
import hashlib
from pathlib import Path
import struct
import tempfile
import unittest

from r09_verify_model_pack import (ModelPolicy, ModelRejected, load_hashes,
                                   policy_for, verify_model, check_reference_manifest)


def model_bytes(entries):
    header = bytearray(b"NRMODEL1" + struct.pack("<II", len(entries), 0))
    start = 16 + sum(4 + len(name.encode()) + 16 for name, _ in entries)
    offset = (start + 255) & ~255
    blobs = []
    for name, raw in entries:
        encoded = name.encode()
        header += struct.pack("<I", len(encoded)) + encoded
        header += struct.pack("<QQ", offset, len(raw))
        blobs.append((offset, raw))
        offset = (offset + len(raw) + 255) & ~255
    full = bytearray(max(offset, len(header)))
    full[:len(header)] = header
    for position, raw in blobs:
        full[position:position+len(raw)] = raw
    return full


class VerifyModelPack(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="r09-model-check-")
        self.path = Path(self.temp.name) / "test.nrmodel"
        self.entries = [
            ("unpacked-preblock/block0.layer0.layer.input_lift.bin", b"\x01\x02\x03\x04"),
            ("unpacked-postblock/block70.layer0.layer.out_project.bin", b"\x05\x06\x07\x08"),
        ]
        self.bytes = model_bytes(self.entries)
        self.policy = ModelPolicy(
            len(self.entries), len(self.bytes),
            {name: hashlib.sha256(data).hexdigest() for name, data in self.entries})
        self.path.write_bytes(self.bytes)

    def tearDown(self):
        self.temp.cleanup()

    def reject(self, raw, policy=None):
        self.path.write_bytes(raw)
        with self.assertRaises(ModelRejected):
            verify_model(self.path, policy or self.policy)

    def test_valid_and_corrupt_weight(self):
        verify_model(self.path, self.policy)
        modified = bytearray(self.bytes)
        modified[256] ^= 1
        self.reject(modified)

    def test_index_corruption_and_wrong_variant(self):
        damaged = bytearray(self.bytes)
        damaged[0] ^= 1
        self.reject(damaged)
        damaged = bytearray(self.bytes)
        damaged[8:12] = struct.pack("<I", 3)
        self.reject(damaged)
        self.reject(self.bytes, ModelPolicy(255, len(self.bytes), self.policy.hashes))

    def test_index_alias_and_truncation(self):
        damaged = bytearray(self.bytes)
        name = self.entries[0][0].encode()
        first_offset_pos = 16 + 4 + len(name)
        damaged[first_offset_pos:first_offset_pos+8] = struct.pack("<Q", 0)
        self.reject(damaged)
        self.reject(self.bytes[:-1])

    def test_wrong_inventory_and_wrong_digest(self):
        wrong = dict(self.policy.hashes)
        wrong[self.entries[0][0]] = "0" * 64
        self.reject(self.bytes, ModelPolicy(2, len(self.bytes), wrong))
        wrong = dict(self.policy.hashes)
        wrong.pop(self.entries[0][0])
        self.reject(self.bytes, ModelPolicy(2, len(self.bytes), wrong))

    def test_canonical_public_metadata(self):
        check_reference_manifest()
        self.assertEqual(len(policy_for("original").hashes), 599)
        self.assertEqual(len(policy_for("compact").hashes), 255)


if __name__ == "__main__":
    unittest.main()
