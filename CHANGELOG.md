# Development changelog

## Unreleased

- Proposed Q4 follow-up after #50: supplied `assemblyAuthor` items need a
  nonblank `name` (local `AssemblyAuthor`, same rule as `MetadataAuthor`); the
  list stays optional and the shared `Author`, taxon and sample rules are
  unchanged. Rejection-boundary change to the unreleased draft; the 75
  conformance vectors and canonical examples are unchanged. The test-only HTML
  binding is re-anchored to the new schema bytes.

- Narrow #50 to the approved Q4 nonempty metadata values and Q8 extraction
  documentation after #51. Require nonblank transcriptome/version/date and
  nonempty, named metadata authors, without tightening optional assembly authors,
  taxon members or the retained sample array. Withdraw libraryProtocol in favor
  of documentation/relatedLink. This changes unreleased draft rejection boundaries;
  existing 75 conformance vector bytes/outcomes and all external consumer pins
  remain unchanged. Shared publication and first-release adoption remain separate.

- Record Molik's Q1–Q9 draft decisions; add `mixed` as the fifth molecule type,
  keeping the three construction types, sample array and current taxon rules.
  Owning source commit: `fcce5f6173322b337d24c7eea51ff8745d7b32aa`.
- Propose typed FHT HTML with seven readable canonical pairs and a test-only
  writer/extractor validated against the owning draft. Record protocol/kit
  context through existing documentation and relatedLink fields.
- Keep shared publication, runtime support and the separate real-data pilot
  handoffs explicit. These changes publish no contract or package.
