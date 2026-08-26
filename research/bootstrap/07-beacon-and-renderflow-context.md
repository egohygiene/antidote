# Beacon and Renderflow Context

`beacon` is the reusable research-project bootstrapper and template library. `renderflow` remains the rendering engine/reference implementation.

```text
Renderflow
    ↓ audit / extract proven conventions
Beacon
    ↓ owns project + template contracts
Research project
    ↓ produces source artifacts
Renderflow / Pandoc / other engines
    ↓ render
PDF / HTML / other outputs
```

Beacon should know what a research project is, which template is selected, required and optional metadata, bibliography/figure locations, evidence/notes/experiment conventions, initialization rules, and template capabilities/versions.

Renderflow should know how documents are rendered, how output engines are invoked, how templates are validated for rendering, and how reproducible artifacts are produced.

Reflector should be treated as a reference implementation / prior research project rather than the canonical template. Longer term it can be harmonized with Beacon after the contracts are proven by this new project.
