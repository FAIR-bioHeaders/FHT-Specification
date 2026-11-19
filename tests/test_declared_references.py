# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. https://mozilla.org/MPL/2.0/.
"""Fixture-only controls; actual pinned-engine integration is a separate job."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("fht_reference_adapter", ROOT / "scripts/audit_declared_references.py")
adapter = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(adapter)


class DeclarationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "schemas").mkdir()
        self.record = json.loads((ROOT / adapter.RECORD).read_text())
        self.write()

    def write(self):
        (self.root / adapter.RECORD).write_text(json.dumps(self.record))

    def test_current_record_maps_three_files_to_their_actual_authority_roles(self):
        table = adapter.inventory(self.root)
        tree, contract = table["references"]
        self.assertEqual(tree["class"], "copied-tree")
        self.assertEqual(contract["class"], "released-contract")
        self.assertEqual([f["path"] for f in contract["files"]], ["fhr.json"])
        actual = {f["local"]: f for row in table["references"] for f in row["files"]}
        self.assertEqual(set(actual), set(self.record["files"]))
        for local, value in self.record["files"].items():
            self.assertEqual(actual[local]["sha256"], value["sha256"])
            self.assertEqual(actual[local]["path"], value["source_path"])
        self.assertEqual(tree["revision"], "v0.6.0")
        self.assertEqual(tree["commit"], self.record["source_commit"])

    def test_normalization_reads_changed_declarations_instead_of_a_stale_inventory(self):
        self.record["files"]["schemas/shared.yaml"]["sha256"] = "0" * 64
        self.record["source_release"] = "v0.6.1 (fixture declaration only)"
        self.write()
        table = adapter.inventory(self.root)
        tree = table["references"][0]
        self.assertEqual(tree["revision"], "v0.6.1")
        self.assertEqual(next(f for f in tree["files"] if f["local"] == "schemas/shared.yaml")["sha256"], "0" * 64)
        self.assertEqual(table["declarationRecords"][0]["sha256"], hashlib.sha256((self.root / adapter.RECORD).read_bytes()).hexdigest())

    def test_floating_release_or_missing_digest_is_not_replaced_with_old_values(self):
        self.record["source_release"] = "main"
        self.record["files"]["schemas/shared.yaml"].pop("sha256")
        self.write()
        tree = adapter.inventory(self.root)["references"][0]
        self.assertIsNone(tree["revision"])
        self.assertIsNone(next(f for f in tree["files"] if f["local"] == "schemas/shared.yaml")["sha256"])

    def test_escaping_source_or_consumer_paths_are_rejected(self):
        original = copy.deepcopy(self.record)
        for local in (False, True):
            self.record = copy.deepcopy(original)
            value = self.record["files"].pop("schemas/shared.yaml")
            if not local:
                value["source_path"] = "../outside.yaml"
            self.record["files"]["../outside.yaml" if local else "schemas/shared.yaml"] = value
            self.write()
            with self.assertRaisesRegex(ValueError, "unsafe declaration path"):
                adapter.inventory(self.root)


class BootstrapTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "scripts").mkdir()
        self.source = self.root / "scripts/check_references.py"
        self.source.write_text("raise RuntimeError('fixture must never execute')\n")
        self.git("init", "-q")
        self.git("config", "user.name", "Reference control")
        self.git("config", "user.email", "reference@example.invalid")
        self.git("add", ".")
        self.git("commit", "-qm", "control source")
        self.metadata = {"repository": adapter.AUTHORITY, "commit": self.git("rev-parse", "HEAD").decode().strip(),
                         "path": "scripts/check_references.py", "sha256": hashlib.sha256(self.source.read_bytes()).hexdigest()}

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.root), *args], stderr=subprocess.DEVNULL)

    def test_verified_source_is_returned_without_executing_it(self):
        self.assertEqual(adapter.verify_checker(self.root, self.metadata), self.source.resolve())

    def test_wrong_head_or_changed_checker_bytes_fail_bootstrap(self):
        bad = dict(self.metadata, commit="0" * 40)
        with self.assertRaisesRegex(ValueError, "HEAD"):
            adapter.verify_checker(self.root, bad)
        self.source.write_bytes(self.source.read_bytes() + b"# changed\n")
        with self.assertRaisesRegex(ValueError, "immutable source/digest"):
            adapter.verify_checker(self.root, self.metadata)

    def test_workflow_uses_the_declared_engine_commit_in_both_lanes(self):
        metadata = json.loads((ROOT / "references/checker.json").read_text())
        workflow = (ROOT / ".github/workflows/declared-references.yml").read_text()
        self.assertEqual(workflow.count("ref: " + metadata["commit"]), 2)
        self.assertIn("contents: read", workflow)
        self.assertIn("workflow_dispatch:", workflow)


if __name__ == "__main__":
    unittest.main()
