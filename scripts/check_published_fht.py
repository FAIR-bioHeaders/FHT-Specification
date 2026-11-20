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

SHARED_COMMIT = '623c79fe58edeb238a20fb6de518c62dd69b92bc'


def load(name, location):
    spec = importlib.util.spec_from_file_location(name, location)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--shared', required=True, type=Path,
                        help='clean shared specification checkout at exact v0.7.0 commit')
    parser.add_argument('--venv', type=Path, help='noneditable published toolkit environment')
    args = parser.parse_args()
    shared = args.shared.resolve()
    head = subprocess.check_output(['git', '-C', str(shared), 'rev-parse', 'HEAD'], text=True).strip()
    dirty = subprocess.check_output(['git', '-C', str(shared), 'status', '--porcelain'], text=True)
    if head != SHARED_COMMIT or dirty:
        parser.error('shared checkout must be clean and exactly ' + SHARED_COMMIT)
    # A caller opting into a historical draft must not contaminate this lane.
    for key in ('BIOHEADERS_EXPERIMENTAL_FHT', 'BIOHEADERS_FHT_SCHEMA'):
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
