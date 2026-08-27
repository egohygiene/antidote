# GitHub Pages and DNS activation

The repository workflow is intentionally safe before activation:

- every pull request and matching `main` push builds and validates `_site/`;
- the reviewable artifact is uploaded to the workflow run;
- the deploy job is skipped unless `PAGES_ENABLED` is exactly `true`.

## Activate the custom-domain publication hub

1. Merge the Antidote publishing setup after its checks pass.
2. Verify `egohygiene.io` for the GitHub organization under its Pages settings
   before binding a repository or DNS record. GitHub recommends this ordering
   to reduce custom-domain takeover risk.
3. Open repository **Settings > Pages**.
4. Under **Build and deployment**, select **GitHub Actions** as the source.
5. In **Custom domain**, enter `antidote.egohygiene.io` and select **Save**.
6. At the DNS provider, confirm the `antidote` CNAME points to
   `egohygiene.github.io`. Do not use a wildcard record.
7. Wait for GitHub's DNS check and certificate provisioning.
8. Open **Settings > Secrets and variables > Actions > Variables**.
9. Create `PAGES_CUSTOM_DOMAIN` with the exact value
   `antidote.egohygiene.io`.
10. Create `PAGES_ENABLED` with the exact value `true`.
11. Open the **GitHub Pages** workflow and run it manually once, or merge a
   matching change to `main`.
12. Confirm the deploy job verifies `/`, `/paper/`, `/antidote.pdf`,
    `/magazine/`, `/downloads/`, `/publication.json`, `/site.json`,
    `/provenance.json`, and `/SHA256SUMS` against the custom HTTPS domain.
13. Enable **Enforce HTTPS** after GitHub reports the certificate ready.

The canonical base in `beacon-project.toml` is
`https://antidote.egohygiene.io/`. The technical GitHub fallback is
`https://egohygiene.github.io/antidote/`; it is not presented as canonical.

GitHub ignores repository `CNAME` files for custom Actions workflows, so this
project does not generate one. The authoritative custom-domain setting lives in
the repository's Pages settings. The source configuration selects the canonical
domain, and the optional workflow variable must match it instead of silently
overriding publication metadata.

## Roll back safely

For an application-level regression:

1. Set `PAGES_ENABLED` to `false` before merging more publication changes.
2. Revert the offending commit or merge a tested corrective change.
3. Inspect the pull-request Pages artifact and its `site.json` and
   `SHA256SUMS` before restoring `PAGES_ENABLED=true`.
4. Run the workflow from corrected `main` and verify the custom-domain routes.

For an urgent takedown, use **Settings > Pages > Unpublish site** in addition
to disabling the variable. Do not leave an unverified DNS CNAME pointing at
GitHub after the Pages binding is removed: remove the CNAME promptly or retain
organization-level verification while corrective work proceeds. For permanent
custom-domain retirement, remove the Pages binding and DNS CNAME in one
maintenance window. Change `beacon-project.toml` and all canonical metadata to
the fallback URL in a reviewed commit before publishing there.

## References

- [Configuring a publishing source](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)
- [Using custom Pages workflows](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)
- [Managing a custom domain](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site)
- [Verifying a custom domain](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/verifying-your-custom-domain-for-github-pages)
- [Troubleshooting custom domains](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/troubleshooting-custom-domains-and-github-pages)
- [Securing a Pages site with HTTPS](https://docs.github.com/en/pages/getting-started-with-github-pages/securing-your-github-pages-site-with-https)
