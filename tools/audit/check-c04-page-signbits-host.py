#!/usr/bin/env python3
"""Pinned, READ-ONLY C04/A32 page-table sign contract, host only."""
from pathlib import Path
import hashlib
import subprocess
import tempfile

root = Path(__file__).resolve().parents[2]
sources = {
    "sources/eden/src/common/page_table.h": "1588eca6168bdcaf04229d6aa4115c3acb624081",
    "encore-active/eden-core/src/dynarmic/backend/x64/emit_x64_memory.h": "c34906cc34a7b9576025520f1eb7f6416543ef33",
}
for name, digest in sources.items():
    data = (root / "vendor" / name).read_bytes()
    h = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\\0" + data).hexdigest()
    assert h == digest, (name, h)

page = (root / "vendor/sources/eden/src/common/page_table.h").read_text()
header = (root / "vendor/encore-active/eden-core/src/dynarmic/backend/x64/emit_x64_memory.h").read_text()
assert "SIGN_BIT = 45 + 12;" in page
assert "ATTRIBUTE_MASK = ((1ULL << 44) - 1) << 12" in page
assert header.count("code.shl(page, *ctx.conf.page_table_sign_extension);") == 3
assert "page_table_log2_stride <= 3" in header
diff_page = (root / "docs/audits/patchsets/C04-page-table-sign-bit55.vendor.patch").read_text()
diff_mem = (root / "docs/audits/patchsets/C04-a32-page-sign-extension.vendor.patch").read_text()
assert diff_page.count("+    static constexpr u64 SIGN_BIT = 44 + 12 - 1;") == 1
assert diff_mem.count("+        code.shl(page, 63 - int(*ctx.conf.page_table_sign_extension));") == 1
assert diff_mem.count("+        code.sar(page, 63 - int(*ctx.conf.page_table_sign_extension));") == 1
assert "return page + tmp.cvt64();" in diff_mem

cpp = r"""
#include <cassert>
#include <cstdint>
constexpr std::uint64_t mask = ((1ULL << 44) - 1) << 12;
constexpr unsigned sign_bit = 44 + 12 - 1;
static_assert(sign_bit == 55);
static_assert(mask & (1ULL << sign_bit));
static_assert((mask & (1ULL << (sign_bit + 1))) == 0);
std::uint64_t Extend(const std::uint64_t x, unsigned bit) {
    const auto amt = 63u - bit;
    return static_cast<std::uint64_t>(static_cast<std::int64_t>(x << amt) >> amt);
}
int main() {
    assert(Extend(0x007fffffffffffffULL, sign_bit) == 0x007fffffffffffffULL);
    assert(Extend(0x0080000000000000ULL, sign_bit) == 0xff80000000000000ULL);
    assert(Extend(0x0080000000000000ULL, 57) != 0xff80000000000000ULL);
    assert(Extend(0, sign_bit) == 0);
}
"""
with tempfile.TemporaryDirectory(prefix="c04-sign-") as td:
    f = Path(td) / "test.cpp"
    exe = Path(td) / "test"
    f.write_text(cpp)
    subprocess.run(["clang++", "-std=c++20", "-O1", "-g",
                    "-fsanitize=address,undefined", "-fno-omit-frame-pointer",
                    str(f), "-o", str(exe)], check=True)
    subprocess.run([str(exe)], check=True)
print("C04_A32_SELECTED_HEADER_BIT55_SIGNEXT_HOST_PASS original_vendor_unchanged=1")
