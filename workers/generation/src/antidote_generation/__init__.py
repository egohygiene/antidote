# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT

"""Antidote generation-worker foundation.

The executable mock worker begins in issue #13. This package currently owns
only cross-language contract validation and generated type projections.
"""

from antidote_generation.contracts import ContractRegistry

__all__ = ["ContractRegistry"]
