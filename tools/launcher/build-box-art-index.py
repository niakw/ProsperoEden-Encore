#!/usr/bin/env python3
"""Build a Switch 1 + Switch 2 flat-box and scene index from Metadata.zip.

The large archive is processed on a build host, NEVER by the console. Only
normalized game names and safe CDN image basenames are packaged, no art assets.
"""
import argparse
import io
import pathlib
import re
import urllib.request
import unicodedata
import xml.etree.ElementTree as ET
import zipfile

SOURCE = "https://gamesdb.launchbox-app.com/Metadata.zip"
IMAGE_FILE = re.compile(r"^(?:r2_)?[0-9a-fA-F-]{36}\.(?:jpg|jpeg|png)$")

# Original physical European front supplied by the user for this exact
# LaunchBox DatabaseID. Keep this in the media INDEX, never in the renderer.
# Current LaunchBox Box - Front (Europe) is an independent fallback. Both
# precede lower-priority regions regardless of resolution.
EUROPE_FRONT_PINS = {
    "79189": (
        "9524e5f7-ccc8-4ce6-a581-03f82c51825e.jpg",
        "a8bcb4cc-a3b0-4cf0-82f3-cb10dd18b27c.jpg",
    ),
}

def normalize(value):
    out = []
    space = False
    for char in value:
        if "A" <= char <= "Z":
            char = char.lower()
        if "a" <= char <= "z" or "0" <= char <= "9":
            out.append(char)
            space = False
        elif out and not space:
            out.append(" ")
            space = True
    return "".join(out).strip()

# Strip only the explicit console-edition suffix, not Deluxe/Ultimate,
# remaster, sequel numbers or other semantic distinctions.
def standard_title(key):
    for suffix in (" nintendo switch 2 edition", " switch 2 edition",
                   " nintendo switch 2 version", " switch 2 version"):
        if key.endswith(suffix):
            return key.removesuffix(suffix).strip()
    return key

def title_keys(label):
    folded = unicodedata.normalize("NFKD", label).encode("ascii", "ignore").decode()
    return {key for spelling in (label, folded)
            for normalized in (normalize(spelling),)
            for key in (normalized, standard_title(normalized)) if key}

def rank(region):
    # User locale first; leave the rest as fallbacks, including a single
    # foreign-region scan. A front and back are ranked independently.
    return {"france": 7, "europe": 6, "world": 5,
            "united kingdom": 4, "germany": 4, "belgium": 4,
            "north america": 3, "united states": 3, "canada": 3,
            "italy": 2, "spain": 2}.get(region.casefold().strip(), 1)

def candidates(items, limit=6):
    # Keep alternate images, do not collapse each side to one filename.
    # A region-preferred first choice may only have a tiny CDN thumbnail,
    # so the console is allowed to try the following candidate.
    seen = set()
    result = []
    for _, filename in sorted(items, key=lambda item: (-item[0], item[1])):
        if filename not in seen:
            result.append(filename)
            seen.add(filename)
        if len(result) >= limit:
            break
    return ";".join(result) if result else "-"

# Region metadata is packaged with every image so the console can choose a
# language-appropriate jacket at runtime (including after language changes).
# Keep both EU/FR and North-American editions; do not hardwire French globally.
REGIONS = {
    "france": "fr", "europe": "eu", "world": "world",
    "north america": "us", "united states": "us", "usa": "us",
    "united kingdom": "uk", "england": "uk",
    "canada": "ca", "germany": "de", "belgium": "eu",
    "italy": "it", "spain": "es", "portugal": "pt",
    "australia": "au", "japan": "jp", "brazil": "br",
    "mexico": "mx", "asia": "asia", "korea": "kr", "south korea": "kr",
    "china": "cn", "taiwan": "tw", "hong kong": "hk",
    "netherlands": "nl", "poland": "pl", "russia": "ru", "thailand": "th",
    "sweden": "sv", "norway": "nb", "denmark": "da", "finland": "fi",
    "greece": "el", "czech republic": "cs", "hungary": "hu",
    "romania": "ro", "turkey": "tr", "ukraine": "ukr", "indonesia": "id",
}
REGION_ORDER = ("fr", "eu", "us", "uk", "ca", "world", "de",
                "es", "it", "pt", "au", "jp", "br", "mx", "asia", "kr", "other")

def region_code(name):
    return REGIONS.get(name.casefold().strip(), "other")

def regional_candidates(items, limit=12, per_region=2):
    # Preserve independent front/back/spine region variants. Cap two sources
    # per region and the total so the on-device index stays small and bounded.
    grouped = {}
    for region, filename in items:
        group = grouped.setdefault(region, [])
        if filename not in group:
            group.append(filename)
    choices = []
    # First cover every available region, then offer its alternate scan.
    # Otherwise two French/European images may displace a Japanese/US face.
    for variant in range(per_region):
        for region in grouped:
            group = grouped.get(region, ())
            if len(group) > variant:
                choices.append(f"{region}:{group[variant]}")
                if len(choices) == limit:
                    return ";".join(choices)
    return ";".join(choices) if choices else "-"

def parse(source):
    games, aliases, images = {}, {}, {}
    iterator = ET.iterparse(source, events=("start", "end"))
    _, root = next(iterator)
    for event, element in iterator:
        if event != "end":
            continue
        tag = element.tag.rsplit("}", 1)[-1]
        if tag == "Game":
            platform = element.findtext("Platform", "")
            gid = element.findtext("DatabaseID", "")
            if gid.isdecimal() and platform:
                games[gid] = (element.findtext("Name", ""),
                              {"Nintendo Switch": "ns1", "Nintendo Switch 2": "ns2"}.get(platform, platform))
        elif tag == "GameAlternateName":
            gid = element.findtext("DatabaseID", "")
            if gid.isdecimal():
                aliases.setdefault(gid, []).append(element.findtext("AlternateName", ""))
        # Images are collected on a second streaming pass after title matching.
        if tag in ("Game", "GameAlternateName", "GameImage"):
            element.clear()
            root.clear()
    names = {}
    platform_names = {}
    keys_by_id = {}
    for gid, (name, platform) in games.items():
        keys = set().union(*(title_keys(label) for label in (name, *aliases.get(gid, ()))))
        keys_by_id[gid] = keys
        for key in keys:
            platform_names.setdefault(key, {}).setdefault(platform, set()).add(gid)
            if platform in ("ns1", "ns2"):
                names.setdefault(f"{platform}:{key}", set()).add(gid)

    def matching_alternatives(key):
        platform, title = key.split(":", 1)
        matches = names.get(key, ())
        if len(matches) != 1:
            return []
        gid = next(iter(matches))
        # Search the STANDARD GamesDB title and every verified alias of the
        # resolved game, not just the localized string used by the launcher.
        # Reject ambiguous releases per platform; never pick an arbitrary sequel.
        candidates = {}
        for spelling in sorted(keys_by_id[gid] | {standard_title(title)}):
            for other_platform, ids in platform_names.get(spelling, {}).items():
                if other_platform != platform:
                    candidates.setdefault(other_platform, set()).update(ids)
        return [next(iter(ids)) for _, ids in sorted(candidates.items())
                if len(ids) == 1]

    eligible = set()
    for key, matching in names.items():
        if len(matching) == 1:
            eligible.update(matching)
            eligible.update(matching_alternatives(key))
    source.seek(0)
    iterator = ET.iterparse(source, events=("start", "end"))
    _, root = next(iterator)
    first_fanart = set()
    for event, element in iterator:
        if event != "end":
            continue
        tag = element.tag.rsplit("}", 1)[-1]
        if tag == "GameImage":
            gid = element.findtext("DatabaseID", "")
            kind = element.findtext("Type", "")
            filename = element.findtext("FileName", "")
            first = kind != "Fanart - Background" or gid not in first_fanart
            if gid in eligible and kind == "Fanart - Background":
                first_fanart.add(gid)
            if (gid in eligible and first and kind in
                    ("Box - Front", "Box - Back", "Box - Spine", "Screenshot - Gameplay",
                     "Fanart - Background", "Screenshot - Game Title", "Square", "Clear Logo", "Banner")
                    and IMAGE_FILE.fullmatch(filename)):
                images.setdefault(gid, {}).setdefault(kind, []).append(
                    (region_code(element.findtext("Region", "")), filename))
        if tag in ("Game", "GameAlternateName", "GameImage"):
            element.clear()
            root.clear()
    lines = ["# Eden Encore media index v11 (platform-first, cross-platform fallbacks, logo and banner)\n"]
    def row(key, gid):
        media = images.get(gid, {})
        front = list(media.get("Box - Front", []))
        if gid in EUROPE_FRONT_PINS:
            front = [("eu", filename) for filename in EUROPE_FRONT_PINS[gid]] + front
        # Fanart is index zero in source order, not region-ranked.
        fanart = ";".join(f"{reg}:{file}" for reg, file in media.get("Fanart - Background", [])[:1]) or "-"
        gameplay = regional_candidates(media.get("Screenshot - Gameplay", []), per_region=3)
        shots = [] if gameplay == "-" else gameplay.split(";")
        fields = [regional_candidates(front),
                  regional_candidates(media.get("Box - Back", [])),
                  regional_candidates(media.get("Box - Spine", [])),
                  fanart, regional_candidates(media.get("Screenshot - Game Title", [])),
                  *[";".join(shots[i::3]) or "-" for i in range(3)],
                  regional_candidates(media.get("Square", [])),
                  regional_candidates(media.get("Clear Logo", [])),
                  regional_candidates(media.get("Banner", []))]
        return fields

    for key, matching in sorted(names.items()):
        if len(matching) != 1:
            continue
        gid = next(iter(matching))
        own = row(key, gid)
        lines.append(key + "\t" + "\t".join(own) + "\n")
        other_ids = matching_alternatives(key)
        alternatives = [[] for _ in own]
        for other in dict.fromkeys(other_ids):
            for col, field in enumerate(row(key, other)):
                if col in (1, 3, 4, 5, 6, 7, 8, 9, 10) and field != "-":
                    alternatives[col].extend(field.split(";"))
        alt = [";".join(list(dict.fromkeys(values))[:12]) or "-" for values in alternatives]
        if any(field != "-" for field in alt):
            lines.append("alt:" + key + "\t" + "\t".join(alt) + "\n")
    return "".join(lines)

def build(archive_path):
    with zipfile.ZipFile(archive_path) as archive:
        xml = [item for item in archive.infolist()
               if pathlib.PurePosixPath(item.filename).name.lower() == "metadata.xml"]
        if len(xml) != 1 or xml[0].file_size > 2 * 1024**3:
            raise ValueError("metadata archive missing or oversized")
        with archive.open(xml[0]) as handle:
            return parse(handle)

def download(target):
    request = urllib.request.Request(SOURCE, headers={"User-Agent": "EdenEncore-IndexBuilder/1.0"})
    with urllib.request.urlopen(request, timeout=40) as response, target.open("wb") as output:
        total = 0
        while block := response.read(1024 * 1024):
            total += len(block)
            if total > 220 * 1024 * 1024:
                raise ValueError("metadata archive exceeded 220 MiB")
            output.write(block)

def self_test():
    sample = """<LaunchBox>
    <Game><DatabaseID>1</DatabaseID><Platform>Nintendo Switch</Platform><Name>Example: Journey</Name></Game>
    <Game><DatabaseID>2</DatabaseID><Platform>Sony Playstation 5</Platform><Name>Example: Journey</Name></Game>
    <Game><DatabaseID>5</DatabaseID><Platform>Nintendo Switch 2</Platform><Name>Example: Next Gen</Name></Game>
    <Game><DatabaseID>3</DatabaseID><Platform>Nintendo Switch</Platform><Name>Ambiguous</Name></Game>
    <Game><DatabaseID>4</DatabaseID><Platform>Nintendo Switch</Platform><Name>Ambiguous</Name></Game>
    <GameImage><DatabaseID>1</DatabaseID><Type>Box - Front</Type><Region>World</Region><FileName>11111111-1111-1111-1111-111111111111.jpg</FileName></GameImage>
    <GameImage><DatabaseID>1</DatabaseID><Type>Box - Front</Type><Region>Europe</Region><FileName>22222222-2222-2222-2222-222222222222.png</FileName></GameImage>
    <GameImage><DatabaseID>1</DatabaseID><Type>Box - Back</Type><Region>France</Region><FileName>33333333-3333-3333-3333-333333333333.jpg</FileName></GameImage>
    <GameImage><DatabaseID>1</DatabaseID><Type>Box - Spine</Type><Region>Europe</Region><FileName>77777777-7777-7777-7777-777777777777.png</FileName></GameImage>
    <GameImage><DatabaseID>1</DatabaseID><Type>Screenshot - Gameplay</Type><Region>World</Region><FileName>88888888-8888-8888-8888-888888888888.jpg</FileName></GameImage>
    <GameImage><DatabaseID>1</DatabaseID><Type>Screenshot - Gameplay</Type><Region>World</Region><FileName>99999999-9999-9999-9999-999999999999.jpg</FileName></GameImage>
    <GameImage><DatabaseID>1</DatabaseID><Type>Fanart - Background</Type><Region>World</Region><FileName>aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa.png</FileName></GameImage>
    <GameImage><DatabaseID>1</DatabaseID><Type>Screenshot - Game Title</Type><Region>World</Region><FileName>bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb.jpg</FileName></GameImage>
    <GameImage><DatabaseID>2</DatabaseID><Type>Box - Back</Type><FileName>44444444-4444-4444-4444-444444444444.jpg</FileName></GameImage>
    <GameImage><DatabaseID>5</DatabaseID><Type>Box - Front</Type><Region>Europe</Region><FileName>r2_22222222-2222-2222-2222-222222222222.png</FileName></GameImage>
    <GameImage><DatabaseID>5</DatabaseID><Type>Box - Back</Type><Region>North America</Region><FileName>r2_33333333-3333-3333-3333-333333333333.jpg</FileName></GameImage>
    <GameImage><DatabaseID>5</DatabaseID><Type>Box - Spine</Type><Region>North America</Region><FileName>r2_77777777-7777-7777-7777-777777777777.jpg</FileName></GameImage>
    <GameImage><DatabaseID>5</DatabaseID><Type>Fanart - Background</Type><Region>World</Region><FileName>r2_aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa.png</FileName></GameImage>
    <GameImage><DatabaseID>5</DatabaseID><Type>Square</Type><Region>World</Region><FileName>r2_cccccccc-cccc-cccc-cccc-cccccccccccc.png</FileName></GameImage>
    <GameImage><DatabaseID>3</DatabaseID><Type>Box - Back</Type><FileName>55555555-5555-5555-5555-555555555555.jpg</FileName></GameImage>
    <GameImage><DatabaseID>4</DatabaseID><Type>Box - Back</Type><FileName>66666666-6666-6666-6666-666666666666.jpg</FileName></GameImage>
    <GameAlternateName><DatabaseID>1</DatabaseID><AlternateName>Example Voyage</AlternateName></GameAlternateName>
    </LaunchBox>"""
    result = parse(io.BytesIO(sample.encode()))
    assert "ns1:example journey\t" in result and "eu:22222222" in result
    assert "world:11111111" in result
    assert "ns1:example voyage\t" in result and "eu:22222222" in result
    assert "fr:33333333-3333-3333-3333-333333333333.jpg" in result
    assert "ns1:ambiguous\t" not in result
    assert "alt:ns1:example journey\t-\tother:44444444" in result
    assert "ns2:example next gen\t" in result
    ns2 = next(row.split("\t") for row in result.splitlines()
               if row.startswith("ns2:example next gen\t"))
    assert ns2[1].startswith("eu:r2_22222222"), ns2
    assert ns2[2].startswith("us:r2_33333333"), ns2
    assert ns2[3].startswith("us:r2_77777777"), ns2
    assert ns2[4].startswith("world:r2_aaaaaaaa"), ns2
    assert ns2[9].startswith("world:r2_cccccccc"), ns2
    assert "eu:77777777-7777-7777-7777-777777777777.png" in result
    fields = next(row.split("\t") for row in result.splitlines()
                  if row.startswith("ns1:example journey\t"))
    assert len(fields) == 12, fields
    assert fields[4].startswith("world:aaaaaaaa"), fields
    assert fields[5].startswith("world:bbbbbbbb"), fields
    assert fields[6].startswith("world:88888888"), fields
    assert "99999999" in fields[7], fields
    assert "Box - 3D" not in result
    # Index zero is authoritative; other-platform fronts are never emitted.
    extra = """<LaunchBox>
    <Game><DatabaseID>1</DatabaseID><Platform>Nintendo Switch</Platform><Name>Cross</Name></Game>
    <Game><DatabaseID>2</DatabaseID><Platform>Windows</Platform><Name>Cross</Name></Game>
    <GameImage><DatabaseID>1</DatabaseID><Type>Fanart - Background</Type><Region>Japan</Region><FileName>aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa.jpg</FileName></GameImage>
    <GameImage><DatabaseID>1</DatabaseID><Type>Fanart - Background</Type><Region>France</Region><FileName>bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb.jpg</FileName></GameImage>
    <GameImage><DatabaseID>1</DatabaseID><Type>Clear Logo</Type><FileName>cccccccc-cccc-cccc-cccc-cccccccccccc.png</FileName></GameImage>
    <GameImage><DatabaseID>2</DatabaseID><Type>Square</Type><FileName>dddddddd-dddd-dddd-dddd-dddddddddddd.png</FileName></GameImage>
    <GameImage><DatabaseID>2</DatabaseID><Type>Box - Front</Type><FileName>eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee.png</FileName></GameImage>
    <GameImage><DatabaseID>2</DatabaseID><Type>Box - Back</Type><FileName>ffffffff-ffff-ffff-ffff-ffffffffffff.jpg</FileName></GameImage>
    <GameImage><DatabaseID>2</DatabaseID><Type>Banner</Type><FileName>11111111-1111-1111-1111-111111111111.png</FileName></GameImage>
    </LaunchBox>"""
    cross = {line.split("\t")[0]: line.split("\t")[1:] for line in
             parse(io.BytesIO(extra.encode())).splitlines() if not line.startswith("#")}
    assert cross["ns1:cross"][3].startswith("jp:aaaaaaaa")
    assert "bbbbbbbb" not in cross["ns1:cross"][3]
    assert "cccccccc" in cross["ns1:cross"][9]
    alt = cross["alt:ns1:cross"]
    assert alt[0] == "-" and "ffffffff" in alt[1]
    assert "dddddddd" in alt[8] and "11111111" in alt[10]
    assert candidates([(7, "f" * 36 + ".jpg"), (1, "0" * 36 + ".png")]).count(";") == 1
    assert candidates([(1, "a" * 36 + ".jpg")]) == "a" * 36 + ".jpg"
    assert rank("France") > rank("Europe") > rank("World") > rank("Japan")
    assert regional_candidates([("eu", EUROPE_FRONT_PINS["79189"][0]),
                                ("us", "0" * 36 + ".jpg")]).startswith(
        "eu:9524e5f7-ccc8-4ce6-a581-03f82c51825e.jpg")
    assert "us:" in regional_candidates([("eu", EUROPE_FRONT_PINS["79189"][0]),
                                         ("us", "0" * 36 + ".jpg")])
    assert normalize("EA SPORTS FC 27!") == "ea sports fc 27"
    edition_xml = """<LaunchBox>
        <Game><DatabaseID>392130</DatabaseID><Platform>Nintendo Switch</Platform><Name>Pokémon Legends: Z-A</Name></Game>
        <Game><DatabaseID>424055</DatabaseID><Platform>Nintendo Switch 2</Platform><Name>Pokémon Legends: Z-A: Nintendo Switch 2 Edition</Name></Game>
        <GameImage><DatabaseID>392130</DatabaseID><Type>Box - Back</Type><Region>Europe</Region><FileName>aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa.jpg</FileName></GameImage>
        <GameImage><DatabaseID>424055</DatabaseID><Type>Box - Front</Type><Region>Germany</Region><FileName>bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb.jpg</FileName></GameImage>
    </LaunchBox>"""
    edition = parse(io.BytesIO(edition_xml.encode()))
    assert "ns1:pokemon legends z a\t" in edition, edition
    assert "ns1:pok mon legends z a\t" in edition, edition
    assert "ns2:pokemon legends z a\t" in edition, edition
    assert "ns2:pokemon legends z a nintendo switch 2 edition\t" in edition, edition
    assert "eu:aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa.jpg" in edition
    assert "de:bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb.jpg" in edition
    standard_xml = """<LaunchBox>
        <Game><DatabaseID>11</DatabaseID><Platform>Nintendo Switch 2</Platform><Name>Example Quest - Switch 2 Edition</Name></Game>
        <Game><DatabaseID>12</DatabaseID><Platform>Windows</Platform><Name>Example Quest</Name></Game>
        <Game><DatabaseID>13</DatabaseID><Platform>PlayStation 5</Platform><Name>Example Quest Deluxe</Name></Game>
        <GameAlternateName><DatabaseID>11</DatabaseID><AlternateName>Quête Exemple</AlternateName></GameAlternateName>
        <GameImage><DatabaseID>12</DatabaseID><Type>Box - Back</Type><FileName>aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa.jpg</FileName></GameImage>
        <GameImage><DatabaseID>13</DatabaseID><Type>Box - Back</Type><FileName>bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb.jpg</FileName></GameImage>
    </LaunchBox>"""
    standard = parse(io.BytesIO(standard_xml.encode()))
    for spelling in ("example quest", "example quest switch 2 edition", "quete exemple"):
        match = next(line for line in standard.splitlines()
                     if line.startswith(f"alt:ns2:{spelling}\\t".replace("\\t", "\t")))
        assert "aaaaaaaa" in match and "bbbbbbbb" not in match
    print("PASS standard title, Switch 2 Edition normalization, aliases and exact multiplatform identity")

def main():
    cli = argparse.ArgumentParser()
    cli.add_argument("--download", action="store_true")
    cli.add_argument("--zip", type=pathlib.Path)
    cli.add_argument("--output", type=pathlib.Path)
    cli.add_argument("--self-test", action="store_true")
    args = cli.parse_args()
    if args.self_test:
        self_test()
        return
    if not args.output:
        cli.error("--output is required")
    archive = args.zip or pathlib.Path("/tmp/encore-metadata.zip")
    if args.download:
        download(archive)
    result = build(archive)
    # The packaged index reports each actual LaunchBox media category, not
    # just the total number of matching Switch title names.
    rows = [row.split("\t") for row in result.splitlines()
            if row and not row.startswith("#")]
    coverage = tuple(sum(len(row) >= 10 and row[col] != "-"
                         for row in rows) for col in (4, 5, 6))
    # A successful metadata download containing only NS1 must not silently
    # become a production catalog for an NS1/NS2 application.
    ns2_rows = [row for row in rows if row[0].startswith("ns2:")]
    for column, role in ((1, "front"), (4, "fanart"), (9, "square")):
        if not any(len(row) == 12 and row[column] != "-" for row in ns2_rows):
            raise ValueError(f"GamesDB snapshot lacks NS2 {role} media")
    print("EDEN_CASE_INDEX_MEDIA fanart={} game_title={} gameplay={} titles={}".format(
        *coverage, len(rows)), flush=True)
    if result.count("\n") < 20:
        raise ValueError("No usable game data; index not installed")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    pending = args.output.with_suffix(".tmp")
    pending.write_text(result, encoding="utf-8")
    pending.replace(args.output)
    print(f"Retail case index: {result.count(chr(10)) - 1} names, {len(result)} bytes")

if __name__ == "__main__":
    main()
