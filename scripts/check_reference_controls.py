#!/usr/bin/env python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. https://mozilla.org/MPL/2.0/.
"""Actual verified engine on controlled fixture authorities, never PR freshness gates."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

from audit_declared_references import AUTHORITY, ROOT, audit


def fixed_record(commit, content):
    return {"source_repository": "https://github.com/" + AUTHORITY,
            "source_commit": commit, "source_release": "v9.9.9 (controlled fixture)",
            "files": {local: {"source_path": source,
                              "sha256": hashlib.sha256(content[source]).hexdigest()}
                      for local, source in (("schemas/core-fixture.yaml", "schemas/core.yaml"),
                                            ("schemas/shared.yaml", "schemas/shared.yaml"),
                                            ("schemas/fhr-fixture.json", "fhr.json"))}}


def run_controls(checker_root):
    before = {name: (ROOT / name).read_bytes() if (ROOT / name).is_file() else None for name in (
        "schemas/provenance.json", "schemas/core-v0.4.yaml", "schemas/shared.yaml",
        "schemas/fhr-v0.6.0.json", "references/checker.json")}
    with tempfile.TemporaryDirectory(prefix="fht-reference-controls-") as work:
        base = Path(work)
        authority, root = base / "authority", base / "consumer"
        authority.mkdir()
        content = {"schemas/core.yaml": b"fixture core\n", "schemas/shared.yaml": b"fixture shared\n",
                   "fhr.json": b'{"fixture":"released contract"}\n'}
        def git(*args):
            return subprocess.check_output(["git", "-C", str(authority), *args], stderr=subprocess.DEVNULL)
        git("init", "-q")
        git("config", "user.name", "Declared-reference fixture")
        git("config", "user.email", "reference@example.invalid")
        for name, raw in content.items():
            target = authority / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
        git("add", ".")
        git("commit", "-qm", "fixed controlled authority")
        commit = git("rev-parse", "HEAD").decode().strip()
        git("tag", "v9.9.9")
        original = fixed_record(commit, content)
        (root / "schemas").mkdir(parents=True)
        (root / "references").mkdir()
        (root / "references/checker.json").write_bytes((ROOT / "references/checker.json").read_bytes())
        mappings = [AUTHORITY + "=" + str(authority)]
        for local, entry in original["files"].items():
            (root / local).write_bytes(content[entry["source_path"]])
        def execute(record=None, mapping=None):
            (root / "schemas/provenance.json").write_text(json.dumps(original if record is None else record))
            return audit(checker_root, mappings if mapping is None else mapping, root=root, strict=True)
        def verdict(report, cls):
            return next(r["verdict"] for r in report["references"] if r["class"] == cls)
        fresh, status = execute()
        assert status == 0 and all(r["verdict"] == "FRESH" and r["localComparison"] == "performed"
                                  for r in fresh["references"])
        for field in ("source_commit", "source_release"):
            incomplete = copy.deepcopy(original)
            incomplete.pop(field)
            report, status = execute(incomplete)
            assert status == 1 and all(r["verdict"] == "ABSENT" for r in report["references"])
        floating = dict(original, source_release="main")
        report, status = execute(floating)
        assert status == 1 and all(r["verdict"] == "DRIFT" for r in report["references"])
        for field in ("source_path", "sha256"):
            incomplete = copy.deepcopy(original)
            incomplete["files"]["schemas/shared.yaml"].pop(field)
            report, status = execute(incomplete)
            assert status == 1 and verdict(report, "copied-tree") == "ABSENT"
        contract = root / "schemas/fhr-fixture.json"
        contract.write_bytes(contract.read_bytes() + b" ")
        report, status = execute()
        assert status == 1 and verdict(report, "released-contract") == "DRIFT"
        contract.unlink()
        report, status = execute()
        assert status == 1 and verdict(report, "released-contract") == "ABSENT"
        contract.write_bytes(content["fhr.json"])
        core = root / "schemas/core-fixture.yaml"
        core.unlink()
        report, status = execute()
        assert status == 1 and verdict(report, "copied-tree") == "ABSENT"
        core.write_bytes(content["schemas/core.yaml"])
        report, status = execute(mapping=["unknown/authority=" + work])
        assert status == 1 and all(r["verdict"] == "QUERY_FAILED" for r in report["references"])
        # Separate authority absence from local absence: the controlled tag and
        # recorded commit deliberately advance together, with one source absent.
        (authority / "schemas/shared.yaml").unlink()
        git("add", "-u")
        git("commit", "-qm", "controlled missing authority import")
        git("tag", "-f", "v9.9.9")
        missing = dict(original, source_commit=git("rev-parse", "HEAD").decode().strip())
        report, status = execute(missing)
        assert status == 1 and verdict(report, "copied-tree") == "ABSENT"
    assert all(((ROOT / name).read_bytes() if (ROOT / name).is_file() else None) == raw
               for name, raw in before.items())
    return {"engine": "actual verified source; temporary fixture authorities only",
            "freshFixtureGroups": 2, "incomplete": "ABSENT", "floating": "DRIFT",
            "mutation": "DRIFT", "missingContract": "ABSENT", "missingLocalImport": "ABSENT",
            "missingAuthorityImport": "ABSENT", "unmappedAuthority": "QUERY_FAILED", "pinWrites": []}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checker-root", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run_controls(args.checker_root), indent=2))


if __name__ == "__main__":
    main()
