"""Contract checks for the generated FHT JSON Schema."""

import copy
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "fht.json"
CHECKSUM = "A" * 43 + "="


def minimal():
    """A field-level minimal record; not a byte-backed #8 fixture."""
    return {
        "schema": (
            "https://raw.githubusercontent.com/FAIR-bioHeaders/"
            "FHT-Specification/main/fht.json"
        ),
        "schemaVersion": "1.0",
        "transcriptome": "Example transcriptome",
        "assemblyType": "de novo",
        "taxon": {
            "name": "Arabidopsis thaliana",
            "uri": "https://identifiers.org/taxonomy:3702",
        },
        "version": "1.0",
        "metadataAuthor": [{"name": "Example author"}],
        "dateCreated": "2026-10-24",
        "checksum": CHECKSUM,
    }


class FhtSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        cls.validator = Draft202012Validator(
            cls.schema, format_checker=FormatChecker()
        )

    def record(self, **changes):
        value = minimal()
        value.update(changes)
        return value

    def assert_valid(self, value):
        errors = sorted(self.validator.iter_errors(value), key=str)
        self.assertEqual(errors, [], [error.message for error in errors])

    def assert_invalid(self, value, fragment):
        errors = sorted(self.validator.iter_errors(value), key=str)
        self.assertTrue(errors, f"expected a validation error containing {fragment!r}")
        self.assertTrue(
            any(fragment in error.message for error in errors),
            [error.message for error in errors],
        )

    def test_schema_is_a_valid_draft_2020_12_schema(self):
        Draft202012Validator.check_schema(self.schema)
        self.assertEqual(
            self.schema["$schema"], "https://json-schema.org/draft/2020-12/schema"
        )
        self.assertFalse(self.schema["additionalProperties"])

    def test_required_fields(self):
        self.assertEqual(
            set(self.schema["required"]),
            {
                "schema",
                "schemaVersion",
                "transcriptome",
                "assemblyType",
                "taxon",
                "version",
                "metadataAuthor",
                "dateCreated",
                "checksum",
            },
        )

    def test_minimal_record_is_valid(self):
        self.assert_valid(minimal())

    def test_each_required_field_is_enforced(self):
        for name in self.schema["required"]:
            value = minimal()
            del value[name]
            self.assert_invalid(value, "'" + name + "' is a required property")

    def test_unknown_key_is_rejected(self):
        # With extension fields (R15) jsonschema names the key and the x- pattern.
        self.assert_invalid(
            self.record(masking="soft-masked"), "'masking' does not match any of the regexes"
        )

    def test_extension_fields(self):
        """FAIR-bioHeaders-Specification docs/FORMAT.md R15: top-level x- keys only."""
        self.assertEqual(
            list(self.schema["patternProperties"]), ["^x-[A-Za-z0-9][A-Za-z0-9_.-]*$"]
        )
        for key in ("x-a", "x-1", "x-example-studyNote", "x-a.b-c_d", "x-transcriptome"):
            for value in ("text", 2, 0.5, True, None, [1, "a"], {"@id": "x", "n": [None]}):
                with self.subTest(key=key, value=value):
                    self.assert_valid(self.record(**{key: value}))
        for key in ("X-a", "x-", "x-_a", "x- a", "x-a b", "x-\u00e4", "x-\uff41", "x-a\r",
                    "x-a\u2028", "xa", "x_a", "ext-a"):
            with self.subTest(key=key):
                self.assert_invalid(self.record(**{key: 1}), "does not match any of the regexes")
        # Python's "$" matches before a final line feed; the key is still invalid.
        self.assert_invalid(self.record(**{"x-a\n": 1}), "should not be valid under")
        nested = self.record()
        nested["taxon"] = dict(nested["taxon"], **{"x-a": 1})
        self.assert_invalid(nested, "Additional properties")
        author = self.record()
        author["metadataAuthor"] = [{"name": "Example author", "x-a": 1}]
        self.assert_invalid(author, "Additional properties")

    def test_schema_url_and_version(self):
        self.assert_valid(self.record(schema="https://w3id.org/fair-bioheaders/fht/v0.4.0"))
        self.assert_invalid(self.record(schema="https://example.org/fht.json"), "does not match")
        self.assert_invalid(self.record(schemaVersion=1.0), "is not of type 'string'")
        self.assert_invalid(self.record(schemaVersion="1.1"), "is not one of ['1.0']")

    def test_assembly_type_values(self):
        # Curator review Q1: exactly three controlled values, no fourth value
        # for mixed or unknown histories (the record stays incomplete).
        self.assertEqual(
            self.schema["$defs"]["AssemblyType"]["enum"],
            ["de novo", "genome-guided", "annotation-derived"],
        )
        for value in ("de novo", "genome-guided", "annotation-derived"):
            self.assert_valid(self.record(assemblyType=value))
        for value in ("mixed", "unknown", "hybrid", "other", "composite"):
            with self.subTest(assemblyType=value):
                self.assert_invalid(self.record(assemblyType=value), "is not one of")

    def test_assembly_type_is_matched_exactly(self):
        # Case, spacing and punctuation variants are not normalized.
        for value in ("De novo", "de-novo", "denovo", "de_novo", "de  novo",
                      " de novo", "de novo ", "Genome-guided", "genome guided",
                      "genome_guided", "annotation derived", "Annotation-derived",
                      "reference-guided", ""):
            with self.subTest(assemblyType=value):
                self.assert_invalid(self.record(assemblyType=value), "is not one of")
        self.assert_invalid(self.record(assemblyType=None), "is not of type 'string'")
        self.assert_invalid(
            self.record(assemblyType=["de novo", "genome-guided"]),
            "is not of type 'string'",
        )

    def test_molecule_type_is_optional_and_restricted(self):
        # Curator review Q2: five values, mixed added.
        self.assertEqual(
            self.schema["$defs"]["MoleculeType"]["enum"],
            ["mRNA", "rRNA", "tRNA", "transcribed RNA", "mixed"],
        )
        self.assert_valid(minimal())
        for value in ("mRNA", "rRNA", "tRNA", "transcribed RNA", "mixed"):
            self.assert_valid(self.record(moleculeType=value))
        for value in ("total RNA", "cDNA", "ncRNA", "unknown", "lncRNA"):
            self.assert_invalid(self.record(moleculeType=value), "is not one of")

    def test_mixed_molecule_type_is_matched_exactly(self):
        # mixed is one value, not a list of classes or a free-text variant.
        for value in ("Mixed", "MIXED", "mixed RNA", "mixed ", "heterogeneous",
                      "mixture", ""):
            with self.subTest(moleculeType=value):
                self.assert_invalid(self.record(moleculeType=value), "is not one of")
        self.assert_invalid(
            self.record(moleculeType=["mRNA", "rRNA"]), "is not of type 'string'"
        )

    def test_strandedness_is_optional_and_normalized(self):
        # Curator review Q3: the forward/reverse convention is kept.
        for value in ("unstranded", "forward", "reverse"):
            self.assert_valid(self.record(strandedness=value))
        self.assert_invalid(self.record(strandedness="firststrand"), "is not one of")
        self.assert_invalid(self.record(strandedness="secondstrand"), "is not one of")
        for value in ("RF", "FR", "fr-firststrand", "dUTP", "mixed", "unknown"):
            with self.subTest(strandedness=value):
                self.assert_invalid(self.record(strandedness=value), "is not one of")

    def test_library_protocol_records_a_named_protocol_or_kit(self):
        # Curator review Q3: protocol or kit name, optional URI (the FHR
        # assemblyProtocol URI rules), one object for the whole set.
        kit = {"name": "Illumina TruSeq Stranded mRNA"}
        self.assert_valid(self.record(libraryProtocol=kit))
        self.assert_valid(
            self.record(
                libraryProtocol=dict(kit, uri="https://example.org/protocols/1"),
                strandedness="reverse",
            )
        )
        self.assert_valid(
            self.record(libraryProtocol={"name": "In-house dUTP protocol v3"})
        )
        self.assert_invalid(self.record(libraryProtocol={}), "'name' is a required property")
        self.assert_invalid(
            self.record(libraryProtocol={"uri": "https://example.org/protocols/1"}),
            "'name' is a required property",
        )
        for name in ("", "   "):
            with self.subTest(name=name):
                self.assert_invalid(
                    self.record(libraryProtocol={"name": name}), "does not match"
                )
        self.assert_invalid(
            self.record(libraryProtocol={"name": "Kit", "uri": "not a uri"}),
            "is not a 'uri'",
        )
        self.assert_invalid(
            self.record(libraryProtocol="Illumina TruSeq Stranded mRNA"),
            "is not of type 'object'",
        )
        self.assert_invalid(
            self.record(libraryProtocol=[kit]), "is not of type 'object'"
        )
        self.assert_invalid(
            self.record(libraryProtocol=dict(kit, version="2")),
            "Additional properties",
        )
        self.assert_invalid(
            self.record(libraryProtocol=dict(kit, **{"x-a": 1})),
            "Additional properties",
        )

    def test_sample_is_an_ordered_non_empty_array(self):
        sample = {"tissue": "ovary", "tissueIdentifier": "UBERON:0000992"}
        self.assert_valid(self.record(sample=[sample]))
        self.assert_valid(
            self.record(
                sample=[
                    {"tissue": "ovary", "condition": "control"},
                    {"tissue": "fat body", "condition": "treated"},
                ]
            )
        )
        self.assert_invalid(self.record(sample=[]), "should be non-empty")
        self.assert_invalid(self.record(sample=sample), "is not of type 'array'")
        self.assert_invalid(
            self.record(sample=[{"tissueIdentifier": "not-a-curie"}]),
            "does not match",
        )
        self.assert_invalid(
            self.record(sample=[{"sampleName": "invented"}]),
            "Additional properties",
        )

    def test_empty_strings_and_empty_sample_objects_are_rejected(self):
        self.assert_invalid(self.record(transcriptome=""), "does not match")
        self.assert_invalid(self.record(transcriptome="   "), "does not match")
        self.assert_invalid(
            self.record(transcriptomeSynonym=[""]), "does not match"
        )
        self.assert_invalid(self.record(libraryStrategy=""), "does not match")
        self.assert_invalid(self.record(libraryStrategy="   "), "does not match")
        self.assert_invalid(self.record(instrument=[""]), "does not match")
        for key in (
            "tissue",
            "developmentalStage",
            "condition",
            "strain",
        ):
            self.assert_invalid(
                self.record(sample=[{key: ""}]), "does not match"
            )
        self.assert_invalid(
            self.record(sample=[{}]), "is not valid under any of the given schemas"
        )

    def test_required_values_are_non_empty(self):
        # Curator review Q4 and FHR's planned GAP-1 rule: a required key must
        # carry a value, not an empty string, list or object.
        for node in (self.schema, self.schema["$defs"]["FHT"]):
            for name in ("transcriptome", "version", "dateCreated"):
                self.assertEqual(node["properties"][name]["minLength"], 1)
                self.assertEqual(node["properties"][name]["pattern"], "\\S")
            self.assertEqual(node["properties"]["metadataAuthor"]["minItems"], 1)
        for name in ("transcriptome", "version", "dateCreated"):
            self.assert_invalid(self.record(**{name: ""}), "should be non-empty")
            for value in (" ", "\t", "\n"):
                with self.subTest(field=name, value=value):
                    self.assert_invalid(self.record(**{name: value}), "does not match")
        # Without format assertion, a blank date is still rejected by pattern.
        plain = Draft202012Validator(self.schema)
        self.assertTrue(list(plain.iter_errors(self.record(dateCreated=" "))))
        self.assert_invalid(self.record(version=""), "should be non-empty")
        self.assert_invalid(self.record(dateCreated=""), "should be non-empty")
        self.assert_invalid(self.record(metadataAuthor=[]), "should be non-empty")
        self.assert_invalid(
            self.record(metadataAuthor=[{}]), "'name' is a required property"
        )
        self.assert_invalid(
            self.record(metadataAuthor=[{"nameType": "Personal"}]),
            "'name' is a required property",
        )
        for name in ("", "  "):
            with self.subTest(author_name=name):
                self.assert_invalid(
                    self.record(metadataAuthor=[{"name": name}]), "does not match"
                )
        self.assert_invalid(
            self.record(
                metadataAuthor=[{"name": "Example author"}, {"name": ""}]
            ),
            "should be non-empty",
        )
        self.assert_invalid(self.record(taxon={"uri": ""}), "does not match")
        for value in (None, [], ""):
            for name in ("transcriptome", "version", "metadataAuthor", "taxon",
                         "dateCreated", "assemblyType", "schemaVersion"):
                with self.subTest(field=name, value=value):
                    self.assert_invalid(self.record(**{name: value}), "")
        for value in (None, [], "", {}):
            for name in ("transcriptome", "version", "metadataAuthor",
                         "dateCreated", "assemblyType", "schemaVersion"):
                with self.subTest(field=name, value=value):
                    self.assert_invalid(self.record(**{name: value}), "")

    def test_taxon_rules_are_unchanged(self):
        # Maintainer decision (FHT-Specification#8, 2026-11-16): keep the
        # current taxon rules. name and uri stay optional members, and no
        # taxonomy identifier is required (FAIR-bioHeaders-Specification#189
        # applies to the next FHR, FHP and FHGFF3 majors only).
        self.assertNotIn("required", self.schema["$defs"]["Taxon"])
        self.assert_valid(self.record(taxon={"name": "Arabidopsis thaliana"}))
        self.assert_valid(
            self.record(taxon={"uri": "https://identifiers.org/taxonomy:3702"})
        )
        self.assert_valid(self.record(taxon={}))

    def test_author_names_are_required_in_assembly_author_too(self):
        # The shared Author object carries the rule, so assemblyAuthor items
        # (optional field) cannot be empty either, as FHR plans.
        self.assert_invalid(self.record(assemblyAuthor=[{}]), "'name' is a required property")
        self.assert_invalid(self.record(assemblyAuthor=[]), "should be non-empty")
        self.assert_valid(self.record(assemblyAuthor=[{"name": "Example assembler"}]))

    def test_sample_record_links_follow_fhr(self):
        # Curator review Q7: as in FHR, a BioSample record is a relatedLink URL
        # and the physical specimen is voucherSpecimen; sample keeps only the
        # FHT-specific biological context and carries no accession member.
        self.assert_valid(
            self.record(
                sample=[{"tissue": "brain", "tissueIdentifier": "UBERON:0000955"}],
                relatedLink=["https://www.ncbi.nlm.nih.gov/biosample/SAMN02803731"],
                voucherSpecimen="Example specimen in an example collection",
            )
        )
        for key in ("biosample", "sampleAccession", "sampleIdentifier", "accession"):
            with self.subTest(member=key):
                self.assert_invalid(
                    self.record(sample=[{"tissue": "brain", key: "SAMN02803731"}]),
                    "Additional properties",
                )

    def test_genome_guided_written_out_from_the_genome_links_its_parent(self):
        # Curator review Q8: a genome-guided set whose final sequences were
        # extracted from the genome links it as an FHR transcribedFrom parent.
        parent = {
            "headerType": "FHR",
            "relationship": "transcribedFrom",
            "checksum": CHECKSUM,
        }
        self.assert_valid(
            self.record(assemblyType="genome-guided", derivedFrom=[parent])
        )
        self.assert_valid(self.record(assemblyType="genome-guided"))
        self.assert_invalid(
            self.record(
                assemblyType="genome-guided",
                derivedFrom=[dict(parent, relationship="assembledFrom")],
            ),
            "is not valid under any of the given schemas",
        )
        no_checksum = dict(parent)
        del no_checksum["checksum"]
        self.assert_invalid(
            self.record(assemblyType="genome-guided", derivedFrom=[no_checksum]),
            "'checksum' is a required property",
        )

    def test_sequencing_runs_are_run_accessions(self):
        self.assert_valid(self.record(sequencingRuns=["SRR123456", "ERR7", "DRR1"]))
        self.assert_invalid(self.record(sequencingRuns=[]), "should be non-empty")
        self.assert_invalid(
            self.record(sequencingRuns=["SRS123456"]), "does not match"
        )

    def test_vital_stats_constraints(self):
        self.assert_valid(
            self.record(
                vitalStats={
                    "totalTranscripts": 0,
                    "N50": 1,
                    "averageTranscriptLength": 0,
                }
            )
        )
        self.assert_invalid(
            self.record(vitalStats={"totalTranscripts": -1}), "less than the minimum"
        )
        self.assert_invalid(
            self.record(vitalStats={"N50": 0}), "less than the minimum"
        )
        self.assert_invalid(
            self.record(vitalStats={"averageTranscriptLength": -0.1}),
            "less than the minimum",
        )
        self.assert_invalid(
            self.record(vitalStats={"geneCount": 10}), "Additional properties"
        )

    def test_derived_from_reviewed_parent_pairs(self):
        fht_parent = {
            "headerType": "FHT",
            "relationship": "filteredFrom",
            "checksum": CHECKSUM,
        }
        fhr_parent = {
            "headerType": "FHR",
            "relationship": "transcribedFrom",
            "checksum": CHECKSUM,
        }
        self.assert_valid(self.record(derivedFrom=[fht_parent]))
        self.assert_valid(self.record(derivedFrom=[fhr_parent]))
        self.assert_invalid(
            self.record(
                derivedFrom=[
                    {
                        "headerType": "FHR",
                        "relationship": "assembledFrom",
                        "checksum": CHECKSUM,
                    }
                ]
            ),
            "is not valid under any of the given schemas",
        )
        self.assert_invalid(
            self.record(
                derivedFrom=[
                    {
                        "headerType": "FHP",
                        "relationship": "filteredFrom",
                        "checksum": CHECKSUM,
                    }
                ]
            ),
            "is not valid under any of the given schemas",
        )
        self.assert_invalid(
            self.record(
                derivedFrom=[
                    {"headerType": "FHT", "relationship": "filteredFrom"}
                ]
            ),
            "'checksum' is a required property",
        )
        self.assert_invalid(self.record(derivedFrom=[]), "should be non-empty")

    def test_rich_record_combines_optional_groups(self):
        value = self.record(
            moleculeType="mRNA",
            assemblySoftware=[
                {
                    "name": "gffread",
                    "version": "0.12.7",
                    "commandLineOption": ["-w"],
                }
            ],
            sample=[{"tissue": "ovary", "tissueIdentifier": "UBERON:0000992"}],
            libraryStrategy="RNA-Seq",
            strandedness="forward",
            libraryProtocol={
                "name": "Example stranded kit",
                "uri": "https://example.org/kit",
            },
            sequencingRuns=["SRR123456"],
            instrument=["Example sequencer"],
            vitalStats={
                "totalTranscripts": 10,
                "N50": 500,
                "averageTranscriptLength": 300.5,
            },
            completeness={
                "lineageDataset": "insecta_odb10",
                "buscoVersion": "6.1.0",
                "mode": "transcriptome",
                "completeSingle": 100,
                "completeDuplicated": 2,
                "fragmented": 3,
                "missing": 4,
                "total": 109,
            },
            derivedFrom=[
                {
                    "headerType": "FHR",
                    "relationship": "transcribedFrom",
                    "checksum": CHECKSUM,
                }
            ],
            identifier=["example:1"],
            accessionID={"name": "Example", "url": "https://example.org/x"},
            scholarlyArticle="10.1234/abc",
            documentation="https://example.org/doc",
            relatedLink=["https://example.org"],
            funding="Example grant",
            reuseConditions="CC0",
            voucherSpecimen="Example freezer",
        )
        self.assert_valid(value)

    def test_legacy_compatible_fields_are_retained(self):
        self.assert_valid(
            self.record(
                transcriptomeSynonym=["Example synonym"],
                assemblyAuthor=[{"name": "Example assembler"}],
                instrument=["Example sequencer"],
            )
        )

    def test_existing_pilot_record_stays_valid(self):
        # Backward compatibility: the real-data pilot header (#45), written
        # before the curator-review changes, still validates unchanged.
        import yaml

        record = yaml.safe_load(
            (ROOT / "pilot" / "dmel-chr4" / "metadata.fht.yaml").read_text(
                encoding="utf-8"
            )
        )
        record["checksum"] = CHECKSUM
        self.assert_valid(record)

    def test_legacy_md5_checksum_is_not_accepted(self):
        self.assert_invalid(
            self.record(checksum="md5:7582b26fcb0a9775b87c38f836e97c42"),
            "does not match",
        )

    def test_null_is_not_an_unknown_value(self):
        self.assert_invalid(self.record(moleculeType=None), "is not of type 'string'")

    def test_completeness_reuses_shared_counts(self):
        self.assert_valid(
            self.record(
                completeness={
                    "lineageDataset": "insecta_odb10",
                    "buscoVersion": "6.1.0",
                    "mode": "transcriptome",
                    "completeSingle": 100,
                    "completeDuplicated": 2,
                    "fragmented": 3,
                    "missing": 4,
                    "total": 109,
                }
            )
        )
        self.assert_invalid(
            self.record(
                completeness={
                    "lineageDataset": "insecta_odb10",
                    "completeSingle": 0,
                    "completeDuplicated": 0,
                    "fragmented": 0,
                    "missing": 0,
                    "total": 0,
                }
            ),
            "less than the minimum",
        )

    def test_dotted_busco_lineage_follows_the_shared_grammar(self):
        # Shared #170 decided dotted versions at v0.6.0: the pinned shared
        # pattern now accepts one or more dot-separated numeric components.
        # Malformed dot forms stay rejected, and a measured lineage is never
        # renamed or coerced to fit the pattern.
        for dataset in ("insecta_odb12.2", "insecta_odb12.2.1"):
            with self.subTest(lineageDataset=dataset):
                self.assert_valid(
                    self.record(
                        completeness={
                            "lineageDataset": dataset,
                            "completeSingle": 1,
                            "completeDuplicated": 0,
                            "fragmented": 0,
                            "missing": 0,
                            "total": 1,
                        }
                    )
                )
        for dataset in ("insecta_odb12.", "insecta_odb.12", "insecta_odb12..2",
                        "insecta_odb12.2b", "Insecta_odb12.2"):
            with self.subTest(lineageDataset=dataset):
                self.assert_invalid(
                    self.record(
                        completeness={
                            "lineageDataset": dataset,
                            "completeSingle": 1,
                            "completeDuplicated": 0,
                            "fragmented": 0,
                            "missing": 0,
                            "total": 1,
                        }
                    ),
                    "does not match",
                )

    def test_date_created_is_an_iso_date(self):
        self.assert_invalid(self.record(dateCreated="2026-10-24T12:00:00"), "is not a 'date'")

    def test_checksum_is_a_44_character_sha512_256_value(self):
        self.assert_invalid(self.record(checksum="A" * 43), "does not match")
        self.assert_invalid(self.record(checksum="A" * 44), "does not match")


if __name__ == "__main__":
    unittest.main()
