# Declared-reference advisory audit

This is FHT's consumer rollout of shared
[#241](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/241)
and [D7](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/211#issuecomment-7017854934).
It observes declarations and reports findings. It never updates a contract,
consumer pin, release, legacy identifier or file-bound header.

`schemas/provenance.json` remains the source of truth. The adapter reads it on
each run, rather than maintaining another frozen inventory: its two shared
LinkML files are selected released copies; its FHR schema is the released
contract used for V5 routing. Both resolve the explicitly declared release tag,
dereferenced commit and exact digests. The complete local `schemas/` set is
checked with the authored provenance record and separately audited FHR contract
excluded from the two-file copy group. This is a selected import scope, not a
claim to mirror the authority's whole schema directory.

The adapted FHP parser ancestry in `tests/fixtures/microdata/provenance.json`
is test-implementation provenance outside these five contract/suite/base/tree
classes. It is intentionally not assigned a fictitious byte-equal FHT target.
Same-repository schema/example/legacy checks and external pilot-data provenance
remain their owning checks, with explicit scope exclusions in the report.

## Verified engine and controlled execution

[checker.json](checker.json) pins the reviewed central checker to full commit
`6dee4c8baba723ec5cad825d521db2dbbc1921ae` and SHA-256
`d64104ed33de344c18ba93c00575cad8b16024db5b95c34ee02556b6868f543c`.
Before execution the adapter checks actual HEAD, immutable git bytes and digest;
Git replacement objects are disabled. The verified immutable bytes execute from
a private snapshot under isolated Python, so changing the working file after
verification or placing neighboring helpers cannot change executed code. An unperformed
or failed bootstrap is not scored as a successful reference comparison.

```sh
python scripts/audit_declared_references.py --checker-root /path/to/pinned-shared
python scripts/audit_declared_references.py --checker-root /path/to/pinned-shared \
  --checkout FAIR-bioHeaders/FAIR-bioHeaders-Specification=/path/to/pinned-shared
python scripts/check_reference_controls.py --checker-root /path/to/pinned-shared
```

The offline authority checkout must contain the declared release tag and commit;
missing objects or mappings are `QUERY_FAILED`, never a skipped pass. Actual
offline integration uses controlled temporary Git authorities and declarations,
not a freshness requirement on real pins. It exercises fresh fixtures, missing
metadata/local/authority files (`ABSENT`), supplied floating refs (`DRIFT`), byte
mutations and query failures, while proving real consumer pins were not written.
Fixture-only adapter tests run normally; verified-engine fixture integration is
its own explicit CI step. Missing recorded fields stay incomplete; supplied
floating values are preserved for the central checker instead of discarded.

## Scheduled/manual findings

The read-only scheduled/manual workflow queries immutable GitHub API authorities,
requires a missing-path negative control, compares actual consumer bytes and
retains an atomically written JSON report and shell-only job summary. A missing
report after checkout/Python failure receives an explicit `QUERY_FAILED` fallback. `FRESH`, `DRIFT`, `ABSENT` and
`QUERY_FAILED` remain distinct. A local comparison not run is labeled separately.
Ordinary findings leave the audit advisory; `--exit-on-findings` is used for
controlled offline integration. A bootstrap or malformed-report error fails
execution and retains an explicit failure record instead of claiming freshness.
Network audit findings are not new PR gates and never trigger automatic repins.

Staged shared FHT artifacts still cite their accepted owning snapshot. This CI
port does not advance that source pin or establish joint schema acceptance,
publication, a new alias or default toolkit support.
