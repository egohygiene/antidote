# Response and consent v1-to-v2 boundary

Status: prospective compatibility guidance; no automatic migration exists.

Issue #82 adds parallel v2 schemas for the proposed H1 collection boundary
without changing existing v1 event bytes. The desktop application, Rust
session authority, and SQLite replay path continue to read and write v1. A v1
record is therefore MVP evidence only and is not a protocol-qualified H1
record.

## Response mapping

An audit or display adapter may expose an explicitly labeled, nonqualifying
compatibility view of a v1 response. The only deterministic value mappings are:

| v1 value | v2 compatibility value |
| --- | --- |
| `wanted_intensity: true` | `wanted_intensity: "yes"` |
| `wanted_intensity: false` | `wanted_intensity: "no"` |
| A field named in `missing_fields` | One `missingness` entry for that field, inheriting the v1 scalar `missingness_reason` |

No other answer may be inferred. In particular:

- v1 `wanted_intensity: null` with an explicit matching missing field and
  reason remains null with that reason; it is never converted to `"unsure"`;
- v1 null without matching missingness metadata is ambiguous and remains a v1,
  nonqualifying record; it is never coerced to declined, unsure, neutral, zero,
  or not applicable;
- a v1 scalar missingness reason cannot safely describe fields absent from its
  `missing_fields` list;
- omitted description, valence, arousal, or intensity keys inside a v1 state
  object remain ambiguous; v2 requires each child key to be present as a value
  or null, with dotted field-level missingness for every null child;
- v2-only instrument fields, correction revision, supersession, and correction
  reason cannot be reconstructed from v1 bytes; and
- an adapter must preserve the original v1 payload and label any compatibility
  projection as derived and nonqualifying.

A protocol-qualified v2 response must be captured natively under the frozen
instrument. It explicitly carries every instrument field as a value or null,
has exactly one canonical reason for every null field, distinguishes
yes/no/unsure from decline, and records immutable correction lineage.

## Consent mapping

Consent is not upgraded by inference. V1 has no `analyze` or `play` action, so a
v1 grant cannot authorize those v2 actions. H1 activation requires a fresh,
explicit v2 grant that names the relevant purposes, one action, sources, and
retention settings. Multiple actions require distinct grant IDs so they remain
separately revocable. Playback approval remains a separate person action; a
`play` scope does not itself start playback.

No compatibility adapter may enable personal-model updates. A v2 grant and v2
response still require an independent, explicit future authority path before
response evidence could affect a personal model.
