# Migration from Empathy

This repository was extracted from the provisional workspace at
`egohygiene/empathy/research/antidote` under Empathy issue 71.

## Immutable source

| Record | Value |
| --- | --- |
| Source repository | `https://github.com/egohygiene/empathy` |
| Extraction commit | `ad699e9e5405bbc344cacac4347881e0af77ad56` |
| Source tree | `5432bdd881afd191e6bba03eab93ccfc192ee25f` |
| Workspace origin commit | `1bc0513d0c87b3702003228e89977ce751b67e11` |
| Source path | `research/antidote` |
| Inventory | `research/inventory/empathy-source-tree.tsv` |

The source commit and tree retain the complete original bytes and Git history.
`make inventory` additionally verifies every artifact classified as
`preserve-unchanged` against its original Git blob.

## Disposition

- The eight bootstrap notes were preserved byte-for-byte as research evidence.
- `paper.md` was converted into the canonical LaTeX manuscript and remains
  recoverable from the source commit.
- `references.bib` became `paper/references.bib` and was extended with a
  primary-source-verified MindMelody record.
- Empty directory sentinels became scoped README files or a real figure.
- The provisional `template.tex` and `template.html` were not copied. Beacon
  `research-paper` `0.1.0` supersedes them.
- The standalone repository is canonical once its bootstrap pull request
  merges. Empathy must then retain only a historical pointer, never a second
  writable manuscript.
