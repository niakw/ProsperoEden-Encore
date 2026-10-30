#!/usr/bin/env python3
"""Static source-owner guard for research NS2 CMake overlays, not a native build."""
from __future__ import annotations
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
CMAKE = (ROOT / "headless/CMakeLists.txt").read_text(encoding="utf-8")
NS2 = ROOT / "headless/ns2/overrides/core"

def require(condition: bool, reason: str) -> None:
    if not condition:
        raise AssertionError(reason)

def main() -> int:
    try:
        require('option(EDEN_NS2_METADATA_EXPERIMENTAL' in CMAKE,
                "No metadata opt-in")
        require('option(EDEN_NS2_EXEFS_EXPERIMENTAL' in CMAKE,
                "No ExeFS opt-in")
        require('option(EDEN_NS2_CPU6_EXPERIMENTAL' in CMAKE,
                "No CPU6 opt-in")
        require('EDEN_NS2_CPU6_EXPERIMENTAL OR' in CMAKE,
                "Final release must reject CPU6 experiment")
        cpu6 = ROOT / "headless/ns2/cpu6"
        require("NUM_CPU_CORES = 6" in (cpu6 / "core/hardware_properties.h").read_text(),
                "Six-core hardware map missing")
        require("MAX_NUM_CPU_CORES = 6" in
                (cpu6 / "dynarmic/interface/exclusive_monitor.h").read_text(),
                "Six-slot Dynarmic exclusive monitor missing")
        require('EDEN_NS2_METADATA_EXPERIMENTAL=ON' in CMAKE,
                "ExeFS must require metadata opt-in")
        require('EDEN_NS2_METADATA_EXPERIMENTAL OR EDEN_NS2_EXEFS_EXPERIMENTAL' in CMAKE,
                "Final release must reject experimental selectors")
        selection = CMAKE.index("# Experimental ExeFS bridge must be selected AFTER")
        am_selection = CMAKE.index("# Research-only Switch 2 AM command 320.")
        release_gate = CMAKE.index("# Release gate: Vulkan/RADV")
        require(selection < am_selection < release_gate,
                "NS2 AM and ExeFS owners must be selected after maintained Encore owners")
        property_sets = [i for i in range(len(CMAKE)) if
                         CMAKE.startswith("set_property(TARGET core PROPERTY SOURCES", i)]
        require(sum(i > selection for i in property_sets) == 2,
                "Unexpected source owner after ExeFS (expected ExeFS and AM only)")
        require('EDEN_NS2_A64_EXPERIMENTAL OR EDEN_NS2_AM_EXPERIMENTAL OR' in CMAKE,
                "Final release must reject NS2 application-manager experiment")
        require('option(EDEN_NS2_AM_EXPERIMENTAL' in CMAKE and
                'if(NOT EDEN_NS2_METADATA_EXPERIMENTAL)' in CMAKE[am_selection:release_gate] and
                'list(FIND eden_ns2_am_sources "${EDEN_APP_FUNCTION_SOURCE}"' in CMAKE,
                "NS2 application manager must require metadata and maintained source owner")
        am_root = ROOT / "headless/ns2/am/core/hle/service/am/service"
        am_impl = (am_root / "application_functions.cpp").read_text()
        am_header = (am_root / "application_functions.h").read_text()
        require("GetScreenShotAndContinuousRecordingInitiallyEnabled" in am_impl and
                "GetScreenShotAndContinuousRecordingInitiallyEnabled" in am_header,
                "AM 320 declaration/handler missing")
        require("GetTitleID" in am_impl,
                "Maintained Encore application metadata behavior lost")
        require('eden_ns2_loader_origin' in CMAKE and
                'eden_ns2_romdir_origin' in CMAKE and
                'list(FIND eden_ns2_exefs_sources "${eden_ns2_original}"' in CMAKE,
                "No version-aware source ownership check")
        loader = (NS2 / "loader/loader.cpp").read_text(encoding="utf-8")
        romdir = (NS2 / "loader/deconstructed_rom_directory.cpp").read_text(encoding="utf-8")
        header = (NS2 / "loader/deconstructed_rom_directory.h").read_text(encoding="utf-8")
        require('extension == "nsz"' in loader and 'extension == "xcz"' in loader,
                "NCZ/NSZ/XCZ loader behavior lost")
        require('<< 14) & 0xffc000' in romdir,
                "16-KiB-aligned Encore ASLR offset lost")
        require('!metadata.UsesExtendedAcid()' in romdir,
                "Extended ACID Dynarmic path guard lost")
        require('bool standalone{true}' in header,
                "Standalone ExeFS state missing")
        require(loader.index('IdentifyFileLoader<AppLoader_DeconstructedRomDirectory>')
                < loader.index('IdentifyFileLoader<AppLoader_NSO>'),
                "ExeFS identification is after generic NSO")
        print("NS2 research source owner / ExeFS safety guards: PASS")
    except (AssertionError, ValueError, OSError) as exc:
        print(f"NS2 source selection check FAILED: {exc}", file=sys.stderr)
        return 1
    print("NOTE: static selection proof only; no complete PS5 CMake configure/compile")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
