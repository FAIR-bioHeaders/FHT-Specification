# FHT 1.0 development contract and legacy migration

Status: **development contract for review under #7**, October 24, 2026,
revised for the [curator-review decisions](#curator-review-decisions-november-2026)
of November 2026. This is the model implemented from the design approved
on #6 / PR #20. It is not a published release, not adopted community
guidance, and not supported by the family toolkit. Publication, release tags, immutable URLs and version
confirmation remain joint maintainer actions.

The generated JSON Schema is [`fht.json`](../fht.json); its source is
[`fht_linkml.yml`](../fht_linkml.yml). The legacy draft is preserved verbatim at
[`legacy/fht-v0.1.json`](../legacy/fht-v0.1.json) for audit.

## Canonical implementation path

`FHT-Specification` is the development source for the FHT model and its
generated development contract. `fht_linkml.yml` is the source; `fht.json` is
generated and must never be hand-edited. The reviewed schema artifacts are
expected to publish through FAIR-bioHeaders-Specification, consistent with the
shared family layout recorded for this development cycle. Until that
publication review happens, this repository is not claiming a released
contract, and no independently maintained competing schema is introduced. The
legacy draft is kept only at `legacy/fht-v0.1.json` for audit.

Consumers select a contract by the cited `schema` URL and the matching
`schemaVersion`. An unsupported version is rejected; it is not silently replaced
with raw main or the latest release. Immutable aliases and offline bundle
provenance are publication/toolkit concerns (#9 and the shared release
process), not something this development tree can establish.

## Shared imports and provenance

FHT imports the shared core and shared objects from the FAIR-bioHeaders
Specification repository at commit
`0ae18b00ee4bd71ab2dc28bae706b0f9d195076b`, the `v0.6.0` release. The design
decisions recorded in `specs/fht-field-decisions.md` were made against
`980029e5886a1a56a2d2545bfe59c7107539d38d` (v0.4.0/v0.4.1); between the two,
shared #170 widened the `lineageDataset` pattern, released in v0.6.0, and the
core file is unchanged. The copies in `schemas/` are verbatim:

| File | Source path | Role |
| --- | --- | --- |
| `schemas/core-v0.4.yaml` | `schemas/core.yaml` | Required/optional core slots, `Taxon`, `Author`, `DerivedFrom`, `HeaderType`, `DerivationRelationship` |
| `schemas/shared.yaml` | `schemas/shared.yaml` | `Software` and BUSCO `Completeness` objects |

`schemas/core.yaml` is byte-identical at v0.4.0, v0.4.1, v0.5.0, v0.6.0 and
the pinned commit; `schemas/shared.yaml` is the v0.6.0 file. Their
SHA-256 digests are recorded in [`schemas/provenance.json`](../schemas/provenance.json)
and checked by `scripts/check_provenance.py`. Replace them from a reviewed
release; do not edit them here.

## Contract version and URLs

The proposed contract version is `schemaVersion: "1.0"` (a string, MAJOR.MINOR),
separate from the transcriptome `version`, a repository release tag and the
file checksum. The generated schema keeps the development `$id`
`https://raw.githubusercontent.com/FAIR-bioHeaders/FHT-Specification/main/fht.json`.
The accepted `schema` value may be that raw-main URL, a future raw tag URL, or a
versioned `https://w3id.org/fair-bioheaders/fht/vX.Y.Z` URL. **No w3id alias or
release tag is published by this change.** Confirm the release line and alias
with maintainers before citing them.

## Required fields

Exactly these nine fields are required, every time, with no exceptions; each has
a real supplied value:

| Field | Contract |
| --- | --- |
| `schema` | FHT schema URL under the pattern above |
| `schemaVersion` | `"1.0"` |
| `transcriptome` | Resource name |
| `assemblyType` | `de novo`, `genome-guided` or `annotation-derived` |
| `taxon` | Shared `Taxon` object |
| `version` | Resource version |
| `metadataAuthor` | Ordered shared `Author` array |
| `dateCreated` | Resource creation date, never the sample collection date |
| `checksum` | Exact-file SHA-512/256, 44-character base64 |

Missing required values cannot be repaired with `null`, `unknown`, a guessed
person or a placeholder checksum. The record is incomplete.

A required key must also carry a value. The schema rejects the empty forms that
FHR 2.0 still accepts and plans to reject in its next major (shared
`docs/SCHEMA-VERSIONS.md`, "Required values are non-empty", GAP-1):

| Field | Rule |
| --- | --- |
| `transcriptome`, `version` | `minLength: 1` and at least one non-whitespace character |
| `dateCreated` | `minLength: 1` and a non-whitespace character, plus the `date` format |
| `metadataAuthor` | `minItems: 1`; every author requires a non-blank `name` (the shared `Author` object, so `assemblyAuthor` items too) |
| `taxon` | Unchanged by maintainer decision (#8, 2026-11-16): `name` and `uri` stay optional members, and no taxonomy identifier is required. The next FHR, FHP and FHGFF3 majors will require an NCBI Taxonomy or ITIS `uri` (shared #189); that is not imported into FHT |
| `schema`, `schemaVersion`, `assemblyType`, `checksum` | Already non-empty through their pattern, enum or exact length |

## Optional fields

`moleculeType`, `assemblySoftware`, `sample`, `libraryStrategy`,
`strandedness`, `sequencingRuns`, `vitalStats`, `completeness`, `derivedFrom`,
`identifier`, `accessionID`, `scholarlyArticle`, `documentation`,
`relatedLink`, `funding`, `reuseConditions`, `voucherSpecimen`, plus the
legacy-compatible `transcriptomeSynonym`, `assemblyAuthor` and `instrument`.

Omit an optional value when it is unknown or is not true of the whole set. Do
not write empty strings, empty arrays or null sentinels. A measured zero is
kept.

### Molecule, library and alphabet

`moleculeType` is one biological class for the whole set: `mRNA`, `rRNA`,
`tRNA` or `transcribed RNA`, or `mixed` when the set is known to contain more
than one class (for example mRNA with rRNA or long non-coding RNA). It is
optional. `mixed` is a statement about known content, not a value for unknown:
a set whose class is unknown omits the field. `total RNA` and `cDNA` are
preparation contexts and are not accepted as molecule classes, and neither one
establishes `mixed` by itself. Do not infer `mRNA` from RNA-Seq, `cDNA` from T/U
bytes, or `transcribed RNA` from `ncRNA`. `mixed` has no single INSDC
`/mol_type` equivalent; a deposit needs per-record values.

`libraryStrategy` is one supplied strategy string, not a frozen ENA enum.
`strandedness` is the FHT normalization `unstranded`, `forward` or `reverse`:
forward means the single read or read 1 is sense relative to the originating
transcript; reverse means antisense. It is not an ENA enum and does not
describe genomic plus/minus orientation. Unknown or mixed protocols are omitted.

Record the library protocol or kit name in `documentation` and a protocol URL in
`relatedLink`, alongside `strandedness`. Do not infer strandedness from a kit
name, and do not put the library protocol in FHR's assembly-specific
`assemblyProtocol` (FHT has no such field).

FASTA parsing and checksums are alphabet-independent. T/U conversion is an
explicit derivative with a new checksum, never a header-parser fix.

### Sample and pooled material

`sample` is an optional **array** of `Sample` objects. It holds the biological
context that FHR has no field for; everything else about the source follows FHR
(see the table below). Each object has optional
`tissue`, `tissueIdentifier`, `developmentalStage`, `condition` and `strain`.
`tissueIdentifier` is a CURIE (for example `UBERON:0000473`); the pattern checks
form, not resolution. Each entry must carry at least one supplied field, and its
text fields must be non-empty. Pooled material is represented by repeated
entries, each with only its own supplied values. Do not collapse a pool into one
fabricated uniform sample or treat a header entry as a complete BioSample record.

How FHT records the source material, compared with FHR (`fhr.json` at shared
`v0.6.0`, shared `docs/TERMS.md` and `docs/MAPPINGS.md` "Identifier
Conventions"):

| Source information | FHR | FHT |
| --- | --- | --- |
| Organism | `taxon` | `taxon`, the same shared object |
| Physical specimen or voucher | `voucherSpecimen` (free text; structured vouchers are shared #139) | `voucherSpecimen`, the same shared slot; it follows #139 when that is decided |
| BioSample or other sample record | URL in `relatedLink` (for example `https://www.ncbi.nlm.nih.gov/biosample/SAMN…`) | The same: URL in `relatedLink`. No separate sample-accession field |
| BioProject, study, experiment | URL in `relatedLink` | The same |
| The data's own identifiers | `identifier`, `accessionID` (never a sample) | The same |
| Tissue, developmental stage, condition, strain | No field | `sample` items (`tissue`, `tissueIdentifier`, `developmentalStage`, `condition`, `strain`), FHT-specific |
| Pooled sources | No field (one specimen description) | Repeated `sample` items |

`tissueIdentifier` keeps its preference for UBERON, PO and CL; FHR has no
ontology-term field to align it with.

### Construction cases and parents

`assemblyType` describes construction, not quality or deposit class.

| Value | Meaning | Parent treatment |
| --- | --- | --- |
| `de novo` | Reads reconstructed without a reference genome constructing or grouping the assembly; later QC alignment does not reclassify it | No genome parent is required |
| `genome-guided` | Read evidence plus a reference constructed models or grouped reads; bases may come from reads or a later extraction | Genome guidance alone never justifies `transcribedFrom` |
| `annotation-derived` | Sequences extracted from existing annotation coordinates and the matching genome, without new read assembly in this step | Identify both sources when known; link the genome by `transcribedFrom` only when bases were extracted from it |

These three values are the whole controlled vocabulary. A composite or
uncertain history (for example a de novo assembly merged with genome-guided
models, or a reference annotation extended with new models) has no `mixed` or
`unknown` value. Do not guess or pick the dominant step. Because `assemblyType`
is required, such a record is incomplete, as FHR treats any required value that
is unavailable: describe the history in `documentation` and raise the case for
maintainer review. A new construction value would be a contract change.

A genome-guided set whose final sequences were written out from the genome, for
example StringTie models extracted with gffread, takes its bases from that
genome. It therefore links the genome as an `FHR` + `transcribedFrom` parent with
the genome file's FHR checksum, exactly as an annotation-derived extraction does.
A genome-guided set whose bases come from the reads (for example genome-guided
Trinity) does not. The `assemblyType` stays `genome-guided` either way.

`derivedFrom` accepts only these reviewed pairs:

| Parent `headerType` | Allowed `relationship` | Condition |
| --- | --- | --- |
| `FHT` | `filteredFrom` | This set is a subset or filtered copy of another FHT file |
| `FHR` | `transcribedFrom` | Transcript bases were extracted from that genome, not merely guided by it; this includes a genome-guided set written out from the genome |

The shared `DerivedFrom` object requires `headerType`, `relationship` and the
parent's FHR-family `checksum`; `accessionID` is additional, not a substitute
for a verified family link. `FHP` parents and other relationship values are not
accepted. An FHGFF3 annotation, project, study, sample, run or protocol is
context, not a sequence-derivation parent: link it through
`relatedLink`/`documentation` until the shared relationship vocabulary (#54) is
decided. `derivedFrom` items are ordered and at least one item is required when
the array is present.

### Statistics and completeness

`vitalStats` is optional and producer-reported:

- `totalTranscripts`: integer >= 0, number of FASTA records including isoforms;
- `N50`: integer >= 1, computed from all sequence symbols by descending record
  length;
- `averageTranscriptLength`: number >= 0, sequence symbols per record excluding
  deflines and line endings.

`completeness` reuses the shared BUSCO count object (`lineageDataset`,
`buscoVersion`, `mode`, four disjoint counts and `total`). BUSCO counts describe
ortholog groups, not FASTA records or genes; `total` is the number of BUSCO
groups searched. Only `vitalStats.totalTranscripts` counts FASTA records. BUSCO
is not a quality cutoff.

The shared lineage pattern accepts `_odb` plus digits and, since
FAIR-bioHeaders-Specification#170 at v0.6.0, one or more dot-separated numeric
version components such as `odb12.2`. A measured lineage is **not renamed or
coerced** to fit the pattern; malformed forms (`odb12.`, `odb.12`, `odb12..2`,
`odb12.2b`) stay rejected. If a measured value cannot be represented in the
typed object, keep it in `documentation` rather than falsifying the lineage.

## Curator-review decisions (November 2026)

David Molik answered the nine questions of the curator-review packet. His
general rule was to follow FHR's logic for the fields that are not FHR's. These
are changes to the unreleased draft contract; `schemaVersion` stays `"1.0"`
because nothing has been released.

| Question | Decision | Contract change |
| --- | --- | --- |
| Q1 construction types | "de novo, genome-guided and annotation-derived are a good start, we should implement the controlled vocabulary for this now" | None: `assemblyType` was already exactly these three values. Mixed histories stay incomplete until reviewed (above); edge-case tests added |
| Q2 molecule type | "mixed is acceptable, so it should be five values" | `mixed` added to `moleculeType` |
| Q3 strand | Keep forward/reverse; "protocol name or kit should have a way to be recorded as well" | `strandedness` unchanged; the protocol or kit name goes in `documentation` and a protocol URL in `relatedLink` |
| Q4 required fields | "absolutely required, everytime, no exceptions"; current taxon rules kept | The nine stay required; empty strings, empty author lists and nameless authors are rejected. `taxon` is unchanged |
| Q5 missing fields | Nothing to add | None |
| Q6 measurements | Statistics and units stay | None |
| Q7 sample | "check what FHR does for this, do that" | Description only: sample records and specimens follow FHR (table above); `sample` keeps the FHT-specific context |
| Q8 parent links | Keep the drafted behaviour | Description only: a genome-guided set written out from the genome links it by `transcribedFrom` |
| Q9 names | Names stay | None |

Compatibility within the draft: every existing example, conformance vector and
the real-data pilot header still validates. A record is newly rejected only if
it has an empty required string, an empty author list or an author without a
name. The `de-novo` and `genome-guided` examples now name their library kits
(and genome-guided records `moleculeType: mixed`) and were regenerated with new
checksums. The conformance vectors do not use `mixed` yet: the released
toolkit's draft lane is pinned to the previous `fht.json` and would reject a
valid vector that carries it, so the value is covered by unit tests until #9
moves that pin.

## Legacy migration (fht.json v0.1 → FHT 1.0)

Migration is explicit. Preserve the original header bytes and supplied
metadata; do not guess values or silently promote a legacy record.

| Legacy field | FHT 1.0 treatment |
| --- | --- |
| `schema` | Keep a valid FHT contract URL. The old value may be malformed; correct the URL, not the transcriptome identity |
| `schemaVersion` | Number `1`/`1.0` becomes string `"1.0"` |
| `transcriptome`, `transcriptomeSynonym`, `taxon`, `version` | Retained. Do not repair a supplied taxon URI or synonym |
| `metadataAuthor` | Retained as header authors. Legacy `url` is not an `Author` member: map to `uri` only when it is a valid ORCID URL; the pinned shared pattern does not accept ROR or other organization URLs, so preserve those in `documentation`/`relatedLink` |
| `assemblyAuthor` | Retained as optional attribution, distinct from header authors and from a deposit submitter. Never merge the roles |
| `dateCreated` | Retained; it is resource creation, not sample collection |
| `assemblySoftware` | Legacy string becomes an array of shared `Software` objects: `name` from the supplied value. Add `version`/options only when actually supplied; never invent a version |
| `sample`, `libraryStrategy`, `strandedness`, `sequencingRuns` | Not inferred from the legacy record. Add only supplied values; an SRS sample accession is not a run |
| `instrument` | Retained as the legacy-compatible free-text array. Prefer run accessions when available |
| `vitalStats` | Keep `totalTranscripts`, `N50`, `averageTranscriptLength` when measured. `GCContent`, `isoformDiversity`, `expressionLevels`, `novelTranscripts` and the free-text `transcriptomeCompleteness` are not guessed into typed fields; preserve any needed text in `documentation` |
| `completeness` | Only from an actual BUSCO run with counts. A legacy completeness string is not converted into counts |
| `accessionID`, `identifier` | Retained as the transcriptome's own identifiers. Project/sample/run links belong in `relatedLink` |
| `scholarlyArticle` | Retained as a bare DOI; remove a resolver prefix only, do not invent a DOI |
| `documentation`, `relatedLink`, `funding`, `voucherSpecimen` | Retained |
| `license` | Reviewed separately into `reuseConditions`; do not copy blindly when the value is a name, a URL or a third-party notice |
| `masking` | Removed: a genome-assembly field with no FHT meaning. Do not add it back to pass older records |
| `checksum` | Legacy `md5:` values are not valid FHT checksums. Recompute SHA-512/256 from the exact file with the reviewed toolkit; never convert an MD5 string |
| Unknown legacy keys | Not accepted by the schema, which is closed except for top-level extension fields (`x-` keys, FAIR-bioHeaders-Specification `docs/FORMAT.md` R15). Decide explicitly whether to retain a value in documentation, move it to a standard field, or keep it under an extension key such as `x-<project>-<field>`; do not silently drop supplied metadata, and do not put a standard field's value only in an extension key |

The legacy examples are preserved verbatim in `legacy/examples/` as historical
review inputs, not valid FHT 1.0 fixtures. `examples/` holds synthetic examples
that validate against `fht.json`, one per construction type, checked by
`tests/test_examples.py`. Actual byte-backed positive and rejection conformance
fixtures, including RNA and cDNA bytes, are owned by #8.

## Verification and publication boundary

Run:

```sh
python -m unittest discover -s tests -v
python json-schema-generator.py
git diff --exit-code fht.json
python scripts/check_provenance.py
```

This PR supplies the model, generated schema, migration record, drift check and
validation tests. It does **not** publish a schema, assign a release tag or
w3id alias, add toolkit support, validate INSDC submission readiness, or create
the #8 fixtures. Those remain separate review gates (#8, #9, #10 and the
independent #157 assessment).

## Related records

- Issue #7: schema implementation and migration.
- Issue #6 / PR #20: approved initial design.
- `specs/fht-field-decisions.md`, `specs/fht-record-designs.md`,
  `specs/005-rna-transcriptome-header/spec.md`.
- Shared #54 (relationship vocabulary), #157 (INSDC coverage) and #170 (BUSCO
  lineage grammar).
