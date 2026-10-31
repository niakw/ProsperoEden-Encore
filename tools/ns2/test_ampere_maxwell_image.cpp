// SPDX-License-Identifier: GPL-3.0-or-later
// Maxwell guest-environment image ABI tests (real Ampere lowerer underneath).
#include <array>
#include <cstdio>
#include <cstdlib>
#include <vector>
#include "shader_recompiler/frontend/ampere/maxwell_image.h"
#include "shader_recompiler/frontend/ampere/program_address_map.h"
using namespace Shader::Ampere;

static void require(bool ok, const char* why) {
    if (!ok) {
        std::fprintf(stderr, "NS2 Maxwell image FAIL: %s\n", why);
        std::exit(1);
    }
}
static void Emit(std::vector<u8>& dest, u32 a, u32 b=0, u32 c=0, u32 d=0) {
    for (const u32 word : {a,b,c,d})
        for (u32 shift=0; shift!=32; shift+=8)
            dest.push_back(static_cast<u8>(word >> shift));
}
int main() {
    constexpr u32 pt = 7U << 12;
    constexpr u32 unconditional = 7U << 23;
    std::array<u8,0x50> header{};
    header[0] = 0x38;
    std::vector<u8> code;
    Emit(code,pt|0x918);                         // NOP
    Emit(code,pt|0x202|(1U<<16),2,15U<<8);      // MOV R1,R2
    Emit(code,pt|0x918);                         // NOP
    Emit(code,pt|0x918);                         // NOP
    Emit(code,pt|0x94d,0,unconditional);        // EXIT

    auto image = BuildMaxwellShaderImage(header,code,4);
    require(image.Ready() && image.ValidForCompiler() &&
            image.native_stage == 4 && image.lowering_status == LowerBridgeStatus::Ready,
            "real NOP/MOV/EXIT lowering and Maxwell image created");
    require(image.code.size() > 0x50/8 &&
            image.code[0] == 0x38 &&
            image.code[1] == 0,
            "preserve 0x50 byte guest Maxwell shader header");
    require(image.first_instruction_address == 0x50 &&
            image.instruction_end_address <= image.cached_highest_address,
            "respect Maxwell initial offset and valid cached extent");
    require(HasNativeAddressMap(image.code) &&
            image.TranslateNativeAddress(0).has_value() &&
            *image.TranslateNativeAddress(0) == 0x50,
            "native instruction zero maps after 0x50 header");
    require(image.TranslateNativeAddress(16).has_value() &&
            *image.TranslateNativeAddress(16) == 0x58,
            "second native program address resolves without scheduler word");
    require(image.TranslateNativeAddress(32).has_value() &&
            *image.TranslateNativeAddress(32) == 0x68,
            "third native address jumps over scheduler word at 0x60");
    for (u32 native = 0; native < image.consumed_native_bytes; native += 16) {
        const auto absolute = image.TranslateNativeAddress(native);
        require(absolute.has_value() && image.ReadMaxwellInstruction(*absolute).has_value(),
                "each native instruction address corresponds to executable Maxwell word");
        require(*absolute < image.instruction_end_address && *absolute >= 0x50 &&
                *absolute % 32 != 0, "address map never references schedule words or metadata");
    }
    require(!image.ReadMaxwellInstruction(0x60) &&
            !image.ReadMaxwellInstruction(0) &&
            !image.ReadMaxwellInstruction(image.instruction_end_address) &&
            !image.TranslateNativeAddress(1) &&
            !image.TranslateNativeAddress(0xfffffff0),
            "invalid/unaligned/end addresses rejected before code access");

    auto corrupted=image;
    corrupted.code[corrupted.code.size()-2]=65536;
    require(!corrupted.ValidForCompiler(), "forged native address-map length rejected");
    corrupted=image;
    corrupted.code.back()=0;
    require(!corrupted.ValidForCompiler(), "missing map magic rejected");
    corrupted=image;
    corrupted.code[corrupted.code.size()-4]=corrupted.instruction_end_address;
    require(!corrupted.ValidForCompiler(), "map cannot target appended metadata");
    corrupted=image;
    corrupted.cached_highest_address+=8;
    require(!corrupted.ValidForCompiler(), "cached extent mismatch rejected");
    corrupted=image;
    corrupted.instruction_end_address=0xffffffffU;
    require(!corrupted.ValidForCompiler(), "forged instruction limit rejected");
    require(!corrupted.ReadMaxwellInstruction(0xfffffff8U),
            "untrusted instruction offset never reads beyond allocation");
    auto repeat=BuildMaxwellShaderImage(header,code,4);
    require(repeat.Ready() && repeat.code == image.code &&
            repeat.diagnostic_cache_key == image.diagnostic_cache_key,
            "same shader/header/stage yields bit-identical deterministic image");
    auto other_stage=BuildMaxwellShaderImage(header,code,5);
    require(other_stage.Ready() &&
            other_stage.diagnostic_cache_key != image.diagnostic_cache_key,
            "shader cache identity isolates native shader stages");
    header[0] ^= 1;
    auto other_header=BuildMaxwellShaderImage(header,code,4);
    require(other_header.Ready() &&
            other_header.diagnostic_cache_key != image.diagnostic_cache_key,
            "native shader identity depends on original guest header");
    header[0] ^= 1;
    std::array<u8,0x4f> truncated_header{};
    require(BuildMaxwellShaderImage(truncated_header,code,4).status ==
                MaxwellImageStatus::InvalidHeader,
            "must not reinterpret arbitrary guest header sizes");
    std::vector<u8> bad_source={0,1,2};
    const auto invalid=BuildMaxwellShaderImage(header,bad_source,4);
    require(invalid.status == MaxwellImageStatus::LoweringFailed &&
            invalid.code.empty() &&
            invalid.diagnostic_cache_key == 0,
            "rejected guest shader cannot poison or populate Maxwell cache");

    const std::array<u8,16> no_exit{0x18,0x79};
    const auto unsupported=BuildMaxwellShaderImage(header,no_exit,4);
    require(unsupported.status == MaxwellImageStatus::LoweringFailed &&
            unsupported.code.empty(),
            "missing EXIT is never represented as translated shader");
    require(!NativeProgramAddress(std::span<const u64>{},0),
            "empty shader code cannot resolve a native branch");
    std::puts("NS2 Ampere->Maxwell shader image: PASS (no PS5 GPU execution)");
}
