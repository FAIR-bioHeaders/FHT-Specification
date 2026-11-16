# FHT prepublication evidence and decisions

Dated 2026-11-16; refs FHT-Specification #8, #9 and #10, and shared
FAIR-bioHeaders-Specification #211. This packet prepares review. It neither
changes acceptance criteria nor closes an issue, approves a candidate, publishes
FHT, or establishes default toolkit support. FHT remains an unreleased draft.

## Acceptance accounting

The seven rows below follow [#8](https://github.com/FAIR-bioHeaders/FHT-Specification/issues/8)
and its [per-box evidence](https://github.com/FAIR-bioHeaders/FHT-Specification/issues/8#issuecomment-6904199033).
The committed suite currently contains 72 vectors (28 valid, 44 invalid).
Four carry `promotion: candidate-unreviewed`; executing them does not approve them.

| #8 box | Existing evidence and this packet | Remaining gate |
| --- | --- | --- |
| 1 examples for three construction types | Six minimal/rich stems, JSON/YAML/FASTA; `tests/test_examples.py` and fixture checker validate and recompute checksums | Existing evidence; no new example claim |
| 2 typed serializations | JSON/YAML/embedded FASTA; JSON-LD and HTML explicitly unsupported | #11 owns reviewed HTML binding; no unsupported format is passed here |
| 3 byte-level vectors and streams | Existing U/T, line endings, comments, checksums and compressed vectors; installed lane now exercises actual stdin/stdout | Shared-manifest absorption and any shared vocabulary decision remain publication work; these process checks add no normative vector |
| 4 strip/combine/conversion preservation | Independent payload expectation, metadata values/order/types and recomputed output verification; actual stream payload stdout is compared as bytes | Default-path acceptance belongs to #9 after publication; canonical header regeneration is not whole-file identity |
| 5 parent outcomes | Existing matching, mismatching and unavailable cases, with distinct exit/report checks | Four added candidate expectations still need independent review |
| 6 version selection and reviewed expectations | Existing V1/V5/V7 cases and documented release-time V4 asymmetry | Independent reviewer must disposition candidates; no marker is removed here |
| 7 named toolkit and shared checks | `run_toolkit_lane.py` against installed 0.11.0; separate Linux CI job; independent fixture/model/provenance gates retained | Shared FHT format does not exist before publication; installed 0.11.0 bundles an older draft, whose digest is printed, not silently substituted |

The installed lane executes all 72 candidate-inclusive cases as **implementation
comparisons**, not 72 independently approved acceptance cases. Its expected
outcomes remain unchanged. The printed toolkit identity and draft-byte digests
bound the comparison: agreement with 0.11.0 is not proof about every change to the
current draft contract. Default-path behavior is reported separately with the
lane disabled. The independent job regenerates into a scratch tree and compares
committed bytes; it does not depend on the toolkit job.

## Independent review request

The derivation author must not approve their own expectations. The following is
a review agenda, not a sign-off. Inspect the bytes, cited clauses and existing
`promotionCandidates` record in `conformance/manifest.json` before deciding.

| Candidate suffix (`fht-fasta-`) | Proposed rule derivation | Question for independent reader |
| --- | --- | --- |
| `parent-subset-citing-whole` | C1/FR-007 permits the parent pair; C3 compares the supplied parent digest, not biological subset coverage | Does checked-pass establish only cited file identity, leaving the derivation claim unverified? |
| `parent-real-digest-wrong-file` | C3 compares the stated digest against the supplied subset file, not any known file with that digest | Confirm verify succeeds for the child while verify-links reports checked-fail, not unchecked |
| `parent-masked-exact` | R1 covers exact case-sensitive bytes; C3 matches the masked parent's own digest | Confirm the stated parent digest independently and checked-pass without case normalization |
| `parent-case-folded-digest` | The original and masked parent have different header and sequence bytes; R1/C3 compare the actual supplied file | Confirm checked-fail; this fixture alone does not isolate sequence-case changes from header changes |

Sources: the draft [FR-007](../specs/005-rna-transcriptome-header/spec.md),
[C1-C3 and absorption notes](../conformance/README.md), and shared
[FORMAT.md](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/blob/main/docs/FORMAT.md).
No implementation output substitutes for that review. If a candidate remains
unreviewed, keep that state visible rather than relabeling it accepted.

### Independent technical review — 2026-11-16

The coordinating root agent, separate from the derivation author, independently
read FR-007/C3 and FORMAT.md R1-R4 and recomputed the four child and three parent
checksums with Python stdlib SHA-512/256, without importing this repository's
runner, generator or the toolkit. Only the unique root `;~checksum:` line and
its LF terminator were excluded. All four child self-checksums matched, and each
child's nested parent digest equaled the manifest's stated parent digest.

| Parent | Independently recomputed checksum |
| --- | --- |
| Whole | `pdDy56KE7+tzfZfk9eVOAQOPc/Fj78DfNBWOpJC4xac=` |
| Subset | `6j+hYGoiuIO0VoiY4NwaOsnOzhtsEL97A0ss66imAdI=` |
| Masked | `2WBzTRWHA/8A0y8TvwMCVENlk1FetSR9Gt4zz0hrCT8=` |

The reviewer agreed with C3's proposed outcomes: subset-citing-whole and
masked-exact checked-pass; real-digest-wrong-file and case-folded-digest
checked-fail. The latter does not isolate sequence case from header differences.
A pass establishes cited file identity, not the scientific derivation claim.
This is an independent **technical review**, not maintainer/curator acceptance.
The existing normative promotion markers remain unchanged pending disposition.

## Concrete maintainer decisions

These remain questions, taken from the
[#10 pilot handoff](https://github.com/FAIR-bioHeaders/FHT-Specification/issues/10#issuecomment-6897167617),
not decisions made by this packet:

1. Does the bounded chr4 subset satisfy the public-transcriptome pilot item, or
   is a complete producer delivery required? Keep the subset label either way.
2. For the annotation-derived pilot, what does `dateCreated` identify, and should
   the extraction script be represented in `assemblySoftware`? A changed value
   changes header/checksum bytes; do not repair these by inference.
3. What reuse wording, if any, should the pilot carry for supplied sequence data?
   Preserve source terms and distinguish newly authored header contributions.
4. Should real-data records remain in `pilot/` or gain an examples lane?
5. How should #8's shared/default-path items be dispositioned for the prepublication
   review? They depend on publication and cannot truthfully be marked delivered
   by a draft-only run. No issue-body gate is changed here.
6. Which shared vocabulary will express reader-lane-dependent expectations and
   promotion state at absorption? This packet adds no manifest fields.

## Verification recorded for this packet

On macOS with Python 3.13, the installed 0.11.0 lane exited 0: 28 valid / 44
invalid compared, 10 parent-link vectors, 0/72 default-path accepts, 28 byte-exact
strips and 28 metadata round trips. Stream checks executed **72 verify, 28 strip,
28 combine**, with byte-exact payload comparisons and verified combined stdout.
The package pin printed `b9ad19a62772092e08935cff44ee77a50981bbaf` /
`11c69d6647736695beaa72976a1d9b30c0f44f8cfe55f8eb171c9d0bcb6795f8`;
local draft bytes printed
`59ad9641adcb0e5591045c2d894c066d1adc9984cca84c5ff6502f8dad88487e`.
Those different digests were reported as a finding, not relabeled equal.

The independent fixture checker passed all 72 vectors and examples. Native
repository unittests, provenance/legacy checks, documentation checks and pinned
Markdownlint passed. Harness controls deliberately corrupt payload stdout,
remove all cases and make the named default accept: each is detected. The Linux
installed-artifact job is prepared; its actual server result must be recorded
after the PR runs. No Linux pass is claimed by the local measurement.

## Handoff order

Complete reproducible prepublication evidence and independent expectation review;
present the remaining decisions in one curator review. Only after recorded
acceptance prepare shared publication through the established maintainer process.
Verify published contract/registry/vector artifacts before promoting default
runtime support or refreshing consumer release pins. Shared absorption must
preserve the recorded V4/V5 selection asymmetry. FHT HTML drafting (#11) can
proceed independently, but no decision here invents it as a new release gate.

No schema, vector, example, pilot or published artifact bytes change in this packet.
