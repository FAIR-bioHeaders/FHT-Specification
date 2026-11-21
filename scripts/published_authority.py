# SPDX-License-Identifier: MPL-2.0
"""Read immutable shared code from a private Git checkout, never mutable neighbors."""
from contextlib import contextmanager
import hashlib
import os
from pathlib import Path
import subprocess
import tempfile

SHARED_COMMIT = '623c79fe58edeb238a20fb6de518c62dd69b92bc'
EXECUTABLE_PINS = {
    'scripts/fht_publication.py': '405b25f3f8bc26cacb0b0604878a166c6a976d6c2a1c9a4ee1a55c72f0dac292',
    'scripts/check_conformance.py': '3bad4d4afc5a49c3f5fb7a1e8533588d7ebc2b076619f2b7ba3dfe36f3983905',
}


def git(*args):
    env = {key: value for key, value in os.environ.items() if not key.startswith('GIT_')}
    env.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull,
               GIT_NO_REPLACE_OBJECTS='1')
    result = subprocess.run(['git', '--no-replace-objects', '-c',
        'core.hooksPath=' + os.devnull, '-c', 'init.templateDir=', *map(str, args)],
        env=env, capture_output=True, check=False)
    if result.returncode:
        raise ValueError('cannot establish immutable shared authority: ' +
                         result.stderr.decode('utf-8', 'replace').strip())
    return result.stdout


def verify_code(root):
    for relative, expected in EXECUTABLE_PINS.items():
        file = root / relative
        if file.is_symlink() or not file.resolve().is_relative_to(root.resolve()):
            raise ValueError('shared executable must be a confined regular file: ' + relative)
        if not file.is_file() or hashlib.sha256(file.read_bytes()).hexdigest() != expected:
            raise ValueError('shared executable SHA-256 mismatch: ' + relative)


@contextmanager
def verified_shared(location):
    """Yield a disposable object-derived checkout at the fixed published identity.

    The caller's tree is not executed. A clone without local object shortcuts,
    replace refs, external Git configuration or hooks also drops ignored/untracked
    neighbor modules. The private tag still supports the immutable HTML binding.
    This is local code provenance, not isolation against a hostile concurrent user.
    """
    source = Path(location).resolve()
    if git('-C', source, 'rev-parse', 'HEAD').decode().strip() != SHARED_COMMIT:
        raise ValueError('shared checkout must be exactly ' + SHARED_COMMIT)
    if git('-C', source, 'status', '--porcelain', '--untracked-files=all'):
        raise ValueError('shared checkout must be clean')
    verify_code(source)  # includes assume-unchanged tracked-file mutations
    with tempfile.TemporaryDirectory(prefix='fht-published-authority-') as directory:
        snapshot = Path(directory) / 'shared'
        git('clone', '--quiet', '--no-local', '--no-checkout', '--', source, snapshot)
        git('-C', snapshot, 'checkout', '--quiet', '--detach', SHARED_COMMIT)
        tag = git('-C', snapshot, 'rev-parse', '--verify', 'refs/tags/v0.7.0^{commit}').decode().strip()
        if tag != SHARED_COMMIT:
            raise ValueError('shared v0.7.0 tag does not identify the pinned authority')
        verify_code(snapshot)
        yield snapshot
