# Continuous integration and local checks

Status: CI lanes for issue #14 (PR checks for the draft schema, examples and
documentation). Every check below also runs locally with the commands given
here. None of these lanes claims that the legacy draft implements the current
family contract, and CI setup does not amend any schema.

## Lanes

| Workflow | Trigger | Covers |
| --- | --- | --- |
| [`validate-specification.yml`](../.github/workflows/validate-specification.yml) | push/PR | The **current FHT 1.0 development contract**: unit tests over the generated `fht.json` (positive/rejection fixtures in `tests/test_fht_schema.py`, synthetic examples in `examples/`), LinkML regeneration drift and the pinned shared-import provenance. Pre-existing; unchanged by #14. |
| [`docs-checks.yml`](../.github/workflows/docs-checks.yml) | push/PR | Owned documentation signals: Markdownlint with the reviewed local config `.markdownlint-cli2.jsonc` (pinned `markdownlint-cli2@0.24.0`, rule set 0.42.0), plus `scripts/check_docs.py` for local relative links/anchors, whitespace (trailing spaces, CR bytes, final newline) and git conflict markers. Fails the job only on real findings; no network access. |
| [`legacy-draft-checks.yml`](../.github/workflows/legacy-draft-checks.yml) | push/PR | Schema health of the preserved legacy draft `legacy/fht-v0.1.json` (`scripts/check_legacy_schema.py`) and the classified example/fixture suite (`scripts/check_legacy_examples.py`). |
| [`external-links.yml`](../.github/workflows/external-links.yml) | schedule (Mondays) + `workflow_dispatch` | Every http(s) URL cited by repository Markdown, one retry each. Never a PR signal: transient remote failures must not gate unrelated work. |

Both PR lanes run every step (`continue-on-error` steps plus an
`if: always()` summary-and-gate step), so one run reports all findings and
each workflow exposes exactly one required-check-friendly status. All
workflows run with `permissions: contents: read`, `persist-credentials:
false`, pinned action commits (checkout v7, setup-python v7, setup-node v7)
and a job `timeout-minutes`.

## Later stage — adopted-contract conformance (NOT implemented here)

Shared-core generation/drift against the publication copy, version-registry
coordination and byte-exact RNA/cDNA/header conformance with the installed
toolkit are a clearly-labeled later stage gated on issue **#8** (byte-backed
positive/rejected conformance fixtures and exact checksums) and issue **#9**
(installed toolkit support and round trips). See
[`../specs/005-rna-transcriptome-header/spec.md`](../specs/005-rna-transcriptome-header/spec.md)
and [`FHT-MIGRATION.md`](FHT-MIGRATION.md). Until those land, the synthetic
`examples/` remain labeled synthetic and no checksum or SeqCol value is
computed or asserted beyond what `tests/test_examples.py` already verifies
against the file's own bytes.

## Pinned tools (PR lanes)

| Tool | Pin | Where |
| --- | --- | --- |
| Python | 3.13 (CI image) | all workflows |
| jsonschema | `4.26.0` (`jsonschema[format]`) | legacy-draft lane; also inside the `>=4.21,<5` range of `requirements-validation.txt` |
| PyYAML | `6.0.3` | legacy-draft lane |
| markdownlint-cli2 | `0.24.0` (markdownlint 0.42.1 rule set) | docs lane via `npx -y`, Node 22 |
| actions/checkout | `3d3c42e5…` v7 | all workflows |
| actions/setup-python | `5fda3b95…` v7 | all workflows |
| actions/setup-node | `949feb24…` v7 | docs lane |

Local setup used for authoring and reproducible in CI:

```sh
python3 -m venv /tmp/fht14venv
/tmp/fht14venv/bin/pip install "jsonschema[format]==4.26.0" "PyYAML==6.0.3"
```

## Running everything locally

From the repository root:

```sh
# Documentation lane (standard library only)
python scripts/check_docs.py
npx -y markdownlint-cli2@0.24.0

# Legacy draft lane (pinned jsonschema/PyYAML)
python scripts/check_legacy_schema.py
python scripts/check_legacy_examples.py

# Current contract lane (pre-existing; needs requirements-linkml.txt)
python -m unittest discover -s tests -v   # includes tests/test_ci_checks.py

# Scheduled lane only — never part of a PR signal (network required)
python scripts/check_external_links.py
```

## Schema health of the legacy draft

`scripts/check_legacy_schema.py` parses `legacy/fht-v0.1.json`, detects the
**declared dialect** `https://json-schema.org/draft/2020-12/schema` via
`jsonschema.validators.validator_for` (matching validator
`Draft202012Validator`), meta-validates it and **enables format checking
explicitly** with `FormatChecker()` from `jsonschema[format]`. A paired probe
shows a `date`-format violation is rejected only with the checker attached —
the legacy contract's `format: date`/`format: uri` annotations are inert
otherwise. The file's SHA-256
(`34eec2e5…894aa`, also recorded in `legacy/README.md`) is pinned, so the
historical bytes cannot drift without an explicit, reviewed change.

The check prints a **defect registry** — documented, not silently patched:

| id | Measured current behavior of the legacy draft |
| --- | --- |
| L1 | `taxon.uri` pattern is unanchored with unescaped dots: leading/trailing junk and `identifiersXorg` match |
| L2 | ORCID pattern has no end anchor and unescaped dots: trailing junk after a valid iD passes |
| L3 | `scholarlyArticle` `^10.` accepts e.g. `10X` |
| L4 | `identifier` item pattern is unanchored |
| L5 | Only the top level closes `additionalProperties`; nested objects accept unknown keys (the historical `url`-instead-of-`uri` typo passes) |
| L6 | No nested `required`: empty author objects and a nameless taxon validate |
| L7 | `masking` is required but its alternation is unanchored (`who knows? unknown` passes) |
| L8 | `checksum` (`definitions.sha2`) constrains only 44 base64-charset characters; no algorithm or byte coverage — real coverage is FORMAT.md/#8 territory |
| L9 | `schemaVersion` is typed `number`; the current draft's string `"1.0"` is rejected — recorded incompatibility, preserved as-is |
| L10 | `date`/`uri` formats are enforced only because the validator enables `FormatChecker` explicitly |
| L11 | The legacy `$id` is the raw-main `fht.json` URL, which today serves the FHT 1.0 draft — cite the archived path/tag for audit |

Each registry entry is a live probe: if a probe's measured behavior changes,
CI fails and the change must be reviewed — CI never edits the contract.

## Example validation and classification

Supported example formats are parsed safely (`json.loads`, `yaml.safe_load`;
FASTA via its `;~` block). The current-contract examples in `examples/` are
validated by `tests/test_examples.py` (pre-existing lane). For the legacy
lane:

- **Positive fixtures** — `tests/fixtures/legacy/valid/full-legacy-record.json`
  must validate against `legacy/fht-v0.1.json` with zero errors (its
  checksum/ORCID/DOI strings are synthetic placeholders following
  `tests/test_fht_schema.py`'s `"A"*43+"="` convention — never real digests).
- **Rejection fixtures** — `tests/fixtures/legacy/rejected/*.json` with
  measured expectations in `expected.json`: missing required fields, unknown
  top-level properties, wrong scalar types (`schemaVersion` string,
  `transcriptome` number), `masking`/`checksum` pattern violations, a
  non-date `dateCreated` and a malformed `relatedLink` URI. Matching is
  exact per path: new errors, disappearing errors and repairs all fail.
  Regenerate with `python scripts/make_legacy_fixtures.py`.
- **Historical samples** — `legacy/examples/` are byte-pinned review inputs,
  classified in `tests/fixtures/legacy/classification.json` (tracked reasons,
  linked to this issue and `legacy/README.md`):

| file | classification | measured |
| --- | --- | --- |
| `example.fht.json` | nonconforming-historical | 4 schema errors: top-level `$schema`/`$id`/`assemblySoftware`/`reuseConditions` unknown; `md5:` checksum too short + bad charset; `soft-masked` fails the masking pattern. Notes: taxon URI is *Homo sapiens* (9606) for "Bombas huntii", `schema` URL truncated (`FHT.jso`), author `url` typo silently accepted (L5). |
| `example.fht.yaml` | nonconforming-historical | 4 schema errors: same field-level defects without `$schema`/`$id`; `schemaVersion: 1` is a legacy-valid number. |
| `example.fht.fasta` | unparseable-historical | `;~` block fails YAML parsing (`expected <block end>`): misindented author list items. Would still carry the value defects. |
| `example.microdata.fhr.html` | not-json-or-yaml-historical | HTML presentation artifact (retired converter era); outside the JSON/YAML lane, kept verbatim. |

A repaired, newly-broken or edited historical file fails
`scripts/check_legacy_examples.py` (digest pins + exact error matching); the
correct response is a reviewed re-classification, never a silent in-place fix.

## External links

`scripts/check_external_links.py` collects every http(s) URL cited **as a
Markdown link or angle autolink** (URLs that appear only as inline code, e.g.
dialect identifiers or version templates, are not fetch targets), fetches
each (GET, 30 s timeout, one retry after 5 s, descriptive User-Agent) and
fails on any non-2xx/3xx answer. It runs only on the weekly schedule and on
manual dispatch; the PR lanes never touch the network, so a transient remote
failure cannot be the sole PR signal.

### Exclusions

Exclusions live in `scripts/external-links-exclusions.json`. Policy: narrow
(exact URL or explicit prefix), dated, and justified by recorded evidence of
a durable failure or a bot-hostile endpoint; transient failures are retried,
not excluded; adding an entry is a reviewed maintainer change. **Baseline
(2026-11-10): all 32 linked URLs in repository Markdown answered HTTP 200 in
local runs, so the exclusion list is intentionally empty.**

## Reviewer notes

- No schema bytes (`fht.json`, `fht_linkml.yml`, `legacy/*`), examples or
  historical URLs/checksums were changed by this CI work; the only edited
  prose is one re-wrap in `specs/005-rna-transcriptome-header/spec.md` (a
  line beginning `#9` read as an ATX heading), `README.md` (pointer to this
  file) and new files.
- Markdownlint deviations from the default rule set are limited to MD013 and
  MD060, each with a recorded reason in `.markdownlint-cli2.jsonc`.
