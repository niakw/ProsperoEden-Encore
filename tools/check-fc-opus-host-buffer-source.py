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
PINS={"a946785d1ad02752ae47f9b32032e99bdbb53e02","db33f8ad0c325c84bd80047d992fafa5c2908151","0264f2ae94ef5889e8585171b5bfcb11fd3659ff","bc78a7610425e95d6645685cbd023a67b729ec24","7b7c4d2a37f9b0b248d3f3d6d9cce40596ed0c99","b9f6052a65ef01e23ca4a46ba1654ed3a58cf181","76c5efe8cc6d706e1c2ab0a00ddcce96e2d0adf3","6f4bb38594b273fe7cc4fba960dfe62cdb9f508e","4572e581d011c444fd59428d5c042098f05dcfca","f7ee793f1ee1bb1c2b1a35f68073844163658262","3f019c64c2907ac3e84baa9b6200de8898f30636","f0324324768bdc090a003079bbf121df862bc7f7","0ae51658a5d93e368408cad2484b99083ed7309f","697159fd0c183f8a164d0493929ae3b4bcb391d1","b1bb49abea63b6664e0945df8431e10aac128c2f","89d70eb505594447b3ca98658311002e74dac8ad", "b68126c9cd95eef6c6656ff6d7834c62c092aa46", "0fc157b7ccef428e675ff945bc48eceb08fff607", "42459a7893c51a178ecd0c2f74f3951cc20fa12d", "d1f8696448ed481e36380c3ea8431e3dc722304e", "c5614d3c7ef75958965bac93c9e343eccdbc0fbe", "67926ea4b6960eefebf0427929cf299e8e056013", "50a849a93494f442d47573b8ce8b8797c3cecd26", "2c85d0e8ed192c5eec79423e6be8d883fa0bd7ab", "053acc8ddf30fe65f6376564bbd6efef58f07ddc", "ffa519db0f68fb0d5d2acf791e381c898a34a175", "9e38066a508716fd959477eccf32c7fb2fde3356", "e298a9b05732346141b685eb4c9850bfa02d9e58","f7ccfda091fd7429f44159318a07391881a3e7c0","92c480e17fedecc21ab4882b76e8507b5aed3771","7039d7752c5d8b1a53db50be0d8f2f7803867e13","d3fca0aa188052f0efd2bad102950aeaeeb36ab0","dfc39fcc087738955b0373b45fa97facdeb2fc47","b806bc497049819e716ef6de81f2a85312b188ce"}
selected=subprocess.check_output(["git","rev-parse","HEAD:vendor"],cwd=ROOT,text=True).strip()
checked=subprocess.check_output(["git","-C",str(VENDOR),"rev-parse","HEAD"],text=True).strip()
assert selected==checked and selected in PINS,(selected,checked)

owners={
 "encore-active/eden/src/audio_core/opus/decoder.cpp":
     "db2d133f00f85bf287fa9852061552ce1055a65c",
 "encore-active/eden/src/audio_core/opus/hardware_opus.cpp":
     "bc65602591b35bb1c3e683953c35152bc5ac5f6e",
}
for path,expected in owners.items():
 actual=subprocess.check_output(["git","-C",str(VENDOR),"hash-object",path],text=True).strip()
 assert actual==expected,(path,expected,actual)

decoder=(VENDOR/"encore-active/eden/src/audio_core/opus/decoder.cpp").read_text()
hardware=(VENDOR/"encore-active/eden/src/audio_core/opus/hardware_opus.cpp").read_text()
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
