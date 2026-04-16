"""
Shared test case for pipeline stage tests.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from documentdb_tests.framework.test_case import BaseTestCase


@dataclass(frozen=True)
class StageTestCase(BaseTestCase):
    """Test case for pipeline stage tests."""

    docs: list[dict[str, Any]] | None = None
    pipeline: list[dict[str, Any]] | None = None
    setup: Callable | None = None
