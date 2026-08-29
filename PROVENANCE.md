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

## Architecture-corpus and repository-support provenance

The 2026-08-27 Antidote architecture corpus uses the 18-document shape defined
by the Ego Hygiene/Aether architecture-document convention. The canonical
organization corpus in `egohygiene/hygiene` supplied the dependency graph,
frontmatter vocabulary, evidence labels, and bounded-document responsibilities.
Reflector supplied a repository-local reference for adapting that graph to a
research and publication project.

Antidote owns the resulting purpose, terminology, human assumptions, scientific
boundaries, runtime structure, design language, decisions, and roadmap. No
Reflector manuscript prose, recursive-development ontology, CLI implementation,
DOI, publication identity, version history, or runtime source was copied.
Same-named architecture files remain separate bounded contexts.

The contribution, security, support, code-of-conduct, getting-started, and
architecture-overview files reuse Reflector's repository-support patterns after
specialization for Antidote's personal-context, model-worker, and scientific
safety boundaries. Reusable publication implementation remains owned upstream
by Beacon as described above.

The MVP directory tree and JSON Schemas are new Antidote-owned contract
scaffolds derived from the research architecture review. They do not claim that
the desktop application, Rust crates, model worker, model adapter, or study
exists.

## Scientific visual provenance

The issue #45 visual manifest, caption registry projection, source
specifications, lifecycle model, validator, and table/figure macros are original
Antidote-owned publication infrastructure. They were informed by Reflector's
standard of reviewable publication evidence but do not copy Reflector branding,
artwork, caption text, manuscript content, or visual identity.

The active semantic-acoustic-response SVG is repository-authored provisional
structure. It contains no third-party image asset and is visibly marked as not
final artwork. Future exact diagrams must remain reproducible from governed
vector or structured-data source. Future generated editorial artwork must
record model/prompt provenance, output identity, reuse terms, disclosure, and
human label verification before activation.
