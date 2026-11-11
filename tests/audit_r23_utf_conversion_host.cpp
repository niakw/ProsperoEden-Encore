// SPDX-License-Identifier: GPL-3.0-or-later
// R23 #29: source-extracted algorithm-only contrast, NOT a linked emulator unit.
// Original: vendor/sources/eden/src/common/string_util.cpp @ 9543a623...
// Upstream: eden-emulator/mirror c6fa5c1f77...
#include <cassert>
#include <codecvt>
#include <cstdint>
#include <iostream>
#include <locale>
#include <stdexcept>
#include <string>
#include <string_view>

std::u16string PinnedUtf8ToUtf16(std::string_view input) {
    std::wstring_convert<std::codecvt_utf8_utf16<char16_t>, char16_t> convert;
    return convert.from_bytes(input.data(), input.data() + input.size());
}

std::u16string UpstreamUtf8ToUtf16(std::string_view input) {
    std::u16string result;
    result.reserve(input.size() * 2);
    for (size_t i = 0; i < input.size(); ) {
        uint32_t code = 0;
        unsigned char c = input[i];
        size_t len = 0;
        if ((c & 0x80) == 0) {
            code = c;
            len = 1;
        } else if ((c & 0xE0) == 0xC0) {
            code = c & 0x1F;
            len = 2;
        } else if ((c & 0xF0) == 0xE0) {
            code = c & 0x0F;
            len = 3;
        } else if ((c & 0xF8) == 0xF0) {
            code = c & 0x07;
            len = 4;
        } else {
            ++i;
            continue;
        }
        if (i + len - 1 >= input.size())
            break;
        for (size_t j = 1; j <= len - 1; ++j) {
            if ((input[i + j] & 0xC0) != 0x80) {
                code = 0xFFFD;
                break;
            }
            code = (code << 6) | (input[i + j] & 0x3F);
        }
        if (code <= 0xFFFF) {
            result.push_back(char16_t(code));
        } else {
            code -= 0x10000;
            result.push_back(char16_t(0xD800 + (code >> 10)));
            result.push_back(char16_t(0xDC00 + (code & 0x3FF)));
        }
        i += len;
    }
    return result;
}

int main() {
    const std::string valid{"\xE2\x82\xAC\xF0\x9F\x98\x80", 7};
    assert(PinnedUtf8ToUtf16(valid) == UpstreamUtf8ToUtf16(valid));
    assert(PinnedUtf8ToUtf16("Hello") == UpstreamUtf8ToUtf16("Hello"));
    const std::string overlong_nul{"\xC0\x80", 2};
    bool pinned_rejected = false;
    try {
        (void)PinnedUtf8ToUtf16(overlong_nul);
    } catch (const std::range_error&) {
        pinned_rejected = true;
    }
    const auto upstream = UpstreamUtf8ToUtf16(overlong_nul);
    assert(pinned_rejected);
    assert(upstream.size() == 1 && upstream[0] == 0);
    std::cout << "R23_UTF_EXTRACTED_HOST_DIVERGENCE_PASS overlong_nul valid_unicode\n";
}
