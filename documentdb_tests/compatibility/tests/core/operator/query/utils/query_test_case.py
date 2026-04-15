"""
Shared test case for query tests.
"""

from dataclasses import dataclass
from typing import Any, Optional

from documentdb_tests.framework.test_case import BaseTestCase


@dataclass(frozen=True)
class QueryTestCase(BaseTestCase):
    """Test case for query operator tests."""

    filter: Any = None
    doc: Optional[list[dict]] = None
