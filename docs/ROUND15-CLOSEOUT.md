# FHT owning closeout preparation — Round 15, November 19, 2026

> Current publication status (November 20, 2026): shared v0.7.0 publishes FHT
> contract 1.0 and its typed binding. The dated draft/candidate receipts below
> describe the preserved owning V7 source, not normal published support.
> [Published handoff and clause matrix](FHT-PUBLISHED-HANDOFF.md) supersedes
> their prospective release gates; actual installed-release and downstream
> receipts remain separately required.

This record prepares the final #8/#9/#10/#11 handoff. It does not publish FHT,
replace a released contract, or close an issue whose release/consumer acts are
still outstanding. The owning model/schema remain accepted commit
`4ddda69cbcbb3920a06ab657173c0198672cd7bf` (schema SHA-256
`b62c4e227042e162b43d2c461cfe6c3ece3806636ca88a4cf9b0b2f902fb1fc3`).
The 93-vector source bytes, IDs, outcomes and dated receipts remain unchanged.

David accepted the reviewed shared #281 package and later stated “I can speak
for Adam on this, he approves” in the coordinating chat, recorded in
[shared #211 comment 7025645941](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/211#issuecomment-7025645941).
That is joint package acceptance recorded through the operating agent, not a
fabricated native human PR review. The package is merged into shared main via
[#281](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/pull/281).
Neither acceptance nor merge supplies a tag, GitHub Release, archive DOI or
working immutable alias. The selected publication remains shared **v0.7.0**,
FHT contract **1.0**, following the separate v0.6.1 guidance stage.

## Installed semantic capability versus generic JSON Schema

The old installed harness partitioned the two complete-count arithmetic cases
as unsupported because generic JSON Schema accepted their records. A correct
installed toolkit now rejects them through its separate C1 semantic check; the
old preflight therefore incorrectly stopped with NOTHING SCORED. That old
receipt is retained as evidence of the harness defect, not a consumer failure
or a passing 93-case readiness claim.

The corrected harness probes both immutable case IDs against the actual
installed executable. A single specific C1 completeness-sum diagnostic with
exit 1, without checksum failure or an unrelated schema error, places each
case in ordinary normative comparisons. Generic schema validity alone cannot
infer runtime arithmetic support. The complete ordinary lane then rechecks
those failures and runs the existing verification, links, default-lane,
strip/combine and stdin/stdout controls. No unsupported case is relabeled valid
and no source vector changes.

Older installed runtimes that actually accept these schema-valid records still
report them as unsupported/not-run; the explicit old 0.11.0 staging procedure
is preserved. The current-capability run uses **neither** schema overlay nor
`--stage-completeness`. Unrelated rejection, checksum failure, missing output or
zero executed cases are not proof of semantic support.

## Acceptance and remaining acts

| Ticket | Earned evidence | Remaining act before complete closure |
| --- | --- | --- |
| #8 | Accepted owning 93-vector package, exact shared absorption, joint package disposition; current installed semantic/read/write evidence recorded separately | Actual release-time absorption/selection and final named consumer receipts |
| #9 | Current candidate implements both arithmetic controls; corrected installed executable harness measures all supported operations without missing-case staging | Actual shared publication, deliberate published bundle/default promotion and installed release receipts; concrete website/Nextflow handoffs |
| #10 | Joint reviewed FHT 1.0/shared v0.7.0 package selected and merged; historical/pilot boundaries retained | Real immutable tag, GitHub Release, actual alias/archive/citation evidence and supported-release documentation |
| #11 | Accepted F1–F7 binding, seven paired reference examples and shared vocabulary/conformance preparation; actual candidate HTML round trips belong to the toolkit receipt | Released binding/selector support, named installed release HTML receipt and website-owner handoff |

The public pilot/full-producer program remains outside the #10 release gate.
JSON-LD, journal/editor copy-paste and biological derivation are not inferred.
Exact parent-file matching, checksum integrity, model validity and curator
acceptance remain separate. No shared fixture mirror is silently repinned to a
new harness commit: this code fix changes consumer measurement, not the
accepted contract/source fixture authority.

## Reproduce the current candidate lane

Use the actual noneditable candidate toolkit environment identified on the PR:

```sh
python scripts/run_toolkit_lane.py --venv /absolute/path/to/candidate-venv --strict
```

Its installed version string alone does not establish publication: record the
wheel/source commit and schema/suite pins beside the output. Full current-head
CI and independent different-model review remain necessary. Exact execution
counts and limitations are recorded on the PR after the run finishes; an old
91-case/two-not-run receipt is never silently rewritten into 93 comparisons.

### Measured current candidate receipt

The noneditable installed candidate wheel (Tools source head `297cf1d`, version
string 0.12.0) has SHA-256
`68b06289a7838b3118f09e4d9f9571cce7fc36e78a620947d3a0d1efa8d8d073`:
62 installed package payload files were byte-compared with that wheel, and
all 62 wheel payloads were independently compared with source commit Git blobs:
zero disagreements. This is a development wheel, not the published PyPI 0.12.0
artifact. With no overlay and no staging flag, the strict lane produced:

- 93 implementation comparisons; 34 valid accepted, 59 invalid rejected;
- zero current-contract unsupported/not-run and zero staged C1 cases;
- ten parent-link vectors, with matched/mismatched/not-checked kept distinct;
- zero of 93 FHT vectors accepted with the V7 lane disabled;
- 34 byte-preserving strips and 34 value/order/type-preserving combines;
- actual stdin/stdout controls: 93 verifies, 34 strips and 34 combines.

Owning Python 3.15 verification ran 129 tests with zero failures/errors/skips,
including 15 harness controls. Independent fixture validation passed all
34 valid / 59 invalid vectors, including both C1 cases. Documentation, shared
import provenance and preserved legacy checks passed. An earlier attempt to
run the full owning suite through the candidate's Python 3.12 runtime failed
two environment prerequisites (Path.read_text newline support and generation
dependencies); it is not a passing owning-suite receipt. The installed CLI
behavior measured above intentionally remains that real Python 3.12 candidate.
