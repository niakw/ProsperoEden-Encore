#!/usr/bin/env python3
"""Build deterministic, bounded Noto fallbacks from the active launcher catalogs.

The original fonts are fetched from one pinned google/fonts commit and verified
by their Git blob SHA-1 before any processing. Only Unicode characters used by
the seven active non-Montserrat catalogues are retained. GSUB/GPOS closure is
kept by fontTools so Arabic/Thai/CJK shaping remains valid.
"""
from __future__ import annotations
import argparse, hashlib, io, json, runpy, urllib.parse, urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
SPEC_PATH=ROOT/"tools/launcher/noto_fallbacks.json"
CATALOGS=ROOT/"headless/prosperoeden/ui/lang"
DEFAULT_OUT=ROOT/"build/generated/noto-fallback"

def git_blob(data: bytes) -> str:
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()

def fetch(repo: str, commit: str, path: str) -> bytes:
    encoded=urllib.parse.quote(path,safe="/")
    url=f"https://raw.githubusercontent.com/{repo}/{commit}/{encoded}"
    request=urllib.request.Request(url,headers={"User-Agent":"Eden-Encore-font-subsetter/1"})
    with urllib.request.urlopen(request,timeout=30) as response:
        data=response.read(24*1024*1024+1)
    if len(data)>24*1024*1024:
        raise RuntimeError(f"font source too large: {path}")
    return data

def catalog_codepoints(locales: list[str]) -> set[int]:
    module=runpy.run_path(str(ROOT/"tools/launcher/strings.py"))
    parse_po=module["parse_po"]
    # The in-game menu composes localized labels with language-neutral Vulkan/AA/FPS values.
    # Keep printable ASCII in every fallback so a whole mixed row can be shaped by one face.
    codepoints=set(range(0x20,0x7f)) | {0x00A0,0xFFFD}
    for locale in locales:
        path=CATALOGS/f"{locale}.po"
        entries=parse_po(path)
        if not entries:
            raise RuntimeError(f"empty catalog: {path}")
        for value in entries.values():
            for char in value:
                if char not in "\r\n":
                    codepoints.add(ord(char))
    # HarfBuzz consumes these controls during shaping; keep them if a catalog
    # starts using them even when they render no outline.
    codepoints.update({0x200B,0x200C,0x200D,0x200E,0x200F,0x061C})
    return codepoints

def subset_font(data: bytes, codepoints: set[int], axes: dict[str,float]) -> bytes:
    try:
        from fontTools.ttLib import TTFont
        from fontTools.varLib.instancer import instantiateVariableFont
        from fontTools.subset import Options, Subsetter
    except ImportError as exc:
        raise SystemExit("fontTools is required (Ubuntu: python3-fonttools)") from exc
    font=TTFont(io.BytesIO(data),recalcBBoxes=False,recalcTimestamp=False,lazy=False)
    if "fvar" in font and axes:
        font=instantiateVariableFont(font,axes,inplace=False,optimize=True)
    options=Options()
    options.layout_features=["*"]
    options.name_IDs=["*"]
    options.name_languages=["*"]
    options.recalc_timestamp=False
    options.notdef_glyph=True
    options.notdef_outline=True
    options.recommended_glyphs=True
    options.prune_unicode_ranges=True
    subsetter=Subsetter(options=options)
    subsetter.populate(unicodes=codepoints)
    subsetter.subset(font)
    output=io.BytesIO()
    font.save(output,reorderTables=True)
    return output.getvalue()

def cmap(data: bytes) -> set[int]:
    from fontTools.ttLib import TTFont
    font=TTFont(io.BytesIO(data),lazy=True)
    chars=set()
    for table in font["cmap"].tables:
        if table.isUnicode():
            chars.update(table.cmap)
    return chars

def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,default=DEFAULT_OUT)
    parser.add_argument("--offline-source",type=Path,
                        help="optional directory containing already downloaded source fonts")
    args=parser.parse_args()
    spec=json.loads(SPEC_PATH.read_text())
    out=args.output
    out.mkdir(parents=True,exist_ok=True)
    receipts=[]
    total=0
    for item in spec["fonts"]:
        source_name=Path(item["source"]).name
        if args.offline_source:
            data=(args.offline_source/source_name).read_bytes()
        else:
            data=fetch(spec["source_repository"],spec["source_commit"],item["source"])
        actual_blob=git_blob(data)
        if actual_blob!=item["git_blob"]:
            raise RuntimeError(f"{item['id']}: source blob {actual_blob} != {item['git_blob']}")
        required=catalog_codepoints(item["locales"])
        built=subset_font(data,required,item.get("axes",{}))
        covered=cmap(built)
        missing=sorted(required-covered)
        if missing:
            raise RuntimeError(f"{item['id']}: subset misses "+",".join(f"U+{c:04X}" for c in missing[:20]))
        target=out/item["output"]
        target.write_bytes(built)
        total+=len(built)
        receipts.append({
            "id":item["id"],"file":item["output"],"locales":item["locales"],
            "source_git_blob":actual_blob,"source_bytes":len(data),
            "subset_bytes":len(built),"subset_sha256":hashlib.sha256(built).hexdigest(),
            "required_codepoints":len(required),
        })
        print(f"NOTO_SUBSET_PASS id={item['id']} locales={','.join(item['locales'])} "
              f"codepoints={len(required)} bytes={len(built)}")
    if total>int(spec["max_total_bytes"]):
        raise RuntimeError(f"Noto fallback budget exceeded: {total} > {spec['max_total_bytes']}")
    receipt={
        "schema":1,"source_repository":spec["source_repository"],
        "source_commit":spec["source_commit"],"total_bytes":total,
        "max_total_bytes":spec["max_total_bytes"],"fonts":receipts,
    }
    (out/"receipt.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(f"NOTO_FALLBACKS_PASS fonts={len(receipts)} total_bytes={total} "
          f"budget={spec['max_total_bytes']}")

if __name__=="__main__":
    main()
