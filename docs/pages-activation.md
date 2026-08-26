# GitHub Pages and DNS activation

The repository workflow is intentionally safe before activation:

- every pull request and matching `main` push builds and validates `_site/`;
- the reviewable artifact is uploaded to the workflow run;
- the deploy job is skipped unless `PAGES_ENABLED` is exactly `true`.

## Activate the default Pages route

1. Merge the Antidote publishing setup after its checks pass.
2. Open repository **Settings > Pages**.
3. Under **Build and deployment**, select **GitHub Actions** as the source.
4. Open **Settings > Secrets and variables > Actions > Variables**.
5. Create `PAGES_ENABLED` with the value `true`.
6. Open the **GitHub Pages** workflow and run it manually once.
7. Verify the landing page, `/paper/`, `/antidote.pdf`,
   `/publication.json`, and `/SHA256SUMS` routes.

The default canonical base in `beacon-project.toml` is
`https://egohygiene.github.io/antidote/`.

## Add an optional custom subdomain

1. Choose the final subdomain. For example, `antidote.egohygiene.io`.
2. At the DNS provider, create a CNAME from that subdomain to
   `egohygiene.github.io`.
3. In **Settings > Pages**, enter the same custom domain and wait for GitHub's
   DNS check and certificate provisioning.
4. Create or update the Actions variable `PAGES_CUSTOM_DOMAIN` with only the
   hostname, without `https://` or a path.
5. Run the **GitHub Pages** workflow and verify that `publication.json` uses the
   custom HTTPS base.
6. Enable **Enforce HTTPS** after GitHub reports the certificate ready.

GitHub ignores repository `CNAME` files for custom Actions workflows, so this
project does not generate one. The authoritative custom-domain setting lives in
the repository's Pages settings; the variable keeps Antidote's generated
publication metadata synchronized with it.

## References

- [Configuring a publishing source](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)
- [Using custom Pages workflows](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)
- [Managing a custom domain](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site)
- [Troubleshooting custom domains](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/troubleshooting-custom-domains-and-github-pages)
- [Securing a Pages site with HTTPS](https://docs.github.com/en/pages/getting-started-with-github-pages/securing-your-github-pages-site-with-https)
