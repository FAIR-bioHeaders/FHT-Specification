"""Failed toolkit prerequisites and timeouts cannot become scored rejections."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import run_toolkit_lane as lane
import check_fht_fixtures as fixtures


class LaneSafetyTests(unittest.TestCase):
    def tearDown(self):
        lane.FAILURES.clear();lane.FINDINGS.clear();fixtures.FAILURES.clear()

    def test_missing_registry_returns_nothing_scored_instead_of_dereferencing_none(self):
        fake=mock.Mock()
        fake.version.return_value='0.11.0';fake.site_packages.return_value=None
        with mock.patch.object(lane,'Toolkit',return_value=fake), \
                mock.patch.object(lane,'load_suite') as load:
            self.assertEqual(lane.main(['--venv','/not-installed']),1)
            load.assert_not_called()

    def test_timeout_aborts_instead_of_becoming_a_vector_rejection(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'bin').mkdir();(root/'bin/bioheaders').write_text('placeholder')
            toolkit=lane.Toolkit(root)
            with mock.patch.object(lane.subprocess,'run',side_effect=subprocess.TimeoutExpired('reader',60)):
                with self.assertRaisesRegex(SystemExit,'NOTHING SCORED'):
                    toolkit.run_bytes('verify','some-file')

    def test_crash_and_silent_failure_never_become_invalid_verdicts(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'bin').mkdir();(root/'bin/bioheaders').write_text('placeholder')
            toolkit=lane.Toolkit(root)
            for code, out in [(1,b'Traceback (most recent call last):\ncrash'),
                              (1,b''),(-9,b'killed')]:
                result=subprocess.CompletedProcess(['reader'],code,b'',out)
                with self.subTest(code=code,out=out), \
                        mock.patch.object(lane.subprocess,'run',return_value=result):
                    with self.assertRaisesRegex(SystemExit,'NOTHING SCORED'):
                        toolkit.run_bytes('verify','invalid-file')

    def test_added_contract_vector_without_expectation_is_reported(self):
        vectors=[{'id':key,'expected':'invalid','rule':'C1'}
                 for key in set(fixtures.EXPECTED_SCHEMA_ERRORS)|set(fixtures.EXPECTED_SEMANTIC_ERRORS)]
        vectors.append({'id':'new-contract-without-oracle','expected':'invalid','rule':'C1'})
        fixtures.lane_expectation_table(vectors)
        self.assertTrue(any('new-contract-without-oracle' in str(item) for item in fixtures.FAILURES))
