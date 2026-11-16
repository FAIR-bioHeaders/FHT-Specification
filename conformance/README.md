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
- `parents/`: one synthetic FHR-headed parent genome (a byte target for the
  C3 link vectors; it is not itself an FHR conformance vector).
- `manifest.json`: the expected outcome for every file. Field names and
  semantics follow the shared manifest (`id`, `file`, `format`, `compressed`,
  `expected`, `rules`, `description`, `checksum`, `metadata`, `rule`,
  `reason`, `result`, `retired`), the proposed format id is `fht-fasta`, and
  two manifest fields here have no shared-manifest precedent:
  `selfChecksum` and `parentLink` are **finalized** for release (maintainer
  decision 2026-11-14, issue #37; semantics below), while the top-level
  `status` label remains provisional pending shared absorption.
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

### Finalized field semantics (issue #37)

`selfChecksum` names, per vector, the state of the file's own root checksum
line under the R1-R5 recomputation, and is recorded on **every** vector
(68/68):

- `matches` — the stated value equals the recomputed value over the covered
  bytes. The positive class: all 26 valid vectors carry it, and so do the
  invalid vectors whose single defect lies elsewhere (the anti-accident rule:
  an implementation must not pass a vector by failing the comparison by
  accident).
- `broken` — the root checksum line parses but recomputes differently
  (negative fixture, 7 vectors).
- `unreachable` — the root checksum line cannot be located or compared at all
  (negative fixture, 9 vectors; the R2/R5 line-shape families).

`parentLink` is an array of per-link entries
`{file, statedChecksum, result}` recorded exactly on the vectors that
exercise C3 (6):

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
| Byte coverage (R1-R4) | RNA `lf`/`crlf`/`cr`/`mixed-endings`/`no-final-newline`, cDNA `T` variant, `gzip` (one member), `bgzf` (multi-block), `gzip-multimember` (two members split inside the checksum line); rejections: CRLF-normalized, U→T-normalized and case-normalized checksums (R1), sequence tamper and its compressed copy `gzip-sequence-tampered` (R3), SHA-256, truncated SHA-512 and non-canonical base64 (R4) |
| Checksum line shape (R2/R5) | root-indented, space-before-colon, quoted value, checksum-first, trailing spaces, nested (derivedFrom) parent checksum; rejections: missing, doubled, nested-only (R2), block literal, continuation, trailing comment (R5) |
| Header text (R6-R8, R10, R12/R13) | ordinary comments/blank lines incl. `;~#` and a post-record `;` comment, raw UTF-8 value; rejections: U+2028 (R6), BOM (R7), duplicate key and anchor/alias (R8), `;~` after record and concatenation (R10), `011` (R12), `.inf` (R13) |
| Writer recommendations | escaped `\x3E`/`\x40` (R11), `javascript:` relatedLink kept valid with `warnings: ["R14"]` |
| Extensions (R15) | valid `x-` values of every JSON type and in the rich record; rejections: nested `x-` key, `X-Wrongcase` key |
| Contract (C1) | minimal (nine required fields only), rich (every optional field), all three `assemblyType` values in `examples/`; rejections: missing/unknown `assemblyType`, `cDNA` molecule type, empty `sample`, FHR `genome` key, legacy `masking` key, `SRS` run accession, and the three parent-shape defects |
| Selection (C2, V1, V5) | valid raw-main citation (`fht-fasta-schema-raw-main`, the only resolvable FHT URL today); rejections: FHR schema URL and arbitrary URL (C2), future major `2.0` and unquoted number via raw-main (V1), `w3id .../fht/v0.5.0` and raw tag `v9.9.9` (V5, `result: invalid-as-fhr` — read as FHR, rejected by the current FHR schema; after FHT registration the w3id vector becomes V4, but the development-repository raw-tag URL remains V5 because it matches no V2 form) |
| Parent links (C3) | checked-pass ×3 (incl. the two-link rich record), unchecked ×1, checked-fail ×1, mixed verdicts ×1 (checked-pass + checked-fail in one record; #37) |

Counts: 26 valid, 42 invalid, 1 parent fixture; every vector carries a
finalized `selfChecksum` (26 matches-invalid + 26 matches-valid = 52, 7
broken, 9 unreachable) and the six C3 link vectors carry `parentLink`
entries. Rule coverage self-check:
every registered rule except the recommendation/warning/outcome-only/lane
rules (R9, R11, R14, V5, V7 — each with a recorded `notApplicable` note in the
manifest) has both a valid and an invalid vector.

### Accountability for FORMAT.md R1-R15

Issue #8's third box asks for stable cases "for R1–R10"; the table is the
answer for the whole shared range, so a reviewer can check each rule instead of
counting vectors. 21 rules are registered: every lettered rule of FORMAT.md
(R1-R15), the three selection rules this suite names (V1, V5, V7) and this
contract's own C1-C3. `scripts/check_fht_fixtures.py` fails the lane if a
rule R1-R15 is absent from the registry, or if a registered rule has neither
both sides nor a recorded reason.

| Rule | Valid vector | Invalid vector | Where |
| --- | --- | --- | --- |
| R1 exact bytes, decompressed | `fht-fasta-lf` (+ `crlf`, `cr`, `mixed-endings`, `no-final-newline`, `cdna`, `gzip`, `bgzf`, `gzip-multimember`) | `fht-fasta-crlf-normalized-checksum`, `-u-normalized-checksum`, `-case-normalized-checksum` | FORMAT.md |
| R2 one root checksum line | `-root-indented`, `-space-before-colon`, `-quoted-value`, `-nested-checksum` | `-missing-checksum`, `-two-checksum-lines`, `-only-nested-checksum` | FORMAT.md |
| R3 exclude that line, hash the rest | `-checksum-first`, `-checksum-trailing-spaces`, `-comments-and-blank-lines` (the excluded line is located, not guessed) | `-sequence-tampered`, `-gzip-sequence-tampered` | FORMAT.md |
| R4 SHA-512/256 canonical base64 | `-lf` (44-char canonical value) | `-checksum-sha256`, `-checksum-truncated-sha512`, `-checksum-non-canonical` | FORMAT.md |
| R5 checksum line grammar | `-quoted-value`, `-checksum-trailing-spaces` | `-block-literal-checksum`, `-continued-checksum`, `-checksum-with-comment` | FORMAT.md |
| R6 UTF-8, no U+0085/2028/2029 | `-utf8-metadata` | `-u2028-in-header` | FORMAT.md |
| R7 no BOM | `-lf` | `-utf8-bom` | FORMAT.md |
| R8 no duplicate keys/anchors/aliases/merge | `-lf` | `-duplicate-key`, `-yaml-anchor-alias` | FORMAT.md |
| R9 microdata token lists | — | — | **not applicable to `fht-fasta`**: a microdata-only rule, and no FHT microdata reader or writer exists (box 2 keeps unimplemented serializations out of the suite; the typed-HTML lane is issue #11). Registered with this `notApplicable` note so the R1-R15 audit accounts for it. |
| R10 leading header block | `-comments-and-blank-lines` | `-header-after-record`, `-concatenated` | FORMAT.md |
| R11 escaped `>`/`@` (writer advice) | `-escaped-record-markers` | — (recommendation; `notApplicable`) | FORMAT.md |
| R12 YAML 1.1/1.2 agreement | `-lf` (all plain scalars agree) | `-yaml-leading-zero` | FORMAT.md |
| R13 finite numbers | `-rich` | `-inf-vital-stats` | FORMAT.md |
| R14 link schemes (warn only) | `-link-scheme-warning` (`warnings: ["R14"]`) | — (never a rejection; `notApplicable`) | FORMAT.md |
| R15 `x-` extensions | `-extension-fields`, `-rich` | `-extension-nested-key`, `-extension-uppercase-key` | FORMAT.md (via FR-010) |
| V1 raw-main selects current | `-schema-raw-main` | `-version-2-0-via-raw-main`, `-schemaversion-number` | SCHEMA-VERSIONS.md |
| V5 unrecognized value is FHR | — (no FHT-valid record can be FHR-valid; `notApplicable`) | `-schema-w3id-release-without-fht`, `-schema-raw-tag-unknown` (`result: invalid-as-fhr`) | SCHEMA-VERSIONS.md, as limited by V7 |
| V7 opt-in draft lane | — (governs whether any record here is read as the draft; no byte outcome of its own, `notApplicable`) | — (same reason) | SCHEMA-VERSIONS.md |
| C1 contract validation | `-minimal`, `-rich`, `-lf`, `-cdna`, `-extension-fields`, the three parent-link positives | the missing/unknown `assemblyType`, `cDNA` molecule type, empty `sample`, FHR `genome` key, legacy `masking` key and `SRS` run rejections | `fht.json`, this README |
| C2 schema-URL closure | `-schema-raw-main` | `-cites-fhr-schema`, `-cites-arbitrary-url` | `fht.json` |
| C3 parent links | `-parent-transcribed-from`, `-parent-filtered-from`, `-parent-unavailable`, `-rich` | `-parent-mismatched`, `-parent-mixed-verdicts` | this README |

The "where" column distinguishes the shared-document rules from this
development contract's own C-rules; the manifest's `rules` entries carry the
same rule summaries, and `docs/FORMAT.md` and `docs/SCHEMA-VERSIONS.md` stay
authoritative for their text.

### The rule this suite cannot carry yet: V7 with the lane closed

Every vector here is read **through** the opt-in draft lane: the `expected`
values describe a reader that chose to read this repository's `fht.json`. Rule
V7 also decides what a reader does when it did *not* choose the lane — then the
owning-repository raw-main URL is "any other value" under V5, so each of these
records is read as FHR and rejected there. Measured 2026-11-15 with
`fair-bioheaders` 0.11.0 in both configurations (see
[`../docs/CI.md`](../docs/CI.md)): 0 of 68 vectors accepted with the lane off,
26 accepted with it on.

That is a second, configuration-dependent outcome for the *same bytes*, and this
manifest vocabulary cannot hold it: a vector has one `file`, one `expected` and
no field for the reader's lane. Two ids for the same bytes with different
`expected` values would be worse — the shared suite's rule is that ids are never
reused or rewritten, and a consumer that reads the whole manifest (the toolkit's
gated `tests/fht_conformance_test.py`, for instance) has no way to know which of
the two it is being asked to reproduce. So the lane-closed behavior is recorded
as a measurement, not as a vector, until either

1. the shared manifest grows a reader-configuration field (a vocabulary change
   for FAIR-bioHeaders-Specification, coordinated at absorption: this repo #55 /
   FAIR-bioHeaders-Specification#107), or
2. issue #9 gives the toolkit a default FHT reader, after which V5-with-the-lane-
   off stops being the FHT story at all.

Until one of those lands, `fht-fasta-schema-raw-main` asserts the lane-on result
only, and `notApplicable` on V7 says so in the manifest itself.

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
  for #9. What has been measured since is recorded in
  [`../docs/CI.md`](../docs/CI.md) ("Manual lane — the named toolkit
  version"): `scripts/run_toolkit_lane.py` runs `verify`, `verify-links`,
  `strip` and a `convert`/`strip`/`combine` round trip against the suite
  with `fair-bioheaders` 0.11.0 under the opt-in lane, and reports
  agreement plus the writer's canonical-header findings. That is a draft-lane
  preview, not the default path, and it changes no expectation here.
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
- **No stdin/stdout vectors.** Stream *framing* is covered: `gzip` (one
  member), `bgzf` (multi-block with the EOF block) and `gzip-multimember`
  (two members with the member boundary inside the root checksum line) are all
  distributed as files whose decompressed bytes are `fht-fasta-lf`, which is
  what R1 makes decidable. What the shared manifest's file-based vocabulary
  cannot express is a reader fed a pipe instead of a path, so the CLI's
  stdin/stdout behavior stays #9 territory.

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
