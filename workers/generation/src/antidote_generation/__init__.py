# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT

"""Contract validation and deterministic model-worker protocol execution."""

from antidote_generation.contracts import ContractRegistry
from antidote_generation.protocol import PROTOCOL_VERSION
from antidote_generation.worker import MockGenerationWorker

__all__ = ["PROTOCOL_VERSION", "ContractRegistry", "MockGenerationWorker"]
