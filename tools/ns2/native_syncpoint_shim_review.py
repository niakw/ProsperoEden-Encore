#!/usr/bin/env python3
"""Reverse only the reviewed Lichii 12125bc NVN syncpoint-shim source diff.

Vendor 8157c796 added a virtual, read-only Host1x syncpoint window to the
already reviewed GPU memory owner. This witness proves the exact successor
blob and reconstructs the exact pre-shim blob before older range/PTE reviews
run. It does not relax admission of any other memory_manager.cpp variant.
"""
import hashlib

BEFORE = "f36837c70435a919fd8d51b46983707c634039cc"
AFTER = "46f0157cc2fd61e63220461261d851b8429ea4fd"

def blob(text: str) -> str:
    raw = text.encode()
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()

SETTER = """void MemoryManager::SetNativeSyncpointShim(GPUVAddr address) {
    native_syncpoint_shim.store(address, std::memory_order_release);
}

"""

SCALAR = """    if constexpr (sizeof(T) == sizeof(u32)) {
        const GPUVAddr shim = native_syncpoint_shim.load(std::memory_order_acquire);
        constexpr u64 shim_bytes = u64{NumShimSyncpoints} * sizeof(u32);
        if (shim != 0 && addr >= shim && addr - shim < shim_bytes &&
            Common::IsAligned(addr - shim, sizeof(u32))) {
            return static_cast<T>(system.Host1x().GetSyncpointManager().GetGuestSyncpointValue(
                static_cast<u32>((addr - shim) / sizeof(u32))));
        }
    }

"""

BLOCK = """    // NVN's syncpoint shim is deliberately not backed by guest/device RAM. Serve reads wholly
    // inside its 192 u32 words directly from Host1x; all ordinary NS1 addresses keep this path.
    const GPUVAddr shim = native_syncpoint_shim.load(std::memory_order_acquire);
    constexpr u64 shim_bytes = u64{NumShimSyncpoints} * sizeof(u32);
    if (shim != 0 && gpu_src_addr >= shim && gpu_src_addr - shim < shim_bytes &&
        size <= shim_bytes - (gpu_src_addr - shim)) {
        auto* out = static_cast<u8*>(dest_buffer);
        u64 rel = gpu_src_addr - shim;
        std::size_t remaining = size;
        while (remaining != 0) {
            const u32 value = system.Host1x().GetSyncpointManager().GetGuestSyncpointValue(
                static_cast<u32>(rel / sizeof(u32)));
            const std::size_t in_word = static_cast<std::size_t>(rel % sizeof(u32));
            const std::size_t amount = (std::min)(remaining, sizeof(u32) - in_word);
            std::memcpy(out, reinterpret_cast<const u8*>(&value) + in_word, amount);
            out += amount;
            rel += amount;
            remaining -= amount;
        }
        return;
    }

"""

def recover_before_syncpoint_shim(actual: str) -> str:
    assert blob(actual) == AFTER, "unreviewed NVN syncpoint-shim memory source drift"
    for label, block in (("setter", SETTER), ("scalar", SCALAR), ("block", BLOCK)):
        assert actual.count(block) == 1, ("syncpoint shim source block drift", label)
        actual = actual.replace(block, "", 1)
    assert "native_syncpoint_shim" not in actual
    assert blob(actual) == BEFORE, "NVN syncpoint shim changed unrelated memory source"
    return actual
