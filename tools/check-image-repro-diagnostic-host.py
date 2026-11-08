#!/usr/bin/env python3
"""Exercise reproducibility diagnostics with equal, changed and short images."""
from pathlib import Path
import subprocess
import sys
import tempfile

root = Path(__file__).resolve().parents[1]
script = root / "tools/ci/diagnose-image-repro.py"
make_dist = (root / "tools/ci/make-dist.py").read_text()
# The shipping format changed: the normal release produces deterministic
# ZIP + FTP ZIP and SHA256SUMS; FFPFSC is explicitly developer-only.
# Do NOT restore an obsolete two-build image parity loop to production just
# to satisfy this test. The binary diff tool itself is still exercised below.
assert "image_only = args[:1] == ['--image-only']" in make_dist
assert "if image_only:" in make_dist
assert "tools/ci/package-image.sh" in make_dist
assert "sys.exit(0)" in make_dist
assert "FFPFSC is an explicit --image-only developer command" in make_dist
assert "ftp_archive = dist / release_info['zip']" in make_dist
assert "with zipfile.ZipFile(ftp_archive" in make_dist
assert "ftp_digest = hashlib.sha256(ftp_archive.read_bytes()).hexdigest()" in make_dist
assert "'SHA256SUMS'" in make_dist
assert make_dist.index("if image_only:") < make_dist.index(
    "shutil.rmtree(dist, ignore_errors=True)")
assert make_dist.index("ftp_digest = hashlib.sha256(") < make_dist.index(
    "(dist / 'SHA256SUMS').write_text(")

with tempfile.TemporaryDirectory(prefix="encore-pfs-diff-") as tmp:
    left = Path(tmp) / "a.ffpfsc"
    right = Path(tmp) / "b.ffpfsc"
    payload = bytearray(b"A" * (1024 * 1024 + 12))
    left.write_bytes(payload)
    right.write_bytes(payload)
    same = subprocess.run([sys.executable, str(script), str(left), str(right)],
                          capture_output=True, text=True, check=True)
    assert "first_different_offset=None" in same.stdout
    payload[1024 * 1024 + 5] = ord("B")
    right.write_bytes(payload)
    diff = subprocess.run([sys.executable, str(script), str(left), str(right)],
                          capture_output=True, text=True)
    assert diff.returncode == 1
    assert "first_different_offset=1048581" in diff.stdout
    assert "offset=0x100005" in diff.stdout
    right.write_bytes(bytes(payload[:100]))
    short = subprocess.run([sys.executable, str(script), str(left), str(right)],
                           capture_output=True, text=True)
    assert short.returncode == 1
    assert "first_different_offset=100" in short.stdout
    assert "a=41 b=EOF" in short.stdout
print("FFPFSC_REPRO_DIAGNOSTIC_PASS")
