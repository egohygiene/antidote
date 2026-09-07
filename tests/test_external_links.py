# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT

"""Tests for bounded, host-compatible external-link validation."""

from __future__ import annotations

import importlib.util
import sys
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "check.py"
sys.path.insert(0, str(ROOT / "scripts"))
SPEC = importlib.util.spec_from_file_location("publication_check", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
CHECK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECK)


class Response:
    """Minimal context-manager response returned by mocked URL probes."""

    def __init__(self, status: int) -> None:
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *_arguments) -> None:
        return None


class ExternalLinkTests(unittest.TestCase):
    """Keep live checks strict without assuming every host supports HEAD."""

    @mock.patch.object(CHECK.urllib.request, "urlopen")
    def test_successful_head_passes(self, urlopen: mock.Mock) -> None:
        urlopen.return_value = Response(200)

        self.assertIsNone(CHECK.probe_live_link("https://example.test/paper"))
        self.assertEqual(urlopen.call_args.args[0].method, "HEAD")

    @mock.patch.object(CHECK.urllib.request, "urlopen")
    def test_method_not_allowed_falls_back_to_ranged_get(
        self, urlopen: mock.Mock
    ) -> None:
        urlopen.side_effect = [
            urllib.error.HTTPError(
                "https://example.test/paper", 405, "method", {}, None
            ),
            Response(206),
        ]

        self.assertIsNone(CHECK.probe_live_link("https://example.test/paper"))
        request = urlopen.call_args_list[1].args[0]
        self.assertEqual(request.method, "GET")
        self.assertEqual(request.headers["Range"], "bytes=0-0")

    @mock.patch.object(CHECK.urllib.request, "urlopen")
    def test_timeout_falls_back_to_get(self, urlopen: mock.Mock) -> None:
        urlopen.side_effect = [TimeoutError("slow HEAD"), Response(200)]

        self.assertIsNone(CHECK.probe_live_link("https://example.test/paper"))
        self.assertEqual(urlopen.call_count, 2)

    @mock.patch.object(CHECK.urllib.request, "urlopen")
    def test_missing_resource_fails_without_masking_status(
        self, urlopen: mock.Mock
    ) -> None:
        urlopen.side_effect = urllib.error.HTTPError(
            "https://example.test/missing", 404, "missing", {}, None
        )

        self.assertEqual(
            CHECK.probe_live_link("https://example.test/missing"),
            "external link returned HTTP 404: https://example.test/missing",
        )
        self.assertEqual(urlopen.call_count, 1)

    @mock.patch.object(CHECK, "probe_live_link")
    def test_concurrent_results_keep_sorted_url_order(self, probe: mock.Mock) -> None:
        probe.side_effect = lambda url: f"bad: {url}"
        errors: list[str] = []

        CHECK.live_link_checks(
            {"https://z.example.test", "https://a.example.test"}, errors
        )

        self.assertEqual(
            errors,
            ["bad: https://a.example.test", "bad: https://z.example.test"],
        )


if __name__ == "__main__":
    unittest.main()
