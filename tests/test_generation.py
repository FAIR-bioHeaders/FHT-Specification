"""Check that the committed FHT schema matches the LinkML model."""

import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load_generator():
    spec = importlib.util.spec_from_file_location(
        "fht_generator", ROOT / "json-schema-generator.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class GenerationTests(unittest.TestCase):
    def test_committed_schema_matches_the_model(self):
        generated = load_generator().generate()
        committed = json.loads((ROOT / "fht.json").read_text(encoding="utf-8"))
        self.assertEqual(committed, generated)

    def test_pinned_imports_match_provenance(self):
        spec = importlib.util.spec_from_file_location(
            "check_provenance", ROOT / "scripts" / "check_provenance.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual(module.main(), 0)


if __name__ == "__main__":
    unittest.main()
