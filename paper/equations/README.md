# Governed equation system

`registry.json` is the canonical machine-readable index for the mathematical
model introduced by issue #39. It fixes each equation's stable identity,
LaTeX label, epistemic class, implementation state, plain-language meaning,
and prohibited inference. It also owns the centralized symbol glossary.

Generate the two appendix projections after changing the registry:

```sh
python3 scripts/generate_equation_appendix.py --write
```

Validate the registry, System Design labels, visible classification lines, and
generated projections with:

```sh
python3 scripts/generate_equation_appendix.py
```

Changing an equation requires one reviewable change that updates the System
Design source, this registry, both generated appendix projections, and any
affected visual specification. A formula's presence does not promote it from
its declared evidence or implementation state.
