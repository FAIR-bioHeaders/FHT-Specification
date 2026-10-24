# FHT minimal and rich record designs

Status: **initial design approved by David for adoption on PR #20 merge**, October 24, 2026. These are field-level record
designs, not schema-valid serialized fixtures or headers. No checksum, ORCID,
taxonomy, run accession or release URL is fabricated. Implementation issues #7
and #8 must create actual fixtures after adoption and calculate exact checksums
with the reviewed toolkit. Read [the decisions](fht-field-decisions.md)
and [revised spec 005](005-rna-transcriptome-header/spec.md) together.

## Minimal field set and the decision each enables

| Required field | Type/cardinality proposal | Decision enabled | Value source in a minimal use case |
| --- | --- | --- | --- |
| `schema` | One string, shared selection rules | Select the intended validation contract | Actual supported release URL, assigned through the release process |
| `schemaVersion` | One MAJOR.MINOR string | Interpret the per-type contract | Adopted type registry; no version assigned by this document |
| `transcriptome` | One string | Identify which resource the file describes | Producer-supplied resource label |
| `taxon` | One shared Taxon object | Select the biological scope | Producer-supplied taxonomic identity; do not infer from sequence names |
| `version` | One string | Distinguish resource revisions | Producer's actual resource version |
| `metadataAuthor` | Shared ordered Author array; shared member constraints | Identify responsibility for header assertions | Supplied header-author identities, distinct from assembly authors or submitters |
| `dateCreated` | One date string | Distinguish creation from later edits/collection | Known date the described resource was created |
| `checksum` | One shared SHA-512/256 scalar | Detect file-byte changes | Tool-computed exact-file checksum using adopted exclusion rules |
| `assemblyType` | One proposed enum string | Choose how to interpret construction/source claims | Known workflow history using D2's definitions |

Requiredness applies to the slot; this proposal does not independently tighten
optional nested Taxon/Author members. The actual generated schema must state
array and nested constraints explicitly. Missing a required value cannot be
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
| `moleculeType` | Optional single string from D1's restricted biological vocabulary | Producer-supported uniform class; omit for unresolved or heterogeneous content |
| `assemblySoftware` | Optional ordered array of shared Software objects | Software name, real version, URI and ordered option strings; extraction is a process too |
| `sequencingRuns` | Optional array of run-accession strings | Actual SRR/ERR/DRR runs; no SRS sample identifier substituted for a run |
| `libraryStrategy` | Optional single strategy string | Actual ENA strategy, when one applies to the whole set |
| `strandedness` | Optional single proposed normalized enum | Actual library read/read-1 orientation using D3's convention |
| `sample` | Optional draft object; exact tissue/stage/condition/strain shape deferred to #7 | Actual biological context; never a fabricated pooled identity or complete BioSample record |
| `vitalStats` | Optional object with independently optional numerical properties | totalTranscripts (integer count), N50 (integer nucleotide length), averageTranscriptLength (finite number of nucleotide symbols) |
| `completeness` | Optional shared count object, subject to D3's lineage compatibility note | Actual BUSCO run, software/dataset version, transcriptome mode and counts summing to total |
| `derivedFrom` | Optional shared relationship array, FHT restrictions reviewed in #7 | Actual family parent identities and only relationships the workflow justifies |
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
