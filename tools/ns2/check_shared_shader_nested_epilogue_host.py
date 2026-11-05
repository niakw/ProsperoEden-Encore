#!/usr/bin/env python3
"""P2.4 shared fragment shader: count every nested exit before demote reordering.

Extracts the exact reviewed DemoteCombinationPass scanning loop from the
active vendor Maxwell IR source. No ROM, game override or PS5 build.
"""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
OWNER = Path(os.environ.get(
    "EDEN_SHADER_CFLOW_SOURCE",
    str(ROOT/"vendor/sources/eden/src/shader_recompiler/frontend/maxwell/structured_control_flow.cpp")))
source = OWNER.read_text()
block = source.split("    void DemoteCombinationPass() {", 1)
assert len(block) == 2, "missing actual shared Maxwell demote pass"
start = "        for (const IR::AbstractSyntaxNode& node : syntax_list) {\n"
end = "        if (demote_blocks.size() == 0) {\n"
assert block[1].count(start) == block[1].count(end) == 1
loop = block[1].split(start, 1)[1].split(end, 1)[0]
assert "if (branch_depth <= 1)" in loop
assert "++num_epilogues;" in loop
assert "if (branch_depth > 1)" not in loop, "nested return lost before count"
assert "demote_blocks.push_back(node.data.block);" in loop
assert "if (op == IR::Opcode::Epilogue)" in loop

cpp = r"""
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <utility>
#include <vector>
using u32 = std::uint32_t;
namespace IR {
enum class Opcode { Other, DemoteToHelperInvocation, Epilogue };
struct Inst {
    Opcode op{};
    [[nodiscard]] Opcode GetOpcode() const noexcept { return op; }
};
struct Block {
    std::vector<Inst> code;
    [[nodiscard]] const std::vector<Inst>& Instructions() const noexcept { return code; }
};
struct AbstractSyntaxNode {
    enum class Type { If, EndIf, Block };
    Type type{};
    struct { Block* block{}; } data{};
};
}
int main() {
    using Type = IR::AbstractSyntaxNode::Type;
    IR::Block shallow_demote{{{IR::Opcode::DemoteToHelperInvocation}}};
    IR::Block nested_demote{{{IR::Opcode::DemoteToHelperInvocation}}};
    IR::Block nested_early_return{{{IR::Opcode::Epilogue}}};
    IR::Block final_return{{{IR::Opcode::Epilogue}}};
    auto node = [](Type type, IR::Block* b = nullptr) {
        IR::AbstractSyntaxNode n{};
        n.type = type;
        n.data.block = b;
        return n;
    };
    const auto scan = [&](const std::vector<IR::AbstractSyntaxNode>& syntax_list) {
        std::vector<IR::Block*> demote_blocks;
        u32 num_epilogues{};
        u32 branch_depth{};
__EXTRACTED_LOOP__
        return std::pair{demote_blocks.size(), num_epilogues};
    };

    const auto nested_return = scan({
        node(Type::If), node(Type::If),
        node(Type::Block, &nested_early_return),
        node(Type::EndIf), node(Type::EndIf),
        node(Type::If), node(Type::Block, &shallow_demote), node(Type::EndIf),
        node(Type::Block, &final_return)
    });
    assert(nested_return.first == 1 && nested_return.second == 2);
    // Two returns must make the enclosing pass reject demote relocation.
    assert(nested_return.second > 1);

    const auto normal = scan({
        node(Type::If), node(Type::Block, &shallow_demote), node(Type::EndIf),
        node(Type::Block, &final_return)
    });
    assert(normal.first == 1 && normal.second == 1);

    const auto skipped_nested_demote = scan({
        node(Type::If), node(Type::If),
        node(Type::Block, &nested_demote),
        node(Type::EndIf), node(Type::EndIf),
        node(Type::Block, &final_return)
    });
    assert(skipped_nested_demote.first == 0 && skipped_nested_demote.second == 1);
    std::puts("P2_4_SHARED_NESTED_EPILOGUE_DEMOTE_PASS");
}
""".replace("__EXTRACTED_LOOP__", start + loop)
env = os.environ.copy()
sdk = Path("/Library/Developer/CommandLineTools/SDKs/MacOSX15.4.sdk")
if sdk.is_dir():
    env["SDKROOT"] = str(sdk)
compilers = list(dict.fromkeys(filter(None, (
    shutil.which("clang++"), shutil.which("g++")))))
assert compilers
with tempfile.TemporaryDirectory(prefix="eden-nested-epilogue-") as temp:
    path = Path(temp)/"shader.cpp"
    path.write_text(cpp)
    for compiler in compilers:
        for opt in ("-O0", "-O2"):
            binary = Path(temp)/(Path(compiler).name.replace("+","p")+opt)
            build = subprocess.run(
                [compiler, "-std=c++20", opt, "-Wall", "-Wextra", "-Werror",
                 "-Wno-unused-parameter", "-fsanitize=undefined",
                 "-fno-sanitize-recover=all", str(path), "-o", str(binary)],
                capture_output=True, text=True, timeout=60, env=env)
            assert build.returncode == 0, (compiler, build.stderr[-3200:])
            run = subprocess.run([str(binary)], capture_output=True, text=True,
                                 timeout=15, env=env)
            assert run.returncode == 0, (compiler, run.stderr[-2500:])
            assert "P2_4_SHARED_NESTED_EPILOGUE_DEMOTE_PASS" in run.stdout
            print("P2_4_SHARED_FRAGMENT_NESTED_RETURN_PASS",
                  Path(compiler).name, opt, flush=True)
