#!/usr/bin/env python3
"""Validate installable Eden Encore ZIP member roots without unpacking them.

The canonical distribution ZIP additionally carries legal/readme files at its
root; the dedicated FTP ZIP MUST carry only PPSA99008/ runtime paths.
"""
import argparse
import io
import json
import pathlib
import re
import zipfile

TITLE = "PPSA99008"
REQUIRED = {f"{TITLE}/eboot.bin", f"{TITLE}/sce_sys/param.json"}
# Match the exact filename emitted by make-dist.py/resolve-encore-release.py.
# Never silently accept an old/foreign title or a different R revision.
FTP_NAME = re.compile(r"Eden-Encore-(R[1-9][0-9]{0,5})-([0-9a-f]{8})-FTP-PPSA99008[.]zip")
FULL_NAME = re.compile(r"Prospero[.]Eden-Encore-(R[1-9][0-9]{0,5})[.]zip")
LEGACY_FTP_NAME = "Eden-Encore-56293953-FTP-PPSA99008.zip"


def select_archives(paths: list[pathlib.Path]) -> tuple[pathlib.Path, pathlib.Path]:
    """Require one matching full+FTP distribution pair with consistent R."""
    ftp = sorted(path for path in paths if FTP_NAME.fullmatch(path.name)
                 or path.name == LEGACY_FTP_NAME)
    full = sorted(path for path in paths if FULL_NAME.fullmatch(path.name))
    if len(ftp) != 1 or len(full) != 1:
        raise ValueError(f"Expected one FTP and one full ZIP: {ftp}, {full}")
    full_revision = FULL_NAME.fullmatch(full[0].name).group(1)
    match = FTP_NAME.fullmatch(ftp[0].name)
    if match:
        if match.group(1) != full_revision:
            raise ValueError(f"FTP/full R revision mismatch: {ftp[0].name}, {full[0].name}")
    elif full_revision != "R1":
        raise ValueError("Legacy FTP file only allowed for the original R1 release")
    return ftp[0], full[0]


def inspect(blob: bytes, ftp_only: bool) -> int:
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        names = z.namelist()
        assert len(names) == len(set(names)), "Duplicate archive entries"
        files = {name for name in names if not name.endswith("/")}
        assert REQUIRED <= files, f"Missing {REQUIRED-files}"
        assert "eboot.bin" not in files, "Flattened title directory"
        assert f"{TITLE}/{TITLE}/eboot.bin" not in files, "Nested title directory"
        assert all(not name.startswith("/") and "\\" not in name and
                   not {"", ".", ".."} & set(pathlib.PurePosixPath(name).parts)
                   for name in names), "Unsafe archive member path"
        if ftp_only:
            assert all(name.startswith(f"{TITLE}/") for name in names), "FTP archive has extra root content"
            assert not any(name.lower().endswith(".zip") for name in names), "Nested zip prohibited"
        param = json.loads(z.read(f"{TITLE}/sce_sys/param.json"))
        assert param["titleId"] == TITLE, "PS5 metadata title differs from folder"
        assert z.getinfo(f"{TITLE}/eboot.bin").file_size > 0, "Missing binary payload"
        return len(files)


def self_test() -> None:
    def build(prefix: str, extra: bool = False):
        output = io.BytesIO()
        with zipfile.ZipFile(output, "w") as z:
            z.writestr(prefix+"eboot.bin", b"\x7fELF")
            z.writestr(prefix+"sce_sys/param.json", '{"titleId":"PPSA99008"}')
            if extra:
                z.writestr("README.md", "full release docs")
        return output.getvalue()
    assert inspect(build("PPSA99008/"), True) == 2
    assert inspect(build("PPSA99008/", True), False) == 3
    for bad in ["", "PPSA99008/PPSA99008/", "WrongFolder/"]:
        try:
            inspect(build(bad), True)
        except AssertionError:
            pass
        else:
            raise AssertionError(f"Incorrect ZIP root accepted: {bad!r}")
    try:
        inspect(build("PPSA99008/", True), True)
    except AssertionError:
        pass
    else:
        raise AssertionError("Unrelated root-level file in FTP ZIP was accepted")
    # Historical naming drift caused a false-negative after signed stage.
    good = [pathlib.Path("Prospero.Eden-Encore-R457.zip"),
            pathlib.Path("Eden-Encore-R457-2c75956d-FTP-PPSA99008.zip")]
    assert select_archives(good) == (good[1], good[0])
    assert select_archives([pathlib.Path("Prospero.Eden-Encore-R1.zip"),
                            pathlib.Path(LEGACY_FTP_NAME)])[0].name == LEGACY_FTP_NAME
    for wrong in (
        [pathlib.Path("Prospero.Eden-Encore-R456.zip"), good[1]],
        [good[0], pathlib.Path("Prospero.Eden-Encore-R457-2c75956d-FTP.zip")],
        [good[0], pathlib.Path("Eden-Encore-R458-2c75956d-FTP-PPSA99008.zip")],
        [good[0], pathlib.Path("Eden-Encore-R457-2c75956d-FTP-WRONG.zip")],
        [good[0], good[1], pathlib.Path("Eden-Encore-R457-ffffffff-FTP-PPSA99008.zip")],
    ):
        try:
            select_archives(wrong)
        except ValueError:
            pass
        else:
            raise AssertionError(f"Mismatched distribution filenames accepted: {wrong}")
    print("ENCORE_PPSA99008_ZIP_LAYOUT_HOST_PASS flat=reject nested=reject extra=reject")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dist", nargs="?", type=pathlib.Path)
    parser.add_argument("--self-test", action="store_true")
    opts = parser.parse_args()
    if opts.self_test:
        self_test()
        return
    if opts.dist is None:
        parser.error("provide dist folder or --self-test")
    try:
        ftp_file, full_file = select_archives(list(opts.dist.glob("*.zip")))
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    print(f"ENCORE_FTP_ZIP_ROOT_OK PPSA99008/ files={inspect(ftp_file.read_bytes(), True)}")
    print(f"ENCORE_FULL_ZIP_ROOT_OK PPSA99008/ files={inspect(full_file.read_bytes(), False)}")


if __name__ == "__main__":
    main()
