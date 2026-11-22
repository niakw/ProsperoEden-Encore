// SPDX-License-Identifier: GPL-3.0-or-later
// Host-only NS1 validation: genuine Eden IR -> maintained SPIR-V image atomics.
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <string>
#include <string_view>
#include <vector>

#include <spirv/unified1/spirv.hpp>

#define CANNOT_EXPLICITLY_INSTANTIATE
#include "common/logging.h"
#include "common/settings.h"
#include "shader_recompiler/backend/spirv/emit_spirv.h"
#include "shader_recompiler/backend/bindings.h"
#include "shader_recompiler/frontend/ir/basic_block.h"
#include "shader_recompiler/frontend/ir/modifiers.h"
#include "shader_recompiler/frontend/ir/program.h"
#include "shader_recompiler/object_pool.h"
#include "shader_recompiler/profile.h"
#include "shader_recompiler/runtime_info.h"

namespace Settings {
Values values{};
}

void AssertFailSoftImpl() {
    std::fputs("NS1 image-atomic host AssertFailSoftImpl\n", stderr);
    std::abort();
}
void AssertFatalImpl() {
    std::fputs("NS1 image-atomic host AssertFatalImpl\n", stderr);
    std::abort();
}
namespace Common::Log {
void FmtLogMessageImpl(Class, Level, const char*, unsigned, const char*,
                       fmt::string_view message, const fmt::format_args&) {
    std::fprintf(stderr, "NS1 image-atomic host log: %.*s\n",
                 static_cast<int>(message.size()), message.data());
}
}

namespace {

using Shader::Backend::Bindings;
using Shader::Backend::SPIRV::EmitSPIRV;
using Shader::IR::AbstractSyntaxNode;
using Shader::IR::Block;
using Shader::IR::Inst;
using Shader::IR::Opcode;
using Shader::IR::Program;
using Shader::IR::TextureInstInfo;
using Shader::IR::Value;

[[noreturn]] void Fail(std::string_view why) {
    std::fprintf(stderr, "NS1_IMAGE_ATOMIC_REAL_SPIRV_FAIL: %.*s\n",
                 static_cast<int>(why.size()), why.data());
    std::exit(1);
}

void Require(bool value, std::string_view why) {
    if (!value) {
        Fail(why);
    }
}

std::size_t CountOp(const std::vector<u32>& words, spv::Op wanted) {
    Require(words.size() >= 5 && words[0] == 0x07230203U, "invalid SPIR-V module header");
    std::size_t result{};
    for (std::size_t pos = 5; pos < words.size();) {
        const u32 encoded = words[pos];
        const u32 count = encoded >> 16;
        Require(count != 0 && count <= words.size() - pos, "invalid SPIR-V instruction stream");
        if ((encoded & 0xffffU) == static_cast<u32>(wanted)) {
            ++result;
        }
        pos += count;
    }
    return result;
}

void WriteModule(const std::string& path, const std::vector<u32>& words) {
    std::ofstream output{path, std::ios::binary | std::ios::trunc};
    Require(bool(output), "cannot open SPIR-V output");
    output.write(reinterpret_cast<const char*>(words.data()),
                 static_cast<std::streamsize>(words.size() * sizeof(u32)));
    Require(bool(output), "cannot write SPIR-V output");
}

struct CompileCase {
    u32 descriptor_count{};
    bool dynamic_index{};
    bool nonuniform_supported{};
    u32 immediate_index{};
    const char* expected_rejection{};
    const char* output_path{};
};

std::vector<u32> Compile(const CompileCase& test) {
    Shader::ObjectPool<Inst> pool{32};
    Block block{pool};
    Program program{};
    program.stage = Shader::Stage::Compute;
    program.workgroup_size = {1, 1, 1};
    program.shared_memory_size = 64;
    program.blocks.push_back(&block);
    auto& node = program.syntax_list.emplace_back();
    node.type = AbstractSyntaxNode::Type::Block;
    node.data.block = &block;
    program.syntax_list.emplace_back().type = AbstractSyntaxNode::Type::Return;

    Shader::ImageBufferDescriptor descriptor{};
    descriptor.format = Shader::ImageFormat::R32_UINT;
    descriptor.is_written = true;
    descriptor.is_read = true;
    descriptor.is_integer = true;
    descriptor.count = test.descriptor_count;
    program.info.image_buffer_descriptors.push_back(descriptor);
    program.info.uses_image_buffers = true;
    program.info.uses_atomic_image_u32 = true;

    TextureInstInfo info{};
    info.raw = static_cast<u32>(Shader::TextureType::Buffer) << 16;

    Value index{test.immediate_index};
    if (test.dynamic_index) {
        block.AppendNewInst(Opcode::IAdd32, {Value{u32{0}}, Value{u32{1}}});
        index = Value{&block.back()};
    }

    block.AppendNewInst(Opcode::ImageAtomicInc32,
                        {index, Value{u32{4}}, Value{u32{7}}});
    block.back().SetFlags(info);
    block.AppendNewInst(Opcode::ImageAtomicDec32,
                        {index, Value{u32{8}}, Value{u32{7}}});
    block.back().SetFlags(info);
    // Exercise the maintained shared-memory CAS backend in the same genuine
    // EmitSPIRV module. The Maxwell frontend owns register decoding separately.
    block.AppendNewInst(Opcode::SharedAtomicCompareExchange32,
                        {Value{u32{0}}, Value{u32{0x11}}, Value{u32{0x22}}});

    Shader::Profile profile{};
    profile.supported_spirv = 0x00010500;
    profile.support_storage_texel_buffer_array_nonuniform_indexing =
        test.nonuniform_supported;
    Bindings bindings{};

    try {
        auto words = EmitSPIRV(profile, Shader::RuntimeInfo{}, program, bindings);
        if (test.expected_rejection != nullptr) {
            Fail("expected descriptor guard did not reject");
        }
        Require(CountOp(words, spv::Op::OpImageTexelPointer) == 2,
                "expected two OpImageTexelPointer instructions");
        Require(CountOp(words, spv::Op::OpAtomicLoad) == 2,
                "expected two OpAtomicLoad instructions");
        Require(CountOp(words, spv::Op::OpAtomicCompareExchange) == 3,
                "expected two image CAS operations plus one shared-memory CAS");
        Require(CountOp(words, spv::Op::OpLoopMerge) == 2,
                "expected two structured CAS loops");
        if (test.descriptor_count > 1) {
            Require(CountOp(words, spv::Op::OpTypeArray) >= 1,
                    "descriptor array did not emit OpTypeArray");
            Require(CountOp(words, spv::Op::OpAccessChain) >= 2,
                    "dynamic image atomics did not select array elements");
        }
        WriteModule(test.output_path, words);
        return words;
    } catch (const std::exception& ex) {
        if (test.expected_rejection == nullptr ||
            std::string_view{ex.what()}.find(test.expected_rejection) == std::string_view::npos) {
            std::fprintf(stderr, "unexpected exception: %s\n", ex.what());
            Fail("genuine EmitSPIRV rejection did not match the expected guard");
        }
        return {};
    }
}

} // namespace

int main(int argc, char** argv) {
    Require(argc == 2, "usage: test_image_atomic_real_spirv <output-prefix>");
    const std::string prefix{argv[1]};

    const auto scalar = Compile({
        .descriptor_count = 1,
        .dynamic_index = false,
        .nonuniform_supported = false,
        .immediate_index = 0,
        .expected_rejection = nullptr,
        .output_path = (prefix + "-scalar.spv").c_str(),
    });
    Require(!scalar.empty(), "scalar image atomic module missing");

    const std::string array_path = prefix + "-array.spv";
    const auto array = Compile({
        .descriptor_count = 2,
        .dynamic_index = true,
        .nonuniform_supported = true,
        .immediate_index = 0,
        .expected_rejection = nullptr,
        .output_path = array_path.c_str(),
    });
    Require(!array.empty(), "dynamic descriptor image atomic module missing");

    (void)Compile({
        .descriptor_count = 2,
        .dynamic_index = true,
        .nonuniform_supported = false,
        .immediate_index = 0,
        .expected_rejection =
            "Dynamic atomic image descriptor requires non-uniform indexing support",
        .output_path = nullptr,
    });
    (void)Compile({
        .descriptor_count = 2,
        .dynamic_index = false,
        .nonuniform_supported = true,
        .immediate_index = 2,
        .expected_rejection = "Atomic image descriptor array index out of range",
        .output_path = nullptr,
    });

    std::puts("NS1_IMAGE_ATOMIC_REAL_SPIRV_EMITTED scalar=1 array=1 inc=1 dec=1 shared_cas=1 "
              "nonuniform_refused=1 out_of_range_refused=1");
    return 0;
}
