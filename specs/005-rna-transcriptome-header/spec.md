# Feature specification proposal: RNA and transcriptome FASTA header (FHT)

Status: **initial development design approved by David; adoption recorded on PR #20 merge**, October 24, 2026.
This is a proposed revision of shared spec 005 at
`980029e5886a1a56a2d2545bfe59c7107539d38d`, developed in the owning FHT repository.
It does not replace the shared publication copy until maintainers review and
coordinate it there. [Research/decisions](../fht-field-decisions.md) provides the
evidence, compatibility impact, maintainer decision and owned follow-ups for #6.

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

- **FR-001:** Import the reviewed shared core and shared objects, pinning their
  provenance through #7. Add required string subject `transcriptome` without
  altering other types. Core constraints remain shared rather than duplicated.
- **FR-002:** Require one `assemblyType` string: `de novo`, `genome-guided` or
  `annotation-derived`, with the D2 construction definitions. Make `moleculeType`
  optional: one producer-justified biological class applying to the whole set,
  selected from `mRNA`, `rRNA`, `tRNA`, `transcribed RNA`. Omit it for unknown or
  heterogeneous sets without a justified uniform classification. Remove the
  old mixed molecule/material enum; no automatic value migration is authorized.
- **FR-003:** Keep optional ordered `assemblySoftware` using shared `Software`;
  optional `sample`, `libraryStrategy`, `strandedness`, `sequencingRuns`,
  `vitalStats`, `completeness` and `derivedFrom`. Do not infer experimental
  metadata from sequence or tool names. `sample` remains a draft object for
  tissue/stage/condition/strain; its exact serialization and controlled tissue
  identifiers require #7 review rather than reusing an invented BioSample schema.
- **FR-004:** Define optional file-wide library fields separately from molecule
  class. `libraryStrategy` is one supplied strategy string, using the producer's
  ENA term where applicable. Proposed `strandedness` enum: `unstranded`, `forward`,
  `reverse`, with D3's explicit read/read-1 orientation convention. Unknown and
  heterogeneous library assertions are omitted, not defaulted or inferred.
- **FR-005:** Statistics are optional producer-reported measurements using D3's
  names, types, units and whole-file population. Reuse shared BUSCO counts where
  representable; do not coerce dotted lineage versions to pass the current pattern.
  No BUSCO, N50, tissue, condition, run or detailed-provenance minimum is imposed.
- **FR-006:** Keep header parsing and checksum coverage alphabet-independent.
  Preserve supplied T/U and all sequence bytes; deposit-specific transformations
  create explicitly derived files with recomputed checksums. Molecule class does
  not prove the alphabet or submission eligibility.
- **FR-007:** Use optional `derivedFrom` only for real reviewed family-file
  relationships. No genome parent is required for de novo. Genome guidance alone
  never establishes a `transcribedFrom` sequence derivation. Source references
  without verifiable family links stay assertions in related URLs/documentation.
  #7 must define the FHT-specific relationship/type/cardinality rules explicitly.
- **FR-008:** Omit unavailable optional values. Required omissions mean an
  incomplete record. Preserve measured zero, array order, dates and numeric types;
  reject unsupported type/version selection without silent latest fallback.
- **FR-009:** Implement migration under #7: remove required `masking`, reconcile
  author roles and reuse conditions, and preserve legacy metadata without guessing
  expression/completeness values. Legacy JSON syntax was repaired in PR #2; this
  proposal does not repeat that repair or implement a new schema.

## Implementation and success criteria

PR #20 completes #6's initial design and consultation disposition on merge. #7 owns
the LinkML model, generated schema, drift/equivalence checks, version selection and
shared publication handoff; #8 owns minimal/rich positive and rejected byte-backed
RNA/cDNA fixtures and exact checksums; #9 owns installed toolkit support and
round trips. FHT currently has no released family contract or toolkit support.

Release and public-pilot outcomes remain under #10: reviewed schema/examples and
conformance evidence, maintainer-controlled release/version/alias decisions, and
a real public transcriptome under appropriate permissions. No DOI, schemaVersion
or successful pilot is invented by these designs. #157 remains the INSDC gate.

## Contract impact for review

This changes proposed requiredness and meaning for moleculeType, proposes a strand
enum and numerical constraints, and clarifies construction semantics. Those are
contract decisions requiring their own review, not incidental documentation fixes.
Released FHR/FHP/FHGFF3 artifacts and the legacy FHT schema are unchanged.
