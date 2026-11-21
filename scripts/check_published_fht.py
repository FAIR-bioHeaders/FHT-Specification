#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""Delegate published FHT checks to its immutable shared authority.

No fixtures, expectations, parser or schema validator are maintained here.
Installed comparison is optional and must use a real published-package venv.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

from published_authority import SHARED_COMMIT, verified_shared


def load(name, location):
    spec = importlib.util.spec_from_file_location(name, location)
    if spec is None or spec.loader is None:
        raise ValueError('cannot load verified module: ' + str(location))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--shared', required=True, type=Path,
                        help='clean shared specification checkout at exact v0.7.0 commit')
    parser.add_argument('--venv', type=Path, help='noneditable published toolkit environment')
    args = parser.parse_args()
    try:
        with verified_shared(args.shared) as shared:
            check(args, parser, shared)
    except (OSError, ValueError) as error:
        parser.error(str(error))


def check(args, parser, shared):
    head = SHARED_COMMIT
    # A caller opting into a historical draft must not contaminate this lane.
    for key in ('BIOHEADERS_EXPERIMENTAL_FHT', 'BIOHEADERS_CANDIDATE_FHT',
                'BIOHEADERS_FHT_SCHEMA'):
        if key in os.environ:
            parser.error('remove draft/overlay environment variable ' + key)
    sys.path.insert(0, str(shared / 'scripts'))
    authority = load('published_fht_authority', shared / 'scripts/fht_publication.py')
    report = authority.check()
    report['examplePairs'] = authority.check_examples()
    if report['cases'] != 93 or report['examplePairs'] != 7:
        raise ValueError('unexpected authority suite/example counts')
    report['authorityCommit'] = head
    report['installedComparison'] = 'NOT-RUN: no --venv supplied'
    if args.venv:
        converter = load('published_shared_converter_check', shared / 'scripts/check_conformance.py')
        conformance = shared / 'conformance/fht-v0.7.0'
        manifest = json.loads((conformance / 'manifest.json').read_text())
        executable = args.venv.resolve() / 'bin/bioheaders'
        if not executable.is_file():
            parser.error('--venv has no installed bin/bioheaders executable')
        # The immutable v0.7.0 command table predates FHT. Adapt only its
        # command lookup to the supported generic CLI; all expectations,
        # diagnostics and comparison logic remain in the shared checker.
        adapter = """import json, pathlib, subprocess, sys
exe, shared, child = sys.argv[1:]
root = pathlib.Path(shared)
manifest = json.loads((root / 'conformance/fht-v0.7.0/manifest.json').read_text())
entry = next(v for v in manifest['vectors']
             if root / 'conformance/fht-v0.7.0' / v['file'] == pathlib.Path(child))
result = subprocess.run([exe, 'verify', child])
if result.returncode == 0 and entry.get('parentLink'):
    parents = [str(root / 'drafts/fht/upstream/conformance' / link['file'])
               for link in entry['parentLink'] if link['file'] is not None]
    required = ['--require-all'] if all(link['file'] is not None
                                        for link in entry['parentLink']) else []
    result = subprocess.run([exe, 'verify-links', *required, child, *parents])
sys.exit(result.returncode)
"""
        def commands(location):
            def command(kind):
                if kind != 'fht-fasta':
                    raise ValueError('unexpected format in FHT-only authority: ' + kind)
                return [sys.executable, '-c', adapter, str(executable), str(shared)]
            return command
        converter.converter_commands = commands
        unsupported = set()
        problems = converter.check_converter(conformance, manifest, str(args.venv.resolve()),
                                             require=('fht-fasta',), unsupported=unsupported)
        if problems or unsupported:
            raise ValueError(json.dumps(dict(problems=problems, unsupported=sorted(unsupported))))
        report['installedComparison'] = dict(cases=len(manifest['vectors']),
                                              disagreements=0, unsupported=sorted(unsupported))
    # The authority report deliberately says publicationVerified=False: this
    # executable does not authenticate release/archive publication or live aliases.
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
