# FHT-Specification

FHT (FAIR Header Transcriptome) is a FAIR metadata header for reference
transcriptome FASTA files. It records who asserted the metadata, when, for which
taxon, how the transcript set was constructed and how to verify the exact file
bytes. The published paper describes the shared FAIR Header Reference concept:
Wright et al., *Briefings in Bioinformatics* 25, no. 3 (2024): bbae122.

**Status: development contract for review under issue #7.** The LinkML model and
generated JSON Schema implement the design approved for #6. They are not a
published release, not adopted community guidance, and not supported by the
family toolkit yet. No release tag, w3id alias, DOI or toolkit support is
established by this repository state. See
[the contract and migration record](docs/FHT-MIGRATION.md).

- Schema source: [`fht_linkml.yml`](fht_linkml.yml)
- Generated contract: [`fht.json`](fht.json)
- Design and evidence: [`specs/fht-field-decisions.md`](specs/fht-field-decisions.md)
- Minimal and rich designs: [`specs/fht-record-designs.md`](specs/fht-record-designs.md)
- Revised spec 005 proposal: [`specs/005-rna-transcriptome-header/spec.md`](specs/005-rna-transcriptome-header/spec.md)
- Legacy draft schema: [`legacy/fht-v0.1.json`](legacy/fht-v0.1.json)

Conversion, validation and checksum computation belong to the family
[FAIR-bioHeaders-Tools](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Tools);
FHT support there is pending ([issue #9](https://github.com/FAIR-bioHeaders/FHT-Specification/issues/9)).
The former FHT-File-Converter repository is retired.

## Header shape

FHT uses the family `;~` comment block. The checksum below is a placeholder: real
headers must carry a computed SHA-512/256, never a hand-written or invented
value. See `docs/FORMAT.md` in the shared specification for the exact format and
escaping rules.

```text
;~schema: https://raw.githubusercontent.com/FAIR-bioHeaders/FHT-Specification/main/fht.json
;~schemaVersion: "1.0"
;~transcriptome: Bombus impatiens reference transcriptome
;~assemblyType: de novo
;~taxon:
;~  name: Bombus impatiens
;~  uri: https://identifiers.org/taxonomy:132113
;~version: "1.0"
;~metadataAuthor:
;~- name: Example author
;~dateCreated: "2026-10-24"
;~checksum: <computed SHA-512/256>
>transcript_1
ACGTACGT
```

The nine required fields are `schema`, `schemaVersion`, `transcriptome`,
`assemblyType`, `taxon`, `version`, `metadataAuthor`, `dateCreated` and
`checksum`. Optional fields cover biological molecule class, software, sample
context, library strategy/strandedness, run accessions, statistics, BUSCO
completeness, reviewed parent links and shared provenance/identity fields. Omit
unknown optional values; do not use `null`, empty strings or invented
placeholders.

Extension fields: as in FHR 2.1, FHP 1.1 and FHGFF3 1.1 (FAIR-bioHeaders-Specification
`docs/FORMAT.md` rule R15), the draft accepts top-level keys that match
`^x-[A-Za-z0-9][A-Za-z0-9_.-]*$`, for example `x-<project>-<field>`, with any value the
standard does not define. Every other unknown key is still rejected, nested objects stay
closed, and an extension field never replaces a standard field. JSON-LD and HTML forms
leave extension fields out.

### Construction types

| Value | Use case |
| --- | --- |
| `de novo` | Reads reconstructed without a reference genome constructing or grouping the assembly |
| `genome-guided` | Read evidence plus a reference constructed models or grouped reads |
| `annotation-derived` | Sequences extracted from existing annotation coordinates and the matching genome |

A composite or uncertain history is not guessed. The record is incomplete until
the case is reviewed. Genome guidance alone does not justify a `transcribedFrom`
parent link.

## Verify the schema in this repository

```sh
python -m pip install -r requirements-linkml.txt
python -m unittest discover -s tests -v
python json-schema-generator.py
git diff --exit-code fht.json
python scripts/check_provenance.py
```

The tests validate the generated contract, required and optional fields, enum and
numeric constraints, reviewed parent pairs, legacy-compatible fields and exact
generation from the model. `tests/test_examples.py` validates the synthetic
examples in `examples/` (one per construction type, plus JSON and YAML forms of
the de novo header) against `fht.json` and recomputes each FASTA file's
SHA-512/256 checksum under the shared FORMAT.md rules. Their names, statistics
and sequence bytes are invented; taxon and ontology identifiers are real. They
are not the byte-exact positive/rejection conformance vectors, which are owned
by #8. The historical pre-contract examples are preserved verbatim under
`legacy/examples/` as review inputs, not valid FHT 1.0 fixtures.

Continuous-integration lanes and their local commands — documentation
Markdownlint plus local link/whitespace/conflict checks, legacy-draft schema
health with its defect registry and classified examples, and the scheduled
external-link check — are documented in [`docs/CI.md`](docs/CI.md).

## Related FHR citations

These DOI records identify FHR resources; they must not be represented as
FHT-specific release DOIs. For FHT-specific citation metadata, use the resource
actually referenced by your work rather than relabeling an FHR DOI.

Chicago bibliography entries are used below. Cite the published paper for a
general description of FHR; cite the specification or converter when using that
resource directly. The software and specification links are concept DOIs; for a
specific release, use the corresponding version DOI from Zenodo. Authors and
years follow the records resolved by the concept DOIs at the v0.3 documentation
update, and can change as later records are published.

### Published paper

Wright, Adam, Mark D. Wilkinson, Christopher Mungall, Scott Cain, Stephen Richards, Paul Sternberg, Ellen Provin, Jonathan L. Jacobs, Scott Geib, Daniela Raciti, Karen Yook, Lincoln Stein, and David C. Molik. “FAIR Header Reference Genome: A TRUSTworthy Standard.” *Briefings in Bioinformatics* 25, no. 3 (2024): bbae122. <https://doi.org/10.1093/bib/bbae122>.

### Specification

Molik, David. *FHR Specification*. Data set. 2022. <https://doi.org/10.5281/zenodo.6762549>.

### Converter

Molik, David, and Adam Wright. *FHR File Converter*. Computer software. 2024. <https://doi.org/10.5281/zenodo.6762547>.

Machine-readable entries are maintained in
[FHR-Citation](https://github.com/FAIR-bioHeaders/FHR-Citation/blob/main/citation.bib).

## Licensing

[![License: MPL-2.0](https://img.shields.io/badge/License-MPL--2.0-blue.svg)](LICENSE)

New project contributions from March 2025 onward use [MPL-2.0](LICENSE). David Molik left USDA in February 2025. Historical USDA public-domain material remains public domain within the United States; its original notice is preserved in LICENSE. Previously granted permissions and third-party terms remain intact. The project includes both historical material and subsequent MPL-2.0 contributions; file notices and history identify provenance.
