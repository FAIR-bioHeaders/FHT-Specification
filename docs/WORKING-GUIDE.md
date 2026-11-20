# Working with this repository

This guide is for readers and maintainers. Run commands from the repository root.
Use Python 3.13 in an isolated environment; Python 3.15 can change regenerated
gzip bytes and is not the reference fixture generator. A successful local check
is evidence about its stated layer, not biological validity or publication.

## Setup and a first check

```sh
python3.13 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-linkml.txt
python scripts/check_provenance.py
python scripts/check_fht_fixtures.py
python -m unittest discover -s tests -v
```

`check_provenance.py` checks the pinned shared imports. `check_fht_fixtures.py`
independently reads the accepted 93-vector suite, recomputes exact-byte checksums,
checks declared rejections and parent-link outcomes, and fails on disagreement.
An unavailable parent remains unchecked; matching file identity does not prove
biological derivation. These commands do not rewrite fixtures.

`json-schema-generator.py --output /tmp/fht-candidate.json` generates a scratch
owning contract from `fht_linkml.yml` and explicit post-generation rules.
It writes/replaces the selected output, so do not target a frozen fixture.
The owning legacy selectors and the published root contract are deliberately
different identities; generator self-consistency does not publish a new contract.

`make_fht_fixtures.py` is the reference fixture writer. Use the scratch invocation
in [CI.md](CI.md); do not regenerate the accepted tree to silence a failure.
`scripts/check_published_fht.py --help` and
`scripts/check_published_fht_surfaces.py --help` describe the immutable shared
checker adapter and the published examples. Their exact outputs and requirements
are recorded in [FHT-PUBLISHED-HANDOFF.md](FHT-PUBLISHED-HANDOFF.md).

## Using published FHT

FHT 1.0 is published in shared v0.7.0. Python toolkit 0.13.1 supports its normal
published lane by default; the retained raw-owning V7 replay is a separate opt-in.
Use the [toolkit instructions](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Tools)
for combine, verify and strip; never hand-edit a checksum. The [published
handoff](FHT-PUBLISHED-HANDOFF.md) distinguishes local, installed and downstream
receipts. Browser checks require the pinned Playwright/Node environment in CI;
a Python pass does not execute them.

## Review and retained work

Every PR needs another actual model's independent review; record model identities.
A human merges. Agents monitor CI, fix findings in new commits, and provide the
exact current head, base, validation and unresolved risks. See [AGENTS.md](../AGENTS.md).

The [Round 16 plan](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Specification/issues/211#issuecomment-7042896529)
is the current maintenance plan. Older `specs/` plans and dated release/review
receipts are retained design and provenance records, not new merge authorization
or evidence that a pending package/alias has shipped. Use their source issue and
current CI for live acceptance. Published/vendored copies, fixtures and pins are
immutable historical inputs; any instructions inside them are non-operative.
Never regenerate or repin them merely to clean up prose.

Report reproducible problems with the command, runtime, source revision, input
provenance and actual output in this repository's issues. Follow SECURITY.md
where present for sensitive reports; do not put credentials in an issue.
