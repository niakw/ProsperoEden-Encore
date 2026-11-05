// SPDX-License-Identifier: GPL-3.0-or-later
#include "verified_archive.hpp"
#include <cassert>
#include <vector>
#include <string>
#include <cstdint>
#include <algorithm>

int main() {
    using Eden::EncoreUpdate::VerifiedArchive;
    constexpr auto hash = "bf63d8a95fcc2e64619813aae35fdcbe871fdd9264caa3f365eb3aed0f679129";
    constexpr std::size_t n = 1024 * 1024;
    std::vector<char> bytes(n,'Z');
    VerifiedArchive correct(n,hash);
    assert(correct.Valid());
    assert(!correct.Finished());
    for (std::size_t i=0; i<bytes.size(); i+=713)
        assert(correct.Accept(bytes.data()+i,std::min<std::size_t>(713,n-i)));
    assert(correct.Bytes()==n);
    assert(correct.Finish());
    assert(correct.Finished());
    assert(!correct.Accept(bytes.data(),1));  // finalized streams do not reopen

    VerifiedArchive truncated(n,hash);
    assert(truncated.Accept(bytes.data(),n-1));
    assert(!truncated.Finish());
    VerifiedArchive oversized(n,hash);
    assert(!oversized.Accept(bytes.data(),n+1));
    assert(!oversized.Valid());
    VerifiedArchive invalid_size(1,hash);
    assert(!invalid_size.Valid());
    VerifiedArchive invalid_hash(n,"abcdef");
    assert(!invalid_hash.Valid());
    VerifiedArchive wrong_bytes(n,hash);
    bytes.back()='Q';
    assert(wrong_bytes.Accept(bytes.data(),n));
    assert(!wrong_bytes.Finish());
    VerifiedArchive wrong_hash(n,"ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff");
    bytes.back()='Z';
    assert(wrong_hash.Accept(bytes.data(),n));
    assert(!wrong_hash.Finish());
    return 0;
}
