// SPDX-License-Identifier: GPL-3.0-or-later
// One-shot host smoke: the portable libwebp used in PPSA99008 round-trips
// a real cover with RGBA pixels and preserves alpha without crashing.
#include <webp/decode.h>
#include <webp/encode.h>
#include <cassert>
#include <cstdio>
#include <cstdint>
#include <vector>
#include <string>
#include <algorithm>
int main(int argc, char** argv) {
    if (argc != 2) return 2;
    std::FILE* f = std::fopen(argv[1], "rb");
    if (!f) return 3;
    std::fseek(f, 0, SEEK_END);
    const long size = std::ftell(f);
    assert(size > 30 && size < 16*1024*1024);
    std::rewind(f);
    std::vector<std::uint8_t> data(static_cast<std::size_t>(size));
    const auto n = std::fread(data.data(), 1, data.size(), f);
    std::fclose(f);
    assert(n == data.size());
    int width = 0, height = 0;
    std::uint8_t* rgba = nullptr;
    std::vector<std::uint8_t> decoded;
    if (std::string(argv[1]).ends_with(".tga")) {
        // Matches the trusted, Encore-generated 32-bit BGRA, top-left TGA.
        assert(data.size() >= 18 && data[0] == 0 && data[1] == 0 &&
               data[2] == 2 && data[16] == 32 && data[17] == 0x28);
        width = data[12] | (data[13] << 8);
        height = data[14] | (data[15] << 8);
        assert(width > 0 && height > 0 && width <= 4096 && height <= 2160);
        assert(data.size() == 18u + static_cast<std::size_t>(width) * height * 4);
        std::uint8_t* compressed_bgra = nullptr;
        const auto encoded_bgra = WebPEncodeBGRA(
            data.data() + 18, width, height, width * 4, 80.0f, &compressed_bgra);
        assert(encoded_bgra && compressed_bgra);
        rgba = WebPDecodeRGBA(compressed_bgra, encoded_bgra, &width, &height);
        WebPFree(compressed_bgra);
    } else {
        assert(WebPGetInfo(data.data(), data.size(), &width, &height));
        assert(width > 0 && height > 0 && width <= 4096 && height <= 4096);
        rgba = WebPDecodeRGBA(data.data(), data.size(), &width, &height);
    }
    assert(rgba);
    std::uint8_t* compressed = nullptr;
    const auto bytes = WebPEncodeRGBA(rgba, width, height, width * 4, 80.0f, &compressed);
    assert(bytes && compressed);
    int w2=0,h2=0;
    assert(WebPGetInfo(compressed, bytes, &w2, &h2) && w2==width && h2==height);
    std::uint8_t* roundtrip = WebPDecodeRGBA(compressed, bytes, &w2, &h2);
    assert(roundtrip);
    // Both encodes must preserve transparency; RGB may be lossy at q80.
    const auto pixel_count = static_cast<std::size_t>(width) * height;
    for (std::size_t i = 0; i < pixel_count; ++i)
        assert(roundtrip[i * 4 + 3] == rgba[i * 4 + 3]);
    WebPFree(roundtrip);
    // Truncated picture data can still have a valid RIFF header; it must not
    // produce a decoded buffer or be mistaken for a complete cached image.
    std::uint8_t* invalid = WebPDecodeRGBA(compressed, bytes / 2, &w2, &h2);
    assert(invalid == nullptr);
    WebPFree(compressed);
    WebPFree(rgba);
    std::printf("PASS webp host decoder/encoder %dx%d input=%zu output=%zu\n",
        width,height,data.size(),bytes);
}
