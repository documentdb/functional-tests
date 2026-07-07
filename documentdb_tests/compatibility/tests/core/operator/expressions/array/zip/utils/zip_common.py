"""
Shared test infrastructure for $zip expression tests.
"""

from dataclasses import dataclass
from typing import Any

from documentdb_tests.framework.test_case import BaseTestCase


@dataclass(frozen=True)
class ZipTest(BaseTestCase):
    """Test case for $zip operator."""

    inputs: Any = None
    use_longest_length: Any = None
    defaults: Any = None
