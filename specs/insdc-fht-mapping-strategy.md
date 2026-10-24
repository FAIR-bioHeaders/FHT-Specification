# FHT → INSDC minimum-specification mapping strategy

**Draft version:** 0.1.0-draft.1
**Status:** proposal
**Checked on:** 2026-10-24
**Pinned versions:**
- INSDC Minimum Specifications v1.0 at `insdc/minimum-specifcations@41f0dc4` (2026-07-06)
- FHT draft fields from spec 005-rna-transcriptome-header/spec.md (FR-002, FR-003)
- FHT-Specification main @ `92f652d`
- AgBioData profile model as reference: `profiles/agbiodata-fhr.yaml`

---

## Purpose

This document describes the INSDC submission-mapping strategy for FHT transcriptome headers. It follows the community-profile pattern established by the AgBioData FHR profile: requirements that are specific to a deposit target go into a mapping/profile layer, not the base schema contract.

**Nothing here changes any published bytes.** This is an exercise in documenting how existing FHT fields map to INSDC minimums when submitters need to prepare a transcriptome deposit, and where gaps require separate action.

---

## Mapping principles (from the federation-wide pattern)

1. **Never invent missing data.** Per `docs/MAPPINGS.md` MIxS projection conventions: missing source fields are reported as omissions; no values are fabricated.
2. **Profile over schema edit.** Transcriptome-specific requirements go into community profiles (#51/#156), not the base contract.
3. **CURIE for cross-database links.** `relatedLink` carries URLs; `identifier` reserves for the transcriptome's own accession.
4. **Separate file-bound from repository metadata.** Geographic location, collection date, and per-record sequence properties are BioSample-layer concerns, not file-header concerns.
5. **Report losses explicitly.** Each mapping row states what is preserved, lost, or conditional — never implied equivalence without conditions.

---

## Table 1 — INSDC categories → FHT field mappings (submission-ready)

### Assembly minimums (Category: Assembly v1.0)

| # | INSDC requirement | FHT field(s) | Relationship | Loss / condition |
|---|---|---|---|---|
| A.a | BioProject link | `relatedLink` → `https://www.ncbi.nlm.nih.gov/bioproject/PRJN……` or `identifier: bioproject:PRJ…` | Exact (if provided) | No dedicated `project` field in base contract; submitters must supply manually. CURIE format not enforced by schema. |
| A.b | BioSample link | `relatedLink` → `https://www.ncbi.nlm.nih.gov/biosample/SAMN……` or `identifier: biosample:SAMN…` | Exact (if provided) | No dedicated `sample` field in base contract. FHT FR-003 optional `sample` struct (tissue/UBERON, stage, condition, strain) carries biological context but not an accession. Community profile (#51) can add `sampleIdentifier`. |
| A.c | Submitter identity | `metadataAuthor[].name` + `metadataAuthor[].uri` (ORCID) | Partial | ORCID identifies individuals; does not express organizational affiliation for consortium submissions. No free-text `affiliation` field in shared core. Per-record: submitter ≠ author necessarily. For submission: submitters must supplement with institution name from other metadata. |
| A.d | TaxID at species rank or below | `taxon.uri` → `https://identifiers.org/taxonomy:<NCBI taxid>` | Exact pattern match | **Rank not schema-checkable.** Pattern-pinned but no mechanism to assert rank ≤ species. Requires online resolution (assess `--online`). Not a blocker: NCBI taxonomy resolves rank at the URI level. |
| A.e | Moltypes appropriate for genome/transcriptome | `moleculeType` (FR-002, draft): mRNA / total RNA / cDNA / ncRNA | Direct analogue | **Pending curator review** per #6. No INSDC-controlled vocabulary alignment yet. Value meanings (biological molecule vs. library material) unresolved. Candidate for profile-defined controlled vocabulary if curators confirm a subset. |
| A.j | Assembly method/version; sequencing technologies | `assemblySoftware` (structured: name/uri/commandLineOption), `sequencingRuns`, `instrument`, `dateCreated` | Partial → Full when all provided | `assemblyProtocol` not a base-field in the shared core (legacy only from fht.json). FHT FR-003 offers `assemblySoftware` (name required) + `sequencingRuns` (SRA accessions) — sufficient for method identification. No version field on `assemblySoftware` schema object at shared-core level; submitters must supply in `commandLineOption`. `instrument` from legacy fht.json is an uncontrolled string, not a controlled vocabulary. |
| A.ver | Versioning: increment on sequence change only | `version` (free-text) + `checksum` (SHA-512/256) | Divergent by design | FH checksum recomputes on any byte change including header edits. INSDC: metadata-only ≠ version bump. Document divergence for submitters: FH identity model is file-bound, INSDC is repository-record-bound. |

### Sequence minimums (Category: Sequence v1.0) — transcriptome-relevant subset

| # | INSDC requirement | FHT field(s) | Relationship | Loss / condition |
|---|---|---|---|---|
| S1 | T instead of U for all sequences | `moleculeType` (context only) | Deliberate divergence | RNA FASTA may use U in sequence data (FR-006). Header parsing and checksums are alphabet-independent. Documented as design choice, not gap. If INSDC requires T enforcement, a profile can add alphabet-constraint rule — base schema unchanged. |
| S10 | Contamination screening; screening checksum report (proposed) | `assemblySoftware` + `assemblyProtocol` | Conceptual alignment | Screening tools and protocols expressed as structured provenance. No structured "screening result" evidence field yet. The philosophy aligns: INSDC's proposed checksum-verified screening reports = FH's exact-byte-checksum stance. Future addition via profile if requested. |
| S13 | Technique keywords validated against molecule type | `assemblyType` (de novo / genome-guided / annotation-derived) + `moleculeType` | File-level analogue | FHT uses typed enums instead of INSDC free-text keywords (HTGS/STS/GSS/WGS/TSA). Cross-validation ("TSA ≠ DNA") would need profile-level constraint. Not a gap: FH's approach is more structured, but the value sets differ. Document mapping in submission guidance. |
| S-xref | Cross-references within categories | `scholarlyArticle` (DOI), `identifier` (CURIE), `relatedLink`, `accessionID`, `derivedFrom` (if opted in) | Partial | Study/sample/project links by CURIE convention only — not enforced patterns. `derivedFrom` inherited from FHP/FHGFF3 via shared core; FHT opt-in per FR-003 but pattern/authority rules TBD. Publication link is direct DOI pattern match. |
| S-ver | accession.version scheme | `version` (free-text) + required schema/version identity | Structural analogue, different semantics | FH: free-text version bound to file-byte identity via checksum. INSDC: structured accession.version with lifecycle rules. Document divergence; not a gap (different layers). |

### Sample minimums (Category: Sample v1.0) — FHT-relevant subset

| # | INSDC requirement | FHT field(s) | Relationship | Loss / condition |
|---|---|---|---|---|
| SM-alias | Sample Alias unique across submission | `sample` struct fields (tissue/UBERON, stage, condition, strain) or community profile `sampleIdentifier` | Partial | No sampleAlias field in base contract. FHT FR-003 optional `sample` carries tissue/UBERON/stage/condition/strain — descriptive context, not submission alias. Community profile can add dedicated alias with uniqueness constraint. |
| SM-org | Organism name (NCBI Taxonomy) | `taxon.name` + `taxon.uri` | Exact for name; rank-limitation noted in A.d | Rank checking requires online resolution; schema pattern only validates URI format, not species-level assertion. Same as all FH types. Not a blocker: NCBI taxonomy resolves at the URI level. |
| SM-geo | Geographic location | — | ✗ Not covered | Absent from every FH type per this ticket's guidance (Geo → BioSample/MIxS layer). Submitters supply via sample-submission metadata, not file header. |
| SM-date | Collection date | `dateCreated` | Partial divergence | `dateCreated` = assembly creation date. MAPPINGS.md already warns: NOT a sample collection date. Must be distinguished in submission guidance. Collection date is a sample-layer concern (BioSample). |
| SM-sub | Submitter name and affiliation | `metadataAuthor[].name` + `metadataAuthor[].uri` | Partial | Name only — no free-text affiliation field in shared core. `nameType: Organizational` classifies the author, not expresses their institution. For INSDC submission: submitters must add institutional affiliation through sample-submission fields. |

---

## Experiment category → FHT mapping (file-level proxy)

| # | INSDC requirement | FHT field(s) | Relationship |
|---|---|---|---|
| E-lay | Library strategy (ENA controlled vocabulary) | `libraryStrategy` (FR-003, free string) | Candidate for controlled vocabulary in spec 005 if curators confirm. Per AgBioData profile pattern: draft-controlled enum as profile constraint, not base schema edit. If aligned with ENA values (poly-A, total RNA, cDNA, rRNA-depleted, etc.), submitters can use exact INSDC terms. |
| E-sel | Library selection (poly-A, random, oligo-dT) | — | ✗ Not in draft FR-003. Could be added via community profile as part of `libraryProfile` struct or standalone field if curators need it. Document as future candidate. |
| E-str | Strandedness (unstranded/firststrand/secondstrand) | `strandedness` (FR-003, free string) | Candidate for controlled vocabulary in spec 005 aligned with ENA values: `unstranded`, `firststrand`, `secondstrand`. Small schema addition benefiting from curator input. |
| E-pla | Platform / sequencing instrument | `instrument` (legacy fht.json, uncontrolled string list) + `sequencingRuns` (FR-003, SRA accessions) | Accept as-is for now. A controlled vocabulary is a schema addition — only if curators request it. SRA accession links provide verifiable run provenance. |

---

## Submission-mapping notes for FHT submitters

### When an FHT header maps to INSDC deposit metadata

| FH field | INSDC target | Instructions |
|---|---|---|
| `taxon.uri` | BioSample → Organism | Extract NCBI taxID from URI; supply in BioSample `organism` field. |
| `metadataAuthor[].name` + `[]uri` | Project/Study submitter | Copy name to submission's `submitter.name`. ORCID → `submitter.orcid` if supported. For consortium: add institution via BioSample `contactInstitution`. |
| `dateCreated` | Assembly creation date | Document: **not** a sample collection date. Supply collection date separately in BioSample metadata. |
| `assemblySoftware[].name` + `[].commandLineOption` | Assembly method description | Construct INSDC `assemblyMethod` string from name + parameters. Version in commandLineOption if present. |
| `moleculeType` (FR-002) | Library source / material | Map as: mRNA → `transcriptomic`, total RNA → `total RNA`, cDNA → `cDNA`, ncRNA → `noncoding RNA`. Pending curator confirmation of alignment. |
| `assemblyType` (FR-002) | Assembly type context | de novo = no reference used; genome-guided = aligned to reference; annotation-derived = transcriptome derived from annotation. Document as metadata for submitters, not a required mapping field. |
| `sequencingRuns[]` | Raw data dependency | Map each SRA accession (SRR/SRS prefix) to BioProject→Study→Run chain. Not enforced by schema — submitters must verify linkage. |
| `scholarlyArticle` | Publication | Copy bare DOI; resolve if needed via crossref API for deposit metadata. |
| `relatedLink` | BioProject / BioSample URLs | Submitter supplies: `https://www.ncbi.nlm.nih.gov/bioproject/PRJN…`, `https://www.ncbi.nlm.nih.gov/biosample/SAMN…`. No CURIE pattern enforcement in base contract. |
| `accessionID.name` + `[].url` | Primary transcriptome accession | If provided: use as primary identifier for the assembly/transcriptome. Prefix not enforced — submitters must supply INSDC-compatible format (GCA_/GCF_ or community prefix). |

### Items requiring separate submission-layer metadata

| INSDC requirement | Not in FHT header; must be supplied elsewhere |
|---|---|
| Geographic location (SM-geo) | BioSample `geographic_location` — collected during sample submission, not embeddable in file header |
| Sample collection date (SM-date) | BioSample `collection_date` — distinct from FHT `dateCreated` (assembly creation date) |
| Per-record sequence properties (S12) | Unified-FASTA per-record defline metadata — future work if INSDC unified format materializes |
| Project/study hierarchy | BioProject/Study relationship — external to file-bound header; supply via CURIE in `relatedLink` |
| Checksum-verified screening results (S10) | Not yet supported. Documented as alignment opportunity with FH checksum philosophy |

### Metadata field length note (A.k: ≤1000 characters per field)

FH headers impose no character limits on any field (R11 escaping only). If submitters export FH values into INSDC submission fields, they must verify length compliance at the deposit boundary. A community profile can add enforcement as a constraint — not a base-schema change.

---

## AgBioData-profile pattern for FHT INSDC requirements

Following `profiles/agbiodata-fhr.yaml` as reference, an FHT-specific INSDC mapping profile would:

1. **Import the draft FHT schema** (once published) or the shared core + FHT additions
2. **Add constraints on top**: controlled vocabularies for `libraryStrategy`, `strandedness`; CURIE patterns for `relatedLink` project/sample values; alphabet constraint if T-only is required
3. **Never edit the base schema.** Community requirements are layered, not merged

Example structure (draft profile model, following AgBioData FHR pattern):

```yaml
# Draft: FHT INSDC mapping profile — not adopted, not published
id: https://w3id.org/fair-bioheaders/profiles/fht-insdc-mapping
name: FHTInsDCMappingProfile
description: >-
  Draft FHT profile: adds controlled vocabularies and CURIE conventions
  for INSDC minimum-specification submission mapping. Community-driven;
  not endorsed by Alliance or AgBioData until reviewed.
prefixes: { linkml: https://w3id.org/linkml/, fhr: https://w3id.org/fair-bioheaders/terms# }
default_prefix: fhr
default_range: string
imports:
- linkml:types
slots:
  libraryStrategy:
    # Controlled vocabulary aligned with ENA LIBRARY_STRATEGY terms
    range: str
    required: false
    enum_class: LibraryStrategyEnum  # defined in profile, not base
  strandedness:
    # ENA-aligned controlled values
    range: str
    required: false
    enum_class: StrandednessEnum  # unstranded | firststrand | secondstrand
  sampleIdentifier:
    pattern: ^[a-z][a-z0-9]*:[A-Za-z0-9._-]+$
    description: Community or INSDC sample accession (biosample:SAMN…) for FHT deposits
classes:
  FHTInsDCMapping:
    is_a: Transcriptome  # inherits draft FHT class
    slot_usage:
      moleculeType:
        required: true  # base optional → required by this profile
      libraryStrategy:
        required: false  # keep optional per FR-003
```

**This profile is illustrative.** The actual terms, enums, and constraints would be determined through issue #6 curator consultation and subsequent review per the profiles registry process (#51).

---

## Resolution of INSDC minimum-specification gates for #6

| Gate | Status | Notes |
|---|---|---|
| FR-002 `assemblyType` enum (de novo / genome-guided / annotation-derived) | ✅ Maps to A.i, S13 context; no INSDC contradiction. Document as metadata hint, not enforcement. |
| FR-002 `moleculeType` enum (pending review per #6) | ⏳ Pending curator review (see Finding 5 above). Not a blocker — value set aligns with transcriptome deposit requirements. |
| FR-003 optional fields (`sample`, `libraryStrategy`, `strandedness`) | ✅ Documented mappings. Controlled vocabularies proposed for `strandedness` and `libraryStrategy` in spec 005 follow-up (curator input needed). |
| No project/study/sample dedicated fields in base contract | ✅ Correctly handled by profile mechanism (#51/#156) and CURIE conventions via `relatedLink`. Not a gap — different design. |
| No geographic location or collection date in any FH type | ✅ Correctly external to file-bound header per ticket guidance (BioSample/MIxS layer). Documented in submission notes. |
| `dateCreated` ≠ collectionDate distinction | ✅ Explicitly documented; MAPPINGS.md already warns this. Submission notes clarify the difference. |

**Conclusion: No base-schema changes are required by this mapping.** The draft FHT field set, when mapped using the conventions and profiles described above, covers all applicable INSDC minimums where they intersect with file-bound transcriptome metadata. Gaps (geo, collection date, per-record seq properties) belong in external submission layers or future design — not in the base contract at this time.

---

## Links

- Issue #6 (FHT field-set consultation): https://github.com/FAIR-bioHeaders/FHT-Specification/issues/6
- INSDC coverage matrix: [specs/insdc-fht-coverage.md](./insdc-fht-coverage.md) (this PR's companion doc)
- Draft spec 005: `specs/005-rna-transcriptome-header/spec.md` (shared repo)
- AgBioData FHR profile model: `profiles/agbiodata-fhr.yaml` (shared repo) — reference for FHT INSDC profile pattern
- Profile registry: `profiles/registry.yaml` (shared repo) — mechanism for draft community profiles
