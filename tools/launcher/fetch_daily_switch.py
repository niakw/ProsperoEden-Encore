#!/usr/bin/env python3
"""Produce a bounded, offline, daily-rotating Switch 1/2 wallpaper snapshot.

Optional build-time utility; never runs inside a PS5 UI frame. No copyrighted
game binaries or firmware. Community release metadata is cross-checked and
images come only from pre-approved Nintendo/Nlib hosts.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

NS2_SOURCE = "https://raw.githubusercontent.com/codemaverick-hub/switch2-tracker/main/data/games.json"
NS1_SOURCE = "https://raw.githubusercontent.com/Langegen/switch-game-collection/main/new_release.json"
DATA_HOSTS = {"raw.githubusercontent.com"}
ART_HOSTS = {"api.nlib.cc", "www.nintendo.com", "assets.nintendo.eu"}
MAX_FEED = 3 * 1024 * 1024
MAX_IMAGE = 7 * 1024 * 1024
MAX_ITEMS = 8
MAX_LOOKBACK = 180

def fetch(url: str, hosts: set[str], maximum: int, timeout: int = 9) -> bytes:
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.hostname not in hosts or parsed.username or parsed.password:
        raise ValueError("Unapproved network origin")
    with urlopen(Request(url, headers={"User-Agent": "EncoreThemeArt/1.0"}),
                 timeout=timeout) as response:
        final = urlsplit(response.geturl())
        if final.scheme != "https" or final.hostname not in hosts:
            raise ValueError("Unexpected redirect")
        raw = response.read(maximum + 1)
    if not raw or len(raw) > maximum:
        raise ValueError("Invalid response length")
    return raw

def valid_day(raw: object, today: date, fmt: str) -> date | None:
    if not isinstance(raw, str):
        return None
    try:
        day = datetime.strptime(raw, fmt).date()
    except ValueError:
        return None
    if today - timedelta(days=MAX_LOOKBACK) <= day <= today:
        return day
    return None

def ns2_candidates(feed: dict, today: date) -> list[dict]:
    if not isinstance(feed, dict) or not isinstance(feed.get("games"), list):
        return []
    result, seen = [], set()
    for entry in feed["games"][:3000]:
        if not isinstance(entry, dict) or entry.get("status") != "r":
            continue
        title, art = entry.get("title"), entry.get("art")
        released = valid_day(entry.get("date"), today, "%b %d, %Y")
        if not isinstance(title, str) or not title.strip() or len(title) > 160 or not released:
            continue
        if not isinstance(art, str) or urlsplit(art).hostname not in ART_HOSTS:
            continue
        key = title.casefold().strip()
        if key in seen:
            continue
        seen.add(key)
        result.append(dict(title=title.strip(), day=released, platform="ns2", art=art))
    result.sort(key=lambda x: (-x["day"].toordinal(), x["title"].casefold()))
    return result[:64]

def verified_ns1(item: dict, today: date) -> dict | None:
    if not isinstance(item, dict):
        return None
    tid = item.get("title_id")
    if not isinstance(tid, str) or not re.fullmatch("[0-9A-Fa-f]{16}", tid):
        return None
    tid = tid.upper()
    # Never use the titles of this community list as release-date proof.
    try:
        payload = fetch(f"https://api.nlib.cc/nx/{tid}?fields=name,releaseDate,console,type,isDemo,banner",
                        {"api.nlib.cc"}, 8192)
        record = json.loads(payload)
        if not isinstance(record, dict) or record.get("id") != tid:
            return None
        if record.get("type") != "base" or record.get("console") != "nx" or record.get("isDemo") is True:
            return None
        released = valid_day(record.get("releaseDate"), today, "%Y-%m-%d")
        name = record.get("name")
        if not released or not isinstance(name, str) or not name or len(name) > 160:
            return None
        if not isinstance(record.get("banner"), str):
            return None
        # Construct the HTTPS path instead of trusting the JSON-provided URL.
        return dict(title=name, day=released, platform="ns1",
                    art=f"https://api.nlib.cc/nx/{tid}/banner/720p")
    except (ValueError, OSError, TimeoutError, json.JSONDecodeError):
        return None

def gather(today: date) -> list[dict]:
    ns1, ns2 = [], []
    try:
        ns2 = ns2_candidates(json.loads(fetch(NS2_SOURCE, DATA_HOSTS, MAX_FEED)), today)
    except (OSError, ValueError, TimeoutError, json.JSONDecodeError) as exc:
        print(f"NS2 feed unavailable: {type(exc).__name__}", file=sys.stderr)
    try:
        items = json.loads(fetch(NS1_SOURCE, DATA_HOSTS, MAX_FEED))
        if isinstance(items, list):
            with ThreadPoolExecutor(max_workers=5) as pool:
                ns1 = [x for x in pool.map(lambda i: verified_ns1(i, today), items[:60]) if x]
    except (OSError, ValueError, TimeoutError, json.JSONDecodeError) as exc:
        print(f"NS1 feed unavailable: {type(exc).__name__}", file=sys.stderr)
    ns1.sort(key=lambda x: (-x["day"].toordinal(), x["title"].casefold()))
    # Keep eight newest verified releases irrespective of platform: new
    # titles replace the oldest release, not a fixed NS1/NS2 quota.
    seen = set()
    result = []
    for item in sorted(ns1 + ns2,
                       key=lambda x: (-x["day"].toordinal(),
                                      x["title"].casefold(), x["platform"])):
        key = item["title"].casefold().strip()
        if key in seen:
            continue
        result.append(item)
        seen.add(key)
        if len(result) == MAX_ITEMS:
            break
    return result

def convert_art(source: Path, target: Path) -> None:
    # ImageMagick 7 exposes 'magick identify'; Ubuntu 24.04 may ship
    # ImageMagick 6 as separate 'convert' and 'identify' programs.
    magick = shutil.which("magick")
    if magick:
        convert = [magick]
        identify = [magick, "identify"]
    else:
        convert_exe = shutil.which("convert")
        identify_exe = shutil.which("identify")
        if not convert_exe or not identify_exe:
            raise RuntimeError("ImageMagick (magick or convert+identify) required")
        convert = [convert_exe]
        identify = [identify_exe]
    prefix = convert + ["-limit", "memory", "256MiB", "-limit", "map", "256MiB"]
    meta = subprocess.check_output(identify + ["-limit", "memory", "256MiB", "-limit", "map", "256MiB", "-format", "%w %h", str(source)],
                                   timeout=12, text=True)
    width, height = map(int, meta.split())
    if not (300 <= width <= 4096 and 200 <= height <= 4096 and width*height <= 12_000_000):
        raise ValueError("Unacceptable image dimensions")
    if width / height >= 1.40:
        command = prefix + [str(source), "-auto-orient", "-resize", "1280x720^",
                            "-gravity", "center", "-extent", "1280x720"]
    else:
        # Square/portrait covers remain recognizable on an ambient blurred canvas.
        command = prefix + [str(source), "-auto-orient", "-resize", "1280x720^",
                            "-gravity", "center", "-extent", "1280x720", "-blur", "0x22",
                            "(", str(source), "-auto-orient", "-resize", "480x670", ")",
                            "-gravity", "center", "-compose", "over", "-composite"]
    # Normalize EXIF orientation before stripping it. No double flip;
    # built-in launcher images use lossy WebP, not JPEG.
    command += ["-strip", "-quality", "80", "-define", "webp:method=5",
                "-define", "webp:lossless=false", str(target)]
    subprocess.run(command, timeout=28, check=True, stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL)
    if target.suffix.lower() != ".webp" or not target.exists():
        raise ValueError("Built-in wallpaper must be WebP")
    data = target.read_bytes()
    if not (4000 <= len(data) <= MAX_IMAGE and
            data[:4] == b"RIFF" and data[8:12] == b"WEBP" and
            int.from_bytes(data[4:8], "little") + 8 == len(data) and
            data[12:16] in (b"VP8 ", b"VP8L", b"VP8X")):
        raise ValueError("Converted WebP invalid")

def existing_catalog(out: Path, today: date) -> list[dict]:
    """Read only a bounded, previously approved WebP catalog, never user paths."""
    index = out / "index.json"
    if index.is_symlink() or not index.is_file() or index.stat().st_size > 64 * 1024:
        return []
    try:
        manifest = json.loads(index.read_text(encoding="utf-8"))
        if not isinstance(manifest, dict) or manifest.get("schema") != 1:
            return []
        entries = manifest.get("entries", [])
        if not isinstance(entries, list) or len(entries) > MAX_ITEMS:
            return []
        cached = []
        for n, item in enumerate(entries):
            if not isinstance(item, dict) or item.get("approved") is not True:
                continue
            if item.get("filename") != f"wall-{n:02d}.webp":
                continue
            if item.get("platform") not in ("ns1", "ns2"):
                continue
            title = item.get("title")
            if not isinstance(title, str) or not (0 < len(title) <= 160):
                continue
            released = date.fromisoformat(item["release_date"])
            # A retained snapshot is not an exemption from the "recent games"
            # admission window. Old titles cannot stay in rotation forever
            # when fresh metadata is temporarily unavailable.
            if not today - timedelta(days=MAX_LOOKBACK) <= released <= today:
                continue
            media = out / item["filename"]
            if media.is_symlink() or not media.is_file():
                continue
            raw = media.read_bytes()
            if not (4000 <= len(raw) <= MAX_IMAGE and
                    raw[:4] == b"RIFF" and raw[8:12] == b"WEBP" and
                    int.from_bytes(raw[4:8], "little") + 8 == len(raw) and
                    raw[12:16] in (b"VP8 ", b"VP8L", b"VP8X")):
                continue
            cached.append(dict(title=title, platform=item["platform"],
                               day=released, cached=raw))
        return cached
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
        return []


def build(out: Path, today: date | None = None, candidates: list[dict] | None = None) -> int:
    out.mkdir(parents=True, exist_ok=True)
    now = today or date.today()
    prior = existing_catalog(out, now)
    incoming = candidates if candidates is not None else gather(now)
    # Recent verified games first, then old valid cached releases. Reuse
    # old data rather than re-download the same game on every package build.
    incoming = [x for x in incoming if isinstance(x, dict) and
                isinstance(x.get("day"), date) and
                now - timedelta(days=MAX_LOOKBACK) <= x["day"] <= now and
                isinstance(x.get("title"), str) and x["title"].strip()]
    cache_by_title = {(x["platform"], x["title"].casefold().strip()): x
                      for x in prior}
    ordered = sorted(incoming + prior, key=lambda x: (
        -x["day"].toordinal(), x["title"].casefold(), x["platform"]))
    entries: list[dict] = []
    media: list[bytes] = []
    seen: set[str] = set()
    with tempfile.TemporaryDirectory(prefix="encore-wallpaper-") as temp:
        scratch = Path(temp)
        for item in ordered:
            if len(entries) >= MAX_ITEMS:
                break
            title = item["title"].strip()
            key = title.casefold()
            if key in seen:
                continue
            prior_item = cache_by_title.get((item["platform"], key))
            # Never use yesterday's art for a changed release record.
            reuse = prior_item if prior_item and prior_item["day"] == item["day"] else None
            data = item.get("cached") or (reuse and reuse["cached"])
            if not data:
                art = item.get("art")
                if not isinstance(art, str) or urlsplit(art).hostname not in ART_HOSTS:
                    continue
                try:
                    raw = fetch(art, ART_HOSTS, MAX_IMAGE)
                    src = scratch / "input.media"
                    src.write_bytes(raw)
                    target = scratch / "fresh.webp"
                    convert_art(src, target)
                    data = target.read_bytes()
                except (OSError, ValueError, TimeoutError, subprocess.SubprocessError) as exc:
                    print(f"Artwork skipped ({title}): {type(exc).__name__}", file=sys.stderr)
                    continue
            filename = f"wall-{len(entries):02d}.webp"
            entries.append(dict(title=title[:160], platform=item["platform"],
                                release_date=item["day"].isoformat(),
                                filename=filename, approved=True))
            media.append(data)
            seen.add(key)
    if not entries:
        print("No current or cached WebP art; existing snapshot unchanged", file=sys.stderr)
        return 0
    # All image data is ready before overwriting the old catalog. Manifest
    # publication is last so readers never observe a future incomplete set.
    for entry, data in zip(entries, media):
        dest = out / entry["filename"]
        staged = out / (entry["filename"] + ".tmp")
        try:
            staged.write_bytes(data)
            os.replace(staged, dest)
        finally:
            staged.unlink(missing_ok=True)
    manifest = {"schema": 1, "generated": now.isoformat(),
                "sources": [NS1_SOURCE, NS2_SOURCE], "entries": entries}
    tmp = out / "index.json.tmp"
    try:
        tmp.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                       encoding="utf-8")
        os.replace(tmp, out / "index.json")
    finally:
        tmp.unlink(missing_ok=True)
    keep = {item["filename"] for item in entries}
    for pattern in ("wall-*.webp", "wall-*.jpg", "wall-*.jpeg"):
        for image in out.glob(pattern):
            if image.name not in keep:
                image.unlink()
    print(f"Prepared {len(entries)} audited Switch 1/2 WebPs, newest releases first")
    return len(entries)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        if build(args.output) == 0:
            sys.exit(2)
    except Exception as exc:
        print(f"Daily wallpaper snapshot unavailable: {type(exc).__name__}: {exc}",
              file=sys.stderr)
        sys.exit(2)
