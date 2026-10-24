"""Generate fht.json from the FHT LinkML model.

The model imports the pinned shared core and shared objects under ``schemas/``.
``fht.json`` is generated, never hand-edited. The generator also applies the
FHT-specific parent rule that LinkML cannot express: a derivedFrom item must be
a reviewed FHT/FHR relationship and must identify the parent by checksum or
accession.
"""

import argparse
import json
from pathlib import Path

from linkml.generators.jsonschemagen import JsonSchemaGenerator
from linkml_runtime import SchemaView

ROOT = Path(__file__).resolve().parent
DIALECT = "https://json-schema.org/draft/2020-12/schema"
SCHEMA_ID = (
    "https://raw.githubusercontent.com/FAIR-bioHeaders/FHT-Specification/main/fht.json"
)
# Core string slots whose exact length LinkML cannot express.
EXACT_LENGTHS = {"checksum": 44, "seqcol_id": 32}
# Optional arrays that are omitted when empty, rather than written as [].
NON_EMPTY_ARRAYS = {
    "transcriptomeSynonym",
    "assemblyAuthor",
    "assemblySoftware",
    "sample",
    "sequencingRuns",
    "instrument",
    "derivedFrom",
}
# Reviewed FHT parent relationships (issue #7). Other relationships are
# deferred to the shared vocabulary decision (#54).
ALLOWED_PARENTS = [
    {
        "properties": {
            "headerType": {"const": "FHT"},
            "relationship": {"const": "filteredFrom"},
        },
        "required": ["headerType", "relationship"],
    },
    {
        "properties": {
            "headerType": {"const": "FHR"},
            "relationship": {"const": "transcribedFrom"},
        },
        "required": ["headerType", "relationship"],
    },
]


def apply_common_rules(generated):
    """Normalize schemaVersion, exact lengths and optional-array cardinality."""
    nodes = (generated, *generated.get("$defs", {}).values())
    for node in nodes:
        version = node.get("properties", {}).get("schemaVersion", {})
        if "const" in version:
            version["enum"] = [version.pop("const")]
        for name, length in EXACT_LENGTHS.items():
            if name in node.get("properties", {}):
                node["properties"][name].update(minLength=length, maxLength=length)
        for name in NON_EMPTY_ARRAYS:
            prop = node.get("properties", {}).get(name)
            if prop and prop.get("type") == "array":
                prop.setdefault("minItems", 1)
    generated["$schema"] = DIALECT
    return generated


def apply_fht_parent_rules(generated):
    """Restrict derivedFrom to reviewed FHT/FHR parent relationships."""
    parent = generated.get("$defs", {}).get("DerivedFrom")
    if parent is None:
        raise ValueError("generated schema has no DerivedFrom definition")
    parent["allOf"] = [
        {
            "description": (
                "Permitted FHT parent relationship: another FHT file filtered "
                "into this set, or an FHR genome whose bases were extracted "
                "(annotation-derived). Genome guidance alone is not a "
                "transcribedFrom link. The shared object already requires the "
                "parent checksum; accessionID is additional, not a substitute."
            ),
            "anyOf": ALLOWED_PARENTS,
        }
    ]
    return generated


def generate():
    view = SchemaView(str(ROOT / "fht_linkml.yml"))
    generated = json.loads(
        JsonSchemaGenerator(
            view.schema,
            include_null=False,
            not_closed=False,
        ).serialize()
    )
    generated = apply_common_rules(generated)
    generated["$id"] = SCHEMA_ID
    generated["title"] = "FHT"
    for key in ("metamodel_version", "version"):
        generated.pop(key, None)
    return apply_fht_parent_rules(generated)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "fht.json",
        help="output file (default: fht.json in the repository root)",
    )
    args = parser.parse_args()
    schema = generate()
    args.output.write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")
    print(f"Generated {args.output}")


if __name__ == "__main__":
    main()
