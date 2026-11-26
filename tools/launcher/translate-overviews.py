#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Synchronize selected-game synopsis requests via the existing private DeepL contract.

Only public text that exactly matches the generated LaunchBox index is sent.
No title ID, console address, library inventory or API key goes in the cache.
No key means no request. No bulk translation of the catalogue.
"""
import argparse
import ftplib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import urllib.request

REMOTE = "/data/prosperoeden/covers"
MAX_JSON = 8192
REQUEST = re.compile(r"synopsis-[0-9A-F]{16}-ns[12]-([A-Za-z]{2}(?:-[A-Za-z]{2,4})?)\.request\.json")
TARGETS = {
    "fr": "FR", "fr-CA": "FR", "de": "DE", "it": "IT", "es": "ES",
    "es-419": "ES", "pt": "PT-PT", "pt-BR": "PT-BR", "nl": "NL",
    "ru": "RU", "pl": "PL", "ja": "JA", "ko": "KO", "zh-Hans": "ZH-HANS",
    "zh-Hant": "ZH-HANT", "th": "TH", "ar": "AR", "cs-CZ": "CS",
    "da-DK": "DA", "el-GR": "EL", "fi-FI": "FI", "hu-HU": "HU",
    "id-ID": "ID", "nb-NO": "NB", "ro-RO": "RO", "sv-SE": "SV",
    "tr-TR": "TR", "uk-UA": "UK", "vi-VN": "VI",
}

def short_overview(text):
    compact = " ".join(text.split())
    excerpt = " ".join(re.split(r"(?<=[.!?])\s+", compact)[:3])
    if len(excerpt) > 360:
        prefix = excerpt[:360]
        boundary = prefix.rfind(" ")
        excerpt = prefix[:boundary] if boundary > 180 else prefix
    return excerpt

def public_overviews(index):
    result = {}
    for line in index.splitlines():
        if line.startswith("# synopsis\t"):
            fields = line.split("\t", 2)
            if len(fields) == 3 and fields[1].startswith(("ns1:", "ns2:")):
                result[fields[1]] = fields[2]
    return result

def read_json(client, path):
    try:
        size = client.size(path)
        if size is None or not 0 < size <= MAX_JSON:
            return {}
        data = bytearray()
        def receive(block):
            data.extend(block)
            if len(data) > MAX_JSON:
                raise ValueError("oversized synopsis cache")
        client.retrbinary("RETR " + path, receive)
        value = json.loads(data)
        return value if isinstance(value, dict) else {}
    except (ftplib.error_perm, OSError, ValueError, UnicodeError):
        return {}

def translate(text, target, key, fetch=urllib.request.urlopen):
    excerpt = short_overview(text)
    if not excerpt:
        return ""
    endpoint = ("https://api-free.deepl.com" if key.endswith(":fx")
                else "https://api.deepl.com") + "/v2/translate"
    req = urllib.request.Request(endpoint,
        data=json.dumps({"text": [excerpt], "target_lang": target,
                         "preserve_formatting": True}, ensure_ascii=False).encode(),
        method="POST", headers={"Authorization": "DeepL-Auth-Key " + key,
                                "Content-Type": "application/json",
                                "User-Agent": "EdenEncore-private-translation/1.0"})
    with fetch(req, timeout=25) as response:
        data = response.read(65537)
    if len(data) > 65536:
        return ""
    translations = json.loads(data).get("translations", [])
    if len(translations) != 1 or not isinstance(translations[0].get("text"), str):
        return ""
    return short_overview(translations[0]["text"])

def sync(client, index, key=None, fetch=urllib.request.urlopen):
    key = (os.environ.get("NIAK_DEEPL_API_KEY", "") if key is None else key).strip()
    if not key:
        return 0
    public = public_overviews(index)
    client.voidcmd("TYPE I")
    try:
        names = client.nlst(REMOTE)
    except ftplib.error_perm:
        return 0
    done = 0
    examined = 0
    for name in sorted(set(PurePosixPath(n).name for n in names)):
        match = REQUEST.fullmatch(name)
        if not match or match.group(1) not in TARGETS:
            continue
        examined += 1
        if examined > 100:
            break
        request_path = REMOTE + "/" + name
        request = read_json(client, request_path)
        source, identity, locale = (request.get(k) for k in ("source", "key", "locale"))
        if not isinstance(identity, str) or not isinstance(source, str) or not source:
            continue
        if locale != match.group(1) or public.get(identity) != source:
            continue
        output = request_path.removesuffix(".request.json") + ".json"
        cached = read_json(client, output)
        if all(cached.get(k) == request.get(k) for k in ("source", "key", "locale")) and cached.get("translation"):
            continue
        try:
            translated = translate(source, TARGETS[locale], key, fetch)
            if not translated:
                break
            payload = json.dumps({"source": source, "key": identity, "locale": locale,
                                  "translation": translated}, ensure_ascii=False).encode()
            if len(payload) > MAX_JSON:
                continue
            # Never remove the previous good cache to work around a failed rename.
            client.storbinary("STOR " + output + ".new", io.BytesIO(payload))
            client.rename(output + ".new", output)
            done += 1
        except (OSError, ValueError, KeyError, TypeError, ftplib.error_reply, ftplib.error_temp, ftplib.error_perm, ftplib.error_proto):
            break  # No automatic billing retry; preserve provider original.
    return done

def self_test():
    source = "First. Second! Third? Fourth."
    ident = "ns2:example quest"
    filename = "synopsis-0400000000001000-ns2-fr.request.json"
    request = {"source": source, "key": ident, "locale": "fr"}
    class FTP:
        def __init__(self):
            self.files = {REMOTE + "/" + filename: json.dumps(request).encode()}
        def voidcmd(self, command):
            pass
        def nlst(self, path):
            return list(self.files)
        def size(self, path):
            if path not in self.files:
                raise ftplib.error_perm("missing")
            return len(self.files[path])
        def retrbinary(self, command, receive):
            receive(self.files[command[5:]])
        def storbinary(self, command, data):
            self.files[command[5:]] = data.read()
        def rename(self, source, target):
            self.files[target] = self.files.pop(source)
    client = FTP()
    calls = []
    def fetch(req, timeout):
        data = json.loads(req.data)
        assert data == {"text": ["First. Second! Third?"], "target_lang": "FR",
                        "preserve_formatting": True}
        assert "0400000000001000" not in str(data)
        assert req.full_url == "https://api-free.deepl.com/v2/translate"
        calls.append(req)
        return io.BytesIO(json.dumps({"translations": [{"text": "Un résumé traduit."}]}).encode())
    index = "# synopsis\t" + ident + "\t" + source + "\n"
    assert sync(client, index, key="", fetch=fetch) == 0 and not calls
    assert sync(client, index, key="test:fx", fetch=fetch) == 1
    assert sync(client, index, key="test:fx", fetch=fetch) == 0 and len(calls) == 1
    request["source"] = "Untrusted console data"
    client.files[REMOTE + "/" + filename] = json.dumps(request).encode()
    assert sync(client, index, key="test:fx", fetch=fetch) == 0 and len(calls) == 1
    print("ENCORE_PRIVATE_SYNOPSIS_TRANSLATION_PASS")

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("host", nargs="?")
    parser.add_argument("--index", type=Path)
    parser.add_argument("--port", type=int, default=2121)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    if not args.host or not args.index:
        parser.error("host and --index are required")
    if not os.environ.get("NIAK_DEEPL_API_KEY", "").strip():
        print("No private translation key configured; original descriptions retained.")
        return
    with ftplib.FTP() as client:
        client.connect(args.host, args.port, timeout=60)
        client.login()
        count = sync(client, args.index.read_text(encoding="utf-8"))
    print(f"Translated and synchronized {count} requested descriptions.")

if __name__ == "__main__":
    main()
