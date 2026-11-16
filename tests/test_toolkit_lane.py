"""Controls for the installed-artifact harness, independent of a toolkit install."""
import contextlib
import io
import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location(
    "toolkit_lane", Path(__file__).resolve().parents[1] / "scripts/run_toolkit_lane.py"
)
lane = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(lane)


class StreamControls(unittest.TestCase):
    def setUp(self):
        lane.FAILURES.clear()

    def test_empty_stream_lane_is_a_failure(self):
        with contextlib.redirect_stdout(io.StringIO()):
            lane.lane_streams(None, [], None)
        self.assertIn("zero cases", lane.FAILURES[0])

    def test_corrupt_stdout_is_not_hidden_by_success_exit(self):
        vector = {"id": "control", "file": "valid/control.fasta", "expected": "valid"}

        class BrokenToolkit:
            def run_bytes(self, *args, **kwargs):
                return subprocess.CompletedProcess(args, 0, b"corrupted", b"diagnostic")

            def run(self, *args, **kwargs):
                return 1, "setup deliberately unavailable"

        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(Path, "read_bytes", return_value=b">id\nAC\n"), \
                    patch.object(lane, "place", return_value=Path(tmp) / "input"):
                with contextlib.redirect_stdout(io.StringIO()):
                    lane.lane_streams(BrokenToolkit(), [vector], tmp)
        self.assertTrue(any("strip changed payload" in x for x in lane.FAILURES))

    def test_named_toolkit_default_cannot_accept_fht(self):
        class IncorrectDefault:
            def version(self):
                return "0.11.0"

            def run(self, *args, **kwargs):
                return 0, "Checksum verified."

        with patch.object(lane, "place", return_value=Path("unused")), \
                contextlib.redirect_stdout(io.StringIO()):
            lane.lane_default_path(IncorrectDefault(), [{"id": "control"}], None)
        self.assertIn("draft lane disabled", lane.FAILURES[0])

    def test_binary_transport_keeps_diagnostic_stderr_separate(self):
        with tempfile.TemporaryDirectory() as tmp:
            binary = Path(tmp) / "bin/bioheaders"
            binary.parent.mkdir()
            binary.touch()
            toolkit = lane.Toolkit(tmp)
            result = subprocess.CompletedProcess([], 0, b"payload\r\n", b"warning\n")
            with patch.object(lane.subprocess, "run", return_value=result) as run:
                actual = toolkit.run_bytes("strip", "-", "-", data=b"input\r\n")
            self.assertEqual(actual.stdout, b"payload\r\n")
            self.assertEqual(run.call_args.kwargs["input"], b"input\r\n")
            self.assertEqual(run.call_args.kwargs["timeout"], 60)
            self.assertNotIn("text", run.call_args.kwargs)


if __name__ == "__main__":
    unittest.main()
