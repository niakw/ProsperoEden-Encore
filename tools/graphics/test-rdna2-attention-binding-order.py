#!/usr/bin/env python3
"""Fail on reversed storage descriptors in RDNA2 QKV->attention Vulkan links."""
import argparse
from pathlib import Path
import re

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--vendor",type=Path,required=True)
    args=ap.parse_args()
    root=args.vendor/"encore-active"/"eden-vulkan"
    shader=(root/"r09_rdna2_nr/window_attention_rdna2.comp").read_text()
    def binding(block):
        match=re.search(
            r"layout\\(set\\s*=\\s*0,\\s*binding\\s*=\\s*(\\d+),"
            r"\\s*std430\\)\\s*(?:readonly|writeonly)\\s+buffer\\s+"
            +block+r"\\b",shader)
        if match is None:
            raise AssertionError("Missing shader block: "+block)
        return int(match.group(1))
    assert binding("Queries")==0
    assert binding("Keys")==1
    assert binding("Values")==2
    assert binding("Bias")==3
    assert binding("Result")==4

    fswin=(root/"nr_rdna2_fswin_descriptors.cpp").read_text()
    assert "put(ready.attention,3u,b.weights);" in fswin
    assert "put(ready.attention,4u,b.context);" in fswin
    split=(root/"nr_rdna2_split_window_link.cpp").read_text()
    pattern=(r"const std::array<VkDescriptorBufferInfo,11> infos\\s*\\{"
             r"\\s*b.input,b.weights,b.scales,b.query,b.key,b.value,"
             r"\\s*b.query,b.key,b.value,b.bias,b.context\\s*\\}")
    assert re.search(pattern,split), "Split-Swin descriptors swapped"
    assert "i<6u?i:i-6u" in split, "Split-Swin binding numbering changed"
    print("RDNA2 attention descriptors: Q/K/V 0/1/2, bias 3, result 4")

if __name__=="__main__":
    main()
