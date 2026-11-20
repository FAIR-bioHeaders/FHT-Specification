"""Immutable execution controls use tiny synthetic repositories, not published fixtures."""
import hashlib
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import published_authority as authority


class PublishedAuthorityTests(unittest.TestCase):
    def source(self, root):
        (root / 'scripts').mkdir()
        code = b'from pathlib import Path\ndef neighbor(): return Path(__file__).with_name("data.txt").read_text()\n'
        (root / 'scripts/good.py').write_bytes(code)
        (root / 'scripts/data.txt').write_text('published')
        def git(*args):
            return subprocess.check_output(['git', '-c', 'core.hooksPath=/dev/null',
                '-c','user.name=Fixture','-c','user.email=fixture@example.invalid',
                '-C',str(root),*args],stderr=subprocess.DEVNULL)
        git('init','--quiet');git('add','scripts');git('commit','--quiet','--no-gpg-sign','-m','published')
        commit=git('rev-parse','HEAD').decode().strip();git('tag','v0.7.0')
        pins={'scripts/good.py':hashlib.sha256(code).hexdigest()}
        return git,commit,pins,code

    def test_private_clone_uses_objects_not_hidden_working_neighbors(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);git,commit,pins,code=self.source(root)
            (root/'scripts/data.txt').write_text('untrusted working bytes')
            git('update-index','--assume-unchanged','scripts/data.txt')
            self.assertFalse(git('status','--porcelain'))
            with mock.patch.object(authority,'SHARED_COMMIT',commit), \
                    mock.patch.object(authority,'EXECUTABLE_PINS',pins):
                with authority.verified_shared(root) as snapshot:
                    self.assertNotEqual(snapshot,root)
                    spec=importlib.util.spec_from_file_location('safe_fixture',snapshot/'scripts/good.py')
                    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
                    self.assertEqual(module.neighbor(),'published')
            self.assertFalse(snapshot.exists())
            self.assertEqual((root/'scripts/data.txt').read_text(),'untrusted working bytes')

    def test_hidden_modified_executable_refuses_before_execution(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);git,commit,pins,code=self.source(root)
            (root/'scripts/good.py').write_bytes(b'raise RuntimeError("unverified code executed")\n')
            git('update-index','--assume-unchanged','scripts/good.py')
            self.assertFalse(git('status','--porcelain'))
            with mock.patch.object(authority,'SHARED_COMMIT',commit), \
                    mock.patch.object(authority,'EXECUTABLE_PINS',pins):
                with self.assertRaisesRegex(ValueError,'SHA-256 mismatch'):
                    with authority.verified_shared(root): self.fail('unverified code was yielded')

    def test_replacement_objects_cannot_change_private_execution(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);git,commit,pins,code=self.source(root)
            (root/'scripts/good.py').write_bytes(b'raise RuntimeError("replacement executed")\n')
            git('commit','--quiet','--no-gpg-sign','-am','replacement')
            replacement=git('rev-parse','HEAD').decode().strip()
            git('checkout','--quiet','--detach',commit);git('replace',commit,replacement)
            self.assertNotEqual(git('show',commit+':scripts/good.py'),code)
            with mock.patch.object(authority,'SHARED_COMMIT',commit), \
                    mock.patch.object(authority,'EXECUTABLE_PINS',pins):
                with authority.verified_shared(root) as snapshot:
                    self.assertEqual((snapshot/'scripts/good.py').read_bytes(),code)

    def test_tag_disagreement_refuses(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);git,commit,pins,code=self.source(root)
            (root/'scripts/data.txt').write_text('later')
            git('commit','--quiet','--no-gpg-sign','-am','later')
            later=git('rev-parse','HEAD').decode().strip()
            with mock.patch.object(authority,'SHARED_COMMIT',later), \
                    mock.patch.object(authority,'EXECUTABLE_PINS',pins):
                with self.assertRaisesRegex(ValueError,'tag does not identify'):
                    with authority.verified_shared(root): self.fail('wrong tag was yielded')
