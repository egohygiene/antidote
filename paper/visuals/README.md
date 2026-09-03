# Scientific visual system

The visual manifest at [`manifest.json`](manifest.json) is the source of truth
for every Antidote figure and table. It allocates stable IDs, manuscript
placement, labels, dimensions, lifecycle state, source mode, caption, alt text,
long description, provenance, licensing, claim-ledger links, and reuse policy.

The system has four governed layers:

1. `manifest.json` owns inventory and scientific meaning.
2. `captions.tex` is the deterministic LaTeX projection consumed by the PDF.
3. `specs/` records the required content and failure boundaries for each visual.
4. `paper/figures/` and `paper/tables/` contain active source assets only.

Run the validator directly when editing the inventory:

```sh
python3 scripts/generate_skeleton_visuals.py
python3 scripts/check_visuals.py
```

During the issue #77 skeleton phase, every planned visual is active in its
intended location. `scripts/generate_skeleton_visuals.py --write` creates the
visibly provisional, data-free frames; the default check and visual validator
reject drift. `ANT-FIG-001` remains a separately authored provisional diagram,
and `ANT-TBL-002` remains the existing literature-derived draft. Issue #46 owns
replacement of all provisional frames with reviewed final assets.

After changing caption, alt, description, or state text in the manifest, refresh
and verify the committed LaTeX registry:

```sh
python3 scripts/check_visuals.py --write-registry
```

`make check-all` and `task check-site HOLON_SOURCE=../holon` also validate the
complete system.

## Lifecycle

`state` describes production maturity:

- `planned`: allocated but no active manuscript asset;
- `placeholder`: structurally useful, visibly provisional artwork;
- `draft`: complete enough for scientific review but not approved as final;
- `final`: approved labels, evidence, accessibility, provenance, and rendering.

`status` describes publication participation:

- `inactive`: allocated and unreferenced;
- `active`: referenced exactly once by the canonical manuscript;
- `retired`: preserved for provenance but unavailable to the manuscript.

An active placeholder must declare its state in SVG metadata and visibly say it
is provisional. Submission-ready and published builds reject every active state
other than `final`. Planned visuals may not be referenced, and active visuals
may not be missing or unreferenced.

## Exact and generated media

Claim-bearing architecture diagrams use structured SVG with fixed dimensions,
stable text labels, and a deterministic SVG-to-PDF conversion. Scientific
tables use LaTeX, with CSV, TSV, or JSON retained beside them when data drives
the rows. The final visual must be reproducible from reviewed repository source.

Image generation is reserved for editorial or conceptual artwork. Generated
complex artwork may remain a high-resolution PNG, but it requires a prompt
record under `prompts/` with the model and version, prompt, seed or equivalent
settings when available, output hash, license/terms review, disclosure, and
human verification of every visible label. Generated media cannot carry exact
architecture, data, or unsupported scientific claims.

## Design and accessibility contract

- Captions live outside image pixels in the generated LaTeX registry.
- Alt text states the visual's essential takeaway; it does not repeat the
  caption. The long description explains topology, encodings, and caveats.
- Normal text targets at least 4.5:1 contrast; large text and meaningful graphic
  boundaries target at least 3:1. Color never carries state by itself.
- Exact figures use redundant labels, shapes, line styles, or patterns and must
  remain legible in grayscale and common color-vision-deficiency simulations.
- Final vector labels target at least 9 pt at a 6.5 inch print width. Lines target
  at least 0.5 pt. Raster editorial assets target at least 300 pixels per inch at
  their intended print size.
- Figures must survive US Letter PDF, responsive accessible HTML, 100 percent
  grayscale printing, and browser zoom without clipping, overlap, or hidden
  meaning.
- Decorative elements cannot obscure data, authority boundaries, failure
  paths, uncertainty, or evidence status.

## Reuse and authority

PDF and accessible web are canonical projections from this repository. A later
magazine may reuse an approved visual, but it must retain the visual ID, state,
caption/description meaning, provenance, license, and claim boundary. The
magazine is never authoritative and may not strengthen or editorialize a
scientific claim.
