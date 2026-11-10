// SPDX-License-Identifier: GPL-3.0-or-later
// Isolated exact Lichii UploadBatch::CanAdd/Add logic; synthetic Vulkan handles.
// No Encore Vulkan scheduler, copy submission or pipeline is linked here.
#include <algorithm>
#include <array>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <iostream>
#include <limits>
#include <span>
#include <stdexcept>
#include <vector>
using u32=std::uint32_t; using u64=std::uint64_t;
using VkBuffer=u64;
struct VkBufferCopy {u64 srcOffset{},dstOffset{},size{};};
class UploadBatch {
public:
    struct Group { VkBuffer src; VkBuffer dst; u32 first; u32 count; };
    static constexpr size_t MaxCopies=64;
    [[nodiscard]] bool Empty()const noexcept {return copies.empty();}
    // Exact method body from Lichii 879b616b1, copied solely as a test fixture.
    [[nodiscard]] bool CanAdd(VkBuffer src, VkBuffer dst,
                              std::span<const VkBufferCopy> new_copies) const {
        if (copies.size() + new_copies.size() > MaxCopies) {
            return false;
        }
        for (const Group& group : groups) {
            if (src == group.dst || dst == group.src) {
                return false;
            }
            if (group.dst != dst) {
                continue;
            }
            for (u32 index = group.first; index < group.first + group.count; ++index) {
                const VkBufferCopy& pending = copies[index];
                for (const VkBufferCopy& copy : new_copies) {
                    if (copy.dstOffset < pending.dstOffset + pending.size &&
                        pending.dstOffset < copy.dstOffset + copy.size) {
                        return false;
                    }
                }
            }
        }
        return true;
    }
    void Add(VkBuffer src, VkBuffer dst, std::span<const VkBufferCopy> new_copies) {
        const u32 first = static_cast<u32>(copies.size());
        const u32 count = static_cast<u32>(new_copies.size());
        copies.insert(copies.end(), new_copies.begin(), new_copies.end());
        if (!groups.empty() && groups.back().src == src && groups.back().dst == dst) {
            groups.back().count += count;
        } else {
            groups.push_back({src, dst, first, count});
        }
    }
    std::vector<VkBufferCopy> copies;
    std::vector<Group> groups;
};
// Candidate preflight for a future Encore port. Vulkan's queueing routine
// must reject empty, overflowing and out-of-allocation regions BEFORE CanAdd.
[[nodiscard]] bool ValidCopy(VkBufferCopy c,u64 src_size,u64 dst_size) {
    return c.size && c.srcOffset<=src_size && c.dstOffset<=dst_size &&
        c.size<=src_size-c.srcOffset && c.size<=dst_size-c.dstOffset;
}
int main() {
    u32 count{};
    const auto check=[&](bool v){++count;if(!v)throw std::runtime_error("upload batch contract "+std::to_string(count));};
    UploadBatch b;
    const std::array<VkBufferCopy,1> region{{{0,0,64}}};
    check(b.Empty());
    check(b.CanAdd(11,22,region));
    check(ValidCopy(region[0],64,64));
    b.Add(11,22,region);
    check(!b.Empty()&&b.copies.size()==1&&b.groups.size()==1&&b.groups[0].count==1);
    const std::array<VkBufferCopy,1> next{{{64,64,64}}};
    check(b.CanAdd(11,22,next)); // Same buffers, non-overlapping destination.
    b.Add(11,22,next);
    check(b.groups.size()==1&&b.groups[0].count==2);
    const std::array<VkBufferCopy,1> dst_overlap{{{128,16,32}}};
    check(!b.CanAdd(11,22,dst_overlap));
    const std::array<VkBufferCopy,1> dst_edge{{{128,128,32}}};
    check(b.CanAdd(11,22,dst_edge));
    check(!b.CanAdd(22,33,dst_edge)); // RAW against prior dst.
    check(!b.CanAdd(33,11,dst_edge)); // WAR against prior src.
    check(b.CanAdd(55,66,dst_edge));
    b.Add(55,66,dst_edge);
    check(b.groups.size()==2&&b.copies.size()==3);
    check(!b.CanAdd(66,77,dst_edge));
    check(!b.CanAdd(77,55,dst_edge));
    const std::array<VkBufferCopy,61> fill{};
    check(b.CanAdd(88,99,fill)); // 3+61=64 (empty-size Vulkan copies not validated here).
    check(!b.CanAdd(88,99,std::span<const VkBufferCopy>{fill.data(),62}));
    check(ValidCopy({64,64,64},128,128));
    check(!ValidCopy({64,65,64},128,128));
    check(!ValidCopy({0,0,0},128,128));
    check(!ValidCopy({std::numeric_limits<u64>::max()-1,8,4},
                     std::numeric_limits<u64>::max(),128));
    check(!ValidCopy({8,std::numeric_limits<u64>::max()-1,4},
                     128,std::numeric_limits<u64>::max()));
    // Very large invalid Vulkan offsets can overflow old overlap arithmetic.
    UploadBatch hostile;
    const std::array<VkBufferCopy,1> wrap{{{0,std::numeric_limits<u64>::max()-1,4}}};
    hostile.Add(1,2,wrap);
    check(hostile.CanAdd(1,2,wrap)); // Existing overlap test wraps and misses it.
    check(!ValidCopy(wrap[0],128,128)); // Required preflight must reject input.
    // Per-copy caller iteration catches in-batch conflicting destinations:
    UploadBatch staged;
    const std::array<VkBufferCopy,1> same{{{0,32,64}}};
    check(staged.CanAdd(1,2,same));
    staged.Add(1,2,same);
    check(!staged.CanAdd(1,2,same));
    std::cout<<"PASS: "<<count<<" exact upstream UploadBatch contract checks; preflight rejects overflows\n";
}
