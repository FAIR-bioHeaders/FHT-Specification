# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. https://mozilla.org/MPL/2.0/.
"""Fixture-only controls; actual pinned-engine integration is a separate job."""
import copy
import os
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

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
        self.record = {"source_repository": "https://github.com/" + adapter.AUTHORITY,
                       "source_commit": "a" * 40, "source_release": "v0.6.0 (fixed fixture)",
                       "files": {"schemas/core-v0.4.yaml": {"source_path": "schemas/core.yaml", "sha256": "1" * 64},
                                 "schemas/shared.yaml": {"source_path": "schemas/shared.yaml", "sha256": "2" * 64},
                                 "schemas/fhr-v0.6.0.json": {"source_path": "fhr.json", "sha256": "3" * 64}}}
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
        self.assertEqual(tree["revision"], "main")
        self.assertEqual(tree["revisionKind"], "branch")
        self.assertIsNone(next(f for f in tree["files"] if f["local"] == "schemas/shared.yaml")["sha256"])

    def test_missing_commit_or_source_path_stays_an_identifiable_incomplete_declaration(self):
        self.record.pop("source_commit")
        self.record["files"]["schemas/shared.yaml"].pop("source_path")
        self.write()
        tree, contract = adapter.inventory(self.root)["references"]
        self.assertEqual(tree["revision"], "v0.6.0")
        self.assertIsNone(tree["commit"])
        self.assertIsNone(next(f for f in tree["files"] if f["local"] == "schemas/shared.yaml")["path"])
        self.assertEqual(contract["class"], "released-contract")

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
        self.assertEqual(adapter.verify_checker(self.root, self.metadata), self.source.read_bytes())

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

    def test_replacement_refs_and_working_bytes_cannot_spoof_the_immutable_script(self):
        original = self.metadata["commit"]
        changed = b"raise RuntimeError('replacement must not be trusted')\n"
        self.source.write_bytes(changed)
        self.git("add", ".")
        self.git("commit", "-qm", "replacement script")
        replacement = self.git("rev-parse", "HEAD").decode().strip()
        self.git("checkout", "-q", "--detach", original)
        self.git("replace", original, replacement)
        environment = dict(os.environ)
        environment.pop("GIT_NO_REPLACE_OBJECTS", None)
        self.assertEqual(subprocess.check_output(
            ["git", "-C", str(self.root), "show", original + ":scripts/check_references.py"],
            env=environment), changed)
        self.source.write_bytes(changed)
        spoofed = dict(self.metadata, sha256=hashlib.sha256(changed).hexdigest())
        with self.assertRaisesRegex(ValueError, "immutable source/digest"):
            adapter.verify_checker(self.root, spoofed)

    def test_execution_uses_verified_snapshot_even_when_working_file_changes(self):
        code = ("import json\nprint(json.dumps({'verifiedSnapshot': True, 'references': ["
                "{'id':'one','verdict':'ABSENT'},{'id':'two','verdict':'ABSENT'}]}))\n")
        self.source.write_text(code)
        self.git("add", "scripts/check_references.py")
        self.git("commit", "-qm", "verified execution fixture")
        self.metadata.update(commit=self.git("rev-parse", "HEAD").decode().strip(),
                             sha256=hashlib.sha256(self.source.read_bytes()).hexdigest())
        consumer = self.root / "consumer"
        (consumer / "references").mkdir(parents=True)
        (consumer / "schemas").mkdir()
        (consumer / "references/checker.json").write_text(json.dumps(self.metadata))
        (consumer / "schemas/provenance.json").write_text(json.dumps({
            "source_repository": "https://github.com/" + adapter.AUTHORITY,
            "source_commit": "a" * 40, "source_release": "v0.6.0", "files": {}}))
        marker = self.root / "unverified-executed"
        evil = "from pathlib import Path\nPath(" + repr(str(marker)) + ").write_text('bad')\nraise RuntimeError('unverified')\n"
        (self.root / "scripts/json.py").write_text(evil)
        original_run = subprocess.run
        swapped = []
        def swap_then_run(command, *args, **kwargs):
            if command[0] == adapter.sys.executable:
                self.source.write_text(evil)
                swapped.append(True)
            return original_run(command, *args, **kwargs)
        with patch.object(adapter.subprocess, "run", side_effect=swap_then_run):
            report, status = adapter.audit(self.root, root=consumer)
        self.assertTrue(swapped)
        self.assertEqual(status, 0)
        self.assertTrue(report["verifiedSnapshot"])
        self.assertFalse(marker.exists())


class WorkflowFallbackTests(unittest.TestCase):
    def test_setup_failure_has_json_and_summary_without_python_setup(self):
        import yaml
        steps = yaml.safe_load((ROOT / ".github/workflows/declared-references.yml").read_text())["jobs"]["advisory"]["steps"]
        fallback = next(s["run"] for s in steps if s.get("name") == "Record an unperformed audit")
        summary = next(s["run"] for s in steps if s.get("name") == "Surface the advisory result")
        with tempfile.TemporaryDirectory() as work:
            summary_file = Path(work) / "summary.md"
            subprocess.run(["bash", "-e", "-c", "python() { return 127; }\n" + fallback + "\n" + summary],
                           check=True, env={**os.environ, "RUNNER_TEMP": work, "GITHUB_STEP_SUMMARY": str(summary_file)})
            report = json.loads((Path(work) / "fht-reference-audit.json").read_text())
            self.assertEqual(report["references"][0]["verdict"], "QUERY_FAILED")
            self.assertEqual(report["references"][0]["localComparison"], "not-run")
            self.assertIn("QUERY_FAILED", summary_file.read_text())


if __name__ == "__main__":
    unittest.main()
