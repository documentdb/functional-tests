"""
Shared test case for projection tests.
"""

from dataclasses import dataclass
from typing import Any, Optional

from documentdb_tests.framework.test_case import BaseTestCase


@dataclass(frozen=True)
class ProjectionTestCase(BaseTestCase):
    """Test case for projection operator tests."""

    projection: Optional[dict] = None
    doc: Optional[list[dict]] = None
    filter: Optional[Any] = None
