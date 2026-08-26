# Standalone build-kit provenance

Antidote's local renderer, checks, styles, themes, web template, and shared task
adapter were generated from the original MIT-licensed Beacon `research-paper`
profile at commit `337f2dd7432b432d41483b2655c11a14cf39dfec`.
Antidote owns this product snapshot so native builds do not require Beacon.

No class, style, font, image, sample prose, or bibliography record was copied
from Beacon's staged references. Future upgrades must compare the pinned
profile, review Antidote-specific adaptations, and update
`dependencies/beacon.lock.toml` in the same change.

## Dispositioned staging references

The upstream Beacon implementation reviewed and replaced these staged trees:

- `.staging/templates/research-paper` at tree
  `39ffe268802b65edf5da92d14caf976055ad9a69` - an incomplete internal
  Markdown/Pandoc prototype with no durable project/bootstrap or arXiv contract.
- `.staging/latex/Academic Articles/arsclassica-article` at tree
  `beb9d5cad7750f7fcdc0a1676177793596c36abb` - hierarchy, theorems, figures,
  subfigures, and equations reference; CC BY-NC-SA 3.0.
- `.staging/latex/Academic Articles/journal-article` at tree
  `fdb50bf82b4782187d11e06a6f73788ddf8c0b07` - author, affiliation, abstract,
  running-head, and bibliography reference; CC BY-NC-SA 4.0.
- `.staging/latex/Academic Articles/stylish-article` at tree
  `9483893ba506f81f8c2d09774dec1e1181d9dfe9` - hierarchy, color, abstract, and
  mathematical-layout reference; CC BY-NC-SA 3.0.
- `.staging/latex/Academic Articles/wenneker-article` at tree
  `7be3dbd2319f7d8ef4d95b3cfd84feda3c0d50f9` - author, affiliation, equation,
  table, and figure reference; CC BY-NC-SA 3.0.

The four external packages originated from LaTeXTemplates.com. Their
noncommercial share-alike terms make direct reuse inappropriate for Beacon's
MIT first-party profile. The deleted files remain recoverable from Git history
using the tree IDs above.

Publisher-specific material under `.staging/latex/Academic Journals/` remains
staged. It represents future publisher adapters and is not replaced by this
neutral research-paper profile.
