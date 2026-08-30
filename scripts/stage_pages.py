#!/usr/bin/env python3
# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT

"""Stage and validate Antidote's deterministic GitHub Pages artifact."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shutil
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit

import tomllib

ROOT = Path(__file__).resolve().parents[1]
DOMAIN = re.compile(
    r"^(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$"
)
LOCAL_LINK = re.compile(r"(?:href|src)=[\"']([^\"']+)[\"']")
TEMPLATE_TOKEN = re.compile(r"\{\{[A-Z0-9_]+\}\}")
SLOT_STATUSES = {"available", "planned", "superseded", "withdrawn"}
OWNER_FILE = ".antidote-pages-owned"
OWNER_TEXT = "antidote-pages/v1\n"
PLANNED_SLOT_FIELDS = {
    "artifacts",
    "id",
    "label",
    "manifest_path",
    "path",
    "stage",
    "status",
    "type",
}
REQUIRED_ROUTES = {
    "home": "",
    "documentation": "docs/",
    "architecture": "architecture/",
    "legal": "legal/",
    "paper": "paper/",
    "paper-pdf": "antidote.pdf",
    "magazine": "magazine/",
    "downloads": "downloads/",
    "publication-manifest": "publication.json",
    "site-catalog": "site.json",
    "site-suite-evidence": "site-suite.provenance.json",
    "checksums": "SHA256SUMS",
}


def sha256(path: Path) -> str:
    """Return the lowercase SHA-256 digest for one file."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def public_artifact_url(pages_url: str, artifact_id: str, path: str) -> str:
    """Return the stable public URL for a paper artifact path."""
    if artifact_id == "accessible_web":
        return urljoin(pages_url, "paper/")
    return urljoin(pages_url, path)


def load_toml(path: Path) -> dict:
    """Load a UTF-8 TOML document."""
    with path.open("rb") as stream:
        return tomllib.load(stream)


def validate_custom_domain(value: str) -> str:
    """Return a normalized custom domain or reject unsafe input."""
    domain = value.strip().lower().rstrip(".")
    if domain and DOMAIN.fullmatch(domain) is None:
        raise ValueError(f"invalid Pages custom domain: {value}")
    return domain


def copy_required(source: Path, destination: Path) -> None:
    """Copy one required file and fail clearly when it is absent or empty."""
    if not source.is_file() or source.stat().st_size == 0:
        raise FileNotFoundError(f"required publication artifact is missing: {source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def validate_output_target(root: Path, build: Path, output: Path) -> None:
    """Limit replacement to owned, generated Pages directories."""
    try:
        relative = output.relative_to(root)
    except ValueError as error:
        raise ValueError(f"Pages output must remain inside the project: {output}") from error
    if not relative.parts:
        raise ValueError(f"refusing unsafe Pages output directory: {output}")
    generated_root = relative.parts[0]
    if not (
        generated_root == "_site"
        or generated_root.startswith("_site-")
        or generated_root.startswith(".antidote-pages-")
    ):
        raise ValueError(f"refusing non-generated Pages output directory: {output}")
    if output == build or output in build.parents or build in output.parents:
        raise ValueError("Pages output cannot overlap the governed build directory")
    if not output.exists():
        return
    if not output.is_dir():
        raise ValueError(f"Pages output exists but is not a directory: {output}")
    owner = output / OWNER_FILE
    if owner.is_file() and owner.read_text(encoding="utf-8") == OWNER_TEXT:
        return
    legacy_site = (
        generated_root == "_site"
        and (output / ".nojekyll").is_file()
        and (output / "SHA256SUMS").is_file()
    )
    if legacy_site:
        validate_checksums(output)
        return
    raise ValueError(f"refusing to replace unowned Pages output directory: {output}")


def render_template(source: Path, destination: Path, replacements: dict[str, str]) -> None:
    """Render one committed static page without permitting unresolved tokens."""
    if not source.is_file() or source.stat().st_size == 0:
        raise FileNotFoundError(f"required site template is missing: {source}")
    rendered = source.read_text(encoding="utf-8")
    for token, value in replacements.items():
        rendered = rendered.replace(f"{{{{{token}}}}}", value)
    unresolved = sorted(set(TEMPLATE_TOKEN.findall(rendered)))
    if unresolved:
        raise RuntimeError(
            f"unresolved site template token(s) in {source}: {', '.join(unresolved)}"
        )
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(rendered, encoding="utf-8")


def resolve_site_path(site: Path, document: Path, target: str) -> Path:
    """Resolve one local HTML target and reject paths that escape the site."""
    parsed = urlsplit(target)
    relative = parsed.path
    candidate = (
        site / relative.lstrip("/")
        if relative.startswith("/")
        else document.parent / relative
    )
    if not relative or relative.endswith("/"):
        candidate = candidate / "index.html"
    elif candidate.is_dir():
        candidate = candidate / "index.html"
    resolved = candidate.resolve()
    if resolved != site and site not in resolved.parents:
        raise ValueError(f"local route escapes staged site: {target}")
    return resolved


def validate_local_links(site: Path) -> None:
    """Require every local route from every HTML page to resolve inside the site."""
    for document in sorted(site.rglob("*.html")):
        html = document.read_text(encoding="utf-8")
        for target in LOCAL_LINK.findall(html):
            parsed = urlsplit(target)
            if target.startswith("//"):
                raise ValueError(f"protocol-relative route is not permitted: {target}")
            if parsed.scheme in {"data", "http", "https", "mailto"}:
                continue
            if parsed.scheme:
                raise ValueError(f"unsupported route scheme: {target}")
            resolved = (
                document.resolve()
                if not parsed.path
                else resolve_site_path(site, document, target)
            )
            if not resolved.is_file():
                relative = document.relative_to(site).as_posix()
                raise FileNotFoundError(
                    f"local route from {relative} does not resolve: {target}"
                )
            if parsed.fragment and resolved.suffix.lower() in {".html", ".htm"}:
                target_html = resolved.read_text(encoding="utf-8")
                fragment = unquote(parsed.fragment)
                identifiers = set(re.findall(r'\sid="([^\"]+)"', target_html))
                if fragment not in identifiers:
                    relative = document.relative_to(site).as_posix()
                    raise FileNotFoundError(
                        f"fragment from {relative} does not resolve: {target}"
                    )


def validate_checksums(site: Path) -> None:
    """Require a complete, unique, safe checksum inventory for staged files."""
    seen: set[str] = set()
    for line in (site / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        if not re.fullmatch(r"[0-9a-f]{64}  .+", line):
            raise ValueError(f"malformed checksum line: {line}")
        expected, relative = line.split("  ", 1)
        relative_path = Path(relative)
        if relative_path.is_absolute() or ".." in relative_path.parts:
            raise ValueError(f"unsafe checksum path: {relative}")
        if relative in seen:
            raise ValueError(f"duplicate checksum path: {relative}")
        seen.add(relative)
        target = (site / relative_path).resolve()
        if target != site and site not in target.parents:
            raise ValueError(f"checksum path escapes staged site: {relative}")
        if not target.is_file():
            raise FileNotFoundError(f"checksummed file is missing: {relative}")
        observed = sha256(target)
        if observed != expected:
            raise RuntimeError(f"published checksum mismatch: {relative}")
    expected_files = {
        path.relative_to(site).as_posix()
        for path in site.rglob("*")
        if path.is_file() and path != site / "SHA256SUMS"
    }
    if seen != expected_files:
        missing = sorted(expected_files - seen)
        extra = sorted(seen - expected_files)
        raise RuntimeError(
            f"checksum inventory mismatch; missing={missing}, extra={extra}"
        )


def validate_page_metadata(site: Path, pages_url: str) -> None:
    """Validate canonical metadata and baseline accessibility on public pages."""
    expected = {
        "index.html": pages_url,
        "docs/index.html": urljoin(pages_url, "docs/"),
        "architecture/index.html": urljoin(pages_url, "architecture/"),
        "legal/index.html": urljoin(pages_url, "legal/"),
        "paper/index.html": urljoin(pages_url, "paper/"),
        "magazine/index.html": urljoin(pages_url, "magazine/"),
        "downloads/index.html": urljoin(pages_url, "downloads/"),
    }
    for relative, canonical in expected.items():
        document = site / relative
        html = document.read_text(encoding="utf-8")
        markers = (
            '<html lang="',
            'name="viewport"',
            "<main",
            "<title>",
        )
        missing = [marker for marker in markers if marker not in html]
        if missing:
            raise RuntimeError(f"{relative} is missing page marker(s): {missing}")
        if (
            not re.search(r'class="[^"]*(?:skip-link|md-skip)[^"]*"', html)
            or not re.search(r'href="#[^"]+"', html)
        ):
            raise RuntimeError(f"{relative} is missing a fragment-targeted skip link")
        canonical_marker = f'<link rel="canonical" href="{canonical}">'
        if html.count(canonical_marker) != 1:
            raise RuntimeError(f"{relative} must declare exactly one canonical URL")
        if f'<meta property="og:url" content="{canonical}">' not in html:
            raise RuntimeError(f"{relative} is missing its canonical Open Graph URL")
        if len(re.findall(r"<h1\b", html)) != 1:
            raise RuntimeError(f"{relative} must contain exactly one h1 heading")
        if html.count("<title>") != 1:
            raise RuntimeError(f"{relative} must contain exactly one title")
        if TEMPLATE_TOKEN.search(html):
            raise RuntimeError(f"{relative} contains an unresolved site template token")
        structured_blocks = re.findall(
            r'<script type="application/ld\+json">\s*(.*?)\s*</script>',
            html,
            flags=re.DOTALL,
        )
        if len(structured_blocks) != 1:
            raise RuntimeError(
                f"{relative} must contain exactly one structured-data block"
            )
        structured_data = json.loads(structured_blocks[0])
        if structured_data.get("url") != canonical:
            raise RuntimeError(f"{relative} structured-data URL is not canonical")
        identifiers = re.findall(r'\sid="([^\"]+)"', html)
        duplicates = sorted(
            {value for value in identifiers if identifiers.count(value) > 1}
        )
        if duplicates:
            raise RuntimeError(f"{relative} contains duplicate HTML IDs: {duplicates}")
        if re.search(r"(?:href|src)=[\"']\s*[\"']", html):
            raise RuntimeError(f"{relative} contains an empty route")


def validate_site_assets(site: Path) -> None:
    """Require the shared site layer to retain responsive and focus behavior."""
    stylesheet = (site / "assets" / "site.css").read_text(encoding="utf-8")
    required_markers = (
        ":focus-visible",
        "@media (max-width:",
        "@media (prefers-reduced-motion: reduce)",
    )
    missing = [marker for marker in required_markers if marker not in stylesheet]
    if missing:
        raise RuntimeError(f"site stylesheet is missing responsive marker(s): {missing}")


def validate_site_suite_input(site_suite: Path, source_revision: str) -> dict:
    """Verify Holon's pre-composition artifact and its Antidote evidence."""
    required = (
        "index.html",
        "docs/index.html",
        "architecture/index.html",
        "legal/index.html",
        "site-suite.manifest.json",
        "site-suite.provenance.json",
    )
    missing = [relative for relative in required if not (site_suite / relative).is_file()]
    if missing:
        raise FileNotFoundError(f"site-suite input is incomplete: {missing}")
    provenance = json.loads(
        (site_suite / "site-suite.provenance.json").read_text(encoding="utf-8")
    )
    if provenance.get("schema") != "antidote.site-suite-provenance/v1":
        raise RuntimeError("site-suite input has an unexpected evidence schema")
    if provenance.get("sourceRevision") != source_revision:
        raise RuntimeError("site-suite and paper inputs disagree on source revision")
    inventory = provenance.get("artifact", {}).get("inventory")
    if not isinstance(inventory, list) or not inventory:
        raise RuntimeError("site-suite evidence has no artifact inventory")
    seen: set[str] = set()
    for record in inventory:
        relative = record.get("path")
        if (
            not isinstance(relative, str)
            or Path(relative).is_absolute()
            or ".." in Path(relative).parts
            or relative in seen
        ):
            raise RuntimeError(f"unsafe or duplicate site-suite artifact: {relative}")
        seen.add(relative)
        target = site_suite / relative
        if (
            not target.is_file()
            or target.stat().st_size != record.get("sizeBytes")
            or sha256(target) != record.get("sha256")
        ):
            raise RuntimeError(f"site-suite artifact drifted: {relative}")
    expected = {
        path.relative_to(site_suite).as_posix()
        for path in site_suite.rglob("*")
        if path.is_file() and path.name != "site-suite.provenance.json"
    }
    if seen != expected:
        raise RuntimeError("site-suite evidence inventory is incomplete")
    return provenance


def publication_url_for_html(site: Path, page: Path, pages_url: str) -> str:
    """Return the canonical directory URL for one staged HTML page."""
    relative = page.relative_to(site).as_posix()
    route = "" if relative == "index.html" else relative.removesuffix("index.html")
    return urljoin(pages_url, route)


def normalize_suite_metadata(
    site: Path, pages_url: str, source_revision: str, paper_version: str
) -> None:
    """Apply Antidote-owned canonical and revision metadata to suite pages."""
    roots = (site / "index.html",)
    pages = list(roots)
    for surface in ("docs", "architecture", "legal"):
        pages.extend(sorted((site / surface).rglob("*.html")))
    for page in pages:
        html = page.read_text(encoding="utf-8")
        canonical = publication_url_for_html(site, page, pages_url)
        canonical_tag = f'<link rel="canonical" href="{canonical}">'
        if re.search(r'<link rel="canonical" href="[^"]+"\s*/?>', html):
            html = re.sub(
                r'<link rel="canonical" href="[^"]+"\s*/?>', canonical_tag, html, count=1
            )
        else:
            html = html.replace("</head>", f"  {canonical_tag}\n</head>")
        og_tag = f'<meta property="og:url" content="{canonical}">'
        if re.search(r'<meta property="og:url" content="[^"]+"\s*/?>', html):
            html = re.sub(
                r'<meta property="og:url" content="[^"]+"\s*/?>', og_tag, html, count=1
            )
        else:
            html = html.replace("</head>", f"  {og_tag}\n</head>")
        revision_tag = f'<meta name="source-revision" content="{source_revision}">'
        if 'name="source-revision"' not in html:
            html = html.replace("</head>", f"  {revision_tag}\n</head>")
        title_match = re.search(r"<title>(.*?)</title>", html, flags=re.DOTALL)
        structured = {
            "@context": "https://schema.org",
            "@type": "WebPage",
            "name": title_match.group(1).strip() if title_match else "Antidote",
            "url": canonical,
            "version": paper_version,
            "isPartOf": {
                "@type": "WebSite",
                "name": "Antidote",
                "url": pages_url,
            },
        }
        block = (
            '  <script type="application/ld+json">\n'
            + json.dumps(structured, indent=2, sort_keys=True)
            + "\n  </script>\n"
        )
        html = re.sub(
            r'\s*<script type="application/ld\+json">.*?</script>\s*',
            "\n",
            html,
            flags=re.DOTALL,
        )
        html = html.replace("</head>", block + "</head>")
        html = html.replace('href=""', 'href="./"')
        page.write_text(html, encoding="utf-8")


def validate_site_catalog(
    site: Path, pages_url: str, custom_domain: str | None = None
) -> dict:
    """Validate the publication hub catalog and its artifact/status invariants."""
    catalog = json.loads((site / "site.json").read_text(encoding="utf-8"))
    if catalog.get("schema_version") != 1:
        raise RuntimeError("site.json must use schema version 1")
    if catalog.get("canonical_url") != pages_url:
        raise RuntimeError("site.json canonical_url does not match the staged base URL")
    if catalog.get("custom_domain") != custom_domain:
        raise RuntimeError("site.json custom_domain does not match its canonical URL")
    fallback_url = catalog.get("technical_fallback_url")
    if fallback_url is not None:
        parsed_fallback = urlsplit(fallback_url)
        if parsed_fallback.scheme != "https" or not parsed_fallback.netloc:
            raise RuntimeError("site.json technical fallback must be an HTTPS URL")
        if fallback_url == pages_url:
            raise RuntimeError("site.json technical fallback cannot be canonical")

    routes = catalog.get("routes")
    if not isinstance(routes, list):
        raise RuntimeError("site.json routes must be an array")
    route_map: dict[str, str] = {}
    for route in routes:
        route_id = route.get("id")
        path = route.get("path")
        if not isinstance(route_id, str) or not isinstance(path, str):
            raise RuntimeError("site.json routes require string id and path fields")
        if route_id in route_map:
            raise RuntimeError(f"duplicate site route id: {route_id}")
        if Path(path).is_absolute() or ".." in Path(path).parts:
            raise RuntimeError(f"unsafe site route: {path}")
        target = resolve_site_path(site, site / "index.html", path)
        if not target.is_file():
            raise FileNotFoundError(f"declared site route is missing: {path}")
        expected_status = "planned" if route_id == "magazine" else "available"
        if route.get("status") != expected_status:
            raise RuntimeError(
                f"site route has the wrong availability state: {route_id}"
            )
        route_map[route_id] = path
    if route_map != REQUIRED_ROUTES:
        raise RuntimeError(
            f"site.json route contract mismatch: expected={REQUIRED_ROUTES}, actual={route_map}"
        )

    slots = catalog.get("slots")
    if not isinstance(slots, list):
        raise RuntimeError("site.json slots must be an array")
    slot_map: dict[str, dict] = {}
    for slot in slots:
        slot_id = slot.get("id")
        status = slot.get("status")
        if not isinstance(slot_id, str) or slot_id in slot_map:
            raise RuntimeError(f"invalid or duplicate publication slot: {slot_id}")
        if status not in SLOT_STATUSES:
            raise RuntimeError(f"invalid publication slot status: {status}")
        artifacts = slot.get("artifacts")
        if not isinstance(artifacts, list):
            raise RuntimeError(f"publication slot artifacts must be an array: {slot_id}")
        if status == "planned":
            unexpected_fields = sorted(set(slot) - PLANNED_SLOT_FIELDS)
            if (
                artifacts
                or slot.get("manifest_path") is not None
                or slot.get("stage") is not None
                or unexpected_fields
            ):
                raise RuntimeError(
                    "planned publication slot cannot declare artifacts or publication "
                    f"metadata: {slot_id}"
                )
        artifact_ids: set[str] = set()
        for artifact in artifacts:
            path = artifact.get("path")
            artifact_id = artifact.get("id")
            if not isinstance(artifact_id, str) or artifact_id in artifact_ids:
                raise RuntimeError(
                    f"invalid or duplicate publication artifact id: {artifact_id}"
                )
            artifact_ids.add(artifact_id)
            if (
                not isinstance(path, str)
                or Path(path).is_absolute()
                or ".." in Path(path).parts
            ):
                raise RuntimeError(f"unsafe publication artifact path: {path}")
            target = (site / path).resolve()
            if not target.is_file():
                raise FileNotFoundError(f"publication artifact is missing: {path}")
            if target.stat().st_size == 0:
                raise RuntimeError(f"publication artifact is empty: {path}")
            if artifact.get("sha256") != sha256(target):
                raise RuntimeError(f"publication artifact digest mismatch: {path}")
            if artifact.get("url") != public_artifact_url(
                pages_url, artifact_id, path
            ):
                raise RuntimeError(f"publication artifact URL mismatch: {path}")
            if not isinstance(artifact.get("media_type"), str):
                raise RuntimeError(f"publication artifact media type is missing: {path}")
        slot_map[slot_id] = slot
    if set(slot_map) != {"paper", "magazine"}:
        raise RuntimeError("site.json must declare exactly the paper and magazine slots")
    if slot_map["paper"].get("status") != "available":
        raise RuntimeError("paper slot must be available")
    if slot_map["magazine"].get("status") != "planned":
        raise RuntimeError("magazine slot must remain planned until an edition exists")
    if slot_map["paper"].get("path") != "paper/":
        raise RuntimeError("paper slot must use the stable paper route")
    if slot_map["paper"].get("manifest_path") != "publication.json":
        raise RuntimeError("paper slot must reference the publication manifest")
    if slot_map["magazine"].get("path") != "magazine/":
        raise RuntimeError("magazine slot must use the stable magazine route")
    return catalog


def validate_publication_manifest(
    site: Path,
    pages_url: str,
    catalog: dict,
    custom_domain: str | None = None,
) -> None:
    """Verify the preserved paper manifest against files and the site catalog."""
    manifest = json.loads((site / "publication.json").read_text(encoding="utf-8"))
    if manifest.get("schema_version") != 1:
        raise RuntimeError("publication.json must use schema version 1")
    if manifest.get("pages_url") != pages_url:
        raise RuntimeError("publication.json pages_url is not canonical")
    if manifest.get("custom_domain") != custom_domain:
        raise RuntimeError("publication.json custom_domain is not canonical")
    if manifest.get("source_revision") != catalog.get("source_revision"):
        raise RuntimeError("site and publication manifests disagree on source revision")
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, dict):
        raise RuntimeError("publication.json artifacts must be an object")
    if set(artifacts) != {
        "accessible_web",
        "arxiv_source",
        "paper_pdf",
        "provenance",
    }:
        raise RuntimeError("publication.json paper artifact inventory is incomplete")
    for artifact_id, artifact in artifacts.items():
        path = artifact.get("path")
        if (
            not isinstance(path, str)
            or Path(path).is_absolute()
            or ".." in Path(path).parts
        ):
            raise RuntimeError(f"unsafe paper artifact path: {path}")
        target = (site / path).resolve()
        if not target.is_file() or target.stat().st_size == 0:
            raise FileNotFoundError(f"paper artifact is missing or empty: {path}")
        if artifact.get("sha256") != sha256(target):
            raise RuntimeError(f"paper artifact digest mismatch: {artifact_id}")
        if artifact.get("url") != public_artifact_url(
            pages_url, artifact_id, path
        ):
            raise RuntimeError(f"paper artifact URL mismatch: {artifact_id}")

    paper_slots = [slot for slot in catalog["slots"] if slot.get("id") == "paper"]
    if len(paper_slots) != 1:
        raise RuntimeError("site.json must contain exactly one paper slot")
    paper_slot = paper_slots[0]
    if paper_slot.get("version") != manifest.get("version"):
        raise RuntimeError("site and publication manifests disagree on paper version")
    if paper_slot.get("stage") != manifest.get("stage"):
        raise RuntimeError("site and publication manifests disagree on paper stage")
    slot_artifacts = {
        artifact.get("id"): artifact for artifact in paper_slot.get("artifacts", [])
    }
    if set(slot_artifacts) != set(artifacts):
        raise RuntimeError("site and publication manifests disagree on paper artifacts")
    for artifact_id, artifact in artifacts.items():
        slot_artifact = slot_artifacts[artifact_id]
        for field in ("path", "sha256", "url"):
            if slot_artifact.get(field) != artifact.get(field):
                raise RuntimeError(
                    "site and publication manifests disagree on paper artifact "
                    f"{artifact_id}: {field}"
                )


def stage_site(
    root: Path,
    build: Path,
    site_suite: Path,
    output: Path,
    *,
    custom_domain: str = "",
) -> dict:
    """Create one complete Pages tree from governed Antidote outputs."""
    root = root.resolve()
    build = build.resolve()
    site_suite = site_suite.resolve()
    output = output.resolve()
    validate_output_target(root, build, output)

    config = load_toml(root / "beacon-project.toml")
    paper = config["paper"]
    publication = config["publication"]
    provenance = json.loads((build / "provenance.json").read_text(encoding="utf-8"))
    validate_site_suite_input(site_suite, provenance["source_revision"])
    archives = sorted((build / "arxiv").glob("*.tar.gz"))
    if len(archives) != 1:
        raise RuntimeError("Pages staging requires exactly one arXiv source archive")

    configured_domain = validate_custom_domain(publication.get("pages_custom_domain", ""))
    requested_domain = validate_custom_domain(custom_domain)
    if requested_domain and configured_domain and requested_domain != configured_domain:
        raise ValueError(
            "Pages custom domain mismatch: "
            f"configuration={configured_domain}, requested={requested_domain}"
        )
    domain = requested_domain or configured_domain
    configured_pages_url = publication["pages_url"].rstrip("/") + "/"
    pages_url = f"https://{domain}/" if domain else configured_pages_url
    if domain and configured_pages_url != pages_url:
        raise ValueError(
            f"publication.pages_url must match the configured custom domain: {pages_url}"
        )
    fallback_url = publication.get("pages_fallback_url")
    if fallback_url:
        fallback_url = fallback_url.rstrip("/") + "/"

    shutil.rmtree(output, ignore_errors=True)
    shutil.copytree(site_suite, output)
    (output / OWNER_FILE).write_text(OWNER_TEXT, encoding="utf-8")
    replacements = {
        "SITE_BASE_URL": pages_url,
        "PAPER_VERSION": paper["version"],
        "SOURCE_REVISION": provenance["source_revision"],
        "SOURCE_ARCHIVE_NAME": archives[0].name,
    }
    for source, destination in (
        (root / "docs" / "magazine" / "index.html", output / "magazine" / "index.html"),
        (root / "docs" / "downloads" / "index.html", output / "downloads" / "index.html"),
    ):
        render_template(source, destination, replacements)
    assets = root / "docs" / "assets"
    if not assets.is_dir():
        raise FileNotFoundError(f"required site assets directory is missing: {assets}")
    shutil.copytree(assets, output / "assets", dirs_exist_ok=True)
    copy_required(root / "docs" / "site.webmanifest", output / "site.webmanifest")
    copy_required(build / "paper.pdf", output / "antidote.pdf")
    copy_required(build / "provenance.json", output / "provenance.json")
    shutil.copytree(build / "web", output / "paper")
    copy_required(archives[0], output / "downloads" / archives[0].name)
    (output / ".nojekyll").write_text("", encoding="utf-8")
    normalize_suite_metadata(
        output,
        pages_url,
        provenance["source_revision"],
        paper["version"],
    )

    artifact_paths = {
        "accessible_web": "paper/index.html",
        "paper_pdf": "antidote.pdf",
        "provenance": "provenance.json",
        "arxiv_source": f"downloads/{archives[0].name}",
    }
    artifact_media_types = {
        "accessible_web": "text/html",
        "paper_pdf": "application/pdf",
        "provenance": "application/json",
        "arxiv_source": "application/gzip",
    }
    artifacts = {
        key: {
            "path": relative,
            "sha256": sha256(output / relative),
            "url": public_artifact_url(pages_url, key, relative),
        }
        for key, relative in artifact_paths.items()
    }
    generated_at = dt.datetime.fromtimestamp(
        int(config["provenance"]["source_date_epoch"]), tz=dt.timezone.utc
    ).isoformat()
    manifest = {
        "schema_version": 1,
        "id": paper["id"],
        "title": paper["title"],
        "version": paper["version"],
        "stage": paper["stage"],
        "generated_at": generated_at,
        "pages_url": pages_url,
        "custom_domain": domain or None,
        "source_repository": config["provenance"]["source_repository"],
        "source_revision": provenance["source_revision"],
        "artifacts": artifacts,
    }
    (output / "publication.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    site_catalog = {
        "schema_version": 1,
        "id": "antidote-publication-hub",
        "title": "Antidote",
        "canonical_url": pages_url,
        "technical_fallback_url": fallback_url,
        "custom_domain": domain or None,
        "generated_at": generated_at,
        "source_repository": config["provenance"]["source_repository"],
        "source_revision": provenance["source_revision"],
        "checksum_manifest_path": "SHA256SUMS",
        "routes": [
            {
                "id": route_id,
                "path": path,
                "status": "planned" if route_id == "magazine" else "available",
            }
            for route_id, path in REQUIRED_ROUTES.items()
        ],
        "slots": [
            {
                "id": "paper",
                "type": "research-paper",
                "label": "Research paper",
                "status": "available",
                "stage": paper["stage"],
                "version": paper["version"],
                "path": "paper/",
                "manifest_path": "publication.json",
                "artifacts": [
                    {
                        "id": artifact_id,
                        "path": artifact["path"],
                        "url": artifact["url"],
                        "sha256": artifact["sha256"],
                        "media_type": artifact_media_types[artifact_id],
                    }
                    for artifact_id, artifact in artifacts.items()
                ],
            },
            {
                "id": "magazine",
                "type": "magazine",
                "label": "Magazine",
                "status": "planned",
                "stage": None,
                "path": "magazine/",
                "manifest_path": None,
                "artifacts": [],
            },
        ],
    }
    (output / "site.json").write_text(
        json.dumps(site_catalog, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    checksum_files = sorted(
        path
        for path in output.rglob("*")
        if path.is_file() and path != output / "SHA256SUMS"
    )
    checksum_lines = [
        f"{sha256(path)}  {path.relative_to(output).as_posix()}"
        for path in checksum_files
    ]
    (output / "SHA256SUMS").write_text(
        "\n".join(checksum_lines) + "\n", encoding="utf-8"
    )

    validate_local_links(output)
    validate_page_metadata(output, pages_url)
    validate_site_assets(output)
    catalog = validate_site_catalog(output, pages_url, domain or None)
    validate_publication_manifest(output, pages_url, catalog, domain or None)
    validate_checksums(output)
    print(f"PASS staged Antidote Pages artifact at {output}")
    return manifest


def main() -> int:
    """Parse CLI arguments and stage the repository-owned Pages artifact."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--build-dir", default="build/egohygiene")
    parser.add_argument("--output-dir", default="_site")
    parser.add_argument("--site-suite-dir", required=True)
    parser.add_argument(
        "--custom-domain",
        default=os.environ.get("PAGES_CUSTOM_DOMAIN", ""),
    )
    arguments = parser.parse_args()
    build = Path(arguments.build_dir).expanduser()
    if not build.is_absolute():
        build = ROOT / build
    output = Path(arguments.output_dir).expanduser()
    if not output.is_absolute():
        output = ROOT / output
    site_suite = Path(arguments.site_suite_dir).expanduser()
    if not site_suite.is_absolute():
        site_suite = ROOT / site_suite
    stage_site(
        ROOT,
        build,
        site_suite,
        output,
        custom_domain=arguments.custom_domain,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
