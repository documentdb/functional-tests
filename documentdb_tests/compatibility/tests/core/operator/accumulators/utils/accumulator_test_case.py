"""Shared test case for accumulator tests."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from documentdb_tests.framework.test_case import BaseTestCase


@dataclass(frozen=True)
class AccumulatorTestCase(BaseTestCase):
    """Test case for accumulator tests."""

    docs: list[dict] | None = None
    pipeline: list[dict[str, Any]] | None = None
