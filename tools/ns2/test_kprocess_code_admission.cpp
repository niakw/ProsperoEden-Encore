// SPDX-License-Identifier: GPL-3.0-or-later
// Host-only: test the admission contract at the real ExeFS -> KProcess call.
// This does not create a KProcess or execute Nintendo firmware.
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <limits>
#include "core/loader/ns2_kprocess_code_admission.h"

using Eden::NS2::ExeFS::AdmitKProcessCode;
using Eden::NS2::ExeFS::KProcessCodeStatus;
namespace {
void Expect(std::size_t module_bytes, std::size_t patch_bytes,
            KProcessCodeStatus status, std::size_t total = 0) {
    const auto result = AdmitKProcessCode(module_bytes, patch_bytes);
    if (result.status != status ||
        (status == KProcessCodeStatus::Ready && result.total_bytes != total)) {
        std::fprintf(stderr, "admission failed: module=%zu patch=%zu status=%u expected=%u\n",
                     module_bytes, patch_bytes, static_cast<unsigned>(result.status),
                     static_cast<unsigned>(status));
        std::abort();
    }
}
}
int main() {
    constexpr std::size_t page = Eden::NS2::ExeFS::KProcessCodePageSize;
    Expect(0, 0, KProcessCodeStatus::EmptyModules);
    Expect(0, page, KProcessCodeStatus::EmptyModules);
    Expect(1, 0, KProcessCodeStatus::UnalignedPages);
    Expect(page - 1, 0, KProcessCodeStatus::UnalignedPages);
    Expect(page, 0, KProcessCodeStatus::Ready, page);
    Expect(page, page, KProcessCodeStatus::Ready, 2 * page);
    Expect(page, 1, KProcessCodeStatus::UnalignedPages);
    Expect(page, std::numeric_limits<std::size_t>::max(),
           KProcessCodeStatus::SizeOverflow);
    Expect(std::numeric_limits<std::size_t>::max(), page,
           KProcessCodeStatus::SizeOverflow);
    if constexpr (sizeof(std::size_t) >= 8) {
        constexpr std::uint64_t max_pages =
            static_cast<std::uint64_t>(std::numeric_limits<std::int32_t>::max());
        constexpr std::size_t max_bytes = static_cast<std::size_t>(max_pages * page);
        Expect(max_bytes, 0, KProcessCodeStatus::Ready, max_bytes);
        Expect(max_bytes - page, page, KProcessCodeStatus::Ready, max_bytes);
        Expect(max_bytes, page, KProcessCodeStatus::PageCountOverflow);
        Expect(max_bytes + 1, 0, KProcessCodeStatus::UnalignedPages);
    }
    std::puts("NS2_KPROCESS_CODE_ADMISSION_PASS (process not executed)");
}
