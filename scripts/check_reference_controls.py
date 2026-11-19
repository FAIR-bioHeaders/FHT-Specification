#!/usr/bin/env python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. https://mozilla.org/MPL/2.0/.
"""Actual pinned-engine offline controls; missing authority is never a skip."""
import argparse
import json
from pathlib import Path
import shutil
import tempfile

from audit_declared_references import AUTHORITY, ROOT, audit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checker-root", type=Path, required=True)
    args = parser.parse_args()
    mappings = [AUTHORITY + "=" + str(args.checker_root.resolve())]
    before = {name: (ROOT / name).read_bytes() for name in (
        "schemas/provenance.json", "schemas/core-v0.4.yaml", "schemas/shared.yaml",
        "schemas/fhr-v0.6.0.json", "references/checker.json")}
    report, status = audit(args.checker_root, mappings, strict=True)
    assert status == 0 and len(report["references"]) == 2
    assert all(row["verdict"] == "FRESH" and row["localComparison"] == "performed"
               and row["negativeControl"] == "confirmed-missing" for row in report["references"])
    with tempfile.TemporaryDirectory(prefix="fht-reference-controls-") as work:
        root = Path(work)
        shutil.copytree(ROOT / "schemas", root / "schemas")
        (root / "references").mkdir()
        shutil.copyfile(ROOT / "references/checker.json", root / "references/checker.json")
        target = root / "schemas/fhr-v0.6.0.json"
        target.write_bytes(target.read_bytes() + b" ")
        mutated, status = audit(args.checker_root, mappings, root=root, strict=True)
        assert status == 1
        assert next(r for r in mutated["references"] if r["class"] == "released-contract")["verdict"] == "DRIFT"
        target.unlink()
        missing, status = audit(args.checker_root, mappings, root=root, strict=True)
        assert status == 1
        assert next(r for r in missing["references"] if r["class"] == "released-contract")["verdict"] == "ABSENT"
        failed, status = audit(args.checker_root, ["unknown/authority=" + work], root=root, strict=True)
        assert status == 1 and all(r["verdict"] == "QUERY_FAILED" for r in failed["references"])
    assert all((ROOT / name).read_bytes() == raw for name, raw in before.items())
    print(json.dumps({"engine": "actual verified pinned source", "freshGroups": 2,
                      "mutation": "DRIFT", "missingLocal": "ABSENT",
                      "unmappedAuthority": "QUERY_FAILED", "pinWrites": []}, indent=2))


if __name__ == "__main__":
    main()
