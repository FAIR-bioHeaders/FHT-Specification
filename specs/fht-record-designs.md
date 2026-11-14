# FHT minimal and rich record designs

Status: **initial design approved by David for adoption on PR #20 merge**, October 24, 2026. These are field-level record
designs, not schema-valid serialized fixtures or headers. No checksum, ORCID,
taxonomy, run accession or release URL is fabricated. PR #21 (#7) implemented
the design in [`fht_linkml.yml`](../fht_linkml.yml) and the generated
[`fht.json`](../fht.json); the tables below describe that merged development
contract, and `fht.json` governs where they differ. Synthetic schema-valid
examples with computed checksums are in [`examples/`](../examples/); byte-exact
conformance fixtures remain owned by #8. Read [the decisions](fht-field-decisions.md)
and [revised spec 005](005-rna-transcriptome-header/spec.md) together.

## Minimal field set and the decision each enables

| Required field | Type/cardinality proposal | Decision enabled | Value source in a minimal use case |
| --- | --- | --- | --- |
| `schema` | One string, shared selection rules | Select the intended validation contract | Actual supported release URL, assigned through the release process |
| `schemaVersion` | One MAJOR.MINOR string; the development contract accepts only `"1.0"` | Interpret the per-type contract | Adopted type registry; `"1.0"` is proposed, not released (#10) |
| `transcriptome` | One string | Identify which resource the file describes | Producer-supplied resource label |
| `taxon` | One shared Taxon object | Select the biological scope | Producer-supplied taxonomic identity; do not infer from sequence names |
| `version` | One string | Distinguish resource revisions | Producer's actual resource version |
| `metadataAuthor` | Shared ordered Author array; shared member constraints | Identify responsibility for header assertions | Supplied header-author identities, distinct from assembly authors or submitters |
| `dateCreated` | One date string | Distinguish creation from later edits/collection | Known date the described resource was created |
| `checksum` | One shared SHA-512/256 scalar | Detect file-byte changes | Tool-computed exact-file checksum using adopted exclusion rules |
| `assemblyType` | One proposed enum string | Choose how to interpret construction/source claims | Known workflow history using D2's definitions |

Requiredness applies to the slot; the contract does not independently tighten
optional nested Taxon/Author members. The generated schema states array and
nested constraints explicitly: optional arrays need at least one item when
present, and empty strings or `null` are not unknown-value sentinels. Missing a required value cannot be
repaired with `null`, `unknown`, a guessed person or a dummy checksum.

## Three minimal record designs

All three designs contain the nine fields above with genuine supplied values and
an actual computed checksum after implementation. Additional fields below are
optional assertions, not hidden validity requirements.

| Design | Construction and required enum | Deliberately optional/absent | Rich counterpart |
| --- | --- | --- | --- |
| M1: reference-free assembly | Reads reconstructed without reference guidance; `assemblyType: de novo` | No reference parent; omit moleculeType if biological class is not known for the whole set | Add measured statistics, actual software/version/options, run accessions and linked study/sample metadata |
| M2: read reconstruction with reference guidance | Read-supported models/grouping uses a reference; `assemblyType: genome-guided` | No automatic transcribedFrom link, sequencing-method inference or molecular-class guess | Document genome identity, how it guided reconstruction, actual run/experiment metadata and reviewed family parent links where justified |
| M3: existing annotation extraction | Coordinates plus matching genome supply transcript sequence; `assemblyType: annotation-derived` | No invented raw reads, sample, library strategy or strandedness | Link the actual annotation and genome resources; record extraction software/version and independently measured sequence statistics |

Known construction mode is needed to claim any of these proposed minimal cases.
An uncertain/composite historical record remains incomplete until reviewed; no
unknown or mixed value is silently accepted. Minimal-header validity would not
prove TSA deposit eligibility or successful checksum/parent verification.

## Rich design: optional additions and preservation rules

| Field/group | Proposed type/cardinality | Example of information to supply when actually known |
| --- | --- | --- |
| `transcriptomeSynonym` | Optional non-empty array of non-blank strings (legacy-compatible) | Other names actually used for the transcriptome |
| `moleculeType` | Optional single string: `mRNA`, `rRNA`, `tRNA` or `transcribed RNA` (D1) | Producer-supported uniform class; omit for unresolved or heterogeneous content |
| `assemblyAuthor` | Optional non-empty ordered array of shared Author objects (legacy-compatible) | People or organizations that assembled or extracted the set, distinct from `metadataAuthor` and from a deposit submitter |
| `assemblySoftware` | Optional ordered array of shared Software objects | Software name, real version, URI and ordered option strings; extraction is a process too |
| `sequencingRuns` | Optional non-empty array of strings matching `^(SRR\|ERR\|DRR)[0-9]+$` | Actual SRR/ERR/DRR runs; no SRS sample identifier substituted for a run |
| `instrument` | Optional non-empty array of non-blank free-text names (legacy-compatible) | Instrument names actually supplied; prefer `sequencingRuns` when run accessions exist, and do not infer an instrument from a run or software name |
| `libraryStrategy` | Optional single strategy string | Actual ENA strategy, when one applies to the whole set |
| `strandedness` | Optional single enum: `unstranded`, `forward` or `reverse` | Actual library read/read-1 orientation using D3's convention |
| `sample` | Optional non-empty array of Sample objects, each with at least one of `tissue`, `tissueIdentifier` (CURIE), `developmentalStage`, `condition`, `strain` | Actual biological context; pooled material as repeated entries, never a fabricated pooled identity or complete BioSample record |
| `vitalStats` | Optional object with independently optional numerical properties | totalTranscripts (integer >= 0), N50 (integer >= 1, nucleotide length), averageTranscriptLength (number >= 0 of nucleotide symbols) |
| `completeness` | Optional shared count object; `lineageDataset` must match `_odb` plus one or more dot-separated numeric version components (widened by shared #170, pinned at v0.6.0), so `odb12.2` is representable while malformed forms stay rejected | Actual BUSCO run, software/dataset version, transcriptome mode and counts summing to total; a measured lineage is never renamed or coerced |
| `derivedFrom` | Optional non-empty ordered array of shared DerivedFrom objects; only `FHT` + `filteredFrom` or `FHR` + `transcribedFrom`, each with the parent checksum (`accessionID` is additional, not a substitute) | Actual family parent identities and only relationships the workflow justifies |
| `identifier` / `accessionID` | Shared optional self-identifiers | Transcriptome's own accession, not its project/sample accession |
| `relatedLink` / `documentation` | Shared optional URL array / string | Source records, experiment metadata, protocol and derivation explanation |
| `reuseConditions`, `scholarlyArticle`, `funding`, `voucherSpecimen` | Shared optional fields | Supplied reuse terms, article DOI, funding and specimen context |

For the rich M3 case, intentionally leave read/library/sample groups absent if
the source annotation does not establish them. For rich M1/M2, retain per-run
differences externally instead of forcing conflicting experiment values into a
single file-wide scalar. FASTA-record counts describe records, not genes; BUSCO
counts describe ortholog groups. BUSCO scores do not establish that every
transcript is complete or experimentally expressed.

## Required implementation acceptance after adoption

- Validate actual positive M1/M2/M3 and rich fixtures against the adopted contract,
  including omission of every optional group and genuine numeric zero values.
- Reject missing required values, unsupported enums/types/versions and invented
  null sentinels; exercise the exact reviewed nested/cardinality rules.
- Verify numeric statistics on known input bytes, schema-valid versus file-valid
  versus parent-verified outcomes, and RNA/cDNA exact-byte round trips.
- Test mixed library metadata without lossy coercion, no reference parent for M1,
  and no false genome-sequence derivation for read-reconstructed M2.
- Preserve original legacy metadata through explicit migration; do not overwrite
  old header bytes or silently promote these design tables to released fixtures.
