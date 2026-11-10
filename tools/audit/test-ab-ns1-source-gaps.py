#!/usr/bin/env python3
"""Deterministic synthetic regression fixtures for PR #45's static source checker.

Tests the checker, NOT maintained C++ compiled objects or a PS5 runtime.
No vendor checkout or network access is required.
"""
import importlib.util
from pathlib import Path

checker = Path(__file__).with_name("check-ab-ns1-source-gaps.py")
spec = importlib.util.spec_from_file_location("ab_checker", checker)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

DATA = {
    "headless/CMakeLists.txt": "EDEN_NS2_QMD_CBUF_DIRECT_SPIRV\n"
       "set_property(TARGET shader_recompiler PROPERTY SOURCES x)\n"
       "EDEN_MAINTAINED_ROMFS_BUILDER",
    "vendor/encore-active/ns2-runtime/ampere/shader_recompiler/backend/spirv/emit_spirv_context_get_set.cpp":
       "void EmitSetFragColor(EmitContext& ctx) { ctx.OpStore(pointer, value); }",
    "vendor/encore-active/ps5-mesa/src/amd/vulkan/radv_cmd_buffer.c":
       "void radv_CmdPipelineBarrier2(VkCommandBuffer cb) { barrier(); }",
    "vendor/sources/ps5-mesa/src/amd/vulkan/meta/radv_meta_buffer.c":
       "void radv_CmdFillBuffer(VkCommandBuffer cb) {}\n"
       "void radv_CmdCopyBuffer2(VkCommandBuffer cb) {}\n"
       "void radv_CmdUpdateBuffer(VkCommandBuffer cb) {}",
    "vendor/sources/ps5-mesa/src/amd/vulkan/meta/radv_meta_copy.c":
       "void radv_CmdCopyBufferToImage2(VkCommandBuffer cb) {}\n"
       "void radv_CmdCopyImageToBuffer2(VkCommandBuffer cb) {}",
    "vendor/encore-active/eden-core/src/core/file_sys/fsmitm_romfsbuild.cpp":
       "RomFSBuildContext::~RomFSBuildContext() = default;",
    "headless/audio.cpp":
       "auto stream = type == StreamType::In ?\n"
       "SinkStreamPtr{std::make_unique<NullSinkStreamImpl>(system, type)} : output;",
    "vendor/sources/eden/src/audio_core/sink/null_sink.h":
       "std::vector<s16> ReleaseBuffer(u64 num_samples) override { return {}; }",
    "vendor/sources/eden/src/audio_core/device/device_session.cpp":
       "void DeviceSession::ReleaseBuffer(const AudioBuffer& buffer) const {\n"
       " WriteBlockUnsafe(buffer.samples, samples.data(), buffer.size);\n}",
    "headless/main.cpp": "Settings::values.audio_output_device_id = \"ps5\";",
    "tools/install-vendored-radv.py": "PATHS = ('src/amd/vulkan/radv_cmd_buffer.c',)",
}

original_read = module.read
try:
    module.read = lambda path: DATA[path]
    initial = module.triage()
    assert len(initial) == 4
    assert all(entry["classification"] == "source-gap" for entry in initial.values())
    assert initial["AB-04-AudioIn"]["null_sink_returns_empty"] is True
    assert initial["AB-04-AudioIn"]["ps5_input_device_explicitly_selected"] is False
    assert initial["AB-01-shader-NaN"]["conditional_shared_source_declared_in_cmake"] is True
    assert initial["AB-02-RADV-transfer"]["meta_unit_active_override_declarations"] == {
        "radv_meta_buffer.c": False, "radv_meta_copy.c": False}
    # One replacement unit must not be confused with coverage for both.
    DATA["tools/install-vendored-radv.py"] = (
        "PATHS = ('src/amd/vulkan/meta/radv_meta_buffer.c',)")
    assert module.triage()["AB-02-RADV-transfer"]["meta_unit_active_override_declarations"] == {
        "radv_meta_buffer.c": True, "radv_meta_copy.c": False}
    DATA["tools/install-vendored-radv.py"] = "PATHS = ('src/amd/vulkan/radv_cmd_buffer.c',)"


    DATA["vendor/sources/eden/src/audio_core/sink/null_sink.h"] = (
        "std::vector<s16> ReleaseBuffer(u64 num_samples) override { "
        "return std::vector<s16>(num_samples, 0); }")
    assert module.triage()["AB-04-AudioIn"]["classification"] == "unknown"
    DATA["vendor/encore-active/eden-core/src/core/file_sys/fsmitm_romfsbuild.cpp"] = (
        "RomFSBuildContext::~RomFSBuildContext() {"
        " root->sibling.reset(); root->child.reset(); root->file.reset(); }")
    assert module.triage()["AB-03-RomFS"]["classification"] == "unlink-present"
    DATA["vendor/encore-active/ns2-runtime/ampere/shader_recompiler/backend/spirv/emit_spirv_context_get_set.cpp"] = (
        "void EmitSetFragColor(EmitContext& ctx) { "
        "ctx.OpSelect(ctx.OpIsNan(value), zero, value); }")
    assert module.triage()["AB-01-shader-NaN"]["classification"] == "guard-present-in-source"
    DATA["vendor/encore-active/ps5-mesa/src/amd/vulkan/radv_cmd_buffer.c"] = (
        "void radv_CmdPipelineBarrier2(VkCommandBuffer cb) { radv_split_cmd_stream_if_due(cb); }")
    for file in ("radv_meta_buffer.c", "radv_meta_copy.c"):
        key = "vendor/sources/ps5-mesa/src/amd/vulkan/meta/" + file
        DATA[key] = DATA[key].replace(" {}", " { radv_split_cmd_stream_if_due(cb); }")
    assert module.triage()["AB-02-RADV-transfer"]["classification"] == "direct-guards-present"
    print("AB_NS1_SYNTHETIC_CLASSIFIER_REGRESSION_4_OF_4_OK")
finally:
    module.read = original_read
