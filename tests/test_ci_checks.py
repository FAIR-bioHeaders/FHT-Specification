"""Wire the issue #14 CI scripts into the existing unittest lane.

The scripts are the authoritative implementations (they print the actionable
per-finding reports CI shows); these tests import and run their ``main()`` so
``python -m unittest discover -s tests`` — used locally and by
.github/workflows/validate-specification.yml — also covers documentation
hygiene, legacy-draft schema health and the classified legacy examples.

The external-link lane (scripts/check_external_links.py) is intentionally NOT
tested here: it needs the network and is scheduled/manual, never a PR signal.

Local usage (pinned environment; see docs/CI.md):

    python -m pip install -r requirements-validation.txt
    python -m unittest tests.test_ci_checks -v
"""

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CiCheckTests(unittest.TestCase):
    def test_owned_documentation_checks_pass(self):
        with self.subTest("local links, whitespace and conflict markers"):
            self.assertEqual(load("check_docs").main([]), 0)

    def test_legacy_schema_health_passes(self):
        self.assertEqual(load("check_legacy_schema").main(), 0)

    def test_legacy_examples_and_fixtures_match_classification(self):
        self.assertEqual(load("check_legacy_examples").main(), 0)


if __name__ == "__main__":
    unittest.main()
