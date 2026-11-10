# Feature specification proposal: RNA and transcriptome FASTA header (FHT)

Status: **initial development design approved by David; adoption recorded on PR #20 merge**, October 24, 2026.
This is a proposed revision of shared spec 005 at
`980029e5886a1a56a2d2545bfe59c7107539d38d`, developed in the owning FHT repository.
It does not replace the shared publication copy until maintainers review and
coordinate it there. [Research/decisions](../fht-field-decisions.md) provides the
evidence, compatibility impact, maintainer decision and owned follow-ups for #6.

PR #21 (#7, merged October 24, 2026) implemented these requirements in
[`fht_linkml.yml`](../../fht_linkml.yml) and the generated
[`fht.json`](../../fht.json), including the sample shape and parent rules that
this proposal originally deferred. The requirements below describe that merged
development contract; the [migration record](../../docs/FHT-MIGRATION.md) gives
the field-by-field detail. Where this text and the generated schema disagree,
`fht.json` is the contract.

## User cases

1. A producer publishes a reference-free read assembly with no invented genome
   parent (`de novo`).
2. A producer reconstructs read-supported transcripts using genome guidance
   (`genome-guided`), documenting whether bases come from reads or reference.
3. A producer extracts transcripts from existing annotation coordinates and the
   corresponding genome (`annotation-derived`), identifying both sources when
   known without inventing a sequencing experiment.

The [record designs](../fht-record-designs.md) state minimal and rich cases.

## Proposed requirements

- **FR-001:** Import the reviewed shared core and shared objects, pinned
  verbatim in `schemas/core-v0.4.yaml` and `schemas/shared.yaml` from shared
  commit `980029e5886a1a56a2d2545bfe59c7107539d38d` (v0.4.0/v0.4.1), with
  SHA-256 digests in `schemas/provenance.json` checked by
  `scripts/check_provenance.py`. Add the required non-blank string subject
  `transcriptome` without altering other types. Core constraints remain shared
  rather than duplicated. Exactly nine fields are required: `schema`,
  `schemaVersion` (the string `"1.0"`), `transcriptome`, `assemblyType`,
  `taxon`, `version`, `metadataAuthor`, `dateCreated` and `checksum`.
- **FR-002:** Require one `assemblyType` string: `de novo`, `genome-guided` or
  `annotation-derived`, with the D2 construction definitions. Make `moleculeType`
  optional: one producer-justified biological class applying to the whole set,
  selected from `mRNA`, `rRNA`, `tRNA`, `transcribed RNA`. Omit it for unknown or
  heterogeneous sets without a justified uniform classification. Remove the
  old mixed molecule/material enum; no automatic value migration is authorized.
- **FR-003:** Keep optional ordered `assemblySoftware` using shared `Software`;
  optional `sample`, `libraryStrategy`, `strandedness`, `sequencingRuns`,
  `vitalStats`, `completeness` and `derivedFrom`; the shared optional fields
  `identifier`, `accessionID`, `scholarlyArticle`, `documentation`,
  `relatedLink`, `funding`, `reuseConditions` and `voucherSpecimen`; and the
  legacy-compatible optional fields `transcriptomeSynonym` (non-blank strings),
  `assemblyAuthor` (shared `Author` objects for the people or organizations that
  assembled the set, distinct from `metadataAuthor`) and `instrument`
  (free-text instrument names; prefer `sequencingRuns` when run accessions
  exist). Optional arrays are omitted rather than written empty. Do not infer
  experimental metadata from sequence or tool names. `sample` is a non-empty
  array of `Sample` objects with optional `tissue`, `tissueIdentifier` (a CURIE,
  preferably UBERON, PO or CL; the pattern checks form, not resolution),
  `developmentalStage`, `condition` and `strain`. Each entry must carry at least
  one of these, and text values must be non-blank. Pooled material is repeated
  entries, each with only its own supplied values, not one fabricated uniform
  sample or a complete BioSample record. `sequencingRuns` items must match
  `^(SRR|ERR|DRR)[0-9]+$`; an SRS sample accession is not a run.
- **FR-004:** Define optional file-wide library fields separately from molecule
  class. `libraryStrategy` is one supplied strategy string, using the producer's
  ENA term where applicable. Proposed `strandedness` enum: `unstranded`, `forward`,
  `reverse`, with D3's explicit read/read-1 orientation convention. Unknown and
  heterogeneous library assertions are omitted, not defaulted or inferred.
- **FR-005:** Statistics are optional producer-reported measurements using D3's
  names, types, units and whole-file population: `vitalStats.totalTranscripts`
  (integer >= 0, FASTA records including isoforms), `N50` (integer >= 1) and
  `averageTranscriptLength` (number >= 0). Reuse the shared BUSCO `Completeness`
  object where representable. Its `lineageDataset` must match the pinned
  pattern `^[a-z0-9_]+_odb[0-9]+$`, so dotted dataset versions such as
  `odb12.2` are rejected; do not rename them to pass, but keep the measured
  value in `documentation` until FAIR-bioHeaders-Specification#170 decides.
  No BUSCO, N50, tissue, condition, run or detailed-provenance minimum is imposed.
- **FR-006:** Keep header parsing and checksum coverage alphabet-independent.
  Preserve supplied T/U and all sequence bytes; deposit-specific transformations
  create explicitly derived files with recomputed checksums. Molecule class does
  not prove the alphabet or submission eligibility.
- **FR-007:** Use optional `derivedFrom` only for real reviewed family-file
  relationships. It is a non-empty ordered array whose items accept exactly two
  pairs: parent `headerType: FHT` with `relationship: filteredFrom` (a subset or
  filtered copy of another FHT file), or `headerType: FHR` with
  `relationship: transcribedFrom` (transcript bases extracted from that genome).
  Every item requires the parent's FHR-family `checksum`; `accessionID` is
  additional, never a substitute. `FHP` parents and other relationship values
  are rejected. No genome parent is required for de novo. Genome guidance alone
  never establishes a `transcribedFrom` sequence derivation. Annotations
  (including FHGFF3 files), projects, samples, runs and protocols, and source
  references without verifiable family links, stay assertions in
  `relatedLink`/`documentation`.
- **FR-008:** Omit unavailable optional values. Required omissions mean an
  incomplete record. Preserve measured zero, array order, dates and numeric types;
  reject unsupported type/version selection without silent latest fallback.
- **FR-009:** Migration is implemented under #7 and recorded in
  `docs/FHT-MIGRATION.md`: `masking` is removed, author roles and reuse
  conditions are reconciled, `transcriptomeSynonym`, `assemblyAuthor` and
  `instrument` are retained as optional legacy-compatible fields, and legacy
  metadata is preserved without guessing expression/completeness values. The
  legacy draft schema is kept verbatim in `legacy/fht-v0.1.json` and its
  examples in `legacy/examples/`. Legacy JSON syntax was repaired in PR #2.
- **FR-010:** Accept top-level extension fields as FAIR-bioHeaders-Specification
  `docs/FORMAT.md` R15 defines them (FAIR-bioHeaders-Specification#197): a key
  matching `^x-[A-Za-z0-9][A-Za-z0-9_.-]*$` may hold any value the standard does
  not define; every other unknown key stays invalid, nested objects stay closed,
  no key contains a line feed, and JSON-LD and HTML forms carry none. FHT has no
  released minor, so the draft `"1.0"` includes the rule; there is no older-minor
  restriction as in FHR 2.1 and FHP/FHGFF3 1.1.

## Implementation and success criteria

PR #20 completed #6's initial design and consultation disposition. PR #21
completed #7: the LinkML model, generated schema, drift check, pinned-import
provenance check and migration record. Coordinating this revision into the
shared publication copy is tracked in FAIR-bioHeaders-Specification#107. #8 owns
minimal/rich positive and rejected byte-backed RNA/cDNA conformance fixtures and
exact checksums (the synthetic examples in `examples/` are not those fixtures);
issue #9 owns installed toolkit support and round trips. FHT currently has no
released family contract or toolkit support.

Release and public-pilot outcomes remain under #10: reviewed schema/examples and
conformance evidence, maintainer-controlled release/version/alias decisions, and
a real public transcriptome under appropriate permissions. No DOI, schemaVersion
or successful pilot is invented by these designs. #157 remains the INSDC gate.

## Contract impact for review

This changes proposed requiredness and meaning for moleculeType, proposes a strand
enum and numerical constraints, and clarifies construction semantics. Those are
contract decisions requiring their own review, not incidental documentation fixes.
Released FHR/FHP/FHGFF3 artifacts and the legacy FHT schema are unchanged.
