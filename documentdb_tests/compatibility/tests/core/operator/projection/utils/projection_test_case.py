"""
Shared test case for projection tests.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from documentdb_tests.framework.test_case import BaseTestCase


@dataclass(frozen=True)
class ProjectionTestCase(BaseTestCase):
    """Test case for projection operator tests."""

    doc: list[dict] | None = None
    projection: dict | None = None
    filter: Any | None = None
