"""
Shared test infrastructure for $isArray expression tests.
"""

from dataclasses import dataclass
from typing import Any

from documentdb_tests.framework.test_case import BaseTestCase


@dataclass(frozen=True)
class IsArrayTest(BaseTestCase):
    """Test case for $isArray operator."""

    value: Any = None
