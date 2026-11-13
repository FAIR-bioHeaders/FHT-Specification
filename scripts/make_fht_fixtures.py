"""Write the FHT conformance vectors, parent fixtures and generated examples (stdlib only).

Issue #8: byte-exact positive/rejection fixtures for the FHT 1.0 development
contract (``fht.json``, generated from ``fht_linkml.yml`` by PR #21;
specs/005-rna-transcriptome-header). Every vector is built from a small
metadata template. Expected checksums are computed here with
``hashlib.sha512_256`` and ``base64`` over the bytes the shared
specification's ``docs/FORMAT.md`` rules R1-R5 cover (FASTA ``;~`` headers).
No installed toolkit computes any value — fair-bioheaders has no FHT support
yet (that is issue #9) — and nothing here is published or adopted. The
vectors mirror the shared suite's ``fhp-fasta`` layout and manifest fields so
the shared ``conformance/manifest.json`` can absorb them when FHT is released
(this repo's #55 chain, FAIR-bioHeaders-Specification#107).

All metadata is synthetic and placeholder-shaped: names carry
``(placeholder)``/``synthetic`` labels and identifiers use reserved example
space (example.org URLs, the 10.5555 test DOI prefix, SRR/ERR/DRR 999xxxx
accessions); the taxon is the real *Homo sapiens* NCBI Taxonomy 9606, reused
from the shared suite's vectors. Parent "genome" files are fabricated
fixtures with their own real computed checksums. No real assembly, project,
person or sequence is described.

Determinism: output depends on nothing but the constants below — no clock,
locale, random seed or filesystem order. Compressed vectors use stored
deflate blocks with mtime 0 and no file name, so bytes do not depend on the
local zlib build (the shared scripts/make_conformance.py technique). Reruns
reproduce identical bytes; scripts/check_fht_fixtures.py enforces that in CI
by regenerating into a temporary directory and comparing.

Local usage:

    python scripts/make_fht_fixtures.py

writes conformance/ (valid/, invalid/, parents/, manifest.json) and the
example files this generator owns under examples/ (see OWNED_EXAMPLES).
"""

import argparse
import base64
import copy
import hashlib
import json
from pathlib import Path
import re
import struct
import sys
import zlib

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFORMANCE = ROOT / "conformance"
DEFAULT_EXAMPLES = ROOT / "examples"
MANIFEST_VERSION = 1

# Until an FHT release exists (issue #10), raw main is the only schema
# citation that selects an FHT contract. Per the V7 note in shared
# docs/SCHEMA-VERSIONS.md (FAIR-bioHeaders-Specification#221 ruling, Option A,
# 2026-11-13), a release-form FHT URL is then "any other value" under V5 —
# read as FHR, near-miss warning included (FAIR-bioHeaders-Tools#125); V4
# unsupported-version begins only when FHT enters schemas/versions.json.
RAW_MAIN = ("https://raw.githubusercontent.com/"
            "FAIR-bioHeaders/FHT-Specification/main/fht.json")
RAW_FHT = "https://raw.githubusercontent.com/FAIR-bioHeaders/FHT-Specification/"
W3ID = "https://w3id.org/fair-bioheaders/"
# The FHR raw-main schema URL (as the shared suite's vectors use it); an FHT
# record citing it must fail selection/pattern rules (T2).
FHR_RAW_MAIN = ("https://raw.githubusercontent.com/"
                "FAIR-bioHeaders/FHR-Specification/main/fhr.json")

# Canonical-shaped placeholder for a parent checksum: 44-character padded
# base64 whose final payload character is 'A' (in FORMAT.md R4's canonical
# set), obviously synthetic, never a real digest. Matches this repository's
# tests/fixtures/legacy convention "A"*43 + "=".
PLACEHOLDER_PARENT = "A" * 43 + "="

PREFIX = b";~"
COMMENT = b";"
SUFFIX = ".fht.fasta"
MARK = b"@CHECKSUM@"
FORMAT = "fht-fasta"  # proposed shared-manifest format id, mirroring fhp-fasta

TRANSCRIPTOME = "Synthetic FHT conformance transcript set"
VERSION = "1.0.0"

# The base record (ordered; header lines are written from it by yaml_lines).
FHT_RECORD = {
    "schema": RAW_MAIN,
    "schemaVersion": "1.0",
    "transcriptome": TRANSCRIPTOME,
    "assemblyType": "de novo",
    "moleculeType": "mRNA",
    "taxon": {"name": "Homo sapiens",
              "uri": "https://identifiers.org/taxonomy:9606"},
    "version": VERSION,
    "metadataAuthor": [{"name": "Synthetic metadata author (placeholder)"}],
    "dateCreated": "2026-11-10",
    "documentation": "Synthetic FHT conformance vector; not a real transcriptome.",
}
EXPECTED_METADATA = {"transcriptome": TRANSCRIPTOME, "version": VERSION,
                     "assemblyType": "de novo"}

# The minimal record: exactly the nine required fields (FR-001).
MINIMAL_RECORD = {
    "schema": RAW_MAIN,
    "schemaVersion": "1.0",
    "transcriptome": TRANSCRIPTOME + " (minimal)",
    "assemblyType": "de novo",
    "taxon": {"name": "Homo sapiens",
              "uri": "https://identifiers.org/taxonomy:9606"},
    "version": VERSION,
    "metadataAuthor": [{"name": "Synthetic metadata author (placeholder)"}],
    "dateCreated": "2026-11-10",
}
MINIMAL_EXPECTED = {"transcriptome": TRANSCRIPTOME + " (minimal)",
                    "version": VERSION, "assemblyType": "de novo"}

# Nucleotide bodies. The RNA body uses U and one lower-case line, so the
# normalization-rejection vectors (R1) have something to normalize; the cDNA
# body is the T alphabet of the same synthetic set (FR-006: header parsing
# and checksum coverage are alphabet-independent, supplied bytes preserved).
RNA_BODY = [
    b">tx1 synthetic RNA transcript",
    b"AUGGAACCUAGGUACGUAAUCCGGGUAACCCUAGGAAUCCGUACGAAG",
    b">tx2 synthetic RNA transcript in lower case",
    b"augcuuauggccagguacguaaug",
]
CDNA_BODY = [
    b">tx1 synthetic cDNA transcript",
    b"ATGGAACCTAGGTACGTAATCCGGGTAACCCCTAGGAATCCGTACGAAG",
    b">tx2 synthetic cDNA transcript in lower case",
    b"atgttattggccaggtacgtaatg",
]
MINIMAL_BODY = [
    b">tx1 synthetic RNA transcript",
    b"AUGGAACCUAGGUACGUAAUCCGGGUAACCCUAGGAAUCCGUACGAAG",
]

# ------------------------------------------------------------------ rules ---
# R1-R15 are the shared docs/FORMAT.md rules (summaries mirror the shared
# conformance manifest; the rule text there is authoritative). V1 and V5 (as
# limited by the V7 note) come from shared docs/SCHEMA-VERSIONS.md. T1-T3 are
# provisional FHT rule ids for this development contract; conformance/
# README.md states their text until the shared publication copy of the FHT
# format document names them.
RULES = {
    "R1": "Checksum rule 1: hash the exact file bytes without normalization; "
          "for gzip/BGZF input, the decompressed bytes. A line ends at LF, CRLF or "
          "a CR not followed by LF.",
    "R2": "Checksum rule 2: exactly one root-level checksum line with an unquoted "
          "key; spaces only to match root indentation and before the colon; nested "
          "checksum properties (such as a derivedFrom parent checksum) stay covered.",
    "R3": "Checksum rule 3: exclude that entire line and its terminator; hash every "
          "other byte, so changing covered bytes invalidates the checksum.",
    "R4": "Checksum rule 4: SHA-512/256 digest in standard padded base64, no prefix; "
          "the encoding is canonical (the unused bits are zero) and checksums compare "
          "as exact strings.",
    "R5": "Header parsing: the checksum line holds only the 44-character value, plain "
          "or quoted, with optional spaces; comments, tags, other text, block "
          "scalars and continuation lines are invalid.",
    "R6": "Header parsing: FHT header lines are UTF-8 without U+0085, U+2028 or "
          "U+2029; bytes outside header lines are not decoded.",
    "R7": "Header parsing: a FASTA file must not begin with a UTF-8 byte order mark.",
    "R8": "Header parsing: no duplicate mapping keys, YAML anchors, aliases or "
          "merge keys.",
    "R10": "Header parsing: header lines form the leading block before the first "
           "FASTA record; a ';~' line after that point, including one from a "
           "concatenated file, is invalid; ordinary ';' comments and blank lines "
           "may be mixed in around and inside the block.",
    "R11": "Header writing (FASTA): header lines should not contain a raw '>' or '@'; "
           "writers escape them as \\x3E and \\x40 in double-quoted YAML scalars, "
           "which read back as the same characters.",
    "R12": "Header parsing: YAML metadata is read with YAML 1.2 core-schema types and "
           "must read the same under YAML 1.1; explicit tags and plain scalars that the "
           "two versions read differently (010, 1_000, 1:30, yes, on, 1e3) are invalid.",
    "R13": "Numbers: a numeric metadata value must be a finite number. YAML .nan, "
           ".inf and -.inf make the record invalid.",
    "R14": "Links: a value whose schema format is uri should use http or https (ftp, "
           "urn, doi and info are also accepted); any other scheme stays schema-valid, "
           "but validators warn.",
    "R15": "Extension fields: from the FHT 1.0 development contract (FR-010), a "
           "top-level key matching ^x-[A-Za-z0-9][A-Za-z0-9_.-]*$ may hold any value; "
           "every other unknown key and an x- key in a nested object stay invalid.",
    "V1": "Schema selection: the raw-main FHT schema URL selects the reader's current "
          "FHT schema (here the 1.0 development contract).",
    "V5": "Schema selection: any schema value outside the recognized released-"
          "schema URLs is FHR, checked against the reader's current FHR schema; "
          "a near-miss URL additionally draws the reader's warning "
          "(FAIR-bioHeaders-Tools#125). While no release registers FHT, its "
          "release-form URLs (an fht w3id URL, an FHT-Specification raw tag) "
          "are such values — the V7 draft lane is the owning development "
          "repository's raw-main URL only — and V4 unsupported-version begins "
          "only when FHT enters schemas/versions.json.",
    "T1": "FHT (provisional; text in conformance/README.md): the parsed header "
          "metadata must validate against fht.json — required fields, enums, "
          "patterns, nested cardinality and the closed top level (plus R15 "
          "extension keys).",
    "T2": "FHT (provisional; text in conformance/README.md): a record's schema value "
          "must be a URL the FHT contract accepts (raw main, an FHT release tag or "
          "an FHT w3id URL). Another type's schema or an arbitrary URL fails "
          "fht.json; it never silently selects the FHT schema.",
    "T3": "FHT (provisional; text in conformance/README.md): a derivedFrom parent "
          "checksum must equal the checksum recomputed over the supplied parent "
          "file's bytes; a mismatch is an invalid link (checked-fail), and a parent "
          "that was not supplied makes the link unchecked, never verified.",
}
# Rules that cannot have an invalid (or valid) vector by their nature.
NOT_APPLICABLE = {
    "R11": "R11 is a writing recommendation: a raw '>' or '@' keeps the file valid "
           "and validators warn; the shared suite likewise has no invalid R11 vector.",
    "R14": "R14 makes validators warn, not reject: an unexpected link scheme is "
           "schema-valid. Its valid vector carries \"warnings\": [\"R14\"].",
    "V5": "V5 outcomes depend on the record's bytes; no record that is valid "
          "against the FHT contract can be FHR-valid (FHT states schemaVersion "
          "'1.0', which the current FHR schema rejects, and the required field "
          "sets are disjoint), so V5 has no valid side here. V4 is not "
          "registered as a rule of this suite at all: with no FHT row in "
          "schemas/versions.json there is no citation it can resolve to.",
}

# ------------------------------------------------------------- emission ----
class Line:
    """One line without its terminator; ``excluded`` lines are not hashed."""

    def __init__(self, text, excluded=False):
        self.text = text
        self.excluded = excluded


PLAIN_TEXT = re.compile(r"[A-Za-z][A-Za-z0-9 ()./_,;-]*(://[A-Za-z0-9./_:-]+)?")
YAML_WORDS = {"y", "yes", "n", "no", "true", "false", "on", "off", "null"}
DATE_LIKE = re.compile(r"^[0-9-]+$|^[0-9:.+]+$")


def yaml_scalar(value):
    """A YAML scalar that reads back as ``value`` under YAML 1.1 and 1.2 (R12)."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return json.dumps(value)
    if value is None:
        return "null"
    if (PLAIN_TEXT.fullmatch(value) and value.lower() not in YAML_WORDS
            and not DATE_LIKE.match(value) and not value.endswith((" ", "."))):
        return value
    return "'" + value.replace("'", "''") + "'"


def yaml_lines(value, indent=""):
    """Block YAML lines for values that are scalars, mappings or lists."""
    lines = []
    for key, item in value.items():
        if isinstance(item, dict):
            if not item:
                lines.append(f"{indent}{key}: {{}}")
            else:
                lines.append(f"{indent}{key}:")
                lines += yaml_lines(item, indent + "  ")
        elif isinstance(item, list):
            if not item:
                lines.append(f"{indent}{key}: []")
            else:
                lines.append(f"{indent}{key}:")
                for element in item:
                    if isinstance(element, dict):
                        inner = yaml_lines(element, indent + "  ")
                        lines.append(indent + "- " + inner[0][len(indent) + 2:])
                        lines += inner[1:]
                    elif element is None:
                        lines.append(f"{indent}- null")
                    elif isinstance(element, list):
                        raise ValueError("nested lists are not emitted; use dicts")
                    else:
                        lines.append(f"{indent}- {yaml_scalar(element)}")
        else:
            lines.append(f"{indent}{key}: {yaml_scalar(item)}")
    return lines


def header(metadata, indent="", key="checksum: "):
    """';~' lines for ``metadata`` (a list of str; None marks the checksum)."""
    lines = []
    for item in metadata:
        if item is None:
            lines.append(Line(PREFIX + indent.encode() + key.encode() + MARK,
                              excluded=True))
        else:
            lines.append(Line(PREFIX + indent.encode() + item.encode("utf-8")))
    return lines


def header_of(record, **options):
    return header(yaml_lines(record) + [None], **options)


def digest(data):
    return base64.b64encode(hashlib.new("sha512_256", data).digest()).decode("ascii")


def assemble(lines, endings=b"\n", final_newline=True, hash_data=None):
    """Join ``lines`` and fill the checksum marker (shared-generator pattern).

    ``endings`` is one terminator or a list cycled over the lines. The
    checksum is computed over the bytes of every line not marked excluded,
    unless ``hash_data`` maps those bytes to the bytes hashed instead (the
    deliberate-miscomputation vectors).
    """
    if isinstance(endings, bytes):
        endings = [endings]
    pieces = []
    for index, line in enumerate(lines):
        last = index == len(lines) - 1
        ending = b"" if last and not final_newline else endings[index % len(endings)]
        pieces.append((line, line.text + ending))
    covered = b"".join(data for line, data in pieces if not line.excluded)
    value = digest(hash_data(covered) if hash_data else covered).encode("ascii")
    return b"".join(data.replace(MARK, value) for _, data in pieces), value.decode()


def lines_of(record, body=RNA_BODY, **options):
    return header_of(record, **options) + [Line(text) for text in body]


def checksum_line(lines):
    positions = [i for i, line in enumerate(lines) if line.excluded]
    assert len(positions) == 1, positions
    return positions[0]


# ---------------------------------------------------------- compression ----
def _stored_deflate(data):
    if not data:
        return b"\x01\x00\x00\xff\xff"
    out = b""
    for start in range(0, len(data), 0xFFFF):
        chunk = data[start:start + 0xFFFF]
        final = start + 0xFFFF >= len(data)
        out += bytes([final]) + struct.pack("<HH", len(chunk), len(chunk) ^ 0xFFFF) + chunk
    return out


def _trailer(data):
    return struct.pack("<II", zlib.crc32(data), len(data) & 0xFFFFFFFF)


def gzip_member(data):
    # ID1 ID2 CM=deflate FLG=0 MTIME=0 XFL=0 OS=unknown: no name, fixed time.
    return b"\x1f\x8b\x08\x00\x00\x00\x00\x00\x00\xff" + _stored_deflate(data) + _trailer(data)


BGZF_EOF = bytes.fromhex("1f8b08040000000000ff0600424302001b0003000000000000000000")


def bgzf(data, block_size=96):
    out = b""
    for start in range(0, len(data), block_size):
        chunk = data[start:start + block_size]
        deflated = _stored_deflate(chunk)
        block_size_minus_one = 18 + len(deflated) + 8 - 1
        out += (
            b"\x1f\x8b\x08\x04\x00\x00\x00\x00\x00\xff"
            + struct.pack("<H", 6) + b"BC" + struct.pack("<HH", 2, block_size_minus_one)
            + deflated + _trailer(chunk)
        )
    return out + BGZF_EOF


def decompress(data):
    """Concatenated gzip members (also valid BGZF input)."""
    out = b""
    while data:
        engine = zlib.decompressobj(31)
        out += engine.decompress(data) + engine.flush()
        data = engine.unused_data
    return out


# ---------------------------------------- this file's reading of the rules --
# Used for the generator's self-check and to source parent checksums from
# written bytes. scripts/check_fht_fixtures.py ships its own separately
# written implementation of the same rules; that pairing is the cross-check.

def split_lines_keepends(data):
    """R1: a line ends at LF, CRLF or a lone CR; the terminator belongs to it."""
    lines, i, n = [], 0, len(data)
    while i < n:
        j = i
        while j < n and data[j] not in (0x0A, 0x0D):
            j += 1
        if j >= n:
            lines.append((data[i:j], b""))
            break
        if data[j] == 0x0A:
            lines.append((data[i:j], b"\n"))
            i = j + 1
        elif j + 1 < n and data[j + 1] == 0x0A:
            lines.append((data[i:j], b"\r\n"))
            i = j + 2
        else:
            lines.append((data[i:j], b"\r"))
            i = j + 1
    return lines


def transform_sequence_lines(data, fn):
    """Apply ``fn`` to sequence-line bytes only (never ';' or '>' lines)."""
    out = []
    for line, term in split_lines_keepends(data):
        if line and line[:1] not in (PREFIX, COMMENT, b">"):
            line = fn(line)
        out.append(line + term)
    return b"".join(out)


B64 = rb"[A-Za-z0-9+/]{42}[AEIMQUYcgkosw048]="
CHECKSUM_VALUE = re.compile(
    rb"^ +(?:(" + B64 + rb")|'(" + B64 + rb")'|\"(" + B64 + rb")\") *$")
CHECKSUM_KEY = re.compile(rb"^([ \t]*)checksum( *):(.*)$", re.S)


def read_header(data):
    """Return (header (line, term) pairs, root_indent); raise per R10."""
    in_block = True
    block = []
    for line, term in split_lines_keepends(data):
        if line.startswith(PREFIX):
            if not in_block:
                raise ValueError("a ';~' line appears after the first record (R10)")
            block.append((line, term))
        elif in_block and line.startswith(b">"):
            in_block = False
    if not block:
        raise ValueError("no header block")
    contents = [line[len(PREFIX):] for line, _ in block]
    indents = [len(text) - len(text.lstrip(b" \t")) for text in contents
               if text.strip() and not text.lstrip().startswith(b"#")]
    if not indents:
        raise ValueError("header block has no mapping lines")
    return block, min(indents)


def reference_checksum(data):
    """Return (stated, computed) applying R2-R4; raise ValueError if invalid."""
    block, root_indent = read_header(data)
    matches = []
    for line, term in block:
        found = CHECKSUM_KEY.match(line[len(PREFIX):])
        if found and len(found.group(1)) == root_indent:
            matches.append((line, term, found))
    if len(matches) != 1:
        raise ValueError(f"expected exactly one root checksum line, "
                         f"found {len(matches)} (R2)")
    line, term, found = matches[0]
    whole = line + term
    if data.count(whole) != 1:
        raise ValueError("checksum line not uniquely locatable (R2)")
    position = data.find(whole)
    grammar = CHECKSUM_VALUE.fullmatch(found.group(3))
    if not grammar:
        raise ValueError("the checksum line holds more than the checksum value (R4, R5)")
    stated = (grammar.group(1) or grammar.group(2) or grammar.group(3)).decode()
    computed = digest(data[:position] + data[position + len(whole):])
    return stated, computed


# --------------------------------------------------------------- vectors ----
VALID = []
INVALID = []
PARENT_LINKS = {}  # keyed by short name; filled while building


def valid(name, data, rules, description, checksum, expected=EXPECTED_METADATA,
          compression=None, warnings=None, parent_links=None):
    VALID.append(dict(name=name, data=data, rules=rules, description=description,
                      checksum=checksum, expected=expected, compression=compression,
                      warnings=warnings, parent_links=parent_links, status="valid"))


def invalid(name, data, rule, reason, self_checksum, metadata=None, result=None,
            parent_links=None):
    INVALID.append(dict(name=name, data=data, rule=rule, reason=reason,
                        self_checksum=self_checksum, metadata=metadata,
                        result=result, parent_links=parent_links, status="invalid"))


def record_of(drop=(), **changes):
    """FHT_RECORD with ``changes`` applied and the keys in ``drop`` removed.

    Overwritten keys keep their declared position; new keys append."""
    record = copy.deepcopy(FHT_RECORD)
    record.update(copy.deepcopy(changes))
    for key in drop:
        record.pop(key, None)
    return record


def fht_invalid_record(name, record, rule, reason):
    """A metadata-invalid vector: bytes and stated checksum stay consistent, so
    an implementation cannot pass by failing the checksum comparison by
    accident (the shared suite's convention for non-checksum rules)."""
    data, value = assemble(lines_of(record))
    invalid(name, data, rule, reason, "matches", metadata=dict(record, checksum=value))


def build_parent_fixture():
    """parents/parent-genome.fhr.fasta — a synthetic FHR-headed genome file that
    gives the parent-link vectors real bytes to verify against. It is a byte
    target, not an FHR conformance vector: its metadata is placeholder-shaped
    FHR 2.1 (a released contract) and its checksum is genuinely computed over
    its own bytes under R1-R5."""
    record = {
        "schema": W3ID + "fhr/v0.5.0",
        "schemaVersion": "2.1",
        "genome": "Synthetic FHR parent genome for FHT link fixtures (placeholder)",
        "taxon": {"name": "Homo sapiens",
                  "uri": "https://identifiers.org/taxonomy:9606"},
        "version": "1.0.0",
        "metadataAuthor": [{"name": "Synthetic metadata author (placeholder)"}],
        "dateCreated": "2026-11-10",
        "masking": "not-masked",
        "documentation": "Synthetic parent fixture for FHT-Specification#8; "
                         "not a real assembly.",
    }
    body = [b">ctgA synthetic scaffold", b"ACGTACGTACGTACGTACGTACGTACGT",
            b">ctgB synthetic scaffold", b"GGTTAACCATCGATCGAT"]
    data, value = assemble(header_of(record) + [Line(text) for text in body])
    stated, computed = reference_checksum(data)
    assert stated == computed == value, "parent fixture must be self-consistent"
    PARENT_LINKS["genome"] = {"file": "parents/parent-genome.fhr.fasta",
                              "statedChecksum": computed}
    return data


def swap_first_different(value):
    """Deterministically perturb a base64 payload: swap the first character
    that differs from the leading one; the canonical final character and the
    character set stay intact, so only the exact-string comparison fails."""
    chars = list(value)
    for i in range(1, 42):
        if chars[i] != chars[0]:
            chars[0], chars[i] = chars[i], chars[0]
            return "".join(chars)
    raise AssertionError(f"{value!r} has no perturbable character")


def build_vectors():
    # ---- valid: shared byte rules on RNA and cDNA bodies --------------------
    data, value = fht_lines_valid(
        "fht-fasta-lf", lines_of(FHT_RECORD),
        ["T1", "R1", "R2", "R3", "R4", "R7", "R8", "R10", "R12"],
        "RNA transcript set (U alphabet); LF line endings; the checksum line is "
        "the last header line; plain scalars and mappings follow R8/R12.")
    plain = data
    fht_lines_valid("fht-fasta-crlf", lines_of(FHT_RECORD), ["R1", "R3"],
                    "CRLF line endings; CR bytes are hashed.", endings=b"\r\n")
    fht_lines_valid("fht-fasta-cr", lines_of(FHT_RECORD), ["R1", "R3"],
                    "Lone CR line endings.", endings=b"\r")
    fht_lines_valid("fht-fasta-mixed-endings", lines_of(FHT_RECORD), ["R1", "R3"],
                    "LF, CRLF and CR line endings mixed in one file.",
                    endings=[b"\n", b"\r\n", b"\r"])
    fht_lines_valid("fht-fasta-no-final-newline", lines_of(FHT_RECORD), ["R1", "R3"],
                    "The last sequence line has no terminator.", final_newline=False)
    fht_lines_valid("fht-fasta-cdna", lines_of(FHT_RECORD, body=CDNA_BODY),
                    ["T1", "R1"],
                    "cDNA representation (T alphabet) of the same synthetic set: "
                    "coverage is alphabet-independent (FR-006) and the supplied T "
                    "bytes are preserved, not converted to U.")
    _, value_min = fht_lines_valid("fht-fasta-minimal",
                                   lines_of(MINIMAL_RECORD, body=MINIMAL_BODY),
                                   ["T1"],
                                   "Exactly the nine required fields (FR-001); no "
                                   "optional field is defaulted or written null.",
                                   expected=MINIMAL_EXPECTED)
    PARENT_LINKS["minimal"] = {"file": "valid/fht-fasta-minimal.fht.fasta",
                               "statedChecksum": value_min}

    lines = header_of(FHT_RECORD)
    lines.insert(0, Line(COMMENT + b" ordinary comment before the header"))
    lines.insert(1, Line(b""))
    lines.insert(5, Line(COMMENT + b" ordinary comment between header lines"))
    lines.insert(6, Line(b""))
    lines.insert(9, Line(PREFIX + b"# a YAML comment inside the header"))
    lines.append(Line(b""))
    lines += [Line(text) for text in RNA_BODY]
    lines.append(Line(COMMENT + b"  legacy FASTA comment after a record"))
    fht_lines_valid("fht-fasta-comments-and-blank-lines", lines, ["R3", "R10"],
                    "Ordinary ';' comments, blank lines and a ';~#' YAML comment "
                    "around or inside the header block; a plain ';' comment after a "
                    "record stays a comment (only ';~' lines after records break "
                    "R10); all of it is hashed.")
    fht_lines_valid("fht-fasta-root-indented", header_of(FHT_RECORD, indent=" ")
                    + [Line(text) for text in RNA_BODY], ["R2"],
                    "Every header line, including the checksum line, has root "
                    "indentation 1.")
    fht_lines_valid("fht-fasta-space-before-colon",
                    header_of(FHT_RECORD, key="checksum  : ")
                    + [Line(text) for text in RNA_BODY], ["R2"],
                    "Spaces before the colon on the checksum line.")
    moved = lines_of(FHT_RECORD)
    position = checksum_line(moved)
    moved.insert(0, moved.pop(position))
    fht_lines_valid("fht-fasta-checksum-first", moved, ["R3"],
                    "The checksum line is first in the header block: R3 excludes "
                    "the line wherever it sits, so the value matches fht-fasta-lf.")
    lines = lines_of(FHT_RECORD)
    lines[checksum_line(lines)].text += b"   "
    fht_lines_valid("fht-fasta-checksum-trailing-spaces", lines, ["R3", "R5"],
                    "Trailing spaces on the checksum line are excluded with it.")
    lines = header_of(FHT_RECORD)
    lines[-1].text = lines[-1].text.replace(MARK, b"'" + MARK + b"'")
    fht_lines_valid("fht-fasta-quoted-value",
                    lines + [Line(text) for text in RNA_BODY], ["R2", "R5"],
                    "The checksum value is a quoted single-line scalar; the key "
                    "stays unquoted.")
    nested = record_of(derivedFrom=[{"headerType": "FHR", "checksum": PLACEHOLDER_PARENT,
                                     "relationship": "transcribedFrom"}])
    fht_lines_valid("fht-fasta-nested-checksum", lines_of(nested), ["R2", "R3", "T1"],
                    "A root checksum line plus the indented nested parent checksum "
                    "under derivedFrom: only the root line is excluded; the nested "
                    "checksum is covered metadata (R2).")
    lines = lines_of(FHT_RECORD)
    doc = [i for i, line in enumerate(lines) if line.text.startswith(PREFIX + b"documentation:")]
    assert len(doc) == 1
    lines[doc[0]] = Line(
        b';~documentation: "transcripts \\x3E 1000 nt; contact someone\\x40example.org"')
    fht_lines_valid("fht-fasta-escaped-record-markers", lines, ["R11", "T1"],
                    "A header value holding '>' and '@' written as \\x3E and \\x40 "
                    "in a double-quoted scalar; it reads back with the real "
                    "characters.",
                    expected=dict(EXPECTED_METADATA,
                                  documentation="transcripts > 1000 nt; contact "
                                                "someone@example.org"))
    utf8_documentation = ("Synthetic FHT conformance vector; caf\u00e9 "
                          "(placeholder UTF-8 metadata)")
    lines = lines_of(FHT_RECORD)
    doc = [i for i, line in enumerate(lines) if line.text.startswith(PREFIX + b"documentation:")]
    lines[doc[0]] = Line((";~documentation: 'Synthetic FHT conformance vector; "
                          "caf\u00e9 (placeholder UTF-8 metadata)'").encode("utf-8"))
    fht_lines_valid("fht-fasta-utf8-metadata", lines, ["R6", "T1"],
                    "Raw non-ASCII UTF-8 (U+00E9) in a header value is allowed; "
                    "only U+0085, U+2028 and U+2029 are excluded from header lines.",
                    expected=dict(EXPECTED_METADATA, documentation=utf8_documentation))
    extension = record_of(**{
        "x-example-note": "Producer extension (placeholder)",
        "x-example-count": 3,
        "x-example-ratio": 0.5,
        "x-example-flag": True,
        "x-example-list": ["a", 2, None],
        "x-example-object": {"internal": "value", "count": 1},
    })
    fht_lines_valid("fht-fasta-extension-fields", lines_of(extension), ["R15", "T1"],
                    "Top-level x- extension fields of every JSON type (FR-010, R15): "
                    "string, integer, number, boolean, list (with null) and object.")
    data_w, value_w = assemble(lines_of(record_of(relatedLink=["javascript:void(0)"])))
    valid("fht-fasta-link-scheme-warning", data_w, ["R14", "T1"],
          "A relatedLink URI with a non-link scheme stays schema-valid; validators "
          "warn (R14).", checksum=value_w,
          expected=dict(EXPECTED_METADATA, relatedLink=["javascript:void(0)"]),
          warnings=["R14"])
    valid("fht-fasta-gzip", gzip_member(plain), ["R1"],
          "fht-fasta-lf compressed as one gzip member; the checksum covers the "
          "decompressed bytes and is unchanged.", checksum=value,
          compression="gzip")
    valid("fht-fasta-bgzf", bgzf(plain), ["R1"],
          "fht-fasta-lf compressed as multi-block BGZF (with EOF block); same "
          "checksum.", checksum=value, compression="bgzf")

    # ---- valid: schema selection (V1, T2) ------------------------------------
    valid("fht-fasta-schema-raw-main", plain, ["V1", "T2"],
          "The raw-main FHT schema URL with schemaVersion '1.0' selects the "
          "reader's current FHT contract — today the 1.0 development schema. The "
          "bytes are those of fht-fasta-lf under a stable V1 vector id.",
          checksum=value,
          expected=dict(EXPECTED_METADATA, schema=RAW_MAIN, schemaVersion="1.0"))

    # ---- valid: parent links (T3) ---------------------------------------------
    genome_checksum = PARENT_LINKS["genome"]["statedChecksum"]
    minimal_checksum = PARENT_LINKS["minimal"]["statedChecksum"]
    transcribed = record_of(derivedFrom=[{
        "headerType": "FHR", "checksum": genome_checksum,
        "relationship": "transcribedFrom",
        "accessionID": {"name": "Synthetic accession DB (placeholder)",
                        "url": "https://example.org/fhr/synthetic-genome"}}])
    fht_lines_valid("fht-fasta-parent-transcribed-from", lines_of(transcribed),
                    ["T1", "T3"],
                    "A transcribedFrom FHR parent: the supplied "
                    "parents/parent-genome.fhr.fasta recomputes to exactly the "
                    "cited checksum (checked-pass). The accessionID is additional, "
                    "not a substitute.",
                    parent_links=[dict(PARENT_LINKS["genome"], result="checked-pass")])
    filtered = record_of(transcriptome=TRANSCRIPTOME + " (filtered subset)",
                         derivedFrom=[{"headerType": "FHT",
                                       "checksum": minimal_checksum,
                                       "relationship": "filteredFrom"}])
    fht_lines_valid("fht-fasta-parent-filtered-from", lines_of(filtered), ["T1", "T3"],
                    "A filteredFrom FHT parent whose file is the fht-fasta-minimal "
                    "vector, cited by its recomputed checksum (checked-pass).",
                    expected=dict(EXPECTED_METADATA,
                                  transcriptome=TRANSCRIPTOME + " (filtered subset)"),
                    parent_links=[dict(PARENT_LINKS["minimal"],
                                       result="checked-pass")])
    unavailable = record_of(derivedFrom=[{"headerType": "FHR",
                                          "checksum": PLACEHOLDER_PARENT,
                                          "relationship": "transcribedFrom"}])
    fht_lines_valid("fht-fasta-parent-unavailable", lines_of(unavailable), ["T1", "T3"],
                    "A well-formed parent checksum whose parent file was not "
                    "supplied: the record is valid and the link is unchecked — a "
                    "reader must not report it verified and must not reject the "
                    "record for the absent parent.",
                    parent_links=[{"file": None, "statedChecksum": PLACEHOLDER_PARENT,
                                   "result": "unchecked"}])

    # ---- valid: rich record (every optional field) ----------------------------
    lengths = [len(text) for text in RNA_BODY if not text.startswith(b">")]
    total = sum(lengths)
    descending = sorted(lengths, reverse=True)
    running, n50 = 0, descending[-1]
    for length in descending:
        running += length
        if running * 2 >= total:
            n50 = length
            break
    rich = record_of(
        accessionID={"name": "Synthetic accession DB (placeholder)",
                     "url": "https://example.org/fht/synthetic-set"},
        assemblyAuthor=[{"name": "Synthetic assembler (placeholder)",
                         "nameType": "Organizational"}],
        assemblySoftware=[{"name": "Synthetic Assembler (placeholder)",
                           "version": "0.0.1",
                           "uri": "https://example.org/synthetic-assembler",
                           "commandLineOption": ["--no-variants", "--jellyfish"]}],
        completeness={"lineageDataset": "primates_odb10",
                      "completeSingle": 1, "completeDuplicated": 0,
                      "fragmented": 0, "missing": 0, "total": 1},
        funding="Synthetic Grant SYN-0001 (placeholder)",
        identifier=["example.org:SYN-FHT-0001"],
        instrument=["Synthetic Instrument 2000 (placeholder)"],
        libraryStrategy="RNA-Seq",
        relatedLink=["https://example.org/synthetic-project"],
        reuseConditions="CC0-1.0",
        sample=[{"tissue": "synthetic tissue", "tissueIdentifier": "UBERON:0000000",
                 "developmentalStage": "placeholder stage"},
                {"tissue": "synthetic tissue", "condition": "placeholder condition"}],
        scholarlyArticle="10.5555/synthetic.example",
        sequencingRuns=["SRR9990001", "ERR9990002", "DRR9990003"],
        strandedness="reverse",
        transcriptomeSynonym=["Synthetic set alias (placeholder)"],
        vitalStats={"totalTranscripts": len(lengths), "N50": n50,
                    "averageTranscriptLength": total / len(lengths)},
        voucherSpecimen="Synthetic voucher, placeholder freezer shelf A1",
        derivedFrom=[{"headerType": "FHR", "checksum": genome_checksum,
                      "relationship": "transcribedFrom"},
                     {"headerType": "FHT", "checksum": minimal_checksum,
                      "relationship": "filteredFrom"}],
        **{"x-example-rich": "extension in the rich record"},
    )
    fht_lines_valid("fht-fasta-rich", lines_of(rich), ["T1", "R13", "R15", "T3"],
                    "Every optional FHT field; vitalStats are genuinely computed "
                    "from the vector's own sequence bytes; both permitted parent "
                    "relationships cite the supplied parent fixtures' recomputed "
                    "checksums (checked-pass); one extension field.",
                    parent_links=[dict(PARENT_LINKS["genome"], result="checked-pass"),
                                  dict(PARENT_LINKS["minimal"],
                                       result="checked-pass")])

    # ---- invalid: checksum coverage (R1/R3/R4) --------------------------------
    data, _ = assemble(lines_of(FHT_RECORD), endings=b"\r\n",
                       hash_data=lambda b: b.replace(b"\r\n", b"\n"))
    invalid("fht-fasta-crlf-normalized-checksum", data, "R1",
            "Checksum computed after normalizing CRLF line endings to LF.", "broken")
    data, _ = assemble(lines_of(FHT_RECORD),
                       hash_data=lambda b: transform_sequence_lines(
                           b, lambda s: s.replace(b"U", b"T").replace(b"u", b"t")))
    invalid("fht-fasta-u-normalized-checksum", data, "R1",
            "Checksum computed after U-to-T (RNA-to-cDNA) normalization of the "
            "sequence lines; the supplied bytes keep U (FR-006).", "broken")
    data, _ = assemble(lines_of(FHT_RECORD),
                       hash_data=lambda b: transform_sequence_lines(b,
                                                                    lambda s: s.upper()))
    invalid("fht-fasta-case-normalized-checksum", data, "R1",
            "Checksum computed after upper-casing the lower-case sequence line.",
            "broken")
    data, _ = assemble(lines_of(FHT_RECORD))
    invalid("fht-fasta-sequence-tampered", data.replace(b"CCGUACGAAG", b"CCGUACGAAC"),
            "R3", "A nucleotide changed after the checksum was computed (checksum "
            "mismatch); the metadata itself is untouched and still valid.", "broken")

    def wrong_digest(algorithm):
        return lambda covered: base64.b64encode(
            hashlib.new(algorithm, covered).digest()[:32]).decode("ascii").encode()

    data, _ = assemble(lines_of(FHT_RECORD), hash_data=wrong_digest("sha256"))
    invalid("fht-fasta-checksum-sha256", data, "R4",
            "The value is standard padded base64 of a SHA-256 digest, not of "
            "SHA-512/256; exact-string comparison fails.", "broken")
    data, _ = assemble(lines_of(FHT_RECORD), hash_data=wrong_digest("sha512"))
    invalid("fht-fasta-checksum-truncated-sha512", data, "R4",
            "The value is SHA-512 truncated to 32 bytes and re-encoded; SHA-512/256 "
            "is a distinct algorithm, so the exact string differs (and the encoding "
            "may not even be canonical).", "broken")
    data, value = assemble(lines_of(FHT_RECORD))
    broken = value[:-2] + ("B" if value[-2] != "B" else "C") + "="
    invalid("fht-fasta-checksum-non-canonical",
            data.replace(value.encode(), broken.encode()), "R4",
            "The final payload character is outside the canonical set "
            "AEIMQUYcgkosw048, so a 32-byte digest can never encode to it.",
            "unreachable")

    # ---- invalid: checksum-line shape (R2/R5) ---------------------------------
    data, _ = assemble(header_of(FHT_RECORD)[:-1] + [Line(text) for text in RNA_BODY])
    invalid("fht-fasta-missing-checksum", data, "R2",
            "No root-level checksum line at all.", "unreachable")
    lines = lines_of(FHT_RECORD)
    position = checksum_line(lines)
    lines.insert(2, Line(lines[position].text, excluded=True))
    data, _ = assemble(lines)
    invalid("fht-fasta-two-checksum-lines", data, "R2",
            "Two root-level checksum lines with the same value.", "unreachable")
    nested_only = dict(MINIMAL_RECORD)
    nested_only["derivedFrom"] = [{"headerType": "FHR", "checksum": PLACEHOLDER_PARENT,
                                   "relationship": "transcribedFrom"}]
    data, _ = assemble(header_of(nested_only)[:-1]
                       + [Line(text) for text in MINIMAL_BODY])
    invalid("fht-fasta-only-nested-checksum", data, "R2",
            "Only the indented derivedFrom parent checksum is present; a nested "
            "checksum never substitutes for the root line.", "unreachable")
    data, value = assemble(lines_of(FHT_RECORD))
    kept = data.split(b"\n")
    index = next(i for i, text in enumerate(kept) if text.startswith(PREFIX + b"checksum:"))
    kept[index:index + 1] = [PREFIX + b"checksum: |-",
                             PREFIX + b"  " + value.encode()]
    invalid("fht-fasta-block-literal-checksum", b"\n".join(kept), "R5",
            "The checksum line is a YAML block scalar indicator ('|-') and the "
            "value sits on the next header line; R5 requires the value on the "
            "checksum line itself.", "unreachable")
    kept = data.split(b"\n")
    kept[index:index + 1] = [PREFIX + b"checksum: QUJD",
                             PREFIX + b" RUZHSUpLS0xNT1="]
    invalid("fht-fasta-continued-checksum", b"\n".join(kept), "R5",
            "A checksum value continued on the following header line (a folded "
            "plain scalar); R5 allows one line only.", "unreachable")
    invalid("fht-fasta-checksum-with-comment",
            data.replace(value.encode(), (value + "  # not covered").encode()),
            "R5", "A YAML comment follows the checksum value; the line holds the "
            "value and nothing else.", "unreachable")

    # ---- invalid: header text rules (R6/R7/R8/R10) -----------------------------
    lines = lines_of(FHT_RECORD)
    doc = [i for i, line in enumerate(lines) if line.text.startswith(PREFIX + b"documentation:")]
    lines[doc[0]] = Line(PREFIX + b'documentation: "Synthetic vector with a raw '
                         b'\xe2\x80\xa8 U+2028 byte (invalid)"')
    data, _ = assemble(lines)
    invalid("fht-fasta-u2028-in-header", data, "R6",
            "A raw U+2028 byte inside a header line: YAML treats it as a line "
            "break (R6 excludes it; U+0085 and U+2029 behave the same way).",
            "matches")
    lines = lines_of(FHT_RECORD)
    lines[0] = Line(b"\xef\xbb\xbf" + lines[0].text)
    data, _ = assemble(lines)
    invalid("fht-fasta-utf8-bom", data, "R7",
            "The file begins with a UTF-8 byte order mark; the BOM also removes "
            "the ';~' prefix from the first header line.", "matches")
    lines = header_of(FHT_RECORD)
    lines.insert(-1, Line(b";~version: 1.0.1"))
    data, _ = assemble(lines + [Line(text) for text in RNA_BODY])
    invalid("fht-fasta-duplicate-key", data, "R8",
            "A duplicate root-level 'version' mapping key.", "matches")
    lines = header_of(FHT_RECORD)
    lines.insert(-1, Line(b";~relatedLink: &links"))
    lines.insert(-1, Line(b";~- https://example.org/synthetic-project"))
    lines.insert(-1, Line(b";~transcriptomeSynonym: *links"))
    data, _ = assemble(lines + [Line(text) for text in RNA_BODY])
    invalid("fht-fasta-yaml-anchor-alias", data, "R8",
            "A YAML anchor on relatedLink reused through an alias on "
            "transcriptomeSynonym.", "matches")
    data, _ = assemble(lines_of(FHT_RECORD)
                       + [Line(b";~funding: added after the first record")])
    invalid("fht-fasta-header-after-record", data, "R10",
            "A ';~' line after the first FASTA record; it is neither ignored nor "
            "merged. (The stated checksum is consistent with the bytes, but a "
            "reader must reject the shape before the comparison stage, so this "
            "vector is classified 'unreachable'.)", "unreachable")
    invalid("fht-fasta-concatenated", plain + plain, "R10",
            "Two complete FHT files concatenated; each part is internally "
            "checksum-consistent, but the second header block follows records "
            "(and adds a second root checksum line).", "unreachable")

    # ---- invalid: YAML value rules (R12/R13) -----------------------------------
    patched = lines_of(FHT_RECORD)
    doc = [i for i, line in enumerate(patched) if line.text.startswith(PREFIX + b"documentation:")]
    patched[doc[0]] = Line(b";~vitalStats:")
    patched.insert(doc[0] + 1, Line(b";~  totalTranscripts: 011"))
    data, _ = assemble(patched)
    invalid("fht-fasta-yaml-leading-zero", data, "R12",
            "A plain integer with a leading zero: YAML 1.1 reads 011 as octal 9, "
            "YAML 1.2 reads decimal 11, so the value is ambiguous (the schema "
            "cannot see this — only the R12 rule rejects it).", "matches")
    patched = lines_of(FHT_RECORD)
    doc = [i for i, line in enumerate(patched) if line.text.startswith(PREFIX + b"documentation:")]
    patched[doc[0]] = Line(b";~vitalStats:")
    patched.insert(doc[0] + 1, Line(b";~  averageTranscriptLength: .inf"))
    data, _ = assemble(patched)
    invalid("fht-fasta-inf-vital-stats", data, "R13",
            "vitalStats.averageTranscriptLength is the YAML .inf: not a finite "
            "number (type 'number' alone accepts it, so R13 is the rejection).",
            "matches")

    # ---- invalid: extension fields (R15) ----------------------------------------
    fht_invalid_record("fht-fasta-extension-nested-key",
                       record_of(taxon={"name": "Homo sapiens",
                                        "uri": "https://identifiers.org/taxonomy:9606",
                                        "x-note": "extension in a nested object"}),
                       "R15", "An x- key inside the nested taxon object: extension "
                       "fields are top level only.")
    fht_invalid_record("fht-fasta-extension-uppercase-key",
                       record_of(**{"X-Wrongcase": "extension keys are lowercase x-"}),
                       "R15", "A top-level key starting with 'X-' does not match "
                       "the extension pattern and is an unknown key.")

    # ---- invalid: FHT contract (T1) ----------------------------------------------
    fht_invalid_record("fht-fasta-missing-assembly-type",
                       record_of(drop=["assemblyType"]), "T1",
                       "The required assemblyType field is absent.")
    fht_invalid_record("fht-fasta-bad-assembly-type", record_of(assemblyType="hybrid"),
                       "T1", "assemblyType hybrid is not an FHT value (de novo, "
                       "genome-guided, annotation-derived).")
    fht_invalid_record("fht-fasta-molecule-type-cdna", record_of(moleculeType="cDNA"),
                       "T1", "moleculeType cDNA is not an FHT value: cDNA is a "
                       "preparation context, not a biological molecule class "
                       "(D1, FR-002).")
    fht_invalid_record("fht-fasta-empty-sample", record_of(sample=[]), "T1",
                       "An optional array written empty instead of omitted "
                       "(sample requires at least one item when present, FR-003).")
    fht_invalid_record("fht-fasta-fhr-key-genome", record_of(genome="Synthetic genome"),
                       "T1", "The FHR-only key genome: the FHT top level is closed.")
    fht_invalid_record("fht-fasta-legacy-key-masking",
                       record_of(masking="not-masked"), "T1",
                       "The legacy FHT key masking was removed by the FHT 1.0 "
                       "contract (FR-009); it is an unknown key.")
    fht_invalid_record("fht-fasta-bad-run-accession",
                       record_of(sequencingRuns=["SRS1234567"]), "T1",
                       "An SRS sample accession in sequencingRuns; only SRR/ERR/DRR "
                       "run accessions are allowed (FR-003).")
    fht_invalid_record("fht-fasta-derived-from-no-checksum",
                       record_of(derivedFrom=[{"headerType": "FHR",
                                               "relationship": "transcribedFrom",
                                               "accessionID": {
                                                   "name": "Synthetic accession DB (placeholder)",
                                                   "url": "https://example.org/fhr/x"}}]),
                       "T1", "A derivedFrom entry without the parent checksum: an "
                       "accessionID alone is never a substitute (FR-007).")
    fht_invalid_record("fht-fasta-derived-from-fhp-parent",
                       record_of(derivedFrom=[{"headerType": "FHP",
                                               "checksum": PLACEHOLDER_PARENT,
                                               "relationship": "translatedFrom"}]),
                       "T1", "An FHP parent with translatedFrom: FHT permits only "
                       "FHR + transcribedFrom and FHT + filteredFrom (FR-007).")
    fht_invalid_record("fht-fasta-derived-from-bad-relationship",
                       record_of(derivedFrom=[{"headerType": "FHR",
                                               "checksum": PLACEHOLDER_PARENT,
                                               "relationship": "annotates"}]),
                       "T1", "relationship annotates with an FHR parent: the FHR "
                       "pair must use transcribedFrom (FR-007).")

    # ---- invalid: schema selection (T2, V1, V5) -----------------------------------
    fht_invalid_record("fht-fasta-cites-fhr-schema", record_of(schema=FHR_RAW_MAIN),
                       "T2", "Citing the FHR raw-main schema URL: the FHT "
                       "contract's schema pattern rejects it, and a reader that "
                       "selected FHR from the URL instead would still reject "
                       "FHT-only keys — the record never silently validates.")
    fht_invalid_record("fht-fasta-cites-arbitrary-url",
                       record_of(schema="https://example.org/schemas/my-fht-profile.json"),
                       "T2", "A schema value outside the closed FHT URL pattern: "
                       "unlike released FHR, whose schema field is unconstrained "
                       "(V5), the FHT development contract accepts only its own "
                       "raw-main, tag and w3id URLs.")
    fht_invalid_record("fht-fasta-version-2-0-via-raw-main",
                       record_of(schemaVersion="2.0"), "V1",
                       "Raw main selects the reader's current FHT contract (1.0); "
                       "a future major stated against it is rejected — no fallback "
                       "and no newer FHT schema exists (FR-008).")
    patched = lines_of(FHT_RECORD)
    sv = [i for i, line in enumerate(patched)
          if line.text.startswith(PREFIX + b"schemaVersion:")]
    assert len(sv) == 1
    patched[sv[0]] = Line(b";~schemaVersion: 1.0")
    data, value = assemble(patched)
    invalid("fht-fasta-schemaversion-number", data, "V1",
            "schemaVersion written as the unquoted YAML number 1.0: the current "
            "contract requires the string '1.0' (docs/SCHEMA-VERSIONS.md quotes "
            "it for exactly this reason).", "matches")
    fht_invalid_record("fht-fasta-schema-w3id-release-without-fht",
                       record_of(schema=W3ID + "fht/v0.5.0"), "V5",
                       "No release registers FHT, so this release-form w3id URL "
                       "matches no V1-V3 form (matching is exact) and stays 'any "
                       "other value' under V5 — read as FHR against the reader's "
                       "current FHR schema, near-miss warning included "
                       "(FAIR-bioHeaders-Tools#125), never as the draft: the V7 "
                       "lane is the raw-main URL only (ruling of 2026-11-13, "
                       "FAIR-bioHeaders-Specification#221). From the record's "
                       "bytes the FHR reading rejects it: schemaVersion '1.0' is "
                       "outside FHR's accepted set; required genome, "
                       "assemblyAuthor and masking are absent; transcriptome, "
                       "assemblyType and moleculeType breach FHR's closed top "
                       "level (schema bytes pinned in conformance/README.md). "
                       "V4 unsupported-version begins only when FHT enters "
                       "schemas/versions.json.")
    INVALID[-1]["result"] = "invalid-as-fhr"
    fht_invalid_record("fht-fasta-schema-raw-tag-unknown",
                       record_of(schema=RAW_FHT + "v9.9.9/fht.json"), "V5",
                       "A raw tag URL of the FHT development repository names "
                       "no registered release; the V7 lane admits only the raw-"
                       "main URL, so this value is likewise 'any other value' "
                       "under V5 — read as FHR with the near-miss warning "
                       "(Tools#125), not V4 unsupported-version (FAIR-bioHeaders-"
                       "Specification#221 ruling, 2026-11-13). It carries the "
                       "same record bytes as fht-fasta-schema-w3id-release-"
                       "without-fht and meets the same FHR-invalid outcome; the "
                       "URL matching the FHT schema pattern no longer buys a "
                       "selection result (conformance/README.md pins the checked "
                       "FHR schema bytes).")
    INVALID[-1]["result"] = "invalid-as-fhr"

    # ---- invalid: parent link mismatch (T3) ----------------------------------------
    wrong = swap_first_different(genome_checksum)
    assert wrong != genome_checksum and wrong != minimal_checksum
    mismatched = record_of(derivedFrom=[{"headerType": "FHR", "checksum": wrong,
                                         "relationship": "transcribedFrom"}])
    data_m, _ = assemble(lines_of(mismatched))
    invalid("fht-fasta-parent-mismatched", data_m, "T3",
            "The child's bytes, metadata and self-checksum are all valid, but the "
            "cited parent checksum does not equal the checksum recomputed over the "
            "supplied parents/parent-genome.fhr.fasta (checked-fail): a verifier "
            "must report an invalid link, not treat it as unchecked and not pass "
            "it silently.", "matches",
            parent_links=[{"file": PARENT_LINKS["genome"]["file"],
                           "statedChecksum": wrong, "result": "checked-fail"}])


def fht_lines_valid(name, lines, rules, description, expected=EXPECTED_METADATA,
                    parent_links=None, **options):
    data, value = assemble(lines, **options)
    valid(name, data, rules, description, checksum=value, expected=expected,
          parent_links=parent_links)
    return data, value


# -------------------------------------------------------------- examples ----
# The generator owns these example bytes: three minimal records (JSON, YAML
# and embedded FASTA) and the JSON/YAML mirrors of the two FASTA-only examples
# added by #23. The pre-existing de-novo.fht.* files and the genome-guided /
# annotation-derived FASTA originals keep their reviewed bytes untouched;
# check_fht_fixtures.py proves every mirror parses to exactly the record its
# FASTA header carries.
MIRROR_RECORDS = {
    "genome-guided": {
        "schema": "https://raw.githubusercontent.com/FAIR-bioHeaders/"
                  "FHT-Specification/main/fht.json",
        "schemaVersion": "1.0",
        "transcriptome": "Zea mays B73 leaf drought-response transcriptome "
                         "(synthetic example)",
        "assemblyType": "genome-guided",
        "taxon": {"name": "Zea mays", "uri": "https://identifiers.org/taxonomy:4577"},
        "version": "2.1",
        "metadataAuthor": [{"name": "M. Example", "nameType": "Personal"}],
        "dateCreated": "2026-07-02",
        "assemblySoftware": [
            {"name": "HISAT2", "version": "2.2.3"},
            {"name": "StringTie", "version": "3.0.3",
             "commandLineOption": ["--rf"]},
            {"name": "gffread", "version": "0.12.9"},
        ],
        "sample": [
            {"tissue": "leaf", "tissueIdentifier": "PO:0025034",
             "condition": "well-watered control", "strain": "B73"},
            {"tissue": "leaf", "tissueIdentifier": "PO:0025034",
             "condition": "7 days water withheld", "strain": "B73"},
        ],
        "libraryStrategy": "RNA-Seq",
        "strandedness": "reverse",
        "vitalStats": {"totalTranscripts": 61530, "N50": 2236,
                       "averageTranscriptLength": 1587.4},
        "relatedLink": [
            "https://www.maizegdb.org/genome/assembly/Zm-B73-REFERENCE-NAM-5.0"],
        "documentation": "Reads aligned to Zm-B73-REFERENCE-NAM-5.0; models "
                         "assembled with StringTie and written out with gffread. "
                         "rRNA-depleted total RNA libraries, so no single molecule "
                         "type is claimed. Genome guidance alone is not a "
                         "transcribedFrom parent link. Synthetic example for the "
                         "FHT development contract: names, statistics and sequence "
                         "bytes are invented; taxon and ontology identifiers are "
                         "real.",
        "checksum": "hjf2YDKlF+uTf8bv+aPHgaJKrTk1Q5M92qyE6jmA6tw=",
    },
    "annotation-derived": {
        "schema": "https://raw.githubusercontent.com/FAIR-bioHeaders/"
                  "FHT-Specification/main/fht.json",
        "schemaVersion": "1.0",
        "transcriptome": "Arabidopsis thaliana Araport11 protein-coding "
                         "transcripts (synthetic example)",
        "assemblyType": "annotation-derived",
        "moleculeType": "mRNA",
        "taxon": {"name": "Arabidopsis thaliana",
                  "uri": "https://identifiers.org/taxonomy:3702"},
        "version": "Araport11-extract-1",
        "metadataAuthor": [{"name": "Example Plant Database Curation Team",
                            "nameType": "Organizational"}],
        "dateCreated": "2026-10-01",
        "assemblySoftware": [
            {"name": "gffread", "version": "0.12.9",
             "commandLineOption": ["-w", "transcripts.fa", "-g",
                                   "TAIR10_chr_all.fas"]},
        ],
        "vitalStats": {"totalTranscripts": 48359, "N50": 1911,
                       "averageTranscriptLength": 1622.8},
        "relatedLink": ["https://www.arabidopsis.org/download/"],
        "documentation": "Protein-coding transcripts extracted from the Araport11 "
                         "annotation and the TAIR10 genome with gffread. No new "
                         "reads were assembled. No derivedFrom parent is given "
                         "because no FHR-headed genome file is cited here; a real "
                         "record adds an FHR transcribedFrom parent with its "
                         "checksum when one exists. Synthetic example for the FHT "
                         "development contract: names, statistics and sequence "
                         "bytes are invented; taxon and ontology identifiers are "
                         "real.",
        "reuseConditions": "CC-BY-4.0",
        "checksum": "Y6A5rek39VLFxvqe6dn8D8Diz8h8jVK34rW/ByOV0Tk=",
    },
}
EXAMPLE_MINIMALS = {
    "minimal-de-novo": {
        "transcriptome": "Bombus impatiens worker brain transcriptome (synthetic "
                         "minimal example)",
        "assemblyType": "de novo",
        "taxon": {"name": "Bombus impatiens",
                  "uri": "https://identifiers.org/taxonomy:132113"},
        "version": "1.0",
        "metadataAuthor": [{"name": "Example Pollinator Genomics Lab",
                            "nameType": "Organizational"}],
        "dateCreated": "2026-09-15",
    },
    "minimal-genome-guided": {
        "transcriptome": "Zea mays B73 leaf drought-response transcriptome "
                         "(synthetic minimal example)",
        "assemblyType": "genome-guided",
        "taxon": {"name": "Zea mays", "uri": "https://identifiers.org/taxonomy:4577"},
        "version": "2.1",
        "metadataAuthor": [{"name": "M. Example", "nameType": "Personal"}],
        "dateCreated": "2026-07-02",
    },
    "minimal-annotation-derived": {
        "transcriptome": "Arabidopsis thaliana Araport11 protein-coding transcripts "
                         "(synthetic minimal example)",
        "assemblyType": "annotation-derived",
        "taxon": {"name": "Arabidopsis thaliana",
                  "uri": "https://identifiers.org/taxonomy:3702"},
        "version": "Araport11-extract-1",
        "metadataAuthor": [{"name": "Example Plant Database Curation Team",
                            "nameType": "Organizational"}],
        "dateCreated": "2026-10-01",
    },
}
EXAMPLE_FASTA_BODY = [
    b">synthetic_transcript_1",
    b"ATGGCGTCTAAAGGTGAAGAACTGTTCACCGGTGTTGTTCCGATCCTGGTTGAACTGGATGGTGATGTTAACGGTCACAAATTC",
]
# Synthetic provenance note carried by every minimal example (documentation is
# optional, so the minimal records are exactly the nine required fields; the
# note lives in the transcriptome label above and in conformance/README.md).


def example_records():
    records = {}
    for stem, fields in EXAMPLE_MINIMALS.items():
        record = {"schema": RAW_MAIN, "schemaVersion": "1.0"}
        record.update(copy.deepcopy(fields))
        records[stem] = record
    records.update(copy.deepcopy(MIRROR_RECORDS))
    return records


def owned_example_names():
    names = []
    for stem in EXAMPLE_MINIMALS:
        names += [f"{stem}.fht.fasta", f"{stem}.fht.json", f"{stem}.fht.yaml"]
    for stem in MIRROR_RECORDS:
        names += [f"{stem}.fht.json", f"{stem}.fht.yaml"]
    return names


def example_outputs():
    """Return {name: bytes} for every example file owned here (no writing)."""
    outputs = {}
    for stem, record in example_records().items():
        if stem in EXAMPLE_MINIMALS:
            data, value = assemble(header_of(record)
                                   + [Line(text) for text in EXAMPLE_FASTA_BODY])
            record["checksum"] = value
            outputs[f"{stem}.fht.fasta"] = data
        outputs[f"{stem}.fht.json"] = (json.dumps(record, indent=2,
                                                  ensure_ascii=False) + "\n").encode()
        outputs[f"{stem}.fht.yaml"] = ("\n".join(yaml_lines(record)) + "\n").encode()
    return outputs


def build_examples(examples_dir):
    examples_dir.mkdir(parents=True, exist_ok=True)
    outputs = example_outputs()
    for rel, data in sorted(outputs.items()):
        (examples_dir / rel).write_bytes(data)
    return outputs


# --------------------------------------------------------------- manifest ----
def path_for(entry):
    suffix = SUFFIX + (".gz" if entry.get("compression") else "")
    return f"{entry['status']}/{entry['name']}{suffix}"


def manifest():
    vectors = []
    for entry in VALID + INVALID:
        item = {"id": entry["name"], "file": path_for(entry), "format": FORMAT,
                "compressed": bool(entry.get("compression"))}
        if entry.get("compression"):
            item["compression"] = entry["compression"]
        if entry["status"] == "valid":
            item.update(expected="valid", rules=entry["rules"],
                        description=entry["description"],
                        checksum=entry["checksum"], metadata=entry["expected"])
            if entry.get("warnings"):
                item["warnings"] = entry["warnings"]
        else:
            item.update(expected="invalid", rule=entry["rule"],
                        reason=entry["reason"], selfChecksum=entry["self_checksum"])
            if entry.get("metadata") is not None:
                item["metadata"] = entry["metadata"]
            if entry.get("result"):
                item["result"] = entry["result"]
        if entry.get("parent_links"):
            item["parentLink"] = entry["parent_links"]
        vectors.append(item)
    covered = {}
    for item in vectors:
        if item["expected"] == "valid":
            for rule in item["rules"]:
                covered.setdefault(rule, set()).add("valid")
        else:
            covered.setdefault(item["rule"], set()).add("invalid")
    for rule in RULES:
        if rule not in NOT_APPLICABLE:
            assert covered.get(rule) == {"valid", "invalid"}, \
                f"rule {rule} needs valid and invalid coverage: {covered.get(rule)}"
    for rule in covered:
        assert rule in RULES, f"vector cites unknown rule {rule}"
    return {
        "manifestVersion": MANIFEST_VERSION,
        "status": "Development vectors for the FHT 1.0 contract "
                  "(FHT-Specification#8). No FHT schema is released and no "
                  "installed toolkit reads FHT yet: every expected outcome is "
                  "derived from the rule text, never from an implementation "
                  "under test.",
        "specification": "https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-"
                         "Specification/blob/main/docs/FORMAT.md (rules R1-R15)",
        "schemaVersionsSpecification": "https://github.com/FAIR-bioHeaders/"
                                       "FAIR-bioHeaders-Specification/blob/main/"
                                       "docs/SCHEMA-VERSIONS.md (rules V1, V5, V7)",
        "fhtContract": "fht.json — the generated FHT 1.0 development schema "
                       "(specs/005-rna-transcriptome-header/spec.md)",
        "fhtRuleText": "conformance/README.md (T1-T3 are provisional ids)",
        "checksumDefinition": "base64(SHA-512/256) over the (decompressed) file "
                              "bytes except the root-level checksum line and its "
                              "terminator (docs/FORMAT.md R1-R5); written by "
                              "scripts/make_fht_fixtures.py and cross-checked by "
                              "scripts/check_fht_fixtures.py",
        "generator": "scripts/make_fht_fixtures.py",
        "rules": {rule: {"summary": text, **({"notApplicable": NOT_APPLICABLE[rule]}
                                             if rule in NOT_APPLICABLE else {})}
                  for rule, text in RULES.items()},
        "vectors": vectors,
        "retired": [],
    }


def self_check():
    names = set()
    for entry in VALID + INVALID:
        assert entry["name"] not in names, entry["name"]
        names.add(entry["name"])
    for entry in VALID:
        data = decompress(entry["data"]) if entry.get("compression") else entry["data"]
        stated, computed = reference_checksum(data)
        assert stated == computed == entry["checksum"], entry["name"]
    for entry in INVALID:
        if entry["self_checksum"] == "matches":
            stated, computed = reference_checksum(entry["data"])
            assert stated == computed, entry["name"]
        elif entry["self_checksum"] == "broken":
            stated, computed = reference_checksum(entry["data"])
            assert stated != computed, entry["name"]
        else:
            assert entry["self_checksum"] == "unreachable", entry["name"]
            try:
                reference_checksum(entry["data"])
            except ValueError:
                continue
            raise AssertionError(f"{entry['name']}: claimed unreachable, but the "
                                 f"root checksum line is comparable")


def produce():
    """Build everything in memory; return {conformance-relative path: bytes}
    plus the owned examples mapping."""
    PARENT_LINKS.clear()
    VALID.clear()
    INVALID.clear()
    parent_data = build_parent_fixture()
    build_vectors()
    self_check()
    outputs = {}
    for entry in VALID + INVALID:
        outputs[path_for(entry)] = entry["data"]
    outputs["parents/parent-genome.fhr.fasta"] = parent_data
    outputs["manifest.json"] = (json.dumps(manifest(), indent=2, ensure_ascii=True)
                                + "\n").encode("ascii")
    return outputs


def write(conformance_dir, examples_dir):
    outputs = produce()
    for status in ("valid", "invalid", "parents"):
        directory = conformance_dir / status
        directory.mkdir(parents=True, exist_ok=True)
        for stale in directory.glob("*"):
            if stale.is_file():
                stale.unlink()
    for rel, data in sorted(outputs.items()):
        path = conformance_dir / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    example_outputs = build_examples(examples_dir)
    return outputs, example_outputs


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--conformance", type=Path, default=DEFAULT_CONFORMANCE,
                        help="directory to write (default: conformance/)")
    parser.add_argument("--examples", type=Path, default=DEFAULT_EXAMPLES,
                        help="examples directory for owned files (default: examples/)")
    args = parser.parse_args(argv)
    if "sha512_256" not in hashlib.algorithms_available:
        print("SHA-512/256 is unavailable in this Python build", file=sys.stderr)
        return 1
    outputs, example_outputs = write(args.conformance, args.examples)
    print(f"Wrote {len(VALID)} valid and {len(INVALID)} invalid vectors, "
          f"1 parent fixture and {len(example_outputs)} example files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
