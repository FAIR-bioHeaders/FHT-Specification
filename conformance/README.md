# FHT conformance vectors (development contract — issue #8)

Byte-exact positive and rejection fixtures for the FHT 1.0 **development**
contract, the generated [`fht.json`](../fht.json) of this repository
([revised spec 005](../specs/005-rna-transcriptome-header/spec.md), PR #21).
They apply the shared specification's header and checksum rules
([docs/FORMAT.md](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/blob/main/docs/FORMAT.md)
R1-R15 on FASTA `;~` headers) and the family schema-selection rules
([docs/SCHEMA-VERSIONS.md](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/blob/main/docs/SCHEMA-VERSIONS.md)
V1/V5, as limited by the V7 draft-lane note) to transcriptome files, in RNA
(U) and cDNA (T) form. The layout and
the manifest fields mirror the shared suite's `fhp-fasta` vectors so the
shared `conformance/manifest.json` can absorb these vectors unchanged when
FHT is published.

**Status: development, not publication.** Nothing here is released, adopted
or published; FHT has no released contract (issue #10), no toolkit support
(issue #9) and no shared-manifest entry yet (issue #55 /
FAIR-bioHeaders-Specification#107, the #55 chain's "lane F").

## Layout

- `valid/`: files a conforming implementation must accept.
- `invalid/`: files it must reject.
- `parents/`: three synthetic FHR-headed genome files, each a byte target for the
  C3 link vectors (none is itself an FHR conformance vector):
  `parent-genome.fhr.fasta` holds both scaffolds, `parent-genome-subset.fhr.fasta`
  holds a proper subset of them, and `parent-genome-masked.fhr.fasta` holds both
  with one sequence line written in lower case and `masking: soft-masked`. The
  three exist so the subset and case hazards can be *compared against real bytes*
  rather than described: each has its own computed digest, and the digests are
  asserted pairwise different by the generator.
- `manifest.json`: the expected outcome for every file. Field names and
  semantics follow the shared manifest (`id`, `file`, `format`, `compressed`,
  `expected`, `rules`, `description`, `checksum`, `metadata`, `rule`,
  `reason`, `result`, `retired`), the proposed format id is `fht-fasta`, and
  three manifest fields here have no shared-manifest precedent:
  `selfChecksum` and `parentLink` are **finalized** for release (maintainer
  decision 2026-11-14, issue #37; semantics below), while the top-level
  `status` label remains provisional pending shared absorption. `promotion`
  (per vector) and `promotionCandidates` (top level) are **review
  bookkeeping**, not release vocabulary: they mark pilot-derived vectors whose
  expectations no second reader has confirmed yet, and both disappear when the
  review lands.
- `*.gz`: gzip or BGZF copies; validate their decompressed bytes.

Every file is byte-exact. The repository `.gitattributes` turns off
line-ending conversion for `conformance/**` and `examples/**`, so CR, CRLF
and checksummed bytes survive every checkout. Do not open and re-save these
files in an editor; run the generator instead.

## Rule registry

R1-R15 and V1/V5 carry the summaries of the shared documents (see
`rules` in `manifest.json`; the documents are authoritative). FHT's own
rules are **C1-C3** — the letter scheme of the shared suite (one uppercase
letter plus number), with `C` for the development **contract** rules; `C` is
unassigned in every federation conformance namespace (the shared manifest
registers R, V, M, G, J and P). They replaced the provisional `T1-T3`
before external citation (issue #36; the old labels were additionally
ambiguous with the RNA-U/cDNA-T notation this suite uses throughout). Their
rule text, derived from the merged contract, is:

- **[C1] Contract validation.** The metadata parsed from a `;~` header must
  validate against `fht.json` (draft 2020-12, asserted `format`s): the nine
  required fields (`schema`, `schemaVersion` `"1.0"`, `transcriptome`,
  `assemblyType`, `taxon`, `version`, `metadataAuthor`, `dateCreated`,
  `checksum`) present and non-empty; enums (`de novo`, `genome-guided`,
  `annotation-derived`; `mRNA`, `rRNA`, `tRNA`, `transcribed RNA`;
  `unstranded`, `forward`, `reverse`); patterns (checksums, run accessions,
  taxon URI, DOI); nested cardinality (`sample` items need one value,
  optional arrays non-empty when present); the closed top level plus the
  `x-` extension pattern; and only the two permitted parent pairs (FR-007).
- **[C2] Schema-URL closure.** A record's `schema` value must match the
  FHT URL pattern: this repository's raw `main` URL, one of its release-tag
  URLs, or a `https://w3id.org/fair-bioheaders/fht/vX.Y.Z` URL. Unlike
  released FHR (selection rule V5 leaves its `schema` open), an arbitrary
  URL or another type's schema URL fails the contract; it never silently
  selects the FHT schema.
- **[C3] Parent-link verification.** A `derivedFrom` item's `checksum` is
  the parent file's FHR-family checksum under R1-R5. A reader that has the
  parent file must recompute it and compare as exact strings: equal is
  **checked-pass**, different is **checked-fail** and must be reported as
  an invalid link (not skipped). Without the parent file the link is
  **unchecked**: the record stays valid, and no implementation may call
  such a link verified. An `accessionID` on the link is additional, never
  a substitute for the checksum (FR-007).

Checked / unchecked / invalid, concretely:
`fht-fasta-parent-transcribed-from` and `fht-fasta-parent-filtered-from`
cite checksums that recompute from files in this directory (checked-pass);
`fht-fasta-parent-unavailable` cites the canonical placeholder
`AAAA…AAA=` with no parent file (unchecked, still valid);
`fht-fasta-parent-mismatched` is byte-valid, schema-valid and
checksum-consistent but cites a perturbed parent checksum (invalid link,
checked-fail); `fht-fasta-parent-mixed-verdicts` pairs a checked-pass and a
checked-fail link in one record, proving the verdict is per entry.
`fht-fasta-parent-real-digest-wrong-file` and
`fht-fasta-parent-case-folded-digest` are checked-fail with a **genuine** digest
— the value is the true checksum of a different real file in `parents/`, so
nothing is malformed and only the exact-string comparison can catch it;
`fht-fasta-parent-subset-citing-whole` and `fht-fasta-parent-masked-exact` are
their checked-pass siblings. Those four are promotion candidates from the
real-data pilot: see "Promotion candidates from the pilot" below.

### Finalized field semantics (issue #37)

`selfChecksum` names, per vector, the state of the file's own root checksum
line under the R1-R5 recomputation, and is recorded on **every** vector
(70/70):

- `matches` — the stated value equals the recomputed value over the covered
  bytes. The positive class: all 27 valid vectors carry it, and so do the
  invalid vectors whose single defect lies elsewhere (the anti-accident rule:
  an implementation must not pass a vector by failing the comparison by
  accident).
- `broken` — the root checksum line parses but recomputes differently
  (negative fixture, 6 vectors).
- `unreachable` — the root checksum line cannot be located or compared at all
  (negative fixture, 9 vectors; the R2/R5 line-shape families).

`parentLink` is an array of per-link entries
`{file, statedChecksum, result}` recorded exactly on the vectors that
exercise C3 (10):

- `result` is one of `checked-pass` / `checked-fail` / `unchecked`.
- `unchecked` ⇔ `file: null`: the parent bytes were not supplied; the link is
  neither verified nor a rejection reason.
- `checked-pass` / `checked-fail` require a named parent file inside this
  directory; `statedChecksum` is compared to its recomputed checksum as an
  exact string. The runner enforces this containment by resolution: a
  parentLink path that escapes `conformance/` (via `../` segments or an
  absolute location) is rejected without being read.
- The verdict is **per entry**: one record may carry both outcomes and the
  checked-fail entry drives rejection
  (`fht-fasta-parent-mixed-verdicts`).

These two fields are finalized for release with the positive and negative
fixtures above; shared absorption may rename them onto whatever the shared
manifest schema uses but must not change this verdict model (issue #9
adopts these failure classes as its toolkit acceptance list). The top-level
`status` label is the only field still provisional pending absorption.

## Provenance — every byte is generated

[`../scripts/make_fht_fixtures.py`](../scripts/make_fht_fixtures.py) (stdlib
only) writes `valid/`, `invalid/`, `parents/`, `manifest.json` and the
generated files in [`../examples/`](../examples/). It is deterministic with
no seed: no clock, locale, random source or filesystem order; gzip/BGZF
vectors use stored deflate blocks with mtime 0 and no name, so reruns
reproduce identical bytes on any zlib build.

Checksums are **cross-checked by a second, independent implementation**: the
generator embeds values computed at build time, and
[`../scripts/check_fht_fixtures.py`](../scripts/check_fht_fixtures.py)
re-derives every expectation from the rule text with its own R1 line
splitting (LF/CRLF/lone CR), its own R2 root-indent detection, its own R5
value grammar and its own SHA-512/256 recomputation (adapted from the
stdlib reference in FAIR-bioHeaders-Specification
`scripts/tool_survey/round6/make_fixtures.py`, not copied from the
generator's same-file helper). CI (`.github/workflows/fht-fixtures.yml`,
also wired into `tests/test_fixtures.py`) runs three proofs:

1. regeneration inside the process, twice, compared with the committed
   bytes (`diff`-level identity, per file);
2. the same regeneration into a scratch directory outside the tree;
3. every vector re-read and re-classified by the independent runner
   (valid: recomputed checksum equals the manifest and the record passes
   `fht.json` with `FormatChecker`; invalid: rejected at exactly the
   declared failure class, with the `selfChecksum` anti-accident rule —
   non-checksum defects carry consistent checksums so an implementation
   cannot pass by failing the comparison by accident).

### Synthetic content policy

No metadata, parent checksum or identifier is invented to look real. Every
name carries a `Synthetic`/`(placeholder)` label; URLs live in example.org
or on this repository's own schema paths; the DOI uses the reserved
`10.5555` prefix; run accessions use `SRR/ERR/DRR 999xxxx`; the parent
placeholder checksum is the canonical-set `"A"*43 + "="`. The taxon is the
real *Homo sapiens* NCBI Taxonomy 9606, reused from the shared suite's
vectors, and the sequences are short synthetic nucleotide strings — no real
transcript is reproduced. All `vitalStats` of `fht-fasta-rich` are genuinely
computed from that vector's own sequence bytes. The parent fixture in
`parents/` is a fabricated FHR file with its own **real computed** checksum,
cited at its recomputed value by the checked-pass vectors.

## Vector census

`manifest.json` is authoritative; this is the map, not the list.

| Group | Vectors |
| --- | --- |
| Byte coverage (R1-R4) | RNA `lf`/`crlf`/`cr`/`mixed-endings`/`no-final-newline`, cDNA `T` variant, `gzip`, `bgzf`; rejections: CRLF-normalized, U→T-normalized and case-normalized checksums (R1), sequence tamper (R3), SHA-256, truncated SHA-512 and non-canonical base64 (R4) |
| Checksum line shape (R2/R5) | root-indented, space-before-colon, quoted value, checksum-first, trailing spaces, nested (derivedFrom) parent checksum; rejections: missing, doubled, nested-only (R2), block literal, continuation, trailing comment (R5) |
| Header text (R6-R8, R10, R12/R13) | ordinary comments/blank lines incl. `;~#` and a post-record `;` comment, raw UTF-8 value; rejections: U+2028 (R6), BOM (R7), duplicate key and anchor/alias (R8), `;~` after record and concatenation (R10), `011` (R12), `.inf` (R13) |
| Writer recommendations | escaped `\x3E`/`\x40` (R11), `javascript:` relatedLink kept valid with `warnings: ["R14"]` |
| Extensions (R15) | valid `x-` values of every JSON type and in the rich record; rejections: nested `x-` key, `X-Wrongcase` key |
| Contract (C1) | minimal (nine required fields only), rich (every optional field), all three `assemblyType` values in `examples/`; rejections: missing/unknown `assemblyType`, `cDNA` molecule type, empty `sample`, FHR `genome` key, legacy `masking` key, `SRS` run accession, and the three parent-shape defects |
| Selection (C2, V1, V5) | valid raw-main citation (`fht-fasta-schema-raw-main`, the only resolvable FHT URL today); rejections: FHR schema URL and arbitrary URL (C2), future major `2.0` and unquoted number via raw-main (V1), `w3id .../fht/v0.5.0` and raw tag `v9.9.9` (V5, `result: invalid-as-fhr` — read as FHR, rejected by the current FHR schema; after FHT registration the w3id vector becomes V4, but the development-repository raw-tag URL remains V5 because it matches no V2 form) |
| Parent links (C3) | checked-pass ×5 (the two-link rich record, `-parent-transcribed-from`, `-parent-filtered-from`, and the two pilot candidates `-parent-subset-citing-whole` and `-parent-masked-exact`), unchecked ×1, checked-fail ×3 (`-parent-mismatched`, and the pilot candidates `-parent-real-digest-wrong-file` and `-parent-case-folded-digest`, whose stated value is a genuine digest of a *different* shipped file), mixed verdicts ×1 (checked-pass + checked-fail in one record; #37) |

Counts: 27 valid, 43 invalid, 3 parent fixtures; every vector carries a
finalized `selfChecksum` (28 matches-invalid + 27 matches-valid = 55, 6
broken, 9 unreachable) and the ten C3 link vectors carry `parentLink`
entries. Rule coverage self-check:
every registered rule except the recommendation/warning/outcome-only rules
(R11, R14, V5 — each with a recorded `notApplicable` note in the manifest)
has both a valid and an invalid vector.

## Promotion candidates from the real-data pilot (#45)

The maintainer decision recorded on #8 is to promote selected pilot cases to
normative vectors. Four vectors here do that, and they are marked as
**candidates**, not as accepted vectors:

- per vector: `"promotion": "candidate-unreviewed"`;
- top level: `promotionCandidates`, carrying the source, the candidate ids and
  the review rule that governs them.

**What was promoted and what was not.** #45 built a real chr4 (`NC_004353.4`)
FHR parent and a 334-transcript FHT subset on top of it. Its *bytes* stay in
`pilot/`: they are third-party sequence, they are 1.4 MB each, and the synthetic
content policy exists so a published vector never depends on a download. What
transfers is the *shape* of what the pilot had to reason about, restated over
synthetic fixtures: a subset whose link cites the whole parent; a parent whose
letters exist in two case encodings with two digests; and a link whose stated
digest is genuine but belongs to a file the reader was not handed.

**The constraint that governs this section.** A vector's `expected` outcome must
not be produced by the implementation under test. Each candidate's expectation
below was written from rule text first — FR-007 in
[`../specs/005-rna-transcriptome-header/spec.md`](../specs/005-rna-transcriptome-header/spec.md)
and rules C3/R1 in this file and in
[`docs/FORMAT.md`](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/blob/main/docs/FORMAT.md)
— and three executors then read the fixtures independently.

| Candidate | Expected, from the clause quoted | A — released `fair-bioheaders` 0.11.0 (PyPI, V7 lane ON) | B — `scripts/check_fht_fixtures.py` (this repository's independent reader) | C — `FAIR-bioHeaders-Tools-JavaScript` at `d8552f6` (`src/reader.js`, `src/parent-links.js`) |
| --- | --- | --- | --- | --- |
| `fht-fasta-parent-subset-citing-whole` | valid + `checked-pass`. C3: "equal is **checked-pass**"; FR-007 fixes the permitted pair and requires the parent's FHR-family checksum, and says nothing about coverage | `verify` exit 0 (`Checksum verified.`); `verify-links` exit 0 printing `matched (` | accepted; link recomputes equal | `valid: true`, verdict `checked-pass`, selection `V7/FHT` |
| `fht-fasta-parent-real-digest-wrong-file` | invalid + `checked-fail`. C3: "different is **checked-fail** and must be reported as an invalid link (not skipped)" | `verify` exit 0 (the file itself is valid), `verify-links` exit 3 printing `not matched (` | rejected in the parent-link class | `valid: false`, verdict `checked-fail`, the error names both digests |
| `fht-fasta-parent-masked-exact` | valid + `checked-pass`. R1: "Read the FASTA/GFA as bytes; do not normalize…", so the masked file's own digest is the only correct citation for it | `verify` exit 0; `verify-links` exit 0, `matched (` | accepted; link recomputes equal | `valid: true`, verdict `checked-pass` |
| `fht-fasta-parent-case-folded-digest` | invalid + `checked-fail`. R1 plus C3's exact-string comparison: the uppercase and masked copies of one set of letters are two files, so citing one against the other fails | `verify` exit 0, `verify-links` exit 3, `not matched (` | rejected in the parent-link class | `valid: false`, verdict `checked-fail` |

Reproducing the cross-check (nothing outside the repository is written; both
reads are read-only):

```sh
# A — the released reader, PyPI 0.11.0, in a throwaway venv
python3 -m venv /tmp/fht0110 && /tmp/fht0110/bin/pip install fair-bioheaders==0.11.0
BIOHEADERS_EXPERIMENTAL_FHT=1 /tmp/fht0110/bin/bioheaders verify \
  conformance/valid/fht-fasta-parent-subset-citing-whole.fht.fasta   # exit 0
BIOHEADERS_EXPERIMENTAL_FHT=1 /tmp/fht0110/bin/bioheaders verify-links \
  conformance/invalid/fht-fasta-parent-real-digest-wrong-file.fht.fasta \
  conformance/parents/parent-genome-subset.fhr.fasta                 # exit 3

# B — this repository's own reader
python scripts/check_fht_fixtures.py

# C — the JavaScript library, read-only export of its origin/main
git -C ../FAIR-bioHeaders-Tools-JavaScript archive origin/main | tar -x -C /tmp/fhtjs
ln -s "$PWD/../FAIR-bioHeaders-Tools-JavaScript/node_modules" /tmp/fhtjs/node_modules
# then call inspectBytes(bytes, {container: 'fasta', drafts: ['FHT'], parents})
# from /tmp/fhtjs/src/reader.js over the manifest's vectors
```

A and C were run against these bytes on 2026-11-15 and reported **no
disagreement with any of the 70 vectors**, not only with the four candidates: A
through `bioheaders verify` / `verify-links`, C through `inspectBytes(bytes,
{container: 'fasta', drafts: ['FHT'], parents})` on a read-only `git archive`
export of that repository's `origin/main`. C's own `capability:draft` runner
refuses this suite by design, because its recorded `suiteManifestSha256` still
names the 66-vector revision — a stale pin, reported and not repaired here. C
reads the contract at `59ad9641…`, this checkout's `fht.json`; A reads its
bundled `11c69d66…` at `b9ad19a6…`, so A's agreement is with that pinned older
revision.

### Expectations require independent review — the reviewer must not be the author of the derivation

Agreement between implementations corroborates an expectation; it does not
substitute for review, and it cannot detect the case where every executor shares
one misreading of the rule text. **The four vectors above were derived by this
PR's author and need a second reader — all four, specifically:**

1. `fht-fasta-parent-subset-citing-whole` — is `valid` the only rule-compatible
   outcome, or does FR-007's "only for real reviewed family-file relationships"
   make a subset-citing-whole link a record defect rather than a scope statement
   the contract cannot see? A reviewer should also decide whether the vector
   should carry a warning field, which would make "file identity only"
   machine-checkable instead of descriptive.
2. `fht-fasta-parent-real-digest-wrong-file` — the outcome is C3's, but whether a
   reader must *name both digests* in its report is not settled by any rule text
   here; #45's `verify-links` output does, and no clause compels it.
3. `fht-fasta-parent-masked-exact` and `fht-fasta-parent-case-folded-digest` —
   both rest on reading R1's "do not normalize" as covering letter case. The rule
   text supports it by omission (case is not in the normalization list, and the
   bytes are the bytes), but that inference is the author's, and a curator should
   confirm it, because the pilot's real parent is exactly this shape (27.8 %
   lowercase, with NCBI's uppercase component file beside it).

No candidate depends on `dateCreated`, `assemblySoftware` or `reuseConditions`:
those are open curator questions and each changes bytes, so all three stay absent
from the candidate records, and the candidates carry the same `dateCreated` as
the rest of the synthetic set (no derivation reads it).

**Accepting a candidate** is a one-line change: drop its id from
`PROMOTION_CANDIDATES` in `scripts/make_fht_fixtures.py` and regenerate. The
vector, its id and its bytes do not move — only the `promotion` marking and the
top-level list do, so review leaves a trace in history. **Rejecting** one follows
the shared retirement rule: retire the id, never rewrite its expectation.

### Measured, deliberately not promoted

- **The lane-off / V5 outcome.** #45 ran the same real FHT file twice: with the
  draft lane closed, the released reader routed it to the current FHR schema and
  rejected `schemaVersion '1.0'`; with the lane open, it verified. Rule V7's text
  gives that reading directly ("Without that choice, V5 governs such a value and
  the outcome is exactly what it was before V7 existed"), and both paths were
  re-measured on this suite on 2026-11-15: `bioheaders verify` with the lane
  closed accepts **0 of 70** vectors; with it open it accepts 31 — the 27 valid
  vectors plus the 4 whose only defect is a `checked-fail` link, which `verify`
  passes by design and `verify-links` rejects with exit 3. It is **not** a
  vector, because a vector carries one
  `file` and one `expected`, and this is one byte string with two outcomes,
  decided by the reader's configuration. Encoding it needs a manifest field for
  the reader's lane — shared vocabulary, so that belongs to #55 /
  FAIR-bioHeaders-Specification#107 and to #9, not to a draft PR inventing it
  here.
- **`assess`'s FHT findings** (`not assessed: unsupported-header-type`, and the
  `derivedFrom[].accessionID` sequence accession `NC_004353.4` flagged against an
  assembly-accession pattern) are toolkit behavior over released vocabulary and
  belong to #9; making them FHT vectors would let an FHT expectation depend on a
  tool's rubric.
- **Any real-data vector** (the chr4 bytes, the 334-record subset, the GFF exon
  proof). They stay pilot evidence in `pilot/dmel-chr4/`.

## What these vectors do **not** yet prove

- **No installed-toolkit behavior in the default path.** A default
  `fair-bioheaders` install still has no FHT feature: the released reader
  routes these records as FHR (rule V5), so there are no default-on
  `bioheaders`/`fhr-*` round trips, strip/combine or conversion claims.
  The opt-in V7 draft lane (fair-bioheaders 0.11.0,
  `BIOHEADERS_EXPERIMENTAL_FHT=1`) consumes this suite through the gated
  `tests/fht_conformance_test.py` in FAIR-bioHeaders-Tools, but a gated
  preview consumer is not shipped support: full support, including the
  default path, belongs to issue #9 after FHT ships in a toolkit release.
  "Strip/combine preserve sequence IDs,
  wrapping, U/T, metadata ordering/types and exact bytes under the
  established checksum coverage policy" is *represented here only* as
  byte-preservation fixtures (the alphabet variants and the
  normalization-rejection vectors); the executable round-trip half waits
  for #9.
- **No shared publication.** These vectors are not in the shared
  `conformance/manifest.json` and cite no resolvable FHT release URL,
  because none exists (the registry has no FHT entry; the w3id URL answers
  404, re-verified 2026-11-13). Expected outcomes for the V5 vectors are
  derived from the SCHEMA-VERSIONS.md rule text, including the V7 note
  (FAIR-bioHeaders-Specification#221 ruling, Option A, 2026-11-13, merged
  in `a4278c4622e8a90258fab8fa6c32532613f9bf26`): a release-shaped URL for
  a type no release registers is "any other value" under V5, read as FHR
  with the near-miss warning (FAIR-bioHeaders-Tools#125); V4 applies only
  once FHT enters `schemas/versions.json`. The FHR-invalid outcome was
  measured, not assumed: the current FHR schema — `fhr.json` at that shared
  commit, byte-identical to release tag `v0.5.0` (sha256
  `694ab5afaf8c3743eacf9e2aacb5551f7cbe37073b6f4afc3ae4a65b47f9d4df`) —
  rejects both records with the same five errors (`'1.0' is not one of
  ['2.0', '2.1']`; required `genome`, `assemblyAuthor` and `masking`
  absent; `transcriptome`, `assemblyType`, `moleculeType` match no FHR
  property or the `x-` pattern), reproduced on 2026-11-13 with jsonschema
  4.26.0 and confirmed by the released reader `bioheaders verify` from
  fair-bioheaders 0.10.0, which reports the V5 warning and the schemaVersion
  rejection for each file. **No implementation under test produced any
  expectation in this
  directory** — there is no FHT implementation. The generator's own
  reference reader and the runner's independently written reader agreeing
  on every byte is the cross-check this stage can honestly offer.
- **No stdin/stream vectors**: the shared manifest's format vocabulary is
  file-based, so the stream behavior of a future CLI is #9 territory.

## How the shared suite absorbs these vectors

When FHT is published through the #55 chain
(FAIR-bioHeaders-Specification#107):

1. Copy the `valid/fht-fasta-*` and `invalid/fht-fasta-*` files and their
   manifest entries into the shared `conformance/` tree; the format id
   `fht-fasta` slots beside `fhp-fasta`.
2. Adopt the finalized fields: `selfChecksum` and `parentLink` were
   finalized at the draft stage with positive and negative fixtures (#37,
   maintainer decision 2026-11-14; semantics in "Finalized field semantics"
   above); shared absorption may rename them onto the shared manifest
   vocabulary but must not change the verdict model. C1-C3 already follow
   the shared rule-label scheme (#36) and carry over as the rule ids of the
   shared FHT format document.
3. Re-point the `schema` URL: vectors currently cite this repository's
   raw-main URL (the only contract that exists). At release, the same
   bytes move to a new `fht-fasta-schema-*` vector set citing the w3id
   URL, exactly as FHP moved to `…/fhp/v0.4.0`; the raw-main vectors stay
   valid under V1 and keep their ids (ids are never reused or rewritten).
   The two V5-shaped rejection vectors then **diverge, and that asymmetry
   is the expected outcome** (recorded on closed #30; the V7 ruling,
   FAIR-bioHeaders-Specification#221 Option A): once FHT enters
   `schemas/versions.json`, a `https://w3id.org/fair-bioheaders/fht/vX.Y.Z`
   citation for an unregistered version becomes a genuine **V4**
   unsupported-version case, while a raw tag URL of *this development
   repository* (`…/FHT-Specification/v9.9.9/fht.json`) stays **V5**,
   because V2 anchors versioned release URLs to the shared publication
   repository and a dev-repo tag URL matches no V2 form at any point.
   Any outcome change retires the old id per the shared retirement rule.
4. Add the toolkit invocation to `scripts/check_conformance.py`
   (`--require-format fht-fasta`) once the released reader supports FHT.

Until then, `python scripts/check_fht_fixtures.py` (pinned jsonschema
4.26.0 + PyYAML 6.0.3, see [`../docs/CI.md`](../docs/CI.md)) is the
verification, and its failure classes are the acceptance list for #9's
toolkit implementation.
