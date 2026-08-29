# Source governance

The source corpus separates discovery, bibliographic identity, full-text
assessment, promotion, and actual manuscript use. The machine-readable status
view is [`catalog.json`](catalog.json); narrative assessments live beside it.
The issue #33 architecture scout also maintains a machine-readable
[`architecture-evidence-map.json`](architecture-evidence-map.json), which maps
accepted sources to one subsystem, an evidence role, a bounded claim, and an
explicit non-claim.

## Source states

| State | Meaning | Bibliography | Source record | Manuscript claim use |
| --- | --- | --- | --- | --- |
| `discovered` | Preserved from a search or reading path; identity or content may still need verification | No | No | No |
| `metadata-verified` | Title, authors, year, venue, and persistent identifier were checked against a primary record | Allowed | Optional | No |
| `full-text-reviewed` | The identified version was read and its findings and limitations were assessed | Allowed | Draft required before promotion | No |
| `promoted` | A governed record defines exact version, claims, limitations, conflicts, and allowed use | Required | Required | Allowed within the recorded boundary |
| `cited` | A promoted source is used by the current canonical manuscript | Required | Required | Yes, only for the linked use |
| `background-only` | Useful context, standard, product documentation, or implementation material that is not scientific claim evidence | Optional | Optional | Context only |
| `superseded` | A version or record has been replaced by a named later authority | Historical only | Required | No |
| `rejected` | Excluded after review, with a documented reason | No | Required | No |

States are current dispositions, not evidence grades. A preprint can be
full-text reviewed but still weak evidence for an efficacy claim; a normative
standard can be authoritative for a data model while irrelevant to affective
outcomes.

## Promotion contract

Every `promoted` or `cited` source must have exactly one bibliography key and
one primary-source record. The record must identify:

- exact publication or preprint version reviewed;
- primary persistent identifier and canonical source;
- source type and peer-review status;
- findings Antidote may rely on;
- limitations, conflicts, and unresolved questions;
- allowed and prohibited manuscript uses.

A source record is not an endorsement and does not turn reported findings into
independently established facts. Secondary summaries may help discovery, but
they never substitute for an available primary record.

## Architecture evidence contract

The architecture map distinguishes scientific precedent, normative standards,
engineering patterns, emerging systems, speculative transfers, and qualifying
evidence. Every mapped source must exist in the catalog, use one required
research cluster, identify its Antidote subsystem, and state both what it may
support and what it does not establish. Architecture precedent never becomes
clinical evidence by proximity.

## Bibliography shelf versus citations

`paper/references.bib` may contain verified, intentionally uncited shelf
entries. That is expected. The source checks fail when a manuscript citation is
unresolved or a promoted/cited source lacks coverage; they do not fail merely
because a verified shelf entry is not cited.
