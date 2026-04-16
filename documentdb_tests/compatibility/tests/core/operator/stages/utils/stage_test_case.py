"""
Shared test case for pipeline stage tests.
"""

from dataclasses import dataclass
from typing import Any, Callable, Optional

from documentdb_tests.framework.test_case import BaseTestCase


@dataclass(frozen=True)
class StageTestCase(BaseTestCase):
    """Test case for pipeline stage tests."""

    docs: Optional[list[dict[str, Any]]] = None
    pipeline: Optional[list[dict[str, Any]]] = None
    setup: Optional[Callable] = None
