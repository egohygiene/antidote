# Local-first software source record

## Verified metadata

| Field | Value |
| --- | --- |
| Title | Local-First Software: You Own Your Data, in Spite of the Cloud |
| Authors | Martin Kleppmann; Adam Wiggins; Peter van Hardenberg; Mark McGranaghan |
| Venue | Onward! 2019 |
| DOI | 10.1145/3359591.3359737 |
| Version reviewed | Published conference paper, 2019 |
| Primary source | https://doi.org/10.1145/3359591.3359737 |
| Source type | Peer-reviewed systems paper and design argument |
| Reviewed | 2026-09-05 |

## Source claims assessed

- The paper proposes local-first software principles intended to combine local
  availability and user ownership with optional collaboration.
- It treats servers as supporting infrastructure rather than the sole
  authoritative home of a person's data.
- The authors discuss offline operation, longevity, privacy, and control as
  design goals and examine CRDT-backed prototypes as one enabling direction.

## Limitations and unresolved questions

- Local-first is a design approach, not a security certification or a complete
  implementation recipe.
- The paper does not address Antidote's consent semantics, sensitive payloads,
  model workers, deletion requirements, or research protocol.
- Device compromise, backup, synchronization, encryption, and key recovery
  remain separate risks.

## Allowed manuscript use

Use as peer-reviewed architecture rationale for keeping Antidote's source of
truth locally available and under person-controlled authority.

## Prohibited manuscript use

Do not claim that local execution alone proves privacy, ownership, regulatory
compliance, secure deletion, resilience, or participant safety.
