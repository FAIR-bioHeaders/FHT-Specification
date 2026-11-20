# Published FHT authority and owning handoff

Current accounting: November 20, 2026. Refs #5, #8, #9, #10 and #11;
all five remain open pending their precise remaining handoffs below.

## Exact authority and preservation

FHT contract **1.0** is published in shared specification **v0.7.0**, immutable
commit `623c79fe58edeb238a20fb6de518c62dd69b92bc`:

- [GitHub Release](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/releases/tag/v0.7.0),
  release object 452203176, published November 20 at 02:42:41 UTC.
- [Version DOI 10.5281/zenodo.24385024](https://doi.org/10.5281/zenodo.24385024).
- [Actual root contract](https://raw.githubusercontent.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/v0.7.0/fht.json),
  SHA-256 `082b0790b7878940c4496c97d7485e32c65de8ba75ecc080e53f04fb44251a43`.
- [Joint package disposition](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/211#issuecomment-7025645941).

The owning source remains `4ddda69cbcbb3920a06ab657173c0198672cd7bf`,
`fht.json` SHA-256
`b62c4e227042e162b43d2c461cfe6c3ece3806636ca88a4cf9b0b2f902fb1fc3`.
Its 239 frozen inputs and 93 legacy vectors are preserved. The published shared
93 counterparts and seven JSON/FASTA/HTML example triples are separate
artifacts with an explicit crosswalk. Existing owning IDs, all fourteen
published JSON/FASTA example files, and file-bound checksums are immutable.

The published fixed selector is
`https://w3id.org/fair-bioheaders/fht/v0.7.0`; its external redirect is **not yet
live** at this checkpoint. External w3id PR 7241 awaits its owners. Actual
raw-tag retrieval above works; neither a proposed redirect nor raw retrieval
proves live w3id resolution. Alias verification remains an exact #10 dependency.

## Clause accounting against current issue bodies

| Issue and clause | Evidence now earned | Remaining artifact/dependency |
| --- | --- | --- |
| #8 examples, byte vectors, typed reference and streams | Accepted owning 93, seven typed pairs, preserved RNA/cDNA/compression/checksum/parent cases | No new corpus or fixture rewrite |
| #8 final joint acceptance | Concrete package disposition linked above | No repeat questionnaire or new curator field decision |
| #8 shared absorption and selectors | Actual v0.7.0 root contract, registry, vocabulary, binding, 93 counterparts and seven example sets | Installed published-package normal-path receipt under #9 |
| #8 current consumer readiness | C1 arithmetic-capable development-wheel evidence in ROUND15-CLOSEOUT; strict owning lane has zero NOT-RUN | Actual published toolkit receipt, not a candidate relabel |
| #9 arithmetic and supported commands | Corrected owning harness in merged #64 measures real C1 failures; development CLI evidence is recorded separately | Published package verify/validate/combine/strip/convert/assess and selector coverage; explicit unsupported surfaces |
| #9 bundle/default promotion | Shared publication is complete | Deliberate toolkit release promotion from actual published artifacts, installed wheel provenance and default 93-case receipt |
| #9 website and Nextflow handoffs | Existing owning links identify website #15 and Nextflow #7/#21 | Concrete FHT owner receipts using the supported package; website #70 head `2cf5556` prepares published forms/exports, with Pages activation awaiting the package |
| #10 final contract/binding acceptance and readiness | Joint disposition and prepublication development evidence complete | No public pilot or FHGM release prerequisite is added |
| #10 publication, archive and fixed identities | Real v0.7.0 tag, GitHub Release and version DOI above | Live fixed redirect verification and final supported-release handoffs; do not equate the tag with the Release |
| #10 docs/citations | Published authority/DOI distinguished here from preserved owning source and historical FHR citations | Final runtime/site/Nextflow receipt links when available |
| #11 final joint binding and shared integration | Released F1–F7 binding/vocabulary and counterpart examples in v0.7.0 | No compulsory JSON-LD or journal/editor copy-paste claim |
| #11 runtime and website | Reference controls and development runtime remain separately recorded | Installed released HTML extraction/writing round trips and website-owner deployment/activation receipt |
| #5 aggregate | Design, consultation, INSDC #157, joint package and shared publication complete | Exactly the outstanding #8/#9/#10/#11 acts above; aggregate closure follows them |

No scientific derivation follows from exact parent-file matching. The 83 legacy
parentless link assertions are not 83 complete parent-verification passes.
Metadata validity, checksum integrity, parent identity and biological provenance
remain distinct outcomes. Public producer/pilot rollout is outside #10's
recorded foundation boundary; FHGM publication is not an additional FHT gate.

## Two deliberately separate verification lanes

The owning lane remains `scripts/run_toolkit_lane.py --venv /absolute/venv
--strict`. It measures the immutable legacy owning V7 suite; its default-lane
rejections remain correct for those legacy selectors. The corrected #64 C1
probe must execute both arithmetic cases. Do not overlay old package schemas
and call that normal published support.

For published FHT use the existing shared **v0.7.0** checker and manifest,
semantic oracle and typed browser checks. In a clean checkout at the exact tag:

```sh
python scripts/fht_publication.py --examples
python scripts/check_conformance.py --help
```

The immutable shared CLI command table does not include FHT. Use the owning
helper below: its explicit command adapter maps the FHT-only manifest to
`bioheaders verify`, then `verify-links` with the immutable manifest
parent files when parent context exists (`--require-all` when all context
files are supplied; unavailable parents retain their unchecked outcome), retaining the shared comparison logic and oracle. Direct
`check_conformance.py --require-format fht-fasta` is unsupported at this tag.
Preserve the source-to-release crosswalk and semantic oracle.
Record installed wheel SHA-256/source provenance, actual registry/schema
pins, all 93 outcomes, seven HTML round trips, default/version selector controls
and supported commands. Execute rather than infer counts from exit status.

At this checkpoint toolkit 0.13 is **not yet published**. Published 0.12 has the
old gaps; its version string is also used by historical development wheels.
Consequently no normal published 0.13 CLI/HTML receipt or CI pin is asserted
here. The existing pinned 0.11 historical lane stays explicitly legacy. Add the
normal installed CI lane only after actual artifact publication and measurement;
keep both lanes distinct. A source-candidate pass cannot fill that cell.

## Prepared normal published CI entry point

`scripts/check_published_fht.py --shared /absolute/shared-v0.7.0` delegates
to the exact clean tag's existing source crosswalk, semantic oracle and seven
example checks. With `--venv /absolute/published-toolkit-venv` it additionally
delegates all 93 normal FHT comparisons to that tag's shared converter checker
using the explicit generic `bioheaders verify`/`verify-links` command adapter
with required FHT support, no skips or known gaps. It rejects dirty/wrong
authority checkouts and draft environment overrides. The no-venv run reports
installed comparison explicitly NOT-RUN. Its inherited
`publicationVerified: false` is intentional: a conformance run cannot prove
Release/archive publication or live aliases.

The `Published FHT authority` PR/push CI job runs this reference-only lane.
This is CI preparation, not an installed-release receipt or a replacement for
the broader supported-command, selector, HTML and owner handoffs. After the real
package is published, pin its measured version/wheel hash in the normal CI job
and call this helper alongside the existing legacy V7 job. No guessed package
version or digest is wired into CI now.

Owning main guidance `bcc6224` is integrated without fixture changes. The
v0.7.0 archive was independently verified across 1,744 files by the coordinating
release lane. Nextflow's concrete FHT handoff belongs to its owner; unrelated
external-pin/distribution completion of the whole Nextflow #7 is not a reverse
FHT release gate. Published native FHGM v0.8.0 remains a separate deliverable.

## Exercised adapter receipt (candidate only)

Independent Python 3.13 environment `/tmp/fht65-independent013` was created
from the immutable copied development wheel for Tools source
`83a61e9824b5f47bccb1cddbe7f40fb70f60ba1f`, wheel SHA-256
`0306c021d3f7a3f4e4b6547f7576cdb6332389952673a02a1587db01046f6fbe`.
Its version string is 0.13.0; this is **candidate evidence only**, not a PyPI
publication receipt. The actual installed helper run executed all 93 comparisons
with zero disagreements/unsupported formats, following the 93-case authority
check (34 valid) and seven example triples. No opt-in, schema overlay or staged
arithmetic flag was set.

The adapter checks the file with `verify`, then executes `verify-links` with
immutable supplied parents. Complete supplied parent context uses `--require-all`
so the mixed-verdict negative cannot become an unchecked success; genuinely
unavailable context stays unchecked. The manifest and shared oracle provide all
expectations. Accept-all and reject-all executable controls both fail: invalid
fixtures expose accept-all, and valid fixtures expose reject-all. Wrong-authority
and draft-opt-in controls also fail. This establishes the adapter path; actual
published-package, broader command/HTML and downstream receipts remain pending.
