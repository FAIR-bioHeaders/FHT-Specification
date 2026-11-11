# FHT conformance vectors (development contract — issue #8)

Byte-exact positive and rejection fixtures for the FHT 1.0 **development**
contract, the generated [`fht.json`](../fht.json) of this repository
([revised spec 005](../specs/005-rna-transcriptome-header/spec.md), PR #21).
They apply the shared specification's header and checksum rules
([docs/FORMAT.md](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/blob/main/docs/FORMAT.md)
R1-R15 on FASTA `;~` headers) and the family schema-selection rules
([docs/SCHEMA-VERSIONS.md](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/blob/main/docs/SCHEMA-VERSIONS.md)
V1/V4) to transcriptome files, in RNA (U) and cDNA (T) form. The layout and
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
  T3 link vectors; it is not itself an FHR conformance vector).
- `manifest.json`: the expected outcome for every file. Field names and
  semantics follow the shared manifest (`id`, `file`, `format`, `compressed`,
  `expected`, `rules`, `description`, `checksum`, `metadata`, `rule`,
  `reason`, `result`, `retired`), the proposed format id is `fht-fasta`, and
  three fields are **provisional** pending shared absorption:
  `selfChecksum` (`matches` / `broken` / `unreachable`, per invalid vector),
  `parentLink` (T3 scenario per vector) and `status` (top-level).
- `*.gz`: gzip or BGZF copies; validate their decompressed bytes.

Every file is byte-exact. The repository `.gitattributes` turns off
line-ending conversion for `conformance/**` and `examples/**`, so CR, CRLF
and checksummed bytes survive every checkout. Do not open and re-save these
files in an editor; run the generator instead.

## Rule registry

R1-R15 and V1/V4 carry the summaries of the shared documents (see
`rules` in `manifest.json`; the documents are authoritative). The FHT
`T` ids are **provisional** — named here because the shared publication
copy of the FHT format document does not exist yet. Their rule text,
derived from the merged contract, is:

- **[T1] Contract validation.** The metadata parsed from a `;~` header must
  validate against `fht.json` (draft 2020-12, asserted `format`s): the nine
  required fields (`schema`, `schemaVersion` `"1.0"`, `transcriptome`,
  `assemblyType`, `taxon`, `version`, `metadataAuthor`, `dateCreated`,
  `checksum`) present and non-empty; enums (`de novo`, `genome-guided`,
  `annotation-derived`; `mRNA`, `rRNA`, `tRNA`, `transcribed RNA`;
  `unstranded`, `forward`, `reverse`); patterns (checksums, run accessions,
  taxon URI, DOI); nested cardinality (`sample` items need one value,
  optional arrays non-empty when present); the closed top level plus the
  `x-` extension pattern; and only the two permitted parent pairs (FR-007).
- **[T2] Schema-URL closure.** A record's `schema` value must match the
  FHT URL pattern: this repository's raw `main` URL, one of its release-tag
  URLs, or a `https://w3id.org/fair-bioheaders/fht/vX.Y.Z` URL. Unlike
  released FHR (selection rule V5 leaves its `schema` open), an arbitrary
  URL or another type's schema URL fails the contract; it never silently
  selects the FHT schema.
- **[T3] Parent-link verification.** A `derivedFrom` item's `checksum` is
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
checked-fail).

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
| Contract (T1) | minimal (nine required fields only), rich (every optional field), all three `assemblyType` values in `examples/`; rejections: missing/unknown `assemblyType`, `cDNA` molecule type, empty `sample`, FHR `genome` key, legacy `masking` key, `SRS` run accession, and the three parent-shape defects |
| Selection (T2, V1, V4) | valid raw-main citation (`fht-fasta-schema-raw-main`, the only resolvable FHT URL today); rejections: FHR schema URL and arbitrary URL (T2), future major `2.0` and unquoted number via raw-main (V1), `w3id .../fht/v0.5.0` and raw tag `v9.9.9` (V4, `result: unsupported-version`) |
| Parent links (T3) | checked-pass ×3 (incl. the two-link rich record), unchecked ×1, checked-fail ×1 |

Counts: 25 valid, 40 invalid, 1 parent fixture. Rule coverage self-check:
every registered rule except the recommendation/warning/outcome-only rules
(R11, R14, V4 — each with a recorded `notApplicable` note in the manifest)
has both a valid and an invalid vector.

## What these vectors do **not** yet prove

- **No installed-toolkit behavior.** fair-bioheaders 0.9.0 has no FHT
  reader/writer, so there are no `bioheaders`/`fhr-*` round trips,
  strip/combine or conversion claims. Those belong to issue #9 after FHT
  ships in a toolkit release. "Strip/combine preserve sequence IDs,
  wrapping, U/T, metadata ordering/types and exact bytes under the
  established checksum coverage policy" is *represented here only* as
  byte-preservation fixtures (the alphabet variants and the
  normalization-rejection vectors); the executable round-trip half waits
  for #9.
- **No shared publication.** These vectors are not in the shared
  `conformance/manifest.json` and cite no FHT release URL, because none
  exists; expected outcomes for the V4 vectors are derived from the
  SCHEMA-VERSIONS.md rule text against the verified fact that no FHT
  release exists (registry has no FHT entry; the w3id URL answers 404).
  **No implementation under test produced any expectation in this
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
2. Retire the provisional fields: fold `selfChecksum` and `parentLink`
   into whatever the shared manifest schema formalizes at that point, and
   give T1-T3 their published rule ids in the shared FHT format document.
3. Re-point the `schema` URL: vectors currently cite this repository's
   raw-main URL (the only contract that exists). At release, the same
   bytes move to a new `fht-fasta-schema-*` vector set citing the w3id
   URL, exactly as FHP moved to `…/fhp/v0.4.0`; the raw-main vectors stay
   valid under V1 and keep their ids (ids are never reused or rewritten).
   Any outcome change retires the old id per the shared retirement rule.
4. Add the toolkit invocation to `scripts/check_conformance.py`
   (`--require-format fht-fasta`) once the released reader supports FHT.

Until then, `python scripts/check_fht_fixtures.py` (pinned jsonschema
4.26.0 + PyYAML 6.0.3, see [`../docs/CI.md`](../docs/CI.md)) is the
verification, and its failure classes are the acceptance list for #9's
toolkit implementation.
