#!/usr/bin/env python3
"""Pin the allocator symmetry behind CodeQL C++ alerts #18-#23.

This checks source invariants of the third-party Boost 1.90.0 snapshot,
without changing its allocator implementation or suppressing active forks.
Run after git submodule update (CodeQL's checkout uses submodules: true).
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
B = ROOT / "vendor/sources/eden-cpm/boost/boost-1.90.0/libs"
paths = {
    "vector": B / "container/include/boost/container/vector.hpp",
    "fca": B / "unordered/include/boost/unordered/detail/fca.hpp",
    "impl": B / "unordered/include/boost/unordered/detail/implementation.hpp",
    "foa": B / "unordered/include/boost/unordered/detail/foa/core.hpp",
}
sources = {}
for name, path in paths.items():
    if not path.is_file():
        raise SystemExit(f"Boost submodule unavailable: {path}")
    sources[name] = path.read_text()

checks = {
    "#23 vector allocator pair": (
        "vector",
        "return allocator_traits_type::allocate(this->alloc(), n);",
        "allocator_traits_type::deallocate(this->alloc(), p, n);",
        "this->deallocate(this->m_start, this->m_capacity);",
    ),
    "#22 fca exception rollback": (
        "fca",
        "buckets = boost::allocator_allocate(bucket_alloc, num_buckets);",
        "boost::allocator_deallocate(bucket_alloc, buckets, num_buckets);",
        "BOOST_CATCH(...)",
    ),
    "#20 fca bucket teardown": (
        "fca",
        "buckets = boost::allocator_allocate(bucket_alloc, num_buckets);",
        "(pb + i)->~bucket_type();",
        "boost::allocator_deallocate(bucket_alloc, buckets, num_buckets);",
    ),
    "#21 fca group teardown": (
        "fca",
        "groups = boost::allocator_allocate(group_alloc, num_groups);",
        "(pg + i)->~group();",
        "boost::allocator_deallocate(group_alloc, groups, num_groups);",
    ),
    "#19 unordered node ownership": (
        "impl",
        "node_ = node_allocator_traits::allocate(alloc_, 1);",
        "boost::unordered::detail::func::destroy(boost::to_address(node_));",
        "node_allocator_traits::deallocate(alloc_, node_, 1);",
    ),
    "#18 foa contiguous buffer": (
        "foa",
        "arrays.elements_=storage_traits::allocate(sal,buffer_size(groups_size));",
        "storage_traits::deallocate(",
        "sal,arrays.elements_,buffer_size(arrays.groups_size_mask+1)",
    ),
}
for desc, (name, *tokens) in checks.items():
    source = sources[name]
    for token in tokens:
        assert token in source, (desc, "missing allocator ownership evidence", token)

config = (ROOT / ".github/codeql/codeql-config.yml").read_text()
workflow = (ROOT / ".github/workflows/codeql-advanced.yml").read_text()
positive, excluded = config.split("paths-ignore:", 1)
for keep in ("  - headless", "  - src", "  - tools", "  - vendor/encore-active"):
    assert keep in positive, ("active first-party scope disappeared", keep)
for path in paths.values():
    relative = path.relative_to(ROOT).as_posix()
    assert f"  - '{relative}'" in excluded, ("audited file missing scoped exception", relative)
assert not any(line.strip().startswith("- ") and "vendor/encore-active" in line
               for line in excluded.splitlines()), "active renderer excluded"
assert "config-file: ./.github/codeql/codeql-config.yml" in workflow
assert "build-mode: none" in workflow
print("ENCORE_CODEQL_ALLOCATOR_PAIR_AUDIT_PASS: alerts #18-#23, active scope retained")
