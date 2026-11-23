#!/usr/bin/env python3
"""Fetch GitHub Actions artifact ZIP, verify API SHA-256 and CRC, extract safely.

Uses stdlib only; never forwards GITHUB_TOKEN to the blob-storage redirect host.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import tempfile
import time
import urllib.error
import urllib.request
import zipfile

API = "https://api.github.com"
REPOSITORY = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\Z")
SHA256 = re.compile(r"sha256:([0-9a-f]{64})\Z")
MAX_ARCHIVE = 512 * 1024 * 1024
MAX_UNPACKED = 3 * 1024 * 1024 * 1024
MAX_ENTRIES = 10000


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def api_get(path: str, token: str) -> object:
    request = urllib.request.Request(
        API + path,
        headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json",
                 "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "encore-ci-artifact-verify"},
    )
    with urllib.request.urlopen(request, timeout=45) as response:
        return json.load(response)


def select_artifact(repository: str, run_id: int, name: str, token: str) -> dict:
    # upload-artifact can finish before GitHub's run-artifact listing has
    # indexed its new ID. The native build ZIP was already uploaded when a
    # same-second read returned zero results. Retry ONLY the empty listing;
    # duplicate names, bad digests and unrelated runs still fail closed.
    for attempt in range(10):
        found = []
        for page in range(1, 21):
            response = api_get(
                f"/repos/{repository}/actions/runs/{run_id}/artifacts?per_page=100&page={page}",
                token,
            )
            artifacts = response["artifacts"]
            found.extend(a for a in artifacts if a["name"] == name)
            if len(artifacts) < 100:
                break
        if len(found) == 1:
            break
        if len(found) > 1 or attempt == 9:
            raise ValueError(
                f"expected exactly one artifact {name!r} on run {run_id}; got {len(found)}"
            )
        time.sleep(3)
    artifact = found[0]
    if artifact.get("expired"):
        raise ValueError("artifact has expired")
    if artifact.get("workflow_run", {}).get("id") not in (None, run_id):
        raise ValueError("artifact run identity mismatch")
    if not SHA256.fullmatch(artifact.get("digest") or ""):
        raise ValueError("artifact API is missing an authoritative SHA-256 digest")
    if not 0 < artifact.get("size_in_bytes", 0) <= MAX_ARCHIVE:
        raise ValueError("artifact archive exceeds size limits")
    return artifact


def download(repository: str, artifact: dict, token: str, archive: Path) -> None:
    # Never forward Authorization outside api.github.com.
    url = f"{API}/repos/{repository}/actions/artifacts/{artifact['id']}/zip"
    request = urllib.request.Request(
        url, headers={"Authorization": f"Bearer {token}", "User-Agent": "encore-ci-artifact-verify"},
    )
    opener = urllib.request.build_opener(NoRedirect)
    # The public artifact redirect may become readable a few seconds after
    # upload completion, even when the artifact list already exposes its ID.
    location = None
    for attempt in range(8):
        try:
            with opener.open(request, timeout=45):
                raise RuntimeError("expected GitHub artifact ZIP to redirect to blob storage")
        except urllib.error.HTTPError as error:
            if error.code in (302, 303, 307, 308):
                location = error.headers.get("Location", "")
                break
            if error.code != 404 or attempt == 7:
                raise
            time.sleep(3)
    if not location:
        raise ValueError("GitHub did not return an artifact ZIP redirect")
    from urllib.parse import urlsplit
    u = urlsplit(location)
    if u.scheme != "https" or not u.netloc or u.username or u.password:
        raise ValueError("artifact redirect must be an HTTPS URL without credentials")
    # Following blob storage requests are unauthenticated.
    blob_request = urllib.request.Request(location, headers={"User-Agent": "encore-ci-artifact-verify"})
    size = 0
    digest = hashlib.sha256()
    with urllib.request.urlopen(blob_request, timeout=90) as stream, archive.open("wb") as output:
        while chunk := stream.read(1024 * 1024):
            size += len(chunk)
            if size > MAX_ARCHIVE:
                raise ValueError("artifact download exceeds hard size limit")
            output.write(chunk)
            digest.update(chunk)
    if size != artifact["size_in_bytes"]:
        raise ValueError(f"artifact archive size mismatch: {size} != {artifact['size_in_bytes']}")
    expected = SHA256.fullmatch(artifact["digest"]).group(1)
    if digest.hexdigest() != expected:
        raise ValueError("artifact ZIP SHA-256 does not match GitHub's published digest")


def inspect_zip(archive: Path) -> int:
    paths = set()
    unpacked = 0
    with zipfile.ZipFile(archive) as zipfile_handle:
        infos = zipfile_handle.infolist()
        if not infos or len(infos) > MAX_ENTRIES:
            raise ValueError("empty or excessive ZIP directory")
        for info in infos:
            name = info.filename
            parts = name.rstrip("/").split("/")
            if not name or name.startswith("/") or "\\" in name or ":" in name or any(p in ("", ".", "..") for p in parts):
                raise ValueError(f"unsafe ZIP path: {name!r}")
            normalized = str(PurePosixPath(*parts))
            if normalized in paths:
                raise ValueError(f"duplicate ZIP path: {normalized!r}")
            paths.add(normalized)
            if stat.S_IFMT(info.external_attr >> 16) == stat.S_IFLNK:
                raise ValueError(f"ZIP symlink forbidden: {name!r}")
            unpacked += info.file_size
            if unpacked > MAX_UNPACKED:
                raise ValueError("ZIP expands beyond unpacked size limit")
        damaged = zipfile_handle.testzip()
        if damaged is not None:
            raise ValueError(f"bad ZIP CRC for {damaged!r}")
    return len(infos)


def extract(archive: Path, destination: Path) -> int:
    members = inspect_zip(archive)
    destination = destination.resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and (not destination.is_dir() or any(destination.iterdir())):
        raise ValueError(f"destination is not empty: {destination}")
    temporary = Path(tempfile.mkdtemp(prefix=f".{destination.name}-extract-", dir=destination.parent))
    try:
        with zipfile.ZipFile(archive) as zipfile_handle:
            zipfile_handle.extractall(temporary)
        if destination.exists():
            destination.rmdir()
        temporary.rename(destination)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)
    return members


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--run-id", required=True, type=int)
    parser.add_argument("--name", required=True)
    parser.add_argument("--dest", required=True, type=Path)
    args = parser.parse_args()
    if not REPOSITORY.fullmatch(args.repo) or args.run_id <= 0 or not args.name:
        parser.error("invalid repository, run ID, or name")
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        parser.error("GITHUB_TOKEN or GH_TOKEN is required")
    artifact = select_artifact(args.repo, args.run_id, args.name, token)
    with tempfile.TemporaryDirectory(prefix="encore-artifact-") as tmp:
        archive = Path(tmp) / "payload.zip"
        download(args.repo, artifact, token, archive)
        members = extract(archive, args.dest)
    print(f"ENCORE_ARTIFACT_DIGEST_PASS id={artifact['id']} files={members} sha256={artifact['digest'].split(':')[1]}")


if __name__ == "__main__":
    main()
