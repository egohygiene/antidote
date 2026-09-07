# Paper preview and revision verification

The writing loop has one implementation and two equivalent contributor
interfaces. Both `make` and `task` dispatch to `scripts/tasks.py`; neither calls
Beacon or maintains a parallel manuscript.

## Fast local loop

Edit one numbered file under `paper/sections/`, then run either:

```sh
make preview HOLON_SOURCE=../holon
task preview HOLON_SOURCE=../holon
```

The command builds and validates the PDF, accessible HTML, provenance record,
arXiv source archive, and complete `_site/` projection before serving that
exact tree at <http://127.0.0.1:8000/>. Review the browser paper at
<http://127.0.0.1:8000/paper/> and the PDF at
<http://127.0.0.1:8000/antidote.pdf>. Stop the server with `Ctrl-C`.

Use `PREVIEW_PORT=8080 make preview HOLON_SOURCE=../holon` or
`task preview PREVIEW_PORT=8080 HOLON_SOURCE=../holon` when port 8000 is
occupied. Binding remains
loopback-only unless a contributor deliberately sets `PREVIEW_HOST`.

For the shortest non-serving iteration, use `make build` or `task build` and
open `build/egohygiene/paper.pdf` plus
`build/egohygiene/web/index.html`. Before pushing, run:

```sh
make check-all
task check-site HOLON_SOURCE=../holon
```

Generated artifacts remain under `build/` and `_site/`; do not commit them.
The visible revision canary records the checked-out Git commit. An uncommitted
edit changes artifact hashes but continues to identify `HEAD`, so commit the
canary before comparing it with CI or a deployed site.

## Pull-request review

Pull requests never deploy. The **Research paper** workflow publishes one
`antidote-paper-<theme>-<sha>` artifact for each theme, and the **GitHub Pages**
workflow publishes `antidote-pages-<sha>`. Reviewers can inspect the PDF,
accessible HTML, provenance, arXiv source, full `_site/`, and SHA-256 inventory
for the exact pull-request commit.

CI invokes both Make and Task. It compares the governed PDF, HTML, provenance,
and arXiv outputs byte-for-byte for both themes, then compares the complete
Pages trees byte-for-byte. The wrappers therefore prove equivalence without
introducing a second build implementation.

## Merged canary

After the change reaches `main` and the **GitHub Pages** deploy job succeeds,
check the custom domain from that exact merged checkout:

```sh
git switch main
git pull --ff-only
make live-check
```

To verify a workflow SHA without changing the checkout, run:

```sh
python3 scripts/verify_live_publication.py \
  --base-url=https://antidote.egohygiene.io/ \
  --expected-revision=<full-40-character-merge-sha>
```

The checker requests every stable route with an immutable cache-busting query,
requires the HTML revision canary to match, confirms that `site.json`,
`publication.json`, `provenance.json`, and `site-suite.provenance.json`
identify the same revision, verifies the accepted Holon pin, and
recomputes the advertised hashes for the web paper, PDF, provenance, and arXiv
source. The deploy job runs this same checker; a route that merely returns 200
is not sufficient.

The issue #48 baseline check on 2026-09-07 verified merged revision
`f9e23128a660066b3f64c73c4dd2d36554b6040a` at the canonical HTTPS domain,
including route metadata and recomputed paper-HTML and PDF hashes. The exact
command and hashes are retained in
[`paper/reviews/reviewable-preprint-v0.1.0.json`](../paper/reviews/reviewable-preprint-v0.1.0.json).
Every later merge remains unverified until its own deploy job passes against
that merge SHA.

## Browser review record

The issue #48 browser pass opened the canonical paper route at a 1363
CSS-pixel viewport and observed the complete section sequence, nine figures,
alt text for all nine figures, 163 links, and no horizontal overflow. The
candidate `_site/` tree separately passed the deterministic route, fragment,
landmark, figure-description, checksum, and repeated-staging validators.

The launch surface remained readable but logged React production error 418,
indicating that its server markup did not hydrate exactly. The accepted Holon
revision uses `renderToStaticMarkup` for the server tree before `hydrateRoot`;
[React documents that static-markup output cannot be
hydrated](https://react.dev/reference/react-dom/server/renderToStaticMarkup),
and [error 418](https://react.dev/errors/418) identifies the observed mismatch.
This inherited site-shell defect is tracked by issue #89 and must be fixed or
explicitly dispositioned before the combined paper-and-magazine launch. It
does not alter the static paper HTML, PDF, manifest, or hash verification, and
it is recorded as an accepted limitation rather than concealed by the
reviewable-paper gate.

## Troubleshooting

| Symptom | Evidence to inspect | Recovery |
| --- | --- | --- |
| LaTeX fails | First `!` error and file/line in `build/<theme>/paper.log` | Fix the canonical `.tex` source; do not edit copied files under `build/`. Run `make check-content` again. |
| PDF navigation is incomplete | Contents page, viewer bookmarks, section links, and unresolved-reference warnings in `paper.log` | Keep a unique `\label{sec:...}` or `\label{app:...}` immediately after every section heading and let `latexmk` complete all passes. |
| Pandoc fails or browser anchors drift | `build/<theme>/web/index.html`, its table-of-contents links, and duplicate/missing ID errors from `scripts/check.py` | Use supported canonical LaTeX, preserve the explicit labels, and change the shared web transform instead of hand-editing HTML. |
| Local browser route is missing | `_site/site.json`, `_site/SHA256SUMS`, and the terminal that runs `make preview` | Re-run `make check-site HOLON_SOURCE=../holon`; confirm the requested path is in the catalog and no stale server is serving another directory. |
| PR has no review artifact | Workflow path filters and the build job logs | Confirm the change matches a declared paper/Pages path and that artifact upload follows successful validation. PR jobs must not enter `deploy`. |
| Custom domain returns 404 | Repository Pages source, `PAGES_ENABLED`, `PAGES_CUSTOM_DOMAIN`, and the most recent Pages run | Treat the active publication as unavailable; follow rollback or recovery in the activation guide. A successful build job alone does not publish. |
| DNS or TLS fails | Exact `antidote` CNAME, GitHub's domain check, certificate status, and **Enforce HTTPS** | Remove conflicting or wildcard records, retain organization domain verification, and wait for GitHub certificate provisioning before enforcing HTTPS. |
| Live revision is stale | `site.json`, `publication.json`, `provenance.json`, `SHA256SUMS`, and `make live-check` output | Verify the expected merge SHA, wait for the matching deploy job, then retry the cache-busted checker. Do not accept a matching page title or a bare HTTP 200 as proof. |
| PDF and manifest disagree | `publication.json`'s `paper_pdf.sha256`, downloaded `/antidote.pdf`, and `SHA256SUMS` | Treat the deployment as failed; rebuild and deploy the reviewed `_site/` artifact for the same SHA. |
| Launch shell logs React error 418 | Browser console plus the pinned Holon `static-entry.tsx`, `render-static.mjs`, and `main.tsx` | Keep the static paper available, track the defect in #89, and replace non-hydratable server markup or client hydration in Holon before the combined launch. |

If rollback is required, follow the safe ordering in
[`pages-activation.md`](pages-activation.md): disable deployment, revert or
correct the source, inspect the PR artifact, and only then republish.
