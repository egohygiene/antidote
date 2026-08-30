# Antidote site adapter

This directory contains only Antidote-owned inputs and the bounded consumer
adapter for Holon's exact-pinned public site suite. LaunchKit, Zensical, React,
Vite, and the site composer remain owned by Holon and are materialized into a
temporary clean-room directory during the Pages build.

The committed content contract is
`publication/antidote-site.content.json`. The immutable framework boundary is
`publication/antidote-site-suite.lock.json`. Antidote owns the paper,
publication manifests, route catalog, checksums, visual inputs, and final
composition.

Build the complete site through the project-owned interfaces:

```bash
make check-site HOLON_SOURCE="../holon"
task check-site HOLON_SOURCE="../holon"
```

The Holon checkout must be exactly the commit recorded by the lock. The build
does not fetch a moving branch, vendor Holon source, or permit the materialized
profiles to rewrite Antidote source.
