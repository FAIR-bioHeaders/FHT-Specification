#!/usr/bin/env python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. https://mozilla.org/MPL/2.0/.
"""Audit FHT's actual declared release imports without writing any pin."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
CONSUMER = "FAIR-bioHeaders/FHT-Specification"
AUTHORITY = "FAIR-bioHeaders/FAIR-bioHeaders-Specification"
RECORD = "schemas/provenance.json"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def relative(value):
    item = PurePosixPath(value)
    if not value or item.is_absolute() or ".." in item.parts:
        raise ValueError("unsafe declaration path")
    return str(item)


def inventory(root=ROOT):
    raw = (root / RECORD).read_bytes()
    record = json.loads(raw)
    if record["source_repository"].removesuffix(".git").rstrip("/") != "https://github.com/" + AUTHORITY:
        raise ValueError("declared source repository is not the shared publication authority")
    match = re.match(r"^(v[0-9]+\.[0-9]+\.[0-9]+)(?: |$)", record.get("source_release", ""))
    revision = match.group(1) if match else None
    common = {"consumer": CONSUMER, "record": RECORD, "repository": AUTHORITY,
              "revision": revision, "revisionKind": "tag", "commit": record.get("source_commit")}
    imports, contracts = [], []
    for local, declaration in record["files"].items():
        item = {"local": relative(local),
                "path": relative(declaration["source_path"]) if declaration.get("source_path") else None,
                "sha256": declaration.get("sha256")}
        (contracts if item["path"] == "fhr.json" else imports).append(item)
    # These are the declared selected imports, not a claim to mirror every file
    # in the authority's schemas directory. FHR is audited separately by role.
    tree = {**common, "id": "fht-shared-model-imports", "class": "copied-tree",
            "materialStatus": "released", "files": imports,
            "sourcePatterns": [f["path"] for f in imports], "localTree": "schemas",
            "localExclusions": [RECORD] + [f["local"] for f in contracts]}
    contract = {**common, "id": "fht-v5-fhr-contract", "class": "released-contract", "files": contracts}
    return {"inventoryVersion": 1, "advisory": True,
            "declarationRecords": [{"path": RECORD, "sha256": digest(raw)}],
            "references": [tree, contract], "coverageGaps": [
                {"record": "tests/fixtures/microdata/provenance.json",
                 "disposition": "Adapted FHP parser ancestry is test-implementation provenance, not a byte-copied contract/suite. Owning provenance tests remain authoritative; no fictitious local equality mapping."},
                {"scope": "Same-repository schema/example/legacy digests and external pilot datasets",
                 "disposition": "Outside the five cross-repository contract/suite/base/tree classes; native owning checks are retained."}]}


def verify_checker(checkout, metadata):
    checkout = checkout.resolve()
    if metadata["repository"] != AUTHORITY or not re.fullmatch(r"[0-9a-f]{40}", metadata["commit"]):
        raise ValueError("invalid checker source pin")
    head = subprocess.check_output(["git", "-C", str(checkout), "rev-parse", "HEAD"]).decode().strip()
    if head != metadata["commit"]:
        raise ValueError("checker checkout HEAD does not match the declared source commit")
    name = relative(metadata["path"])
    source = checkout / name
    raw = source.read_bytes()
    immutable = subprocess.check_output(["git", "-C", str(checkout), "show", f"{head}:{name}"])
    if source.is_symlink() or raw != immutable or digest(raw) != metadata["sha256"]:
        raise ValueError("checker file does not match its immutable source/digest")
    return source


def audit(checkout, mappings=(), root=ROOT, strict=False):
    metadata = json.loads((root / "references/checker.json").read_text())
    checker = verify_checker(checkout, metadata)
    table = inventory(root)
    with tempfile.TemporaryDirectory(prefix="fht-declared-references-") as work:
        generated = Path(work) / "inventory.json"
        generated.write_text(json.dumps(table, indent=2) + "\n")
        command = [sys.executable, "-I", str(checker), "--inventory", str(generated),
                   "--consumer", CONSUMER, "--consumer-root", str(root.resolve())]
        for mapping in mappings:
            command.extend(["--checkout", mapping])
        # Isolated Python does not import neighboring unverified helper modules.
        result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode or not result.stdout.strip():
        raise RuntimeError("verified checker failed to produce an advisory report: " + result.stderr.strip())
    report = json.loads(result.stdout)
    if len(report.get("references", [])) != len(table["references"]):
        raise RuntimeError("checker did not report every declared reference group")
    report.update(consumer=CONSUMER, checkerSource=metadata,
                  declarationRecords=table["declarationRecords"])
    return report, int(strict and any(row["verdict"] != "FRESH" for row in report["references"]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checker-root", type=Path, required=True)
    parser.add_argument("--checkout", action="append", default=[], metavar="OWNER/REPO=PATH")
    parser.add_argument("--exit-on-findings", action="store_true", help="controlled offline check; scheduled audit stays advisory")
    args = parser.parse_args()
    try:
        report, status = audit(args.checker_root, args.checkout, strict=args.exit_on_findings)
    except FileNotFoundError as exc:
        missing_declaration = bool(exc.filename) and Path(exc.filename).resolve() == (ROOT / RECORD).resolve()
        report = {"advisory": True, "wrote": [], "references": [{"id": "fht-declarations",
                  "verdict": "ABSENT" if missing_declaration else "QUERY_FAILED",
                  "localComparison": "not-run", "reason": str(exc)}]}
        status = int(args.exit_on_findings) if missing_declaration else 1
    except (ValueError, KeyError, TypeError, AttributeError, OSError, subprocess.SubprocessError, RuntimeError) as exc:
        report = {"advisory": True, "wrote": [], "references": [{"id": "fht-audit-bootstrap",
                  "verdict": "QUERY_FAILED", "localComparison": "not-run", "reason": str(exc)}]}
        status = 1
    print(json.dumps(report, indent=2))
    return status


if __name__ == "__main__":
    raise SystemExit(main())
