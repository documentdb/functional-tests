"""
Shared test infrastructure for $in expression tests.

Note: This file lives in array/utils/ rather than array/in/utils/ because
"in" is a Python keyword and cannot be used in import paths.
"""

from dataclasses import dataclass
from typing import Any

from documentdb_tests.framework.test_case import BaseTestCase


@dataclass(frozen=True)
class InTest(BaseTestCase):
    """Test case for $in operator."""

    value: Any = None
    array: Any = None
