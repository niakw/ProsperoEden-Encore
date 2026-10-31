#!/usr/bin/env python3
"""N65: native PS5 VkSparseImageMemoryRequirements query, without dispatch layout changes."""
from pathlib import Path
import argparse
def replace(src,old,new):
    if src.count(old)!=1:
        raise RuntimeError("N65 native PS5 Vulkan wrapper owner drift: "+old[:110])
    return src.replace(old,new)
def adapt(header,code):
    header=replace(header,
        '''    VkMemoryRequirements GetImageMemoryRequirements(VkImage image) const noexcept;''',
        '''    VkMemoryRequirements GetImageMemoryRequirements(VkImage image) const noexcept;

    // N65: query the actual sparse 2D tile/mip-tail requirements.
    // No DeviceDispatch layout change: resolve entrypoint on demand.
    [[nodiscard]] std::vector<VkSparseImageMemoryRequirements>
        GetSparseImageMemoryRequirements(VkImage image) const;''')
    code=replace(code,'''std::vector<VkPipelineExecutablePropertiesKHR> Device::GetPipelineExecutablePropertiesKHR(
    VkPipeline pipeline) const {''',
'''std::vector<VkSparseImageMemoryRequirements>
Device::GetSparseImageMemoryRequirements(VkImage image) const {
    // Native PS5 Vulkan shim might not export this optional entry point.
    if (!image || !dld || !dld->vkGetDeviceProcAddr) return {};
    const auto fn = reinterpret_cast<PFN_vkGetImageSparseMemoryRequirements>(
        dld->vkGetDeviceProcAddr(handle, "vkGetImageSparseMemoryRequirements"));
    if (!fn) return {};
    u32 count = 0;
    fn(handle, image, &count, nullptr);
    // Vulkan can report multiple aspects. Bound counts to avoid untrusted
    // allocation sizes on malformed/buggy drivers.
    if (!count || count > 64) return {};
    std::vector<VkSparseImageMemoryRequirements> requirements(count);
    fn(handle, image, &count, requirements.data());
    if (!count || count > requirements.size()) return {};
    requirements.resize(count);
    return requirements;
}

std::vector<VkPipelineExecutablePropertiesKHR> Device::GetPipelineExecutablePropertiesKHR(
    VkPipeline pipeline) const {''')
    return header,code
def main():
    p=argparse.ArgumentParser()
    for x in ('header','source','output'):p.add_argument('--'+x,required=True)
    a=p.parse_args()
    h,c=adapt(Path(a.header).read_text(),Path(a.source).read_text())
    out=Path(a.output)
    hfile=out/'include/video_core/vulkan_common/vulkan_wrapper.h'
    cfile=out/'vulkan_wrapper.cpp'
    hfile.parent.mkdir(parents=True,exist_ok=True)
    hfile.write_text(h);cfile.write_text(c)
    print("N65_NATIVE_PS5_SPARSE_IMAGE_REQUIREMENTS_OWNER_GENERATED")
if __name__=='__main__': main()
