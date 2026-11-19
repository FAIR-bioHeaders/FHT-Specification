# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. https://mozilla.org/MPL/2.0/.
"""FHT C1 arithmetic that standard JSON Schema cannot express.

The owning draft's requiredness/types remain the generated schema's job.
No absent value is defaulted and no file/checksum/biological claim is checked.
"""

BUSCO_COMPONENTS = ("completeSingle", "completeDuplicated", "fragmented", "missing")
BUSCO_COUNTS = BUSCO_COMPONENTS + ("total",)


def completeness_errors(record):
    """Compare an entirely supplied integer count set, otherwise defer to schema."""
    value = record.get("completeness") if isinstance(record, dict) else None
    if not isinstance(value, dict):
        return []
    if not all(name in value and type(value[name]) is int for name in BUSCO_COUNTS):
        return []
    observed = sum(value[name] for name in BUSCO_COMPONENTS)
    if observed != value["total"]:
        return ["C1: completeness component counts must sum to total "
                f"(sum {observed}, total {value['total']})"]
    return []
