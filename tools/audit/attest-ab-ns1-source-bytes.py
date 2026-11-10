#!/usr/bin/env python3
"""Read-only SHA256 comparison between *scheduled* sources and pinned source owners.

This is not compile, link, executed-path or PS5 runtime attestation. It requires
an existing compile_commands.json and the existing vendor checkout. No network,
build, source rewrite, or CI dispatch is performed.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
OWNER_SCRIPT = Path(__file__).with_name('verify-ab-ns1-compile-owners.py')

CANONICAL = {
    'audio_adapter': ('headless/audio.cpp',),
    'romfs_builder': ('vendor/encore-active/eden-core/src/core/file_sys/fsmitm_romfsbuild.cpp',),
    'shader_emitter': ('vendor/encore-active/ns2-runtime/ampere/shader_recompiler/backend/spirv/emit_spirv_context_get_set.cpp',),
    'jit_data': (
        'vendor/encore-active/eden-core/src/dynarmic/backend/x64/emit_x64_data_processing.cpp',
        'vendor/sources/eden/src/dynarmic/src/dynarmic/backend/x64/emit_x64_data_processing.cpp',
    ),
    'jit_vector': (
        'vendor/encore-active/eden-core/src/dynarmic/backend/x64/emit_x64_vector.cpp',
        'vendor/sources/eden/src/dynarmic/src/dynarmic/backend/x64/emit_x64_vector.cpp',
    ),
    'jit_fp': (
        'vendor/encore-active/eden-core/src/dynarmic/backend/x64/emit_x64_floating_point.cpp',
        'vendor/sources/eden/src/dynarmic/src/dynarmic/backend/x64/emit_x64_floating_point.cpp',
    ),
    'radv_cmd': (
        'vendor/encore-active/ps5-mesa/src/amd/vulkan/radv_cmd_buffer.c',
        'vendor/sources/ps5-mesa/src/amd/vulkan/radv_cmd_buffer.c',
    ),
    'radv_meta_buffer': ('vendor/sources/ps5-mesa/src/amd/vulkan/meta/radv_meta_buffer.c',),
    'radv_meta_copy': ('vendor/sources/ps5-mesa/src/amd/vulkan/meta/radv_meta_copy.c',),
}


def load_owner_tool():
    spec = importlib.util.spec_from_file_location('ab_compile_owner', OWNER_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError('compile-owner tool cannot be imported')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def attest(commands: list, root: Path, owner_tool) -> dict:
    owners = owner_tool.inspect(commands)
    results = {}
    for key in owner_tool.OWNERS:
        row = owners[key]
        paths = row['source_paths']
        references = {}
        for relative in CANONICAL[key]:
            canonical = root / relative
            if canonical.is_file():
                references[relative] = sha256(canonical)
        source = Path(paths[0]['path']) if len(paths) == 1 else None
        exists = source is not None and source.is_file()
        source_hash = sha256(source) if exists else None
        matches = [rel for rel, digest in references.items() if digest == source_hash] if source_hash else []
        if row['status'] == 'not-in-database':
            status = 'not-in-database'
        elif row['status'] != 'one-source-path':
            status = 'ambiguous-source-paths'
        elif not exists:
            status = 'compiled-source-not-on-disk'
        elif not references:
            status = 'canonical-reference-not-on-disk'
        else:
            status = 'byte-equal-canonical' if matches else 'byte-mismatch'
        results[key] = {
            'status': status,
            'scheduled_owner': row['status'],
            'compiled_source_path': str(source) if source else None,
            'compiled_source_sha256': source_hash,
            'canonical_sources_present': sorted(references),
            'canonical_byte_matches': matches,
            'canonical_sources_missing': sorted(set(CANONICAL[key]) - set(references)),
        }
    return results


def self_test():
    owner = load_owner_tool()
    with tempfile.TemporaryDirectory(prefix='ab-ns1-byte-') as tmp:
        root = Path(tmp)
        native = root / 'headless/audio.cpp'
        native.parent.mkdir(parents=True)
        native.write_bytes(b'audio-unchanged\n')
        row = {'directory': str(root), 'file': str(native)}
        result = attest([row], root, owner)
        assert result['audio_adapter']['status'] == 'byte-equal-canonical'
        assert result['jit_fp']['status'] == 'not-in-database'
        compiled = root / '.deps/work/radv-src/src/amd/vulkan/radv_cmd_buffer.c'
        compiled.parent.mkdir(parents=True)
        compiled.write_bytes(b'radv-original\n')
        canonical = root / CANONICAL['radv_cmd'][0]
        canonical.parent.mkdir(parents=True)
        canonical.write_bytes(b'radv-original\n')
        radv_row = {'directory': str(root), 'file': str(compiled)}
        result = attest([radv_row], root, owner)
        assert result['radv_cmd']['status'] == 'byte-equal-canonical'
        compiled.write_bytes(b'changed\n')
        assert attest([radv_row], root, owner)['radv_cmd']['status'] == 'byte-mismatch'
        compiled.unlink()
        assert attest([radv_row], root, owner)['radv_cmd']['status'] == 'compiled-source-not-on-disk'
        canonical.unlink()
        compiled.write_bytes(b'changed\n')
        assert attest([radv_row], root, owner)['radv_cmd']['status'] == 'canonical-reference-not-on-disk'
        second = root / 'vendor/encore-active/ps5-mesa/src/amd/vulkan/radv_cmd_buffer.c'
        second.write_bytes(b'changed\n')
        assert attest([radv_row, {'directory': str(root), 'file': str(second)}], root, owner)['radv_cmd']['status'] == 'ambiguous-source-paths'
    print('AB_NS1_SOURCE_BYTE_ATTEST_SELFTEST_OK')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('compile_commands', nargs='*', type=Path)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--require', action='append', choices=sorted(CANONICAL))
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    if not args.compile_commands:
        parser.error('provide existing compile_commands.json file(s) or --self-test')
    try:
        commands = []
        for path in args.compile_commands:
            with path.open(encoding='utf-8') as stream:
                entries = json.load(stream)
            if not isinstance(entries, list):
                raise ValueError(f'{path}: compilation database must be an array')
            commands.extend(entries)
        result = attest(commands, args.root, load_owner_tool())
    except (OSError, ValueError, json.JSONDecodeError, RuntimeError) as error:
        print(json.dumps({'status': 'incomplete-inputs', 'error': str(error)}))
        return 2
    gaps = [name for name in args.require or [] if result[name]['status'] != 'byte-equal-canonical']
    print(json.dumps({
        'scope': 'scheduled-source-bytes-only',
        'proves_compiled_linked_or_executed': False,
        'requires_complete_matching_vendor_checkout': True,
        'required_byte_match_gaps': gaps,
        'owners': result,
    }, indent=2, sort_keys=True))
    return int(bool(gaps))


if __name__ == '__main__':
    sys.exit(main())
