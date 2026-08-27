# Standards baseline

Verified 2026-08-26. These sources define behavior and review expectations; no
source code or sample prose was copied from them.

- [arXiv: Submit TeX/LaTeX](https://info.arxiv.org/help/submit_tex.html) - arXiv
  compiles from the submission root, requires needed style and figure files,
  accepts PDF figures for PDFLaTeX, does not convert figures during processing,
  supports BibTeX, and can consume a matching generated `.bbl`. It also advises
  against `\today`, hidden files, JavaScript, and extraneous build products.
- [Pandoc User's Guide](https://pandoc.org/MANUAL.html) - informs the standalone
  HTML, table of contents, section wrappers, citation processing, and MathML
  projection.
- [CRediT](https://credit.niso.org/) - supplies the optional standardized
  contributor-role vocabulary. Roles describe contributions; they do not decide
  authorship.
- [ORCID registry search guidance](https://info.orcid.org/documentation/api-tutorials/api-tutorial-searching-the-orcid-registry/)
  - supports the rule that Beacon never guesses or assigns an ORCID identifier.
  A project records one only when the author supplies or authenticates it.
- [Reproducible Builds: SOURCE_DATE_EPOCH](https://reproducible-builds.org/docs/source-date-epoch/)
  - supplies the build-time convention used for deterministic artifact checks.

arXiv's submission system and TeX Live versions change over time. Re-verify the
official guidance before a public submission and visually inspect the server's
generated PDF.

## Architecture and prototype baseline

Verified during the 2026-08-27 architecture scout. Research papers support
rationale; standards define interoperable records; framework documentation
supports implementation choices only.

- [Local-First Software](https://doi.org/10.1145/3359591.3359737) - informs
  local ownership, offline operation, longevity, and the rule that optional
  servers support rather than replace the local source of truth.
- [Just-in-Time Adaptive Interventions](https://doi.org/10.1007/s12160-016-9830-8)
  - supplies decision points, intervention options, tailoring variables,
  proximal outcomes, and decision rules for moment-specific adaptation.
- [The Micro-Randomized Trial for Developing Digital Interventions](https://arxiv.org/abs/2107.03544)
  and [StudyU](https://doi.org/10.2196/35884) - inform future bounded adaptation
  studies and digital N-of-1 separation; neither validates Antidote's efficacy.
- [Cognitive Architectures for Language Agents](https://arxiv.org/abs/2309.02427),
  [MemGPT](https://arxiv.org/abs/2310.08560), and
  [Mem0](https://arxiv.org/abs/2504.19413) - provide comparators for modular,
  bounded, and derived memory. Antidote additionally preserves approved source
  records beside replaceable projections.
- [W3C PROV-DM](https://www.w3.org/TR/prov-dm/) and
  [Workflow Run RO-Crate](https://doi.org/10.1371/journal.pone.0309210) - inform
  internal lineage and privacy-reviewed shareable experiment packages.
- [Model Cards](https://doi.org/10.1145/3287560.3287596) - informs adapter and
  model reporting of intended use, limitations, versions, and evaluations.
- [ACE-Step 1.5](https://arxiv.org/abs/2602.00744) and
  [MusicGen](https://arxiv.org/abs/2306.05284) - leading generation candidates
  for technical evaluation. No adapter or weight dependency is selected.
- [Tauri 2](https://v2.tauri.app/), [SQLite](https://www.sqlite.org/),
  [Web Audio](https://www.w3.org/TR/webaudio-1.1/), and
  [Safetensors](https://huggingface.co/docs/safetensors/index) - implementation
  references, not scientific evidence.

The broader architecture source atlas remains a working research record until
individual entries are verified and promoted into the canonical bibliography.
