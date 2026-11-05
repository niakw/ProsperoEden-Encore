#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Release files from a built PPSA99008 folder (make release, make image).

  tools/ci/make-dist.py [--image-only] APP_DIR

dist/Prospero.Eden-Encore-RN.zip (the folder plus README, INSTALL, SECURITY, LICENSE,
THIRD_PARTY_NOTICES and LICENSES/; fixed timestamps, so equal inputs give equal bytes),
dist/Prospero.Eden-Encore-RN-FTP.zip (minimal PPSA99008 folder for manual FTP installs:
runtime files only, without installed legal texts or ShadowMount-only .txt language companions),
dist/Prospero.Eden-Encore-RN.ffpfsc
(the same title as a package image, tools/ci/package-image.sh), SHA256SUMS and release-notes.md.
"""
import hashlib
import json
import pathlib
import re
import shutil
import subprocess
import sys
import zipfile

root = pathlib.Path(__file__).resolve().parents[2]
args = sys.argv[1:]
image_only = args[:1] == ['--image-only']
if image_only:
    args = args[1:]
if len(args) != 1:
    sys.exit(__doc__.strip())
app = pathlib.Path(args[0]).resolve()
# The compiled app, not a hardcoded header or workflow HEAD, determines R.
import importlib.util
spec = importlib.util.spec_from_file_location("resolve_encore_release",
                                            root / "tools/ci/resolve-encore-release.py")
resolver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(resolver)
attestation_file = app / "encore-release.json"
if not attestation_file.is_file():
    raise SystemExit("Cannot package unversioned native app: encore-release.json missing")
attestation = json.loads(attestation_file.read_text(encoding="utf-8"))
source_sha = attestation.get("source_sha")
if not isinstance(source_sha, str) or not re.fullmatch(r"[a-f0-9]{40}", source_sha):
    raise SystemExit("Invalid source SHA in release attestation")
try:
    release_info = resolver.resolve(app, source_sha)
except (OSError, ValueError, TypeError) as exc:
    raise SystemExit(f"Native release attestation rejected: {exc}") from exc
release = release_info["label"]
dist = root / 'dist'
image = dist / f'Prospero.Eden-Encore-{release}.ffpfsc'
if image_only:
    dist.mkdir(exist_ok=True)
    subprocess.run(['bash', str(root / 'tools/ci/package-image.sh'), str(app), str(image)], check=True)
    print(f'{image} {hashlib.sha256(image.read_bytes()).hexdigest()}')
    sys.exit(0)
shutil.rmtree(dist, ignore_errors=True)
dist.mkdir()
archive = dist / f'Prospero.Eden-Encore-{release}.zip'
files = [(p, 'PPSA99008/' + p.relative_to(app).as_posix()) for p in sorted(app.rglob('*')) if p.is_file()]
files += [(root / name, name) for name in
          ('README.md', 'INSTALL.md', 'SECURITY.md', 'LICENSE', 'THIRD_PARTY_NOTICES.md')
          if (root / name).exists()]
files += [(p, 'LICENSES/' + p.name) for p in sorted((root / 'LICENSES').iterdir()) if p.is_file()]
with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as zip_file:
    for path, name in files:
        info = zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o644 << 16
        zip_file.writestr(info, path.read_bytes())
digest = hashlib.sha256(archive.read_bytes()).hexdigest()

# Manual PS5 FTP servers commonly support binary STOR only. FileZilla may switch .txt files to
# ASCII automatically, so publish a separate runtime-only folder archive for manual FTP installs.
# The full ZIP and FFPFSC above remain the canonical distribution artifacts and keep every legal
# notice plus the ShadowMount .txt catalog companions.
ftp_archive = dist / f'Prospero.Eden-Encore-{release}-FTP.zip'
ftp_files = []
for path in sorted(app.rglob('*')):
    if not path.is_file():
        continue
    relative = path.relative_to(app)
    posix = relative.as_posix()
    if posix == 'legal' or posix.startswith('legal/'):
        continue
    if relative.parent.as_posix() == 'ui/lang' and relative.suffix == '.txt':
        continue
    ftp_files.append((path, 'PPSA99008/' + posix))
with zipfile.ZipFile(ftp_archive, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as zip_file:
    for path, name in ftp_files:
        info = zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o644 << 16
        zip_file.writestr(info, path.read_bytes())
ftp_digest = hashlib.sha256(ftp_archive.read_bytes()).hexdigest()

subprocess.run(['bash', str(root / 'tools/ci/package-image.sh'), str(app), str(image)], check=True)
image_digest = hashlib.sha256(image.read_bytes()).hexdigest()
# Prove the package-image path is deterministic before publishing its checksum. This catches a
# third-party timestamp/randomness regression instead of silently changing release bytes.
repro = dist / f'.{image.name}.repro'
try:
    subprocess.run(['bash', str(root / 'tools/ci/package-image.sh'), str(app), str(repro)], check=True)
    repro_digest = hashlib.sha256(repro.read_bytes()).hexdigest()
    if repro_digest != image_digest:
        # Report byte offsets, not just hashes. This check still fails closed;
        # do not publish potentially nondeterministic release image bytes.
        subprocess.run([sys.executable, str(root / 'tools/ci/diagnose-image-repro.py'),
                        str(image), str(repro)], check=False)
        raise SystemExit(f'FFPFSC reproducibility check failed: {image_digest} != {repro_digest}')
finally:
    repro.unlink(missing_ok=True)
(dist / 'SHA256SUMS').write_text(
    f'{digest}  {archive.name}\n'
    f'{ftp_digest}  {ftp_archive.name}\n'
    f'{image_digest}  {image.name}\n'
)
# The unstripped executable of this release, to name the functions in a crash report later
# (tools/symbolize-crash.py). Kept out of dist/: it is not a release file.
unstripped = root / 'build/headless-native/llvm-pie.elf'
if unstripped.exists():
    symbols = root / 'build/symbols' / f'Prospero.Eden-Encore-{release}.elf'
    symbols.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(unstripped, symbols)
    print(f'{symbols} (keep it with the release: crash reports are read with it)')
readme = (root / 'README.md').read_text()
heading = f'Encore {release}'
match = re.search(rf'^## Changes in {re.escape(heading)}\n(.*?)(?=^## )', readme, re.M | re.S)
if match:
    (dist / 'release-notes.md').write_text(match.group(1).strip() + '\n')
else:
    # Do not publish outdated R1 notes for an R25 artifact.
    (dist / 'release-notes.md').write_text(
        f'# Eden Encore {release} — native PS5 build\n\n'
        f'Compiled source SHA: {source_sha}\n\n'
        'Package metadata and checksums are bound to this artifact. '
        'A successful build does not establish gameplay or console stability.\n'
    )
print(f'{archive} {digest}')
print(f'{ftp_archive} {ftp_digest}')
print(f'{image} {image_digest}')
