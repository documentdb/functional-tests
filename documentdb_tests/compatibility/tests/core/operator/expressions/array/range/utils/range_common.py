"""
Shared test infrastructure for $range expression tests.
"""

from dataclasses import dataclass
from typing import Any

from documentdb_tests.framework.test_case import BaseTestCase


@dataclass(frozen=True)
class RangeTest(BaseTestCase):
    """Test case for $range operator."""

    start: Any = None
    end: Any = None
    step: Any = None
