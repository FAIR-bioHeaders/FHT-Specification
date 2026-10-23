# INSDC minimum-specification coverage review — FHT draft fields (matrix v1)

**Pinned versions reviewed:**
- **INSDC side:** insdc/minimum-specifcations at commit `41f0dc4` (2026-07-06), all categories v1.0. Retrieved 2026-10-23.
- **FHT side:** FHT-Specification main @ `92f652d` (AGENTS.md commit); draft spec 005-rna-transcriptome-header/spec.md; legacy fht.json schema.

**Coverage key:** ✅ covered · ◐ partially covered · ✗ not covered · — not applicable to a file-bound header

## Table 1 — INSDC categories relevant to FHT transcriptome FASTA

| INSDC spec (all v1.0) | FH context | Relevance | Summary |
|---|---|---|---|
| [Sequence](https://github.com/insdc/minimum-specifcations/tree/41f0dc4/Sequence) | FHT (draft transcriptome FASTA header) | **Direct** | Per-record sequence metadata, molecule type, topology; file-level metadata aligns with the `;~` block |
| [Assembly](https://github.com/insdc/minimum-specifcations/tree/41f0dc4/Assembly) | FHT (de novo / genome-guided transcriptome assemblies) | **Direct** | Assembly method/version, technology, submitter identity, taxID — all map to FHR-style required fields that FHT inherits |
| [Annotations](https://github.com/insdc/minimum-specifcations/tree/41f0dc4/Annotations) | FHT ✗ (transcriptome FASTA has no features; annotation belongs to the GFF3 side) | — | Not applicable to a transcriptome header file. The derived-from FHRGFF3 annotation is handled by FHGFF3's `genomeReference` slot |
| [Analysis](https://github.com/insdc/minimum-specifcations/tree/41f0dc4/Analysis) | FHT (`assemblyType`, `libraryStrategy`, platform → `instrument`) | **Partial** | Title/description/map to `transcriptome`+`documentation`; technology keywords align with `moleculeType`+`libraryStrategy`; STUDY_REF has no FH field |
| [Sample](https://github.com/insdc/minimum-specifcations/tree/41f0dc4/Sample) | FHT draft FR-003 `sample` (tissue/UBERON, stage, condition, strain) | **Partial** | No released type has a sample object yet; the draft AgBioData profile adds a community-only `sampleIdentifier` slot. FHT's optional `sample` struct fills part of this gap |
| [Project](https://github.com/insdc/minimum-specifcations/tree/41f0dc4/Project) | FHT ✗ (no project field in any released type) | — | BioProject links possible via `identifier` CURIE (`bioproject:PRJ…`) or `relatedLink`, by convention only. A dedicated `project` field would be a **schema addition** |
| [Package-Checklist](https://github.com/insdc/minimum-specifcations/tree/41f0dc4/Package-Checklist) | FHT (`schema`+`schemaVersion` + draft profiles machinery) | **Conceptual analogue** | FHT's own optional fields (libraryStrategy, strandedness, etc.) would be expressed through community profiles (#51/#156), never by editing the base contract |
| [Experiment](https://github.com/insdc/minimum-specifcations/tree/41f0dc4/Experiment) | FHT draft FR-003 (`libraryStrategy`, `strandedness`, `sequencingRuns`) | **Partial** | No experiment object exists in the family. The FHT optional fields serve as a *file-level proxy* for Experiment metadata, not an Experiment replacement |
| [Raw Reads](https://github.com/insdc/minimum-specifcations/tree/41f0dc4/Raw%20Reads) | FHT ✗ (FASTQ/BAM/CRAM header type not proposed) | N/A | No action |
| [Compressed Reads](https://github.com/insdc/minimum-specifcations/tree/41f0dc4/Compressed%20Reads) | FHT ✗ | N/A | Not applicable |

## Table 2 — Sequence Minimum Standards v1.0 mapped to FHT draft fields

| # | INSDC requirement | Cov. | Location in FHT | Disposition |
|---|---|---|---|---|
| **S1** | IUPAC nucleotide characters only, no dashes; **T instead of U regardless of molecule type** | ✗ | specs/005 FR-006 deliberately **allows U in RNA FASTA**. The FHT spec explicitly says "RNA FASTA may use U for uracil; header parsing and checksums are alphabet-independent." This is a deliberate divergence from INSDC (which mandates T for all transcriptome sequences). | **Document** the T-vs-U divergence in spec 005. No schema action — the schema has no molecule-type field that constrains alphabet. If curators require this, a separate alphabet-constraint would be a **schema addition**, not now. |
| **S2** | DNA 5'→3' directionality | — | sequence-content rule; headers carry no directional metadata | N/A for a file-bound header; per-record defline metadata is future work (see S12) |
| **S3/S4** | Minimum sizes (100 nt; 1000 nt WGS top-level contigs) | — | FHT draft `vitalStats` reports transcript count, N50, mean length but enforces no minimums | Document boundary: INSDC sets deposit-level thresholds; FH headers report statistics without gatekeeping. A profile could add `minTranscriptLength` if curators require it |
| **S5** | ≤50% Ns in contigs/scaffolds | — | sequence-content rule | N/A for a file-bound header |
| **S6/S7** | Gap spans all-N; no leading/trailing Ns unless telomere/centromere/circular/contamination gap | — | sequence-content rule | N/A for a file-bound header |
| **S8** | Sequence directly determined or contracted by submitter | ◐ | `metadataAuthor` (required) + `assemblyAuthor` (required) record identity; `sourceType`-style assertion is not in FHT draft. FHP uses `sourceType` (predicted/database/mixed) — FHT could benefit from the same | **Proposal:** borrow FHP's `sourceType` as an optional field for FHT to indicate whether transcripts are experimentally determined vs. in silico predicted |
| **S9** | Joined sequences in biological order with appropriate gaps | — | sequence-content rule; the file header cannot express per-record ordering | N/A for a file-bound header |
| **S10** | ≤50% Ns (dup); contamination screening to taxonomic order; proposal for screening checksum report included in submission | ◐ | `assemblySoftware` (structured) can name screening tools (`fastp`, `bbduk`, etc.); `assemblyProtocol` can describe the screening workflow. No structured screening-result evidence field yet. The INSDC proposal for "checksum-verified screening reports" aligns with FH's exact-byte-checksum philosophy | **Document** the alignment. A future schema addition for a `screeningResults` struct is only needed if curators require it; not now |
| **S11** | Semantic/syntactic FASTA validation; "full spec will need to be developed" | ✅ | FH provides exactly what INSDC says is missing: exact header syntax (FORMAT.md R1–R11), versioned JSON Schema contracts, conformance vectors, `bioheaders verify`, and `assess sniff/conventions`. INSDC's Sequence v1.0 **already cites the 2024 FHR paper** (engagement opportunity) | No FH gap. This is an **engagement opportunity**: the unified-FASTA per-record defline that INSDC proposes would need a companion FH type or extension, but it is not part of #6's scope |
| **S12** | Per-record sequence-specific metadata: molecule type, topology, chromosome number/location, viral segment, plasmid name; topology+completeness in deflines | ✗ | **No per-record mechanism exists in any FH header type.** Headers are file-bound (`;~`/`#~`), not per-sequence. The INSDC unified-FASTA proposal carries per-record JSON deflines — a different layer from FH's design | Document boundary. Per-record FASTA modifiers are future work only if INSDC's unified format materializes and curators request FH support. Not in #6 scope |
| **S13** | Technique keywords (HTGS/STS/GSS/WGS/TSA) validated against molecule type ("TSA should not be DNA") | ◐ | FHT draft FR-002: `assemblyType` (de novo / genome-guided / annotation-derived) + `moleculeType` (mRNA / total RNA / cDNA / ncRNA) **are the file-level analogue** of INSDC's technique keywords. The molecule type constraint is built into the enum; cross-type validation (e.g., "TSA ≠ DNA") would need a profile | Document as design choice: FH uses typed enums rather than free-text keywords. `moleculeType`'s T-vs-U question is noted in S1 row above |
| **S14** | Sequence name <51 chars, INSDC-legal characters, must not match another record's accession pattern | — | per-record naming; the file header carries no per-record name constraints. Adjacent: `assess related` compares names across files | N/A for a file-bound header |
| **S15** | Chromosome/linkage-group, plasmid and organelle naming rules | — | per-record naming | N/A for a file-bound header |
| **S-xref** | Cross-references: logical links out (publication) and within categories (reads, assembly, annotations, study, sample, validation reports) | ◐ | `scholarlyArticle` (DOI), `identifier` (CURIE prefix:accession), `relatedLink`, `accessionID`, `derivedFrom` (FHT opts in per FR-003). Study/sample links only by CURIE convention (unimplemented yet) | Document convention (`bioproject:PRJ…`, `biosample:SAMN…`). A dedicated `project` or `sample` field would be a **schema addition** — document as future work |
| **S-ver** | Accessioning/versioning: `accession.version`; version increments on sequence change; **not** on metadata-only change | ◐ | FH uses free-text required `version` + required exact-byte SHA-512/256 `checksum`. An FH metadata edit bumps the checksum (and arguably warrants a version bump) — INSDC's "metadata-only = no version bump" is a different layer convention. Document divergence | **Document** in spec 005; not a gap to close (different layers, different identity model). A submission-mapping note should clarify this for curators |

## Table 3 — Assembly Minimum Specification v1.0 mapped to FHT draft fields

| # | INSDC requirement | Cov. | Location in FHT | Disposition |
|---|---|---|---|---|
| **A.a** | Link to a public BioProject | ◐ | No dedicated `project` field yet. `identifier` CURIE (`bioproject:PRJ…`) or `relatedLink` can carry it, by convention | Document the convention; a dedicated `project` slot would be a schema addition — only if curators ask for it explicitly |
| **A.b** | Link to a public BioSample | ◐ | FHT draft FR-003 optional `sample` struct (tissue/UBERON, stage, condition, strain). The AgBioData community profile (#51/#156) adds `sampleIdentifier`. No released type has a sample field yet | Document; the profile route is the correct mechanism — never edit the base contract for community-specific requirements |
| **A.c** | Submitter/owner/consortium/center identity | ✅ | `metadataAuthor` (required name + ORCID uri + nameType Personal/Organizational), `assemblyAuthor` (required). Fully covered | No action needed |
| **A.d** | BioSample associated with a taxID at species rank or below; binomial, not environmental, for clone/isolate assemblies | ◐ | `taxon` required: URI pattern-pinned to `https://identifiers.org/taxonomy:<NCBI taxid>`. **Rank is not schema-checkable** — same limitation as FHR/FHP. Taxonomy resolution is online (assess `--online` territory) | Document the limitation. No schema action — rank checking requires external resolution. Not a blocker for transcriptome use |
| **A.e** | Moltypes appropriate for a genome (genomic DNA/RNA, viral cRNA, …) | ✅ | FHT FR-002 `moleculeType` (mRNA / total RNA / cDNA / ncRNA). Each is appropriate for a transcriptome assembly type. This is **the core value-add** of the FHT molecule type over a generic genome schema | No action — already designed into spec 005 |
| **A.f/A.g** | All linked sequences live; withdrawn sequences withdraw the assembly | — | repository lifecycle policy, outside file-bound header scope. Adjacent: `derivedFrom` checksum + `bioheaders verify` detects stale parents offline | N/A for a file-bound header |
| **A.h** | All sequences from the same BioSample and taxID | ◐ | structural: `taxon` is a single required scalar, so a valid FHT file asserts one taxon. No sample field to assert one sample (see A.b) | Document as expected behavior; not a gap — consistent with how all FH types handle taxonomic identity |
| **A.i** | All sequences from the same INSDC provider | — | N/A for a file-bound header | Not applicable |
| **A.j** | Metadata: assembly method and version/dates (e.g., "Canu v. 1.2.3"); sequencing technologies | ✅ | `assemblySoftware` (structured: name required, version/uri/commandLineOption), `assemblyProtocol`, `dateCreated` (required). For FHT specifically, the draft also mentions `instrument` and `sequencingRuns` as optional | No action needed — fully covered by the draft field set |
| **A.k** | Metadata fields ≤1000 characters | ✗ | FH sets no length limits (R11 escaping only). Relevant only when exporting FH values into INSDC submissions | Document in submission-mapping guidance; not a schema change. If curators need enforcement, a profile can add it |
| **A.l** | Unique sequence names; chromosome/plasmid/organelle names declared; per-sequence type and level | ✗ | per-record assembly structure; the NCBI assembly-report/AGP layer. FHT `vitalStats` carries aggregates only (transcriptCount, N50, meanLength) | Document boundary; no header action. The transcriptome header is not an assembly report |
| **A-ver** | Versioning: increment on sequence update/addition/removal/level change; **not** on metadata-only change | ◐ | Same S-ver point above (see Table 2). Different identity model — FH metadata edit recomputes checksum and may warrant a version bump | Document divergence; not a gap to close |

## Table 4 — Experiment Minimum Specification v1.0 mapped to FHT draft fields

| # | INSDC requirement | Cov. | Location in FHT | Disposition |
|---|---|---|---|---|
| **E-lay** | Library strategy (mRNA-Seq, total RNA-Seq, etc.) | ◐ | FHT FR-003 `libraryStrategy` (string, no enum yet). The name overlaps with INSDC Experiment's `LIBRARY_STRATEGY` — but FHT is file-bound, not experiment-bound. **Recommendation:** either constrain to INSDC's controlled vocabulary or document that FHT uses a superset and note which values diverge | Propose an INSDC-aligned enum in spec 005 if curators confirm it; otherwise keep as free string and suggest alignment |
| **E-sou** | Library source (transcriptomic, genomic, cDNA, …) | ◐ | Overlaps with `moleculeType` (FR-002). There is a conceptual overlap between "library source" and "molecule type" — this is one of the ambiguity issues noted in #6 | **Decision:** keep `moleculeType` as FR-002 specifies; deprecate treating `libraryStrategy` as a substitute for library source. If curators request a separate field, it would be a **schema addition** via profile, not now |
| **E-sel** | Library selection (poly-A, random, oligo-dT, …) | ✗ | Not in FHT draft FR-003. Could be added as part of a libraryProfile struct or a community profile | Document as a potential future addition; only if curators request it explicitly |
| **E-str** | Strandedness (unstranded, firststrand, secondstrand) | ◐ | FHT FR-003 `strandedness` (string). Same recommendation as libraryStrategy — propose an INSDC-aligned enum in spec 005 | Propose enum aligned with ENA/INSDC conventions in spec 005 |
| **E-pla** | Platform (ILLUMINA, ION Torrent, …) | ◐ | FHT optional `instrument` carries platform identifiers (legacy fht.json example: "Sequel IIe", "Nanopore"). `sequencingRuns` carries SRA accessions for run-level detail | Accept as-is; a controlled vocabulary would be a schema addition — only if curators request it |
| **E-stu** | STUDY_REF (link to study) | ✗ | No `study` field in any FH type yet. `identifier` CURIE or `relatedLink` can carry it by convention | Document convention; no schema action now |

## Table 5 — Sample Minimum Specification v1.0 mapped to FHT draft fields

| # | INSDC requirement | Cov. | Location in FHT | Disposition |
|---|---|---|---|---|
| **SM-alias** | Sample Alias (unique across submission) | ◐ | FHT FR-003 `sample` struct includes tissue/UBERON, stage, condition, strain fields. No dedicated sampleAlias field | Document; a community profile can add this if curators need it |
| **SM-org** | Organism name (NCBI Taxonomy) | ◐ | FHT inherits `taxon` from the core — required in every type (see A.d). Same rank limitation as all types | No action beyond documentation |
| **SM-geo** | Geographic location | ✗ | Absent from every FH type. Per this ticket's guidance: keep external (BioSample/MIxS layer) | Document as N/A; geographic metadata belongs in the BioSample layer, not a file-bound header |
| **SM-date** | Collection date | ✗ | FHT has `dateCreated` (assembly creation date). The spec already warns this is **not** a sample collection date (see MAPPINGS.md) | Document the distinction explicitly; add a note in the draft decision record that `dateCreated` ≠ collectionDate |
| **SM-cls** | Checklist/Package name validated against a version | ✅ | Required `schema` + `schemaVersion` — same pattern as INSDC's Package-Checklist. FHT's profile machinery (#51/#156) is the direct analogue for community checklists | No action needed |
| **SM-sub** | Submitter name and affiliation | ✅ | `metadataAuthor` (see A.c). Same limitation: affiliation only via Organizational nameType + org URI; no free-text affiliation field. **Acceptable for INSDC submission mapping** (name is sufficient) | No action needed |

## Key findings and recommendations

### 1. Core coverage is strong — the draft field set already meets the INSDC minimums where it matters
The FHT draft FR-002/FR-003 field set (`assemblyType`, `moleculeType` + optional `assemblySoftware`, `sample`, `libraryStrategy`, `strandedness`, `sequencingRuns`, `vitalStats`, `completeness`, `derivedFrom`) covers the INSDC Assembly requirements (A.a through A.j) at **or above** the level that FHR achieves. The key differentiator is `moleculeType` — which no other FH type has — and this is exactly what transcriptome curators asked for in #6.

### 2. T-vs-U divergence from INSDC (S1) needs explicit documentation
INSDC Sequence v1.0 mandates T for all sequences regardless of molecule type. The FHT draft FR-006 explicitly allows U in RNA FASTA ("alphabet-independent"). This is a **deliberate design divergence**, not a gap. The rationale:
- Many transcriptome datasets use `u` in the actual sequence file (e.g., from direct cDNA-to-RNA mapping)
- Header parsing and checksums are already alphabet-independent (FR-006)
- The `moleculeType` field already signals whether the file contains RNA-derived transcripts

**Recommendation:** Document this divergence in spec 005 with the rationale, not as a gap to close. If curators require T-only enforcement, that would be a **schema addition** (new validation rule) via profile, not a change to the base contract.

### 3. Per-record sequence metadata (S12) is outside FHT scope by design
INSDC's proposed unified-FASTA with per-record defline JSON metadata is a different layer from FH's file-bound header design. This is an **engagement opportunity** (noted in #157's review: INSDC Sequence v1.0 already cites the 2024 FHR paper). If future INSDC adoption materializes, a companion per-record mechanism would be needed — but this is not part of the current consultation (#6) scope.

### 4. Study/project links need convention documentation
No FH type has a dedicated `project` or `study` field. The convention is to use `identifier` CURIE (`bioproject:PRJ…`, `studynum:SRS…`) or `relatedLink`. For INSDC submission, this means submitters must know the CURIE format — which most do (it's part of standard practice), but it should be documented in a submission-mapping note for FHT.

### 5. No schema changes required at this time
The draft field set **covers** the applicable INSDC minimum specifications. The gaps identified are:
- Items that are outside file-bound header scope (per-record metadata, geographic location, collection date) — correctly classified as N/A
- Items that can be addressed via community profiles (#51/#156) rather than base contract edits
- A deliberate T-vs-U design choice (documented, not changed)

**Action items for spec 005:**
- Document the T-vs-U divergence from INSDC S1 with rationale
- Add a "Submission Mapping to INSDC" note section covering: versioning convention difference, project/study link conventions, metadata field length limits
- Clarify `dateCreated` ≠ collectionDate distinction
- Propose controlled vocabulary enums for `strandedness` (aligned with ENA: `unstranded`, `firststrand`, `secondstrand`) — these are small schema additions that benefit from curator input
- Consider adding FHP's `sourceType` as optional to FHT (see S8)

### 6. No new fields proposed for the base contract at this time
Adding `project`, `study`, or geography would be **schema additions** that require their own proposal cycle. They are covered by the community profile machinery (#51/#156), which is the correct mechanism for transcriptome-specific requirements from Alliance/AgBioData curators.
