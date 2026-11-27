#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Compile and execute the exact packaged NanoDNS-derived matcher contract."""
from pathlib import Path
import shutil
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
hosts = root / "headless/network-hosts.txt"
rules = [line.strip() for line in hosts.read_text().splitlines()
         if line.strip() and not line.lstrip().startswith("#")]
assert len(rules) == 233
assert len(rules) == len(set(rules))
for pattern in (
    "*playstation*", "*sony*", "*.psn.akadns99.net", "a192.d.akamai.net",
    "*nintendo*", "*.ea.com", "*.epicgames.com", "*.xboxlive.com",
    "steampowered.com", "*.steamcommunity.com", "*.gogcdn.net",
):
    assert pattern in rules, pattern
for retained_legacy in (
    "microsoft.com", "pokemon.com", "phoenix-api.wbagora.com",
    "scsi-upload-lp1.s3.us-west-2.amazonaws.com",
):
    assert retained_legacy in rules, retained_legacy

code = r"""
#include "network_domain_rules.h"
#include <assert.h>
#include <stdio.h>
static void yes(const char* name) { assert(eden_network_host_blocked(name) == 1); }
static void no(const char* name) { assert(eden_network_host_blocked(name) == 0); }
int main(int argc, char** argv) {
    assert(argc == 2);
    yes("api.github.com"); // fail closed before policy publication
    assert(eden_network_filter_load("/no/such/network-hosts.txt") != 0);
    yes("not-yet-initialized.example");
    assert(eden_network_filter_load(argv[1]) == 0);
    assert(eden_network_filter_count() == 233);

    yes("ps5.np.playstation.net");
    yes("telemetry-console.api.playstation.com");
    yes("sonyent.example");
    yes("atumn.hac.lp1.d4c.nintendo.net");
    yes("www.nintendoswitch.com");
    yes("accounts.epicgames.com");
    yes("telemetry.ea.com");
    yes("xsts.auth.xboxlive.com");
    yes("cdn.steamcommunity.com");
    yes("hub.gogcdn.net");
    yes("a192.d.akamai.net");

    no("github.com");
    no("raw.githubusercontent.com");
    no("youtube.com");
    yes("microsoft.com");
    yes("login.microsoft.com");
    yes("pokemon.com");
    yes("www.pokemon.com");
    yes("phoenix-api.wbagora.com");
    yes("scsi-upload-lp1.s3.us-west-2.amazonaws.com");
    no("other.s3.us-west-2.amazonaws.com");
    no("8.8.8.8");

    yes("broken..domain");
    yes(NULL);
    puts("PASS: exact 233-rule NanoDNS-derived hostname policy");
}
"""
c = shutil.which("clang") or shutil.which("cc")
assert c, "C compiler is required"
with tempfile.TemporaryDirectory(prefix="encore-network-hosts-") as directory:
    tmp = Path(directory)
    source = tmp / "policy.c"
    source.write_text(code)
    exe = tmp / "policy"
    subprocess.run([
        c, "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
        "-I" + str(root / "headless"),
        str(root / "headless/network_domain_rules.c"),
        str(source), "-o", str(exe),
    ], check=True)
    subprocess.run([str(exe), str(hosts)], check=True, timeout=10)
print("Host network policy: NanoDNS 233-rule projection compiled and passed")
