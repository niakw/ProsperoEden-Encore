#!/usr/bin/env python3
"""Exact engine-selected FC-family Opus host-buffer source contract.

Upstream evidence: Eden Issue-Reports #684 reproduces a host libopus overflow
in FC26. This gate proves the engine pin selects the reviewed Encore adaptation;
it does not claim FC27 or PS5 runtime validation.
"""
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
VENDOR=ROOT/"vendor"
PIN="a946785d1ad02752ae47f9b32032e99bdbb53e02"
selected=subprocess.check_output(["git","rev-parse","HEAD:vendor"],cwd=ROOT,text=True).strip()
checked=subprocess.check_output(["git","-C",str(VENDOR),"rev-parse","HEAD"],text=True).strip()
assert selected==checked==PIN,(selected,checked)

owners={
 "encore-active/eden-core/src/audio_core/opus/decoder.cpp":
     "db2d133f00f85bf287fa9852061552ce1055a65c",
 "encore-active/eden-core/src/audio_core/opus/hardware_opus.cpp":
     "bc65602591b35bb1c3e683953c35152bc5ac5f6e",
}
for path,expected in owners.items():
 actual=subprocess.check_output(["git","-C",str(VENDOR),"hash-object",path],text=True).strip()
 assert actual==expected,(path,expected,actual)

decoder=(VENDOR/"encore-active/eden-core/src/audio_core/opus/decoder.cpp").read_text()
hardware=(VENDOR/"encore-active/eden-core/src/audio_core/opus/hardware_opus.cpp").read_text()
assert decoder.count("std::max<u64>(transfer_memory_size, host_work_size)") == 2
assert decoder.count("work_size + buffer_size") == 2
assert decoder.count("* sizeof(s16)") >= 2
assert "hardware_opus.GetWorkBufferSize(params.channel_count)" in decoder
assert "hardware_opus.GetWorkBufferSizeForMultiStream(" in decoder
assert "shared_buffer.resize(transfer_memory_size" not in decoder
capacity="output_data_size / (static_cast<u64>(channel_count) * sizeof(s16))"
assert hardware.count(capacity) == 2
assert "R_UNLESS(channel_count > 0 && channel_count <= shared_memory.channel_mapping.size()," in hardware
assert "ASSERT(channel_count <= shared_memory.channel_mapping.size())" not in hardware
print("FC_OPUS_ENGINE_SELECTED_SOURCE_PASS exact_pin=1 owners=2 byte_pcm=1 host_state=1 samples_per_channel=1 console_pending=1")
