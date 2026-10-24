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
            "name": "Example species",
            "uri": "https://identifiers.org/taxonomy:9606",
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
        self.assert_invalid(self.record(masking="soft-masked"), "Additional properties")

    def test_schema_url_and_version(self):
        self.assert_valid(self.record(schema="https://w3id.org/fair-bioheaders/fht/v0.4.0"))
        self.assert_invalid(self.record(schema="https://example.org/fht.json"), "does not match")
        self.assert_invalid(self.record(schemaVersion=1.0), "is not of type 'string'")
        self.assert_invalid(self.record(schemaVersion="1.1"), "is not one of ['1.0']")

    def test_assembly_type_values(self):
        for value in ("de novo", "genome-guided", "annotation-derived"):
            self.assert_valid(self.record(assemblyType=value))
        self.assert_invalid(self.record(assemblyType="mixed"), "is not one of")
        self.assert_invalid(self.record(assemblyType="unknown"), "is not one of")

    def test_molecule_type_is_optional_and_restricted(self):
        self.assert_valid(minimal())
        for value in ("mRNA", "rRNA", "tRNA", "transcribed RNA"):
            self.assert_valid(self.record(moleculeType=value))
        for value in ("total RNA", "cDNA", "ncRNA"):
            self.assert_invalid(self.record(moleculeType=value), "is not one of")

    def test_strandedness_is_optional_and_normalized(self):
        for value in ("unstranded", "forward", "reverse"):
            self.assert_valid(self.record(strandedness=value))
        self.assert_invalid(self.record(strandedness="firststrand"), "is not one of")
        self.assert_invalid(self.record(strandedness="secondstrand"), "is not one of")

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

    def test_dotted_busco_lineage_is_preserved_not_coerced(self):
        # Shared #170 owns the dotted-version grammar. Until it changes, a dotted
        # lineage is rejected rather than renamed; keep the measured value in
        # documentation instead of "fixing" it.
        self.assert_invalid(
            self.record(
                completeness={
                    "lineageDataset": "insecta_odb12.2",
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
